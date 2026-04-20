# lib_PIC Feature Training Track Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить новый bounded training track, где производные признаки `lib_PIC` используются внутри модели для задачи `take_skip_trailing_stop_v2`, а не только как внешний фильтр.

**Architecture:** Новый track не ломает общий `ML.train`: добавляется отдельный runner с собственным dual-stream transformer. Sequence branch читает стандартный фрактальный тензор `(N, seq_len, 20)`, feature branch читает профиль `lib_PIC` (`baseline_clean`, `baseline_clean_path`, `baseline_clean_geometry_path`), выход модели — multi-label вероятности `take_skip_v2`.

**Tech Stack:** Python 3, pandas, NumPy, PyTorch, pytest, существующие `ML/data_loader.py`, `ML/lib_pic_feature_profiles.py`, `ML/take_skip_trailing_stop_v2_task.py`, `ML/benchmark_take_skip_trailing_stop_v2.py`.

---

## Files

- Create: `ML/models/take_skip_dual_stream_transformer.py`
- Create: `ML/run_take_skip_lib_pic_feature_matrix.py`
- Create: `tests/test_take_skip_lib_pic_feature_matrix.py`
- Modify: `ML/README.md`
- Modify: `MODULE_INDEX.md`
- Later, after real run: add report under `docs/reports/`

## Task 1: Dual-stream take/skip model

- [x] **Step 1: Write failing model test**

Test file: `tests/test_take_skip_lib_pic_feature_matrix.py`

Expected behavior:
- model accepts `x`, `engineered`, `mask`;
- output shape is `(batch, 15)`;
- output is raw logits, not probabilities.

- [x] **Step 2: Run red test**

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_lib_pic_feature_matrix.py::test_take_skip_dual_stream_model_outputs_logits -q
```

Expected: fails with missing module/model.

- [x] **Step 3: Implement model**

Create `ML/models/take_skip_dual_stream_transformer.py`.

Use the same sequence encoder pattern as `EntryPathDualStreamTransformer`, but a single head:

- sequence encoder: transformer + CLS token;
- feature encoder: LayerNorm + MLP;
- fusion: concatenate sequence and engineered outputs;
- head: `Linear(..., 15)`.

- [x] **Step 4: Run green test**

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_lib_pic_feature_matrix.py::test_take_skip_dual_stream_model_outputs_logits -q
```

Expected: pass.

## Task 2: Dataset builder for sequence + lib_PIC features

- [x] **Step 1: Write failing dataset test**

Test behavior:
- small DataFrame with `fractal0..fractal4`, `ATR`, target pnl columns builds tensors;
- sequence is truncated to requested `seq_len`;
- engineered feature width matches selected profile;
- labels shape is `(rows, 15)`.

- [x] **Step 2: Run red test**

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_lib_pic_feature_matrix.py::test_build_feature_dataset_uses_profile_and_targets -q
```

Expected: fails with missing function.

- [x] **Step 3: Implement dataset helpers**

In `ML/run_take_skip_lib_pic_feature_matrix.py`:

- `TakeSkipFeatureDataset`;
- `build_take_skip_feature_arrays(frame, feature_profile, seq_len)`;
- use `parse_fractals_to_3d`;
- use `build_lib_pic_feature_profile`;
- use `split_take_skip_v2_targets`.

- [x] **Step 4: Run green test**

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_lib_pic_feature_matrix.py::test_build_feature_dataset_uses_profile_and_targets -q
```

Expected: pass.

## Task 3: Training/evaluation smoke path

- [x] **Step 1: Write failing smoke test**

Test behavior:
- train one tiny epoch on synthetic frames;
- export validation/test prediction frames;
- run `ML.benchmark_take_skip_trailing_stop_v2.run_benchmark`;
- summary contains `validation_grid_path` and `final_verdict`.

- [x] **Step 2: Run red test**

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_lib_pic_feature_matrix.py::test_run_single_config_writes_summary_and_exports -q
```

Expected: fails with missing runner.

- [x] **Step 3: Implement bounded runner**

Create CLI:

```bash
MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_take_skip_lib_pic_feature_matrix \
  --output-dir ML/reports/take_skip_lib_pic_feature_matrix \
  --feature-profiles baseline_clean baseline_clean_path baseline_clean_geometry_path \
  --seq-lens 20 50 100 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6
```

Runner must:
- train each `(feature_profile, seq_len)` config;
- save checkpoint per config under run dir;
- export validation/test predictions;
- run benchmark;
- write `summary.json` per config and `manifest.json`.

- [x] **Step 4: Run green tests**

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_lib_pic_feature_matrix.py -q
```

Expected: all tests pass.

## Task 4: Documentation and handoff

- [x] Update `ML/README.md`.
- [x] Update `MODULE_INDEX.md`.
- [ ] If real training is deferred to server, write exact command in final response.
- [x] Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_lib_pic_feature_matrix.py tests/test_take_skip_trailing_stop_v2_task.py -q
```

- [ ] Commit implementation.

## Heavy Training Boundary

Local work should stop after smoke tests and code verification if full matrix is expected to be slow. Full matrix can run on the remote server after `git push` and `git pull`.
