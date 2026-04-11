# Triple Barrier MT4-Matched Python Evaluation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Собрать Python-режим для `triple_barrier`, который повторяет MT4 execution-семантику один в один, чтобы получить честный offline verdict без разрыва между `test`-оценкой и реальным тестером.

**Architecture:** Этот этап не должен переобучать `triple_barrier`, калибратор или frozen rule. Вся работа идёт поверх уже зафиксированных артефактов: `tb_selected_rule.json`, `ml_signals_tb.csv` и labeled CSV. Новый Python-контур должен повторять реальные MT4-правила: вход на следующем баре, не более одной позиции, пропуск сигнала при открытой позиции, закрытие по SL/TP/timeout и принудительное закрытие по встречному сигналу. После этого нужна сверка Python-симуляции с существующими MT4 reconciliation-артефактами и выпуск итогового verdict report.

**Tech Stack:** Python 3.11, pandas, numpy, pytest, JSON, markdown reports, existing `statistics/signal_tracer.py`, existing MT4 TB signal export

---

## File Map

### Read First
- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/reports/2026-04-08-triple-barrier-hardening.md`
- `docs/reports/2026-04-08-triple-barrier-runtime-verdict.md`
- `wiki/research/execution-tracks.md`
- `ML/reports/tb_selected_rule.json`
- `ML/reports/evaluate_test_tb.md`
- `MT/MQL4/Include/lib_ML_Signal_TB.mqh`

### Existing Files To Reuse
- `statistics/signal_tracer.py`
- `tests/test_signal_tracer_tb.py`
- `tests/test_triple_barrier_first_touch.py`
- `tests/test_triple_barrier_calibration.py`
- `tests/test_triple_barrier_training.py`

### Files To Create
- `ML/triple_barrier_mt4_execution.py`
- `ML/benchmark_triple_barrier_mt4_execution.py`
- `tests/test_triple_barrier_mt4_execution.py`
- `ML/reports/tb_mt4_python_validation_trades.csv`
- `ML/reports/tb_mt4_python_test_trades.csv`
- `ML/reports/tb_mt4_python_summary.json`
- `ML/reports/tb_mt4_python_yearly.csv`
- `docs/reports/2026-04-11-triple-barrier-mt4-matched-python-eval.md`

### Files To Modify Only If Needed
- `statistics/signal_tracer.py`
- `tests/test_signal_tracer_tb.py`

### Frozen Inputs For This Stage
- Rule: `theta=0.475`, `min_ev=0.10`
- Validation reference: `121 trades`, `PF=1.53`
- Offline test reference before MT4 matching: `253 trades`, `PF=1.11`
- MT4 runtime reference: `92 trades`, `PF=1.27`

---

### Task 1: Freeze The MT4 Execution Contract In Tests

**Files:**
- Create: `tests/test_triple_barrier_mt4_execution.py`
- Read: `MT/MQL4/Include/lib_ML_Signal_TB.mqh`

- [ ] **Step 1: Write failing tests for the five critical MT4 semantics**

Cover exactly these cases:
- signal opens on the next bar, not on the signal bar itself
- if a position is already open, the next signal is skipped
- timeout closes the position after the configured hold window
- opposite signal closes the current position with reason `TB_Reversal`
- SL/TP outcome is determined by path order, not by close-only return

Use small toy price paths with explicit ATR, signal time and expected reason strings.

- [ ] **Step 2: Run the new test file and verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_triple_barrier_mt4_execution.py -q
```

Expected:
- FAIL because the execution simulator does not exist yet.

- [ ] **Step 3: Inspect the MQL4 contract before implementation**

Read these exact lines:

```bash
sed -n '118,220p' MT/MQL4/Include/lib_ML_Signal_TB.mqh
sed -n '696,860p' statistics/signal_tracer.py
```

Expected:
- Contract is frozen before writing Python logic.

- [ ] **Step 4: Commit the failing test scaffold**

```bash
git add tests/test_triple_barrier_mt4_execution.py
git commit -m "test: define tb mt4 execution contract"
```

---

### Task 2: Implement The MT4-Matched Execution Core

**Files:**
- Create: `ML/triple_barrier_mt4_execution.py`
- Modify: `tests/test_triple_barrier_mt4_execution.py`

- [ ] **Step 1: Implement the minimal simulator to satisfy the contract**

