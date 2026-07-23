# audit_time_only_robustness.py

## Назначение

Validation-slice audit для fixed normalized `time_only` winner. Скрипт читает
saved artifacts, не обучает модель, не выбирает новое правило и не открывает
`locked_test`.

## Команда

```bash
./.venv/bin/python ML/baseline/audit_time_only_robustness.py \
  --input-prefix ML/reports/fractal0_rich_entry_quality_normalized \
  --output-prefix ML/reports/time_only_robustness_audit
```

## Входы

- `ML/reports/fractal0_rich_entry_quality_normalized.json`
- `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_trades.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_scores.csv`

## Выходы

- `ML/reports/time_only_robustness_audit.json`
- `ML/reports/time_only_robustness_audit_yearly.csv`
- `ML/reports/time_only_robustness_audit_quarterly.csv`
- `ML/reports/time_only_robustness_audit_side.csv`
- `ML/reports/time_only_robustness_audit_year_side.csv`
- `ML/reports/time_only_robustness_audit_score_shift.csv`
- `ML/reports/time_only_robustness_audit_stricter_cutoff.csv`
- `ML/reports/time_only_robustness_audit_topk_sensitivity.csv`
- `ML/reports/time_only_robustness_audit_calendar_no_ml_baselines.csv`
- `ML/reports/time_only_robustness_audit_calendar_slices.csv`
- `ML/reports/time_only_robustness_audit_spread_stress.csv`
- `ML/reports/time_only_robustness_audit_timezone_shift.csv`
- `ML/reports/time_only_robustness_audit_calendar_permutation_importance.csv`
- `ML/reports/time_only_robustness_audit_sequential.csv`

## Ограничения

- `locked_test=not_opened`.
- `scope=validation_artifact_robustness_slice`.
- `multi_seed_status=NOT_RUN`.
- `provider_drift_status=NOT_RUN`.
- `transfer_status=NOT_RUN`.
- `timezone_shift_status=NOT_RUN`.
- `calendar_permutation_importance_status=NOT_RUN`.
- Maximum verdict: `research_only`.
- При нарушении fixed rule contract скрипт пишет JSON со статусом `UNKNOWN`
  и завершает CLI с кодом `1`.
