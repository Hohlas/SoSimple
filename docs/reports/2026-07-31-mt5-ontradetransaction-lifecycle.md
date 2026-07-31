# 2026-07-31 — MT5 OnTradeTransaction Lifecycle Closure

Статус: `DIAGNOSTIC_ONLY`. Этап: инфраструктурная диагностика исполнения
(без поискового бюджета, без выбора правил/порогов по результатам тестера).

## Цель

Закрыть жизненный цикл торговых событий диагностического MT5-исполнителя:
логировать каждое открытие/закрытие через нативные события
`OnTradeTransaction`, повторить сценарий прогона 2026-07-30, классифицировать
все открытия и снять неопределённость `same_h1_lifecycle_status`.

## Что сделано

1. MQL5: добавлен `MT5_OnTradeTransaction` в
   `MT/MQL5/Include/lib_ML_Signal.mqh` + обработчик `OnTradeTransaction` в
   `MT/MQL5/Experts/$o$imple.mq5` (no-op вне `MT5_DiagnosticExecutor`).
   Новые события `TX_OPEN` (deal entry IN) и `TX_CLOSE` (OUT/OUT_BY),
   пишутся в тот же 46-колоночный event CSV; идентичность — в `comment`:
   `position_id=<id>|deal=<ticket>|reason=<DEAL_REASON>`. Timing-поля у TX
   строк пусты (связь с сигналом делается в Python через OPEN-строки).
   Старый H1-polling механизм не менялся — он baseline для сравнения.
2. Python: whitelist имён событий в `ML/baseline/mt5_signal_schema.py`
   (10 имён, опечатки теперь отклоняются); reconciliation в
   `ML/baseline/parse_mt5_execution_report.py` (классы CLOSED_TX /
   OPEN_AT_END / UNEXPLAINED, `same_h1_count`); тесты дополнены.
3. Компиляция headless: `0 errors, 0 warnings`, лог
   `ML/reports/mt5_execution_loop/mt5_compile_20260731_tx_lifecycle.log`
   (sha256 `c38811e1...ce2b`).
4. Smoke-прогон (2019.06.20–2019.07.20): TX-события срабатывают под
   Model 1; 24 TX_OPEN / 24 TX_CLOSE, UNEXPLAINED=0, причины сделок
   непустые. Единственная позиция без polling-OPEN — вход 01:11, SL 01:15
   внутри одного H1 бара (ожидаемое слепое пятно polling).
   Построчный пример — наблюдение сессии: smoke event CSV перезаписан
   полным прогоном в каталоге агента, в манифесте сохранены только
   агрегаты (24/24/0).
5. Полный прогон: тот же сценарий, что 2026-07-30 (XAUUSD, H1,
   2019.06.20–2022.12.03, Model 1, депозит 10000 USD, 1:500, hedging,
   agent build 6061, 4 850 645 тиков, 20 427 баров, 0:08:04).

## Команды

```bash
# компиляция
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' \
  /compile:'/home/hohla/git/SoSimple/MT/MQL5/Experts/$o$imple.mq5' \
  /log:'/tmp/sosimple_mt5_compile.log'
# полный прогон
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/terminal64.exe' \
  '/config:C:\mt5_tx_full.ini'
# парсинг + reconciliation
./.venv/bin/python -m ML.baseline.parse_mt5_execution_report \
  --events ML/reports/mt5_execution_loop/mt5_trade_events_20260731_tx_lifecycle.csv \
  --output-json ML/reports/mt5_execution_loop/mt5_execution_metrics_20260731_tx_lifecycle.json
# проверки
./.venv/bin/python -m pytest tests/test_parse_mt5_execution_report.py \
  tests/test_mt5_signal_executor_schema.py -q
```

Копии tester INI (условия воспроизведения: диапазон, Model, депозит, плечо)
сохранены в repo: `ML/reports/mt5_execution_loop/mt5_tx_lifecycle_tester_20260731_full.ini`
и `..._smoke.ini` (оригиналы — `C:\mt5_tx_full.ini`, `C:\mt5_tx_smoke.ini` вне repo).

## Verification

- `./.venv/bin/python -m pytest tests/test_parse_mt5_execution_report.py tests/test_mt5_signal_executor_schema.py -q`
  → `16 passed` (было 13 до этого этапа: +2 reconciliation/TX-теста,
  +1 на whitelist имён событий).
- `validate_mt5_event_frame` на полном event CSV → PASS.
- MetaEditor compile `MT/MQL5/Experts/$o$imple.mq5` → `0 errors, 0 warnings`.

## Результаты

Артефакты и hash'и — в манифесте
`ML/reports/mt5_execution_loop/mt5_tx_lifecycle_run_manifest_20260731.json`;
event CSV sha256 `3ab9b78b...d60b`, вход — тот же frozen CSV сигналов
(sha256 `0b30fc5b...f900`, без пересоздания).

| Событие | 2026-07-30 | 2026-07-31 |
|---|---|---|
| ORDER_PLACED | 294 | 294 |
| OPEN (polling) | 252 | 252 |
| CLOSE (polling) | 18 | 18 |
| ML_CLOSE | 53 | 53 |
| ML_EVAL | 1915 | 1915 |
| TX_OPEN | — | 269 |
| TX_CLOSE | — | 269 |

