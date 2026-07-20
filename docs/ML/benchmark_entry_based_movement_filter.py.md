# benchmark_entry_based_movement_filter.py

`ML/baseline/benchmark_entry_based_movement_filter.py` строит простой pre-entry фильтр
`есть движение / нет движения` поверх уже готового source artifact
`ML/reports/entry_based_amplitude_movement.json`.

Цель runner-а: не искать направление и не считать торговую прибыль, а проверить,
можно ли заранее выбрать малую долю входов с существенно более сильным будущим
движением.

## Scope

Runner жёстко ограничен:

- source artifact: только `ML/reports/entry_based_amplitude_movement.json`;
- score family: только `time_plus_atr` и `simple_combined`;
- target family: только `entry_movement`;
- выбор winner: только по `val_select`;
- `val_eval`: только проверка одного заранее выбранного фильтра;
- `2026`: только disclosure;
- `locked_test`: не открывается;
- direction, BUY/SELL, PnL, PF, spread, stop-loss и take-profit запрещены.

## Входы

- `--source`: путь к amplitude artifact;
- `--output-prefix`: префикс для выходных артефактов.

По умолчанию CLI принимает только канонический `--source`
`ML/reports/entry_based_amplitude_movement.json`. Флаг
`--allow-noncanonical-source` существует только для fixture-тестов и не должен
использоваться для исследовательского прогона.

Из source artifact runner читает:

- `seed_aggregate` для bounded candidate list;
- `feature_audit_rows` и `selection_policy` для contract check;
- metadata, нужную для точного rerun разрешённых score family.

## Логика выбора

1. Проверяется source contract:
   - `locked_test = not_opened`;
   - есть `run_config_hash`;
   - для `time_plus_atr` и `simple_combined` metadata-audit проходит на
     `train`, `val_select`, `val_eval`, `low_n_disclosure`.
2. Из `seed_aggregate` берётся лучший `model_key` на каждый `(profile, horizon)`.
3. Для каждого кандидата проверяются только `top_fraction`:
   - `0.05`
   - `0.10`
   - `0.20`
   - `0.30`
4. Winner на `val_select` должен пройти gate:
   - `selected_n >= 200`;
   - `movement_lift >= 1.25`;
   - `selected_p80 > skipped_p80`.
5. Один winner проверяется на `val_eval`.

Итоговый verdict allowlist:

- `ABORT_CONTRACT_FAIL`
- `MOVEMENT_FILTER_REJECTED`
- `SIMPLE_MOVEMENT_FILTER_RESEARCH_ONLY`

## Выходы

- `ML/reports/entry_based_movement_filter.json`
- `ML/reports/entry_based_movement_filter_candidates.csv`
- `ML/reports/entry_based_movement_filter_yearly.csv`
- `ML/reports/entry_based_movement_filter_selected_rows.csv`

`selected_rows.csv` содержит только:

- выбранные строки `val_eval`;
- выбранные строки `2026 low_n_disclosure`.

## Фактический результат 2026-07-07

Выбранный filter:

- `profile = simple_combined`
- `model_key = extra_trees_small`
- `horizon = H3`
- `top_fraction = 0.05`

Ключевые числа:

- `val_select`: `selected_n=333`, `movement_lift=2.1528`
- `val_eval`: `selected_n=333`, `movement_lift=2.4806`,
  `yearly_lift_pass_rate=1.0`
- `2026 disclosure`: `selected_n=59`, `movement_lift=1.6292`

Корректная интерпретация: это только исследовательский movement-filter.
Он не является direction-моделью, не является торговым candidate и не даёт права
открывать `locked_test`.

## Запуск

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_movement_filter.py \
  --source ML/reports/entry_based_amplitude_movement.json \
  --output-prefix ML/reports/entry_based_movement_filter
```

## Тесты

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter.py -q
```

Покрытие тестов:

- source contract и `locked_test` guard;
- bounded candidate enumeration;
- `top_fraction` filter evaluation;
- winner selection и verdict logic;
- `2026`-only disclosure contract;
- CLI smoke на fixture artifact.
