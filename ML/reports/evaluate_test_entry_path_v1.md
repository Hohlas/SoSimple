# Entry Path v1 Test Set Evaluation

**Модель**: transformer
**Набор**: Test (9378 строк)

**Checkpoint epoch**: 5
**Best val ret_pearson_r**: 0.2758

## Summary

- row_count: **9378**
- ret_pearson_r: **0.2507**
- path_reg_pearson_r: **0.2667**
- path_cls_f1_macro: **0.4013**

## Return Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.2385 | 0.1361 |
| ret_12_dir_atr | 0.2564 | 0.1746 |
| ret_24_dir_atr | 0.2572 | 0.2741 |

## Path Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| fav_6_atr | 0.2100 | 0.0577 |
| adv_6_atr | 0.3419 | 0.1275 |
| fav_12_atr | 0.1822 | 0.0660 |
| adv_12_atr | 0.3450 | 0.1713 |
| fav_24_atr | 0.1677 | 0.0879 |
| adv_24_atr | 0.3537 | 0.2561 |

## Path Class

| Class | F1 |
|-------|----|
| -1 | 0.2755 |
| 0 | 0.9283 |
| 1 | 0.0000 |

## Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 937 | -0.8063 | 3.5% |
| Top 10% | 937 | 0.0000 | 0.0% |

## Artifacts

- Predictions CSV: `entry_path_test_predictions.csv`

## Active Trades Only

- active_rows: **480**
- active_ret_pearson_r: **0.2241**
- active_path_cls_f1_macro: **0.3208**

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.2309 | 1.3421 |
| ret_12_dir_atr | 0.2318 | 1.8045 |
| ret_24_dir_atr | 0.2096 | 2.9687 |

## Active Path Class

| Class | F1 |
|-------|----|
| -1 | 0.7231 |
| 0 | 0.2392 |
| 1 | 0.0000 |

## Active Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 48 | -2.6210 | 14.6% |
| Top 10% | 48 | 2.2129 | 70.8% |