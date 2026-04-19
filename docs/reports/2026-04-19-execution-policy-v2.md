# Execution Policy v2: Python + MT4 Verdict

> **Date**: 2026-04-19 13:53
> **Status**: Completed
> **Goal**: Проверить варианты выхода для готовых `quality` и `frequency` ML-сигналов без нового обучения, затем подтвердить ключевые варианты в MT4.
> **Related plan/spec**: `docs/reports/2026-04-18-take-skip-frequency-followup.md`, `docs/reports/2026-04-18-take-skip-rule-consumer.md`, `docs/reports/2026-04-18-mt4-trailing-stop-execution.md`
> **Related commit**: pending

## Context

После `take_skip_trailing_stop_v2` появились два рабочих набора сигналов:

- `quality` — реже, но с очень высоким PF;
- `frequency` — чаще, но сильнее зависит от политики выхода.

MT4 уже умел исполнять прямые ML-сигналы с trailing-stop через `ML_ExitMode=1` и `ML_TrailATR`, но не было отдельного инструмента для честного сравнения вариантов выхода по форме equity. Простого сравнения net profit и PF недостаточно: оно может выбрать режим, который держится на одной редкой длинной сделке.

## What Was Done

- Добавлен `ML/benchmark_execution_policy_v2.py`.
- Добавлены тесты `tests/test_benchmark_execution_policy_v2.py`.
- Benchmark сравнивает варианты выхода на готовых CSV без нового обучения:
  - чистый трейлинг `trail_x6 / x8 / x10`;
  - трейлинг `x8` плюс take profit `8 / 12 / 16 / 24 ATR`;
  - простой stop + take profit;
  - сужающийся trailing-stop.
- Добавлены метрики устойчивости:
  - `max_drawdown_atr`;
  - `ulcer_index_atr`;
  - `equity_linearity_r2`;
  - `profit_concentration_top_1/3/10`;
  - `negative_months / negative_years`;
  - худшая сделка и худшая серия.
- В MT4 добавлен параметр `ML_TakeProfitATR`.
- В прямом ML-контуре `iSignal=3` take profit выставляется как обычный broker-side TP:
  - BUY: `entry + ATR * ML_TakeProfitATR`;
  - SELL: `entry - ATR * ML_TakeProfitATR`;
  - `ML_TakeProfitATR=0` отключает TP.

## Changed Files

- `ML/benchmark_execution_policy_v2.py` — новый benchmark вариантов выхода.
- `tests/test_benchmark_execution_policy_v2.py` — unit tests.
- `ML/reports/execution_policy_v2/` — результаты Python-прогонов.
- `MT/MQL4/Experts/$o$imple.mq4` — добавлен внешний параметр `ML_TakeProfitATR`.
- `MT/MQL4/Include/lib_ML_Signal.mqh` — take profit протянут в прямой ML execution.
- `ML/README.md`, `MODULE_INDEX.md`, `docs/ML/benchmark_execution_policy_v2.py.md` — индекс и документация нового benchmark.

## Verification

```bash
./.venv/bin/python -m pytest tests/test_benchmark_execution_policy_v2.py -q
# 2 passed

./.venv/bin/python -m ML.benchmark_execution_policy_v2 \
  --output-dir ML/reports/execution_policy_v2

./.venv/bin/python -m ML.benchmark_execution_policy_v2 \
  --policy-set frequency_trail_scan \
  --datasets frequency \
  --output-dir ML/reports/execution_policy_v2/frequency_trail_scan
```

MT4 проверялся вручную на периоде `2023-2026`, `Risk=0`, `ML_MaxPositions=100`, `ML_UseScoreFilter=false`, `ML_AllowReversal=false`.

## Python Results

### Quality

Основной вывод: `quality` выдерживает take profit лучше, чем `frequency`.

| Policy | Trades | PF | Net ATR | Max DD ATR | R2 | Top 3 Concentration |
|---|---:|---:|---:|---:|---:|---:|
| `trail_x8` | 20 | 55.87 | 194.90 | 3.55 | 0.951 | 50.9% |
| `trail_x8_tp12` | 20 | 50.42 | 175.57 | 3.55 | 0.994 | 20.1% |

`trail_x8_tp12` снижает зависимость от крупнейших сделок и делает equity заметно ровнее, но сохраняет высокий PF.

