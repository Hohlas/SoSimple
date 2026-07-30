# MT5 Execution Loop Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Построить минимальный MT5-контур, где MT5 формирует `Nero.csv`-совместимый поток признаков, Python обучает/готовит ML-кандидатов, а исполнение сделок, fill лимиток, SL/TP и ML-close проверяются в MT5 Strategy Tester вместо самописного Python-симулятора.

**Architecture:** Переход делается как вертикальный прототип поверх существующего MQL5-порта `$o$imple.mq5`, а не как слепое создание нового параллельного советника. Минимальная MT5-версия обязана иметь два слоя: `Nero.csv` producer и tester execution. MT5 сначала формирует тот же тип рыночных строк, который сейчас даёт MT4 `Nero.csv`; Python отвечает за обучение, frozen metadata и подготовку entry/model artifacts; MQL5-советник в MT5 tester сам ставит лимитки, отслеживает фактический fill, считает признаки открытой позиции после fill, применяет простой экспортированный ML-exit слой или заранее зафиксированную диагностическую модель и пишет machine-readable event log. Python затем парсит MT5 deals/events и считает метрики. Новый минимальный `SoSimpleMT5SignalExecutor.mq5` допустим только как fallback, если аудит покажет, что текущий `$o$imple.mq5` не компилируется или слишком связан для безопасного прототипа.

**Tech Stack:** `./.venv/bin/python`, pandas, pytest, CSV/JSON, MQL5, MT5 Strategy Tester, `MT/MQL5/`, `ML/baseline/`, `ML/reports/`, `docs/reports/`.

## Global Constraints

- Работать на текущей ветке, не делать `git push` без явной просьбы пользователя.
- Не запускать полный suite `./.venv/bin/python -m pytest tests/ -q`.
- Не удалять и не переписывать текущий MT4-контур; MT5-контур создаётся рядом с ним.
- Не считать MT5-прототип доказательством прибыльности, пока не пройдены feature contract, split/freeze, tester reconciliation и отчётный audit.
- Статус первого MT5-контура: `DIAGNOSTIC_ONLY`.
- Python не должен финально выбирать кандидата по самописному trade PF/PnL/DD, если исполнение должно проверяться MT5.
- MT5 tester решает только execution-проблему; он не доказывает честность ML-признаков. Feature leakage gate остаётся обязательным.
- Минимальный MT5-контур должен уметь генерировать `Nero.csv`-совместимый файл или явно доказать, что временно использует read-only legacy `Nero.csv` только для механической диагностики. Для рабочего перехода `Nero.csv` producer обязателен.
- Для текущей стратегии с ML-анализом открытой позиции ML-exit нельзя заранее выгружать как “судьбу Python-сделки”, если фактический fill ещё не получен от tester.
- `bars_since_fill=0` не является рабочим ML-exit решением без отдельного post-fill decision timestamp.
- Проектный MT5-каталог известен: `MT/MQL5`. Это не путь к `terminal64.exe`, а существующая попытка порта `$o$imple` на MQL5.
- Если установленный MT5 terminal executable не доступен агенту, план должен завершиться на подготовке исходников, схем, файлов и ручных инструкций для пользователя.

## Unknowns / Questions To Resolve Before Full Automation

- Доступен ли командный запуск MT5 Strategy Tester из текущей среды агента.
- Какой режим MT5 tester использовать как основной для XAUUSD H1: real ticks, generated ticks или control/open prices. Для parity лучше real/generated ticks, но скорость может быть blocker.
- Доступна ли в текущем билде MT5 поддержка ONNX для нужной модели. Если нет, первый прототип должен использовать простую экспортируемую модель или rule-based scorer.
- Требуется ли netting или hedging account mode. Для прототипа предпочтителен one-position-per-rule режим.

## Design Decision

Принятый целевой путь для первого этапа:

```text
MT5 Nero.csv export -> Python train/export -> MT5 tester execution -> Python parser/metrics
```

Базовый MQL5 target:

```text
MT/MQL5/Experts/$o$imple.mq5
```

Fallback target только после явного решения:

```text
MT/MQL5/Experts/SoSimpleMT5SignalExecutor.mq5
```

Не использовать на первом этапе:

- новый параллельный MQL5-советник без аудита существующего `$o$imple.mq5`;
- запуск Python-кода внутри MT5 tester;
- полный grid-search через MT5 для сотен/тысяч комбинаций;
- ONNX как обязательное условие прототипа.

Первый прототип проверяет одно правило и один символ. После него можно расширять до batch-run 20-50 кандидатов.

## Methodology Map

- `docs/methodology/README.md`: торговый результат нельзя считать качеством модели, пока данные, признаки, split, export и execution не соответствуют моменту решения.
- `docs/methodology/03-feature-contract-leakage.md`: перед MT5-прогоном нужен feature contract; future-derived поля не входят в input; `decision_time` фиксируется явно.
- `docs/methodology/06-temporal-split.md`: MT5 batch selection нельзя проводить на already-open locked_test без статуса `DIAGNOSTIC_ONLY`.
- `docs/methodology/09-validation-freeze.md`: перед настоящим MT5 locked_test нужно заморозить rule/model/export contract на validation.
- `docs/methodology/10-frozen-test-oos.md`: изменение execution engine после freeze требует нового цикла или понижает статус до `DIAGNOSTIC_ONLY`.
- `docs/methodology/12-backtest-costs.md`: tester execution, spread, commission, slippage, missed opens, latency и close reasons должны быть частью отчёта.
- `docs/methodology/13-export-mt4-parity.md`: применить тот же смысл к MT5: доказать, что tester исполняет тот же signal/model contract, который выбран Python.
- `docs/methodology/13b-mt5-execution-parity.md`: использовать MT5-specific paths, MetaEditor compile command, compile verdict по UTF-16LE log и обязательную проверку `.ex5`.
- `docs/methodology/16-reporting-audit.md`: все команды, paths, hashes, artifacts, limitations и invalidated assumptions фиксируются в отчёте.

---

### Task 1: MT5 Feasibility And Local Layout

**Files:**
- Read: `MT/README.md`
- Read: `MT/MQL5/Experts/$o$imple.mq5`
- Read: `MT/MQL5/Include/lib_ML_Signal.mqh`
- Create: `docs/reports/2026-07-29-mt5-feasibility.md`
- Create: `ML/reports/mt5_execution_loop/mt5_environment_manifest.json`

**Interfaces:**
- Consumes: existing MT4/MT5 repository layout.
- Produces: environment manifest used by later tasks.

**Applicable Methodology:**
- `docs/methodology/01-raw-data-inventory.md`: source, producer, timezone, symbol and history availability.
- `docs/methodology/12-backtest-costs.md`: tester data and execution mode must be known before interpreting metrics.
- `docs/methodology/13b-mt5-execution-parity.md`: MT5 terminal path, MetaEditor compile command and `.ex5` freshness must be checked.

**Mandatory Checks:**
- Confirm whether `MT/MQL5/Experts/$o$imple.mq5` compiles or is only legacy/experimental source.
- Confirm whether existing MQL5 `lib_ML_Signal.mqh` can be adapted for MT5 execution-loop logging and post-fill ML-exit features.
- Confirm whether an MT5 terminal executable path is known.
- Confirm whether command-line tester can be run by agent; if not, mark manual step.
- Record account mode assumption: `one_position_per_rule`.

**Completion Criterion:**
- `mt5_environment_manifest.json` exists and states `automation_status`: `agent_can_run_tester`, `manual_user_run_required`, or `unknown`.

- [ ] **Step 1: Inspect current MT5 source presence**

Run:

```bash
rg --files MT/MQL5 | rg 'Experts|Include/lib_ML|Include/Trade|README'
```

Expected:

```text
MT/MQL5/Experts/$o$imple.mq5 and MQL5 include files are listed.
```

- [ ] **Step 2: Write environment manifest generator**

Create `ML/reports/mt5_execution_loop/mt5_environment_manifest.json` with this structure:

