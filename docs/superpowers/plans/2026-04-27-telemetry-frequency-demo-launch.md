# Telemetry Frequency Demo Launch Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `telemetry_frequency_v1`: a high-frequency diagnostic ML execution mode plus automated daily reconciliation for demo-account launch readiness.

**Architecture:** Reuse the existing `take_skip_trailing_stop_v2` score/export contour and the existing MT4 direct ML execution path (`EXPERT::ML_TRADE()`, `iSignal=3`). Add bounded diagnostic calibration in Python, tighten/extend existing MQL multi-position behavior only where needed, and build a daily reconciliation CLI that compares exported signals, MT4 logs, and optional tester output. Use `ORDERS.mqh` `INPUT.mqh` `OUTPUT.mqh` and `SERVICE.mqh` as first-choice reuse points for trade operations and MQL-side reporting/monitoring.

**Tech Stack:** Python 3, pandas, pytest, existing SoSimple CLI modules, MQL4 (`$o$imple.mq4`, `lib_ML_Signal.mqh`, `ORDERS.mqh`, `SERVICE.mqh`), MT4 Strategy Tester logs.

---

## Scope Notes

- Do **not** create a git worktree. `AGENTS.md` explicitly says not to use worktrees.
- Stay on feature branch `telemetry-frequency-demo-launch`.
- Do not touch the user's unstaged `AGENTS.md` change unless explicitly asked.
- Treat `SL=3 ATR`, `TP=5 ATR` as the initial diagnostic exit preset, not a profitability optimization.
- The diagnostic mode is not a production or portfolio verdict.

## Read First

- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/specs/2026-04-27-telemetry-frequency-demo-launch-design.md`
- `docs/MT/ml_signal_integration.md`
- `docs/MT/trading_strategy.md`
- `docs/reports/2026-04-18-take-skip-frequency-followup.md`
- `docs/reports/2026-04-19-execution-policy-v2.md`
- `API/export_take_skip_trailing_stop_v2_signals.py`
- `ML/benchmark_signal_export_parity.py`
- `statistics/signal_tracer.py`
- `MT/MQL4/Include/lib_ML_Signal.mqh`
- `MT/MQL4/Include/ORDERS.mqh`
- `MT/MQL4/Include/SERVICE.mqh`

## File Structure

### Files To Create

- `ML/benchmark_telemetry_frequency_calibration.py`
  - Sweeps diagnostic selectors over existing prediction CSV and writes candidate presets.
- `tests/test_benchmark_telemetry_frequency_calibration.py`
  - Unit tests for frequency calibration, selected preset payload, and report outputs.
- `ML/telemetry_daily_reconciliation.py`
  - Daily CLI for signal/export/log reconciliation.
- `tests/test_telemetry_daily_reconciliation.py`
  - Unit tests for MLP open/close parsing, signal matching, output files, and exit-code verdict.
- `docs/ML/benchmark_telemetry_frequency_calibration.py.md`
  - Module documentation.
- `docs/ML/telemetry_daily_reconciliation.py.md`
  - Module documentation.
- `docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`
  - Stage report after implementation and tester proof.

### Files To Modify

- `API/export_take_skip_trailing_stop_v2_signals.py`
  - Optional metadata output for hashes/counts if needed by daily reconciliation.
- `tests/test_export_take_skip_trailing_stop_v2_signals.py`
  - Tests for metadata output if exporter is changed.
- `ML/benchmark_signal_export_parity.py`
  - Reuse or extend parsing helpers if they naturally fit daily reconciliation.
- `tests/test_signal_export_parity.py`
  - Extend only if helper behavior changes.
- `MT/MQL4/Include/lib_ML_Signal.mqh`
  - Existing direct ML path; fix/extend multi-position, ticket logging, spread/ATR logging, SL/TP telemetry.
- `MT/MQL4/Include/ORDERS.mqh`
  - Use or extend existing order operations if compatible with diagnostic ML flow.
- `MT/MQL4/Include/SERVICE.mqh`
  - Use or extend existing report/monitor/tester file mechanisms if compatible.
- `MT/MQL4/Experts/$o$imple.mq4`
  - Version bump and, only if necessary, extern parameter additions.
- `docs/MT/ml_signal_integration.md`
  - Operational guide for `telemetry_frequency_v1`.
- `docs/MT/trading_strategy.md`
  - Update active `iSignal=3` behavior and tester checklist.
- `ML/README.md`
- `API/README.md`
- `MODULE_INDEX.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/research/execution-tracks.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

