# Experiment 2: HGB + LR 3-Class Model Results

Date: 2026-05-15

## Summary

Tested HistGradientBoosting (HGB) and LogisticRegression (LR) as 3-class classifiers alongside the existing RandomForest baseline.

## Results (Target D, standalone, nearest_k4)

| Model | Best PF | Best Seq PF | Threshold | Trades | BUY PF | SELL PF |
|-------|---------|-------------|-----------|--------|--------|---------|
| RF (baseline) | 1.11 | 1.15 | 0.10 | 9415 | 1.31 | 0.99 |
| HGB | 1.01 | 1.05 | 0.40 | 3294 | 1.15 | 0.93 |
| LR | 1.05 | 0.83 | 0.10 | 9415 | 1.22 | 0.94 |
| LR | 1.11 | 1.23 | 0.40 | 1091 | 1.70 | 0.95 |

## Diagnostic Conclusion

1. **HGB is worse than RF** for 3-class. PF drops from 1.11 to 1.01. The HGB model does not improve classification.
2. **LR is comparable to RF only at high thresholds** (PF=1.11 at threshold=0.40, 1091 trades). At low thresholds, LR is worse (PF=1.05). This means:
   - The signal is partially in linear combinations (LR can extract it with threshold filtering)
   - Non-linear interactions are important at lower thresholds (RF outperforms LR there)
   - The improvement from RF over LR is modest, not dramatic
3. Neither HGB nor LR 3-class passes the PF=1.15 validation gate.

## Decision

E2 does not produce a standalone winner. The 3-class formulation is fundamentally weak regardless of model choice. Proceed to E3 (Zone Features) per plan.