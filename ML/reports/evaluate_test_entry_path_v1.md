# Entry Path v1 Test Set Evaluation

**Модель**: transformer
**Набор**: Test (9378 строк)

## Summary

- row_count: **9378**
- ret_pearson_r: **0.2450**
- path_reg_pearson_r: **0.2745**
- path_cls_f1_macro: **0.3259**

## Return Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.2317 | 0.0991 |
| ret_12_dir_atr | 0.2486 | 0.1327 |
| ret_24_dir_atr | 0.2546 | 0.2027 |

## Path Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| fav_6_atr | 0.2219 | 0.0574 |
| adv_6_atr | 0.3434 | 0.1306 |
| fav_12_atr | 0.1955 | 0.0690 |
| adv_12_atr | 0.3446 | 0.1749 |
| fav_24_atr | 0.1811 | 0.0877 |
| adv_24_atr | 0.3605 | 0.2569 |

## Path Class

| Class | F1 |
|-------|----|
| -1 | 0.0000 |
| 0 | 0.9777 |
| 1 | 0.0000 |

## Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 937 | -0.7774 | 4.1% |
| Top 10% | 937 | 0.0041 | 0.3% |

## Artifacts

- Predictions CSV: `entry_path_test_predictions.csv`

## Active Trades Only

- active_rows: **480**
- active_ret_pearson_r: **0.2039**

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.2075 | 1.4417 |
| ret_12_dir_atr | 0.2025 | 1.9800 |
| ret_24_dir_atr | 0.2016 | 3.3222 |

## Active Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 48 | -2.2741 | 20.8% |
| Top 10% | 48 | 0.2442 | 56.2% |