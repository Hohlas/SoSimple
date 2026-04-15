# Entry Path v1 Test Set Evaluation

**Модель**: transformer
**Набор**: Test (9378 строк)

**Checkpoint epoch**: 3
**Best val ret_pearson_r**: 0.2222

## Summary

- row_count: **9378**
- ret_pearson_r: **0.2221**
- path_reg_pearson_r: **0.2488**
- path_cls_f1_macro: **0.3912**

## Return Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.2054 | 0.1403 |
| ret_12_dir_atr | 0.2246 | 0.1647 |
| ret_24_dir_atr | 0.2364 | 0.2796 |

## Path Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| fav_6_atr | 0.2032 | 0.0534 |
| adv_6_atr | 0.3068 | 0.1254 |
| fav_12_atr | 0.1775 | 0.0621 |
| adv_12_atr | 0.3088 | 0.1623 |
| fav_24_atr | 0.1687 | 0.0815 |
| adv_24_atr | 0.3278 | 0.2536 |

## Path Class

| Class | F1 |
|-------|----|
| -1 | 0.2464 |
| 0 | 0.9273 |
| 1 | 0.0000 |

## Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 937 | -0.7284 | 3.8% |
| Top 10% | 937 | 0.0000 | 0.0% |

## Artifacts

- Predictions CSV: `entry_path_test_predictions.csv`

## Active Trades Only

- active_rows: **480**
- active_ret_pearson_r: **0.1739**
- active_path_cls_f1_macro: **0.2902**
- trades_per_year: **96.00**
- PF: **0.1900**
- profit_concentration_top_10: **0.8927**
- negative_year_slices: **5**

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.1629 | 1.3764 |
| ret_12_dir_atr | 0.1700 | 1.8701 |
| ret_24_dir_atr | 0.1888 | 3.1002 |

## Active Path Class

| Class | F1 |
|-------|----|
| -1 | 0.6624 |
| 0 | 0.2083 |
| 1 | 0.0000 |

## Active Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 48 | -3.3712 | 12.5% |
| Top 10% | 48 | 0.5119 | 52.1% |