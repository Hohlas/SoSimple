# Fixed11 Current OHLC Rerun Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Пересчитать fixed11 locked-test на свежих H1/M5 OHLC для исполнения без изменения Python-логики внутри H1-бара и отделить эффект смены OHLC от будущего исправления хронологии.

**Architecture:** Этап является диагностическим rerun: текущие H1/M5 CSV становятся OHLC-источником исполнения, но `DATA/Nero_XAUUSD_test_labeled.csv` остаётся тем же labeled locked-test input. Runner, правила, cutoffs, entry/exit/stop/spread и политика same-H1 обработки не меняются. Результат сохраняется отдельным output-prefix, сравнивается со старым locked-test artifact и не используется для нового выбора rules.

**Tech Stack:** `./.venv/bin/python`, pandas/stdlib CSV/JSON, `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`, `ML/baseline/benchmark_fractal0_entry_exit_grid.py`, `ML/reports/fractal0_fixed11_retained_mt4_parity/reconcile_fill_chronology.py`, Markdown report.

## Global Constraints

- Работать на текущей ветке, не делать `git push` без явной просьбы.
- Не запускать полный suite `./.venv/bin/python -m pytest tests/ -q`.
- Не менять Python execution logic, MQL4 runtime, MT4 settings, retained rules, cutoffs, profiles, models, targets, filters, stops, entry/exit policies, spread или PnL convention.
- Использовать свежие canonical OHLC paths:
  - H1: `DATA/XAUUSD_H1_OHLC.csv`;
  - M5: `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`.
- Старый H1 source сохранять как diagnostic baseline: `DATA/XAUUSD_H1_OHLC_prev_20260701.csv`.
- Labeled locked-test input не пересобирать в этом плане: `DATA/Nero_XAUUSD_test_labeled.csv` остаётся исходным набором строк/признаков. Полная пересборка labeled dataset из текущей MT4 history требует отдельного плана и source/producer audit.
- Новый rerun output-prefix: `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history`.
- Старые artifacts `ML/reports/fractal0_fixed11_rich_entry_locked_test.json` и `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv` не перезаписывать.
- Максимальный вердикт этого этапа: `DIAGNOSTIC_ONLY`, потому что меняется OHLC source после прежнего locked-test, labeled dataset остаётся старым, и H1 same-bar MLClose contract ещё не исправлен.
- Если команда пересчёта падает из-за отсутствия входов или несовместимого schema, остановиться и зафиксировать blocker; не чинить runner в этом плане.

---

## Methodology Map

- `docs/methodology/README.md`: результат с неполным execution contract не выше `DIAGNOSTIC_ONLY`.
- `docs/methodology/01-raw-data-inventory.md`: зафиксировать source, период, hash, CSV contract, provider/timezone risks для H1 и M5.
- `docs/methodology/10-frozen-test-oos.md`: locked-test не используется для нового выбора; execution contract должен быть тем же, кроме явно диагностической смены OHLC source.
- `docs/methodology/12-backtest-costs.md`: M5 может использоваться только для execution ordering, не как feature source; price convention и source должны быть указаны.
- `docs/methodology/13-export-mt4-parity.md`: этот этап не делает MT4 parity, но сохраняет данные, нужные для будущего export/reconciliation.
- `docs/methodology/16-reporting-audit.md`: отчет должен содержать команды, paths, hashes, artifacts, limitations, invalidated assumptions и next step.

---

### Task 1: Freeze Current OHLC Sources And Labeled Input

**Files:**
- Read: `docs/methodology/README.md`
- Read: `docs/methodology/01-raw-data-inventory.md`
- Read: `docs/methodology/12-backtest-costs.md`
- Read: `DATA/XAUUSD_H1_OHLC.csv`
- Read: `DATA/XAUUSD_H1_OHLC_prev_20260701.csv`
- Read: `MT/MQL4/Files/XAUUSD_H1_OHLC.csv`
- Read: `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`
- Read: `DATA/Nero_XAUUSD_test_labeled.csv`
- Read: `/home/hohla/.mt4/drive_c/Program Files (x86)/MetaTrader 4/history/MetaQuotes-Demo/XAUUSD60.hst`
- Read: `/home/hohla/.mt4/drive_c/Program Files (x86)/MetaTrader 4/history/MetaQuotes-Demo/XAUUSD5.hst`
- Modify: `ML/reports/fractal0_fixed11_retained_mt4_parity/fill_chronology_manifest.json`

