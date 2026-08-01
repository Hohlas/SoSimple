# MT5 Diagnostic Timing Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the MT5 diagnostic entry timing contract explicit, validated in Python and MQL, and visible in regenerated diagnostic artifacts without opening `locked_test` or making new PnL/PF claims.

**Architecture:** Keep the current MT5 placement mechanics for `latency_bars=0`: signal row `time=T` is matched by `Time[1]`, so the order is placed on the first tick of bar `T+1`. Python prepares and validates the stricter timing contract; MQL rejects invalid rows at load time and logs `TIMING_VIOLATION`; diagnostics verify the same invariant over generated event logs. `latency_bars>0` is implemented only as a separately labelled diagnostic export mode and must not enter winner selection.

**Tech Stack:** Python via `./.venv/bin/python`, `pandas`, `pytest`, existing MT5 scripts under `ML/baseline/`, existing MQL5 expert `MT/MQL5/Experts/$o$imple.mq5` and include `MT/MQL5/Include/lib_ML_Signal.mqh`, MT5 Strategy Tester via Wine as documented in `docs/methodology/13b-mt5-execution-parity.md`.

## Global Constraints

- Spec source: `docs/superpowers/specs/2026-08-01-mt5-diagnostic-timing-contract-design.md`.
- Result status remains `DIAGNOSTIC_ONLY`.
- Do not open `locked_test`.
- Do not make new PnL/PF trading-quality claims.
- Default mode is `latency_bars=0`.
- `latency_bars>0` is a separate diagnostic mode and must not participate in winner selection.
- For `latency_bars=0`, do not change the MT5 placement moment: `ORDER_PLACED` remains on the open of the bar after `signal_time`.
- Preserve `TX_OPEN` and `TX_CLOSE` rows with empty timing fields; they are linked by Python reconciliation.
- Worktree warning: related files may already contain uncommitted executor changes. Inspect current content before editing and do not revert unrelated changes.
- Methodology required for this plan:
  - `docs/methodology/13b-mt5-execution-parity.md`: MT5 compile, tester, event log, reconciliation, tester metadata.
  - `docs/methodology/03-feature-contract-leakage.md`: `decision_time`, feature availability, executable entry price, `DIAGNOSTIC_ONLY` when leakage/execution contract is not fully proven.
  - `docs/methodology/16-reporting-audit.md`: report structure, facts versus hypotheses, structured artifacts, limitations, forbidden interpretations.
- No dedicated current file exists at `docs/schemas/mt5_signal_executor_schema.md`; use `ML/baseline/mt5_signal_schema.py` as the executable schema source and synchronize `docs/methodology/13b-mt5-execution-parity.md`.

---

## File Structure

- Modify: `ML/baseline/mt5_signal_schema.py`
  - Owns the Python signal/event column lists, event-name allowlist, and strict timing validators.
- Modify: `tests/test_mt5_signal_executor_schema.py`
  - Owns Python schema tests and static checks against the MQL event header.
- Modify: `tests/test_parse_mt5_execution_report.py`
  - Keeps the parser contract for `TX_OPEN`/`TX_CLOSE` rows with empty timing fields.
- Modify: `ML/baseline/prepare_mt5_entry_source.py`
  - Converts entry-quality rows into the stricter MT5 entry source timing contract.
- Modify: `ML/baseline/export_mt5_entry_signals.py`
  - Propagates timing fields and records timing metadata.
- Modify: `ML/baseline/mt5_execution_diagnostics.py`
  - Adds read-only batch timing-contract diagnostics.
- Modify: `tests/test_mt5_execution_diagnostics.py`
  - Tests the new diagnostic summary.
- Modify: `MT/MQL5/Include/lib_ML_Signal.mqh`
  - Uses a single match key, validates timing rows on load, logs `TIMING_VIOLATION`, and preserves event timing semantics.
- Read only: `MT/MQL5/Experts/$o$imple.mq5`
  - Verify `bar=1` and `#property tester_file "mt5_entry_signals.csv"` remain unchanged.
- Modify: `docs/methodology/13b-mt5-execution-parity.md`
  - Synchronizes the documented MT5 diagnostic executor contract.
- Create: `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md`
  - Final stage report after implementation and verification.
- Generated artifacts: `ML/reports/mt5_execution_loop/batch/{run_id}/entry_signals.csv`, `entry_signals.json`, `events.csv`, `metrics.json`, `ML/reports/mt5_execution_loop/batch/batch_summary.json`, and diagnostics under `ML/reports/mt5_execution_loop/diagnostics/`.

## Unknowns And Questions

- MT5/Wine availability is environment-dependent. If compile or tester launch fails because the terminal is unavailable, record the exact failure and keep status `UNKNOWN` for runtime verification.
- The current branch already has uncommitted changes in several related files. Before starting Task 1, inspect `git diff -- <file>` for every file you will edit and preserve any existing user/executor changes that are not contradicted by this plan.
- The spec assumes H1 bars. Implement the bridge with an explicit one-hour bar delta and document it in metadata. Do not generalize timeframe handling in this task.
- Full batch runtime is expected to be long. If the user explicitly asks to stop after smoke verification, the implementation report must mark full-batch acceptance as not executed.

---

### Task 1: Python Schema Timing Contract

**Files:**
- Modify: `ML/baseline/mt5_signal_schema.py`
- Modify: `tests/test_mt5_signal_executor_schema.py`
- Modify: `tests/test_parse_mt5_execution_report.py`

**Interfaces:**
- Consumes: existing `MT5_SIGNAL_COLUMNS`, `MT5_EVENT_COLUMNS`, `validate_mt5_signal_frame(frame)`, `validate_mt5_event_frame(frame)`.
- Produces:
  - `MT5_SIGNAL_LINKED_EVENT_NAMES: set[str]`
  - signal validation for `feature_time <= time < feature_available_time <= decision_time`
  - event validation for signal-linked rows with non-empty timing fields using `feature_time <= signal_time < feature_available_time <= decision_time <= execution_time`
  - event allowlist containing `TIMING_VIOLATION`

**Applicable Methodology:** `docs/methodology/03-feature-contract-leakage.md` ML Leakage Preflight checks 1 (`decision_time`) and 19 (entry price executable after feature availability); `docs/methodology/13b-mt5-execution-parity.md` CSV contract and event log sections.

**Required Checks:** targeted pytest for schema/parser tests; `rg` check that `TIMING_VIOLATION` is in the Python allowlist.

**Done Criteria:** Python rejects copied timing fields for new signal CSV rows, accepts `TIMING_VIOLATION`, and still accepts `TX_OPEN`/`TX_CLOSE` rows with empty timing fields.

- [ ] **Step 1: Add failing schema tests**

Append these tests to `tests/test_mt5_signal_executor_schema.py`:

```python
def test_mt5_signal_schema_requires_match_time_before_feature_available_time():
    frame = pd.DataFrame(
        [
            {
                "time": "2023.01.02 09:00",
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


def test_mt5_signal_schema_rejects_copied_timing_contract():
    frame = pd.DataFrame(
        [
            {
                "time": "2023.01.02 09:00",
                "feature_time": "2023.01.02 09:00",
                "feature_available_time": "2023.01.02 09:00",
                "decision_time": "2023.01.02 09:00",
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

    with pytest.raises(ValueError, match="time >= feature_available_time"):
        validate_mt5_signal_frame(frame)


def test_mt5_event_schema_accepts_timing_violation_event_name():
    frame = pd.DataFrame(
        [{col: "" for col in MT5_EVENT_COLUMNS}],
        columns=MT5_EVENT_COLUMNS,
    )
    frame.loc[0, "event"] = "TIMING_VIOLATION"

    validate_mt5_event_frame(frame)


def test_mt5_event_schema_validates_signal_time_as_entry_match_key():
    frame = pd.DataFrame(
        [
            {
                "event": "ORDER_PLACED",
                "time": "2023.01.02 10:00",
                "feature_time": "2023.01.02 09:00",
                "feature_available_time": "2023.01.02 10:00",
                "decision_time": "2023.01.02 10:00",
                "execution_time": "2023.01.02 10:00",
                "rule_id": "rule01",
                "signal_time": "2023.01.02 09:00",
                "error_code": 0,
                "error_class": "",
                "retcode": 0,
                "retcode_text": "",
                "request_seq": 1,
                "magic": 163856259,
                "symbol": "XAUUSD",
                "entry_type": "BUY_LIMIT",
                "ticket": 0,
                "side": "BUY",
                "requested_price": 1900.0,
                "fill_price": 0.0,
                "order_open_price": 0.0,
                "order_close_price": 0.0,
                "stop_price": 1890.0,
                "close_reason": "",
                "profit": 0.0,
                "bars_since_fill": 0,
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
                "entry": 0.0,
                "take_profit": 0.0,
                "close": 0.0,
                "swap": 0.0,
                "commission": 0.0,
                "hold_bars": 0,
                "open_positions": 0,
                "max_positions": 1,
                "balance": 10000.0,
                "equity": 10000.0,
                "entry_time": "",
                "exit_time": "",
                "unrealized_pnl_r_before_decision": 0.0,
                "max_favorable_r_before_decision": 0.0,
                "max_adverse_r_before_decision": 0.0,
                "ml_exit_score": 0.0,
                "ml_exit_decision": 0,
                "comment": "",
            }
        ],
        columns=MT5_EVENT_COLUMNS,
    )

    validate_mt5_event_frame(frame)
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_mt5_signal_executor_schema.py::test_mt5_signal_schema_requires_match_time_before_feature_available_time \
  tests/test_mt5_signal_executor_schema.py::test_mt5_signal_schema_rejects_copied_timing_contract \
  tests/test_mt5_signal_executor_schema.py::test_mt5_event_schema_accepts_timing_violation_event_name \
  tests/test_mt5_signal_executor_schema.py::test_mt5_event_schema_validates_signal_time_as_entry_match_key \
  tests/test_parse_mt5_execution_report.py::test_tx_rows_with_empty_timing_fields_pass_validation \
  -q
```

Expected: at least the copied-timing and `TIMING_VIOLATION` tests fail before implementation; the TX-row test must still pass or fail only because the shared schema was already changed in the dirty worktree.

- [ ] **Step 3: Implement strict timing validation**

In `ML/baseline/mt5_signal_schema.py`, add the event-name set and strict validators near `_validate_time_order`:

```python
MT5_SIGNAL_LINKED_EVENT_NAMES = {
    "ORDER_PLACED",
    "ORDER_EXPIRED",
    "OPEN_FAILED",
    "OPEN",
    "ML_EVAL",
    "ML_CLOSE",
    "CLOSE",
}


def _nonempty_timestamp_mask(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    mask = pd.Series(True, index=frame.index)
    for column in columns:
        if column not in frame.columns:
            return pd.Series(False, index=frame.index)
        mask &= frame[column].fillna("").astype(str).str.strip().ne("")
    return mask


def _parse_required_timestamps(frame: pd.DataFrame, columns: list[str]) -> dict[str, pd.Series]:
    parsed = {column: pd.to_datetime(frame[column], errors="coerce") for column in columns}
    bad = [
        column
        for column, values in parsed.items()
        if values.isna().any()
    ]
    if bad:
        raise ValueError(f"invalid MT5 timestamp values in columns: {bad}")
    return parsed


def _validate_strict_timing_chain(
    frame: pd.DataFrame,
    columns: list[str],
    *,
    strict_pairs: set[tuple[str, str]],
) -> None:
    if frame.empty:
        return
    parsed = _parse_required_timestamps(frame, columns)
    for left, right in zip(columns, columns[1:]):
        if (left, right) in strict_pairs:
            invalid = parsed[left].ge(parsed[right])
            op = ">="
        else:
            invalid = parsed[left].gt(parsed[right])
            op = ">"
        if invalid.any():
            raise ValueError(f"MT5 timing contract violation: {left} {op} {right}")
```

Then update validators:

```python
def validate_mt5_signal_frame(frame: pd.DataFrame) -> None:
    missing = [col for col in MT5_SIGNAL_COLUMNS if col not in frame.columns]
    if missing:
        raise ValueError(f"missing MT5 signal columns: {missing}")

    forbidden = sorted(MT5_FORBIDDEN_SIGNAL_COLUMNS.intersection(frame.columns))
    if forbidden:
        raise ValueError(
            f"forbidden future/result columns in MT5 signal frame: {forbidden}"
        )

    bad_side = set(frame["side"].astype(str)) - {"BUY", "SELL"}
    if bad_side:
        raise ValueError(f"unsupported side values: {sorted(bad_side)}")

    bad_entry = set(frame["entry_type"].astype(str)) - {"BUY_LIMIT", "SELL_LIMIT"}
    if bad_entry:
        raise ValueError(f"unsupported entry_type values: {sorted(bad_entry)}")

    _validate_strict_timing_chain(
        frame,
        ["feature_time", "time", "feature_available_time", "decision_time"],
        strict_pairs={("time", "feature_available_time")},
    )
```

Add `TIMING_VIOLATION` to `MT5_EVENT_NAMES`, and update event validation:

```python
def validate_mt5_event_frame(frame: pd.DataFrame) -> None:
    missing = [col for col in MT5_EVENT_COLUMNS if col not in frame.columns]
    if missing:
        raise ValueError(f"missing MT5 event columns: {missing}")

    unknown = sorted(set(frame["event"].astype(str)) - MT5_EVENT_NAMES)
    if unknown:
        raise ValueError(f"unknown MT5 event names: {unknown}")

    signal_rows = frame["event"].astype(str).isin(MT5_SIGNAL_LINKED_EVENT_NAMES)
    timing_columns = ["feature_time", "signal_time", "feature_available_time", "decision_time", "execution_time"]
    complete_timing = _nonempty_timestamp_mask(frame, timing_columns)
    timing_frame = frame.loc[signal_rows & complete_timing, timing_columns]
    _validate_strict_timing_chain(
        timing_frame,
        timing_columns,
        strict_pairs={("signal_time", "feature_available_time")},
    )

    _validate_time_order(
        frame,
        ["feature_time", "feature_available_time", "decision_time", "execution_time"],
    )
```

Do not remove `_validate_time_order`; it still protects legacy event rows that have no `signal_time` but do have the old four timing fields.

