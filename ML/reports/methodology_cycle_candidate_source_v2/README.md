# Methodology Cycle: Candidate Source v2

Date: 2026-05-25

This directory contains Stage 00-09 artifacts for the ML cycle run under `docs/methodology/README.md`.

## Files

- `stage00_research_contract.json` — hypothesis, decision time, decision unit, split protocol, gates, expected artifacts
- `stage01_raw_data_inventory.json` — raw CSV and producer inventory
- `stage01_gate_verdict.json` — unified verdicts for all stages, next allowed stage
- `feature_contract.csv` — field-level live-safe contract (32 rows)
- `candidate_source_live_safe_audit.md` — candidate-source verdict and restrictions
- `stage02_data_pipeline.json` — pipeline manifest: commands, split, normalization groups, hashes
- `stage02_scale_audit_inputs.csv` — scale audit for input fields/families
- `stage02_scale_audit_targets.csv` — scale audit for target/label fields
- `stage02_dominance_check.csv` — p99 dominance check for normalization pools
- `stage03_leakage_gate.json` — ML Leakage Preflight: 14 checks PASS
- `stage04_labeling_audit.json` — label convention audit: 56 targets, TB/updn/trail conventions
- `stage05_eda_audit.json` — EDA: no NaN/Inf, regime shift detected, test NOT viewed
- `stage06_temporal_split_manifest.json` — sequential split manifest and validation/test use rules
- `stage07_baselines.json` — Baselines: RF PF=1.58 (all 12 TB + trail tested)
- `stage08_model_sweep.json` — Model sweep: Transformer PF=11.60, BiLSTM PF=1.74 (binary TP-vs-SL, timeout excluded)
- `stage08_validation_predictions.csv` — Validation predictions from Stage 08 exploratory sweep
- `stage09_frozen_rule.json` — Frozen winner: Transformer 3-class, stability-refrozen threshold, PF=1.97, 142 trades
- `stage09_stability_refreeze.json` — Validation-only threshold/top-k stability scan; test not viewed

## Current Verdicts

| Stage | Verdict | Note |
|-------|---------|------|
| 00 — Research Management | PASS | Hypothesis, gates, split protocol fixed |
| 01 — Raw Data Inventory | PASS | All fields classified, producer audited |
| 02 — Data Pipeline | PASS | Sort→label→split, PLL normalizer, dominance resolved |
| 03 — Feature Contract / Leakage | PASS | 14/14 preflight PASS, 5 production-gate pending model |
| 04 — Labeling | PASS | TB convention explicit, up/dn monotonic, timeout separated |
| 05 — EDA / Data Quality | PASS | Train+val only. Regime shift detected (ATR KS=0.56). Test NOT viewed. |
| 06 — Temporal Split | PASS | Sequential manifest added; no overlap, no shuffle, 0 sorting errors |
| 07 — Baselines | PASS | RF baseline plus confusion/classification/per-year diagnostics; RF has 1 neg year |
| 08 — Model Sweep | PASS | Exploratory validation-only sweep with timeout-excluded binary formulation |
| **09 — Validation Freeze** | **PASS** | **Transformer stability rule PF=1.97, 142 trades, 0 neg yrs, 4 active years** |

Next allowed stage: `10-frozen-test-oos`
