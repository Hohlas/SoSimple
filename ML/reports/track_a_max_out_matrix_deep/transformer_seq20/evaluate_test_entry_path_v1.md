# Entry Path v1 Test Set Evaluation

**Модель**: transformer
**Набор**: Test (9378 строк)

**Checkpoint epoch**: 10
**Best val ret_pearson_r**: 0.2921

## Summary

- row_count: **9378**
- ret_pearson_r: **0.2681**
- path_reg_pearson_r: **0.2719**
- path_cls_f1_macro: **0.3902**

## Return Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.2556 | 0.1448 |
| ret_12_dir_atr | 0.2755 | 0.1951 |
| ret_24_dir_atr | 0.2732 | 0.3051 |

## Path Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| fav_6_atr | 0.2044 | 0.0637 |
| adv_6_atr | 0.3581 | 0.1353 |
| fav_12_atr | 0.1759 | 0.0722 |
| adv_12_atr | 0.3639 | 0.1803 |
| fav_24_atr | 0.1571 | 0.0961 |
| adv_24_atr | 0.3719 | 0.2666 |

## Path Class

| Class | F1 |
|-------|----|
| -1 | 0.2615 |
| 0 | 0.9090 |
| 1 | 0.0000 |

## Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 937 | -0.7417 | 2.8% |
| Top 10% | 937 | 0.0127 | 0.3% |

## Artifacts

- Predictions CSV: `entry_path_test_predictions.csv`

## Active Trades Only

- active_rows: **480**
- active_ret_pearson_r: **0.3440**
- active_path_cls_f1_macro: **0.3144**
- trades_per_year: **96.00**
- PF: **0.1900**
- profit_concentration_top_10: **0.8927**
- negative_year_slices: **5**

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.3527 | 1.3184 |
| ret_12_dir_atr | 0.3626 | 1.7419 |
| ret_24_dir_atr | 0.3167 | 2.8921 |

## Active Path Class

| Class | F1 |
|-------|----|
| -1 | 0.7723 |
| 0 | 0.1711 |
| 1 | 0.0000 |

## Active Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 48 | -3.4810 | 6.2% |
| Top 10% | 48 | 2.7345 | 75.0% |