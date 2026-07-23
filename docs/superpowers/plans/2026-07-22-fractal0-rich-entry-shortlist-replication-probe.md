# Fractal0 Rich Entry Shortlist Replication Probe Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить заранее зафиксированный shortlist Fractal0 rich-entry кандидатов на закрытом периоде без нового подбора.

**Architecture:** План отделяет поисковый этап от проверочного: shortlist пришёл из `val_select`/`val_eval`, а `locked_test` используется один раз как проверка уже заданного протокола. Runner должен переиспользовать существующий `ML/baseline/benchmark_fractal0_entry_quality_filter.py` и не добавлять новые профили, модели, targets, фильтры или пороги после просмотра результата.

**Tech Stack:** Python через `./.venv/bin/python`, pandas CSV с `sep=";"`, существующие артефакты `ML/reports/fractal0_rich_entry_quality_*`, отчёт в `docs/reports/`.

## Global Constraints

- Статус до запуска `locked_test`: `RESEARCH_HINT_RICH_FEATURES`.
- `locked_test` открывается ровно один раз для этого frozen shortlist из 11 кандидатов.
- Запрещено менять candidate list, feature profiles, model ids, target ids, filters, spread, fill policy, PnL convention, execution OHLC path и same-bar ordering после просмотра `locked_test`.
- Запрещено выбирать нового winner по `locked_test`; результат может только подтвердить, понизить или отклонить заранее заданный shortlist.
- Если код/контракт исполнения меняется перед запуском, нужно заново проверить `val_eval` тем же frozen shortlist и обновить этот план до открытия `locked_test`.
- `locked_test` не является forward-test; при PASS статус не выше `candidate`.
- Источник shortlist: `docs/reports/2026-07-21-fractal0-rich-entry-quality.md` и `ML/reports/fractal0_rich_entry_quality_summary.csv`.

---

## Frozen Inputs

Base contour for every candidate:

```text
stop_policy_id = S2_fractal0_buffer_0_5_entry_floor_2
entry_id = E3_open_pullback_1_0atr
mask_id = M0_no_mask
exit_id = X2_ml_opposite_any_p0_50
spread = 0.2
primary_ohlc_path = DATA/XAUUSD_H1_OHLC.csv
execution_ohlc_path = MT/MQL4/Files/XAUUSD_M5_OHLC.csv
```

`primary_ohlc_path` задаёт основную H1-историю сигналов и сделок. `execution_ohlc_path` не меняет рабочий таймфрейм на M5; он нужен только для уточнения порядка TP/SL внутри той же H1-свечи, когда по H1 невозможно понять, что случилось раньше.

Frozen shortlist:

| id | profile | model | target | filter |
|---:|---|---|---|---|
| 1 | `planned_geometry_only` | `extra_trees_shallow` | `target_entry_avoid_sl` | `top30` |
| 2 | `movement_plus_time` | `linear` | `target_entry_ev_regression` | `top50` |
| 3 | `planned_geometry_only` | `extra_trees_shallow` | `target_entry_avoid_sl` | `top40` |
| 4 | `movement_plus_time` | `linear` | `target_entry_good_0_5r` | `top40` |
| 5 | `movement_plus_time` | `linear` | `target_entry_good_0_5r` | `top30` |
| 6 | `structure_nearest_k40` | `hist_gradient_boosting` | `target_entry_good_0_5r` | `top30` |
| 7 | `relative_geometry_k40` | `hist_gradient_boosting` | `target_entry_good_0_5r` | `top30` |
| 8 | `movement_plus_time` | `extra_trees_shallow` | `target_entry_good_0_5r` | `top40` |
| 9 | `structure_nearest_k40` | `linear` | `target_entry_good_0_5r` | `top30` |
| 10 | `relative_geometry_k40` | `linear` | `target_entry_good_0_5r` | `top30` |
| 11 | `planned_geometry_only` | `linear` | `target_entry_good_0_5r` | `top30` |

Rationale: список включает все 11 non-time candidates из отчёта, которые на `val_eval` прошли минимум `n_trades >= 300`, `PF > 2.7873`, `BS_p05 > 2.5085` и `mean_pnl_r > 0`. Это уменьшает произвольность по сравнению с ручным top-5 и сохраняет запрет на новый подбор после открытия `locked_test`.

Frozen validation reference:

| id | val_eval_n | val_eval_PF | val_eval_BS_p05 | val_eval_mean | val_eval_DD |
|---:|---:|---:|---:|---:|---:|
| 1 | 532 | 3.2069 | 2.6519 | 0.3577 | 5.3952 |
| 2 | 1332 | 3.2690 | 2.7998 | 0.3173 | 5.6900 |
| 3 | 828 | 3.0329 | 2.5265 | 0.3178 | 6.6663 |
| 4 | 997 | 3.2496 | 2.7501 | 0.2970 | 5.6621 |
| 5 | 785 | 3.5465 | 3.0671 | 0.3126 | 4.3695 |
| 6 | 658 | 3.4858 | 2.9337 | 0.3599 | 6.5776 |
| 7 | 658 | 3.4858 | 2.9337 | 0.3599 | 6.5776 |
| 8 | 916 | 3.3393 | 2.8512 | 0.3616 | 3.8051 |
| 9 | 643 | 3.3038 | 2.8030 | 0.3552 | 3.7064 |
| 10 | 643 | 3.3038 | 2.8030 | 0.3552 | 3.7064 |
| 11 | 549 | 3.3574 | 2.7743 | 0.3325 | 3.9482 |

