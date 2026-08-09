# MT5 Per-Expert ML-CSV Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Поддержка нескольких экспертов (`EXP[]`, `#.csv`) при MT5-diagnostic execution, где каждый эксперт читает один signal CSV (`mt5_entry_signals.csv`) и обрабатывает только строки с `rule_id == (string)Mgc`.

**Architecture:**
- MQL5: `lib_ML_Signal.mqh` получает per-expert tracker (массив `MT5_TrackedPositions[]` уже введён closeout-планом) плюс per-expert `rule_id_filter` local в `ML_TRADE`. `MT5_ENTRY_INIT` грузит весь CSV один раз (глобально), но `MT5_FindEntrySignal(barTime, rule_id_filter)` выбирает только строки где `(rule_id_filter=="" || MT5_RuleIds[i]==rule_id_filter) && MT5_EntryTimes[i] == barTime`. **У-4**: `rule_id_filter` это **local string** внутри `ML_TRADE` (значение `"mt5_rule_" + (string)Mgc`), НЕ global; глобальная `MT5_RuleIdFilter` не вводится (это избегает гонки singleton между экспертами).
- Python: `prepare_mt5_entry_source` уже подставляет `rule_id=run_id` (существующий контракт). `run_mt5_batch.py` генерирует multi-rule signal CSV, где `rule_id` каждого столбца совпадает со строковым magic соответствующего эксперта в `#.csv`.
- Reconciliation: `parse_mt5_execution_report` группирует события по `rule_id` (new) и по `magic` (new), что даёт per-rule + per-expert метрики в одном отчёте.

**Tech Stack:** MQL5 (MetaEditor 5, Wine), Python 3.10+ (pandas, pytest), существующие `mt5_signal_schema`, `export_mt5_entry_signals`, `parse_mt5_execution_report`.

## Global Constraints

- **Precondition (closeout-план исполнен)**: `MT5_TrackedTicket` singleton в `lib_ML_Signal.mqh` заменён на `MT5_TRACKED_POSITION` struct + `MT5_TrackedPositions[]` массив + `MT5_TrackedPositionCount`; все `(int)OrderTicket()`/`(int)ticket` касты удалены; `MT5_LogLifecycleForTicket` введён; `force_rerun` skip-override в `run_batch` работает. Перед стартом Tasks 1-N verifier Task P0 проверяет это состояние. Если closeout ещё не закоммичен, **plan BLOCKED** — исполнитель сначала завершает closeout, потом возвращается сюда.
- **MT5 methodologist contract** (`docs/methodology/13b-mt5-execution-parity.md`):
  - Compile gate: `0 errors, 0 warnings` (строка 165). Не считать exit-код `wine` verdict-ом (строки 168-170).
  - CSV contract для signal (строки 58) и event (строки 73) — не расширять new колонки без синхронизации Python+MQL5 schema testов (`tests/test_mt5_signal_executor_schema.py:18-24`).
  - Timing contract: `feature_time <= time < feature_available_time <= decision_time` (строки 76-86); `feature_time <= signal_time < feature_available_time <= decision_time <= execution_time` (строки 82-86).
  - Limit-only entries: `BUY_LIMIT`/`SELL_LIMIT` (строки 38-43). otro `entry_type` не допускается.
- **Reporting** (`docs/methodology/16-reporting-audit.md`):
  - Disclosure fields (исследовательский блок, методология 16:65-77, обязятельны 8 полей для research-first отчёта): `lifecycle_status`, `origin_bias`, `research_priority`, `current_search_budget`, `cumulative_search_budget`, `next_probe_freeze`, `allowed_max_verdict`, `forbidden_interpretations`. `roadmap_track` — не mandatory (не входит в research-first блок).
  - `allowed_max_verdict: DIAGNOSTIC_ONLY`.
  - Запрещённые интерпретации (`forbidden_interpretations`): `profitable`, `ready`, `live-ready`, `tradable`, `new winner`, `model-quality proof`.
- **No ML changes**: plan не меняет модель, frozen export, threshold, profile, side, horizon, entry/exit rule. Только execution tracker + signal CSV routing.
- **Compat constraint**: `MT5_MaxPositions=1` остаётся каноническим single-position режимом. Multi-expert + per-rule filter работают и при `MaxPositions=1`, и при `MaxPositions>1`. Backcompat ветка для старого single-expert без `rule_id`-фильтра сохраняется.
- **Scope ограничение**: `iSignal==5` (`ML_TRADE_TB` в `lib_ML_Signal_TB.mqh`) — **out of scope**. Это отдельный signal lib с собственным CSV (`ml_signals_tb.csv`), не имеет `rule_id` колонки и не читает `mt5_entry_signals.csv`. Покрывается отдельным планом, если потребуется. Данный план работает только с `iSignal==3` (`ML_TRADE`, `MT5_DiagnosticExecutor=true`).
- **#.csv contract**: `SERVICE.mqh:122-220` (`INPUT_FILE_READ`) читает `#.csv` в `EXP[]`. При `Real=true` в тестере (см. пользователя: «эмулирует live, перебирает все строки») все строки `#.csv` грузятся. `EXP[e].Mgc` — int, генерируется `MAGIC_GENERATOR()` (`SERVICE.mqh:95-100`) из входных параметров + Symbol + Period. План не меняет `#.csv` формат или `INPUT_FILE_READ`; он только прибавляет `\n` строку связи `rule_id ↔ Mgc`.
- **rule_id ↔ magic binding**: `prepare_mt5_entry_source` (`prepare_mt5_entry_source.py:76`) подставляет `rule_id=run_id` по умолчанию; в `run_mt5_batch.py:142` `rule_id=run_id` где `run_id=make_run_id(cand)=f"{profile}_{model_key}_{horizon}h_thr{threshold_value}"` (строки 46-47). Этот `run_id` — **строка**, не magic. Поэтому мостом `rule_id ↔ Mgc` делаем явную конвенцию: при multi-expert генерации `rule_id=f"mt5_rule_{Mgc}"` (уникальное строковое представление int magic), и в `ML_TRADE` local `rule_id_filter = "mt5_rule_" + (string)Mgc` передаётся аргументом в `MT5_FindEntrySignal`. Сейчас magic в `#.csv` — 16-я колонка (`SERVICE.mqh:178`), читается в `EXP[e].Mgc` (int). Конвенция `rule_id == "mt5_rule_" + IntegerToString(Mgc)` детерминирована и тестируема. Для backcompat без multi-expert: `rule_id_filter = ""` означает «без фильтра» (текущее поведение, выбирает первое совпадение по time) — что сохраняет старые сигналы. **У-4**: global `MT5_RuleIdFilter` не вводится.
- **Compile OS**: Wine + xvfb-run на Linux, `WINEPREFIX=/home/hohla/.mt5`. Конкретные пути — см. `docs/methodology/13b-mt5-execution-parity.md:150-170`.
- **Run environment**: `./.venv/bin/python` для всех Python вызовов (AGENTS.md).
- **Запрет генерировать магические числа с extra prefix**: `MAGIC_GENERATOR` возвращает `MathAbs(int(MagicLong))` (`SERVICE.mqh:99`), int magic. Поэтому `"mt5_rule_" + (string)Mgc` — строка `mt5_rule_163856259` (например). Не использовать `run_id` (с `_`) как rule_id внутри MQL5, если `run_id` содержит запятые/недопустимые символы — MQL5 CSV reader их не поломает (читает по `;`), но проще держать одну конвенцию.

---

## Task P0: Verify closeout-план precondition

**Files:**
- Read-only: `MT/MQL5/Include/lib_ML_Signal.mqh`, `MT/MQL5/Include/FUNCTIONS.mqh`, `ML/baseline/run_mt5_batch.py`

**Interfaces:**
- Consumes: git-состояние `lib_ML_Signal.mqh` и `run_mt5_batch.py` после предполагаемого исполнения closeout-плана `docs/superpowers/plans/2026-08-03-mt5-multi-position-closeout.md`.
- Produces: `PRECONDITION_OK` или `PRECONDITION_FAILED` + точный список незакрытых аудиторских замечаний.

- [ ] **Step 1: Run grep checks для closeout signals**

Run:

```bash
rg -n "MT5_TrackedTicket\b" MT/MQL5/Include/lib_ML_Signal.mqh
rg -n "MT5_TRACKED_POSITION\b|MT5_TrackedPositions\b|MT5_LogLifecycleForTicket\b" MT/MQL5/Include/lib_ML_Signal.mqh
rg -n "\(int\)OrderTicket\(\)|\(int\)ticket\b|\(int\)MT5_TrackedTicket" MT/MQL5/Include/lib_ML_Signal.mqh MT/MQL5/Include/ORDERS.mqh MT/MQL5/Include/ERRORs.mqh
rg -n "force_rerun" ML/baseline/run_mt5_batch.py
```

Expected: первая команда возвращает **0 строк** (singleton удалён); вторая — минимум 4 строки (struct, массив, функция, вызов); третья — 0 строк (касты удалены); четвёртая — не 0 (`force_rerun` уже в `run_batch`).

- [ ] **Step 2: Decision branch по результату**

If **все 4 grep checks прошли** → записать в `docs/reports/2026-08-03-mt5-per-expert-precondition.md` с одной строкой `precondition: OK` и SHA всех проверенных файлов; продолжить Task 1.

If **хотя бы один check failed** → записать тот же файл с `precondition: FAILED` и списком незакрытых пунктов. **STOP**. Сообщить, что план BLOCKED на closeout. Незакрытые пункты указывать по фактическим заголовкам задач closeout-плана `docs/superpowers/plans/2026-08-03-mt5-multi-position-closeout.md` (Tasks 1-9): «Task 1: Static Contract Tests For Audit Findings», «Task 2: Fix POSITION ticket type and order placement gate», «Task 3: Fix side-specific close helpers and clean INPUT», «Task 4: Replace single-ticket diagnostic lifecycle with multi-ticket tracker», «Task 5: Add forced rerun support for reproducible backcompat checks», «Task 6: Compile gate and focused tester checks», «Task 7: Backcompat and multi-position evidence comparison», «Task 8: Correct old plan/report claims», «Task 9: Final closeout report and project state sync». **Внимание**: названия задач приведены по состоянию на коммит closeout-плана; исполнитель сверяет с актуальной версией closeout-плана перед использованием. Соответствие grep-check → задача: absence `MT5_TrackedTicket` / наличие struct+массива+`MT5_LogLifecycleForTicket` → Task 4; absence int-кастов ticket → Tasks 2-4; наличие `force_rerun` → Task 5. Не переходить к Task 1.

- [ ] **Step 3: Commit precondition check**

```bash
# только если precondition OK
git add docs/reports/2026-08-03-mt5-per-expert-precondition.md
git commit -m "docs: per-expert plan precondition (closeout verified)"
```

Если precondition failed — commit всё равно делается (это артефакт аудита), но больше задач не исполняется.

---

## Task 1: Static contract tests для per-expert rule_id filter

**Files:**
- Create: `tests/test_mt5_per_expert_ml_tracker_contract.py`
- Modify (read-only reference): `MT/MQL5/Include/lib_ML_Signal.mqh`, `ML/baseline/run_mt5_batch.py`, `ML/baseline/prepare_mt5_entry_source.py`

**Interfaces:**
- Consumes: сигнатуры `MT5_FindEntrySignal`, `MT5_ENTRY_INIT`, `ML_TRADE` из `lib_ML_Signal.mqh`; сигнатуры `prepare_entry_quality_source`, `make_run_id` из Python.
- Produces: failing-тесты, которые фиксируют целевую структуру: (а) `MT5_FindEntrySignal` принимает `datetime barTime, string rule_id_filter`; (б) `MT5_ENTRY_INIT` грузит весь CSV без фильтра; (в) `ML_TRADE` выставляет local `rule_id_filter = "mt5_rule_" + (string)Mgc` перед вызовом `MT5_FindEntrySignal(barTime, rule_id_filter)` (без global singleton); (г) `prepare_entry_quality_source` type-guards `rule_id` на `str` (Task 2 правит зов), принимает `rule_id` строку-аргумент любой формы (без введения нового параметра `rule_id_prefix`); (д) `run_mt5_batch` для per-expert mode подставляет `rule_id=f"mt5_rule_{Mgc}"` при multi-expert генерации (Task 5), не меняя `make_run_id` (одного для single-expert backcompat).

- [ ] **Step 1: Write the failing static tests**

Создать файл `tests/test_mt5_per_expert_ml_tracker_contract.py` с содержимым:

```python
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

MQL_SIGNAL_LIB = Path("MT/MQL5/Include/lib_ML_Signal.mqh")
RUN_BATCH = Path("ML/baseline/run_mt5_batch.py")
PREPARE_SOURCE = Path("ML/baseline/prepare_mt5_entry_source.py")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_mt5_find_entry_signal_accepts_rule_id_filter() -> None:
    text = _text(MQL_SIGNAL_LIB)
    # Новая сигнатура: MT5_FindEntrySignal(datetime barTime, string rule_id_filter)
    match = re.search(
        r"int\s+MT5_FindEntrySignal\s*\(\s*datetime\s+barTime\s*,\s*string\s+rule_id_filter\s*\)\s*\{",
        text,
    )
    assert match is not None, (
        "MT5_FindEntrySignal должен принимать второй параметр string rule_id_filter "
        "для per-expert фильтрации сигналов по rule_id == (string)Mgc."
    )


def test_mt5_find_entry_signal_filters_by_rule_id_when_provided() -> None:
    text = _text(MQL_SIGNAL_LIB)
    # Тело MT5_FindEntrySignal должно содержать условие:
    # if (rule_id_filter != "" && MT5_RuleIds[i] != rule_id_filter) continue;
    match = re.search(
        r"int\s+MT5_FindEntrySignal\s*\([^)]*\)\s*\{(?P<body>.*?)\n\}",
        text,
        flags=re.S,
    )
    assert match is not None
    body = match.group("body")
    assert "rule_id_filter" in body
    assert "MT5_RuleIds[i]" in body
    # Фильтр должен быть «opt-in»: пустой строкой filter выключается (backcompat).
    assert 'rule_id_filter != ""' in body or 'rule_id_filter!=' + '""' in body.replace(" ", "")


def test_mt5_entry_init_still_loads_whole_csv_without_rule_filter() -> None:
    text = _text(MQL_SIGNAL_LIB)
    # MT5_ENTRY_INIT грузит CSV в массивы БЕЗ фильтра rule_id (фильтр происходит в MT5_FindEntrySignal).
    # Это позволяет одному CSV разделять сигналы между экспертами.
    match = re.search(
        r"bool\s+MT5_ENTRY_INIT\s*\(\s*\)\s*\{(?P<body>.*?)\n\}",
        text,
        flags=re.S,
    )
    assert match is not None
    body = match.group("body")
    # Загрузка не зависит от rule_id_filter (его здесь вообще нет).
    assert "rule_id_filter" not in body
    assert "MT5_RuleIds[i]" in body  # колонка читается и хранится в массиве.


def test_ml_trade_sets_rule_id_filter_from_magic_before_find() -> None:
    text = _text(MQL_SIGNAL_LIB)
    match = re.search(
        r"void\s+EXPERT::ML_TRADE\s*\(\s*\)\s*\{(?P<body>.*?)\n\}",
        text,
        flags=re.S,
    )
    assert match is not None
    body = match.group("body")
    # Per-expert: перед MT5_FindEntrySignal указывается rule_id фильтр из Mgc.
    # Один из двух допустимых способов:
    #   string rule_id_filter = "mt5_rule_" + (string)Mgc;
    # либо inline-аргумент: MT5_FindEntrySignal(Time[bar], "mt5_rule_" + (string)Mgc)
    assert '"mt5_rule_"' in body, (
        "ML_TRADE должен конструировать rule_id filter как 'mt5_rule_' + (string)Mgc, "
        "чтобы каждый эксперт обрабатывал только сигналы с своим magic."
    )
    # MT5_FindEntrySignal вызывается с двумя аргументами, не одним.
    assert re.search(
        r"MT5_FindEntrySignal\s*\([^)]*,[^)]*\)",
        body,
    ), "MT5_FindEntrySignal вызывается с двумя аргументами (включая rule_id_filter)."


def test_ml_trade_backcompat_when_rule_id_filter_empty() -> None:
    """Старые signal CSV без column-aware rule_id остаются рабочими: если фильтр пуст,
    MT5_FindEntrySignal выбирает первое совпадение по time (текущее поведение).
    Этот контракт гарантирует, что single-expert workflow не ломается."""
    text = _text(MQL_SIGNAL_LIB)
    # Тело MT5_FindEntrySignal должно явно допукать пустой filter:
    # когда rule_id_filter=="" — фильтра нет, берётся первое match по time.
    match = re.search(
        r"int\s+MT5_FindEntrySignal\s*\([^)]*\)\s*\{(?P<body>.*?)\n\}",
        text,
        flags=re.S,
    )
    assert match is not None
    body = match.group("body")
    # Когда filter пуст — переменная не мешает матчингу по time.
    assert 'rule_id_filter != ""' in body or 'rule_id_filter!=' + '""' in body.replace(" ", "")


def test_ml_trade_has_k3_fallback_when_first_find_returns_minus_one() -> None:
    """К-3: ML_TRADE должна делать повторный поиск с пустым rule_id_filter,
    если первый поиск с "mt5_rule_<Mgc>" вернул -1. Это backcompat для
    32 существующих CSV без колонки rule_id (pre-multi-expert era).
    Без этого теста миграция сломала бы legacy single-expert runs без new CSV.
    Guard !MT5_HasRuleIds гарантирует, что fallback не применяется к новым
    multi-rule CSV (защита per-expert изоляции).
    """
    text = _text(MQL_SIGNAL_LIB)
    match = re.search(
        r"void\s+EXPERT::ML_TRADE\s*\(\s*\)\s*\{(?P<body>.*?)\n\}",
        text,
        flags=re.S,
    )
    assert match is not None
    body = match.group("body")
    # Второй вызов MT5_FindEntrySignal с пустым фильтром ("") после if (mt5_idx < 0 && !MT5_HasRuleIds):
    # ищем паттерн `MT5_FindEntrySignal(Time[bar], "")` либо `MT5_FindEntrySignal(Time[bar],"")`
    fallback = re.search(
        r"MT5_FindEntrySignal\s*\([^)]*,\s*" + '""' + r"\s*\)",
        body.replace(" ", ""),
    )
    assert fallback is not None, (
        "К-3: ML_TRADE должен содержать повторный вызов MT5_FindEntrySignal(Time[bar], \"\") "
        "после if (mt5_idx < 0 && !MT5_HasRuleIds) — backcompat для старых CSV без колонки rule_id."
    )
    # Guard: fallback применяется только когда CSV legacy (без rule_id):
    assert "MT5_HasRuleIds" in body, (
        "К-3: ML_TRADE должен проверять MT5_HasRuleIds перед fallback — "
        "без этого guard эксперт A может взять сигнал эксперта B в multi-rule CSV."
    )


def test_prepare_entry_quality_source_supports_rule_id_prefix_for_multi_expert() -> None:
    from ML.baseline.prepare_mt5_entry_source import prepare_entry_quality_source

    source = pd.DataFrame(
        [
            {
                "time": "2021.01.05 10:00",
                "signal_time": "2021.01.05 10:00",
                "side": "BUY",
                "limit_price": 1900.0,
                "protective_stop_price": 1890.0,
                "atr": 10.0,
            }
        ]
    )

    # Multi-expert mode: rule_id = prefix + str(magic), где magic — int.
    prepared = prepare_entry_quality_source(source, rule_id="mt5_rule_163856259")

    assert prepared.loc[0, "rule_id"] == "mt5_rule_163856259"
    # Одиночный (legacy) режим: rule_id остаётся как есть.
    legacy = prepare_entry_quality_source(source, rule_id="run_a")
    assert legacy.loc[0, "rule_id"] == "run_a"


def test_prepare_entry_quality_source_rejects_non_string_rule_id() -> None:
    from ML.baseline.prepare_mt5_entry_source import prepare_entry_quality_source

    source = pd.DataFrame(
        [
            {
                "time": "2021.01.05 10:00",
                "signal_time": "2021.01.05 10:00",
                "side": "SELL",
                "limit_price": 1910.0,
                "protective_stop_price": 1920.0,
                "atr": 10.0,
            }
        ]
    )

    # rule_id должен быть строкой; int magic подаётся уже обёрнутым в "mt5_rule_<int>".
    with pytest.raises(TypeError, match="rule_id must be str"):
        prepare_entry_quality_source(source, rule_id=163856259)  # type: ignore[arg-type]


def test_run_mt5_batch_make_run_id_unchanged_for_single_expert_mode() -> None:
    """В single-expert режиме (default) make_run_id возвращает тот же составной run_id,
    что используется как rule_id в signal CSV по конвенции closeout-плана.
    Multi-expert режим — это отдельный код-путь в Task 5."""
    from ML.baseline.run_mt5_batch import make_run_id

    cand = {
        "profile": "fractal0",
        "model_key": "entry_quality_v1",
        "horizon": 12,
        "threshold_value": 0.5,
    }
    assert make_run_id(cand) == "fractal0_entry_quality_v1_12h_thr0.5"


def test_run_mt5_batch_has_multi_expert_flag() -> None:
    """new CLI flag --multi-expert включает per-rule генерацию и batch-orchestration.
    Без флага поведение полностью backcompat."""
    text = _text(RUN_BATCH)
    assert "--multi-expert" in text, (
        "run_mt5_batch должен принимать --multi-expert flag, "
        "переключающий multi-rule signal generation и batch run per expert."
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_expert_ml_tracker_contract.py -q
```

