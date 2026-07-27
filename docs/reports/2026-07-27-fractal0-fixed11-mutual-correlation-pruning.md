# Fractal0 Fixed-11 Mutual-Correlation Pruning

> **Дата**: 2026-07-27
> **Статус**: Completed
> **Вердикт**: PASS
> **Цель**: Сократить 11 already-passed fixed rules до retained subset по измеренному mutual overlap без изменения правил и без выбора нового winner по `locked_test`.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-27-fixed11-mutual-correlation-pruning.md`

## Context

Предыдущий audit подтвердил `candidate_audit_passed` для 11 individual fixed rules из `ML/reports/fractal0_fixed11_rich_entry_locked_test*`. Этот этап был разрешён только как read-only pruning: `locked_test` уже открыт, поэтому его нельзя использовать для нового выбора по PF, PnL, drawdown или `BS_p05`.

Канонический предыдущий отчёт: `docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md`.

## Уровень этапа

- `lifecycle_status`: `post_locked_test_read_only_pruning`
- `stage_level`: проверочный audit/disclosure, без повышения выше `candidate`
- `allowed_max_verdict`: `candidate_not_trading_ready`
- `allowed_max_verdict_note`: local stage interpretation cap, not a methodology verdict value
- `overall_decision`: `pruning_passed`

## Methodology

Применены ограничения `docs/methodology/00-research-management.md`, `06-temporal-split.md`, `09-validation-freeze.md`, `10-frozen-test-oos.md`, `11-robustness.md`, `12-backtest-costs.md`, `16-reporting-audit.md`.

Политика запуска:

- `current_search_budget`: `0_new_rules`
- `cumulative_search_budget`: `inherited_from_fixed11_candidate_audit`
- `origin_bias`: `follow_up_required_from_fixed11_candidate_audit`
- `locked_test_policy`: `overlap_measurement_only_no_winner_selection`
- `representative_policy`: `lowest_original_rank_then_rule_id`
- `locked_test_performance_used_for_representative_choice`: `false`
- allowed decisions: `pruning_passed`, `all_rules_duplicate_research_only`, `pruning_blocked`

## What Was Done

Добавлен runner `ML/baseline/prune_fractal0_fixed11_mutual_correlation.py`. Он читает только сохранённые fixed-11 CSV/JSON, проверяет preflight contract, нормализует сделки, считает pairwise overlap/correlation, строит duplicate clusters и пишет retained-subset manifest.

Runner не обучает модель, не считает новые scores, не запускает симулятор, не меняет cutoffs/rules/profile/model/target/filter, spread, fill policy или PnL convention.

## Multiple Testing Context

Новый search не выполнялся: `current_search_budget=0_new_rules`. Этап измеряет только взаимное дублирование 11 правил, которые уже прошли независимый audit. Накопленный риск подбора унаследован от fixed-11 candidate audit и не обнуляется.

Retained subset не является новым winner по `locked_test`; представители выбираются только по заранее существующему `original_rank`, затем по стабильному `rule_id`.

## Changed Files

- `ML/baseline/prune_fractal0_fixed11_mutual_correlation.py`
- `tests/test_fractal0_fixed11_mutual_correlation_pruning.py`
- `docs/ML/prune_fractal0_fixed11_mutual_correlation.py.md`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_*`

## Verification

Команды:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_mutual_correlation_pruning.py -q
./.venv/bin/python -m pytest tests/ -q
./.venv/bin/python ML/baseline/prune_fractal0_fixed11_mutual_correlation.py \
  --input-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test \
  --audit-json ML/reports/fractal0_fixed11_candidate_audit.json \
  --output-prefix ML/reports/fractal0_fixed11_mutual_correlation_pruning
```

Результаты проверки:

- unit tests: `12 passed`
- full test suite: `1480 passed, 52 warnings`
- CLI result: `overall_decision=pruning_passed`
- pairwise rows: `55`
- input rules: `11`
- retained rules: `5`
- removed strong duplicates: `6`
- all metric matrices are `11 x 11`, symmetric, with diagonal `1.0`

## Results

Structured artifacts:

- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_pairwise.csv`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_clusters.csv`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_fill_daily_pnl_matrix.csv`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_fill_weekly_pnl_matrix.csv`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_exit_daily_pnl_matrix.csv`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_exit_weekly_pnl_matrix.csv`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_exit_drawdown_overlap_matrix.csv`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_retained_subset.json`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_summary.json`

Input SHA256 hashes are recorded in `ML/reports/fractal0_fixed11_mutual_correlation_pruning_summary.json`.

Thresholds:

