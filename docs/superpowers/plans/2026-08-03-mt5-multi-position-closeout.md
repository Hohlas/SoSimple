# MT5 Multi-Position Closeout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Исправить замечания аудита `docs/superpowers/audit.md` по MT5 multi-position refactor и закрыть этап доказуемым `DIAGNOSTIC_ONLY` результатом без trading-выводов.

**Architecture:** Исправление делится на четыре слоя: статические guard-тесты для MQL5-контрактов, реальная multi-position установка и side-specific close, multi-ticket диагностический lifecycle logger, затем воспроизводимые MT5 проверки и отчёт. `InpMT5_MaxPositions=1` остаётся каноническим режимом обратной совместимости; `>1` используется только как диагностическая проверка механики исполнения.

**Tech Stack:** MQL5/MQL4Compat, Python `./.venv/bin/python`, `pytest`, MetaEditor через Wine/Xvfb, `ML.baseline.run_mt5_batch`, документация `docs/methodology/13b-mt5-execution-parity.md` и `docs/methodology/16-reporting-audit.md`.

## Global Constraints

- Работать из корня `/home/hohla/git/SoSimple`.
- Python запускать только через `./.venv/bin/python`.
- Не открывать `locked_test`; не выбирать winner; не менять модель, threshold, признаки или frozen export.
- Максимальный verdict этапа: `DIAGNOSTIC_ONLY`.
- `InpMT5_MaxPositions=1` обязан сохранить single-position поведение; `InpMT5_MaxPositions>1` не является торговым режимом.
- MT5 compile gate по методике: лог должен показывать `Result: 0 errors, 0 warnings`, либо отчёт обязан явно зафиксировать `FAIL/PASS_WITH_WARNINGS` и не закрывать parity gate как PASS. Чтобы убрать `possible loss of data` warnings от ticket-кастов, все `OrderSelect((int)ticket, ...)` по `SELECT_BY_TICKET` должны быть заменены на `OrderSelect(ticket, ...)` (MT5 `OrderSelect` принимает `ulong` напрямую); см. Task 4 Step 4b.
- Для tester-прогонов фиксировать фактические paths, model, date range, broker/server, symbol, deposit/currency/leverage, spread mode, account mode, время `.ex5`.
- Не делать `git push`.

## Scope

- Покрытие: только `iSignal == 3` (диагностический ML_TRADE path, `MT5_DiagnosticExecutor=true`). По умолчанию `InpiSignal=3` в `MT/MQL5/Experts/$o$imple.mq5:41`.
- Вне покрытия: `iSignal == 5` (`ML_TRADE_TB` в `lib_ML_Signal_TB.mqh`) — отдельная signal-система с собственным state (`TB_Times[]`, `TB_SignalCount`, `TB_cnt_*`); в рамках этого closeout не тестируется. Будет покрыта отдельным планом `2026-08-03-mt5-per-expert-ml-tracker.md`.
- Архитектурное ограничение multi-pos: `set.BUY`/`set.SEL` в `INPUT.mqh` остаются singleton pending-queue (один planned order per bar, `INPUT.mqh:13-14`). Поэтому multiple same-side позиции могут возникнуть только через серию баров (pending → fill → следующий бар → новый pending), а не через постановку нескольких ордеров в одном баре. Это ограничение явно фиксируется в отчёте (Task 9 Limitations).
- Multi-expert (`ExpTotal>1`) и per-expert ML-CSV (`rule_id` filter) не покрываются — это отдельный план `2026-08-03-mt5-per-expert-ml-tracker.md`.

---

## File Structure

- Modify: `MT/MQL5/Include/FUNCTIONS.mqh`
  - Хранит `POSITION_TRACKER`, helper-функции по `Pos[]`, тип ticket.
- Modify: `MT/MQL5/Include/ORDERS.mqh`
  - Исправляет `SET_BUY()` / `SET_SEL()` так, чтобы `MT5_MaxPositions>1` не блокировался legacy `BUY.Val` / `SEL.Val`.
- Modify: `MT/MQL5/Include/OUTPUT.mqh`
  - Исправляет `CloseBuySide()` / `CloseSellSide()`; side проверяется до изменения `Pos[i].data.Val`.
- Modify: `MT/MQL5/Include/INPUT.mqh`
  - Удаляет мёртвую переменную `BuyPosCnt`.
- Modify: `MT/MQL5/Include/lib_ML_Signal.mqh`
  - Переводит диагностический lifecycle с одного `MT5_TrackedTicket` на массив tracked tickets.
- Modify: `ML/baseline/run_mt5_batch.py`
  - Добавляет режим принудительного пересчёта smoke/batch или отдельный output suffix, чтобы backcompat не доказывался через `SKIP`.
- Create/Modify: `tests/test_mt5_mql5_multiposition_contract.py`
  - Статические contract-тесты на MQL5-код: order path, close-side порядок, lifecycle tracker, disclosure guard.
- Modify: `tests/test_mt5_batch_runtime_contract.py`
  - Проверка проброса `max_positions` и нового режима пересчёта/отдельного output path.
- Create: `docs/reports/2026-08-03-mt5-multi-position-closeout.md`
  - Финальный отчёт закрытия замечаний.
- Modify: `docs/reports/2026-08-02-mt5-multi-position-probe.md`
  - Исправляет неподтверждённые формулировки: "identical", "not a refactoring bug", compile PASS.
- Modify: `docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md`
  - Исправляет неверные команды Task 6 и критерии.
- Modify: `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `docs/superpowers/roadmap.md`
  - Синхронизация только после успешного closeout отчёта.

---

## Task 1: Static Contract Tests For Audit Findings

**Files:**
- Create: `tests/test_mt5_mql5_multiposition_contract.py`
- Modify: `tests/test_mt5_batch_runtime_contract.py`

**Interfaces:**
- Consumes: current MQL5 source text.
- Produces: pytest guards that fail before MQL5 fixes and pass after them.

- [ ] **Step 1: Create failing static tests**

Create `tests/test_mt5_mql5_multiposition_contract.py` with these tests:

```python
from __future__ import annotations

import re

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORDERS = ROOT / "MT" / "MQL5" / "Include" / "ORDERS.mqh"
OUTPUT = ROOT / "MT" / "MQL5" / "Include" / "OUTPUT.mqh"
INPUT = ROOT / "MT" / "MQL5" / "Include" / "INPUT.mqh"
ML_SIGNAL = ROOT / "MT" / "MQL5" / "Include" / "lib_ML_Signal.mqh"
FUNCTIONS = ROOT / "MT" / "MQL5" / "Include" / "FUNCTIONS.mqh"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


# Regex for an MQL5 outer function definition: "void EXPERT::Foo(" or
# "void EXPERT_PARENT_CLASS::Foo(" etc. Used to find the next function boundary
# instead of relying on comment markers like "//Ж" (which are brittle and
# cause ValueError instead of a readable assertion failure if moved/changed).
_FUNC_SIGNATURE = re.compile(
    r"^\s*(?:void|bool|int|float|double|string|datetime|ulong|char|short|uchar|ushort)\s+"
    r"(?:[A-Za-z_][A-Za-z0-9_]*::)?[A-Za-z_][A-Za-z0-9_]*\s*\(",
    re.MULTILINE,
)


