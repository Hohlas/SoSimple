# Stage 6.2 Range W1 Post-Mortem

> **Дата**: 2026-06-30
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: Check why `range_w1_atr` dominates Stage 6.2 and why the stability check remains weak.

## Sources And Commands

- Source Stage 6.2 JSON: `ML/reports/stage6_2_h12_price_action_feature_family.json`.
- Generated JSON: `ML/reports/stage6_2_range_w1_postmortem.json`.
- Command: `./.venv/bin/python ML/baseline/analyze_stage6_2_range_w1_postmortem.py`.
- Scope: no retraining, no new horizon/ATR/TP/SL/profile search.

## Artifact Consistency

- Primary profile: `h12_price_action_core`.
- Stage 6.2 gate status: `TRADING_GATE_FAILED`.
- Stage 6.2 primary p-value: `0.16`.
- Top feature from Stage 6.2 JSON: `range_w1_atr`.

## Multiple Testing Context

- This post-mortem runs after the fixed Stage 6.2 search: 5 profiles x 3 seeds.
- It does not train models, add features, search thresholds, or change the gate.
- `val_stop` is used only to explain the already failed Stage 6.2 gate.
- `diagnostic_holdout` and `low_n_disclosure` remain disclosure-only.

## Facts

- Top feature: `range_w1_atr`.
- Top/second importance ratio: `7.561135293909447`.
- `range_w1_atr` vs target correlation on non-zero `val_stop`: `0.202190339994974`.
- `range_w1_atr` vs PnL correlation on non-zero `val_stop`: `0.008055152024203831`.
- Primary permutation p-value: `0.16`; required `<= 0.1`.
- Seed p-value range: `0.155` to `0.35`.
- Zero-vector rows on `val_stop`: `3/5415`.
- Evidence strength: `weak`.

## Selected Trade Analysis

- Seeds available for selected-trade analysis: `3/3`.
- See JSON section `selected_trade_analysis.per_seed` for selected vs non-selected TP-rate, PnL, and bucket rates.

## Side And Year Disclosure

- See JSON section `side_analysis` for BUY/SELL counts, TP-rate, PnL, and correlations.
- See JSON section `year_side_matrix` for year x side breakdown.

## Activity Proxy Checks

- `range_w1_atr` vs `ATR` correlation: `-0.05920375836345099`.
- `range_w1_atr` vs `bar_range_1_atr` correlation: `0.8462004381696618`.
- Zero-vector share on `val_stop`: `0.000554016620498615`.

## Validation Disclosure

- `val_stop`: `3/5415` zero-vector rows.
- `diagnostic_holdout`: `48/8091` zero-vector rows.
- `low_n_disclosure`: `551/1162` zero-vector rows.
- `diagnostic_holdout` and `low_n_disclosure` were not used for choosing profiles, seeds, thresholds, or gates.

## Permutation Context

- Observed median PF: `1.306892558717911`.
- Observed PF range: `1.1796434030029757` to `1.3587603797701053`.
- See JSON section `permutation_context.per_seed` for observed PF vs median and p95 random PF by seed.

## Interpretation

- Facts above are measurements from the frozen Stage 6.2 artifacts.
- The dominant feature is associated with the one-bar price range, but this is not enough to prove a robust trading rule.
- The stability check stayed weak because observed PF was not far enough above the random-permutation comparison across seeds.
- Any causal explanation remains a hypothesis unless a later fixed validation cycle tests it.

This post-mortem does not change the Stage 6.2 verdict and does not promote the feature family.

## Forbidden Next Steps

- Do not reopen H12/ATR/TP/SL search from this result.
- Do not create another small OHLC-window variant unless this report provides concrete evidence for a materially new family.

## Decision

- Promote Stage 6.2: `False`.
- Next research step: `Regression Up/Dn target foundation`.
