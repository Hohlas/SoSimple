# MT5 Multi-Position Closeout — 2026-08-03

> **Stage level:** `research_hypothesis` · **Allowed verdict:** `DIAGNOSTIC_ONLY` · **Result:** `PASS` (smoke-level; full batch `NOT_RUN`)

## Research-first disclosure

- lifecycle_status: research_hypothesis
- origin_bias: follow-up to audit `docs/superpowers/audit.md`
- research_priority: medium — needed to determine whether single-position policy is a real execution constraint, but all results remain DIAGNOSTIC_ONLY
- current_search_budget: 0 model/search configurations; MQL5 execution refactor closeout; 3 smoke tester runs (max=1, max=2, max=16) listed below
- cumulative_search_budget: inherited from 2026-07-31 batch, 2026-08-01 diagnostics, 2026-08-02 multi-position refactor
- next_probe_freeze: no ML winner selection; next execution probe must use fixed max_positions values and saved candidates only
- allowed_max_verdict: DIAGNOSTIC_ONLY
- forbidden_interpretations: profitable, ready, live-ready, tradable, new winner, model-quality proof

## Context

Закрытие замечаний аудита по MT5 multi-position refactor
(`docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md`, отчёт
`docs/reports/2026-08-02-mt5-multi-position-probe.md`). Проба 2026-08-02
заблокировалась на single-ticket диагностическом трекере
(`MT5_LogLifecycleForCurrentState`): в multi-pos режиме он привязывал новый
сигнал к старому тикету и нарушал timing-контракт. Closeout переводит
диагностику на multi-ticket tracker, чинит order-placement гейт и side-safe
закрытие, добавляет принудительный пересчёт батча (`--force-rerun`) и
доказывает работоспособность smoke-прогонами max=1/2/16.

Scope: только `iSignal == 3` (`ML_TRADE`, `MT5_DiagnosticExecutor=true`).
`InpMT5_MaxPositions=1` — канонический режим; `>1` — только диагностическая
проверка механики исполнения, не торговый режим.

## Audit Findings Addressed

Аудит `docs/superpowers/audit.md` перезаписывается каждым новым аудитом,
поэтому ниже каждая строка содержит краткую цитату сути пункта. Формулировки
пунктов восстановимы через git: версия аудита данного closeout-плана лежит в
коммите `1351e48` (`git show 1351e48:docs/superpowers/audit.md`), предшествующая
версия (аудит per-expert плана) — в коммите
`f0d20673805d3e93708bc5c8e911ab08c692b5b1`
(`git show f0d20673805d3e93708bc5c8e911ab08c692b5b1:docs/superpowers/audit.md`).

| Audit item | Суть (краткая цитата) | Status | Evidence |
|---|---|---|---|
| 1 | «проверка связки сигнал→тикет использует несуществующую колонку `idx`» — сигнальный индекс пишется в `request_seq` | PASS | Task 7 Step 5 выполнен по колонке `request_seq` (фильтр `>= 0`); `binding_violations: 0` для max=1/2/16 |
| 2 | «удаление singleton-состояния не покрывает все места использования `MT5_TrackedMagic`» (строки 185, 308, 309, 407, 764) | PASS | все точки закрыты: 185/407 → `MT5_LastPlacedMagic`, 308-309 → per-event `magic`, 764 удалено; `rg "MT5_TrackedMagic\|MT5_TrackedTicket\|MT5_TrackedIdx\|MT5_TrackedOpenLogged" MT/MQL5/Include/` → пусто; коммит `278ab99` |
| 3 | «0 warnings недостижим без правки `MQL4Compat.mqh`» (`OrderSelect_MQL4(int index, ...)` + макрос `#define OrderSelect`) | PASS | добавлены `OrderSelectByTicket_MQL4(ulong, int)` и `ulong`-перегрузка `OrderSelect_MQL4`; compile log: `Result: 0 errors, 0 warnings` |
| 4 | «код теста в тексте Task 1 Step 1 содержит синтаксическую ошибку Python» (regex) | PASS | закоммиченный тест содержит корректные regex (`tests/test_mt5_mql5_multiposition_contract.py`, коммит `4b7eddd`); текст плана обновлён в `1351e48` |
| 5 | «sentinel `DATETIME_MAX` не определён в дереве MT» | PASS | введена локальная константа `const datetime MT5_NO_HI_BOUND = D'2100.01.01 00:00';` (`lib_ML_Signal.mqh`) |
| 6 | «усиление A5 фактически не проверяет компакцию» (ветка `or "close_logged"`) | PASS | assertion ужесточён до `assert "MT5_TrackedPositionCount--" in ml_signal` (коммит `278ab99`) |
| 7 | «Task 8 Step 2: строка для замены цитируется неточно» («not a bug refactoring plan» vs фактическая русская формулировка) | PASS | использована точная цитата `docs/reports/2026-08-02-mt5-multi-position-probe.md:158`; заменено на «blocking gap in multi-position lifecycle coverage» (коммит `e9f0089`) |
| 8 | «мелкий сдвиг номеров строк `INPUT.mqh`» (16-27, а не 18-32) | CLOSED/NOTED | документационное замечание; кодовых изменений не требует |
| 9 | «где физически искать `ambiguous_fills_in_window`» | PASS | путь зафиксирован: `/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/Tester/logs/<дата>.log` и `.../Tester/Agent-127.0.0.1-3000/logs/<дата>.log`; grep по обоим журналам → 0 совпадений |
| 10 | «воспроизводимость ссылок на `docs/superpowers/audit.md`» | PASS | в данном отчёте каждая строка таблицы содержит цитату, а в Related Materials — SHA коммитов с версиями audit.md |

