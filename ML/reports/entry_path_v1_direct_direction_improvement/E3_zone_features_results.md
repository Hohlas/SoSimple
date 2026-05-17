# Experiment 3: Zone Features Results

Date: 2026-05-15

## Results (Target D, RandomForest, 3-class)

| Input Family | Features | Best PF | Best Seq PF | Threshold | Trades | BUY PF | SELL PF |
|-------------|----------|---------|-------------|-----------|--------|--------|---------|
| nearest_k4 (baseline) | 97 | 1.11 | 1.15 | 0.10 | 9415 | 1.31 | 0.99 |
| zones | 127 | 1.08 | 0.87 | 0.40 | 2469 | 1.17 | 1.05 |
| zones_plus_nearest_k4 | 221 | 1.04 | 0.87 | 0.30 | 9293 | 1.24 | 0.95 |

## Conclusion

- **Zone features alone (PF=1.08) are worse than nearest_k4 baseline (PF=1.11).**
- **Zones + nearest_k4 combined (PF=1.04) is worse than either alone**, suggesting the zone features add noise rather than signal.
- Zone features do improve SELL PF slightly (1.05 vs 0.99) but at the cost of BUY PF and overall performance.
- Zone aggregation masks fine-grained proximity information that nearest_k preserves better.

Decision: Zone features do not improve the 3-class model. Proceed to E5 (Score Direction) since E4 (Target Grid) would test different target parameters with the same 3-class formulation, which has consistently shown PF < 1.15. The best results so far are from E1 (binary models).