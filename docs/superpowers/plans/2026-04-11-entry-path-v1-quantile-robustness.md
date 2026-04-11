# Entry Path v1 Quantile Robustness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, устойчив ли `entry_path_v1_quantile` как реальный апгрейд над frozen baseline `entry_path_v1` (`A @ 7.5%`) на нескольких `seed`, годовых срезах и rolling/forward-проверках, и только после этого принимать решение о MT4 parity-check.

**Architecture:** Базовая модель, quantile-layer и frozen baseline rule уже существуют; этот этап не должен искать новые heads, лоссы или правила. Работа делится на две части: сначала сделать repeatable multi-run контур без перезаписи артефактов, затем добавить robustness-анализатор, который агрегирует `validation/test/sequential/yearly/rolling` итоги по фиксированному набору `seed` и выпускает один go/no-go verdict для следующего MT4-этапа.

**Tech Stack:** Python 3.11, pandas, numpy, pytest, JSON, markdown reports, existing `ML.train`, `ML.evaluate_test`, `ML.export_entry_path_v1_quantile_predictions`, `ML.benchmark_entry_path_v1_quantile_filter`

---

## File Map

### Read First
- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/reports/2026-04-10-entry-path-v1-quantile.md`
- `docs/reports/2026-04-09-entry-path-trade-filter.md`
- `wiki/research/execution-tracks.md`
- `ML/reports/entry_path_v1_quantile_filter_selected_rule.json`
- `ML/reports/entry_path_trade_filter_selected_rule.json`

### Existing Files To Reuse
- `ML/train.py`
- `ML/evaluate_test.py`
- `ML/export_entry_path_v1_quantile_predictions.py`
- `ML/benchmark_entry_path_v1_quantile_filter.py`
- `ML/entry_path_v1_quantile_task.py`
- `tests/test_entry_path_v1_quantile_training.py`
- `tests/test_entry_path_v1_quantile_reports.py`
- `tests/test_entry_path_v1_quantile_filter.py`

### Files To Create
- `ML/entry_path_v1_quantile_robustness.py`
- `ML/benchmark_entry_path_v1_quantile_robustness.py`
- `tests/test_entry_path_v1_quantile_robustness.py`
- `ML/reports/entry_path_v1_quantile_robustness/summary.json`
- `ML/reports/entry_path_v1_quantile_robustness/runs.csv`
- `ML/reports/entry_path_v1_quantile_robustness/yearly.csv`
- `ML/reports/entry_path_v1_quantile_robustness/rolling.csv`
- `docs/reports/2026-04-11-entry-path-v1-quantile-robustness.md`

### Files To Modify
- `ML/train.py`
- `ML/evaluate_test.py`

### Fixed Baselines For This Stage
- Frozen quantile validation winner: `lb_gt_m`
- Frozen quantile reference: validation `25 trades / PF=11.0465`, test `24 trades / PF=inf`, sequential `11 trades / PF=inf`
- Frozen baseline rule: `A @ 7.5%`
- Frozen baseline reference: test `44 trades / PF=4.29`, sequential `30 trades / PF=2.87`
- Fixed TB-style hold for sequential check: `24` bars
- Fixed seed set for robustness pass: `7, 17, 42, 77, 123`

---

### Task 1: Make Quantile Runs Non-Destructive And Seed-Scoped

**Files:**
- Modify: `ML/train.py`
- Modify: `ML/evaluate_test.py`
- Test: `tests/test_entry_path_v1_quantile_training.py`
- Test: `tests/test_entry_path_v1_quantile_reports.py`

- [ ] **Step 1: Write failing tests for seed-scoped artifact paths**

Add tests that verify:
- `ML.train --task entry_path_v1_quantile` can write checkpoint/result JSON into an explicit run directory without overwriting the default files.
- `ML.evaluate_test --task entry_path_v1_quantile` can write report and exported test predictions into an explicit output directory.

Use this concrete shape in tests:

```python
checkpoint_dir = tmp_path / "seed_042" / "checkpoints"
report_dir = tmp_path / "seed_042" / "reports"
```

Expected file names:
- `transformer_entry_path_v1_quantile_best.pt`
- `transformer_entry_path_v1_quantile_result.json`
- `evaluate_test_entry_path_v1_quantile.md`
- `entry_path_v1_quantile_test_predictions.csv`

- [ ] **Step 2: Run the narrow test slice and verify it fails**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_entry_path_v1_quantile_training.py \
  tests/test_entry_path_v1_quantile_reports.py -q
```

