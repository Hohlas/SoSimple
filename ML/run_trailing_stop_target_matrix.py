from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

import pandas as pd

from API.generate_signals import generate_signals
from ML.benchmark_trailing_stop_target import pick_validation_winner, summarize_candidate
from ML.data_loader import task_checkpoint_suffix
from ML.evaluate_test import run_evaluation
from ML.train import CHECKPOINTS_DIR, REPORTS_DIR, train_model
from ML.trailing_stop_target_task import TRAILING_STOP_TARGET


DEFAULT_MATRIX_CONFIGS = [
    {'target_column': 'trail_48_pnl_atr_x2', 'seq_len': 20},
    {'target_column': 'trail_48_pnl_atr_x2', 'seq_len': 50},
    {'target_column': 'trail_48_pnl_atr_x2', 'seq_len': 100},
    {'target_column': 'trail_48_pnl_atr_x3', 'seq_len': 20},
    {'target_column': 'trail_48_pnl_atr_x3', 'seq_len': 50},
    {'target_column': 'trail_48_pnl_atr_x3', 'seq_len': 100},
    {'target_column': 'trail_48_pnl_atr_x5', 'seq_len': 20},
    {'target_column': 'trail_48_pnl_atr_x5', 'seq_len': 50},
    {'target_column': 'trail_48_pnl_atr_x5', 'seq_len': 100},
]
DEFAULT_THRESHOLD_QUANTILES = (0.80, 0.85, 0.90, 0.95, 0.975)


def config_slug(target_column: str, seq_len: int) -> str:
    return f'{target_column}_seq{seq_len}'


def _jsonable(value):
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, 'tolist'):
        return value.tolist()
    if hasattr(value, 'item'):
        return value.item()
    return value


def _copy_if_exists(source: Path, destination: Path) -> None:
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _active_rows(frame: pd.DataFrame) -> pd.DataFrame:
    signal = pd.to_numeric(frame.get('signal', 0), errors='coerce').fillna(0).astype(int)
    return frame.loc[signal != 0].copy()


def _candidate_table(
    frame: pd.DataFrame,
    target_column: str,
    quantiles: tuple[float, ...] = DEFAULT_THRESHOLD_QUANTILES,
) -> pd.DataFrame:
    active = _active_rows(frame)
    score_col = f'pred_{target_column}'
    true_pnl_col = f'true_{target_column}'
    if active.empty:
        return pd.DataFrame(columns=['candidate', 'threshold', 'trades', 'gross_profit', 'gross_loss', 'pf', 'ulcer_index_atr'])

    thresholds = sorted(
        {float(active[score_col].quantile(q)) for q in quantiles},
        reverse=True,
    )
    rows = [summarize_candidate(active, score_col=score_col, threshold=threshold, true_pnl_col=true_pnl_col) for threshold in thresholds]
    return pd.DataFrame(rows)