- [ ] **Step 4: Run schema tests and verify they pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py tests/test_parse_mt5_execution_report.py -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/mt5_signal_schema.py tests/test_mt5_signal_executor_schema.py tests/test_parse_mt5_execution_report.py
git commit -m "test: enforce mt5 diagnostic timing schema"
```

---

### Task 2: Entry Source Timing Bridge

**Files:**
- Modify: `ML/baseline/prepare_mt5_entry_source.py`
- Modify: `tests/test_mt5_signal_executor_schema.py`

**Interfaces:**
- Consumes: `prepare_entry_quality_source(source: pd.DataFrame, *, rule_id: str = "entry_quality_filter")`.
- Produces:
  - `prepare_entry_quality_source(..., latency_bars: int = 0) -> pd.DataFrame`
  - H1 timing contract: `feature_time=signal_time`, `feature_available_time=signal_time+1h`, `decision_time=feature_available_time+latency_bars*h`, `time=decision_time-1h`.
  - metadata `time_policy`, `timing_contract`, `latency_bars`, `output_csv_sha256`.

**Applicable Methodology:** `docs/methodology/03-feature-contract-leakage.md` ML Leakage Preflight check 19 (entry price executable after feature availability); `docs/methodology/13b-mt5-execution-parity.md` CSV contract.

**Required Checks:** unit tests for default timing, positive latency timing, negative latency rejection, metadata content.

**Done Criteria:** generated prepared rows no longer copy all timing fields from `signal_time`, and default `latency_bars=0` preserves match key `time=signal_time`.

**Column Boundary:** `prepare_entry_quality_source` keeps `protective_stop_price` in its intermediate `OUTPUT_COLUMNS`. `export_mt5_entry_signals._build_export_frame` maps `protective_stop_price` to the signal CSV column `stop_price` and adds `entry_type` plus `max_fill_lag_bars`.

- [ ] **Step 1: Replace bridge tests with stricter timing expectations**

In `tests/test_mt5_signal_executor_schema.py`, replace `test_prepare_mt5_entry_source_from_entry_quality_scores_contract` and `test_prepare_mt5_entry_source_rejects_time_mismatch` with:

```python
def test_prepare_mt5_entry_source_from_entry_quality_scores_contract():
    from ML.baseline.prepare_mt5_entry_source import prepare_entry_quality_source

    source = pd.DataFrame(
        [
            {
                "time": "2023.01.02 10:00",
                "signal_time": "2023.01.02 10:00",
                "side": "SELL",
                "limit_price": 1910.0,
                "protective_stop_price": 1920.0,
                "atr": 10.0,
                "pnl_r": -1.0,
                "exit_time": "2023.01.02 15:00",
            }
        ]
    )

    prepared = prepare_entry_quality_source(source)

    assert prepared.to_dict(orient="records") == [
        {
            "time": "2023.01.02 10:00",
            "feature_time": "2023.01.02 10:00",
            "feature_available_time": "2023.01.02 11:00",
            "decision_time": "2023.01.02 11:00",
            "rule_id": "entry_quality_filter",
            "side": "SELL",
            "limit_price": 1910.0,
            "protective_stop_price": 1920.0,
            "atr": 10.0,
        }
    ]
    assert "pnl_r" not in prepared.columns
    assert "exit_time" not in prepared.columns


def test_prepare_mt5_entry_source_latency_bars_shifts_match_time_to_decision_minus_one_bar():
    from ML.baseline.prepare_mt5_entry_source import prepare_entry_quality_source

    source = pd.DataFrame(
        [
            {
                "time": "2023.01.02 10:00",
                "signal_time": "2023.01.02 10:00",
                "side": "BUY",
                "limit_price": 1900.0,
                "protective_stop_price": 1890.0,
                "atr": 10.0,
            }
        ]
    )

    prepared = prepare_entry_quality_source(source, latency_bars=2)

    assert prepared.loc[0, "feature_time"] == "2023.01.02 10:00"
    assert prepared.loc[0, "feature_available_time"] == "2023.01.02 11:00"
    assert prepared.loc[0, "decision_time"] == "2023.01.02 13:00"
    assert prepared.loc[0, "time"] == "2023.01.02 12:00"


def test_prepare_mt5_entry_source_rejects_negative_latency_bars():
    from ML.baseline.prepare_mt5_entry_source import prepare_entry_quality_source

    source = pd.DataFrame(
        [
            {
                "time": "2023.01.02 10:00",
                "signal_time": "2023.01.02 10:00",
                "side": "BUY",
                "limit_price": 1900.0,
                "protective_stop_price": 1890.0,
                "atr": 10.0,
            }
        ]
    )

    with pytest.raises(ValueError, match="latency_bars must be >= 0"):
        prepare_entry_quality_source(source, latency_bars=-1)
```

- [ ] **Step 2: Run bridge tests and verify they fail**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_mt5_signal_executor_schema.py::test_prepare_mt5_entry_source_from_entry_quality_scores_contract \
  tests/test_mt5_signal_executor_schema.py::test_prepare_mt5_entry_source_latency_bars_shifts_match_time_to_decision_minus_one_bar \
  tests/test_mt5_signal_executor_schema.py::test_prepare_mt5_entry_source_rejects_negative_latency_bars \
  -q
```

Expected: the default timing test fails because the current bridge copies `signal_time`; the latency tests fail because `latency_bars` is not implemented.

- [ ] **Step 3: Implement H1 timing preparation**

In `ML/baseline/prepare_mt5_entry_source.py`, add:

```python
H1_BAR_DELTA = pd.Timedelta(hours=1)
TIMING_CONTRACT = "feature_time <= time < feature_available_time <= decision_time"
```

Update the function signature and timing block:

```python
def prepare_entry_quality_source(
    source: pd.DataFrame,
    *,
    rule_id: str = "entry_quality_filter",
    latency_bars: int = 0,
) -> pd.DataFrame:
    if latency_bars < 0:
        raise ValueError("latency_bars must be >= 0")

    missing = [col for col in SOURCE_COLUMNS if col not in source.columns]
    if missing:
        raise ValueError(f"missing entry source columns: {missing}")

    signal_dt = pd.to_datetime(source["signal_time"], errors="coerce")
    if signal_dt.isna().any():
        raise ValueError("invalid signal_time values")

    feature_time = signal_dt
    feature_available_time = signal_dt + H1_BAR_DELTA
    decision_time = feature_available_time + latency_bars * H1_BAR_DELTA
    match_time = decision_time - H1_BAR_DELTA

    side = source["side"].astype(str).str.upper().str.strip()
    bad_side = sorted(set(side) - {"BUY", "SELL"})
    if bad_side:
        raise ValueError(f"unsupported side values: {bad_side}")

    prepared = pd.DataFrame(
        {
            "time": match_time.dt.strftime("%Y.%m.%d %H:%M"),
            "feature_time": feature_time.dt.strftime("%Y.%m.%d %H:%M"),
            "feature_available_time": feature_available_time.dt.strftime("%Y.%m.%d %H:%M"),
            "decision_time": decision_time.dt.strftime("%Y.%m.%d %H:%M"),
            "rule_id": rule_id,
            "side": side,
            "limit_price": pd.to_numeric(source["limit_price"], errors="raise"),
            "protective_stop_price": pd.to_numeric(source["protective_stop_price"], errors="raise"),
            "atr": pd.to_numeric(source["atr"], errors="raise"),
        }
    )
    return prepared[OUTPUT_COLUMNS].copy()
```

Do not keep the old `time == signal_time` rejection.

- [ ] **Step 4: Add CLI and metadata support**

Update `write_prepared_source` and `parse_args` in `ML/baseline/prepare_mt5_entry_source.py`:

```python
def write_prepared_source(
    *,
    input_csv: str | Path,
    output_csv: str | Path,
    output_json: str | Path,
    rule_id: str = "entry_quality_filter",
    latency_bars: int = 0,
) -> dict[str, Any]:
    input_path = Path(input_csv)
    output_csv_path = Path(output_csv)
    output_json_path = Path(output_json)

    source = pd.read_csv(input_path, sep=";", usecols=lambda col: col in set(SOURCE_COLUMNS) | FORBIDDEN_COLUMNS)
    prepared = prepare_entry_quality_source(source, rule_id=rule_id, latency_bars=latency_bars)

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    prepared.to_csv(output_csv_path, sep=";", index=False)

    metadata: dict[str, Any] = {
        "status": "DIAGNOSTIC_ONLY",
        "source_csv": str(input_path),
        "source_csv_sha256": _sha256_file(input_path),
        "output_csv": str(output_csv_path),
        "output_csv_sha256": _sha256_file(output_csv_path),
        "rows": int(len(prepared)),
        "rule_id": rule_id,
        "date_from": str(prepared["time"].min()) if not prepared.empty else None,
        "date_to": str(prepared["time"].max()) if not prepared.empty else None,
        "time_policy": "H1 diagnostic timing: feature_time=signal_time; feature_available_time=signal_time+1h; decision_time=feature_available_time+latency_bars*h; time=decision_time-1h for MT5 Time[1] matching",
        "timing_contract": TIMING_CONTRACT,
        "latency_bars": int(latency_bars),
        "forbidden_source_columns_present": sorted(set(source.columns) & FORBIDDEN_COLUMNS),
        "forbidden_columns_exported": sorted(set(prepared.columns) & FORBIDDEN_COLUMNS),
    }
    output_json_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metadata
```

