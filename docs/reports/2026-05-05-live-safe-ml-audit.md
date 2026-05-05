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
- `ML/reports/live_safe_ml_audit/<system>/legacy_export.csv`
- `ML/reports/live_safe_ml_audit/<system>/legacy_export_metadata.json`
- `ML/reports/live_safe_ml_audit/<system>/verdict.json`

## What Was Done

- Registered five mature systems: `quality`, `frequency`, `original_plus_path`,
  `entry_path_v1`, `entry_path_v1_quantile`.
- Built artifact inventories for checkpoints, rules, predictions, and reports.
- Built feature/source trace tables.
- Applied the leakage/preflight gate.
- Summarized old frozen metrics from existing artifacts only.
- Replayed legacy signal export from old predictions and old frozen rules.
- Wrote explicit verdicts for each system.

No model was retrained. No threshold was changed. No online trading was run.

The follow-up `entry_path_v1_live_safe` retrain below was added after the audit
verdict. It is part of the same decision chain: first reject the unsafe old
checkpoint, then test whether the same trading idea survives without the
future-derived input.

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

## Legacy Export Replay

This is a diagnostic check with old inputs and old rules. Its goal is to prove
that the saved prediction/rule/export path still runs and produces trade
signals. It does not prove that the model is valid for online trading.

| System | Export rows | Non-zero signals | BUY | SELL |
|---|---:|---:|---:|---:|
| `quality` | 8887 | 30 | 21 | 9 |
| `frequency` | 8887 | 78 | 50 | 28 |
| `original_plus_path` | 8887 | 37 | 24 | 13 |
| `entry_path_v1` | 8872 | 23 | 17 | 6 |
| `entry_path_v1_quantile` | 8872 | 18 | 13 | 5 |

All replay outputs are marked `diagnostic_only=true` in
`ML/reports/live_safe_ml_audit/legacy_export_summary.json`.

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

## Entry Path v1 Live-Safe Retrain

The first rebuild target was `entry_path_v1`, because it failed only on
`ret_dir_atr_lag1`, while the rest of its built-in feature profile could be
kept.

New profile: `entry_path_v1_live_safe`.

Feature change:

- old profile: `session_hour`, `weekday`, `range_atr_6`, `body_atr_3`,
  `ret_dir_atr_lag1`, `vol_regime_24`, row feature-bank columns;
- new profile: same columns, but without `ret_dir_atr_lag1`.

The old `entry_path_v1` profile is kept for legacy reproduction only.

### Single-Seed Result

Seed `42` retrain:

| Check | Trades | PF | Win rate | Notes |
|---|---:|---:|---:|---|
| validation winner `A @ 7.5%` | 36 | 2.8881 | 66.67% | selected on validation |
| frozen test | 37 | 3.6567 | 72.97% | same validation threshold |
| sequential test | 25 | 2.3419 | 68.00% | fixed 24-bar single-position check |

Signal export:

| File | Rows | Non-zero | BUY | SELL |
|---|---:|---:|---:|---:|
| `entry_path_v1_live_safe_test_signals.csv` | 8872 | 26 | 19 | 7 |

Comparison with old invalid `entry_path_v1`:

- old sequential: 30 trades, PF 2.87, win rate 66.67%;
- new live-safe sequential: 25 trades, PF 2.3419, win rate 68.00%.

Meaning: profitability did not survive unchanged. Trade count and PF are lower,
but the system did not collapse after removing the unsafe input.

### Multi-Seed Follow-Up

The retrain was repeated with seeds `7`, `17`, `42`, `77`, `123`.

`seed` means the starting number for controlled randomness. With the same seed,
training is repeatable. With different seeds, the model starts differently, so
the check shows whether a result is stable or just lucky.

| Seed | Val ret r | Winner | Test PF | Sequential trades | Sequential PF | Export supported |
|---:|---:|---|---:|---:|---:|---|
| 7 | 0.2792 | `B_no_path6` | 4.3044 | 32 | 2.7922 | no |
| 17 | 0.2796 | `B` | 6.3893 | 25 | 4.5985 | no |
| 42 | 0.2681 | `A` | 3.6567 | 25 | 2.3419 | yes |
| 77 | 0.2844 | `A` | 2.0024 | 32 | 1.5171 | yes |
| 123 | 0.2767 | `A` | 2.7762 | 33 | 1.8633 | yes |

Summary:

- median sequential PF: `2.3419`;
- min sequential PF: `1.5171`;
- max sequential PF: `4.5985`;
- PF > 2.0: `3 / 5` seeds;
- PF <= 1.0: `0 / 5` seeds;
- same winner: `A` in `3 / 5` seeds;
- MT4 signal export is currently supported only for `A` winners.

Updated retrain verdict: the live-safe `entry_path_v1` idea is alive but not
fully stable. Removing `ret_dir_atr_lag1` did not destroy profitability, but the
result is weaker and more variable than the old invalid system. MT4 parity is
intentionally deferred.

Artifacts:

- `ML/checkpoints/transformer_entry_path_v1_features_entry_path_v1_live_safe_best.pt`
- `ML/checkpoints/transformer_entry_path_v1_features_entry_path_v1_live_safe_result.json`
- `ML/reports/entry_path_v1_live_safe/`
- `ML/reports/entry_path_v1_live_safe/multi_seed_summary.csv`
- `ML/reports/entry_path_v1_live_safe/multi_seed_summary.json`
- `ML/reports/entry_path_v1_live_safe/seed_*/`

## Conclusions

The old high-PF take/skip checkpoints are not valid online candidates as-is.
They can still guide a live-safe rebuild, but they must not be used as proof of
online ML quality.

The first live-safe rebuild of `entry_path_v1` has now been run. It is not a
production approval, but it is enough to reject the worst fear: removing
`ret_dir_atr_lag1` did not make the system unprofitable.

Next decision, before any MT4 work: either freeze the exporter-supported `A`
rule family, or extend the signal exporter for `B` / `B_no_path6`. Only after a
chosen live-safe baseline is fixed should `entry_path_v1_quantile` be rebuilt
and judged again.

## Verification

Commands run:

```bash
./.venv/bin/python -m pytest tests/test_live_safe_audit.py -q
./.venv/bin/python -m ML.run_live_safe_ml_audit --phase all --output-dir ML/reports/live_safe_ml_audit
./.venv/bin/python -m pytest tests/test_entry_path_task.py tests/test_entry_path_training.py tests/test_entry_path_v1_quantile_reports.py tests/test_live_safe_audit.py -q
```

Results:

- `12 passed`
- `34 passed`
- audit files generated for all five systems
- legacy export replay generated for all five systems
- live-safe `entry_path_v1` retrain and multi-seed artifacts generated
