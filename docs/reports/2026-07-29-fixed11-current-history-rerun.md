# Fixed11 Current OHLC Rerun

> **Дата**: 2026-07-29
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: проверить влияние свежих H1/M5 OHLC на fixed11 locked-test без изменения Python-логики внутри H1-бара и без пересборки labeled locked-test dataset.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-29-fixed11-current-history-rerun.md`

## Context

- старый H1: `DATA/XAUUSD_H1_OHLC_prev_20260701.csv`;
- текущий H1: `DATA/XAUUSD_H1_OHLC.csv`;
- текущий M5: `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`;
- unchanged labeled input: `DATA/Nero_XAUUSD_test_labeled.csv`;
- старый artifact: `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`;
- новый artifact: `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json`;
- comparison: `ML/reports/fractal0_fixed11_current_history_comparison.json`.

## Уровень этапа

Проверочный диагностический rerun. Это не новый locked-test PASS, не выбор
winner и не MT4 parity.

Максимальный статус: `DIAGNOSTIC_ONLY`.

Python-логика внутри H1 не менялась. `DATA/Nero_XAUUSD_test_labeled.csv`
не пересобирался из текущей MT4 history.

## What Was Done

1. Проверены текущие H1/M5 OHLC sources, старый H1 baseline и неизменённый
   labeled locked-test input.
2. Пересобран и проверен
   `ML/reports/fractal0_fixed11_retained_mt4_parity/fill_chronology_manifest.json`.
3. Запущен fixed11 locked-test rerun с новым output-prefix:
   `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history`.
4. Старые locked-test artifacts не перезаписывались.
5. Создано структурное сравнение старого и current-history результата по всем
   11 rules.
6. Отдельно проверен retained slot 1:
   `rank05_time_only_linear_target_entry_avoid_sl_top30`.

## Multiple Testing Context

```text
lifecycle_status=diagnostic_rerun
new_rules=0
new_models=0
new_profiles=0
new_thresholds=0
new_entry_policy=0
new_exit_policy=0
changed_ohlc_source=true
changed_labeled_dataset=false
logic_change=none
allowed_max_verdict=DIAGNOSTIC_ONLY
forbidden_interpretations=PASS/candidate/live-ready/MT4 parity/profitability proof
```

`locked_test` не использовался для нового выбора rule, cutoff, filter, entry,
exit, stop, spread или PnL convention.

## Changed Files

- `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv`
- `ML/reports/fractal0_fixed11_current_history_comparison.json`
- `docs/reports/2026-07-29-fixed11-current-history-rerun.md`
- `docs/superpowers/roadmap.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`

## Verification

Methodology and source checks:

```bash
sed -n '1,90p' docs/methodology/README.md
sed -n '1,120p' docs/methodology/01-raw-data-inventory.md
sed -n '1,120p' docs/methodology/12-backtest-costs.md
```

```bash
ls -l DATA/XAUUSD_H1_OHLC.csv \
  DATA/XAUUSD_H1_OHLC_prev_20260701.csv \
  MT/MQL4/Files/XAUUSD_H1_OHLC.csv \
  MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  DATA/Nero_XAUUSD_test_labeled.csv
```

```bash
sha256sum DATA/XAUUSD_H1_OHLC.csv \
  DATA/XAUUSD_H1_OHLC_prev_20260701.csv \
  MT/MQL4/Files/XAUUSD_H1_OHLC.csv \
  MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  DATA/Nero_XAUUSD_test_labeled.csv
```

Observed hashes:

```text
current H1 = affd627e55ad777cd763a4f5105420e38cefdf6e4ae94974f14c33509865029f
previous H1 = 4bf7a23ab79f41824713fa881078d06fb84fd7c484b2840c3cdec0bfdfda5aff
MT4 exported H1 = affd627e55ad777cd763a4f5105420e38cefdf6e4ae94974f14c33509865029f
M5 CSV = 85e6bbc49bc7e4049810cfb4a3d603576b9cd7b363c7b2f52bc43b59ef8c9a9b
labeled input = 5beb70f29ee27caa2b20a8cd80376879b64179d4ef0e5197a29357b58483f535
```

History reconciliation:

```bash
./.venv/bin/python ML/reports/fractal0_fixed11_retained_mt4_parity/reconcile_fill_chronology.py
```

Manifest validation:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

p = Path("ML/reports/fractal0_fixed11_retained_mt4_parity/fill_chronology_manifest.json")
d = json.loads(p.read_text(encoding="utf-8"))

required = [
    "previous_python_h1_vs_hst",
    "current_data_h1_vs_hst",
    "current_m5_vs_hst_m5",
    "previous_python_h1_vs_current_data_h1",
    "current_data_h1_vs_mt4_exported_h1",
]
missing = [k for k in required if k not in d]
assert not missing, missing
assert d["current_data_h1_vs_mt4_exported_h1"]["diff_rows"] == 0
assert d["current_data_h1_vs_hst"]["matched_rows"] > 120000
assert d["current_m5_vs_hst_m5"]["matched_rows"] > 1000000
assert d["previous_python_h1_vs_current_data_h1"]["diff_rows"] > 0
print("history_manifest_ok")
PY
```

