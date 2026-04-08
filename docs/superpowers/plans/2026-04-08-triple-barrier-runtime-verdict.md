# Triple Barrier MT4 Runtime Verdict Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Получить свежую MT4 runtime-проверку для уже замороженного `triple_barrier` правила, выполнить полную Python ↔ MT4 сверку и вынести финальный go/no-go verdict по TB как отдельному EA-режиму.

**Architecture:** Базовый offline-hardening уже завершён: first-touch labels, validation-only calibration, frozen rule и `ml_signals_tb.csv` готовы. Продолжение этого этапа не должно ретюнить модель или пороги. Единственная цель теперь — взять свежий TB tester log, прогнать его через существующий reconciliation tooling и на этой базе выпустить честный runtime verdict.

**Tech Stack:** Python 3.11, pytest, pandas/csv, existing `statistics/signal_tracer.py`, MT4 Strategy Tester logs, Markdown reports

---

## File Structure

### Read First
- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/reports/2026-04-08-triple-barrier-hardening.md`
- `ML/reports/threshold_analysis_tb.md`
- `ML/reports/evaluate_test_tb.md`
- `ML/reports/tb_selected_rule.json`

### Existing Runtime Inputs
- `MT/MQL4/Files/ml_signals_tb.csv`
- `MT/MQL4/Include/lib_ML_Signal_TB.mqh`
- `statistics/signal_tracer.py`
- `tests/test_signal_tracer_tb.py`

### Artefacts To Create During Execution
- `ML/reports/tb_mt4_reconciliation.csv`
- `ML/reports/tb_mt4_reconciliation_losses.csv`
- `docs/reports/2026-04-08-triple-barrier-runtime-verdict.md`

### Files To Modify Only If Needed
- `statistics/signal_tracer.py`
- `tests/test_signal_tracer_tb.py`
- `docs/statistics/signal_tracer.py.md`

### Files To Update At Stage Close
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`

---

### Task 1: Bootstrap The Frozen TB Baseline

**Files:**
- Read: `AGENTS.md`
- Read: `CONTEXT_HANDOFF.md`
- Read: `docs/reports/2026-04-08-triple-barrier-hardening.md`
- Read: `ML/reports/threshold_analysis_tb.md`
- Read: `ML/reports/evaluate_test_tb.md`
- Read: `ML/reports/tb_selected_rule.json`

- [ ] **Step 1: Read the current stage context**

Run:

```bash
sed -n '1,220p' AGENTS.md
sed -n '1,220p' CONTEXT_HANDOFF.md
sed -n '1,260p' docs/reports/2026-04-08-triple-barrier-hardening.md
sed -n '1,200p' ML/reports/threshold_analysis_tb.md
sed -n '1,200p' ML/reports/evaluate_test_tb.md
cat ML/reports/tb_selected_rule.json
```

Expected:
- Frozen rule is still `theta=0.75`, `min_ev=0.0`
- Offline test reference remains `PF=4.31`, `Trades=141`, `Wins/Losses/Timeouts=103/38/10`

- [ ] **Step 2: Verify required TB artifacts exist before touching anything**

Run:

```bash
test -f MT/MQL4/Files/ml_signals_tb.csv
test -f ML/reports/tb_selected_rule.json
test -f ML/reports/tb_probability_calibrator.joblib
test -f statistics/signal_tracer.py
echo "TB baseline artifacts are present"
```

Expected:
- Shell exits `0`
- Final line: `TB baseline artifacts are present`

- [ ] **Step 3: Re-run the narrow TB regression suite**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_triple_barrier_first_touch.py \
  tests/test_triple_barrier_calibration.py \
  tests/test_generate_signals_research.py \
  tests/test_signal_tracer_tb.py \
  tests/test_triple_barrier_training.py -q
