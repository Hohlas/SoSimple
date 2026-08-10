# MT5 Per-Magic Signal Multiplexing (Single-Expert Loop) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Обеспечить корректное мультиплексирование ML-сигналов между несколькими алгоритмами (`EXP[e]`, `e ∈ [0, ExpTotal)`) внутри **одного** эксперта на **одном** графике, когда каждый алгоритм идентифицируется своим `magic = EXP[e].Mgc`, а сигналы из общего CSV `mt5_entry_signals.csv` маршрутизируются по `rule_id == "mt5_rule_" + IntegerToString(Mgc)`.

**Architecture:**
- MQL5: `MT5_FindEntrySignal(datetime barTime, string rule_id_filter)` возвращает индекс первой строки, где `MT5_EntryTimes[i]==barTime && (rule_id_filter=="" || MT5_RuleIds[i]==rule_id_filter)`. Вызов из `ML_TRADE` строит `rule_id_filter` локально как `"mt5_rule_" + IntegerToString(Mgc)` — **без глобального синглтона**. Backcompat: `rule_id_filter==""` выбирает первую строку по `barTime` (текущее поведение).
- Python: `prepare_entry_quality_source` принимает `rule_id: str` (type-guard); `run_mt5_batch.py` в multi-algo режиме генерирует объединённый signal CSV, где каждой строке приписан `rule_id=f"mt5_rule_{Mgc}"` соответствующего алгоритма из `#.csv`. Single-algo режим не меняется.
- Reconciliation: `parse_mt5_execution_report` группирует события по `(magic, rule_id)`; оба поля уже пишутся в event CSV.

**Tech Stack:** MQL5 (MetaEditor 5, Wine + xvfb-run), Python 3.10+ (pandas, pytest), существующие `mt5_signal_schema`, `export_mt5_entry_signals`, `parse_mt5_execution_report`.

## Global Constraints

- depends_on: `docs/superpowers/plans/2026-08-03-mt5-multi-position-closeout.md` (исполнен 2026-08-07).
- blocks: production multi-algo rollout (`ExpTotal>1` в live).
- supersedes: прежняя формулировка «per-expert = несколько графиков» (удалена).
- exit_decisions: `continue` к production `ExpTotal>1` rollout, `close` (мультиплексирование не требуется), `unblock` (обнаружена иная причина, по которой multi-algo не нужен).
- locked_test_policy: `locked_test` не открывать. Выбор моделей/порогов/профилей/сайдов/горизонтов этим планом не производится.
- Compile gate: `0 errors, 0 warnings` (MetaEditor; `docs/methodology/13b-mt5-execution-parity.md:165`). Exit-код `wine` — не verdict (строки 168-170).
- Timing contract: `feature_time <= time < feature_available_time <= decision_time` (signal CSV); `feature_time <= signal_time < feature_available_time <= decision_time <= execution_time` (event CSV, signal-linked rows).
- CSV contract: не расширять колонки signal/event CSV без синхронизации `tests/test_mt5_signal_executor_schema.py` (`docs/methodology/13b-mt5-execution-parity.md:58,73`).
- `allowed_max_verdict: DIAGNOSTIC_ONLY`.
- Forbidden interpretations: `profitable`, `ready`, `live-ready`, `tradable`, `new winner`, `model-quality proof`.
- No ML changes: план не меняет модель, frozen export, threshold, profile, side, horizon, entry/exit rule. Только маршрутизация сигналов + reconciliation.
- Compat constraint: `InpMT5_MaxPositions=1` остаётся каноническим single-position режимом. Multi-algo мультиплексирование работает и при `MaxPositions=1`, и при `MaxPositions>1`. Backcompat для single-algo (`ExpTotal==1`, без `rule_id`-фильтра) сохраняется.
- `iSignal==5` (`ML_TRADE_TB` в `lib_ML_Signal_TB.mqh`) — **out of scope**. Собственный CSV (`ml_signals_tb.csv`) без `rule_id`. Данный план работает только с `iSignal==3` (`ML_TRADE`, `MT5_DiagnosticExecutor=true`).
- `#.csv` contract: `SERVICE.mqh:122-220` (`INPUT_FILE_READ`) читает `#.csv` в `EXP[]`; `EXP[e].Mgc` (int) генерируется `MAGIC_GENERATOR()` (`SERVICE.mqh:95-100`). План не меняет формат `#.csv` и `INPUT_FILE_READ`; добавляет только конвенцию `rule_id == "mt5_rule_" + IntegerToString(Mgc)`.
- Magic is int: `MAGIC_GENERATOR` возвращает `MathAbs(int(MagicLong))` (`SERVICE.mqh:99`). Не использовать `run_id` с `_` и спецсимволами внутри MQL5; конвенция `mt5_rule_<int>` детерминирована и тестируема.
- Run environment: `./.venv/bin/python` для всех Python-вызовов (AGENTS.md).
- Compile OS: Wine + xvfb-run на Linux, `WINEPREFIX=/home/hohla/.mt5`.