**Interfaces:**
- Consumes: canonical H1/M5 CSV, old H1 backup and unchanged labeled locked-test CSV.
- Produces: refreshed `fill_chronology_manifest.json` with hashes and H1/M5 HST comparison used by Task 2 and Task 4.

**Applicable Methodology:**
- `docs/methodology/01-raw-data-inventory.md`: source, CSV contract, period, duplicates, provider/timezone risks.
- `docs/methodology/12-backtest-costs.md`: M5 is execution ordering only, not ML feature source.

**Mandatory Checks:**
- H1 `DATA/XAUUSD_H1_OHLC.csv` and `MT/MQL4/Files/XAUUSD_H1_OHLC.csv` have identical hash.
- Current H1 vs `XAUUSD60.hst` has no material historical mismatch except incomplete/latest edge rows.
- Current M5 vs `XAUUSD5.hst` has no material historical mismatch except incomplete/latest edge rows.
- Old H1 backup remains present and hashable.
- `DATA/Nero_XAUUSD_test_labeled.csv` is present, hashable and recorded as the unchanged labeled input.

**Completion Criterion:**
- Manifest exists and records current H1/M5 hashes, previous H1 hash, labeled input hash, HST paths, row counts, matched rows, and yearly diff counts.

- [ ] **Step 1: Verify local methodology entry point**

Run:

```bash
sed -n '1,90p' docs/methodology/README.md
sed -n '1,120p' docs/methodology/01-raw-data-inventory.md
sed -n '1,120p' docs/methodology/12-backtest-costs.md
```

Expected:

```text
README includes DIAGNOSTIC_ONLY definition.
01-raw-data-inventory includes Lower-Timeframe Execution OHLC Audit.
12-backtest-costs includes Lower-timeframe execution ordering.
```

- [ ] **Step 2: Verify canonical files are present**

Run:

```bash
ls -l DATA/XAUUSD_H1_OHLC.csv \
  DATA/XAUUSD_H1_OHLC_prev_20260701.csv \
  MT/MQL4/Files/XAUUSD_H1_OHLC.csv \
  MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  DATA/Nero_XAUUSD_test_labeled.csv
```

Expected:

```text
All four files exist.
```

- [ ] **Step 3: Verify hashes of current H1 sources**

Run:

```bash
sha256sum DATA/XAUUSD_H1_OHLC.csv \
  DATA/XAUUSD_H1_OHLC_prev_20260701.csv \
  MT/MQL4/Files/XAUUSD_H1_OHLC.csv \
  MT/MQL4/Files/XAUUSD_M5_OHLC.csv
```

Expected:

```text
DATA/XAUUSD_H1_OHLC.csv and MT/MQL4/Files/XAUUSD_H1_OHLC.csv have the same sha256.
DATA/XAUUSD_H1_OHLC_prev_20260701.csv has a different sha256 from current H1.
MT/MQL4/Files/XAUUSD_M5_OHLC.csv has its own sha256.
DATA/Nero_XAUUSD_test_labeled.csv has its own sha256.
```

- [ ] **Step 4: Refresh history reconciliation manifest**

Run:

```bash
./.venv/bin/python ML/reports/fractal0_fixed11_retained_mt4_parity/reconcile_fill_chronology.py
```

Expected:

```text
Command exits 0.
Output includes ML/reports/fractal0_fixed11_retained_mt4_parity/fill_chronology_manifest.json.
Event counts are printed.
```

- [ ] **Step 5: Check manifest history sections**

Run:

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

for name in ["current_data_h1", "previous_python_h1", "mt4_exported_h1", "m5_csv"]:
    info = d["artifact_hashes"][name]
    assert info["exists"] is True
    assert len(info["sha256"]) == 64

print("history_manifest_ok")
print("current_data_h1_vs_hst", d["current_data_h1_vs_hst"])
print("current_m5_vs_hst_m5", d["current_m5_vs_hst_m5"])
print("previous_python_h1_vs_current_data_h1", d["previous_python_h1_vs_current_data_h1"])
PY
```

Expected:

```text
history_manifest_ok
current_data_h1_vs_hst {...}
current_m5_vs_hst_m5 {...}
previous_python_h1_vs_current_data_h1 {...}
```

---

### Task 2: Rerun Fixed11 Locked Test On Current OHLC Without Logic Changes

**Files:**
- Read: `docs/methodology/10-frozen-test-oos.md`
- Read: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`
- Read: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- Read: `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`
- Read: `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`
- Read: `ML/reports/leaderboard_closure_audit_rules.csv`
- Read: `ML/reports/fractal0_stop_grid_m5.json`
- Read: `DATA/Nero_XAUUSD_test_labeled.csv`
- Read: `DATA/XAUUSD_H1_OHLC.csv`
- Read: `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`
- Create: `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json`
- Create: `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv`

