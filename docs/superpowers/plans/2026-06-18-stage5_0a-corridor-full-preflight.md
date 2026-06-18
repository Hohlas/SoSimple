# Stage 5.0a Corridor Full Preflight Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking. Do not commit unless the user explicitly asks.

**Goal:** Добавить допроверку corridor-профилей без лимита `seq_len=40`, исправить измерение truncation и отделить чистую геометрию от вариантов с `ATR` на входе модели.

**Architecture:** Stage 5.0a остаётся чисто диагностическим этапом без обучения. Сначала runner начинает считать raw corridor coverage до среза по `seq_len`, затем получает новые `full`-профили (`seq_len=100`) в двух вариантах: без календаря и без `ATR` как входа модели, а также контрольные варианты с `ATR`. После этого preflight снова строит JSON/CSV/report и даёт решение, какие corridor-профили вообще можно обсуждать для Stage 5.0 rerun.

**Tech Stack:** Python, pandas, numpy, pytest, существующий runner `ML/baseline/benchmark_stage5_transformer_breach.py`, `~/git/SoSimple/.venv/bin/python`.

---

## Source Of Truth

- `docs/reports/2026-06-18-stage5_0a-feature-preflight.md`
- `ML/reports/stage5_0a_feature_preflight.json`
- `ML/reports/stage5_0a_feature_stats_normalized.csv`
- `ML/reports/stage5_0a_profile_summary.csv`
- `docs/methodology/A7-feature-distribution-audit.md`
- `docs/methodology/A6-fractal-feature-profile-catalog.md`
- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `tests/test_stage5_transformer_breach.py`

## Hard Boundaries

- Не запускать обучение Transformer.
- Не интерпретировать PF, AUC или trading-метрики.
- Не менять существующие Stage 5.0 training profiles без отдельного согласования.
- Не использовать holdout для выбора scaler, clipping или состава признаков.
- Все новые выводы оставить в статусе `DIAGNOSTIC_ONLY`.
- Профили с `row_dim=0` в этом этапе использовать только для preflight; допуск к обучению требует отдельной проверки поддержки `row_dim=0` в `ML/models/fractal_breach_transformer.py` или явного решения по нулевому row-контексту.

## Design Decisions To Lock Before Implementation

1. `seq_len=100` считать “без лимита” только в смысле текущего CSV-контракта:
   - максимум доступны `fractal0..fractal99`;
   - full-corridor = все доступные фракталы, прошедшие corridor-filter.
2. Разделить два уровня использования `ATR`:
   - `ATR` как знаменатель в `price_coord_atr` допустим в чистом геометрическом профиле;
   - `ATR` как отдельный `row_feature` должен быть либо явно включён в имя профиля, либо отсутствовать.
3. Настоящая truncation определяется только по raw candidate count:
   - `candidate_count_before_cap`
   - `selected_count_after_cap`
   - `is_truncated = candidate_count_before_cap > seq_len`

## New Profiles To Add

Обязательные:

- `corridor_5atr_relative_price_no_time_full`
- `corridor_10atr_relative_price_no_time_full`

Смысл:
- `seq_len=100`
- `row_fields=[]`
- `token_fields=['price_coord_atr', direction, front, back, strong, break, reverse, power, count, impulse]`
- `uses_time=False`
- `ATR` не подаётся в модель как отдельный row-признак
- `ATR` используется только внутри расчёта `price_coord_atr`

Контрольные варианты:

- `corridor_5atr_relative_price_atr_full`
- `corridor_10atr_relative_price_atr_full`

Смысл:
- то же самое, но `row_fields=['ATR']`

## Comparison Matrix To Keep Clean

Нельзя смешивать в одном сравнении два изменения сразу: снятие лимита `seq_len=40 -> 100` и удаление `ATR` из входа модели.

Поэтому сравнения разделить так:

1. Честное сравнение “старый corridor vs full corridor при сохранении `ATR` как входа модели”:
   - `corridor_5atr_relative_price_no_time` vs `corridor_5atr_relative_price_atr_full`
   - `corridor_10atr_relative_price_no_time` vs `corridor_10atr_relative_price_atr_full`

