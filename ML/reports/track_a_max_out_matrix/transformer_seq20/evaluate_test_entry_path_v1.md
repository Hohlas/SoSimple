# Entry Path v1 Test Set Evaluation

**Модель**: transformer
**Набор**: Test (9378 строк)

**Checkpoint epoch**: 3
**Best val ret_pearson_r**: 0.2452

## Summary

- row_count: **9378**
- ret_pearson_r: **0.2372**
- path_reg_pearson_r: **0.2635**
- path_cls_f1_macro: **0.3771**

## Return Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.2209 | 0.1357 |
| ret_12_dir_atr | 0.2386 | 0.1752 |
| ret_24_dir_atr | 0.2521 | 0.2731 |

## Path Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| fav_6_atr | 0.2153 | 0.0570 |
| adv_6_atr | 0.3272 | 0.1309 |
| fav_12_atr | 0.1883 | 0.0652 |
| adv_12_atr | 0.3265 | 0.1701 |
| fav_24_atr | 0.1761 | 0.0862 |
| adv_24_atr | 0.3474 | 0.2598 |

## Path Class

| Class | F1 |
|-------|----|
| -1 | 0.2308 |
| 0 | 0.9004 |
| 1 | 0.0000 |

## Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 937 | -0.7793 | 3.9% |
| Top 10% | 937 | 0.0000 | 0.0% |

## Artifacts

- Predictions CSV: `entry_path_test_predictions.csv`

## Active Trades Only

- active_rows: **480**
- active_ret_pearson_r: **0.1921**
- active_path_cls_f1_macro: **0.3094**
- trades_per_year: **96.00**
- PF: **0.1900**
- profit_concentration_top_10: **0.8927**
- negative_year_slices: **5**

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.1806 | 1.3633 |
| ret_12_dir_atr | 0.1851 | 1.8155 |
| ret_24_dir_atr | 0.2107 | 3.0376 |

## Active Path Class

| Class | F1 |
|-------|----|
| -1 | 0.7393 |
| 0 | 0.1889 |
| 1 | 0.0000 |

## Active Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 48 | -3.1444 | 12.5% |
| Top 10% | 48 | 0.6359 | 56.2% |