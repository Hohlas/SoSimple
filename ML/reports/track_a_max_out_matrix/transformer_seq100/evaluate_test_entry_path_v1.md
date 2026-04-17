# Entry Path v1 Test Set Evaluation

**Модель**: transformer
**Набор**: Test (9378 строк)

**Checkpoint epoch**: 3
**Best val ret_pearson_r**: 0.1526

## Summary

- row_count: **9378**
- ret_pearson_r: **0.1458**
- path_reg_pearson_r: **0.1944**
- path_cls_f1_macro: **0.3562**

## Return Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.1286 | 0.1723 |
| ret_12_dir_atr | 0.1436 | 0.1950 |
| ret_24_dir_atr | 0.1651 | 0.3045 |

## Path Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| fav_6_atr | 0.1775 | 0.0609 |
| adv_6_atr | 0.2137 | 0.1341 |
| fav_12_atr | 0.1568 | 0.0696 |
| adv_12_atr | 0.2162 | 0.1740 |
| fav_24_atr | 0.1527 | 0.0897 |
| adv_24_atr | 0.2498 | 0.2657 |

## Path Class

| Class | F1 |
|-------|----|
| -1 | 0.1697 |
| 0 | 0.8989 |
| 1 | 0.0000 |

## Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 937 | -0.6158 | 3.2% |
| Top 10% | 937 | 0.0000 | 0.0% |

## Artifacts

- Predictions CSV: `entry_path_test_predictions.csv`

## Active Trades Only

- active_rows: **480**
- active_ret_pearson_r: **0.0495**
- active_path_cls_f1_macro: **0.2506**
- trades_per_year: **96.00**
- PF: **0.1900**
- profit_concentration_top_10: **0.8927**
- negative_year_slices: **5**

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.0240 | 1.4034 |
| ret_12_dir_atr | 0.0195 | 1.9117 |
| ret_24_dir_atr | 0.1050 | 3.1978 |

## Active Path Class

| Class | F1 |
|-------|----|
| -1 | 0.5859 |
| 0 | 0.1660 |
| 1 | 0.0000 |

## Active Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 48 | -2.6947 | 18.8% |
| Top 10% | 48 | -0.8116 | 31.2% |