# benchmark_entry_based_amplitude_movement.py

`ML/baseline/benchmark_entry_based_amplitude_movement.py` проверяет диагностическую постановку entry-based amplitude / movement-regime.

Цель runner-а: понять, есть ли устойчивый сигнал будущей величины движения после входа, и можно ли объяснить его простыми baseline-признаками.

## Target

Основной target:

```text
entry_movement_H = max(entry_up_H, entry_dn_H)
```

Горизонты:

- `H3`
- `H6`
- `H12`
- `H24`

Дополнительно строятся train-only quantile-флаги:

- `movement_flag_q80_H`
- `movement_flag_q90_H`
- `movement_flag_q95_H`

## Профили признаков

Simple baseline:

- `atr_only`
- `time_only_clean`
- `time_plus_atr`
- `distance_to_level_pre_entry_only`
- `fractal_density_only`
- `simple_combined`

Diagnostic-only:

- `distance_to_entry_open_post_entry_diagnostic_only`

Он не участвует в выборе verdict, потому что использует post-entry цену.

Wide profiles:

- `nearest_k60_tabular`
- `nearest_k80_tabular`
- `nearest_k60_no_price_coord_tabular`
- `nearest_k80_no_price_coord_tabular`
- `nearest_k60_sequence_flat`
- `nearest_k80_sequence_flat`
- `nearest_k60_no_time_sequence_flat`
- `nearest_k60_no_price_coord_sequence_flat`

## Выходы

Основные артефакты:

- `ML/reports/entry_based_amplitude_movement.json`
- `ML/reports/entry_based_amplitude_movement_metrics.csv`
- `ML/reports/entry_based_amplitude_movement_rows.csv`
- `ML/reports/entry_based_amplitude_movement_seed_aggregate.csv`
- `ML/reports/entry_based_amplitude_movement_quantiles.csv`
- `ML/reports/entry_based_amplitude_movement_yearly.csv`
- `ML/reports/entry_based_amplitude_movement_target_distribution.csv`
- `ML/reports/entry_based_amplitude_movement_feature_audit.csv`

`entry_based_amplitude_movement_yearly.csv` сохраняет идентификатор запуска:
`profile`, `model_key`, `seed`, `target_family`, `split`, `year`, `horizon`,
`spearman`, `top10_lift`, `top_n`, `rest_n`.

## Контракты

- `locked_test` не используется.
- `low_n_disclosure=2026` не влияет на verdict.
- Quantile thresholds fit only on train.
- Input normalization fit only on train.
- Post-entry diagnostic profiles имеют `selection_eligible=false`.
- Wide-search результат остаётся `DIAGNOSTIC_ONLY`.
- Freeze-like verdict запрещён.

## Запуск

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_amplitude_movement.py \
  --entry-based-amplitude-movement \
  --no-resume \
  --threads 24
```

Resume включён по умолчанию:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_amplitude_movement.py \
  --entry-based-amplitude-movement \
  --threads 24
```

## Тесты

```bash
./.venv/bin/python -m pytest tests/test_entry_based_amplitude_movement.py -q
```

Покрытие тестов:

- target formula и train-only quantile thresholds;
- запрет target/leakage колонок во входах;
- metadata профилей и selection eligibility;
- skip/resume/progress контракты;
- verdict allowlist;
- feature audit и target contract;
- yearly check и идентификаторы запуска в yearly artifact.