Expected:
- Fails because `train.py` and `evaluate_test.py` do not yet expose explicit artifact directories for this task.

- [ ] **Step 3: Add explicit artifact path controls**

Implement:
- In `ML/train.py`, add CLI args:
  - `--checkpoint-dir`
  - `--result-dir`
- In `ML/evaluate_test.py`, add CLI arg:
  - `--output-dir`

Rules:
- Default behavior must stay byte-for-byte compatible with current single-run workflow.
- New args are optional.
- `entry_path_v1_quantile` must use the supplied directories when present; other tasks may keep existing defaults.

- [ ] **Step 4: Re-run the same tests and verify they pass**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_entry_path_v1_quantile_training.py \
  tests/test_entry_path_v1_quantile_reports.py -q
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add ML/train.py ML/evaluate_test.py \
  tests/test_entry_path_v1_quantile_training.py \
  tests/test_entry_path_v1_quantile_reports.py
git commit -m "feat: isolate quantile artifacts per run"
```

---

### Task 2: Build Robustness Aggregation Helpers

**Files:**
- Create: `ML/entry_path_v1_quantile_robustness.py`
- Create: `tests/test_entry_path_v1_quantile_robustness.py`

- [ ] **Step 1: Write failing tests for run aggregation, yearly slices, rolling windows and verdict logic**

Cover these behaviors:
- `load_seed_run()` reads one seed directory and returns normalized metrics from:
  - checkpoint result JSON
  - quantile selected rule JSON
  - exported test predictions CSV
- `build_yearly_summary()` computes year-level `trades`, `pf`, `win_rate`, `mean_pnl_atr` using the frozen selected rule for that seed.
- `build_rolling_summary()` computes fixed forward windows on `test` with no rule re-fit.
- `summarize_seed_matrix()` aggregates medians/minima across seeds.
- `build_verdict()` returns `go_mt4`, `needs_more_research`, or `reject_quantile_upgrade`.

Use a toy fixture with two seeds and explicit timestamps spanning at least two years.

- [ ] **Step 2: Run the new test file and verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_path_v1_quantile_robustness.py -q
```

Expected:
- FAIL with missing robustness module/functions.

- [ ] **Step 3: Implement the robustness helper module**

Implement the following responsibilities in `ML/entry_path_v1_quantile_robustness.py`:
- canonical seed directory loader
- safe PF helper that preserves `inf`
- yearly slice builder from exported predictions
- rolling-window evaluator with fixed `hold_bars=24`
- aggregation table builder across seeds
- explicit verdict builder against the current baseline

Use this seed directory layout:

```text
ML/reports/entry_path_v1_quantile_robustness/seed_007/
ML/reports/entry_path_v1_quantile_robustness/seed_017/
ML/reports/entry_path_v1_quantile_robustness/seed_042/
ML/reports/entry_path_v1_quantile_robustness/seed_077/
ML/reports/entry_path_v1_quantile_robustness/seed_123/
```

The module must emit three tables:
- per-seed run summary
- yearly summary
- rolling summary

And one JSON verdict with at least these keys:

```json
{
  "seed_count": 5,
  "same_rule_count": 0,
  "median_test_pf": 0.0,
  "median_sequential_pf": 0.0,
  "worst_seed_test_trades": 0,
  "negative_year_slices": 0,
  "verdict": "needs_more_research"
}
```

