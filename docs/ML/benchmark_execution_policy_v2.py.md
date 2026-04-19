# benchmark_execution_policy_v2.py

## Назначение

`ML/benchmark_execution_policy_v2.py` сравнивает варианты выхода для уже готовых ML-сигналов без нового обучения и без запуска MT4.

Цель модуля — быстро понять, что даёт лучший баланс между прибылью, просадкой, гладкостью equity curve и зависимостью от крупных сделок.

## Входные данные

- `MT/tester/files/ml_signals_quality.csv` — более редкий набор сигналов.
- `MT/tester/files/ml_signals_frequency.csv` — более частый набор сигналов.
- `DATA/XAUUSD_H1_OHLC.csv` — H1 OHLC и `atr14`.

По умолчанию период ограничен:

```text
2023-01-01 <= signal_time < 2026-01-01
```

Это соответствует последним ручным MT4-прогонам.

## Проверяемые выходы

- `trail_x6 / trail_x8 / trail_x10` — чистый трейлинг без take profit.
- `trail_x8` — чистый трейлинг `8 ATR`.
- `trail_x8_tp8/12/16/24` — трейлинг `8 ATR` плюс take profit.
- `stop_x8_tp8/12/16/24` — стартовый стоп `8 ATR` плюс take profit без трейлинга.
- `shrinking_trail_8_6_4_3` — широкий стартовый трейлинг, который сужается при росте накопленной прибыли.

## Метрики

- `pf`
- `net_atr`
- `max_drawdown_atr`
- `ulcer_index_atr`
- `equity_linearity_r2`
- `profit_concentration_top_1/3/10`
- `negative_months`
- `negative_years`
- `worst_trade_atr`
- `best_trade_atr`
- `max_consecutive_losses`
- `max_consecutive_loss_atr`
- `max_consecutive_wins`
- `max_consecutive_win_atr`
- `avg_hold_hours`

Результаты нормируются в ATR на входе сделки, чтобы сравнение не зависело от абсолютного уровня цены XAUUSD в разные годы.

## Запуск

```bash
python -m ML.benchmark_execution_policy_v2
```

Опционально:

```bash
python -m ML.benchmark_execution_policy_v2 \
  --start 2023-01-01 \
  --end 2026-01-01 \
  --output-dir ML/reports/execution_policy_v2
```

Узкий прогон только для частого набора сигналов и чистого трейлинга:

```bash
python -m ML.benchmark_execution_policy_v2 \
  --policy-set frequency_trail_scan \
  --datasets frequency \
  --output-dir ML/reports/execution_policy_v2/frequency_trail_scan
```

## Выходные файлы

- `ML/reports/execution_policy_v2/summary.csv`
- `ML/reports/execution_policy_v2/summary.json`
- `ML/reports/execution_policy_v2/trades.csv`

Для узкого прогона `frequency_trail_scan`:

- `ML/reports/execution_policy_v2/frequency_trail_scan/summary.csv`
- `ML/reports/execution_policy_v2/frequency_trail_scan/summary.json`
- `ML/reports/execution_policy_v2/frequency_trail_scan/trades.csv`

## Ограничения

Это OHLC-симуляция, а не точная копия MT4 tester. Внутри одного бара порядок `high/low` неизвестен, поэтому результат нужно использовать для research-сравнения вариантов выхода, а выбранные варианты отдельно проверять в MT4.