```json
{
  "status": "DIAGNOSTIC_ONLY",
  "mt5_source_root": "MT/MQL5",
  "mt5_terminal_executable_path": "/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/terminal64.exe",
  "mt5_metaeditor_executable_path": "/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe",
  "mt5_compile_log": "/tmp/sosimple_mt5_compile.log",
  "agent_can_run_mt5_tester": false,
  "manual_user_run_required": true,
  "symbol": "XAUUSD",
  "timeframe": "H1",
  "execution_mode_preference": "real_ticks_or_generated_ticks",
  "account_mode_assumption": "one_position_per_rule",
  "source_layout": {
    "mt5_expert_primary": "MT/MQL5/Experts/$o$imple.mq5",
    "mt5_ml_signal_include_primary": "MT/MQL5/Include/lib_ML_Signal.mqh",
    "mt5_new_expert_fallback_only": "MT/MQL5/Experts/SoSimpleMT5SignalExecutor.mq5",
    "python_output_dir": "ML/reports/mt5_execution_loop",
    "mt5_files_dir_planned": "DISCOVER_WITH_TERMINAL_DATA_PATH_OR_FILE_COMMON"
  },
  "blocking_unknowns": [
    "whether agent can invoke MT5 tester",
    "whether selected model can be exported to ONNX or simple MQL5 scorer"
  ]
}
```

- [ ] **Step 3: Write feasibility report**

Create `docs/reports/2026-07-29-mt5-feasibility.md`:

```markdown
# MT5 Execution Loop Feasibility

> **Дата**: 2026-07-29
> **Статус**: Draft
> **Вердикт**: DIAGNOSTIC_ONLY

## Goal

Проверить, можно ли использовать MT5 Strategy Tester как источник торговых метрик вместо Python-симулятора исполнения.

## Findings

- MT5 source directory exists: `MT/MQL5/`.
- Existing MT5 source root: `MT/MQL5`.
- Existing MT5 expert path: `MT/MQL5/Experts/$o$imple.mq5`.
- Existing MT5 ML include: `MT/MQL5/Include/lib_ML_Signal.mqh`.
- First migration target is the existing `$o$imple.mq5` port if it compiles and can be safely instrumented.
- Minimal `SoSimpleMT5SignalExecutor.mq5` is fallback only.

## Unknowns

- MT5 terminal path is known: `/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/terminal64.exe`.
- MetaEditor path is known: `/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe`.
- Automated tester launch is unknown.
- ONNX/model execution path is unknown.
- Compile status of existing `$o$imple.mq5` must be checked with the `13b` MetaEditor command before tester run.

## Decision

Proceed with source-level prototype and manual tester handoff until MT5 terminal automation is confirmed.
```

- [ ] **Step 4: Verify files exist**

Run:

```bash
test -f ML/reports/mt5_execution_loop/mt5_environment_manifest.json
test -f docs/reports/2026-07-29-mt5-feasibility.md
```

Expected:

```text
Both commands exit 0.
```

---

### Task 1A: MT5 `Nero.csv` Producer Parity

**Files:**
- Modify: `MT/MQL5/Experts/$o$imple.mq5`
- Modify: `MT/MQL5/Include/lib_PIC.mqh`
- Read: `MT/MQL4/Include/lib_PIC.mqh`
- Read: `docs/MT/lib_PIC.mqh.md`
- Create: `docs/schemas/mt5_nero_csv_contract.md`
- Create: `ML/reports/mt5_execution_loop/mt5_nero_parity_manifest.json`

**Interfaces:**
- Consumes: existing MT4 `NERO_CSV_CREATE()` contract and MQL5 port.
- Produces: MT5-generated `Nero.csv`-compatible file for Python processing.

**Applicable Methodology:**
- `docs/methodology/01-raw-data-inventory.md`: producer, source, timezone, symbol and field availability must be explicit.
- `docs/methodology/03-feature-contract-leakage.md`: `Nero.csv` fields must be available at row decision time; no future labels in producer output.
- `docs/methodology/13-export-mt4-parity.md`: MT5 producer output must be count/hash/row compared against MT4/current dataset before use.

**Mandatory Checks:**
- MT5 can write a `Nero.csv`-compatible file from tester/runtime history.
- Column order and delimiter match the Python processing expectation or are documented with an adapter.
- `fractal0` ordering and `time` convention are compared against MT4 `Nero.csv` on the same interval.
- Every `fractal0..fractal99` cell has exactly 23 colon-separated fields:
  `T:P:Dir:FrntVal:BackVal:Strong:Brk:Rev:PwrSum:Cnt:Imp:Up12:Dn12:Up24:Dn24:Up48:Dn48:Up3:Dn3:Up6:Dn6:FractalAtr:Shift`.
- MT5 producer writes the 23rd `Shift` field exactly like MT4: `SHIFT(F[f].T) - cur_bar`.
- MT5 `Nero.csv` is producer data only; it must not contain Python labels, future exit times, Python fill times or PnL.
- If full parity is not reached, downstream training status remains `DIAGNOSTIC_ONLY`.

**Completion Criterion:**
- A user/agent can generate MT5 `Nero.csv`, and `mt5_nero_parity_manifest.json` records whether it is `PASS`, `FAIL`, `UNKNOWN` or `DIAGNOSTIC_ONLY` against the MT4/Python input contract.

- [ ] **Step 1: Locate existing MQL5 Nero producer hooks**

Run:

```bash
rg -n "NERO_CSV_CREATE|fractal0|FileWrite|Nero.csv|PIC\\(" MT/MQL5/Experts/'$o$imple.mq5' MT/MQL5/Include/lib_PIC.mqh MT/MQL5/Include/MAIN.mqh MT/MQL4/Include/lib_PIC.mqh
```

Expected:

```text
Existing MT4 and MQL5 producer functions or missing MQL5 gaps are visible.
```

- [ ] **Step 2: Write MT5 Nero CSV contract**

Create `docs/schemas/mt5_nero_csv_contract.md`:

```markdown
# MT5 Nero.csv Producer Contract

> **Status**: required for MT5 execution-loop migration.

## Goal

MT5 must be able to generate a `Nero.csv`-compatible market feature stream.
Without this producer, MT5 can only test execution of already prepared Python
signals and cannot become the source of truth for the full live/test cycle.

## Required Properties

- Producer: `MT/MQL5/Experts/$o$imple.mq5` via MQL5 `lib_PIC.mqh`.
- Output role: raw/runtime input for Python processing.
- Forbidden output: Python labels, Python simulated fill, Python exit time, PnL.
- Time convention: H1 row time must match the current MT4/Python convention and be documented in parity manifest.
- Delimiter: semicolon.

## Parity Checks

Compare MT5-generated `Nero.csv` against current MT4/Python source on the same
symbol, timeframe and interval:

- row count;
- min/max time;
- duplicate time count;
- column names/order;
- `fractal0..fractal99` parse success;
- `len(fractalN.split(':')) == 23` for every non-empty fractal field;
- 23rd nested field is `Shift`;
- full nested format agreement against MT4 on sampled rows;
- `fractal0.direction` agreement rate;
- `fractal0.price` difference summary.

## Verdict

If MT5 `Nero.csv` parity is not proven, any downstream MT5 ML result remains
`DIAGNOSTIC_ONLY`.
```

- [ ] **Step 3: Add manifest template**

Create `ML/reports/mt5_execution_loop/mt5_nero_parity_manifest.json`:

```json
{
  "status": "UNKNOWN",
  "allowed_max_verdict_until_parity": "DIAGNOSTIC_ONLY",
  "producer": "MT/MQL5/Experts/$o$imple.mq5",
  "source_symbol": "XAUUSD",
  "source_timeframe": "H1",
  "mt5_nero_csv": "USER_FILLS_AFTER_EXPORT",
  "reference_nero_csv": "USER_FILLS_AFTER_EXPORT",
  "checks": {
    "row_count": "UNKNOWN",
    "time_range": "UNKNOWN",
    "duplicate_time_count": "UNKNOWN",
    "column_contract": "UNKNOWN",
    "fractal_parse_success": "UNKNOWN",
    "fractal_nested_field_count_23": "UNKNOWN",
    "shift_field_present": "UNKNOWN",
    "sampled_full_nested_format_agreement": "UNKNOWN",
    "fractal0_direction_agreement": "UNKNOWN",
    "fractal0_price_diff_summary": "UNKNOWN"
  }
}
```

- [ ] **Step 4: Add or repair MT5 producer only after reading existing code**

If `MT/MQL5/Include/lib_PIC.mqh` already has `NERO_CSV_CREATE(...)`, adapt it minimally to write the same raw columns as MT4. If it does not, port only the producer path from `MT/MQL4/Include/lib_PIC.mqh`; do not port unrelated trading logic.

Known gap to fix first: current MQL5 `NERO_CSV_CREATE(int cur_bar)` ends each fractal field at `FractalAtr`, while Python expects the MT4 23-field format with `Shift`. Add the final field to both normalized and raw MQL5 branches:

```cpp
":" + S0(SHIFT(F[f].T) - cur_bar)
```

Required guard in code:

```cpp
input bool InpMT5_ExportNero = false;
input string InpMT5_NeroFile = "Nero_MT5.csv";
```

Expected behavior:

```text
InpMT5_ExportNero=false -> no producer side effect.
InpMT5_ExportNero=true -> MT5 writes Nero-compatible rows on new H1 bars.
```

Both overloads `NERO_CSV_CREATE()` and `NERO_CSV_CREATE(int cur_bar)` must start with:

```cpp
if(!MT5_ExportNero)
   return;
```

All output file names must use `MT5_NeroFile`; no default-off tester run may create or append `Nero.csv`/`Nero_MT5.csv`.

- [ ] **Step 5: Static checks**

Run:

```bash
rg -n "InpMT5_ExportNero|InpMT5_NeroFile|NERO_CSV_CREATE|Nero_MT5.csv" MT/MQL5/Experts/'$o$imple.mq5' MT/MQL5/Include/lib_PIC.mqh docs/schemas/mt5_nero_csv_contract.md ML/reports/mt5_execution_loop/mt5_nero_parity_manifest.json
rg -n "SHIFT\\(F\\[f\\]\\.T\\) - cur_bar|if\\(!MT5_ExportNero\\)|MT5_NeroFile" MT/MQL5/Include/lib_PIC.mqh
```

Expected:

```text
All required producer symbols appear, or the report explicitly marks producer parity as UNKNOWN/manual.
```

---

### Task 2: Define MT5 Signal And Event Schemas

**Files:**
- Create: `docs/schemas/mt5_signal_executor_schema.md`
- Create: `tests/test_mt5_signal_executor_schema.py`
- Create: `ML/baseline/mt5_signal_schema.py`

**Interfaces:**
- Produces:
  - `MT5_SIGNAL_COLUMNS`
  - `MT5_EVENT_COLUMNS`
  - `validate_mt5_signal_frame(frame: pd.DataFrame) -> None`
  - `validate_mt5_event_frame(frame: pd.DataFrame) -> None`

**Applicable Methodology:**
- `docs/methodology/03-feature-contract-leakage.md`: feature/decision/execution timing must be explicit.
- `docs/methodology/13-export-mt4-parity.md`: export format, counts and hashes must be fixed.

**Mandatory Checks:**
- Schema separates entry signal from open-position ML-exit features.
- Entry rows must not contain future fill/exit time.
- Entry rows must include explicit timing fields: `feature_time`, `feature_available_time`, `decision_time`.
- Event rows must include enough fields for reconciliation: `event`, `time`, `feature_time`, `feature_available_time`, `decision_time`, `execution_time`, `rule_id`, `signal_time`, `ticket`, `side`, `requested_price`, `fill_price`, `stop_price`, `close_reason`, `profit`, `bars_since_fill`, `bid`, `ask`, `spread`, `slippage_points`, `commission`, `swap`, `balance`, `equity`, `order_open_price`, `order_close_price`, `entry_time`, `exit_time`.

**Completion Criterion:**
- Schema tests pass and document defines exact CSV columns.

- [ ] **Step 1: Write failing schema tests**

Create `tests/test_mt5_signal_executor_schema.py`:

```python
import pandas as pd
import pytest

from ML.baseline.mt5_signal_schema import (
    MT5_EVENT_COLUMNS,
    MT5_SIGNAL_COLUMNS,
    validate_mt5_event_frame,
    validate_mt5_signal_frame,
)


def test_mt5_signal_schema_rejects_future_exit_columns():
    frame = pd.DataFrame(
        [
            {
                "time": "2023.01.02 10:00",
                "feature_time": "2023.01.02 09:00",
                "feature_available_time": "2023.01.02 10:00",
                "decision_time": "2023.01.02 10:00",
                "rule_id": "rule01",
                "side": "BUY",
                "entry_type": "BUY_LIMIT",
                "limit_price": 1900.0,
                "stop_price": 1890.0,
                "atr": 10.0,
                "max_fill_lag_bars": 6,
                "future_exit_time": "2023.01.02 14:00",
            }
        ]
    )

    with pytest.raises(ValueError, match="future_exit_time"):
        validate_mt5_signal_frame(frame)


def test_mt5_signal_schema_accepts_entry_only_contract():
    frame = pd.DataFrame(
        [
            {
                "time": "2023.01.02 10:00",
                "feature_time": "2023.01.02 09:00",
                "feature_available_time": "2023.01.02 10:00",
                "decision_time": "2023.01.02 10:00",
                "rule_id": "rule01",
                "side": "BUY",
                "entry_type": "BUY_LIMIT",
                "limit_price": 1900.0,
                "stop_price": 1890.0,
                "atr": 10.0,
                "max_fill_lag_bars": 6,
            }
        ]
    )

    validate_mt5_signal_frame(frame)


def test_mt5_event_schema_requires_reconciliation_columns():
    assert {
        "event",
        "time",
        "feature_time",
        "feature_available_time",
        "decision_time",
        "execution_time",
        "rule_id",
        "signal_time",
        "ticket",
        "side",
        "requested_price",
        "fill_price",
        "order_open_price",
        "order_close_price",
        "stop_price",
        "close_reason",
        "profit",
        "bars_since_fill",
        "bid",
        "ask",
        "spread",
        "slippage_points",
        "commission",
        "swap",
        "balance",
        "equity",
        "entry_time",
        "exit_time",
    }.issubset(set(MT5_EVENT_COLUMNS))
```

- [ ] **Step 2: Run tests and confirm expected failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py -q
```

Expected:

```text
Fails because ML.baseline.mt5_signal_schema does not exist.
```

- [ ] **Step 3: Implement schema module**

Create `ML/baseline/mt5_signal_schema.py`:

```python
from __future__ import annotations

import pandas as pd


MT5_SIGNAL_COLUMNS = [
    "time",
    "feature_time",
    "feature_available_time",
    "decision_time",
    "rule_id",
    "side",
    "entry_type",
    "limit_price",
    "stop_price",
    "atr",
    "max_fill_lag_bars",
]

MT5_FORBIDDEN_SIGNAL_COLUMNS = {
    "fill_time",
    "exit_time",
    "future_exit_time",
    "future_favorable_r_3",
    "future_adverse_r_3",
    "hold_3_pnl_r",
    "pnl_r",
}

MT5_EVENT_COLUMNS = [
    "event",
    "time",
    "feature_time",
    "feature_available_time",
    "decision_time",
    "execution_time",
    "rule_id",
    "signal_time",
    "ticket",
    "side",
    "requested_price",
    "fill_price",
    "order_open_price",
    "order_close_price",
    "stop_price",
    "close_reason",
    "profit",
    "bars_since_fill",
    "bid",
    "ask",
    "spread",
    "spread_atr",
    "bar_open",
    "bar_high",
    "bar_low",
    "bar_close",
    "calculation_open",
    "slippage_points",
    "entry",
    "take_profit",
    "close",
    "swap",
    "commission",
    "hold_bars",
    "open_positions",
    "max_positions",
    "balance",
    "equity",
    "entry_time",
    "exit_time",
    "ml_exit_score",
    "ml_exit_decision",
    "comment",
]


def validate_mt5_signal_frame(frame: pd.DataFrame) -> None:
    missing = [col for col in MT5_SIGNAL_COLUMNS if col not in frame.columns]
    if missing:
        raise ValueError(f"missing MT5 signal columns: {missing}")
    forbidden = sorted(MT5_FORBIDDEN_SIGNAL_COLUMNS.intersection(frame.columns))
    if forbidden:
        raise ValueError(f"forbidden future/result columns in MT5 signal frame: {forbidden}")
    bad_side = set(frame["side"].astype(str)) - {"BUY", "SELL"}
    if bad_side:
        raise ValueError(f"unsupported side values: {sorted(bad_side)}")
    bad_entry = set(frame["entry_type"].astype(str)) - {"BUY_LIMIT", "SELL_LIMIT"}
    if bad_entry:
        raise ValueError(f"unsupported entry_type values: {sorted(bad_entry)}")


def validate_mt5_event_frame(frame: pd.DataFrame) -> None:
    missing = [col for col in MT5_EVENT_COLUMNS if col not in frame.columns]
    if missing:
        raise ValueError(f"missing MT5 event columns: {missing}")