Rerun pre/post hash checks:

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

Pre/post hashes matched exactly for all ten paths.

Runner CLI and no-code-diff checks:

```bash
rg -n "source-rules-csv|source-artifact|locked-test-path|execution-ohlc-path|output-prefix" \
  ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py
git diff -- ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py \
  ML/baseline/benchmark_fractal0_entry_exit_grid.py \
  ML/baseline/benchmark_fractal0_entry_quality_filter.py
```

Current-history rerun:

```bash
./.venv/bin/python ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py \
  --locked-test-path DATA/Nero_XAUUSD_test_labeled.csv \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --output-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history
```

New artifact validation:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd

json_path = Path("ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json")
trades_path = Path("ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv")
assert json_path.exists(), json_path
assert trades_path.exists(), trades_path

d = json.loads(json_path.read_text(encoding="utf-8"))
assert d["h1_ohlc_path"] == "DATA/XAUUSD_H1_OHLC.csv"
assert d["execution_ohlc_path"] == "MT/MQL4/Files/XAUUSD_M5_OHLC.csv"
assert d["locked_test_path"] == "DATA/Nero_XAUUSD_test_labeled.csv"

df = pd.read_csv(trades_path, sep=";", nrows=5)
required = {"rule_id", "signal_time", "fill_time", "exit_time", "close_reason", "pnl_r", "hold_bars"}
assert required <= set(df.columns)
print("current_history_artifacts_ok")
print("rows_sample", len(df))
PY
```

Comparison creation and validation:

```bash
./.venv/bin/python - <<'PY'
# inline comparison script from the plan
PY
```

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

d = json.loads(Path("ML/reports/fractal0_fixed11_current_history_comparison.json").read_text(encoding="utf-8"))
assert len(d["per_rule"]) == 11, len(d["per_rule"])
assert d["logic_change"] == "none"
assert d["status"] == "DIAGNOSTIC_ONLY"
assert d["aggregate_old"]["trades"] > 0
assert d["aggregate_current"]["trades"] > 0
assert "rank05_time_only_linear_target_entry_avoid_sl_top30" in d["per_rule"]
for key in ["old_json_sha256", "old_trades_sha256", "current_json_sha256", "current_trades_sha256"]:
    assert len(d[key]) == 64, key
print("comparison_ok")
print("rules", len(d["per_rule"]))
print("slot1_added", d["slot1"]["added_keys"])
print("slot1_removed", d["slot1"]["removed_keys"])
PY
```

Observed:

```text
comparison_ok
rules 11
slot1_added 37
slot1_removed 140
```

Retained slot 1 same-H1 risk:

```bash
./.venv/bin/python - <<'PY'
import pandas as pd

RULE = "rank05_time_only_linear_target_entry_avoid_sl_top30"
df = pd.read_csv("ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv", sep=";")
sub = df[df["rule_id"] == RULE].copy()
same_h1 = sub[pd.to_datetime(sub["fill_time"]) == pd.to_datetime(sub["exit_time"])]
hold0 = sub[sub["hold_bars"] == 0]
print("slot1_trades", len(sub))
print("slot1_same_h1_fill_exit", len(same_h1))
print("slot1_hold_bars_0", len(hold0))
print("slot1_hold0_close_reasons", hold0["close_reason"].value_counts().to_dict())
print("slot1_hold0_pnl_r_sum", round(float(hold0["pnl_r"].sum()), 6))
PY
```

Observed:

```text
slot1_trades 1091
slot1_same_h1_fill_exit 368
slot1_hold_bars_0 368
slot1_hold0_close_reasons {'ML_CLOSE': 335, 'SL': 33}
slot1_hold0_pnl_r_sum -98.196808
```

Full `./.venv/bin/python -m pytest tests/ -q` was not run because this plan
explicitly forbids the full suite for this workflow.

## Results

H1/M5 source checks:

