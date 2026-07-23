# Context Handoff

**Дата:** 2026-07-23

## Текущее состояние

Ветка: `fractal0-entry-exit-grid`.

Текущий завершённый этап:

- отчёт: `docs/reports/2026-07-23-time-only-robustness-audit.md`
- план: `docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md`
- script: `ML/baseline/audit_time_only_robustness.py`
- module docs: `docs/ML/audit_time_only_robustness.py.md`

## Команда

```bash
./.venv/bin/python ML/baseline/audit_time_only_robustness.py \
  --input-prefix ML/reports/fractal0_rich_entry_quality_normalized \
  --output-prefix ML/reports/time_only_robustness_audit
```

## Итог

Decision: `REGIME_REFORMULATION_REQUIRED`.

Причины:

- `stricter_cutoff_sample_fragile`;
- `stress_costs_not_computable`.

Disclosure:

- `locked_test=not_opened`;
- `verdict=research_only`;
- `scope=validation_artifact_robustness_slice`;
- `multi_seed_status=NOT_RUN`;
- `provider_drift_status=NOT_RUN`;
- `transfer_status=NOT_RUN`;
- `sequential_position_constraint_status=NOT_RUN`.

## Fixed Rule

```text
S2_fractal0_buffer_0_5_entry_floor_2 /
E3_open_pullback_1_0atr /
M0_no_mask /
X2_ml_opposite_any_p0_50 /
profile=time_only /
model=linear /
target=target_entry_ev_regression /
filter=top30 /
score_cutoff_on_val_select=-0.026718184259660646
```

## Основные числа

- `val_eval n_trades=660`
- `PF=4.0268`
- `sequential_block_BS_p05=3.3068`
- `pf_without_best_year=3.5465`
- `effective_profit_years=1.9922`
- `best_year_share=0.5312`
- `BUY PF=5.1463`, `SELL PF=3.2554`
- worst entry-time quarter: Q3 by `signal_time`, `PF=3.5546`, `n_trades=205`
- worst entry-time month: month `10`, `PF=2.3309`, `n_trades=54`
- score shift: `val_select` fraction above cutoff `0.301628`, `val_eval`
  fraction above cutoff `0.309806`
- calendar no-ML baseline: `NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS`, saved
  artifacts содержат `top30,top40,top50`, но не unfiltered baseline.
- `timezone_shift_status=NOT_RUN`
- `calendar_permutation_importance_status=NOT_RUN`

Эти числа не являются торговым выводом: это validation artifact slice после
широкого validation search, `locked_test` не открыт.

## Артефакты

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

## Verification

```bash
./.venv/bin/python -m pytest tests/test_time_only_robustness_audit.py -q
./.venv/bin/python -m pytest tests/ -q
```

Результат полного прогона: `1390 passed, 52 warnings`.

## Next Step

Написать план `Regime filter reformulation` без открытия `locked_test`.
Сначала закрыть stress-cost resimulation, entry-time calendar slices и
timezone-shift disclosure.
