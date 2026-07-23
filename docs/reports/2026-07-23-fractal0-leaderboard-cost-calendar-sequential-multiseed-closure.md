# Fractal0 Leaderboard Cost Calendar Sequential Multiseed Closure

> **Дата**: 2026-07-23
> **Статус**: Completed
> **Вердикт**: research_only
> **Цель**: Закрыть или явно раскрыть cost/calendar/sequential/multi-seed блокеры для 11 fixed normalized rich-entry leaderboard rows без нового поиска и без открытия `locked_test`.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-23-fractal0-leaderboard-cost-calendar-sequential-multiseed-closure.md`

## Context

Этап продолжает leaderboard robustness audit для 11 fixed normalized rows. Он
не выбирает нового winner, не расширяет список правил и не открывает
`locked_test`.

## Уровень Этапа

Research-only validation artifact closure.

```text
lifecycle_status=research_only
origin_bias=normalized rich-entry validation leaderboard selected after broad search
research_priority=medium; close/disclose internal robustness blockers before any freeze discussion
current_search_budget=no new search, 11 fixed audit input rows, 5 predefined multi-seed seeds only if bounded rerun is implemented
cumulative_search_budget=inherited from normalized rich-entry search, 243 ranked configs plus diagnostic controls
next_probe_freeze=not created in this stage
allowed_max_verdict=research_only
locked_test=not_opened
provider_drift_status=NOT_IN_SCOPE
transfer_status=NOT_IN_SCOPE
cost_model_disclosure_status=spread=DISCLOSED_BASELINE; commission/swap/slippage/requote_open_failure/latency/next_bar_entry/position_limits=NOT_IN_SCOPE; net-cost gate NOT_RUN
calendar_permutation_importance_status=NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS
calendar_no_ml_baseline_status=NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS
forbidden_interpretations=candidate/tradable/live_ready/production/permission_to_open_locked_test/new_winner
```

## What Was Done

- Added `ML/baseline/audit_leaderboard_closure.py`.
- Added `tests/test_leaderboard_closure_audit.py`.
- Reused the exact 11 `LEADERBOARD_RULES` and preserved `original_rank`.
- Computed calendar slices and sequential-position diagnostics from saved
  `val_eval` trades.
- Disclosed stress-cost, timezone-shift, calendar permutation/no-ML baseline
  and multi-seed as not computable from saved artifacts where no honest frozen
  resimulation/rescore/per-seed path exists.
- Wrote `ML/reports/leaderboard_closure_audit*` artifacts.

## Multiple Testing Context

No new search was run. The 11 rows are inherited from the normalized rich-entry
leaderboard selected after a broad validation search. This closure only audits
that fixed universe and cannot promote any row to candidate.

## Changed Files

- `ML/baseline/audit_leaderboard_closure.py`
- `tests/test_leaderboard_closure_audit.py`
- `docs/ML/audit_leaderboard_closure.py.md`
- `docs/ML/audit_leaderboard_robustness.py.md`
- `docs/reports/2026-07-23-fractal0-leaderboard-cost-calendar-sequential-multiseed-closure.md`
- `docs/superpowers/roadmap.md`
- `MODULE_INDEX.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`
- `ML/reports/leaderboard_closure_audit*`

Pre-existing unrelated working-tree change not touched by this stage:
`docs/superpowers/audit.md`.

## Verification

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_closure_audit.py -q
```

Result after audit fixes: `14 passed in 0.66s`.

```bash
./.venv/bin/python ML/baseline/audit_leaderboard_closure.py --input-prefix ML/reports/fractal0_rich_entry_quality_normalized --output-prefix ML/reports/leaderboard_closure_audit
```

Result: exit code `0`, `status=completed`,
`overall_decision=LEADERBOARD_CLOSURE_INCOMPLETE_RESEARCH_ONLY`.

```bash
./.venv/bin/python -m pytest tests/ -q
```

Result after audit fixes: `1417 passed, 52 warnings in 288.42s`.

Input artifacts used by `ML/reports/leaderboard_closure_audit.json`:

| input | path | sha256 | size_bytes |
|---|---|---|---:|
| `artifact_json` | `ML/reports/fractal0_rich_entry_quality_normalized.json` | `124859f3aba89a4fe2b4b663919740315d9218b8f2c748298a1dc013e00379cb` | 3480367 |
| `summary_csv` | `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv` | `89e825e2d54f24c6cb0167dab4a87fba7e415036f62006f6402a53166aa6dd81` | 349060 |
| `trades_csv` | `ML/reports/fractal0_rich_entry_quality_normalized_trades.csv` | `871413b9bab8758a78b9924abe27223c8bf2df037947b49d23c79d7424b22259` | 310798934 |
| `scores_csv` | `ML/reports/fractal0_rich_entry_quality_normalized_scores.csv` | `03a765a9134afd99add5c92dd58e018bcc0871156ebe650acb6d2f29f276f92d` | 491649054 |

## Results

- `status=completed`
- `verdict=research_only`
- `locked_test=not_opened`
- `leaderboard_rule_count=11`
- `overall_decision=LEADERBOARD_CLOSURE_INCOMPLETE_RESEARCH_ONLY`
- `stress_costs_status=NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS`
- `cost_model_disclosure_status=DISCLOSED_BASELINE,NOT_IN_SCOPE`
- `time_calendar_status=COMPUTED`
- `calendar_permutation_importance_status=NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS`
- `calendar_no_ml_baseline_status=NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS`
- `timezone_shift_status=NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS`
- `sequential_position_constraint_status=COMPUTED`
- `multi_seed_status=NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS`
- `calendar_n_trades_gate_status=LOW_N_DIAGNOSTIC_ONLY`
- `calendar_low_n_slice_count_lt_30=306`
- `calendar_low_n_slice_count_lt_10=92`
- classification decisions: `{'CLOSURE_INCOMPLETE': 11}`