**Interfaces:**
- Consumes: frozen fixed11 rule definitions, unchanged labeled locked-test input and current H1/M5 OHLC.
- Produces: current-history locked-test artifacts for Task 3 comparison.

**Applicable Methodology:**
- `docs/methodology/10-frozen-test-oos.md`: no new rule/cutoff selection on locked-test; report sample size, sides, weak periods.
- `docs/methodology/12-backtest-costs.md`: keep execution and spread convention unchanged; M5 use remains execution diagnostic only.

**Mandatory Checks:**
- Runner command uses a new `--output-prefix`; old artifacts are not overwritten.
- Source rules, source artifact, labeled locked-test input and runner code stay unchanged.
- No code logic change is made before rerun.
- Output JSON records current `h1_ohlc_path` and `execution_ohlc_path`.

**Completion Criterion:**
- New JSON and trades CSV exist, have non-empty locked-test results, old artifact files remain byte-identical to their pre-rerun hashes, and source/rules/code hashes are recorded.

- [ ] **Step 1: Record input and code hashes before rerun**

Run:

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

Expected:

```text
Ten sha256 lines are printed. Save them in the task notes or final report.
```

- [ ] **Step 2: Verify runner CLI supports separate output prefix**

Run:

```bash
rg -n "source-rules-csv|source-artifact|locked-test-path|execution-ohlc-path|output-prefix" \
  ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py
```

Expected:

```text
The file contains --execution-ohlc-path and --output-prefix arguments.
```

- [ ] **Step 3: Verify there is no planned code diff in runner files**

Run:

```bash
git diff -- ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py \
  ML/baseline/benchmark_fractal0_entry_exit_grid.py \
  ML/baseline/benchmark_fractal0_entry_quality_filter.py
```

Expected:

```text
No diff is printed. If a diff is printed, stop and classify this rerun as not logic_change=none.
```

- [ ] **Step 4: Run current-OHLC locked-test rerun**

Run:

```bash
./.venv/bin/python ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py \
  --locked-test-path DATA/Nero_XAUUSD_test_labeled.csv \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --output-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history
```

Expected:

```text
Command exits 0.
Creates ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json.
Creates ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv.
```

- [ ] **Step 5: Verify old artifacts and inputs were not overwritten**

Run:

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

Expected:

```text
Hashes match Step 1.
```

- [ ] **Step 6: Verify new artifacts exist and contain current paths**

Run:

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
assert len(d["h1_ohlc_sha256"]) == 64
assert len(d["execution_ohlc_sha256"]) == 64
assert d["locked_test_path"] == "DATA/Nero_XAUUSD_test_labeled.csv"
assert len(d["locked_test_sha256"]) == 64

df = pd.read_csv(trades_path, sep=";", nrows=5)
required = {"rule_id", "signal_time", "fill_time", "exit_time", "close_reason", "pnl_r", "hold_bars"}
assert required <= set(df.columns), sorted(required - set(df.columns))

