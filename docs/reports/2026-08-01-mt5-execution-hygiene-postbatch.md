# MT5 Execution Hygiene And Post-Batch Diagnostics

> **Дата**: 2026-08-01
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: классифицировать доступные MT5 execution error artifacts и разобрать post-batch failure modes без выбора нового winner.
> **Related plan/spec**: `docs/superpowers/plans/2026-08-01-mt5-execution-hygiene-postbatch.md`

## Stage Level

Search/post-mortem diagnostic stage. This report does not create a candidate and cannot raise verdict above `DIAGNOSTIC_ONLY`.

## Research-first disclosure

- **lifecycle_status**: DIAGNOSTIC_ONLY
- **execution_hygiene_status**: EXECUTION_HYGIENE_PARTIAL
- **origin_bias**: post-mortem after `BATCH_NO_WINNER`; no new selection
- **research_priority**: medium; infrastructure first, then post-batch diagnostics
- **current_search_budget**: 0 new model/search configurations
- **diagnostic_checks_budget**: 6 diagnostic groups: error classes, source buckets, event anomaly categories, trade-count buckets, top-11 candidate slices, profit concentration slice
- **cumulative_search_budget**: inherits 64 benchmark -> 32 shortlist -> 32 MT5 tester -> 11 eligible from 2026-07-31 batch
- **next_probe_freeze**: use only current saved batch artifacts; historical missing external logs are excluded from future decisions
- **allowed_max_verdict**: DIAGNOSTIC_ONLY
- **forbidden_interpretations**: profitable, ready, live-ready, tradable, new winner, model-quality proof

## Context

The 2026-07-30 single-rule diagnostic reported external tester-agent `ERROR-4756` lines, 9 `ORDER_EXPIRED`, pending-order-not-found messages, and an unanalysed `ERROR_SoSimple_163856259.csv` observation. These historical missing artifacts are now explicitly abandoned as non-reproducible inputs and are not used for current batch decisions.

The 2026-07-31 OnTradeTransaction lifecycle report closed event/deal reconciliation for the diagnostic executor: 269 positions, `CLOSED_TX=269`, `UNEXPLAINED=0`, `same_h1_count=17`.

The 2026-07-31 Nero parity report states `PARITY_PASS` with diagnostic limitations. The 2026-07-31 MT5 batch selection then ran 32 candidates and ended `BATCH_NO_WINNER`: 11 eligible candidates all failed `BS_p05 > 1.0`; Holm-Bonferroni rejected 0 hypotheses.

## Methodology

Applied sections: `docs/methodology/00-research-management.md`, `09-validation-freeze.md`, `12-backtest-costs.md`, `13b-mt5-execution-parity.md`, `16-reporting-audit.md`, and `A5-post-mortem-diagnostics.md`.

No exact methodology section exists for `ERROR_SoSimple_*.csv`; `13b` controls because these are execution artifacts. Facts below come from JSON/CSV artifacts. Hypotheses are explicitly marked.

## Multiple Testing Context

No new model/search configuration was selected. The inherited batch budget remains: 32 MT5 tester candidates, 11 eligible hypotheses, Holm-Bonferroni rejected 0. Diagnostic checks were limited to 6 groups: error classes, source buckets, event anomaly categories, trade-count buckets, top-11 candidate slices, and profit concentration slice. All post-mortem slices remain `DIAGNOSTIC_ONLY`.

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
- `error_summary.json`: `57be2f56f862d76f07fc603b91855a26463c9d1419db0201094d219ab60a49f0`
- `error_rows_classified.csv`: `79d5978b45c31aa690d88247712af7554ff69c3a3d73927b7212ae622da32017`
- `event_anomaly_summary.json`: `8a32bb2df4881b3417544fa7fb9c0b13ec0417f9eadf11166eb88bff34bbb59b`
- `event_anomalies.csv`: `fe759538db6999c8491333d961ed1c1691592aebf7be0fc0f2dfea6c54bacea9`
- `post_batch_diagnostics.json`: `41932413b42a9983bfb4428021fa6206544ed24bbd6649bc443e83a69951d491`
- `post_batch_top_candidates.csv`: `ed73d7d960309c482645d1b287b2ed60eb0ee85b322f2beda21482be01c00b48`
- `batch_summary.json`: `bbe2bf19a3a2b42c1fefb0f3207a29c6636eca5c5a8e0d4e37743cceb767e897`
- `mt5_execution_metrics_20260731_tx_lifecycle.json`: `e550d8bce1e364bba5424f725b93a002ddc822d0a6a0ce1b20b517facd182d28`
- `mt5_execution_metrics_20260730_entry_quality_filter.json`: `9a5af9bc89170d26f10cd06da14fa98b3e8ad767e238ee75c13ecc4c18c10494`

