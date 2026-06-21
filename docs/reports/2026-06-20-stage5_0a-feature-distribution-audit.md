# Stage 5.0a Feature Distribution Audit

> **Date**: 2026-06-20
> **Status**: Completed (`DIAGNOSTIC_ONLY`)
> **Goal**: По методике A7 (`docs/methodology/A7-feature-distribution-audit.md`) проверить распределения признаков 7 профилей-кандидатов Stage 5.0 rerun до обучения: нормализация, хвосты, сдвиг split, padding, corridor bounds. Исправить найденные проблемы transform-ами, выбранными по train/val audit (не по holdout).
> **Related**:
> - `docs/methodology/A7-feature-distribution-audit.md` — методика
> - `docs/reports/2026-06-18-stage5_0a-feature-preflight.md` — предыдущий preflight
> - `wiki/research/fractal-stop-research.md` — синтез Fractal Stop

## Context

Stage 5.0a feature preflight (2026-06-18) и corridor full addendum зафиксировали матрицу профилей и coverage, но не делали полного feature distribution audit по A7: aggregated token stats скрывали per-position проблемы, ATR как row-признак имел критический holdout regime shift, `price_coord_atr` подавался raw. Этот этап закрывает gap до повторного обучения Transformer.

Кандидаты Stage 5.0 rerun (из CONTEXT_HANDOFF 2026-06-18):

- `all100_no_price_time`
- `all100_relative_price_no_time`
- `all100_relative_price_time`
- `nearest40_relative_price_no_time`
- `nearest40_relative_price_time`
- `corridor_5atr_relative_price_atr_full`
- `corridor_10atr_relative_price_atr_full`

Split: train ≤2020, val_stop 2021-2022, holdout ≥2023. Target: `sell_stop_broken_H6_off05_flag`.

## What Was Done

### 1. Feature distribution audit по A7

Извлечены статистики из `stage5_0a_feature_stats_normalized.csv` по 7 профилям-кандидатам: row/token/coverage по train/val_stop/holdout. Проверены A7 ERROR/WARNING флаги.

**Найдено:**
- `ERROR` — 0 во всех профилях.
- `WARNING` — одинаковая для всех 7: `REGIME_SHIFT in ATR (row)` + `TAIL_GT10/TAIL_GT20 in holdout ATR`. Все 7 включают ATR в `row_fields`.
- Token-признаки (direction, front, back, strong, break, reverse, power, count, impulse) — чистые, shift <0.15 по p95, хвостов >10std нет.
- `price_coord_atr` (в 6 relative_price профилях) — чистый по aggregated, shift малый.
- Corridor bounds — в пределах (Stage 5.0a addendum уже проверил raw coverage).

### 2. ATR regime shift — log1p transform

**Проблема:** ATR как row-признак normalуется raw → StandardScaler (fit на train). Распределение:

| Split | p50 | p95 | p99 | max | frac >10std | frac >20std |
|---|---|---|---|---|---|---|
| train | −0.148 | 1.830 | 3.809 | 6.522 | 0.000 | 0.000 |
| val_stop | +0.699 | 1.830 | 3.356 | 3.639 | 0.000 | 0.000 |
| holdout | +1.774 | **12.062** | **27.885** | **32.865** | **0.0610** | **0.0130** |

Holdout ATR уходит до +32.9 std — модель не видела таких значений в train. Сдвиг начинается уже в val_stop (p50 −0.15 → +0.70).

**Решение (A7):** ATR неотрицательный с длинным правым хвостом → `log1p(ATR)` перед StandardScaler. A7 прямо рекомендует `log1p(x)` для таких величин. Решение принято по train/val audit (val_stop уже показывает сдвиг), не по holdout — методически чисто.

Реализовано в `build_row_features` (`ML/baseline/benchmark_stage5_transformer_breach.py:656`): `np.log1p(vals.clip(lower=0.0))`. `price_coord_atr` и corridor selector **не затронуты** — они используют raw ATR как знаменатель отдельно (`build_profile_features_from_parsed:924`), что и должно быть.

TDD: RED-тест `test_atr_log1p_transformed_in_row_features` (упал на raw `e−1=1.718` vs `log1p(e−1)=1.0`) → GREEN.

### 3. Per-position token stats (gap A7)

**Gap:** A7 требует «по каждой позиции токена, если порядок имеет смысл». Stage 5.0a агрегировал token stats по всем позициям (`token_position` пустой). Для corridor (anchor first, then ascending distance), nearest (ascending distance), all100 (freshness) порядок осмыслен.