print("current_history_artifacts_ok")
print("rows_sample", len(df))
PY
```

Expected:

```text
current_history_artifacts_ok
rows_sample 5
```

---

### Task 3: Compare Old OHLC Result Against Current OHLC Result

**Files:**
- Read: `docs/methodology/10-frozen-test-oos.md`
- Read: `docs/methodology/16-reporting-audit.md`
- Read: `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`
- Read: `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`
- Read: `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json`
- Read: `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv`
- Create: `ML/reports/fractal0_fixed11_current_history_comparison.json`

**Interfaces:**
- Consumes: old and current-OHLC fixed11 artifacts.
- Produces: structured comparison used by Task 4 report.

**Applicable Methodology:**
- `docs/methodology/10-frozen-test-oos.md`: compare trades, yearly slices, BUY/SELL, close reasons; do not select new winner.
- `docs/methodology/16-reporting-audit.md`: key numbers must be in structured artifact or reproducible command.

**Mandatory Checks:**
- Compare all 11 fixed rules, not only retained slot 1.
- Include special diagnostics for retained slot 1 / `rank05_time_only_linear_target_entry_avoid_sl_top30`.
- Count `hold_bars=0`, `ML_CLOSE`, `SL`, `TIME`, total trades, PnL sum, PF by old/current.
- Count added and removed `signal_time + side + rule_id` keys.

**Completion Criterion:**
- `ML/reports/fractal0_fixed11_current_history_comparison.json` exists and contains input hashes, aggregate, per-rule and retained-slot-1 comparison.

- [ ] **Step 1: Create comparison artifact with an inline read-only script**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
import math
import hashlib
from pathlib import Path

import pandas as pd

OLD_JSON = Path("ML/reports/fractal0_fixed11_rich_entry_locked_test.json")
OLD = Path("ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv")
NEW_JSON = Path("ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json")
NEW = Path("ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv")
OUT = Path("ML/reports/fractal0_fixed11_current_history_comparison.json")
SLOT1 = "rank05_time_only_linear_target_entry_avoid_sl_top30"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def pf(s: pd.Series) -> float:
    gains = float(s[s > 0].sum())
    losses = float(-s[s < 0].sum())
    return math.inf if losses == 0 else gains / losses

def summarize(df: pd.DataFrame) -> dict[str, object]:
    return {
        "trades": int(len(df)),
        "pnl_r_sum": round(float(df["pnl_r"].sum()), 6),
        "pnl_r_mean": round(float(df["pnl_r"].mean()), 6) if len(df) else None,
        "pf": None if len(df) == 0 else round(float(pf(df["pnl_r"])), 6),
        "hold_bars_0": int((df["hold_bars"] == 0).sum()),
        "close_reasons": {str(k): int(v) for k, v in df["close_reason"].value_counts().items()},
        "side_counts": {str(k): int(v) for k, v in df["side"].value_counts().items()},
        "year_pnl_r": {
            str(int(k)): round(float(v), 6)
            for k, v in df.assign(year=pd.to_datetime(df["signal_time"]).dt.year).groupby("year")["pnl_r"].sum().items()
        },
    }

old = pd.read_csv(OLD, sep=";")
new = pd.read_csv(NEW, sep=";")
for frame in [old, new]:
    frame["signal_time_norm"] = pd.to_datetime(frame["signal_time"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    frame["key"] = frame["rule_id"].astype(str) + "|" + frame["side"].astype(str) + "|" + frame["signal_time_norm"]

rules = sorted(set(old["rule_id"]) | set(new["rule_id"]))
per_rule = {}
for rule in rules:
    o = old[old["rule_id"] == rule]
    n = new[new["rule_id"] == rule]
    old_keys = set(o["key"])
    new_keys = set(n["key"])
    per_rule[rule] = {
        "old": summarize(o),
        "current": summarize(n),
        "added_keys": int(len(new_keys - old_keys)),
        "removed_keys": int(len(old_keys - new_keys)),
        "common_keys": int(len(old_keys & new_keys)),
    }

out = {
    "stage": "fixed11_current_history_rerun",
    "status": "DIAGNOSTIC_ONLY",
    "old_json_path": str(OLD_JSON),
    "old_json_sha256": sha256(OLD_JSON),
    "old_trades_path": str(OLD),
    "old_trades_sha256": sha256(OLD),
    "current_json_path": str(NEW_JSON),
    "current_json_sha256": sha256(NEW_JSON),
    "current_trades_path": str(NEW),
    "current_trades_sha256": sha256(NEW),
    "comparison_key": "rule_id + side + signal_time",
    "logic_change": "none",
    "aggregate_old": summarize(old),
    "aggregate_current": summarize(new),
    "per_rule": per_rule,
    "slot1_rule_id": SLOT1,
    "slot1": per_rule[SLOT1],
}
OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(OUT)
print("aggregate_old", out["aggregate_old"])
print("aggregate_current", out["aggregate_current"])
print("slot1_old", out["slot1"]["old"])
print("slot1_current", out["slot1"]["current"])
PY
```

Expected:

```text
ML/reports/fractal0_fixed11_current_history_comparison.json
aggregate_old {...}
aggregate_current {...}
slot1_old {...}
slot1_current {...}
```

- [ ] **Step 2: Verify comparison covers 11 rules**

Run:

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

Expected:

