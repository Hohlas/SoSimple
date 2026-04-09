# Entry Path v1 Test Set Evaluation

**Модель**: transformer
**Набор**: Validation (9378 строк)

**Checkpoint epoch**: 5
**Best val ret_pearson_r**: 0.2758

## Summary

- row_count: **9378**
- ret_pearson_r: **0.2758**
- path_reg_pearson_r: **0.2987**
- path_cls_f1_macro: **0.4074**

## Return Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.2644 | 0.1280 |
| ret_12_dir_atr | 0.2781 | 0.1601 |
| ret_24_dir_atr | 0.2848 | 0.2399 |

## Path Targets

| Target | Pearson r | MAE |
|--------|-----------|-----|
| fav_6_atr | 0.2620 | 0.0511 |
| adv_6_atr | 0.3444 | 0.1279 |
| fav_12_atr | 0.2329 | 0.0599 |
| adv_12_atr | 0.3537 | 0.1637 |
| fav_24_atr | 0.2355 | 0.0753 |
| adv_24_atr | 0.3636 | 0.2418 |

## Path Class

| Class | F1 |
|-------|----|
| -1 | 0.2846 |
| 0 | 0.9375 |
| 1 | 0.0000 |

## Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 937 | -0.7766 | 4.2% |
| Top 10% | 937 | 0.0026 | 0.1% |

## Artifacts

- Predictions CSV: `entry_path_v1_validation_predictions.csv`

## Active Trades Only

- active_rows: **473**
- active_ret_pearson_r: **0.2089**
- active_path_cls_f1_macro: **0.3125**

| Target | Pearson r | MAE |
|--------|-----------|-----|
| ret_6_dir_atr | 0.2189 | 1.3418 |
| ret_12_dir_atr | 0.2402 | 1.7248 |
| ret_24_dir_atr | 0.1677 | 2.6198 |

## Active Path Class

| Class | F1 |
|-------|----|
| -1 | 0.6909 |
| 0 | 0.2466 |
| 1 | 0.0000 |

## Active Slice: pred_ret_24_dir_atr

| Slice | Rows | mean true_ret_24_dir_atr | positive share |
|-------|------|--------------------------|----------------|
| Bottom 10% | 47 | -3.6454 | 12.8% |
| Top 10% | 47 | 0.4876 | 53.2% |