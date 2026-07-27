# Fixed11 Retained Subset MT4 Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Доказать или заблокировать MT4/tester parity для 5 retained fixed11 rules без потери `rule_id`, дублей времени, противоположных сигналов и Python execution contract.

**Architecture:** Сначала выполняется feasibility gate: можно ли текущим MT4 runtime честно повторить Python fixed11 contract `E3/S2/X2/spread=0.20` и представить 5-rule trade stream без схлопывания. Только если gate прошёл, создаётся export и запускается MT4/tester; если нет, этап закрывается как `parity_blocked`, а не имитирует parity через неподходящий `time;signal`.

**Tech Stack:** `./.venv/bin/python`, pandas/stdlib CSV/JSON, `ML.online_tester_reconciliation`, MT4 tester, `MT/MQL4/Experts/$o$imple.mq4`, `MT/tester/$o$imple.ini`, `MT/MQL4/Files/#.csv`, Markdown reports, wiki generator.

## Global Constraints

depends_on:
- `docs/reports/2026-07-24-fractal0-fixed11-locked-test.md`
- `docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md`
- `docs/reports/2026-07-27-fractal0-fixed11-mutual-correlation-pruning.md`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`
- `ML/reports/fractal0_fixed11_candidate_audit.json`
- `ML/reports/fractal0_fixed11_candidate_audit_findings.csv`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_retained_subset.json`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_summary.json`

blocks:
- `Locked-test stress-spread disclosure`
- `Model card for retained subset`

supersedes:
- Nothing. This is the next active gate after fixed11 mutual-correlation pruning.

exit_decisions:
- `parity_passed`
- `parity_blocked`
- `parity_failed`

verdict_mapping:
- `parity_passed` -> report `Вердикт: PASS`
- `parity_failed` -> report `Вердикт: FAIL`
- `parity_blocked` -> report `Вердикт: UNKNOWN`

locked_test_policy:
- Use existing locked-test artifacts only to reproduce/export already accepted retained rules.
- Do not create new rules, cutoffs, profiles, models, targets, filters, entries, exits, stops, spread assumptions, fill policy, or PnL convention.
- Do not export all 11 rules as independent candidates.
- Do not treat MT4 parity as proof of profitability.

Retained rules are fixed:
- `rank05_time_only_linear_target_entry_avoid_sl_top30`
- `rank02_time_only_linear_target_entry_ev_regression_top40`
- `rank11_movement_plus_time_linear_target_entry_good_0_5r_top50`
- `rank09_time_only_hist_gradient_boosting_target_entry_good_0_5r_top50`
- `rank10_movement_plus_time_linear_target_entry_ev_regression_top50`

Methodology entry point:
- Start from `docs/methodology/README.md`.
- Main method: `docs/methodology/13-export-mt4-parity.md`.
- Reporting method: `docs/methodology/16-reporting-audit.md`.
- Pipeline invariants: `docs/DATA_FLOW.md`, only for export/reconciliation data-flow checks.

Known runtime inputs:
- MT4 project directory: `MT/MQL4`.
- MT4 expert: `MT/MQL4/Experts/$o$imple.mq4`.
- MT4 tester settings file: `MT/tester/$o$imple.ini`.
- Current tester input says `BackTest=2`.
- Main MT4 runtime parameter source for tester mode is `MT/MQL4/Files/#.csv`, selected by `BackTest`.
- `MT/tester/opt.set` is auxiliary unless the actual launch workflow proves it is the active source.

Known blocking risks:
- Current retained data has many duplicate `signal_time` values across rules.
- Current retained data has opposite directions at the same `signal_time`.
- Current `iSignal=3` direct mode opens on the next bar and does not obviously implement Python fixed11 `E3_open_pullback_1_0atr` plus `X2_ml_opposite_any_p0_50`.

---

### Task 1: Prove Parity Feasibility Before Export

