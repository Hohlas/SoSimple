# Limit-Order Spread Grid Results

| Spread | Fill Rate | PF (best model) | Trades/yr | Neg Years | Gate |
|--------|----------|-----------------|-----------|-----------|------|
| 0 | 98.6% | 1.556 (HGB) | 169.4 | 0 | PASS |
| 0.20 (canonical) | 96.4% | 1.531 (RF) | 55.3 | 0 | PASS |
| 0.40 (2×) | 93.9% | 1.232 (RF) | 53.8 | 1 | FAIL |
| 0.80 (4×) | 90.5% | 1.018 (HGB) | 406.0 | 2 | FAIL |

## Conclusion
Limit-order hypothesis confirmed at canonical spread (XAUUSD ~20 points).
PF monotonically degrades with spread: 1.56→1.53→1.23→1.02.
Breaks at 2× canonical spread (0.40).
