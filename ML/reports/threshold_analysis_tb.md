# Triple Barrier Threshold Analysis

**Дата**: 2026-04-08 17:29
**Модель**: transformer
**Калибратор**: `tb_probability_calibrator.joblib` (validation-only isotonic)

## Frozen Signal Rule

- Selection: support-gated: trades >= 80 & win_rate >= 35%
- θ: **0.475**
- min_ev: **0.10**
- Trades: 121
- Wins / Losses / Timeouts: 70 / 51 / 14
- Win Rate: 57.9%
- Profit Factor: **1.53**
- Dominant target: `buy_sl3_tp3` (105 trades)

## Support-Gated Best θ per Target

| Target | θ | Trades | Wins | Timeouts | Win Rate | PF |
|--------|---|--------|------|----------|----------|------|
| buy_sl2_tp3 | 0.380 | 81 | 40 | 6 | 49.4% | 1.46 |
| buy_sl3_tp3 | 0.512 | 107 | 62 | 14 | 57.9% | 1.38 |
| sell_sl2_tp3 | 0.380 | 411 | 168 | 35 | 40.9% | 1.04 |
| sell_sl3_tp3 | 0.406 | 826 | 341 | 149 | 41.3% | 0.70 |

## Signal Rule Grid

Saved to: `ML/reports/threshold_tb_signal_rules.csv`

## Full Per-Target Table

Saved to: `ML/reports/threshold_tb_full.csv`