## File Structure

| Файл | Ответственность | Тип изменения |
|---|---|---|
| `MT/MQL5/Include/lib_ML_Signal.mqh` | `MT5_FindEntrySignal` + локальный `rule_id_filter` в `ML_TRADE` | Modify |
| `ML/baseline/prepare_mt5_entry_source.py` | type-guard `rule_id: str` | Modify (type guard only) |
| `ML/baseline/run_mt5_batch.py` | флаг `--multi-algo`, multi-rule signal CSV generation | Modify |
| `ML/baseline/parse_mt5_execution_report.py` | `(magic, rule_id)`-группировка в reconciliation | Modify |
| `tests/test_mt5_per_magic_multiplexing_contract.py` | static contract tests (MQL5 + Python) | Create |
| `tests/test_mt5_multi_algo_smoke.py` | интеграционный smoke-тест `ExpTotal=2` | Create |

---

## Task P0: Verify closeout-план precondition

**Files:**
- Read-only: `MT/MQL5/Include/lib_ML_Signal.mqh`, `MT/MQL5/Include/FUNCTIONS.mqh`, `ML/baseline/run_mt5_batch.py`

**Interfaces:**
- Consumes: git-состояние `lib_ML_Signal.mqh` и `run_mt5_batch.py` после closeout-плана.
- Produces: `PRECONDITION_OK` или `PRECONDITION_FAILED` + точный список незакрытых пунктов closeout-плана.

- [ ] **Step 1: Run grep checks для closeout signals**

```bash
rg -n "MT5_TrackedTicket\b" MT/MQL5/Include/lib_ML_Signal.mqh
rg -n "MT5_TRACKED_POSITION\b|MT5_TrackedPositions\b|MT5_LogLifecycleForTicket\b" MT/MQL5/Include/lib_ML_Signal.mqh
rg -n "\(int\)OrderTicket\(\)|\(int\)ticket\b|\(int\)MT5_TrackedTicket" MT/MQL5/Include/lib_ML_Signal.mqh MT/MQL5/Include/ORDERS.mqh MT/MQL5/Include/ERRORs.mqh
rg -n "force_rerun" ML/baseline/run_mt5_batch.py
```

Expected: 1-я команда — **0 строк** (singleton удалён); 2-я — ≥4 строки (struct, массив, функция, вызов); 3-я — 0 строк (int-касты удалены); 4-я — ≥1 (`force_rerun` в `run_batch`).

- [ ] **Step 2: Decision branch**

- Все 4 check прошли → записать `docs/reports/2026-08-03-mt5-per-magic-multiplexing-precondition.md` с `precondition: OK` и SHA файлов; перейти к Task 1.
- Хотя бы один failed → записать тот же файл с `precondition: FAILED` + список незакрытых пунктов closeout-плана `docs/superpowers/plans/2026-08-03-mt5-multi-position-closeout.md` (Tasks 1-9). **STOP**. Соответствие check → задача: absence `MT5_TrackedTicket` / наличие struct+массив+`MT5_LogLifecycleForTicket` → Task 4; absence int-кастов → Tasks 2-4; наличие `force_rerun` → Task 5.

- [ ] **Step 3: Commit precondition artifact**

```bash
git add docs/reports/2026-08-03-mt5-per-magic-multiplexing-precondition.md
git commit -m "docs: per-magic multiplexing precondition (closeout verified)"
```

Если `precondition: FAILED` — commit всё равно делается (аудит-артефакт), но дальнейшие задачи не исполняются.

---

## Task 1: Static contract tests для per-magic multiplexing

**Files:**
- Create: `tests/test_mt5_per_magic_multiplexing_contract.py`
- Read-only reference: `MT/MQL5/Include/lib_ML_Signal.mqh`, `ML/baseline/run_mt5_batch.py`, `ML/baseline/prepare_mt5_entry_source.py`, `ML/baseline/parse_mt5_execution_report.py`

**Interfaces:**
- Consumes: сигнатуры `MT5_FindEntrySignal`, `MT5_ENTRY_INIT`, `ML_TRADE`; сигнатуры `prepare_entry_quality_source`, `make_run_id`; сигнатура `parse_mt5_execution_report`.
- Produces: failing-тесты, фиксирующие целевые контракты: (а) `MT5_FindEntrySignal(datetime barTime, string rule_id_filter)`; (б) `MT5_ENTRY_INIT` грузит CSV без фильтра; (в) `ML_TRADE` выставляет local `rule_id_filter = "mt5_rule_" + (string)Mgc` перед вызовом `MT5_FindEntrySignal(barTime, rule_id_filter)`; (г) `prepare_entry_quality_source` type-guards `rule_id: str`; (д) `run_mt5_batch` при `--multi-algo` генерирует `rule_id=f"mt5_rule_{Mgc}"`; (е) `parse_mt5_execution_report` группирует по `(magic, rule_id)`.

