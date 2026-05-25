# Methodology Cycle: Candidate Source v2

Date: 2026-05-25

This directory contains Stage 00-05 artifacts for the ML cycle run under `docs/methodology/README.md`.

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

## Current Verdicts

| Stage | Verdict | Note |
|-------|---------|------|
| 00 — Research Management | PASS | Hypothesis, gates, split protocol fixed |
| 01 — Raw Data Inventory | PASS | All fields classified, producer audited |
| 02 — Data Pipeline | PASS | Sort→label→split, PLL normalizer, dominance resolved |
| 03 — Feature Contract / Leakage | PASS | 14/14 preflight PASS, 5 production-gate pending model |
| 04 — Labeling | PASS | TB convention explicit, up/dn monotonic, timeout separated |
| 05 — EDA / Data Quality | PASS | Train+val only. Regime shift detected (ATR KS=0.56). Test NOT viewed. |

Next allowed stage: `06-temporal-split`