Реализована функция `compute_per_position_token_stats` — per-feature stats для каждой позиции 0..seq_len−1, используя только valid (mask=True) samples. Fully-padded позиции (n_valid=0) сохраняются (padding coverage — отдельный A7 diagnostic). Интегрирована в `run_feature_preflight`, новый артефакт `stage5_0a_feature_stats_per_position.csv` (30900 rows для 14 sequence-профилей).

TDD: 3 RED-теста (ImportError) → GREEN.

### 4. Per-position нашёл скрытую проблему: pos99 TAIL_GT10

Aggregated stats скрыли: `all100_relative_price_no_time` и `all100_relative_price_time` имеют **TAIL_GT10 на позиции 99 в train** (p95=10.855, max=13.896). Pos99 = самый старый фрактал (fractal99) — может быть далеко от anchor в ATR. В aggregated frac_gt10=0.001 (порог 1%): pos99 это 1/100 позиций, 5% хвостов на ней = 0.05% от всех. Per-position анализ оправдал себя.

### 5. signed-log для price_coord_atr

**Решение (A7):** A7 прямо рекомендует `sign(x)·log1p(abs(x))` для signed price coordinate. Реализован helper `_signed_log1p` и применён в обоих местах сборки `price_coord_atr` (`build_profile_features:814`, `build_profile_features_from_parsed:932`) для всех relative_price профилей.

TDD: обновлены `test_relative_price_formula_verified` и `test_relative_price_formula_matches_contract` (контракт raw → signed-log: `5.0 → 1.7918`), добавлен `test_price_coord_atr_signed_log_edge_cases`. RED → GREEN.

### 6. Raw corridor bounds recovery

После signed-log `compute_profile_coverage` считал `min/max_price_coord_atr` из post-transform tokens — это ослабляло A7 raw corridor bounds check (signed-log всегда меньше raw, не ловит raw violations). Восстановлены raw bounds через точное обратное преобразование для экстремумов: `raw = sign(x)·expm1(|x|)`. `test_corridor_profiles_respect_declared_boundaries` обновлён для raw check.

## Changed Files

- `ML/baseline/benchmark_stage5_transformer_breach.py`:
  - `_signed_log1p` helper
  - `build_row_features`: `log1p(ATR)` перед scaler
  - `build_profile_features`, `build_profile_features_from_parsed`: signed-log для `price_coord_atr`
  - `compute_per_position_token_stats`: новая функция
  - `compute_profile_coverage`: raw bounds recovery через expm1 для relative_price
  - `run_feature_preflight`: per-position сбор + `stage5_0a_feature_stats_per_position.csv` артефакт
  - `transform_type`: `raw_or_price_coord_atr` → `log1p_atr_or_price_coord_atr`
  - шапка файла: добавлен per_position.csv в Output
- `tests/test_stage5_transformer_breach.py`:
  - `test_atr_log1p_transformed_in_row_features` (новый)
  - `TestPerPositionTokenStats` класс (3 новых теста)
  - `test_relative_price_formula_verified`, `test_relative_price_formula_matches_contract` (обновлены под signed-log контракт)
  - `test_price_coord_atr_signed_log_edge_cases` (новый)
  - `test_corridor_profiles_respect_declared_boundaries` (обновлён для raw bounds check)

## Verification

```bash
~/git/SoSimple/.venv/bin/python -m pytest tests/ -q
~/git/SoSimple/.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --feature-preflight-only
```

Результат:
- `762 passed` (полный набор проекта; было 759 до доработок, +5 новых тестов Stage 5, ничего не сломано)
- preflight завершён успешно, без запуска обучения

## Artifacts

- `ML/reports/stage5_0a_feature_preflight.json` — обновлён (log1p, signed-log, per_position_csv путь)
- `ML/reports/stage5_0a_feature_stats_normalized.csv` — обновлён (ATR log1p, price_coord_atr signed-log)
- `ML/reports/stage5_0a_feature_stats_per_position.csv` — **новый** (30900 rows, per-position token stats)
- `ML/reports/stage5_0a_profile_summary.csv` — обновлён (`transform_type=log1p_atr_or_price_coord_atr`, TAIL_GT10 исчезли)

## Main Summary

### ATR regime shift: до vs после log1p (все 7 профилей)

| Метрика holdout ATR | До log1p | После log1p |
|---|---|---|
| max | 32.865 | 7.063 |
| p99 | 27.885 | 6.675 |
| p95 | 12.062 | 4.797 |
| frac >10std | 0.0610 | **0.0000** |
| frac >20std | 0.0130 | **0.0000** |
| REGIME_SHIFT delta | 10.23 | 3.14 |

