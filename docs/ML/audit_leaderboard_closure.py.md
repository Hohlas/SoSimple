# audit_leaderboard_closure.py

## Назначение

Closure/disclosure audit для 11 fixed normalized rich-entry leaderboard rows.
Скрипт переиспользует `LEADERBOARD_RULES` из
`ML/baseline/audit_leaderboard_robustness.py`, проверяет сохранённые
artifacts и пишет structured JSON/CSV результаты без нового поиска.

## Команда

```bash
./.venv/bin/python ML/baseline/audit_leaderboard_closure.py \
  --input-prefix ML/reports/fractal0_rich_entry_quality_normalized \
  --output-prefix ML/reports/leaderboard_closure_audit
```

## Входы

- `ML/reports/fractal0_rich_entry_quality_normalized.json`
- `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_trades.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_scores.csv`

## Выходы

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

## Ограничения

`locked_test` remains closed. Provider drift and transfer are not in scope.
The script checks all 11 fixed leaderboard rows and never performs winner selection.
Maximum verdict is `research_only`.

- `locked_test=not_opened`
- `provider_drift_status=NOT_IN_SCOPE`
- `transfer_status=NOT_IN_SCOPE`
- `scope=validation_artifact_leaderboard_cost_calendar_sequential_multiseed_closure`
- `input_artifacts` in JSON records path, `sha256` and size for normalized
  JSON, summary, trades and scores inputs.
- Calendar CSV records `n_trades_gate_status` and `low_n_calendar_slice`;
  small slices are descriptive diagnostics, not a robustness PASS.
- Stress-cost, timezone shift and multi-seed are marked
  `NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS` when the saved artifacts do not contain
  an honest resimulation/rescore/per-seed path.
- Sequential-position diagnostics use real position interval
  `[fill_time, exit_time]`. The sequential CSV records `interval_basis`; if
  `fill_time` is absent in old saved trades, status becomes
  `COMPUTED_WITH_SIGNAL_TIME_FALLBACK`.