**Files:**
- Read: `docs/methodology/README.md`
- Read: `docs/methodology/13-export-mt4-parity.md`
- Read: `docs/methodology/16-reporting-audit.md`
- Read: `docs/DATA_FLOW.md`
- Read: `docs/reports/2026-07-24-fractal0-fixed11-locked-test.md`
- Read: `docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md`
- Read: `docs/reports/2026-07-27-fractal0-fixed11-mutual-correlation-pruning.md`
- Read: `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`
- Read: `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`
- Read: `ML/reports/fractal0_fixed11_candidate_audit.json`
- Read: `ML/reports/fractal0_fixed11_candidate_audit_findings.csv`
- Read: `ML/reports/fractal0_fixed11_mutual_correlation_pruning_retained_subset.json`
- Read: `ML/reports/fractal0_fixed11_mutual_correlation_pruning_summary.json`
- Read: `MT/README.md`
- Read: `MT/MQL4/README.md`
- Read: `docs/MT/trading_strategy.md`
- Read: `docs/MT/ml_signal_integration.md`
- Read: `MT/tester/$o$imple.ini`
- Read: `MT/MQL4/Files/#.csv`
- Read: `MT/tester/opt.set`
- Create: `ML/reports/fractal0_fixed11_retained_mt4_parity/feasibility.json`
- Create: `ML/reports/fractal0_fixed11_retained_mt4_parity/freeze.json`

**Interfaces:**
- Consumes: fixed retained rules, locked-test execution contract, MT4 runtime docs/settings.
- Produces: feasibility verdict and frozen scope. Later tasks must not run if `feasibility_decision=parity_blocked`.

**Applicable Methodology:**
- `docs/methodology/13-export-mt4-parity.md`: MT4 must read the checked file, exporter must not change rules after `locked_test`, duplicate timestamps must be understood, and offline M1/M5 ordering is not MT4 parity.
- `docs/methodology/16-reporting-audit.md`: record paths, hashes, rules, commands, limitations.
- `docs/DATA_FLOW.md`: verify the path is `prediction/export CSV -> ml_signals.csv -> MT4 tester -> reconciliation`.

- [ ] **Step 1: Verify retained subset and trade stream shape**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd

retained_path = Path("ML/reports/fractal0_fixed11_mutual_correlation_pruning_retained_subset.json")
trades_path = Path("ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv")
retained = [
    r["rule_id"]
    for r in json.loads(retained_path.read_text(encoding="utf-8"))["rules"]
    if r["decision"] == "RETAIN"
]
expected = {
    "rank05_time_only_linear_target_entry_avoid_sl_top30",
    "rank02_time_only_linear_target_entry_ev_regression_top40",
    "rank11_movement_plus_time_linear_target_entry_good_0_5r_top50",
    "rank09_time_only_hist_gradient_boosting_target_entry_good_0_5r_top50",
    "rank10_movement_plus_time_linear_target_entry_ev_regression_top50",
}
assert set(retained) == expected
df = pd.read_csv(trades_path, sep=";")
required = {"signal_time", "fill_time", "side", "rule_id", "exit_time", "close_reason", "entry_effective_price"}
missing = required - set(df.columns)
assert not missing, sorted(missing)
sub = df[df["rule_id"].isin(retained)].copy()
sub["direction"] = sub["side"].map({"BUY": 1, "SELL": -1})
by_time = sub.groupby("signal_time").agg(
    rows=("rule_id", "size"),
    directions=("direction", lambda s: len(set(s))),
    rule_count=("rule_id", lambda s: len(set(s))),
)
print(
    "retained_trades",
    len(sub),
    "unique_signal_time",
    sub["signal_time"].nunique(),
    "unique_signal_time_direction",
    sub[["signal_time", "direction"]].drop_duplicates().shape[0],
    "duplicate_signal_time_count",
    int((by_time["rows"] > 1).sum()),
    "opposite_signal_time_count",
    int((by_time["directions"] > 1).sum()),
)
PY
```

Expected from current artifacts: retained trades are more numerous than unique `signal_time`, and duplicate/opposite-time counts are non-zero. This does not fail the plan; it proves a plain `time;signal` stream cannot be used for five independent rules.

- [ ] **Step 2: Verify Python fixed11 execution contract**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("ML/reports/fractal0_fixed11_rich_entry_locked_test.json").read_text(encoding="utf-8"))
print(json.dumps(data["execution_contract"], indent=2, sort_keys=True))
assert data["execution_contract"] == {
    "stop_policy_id": "S2_fractal0_buffer_0_5_entry_floor_2",
    "entry_id": "E3_open_pullback_1_0atr",
    "mask_id": "M0_no_mask",
    "exit_id": "X2_ml_opposite_any_p0_50",
    "spread": 0.2,
}
PY
```