TAIL_GT10/TAIL_GT20 **исчезли** во всех 7 профилях (feature_stats: 0 WARNING). Остаточный REGIME_SHIFT delta=3.14 — почти на пороге 3 std A7, holdout max=7.06 в разумных пределах для нейросети. A7: «зафиксировать regime shift, не подгонять scaler по holdout».

### price_coord_atr: до vs после signed-log (aggregated)

| Профиль | max raw | max signed-log | pos99 TAIL_GT10 |
|---|---|---|---|
| all100_relative_price_* | 13.896 | 2.777 | исчез |
| nearest40_relative_price_* | 11.085 | 3.181 | не было |
| corridor_5atr_*_full | 2.078 | 1.726 | не было |
| corridor_10atr_*_full | 2.247 | 1.741 | не было |

### Per-position: padding coverage (train)

| Профиль | n_pos | empty positions | n_valid pos0 / p50 / last |
|---|---|---|---|
| all100_* | 100 | 0 | 25672 / 25672 / 25672 |
| nearest40_* | 40 | 0 | 25672 / 25672 / 25672 |
| corridor_5atr_*_full | 100 | 16 | 25672 / 5744 / 0 |
| corridor_10atr_*_full | 100 | 9 | 25672 / 19368 / 3 |

Corridor empty positions — норм (узкий коридор), mask обрабатывает.

### Anchor (pos0) price_coord_atr

- all100/corridor: pos0 = const после scaler (anchor=fractal0, raw `price_coord_atr=0` → StandardScaler даёт константу). Ожидаемое свойство.
- nearest40: pos0 ≠ const (`exclude_anchor_from_k=True`, pos0 = ближайший к anchor, не сам anchor). Правильно.

### Corridor raw bounds (после expm1 recovery)

| Профиль | raw min | raw max | expected | |
|---|---|---|---|---|
| corridor_5atr_*_full | −3.10 | +4.62 | ±5 | OK |
| corridor_10atr_*_full | −3.04 | +4.70 | ±10 | OK |

## Final Decision Gate

Все 7 профилей-кандидатов после log1p(ATR) + signed-log(price_coord_atr):

- `ERROR`: 0
- `TAIL_GT10`/`TAIL_GT20`: 0 (исчезли)
- `REGIME_SHIFT`: delta=3.14 (ATR) — остаточный, A7: accept-as-warning, не подгонять scaler по holdout
- Per-position WARNING: 0 (pos99 TAIL_GT10 исчез)
- Corridor raw bounds: в пределах

**Все 7 профилей методически чистые по A7 и допущены к повторному обучению Stage 5.0.** Единственный остаточный WARNING — REGIME_SHIFT delta=3.14 для ATR, что A7 относит к «зафиксировать, не подгонять».

### Решение по transform-ам (принято по train/val audit)

| Признак | Transform | Обоснование (A7) |
|---|---|---|
| ATR (row) | `log1p(x)` перед StandardScaler | Неотрицательная величина с длинным правым хвостом |
| price_coord_atr (token) | `sign(x)·log1p(abs(x))` | Signed price coordinate с длинным хвостом (pos99 all100) |
| direction, front, back, и т.д. (token) | raw → StandardScaler | Чистые распределения, хвостов нет |
| time (hour/dow sin/cos) (row) | raw → StandardScaler | Фиксированный диапазон, shift=0 |

## Addendum 2026-06-21: сравнение способов сжатия хвостов

После обсуждения остаточного `ATR`-сдвига выполнена отдельная проверка распределения признаков без обучения модели. Цель — сравнить текущий способ сжатия хвостов с двумя альтернативами:

- `current`: текущий вариант `log1p(ATR)` + `sign(x)·log1p(abs(x))` для `price_coord_atr`;
- `asinh`: `asinh(x)` для `ATR` и `price_coord_atr`;
- `piecewise_tail`: кусочное сжатие хвостов; пороги `p05/p95` рассчитываются только на train, середина остаётся линейной, значения ниже `p05` и выше `p95` сжимаются логарифмически.

Проверка выполнена только для 7 профилей-кандидатов Stage 5.0 rerun:

- `all100_no_price_time`
- `all100_relative_price_no_time`
- `all100_relative_price_time`
- `nearest40_relative_price_no_time`
- `nearest40_relative_price_time`
- `corridor_5atr_relative_price_atr_full`
- `corridor_10atr_relative_price_atr_full`

