# 2026-05-24 Methodology Review Notes

## Scope

Review target:
- `docs/methodology/`
- `.claude/skills/ml-methodology/SKILL.md`

Reference context:
- `AGENTS.md`
- `docs/PRD.md`
- `docs/DATA_FLOW.md`
- `docs/dataset_description.md`
- `CONTEXT_HANDOFF.md`
- `CHANGELOG.md` first 400 lines

Review criteria:
1. Stage structure: whether the methodology covers the stages required for ML trading.
2. Best practices: leakage prevention, temporal validation, baselines, cost-aware evaluation, walk-forward, reproducibility.
3. Project fit: Forex H1, event-driven data, MT4 execution, and SoSimple-specific gaps.
4. Skill trigger coverage for real project scenarios.

## Summary

The methodology structure is broadly sound. It covers the main ML-trading lifecycle:
research management, raw data inventory, pipeline, leakage gate, labeling, EDA,
temporal split, baselines, model development, validation freeze, frozen test,
robustness, cost-aware backtest, MT4 parity, forward test, monitoring and reporting.

The main gaps are not missing whole stages, but weak gates in high-risk places:
purging/embargo near split boundaries, statistical uncertainty of validation winners,
risk sizing before launch, and hidden rules that are easy to miss when agents follow
only one methodology file.

## Findings

### 1. Embargo / purging is too weak for event-driven fixed-horizon labels

File: `docs/methodology/06-temporal-split.md:19`

Issue:
The methodology says: "If label horizon crosses the split boundary, evaluate whether
an embargo gap is needed." For financial time series with fixed horizons 3/6/12/24/48
bars and event-driven rows, this is too soft. Rows near the split boundary may have
labels that depend on future bars already inside the next split.

Why it matters:
The project uses event-driven snapshots and fixed-horizon MFE/MAE targets. Split leakage
can happen even when rows are not shuffled.

Hypothesis:
If the current split is index-only without purging/embargo, some train labels near a
boundary may use price path from validation/test periods.

Recommended fix:
Make purging/embargo an explicit required decision:
- compute max label horizon in bars/time;
- document whether overlap exists;
- require either an embargo gap or a written proof that no label/result crosses the split boundary.

### 2. Validation winner selection lacks statistical uncertainty checks

File: `docs/methodology/09-validation-freeze.md:17`

Issue:
The methodology allows validation grid/sweep and checks trade count, yearly/monthly
slices, BUY/SELL, drawdown and profit concentration. It does not require confidence
intervals, bootstrap, multiple-testing awareness, or another uncertainty estimate.

Why it matters:
SoSimple has repeatedly produced high PF on very small samples. Example from current
handoff: Trail PF=2.41 on 58 trades and 0.6% utilisation. Minimum trade gates reduce
risk, but they do not measure statistical uncertainty.

Recommended fix:
Add a required uncertainty section for validation winners:
- confidence interval or bootstrap for PF/EV/trade;
- number of tried configurations;
- explicit overfit risk note for small-N winners;
- automatic downgrade to `research_only` when the winner depends on sparse trades.

### 3. SeqPF ban is hidden in an appendix and easy to miss

Files:
- `docs/methodology/README.md:12`
- `docs/methodology/A3-typical-false-conclusions.md:23`

Issue:
The README tells agents not to read every file, but the important rule "SeqPF is not a
valid model-quality metric" appears only in Appendix A3. An agent working only through
`09-validation-freeze.md`, `10-frozen-test-oos.md` or `11-robustness.md` can miss it.

Why it matters:
`CONTEXT_HANDOFF.md` and `CHANGELOG.md` both record that SeqPF was invalidated by a
shuffle test with extreme variance. This should be visible in the main validation/test
stages, not only in an appendix.

Recommended fix:
Add explicit notes to:
- `09-validation-freeze.md`: SeqPF must not be a winner-selection gate;
- `10-frozen-test-oos.md`: SeqPF may be reported only as diagnostic;
- `11-robustness.md`: sequential simulation is for position-constraint diagnostics,
  not model-quality proof.

### 4. Target prefix rule conflicts with legacy SoSimple dataset names

Files:
- `docs/methodology/02-data-pipeline.md:37`
- `docs/methodology/04-labeling.md:20`
- `docs/dataset_description.md:10`

