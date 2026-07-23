# Fractal0 Rich Entry Leaderboard Robustness Audit

> **Дата**: 2026-07-23
> **Статус**: Completed
> **Вердикт**: research_only
> **Цель**: Проверить validation-slice устойчивость 11 fixed normalized rich-entry leaderboard input rows без нового поиска и без открытия `locked_test`.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md`

## Context

Audit covers the 11 rows from `Candidate Shortlist / Leaderboard` in
`docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`.
The original rank is preserved. Winner selection was not performed.

## Уровень Этапа

Research-only validation artifact audit.
`scope=validation_artifact_leaderboard_robustness_slice`.

```text
lifecycle_status: research_only
origin_bias: normalized rich-entry validation leaderboard selected after broad search
research_priority: compare robustness profiles before deciding whether regime reformulation or a narrower additive probe is justified
current_search_budget: no new search, 11 fixed audit input rows
cumulative_search_budget: inherited from normalized rich-entry search, 243 ranked configs plus diagnostic controls
next_probe_freeze: not created in this stage
allowed_max_verdict: research_only
forbidden_interpretations: candidate, tradable, live_ready, production, permission_to_open_locked_test, new_winner
```

## What Was Done

- Added `ML/baseline/audit_leaderboard_robustness.py`.
- Added `tests/test_leaderboard_robustness_audit.py`.
- Recomputed per-rule validation-slice robustness diagnostics for 11 fixed leaderboard rows.
- Preserved original leaderboard order and did not perform winner selection.
- Wrote `ML/reports/leaderboard_robustness_audit*` artifacts.

## Multiple Testing Context

This audit inherits origin bias from the normalized rich-entry validation search.
The 11 rows were already chosen by a practical `val_eval` screen. Metrics below
are diagnostics only and do not authorize `locked_test`.

## Scale Contract / Normalization Disclosure

- `scale_contract.status=DIAGNOSTIC_ONLY`.
- `structural_profile_gate_status=PASS`.
- `normalized_feature_distribution_flag_counts={'PASS': 6072, 'WARNING': 6990}`.
- Warning action: `accept-as-warning`. Constant or near-constant normalized
  feature columns are disclosed as preprocessing warnings; this audit remains
  `research_only` and cannot support stronger interpretation.
- `normalization_config.mode=normalized_atr_unit`.
- `normalization_config.fit_split=train_core`.
- `normalization_config_json=/home/hohla/git/SoSimple/ML/reports/fractal0_rich_entry_quality_normalized_normalization_config.json`.
- `normalized_feature_distribution_audit_csv=/home/hohla/git/SoSimple/ML/reports/fractal0_rich_entry_quality_normalized_normalized_feature_distribution_audit.csv`.
- Source structural `flag_statuses=['PASS']`.
- `locked_test` was not used to choose normalization, scaler, clipping or transformations.

## Changed Files

Tracked/visible changes for this stage:

- `ML/baseline/audit_leaderboard_robustness.py`
- `tests/test_leaderboard_robustness_audit.py`
- `docs/ML/audit_leaderboard_robustness.py.md`
- `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
- `MODULE_INDEX.md`
- `docs/reports/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md`
- `docs/superpowers/roadmap.md`
- `CONTEXT_HANDOFF.md`
- `CHANGELOG.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`
- `ML/reports/leaderboard_robustness_audit.json`
- `ML/reports/leaderboard_robustness_audit*.csv`

Unrelated pre-existing working-tree change not touched by this stage:

- `docs/superpowers/audit.md`

## Verification

