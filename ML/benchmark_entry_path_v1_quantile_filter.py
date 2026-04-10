import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ML.entry_path_trade_filter import compute_pf


DEFAULT_VALIDATION_CSV = Path('ML/reports/entry_path_v1_quantile_validation_predictions.csv')
DEFAULT_TEST_CSV = Path('ML/reports/entry_path_v1_quantile_test_predictions.csv')
DEFAULT_BASELINE_RULE = Path('ML/reports/entry_path_trade_filter_selected_rule.json')
DEFAULT_OUTPUT_DIR = Path('ML/reports')
DEFAULT_ALPHA = 0.10
DEFAULT_MIN_TRADES = 10


def load_prediction_frame(path) -> pd.DataFrame:
    frame = pd.read_csv(Path(path), sep=';')
    frame['time'] = pd.to_datetime(frame['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    return frame


def load_baseline_rule(path) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def attach_baseline_score(frame: pd.DataFrame, baseline_frame: pd.DataFrame) -> pd.DataFrame:
    joined = frame.merge(
        baseline_frame[['time', 'signal', 'pred_ret_24_dir_atr']].rename(
            columns={'pred_ret_24_dir_atr': 'baseline_score'}
        ),
        on=['time', 'signal'],
        how='inner',
    )
    joined['baseline_selected'] = False
    return joined


def compute_conformal_correction(
    true_ret,
    pred_q10,
    pred_q90,
    alpha: float = DEFAULT_ALPHA,
) -> float:
    true_ret = np.asarray(true_ret, dtype=np.float64).reshape(-1)
    pred_q10 = np.asarray(pred_q10, dtype=np.float64).reshape(-1)
    pred_q90 = np.asarray(pred_q90, dtype=np.float64).reshape(-1)
    if len(true_ret) == 0:
        return 0.0

    lower = np.minimum(pred_q10, pred_q90)
    upper = np.maximum(pred_q10, pred_q90)
    scores = np.maximum(lower - true_ret, true_ret - upper)
    scores = np.maximum(scores, 0.0)
    level = min((1.0 - alpha) * (1.0 + 1.0 / len(scores)), 1.0)
    return float(np.quantile(scores, level, method='higher'))


def apply_conformal_correction(frame: pd.DataFrame, correction: float) -> pd.DataFrame:
    out = frame.copy()
    out['lb'] = np.minimum(out['pred_ret_24_q10'], out['pred_ret_24_q90']) - correction
    out['ub'] = np.maximum(out['pred_ret_24_q10'], out['pred_ret_24_q90']) + correction
    out['width'] = out['ub'] - out['lb']
    return out


def build_rule_mask(frame: pd.DataFrame, rule: str, m: float, w: float) -> pd.Series:
    if rule == 'baseline':
        return frame['baseline_selected']
    if rule == 'lb_gt_0':
        return frame['baseline_selected'] & (frame['lb'] > 0.0)
    if rule == 'lb_gt_m':
        return frame['baseline_selected'] & (frame['lb'] > m)
    if rule == 'lb_gt_m_width_le_w':
        return frame['baseline_selected'] & (frame['lb'] > m) & (frame['width'] <= w)
    raise ValueError(f'Unknown rule: {rule}')


def summarize_rule(frame: pd.DataFrame, candidate: str, rule: str, m: float, w: float) -> dict[str, object]:
    selected_mask = build_rule_mask(frame, rule=rule, m=m, w=w)
    selected = frame.loc[selected_mask].copy()
    pnl = selected['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
    trades = int(len(selected))
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = float(-pnl[pnl < 0].sum())
    pf = compute_pf(pnl)
    win_rate = float((pnl > 0).mean()) if trades > 0 else 0.0
    mean_pnl_atr = float(pnl.mean()) if trades > 0 else 0.0
    coverage = float(trades / int(frame['baseline_selected'].sum())) if int(frame['baseline_selected'].sum()) > 0 else 0.0
    median_interval_width = float(selected['width'].median()) if trades > 0 else 0.0

    return {
        'candidate': candidate,
        'rule': rule,
        'm': float(m),
        'w': float(w),
        'trades': trades,
        'pf': pf,
        'win_rate': win_rate,
        'mean_pnl_atr': mean_pnl_atr,
        'coverage': coverage,
        'median_interval_width': median_interval_width,
        'gross_profit': gross_profit,
        'gross_loss': gross_loss,
    }


def pick_winner(table: pd.DataFrame, min_trades: int = DEFAULT_MIN_TRADES) -> pd.Series:
    live = table[table['trades'] >= min_trades].copy()
    if live.empty:
        live = table.copy()
    return live.sort_values(
        ['pf', 'trades', 'median_interval_width'],
        ascending=[False, False, True],
    ).iloc[0]


def build_report_markdown(validation_best: dict, test_row: dict, baseline_rule_path: str, alpha: float) -> str:
    return '\n'.join([
        '# Entry Path v1 Quantile Filter Report',
        '',
        f"Победитель: **{validation_best.get('candidate', 'N/A')}**",
        '',
        '## Validation Winner',
        '',
        f"- candidate: `{validation_best.get('candidate', 'N/A')}`",
        f"- rule: `{validation_best.get('rule', 'N/A')}`",
        f"- pf: **{float(validation_best.get('pf', 0.0)):.4f}**",
        f"- trades: **{int(validation_best.get('trades', 0))}**",
        f"- coverage: **{float(validation_best.get('coverage', 0.0)):.2%}**",
        f"- median_interval_width: **{float(validation_best.get('median_interval_width', 0.0)):.4f}**",
        '',
        '## Test Check',
        '',
        f"- candidate: `{test_row.get('candidate', 'N/A')}`",
        f"- rule: `{test_row.get('rule', 'N/A')}`",
        f"- pf: **{float(test_row.get('pf', 0.0)):.4f}**",
        f"- trades: **{int(test_row.get('trades', 0))}**",
        f"- coverage: **{float(test_row.get('coverage', 0.0)):.2%}**",
        f"- median_interval_width: **{float(test_row.get('median_interval_width', 0.0)):.4f}**",
        '',
        '## Frozen Rule',
        '',
        f'- baseline_rule: `{baseline_rule_path}`',
        f'- alpha: **{alpha:.2f}**',
    ])


def run_benchmark(
    validation_csv: str | Path,
    test_csv: str | Path,
    baseline_rule: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    alpha: float = DEFAULT_ALPHA,
    min_trades: int = DEFAULT_MIN_TRADES,
) -> dict:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    validation_frame = load_prediction_frame(validation_csv)
    test_frame = load_prediction_frame(test_csv)
    baseline_rule_data = load_baseline_rule(baseline_rule)

    baseline_validation = load_prediction_frame(baseline_rule_data['validation_csv'])
    baseline_test = load_prediction_frame(baseline_rule_data['test_csv'])
    baseline_threshold = float(baseline_rule_data['winner']['score_threshold'])
    baseline_candidate = baseline_rule_data['winner'].get('candidate', 'A')

    validation = attach_baseline_score(validation_frame, baseline_validation)
    test = attach_baseline_score(test_frame, baseline_test)

    validation['baseline_selected'] = (
        (validation['signal'].to_numpy() != 0)
        & (validation['baseline_score'].to_numpy(dtype=np.float64) >= baseline_threshold)
    )
    test['baseline_selected'] = (
        (test['signal'].to_numpy() != 0)
        & (test['baseline_score'].to_numpy(dtype=np.float64) >= baseline_threshold)
    )

    validation_selected = validation.loc[validation['baseline_selected']].copy()
    correction = compute_conformal_correction(
        validation_selected['true_ret_24_dir_atr'].to_numpy(dtype=np.float64),
        validation_selected['pred_ret_24_q10'].to_numpy(dtype=np.float64),
        validation_selected['pred_ret_24_q90'].to_numpy(dtype=np.float64),
        alpha=alpha,
    )

    validation = apply_conformal_correction(validation, correction)
    test = apply_conformal_correction(test, correction)

    validation_base_mask = validation['baseline_selected']
    validation_m = float(validation.loc[validation_base_mask, 'lb'].median()) if validation_base_mask.any() else 0.0
    validation_w = float(validation.loc[validation_base_mask, 'width'].median()) if validation_base_mask.any() else 0.0

    validation_summary = pd.DataFrame([
        summarize_rule(validation, candidate='baseline', rule='baseline', m=validation_m, w=validation_w),
        summarize_rule(validation, candidate='lb_gt_0', rule='lb_gt_0', m=validation_m, w=validation_w),
        summarize_rule(validation, candidate='lb_gt_m', rule='lb_gt_m', m=validation_m, w=validation_w),
        summarize_rule(validation, candidate='lb_gt_m_width_le_w', rule='lb_gt_m_width_le_w', m=validation_m, w=validation_w),
    ])

    winner = pick_winner(validation_summary, min_trades=min_trades).to_dict()

    frozen_test_row = summarize_rule(
        test,
        candidate=winner['candidate'],
        rule=winner['rule'],
        m=winner['m'],
        w=winner['w'],
    )
    test_summary = pd.DataFrame([frozen_test_row])

    validation_summary_path = output_path / 'entry_path_v1_quantile_filter_validation_summary.csv'
    test_summary_path = output_path / 'entry_path_v1_quantile_filter_test_summary.csv'
    rule_path = output_path / 'entry_path_v1_quantile_filter_selected_rule.json'
    report_path = output_path / 'entry_path_v1_quantile_filter_report.md'

    validation_summary.to_csv(validation_summary_path, sep=';', index=False)
    test_summary.to_csv(test_summary_path, sep=';', index=False)

    payload = {
        'winner': winner,
        'frozen_winner': frozen_test_row,
        'baseline_rule_path': str(baseline_rule),
        'baseline_candidate': baseline_candidate,
        'baseline_threshold': baseline_threshold,
        'alpha': float(alpha),
        'correction': float(correction),
        'validation_csv': str(validation_csv),
        'test_csv': str(test_csv),
        'validation_summary_path': str(validation_summary_path),
        'test_summary_path': str(test_summary_path),
        'validation_m': float(validation_m),
        'validation_w': float(validation_w),
    }
    rule_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    report_path.write_text(
        build_report_markdown(
            validation_best=winner,
            test_row=frozen_test_row,
            baseline_rule_path=str(baseline_rule),
            alpha=alpha,
        ),
        encoding='utf-8',
    )

    return payload


def parse_args():
    parser = argparse.ArgumentParser(description='Benchmark quantile filter on top of frozen entry_path baseline.')
    parser.add_argument('--validation-csv', default=str(DEFAULT_VALIDATION_CSV))
    parser.add_argument('--test-csv', default=str(DEFAULT_TEST_CSV))
    parser.add_argument('--baseline-rule', dest='baseline_rule', default=str(DEFAULT_BASELINE_RULE))
    parser.add_argument('--output-dir', default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument('--alpha', type=float, default=DEFAULT_ALPHA)
    parser.add_argument('--min-trades', type=int, default=DEFAULT_MIN_TRADES)
    return parser.parse_args()


def main():
    args = parse_args()
    payload = run_benchmark(
        validation_csv=args.validation_csv,
        test_csv=args.test_csv,
        baseline_rule=args.baseline_rule,
        output_dir=args.output_dir,
        alpha=args.alpha,
        min_trades=args.min_trades,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


if __name__ == '__main__':
    main()