def run_benchmark(
    *,
    validation_csv: Path,
    test_csv: Path,
    target_column: str,
    output_dir: Path,
    min_pf: float,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    validation = pd.read_csv(validation_csv, sep=';')
    test = pd.read_csv(test_csv, sep=';')

    validation_table = _candidate_table(validation, target_column)
    validation_table.to_csv(output_dir / 'validation_grid.csv', sep=';', index=False)

    winner = pick_validation_winner(validation_table, min_pf=min_pf)
    final_verdict: dict[str, object] = {
        'verdict': 'reject',
        'target_column': target_column,
        'validation_winner': None,
        'test_result': None,
    }
    if winner is not None:
        test_result = summarize_candidate(
            _active_rows(test),
            score_col=f'pred_{target_column}',
            threshold=float(winner['threshold']),
            true_pnl_col=f'true_{target_column}',
        )
        final_verdict = {
            'verdict': 'go',
            'target_column': target_column,
            'validation_winner': _jsonable(winner.to_dict()),
            'test_result': _jsonable(test_result),
        }

    final_verdict_path = output_dir / 'final_verdict.json'
    final_verdict_path.write_text(json.dumps(_jsonable(final_verdict), ensure_ascii=False, indent=2), encoding='utf-8')
    return {
        'validation_grid_path': str(output_dir / 'validation_grid.csv'),
        'final_verdict_path': str(final_verdict_path),
        'final_verdict': final_verdict,
    }


def run_single_config(
    *,
    target_column: str,
    seq_len: int,
    output_dir: Path,
    epochs: int,
    patience: int,
    batch_size: int,
    seed: int,
    min_pf: float,
    skip_existing: bool,
) -> dict[str, object]:
    slug = config_slug(target_column, seq_len)
    run_dir = output_dir / slug
    run_dir.mkdir(parents=True, exist_ok=True)

    summary_path = run_dir / 'summary.json'
    if skip_existing and summary_path.exists():
        return json.loads(summary_path.read_text(encoding='utf-8'))

    started_at = time.time()
    train_result = train_model(
        model_name='transformer',
        task=TRAILING_STOP_TARGET,
        epochs=epochs,
        batch_size=batch_size,
        lr=1e-3,
        weight_decay=1e-4,
        patience=patience,
        seed=seed,
        use_scaler=False,
        use_weighted_sampler=False,
        seq_len=seq_len,
        clear_cache=False,
        silent=False,
        model_kwargs={},
    )

    suffix = task_checkpoint_suffix(TRAILING_STOP_TARGET)
    checkpoint_path = CHECKPOINTS_DIR / f'transformer{suffix}_best.pt'
    run_checkpoint_path = run_dir / 'checkpoint.pt'
    _copy_if_exists(checkpoint_path, run_checkpoint_path)

    run_evaluation(
        model_name='transformer',
        checkpoint_path=str(run_checkpoint_path),
        task=TRAILING_STOP_TARGET,
        seed=seed,
    )
    _copy_if_exists(REPORTS_DIR / 'evaluate_test_trailing_stop_target_v1.md', run_dir / 'evaluate_test_trailing_stop_target_v1.md')
    _copy_if_exists(REPORTS_DIR / 'trailing_stop_target_test_predictions.csv', run_dir / 'trailing_stop_target_test_predictions.csv')

    export_prefix = run_dir / 'trailing_stop_target'
    generate_signals(
        model_name='transformer',
        task=TRAILING_STOP_TARGET,
        seed=seed,
        research_out_prefix=str(export_prefix),
    )

    validation_csv = run_dir / 'trailing_stop_target_validation_predictions.csv'
    test_csv = run_dir / 'trailing_stop_target_test_predictions.csv'
    benchmark = run_benchmark(
        validation_csv=validation_csv,
        test_csv=test_csv,
        target_column=target_column,
        output_dir=run_dir / 'benchmark',
        min_pf=min_pf,
    )

    payload = {
        'config': {
            'target_column': target_column,
            'seq_len': seq_len,
            'epochs': epochs,
            'patience': patience,
            'batch_size': batch_size,
            'seed': seed,
        },
        'train_result': _jsonable(train_result),
        'checkpoint_path': str(run_checkpoint_path),
        'exports': {
            'validation_csv': str(validation_csv),
            'test_csv': str(test_csv),
        },
        'benchmark': _jsonable(benchmark),
        'runtime_sec': time.time() - started_at,
    }
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run bounded trailing-stop target matrix.')
    parser.add_argument('--output-dir', default='ML/reports/trailing_stop_target_matrix')
    parser.add_argument('--epochs', type=int, default=3)
    parser.add_argument('--patience', type=int, default=2)
    parser.add_argument('--batch-size', type=int, default=256)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--min-pf', type=float, default=1.0)
    parser.add_argument('--configs', nargs='*', default=None, help='Optional list of config slugs to run.')
    parser.add_argument('--skip-existing', action='store_true')
    return parser.parse_args()


def main() -> dict[str, object]:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    selected = set(args.configs or [])
    matrix = [
        row for row in DEFAULT_MATRIX_CONFIGS
        if not selected or config_slug(row['target_column'], row['seq_len']) in selected
    ]

    runs: list[dict[str, object]] = []
    for row in matrix:
        runs.append(
            run_single_config(
                target_column=row['target_column'],
                seq_len=row['seq_len'],
                output_dir=output_dir,
                epochs=args.epochs,
                patience=args.patience,
                batch_size=args.batch_size,
                seed=args.seed,
                min_pf=args.min_pf,
                skip_existing=args.skip_existing,
            )
        )

    manifest = {
        'configs': [config_slug(row['target_column'], row['seq_len']) for row in matrix],
        'runs': runs,
    }
    (output_dir / 'manifest.json').write_text(json.dumps(_jsonable(manifest), ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(_jsonable(manifest), ensure_ascii=False, indent=2))
    return manifest


if __name__ == '__main__':
    main()