- [ ] **Step 1: Write the failing static tests**

Создать `tests/test_mt5_per_magic_multiplexing_contract.py`:

```python
from __future__ import annotations

import re
from pathlib import Path

import pytest

MQL_LIB = Path("MT/MQL5/Include/lib_ML_Signal.mqh")
RUN_BATCH = Path("ML/baseline/run_mt5_batch.py")
PREPARE_SOURCE = Path("ML/baseline/prepare_mt5_entry_source.py")
PARSE_REPORT = Path("ML/baseline/parse_mt5_execution_report.py")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _fn_body(text: str, sig_re: str) -> str:
    m = re.search(sig_re + r"\s*\{(?P<body>.*?)\n\}", text, flags=re.S)
    assert m is not None, f"signature not found: {sig_re}"
    return m.group("body")


# --- MQL5: MT5_FindEntrySignal signature ---

def test_mql5_find_entry_signal_accepts_rule_id_filter() -> None:
    text = _text(MQL_LIB)
    m = re.search(
        r"int\s+MT5_FindEntrySignal\s*\(\s*datetime\s+barTime\s*,\s*string\s+rule_id_filter\s*\)\s*\{",
        text,
    )
    assert m is not None, (
        "MT5_FindEntrySignal должен принимать (datetime barTime, string rule_id_filter) "
        "для per-magic маршрутизации сигналов внутри одного эксперта."
    )


def test_mql5_find_entry_signal_filters_by_rule_id_opt_in() -> None:
    text = _text(MQL_LIB)
    body = _fn_body(text, r"int\s+MT5_FindEntrySignal\s*\([^)]*\)")
    assert "rule_id_filter" in body
    assert "MT5_RuleIds[i]" in body
    assert 'rule_id_filter != ""' in body or 'rule_id_filter!=""' in body.replace(" ", ""), (
        "rule_id_filter должен быть opt-in: пустая строка = backcompat (первое совпадение по barTime)."
    )


def test_mql5_entry_init_has_no_rule_id_filter() -> None:
    text = _text(MQL_LIB)
    body = _fn_body(text, r"bool\s+MT5_ENTRY_INIT\s*\(\s*\)")
    assert "rule_id_filter" not in body, (
        "MT5_ENTRY_INIT должен грузить CSV целиком; фильтрация — только в MT5_FindEntrySignal."
    )
    assert "MT5_RuleIds[i]" in body, "Колонка rule_id читается и хранится в MT5_RuleIds[]."


# --- MQL5: ML_TRADE sets local rule_id_filter from Mgc ---

def test_ml_trade_builds_rule_id_filter_from_mgc() -> None:
    text = _text(MQL_LIB)
    # Ищем класс EXPERT::ML_TRADE либо свободную функцию ML_TRADE — обе формы могут встречаться.
    body_match = re.search(
        r"(?:void\s+EXPERT::ML_TRADE|void\s+ML_TRADE)\s*\(\s*\)\s*\{(?P<body>.*?)\n\}",
        text,
        flags=re.S,
    )
    assert body_match is not None
    body = body_match.group("body")
    assert "rule_id_filter" in body
    assert re.search(r'"mt5_rule_"\s*\+\s*\(string\)\s*Mgc|"mt5_rule_"\s*\+\s*IntegerToString\s*\(\s*Mgc', body), (
        "rule_id_filter должен строиться локально как 'mt5_rule_' + (string)Mgc; "
        "глобальный синглтон MT5_RuleIdFilter запрещён."
    )
    assert re.search(r"MT5_FindEntrySignal\s*\([^)]*rule_id_filter[^)]*\)", body), (
        "ML_TRADE должен передавать rule_id_filter в MT5_FindEntrySignal."
    )


def test_no_global_rule_id_filter_singleton() -> None:
    text = _text(MQL_LIB)
    m = re.search(r"^(?:string|static\s+string)\s+MT5_RuleIdFilter\b", text, flags=re.M)
    assert m is None, (
        "Глобальный синглтон MT5_RuleIdFilter запрещён: мультиплексирование идёт в одном "
        "потоке терминала последовательно по EXP[], локальная переменная достаточна."
    )


# --- Python: prepare_entry_quality_source type guard ---

def test_prepare_entry_quality_source_rule_id_type_annotation() -> None:
    text = _text(PREPARE_SOURCE)
    m = re.search(
        r"def\s+prepare_entry_quality_source\s*\([^)]*rule_id\s*:\s*str[,\)]",
        text,
    )
    assert m is not None, "prepare_entry_quality_source: rule_id: str type annotation обязателен."


def test_prepare_entry_quality_source_rule_id_runtime_guard() -> None:
    text = _text(PREPARE_SOURCE)
    body = _fn_body(text, r"def\s+prepare_entry_quality_source\s*\([^)]*\)")
    assert re.search(r"isinstance\s*\(\s*rule_id\s*,\s*str\s*\)", body), (
        "prepare_entry_quality_source должен runtime-check 'isinstance(rule_id, str)' "
        "и бросать TypeError на не-str (None, int, float)."
    )


# --- Python: run_mt5_batch multi-algo flag ---

def test_run_mt5_batch_has_multi_algo_flag() -> None:
    text = _text(RUN_BATCH)
    assert re.search(r'add_argument\s*\(\s*["\']--multi-algo["\']', text), (
        "run_mt5_batch.py: --multi-algo флаг включает multi-rule signal generation."
    )


def test_run_mt5_batch_multi_algo_uses_mt5_rule_magic_convention() -> None:
    text = _text(RUN_BATCH)
    assert re.search(r'rule_id\s*=\s*f["\']mt5_rule_\{[^}]*\}["\']', text), (
        "В --multi-algo режиме rule_id = 'mt5_rule_<Mgc>' (int magic → str)."
    )


# --- Python: parse_mt5_execution_report (magic, rule_id) grouping ---

def test_parse_mt5_execution_report_groups_by_magic_and_rule_id() -> None:
    text = _text(PARSE_REPORT)
    assert "rule_id" in text, "parse_mt5_execution_report должен читать колонку rule_id."
    assert re.search(r"groupby\s*\(\s*\[[\"']magic[\"'],\s*[\"']rule_id[\"']\]", text) or re.search(
        r"groupby\s*\(\s*\[[\"']rule_id[\"'],\s*[\"']magic[\"']\]", text
    ), "Группировка событий по (magic, rule_id) — per-algo метрики в одном отчёте."
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_magic_multiplexing_contract.py -q
```

