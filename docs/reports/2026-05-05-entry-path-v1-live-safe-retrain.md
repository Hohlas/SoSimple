# Entry Path v1 Live-Safe Retrain

> **Date**: 2026-05-05
> **Goal**: Check whether `entry_path_v1` remains profitable after removing the future-derived input `ret_dir_atr_lag1`.
> **Gate**: `docs/ML/ml_leakage_preflight_checklist.md`

## Context

The live-safe ML audit proved that the old `entry_path_v1` checkpoint is not
valid for online use because its feature contract includes `ret_dir_atr_lag1`.
That column is built from `ret_6_dir_atr.shift(1)`, while `ret_6_dir_atr` itself
is a future-return target.

This stage keeps the old system reproducible and adds a new feature profile:
`entry_path_v1_live_safe`.

## Feature Change

Old built-in profile:

- `session_hour`
- `weekday`
- `range_atr_6`
- `body_atr_3`
- `ret_dir_atr_lag1`
- `vol_regime_24`
- row feature-bank columns

New live-safe profile:

- same columns, but without `ret_dir_atr_lag1`

The old `entry_path_v1` profile is kept for legacy reproduction only.

## Commands

```bash
./.venv/bin/python -m ML.train \
  --model transformer \
  --task entry_path_v1 \
  --epochs 5 \
  --seed 42 \
  --entry_path_feature_profile entry_path_v1_live_safe \
  --clear_cache

./.venv/bin/python -m ML.export_entry_path_predictions \
  --task entry_path_v1 \
  --input-csv DATA/Nero_validation_labeled.csv \
  --checkpoint ML/checkpoints/transformer_entry_path_v1_features_entry_path_v1_live_safe_best.pt \
  --output ML/reports/entry_path_v1_live_safe/entry_path_v1_live_safe_validation_predictions.csv \
  --feature-profile entry_path_v1_live_safe

./.venv/bin/python -m ML.export_entry_path_predictions \
  --task entry_path_v1 \
  --input-csv DATA/Nero_test_labeled.csv \
  --checkpoint ML/checkpoints/transformer_entry_path_v1_features_entry_path_v1_live_safe_best.pt \
  --output ML/reports/entry_path_v1_live_safe/entry_path_v1_live_safe_test_predictions.csv \
  --feature-profile entry_path_v1_live_safe

./.venv/bin/python -m ML.benchmark_entry_path_trade_filter \
  --validation-csv ML/reports/entry_path_v1_live_safe/entry_path_v1_live_safe_validation_predictions.csv \
  --test-csv ML/reports/entry_path_v1_live_safe/entry_path_v1_live_safe_test_predictions.csv \
  --output-dir ML/reports/entry_path_v1_live_safe \
  --coverage-grid 0.05 0.075 0.10 0.125 0.15 0.20 0.25 0.30
```

## Results

Training:

| Metric | Value |
|---|---:|
| best epoch | 4 |
| best validation `ret_pearson_r` | 0.2681 |
| validation `path_reg_pearson_r` | 0.2975 |
| validation `path_cls_f1_macro` | 0.3904 |

Trade filter:

| Check | Trades | PF | Win rate | Notes |
|---|---:|---:|---:|---|
| validation winner `A @ 7.5%` | 36 | 2.8881 | 66.67% | selected on validation |
| frozen test | 37 | 3.6567 | 72.97% | same validation threshold |
| sequential test | 25 | 2.3419 | 68.00% | fixed 24-bar single-position check |

Signal export:

| File | Rows | Non-zero | BUY | SELL |
|---|---:|---:|---:|---:|
| `entry_path_v1_live_safe_test_signals.csv` | 8872 | 26 | 19 | 7 |

## Comparison With Old System

Old `entry_path_v1` reported:

- validation `A @ 7.5%`: 36 trades, PF 2.67;
- test `A @ 7.5%`: 44 trades, PF 4.29;
- sequential test: 30 trades, PF 2.87, win rate 66.67%.

New live-safe retrain:

- validation `A @ 7.5%`: 36 trades, PF 2.8881;
- test `A @ 7.5%`: 37 trades, PF 3.6567;
- sequential test: 25 trades, PF 2.3419, win rate 68.00%.

## Verdict

The profitability characteristics did not fully survive unchanged: trade count
and PF are lower than the old `entry_path_v1` sequential result.

However, the system did not collapse after removing `ret_dir_atr_lag1`.
On this frozen retrain/check, `entry_path_v1_live_safe` remains profitable:
sequential PF is above 2 with 25 trades.

This is a candidate, not yet production approval. Next checks should cover:

- repeat across several seeds;
- MT4 parity with the exported live-safe signals;
- forward or online dry-run after parity passes.

## Artifacts

- `ML/checkpoints/transformer_entry_path_v1_features_entry_path_v1_live_safe_best.pt`
- `ML/checkpoints/transformer_entry_path_v1_features_entry_path_v1_live_safe_result.json`
- `ML/reports/entry_path_v1_live_safe/entry_path_v1_live_safe_validation_predictions.csv`
- `ML/reports/entry_path_v1_live_safe/entry_path_v1_live_safe_test_predictions.csv`
- `ML/reports/entry_path_v1_live_safe/entry_path_trade_filter_selected_rule.json`
- `ML/reports/entry_path_v1_live_safe/entry_path_trade_filter_report.md`
- `ML/reports/entry_path_v1_live_safe/entry_path_v1_live_safe_test_signals.csv`

## Verification

```bash
./.venv/bin/python -m pytest tests/test_entry_path_task.py tests/test_entry_path_training.py tests/test_entry_path_v1_quantile_reports.py -q
./.venv/bin/python -m pytest tests/test_live_safe_audit.py -q
```

Results:

- `21 passed`
- `13 passed`
