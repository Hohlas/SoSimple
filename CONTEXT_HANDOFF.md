# Context Handoff

Дата: 2026-06-18

## Текущий этап

Fractal Stop находится после Stage 5.0a feature preflight и после corridor full addendum. Обучение Transformer по этому addendum не запускалось.

Статус: **DIAGNOSTIC_ONLY**.

## Что сделано

1. В `ML/baseline/benchmark_stage5_transformer_breach.py` режим `--feature-preflight-only` расширен:
   - считает raw corridor coverage до cap;
   - сохраняет честную truncation-метрику;
   - строит 4 новых full-corridor профиля.
2. Builder теперь возвращает `selection_meta`:
   - `candidate_count_before_cap`
   - `selected_count_after_cap`
   - `is_truncated`
3. Добавлены новые профили:
   - `corridor_5atr_relative_price_no_time_full`
   - `corridor_10atr_relative_price_no_time_full`
   - `corridor_5atr_relative_price_atr_full`
   - `corridor_10atr_relative_price_atr_full`
4. `*_no_time_full` заданы с `row_dim=0` и помечены как `DIAGNOSTIC_ONLY`.
5. Обновлены тесты runner-а; текущий статус:
   - `72 passed`

## Где лежат результаты

- `docs/reports/2026-06-18-stage5_0a-feature-preflight.md`
- `ML/reports/stage5_0a_feature_preflight.json`
- `ML/reports/stage5_0a_feature_stats_normalized.csv`
- `ML/reports/stage5_0a_profile_summary.csv`

## Главные выводы

### 1. Технически preflight чистый

Не обнаружено:

- `NaN`
- `Inf`
- `PADDING_NOT_ZERO`
- нарушений profile contract

### 2. ATR остаётся главным источником holdout warning

Это относится ко всем профилям, где `ATR` идёт в `row_fields`. Это disclosure-факт, а не автоматический запрет на rerun.

### 3. Абсолютная цена остаётся только диагностическим контролем

`all100_absolute_price_time` по-прежнему показывает holdout shift по абсолютной цене.

### 4. Старые corridor-профили с `seq_len=40` больше не стоит использовать как основные

Честная truncation после исправления метрики:

- `corridor_5atr_relative_price_no_time`: `0.491`
- `corridor_10atr_relative_price_no_time`: `0.871`

Причина: раньше эти профили слишком часто упирались в cap.

### 5. Full corridor дал два разных вывода

- `corridor_5atr_relative_price_atr_full`:
  - median raw candidates = `40`
  - median selected = `40`
  - truncation = `0.000`
  - снятие cap мало меняет медиану, но убирает искажение на части строк

- `corridor_10atr_relative_price_atr_full`:
  - median raw candidates = `62`
  - median selected = `62`
  - truncation = `0.000`
  - старый capped-вариант реально терял информацию

### 6. Full corridor не превратился в фактический all100

Формальный контроль “почти all100”:

- `corridor_10atr_relative_price_no_time_full`:
  - `% candidate_count_before_cap >= 90` = `0.0105`
  - `% selected_count_after_cap >= 90` = `0.0105`

Значит `corridor_10atr_full` остаётся отдельным представлением, а не замаскированным `all100`.

### 7. Профили с `row_dim=0` пока нельзя автоматически тащить в обучение

`corridor_*_no_time_full` пригодны для диагностики, но не для немедленного training rerun. Для обучения нужен отдельный осознанный support `row_dim=0` в модельном слое Stage 5.

## Что делать дальше

Обсуждать Stage 5.0 rerun уже с новой corridor-матрицей.

### Можно обсуждать для training rerun

- `all100_no_price_time`
- `all100_relative_price_no_time`
- `all100_relative_price_time`
- `nearest40_relative_price_no_time`
- `nearest40_relative_price_time`
- `corridor_5atr_relative_price_atr_full`
- `corridor_10atr_relative_price_atr_full`

### Оставить только как diagnostic-only

- `time_only_clean`
- `atr_only`
- `time_plus_atr`
- `all100_absolute_price_time`
- `corridor_5atr_relative_price_no_time_full`
- `corridor_10atr_relative_price_no_time_full`
- `corridor_15atr_relative_price_no_time`
- `corridor_10atr_relative_price_time`

### Не использовать как основной rerun-кандидат

- `corridor_5atr_relative_price_no_time`
- `corridor_10atr_relative_price_no_time`

## Файлы

Код:

- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `tests/test_stage5_transformer_breach.py`

Документы:

- `docs/reports/2026-06-18-stage5_0a-feature-preflight.md`
- `docs/ML/benchmark_stage5_transformer_breach.py.md`
- `docs/superpowers/plans/2026-06-18-stage5_0a-corridor-full-preflight.md`

Артефакты:

- `ML/reports/stage5_0a_feature_preflight.json`
- `ML/reports/stage5_0a_feature_stats_normalized.csv`
- `ML/reports/stage5_0a_profile_summary.csv`