def _body(text: str, signature: str, next_signature: str) -> str:
    """Return text between two function signatures, asserting both exist.

    Raises AssertionError with a readable message if either anchor is missing
    (instead of ValueError from str.index), and finds the next anchor by
    function-signature regex to avoid depending on comment layout.
    """
    assert signature in text, f"anchor not found: {signature!r}"
    start = text.index(signature)
    # Search forward for the next function signature after `start`.
    for m in _FUNC_SIGNATURE.finditer(text, start + len(signature)):
        candidate = m.group(0).strip()
        if next_signature in text[m.start():]:
            end = m.start()
            return text[start:end]
    raise AssertionError(
        f"next function anchor matching {next_signature!r} not found after {signature!r}"
    )


def test_set_buy_sell_do_not_use_legacy_singleton_as_multi_pos_loop_gate() -> None:
    orders = _text(ORDERS)
    # Anchors use next function definition, not comment markers.
    buy_body = _body(orders, "void EXPERT_PARENT_CLASS::SET_BUY()", "void EXPERT_PARENT_CLASS::SET_SEL()")
    sell_body = _body(orders, "void EXPERT_PARENT_CLASS::SET_SEL()", "void EXPERT_PARENT_CLASS::MODIFY()")

    assert "CanPlaceBuyOrder()" in buy_body
    assert "CanPlaceSellOrder()" in sell_body
    assert "while (repeat>0 && BUY.Val==0)" not in buy_body
    assert "while (repeat>0 &&  SEL.Val==0)" not in sell_body
    assert "while (repeat>0 && CanPlaceBuyOrder())" in buy_body
    assert "while (repeat>0 && CanPlaceSellOrder())" in sell_body


def test_close_side_checks_ticket_side_before_zero_price_mutation() -> None:
    output = _text(OUTPUT)
    buy_body = _body(output, "void EXPERT::CloseBuySide", "void EXPERT::CloseSellSide")
    sell_body = _body(output, "void EXPERT::CloseSellSide", "void EXPERT::CLOSE_BUY")

    for body, side in ((buy_body, "POSITION_TYPE_BUY"), (sell_body, "POSITION_TYPE_SELL")):
        side_check = body.index(f"pt != {side}")
        zero_mutation = body.index("if (price == 0)")
        assert side_check < zero_mutation


def test_input_has_no_unused_buyposcnt_estimate() -> None:
    assert "BuyPosCnt" not in _text(INPUT)


def test_diagnostic_lifecycle_uses_multi_ticket_tracker() -> None:
    ml_signal = _text(ML_SIGNAL)
    assert "MT5_TRACKED_POSITION" in ml_signal
    assert "MT5_TrackedPositions[]" in ml_signal
    assert "MT5_TrackedTicket" not in ml_signal
    assert "MT5_FindTrackedIndexByTicket" in ml_signal
    assert "MT5_LogLifecycleForTicket" in ml_signal
    # NEW (A5 cleanup): closed tracked positions must be compacted out of the active array.
    assert "MT5_TrackedPositionCount--" in ml_signal or "close_logged" in ml_signal


def test_position_tracker_ticket_uses_ulong() -> None:
    functions = _text(FUNCTIONS)
    assert "struct POSITION_TRACKER { ulong ticket;" in functions
    assert "int FindPosIndexByTicket(ulong ticket)" in functions
    assert "void RemovePositionByTicket(ulong ticket)" in functions
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_mql5_multiposition_contract.py -q
```

Expected now: FAIL for legacy loop gate, close-side order, unused `BuyPosCnt`, single-ticket tracker, and `int ticket`.

- [ ] **Step 3: Add runtime contract test for no-SKIP backcompat verification**

Append to `tests/test_mt5_batch_runtime_contract.py`:

```python
def test_main_accepts_force_rerun_flag() -> None:
    from ML.baseline import run_mt5_batch

    parser = run_mt5_batch.build_arg_parser()
    args = parser.parse_args(["--phase", "tester", "--max-positions", "1", "--force-rerun"])

    assert args.phase == "tester"
    assert args.max_positions == 1
    assert args.force_rerun is True


def test_run_batch_force_rerun_overrides_skip_when_unexplained_zero(
    monkeypatch, tmp_path
) -> None:
    """Behavioral contract: when force_rerun=True and metrics.json already exists
    with UNEXPLAINED=0, run_batch must NOT skip and must invoke run_tester.

    Audit item 4: backcompat was wrongly proved by 32/32 SKIP. force_rerun must
    make the skip-path inert.
    """
    from ML.baseline import run_mt5_batch
    import json

    run_id = "candidate_skip"
    batch_dir = tmp_path / "batch"
    tester_files = tmp_path / "tester_files"
    out_dir = batch_dir / run_id
    out_dir.mkdir(parents=True)
    tester_files.mkdir()

    # Pre-existing metrics claiming success -> normally causes SKIP.
    metrics_with_zero = {"reconciliation": {"class_counts": {"UNEXPLAINED": 0}}}
    (out_dir / "metrics.json").write_text(json.dumps(metrics_with_zero), encoding="utf-8")
    # events.csv must exist for the skip guard; content doesn't matter for force_rerun.
    (out_dir / "events.csv").write_text("event\nINIT\n", encoding="utf-8")
    (out_dir / "entry_signals.csv").write_text("time\n2023.01.02 09:00\n", encoding="utf-8")

    calls = {"run_tester": 0}

    def fake_run_tester(ini_path):
        calls["run_tester"] += 1
        # Simulate tester producing an events file.
        events_src = tester_files / f"mt5_trade_events_{run_id}.csv"
        events_src.write_text("event\nINIT\n", encoding="utf-8")
        return True

    monkeypatch.setattr(run_mt5_batch, "BATCH_DIR", batch_dir)
    monkeypatch.setattr(run_mt5_batch, "TESTER_FILES", tester_files)
    monkeypatch.setattr(run_mt5_batch, "TERMINAL_FILES", tmp_path / "terminal")
    monkeypatch.setattr(run_mt5_batch, "make_run_id", lambda candidate: run_id)
    monkeypatch.setattr(run_mt5_batch, "create_set_file", lambda run_id, *, max_positions=1: tmp_path / "settings.set")
    monkeypatch.setattr(run_mt5_batch, "create_ini_file", lambda run_id, set_name: tmp_path / "tester.ini")
    monkeypatch.setattr(run_mt5_batch, "wait_for_liveupdate_clear", lambda: True)
    monkeypatch.setattr(run_mt5_batch, "copy_entry_signal_file", lambda src: None)
    monkeypatch.setattr(run_mt5_batch, "run_tester", fake_run_tester)
    # parse_events returns a minimal metrics dict so run_batch records n_done.
    monkeypatch.setattr(run_mt5_batch, "parse_events", lambda run_id, events_dst: {"reconciliation": {"class_counts": {"UNEXPLAINED": 0, "CLOSED_TX": 1}}})

    run_mt5_batch.run_batch([{"profile": "candidate"}], force_rerun=True)

    assert calls["run_tester"] == 1, "force_rerun=True must override SKIP and invoke run_tester"


def test_run_batch_skips_when_unexplained_zero_and_no_force_rerun(
    monkeypatch, tmp_path
) -> None:
    """Inverse: without force_rerun, existing metrics.json with UNEXPLAINED=0
    must still SKIP (backcompat regression guard)."""
    from ML.baseline import run_mt5_batch
    import json

    run_id = "candidate_skip_normally"
    batch_dir = tmp_path / "batch"
    out_dir = batch_dir / run_id
    out_dir.mkdir(parents=True)

    (out_dir / "metrics.json").write_text(
        json.dumps({"reconciliation": {"class_counts": {"UNEXPLAINED": 0}}}),
        encoding="utf-8",
    )
    (out_dir / "events.csv").write_text("event\nINIT\n", encoding="utf-8")

    calls = {"run_tester": 0}
    monkeypatch.setattr(run_mt5_batch, "BATCH_DIR", batch_dir)
    monkeypatch.setattr(run_mt5_batch, "make_run_id", lambda candidate: run_id)
    monkeypatch.setattr(run_mt5_batch, "run_tester", lambda ini_path: calls.__setitem__("run_tester", calls["run_tester"] + 1) or True)

    run_mt5_batch.run_batch([{"profile": "candidate"}], force_rerun=False)

    assert calls["run_tester"] == 0, "force_rerun=False with UNEXPLAINED=0 must SKIP"
