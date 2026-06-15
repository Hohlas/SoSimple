# Stage 4.5 Trailing And Partial Exit Mechanics Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking. Do not commit unless the user explicitly asks.

**Goal:** Проверить trailing stop, breakeven и partial exit как отдельную execution-механику для Fractal Stop, не смешивая её с качеством модели.

**Architecture:** Новый diagnostic runner берёт фиксированные Stage 4.4 предсказания и сравнивает несколько заранее заданных exit-policy на одном и том же universe сделок. Перед использованием на исторических данных симулятор выходов покрывается синтетическими тестами.

**Tech Stack:** Python 3.10+, pandas, numpy, pytest. Использовать `~/git/SoSimple/.venv/bin/python`.

---

## Source Of Truth

- `docs/audit/to_do.md` — пункт `Отдельный план: trailing / partial exit mechanics`.
- `docs/reports/2026-06-15-stage4_4-micro-check.md` — fixed TP R=0.7 как текущий простой baseline выхода.
- `docs/reports/2026-06-14-stage4-deep-diagnostics.md` — старый diagnostic trailing atr_02 PF=1.655, не считать доказательством.
- `docs/methodology/12-backtest-costs.md` — обязательные проверки симулятора и издержек.
- `docs/methodology/09-validation-freeze.md` — запрет на скрытый выбор winner.

## Hard Boundaries

- Не открывать test.
- Не выбирать production winner.
- Не смешивать улучшение exit-механики с улучшением модели.
- Не менять breach/fav модели.
- Не использовать старый PF=1.655 как доказательство.
- Все результаты до clean cycle имеют статус `DIAGNOSTIC_ONLY`.

## Files

| File | Action | Purpose |
|---|---|---|
| `ML/baseline/diagnose_stage4_5_exit_mechanics.py` | Create | Exit-mechanics diagnostic runner |
| `tests/test_stage4_5_exit_mechanics.py` | Create | Synthetic tests for exit simulator |
| `ML/reports/stage4_5_exit_mechanics.json` | Generate | Structured results |
| `docs/reports/2026-06-15-stage4_5-exit-mechanics.md` | Create | Canonical report |
| `docs/ML/diagnose_stage4_5_exit_mechanics.py.md` | Create | Module docs |
| `MODULE_INDEX.md` | Modify | Add module |
| `docs/audit/to_do.md` | Modify | Add plan link; mark item complete only after execution |
| `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md` | Modify after report | Wiki ingest |

---

### Task 1: Synthetic Exit Simulator Tests

**Files:**
- Create: `tests/test_stage4_5_exit_mechanics.py`
- Create: `ML/baseline/diagnose_stage4_5_exit_mechanics.py`

- [ ] **Step 1: Write tests before implementation**
  - TP-only path closes at TP with positive PnL.
  - SL-only path closes at SL with negative PnL.
  - TP and SL in the same H1 bar follows explicit ambiguous convention.
  - Timeout path closes at timeout price.
  - Breakeven moves stop only after trigger.
  - Trailing stop moves only in favorable direction.
  - Partial exit books partial PnL and leaves remaining size.

- [ ] **Step 2: Implement minimal simulator helpers**
  - Keep OHLC=Bid convention from Stage 4.4.
  - Explicitly document BUY/SELL spread handling.
  - Include `exit_policy`, `close_reason`, `pnl_val`, `pnl_r`, `ambiguous`.

- [ ] **Step 3: Run tests**
  - Command: `~/git/SoSimple/.venv/bin/python -m pytest tests/test_stage4_5_exit_mechanics.py -q`.
  - Expected: all tests pass.

---

### Task 2: Fixed Baseline Reproduction

**Files:**
- Modify: `ML/baseline/diagnose_stage4_5_exit_mechanics.py`

- [ ] **Step 1: Reuse Stage 4.4 models and universe**
  - Same split.
  - Same target `sell_H6_off05`.
  - Same predictions.
  - Same canonical spread `0.20`.

- [ ] **Step 2: Reproduce baseline policies**
  - Baseline fav TP: PF=1.015, n=503.
  - Fixed TP R=0.7: PF=1.038, n=503.
  - Stop if reproduction fails.

---

### Task 3: Predefined Exit Policy Set

**Files:**
- Modify: `ML/baseline/diagnose_stage4_5_exit_mechanics.py`

- [ ] **Step 1: Define small policy budget**
  - `fixed_r_0_7`: control baseline.
  - `breakeven_0_3`: move stop to entry after 30% of TP.
  - `trail_atr_0_2`: trailing stop with 0.2 ATR offset.
  - `trail_atr_0_3`: trailing stop with 0.3 ATR offset.
  - `partial_50_at_0_5R_then_trail_0_2`: close 50% at 0.5R, trail rest.

- [ ] **Step 2: No extra sweep**
  - Do not add new trailing offsets after seeing results.
  - Record search budget.

- [ ] **Step 3: Simulate each policy**
  - Same entry set as fixed TP R=0.7 unless explicitly documented.
  - Compute PF, BS_p05, yearly PF, trades/year, TP/SL/TIMEOUT/trailing exits.
  - Compute spread stress: `0.20`, `0.40`.

---

### Task 4: Robustness And Negative Controls

**Files:**
- Modify: `ML/baseline/diagnose_stage4_5_exit_mechanics.py`

- [ ] **Step 1: Block bootstrap**
  - block size 15, 500 iterations.

- [ ] **Step 2: Permutation test**
  - Shuffle breach probabilities and repeat the same fixed entry+exit policy.
  - If policy selection is treated as a family, report permutation as diagnostic only.

- [ ] **Step 3: Year and concentration checks**
  - Negative years.
  - One-year gross-profit share.
  - Trade count per year.

---

### Task 5: Report And Interpretation

**Files:**
- Generate: `ML/reports/stage4_5_exit_mechanics.json`
- Create: `docs/reports/2026-06-15-stage4_5-exit-mechanics.md`

- [ ] **Step 1: JSON schema**
  - `status`, `config`, `search_budget`, `baseline_reproduction`, `exit_policies`, `stress_spread`, `interpretation_guards`.

- [ ] **Step 2: Report sections**
  - Context.
  - Simulator tests.
  - Methodology and split.
  - Search budget.
  - Policy comparison.
  - Cost stress.
  - What can and cannot be concluded.

- [ ] **Step 3: Non-conclusions**
  - No test opened.
  - No production winner.
  - Old trailing PF=1.655 is not reused as evidence.
  - Any attractive policy requires clean candidate-cycle before test.

---

### Task 6: Docs, Wiki, And Verification

**Files:**
- Create: `docs/ML/diagnose_stage4_5_exit_mechanics.py.md`
- Modify: `MODULE_INDEX.md`
- Modify after report: `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`

- [ ] **Step 1: Module docs**
  - Inputs, outputs, command, status, limitations.

- [ ] **Step 2: Index**
  - Add module to `MODULE_INDEX.md`.

- [ ] **Step 3: Wiki ingest**
  - Update Fractal Stop wiki with Stage 4.5 results.
  - Run `wiki/wiki.py generate` and `wiki/wiki.py verify`.

- [ ] **Step 4: Verification**
  - Run tests.
  - Run diagnostic.
  - Validate JSON.
  - Run `git diff --check`.

## Acceptance Criteria

- Synthetic simulator tests pass.
- Baseline fixed TP R=0.7 reproduces Stage 4.4.
- Policy search budget is fixed and disclosed.
- Cost stress is reported.
- No test opened and no winner selected.
- Report clearly decides whether trailing/partial exit deserves a clean candidate-cycle.
