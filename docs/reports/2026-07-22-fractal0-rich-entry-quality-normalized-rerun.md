# Fractal0 Rich Entry Quality Normalized Rerun

> **Дата**: 2026-07-22
> **Статус**: Completed
> **Вердикт**: research_only
> **Result note**: RESEARCH_HINT_RICH_FEATURES
> **Цель**: Перезапустить Fractal0 rich entry-quality search с исправленным feature contract: price-like inputs переводятся в ATR-координаты, затем финальные входы модели приводятся train-only scaler-ом к диапазону `0..1`.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`

## Context

Предыдущий corrected rich-entry run от 2026-07-21 прошёл feature-contract gates после исправления потери `fractal0..fractal99`, но оставил методический риск масштаба: часть rich-признаков использовала raw price-like значения или price deltas. Это мешало честно сравнить `time_only` с фрактальной геометрией, потому что модель могла видеть абсолютный ценовой режим, а не только структуру уровней.

Этот этап сохраняет тот же контур:

```text
S2_fractal0_buffer_0_5_entry_floor_2 /
E3_open_pullback_1_0atr /
M0_no_mask /
X2_ml_opposite_any_p0_50
```

Уровень этапа: поисковый research cycle. Это не freeze, не candidate и не permission to open `locked_test`.

Research-first disclosure:

```text
lifecycle_status: research_hint
origin_bias: broad validation search after stop-grid and entry-quality predecessors
research_priority: verify normalized feature contract and compare against old rich run
current_search_budget: 243 ranked configs
cumulative_search_budget: includes parent stop-grid, narrow entry-quality and old rich-entry search
next_probe_freeze: not created in this stage
allowed_max_verdict: RESEARCH_HINT_RICH_FEATURES
forbidden_interpretations: candidate, tradable, live_ready, production, permission_to_open_locked_test
```

`RESEARCH_HINT_RICH_FEATURES` is the runner artifact label for this research hint. The canonical methodology verdict is `research_only`.

## What Was Done

В `ML/baseline/benchmark_fractal0_entry_quality_filter.py` добавлен режим:

```bash
--normalized-rich-features
```

Ключевые изменения:

- добавлен отдельный normalized-rich feature path, не перезаписывающий старый rich mode;
- добавлены explicit allowlists для normalized profiles;
- запрещены raw price-like inputs: `fractal*_price`, `h1_open/high/low/close`, raw `body/range/distance/delta` без `_atr` или `_unit`;
- price-like поля переводятся в ATR-координаты до unit scaling;
- scaler fit выполняется только на `train_core`;
- `val_select` и `val_eval` используют сохранённые train_core scaler bounds;
- missing indicators создаются как фиксированная часть схемы, а не split-dependent columns;
- padded fractal token fields остаются `0.0`, имеют `fractalN_present=0.0` и исключаются из scaler fit;
- добавлены diagnostic-only profiles: `atr_only`, `time_plus_atr`, `planned_geometry_no_atr`;
- добавлены artifacts: normalization config, normalized feature audit, token coverage, Up/Dn usage/provenance gate, protocol comparison, diagnostic best table и artifact auto-check.

Во время проверки был найден дефект реализации normalized gate: `structure_f0_only` проверял старые поля `fractal0_price` / `fractal0_direction`, которых в normalized mode уже нет. Добавлен regression test, gate переведён на `fractal0_price_to_planned_limit_atr` и `fractal0_direction_unit`; `_missing` indicators исключены из structural gate denominator.

Также после полного rerun обнаружено, что Task 5 comparison artifacts не были записаны. Добавлен тест `compare_rich_runs_protocol`, реализованы `*_protocol_comparison.csv` и `*_diagnostic_best_val_eval_by_profile.csv`, файлы созданы из уже готовых summary без повторного обучения.

Audit follow-up on 2026-07-23:

- `structure_nearest_k20` token coverage was corrected from 40 to 20 tokens; model metrics did not change because model columns were already limited by the k20 allowlist;
- `forbidden_column_audit.csv` now stores `target_or_future_forbidden`, `raw_price_like` and combined `forbidden`;
- Up/Dn artifact now reports usage-level `PASS` and source-producer provenance `UNKNOWN`, not a source-level `PASS`;
- `ML/reports/fractal0_rich_entry_quality_normalized_artifact_auto_check.json` was added.

## Multiple Testing Context

Ranked search budget сохранён как в предыдущем corrected rich run:

```text
9 eligible profiles x 3 models x 3 targets x 3 primary filters = 243 ranked configs
```

Фактически выполнено `324` job, потому что дополнительно исполнены 3 diagnostic-only control profiles:

```text
(9 eligible + 3 diagnostic) x 3 models x 3 targets x 3 filters = 324 jobs
```

Diagnostic-only profiles не участвуют в winner selection.

Structured artifact:

- `ranked_search_budget.n_total_ranked_configs = 243`
- `active_search_budget.n_total_ranked_configs = 243`
- `n_total_executed_configs = 324`
- `permutation_null_repeats_executed_for_full_selection = 0`
- `permutation_gate = NOT_RUN_FOR_FULL_SELECTION`
- `ranked_search_budget.n_diagnostic_configs = 1521`
- `diagnostic_budget.listed_diagnostic_configs = 1521`

`listed_diagnostic_configs=1521` is the listed diagnostic space in JSON. It is not the ranked selection budget and was not executed by the default normalized run; executed jobs are `324`.

Команда передавала `--permutation-repeats 200`, но full-selection permutation этим run-ом не выполнена. Поэтому результат остаётся `RESEARCH_HINT_RICH_FEATURES`, а не statistical freeze.

## Changed Files

Код и тесты:

- `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- `tests/test_fractal0_entry_quality_filter.py`

