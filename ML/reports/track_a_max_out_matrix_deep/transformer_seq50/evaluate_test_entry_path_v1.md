# Entry Path v1 Test Set Evaluation

**Модель**: transformer
**Набор**: Test (9378 строк)

**Checkpoint epoch**: 10
**Best val ret_pearson_r**: 0.2904

## Summary

- row_count: **9378**
- ret_pearson_r: **0.2732**
- path_reg_pearson_r: **0.2701**
- path_cls_f1_macro: **0.3904**

## Return Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.2617 | 0.1461 |
| ret_12_dir_atr | 0.2802 | 0.1927 |
| ret_24_dir_atr | 0.2776 | 0.3007 |

## Path Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| fav_6_atr | 0.2013 | 0.0629 |
| adv_6_atr | 0.3592 | 0.1341 |
| fav_12_atr | 0.1731 | 0.0715 |
| adv_12_atr | 0.3643 | 0.1795 |
| fav_24_atr | 0.1528 | 0.0954 |
| adv_24_atr | 0.3702 | 0.2652 |

## Path Class

| Class | F1 |
|-------|----|
| -1 | 0.2641 |
| 0 | 0.9071 |
| 1 | 0.0000 |

## Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 937 | -0.7628 | 2.8% |
| Top 10% | 937 | 0.0426 | 0.9% |

## Artifacts

- Predictions CSV: `entry_path_test_predictions.csv`

## Active Trades Only

- active_rows: **480**
- active_ret_pearson_r: **0.3648**
- active_path_cls_f1_macro: **0.3266**
- trades_per_year: **96.00**
- PF: **0.1900**
- profit_concentration_top_10: **0.8927**
- negative_year_slices: **5**

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.3782 | 1.3008 |
| ret_12_dir_atr | 0.3794 | 1.7281 |
| ret_24_dir_atr | 0.3369 | 2.8797 |

## Active Path Class

| Class | F1 |
|-------|----|
| -1 | 0.7893 |
| 0 | 0.1905 |
| 1 | 0.0000 |

## Active Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 48 | -3.3829 | 12.5% |
| Top 10% | 48 | 2.6886 | 77.1% |