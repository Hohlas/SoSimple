# Stage 5.0a Transform Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a no-training diagnostic comparison of current, asinh, and piecewise-tail feature transforms for Stage 5.0a feature distribution audit.

**Architecture:** Extend the existing `--feature-preflight-only` runner to reuse the same parsed features, profiles, normalization, distribution audit, coverage audit, and per-position audit. The comparison writes separate CSV/JSON artifacts and does not train or select a model.

**Tech Stack:** Python 3.10, pandas, numpy, scikit-learn `StandardScaler`, pytest.

## Global Constraints

- Use `./.venv/bin/python`.
- Do not run Transformer training.
- Fit transform thresholds only on `train`; use `val_stop` and `holdout` only for disclosure.
- Preserve raw `ATR` as denominator for `price_coord_atr`; row `ATR` transform is separate.
- Do not commit; project commit flow is handled by `stage-reporting` only when closing an этап.

---

### Task 1: Transform Policy

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `TRANSFORM_VARIANTS`, `_asinh_transform(x)`, `_fit_piecewise_tail_params(values, lower_q, upper_q)`, `_apply_piecewise_tail_transform(x, params)`.
- Consumes: existing `_signed_log1p`, `build_row_features`, `build_profile_features_from_parsed`.

- [x] Add tests for `asinh` preserving zero/sign and compressing tails.
- [x] Add tests for piecewise-tail preserving the middle interval and compressing both tails.
- [x] Implement transform helpers.
- [x] Run targeted transform tests.

### Task 2: Preflight Comparison Runner

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `run_transform_comparison(train_df, val_stop_df, holdout_df) -> dict`.
- Writes: `ML/reports/stage5_0a_transform_comparison.json`, `ML/reports/stage5_0a_transform_comparison_summary.csv`, `ML/reports/stage5_0a_transform_comparison_stats.csv`, `ML/reports/stage5_0a_transform_comparison_per_position.csv`.

- [x] Add tests that comparison includes `current`, `asinh`, `piecewise_tail`.
- [x] Add tests that `piecewise_tail` params are fit on train only.
- [x] Implement comparison loop for the 7 rerun candidate profiles.
- [x] Add `--transform-comparison-only` CLI flag that runs no training.
- [x] Run targeted comparison tests.

### Task 3: Documentation And Verification

**Files:**
- Modify: `docs/ML/benchmark_stage5_transformer_breach.py.md`

**Interfaces:**
- Documents command: `./.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --transform-comparison-only`.

- [x] Document Russian name: "проверка распределения признаков".
- [x] Document artifacts and no-training status.
- [x] Run `./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -q`.
- [x] Run transform comparison command.
