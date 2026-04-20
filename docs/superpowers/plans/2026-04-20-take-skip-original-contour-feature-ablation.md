# Take/Skip Original Contour Feature Ablation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить `lib_PIC` path/geometry признаки в максимально близком к старому прибыльному `take_skip_trailing_stop_v2` training contour.

**Architecture:** Новый runner должен воспроизвести старую схему: `TransformerClassifier` получает один sequence tensor, где базовые фрактальные признаки и engineered-признаки объединены как каналы каждого шага последовательности. Сначала запускается контроль `original_baseline`; только если он воспроизводит старый результат, запускаются `original_plus_path` и `original_plus_geometry_path`.

**Tech Stack:** Python 3, pandas, NumPy, PyTorch, pytest, существующие `ML/train.py`, `ML/data_loader.py`, `ML/models/transformer.py`, `ML/lib_pic_feature_profiles.py`, `ML/take_skip_trailing_stop_v2_task.py`, `ML/benchmark_take_skip_trailing_stop_v2.py`.

---

## Context

Предыдущий этап `take_skip_lib_pic_feature_training` проверял новый `dual-stream`-контур. Он не дал рабочего результата, но это не закрывает гипотезу "добавить новые признаки к исходному прибыльному baseline".

Причина: старый прибыльный результат был получен другим способом. Старый контур добавлял engineered-признаки внутрь основного sequence tensor как повторяющиеся каналы на каждом шаге последовательности. Новый `dual-stream`-контур держал фракталы и `lib_PIC`-признаки в двух разных ветках модели. Это разные условия сравнения.

## Why Control May Not Reproduce

Контроль может не воспроизвести старый результат по техническим причинам:

- изменился код `ML/data_loader.py`, `ML/train.py`, `ML/take_skip_trailing_stop_v2_task.py`;
- старый runner `ML/run_take_skip_trailing_stop_v2_matrix.py` сейчас не является активным файлом HEAD и должен быть восстановлен аккуратно;
- текущий target contract расширен до `x10/x12`, а старый прибыльный запуск использовал доступную сетку `x2/x4/x8`;
- кэш `.npy` мог быть создан старой версией loader-а и давать другой набор входов;
- порядок, ширина и состав входных признаков могли измениться после старого этапа;
- seed одинаковый, но полная бит-в-бит повторяемость PyTorch на CPU не гарантируется, поэтому критерий должен быть "та же область результата", а не идентичные числа.

Практический критерий воспроизведения: `original_baseline_seq50` должен снова дать `go` или близкую validation-область вокруг старого winner-а: `take_24_x8`, `prob_ge_threshold` около `0.70`, не меньше `6` сделок в год, `PF > 1` на validation. Если контроль этого не делает, дальнейшее добавление признаков нельзя интерпретировать.

## Files

- Create: `ML/run_take_skip_original_contour_feature_matrix.py`
- Create: `tests/test_take_skip_original_contour_feature_matrix.py`
- Create after run: `docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md`
- Modify: `ML/README.md`
- Modify: `MODULE_INDEX.md`
- Modify after run: `CHANGELOG.md`
- Modify after run: `CONTEXT_HANDOFF.md`
- Modify after run: `wiki/index.md`
- Modify after run: `wiki/research/execution-tracks.md`
- Regenerate after run: `wiki/REPO_integrity.md`

## Feature Modes

Use three explicit modes:

- `original_baseline`: old-style baseline only.
- `original_plus_path`: old-style baseline plus selected `lib_PIC` path-reaction features.
- `original_plus_geometry_path`: old-style baseline plus selected `lib_PIC` geometry and path-reaction features.

Do not use `baseline_clean` as the baseline for this plan. The point is to test additions on top of the original feature representation, not on top of the shortened profile.

## Stop Rules

- If `original_baseline_seq50` cannot roughly reproduce the old profitable area, stop and write a diagnostic report.
- If `original_baseline_seq50` reproduces the old area, continue to feature additions.
- If `original_plus_path` improves validation but breaks frozen test, do not promote it; record as overfit risk.
- If `original_plus_geometry_path` is worse than `original_plus_path`, do not expand geometry further.

