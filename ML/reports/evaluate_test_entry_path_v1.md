# Entry Path v1 Test Set Evaluation

**Модель**: transformer
**Набор**: Test (9378 строк)

## Summary

- row_count: **9378**
- ret_pearson_r: **-0.0216**
- path_reg_pearson_r: **0.1694**
- path_cls_f1_macro: **0.3259**

## Return Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | -0.0296 | 0.1719 |
| ret_12_dir_atr | -0.0264 | 0.1795 |
| ret_24_dir_atr | -0.0086 | 0.2248 |

## Path Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| fav_6_atr | 0.1362 | 0.2222 |
| adv_6_atr | 0.2600 | 0.1461 |
| fav_12_atr | 0.0715 | 0.3226 |
| adv_12_atr | 0.2660 | 0.2068 |
| fav_24_atr | 0.1051 | 0.4339 |
| adv_24_atr | 0.1779 | 0.3204 |

## Path Class

| Class | F1 |
|-------|----|
| -1 | 0.0000 |
| 0 | 0.9777 |
| 1 | 0.0000 |

## Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 937 | -0.4176 | 2.6% |
| Top 10% | 937 | -0.1612 | 0.2% |

## Artifacts

- Predictions CSV: `entry_path_test_predictions.csv`