## Acceptance Rules

- `telemetry_frequency_v1` can produce materially higher trade frequency than current production candidates.
- The selector is calibrated for diagnostic frequency, not PF.
- Existing production exports and rules remain unchanged.
- `ML_MaxPositions=1` preserves old behavior.
- `ML_MaxPositions>1` allows multiple simultaneous ML positions, including multiple same-direction positions, unless broker/platform constraints reject them.
- `ML_MaxPositions` caps total open ML positions.
- Open and close logs include enough fields to match trades by `ticket`.
- Daily reconciliation returns non-zero on critical mismatches.
- Documentation clearly states that the mode is diagnostic and not a profitability verdict.

---

### Task 1: Add Diagnostic Frequency Calibration Benchmark

**Files:**
- Create: `ML/benchmark_telemetry_frequency_calibration.py`
- Create: `tests/test_benchmark_telemetry_frequency_calibration.py`
- Later docs: `docs/ML/benchmark_telemetry_frequency_calibration.py.md`

- [ ] **Step 1: Write failing tests for candidate evaluation**

Create synthetic prediction data with `time`, `signal`, `pred_take_24_x8`, and `pnl_atr` or `trade_pnl_atr`-style outcome column used only for diagnostics.

Test contracts:

```python
def test_calibration_counts_trades_per_day_without_using_pf_as_primary_selector():
    ...

def test_top_k_selector_uses_only_active_signal_rows():
    ...

def test_selected_preset_payload_is_exporter_compatible():
    ...
```

Expected selected rule payload shape:

```json
{
  "mode": "telemetry_frequency_v1",
  "diagnostic": true,
  "winner": {
    "score_target": "take_24_x8",
    "selector": "top_k_probability",
    "threshold": 0.50,
    "exit_atr_multiplier": 8
  },
  "execution": {
    "stop_atr": 3.0,
    "take_profit_atr": 5.0,
    "max_hold_bars": 24,
    "max_positions": 10
  }
}
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_benchmark_telemetry_frequency_calibration.py -q
```

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement the benchmark module**

Implement pure functions:

```python
def load_prediction_frame(path: str | Path) -> pd.DataFrame: ...
def evaluate_candidate(frame: pd.DataFrame, *, score_target: str, selector: str, threshold: float) -> dict: ...
def select_diagnostic_preset(results: pd.DataFrame, *, min_trades_per_day: float | None = None) -> dict: ...
def run_calibration(... ) -> dict: ...
```

Candidate families:

```python
score_targets = ["take_24_x8"]
prob_thresholds = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50]
top_k = [0.20, 0.30, 0.40, 0.50, 0.70, 1.00]
```

Selection rule:

- maximize `trades_per_day`;
- prefer no duplicate opposite signals per same time;
- keep PF/mean PnL only as diagnostic columns;
- do not optimize by PF.

Output files:

- `calibration_grid.csv`
- `selected_rule.json`
- `summary.json`
- `summary.md`

- [ ] **Step 4: Run calibration tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_benchmark_telemetry_frequency_calibration.py -q
```

Expected: PASS.

- [ ] **Step 5: Smoke-run calibration on available prediction CSV**

Use the existing take/skip prediction CSV from the latest report:

```bash
./.venv/bin/python -m ML.benchmark_telemetry_frequency_calibration \
  --predictions ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/test.csv \
  --score-target take_24_x8 \
  --output-dir ML/reports/telemetry_frequency_v1/calibration
```

Expected:

- `selected_rule.json` exists.
- `summary.md` states that the result is diagnostic.
- Frequency is materially higher than production `quality/frequency` baselines.

- [ ] **Step 6: Commit**

```bash
git add ML/benchmark_telemetry_frequency_calibration.py \
  tests/test_benchmark_telemetry_frequency_calibration.py \
  ML/reports/telemetry_frequency_v1/calibration
