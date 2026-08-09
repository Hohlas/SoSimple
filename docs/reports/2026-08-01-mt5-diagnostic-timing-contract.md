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

## Research-first disclosure

```text
lifecycle_status: DIAGNOSTIC_ONLY
origin_bias: engineering fix of diagnostic entry timing contract; BATCH_NO_WINNER inherited; no new selection
research_priority: high — honest entry timing is a prerequisite for any future diagnostic cycle
current_search_budget: 32 MT5 tester diagnostic reruns for previously selected validation candidates; no new model/profile/threshold selection
cumulative_search_budget: inherit from docs/reports/2026-07-31-mt5-batch-selection.md; this stage adds timing-contract verification only
next_probe_freeze: use only regenerated timing-contract artifacts; any future winner claim still requires the separate methodology gates
allowed_max_verdict: DIAGNOSTIC_ONLY
forbidden_interpretations: profitable; ready; live-ready; tradable; new winner; model-quality proof
```

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

Code and tests:

- `ML/baseline/mt5_signal_schema.py`
- `ML/baseline/prepare_mt5_entry_source.py`
- `ML/baseline/export_mt5_entry_signals.py`
- `ML/baseline/run_mt5_batch.py`
- `ML/baseline/mt5_execution_diagnostics.py`
- `MT/MQL5/Include/lib_ML_Signal.mqh`
- `tests/test_mt5_batch_runtime_contract.py`
- `tests/test_mt5_signal_executor_schema.py`
- `tests/test_parse_mt5_execution_report.py`
- `tests/test_mt5_execution_diagnostics.py`

Documentation and methodology:

- `CHANGELOG.md`
- `docs/methodology/13b-mt5-execution-parity.md`
- `docs/ML/mt5_execution_loop.md`

Project state and wiki (commits b536bf7, d880f60):

- `CONTEXT_HANDOFF.md`
- `MODULE_INDEX.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`
- `wiki/research/mt5-execution-loop.md`

Plans, specs and reports:

- `docs/superpowers/plans/2026-08-01-mt5-diagnostic-timing-contract.md`
- `docs/superpowers/specs/2026-08-01-mt5-diagnostic-timing-contract-design.md`
- `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md`

Regenerated artifacts (`ML/reports/mt5_execution_loop/`):

- `batch/batch_summary.json`
- `batch/{run_id}/entry_signals.csv` and `entry_signals.json` (32 run dirs)
- `batch/{run_id}/metrics.json` (32 run dirs)
- `batch/_smoke/metrics.json`
- `diagnostics/event_anomaly_summary.json`
- `diagnostics/event_anomalies.csv`
- `diagnostics/signal_timing_check.json` (audit follow-up, see Results)

The list above covers all files actually touched by the stage commits
(`9c331c7..d880f60` verified with `git show --stat`); the previous version of
this section only listed code/tests and missed the project-state, wiki and
regenerated-artifact files.

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

Post-review LiveUpdate recovery and failed-run recount:

```bash
./.venv/bin/python -m pytest tests/test_mt5_batch_runtime_contract.py -q
./.venv/bin/python -m py_compile ML/baseline/run_mt5_batch.py
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase aggregate
./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics \
  --phase events \
  --output-json ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json \
  --output-csv ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv
```

Results: runtime contract tests passed (`5 passed`), compile check passed,
tester rerun completed `30 done, 2 skipped, 0 failed`.

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

Results: targeted final subset passed (`55 passed`). Static checks passed.
`wiki/wiki.py status` reported changed files after this report/update pass and
therefore returned non-zero. Full `tests/` suite finished with `1570 passed,
1 failed, 52 warnings`; the failing test was
`tests/test_mql_telemetry_params_csv_contract.py::test_tester_ini_selects_telemetry_backtest_row`,
which expects `BackTest=2` in `MT/tester/$o$imple.ini`, while the file currently
contains `BackTest=0`. This file and test were not changed by this stage.

Audit note (2026-08-09): the `55 passed` count is a snapshot of the 4-file
subset at the stage commit. It can drift with later commits: the same 4-file
subset re-ran during the audit gave `62 passed`. For a reproducible count, run
the subset at a fixed commit hash.

## Results

Structured artifacts:

```text
ML/reports/mt5_execution_loop/batch/batch_summary.json
ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json
ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv
ML/reports/mt5_execution_loop/diagnostics/signal_timing_check.json
/tmp/sosimple_mt5_compile.log
docs/superpowers/specs/2026-08-01-mt5-diagnostic-timing-contract-design.md
docs/superpowers/plans/2026-08-01-mt5-diagnostic-timing-contract.md
```

Facts from regenerated artifacts:

- signal artifacts: 32/32 `entry_signals.json` include `timing_contract` and `latency_bars=0`.
- signal timing check: `checked_signal_files=32`, `bad_files=0`; saved and reproducible as `ML/reports/mt5_execution_loop/diagnostics/signal_timing_check.json`.
- smoke tester: passed with `UNEXPLAINED=0` (snapshot: committed `batch/_smoke/metrics.json` at stage commit `d880f60`; later commits re-generated this artifact).
- initial full batch runtime: `UNKNOWN`; `run_mt5_batch --phase all` observed expected event files for 2/32 runs and failed to find event files for 30/32.
- root cause: MT5 LiveUpdate intercepted terminal startup. The terminal log showed `LiveUpdate start ... /config:<mt5_batch_*.ini>` followed by normal process exit code 0, so the Python runner could treat the process as successful even though the Strategy Tester did not run and did not create the expected event file.
- mitigation: `run_mt5_batch.py` now copies `mt5_entry_signals.csv` to both terminal and tester-agent `MQL5/Files`, rejects LiveUpdate redirects from the terminal log, waits for LiveUpdate to finish, settles briefly, then retries the same `.ini`.
- recounted full batch runtime: `run_mt5_batch --phase tester` completed `30 done, 2 skipped, 0 failed`; expected event files are now present for 32/32 candidates. The two numbers `30/32` (missing event files initially) and `30 done` are different metrics and must not be compared; the `2 skipped` in the rerun are candidates that already had valid event files from the earlier run and were therefore skipped (`run_mt5_batch.py` skip logic in `--phase tester`).
- `batch_summary.json`: `status=DIAGNOSTIC_ONLY`, `verdict=BATCH_NO_WINNER`, `n_candidates=32`, `n_valid=32`, `n_eligible=11`, `n_diagnostic_only=16`. The category counts are not exhaustive: the 5 candidates outside `eligible`/`diagnostic_only` are valid runs (`unexplained=0`) with `trades_count < 30`, below the diagnostic-only trade-count band (30..99).
- `event_anomaly_summary.json` `batch_runs`: `total_rows=54078`; `timing_contract.checked_rows=49030`, `violation_rows=0`, `timing_violation_event_count=0`.
- `event_anomaly_summary.json` `reference_runs.timing_contract`: `checked_rows=22510`, `violation_rows=22510`; this reflects historical copied-timing reference artifacts, not the regenerated batch signal contract.

## Conclusions

The diagnostic timing contract is now explicit and enforced in code. Default
`latency_bars=0` preserves the MT5 placement mechanics: signal row `time=T` is
matched by `Time[1]`, so order placement remains on the first tick of bar
`T+1`.

The stage does not produce a new model-quality conclusion. It only improves the
diagnostic execution contract and confirms that the 32 candidate MT5 rerun is
complete after LiveUpdate recovery.

## Limitations / Open Questions

- The original Task 7 runtime evidence remains historically `UNKNOWN` for that
  exact run: MT5 LiveUpdate intercepted 30 of 32 tester launches before the
  runner had LiveUpdate retry logic.
- The replacement rerun completed 32/32 candidate event files, but remains
  `DIAGNOSTIC_ONLY`; it must not be interpreted as a new model-quality winner.
- Historical reference event artifacts still contain copied-timing violations.
  They are useful only as legacy reference context.
- `latency_bars>0` is implemented as metadata/export support, but remains a
  separate diagnostic mode and must not enter winner selection.
- Signal timing contract (`feature_time <= time < feature_available_time <= decision_time`) holds at `latency_bars=0`. With `latency_bars>0` the bridge produces `time >= feature_available_time`, violating the contract; such a frame is rejected by `validate_mt5_signal_frame`. This protective behavior was not captured when the stage ran and is recorded here as an audit follow-up.
- Open question (deferred decision): `docs/schemas/mt5_signal_executor_schema.md`, conditionally referenced by plan Task 6, was not created; the report correctly omits it from Changed Files. Whether a separate human-readable schema doc is needed, or `mt5_signal_schema.py` remains the executable source of truth, is an open design decision.
- Full project pytest has an unrelated existing MT4 tester config failure:
  `MT/tester/$o$imple.ini` has `BackTest=0`, while
  `test_tester_ini_selects_telemetry_backtest_row` expects `BackTest=2`.

## Invalidated Assumptions

- Assumption: *"copying `signal_time` into all timing columns proves a valid entry timing contract"*. Invalidated: the copy only coincided with the contract at `latency_bars=0` and never proved the MQL5 reader resolved the honest `time` key. Regenerated rows now use the contractual formula (`prepare_mt5_entry_source.py:89-92`); historical copied-timing rows remain reference-only (`reference_runs` in `event_anomaly_summary.json` report 22510 violations).
- Assumption: *"a tester process that exits with code 0 has actually run the Strategy Tester"*. Invalidated: MT5 LiveUpdate redirects the launch and exits with code 0 without running the tester; the runner now detects the redirect, waits, and retries the same `.ini`.
- Assumption: *"`--phase all` producing exit code 0 implies all event files exist"*. Invalidated: the initial run found event files for 2/32; after LiveUpdate recovery the recount (`--phase tester`) reached 32/32.

## Split Disclosure

```text
train: not used by this timing-contract rerun; candidate training/search context inherited from `docs/reports/2026-07-31-mt5-batch-selection.md`.
validation: 2021-01-04..2022-12-02; runner source role is `val_select`.
val-stop: not used by this timing-contract rerun; inherited/unchanged where applicable.
val-select: used only to regenerate and rerun the 32 previously selected diagnostic candidates.
val-eval: not used by this timing-contract rerun; inherited/unchanged where applicable.
locked_test: not opened
sample_size_gate: no winner selection in this stage; `batch_summary.json` reports n_candidates=32, n_valid=32, n_eligible=11, n_diagnostic_only=16.
```

## Next Step

Keep LiveUpdate recovery in the MT5 batch runner and use the same event-file
freshness checks for future tester runs. Any future winner claim still requires
the separate methodology gates; this rerun remains `DIAGNOSTIC_ONLY`.

## Related Materials

- `docs/methodology/13b-mt5-execution-parity.md`
- `docs/methodology/03-feature-contract-leakage.md`
- `docs/methodology/16-reporting-audit.md`
- `docs/reports/2026-07-31-mt5-batch-selection.md`
- `docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md`
- `docs/audit/2026-08-02-Diagnostic Timing` (first audit; source of the Changed Files, Research-first, wiki and artifact fixes)
- `docs/superpowers/audit.md` (second audit; source of the `latency_bars>0` contract and schema-doc questions)