```text
comparison_ok
rules 11
slot1_added <integer>
slot1_removed <integer>
```

- [ ] **Step 3: Inspect current-history same-H1 risk for retained slot 1**

Run:

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

Expected:

```text
slot1_trades <integer>
slot1_same_h1_fill_exit <integer>
slot1_hold_bars_0 <integer>
slot1_hold0_close_reasons {...}
slot1_hold0_pnl_r_sum <number>
```

---

### Task 4: Write Diagnostic Report And Next-Step Decision

**Files:**
- Read: `docs/methodology/16-reporting-audit.md`
- Read: `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`
- Read: `ML/reports/fractal0_fixed11_retained_mt4_parity/fill_chronology_manifest.json`
- Read: `ML/reports/fractal0_fixed11_current_history_comparison.json`
- Create: `docs/reports/2026-07-29-fixed11-current-history-rerun.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify only if needed: `CONTEXT_HANDOFF.md`
- Modify only if stage is closed: `CHANGELOG.md`

**Interfaces:**
- Consumes: current-OHLC rerun artifacts and comparison JSON.
- Produces: report that tells the next agent whether the main issue is mostly data drift or still execution chronology.

**Applicable Methodology:**
- `docs/methodology/16-reporting-audit.md`: report sections, commands, hashes, modified files, limitations, split disclosure, next step.
- `docs/methodology/10-frozen-test-oos.md`: explicitly state no new winner/cutoff/filter was selected.
- `docs/methodology/13-export-mt4-parity.md`: do not claim MT4 parity from Python-only rerun.

**Mandatory Checks:**
- Report states `DIAGNOSTIC_ONLY`.
- Report says logic inside H1 was not changed.
- Report states whether current-OHLC rerun materially changes the old result.
- Report contains mandatory sections from `docs/methodology/16-reporting-audit.md`: `Context`, `Уровень этапа`, `What Was Done`, `Multiple Testing Context`, `Changed Files`, `Verification`, `Results`, `Conclusions`, `Limitations / Open Questions`, `Split Disclosure`, `Next Step`, `Related Materials`.
- Report explicitly decides next step:
  - if same-H1/hold0 risk remains material: write/execute a separate chronology-fix plan;
  - if it almost disappears: regenerate MT4 exports from current-history artifacts and continue parity.

**Completion Criterion:**
- Report exists and roadmap points to it as the current source for this branch.

- [ ] **Step 1: Draft report from structured artifacts**

Create `docs/reports/2026-07-29-fixed11-current-history-rerun.md` with this structure:

```markdown
# Fixed11 Current OHLC Rerun

> **Дата**: 2026-07-29
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: проверить влияние свежих H1/M5 OHLC на fixed11 locked-test без изменения Python-логики внутри H1-бара и без пересборки labeled locked-test dataset.

## Context

- старый H1: `DATA/XAUUSD_H1_OHLC_prev_20260701.csv`;
- текущий H1: `DATA/XAUUSD_H1_OHLC.csv`;
- текущий M5: `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`;
- unchanged labeled input: `DATA/Nero_XAUUSD_test_labeled.csv`;
- старый artifact: `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`;
- новый artifact: `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json`;
- comparison: `ML/reports/fractal0_fixed11_current_history_comparison.json`.

## Уровень этапа

Diagnostic rerun. Максимальный статус `DIAGNOSTIC_ONLY`.
Это не новый locked-test PASS, не выбор winner и не MT4 parity.

## What Was Done

- Changed OHLC source: `DATA/XAUUSD_H1_OHLC.csv` and `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`.
- Kept labeled locked-test input unchanged: `DATA/Nero_XAUUSD_test_labeled.csv`.
- Kept runner logic unchanged: `logic_change=none`.
- Kept same-H1 MLClose processing unchanged.

## Multiple Testing Context

```text
new_rules=0
new_models=0
new_profiles=0
new_thresholds=0
new_entry_policy=0
new_exit_policy=0
changed_ohlc_source=true
changed_labeled_dataset=false
allowed_max_verdict=DIAGNOSTIC_ONLY
forbidden_interpretations=PASS/candidate/live-ready/MT4 parity/profitability proof
```

## Changed Files

- `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv`
- `ML/reports/fractal0_fixed11_current_history_comparison.json`
- `docs/reports/2026-07-29-fixed11-current-history-rerun.md`
- `docs/superpowers/roadmap.md`

## Verification

