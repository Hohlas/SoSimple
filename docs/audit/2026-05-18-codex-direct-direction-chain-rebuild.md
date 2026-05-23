# Direct Direction Chain Rebuild Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the direct-direction research chain from raw/current-row features, fix audit-proven data contract errors, and test only validation-selected candidates before one final frozen test.

**Architecture:** Separate feature source, target source, and diagnostic source. First prove data contracts with minimal tests. Then run validation-only experiments with explicit gates. Frozen test is allowed once, only for the single selected candidate.

**Tech Stack:** Python 3.12, pandas, numpy, scikit-learn, existing `processing`, `ML`, and `API` modules.

---

## Non-Negotiable Rules

- Do not use test split for hypotheses, parameters, thresholds, or model selection.
- Frozen test runs once for the final candidate.
- Build model inputs from raw/current-row data, not from normalized target-bearing split CSV.
- Top-level `up_*/dn_*`, `signal`, `predict`, `ret_*`, `fav_*`, `adv_*` are never model inputs.
- BUY and SELL must have side-specific gates.
- Repeated BUY/SELL and simultaneous opposite positions are allowed in the final execution model, so validation must report both all-signal PF and sequential PF.

## Task 1: Prove And Lock Data Contract

**Files:**
- Modify: `ML/fractal_level_feature_builder.py`
- Modify: `tests/test_fractal_level_feature_builder.py`
- Create: `ML/reports/direct_direction_chain_rebuild/data_contract_audit.json`

- [ ] Add a test proving top-level target perturbation must not change model features.
- [ ] Add a raw/current-row feature builder path that takes raw sorted rows before target normalization.
- [ ] Compute `raw_distance_atr` from raw prices and raw ATR.
- [ ] Add a parity report comparing raw/current-row features against current normalized split features.
- [ ] Gate: no model experiment can run until `target_perturbation_changes_features == false` and raw distance units are verified.

## Task 2: Fix Target Construction

**Files:**
- Modify: `ML/entry_path_direct_direction_targets.py`
- Modify: `tests/test_entry_path_direct_direction_targets.py`
- Create: `ML/reports/direct_direction_chain_rebuild/target_unit_audit.json`

- [ ] Rebuild Target A/C from raw `up/dn / ATR` or OHLC-derived moves.
- [ ] Keep Target D OHLC-based, but add explicit execution policy metadata.
- [ ] Report class balance and ambiguous rate by year for train/validation only.
- [ ] Gate: target family is eligible only if each side has enough validation examples and no major year is side-empty.

## Task 3: Fix Winner Selection And Diagnostics

**Files:**
- Modify: `ML/benchmark_entry_path_binary_direction.py`
- Modify: `ML/benchmark_entry_path_score_direction.py`
- Modify: `tests/test_benchmark_entry_path_binary_direction.py`
- Create: `ML/reports/direct_direction_chain_rebuild/selection_audit.json`

- [ ] Make winner selector explicit: exclude one-sided candidates unless experiment is intentionally one-sided.
- [ ] Require `negative_years == 0` on validation for balanced candidates.
- [ ] Decide ranking order before running: default `validation_sequential_pf`, then `validation_pf`, then trades.
- [ ] Fix `both_high_rate` to use current thresholds, not hard-coded `0.5`.
- [ ] Fix E5 score-direction selection to symmetric confidence: `max(P_BUY, P_SELL) >= threshold` or separate side thresholds.
- [ ] Gate: `summary.json` winner must match the config eligible for frozen test.

## Task 4: Validation-Only Experiment Matrix

**Files:**
- Create: `ML/reports/direct_direction_chain_rebuild/validation_leaderboard.csv`
- Create: `ML/reports/direct_direction_chain_rebuild/validation_summary.json`

- [ ] Run corrected binary RF/HGB/LR baselines on raw/current-row features.
- [ ] Run binary target grid for A/C/D variants on validation only.
- [ ] Run corrected score-direction resolver on validation only.
- [ ] Run BUY-only and SELL-repair experiments as separate candidates, not as post-test edits.
- [ ] Optional: test LightGBM/CatBoost only if dependencies already exist; otherwise use scikit-learn HGB/ExtraTrees/CalibratedClassifier first.
- [ ] Gate for balanced candidate: validation PF > 2.0 or materially better than current candidate, sequential PF > 2.0 or materially better, BUY PF >= 1.1, SELL PF >= 1.1, no negative major year.
- [ ] Gate for one-sided BUY candidate: mark explicitly one-sided, require validation PF >= 1.5, sequential PF >= 1.3, no negative major year, and explain production implication.

## Task 5: Robustness Before Frozen Test

**Files:**
- Create: `ML/reports/direct_direction_chain_rebuild/robustness_summary.json`

- [ ] Run multi-seed validation for top candidates.
- [ ] Run walk-forward validation inside train+validation only.
- [ ] Add bootstrap confidence intervals for PF on validation trades.
- [ ] Reject candidates whose profit is dominated by one year or one side.
- [ ] Select one candidate and freeze all config fields in JSON.

## Task 6: Single Frozen Test

**Files:**
- Create: `ML/reports/direct_direction_chain_rebuild/frozen_candidate.json`
- Create: `ML/reports/direct_direction_chain_rebuild/frozen_test.json`

- [ ] Retrain only the selected candidate on train+validation.
- [ ] Run test once.
- [ ] Report all-signal PF, sequential PF, BUY/Sell PF, yearly PF, trade count, mean PnL ATR.
- [ ] If it fails gates, do not tune on test. Close the line or return to validation with a new plan and a newly reserved future test.

## Task 7: Report And Wiki

**Files:**
- Create: `docs/reports/YYYY-MM-DD-direct-direction-chain-rebuild.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/execution-tracks-reconciliation-plus-audit.md` or create a new wiki research page
- Modify: `wiki/index.md`

- [ ] Write the final report with commands and artifact paths.
- [ ] Update handoff and changelog.
- [ ] Ingest `2026-05-15` and rebuild reports into wiki.
- [ ] Run `python wiki/wiki.py generate`.

## Stop Conditions

- If feature provenance cannot be made independent of target-only columns, stop.
- If corrected validation cannot beat the current candidate meaningfully, stop.
- If BUY/Sell balance is impossible without SELL PF collapse, consider one-sided BUY only as a separate product decision.
- If all validation candidates remain below PF/SeqPF 2.0 and unstable by year, the honest next step is forward data collection, not more historical tuning.