Commands run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_robustness_audit.py -q
```

Result: `11 passed in 0.67s`.

```bash
./.venv/bin/python ML/baseline/audit_leaderboard_robustness.py --input-prefix ML/reports/fractal0_rich_entry_quality_normalized --output-prefix ML/reports/leaderboard_robustness_audit
```

Result: exit code `0`, `status=completed`, `overall_decision=LEADERBOARD_ROBUSTNESS_INCOMPLETE_NEEDS_COST_TIME_CHECKS`.

```bash
./.venv/bin/python -m pytest tests/ -q
```

Result: `1401 passed, 52 warnings in 285.31s`.

## Results

- `status=completed`
- `verdict=research_only`
- `locked_test=not_opened`
- `leaderboard_rule_count=11`
- `overall_decision=LEADERBOARD_ROBUSTNESS_INCOMPLETE_NEEDS_COST_TIME_CHECKS`
- `overall_decision_reasons=['stress_costs_not_computable', 'timezone_shift_not_run', 'calendar_permutation_importance_not_run', 'sequential_position_constraint_not_run', 'multi_seed_not_run', 'provider_drift_not_run', 'transfer_not_run']`
- `scale_contract=DIAGNOSTIC_ONLY`
- classification decisions: `{'RULE_ROBUSTNESS_INCOMPLETE': 11}`
- interpretations: `{'stable_but_time_explained_needs_cost_resimulation': 7, 'time_heavy_not_additive_evidence_needs_cost_resimulation': 4}`
- anchor row: `rank01_time_only_linear_target_entry_ev_regression_top30`, `n_trades=660`, `pf=4.026757702884287`, `sequential_block_bs_p05=3.3067645101786955`

Per-rule classification:

| rank | rule_id | decision | interpretation | reasons |
|---:|---|---|---|---|
| 1 | `rank01_time_only_linear_target_entry_ev_regression_top30` | `RULE_ROBUSTNESS_INCOMPLETE` | `stable_but_time_explained_needs_cost_resimulation` | `stricter_cutoff_sample_fragile,stress_costs_not_computable` |
| 2 | `rank02_time_only_linear_target_entry_ev_regression_top40` | `RULE_ROBUSTNESS_INCOMPLETE` | `stable_but_time_explained_needs_cost_resimulation` | `stress_costs_not_computable` |
| 3 | `rank03_time_only_linear_target_entry_ev_regression_top50` | `RULE_ROBUSTNESS_INCOMPLETE` | `stable_but_time_explained_needs_cost_resimulation` | `stress_costs_not_computable` |
| 4 | `rank04_time_only_linear_target_entry_good_0_5r_top40` | `RULE_ROBUSTNESS_INCOMPLETE` | `stable_but_time_explained_needs_cost_resimulation` | `stricter_cutoff_sample_fragile,stress_costs_not_computable` |
| 5 | `rank05_time_only_linear_target_entry_avoid_sl_top30` | `RULE_ROBUSTNESS_INCOMPLETE` | `stable_but_time_explained_needs_cost_resimulation` | `stricter_cutoff_sample_fragile,stress_costs_not_computable` |
| 6 | `rank06_time_only_linear_target_entry_good_0_5r_top50` | `RULE_ROBUSTNESS_INCOMPLETE` | `stable_but_time_explained_needs_cost_resimulation` | `stricter_cutoff_sample_fragile,stress_costs_not_computable` |
| 7 | `rank07_movement_plus_time_linear_target_entry_good_0_5r_top40` | `RULE_ROBUSTNESS_INCOMPLETE` | `time_heavy_not_additive_evidence_needs_cost_resimulation` | `stricter_cutoff_sample_fragile,stress_costs_not_computable` |
| 8 | `rank08_movement_plus_time_linear_target_entry_good_0_5r_top30` | `RULE_ROBUSTNESS_INCOMPLETE` | `time_heavy_not_additive_evidence_needs_cost_resimulation` | `stricter_cutoff_sample_fragile,stress_costs_not_computable` |
| 9 | `rank09_time_only_hist_gradient_boosting_target_entry_good_0_5r_top50` | `RULE_ROBUSTNESS_INCOMPLETE` | `stable_but_time_explained_needs_cost_resimulation` | `stricter_cutoff_sample_fragile,stress_costs_not_computable` |
| 10 | `rank10_movement_plus_time_linear_target_entry_ev_regression_top50` | `RULE_ROBUSTNESS_INCOMPLETE` | `time_heavy_not_additive_evidence_needs_cost_resimulation` | `stress_costs_not_computable` |
| 11 | `rank11_movement_plus_time_linear_target_entry_good_0_5r_top50` | `RULE_ROBUSTNESS_INCOMPLETE` | `time_heavy_not_additive_evidence_needs_cost_resimulation` | `stress_costs_not_computable` |

All rows disclose `sequential_position_constraint_not_run`, `timezone_shift_not_run`
and `calendar_permutation_importance_not_run`.

Side/year gate summary:

- side diagnostics file: `ML/reports/leaderboard_robustness_audit_side.csv`
- yearly diagnostics file: `ML/reports/leaderboard_robustness_audit_yearly.csv`
- min side trades: `269`
- min side PF: `3.030454150121584`
- max side drawdown R: `5.459524290552736`
- min yearly trades: `265`
- min yearly PF: `2.994451199991656`

These values are validation-slice diagnostics only. They are not a trading
verdict and do not raise the stage above `research_only`.

```text
allowed_max_verdict=research_only
not_trading_evidence_reason=validation artifact leaderboard slice, locked_test not opened, inherited broad-search origin bias
forbidden_interpretations=candidate/tradable/live_ready/production/permission_to_open_locked_test/new_winner
```

## Conclusions

The checked leaderboard remains time-heavy: all 11 rows are `time_only` or
`movement_plus_time`. This audit cannot establish standalone fractal/additive
non-time evidence.

Stronger interpretation is blocked by missing stress-cost resimulation,
timezone-shift rescore, calendar permutation importance, multi-seed,
provider-drift, transfer and sequential-position checks. Winner selection was
not performed.

## Limitations / Open Questions

- `multi_seed_status=NOT_RUN`.
- `provider_drift_status=NOT_RUN`.
- `transfer_status=NOT_RUN`.
- `locked_test_status=not_opened`.
- `stress_costs_status=NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS`.
- `timezone_shift_status=NOT_RUN`.
- `calendar_permutation_importance_status=NOT_RUN`.
- `sequential_position_constraint_status=NOT_RUN`.

## Split Disclosure

Source split rows from `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`:

| split | start | end | rows | positives | positive_rate |
|---|---|---|---:|---:|---:|
| `train_core` | 2004-07-06 20:00:00 | 2019-06-20 14:00:00 | 44159 | 21343 | 0.4833 |
| `val_select` | 2019-06-20 16:00:00 | 2021-03-08 03:00:00 | 4731 | 2294 | 0.4849 |
| `val_eval` | 2021-03-08 05:00:00 | 2022-12-02 07:00:00 | 4732 | 2298 | 0.4856 |
| `locked_test` | UNKNOWN_IN_SOURCE_ARTIFACTS | UNKNOWN_IN_SOURCE_ARTIFACTS | UNKNOWN_IN_SOURCE_ARTIFACTS | UNKNOWN_IN_SOURCE_ARTIFACTS | UNKNOWN_IN_SOURCE_ARTIFACTS |

Split roles:

- `train_core`: trains ML-exit, ML-entry and normalized unit scalers.
- `val_select`: stores fixed cutoff per leaderboard rule.
- `val_eval`: fixed validation evaluation slice used by this audit.
- `locked_test`: not opened.

Sample-size gate after filters is rule-level. In this audit, all 11 fixed rows
have `val_eval` trades in `ML/reports/leaderboard_robustness_audit_summary.csv`;
stricter cutoff small-N warnings remain for ranks 1, 4, 5, 6, 7, 8 and 9.

## Next Step

Write a bounded stress-cost/time-calendar/sequential-position robustness
closure plan before any new shortlist, freeze or `locked_test` discussion.

## Related Materials

- `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`
- `docs/reports/2026-07-23-time-only-robustness-audit.md`
- `ML/reports/leaderboard_robustness_audit.json`
- `docs/ML/audit_leaderboard_robustness.py.md`