## Task 1: Reconstruct Original Feature Builder

- [ ] **Step 1: Write failing unit test for original baseline width**

Test file: `tests/test_take_skip_original_contour_feature_matrix.py`

Expected behavior:
- small DataFrame with `fractal0..fractal99`, row features, and `trail_*_pnl_atr_x*` columns is converted to `(X, y, mask)`;
- `X` is a single 3D tensor;
- engineered features are repeated across every sequence step;
- labels use only target columns whose source `trail_*` columns exist in the DataFrame.

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_original_contour_feature_matrix.py::test_original_contour_builder_repeats_engineered_channels -q
```

Expected: fail with missing module/function.

- [ ] **Step 2: Implement original feature builder**

In `ML/run_take_skip_original_contour_feature_matrix.py`, implement:

- `available_take_skip_v2_columns(frame)`;
- `build_original_baseline_features(frame, parsed_fractals)`;
- `append_repeated_channels(X, engineered)`;
- `build_original_contour_arrays(frame, feature_mode, seq_len)`.

Use the old known behavior:

- parse `fractal0..fractal99` via existing parser;
- build multi-scale fractal summaries;
- add old row-wise features when present;
- fill missing optional row-wise columns with `0.0`;
- repeat engineered features over sequence length;
- concatenate with parsed fractal tensor.

- [ ] **Step 3: Run green unit test**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_original_contour_feature_matrix.py::test_original_contour_builder_repeats_engineered_channels -q
```

Expected: pass.

## Task 2: Add Feature Modes

- [ ] **Step 1: Write failing test for feature modes**

Test behavior:

- `original_baseline` has the smallest engineered width;
- `original_plus_path` adds path columns;
- `original_plus_geometry_path` adds more columns than `original_plus_path`;
- all modes preserve the same row count, labels and mask.

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_original_contour_feature_matrix.py::test_feature_modes_expand_original_contour_without_row_drift -q
```

Expected: fail until modes are wired.

- [ ] **Step 2: Implement feature modes**

Use existing `ML/lib_pic_feature_profiles.py` only as source for additional feature columns. Do not replace the old baseline with `baseline_clean`.

Implementation rule:

- `original_baseline` = old baseline features only;
- `original_plus_path` = old baseline + path features from `baseline_clean_path` minus `baseline_clean`;
- `original_plus_geometry_path` = old baseline + all extra columns from `baseline_clean_geometry_path` minus `baseline_clean`.

- [ ] **Step 3: Run green feature-mode test**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_original_contour_feature_matrix.py::test_feature_modes_expand_original_contour_without_row_drift -q
```

Expected: pass.

## Task 3: Training Runner and Exports

- [ ] **Step 1: Write failing smoke test**

Test behavior:

- tiny synthetic train/validation/test frames can train one epoch;
- runner saves `checkpoint.pt`;
- runner exports validation/test prediction CSV;
- runner runs `benchmark_take_skip_trailing_stop_v2`;
- runner writes `summary.json`.

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_original_contour_feature_matrix.py::test_original_contour_runner_writes_summary_and_benchmark -q
```

Expected: fail with missing runner entry point.

- [ ] **Step 2: Implement bounded runner**

Implement CLI:

```bash
PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_take_skip_original_contour_feature_matrix \
  --output-dir ML/reports/take_skip_original_contour_feature_matrix \
  --feature-modes original_baseline original_plus_path original_plus_geometry_path \
  --seq-lens 50 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6 \
  --jobs auto \
  --torch-threads auto \
  --cpu-load 0.5 \
  --clear-cache
```

Runner requirements:

- train `TransformerClassifier`;
- set `input_features` from actual built tensor width;
- use `BCEWithLogitsLoss`;
- early stop on validation BCE;
- export probabilities for all available take/skip columns;
- include selected target columns in `summary.json`;
- write `manifest.json`;
- print unbuffered progress lines: `[matrix-start]`, `[matrix-complete]`, `[matrix-failed]`, `[matrix-done]`.

- [ ] **Step 3: Run smoke test**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_original_contour_feature_matrix.py -q
```

Expected: all tests pass.

## Task 4: Control Run

- [ ] **Step 1: Run local or server control for seq50 only**

