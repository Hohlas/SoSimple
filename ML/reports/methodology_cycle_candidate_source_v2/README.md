# Methodology Cycle: Candidate Source v2

Date: 2026-05-24

This directory contains Stage 0-2 artifacts for the new ML cycle run under `docs/methodology/README.md`.

## Files

- `stage00_research_contract.json` - hypothesis, decision time, decision unit, split protocol, gates, and expected artifacts.
- `stage01_raw_data_inventory.json` - raw CSV and producer inventory.
- `feature_contract.csv` - field-level live-safe contract.
- `candidate_source_live_safe_audit.md` - candidate-source verdict and restrictions.
- `stage01_gate_verdict.json` - stage verdicts and next allowed stage.
- `stage02_scale_audit_inputs.csv` - scale audit for current prepared input fields/families.
- `stage02_scale_audit_targets.csv` - scale audit for current prepared target/label fields.
- `stage02_dominance_check.csv` - p99 dominance check for draft normalization pools.
- `stage02_normalization_groups_draft.json` - draft normalization groups and hard rules.
- `stage02_pipeline_manifest.json` - Stage 2 data source and artifact manifest.
- `stage02_gate_verdict.json` - Stage 2 verdict.

## Current Verdict

Stage 0: `PASS`

Stage 1: `PASS`

Stage 2: `FAIL`

Reason: `DATA/Nero_*_labeled.csv` were rebuilt from the updated historical raw
`MT/MQL4/Files/Nero.csv` with `--no-normalize`, and scale audit artifacts were
generated. Final Stage 2 `PASS` is still blocked by normalization design issues:

- `input_power_count_reverse_break` has dominance (`p99_ratio=32.5`);
- `target_ret_fav_adv` has dominance (`p99_ratio=1693.0`);
- final ATR/volatility contract is still open.

Next allowed action: split/revise those normalization pools and freeze the
normalization contract. Stage 3 is blocked until Stage 2 receives explicit
`PASS`.
