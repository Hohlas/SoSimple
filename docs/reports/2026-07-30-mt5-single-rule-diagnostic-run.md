# MT5 Single Rule Diagnostic Run — 2026-07-30

Status: DIAGNOSTIC_ONLY

## Context

Первый сквозной прогон MT5 execution loop для одного диагностического правила
(`entry_quality_filter`): entry CSV → MT5 Strategy Tester → `mt5_trade_events.csv`
→ парсер → метрики. План: `docs/superpowers/plans/2026-07-30-mt5-single-rule-diagnostic-run.md`.
Продолжение отчёта `docs/reports/2026-07-29-mt5-execution-loop-migration.md`.

## Stage Level

Диагностика исполнения (execution-loop plumbing). Не эксперимент по отбору
правил, не проверка прибыльности. Уровень этапа по
`docs/methodology/00-research-management.md`: не поисковый и не проверочный —
инфраструктурная диагностика, search budget не расходуется.

## What Was Done

1. Прогон MT5 Strategy Tester (headless, wine + xvfb) с
   `InpMT5_DiagnosticExecutor=true` на XAUUSD H1, 2019.06.20–2022.12.03.
2. Исправлена серия крахов `array out of range` в MQL5 compat-слое
   (см. Changed Files) — до исправлений tester падал в OnInit/OnTester.
3. Добавлен `#property tester_file "mt5_entry_signals.csv"` — без него tester
   agent очищает свой каталог `Files` и сигнальный CSV не находится
   (первый прогон дал единственное событие INIT с
   `entry_signal_file_open_failed`; наблюдение сессии — артефакты первого
   неудачного прогона перезаписаны и не сохранены).
4. Разорвана петля LiveUpdate: скачанный build 6070 в
   `.../AppData/Roaming/MetaQuotes/Terminal/<id>/liveupdate/` заставлял терминал
   выходить сразу после старта; payload перемещён в
   `/tmp/mt5_liveupdate_backup/` (наблюдение сессии; backup вне repo и
   исчезнет при перезагрузке).
5. События распарсены `ML/baseline/parse_mt5_execution_report.py`, схема
   провалидирована, метрики записаны в JSON, артефакты захешированы.

## Multiple Testing Context

Нет нового ML-search. Нет выбора winner/threshold/rule/cost/entry/exit/stop по
результатам tester. Одно заранее выбранное правило, один прогон (плюс
технические перезапуски из-за крахов, не влияющие на выбор).

## Changed Files

- `MT/MQL5/Include/SERVICE.mqh` — `RefreshPriceArrays()` в начале OnInit;
  `iTime()` вместо `Time[Bars-1]` (2 места); `ArrayResize(EXP,...)` в ветке
  `BackTest==0` (EXP[] не расширялся вне `INPUT_FILE_READ()`).
- `MT/MQL5/Include/MAIN.mqh` — `iTime()` вместо `Time[Bars-1]` в конструкторе EXPERT.
- `MT/MQL5/Include/lib_PIC.mqh` — то же в PIC INIT print и `NEW_LEVEL()`.
- `MT/MQL5/Include/MQL4Compat.mqh` — `RefreshPriceArrays()` копирует всю
  историю (было 10000 баров; частичная копия ломала индексы
  `iLowest`/`iHighest` на 20427 барах теста). Файл ранее не отслеживался git;
  добавлен под контроль версий 2026-07-31, sha256
  `19c6faebfdb3ded5a8ecfab5c2cba2bf9e54079395e80764fb83e99cb9e1dfc5`.
- `MT/MQL5/Experts/$o$imple.mq5` — `#property tester_file "mt5_entry_signals.csv"`.
- `ML/baseline/mt5_signal_schema.py` — построчная проверка некорректных
  timestamp (ложный FAIL, когда служебная строка INIT пуста, а торговые строки валидны).
- `MT/MQL5/Profiles/Tester/mt5_single_rule_diagnostic_20260730.set` —
  `InpMT5_ExportNero=true`.

## Verification