Документация и handoff:

- `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`
- `docs/reports/2026-07-21-fractal0-rich-entry-quality.md`
- `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

Основные новые artifacts:

- `ML/reports/fractal0_rich_entry_quality_normalized.json`
- `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_scores.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_trades.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_feature_contract.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_feature_distribution_audit.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_normalized_feature_distribution_audit.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_token_coverage.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_normalization_config.json`
- `ML/reports/fractal0_rich_entry_quality_normalized_forbidden_column_audit.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_protocol_comparison.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_diagnostic_best_val_eval_by_profile.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_updn_provenance_gate.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_artifact_auto_check.json`

## Verification

TDD checks:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_normalized_rich_allowlist_excludes_raw_price_like_columns -q
```

Initial expected failure: missing `normalized_rich_feature_allowlist`.

Focused normalized feature/scaler tests:

```bash
./.venv/bin/python -m pytest \
  tests/test_fractal0_entry_quality_filter.py::test_normalized_rich_allowlist_excludes_raw_price_like_columns \
  tests/test_fractal0_entry_quality_filter.py::test_normalized_fractal_geometry_uses_atr_coordinates \
  tests/test_fractal0_entry_quality_filter.py::test_normalized_fractal_padding_is_zero_and_explicitly_masked \
  tests/test_fractal0_entry_quality_filter.py::test_normalized_schema_keeps_missing_indicator_columns_stable_across_splits -q
```

Result: `4 passed`.

Train-only scaler checks:

```bash
./.venv/bin/python -m pytest \
  tests/test_fractal0_entry_quality_filter.py::test_unit_scaler_fits_train_only_and_clips_validation \
  tests/test_fractal0_entry_quality_filter.py::test_assert_unit_scaled_frame_rejects_out_of_range_values -q
```

Result: `2 passed`.

Regression test for normalized `structure_f0_only` gate:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_normalized_structure_f0_gate_uses_normalized_required_fields -q
```

Red result before fix: `FEATURE_CONTRACT_FAIL`; green result after fix: `1 passed`.

Comparison artifact test:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_compare_rich_runs_protocol_uses_val_select_then_fixed_val_eval -q
```

Red result before implementation: missing `compare_rich_runs_protocol`; green result after implementation: `1 passed`.

Full test suite after final code changes:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Result:

```text
1376 passed, 52 warnings in 286.08s
```

This full-suite output was a local console verification. No separate saved test-log artifact was produced for that historical run.

Full normalized rerun command:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --rich-entry-quality \
  --normalized-rich-features \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_rich_entry_quality_normalized \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id S2_fractal0_buffer_0_5_entry_floor_2 \
  --permutation-repeats 200
