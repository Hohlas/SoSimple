# benchmark_signal_export_parity.py

## Назначение

`ML/benchmark_signal_export_parity.py` проверяет, как exported `ml_signals.csv` соотносится с MT4 tester log.

Инструмент нужен для случаев, когда Python benchmark считает строки датасета, а MT4 исполняет сигналы по времени бара.

## Что считает

По `ml_signals.csv`:

- всего строк;
- ненулевых строк;
- уникальных `time` среди ненулевых сигналов;
- уникальных пар `time + signal`;
- количество повторов одного `time`;
- количество повторов одной пары `time + signal`;
- случаи, где на одно время есть противоположные сигналы.

По MT4 log:

- количество строк `MLP BUY/SELL`;
- количество BUY/SELL;
- уникальные `signal_time`;
- финальную MLP-диагностику:
  - `Total signals`;
  - `Score filtered`;
  - `Position blocked`;
  - `Opened`;
  - `Trailing closes`.

## Запуск

```bash
python -m ML.benchmark_signal_export_parity \
  --signals MT/tester/files/ml_signals.csv \
  --mt4-log MT/tester/logs/20260420.log \
  --output-dir ML/reports/signal_export_parity/original_plus_path_20260420 \
  --label original_plus_path_20260420
```

Без MT4 log:

```bash
python -m ML.benchmark_signal_export_parity \
  --signals MT/tester/files/ml_signals.csv \
  --output-dir ML/reports/signal_export_parity/current_export_only
```

## Выходные файлы

- `summary.json` — машинно-читаемый результат.
- `summary.md` — компактная таблица для чтения.

## Ограничения

Инструмент ничего не меняет в signal CSV:

- не удаляет дубли;
- не схлопывает несколько пиков одного бара;
- не пересчитывает торговую статистику.

Он только показывает, где расходятся уровни детализации:

- ML/export: строка датасета;
- MT4 direct execution: сигнал по времени бара.
