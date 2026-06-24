# Stage 5.0e — посмертная проверка переобучения Transformer на H6_off05

> **Дата**: 2026-06-23
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: Проверить, уменьшает ли малая и сильнее ограниченная версия Transformer признаки переобучения на `sell_stop_broken_H6_off05_flag`, не открывая заново уже закрытую постановку
> **Уровень этапа**: проверка после провала
> **План**: `docs/superpowers/plans/2026-06-23-stage5_0e-small-transformer-overfit-check.md`

## Контекст

Stage 5.0d зафиксировал, что постановка `H6_off05 stop broken` на текущих профилях исследовательски исчерпана. При этом в 5.0c был виден локальный рисунок переобучения: `val_auc` сначала рос, затем падал при продолжающемся снижении train loss. Stage 5.0e не пытается открыть новую ветку. Его задача уже: проверить, объясняет ли уменьшение модели часть провала Transformer.

## Что сделано

- Добавлен отдельный режим `--stage5-0e-small-transformer-check`.
- Зафиксирован один профиль: `all100_relative_price_time`.
- Зафиксирована одна цель: `sell_stop_broken_H6_off05_flag`.
- Сравнены две конфигурации Transformer:
  - `current`: d_model=64, layers=2, heads=4, ff=128, dropout=0.15, weight_decay=1e-4, patience=8;
  - `small_regularized`: d_model=32, layers=1, heads=2, ff=64, dropout=0.35, weight_decay=1e-3, patience=3.
- Для каждой конфигурации выполнено 3 seed: `[42, 77, 123]`.
- XGBoost на тех же признаках обучен как главное сравнение.
- Holdout 2023-2026 раскрыт, но не использован в решении.

## Контекст перебора

Объём перебора заранее зафиксирован и мал: 1 профиль × 1 цель × 2 конфигурации × 3 seed = 6 прогонов Transformer, плюс 1 XGBoost на тех же признаках.
Коррекция множественного перебора не применялась, потому что этап имеет статус `DIAGNOSTIC_ONLY` и не создаёт кандидата. Решение делится на два независимых поля:

- `overfit_hypothesis_supported`
- `transformer_reopens_h6_off05`

Даже сильный результат не открывает следующий этап автоматически.

## Изменённые файлы

