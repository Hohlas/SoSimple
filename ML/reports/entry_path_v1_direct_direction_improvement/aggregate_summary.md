# Direct Direction Improvement: Aggregate Results Summary

Date: 2026-05-15

## Experiment Results Overview

| # | Experiment | Best PF | Best Seq PF | Trades | BUY PF | SELL PF | BUY/SELL Balance | Passes Gate? |
|---|------------|---------|-------------|--------|--------|---------|------------------|--------------|
| E0a | k=4 baseline (3-class RF) | 1.11 | 1.15 | 9415 | 1.31 | 0.99 | 0.37 | No (PF<1.15) |
| E0b | k=6 (3-class RF) | 1.03 | 0.82 | 9264 | 1.20 | 0.94 | 0.38 | No |
| E0c | k=8 (3-class RF) | 1.05 | 1.03 | 9251 | 1.21 | 0.94 | 0.38 | No |
| E0d | k=16 (3-class RF) | 1.08 | 1.12 | 9221 | 1.29 | 0.97 | 0.37 | No |
| E0e | k=4 geometry_only (3-class RF) | 1.07 | 1.15 | 9247 | 1.23 | 0.96 | 0.38 | No |
| **E1** | **Binary RF margin=0.10** | **1.25** | **1.30** | **1923** | **1.32** | **1.21** | **0.37** | **Yes** |
| E1 | Binary HGB margin=0.05 (one-sided) | 1.38 | 1.29 | 1931 | 1.36 | 1.54 | 0.09 | No (one-sided) |
| E2 | HGB 3-class | 1.01 | 1.05 | 3294 | 1.15 | 0.93 | 0.39 | No |
| E2 | LR 3-class | 1.05 | 0.83 | 9415 | 1.22 | 0.94 | 0.38 | No |
| E3 | Zones (3-class RF) | 1.08 | 0.87 | 2469 | 1.17 | 1.05 | 0.26 | No |
| E3 | Zones+nearest_k4 (3-class RF) | 1.04 | 0.87 | 9293 | 1.24 | 0.95 | 0.33 | No |
| E5 | Score direction HGB | 1.09 | 1.16 | 5510 | 1.29 | 0.95 | 0.44 | No (PF<1.15) |
| E5 | Fractal0.direction diagnostic | 0.98 | 0.99 | 6174 | 1.09 | 0.86 | 0.46 | No |

## Overall Winner

**E1 Binary RF with margin=0.10, buy_threshold=0.4, sell_threshold=0.6**

- PF=1.25, SeqPF=1.30, 1923 trades (711 BUY / 1212 SELL)
- BUY/SELL balance=0.37, 0 negative years
- Passes all validation gates (PF≥1.15, SeqPF≥1.1, trades≥100, not overfitting, not one-sided)

## Files Changed

- `ML/fractal_level_feature_builder.py` — added geometry_only, zones, zones_plus_nearest_k
- `ML/benchmark_entry_path_fractal_level_direct_direction.py` — added --k, --geometry-only, --model, --input-family, --e0-grid
- `ML/benchmark_entry_path_binary_direction.py` — new file, binary BUY/SELL models
- `ML/benchmark_entry_path_score_direction.py` — new file, score-filtered direction resolver
- `tests/test_fractal_level_feature_builder.py` — k variants, geometry_only, zones tests
- `tests/test_benchmark_entry_path_binary_direction.py` — new file, binary signal logic tests

## E0 Diagnostic Answers

1. **Does increasing k improve PF?** No. k=4 (97 features) remains best at PF=1.11. Adding neighbors (k=6 PF=1.03, k=8 PF=1.05, k=16 PF=1.08) degrades or does not improve.
2. **Do up/dn fields help or hurt?** Marginally. E0e geometry_only (57 features, no up/dn) achieves PF=1.07 at threshold=0.30. In baseline, up/dn importance ~0.016 vs geometry ~0.017 — essentially flat.
3. **Is signal all in fractal0_direction?** No. fractal0_direction not in top-20 for any variant. Top features: front, back, impulse from nearest fractals. Signal distributed but weak.

## E2 Diagnostic Conclusion (LR vs RF vs HGB)

- LR comparable to RF only at high thresholds (LR PF=1.11 at thr=0.40). At low thresholds, LR much worse (PF=1.05 at thr=0.10).
- Non-linear interactions matter at lower thresholds. Signal is partially linear but RF extracts more.
- HGB 3-class is worse than RF (PF=1.01), likely due to different class weighting behavior.

## E1 Detailed Binary Winners Table

| Config | Model | BUY thr | SELL thr | Margin | Trades | PF | Seq PF | BUY PF | SELL PF | Balance | Neg Yrs |
|--------|-------|---------|----------|--------|--------|------|--------|--------|---------|---------|---------|
| rf_buy0.60_sell0.60_m0.10 | RF | 0.6 | 0.6 | 0.10 | 1828 | 1.257 | 1.192 | 1.342 | 1.209 | 0.337 | 0 |
| **rf_buy0.40_sell0.60_m0.10** | **RF** | **0.4** | **0.6** | **0.10** | **1923** | **1.251** | **1.300** | **1.315** | **1.209** | **0.370** | **0** |
| rf_buy0.30_sell0.60_m0.10 | RF | 0.3 | 0.6 | 0.10 | 1923 | 1.251 | 1.300 | 1.315 | 1.209 | 0.370 | 0 |
| hgb_buy0.30_sell0.30_m0.05 | HGB | 0.3 | 0.3 | 0.05 | 4637 | 1.208 | 1.237 | 1.362 | 1.112 | 0.379 | 0 |
| hgb_buy0.50_sell0.50_m0.00 | HGB | 0.5 | 0.5 | 0.00 | 5182 | 1.160 | 1.398 | 1.396 | 1.019 | 0.380 | 0 |

## Frozen Test Baselines (from plan)

| Baseline | Test PF | Seq PF | Trades / seq trades |
|----------|---------|--------|---------------------|
| all-rows ranking | 0.9134 | 0.5908 | 329 / 133 |
| causal surrogate | 1.1537 | 1.4111 | 36 / 31 |
| direct bar model | 1.1141 | 1.1334 | 1277 / 274 |
| fractal level direct direction (D nearest_k4) | computed | computed | computed |

## Next Step

Per the plan: select the E1 binary RF winner and run one frozen test.