Issue:
`02-data-pipeline.md` requires target/label columns to have explicit prefixes. The
current canonical dataset uses legacy names without prefixes: `signal`, `predict`,
`up_3..dn_48`. `04-labeling.md` allows legacy names when an explicit allowlist/denylist
contract exists, but `02-data-pipeline.md` does not repeat that exception.

Why it matters:
This creates an internal inconsistency. A strict audit of the current dataset could
fail the pipeline stage even though the labeling stage allows legacy columns with a
proper denylist.

Recommended fix:
Align `02-data-pipeline.md` with `04-labeling.md`:
- new target columns require `target_`, `label_` or `outcome_`;
- legacy columns are allowed only with explicit denylist/allowlist and feature-builder tests.

### 5. Slippage guidance is over-specific and poorly grounded

File: `docs/methodology/12-backtest-costs.md:33`

Issue:
The methodology states that 0.5-1.0 ATR slippage is realistic. For XAUUSD H1 this is
too strong without broker/tester evidence. Slippage should come from MT4/broker logs
in points or price units. ATR multiples are useful for stress tests, not as a default
realistic assumption.

Why it matters:
Bad execution assumptions can either kill a viable candidate or make cost-aware
evaluation inconsistent with MT4 reality.

Recommended fix:
Change the wording:
- base slippage: measured from MT4/tester/online logs;
- stress slippage: ATR-based scenarios, clearly marked as stress tests.

### 6. Risk sizing is not a pre-launch gate

File: `docs/methodology/12-backtest-costs.md:17`

Issue:
The backtest stage covers costs and position limits, but does not require a separate
risk-sizing contract: lot size, risk per trade, max exposure, margin/leverage,
stop-out risk, and portfolio exposure. Risk limits appear later in monitoring, but
not as a pre-launch gate.

Why it matters:
For trading systems, PF and drawdown are not enough. The same signal rule can be safe
or unsafe depending on sizing and exposure constraints.

Recommended fix:
Add a required "Risk sizing and exposure" block to the backtest/pre-launch stage:
- lot sizing rule;
- max open exposure;
- margin/leverage assumptions;
- risk per trade/day/week;
- stop-out / account ruin guard;
- behavior after consecutive losses or drawdown threshold.

### 7. `production_candidate` status is too permissive around robustness vs walk-forward

File: `docs/methodology/A4-verdicts-stop-conditions.md:9`

Issue:
`production_candidate` requires robustness or walk-forward. These checks cover different
risks and should not be freely interchangeable without a written reason.

Why it matters:
A candidate can pass one robustness slice but fail real forward behavior, or pass one
walk-forward window while still being fragile by side/year/provider. The current wording
can over-promote candidates.

Recommended fix:
Use one of these stricter rules:
- require both robustness and walk-forward for `production_candidate`; or
- allow one to substitute for the other only with a documented reason and downgrade
  the status to `candidate` or `research_only` when evidence is incomplete.

### 8. Skill trigger misses several SoSimple-specific scenarios

File: `.claude/skills/ml-methodology/SKILL.md:10`

Issue:
The skill trigger covers general ML scenarios, but does not explicitly name several
real SoSimple tasks:
- candidate-source live-safe audit;
- signal filter audit;
- `entry_path` research;
- execution policy;
- online watcher contract;
- OHLC-derived feature contamination;
- MT4 tester vs online reconciliation.

Why it matters:
Agents may skip the methodology for a "trading rule" or "watcher" task because it does
not look like model development, even though those tasks can invalidate ML conclusions.

Recommended fix:
Expand the trigger list with project-specific phrases:
- candidate-source and signal gate audits;
- entry/exit/execution policy;
- live-safe watcher and online preprocessing contract;
- OHLC-derived feature/target contamination;
- MT4 tester/online parity and reconciliation.

## Non-findings

No major missing lifecycle stage was found. The methodology already covers:
- leakage prevention;
- temporal split;
- baseline-first workflow;
- validation freeze;
- frozen test;
- robustness/provider drift/transfer;
- cost-aware backtest;
- MT4 export parity and reconciliation;
- forward testing;
- monitoring/retraining;
- reporting and model card.

The strongest improvement area is tightening existing gates, not adding a new parallel
methodology.