Пункты прежнего аудита, встроенные в текст closeout-плана под идентификаторами
U2/U4/U5, V1-V3, A2/A4/A5/A6/A8/A10/A13/A14, закрыты самой реализацией:
нормализованные regex legacy-гейта (U2, тест `test_set_buy_sell_...`), удаление
мёртвого `CountActiveByType` (U4), directory-wide grep ticket-кастов (U5, вывод
пуст), `--smoke-only` режим (V1), гейт считает только MARKET-позиции и это
задокументировано (V2), окно привязки fill→signal + логирование неоднозначностей
(V3, `MT5_FindFilledTicketForSignal`), передача ticket без `(int)`-кастов (A2),
запрет rebind tracked ticket (A4), swap-remove компакция (A5), `force_rerun`
семантика без удаления `entry_signals.csv` (A6), единый канонический compile-лог
(A8), `research_priority` в disclosure (A10), исправление всех битых команд
старого плана (A13), `build_arg_parser()` без дублирования существующих флагов (A14).

## Changed Files

- `MT/MQL5/Include/lib_ML_Signal.mqh` — `MT5_TRACKED_POSITION`/`MT5_TrackedPositions[]`,
  `MT5_FindTrackedIndexByTicket`, `MT5_AddTrackedPosition` (A4/A5 guards),
  `MT5_FindFilledTicketForSignal` (decision-time окно + WARN ambiguity),
  `MT5_LogLifecycleForTicket` (OPEN/ML_EVAL/ML_CLOSE/CLOSE per ticket, swap-remove),
  переписанный `MT5_LogLifecycleForCurrentState`, удалены все singleton-переменные.
- `MT/MQL5/Include/MQL4Compat.mqh` — `OrderSelectByTicket_MQL4(ulong, int)` helper,
  `ulong`-перегрузка `OrderSelect_MQL4`, исправление history-ветки: поиск закрытия
  по `DEAL_POSITION_ID == ticket` вместо обращения к истории по deal-тикету.
- `MT/MQL5/Include/FUNCTIONS.mqh`, `ORDERS.mqh`, `OUTPUT.mqh`, `INPUT.mqh` —
  изменения Tasks 2-3 (коммиты `b1a714d`, `c9563fa`): `ulong ticket`,
  `CountActiveBySide`, `CanPlaceBuyOrder()/CanPlaceSellOrder()`, side-check до
  `price == 0`, удаление `BuyPosCnt`/`CountActiveByType`.
- `ML/baseline/run_mt5_batch.py` — `build_arg_parser()`, `--force-rerun`,
  `--smoke-only`, skip-override в `run_batch` (коммит `b2d9497`).
- `tests/test_mt5_mql5_multiposition_contract.py` — статические contract-тесты
  (коммиты `4b7eddd`, `278ab99`).
- `docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md`,
  `docs/reports/2026-08-02-mt5-multi-position-probe.md` — исправление битых
  команд и overclaims (коммит `e9f0089`).

## Verification

Все команды выполнялись из `/home/hohla/git/SoSimple`.