Add parser argument and pass it through:

```python
parser.add_argument("--latency-bars", type=int, default=0)
```

```python
latency_bars=args.latency_bars,
```

- [ ] **Step 5: Run bridge tests and verify they pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py -q
```

Expected: all tests in `tests/test_mt5_signal_executor_schema.py` pass.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/prepare_mt5_entry_source.py tests/test_mt5_signal_executor_schema.py
git commit -m "fix: stamp mt5 entry timing contract"
```

---

### Task 3: Export Metadata Contract

**Files:**
- Modify: `ML/baseline/export_mt5_entry_signals.py`
- Modify: `tests/test_mt5_signal_executor_schema.py`
- Modify only if needed: `ML/baseline/run_mt5_batch.py`

**Interfaces:**
- Consumes: `export_mt5_entry_signals(..., max_fill_lag_bars: int, ...)`.
- Produces:
  - `export_mt5_entry_signals(..., latency_bars: int = 0, ...)`
  - metadata keys `timing_contract` and `latency_bars`
  - `run_config` includes `timing_contract` and `latency_bars` so `run_config_hash` changes when timing policy changes.

**Applicable Methodology:** `docs/methodology/13b-mt5-execution-parity.md` frozen export/hash rules; `docs/methodology/16-reporting-audit.md` structured artifact and hash disclosure.

**Required Checks:** metadata unit test; `run_mt5_batch.py --phase signals` must not silently skip old copied-timing JSON as valid.

**Done Criteria:** every new `entry_signals.json` records the stricter timing contract and default `latency_bars=0`.

- [ ] **Step 1: Add failing metadata test**

Append to `tests/test_mt5_signal_executor_schema.py`:

```python
def test_export_mt5_entry_signals_metadata_records_timing_contract(tmp_path):
    from ML.baseline.export_mt5_entry_signals import export_mt5_entry_signals

    source = pd.DataFrame(
        [
            {
                "time": "2023.01.02 09:00",
                "feature_time": "2023.01.02 09:00",
                "feature_available_time": "2023.01.02 10:00",
                "decision_time": "2023.01.02 10:00",
                "rule_id": "rule01",
                "side": "BUY",
                "limit_price": 1900.0,
                "protective_stop_price": 1890.0,
                "atr": 10.0,
            }
        ]
    )

    out_csv = tmp_path / "signals.csv"
    out_json = tmp_path / "signals.json"

    export_mt5_entry_signals(
        source,
        out_csv,
        out_json,
        max_fill_lag_bars=6,
        latency_bars=0,
    )

    metadata = json.loads(out_json.read_text(encoding="utf-8"))
    assert metadata["timing_contract"] == "feature_time <= time < feature_available_time <= decision_time"
    assert metadata["latency_bars"] == 0
    assert metadata["run_config"]["latency_bars"] == 0
```

Add `import json` near the top of the test file if it is not already present.

- [ ] **Step 2: Run metadata test and verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py::test_export_mt5_entry_signals_metadata_records_timing_contract -q
```

Expected: fail because `latency_bars` is not an accepted argument or metadata key is absent.

- [ ] **Step 3: Implement export metadata**

In `ML/baseline/export_mt5_entry_signals.py`, add:

```python
TIMING_CONTRACT = "feature_time <= time < feature_available_time <= decision_time"
```

Add `latency_bars: int` to `_build_metadata` and to `export_mt5_entry_signals` with default `0`. Add it to `run_config`:

```python
run_config = {
    "label": label,
    "run_id": run_id,
    "max_fill_lag_bars": int(max_fill_lag_bars),
    "latency_bars": int(latency_bars),
    "timing_contract": TIMING_CONTRACT,
    "columns": MT5_SIGNAL_COLUMNS,
    "rule_metadata_sha256": rule_metadata_sha256,
    "source_csv_sha256": source_hash,
}
```

Add the top-level metadata keys:

```python
"timing_contract": TIMING_CONTRACT,
"latency_bars": int(latency_bars),
```

Pass `latency_bars` from CLI:

```python
parser.add_argument("--latency-bars", type=int, default=0)
```

```python
latency_bars=args.latency_bars,
```

In `ML/baseline/run_mt5_batch.py`, call export explicitly with default latency:

```python
export_mt5_entry_signals(
    prepared,
    output_csv=entry_csv,
    output_json=entry_json,
    max_fill_lag_bars=6,
    run_id=run_id,
    label="mt5_batch_selection",
    latency_bars=0,
)
```

- [ ] **Step 4: Make signal regeneration skip logic timing-aware**

In `ML/baseline/run_mt5_batch.py`, replace the existing skip condition for signal generation with a metadata check:

```python
if entry_csv.exists() and entry_json.exists():
    meta = json.loads(entry_json.read_text(encoding="utf-8"))
    if (
        meta.get("rows_total", 0) > 0
        and meta.get("timing_contract") == "feature_time <= time < feature_available_time <= decision_time"
        and int(meta.get("latency_bars", -1)) == 0
    ):
        n_skipped += 1
        print(f"[{i}/{n_total}] SKIP {run_id} (exists, {meta['rows_total']} rows, timing_contract=v2)")
        continue
```

This forces regeneration of existing copied-timing artifacts that lack the new metadata.
The `latency_bars == 0` check is deliberate: positive latency artifacts are a separate diagnostic mode and must not be treated as the default batch source.

- [ ] **Step 5: Run export and batch-script tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py -q
./.venv/bin/python -m py_compile ML/baseline/run_mt5_batch.py
rg -n "max_fill_lag_bars=6|latency_bars=0" ML/baseline/run_mt5_batch.py
```

Expected: tests pass, `py_compile` exits with code `0`, and `run_mt5_batch.py` shows default `max_fill_lag_bars=6` plus `latency_bars=0`.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/export_mt5_entry_signals.py ML/baseline/run_mt5_batch.py tests/test_mt5_signal_executor_schema.py
git commit -m "feat: record mt5 timing contract metadata"
```

---

### Task 4: MQL Reader Timing Guard

**Files:**
- Modify: `MT/MQL5/Include/lib_ML_Signal.mqh`
- Modify: `tests/test_mt5_signal_executor_schema.py`
- Read: `MT/MQL5/Experts/$o$imple.mq5`

**Interfaces:**
- Consumes: MQL arrays `MT5_EntryTimes`, `MT5_FeatureTimes`, `MT5_FeatureAvailableTimes`, `MT5_DecisionTimes`.
- Produces:
  - `MT5_FindEntrySignal(datetime barTime)` matches only `MT5_EntryTimes[i] == barTime`.
  - Invalid loaded rows emit `TIMING_VIOLATION` and are not added to active signal arrays.
  - `ML_EVAL` and `ML_CLOSE` event rows keep the source signal `MT5_DecisionTimes[idx]` in the `decision_time` column.

**Applicable Methodology:** `docs/methodology/13b-mt5-execution-parity.md` diagnostic executor, event log, compile rules.

**Required Checks:** static pytest checks; MetaEditor compile log with `0 errors, 0 warnings`.

**Done Criteria:** MQL cannot double-match a signal by `decision_time`, and invalid signal rows are observable as `TIMING_VIOLATION` without placing orders.

- [ ] **Step 1: Add failing static tests for MQL**

Append to `tests/test_mt5_signal_executor_schema.py`:

```python
def test_mt5_find_entry_signal_uses_entry_time_only():
    text = MQL_SIGNAL_LIB.read_text(encoding="utf-8")
    match = re.search(r"int\s+MT5_FindEntrySignal\(datetime barTime\)\s*\{(?P<body>.*?)\n\}", text, flags=re.S)

    assert match is not None
    body = match.group("body")
    assert "MT5_EntryTimes[i] == barTime" in body
    assert "MT5_DecisionTimes[i] == barTime" not in body


