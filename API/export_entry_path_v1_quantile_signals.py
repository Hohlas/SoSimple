import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


RULE_JSON = 'entry_path_v1_quantile_filter_selected_rule.json'
MT4_TESTER_SIGNALS = Path('MT/tester/files/ml_signals.csv')
MT4_RUNTIME_SIGNALS = Path('MT/MQL4/Files/ml_signals.csv')


def load_prediction_frame(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(Path(path), sep=';')
    return frame.drop_duplicates(subset=['time'], keep='last').reset_index(drop=True)


def load_rule_payload(seed_dir: str | Path) -> dict:
    rule_path = Path(seed_dir) / RULE_JSON
    return json.loads(rule_path.read_text(encoding='utf-8'))


def load_rule_payload_from_file(rule_path: str | Path) -> dict:
    """Load production rule JSON and normalize to the legacy shape used by apply_frozen_rule.

    Production file stores correction inside winner; legacy file stores it at root.
    """
    raw = json.loads(Path(rule_path).read_text(encoding='utf-8'))
    winner = raw['winner']
    return {
        'correction': float(winner['correction']),
        'baseline_threshold': float(raw['baseline_threshold']),
        'winner': {
            'candidate': winner.get('candidate', winner.get('rule', '')),
            'rule': winner['rule'],
            'm': float(winner.get('m', 0.0)),
            'w': float(winner.get('w', 0.0)),
        },
    }


def apply_production_rule(
    frame: pd.DataFrame,
    baseline_frame: pd.DataFrame,
    rule_payload: dict,
) -> pd.Series:
    """Apply frozen production rule using baseline model's score column.

    Unlike the legacy per-seed path which reuses the quantile model's own
    pred_ret_24_dir_atr as score, production logic mirrors the research
    benchmark: baseline_score is sourced from the baseline predictions frame
    via (time, signal) inner join.
    """
    from ML.benchmark_entry_path_v1_quantile_filter import (
        attach_baseline_score,
        apply_conformal_correction,
        build_rule_mask,
    )

    correction = float(rule_payload['correction'])
    baseline_threshold = float(rule_payload['baseline_threshold'])
    winner = rule_payload['winner']
    rule = winner['rule']
    m = float(winner.get('m', 0.0))
    w = float(winner.get('w', 0.0))

    frame_dt = frame.copy()
    if not pd.api.types.is_datetime64_any_dtype(frame_dt['time']):
        frame_dt['time'] = pd.to_datetime(frame_dt['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    baseline_dt = baseline_frame.copy()
    if not pd.api.types.is_datetime64_any_dtype(baseline_dt['time']):
        baseline_dt['time'] = pd.to_datetime(baseline_dt['time'], format='%Y.%m.%d %H:%M', errors='coerce')

    joined = attach_baseline_score(frame_dt, baseline_dt)
    joined['baseline_selected'] = (
        (joined['signal'].to_numpy() != 0)
        & (joined['baseline_score'].to_numpy(dtype=np.float64) >= baseline_threshold)
    )
    joined = apply_conformal_correction(joined, correction)
    mask = build_rule_mask(joined, rule=rule, m=m, w=w)
    selected_keys = set(zip(
        joined.loc[mask, 'time'].tolist(),
        joined.loc[mask, 'signal'].tolist(),
    ))
    keys = list(zip(frame_dt['time'].tolist(), frame_dt['signal'].tolist()))
    return pd.Series([k in selected_keys for k in keys], index=frame.index)


def apply_frozen_rule(frame: pd.DataFrame, rule_payload: dict) -> pd.Series:
    out = frame.copy()
    correction = float(rule_payload['correction'])
    baseline_threshold = float(rule_payload['baseline_threshold'])
    winner = rule_payload['winner']
    rule = winner['rule']
    m = float(winner.get('m', 0.0))
    w = float(winner.get('w', 0.0))

    out['lb'] = np.minimum(out['pred_ret_24_q10'], out['pred_ret_24_q90']) - correction
    out['ub'] = np.maximum(out['pred_ret_24_q10'], out['pred_ret_24_q90']) + correction
    out['width'] = out['ub'] - out['lb']
    baseline_selected = (
        (out['signal'].to_numpy() != 0)
        & (out['pred_ret_24_dir_atr'].to_numpy(dtype=np.float64) >= baseline_threshold)
    )

    if rule == 'lb_gt_m':
        return pd.Series(baseline_selected & (out['lb'] > m), index=out.index)
    if rule == 'baseline':
        return pd.Series(baseline_selected, index=out.index)
    if rule == 'lb_gt_0':
        return pd.Series(baseline_selected & (out['lb'] > 0.0), index=out.index)
    if rule == 'lb_gt_m_width_le_w':
        return pd.Series(baseline_selected & (out['lb'] > m) & (out['width'] <= w), index=out.index)
    raise ValueError(f'Unknown rule: {rule}')


def _resolve_baseline_predictions_path(rule_path: Path, split: str) -> Path:
    raw = json.loads(Path(rule_path).read_text(encoding='utf-8'))
    baseline_rule_path = Path(raw['baseline_rule_path'])
    baseline_raw = json.loads(baseline_rule_path.read_text(encoding='utf-8'))
    key = 'test_csv' if split == 'test' else 'validation_csv'
    return Path(baseline_raw[key])


def export_signals(
    seed_dir: str | Path,
    split: str,
    output_path: str | Path,
    copy_to_mt4: bool = False,
    rule_path: str | Path | None = None,
    baseline_predictions_path: str | Path | None = None,
) -> Path:
    seed_root = Path(seed_dir)
    frame_path = seed_root / f'entry_path_v1_quantile_{split}_predictions.csv'

    if rule_path is not None:
        rule_payload = load_rule_payload_from_file(rule_path)
        if baseline_predictions_path is None:
            baseline_predictions_path = _resolve_baseline_predictions_path(Path(rule_path), split)
        # Production path: preserve duplicate (time, signal) rows so mixed-signal
        # bars are not silently lost in pre-merge deduplication.
        raw_frame = pd.read_csv(Path(frame_path), sep=';')
        baseline_frame = pd.read_csv(Path(baseline_predictions_path), sep=';')
        selected_mask = apply_production_rule(raw_frame, baseline_frame, rule_payload)

        out = raw_frame[['time', 'signal']].copy()
        out.loc[~selected_mask, 'signal'] = 0
        out['_abs'] = out['signal'].abs()
        out = (
            out.sort_values(['time', '_abs'], ascending=[True, False], kind='stable')
               .drop_duplicates(subset=['time'], keep='first')
               .drop(columns='_abs')
               .sort_values('time', kind='stable')
               .reset_index(drop=True)
        )
        export = out
    else:
        frame = load_prediction_frame(frame_path)
        rule_payload = load_rule_payload(seed_root)
        selected_mask = apply_frozen_rule(frame, rule_payload)
        export = frame[['time', 'signal']].copy()
        export.loc[~selected_mask, 'signal'] = 0

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(output, sep=';', index=False)

    if copy_to_mt4:
        MT4_TESTER_SIGNALS.parent.mkdir(parents=True, exist_ok=True)
        MT4_RUNTIME_SIGNALS.parent.mkdir(parents=True, exist_ok=True)
        export.to_csv(MT4_TESTER_SIGNALS, sep=';', index=False)
        export.to_csv(MT4_RUNTIME_SIGNALS, sep=';', index=False)

    return output


def parse_args():
    parser = argparse.ArgumentParser(description='Export frozen entry_path_v1_quantile signals for MT4.')
    parser.add_argument('--seed-dir', required=True)
    parser.add_argument('--split', choices=['validation', 'test'], default='test')
    parser.add_argument('--output', required=True)
    parser.add_argument('--copy-to-mt4', action='store_true')
    parser.add_argument('--rule-path', default=None,
                        help='Path to production rule JSON (e.g. entry_path_v1_quantile_selected_rule.json). '
                             'If omitted, legacy per-seed rule is used.')
    parser.add_argument('--baseline-predictions', default=None,
                        help='Optional override for baseline predictions CSV. '
                             'If omitted when --rule-path is set, it is resolved from the rule JSON.')
    return parser.parse_args()


def main():
    args = parse_args()
    path = export_signals(
        seed_dir=args.seed_dir,
        split=args.split,
        output_path=args.output,
        copy_to_mt4=args.copy_to_mt4,
        rule_path=args.rule_path,
        baseline_predictions_path=args.baseline_predictions,
    )
    print(path)
    return path


if __name__ == '__main__':
    main()