Polling-поток идентичен прогону 30.07 — прогоны сопоставимы. Остальные
события в таблицу не вынесены и тоже идентичны: OPEN_FAILED 8714/8714
(разбивка 8682 + 32), ORDER_EXPIRED 9/9, INIT 1/1; полные счётчики — в
манифесте.

Суммы `profit` (сантехнический выход, НЕ PnL-вывод, `DIAGNOSTIC_ONLY`):
по 269 TX_CLOSE = `−1755.1`, по 18 старым polling-CLOSE = `242.5`.
`DEAL_PROFIT` не включает swap и commission (в TX-строках обе колонки = 0).
Поле `profit_sum` в metrics JSON остаётся polling-only (242.5).

Legacy-оценки в metrics JSON — `missing_open_estimate=42` и
`open_without_close_estimate=234` — считаются только по polling-потоку
(294−252 и 252−18) и заменены reconciliation: фактически незакрытых
позиций нет (`OPEN_AT_END=0`, `UNEXPLAINED=0`).

### Reconciliation (главный итог)

- Позиции: 269. Классы: `CLOSED_TX=269`, `OPEN_AT_END=0`, `UNEXPLAINED=0`.
- `same_h1_lifecycle_status=MEASURED:17` — 17 позиций открылись и закрылись
  внутри одного H1 бара; ровно они объясняют разрыв OPEN 252 vs TX_OPEN 269
  (252 + 17 = 269) и недоступны старому polling по построению.
- Причины закрытий (из `DEAL_REASON`): `EXPERT=145`, `SL=124`.
  Плейсхолдер `broker_history_limited` остаётся только в 18 старых
  polling-CLOSE строках.
- Разрыв polling CLOSE=18 vs TX_CLOSE=269: подтверждено, что старый
  механизм наблюдал закрытие только когда история позиции была доступна по
  тикету на следующем опросе; гипотеза о причине (несовпадение order ticket
  vs position id в MODE_HISTORY через MQL4-компат слой) остаётся гипотезой —
  на классификацию не влияет, т.к. TX-поток покрывает 100% закрытий.
- Арифметика размещений: 294 ORDER_PLACED = 269 fills (из них 17 same-H1,
  которые polling видел как `pending order was not found`) + 9 ORDER_EXPIRED
  + 15 реально исчезнувших отложников + 1 остаток на конце теста
  (269 + 9 + 32 − 17 + 1 = 294). Отдельная классификация ERROR-4756 —
  следующий шаг roadmap, не этот прогон.
- Timing-контракт: PASS на всех строках с заполненными timing-полями
  (валидатор `validate_mt5_event_frame`); TX-строки timing-полей не несут
  по дизайну и связываются с сигналами на этапе reconciliation:
  252 из 269 TX_OPEN связаны с OPEN-строками, остальные 17 — same-H1
  позиции без polling-OPEN (объяснены поимённо через `same_h1_count`).

## Split disclosure / multiple testing

Прогон использует тот же frozen вход, что 2026-07-30 (никакого нового
отбора). Диапазон тестера покрывает исторические train/val/test периоды —
поэтому любые агрегаты запрещено читать как качество модели. Новых
сравнений/выборов не выполнялось (multiple-testing бюджет не расходовался).

## forbidden_interpretations

- `profit_sum=242.5` (polling-CLOSE) и сумма `profit` по TX_CLOSE `−1755.1` —
  сантехнический выход, НЕ PnL/PF-утверждение; без swap/commission.
- Запрещено: выводы о качестве entry-правила, прибыльности, выбор
  правил/порогов/стопов по этим числам.

## Limitations

- Wine 9.0 помечен терминалом как unsupported — среда нестабильна
  потенциально; фактических крахов в прогоне не было (наблюдение сессии,
  строка предупреждения в журнале терминала не сохранена как артефакт).
- Семантика ORDER_EXPIRED: событие означает «отложник исчез И срок истёк»,
  а не «снят по сроку». Живой просроченный pending события не порождает
  (`lib_ML_Signal.mqh:485`) — последнее размещение 2022.11.30 22:00 всё ещё
  существовало 2022.12.02 08:00 при `max_fill_lag_bars=6`. Это единственный
  «остаток на конце теста»; на batch-этапе такая семантика исказит
  статистику отказов, поэтому экспирацию следует ставить на сам ордер
  (`ORDER_TIME_SPECIFIED`) либо снимать просроченный pending явно.
- Причина слепоты старого polling-CLOSE не доказана на уровне кода
  (помечена как гипотеза); TX-поток делает её некритичной.
- `DEAL_ENTRY_INOUT` (reversal) в прогоне не наблюдался — ветка в коде
  осталась непроверенной на реальных данных.
- Agent-лог за день кумулятивный (утренний + smoke + full), пер-прогонная
  разбивка ERROR-4756 не выделялась (задача следующего шага).

## Decision memo

`continue` — lifecycle закрыт (`UNEXPLAINED=0`,
`same_h1_lifecycle_status=MEASURED:17`), блокер снят. Следующий шаг
roadmap: MT5 `Nero.csv` parity, затем классификация ERROR-4756.
