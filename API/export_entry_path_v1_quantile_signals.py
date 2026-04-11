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


def export_signals(
    seed_dir: str | Path,
    split: str,
    output_path: str | Path,
    copy_to_mt4: bool = False,
) -> Path:
    seed_root = Path(seed_dir)
    frame_path = seed_root / f'entry_path_v1_quantile_{split}_predictions.csv'
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
    return parser.parse_args()


def main():
    args = parse_args()
    path = export_signals(
        seed_dir=args.seed_dir,
        split=args.split,
        output_path=args.output,
        copy_to_mt4=args.copy_to_mt4,
    )
    print(path)
    return path


if __name__ == '__main__':
    main()
