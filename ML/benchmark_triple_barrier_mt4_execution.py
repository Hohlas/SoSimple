import argparse
import json
from pathlib import Path

from ML.entry_path_trade_filter import compute_pf
from ML.triple_barrier_mt4_execution import build_yearly_summary
from ML.triple_barrier_mt4_execution import load_labeled_frame
from ML.triple_barrier_mt4_execution import load_tb_signals
from ML.triple_barrier_mt4_execution import simulate_mt4_tb


DEFAULT_SIGNALS = Path('MT/MQL4/Files/ml_signals.csv')
DEFAULT_LABELED = Path('DATA/Nero_test_labeled.csv')
DEFAULT_RULE = Path('ML/reports/tb_selected_rule.json')
DEFAULT_OUTPUT_TRADES = Path('ML/reports/tb_mt4_trades.csv')
DEFAULT_OUTPUT_YEARLY = Path('ML/reports/tb_mt4_yearly.csv')
DEFAULT_OUTPUT_SUMMARY = Path('ML/reports/tb_mt4_summary.json')


def run_benchmark(
    signals_path: str | Path,
    labeled_path: str | Path,
    rule_json: str | Path,
    output_trades: str | Path,
    output_summary: str | Path,
    output_yearly: str | Path,
    hold_bars: int = 24,
    timeout_pnl_atr: float = 0.5,
) -> dict[str, object]:
    rule = json.loads(Path(rule_json).read_text(encoding='utf-8'))
    theta = float(rule.get('theta', 0.0))
    min_ev = float(rule.get('min_ev', 0.0))

    signals = load_tb_signals(signals_path, theta=theta, min_ev=min_ev)
    labeled = load_labeled_frame(labeled_path)
    trades, meta = simulate_mt4_tb(
        signals=signals,
        labeled=labeled,
        hold_bars=hold_bars,
        timeout_pnl_atr=timeout_pnl_atr,
    )
    yearly = build_yearly_summary(trades)

    output_trades_path = Path(output_trades)
    output_summary_path = Path(output_summary)
    output_yearly_path = Path(output_yearly)
    output_trades_path.parent.mkdir(parents=True, exist_ok=True)
    output_summary_path.parent.mkdir(parents=True, exist_ok=True)
    output_yearly_path.parent.mkdir(parents=True, exist_ok=True)

    trades.to_csv(output_trades_path, sep=';', index=False)
    yearly.to_csv(output_yearly_path, sep=';', index=False)

    payload = {
        **meta,
        'theta': theta,
        'min_ev': min_ev,
        'hold_bars': int(hold_bars),
        'timeout_pnl_atr': float(timeout_pnl_atr),
        'signals_path': str(Path(signals_path)),
        'labeled_path': str(Path(labeled_path)),
        'rule_json': str(Path(rule_json)),
        'output_trades': str(output_trades_path),
        'output_yearly': str(output_yearly_path),
        'output_summary': str(output_summary_path),
        'net_pnl_atr': float(trades['pnl_atr'].sum()) if not trades.empty else 0.0,
        'gross_profit': float(trades.loc[trades['pnl_atr'] > 0, 'pnl_atr'].sum()) if not trades.empty else 0.0,
        'gross_loss': float(-trades.loc[trades['pnl_atr'] < 0, 'pnl_atr'].sum()) if not trades.empty else 0.0,
        'pf_recomputed': float(compute_pf(trades['pnl_atr'].to_numpy())) if not trades.empty else 0.0,
    }
    output_summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return payload


def parse_args():
    parser = argparse.ArgumentParser(description='Benchmark triple-barrier MT4 execution against frozen rule.')
    parser.add_argument('--signals-path', default=str(DEFAULT_SIGNALS))
    parser.add_argument('--labeled-path', default=str(DEFAULT_LABELED))
    parser.add_argument('--rule', dest='rule_json', default=str(DEFAULT_RULE))
    parser.add_argument('--output-trades', default=str(DEFAULT_OUTPUT_TRADES))
    parser.add_argument('--output-summary', default=str(DEFAULT_OUTPUT_SUMMARY))
    parser.add_argument('--output-yearly', default=str(DEFAULT_OUTPUT_YEARLY))
    parser.add_argument('--hold-bars', type=int, default=24)
    parser.add_argument('--timeout-pnl-atr', type=float, default=0.5)
    return parser.parse_args()


def main():
    args = parse_args()
    payload = run_benchmark(
        signals_path=args.signals_path,
        labeled_path=args.labeled_path,
        rule_json=args.rule_json,
        output_trades=args.output_trades,
        output_summary=args.output_summary,
        output_yearly=args.output_yearly,
        hold_bars=args.hold_bars,
        timeout_pnl_atr=args.timeout_pnl_atr,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
