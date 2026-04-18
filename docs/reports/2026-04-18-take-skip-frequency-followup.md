# Take/Skip Frequency Follow-Up

> **Date**: 2026-04-18 18:40
> **Status**: Completed
> **Goal**: Проверить, можно ли на уже обученном `take_skip_trailing_stop_v2` увеличить частоту сделок и аккуратно пощупать более широкий trailing-stop `10 / 12 ATR` без нового цикла обучения.
> **Related plan/spec**: `docs/superpowers/plans/2026-04-18-take-skip-frequency-followup.md`
> **Related commit**: fa343b3

## Context

Предыдущий этап `multi-horizon take-skip feature track` впервые дал валидный `go`: лучший кандидат был `seq50 + take_24_x8 + prob_ge_threshold >= 0.70`.

После этого остались два практических вопроса:

- можно ли получить заметно больше сделок, даже ценой снижения PF;
- помогает ли более широкий trailing-stop `10 / 12 ATR`, если не переобучать модель, а использовать уже найденный score-контур.

Ключевое ограничение: в репозитории не было сохранённых `take_skip_trailing_stop_v2_*_predictions.csv`. Поэтому follow-up пришлось строить не на старом runner, а через локальное восстановление score из checkpoint без обучения.

## What Was Done

- Расширен trailing-stop grid в labels:
  - `processing/label_signals.py`
  - `tests/test_trailing_stop_target_labels.py`
- Расширен `take_skip_trailing_stop_v2` target contract до `x10 / x12`:
  - `ML/take_skip_trailing_stop_v2_task.py`
  - `tests/test_take_skip_trailing_stop_v2_task.py`
- Восстановлен общий benchmark-helper слой:
  - `ML/benchmark_take_skip_trailing_stop.py`
- Добавлен отдельный follow-up benchmark:
  - `ML/benchmark_take_skip_trailing_stop_v2_followup.py`
  - `tests/test_benchmark_take_skip_trailing_stop_v2_followup.py`
- Локально восстановлены score для `seq50` из checkpoint `transformer_seq50/checkpoint.pt`:
  - без обучения;
  - с тем же входным представлением, под которое реально обучался checkpoint (`20 fractal features + multi-scale summaries + row-wise features = 539`);
  - `x10 / x12` рассчитаны поверх `DATA/XAUUSD_H1_OHLC.csv`.

## Changed Files

- `processing/label_signals.py`
- `ML/take_skip_trailing_stop_v2_task.py`
- `ML/benchmark_take_skip_trailing_stop.py`
- `ML/benchmark_take_skip_trailing_stop_v2_followup.py`
- `tests/test_trailing_stop_target_labels.py`
- `tests/test_take_skip_trailing_stop_v2_task.py`
- `tests/test_benchmark_take_skip_trailing_stop_v2_followup.py`
- `ML/reports/take_skip_trailing_stop_v2_followup/seq50/followup_summary.json`
- `ML/reports/take_skip_trailing_stop_v2_followup/seq50/validation_followup_grid.csv`

## Verification

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_trailing_stop_target_labels.py \
  tests/test_take_skip_trailing_stop_v2_task.py \
  tests/test_benchmark_take_skip_trailing_stop_v2.py \
  tests/test_benchmark_take_skip_trailing_stop_v2_followup.py -q

/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_take_skip_trailing_stop_v2_followup \
  --validation-csv ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/validation.csv \
  --test-csv ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/test.csv \
  --output-dir ML/reports/take_skip_trailing_stop_v2_followup/seq50 \
  --score-target take_24_x8 \
  --score-target take_24_x4 \
  --score-target take_24_x2
```

## Results

Базовый quality-first winner не изменился:

| Mode | score target | exit | selector | validation trades/year | validation PF | test trades/year | test PF |
|---|---|---|---|---:|---:|---:|---:|
| quality-first | `take_24_x8` | `x8` | `prob >= 0.70` | 6.75 | inf | 8.2 | 39.74 |

Новый frequency-first winner нашёлся:

| Mode | score target | exit | selector | validation trades | validation trades/year | validation PF | test trades | test trades/year | test PF |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| frequency-first | `take_24_x4` | `x10` | `top_k 20%` | 95 | 23.75 | 3.92 | 96 | 19.2 | 7.18 |

Структурные метрики для frequency-first:

- validation:
  - `negative_year_slices = 0`
  - `profit_concentration_top_10 = 0.304`
  - `max_drawdown_atr = 16.65`
- test:
  - `negative_year_slices = 1`
  - `profit_concentration_top_10 = 0.267`
  - `max_drawdown_atr = 8.97`

## Conclusions

- Без нового обучения удалось найти область с заметно большей частотой сделок.
- Компромисс выглядит реальным, а не косметическим:
  - `8.2 -> 19.2` сделок в год на test;
  - `PF` снижается, но остаётся сильно выше `1`.
- Более широкий trailing-stop `x10` оказался полезнее именно в frequency-first режиме.
- При этом цена за частоту понятна:
  - quality-first остаётся намного чище;
  - у frequency-first на test появляется `1` отрицательный годовой срез.

Итог: линия `take_skip_trailing_stop_v2` жива не только как high-PF low-frequency winner, но и как более частый рабочий режим. Однако frequency-first пока нельзя считать столь же устойчивым, как базовый quality-first winner.

## Limitations / Open Questions

- Follow-up был сделан только на базе лучшего контура `seq50`; `seq20/seq100` здесь не переоценивались.
- `x10 / x12` проверялись без переобучения: модель ранжировала по старым score-targets `x2 / x4 / x8`, а новый exit сравнивался уже после отбора.
- В репозитории по-прежнему нет канонически сохранённых `v2` prediction CSV; score пришлось локально восстановить из checkpoint.

## Next Step

Сделать короткий frozen follow-up вокруг двух режимов:

1. `quality-first`: оставить как основной чистый кандидат.
2. `frequency-first`: отдельно проверить, можно ли слегка ужать область (`top_k < 20%` или соседний threshold), чтобы снять отрицательный годовой срез и сохранить заметно больше сделок, чем у quality-first.

## Related Materials

- `docs/reports/2026-04-18-multi-horizon-take-skip-feature-track.md`
- `ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/summary.json`
- `ML/reports/take_skip_trailing_stop_v2_followup/seq50/followup_summary.json`
