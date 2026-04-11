import argparse
import json
from pathlib import Path

from ML.triple_barrier_mt4_execution import (
    build_yearly_summary,
    load_labeled_frame,
    load_tb_signals,
    simulate_mt4_tb,
)


def run_benchmark(
    signals_path: str | Path,
    labeled_path: str | Path,
    rule_json: str | Path,
    output_trades: str | Path,
    output_summary: str | Path,
    output_yearly: str | Path,
) -> dict[str, object]:
    rule = json.loads(Path(rule_json).read_text(encoding='utf-8'))
    signals = load_tb_signals(signals_path, theta=rule.get('theta', 0.0), min_ev=rule.get('min_ev', 0.0))
    labeled = load_labeled_frame(labeled_path)
    trades, summary = simulate_mt4_tb(signals, labeled)
    yearly = build_yearly_summary(trades)

    Path(output_trades).parent.mkdir(parents=True, exist_ok=True)
    Path(output_summary).parent.mkdir(parents=True, exist_ok=True)
    Path(output_yearly).parent.mkdir(parents=True, exist_ok=True)

    trades.to_csv(output_trades, sep=';', index=False)
    yearly.to_csv(output_yearly, sep=';', index=False)
    Path(output_summary).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return summary


def parse_args():
    parser = argparse.ArgumentParser(description='Run MT4-matched TB evaluation in Python.')
    parser.add_argument('--signals', dest='signals_path', required=True)
    parser.add_argument('--labeled', dest='labeled_path', required=True)
    parser.add_argument('--rule-json', required=True)
    parser.add_argument('--output-trades', required=True)
    parser.add_argument('--output-summary', required=True)
    parser.add_argument('--output-yearly', required=True)
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
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


if __name__ == '__main__':
    main()
