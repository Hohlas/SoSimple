# Label Convention Audit

> **Date**: 2026-04-13 18:40
> **Status**: Completed
> **Goal**: Проверить TB-консьюмеры на некорректную обработку float-лейблов `{1.0, 0.0, 0.5}` и минимально исправить только подтверждённые баги

## Canon

- Source of truth не менялся: `processing/label_signals.py`
- Canon:
  - `TP = 1.0`
  - `SL = 0.0`
  - `TIMEOUT = 0.5`
  - classifier thresholds: `>= 0.75 -> TP`, `<= 0.25 -> SL`, else `Timeout`

## Inventory

- Inventory file: `ML/reports/label_convention_audit_inventory.csv`
- Reviewed TB label consumers:
  - `processing/label_signals.py`
  - `ML/tb_signal_logic.py`
  - `ML/threshold_analysis.py`
  - `ML/data_loader.py`
  - `ML/evaluate_test.py`
  - `ML/tb_probability_calibration.py`
  - `ML/triple_barrier_mt4_execution.py`
  - `statistics/signal_tracer.py`

## Confirmed Bugs

### 1. `ML/tb_signal_logic.py`

- Static pattern: `loss_mask = ~win_mask`
- Dynamic reproducer: timeout row counted as loss
- Before fix:
  - `wins=1`
  - `losses=2`
  - `timeouts=1`
  - `loss=8.0`
- After fix:
  - `wins=1`
  - `losses=1`
  - `timeouts=1`
  - `loss=3.0`

### 2. `ML/threshold_analysis.py`

- Static pattern: `losses = n_trades - wins`
- Dynamic reproducer: timeouts inflated `losses` and `loss`
- Before fix:
  - `trades=10`
  - `wins=4`
  - `losses=6`
  - `timeouts=3`
  - `loss=18.0`
- After fix:
  - `trades=10`
  - `wins=4`
  - `losses=3`
  - `timeouts=3`
  - `loss=9.0`

## Safe Patterns

- `ML/data_loader.py`: timeout -> non-TP binary reduction is intentional for train/inference targets
- `ML/evaluate_test.py`: binary metrics path keeps raw labels for downstream signal-rule evaluation
- `ML/tb_probability_calibration.py`: calibrates explicit TP-vs-not-TP probability
- `statistics/signal_tracer.py`: explicit `1.0 / 0.5 / 0.0` branches, no conflation
- `ML/triple_barrier_mt4_execution.py`: explicit three-way classifier already correct

## Permanent Guards

- `tests/test_tb_label_invariants.py`
  - `test_tb_signal_logic_loss_excludes_timeout`
  - `test_threshold_analysis_loss_excludes_timeout`

## Verification

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_triple_barrier_mt4_execution.py tests/test_triple_barrier_first_touch.py tests/test_triple_barrier_calibration.py tests/test_triple_barrier_training.py tests/test_signal_tracer_tb.py tests/test_generate_signals_research.py tests/test_tb_label_invariants.py -q
# 18 passed
```

## Frozen Rerun Check

- Frozen rerun against `ML/reports/tb_selected_rule.json` was executed on the canonical artifacts from the main workspace:
  - `MT/MQL4/Files/ml_signals_tb.csv`
  - `DATA/Nero_validation_labeled.csv`
  - `DATA/Nero_test_labeled.csv`
- Fresh benchmark results matched the historical `2026-04-12` verdict exactly:
  - validation: `28 / 16 / 4 / 2`, `PF=4.333333333333333`
  - test: `69 / 29 / 23 / 5`, `PF=1.2777777777777777`
- Conclusion from rerun:
  - confirmed bugs in `ML/tb_signal_logic.py` and `ML/threshold_analysis.py` do **not** materially change the frozen TB verdict

## Conclusion

- Audit found 2 real `R2 not_win_is_loss` bugs outside the already-fixed MT4 simulator.
- Both bugs are fixed with minimal changes.
- Source-of-truth label convention and TB rule artifacts were left untouched.
- Frozen rerun confirms that the `2026-04-12` TB verdict does not change.