2. Отдельный новый диагностический контроль “что даёт corridor без `ATR` как входа модели”:
   - `corridor_5atr_relative_price_no_time_full`
   - `corridor_10atr_relative_price_no_time_full`

3. Внешние ориентиры для интерпретации:
   - `nearest40_relative_price_*`
   - `all100_relative_price_*`

## Expected Output

- Обновлённый `ML/reports/stage5_0a_feature_preflight.json`
- Обновлённый `ML/reports/stage5_0a_feature_stats_normalized.csv`
- Обновлённый `ML/reports/stage5_0a_profile_summary.csv`
- Обновлённый `docs/reports/2026-06-18-stage5_0a-feature-preflight.md`
- Обновлённый `CONTEXT_HANDOFF.md`
- При изменении кода — синхронизация docs/wiki по правилам проекта

## Task 1: Corridor Contract And Naming Guards

**Files:**
- Modify: `tests/test_stage5_transformer_breach.py`
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`

- [ ] Добавить тест, что новые `*_no_time_full` corridor-профили не содержат ни calendar, ни `ATR` в `row_fields`.
- [ ] Добавить тест, что новые `*_atr_full` corridor-профили содержат `row_fields=['ATR']`.
- [ ] Добавить тест, что `seq_len=100` у всех `*_full` corridor-профилей.
- [ ] Добавить тест, что `price_coord_atr` остаётся в `token_fields` у всех новых профилей.
- [ ] Добавить тест, что profile contract новых профилей явно различает:
  - `row_fields=[]` для чистой геометрии
  - `row_fields=['ATR']` для контрольного варианта

Run:

```bash
~/git/SoSimple/.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -q
```

Expected: новые contract-тесты падают до реализации и проходят после реализации.

## Task 2: Raw Corridor Coverage Before Cap

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Modify: `tests/test_stage5_transformer_breach.py`

- [ ] Добавить в corridor builder/coverage отдельный расчёт:
  - `candidate_count_before_cap`
  - `selected_count_after_cap`
  - `is_truncated`
- [ ] Изменить feature builder так, чтобы он возвращал дополнительный объект `selection_meta` со строковыми массивами минимум для:
  - `candidate_count_before_cap`
  - `selected_count_after_cap`
  - `is_truncated`
- [ ] При необходимости добавить в `selection_meta` дополнительные производные поля для отчёта:
  - `candidate_count_ge_40`
  - `candidate_count_ge_90`
  - `candidate_count_eq_100`
- [ ] Изменить `compute_profile_coverage()` так, чтобы он принимал `selection_meta`, а truncation считался только по правилу `candidate_count_before_cap > seq_len`.
- [ ] Добавить coverage-метрики в JSON/CSV:
  - p5/p25/p50/p75/p95 для `candidate_count_before_cap`
  - p5/p25/p50/p75/p95 для `selected_count_after_cap`
  - `pct_truncation_true`
- [ ] Добавить тест, что строка с `candidate_count_before_cap == seq_len` не считается truncated.
- [ ] Добавить тест, что строка с `candidate_count_before_cap > seq_len` считается truncated.
- [ ] Добавить тест, что для `seq_len=100` truncation считается честно, а не по условию `selected_count_after_cap == seq_len`.

Run:

```bash
~/git/SoSimple/.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -q
```

Expected: все тесты проходят.

## Task 3: Full Corridor Profiles In Preflight

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Modify: `tests/test_stage5_transformer_breach.py`

- [ ] Добавить 4 новых профиля в `PROFILE_DEFS`.
- [ ] Включить их в `PREFLIGHT_PROFILE_NAMES`.
- [ ] Убедиться, что preflight builder строит их через тот же `relative_price` pipeline.
- [ ] Для `*_no_time_full` задать `row_dim=0`.
- [ ] Явно пометить в contract/report, что `*_no_time_full` с `row_dim=0` имеют статус `DIAGNOSTIC_ONLY` до отдельной проверки модели.
- [ ] Проверить, что normalizer корректно работает с `row_dim=0`.
- [ ] Добавить тест shapes для новых профилей.
- [ ] Добавить тест, что `build_profile_features` для `*_full` реально может вернуть больше 40 выбранных фракталов, если они есть в corridor.

Run:

```bash
~/git/SoSimple/.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -q
```

Expected: новые full-профили строятся без ошибок.

## Task 4: Rerun Stage 5.0a Preflight

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Generate: `ML/reports/stage5_0a_feature_preflight.json`
- Generate: `ML/reports/stage5_0a_feature_stats_normalized.csv`
- Generate: `ML/reports/stage5_0a_profile_summary.csv`

- [ ] Запустить preflight после добавления новых профилей и raw corridor coverage.
- [ ] Проверить, что в CSV есть новые поля и новые профили.
- [ ] Отдельно собрать сравнение:
  - `corridor_5atr_relative_price_no_time` vs `corridor_5atr_relative_price_atr_full`
  - `corridor_10atr_relative_price_no_time` vs `corridor_10atr_relative_price_atr_full`
  - `corridor_5atr_relative_price_no_time_full`
  - `corridor_10atr_relative_price_no_time_full`
  - `corridor_5atr_relative_price_atr_full`
  - `corridor_10atr_relative_price_atr_full`
  - `nearest40_relative_price_*`
  - `all100_relative_price_*`
- [ ] Проверить, остаётся ли `candidate_count_before_cap` у full-corridor значительно меньше 100 или профиль фактически превращается в почти `all100`.
- [ ] Отдельно посчитать formal “almost all100” indicators:
  - доля строк, где `candidate_count_before_cap >= 90`
  - доля строк, где `selected_count_after_cap >= 90`

Run:

```bash
~/git/SoSimple/.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --feature-preflight-only
```

Expected:
- JSON/CSV пересозданы
- preflight не запускает обучение
- новые corridor full-профили отражены в structured artifact

## Task 5: Report And Decision Gate

**Files:**
- Modify: `docs/reports/2026-06-18-stage5_0a-feature-preflight.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/ML/benchmark_stage5_transformer_breach.py.md`
- Modify: `MODULE_INDEX.md`
- Update wiki after code/doc changes

- [ ] Обновить отчёт Stage 5.0a: добавить corridor full-проверку и объяснить разницу между:
  - основной Stage 5.0a preflight
  - addendum `Stage 5.0a Addendum: Corridor Full Preflight`
  - `ATR` как scaler/unit в `price_coord_atr`
  - `ATR` как отдельным входом модели
- [ ] В addendum отдельно показать две линии сравнения:
  - старый corridor `seq_len=40` vs `*_atr_full`
  - новые чистые `*_no_time_full` как диагностический контроль
- [ ] В отчёте формально показать “почти all100” через метрики:
  - `% rows with candidate_count_before_cap >= 90`
  - `% rows with selected_count_after_cap >= 90`
- [ ] Явно зафиксировать, что `row_dim=0` профили не допускаются в training rerun автоматически, даже если preflight выглядит чисто.
- [ ] Зафиксировать, какие corridor-профили:
  - остаются diagnostic-only
  - допустимы к обсуждению для training rerun
  - должны быть исключены
- [ ] Обновить handoff с новым решением по corridor.
- [ ] Синхронизировать docs для runner-а.
- [ ] Выполнить wiki ingest/update, если выводы `fractal-stop-research.md` меняются.

## Acceptance Criteria

- Есть честная метрика truncation на основе raw candidate count.
- Builder возвращает `selection_meta`, из которого можно восстановить raw corridor coverage до cap.
- Есть отдельные full corridor-профили без `ATR` как входа модели.
- Есть контрольные full corridor-профили с `ATR` как входом модели.
- В JSON/CSV различаются:
  - `candidate_count_before_cap`
  - `selected_count_after_cap`
  - `pct_truncation_true`
- Новые профили и старые `seq_len=40` corridor-профили сравнимы в отчёте.
- Есть явный вывод: corridor full действительно даёт новое представление или почти сводится к `all100`, подтверждённый метриками `candidate_count_before_cap >= 90` / `selected_count_after_cap >= 90`.
- Есть явный вывод: нужен ли `ATR` как вход модели в corridor-профиле.
- Есть явная пометка, что `row_dim=0` профили остаются `DIAGNOSTIC_ONLY`, пока модельный слой не подтверждён отдельно.
- После допроверки всё ещё не запускается обучение Transformer без отдельного согласования пользователя.
