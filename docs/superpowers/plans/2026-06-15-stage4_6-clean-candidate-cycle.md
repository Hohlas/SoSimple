# Stage 4.6 Clean Candidate Cycle Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking. Do not commit unless the user explicitly asks.

**Goal:** Проверить найденные в Stage 4.3/4.4 diagnostic-зоны в чистом `val-select` / `val-eval` протоколе, не открывая test.

**Architecture:** Новый runner делит validation на два непересекающихся периода: `val-select` для выбора одного правила из заранее заданного малого набора и `val-eval` для оценки выбранного правила. Permutation test должен повторять тот же процесс выбора, иначе результат остаётся diagnostic only.

**Tech Stack:** Python 3.10+, pandas, numpy, scikit-learn/XGBoost. Использовать `~/git/SoSimple/.venv/bin/python`.

---

## Source Of Truth

- `docs/audit/to_do.md` — пункт `чистый candidate-cycle для найденной Stage 4.3 зоны`.
- `docs/reports/2026-06-15-stage4_3-diagnostics.md` — diagnostic зона `pred_fav/stop_val ∈ [1.0, 1.3)`.
- `docs/reports/2026-06-15-stage4_4-micro-check.md` — fixed TP R=0.7 и fav-filter выводы.
- `docs/methodology/09-validation-freeze.md` — `val-select` / `val-eval`, множественное тестирование.
- `docs/methodology/A5-post-mortem-diagnostics.md` — diagnostic zones are not winners.

## Hard Boundaries

- Не открывать test.
- Не использовать весь validation одновременно для выбора и оценки.
- Не расширять search budget после просмотра `val-select`.
- Не объявлять PASS без `val-eval` и bootstrap/permutation.
- Не менять модели в этом плане; используется Stage 4.4 model stack.

## Split Proposal

Validation уже использовался исторически, поэтому весь Stage 4.6 остаётся research/diagnostic до будущего test/frozen cycle. Для чистого внутреннего протокола:

- train: `<=2016`;
- val_stop: `2017-2018`;
- val_select: `2019-2020`;
- val_eval: `2021-2022`.

Если годовые границы отличаются в данных, runner должен вывести фактические даты и остановиться при пустом периоде.

## Files

| File | Action | Purpose |
|---|---|---|
| `ML/baseline/benchmark_stage4_6_clean_cycle.py` | Create | Clean val-select/val-eval runner |
| `tests/test_stage4_6_clean_cycle.py` | Create | Selection protocol smoke tests |
| `ML/reports/stage4_6_clean_cycle.json` | Generate | Structured results |
| `docs/reports/2026-06-15-stage4_6-clean-candidate-cycle.md` | Create | Canonical report |
| `docs/ML/benchmark_stage4_6_clean_cycle.py.md` | Create | Module docs |
| `MODULE_INDEX.md` | Modify | Add module |
| `docs/audit/to_do.md` | Modify | Add plan link; mark item complete only after execution |
| `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md` | Modify after report | Wiki ingest |

---

### Task 1: Selection Protocol Tests

**Files:**
- Create: `tests/test_stage4_6_clean_cycle.py`
- Create: `ML/baseline/benchmark_stage4_6_clean_cycle.py`

- [ ] **Step 1: Write tests**
  - `select_rule()` selects only from candidates passing minimum trades/year.
  - Tie-breaker uses `BS_p05`, not raw PF.
  - `val_eval` metrics are computed after selection and cannot change selected rule.
  - permutation selection repeats the same `select_rule()` function.

- [ ] **Step 2: Implement minimal helpers**
  - `CandidateRule` data object.
  - `select_rule(results, gates)`.
  - `evaluate_rule(rule, split)`.

- [ ] **Step 3: Run tests**
  - `~/git/SoSimple/.venv/bin/python -m pytest tests/test_stage4_6_clean_cycle.py -q`.

---

### Task 2: Candidate Family Definition

**Files:**
- Modify: `ML/baseline/benchmark_stage4_6_clean_cycle.py`

- [ ] **Step 1: Predefine small search budget**
  - `baseline_fav_tp`: Stage 4.4 baseline.
  - `fixed_r_0_7`: Stage 4.4 best simple TP.
  - `fav_ratio_band_1_0_1_3`: Stage 4.3 diagnostic zone.
  - `fixed_r_0_7_plus_fav_ratio_band_1_0_1_3`.

- [ ] **Step 2: Explicitly reject expansion**
  - Do not add more R values.
  - Do not add more fav-ratio bands.
  - Do not add trailing here.

- [ ] **Step 3: Define gates**
  - minimum trades/year >= 30 on `val_select`;
  - BS_p05 not null;
  - no single year >60% gross profit;
  - tie-breaker: highest BS_p05, then PF.

---

### Task 3: Run Val-Select

**Files:**
- Modify: `ML/baseline/benchmark_stage4_6_clean_cycle.py`

- [ ] **Step 1: Reproduce model stack**
  - Same Stage 4.4 training protocol.
  - Same target `sell_H6_off05`.

- [ ] **Step 2: Evaluate all candidates on val_select**
  - PF, BS_p05, yearly PF, trades/year, gross profit concentration.

- [ ] **Step 3: Select one rule**
  - If no rule passes gates, report `NO_CANDIDATE` and stop before val_eval interpretation.

---

### Task 4: Run Val-Eval And Permutation Selection

**Files:**
- Modify: `ML/baseline/benchmark_stage4_6_clean_cycle.py`

- [ ] **Step 1: Evaluate selected rule on val_eval**
  - No parameter changes after selection.
  - Report PF, BS_p05, yearly PF, trade count.

- [ ] **Step 2: Permutation test with repeated selection**
  - For each permutation, shuffle breach probabilities.
  - Re-evaluate all candidate rules on val_select.
  - Re-run `select_rule()`.
  - Evaluate selected permuted rule on val_eval.
  - Report conservative p-value.

- [ ] **Step 3: Interpretation**
  - If selected rule fails val_eval gate, reject candidate family.
  - If selected rule passes, mark as `RESEARCH_CANDIDATE`, not frozen test candidate.

---

### Task 5: Report, Docs, Wiki

**Files:**
- Generate: `ML/reports/stage4_6_clean_cycle.json`
- Create: `docs/reports/2026-06-15-stage4_6-clean-candidate-cycle.md`
- Create: `docs/ML/benchmark_stage4_6_clean_cycle.py.md`
- Modify: `MODULE_INDEX.md`, wiki files

- [ ] **Step 1: JSON**
  - `status`, `split`, `search_budget`, `val_select_results`, `selected_rule`, `val_eval_result`, `permutation_selection`, `interpretation_guards`.

- [ ] **Step 2: Report**
  - Context.
  - Search budget.
  - Val-select results.
  - Selected rule.
  - Val-eval result.
  - What can and cannot be concluded.

- [ ] **Step 3: Docs and wiki**
  - Module docs.
  - MODULE_INDEX.
  - Fractal Stop wiki ingest.
  - `wiki.py generate` and `wiki.py verify`.

- [ ] **Step 4: Verification**
  - Tests.
  - Runner.
  - JSON validation.
  - `git diff --check`.

## Acceptance Criteria

- `val-select` and `val-eval` are separate.
- Candidate family is fixed before running.
- Selection is repeated inside permutation test.
- No test opened.
- If no rule passes, the result is an explicit reject, not an invitation to expand the grid.