Expected: command exits `0` and prints the frozen Python contract.

- [ ] **Step 3: Verify MT4 runtime parameter sources**

Run:

```bash
nl -ba MT/tester/'$o$imple.ini' | sed -n '1,40p'
nl -ba MT/MQL4/Files/#.csv | sed -n '1,3p'
./.venv/bin/python - <<'PY'
from pathlib import Path
opt = Path("MT/tester/opt.set").read_text(errors="replace")
for key in [
    "ML_ExitMode",
    "ML_TrailATR",
    "ML_TakeProfitATR",
    "ML_MaxPositions",
    "ML_HoldBars",
    "ML_AllowReversal",
    "ML_UseScoreFilter",
    "ML_ScoreThreshold",
    "ML_BackStopATR",
]:
    print(key, key in opt)
PY
```

Expected:
- `MT/tester/$o$imple.ini` shows `BackTest=2`;
- `MT/MQL4/Files/#.csv` row 2 contains `ML_ExitMode`, `ML_TakeProfitATR`, `ML_MaxPositions`, `ML_HoldBars`, `ML_BackStopATR`;
- `MT/tester/opt.set` does not contain the full `ML_*` runtime contract and must not be the only frozen settings source.

- [ ] **Step 4: Verify whether current MT4 can execute Python fixed11 contract**

Run:

```bash
rg -n "E3_open_pullback_1_0atr|S2_fractal0_buffer_0_5_entry_floor_2|X2_ml_opposite_any_p0_50|ML_ExitMode|ML_TakeProfitATR|ML_MaxPositions|ML_HoldBars|ML_BackStopATR|ML_AllowReversal|ML_TRADE|signal_time" MT/MQL4 docs/MT ML/baseline docs/reports/2026-07-24-fractal0-fixed11-locked-test.md
```

Expected:
- if MT4 has a direct implementation of `E3/S2/X2/spread=0.20`, record how it is activated;
- if MT4 only has current `iSignal=3` next-bar runtime, record `runtime_contract_match=false`.

- [ ] **Step 5: Write `feasibility.json`**

Create `ML/reports/fractal0_fixed11_retained_mt4_parity/feasibility.json`:

```json
{
  "stage": "fixed11_retained_subset_mt4_parity",
  "feasibility_decision": "parity_blocked",
  "methodology_status": "UNKNOWN",
  "python_execution_contract": {
    "stop_policy_id": "S2_fractal0_buffer_0_5_entry_floor_2",
    "entry_id": "E3_open_pullback_1_0atr",
    "mask_id": "M0_no_mask",
    "exit_id": "X2_ml_opposite_any_p0_50",
    "spread": 0.2,
    "execution_ohlc": "MT/MQL4/Files/XAUUSD_M5_OHLC.csv"
  },
  "mt4_runtime_contract": {
    "expert": "MT/MQL4/Experts/$o$imple.mq4",
    "tester_ini": "MT/tester/$o$imple.ini",
    "tester_backtest_row": 2,
    "params_csv": "MT/MQL4/Files/#.csv",
    "opt_set": "MT/tester/opt.set",
    "runtime_contract_match": false,
    "runtime_contract_match_reason": "current iSignal=3 direct mode opens on next bar and does not prove E3/S2/X2 fixed11 execution"
  },
  "retained_stream_counts": {
    "retained_trade_count": 6177,
    "unique_signal_time_count": 2806,
    "unique_signal_time_direction_count": 2827,
    "duplicate_signal_time_count": 1670,
    "opposite_signal_time_count": 21
  },
  "plain_time_signal_export_allowed": false,
  "plain_time_signal_export_blocker": "time;signal cannot preserve five-rule trade stream because it drops rule_id and collapses duplicate signal_time rows",
  "allowed_next_modes": [
    "separate_per_rule_export_and_mt4_run",
    "new_mt4_runtime_with_rule_id_and_fixed11_execution_contract",
    "weaker_aggregated_signal_reading_diagnostic_without_trade_parity_claim"
  ]
}
```

