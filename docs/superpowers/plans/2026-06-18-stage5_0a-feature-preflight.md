# Stage 5.0a Feature Preflight Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking. Do not commit unless the user explicitly asks.

**Goal:** Проверить профили признаков Stage 5.0 до обучения Transformer, чтобы не повторить ошибку с масштабом, абсолютной ценой и нечистыми time-контролями.

**Architecture:** Один diagnostic runner строит финальные входы тем же feature builder-ом, который будет использовать обучение, и сохраняет A7 Feature Distribution Audit по каждому профилю. Этап не обучает модель, не смотрит торговый PF и не выбирает winner.

**Tech Stack:** Python, pandas, numpy, scikit-learn, существующий Stage 5.0 runner, `~/git/SoSimple/.venv/bin/python`.

---

## Source Of Truth

- `CONTEXT_HANDOFF.md` — текущее состояние Stage 5.0.
- `docs/methodology/A7-feature-distribution-audit.md` — обязательный формат проверки распределений.
- `docs/methodology/A6-fractal-feature-profile-catalog.md` — каталог фрактальных профилей.
- `docs/methodology/08-model-development.md` — Final Tensor Scale Audit.
- `docs/reports/2026-06-17-stage5-transformer-breach.md` — старый ненормализованный Stage 5.0 результат.
- `ML/baseline/benchmark_stage5_transformer_breach.py` — текущий feature builder и normalization code.
- `tests/test_stage5_transformer_breach.py` — существующие тесты Stage 5.0.

## Hard Boundaries

- Не обучать Transformer.
- Не запускать торговый слой и PF grid search.
- Не выбирать winner по holdout.
- Не менять профили после просмотра holdout-метрик.
- 2023-2026 использовать только для disclosure сдвига распределений, не для выбора scaler, clipping, corridor width или состава признаков.
- Все выводы Stage 5.0a имеют статус `DIAGNOSTIC_ONLY`.

## Profiles To Audit

Зафиксировать матрицу до запуска:

| Profile | Смысл |
|---|---|
| `time_only_clean` | Только `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` |
| `atr_only` | Только ATR или заранее выбранный volatility-признак |
| `time_plus_atr` | Время + ATR; бывший нечистый `time_only` должен попасть сюда |
| `all100_absolute_price_time` | Контроль старого представления с абсолютной ценой |
| `all100_no_price_time` | Проверка, не вредит ли абсолютная цена |
| `all100_relative_price_no_time` | Чистая геометрия всех 100 фракталов без календаря |
| `all100_relative_price_time` | Геометрия всех 100 фракталов + календарь |
| `corridor_5atr_relative_price_no_time` | Узкий corridor вокруг `fractal0` |
| `corridor_10atr_relative_price_no_time` | Основной corridor-кандидат |
| `corridor_15atr_relative_price_no_time` | Широкий corridor |
| `corridor_10atr_relative_price_time` | Corridor + календарь |
| `nearest40_relative_price_no_time` | 40 ближайших к `fractal0` уровней без календаря |
| `nearest40_relative_price_time` | 40 ближайших к `fractal0` уровней + календарь |

Для corridor-профилей координата цены:

```text
price_coord_atr = (fractal_price - fractal0_price) / ATR
```

Дополнительно посчитать `corridor_width_atr`, если используется range-нормализация.

## Profile Contracts

Каждый профиль должен быть описан не только именем, но и полным контрактом входа. Этот контракт сохраняется в JSON и в отчёте.

Общие правила:

- `fractal0` — anchor, точка отсчёта цены и свежести.
- Для `nearest40_*` `fractal0` используется как anchor и **не считается** одним из 40 соседей.
- Для `corridor_*` `fractal0` включается как первый anchor-token, затем добавляются уровни внутри corridor; если реализация выберет другой вариант, это должно быть явно помечено `CONTRACT_WARNING`.
- `padding_value = 0.0`.
- `mask = 1` означает реальный token, `mask = 0` означает padding.
- Padding не участвует в fit scaler, статистиках признаков и tail-check.