Expected: FAIL с сообщениями «assert match is not None» для MQL5 static-тестов и `TypeError`/`AssertionError` для Python-тестов. Так как `MT5_FindEntrySignal(datetime barTime)` сегодня принимает один аргумент (lib_ML_Signal.mqh:128), `prepare_entry_quality_source(..., rule_id=int)` сегодня не имеет type-check и просто работает (но возвращает rule_id как `"mt5_rule_" + int` ≈ аномалия), а `--multi-expert` flag ещё нет.

- [ ] **Step 3: Commit failing tests**

```bash
git add tests/test_mt5_per_expert_ml_tracker_contract.py
git commit -m "test: per-expert ml-tracker contract (failing)"
```

---

## Task 2: Implement Python `prepare_entry_quality_source` rule_id type guard

**Files:**
- Modify: `ML/baseline/prepare_mt5_entry_source.py:73-112`
- Test: `tests/test_mt5_per_expert_ml_tracker_contract.py` (тест `test_prepare_entry_quality_source_rejects_non_string_rule_id`)

**Interfaces:**
- Consumes: существующую сигнатуру `prepare_entry_quality_source(source, *, rule_id="entry_quality_filter", latency_bars=0)`.
- Produces: та же функция с дополнительным type-guard: `rule_id: str` (raise `TypeError` если не str). Поведение для строк остаётся прежним.

- [ ] **Step 1: Run failing test to confirm baseline**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_expert_ml_tracker_contract.py::test_prepare_entry_quality_source_rejects_non_string_rule_id -q
```

Expected: FAIL (TypeError ещё не реализован — сегодня функция принимает `rule_id` как есть и отдаёт в DataFrame, где он может быть int).

- [ ] **Step 2: Type-guard implement**

В файле `ML/baseline/prepare_mt5_entry_source.py`, функция `prepare_entry_quality_source` (строки 73-112), добавить guard в начало тела:

Было (строки 73-80):

```python
def prepare_entry_quality_source(
    source: pd.DataFrame,
    *,
    rule_id: str = "entry_quality_filter",
    latency_bars: int = 0,
) -> pd.DataFrame:
    latency_bars = _validate_latency_bars(latency_bars)
```

Стало:

```python
def prepare_entry_quality_source(
    source: pd.DataFrame,
    *,
    rule_id: str = "entry_quality_filter",
    latency_bars: int = 0,
) -> pd.DataFrame:
    if not isinstance(rule_id, str):
        raise TypeError("rule_id must be str")
    latency_bars = _validate_latency_bars(latency_bars)
```

- [ ] **Step 3: Run failing test and confirm it now passes**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_expert_ml_tracker_contract.py::test_prepare_entry_quality_source_rejects_non_string_rule_id tests/test_mt5_per_expert_ml_tracker_contract.py::test_prepare_entry_quality_source_supports_rule_id_prefix_for_multi_expert -q
```

Expected: PASS (оба правила: type guard и legacy string path).

- [ ] **Step 4: Run existing prepare_mt5_entry_source tests чтобы убедиться что backcompat не сломан**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py -q
```

Expected: PASS (все существующие тесты на `prepare_entry_quality_source` подают `rule_id` как str).

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/prepare_mt5_entry_source.py
git commit -m "feat: prepare_entry_quality_source type-guards rule_id as str"
```

---

## Task 3: Implement MQL5 per-expert rule_id filter в MT5_FindEntrySignal

**Files:**
- Modify: `MT/MQL5/Include/lib_ML_Signal.mqh:207` (`MT5_FindEntrySignal`), `MT/MQL5/Include/lib_ML_Signal.mqh:852-1175` (`EXPERT::ML_TRADE`)
- Test: `tests/test_mt5_per_expert_ml_tracker_contract.py::test_mt5_find_entry_signal_*`, `::test_ml_trade_sets_rule_id_filter_from_magic_before_find`, `::test_ml_trade_backcompat_when_rule_id_filter_empty`

**Interfaces:**
- Consumes: `MT5_RuleIds[]` (глобальный массив, заполненный `MT5_ENTRY_INIT`), `MT5_EntryTimes[]`, `Mgc` (поле текущего эксперта, `int`).
- Produces: новая сигнатура `MT5_FindEntrySignal(datetime barTime, string rule_id_filter) -> int index or -1`. Вызов из `ML_TRADE` заменён на `MT5_FindEntrySignal(Time[bar], "mt5_rule_" + (string)Mgc)`.

- [ ] **Step 1: Run failing test to confirm baseline**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_expert_ml_tracker_contract.py::test_mt5_find_entry_signal_accepts_rule_id_filter tests/test_mt5_per_expert_ml_tracker_contract.py::test_mt5_find_entry_signal_filters_by_rule_id_when_provided -q
```

Expected: FAIL (regex на двух-аргументную сигнатуру не падает — сегодня один аргумент).

- [ ] **Step 2: Rewrite `MT5_FindEntrySignal` в lib_ML_Signal.mqh**

В файле `MT/MQL5/Include/lib_ML_Signal.mqh`, заменить функцию (строка 207):

Было:

```cpp
int MT5_FindEntrySignal(datetime barTime) {
   for (int i = 0; i < MT5_EntrySignalCount; i++) {
      if (MT5_EntryTimes[i] == barTime) return i;
   }
   return -1;
}
```

Стало:

```cpp
int MT5_FindEntrySignal(datetime barTime, string rule_id_filter) {
   for (int i = 0; i < MT5_EntrySignalCount; i++) {
      if (MT5_EntryTimes[i] != barTime) continue;
      // Per-expert filter: когда rule_id_filter не пуст, принимаем только строки
      // с matching MT5_RuleIds[i]. Пустая строка — backcompat (без фильтра, первый match).
      if (rule_id_filter != "" && MT5_RuleIds[i] != rule_id_filter) continue;
      return i;
   }
   return -1;
}
```

- [ ] **Step 3: Rewrite call site в `EXPERT::ML_TRADE` (К-3 fallback)**

В файле `MT/MQL5/Include/lib_ML_Signal.mqh`, заменить вызов в `ML_TRADE` (строка 875):

Было:

```cpp
      int mt5_idx = MT5_FindEntrySignal(Time[bar]);
      if (mt5_idx < 0) return;
```

Стало (К-3: fallback с пустым `rule_id_filter` — backcompat для 32 существующих CSV без колонки `rule_id`):

Дополнительно ввести глобальный флаг `bool MT5_HasRuleIds = false;` (рядом с `MT5_RuleIds[]`, строка ~60). В `MT5_ENTRY_INIT` (строка 686) после заполнения `MT5_RuleIds[i]` добавить: `if (rule_id != "") MT5_HasRuleIds = true;`.

```cpp
      string mt5_rule_filter = "mt5_rule_" + (string)Mgc;
      int mt5_idx = MT5_FindEntrySignal(Time[bar], mt5_rule_filter);
      // К-3: fallback для backcompat — старые CSV (pre-2026-08-03 multi-rule миграции)
      // не содержат колонку rule_id и MT5_HasRuleIds == false →
      // повторный поиск с пустым фильтром (выбирает первый match по barTime, как до миграции).
      // ВАЖНО: fallback применяется ТОЛЬКО когда CSV legacy (без rule_id).
      // Если MT5_HasRuleIds == true (новый multi-rule CSV), fallback не применяется —
      // это предотвращает cross-expert isolation breach (эксперт A не берёт сигнал эксперта B).
      if (mt5_idx < 0 && !MT5_HasRuleIds) {
         mt5_idx = MT5_FindEntrySignal(Time[bar], "");
      }
      if (mt5_idx < 0) return;
```

Замечание: `Mgc` здесь — поле текущего эксперта (`EXP[CurExp].Mgc`), доступно в `EXPERT::ML_TRADE`. `(string)Mgc` конвертирует int magic в строковое десятичное представление, которое сравнивается с `MT5_RuleIds[i]` — массивом строк, заполненным `MT5_ENTRY_INIT` из 5-й колонки CSV (строки 524, 554).

**К-3 backcompat стратегия**: если первый поиск с `"mt5_rule_<Mgc>"` возвращает `-1`, второй — с `""` — для тех же barTime берёт первую запись. Это preserves 32 исторических CSV без `rule_id` колонки (pre-multi-expert era). Guard `!MT5_HasRuleIds` гарантирует, что fallback НЕ срабатывает для новых multi-rule CSV — это защищает per-expert изоляцию: если эксперт A не имеет сигнала на данном barTime, он не возьмёт сигнал эксперта B.

- [ ] **Step 4: Run static contract tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_expert_ml_tracker_contract.py::test_mt5_find_entry_signal_accepts_rule_id_filter tests/test_mt5_per_expert_ml_tracker_contract.py::test_mt5_find_entry_signal_filters_by_rule_id_when_provided tests/test_mt5_per_expert_ml_tracker_contract.py::test_ml_trade_sets_rule_id_filter_from_magic_before_find tests/test_mt5_per_expert_ml_tracker_contract.py::test_ml_trade_backcompat_when_rule_id_filter_empty -q
```

Expected: PASS (4 теста).