If Step 4 proves MT4 can exactly execute `E3/S2/X2/spread=0.20` and can preserve `rule_id`, set `feasibility_decision` to `parity_feasible`, `methodology_status` to `PASS`, and explain the exact activation. Do not set it to feasible by assumption.

- [ ] **Step 6: Write `freeze.json`**

Create `ML/reports/fractal0_fixed11_retained_mt4_parity/freeze.json` with all input hashes:

```json
{
  "stage": "fixed11_retained_subset_mt4_parity",
  "depends_on": [
    "docs/reports/2026-07-24-fractal0-fixed11-locked-test.md",
    "docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md",
    "docs/reports/2026-07-27-fractal0-fixed11-mutual-correlation-pruning.md",
    "ML/reports/fractal0_fixed11_rich_entry_locked_test.json",
    "ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv",
    "ML/reports/fractal0_fixed11_candidate_audit.json",
    "ML/reports/fractal0_fixed11_candidate_audit_findings.csv",
    "ML/reports/fractal0_fixed11_mutual_correlation_pruning_retained_subset.json",
    "ML/reports/fractal0_fixed11_mutual_correlation_pruning_summary.json"
  ],
  "retained_rule_ids": [
    "rank05_time_only_linear_target_entry_avoid_sl_top30",
    "rank02_time_only_linear_target_entry_ev_regression_top40",
    "rank11_movement_plus_time_linear_target_entry_good_0_5r_top50",
    "rank09_time_only_hist_gradient_boosting_target_entry_good_0_5r_top50",
    "rank10_movement_plus_time_linear_target_entry_ev_regression_top50"
  ],
  "locked_test_boundaries": {
    "source": "docs/reports/2026-07-27-fractal0-fixed11-mutual-correlation-pruning.md",
    "locked_test_min_time": "2022-12-02 11:00:00",
    "locked_test_max_time": "2026-06-04 12:00:00",
    "edge_exclusions": []
  },
  "input_sha256": {
    "locked_test_report_md": "<sha256>",
    "candidate_audit_report_md": "<sha256>",
    "pruning_report_md": "<sha256>",
    "locked_test_json": "<sha256>",
    "locked_test_trades_csv": "<sha256>",
    "candidate_audit_json": "<sha256>",
    "candidate_audit_findings_csv": "<sha256>",
    "retained_subset_json": "<sha256>",
    "pruning_summary_json": "<sha256>",
    "tester_ini": "<sha256>",
    "params_csv": "<sha256>",
    "opt_set": "<sha256>"
  },
  "forbidden_changes": [
    "rules",
    "cutoffs",
    "profiles",
    "models",
    "targets",
    "filters",
    "entries",
    "exits",
    "stops",
    "spread",
    "fill_policy",
    "pnl_convention"
  ]
}
```

Replace only `<sha256>` values with real hashes.

- [ ] **Step 7: Completion criterion**

Task is complete when `feasibility.json` and `freeze.json` exist, both are valid JSON, and the next task is allowed only if `feasibility_decision=parity_feasible`.

**Mandatory checks:**

```bash
./.venv/bin/python -m json.tool ML/reports/fractal0_fixed11_retained_mt4_parity/feasibility.json
./.venv/bin/python -m json.tool ML/reports/fractal0_fixed11_retained_mt4_parity/freeze.json
```

Expected: both JSON files are valid.

---

### Task 2: Choose Honest Export Mode Or Stop

**Files:**
- Read: `ML/reports/fractal0_fixed11_retained_mt4_parity/feasibility.json`
- Read: `ML/reports/fractal0_fixed11_retained_mt4_parity/freeze.json`
- Potential create/modify only if feasible: `ML/baseline/prepare_fractal0_fixed11_retained_mt4_parity.py`
- Potential create/modify only if feasible: `tests/test_prepare_fractal0_fixed11_retained_mt4_parity.py`
- Potential output only if feasible: `ML/reports/fractal0_fixed11_retained_mt4_parity/export_metadata.json`
- Potential output only if feasible: one of:
  - separate per-rule `ml_signals.csv` files;
  - extended MT4 input preserving `rule_id`;
  - weaker aggregate diagnostic explicitly marked not trade parity.

**Interfaces:**
- Consumes: feasibility decision.
- Produces: either `parity_blocked` stop artifact or a frozen export with an explicit mode.

