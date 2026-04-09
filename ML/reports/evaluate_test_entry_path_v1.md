# Entry Path v1 Test Set Evaluation

**Модель**: transformer
**Набор**: Test (9378 строк)

**Checkpoint epoch**: 5
**Best val ret_pearson_r**: 0.2736

## Summary

- row_count: **9378**
- ret_pearson_r: **0.2494**
- path_reg_pearson_r: **0.2722**
- path_cls_f1_macro: **0.4160**

## Return Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.2366 | 0.1570 |
| ret_12_dir_atr | 0.2539 | 0.2010 |
| ret_24_dir_atr | 0.2577 | 0.3045 |

## Path Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| fav_6_atr | 0.2168 | 0.0590 |
| adv_6_atr | 0.3452 | 0.1343 |
| fav_12_atr | 0.1882 | 0.0695 |
| adv_12_atr | 0.3488 | 0.1787 |
| fav_24_atr | 0.1747 | 0.0892 |
| adv_24_atr | 0.3596 | 0.2649 |

## Path Class

| Class | F1 |
|-------|----|
| -1 | 0.2945 |
| 0 | 0.9534 |
| 1 | 0.0000 |

## Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 937 | -0.7733 | 3.8% |
| Top 10% | 937 | 0.0000 | 0.0% |

## Artifacts

- Predictions CSV: `entry_path_test_predictions.csv`

## Active Trades Only

- active_rows: **480**
- active_ret_pearson_r: **0.2285**

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.2337 | 1.3135 |
| ret_12_dir_atr | 0.2283 | 1.7533 |
| ret_24_dir_atr | 0.2235 | 2.8998 |

## Active Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 48 | -2.7441 | 16.7% |
| Top 10% | 48 | 0.4343 | 58.3% |