def test_mt5_entry_init_logs_and_skips_timing_violations():
    text = MQL_SIGNAL_LIB.read_text(encoding="utf-8")
    assert "TIMING_VIOLATION" in text
    assert "feature_time <= time < feature_available_time <= decision_time" in text
    assert re.search(r"continue\s*;", text[text.find("TIMING_VIOLATION") : text.find("MT5_EntrySignalCount++")], flags=re.S)


def test_mt5_lifecycle_events_keep_source_decision_time():
    text = MQL_SIGNAL_LIB.read_text(encoding="utf-8")
    assert '"ML_EVAL", TimeCurrent(), MT5_FeatureTimes[idx], MT5_FeatureAvailableTimes[idx], MT5_DecisionTimes[idx]' in text
    assert '"ML_CLOSE", TimeCurrent(), MT5_FeatureTimes[idx], MT5_FeatureAvailableTimes[idx], MT5_DecisionTimes[idx]' in text
```

- [ ] **Step 2: Run static tests and verify they fail**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_mt5_signal_executor_schema.py::test_mt5_find_entry_signal_uses_entry_time_only \
  tests/test_mt5_signal_executor_schema.py::test_mt5_entry_init_logs_and_skips_timing_violations \
  tests/test_mt5_signal_executor_schema.py::test_mt5_lifecycle_events_keep_source_decision_time \
  -q
```

Expected: fail before MQL changes because OR matching and `Time[bar]` lifecycle logging are still present.

- [ ] **Step 3: Change signal matching to one key**

In `MT/MQL5/Include/lib_ML_Signal.mqh`, replace `MT5_FindEntrySignal` at the current `nl -ba` range `128-133` with:

```cpp
int MT5_FindEntrySignal(datetime barTime) {
   for (int i = 0; i < MT5_EntrySignalCount; i++) {
      if (MT5_EntryTimes[i] == barTime) return i;
   }
   return -1;
}
```

- [ ] **Step 4: Add MQL timing guard helper**

Add near the diagnostic helper functions:

```cpp
bool MT5_IsEntryTimingValid(datetime feature_time, datetime entry_time, datetime feature_available_time, datetime decision_time) {
   return (feature_time <= entry_time &&
           entry_time < feature_available_time &&
           feature_available_time <= decision_time);
}

void MT5_LogTimingViolation(datetime feature_time,
                            datetime entry_time,
                            datetime feature_available_time,
                            datetime decision_time,
                            string rule_id,
                            string side,
                            string entry_type,
                            double limit_price,
                            double stop_price,
                            double atr_value,
                            string comment) {
   MT5_ML_LogEvent(
      "TIMING_VIOLATION",
      TimeCurrent(),
      feature_time,
      feature_available_time,
      decision_time,
      TimeCurrent(),
      rule_id,
      MT5_TimeText(entry_time),
      0,
      side,
      limit_price,
      0.0,
      0.0,
      0.0,
      stop_price,
      "",
      0.0,
      -1,
      atr_value,
      0,
      0,
      0.0,
      0.0,
      0.0,
      0.0,
      0,
      comment,
      0,
      "",
      0,
      "",
      -1,
      MT5_TrackedMagic,
      Symbol(),
      entry_type
   );
}
```

- [ ] **Step 5: Validate rows during `MT5_ENTRY_INIT`**

Inside the CSV load loop, read values into local variables first, validate them, and only then assign into arrays and increment the count:

```cpp
datetime entry_time = StringToTime(time_str);
datetime feature_time = StringToTime(FileReadString(handle));
datetime feature_available_time = StringToTime(FileReadString(handle));
datetime decision_time = StringToTime(FileReadString(handle));
string rule_id = FileReadString(handle);
string side = FileReadString(handle);
string entry_type = FileReadString(handle);
double limit_price = StringToDouble(FileReadString(handle));
double stop_price = StringToDouble(FileReadString(handle));
double atr_value = StringToDouble(FileReadString(handle));
int max_fill_lag_bars = (int)StringToInteger(FileReadString(handle));

if (!MT5_IsEntryTimingValid(feature_time, entry_time, feature_available_time, decision_time)) {
   MT5_LogTimingViolation(
      feature_time,
      entry_time,
      feature_available_time,
      decision_time,
      rule_id,
      side,
      entry_type,
      limit_price,
      stop_price,
      atr_value,
      "feature_time <= time < feature_available_time <= decision_time"
   );
   continue;
}

int i = MT5_EntrySignalCount;
MT5_EntryTimes[i] = entry_time;
MT5_FeatureTimes[i] = feature_time;
MT5_FeatureAvailableTimes[i] = feature_available_time;
MT5_DecisionTimes[i] = decision_time;
MT5_RuleIds[i] = rule_id;
MT5_Sides[i] = side;
MT5_EntryTypes[i] = entry_type;
MT5_LimitPrices[i] = limit_price;
MT5_StopPrices[i] = stop_price;
MT5_Atrs[i] = atr_value;
MT5_MaxFillLagBars[i] = max_fill_lag_bars;
MT5_EntrySignalCount++;
```

- [ ] **Step 6: Keep source decision time in lifecycle events**

Replace the `Time[bar]` argument in `ML_EVAL` and `ML_CLOSE` `MT5_ML_LogEvent` calls with `MT5_DecisionTimes[idx]`.
After this change, `decision_time` in the event log reflects the signal CSV value, not the current lifecycle bar. Verify that `parse_mt5_execution_report.py` reconciliation still works with this broader timing semantics; reconciliation should remain based on event names, tickets, transaction rows, and position ids, not on equality to the current bar time.

- [ ] **Step 7: Run static tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py -q
```

Expected: all static contract tests pass.

- [ ] **Step 8: Compile MT5 expert**

Run:

```bash
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' \
  /compile:'/home/hohla/git/SoSimple/MT/MQL5/Experts/$o$imple.mq5' \
  /log:'/tmp/sosimple_mt5_compile.log'
```

Read log:

```bash
iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile.log | tail -n 20
```

Expected: `Result: 0 errors, 0 warnings`; do not use Wine exit code alone as verdict.

- [ ] **Step 9: Commit**

```bash
git add MT/MQL5/Include/lib_ML_Signal.mqh tests/test_mt5_signal_executor_schema.py
git commit -m "fix: validate mt5 diagnostic timing in reader"
```

---

### Task 5: Batch Timing Diagnostics

**Files:**
- Modify: `ML/baseline/mt5_execution_diagnostics.py`
- Modify: `tests/test_mt5_execution_diagnostics.py`

**Interfaces:**
- Consumes: `load_event_rows(paths: list[Path]) -> pd.DataFrame`.
- Produces:
  - `TIMING_CHECK_EVENT_NAMES: set[str]`
  - `summarize_timing_contract(events: pd.DataFrame) -> dict[str, object]`
  - JSON fields under events summary: `timing_contract`

**Applicable Methodology:** `docs/methodology/13b-mt5-execution-parity.md` reconciliation and event-log verification; `docs/methodology/16-reporting-audit.md` structured artifact consistency.

**Required Checks:** unit tests for pass/fail counts, TX exclusion, `TIMING_VIOLATION` count; diagnostics command over current artifacts after implementation.

**Done Criteria:** diagnostics can prove zero timing violations over all signal-linked batch event rows with complete timing fields.

- [ ] **Step 1: Add failing diagnostics tests**

Append to `tests/test_mt5_execution_diagnostics.py`:

```python
def test_summarize_timing_contract_excludes_tx_rows_with_empty_timing_fields() -> None:
    from tests.test_parse_mt5_execution_report import _event_row, _tx_row
    from ML.baseline.mt5_execution_diagnostics import summarize_timing_contract

    events = pd.DataFrame(
        [
            _event_row(
                "ORDER_PLACED",
                "2023.01.02 10:00",
                feature_time="2023.01.02 09:00",
                signal_time="2023.01.02 09:00",
                feature_available_time="2023.01.02 10:00",
                decision_time="2023.01.02 10:00",
                execution_time="2023.01.02 10:00",
            ),
            _tx_row("TX_OPEN", "2023.01.02 10:05", 100, 1001, "EXPERT"),
            _tx_row("TX_CLOSE", "2023.01.02 10:40", 100, 1002, "SL"),
        ],
        columns=MT5_EVENT_COLUMNS,
    )

    summary = summarize_timing_contract(events)

    assert summary["checked_rows"] == 1
    assert summary["violation_rows"] == 0
    assert summary["tx_rows_excluded"] == 2


