# MT/

MetaTrader часть проекта: исходники торгового советника, MQL4/MQL5 библиотеки и файлы обмена с Python.

## Структура

```
MT/
├── MQL4/                # MetaTrader 4 — основная ветка проекта
│   ├── Experts/         #   Советник $o$imple.mq4 (торговый эксперт)
│   ├── Include/         #   Библиотеки .mqh — открывать только по #include-связи
│   ├── Indicators/      #   Индикаторы (.mq4/.ex4), включая iPIC — визуализация фракталов
│   ├── Scripts/         #   Скрипты: ExportOHLC, MATLABLOG, trade, PeriodConverter
│   ├── Libraries/       #   stdlib, stderror, Myfxbook.dll
│   ├── Files/           #   Файлы обмена ML↔MT4 (см. ниже)
│   └── (Logs, Profiles, Trash, Indicators/Examples, Scripts/Examples)
├── MQL5/                # MetaTrader 5 — порт $o$imple.mq5 (экспериментальный)
│   ├── Experts/
│   ├── Include/
│   └── Profiles/
├── tester/              # Файлы MT4 Strategy Tester
│   ├── files/           #   Входные/выходные файлы тестера (ml_signals.csv, ml_trade_events.csv, *.set)
│   ├── $o$imple.ini     #   Конфиг тестера
│   └── (lasttest.chr, lastparameters.ini, opt.set, check.txt)
├── ml_signals.csv       # Рабочая копия сигналов для MT4 (вне MQL4/Files)
└── #.csv                # Параметры оптимизации MT4 (opt-сеты в CSV)
```

## MQL4/Files/ — файлы обмена ML ↔ MT4

| Файл | Роль |
|------|------|
| `Nero.csv` | Исходный датасет от `lib_PIC.mqh` (фракталы) — источник для processing pipeline |
| `Nero_<SYMBOL>.csv` | Многоинструментные выгрузки (XAUUSD, EURUSD, GBPUSD, USDCHF, XAGUSD) |
| `ml_signals.csv` | ML-сигналы из Python → MT4 исполняет `lib_ML_Signal.mqh` |
| `ML_Trade_Events_*.csv` | Логи сделок для reconciliation (`signal_tracer.py`, `online_tester_reconciliation.py`) |
| `*_H1_OHLC.csv` | OHLC бары + atr14 для `API/signal_research.py` |
| `Demo_*.csv`, `ERROR_*.csv` | Диагностические выгрузки советника |
| `MatLabUSD.csv`, `Reports.csv` | Legacy/диагностика |

`tester/files/` — отдельная копия для Strategy Tester (`ml_signals.csv`, `Nero.csv`, `ml_trade_events.csv`, `*.set` opt-файлы). Файлы здесь изолированы от `MQL4/Files/` и нужны для запуска тестера под конкретный `Magic`.

## Правила для агентов

- Файлы `*.mqh`, `*.mq4`, `*.mq5` открывать точечно и только при явной `#include`-связи с текущим файлом или прямой задаче по торговому эксперту.
- `MQL5/` — экспериментальный порт; не трогать без явной просьбы.
- `tester/` — только для запуска MT4 Strategy Tester и reconciliation; не редактировать `.set`/`.ini` без явной просьбы.
- Файлы в `MQL4/Files/` и `tester/files/` — это runtime-данные, не исходники. Не редактировать вручную.

## Читать

- [`docs/MT/lib_PIC.mqh.md`](../docs/MT/lib_PIC.mqh.md) — формирование PIC-фракталов, `NERO_CSV_CREATE()`.
- [`docs/MT/ml_signal_integration.md`](../docs/MT/ml_signal_integration.md) — интеграция ML-сигналов с MT4, форматы `ml_signals.csv`, `iSignal` режимы.
- [`docs/MT/trading_strategy.md`](../docs/MT/trading_strategy.md) — полная торговая логика эксперта `MAIN()`.
- [`MT/MQL4/README.md`](MQL4/README.md) — детали MQL4-ветки.
