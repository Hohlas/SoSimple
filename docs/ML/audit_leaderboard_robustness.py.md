# audit_leaderboard_robustness.py

## Назначение

Validation-slice audit для 11 fixed audit input rows из normalized rich-entry leaderboard.
Скрипт читает saved artifacts, не обучает модель, не выбирает новый winner и
не открывает `locked_test`.

## Команда

```bash
./.venv/bin/python ML/baseline/audit_leaderboard_robustness.py \
  --input-prefix ML/reports/fractal0_rich_entry_quality_normalized \
  --output-prefix ML/reports/leaderboard_robustness_audit
```

## Входы

- `ML/reports/fractal0_rich_entry_quality_normalized.json`
- `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_trades.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_scores.csv`

## Выходы

- `ML/reports/leaderboard_robustness_audit.json`
- `ML/reports/leaderboard_robustness_audit_rules.csv`
- `ML/reports/leaderboard_robustness_audit_summary.csv`
- `ML/reports/leaderboard_robustness_audit_yearly.csv`
- `ML/reports/leaderboard_robustness_audit_quarterly.csv`
- `ML/reports/leaderboard_robustness_audit_side.csv`
- `ML/reports/leaderboard_robustness_audit_year_side.csv`
- `ML/reports/leaderboard_robustness_audit_score_shift.csv`
- `ML/reports/leaderboard_robustness_audit_stricter_cutoff.csv`
- `ML/reports/leaderboard_robustness_audit_topk_sensitivity.csv`
- `ML/reports/leaderboard_robustness_audit_calendar_slices.csv`
- `ML/reports/leaderboard_robustness_audit_missing_diagnostics.csv`
- `ML/reports/leaderboard_robustness_audit_classification.csv`

## Ограничения

- `locked_test=not_opened`.
- `scope=validation_artifact_leaderboard_robustness_slice`.
- `allowed_max_verdict=research_only`.
- `multi_seed_status=NOT_RUN`.
- `provider_drift_status=NOT_RUN`.
- `transfer_status=NOT_RUN`.
- Stress-cost resimulation, timezone-shift rescore and model-level calendar
  permutation importance are not computed from saved filtered artifacts unless
  a later implementation adds an explicitly frozen resimulation/rescore path.
- The script preserves `original_rank` and never selects a new winner.

## Follow-up Closure

The follow-up closure script is `ML/baseline/audit_leaderboard_closure.py`.
It reuses the same 11 fixed leaderboard rows and adds
cost/calendar/sequential/multi-seed disclosure under
`scope=validation_artifact_leaderboard_cost_calendar_sequential_multiseed_closure`.