git commit -m "Add telemetry frequency calibration benchmark"
```

---

### Task 2: Make Export Metadata Reproducible

**Files:**
- Modify: `API/export_take_skip_trailing_stop_v2_signals.py`
- Modify: `tests/test_export_take_skip_trailing_stop_v2_signals.py`

- [ ] **Step 1: Write failing metadata test**

Add a test that calls `export_signals(..., metadata_output=tmp_path / "metadata.json", label="telemetry_frequency_v1")`.

Expected metadata fields:

```json
{
  "label": "telemetry_frequency_v1",
  "predictions_path": "...",
  "rule_path": "...",
  "output_path": "...",
  "predictions_sha256": "...",
  "rule_sha256": "...",
  "output_sha256": "...",
  "rows_total": 123,
  "nonzero_rows": 45,
  "buy_rows": 20,
  "sell_rows": 25,
  "duplicate_time_rows": 0,
  "same_time_opposite_signal_groups": 0
}
```

- [ ] **Step 2: Run exporter tests and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_export_take_skip_trailing_stop_v2_signals.py -q
```

Expected: FAIL because metadata args/output do not exist.

- [ ] **Step 3: Implement metadata output**

Add:

```python
def sha256_file(path: str | Path) -> str: ...
def build_export_metadata(... ) -> dict: ...
```

Extend `export_signals` signature:

```python
metadata_output: str | Path | None = None
label: str = "take_skip_trailing_stop_v2"
```

Extend CLI:

```bash
--metadata-output ML/reports/telemetry_frequency_v1/export_metadata.json
--label telemetry_frequency_v1
```

- [ ] **Step 4: Run exporter tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_export_take_skip_trailing_stop_v2_signals.py -q
```

Expected: PASS.

- [ ] **Step 5: Export telemetry diagnostic signals**

Run:

```bash
./.venv/bin/python -m API.export_take_skip_trailing_stop_v2_signals \
  --predictions ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/test.csv \
  --rule-path ML/reports/telemetry_frequency_v1/calibration/selected_rule.json \
  --output ML/reports/telemetry_frequency_v1/ml_signals_telemetry_frequency_v1.csv \
  --metadata-output ML/reports/telemetry_frequency_v1/export_metadata.json \
  --label telemetry_frequency_v1
```

Expected:

- `ml_signals_telemetry_frequency_v1.csv` exists.
- metadata hashes are present.
- no copy to MT4 yet unless doing an explicit tester run.

- [ ] **Step 6: Commit**

```bash
git add API/export_take_skip_trailing_stop_v2_signals.py \
  tests/test_export_take_skip_trailing_stop_v2_signals.py \
  ML/reports/telemetry_frequency_v1/ml_signals_telemetry_frequency_v1.csv \
  ML/reports/telemetry_frequency_v1/export_metadata.json