```

- [ ] **Step 4: Write schema document**

Create `docs/schemas/mt5_signal_executor_schema.md`:

```markdown
# MT5 Signal Executor CSV Schema

> **Status**: diagnostic schema for MT5 Strategy Tester prototype.

## Entry Signal CSV

Path pattern:

```text
ML/reports/mt5_execution_loop/mt5_entry_signals_<run_id>.csv
```

Columns:

```text
time;feature_time;feature_available_time;decision_time;rule_id;side;entry_type;limit_price;stop_price;atr;max_fill_lag_bars
```

Forbidden columns:

```text
fill_time;exit_time;future_exit_time;future_favorable_r_3;future_adverse_r_3;hold_3_pnl_r;pnl_r
```

Reason: entry CSV describes decisions before tester fill. It must not contain
the future lifecycle of a Python-simulated trade.

## MT5 Event Log CSV

Path pattern:

```text
ML/reports/mt5_execution_loop/mt5_trade_events_<run_id>.csv
```

Columns:

```text
event;time;feature_time;feature_available_time;decision_time;execution_time;rule_id;signal_time;ticket;side;requested_price;fill_price;order_open_price;order_close_price;stop_price;close_reason;profit;bars_since_fill;bid;ask;spread;spread_atr;bar_open;bar_high;bar_low;bar_close;calculation_open;slippage_points;entry;take_profit;close;swap;commission;hold_bars;open_positions;max_positions;balance;equity;entry_time;exit_time;ml_exit_score;ml_exit_decision;comment
```

## Timing Contract

```text
feature_time <= decision_time <= execution_time
```

For ML-exit:

- `bars_since_fill=0` is not a working ML-exit decision.
- open-position features are computed by the MT5 expert after factual tester fill.
- first working ML-exit decision is allowed only after at least one closed H1 bar after fill.
- `feature_time`, `feature_available_time`, `decision_time` and `execution_time` must be material columns in signal/event CSV, not only prose in this document.
- If a decision is made at H1-open using the previous closed H1 bar, close execution may happen immediately after that decision; do not add an extra H1-bar delay.
```

- [ ] **Step 5: Run schema tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py -q
```

Expected:

```text
3 passed
```

---

### Task 3: Export Entry-Only MT5 Signals From Python

**Files:**
- Create: `ML/baseline/export_mt5_entry_signals.py`
- Modify: `tests/test_mt5_signal_executor_schema.py`
- Create: `ML/reports/mt5_execution_loop/README.md`

**Interfaces:**
- Consumes:
  - `validate_mt5_signal_frame(...)`
  - fixed11-like rule metadata or selected rule CSV
- Produces:
  - `export_mt5_entry_signals(...) -> pd.DataFrame`
  - `ML/reports/mt5_execution_loop/mt5_entry_signals_<run_id>.csv`
  - `ML/reports/mt5_execution_loop/mt5_entry_signals_<run_id>.json`

**Applicable Methodology:**
- `docs/methodology/03-feature-contract-leakage.md`: entry export cannot contain future fill/exit results.
- `docs/methodology/13-export-mt4-parity.md`: export counts and hashes are mandatory.

**Mandatory Checks:**
- Export contains only entry decisions and static risk parameters.
- Export has no `exit_time`, `pnl_r`, `fill_time` or future outcome fields.
- Hash, row counts, active/nonzero counts, side counts, duplicate times, source CSV hash, rule/model metadata and run config hash are written to JSON.

**Completion Criterion:**
- Python can generate a small deterministic MT5 entry CSV for one rule.

- [ ] **Step 1: Add exporter test**

Append to `tests/test_mt5_signal_executor_schema.py`:

```python
def test_export_mt5_entry_signals_writes_entry_only_csv(tmp_path):
    from ML.baseline.export_mt5_entry_signals import export_mt5_entry_signals

    source = pd.DataFrame(
        [
            {
                "time": "2023.01.02 10:00",
                "feature_time": "2023.01.02 09:00",
                "feature_available_time": "2023.01.02 10:00",
                "decision_time": "2023.01.02 10:00",
                "rule_id": "rule01",
                "side": "BUY",
                "limit_price": 1900.0,
                "protective_stop_price": 1890.0,
                "ATR": 10.0,
                "exit_time": "2023.01.02 14:00",
                "pnl_r": 1.5,
            }
        ]
    )

    out_csv = tmp_path / "signals.csv"
    out_json = tmp_path / "signals.json"
    frame = export_mt5_entry_signals(source, out_csv, out_json, max_fill_lag_bars=6)

    assert out_csv.exists()
    assert out_json.exists()
    assert list(frame.columns) == MT5_SIGNAL_COLUMNS
    assert "exit_time" not in frame.columns
    assert "pnl_r" not in frame.columns
```

- [ ] **Step 2: Run test and confirm expected failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py::test_export_mt5_entry_signals_writes_entry_only_csv -q
```

Expected:

```text
Fails because ML.baseline.export_mt5_entry_signals does not exist.
```

- [ ] **Step 3: Implement exporter**

Create `ML/baseline/export_mt5_entry_signals.py`:

```python
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from ML.baseline.mt5_signal_schema import MT5_SIGNAL_COLUMNS, validate_mt5_signal_frame


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_mt5_entry_signals(
    source: pd.DataFrame,
    output_csv: str | Path,
    output_json: str | Path,
    max_fill_lag_bars: int,
) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "time": source["time"].astype(str),
            "feature_time": source["feature_time"].astype(str),
            "feature_available_time": source["feature_available_time"].astype(str),
            "decision_time": source["decision_time"].astype(str),
            "rule_id": source.get("rule_id", pd.Series("rule01", index=source.index)).astype(str),
            "side": source["side"].astype(str),
            "entry_type": source["side"].astype(str).map({"BUY": "BUY_LIMIT", "SELL": "SELL_LIMIT"}),
            "limit_price": pd.to_numeric(source["limit_price"], errors="raise"),
            "stop_price": pd.to_numeric(source["protective_stop_price"], errors="raise"),
            "atr": pd.to_numeric(source.get("ATR", source.get("atr")), errors="raise"),
            "max_fill_lag_bars": int(max_fill_lag_bars),
        }
    )[MT5_SIGNAL_COLUMNS]
    validate_mt5_signal_frame(out)

    output_csv = Path(output_csv)
    output_json = Path(output_json)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_csv, sep=";", index=False)
    meta = {
        "status": "DIAGNOSTIC_ONLY",
        "schema": "mt5_entry_signal_v1",
        "rows": int(len(out)),
        "active_signal_rows": int(out["side"].isin(["BUY", "SELL"]).sum()),
        "buy_rows": int(out["side"].eq("BUY").sum()),
        "sell_rows": int(out["side"].eq("SELL").sum()),
        "unique_times": int(out["time"].nunique()),
        "duplicate_time_rows": int(len(out) - out["time"].nunique()),
        "side_counts": out["side"].value_counts().to_dict(),
        "source_csv": "DATAFRAME_INPUT_OR_CLI_SOURCE",
        "source_csv_sha256": "AVAILABLE_IN_CLI_MODE",
        "rule_id": sorted(out["rule_id"].astype(str).unique().tolist()),
        "rule_hash": "USER_FILLS_OR_EXPORTER_COMPUTES_FROM_RULE_METADATA",
        "run_config_hash": "USER_FILLS_OR_EXPORTER_COMPUTES_FROM_EXPORT_ARGS",
        "output_csv": str(output_csv),
        "output_csv_sha256": _sha256(output_csv),
        "forbidden_future_lifecycle_columns_removed": True,
    }
    output_json.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out
```

Add a minimal CLI at the bottom:

```python
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--max-fill-lag-bars", type=int, default=6)
    args = parser.parse_args()
    source = pd.read_csv(args.source, sep=";")
    export_mt5_entry_signals(source, args.output_csv, args.output_json, args.max_fill_lag_bars)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run exporter test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py::test_export_mt5_entry_signals_writes_entry_only_csv -q