```

Full run result:

```text
finished fractal0_rich_entry_quality
exit code 0
```

Artifact contract check:

```text
normalized full artifact contract PASS
```

Saved auto-check artifact:

```text
ML/reports/fractal0_rich_entry_quality_normalized_artifact_auto_check.json
overall_status=PASS
checks=11
```

Verified fields:

- `status=completed`
- `locked_test=not_opened`
- `feature_contract_variant=normalized_atr_unit`
- `normalization_config.fit_split=train_core`
- `ranked_search_budget.n_total_ranked_configs=243`
- `permutation_null_repeats_executed_for_full_selection=0`
- final normalized audit has `below_zero_rate.max=0.0`
- final normalized audit has `above_one_rate.max=0.0`
- forbidden column audit has `forbidden.sum=0`, `raw_price_like.sum=0`, `target_or_future_forbidden.sum=0`
- Up/Dn artifact has `usage_status=PASS` and `source_provenance_status=UNKNOWN`

## Results

Selected winner on `val_select`:

| field | value |
|---|---:|
| profile | `time_only` |
| model | `linear` |
| target | `target_entry_ev_regression` |
| filter | `top30` |
| n_trades | 625 |
| PF | 5.3059 |
| BS_p05 | 4.4198 |
| mean_pnl_r | 0.4447 |
| max_drawdown_r | 2.9656 |
| selected_fraction | 0.2724 |
| SL-rate | 0.0208 |

Fixed `val_eval` for selected rule:

| field | value |
|---|---:|
| n_trades | 660 |
| PF | 4.0268 |
| BS_p05 | 3.3955 |
| mean_pnl_r | 0.3397 |
| max_drawdown_r | 3.3906 |
| selected_fraction | 0.2872 |
| SL-rate | 0.0197 |

Diagnostic best `val_eval` equals the selected fixed `val_eval`; it is not a separate rule and does not raise the verdict.

### Candidate Shortlist / Leaderboard

These rows are not a new winner selection. They show the strongest normalized rows that passed the same practical `val_eval` screen used in the previous rich report: `PF > 2.7873`, `BS_p05 > 2.5085`, `n_trades >= 300` and positive `mean_pnl_r`. Columns `sel_*` are from `val_select`, where the rule was chosen; columns `eval_*` are the fixed check on the next validation segment.

| # | profile | model | target | filter | sel_frac | sel_PF | sel_BS_p05 | sel_mean | sel_DD | eval_n | eval_PF | eval_BS_p05 | eval_mean | eval_DD | eval_status |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `time_only` | `linear` | `target_entry_ev_regression` | `top30` | 27.2% | 5.3059 | 4.4198 | 0.4447 | 2.9656 | 660 | 4.0268 | 3.3955 | 0.3397 | 3.3906 | PASS |
| 2 | `time_only` | `linear` | `target_entry_ev_regression` | `top40` | 38.0% | 4.2040 | 3.4943 | 0.3936 | 3.5356 | 900 | 3.7417 | 3.1972 | 0.3401 | 4.9122 | PASS |
| 3 | `time_only` | `linear` | `target_entry_ev_regression` | `top50` | 48.0% | 4.0981 | 3.5928 | 0.3816 | 5.3712 | 1109 | 3.5710 | 3.1720 | 0.3284 | 6.1749 | PASS |
| 4 | `time_only` | `linear` | `target_entry_good_0_5r` | `top40` | 36.6% | 4.4321 | 3.7596 | 0.4137 | 4.2250 | 840 | 3.7279 | 3.1386 | 0.3346 | 4.2618 | PASS |
| 5 | `time_only` | `linear` | `target_entry_avoid_sl` | `top30` | 25.6% | 3.8982 | 3.1916 | 0.3698 | 4.2615 | 570 | 3.7630 | 3.1078 | 0.3338 | 3.5590 | PASS |
| 6 | `time_only` | `linear` | `target_entry_good_0_5r` | `top50` | 47.1% | 4.0090 | 3.5016 | 0.3907 | 5.5356 | 1099 | 3.5826 | 3.1054 | 0.3347 | 5.7347 | PASS |
| 7 | `movement_plus_time` | `linear` | `target_entry_good_0_5r` | `top40` | 36.7% | 4.0134 | 3.4647 | 0.3751 | 6.1843 | 979 | 3.3121 | 2.8836 | 0.3030 | 5.7166 | PASS |
| 8 | `movement_plus_time` | `linear` | `target_entry_good_0_5r` | `top30` | 26.0% | 4.1877 | 3.3793 | 0.3858 | 3.9608 | 760 | 3.4238 | 2.8551 | 0.3102 | 5.5577 | PASS |
| 9 | `time_only` | `hist_gradient_boosting` | `target_entry_good_0_5r` | `top50` | 48.6% | 3.6783 | 3.1580 | 0.3759 | 7.1506 | 1107 | 3.2926 | 2.8409 | 0.3367 | 4.4918 | PASS |
| 10 | `movement_plus_time` | `linear` | `target_entry_ev_regression` | `top50` | 46.9% | 4.0153 | 3.5155 | 0.3774 | 4.0928 | 1335 | 3.2778 | 2.8343 | 0.3196 | 5.6900 | PASS |
| 11 | `movement_plus_time` | `linear` | `target_entry_good_0_5r` | `top50` | 46.6% | 4.0341 | 3.5054 | 0.3835 | 5.3383 | 1223 | 3.2669 | 2.8338 | 0.3037 | 5.2031 | PASS |

Critical read: the normalized leaderboard is dominated by `time_only`; the remaining rows are `movement_plus_time`, which is also time-heavy. No normalized fractal-geometry profile enters this top-11 practical screen.

### Normalization impact on leaderboard rules

This table compares the exact same rules as the normalized leaderboard against their old rich-run `val_eval` results.

| profile | model | target | filter | old_BS_p05 | new_BS_p05 | delta_BS_p05 | old_PF | new_PF | delta_PF |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| `time_only` | `linear` | `target_entry_ev_regression` | `top30` | 3.3955 | 3.3955 | +0.0000 | 4.0268 | 4.0268 | +0.0000 |
| `time_only` | `linear` | `target_entry_ev_regression` | `top40` | 3.1972 | 3.1972 | +0.0000 | 3.7417 | 3.7417 | +0.0000 |
| `time_only` | `linear` | `target_entry_ev_regression` | `top50` | 3.1720 | 3.1720 | +0.0000 | 3.5710 | 3.5710 | +0.0000 |
| `time_only` | `linear` | `target_entry_good_0_5r` | `top40` | 3.2373 | 3.1386 | -0.0987 | 3.8202 | 3.7279 | -0.0923 |
| `time_only` | `linear` | `target_entry_avoid_sl` | `top30` | 3.1078 | 3.1078 | +0.0000 | 3.7630 | 3.7630 | +0.0000 |
| `time_only` | `linear` | `target_entry_good_0_5r` | `top50` | 2.9846 | 3.1054 | +0.1208 | 3.4275 | 3.5826 | +0.1552 |
| `movement_plus_time` | `linear` | `target_entry_good_0_5r` | `top40` | 2.7501 | 2.8836 | +0.1335 | 3.2496 | 3.3121 | +0.0625 |
| `movement_plus_time` | `linear` | `target_entry_good_0_5r` | `top30` | 3.0671 | 2.8551 | -0.2120 | 3.5465 | 3.4238 | -0.1227 |
| `time_only` | `hist_gradient_boosting` | `target_entry_good_0_5r` | `top50` | 2.6369 | 2.8409 | +0.2040 | 3.0959 | 3.2926 | +0.1967 |
| `movement_plus_time` | `linear` | `target_entry_ev_regression` | `top50` | 2.7998 | 2.8343 | +0.0345 | 3.2690 | 3.2778 | +0.0089 |
| `movement_plus_time` | `linear` | `target_entry_good_0_5r` | `top50` | 2.8127 | 2.8338 | +0.0212 | 3.2655 | 3.2669 | +0.0014 |

Normalization barely changed the pure `time_only` rules because they do not contain raw price-like inputs. It modestly improved some time-heavy rules, especially `time_only / hist_gradient_boosting / target_entry_good_0_5r / top50` and `movement_plus_time / linear / target_entry_good_0_5r / top40`, but this did not create a stronger non-time leader.

### Old-vs-normalized protocol comparison

Primary comparison uses protocol path: select per profile on `val_select`, then report fixed `val_eval`.

| profile | old_eval_BS_p05 | new_eval_BS_p05 | delta_BS_p05 | old_eval_PF | new_eval_PF | delta_PF |
|---|---:|---:|---:|---:|---:|---:|
| `time_only` | 3.3955 | 3.3955 | 0.0000 | 4.0268 | 4.0268 | 0.0000 |
| `rich_combined_k40` | 2.2701 | 2.6696 | +0.3994 | 2.7715 | 3.0724 | +0.3009 |
| `price_action_h1` | 2.2980 | 2.4810 | +0.1831 | 2.6590 | 2.8890 | +0.2300 |
| `structure_f0_only` | 2.3513 | 2.4775 | +0.1261 | 2.7913 | 2.9296 | +0.1383 |
| `planned_geometry_only` | 2.6519 | 2.4622 | -0.1896 | 3.2069 | 3.0481 | -0.1588 |
| `structure_nearest_k20` | 2.4456 | 2.2727 | -0.1729 | 2.9027 | 2.8044 | -0.0983 |
| `movement_plus_time` | 2.7998 | 2.2088 | -0.5910 | 3.2690 | 2.8388 | -0.4302 |
| `relative_geometry_k40` | 2.2147 | 2.1462 | -0.0685 | 2.6503 | 2.5856 | -0.0647 |
| `structure_nearest_k40` | 2.2147 | 2.1462 | -0.0685 | 2.6503 | 2.5856 | -0.0647 |

Interpretation: normalized contract did not change the formal winner. It improved fixed `val_eval` for `rich_combined_k40`, `price_action_h1` and `structure_f0_only`, but not enough to beat `time_only` in the selection protocol.

### Diagnostic best by profile

Diagnostic best-on-`val_eval` table is not eligible for winner selection.

| profile | old_BS_p05 | new_BS_p05 | old_PF | new_PF |
|---|---:|---:|---:|---:|
| `movement_plus_time` | 3.0671 | 2.8836 | 3.5465 | 3.3121 |
| `planned_geometry_only` | 2.7743 | 2.5618 | 3.3574 | 3.0667 |
| `price_action_h1` | 2.6873 | 2.7035 | 3.0283 | 3.2849 |
| `relative_geometry_k40` | 2.9337 | 2.7533 | 3.4858 | 3.2826 |
| `rich_combined_k40` | 2.6663 | 2.7206 | 3.2703 | 3.1590 |
| `structure_f0_only` | 2.7218 | 2.7377 | 3.2408 | 3.3044 |
| `structure_nearest_k20` | 2.6277 | 2.7233 | 3.1436 | 3.1353 |
| `structure_nearest_k40` | 2.9337 | 2.7533 | 3.4858 | 3.2826 |
| `time_only` | 3.3955 | 3.3955 | 4.0268 | 4.0268 |

### Diagnostic control profiles

These profiles were executed to interpret `time_only`; they were not eligible for winner selection.

Protocol path: select within the profile on `val_select`, then apply the fixed rule to `val_eval`.

| profile | selected_on_val_select | val_select_BS_p05 | fixed_val_eval_BS_p05 | fixed_val_eval_PF | fixed_val_eval_trades |
|---|---|---:|---:|---:|---:|
| `atr_only` | `linear / target_entry_ev_regression / top30` | 3.2246 | 1.7696 | 2.5521 | 179 |
| `time_plus_atr` | `linear / target_entry_ev_regression / top30` | 3.8507 | 2.5106 | 3.2257 | 371 |
| `planned_geometry_no_atr` | `extra_trees_shallow / target_entry_ev_regression / top30` | 3.3268 | 2.3758 | 2.9073 | 698 |

Post-hoc diagnostic best on `val_eval`, not eligible for winner selection:

| profile | best_val_eval_BS_p05 | best_val_eval_PF | trades | rule |
|---|---:|---:|---:|---|
| `atr_only` | 2.2993 | 2.5777 | 1622 | `extra_trees_shallow / target_entry_ev_regression / top40` |
| `time_plus_atr` | 3.1986 | 3.6585 | 938 | `hist_gradient_boosting / target_entry_avoid_sl / top40` |
| `planned_geometry_no_atr` | 2.6227 | 3.0765 | 727 | `extra_trees_shallow / target_entry_avoid_sl / top30` |

Interpretation: `time_plus_atr` is stronger than `atr_only`, but still weaker than the formal `time_only` winner on the protocol path. The post-hoc diagnostic best for `time_plus_atr` is close enough to disclose, but it is not a selectable rule in this rerun.

### Feature and scale audits

Final normalized feature audit:

```text
PASS rows: 6072
WARNING rows: 6990
ERROR rows: 0
below_zero_rate.max = 0.0
above_one_rate.max = 0.0
```

`WARNING` means many columns are constant or near-constant after scaling, not that values violate the `[0,1]` contract. Decision: accept-as-warning for this research rerun; disclose before any future shortlist/freeze.

Warning breakdown:

| warning_type | rows | decision |
|---|---:|---|
| missing indicators constant zero | 6531 | expected schema artifact |
| present masks constant | 420 | expected because every row has enough tokens |
| source features constant/near-constant | 39 | disclosed; not interpreted as signal |

The 39 source-feature warnings are `fractal0_strong`, `fractal0_break`, `fractal0_shift` and `fractal0_up/dn_*` horizons across splits. They are retained as disclosed research inputs, not as evidence of informative source features.

Token coverage:

```text
WARNING rows: 15
rows_with_zero_tokens_rate = 0.0
padding_rate = 0.0
truncation_rate = 1.0
```

Decision: accept-as-warning for this rerun. The warnings are expected because all rows have more available fractal snapshots than profile length, so nearest-k profiles truncate to K tokens. This is not a missing-token defect, but it must be treated as a profile design disclosure.

Audit correction: `structure_nearest_k20` token coverage now reports K=20. The previous artifact row showed K=40 and was invalidated for A7 token-coverage interpretation only; model metrics were unchanged because the model allowlist already used 20-token columns.

Feature distribution gates:

| profile | features | constant_features | non_constant_fraction | status |
|---|---:|---:|---:|---|
| `planned_geometry_only` | 5 | 0 | 1.0000 | PASS |
| `time_only` | 6 | 0 | 1.0000 | PASS |
| `structure_f0_only` | 22 | 12 | 0.4545 | PASS |
| `structure_nearest_k20` | 300 | 20 | 0.9333 | PASS |
| `structure_nearest_k40` | 600 | 40 | 0.9333 | PASS |
| `relative_geometry_k40` | 600 | 40 | 0.9333 | PASS |
| `price_action_h1` | 7 | 0 | 1.0000 | PASS |
| `movement_plus_time` | 7 | 0 | 1.0000 | PASS |
| `rich_combined_k40` | 618 | 40 | 0.9353 | PASS |
| `atr_only` | 1 | 0 | 1.0000 | PASS |
| `time_plus_atr` | 7 | 0 | 1.0000 | PASS |
| `planned_geometry_no_atr` | 4 | 0 | 1.0000 | PASS |

`structure_f0_only` has `non_constant_fraction=0.4545`, below the generic 0.50 structural threshold, but passes a special required-fields gate. The required live fields `fractal0_price_to_planned_limit_atr`, `fractal0_direction_unit` and `fractal0_shift` are present; constant Up/Dn and `fractal0_shift` rows are disclosed informational constants, not proof of signal.

Scale contract verdict: `PASS` for bounded finite final model inputs; `RESEARCH_HINT_RICH_FEATURES` remains the experiment verdict because model selection is still a validation-search result.

## Conclusions

The normalized rerun fixed the scale contract, not the core research conclusion.

Main conclusion:

- formal winner remains `time_only / linear / target_entry_ev_regression / top30`;
- normalized rich/fractal profiles did not beat `time_only` under the protocol selection path;
- `rich_combined_k40`, `price_action_h1` and `structure_f0_only` improved versus old rich under protocol comparison, so the normalization was not neutral for all profiles;
- those improvements are research hints only, not candidate evidence.

Invalidated assumption:

- The old rich comparison was not a clean test of rich geometry under a bounded normalized contract. It remains useful as historical baseline, but normalized artifacts are now the preferred source for old-vs-normalized interpretation.

No permission is granted to open `locked_test`.

## Limitations / Open Questions

- Full-selection permutation was not run: `permutation_gate=NOT_RUN_FOR_FULL_SELECTION`.
- Diagnostic-only profiles increased executed jobs to `324`, but ranked budget remains `243`.
- `normalized_feature_distribution_audit` has many `WARNING` rows due constant/near-constant features.
- `token_coverage` has `WARNING` rows due truncation rate `1.0` in nearest-k profiles.
- Up/Dn source-producer provenance remains `UNKNOWN`; this rerun verifies Python normalized-builder usage only.
- The historical full-suite verification was not saved as a separate test-log artifact; current reproducible checks are listed in Verification and `artifact_auto_check.json`.
- pandas `PerformanceWarning` appeared during unit scaling because DataFrame columns are inserted one by one. This is a performance issue, not a contract failure.
- Generated `scores.csv` and `trades.csv` are large; read with `usecols`, `nrows` or chunks.
- `locked_test` remains closed.

## Split Disclosure

| split | min_time | max_time | planned_orders | filled_trades | fill_rate |
|---|---|---|---:|---:|---:|
| `train_core` | 2004-07-06 20:00:00 | 2019-06-20 14:00:00 | 44159 | 21343 | 0.4833 |
| `val_select` | 2019-06-20 16:00:00 | 2021-03-08 03:00:00 | 4731 | 2294 | 0.4849 |
| `val_eval` | 2021-03-08 05:00:00 | 2022-12-02 07:00:00 | 4732 | 2298 | 0.4856 |

Split roles:

- `train_core`: trains ML-exit, ML-entry and normalized unit scalers.
- `val_select`: selects exactly one eligible rule.
- `val_eval`: fixed selected rule only.
- `locked_test`: not opened.

Planned-order diagnostics:

| split | planned_orders | filled_orders | no_fill_orders | expected_pnl_per_filled_trade | expected_pnl_per_planned_order |
|---|---:|---:|---:|---:|---:|
| `train_core` | 44159 | 21343 | 22816 | -0.0518 | -0.0250 |
| `val_select` | 4731 | 2294 | 2437 | -0.0079 | -0.0038 |
| `val_eval` | 4732 | 2298 | 2434 | -0.0653 | -0.0317 |

## Next Step

Do not open `locked_test`.

Recommended next step: a new pre-registered shortlist replication/probe using a small frozen set. Do not expand the grid during that probe. Reasonable shortlist candidates from normalized artifacts:

- `time_only / linear / target_entry_ev_regression / top30` as the formal protocol winner;
- `rich_combined_k40` as the strongest normalized improvement versus old protocol comparison;
- `structure_f0_only` or `price_action_h1` as smaller normalized controls with positive protocol deltas.

Before any freeze/candidate claim:

- define the shortlist before running;
- keep fixed `val_select` cutoff logic;
- add yearly/side robustness;
- decide how to handle token truncation warnings;
- run a proper correction or independent verification period.

## Related Materials

- Plan: `docs/superpowers/plans/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`
- Previous rich report: `docs/reports/2026-07-21-fractal0-rich-entry-quality.md`
- Main artifact: `ML/reports/fractal0_rich_entry_quality_normalized.json`
- Summary: `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv`
- Normalization config: `ML/reports/fractal0_rich_entry_quality_normalized_normalization_config.json`
- Final input audit: `ML/reports/fractal0_rich_entry_quality_normalized_normalized_feature_distribution_audit.csv`
- Protocol comparison: `ML/reports/fractal0_rich_entry_quality_normalized_protocol_comparison.csv`
- Diagnostic best by profile: `ML/reports/fractal0_rich_entry_quality_normalized_diagnostic_best_val_eval_by_profile.csv`
- Artifact auto-check: `ML/reports/fractal0_rich_entry_quality_normalized_artifact_auto_check.json`
- Runner docs: `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
