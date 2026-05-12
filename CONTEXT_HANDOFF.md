# Context Handoff

Дата: 2026-05-12.

## Текущий этап

Идёт online-проверка диагностического M5-тракта:

`MT4 -> Nero.csv -> API.telemetry_signal_watcher -> ml_signals.csv -> MT4 -> ml_trade_events.csv`

Цель этапа - проверить механику обмена и исполнения, а не прибыльность. Диагностический режим специально даёт много сделок, чтобы быстро набрать факты по открытию, закрытию, стопам, тейкам, задержкам, спреду и журналам.

## Git

Локальная ветка: `trade-execution-m5-parity`.

Последние коммиты:

- `72fe177 fix(mt4): resolve array out of range error in orphan order cleanup`
- `9b91fcb chore(mt4): standardize code formatting and update documentation`
- `0205049 feat: add mt4 trade event log`

Ветка локально на 1 коммит впереди `origin/telemetry-maxpositions-20`.

Незакоммиченные изменения на момент handoff:

- `.claude/skills/stage-reporting/SKILL.md` - пользователь уточнил правило заполнения `CONTEXT_HANDOFF.md`;
- `.claude/skills/update-docs-on-code-change/SKILL.md` - пользовательский/локальный diff, нужно проверить перед коммитом;
- `CONTEXT_HANDOFF.md` - сжат до актуального состояния для новой сессии.

Не трогать `AGENTS.md` без явной просьбы пользователя.

## Что уже сделано

В диагностическом MT4-контуре:

- добавлен подробный торговый журнал `MT/MQL4/Files/ml_trade_events.csv`;
- `lib_ML_Signal.mqh` пишет события `OPEN` и `CLOSE`;
- в журнал входят ticket, направление, время сигнала, время входа/выхода, причина закрытия, bid/ask, spread, ATR, цена входа, stop, take profit, close, profit, число баров удержания, число открытых позиций;
- `ML_MaxPositions` поднят до `20`, чтобы не терять сделки в частом M5-тесте;
- исправлено падение `array out of range in 'SERVICE.mqh' (209,16)` при очистке старых ордеров с magic, которого нет в текущем `#.csv`.

Проверка фикса `SERVICE.mqh`:

- причина была в обращении к `EXP[e]`, когда `e == ExpTotal`;
- исправление закрывает/удаляет чужой ордер напрямую по ticket;
- локально прошёл тест:

```bash
./.venv/bin/python -m pytest tests/test_mql_telemetry_params_csv_contract.py -q
```

Результат: `11 passed`.

## Серверный online-тест

Сервер: `ssh hohla`, репозиторий `/home/hohla/git/SoSimple`.

На сервер вручную отправлены актуальные:

- `MT/MQL4/Include/SERVICE.mqh`;
- `CONTEXT_HANDOFF.md`.

Серверный watcher запущен командой:

```bash
./.venv/bin/python -m API.telemetry_signal_watcher \
  --poll-interval-sec 1 \
  --heartbeat-sec 60 \
  --max-runtime-rows 12000 \
  --diagnostic-target-signals-per-year 5000 \
  --allow-unsafe-future-features \
  --verbose
```

Важно: `--allow-unsafe-future-features` здесь допустим только потому, что это механический диагностический тест, а не проверка честной прибыльности ML.

Проверка примерно через 10 часов online-работы, 2026-05-12 около `05:27 UTC`:

- watcher жив, PID `604115`;
- uptime watcher около `12:41:47`;
- последняя обработанная свеча: `2026.05.12 07:15`;
- `runtime_ml_signals.csv`, `MT/MQL4/Files/ml_signals.csv`, `MT/tester/files/ml_signals.csv` совпали по hash;
- `runtime_export_metadata.json`: `rows_total=42`, `nonzero_rows=42`, `buy_rows=21`, `sell_rows=21`;
- дублей времени и противоположных сигналов на одно время нет.

Торговый журнал `MT/MQL4/Files/ml_trade_events.csv`:

- всего событий: `79`;
- `OPEN`: `43`;
- `CLOSE`: `36`;
- открытыми оставались `7` позиций;
- закрытая сумма: `-759.05`;
- выигрышных закрытий: `13`;
- убыточных закрытий: `23`.