| Profile family | selector | token_fields | row_fields | token_order | seq_len |
|---|---|---|---|---|---:|
| `time_only_clean` | no token selector | none | `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` | none | 0 |
| `atr_only` | no token selector | none | `ATR` | none | 0 |
| `time_plus_atr` | no token selector | none | `ATR`, `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` | none | 0 |
| `all100_absolute_price_time` | `fractal0..fractal99` | base10 with raw `price` | `ATR`, `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` | freshness: `fractal0`, `fractal1`, ... | 100 |
| `all100_no_price_time` | `fractal0..fractal99` | base10 without `price` | `ATR`, `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` | freshness: `fractal0`, `fractal1`, ... | 100 |
| `all100_relative_price_no_time` | `fractal0..fractal99` | base10 where `price` -> `price_coord_atr` | `ATR` | freshness: `fractal0`, `fractal1`, ... | 100 |
| `all100_relative_price_time` | `fractal0..fractal99` | base10 where `price` -> `price_coord_atr` | `ATR`, `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` | freshness: `fractal0`, `fractal1`, ... | 100 |
| `corridor_5atr_relative_price_no_time` | levels within +/-5 ATR from `fractal0.price` | base10 where `price` -> `price_coord_atr` | `ATR` | anchor first, then ascending absolute distance to anchor | fixed before run; report actual |
| `corridor_10atr_relative_price_no_time` | levels within +/-10 ATR from `fractal0.price` | base10 where `price` -> `price_coord_atr` | `ATR` | anchor first, then ascending absolute distance to anchor | fixed before run; report actual |
| `corridor_15atr_relative_price_no_time` | levels within +/-15 ATR from `fractal0.price` | base10 where `price` -> `price_coord_atr` | `ATR` | anchor first, then ascending absolute distance to anchor | fixed before run; report actual |
| `corridor_10atr_relative_price_time` | levels within +/-10 ATR from `fractal0.price` | base10 where `price` -> `price_coord_atr` | `ATR`, `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` | anchor first, then ascending absolute distance to anchor | fixed before run; report actual |
| `nearest40_relative_price_no_time` | 40 closest levels to `fractal0.price`, excluding anchor from K | base10 where `price` -> `price_coord_atr` | `ATR` | ascending absolute distance to anchor; tie-breaker by freshness | 40 |
| `nearest40_relative_price_time` | 40 closest levels to `fractal0.price`, excluding anchor from K | base10 where `price` -> `price_coord_atr` | `ATR`, `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` | ascending absolute distance to anchor; tie-breaker by freshness | 40 |

`base10` means:

```text
price/price_coord_atr, direction, front, back, strong, break, reverse, power, count, impulse
```

For `no_price`, token fields are:

```text
direction, front, back, strong, break, reverse, power, count, impulse
```

If any implementation detail differs from this table, Stage 5.0a must stop with `CONTRACT_ERROR` or explicitly report `CONTRACT_WARNING` before producing model-ready artifacts.

## Expected Output

- `ML/reports/stage5_0a_feature_preflight.json` — structured artifact.
- `ML/reports/stage5_0a_feature_stats_normalized.csv` — плоская таблица статистик каждого признака после нормализации.
- `ML/reports/stage5_0a_profile_summary.csv` — сводка по профилям: coverage, warnings/errors, corridor counts, tail flags.
- `docs/reports/2026-06-18-stage5_0a-feature-preflight.md` — короткий отчёт.
- Обновление `CONTEXT_HANDOFF.md` после выполнения.
- При изменении кода — обновить docs/MODULE_INDEX/wiki по правилам проекта.

## Task 1: Tests And Contract Guards

**Files:**
- Modify: `tests/test_stage5_transformer_breach.py`
- Modify/Create: `ML/baseline/benchmark_stage5_transformer_breach.py`

- [ ] Добавить тест, что `time_only_clean` содержит только 4 календарных признака и не содержит ATR.
- [ ] Добавить тест, что `time_plus_atr` содержит календарь + ATR.
- [ ] Добавить тест, что каждый profile сохраняет contract: `selector`, `token_fields`, `row_fields`, `token_order`, `seq_len`, `padding_value`, `mask_semantics`.
- [ ] Добавить тест порядка токенов: `all100_*` по свежести, `corridor_*` anchor first затем по расстоянию, `nearest40_*` по расстоянию с tie-breaker по свежести.
- [ ] Добавить тест, что `nearest40_*` исключает `fractal0` из K соседей или выдаёт `CONTRACT_WARNING`.
- [ ] Добавить тест формулы `price_coord_atr = (price_i - fractal0_price) / ATR`.
- [ ] Добавить тест, что corridor 5/10/15 ATR не содержит токены вне заявленных границ.

Run:

```bash
~/git/SoSimple/.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -q
```

Expected: все тесты проходят.

## Task 2: Feature Preflight Runner

**Files:**
- Modify/Create: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Generate: `ML/reports/stage5_0a_feature_preflight.json`

- [ ] Добавить CLI-режим `--feature-preflight-only`.
- [ ] Для каждого profile построить финальные `tokens`, `row_features`, `mask` на train, val_stop, holdout.
- [ ] Применить normalization только с fit на train.
- [ ] Не запускать обучение модели.
- [ ] Сохранить `normalization_config`, scaler stats и `normalized_distribution_audit`.
- [ ] Сохранить `profile_contracts` для каждого профиля: `selector`, `token_fields`, `row_fields`, `token_order`, `seq_len`, `padding_value`, `mask_semantics`.
- [ ] Сохранить полную таблицу статистик признаков после нормализации в `ML/reports/stage5_0a_feature_stats_normalized.csv`.
- [ ] Сохранить сводную таблицу по профилям в `ML/reports/stage5_0a_profile_summary.csv`.
- [ ] Для каждого profile сохранить coverage: valid tokens p5/p25/p50/p75/p95, empty/single/two/three_plus, truncation.
- [ ] Для holdout сохранить только shift/disclosure, без принятия решений по обработке.

