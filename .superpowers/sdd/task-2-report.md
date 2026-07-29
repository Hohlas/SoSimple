# Task 2 Report: Fixed11 current-history locked-test rerun

## Goal

Run the fixed11 locked test on the current OHLC inputs with a new output prefix, without changing any Python logic, MQL4 runtime, rules, cutoffs, profiles, models, targets, filters, stops, entry/exit policies, spread, or PnL convention.

## Commands Run

1. Read task brief:

```bash
sed -n '1,260p' .superpowers/sdd/task-2-brief.md
```

2. Read methodology and runner:

```bash
sed -n '1,240p' docs/methodology/10-frozen-test-oos.md
sed -n '1,420p' ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py
```

3. Check repo status and existing report files:

```bash
git status --short
ls -1 ML/reports | rg 'fractal0_fixed11_rich_entry_locked_test|leaderboard_closure_audit_rules|fractal0_stop_grid_m5'
```

4. Record pre-rerun hashes:

```bash
sha256sum ML/reports/fractal0_fixed11_rich_entry_locked_test.json \
  ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv \
  ML/reports/leaderboard_closure_audit_rules.csv \
  ML/reports/fractal0_stop_grid_m5.json \
  DATA/Nero_XAUUSD_test_labeled.csv \
  DATA/XAUUSD_H1_OHLC.csv \
  MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py \
  ML/baseline/benchmark_fractal0_entry_exit_grid.py \
  ML/baseline/benchmark_fractal0_entry_quality_filter.py
```

5. Verify CLI support and no planned diff:

```bash
rg -n "source-rules-csv|source-artifact|locked-test-path|execution-ohlc-path|output-prefix" \
  ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py
git diff -- ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py \
  ML/baseline/benchmark_fractal0_entry_exit_grid.py \
  ML/baseline/benchmark_fractal0_entry_quality_filter.py
```

6. Run rerun on current OHLC:

```bash
./.venv/bin/python ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py \
  --locked-test-path DATA/Nero_XAUUSD_test_labeled.csv \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --output-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history
```

7. Recheck hashes after rerun and validate new artifacts:

```bash
sha256sum ML/reports/fractal0_fixed11_rich_entry_locked_test.json \
  ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv \
  ML/reports/leaderboard_closure_audit_rules.csv \
  ML/reports/fractal0_stop_grid_m5.json \
  DATA/Nero_XAUUSD_test_labeled.csv \
  DATA/XAUUSD_H1_OHLC.csv \
  MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py \
  ML/baseline/benchmark_fractal0_entry_exit_grid.py \
  ML/baseline/benchmark_fractal0_entry_quality_filter.py

./.venv/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd

json_path = Path('ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json')
trades_path = Path('ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv')
assert json_path.exists(), json_path
assert trades_path.exists(), trades_path

d = json.loads(json_path.read_text(encoding='utf-8'))
assert d['h1_ohlc_path'] == 'DATA/XAUUSD_H1_OHLC.csv'
assert d['execution_ohlc_path'] == 'MT/MQL4/Files/XAUUSD_M5_OHLC.csv'
assert d['locked_test_path'] == 'DATA/Nero_XAUUSD_test_labeled.csv'
assert len(d['h1_ohlc_sha256']) == 64
assert len(d['execution_ohlc_sha256']) == 64
assert len(d['locked_test_sha256']) == 64
assert d['status'] == 'completed'
assert d['verdict'] in {'candidate_check_required', 'reject'}
assert d['kept_candidates'] == 11
assert d['rule_count'] == 11

trades = pd.read_csv(trades_path, sep=';')
assert len(trades) > 0
required = {'rule_id', 'signal_time', 'fill_time', 'exit_time', 'close_reason', 'pnl_r', 'hold_bars'}
missing = required - set(trades.columns)
assert not missing, sorted(missing)

print('current_history_artifacts_ok')
print('trade_rows', len(trades))
print('trade_cols', len(trades.columns))
PY
```

## Hashes Before and After

Pre-rerun hashes:

- `ML/reports/fractal0_fixed11_rich_entry_locked_test.json` `db737be2012a45aa251bbc7eb33a67c3ae062b5158c379d0e0bfc7d01b355e97`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv` `5f73f3399968099a674b1e533be45c69a3f11e4e6c45521fea00148b6dd9b0b6`
- `ML/reports/leaderboard_closure_audit_rules.csv` `d98c1194d954e20aaa7d7a132547a9ac52caf1c7073f5ce98997cda1ee3b808c`
- `ML/reports/fractal0_stop_grid_m5.json` `20e6931a1b47d7d2fe3c5455e698d8bb3160bd570a418a35a0a0ea083358e0b6`
- `DATA/Nero_XAUUSD_test_labeled.csv` `5beb70f29ee27caa2b20a8cd80376879b64179d4ef0e5197a29357b58483f535`
- `DATA/XAUUSD_H1_OHLC.csv` `affd627e55ad777cd763a4f5105420e38cefdf6e4ae94974f14c33509865029f`
- `MT/MQL4/Files/XAUUSD_M5_OHLC.csv` `85e6bbc49bc7e4049810cfb4a3d603576b9cd7b363c7b2f52bc43b59ef8c9a9b`
- `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py` `0eeb7b3a25206855696964c0ba0a2f2671d37230b9374891ed6e769cd4593a96`
- `ML/baseline/benchmark_fractal0_entry_exit_grid.py` `c4f1213afa74066d54538e4a2d0971a370a6bf89c982f5a0a814585a6a85d565`
- `ML/baseline/benchmark_fractal0_entry_quality_filter.py` `793f18b49e06f815f8144ac6ec1fb9eff1acb67d264a002874b00039e2f0911f`

Post-rerun hashes matched exactly for all ten paths.

## Key Results

- Rerun command exited `0`.
- New artifact prefix created:
  - `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json`
  - `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv`
  - plus the expected summary, yearly, side, and selection CSVs under the same prefix.
- New JSON records current paths:
  - `h1_ohlc_path = DATA/XAUUSD_H1_OHLC.csv`
  - `execution_ohlc_path = MT/MQL4/Files/XAUUSD_M5_OHLC.csv`
  - `locked_test_path = DATA/Nero_XAUUSD_test_labeled.csv`
- New JSON status:
  - `status = completed`
  - `verdict = candidate_check_required`
  - `kept_candidates = 11`
  - `rule_count = 11`
- Trade sample check passed:
  - `trade_rows = 13039`
  - `trade_cols = 38`

## Changed Files

Tracked or created for Task 2:

- `.superpowers/sdd/task-2-report.md`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json`

Generated but gitignored CSV artifacts also exist under the same prefix:

- `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_summary.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_yearly.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_side.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_selection.csv`

## Self-Check

- Verified the rerun used the new `--output-prefix`.
- Verified the old locked-test artifacts were byte-identical before and after rerun.
- Verified the source rule file, source artifact, labeled locked-test input, and runner code hashes did not change.
- Verified the new JSON points to the current H1 and M5 OHLC paths.
- Verified the new trades file is non-empty and has the required columns.
- Did not run the full `./.venv/bin/python -m pytest tests/ -q`.

