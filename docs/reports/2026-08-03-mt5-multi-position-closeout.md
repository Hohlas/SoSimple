# MT5 Multi-Position Closeout — 2026-08-03

> **Stage level:** `research_hypothesis` · **Allowed verdict:** `DIAGNOSTIC_ONLY` · **Result:** `PASS` (smoke + full batch 32×2; см. «Full Batch 32×2»)

## Research-first disclosure

- lifecycle_status: research_hypothesis
- origin_bias: follow-up to audit `docs/superpowers/audit.md`
- research_priority: medium — needed to determine whether single-position policy is a real execution constraint, but all results remain DIAGNOSTIC_ONLY
- current_search_budget: 0 model/search configurations; MQL5 execution refactor closeout; 3 smoke tester runs (max=1, max=2, max=16); full batch 32 кандидата × 2 режима (max=1, max=64) от 2026-08-07
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
| 7 | «Task 8 Step 2: строка для замены цитируется неточно» («not a bug refactoring plan» vs фактическая русская формулировка) | PASS | использована точная цитата `docs/reports/2026-08-02-mt5-multi-position-probe.md:158` на момент коммита `1351e48` (версия аудита closeout-плана); заменено на «blocking gap in multi-position lifecycle coverage» (коммит `e9f0089`) |
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

Дополнения этапа Full Batch 32×2 (2026-08-07, закоммичены в `c8dc941`):

- `MT/MQL5/Include/lib_ML_Signal.mqh` — три регрессионных фикса:
  (1) `MT5_LogLifecycleForTicket`/`MT5_LogLifecycleForCurrentState` возвращают
  тип и тикет позиции, выбранной ML-выходом, и `ML_TRADE` исполняет закрытие
  через legacy-семантику (`BUY.Val=0`/`SEL.Val=0` + сброс `Pos[].data.Val`);
  (2) верхняя граница окна привязки fill в `MT5_FindFilledTicketForSignal` —
  expiry размещённого ордера (`MT5_LastPlacedExpiry`), а не время следующего
  сигнала; (3) legacy-закрытия при `max=1` больше не игнорируются.
- `MT/MQL5/Include/ORDERS.mqh` — в `MODIFY()` при `MT5_MaxPositions==1`
  close/modify-запросы читаются из legacy BUY/SEL, а не из пересобираемого
  каждый бар `Pos[]` (иначе запросы отбрасывались).
- `ML/baseline/run_mt5_batch.py` — флаг `--only RUN_ID` (диагностический
  прогон одного кандидата; агрегация пропускается для защиты
  `batch_summary.json`).

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
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=1 --force-rerun
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=64 --force-rerun
# → 2026-08-07: оба батча 32/32 done, 0 failed, UNEXPLAINED=0 во всех 64
#   прогонах (с промежуточными перезапусками из-за LiveUpdate, см.
#   «Full Batch 32×2 → Инциденты запуска»).
./.venv/bin/python -m pytest tests/test_mt5_mql5_multiposition_contract.py tests/test_mt5_batch_runtime_contract.py -q
# → 15 passed (после добавления --only и регрессионных фиксов).
```

Паритет max=1 vs эталон 2026-07-31 проверялся pandas-скриптом по парам
`multipos_pilot/reference/<run_id>/events.csv` и `multipos_pilot/max1/<run_id>/events.csv`:
сравнение множеств `(ticket, execution_time)` всех TX_CLOSE и суммы `profit`;
результат 32/32 точных совпадений. Команда воспроизведения:

```bash
./.venv/bin/python -c "
import pandas as pd, pathlib, sys
ref_dir = pathlib.Path('ML/reports/mt5_execution_loop/multipos_pilot/reference')
max1_dir = pathlib.Path('ML/reports/mt5_execution_loop/multipos_pilot/max1')
matches = 0
for ref_run in sorted(ref_dir.iterdir()):
    if not ref_run.is_dir(): continue
    max1_run = max1_dir / ref_run.name
    ref_ev = pd.read_csv(ref_run / 'events.csv', sep=';')
    max1_ev = pd.read_csv(max1_run / 'events.csv', sep=';')
    ref_tx = set(zip(ref_ev[ref_ev.event=='TX_CLOSE'].ticket, ref_ev[ref_ev.event=='TX_CLOSE'].execution_time))
    max1_tx = set(zip(max1_ev[max1_ev.event=='TX_CLOSE'].ticket, max1_ev[max1_ev.event=='TX_CLOSE'].execution_time))
    if ref_tx == max1_tx: matches += 1
    else: print(f'MISMATCH {ref_run.name}', file=sys.stderr)
print(f'{matches}/32 parity matches')
"
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
- Full batch: выполнен 2026-08-07, см. раздел «Full Batch 32×2» ниже.