### Frequency

Узкий прогон `frequency_trail_scan`:

| Policy | Trades | PF | Net ATR | Max DD ATR | Ulcer | R2 | Top 1 | Top 3 | Negative Months |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `trail_x6` | 56 | 4.08 | 169.72 | 18.00 | 5.79 | 0.821 | 13.8% | 37.3% | 8 |
| `trail_x8` | 56 | 3.73 | 215.77 | 22.54 | 7.28 | 0.766 | 18.9% | 38.1% | 9 |
| `trail_x10` | 56 | 4.12 | 323.09 | 39.66 | 16.52 | 0.564 | 30.3% | 56.7% | 12 |

Интерпретация:

- `trail_x6` — самый ровный и осторожный.
- `trail_x8` — лучший баланс прибыли и устойчивости.
- `trail_x10` — максимальная прибыль, но сильная зависимость от редких крупных сделок.

## MT4 Results

### Quality

| Mode | Net Profit | Trades | PF | Max Relative DD | Max Win |
|---|---:|---:|---:|---:|---:|
| `TrailATR=8, TP=0` | 18037.59 | 20 | 51.95 | 11.70% | 7996.90 |
| `TrailATR=8, TP=12` | 11544.89 | 20 | 33.61 | 4.97% | 1817.00 |

Вывод: TP=12 резко снижает зависимость от одной большой сделки и уменьшает просадку, но забирает часть прибыли.

### Frequency

| Mode | Net Profit | Trades | PF | Max Relative DD |
|---|---:|---:|---:|---:|
| `TrailATR=6, TP=0` | 18455.93 | 56 | 4.22 | 16.78% |
| `TrailATR=8, TP=0` | 24521.88 | 56 | 3.77 | 25.71% |
| `TrailATR=10, TP=0` | 26137.10 | 56 | 3.31 | 27.44% |
| `TrailATR=12, TP=0` | 21958.91 | 56 | 2.72 | 29.70% |
| `TrailATR=8, TP=12` | 12085.05 | 56 | 2.37 | 17.27% |

Вывод: для `frequency` take profit режет главный источник прибыли сильнее, чем улучшает устойчивость. Лучшие кандидаты — чистый trailing без TP.

## Conclusions

- `ML_TakeProfitATR` полезен как проверяемый механизм выхода, но не должен быть включён по умолчанию для `frequency`.
- Для `quality` вариант `TrailATR=8, TakeProfitATR=12` выглядит как более ровная версия с меньшей зависимостью от экстремальной сделки.
- Для `frequency` основной practical candidate: `TrailATR=8, TakeProfitATR=0`.
- Осторожный frequent candidate: `TrailATR=6, TakeProfitATR=0`.
- `TrailATR=10` не выбран основным, потому что выигрыш в прибыли сопровождается ухудшением формы equity: выше просадка, выше ulcer index, хуже линейность, выше концентрация прибыли.

## Limitations / Open Questions

- Python benchmark — это OHLC-симуляция, не точная копия MT4 tester. Внутри одного бара неизвестен порядок high/low.
- MT4-результаты получены вручную и не сохранены как machine-readable отчёт из tester.
- `ML_MaxPositions=100` использовался как аварийный потолок, а не как торговое правило.
- Money management намеренно не включался: на исследовательском этапе используется fixed lot.

## Next Step

1. Для `frequency` считать основным MT4-кандидатом `ML_TrailATR=8`, `ML_TakeProfitATR=0`.
2. Держать `ML_TrailATR=6`, `ML_TakeProfitATR=0` как осторожную альтернативу.
3. Не продолжать подбор take profit для `frequency`, пока не появится новая причина.
4. Следующий крупный шаг — искать независимую некоррелированную торговую систему, а не выжимать ещё один параметр из этого же набора сигналов.

## Related Materials

- `ML/benchmark_execution_policy_v2.py`
- `ML/reports/execution_policy_v2/summary.csv`
- `ML/reports/execution_policy_v2/frequency_trail_scan/summary.csv`
- `docs/reports/2026-04-18-take-skip-frequency-followup.md`
- `docs/reports/2026-04-18-take-skip-rule-consumer.md`
- `docs/reports/2026-04-18-mt4-trailing-stop-execution.md`