`ML/triple_barrier_mt4_execution.py` must include:
- signal loader for `ml_signals_tb.csv`
- dataset loader for `DATA/Nero_validation_labeled.csv` and `DATA/Nero_test_labeled.csv`
- event loop with:
  - next-bar entry
  - one open position max
  - `PosBlock` skip while open
  - `TB_Reversal` close on opposite signal
  - `HoldOverTime` close after fixed timeout
  - first-touch `TP/SL` close using path order

Each closed trade row must contain at least:
- `entry_time`
- `exit_time`
- `direction`
- `close_reason`
- `pnl_atr`
- `signal_time`
- `source_target`

- [ ] **Step 2: Re-run the new test file and verify it passes**

Run:

```bash
./.venv/bin/python -m pytest tests/test_triple_barrier_mt4_execution.py -q
```

Expected:
- PASS

- [ ] **Step 3: Run the existing narrow TB suite to ensure no regression**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_triple_barrier_first_touch.py \
  tests/test_triple_barrier_calibration.py \
  tests/test_triple_barrier_training.py \
  tests/test_signal_tracer_tb.py \
  tests/test_triple_barrier_mt4_execution.py -q
```

Expected:
- PASS

- [ ] **Step 4: Commit**

```bash
git add ML/triple_barrier_mt4_execution.py \
  tests/test_triple_barrier_mt4_execution.py
git commit -m "feat: add mt4-matched triple barrier execution core"
```

---

### Task 3: Add A Benchmark CLI And Summary Artefacts

**Files:**
- Create: `ML/benchmark_triple_barrier_mt4_execution.py`
- Modify: `tests/test_triple_barrier_mt4_execution.py`

- [ ] **Step 1: Extend the test file with a CLI smoke test**

The CLI test must verify that one command produces:
- trade-level CSV
- yearly summary CSV
- summary JSON

Use a tiny synthetic split under `tmp_path`.

- [ ] **Step 2: Run the test file and verify the CLI case fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_triple_barrier_mt4_execution.py -q
```

Expected:
- FAIL because the benchmark CLI does not exist yet.

- [ ] **Step 3: Implement the CLI**

`ML/benchmark_triple_barrier_mt4_execution.py` must:
- accept `--signals MT/MQL4/Files/ml_signals_tb.csv`
- accept `--labeled DATA/Nero_validation_labeled.csv` or `DATA/Nero_test_labeled.csv`
- accept `--rule-json ML/reports/tb_selected_rule.json`
- accept `--output-trades`
- accept `--output-summary`
- accept `--output-yearly`

The summary JSON must include:

```json
{
  "trades": 0,
  "wins": 0,
  "losses": 0,
  "timeouts": 0,
  "reversals": 0,
  "posblock_skips": 0,
  "pf": 0.0,
  "win_rate": 0.0
}
```

- [ ] **Step 4: Re-run the CLI smoke test and verify it passes**

Run:

```bash
./.venv/bin/python -m pytest tests/test_triple_barrier_mt4_execution.py -q
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add ML/benchmark_triple_barrier_mt4_execution.py \
  tests/test_triple_barrier_mt4_execution.py
git commit -m "feat: add tb mt4-matched benchmark cli"
```

---

### Task 4: Run Validation/Test With The Frozen Rule

**Files:**
- Create: `ML/reports/tb_mt4_python_validation_trades.csv`
- Create: `ML/reports/tb_mt4_python_test_trades.csv`
- Create: `ML/reports/tb_mt4_python_summary.json`
- Create: `ML/reports/tb_mt4_python_yearly.csv`

- [ ] **Step 1: Run the full verification suite before producing research artefacts**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_triple_barrier_first_touch.py \
  tests/test_triple_barrier_calibration.py \
  tests/test_triple_barrier_training.py \
  tests/test_signal_tracer_tb.py \
  tests/test_triple_barrier_mt4_execution.py -q
```

Expected:
- PASS

- [ ] **Step 2: Run the validation split with the frozen TB rule**

Run:

```bash
./.venv/bin/python -m ML.benchmark_triple_barrier_mt4_execution \
  --signals MT/MQL4/Files/ml_signals_tb.csv \
  --labeled DATA/Nero_validation_labeled.csv \
  --rule-json ML/reports/tb_selected_rule.json \
  --output-trades ML/reports/tb_mt4_python_validation_trades.csv \
  --output-summary ML/reports/tb_mt4_python_summary.json \
  --output-yearly ML/reports/tb_mt4_python_yearly.csv
