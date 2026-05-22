# Direct Direction Corrected Validation Baseline

> Date: 2026-05-19
> Scope: validation-only; frozen test not used.

## Protocol

- Feature distance source: `MT/MQL4/Files/Nero.csv` raw prices, sorted row-wise, first train+validation rows only.
- Model source: `DATA/Nero_XAUUSD_train_labeled.csv` + `DATA/Nero_XAUUSD_validation_labeled.csv`.
- Target: D, OHLC-derived trailing profit (`trail_n=2.0`, `profit_z=1.0`, `horizon=24`).
- Models: RF and HGB; threshold/margin grid unchanged from previous baseline.
- Selection primary metric: `validation_sequential_pf`; test split/artifacts not used.

## Selection Result

- Automatic winner found: `False`
- Decision reason: `no validation winner`

## Top Validation Rows By Sequential PF

| config | model_type | validation_trades | validation_pf | validation_sequential_pf | buy_trades | sell_trades | buy_pf | sell_pf | one_sided_candidate | negative_years | overfitting_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D_rf_buy0.30_sell0.50_m0.00_standalone | rf | 73 | 2.8736 | 2.4203 | 73 | 0 | 2.8736 | 0.0000 | True | 0 | True |
| D_rf_buy0.40_sell0.50_m0.00_standalone | rf | 74 | 2.2561 | 2.4203 | 73 | 1 | 2.8736 | 0.0000 | True | 0 | True |
| D_hgb_buy0.50_sell0.60_m0.10_standalone | hgb | 360 | 1.3625 | 1.4527 | 302 | 58 | 1.3928 | 1.2057 | True | 1 | True |
| D_rf_buy0.50_sell0.60_m0.00_standalone | rf | 3535 | 1.1697 | 1.3445 | 3392 | 143 | 1.1919 | 0.7635 | True | 1 | False |
| D_rf_buy0.30_sell0.60_m0.00_standalone | rf | 3557 | 1.1649 | 1.3226 | 3557 | 0 | 1.1649 | 0.0000 | True | 1 | False |
| D_rf_buy0.40_sell0.60_m0.00_standalone | rf | 3558 | 1.1606 | 1.3226 | 3557 | 1 | 1.1649 | 0.0000 | True | 1 | False |
| D_hgb_buy0.30_sell0.60_m0.10_standalone | hgb | 376 | 1.3784 | 1.2980 | 318 | 58 | 1.4089 | 1.2057 | True | 1 | True |
| D_hgb_buy0.40_sell0.60_m0.10_standalone | hgb | 376 | 1.3784 | 1.2980 | 318 | 58 | 1.4089 | 1.2057 | True | 1 | True |

## Side Policy

- BUY-only gate pass: `False`
- SELL gate pass: `False`
- Combined gate pass: `False`

73-trade RF BUY-only slice has PF/SeqPF > 2 but fails the 100-trade protocol support floor.

Some rows have SELL side PF > 1.0, but they are one-sided/unstable or overfitting-risk rows; confidence monotonicity was not established.

## Conclusion

Corrected validation-only chain did not reproduce a protocol-valid winner. The previous weak uplift does not survive the corrected selection/provenance gates as a production candidate. No frozen test was run.
