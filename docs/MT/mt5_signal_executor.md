# MT5 Signal Executor

> **Status**: diagnostic prototype.

## Purpose

Основная цель - проверить, может ли MT5 Strategy Tester исполнять entry-only
сигналы через существующий порт советника:

```text
MT/MQL5/Experts/$o$imple.mq5
```

Это не отдельный fallback expert. Диагностический путь встроен в текущий
`iSignal=3` / `ML_TRADE()` и по умолчанию выключен:

```text
InpMT5_DiagnosticExecutor=false
```

## Inputs

Включение режима:

```text
InpMT5_DiagnosticExecutor=true
InpMT5_EntrySignalFile=mt5_entry_signals.csv
InpMT5_EventFile=mt5_trade_events.csv
InpMT5_BlockBarsSinceFill0Exit=true
```

`mt5_entry_signals.csv` должен лежать в файловом каталоге MT5 tester `Files`.
Схема входного файла задана в:

```text
docs/schemas/mt5_signal_executor_schema.md
```

Обязательные поля:

```text
time;feature_time;feature_available_time;decision_time;rule_id;side;entry_type;limit_price;stop_price;atr;max_fill_lag_bars
```

Диагностический reader отдельный от legacy `ML_SIGNALS_FILE=ml_signals.csv`.
Если `InpMT5_DiagnosticExecutor=false`, старый reader `ML_INIT()` и старый
`ml_signals.csv` path остаются рабочим поведением `ML_TRADE()`.

## Execution

Диагностический путь читает строку по `decision_time` или `time`, совпадающему
с текущим рабочим баром `Time[bar]`.

Поддержаны только entry-only лимитные заявки:

```text
side=BUY,  entry_type=BUY_LIMIT или LIMIT
side=SELL, entry_type=SELL_LIMIT или LIMIT
```

Цена входа берётся только из `limit_price`, защитный стоп - только из
`stop_price`, срок жизни заявки - из `max_fill_lag_bars`. Значения не
выводятся из legacy `ml_signals.csv`.

Размещение идёт через существующий order path:

```text
set.BUY / set.SEL -> ORDERS_SET() -> SET_BUY() / SET_SEL()
```

Код не переписан на native `CTrade`, потому что текущий MT5 порт использует
`MQL4Compat`.

## Event Log

Файл событий задаётся `InpMT5_EventFile`. В tester-режиме файл удаляется один
раз перед первой записью нового прогона.

Формат колонок должен соответствовать:

```text
docs/schemas/mt5_signal_executor_schema.md
```

События в диагностическом executor:

```text
INIT
ORDER_PLACED
ORDER_EXPIRED
OPEN
CLOSE
OPEN_FAILED
ML_EVAL
ML_CLOSE
```

Ограничение: `ORDER_PLACED` пишется в момент подготовки `set.BUY`/`set.SEL`,
до того как существующий `ORDERS_SET()` вернул фактический ticket. Поэтому
ticket в этой строке может быть `0`.

`OPEN` фиксируется, когда на следующем баре уже виден фактический market-order
с нужным magic. `ML_EVAL` пишется только для фактически открытой позиции и
содержит post-fill признаки:

```text
bars_since_fill
unrealized_pnl_r_before_decision
max_favorable_r_before_decision
max_adverse_r_before_decision
ml_exit_score
ml_exit_decision
```

При `InpMT5_BlockBarsSinceFill0Exit=true` строка с `bars_since_fill=0` не
считается рабочим ML-close решением. `ML_CLOSE` пишется как диагностическое
решение закрыть позицию; фактическое закрытие проходит через существующий
`MQL4Compat` order path и затем отражается отдельной history-строкой `CLOSE`.

`CLOSE` в Task 4 ограничен: он берётся из history по отслеживаемому ticket.
Причина закрытия пишется как `broker_history_limited`, потому что надёжное
разделение SL/TP/manual/ML-close без более глубокой переделки order layer и
history reconciliation не реализовано в этой задаче. Цена закрытия тоже
manual/limited: в текущем `MQL4Compat` нет `OrderClosePrice()`, поэтому
`order_close_price` заполняется доступной ценой выбранной history-deal и
должен сверяться вручную с MT5 history/deals при tester-прогоне.

## Compile

Проверка компиляции берётся из `docs/methodology/13b-mt5-execution-parity.md`:

```bash
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' \
  /compile:'/home/hohla/git/SoSimple/MT/MQL5/Experts/$o$imple.mq5' \
  /log:'/tmp/sosimple_mt5_compile.log'
iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile.log | tail -n 20
```

Успех засчитывается только если лог содержит:

```text
Result: 0 errors, 0 warnings
```

и `MT/MQL5/Experts/$o$imple.ex5` обновлён после правок исходника.

## Manual Tester Run

Ручной tester-прогон:

```text
symbol: XAUUSD
timeframe: H1
model: real ticks или generated ticks, записать в отчёт
dates: выбранный diagnostic split
```

Интерпретация результата: `DIAGNOSTIC_ONLY`. Этот путь проверяет MT5
исполнение лимитных заявок, fill, SL и close mechanics. Он не доказывает
качество ML без отдельных leakage, split, locked-test, robustness и
reconciliation-проверок.