```bash
./.venv/bin/python -m pytest tests/test_mt5_mql5_multiposition_contract.py tests/test_mt5_batch_runtime_contract.py tests/test_parse_mt5_execution_report.py tests/test_mt5_signal_executor_schema.py -q
# → 44 passed
git diff --check
# → пусто
rg -n "\(int\)OrderTicket\(\)|\(int\)Pos\[|\(int\)ticket|\(int\)MT5_" MT/MQL5/Include/
# → пусто (остаток только в комментарии)
rg -n "MT5_TrackedMagic|MT5_TrackedTicket|MT5_TrackedIdx|MT5_TrackedOpenLogged" MT/MQL5/Include/
# → пусто
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' \
  /compile:'/home/hohla/git/SoSimple/MT/MQL5/Experts/$o$imple.mq5' \
  /log:'/tmp/sosimple_mt5_compile_closeout.log'
iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile_closeout.log | tail -n 2
# → Result: 0 errors, 0 warnings, 5515 ms elapsed, cpu='X64 Regular'
#   (.ex5 пересобран: MT/MQL5/Experts/$o$imple.ex5, mtime позже старта компиляции;
#    batch-лог компиляции /tmp/sosimple_mt5_batch_compile.log согласован: 0 errors, 0 warnings)
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=1 --force-rerun --smoke-only
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=2 --force-rerun --smoke-only
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=16 --force-rerun --smoke-only
# → все три: Smoke test PASSED, UNEXPLAINED=0, без "--- FULL BATCH ---"
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=2 --force-rerun
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=16 --force-rerun
# → NOT_RUN: осознанное решение по стоимости (32 тестерных прогона на каждое
#   значение max); smoke-закрытие достаточно для DIAGNOSTIC_ONLY, batch-сравнение
#   остаётся UNKNOWN.
```

Проверки timing/binding/reconciliation выполнялись inline-скриптами pandas по
`ML/reports/mt5_execution_loop/batch/_smoke/events.csv` (sep=`;`) и сохранённым
копиям прогонов; отдельный utility-файл не создавался (ручных проверок достаточно):

- timing (`decision_time > execution_time`): max=1 checked 282 / violations 0;
  max=2 checked 487 / violations 0; max=16 checked 540 / violations 0;
- binding (`ticket → request_seq` уникальность, signal-linked события):
  max=1 checked 2 / violations 0; max=2 checked 32 / violations 0;
  max=16 checked 36 / violations 0;
- reconciliation: `UNEXPLAINED=0` во всех трёх прогонах.

## Results

| Прогон | SMOKE RESULT | timing violations | binding violations | max одновременных позиций (BUY/SELL) |
|---|---|---|---|---|
| `--max-positions=1 --force-rerun --smoke-only` | positions=3, UNEXPLAINED=0 | 0 | 0 | 1 / 1 (single-pos канон) |
| `--max-positions=2 --force-rerun --smoke-only` | positions=68, UNEXPLAINED=0 | 0 | 0 | 4 / 3 |
| `--max-positions=16 --force-rerun --smoke-only` | positions=74, UNEXPLAINED=0 | 0 | 0 | 4 / 3 |

- Backcompat (`=1`): smoke после всех правок воспроизводит `positions=3, UNEXPLAINED=0`;
  описывается как smoke — event-level сравнение с pinned baseline не выполнялось.
- Multi-pos механика: smoke max=2/max=16 проходят полный lifecycle
  (ORDER_PLACED → OPEN → ML_EVAL → TX_CLOSE → CLOSE) без нарушений
  timing-контракта и без неоднозначных привязок сигнал→тикет
  (`ambiguous_fills_in_window` в журналах тестера: 0).
- Найден и исправлен дефект, проявившийся только при max=16: history-ветка
  `OrderSelect_MQL4` читала историю по deal-тикету, тогда как tracked ticket —
  это id позиции (пример: позиция 95 закрыта сделкой с тикетом 91). Коллизия
  давала CLOSE-строку с `execution_time` раньше `decision_time` (1 нарушение).
  Исправлено поиском по `DEAL_POSITION_ID` (коммит `9b2c835`); повторные прогоны
  всех трёх max — чистые.
- Full batch: `NOT_RUN`; сравнение batch-артефактов между max-режимами — `UNKNOWN`.

## Limitations

- Multi-pos проверяется только через `iSignal == 3` (`ML_TRADE`,
  `MT5_DiagnosticExecutor=true`). `iSignal == 5` (`ML_TRADE_TB` в
  `lib_ML_Signal_TB.mqh`) вне покрытия; отдельный план
  `2026-08-03-mt5-per-expert-ml-tracker.md`.