git commit -m "Add reproducible telemetry signal export metadata"
```

---

### Task 3: Audit Existing MQL Trade/Service Reuse Points

**Files:**
- Read: `MT/MQL4/Include/lib_ML_Signal.mqh`
- Read: `MT/MQL4/Include/ORDERS.mqh`
- Read: `MT/MQL4/Include/SERVICE.mqh`
- Create or update: `docs/reports/2026-04-27-telemetry-frequency-demo-launch.md` section "MQL reuse audit"

- [ ] **Step 1: Inspect order-operation contracts**

Document whether these existing functions can be reused directly for `telemetry_frequency_v1`:

- `ORDERS_SET()`
- `MODIFY()`
- `CLOSE_BUY(...)`
- `CLOSE_SEL(...)`
- any helpers around `OrderSend`, `OrderClose`, `OrderModify`
- `REPORT(...)`
- `OnTester()`
- tester file creation helpers in `SERVICE.mqh`

- [ ] **Step 2: Decide reuse vs local extension**

Record one of three outcomes for each operation:

- `reuse_as_is`
- `extend_existing_function`
- `keep_local_in_lib_ML_Signal_with_reason`

Expected likely result:

- `REPORT(...)` and service metadata should be reused.
- Existing close/open wrappers may need extension or may be incompatible with ticket-level multi-position ML because `set.BUY`/`set.SEL` represent one desired state.
- If incompatible, document why local `MLP_OpenMarketOrder` / `MLP_CloseSelectedOrder` remains acceptable.

- [ ] **Step 3: Commit audit note before MQL edits**

```bash
git add docs/reports/2026-04-27-telemetry-frequency-demo-launch.md
git commit -m "Document MQL reuse audit for telemetry mode"
```

---

### Task 4: Harden MQL Multi-Position Execution and Telemetry Logs

**Files:**
- Modify: `MT/MQL4/Include/lib_ML_Signal.mqh`
- Modify if audit says needed: `MT/MQL4/Include/ORDERS.mqh`
- Modify if audit says needed: `MT/MQL4/Include/SERVICE.mqh`
- Modify: `MT/MQL4/Experts/$o$imple.mq4`
- Modify docs later: `docs/MT/ml_signal_integration.md`, `docs/MT/trading_strategy.md`

- [ ] **Step 1: Verify current multi-position branch by inspection**

Confirm behavior around:

```cpp
if (ML_MaxPositions > 1) {
   MLP_ManageMultiPositions(Mgc, ExpNum, Sym, ATR);
   ...
   int open_positions = MLP_CountOwnMarketOrders(Mgc, Sym);
   if (open_positions >= ML_MaxPositions) ...
   MLP_OpenMarketOrder(...);
   return;
}
```

Acceptance:

- `BUY.Typ` / `SEL.Typ` must not block multi-position branch.
- same-direction positions must not be rejected by an old state variable.

- [ ] **Step 2: Add/confirm diagnostic SL/TP configuration**

Prefer existing parameters first:

- `ML_BackStopATR = 3.0` as diagnostic SL;
- `ML_TakeProfitATR = 5.0` as diagnostic TP;
- `ML_HoldBars` as max hold for timeout mode if used.

Only add a new extern like `ML_StopATR` if using `ML_BackStopATR` for true diagnostic stop creates unacceptable ambiguity.

- [ ] **Step 3: Add open log fields**

Ensure every `MLP BUY/SELL mode=multi_position` line includes:

```text
mode=telemetry_frequency_v1
ticket=
signal_time=
entry_time=
score=
atr=
spread=
spread_atr=
open_positions=
max_positions=
Val=
Stp=
Prf=
Lot=
```

If no new mode extern is added, use a stable label in the comment/log path when `ML_MaxPositions > 1`.

- [ ] **Step 4: Add close log fields**

Ensure `MLP CLOSE BUY/SELL` from `MLP_CloseSelectedOrder(...)` includes:

```text
ticket=
reason=
entry_time=
exit_time=
hold_bars=
entry=
exit=
atr=
spread=
spread_atr=
pnl_atr=
profit=
```

Acceptance:

- daily parser can link open and close by `ticket`.
- close lines are present for timeout/trailing/broker-side close where possible.

- [ ] **Step 5: Preserve single-position behavior**

Review that the `ML_MaxPositions == 1` branch remains behavior-compatible:

- one active position;
- existing `PosBlock` logs;
- existing timeout/trailing/reversal behavior.

- [ ] **Step 6: Bump expert version**

Update:

```cpp
#define VERSION "260.xxx"
```

in `MT/MQL4/Experts/$o$imple.mq4`.

- [ ] **Step 7: Static verification**

Run text checks:

```bash
rg -n "telemetry_frequency_v1|spread_atr|open_positions|max_positions|ticket=" MT/MQL4/Include/lib_ML_Signal.mqh MT/MQL4/Experts/\\$o\\$imple.mq4
```

Expected: new log fields are present.

- [ ] **Step 8: Commit**

```bash
git add MT/MQL4/Include/lib_ML_Signal.mqh MT/MQL4/Include/ORDERS.mqh MT/MQL4/Include/SERVICE.mqh MT/MQL4/Experts/\\$o\\$imple.mq4
git commit -m "Harden telemetry multi-position MQL execution"
```

Only add `ORDERS.mqh` / `SERVICE.mqh` if they were actually modified.

---

### Task 5: Add Daily Telemetry Reconciliation CLI

**Files:**
- Create: `ML/telemetry_daily_reconciliation.py`
- Create: `tests/test_telemetry_daily_reconciliation.py`
- Reuse: `ML/benchmark_signal_export_parity.py`

- [ ] **Step 1: Write failing parser tests**

Use log fixture lines:

```text
MLP BUY mode=telemetry_frequency_v1 ticket=101 signal_time=2025.01.01 00:00 entry_time=2025.01.01 01:00 score=0.88 atr=12.34 spread=0.20 spread_atr=0.0162 open_positions=2 max_positions=10 Val=2500.00 Stp=2463.00 Prf=2561.70 Lot=0.10
MLP CLOSE BUY reason=TakeProfit ticket=101 entry_time=2025.01.01 01:00 exit_time=2025.01.01 07:00 hold_bars=6 entry=2500.00 exit=2561.70 atr=12.34 spread=0.20 spread_atr=0.0162 pnl_atr=5.0000 profit=123.45
```

Tests:

```python
def test_parse_mlp_open_close_events_links_by_ticket(): ...
def test_reconciliation_flags_missing_opened_trade(): ...
def test_run_daily_reconciliation_writes_required_outputs(): ...
def test_critical_mismatch_sets_nonzero_exit_code(): ...
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_telemetry_daily_reconciliation.py -q
```

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement parser and reconciliation functions**

Implement:

```python
def parse_mlp_events(log_path: str | Path) -> dict[str, pd.DataFrame]: ...
def load_signal_export(signals_path: str | Path) -> pd.DataFrame: ...
def reconcile_expected_vs_opened(signals: pd.DataFrame, opens: pd.DataFrame) -> pd.DataFrame: ...
def reconcile_open_close(opens: pd.DataFrame, closes: pd.DataFrame) -> pd.DataFrame: ...
def build_daily_summary(...) -> dict: ...
def run_daily_reconciliation(...) -> dict: ...
```

Critical mismatches:

- signal expected but no open and no matching skip reason;
- wrong direction;
- duplicate open on same `signal_time` when only one open per bar is allowed;
- open without signal;
- stale export metadata hash mismatch;
- missing close for completed tester period.

- [ ] **Step 4: Implement CLI**

CLI:

```bash
./.venv/bin/python -m ML.telemetry_daily_reconciliation \
  --signals MT/MQL4/Files/ml_signals.csv \
  --mt4-log MT/tester/logs/YYYYMMDD.log \
  --export-metadata ML/reports/telemetry_frequency_v1/export_metadata.json \
  --output-dir ML/reports/telemetry_frequency_v1/daily/YYYY-MM-DD \
  --label telemetry_frequency_v1
