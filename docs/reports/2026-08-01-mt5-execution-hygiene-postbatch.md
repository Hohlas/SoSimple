# MT5 Execution Hygiene And Post-Batch Diagnostics

> **Дата**: 2026-08-01
> **Статус**: DIAGNOSTIC_ONLY
> **Вердикт**: EXECUTION_HYGIENE_PARTIAL
> **Цель**: классифицировать доступные MT5 execution error artifacts и разобрать post-batch failure modes без выбора нового winner.
> **Related plan/spec**: `docs/superpowers/plans/2026-08-01-mt5-execution-hygiene-postbatch.md`

## Stage Level

Search/post-mortem diagnostic stage. This report does not create a candidate and cannot raise verdict above `DIAGNOSTIC_ONLY`.

## Research-first disclosure

- **lifecycle_status**: DIAGNOSTIC_ONLY
- **origin_bias**: post-mortem after `BATCH_NO_WINNER`; no new selection
- **research_priority**: infrastructure first, then post-batch diagnostics
- **current_search_budget**: 0 new model/search configurations
- **cumulative_search_budget**: inherits 64 benchmark -> 32 shortlist -> 32 MT5 tester -> 11 eligible from 2026-07-31 batch
- **next_probe_freeze**: not selected in this report
- **allowed_max_verdict**: DIAGNOSTIC_ONLY
- **forbidden_interpretations**: profitable, ready, live-ready, tradable, new winner, model-quality proof

## Context

The 2026-07-30 single-rule diagnostic reported external tester-agent `ERROR-4756` lines, 9 `ORDER_EXPIRED`, pending-order-not-found messages, and an unanalysed `ERROR_SoSimple_163856259.csv` observation.

The 2026-07-31 OnTradeTransaction lifecycle report closed event/deal reconciliation for the diagnostic executor: 269 positions, `CLOSED_TX=269`, `UNEXPLAINED=0`, `same_h1_count=17`.

The 2026-07-31 Nero parity report states `PARITY_PASS` with diagnostic limitations. The 2026-07-31 MT5 batch selection then ran 32 candidates and ended `BATCH_NO_WINNER`: 11 eligible candidates all failed `BS_p05 > 1.0`; Holm-Bonferroni rejected 0 hypotheses.

## Methodology

Applied sections: `docs/methodology/00-research-management.md`, `09-validation-freeze.md`, `12-backtest-costs.md`, `13b-mt5-execution-parity.md`, `16-reporting-audit.md`, and `A5-post-mortem-diagnostics.md`.

No exact methodology section exists for `ERROR_SoSimple_*.csv`; `13b` controls because these are execution artifacts. Facts below come from JSON/CSV artifacts. Hypotheses are explicitly marked.

## Multiple Testing Context

No new model/search configuration was selected. The inherited batch budget remains: 32 MT5 tester candidates, 11 eligible hypotheses, Holm-Bonferroni rejected 0. All post-mortem slices remain `DIAGNOSTIC_ONLY`.

## What Was Done

Generated artifacts:

- `ML/reports/mt5_execution_loop/diagnostics/error_inventory.json`
- `ML/reports/mt5_execution_loop/diagnostics/error_summary.json`
- `ML/reports/mt5_execution_loop/diagnostics/error_rows_classified.csv`
- `ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json`
- `ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv`
- `ML/reports/mt5_execution_loop/diagnostics/post_batch_diagnostics.json`
- `ML/reports/mt5_execution_loop/diagnostics/post_batch_top_candidates.csv`

Commands:

```bash
./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics --phase inventory --output-json ML/reports/mt5_execution_loop/diagnostics/error_inventory.json
./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics --phase errors --output-json ML/reports/mt5_execution_loop/diagnostics/error_summary.json --output-csv ML/reports/mt5_execution_loop/diagnostics/error_rows_classified.csv
./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics --phase events --output-json ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json --output-csv ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv
./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics --phase batch --output-json ML/reports/mt5_execution_loop/diagnostics/post_batch_diagnostics.json --output-csv ML/reports/mt5_execution_loop/diagnostics/post_batch_top_candidates.csv
```

## Changed Files

Plan implementation commits created or modified:

- `ML/baseline/mt5_execution_diagnostics.py`
- `tests/test_mt5_execution_diagnostics.py`
- `ML/reports/mt5_execution_loop/diagnostics/error_inventory.json`
- `ML/reports/mt5_execution_loop/diagnostics/error_summary.json`
- `ML/reports/mt5_execution_loop/diagnostics/error_rows_classified.csv`
- `ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json`
- `ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv`
- `ML/reports/mt5_execution_loop/diagnostics/post_batch_diagnostics.json`
- `ML/reports/mt5_execution_loop/diagnostics/post_batch_top_candidates.csv`

Final documentation/wiki commit modified:

- `docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md`
- `CONTEXT_HANDOFF.md`
- `CHANGELOG.md`
- `docs/superpowers/roadmap.md`
- `wiki/research/mt5-execution-loop.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

## Artifact Hashes

- `error_inventory.json`: `fc7d10705bedec6b092501f6d1d46727cceca96794f127af09e5a29cb22d9efe`
- `error_summary.json`: `629eee4af71d1d48ea3cf5025d172df506447d0490413534063febcbd7ff33e3`
- `error_rows_classified.csv`: `23450f45b13aaa763d6d8adc45f1f72e43d0559a13ad347126dec417a9561ad8`
- `event_anomaly_summary.json`: `ebc27151d8b7fb817ead8fbf237b26c204e0ad2af01607d2668ca18b25df69b0`
- `event_anomalies.csv`: `439d436610523a60d1c843701751ebf04af6e28fef8f837085889aa67f9493c4`
- `post_batch_diagnostics.json`: `4b1dc417738cb063e71471dcef9da6f5ad40051029a1594d0f2a68c85d1af25a`
- `post_batch_top_candidates.csv`: `abf1b0c9ab009698ef1ba2d8c75aa1210b33104bec4aadba556ade63a960f725`
- `batch_summary.json`: `215fa1322a2df30ea79bdf49ae4d5c933fbfe4b11dfc6919373ab63a657beafe`
- `mt5_execution_metrics_20260731_tx_lifecycle.json`: `e550d8bce1e364bba5424f725b93a002ddc822d0a6a0ce1b20b517facd182d28`
- `mt5_execution_metrics_20260730_entry_quality_filter.json`: `9a5af9bc89170d26f10cd06da14fa98b3e8ad767e238ee75c13ecc4c18c10494`

## Structured Artifact Cross-Check

- 6 discovered `ERROR_SoSimple_*.csv`: `error_inventory.json.files`.
- Missing `ERROR_SoSimple_163856259.csv`: `error_inventory.json.unknowns.not_found_expected_files`.
- 1879 classified error rows: `error_summary.json.total_rows`.
- Error classes `OTHER=1174`, `INVALID_STOPS=670`, `MODIFICATION_TOO_CLOSE=35`: `error_summary.json.by_error_class`.
- MT4/MT5 split `mt4_files=1174`, `mt_tester_files=705`: `error_summary.json.by_source_bucket`.
- Historical lifecycle numbers `position_count=269`, `CLOSED_TX=269`, `UNEXPLAINED=0`, `same_h1_count=17`: `ML/reports/mt5_execution_loop/mt5_execution_metrics_20260731_tx_lifecycle.json.reconciliation`.
- Historical external `ERROR-4756` count: not used as a structured key number in this report because no repo JSON/CSV for the cumulative tester-agent log exists; linkage remains `UNKNOWN`.
- Historical single-rule `ORDER_EXPIRED=9`: `ML/reports/mt5_execution_loop/mt5_execution_metrics_20260730_entry_quality_filter.json.order_counts.ORDER_EXPIRED`.
- 32 batch event paths, `_smoke` excluded: `event_anomaly_summary.json.batch_run_count`, `batch_event_path_count`, `excluded_service_dirs`.
- Batch `OPEN_FAILED=22767`: `event_anomaly_summary.json.batch_runs.event_counts.OPEN_FAILED`.
- Batch `ORDER_EXPIRED=67`: `event_anomaly_summary.json.batch_runs.event_counts.ORDER_EXPIRED`.
- Event linkage status `UNKNOWN`: `event_anomaly_summary.json.linkage_status`.
- Batch verdict `BATCH_NO_WINNER`: `post_batch_diagnostics.json.verdict`.
- 11 top candidates all with `BS_p05 < 1.0`: `post_batch_diagnostics.json.top_failure_modes.low_bootstrap_lower_bound`.
- Trade-count buckets: `post_batch_diagnostics.json.top_failure_modes.trade_count_buckets`.
- One profit-concentration failure: `post_batch_diagnostics.json.top_failure_modes.profit_concentration_fail`.
- Top candidate PF/BS/trades/fill rate: `post_batch_diagnostics.json.top_candidates[0]`.

## Verification

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py tests/test_parse_mt5_execution_report.py tests/test_mt5_signal_executor_schema.py -q
```