- [ ] **Step 4: Re-run the robustness tests and verify they pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_path_v1_quantile_robustness.py -q
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add ML/entry_path_v1_quantile_robustness.py \
  tests/test_entry_path_v1_quantile_robustness.py
git commit -m "feat: add quantile robustness aggregation helpers"
```

---

### Task 3: Add A CLI To Aggregate The Full Robustness Pass

**Files:**
- Create: `ML/benchmark_entry_path_v1_quantile_robustness.py`
- Modify: `tests/test_entry_path_v1_quantile_robustness.py`

- [ ] **Step 1: Extend the test file with a CLI smoke test**

Add a test that prepares two seed directories under `tmp_path`, runs the CLI, and verifies it writes:
- `runs.csv`
- `yearly.csv`
- `rolling.csv`
- `summary.json`

- [ ] **Step 2: Run the robustness tests again and verify the new case fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_path_v1_quantile_robustness.py -q
```

Expected:
- FAIL because the CLI wrapper does not exist yet.

- [ ] **Step 3: Implement the CLI wrapper**

`ML/benchmark_entry_path_v1_quantile_robustness.py` must:
- accept `--root-dir`
- accept `--seeds 7 17 42 77 123`
- accept `--baseline-rule ML/reports/entry_path_trade_filter_selected_rule.json`
- accept `--output-dir`
- read all seed directories
- emit the four aggregated artifacts
- print one short console verdict line

Expected verdict protocol for this stage:
- `go_mt4` only if all conditions hold:
  - at least `4/5` seeds keep the same validation winner rule family
  - median test `PF > 4.29`
  - median sequential `PF >= 2.87`
  - worst-seed test trades `>= 15`
  - no yearly slice with `trades >= 5` has negative net PnL
- `needs_more_research` if the result is positive but misses one gate
- `reject_quantile_upgrade` if median test PF falls below the baseline or multiple seeds collapse

- [ ] **Step 4: Re-run the test file and verify it passes**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_path_v1_quantile_robustness.py -q
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add ML/benchmark_entry_path_v1_quantile_robustness.py \
  tests/test_entry_path_v1_quantile_robustness.py
git commit -m "feat: add quantile robustness benchmark cli"
```

---

### Task 4: Execute The Fixed Five-Seed Robustness Pass

**Files:**
- Read/Write: `ML/checkpoints/entry_path_v1_quantile_robustness/seed_*/`
- Read/Write: `ML/reports/entry_path_v1_quantile_robustness/seed_*/`
- Use: `ML/reports/entry_path_trade_filter_selected_rule.json`

- [ ] **Step 1: Run the narrow regression suite before the expensive pass**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_entry_path_v1_quantile_model.py \
  tests/test_entry_path_v1_quantile_task.py \
  tests/test_entry_path_v1_quantile_training.py \
  tests/test_entry_path_v1_quantile_reports.py \
  tests/test_entry_path_v1_quantile_filter.py \
  tests/test_entry_path_v1_quantile_robustness.py -q
```

Expected:
- PASS

- [ ] **Step 2: Execute the five fixed seeds with isolated artifact directories**

Run:

```bash
for seed in 7 17 42 77 123; do
  seed_tag=$(printf "seed_%03d" "$seed")
  ckpt_dir="ML/checkpoints/entry_path_v1_quantile_robustness/${seed_tag}"
  report_dir="ML/reports/entry_path_v1_quantile_robustness/${seed_tag}"

  ./.venv/bin/python -m ML.train \
    --model transformer \
    --task entry_path_v1_quantile \
    --epochs 5 \
    --seed "$seed" \
    --clear_cache \
    --checkpoint-dir "$ckpt_dir" \
    --result-dir "$ckpt_dir"

  ./.venv/bin/python -m ML.export_entry_path_v1_quantile_predictions \
    --checkpoint "${ckpt_dir}/transformer_entry_path_v1_quantile_best.pt" \
    --output-dir "$report_dir" \
    --seed "$seed"

  ./.venv/bin/python -m ML.evaluate_test \
    --task entry_path_v1_quantile \
    --checkpoint "${ckpt_dir}/transformer_entry_path_v1_quantile_best.pt" \
    --seed "$seed" \
    --output-dir "$report_dir"

  ./.venv/bin/python -m ML.benchmark_entry_path_v1_quantile_filter \
    --validation-csv "${report_dir}/entry_path_v1_quantile_validation_predictions.csv" \
    --test-csv "${report_dir}/entry_path_v1_quantile_test_predictions.csv" \
    --baseline-rule ML/reports/entry_path_trade_filter_selected_rule.json \
    --output-dir "$report_dir"
done
```