```

Expected:

```text
1 passed
```

---

### Task 4: Audit And Instrument Existing `$o$imple.mq5` MT5 Port

**Files:**
- Modify: `MT/MQL5/Experts/$o$imple.mq5`
- Modify: `MT/MQL5/Include/lib_ML_Signal.mqh`
- Read: `MT/MQL5/Include/MAIN.mqh`
- Create: `docs/MT/mt5_signal_executor.md`

**Interfaces:**
- Consumes: MT5 entry CSV schema from Task 2.
- Produces: existing MQL5 expert path that can be compiled by user and run in MT5 Strategy Tester with diagnostic event logging.

**Applicable Methodology:**
- `docs/methodology/12-backtest-costs.md`: tester execution is source of fill/SL/TP/close reasons.
- `docs/methodology/13-export-mt4-parity.md`: event log must support reconciliation.

**Mandatory Checks:**
- Existing `$o$imple.mq5` remains the primary target unless it fails compile or is too coupled for safe diagnostic instrumentation.
- `MT/MQL5/Include/lib_ML_Signal.mqh` is audited before any new MQL5 executor is created.
- Expert reads entry-only CSV or documented current ML CSV.
- Diagnostic path must read `mt5_entry_signals.csv` with fields from `docs/schemas/mt5_signal_executor_schema.md`: `feature_time`, `feature_available_time`, `decision_time`, `rule_id`, `side`, `entry_type`, `limit_price`, `stop_price`, `atr`, `max_fill_lag_bars`.
- Diagnostic path must use `limit_price`, `stop_price` and `max_fill_lag_bars` from that CSV; it must not infer those values from old `ml_signals.csv`.
- Expert places tester-executed pending/limit orders for the diagnostic path, not Python-simulated fills.
- Expert logs `INIT`, `ORDER_PLACED`, `OPEN`, `CLOSE`, `ORDER_EXPIRED`, `OPEN_FAILED`, `ML_EVAL`.
- Event log format matches `docs/schemas/mt5_signal_executor_schema.md`.
- Expert computes open-position state after factual tester fill.
- `bars_since_fill=0` does not trigger ML-close.
- First ML-exit implementation may be a deterministic diagnostic scorer; model integration is separate Task 5.

**Completion Criterion:**
- User can compile `MT/MQL5/Experts/$o$imple.mq5`; if agent cannot compile MT5, plan records manual compile requirement and exact files changed.

- [ ] **Step 1: Audit current MT5 port entry points**

Run:

```bash
rg -n "OnTick|SyncInputs|ML_TRADE|ML_INIT|CLOSE_BUY|CLOSE_SEL|ORDERS_SET|ORDER_CHECK" \
  MT/MQL5/Experts/'$o$imple.mq5' \
  MT/MQL5/Include/MAIN.mqh \
  MT/MQL5/Include/lib_ML_Signal.mqh \
  MT/MQL5/Include/ORDERS.mqh
```

Expected:

```text
Existing OnTick, MAIN, ML_TRADE and order paths are visible.
```

- [ ] **Step 2: Add diagnostic inputs to existing expert**

In `MT/MQL5/Experts/$o$imple.mq5`, add inputs near existing ML inputs:

```cpp
input bool   InpMT5_DiagnosticExecutor = false;
input string InpMT5_EntrySignalFile    = "mt5_entry_signals.csv";
input string InpMT5_EventFile          = "mt5_trade_events.csv";
input bool   InpMT5_BlockBarsSinceFill0Exit = true;
```

Add corresponding runtime globals near existing ML globals:

```cpp
bool   MT5_DiagnosticExecutor = false;
string MT5_EntrySignalFile = "mt5_entry_signals.csv";
string MT5_EventFile = "mt5_trade_events.csv";
bool   MT5_BlockBarsSinceFill0Exit = true;
```

In `SyncInputs()`, copy:

```cpp
   MT5_DiagnosticExecutor = InpMT5_DiagnosticExecutor;
   MT5_EntrySignalFile = InpMT5_EntrySignalFile;
   MT5_EventFile = InpMT5_EventFile;
   MT5_BlockBarsSinceFill0Exit = InpMT5_BlockBarsSinceFill0Exit;