This table is not a locked-test target and not a pass threshold. It records the validation evidence that justified freezing the shortlist before opening `locked_test`.

Baseline to beat on `locked_test`:

```text
Primary baseline: same S2/E3/M0/X2 no-mask contour on locked_test.
Secondary baseline: S0/E3/M0/X0_fixed_r_0_7 on locked_test.
```

If locked-test baseline rows are not produced by the runner, the run status is `UNKNOWN`, not PASS.

The concrete values `locked_test_S2_E3_M0_X2_no_mask_PF` and `locked_test_S2_E3_M0_X2_no_mask_BS_p05` are intentionally unknown before the locked run. They must be computed on the same locked-test period and execution contract as the candidates. These values are comparators for added value over the unfiltered contour, not the only quality threshold. Using the known `val_eval` baseline values here would leak validation expectations into the final gate.

## PASS / FAIL Gates

Candidate-level PASS on `locked_test` requires all of:

- `n_trades >= 300`.
- `PF >= 2.0`.
- `PF > locked_test_S2_E3_M0_X2_no_mask_PF`.
- `BS_p05 > locked_test_S2_E3_M0_X2_no_mask_BS_p05`.
- `mean_pnl_r > 0`.
- `max_drawdown_r <= 8.5`.
- No negative calendar year if the candidate has at least two locked-test years.
- BUY and SELL both have `n >= 30`; each side has `mean_pnl_r > 0`.
- Result is not entirely concentrated in one year: report `effective_profit_years`; if it fails methodology gate, status becomes `RESEARCH_ONLY_WARNING` unless PF without best year is below `1.0`, then candidate FAIL.

Shortlist-level PASS requires:

- At least 3 of 11 candidates pass candidate-level gates.
- At least 2 distinct feature families pass among `planned_geometry_only`, `movement_plus_time`, `structure_nearest_k40`, `relative_geometry_k40`.
- No candidate is promoted if no-mask baseline is not computed on the same locked-test period and execution contract.

Shortlist-level FAIL:

- 0, 1 or 2 candidates pass.
- All passing candidates belong to one feature family only.
- Any post-locked-test change is needed to make the result acceptable.

## Required Outputs

Use output prefix:

```text
ML/reports/fractal0_rich_entry_shortlist_locked_probe
```

Required artifacts:

- `ML/reports/fractal0_rich_entry_shortlist_locked_probe.json`
- `ML/reports/fractal0_rich_entry_shortlist_locked_probe_summary.csv`
- `ML/reports/fractal0_rich_entry_shortlist_locked_probe_trades.csv`
- `ML/reports/fractal0_rich_entry_shortlist_locked_probe_split_manifest.csv`
- `ML/reports/fractal0_rich_entry_shortlist_locked_probe_yearly.csv`
- `ML/reports/fractal0_rich_entry_shortlist_locked_probe_side.csv`
- `docs/reports/2026-07-22-fractal0-rich-entry-shortlist-locked-probe.md`

## Task 1: Freeze Verification

**Files:**
- Read: `docs/reports/2026-07-21-fractal0-rich-entry-quality.md`
- Read: `ML/reports/fractal0_rich_entry_quality_summary.csv`
- Read: `ML/reports/fractal0_rich_entry_quality.json`
- Modify only if missing metadata: `docs/superpowers/plans/2026-07-22-fractal0-rich-entry-shortlist-replication-probe.md`

**Interfaces:**
- Consumes: current rich-entry report and summary CSV.
- Produces: explicit go/no-go note before any locked-test run.

- [ ] **Step 1: Verify frozen shortlist rows exist**

Run:

```bash
./.venv/bin/python - <<'PY'
import pandas as pd

summary = pd.read_csv("ML/reports/fractal0_rich_entry_quality_summary.csv", sep=";")
shortlist = [
    ("planned_geometry_only", "extra_trees_shallow", "target_entry_avoid_sl", "top30"),
    ("movement_plus_time", "linear", "target_entry_ev_regression", "top50"),
    ("planned_geometry_only", "extra_trees_shallow", "target_entry_avoid_sl", "top40"),
    ("movement_plus_time", "linear", "target_entry_good_0_5r", "top40"),
    ("movement_plus_time", "linear", "target_entry_good_0_5r", "top30"),
    ("structure_nearest_k40", "hist_gradient_boosting", "target_entry_good_0_5r", "top30"),
    ("relative_geometry_k40", "hist_gradient_boosting", "target_entry_good_0_5r", "top30"),
    ("movement_plus_time", "extra_trees_shallow", "target_entry_good_0_5r", "top40"),
    ("structure_nearest_k40", "linear", "target_entry_good_0_5r", "top30"),
    ("relative_geometry_k40", "linear", "target_entry_good_0_5r", "top30"),
    ("planned_geometry_only", "linear", "target_entry_good_0_5r", "top30"),
]
missing = []
for profile, model, target, filter_id in shortlist:
    rows = summary[
        summary["profile_id"].eq(profile)
        & summary["model_id"].eq(model)
        & summary["target_id"].eq(target)
        & summary["filter_id"].eq(filter_id)
        & summary["split"].eq("val_eval")
    ]
    if len(rows) != 1:
        missing.append((profile, model, target, filter_id, len(rows)))
print({"missing": missing, "checked": len(shortlist)})
raise SystemExit(1 if missing else 0)
PY
```