- `DATA/XAUUSD_H1_OHLC.csv` and `MT/MQL4/Files/XAUUSD_H1_OHLC.csv` have the
  same hash.
- Current H1 vs `XAUUSD60.hst`: `matched_rows=128679`, `diff_rows=1`,
  `large_differences_by_year={"2026": 1}`.
- Current M5 vs `XAUUSD5.hst`: `matched_rows=1484849`, `diff_rows=1`,
  `large_differences_by_year={"2026": 1}`.
- Old H1 vs current H1: `diff_rows=13504`.

Aggregate fixed11:

| Metric | Old OHLC | Current OHLC |
|---|---:|---:|
| trades | 14507 | 13039 |
| pnl_r_sum | 4429.782419 | 4065.034595 |
| PF | 3.097520 | 3.116313 |
| hold_bars_0 | 5100 | 4495 |

Aggregate close reasons:

| Reason | Old OHLC | Current OHLC |
|---|---:|---:|
| ML_CLOSE | 10448 | 9345 |
| TIME | 3582 | 3230 |
| SL | 477 | 464 |

Retained slot 1:

| Metric | Old OHLC | Current OHLC |
|---|---:|---:|
| trades | 1196 | 1091 |
| pnl_r_sum | 395.026902 | 339.192111 |
| PF | 3.295678 | 3.113871 |
| hold_bars_0 | 406 | 368 |

Retained slot 1 key comparison:

```text
slot1.added_keys=37
slot1.removed_keys=140
slot1.common_keys=1017
comparison_key=signal_time + side + rule_id
```

Retained slot 1 current-history same-H1 risk:

```text
slot1_same_h1_fill_exit=368
slot1_hold_bars_0=368
slot1_hold0_close_reasons={'ML_CLOSE': 335, 'SL': 33}
slot1_hold0_pnl_r_sum=-98.196808
```

## Conclusions

Changing only OHLC source materially changed the old result:

- aggregate trade count fell from `14507` to `13039`;
- aggregate PnL fell from `4429.782419R` to `4065.034595R`;
- retained slot 1 trade count fell from `1196` to `1091`;
- retained slot 1 PnL fell from `395.026902R` to `339.192111R`.

But the OHLC refresh did not remove the core chronology problem. Retained slot 1
still has `368` same-H1 fill/exit trades and `368` `hold_bars=0` trades in the
current-history artifact. That is material because it is about one third of
slot 1 current-history trades and the `hold_bars=0` group remains negative.

Therefore the previous blocker is not mostly solved by data refresh. The main
remaining issue is still the Python execution chronology inside H1.

## Limitations / Open Questions

- This is not MT4 parity.
- This is not a new winner selection.
- The labeled locked-test dataset was not rebuilt from current MT4 history.
- H1 same-bar `MLClose` logic was not fixed.
- MT4 tester was not rerun after new current-history export.
- The one-row H1/M5 HST differences are latest-edge diagnostics, not a repaired
  execution contract.
- Current-history artifacts inherit the old labeled locked-test rows and feature
  availability assumptions.

## Split Disclosure

- locked-test input path: `DATA/Nero_XAUUSD_test_labeled.csv`;
- split role: unchanged diagnostic locked-test input;
- old/current comparison key: `signal_time + side + rule_id`;
- `locked_test` was not used for new rule/cutoff/filter selection;
- old Python artifact split is inherited from
  `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`;
- current-history rerun uses the same labeled locked-test input rows.

## Next Step

Write and execute a separate chronology-fix plan.

The plan should fix Python execution chronology before any new MT4 export:

1. define whether first ML-exit after fill on H1 bar `T` is allowed only from
   the next closed H1 bar or from a verified lower-timeframe timestamp after
   fill;
2. add focused tests for fill at H1 open, fill after H1 open, same-H1
   `MLClose`, and SL/TP same-bar M5 ordering;
3. rerun fixed11 locked-test artifacts after the contract change;
4. export current artifacts and rerun MT4 slot 1 parity only after the Python
   contract is fixed.

Do not regenerate MT4 exports from the current-history artifact as a parity
claim yet: same-H1/hold0 risk remains material.

## Related Materials

- `docs/superpowers/plans/2026-07-29-fixed11-current-history-rerun.md`
- `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`
- `docs/reports/2026-07-27-fractal0-fixed11-retained-subset-mt4-parity.md`
- `ML/reports/fractal0_fixed11_retained_mt4_parity/fill_chronology_manifest.json`
- `ML/reports/fractal0_fixed11_current_history_comparison.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv`