```

Expected:
- Validation artefacts are written without changing the rule.

- [ ] **Step 3: Run the test split with the same frozen rule**

Run:

```bash
./.venv/bin/python -m ML.benchmark_triple_barrier_mt4_execution \
  --signals MT/MQL4/Files/ml_signals_tb.csv \
  --labeled DATA/Nero_test_labeled.csv \
  --rule-json ML/reports/tb_selected_rule.json \
  --output-trades ML/reports/tb_mt4_python_test_trades.csv \
  --output-summary ML/reports/tb_mt4_python_summary.json \
  --output-yearly ML/reports/tb_mt4_python_yearly.csv
```

Expected:
- Test artefacts are written with exactly the same frozen rule.

- [ ] **Step 4: Sanity-check the resulting summary**

Run:

```bash
sed -n '1,40p' ML/reports/tb_mt4_python_summary.json
sed -n '1,20p' ML/reports/tb_mt4_python_yearly.csv
```

Expected:
- Trade count should move materially closer to the MT4 runtime reference (`92`) than the old offline count (`253`).

- [ ] **Step 5: Commit**

```bash
git add ML/reports/tb_mt4_python_validation_trades.csv \
  ML/reports/tb_mt4_python_test_trades.csv \
  ML/reports/tb_mt4_python_summary.json \
  ML/reports/tb_mt4_python_yearly.csv
git commit -m "exp: run tb mt4-matched python evaluation"
```

---

### Task 5: Compare Against Existing MT4 Runtime Artefacts

**Files:**
- Read: `ML/reports/tb_mt4_reconciliation.csv`
- Read: `ML/reports/tb_mt4_reconciliation_losses.csv`
- Modify only if needed: `statistics/signal_tracer.py`
- Modify only if needed: `tests/test_signal_tracer_tb.py`

- [ ] **Step 1: Confirm the MT4 reconciliation artefacts exist**

Run:

```bash
test -f ML/reports/tb_mt4_reconciliation.csv
test -f ML/reports/tb_mt4_reconciliation_losses.csv
echo "tb runtime artefacts are present"
```

Expected:
- Shell exits `0`

Stop condition:
- If these files do not exist, stop and use the already existing MT4 runtime-verdict workflow first. Do not invent a new runtime baseline.

- [ ] **Step 2: Compare Python and MT4 category counts**

Run a small comparison script or notebook-free one-shot command that produces:
- trade count delta
- PF delta
- `close_reason` distribution vs MT4 categories
- unmatched edge cases

Expected:
- Most of the old gap (`253` vs `92`) should now be explained by Python using MT4 semantics instead of naive offline counting.

- [ ] **Step 3: If tracer mismatch is due to parser assumptions, fix tracer before reporting**

Run:

```bash
./.venv/bin/python -m pytest tests/test_signal_tracer_tb.py -q
```

Expected:
- PASS

Only if needed:
- patch `statistics/signal_tracer.py`
- extend `tests/test_signal_tracer_tb.py`

- [ ] **Step 4: Commit tracer changes only if they were necessary**

```bash
git add statistics/signal_tracer.py tests/test_signal_tracer_tb.py
git commit -m "fix: align tb tracer with mt4 matched execution"
```

Skip this commit if nothing changed.

---

### Task 6: Write The Final Verdict And Handoff

**Files:**
- Create: `docs/reports/2026-04-11-triple-barrier-mt4-matched-python-eval.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`

- [ ] **Step 1: Write the report from the frozen rule and produced artefacts**

The report must include:
- frozen rule
- validation summary
- test summary
- comparison table: old offline vs MT4-matched Python vs MT4 tester
- clear verdict on whether TB is a secondary live candidate or only a control track

- [ ] **Step 2: Update `CHANGELOG.md`**

Include:
- new Python-matched trade count
- PF
- delta against MT4 tester
- verdict

- [ ] **Step 3: Update `CONTEXT_HANDOFF.md`**

If the new Python mode stays close to MT4:
- mark TB as a reliable secondary/control track

If the gap remains large:
- next TB step becomes reconciliation/debugging, not new model work

- [ ] **Step 4: Run final verification**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_triple_barrier_first_touch.py \
  tests/test_triple_barrier_calibration.py \
  tests/test_triple_barrier_training.py \
  tests/test_signal_tracer_tb.py \
  tests/test_triple_barrier_mt4_execution.py -q
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add docs/reports/2026-04-11-triple-barrier-mt4-matched-python-eval.md \
  CHANGELOG.md CONTEXT_HANDOFF.md
git commit -m "docs: record tb mt4-matched evaluation verdict"
```
