# fractal0_fixed11_internal_closure_rerun.py

## Назначение

Bounded internal closure rerun для ровно 11 fixed normalized leaderboard rule families.
Модуль считает producer-level stress-cost, frozen timezone/calendar diagnostics
и bounded multi-seed diagnostics без открытия `locked_test` и без выбора нового winner.

## Command

```bash
./.venv/bin/python ML/baseline/fractal0_fixed11_internal_closure_rerun.py \
  --source-prefix ML/reports/fractal0_rich_entry_quality_normalized \
  --source-rules-csv ML/reports/leaderboard_closure_audit_rules.csv \
  --output-prefix ML/reports/fractal0_fixed11_internal_closure_rerun \
  --run-groups stress_cost,timezone_calendar,multiseed \
  --threads 24
```

## Scope

- `locked_test=not_opened`
- `provider_drift_status=NOT_IN_SCOPE`
- `transfer_status=NOT_IN_SCOPE`
- `allowed_max_verdict=research_only`
- fixed 11 `LEADERBOARD_RULES`
- saved `score_cutoff_on_val_select` only
- no new profiles, models, targets, filters, instruments or selection metrics

## Outputs

- `ML/reports/fractal0_fixed11_internal_closure_rerun.json`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_run_matrix.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_stress_cost.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_timezone_rescore.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_canonical_feature_state_manifest.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_calendar_permutation_importance.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_calendar_no_ml_baselines.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_multiseed.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_multiseed_aggregate.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_classification.csv`

## Результат 2026-07-23

Full run завершился с `status=completed`, `overall_decision=FIXED11_INTERNAL_CLOSURE_RISK_FLAGS_RESEARCH_ONLY`.
Все primary diagnostics имеют `COMPUTED` строки, но risk flags остаются:
stress-cost `12/33`, calendar permutation `4/11`, no-ML calendar baseline `11/11`.
Timezone rescore и multi-seed aggregate прошли без risk flags.

Интерпретация остаётся исследовательской: это не trading conclusion, не permission
to open `locked_test`, не provider drift и не transfer check.
