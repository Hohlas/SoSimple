# Signal Export Parity Benchmark

> **Date**: 2026-04-22
> **Status**: Completed
> **Goal**: Закрыть расхождение между количеством строк в exported `ml_signals.csv` и количеством сделок, реально открытых MT4.
> **Related commit**: 2b8d1c8

## Context

После MT4-подтверждения `original_plus_path_seq50` возникло видимое расхождение:

- Python/export давал `51` ненулевую строку в `ml_signals.csv`;
- MT4 tester открыл `29` сделок.

Причина не в ошибке `lib_PIC`: `Nero.csv` ожидаемо может иметь несколько строк с одинаковым временем, если на одном баре сформированы разные пики/уровни. Эти строки нельзя схлопывать в DATA, потому что у них разные `Dir`, цена пика, `Back`, `Front` и другие признаки.

Проблема была не исследовательская, а диагностическая: нужен инструмент, который явно показывает разные уровни детализации.

## What Was Done

Добавлен модуль:

- `ML/benchmark_signal_export_parity.py`

Добавлены тесты:

- `tests/test_signal_export_parity.py`

Добавлена документация:

- `docs/ML/benchmark_signal_export_parity.py.md`

Инструмент считает:

- всего строк в `ml_signals.csv`;
- ненулевых строк;
- уникальных `time`;
- уникальных пар `time + signal`;
- повторов `time`;
- повторов `time + signal`;
- случаи противоположных сигналов на одном времени;
- количество `MLP BUY/SELL` событий в MT4 log;
- финальную MLP-диагностику MT4.

## Verification

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_signal_export_parity.py -q
```

Результат:

```text
3 passed
```

Фактический запуск:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_signal_export_parity \
  --signals MT/tester/files/ml_signals.csv \
  --mt4-log MT/tester/logs/20260420.log \
  --output-dir ML/reports/signal_export_parity/original_plus_path_20260420 \
  --label original_plus_path_20260420
```

## Results

Export structure:

| Metric | Value |
|---|---:|
| rows_total | 9378 |
| nonzero_rows | 51 |
| long_rows | 38 |
| short_rows | 13 |
| unique_time_total | 8872 |
| nonzero_unique_time | 37 |
| nonzero_unique_time_signal | 37 |
| duplicate_time_rows | 14 |
| duplicate_time_signal_rows | 14 |
| same_time_opposite_signal_groups | 0 |

MT4 structure:

| Metric | Value |
|---|---:|
| opened_trades_from_events | 29 |
| opened_buy_from_events | 16 |
| opened_sell_from_events | 13 |
| unique_signal_times_opened | 29 |
| diagnostics.total_signals | 29 |
| diagnostics.score_filtered | 0 |
| diagnostics.position_blocked | 0 |
| diagnostics.opened | 29 |
| diagnostics.trailing_closes | 29 |

Comparison:

| Metric | Value |
|---|---:|
| nonzero_rows_minus_opened_events | 22 |
| unique_time_minus_opened_events | 8 |
| unique_time_signal_minus_opened_events | 8 |
| mt4_diagnostics_opened_minus_opened_events | 0 |

Duplicate `time+signal` examples:

- `2023.01.12 16:00`, signal `1`, rows `2`;
- `2025.05.15 09:00`, signal `1`, rows `2`;
- `2025.08.20 04:00`, signal `1`, rows `2`.

## Conclusions

1. `Nero.csv` / DATA duplicate timestamps are expected.

Один H1-бар может сформировать несколько разных пиков/уровней. Эти строки нельзя удалять из DATA.

2. MT4 signal execution работает на уровне `time;signal`.

В текущем runtime-формате нет row id или id пика. Поэтому несколько одинаковых `time;signal` в export не становятся несколькими отдельными сделками в MT4.

3. Расхождение по 51 vs 29 теперь объяснено численно.

Из `51` ненулевой строки:

- `14` строк — повторы того же `time+signal`;
- остаётся `37` уникальных `time+signal`;
- MT4 открыл `29` сделок в tester interval;
- ещё `8` уникальных сигналов не попали в MT4-opened events из-за границ периода/исполнительного контура, но не из-за score/position фильтров.

4. `original_plus_path_seq50` MT4-verdict не меняется.

MT4 log подтверждает:

- `Position blocked=0`;
- `Score filtered=0`;
- `Opened=29`;
- `Trailing closes=29`.

Parity benchmark уточняет интерпретацию количества сделок, но не отменяет положительный MT4 результат.

## Next Step

Теперь можно переходить к roadmap item 5: cross-instrument robustness check.

Перед этим для каждого нового MT4-сигнала нужно запускать `benchmark_signal_export_parity.py`, чтобы отчёт сразу показывал:

- строковую частоту export;
- уникальные времена;
- MT4-opened trades.

## Related Materials

- `ML/benchmark_signal_export_parity.py`
- `docs/ML/benchmark_signal_export_parity.py.md`
- `ML/reports/signal_export_parity/original_plus_path_20260420/summary.json`
- `ML/reports/signal_export_parity/original_plus_path_20260420/summary.md`
- `docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md`
