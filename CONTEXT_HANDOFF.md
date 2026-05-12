# Context Handoff

Дата контекста: 2026-05-12.

## Текущая работа

Идёт локальная проверка тракта `MT4 -> Nero.csv -> Python watcher -> ml_signals.csv -> MT4` на M5.

Цель этого этапа не прибыльность. Цель - проверить механику:

- MT4 пишет свежий `MT/MQL4/Files/Nero.csv`;
- watcher пересобирает `ML/reports/telemetry_frequency_v1/runtime/runtime_ml_signals.csv`;
- watcher копирует сигналы в `MT/MQL4/Files/ml_signals.csv` и `MT/tester/files/ml_signals.csv`;
- советник MT4 видит свежий `ml_signals.csv`;
- советник открывает/закрывает сделки по тем же правилам, что потом будем сравнивать с тестером;
- новый файл `ml_trade_events.csv` должен дать подробный журнал сделок для сверки времени, цены, стопа, тейка, спреда, bid/ask и причины закрытия.

## Ветка и состояние Git

Текущая ветка: `telemetry-maxpositions-20`.

Локальный коммит в этой ветке:

- `0205049 feat: add mt4 trade event log`

Коммит ещё не слит в `main` и не запушен.

Текущее незакоммиченное изменение:

- `MT/MQL4/Include/SERVICE.mqh` - точечная правка падения `array out of range in 'SERVICE.mqh' (209,16)` на сервере.

Причина ошибки: при `Real=true` код проверяет открытые/отложенные ордера и удаляет ордера, magic которых отсутствует в `#.csv`. Если magic не найден, внутренний цикл заканчивается с `e == ExpTotal`, а старый код вызывал `EXP[e].EMPTY_EXPERTS_DELETE()`. Это выход за массив.

Правка: для такого "чужого" ордера код больше не обращается к `EXP[e]`, а закрывает/удаляет уже выбранный ордер напрямую по ticket:

- рыночный `BUY` закрывается по `BID`;
- рыночный `SELL` закрывается по `ASK`;
- отложенные ордера удаляются через `OrderDelete`.

После правки прошёл тест:

```bash
./.venv/bin/python -m pytest tests/test_mql_telemetry_params_csv_contract.py -q
```

Результат: `11 passed`.

Нужно пересобрать эксперта в MetaEditor/MT4 и повторить запуск на сервере.

Проверка на сервере после пересборки:

- первое падение `20:28:19 array out of range in 'SERVICE.mqh' (209,16)` было на старом `.ex4`;
- после повторной компиляции `20:36:49` ошибка не повторилась;
- советник нашёл старые позиции с magic `517154336`, которого нет в текущем `#.csv`;
- исправленный код закрыл эти старые позиции напрямую по ticket;
- один ticket сначала дал `requote ERROR-138`, но затем был закрыт повторной попыткой;
- советник дошёл до `RECOUNT_HISTORY done` и `initialized`;
- watcher обновил сигналы до `2026.05.11 22:35`;
- MT4 открыл новую сделку по сигналу:
  - `OPEN;1581709174;SELL;signal_time=2026.05.11 22:35;entry_time=2026.05.11 22:40`
  - `entry=4737.56`
  - `stop=4745.79`
  - `take_profit=4723.85`
  - `spread=0.40`
  - `spread_atr=0.1459`
  - `max_positions=20`
- появился `MT/MQL4/Files/ml_trade_events.csv`.

Вывод: серверный тракт дошёл до полного цикла `MT4 -> Nero.csv -> watcher -> ml_signals.csv -> MT4 open trade -> ml_trade_events.csv`.

## Online тест на сервере, первые ~10 часов

Проверка выполнена 2026-05-12 около `05:27 UTC` на сервере `hohla`.

Состояние watcher:

- процесс жив: PID `604115`;
- uptime около `12:41:47`;
- последняя обработанная свеча в watcher: `2026.05.12 07:15`;
- `runtime_ml_signals.csv`, `MT/MQL4/Files/ml_signals.csv`, `MT/tester/files/ml_signals.csv` совпали по hash;
- `runtime_export_metadata.json`: `rows_total=42`, `nonzero_rows=42`, `buy_rows=21`, `sell_rows=21`, дублей времени нет, противоположных сигналов на одно время нет.

Торговый журнал `MT/MQL4/Files/ml_trade_events.csv`:

- всего строк событий: `79`;
- `OPEN`: `43`;
- `CLOSE`: `36`;
- открытыми остаются `7` позиций;
- закрыто с общей суммой `-759.05`;
- выигрышных закрытий `13`, убыточных `23`.

Закрытия по причинам:

- `StopLoss`: `16`, сумма `-2332.05`;
- `TakeProfit`: `5`, сумма `995.80`;
- `Timeout`: `15`, сумма `577.20`.

По направлениям:

- `BUY`: `20` закрытий, сумма `-1481.80`;
- `SELL`: `16` закрытий, сумма `722.75`.

Механика входов:

- почти все входы прошли через `5` минут после сигнала, как ожидается для M5;
- один вход был с задержкой `65` минут: `ticket=1581716381`, `BUY`, `signal_time=2026.05.11 22:55`, `entry_time=2026.05.12 00:00`, `spread=0.92`, `atr=1.81`; это нужно отдельно проверить как стартовый/ночной разрыв или ожидание доступной цены/файла.

Ошибки/предупреждения:

- `array out of range` после пересборки эксперта не повторялся; единственная запись осталась от старого `.ex4`;
- были `requote ERROR-138` на открытии/закрытии, но часть операций затем выполнялась повтором;
- `MAIL_SEND-706 ERROR-4060` относится к почте и не блокирует торговый тракт;
- `MLP_WAIT: timeout` встречался, но тракт затем догонял файл и продолжал работу.

Вывод: механический online тракт работает: watcher обновляет сигналы, MT4 их подхватывает, сделки открываются и закрываются, `ml_trade_events.csv` пишет достаточно данных для сверки с тестером. Прибыльность этого diagnostic режима не является целью и сейчас отрицательная.

## Что уже изменено в коде

В коммите `0205049`:

- `MT/MQL4/Experts/$o$imple.mq4` поднят до версии `260.333`;
- `MT/MQL4/Include/lib_ML_Signal.mqh` поднят до `v4.3`;
- добавлен торговый журнал `MT/MQL4/Files/ml_trade_events.csv`;
- `ML_MaxPositions` увеличен с `10` до `20`;
- обновлены тесты и документация.

Новый `ml_trade_events.csv` пишет события:

- `OPEN` - после успешного открытия сделки;
- `CLOSE` - при закрытии советником или при обнаружении закрытой сделки в истории брокера.

Поля журнала:

`event;ticket;direction;signal_time;entry_time;exit_time;reason;score;atr;bid;ask;spread;spread_atr;bar_open;bar_high;bar_low;bar_close;requested_price;order_open_price;order_close_price;slippage_points;entry;stop;take_profit;close;profit;swap;commission;hold_bars;open_positions;max_positions;balance;equity`

Смысл: потом можно точно сравнить онлайн и тестер - не только количество сделок, но и время входа, цену входа, стоп, тейк, закрытие, spread, bid/ask и проскальзывание.

## Важная правка `#.csv`

Была ошибка чтения параметров:

`INPUT_FILE_READ-165: invalid function parameter value! ERROR-4051`

Причина: строка `INFO` в `#.csv` начиналась с текста `M5-diagnostic ...`. В MQL-парсере первый дефис после начала строки воспринимается как разделитель даты, поэтому дефис в `M5-diagnostic` ломал чтение.

Исправлено: `INFO` теперь начинается с версии и даты без лишнего дефиса до даты.

Текущие строки в:

- `MT/MQL4/Files/#.csv`
- `MT/tester/files/#.csv`

Ключевые параметры:

- `INFO=SoSimple260.333 2025.11.14-2026.05.11, Sprd=0, StpLev=0, OPT-telemetry_frequency_v1_highfreq500_M5_fixed_hold`
- `SymPer=XAUUSD5`
- `Risk=1`
- `Magic=662427296`
- `ML_ExitMode=0`
- `ML_TrailATR=0`
- `ML_TakeProfitATR=5`
- `ML_MaxPositions=20`
- `ML_HoldBars=24`
- `ML_AllowReversal=0`
- `ML_UseScoreFilter=0`
- `ML_ScoreThreshold=0`
- `ML_BackStopATR=3`

После этой правки тест прошёл:

```bash
./.venv/bin/python -m pytest tests/test_mql_telemetry_params_csv_contract.py -q
```

Результат: `11 passed`.

До текущего handoff также проходили:

```bash
./.venv/bin/python -m pytest tests/test_mql_telemetry_params_csv_contract.py tests/test_telemetry_daily_reconciliation.py tests/test_telemetry_signal_watcher.py -q
```

Результат: `36 passed`.

```bash
./.venv/bin/python wiki/wiki.py verify
```

Результат: `OK`.

## Локальный MT4: состояние советника

Пользователь скомпилировал эксперта и запустил локальный MT4.

Проверенный лог:

- `MT/MQL4/Logs/20260511.log`

Советник успешно загрузил новую версию и параметры:

- `OnInit() SoSimple.V260.333`
- `CSV parameters loaded ... ML_MaxPositions=20 ... ML_HoldBars=24 ... ML_TakeProfitATR=5 ... ML_BackStopATR=3`
- `MLP_INIT: Loaded V4.3 ... MaxPositions=20 ... TrailATR=0.00 TakeProfitATR=5.00`

Это значит: новый код советника и новые параметры применились.

На момент проверки советник не открыл сделку, потому что `ml_signals.csv` отставал от текущего бара:

- MT4 ждал `bar_time=2026.05.11 22:00`;
- `ml_signals.csv` тогда заканчивался на `2026.05.11 21:10`;
- после первой пересборки watcher файл дошёл до `2026.05.11 21:35`;
- затем watcher завершил вторую пересборку до `2026.05.11 22:05`.

В логе MT4 было:

- `MLP_WAIT: file still behind bar_time=2026.05.11 22:00 last=2026.05.11 21:10`
- затем `MLP NO_SIGNAL bar_time=2026.05.11 22:00 ... last=2026.05.11 21:10`
- после этого watcher уже обновил `ml_signals.csv` до `2026.05.11 22:05`, но в логе MT4 ещё не было свежего `MLP_RELOAD` после этой пересборки.

Это не ошибка торговли. Это означает, что на тот момент watcher ещё не догнал свежий бар.

Файл `MT/MQL4/Files/ml_trade_events.csv` на момент проверки ещё не создан. Это нормально: он появится только после первого `OPEN` или `CLOSE`.

Побочные ошибки в логе:

- `MAIL_SEND-647: requested history data is in update state! ERROR-4066`
- `MAIL_SEND-702: function is not confirmed! ERROR-4060`

Они относятся к почте/истории и пока не выглядят блокером для ML-тракта.

## Локальный watcher: состояние

Пользователь запустил локальный watcher.

Команда процесса:

```bash
./.venv/bin/python -m API.telemetry_signal_watcher \
  --poll-interval-sec 1 \
  --heartbeat-sec 60 \
  --max-runtime-rows 12000 \
  --diagnostic-target-signals-per-year 5000 \
  --allow-unsafe-future-features \
  --verbose
```

Процесс найден:

- PID `512758`
- команда совпадает с watcher выше;
- на момент проверки процесс был жив и потреблял CPU.

Важно: используется `--allow-unsafe-future-features`. Это осознанно, потому что текущая задача диагностическая: нам нужно много сигналов для проверки механики MT4, а не честная ML-прибыльность.

Лог watcher:

- `ML/reports/telemetry_frequency_v1/runtime/telemetry_signal_watcher.log`

Свежие строки:

- `2026-05-11 23:09:20 INFO WATCHER rebuild start: time=2026.05.11 21:35`
- `2026-05-11 23:09:20 WARNING WATCHER unsafe online contract override enabled: mode=original_contour feature_mode=original_baseline`
- `2026-05-11 23:12:15 INFO WATCHER rebuild done: time=2026.05.11 21:35`
- `2026-05-11 23:12:15 INFO WATCHER HEARTBEAT: status=REBUILT last_bar=2026.05.11 21:35`
- `2026-05-11 23:12:17 INFO WATCHER rebuild start: time=2026.05.11 22:05`
- `2026-05-11 23:15:11 INFO WATCHER rebuild done: time=2026.05.11 22:05`
- `2026-05-11 23:15:11 INFO WATCHER HEARTBEAT: status=REBUILT last_bar=2026.05.11 22:05`
- `2026-05-11 23:18:13 INFO WATCHER HEARTBEAT: status=IDLE last_bar=2026.05.11 22:05`

На момент последней проверки watcher догнал `Nero.csv` до `2026.05.11 22:05` и ушёл в `IDLE`.

Текущий `MT/MQL4/Files/ml_signals.csv` после первой пересборки заканчивался так:

```text
2026.05.11 20:40;-1
2026.05.11 20:50;1
2026.05.11 21:00;-1
2026.05.11 21:05;1
2026.05.11 21:10;-1
2026.05.11 21:35;1
2026.05.11 22:05;-1
```

`runtime_export_metadata.json` после первой пересборки:

- `rows_total=11441`
- `nonzero_rows=5677`
- `buy_rows=2871`
- `sell_rows=2806`
- `duplicate_time_rows=0`
- `same_time_opposite_signal_groups=0`

Hash трёх файлов сигналов совпал:

```text
261d924b260e9a2f5fa462b58453c086f902fc71494dff207df63e8dcc2ef5f3  ML/reports/telemetry_frequency_v1/runtime/runtime_ml_signals.csv
261d924b260e9a2f5fa462b58453c086f902fc71494dff207df63e8dcc2ef5f3  MT/MQL4/Files/ml_signals.csv
261d924b260e9a2f5fa462b58453c086f902fc71494dff207df63e8dcc2ef5f3  MT/tester/files/ml_signals.csv
```