Expected: `{'missing': [], 'checked': 11}` and exit code `0`.

- [ ] **Step 2: Verify locked_test is still unopened**

Run:

```bash
./.venv/bin/python - <<'PY'
import json

with open("ML/reports/fractal0_rich_entry_quality.json", "r", encoding="utf-8") as f:
    data = json.load(f)
print({"locked_test": data.get("locked_test")})
raise SystemExit(0 if data.get("locked_test") == "not_opened" else 1)
PY
```

Expected: `{'locked_test': 'not_opened'}` and exit code `0`.

## Task 2: Locked-Test Runner Scope

**Files:**
- Modify only if needed: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Test if modified: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Consumes: frozen shortlist from this plan.
- Produces: a run mode that evaluates only the frozen shortlist on `locked_test`, plus same-period baselines.

- [ ] **Step 1: Check whether existing runner supports locked-test shortlist without code changes**

Run:

```bash
./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py --help
```

Expected: help text shows options sufficient to select `locked_test`, restrict profiles/models/targets/filters, and keep baselines. If not, implement the minimum CLI extension.

- [ ] **Step 2: If CLI extension is required, add tests first**

Test intent:

```python
def test_locked_probe_restricts_to_frozen_shortlist():
    """Runner must reject accidental extra configs in locked-test probe mode."""
```

Required assertion: generated job list contains exactly the eleven frozen tuples from this plan and no other tuple.

- [ ] **Step 3: Run focused tests if Python code changed**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py -q
```

Expected: all tests pass.

## Task 3: One-Time Locked-Test Execution

**Files:**
- Create: `ML/reports/fractal0_rich_entry_shortlist_locked_probe.*`

**Interfaces:**
- Consumes: frozen shortlist and locked-test split.
- Produces: locked-test metrics for each candidate and baselines.

- [ ] **Step 1: Run locked-test probe once**

Run the final command only after Task 1 and Task 2 pass. The exact command must include the frozen shortlist restriction. If the runner needs a new CLI flag, use the implemented flag name from Task 2.

Expected command shape:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --rich-entry-quality \
  --locked-test-probe \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_rich_entry_shortlist_locked_probe \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id S2_fractal0_buffer_0_5_entry_floor_2
```

Expected: process exits with code `0`, JSON says `locked_test=open_once_for_frozen_shortlist`, and output contains exactly eleven candidate rows plus required baselines.

- [ ] **Step 2: Do not rerun after seeing result**

Allowed rerun only if the first run crashes before producing locked-test metrics. If metrics are written, any rerun must be reported as protocol violation and the result status becomes `INVALID_FOR_LOCKED_TEST`.

## Task 4: Report Locked-Test Result

**Files:**
- Create: `docs/reports/2026-07-22-fractal0-rich-entry-shortlist-locked-probe.md`
- Modify: `docs/reports/2026-07-21-fractal0-rich-entry-quality.md` only to link the new report.
- Modify if stage closed: `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `wiki/index.md`, `wiki/log.md`

**Interfaces:**
- Consumes: locked-test probe artifacts.
- Produces: final report with verdict `reject`, `research_only`, or `candidate`.

- [ ] **Step 1: Report required tables**

The report must include:

- frozen shortlist table;
- locked-test baseline table;
- candidate locked-test aggregate table;
- yearly table per passing candidate;
- BUY/SELL table per passing candidate;
- explicit PASS/FAIL gate table;
- statement that no post-test tuning was performed.

- [ ] **Step 2: Assign verdict**

Use:

```text
candidate: shortlist-level PASS and no protocol violation.
research_only: aggregate promising, but yearly/side/concentration gate warns.
reject: shortlist-level FAIL.
INVALID_FOR_LOCKED_TEST: any post-result rerun or rule change.
```

- [ ] **Step 3: Run documentation checks**

Run:

```bash
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

Expected: wiki status reports no gaps.

## Self-Review

- Spec coverage: plan fixes shortlist, baselines, locked-test use, PASS/FAIL gates, one-time execution rule, and reporting.
- Placeholder scan: no `TBD`, no unspecified candidate set, no undefined PASS criteria.
- Methodology status before execution: `UNKNOWN` until Task 1 verifies frozen inputs; `locked_test` remains unopened.