- `set.BUY`/`set.SEL` (`INPUT.mqh:13-14`) остаются singleton pending-очередью:
  один planned order на бар, несколько однонаправленных позиций возникают только
  через серию баров. Мультипозиция доказана фактически: в smoke max=2
  одновременно открыто до 4 BUY и 3 SELL позиций (больше лимита, см. ниже).
- Гейт размещения считает только MARKET-позиции (`CountActiveBySide`,
  `PositionSelectByTicket` не видит pending). Поэтому при задержке заполнения
  несколько pending накапливаются и после fill одновременных позиций может быть
  больше `InpMT5_MaxPositions` (наблюдено: 4 BUY при max=2). Это задокументированный
  контракт гейта (audit V2), а не баг closeout; pending-семантика отслеживается
  диагностическим логгером отдельно.
- Multi-expert (`ExpTotal>1`) и per-expert ML-CSV (`rule_id` filter) вне покрытия.
- `CLOSE`-событие читает историю MT5 по тикету позиции и использует placeholder
  `broker_history_limited` для причины закрытия, `order_close_price`,
  `take_profit`, `swap`, `commission`
  (`docs/methodology/13b-mt5-execution-parity.md:138-141`); сверка с MT5 deals
  в этом closeout не выполнялась.
- Smoke-период: Model=2, 2021.01.04–2021.03.31, один кандидат
  (`simple_combined_extra_trees_small_3h_thr0.05`); полный батч 32 кандидатов
  для max=2/max=16 не запускался (`NOT_RUN`).
- Статические MQL5-тесты — текстовые guards, не замена тестеру; тестерные smoke
  выполнены и приведены выше.

## Split Disclosure

- **Backcompat (`max=1`)**: smoke PASS с `--force-rerun` (SKIP-гейт отключён;
  32/32 SKIP больше не принимается как доказательство). Формулировка — smoke-only,
  event-level сравнение не выполнялось.
- **Multi-pos smoke (`max=2`, `max=16`)**: PASS — lifecycle полный,
  timing/binding нарушения отсутствуют.
- **Multi-pos full batch**: `NOT_RUN` → `UNKNOWN`.
- Вердикт этапа: `DIAGNOSTIC_ONLY`.

## Forbidden Interpretations

- Не интерпретировать результаты как profitable / ready / live-ready / tradable.
- Не выбирать winner и не открывать `locked_test`.
- `InpMT5_MaxPositions>1` не является торговым режимом.
- Smoke-совпадение счётчиков не является event-level доказательством backcompat.

## Next Step

1. При необходимости — полный батч 32 кандидатов для max=2 и max=16
   (`--phase tester --max-positions=N --force-rerun` + `--phase aggregate`);
   решение принимается отдельно с учётом стоимости.
2. Затем — план `2026-08-03-mt5-per-expert-ml-tracker.md` (зависит от этого
   closeout и теперь разблокирован).
3. ACTIVE-трек roadmap не меняется: «MT5 entry mechanics / trade-count frozen
   probe» остаётся направлением (закрытие выполнено только на smoke-уровне).

## Related Materials

- План: `docs/superpowers/plans/2026-08-03-mt5-multi-position-closeout.md`
- Предыдущий отчёт: `docs/reports/2026-08-02-mt5-multi-position-probe.md`
- Методики: `docs/methodology/13b-mt5-execution-parity.md`,
  `docs/methodology/16-reporting-audit.md`
- Аудит (версии в git): `git show 1351e48:docs/superpowers/audit.md`
  (аудит данного плана, пункты 1-10),
  `git show f0d20673805d3e93708bc5c8e911ab08c692b5b1:docs/superpowers/audit.md`
  (предшествующая версия)
- Коммиты closeout: `4b7eddd` (тесты), `b1a714d` (Task 2), `c9563fa` (Task 3),
  `278ab99` (Task 4), `b2d9497` (Task 5), `9b2c835` (Task 6 фикс history-биндинга),
  `e9f0089` (Task 8 docs)
- Артефакты: `/tmp/sosimple_mt5_compile_closeout.log`,
  `ML/reports/mt5_execution_loop/batch/_smoke/events.csv`,
  `ML/reports/mt5_execution_loop/batch/_smoke/metrics.json`