```

Expected:
- `5 passed`

- [ ] **Step 4: Freeze the offline comparison targets in your notes**

Use these exact reference numbers in the later runtime report:

```text
offline_test_pf = 4.31
offline_test_trades = 141
offline_test_wins = 103
offline_test_losses = 38
offline_test_timeouts = 10
offline_rule_theta = 0.75
offline_rule_min_ev = 0.0
```

Expected:
- These constants are copied into your scratchpad and used later for comparison


### Task 2: Acquire A Fresh TB Strategy Tester Log

**Files:**
- Read: `MT/MQL4/Include/lib_ML_Signal_TB.mqh`
- Read: `MT/MQL4/Files/ml_signals_tb.csv`
- Read: `MT/**/*.log`

- [ ] **Step 1: Search the workspace for TB tester output**

Run:

```bash
rg -n "TB BUY|TB SELL|TB SKIP" MT -g '*.log'
```

Expected:
- At least one match from a fresh tester log

Stop condition:
- If this command returns no matches, stop the execution here and ask the user for a fresh MT4 Strategy Tester log produced with:
  - `iSignal=5`
  - `Tper=24`
  - current `MT/MQL4/Files/ml_signals_tb.csv`

- [ ] **Step 2: Identify the exact log file you will reconcile**

Run:

```bash
find MT -type f -name '*.log' -printf '%TY-%Tm-%Td %TT %p\n' | sort -r | head -n 20
```

Expected:
- You can point to one concrete log path that contains `TB BUY` / `TB SELL` entries

- [ ] **Step 3: Inspect the first TB lines before running any parser**

Run:

```bash
rg -n "TB BUY|TB SELL|TB SKIP" <TB_LOG_PATH> | head -n 20
head -n 5 MT/MQL4/Files/ml_signals_tb.csv
rg -n "TB BUY|TB SELL" MT/MQL4/Include/lib_ML_Signal_TB.mqh
```

Expected:
- Log lines visibly contain `prob=... ev=... SL=...ATR TP=...ATR`
- `ml_signals_tb.csv` header is `time;signal;sl_atr;tp_atr;prob;ev`
- MQL print format matches the parser assumptions in `statistics/signal_tracer.py`

- [ ] **Step 4: If the log format visibly differs, do not continue to verdict**

Run:

```bash
sed -n '680,760p' statistics/signal_tracer.py
sed -n '1,220p' tests/test_signal_tracer_tb.py
```

Expected:
- You either confirm the regex matches the real log format, or you stop and do a separate tracer bugfix before proceeding


### Task 3: Run Full TB Reconciliation And Export Artefacts

**Files:**
- Read: `statistics/signal_tracer.py`
- Create: `ML/reports/tb_mt4_reconciliation.csv`
- Create: `ML/reports/tb_mt4_reconciliation_losses.csv`

- [ ] **Step 1: Run the full from-log reconciliation**

Run:

```bash
./.venv/bin/python statistics/signal_tracer.py \
  --from-log <TB_LOG_PATH> \
  --signals MT/MQL4/Files/ml_signals_tb.csv \
  --csv-out ML/reports/tb_mt4_reconciliation.csv
```

Expected:
- Script exits `0`
- It prints a non-zero trade count
- `ML/reports/tb_mt4_reconciliation.csv` is created

- [ ] **Step 2: Run the losses-only slice for failure analysis**

Run:

```bash
./.venv/bin/python statistics/signal_tracer.py \
  --from-log <TB_LOG_PATH> \
  --signals MT/MQL4/Files/ml_signals_tb.csv \
  --losses-only \
  --csv-out ML/reports/tb_mt4_reconciliation_losses.csv
```

Expected:
- Script exits `0`
- `ML/reports/tb_mt4_reconciliation_losses.csv` is created

- [ ] **Step 3: Verify both CSV artefacts exist and are non-empty**

Run:

```bash
wc -l ML/reports/tb_mt4_reconciliation.csv
wc -l ML/reports/tb_mt4_reconciliation_losses.csv
```

Expected:
- Both files exist
- Each file has more than `1` line

- [ ] **Step 4: Quick sanity-check the exported categories**

Run:

```bash
./.venv/bin/python - <<'PY'
import csv
from collections import Counter
from pathlib import Path

