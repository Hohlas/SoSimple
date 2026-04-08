# Triple Barrier Test Set Evaluation

**Модель**: transformer
**Набор**: Test (9378 строк)
**Mean AUC**: 0.5895
**Калибратор**: `tb_probability_calibrator.joblib`

## Frozen Signal Rule

- θ: **0.475**
- min_ev: **0.10**
- Trades: 253
- Wins / Losses / Timeouts: 128 / 125 / 24
- Win Rate: 50.6%
- Profit Factor: **1.11**
- Dominant target: `buy_sl3_tp3` (220 trades)

## Per-target AUC
| Target | AUC | Precision | Recall | Pos Rate |
|--------|-----|-----------|--------|----------|
| buy_sl2_tp3 | 0.5147 | 0.5333 | 0.0024 | 35.7% |
| buy_sl2_tp6 | 0.5551 | 0.0000 | 0.0000 | 11.6% |
| buy_sl2_tp9 | 0.5631 | 0.0000 | 0.0000 | 3.1% |
| buy_sl3_tp3 | 0.5255 | 0.5238 | 0.0423 | 38.8% |
| buy_sl3_tp6 | 0.5595 | 0.0000 | 0.0000 | 12.4% |
| buy_sl3_tp9 | 0.5643 | 0.0000 | 0.0000 | 3.3% |
| sell_sl2_tp3 | 0.5361 | 0.1429 | 0.0004 | 27.1% |
| sell_sl2_tp6 | 0.6137 | 0.4000 | 0.0030 | 7.0% |
| sell_sl2_tp9 | 0.7406 | 0.2000 | 0.0088 | 2.4% |
| sell_sl3_tp3 | 0.5428 | 0.7500 | 0.0011 | 30.3% |
| sell_sl3_tp6 | 0.6210 | 0.3077 | 0.0056 | 7.6% |
| sell_sl3_tp9 | 0.7379 | 0.3333 | 0.0040 | 2.7% |

## Rule Source

Loaded from `tb_selected_rule.json`