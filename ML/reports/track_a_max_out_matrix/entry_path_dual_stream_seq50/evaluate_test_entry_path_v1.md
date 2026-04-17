# Entry Path v1 Test Set Evaluation

**Модель**: entry_path_dual_stream
**Набор**: Test (9378 строк)

**Checkpoint epoch**: 3
**Best val ret_pearson_r**: 0.0758

## Summary

- row_count: **9378**
- ret_pearson_r: **0.0580**
- path_reg_pearson_r: **0.0784**
- path_cls_f1_macro: **0.3259**

## Return Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.0496 | 0.1784 |
| ret_12_dir_atr | 0.0546 | 0.2178 |
| ret_24_dir_atr | 0.0698 | 0.3538 |

## Path Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| fav_6_atr | 0.0932 | 0.0731 |
| adv_6_atr | 0.0139 | 0.1463 |
| fav_12_atr | 0.0801 | 0.0862 |
| adv_12_atr | 0.0939 | 0.1930 |
| fav_24_atr | 0.0760 | 0.1066 |
| adv_24_atr | 0.1132 | 0.2851 |

## Path Class

| Class | F1 |
|-------|----|
| -1 | 0.0000 |
| 0 | 0.9777 |
| 1 | 0.0000 |

## Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 937 | -0.3075 | 2.5% |
| Top 10% | 937 | -0.0047 | 0.1% |

## Artifacts

- Predictions CSV: `entry_path_test_predictions.csv`

## Active Trades Only

- active_rows: **480**
- active_ret_pearson_r: **-0.0525**
- active_path_cls_f1_macro: **0.0848**
- trades_per_year: **96.00**
- PF: **0.1900**
- profit_concentration_top_10: **0.8927**
- negative_year_slices: **5**

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | -0.0820 | 1.4514 |
| ret_12_dir_atr | -0.0780 | 2.0012 |
| ret_24_dir_atr | 0.0026 | 3.3026 |

## Active Path Class

| Class | F1 |
|-------|----|
| -1 | 0.0000 |
| 0 | 0.2545 |
| 1 | 0.0000 |

## Active Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 48 | -2.2820 | 25.0% |
| Top 10% | 48 | -1.8951 | 18.8% |