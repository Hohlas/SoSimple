# Entry Path v1 All-Rows Ranking

## Context

Цель: проверить `pred_ret_24_dir_atr` на всех строках, без offline `signal != 0` gate.
Направление берётся из `fractal0.direction` по существующей diagnostic-конвенции.

## Inputs

- validation_predictions: `ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/validation_predictions.csv`
- test_predictions: `ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/test_predictions.csv`
- ohlc: `DATA/XAUUSD_H1_OHLC.csv`
- horizon: `24`

## Validation Winner

- target_coverage: `0.05`
- score_threshold: `-0.00183110685`
- trades: `471`
- pf: `0.9661`

## Frozen Test

- trades: `329`
- pf: `0.9134`
- win_rate: `46.20%`
- mean_pnl_atr: `-0.1275`

## Sequential Test

- trades: `133`
- pf: `0.5908`
- win_rate: `40.60%`
- mean_pnl_atr: `-0.6768`

## Limitation

Это не production approval. Модель обучалась на другой постановке, поэтому положительный результат требует отдельного retrain или forward-проверки.