## Structured Artifact Cross-Check

- 6 discovered `ERROR_SoSimple_*.csv`: `error_inventory.json.files`.
- Missing `ERROR_SoSimple_163856259.csv`: `error_inventory.json.unknowns.not_found_expected_files`.
- 1879 classified error rows: `error_summary.json.total_rows`.
- Error classes `INVALID_STOPS=670`, `OTHER=621`, `REQUOTE=550`, `MODIFICATION_TOO_CLOSE=35`, `MARKET_CLOSED=2`, `INVALID_PRICE=1`: `error_summary.json.by_error_class`.
- Source buckets `mt4_files=1174`, `mt_tester_files=705`: `error_summary.json.by_source_bucket`.
- Historical lifecycle numbers `position_count=269`, `CLOSED_TX=269`, `UNEXPLAINED=0`, `same_h1_count=17`: `ML/reports/mt5_execution_loop/mt5_execution_metrics_20260731_tx_lifecycle.json.reconciliation`.
- Historical external `ERROR-4756` count: not used as a structured key number in this report because no repo JSON/CSV for the cumulative tester-agent log exists. The missing historical log is abandoned and must not block current batch follow-up.
- Historical single-rule `ORDER_EXPIRED=9`: `ML/reports/mt5_execution_loop/mt5_execution_metrics_20260730_entry_quality_filter.json.order_counts.ORDER_EXPIRED`.
- 32 batch event paths, `_smoke` excluded: `event_anomaly_summary.json.batch_run_count`, `batch_event_path_count`, `excluded_service_dirs`.
- Batch `OPEN_FAILED=22767`: `event_anomaly_summary.json.batch_runs.event_counts.OPEN_FAILED`.
- Batch `ORDER_EXPIRED=67`: `event_anomaly_summary.json.batch_runs.event_counts.ORDER_EXPIRED`.
- Event linkage status `UNKNOWN`: `event_anomaly_summary.json.linkage_status`.
- Batch verdict `BATCH_NO_WINNER`: `post_batch_diagnostics.json.verdict`.
- 11 top candidates all with `BS_p05 < 1.0`: `post_batch_diagnostics.json.top_failure_modes.low_bootstrap_lower_bound`.
- Trade-count buckets: `post_batch_diagnostics.json.top_failure_modes.trade_count_buckets`.
- One profit-concentration failure: `post_batch_diagnostics.json.top_failure_modes.profit_concentration_fail`.
- Top candidate PF/BS/trades/fill rate/gross PnL slices: `post_batch_diagnostics.json.top_candidates[0]`.

## Sample Size Disclosure

| Scope | Period / split role | Rows / events / signals / trades | Source |
|-------|---------------------|----------------------------------|--------|
| Reference event artifacts | historical diagnostic validation | 23050 events | `event_anomaly_summary.json.reference_runs.total_rows` |
| Batch event artifacts | XAUUSD H1 validation 2021.01.04-2022.12.02 / validation diagnostic | 54078 events across 32 candidate runs | `event_anomaly_summary.json.batch_runs.total_rows`, `batch_run_count` |
| Batch candidate table | XAUUSD H1 validation 2021.01.04-2022.12.02 / validation diagnostic | 32 valid candidate runs, 11 eligible top candidates | `post_batch_diagnostics.json.n_valid`, `n_eligible` |
| Eligible top candidates | XAUUSD H1 validation 2021.01.04-2022.12.02 / validation diagnostic | 1424 trades | `post_batch_diagnostics.json.sample_sizes.eligible_top_candidate_trades` |
| Eligible top candidate signals | XAUUSD H1 validation 2021.01.04-2022.12.02 / validation diagnostic | 14954 active signal rows; buy 7092, sell 7862 | `post_batch_diagnostics.json.sample_sizes` |

