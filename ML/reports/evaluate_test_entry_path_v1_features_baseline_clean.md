# Entry Path v1 Test Set Evaluation

**Модель**: transformer
**Набор**: Test (9378 строк)

**Checkpoint epoch**: 10
**Best val ret_pearson_r**: 0.2920

## Summary

- row_count: **9378**
- ret_pearson_r: **0.2269**
- path_reg_pearson_r: **0.2379**
- path_cls_f1_macro: **0.3838**

## Return Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.2202 | 0.1195 |
| ret_12_dir_atr | 0.2345 | 0.1597 |
| ret_24_dir_atr | 0.2260 | 0.2490 |

## Path Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| fav_6_atr | 0.1747 | 0.0571 |
| adv_6_atr | 0.3151 | 0.1255 |
| fav_12_atr | 0.1525 | 0.0647 |
| adv_12_atr | 0.3161 | 0.1694 |
| fav_24_atr | 0.1493 | 0.0871 |
| adv_24_atr | 0.3199 | 0.2536 |

## Path Class

| Class | F1 |
|-------|----|
| -1 | 0.2462 |
| 0 | 0.9052 |
| 1 | 0.0000 |

## Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 937 | -0.7038 | 3.1% |
| Top 10% | 937 | 0.0159 | 0.4% |

## Artifacts

- Predictions CSV: `entry_path_features_baseline_clean_test_predictions.csv`

## Active Trades Only

- active_rows: **480**
- active_ret_pearson_r: **0.2033**
- active_path_cls_f1_macro: **0.3153**
- trades_per_year: **96.00**
- PF: **0.1900**
- profit_concentration_top_10: **0.8927**
- negative_year_slices: **5**

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.2207 | 1.3726 |
| ret_12_dir_atr | 0.2191 | 1.8476 |
| ret_24_dir_atr | 0.1702 | 3.0676 |

## Active Path Class

| Class | F1 |
|-------|----|
| -1 | 0.7565 |
| 0 | 0.1893 |
| 1 | 0.0000 |

## Active Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 48 | -3.8343 | 4.2% |
| Top 10% | 48 | 1.4226 | 64.6% |