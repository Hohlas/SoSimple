## 13b. MT5 execution parity

### Цель

Проверить, что MT5-эксперт собран из git-исходников и tester исполняет тот же
frozen-сигнал, который проверялся в Python.

Общие правила frozen export, hash, counts, reconciliation, запрета подгонки по
tester-результату и разделения parity от качества ML брать из
[`13-export-mt4-parity.md`](13-export-mt4-parity.md).

### Контур

- Терминал: `/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5`.
- `MQL5` внутри терминала является симлинком на `MT/MQL5`.
- Основной эксперт: `MT/MQL5/Experts/$o$imple.mq5`.
- Скомпилированный файл: `MT/MQL5/Experts/$o$imple.ex5`.
- Диагностический executor не является отдельным fallback expert: он встроен в
  текущий `iSignal=3` / `ML_TRADE()` и по умолчанию выключен.

### Диагностический executor

Включение режима:

```text
InpMT5_DiagnosticExecutor=true
InpMT5_EntrySignalFile=mt5_entry_signals.csv
InpMT5_EventFile=mt5_trade_events.csv
InpMT5_BlockBarsSinceFill0Exit=true
```

`mt5_entry_signals.csv` должен лежать в файловом каталоге MT5 tester `Files`.
Диагностический reader отдельный от legacy `ML_SIGNALS_FILE=ml_signals.csv`.
Строка выбирается по `decision_time` или `time`, совпадающему с рабочим баром
`Time[bar]`. Поддержаны только лимитные заявки на вход:

```text
side=BUY,  entry_type=BUY_LIMIT
side=SELL, entry_type=SELL_LIMIT
```

Цена входа берётся только из `limit_price`, защитный стоп - только из
`stop_price`, срок жизни заявки - из `max_fill_lag_bars`. Размещение идёт через
существующий order path:

```text
set.BUY / set.SEL -> ORDERS_SET() -> SET_BUY() / SET_SEL()
```

### CSV contract

Входной signal CSV:

```text
time;feature_time;feature_available_time;decision_time;rule_id;side;entry_type;limit_price;stop_price;atr;max_fill_lag_bars
```

Запрещённые входные колонки:

```text
fill_time;exit_time;future_exit_time;future_favorable_r_3;future_adverse_r_3;hold_3_pnl_r;pnl_r
```

Причина: entry CSV описывает решение до tester fill и не должен содержать
будущую судьбу Python-смоделированной сделки.

Event log CSV:

```text
event;time;feature_time;feature_available_time;decision_time;execution_time;rule_id;signal_time;ticket;side;requested_price;fill_price;order_open_price;order_close_price;stop_price;close_reason;profit;bars_since_fill;bid;ask;spread;spread_atr;bar_open;bar_high;bar_low;bar_close;calculation_open;slippage_points;entry;take_profit;close;swap;commission;hold_bars;open_positions;max_positions;balance;equity;entry_time;exit_time;unrealized_pnl_r_before_decision;max_favorable_r_before_decision;max_adverse_r_before_decision;ml_exit_score;ml_exit_decision;comment
```

Timing contract:

```text
feature_time <= decision_time <= execution_time
```

Временные поля должны быть колонками CSV, а не только текстом отчёта.

### Event log

В tester-режиме файл событий удаляется один раз перед первой записью нового
прогона.

События диагностического executor:

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

Минимальные требования к событиям:

- `ORDER_PLACED` пишется до возврата фактического ticket, поэтому `ticket` может
  быть `0`.
- `OPEN` фиксируется только после видимого tester fill.
- `ML_EVAL` пишется только для открытой позиции и содержит post-fill признаки:
  `bars_since_fill`, `unrealized_pnl_r_before_decision`,
  `max_favorable_r_before_decision`, `max_adverse_r_before_decision`,
  `ml_exit_score`, `ml_exit_decision`.
- При `InpMT5_BlockBarsSinceFill0Exit=true` строка с `bars_since_fill=0` не
  считается рабочим ML-close решением.
- `ML_CLOSE` - диагностическое решение закрыть позицию; фактическое закрытие
  отражается отдельной строкой `CLOSE`.

### Ограничения прототипа

- `CLOSE` берётся из history по отслеживаемому ticket; причина закрытия
  записывается как `broker_history_limited`.
- `order_close_price`, `take_profit`, `swap` и `commission` требуют ручной
  сверки с MT5 history/deals; текущий writer не доказывает эти значения.
- Сопровождение работает на H1-баре, а не через `OnTradeTransaction`; если
  pending-order открылся и закрылся внутри одного H1-бара, полный lifecycle
  может не восстановиться.

### Компиляция

```bash
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' \
  /compile:'/home/hohla/git/SoSimple/MT/MQL5/Experts/$o$imple.mq5' \
  /log:'/tmp/sosimple_mt5_compile.log'
```

Лог MetaEditor читать так:

```bash
iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile.log | tail -n 20
```

Успех компиляции: в логе `Result: 0 errors, 0 warnings` и обновлён
`MT/MQL5/Experts/$o$imple.ex5`.

Не считать сам код возврата `wine` verdict-ом компиляции: в текущем окружении
MetaEditor может вернуть `1` при успешной сборке. Если `wine` в песочнице
возвращает `159` или не пишет лог, повторить запуск вне песочницы.

### Порядок

1. Проверить симлинк `MQL5 -> MT/MQL5`.
2. Скомпилировать `MT/MQL5/Experts/$o$imple.mq5`.
3. Проверить лог MetaEditor и время изменения `.ex5`.
4. Найти фактический MT5 tester `Files` каталог; не считать repo path
   `MT/MQL5/Files` гарантированным runtime-каталогом.
5. Скопировать signal CSV в найденный каталог как `mt5_entry_signals.csv`.
6. Запустить MT5 tester только после успешной компиляции:
   - symbol: `XAUUSD`;
   - timeframe: `H1`;
   - date range: выбранный diagnostic interval;
   - tester model: записать точное значение;
   - diagnostic inputs: как в секции "Диагностический executor".
7. Вернуть `mt5_trade_events.csv` из фактического output path и tester HTML/XML
   report, если он доступен.
8. Сверять tester-исполнение по правилам
   [`13-export-mt4-parity.md`](13-export-mt4-parity.md): frozen export,
   opened/closed trades, missing opens, wrong direction, close reasons, PnL.
9. Если MT5 заменяет Python-симулятор, зафиксировать отдельно:
   - кто создаёт `Nero.csv`;
   - когда строка признаков доступна;
   - когда Python публикует сигнал;
   - когда MT5 может поставить, удалить или закрыть ордер.
10. Зафиксировать tester metadata:
    - MT5 build number;
    - broker/server;
    - symbol contract specification;
    - tester model;
    - date range;
    - deposit/currency/leverage;
    - spread mode;
    - netting или hedging account mode.

### Обязательные проверки

- `.ex5` собран из текущего `$o$imple.mq5`.
- MetaEditor log сохранён и показывает `0 errors, 0 warnings`.
- MT5 tester читает проверенный frozen export.
- Все расхождения исполнения классифицированы.
- Tester-result не объявляется качеством ML без leakage, split, locked_test,
  robustness и reconciliation-проверок.

### Типовые ошибки

- Не экранировать `$o$imple.mq5` кавычками.
- Считать старый `.ex5` актуальным без проверки времени изменения.
- Считать `wine=1` ошибкой компиляции без чтения MetaEditor log.
- Подгонять модель или export по tester-результату.
- Переносить MT4-логику в MT5 без проверки отличий order API, tester model и
  путей файлов.

---