## Full Batch 32×2 (2026-08-07)

Полный батч 32 кандидатов прогнан в двух режимах: `max=1` (канонический
single-position) и `max=64` (диагностическая мультипозиция; лимит выбран
пользователем). Эталон — артефакты батча 2026-07-31
(`ML/reports/mt5_execution_loop/multipos_pilot/reference/`), сохранённые до
перезаписи. Все 64 прогона: `UNEXPLAINED=0`.

### Паритет режима 1 с эталоном

32/32 кандидата: TX_CLOSE-множества идентичны эталону по тикетам и временам,
прибыль совпадает до цента. Рефакторинг не изменил поведение канонического
режима. Перед достижением паритета на пилоте были найдены и исправлены три
регрессии рефакторинга (см. Changed Files): ML-закрытия не исполнялись,
окно привязки fill обрывалось по времени следующего сигнала, legacy-закрытия
(таймер удержания и др.) игнорировались при `max=1`. Промежуточные прогоны
пилота: 30 → 51 → 89 → 102 сделки — каждый прогон добавлял кандидаты или
применял следующий фикс, поэтому число сделок росло; финальное число 102
соответствует полному паритету 32/32.

### Воронка исполнения, агрегат по 32 кандидатам

| Показатель | max=1 | max=64 |
|---|---|---|
| ORDER_PLACED | 2 601 | 25 103 |
| TX_OPEN / TX_CLOSE | 2 508 / 2 508 | 23 932 / 23 932 |
| не исполнено (expired/failed) | 93 (3.6%) | 1 171 (4.7%) |
| Суммарная прибыль (без свопа/комиссии) | −10 209.5 | −114 622.9 |
| PF | 0.910 | 0.895 |
| Win rate | 39.0% | 43.3% |
| Прибыль BUY / SELL | +1 035.3 / −11 244.8 | +21 145.8 / −135 768.7 |
| UNEXPLAINED | 0 | 0 |

- Все открытые позиции в обоих режимах закрыты (TX_OPEN == TX_CLOSE у всех
  32 кандидатов). Источники закрытий max=64: `EXPERT` 16 881 (70.5%),
  `SL` 7 051 (29.5%).
- Timing-контракт (`decision_time <= execution_time`): 112 865 проверенных
  строк max=64, нарушений 0.
- Максимум одновременных позиций: 17
  (`simple_combined_extra_trees_small_12h_thr0.2`) — лимит 64 ни разу не
  достигнут; размещение упирается в частоту сигналов (один planned order на
  бар), а не в гейт.
- Мультипозиция исполняет ~9.6× больше размещений, чем канонический режим
  (25 103 против 2 601): single-position гейт действительно был главным
  ограничителем числа позиций, что подтверждает исходную мотивацию работы.
- Убыток в обоих режимах сосредоточен в SELL-позициях; у всех 32 кандидатов
  кроме одного (`time_plus_atr_extra_trees_small_12h_thr0.05`, +660.4) режим
  max=64 дал отрицательный итог. Это наблюдение о механике исполнения
  DIAGNOSTIC_ONLY периода 2021.01–2021.06 (полный батч-период), не оценка
  качества моделей.

### Инциденты запуска

- LiveUpdate терминала дважды скачивал payload build 6096 и прерывал батч
  (кандидаты 4/32 и 12/32). Payload вынесен в `/tmp/mt5_liveupdate_backup/`,
  каталог `liveupdate/` переведён в read-only (`chmod 555`) — по прежней
  практике проекта (`docs/reports/2026-07-30-mt5-single-rule-diagnostic-run.md`).
- Skip-гейт раннера пропускал кандидатов по наличию метрик с `UNEXPLAINED=0`,
  не различая режим; ложные пропуски устранены повторным запуском с
  `--force-rerun` / точечным удалением метрик чужого режима. Данные не
  потеряны: артефакты каждого режима сохранялись сразу после прогона.

### Артефакты

- `ML/reports/mt5_execution_loop/multipos_pilot/reference/<run_id>/` — эталоны
  2026-07-31 (32 кандидата).
- `ML/reports/mt5_execution_loop/multipos_pilot/max1/<run_id>/`,
  `.../max64/<run_id>/` — `metrics.json` + `events.csv` обоих режимов.
- `ML/reports/mt5_execution_loop/batch/<run_id>/` — восстановлены эталонные
  артефакты; `batch_summary.json` не пересобирался (фаза aggregate не
  запускалась, `--only`-прогоны агрегацию пропускают).

## Conclusions

Closeout закрыл 10/10 пунктов аудита `docs/superpowers/audit.md` (версия
`1351e48`). Backcompat max=1 доказан event-level паритетом 32/32 кандидатов
с эталоном 2026-07-31 (TX_CLOSE-множества идентичны, прибыль совпадает до
цента). Multi-pos механика доказана smoke max=2/16 (полный lifecycle, 0
timing/binding нарушений) и full batch max=64 (32/32 `UNEXPLAINED=0`, все
позиции закрыты). Вердикт этапа: `DIAGNOSTIC_ONLY`.