- Компиляция: `MetaEditor64.exe /compile` → `0 errors, 0 warnings` (verdict по
  строке Result compile-log, не по exit code wine). Первичный вердикт от
  30.07 относился к предыдущей сборке; 31.07 финальный исходник (не менявшийся
  после старта финального прогона) пересобран заново с тем же результатом,
  лог сохранён: `ML/reports/mt5_execution_loop/mt5_compile_20260731_final.log`
  sha256 `7dbb65f6a3f8854beb77fe9480b1d9a4329b930377609683e0adb23f861c4299`.
- Tester: `Test passed in 0:08:00.858`, OnTester result записан, крахов нет.
- `pytest tests/test_parse_mt5_execution_report.py tests/test_mt5_signal_executor_schema.py`
  → 13 passed.
- `validate_mt5_event_frame` → PASS.
- Тайминг-контракт `feature_time <= feature_available_time <= decision_time <= execution_time`
  выполнен на 2532/2532 торговых строках (ORDER_PLACED/OPEN/CLOSE/ML_CLOSE/ML_EVAL).

## Results

Inputs:

- Source origin CSV: `ML/reports/fractal0_entry_quality_filter_scores.csv`
  sha256 `85a11f8b699658fe1211b5cfdf755c18dba0c0e66ccc2868926a91ce2f64932e`
- Bridge source CSV: `ML/reports/mt5_execution_loop/mt5_entry_source_20260730_entry_quality_filter.csv`
  sha256 `071d12817961c0a7ecaf93966281d3401a78dff0852e3956a3194b0be77cd7d0`
- Entry CSV: `ML/reports/mt5_execution_loop/mt5_entry_signals_20260730_entry_quality_filter.csv`
  sha256 `0b30fc5b6e8da9b2460ed1c21f9203b51b53852bfee531a08c62b33caecf9900`
  (9463 строки; BUY 4494 / SELL 4969)

Tester metadata:

- Terminal: MetaTrader 5 под Wine 9.0, terminal build с LiveUpdate-конфликтом
  (agent build 6061 — подтверждён журналом агента; сервер MetaQuotes-Demo
  build 6074 — наблюдение сессии, сохранённым артефактом не подтверждается)
- Config: `C:\mt5_test.ini` (копия
  `ML/reports/mt5_execution_loop/mt5_single_rule_tester_20260730_entry_quality_filter.ini`;
  путь без пробелов — путь с пробелами в `/config:` парсится с лишней кавычкой)
- Symbol XAUUSD, Period H1, Model 1 (1 minute OHLC), 2019.06.20–2022.12.03,
  Deposit 10000 USD, Leverage 1:500, demo hedging account
- Тест: 4850645 ticks, 20427 bars, history quality 99%
- Runtime Files каталог tester agent:
  `~/.mt5/drive_c/Program Files/MetaTrader 5/Tester/Agent-127.0.0.1-3000/MQL5/Files/`

Outputs:

- Event CSV: `ML/reports/mt5_execution_loop/mt5_trade_events_20260730_entry_quality_filter.csv`
  sha256 `ef88abf44c589222ae1e78c9fa510ad0743fff630223394dbca3d2af505159db` (11256 событий)
- Metrics JSON: `ML/reports/mt5_execution_loop/mt5_execution_metrics_20260730_entry_quality_filter.json`
  sha256 `9a5af9bc89170d26f10cd06da14fa98b3e8ad767e238ee75c13ecc4c18c10494`
- `Nero_MT5.csv` создан (191 МБ, каталог tester agent); parity не проверялась.

Event counts:

| event | count |
|---|---|
| INIT | 1 |
| ORDER_PLACED | 294 |
| OPEN | 252 |
| CLOSE | 18 |
| ML_CLOSE | 53 |
| ML_EVAL | 1915 |
| OPEN_FAILED | 8714 |
| ORDER_EXPIRED | 9 |

Lifecycle:

- missing_open_estimate = 42 (32 `pending order was not found after ORDER_PLACED`
  + 9 ORDER_EXPIRED покрывают 41 из 42; остаток 1 не классифицирован построчно)
- open_without_close_estimate = 234
- CLOSE reasons: `broker_history_limited` = 18 — восстановление закрытий через
  историю ограничено; большинство закрытий позиций не наблюдается H1-опросом
- OPEN_FAILED: 8682 `position_or_pending_order_exists` (одна позиция за раз —
  ожидаемое поведение диагностического executor при 9463 сигналах), 32 см. выше