def test_summarize_timing_contract_reports_signal_time_violation() -> None:
    from tests.test_parse_mt5_execution_report import _event_row
    from ML.baseline.mt5_execution_diagnostics import summarize_timing_contract

    events = pd.DataFrame(
        [
            _event_row(
                "ORDER_PLACED",
                "2023.01.02 10:00",
                feature_time="2023.01.02 09:00",
                signal_time="2023.01.02 10:00",
                feature_available_time="2023.01.02 10:00",
                decision_time="2023.01.02 10:00",
                execution_time="2023.01.02 10:00",
            )
        ],
        columns=MT5_EVENT_COLUMNS,
    )

    summary = summarize_timing_contract(events)

    assert summary["checked_rows"] == 1
    assert summary["violation_rows"] == 1
    assert summary["violations_by_rule"]["signal_time < feature_available_time"] == 1


def test_summarize_timing_contract_reports_invalid_timestamp_separately() -> None:
    from tests.test_parse_mt5_execution_report import _event_row
    from ML.baseline.mt5_execution_diagnostics import summarize_timing_contract

    events = pd.DataFrame(
        [
            _event_row(
                "ORDER_PLACED",
                "2023.01.02 10:00",
                feature_time="not-a-time",
                signal_time="2023.01.02 09:00",
                feature_available_time="2023.01.02 10:00",
                decision_time="2023.01.02 10:00",
                execution_time="2023.01.02 10:00",
            )
        ],
        columns=MT5_EVENT_COLUMNS,
    )

    summary = summarize_timing_contract(events)

    assert summary["checked_rows"] == 1
    assert summary["invalid_timestamp_rows"] == 1
    assert summary["violations_by_rule"]["invalid_timestamp"] == 1
```

- [ ] **Step 2: Run diagnostics tests and verify they fail**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_mt5_execution_diagnostics.py::test_summarize_timing_contract_excludes_tx_rows_with_empty_timing_fields \
  tests/test_mt5_execution_diagnostics.py::test_summarize_timing_contract_reports_signal_time_violation \
  tests/test_mt5_execution_diagnostics.py::test_summarize_timing_contract_reports_invalid_timestamp_separately \
  -q
```

Expected: fail because `summarize_timing_contract` is missing.

- [ ] **Step 3: Implement timing summary**

Add to `ML/baseline/mt5_execution_diagnostics.py`:

```python
TIMING_CHECK_EVENT_NAMES = {
    "ORDER_PLACED",
    "ORDER_EXPIRED",
    "OPEN_FAILED",
    "OPEN",
    "ML_EVAL",
    "ML_CLOSE",
    "CLOSE",
}
TIMING_CONTRACT_COLUMNS = ["feature_time", "signal_time", "feature_available_time", "decision_time", "execution_time"]


def _complete_timing_rows(events: pd.DataFrame) -> pd.Series:
    mask = pd.Series(True, index=events.index)
    for column in TIMING_CONTRACT_COLUMNS:
        mask &= events[column].fillna("").astype(str).str.strip().ne("")
    return mask


def summarize_timing_contract(events: pd.DataFrame) -> dict[str, object]:
    if events.empty:
        return {
            "status": "DIAGNOSTIC_ONLY",
            "contract": "feature_time <= signal_time < feature_available_time <= decision_time <= execution_time",
            "checked_rows": 0,
            "violation_rows": 0,
            "tx_rows_excluded": 0,
            "timing_violation_event_count": 0,
            "invalid_timestamp_rows": 0,
            "violations_by_rule": {},
        }

    event_names = events["event"].astype(str)
    signal_mask = event_names.isin(TIMING_CHECK_EVENT_NAMES)
    complete_mask = _complete_timing_rows(events)
    checked = events.loc[signal_mask & complete_mask, TIMING_CONTRACT_COLUMNS].copy()
    parsed = {column: pd.to_datetime(checked[column], errors="coerce") for column in TIMING_CONTRACT_COLUMNS}
    invalid_timestamp = pd.Series(False, index=checked.index)
    for values in parsed.values():
        invalid_timestamp |= values.isna()
    valid_timestamp = ~invalid_timestamp

    rules = {
        "feature_time <= signal_time": parsed["feature_time"].le(parsed["signal_time"]),
        "signal_time < feature_available_time": parsed["signal_time"].lt(parsed["feature_available_time"]),
        "feature_available_time <= decision_time": parsed["feature_available_time"].le(parsed["decision_time"]),
        "decision_time <= execution_time": parsed["decision_time"].le(parsed["execution_time"]),
    }
    violations_by_rule = {
        rule: int((~mask.fillna(False) & valid_timestamp).sum())
        for rule, mask in rules.items()
        if int((~mask.fillna(False) & valid_timestamp).sum()) > 0
    }
    if invalid_timestamp.any():
        violations_by_rule["invalid_timestamp"] = int(invalid_timestamp.sum())
    row_violation = pd.Series(False, index=checked.index)
    for mask in rules.values():
        row_violation |= ~mask.fillna(False) & valid_timestamp
    row_violation |= invalid_timestamp

    tx_rows_excluded = int(event_names.isin({"TX_OPEN", "TX_CLOSE"}).sum())

    return {
        "status": "DIAGNOSTIC_ONLY",
        "contract": "feature_time <= signal_time < feature_available_time <= decision_time <= execution_time",
        "checked_rows": int(len(checked)),
        "violation_rows": int(row_violation.sum()),
        "tx_rows_excluded": tx_rows_excluded,
        "timing_violation_event_count": int(event_names.eq("TIMING_VIOLATION").sum()),
        "invalid_timestamp_rows": int(invalid_timestamp.sum()),
        "violations_by_rule": violations_by_rule,
    }
```

Add this to the return value of `summarize_event_anomalies`:

```python
"timing_contract": summarize_timing_contract(events),
```