Expected:
- Each seed directory contains checkpoint, result JSON, exported CSVs, test report and quantile selected rule JSON.
- No default top-level artifact is overwritten during the loop.

- [ ] **Step 3: Aggregate the full robustness pass**

Run:

```bash
./.venv/bin/python -m ML.benchmark_entry_path_v1_quantile_robustness \
  --root-dir ML/reports/entry_path_v1_quantile_robustness \
  --seeds 7 17 42 77 123 \
  --baseline-rule ML/reports/entry_path_trade_filter_selected_rule.json \
  --output-dir ML/reports/entry_path_v1_quantile_robustness
```

Expected:
- Writes `runs.csv`, `yearly.csv`, `rolling.csv`, `summary.json`
- Prints a one-line verdict

- [ ] **Step 4: Sanity-check the aggregated artifacts**

Run:

```bash
sed -n '1,40p' ML/reports/entry_path_v1_quantile_robustness/summary.json
sed -n '1,20p' ML/reports/entry_path_v1_quantile_robustness/runs.csv
sed -n '1,20p' ML/reports/entry_path_v1_quantile_robustness/yearly.csv
sed -n '1,20p' ML/reports/entry_path_v1_quantile_robustness/rolling.csv
```

Expected:
- Summary JSON clearly states whether the next stage is `go_mt4`, `needs_more_research`, or `reject_quantile_upgrade`.

- [ ] **Step 5: Commit**

```bash
git add ML/checkpoints/entry_path_v1_quantile_robustness \
  ML/reports/entry_path_v1_quantile_robustness
git commit -m "exp: run entry_path quantile robustness pass"
```

---

### Task 5: Write The Research Verdict And Handoff

**Files:**
- Create: `docs/reports/2026-04-11-entry-path-v1-quantile-robustness.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`

- [ ] **Step 1: Write the stage report from the aggregated artifacts only**

The report must include:
- seed table
- yearly failure/survival summary
- rolling-window summary
- exact verdict
- explicit next step

Do not add new tuning or post-hoc thresholds after seeing the outcomes.

- [ ] **Step 2: Update `CHANGELOG.md` with the stage result**

Required numbers to include:
- median and worst-seed test PF
- median and worst-seed sequential PF
- number of negative yearly slices
- final verdict

- [ ] **Step 3: Update `CONTEXT_HANDOFF.md`**

If verdict is:
- `go_mt4`: next step becomes quantile MT4 parity-check
- `needs_more_research`: next step becomes additional robustness work, not MT4 integration
- `reject_quantile_upgrade`: baseline reverts to frozen `A @ 7.5%`

- [ ] **Step 4: Run final verification**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_entry_path_v1_quantile_model.py \
  tests/test_entry_path_v1_quantile_task.py \
  tests/test_entry_path_v1_quantile_training.py \
  tests/test_entry_path_v1_quantile_reports.py \
  tests/test_entry_path_v1_quantile_filter.py \
  tests/test_entry_path_v1_quantile_robustness.py -q
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add docs/reports/2026-04-11-entry-path-v1-quantile-robustness.md \
  CHANGELOG.md CONTEXT_HANDOFF.md
git commit -m "docs: record quantile robustness verdict"
```
