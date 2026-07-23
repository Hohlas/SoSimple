# Fractal0 Fixed-11 Internal Closure Rerun

> **Дата**: 2026-07-23
> **Статус**: Completed
> **Вердикт**: research_only
> **Цель**: довести internal closure fixed normalized leaderboard до producer-level stress-cost, frozen timezone/calendar diagnostics и bounded multi-seed rerun для ровно 11 rule families без открытия `locked_test`.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-23-fractal0-fixed11-internal-closure-rerun.md`

## Context

Предыдущий closure audit мог только раскрыть часть рисков из saved artifacts. Этот rerun пересчитал нужные проверки на уровне producer-runner для тех же 11 fixed rows из `ML.baseline.audit_leaderboard_robustness.LEADERBOARD_RULES`.

Fixed execution contract:
`S2_fractal0_buffer_0_5_entry_floor_2 / E3_open_pullback_1_0atr / M0_no_mask / X2_ml_opposite_any_p0_50 / canonical_spread=0.2 / entry_filter_score_col=rich_entry_score`.

## Уровень этапа

```text
lifecycle_status=research_only
origin_bias=normalized rich-entry validation leaderboard selected after broad search
research_priority=medium; close internal robustness blockers before any provider/transfer/locked-test discussion
current_search_budget=no new winner search; exact 11 fixed rule families; stress_spreads=3; timezone_shifts=5; multiseed_seeds=5; diagnostic calendar baseline families=3
cumulative_search_budget=inherited from normalized rich-entry search, 243 ranked configs plus diagnostic controls and this fixed internal closure rerun
next_probe_freeze=not created in this stage
allowed_max_verdict=research_only
locked_test=not_opened
provider_drift_status=NOT_IN_SCOPE
transfer_status=NOT_IN_SCOPE
forbidden_interpretations=candidate/tradable/live_ready/production/permission_to_open_locked_test/new_winner
not_trading_evidence_reason=validation artifact rerun on broad-search descendants; no locked_test, no provider drift, no transfer, no MT4 parity
```

## What Was Done

- Added `ML/baseline/fractal0_fixed11_internal_closure_rerun.py`.
- Extended `ML/baseline/benchmark_fractal0_entry_quality_filter.py` for fixed manifest, saved cutoffs, seed, spread and timezone shift.
- Ran full fixed rerun with `--threads 24`.
- Produced stress-cost, timezone rescore, calendar permutation, no-ML calendar baseline, multi-seed and classification artifacts.
- Preserved `original_rank`; no new winner was selected.

## Multiple Testing Context

Current budget is bounded and diagnostic: exactly 11 fixed rule families, 3 stress spreads, 5 timezone shifts, 5 seeds and 3 calendar baseline families. No new profiles, models, targets, filters, cutoffs, instruments or selection metrics were added.

Cumulative budget is inherited from the normalized rich-entry search: 243 ranked configs plus diagnostic controls and this fixed internal closure rerun. Because the source rules descend from broad validation search, positive PF/PnL remains `research_only`.

## Changed Files

- `ML/baseline/fractal0_fixed11_internal_closure_rerun.py`
- `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- `tests/test_fractal0_fixed11_internal_closure_rerun.py`
- `tests/test_fractal0_entry_quality_filter.py`
- `docs/ML/fractal0_fixed11_internal_closure_rerun.py.md`
- `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
- `docs/reports/2026-07-23-fractal0-fixed11-internal-closure-rerun.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/roadmap.md`
- `MODULE_INDEX.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

## Verification

Commands:

```bash
./.venv/bin/python ML/baseline/fractal0_fixed11_internal_closure_rerun.py \
  --source-prefix ML/reports/fractal0_rich_entry_quality_normalized \
  --source-rules-csv ML/reports/leaderboard_closure_audit_rules.csv \
  --output-prefix ML/reports/fractal0_fixed11_internal_closure_rerun \
  --run-groups stress_cost,timezone_calendar,multiseed \
  --threads 24

./.venv/bin/python -m pytest tests/test_fractal0_fixed11_internal_closure_rerun.py -q
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py -q
./.venv/bin/python -m pytest tests/ -q
```

Observed after final docs sync: targeted fixed11/rich-entry tests `70 passed`; full suite `1442 passed, 52 warnings`. The test result is a console observation from this run; no separate pytest log artifact was written. Re-run the commands above to verify.

Input artifact hashes from primary JSON:

| Input | Path | SHA256 | Size bytes |
|---|---|---|---:|
| source rules CSV | `ML/reports/leaderboard_closure_audit_rules.csv` | `d98c1194d954e20aaa7d7a132547a9ac52caf1c7073f5ce98997cda1ee3b808c` | 2267 |
| source normalized JSON | `ML/reports/fractal0_rich_entry_quality_normalized.json` | `124859f3aba89a4fe2b4b663919740315d9218b8f2c748298a1dc013e00379cb` | 3480367 |
| source movement freeze JSON | recorded in source JSON | `52c3340150dde391e94db3d9023150275d94777ac76da6647505b4741155abaa` | - |
| source H1 OHLC | recorded in source JSON | `4bf7a23ab79f41824713fa881078d06fb84fd7c484b2840c3cdec0bfdfda5aff` | - |
| source train_core | recorded in source JSON | `5cc0c1180d96966ac08c4832947be6b2770f1d14b0b572a4f63f0f28b3e49b62` | - |
| source validation | recorded in source JSON | `f31d54f8e47b29675cbd21f78f457ee4b135936480698baac54180c5a83f14fd` | - |
| source movement freeze scores | recorded in source JSON | `385dc1c125e9b2ba9ec9a278e4a56f60fe3f2c10a66a425ff92fd5b9cb105eae` | - |
| source execution OHLC | recorded in source JSON | `504666ce286b27f3ae61679d5e722a629a0d8662d93a428c4f8dd5e6b2ce4f60` | - |
| source stop-grid artifact | recorded in source JSON | `20e6931a1b47d7d2fe3c5455e698d8bb3160bd570a418a35a0a0ea083358e0b6` | - |

## Results

Primary JSON: `ML/reports/fractal0_fixed11_internal_closure_rerun.json`.

```text
status=completed
verdict=research_only
overall_decision=FIXED11_INTERNAL_CLOSURE_RISK_FLAGS_RESEARCH_ONLY
locked_test=not_opened
provider_drift_status=NOT_IN_SCOPE
transfer_status=NOT_IN_SCOPE
leaderboard_rule_count=11
threads_requested=24
stress_cost_status=COMPUTED
timezone_rescore_status=COMPUTED
calendar_permutation_status=COMPUTED
calendar_no_ml_baseline_status=COMPUTED
multiseed_status=COMPUTED
classification_decisions={'INTERNAL_CLOSURE_RISK_FLAGGED': 11}
```

Row counts:

| Artifact | Rows | Risk flags |
|---|---:|---:|
| stress-cost | 33 | 12 |
| timezone rescore | 55 | 0 |
| calendar permutation | 11 | 4 |
| no-ML calendar baseline | 11 | 11 |
| multi-seed aggregate | 11 | 0 |
| classification | 11 | 11 |

Stress-cost by spread:

| Spread | Rows | Risk flags | min PF | min BS_p05 | min trades |
|---:|---:|---:|---:|---:|---:|
| 0.2 | 11 | 0 | 3.2669 | 2.8338 | 570 |
| 0.4 | 11 | 5 | 2.7223 | 2.0813 | 93 |
| 0.8 | 11 | 7 | 1.3202 | 0.6557 | 0 |

Timezone rescore had no risk flags. Minimum PF across shifts was `2.7968`, minimum `BS_p05=2.3275`, minimum trades `378`.

Calendar permutation flagged 4 rules: ranks 1, 2, 4 and 5. `pf_drop_ratio` range was `0.2011..0.3727`, median `0.2848`.

No-ML calendar baseline flagged all 11 rules. Selected family was `hour` for all rows; `baseline_to_ml_pf_ratio` range was `0.8588..1.0698`, median `0.9780`.

Multi-seed aggregate had no risk flags: every rule had `computed_seed_count=5` and `passing_seed_count=5`.

## Calendar Diagnostic Protocol

No-ML baseline:

- families: `hour`, `weekday`, `hour_weekday`;
- `selection_split=val_select`;
- `evaluation_split=val_eval`;
- bucket gates on `val_select`: `n_trades >= 30`, `PF >= 1.20`, `BS_p05 >= 1.00`;
- tie-breaker: highest `BS_p05_val_select`, then higher `PF_val_select`, then larger `n_trades_val_select`;
- `uses_rich_entry_score=False`;
- selected family in this run: `hour` for all 11 rows.

Calendar permutation:

- `permutation_repeats=50`;
- grouping: `year_side`;
- small groups with fewer than `5` rows are skipped;
- deterministic seed formula: `1000 + original_rank + repeat_index`;
- row count, index alignment and non-calendar feature preservation checks are all `True` in the artifact.

## Conclusions

Internal closure is computed but risk-flagged. The strongest blocker is calendar dominance: a simple no-ML hour baseline reaches at least 85.9% of ML PF for every fixed rule and exceeds ML PF for several movement-plus-time rows. Stress-cost also weakens materially under 2x/4x spread through low trade counts and low lower-bound metrics.

This closes the rich/fractal entry-quality branch as time-heavy `research_only` evidence unless a narrower regime-filter reformulation plan is written. It does not justify provider drift, transfer or `locked_test`.

## Limitations / Open Questions

