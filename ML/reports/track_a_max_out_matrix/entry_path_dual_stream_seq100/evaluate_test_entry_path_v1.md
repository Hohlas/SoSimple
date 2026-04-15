# Entry Path v1 Test Set Evaluation

**Модель**: entry_path_dual_stream
**Набор**: Test (9378 строк)

**Checkpoint epoch**: 3
**Best val ret_pearson_r**: 0.0754

## Summary

- row_count: **9378**
- ret_pearson_r: **0.0568**
- path_reg_pearson_r: **0.0887**
- path_cls_f1_macro: **0.3259**

## Return Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.0512 | 0.1503 |
| ret_12_dir_atr | 0.0518 | 0.1840 |
| ret_24_dir_atr | 0.0673 | 0.3230 |

## Path Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| fav_6_atr | 0.0859 | 0.0687 |
| adv_6_atr | 0.0923 | 0.1402 |
| fav_12_atr | 0.0761 | 0.0781 |
| adv_12_atr | 0.0874 | 0.1885 |
| fav_24_atr | 0.0814 | 0.0992 |
| adv_24_atr | 0.1090 | 0.2747 |

## Path Class

| Class | F1 |
|-------|----|
| -1 | 0.0000 |
| 0 | 0.9777 |
| 1 | 0.0000 |

## Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 937 | -0.3055 | 2.8% |
| Top 10% | 937 | -0.0059 | 0.1% |

## Artifacts

- Predictions CSV: `entry_path_test_predictions.csv`

## Active Trades Only

- active_rows: **480**
- active_ret_pearson_r: **-0.0367**
- active_path_cls_f1_macro: **0.0848**
- trades_per_year: **96.00**
- PF: **0.1900**
- profit_concentration_top_10: **0.8927**
- negative_year_slices: **5**

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | -0.0391 | 1.4611 |
| ret_12_dir_atr | -0.0855 | 2.0215 |
| ret_24_dir_atr | 0.0145 | 3.3232 |

## Active Path Class

| Class | F1 |
|-------|----|
| -1 | 0.0000 |
| 0 | 0.2545 |
| 1 | 0.0000 |

## Active Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 48 | -2.4260 | 20.8% |
| Top 10% | 48 | -1.8614 | 20.8% |