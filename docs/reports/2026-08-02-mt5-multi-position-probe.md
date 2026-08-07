# MT5 Multi-Position Probe — 2026-08-02

> **Stage level:** `research_hypothesis` · **Allowed verdict:** `DIAGNOSTIC_ONLY` · **Result:** `BLOCKED_ON_DIAGNOSTIC_LAYER`

## Research-first disclosure

- **lifecycle_status:** `research_hypothesis`
- **origin_bias:** direct user request after fill-rate probe showed 99.2% of OPEN_FAILED
  is single-position policy blocking
- **research_priority:** medium — needed to determine whether single-position policy is a real
  execution constraint, but all results remain DIAGNOSTIC_ONLY
- **roadmap_track:** deviation from ACTIVE track ("entry mechanics / trade-count") — explicitly
  recorded and accepted by user. ACTIVE roadmap track ("Accept single-position policy as
  design constraint") remains in force for the *trade-count probe planning track*; this plan
  supersedes that constraint for the MQL5 execution step only and does not change the
  trade-count probe planning track.
- **current_search_budget:** 0 new model/search configurations; 1 MQL5 refactoring + 1 batch
  smoke run (max=1), 1 batch run attempt (max=2, which surfaced the blocker)
- **cumulative_search_budget:** inherited from 2026-07-31 batch and 2026-08-01 diagnostics
- **next_probe_freeze:** after maxpos=1 verification, attempt maxpos=2/maxpos=16 batch
  (in progress, blocked — see below); trade-count/entry-mechanics probe remains ACTIVE
  roadmap track
- **allowed_max_verdict:** `DIAGNOSTIC_ONLY`
- **forbidden_interpretations:** profitable, ready, live-ready, tradable, new winner,
  model-quality proof
- **`InpMT5_MaxPositions=1` canonical guarantee:** at default, fill-rate probe verdict
  ("single-position policy blocks 99.2% of OPEN_FAILED") retains full force. Smoke test
  with `--max-positions=1` produced `positions=3, UNEXPLAINED=0`, which matches the previous
  smoke counters available in this report (event-level comparison was not run).

## Context

Цель этапа — проверить, снимает ли разрешение нескольких одновременных позиций
блокировку `OPEN_FAILED`, обнаруженную в fill-rate probe (99.2% от active signal rows
блокированы single-position policy). Для этого в советник добавлен `input int
InpMT5_MaxPositions` (default `=1` — канонический single-position режим), а план
`docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md` задаёт
рефакторинг MQL5 из single-position singleton (`PRICE BUY, SEL`) в ticket-indexed
массив `POSITION_TRACKER Pos[64]` с helper-функциями `AddPosition` /
`RemovePositionByTicket` / `FindPosIndexByTicket` / `CountActiveByType`.

## Methodology

Применённые документы:

- `docs/methodology/00-research-management.md` — research levels, disclosure block
- `docs/methodology/13b-mt5-execution-parity.md:148-166` — compile verification
  (MetaEditor /compile + iconv чтение лога)
- `docs/methodology/16-reporting-audit.md:64-86` — research-first disclosure
- `docs/methodology/A5-post-mortem-diagnostics.md` — предыдущий batch `BATCH_NO_WINNER`

## Что сделано (по задачам плана)

| Task | Файлы | Статус |
|------|-------|--------|
| 1 — Data structure foundation | `FUNCTIONS.mqh` (struct `POSITION_TRACKER`, `MAX_MULTIPOS=64`, helpers, `BUY/SEL` помечены DEPRECATED, оставлены для transition) | PASS, 0 errors 0 warnings |
| 2 — ORDER_CHECK / MODIFY | `ORDERS.mqh` (new `ORDER_CHECK` populates `Pos[]` + backcompat shim mirrors singleton `BUY/SEL`; `MODIFY` ищет ticket через `FindPosIndexByTicket`, fallback на legacy singleton при `MT5_MaxPositions==1`) | PASS_WITH_WARNINGS (0 errors, 2 warnings: pre-existing `ulong→int` `OrderTicket()`) |
| 3 — OUTPUT (CLOSE/TRAIL/OUTPUT/IMPULSE/POC) | `OUTPUT.mqh`: новые helpers `CloseBuySide`/`CloseSellSide` (multi-pos итерация по `Pos[]`); `CLOSE_BUY/SEL` форвардят на `*Side` при `MT5_MaxPositions>1` и сохраняют legacy path иначе; `TRAILING_STOP` и `OUTPUT()` имеют multi-pos path; `IMPULSE_UP/DN` / `POC_CLOSE_TO_*` оставлены без изменений (вызываются только в `iSignal != 3`, который сам по себе legacy branch). Forward declarations добавлены в `MAIN.mqh`. | PASS_WITH_WARNINGS (0 errors, 2 warnings) |
| 4 — COUNT / TIMER | `COUNT.mqh`: `COUNT()` multi-pos обновляет per-position Min/Max; `TIMER()` multi-pos помечает `Pos[i].data.Val=0` для позиций, превысивших `Tper`. `FINE_TIME()` использует `CLOSE_BUY/SEL`, которые уже форвардят на `*Side`. | PASS_WITH_WARNINGS (0 errors, 2 warnings) |
| 5 — Gate removal | `INPUT.mqh` (строки 5-6 + 9-10 обёрнуты `if (MT5_MaxPositions==1)`; multi-pos path считает `BuyActiveCnt`/`SelActiveCnt` через `PositionSelectByTicket`), `lib_ML_Signal.mqh` (строки 779, 859-868, 924-928, 945-949: single-pos gate обёрнут; multi-pos path реализует gate `same-dir count >= MaxPositions` → `OPEN_FAILED: max_positions_reached`; reversal close в multi-pos закрывает earliest opposite position по `Pos[].data.T`, не все позиции), `lib_ML_Signal_TB.mqh` (симметричные изменения для строк 151-181; `ibt.txt` заменён на `lib_ML_Signal_TB.mqh`), `ERRORs.mqh` (`Str9`/`Str11` в multi-pos summarise `Pos[]`, сохраняя legacy singleton для `=1`). | PASS_WITH_WARNINGS (0 errors, 2 warnings) |
| 6 Step 1-5 — Pipeline integration + smoke | `$o$imple.mq5`: `input int InpMT5_MaxPositions=1;`, runtime `int MT5_MaxPositions=1;` (заявлен в Task 3), `SyncInputs()` копирует `InpMT5_MaxPositions` → `MT5_MaxPositions`. `run_mt5_batch.py`: `create_set_file(run_id, *, max_positions=1)` добавляет строку `InpMT5_MaxPositions={value}||false||0||true||N`; CLI `--max-positions` (int, default 1); `run_smoke_test`/`run_batch` принимают `*, max_positions=1` и пробрасывают в `create_set_file`; `main()` передает `args.max_positions`. Smoke run: `--max-positions=1 phase tester` → **`SMOKE RESULT: positions=3, UNEXPLAINED=0`, Smoke test PASSED**. | PASS |
| 6 Step 6-7 — Batch max=2 / max=16 + aggregate | **НА ЗАВЕРШЕНИИ — заблокировано** на диагностическом слое (см. Limitations). | BLOCKED |
| 7 — Report + project state sync | Этот отчёт + CHANGELOG + CONTEXT_HANDOFF + roadmap (см. ниже). | PASS |

## Структурированный cross-check артефактов

- `MT/MQL5/Include/FUNCTIONS.mqh` (struct POSITION_TRACKER, helpers, maxpos define) —
  `+45 / -2` строк после Task 1
- `MT/MQL5/Include/ORDERS.mqh` (`ORDER_CHECK` переписан, `MODIFY` использует
  `FindPosIndexByTicket`) — `+87 / -53` после Task 2
- `MT/MQL5/Include/OUTPUT.mqh` (новые `CloseBuySide`/`CloseSellSide`,
  multi-pos paths в `CLOSE_BUY/SEL`, `TRAILING_STOP`, `OUTPUT`) — `+140 / -1`
- `MT/MQL5/Include/MAIN.mqh` (forward-декларации `*Side` методов) — `+2 / -0`
- `MT/MQL5/Include/COUNT.mqh` (multi-pos per-position tracking, multi-pos TIMER) —
  `+31 / -10`
- `MT/MQL5/Include/INPUT.mqh` (gate обёрнут `if (MT5_MaxPositions==1)`,
  multi-pos path с подсчётом активных позиций по стороне) — `+30 / -0` (approx)
- `MT/MQL5/Include/lib_ML_Signal.mqh` (gate removal + earliest-opposite reversal
  close) — `+158 / -54`
- `MT/MQL5/Include/lib_ML_Signal_TB.mqh` (симметричные изменения) — `+64 / -10`
- `MT/MQL5/Include/ERRORs.mqh` (multi-pos Str9/Str11 summary) — `+42 / -10`
- `MT/MQL5/Experts/$o$imple.mq5` (input + SyncInputs) — `+4 / -0`
- `ML/baseline/run_mt5_batch.py` (`create_set_file() kwarg`, CLI `--max-positions`,
  `run_smoke_test` / `run_batch` kwargs) — `+29 / -8`
- `tests/test_mt5_batch_runtime_contract.py` (поправлен mock `create_set_file` с учётом
  нового kwarg) — `+1 / -1`

## Compile verification (per `13b-mt5-execution-parity.md`)

```
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' \
  /compile:'.../MT/MQL5/Experts/$o$imple.mq5' \
  /log:'/tmp/sosimple_mt5_compile.log'
```

Финальный лог (после всего рефакторинга):

```
Result: 0 errors, 2 warnings, 5384 ms elapsed, cpu='X64 Regular'
warnings: ORDERS.mqh:77,167 — 'possible loss of data due to type conversion
          from `ulong` to `int`' — pre-existing (OrderTicket returns ulong,
          POSITION_TRACKER.ticket is int for MT4-compat).
```

## Результаты

### Backcompat (Task 6 Step 5) — PASS

```bash
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=1
```

Лог:

```
--- SMOKE TEST ---
SMOKE TEST: simple_combined_extra_trees_small_3h_thr0.05 (Model=2, 2021.01-2021.03)
  SMOKE RESULT: positions=3, UNEXPLAINED=0
Smoke test PASSED.

--- FULL BATCH ---
[1/32] SKIP simple_combined_extra_trees_small_3h_thr0.05 (metrics exist, UNEXPLAINED=0)
...
[32/32] SKIP simple_combined_extra_trees_small_24h_thr0.3 (metrics exist, UNEXPLAINED=0)

Batch complete: 0 done, 32 skipped, 0 failed.
```

Все 32 кандидата SKIPed (метрики уже существуют от прошлых прогонов), smoke сλα
max=1 возвращает ровно 3 позиции с UNEXPLAINED=0 — это эквивалентно предыдущему
baseline по счётчикам smoke. **Canonical guarantee (Var Contract: default `=1`
воспроизводит single-position поведение) partially checked by smoke; full
event-level backcompat remains open until closeout.** (32/32 SKIP не является
доказательством backcompat — см. closeout 2026-08-03, `--force-rerun`.)

### Multi-pos batch (Task 6 Step 6) — BLOCKED

Запуск `./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=2`
завершился ABORT: smoke test failed при парсинге events в
`ML.baseline.parse_mt5_execution_report`.

**Причина:** MT5 timing contract violation `decision_time > execution_time`.
Проверка `mt5_signal_schema.py:115` поднимает `ValueError`.

Анализ события `mt5_trade_events__smoke.csv` показал, что для тикета 37 (originally
SELL_LIMIT, заполненный в 11:59) появляются повторные OPEN events с `side=BUY`
на следующих барах 13:00/15:00/17:00 — с `decision_time=13:00/15:00/17:00`,
но `execution_time=2021-03-12 11:59` (исходное OpenTime тикета 37).

**Корень проблемы:** в `lib_ML_Signal.mqh::MT5_LogLifecycleForCurrentState` (строки
582-628), диагностический логгер `MT5_DiagnosticExecutor` — это **однотикетный
трекер** (`MT5_TrackedTicket`, `MT5_TrackedIdx`, `MT5_TrackedOpenLogged`). Он
ищет один `buy_market = MT5_FindActiveTicket(magic, OP_BUY, OP_BUY)` или
один `sell_market = MT5_FindActiveTicket(magic, OP_SELL, OP_SELL)` и привязывает
его к одному `MT5_TrackedIdx` сигнала. В multi-pos режиме одновременно активны
несколько market-ордеров (например SELL=37 и новый BUY), но трекер находит
«первый» в списке `OrdersTotal()`, оказывается снова на тикете 37 (original
SELL), и логирует новое OPEN с decision_time нового сигнала, но
execution_time старого тикета 37 — что нарушает contract.

Это **blocking gap in multi-position lifecycle coverage**: диагностический слой
executor-а не поддерживал несколько tracked tickets, что блокировало multi-pos
прогон. План явно не предусматривал переработку
`MT5_LogLifecycleForCurrentState` под multi-pos; но и не мог продолжить с одним
трекером в новом режиме. Закрыто в closeout 2026-08-03 (multi-ticket tracker).

## Nested-split disclosure

- **Backcompat (`max=1`)** — single-position canonical проход: smoke confirms
  matching smoke counters (`positions=3, UNEXPLAINED=0`) vs previous baseline; 32 candidate
  metrics untouched (SKIPPED paths). **PASS** (smoke-only; event-level comparison not run).
- **Multi-pos (`max=2`, `max=16`)** — проба не завершена: smoke run валится на
  timing-contract check из-за single-ticket ограничений
  `MT5_LogLifecycleForCurrentState`. Рефакторинг MQL5 сам по себе выполнен и
  компилируется (PASS_WITH_WARNINGS: 0 errors, 2 warnings), но диагностический логгер не поддерживает несколько
  одновременных tracked tickets. **BLOCKED**.

## Forbidden interpretations

- Не делать выводов о том, «может ли мульти-позиция улучшить PF» — бач не завершён.
- Не интерпретировать «refactoring готов к продакшену» — `DIAGNOSTIC_ONLY` verdict.
- Не использовать этот отчёт как основание для смены winner-track в roadmap.

## Ограничения (limitations)

1. **Single-ticket diagnostic executor (CRITICAL)** — `MT5_LogLifecycleForCurrentState`
   отслеживает один `MT5_TrackedTicket` и не умеет разделять несколько одновременных
   позиций. Чтобы выполнить `Step 6/7` плана (batch max=2 и max=16), нужно расширить
   диагностический слой: либо (а) массив `MT5_TrackedTickets[]` с per-idx
   rotation, либо (б) логировать все активные позиции на каждом баре с пометкой
   `MT5_TrackedIdx` для каждой.
2. **Multi-pos path ограничен `iSignal==3`** в `OUTPUT.mqh` — oImp/oGlb/oLoc/POC
   branches в multi-pos режиме не активированы (только для single-pos legacy
   path `MT5_MaxPositions==1`). Это валидно по disclosure: multi-position probe
   запускается с `MT5_DiagnosticExecutor=true` + `iSignal==3` (ML_TRADE).
3. **`ExpTotal==1` assumption** — глобальный массив `Pos[]` и `PosCount`
   корректны только при `ExpTotal==1` (см. `SERVICE.mqh:47`). Если в будущем
   `ExpTotal>1`, `Pos[]` нужно сделать per-expert полем `EXPERT_PARENT_CLASS`.
4. **`set.BUY`/`set.SEL` pending-order queue остаётся single** — как и было
   запланировано: одна bar = один новый ордер в очереди; `MT5_MaxPositions`
   ограничивает только активные рыночные/отложенные позиции, а не очередь
   планирования.
5. **Warnings `ulong → int` для `OrderTicket`** — pre-existing, обусловлены
   несовместимостью типов MQL4 (int) / MQL5 (ulong). Не blockирующие.

## Risk: uncovered blocker

**MT5_DiagnosticExecutor single-ticket tracker не поддерживает multi-position
execution logging.** Прежде, чем запускать Step 6/7 плана, нужно расширить
`MT5_LogLifecycleForCurrentState` (и, возможно, `MT5_OnTradeTransaction`) для
корректной регистрации 每个 ордера в условиях multi-pos. Без этого timing contract
нарушается на этапе parse → metrics → comparison.

## Next step

1. Расширить диагностический слой executor-а на multi-pos support (отдельный план
   `2026-08-02-mt5-diagnostic-multi-pos-tracker.md`, аналогично по disclosure).
2. Повторить `Step 6` (batch max=2 / max=16) после fix-а.
3. Если `max=2`/`max=16` подтверждают, что PF не улучшается по сравнению с
   `max=1` baseline (32 saved candidate metrics): сохранить вердикт fill-rate
   probe («single-position policy is the dominant blocker; multi-position не
   снимает проблему полностью») и продолжить ACTIVE track roadmap-a (entry
   mechanics / trade-count).
4. Если觉察 PF улучшается: изменить `CONTEXT_HANDOFF.md` single-position design
   constraint — при условии, что batch результат проходит публикационный
   cross-check.

## Related materials

- `docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md` — план
- `docs/superpowers/audit.md` — аудит плана (C1, B1-B5, U1-U6, Q1-Q2)
- `docs/reports/2026-08-01-mt5-saved-batch-fill-rate-probe.md` — предыдущий
  этап fill-rate probe, 99.2% OPEN_FAILED
- `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md` — timing contract
  background
- `ML/reports/mt5_execution_loop/diagnostics/fill_rate_diagnostics.json` —
  batch counters `total_open_failed=22767, total_trades=2508, total_active_signal_rows=28808`
- `CONTEXT_HANDOFF.md` — single-position design constraint decision
- `docs/superpowers/roadmap.md` — ACTIVE track
