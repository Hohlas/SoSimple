# Stage 5.0a Feature Preflight

> **Date**: 2026-06-18
> **Status**: Completed (`DIAGNOSTIC_ONLY`)
> **Goal**: Проверить финальные входы Stage 5.0 до обучения Transformer: clean-controls, абсолютную цену, `relative_price`, `nearest40`, `corridor` и нормализацию.
> **Related plan/spec**: `docs/superpowers/plans/2026-06-18-stage5_0a-feature-preflight.md`
> **Related commit**: pending

## Context

Stage 5.0 дал `DIAGNOSTIC_FAIL_WITH_PREPROCESSING_BUG`: старый прогон Transformer был выполнен без фактической нормализации финальных признаков. Перед повторным обучением требовалось доказать, что новый feature builder строит корректные профили, scaler fit-ится только на train, padding остаётся нулём, а clean-controls действительно чистые.

## What Was Done

1. В `ML/baseline/benchmark_stage5_transformer_breach.py` добавлен режим `--feature-preflight-only`.
2. Зафиксирована матрица из 13 профилей Stage 5.0a: clean-controls, `all100_*`, `nearest40_*`, `corridor_*`.
3. Добавлены profile contracts: `selector`, `token_fields`, `row_fields`, `token_order`, `seq_len`, `padding_value`, `mask_semantics`.
4. Исправлен контракт `nearest40_*`: `fractal0` используется как anchor и не входит в 40 соседей.
5. Добавлены тесты контрактов, порядка токенов, формулы `price_coord_atr`, corridor-границ и padding.
6. Запущен preflight без обучения; сохранены JSON и две CSV с аудитом распределений.

## Changed Files

- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `ML/models/fractal_breach_transformer.py`
- `tests/test_stage5_transformer_breach.py`
- `docs/ML/benchmark_stage5_transformer_breach.py.md`
- `MODULE_INDEX.md`

## Verification

```bash
~/git/SoSimple/.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -q
~/git/SoSimple/.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --feature-preflight-only
```

Результат:
- `64 passed`
- preflight завершён за `1m21s`

## Results

### Артефакты

- `ML/reports/stage5_0a_feature_preflight.json`
- `ML/reports/stage5_0a_feature_stats_normalized.csv`
- `ML/reports/stage5_0a_profile_summary.csv`

### Сводка по профилям

| Профиль | Статус | Ключевой вывод |
|---|---|---|
| `time_only_clean` | `OK` | чистый календарный контроль, без ATR |
| `atr_only` | `WARNING` | сильный holdout regime shift по ATR |
| `time_plus_atr` | `WARNING` | тот же ATR shift, ожидаемо |
| `all100_absolute_price_time` | `WARNING` | кроме ATR shift есть regime shift по абсолютной цене |
| `all100_no_price_time` | `WARNING` | технически чисто; warning идёт только от ATR holdout shift |
| `all100_relative_price_no_time` | `WARNING` | train/val чистые, хвосты малы |
| `all100_relative_price_time` | `WARNING` | train/val чистые, хвосты малы |
| `nearest40_relative_price_no_time` | `WARNING` | train/val чистые, без truncation |
| `nearest40_relative_price_time` | `WARNING` | train/val чистые, без truncation |
| `corridor_5atr_relative_price_no_time` | `WARNING` | coverage хороший, но truncation ~52% на train |
| `corridor_10atr_relative_price_no_time` | `WARNING` | coverage высокий, но truncation ~88% на train |
| `corridor_15atr_relative_price_no_time` | `WARNING` | coverage высокий, но truncation ~97% на train |
| `corridor_10atr_relative_price_time` | `WARNING` | те же проблемы truncation, что и без времени |

### Худшие признаки по audit

- Главный источник warning во всех рабочих профилях: `ATR` на holdout.
  - `frac_abs_gt10 = 0.060968`
  - `max = 32.8649`
  - `TAIL_GT20 = 0.013033`
- `all100_absolute_price_time` дополнительно получил `REGIME_SHIFT` по token `price`.
- У `relative_price` хвосты на train малы:
  - `all100_relative_price_*`: `frac_abs_gt10 = 0.001094`
  - `nearest40_relative_price_*`: `frac_abs_gt10 = 0.000024`

### Corridor coverage

| Профиль | Train p5 | Train p50 | Train truncation |
|---|---:|---:|---:|
| `corridor_5atr_relative_price_no_time` | 13 | 40 | 0.519 |
| `corridor_10atr_relative_price_no_time` | 29 | 40 | 0.880 |
| `corridor_15atr_relative_price_no_time` | 40 | 40 | 0.967 |

Важно: проблема corridor сейчас не в пустых строках. Наоборот, фракталов слишком много, и профиль почти всегда режется по `seq_len=40`. Значит, `corridor_10atr` и тем более `corridor_15atr` в текущем виде не являются чистым представлением всего коридора.

## Conclusions

1. **Технических блокеров нет.** `NaN`, `Inf`, `PADDING_NOT_ZERO` и нарушения contract не обнаружены.
2. **`time_only_clean` теперь действительно чистый.** Старое смешение времени и ATR устранено.
3. **Абсолютная цена остаётся только диагностическим контролем.** На holdout у неё виден regime shift; как основной кандидат её использовать нельзя.
4. **Лучшие кандидаты на rerun — `relative_price` и `nearest40_relative_price`.** У них чистый contract, малые train-хвосты и нет truncation.
5. **Corridor-профили в текущем виде требуют осторожности.** Они не пустые, но слишком часто обрезаются. Это искажает смысл профиля.

## Limitations / Open Questions

1. Warning по ATR сформирован на holdout disclosure. По правилам Stage 5.0a это не должно само по себе запрещать rerun, но должно быть зафиксировано в отчёте.
2. Для corridor остаётся открытым вопрос: увеличивать `seq_len`, сужать коридор или менять правило отбора. Без этого `corridor_10atr/15atr` смешивают corridor-идею и жёсткий top-40 cap.
3. В этом этапе не тестировались торговые метрики и не запускалось обучение.

## Next Step

1. Остановиться на human review.
2. Для Stage 5.0 rerun разрешить только профили без методического конфликта:
   - `time_only_clean`
   - `atr_only`
   - `time_plus_atr`
   - `all100_no_price_time`
   - `all100_relative_price_no_time`
   - `all100_relative_price_time`
   - `nearest40_relative_price_no_time`
   - `nearest40_relative_price_time`
3. Не включать в rerun:
   - `all100_absolute_price_time` как обучающий кандидат
   - `corridor_10atr_relative_price_*` и `corridor_15atr_relative_price_no_time` до решения по truncation
4. `corridor_5atr_relative_price_no_time` можно оставить только как дополнительный diagnostic-кандидат, не как основной профиль.

## Related Materials

- `docs/superpowers/plans/2026-06-18-stage5_0a-feature-preflight.md`
- `ML/reports/stage5_0a_feature_preflight.json`
- `ML/reports/stage5_0a_feature_stats_normalized.csv`
- `ML/reports/stage5_0a_profile_summary.csv`
- `docs/reports/2026-06-17-stage5-transformer-breach.md`
