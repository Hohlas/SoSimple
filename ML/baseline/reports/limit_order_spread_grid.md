# Limit-Order Spread Grid Results (post-fix)

| Spread | Fill Rate | PF (best) | Trades/yr | Neg Years | Mismatch | Gate |
|--------|----------|-----------|-----------|-----------|----------|------|
| 0 | 98.6% | 1.556 (HGB) | 169.4 | 0 | 0/0/0 | **PASS** |
| 0.20 (canonical) | 96.4% | 1.531 (RF) | 55.3 | 0 | 0/0/0 | **PASS** |
| 0.40 (2×) | 93.9% | 1.232 (RF) | 53.8 | 1 | 0/0/0 | FAIL |
| 0.80 (4×) | 90.5% | 1.018 (HGB) | 406.0 | 2 | 0/0/0 | FAIL |

Mismatch: train/val/test row count where fill_lag=-1 but TB target != -999.
Post-fix: all 0 across all spreads and splits.

## Conclusion
- Canonical spread (0.20, ~20 XAUUSD points) passes gate with PF=1.53
- PF degrades: 1.56→1.53→1.23→1.02
- Breaks at 2× spread (0.40): negative year appears
- Hypothesis confirmed at Phase 2 level → eligible for Phase 3 (Transformer)