- same_h1_lifecycle_status=UNKNOWN
  reason=no independent MT5 history/deals or tester report available to detect
  same-H1 open-and-close rows missed by H1 event polling
- Журнал tester agent содержит 690 строк `ERROR-4756` (Trade request send
  failed): 230 `TESTER_FILE_CREATE-72`, 230 `TESTER_FILE_CREATE-91`,
  115 `EXPERT::COUNT`, 85 `EXPERT::OUTPUT`, 11 `SET_SEL`, 4 `SET_BUY`;
  плюс 30 отказов `[Market closed]` (failed buy/sell limit и modify).
  Гипотеза: часть отказов объясняет 32 `pending order was not found` и
  9 ORDER_EXPIRED, но построчная связка не выполнена — неклассифицированный
  остаток. В каталоге агента сохранён `ERROR_SoSimple_163856259.csv` (34 МБ),
  не проанализирован.
- `profit_sum=242.5` в metrics JSON покрывает только 18 наблюдённых CLOSE
  (7% открытий) и не является PnL прогона.
- MT5 `Nero.csv` parity: NOT TESTED (файл создан, построчное сравнение с MT4
  Nero.csv не выполнялось)

## Conclusions

- MT5 execution loop сквозной: сигнальный CSV читается, ордера ставятся,
  события пишутся, парсер и схема проходят, тайминг-контракт выполняется.
- Contract-цепочка работает только после `#property tester_file`; runtime-каталог —
  каталог tester agent, а не терминальный `MQL5/Files`.
- Lifecycle-события неполные: закрытия восстанавливаются ограниченно
  (18 CLOSE при 252 OPEN), это ожидаемое ограничение прототипа на H1-опросе
  без `OnTradeTransaction` (`docs/methodology/13b-mt5-execution-parity.md`).

## Limitations / Open Questions

- Тайминг-контракт тривиален: bridge копирует `signal_time` во все временные
  поля (`time_policy` в манифесте), поэтому PASS не доказывает честность
  доступности признаков — только консистентность формата.
- 234 OPEN без CLOSE: не классифицированы построчно (конец периода vs
  недологированные закрытия).
- Tester HTML report не создан: `Report=` в INI с относительным путём не
  сработал под wine; independent deal-сверка недоступна.
- LiveUpdate: терминал стремится обновиться до build 6070+; payload удалён из
  liveupdate-каталога, при следующем скачивании петля может вернуться.
- `open_without_close_estimate` и `missing_open_estimate` — оценки по
  агрегатам, не по ticket-трассировке.

## Split Disclosure

locked_test не использовался. Tester-диапазон 2019.06.20–2022.12.03 покрывает
период источника сигналов (2019.06.20 16:00 – 2022.12.02 07:00); хвостовой
день 2022.12.03 не содержит сигналов. Никакой выбор по результату не
производился.

## forbidden_interpretations

Запрещено интерпретировать этот прогон как: profitable, production-ready,
доказательство качества правила `entry_quality_filter`, основание для выбора
правил/порогов/стопов, подтверждение Nero parity. Запрещено трактовать
`profit_sum=242.5` как PnL прогона — это сумма profit по 18 наблюдённым CLOSE
(7% открытий), не торговый вывод.

## Next Step

Decision: continue.

1. Классифицировать 234 OPEN-без-CLOSE (ticket-трассировка или
   `OnTradeTransaction`-логирование) перед использованием tester-метрик.
2. Проверить `Nero_MT5.csv` parity против MT4 `Nero.csv` или явно ограничить
   статусом DIAGNOSTIC_ONLY.
3. Только после этого — MT5 batch selection 20–50 кандидатов (roadmap
   `NEXT_AFTER_MT5_SINGLE_RULE`).

## Related Materials

- План: `docs/superpowers/plans/2026-07-30-mt5-single-rule-diagnostic-run.md`
- Манифест: `ML/reports/mt5_execution_loop/mt5_single_rule_run_manifest_20260730_entry_quality_filter.json`
- Методики: `docs/methodology/13b-mt5-execution-parity.md`,
  `docs/methodology/16-reporting-audit.md`, `docs/methodology/03-feature-contract-leakage.md`
- Предыдущий отчёт: `docs/reports/2026-07-29-mt5-execution-loop-migration.md`