- `ML/baseline/benchmark_stage5_transformer_breach.py` — константы 5.0e, `model_config` в `train_transformer`, расширенная история обучения, `run_stage5_0e_small_transformer_check`, функция решения, CLI.
- `tests/test_stage5_transformer_breach.py` — тесты констант, `model_config`, runner и CLI.
- `ML/reports/stage5_0e_small_transformer_check.json` — structured artifact.
- `docs/reports/2026-06-23-stage5_0e-small-transformer-check.md` — канонический отчёт.
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`

## Проверка

- `./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k 'stage5_0e or train_transformer' -q` — 4 passed.
- `./.venv/bin/python -m pytest tests/ -q` — 795 passed, 0 failed.
- `./.venv/bin/python ML/baseline/benchmark_stage5_transformer_breach.py --stage5-0e-small-transformer-check` — JSON записан.

## Условия

- Цель: `sell_stop_broken_H6_off05_flag`
- Профиль: `all100_relative_price_time`
- Преобразование: `asinh`
- Seeds: `[42, 77, 123]`
- Split:
  - train: `year <= 2020`
  - `val_stop`: 2021-2022
  - holdout: 2023-2026
- Использование holdout: только раскрытие
- normalization_config:
  - `StandardScaler`
  - token scaler fit only on valid train positions (`mask=True`)
  - row scaler fit only on train rows
  - padding kept at `0.0`, не участвует в fit
- normalized_feature_distribution_audit:
  - `current`: `OK`, 0 flags на каждом seed
  - `small_regularized`: `OK`, 0 flags на каждом seed
- scale_contract: `PASS`

## Результаты

### XGBoost на тех же признаках

| Модель | val_auc | val_lift_30 | holdout_auc | holdout_lift_30 |
|---|---:|---:|---:|---:|
| XGBoost на тех же признаках | 0.6742 | 0.5260 | 0.6569 | 0.5906 |

### Сводка Transformer по конфигурациям

| Config | median val_auc | median val_lift_30 | seed spread val_auc | median overfit_drop_after_best | median holdout_auc | per-seed pass vs XGBoost |
|---|---:|---:|---:|---:|---:|---:|
| current | 0.6685 | 0.5260 | 0.0078 | 0.0170 | 0.6373 | 0 / 3 |
| small_regularized | 0.6657 | 0.5663 | 0.0022 | 0.0009 | 0.6387 | 0 / 3 |

### Прогоны Transformer по seed

| Config | Seed | val_auc | val_lift_30 | holdout_auc | overfit_drop_after_best | best_epoch |
|---|---:|---:|---:|---:|---:|---:|
| current | 42 | 0.6719 | 0.5044 | 0.6373 | 0.0170 | 11 |
| current | 77 | 0.6685 | 0.5260 | 0.6393 | 0.0359 | 6 |
| current | 123 | 0.6641 | 0.5601 | 0.6362 | 0.0154 | 5 |
| small_regularized | 42 | 0.6657 | 0.5725 | 0.6458 | 0.0006 | 18 |
| small_regularized | 77 | 0.6673 | 0.5663 | 0.6332 | 0.0009 | 11 |
| small_regularized | 123 | 0.6651 | 0.5570 | 0.6387 | 0.0016 | 17 |

### Решение

- `overfit_hypothesis_supported = yes`
- `transformer_reopens_h6_off05 = no`

Основание:

1. `small_regularized` резко уменьшил `median overfit_drop_after_best`: `0.0009` против `0.0170`.
2. Потеря по `median val_auc` против `current` мала: `0.6657` против `0.6685`, то есть хуже только на `0.0028`.
3. Разброс по seed у `small_regularized` мал: `0.0022`.
4. Но обе Transformer-конфигурации остаются хуже XGBoost на тех же признаках по `median val_auc`.
5. `small_regularized` ещё и хуже XGBoost по `median val_lift_30`: `0.5663` против `0.5260` (меньше лучше).
6. Ни один seed не прошёл сравнение с XGBoost на тех же признаках одновременно по `val_auc` и `val_lift_30`.

## Выводы

1. **Гипотеза о переобучении локально подтверждена.** Уменьшение модели и усиление ограничений почти убрало просадку `val_auc` после лучшей эпохи.
2. **Но это не решает главную проблему.** Даже после снятия признаков переобучения Transformer не догоняет XGBoost на тех же признаках.
3. **Текущая лучшая по качеству конфигурация всё ещё `current`, а не `small_regularized`.** По `median val_auc` лучшая конфигурация — `current` (`0.6685` против `0.6657`).
4. **Постановка H6_off05 остаётся закрытой.** Stage 5.0e не дал основания отменить решение 5.0d.
5. **Слабость Transformer здесь не сводится только к слишком большой ёмкости.** Переобучение было частью проблемы, но не её главным объяснением.

## Ограничения и открытые вопросы

- Проверка выполнена только на одном профиле и одной цели, как и было заранее заморожено.
- Holdout не участвовал в решении; ухудшение или улучшение на holdout не может менять вердикт.
- Проверялись только две заранее зафиксированные конфигурации, без дальнейшего поиска.
- `small_regularized` уменьшает переобучение, но ухудшает `lift_30`; причина этого не разобрана отдельно.
- Этап не отвечает на вопрос, почему XGBoost лучше извлекает сигнал из тех же признаков.
- Проверка после провала выполнена; новый исследовательский цикл по H6_off05 не разрешён этим отчётом.

## Раскрытие split

- `val_stop` 2021-2022 — единственный split, который использовался для решения.
- `holdout` 2023-2026 — только раскрытие.
- `val_select` и `val_eval` отдельно не использовались.
- Этап не претендует на frozen candidate и не нарушает решение 5.0d.

## Следующий шаг

Не продолжать настройку Transformer на `H6_off05 stop broken`. Следующий осмысленный шаг — смена цели или смена признаков. Отдельно полезно разобрать, почему XGBoost извлекает умеренный сигнал из плоского представления, а последовательная модель на тех же данных нет.

## Связанные материалы

- `ML/reports/stage5_0e_small_transformer_check.json`
- `docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md`
- `docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md`
- `docs/superpowers/plans/2026-06-23-stage5_0e-small-transformer-overfit-check.md`