Команда:

```bash
./.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --transform-comparison-only
```

### Результат сравнения

| Вариант | OK | WARNING | Главный вывод |
|---|---:|---:|---|
| `current` | 0 | 7 | Во всех 7 профилях остаётся `REGIME_SHIFT in ATR`: train p95=1.66, holdout p95=4.80, delta=3.14 |
| `asinh` | 7 | 0 | Предупреждения исчезли во всех 7 профилях |
| `piecewise_tail` | 7 | 0 | Предупреждения исчезли во всех 7 профилях |

Per-position проверка также чистая:

| Вариант | OK rows | EMPTY rows | WARNING rows |
|---|---:|---:|---:|
| `current` | 16080 | 1020 | 0 |
| `asinh` | 16080 | 1020 | 0 |
| `piecewise_tail` | 16080 | 1020 | 0 |

`EMPTY` строки — ожидаемые полностью пустые позиции в corridor-профилях; это не ошибка, а следствие ограниченного числа фракталов внутри коридора.

### Интерпретация

`asinh` и `piecewise_tail` лучше текущего варианта именно по задаче проверки распределения признаков: они убирают остаточное предупреждение по `ATR` без просмотра качества модели. Это не доказывает, что Transformer станет лучше; обучение не запускалось.

Решение для следующего training rerun: **использовать `asinh` как основной transform-кандидат**. Причина: `asinh` не требует fit-порогов, гладко сжимает хвосты, проще воспроизводится и меньше добавляет ручных степеней свободы. `piecewise_tail` оставить как диагностический контроль: он сильнее сжимает остаточный `ATR`-сдвиг, но требует заранее выбранных `p05/p95` и поэтому несёт больший риск скрытого перебора конфигураций.

Методически корректное следствие: следующий training rerun нужно планировать с заранее зафиксированным `asinh`. Если дополнительно обучать `piecewise_tail`, это должно быть оформлено как явно диагностическое сравнение, иначе появится новый скрытый перебор конфигураций.

### Артефакты addendum

- `ML/reports/stage5_0a_transform_comparison.json` — structured artifact сравнения
- `ML/reports/stage5_0a_transform_comparison_summary.csv` — краткая сводка `current/asinh/piecewise_tail`
- `ML/reports/stage5_0a_transform_comparison_stats.csv` — агрегированные статистики признаков
- `ML/reports/stage5_0a_transform_comparison_per_position.csv` — статистики по позициям последовательности

### Проверка addendum

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -q
./.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --transform-comparison-only
./.venv/bin/python -m pytest tests/ -q
```

Результат:

- `80 passed` для `tests/test_stage5_transformer_breach.py`
- transform comparison завершён успешно, без обучения
- `765 passed, 29 warnings` для полного набора `tests/`

## Методические замечания

- **log1p и signed-log выбраны по train/val audit**, не по holdout. val_stop уже показывал ATR сдвиг p50 (−0.15 → +0.70) — это обоснование log1p. Holdout только подтвердил что shift уменьшился. Это соответствует A7: «преобразования выбираются по train/validation audit, а не по test/holdout метрикам».
- **Per-position анализ обязателен** для sequence-профилей с осмысленным порядком. Aggregated stats скрыли pos99 TAIL_GT10 (0.05% от всех, под порогом 1%, но 5% на самой позиции). Без per-position эта проблема всплыла бы только в обучении.
- **Raw corridor bounds check** требует raw `price_coord_atr`. После signed-log нужен recovery через expm1 (или отдельный raw pass). Иначе check ослабевает.
- **Кусочное сжатие требует train-only fit.** Пороги `p05/p95` нельзя рассчитывать по `val_stop` или `holdout`; иначе преобразование будет подогнано под будущие периоды.

## Related Materials

- `docs/methodology/A7-feature-distribution-audit.md` — методика
- `docs/reports/2026-06-18-stage5_0a-feature-preflight.md` — предыдущий preflight
- `docs/reports/2026-06-18-stage5_0a-corridor-full-preflight.md` — corridor addendum
- `docs/ML/benchmark_stage5_transformer_breach.py.md` — документация модуля
- `wiki/research/fractal-stop-research.md` — синтез Fractal Stop
- `ML/reports/stage5_0a_feature_stats_per_position.csv` — per-position артефакт
- `ML/reports/stage5_0a_transform_comparison_summary.csv` — addendum 2026-06-21, сравнение способов сжатия хвостов