**Applicable Methodology:**
- `docs/methodology/13-export-mt4-parity.md`: export format, hash, counts, duplicate timestamps, opposite signals, MT4 reads exactly checked file.
- `docs/methodology/16-reporting-audit.md`: limitations and forbidden interpretations must be explicit.

- [ ] **Step 1: Stop if feasibility is blocked**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("ML/reports/fractal0_fixed11_retained_mt4_parity/feasibility.json").read_text(encoding="utf-8"))
print(data["feasibility_decision"])
assert data["feasibility_decision"] in {"parity_feasible", "parity_blocked"}
if data["feasibility_decision"] == "parity_blocked":
    raise SystemExit(2)
PY
```

Expected:
- exit `2` means stop implementation and go directly to Task 5 with stage decision `parity_blocked`;
- exit `0` means export is allowed.

- [ ] **Step 2: If feasible, choose one export mode**

Allowed modes:
- `separate_per_rule_export_and_mt4_run`: each retained rule gets its own `ml_signals.csv`, Magic/event-log, and reconciliation. This preserves `rule_id` without changing MT4.
- `rule_id_runtime_export`: implement or use an MT4 runtime that reads `rule_id` and executes the Python fixed11 entry/exit contract. This requires separate tests for the runtime contract.
- `aggregated_signal_reading_diagnostic`: allowed only as `DIAGNOSTIC_ONLY`; it may check whether MT4 reads an aggregated signal stream, but it must not claim fixed11 trade parity.

Do not use one plain `time;signal` file for five independent retained rules if `duplicate_signal_time_count > 0` or `opposite_signal_time_count > 0`.

- [ ] **Step 3: Write failing tests for the chosen export mode**

For `separate_per_rule_export_and_mt4_run`, tests must assert:
- exactly five output files;
- each file contains one rule only;
- `duplicate_time_rows=0` within each per-rule file;
- `same_time_opposite_signal_groups=0` within each per-rule file;
- source columns are actual locked-test columns: `signal_time`, `fill_time`, `side`, `rule_id`;
- `signal_time` is used only for signal-stream parity; `fill_time` is not silently substituted.

For `rule_id_runtime_export`, tests must assert:
- `rule_id` is present in the export;
- duplicate `signal_time` is allowed only when `rule_id` differs;
- opposite directions at the same `signal_time` are represented without order dependence;
- MT4 runtime contract names `E3/S2/X2/spread=0.20`.

For `aggregated_signal_reading_diagnostic`, tests must assert:
- report status is `DIAGNOSTIC_ONLY`;
- duplicate/opposite groups are resolved by a predeclared policy;
- the output cannot be called fixed11 trade parity.

- [ ] **Step 4: Implement minimal exporter for the chosen mode**

Required behavior for any mode:
- fail if retained rule count is not `5`;
- fail if source trade columns are missing;
- read only retained trades;
- map BUY/LONG/`1` to `signal=1` and SELL/SHORT/`-1` to `signal=-1`;
- record rows total, nonzero rows, unique time, unique time+signal, duplicate time, opposite signals on same time;
- include SHA256 for source trades and produced export files;
- do not change any source locked-test artifact.

- [ ] **Step 5: Run targeted tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_prepare_fractal0_fixed11_retained_mt4_parity.py -q
```

Expected: PASS if exporter code was added. If stage is `parity_blocked` and no exporter code was added, this test file should not exist and this step is skipped with the reason recorded in the report.

- [ ] **Step 6: Completion criterion**

Task is complete when either:
- `feasibility_decision=parity_blocked` and no misleading export was produced;
- or export artifacts exist, preserve the chosen decision unit, and `export_metadata.json` proves duplicate/opposite-time handling.

---

### Task 3: Run MT4 Tester Only For A Feasible Export

**Files:**
- Input to MT4: export files from Task 2.
- Required runtime settings:
  - `MT/MQL4/Experts/$o$imple.mq4`
  - `MT/tester/$o$imple.ini`
  - `MT/MQL4/Files/#.csv`
  - auxiliary `MT/tester/opt.set` if the launch workflow uses it.
- Required MT4 output: fresh `ML_Trade_Events_<NAME>_<magic>.csv` path from tester files or documented MT4 output location.
- Modify: `ML/reports/fractal0_fixed11_retained_mt4_parity/freeze.json` only to add verified runtime log details and edge exclusions.

