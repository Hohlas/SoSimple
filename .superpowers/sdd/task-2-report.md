# Task 2 Report: Define MT5 Signal And Event Schemas

## RED evidence

Command:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py -q
```

Result before implementation:

```text
ModuleNotFoundError: No module named 'ML.baseline.mt5_signal_schema'
```

This confirmed the test failed for the expected reason: the schema module was missing.

## GREEN evidence

Command:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py -q
```

Result after implementation:

```text
3 passed in 0.26s
```

## Files

- Added `tests/test_mt5_signal_executor_schema.py`
- Added `ML/baseline/mt5_signal_schema.py`
- Added `docs/schemas/mt5_signal_executor_schema.md`

## Risks

- Validation is contract-level only: it checks required/forbidden columns and allowed enum values, but not column order, dtypes, or timing relations between row values.
- The schema document is descriptive and does not enforce the CSV contract by itself.
- Event schema currently validates presence of the declared columns only; runtime reconciliation rules still need consumer-side checks.
