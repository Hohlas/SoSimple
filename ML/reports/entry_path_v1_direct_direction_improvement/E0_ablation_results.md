# Experiment 0: Feature Ablation Results

Date: 2026-05-15

## Ablation Matrix Results (Target D, RandomForest, threshold grid [0.10, 0.20, 0.30, 0.40])

| Variant | Features | Best PF | Best Seq PF | Threshold | Trades | BUY PF | SELL PF | overfitting_risk |
|---------|----------|---------|-------------|-----------|-------|--------|---------|------------------|
| E0a k=4 (baseline) | 97 | 1.11 | 1.15 | 0.10 | 9415 | 1.31 | 0.99 | False |
| E0b k=6 | 143 | 1.03 | 0.82 | 0.30 | 9264 | 1.20 | 0.94 | False |
| E0c k=8 | 189 | 1.05 | 1.03 | 0.30 | 9251 | 1.21 | 0.94 | False |
| E0d k=16 | 373 | 1.08 | 1.12 | 0.30 | 9221 | 1.29 | 0.97 | False |
| E0e k=4 geom_only | 57 | 1.07 | 1.15 | 0.30 | 9247 | 1.23 | 0.96 | False |

All variants above threshold 0.40 have overfitting_risk=True or <100 trades.

## Top-5 Feature Importances (Target D)

### E0a k=4 baseline
| rank | feature | importance |
|------|---------|------------|
| 1 | nearest_01_front | 0.01792 |
| 2 | nearest_01_impulse | 0.01782 |
| 3 | nearest_00_front | 0.01775 |
| 4 | nearest_03_impulse | 0.01755 |
| 5 | nearest_01_back | 0.01753 |

Avg importance of up/dn features (in top 20): 0.01563
Avg importance of geometry features (in top 20): 0.01674
fractal0_direction: not in top 20

### E0e k=4 geometry_only
| rank | feature | importance |
|------|---------|------------|
| 1 | nearest_02_back | 0.03503 |
| 2 | nearest_00_back | 0.03464 |
| 3 | nearest_01_back | 0.03452 |
| 4 | nearest_03_back | 0.03431 |
| 5 | nearest_01_impulse | 0.03409 |

fractal0_direction: not in top 20

## Diagnostic Answers

1. **Does increasing k improve PF?** No. k=4 (97 features) remains best at PF=1.11. Increasing k to 6/8/16 adds features without signal, predominantly increasing overfitting. k=16 (373 features) partially recovers at threshold=0.30 (PF=1.08) but still worse than k=4.

2. **Do up/dn fields help or hurt?** Marginally. E0e (geometry_only, no up/dn, 57 features) achieves PF=1.07 at threshold=0.30 with Seq PF=1.15 — comparable to k=4 baseline. In baseline, up/dn feature importance averages 0.016 vs geometry 0.017, essentially flat. Removing up/dn loses ~0.04 PF but simplifies the model.

3. **Is signal all in fractal0_direction?** No. `fractal0_direction` is not in top-20 for any variant. Top features are `front`, `back`, `impulse` from nearest fractals. Signal is distributed but weak — all features have importance ~0.015-0.018, essentially flat.

## Conclusion

- k=4 with full features is the best baseline (PF=1.11, still below 1.15 gate)
- Increasing k hurts more than it helps
- up/dn features contribute marginal signal (~0.04 PF difference)
- Feature importances are flat — no single feature dominates
- Proceed to E1 (Binary BUY/SELL models) — the core problem is 3-class separation, not feature engineering

## Winner Gate Status

No variant passes PF >= 1.15. All are negative results for standalone winner.