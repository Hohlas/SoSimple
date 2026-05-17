# Entry Path Direct Bar Model

> **Date**: 2026-05-14
> **Status**: Completed
> **Goal**: Проверить модель, которая сама выдаёт score и direction для каждого бара.
> **Related plan/spec**: direct user request
> **Related commit**: pending

## Context

Предыдущие проверки показали:

- offline `signal != 0` сам по себе убыточен;
- all-rows ranking со старым `pred_ret_24_dir_atr` не переносится на все бары;
- causal surrogate даёт слабоположительный результат, но плохо отделяет active
  candidate.

Третий вариант - убрать зависимость от offline `signal` как candidate-source и
обучить модель сразу на `BUY / SELL / SKIP` для каждого бара.

## What Was Done

Добавлен benchmark:

- `ML/benchmark_entry_path_direct_bar_model.py`;
- `tests/test_benchmark_entry_path_direct_bar_model.py`;
- `docs/ML/benchmark_entry_path_direct_bar_model.py.md`.

Цель для обучения строится по OHLC:

- вход: open следующего бара;
- выход: close через `24` бара;
- `BUY`, если buy-return >= `0.25` ATR и лучше sell-return;
- `SELL`, если sell-return >= `0.25` ATR и лучше buy-return;
- иначе `SKIP`.

Признаки:

- `ATR`;
- `session_hour`;
- `weekday`;
- текущий `fractal0`: direction, front, back, strong, break, reverse, power,
  count, impulse, fractal ATR.

Не используются как признаки: `signal`, `predict`, `ret_*`, `fav_*`, `adv_*`.

## Changed Files

- `ML/benchmark_entry_path_direct_bar_model.py`
- `tests/test_benchmark_entry_path_direct_bar_model.py`
- `docs/ML/benchmark_entry_path_direct_bar_model.py.md`
- `ML/reports/entry_path_v1_direct_bar_model/summary.json`
- `ML/reports/entry_path_v1_direct_bar_model/summary.md`
- `ML/reports/entry_path_v1_direct_bar_model/validation_summary.csv`
- `ML/reports/entry_path_v1_direct_bar_model/test_selected_rows.csv`
- `MODULE_INDEX.md`
- `ML/README.md`

## Verification

Команды:

```bash
./.venv/bin/python -m pytest tests/test_benchmark_entry_path_direct_bar_model.py -q
./.venv/bin/python -m ML.benchmark_entry_path_direct_bar_model
```

## Results

Validation winner:

| Metric | Value |
|---|---:|
| probability threshold | 0.80 |
| trades | 1450 |
| PF | 1.1673 |
| win rate | 51.17% |
| mean pnl ATR | 0.2392 |
| active precision | 93.52% |
| active recall | 15.47% |
| correct signal precision | 47.45% |

Frozen test:

| Metric | Value |
|---|---:|
| trades | 1277 |
| PF | 1.1141 |
| win rate | 48.24% |
| mean pnl ATR | 0.1631 |
| active precision | 90.05% |
| active recall | 13.89% |
| correct signal precision | 45.50% |

Sequential test (`hold_bars=24`):

| Metric | Value |
|---|---:|
| trades | 274 |
| PF | 1.1334 |
| win rate | 45.26% |
| mean pnl ATR | 0.1660 |

## Conclusions

Прямая модель выглядит лучше all-rows ranking и даёт положительный frozen test
без offline `signal != 0` gate. Это подтверждает, что production-контур лучше
строить как прямой `score + direction` по каждому бару.

Но результат пока слабый:

- PF test только `1.1141`;
- один отрицательный год на test (`2022`);
- направление среди выбранных active-строк почти случайное (`~50.5%`);
- правильный полный сигнал среди выбранных строк только `45.50%`.

## Limitations / Open Questions

- Использован простой RandomForestClassifier, не основной neural checkpoint.
- Цель задана простым fixed-horizon close-return, без комиссии, спреда и
  реального MT4 исполнения.
- Нет калибровки под частоту сделок и drawdown.
- Нужна следующая итерация: обучить production-модель на той же постановке
  `BUY / SELL / SKIP`, затем прогнать MT4 parity.

## Related Materials

- `ML/reports/entry_path_v1_direct_bar_model/summary.md`
- `docs/reports/2026-05-14-entry-path-causal-surrogate.md`
- `docs/reports/2026-05-14-entry-path-all-rows-ranking.md`