```

Optional:

```bash
--tester-log MT/tester/logs/YYYYMMDD_tester.log
--online-log MT/live/logs/YYYYMMDD.log
```

Outputs:

- `summary.json`
- `summary.md`
- `signals_diff.csv`
- `trades_reconciliation.csv`

- [ ] **Step 5: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_telemetry_daily_reconciliation.py tests/test_signal_export_parity.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/telemetry_daily_reconciliation.py tests/test_telemetry_daily_reconciliation.py
git commit -m "Add telemetry daily reconciliation CLI"
```

---

### Task 6: Add Documentation and Index Entries

**Files:**
- Create: `docs/ML/benchmark_telemetry_frequency_calibration.py.md`
- Create: `docs/ML/telemetry_daily_reconciliation.py.md`
- Modify: `docs/MT/ml_signal_integration.md`
- Modify: `docs/MT/trading_strategy.md`
- Modify: `ML/README.md`
- Modify: `API/README.md`
- Modify: `MODULE_INDEX.md`

- [ ] **Step 1: Document calibration CLI**

Create `docs/ML/benchmark_telemetry_frequency_calibration.py.md` with:

- purpose;
- inputs;
- outputs;
- example command;
- warning that PF is diagnostic only.

- [ ] **Step 2: Document daily reconciliation CLI**