**Interfaces:**
- Consumes: feasible frozen export.
- Produces: MT4 tester event-log with `OPEN`, `OPEN_FAILED`, `CLOSE` events.

**Applicable Methodology:**
- `docs/methodology/13-export-mt4-parity.md`: MT4 must read the checked file, tester event-log must be cleaned before run, and event-log must include failure and cost fields.

- [ ] **Step 1: Confirm Task 2 did not stop**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("ML/reports/fractal0_fixed11_retained_mt4_parity/feasibility.json").read_text(encoding="utf-8"))
assert data["feasibility_decision"] == "parity_feasible", data["feasibility_decision"]
PY
```

Expected: exit `0`. If not, skip Task 3 and continue to Task 5 with `parity_blocked`.

- [ ] **Step 2: Copy only verified export files to MT4**

Copy through the exporter command from Task 2, not by manually editing runtime files. The copied files must hash-match `export_metadata.json`.

- [ ] **Step 3: Clean only the target tester event-log**

Before deleting or overwriting any MT4 log, confirm the exact path. Do not clean unrelated MT4 files.

- [ ] **Step 4: Run MT4 tester manually or through the existing project workflow**

Use `MT/MQL4/Experts/$o$imple.mq4`, `MT/tester/$o$imple.ini` with `BackTest=2`, and the selected row from `MT/MQL4/Files/#.csv`. The run must cover the locked-test interval from `2022-12-02 11:00:00` to `2026-06-04 12:00:00`; any incomplete edge exclusions must be recorded with reason and excluded signal/trade counts.

Expected event-log fields:
- `OPEN`;
- `OPEN_FAILED`;
- `CLOSE`;
- `ticket`;
- `signal_time`;
- `entry_time`;
- `exit_time`;
- `direction`;
- spread and `spread_atr`;
- Bid/Ask;
- requested and actual open/close prices;
- slippage if available;
- commission;
- swap;
- balance/equity if available;
- close reason.

- [ ] **Step 5: Record actual MT4 runtime details**

Update only the runtime details in `freeze.json`:

```json
{
  "mt4_runtime_contract": {
    "expert": "MT/MQL4/Experts/$o$imple.mq4",
    "tester_ini": "MT/tester/$o$imple.ini",
    "tester_backtest_row": 2,
    "params_csv": "MT/MQL4/Files/#.csv",
    "params_loaded_log_line": "<fresh PARAMS_LOADED line from tester log>",
    "expert_version_log_line": "<fresh OnInit version line from tester log>",
    "event_log_path": "<fresh tester event-log path>",
    "strict_match_key": "signal_time_plus_direction"
  }
}
```

- [ ] **Step 6: Completion criterion**

Task is complete when MT4 produced a fresh event-log, the tester log proves the selected parameter row was loaded, and `freeze.json` records exact runtime details.

---

### Task 4: Reconcile Python Export With MT4 Tester Events

**Files:**
- Read: export files and `export_metadata.json` from Task 2.
- Read: tester event-log path from `freeze.json`.
- Use: `ML/online_tester_reconciliation.py`.
- Output directory: `ML/reports/fractal0_fixed11_retained_mt4_parity/reconciliation`.

**Interfaces:**
- Consumes: frozen export and MT4 tester event-log.
- Produces: `signals_diff.csv`, `online_trades.csv`, `online_closed_trades.csv`, `summary.json`, `summary.md`; `tester_trades.csv`, `tester_closed_trades.csv`, and `trades_comparison.csv` only when a real separate `--tester-events` input exists.

**Applicable Methodology:**
- `docs/methodology/13-export-mt4-parity.md`: compare by `signal_time + direction`, explain missing trades, wrong direction, close reasons, critical mismatches, and duplicate timestamp effect.
- `docs/methodology/16-reporting-audit.md`: store commands, artifacts, metrics, limitations.

- [ ] **Step 1: Run tester-only reconciliation with correct output expectations**

For a tester-only event-log, run:

```bash
./.venv/bin/python -m ML.online_tester_reconciliation \
  --events <fresh_tester_event_log_path> \
  --signals <matching_export_ml_signals_csv> \
  --output-dir ML/reports/fractal0_fixed11_retained_mt4_parity/reconciliation \
  --start-time "2022.12.02 11:00" \
  --end-time "2026.06.04 12:00"
```