Result: passed before report writing; final verification repeated after document sync.

## Results

Error inventory found 6 available `ERROR_SoSimple_*.csv` files. `ERROR_SoSimple_163856259.csv` remains missing and is recorded as `UNKNOWN`.

Error row classification produced 1879 rows: `OTHER=1174`, `INVALID_STOPS=670`, `MODIFICATION_TOO_CLOSE=35`. Source buckets remain separated: `mt4_files=1174`, `mt_tester_files=705`.

Event anomaly summary covers reference runs and 32 batch runs. Batch counts include `OPEN_FAILED=22767` and `ORDER_EXPIRED=67`; `_smoke` is excluded. Linkage between event rows and `ERROR_SoSimple` rows is `UNKNOWN`, because current artifacts do not provide a proven stable row-level key.

Post-batch diagnostics preserve `BATCH_NO_WINNER`. Among 11 eligible ranked candidates, all 11 failed low bootstrap lower bound; trade-count buckets are `100-149=9` and `150+=2`; one candidate failed profit concentration. Top candidate `time_plus_atr_extra_trees_small_12h_thr0.2` has PF `1.2323`, `BS_p05=0.8867479736061653`, `trades_count=102`, fill rate `0.09444444444444444`.

## Conclusions

Verdict: `EXECUTION_HYGIENE_PARTIAL`.

Facts: available repo error CSVs, reference events, batch events, and batch failure modes are now parsed into structured artifacts. No new winner was selected.

Hypothesis: batch failure is mainly consistent with low bootstrap lower bound under small-to-moderate trade counts and low fill rate, not with unexplained event/deal reconciliation, because batch reconciliation remains `UNEXPLAINED=0` in per-run metrics. This is a hypothesis, not a model-quality conclusion.

The verdict cannot be `EXECUTION_HYGIENE_CLASSIFIED` because the expected `ERROR_SoSimple_163856259.csv` and cumulative tester agent log with external `ERROR-4756` lines are not available in the repo, and row-level error-to-event linkage is `UNKNOWN`.

## Limitations / Open Questions

- Missing `ERROR_SoSimple_163856259.csv`.
- Missing cumulative tester agent log containing external `ERROR-4756` lines.
- Batch INI, batch compile log, terminal log, and agent log were not saved as batch artifacts.
- Error/event linkage is `UNKNOWN`; no causality is inferred.
- Cost model remains incomplete: swap, commission, slippage, latency, and stress-cost checks are not closed.

## Split Disclosure

Batch period: XAUUSD H1 validation 2021.01.04-2022.12.02 from the 2026-07-31 batch. This diagnostic did not use `locked_test` or holdout for any selection, threshold, feature, entry, exit, stop, spread, cost, or PnL convention decision.

## Forbidden Interpretations

Do not interpret tester PF/PnL as profitable, production-ready, live-ready, tradable, or model-quality proof. Do not treat this report as a new winner selection or as permission to open `locked_test`.

## Next Step

Exactly one next action: retrieve the missing cumulative tester agent log and `ERROR_SoSimple_163856259.csv`.

## Related Materials

- `docs/superpowers/plans/2026-08-01-mt5-execution-hygiene-postbatch.md`
- `docs/reports/2026-07-30-mt5-single-rule-diagnostic-run.md`
- `docs/reports/2026-07-31-mt5-ontradetransaction-lifecycle.md`
- `docs/reports/2026-07-31-mt5-nero-parity.md`
- `docs/reports/2026-07-31-mt5-batch-selection.md`
- `ML/reports/mt5_execution_loop/diagnostics/`