Expected: **FAIL** — не менее 8 failing тестов (текущая сигнатура `MT5_FindEntrySignal(datetime barTime)`, отсутствие `--multi-algo`, отсутствие `(magic, rule_id)`-группировки).

- [ ] **Step 3: Commit failing tests**

```bash
git add tests/test_mt5_per_magic_multiplexing_contract.py
git commit -m "test: add failing static contract tests for per-magic multiplexing"
```

---

## Task 2: Implement MQL5 per-magic `rule_id` filter in `MT5_FindEntrySignal`

**Files:**
- Modify: `MT/MQL5/Include/lib_ML_Signal.mqh:207-212` (`MT5_FindEntrySignal`)
- Modify: `MT/MQL5/Include/lib_ML_Signal.mqh` (тело `ML_TRADE` — см. Task 3)

**Interfaces:**
- Consumes: массив `MT5_RuleIds[]`, `MT5_EntryTimes[]`, `MT5_EntrySignalCount` (уже populated в `MT5_ENTRY_INIT`).
- Produces: новая сигнатура `int MT5_FindEntrySignal(datetime barTime, string rule_id_filter)`. Контракт: opt-in фильтр; `rule_id_filter==""` возвращает первое совпадение по `barTime` (backcompat).

- [ ] **Step 1: Modify `MT5_FindEntrySignal` signature and body**

Replace `MT/MQL5/Include/lib_ML_Signal.mqh:207-212` with:

```cpp
int MT5_FindEntrySignal(datetime barTime, string rule_id_filter) {
   for (int i = 0; i < MT5_EntrySignalCount; i++) {
      if (MT5_EntryTimes[i] != barTime) continue;
      if (rule_id_filter != "" && MT5_RuleIds[i] != rule_id_filter) continue;
      return i;
   }
   return -1;
}
```

- [ ] **Step 2: Update all internal callers to pass empty string (backcompat)**

Search all `.mqh`/`.mq5` for `MT5_FindEntrySignal(` and update every call to pass `""` as second argument — **кроме** `ML_TRADE`, который будет править Task 3:

```bash
rg -n "MT5_FindEntrySignal\s*\(" MT/MQL5
```

Expected: список вызовов. Каждый вызов вне `ML_TRADE` превратить в `MT5_FindEntrySignal(Time[bar], "")`. Если единственный вызов — `lib_ML_Signal.mqh:875` внутри `ML_TRADE`, обновить только его (см. Task 3).

- [ ] **Step 3: Compile gate**

```bash
xvfb-run -a wine /home/hohla/.mt5/drive_c/Program\ Files/MetaTrader\ 5/metaeditor5.exe \
  /compile:"/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MQL5/Experts/\$o\$imple.mq5" \
  /log /inc:"/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MQL5/Include"
```

Expected: `0 errors, 0 warnings` в `compile.log`.

- [ ] **Step 4: Run affected static tests**

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_magic_multiplexing_contract.py -q \
  -k "find_entry_signal or entry_init"
