---
kind: business_term
name: Business Glossary
category: business_term
scope:
    - '**'
---

### locked_test
- Definition：A single, frozen evaluation run on a holdout dataset that is opened exactly once for a fixed set of rules without any post-hoc tuning. It is the final historical check before a candidate can advance toward production. The term carries methodological weight: if the same file was previously used for feature/model/threshold selection, it becomes an invalidated holdout rather than a valid locked_test.
- Aliases：frozen test、OOS test

### validation freeze
- Definition：The protocol of selecting one winner rule on validation data and freezing all aspects of that rule (entry, exit, stop, mask, model profile, target, filter, cutoff, spread, execution contract) before opening locked_test. Any change to these frozen fields invalidates the frozen rule.
- Aliases：freeze、frozen_rule_for_locked_test

### Fractal0
- Definition：A specific fractal configuration/profile used as the basis for the 11-system locked-test portfolio selection. Fractal0 refers to the first level of fractal detection in the NERO pipeline, with its associated features (fractal0–fractal99, each with 23 fields).
- Aliases：fractal0、F0

### Nero.csv
- Definition：The raw CSV output from MT4's `$o$imple.mq4` expert via `NERO_CSV_CREATE()`. Contains time, signal, predict, ATR, and fractal0–fractal99 columns (each with 23 fields). This is the canonical input to the Python preprocessing pipeline.
- Aliases：raw NER0 data、source CSV

### Up/Dn targets
- Definition：Ten directional-independent targets representing maximum favorable excursion (MFE) and maximum adverse excursion (MAE) over fixed horizons: up_3, dn_3, up_6, dn_6, up_12, dn_12, up_24, dn_24, up_48, dn_48. These are computed in MT4's `lib_PIC.mqh` and exported incrementally, so they represent historical price reaction up to the current bar, not future knowledge.
- Aliases：up_dn_targets、MFE_MAЕ_targets

### Triple Barrier
- Definition：An alternative labeling scheme producing 12 binary columns (buy_sl2_tp3 … sell_sl3_tp9) based on SL/TP combinations applied to up_24/dn_24. Requires transfer learning from an existing encoder checkpoint to avoid encoder collapse. Uses BCEWithLogitsLoss instead of DirectionalAsymmetricLoss.
- Aliases：TB labels、triple_barrier

### PF (Profit Factor)
- Definition：Ratio of gross profit to gross loss, used as a key gate metric. In this project, PF must pass multiple checks: net PF >= 1.20 on locked_test, yearly/quarterly breakdowns, BUY/SELL side analysis, and profit concentration diagnostics. Aggregate PF alone cannot hide negative years or weak sides.
- Aliases：profit factor、pf

### BS_p05
- Definition：Bootstrap percentile-5 lower bound on profit factor, computed via block bootstrap over trade PnL sequences. Used as a risk-adjusted tie-breaker and gate criterion to ensure PF stability under temporal correlation of trades.
- Aliases：bootstrap_pf_lower_bound、bs_p05

### execution_order_diagnostic
- Definition：Analysis using M5 OHLC to resolve TP/SL ambiguity within H1 bars where both conditions could trigger simultaneously. Records ambiguous_same_bar_rate_h1 and ambiguous_same_bar_rate_m5, with fallback policies when resolution is NOT_COMPUTABLE. Used only for disclosure, never to change candidate ranking.
- Aliases：same_bar_resolution、M5_diagnostics

### model_card
- Definition：Structured artifact required for every KEEP_CANDIDATE, containing instrument/timeframe, decision_time, feature/target contracts, train/validation/locked_test windows, rule/export paths, cumulative search budget, cost assumptions, verdicts, known risks, monitoring/retraining policy, and stop conditions.
- Aliases：model card、model_card

### cumulative_search_budget
- Definition：Total count of configurations searched across models × profiles × targets × sides × horizons × seeds × instruments × entry/exit policies × spread/fill conventions × transforms/scalers × filters × parameters. Must be disclosed in reports to contextualize multiple testing correction and overfit risk.
- Aliases：search_budget、multiple_testing_budget

### effective_profit_years
- Definition：Diversity metric for profit distribution across years, calculated as 1 / sum(share_y^2) where share_y is each year's gross profit divided by total gross profit. Values near 1.0 indicate profit concentrated in one year; higher values indicate more distributed profitability. Gate threshold: effective_profit_years >= max(1.5, 0.6 * n_years).
- Aliases：profit_diversity、effective_years

### sample_size_gate
- Definition：Minimum requirements for train/validation/locked_test periods: raw rows, independent events, classes/sides, trades after filters, coverage across months/years. Default thresholds include >=100 trades after filters, >=30 per active side, and coverage of at least 3 calendar months for regime-local diagnostic avoidance.
- Aliases：sample_gate、minimum_sample_size

### val-stop / val-select / val-eval
- Definition：Three distinct roles that validation data can play: val-stop for model-influencing actions (early stopping, epoch count, ablation winner); val-select for trading parameter tuning (threshold/top-k/grid search, rule-family selection); val-eval for final evaluation of the chosen rule before locked_test. When combined in one validation period, status is limited to RESEARCH_ONLY.
- Aliases：validation_roles、val_split

### canonical_spread
- Definition：The production spread assumption used throughout backtesting and locked_test evaluation. In this project, canonical_spread=0.2 (full bid-ask spread). Zero-spread results are DIAGNOSTIC_ONLY and cannot serve as production gates.
- Aliases：spread_assumption、production_spread

### OHLC price convention
- Definition：Specification of whether OHLC data represents bid, ask, mid, or broker/tester executable price, and how spread is defined (full bid-ask spread vs pre-shifted unfavorable price). Critical for SL-trigger logic and PnL calculation. Unknown convention limits verdict to DIAGNOSTIC_ONLY.
- Aliases：price_type、OHLC_convention

### forward-test
- Definition：Live or simulated trading on data after the decision date, not cut from historical data. Required to advance from candidate to confirmed status. If no forward data exists, verdict cannot exceed watch/no_forward_data.
- Aliases：live_test、forward_validation

### verdict statuses
- Definition：Standardized outcome classifications: PASS (proceed), FAIL (blocking defect), UNKNOWN (insufficient data, treat as FAIL), DIAGNOSTIC_ONLY (pipeline mechanics only, no profitability claims), reject, research_only, candidate, unknown. Each status has specific implications for next steps and allowed interpretations.
- Aliases：status、verdict
