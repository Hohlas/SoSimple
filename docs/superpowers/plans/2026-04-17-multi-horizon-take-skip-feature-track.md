# Multi-Horizon Take/Skip Feature Track Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Построить новый `take / skip` training track на полном наборе из 100 фракталов, multi-scale summaries и нескольких горизонтах `12 / 24 / 48`, чтобы проверить, снимает ли richer feature representation bottleneck предыдущих trailing-stop исследований.

**Architecture:** План не расширяет старый `take_skip_trailing_stop_v1`, а создаёт следующую версию task с новым feature representation. Labeling считает continuous trailing-stop outcomes для сетки `H × X`, task превращает их в multi-label binary targets, feature builder собирает последовательность + summaries + существующие строковые числовые признаки, а benchmark выбирает candidate только на validation и замораживает winner для test.

**Tech Stack:** Python 3, pandas, NumPy, PyTorch, pytest, существующий training stack `ML/data_loader.py`, `ML/train.py`, `ML/evaluate_test.py`, `API/generate_signals.py`.

---

## File Structure

### Read First

- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/reports/2026-04-17-take-skip-trailing-stop-matrix.md`
- `docs/superpowers/specs/2026-04-17-multi-horizon-take-skip-feature-track-design.md`
- `ML/take_skip_trailing_stop_task.py`
- `ML/benchmark_take_skip_trailing_stop.py`
- `ML/run_take_skip_trailing_stop_matrix.py`

### Files To Create

- `ML/multi_scale_fractal_features.py`
- `ML/take_skip_trailing_stop_v2_task.py`
- `ML/benchmark_take_skip_trailing_stop_v2.py`
- `ML/run_take_skip_trailing_stop_v2_matrix.py`
- `tests/test_multi_scale_fractal_features.py`
- `tests/test_take_skip_trailing_stop_v2_task.py`
- `tests/test_benchmark_take_skip_trailing_stop_v2.py`
- `tests/test_run_take_skip_trailing_stop_v2_matrix.py`
- `docs/reports/2026-04-17-multi-horizon-take-skip-feature-track-handoff.md`

### Files To Modify

- `processing/label_signals.py`
- `ML/data_loader.py`
- `ML/train.py`
- `ML/evaluate_test.py`
- `API/generate_signals.py`
- `MODULE_INDEX.md`
- `CHANGELOG.md`

### Files To Update At Stage Close

- `docs/reports/2026-04-17-multi-horizon-take-skip-feature-track-handoff.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/research/execution-tracks.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

---

## Acceptance Rules

- Первый прогон работает только на `Transformer`.
- Горизонты фиксированы: `12 / 24 / 48`.
- Сетка trailing-stop фиксирована: `X = 2 / 4 / 8`.
- Positive class фиксирован: `trail_pnl >= 0.5 ATR`.
- Search делается только на validation.
- Test используется только как frozen check.
- Новый benchmark обязан считать `PF`, `trades_per_year`, yearly stability и concentration diagnostics.
- Full matrix локально не запускается; локально только tests и smoke-run.

---

### Task 1: Add Multi-Horizon Trailing-Stop Labels

**Files:**
- Modify: `processing/label_signals.py`
- Modify: `tests/test_trailing_stop_target_labels.py`

- [ ] **Step 1: Write the failing label tests**

Add expectations for continuous outcome columns:

```python
expected = [
    'trail_12_pnl_atr_x2',
    'trail_12_pnl_atr_x4',
    'trail_12_pnl_atr_x8',
    'trail_24_pnl_atr_x2',
    'trail_24_pnl_atr_x4',
    'trail_24_pnl_atr_x8',
    'trail_48_pnl_atr_x2',
    'trail_48_pnl_atr_x4',
    'trail_48_pnl_atr_x8',
]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_trailing_stop_target_labels.py -q
```

Expected: FAIL because only old horizon/grid columns exist.

- [ ] **Step 3: Implement multi-horizon label generation**

In `processing/label_signals.py`:

- introduce fixed horizon grid:

```python
TRAILING_STOP_HORIZONS = (12, 24, 48)
TRAILING_STOP_ATR_MULTIPLIERS_V2 = (2, 4, 8)
```

- compute continuous labels for each `(horizon, x_value)` pair:

```python
for horizon in TRAILING_STOP_HORIZONS:
    horizon_bars = bars[:horizon]
    for x_value in TRAILING_STOP_ATR_MULTIPLIERS_V2:
        out.at[row_label, f'trail_{horizon}_pnl_atr_x{x_value}'] = simulate_trailing_stop_exit(
            bars=horizon_bars,
            direction=direction,
            entry_price=entry_price,
            atr=atr,
            trail_atr=float(x_value),
        )
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_trailing_stop_target_labels.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add processing/label_signals.py tests/test_trailing_stop_target_labels.py
git commit -m "labels: add multi-horizon trailing-stop outcomes"
```

---

### Task 2: Build Multi-Scale Fractal Feature Builder