Открытые вопросы: (1) `iSignal == 5` (`ML_TRADE_TB`) вне покрытия closeout —
риск требует оценки приоритета переноса фиксов (см. Limitations); (2)
`InpMT5_MaxPositions` не является жёстким лимитом — фактический лимит зависит
от частоты сигналов и скорости fill (см. Limitations); (3) multi-tester
(per-expert magic) не реализован — план `2026-08-03-mt5-per-expert-ml-tracker.md`.

## Limitations

- Multi-pos проверяется только через `iSignal == 3` (`ML_TRADE`,
  `MT5_DiagnosticExecutor=true`). `iSignal == 5` (`ML_TRADE_TB` в
  `lib_ML_Signal_TB.mqh`) вне покрытия; отдельный план
  `2026-08-03-mt5-per-expert-ml-tracker.md`. Риск: если `ML_TRADE_TB`
  используется в production-прогонах, его multi-pos механика может содержать
  те же дефекты, что и `ML_TRADE` до closeout (ML-закрытия не исполнялись,
  окно привязки fill обрывалось, legacy-закрытия игнорировались). Текущий
  статус: `iSignal == 5` не используется в диагностических прогонам closeout
  (все 32 кандидата — `iSignal == 3`), поэтому срочность переноса фиксов
  требует уточнения у пользователя.
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
  (`simple_combined_extra_trees_small_3h_thr0.05`). Полный батч 32 кандидатов
  выполнен 2026-08-07 для `max=1` и `max=64` (полный период батча);
  для `max=2`/`max=16` по-прежнему только smoke.
- Число входящих ML-сигналов (`entry_signals.csv`) сохранено только для
  пилотного кандидата, поэтому доля «сигнал → размещение» (затенение
  дублей на одном баре) количественно оценена только для него
  (954/1080 размещено); для остальных 32 используется косвенный показатель
  ORDER_PLACED.
- Статические MQL5-тесты — текстовые guards, не замена тестеру; тестерные smoke
  выполнены и приведены выше.

## Split Disclosure

- **Backcompat (`max=1`)**: полный батч 32 кандидатов 2026-08-07 — event-level
  паритет с эталоном 2026-07-31: 32/32 точных совпадений TX_CLOSE
  (тикеты/времена/прибыль).
- **Multi-pos smoke (`max=2`, `max=16`)**: PASS — lifecycle полный,
  timing/binding нарушения отсутствуют.
- **Multi-pos full batch (`max=64`)**: выполнен 2026-08-07, 32/32
  `UNEXPLAINED=0`, все позиции закрыты; интерпретация только DIAGNOSTIC_ONLY.
- **Multi-pos full batch (`max=2`, `max=16`)**: `NOT_RUN` → `UNKNOWN`.
- Вердикт этапа: `DIAGNOSTIC_ONLY`.

## Forbidden Interpretations

- Не интерпретировать результаты как profitable / ready / live-ready / tradable.
- Не выбирать winner и не открывать `locked_test`.
- `InpMT5_MaxPositions>1` не является торговым режимом.
- Smoke-совпадение счётчиков не является event-level доказательством backcompat.

## Next Step

1. Коммит `c8dc941` содержит все три фикса этапа Full Batch 32×2; паритет
   max=1 воспроизводится на HEAD.
2. Обновить `docs/methodology/13b-mt5-execution-parity.md` (строки 145-153):
   per-ticket lifecycle реализован в closeout 2026-08-03 (multi-ticket tracker,
   swap-remove, per-ticket OPEN/ML_EVAL/ML_CLOSE/CLOSE); осталось multi-tester
   (per-expert magic) — план `2026-08-03-mt5-per-expert-ml-tracker.md`.
3. При необходимости — полный батч 32 кандидатов для max=2 и max=16
   (`--phase tester --max-positions=N --force-rerun` + `--phase aggregate`);
   решение принимается отдельно с учётом стоимости.
4. Затем — план `2026-08-03-mt5-per-expert-ml-tracker.md` (зависит от этого
   closeout и теперь разблокирован).
5. ACTIVE-трек roadmap не меняется: «MT5 entry mechanics / trade-count frozen
   probe» остаётся направлением.

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
  `ML/reports/mt5_execution_loop/batch/_smoke/metrics.json`,
  `ML/reports/mt5_execution_loop/multipos_pilot/{reference,max1,max64}/`
  (этап Full Batch 32×2), `/tmp/mt5_liveupdate_backup/` (вынесенный payload
  LiveUpdate build 6096)