```

Expected: 3 passed (сигнатура + opt-in filter + `MT5_ENTRY_INIT` не содержит `rule_id_filter`).

- [ ] **Step 5: Commit**

```bash
git add MT/MQL5/Include/lib_ML_Signal.mqh
git commit -m "feat(mt5): per-magic rule_id filter in MT5_FindEntrySignal"
```

---

## Task 3: ML_TRADE builds local `rule_id_filter` from `Mgc`

**Files:**
- Modify: `MT/MQL5/Include/lib_ML_Signal.mqh` (тело `ML_TRADE`, текущий `mt5_idx = MT5_FindEntrySignal(Time[bar])` на строке 875)

**Interfaces:**
- Consumes: `Mgc` (входной параметр `ML_TRADE`, см. `lib_ML_Signal.mqh:365`); сигнатура из Task 2.
- Produces: `string rule_id_filter` (local), вызов `MT5_FindEntrySignal(Time[bar], rule_id_filter)`.

- [ ] **Step 1: Build local rule_id_filter in ML_TRADE**

В теле `ML_TRADE` перед вызовом `MT5_FindEntrySignal` (строка 875) добавить:

```cpp
   string rule_id_filter = "mt5_rule_" + IntegerToString(Mgc);
   int mt5_idx = MT5_FindEntrySignal(Time[bar], rule_id_filter);
```

**У-4 (global singleton запрещён)**: `rule_id_filter` — **local string**. Глобальная `MT5_RuleIdFilter` не вводится: `ML_TRADE` вызывается последовательно в `for (e=0; e<ExpTotal; e++) EXP[e].MAIN()` — гонки между алгоритмами нет.

- [ ] **Step 2: Add backcompat branch for single-algo**

Чтобы старый single-algo режим (`ExpTotal==1`, CSV без `rule_id` или с одним значением) продолжал работать, обернуть фильтр:

```cpp
   string rule_id_filter = "";
   if (MT5_EntrySignalCount > 0 && MT5_RuleIds[0] != "") {
      rule_id_filter = "mt5_rule_" + IntegerToString(Mgc);
   }
   int mt5_idx = MT5_FindEntrySignal(Time[bar], rule_id_filter);
```

Контракт: если в CSV вообще нет `rule_id` (все строки пустые) — фильтр выключен, поведение идентично старому. Если `rule_id` есть — включается per-magic фильтрация.

- [ ] **Step 3: Compile gate**

```bash
xvfb-run -a wine /home/hohla/.mt5/drive_c/Program\ Files/MetaTrader\ 5/metaeditor5.exe \
  /compile:"/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MQL5/Experts/\$o\$imple.mq5" \
  /log /inc:"/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MQL5/Include"
```

Expected: `0 errors, 0 warnings`.

- [ ] **Step 4: Run the ML_TRADE static test**

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_magic_multiplexing_contract.py::test_ml_trade_builds_rule_id_filter_from_mgc -v
./.venv/bin/python -m pytest tests/test_mt5_per_magic_multiplexing_contract.py::test_no_global_rule_id_filter_singleton -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add MT/MQL5/Include/lib_ML_Signal.mqh
git commit -m "feat(mt5): per-magic rule_id filter built locally in ML_TRADE"
```

---

## Task 4: Python `prepare_entry_quality_source` rule_id type guard

**Files:**
- Modify: `ML/baseline/prepare_mt5_entry_source.py` (функция `prepare_entry_quality_source`, параметры `rule_id: str = "entry_quality_filter"`)

**Interfaces:**
- Consumes: существующая сигнатура.
- Produces: runtime `isinstance(rule_id, str)` → `TypeError` otherwise.

- [ ] **Step 1: Add runtime guard at function entry**

В начало тела `prepare_entry_quality_source` (сразу после сигнатуры) добавить:

```python
    if not isinstance(rule_id, str):
        raise TypeError(
            f"rule_id must be str, got {type(rule_id).__name__}: {rule_id!r}"
        )
```

- [ ] **Step 2: Run the type-guard tests**

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_magic_multiplexing_contract.py -q \
  -k "prepare_entry_quality_source"
```

Expected: 2 passed (type annotation + runtime guard).

- [ ] **Step 3: Run full signal-related pytest suite**

```bash
./.venv/bin/python -m pytest tests/ -q -k "mt5 or entry_signal or signal_schema"
```

Expected: все ранее проходившие тесты проходят (type guard не ломает совместимость: `rule_id` всегда был `str`).

- [ ] **Step 4: Commit**

```bash
git add ML/baseline/prepare_mt5_entry_source.py
git commit -m "feat(mt5): prepare_entry_quality_source rule_id type guard"
```

---

## Task 5: `--multi-algo` flag in `run_mt5_batch.py`

**Files:**
- Modify: `ML/baseline/run_mt5_batch.py`

**Interfaces:**
- Consumes: `#.csv`-контракт (`SERVICE.mqh:122-220`) — список `EXP[e].Mgc` для каждой строки. Python-парсер `#.csv` уже существует в `run_mt5_batch.py` (grep `INPUT_FILE_READ` / `read_exp_csv`).
- Produces: флаг `--multi-algo`, который включает multi-rule signal generation: одна CSV, где `rule_id=f"mt5_rule_{Mgc}"` для каждой строки, соответствующей конкретному алгоритму.