Artifact row counts:

| artifact | rows |
|---|---:|
| `leaderboard_closure_audit_rules.csv` | 11 |
| `leaderboard_closure_audit_calendar.csv` | 1587 |
| `leaderboard_closure_audit_calendar_permutation_importance.csv` | 11 |
| `leaderboard_closure_audit_calendar_no_ml_baselines.csv` | 11 |
| `leaderboard_closure_audit_sequential_positions.csv` | 33 |
| `leaderboard_closure_audit_stress_cost.csv` | 44 |
| `leaderboard_closure_audit_timezone_shift.csv` | 44 |
| `leaderboard_closure_audit_multiseed.csv` | 55 |
| `leaderboard_closure_audit_cost_model_disclosure.csv` | 88 |
| `leaderboard_closure_audit_classification.csv` | 11 |

Sequential-position diagnostics computed all `33` policy rows. Dropped trades
range from `14` to `717` depending on rule and max-position policy. Current
saved trades contain `fill_time`, so all sequential rows have
`interval_basis=fill_time`.

Calendar slices are descriptive diagnostics, not a passed calendar-robustness
gate. The CSV now marks `n_trades_gate_status`; `306/1587` slices have fewer
than `30` trades and `92/1587` have fewer than `10` trades, so PF in those
slices must not be interpreted as standalone stability evidence.

## Conclusions

The closure does not justify shortlist/freeze/locked-test discussion. It does
reduce uncertainty in two places: time-calendar slices are computed, and
sequential-position constraints are computed from saved trade intervals. The
remaining blockers require producer-level or frozen rerun work.

## Limitations / Open Questions

- Stress-cost cannot be recomputed honestly from realized saved PnL only.
- Timezone shift requires frozen rescore of time features.
- Multi-seed needs persisted per-seed artifacts or a bounded rerun over the
  exact same 11 rule families.
- Calendar permutation importance and no-ML calendar baseline are not persisted
  in current artifacts.
- Provider drift and transfer are explicitly not in scope.

## Split Disclosure

Source split boundaries from
`docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`:

| split | min_time | max_time | planned_orders | filled_trades | fill_rate |
|---|---|---|---:|---:|---:|
| `train_core` | 2004-07-06 20:00:00 | 2019-06-20 14:00:00 | 44159 | 21343 | 0.4833 |
| `val_select` | 2019-06-20 16:00:00 | 2021-03-08 03:00:00 | 4731 | 2294 | 0.4849 |
| `val_eval` | 2021-03-08 05:00:00 | 2022-12-02 07:00:00 | 4732 | 2298 | 0.4856 |

Split roles:

- `train_core`: source training split for models and normalization.
- `val_select`: source of the fixed `score_cutoff_on_val_select` for each row.
- `val_eval`: only split used for computed closure diagnostics.
- `locked_test`: `not_opened`.

Rule-level sample sizes from `leaderboard_closure_audit_rules.csv`:

| original_rank | rule_id | val_select_n_trades | val_eval_n_trades |
|---:|---|---:|---:|
| 1 | `rank01_time_only_linear_target_entry_ev_regression_top30` | 625 | 660 |
| 2 | `rank02_time_only_linear_target_entry_ev_regression_top40` | 871 | 900 |
| 3 | `rank03_time_only_linear_target_entry_ev_regression_top50` | 1101 | 1109 |
| 4 | `rank04_time_only_linear_target_entry_good_0_5r_top40` | 839 | 840 |
| 5 | `rank05_time_only_linear_target_entry_avoid_sl_top30` | 587 | 570 |
| 6 | `rank06_time_only_linear_target_entry_good_0_5r_top50` | 1081 | 1099 |
| 7 | `rank07_movement_plus_time_linear_target_entry_good_0_5r_top40` | 841 | 979 |
| 8 | `rank08_movement_plus_time_linear_target_entry_good_0_5r_top30` | 596 | 760 |
| 9 | `rank09_time_only_hist_gradient_boosting_target_entry_good_0_5r_top50` | 1116 | 1107 |
| 10 | `rank10_movement_plus_time_linear_target_entry_ev_regression_top50` | 1077 | 1335 |
| 11 | `rank11_movement_plus_time_linear_target_entry_good_0_5r_top50` | 1068 | 1223 |

`locked_test=not_opened`; no holdout result was used for selection,
normalization choice, closure decision or winner selection.

## Next Step

Next allowed action: write an explicit producer-level stress-cost resimulation
plan, write a frozen timezone-rescore plan, write a bounded multi-seed rerun
plan for exactly the 11 fixed rule families, or close rich/fractal entry-quality
branch as time-heavy research-only rather than starting freeze work.

## Related Materials

- `ML/reports/leaderboard_closure_audit.json`
- `ML/reports/leaderboard_closure_audit_rules.csv`
- `ML/reports/leaderboard_closure_audit_stress_cost.csv`
- `ML/reports/leaderboard_closure_audit_cost_model_disclosure.csv`
- `ML/reports/leaderboard_closure_audit_calendar.csv`
- `ML/reports/leaderboard_closure_audit_calendar_permutation_importance.csv`
- `ML/reports/leaderboard_closure_audit_calendar_no_ml_baselines.csv`
- `ML/reports/leaderboard_closure_audit_timezone_shift.csv`
- `ML/reports/leaderboard_closure_audit_sequential_positions.csv`
- `ML/reports/leaderboard_closure_audit_multiseed.csv`
- `ML/reports/leaderboard_closure_audit_classification.csv`
- `docs/reports/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md`
- `docs/reports/2026-07-23-time-only-robustness-audit.md`
- `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`