```

- [ ] **Step 3: Add diagnostic entry-signal reader**

In `MT/MQL5/Include/lib_ML_Signal.mqh`, add a diagnostic reader for `MT5_EntrySignalFile`, separate from the legacy `ML_SIGNALS_FILE` reader.

Required loaded arrays:

```cpp
datetime MT5_EntryTimes[];
datetime MT5_FeatureTimes[];
datetime MT5_FeatureAvailableTimes[];
datetime MT5_DecisionTimes[];
string   MT5_RuleIds[];
string   MT5_Sides[];
string   MT5_EntryTypes[];
double   MT5_LimitPrices[];
double   MT5_StopPrices[];
double   MT5_Atrs[];
int      MT5_MaxFillLagBars[];
```

Required behavior:

```text
Read `mt5_entry_signals.csv`.
Find rows by current bar time / decision_time.
For BUY_LIMIT or SELL_LIMIT place tester-executed pending order at `limit_price`.
Set protective SL from `stop_price`.
Expire/delete pending order after `max_fill_lag_bars`.
Log ORDER_PLACED, ORDER_EXPIRED and OPEN_FAILED with the original timing fields.
```

The current MQL5 legacy `ML_INIT()` only reads `ml_signals.csv`; do not rely on it for this diagnostic path.

- [ ] **Step 4: Add event logger to existing `lib_ML_Signal.mqh`**

In `MT/MQL5/Include/lib_ML_Signal.mqh`, add a logger function:

```cpp
void MT5_ML_LogEvent(
   string event_name,
   datetime event_time,
   datetime feature_time,
   datetime feature_available_time,
   datetime decision_time,
   datetime execution_time,
   string rule_id,
   string signal_time,
   ulong ticket,
   string side,
   double requested_price,
   double fill_price,
   double order_open_price,
   double order_close_price,
   double stop_price,
   string close_reason,
   double profit,
   int bars_since_fill,
   double atr_value,
   datetime entry_time,
   datetime exit_time,
   double ml_exit_score,
   int ml_exit_decision,
   string comment
)
{
   if(!MT5_DiagnosticExecutor)
      return;
   MT5_PrepareEventFileIfNeeded();
   int handle = FileOpen(MT5_EventFile, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if(handle == INVALID_HANDLE)
   {
      Print("MT5_ML_LogEvent: Cannot open ", MT5_EventFile, " Error=", GetLastError());
      return;
   }
   if(FileSize(handle) == 0)
      FileWrite(handle, "event", "time", "feature_time", "feature_available_time", "decision_time", "execution_time", "rule_id", "signal_time", "ticket", "side", "requested_price", "fill_price", "order_open_price", "order_close_price", "stop_price", "close_reason", "profit", "bars_since_fill", "bid", "ask", "spread", "spread_atr", "bar_open", "bar_high", "bar_low", "bar_close", "calculation_open", "slippage_points", "entry", "take_profit", "close", "swap", "commission", "hold_bars", "open_positions", "max_positions", "balance", "equity", "entry_time", "exit_time", "ml_exit_score", "ml_exit_decision", "comment");
   FileSeek(handle, 0, SEEK_END);
   RefreshRates();
   double spread_value = Ask - Bid;
   double spread_atr = (atr_value > 0.0 ? spread_value / atr_value : 0.0);
   FileWrite(handle, event_name, TimeToString(event_time, TIME_DATE | TIME_MINUTES), TimeToString(feature_time, TIME_DATE | TIME_MINUTES), TimeToString(feature_available_time, TIME_DATE | TIME_MINUTES), TimeToString(decision_time, TIME_DATE | TIME_MINUTES), TimeToString(execution_time, TIME_DATE | TIME_MINUTES), rule_id, signal_time, (string)ticket, side, requested_price, fill_price, order_open_price, order_close_price, stop_price, close_reason, profit, bars_since_fill, Bid, Ask, spread_value, spread_atr, Open[bar], High[bar], Low[bar], Close[bar], Open[bar], 0.0, order_open_price, 0.0, order_close_price, 0.0, 0.0, 0, 0, 1, AccountBalance(), AccountEquity(), TimeToString(entry_time, TIME_DATE | TIME_MINUTES), TimeToString(exit_time, TIME_DATE | TIME_MINUTES), ml_exit_score, ml_exit_decision, comment);
   FileClose(handle);
}
```

Add a one-run cleanup guard before the logger:

```cpp
bool MT5_EventFilePrepared = false;

void MT5_PrepareEventFileIfNeeded()
{
   if(MT5_EventFilePrepared)
      return;
   if(IsTesting())
      FileDelete(MT5_EventFile);
   MT5_EventFilePrepared = true;
}
```

Use this logger only in diagnostic path first. Do not rewrite all order code in this task.

- [ ] **Step 5: Compile after MQL5 instrumentation**

Run the MetaEditor compile check from `docs/methodology/13b-mt5-execution-parity.md`:

```bash
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' \
  /compile:'/home/hohla/git/SoSimple/MT/MQL5/Experts/$o$imple.mq5' \
  /log:'/tmp/sosimple_mt5_compile.log'
iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile.log | tail -n 20
```

Expected:

```text
MetaEditor log contains `Result: 0 errors, 0 warnings`, and `MT/MQL5/Experts/$o$imple.ex5` modification time is after the source edits.
```

If the agent cannot run Wine/MetaEditor, record `compile_status: MANUAL_REQUIRED` in the report and handoff.

- [ ] **Step 6: Document manual compile/run handoff**

Create `docs/MT/mt5_signal_executor.md`:

```markdown
# MT5 Signal Executor

> **Status**: diagnostic prototype.

## Purpose

The primary MT5 target is the existing port:

```text
MT/MQL5/Experts/$o$imple.mq5
```

The first migration step instruments this existing expert for MT5 Strategy
Tester diagnostics. A separate minimal `SoSimpleMT5SignalExecutor.mq5` is
allowed only as fallback if `$o$imple.mq5` cannot compile or cannot be safely
instrumented.

## Files

- Expert: `MT/MQL5/Experts/$o$imple.mq5`
- ML include: `MT/MQL5/Include/lib_ML_Signal.mqh`
- Input CSV: `mt5_entry_signals.csv`
- Event CSV: `mt5_trade_events.csv`

## Manual User Step

Compile `MT/MQL5/Experts/$o$imple.mq5` in MetaEditor 5. If agent-side compile is available, use the exact command from `docs/methodology/13b-mt5-execution-parity.md` and save `/tmp/sosimple_mt5_compile.log`.

Run MT5 Strategy Tester on:

- symbol: `XAUUSD`
- timeframe: `H1`
- dates: match selected diagnostic split
- model: real ticks or generated ticks, recorded in report

## Interpretation

The first prototype is `DIAGNOSTIC_ONLY`. It checks whether MT5 can replace
Python execution simulation for fill/order/SL/close mechanics.
```

- [ ] **Step 7: Static text check**

Run:

```bash
rg -n "InpMT5_DiagnosticExecutor|InpMT5_EntrySignalFile|MT5_ML_LogEvent|MT5_PrepareEventFileIfNeeded|MT5_EntrySignalFile|bars_since_fill|\\$o\\$imple.mq5" MT/MQL5/Experts/'$o$imple.mq5' MT/MQL5/Include/lib_ML_Signal.mqh docs/MT/mt5_signal_executor.md
```

Expected:

```text
All searched symbols appear.
```

---

### Task 5: Implement MT5 Open-Position Feature And Diagnostic ML-Exit In Existing Port

**Files:**
- Modify: `MT/MQL5/Include/lib_ML_Signal.mqh`
- Modify: `MT/MQL5/Include/MAIN.mqh` only if needed to access factual position state.
- Create: `docs/schemas/mt5_open_position_feature_contract.md`

**Interfaces:**
- Consumes: factual MT5 fill state from tester.
- Produces:
  - `bars_since_fill`
  - `unrealized_pnl_r_before_decision`
  - `max_favorable_r_before_decision`
  - `max_adverse_r_before_decision`
  - diagnostic `ml_exit_score`

**Applicable Methodology:**
- `docs/methodology/03-feature-contract-leakage.md`: open-position features must be computed only after factual fill and only from known bars.
- `docs/methodology/12-backtest-costs.md`: close reason and cost-aware execution must be logged.

**Mandatory Checks:**
- `bars_since_fill=0` never triggers ML-close.
- Features are computed from bars after factual fill and before decision.
- Diagnostic scorer is explicitly not the final trained model.

**Completion Criterion:**
- MT5 event log can show post-fill feature values and diagnostic close decisions.

- [ ] **Step 1: Write feature contract document**

Create `docs/schemas/mt5_open_position_feature_contract.md`:

```markdown
# MT5 Open Position Feature Contract

## Decision Timing

For H1 prototype:

```text
fill happens inside tester -> wait until at least one H1 bar after fill is closed -> compute ML-exit features -> close immediately after decision
```

## Working Features

- `bars_since_fill`: number of completed H1 bars after factual fill.
- `unrealized_pnl_r_before_decision`: PnL at last known close.
- `max_favorable_r_before_decision`: favorable movement after fill using only completed bars before decision.
- `max_adverse_r_before_decision`: adverse movement after fill using only completed bars before decision.
- `ATR`: entry-time ATR or explicitly documented current ATR.

## Forbidden

- `bars_since_fill=0` ML-close.
- Future exit time from Python.
- Python-simulated fill or Python-simulated trade PnL as MT5 input.
```

- [ ] **Step 2: Implement diagnostic scorer**

In `MT/MQL5/Include/lib_ML_Signal.mqh`, implement a diagnostic score function:

```cpp
double DiagnosticMlExitScore(int bars_since_fill, double unrealized_r, double favorable_r, double adverse_r)
{
   if(bars_since_fill <= 0)
      return 0.0;
   if(adverse_r >= 0.75 && unrealized_r <= 0.0)
      return 1.0;
   if(bars_since_fill >= 24)
      return 1.0;
   return 0.0;
}
```

This is only to prove the MT5 loop can close positions from post-fill features. It is not a model-quality result.

- [ ] **Step 3: Log feature values before close**

Extend `MT5_ML_LogEvent(...)` calls for open positions so every `ML_EVAL` row includes:

```text
bars_since_fill;ml_exit_score;ml_exit_decision
```

Expected event types:

```text
ML_EVAL
ML_CLOSE
```

- [ ] **Step 4: Static check**

Run:

```bash
rg -n "DiagnosticMlExitScore|ML_EVAL|ML_CLOSE|bars_since_fill <= 0" MT/MQL5/Include/lib_ML_Signal.mqh docs/schemas/mt5_open_position_feature_contract.md
```

Expected:

```text
All searched symbols appear.
```

---

### Task 6: Parse MT5 Event Log And Compute Metrics In Python

**Files:**
- Create: `ML/baseline/parse_mt5_execution_report.py`
- Create: `tests/test_parse_mt5_execution_report.py`
- Create: `ML/reports/mt5_execution_loop/sample_mt5_trade_events.csv`

**Interfaces:**
- Consumes: MT5 event CSV from Task 2.
- Produces:
  - `parse_mt5_events(path: Path) -> pd.DataFrame`
  - `compute_mt5_metrics(events: pd.DataFrame) -> dict[str, object]`
  - `ML/reports/mt5_execution_loop/mt5_metrics_<run_id>.json`

**Applicable Methodology:**
- `docs/methodology/12-backtest-costs.md`: gross/net, close reasons, missed opens and costs separated.
- `docs/methodology/13-export-mt4-parity.md`: counts and reconciliation report required.

**Mandatory Checks:**
- Parser rejects missing schema columns.
- Metrics include order counts, open counts, close counts, close reason counts, total profit and missing opens.
- Metrics are `DIAGNOSTIC_ONLY` until feature contract and MT5 run metadata pass.

**Completion Criterion:**
- Python can parse a sample MT5 event log and produce JSON metrics.

- [ ] **Step 1: Add parser tests**

Create `tests/test_parse_mt5_execution_report.py`:

```python
import pandas as pd

from ML.baseline.parse_mt5_execution_report import compute_mt5_metrics, parse_mt5_events


def test_parse_mt5_events_and_compute_metrics(tmp_path):
    path = tmp_path / "events.csv"
    def event_row(event, time, profit=0.0, bars_since_fill=0, close_reason=""):
        return {
            "event": event,
            "time": time,
            "feature_time": "2023.01.02 09:00",
            "feature_available_time": "2023.01.02 10:00",
            "decision_time": "2023.01.02 10:00",
            "execution_time": time,
            "rule_id": "rule01",
            "signal_time": "2023.01.02 10:00",
            "ticket": 1,
            "side": "BUY",
            "requested_price": 1900.0,
            "fill_price": 1900.0 if event != "ORDER_PLACED" else 0.0,
            "order_open_price": 1900.0 if event != "ORDER_PLACED" else 0.0,
            "order_close_price": 1912.5 if event == "CLOSE" else 0.0,
            "stop_price": 1890.0,
            "close_reason": close_reason,
            "profit": profit,
            "bars_since_fill": bars_since_fill,
            "bid": 1900.0,
            "ask": 1900.2,
            "spread": 0.2,
            "spread_atr": 0.02,
            "bar_open": 1901.0,
            "bar_high": 1913.0,
            "bar_low": 1899.0,
            "bar_close": 1912.5,
            "calculation_open": 1901.0,
            "slippage_points": 0.0,
            "entry": 1900.0,
            "take_profit": 0.0,
            "close": 1912.5 if event == "CLOSE" else 0.0,
            "swap": 0.0,
            "commission": 0.0,
            "hold_bars": bars_since_fill,
            "open_positions": 1 if event != "CLOSE" else 0,
            "max_positions": 1,
            "balance": 10000.0,
            "equity": 10012.5,
            "entry_time": "2023.01.02 10:05" if event != "ORDER_PLACED" else "",
            "exit_time": time if event == "CLOSE" else "",
            "ml_exit_score": 1.0 if close_reason == "ML_CLOSE" else 0.0,
            "ml_exit_decision": 1 if close_reason == "ML_CLOSE" else 0,
            "comment": "",
        }
    pd.DataFrame(
        [
            event_row("ORDER_PLACED", "2023.01.02 10:00"),
            event_row("OPEN", "2023.01.02 10:05"),
            event_row("CLOSE", "2023.01.02 12:00", profit=12.5, bars_since_fill=1, close_reason="ML_CLOSE"),
        ]
    ).to_csv(path, sep=";", index=False)

    events = parse_mt5_events(path)
    metrics = compute_mt5_metrics(events)

    assert metrics["status"] == "DIAGNOSTIC_ONLY"
    assert metrics["event_counts"]["ORDER_PLACED"] == 1
    assert metrics["event_counts"]["OPEN"] == 1
    assert metrics["event_counts"]["CLOSE"] == 1
    assert metrics["close_reason_counts"]["ML_CLOSE"] == 1
    assert metrics["profit_sum"] == 12.5
```

- [ ] **Step 2: Run test and confirm expected failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_parse_mt5_execution_report.py -q
```

Expected:

```text
Fails because ML.baseline.parse_mt5_execution_report does not exist.
```

- [ ] **Step 3: Implement parser**

Create `ML/baseline/parse_mt5_execution_report.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ML.baseline.mt5_signal_schema import validate_mt5_event_frame


def parse_mt5_events(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep=";")
    validate_mt5_event_frame(frame)
    return frame


def compute_mt5_metrics(events: pd.DataFrame) -> dict[str, object]:
    event_counts = events["event"].astype(str).value_counts().to_dict()
    closes = events.loc[events["event"].astype(str).eq("CLOSE")].copy()
    profit = pd.to_numeric(closes["profit"], errors="coerce").fillna(0.0)
    return {
        "status": "DIAGNOSTIC_ONLY",
        "event_counts": {str(k): int(v) for k, v in event_counts.items()},
        "close_reason_counts": closes["close_reason"].astype(str).value_counts().to_dict(),
        "profit_sum": float(profit.sum()),
        "closed_trades": int(len(closes)),
        "missing_open_estimate": int(event_counts.get("ORDER_PLACED", 0) - event_counts.get("OPEN", 0)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()
    events = parse_mt5_events(args.events)
    metrics = compute_mt5_metrics(events)
    Path(args.output_json).write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run parser tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_parse_mt5_execution_report.py -q
```

Expected:

```text
1 passed
```

---

### Task 7: Manual MT5 Tester Run Handoff

**Files:**
- Create: `docs/reports/2026-07-29-mt5-manual-tester-runbook.md`
- Create: `ML/reports/mt5_execution_loop/manual_run_manifest_template.json`

**Interfaces:**
- Consumes: compiled MQL5 expert and signal CSV.
- Produces: user-run procedure and required artifact checklist.

**Applicable Methodology:**
- `docs/methodology/13-export-mt4-parity.md`: tester logs and reconciliation are mandatory.
- `docs/methodology/16-reporting-audit.md`: commands, paths and hashes must be reportable.

**Mandatory Checks:**
- Runbook tells user exactly which files to copy into MT5 tester files directory.
- Runbook must not assume `MT/MQL5/Files` exists; it must discover the actual file directory with `TerminalInfoString(TERMINAL_DATA_PATH)` / tester agent path or explicitly use `FILE_COMMON`.
- Runbook asks user to report tester mode, symbol, timeframe, date range, spread mode and generated output path.
- Runbook forbids interpreting the diagnostic scorer as ML-quality proof.

**Completion Criterion:**
- User can compile/run the MT5 tester and return event CSV for parsing.

- [ ] **Step 1: Write manual runbook**

Create `docs/reports/2026-07-29-mt5-manual-tester-runbook.md`:

```markdown
# MT5 Manual Tester Runbook

> **Дата**: 2026-07-29
> **Статус**: Draft
> **Вердикт**: DIAGNOSTIC_ONLY

## Inputs

- Expert: `MT/MQL5/Experts/$o$imple.mq5`
- Signal CSV: `ML/reports/mt5_execution_loop/mt5_entry_signals_<run_id>.csv`
- Event output CSV: `mt5_trade_events_<run_id>.csv`

## User Steps

1. Compile `MT/MQL5/Experts/$o$imple.mq5` in MetaEditor 5.
2. Discover the actual MT5 file directory before copying CSV:
   - preferred: expert prints `TerminalInfoString(TERMINAL_DATA_PATH)` and the directory where `FileOpen()` reads/writes tester files;
   - fallback: diagnostic path uses `FILE_COMMON` and the runbook records `TERMINAL_COMMONDATA_PATH`;
   - do not assume repo path `MT/MQL5/Files`, because it may not exist.
3. Copy signal CSV to the discovered MT5 tester `Files` directory as `mt5_entry_signals.csv`.
4. Run Strategy Tester:
   - symbol: `XAUUSD`;
   - timeframe: `H1`;
   - date range: selected diagnostic interval;
   - model: record exact tester mode;
   - expert input `InpMT5_DiagnosticExecutor=true`;
   - expert input `InpMT5_EventFile=mt5_trade_events.csv`.
5. Return `mt5_trade_events.csv` from the discovered output path and tester HTML/XML report if available.

## Required Metadata

- MT5 build number.
- Broker/server.
- Symbol contract specification.
- Tester model.
- Date range.
- Deposit/currency/leverage.
- Spread mode.
- Whether account mode is netting or hedging.

## Interpretation

This run only validates the MT5 execution loop. It does not prove ML
profitability until a real frozen model contract is used and audited.
```

- [ ] **Step 2: Write manifest template**

Create `ML/reports/mt5_execution_loop/manual_run_manifest_template.json`:

```json
{
  "status": "DIAGNOSTIC_ONLY",
  "mt5_build": "USER_FILLS_AFTER_RUN",
  "broker_server": "USER_FILLS_AFTER_RUN",
  "symbol": "XAUUSD",
  "timeframe": "H1",
  "tester_model": "USER_FILLS_AFTER_RUN",
  "date_from": "USER_FILLS_AFTER_RUN",
  "date_to": "USER_FILLS_AFTER_RUN",
  "spread_mode": "USER_FILLS_AFTER_RUN",
  "account_mode": "USER_FILLS_AFTER_RUN",
  "terminal_data_path": "USER_FILLS_AFTER_RUN",
  "terminal_commondata_path": "USER_FILLS_IF_FILE_COMMON_USED",
  "actual_signal_csv_path": "USER_FILLS_AFTER_RUN",
  "actual_event_csv_path": "USER_FILLS_AFTER_RUN",
  "signal_csv": "mt5_entry_signals.csv",
  "event_csv": "mt5_trade_events.csv",
  "interpretation": "diagnostic execution-loop run only"
}
```

- [ ] **Step 3: Static check**

Run:

```bash
rg -n "\\$o\\$imple.mq5|mt5_entry_signals.csv|mt5_trade_events.csv|DIAGNOSTIC_ONLY|tester model" docs/reports/2026-07-29-mt5-manual-tester-runbook.md ML/reports/mt5_execution_loop/manual_run_manifest_template.json
```

Expected:

```text
All searched terms appear.
```

---

### Task 8: MT5 Batch Selection Design For 20-50 Candidates

**Files:**
- Create: `docs/reports/2026-07-29-mt5-batch-selection-design.md`
- Create: `ML/reports/mt5_execution_loop/batch_selection_contract.json`

**Interfaces:**
- Consumes: successful single-rule MT5 execution loop.
- Produces: next-stage design for selecting candidates by MT5 metrics.

**Applicable Methodology:**
- `docs/methodology/09-validation-freeze.md`: freeze before locked test.
- `docs/methodology/10-frozen-test-oos.md`: locked test only after validation selection.
- `docs/methodology/13-export-mt4-parity.md`: batch tester metrics must be reconciled, not just parsed.

**Mandatory Checks:**
- Batch selection is not enabled until single-rule prototype works.
- Batch selection is not enabled until MT5 `Nero.csv` producer parity is at least understood and documented.
- Python proxy metrics are allowed only for shortlist, not final PF/PnL verdict.
- MT5 tester metrics become the selection metric only in validation, not opened locked_test.

**Completion Criterion:**
- Project has a documented next step for moving from one diagnostic MT5 run to 20-50 candidate evaluation.

- [ ] **Step 1: Write batch selection contract**

Create `ML/reports/mt5_execution_loop/batch_selection_contract.json`:

```json
{
  "status": "PLANNED_AFTER_SINGLE_RULE_PROTOTYPE",
  "allowed_max_verdict_before_successful_single_rule_run": "DIAGNOSTIC_ONLY",
  "python_role": [
    "train models",
    "audit feature contract",
    "create shortlist",
    "export entry/model artifacts",
    "parse MT5 metrics"
  ],
  "mt5_role": [
    "place limit orders",
    "detect factual fill",
    "manage SL/TP",
    "compute open-position features after fill",
    "apply ML-exit or diagnostic scorer",
    "write events/deals"
  ],
  "shortlist_size_target": {
    "min": 20,
    "max": 50
  },
  "selection_metric_source": "MT5 validation tester metrics",
  "locked_test_policy": "freeze selected MT5 contract before locked_test"
}
```

- [ ] **Step 2: Write batch design report**

Create `docs/reports/2026-07-29-mt5-batch-selection-design.md`:

```markdown
# MT5 Batch Selection Design

> **Дата**: 2026-07-29
> **Статус**: Planned
> **Вердикт**: DIAGNOSTIC_ONLY

## Goal

Use MT5 Strategy Tester as the metric source for selecting among 20-50
shortlisted candidates after the single-rule prototype proves the execution
loop.

## Selection Principle

Python may shortlist candidates by cheap live-safe proxy metrics, but final
validation ranking must use MT5 tester metrics.

## Required Precondition

Single-rule MT5 loop must produce:

- MT5-generated or parity-approved `Nero.csv`;
- valid entry signal CSV;
- compiled MQL5 executor;
- MT5 event log;
- parsed Python metrics;
- no critical schema/reconciliation mismatch.

## Not Allowed

- selecting production candidates by Python trade PF while MT5 execution is the intended production execution engine;
- using opened locked_test to tune candidate count, thresholds or exit policy;
- using Python-simulated exit lifecycle as input to MT5.
```

- [ ] **Step 3: Static check**

Run:

```bash
rg -n "20-50|MT5 validation tester metrics|locked_test|DIAGNOSTIC_ONLY|single-rule" docs/reports/2026-07-29-mt5-batch-selection-design.md ML/reports/mt5_execution_loop/batch_selection_contract.json
```

Expected:

```text
All searched terms appear.
```

---

### Task 9: Final Report And Context Sync

**Files:**
- Create: `docs/reports/2026-07-29-mt5-execution-loop-migration.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md` only if manual report indexing is used.

**Interfaces:**
- Consumes: artifacts from Tasks 1-8.
- Produces: project-level context for the next agent/user.

**Applicable Methodology:**
- `docs/methodology/16-reporting-audit.md`: report paths, commands, hashes, limitations and next step.
- `docs/methodology/13-export-mt4-parity.md`: do not claim parity without tester reconciliation.

**Mandatory Checks:**
- Report states this is not production readiness.
- Report separates feature-leakage risk from execution-simulator risk.
- Report states whether MT5 `Nero.csv` producer parity is proven, unknown or blocked.
- Roadmap next step is single-rule MT5 compile/run, not full batch optimization.
- Changelog and handoff do not claim MT5 metrics exist unless user actually ran tester.

**Completion Criterion:**
- Project docs clearly say what was built, what remains manual, and what must happen before MT5 can be used for candidate selection.

- [ ] **Step 1: Write migration report**

Create `docs/reports/2026-07-29-mt5-execution-loop-migration.md` with required sections:

```markdown
# MT5 Execution Loop Migration

> **Дата**: 2026-07-29
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY

## Goal

## Stage Level

## Methodology

## Changed Files

## What Was Built

## MT5 Nero.csv Producer Status

## What MT5 Solves

## What MT5 Does Not Solve

## Commands

## Artifacts

## Manual Tester Status

## Limitations

## Next Step
```

Required wording:

```text
MT5 tester can replace Python execution simulation for orders/fills/SL/TP/close mechanics, but it does not by itself prove that Python ML features are live-safe.
```

- [ ] **Step 2: Update roadmap**

In `docs/superpowers/roadmap.md`, add a current item:

```markdown
### MT5 execution-loop prototype

Status: planned/diagnostic.
Next action: first prove or document MT5 `Nero.csv` producer parity from existing `MT/MQL5/Experts/$o$imple.mq5`; then compile/run one fixed11-like rule with `InpMT5_DiagnosticExecutor=true` and parse `mt5_trade_events.csv` with `ML/baseline/parse_mt5_execution_report.py`.
```

- [ ] **Step 3: Update changelog/handoff/wiki**

Add concise entries:

```text
Added MT5 diagnostic execution-loop migration plan and prototype artifacts. Status DIAGNOSTIC_ONLY; MT5 `Nero.csv` producer parity and tester results are not available until manual compile/run.
```

- [ ] **Step 4: Verify documentation consistency**

Run:

```bash
rg -n "MT5 execution-loop|Nero.csv|\\$o\\$imple.mq5|DIAGNOSTIC_ONLY|does not by itself prove" docs/reports/2026-07-29-mt5-execution-loop-migration.md docs/superpowers/roadmap.md CHANGELOG.md CONTEXT_HANDOFF.md wiki/research/fractal-stop-research.md
```

Expected:

```text
All searched terms appear, except wiki/index.md if report indexing is not manual.
```

---

## Final Verification

Run these commands; do not run full project pytest:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py tests/test_parse_mt5_execution_report.py -q
```

Expected:

```text
All MT5 prototype Python tests pass.
```

Compile MQL5 after any `.mq5/.mqh` changes:

```bash
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' \
  /compile:'/home/hohla/git/SoSimple/MT/MQL5/Experts/$o$imple.mq5' \
  /log:'/tmp/sosimple_mt5_compile.log'
iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile.log | tail -n 20
stat -c '%y %n' MT/MQL5/Experts/'$o$imple.ex5'
```

Expected:

```text
MetaEditor log contains `Result: 0 errors, 0 warnings`, and `.ex5` is newer than edited source files.
If the agent cannot run MetaEditor/Wine, final report must state `compile_status: MANUAL_REQUIRED`.
```

```bash
rg -n "future_exit_time|pnl_r|fill_time" ML/baseline/export_mt5_entry_signals.py docs/schemas/mt5_signal_executor_schema.md
```

Expected:

```text
Matches only forbidden-column checks and documentation, not exported signal columns.
```

```bash
rg -n "DIAGNOSTIC_ONLY|feature_time <= decision_time <= execution_time|bars_since_fill=0|Nero.csv|MT5_PrepareEventFileIfNeeded|mt5_entry_signals.csv|Result: 0 errors, 0 warnings" docs/superpowers/plans/2026-07-29-mt5-execution-loop-migration.md docs/schemas/mt5_signal_executor_schema.md docs/schemas/mt5_open_position_feature_contract.md docs/schemas/mt5_nero_csv_contract.md
```

Expected:

```text
All required contract terms appear.
```

## Plan Self-Review

- Spec coverage: covered MT5 environment discovery, MT5 `Nero.csv` producer parity, signal schema, entry export, existing `$o$imple.mq5` instrumentation, open-position feature contract, event parser, manual tester handoff, batch design and final reporting.
- Placeholder scan: no `TBD`, no vague “add tests”, no unspecified implementation step.
- Type consistency: Python schema/export/parser names are stable across tasks; MQL5 expert/include names are stable.
- Methodology status: `DIAGNOSTIC_ONLY` until MT5 tester run and feature contract audit pass.
