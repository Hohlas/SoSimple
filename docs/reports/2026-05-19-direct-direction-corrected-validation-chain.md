# Direct Direction Corrected Validation Chain

> **Date**: 2026-05-19
> **Status**: Completed
> **Goal**: Исправить protocol gates и feature/target provenance direct-direction chain, затем проверить minimal validation-only baseline без подбора по test split.
> **Related plan/spec**: `docs/audit/2026-05-19-direct-direction-chain-audit.md`
> **Related commit**: pending

## Context

Аудит `docs/audit/2026-05-19-direct-direction-chain-audit.md` подтвердил методологические дефекты direct-direction ветки: winner selection не был механически воспроизводимым, top-level target columns могли влиять на нормализованные fractal Up/Dn features, distance/ATR считался в смешанных единицах, а A/C targets назывались `_atr`, хотя использовали normalized split `up/dn`.

Test split объявлен закрытым до финального frozen test. В этом этапе test split и test artifacts не использовались для выбора гипотез, порогов, признаков или моделей.

## What Was Done

- Зафиксирован `selection_policy()` для binary direct-direction benchmark: primary metric `validation_sequential_pf`, отдельные gates для `one_sided_candidate`, `negative_years`, `overfitting_risk`, min trades и PF.
- `run_validation_matrix()` теперь пишет `selection_decision.json` и `feature_manifest.json`.
- `normalize_rowwise()` получил default-safe `include_targets_in_updn_pool=False`, чтобы top-level `up_*/dn_*` не задавали scaling фрактальных Up/Dn features.
- `fractal_level_feature_builder.py` получил `raw_price_frame`; distance/zone features могут считаться как raw price / raw ATR.
- `entry_path_direct_direction_targets.py` перевёл A/C `_atr` moves на raw `up/dn / ATR` contract и по умолчанию запрещает A/C frequency gate для normalized split source.
- Запущен minimal validation-only baseline: nearest-k4, Target D, RF/HGB, side-specific metrics, sequential PF, yearly stability.
- Frozen test не запускался, потому что validation winner отсутствует.

## Changed Files

- `ML/benchmark_entry_path_binary_direction.py`
- `ML/fractal_level_feature_builder.py`
- `ML/entry_path_direct_direction_targets.py`
- `processing/normalize.py`
- `tests/test_benchmark_entry_path_binary_direction.py`
- `tests/test_fractal_level_feature_builder.py`
- `tests/test_entry_path_direct_direction_targets.py`
- `tests/test_inverse_piecewise.py`
- `docs/ML/benchmark_entry_path_binary_direction.py.md`
- `docs/ML/fractal_level_feature_builder.py.md`
- `docs/ML/entry_path_direct_direction_targets.py.md`
- `docs/processing/normalize.py.md`
- `ML/reports/direct_direction_corrected_validation_baseline/`

## Verification

```bash
./.venv/bin/python -m pytest tests/test_benchmark_entry_path_binary_direction.py tests/test_inverse_piecewise.py::test_normalize_rowwise_can_exclude_top_level_targets_from_updn_pool tests/test_fractal_level_feature_builder.py tests/test_entry_path_direct_direction_targets.py -q
# 32 passed

./.venv/bin/python -m ML.benchmark_entry_path_binary_direction --stage target-frequency --output-dir ML/reports/direct_direction_corrected_validation_baseline --train-source DATA/Nero_XAUUSD_train_labeled.csv --validation-source DATA/Nero_XAUUSD_validation_labeled.csv --ohlc DATA/XAUUSD_H1_OHLC.csv
# Target D gate_pass=true, test_set_used=false

./.venv/bin/python -m ML.benchmark_entry_path_binary_direction --stage validation-matrix --output-dir ML/reports/direct_direction_corrected_validation_baseline --train-source DATA/Nero_XAUUSD_train_labeled.csv --validation-source DATA/Nero_XAUUSD_validation_labeled.csv --validation-predictions ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/validation_predictions.csv --ohlc DATA/XAUUSD_H1_OHLC.csv --raw-feature-source MT/MQL4/Files/Nero.csv --k 4
# winner_found=false, test_set_used=false
```

## Results

Selection decision: `no validation winner`. Automatic winner found: `False`.

Top validation rows by sequential PF:

| config | validation_trades | validation_pf | validation_sequential_pf | buy_trades | sell_trades | buy_pf | sell_pf | one_sided_candidate | negative_years | overfitting_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D_rf_buy0.30_sell0.50_m0.00_standalone | 73 | 2.8736 | 2.4203 | 73 | 0 | 2.8736 | 0.0000 | True | 0 | True |
| D_rf_buy0.40_sell0.50_m0.00_standalone | 74 | 2.2561 | 2.4203 | 73 | 1 | 2.8736 | 0.0000 | True | 0 | True |
| D_hgb_buy0.50_sell0.60_m0.10_standalone | 360 | 1.3625 | 1.4527 | 302 | 58 | 1.3928 | 1.2057 | True | 1 | True |
| D_rf_buy0.50_sell0.60_m0.00_standalone | 3535 | 1.1697 | 1.3445 | 3392 | 143 | 1.1919 | 0.7635 | True | 1 | False |
| D_rf_buy0.30_sell0.60_m0.00_standalone | 3557 | 1.1649 | 1.3226 | 3557 | 0 | 1.1649 | 0.0000 | True | 1 | False |

Side policy:

| Policy | Gate pass | Note |
|---|---:|---|
| BUY-only | `False` | 73-trade RF BUY-only slice has PF/SeqPF > 2 but fails the 100-trade protocol support floor. |
| SELL diagnostic | `False` | Some rows have SELL side PF > 1.0, but they are one-sided/unstable or overfitting-risk rows; confidence monotonicity was not established. |
| Combined | `False` | No combined candidate passed selection policy; combined is therefore rejected. |

## Conclusions

Corrected validation-only chain did **not** produce a protocol-valid winner. The best high-PF slices are one-sided, below the support floor, unstable by year, or marked as overfitting risk. SELL is not enabled: side-specific validation gate and confidence monotonicity were not established.

The previous weak uplift should be treated as not production-actionable under the corrected contract. The direct-direction line should not proceed to frozen test from this baseline.

Decision: close the current two-sided direct-direction candidate and do not run frozen test. BUY-only remains only a future hypothesis if it can pass validation with enough support; current corrected baseline does not justify it.

## Limitations / Open Questions

- Raw price source was reconstructed from `MT/MQL4/Files/Nero.csv` first train+validation rows and row-wise sorting, not from separately materialized raw split artifacts.
- Confidence monotonicity for SELL was not established because no SELL candidate passed prerequisite gates.
- A/C corrected raw target grid was not run because Gates 1-4 did not produce a valid baseline winner.

## Next Step

Stop direct-direction frozen-test work for now. If this line is reopened, first create materialized raw train/validation feature-source artifacts with explicit provenance and then test BUY-only as a separate validation-only research line with a support floor and rolling/yearly stability.

## Related Materials

- `docs/audit/2026-05-19-direct-direction-chain-audit.md`
- `docs/reports/2026-05-15-direct-direction-improvement.md`
- `ML/reports/direct_direction_corrected_validation_baseline/summary.md`
- `ML/reports/direct_direction_corrected_validation_baseline/selection_decision.json`
- `ML/reports/direct_direction_corrected_validation_baseline/feature_manifest.json`
- `ML/reports/direct_direction_corrected_validation_baseline/side_policy_summary.json`