- [ ] **Step 1: Add `--multi-algo` argument to argparse**

В блоке `argparse` добавить:

```python
    parser.add_argument(
        "--multi-algo",
        action="store_true",
        help=(
            "Generate multi-rule signal CSV: each row tagged with "
            "rule_id=f'mt5_rule_{Mgc}' per #.csv algorithm. "
            "Default (off): single rule_id per run (backcompat)."
        ),
    )
```

- [ ] **Step 2: Implement multi-rule generation**

В функции `signals`/`prepare_signals` (или аналог, отвечающий за генерацию signal CSV) добавить ветку:

```python
    if args.multi_algo:
        exp_rows = read_exp_csv(EXP_CSV_PATH)  # существующий парсер #.csv
        per_algo_sources: list[pd.DataFrame] = []
        for _, exp in exp_rows.iterrows():
            mgc = int(exp["Mgc"])
            src = prepare_entry_quality_source(
                source=base_source,
                rule_id=f"mt5_rule_{mgc}",
                latency_bars=args.latency_bars,
            )
            per_algo_sources.append(src)
        combined = pd.concat(per_algo_sources, ignore_index=True)
        combined = combined.sort_values("time").reset_index(drop=True)
    else:
        combined = prepare_entry_quality_source(
            source=base_source,
            rule_id=make_run_id(cand),
            latency_bars=args.latency_bars,
        )
```

- [ ] **Step 3: Run multi-algo static tests**

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_magic_multiplexing_contract.py -q \
  -k "run_mt5_batch"
```

Expected: 2 passed (flag + convention).

- [ ] **Step 4: Smoke: generate multi-algo CSV и проверить структуру**

```bash
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase signals --multi-algo --smoke-only
./.venv/bin/python -c "
import pandas as pd
df = pd.read_csv('ML/reports/mt5_execution_loop/batch/_smoke/entry_signals.csv', sep=';')
print('rows=', len(df), 'unique_rule_ids=', df['rule_id'].nunique())
print('rule_id sample:', sorted(df['rule_id'].unique())[:5])
assert df['rule_id'].str.startswith('mt5_rule_').all(), 'all rows must carry mt5_rule_<Mgc>'
"
```

Expected: ≥2 уникальных `rule_id` (если в `#.csv` ≥2 строки); все значения вида `mt5_rule_<int>`.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/run_mt5_batch.py
git commit -m "feat(mt5): --multi-algo flag generates multi-rule signal CSV"
```

---

## Task 6: Per-(magic, rule_id) reconciliation в `parse_mt5_execution_report.py`

**Files:**
- Modify: `ML/baseline/parse_mt5_execution_report.py`

**Interfaces:**
- Consumes: event CSV, в котором уже есть колонки `magic` и `rule_id`.
- Produces: итоговый отчёт с группировкой по `(magic, rule_id)` — per-algo + per-rule метрики в одном документе.

- [ ] **Step 1: Add `(magic, rule_id)` groupby branch**

В функции агрегации событий (после базовой агрегации по `magic`) добавить:

```python
    if "rule_id" in df.columns:
        df["rule_id"] = df["rule_id"].fillna("").astype(str)
        grouped = df.groupby(["magic", "rule_id"])
        report["per_algo"] = {
            (int(m), str(r)): _agg(group)
            for (m, r), group in grouped
        }
```

где `_agg(group)` — существующий helper агрегации (count OPEN/CLOSE, PnL sum, fill rate и т.д.).

- [ ] **Step 2: Run the reconciliation test**

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_magic_multiplexing_contract.py::test_parse_mt5_execution_report_groups_by_magic_and_rule_id -v
```

Expected: 1 passed.

- [ ] **Step 3: Run full parse/reconciliation pytest suite**

```bash
./.venv/bin/python -m pytest tests/ -q -k "parse_mt5 or reconciliation or mt5_execution"
```

Expected: все ранее проходившие тесты проходят (новая группировка additive, не ломает старую).

- [ ] **Step 4: Commit**

```bash
git add ML/baseline/parse_mt5_execution_report.py
git commit -m "feat(mt5): (magic, rule_id) grouping in parse_mt5_execution_report"
```

---

## Task 7: Compile gate и multi-algo smoke (`ExpTotal=2`)

**Files:**
- Create: `tests/test_mt5_multi_algo_smoke.py`
- Read-only: `MT/MQL5/Experts/$o$imple.mq5`, `MT/MQL5/Include/*.mqh`