## Verification

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py tests/test_parse_mt5_execution_report.py tests/test_mt5_signal_executor_schema.py -q
```

Result after audit fixes: `53 passed in 0.47s` (test functions: `test_mt5_execution_diagnostics.py` 24, `test_parse_mt5_execution_report.py` 6, `test_mt5_signal_executor_schema.py` 23).

## Results

Error inventory found 6 available `ERROR_SoSimple_*.csv` files. `ERROR_SoSimple_163856259.csv` remains missing, is recorded as `UNKNOWN`, and is abandoned as a historical non-reproducible artifact.

Error row classification produced 1879 rows: `INVALID_STOPS=670`, `OTHER=621`, `REQUOTE=550`, `MODIFICATION_TOO_CLOSE=35`, `MARKET_CLOSED=2`, `INVALID_PRICE=1`. Source buckets remain separated by artifact path: `mt4_files=1174`, `mt_tester_files=705`.

Event anomaly summary covers reference runs and 32 batch runs. Batch counts include `OPEN_FAILED=22767` and `ORDER_EXPIRED=67`; for execution-scale context, also `ORDER_PLACED=2601`, `OPEN=2367`, `TX_OPEN=2508`, `TX_CLOSE=2508`. `_smoke` is excluded. The 22767 `OPEN_FAILED` events count retry attempts per same-bar signal under the single-position policy, not distinct broker refusals. Linkage between event rows and `ERROR_SoSimple` rows is `UNKNOWN`, because current artifacts do not provide a proven stable row-level key.

Post-batch diagnostics preserve `BATCH_NO_WINNER`. Among 11 eligible ranked candidates, all 11 failed low bootstrap lower bound; trade-count buckets are `100-149=9` and `150+=2`; one candidate failed profit concentration. Top candidate `time_plus_atr_extra_trees_small_12h_thr0.2` has PF `1.2323`, `BS_p05=0.8867479736061653`, `trades_count=102`, fill rate `0.09444444444444444`, `gross_profit=5468.199999999997`, `gross_loss=4437.3`, `average_win=130.19523809523804`, and `average_loss_abs=73.955`.

## Conclusions

Verdict: `DIAGNOSTIC_ONLY`.

Execution hygiene status: `EXECUTION_HYGIENE_PARTIAL`.

Facts: available repo error CSVs, reference events, batch events, and batch failure modes are now parsed into structured artifacts. No new winner was selected.

Hypothesis: batch failure is mainly consistent with low bootstrap lower bound under small-to-moderate trade counts and low fill rate, not with unexplained event/deal reconciliation, because batch reconciliation remains `UNEXPLAINED=0` in per-run metrics. This is a hypothesis, not a model-quality conclusion.

A5 post-mortem scope: partial. This report covers available failure-mode slices, gross PnL from saved `pnl_by_trade`, yearly PF/gross profit fields, and close-reason counts available in per-run `metrics.json`. It does not complete oracle component decomposition, TP/SL/TIMEOUT exit slices, yearly gross loss contribution, feature-period contrasts, or negative controls; those require additional saved inputs or a new diagnostic cycle.

The execution hygiene status remains `EXECUTION_HYGIENE_PARTIAL` because row-level error-to-event linkage is still `UNKNOWN`. The missing historical `ERROR_SoSimple_163856259.csv` and cumulative tester-agent log are no longer blockers for current batch follow-up.

## Limitations / Open Questions

- Historical `ERROR_SoSimple_163856259.csv` is missing and abandoned as non-reproducible; do not use it in future conclusions.
- Historical cumulative tester agent log containing external `ERROR-4756` lines is missing and abandoned as non-reproducible; do not use it in future conclusions.
- Batch INI, batch compile log, terminal log, and agent log were not saved as batch artifacts.
- Error/event linkage is `UNKNOWN`; no causality is inferred.
- Cost model remains incomplete: swap, commission, slippage, latency, and stress-cost checks are not closed.

## Split Disclosure

Batch period: XAUUSD H1 validation 2021.01.04-2022.12.02 from the 2026-07-31 batch. This diagnostic did not use `locked_test` or holdout for any selection, threshold, feature, entry, exit, stop, spread, cost, or PnL convention decision.

## Forbidden Interpretations

Do not interpret tester PF/PnL as profitable, production-ready, live-ready, tradable, or model-quality proof. Do not treat this report as a new winner selection or as permission to open `locked_test`.

## Next Step

Exactly one next action: plan the next frozen probe using only current saved batch artifacts; do not wait for historical `ERROR-4756` logs or `ERROR_SoSimple_163856259.csv`.

## Related Materials

- `docs/superpowers/plans/2026-08-01-mt5-execution-hygiene-postbatch.md`
- `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md`
- `docs/reports/2026-07-30-mt5-single-rule-diagnostic-run.md`
- `docs/reports/2026-07-31-mt5-ontradetransaction-lifecycle.md`
- `docs/reports/2026-07-31-mt5-nero-parity.md`
- `docs/reports/2026-07-31-mt5-batch-selection.md`
- `docs/superpowers/roadmap.md`
- `ML/reports/mt5_execution_loop/diagnostics/`