Вывод: watcher работает и копирование сигналов работает. Осталось дождаться реакции MT4 на обновлённый `ml_signals.csv` после `22:05`: нужен свежий `MLP_RELOAD`, затем `MLP BUY`/`MLP SELL` или понятный `MLP NO_SIGNAL`.

## Что проверить следующим

1. Проверить, не появилась ли новая пересборка watcher после `22:05`:

```bash
tail -60 ML/reports/telemetry_frequency_v1/runtime/telemetry_signal_watcher.log
```

Если `Nero.csv` обновился, ждём строки вида:

```text
WATCHER rebuild done: time=...
WATCHER HEARTBEAT: status=REBUILT last_bar=...
```

2. Проверить хвост сигналов:

```bash
tail -30 MT/MQL4/Files/ml_signals.csv
tail -30 ML/reports/telemetry_frequency_v1/runtime/runtime_ml_signals.csv
sha256sum ML/reports/telemetry_frequency_v1/runtime/runtime_ml_signals.csv MT/MQL4/Files/ml_signals.csv MT/tester/files/ml_signals.csv
```

Цель: три файла должны совпадать по hash, а хвост должен быть не старее текущего бара MT4.

3. Проверить лог MT4:

```bash
tail -120 MT/MQL4/Logs/20260511.log
```

Искать:

- `MLP_RELOAD` - MT4 увидел изменение `ml_signals.csv`;
- `MLP_INIT: Loaded V4.3` - MT4 перечитал сигналы новым кодом;
- `MLP BUY` или `MLP SELL` - сделка открылась;
- `MLP WAIT` - MT4 ещё ждёт файл;
- `MLP NO_SIGNAL` - на бар нет подходящего сигнала.

4. Если появится сделка, проверить новый подробный журнал:

```bash
tail -20 MT/MQL4/Files/ml_trade_events.csv
```

Первый `OPEN` должен содержать ticket, direction, signal_time, entry_time, bid, ask, spread, spread_atr, requested_price, order_open_price, stop, take_profit, open_positions и max_positions.

5. Если `ml_signals.csv` всё ещё отстаёт:

```bash
ps -o pid,etime,pcpu,pmem,cmd -p 512758
tail -80 ML/reports/telemetry_frequency_v1/runtime/telemetry_signal_watcher.log
```

Если watcher долго висит без `rebuild done`, смотреть ошибку в конце лога. `Nero.csv` большой, поэтому несколько минут на пересборку допустимы.

## Что делать после локальной проверки

Когда локально будет видно, что:

- watcher догоняет текущие M5-бары;
- MT4 делает `MLP_RELOAD`;
- появляется хотя бы один `MLP BUY` или `MLP SELL`;
- `ml_trade_events.csv` пишет событие `OPEN`;

тогда можно переносить на сервер.

Перед сервером нужно:

1. Решить, коммитить ли новый `.ex4` после локальной компиляции.
2. Проверить и убрать случайные line-ending изменения в `SERVICE.mqh` и `iPIC.mq4`, если там нет смысловых изменений.
3. Слить ветку в `main`, если пользователь подтвердит.
4. Запушить только по явной просьбе пользователя.
5. На сервере сделать `git pull`.
6. Передать нужные CSV через `rsync`.

Команда rsync для отправки файлов на сервер `hohla`:

```bash
rsync -az --progress --partial --inplace --timeout=60 \
  /home/hohla/git/SoSimple/MT/MQL4/Files/#.csv \
  /home/hohla/git/SoSimple/MT/MQL4/Files/ml_signals.csv \
  hohla:/home/hohla/git/SoSimple/MT/MQL4/Files/
```

И отдельно для tester:

```bash
rsync -az --progress --partial --inplace --timeout=60 \
  /home/hohla/git/SoSimple/MT/tester/files/#.csv \
  /home/hohla/git/SoSimple/MT/tester/files/ml_signals.csv \
  hohla:/home/hohla/git/SoSimple/MT/tester/files/
```

## Важные ограничения

- `telemetry_frequency_v1` в этом режиме - диагностический контур, а не честная ML-система.
- `--allow-unsafe-future-features` разрешён только для проверки механики торговли.
- Для прибыльной/честной online-системы остаётся основной кандидат `entry_path_v1_live_safe + A`, но сейчас мы не его торгуем, а проверяем механику MT4 на частых M5-сигналах.
- `ml_trade_events.csv` не появится до первой сделки.
- `BackTest=0` на online-торговле правильный для текущего советника: он последовательно читает строки `#.csv`.
