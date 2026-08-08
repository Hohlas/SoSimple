# CONTEXT HANDOFF

## Current Active State

- active track: `MT5 entry mechanics / trade-count frozen probe planning`
- latest report: `docs/reports/2026-08-03-mt5-multi-position-closeout.md`
- latest plan: `docs/superpowers/plans/2026-08-01-mt5-saved-batch-fill-rate-probe.md`
- latest spec: `docs/superpowers/specs/2026-08-01-mt5-diagnostic-timing-contract-design.md`
- batch summary: `ML/reports/mt5_execution_loop/batch/batch_summary.json`
- event diagnostics: `ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json`

## Decision

Fill-rate probe completed as `DIAGNOSTIC_ONLY`. Conversion-position-policy-dominant.
Fill rate is NOT the primary cause of `BATCH_NO_WINNER`. Single-position policy
blocks 99.2% of OPEN_FAILED signals; broker no-fill is negligible (0.8%).
Median fill_rate=0.094, residual=12.5% unexplained.
Next probe target: entry mechanics and trade-count consolidation, not fill rate.

MT5 diagnostic timing contract continues as `DIAGNOSTIC_ONLY`.

- Signal CSV timing is now `feature_time <= time < feature_available_time <= decision_time`.
- Event timing for signal-linked rows is now `feature_time <= signal_time < feature_available_time <= decision_time <= execution_time`.
- MQL5 signal matching uses only `time` / `MT5_EntryTimes[i] == Time[bar]`; `decision_time` is descriptive and no longer a match key.
- Invalid signal rows are logged as `TIMING_VIOLATION` and skipped before order placement.
- `TX_OPEN` and `TX_CLOSE` may keep timing fields empty; Python reconciliation links them later.
- Default mode remains `latency_bars=0`; positive latency is diagnostic-only export mode and must not enter winner selection.
- MT5 LiveUpdate startup interception is now handled in `run_mt5_batch.py`: the runner detects `LiveUpdate start ... /config:<ini>`, waits for update completion, settles briefly, then retries the same tester `.ini`.

MT5 multi-position: closeout-план **исполнен** (2026-08-07), per-expert остаётся отложен:

- `docs/superpowers/plans/2026-08-03-mt5-multi-position-closeout.md` — multi-position lifecycle tracking. **Исполнен**: диагностический слой переведён на массив tracked tickets (`MT5_TrackedPositions[]`), compile gate `0 errors, 0 warnings`, smoke max=1/2/16 с `UNEXPLAINED=0` и без нарушений timing-контракта. Отчёт: `docs/reports/2026-08-03-mt5-multi-position-closeout.md` (вердикт `DIAGNOSTIC_ONLY`). Дополнено 2026-08-07: **Full Batch 32×2** — max=1 паритет с эталоном 31.07 на уровне сделок 32/32; max=64 исполняет ~9.6× больше размещений, все позиции закрыты, `UNEXPLAINED=0`; артефакты в `ML/reports/mt5_execution_loop/multipos_pilot/{reference,max1,max64}/`. Регрессионные фиксы (`lib_ML_Signal.mqh`, `ORDERS.mqh`, `--only` раннера) не закоммичены.
- `docs/superpowers/plans/2026-08-03-mt5-per-expert-ml-tracker.md` — per-expert `rule_id` filter + multi-expert smoke. **Не исполнен**; зависел от closeout-плана, теперь разблокирован.
- Order management refactor (`POSITION_TRACKER Pos[]`) уже исполнен (отчёт `docs/reports/2026-08-02-mt5-multi-position-probe.md`, вердикт `DIAGNOSTIC_ONLY — BLOCKED на диагностическом слое`); блокер закрыт closeout-планом. Побочный фикс per-expert `Pos[]` — коммит `b1a714d` (`FUNCTIONS.mqh`, `EXPERT_PARENT_CLASS`).
- Ограничение зафиксировано в `docs/methodology/13b-mt5-execution-parity.md` → секция «Ограничения прототипа». Single-expert диагностические прогоны работают корректно; `InpMT5_MaxPositions=1` остаётся каноническим режимом.

## Current Diagnostic Facts

- 32/32 regenerated `entry_signals.json` files contain `timing_contract` and `latency_bars=0`.
- Signal timing verification: `checked_signal_files=32`, `bad_files=0`.
- MetaEditor compile log: `Result: 0 errors, 0 warnings`.
- Smoke tester: passed with `UNEXPLAINED=0`.
- Initial full batch runtime was `UNKNOWN`: MT5 LiveUpdate intercepted 30/32 tester launches, producing process exit code 0 without Strategy Tester event files.
- Replacement tester rerun completed `30 done, 2 skipped, 0 failed`; expected event files are present for 32/32 candidates.
- `batch_summary.json`: `status=DIAGNOSTIC_ONLY`, `verdict=BATCH_NO_WINNER`, `n_candidates=32`, `n_valid=32`, `n_eligible=11`, `n_diagnostic_only=16`.
- `batch_runs`: `total_rows=54078`; `timing_contract.checked_rows=49030`, `violation_rows=0`, `timing_violation_event_count=0`.
- `reference_runs.timing_contract`: historical copied-timing violations remain (`violation_rows=22510`); treat them as legacy context, not fresh batch evidence.

## Do Not Do

- Do not interpret tester PF/PnL as profitable, live-ready, tradable, or model-quality proof.
- Do not select a new winner from this diagnostic rerun.
- Do not use or open `locked_test` for any choice.
- Do not let `latency_bars>0` artifacts participate in default batch selection.

## Next Step

Create the next frozen probe plan targeting entry mechanics and trade-count
consolidation. The fill-rate probe rejected conversion rate as the primary cause
of BATCH_NO_WINNER: OPEN_FAILED is 99.2% single-position policy blocking, not
broker no-fill. PF > 1.0 for 11 eligible candidates with BS_p05 < 1.0 for all
suggests noise from low trade count, not fill rate.

The next plan must:
- Accept single-position policy as design constraint (cannot fix it).
- Focus on why PF > 1.0 coexists with BS_p05 < 1.0: entry signal mechanics,
  trade count consistency, and/or exit quality.
- Keep the same batch artifacts (no MT5 rerun for planning).
- Not open `locked_test`, not select new winner, max verdict DIAGNOSTIC_ONLY.
- Optionally resolve the 12.5% residual (signals with neither ORDER_PLACED
  nor OPEN_FAILED) via row-level event linkage.

## Verification

Completed relevant checks:

- targeted schema/parser/diagnostics pytest subsets passed during Tasks 1-5.
- `./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py -q` -> `21 passed` after final diagnostics fix.
- MetaEditor compile log contained `Result: 0 errors, 0 warnings`.
- `./.venv/bin/python -m ML.baseline.run_mt5_batch --phase signals` regenerated 32 signal artifacts.
- timing verification over 32 signal CSVs passed.
- smoke tester passed.
- `./.venv/bin/python -m pytest tests/test_mt5_batch_runtime_contract.py -q` -> `5 passed`.
- `./.venv/bin/python -m py_compile ML/baseline/run_mt5_batch.py` passed.
- `./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester` -> `30 done, 2 skipped, 0 failed`.
- `./.venv/bin/python -m ML.baseline.run_mt5_batch --phase aggregate` -> `BATCH_NO_WINNER`.
- event diagnostics regenerated after the replacement rerun.
