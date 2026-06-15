# Stage 4 Remaining Hypotheses Master Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking. Do not commit unless the user explicitly asks.

**Goal:** Выполнить оставшиеся гипотезы из `docs/audit/to_do.md` после Stage 4.4 и подготовить решение: переходить к Stage 5.0 Transformer, проверять новую механику выхода или закрывать ветку.

**Architecture:** Это master-план: он задаёт порядок выполнения трёх уже подготовленных под-планов, критерии остановки и правила синхронизации отчётов. Каждый под-план создаёт отдельный runner/report и остаётся `DIAGNOSTIC_ONLY`, пока не появится отдельный clean candidate-cycle.

**Tech Stack:** Python 3.10+, pandas, numpy, XGBoost/scikit-learn, pytest, project wiki. Использовать `~/git/SoSimple/.venv/bin/python`.

---

## Source Of Truth

- `docs/audit/to_do.md` — список оставшихся гипотез.
- `docs/audit/next.md` — текущий порядок исследований после Stage 4.3/4.4.
- `docs/reports/2026-06-15-stage4_4-micro-check.md` — текущий baseline.
- `wiki/research/fractal-stop-research.md` — синтез Fractal Stop Stage 1-4.4.
- `docs/methodology/09-validation-freeze.md` — `val-select` / `val-eval`.
- `docs/methodology/11-robustness.md` — robustness, calendar feature risk, permutation.
- `docs/methodology/12-backtest-costs.md` — симулятор, spread/costs, exit mechanics.
- `docs/methodology/A5-post-mortem-diagnostics.md` — `DIAGNOSTIC_ONLY` post-mortem.

## Global Hard Boundaries

- Не открывать test.
- Не делать `git commit` / `git push`.
- Не объявлять winner по diagnostic-результатам.
- Не расширять search budget после просмотра результатов.
- Не смешивать улучшение модели, улучшение фильтра и улучшение механики выхода в один вывод.
- Если baseline Stage 4.4 не воспроизводится, остановиться и сначала объяснить расхождение.

## Execution Order

Выполнять в таком порядке:

1. **Stage 5.0-prep diagnostics** — модельный вопрос: на чём держится breach-сигнал и какой прирост AUC/lift нужен для PF-gate.
2. **Stage 4.5 exit mechanics** — отдельный вопрос: может ли trailing/breakeven/partial exit улучшить механику выхода при фиксированных моделях.
3. **Stage 4.6 clean candidate-cycle** — выполнять только если Stage 4.3/4.4/4.5 дают конкретную diagnostic-зону или policy-family, которую стоит честно проверить через `val-select` / `val-eval`.

---

### Task 1: Execute Stage 5.0-Prep Diagnostics

**Files / Plan:**
- Execute: `docs/superpowers/plans/2026-06-15-stage5_prep-diagnostics.md`

- [ ] **Step 1: Read the sub-plan completely**
  - Confirm it covers both `breach feature ablation` and `AUC→PF sensitivity`.

- [ ] **Step 2: Implement exactly the fixed diagnostic budget**
  - Do not add extra feature profiles after seeing results.
  - Do not open test.
  - Keep status `DIAGNOSTIC_ONLY`.

- [ ] **Step 3: Verify required outputs**
  - `ML/reports/stage5_prep_diagnostics.json`
  - `docs/reports/2026-06-15-stage5-prep-diagnostics.md`
  - `docs/ML/diagnose_stage5_prep.py.md`
  - tests passing
  - wiki updated and verified

- [ ] **Step 4: Interpret only for Stage 5 design**
  - If time/calendar dominates, Stage 5.0 must include calendar baseline and timezone-shift controls.
  - If fractal groups carry meaningful signal, Stage 5.0 Transformer remains justified.
  - If AUC→PF sensitivity requires unrealistic improvement, prioritize exit mechanics before a full Transformer trading layer.

**Stop condition after Task 1:** If feature ablation shows breach signal is mostly calendar and AUC→PF sensitivity requires implausibly high uplift, pause and report before starting Transformer work.

---

### Task 2: Execute Stage 4.5 Exit Mechanics

**Files / Plan:**
- Execute: `docs/superpowers/plans/2026-06-15-stage4_5-trailing-partial-exit.md`

- [ ] **Step 1: Read the sub-plan completely**
  - Confirm synthetic simulator tests are first.
  - Confirm old trailing PF=1.655 is not reused as evidence.

- [ ] **Step 2: Implement simulator tests before historical evaluation**
  - TP-only, SL-only, ambiguous bar, timeout, breakeven, trailing, partial exit.
  - If any synthetic test fails, do not run historical diagnostics.

