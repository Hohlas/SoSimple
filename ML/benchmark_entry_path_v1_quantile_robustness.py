import argparse
import json
from pathlib import Path

import pandas as pd

from ML.entry_path_v1_quantile_robustness import (
    build_rolling_summary,
    build_verdict,
    build_yearly_summary,
    load_seed_run,
    summarize_seed_matrix,
)


DEFAULT_ROOT_DIR = Path('ML/reports/entry_path_v1_quantile_robustness')
DEFAULT_BASELINE_RULE = Path('ML/reports/entry_path_trade_filter_selected_rule.json')
DEFAULT_OUTPUT_DIR = DEFAULT_ROOT_DIR


def _load_baseline_rule(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def run_benchmark(
    root_dir: str | Path,
    seeds: list[int],
    baseline_rule: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, object]:
    root = Path(root_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    run_rows = []
    yearly_frames = []
    rolling_frames = []
    for seed in seeds:
        seed_dir = root / f'seed_{seed:03d}'
        run_rows.append(load_seed_run(seed_dir))
        yearly_frames.append(build_yearly_summary(seed_dir))
        rolling_frames.append(build_rolling_summary(seed_dir))

    runs = summarize_seed_matrix(run_rows)
    yearly = pd.concat(yearly_frames, ignore_index=True) if yearly_frames else pd.DataFrame()
    rolling = pd.concat(rolling_frames, ignore_index=True) if rolling_frames else pd.DataFrame()

    baseline = _load_baseline_rule(baseline_rule)
    summary = build_verdict(
        runs,
        yearly,
        baseline_test_pf=float(baseline.get('winner', {}).get('pf', 0.0)),
        baseline_sequential_pf=float(baseline.get('sequential_summary', {}).get('pf', 0.0)),
    )

    runs_path = out / 'runs.csv'
    yearly_path = out / 'yearly.csv'
    rolling_path = out / 'rolling.csv'
    summary_path = out / 'summary.json'

    runs.to_csv(runs_path, sep=';', index=False)
    yearly.to_csv(yearly_path, sep=';', index=False)
    rolling.to_csv(rolling_path, sep=';', index=False)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

    payload = {
        **summary,
        'runs_path': str(runs_path),
        'yearly_path': str(yearly_path),
        'rolling_path': str(rolling_path),
        'summary_path': str(summary_path),
    }
    return payload


def parse_args():
    parser = argparse.ArgumentParser(description='Aggregate multi-seed robustness for entry_path_v1_quantile.')
    parser.add_argument('--root-dir', default=str(DEFAULT_ROOT_DIR))
    parser.add_argument('--seeds', type=int, nargs='+', required=True)
    parser.add_argument('--baseline-rule', default=str(DEFAULT_BASELINE_RULE))
    parser.add_argument('--output-dir', default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def main():
    args = parse_args()
    payload = run_benchmark(
        root_dir=args.root_dir,
        seeds=args.seeds,
        baseline_rule=args.baseline_rule,
        output_dir=args.output_dir,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


if __name__ == '__main__':
    main()