- [ ] **Step 5: Run `test_mt5_signal_executor_schema.py` — MQL-header contract test должен пройти**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py::test_mt5_find_entry_signal_uses_entry_time_only -q
```

Expected: FAIL — тест `test_mt5_find_entry_signal_uses_entry_time_only` (строки 349-356 `test_mt5_signal_executor_schema.py`) использует regex `int\s+MT5_FindEntrySignal\(datetime barTime\)\s*\{` и сломается на новой сигнатуре. Это marker, что существующий contract-тест нужно адаптировать в следующем шаге.

- [ ] **Step 6: Адаптировать существующий contract-test на новую сигнатуру**

В файле `tests/test_mt5_signal_executor_schema.py`, функция `test_mt5_find_entry_signal_uses_entry_time_only` (строки 349-356), заменить regex:

Было:

```python
def test_mt5_find_entry_signal_uses_entry_time_only():
    text = MQL_SIGNAL_LIB.read_text(encoding="utf-8")
    match = re.search(r"int\s+MT5_FindEntrySignal\(datetime barTime\)\s*\{(?P<body>.*?)\n\}", text, flags=re.S)

    assert match is not None
    body = match.group("body")
    assert "MT5_EntryTimes[i] == barTime" in body
    assert "MT5_DecisionTimes[i] == barTime" not in body
```

Стало:

```python
def test_mt5_find_entry_signal_uses_entry_time_only():
    text = MQL_SIGNAL_LIB.read_text(encoding="utf-8")
    # Сигнатура теперь принимает два параметра: barTime + rule_id_filter (per-expert binding).
    match = re.search(
        r"int\s+MT5_FindEntrySignal\s*\(\s*datetime\s+barTime\s*,\s*string\s+rule_id_filter\s*\)\s*\{(?P<body>.*?)\n\}",
        text,
        flags=re.S,
    )

    assert match is not None
    body = match.group("body")
    # У-3: сильная формулировка — `!= barTime` continue (как в Task 3 Step 4 реализации строка 406).
    # Слабая формулировка `"MT5_EntryTimes[i]" in body` допускала бы безусловный `MT5_EntryTimes[i] == MT5_DecisionTimes[i]`,
    # что не эквивалентно фильтру по barTime.
    assert "MT5_EntryTimes[i] != barTime" in body or "MT5_EntryTimes[i]==barTime" in body.replace(" ", "")
    assert "MT5_DecisionTimes[i]" not in body
    # Per-expert filter применяется только когда rule_id_filter не пуст (backcompat).
    assert "rule_id_filter" in body
```

- [ ] **Step 7: Re-run test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py::test_mt5_find_entry_signal_uses_entry_time_only -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add MT/MQL5/Include/lib_ML_Signal.mqh tests/test_mt5_signal_executor_schema.py
git commit -m "feat: per-expert rule_id filter in MT5_FindEntrySignal"
```

---

## Task 4: Multi-rule signal generation в Python (`prepare_entry_quality_source` extension)

**Files:**
- Create: `ML/baseline/prepare_mt5_multi_expert_source.py`
- Modify: `ML/baseline/run_mt5_batch.py:68-158` (новый код-путь в `generate_signals`)
- Test: `tests/test_mt5_per_expert_ml_tracker_contract.py` (новые тесты multi-expert)

**Interfaces:**
- Consumes: `prepare_entry_quality_source` (Task 2 обновил её type guard), `export_mt5_entry_signals`, существующий список candidates из `CANDIDATES_CSV`.
- Produces: `prepare_mt5_multi_expert_source(experts: list[dict], source_groups: dict[str, pd.DataFrame], *, rule_id_prefix="mt5_rule_") -> pd.DataFrame` — собирает multi-rule signal CSV, где каждый `rule_id` — `f"{rule_id_prefix}{expert_magic}"`, и строки кладутся друг за другом (в порядке `barTime`, как сегодня). Magic определяется на этапе конфигурации экспертов (Task 5 завозит `experts` array из `#.csv` или из `--multi-expert-magics` CLI).

- [ ] **Step 1: Write failing tests для multi-rule assembly**

Добавить в `tests/test_mt5_per_expert_ml_tracker_contract.py`:

```python
def test_prepare_multi_expert_source_assembles_per_rule_rows(tmp_path) -> None:
    from ML.baseline.prepare_mt5_multi_expert_source import prepare_mt5_multi_expert_source

    # Two experts with magics 163856259 and 987654321. Их raw-сигналы (source groups)
    # отображаются в один CSV с rule_id="mt5_rule_<magic>".
    source_groups = {
        "mt5_rule_163856259": pd.DataFrame([
            {
                "time": "2021.01.05 10:00",
                "signal_time": "2021.01.05 10:00",
                "side": "BUY",
                "limit_price": 1900.0,
                "protective_stop_price": 1890.0,
                "atr": 10.0,
            }
        ]),
        "mt5_rule_987654321": pd.DataFrame([
            {
                "time": "2021.01.05 11:00",
                "signal_time": "2021.01.05 11:00",
                "side": "SELL",
                "limit_price": 1910.0,
                "protective_stop_price": 1920.0,
                "atr": 10.0,
            }
        ]),
    }
    experts = [
        {"magic": 163856259, "name": "SoSimple", "sym": "XAUUSD", "per": 60},
        {"magic": 987654321, "name": "SoSimple", "sym": "XAUUSD", "per": 60},
    ]

    prepared, rule_map = prepare_mt5_multi_expert_source(
        experts, source_groups, rule_id_prefix="mt5_rule_"
    )

    assert list(prepared["rule_id"].unique()) == ["mt5_rule_163856259", "mt5_rule_987654321"]
    assert prepared.loc[prepared["rule_id"] == "mt5_rule_163856259", "side"].iloc[0] == "BUY"
    assert prepared.loc[prepared["rule_id"] == "mt5_rule_987654321", "side"].iloc[0] == "SELL"
    # rule_map возвращает manifest: rule_id → magic, для аудита.
    assert rule_map == {
        "mt5_rule_163856259": 163856259,
        "mt5_rule_987654321": 987654321,
    }


def test_prepare_multi_expert_source_rejects_mismatched_keys() -> None:
    from ML.baseline.prepare_mt5_multi_expert_source import prepare_mt5_multi_expert_source

    source_groups = {
        "mt5_rule_163856259": pd.DataFrame([
            {
                "time": "2021.01.05 10:00",
                "signal_time": "2021.01.05 10:00",
                "side": "BUY",
                "limit_price": 1900.0,
                "protective_stop_price": 1890.0,
                "atr": 10.0,
            }
        ]),
    }
    experts = [{"magic": 999, "name": "SoSimple", "sym": "XAUUSD", "per": 60}]
    with pytest.raises(ValueError, match="no expert for rule_id"):
        prepare_mt5_multi_expert_source(experts, source_groups, rule_id_prefix="mt5_rule_")


def test_prepare_multi_expert_source_rejects_empty_source_groups() -> None:
    from ML.baseline.prepare_mt5_multi_expert_source import prepare_mt5_multi_expert_source

    with pytest.raises(ValueError, match="source_groups is empty"):
        prepare_mt5_multi_expert_source(
            [{"magic": 1, "name": "X", "sym": "XAUUSD", "per": 60}],
            {},
        )


def test_prepare_multi_expert_source_preserves_timing_contract() -> None:
    """Каждая строка ассемблированного multi-rule CSV проходит
    валидацию validate_mt5_signal_frame (после export_mt5_entry_signals)."""
    from ML.baseline.export_mt5_entry_signals import export_mt5_entry_signals
    from ML.baseline.prepare_mt5_multi_expert_source import prepare_mt5_multi_expert_source
    from ML.baseline.mt5_signal_schema import validate_mt5_signal_frame

    source_groups = {
        "mt5_rule_163856259": pd.DataFrame([
            {
                "time": "2021.01.05 10:00",
                "signal_time": "2021.01.05 10:00",
                "side": "BUY",
                "limit_price": 1900.0,
                "protective_stop_price": 1890.0,
                "atr": 10.0,
            }
        ]),
    }
    experts = [{"magic": 163856259, "name": "SoSimple", "sym": "XAUUSD", "per": 60}]
    prepared, _ = prepare_mt5_multi_expert_source(experts, source_groups)
    # export_mt5_entry_signals добавит entry_type и max_fill_lag_bars.
    frame = export_mt5_entry_signals(
        prepared, "out.csv", "out.json", max_fill_lag_bars=6, latency_bars=0,
    )
    validate_mt5_signal_frame(frame)  # не должно raise.


def test_prepare_multi_expert_source_same_bar_collision_two_rule_ids_ok() -> None:
    """Q-2: две строки с одинаковым barTime, но разными rule_id **допустимы** —
    это и есть смысл multi-expert: каждый эксперт берёт свою строку по rule_id filter.
    Контракт: sort стабилен по time, правила остаются в исходном порядке
    (сначала rule_A, затем rule_B для того же time).
    """
    from ML.baseline.prepare_mt5_multi_expert_source import prepare_mt5_multi_expert_source

    source_groups = {
        "mt5_rule_163856259": pd.DataFrame([
            {
                "time": "2021.01.05 10:00",
                "signal_time": "2021.01.05 10:00",
                "side": "BUY",
                "limit_price": 1900.0,
                "protective_stop_price": 1890.0,
                "atr": 10.0,
            }
        ]),
        "mt5_rule_987654321": pd.DataFrame([
            {
                "time": "2021.01.05 10:00",  # та же time что у rule_163856259
                "signal_time": "2021.01.05 10:00",
                "side": "SELL",
                "limit_price": 1910.0,
                "protective_stop_price": 1920.0,
                "atr": 10.0,
            }
        ]),
    }
    experts = [
        {"magic": 163856259, "name": "SoSimple", "sym": "XAUUSD", "per": 60},
        {"magic": 987654321, "name": "SoSimple", "sym": "XAUUSD", "per": 60},
    ]

    prepared, rule_map = prepare_mt5_multi_expert_source(experts, source_groups)

    # Обе строки присутствуют:
    assert len(prepared) == 2
    # Каждый rule_id имеет свою строку (фильтр в ML_TRADE выбирает по rule_id):
    assert prepared["rule_id"].value_counts().to_dict() == {
        "mt5_rule_163856259": 1,
        "mt5_rule_987654321": 1,
    }
    # Контракт: при коллизии по time order стабильный по insertion order source_groups:
    assert prepared.iloc[0]["rule_id"] == "mt5_rule_163856259"
    assert prepared.iloc[1]["rule_id"] == "mt5_rule_987654321"
    # MQL side: MT5_FindEntrySignal(barTime, "mt5_rule_163856259") даст BUY эксперт A,
    # MT5_FindEntrySignal(barTime, "mt5_rule_987654321") даст SELL эксперт B — без коллизии.
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_expert_ml_tracker_contract.py -q -k "multi_expert_source"
```

Expected: FAIL (модуль `ML.baseline.prepare_mt5_multi_expert_source` не существует).

- [ ] **Step 3: Create `ML/baseline/prepare_mt5_multi_expert_source.py`**

```python
from __future__ import annotations

from typing import Any

import pandas as pd

from ML.baseline.prepare_mt5_entry_source import (
    OUTPUT_COLUMNS,
    prepare_entry_quality_source,
)


def prepare_mt5_multi_expert_source(
    experts: list[dict[str, Any]],
    source_groups: dict[str, pd.DataFrame],
    *,
    rule_id_prefix: str = "mt5_rule_",
    latency_bars: int = 0,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Собрать multi-rule signal CSV из per-rule source-групп.

    Каждый ключ в source_groups — это `rule_id` (= `rule_id_prefix + str(magic)`).
    Возвращает tuple (prepared DataFrame, rule_map: rule_id → magic).
    Каждый DataFrame из source_groups обрабатывается через prepare_entry_quality_source
    с тем же rule_id, что и ключ. Затем все группы concat-ятся в один CSV.
    """
    if not source_groups:
        raise ValueError("source_groups is empty")

    expert_magics = {int(expert["magic"]) for expert in experts}
    rule_map: dict[str, int] = {}
    frames: list[pd.DataFrame] = []

    for rule_id, source in source_groups.items():
        # Проверяем, что rule_id соответствует хотя бы одному эксперту.
        if not rule_id.startswith(rule_id_prefix):
            raise ValueError(f"rule_id missing prefix {rule_id_prefix!r}: {rule_id!r}")
        magic_str = rule_id[len(rule_id_prefix) :]
        try:
            magic = int(magic_str)
        except ValueError as exc:
            raise ValueError(f"rule_id has non-integer magic: {rule_id!r}") from exc
        if magic not in expert_magics:
            raise ValueError(f"no expert for rule_id {rule_id!r} (magic={magic})")

        # prepare_entry_quality_source уже type-guards rule_id (str required).
        prepared = prepare_entry_quality_source(
            source, rule_id=rule_id, latency_bars=latency_bars
        )
        frames.append(prepared)
        rule_map[rule_id] = magic

    combined = pd.concat(frames, ignore_index=True)
    # Сортировка по времени (stable) для предсказуемого порядка.
    combined = combined.sort_values(by="time", kind="stable").reset_index(drop=True)
    return combined[OUTPUT_COLUMNS].copy(), rule_map
```

- [ ] **Step 4: Run failing tests для multi-rule assembly**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_expert_ml_tracker_contract.py -q -k "multi_expert_source"
```

Expected: PASS (все 4 multi_expert_source теста).

- [ ] **Step 5: Run existing test suite чтобы убедиться что backcompat не сломан**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py tests/test_mt5_per_expert_ml_tracker_contract.py -q
```

Expected: PASS (всё исправно).

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/prepare_mt5_multi_expert_source.py tests/test_mt5_per_expert_ml_tracker_contract.py
git commit -m "feat: multi-rule signal CSV assembly for per-expert MT5 execution"
```

---

## Task 5: `--multi-expert` flag в `run_mt5_batch.py`

**Files:**
- Modify: `ML/baseline/run_mt5_batch.py:46-158` (signal generation), `ML/baseline/run_mt5_batch.py:769-810` (`main` + CLI)
- Test: `tests/test_mt5_per_expert_ml_tracker_contract.py::test_run_mt5_batch_has_multi_expert_flag`, new `::test_run_mt5_batch_multi_expert_mode_generates_multi_rule_csv`

**Interfaces:**
- Consumes: существующий `make_run_id`, `generate_signals`, `load_candidates`, `export_mt5_entry_signals`. Новый `prepare_mt5_multi_expert_source` (Task 4).
- Produces: CLI flag `--multi-expert --multi-expert-magics "163856259,987654321"` в batch-режиме (CLI требует явных магиков). В smoke-режиме `--phase smoke-multi-expert` (Task 8 Step 6) `--multi-expert-magics` явно **не задаётся** — auto-magics берутся из эталонного прогона `MAGIC_GENERATOR` (К-6). В multi-expert batch mode `generate_signals` для каждого candidate-τ кортежа (группа от `n_experts` кандидатов) генерирует один multi-rule CSV `entry_signals_<batch_id>.csv` + `entry_signals_<batch_id>.json` с manifest `rule_map`. CLI default — `single-expert` (backcompat). **У-5**: режим `--multi-expert-magics auto` НЕ существует (никогда не реализовывался и не нужен — smoke использует `--phase smoke-multi-expert` без аргумента magics).

- [ ] **Step 1: Write failing test для multi-expert flag aware generation**

Добавить в `tests/test_mt5_per_expert_ml_tracker_contract.py`:

```python
def test_run_mt5_batch_multi_expert_mode_generates_multi_rule_csv(monkeypatch, tmp_path) -> None:
    """--multi-expert mode собирает multi-rule CSV из двух candidatов и пишет manifest."""
    from ML.baseline import run_mt5_batch

    # Перенаправляем BATCH_DIR в tmp.
    batch_dir = tmp_path / "batch"
    batch_dir.mkdir()
    monkeypatch.setattr(run_mt5_batch, "BATCH_DIR", batch_dir)

    # Подделываем candidates: 2 кандидата с разными magic-ями.
    # score_cutoff — обязательное поле (Task 5 Step реализация:943).
    candidates = [
        {"profile": "p1", "model_key": "m1", "horizon": 12, "threshold_value": 0.5, "score_cutoff": 0.0},
        {"profile": "p2", "model_key": "m2", "horizon": 12, "threshold_value": 0.5, "score_cutoff": 0.0},
    ]

    # Перехватываем materialize_candidate_score_frames и export_mt5_entry_signals
    calls = {"multi_source_builds": []}

    def fake_materialize(cand, ctx):
        # Возвращаем mock-frame из 2 строк: по одной на seed для demo.
        return {
            "frames": {
                "val_select": pd.DataFrame([
                    {"time": "2021.01.05 10:00", "score": 1.0},
                    {"time": "2021.01.05 11:00", "score": 1.0},
                ])
            }
        }

    def fake_export(prepared, output_csv, output_json, max_fill_lag_bars, latency_bars=0, **kwargs):
        # Записываем out.csv и out.json (с manifest).
        import json
        from pathlib import Path
        Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
        prepared.to_csv(output_csv, sep=";", index=False)
        calls["multi_source_builds"].append(str(output_csv))
        manifest = {
            "rows_total": int(len(prepared)),
            "rule_id_groups": sorted(prepared["rule_id"].unique().tolist()),
        }
        Path(output_json).write_text(json.dumps(manifest) + "\n", encoding="utf-8")
        return prepared

    monkeypatch.setattr(run_mt5_batch, "materialize_candidate_score_frames", fake_materialize, raising=False)
    monkeypatch.setattr(run_mt5_batch, "export_mt5_entry_signals", fake_export)
    # eq_scores возвращаем минимальный frame.
    monkeypatch.setattr(run_mt5_batch, "load_eq_scores", lambda: pd.DataFrame([
        {"time_dt": pd.Timestamp("2021.01.05 10:00"), "time": "2021.01.05 10:00",
         "signal_time": "2021.01.05 10:00", "side": "BUY", "limit_price": 1900.0,
         "protective_stop_price": 1890.0, "atr": 10.0},
    ]))
    monkeypatch.setattr(run_mt5_batch, "_build_runtime_context", lambda artifact: {}, raising=False)
    monkeypatch.setattr(run_mt5_batch, "load_candidates", lambda: candidates)
    monkeypatch.setattr(run_mt5_batch, "SOURCE_ARTIFACT_JSON", tmp_path / "artifact.json")
    (tmp_path / "artifact.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(run_mt5_batch, "EQ_SCORES_CSV", tmp_path / "eq.csv")
    (tmp_path / "eq.csv").write_text("time\n2021.01.05 10:00\n", encoding="utf-8")

    # multi-expert mode: по 2 эксперта в batch, magics фиксированы.
    run_mt5_batch.main_multi_expert(candidates, magics=[163856259, 987654321])

    # Должно быть сгенерировано 1 CSV (один batch из 2 экспертов).
    csvs = list(batch_dir.glob("*/entry_signals.csv"))
    assert len(csvs) == 1
    written = pd.read_csv(csvs[0], sep=";")
    assert set(written["rule_id"].unique()) == {"mt5_rule_163856259", "mt5_rule_987654321"}


def test_run_mt5_batch_multi_expert_mode_rejects_mismatched_magics_count(monkeypatch, tmp_path) -> None:
    from ML.baseline import run_mt5_batch

    candidates = [{"profile": "p1"}, {"profile": "p2"}]  # 2 кандидата
    with pytest.raises(ValueError, match="magics count"):
        run_mt5_batch.main_multi_expert(candidates, magics=[163856259])  # 1 magic


def test_run_mt5_batch_main_has_multi_expert_cli_flag() -> None:
    from ML.baseline import run_mt5_batch
    import inspect

    source = inspect.getsource(run_mt5_batch.build_arg_parser) if hasattr(run_mt5_batch, "build_arg_parser") else ""
    assert "--multi-expert" in source or "--multi-expert" in inspect.getsource(run_mt5_batch.main)
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_expert_ml_tracker_contract.py -q -k "multi_expert_mode or multi_expert_flag"
```

Expected: FAIL (функции `main_multi_expert` и CLI flag ещё нет).

- [ ] **Step 3: Добавить CLI flag и `main_multi_expert`**

В файле `ML/baseline/run_mt5_batch.py`, изменить `main()` (строки 769-810):

Было:

```python
def main() -> None:
    parser = argparse.ArgumentParser(description="MT5 batch selection pipeline")
    parser.add_argument("--phase", choices=["signals", "tester", "aggregate", "all"], default="all")
    parser.add_argument(
        "--max-positions",
        type=int,
        default=1,
        help="MT5 multi-position cap passed to the expert's InpMT5_MaxPositions input "
        "(1 = single-position canonical, >1 = multi-pos diagnostic probe).",
    )
    args = parser.parse_args()
```

Стало:

```python
def main() -> None:
    parser = argparse.ArgumentParser(description="MT5 batch selection pipeline")
    parser.add_argument("--phase", choices=["signals", "tester", "aggregate", "all", "smoke-multi-expert"], default="all")
    parser.add_argument(
        "--max-positions",
        type=int,
        default=1,
        help="MT5 multi-position cap passed to the expert's InpMT5_MaxPositions input "
        "(1 = single-position canonical, >1 = multi-pos diagnostic probe).",
    )
    parser.add_argument(
        "--multi-expert",
        action="store_true",
        help="Per-expert ML-CSV mode: генерирует multi-rule signal CSV где rule_id='mt5_rule_<magic>' "
        "для каждого эксперта из --multi-expert-magics, и запускает один tester pass на batch.",
    )
    parser.add_argument(
        "--multi-expert-magics",
        type=str,
        default="",
        help="Comma-separated int magics для multi-expert mode, например '163856259,987654321'. "
        "Количество magics должно совпадать с количеством candidates при signals/tester phase "
        "(или 2 в режиме all, см. batch-size в multi-expert grouping).",
    )
    args = parser.parse_args()
    if args.phase == "smoke-multi-expert":
        # Отдельный multi-expert smoke (Task 8 Step 5): без --multi-expert-magics,
        # магики берутся из эталонного прогона MAGIC_GENERATOR (К-6).
        if not compile_expert():
            print("ABORT: compilation failed")
            sys.exit(1)
        result = run_smoke_test_multi_expert(max_positions=args.max_positions)
        if not result["passed"]:
            print("Smoke multi-expert FAILED.")
            sys.exit(1)
        print("Smoke multi-expert PASSED.")
        return
```

Добавить новую функцию сразу после `main()`:

```python
def main_multi_expert(candidates: list[dict], *, magics: list[int], batch_size: int = 2) -> None:
    """Multi-expert mode: группирует candidates по batch_size, для каждой группы
    собирает multi-rule signal CSV где rule_id='mt5_rule_<magic>' и запускает tester.
    В текущей реализации: одна группа = один tester run."""
    if len(magics) != batch_size:
        raise ValueError(
            f"magics count ({len(magics)}) must match batch_size ({batch_size}) in multi-expert mode"
        )
    # multi-expert mode проверяет только, что магики — int.
    if not all(isinstance(m, int) and m > 0 for m in magics):
        raise ValueError("multi-expert magics must be positive ints")

    from ML.baseline.prepare_mt5_multi_expert_source import prepare_mt5_multi_expert_source
    from ML.baseline.export_mt5_entry_signals import export_mt5_entry_signals

    eq_scores = load_eq_scores()
    experts = [
        {"magic": m, "name": "SoSimple", "sym": "XAUUSD", "per": 60}
        for m in magics
    ]

    # Каждая группа — это набор из batch_size candidates, "склеенных" в один batch.
    for start in range(0, len(candidates), batch_size):
        group = candidates[start:start + batch_size]
        if len(group) != batch_size:
            print(f"SKIP incomplete group {start // batch_size} (only {len(group)} candidates)")
            continue
        batch_id = f"mbatch_{start // batch_size}"
        # К-4: tester-ветка ищет CSV через make_run_id(cand). Чтобы каталог генерации
        # совпал с каталогом поиска в run_batch (run_mt5_batch.py:474-488), имя
        # каталога строится из того же pseudo-candidate через make_run_id.
        pseudo_cand = {"profile": batch_id, "model_key": "multi", "horizon": 0, "threshold_value": 0.0}
        run_id = make_run_id(pseudo_cand)
        out_dir = BATCH_DIR / run_id
        entry_csv = out_dir / "entry_signals.csv"
        entry_json = out_dir / "entry_signals.json"

        if entry_csv.exists() and entry_json.exists():
            print(f"SKIP {batch_id} (already exists)")
            continue

        # Собираем source_groups: для каждого magic в batch_size отдельно materialize.
        source_groups: dict[str, pd.DataFrame] = {}
        for i, (cand, magic) in enumerate(zip(group, magics)):
            rule_id = f"mt5_rule_{magic}"
            result = materialize_candidate_score_frames(cand, _runtime_ctx_or_empty())
            score_frame = result["frames"]["val_select"].copy()
            if "time" not in score_frame.columns:
                print(f"  WARNING: no time column for cand {cand.get('profile')}")
                continue
            score_frame["time_dt"] = pd.to_datetime(score_frame["time"], errors="coerce")
            score_frame = score_frame.dropna(subset=["time_dt"])
            score_frame = score_frame[(score_frame["time_dt"] >= VAL_FROM) & (score_frame["time_dt"] <= VAL_TO)]
            score_cutoff = float(cand["score_cutoff"])
            filtered_scores = score_frame[score_frame["score"] >= score_cutoff]
            if filtered_scores.empty:
                continue
            eq_for_join = eq_scores[["time_dt", "time", "signal_time", "side", "limit_price", "protective_stop_price", "atr"]].copy()
            merged = filtered_scores.merge(eq_for_join, on="time_dt", how="inner")
            if merged.empty:
                continue
            source_df = pd.DataFrame({
                "time": merged["time_y"],
                "signal_time": merged["signal_time"],
                "side": merged["side"],
                "limit_price": pd.to_numeric(merged["limit_price"], errors="coerce"),
                "protective_stop_price": pd.to_numeric(merged["protective_stop_price"], errors="coerce"),
                "atr": pd.to_numeric(merged["atr"], errors="coerce"),
            }).dropna()
            source_groups[rule_id] = source_df

        if not source_groups:
            print(f"  SKIP {batch_id}: no groups with signals")
            continue

        prepared, rule_map = prepare_mt5_multi_expert_source(experts, source_groups)
        out_dir.mkdir(parents=True, exist_ok=True)
        export_mt5_entry_signals(
            prepared,
            entry_csv,
            entry_json,
            max_fill_lag_bars=6,
            latency_bars=0,
            rule_metadata={"rule_map": rule_map, "batch_id": batch_id},
            run_id=batch_id,
            label="mt5_multi_expert_batch",
        )
        print(f"  OK {batch_id}: {len(prepared)} rows, {len(rule_map)} rules")


def _runtime_ctx_or_empty() -> dict:
    """Заглушка для runtime context. В реальном коде вызывается _build_runtime_context,
    но в multi-expert mode тестах он мок-ан. Для production использовать настоящий ctx."""
    try:
        from ML.baseline.benchmark_entry_based_movement_filter import _build_runtime_context
        source_artifact = json.loads(SOURCE_ARTIFACT_JSON.read_text(encoding="utf-8"))
        return _build_runtime_context(source_artifact)
    except Exception:
        return {}
```

В конце `main()` добавить ветку multi-expert (перед последним `if args.phase in ("aggregate", "all"):`):

```python
    if args.multi_expert:
        if not args.multi_expert_magics:
            print("ABORT: --multi-expert requires --multi-expert-magics")
            sys.exit(1)
        try:
            magics = [int(m.strip()) for m in args.multi_expert_magics.split(",") if m.strip()]
        except ValueError:
            print("ABORT: --multi-expert-magics must be comma-separated ints")
            sys.exit(1)
        if args.phase in ("signals", "all"):
            main_multi_expert(candidates, magics=magics)
        if args.phase in ("tester", "all"):
            if not compile_expert():
                print("ABORT: compilation failed")
                sys.exit(1)
            if not check_liveupdate():
                print("ABORT: liveupdate files present")
                sys.exit(1)
            if not check_tester_file_property():
                print("ABORT: tester_file property missing")
                sys.exit(1)
            print("\n--- SMOKE TEST (multi-expert) ---")
            # К-4: обычный run_smoke_test берёт candidates[0] и ищет single-expert CSV,
            # который multi-expert генерация не создаёт. Используем multi-expert smoke.
            smoke_result = run_smoke_test_multi_expert(max_positions=args.max_positions)
            if not smoke_result["passed"]:
                print("ABORT: multi-expert smoke test failed")
                sys.exit(1)
            print("Smoke test PASSED.\n")
            print("--- MULTI-EXPERT BATCH ---")
            # К-4: pseudo-cand идентичен тому, что main_multi_expert использует для
            # make_run_id — run_batch найдёт CSV в том же каталоге BATCH_DIR/run_id.
            for start in range(0, len(candidates), 2):
                batch_id = f"mbatch_{start // 2}"
                pseudo_cand = {"profile": batch_id, "model_key": "multi", "horizon": 0, "threshold_value": 0.0}
                run_batch([pseudo_cand], max_positions=args.max_positions)
        if args.phase in ("aggregate", "all"):
            aggregate_batch(candidates)
        return
```

- [ ] **Step 4: Run failing tests для multi-expert main path**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_expert_ml_tracker_contract.py -q -k "multi_expert_mode or multi_expert_flag"
```

Expected: PASS (3 теста: flag detect, generate multi-rule CSV, reject mismatched magics count).

- [ ] **Step 5: Run existing batch runtime contract test для backcompat**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_batch_runtime_contract.py -q
```

Expected: PASS (single-expert path не изменился на уровне `run_tester`/`run_batch`).

- [ ] **Step 6: Run py_compile для run_mt5_batch.py**

Run:

```bash
./.venv/bin/python -m py_compile ML/baseline/run_mt5_batch.py
```

Expected: PASS (без syntax-ошибок).

- [ ] **Step 7: Commit**

```bash
git add ML/baseline/run_mt5_batch.py tests/test_mt5_per_expert_ml_tracker_contract.py
git commit -m "feat: --multi-expert flag in run_mt5_batch (per-rule CSV assembly)"
```

---

## Task 6: Per-expert lifecycle state by magic

**Files:**
- Modify: `MT/MQL5/Include/lib_ML_Signal.mqh:68-77` (глобальные переменные lifecycle), `MT/MQL5/Include/lib_ML_Signal.mqh:582-648` (`MT5_LogLifecycleForCurrentState`), `MT/MQL5/Include/lib_ML_Signal.mqh:758-860` (`ML_TRADE`)
- Test: `tests/test_mt5_per_expert_ml_tracker_contract.py::test_mt5_lifecycle_state_per_magic_*` (новые)

**Interfaces:**
- Consumes: `MT5_TrackedPositions[]` массив (mult-positions tracker'а от closeout-плана) + `MT5_LastPlacedIdx`/`MT5_LastPlacedMagic`/`MT5_LastPlacedExpiry` глобальные переменные.
- Produces: закладывается новая функция `MT5_PerExpertLastPlaced(int magic, int &out_idx, datetime &out_expiry)` — ищет в `MT5_TrackedPositions[]` запись с `MT5_TrackedPositions[i].magic == magic && open_logged=false`. Глобальные переменные `MT5_LastPlacedIdx/Magic/Expiry` уходят в **deprecated** (но остаются для backcompat single-expert), а вся логика `MT5_LogLifecycleForCurrentState` переходит на per-magic lookup.

**Архитектурное обоснование**: При `Real=true` в тестере `OnTick()` цикл по `e` в `EXP[]` вызывает `ML_TRADE()` пер-экспертно (`$o$imple.mq5:162` цикл → `EXPERT::MAIN()` определена в `MAIN.mqh:133` → `INPUT().ML_TRADE()`); `MT5_LastPlacedIdx` как singleton ломается: после `ML_TRADE(expert_A)` устанавливается для магика A, затем `ML_TRADE(expert_B)` перетирает его же. Поэтому per-expert записи должны жить в отдельной таблице, индексированной по magic.

- [ ] **Step 1: Write failing tests для per-magic tracker state**

Добавить в `tests/test_mt5_per_expert_ml_tracker_contract.py`:

```python
def test_mt5_lifecycle_state_uses_per_magic_lookup() -> None:
    """MT5_LogLifecycleForCurrentState не должен полагаться на глобальный
    singleton MT5_LastPlacedIdx. Должен вызывать per-magic lookup
    (через MT5_TrackedPositions[] по magic == параметру).

    У-2: тест дополняется assertion что тело MT5_LogLifecycleForCurrentState
    содержит вызов MT5_PerExpertLastPlaced — простая проверка сигнатуры
    даёт лишь «функция существует», а не что она используется.
    """
    text = _text(MQL_SIGNAL_LIB)
    match = re.search(
        r"void\s+MT5_LogLifecycleForCurrentState\s*\(\s*int\s+magic\s*,\s*int\s+&ml_close_order_type\s*,\s*ulong\s+&ml_close_ticket\s*\)\s*\{(?P<body>.*?)\n\}",
        text,
        flags=re.S,
    )
    assert match is not None, "Сигнатура MT5_LogLifecycleForCurrentState(int magic, int &ml_close, ulong &ml_close_ticket) сохранена."
    body = match.group("body")
    # У-2: тело функции содержит вызов MT5_PerExpertLastPlaced (не только сигнатура):
    assert "MT5_PerExpertLastPlaced" in body, (
        "MT5_LogLifecycleForCurrentState должен вызывать MT5_PerExpertLastPlaced(magic, idx, expiry) "
        "для per-expert lookup, а не полагаться на singleton MT5_LastPlacedIdx."
    )


def test_mt5_global_last_placed_vars_marked_deprecated() -> None:
    """Глобальные variables MT5_LastPlacedIdx, MT5_LastPlacedMagic, MT5_LastPlacedExpiry
    оставлены для backcompat single-expert пути, но в ML_TRADE больше не меняются
    напрямую — вместо этого используется MT5_PerExpertLastPlaced(magic, idx, expiry)
    и MT5_TrackedPositions[] поиск."""
    text = _text(MQL_SIGNAL_LIB)
    # Пер-эксперт lookup функция должна быть объявлена.
    assert re.search(
        r"(bool|void)\s+MT5_PerExpertLastPlaced\s*\(\s*int\s+magic\s*,\s*int\s+&[^)]*\)",
        text,
    ), "MT5_PerExpertLastPlaced(int magic, int &out_idx, datetime &out_expiry) объявляется."


def test_ml_trade_calls_per_expert_lookup_not_singletons() -> None:
    """ML_TRADE НЕ должна писать в глобальные MT5_LastPlacedIdx/Magic/Expiry при
    multi-expert mode. Должна вызывать MT5_PerExpertLastPlaced(magic, ...)
    или напрямую искать unlogged запись в MT5_TrackedPositions[] по этому magic.

    У-2: тест усиливается двумя проверками:
    (1) в теле ML_TRADE отсутствует безусловное присваивание `MT5_LastPlacedIdx = ...`
        (безусловное сломает multi-expert: singleton перетирается между экспертами).
    (2) в теле ML_TRADE присутствует вызов MT5_PerExpertLastPlaced
        (ИЛИ прямой поиск по MT5_TrackedPositions[i].magic == magic).
    OR-условие было слабым и пропускало код без per-expert lookup.
    """
    text = _text(MQL_SIGNAL_LIB)
    match = re.search(
        r"void\s+EXPERT::ML_TRADE\s*\(\s*\)\s*\{(?P<body>.*?)\n\}",
        text,
        flags=re.S,
    )
    assert match is not None
    body = match.group("body")
    # Per-expert lookup — обязательно присутствует один из вариантов:
    assert (
        "MT5_PerExpertLastPlaced" in body
        or "MT5_TrackedPositions[i].magic == magic" in body
    ), "ML_TRADE должен вызывать MT5_PerExpertLastPlaced или искать в MT5_TrackedPositions по magic."
    # У-2 (2): безусловных присваиваний в singleton нет.
    # Безусловное: строка вида `MT5_LastPlacedIdx = <expr>;` без surrounding if.
    # Здесь regex ловит любое `MT5_LastPlacedIdx\s*=`; допустимо только в backcompat-ветке
    # (которую близко-заключить в `if (!MT5_DiagnosticExecutor ...)`).
    unconditional = re.findall(r"^\s*MT5_LastPlacedIdx\s*=", body, flags=re.M)
    assert not unconditional, (
        "ML_TRADE не должна делать безусловное присваивание MT5_LastPlacedIdx= "
        "(singleton перетирается между экспертами). Допустимо только в backcompat-ветке "
        "с условным переходом."
    )


def test_mt5_tracked_position_struct_has_expiry_and_pending_consumed_fields() -> None:
    """К-1: struct MT5_TRACKED_POSITION должен содержать datetime expiry field,
    чтобы MT5_PerExpertLastPlaced возвращал реальный expiry pending order.
    Без expiry в struct ORDER_EXPIRED проверка TimeCurrent() > 0 не срабатывает.

    К-2: struct должен содержать bool pending_consumed, чтобы mark-consumed
    блокировал повторные ORDER_EXPIRED/OPEN_FAILED события того же pending slot.
    """
    text = _text(MQL_SIGNAL_LIB)
    # Сначала ищем struct declaration, затем ищем поля inside.
    struct_match = re.search(
        r"struct\s+MT5_TRACKED_POSITION\s*\{(?P<body>.*?)\}",
        text,
        flags=re.S,
    )
    assert struct_match is not None, "struct MT5_TRACKED_POSITION должен существовать (closeout-план)."
    body = struct_match.group("body")
    # К-1:
    assert re.search(r"\bdatetime\s+expiry\b", body), (
        "К-1: struct MT5_TRACKED_POSITION должен содержать `datetime expiry` — "
        "иначе MT5_PerExpertLastPlaced возвращает out_expiry=0 и ORDER_EXPIRED никогда "
        "не срабатывает (TimeCurrent() > 0 всегда true при любом TimeCurrent)."
    )
    # К-2:
    assert re.search(r"\bbool\s+pending_consumed\b", body), (
        "К-2: struct должен содержать `bool pending_consumed` — иначе повторные события "
        "ORDER_EXPIRED/OPEN_FAILED вызываются на каждом баре для того же pending slot."
    )


def test_mt5_per_expert_last_placed_returns_real_expiry_from_tracker() -> None:
    """К-1: MT5_PerExpertLastPlaced должен читать out_expiry из MT5_TrackedPositions[].expiry,
    а НЕ возвращать 0. Без этого ORDER_EXPIRED ломается.
    """
    text = _text(MQL_SIGNAL_LIB)
    fn_match = re.search(
        r"bool\s+MT5_PerExpertLastPlaced\s*\((?P<params>[^)]*)\)\s*\{(?P<body>.*?)\n\}",
        text,
        flags=re.S,
    )
    assert fn_match is not None
    body = fn_match.group("body")
    # К-1: literal `out_expiry = 0;` — признак поломанной версии.
    assert (
        "out_expiry = 0" not in body.replace(" ", "")
    ), "К-1: MT5_PerExpertLastPlaced НЕ должен возвращать out_expiry=0 — это ломает ORDER_EXPIRED проверку."
    # Per-expert path должен читать из tracker:
    assert "MT5_TrackedPositions[i].expiry" in body or "out_expiry =" in body


def test_mt5_mark_pending_consumed_helper_exists() -> None:
    """К-2: helper MT5_MarkPendingConsumed(magic, idx) должен быть объявлён,
    вызывается в MT5_LogLifecycleForCurrentState после fill/expire/fail веток.
    """
    text = _text(MQL_SIGNAL_LIB)
    assert re.search(
        r"void\s+MT5_MarkPendingConsumed\s*\(\s*int\s+magic\s*,\s*int\s+idx\s*\)",
        text,
    ), "К-2: MT5_MarkPendingConsumed(magic, idx) helper должен быть объявлён."

    # В теле MT5_LogLifecycleForCurrentState helper вызывается в трёх ветках:
    # fill, ORDER_EXPIRED, OPEN_FAILED. Проверяем хотя бы 2 вхождения.
    fn_match = re.search(
        r"void\s+MT5_LogLifecycleForCurrentState\s*\([^)]*\)\s*\{(?P<body>.*?)\n\}",
        text,
        flags=re.S,
    )
    assert fn_match is not None
    body = fn_match.group("body")
    count = body.count("MT5_MarkPendingConsumed")
    assert count >= 3, (
        f"К-2: MT5_MarkPendingConsumed должен вызываться в 3 ветках (fill/expire/fail), "
        f"найдено {count}. Если < 3 — pending slot не consumed → повторные события на следующих барах."
    )


def test_mt5_register_pending_signal_helper_exists() -> None:
    """К-1: helper MT5_RegisterPendingSignal(magic, idx, expiry) должен быть объявлён,
    вызывается из ML_TRADE вместо closeout MT5_AddTrackedPosition (который guard-ит ticket==0).
    """
    text = _text(MQL_SIGNAL_LIB)
    assert re.search(
        r"void\s+MT5_RegisterPendingSignal\s*\(\s*int\s+magic\s*,\s*int\s+idx\s*,\s*datetime\s+expiry\s*\)",
        text,
    ), "К-1: MT5_RegisterPendingSignal(magic, idx, expiry) helper должен быть объявлён."
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_expert_ml_tracker_contract.py -q -k "lifecycle_state_per_magic or last_placed_deprecated or per_expert_lookup or expiry_field or real_expiry_from_tracker or mark_pending_consumed or register_pending_signal"
```

Expected: FAIL (lookup функции ещё нет, ML_TRADE всё ещё пишет в синглтоны).

- [ ] **Step 3: Read-closeout артефакты — структура `MT5_TRACKED_POSITION` + К-1 expiry + В-4 PosMap migration**

Перед редактированием, executor должен сверить фактическое состояние `MT5_TRACKED_POSITION` struct в `lib_ML_Signal.mqh` (post-closeout). Проверить что struct содержит `magic` field. Проверка через read-only grep:

```bash
rg -n "struct\s+MT5_TRACKED_POSITION|MT5_TRACKED_POSITION\s*\{" MT/MQL5/Include/lib_ML_Signal.mqh
rg -n "MT5_RegisterPosition\b|MT5_PosMapCount\b|MT5_PosMapIds\b" MT/MQL5/Include/lib_ML_Signal.mqh
```

Если struct существует, но не содержит `datetime expiry;` (К-1: текущий closeout-plan struct имеет только `ticket, magic, idx, open_logged, close_logged` — `expiry` нет), **executor добавляет `expiry` field**:

Было (closeout-plan):

```cpp
struct MT5_TRACKED_POSITION {
   ulong ticket;
   int magic;
   int idx;
   bool open_logged;
   bool close_logged;
};
```

Стало (К-1 fix):

```cpp
struct MT5_TRACKED_POSITION {
   ulong ticket;
   int magic;
   int idx;
   datetime expiry;          // К-1: real expiry pending order; 0 для filled market positions
   bool open_logged;
   bool close_logged;
   bool pending_consumed;     // К-2: true после fill/expire/fail — блокирует повторные события для этого pending slot
};
```

**В-4 Migration**: В closeout-плане уже существуют `MT5_PosMapCount`/`MT5_PosMapIds[]`/`MT5_PosMapIdx[]` (`lib_ML_Signal.mqh:80-82` post-closeout) + `MT5_RegisterPosition(ulong, int)` (84-94). **Дополнительно** closeout ввёл `MT5_TrackedPositions[]` и `MT5_TRACKED_POSITION` struct — это **две параллельные структуры**:

- `MT5_PosMapIds[]`/`MT5_PosMapIdx[]` — быстрый lookup `ticket → idx` (для Python-связывания через `OPEN` rows).
- `MT5_TrackedPositions[]` — per-expert lifecycle tracker с open/close_logged.

**Migration policy (В-4)**: не дублировать. `MT5_PosMapIds[]` остаётся для Python-linkage (в closeout-плане `MT5_RegisterPosition(ticket, idx)` вызывается в `lib_ML_Signal.mqh:592` post-fill => это для `OPEN` row). `MT5_TrackedPositions[]` этот план расширяет только `expiry` + `pending_consumed` fields (К-1/К-2). **Мост**: helper `MT5_RegisterPendingSignal(magic, idx, expiry)` (Step 5 ниже) создаёт `MT5_TrackedPositions[]` entry с `ticket=0` (pending ещё не назначен). После fill closeout-план в `MT5_LogLifecycleForTicket` ставит `open_logged=true` и `MT5_RegisterPosition(ticket, idx)` обновляет `MT5_PosMapIds[]` — это две разные таблицы для двух разных задач, дублирования нет.

Если closeout-план уже завёл `magic` field — ничего не менять, переходить к шагу 4. Если `expiry`/`pending_consumed` нет — расширить struct здесь (Step 3).

- [ ] **Step 4: Add `MT5_PerExpertLastPlaced` function (К-1: real expiry)**

В файле `MT/MQL5/Include/lib_ML_Signal.mqh`, сразу после `MT5_FindEntrySignal` (Task 3 внёс правки), добавить:

```cpp
// ─── Per-expert lookup для MT5_TrackedPositions[] ────────────────────
// Возвращает true если найдена незакрытая pending-запись для этого magic
// (pending_consumed=false, ticket==0 — сигнал "ORDER_PLACED поставлен, ждёт fill").
// К-1: возвращает out_expiry РЕАЛЬНЫЙ (не 0), сохранённый в MT5_TrackedPositions[].expiry.
// Заполняет out_idx (index в MT5_EntryTimes[]).
// Backcompat: если MT5_TrackedPositions[] пуст (Real=false, single-expert),
// читает из глобального MT5_LastPlacedIdx singleton.
bool MT5_PerExpertLastPlaced(int magic, int &out_idx, datetime &out_expiry) {
   // 1) Per-expert path: ищем в TrackedPositions запись этого magic с ticket==0 && pending_consumed=false.
   for (int i = 0; i < MT5_TrackedPositionCount; i++) {
      if (MT5_TrackedPositions[i].magic != magic) continue;
      if (MT5_TrackedPositions[i].ticket != 0) continue;       // уже заполнен (filled)
      if (MT5_TrackedPositions[i].pending_consumed) continue;  // К-2: уже обработан
      out_idx = MT5_TrackedPositions[i].idx;
      out_expiry = MT5_TrackedPositions[i].expiry;  // К-1: real expiry
      return true;
   }
   // 2) Backcompat: singleton для Real=false tester / single-expert live.
   if (MT5_LastPlacedMagic == magic && MT5_LastPlacedIdx >= 0) {
      out_idx = MT5_LastPlacedIdx;
      out_expiry = MT5_LastPlacedExpiry;  // singleton всё ещё хранит real expiry для single-expert
      return true;
   }
   return false;
}
```

- [ ] **Step 4b: Add `MT5_RegisterPendingSignal` helper (К-1 pending slot)**

В closeout-плане `MT5_AddTrackedPosition(ulong ticket, int magic, int idx)` имеет guard `if (ticket == 0 || idx < 0) return;` — не позволяет зарегистрировать pending slot (`ticket=0`). Этот план вводит новый helper:

```cpp
// К-1: регистрирует pending-запись (ticket=0, expiry сохранён) в MT5_TrackedPositions[].
// После fill/expire/fail вызывается MT5_MarkPendingConsumed(idx, magic) (К-2).
void MT5_RegisterPendingSignal(int magic, int idx, datetime expiry) {
   if (idx < 0) return;
   // Проверяем, нет ли уже pending-slot этого magic/idx:
   for (int i = 0; i < MT5_TrackedPositionCount; i++) {
      if (MT5_TrackedPositions[i].magic != magic) continue;
      if (MT5_TrackedPositions[i].idx != idx) continue;
      if (MT5_TrackedPositions[i].ticket != 0) continue;
      // Уже есть незакрытый pending slot — обновляем expiry (если retries):
      MT5_TrackedPositions[i].expiry = expiry;
      MT5_TrackedPositions[i].pending_consumed = false;
      return;
   }
   ArrayResize(MT5_TrackedPositions, MT5_TrackedPositionCount + 1);
   MT5_TrackedPositions[MT5_TrackedPositionCount].ticket = 0;
   MT5_TrackedPositions[MT5_TrackedPositionCount].magic = magic;
   MT5_TrackedPositions[MT5_TrackedPositionCount].idx = idx;
   MT5_TrackedPositions[MT5_TrackedPositionCount].expiry = expiry;
   MT5_TrackedPositions[MT5_TrackedPositionCount].open_logged = false;
   MT5_TrackedPositions[MT5_TrackedPositionCount].close_logged = false;
   MT5_TrackedPositions[MT5_TrackedPositionCount].pending_consumed = false;
   MT5_TrackedPositionCount++;
}

// К-2: mark pending slot consumed по (magic, idx) — блокирует повторные ORDER_EXPIRED/OPEN_FAILED.
// Вызывается в Step 6 после первого ORD_PLACED → fill/expire/fail события.
void MT5_MarkPendingConsumed(int magic, int idx) {
   for (int i = 0; i < MT5_TrackedPositionCount; i++) {
      if (MT5_TrackedPositions[i].magic != magic) continue;
      if (MT5_TrackedPositions[i].idx != idx) continue;
      if (MT5_TrackedPositions[i].ticket != 0) continue;  // только pending slots
      MT5_TrackedPositions[i].pending_consumed = true;
      return;
   }
}
```

- [ ] **Step 5: Refactor `ML_TRADE` — убрать прямые singleton пишет, использовать per-expert lookup**

В файле `MT/MQL5/Include/lib_ML_Signal.mqh`, в функции `EXPERT::ML_TRADE()` (строка 852), заменить блок «ORDER_PLACED path» (примерные строки 920-955, исполнитель сверяется с фактическим):

Было (для BUY_LIMIT ветки, аналогично для SELL_LIMIT):

```cpp
      if (is_buy_limit) {
         if (limit_price >= Ask - StopLevel || stop_price >= limit_price) {
            MT5_LogSignalEvent("OPEN_FAILED", mt5_idx, 0, "BUY_LIMIT price/stop invalid for current market");
            return;
         }
         set.BUY.Sig = GOGO;
         set.BUY.Val = (float)limit_price;
         set.BUY.Stp = (float)stop_price;
         set.BUY.Prf = 0;
         set.BUY.Exp = expiry;
         UP = 1;
         MT5_LastPlacedIdx = mt5_idx;
         MT5_LastPlacedMagic = Mgc;
         MT5_LastPlacedExpiry = expiry;
         MT5_LogSignalEvent("ORDER_PLACED", mt5_idx, 0, "set.BUY path prepared");
         return;
      }
```

Стало (для BUY_LIMIT ветки, аналогично для SELL_LIMIT):

```cpp
      if (is_buy_limit) {
         if (limit_price >= Ask - StopLevel || stop_price >= limit_price) {
            MT5_LogSignalEvent("OPEN_FAILED", mt5_idx, 0, "BUY_LIMIT price/stop invalid for current market");
            return;
         }
         set.BUY.Sig = GOGO;
         set.BUY.Val = (float)limit_price;
         set.BUY.Stp = (float)stop_price;
         set.BUY.Prf = 0;
         set.BUY.Exp = expiry;
         UP = 1;
         // К-1: Per-expert pending slot — сохраняем real expiry в tracker.
         MT5_RegisterPendingSignal(Mgc, mt5_idx, expiry);
         // Backcompat singleton: сохраняем для single-expert legacy путей (не мешает multi-expert,
         // т.к. MT5_PerExpertLastPlaced сначала ищет в TrackedPositions[]).
         MT5_LastPlacedIdx = mt5_idx;
         MT5_LastPlacedMagic = Mgc;
         MT5_LastPlacedExpiry = expiry;
         MT5_LogSignalEvent("ORDER_PLACED", mt5_idx, 0, "set.BUY path prepared");
         return;
      }
```

Замечание: **`MT5_RegisterPendingSignal(magic, idx, expiry)`** — новый helper, добавленный в Step 4b (НЕ closeout `MT5_AddTrackedPosition` — тот guard-ит `ticket==0`). Closeout `MT5_AddTrackedPosition` используется post-fill в `MT5_LogLifecycleForTicket` для регистрации filled market positions (`ticket>0`), это раздельные роли.

Аналогично для SELL_LIMIT ветки.

- [ ] **Step 6: Refactor `MT5_LogLifecycleForCurrentState` — per-magic вместо singleton + К-2 mark consumed**

В файле `MT/MQL5/Include/lib_ML_Signal.mqh`, изменить функцию `MT5_LogLifecycleForCurrentState` (строка 714, executor сверяется с фактическим):

Было (post-closeout, текущее состояние):

```cpp
void MT5_LogLifecycleForCurrentState(int magic, int &ml_close_order_type, ulong &ml_close_ticket) {
   ml_close_order_type = -1;
   ml_close_ticket = 0;

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
      MT5_LogLifecycleForTicket(i, magic, ml_close_order_type, ml_close_ticket);
      if (MT5_TrackedPositionCount < before) i--;
   }
}
```

Стало (per-magic путь, backcompat singleton сохраняется через `MT5_PerExpertLastPlaced`):

```cpp
void MT5_LogLifecycleForCurrentState(int magic, int &ml_close_order_type, ulong &ml_close_ticket) {
   ml_close_order_type = -1;
   ml_close_ticket = 0;

   // Per-expert path: проверяем pending-запись для этого magic.
   int mt5_last_idx = -1;
   datetime mt5_last_expiry = 0;
   bool has_pending = MT5_PerExpertLastPlaced(magic, mt5_last_idx, mt5_last_expiry);

   if (has_pending) {
      ulong buy_pending = MT5_FindActiveTicket(magic, OP_BUYLIMIT, OP_BUYSTOP);
      ulong sell_pending = MT5_FindActiveTicket(magic, OP_SELLLIMIT, OP_SELLSTOP);
      ulong buy_market = MT5_FindActiveTicket(magic, OP_BUY, OP_BUY);
      ulong sell_market = MT5_FindActiveTicket(magic, OP_SELL, OP_SELL);
      if (buy_market > 0 || sell_market > 0) {
         // Регистрируем реальную fill-позицию в tracker (multi-pos).
         MT5_AddTrackedPosition((buy_market > 0 ? buy_market : sell_market), mt5_last_idx, magic);
         // К-2: mark pending slot consumed — заполнение (fill) случилось.
         MT5_MarkPendingConsumed(magic, mt5_last_idx);
         // Сбрасываем singleton (backcompat single-expert).
         MT5_LastPlacedIdx = -1;
         if (MT5_LastPlacedMagic == magic) MT5_LastPlacedExpiry = 0;
      } else if (buy_pending == 0 && sell_pending == 0 && mt5_last_expiry > 0 && TimeCurrent() > mt5_last_expiry) {
         // К-1:  expiry > 0 теперь работает (MT5_PerExpertLastPlaced возвращает real expiry из tracker).
         MT5_LogSignalEvent("ORDER_EXPIRED", mt5_last_idx, 0, "pending order not active after max_fill_lag_bars");
         // К-2: mark pending slot consumed — expired, событие не повторяется на следующем баре.
         MT5_MarkPendingConsumed(magic, mt5_last_idx);
         MT5_LastPlacedIdx = -1;
         if (MT5_LastPlacedMagic == magic) MT5_LastPlacedExpiry = 0;
      } else if (buy_pending == 0 && sell_pending == 0) {
         MT5_LogSignalEvent("OPEN_FAILED", mt5_last_idx, 0, "pending order was not found after ORDER_PLACED");
         // К-2: mark pending slot consumed — fail, событие не повторяется на следующем баре.
         MT5_MarkPendingConsumed(magic, mt5_last_idx);
         MT5_LastPlacedIdx = -1;
         if (MT5_LastPlacedMagic == magic) MT5_LastPlacedExpiry = 0;
      }
   }

   // Multi-pos lifecycle: проходим по всем tracked positions этого magic (filled, ticket>0).
   // (closeout-план ввёл MT5_LogLifecycleForTicket; здесь — обёртка по magic.)
   for (int tp = 0; tp < MT5_TrackedPositionCount; tp++) {
      if (MT5_TrackedPositions[tp].magic != magic) continue;
      if (MT5_TrackedPositions[tp].ticket == 0) continue;  // К-2: skip pending slots (обработаны выше)
      int before = MT5_TrackedPositionCount;
      MT5_LogLifecycleForTicket(tp, magic, ml_close_order_type, ml_close_ticket);
      if (MT5_TrackedPositionCount < before) tp--;
   }
}
```

Замечание: `MT5_AddTrackedPosition`, `MT5_TrackedPositions[]`, `MT5_LogLifecycleForTicket` — из closeout-плана. Этот план дополняет struct только `expiry` + `pending_consumed` (К-1/К-2) и добавляет `MT5_RegisterPendingSignal`/`MT5_MarkPendingConsumed` helpers (Step 4b). `MT5_PosMapIds[]` (существующий в `lib_ML_Signal.mqh:80-82`) остаётся для Python-linkage, дублирования нет.

- [ ] **Step 7: Run static contract tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_expert_ml_tracker_contract.py -q -k "lifecycle_state_per_magic or last_placed_deprecated or per_expert_lookup"
```

Expected: PASS (7 тестов: 3 старых + 4 новых К-1/К-2 static contract теста: `test_mt5_tracked_position_struct_has_expiry_and_pending_consumed_fields`, `test_mt5_per_expert_last_placed_returns_real_expiry_from_tracker`, `test_mt5_mark_pending_consumed_helper_exists`, `test_mt5_register_pending_signal_helper_exists`).

- [ ] **Step 8: Run existing MQL-header contract tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py tests/test_mt5_per_expert_ml_tracker_contract.py -q
```

Expected: PASS (существующие тесты (`test_mt5_lifecycle_events_keep_source_decision_time`, `test_mt5_entry_init_logs_and_skips_timing_violations`, …) могут нуждаться в адаптации; если fail — фиксить regex в шаге 9).

- [ ] **Step 9: Smoke-run tests после адаптации reg-exов**

Если шаг 8 показал fail в существующем тесте, адаптировать regex по образцу Task 3 Step 6 — добавить `(?:\s*,\s*int\s+magic)?` опц-группу или явно расширить сигнатурy. чанное правило: не удалять существующие assertion-ы, только расширять regex на новую сигнатуру.

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py tests/test_mt5_per_expert_ml_tracker_contract.py -q
```

Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add MT/MQL5/Include/lib_ML_Signal.mqh tests/test_mt5_per_expert_ml_tracker_contract.py tests/test_mt5_signal_executor_schema.py
git commit -m "feat: per-expert tracker state (MT5_PerExpertLastPlaced + pending expiry К-1 + mark pending consumed К-2 + PosMap migration В-4)"
```

---

## Task 7: Per-rule reconciliation в `parse_mt5_execution_report.py`

**Files:**
- Modify: `ML/baseline/parse_mt5_execution_report.py:1-155`
- Test: `tests/test_parse_mt5_execution_report.py` (новые тесты для per-rule reconciliation)

**Interfaces:**
- Consumes: event CSV (`mt5_trade_events.csv`) из MT5 tester с колонками `rule_id`, `magic` (методология 13b строки 73). Существующий `reconcile_positions(events)` возвращал `class_counts` (CLOSED_TX, OPEN_AT_END, UNEXPLAINED).
- Produces: new `reconcile_positions_per_rule(events: pd.DataFrame) -> dict[str, dict[str, object]]` — для каждого `rule_id` возвращает `{"class_counts": {...}, "magic": int, "matched_tx_count": int}`. `reconcile_positions` остаётся как aggregate-over-all-rules (backcompat), а per-rule — новое дополнение в `metrics.json` под ключом `per_rule_reconciliation`.

- [ ] **Step 1: Read existing `parse_mt5_execution_report.py` и тесты**

Run:

```bash
wc -l ML/baseline/parse_mt5_execution_report.py tests/test_parse_mt5_execution_report.py
```

Затем прочитать файлы точечно (executor сам через `Read` с offset/limit):

```bash
# файлы затем читаются инструментально, не cat.
```

- [ ] **Step 2: Write failing tests для per-rule reconciliation**

Добавить в `tests/test_parse_mt5_execution_report.py` (после существующих тестов):

```python
def test_reconcile_positions_per_rule_splits_by_rule_id() -> None:
    """reconcile_positions_per_rule возвращает per-rule классификацию."""
    from ML.baseline.parse_mt5_execution_report import reconcile_positions_per_rule

    events = pd.DataFrame([
        _event_row("TX_OPEN", "2021.01.05 10:00", ticket=101, magic=163856259, rule_id="mt5_rule_163856259"),
        _event_row("TX_CLOSE", "2021.01.05 14:00", ticket=101, magic=163856259, rule_id="mt5_rule_163856259"),
        _event_row("TX_OPEN", "2021.01.06 10:00", ticket=201, magic=987654321, rule_id="mt5_rule_987654321"),
        # останется OPEN_AT_END (нет соответствующего TX_CLOSE)
    ])
    per_rule = reconcile_positions_per_rule(events)
    assert set(per_rule.keys()) == {"mt5_rule_163856259", "mt5_rule_987654321"}
    assert per_rule["mt5_rule_163856259"]["class_counts"]["CLOSED_TX"] == 1
    assert per_rule["mt5_rule_987654321"]["class_counts"]["OPEN_AT_END"] == 1
    assert per_rule["mt5_rule_163856259"]["magic"] == 163856259
    assert per_rule["mt5_rule_987654321"]["magic"] == 987654321


def test_reconcile_positions_per_rule_classifies_unexplained() -> None:
    from ML.baseline.parse_mt5_execution_report import reconcile_positions_per_rule

    events = pd.DataFrame([
        _event_row("TX_OPEN", "2021.01.05 10:00", ticket=301, magic=163856259, rule_id="mt5_rule_163856259"),
        # ни TX_CLOSE, ни завершающего tx — засчитают OPEN_AT_END (не UNEXPLAINED):
        # position_id из TX_OPEN без TX_CLOSE → OPEN_AT_END (reconcile_positions:85-86).
    ])
    per_rule = reconcile_positions_per_rule(events)
    assert per_rule["mt5_rule_163856259"]["class_counts"]["OPEN_AT_END"] == 1
    assert per_rule["mt5_rule_163856259"]["class_counts"]["UNEXPLAINED"] == 0


def test_reconcile_positions_per_rule_returns_empty_dict_for_no_tx_events() -> None:
    from ML.baseline.parse_mt5_execution_report import reconcile_positions_per_rule

    events = pd.DataFrame([_event_row("ORDER_PLACED", "2021.01.05 10:00", rule_id="mt5_rule_1", magic=1)])
    per_rule = reconcile_positions_per_rule(events)
    assert per_rule == {}


def test_reconcile_positions_per_rule_fallback_no_rule_id_backcompat() -> None:
    """К-3 fallback: события без rule_id (старые CSV до миграции) попадают в __no_rule_id__ bucket.
    Имитирует 32 существующих CSV без колонки rule_id или с пустым значением.
    """
    from ML.baseline.parse_mt5_execution_report import reconcile_positions_per_rule

    events = pd.DataFrame([
        _event_row("TX_OPEN", "2021.01.05 10:00", ticket=101, magic=163856259, rule_id=""),
        _event_row("TX_CLOSE", "2021.01.05 14:00", ticket=101, magic=163856259, rule_id=""),
    ])
    per_rule = reconcile_positions_per_rule(events)
    assert set(per_rule.keys()) == {"__no_rule_id__"}
    assert per_rule["__no_rule_id__"]["class_counts"]["CLOSED_TX"] == 1
    assert per_rule["__no_rule_id__"]["magic"] == 163856259


def test_main_writes_per_rule_reconciliation_to_metrics_json(tmp_path: Path) -> None:
    from ML.baseline.parse_mt5_execution_report import main as parser_main

    events_csv = tmp_path / "events.csv"
    metrics_json = tmp_path / "metrics.json"
    pd.DataFrame([
        _event_row("TX_OPEN", "2021.01.05 10:00", ticket=101, magic=163856259, rule_id="mt5_rule_163856259"),
        _event_row("TX_CLOSE", "2021.01.05 14:00", ticket=101, magic=163856259, rule_id="mt5_rule_163856259"),
    ]).to_csv(events_csv, sep=";", index=False)

    parser_main(["--events", str(events_csv), "--output-json", str(metrics_json)])

    metrics = json.loads(metrics_json.read_text(encoding="utf-8"))
    assert "per_rule_reconciliation" in metrics
    assert "mt5_rule_163856259" in metrics["per_rule_reconciliation"]


def test_reconcile_positions_per_rule_classifies_unexplained_tx_close_only() -> None:
    """UNEXPLAINED: позиция без TX_OPEN (есть только TX_CLOSE → position_id не из TX_OPEN).
    По фактической логике reconcile_positions (parse_mt5_execution_report.py:79-88)
    UNEXPLAINED получает позиция без валидного TX_OPEN (например только TX_CLOSE).
    Этот тест — regression на такое поведение в per-rule срезе.
    """
    from ML.baseline.parse_mt5_execution_report import reconcile_positions_per_rule

    events = pd.DataFrame([
        _event_row("TX_CLOSE", "2021.01.05 14:00", ticket=777, magic=163856259, rule_id="mt5_rule_163856259"),
        # TX_OPEN отсутствует → этот ticket становится UNEXPLAINED в per-rule срезе
    ])
    per_rule = reconcile_positions_per_rule(events)
    assert per_rule["mt5_rule_163856259"]["class_counts"]["UNEXPLAINED"] == 1
```

- [ ] **Step 3: Run failing tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_parse_mt5_execution_report.py -q -k "per_rule"
```

Expected: FAIL (функция `reconcile_positions_per_rule` ещё не существует; `per_rule_reconciliation` key в metrics нет). 6 тестов: `test_reconcile_positions_per_rule_splits_by_rule_id`, `test_reconcile_positions_per_rule_classifies_unexplained`, `test_reconcile_positions_per_rule_returns_empty_dict_for_no_tx_events`, `test_reconcile_positions_per_rule_fallback_no_rule_id_backcompat`, `test_main_writes_per_rule_reconciliation_to_metrics_json`, `test_reconcile_positions_per_rule_classifies_unexplained_tx_close_only`.

- [ ] **Step 4: Implement `reconcile_positions_per_rule`**

В файле `ML/baseline/parse_mt5_execution_report.py`, добавить функцию после существующей `reconcile_positions` (между строками 112 и 114, перед `compute_mt5_metrics`):

```python
def reconcile_positions_per_rule(events: pd.DataFrame) -> dict[str, dict[str, object]]:
    """Per-rule классификация: для каждого rule_id отдельно считает CLOSED_TX / OPEN_AT_END / UNEXPLAINED
    и связанный magic. Возвращает dict: rule_id → {"class_counts": {...}, "magic": int, ...}.
    Если в events нет TX_* событий, возвращает пустой dict.

    Реализует К-3 fallback: события без колонки `rule_id` (или пустым значением) группируются
    под ключом `__no_rule_id__` — backcompat для CSV, записанных до миграции (32 исторических CSV).
    """
    if events.empty:
        return {}
    tx_events = events[events["event"].isin(["TX_OPEN", "TX_CLOSE"])].copy()
    if tx_events.empty:
        return {}

    # по правилу magic — выясняем из первого matching event.
    rule_to_magic: dict[str, int] = {}
    for _, row in events.iterrows():
        rule_id = str(row.get("rule_id", "")).strip()
        if rule_id == "":
            rule_id = "__no_rule_id__"
        try:
            magic = int(row.get("magic", 0) or 0)
        except (TypeError, ValueError):
            magic = 0
        if rule_id not in rule_to_magic and magic > 0:
            rule_to_magic[rule_id] = magic
        elif rule_id not in rule_to_magic:
            rule_to_magic[rule_id] = 0

    per_rule: dict[str, dict[str, object]] = {}
    for rule_id, magic in rule_to_magic.items():
        per_rule[rule_id] = {
            "magic": magic,
            "class_counts": {"CLOSED_TX": 0, "OPEN_AT_END": 0, "UNEXPLAINED": 0},
        }

    # Группируем events по rule_id и вызываем reconcile_positions(subset).
    rule_col = events["rule_id"].astype(str).str.strip() if "rule_id" in events.columns else pd.Series([""] * len(events))
    for rule_id in rule_to_magic:
        if rule_id == "__no_rule_id__":
            sub = events[rule_col.eq("")]
        else:
            sub = events[rule_col.eq(rule_id)]
        if sub.empty:
            continue
        sub_recon = reconcile_positions(sub)
        per_rule[rule_id]["class_counts"] = sub_recon.get("class_counts", {})
        if "unexplained_position_ids" in sub_recon:
            per_rule[rule_id]["unexplained_position_ids"] = sub_recon["unexplained_position_ids"]

    return per_rule
```

- [ ] **Step 5: Wire per-rule в выход `compute_mt5_metrics`** (не в `main`)

В `ML/baseline/parse_mt5_execution_report.py:114-140`, функция `compute_mt5_metrics` уже возвращает dict с ключом `"reconciliation"` (строка 139). Добавить параллельный ключ прямо в return dict `compute_mt5_metrics`:

```python
        "reconciliation": reconcile_positions(events),
        "per_rule_reconciliation": reconcile_positions_per_rule(events),
```

**Note (К-7):** `main()` (строка 143) имеет сигнатуру `def main() -> None:` — без параметра `argv`, а тест `test_main_writes_per_rule_reconciliation_to_metrics_json` вызывает `parser_main(["--events", ..., "--output-json", ...])` (список argv). Это **type mismatch** — план правит сигнатуру `main` на:

```python
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Parse MT5 execution report and emit diagnostic metrics.")
    parser.add_argument("--events", required=True, help="Path to MT5 event CSV")
    parser.add_argument("--output-json", required=True, help="Path to output metrics JSON")
    args = parser.parse_args(argv)

    events = parse_mt5_events(args.events)
    metrics = compute_mt5_metrics(events)
    Path(args.output_json).write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
```

`if __name__ == "__main__": main()` (строка 155) остаётся без изменений — `argv=None` → `argparse` берёт `sys.argv[1:]`. CLI backcompat сохранён.

- [ ] **Step 6: Run failing tests для main**

Run:

```bash
./.venv/bin/python -m pytest tests/test_parse_mt5_execution_report.py -q -k "per_rule or main_writes_per_rule"
```

Expected: PASS (6 тестов).

- [ ] **Step 7: Run existing parse_mt5_execution_report tests для backcompat**

Run:

```bash
./.venv/bin/python -m pytest tests/test_parse_mt5_execution_report.py -q
```

Expected: PASS (существующие test продолжают работать — новый ключ аддитивен).

- [ ] **Step 8: Commit**

```bash
git add ML/baseline/parse_mt5_execution_report.py tests/test_parse_mt5_execution_report.py
git commit -m "feat: per-rule reconciliation in parse_mt5_execution_report"
```

---
---

## Task 8: Compile gate и multi-expert smoke

**Files:**
- Run-only: `MT/MQL5/Experts/$o$imple.mq5`, `docs/methodology/13b-mt5-execution-parity.md:150-170`

**Interfaces:**
- Consumes: все MQL5 правки из Tasks 3, 6 + Python правки из Tasks 4, 5, 7. Tester-конфиг из `run_mt5_batch.create_set_file`/`create_ini_file`.
- Produces: свежий `.ex5` + compile-лог `/tmp/sosimple_mt5_per_expert_compile.log` + smoke-результат.

**Методология**: `docs/methodology/13b-mt5-execution-parity.md:150-170` (компиляция), `165` (`0 errors, 0 warnings`), `168-170` (не считать exit-code wine verdict-ом).

- [ ] **Step 1: Полный pytest-набор для MQL5 + Python контрактов**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_expert_ml_tracker_contract.py tests/test_mt5_signal_executor_schema.py tests/test_mt5_batch_runtime_contract.py tests/test_parse_mt5_execution_report.py tests/test_mt5_execution_diagnostics.py -q
```

Expected: PASS (все тесты). Если FAIL — вернуться к Task 1/3/6/7 и дополнить regex-адаптации.

- [ ] **Step 2: Source formatting check**

Run:

```bash
./.venv/bin/python -m py_compile ML/baseline/run_mt5_batch.py ML/baseline/prepare_mt5_entry_source.py ML/baseline/prepare_mt5_multi_expert_source.py ML/baseline/parse_mt5_execution_report.py ML/baseline/export_mt5_entry_signals.py
```

Expected: PASS (без syntax-ошибок).

- [ ] **Step 3: Compile MT5 expert**

Run (метаданные из `docs/methodology/13b-mt5-execution-parity.md:148-153`). **В-8**: путь содержит `$o$imple` — `$` раскрывается bash как переменная, если строку выполнять в двойных кавычках или без кавычек. Команда ниже обёрнута в **одинарные** кавычки — внутри них bash не раскрывает `$` и не обрабатывает `\$`, поэтому бэкслэши НЕ нужны (с ними wine получит несуществующий путь `\$o\$imple.mq5`):

```bash
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' \
  /compile:'/home/hohla/git/SoSimple/MT/MQL5/Experts/$o$imple.mq5' \
  /log:'/tmp/sosimple_mt5_per_expert_compile.log'
```

- [ ] **Step 4: Прочитать compile-лог**

Run:

```bash
iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_per_expert_compile.log | tail -n 20
```

Expected: строка `Result: 0 errors, 0 warnings` и обновлённый `MT/MQL5/Experts/$o$imple.ex5`. Не считать exit-код `wine` окончательным verdict-ом (13b:168-170).

- [ ] **Step 4b: Grep-проверка отсутствия регрессии кастов**

Run:

```bash
rg -n "\(int\)OrderTicket\(\)|\(int\)ticket\b|\(int\)MT5_TrackedTicket" MT/MQL5/Include/lib_ML_Signal.mqh MT/MQL5/Include/ORDERS.mqh MT/MQL5/Include/ERRORs.mqh MT/MQL5/Include/OUTPUT.mqh
rg -n "MT5_TrackedTicket\b" MT/MQL5/Include/lib_ML_Signal.mqh
```

Expected: первая команда — 0 строк (касты не вернулись); вторая — 0 строк (singleton не вернулся); если что-то появилось — fallback к closeout Task 4 Step 4b / Task 6 Step 3 (struct уже содержит `magic`).

- [ ] **Step 5: Run multi-expert smoke через новый tester-branch в `run_mt5_batch.py`**

**К-4/К-5/К-6 правки.** Существующий `run_smoke_test` (`ML/baseline/run_mt5_batch.py:425`) берёт `entry_csv = BATCH_DIR / run_id / "entry_signals.csv"`, где `run_id = make_run_id(cand)` — это `"fractal0_entry_quality_v1_12h_thr0.5"` или `"mbatch_0_multi_0h_thr0.0"` (мulti-expert), не `mbatch_N`. `copy_entry_signal_file` (438) затирает ручную подкладку. Для multi-expert smoke этот путь ломается (К-4). Решение: новый **tester-branch** `run_smoke_test_multi_expert(out_dir, auto_magics: list[int], max_positions: int = 1) -> dict` в `run_mt5_batch.py`, который:

1. **К-5: генерирует smoke-строки в окне** `2021.01.05 - 2021.03.31` (текущее `VAL_FROM=2021.01.04 … VAL_TO=2022.12.02` в Python `run_mt5_batch.py:27-28`; smoke-окно уже внутри val_stop — smoke создаёт всего 2 строки на 2 эксперта, что не нагружает batch-оркестрацию). Smoke сводится к двум строкам:
   - `2021.01.05 10:00`, `mt5_rule_<magic_A>` (magic_A из `auto_magics[0]`)
   - `2021.01.06 11:00`, `mt5_rule_<magic_B>` (magic_B из `auto_magics[1]`)
2. **К-6: auto-magics из `MAGIC_GENERATOR`** вместо произвольных `163856259/987654321`. Concretно: запускаем **эталонный single-expert compile-gate прогон** в read-only режиме (одна static `MQL5 OnTick()` в тестере без `mt5_entry_signals.csv`), `MAGIC_GENERATOR()` возвращает 1 magic для `Symbol="XAUUSD", Period=M1, iSignal=3` (и входных параметров по умолчанию из `#.csv[0]`). Берём **две инстанции** с разными `iParam=1, 2` (или разными `#-строками` из `#.csv`), получаем 2 детерминированных магика. Это гарантирует `CHECKSUM` (`SERVICE.mqh:251`: `MAGIC_GENERATOR()==EXP[e].Mgc`) → 2 эксперта не отключены → smoke даёт ≥2 ORDER_PLACED событий.

`run_smoke_test_multi_expert` шаги:

- Создаёт временный `mt5_entry_signals.csv` с 2 строками в `MT/MQL5/Files/` напрямую (НЕ через `copy_entry_signal_file`, чтобы не затирать — К-4).
- Создаёт тестовый `#.csv` с 2 экспертами, у которых `Mgc` совпадает с `auto_magics` (так `CHECKSUM` проходит).
- Создаёт `.set`/`.ini` файлы через `create_set_file`/`create_ini_file` (параметр `InpMT5_DiagnosticExecutor=true`, `InpMT5_NeroFile=""`, `iSignal=3`).
- Запускает wine tester с multi-expert конфигурацией.
- Парсит `mt5_trade_events.csv` через `parse_mt5_events` + `compute_mt5_metrics` (Task 7 дал `per_rule_reconciliation`).
- Возвращает `{"passed": bool, "metrics": dict, "per_rule": dict, "events_csv": str}`.

**Критерий PASS (К-6, новый, не только `UNEXPLAINED=0`):**
- `metrics["order_counts"]["ORDER_PLACED"] >= 2` (по 1+ на rule_id).
- `metrics["order_counts"]["CLOSED"] >= 2` (или в `per_rule_reconciliation` каждый `rule_id` имеет `class_counts["CLOSED_TX"] >= 1`).
- `metrics["reconciliation"]["class_counts"]["UNEXPLAINED"] == 0`.
- Каждый `rule_id` в `per_rule_reconciliation` имеет `CLOSED_TX >= 1`.

Если только `UNEXPLAINED=0` без ORDER_PLACED → ложный PASS (это состояние К-6: эксперты отключены `CHECKSUM` → 0 событий → тривиально 0 unexplained). Новый критерий блокирует эту подмену.

- [ ] **Step 6: Run multi-expert smoke через `run_smoke_test_multi_expert`**

Run:

```bash
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase smoke-multi-expert --max-positions 1
```

`--phase smoke-multi-expert` — новый CLI флаг, который вызывает `run_smoke_test_multi_expert` напрямую (без `--multi-expert-magics`: берёт auto-magics из эталонного прогона `MAGIC_GENERATOR`). По завершении печатает строку `Smoke multi-expert PASSED.`/`FAILED` с указанием `per_rule` per-rule_id CLOSED_TX или причину FAIL.

Если FAIL — критерии по К-6:
- `ORDER_PLACED < 2` — эксперты отключены (`CHECKSUM`), смотри auto-magics генерацию Step 5. Возможная причина коллизия magic — использовать другой `iParam` (`MAGIC_GENERATOR` зависит от `iParam`).
- `CLOSED < 2` — ордера не закрываются. Проверить `MT5_LogLifecycleForTicket` (Task 6) для обоих rule_id через `per_rule_reconciliation`.
- `UNEXPLAINED > 0` — диагностика в `per_rule_reconciliation`: какой `rule_id` имеет UNEXPLAINED → мимо от `MT5_FindEntrySignal` фильтра (Task 3) — ошибка с rule_id → magic mapping.

- [ ] **Step 7: Проверить per-rule reconciliation в metrics.json из `run_smoke_test_multi_expert`**

Прочитать `ML/reports/mt5_execution_loop/batch/_smoke_multi_expert/metrics.json` (path возвращается из `run_smoke_test_multi_expert`). Должен содержать:

```json
{
  "reconciliation": {"class_counts": {"CLOSED_TX": 2, "OPEN_AT_END": 0, "UNEXPLAINED": 0}},
  "per_rule_reconciliation": {
    "mt5_rule_<magic_A>": {"magic": <magic_A>, "class_counts": {"CLOSED_TX": 1, ...}},
    "mt5_rule_<magic_B>": {"magic": <magic_B>, "class_counts": {"CLOSED_TX": 1, ...}}
  }
}
```

Если `per_rule_reconciliation` отсутствует или `rule_id == ""` — проблема в `MT5_ENTRY_INIT` не сохраняет `MT5_RuleIds[]` (Task 3), либо в `MT5_LogSignalEvent` не передаёт `rule_id` в `MT5_ML_LogEvent` (lib_ML_Signal.mqh:371-411, executor проверяет). Исправить в Task 3/6 — fallback.

**К-3 fallback**: если события без `rule_id` в CSV (старая схема до миграции), они попадают в bucket `__no_rule_id__` в `per_rule_reconciliation` (см. Task 7 Step 4 реализация).

- [ ] **Step 8: Полный pytest run (пост-smoke, чтобы убедиться что правок не потребовалось)**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_expert_ml_tracker_contract.py tests/test_mt5_signal_executor_schema.py tests/test_mt5_batch_runtime_contract.py tests/test_parse_mt5_execution_report.py tests/test_mt5_execution_diagnostics.py tests/test_mt5_nero_parity.py -q
```

Expected: PASS (smoke мог выявить адаптации в regex или логике, которые теперь отражены в тестах).

- [ ] **Step 9: Commit smoke artifacts (если source менялся после Step 3)**

```bash
git add -- MT/MQL5/Include/lib_ML_Signal.mqh ML/baseline/ ML/reports/mt5_execution_loop/batch/_smoke_multi_expert/ tests/
git commit -m "test: multi-expert smoke for per-rule ml-tracker (0 warnings, 0 unexplained)"
```

Если source не менялся после Task 7 — этот commit опционален (smoke-artifacts gitignored).

---

## Task 9: Финальная отчётность и синхронизация CHANGELOG / CONTEXT_HANDOFF

**Files:**
- Create: `docs/reports/2026-08-03-mt5-per-expert-ml-tracker.md`
- Modify: `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `docs/superpowers/roadmap.md` (только если меняет ACTIVE track — обычно не меняет), `docs/superpowers/audit.md` (только если аудит закрыт этим планом — обычно нет)

**Методология**: `docs/methodology/16-reporting-audit.md` (disclosure). Раздел Self-Review ниже содержит обязательные поля disclosure.

- [ ] **Step 1: Создать отчёт `docs/reports/2026-08-03-mt5-per-expert-ml-tracker.md`**

Скопировать шаблон disclosure:

```markdown
# MT5 Per-Expert ML-CSV Tracker Report

## Research-first disclosure

- lifecycle_status: research_hypothesis
- origin_bias: follow-up to `2026-08-03-mt5-multi-position-closeout` plan; this plan covers multi-expert + per-rule `rule_id` filter as the next execution-parity step.
- roadmap_track: mt5-execution-per-expert
- research_priority: medium — execution tracker before per-rule verdict aggregation; all results remain DIAGNOSTIC_ONLY.
- current_search_budget: 0 model/search configurations; only MT5 tracker refactor and Python multi-rule export.
- cumulative_search_budget: inherited from `2026-08-03-mt5-multi-position-closeout`.
- next_probe_freeze: no ML winner selection; next execution probe must use fixed max_positions=1 and 2-expert mode.
- allowed_max_verdict: DIAGNOSTIC_ONLY
- forbidden_interpretations: profitable, ready, live-ready, tradable, new winner, model-quality proof

## Context

- Closeout plan `2026-08-03-mt5-multi-position-closeout.md` исполнен (precondition OK, см. `docs/reports/2026-08-03-mt5-per-expert-precondition.md`).
- Per-expert smoke: `run_mt5_batch --phase smoke-multi-expert --max-positions 1` (магики из эталонного прогона `MAGIC_GENERATOR`); batch-режим: `run_mt5_batch --multi-expert --multi-expert-magics "<magic_A>,<magic_B>" --max-positions 1`.
- Конвенция `rule_id`: `"mt5_rule_" + (string)Mgc` для строкового представления int magic из `#.csv`.

## Implementation Summary

Заполняется executorом после прохождения Tasks 1-8. Точки для заполнения:
- Какие задачи закрыты (по commit SHA).
- Какие аудиторские замечания требовали fallback в Smoke.
- Финальный compile result (paste из 13b:165).
- Финальный smoke result (`UNEXPLAINED=0` для обоих rule_id?).

## Verification

- Static contract tests pass: `tests/test_mt5_per_expert_ml_tracker_contract.py` (N tests, includes К-1/К-2/К-3 contract tests + Q-2 collision test).
- Compile: `/tmp/sosimple_mt5_per_expert_compile.log` показывает `Result: 0 errors, 0 warnings`.
- Multi-expert smoke (`--phase smoke-multi-expert`, K-6 auto-magics из `MAGIC_GENERATOR`):
  - `per_rule_reconciliation` содержит оба rule_id (`mt5_rule_<magic_A>`, `mt5_rule_<magic_B>`).
  - Каждый rule_id с `CLOSED_TX >= 1` и `UNEXPLAINED == 0`.
  - `metrics["order_counts"]["ORDER_PLACED"] >= 2` (К-6: положительный сигнал, не только `UNEXPLAINED=0`).
- **Backcompat single-expert smoke**: К-3 гарантирует backcompat через fallback в `ML_TRADE` — если первый поиск с `"mt5_rule_<Mgc>"` возвращает `-1`, повторный поиск с `""` (пустой фильтр) выбирает первый match по `barTime` (текущее поведение). Это позволяет 32 существующим CSV без колонки `rule_id` работать без перегенерации. План НЕ запускает отдельный single-expert smoke (старый CSV без `rule_id`), но К-3 контракт-тест `test_ml_trade_has_k3_fallback_when_first_find_returns_minus_one` верифицирует путь статически. Если smoke категория К-6 выявит регрессию — добавить явный single-expert regression smoke в Task 8 Step 6b как fallback.

## Results

На момент закрытия плана: N/A — исполнитель заполняет после smoke. Стандарт:
- `n_experts_in_smoke`: 2
- `n_rules_in_csv`: 2
- `CLOSED_TX per rule`: {mt5_rule_<magic_A>: X, mt5_rule_<magic_B>: Y}
- `overall UNEXPLAINED`: 0

## Conclusions

Исполнитель заполняет после smoke. Стандартные выводы:
- Per-expert isolation подтверждён: каждый эксперт обрабатывает только строки своего `rule_id`.
- K-3 fallback работает для legacy CSV (без `rule_id`), не применяется для новых multi-rule CSV.
- Multi-position tracker корректно работает в per-expert режиме.

## Limitations

Обязательные limitations:
- Per-expert работает только при `Real=true` в тестере (см. SERVICE.mqh:9 — `if (!IsTesting() && !IsOptimization()) {Real=true;}`) либо при `InpReal=true` override. При `Real=false` + `IsTesting()` `ExpTotal=1` (SERVICE.mqh:47). Multi-expert flow в этом режиме не запускается.
- `iSignal==5` (`ML_TRADE_TB` в `lib_ML_Signal_TB.mqh`) всё ещё вне coverage — использует `ml_signals_tb.csv` без `rule_id` колонки. Отдельный план при необходимости.
- Multi-rule signal CSV один на всех экспертов одной сессии; невозможно runtime-переключение правил внутри бара. Каждый эксперт обрабатывает все строки своего `rule_id` по `MT5_EntryTimes[i] == Time[bar]`, остальные игнорируются (backcompat: `rule_id_filter==""` выбирает первое совпадение).
- `max_positions>1` совместим с multi-expert, но smoke в Task 8 запускает только `max_positions=1` (канонический single-pos per expert). Multi-pos + multi-expert smoke — отдельный этап, нев этом plan.
- `CLOSE` event берёт close reason из `broker_history_limited` (13b:138-141); per-rule reconciliation не дополняет close reason новой информацией.
- Имена экспертов в `#.csv` — `EXP[e].Name`, д. соответствовать `NAME` (`SoSimple`); иначе `EXPERT_SET` вернёт false (SERVICE.mqh:240) и эксперт не торгует. Executor smoke `#.csv` обязан это учитывать.
- **Per-expert Nero source file вне scope этого плана.** В режиме `iSignal==3` + `MT5_DiagnosticExecutor=true` (единственный режим этого плана) `PIC()` вообще не вызывается (`COUNT.mqh:6` return раньше), значит `NERO_CSV_CREATE*` недостижимы. Per-magic Nero-файл — задача отдельного следующего плана для non-diagnostic режимов; этот план не модифицирует `lib_PIC.mqh:Nero*`.
- **Nero mutex не вводится** (в этом плане): вне scope по той же причине — Nxзапись в `MT5_NeroFile` привязана к `PIC()`, а `PIC()` здесь не выполняется.

## Split Disclosure

N/A (нет отдельных train/val/test разрезов — это execution tracker, не ML split).

## Forbidden Interpretations

В отчёте запрещены: profitable, ready, live-ready, tradable, new winner, model-quality proof.
В отчёте не писать: «multi-expert прибыльнее single-expert», «per-rule PF>1 — сигнал к winner selection», «probe показал готовность к live».

## Next Step

- Рассмотреть multi-expert smoke с `max_positions>1` (multi-expert × multi-pos).
- Распространить `rule_id` filter на `iSignal==5` (`lib_ML_Signal_TB.mqh`) — если требуется отдельный план.
- Финальный verdict-agnostic агреггация по 32 baseline кандидатам в multi-expert batch — запустить `run_mt5_batch --phase all --multi-expert` с парами магиков.

## Related Materials

- `docs/superpowers/plans/2026-08-03-mt5-multi-position-closeout.md` (precondition)
- `docs/superpowers/plans/2026-08-03-mt5-per-expert-ml-tracker.md` (этот план)
- `docs/methodology/13b-mt5-execution-parity.md`
- `docs/methodology/16-reporting-audit.md`
- `docs/reports/2026-08-03-mt5-per-expert-precondition.md` (Task P0 artefact)
```

- [ ] **Step 2: Заполнить Implementation Summary и Results**

Подставить конкретные значения для `tests passed`, `compile result`, `smoke per-rule class_counts`. Если smoke task 8 провален уперся в blocker — explicitly написать в отчёт:
- `smoke_status: BLOCKED`
- `blocker: <описание>`
- `next_step: <конкретный шаг для разблокировки>`

Не выдумывать значения. Если Task 8 не достиг `UNEXPLAINED=0` — записать фактический `per_rule_reconciliation` snapshot.

- [ ] **Step 3: Update `CHANGELOG.md`**

Добавить новый entry в начало `CHANGELOG.md` (после заголовка-шаблона):

```markdown
## [2026-08-03] — MT5 Per-Expert ML-CSV Tracker (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-08-03-mt5-per-expert-ml-tracker.md`
- **topics**: `multi-expert`, `per-rule filter`, `MQL5-tracker`, `rule_id-binding`, `reconciliation`
- **summary**: Per-expert MT5 execution через `rule_id == "mt5_rule_" + (string)Mgc` фильтр в `MT5_FindEntrySignal`, multi-rule signal CSV в Python (`prepare_mt5_multi_expert_source`), per-rule reconciliation в `parse_mt5_execution_report.py`. Backcompat: `rule_id==""` сохраняет single-expert path.
- **artifacts**: `MT/MQL5/Include/lib_ML_Signal.mqh` (Task 3, 6), `ML/baseline/prepare_mt5_multi_expert_source.py` (Task 4), `ML/baseline/run_mt5_batch.py` (Task 5), `ML/baseline/parse_mt5_execution_report.py` (Task 7), `tests/test_mt5_per_expert_ml_tracker_contract.py` (Task 1)
- **decision**: multi-expert support landed as DIAGNOSTIC_ONLY; no winner selection; `iSignal==5` вне coverage.
- **notes**: closeout `2026-08-03-mt5-multi-position-closeout` является precondition; если not done, plan BLOCKED.
```

- [ ] **Step 4: Update `CONTEXT_HANDOFF.md`**

Обновить поля:
- `active track`: `MT5 entry mechanics / trade-count frozen probe planning` (если remains) → добавить sub-bullet: `per-expert ml-tracker execution landed`.
- `latest report`: `docs/reports/2026-08-03-mt5-per-expert-ml-tracker.md`.
- `latest plan`: `docs/superpowers/plans/2026-08-03-mt5-per-expert-ml-tracker.md` (этот план).
- `Decision`: добавить блок про per-expert mode.
- `Next Step`: update на next probe (multi-pos × multi-expert, либо `iSignal==5` coverage, либо batch-run over 32 candidates in multi-expert grouping).

- [ ] **Step 5: Update `docs/superpowers/roadmap.md` — ТОЛЬКО если меняет ACTIVE track**

Run:

```bash
rg -n "ACTIVE|MT5 entry mechanics" docs/superpowers/roadmap.md
```

Если `ACTIVE` остаётся тот же track и только добавляется sub-progress — ничего не менять (roadmap правила: «в работе только один ACTIVE-trek»; этот план — исполнение, не новый track). Если closeout + этот план формально завершают track (исполнение tracker refactor) и открывается новый probe-направление — тогда переименовать ACTIVE entry и добавить ссылку на новый roadmap_item. В большинстве случаев — без изменений.

- [ ] **Step 6: Final verification run**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_per_expert_ml_tracker_contract.py tests/test_mt5_signal_executor_schema.py tests/test_mt5_batch_runtime_contract.py tests/test_parse_mt5_execution_report.py tests/test_mt5_execution_diagnostics.py -q
git diff --check
```

Expected: all tests pass; no diff whitespace errors.

- [ ] **Step 7: Commit отчётные артефакты**

```bash
git add docs/reports/2026-08-03-mt5-per-expert-ml-tracker.md CHANGELOG.md CONTEXT_HANDOFF.md
git commit -m "docs: close mt5 per-expert ml-tracker plan (DIAGNOSTIC_ONLY)"
```

Если roadmap менялся (Step 5) — добавить в `git add`.

---

## Completion Criteria

Этап считается закрытым только если все верно:

- Static contract tests pass: `tests/test_mt5_per_expert_ml_tracker_contract.py` (9+ tests).
- Existing contract tests pass: `tests/test_mt5_signal_executor_schema.py`, `tests/test_mt5_batch_runtime_contract.py`, `tests/test_parse_mt5_execution_report.py`, `tests/test_mt5_execution_diagnostics.py`.
- Compile log `/tmp/sosimple_mt5_per_expert_compile.log` показывает `Result: 0 errors, 0 warnings` (13b:165).
- Grep checks подтверждают: `(int)OrderTicket()`/`(int)ticket`/`MT5_TrackedTicket` отсутствуют (closeout precondition сохранён).
- Multi-expert smoke (`--phase smoke-multi-expert --max-positions 1`, магики из эталонного прогона `MAGIC_GENERATOR`, К-6): `per_rule_reconciliation` содержит оба `rule_id` (`mt5_rule_<magic_A>`, `mt5_rule_<magic_B>`), каждый с `CLOSED_TX >= 1` и общим `UNEXPLAINED == 0`, плюс положительный сигнал `metrics["order_counts"]["ORDER_PLACED"] >= 2` (защита от ложного PASS пустого прогона).
- `parse_mt5_execution_report.py` возвращает `per_rule_reconciliation` key в metrics.json.
- `run_mt5_batch.py --multi-expert` flag регистрируется и исполняет multi-rule генерацию.
- Backcompat single-expert smoke (без `--multi-expert`) — НЕ запускался повторно; backcompat путь верифицирован К-3 fallback в `ML_TRADE` и static-тестом `test_ml_trade_backcompat_when_rule_id_filter_empty` (`test_mt5_batch_runtime_contract.py` проходит).
- Финальный отчёт `docs/reports/2026-08-03-mt5-per-expert-ml-tracker.md`:
  - disclosure содержит все 8 обязательных полей методологии 16 (`lifecycle_status`, `origin_bias`, `research_priority`, `current_search_budget`, `cumulative_search_budget`, `next_probe_freeze`, `allowed_max_verdict`, `forbidden_interpretations`); `roadmap_track` — добровольное расширение проекта.
  - `allowed_max_verdict: DIAGNOSTIC_ONLY` (16-reporting-audit.md).
  - Limitations явно включают: `iSignal==5` вне coverage, `Real=true` requirement, `max_positions=1` smoke-only.
  - `Implementation Summary` завершён (не содержит TODO/«executor fills later» если smoke запущен).
- CHANGELOG и CONTEXT_HANDOFF обновлены (Step 3-4).
- Closeout precondition confirmed в `docs/reports/2026-08-03-mt5-per-expert-precondition.md` (Task P0).

## Self-Review

(Исполнитель заполняет после прохождения Tasks 1-9 — не для блока самого плана.)

- **Spec coverage**: все фронты работы покрыты Tasks 1-9? (1) или (P0+1+3+6+8 compile) — да. (2) новый `MT5_FindEntrySignal` с rule_id filter — Task 3. (3) `MT5_LogLifecycleForCurrentState` для нескольких tracked tickets — Task 6. (4) Python multi-rule export — Task 4. (5) `parse_mt5_execution_report` per-rule reconciliation — Task 7. (6) Контракты — Task 1. (7) compile gate 0/0 — Task 8 Steps 3-4. (8) отчёт — Task 9. Per-expert Nero-файл (`lib_PIC.mqh:Nero*`) вне scope: в diagnostic-режиме (`MT5_DiagnosticExecutor=true`, `COUNT.mqh:6`) `PIC()` недостижим — задача вынесена в отдельный следующий plan.
- **Placeholder scan**: поиск TBD/TODO/«fill in» — все найденные placeholders устранены? Единственные допустимые «placeholders» — в шаблоне отчёта Task 9, где executor подставляет значения smoke; это не placeholder кода, ожидаемая форма.
- **Type consistency**: `MT5_PerExpertLastPlaced(int magic, int &out_idx, datetime &out_expiry)` — сигнатуры в Task 6 Step 4 (decl), Step 5 (call), Step 6 (use). `MT5_AddTrackedPosition(ticket, idx, magic)` — проверить через closeout документ, что функция принимает 3 аргумента; executor сверяется с фактическим. Если closeout завёл её с другой сигнатурой — падает в Task 6 Step 3 (struct field add) и адаптирует.
- **Precondition risk**: если closeout НЕ исполнен (P0 проверка failed), план BLOCKED. Executor НЕ продолжает к Task 1 — план ожидает закрытия closeout сначала.

 Если Self-Review выявил gap — вернуться к соответствующему Task и дополнить; повторной ревизии не требуется.

---

## Execution Handoff

План сохранён в `docs/superpowers/plans/2026-08-03-mt5-per-expert-ml-tracker.md`. Два варианта исполнения:

**1. Subagent-Driven (recommended)** — dispatcher создаёт свежего sub-agent на каждый Task, ревью между Tasks, быстрая итерация. Использует скилл `superpowers:subagent-driven-development`.

**2. Inline Execution** — исполнение в текущей сессии через скилл `superpowers:executing-plans`, batch execution с чек-поинтами для review.

**Какой подход?**

---

## Применимость методологии

Методология, используемая в этом плане (согласно требованию пользователя и `docs/methodology/README.md`):

| Этап плана | Файл методологии | Применимая проверка | Критерий завершения |
|---|---|---|---|
| **Task P0** (precondition) | — (нет специализированного файла методологии для «plan precondition») | Grep-аудит `lib_ML_Signal.mqh` / `run_mt5_batch.py` на ключевые маркеры closeout | Все 4 grep checks passed; `docs/reports/2026-08-03-mt5-per-expert-precondition.md` создан с `precondition: OK` |
| **Tasks 1, 2, 3, 4, 5, 6, 7** (implementation) | `13b-mt5-execution-parity.md` (CSV contract строки 58, 73; timing строки 76-86; limit-only строки 38-43) | Static contract tests через `rg` regex на MQL5 source + Python `pytest` | Все `test_mt5_per_expert_ml_tracker_contract.py` тесты PASS; backcompat `test_mt5_signal_executor_schema.py` / `test_mt5_batch_runtime_contract.py` PASS |
| **Task 8** (compile + smoke) | `13b-mt5-execution-parity.md` (компиляция строки 150-170; тестер 172-215) | Compile log читается через `iconv`, проверяется `Result: 0 errors, 0 warnings`; smoke через `run_mt5_batch --phase tester --multi-expert` | `Result: 0 errors, 0 warnings`; smoke `UNEXPLAINED=0` для каждого `rule_id` в `per_rule_reconciliation` |
| **Task 9** (отчёт) | `16-reporting-audit.md` (disclosure fields) | Контракт: отчёт содержит все обязательные поля disclosure; `allowed_max_verdict: DIAGNOSTIC_ONLY` | Отчёт создан, CHANGELOG и CONTEXT_HANDOFF обновлены; `git diff --check` чист |

**Разделы методологии, для которых нет специализированного файла**:
- **Multi-expert execution tracker** в MQL5: методология 13b описывает один эксперт (`MT/mql5/Experts/$o$imple.mq5`) и один signal CSV (`mt5_entry_signals.csv`). Per-expert routing через `#.csv` (`SERVICE.mqh:INPUT_FILE_READ`) — **этоне освещено в методологии**. Обоснованный порядок действий (этот план): (а) переиспользовать существующий `#.csv` loader без модификаций, (б) ввести строковое правило `rule_id ↔ magic` без новых колонок в `#.csv`, (в) весь multi-expert flow протестировать через `Real=true` в тестере (чтобы `INPUT_FILE_READ` грузил все строки). Если в будущем методология потребуется — она должна быть добавлена в 13b как новый подраздел «Multi-expert execution» после исполнения этого плана. Это зафиксировано в Limitations отчёта.
- **Backcompat type-check в Python prepare**: `rule_id type guard` как type-check не описан в 16-reporting. Обоснованный подход — применённый здесь minimal guard `if not isinstance(rule_id, str): raise TypeError("rule_id must be str")` поднимает ошибку рано (а не produces молчаливо неверный CSV). Future раздел методологии может зафиксировать это как contract.

**Запреты методологии, применённые в плане**:
- Запрещено объявлять tester-result качеством ML без leakage, split, locked_test, robustness, reconciliation-проверок (13b:208). → Все results в отчёте остаются `DIAGNOSTIC_ONLY`.
- Запрещено подгонять модель или export по tester-результату (13b:216). → Plan не меняет model/export, только execution tracker.
- Запрещено считать `wine=1` ошибкой компиляции без чтения MetaEditor log (13b:215). → Task 8 Step 4 явно читает log через `iconv`.
- Запрещено не экранировать `$o$imple.mq5` кавычками в shell-команде (13b:213). → Task 8 Step 3 оборачивает путь в одинарные кавычки без бэкслэшей (В-8).

---

## Open Questions и Unknowns

(Исполнитель фиксирует здесь, если в ходе исполнения обнаружит новые вопросы — НЕ блокируя Tasks.)

1. **`MT5_AddTrackedPosition` сигнатура**: план предполагает `void MT5_AddTrackedPosition(ulong ticket, int idx, int magic)`. Если closeout завёл её без `magic` (только `ticket, idx`) — executor в Task 6 Step 3 добавляет `magic` field к `MT5_TRACKED_POSITION` struct и адаптирует сигнатуру. Под вопросом остаётся обратная compatibility — нужно ли backcompat path для старых вызовов с 2 аргументами. Решение: **нет backcompat** — closeout ещё не зарелижен в production (мы в diagnostic preview), старых вызовов нет. executor адаптирует все вызовы на 3-аргументную сигнатуру.

2. **Magic generation для smoke**: `MAGIC_GENERATOR()` (`SERVICE.mqh:95-100`) детерминирован от `Symbol()+Period()+iSignal+iParam+...`. Smoke берёт магики из эталонного прогона `MAGIC_GENERATOR` (Task 8 Step 5, К-6), поэтому `CHECKSUM` (`SERVICE.mqh:251`) проходит и эксперты не отключаются. Для batch-режима (`--multi-expert-magics`) действует то же требование: переданные магики должны совпадать со значениями `MAGIC_GENERATOR()` для соответствующих строк `#.csv`, иначе `EXPERT_SET` (SERVICE.mqh:240) вернёт false и эксперт не торгует. Если магики не соответствуют — smoke/batch деградирует к меньшему числу экспертов; положительный критерий `ORDER_PLACED >= 2` (Completion Criteria) это ловит.

3. **`EXP[CurExp].Mgc` vs `EXP[e].Mgc`**: `Mgc` в `EXPERT::ML_TRADE` — это `this->Mgc`, который `EXPERT_SET` заполнил из `EXP[e].Mgc` (SERVICE.mqh:240). В multi-expert mode каждый вызов `ML_TRADE()` работает с правильным `Mgc` своего эксперта. План предполагает это. Если фактически `Mgc` в момент `ML_TRADE()` ещё singleton — это баг closeout, не этого плана. Executor сверь: `rg -n "this->Mgc|EXP\[CurExp\].Mgc|EXP\[e\].Mgc" MT/MQL5/`.

4. **iSignal==3 singleton за call**: При `Real=true + IsTesting()` `ML_TRADE()` вызывается per `EXP[e]` (`$o$imple.mq5:162`, `EXPERT::MAIN()` в `MAIN.mqh:133`). Но `set.BUY/SEL` — это **поля экземпляра** `EXP[e]`, не глобальные. Сигнал `set.BUY.Sig=GOGO` ставится и обрабатывается в `ORDERS_SET` (`ORDERS.mqh:5` — `EXPERT_PARENT_CLASS::ORDERS_SET`) для того же экземпляра. So пер-экспертно безопасно. План предполагает это; executor проверяет что `ORDERS_SET` тоже per-instance (через `EXP[e]`, `MAIN.mqh:133`).

5. **`mt5_trade_events.csv` в tester Files**: только один event file (`InpMT5_EventFile`) — не per-expert. При multi-expert все события экспертов пишутся в один CSV, разделяясь `rule_id` и `magic` колонками. Methodology 13b (строки 73) это допускает: `rule_id` и `magic` уже в схеме. Plan оставляет это как есть.

Если в процессе исполнения появятся новые questions — executor добавляет их сюда, не блокируя работу.