Create `docs/ML/telemetry_daily_reconciliation.py.md` with:

- purpose;
- required inputs;
- output files;
- critical mismatch list;
- daily run example.

- [ ] **Step 3: Update MT docs**

In `docs/MT/ml_signal_integration.md` add:

- `telemetry_frequency_v1` section;
- recommended diagnostic parameters:
  - `iSignal=3`;
  - `ML_MaxPositions>1`;
  - `ML_BackStopATR=3`;
  - `ML_TakeProfitATR=5`;
  - `ML_HoldBars=<selected>`;
  - fixed minimal lot / demo only.

In `docs/MT/trading_strategy.md` add:

- current multi-position behavior;
- log fields;
- tester checklist for telemetry mode.

- [ ] **Step 4: Update indexes**

Update:

- `ML/README.md`
- `API/README.md` if exporter CLI changed;
- `MODULE_INDEX.md` for new Python modules.

- [ ] **Step 5: Run focused docs checks**

Run:

```bash
rg -n "telemetry_frequency_v1|benchmark_telemetry_frequency_calibration|telemetry_daily_reconciliation" docs ML/README.md API/README.md MODULE_INDEX.md
```

Expected: all new modules and mode names are discoverable.

- [ ] **Step 6: Commit**

```bash
git add docs/ML/benchmark_telemetry_frequency_calibration.py.md \
  docs/ML/telemetry_daily_reconciliation.py.md \
  docs/MT/ml_signal_integration.md \
  docs/MT/trading_strategy.md \
  ML/README.md API/README.md MODULE_INDEX.md
git commit -m "Document telemetry frequency demo launch tools"
```

---

### Task 7: Run Verification Suite

**Files:**
- No new files expected.

- [ ] **Step 1: Run focused Python tests**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_benchmark_telemetry_frequency_calibration.py \
  tests/test_export_take_skip_trailing_stop_v2_signals.py \
  tests/test_signal_export_parity.py \
  tests/test_telemetry_daily_reconciliation.py -q
```

Expected: PASS.

- [ ] **Step 2: Run related existing tests**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_benchmark_execution_policy_v2.py \
  tests/test_export_take_skip_v2_predictions.py \
  tests/test_benchmark_cross_instrument_robustness.py -q
```

Expected: PASS.

- [ ] **Step 3: Generate telemetry export parity summary without MT4 log**

Run:

```bash
./.venv/bin/python -m ML.benchmark_signal_export_parity \
  --signals ML/reports/telemetry_frequency_v1/ml_signals_telemetry_frequency_v1.csv \
  --output-dir ML/reports/telemetry_frequency_v1/export_parity \
  --label telemetry_frequency_v1_export_only
```

Expected:

- `summary.json` exists.
- no exception.

- [ ] **Step 4: Commit verification artifacts if they are canonical**

Only commit reports that are part of the stage evidence:

```bash
git add ML/reports/telemetry_frequency_v1/export_parity
git commit -m "Add telemetry frequency verification artifacts"
```

Skip this commit if artifacts are temporary.

---

### Task 8: Manual MT4 Tester Proof

**Files:**
- Modify after proof: `docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`
- Use: `MT/tester/files/ml_signals.csv`
- Use: `MT/tester/$o$imple.ini`
- Use: `MT/tester/logs/*.log`

- [ ] **Step 1: Copy telemetry signals to tester/runtime paths**

Run only when ready for manual tester:

```bash
./.venv/bin/python -m API.export_take_skip_trailing_stop_v2_signals \
  --predictions ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/test.csv \
  --rule-path ML/reports/telemetry_frequency_v1/calibration/selected_rule.json \
  --output MT/tester/files/ml_signals.csv \
  --metadata-output ML/reports/telemetry_frequency_v1/tester_export_metadata.json \
  --label telemetry_frequency_v1 \
  --copy-to-mt4
```

- [ ] **Step 2: Configure MT4 tester**