**Files:**
- Create: `ML/multi_scale_fractal_features.py`
- Create: `tests/test_multi_scale_fractal_features.py`

- [ ] **Step 1: Write failing tests for summaries**

Create tests that assert:

- output exists for windows `5 / 10 / 20 / 50 / 100`;
- feature frame row count matches input row count;
- missing/short sequences do not break shape contract;
- all generated values are finite.

Use a minimal contract like:

```python
summary = build_multi_scale_fractal_features(
    fractal_tensor=np.ones((2, 100, 20), dtype=np.float32),
    windows=(5, 10, 20, 50, 100),
)
assert summary.shape[0] == 2
assert summary.shape[1] > 0
assert np.isfinite(summary).all()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_multi_scale_fractal_features.py -q
```

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement the feature builder**

In `ML/multi_scale_fractal_features.py` implement:

- `MULTI_SCALE_WINDOWS = (5, 10, 20, 50, 100)`
- `build_multi_scale_fractal_features(fractal_tensor, windows=MULTI_SCALE_WINDOWS)`

The builder should compute compact summaries per window. First version should stay simple and robust:

- mean level
- standard deviation
- last-minus-mean
- linear slope proxy `(last - first) / window`
- range `(max - min)`

Keep implementation deterministic and finite-safe.

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_multi_scale_fractal_features.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/multi_scale_fractal_features.py tests/test_multi_scale_fractal_features.py
git commit -m "ml: add multi-scale fractal features"
```

---

### Task 3: Define V2 Take/Skip Task Contract

**Files:**
- Create: `ML/take_skip_trailing_stop_v2_task.py`
- Create: `tests/test_take_skip_trailing_stop_v2_task.py`

- [ ] **Step 1: Write failing task contract tests**

Test exact target columns:

```python
expected = [
    'take_12_x2', 'take_12_x4', 'take_12_x8',
    'take_24_x2', 'take_24_x4', 'take_24_x8',
    'take_48_x2', 'take_48_x4', 'take_48_x8',
]
```

Also test:

- thresholding at `>= 0.5`;
- export-frame contract;
- finite metric checks;
- shape validation.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_trailing_stop_v2_task.py -q
```

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement the task module**

Add:

- `TAKE_SKIP_TRAILING_STOP_V2_TARGET`
- target/source column lists for full `H × X` grid
- `split_take_skip_v2_targets(frame)`
- `build_take_skip_v2_export_frame(...)`
- `compute_take_skip_v2_metrics(...)`

Metrics contract:

- average BCE
- per-column positive rate
- per-column brier score
- validation for finite probabilities and binary labels

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_trailing_stop_v2_task.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/take_skip_trailing_stop_v2_task.py tests/test_take_skip_trailing_stop_v2_task.py
git commit -m "ml: add multi-horizon take-skip task"
```

---

### Task 4: Wire V2 Task Into Data Loader And Training

**Files:**
- Modify: `ML/data_loader.py`
- Modify: `ML/train.py`
- Modify: `ML/evaluate_test.py`
- Modify: `API/generate_signals.py`
- Test: `tests/test_take_skip_trailing_stop_v2_task.py`

- [ ] **Step 1: Extend tests for stack registration**

Add assertions that:

- new task constant is registered in `ML/data_loader.py`
- loader returns correct multi-label shape `(n, 9)`
- evaluation can export validation/test predictions for the new task

- [ ] **Step 2: Run targeted tests and verify failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_trailing_stop_v2_task.py -q
```

Expected: FAIL because the stack does not know the new task.

- [ ] **Step 3: Implement stack wiring**

In `ML/data_loader.py`:

- register `take_skip_trailing_stop_v2`
- load full 100-fractal sequence for this task
- append multi-scale summaries to engineered numeric features
- keep existing row-level numeric features where compatible

In `ML/train.py`:

- add parser choice for new task
- use `BCEWithLogitsLoss`
- set initial best metric for BCE-based validation

In `ML/evaluate_test.py` and `API/generate_signals.py`:

- export `pred_take_*`, `true_take_*`, `true_trail_*`
- preserve validation/test CSV contract for benchmark

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_multi_scale_fractal_features.py \
  tests/test_take_skip_trailing_stop_v2_task.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/data_loader.py ML/train.py ML/evaluate_test.py API/generate_signals.py \
  tests/test_take_skip_trailing_stop_v2_task.py
git commit -m "ml: wire multi-horizon take-skip v2 stack"
```

---

### Task 5: Implement Validation-First V2 Benchmark

**Files:**
- Create: `ML/benchmark_take_skip_trailing_stop_v2.py`
- Create: `tests/test_benchmark_take_skip_trailing_stop_v2.py`

- [ ] **Step 1: Write failing benchmark tests**

Cover:

- both candidate families exist
- yearly coverage uses full split span
- validation winner is frozen to test
- malformed dates fail fast
- metrics include `PF`, `trades_per_year`, `negative_year_slices`, `profit_concentration_top_10`, `ulcer_index_atr`, `max_drawdown_atr`
- success gate is `PF > 1`, `trades_per_year >= 6`, no obvious yearly collapse

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_take_skip_trailing_stop_v2.py -q
```

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement the benchmark**