```

- [ ] **Step 4: Run focused tests and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_mql5_multiposition_contract.py tests/test_mt5_batch_runtime_contract.py::test_main_accepts_force_rerun_flag -q
```

Expected: FAIL because `build_arg_parser()` / `--force-rerun` do not exist yet.

- [ ] **Step 5: Commit failing tests**

```bash
git add tests/test_mt5_mql5_multiposition_contract.py tests/test_mt5_batch_runtime_contract.py
git commit -m "test: cover mt5 multi-position audit findings"
```

---

## Task 2: Fix POSITION ticket type and order placement gate

**Files:**
- Modify: `MT/MQL5/Include/FUNCTIONS.mqh`
- Modify: `MT/MQL5/Include/ORDERS.mqh`

**Interfaces:**
- Produces: `CountActiveBySide(int position_type, bool include_pending) -> int`, `CanPlaceBuyOrder() -> bool`, `CanPlaceSellOrder() -> bool`.
- Consumes: `MT5_MaxPositions`, `PositionSelectByTicket`, `POSITION_TYPE_BUY`, `POSITION_TYPE_SELL`.

- [ ] **Step 1: Change ticket type to `ulong`**

In `MT/MQL5/Include/FUNCTIONS.mqh`, replace:

```cpp
struct POSITION_TRACKER { int ticket; PRICE data; bool active; };
```

with:

```cpp
struct POSITION_TRACKER { ulong ticket; PRICE data; bool active; };
```

Change helper signatures:

```cpp
void RemovePositionByTicket(ulong ticket)
int FindPosIndexByTicket(ulong ticket)
```

- [ ] **Step 2: Add side-count helper**

Inside `EXPERT_PARENT_CLASS`, after `CountActiveByType(char typ)`, add:

```cpp
int CountActiveBySide(int position_type, bool include_pending) {
   int n = 0;
   for (int i=0; i<PosCount; i++) {
      if (!Pos[i].active || Pos[i].data.Typ == NONE) continue;
      if (!include_pending && Pos[i].data.Typ != MARKET) continue;
      if (!PositionSelectByTicket(Pos[i].ticket)) continue;
      ENUM_POSITION_TYPE pt = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      if ((int)pt == position_type) n++;
   }
   return n;
}
```

- [ ] **Step 3: Add order placement helpers**

Inside `EXPERT_PARENT_CLASS`, after `CountActiveBySide(...)`, add:

```cpp
bool CanPlaceBuyOrder() {
   if (MT5_MaxPositions == 1) return (BUY.Val == 0);
   return (CountActiveBySide((int)POSITION_TYPE_BUY, true) < MT5_MaxPositions);
}

bool CanPlaceSellOrder() {
   if (MT5_MaxPositions == 1) return (SEL.Val == 0);
   return (CountActiveBySide((int)POSITION_TYPE_SELL, true) < MT5_MaxPositions);
}
```

- [ ] **Step 4: Replace SET_BUY/SET_SEL loop gates**

In `MT/MQL5/Include/ORDERS.mqh`, replace:

```cpp
while (repeat>0 && BUY.Val==0){
```

with:

```cpp
while (repeat>0 && CanPlaceBuyOrder()){
```

Replace:

```cpp
while (repeat>0 &&  SEL.Val==0){
```

with:

```cpp
while (repeat>0 && CanPlaceSellOrder()){
```

- [ ] **Step 5: Remove unsafe casts at FindPosIndexByTicket call sites**

In `MT/MQL5/Include/ORDERS.mqh`, keep:

```cpp
int posIdx = FindPosIndexByTicket(OrderTicket());
```

After Step 1 changed `FindPosIndexByTicket` to accept `ulong ticket`, the previous `ulong -> int` warning at this call site disappears (no lossy cast into the helper). Warning status at other call sites (`OrderSelect((int)ticket, ...)` in `lib_ML_Signal.mqh`, `OrderSelect(ticket, ...)` in `OUTPUT.mqh`) is handled in Task 4 Step 4b and is a compile-gate precondition for Task 6 Step 3.

Also verify `MT/MQL5/Include/ERRORs.mqh` call sites of `EXP[ExpNum].Pos[i].ticket` compile-cleanly: `PositionSelectByTicket(EXP[ExpNum].Pos[i].ticket)` at `ERRORs.mqh:105` must use the new `ulong ticket` directly without `(int)` cast. If any explicit `(int)` cast remains in `ERRORs.mqh`, remove it (MT5 `PositionSelectByTicket` accepts `ulong`).

- [ ] **Step 5b: Verify compile-after-Task-2 has only legacy warnings from lib_ML_Signal**

Run a quick sanity grep (not a test gate yet): no explicit `(int)OrderTicket()` cast should remain inside `ORDERS.mqh`.

```bash
rg -n "\(int\)OrderTicket\(\)" MT/MQL5/Include/ORDERS.mqh MT/MQL5/Include/ERRORs.mqh
```

Expected: no output. If output appears, fix the cast before commit. This is preparation for Task 6 Step 3 (`0 warnings`).