Expected files:
- `signals_diff.csv`;
- `online_trades.csv`;
- `online_closed_trades.csv`;
- `summary.json`;
- `summary.md`.

The `online_*` filenames are technical names from the existing tool. In this tester-only use they contain tester events. Do not pass the same tester log to both `--events` and `--tester-events`; that would create artificial online/tester agreement.

- [ ] **Step 2: If a real online event-log exists, run online/tester comparison**

Only when there is a separate online event-log for the same export and period, run:

```bash
./.venv/bin/python -m ML.online_tester_reconciliation \
  --events <real_online_event_log_path> \
  --signals <matching_export_ml_signals_csv> \
  --tester-events <fresh_tester_event_log_path> \
  --output-dir ML/reports/fractal0_fixed11_retained_mt4_parity/reconciliation_online_vs_tester \
  --start-time "2022.12.02 11:00" \
  --end-time "2026.06.04 12:00"
```

Expected additional files:
- `tester_trades.csv`;
- `tester_closed_trades.csv`;
- `trades_comparison.csv`.

- [ ] **Step 3: Inspect summary**

Run:

```bash
./.venv/bin/python -m json.tool ML/reports/fractal0_fixed11_retained_mt4_parity/reconciliation/summary.json
```

Expected:
- `critical_mismatch_count=0`, or every critical mismatch has a documented non-blocking reason;
- missing opens are absent, explained as non-blocking, or marked blocker;
- wrong directions are `0`;
- close reasons are present for closed tester trades.

- [ ] **Step 4: Inspect detailed mismatches**

Run:

```bash
./.venv/bin/python - <<'PY'
from pathlib import Path
import pandas as pd

base = Path("ML/reports/fractal0_fixed11_retained_mt4_parity/reconciliation")
for name in ["signals_diff.csv", "online_trades.csv", "online_closed_trades.csv"]:
    path = base / name
    assert path.exists(), path
    df = pd.read_csv(path, sep=";")
    print(name, df.shape)
    print(df.head(10).to_string())
PY
```

Expected: row counts are understood and any mismatch rows are classed as blocking or non-blocking.

- [ ] **Step 5: Completion criterion**

Task is complete when reconciliation artifacts exist and the stage decision is clear:
- `parity_passed`: `critical_mismatch_count=0` or accepted non-blocking differences only;
- `parity_failed`: signal direction/time/open/close mismatches are real and blocking;
- `parity_blocked`: MT4/tester log, runtime contract, export mode, or required fields are missing.

---

### Task 5: Report, Handoff, Wiki, And Tests

**Files:**
- Create: `docs/reports/2026-07-27-fractal0-fixed11-retained-subset-mt4-parity.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `CHANGELOG.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Generated: `wiki/REPO_integrity.md`

**Interfaces:**
- Consumes: `feasibility.json`, `freeze.json`, optional `export_metadata.json`, optional reconciliation `summary.json`, detailed CSV artifacts.
- Produces: canonical report and updated handoff/wiki state.

**Applicable Methodology:**
- `docs/methodology/16-reporting-audit.md`: completed stage report with context, level, commands, changed files, verification, results, limitations, split disclosure, next step.
- `docs/reports/README.md`: report header and required sections.
- Project rule: final sync of report/changelog/handoff/wiki uses `stage-reporting`.

- [ ] **Step 1: Write the report**

Create `docs/reports/2026-07-27-fractal0-fixed11-retained-subset-mt4-parity.md`.

Required header:

