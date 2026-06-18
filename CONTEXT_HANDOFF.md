# Context Handoff

Дата: 2026-06-18

## Текущий этап

Fractal Stop находится после Stage 5.0a и перед согласованием нового Stage 5.0 rerun.

Stage 5.0a Feature Preflight выполнен. Статус результата: **DIAGNOSTIC_ONLY**. Цель этапа была не обучать модель, а проверить final tensors, contracts профилей, нормализацию, clean-controls и coverage до повторного запуска Transformer.

## Что сделано

1. В `ML/baseline/benchmark_stage5_transformer_breach.py` добавлен режим:
   - `--feature-preflight-only`
2. Зафиксирована матрица Stage 5.0a из 13 профилей:
   - `time_only_clean`
   - `atr_only`
   - `time_plus_atr`
   - `all100_absolute_price_time`
   - `all100_no_price_time`
   - `all100_relative_price_no_time`
   - `all100_relative_price_time`
   - `corridor_5atr_relative_price_no_time`
   - `corridor_10atr_relative_price_no_time`
   - `corridor_15atr_relative_price_no_time`
   - `corridor_10atr_relative_price_time`
   - `nearest40_relative_price_no_time`
   - `nearest40_relative_price_time`
3. Добавлены profile contracts:
   - `selector`
   - `token_fields`
   - `row_fields`
   - `token_order`
   - `seq_len`
   - `padding_value`
   - `mask_semantics`
4. Исправлен контракт `nearest40_*`: `fractal0` теперь anchor и не входит в 40 соседей.
5. Добавлены тесты Stage 5.0 runner; свежий статус:
   - `64 passed`

## Где лежат результаты Stage 5.0a

- `docs/reports/2026-06-18-stage5_0a-feature-preflight.md`
- `ML/reports/stage5_0a_feature_preflight.json`
- `ML/reports/stage5_0a_feature_stats_normalized.csv`
- `ML/reports/stage5_0a_profile_summary.csv`

## Главные выводы Stage 5.0a

### 1. Технических блокеров нет

Не обнаружено:

- `NaN`
- `Inf`
- `PADDING_NOT_ZERO`
- нарушений profile contract
- ошибок формулы `price_coord_atr`

Значит, Stage 5.0 runner теперь строит корректные входы для повторного обучения.

### 2. Clean-controls теперь действительно чистые

- `time_only_clean` содержит только `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos`
- `time_plus_atr` отделён от него явно

Старый риск, где `time_only` фактически содержал ATR, снят.

### 3. Абсолютная цена остаётся только диагностическим контролем

`all100_absolute_price_time` получил disclosure-warning по holdout regime shift абсолютной цены. Это подтверждает исходную гипотезу: на длинном периоде 2004-2026 абсолютная цена кодирует эпоху и не должна быть основным представлением геометрии.

### 4. Лучшие кандидаты на rerun — relative-price и nearest40

Наиболее чистые профили по contract и preflight:

- `all100_no_price_time`
- `all100_relative_price_no_time`
- `all100_relative_price_time`
- `nearest40_relative_price_no_time`
- `nearest40_relative_price_time`

У них:

- корректный contract
- малые хвосты на train
- нет truncation-проблемы у `nearest40`

### 5. Corridor-профили не пустые, но слишком часто обрезаются

Главная проблема corridor сейчас — не бедность данных, а высокая truncation:

- `corridor_5atr_relative_price_no_time`: train truncation `0.519`
- `corridor_10atr_relative_price_no_time`: train truncation `0.880`
- `corridor_15atr_relative_price_no_time`: train truncation `0.967`

Это означает, что `corridor_10atr` и `corridor_15atr` в текущем виде не представляют весь коридор, а почти всегда режутся по `seq_len=40`.

## Что НЕ делать дальше

- Не запускать старый Stage 5.0 rerun вслепую по всем профилям.
- Не использовать `all100_absolute_price_time` как обучающий кандидат.
- Не включать `corridor_10atr_relative_price_*` и `corridor_15atr_relative_price_no_time` в rerun до отдельного решения по truncation.
- Не использовать holdout 2023-2026 для ручной подгонки профилей или scaler.

## Следующий шаг

Остановиться на human review и согласовать матрицу Stage 5.0 rerun.

Рекомендуемая матрица для повторного обучения:

1. `time_only_clean`
2. `atr_only`
3. `time_plus_atr`
4. `all100_no_price_time`
5. `all100_relative_price_no_time`
6. `all100_relative_price_time`
7. `nearest40_relative_price_no_time`
8. `nearest40_relative_price_time`

Допустимо оставить только как дополнительный diagnostic-кандидат:

9. `corridor_5atr_relative_price_no_time`

Не рекомендованы к rerun в текущем виде:

- `all100_absolute_price_time`
- `corridor_10atr_relative_price_no_time`
- `corridor_10atr_relative_price_time`
- `corridor_15atr_relative_price_no_time`

## Файлы

Код:

- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `ML/models/fractal_breach_transformer.py`
- `tests/test_stage5_transformer_breach.py`

Документы:

- `docs/reports/2026-06-17-stage5-transformer-breach.md`
- `docs/reports/2026-06-18-stage5_0a-feature-preflight.md`
- `docs/superpowers/plans/2026-06-18-stage5_0a-feature-preflight.md`

Артефакты:

- `ML/reports/stage5_0a_feature_preflight.json`
- `ML/reports/stage5_0a_feature_stats_normalized.csv`
- `ML/reports/stage5_0a_profile_summary.csv`

## Git

Ветка: `feature/fractal-stop-fav-spec`.

На момент обновления handoff есть незакоммиченные изменения кода и документации, связанные со Stage 5.0a.