Reuse the hardened structure from `ML/benchmark_take_skip_trailing_stop.py`, but operate on multi-horizon columns.

Write:

- `validation_grid.csv`
- `final_verdict.json`

Candidate families:

- `prob_ge_threshold`
- `top_k_probability`

Threshold grids:

```python
DEFAULT_THRESHOLDS = (0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95)
DEFAULT_TOP_K = (0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10)
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_take_skip_trailing_stop_v2.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/benchmark_take_skip_trailing_stop_v2.py tests/test_benchmark_take_skip_trailing_stop_v2.py
git commit -m "ml: add multi-horizon take-skip benchmark"
```

---

### Task 6: Add Matrix Runner And Smoke Handoff

**Files:**
- Create: `ML/run_take_skip_trailing_stop_v2_matrix.py`
- Create: `tests/test_run_take_skip_trailing_stop_v2_matrix.py`
- Create: `docs/reports/2026-04-17-multi-horizon-take-skip-feature-track-handoff.md`
- Modify: `MODULE_INDEX.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Write failing runner tests**

Cover:

- config slug generation
- summary writing
- manifest writing
- fail when checkpoint is missing
- runner calls benchmark with generated validation/test CSV paths

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_run_take_skip_trailing_stop_v2_matrix.py -q
```

Expected: FAIL because runner does not exist.

- [ ] **Step 3: Implement the runner**

Support:

```bash
python -m ML.run_take_skip_trailing_stop_v2_matrix \
  --output-dir ML/reports/take_skip_trailing_stop_v2_matrix \
  --seq-lens 20 50 100 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6
```

Runner responsibilities:

- train one run per `seq_len`
- export validation/test predictions
- invoke benchmark
- write per-run `summary.json`
- write top-level `manifest.json`

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_run_take_skip_trailing_stop_v2_matrix.py -q
```

Expected: PASS.

- [ ] **Step 5: Run local verification**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_multi_scale_fractal_features.py \
  tests/test_take_skip_trailing_stop_v2_task.py \
  tests/test_benchmark_take_skip_trailing_stop_v2.py \
  tests/test_run_take_skip_trailing_stop_v2_matrix.py -q
```

Expected: PASS.

- [ ] **Step 6: Run smoke**

Run:

```bash
MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_take_skip_trailing_stop_v2_matrix \
  --output-dir ML/reports/take_skip_trailing_stop_v2_matrix_smoke \
  --seq-lens 20 \
  --epochs 1 \
  --patience 1 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6
```

Expected: end-to-end completion with `manifest.json` and per-run benchmark outputs.

- [ ] **Step 7: Update docs**

Update:

- `docs/reports/2026-04-17-multi-horizon-take-skip-feature-track-handoff.md`
- `MODULE_INDEX.md`
- `CHANGELOG.md`

The handoff report must include:

- local verification commands and outcomes
- exact remote training command
- explicit note that server-side `DATA/` must already contain the new multi-horizon trailing-stop columns

- [ ] **Step 8: Commit**

```bash
git add ML/run_take_skip_trailing_stop_v2_matrix.py \
  tests/test_run_take_skip_trailing_stop_v2_matrix.py \
  docs/reports/2026-04-17-multi-horizon-take-skip-feature-track-handoff.md \
  MODULE_INDEX.md CHANGELOG.md
git commit -m "ml: add multi-horizon take-skip matrix runner"
```

---

### Task 7: Close The Stage After Remote Matrix Run

**Files:**
- Modify: `docs/reports/2026-04-17-multi-horizon-take-skip-feature-track-handoff.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/execution-tracks.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

- [ ] **Step 1: Pull remote results**

Required artifacts:

- `ML/reports/take_skip_trailing_stop_v2_matrix/manifest.json`
- per-run `summary.json`
- per-run `benchmark/final_verdict.json`
- per-run `benchmark/validation_grid.csv`

- [ ] **Step 2: Write final report**

Summarize:

- best candidate per `seq_len`
- best horizon / trailing-stop pair
- whether any candidate crossed `PF > 1`
- whether probability thresholds remained dead or revived
- whether richer features changed the picture relative to v1

- [ ] **Step 3: Sync changelog, handoff, wiki**

Use stage-closing workflow:

- canonical report in `docs/reports/`
- short changelog entry
- new current state in `CONTEXT_HANDOFF.md`
- ingest into `wiki/`

- [ ] **Step 4: Commit**

```bash
git add docs/reports CHANGELOG.md CONTEXT_HANDOFF.md wiki
git commit -m "reports: record multi-horizon take-skip feature-track verdict"
```

---

Plan complete and saved to `docs/superpowers/plans/2026-04-17-multi-horizon-take-skip-feature-track.md`. Ready to execute?
