# Entry Path v1 Test Set Evaluation

**Модель**: entry_path_dual_stream
**Набор**: Test (9378 строк)

**Checkpoint epoch**: 3
**Best val ret_pearson_r**: 0.2248

## Summary

- row_count: **9378**
- ret_pearson_r: **0.2096**
- path_reg_pearson_r: **0.2464**
- path_cls_f1_macro: **0.3188**

## Return Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.1948 | 0.1547 |
| ret_12_dir_atr | 0.2112 | 0.1873 |
| ret_24_dir_atr | 0.2228 | 0.3240 |

## Path Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| fav_6_atr | 0.2084 | 0.0694 |
| adv_6_atr | 0.3035 | 0.1404 |
| fav_12_atr | 0.1781 | 0.0777 |
| adv_12_atr | 0.3025 | 0.1880 |
| fav_24_atr | 0.1679 | 0.1017 |
| adv_24_atr | 0.3178 | 0.2760 |

## Path Class

| Class | F1 |
|-------|----|
| -1 | 0.1593 |
| 0 | 0.7970 |
| 1 | 0.0000 |

## Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 937 | -0.7309 | 3.8% |
| Top 10% | 937 | 0.0016 | 0.1% |

## Artifacts

- Predictions CSV: `entry_path_test_predictions.csv`

## Active Trades Only

- active_rows: **480**
- active_ret_pearson_r: **0.2045**
- active_path_cls_f1_macro: **0.2916**
- trades_per_year: **96.00**
- PF: **0.1900**
- profit_concentration_top_10: **0.8927**
- negative_year_slices: **5**

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.2083 | 1.3788 |
| ret_12_dir_atr | 0.1689 | 1.8817 |
| ret_24_dir_atr | 0.2364 | 3.1362 |

## Active Path Class

| Class | F1 |
|-------|----|
| -1 | 0.7887 |
| 0 | 0.0862 |
| 1 | 0.0000 |

## Active Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 48 | -2.0581 | 22.9% |
| Top 10% | 48 | 0.1889 | 52.1% |