Set:

- `iSignal=3`
- `ML_MaxPositions=<selected from calibration>`
- `ML_BackStopATR=3.0`
- `ML_TakeProfitATR=5.0`
- `ML_UseScoreFilter=false` if CSV already prefiltered
- `ML_AllowReversal=false`
- fixed minimal lot / `Risk=0`

- [ ] **Step 3: Run MT4 tester manually**

Acceptance:

- version in log matches updated `$o$imple.mq4`;
- several positions can be open at once;
- at least one same-direction multi-position case appears if signals allow it;
- `MaxPositions` blocks only after reaching the configured limit;
- logs include `ticket`, `spread_atr`, `open_positions`.

- [ ] **Step 4: Run daily reconciliation on tester log**

Run:

```bash
./.venv/bin/python -m ML.telemetry_daily_reconciliation \
  --signals MT/tester/files/ml_signals.csv \
  --mt4-log MT/tester/logs/<LATEST>.log \
  --export-metadata ML/reports/telemetry_frequency_v1/tester_export_metadata.json \
  --output-dir ML/reports/telemetry_frequency_v1/tester_reconciliation \
  --label telemetry_frequency_v1_tester
```

Expected:

- exit code `0` if no critical mismatches;
- `summary.md` explains non-critical differences;
- `trades_reconciliation.csv` links open/close by ticket.

- [ ] **Step 5: Commit tester proof report**

```bash
git add docs/reports/2026-04-27-telemetry-frequency-demo-launch.md \
  ML/reports/telemetry_frequency_v1/tester_reconciliation
git commit -m "Add telemetry frequency MT4 tester proof"
```

---

### Task 9: Stage Close and Wiki Sync

**Files:**
- Modify: `docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/execution-tracks.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

- [ ] **Step 1: Write final stage report**

Report must include:

- selected diagnostic preset;
- trade frequency;
- MQL reuse audit verdict for `ORDERS.mqh` / `SERVICE.mqh`;
- MQL changes made;
- daily reconciliation command;
- tester proof result;
- explicit statement: diagnostic mode is not a profitability verdict.

- [ ] **Step 2: Update changelog and handoff**

Update:

- first section of `CHANGELOG.md`;
- `CONTEXT_HANDOFF.md` current stage / next step / risks.

- [ ] **Step 3: Update wiki synthesis**

Update `wiki/research/execution-tracks.md` with a short operational subsection:

- `telemetry_frequency_v1`;
- purpose;
- how it relates to production systems;
- current readiness.

Update `wiki/index.md` if needed.

Append `wiki/log.md`.

- [ ] **Step 4: Regenerate integrity map**

Run:

```bash
./.venv/bin/python wiki/wiki.py generate
```

Expected: `wiki/REPO_integrity.md` updated.

- [ ] **Step 5: Run wiki status**

Run:

```bash
./.venv/bin/python wiki/wiki.py status
```

Expected:

- existing unrelated uncovered/broken wiki items may remain;
- no new broken links from this stage.

- [ ] **Step 6: Commit stage close**

```bash
git add docs/reports/2026-04-27-telemetry-frequency-demo-launch.md \
  CHANGELOG.md CONTEXT_HANDOFF.md \
  wiki/research/execution-tracks.md wiki/index.md wiki/log.md wiki/REPO_integrity.md
git commit -m "Close telemetry frequency demo launch stage"
```

---

## Final Verification Checklist

- [ ] `telemetry_frequency_v1` selected rule exists.
- [ ] Export metadata contains hashes and counts.
- [ ] MT4 tester opens multiple positions with `ML_MaxPositions>1`.
- [ ] Same-direction multi-position is not blocked by legacy state.
- [ ] Logs include `ticket`, `spread_atr`, SL/TP, and open position count.
- [ ] Daily reconciliation writes all required outputs.
- [ ] Daily reconciliation returns non-zero on critical mismatch fixtures.
- [ ] Docs and indexes are updated.
- [ ] `wiki/REPO_integrity.md` regenerated.
- [ ] User's unrelated `AGENTS.md` change is not reverted or accidentally committed.