Закрытия по причинам:

- `StopLoss`: `16`, сумма `-2332.05`;
- `TakeProfit`: `5`, сумма `995.80`;
- `Timeout`: `15`, сумма `577.20`.

По направлениям:

- `BUY`: `20` закрытий, сумма `-1481.80`;
- `SELL`: `16` закрытий, сумма `722.75`.

Вывод: online-тракт работает. MT4 пишет `Nero.csv`, watcher строит `ml_signals.csv`, MT4 подхватывает сигналы, открывает и закрывает сделки, а `ml_trade_events.csv` даёт подробные данные для сверки с тестером.

## Итоги online/tester сверки 2026-05-12

Создан краткий отчёт:

- `docs/reports/2026-05-12-online-tester-execution-reconciliation.md`.

Ключевой вывод: `ml_signals.csv` online/tester совпали, но старое online-исполнение
пропустило 6 входов на общей исполнимой части. Первые три подтверждены в
online MT4-логе как `requote ERROR-138`.

Стабильный закрытый срез `2026.05.12 00:10` -> `2026.05.12 13:05`:

- online: 67 закрытых сделок, PnL `-680.2`, матожидание `-10.1522`;
- tester: 68 закрытых сделок, PnL `-522.6`, матожидание `-7.6853`;
- парные 65 закрытых сделок: online `-745.0`, tester `-696.7`,
  разница матожидания `-0.7431`.

Главный вред дали пропущенные online-входы, а не расхождения PnL по парным
сделкам.

`ML/online_tester_reconciliation.py` обновлён:

- сравнение online/tester по `signal_time + direction`;
- `OPEN_FAILED` учитывается отдельным статусом;
- добавлены `--start-time` / `--end-time`;
- summary считает `closed_trades`, `signal_basis` и paired-метрики.

`OPEN_FAILED` уже реализован в `MT/MQL4/Include/lib_ML_Signal.mqh`; для старых
логов таких строк ещё нет, поэтому они видны как `missing_open`.

## Открытые вопросы

1. Найден один вход с задержкой `65` минут:
   - ticket `1581716381`;
   - `BUY`;
   - signal_time `2026.05.11 22:55`;
   - entry_time `2026.05.12 00:00`;
   - spread `0.92`;
   - ATR `1.81`.

   Нужно понять, это стартовый/ночной эффект, задержка файла, ожидание цены, перезапуск, широкий спред или логическая ошибка.

2. Были `requote ERROR-138` при открытии/закрытии. Старый online/tester анализ
   показал, что часть входов из-за этого не открылась. В новом тесте нужно
   проверить, что такие случаи попадают в `OPEN_FAILED`, а не теряются.

3. `MAIL_SEND-706 ERROR-4060` встречается в логах, но относится к почте и не блокирует торговый тракт.

4. Прибыльность diagnostic режима отрицательная. Это ожидаемо и не является критерием успеха текущего этапа.

## Следующий шаг

Продолжить в новой сессии с проверки свежего состояния сервера:

```bash
ssh hohla 'cd /home/hohla/git/SoSimple && date && ps -eo pid,etime,pcpu,pmem,cmd | rg telemetry_signal_watcher || true'
ssh hohla 'cd /home/hohla/git/SoSimple && tail -80 ML/reports/telemetry_frequency_v1/runtime/telemetry_signal_watcher.log'
ssh hohla 'cd /home/hohla/git/SoSimple && tail -80 MT/MQL4/Logs/20260512.log'
ssh hohla 'cd /home/hohla/git/SoSimple && tail -30 MT/MQL4/Files/ml_trade_events.csv'
```

После этого:

1. Провести новый online-тест несколько часов уже с append-only `ml_signals.csv`
   и `OPEN_FAILED` event-log.
2. Запустить `ML.online_tester_reconciliation` по новому online/tester участку
   с явными `--start-time` / `--end-time`.
3. Разобрать задержку входа ticket `1581716381`, если она повторится вне края
   файла.
4. Перед финальным закрытием этапа сжать handoff ещё раз до актуального
   состояния, а подробные итоги перенести в `docs/reports/` и коротко в
   `CHANGELOG.md`.