**Interfaces:**
- Consumes: результат Tasks 1-6.
- Produces: smoke-репорт `ML/reports/mt5_execution_loop/multiplex_smoke/` с подпрогонами `single_algo_max1`, `single_algo_max64`, `multi_algo_max1`, `multi_algo_max64`.

- [ ] **Step 1: Compile full Expert**

```bash
xvfb-run -a wine /home/hohla/.mt5/drive_c/Program\ Files/MetaTrader\ 5/metaeditor5.exe \
  /compile:"/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MQL5/Experts/\$o\$imple.mq5" \
  /log /inc:"/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MQL5/Include"
grep -E "errors|warnings" <compile.log>
```

Expected: `0 errors, 0 warnings`.

- [ ] **Step 2: Prepare #.csv с `ExpTotal=2`**

Создать `MT/MQL5/Files/$o$imple.csv` (или tester-копию) с двумя строками, отличающимися magic:

```csv
$o$imple_v3.0;...;<Mgc_A>
$o$imple_v3.0;...;<Mgc_B>
```

где `Mgc_A` и `Mgc_B` — разные int, сгенерированные `MAGIC_GENERATOR()` для двух наборов входных параметров.

- [ ] **Step 3: Generate multi-algo signal CSV (smoke)**

```bash
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase signals --multi-algo --smoke-only
```

Expected: `_smoke/entry_signals.csv` содержит строки `rule_id=mt5_rule_<Mgc_A>` и `rule_id=mt5_rule_<Mgc_B>`.

- [ ] **Step 4: Run MT5 tester smoke в 4 режимах**

```bash
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --smoke-only --max-positions=1
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --smoke-only --max-positions=64
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --smoke-only --multi-algo --max-positions=1
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --smoke-only --multi-algo --max-positions=64
```

Expected для каждого:
- Process exits `0`.
- Event CSV создан и содержит события обоих magic (в multi-algo режимах).
- `UNEXPLAINED=0` в per-magic lifecycle counters.
- `TIMING_VIOLATION=0`.
- В single-algo режимах поведение **не меняется** относительно closeout-эталона 2026-08-07.

- [ ] **Step 5: Aggregate и сравнить с single-algo эталоном**

```bash
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase aggregate --smoke-only
```

Expected: per-algo PnL в multi-algo режиме совпадает (в пределах копеек) с PnL соответствующего single-algo прогона → мультиплексирование не вносит интерференции.

- [ ] **Step 6: Write smoke test**

Создать `tests/test_mt5_multi_algo_smoke.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

SMOKE_DIR = Path("ML/reports/mt5_execution_loop/multiplex_smoke")


def test_multi_algo_per_algo_pnl_matches_single_algo_reference() -> None:
    ref = json.loads((SMOKE_DIR / "single_algo_max1" / "metrics.json").read_text())
    multi = json.loads((SMOKE_DIR / "multi_algo_max1" / "metrics.json").read_text())
    for (magic, rule_id), per_algo in multi["per_algo"].items():
        ref_pnl = ref["per_magic"][str(magic)]["pnl"]
        assert abs(per_algo["pnl"] - ref_pnl) < 0.02, (
            f"magic={magic} rule_id={rule_id}: multi-algo PnL {per_algo['pnl']} "
            f"!= single-algo reference {ref_pnl}"
        )


def test_multi_algo_unexplained_zero() -> None:
    for mode in ("multi_algo_max1", "multi_algo_max64"):
        summary = json.loads((SMOKE_DIR / mode / "summary.json").read_text())
        assert summary["unexplained"] == 0, f"{mode}: unexplained={summary['unexplained']}"


def test_multi_algo_no_timing_violation() -> None:
    for mode in ("multi_algo_max1", "multi_algo_max64"):
        summary = json.loads((SMOKE_DIR / mode / "summary.json").read_text())
        assert summary.get("timing_violation_count", 0) == 0
```

- [ ] **Step 7: Run smoke tests**

```bash
./.venv/bin/python -m pytest tests/test_mt5_multi_algo_smoke.py -v
```

Expected: 3 passed.

- [ ] **Step 8: Commit**

```bash
git add tests/test_mt5_multi_algo_smoke.py ML/reports/mt5_execution_loop/multiplex_smoke/
git commit -m "test(mt5): multi-algo ExpTotal=2 smoke (max=1 / max=64)"
```

---

## Task 8: Финальная отчётность и синхронизация

**Files:**
- Create: `docs/reports/2026-08-03-mt5-per-magic-multiplexing.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md` (указатель на active plan + latest report)
- Modify: `docs/superpowers/roadmap.md` (ACTIVE → status: plan completed)

**Interfaces:**
- Consumes: результаты Tasks P0, 1-7.
- Produces: отчёт со всеми 8 mandatory disclosure fields (`docs/methodology/16-reporting-audit.md:65-77`): `lifecycle_status`, `origin_bias`, `research_priority`, `current_search_budget`, `cumulative_search_budget`, `next_probe_freeze`, `allowed_max_verdict`, `forbidden_interpretations`.