Формат `stage5_0a_feature_stats_normalized.csv`:

| Column | Meaning |
|---|---|
| `profile` | Имя feature profile |
| `split` | `train`, `val_stop`, `holdout` |
| `feature_group` | `token`, `row`, `mask`, `coverage` |
| `feature_name` | Имя признака: например `price_coord_atr`, `direction`, `ATR`, `hour_sin` |
| `token_position` | Позиция токена, если статистика считается по позиции; иначе пусто |
| `n_valid` | Число реальных значений без padding |
| `missing_pct` | Доля пропусков |
| `zero_pct` | Доля нулей среди реальных значений |
| `mean` / `std` | Среднее и стандартное отклонение после нормализации |
| `min`, `p1`, `p5`, `p25`, `p50`, `p75`, `p95`, `p99`, `max` | Распределение после нормализации |
| `frac_abs_gt3`, `frac_abs_gt5`, `frac_abs_gt10`, `frac_abs_gt20` | Доли хвостов после нормализации |
| `nan_count`, `inf_count` | Технические ошибки |
| `status` | `OK`, `WARNING`, `ERROR` |
| `flags` | Список флагов через `;`: `TAIL_GT10`, `TAIL_GT20`, `PADDING_NOT_ZERO`, `REGIME_SHIFT` |

Важно:

- В CSV должны попасть именно финальные значения после normalization, которые реально пойдут в модель.
- Padding не включать в `n_valid`, `mean`, `std`, percentiles и tail fractions.
- Для holdout статистики сохранять, но не использовать их для выбора scaler, clipping, log/signed-log или профиля.
- Если размер CSV получается большим, дополнительно можно сохранить parquet, но CSV обязателен для ручного просмотра.

Run:

```bash
~/git/SoSimple/.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --feature-preflight-only
```

Expected: создаются `ML/reports/stage5_0a_feature_preflight.json`, `ML/reports/stage5_0a_feature_stats_normalized.csv`, `ML/reports/stage5_0a_profile_summary.csv`; обучение не запускается.

## Task 3: Report

**Files:**
- Create: `docs/reports/2026-06-18-stage5_0a-feature-preflight.md`

- [ ] Свести таблицу по всем профилям: статус `OK/WARNING/ERROR`, coverage, хвосты, NaN/Inf, padding.
- [ ] Дать ссылку на `ML/reports/stage5_0a_feature_stats_normalized.csv` как главный файл для ручного анализа распределений признаков после нормализации.
- [ ] В отчёте показать сжатую выдержку из CSV: худшие признаки по `frac_abs_gt10`, `max(abs(x))`, `zero_pct`, `REGIME_SHIFT`.
- [ ] Отдельно показать clean controls: `time_only_clean`, `atr_only`, `time_plus_atr`.
- [ ] Отдельно показать corridor 5/10/15 ATR: сколько фракталов попадает в коридор и есть ли бедные периоды.
- [ ] Отдельно показать absolute price vs no_price vs relative_price.
- [ ] Зафиксировать, какие `ERROR` блокируют обучение.
- [ ] Зафиксировать, какие `WARNING` можно принять как риск, а какие требуют изменения профиля.
- [ ] В конце дать рекомендацию: какую матрицу профилей разрешить для Stage 5.0 rerun.

## Task 4: Stop For Human Review

**Files:**
- Modify: `CONTEXT_HANDOFF.md`

- [ ] Обновить `CONTEXT_HANDOFF.md`: Stage 5.0a выполнен, указать путь к JSON/report.
- [ ] Не запускать Stage 5.0 training rerun без явного согласования пользователя.
- [ ] В финальном ответе показать 3 пункта: блокеры, предупреждения, рекомендуемый rerun-профиль.

## Acceptance Criteria

- Есть JSON и markdown-отчёт Stage 5.0a.
- Есть `ML/reports/stage5_0a_feature_stats_normalized.csv` со статистикой каждого признака после нормализации.
- Есть `ML/reports/stage5_0a_profile_summary.csv` со сводкой по профилям.
- Все профили построены тем же builder-ом, что будет использовать обучение.
- Каждый профиль имеет сохранённый и проверенный contract: selector, fields, token order, seq_len, padding, mask.
- Есть тест стабильности порядка токенов для all100/corridor/nearest.
- Есть доказательство, что scaler fit выполнен только на train.
- Padding остаётся нулём.
- `time_only_clean` не содержит ATR.
- Corridor coverage посчитан по train/val_stop/holdout.
- Holdout не использован для выбора обработки.
- Есть явное решение: можно ли запускать Stage 5.0 rerun и с какой матрицей профилей.
