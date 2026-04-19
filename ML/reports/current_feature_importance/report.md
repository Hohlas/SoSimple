# Current Feature Importance Diagnostics

## Scope

Read-only diagnostic over existing labeled CSV exports. No neural-network training and no `lib_PIC` changes.

## Configuration

- Target: `trail_24_pnl_atr_x8`
- Train rows: `12000`
- Validation rows: `6000`
- Feature count: `261`
- seq_len: `20`
- RandomForest trees: `120`

## Baseline

- Validation R2: `0.058827`
- Validation MAE: `0.281213`
- Directional accuracy: `0.8393`

## Group Importance

| group | feature_count | r2_drop | mae_increase | permuted_r2 | permuted_mae | model_importance_sum |
| --- | --- | --- | --- | --- | --- | --- |
| geometry | 36 | 0.220496 | 0.043171 | -0.161669 | 0.324384 | 0.458713 |
| break_impulse | 24 | 0.007426 | 0.002586 | 0.051401 | 0.283799 | 0.159924 |
| row_context | 9 | 0.003668 | 0.002456 | 0.055159 | 0.283669 | 0.029041 |
| atr | 12 | 0.000543 | 0.001359 | 0.058284 | 0.282572 | 0.027655 |
| direction | 12 | -0.000088 | -0.000005 | 0.058915 | 0.281208 | 0.001811 |
| path_long | 72 | -0.000696 | 0.001068 | 0.059523 | 0.282282 | 0.106403 |
| strength | 36 | -0.000829 | 0.000278 | 0.059656 | 0.281491 | 0.048519 |
| price_position | 12 | -0.002289 | -0.000477 | 0.061116 | 0.280736 | 0.051333 |
| path_short | 48 | -0.005017 | 0.002293 | 0.063844 | 0.283506 | 0.116601 |

## Top Individual Features

| feature | model_importance | group |
| --- | --- | --- |
| front_last_w20 | 0.118385 | geometry |
| front_last_w10 | 0.105309 | geometry |
| front_last_w5 | 0.099828 | geometry |
| break_std_w10 | 0.028756 | break_impulse |
| back_max_w20 | 0.012011 | geometry |
| back_max_w5 | 0.011704 | geometry |
| break_std_w20 | 0.011294 | break_impulse |
| impulse_max_w20 | 0.010591 | break_impulse |
| dn_12_max_w20 | 0.010356 | path_long |
| impulse_last_w20 | 0.010213 | break_impulse |
| impulse_mean_w5 | 0.009687 | break_impulse |
| up_6_mean_w10 | 0.009642 | path_short |
| break_mean_w5 | 0.008922 | break_impulse |
| price_last_w5 | 0.008807 | price_position |
| impulse_mean_w10 | 0.008674 | break_impulse |
| row_vol_regime_24 | 0.008362 | row_context |
| impulse_std_w5 | 0.008315 | break_impulse |
| break_mean_w10 | 0.008171 | break_impulse |
| front_std_w20 | 0.007922 | geometry |
| impulse_last_w10 | 0.007818 | break_impulse |
| front_max_w10 | 0.007765 | geometry |
| row_hour_sin | 0.007752 | row_context |
| front_mean_w20 | 0.007645 | geometry |
| dn_6_std_w20 | 0.007029 | path_short |
| front_max_w20 | 0.006924 | geometry |

## Interpretation Rules

- `r2_drop` shows how much validation R2 falls when the whole group is shuffled.
- `mae_increase` shows how much validation error grows when the whole group is shuffled.
- This is not a trading verdict. It only shows which current input groups are useful for the chosen target.