- [ ] **Step 6: Run static tests for this task**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_mql5_multiposition_contract.py::test_set_buy_sell_do_not_use_legacy_singleton_as_multi_pos_loop_gate tests/test_mt5_mql5_multiposition_contract.py::test_position_tracker_ticket_uses_ulong -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add MT/MQL5/Include/FUNCTIONS.mqh MT/MQL5/Include/ORDERS.mqh tests/test_mt5_mql5_multiposition_contract.py
git commit -m "fix: allow mt5 same-side multi-position order placement"
```

---

## Task 3: Fix side-specific close helpers and clean INPUT

**Files:**
- Modify: `MT/MQL5/Include/OUTPUT.mqh`
- Modify: `MT/MQL5/Include/INPUT.mqh`

**Interfaces:**
- Consumes: `Pos[]`, `PositionSelectByTicket`, `POSITION_TYPE_BUY`, `POSITION_TYPE_SELL`.
- Produces: side-safe `CloseBuySide()` / `CloseSellSide()`.

- [ ] **Step 1: Move `price == 0` after side check in `CloseBuySide`**

In `CloseBuySide`, make the top of the loop exactly:

```cpp
for (int i = 0; i < PosCount; i++) {
   if (!Pos[i].active || Pos[i].data.Typ == NONE) continue;
   if (!PositionSelectByTicket(Pos[i].ticket)) continue;
   ENUM_POSITION_TYPE pt = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   if (pt != POSITION_TYPE_BUY) continue;
   if (price == 0) { Pos[i].data.Val = 0; continue; }
   if (Pos[i].data.Typ != MARKET) {
```

- [ ] **Step 2: Move `price == 0` after side check in `CloseSellSide`**

In `CloseSellSide`, make the top of the loop exactly:

```cpp
for (int i = 0; i < PosCount; i++) {
   if (!Pos[i].active || Pos[i].data.Typ == NONE) continue;
   if (!PositionSelectByTicket(Pos[i].ticket)) continue;
   ENUM_POSITION_TYPE pt = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   if (pt != POSITION_TYPE_SELL) continue;
   if (price == 0) { Pos[i].data.Val = 0; continue; }
   if (Pos[i].data.Typ != MARKET) {
```

- [ ] **Step 3: Remove dead `BuyPosCnt` from INPUT**

Delete these lines from `MT/MQL5/Include/INPUT.mqh`:

```cpp
int BuyPosCnt = CountActiveByType(MARKET);  // здесь грубая оценка: includes both sides for MARKET,
                                            // уточняется ниже через PositionSelectByTicket.
// Уточним сторону для каждой активной позиции:
```

Leave a single comment:

```cpp
// Считаем активные позиции по стороне.
```

- [ ] **Step 4: Run static tests for this task**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_mql5_multiposition_contract.py::test_close_side_checks_ticket_side_before_zero_price_mutation tests/test_mt5_mql5_multiposition_contract.py::test_input_has_no_unused_buyposcnt_estimate -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add MT/MQL5/Include/OUTPUT.mqh MT/MQL5/Include/INPUT.mqh tests/test_mt5_mql5_multiposition_contract.py
git commit -m "fix: make mt5 multi-position close helpers side-safe"
```

---

## Task 4: Replace single-ticket diagnostic lifecycle with multi-ticket tracker

**Files:**
- Modify: `MT/MQL5/Include/lib_ML_Signal.mqh`
- Modify: `tests/test_mt5_mql5_multiposition_contract.py`

**Interfaces:**
- Produces: `MT5_TRACKED_POSITION`, `MT5_TrackedPositions[]`, `MT5_FindTrackedIndexByTicket(ulong ticket)`, `MT5_LogLifecycleForTicket(int tracked_i, int magic, int &ml_close_order_type)`.
- Consumes: `MT5_RegisterPosition`, `MT5_ML_LogEvent`, `MT5_CalculateOpenPositionFeatures`.

- [ ] **Step 1: Replace singleton tracking state**

In `MT/MQL5/Include/lib_ML_Signal.mqh`, replace:

```cpp
ulong    MT5_TrackedTicket = 0;
int      MT5_TrackedMagic = 0;
int      MT5_TrackedIdx = -1;
bool     MT5_TrackedOpenLogged = false;
```

with:

```cpp
struct MT5_TRACKED_POSITION {
   ulong ticket;
   int magic;
   int idx;
   bool open_logged;
   bool close_logged;
};

MT5_TRACKED_POSITION MT5_TrackedPositions[];
int MT5_TrackedPositionCount = 0;
```

- [ ] **Step 2: Add tracker helpers**

After `MT5_RegisterPosition(...)`, add:

```cpp
int MT5_FindTrackedIndexByTicket(ulong ticket) {
   for (int i = 0; i < MT5_TrackedPositionCount; i++) {
      if (MT5_TrackedPositions[i].ticket == ticket) return i;
   }
   return -1;
}

void MT5_AddTrackedPosition(ulong ticket, int magic, int idx) {
   if (ticket == 0 || idx < 0) return;
   int existing = MT5_FindTrackedIndexByTicket(ticket);
   if (existing >= 0) {
      // A4 guard: refuse to rebind an already-tracked ticket to a different
      // signal index. A rebinding would mean a stale MT5_LastPlacedIdx got
      // reused after the signal was already linked to a different fill; that
      // corrupts timing/logging. Update magic only if it agrees.
      if (MT5_TrackedPositions[existing].idx != idx) {
         Print("WARN: MT5_AddTrackedPosition ticket=", ticket,
               " already tracked with idx=", MT5_TrackedPositions[existing].idx,
               " refusing rebinding to new idx=", idx);
         return;
      }
      MT5_TrackedPositions[existing].magic = magic;
      return;
   }
   // A5 guard: do not resurrect an already-closed tracked entry. If a slot was
   // compacted (close_logged + removed), FindTrackedIndexByTicket returns -1
   // and we create a fresh entry below — that is the intended path.
   ArrayResize(MT5_TrackedPositions, MT5_TrackedPositionCount + 1);
   MT5_TrackedPositions[MT5_TrackedPositionCount].ticket = ticket;
   MT5_TrackedPositions[MT5_TrackedPositionCount].magic = magic;
   MT5_TrackedPositions[MT5_TrackedPositionCount].idx = idx;
   MT5_TrackedPositions[MT5_TrackedPositionCount].open_logged = false;
   MT5_TrackedPositions[MT5_TrackedPositionCount].close_logged = false;
   MT5_TrackedPositionCount++;
   MT5_RegisterPosition(ticket, idx);
}
```

- [ ] **Step 3: Add side-aware fill discovery for the last placed signal**

Add:

```cpp
ulong MT5_FindFilledTicketForSignal(int magic, int idx) {
   if (idx < 0 || idx >= MT5_EntrySignalCount) return 0;
   bool want_buy = (MT5_Sides[idx] == "BUY" || MT5_Sides[idx] == "LONG" || MT5_Sides[idx] == "1");
   for (int i = 0; i < OrdersTotal(); i++) {
      if (OrderSelect(i, SELECT_BY_POS, MODE_TRADES) != true) continue;
      if (OrderMagicNumber() != magic) continue;
      int typ = OrderType();
      if (want_buy && typ != OP_BUY) continue;
      if (!want_buy && typ != OP_SELL) continue;
      ulong ticket = (ulong)OrderTicket();
      if (MT5_FindTrackedIndexByTicket(ticket) >= 0) continue;
      if (OrderOpenTime() < MT5_DecisionTimes[idx]) continue;
      return ticket;
   }
   return 0;
}
```

- [ ] **Step 4: Split one-ticket logging into `MT5_LogLifecycleForTicket`**

Create a new function by moving the body from the old `if (MT5_TrackedTicket > 0 && OrderSelect(...))` branches into:

```cpp
void MT5_LogLifecycleForTicket(int tracked_i, int magic, int &ml_close_order_type) {
   ulong ticket = MT5_TrackedPositions[tracked_i].ticket;
   int idx = MT5_TrackedPositions[tracked_i].idx;
   if (idx < 0 || idx >= MT5_EntrySignalCount) return;

   // A2: pass ticket directly (MT5 OrderSelect with SELECT_BY_TICKET accepts ulong);
   // using (int)ticket keeps `possible loss of data` warning and violates the
   // `0 warnings` compile gate required by Global Constraints.
   if (OrderSelect(ticket, SELECT_BY_TICKET, MODE_TRADES) == true) {
      int typ = OrderType();
      if (typ != OP_BUY && typ != OP_SELL) return;
      int bars_since_fill = (int)MathMax(0, SHIFT(OrderOpenTime()) - bar);
      if (!MT5_TrackedPositions[tracked_i].open_logged) {
         MT5_ML_LogEvent("OPEN", TimeCurrent(), MT5_FeatureTimes[idx], MT5_FeatureAvailableTimes[idx], MT5_DecisionTimes[idx], OrderOpenTime(), MT5_RuleIds[idx], MT5_TimeText(MT5_EntryTimes[idx]), ticket, MT5_Sides[idx], MT5_LimitPrices[idx], OrderOpenPrice(), OrderOpenPrice(), 0.0, OrderStopLoss(), "", 0.0, bars_since_fill, MT5_Atrs[idx], OrderOpenTime(), 0, 0.0, 0.0, 0.0, 0.0, 0, "tester fill observed", 0, "", 0, "", idx, magic, Symbol(), MT5_EntryTypes[idx]);
         MT5_TrackedPositions[tracked_i].open_logged = true;
      }
      double unrealized_r = 0.0;
      double favorable_r = 0.0;
      double adverse_r = 0.0;
      bool features_ready = MT5_CalculateOpenPositionFeatures(typ, OrderOpenPrice(), OrderStopLoss(), bars_since_fill, unrealized_r, favorable_r, adverse_r);
      int ml_exit_decision = 0;
      double ml_exit_score = 0.0;
      if (MT5_BlockBarsSinceFill0Exit && bars_since_fill <= 0) {
         ml_exit_decision = 0;
      } else if (features_ready) {
         ml_exit_score = DiagnosticMlExitScore(bars_since_fill, unrealized_r, favorable_r, adverse_r);
         ml_exit_decision = (ml_exit_score >= 1.0 ? 1 : 0);
      }
      string eval_comment = (features_ready ? "diagnostic eval only" : "diagnostic eval skipped: post-fill features not ready");
      MT5_ML_LogEvent("ML_EVAL", TimeCurrent(), MT5_FeatureTimes[idx], MT5_FeatureAvailableTimes[idx], MT5_DecisionTimes[idx], TimeCurrent(), MT5_RuleIds[idx], MT5_TimeText(MT5_EntryTimes[idx]), ticket, MT5_Sides[idx], MT5_LimitPrices[idx], OrderOpenPrice(), OrderOpenPrice(), 0.0, OrderStopLoss(), "", OrderProfit(), bars_since_fill, MT5_Atrs[idx], OrderOpenTime(), 0, unrealized_r, favorable_r, adverse_r, ml_exit_score, ml_exit_decision, eval_comment, 0, "", 0, "", idx, magic, Symbol(), MT5_EntryTypes[idx]);
      if (ml_exit_decision == 1 && ml_close_order_type < 0) {
         double close_price = (typ == OP_BUY ? Bid : Ask);
         MT5_ML_LogEvent("ML_CLOSE", TimeCurrent(), MT5_FeatureTimes[idx], MT5_FeatureAvailableTimes[idx], MT5_DecisionTimes[idx], TimeCurrent(), MT5_RuleIds[idx], MT5_TimeText(MT5_EntryTimes[idx]), ticket, MT5_Sides[idx], MT5_LimitPrices[idx], OrderOpenPrice(), OrderOpenPrice(), close_price, OrderStopLoss(), "ML_CLOSE", OrderProfit(), bars_since_fill, MT5_Atrs[idx], OrderOpenTime(), TimeCurrent(), unrealized_r, favorable_r, adverse_r, ml_exit_score, ml_exit_decision, "diagnostic ml exit requested", 0, "", 0, "", idx, magic, Symbol(), MT5_EntryTypes[idx]);
         ml_close_order_type = typ;
      }
      return;
   }

   // A2: same as the MODE_TRADES branch — pass ticket directly without (int) cast.
   if (!MT5_TrackedPositions[tracked_i].close_logged && OrderSelect(ticket, SELECT_BY_TICKET, MODE_HISTORY) == true) {
      int bars_since_fill = (int)MathMax(0, SHIFT(OrderOpenTime()) - SHIFT(OrderCloseTime()));
      MT5_ML_LogEvent("CLOSE", TimeCurrent(), MT5_FeatureTimes[idx], MT5_FeatureAvailableTimes[idx], MT5_DecisionTimes[idx], OrderCloseTime(), MT5_RuleIds[idx], MT5_TimeText(MT5_EntryTimes[idx]), ticket, MT5_Sides[idx], MT5_LimitPrices[idx], OrderOpenPrice(), OrderOpenPrice(), OrderOpenPrice(), OrderStopLoss(), "broker_history_limited", OrderProfit(), bars_since_fill, MT5_Atrs[idx], OrderOpenTime(), OrderCloseTime(), 0.0, 0.0, 0.0, 0.0, 0, "history price/reason is limited in Task 4", 0, "", 0, "", idx, magic, Symbol(), MT5_EntryTypes[idx]);
      MT5_TrackedPositions[tracked_i].close_logged = true;
      // A5 cleanup: compact this closed tracked entry out of the active array so
      // the lifecycle loop in Step 5 does not iterate dead tickets on every tick.
      // Swap-remove: move the last entry into this slot and shrink the count.
      int last = MT5_TrackedPositionCount - 1;
      if (tracked_i != last) {
         MT5_TrackedPositions[tracked_i] = MT5_TrackedPositions[last];
      }
      MT5_TrackedPositionCount--;
      ArrayResize(MT5_TrackedPositions, MT5_TrackedPositionCount);
   }
}
```

- [ ] **Step 4b: Audit all remaining `(int)ticket` / `(int)OrderTicket()` casts in lib_ML_Signal.mqh**

The `0 warnings` compile gate (Global Constraints + Task 6 Step 3) is unreachable if any `(int)ticket` or `(int)OrderTicket()` cast remains. Search the whole `lib_ML_Signal.mqh`:

```bash
rg -n "\(int\)OrderTicket\(\)|\(int\)MT5_TrackedTicket|\(int\)ticket" MT/MQL5/Include/lib_ML_Signal.mqh
```

For each match, replace the cast with a direct `ulong` pass-through (MT5 `OrderSelect` and `MT5_RegisterPosition` accept `ulong`). `MT5_OnTradeTransaction` (around line 460+) and `MT5_ML_LogEvent` callers must pass `trans.order` / deal ticket as `ulong`. If a helper explicitly requires `int` (none currently do after Task 2 Step 1), document it as an unavoidable exception and downgrade compile status to `PASS_WITH_WARNINGS` in the report.

Expected after this step: empty grep output; no `possible loss of data` warnings related to ticket types remain in `lib_ML_Signal.mqh`.

- [ ] **Step 5: Rewrite `MT5_LogLifecycleForCurrentState`**

Replace the old singleton implementation with:

```cpp
void MT5_LogLifecycleForCurrentState(int magic, int &ml_close_order_type) {
   ml_close_order_type = -1;

   if (MT5_LastPlacedIdx >= 0 && MT5_LastPlacedMagic == magic) {
      ulong filled_ticket = MT5_FindFilledTicketForSignal(magic, MT5_LastPlacedIdx);
      ulong buy_pending = MT5_FindActiveTicket(magic, OP_BUYLIMIT, OP_BUYSTOP);
      ulong sell_pending = MT5_FindActiveTicket(magic, OP_SELLLIMIT, OP_SELLSTOP);
      if (filled_ticket > 0) {
         MT5_AddTrackedPosition(filled_ticket, magic, MT5_LastPlacedIdx);
         MT5_LastPlacedIdx = -1;
      } else if (buy_pending == 0 && sell_pending == 0 && MT5_LastPlacedExpiry > 0 && TimeCurrent() > MT5_LastPlacedExpiry) {
         MT5_LogSignalEvent("ORDER_EXPIRED", MT5_LastPlacedIdx, 0, "pending order not active after max_fill_lag_bars");
         MT5_LastPlacedIdx = -1;
      } else if (buy_pending == 0 && sell_pending == 0) {
         MT5_LogSignalEvent("OPEN_FAILED", MT5_LastPlacedIdx, 0, "pending order was not found after ORDER_PLACED");
         MT5_LastPlacedIdx = -1;
      }
   }

   for (int i = 0; i < MT5_TrackedPositionCount; i++) {
      if (MT5_TrackedPositions[i].magic != magic) continue;
      int before = MT5_TrackedPositionCount;
      MT5_LogLifecycleForTicket(i, magic, ml_close_order_type);
      // A5: if MT5_LogLifecycleForTicket compacted slot i (swap-remove of last
      // element into slot i after a CLOSE), re-inspect the same index i so we
      // do not skip the moved entry. Only decrement when we did a real removal.
      if (MT5_TrackedPositionCount < before) i--;
   }
}
```

- [ ] **Step 6: Update ML_TRADE assignment**

In `EXPERT::ML_TRADE()`, delete:

```cpp
MT5_TrackedMagic = Mgc;
```

because tracked magic is now per tracked position.

- [ ] **Step 7: Run static lifecycle test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_mql5_multiposition_contract.py::test_diagnostic_lifecycle_uses_multi_ticket_tracker -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add MT/MQL5/Include/lib_ML_Signal.mqh tests/test_mt5_mql5_multiposition_contract.py
git commit -m "fix: track mt5 diagnostic lifecycle per ticket"
```

---

## Task 5: Add forced rerun support for reproducible backcompat checks

**Files:**
- Modify: `ML/baseline/run_mt5_batch.py`
- Modify: `tests/test_mt5_batch_runtime_contract.py`

**Interfaces:**
- Produces: `build_arg_parser() -> argparse.ArgumentParser`, `run_batch(..., force_rerun: bool = False)`, `run_smoke_test(..., force_rerun: bool = False)`.

- [ ] **Step 1: Extract parser builder**

In `ML/baseline/run_mt5_batch.py`, add before `main()`:

```python
def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MT5 batch selection pipeline")
    parser.add_argument("--phase", choices=["signals", "tester", "aggregate", "all"], default="all")
    parser.add_argument(
        "--max-positions",
        type=int,
        default=1,
        help="MT5 multi-position cap passed to the expert's InpMT5_MaxPositions input "
        "(1 = single-position canonical, >1 = multi-pos diagnostic probe).",
    )
    parser.add_argument(
        "--force-rerun",
        action="store_true",
        help="Ignore existing metrics/events for tester runs and regenerate artifacts.",
    )
    return parser
```

- [ ] **Step 2: Use parser builder in `main()`**

Replace parser construction in `main()` with:

```python
parser = build_arg_parser()
args = parser.parse_args()
```

- [ ] **Step 3: Add `force_rerun` to smoke and batch calls**

Change signatures:

```python
def run_smoke_test(candidates: list[dict], *, max_positions: int = 1, force_rerun: bool = False) -> bool:
def run_batch(candidates: list[dict], *, max_positions: int = 1, force_rerun: bool = False) -> None:
```

**Semantics (A6):**
- `force_rerun` has **runtime effect only in `run_batch`** — it overrides the existing-skip guard. In `run_smoke_test`, the parameter is accepted for API consistency but is a no-op (smoke always recalculates; there is no skip logic in `run_smoke_test` today). Do not claim `--force-rerun` enables event-level backcompat for smoke: it only guarantees smoke won't reuse an existing batch artifact by accident, and forces batch candidates to actually run the tester.
- `force_rerun` MUST NOT delete source `entry_signals.csv`.

In `main()`, call:

```python
if not run_smoke_test(candidates, max_positions=args.max_positions, force_rerun=args.force_rerun):
...
run_batch(candidates, max_positions=args.max_positions, force_rerun=args.force_rerun)
```

- [ ] **Step 4: Implement skip override (full patch for `run_batch`)**

In `run_batch`, replace the existing skip guard:

```python
if metrics_json.exists() and events_csv.exists():
    meta = json.loads(metrics_json.read_text(encoding="utf-8"))
    recon = meta.get("reconciliation", {})
    unexpl = recon.get("class_counts", {}).get("UNEXPLAINED", -1)
    if unexpl == 0:
        n_skipped += 1
        print(f"[{i}/{n_total}] SKIP {run_id} (metrics exist, UNEXPLAINED=0)")
        continue
```

with:

```python
if force_rerun:
    # Audit item 4: backcompat was wrongly proved via 32/32 SKIP. Delete ONLY
    # per-run generated artifacts (events.csv, metrics.json); never touch the
    # source entry_signals.csv so the tester still reads the same inputs.
    for stale_path in (events_csv, metrics_json):
        if stale_path.exists():
            stale_path.unlink()
    # Fall through to the normal run path below.
else:
    if metrics_json.exists() and events_csv.exists():
        meta = json.loads(metrics_json.read_text(encoding="utf-8"))
        recon = meta.get("reconciliation", {})
        unexpl = recon.get("class_counts", {}).get("UNEXPLAINED", -1)
        if unexpl == 0:
            n_skipped += 1
            print(f"[{i}/{n_total}] SKIP {run_id} (metrics exist, UNEXPLAINED=0)")
            continue
```

Notes:
- The `force_rerun` block drops straight through to the existing tester-run path — there is no separate branch. The `entry_signals.csv` check (`if not entry_csv.exists()`) below stays unchanged and still aborts a candidate that lacks source inputs.
- `n_skipped` semantics: when `force_rerun=True`, every executed candidate increments `n_done` (or `n_failed`); none stays in SKIP. The new behavioral tests in Task 1 Step 3 assert both directions.

- [ ] **Step 5: Run parser test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_batch_runtime_contract.py::test_main_accepts_force_rerun_flag -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/run_mt5_batch.py tests/test_mt5_batch_runtime_contract.py
git commit -m "feat: force mt5 batch rerun for parity checks"
```

---

## Task 6: Compile gate and focused tester checks

**Files:**
- Read/verify: `MT/MQL5/Experts/$o$imple.mq5`
- Output artifacts: `/tmp/sosimple_mt5_compile_closeout.log`, `ML/reports/mt5_execution_loop/batch/_smoke/events.csv`, `ML/reports/mt5_execution_loop/batch/_smoke/metrics.json`

**Interfaces:**
- Consumes: fixed MQL5 source.
- Produces: evidence for `13b-mt5-execution-parity.md`.

- [ ] **Step 1: Run Python test suite for touched Python/static contracts**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_mql5_multiposition_contract.py tests/test_mt5_batch_runtime_contract.py tests/test_parse_mt5_execution_report.py tests/test_mt5_signal_executor_schema.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Check source formatting**

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 3: Compile MT5 expert**

**Two compile logs will exist; pin one as canonical for the report (A8).**

1. **Canonical closeout log** (manual, this step): the report MUST cite this one.
2. **Batch compile log** `/tmp/sosimple_mt5_batch_compile.log` (produced automatically by `run_mt5_batch.py:167` via `compile_expert()` when Step 4 invokes the batch): used only to confirm the batch ran the latest source, not a success criterion on its own.

Run the manual compile:

```bash
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' \
  /compile:'/home/hohla/git/SoSimple/MT/MQL5/Experts/$o$imple.mq5' \
  /log:'/tmp/sosimple_mt5_compile_closeout.log'
```

Then run:

```bash
iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile_closeout.log | tail -n 30
ls -l /tmp/sosimple_mt5_compile_closeout.log MT/MQL5/Experts/'$o$imple.ex5'
```

Expected: `Result: 0 errors, 0 warnings` and `.ex5` mtime later than compile start. If warnings remain, **do NOT stop silently** — re-run Task 2 Step 5b and Task 4 Step 4b greps to find any remaining `(int)ticket`/`(int)OrderTicket()` cast, fix them, and re-compile. Compile gate is satisfied only when the closeout log shows `0 warnings`. If a warning is genuinely unavoidable (e.g. a third-party `.mqh`), record `FAIL` for compile gate in the report and downgrade the stage accordingly.

- [ ] **Step 4: Run single-position smoke with forced rerun**

Run:

```bash
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=1 --force-rerun
```

Expected:
- smoke completes;
- no `ABORT: smoke test failed`;
- metrics contain `reconciliation.class_counts.UNEXPLAINED=0`;
- report must not claim full batch identity unless event-level comparison is run.

- [ ] **Step 5: Run multi-position smoke with max=2**

Run:

```bash
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=2 --force-rerun
```

Expected:
- no timing-contract `ValueError`;
- smoke metrics parse successfully;
- event log has no row where `decision_time > execution_time` for signal-linked rows.

If this fails, stop. Do not run max=16 or aggregate.

- [ ] **Step 6: Run max=16 only after max=2 passes**

Run:

```bash
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=16 --force-rerun
```

Expected:
- no timing-contract `ValueError`;
- smoke metrics parse successfully.

- [ ] **Step 7: Commit compile/test-support state if source changed after previous commit**

If Tasks 6.1-6.6 required source fixes, commit them:

```bash
git add MT/MQL5/Include ML/baseline tests
git commit -m "fix: pass mt5 multi-position closeout checks"
```

---

## Task 7: Backcompat and multi-position evidence comparison

**Files:**
- Read: `ML/reports/mt5_execution_loop/batch/_smoke/events.csv`
- Read: `ML/reports/mt5_execution_loop/batch/_smoke/metrics.json`
- Optional create: `ML/reports/mt5_execution_loop/diagnostics/mt5_multi_position_closeout_summary.json`

**Interfaces:**
- Produces: structured evidence for final report.

- [ ] **Step 1: Add a small comparison utility only if manual comparison is not enough**

If repeated manual checks become error-prone, add `ML/baseline/compare_mt5_closeout_runs.py` with:

```python
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def summarize_run(events_csv: Path, metrics_json: Path) -> dict:
    events = pd.read_csv(events_csv, sep=";")
    metrics = json.loads(metrics_json.read_text(encoding="utf-8"))
    return {
        "event_counts": events["event"].value_counts().to_dict(),
        "position_count": metrics["reconciliation"]["position_count"],
        "class_counts": metrics["reconciliation"]["class_counts"],
        "timing_violations": int(
            (
                pd.to_datetime(events["decision_time"], errors="coerce")
                > pd.to_datetime(events["execution_time"], errors="coerce")
            ).fillna(False).sum()
        ),
    }
```

If manual checks are sufficient, skip creating this file and document exact commands used in the report.

- [ ] **Step 2: Verify no timing violation in final smoke events**

Run:

```bash
./.venv/bin/python - <<'PY'
from pathlib import Path
import pandas as pd

events = pd.read_csv(Path("ML/reports/mt5_execution_loop/batch/_smoke/events.csv"), sep=";")
decision = pd.to_datetime(events["decision_time"], errors="coerce")
execution = pd.to_datetime(events["execution_time"], errors="coerce")
mask = decision.notna() & execution.notna() & (decision > execution)
print({"checked": int((decision.notna() & execution.notna()).sum()), "violations": int(mask.sum())})
if mask.any():
    print(events.loc[mask, ["event", "ticket", "side", "signal_time", "decision_time", "execution_time"]].head(10).to_string(index=False))
    raise SystemExit(1)
PY
```

Expected: `violations: 0`.

- [ ] **Step 3: Verify metrics parse and reconciliation**

Run:

```bash
./.venv/bin/python - <<'PY'
from pathlib import Path
import json

metrics = json.loads(Path("ML/reports/mt5_execution_loop/batch/_smoke/metrics.json").read_text())
print(metrics["reconciliation"])
assert metrics["reconciliation"]["class_counts"].get("UNEXPLAINED", -1) == 0
PY
```

Expected: printed reconciliation with `UNEXPLAINED: 0`.

- [ ] **Step 4: Decide whether full batch is required**

If max=2 and max=16 smoke pass but full batch was not run, final report may close only "multi-position smoke/lifecycle blocker" and must keep batch comparison `UNKNOWN`.

If full batch is required for closing the original Task 6 Step 6/7, run:

```bash
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=2 --force-rerun
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase aggregate
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=16 --force-rerun
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase aggregate
```

Expected: no parse failures; aggregate summaries written. If runtime is too high, stop after smoke and mark full batch `NOT_RUN`.

---

## Task 8: Correct old plan/report claims

**Files:**
- Modify: `docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md`
- Modify: `docs/reports/2026-08-02-mt5-multi-position-probe.md`

**Interfaces:**
- Consumes: audit findings and new verification results.
- Produces: corrected historical documents that no longer overclaim.

- [ ] **Step 1: Fix all broken commands in old plan (A13 — cover every malformed line)**

Audit item 7 lists three malformed command lines in `docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md` Task 6: `ML.baseline.tester` (non-existent module), `./.venv/bin/pythonスス...` (UTF-8 garbage from `Step 6`), and `ML.baseline.mt5_exec_diagnostic --phase multi-pos-comparison` (Step 7).

In `docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md`:

1. **Task 6 Step 5** — keep the existing `--max-positions=1` smoke command (already correct).

2. **Task 6 Step 6** — replace the broken batch commands with the ones the closeout actually uses:
   ```bash
   ./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=2 --force-rerun
   ./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=16 --force-rerun
   ```
   Mention that `--force-rerun` was added by this closeout (Task 5); for the old plan the historical command without `--force-rerun` is acceptable as long as the comment "rerun to overwrite SKIP" is attached.

3. **Task 6 Step 7** — replace the malformed `mt5_exec_diagnostic --phase multi-pos-comparison ...` with the actual aggregator the closeout uses:
   ```bash
   ./.venv/bin/python -m ML.baseline.run_mt5_batch --phase aggregate
   ```
   Delete the `pythonスス... root` UTF-8 garbage line (it appears once, between Step 6 and Step 7 command blocks).

4. Replace the expected `102 trades, same events` claim with:
   ```text
   Expected: event-level comparison against a pinned baseline artifact (produced by a fresh --force-rerun batch in the 2026-08-03 closeout), or explicitly mark backcompat as smoke-only.
   ```

Verify after edits:

```bash
rg -n "ML\.baseline\.tester|baseline\.mt5_exec_diagnostic|pythonス" docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md
```

Expected: no output (all malformed lines removed).

- [ ] **Step 2: Fix overclaims in old report**

In `docs/reports/2026-08-02-mt5-multi-position-probe.md`:
- replace "identical to previous baseline" with "matches previous smoke counters available in this report";
- replace "Canonical guarantee ... подтверждена" with "Canonical guarantee partially checked by smoke; full event-level backcompat remains open until closeout";
- replace "not a bug refactoring plan" with "blocking gap in multi-position lifecycle coverage";
- replace compile `PASS` wording with `PASS_WITH_WARNINGS` or `FAIL` according to the new closeout compile log (Task 6 Step 3).

- [ ] **Step 3: Add `research_priority` and `roadmap_track` (A10)**

In both old plan/report disclosure blocks, add:

```text
research_priority: medium — needed to determine whether single-position policy is a real execution constraint, but all results remain DIAGNOSTIC_ONLY.
roadmap_track: mt5-execution-closeout
```

`roadmap_track` is required by `docs/methodology/16-reporting-audit.md` disclosure; it references the named track in `docs/superpowers/roadmap.md`.

- [ ] **Step 4: Commit docs corrections**

```bash
git add docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md docs/reports/2026-08-02-mt5-multi-position-probe.md
git commit -m "docs: correct mt5 multi-position probe claims"
```

**Note (A7):** `CHANGELOG.md` and `CONTEXT_HANDOFF.md` for the previous [2026-08-02] entry are NOT updated in this commit — they are reconciled in Task 9 Step 4 in the same commit that lands the closeout report. This keeps history consistent: until Task 9, the only committed correction is the source plan/report text.

---

## Task 9: Final closeout report and project state sync

**Files:**
- Create: `docs/reports/2026-08-03-mt5-multi-position-closeout.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `docs/superpowers/audit.md` only if new verification changes an audit conclusion.

**Interfaces:**
- Consumes: Tasks 1-8 verification outputs.
- Produces: final stage report and synchronized project state.

- [ ] **Step 1: Write closeout report**

Create `docs/reports/2026-08-03-mt5-multi-position-closeout.md` with these sections:

```markdown
# MT5 Multi-Position Closeout — 2026-08-03

> **Stage level:** `research_hypothesis` · **Allowed verdict:** `DIAGNOSTIC_ONLY` · **Result:** `PASS` or `BLOCKED`

## Research-first disclosure

- lifecycle_status: research_hypothesis
- origin_bias: follow-up to audit `docs/superpowers/audit.md`
- roadmap_track: mt5-execution-closeout
- research_priority: medium — needed to determine whether single-position policy is a real execution constraint, but all results remain DIAGNOSTIC_ONLY
- current_search_budget: 0 model/search configurations; MQL5 execution refactor closeout; maxpos smoke/batch runs listed below
- cumulative_search_budget: inherited from 2026-07-31 batch, 2026-08-01 diagnostics, 2026-08-02 multi-position refactor
- next_probe_freeze: no ML winner selection; next execution probe must use fixed max_positions values and saved candidates only
- allowed_max_verdict: DIAGNOSTIC_ONLY
- forbidden_interpretations: profitable, ready, live-ready, tradable, new winner, model-quality proof

## Context

## Audit Findings Addressed

## Changed Files

## Verification

## Results

## Limitations

Multi-position scope (A11) — MANDATORY content of this section:
- Multi-pos is exercised only through `iSignal == 3` (`ML_TRADE`, `MT5_DiagnosticExecutor=true`). `iSignal == 5` (`ML_TRADE_TB` in `lib_ML_Signal_TB.mqh`) is out of scope for this closeout; covered by separate plan `2026-08-03-mt5-per-expert-ml-tracker.md`.
- `set.BUY` / `set.SEL` in `INPUT.mqh:13-14` remain a single planned order per bar. Therefore multiple same-side positions can only appear across multiple bars (pending → fill → next bar → new pending), never as several simultaneous `OrderSend` calls in the same bar. If max=2 smoke does not produce two simultaneous BUY (or SELL) positions on any tick, record the max-counted simultaneous positions explicitly and mark multi-pos proof as PARTIAL — do NOT claim full multi-pos proof from a single-bar-incomplete smoke.
- Multi-expert (`ExpTotal>1`) and per-expert ML-CSV (`rule_id` filter) are out of scope; covered by separate plan.
- `CLOSE` event only reads MT5 history by ticket and uses placeholder `broker_history_limited` for close reason, `order_close_price`, `take_profit`, `swap`, `commission` per `docs/methodology/13b-mt5-execution-parity.md:138-141` — not reconciled against MT5 deals in this closeout.

## Split Disclosure

## Forbidden Interpretations

## Next Step

## Related Materials
```

- [ ] **Step 2: Fill `Audit Findings Addressed`**

For each audit item 1-10, write one row:

```markdown
| Audit item | Status | Evidence |
|---|---|---|
| 1 same-direction blocked | PASS/FAIL | file lines + command |
```

- [ ] **Step 3: Fill `Verification` with exact commands**

Include:

```bash
./.venv/bin/python -m pytest tests/test_mt5_mql5_multiposition_contract.py tests/test_mt5_batch_runtime_contract.py tests/test_parse_mt5_execution_report.py tests/test_mt5_signal_executor_schema.py -q
git diff --check
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine ...
iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile_closeout.log | tail -n 30
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=1 --force-rerun
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=2 --force-rerun
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=16 --force-rerun
```

If any command was not run, write `NOT_RUN` and the reason.

- [ ] **Step 4: Update project state**

Update `CHANGELOG.md` newest entry with:

```markdown
## 2026-08-03 — MT5 Multi-Position Closeout

- **status**: DIAGNOSTIC_ONLY
- **summary**: ...
- **report**: `docs/reports/2026-08-03-mt5-multi-position-closeout.md`
- **decision**: ...
```

Also revise the existing `## 2026-08-02` entry in `CHANGELOG.md` so it no longer claims compile `PASS`: downgrade to `PASS_WITH_WARNINGS` (or `FAIL` if the new closeout compile gate did not reach `0 warnings`), and add a one-line pointer to `2026-08-03` closeout. This is the deferred CHANGELOG reconciliation referenced in Task 8 Step 4 note (A7).

Update `CONTEXT_HANDOFF.md` with the current next action. If full max=2/max=16 batch did not run, keep next action as execution closeout, not trade-count probe. Also note the pos-[] per-expert state fix (`Pos[]` in `EXPERT_PARENT_CLASS`) is now committed (it was uncommitted at audit time) — reference the commit SHA in this section.

Update `docs/superpowers/roadmap.md` only if the closeout changes the ACTIVE track. If only smoke passed, do not change the roadmap direction.

- [ ] **Step 5: Final verification**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_mql5_multiposition_contract.py tests/test_mt5_batch_runtime_contract.py tests/test_parse_mt5_execution_report.py tests/test_mt5_signal_executor_schema.py -q
git diff --check
```

Expected: all tests pass; no diff whitespace errors.

- [ ] **Step 6: Commit closeout docs**

```bash
git add docs/reports/2026-08-03-mt5-multi-position-closeout.md CHANGELOG.md CONTEXT_HANDOFF.md docs/superpowers/roadmap.md docs/superpowers/audit.md
git commit -m "docs: close mt5 multi-position refactor audit"
```

---

## Completion Criteria

The stage can be considered closed only if all are true:

- Static contract tests pass (including force-rerun behavioral tests from Task 1 Step 3).
- MT5 compile log for current `.ex5` shows `0 errors, 0 warnings` (Task 4 Step 4b removed `(int)ticket` casts); batch compile log agrees.
- `--max-positions=1 --force-rerun` smoke passes and is described as smoke unless event-level comparison is done.
- `--max-positions=2 --force-rerun` smoke passes without timing-contract violation.
- `--max-positions=16 --force-rerun` smoke either passes or is explicitly `NOT_RUN` with stage remaining `BLOCKED/UNKNOWN` for full multi-pos batch.
- Multi-position limits (one-signal-per-bar, multi-expert out of scope, `iSignal==5` out of scope) are written explicitly in the report's `Limitations` section.
- Final report does not use trading interpretations and keeps `allowed_max_verdict: DIAGNOSTIC_ONLY`.
- Final report disclosure contains `roadmap_track` and `research_priority` (A10).
- Catss `(int)` not found in `lib_ML_Signal.mqh` after Task 4 Step 4b (verified by `rg -n`).
- Old report/plan no longer contain known false or overstrong claims (Task 8 Step 1 grep returns no output).

## Self-Review

- Covers audit items 1-10: yes, mapped in Tasks 1-9.
- Methodology coverage: `13b` compile/tester parity and `16` report disclosure (incl. `roadmap_track`) are explicit.
- No `locked_test`, no winner selection, no model changes.
- Known risk: MQL5 static tests are text guards, not a substitute for tester; tester smoke is mandatory before closeout.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-03-mt5-multi-position-closeout.md`.

Two execution options:

1. **Subagent-Driven (recommended)** - dispatch a fresh subagent per task, review between tasks, faster isolation of MQL5/test/report changes.
2. **Inline Execution** - execute tasks in this session using executing-plans, with checkpoints after tests, MQL5 fixes, tester runs, and docs sync.