- `strong_duplicate`: `fill_overlap_ratio >= 0.75`, `same_direction_ratio >= 0.90`, `fill_bucket_pnl_corr >= 0.85`, `fill_daily_pnl_corr >= 0.75`, `fill_weekly_pnl_corr >= 0.75`, `exit_daily_pnl_corr >= 0.75`, `exit_weekly_pnl_corr >= 0.75`
- `partial_overlap`: disclosure warning only; it does not drop a rule

## Retained Subset

- `rank01_time_only_linear_target_entry_ev_regression_top30`
- `rank05_time_only_linear_target_entry_avoid_sl_top30`
- `rank07_movement_plus_time_linear_target_entry_good_0_5r_top40`
- `rank09_time_only_hist_gradient_boosting_target_entry_good_0_5r_top50`
- `rank10_movement_plus_time_linear_target_entry_ev_regression_top50`

## Dropped Duplicate Rules

- `rank02_time_only_linear_target_entry_ev_regression_top40` -> `rank01_time_only_linear_target_entry_ev_regression_top30`
- `rank03_time_only_linear_target_entry_ev_regression_top50` -> `rank01_time_only_linear_target_entry_ev_regression_top30`
- `rank04_time_only_linear_target_entry_good_0_5r_top40` -> `rank01_time_only_linear_target_entry_ev_regression_top30`
- `rank06_time_only_linear_target_entry_good_0_5r_top50` -> `rank01_time_only_linear_target_entry_ev_regression_top30`
- `rank08_movement_plus_time_linear_target_entry_good_0_5r_top30` -> `rank07_movement_plus_time_linear_target_entry_good_0_5r_top40`
- `rank11_movement_plus_time_linear_target_entry_good_0_5r_top50` -> `rank07_movement_plus_time_linear_target_entry_good_0_5r_top40`

## Partial-Overlap Warnings

Pairwise verdict counts:

- `strong_duplicate`: `13`
- `partial_overlap`: `42`
- `unclear_or_complementary`: `0`

There are `7` additional `strong_duplicate` edges recorded as disclosure-only in `non_representative_strong_duplicate_pairs`. They were not used for drops because the pruning policy drops a rule only on a direct `strong_duplicate` edge to its retained representative.

Partial-overlap links are disclosure warnings only. They did not remove rules automatically.

## Split Disclosure

Split boundaries and sample-size checks are inherited from `docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md` and `ML/reports/fractal0_fixed11_candidate_audit.json`.

| role | row_count | min_time | max_time | source |
|---|---:|---|---|---|
| `train_core` | 44159 | `2004-07-06 20:00:00` | `2019-06-20 14:00:00` | `computed_from_local_csv` |
| `val_select` | 4731 | `2019-06-20 16:00:00` | `2021-03-08 03:00:00` | `computed_from_local_csv` |
| `val_eval` | 4732 | `2021-03-08 05:00:00` | `2022-12-02 07:00:00` | `computed_from_local_csv` |
| `locked_test` | 9463 | `2022-12-02 11:00:00` | `2026-06-04 12:00:00` | `computed_from_local_csv` |

This pruning stage did not open a new period and did not combine `locked_test` with forward data. Every input rule had at least `100` locked-test trades; the preflight also checked that `summary`, `selection`, and `trades` use the same 11 `rule_id`.

## Forbidden Interpretations

- Retained subset is not trading-ready.
- Pruning does not improve profitability.
- Dropped duplicate rules are not bad rules.
- `locked_test` PF/PnL/drawdown/`BS_p05` were not used to select a new winner.

## Limitations / Open Questions

- This is post-`locked_test` read-only disclosure, not independent confirmation on new data.
- MT4/tester parity is still not done for the retained subset.
- Stress-spread disclosure is still not done for the retained subset.
- Model card is still blocked until parity/stress disclosure.
- `partial_overlap` is only a warning; it may still matter for portfolio sizing and monitoring.

## Conclusions

The fixed-11 set is reduced to 5 retained rules and 6 direct strong-duplicate drops. The result is a valid pruning outcome with `overall_decision=pruning_passed`, but it does not raise the candidate beyond the previous fixed-11 audit status.

## Next Step

Run MT4/tester parity only for the retained subset:

- `rank01_time_only_linear_target_entry_ev_regression_top30`
- `rank05_time_only_linear_target_entry_avoid_sl_top30`
- `rank07_movement_plus_time_linear_target_entry_good_0_5r_top40`
- `rank09_time_only_hist_gradient_boosting_target_entry_good_0_5r_top50`
- `rank10_movement_plus_time_linear_target_entry_ev_regression_top50`

After parity, run stress-spread disclosure for the retained subset. Create model card only after pruning, parity, and stress disclosure are complete.

## Related Materials

- `docs/superpowers/plans/2026-07-27-fixed11-mutual-correlation-pruning.md`
- `docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_summary.json`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_retained_subset.json`
- `docs/ML/prune_fractal0_fixed11_mutual_correlation.py.md`
