---
name: ml-leakage-preflight
description: "Use before ML work that may be interpreted as model quality: training, validation/test benchmark, frozen test, feature/target/preprocessing/normalization changes."
---

# ML Leakage Preflight

## Purpose

Prevent invalid ML conclusions from data leakage, mismatched training/online contracts, target-derived inputs, or post-test selection.

The source of truth is [`docs/ML/ml_leakage_preflight_checklist.md`](../../../docs/ML/ml_leakage_preflight_checklist.md). Open it before making or approving ML-quality claims.

## When To Use

Use for:

- model training or retraining;
- validation/test/frozen-test benchmark;
- changes to feature builders, target builders, preprocessing, normalization, split logic, exporters, or online runners.

Do not run as a full gate for purely mechanical diagnostics, such as checking that files are written, logs rotate, or watcher plumbing works. Those runs must be labeled `DIAGNOSTIC_ONLY`.

## Workflow

1. Read `docs/ML/ml_leakage_preflight_checklist.md`.
2. Identify the decision time and whether the run is ML evidence or `DIAGNOSTIC_ONLY`.
3. Build or inspect the feature/source contract: role, source, available_at, normalization, model_input.
4. Check all gates in the checklist before using validation/test/MT4/online metrics as evidence.
5. If any gate is `FAIL` or `UNKNOWN`, stop ML-quality interpretation and report the blocker.
6. If producing a report, include the minimal evidence required by the checklist.

## Output

State the verdict explicitly:

```text
ML Leakage Preflight: PASS | FAIL | UNKNOWN | DIAGNOSTIC_ONLY
Evidence: <paths to contract/report/scripts>
Blockers: <only if not PASS>
```