Report must include the exact commands from Task 1, Task 2 and Task 3.

## Results

Report must include these exact fields from
`ML/reports/fractal0_fixed11_current_history_comparison.json`:

- `aggregate_old.trades`, `aggregate_old.pnl_r_sum`, `aggregate_old.pf`, `aggregate_old.hold_bars_0`;
- `aggregate_current.trades`, `aggregate_current.pnl_r_sum`, `aggregate_current.pf`, `aggregate_current.hold_bars_0`;
- `slot1.old.trades`, `slot1.old.pnl_r_sum`, `slot1.old.pf`, `slot1.old.hold_bars_0`;
- `slot1.current.trades`, `slot1.current.pnl_r_sum`, `slot1.current.pf`, `slot1.current.hold_bars_0`;
- `slot1.added_keys`, `slot1.removed_keys`, `slot1.common_keys`.

## Conclusions

Report must state whether changing only OHLC source materially changed:

- aggregate fixed11 metrics;
- retained slot 1 metrics;
- hold_bars=0 / same-H1 risk.

## Limitations / Open Questions

- это не MT4 parity;
- это не новый выбор winner;
- labeled locked-test dataset не пересобран из текущей MT4 history;
- H1 same-bar MLClose logic не исправлена;
- MT4 tester после нового export ещё не запускался.

## Split Disclosure

- locked-test input path: `DATA/Nero_XAUUSD_test_labeled.csv`;
- split role: unchanged diagnostic locked-test input;
- old/current comparison key: `rule_id + side + signal_time`;
- `locked_test` not used for new rule/cutoff/filter selection.

## Next Step

Report must choose exactly one:

- if same-H1 risk remains material: write/execute a separate chronology-fix plan;
- if same-H1 risk almost disappears: export current-OHLC signals/exits and run MT4 slot 1 parity;
- if old labeled input is now the main blocker: write a separate plan to rebuild labeled locked-test dataset from current MT4 history.

## Related Materials

- `docs/superpowers/plans/2026-07-29-fixed11-current-history-rerun.md`
- `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`
- `ML/reports/fractal0_fixed11_retained_mt4_parity/fill_chronology_manifest.json`
- `ML/reports/fractal0_fixed11_current_history_comparison.json`
```

Expected:

```text
Report contains no claim of PASS/candidate/live readiness.
Report cites structured artifact paths.
```

- [ ] **Step 2: Update roadmap**

Modify `docs/superpowers/roadmap.md` current section to point to:

```text
docs/reports/2026-07-29-fixed11-current-history-rerun.md
ML/reports/fractal0_fixed11_current_history_comparison.json
```

Expected:

```text
Roadmap says current-OHLC rerun is the latest Python-side diagnostic before any H1 chronology logic change.
```

- [ ] **Step 3: Optional final docs sync**

If the report materially changes project knowledge, update `CHANGELOG.md` and `CONTEXT_HANDOFF.md` with one short entry each. Do not open either file fully; use `rg` for insertion point.

Run:

```bash
rg -n "fixed11|current history|fill chronology|Latest|Unreleased|2026-07-29" CHANGELOG.md CONTEXT_HANDOFF.md
```

Expected:

```text
Relevant insertion points are found, or the report states why final docs sync was deferred.
```

- [ ] **Step 4: Verification before completion**

Run:

```bash
rg -n "DIAGNOSTIC_ONLY|logic inside H1|same-H1|fractal0_fixed11_current_history_comparison|XAUUSD_H1_OHLC_prev_20260701|XAUUSD_M5_OHLC.csv|Nero_XAUUSD_test_labeled" \
  docs/reports/2026-07-29-fixed11-current-history-rerun.md \
  docs/superpowers/roadmap.md
```

Expected:

```text
All required phrases and artifact links are found.
```

---

## Final Self-Review Checklist

- [ ] Plan starts from `docs/methodology/README.md`.
- [ ] Plan uses only relevant methodology sections: `01`, `10`, `12`, `13`, `16`.
- [ ] Plan separates OHLC-source effect from H1 chronology logic effect.
- [ ] Plan explicitly states that labeled locked-test dataset is not rebuilt in this stage.
- [ ] Plan does not overwrite old locked-test artifacts.
- [ ] Plan does not ask for full `pytest tests/ -q`.
- [ ] Plan contains exact commands and expected outputs.
- [ ] Plan contains no placeholder markers or deferred-content phrases.
