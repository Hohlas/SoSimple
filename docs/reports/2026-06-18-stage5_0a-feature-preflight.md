# Stage 5.0a Feature Preflight

> **Date**: 2026-06-18
> **Status**: Completed (`DIAGNOSTIC_ONLY`)
> **Goal**: Проверить финальные входы Stage 5.0 до обучения Transformer: clean-controls, абсолютную цену, `relative_price`, `nearest40`, `corridor`, нормализацию и честный coverage до среза по `seq_len`.
> **Related plan/spec**:
> - `docs/superpowers/plans/2026-06-18-stage5_0a-feature-preflight.md`
> - `docs/superpowers/plans/2026-06-18-stage5_0a-corridor-full-preflight.md`

## Context

Stage 5.0 дал `DIAGNOSTIC_FAIL_WITH_PREPROCESSING_BUG`: старый прогон Transformer был выполнен без фактической нормализации финальных признаков. Поэтому Stage 5.0a сначала проверял feature builder и final tensors без обучения. После первого прогона остался методический вопрос по `corridor_*`: старая метрика truncation смотрела только на уже выбранные токены и не отличала настоящий full corridor от результата после жёсткого cap.

## What Was Done

1. В `ML/baseline/benchmark_stage5_transformer_breach.py` добавлен режим `--feature-preflight-only`.
2. Зафиксирована матрица preflight-профилей, включая clean-controls, `all100_*`, `nearest40_*`, старые `corridor_*` и новые `corridor_*_full`.
3. Добавлены profile contracts, включая явный флаг `diagnostic_only`.
4. Feature builder теперь возвращает `selection_meta`:
   - `candidate_count_before_cap`
   - `selected_count_after_cap`
   - `is_truncated`
5. `compute_profile_coverage()` переведён на честную truncation-метрику:
   - `is_truncated = candidate_count_before_cap > seq_len`
6. Добавлены 4 full-corridor профиля:
   - `corridor_5atr_relative_price_no_time_full`
   - `corridor_10atr_relative_price_no_time_full`
   - `corridor_5atr_relative_price_atr_full`
   - `corridor_10atr_relative_price_atr_full`
7. `*_no_time_full` заданы с `row_dim=0` и помечены как `DIAGNOSTIC_ONLY`.
8. Добавлены тесты на naming/contract, raw coverage, full-corridor shapes и честную truncation.

## Changed Files

- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `tests/test_stage5_transformer_breach.py`
- `docs/ML/benchmark_stage5_transformer_breach.py.md`
- `MODULE_INDEX.md`
- `CONTEXT_HANDOFF.md`

## Verification

```bash
~/git/SoSimple/.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -q
~/git/SoSimple/.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --feature-preflight-only
```

Результат:
- `72 passed`
- preflight завершён успешно, без запуска обучения

## Artifacts

- `ML/reports/stage5_0a_feature_preflight.json`
- `ML/reports/stage5_0a_feature_stats_normalized.csv`
- `ML/reports/stage5_0a_profile_summary.csv`

## Stage 5.0a Main Summary

| Профиль | Статус | Ключевой вывод |
|---|---|---|
| `time_only_clean` | `OK` | чистый календарный контроль, без ATR |
| `atr_only` | `WARNING` | общий holdout shift по ATR |
| `time_plus_atr` | `WARNING` | тот же ATR shift |
| `all100_absolute_price_time` | `WARNING` | кроме ATR shift есть shift по абсолютной цене |
| `all100_no_price_time` | `WARNING` | warning идёт от ATR holdout shift |
| `all100_relative_price_no_time` | `WARNING` | train/val чистые, хвосты малы |
| `all100_relative_price_time` | `WARNING` | train/val чистые, хвосты малы |
| `nearest40_relative_price_no_time` | `WARNING` | train/val чистые, без truncation |
| `nearest40_relative_price_time` | `WARNING` | train/val чистые, без truncation |
| `corridor_5atr_relative_price_no_time` | `WARNING` | профиль часто обрезается cap=40 |
| `corridor_10atr_relative_price_no_time` | `WARNING` | профиль почти всегда обрезается cap=40 |
| `corridor_15atr_relative_price_no_time` | `WARNING` | профиль почти всегда обрезается cap=40 |
| `corridor_10atr_relative_price_time` | `WARNING` | те же проблемы truncation, плюс время |

Главные выводы базового preflight:

1. Технических блокеров нет: `NaN`, `Inf`, `PADDING_NOT_ZERO`, contract-break не найдены.
2. `time_only_clean` теперь действительно чистый.
3. `all100_absolute_price_time` оставлен только как диагностический контроль.
4. Лучшие кандидаты на rerun без corridor-addendum:
   - `all100_no_price_time`
   - `all100_relative_price_no_time`
   - `all100_relative_price_time`
   - `nearest40_relative_price_no_time`
   - `nearest40_relative_price_time`

## Stage 5.0a Addendum: Corridor Full Preflight

### Зачем нужен addendum

Первый Stage 5.0a показал, что corridor-профили обрезаются при `seq_len=40`, но старая метрика не отделяла:

- сколько фракталов реально попало в corridor;
- сколько фракталов осталось после cap.

Теперь это разделено честно:

- `candidate_count_before_cap` = сколько фракталов реально попало в corridor;
- `selected_count_after_cap` = сколько реально ушло в модель;
- truncation = только строки, где `candidate_count_before_cap > seq_len`.

