# Task 1 Report: Python Schema Timing Contract

## Status

Completed on 2026-08-01.

## Scope

Task 1 required making the MT5 diagnostic timing contract explicit in Python schema code only:

- `ML/baseline/mt5_signal_schema.py`
- `tests/test_mt5_signal_executor_schema.py`
- `tests/test_parse_mt5_execution_report.py`

No `locked_test` files were opened. No PnL/PF claims are made here.

## Implementation

Updated `ML/baseline/mt5_signal_schema.py` to:

1. Export `MT5_SIGNAL_LINKED_EVENT_NAMES`.
2. Add `_nonempty_timestamp_mask(...)`.
3. Add `_parse_required_timestamps(...)`.
4. Add `_validate_strict_timing_chain(...)`.
5. Tighten signal-frame validation to enforce:
   - `feature_time <= time`
   - `time < feature_available_time`
   - `feature_available_time <= decision_time`
6. Extend `MT5_EVENT_NAMES` with `TIMING_VIOLATION`.
7. Keep relaxed event-wide ordering for existing timestamp fields.
8. Add strict validation for signal-linked event rows with all timing fields present:
   - `feature_time <= signal_time`
   - `signal_time < feature_available_time`
   - `feature_available_time <= decision_time`
   - `decision_time <= execution_time`
9. Leave `TX_OPEN` / `TX_CLOSE` rows valid when their timing bridge fields are empty.

## Test Changes

Added the required RED tests to `tests/test_mt5_signal_executor_schema.py`:

- `test_mt5_signal_schema_requires_match_time_before_feature_available_time`
- `test_mt5_signal_schema_rejects_copied_timing_contract`
- `test_mt5_event_schema_accepts_timing_violation_event_name`
- `test_mt5_event_schema_validates_signal_time_as_entry_match_key`

Adjusted existing schema/parser fixtures that previously used copied timing values so they match the new explicit contract:

- signal fixtures now use `time < feature_available_time`
- event fixtures now use `signal_time < feature_available_time`

Updated parser helper fixture in `tests/test_parse_mt5_execution_report.py` accordingly.

## TDD Evidence

### RED

Command run before implementation:

```bash
./.venv/bin/python -m pytest \
  tests/test_mt5_signal_executor_schema.py::test_mt5_signal_schema_requires_match_time_before_feature_available_time \
  tests/test_mt5_signal_executor_schema.py::test_mt5_signal_schema_rejects_copied_timing_contract \
  tests/test_mt5_signal_executor_schema.py::test_mt5_event_schema_accepts_timing_violation_event_name \
  tests/test_mt5_signal_executor_schema.py::test_mt5_event_schema_validates_signal_time_as_entry_match_key \
  tests/test_parse_mt5_execution_report.py::test_tx_rows_with_empty_timing_fields_pass_validation \
  -q
```

Observed result:

- exit code `1`
- `2 failed, 3 passed`
- failing tests:
  - `test_mt5_signal_schema_rejects_copied_timing_contract`
  - `test_mt5_event_schema_accepts_timing_violation_event_name`

This matches the task brief expectation.

### GREEN

Targeted command re-run after implementation:

```bash
./.venv/bin/python -m pytest \
  tests/test_mt5_signal_executor_schema.py::test_mt5_signal_schema_requires_match_time_before_feature_available_time \
  tests/test_mt5_signal_executor_schema.py::test_mt5_signal_schema_rejects_copied_timing_contract \
  tests/test_mt5_signal_executor_schema.py::test_mt5_event_schema_accepts_timing_violation_event_name \
  tests/test_mt5_signal_executor_schema.py::test_mt5_event_schema_validates_signal_time_as_entry_match_key \
  tests/test_parse_mt5_execution_report.py::test_tx_rows_with_empty_timing_fields_pass_validation \
  -q
```

Observed result:

- exit code `0`
- `5 passed in 0.25s`

Additional targeted verification:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py tests/test_parse_mt5_execution_report.py -q
```

Observed result:

- exit code `0`
- `22 passed in 0.30s`

Allowlist verification:

```bash
rg -n "TIMING_VIOLATION" ML/baseline/mt5_signal_schema.py
```

Observed result:

- line `196` contains `TIMING_VIOLATION`

## Changed Files

- `ML/baseline/mt5_signal_schema.py`
- `tests/test_mt5_signal_executor_schema.py`
- `tests/test_parse_mt5_execution_report.py`
- `.superpowers/sdd/2026-08-01-mt5-diagnostic-timing-contract/task-1-report.md`

## Self-Review

- Implementation stayed inside the Python schema layer, as requested.
- Existing dirty worktree files outside task scope were not reverted.
- TX reconciliation path was preserved by gating strict event validation on both event name and non-empty timing fields.
- Existing schema tests were updated only where their fixtures encoded the old copied-timing contract.

## Concerns

1. `ML/baseline/prepare_mt5_entry_source.py` still documents and emits copied timing fields for its diagnostic bridge output. This task explicitly did not change that file, but the broader MT5 timing migration is not complete while that producer remains unchanged.
2. `tests/test_mt5_signal_executor_schema.py` contains exporter/preparation tests in the same file as schema tests. That is workable, but it increases the chance that future contract shifts require fixture maintenance outside pure schema assertions.