path = Path("ML/reports/tb_mt4_reconciliation.csv")
rows = list(csv.DictReader(path.open(encoding="utf-8"), delimiter=';'))
print("rows", len(rows))
print("categories", Counter(r["category"] for r in rows))
print("mt4_results", Counter(r["mt4_result"] for r in rows))
print("unknown_count", sum(r["category"] == "UNKNOWN" for r in rows))
PY
```

Expected:
- `rows` is non-zero
- `unknown_count` is ideally `0`
- Categories and MT4 results are readable and finite

Stop condition:
- If `rows == 0` or `unknown_count > 0`, do not write the final verdict yet; fix reconciliation correctness first


### Task 4: Quantify The Python ↔ MT4 Gap

**Files:**
- Read: `ML/reports/tb_mt4_reconciliation.csv`
- Read: `ML/reports/tb_mt4_reconciliation_losses.csv`
- Read: `ML/reports/evaluate_test_tb.md`

- [ ] **Step 1: Compute headline runtime metrics from the reconciliation CSV**

Run:

```bash
./.venv/bin/python - <<'PY'
import csv
from collections import Counter
from pathlib import Path

OFFLINE_TEST_PF = 4.31
OFFLINE_TEST_TRADES = 141

path = Path("ML/reports/tb_mt4_reconciliation.csv")
rows = list(csv.DictReader(path.open(encoding="utf-8"), delimiter=';'))
rows = [r for r in rows if r["mt4_result"] and r["mt4_result"] != "OPEN"]

pnl = [float(r["mt4_pnl_atr"] or 0.0) for r in rows]
gross_profit = sum(x for x in pnl if x > 0)
gross_loss = -sum(x for x in pnl if x < 0)
pf = gross_profit / gross_loss if gross_loss else float("inf")

mean_abs_sl_delta = sum(abs(float(r["sl_delta"] or 0.0)) for r in rows) / len(rows)
mean_abs_tp_delta = sum(abs(float(r["tp_delta"] or 0.0)) for r in rows) / len(rows)
mean_abs_atr_delta = sum(abs(float(r["atr_delta"] or 0.0)) for r in rows) / len(rows)

print("runtime_trades", len(rows))
print("runtime_pf", round(pf, 4))
print("pf_vs_offline_ratio", round(pf / OFFLINE_TEST_PF, 4))
print("trade_count_gap", len(rows) - OFFLINE_TEST_TRADES)
print("mt4_results", Counter(r["mt4_result"] for r in rows))
print("tb_categories", Counter(r["category"] for r in rows))
print("mean_abs_sl_delta", round(mean_abs_sl_delta, 4))
print("mean_abs_tp_delta", round(mean_abs_tp_delta, 4))
print("mean_abs_atr_delta", round(mean_abs_atr_delta, 4))
print("category_x_result")
for pair, count in sorted(Counter((r["category"], r["mt4_result"]) for r in rows).items()):
    print(pair, count)
PY
```

Expected:
- The command prints concrete runtime metrics you can paste into the final report

- [ ] **Step 2: Inspect the loss slice manually before writing the conclusion**

Run:

```bash
sed -n '1,40p' ML/reports/tb_mt4_reconciliation_losses.csv
```

Expected:
- You can see whether losses cluster around:
  - `SL_FIRST`
  - `TIMEOUT`
  - `LOSS(MKT)`
  - large `sl_delta` / `tp_delta`

- [ ] **Step 3: Record a conservative verdict rubric before interpreting the numbers**

Use this rubric verbatim:

```text
1. Do not claim runtime parity if the log is missing, parser coverage is incomplete, or UNKNOWN categories remain.
2. Do not call TB production-ready only because offline PF was strong; MT4 evidence is the deciding layer now.
3. If MT4 remains profitable and structural mismatches are small, verdict = "candidate survives runtime check".
4. If MT4 collapses materially or categories contradict the frozen TB labels, verdict = "do not promote TB mode".
5. If evidence is mixed, verdict = "promising but unresolved" and list the exact blocker.
```

Expected:
- The later report uses one of these three verdicts exactly:
  - `candidate survives runtime check`
  - `do not promote TB mode`
  - `promising but unresolved`


### Task 5: Write The Final Runtime Verdict Report

**Files:**
- Create: `docs/reports/2026-04-08-triple-barrier-runtime-verdict.md`

- [ ] **Step 1: Create the final report with the required metadata and sections**

Write this file:

```md
# Triple Barrier MT4 Runtime Verdict

> **Date**: 2026-04-08 HH:MM MSK
> **Status**: Completed
> **Goal**: Проверить frozen TB rule на реальном MT4 runtime и вынести финальный verdict по пригодности TB как отдельного EA-режима
> **Related plan/spec**: `docs/superpowers/plans/2026-04-08-triple-barrier-runtime-verdict.md`, `docs/reports/2026-04-08-triple-barrier-hardening.md`
> **Related commit**: pending

