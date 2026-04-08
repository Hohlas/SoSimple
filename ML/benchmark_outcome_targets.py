import argparse
import json
from datetime import datetime, UTC
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ML.data_loader import (
    ARCHETYPE_TARGET,
    BINARY_CLASSIFICATION_TARGETS,
    CSV_SEP,
    TRADE_OUTCOME_TARGET,
    TRADE_PNL_TARGET,
    VAL_FILE,
    create_data_loaders,
    task_checkpoint_suffix,
    task_target_column,
)
from ML.models import get_model
from ML.utils import get_device, set_seed


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHECKPOINTS_DIR = PROJECT_ROOT / 'ML' / 'checkpoints'
REPORTS_DIR = PROJECT_ROOT / 'ML' / 'reports'

TASKS = [TRADE_OUTCOME_TARGET, TRADE_PNL_TARGET, ARCHETYPE_TARGET]
DEFAULT_TOP_PCTS = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]


def rank_candidates(
    table: pd.DataFrame,
    min_trades: int = 80,
    min_stability_ratio: float = 0.75,
) -> pd.DataFrame:
    out = table[table['trades'] >= min_trades].copy()
    if 'stability_ratio' in out.columns:
        out = out[out['stability_ratio'] >= min_stability_ratio].copy()
    out = out.sort_values(
        ['pf', 'stability_ratio', 'trades'],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    return out


def pick_winner(
    table: pd.DataFrame,
    min_trades: int = 80,
    min_stability_ratio: float = 0.75,
) -> pd.Series:
    live = rank_candidates(
        table,
        min_trades=min_trades,
        min_stability_ratio=min_stability_ratio,
    )
    if live.empty:
        raise ValueError('No outcome target candidates passed the trade-floor and stability filters.')
    return live.iloc[0]


def summarize_task_candidate(
    table: pd.DataFrame,
    min_trades: int = 80,
    min_stability_ratio: float = 0.75,
) -> pd.Series:
    if table.empty:
        raise ValueError('Outcome target benchmark received an empty slice table.')

    live = rank_candidates(
        table,
        min_trades=min_trades,
        min_stability_ratio=min_stability_ratio,
    )
    if not live.empty:
        best = live.iloc[0].copy()
        best['passed_filters'] = True
        best['rejection_reason'] = ''
        return best

    fallback = table.sort_values(
        ['pf', 'stability_ratio', 'trades'],
        ascending=[False, False, False],
    ).reset_index(drop=True).iloc[0].copy()
    fallback['passed_filters'] = False
    fallback['rejection_reason'] = 'no_slice_passed_filters'
    return fallback


@torch.no_grad()
def run_validation_scores(model: torch.nn.Module, val_loader, task: str, device: torch.device) -> np.ndarray:
    all_scores = []
    model.eval()

    for X_batch, _y_batch, mask_batch in val_loader:
        X_batch = X_batch.to(device)
        mask_batch = mask_batch.to(device)
        logits = model(X_batch, mask=mask_batch).cpu()

        if task in BINARY_CLASSIFICATION_TARGETS:
            score = torch.softmax(logits, dim=1)[:, 1].numpy()
        else:
            score = logits.numpy()
            if score.ndim > 1 and score.shape[-1] == 1:
                score = score.squeeze(-1)
        all_scores.append(score)

    return np.concatenate(all_scores)


def load_validation_frame() -> pd.DataFrame:
    cols = ['time', 'signal', 'trade_pnl_h12_atr', 'trade_outcome_h12', 'archetype_target']
    frame = pd.read_csv(VAL_FILE, sep=CSV_SEP, usecols=cols, low_memory=False)
    frame['time'] = pd.to_datetime(frame['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    return frame


def evaluate_score_slices(
    frame: pd.DataFrame,
    score: np.ndarray,
    task: str,
    top_pcts: list[float],
    min_year_trades: int = 10,
) -> pd.DataFrame:
    signal_mask = frame['signal'].values != 0
    eligible = frame.loc[signal_mask].copy().reset_index(drop=True)
    score = np.asarray(score)
    if len(score) == len(eligible):
        eligible['score'] = score
    elif len(score) == len(frame):
        eligible['score'] = score[signal_mask]
    else:
        raise ValueError(
            f'Unexpected score length for {task}: got {len(score)}, '
            f'expected {len(eligible)} signal rows or {len(frame)} full rows.'
        )

    rows = []
    for top_pct in top_pcts:
        threshold = float(eligible['score'].quantile(1.0 - top_pct))
        selected = eligible.loc[eligible['score'] >= threshold].copy()
        pnl = selected['trade_pnl_h12_atr'].values.astype(np.float64)

        trades = int(len(selected))
        gross_profit = float(pnl[pnl > 0].sum())
        gross_loss = float(-pnl[pnl < 0].sum())
        pf = gross_profit / gross_loss if gross_loss > 0 else (np.inf if gross_profit > 0 else 0.0)
        win_rate = float((pnl > 0).mean()) if trades > 0 else 0.0
        mean_pnl = float(pnl.mean()) if trades > 0 else 0.0

        eligible_years = 0
        stable_years = 0
        worst_year_pf = np.nan
        yearly_detail = {}
        if trades > 0:
            selected['year'] = selected['time'].dt.year
            yearly_pfs = []
            for year, group in selected.groupby('year', dropna=True):
                gp = float(group.loc[group['trade_pnl_h12_atr'] > 0, 'trade_pnl_h12_atr'].sum())
                gl = float(-group.loc[group['trade_pnl_h12_atr'] < 0, 'trade_pnl_h12_atr'].sum())
                year_pf = gp / gl if gl > 0 else (np.inf if gp > 0 else 0.0)
                yearly_detail[str(int(year))] = {
                    'trades': int(len(group)),
                    'pf': year_pf,
                    'mean_pnl': float(group['trade_pnl_h12_atr'].mean()),
                }
                if len(group) >= min_year_trades:
                    eligible_years += 1
                    stable_years += int(year_pf >= 1.0)
                    yearly_pfs.append(year_pf)
            if yearly_pfs:
                worst_year_pf = float(np.min(yearly_pfs))

        stability_ratio = float(stable_years / eligible_years) if eligible_years > 0 else 0.0
        rows.append({
            'task': task,
            'top_pct': float(top_pct),
            'score_threshold': threshold,
            'trades': trades,
            'pf': pf,
            'win_rate': win_rate,
            'mean_pnl_atr': mean_pnl,
            'eligible_years': int(eligible_years),
            'stable_years': int(stable_years),
            'stability_ratio': stability_ratio,
            'worst_year_pf': worst_year_pf,
            'yearly_detail_json': json.dumps(yearly_detail, ensure_ascii=False, sort_keys=True),
        })

    return pd.DataFrame(rows)


def load_model_for_task(model_name: str, task: str, device: torch.device) -> tuple[torch.nn.Module, dict, Path]:
    ckpt_path = CHECKPOINTS_DIR / f'{model_name}{task_checkpoint_suffix(task)}_best.pt'
    if not ckpt_path.exists():
        raise FileNotFoundError(f'Checkpoint not found for {task}: {ckpt_path}')

    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    model_kwargs = ckpt.get('model_kwargs', {})
    model = get_model(
        ckpt.get('model_name', model_name),
        num_classes=ckpt.get('num_classes', 1),
        **model_kwargs,
    )
    model.load_state_dict(ckpt['model_state_dict'])
    model = model.to(device)
    model.eval()
    return model, model_kwargs, ckpt_path


def benchmark_outcome_targets(
    model_name: str = 'transformer',
    top_pcts: list[float] | None = None,
    min_trades: int = 80,
    min_stability_ratio: float = 0.75,
    min_year_trades: int = 10,
    seed: int = 42,
) -> dict:
    set_seed(seed)
    device = get_device()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    top_pcts = list(top_pcts or DEFAULT_TOP_PCTS)
    validation_frame = load_validation_frame()

    per_task_best = []
    full_rows = []

    for task in TASKS:
        print(f'\n{"─" * 60}')
        print(f'🔎 Validation benchmark for {task}')

        _, val_loader, _ = create_data_loaders(
            batch_size=256,
            target=task_target_column(task),
            seq_len=20,
            clear_cache=False,
        )
        model, _model_kwargs, ckpt_path = load_model_for_task(model_name, task, device)
        score = run_validation_scores(model, val_loader, task, device)
        table = evaluate_score_slices(
            validation_frame,
            score,
            task=task,
            top_pcts=top_pcts,
            min_year_trades=min_year_trades,
        )
        table['checkpoint'] = str(ckpt_path)
        full_rows.append(table)

        best = summarize_task_candidate(
            table,
            min_trades=min_trades,
            min_stability_ratio=min_stability_ratio,
        )
        per_task_best.append(best)
        if best['passed_filters']:
            print(
                f"  best slice: top_pct={best['top_pct']:.2f}, threshold={best['score_threshold']:.4f}, "
                f"trades={int(best['trades'])}, pf={best['pf']:.4f}, stability={best['stability_ratio']:.2f}"
            )
        else:
            print(
                f"  no viable slice passed filters; strongest rejected slice: top_pct={best['top_pct']:.2f}, "
                f"trades={int(best['trades'])}, pf={best['pf']:.4f}, stability={best['stability_ratio']:.2f}"
            )

    full_table = pd.concat(full_rows, ignore_index=True)
    best_table = pd.DataFrame(per_task_best).reset_index(drop=True)
    winner_pool = best_table.loc[best_table['passed_filters']].copy()
    winner = None
    if not winner_pool.empty:
        winner = pick_winner(
            winner_pool,
            min_trades=min_trades,
            min_stability_ratio=min_stability_ratio,
        )

    csv_path = REPORTS_DIR / 'outcome_target_validation_benchmark.csv'
    full_table.to_csv(csv_path, index=False)

    md_path = REPORTS_DIR / 'outcome_target_validation_benchmark.md'
    lines = [
        '# Outcome Target Validation Benchmark',
        '',
        f'- model: `{model_name}`',
        f'- min_trades: {min_trades}',
        f'- min_stability_ratio: {min_stability_ratio:.2f}',
        f'- min_year_trades: {min_year_trades}',
        '',
        '## Per-Task Winners',
        '',
        '| task | status | top_pct | threshold | trades | pf | stability | mean_pnl_atr |',
        '|------|--------|---------|-----------|--------|----|-----------|--------------|',
    ]
    for _, row in best_table.iterrows():
        status = 'passed' if row['passed_filters'] else row['rejection_reason']
        lines.append(
            f"| {row['task']} | {status} | {row['top_pct']:.2f} | {row['score_threshold']:.4f} | "
            f"{int(row['trades'])} | {row['pf']:.4f} | {row['stability_ratio']:.2f} | "
            f"{row['mean_pnl_atr']:.4f} |"
        )
    lines.extend([
        '',
        '## Frozen Winner',
        '',
    ])
    if winner is None:
        lines.append('- No target family passed the shared trade-floor and yearly-stability filters.')
        lines.append('- No frozen winner was created, so test evaluation must not be run.')
    else:
        lines.extend([
            f"- task: `{winner['task']}`",
            f"- checkpoint: `{Path(winner['checkpoint']).name}`",
            f"- top_pct: {winner['top_pct']:.2f}",
            f"- score_threshold: {winner['score_threshold']:.4f}",
            f"- trades: {int(winner['trades'])}",
            f"- pf: {winner['pf']:.4f}",
            f"- stability_ratio: {winner['stability_ratio']:.2f}",
        ])
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    frozen_path = REPORTS_DIR / 'frozen_outcome_target.json'
    if frozen_path.exists():
        frozen_path.unlink()

    frozen = None
    if winner is not None:
        frozen = {
            'saved_at': datetime.now(UTC).isoformat(),
            'split_profile': 'validation_research',
            'settings': {
                'model': model_name,
                'top_pcts': top_pcts,
                'min_trades': min_trades,
                'min_stability_ratio': min_stability_ratio,
                'min_year_trades': min_year_trades,
                'score_rule': 'select signal rows with score >= threshold chosen on validation only',
            },
            'winner': {
                'task': winner['task'],
                'checkpoint': winner['checkpoint'],
                'top_pct': float(winner['top_pct']),
                'score_threshold': float(winner['score_threshold']),
                'trades': int(winner['trades']),
                'pf': float(winner['pf']),
                'stability_ratio': float(winner['stability_ratio']),
                'mean_pnl_atr': float(winner['mean_pnl_atr']),
                'worst_year_pf': None if pd.isna(winner['worst_year_pf']) else float(winner['worst_year_pf']),
            },
            'rejected': [
                {
                    'task': row['task'],
                    'trades': int(row['trades']),
                    'pf': float(row['pf']),
                    'stability_ratio': float(row['stability_ratio']),
                    'mean_pnl_atr': float(row['mean_pnl_atr']),
                    'passed_filters': bool(row['passed_filters']),
                    'rejection_reason': row['rejection_reason'],
                }
                for _, row in best_table.loc[best_table['task'] != winner['task']].iterrows()
            ],
        }
        frozen_path.write_text(json.dumps(frozen, indent=2, ensure_ascii=False), encoding='utf-8')

    return {
        'winner': None if frozen is None else frozen['winner'],
        'csv_path': str(csv_path),
        'md_path': str(md_path),
        'json_path': None if frozen is None else str(frozen_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Validation-only benchmark for outcome-aligned target families.')
    parser.add_argument('--model', type=str, default='transformer')
    parser.add_argument('--min-trades', type=int, default=80)
    parser.add_argument('--min-stability-ratio', type=float, default=0.75)
    parser.add_argument('--min-year-trades', type=int, default=10)
    parser.add_argument('--top-pcts', type=float, nargs='*', default=DEFAULT_TOP_PCTS)
    parser.add_argument('--seed', type=int, default=42)
    return parser.parse_args()


def main():
    args = parse_args()
    result = benchmark_outcome_targets(
        model_name=args.model,
        top_pcts=args.top_pcts,
        min_trades=args.min_trades,
        min_stability_ratio=args.min_stability_ratio,
        min_year_trades=args.min_year_trades,
        seed=args.seed,
    )
    if result['winner'] is None:
        print('\n⚠ No frozen winner: no target family passed the shared validation filters.')
        print(f'   benchmark_md={result["md_path"]}')
    else:
        print(f'\n✅ Frozen winner: {result["winner"]["task"]}')
        print(f'   threshold={result["winner"]["score_threshold"]:.4f}, pf={result["winner"]["pf"]:.4f}')
        print(f'   json={result["json_path"]}')


if __name__ == '__main__':
    main()
