# MT5 Diagnostic Timing Contract

> **Дата**: 2026-08-01
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: сделать MT5 diagnostic entry timing contract явным в Python, MQL5, документации и диагностических артефактах.
> **Related plan/spec**: `docs/superpowers/plans/2026-08-01-mt5-diagnostic-timing-contract.md`, `docs/superpowers/specs/2026-08-01-mt5-diagnostic-timing-contract-design.md`

## Context

Предыдущий MT5 diagnostic bridge копировал `signal_time` во все timing-поля.
Это было удобно для первого smoke, но не доказывало честный entry timing
contract. Этап исправил контракт без открытия `locked_test` и без нового
winner search.

## Уровень этапа

allowed_max_verdict: DIAGNOSTIC_ONLY
forbidden_interpretations: no live-ready claim; no production-ready claim; no new PnL/PF quality claim; no locked_test conclusion

## What Was Done

- Python schema теперь проверяет `feature_time <= time < feature_available_time <= decision_time`.
- Event schema и diagnostics проверяют `feature_time <= signal_time < feature_available_time <= decision_time <= execution_time` для signal-linked rows with complete timing fields; rows without `signal_time` are treated as legacy/partial diagnostic rows, not as fully verified v2 event rows.
- Entry source bridge формирует H1 timing: `feature_time=signal_time`, `feature_available_time=signal_time+1h`, `decision_time=feature_available_time+latency_bars*h`, `time=decision_time-1h`.
- Export metadata пишет `timing_contract`, `latency_bars` и включает их в `run_config_hash`.
- MQL5 reader матчится только по `time`, отклоняет неверные строки через `TIMING_VIOLATION` и не добавляет их в активный массив сигналов.
- Методология `13b` синхронизирована с новым time-only matching.

## Multiple Testing Context

```text
current_search_budget: 32 MT5 tester diagnostic reruns for previously selected validation candidates; no new model/profile/threshold selection.
cumulative_search_budget: inherit from `docs/reports/2026-07-31-mt5-batch-selection.md`; this stage adds timing-contract verification only.
selection_policy: no threshold, model, profile, side, horizon, entry/exit policy, spread/fill convention, transform, scaler, or filter may be selected from this rerun.
allowed_max_verdict: DIAGNOSTIC_ONLY
```

## Changed Files

- `ML/baseline/mt5_signal_schema.py`
- `ML/baseline/prepare_mt5_entry_source.py`
- `ML/baseline/export_mt5_entry_signals.py`
- `ML/baseline/run_mt5_batch.py`
- `ML/baseline/mt5_execution_diagnostics.py`
- `MT/MQL5/Include/lib_ML_Signal.mqh`
- `CHANGELOG.md`
- `docs/methodology/13b-mt5-execution-parity.md`
- `docs/ML/mt5_execution_loop.md`
- `tests/test_mt5_batch_runtime_contract.py`
- `tests/test_mt5_signal_executor_schema.py`
- `tests/test_parse_mt5_execution_report.py`
- `tests/test_mt5_execution_diagnostics.py`

## Verification

Executed during tasks:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py tests/test_parse_mt5_execution_report.py -q
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py -q
./.venv/bin/python -m py_compile ML/baseline/run_mt5_batch.py
rg -n "max_fill_lag_bars=6|latency_bars=0" ML/baseline/run_mt5_batch.py
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py -q
rg -n "decision_time` or `time|decision_time\\` или|feature_time <= time < feature_available_time <= decision_time|TIMING_VIOLATION|TX_OPEN|TX_CLOSE" docs/methodology/13b-mt5-execution-parity.md docs/schemas
git diff --check -- docs/methodology/13b-mt5-execution-parity.md docs/schemas
```

MT5 compile:

```bash
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' \
  /compile:'/home/hohla/git/SoSimple/MT/MQL5/Experts/$o$imple.mq5' \
  /log:'/tmp/sosimple_mt5_compile.log'
iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile.log | tail -n 20
```

Compile log contained `Result: 0 errors, 0 warnings`.

Task 7 commands:

```bash
rg -n "#property tester_file \"mt5_entry_signals.csv\"|int      bar=1|MT5_FindEntrySignal\\(Time\\[bar\\]\\)" 'MT/MQL5/Experts/$o$imple.mq5' MT/MQL5/Include/lib_ML_Signal.mqh
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase signals
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase all
./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics \
  --phase events \
  --output-json ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json \
  --output-csv ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv
```

Final Task 8 checks were run separately after report creation.

Final Task 8 checks:

```bash
./.venv/bin/python -m pytest \
  tests/test_mt5_signal_executor_schema.py \
  tests/test_parse_mt5_execution_report.py \
  tests/test_mt5_execution_diagnostics.py \
  tests/test_mt5_batch_runtime_contract.py \
  -q
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
./.venv/bin/python wiki/wiki.py status
./.venv/bin/python -m pytest tests/ -q
```

Results: targeted final subset passed (`53 passed`). Static checks and wiki
status passed. Full `tests/` suite finished with `1568 passed, 1 failed,
52 warnings`; the failing test was
`tests/test_mql_telemetry_params_csv_contract.py::test_tester_ini_selects_telemetry_backtest_row`,
which expects `BackTest=2` in `MT/tester/$o$imple.ini`, while the file currently
contains `BackTest=0`. This file and test were not changed by this stage.

## Results

Structured artifacts:

```text
ML/reports/mt5_execution_loop/batch/batch_summary.json
ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json
ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv
/tmp/sosimple_mt5_compile.log
docs/superpowers/specs/2026-08-01-mt5-diagnostic-timing-contract-design.md
docs/superpowers/plans/2026-08-01-mt5-diagnostic-timing-contract.md
```

Facts from regenerated artifacts:

- signal artifacts: 32/32 `entry_signals.json` include `timing_contract` and `latency_bars=0`.
- signal timing check: `checked_signal_files=32`, `bad_files=0`.
- smoke tester: passed with `UNEXPLAINED=0`.
- full batch runtime: `UNKNOWN`; `run_mt5_batch --phase all` observed expected event files for 2/32 runs and failed to find event files for 30/32. After final review, the runner was hardened to delete stale tester event files before each future launch and to reject non-zero tester exit codes.
- `batch_summary.json`: `status=DIAGNOSTIC_ONLY`, `verdict=BATCH_NO_WINNER`, `n_candidates=32`, `n_valid=2`, `n_eligible=0`.
- `event_anomaly_summary.json` `batch_runs.timing_contract`: `checked_rows=2189`, `violation_rows=0`, `timing_violation_event_count=0`.
- `event_anomaly_summary.json` `reference_runs.timing_contract`: `checked_rows=22510`, `violation_rows=22510`; this reflects historical copied-timing reference artifacts, not the regenerated batch signal contract.

## Conclusions

The diagnostic timing contract is now explicit and enforced in code. Default
`latency_bars=0` preserves the MT5 placement mechanics: signal row `time=T` is
matched by `Time[1]`, so order placement remains on the first tick of bar
`T+1`.

The stage does not produce a new model-quality conclusion. It only improves the
diagnostic execution contract and records that the full 32-run runtime rerun is
not fully verified in this environment.

## Limitations / Open Questions

- Full 32-run runtime verification is `UNKNOWN`: MT5 tester did not write the
  expected `mt5_trade_events_<run_id>.csv` for 30 of 32 runs.
- The original Task 7 runtime evidence cannot be upgraded beyond `UNKNOWN`;
  freshness safeguards were added after review and require a new full-batch run
  to re-establish runtime evidence.
- Historical reference event artifacts still contain copied-timing violations.
  They are useful only as legacy reference context.
- `latency_bars>0` is implemented as metadata/export support, but remains a
  separate diagnostic mode and must not enter winner selection.
- Full project pytest has an unrelated existing MT4 tester config failure:
  `MT/tester/$o$imple.ini` has `BackTest=0`, while
  `test_tester_ini_selects_telemetry_backtest_row` expects `BackTest=2`.

## Split Disclosure

```text
train: not used by this timing-contract rerun; candidate training/search context inherited from `docs/reports/2026-07-31-mt5-batch-selection.md`.
validation: 2021-01-04..2022-12-02; runner source role is `val_select`.
val-stop: not used by this timing-contract rerun; inherited/unchanged where applicable.
val-select: used only to regenerate and rerun the 32 previously selected diagnostic candidates.
val-eval: not used by this timing-contract rerun; inherited/unchanged where applicable.
locked_test: not opened
sample_size_gate: no winner selection in this stage; `batch_summary.json` reports n_candidates=32, n_valid=2, n_eligible=0.
```

## Next Step

Investigate why MT5/Wine produced expected event files for smoke and the first
two full-batch runs but not for the remaining 30. Re-run full batch only after
that file-output issue is understood; keep any result at `DIAGNOSTIC_ONLY`
unless separate methodology gates are passed.

## Related Materials

- `docs/methodology/13b-mt5-execution-parity.md`
- `docs/methodology/03-feature-contract-leakage.md`
- `docs/methodology/16-reporting-audit.md`
- `docs/reports/2026-07-31-mt5-batch-selection.md`
- `docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md`
