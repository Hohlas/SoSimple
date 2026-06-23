# Context Handoff

Дата: 2026-06-23

## Текущий этап

Stage 5.0e завершён. Вердикт: **DIAGNOSTIC_ONLY**.

Состояние ветки `H6_off05 stop broken` не изменилось: она остаётся закрытой после решения Stage 5.0d.  
Статус проекта: **DIAGNOSTIC_ONLY**.

## Что сделано

### Stage 5.0e (2026-06-23) — посмертная проверка малого Transformer
- Новый CLI `--stage5-0e-small-transformer-check`
- Зафиксированы:
  - 1 цель: `sell_stop_broken_H6_off05_flag`
  - 1 профиль: `all100_relative_price_time`
  - 2 конфигурации Transformer: `current` и `small_regularized`
  - 3 seed: `[42, 77, 123]`
- В `train_transformer` добавлена поддержка `model_config`
- История обучения расширена полями `best_epoch`, `last_val_auc`, `overfit_drop_after_best`
- Структурированный артефакт: `ML/reports/stage5_0e_small_transformer_check.json`
- Отчёт: `docs/reports/2026-06-23-stage5_0e-small-transformer-check.md`
- 795 tests passed

## Главный результат

- `overfit_hypothesis_supported = yes`
- `transformer_reopens_h6_off05 = no`

Ключевые числа:

- XGBoost на тех же признаках: `val_auc=0.6742`, `val_lift_30=0.5260`
- Transformer `current`: median `val_auc=0.6685`, median `lift_30=0.5260`, median `overfit_drop_after_best=0.0170`
- Transformer `small_regularized`: median `val_auc=0.6657`, median `lift_30=0.5663`, median `overfit_drop_after_best=0.0009`

Вывод:

1. Меньшая модель почти убирает просадку `val_auc` после лучшей эпохи.
2. Но даже после этого Transformer не догоняет XGBoost на тех же признаках.
3. Значит, переобучение было только частью проблемы, а не её главным объяснением.
4. Решение 5.0d не меняется: `H6_off05 stop broken` остаётся закрытым.

## Где мы сейчас

Ветка `H6_off05` закрыта для дальнейшей настройки модели.

Правильное направление дальше:
- менять цель;
- или менять признаки;
- или разбирать, почему табличное представление лучше последовательной модели на тех же данных.

Неправильное направление дальше:
- продолжать крутить Transformer на том же `H6_off05` и том же профиле.

## Ключевые файлы

Код:
- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `tests/test_stage5_transformer_breach.py`

Отчёты:
- `docs/reports/2026-06-23-stage5_0e-small-transformer-check.md`
- `docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md`
- `docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md`

Артефакты:
- `ML/reports/stage5_0e_small_transformer_check.json`
- `ML/reports/stage5_0d_diagnostic_screening.json`

## Открытые вопросы

- Почему XGBoost извлекает умеренный сигнал из flattened-представления, а Transformer на тех же данных — нет.
- Есть ли более перспективная новая цель внутри Fractal Stop family, чем `stop broken`.
- Какие новые признаки действительно добавляют информацию сверх `base_raw_plus_time`.