## Context

Коротко опиши, что hardening уже завершён и offline baseline зафиксирован.

## What Was Done

- Укажи путь к использованному TB tester log
- Укажи команды reconciliation
- Укажи созданные CSV artefacts
- Укажи, потребовались ли изменения в tracer или нет

## Changed Files

- `ML/reports/tb_mt4_reconciliation.csv` (создан)
- `ML/reports/tb_mt4_reconciliation_losses.csv` (создан)
- `docs/reports/2026-04-08-triple-barrier-runtime-verdict.md` (создан)

## Verification

Вставь точные команды, которые реально выполнялись.

## Results

Обязательно включи:
- offline test baseline: `PF=4.31`, `Trades=141`, `Wins/Losses/Timeouts=103/38/10`
- runtime MT4 metrics
- `pf_vs_offline_ratio`
- `trade_count_gap`
- counters по `mt4_result`
- counters по `category`
- mean absolute deltas

## Conclusions

Выбери ровно один verdict:
- `candidate survives runtime check`
- `do not promote TB mode`
- `promising but unresolved`

Сразу после verdict объясни 2-4 предложениями, почему именно он.

## Limitations / Open Questions

- Что осталось непроверенным
- Какие искажения всё ещё возможны
- Что мешает считать verdict окончательным, если он не окончательный

## Next Step

Если verdict positive:
- предложи следующий узкий шаг для EA prototype / limited forward test

Если verdict negative:
- предложи закрыть TB track и не инвестировать дальше

Если verdict mixed:
- предложи один конкретный недостающий runtime experiment

## Related Materials

- `docs/reports/2026-04-08-triple-barrier-hardening.md`
- `ML/reports/evaluate_test_tb.md`
- `ML/reports/tb_selected_rule.json`
- `ML/reports/tb_mt4_reconciliation.csv`
- `ML/reports/tb_mt4_reconciliation_losses.csv`
```

Expected:
- Report exists and contains all 9 required sections

- [ ] **Step 2: Re-read the report and remove soft claims**

Run:

```bash
sed -n '1,260p' docs/reports/2026-04-08-triple-barrier-runtime-verdict.md
```

Expected:
- No phrases like `probably`, `seems`, `should be fine`
- Verdict language is explicit and evidence-backed


### Task 6: Sync Project History If The Runtime Verdict Is Final

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Read: `docs/reports/README.md`

- [ ] **Step 1: Update the changelog with a short runtime-verdict entry**

Run:

```bash
sed -n '1,120p' CHANGELOG.md
sed -n '1,200p' docs/reports/README.md
```

Then add one new top entry with:
- runtime log present
- final verdict
- one-line link to `docs/reports/2026-04-08-triple-barrier-runtime-verdict.md`

Expected:
- `CHANGELOG.md` gains one concise stage-closing entry

- [ ] **Step 2: Update handoff so the next chat does not reopen the same uncertainty**

Update:

```md
## Current Stage
[Replace with final runtime verdict and exact status]

## Last Completed Stage
Triple Barrier MT4 Runtime Verdict (2026-04-08).

## Next Step
[Either advance TB, close TB, or request one missing runtime experiment]
```

Expected:
- `CONTEXT_HANDOFF.md` reflects the final runtime state, not the pre-verdict blocker

- [ ] **Step 3: Run one final proof pass before claiming the stage is closed**

Run:

```bash
./.venv/bin/python -m pytest tests/test_signal_tracer_tb.py -q
git status --short
```

Expected:
- `tests/test_signal_tracer_tb.py` still passes
- Working tree shows only the files you intentionally changed

---

## Self-Review Checklist

- The plan does **not** retune the model, recalibrate probabilities, or change `theta/min_ev` without new evidence.
- The plan stops immediately if there is no fresh TB tester log.
- The final report compares MT4 against the exact frozen offline baseline (`PF=4.31`, `N=141`).
- The verdict is explicitly one of:
  - `candidate survives runtime check`
  - `do not promote TB mode`
  - `promising but unresolved`
- `CHANGELOG.md` and `CONTEXT_HANDOFF.md` are updated only after the runtime verdict is real, not assumed.