- [ ] **Step 1: Write the report**

Создать `docs/reports/2026-08-03-mt5-per-magic-multiplexing.md` со структурой:

```markdown
# MT5 Per-Magic Signal Multiplexing Report

## Вердикт
`DIAGNOSTIC_ONLY`.

## Summary
1-2 абзаца: мультиплексирование сигналов внутри одного эксперта на одном графике
(ExpTotal>1, цикл EXP[]) проверено; per-magic rule_id filter работает; per-algo
PnL в multi-algo совпадает с single-algo эталоном; UNEXPLAINED=0, TIMING_VIOLATION=0.

## Research-first disclosure
- lifecycle_status: diagnostic_infrastructure
- origin_bias: port-audit (MT4 → MT5 мультиплексирование)
- research_priority: medium (production rollout enabler)
- current_search_budget: <N> hours
- cumulative_search_budget: <N> hours
- next_probe_freeze: production ExpTotal>1 rollout
- allowed_max_verdict: DIAGNOSTIC_ONLY
- forbidden_interpretations: profitable, ready, live-ready, tradable, new winner,
  model-quality proof

## Evidence
- `ML/reports/mt5_execution_loop/multiplex_smoke/` (4 подпрогона).
- Per-magic PnL parity: <таблица>.
- UNEXPLAINED counts: 0 во всех режимах.
- Compile log: `0 errors, 0 warnings`.

## Limitations
- Только iSignal=3 (ML_TRADE); iSignal=5 (ML_TRADE_TB) — out of scope.
- locked_test не открывался.
- Никаких выводов о качестве моделей или PnL-готовности.

## Next Step
Production rollout: ExpTotal>1 в live-конфигурации (отдельный план).
```

- [ ] **Step 2: Update CONTEXT_HANDOFF.md**

- Раздел «Current Active State» → latest plan заменить на `docs/superpowers/plans/2026-08-03-mt5-per-magic-multiplexing.md` (latest plan completed).
- Раздел «Decision»: добавить «per-magic multiplexing verified DIAGNOSTIC_ONLY; production ExpTotal>1 rollout — next step, отдельный план».

- [ ] **Step 3: Update `docs/superpowers/roadmap.md` ACTIVE-секция**

Status: `plan completed`. Обновить current facts и next action (production rollout).

- [ ] **Step 4: Update CHANGELOG.md**

Новая запись в начале:

```markdown
## [2026-08-XX] — MT5 Per-Magic Signal Multiplexing (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-08-03-mt5-per-magic-multiplexing.md`
- **topics**: `mt5`, `multiplexing`, `per-magic`, `rule_id`, `single-expert-loop`
- **summary**: ... (1-2 предложения).
- **artifacts**: `MT/MQL5/Include/lib_ML_Signal.mqh`, `ML/baseline/run_mt5_batch.py`,
  `ML/baseline/parse_mt5_execution_report.py`,
  `ML/reports/mt5_execution_loop/multiplex_smoke/`
- **decision**: `DIAGNOSTIC_ONLY`. Production ExpTotal>1 rollout — отдельный следующий план.
```

- [ ] **Step 5: Commit**

```bash
git add docs/reports/2026-08-03-mt5-per-magic-multiplexing.md \
        CONTEXT_HANDOFF.md docs/superpowers/roadmap.md CHANGELOG.md
git commit -m "docs: per-magic multiplexing report + project state sync"
```

---

## Completion Criteria

- Все Tasks P0, 1-7 успешно завершены (pytest green, compile `0/0`, smoke parity).
- Отчёт `docs/reports/2026-08-03-mt5-per-magic-multiplexing.md` создан со всеми 8 disclosure fields.
- `CONTEXT_HANDOFF.md`, `roadmap.md`, `CHANGELOG.md` синхронизированы.
- `locked_test` не открывался.
- Вердикт: `DIAGNOSTIC_ONLY`.

## Self-Review

После написания всех задач пройтись по чеклисту:

1. **Spec coverage**: сигнатура `FindEntrySignal(barTime, rule_id_filter)` ✓ (Task 2); `ML_TRADE` строит локальный фильтр ✓ (Task 3); type guard Python ✓ (Task 4); multi-algo CSV ✓ (Task 5); `(magic, rule_id)` reconciliation ✓ (Task 6); smoke ExpTotal=2 ✓ (Task 7); отчёт + sync ✓ (Task 8).
2. **Placeholder scan**: нет `TBD`, `TODO`, «implement later», «similar to Task N»; каждый step содержит реальный код или реальную команду.
3. **Type consistency**: сигнатура `MT5_FindEntrySignal(datetime, string)` одинакова в Tasks 1, 2, 3; `rule_id_filter` локально везде; `rule_id=f"mt5_rule_{Mgc}"` единая конвенция в Tasks 1, 3, 5, 6.