```markdown
# Fractal0 Fixed11 Retained Subset MT4 Parity

> **Дата**: 2026-07-27
> **Статус**: Completed
> **Вердикт**: PASS | FAIL | UNKNOWN | DIAGNOSTIC_ONLY
> **Stage decision**: parity_passed | parity_failed | parity_blocked
> **Цель**: Проверить, что MT4/tester исполняет retained subset так же, как Python fixed11 contract, или честно зафиксировать blocker.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-27-fixed11-retained-subset-mt4-parity.md`
```

Required sections:
- `Context`
- `Уровень этапа`
- `Methodology`
- `What Was Done`
- `Multiple Testing Context`
- `Changed Files`
- `Verification`
- `Results`
- `Split Disclosure`
- `Limitations / Open Questions`
- `Conclusions`
- `Next Step`
- `Related Materials`

Required disclosure:
- parity is not proof of profitability;
- no new rules/cutoffs/profiles/models/targets/filters/entries/exits/stops/spread/fill/PnL convention were selected;
- only 5 retained rules are in scope;
- dropped duplicate rules were not reintroduced;
- if `parity_blocked`, explicitly state which blocker stopped export/tester/reconciliation;
- if any aggregate signal diagnostic was run, state `DIAGNOSTIC_ONLY` and do not call it fixed11 trade parity.

- [ ] **Step 2: Update handoff**

Update `CONTEXT_HANDOFF.md`:
- if `parity_passed`, unblock stress-spread disclosure;
- if `parity_failed`, keep stress-spread blocked and name the failing mismatch class;
- if `parity_blocked`, keep this track active and list exact missing runtime/export requirement.

- [ ] **Step 3: Update changelog and wiki**

Update `CHANGELOG.md` only if the stage produced a real decision or new artifacts. Update wiki pages so the next agent sees the current state without reading every report.

- [ ] **Step 4: Run required checks**

If Python code was added or changed, run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: all tests pass.

For docs/wiki changes, run:

```bash
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

Expected: wiki status reports no gaps.

- [ ] **Step 5: Completion criterion**

Task is complete when:
- report exists and links this plan;
- `CONTEXT_HANDOFF.md` names the next step correctly;
- changelog/wiki are synchronized if the decision changed project state;
- full tests pass if Python changed;
- wiki status has no gaps.

---

## Audit Disposition Applied To This Plan

- Audit item 1: accepted. Plain one-file `time;signal` export is blocked for five independent rules because it loses `rule_id` and collapses duplicate/opposite `signal_time`.
- Audit item 2: accepted. Current `iSignal=3` next-bar direct runtime is not assumed to match Python `E3/S2/X2/spread=0.20`; feasibility must prove this before export.
- Audit item 3: partially accepted. `MT/tester/opt.set` remains an auxiliary launch file, but full runtime settings are frozen from `MT/tester/$o$imple.ini` and `MT/MQL4/Files/#.csv`.
- Audit item 4: accepted. Tester-only reconciliation expects `online_*` output filenames from the current tool; `tester_*` files require a real separate `--tester-events`.
- Audit item 5: accepted. The plan uses actual columns `signal_time`, `fill_time`, `side`, and `rule_id`, and forbids silently substituting `fill_time` for `signal_time`.
- Audit item 6: accepted. Candidate audit, locked-test report, locked-test JSON, and related hashes are explicit dependencies.
- Audit item 7: accepted. Locked-test boundaries are fixed at `2022-12-02 11:00:00` to `2026-06-04 12:00:00`; edge exclusions must be explicit.
- Audit item 8: accepted. Report verdict and stage decision are separate fields with an explicit mapping.

## Plan Self-Review

Spec coverage:
- The plan starts from `docs/methodology/README.md` and applies only relevant methodology sections: `13-export-mt4-parity.md`, `16-reporting-audit.md`, and `docs/DATA_FLOW.md` for data-flow invariants.
- Each task lists applicable methodology, required checks, and completion criteria.
- The retained subset is fixed to 5 rules from the current pruning artifacts.
- The plan forbids changing rules, cutoffs, models, filters, entries, exits, stops, spread, fill policy, and PnL convention.

Unknowns:
- The core unknown is whether current MT4 can execute Python fixed11 `E3/S2/X2/spread=0.20` while preserving five-rule trade identity.
- If current MT4 cannot do that, the correct stage decision is `parity_blocked`.

Placeholder scan:
- No `TBD`, `TODO`, "implement later", "fill in details", or ellipsis placeholders are used.
- `<sha256>`, `<fresh_tester_event_log_path>`, `<matching_export_ml_signals_csv>`, `<real_online_event_log_path>`, and fresh tester log lines are explicit run-time values that must be filled from produced artifacts or tester logs, not design gaps.

Execution note:
- Use `superpowers:subagent-driven-development` only if independent subagents are available and tasks can be split safely. Otherwise use `superpowers:executing-plans` and execute tasks strictly in order.
