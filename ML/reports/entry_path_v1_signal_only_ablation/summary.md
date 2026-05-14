# Entry Path v1 Signal-Only Ablation

## Context

Цель: оценить вклад offline `signal != 0` без ML score-фильтра.

## Inputs

- predictions: `ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/test_predictions.csv`
- score_threshold: `-0.07158749`
- sequential_hold_bars: `24`

## Summary

| Mode | Selected trades | Selected PF | Selected win rate | Sequential trades | Sequential PF | Sequential win rate |
|---|---:|---:|---:|---:|---:|---:|
| signal_only | 486 | 0.1757 | 16.87% | 237 | 0.1696 | 16.46% |
| current_score_gate | 41 | 7.5737 | 73.17% | 27 | 5.9352 | 70.37% |

## Delta: current_score_gate - signal_only

- selected_trade_delta: `-445`
- selected_pf_delta: `7.3980`
- selected_mean_pnl_atr_delta: `4.2894`
- sequential_trade_delta: `-210`
- sequential_pf_delta: `5.7655`
- sequential_mean_pnl_atr_delta: `4.2769`

## Interpretation

Если `signal_only` уже силён, edge в основном приходит из offline candidate universe. Если `current_score_gate` заметно лучше, модель вносит дополнительный фильтрующий вклад, но всё ещё поверх недоступного live `signal`.