### Важный методический нюанс про ATR

Нужно различать две роли ATR:

1. ATR как единица масштаба внутри `price_coord_atr`:
   - это способ выразить расстояние по цене в “сколько ATR”.
2. ATR как отдельный вход модели в `row_fields`:
   - это уже отдельный признак, который модель видит напрямую.

Поэтому:

- `corridor_*_atr_full` нужны для честного сравнения со старым профилем;
- `corridor_*_no_time_full` нужны как чистый диагностический контроль без `ATR` во входе модели.

### Честное сравнение: старый corridor vs full corridor с ATR-входом

| Сравнение | Train median raw candidates | Train median selected | True truncation |
|---|---:|---:|---:|
| `corridor_5atr_relative_price_no_time` | 40 | 40 | 0.491 |
| `corridor_5atr_relative_price_atr_full` | 40 | 40 | 0.000 |
| `corridor_10atr_relative_price_no_time` | 62 | 40 | 0.871 |
| `corridor_10atr_relative_price_atr_full` | 62 | 62 | 0.000 |

Смысл:

- `corridor_5atr`: снятие cap почти ничего не меняет в медиане. Коридор сам по себе уже узкий. Но около 49% строк всё же были реально обрезаны в старой версии.
- `corridor_10atr`: снятие cap меняет представление существенно. Старая версия видела только 40 токенов, а full-версия в медиане видит 62.

### Новый диагностический контроль: corridor без ATR как входа модели

| Профиль | `row_dim` | Train median raw candidates | Train median selected | True truncation | Статус |
|---|---:|---:|---:|---:|---|
| `corridor_5atr_relative_price_no_time_full` | 0 | 40 | 40 | 0.000 | `OK`, `DIAGNOSTIC_ONLY` |
| `corridor_10atr_relative_price_no_time_full` | 0 | 62 | 62 | 0.000 | `OK`, `DIAGNOSTIC_ONLY` |

Ограничение: эти профили не должны автоматически идти в training rerun. Причина простая: текущий модельный слой Stage 5 строит `nn.Linear(row_dim, ...)`, а `row_dim=0` здесь проверен только на preflight-пайплайне, без обучения.

### “Почти all100” — формальный контроль

| Профиль | `% rows with candidate_count_before_cap >= 90` | `% rows with selected_count_after_cap >= 90` |
|---|---:|---:|
| `corridor_5atr_relative_price_no_time_full` | 0.000 | 0.000 |
| `corridor_10atr_relative_price_no_time_full` | 0.0105 | 0.0105 |
| `all100_relative_price_no_time` | 1.000 | 1.000 |

Вывод: даже full `corridor_10atr` не превращается в фактический `all100`. Почти все строки всё ещё содержат заметно меньше 90 фракталов. Значит corridor сохраняет свой смысл как отдельное представление.

### Coverage по corridor после исправления метрики

| Профиль | Train p5 raw | Train p50 raw | Train p95 raw | True truncation |
|---|---:|---:|---:|---:|
| `corridor_5atr_relative_price_no_time` | 13 | 40 | 60 | 0.491 |
| `corridor_5atr_relative_price_no_time_full` | 13 | 40 | 60 | 0.000 |
| `corridor_10atr_relative_price_no_time` | 29 | 62 | 80 | 0.871 |
| `corridor_10atr_relative_price_no_time_full` | 29 | 62 | 80 | 0.000 |

Ключевой смысл:

- проблема `corridor_5atr` была умеренной: часть строк реально упиралась в cap, но сам профиль не становился почти `all100`;
- проблема `corridor_10atr` была сильной: старый профиль часто резал почти треть доступного corridor.

## Final Decision Gate

### Допустимы к обсуждению для training rerun

- `all100_no_price_time`
- `all100_relative_price_no_time`
- `all100_relative_price_time`
- `nearest40_relative_price_no_time`
- `nearest40_relative_price_time`
- `corridor_5atr_relative_price_atr_full`
- `corridor_10atr_relative_price_atr_full`

Причина: эти профили имеют обычный `row_dim`, честный coverage и больше не страдают от ложной truncation-метрики.

### Diagnostic-only

- `time_only_clean`
- `atr_only`
- `time_plus_atr`
- `all100_absolute_price_time`
- `corridor_5atr_relative_price_no_time_full`
- `corridor_10atr_relative_price_no_time_full`
- `corridor_15atr_relative_price_no_time`
- `corridor_10atr_relative_price_time`

Причины разные:

- clean-controls и absolute-price нужны как контроль;
- `*_no_time_full` имеют `row_dim=0`;
- `corridor_15atr_relative_price_no_time` всё ещё слишком широк и остаётся методически спорным;
- `corridor_10atr_relative_price_time` добавляет время поверх уже спорного corridor-сравнения.

### Исключить как основной обучающий кандидат

- `all100_absolute_price_time`
- старые capped-профили:
  - `corridor_5atr_relative_price_no_time`
  - `corridor_10atr_relative_price_no_time`

Причина: теперь есть более честные full-версии; старые capped-представления больше не нужны как основной вариант rerun.

## Related Materials

- `ML/reports/stage5_0a_feature_preflight.json`
- `ML/reports/stage5_0a_feature_stats_normalized.csv`
- `ML/reports/stage5_0a_profile_summary.csv`
- `docs/reports/2026-06-17-stage5-transformer-breach.md`