- No `locked_test`.
- No provider drift.
- No transfer check.
- No MT4 parity.
- Calendar diagnostics are validation-only diagnostics after broad source search.
- Stress-cost changes spread, which changes fill/no-fill and labels; stress rows are internal robustness evidence, not proof of the same frozen rule for `locked_test`.

## Split Disclosure

- `train_core` trains models and scalers.
- `val_select` supplies saved `score_cutoff_on_val_select`.
- `val_eval` is the only evaluation split used here.
- `locked_test` remains closed.

Split boundaries and sample sizes from `ML/reports/fractal0_rich_entry_quality_normalized_split_manifest.csv`:

| Split | Min time | Max time | Raw rows | Planned orders | Filled trades | Fill rate |
|---|---|---|---:|---:|---:|---:|
| train_core | 2004-07-06 20:00:00 | 2019-06-20 14:00:00 | 44159 | 44159 | 21343 | 0.483322 |
| val_select | 2019-06-20 16:00:00 | 2021-03-08 03:00:00 | 4731 | 4731 | 2294 | 0.484887 |
| val_eval | 2021-03-08 05:00:00 | 2022-12-02 07:00:00 | 4732 | 4732 | 2298 | 0.485630 |

Rule-level validation sample sizes from `ML/reports/leaderboard_closure_audit_rules.csv`:

| Rank | Rule | val_select trades | val_eval trades | val_eval PF | val_eval BS_p05 |
|---:|---|---:|---:|---:|---:|
| 1 | `rank01_time_only_linear_target_entry_ev_regression_top30` | 625 | 660 | 4.0268 | 3.3955 |
| 2 | `rank02_time_only_linear_target_entry_ev_regression_top40` | 871 | 900 | 3.7417 | 3.1972 |
| 3 | `rank03_time_only_linear_target_entry_ev_regression_top50` | 1101 | 1109 | 3.5710 | 3.1720 |
| 4 | `rank04_time_only_linear_target_entry_good_0_5r_top40` | 839 | 840 | 3.7279 | 3.1386 |
| 5 | `rank05_time_only_linear_target_entry_avoid_sl_top30` | 587 | 570 | 3.7630 | 3.1078 |
| 6 | `rank06_time_only_linear_target_entry_good_0_5r_top50` | 1081 | 1099 | 3.5826 | 3.1054 |
| 7 | `rank07_movement_plus_time_linear_target_entry_good_0_5r_top40` | 841 | 979 | 3.3121 | 2.8836 |
| 8 | `rank08_movement_plus_time_linear_target_entry_good_0_5r_top30` | 596 | 760 | 3.4238 | 2.8551 |
| 9 | `rank09_time_only_hist_gradient_boosting_target_entry_good_0_5r_top50` | 1116 | 1107 | 3.2926 | 2.8409 |
| 10 | `rank10_movement_plus_time_linear_target_entry_ev_regression_top50` | 1077 | 1335 | 3.2778 | 2.8343 |
| 11 | `rank11_movement_plus_time_linear_target_entry_good_0_5r_top50` | 1068 | 1223 | 3.2669 | 2.8338 |

Sample-size gates used in this fixed closure:

- stress-cost and timezone rows: risk flag if `n_trades < 300`;
- multi-seed row pass: `n_trades >= 300`, `PF >= 1.20`, `BS_p05 >= 1.00`;
- no-ML calendar bucket eligibility on `val_select`: `n_trades >= 30`;
- `locked_test` sample size is intentionally not reported because `locked_test` was not opened.

OHLC/execution disclosure:

```text
ohlc_price_convention=bid_ohlc_with_spread_adjusted_sell_exit_bars
spread_definition=full_bid_ask_spread_in_price_units
entry_price_rule=buy_fill_when_low_plus_spread_le_limit_and_sell_fill_when_high_ge_limit; entry_effective_price_equals_limit_price
sl_trigger_rule=protective_stop_checked_on_effective_exit_bars; same_bar_tp_sl_without_execution_ohlc_resolves_sl_first
tp_rule=fixed_r_take_profit_from_entry_effective_price_plus_or_minus_tp_r_times_r_value
timeout_pnl_rule=time_exit_marks_to_close_price_of_hold_limit_bar_on_effective_exit_bars
```

## Next Step

Close rich/fractal entry-quality branch as time-heavy research-only, then write a narrower regime-filter reformulation plan. Do not open `locked_test`.

## Related Materials

- `ML/reports/fractal0_fixed11_internal_closure_rerun.json`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_classification.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_stress_cost.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_timezone_rescore.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_calendar_permutation_importance.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_calendar_no_ml_baselines.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_multiseed_aggregate.csv`
- `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`
- `docs/reports/2026-07-23-fractal0-leaderboard-cost-calendar-sequential-multiseed-closure.md`