- [ ] **Step 3: Run fixed policy budget only**
  - Do not add new trailing offsets or partial-exit variants after seeing results.
  - Keep results `DIAGNOSTIC_ONLY`.

- [ ] **Step 4: Verify required outputs**
  - `ML/reports/stage4_5_exit_mechanics.json`
  - `docs/reports/2026-06-15-stage4_5-exit-mechanics.md`
  - `docs/ML/diagnose_stage4_5_exit_mechanics.py.md`
  - tests passing
  - wiki updated and verified

- [ ] **Step 5: Interpret separately from model quality**
  - If exit policy improves PF but breach/fav predictions are unchanged, write: improvement is exit-mechanics effect, not model improvement.
  - If improvement fails under spread stress, reject or keep as diagnostic only.

**Stop condition after Task 2:** If no exit policy beats fixed TP R=0.7 on PF, BS_p05, yearly robustness and spread stress, do not run Stage 4.6 for exit policies.

---

### Task 3: Decide Whether Stage 4.6 Is Warranted

**Inputs:**
- Stage 4.3 report.
- Stage 4.4 report.
- Stage 5.0-prep report.
- Stage 4.5 report, if executed.

- [ ] **Step 1: Identify candidate families**
  - Candidate family may include only zones/policies already found before Stage 4.6.
  - Do not invent new thresholds here.

- [ ] **Step 2: Check whether any family deserves clean validation**
  - Minimum condition: diagnostic PF > baseline, meaningful BS_p05 improvement, enough trades/year, no single-year concentration.

- [ ] **Step 3: If no family qualifies**
  - Write a short note in the final report: Stage 4.6 skipped because no diagnostic family warranted clean candidate-cycle.
  - Proceed to Stage 5.0 planning or close Stage 4.x.

- [ ] **Step 4: If a family qualifies**
  - Execute Task 4.

---

### Task 4: Execute Stage 4.6 Clean Candidate Cycle

**Files / Plan:**
- Execute: `docs/superpowers/plans/2026-06-15-stage4_6-clean-candidate-cycle.md`

- [ ] **Step 1: Read the sub-plan completely**
  - Confirm candidate family is fixed before running.
  - Confirm `val-select` and `val-eval` are separate.

- [ ] **Step 2: Execute selection protocol**
  - Select only on `val-select`.
  - Evaluate selected rule only once on `val-eval`.
  - Do not change rule after seeing `val-eval`.

- [ ] **Step 3: Run permutation with repeated selection**
  - Each permutation must repeat the same selection process.
  - A permutation of only the already selected rule is insufficient for multiple-testing correction.

- [ ] **Step 4: Verify required outputs**
  - `ML/reports/stage4_6_clean_cycle.json`
  - `docs/reports/2026-06-15-stage4_6-clean-candidate-cycle.md`
  - `docs/ML/benchmark_stage4_6_clean_cycle.py.md`
  - tests passing
  - wiki updated and verified

**Stop condition after Task 4:** If val-eval fails, reject the candidate family. Do not expand the grid.

---

### Task 5: Final Synthesis

**Files:**
- Modify: `docs/audit/to_do.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify only if user asks to close stage: `CHANGELOG.md`, `CONTEXT_HANDOFF.md`

- [ ] **Step 1: Update `docs/audit/to_do.md`**
  - Mark completed hypotheses `[x]` only after their reports exist and verification passed.
  - If a hypothesis was skipped by stop condition, leave unchecked and add reason.

- [ ] **Step 2: Update wiki synthesis**
  - Add concise results from completed reports.
  - Keep raw metrics in `docs/reports/`; wiki should summarize.

- [ ] **Step 3: Decide next branch**
  - If Stage 5.0-prep supports sequence modeling: next plan is Stage 5.0 Transformer.
  - If exit mechanics dominate: next plan is clean candidate-cycle for exit policy.
  - If both fail: close Fractal Stop current formulation or redesign target/exit.

- [ ] **Step 4: Verification**
  - Run all new tests.
  - Run all new runners or document why a stop condition skipped them.
  - Run `git diff --check`.
  - Run `~/git/SoSimple/.venv/bin/python wiki/wiki.py generate`.
  - Run `~/git/SoSimple/.venv/bin/python wiki/wiki.py verify`.
  - Run `knowledge-rag reindex_documents(force=True)`.

## Acceptance Criteria

- Every open hypothesis in `docs/audit/to_do.md` is either completed with a report or explicitly skipped by a documented stop condition.
- No test split is opened.
- No diagnostic result is promoted to winner.
- Search budgets are disclosed in every report.
- `docs/audit/to_do.md`, wiki and module docs are synchronized.
- Final synthesis gives a concrete next action: Stage 5.0 Transformer, clean exit-policy cycle, or close/redesign.
