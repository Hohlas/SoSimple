import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from API.export_entry_path_v1_quantile_signals import (
    _resolve_baseline_predictions_path,
    apply_production_rule,
    load_rule_payload_from_file,
)
from API.signal_path_atlas import build_conditioning_frame
from ML.benchmark_entry_path_v1_quantile_filter import (
    apply_conformal_correction,
    attach_baseline_score,
    build_rule_mask,
    load_prediction_frame,
    summarize_selection,
)


GATE_MIN_TRADES = 30
GATE_MIN_PF = 2.0
GATE_MIN_YEAR_TRADES = 3
DEFAULT_RULE_PATH = Path('ML/reports/entry_path_v1_quantile_selected_rule.json')
DEFAULT_SEED_DIR = Path('ML/reports/entry_path_v1_quantile_robustness/seed_007')
DEFAULT_OUTPUT_DIR = Path('ML/reports/quantile_fav_composition')
DEFAULT_SIGNAL_RESEARCH_CSV = Path('ML/reports/ml_signals_research.csv')
DEFAULT_UPDN_ACTIVE_DIR = Path('ML/reports/quantile_fav_composition/updn_active_source')
DEFAULT_FAV_THRESHOLD = 0.653


def load_signal_research_frame(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(Path(path), sep=';')
    frame['time'] = pd.to_datetime(frame['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    if 'entry_atr14' not in frame.columns:
        frame['entry_atr14'] = 1.0
    conditioned, _ = build_conditioning_frame(frame)
    return (
        conditioned[['time', 'signal', 'fav_3_vs_12']]
        .drop_duplicates(subset=['time', 'signal'], keep='last')
        .reset_index(drop=True)
    )


def load_updn_active_frame(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(Path(path), sep=';')
    frame['time'] = pd.to_datetime(frame['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    return frame[['time', 'signal', 'fav_3_vs_12']].copy()


def compose_intersection_mask(mask_q: pd.Series, mask_f: pd.Series) -> pd.Series:
    return pd.Series(mask_q.to_numpy(dtype=bool) & mask_f.to_numpy(dtype=bool), index=mask_q.index)


def compute_mode_masks(
    frame: pd.DataFrame,
    baseline_threshold: float,
    fav_threshold: float,
    rule: str,
    m: float,
    w: float,
) -> dict[str, pd.Series]:
    baseline_selected = (
        (frame['signal'].to_numpy() != 0)
        & (frame['baseline_score'].to_numpy(dtype=np.float64) >= float(baseline_threshold))
    )
    enriched = frame.copy()
    enriched['baseline_selected'] = baseline_selected
    quantile_only = build_rule_mask(enriched, rule=rule, m=float(m), w=float(w))
    fav_values = pd.to_numeric(enriched['fav_3_vs_12'], errors='coerce').to_numpy(dtype=np.float64)
    fav_only = enriched['baseline_selected'] & np.isfinite(fav_values) & (fav_values <= float(fav_threshold))
    composition = compose_intersection_mask(quantile_only, fav_only)
    return {
        'baseline': pd.Series(enriched['baseline_selected'].to_numpy(dtype=bool), index=frame.index),
        'quantile_only': pd.Series(quantile_only.to_numpy(dtype=bool), index=frame.index),
        'fav_only': pd.Series(fav_only.to_numpy(dtype=bool), index=frame.index),
        'composition': pd.Series(composition.to_numpy(dtype=bool), index=frame.index),
    }


def materialize_export_frame(frame: pd.DataFrame, selected_mask: pd.Series) -> pd.DataFrame:
    out = frame[['time', 'signal']].copy()
    out.loc[~selected_mask, 'signal'] = 0
    out['_abs'] = out['signal'].abs()
    return (
        out.sort_values(['time', '_abs'], ascending=[True, False], kind='stable')
        .drop_duplicates(subset=['time'], keep='first')
        .drop(columns='_abs')
        .sort_values('time', kind='stable')
        .reset_index(drop=True)
    )


def _seed_split_path(seed_dir: Path, split: str) -> Path:
    return seed_dir / f'entry_path_v1_quantile_{split}_predictions.csv'


def attach_fav_by_active_row_order(
    quantile_frame: pd.DataFrame,
    updn_active_frame: pd.DataFrame,
) -> pd.DataFrame:
    out = quantile_frame.copy()
    out['fav_3_vs_12'] = np.nan
    active_mask = out['signal'].to_numpy() != 0
    active = out.loc[active_mask, ['time', 'signal']].reset_index(drop=True)
    source = updn_active_frame[['time', 'signal', 'fav_3_vs_12']].reset_index(drop=True)
    if len(active) != len(source) or not active.equals(source[['time', 'signal']]):
        raise ValueError('Aligned active updn source does not match quantile active row order')
    out.loc[active_mask, 'fav_3_vs_12'] = source['fav_3_vs_12'].to_numpy(dtype=np.float64)
    return out


def _build_joined_frame(
    quantile_frame: pd.DataFrame,
    baseline_frame: pd.DataFrame,
    fav_source: pd.DataFrame,
    rule_payload: dict,
    fav_source_mode: str,
) -> pd.DataFrame:
    if fav_source_mode == 'aligned_updn_active':
        quantile_frame = attach_fav_by_active_row_order(quantile_frame, fav_source)
    else:
        quantile_frame = quantile_frame.merge(fav_source, on=['time', 'signal'], how='left')
    joined = attach_baseline_score(quantile_frame, baseline_frame)
    joined['baseline_selected'] = (
        (joined['signal'].to_numpy() != 0)
        & (joined['baseline_score'].to_numpy(dtype=np.float64) >= float(rule_payload['baseline_threshold']))
    )
    joined = apply_conformal_correction(joined, float(rule_payload['correction']))
    return joined


def _build_raw_quantile_mask(
    raw_quantile_frame: pd.DataFrame,
    baseline_frame: pd.DataFrame,
    rule_payload: dict,
) -> pd.Series:
    return apply_production_rule(raw_quantile_frame, baseline_frame, rule_payload)


def _summarize_modes(
    joined_frame: pd.DataFrame,
    masks: dict[str, pd.Series],
    mode_labels: dict[str, str],
) -> dict[str, dict]:
    out = {}
    for mode, mask in masks.items():
        summary = summarize_selection(joined_frame, mask, candidate=mode_labels[mode])
        summary['rule'] = mode
        out[mode] = summary
    return out


def _yearly_breakdown(joined_frame: pd.DataFrame, masks: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    for mode, mask in masks.items():
        selected = joined_frame.loc[mask].copy()
        if selected.empty:
            continue
        selected['year'] = selected['time'].dt.year
        for year, group in selected.groupby('year'):
            pnl = group['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
            gross_profit = float(pnl[pnl > 0].sum())
            gross_loss = float(-pnl[pnl < 0].sum())
            rows.append({
                'year': int(year),
                'mode': mode,
                'N': int(len(group)),
                'wins': int((pnl > 0).sum()),
                'losses': int((pnl < 0).sum()),
                'gross_profit': gross_profit,
                'gross_loss': gross_loss,
                'pf': None if gross_loss == 0.0 else gross_profit / gross_loss,
            })
    return pd.DataFrame(rows).sort_values(['year', 'mode']).reset_index(drop=True)


def count_negative_year_slices_from_trades(
    test_frame: pd.DataFrame,
    selected_mask: pd.Series,
    min_year_trades: int = GATE_MIN_YEAR_TRADES,
) -> int:
    selected = test_frame.loc[selected_mask].copy()
    if selected.empty:
        return 0
    selected['year'] = selected['time'].dt.year
    total = 0
    for _, group in selected.groupby('year'):
        if len(group) < min_year_trades:
            continue
        pnl = group['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
        if pnl.sum() < 0:
            total += 1
    return total


def _evaluate_gate(n_trades: int, pf: float, negative_year_slices: int) -> dict:
    reasons = []
    if n_trades < GATE_MIN_TRADES:
        reasons.append(f'n_trades={n_trades} < {GATE_MIN_TRADES}')
    if pf < GATE_MIN_PF:
        reasons.append(f'pf={pf:.2f} < {GATE_MIN_PF}')
    if negative_year_slices > 0:
        reasons.append(f'negative_year_slices={negative_year_slices} > 0')
    verdict = 'gate_fail'
    if n_trades < GATE_MIN_TRADES:
        verdict = 'gate_inconclusive'
    elif not reasons:
        verdict = 'gate_pass'
    return {
        'verdict': verdict,
        'n_trades': int(n_trades),
        'pf': float(pf),
        'negative_year_slices': int(negative_year_slices),
        'reasons': reasons,
    }


def _safe_git_head() -> str:
    result = subprocess.run(
        ['git', 'rev-parse', 'HEAD'],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def run_benchmark(
    rule_path: str | Path,
    seed_dir: str | Path,
    fav_threshold: float,
    output_dir: str | Path,
    signal_research_csv: str | Path = DEFAULT_SIGNAL_RESEARCH_CSV,
    updn_active_dir: str | Path | None = None,
) -> dict:
    rule_path = Path(rule_path)
    seed_dir = Path(seed_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rule_payload = load_rule_payload_from_file(rule_path)
    baseline_validation_path = _resolve_baseline_predictions_path(rule_path, 'validation')
    baseline_test_path = _resolve_baseline_predictions_path(rule_path, 'test')

    quantile_validation_path = _seed_split_path(seed_dir, 'validation')
    quantile_test_path = _seed_split_path(seed_dir, 'test')

    quantile_validation = load_prediction_frame(quantile_validation_path)
    quantile_test = load_prediction_frame(quantile_test_path)
    baseline_validation = load_prediction_frame(baseline_validation_path)
    baseline_test = load_prediction_frame(baseline_test_path)
    if updn_active_dir is not None:
        updn_active_dir = Path(updn_active_dir)
        validation_fav_source = load_updn_active_frame(updn_active_dir / 'validation_active_updn_predictions.csv')
        test_fav_source = load_updn_active_frame(updn_active_dir / 'test_active_updn_predictions.csv')
        fav_source_mode = 'aligned_updn_active'
    else:
        validation_fav_source = load_signal_research_frame(signal_research_csv)
        test_fav_source = validation_fav_source
        fav_source_mode = 'signal_research'

    validation = _build_joined_frame(
        quantile_validation, baseline_validation, validation_fav_source, rule_payload, fav_source_mode
    )
    test = _build_joined_frame(
        quantile_test, baseline_test, test_fav_source, rule_payload, fav_source_mode
    )

    winner = rule_payload['winner']
    validation_masks = compute_mode_masks(
        frame=validation,
        baseline_threshold=float(rule_payload['baseline_threshold']),
        fav_threshold=fav_threshold,
        rule=winner['rule'],
        m=float(winner.get('m', 0.0)),
        w=float(winner.get('w', 0.0)),
    )
    test_masks = compute_mode_masks(
        frame=test,
        baseline_threshold=float(rule_payload['baseline_threshold']),
        fav_threshold=fav_threshold,
        rule=winner['rule'],
        m=float(winner.get('m', 0.0)),
        w=float(winner.get('w', 0.0)),
    )

    mode_labels = {
        'baseline': 'baseline',
        'quantile_only': 'quantile_only',
        'fav_only': 'fav_only',
        'composition': 'composition',
    }
    validation_metrics = _summarize_modes(validation, validation_masks, mode_labels)
    test_metrics = _summarize_modes(test, test_masks, mode_labels)
    yearly_breakdown = _yearly_breakdown(test, test_masks)

    composition_mask = test_masks['composition']
    negative_year_slices = count_negative_year_slices_from_trades(test, composition_mask)
    n_boost_gate = _evaluate_gate(
        n_trades=test_metrics['composition']['trades'],
        pf=test_metrics['composition']['pf'],
        negative_year_slices=negative_year_slices,
    )

    intersection_diagnostic = {
        'n_quantile': int(test_masks['quantile_only'].sum()),
        'n_fav': int(test_masks['fav_only'].sum()),
        'n_intersection': int(test_masks['composition'].sum()),
        'n_rows_with_fav_feature': int(test['fav_3_vs_12'].notna().sum()),
        'n_baseline_rows_with_fav_feature': int((test['baseline_selected'] & test['fav_3_vs_12'].notna()).sum()),
    }
    intersection_diagnostic['intersection_over_quantile'] = (
        intersection_diagnostic['n_intersection'] / intersection_diagnostic['n_quantile']
        if intersection_diagnostic['n_quantile'] > 0 else 0.0
    )
    intersection_diagnostic['intersection_over_fav'] = (
        intersection_diagnostic['n_intersection'] / intersection_diagnostic['n_fav']
        if intersection_diagnostic['n_fav'] > 0 else 0.0
    )
    intersection_diagnostic['trades_lost_from_quantile'] = (
        intersection_diagnostic['n_quantile'] - intersection_diagnostic['n_intersection']
    )

    raw_quantile_test = pd.read_csv(quantile_test_path, sep=';')
    raw_quantile_test_mask = _build_raw_quantile_mask(raw_quantile_test, pd.read_csv(baseline_test_path, sep=';'), rule_payload)
    quantile_export = materialize_export_frame(raw_quantile_test, raw_quantile_test_mask)

    run_metadata = {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'git_head': _safe_git_head(),
        'config': {
            'rule_path': str(rule_path),
            'seed_dir': str(seed_dir),
            'fav_threshold': float(fav_threshold),
            'output_dir': str(output_dir),
            'signal_research_csv': str(signal_research_csv),
            'updn_active_dir': str(updn_active_dir) if updn_active_dir is not None else None,
            'fav_source_mode': fav_source_mode,
        },
        'inputs': {
            'quantile_validation_csv': str(quantile_validation_path),
            'quantile_test_csv': str(quantile_test_path),
            'baseline_validation_csv': str(baseline_validation_path),
            'baseline_test_csv': str(baseline_test_path),
        },
        'rule_snapshot': json.loads(rule_path.read_text(encoding='utf-8')),
        'quantile_test_export_rows': int(len(quantile_export)),
        'quantile_test_export_nonzero': int((quantile_export['signal'] != 0).sum()),
    }

    (output_dir / 'run_metadata.json').write_text(json.dumps(run_metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    (output_dir / 'validation_metrics.json').write_text(json.dumps(validation_metrics, ensure_ascii=False, indent=2), encoding='utf-8')
    (output_dir / 'test_metrics.json').write_text(json.dumps(test_metrics, ensure_ascii=False, indent=2), encoding='utf-8')
    (output_dir / 'intersection_diagnostic.json').write_text(json.dumps(intersection_diagnostic, ensure_ascii=False, indent=2), encoding='utf-8')
    (output_dir / 'n_boost_composition.json').write_text(json.dumps(n_boost_gate, ensure_ascii=False, indent=2), encoding='utf-8')
    yearly_breakdown.to_csv(output_dir / 'yearly_breakdown_test.csv', sep=';', index=False)

    return {
        'validation_metrics': validation_metrics,
        'test_metrics': test_metrics,
        'intersection_diagnostic': intersection_diagnostic,
        'n_boost_composition': n_boost_gate,
        'yearly_breakdown_test': yearly_breakdown,
    }


def parse_args():
    parser = argparse.ArgumentParser(description='Benchmark quantile × fav_3_vs_12 composition.')
    parser.add_argument('--rule-path', default=str(DEFAULT_RULE_PATH))
    parser.add_argument('--seed-dir', default=str(DEFAULT_SEED_DIR))
    parser.add_argument('--fav-threshold', type=float, default=DEFAULT_FAV_THRESHOLD)
    parser.add_argument('--output-dir', default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument('--signal-research-csv', default=str(DEFAULT_SIGNAL_RESEARCH_CSV))
    parser.add_argument('--updn-active-dir', default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    payload = run_benchmark(
        rule_path=args.rule_path,
        seed_dir=args.seed_dir,
        fav_threshold=args.fav_threshold,
        output_dir=args.output_dir,
        signal_research_csv=args.signal_research_csv,
        updn_active_dir=args.updn_active_dir,
    )
    print(json.dumps({
        'validation_metrics': payload['validation_metrics'],
        'test_metrics': payload['test_metrics'],
        'intersection_diagnostic': payload['intersection_diagnostic'],
        'n_boost_composition': payload['n_boost_composition'],
    }, ensure_ascii=False, indent=2))
    return payload


if __name__ == '__main__':
    main()