- [ ] **Step 4: Run diagnostics tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/mt5_execution_diagnostics.py tests/test_mt5_execution_diagnostics.py
git commit -m "feat: summarize mt5 event timing contract"
```

---

### Task 6: Methodology Synchronization

**Files:**
- Modify: `docs/methodology/13b-mt5-execution-parity.md`
- Optionally create: `docs/schemas/mt5_signal_executor_schema.md`

**Interfaces:**
- Consumes: implemented Python/MQL contract from Tasks 1-5.
- Produces: methodology text that matches the implemented diagnostic executor.

**Applicable Methodology:** `docs/methodology/13b-mt5-execution-parity.md`; `docs/methodology/16-reporting-audit.md` for documenting changed assumptions.

**Required Checks:** exact-text search for removed OR-matching phrasing, new timing chain, `TIMING_VIOLATION`, and TX timing exception.

**Done Criteria:** no project methodology text still says the diagnostic signal row is selected by `decision_time` or `time`.

- [ ] **Step 1: Update diagnostic executor wording**

In `docs/methodology/13b-mt5-execution-parity.md`, replace:

```text
Строка выбирается по `decision_time` или `time`, совпадающему с рабочим баром
`Time[bar]`.
```

with:

```text
Строка выбирается только по колонке `time`, совпадающей с рабочим баром
`Time[bar]`. В текущем эксперте `bar=1`, поэтому при `latency_bars=0`
`time=T` означает размещение на первом тике бара `T+1`.
`decision_time` является проверяемым описательным полем и не участвует в
матчинге сигнала.
```

- [ ] **Step 2: Update timing contract**

Replace:

```text
feature_time <= decision_time <= execution_time
```

with:

```text
feature_time <= time < feature_available_time <= decision_time <= execution_time
```

Add immediately after it:

```text
В event log исходная колонка `time` из signal CSV записывается как
`signal_time`, потому что колонка `time` в event log обозначает время самого
события.
```

- [ ] **Step 3: Add event name and TX exception**

Add `TIMING_VIOLATION` to the diagnostic executor event list and add:

```text
`TIMING_VIOLATION` фиксирует входную строку signal CSV, нарушившую контракт
`feature_time <= time < feature_available_time <= decision_time`; такая строка
не должна размещать ордер.

`TX_OPEN` и `TX_CLOSE` могут иметь пустые timing-поля: они приходят из
`OnTradeTransaction`, а связь с сигналом выполняется позже в Python
reconciliation.
```

- [ ] **Step 4: Decide whether to add a schema document**

If the implementation changes only executable schema code and `13b`, do not create a new schema file. If the team wants a human-readable CSV schema under `docs/schemas/`, create `docs/schemas/mt5_signal_executor_schema.md` with these sections:

````markdown
# MT5 Signal Executor CSV Contract

Status: diagnostic contract, `DIAGNOSTIC_ONLY`.

## Signal CSV

Columns:

```text
time;feature_time;feature_available_time;decision_time;rule_id;side;entry_type;limit_price;stop_price;atr;max_fill_lag_bars
```

Timing:

```text
feature_time <= time < feature_available_time <= decision_time
```

## Event CSV

The executable column order is defined in `ML/baseline/mt5_signal_schema.py`.
For signal-linked rows, event validation uses:

```text
feature_time <= signal_time < feature_available_time <= decision_time <= execution_time
```

`TX_OPEN` and `TX_CLOSE` rows may leave signal timing fields empty.
````

- [ ] **Step 5: Run documentation checks**

Run:

```bash
rg -n "decision_time` or `time|decision_time\\` или|feature_time <= time < feature_available_time <= decision_time|TIMING_VIOLATION|TX_OPEN|TX_CLOSE" docs/methodology/13b-mt5-execution-parity.md docs/schemas
git diff --check -- docs/methodology/13b-mt5-execution-parity.md docs/schemas
```

Expected: no old OR-matching phrasing remains; new timing chain and `TIMING_VIOLATION` are present; `git diff --check` exits with code `0`.

- [ ] **Step 6: Commit**

```bash
git add docs/methodology/13b-mt5-execution-parity.md docs/schemas/mt5_signal_executor_schema.md
git commit -m "docs: sync mt5 diagnostic timing methodology"
```

If `docs/schemas/mt5_signal_executor_schema.md` was not created, run:

```bash
git add docs/methodology/13b-mt5-execution-parity.md
git commit -m "docs: sync mt5 diagnostic timing methodology"
```

---

### Task 7: Regenerate Diagnostic Artifacts And Verify Runtime

**Files:**
- Read: `docs/methodology/13b-mt5-execution-parity.md`
- Read: `MT/MQL5/Experts/$o$imple.mq5`
- Generated/modify: `ML/reports/mt5_execution_loop/batch/{run_id}/entry_signals.csv`
- Generated/modify: `ML/reports/mt5_execution_loop/batch/{run_id}/entry_signals.json`
- Generated/modify: `ML/reports/mt5_execution_loop/batch/{run_id}/events.csv`
- Generated/modify: `ML/reports/mt5_execution_loop/batch/{run_id}/metrics.json`
- Generated/modify: `ML/reports/mt5_execution_loop/batch/batch_summary.json`
- Generated/modify: `ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json`
- Generated/modify: `ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv`

**Interfaces:**
- Consumes: `ML/baseline/run_mt5_batch.py --phase signals|tester|aggregate|all`.
- Produces: regenerated batch artifacts with timing-contract metadata and event timing diagnostics.

**Applicable Methodology:** `docs/methodology/13b-mt5-execution-parity.md` compile/tester/reconciliation; `docs/methodology/03-feature-contract-leakage.md` `DIAGNOSTIC_ONLY` guard; `docs/methodology/16-reporting-audit.md` structured artifact verification.

**Required Checks:** MetaEditor compile, signal regeneration, smoke tester run, full batch, aggregate, timing diagnostics.

**Done Criteria:** all 32 batch run directories have regenerated signal metadata, all parsed event logs have `UNEXPLAINED == 0`, no `TIMING_VIOLATION`, and timing diagnostics report zero violations.

- [ ] **Step 1: Verify expert still has required tester file and H1 match basis**

Run:

```bash
rg -n "#property tester_file \"mt5_entry_signals.csv\"|int      bar=1|MT5_FindEntrySignal\\(Time\\[bar\\]\\)" 'MT/MQL5/Experts/$o$imple.mq5' MT/MQL5/Include/lib_ML_Signal.mqh
```

Expected: all three required strings are present.

- [ ] **Step 2: Compile expert**

Run:

```bash
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' \
  /compile:'/home/hohla/git/SoSimple/MT/MQL5/Experts/$o$imple.mq5' \
  /log:'/tmp/sosimple_mt5_compile.log'
iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile.log | tail -n 20
```

Expected: log contains `Result: 0 errors, 0 warnings`.

- [ ] **Step 3: Regenerate signals**

Run:

```bash
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase signals
```

Expected: 32 run directories have `entry_signals.csv` and `entry_signals.json`; old copied-timing artifacts are regenerated because their metadata lacks the new timing contract.

- [ ] **Step 4: Verify regenerated signal timing**

Run:

```bash
./.venv/bin/python - <<'PY'
from pathlib import Path
import json
import pandas as pd

root = Path("ML/reports/mt5_execution_loop/batch")
paths = sorted(p for p in root.glob("*/entry_signals.csv") if not p.parent.name.startswith("_"))
assert len(paths) == 32, len(paths)
bad = []
for path in paths:
    frame = pd.read_csv(path, sep=";")
    feature = pd.to_datetime(frame["feature_time"])
    match = pd.to_datetime(frame["time"])
    available = pd.to_datetime(frame["feature_available_time"])
    decision = pd.to_datetime(frame["decision_time"])
    ok = feature.le(match) & match.lt(available) & available.le(decision)
    if not bool(ok.all()):
        bad.append(str(path))
    meta = json.loads(path.with_name("entry_signals.json").read_text(encoding="utf-8"))
    assert meta["timing_contract"] == "feature_time <= time < feature_available_time <= decision_time", path
    assert meta["latency_bars"] == 0, path
assert not bad, bad[:5]
print({"checked_signal_files": len(paths), "bad_files": len(bad)})
PY
```

Expected: prints `{'checked_signal_files': 32, 'bad_files': 0}`.

- [ ] **Step 5: Run smoke tester**

Run the existing smoke function directly:

```bash
./.venv/bin/python - <<'PY'
from ML.baseline.run_mt5_batch import load_candidates, run_smoke_test

ok = run_smoke_test(load_candidates())
raise SystemExit(0 if ok else 1)
PY
```

Expected: smoke run returns `UNEXPLAINED=0` and no `TIMING_VIOLATION`.

- [ ] **Step 6: Run full batch**

Run:

```bash
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase all
```

Expected: all 32 candidates have `events.csv` and `metrics.json`; aggregate produces `batch_summary.json`; result remains `DIAGNOSTIC_ONLY`.

- [ ] **Step 7: Verify full-batch timing**

Run:

```bash
./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics \
  --phase events \
  --output-json ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json \
  --output-csv ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv
```

Then run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

summary = json.loads(Path("ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json").read_text(encoding="utf-8"))
batch = summary["batch_runs"]
timing = batch["timing_contract"]
assert timing["checked_rows"] > 0, timing
assert timing["violation_rows"] == 0, timing
assert timing["timing_violation_event_count"] == 0, timing

batch_summary = json.loads(Path("ML/reports/mt5_execution_loop/batch/batch_summary.json").read_text(encoding="utf-8"))
assert batch_summary["status"] == "DIAGNOSTIC_ONLY", batch_summary.get("status")
for row in batch_summary["runs"]:
    if row.get("status") in {None, "OK", "DIAGNOSTIC_ONLY"}:
        assert int(row.get("unexplained", 0)) == 0, row.get("run_id")
print({"timing_checked_rows": timing["checked_rows"], "batch_status": batch_summary["status"]})
PY
```

Expected: prints checked row count and `batch_status` as `DIAGNOSTIC_ONLY`.

- [ ] **Step 8: Commit generated artifacts**

```bash
git add ML/reports/mt5_execution_loop/batch ML/reports/mt5_execution_loop/diagnostics
git commit -m "data: regenerate mt5 timing diagnostics batch"
```

---

### Task 8: Implementation Report And Final Verification

**Files:**
- Create: `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify if stage-reporting requires it: `wiki/`
- Track: `docs/superpowers/specs/2026-08-01-mt5-diagnostic-timing-contract-design.md`
- Track: `docs/superpowers/plans/2026-08-01-mt5-diagnostic-timing-contract.md`

**Interfaces:**
- Consumes: all code, tests, compile log, regenerated batch artifacts, diagnostics JSON.
- Produces: reproducible stage report and synchronized project state.

**Applicable Methodology:** `docs/methodology/16-reporting-audit.md`; `docs/methodology/13b-mt5-execution-parity.md`; `docs/methodology/03-feature-contract-leakage.md`.

**Required Checks:** targeted pytest, full relevant pytest subset, compile log, smoke/full batch evidence, report-to-artifact consistency.

**Done Criteria:** report states `DIAGNOSTIC_ONLY`, no `locked_test`, no new trading-quality claim, exact commands and artifact paths are recorded, and spec/plan files are tracked by git.

- [ ] **Step 1: Write report with required sections**

Create `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md` with these sections:

````markdown
# MT5 Diagnostic Timing Contract

Дата: 2026-08-01
Статус: DIAGNOSTIC_ONLY

## Context

## Уровень этапа

## What Was Done

## Multiple Testing Context

Diagnostic engineering rerun only; no new winner search. Use:

```text
current_search_budget: 32 MT5 tester diagnostic reruns for previously selected validation candidates; no new model/profile/threshold selection.
cumulative_search_budget: inherit from `docs/reports/2026-07-31-mt5-batch-selection.md`; this stage adds timing-contract verification only.
selection_policy: no threshold, model, profile, side, horizon, entry/exit policy, spread/fill convention, transform, scaler, or filter may be selected from this rerun.
allowed_max_verdict: DIAGNOSTIC_ONLY
```

## Changed Files

## Verification

## Results

## Conclusions

## Limitations / Open Questions

## Split Disclosure

Use the existing validation window from `ML/baseline/run_mt5_batch.py`:

```text
VAL_FROM: 2021-01-04
VAL_TO: 2022-12-02
locked_test: not opened
```

## Next Step

## Related Materials
````

The report must explicitly say:

```text
allowed_max_verdict: DIAGNOSTIC_ONLY
forbidden_interpretations: no live-ready claim; no production-ready claim; no new PnL/PF quality claim; no locked_test conclusion
```

- [ ] **Step 2: Record verification commands and artifact paths**

Include exact paths for:

```text
ML/reports/mt5_execution_loop/batch/batch_summary.json
ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json
ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv
/tmp/sosimple_mt5_compile.log
docs/superpowers/specs/2026-08-01-mt5-diagnostic-timing-contract-design.md
docs/superpowers/plans/2026-08-01-mt5-diagnostic-timing-contract.md
```

Include exact commands from Task 7.

- [ ] **Step 3: Run final test subset**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_mt5_signal_executor_schema.py \
  tests/test_parse_mt5_execution_report.py \
  tests/test_mt5_execution_diagnostics.py \
  -q
```

Expected: all selected tests pass.

- [ ] **Step 4: Run final static/document checks**

Run:

```bash
rg -n "TIMING_VIOLATION|feature_time <= time < feature_available_time <= decision_time|feature_time <= signal_time < feature_available_time <= decision_time <= execution_time|DIAGNOSTIC_ONLY|locked_test" \
  docs/superpowers/specs/2026-08-01-mt5-diagnostic-timing-contract-design.md \
  docs/superpowers/plans/2026-08-01-mt5-diagnostic-timing-contract.md \
  docs/methodology/13b-mt5-execution-parity.md \
  docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md \
  ML/baseline/mt5_signal_schema.py \
  ML/baseline/mt5_execution_diagnostics.py \
  MT/MQL5/Include/lib_ML_Signal.mqh
git diff --check
git status --short docs/superpowers/specs/2026-08-01-mt5-diagnostic-timing-contract-design.md docs/superpowers/plans/2026-08-01-mt5-diagnostic-timing-contract.md
```

Expected: required terms are present; `git diff --check` exits with code `0`; spec and plan are visible to git as staged or untracked files before final commit.

- [ ] **Step 5: Update project handoff files using stage-reporting**

Use the `stage-reporting` skill before updating final report/changelog/handoff/wiki. Record only this engineering diagnostic result, not a new model-quality conclusion.

- [ ] **Step 6: Commit report and documentation**

```bash
git add docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md CHANGELOG.md CONTEXT_HANDOFF.md wiki docs/superpowers/specs/2026-08-01-mt5-diagnostic-timing-contract-design.md docs/superpowers/plans/2026-08-01-mt5-diagnostic-timing-contract.md
git commit -m "docs: report mt5 diagnostic timing contract"
```

---

## Self-Review

**Spec Coverage**

- Honest `feature_time`, `feature_available_time`, `decision_time`: Task 2.
- Runtime invariant and `TIMING_VIOLATION`: Tasks 1, 4, 5.
- Optional latency simulation: Tasks 2 and 3, default `latency_bars=0`.
- OR-matching removal: Task 4.
- Python schema event allowlist: Task 1.
- Methodology synchronization: Task 6.
- Batch regeneration and acceptance checks: Task 7.
- Report with `DIAGNOSTIC_ONLY` guard: Task 8.

**Methodology Coverage**

- `03-feature-contract-leakage.md`: each implementation task preserves or checks feature availability and executable timing; results remain `DIAGNOSTIC_ONLY`.
- `13b-mt5-execution-parity.md`: compile, tester files, diagnostic executor, event log, reconciliation, tester metadata are used as required.
- `16-reporting-audit.md`: final report records commands, artifacts, limitations, structured outputs, and forbidden interpretations.

**Placeholder Scan**

- No task contains forbidden placeholder markers or an unspecified "write tests" step.
- The only unresolved items are explicit environment unknowns: MT5/Wine availability and whether a human chooses to add an optional human-readable schema file.

**Type And Name Consistency**

- `latency_bars` is used consistently in `prepare_entry_quality_source`, `write_prepared_source`, `export_mt5_entry_signals`, metadata, and CLI.
- Event validation uses `signal_time` as the copied signal CSV `time` key because event CSV column `time` is the event timestamp.
- `TIMING_VIOLATION` is present in MQL log events and Python event-name allowlist.