Command:

```bash
PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_take_skip_original_contour_feature_matrix \
  --output-dir ML/reports/take_skip_original_contour_feature_matrix_control \
  --feature-modes original_baseline \
  --seq-lens 50 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6 \
  --jobs 1 \
  --torch-threads auto \
  --cpu-load 0.5 \
  --clear-cache \
  2>&1 | tee ML/reports/take_skip_original_contour_feature_matrix_control/run.log
```

- [ ] **Step 2: Check reproduction criteria**

Open:

- `ML/reports/take_skip_original_contour_feature_matrix_control/original_baseline_seq50/summary.json`
- `ML/reports/take_skip_original_contour_feature_matrix_control/original_baseline_seq50/benchmark/final_verdict.json`
- `ML/reports/take_skip_original_contour_feature_matrix_control/original_baseline_seq50/benchmark/validation_grid.csv`

Expected acceptable result:

- `verdict=go`, or best practical validation row with `PF > 1` and `trades_per_year >= 6`;
- ideally near old area `take_24_x8`, `prob_ge_threshold` around `0.70`;
- frozen test not catastrophically worse.

- [ ] **Step 3: Stop if control fails**

If control fails, do not run feature additions. Write a short diagnostic report covering:

- input feature width;
- target columns used;
- cache mode;
- best validation rows;
- difference from old known `seq50` result.

## Task 5: Feature Addition Matrix

- [ ] **Step 1: Run full feature comparison only after control passes**

Command:

```bash
PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_take_skip_original_contour_feature_matrix \
  --output-dir ML/reports/take_skip_original_contour_feature_matrix \
  --feature-modes original_baseline original_plus_path original_plus_geometry_path \
  --seq-lens 20 50 100 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6 \
  --jobs auto \
  --torch-threads auto \
  --cpu-load 0.5 \
  --clear-cache \
  2>&1 | tee ML/reports/take_skip_original_contour_feature_matrix/run.log
```

- [ ] **Step 2: Compare results**

Compare by validation first:

- `verdict`;
- `PF`;
- `trades_per_year`;
- `negative_year_slices`;
- `profit_concentration_top_10`;
- `ulcer_index_atr`;
- frozen test result.

Do not select a feature mode by test performance. Test is only confirmation after validation selection.

## Task 6: Documentation

- [ ] Update `ML/README.md`.
- [ ] Update `MODULE_INDEX.md`.
- [ ] Add `docs/ML/run_take_skip_original_contour_feature_matrix.py.md`.
- [ ] Add report `docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md`.
- [ ] Update `CHANGELOG.md`.
- [ ] Update `CONTEXT_HANDOFF.md`.
- [ ] Run wiki ingest for the new report and update `wiki/research/execution-tracks.md`.
- [ ] Regenerate `wiki/REPO_integrity.md`.

## Task 7: Verification and Commit

- [ ] Run focused tests:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_take_skip_original_contour_feature_matrix.py \
  tests/test_take_skip_trailing_stop_v2_task.py \
  tests/test_take_skip_lib_pic_feature_matrix.py \
  -q
```

- [ ] Run repository status check:

```bash
git status --short
```

- [ ] Commit implementation and documentation:

```bash
git add \
  ML/run_take_skip_original_contour_feature_matrix.py \
  tests/test_take_skip_original_contour_feature_matrix.py \
  docs/ML/run_take_skip_original_contour_feature_matrix.py.md \
  ML/README.md \
  MODULE_INDEX.md \
  docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md \
  CHANGELOG.md \
  CONTEXT_HANDOFF.md \
  wiki/index.md \
  wiki/research/execution-tracks.md \
  wiki/REPO_integrity.md
git commit -m "ml: compare lib pic features on original take skip contour"
```

## Heavy Training Boundary

Full matrix can run on the remote server. Before server handoff:

- commit code and docs needed for execution;
- push only after explicit user approval;
- on server, remove stale untracked generated reports before switching branches;
- verify `DATA/Nero_train_labeled.csv`, `DATA/Nero_validation_labeled.csv`, `DATA/Nero_test_labeled.csv` contain the required `trail_*_pnl_atr_x*` columns.
