# Live-Safe ML Audit

> **Date**: 2026-05-05
> **Goal**: Re-audit profitable ML systems before any online trading decision.
> **Gate**: [`docs/ML/ml_leakage_preflight_checklist.md`](../ML/ml_leakage_preflight_checklist.md)

## Context

The project had several profitable historical ML systems. After the online
inference contract hardening, high PF is no longer enough: every system must
prove that its model inputs are available at the trading decision time.

This audit separates two things:

- legacy result: old frozen artifact metrics, without retraining or changing thresholds;
- live-safe verdict: whether the same checkpoint/rule can be trusted for online ML quality.

Generated evidence lives in:

- `ML/reports/live_safe_ml_audit/manifest.json`
- `ML/reports/live_safe_ml_audit/<system>/artifact_inventory.json`
- `ML/reports/live_safe_ml_audit/<system>/feature_contract.csv`
- `ML/reports/live_safe_ml_audit/<system>/source_trace.csv`
- `ML/reports/live_safe_ml_audit/<system>/legacy_reproduction.json`
- `ML/reports/live_safe_ml_audit/<system>/verdict.json`

## What Was Done

- Registered five mature systems: `quality`, `frequency`, `original_plus_path`,
  `entry_path_v1`, `entry_path_v1_quantile`.
- Built artifact inventories for checkpoints, rules, predictions, and reports.
- Built feature/source trace tables.
- Applied the leakage/preflight gate.
- Summarized old frozen metrics from existing artifacts only.
- Wrote explicit verdicts for each system.

No model was retrained. No threshold was changed. No online trading was run.

## Legacy Results

These numbers are historical artifact summaries. They are useful for comparing
ideas, but not by themselves enough for online approval.

| System | Legacy test PF | Trades / frequency | Source |
|---|---:|---:|---|
| `quality` | `39.74` | 41 trades | `take_skip_trailing_stop_v2_quality_selected_rule.json` |
| `frequency` | `13.12` | 16.4 trades/year | `take_skip_trailing_stop_v2_frequency_selected_rule.json` |
| `original_plus_path` | `38.78` | 51 trades | `take_skip_trailing_stop_v2_original_plus_path_selected_rule.json` |
| `entry_path_v1` | `2.87` sequential | 30 trades | `entry_path_trade_filter_selected_rule.json` |
| `entry_path_v1_quantile` | `8.18` frozen test, `3.64` sequential | 48 / 22 trades | `entry_path_v1_quantile_selected_rule.json` |

## Feature Findings

The three take/skip systems share the old row-feature family. Their input set
contains future-derived fields:

- `predict`
- `ret_6_dir_atr`, `ret_12_dir_atr`, `ret_24_dir_atr`
- `fav_3_atr`, `adv_3_atr`, `fav_6_atr`, `adv_6_atr`
- `fav_12_atr`, `adv_12_atr`, `fav_24_atr`, `adv_24_atr`

They also contain `ret_dir_atr_lag1`. Follow-up source audit closed this as
future-derived: `processing/label_signals.py:add_entry_path_frequency_features`
builds it as `ret_6_dir_atr.shift(1)`, while `label_entry_path_targets()` builds
`ret_6_dir_atr` from future bars after the signal row.

`entry_path_v1` does not include the take/skip forbidden row fields, but it does
include `ret_dir_atr_lag1`. Therefore the current checkpoint is not live-safe.

`entry_path_v1_quantile` depends on the `entry_path_v1` baseline score in the
production rule. Therefore it inherits the failed baseline risk.

## Verdicts

| System | Verdict | Reason | Allowed next step |
|---|---|---|---|
| `quality` | `FAIL` | future-derived model inputs | reject old checkpoint for online or retrain/rebuild |
| `frequency` | `FAIL` | future-derived model inputs | reject old checkpoint for online or retrain/rebuild |
| `original_plus_path` | `FAIL` | future-derived model inputs | reject old checkpoint for online or retrain/rebuild |
| `entry_path_v1` | `FAIL` | `ret_dir_atr_lag1` is derived from future `ret_6_dir_atr` | rebuild/retrain without that input |
| `entry_path_v1_quantile` | `FAIL` | production rule depends on failed `entry_path_v1` baseline score | rebuild baseline dependency first |

No audited system currently has `PASS`.

## Conclusions

The old high-PF take/skip checkpoints are not valid online candidates as-is.
They can still guide a live-safe rebuild, but they must not be used as proof of
online ML quality.

The best next implementation target is a live-safe rebuild/retrain of
`entry_path_v1` without `ret_dir_atr_lag1`, or with a replacement whose source
and decision-time availability are proven. Only after that can
`entry_path_v1_quantile` be rebuilt and judged.

## Verification

Commands run:

```bash
./.venv/bin/python -m pytest tests/test_live_safe_audit.py -q
./.venv/bin/python -m ML.run_live_safe_ml_audit --phase all --output-dir ML/reports/live_safe_ml_audit
```

Results:

- `11 passed`
- audit files generated for all five systems
