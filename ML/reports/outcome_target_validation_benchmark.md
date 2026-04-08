# Outcome Target Validation Benchmark

- model: `transformer`
- min_trades: 80
- min_stability_ratio: 0.75
- min_year_trades: 10

## Per-Task Winners

| task | status | top_pct | threshold | trades | pf | stability | mean_pnl_atr |
|------|--------|---------|-----------|--------|----|-----------|--------------|
| trade_outcome_cls | no_slice_passed_filters | 0.05 | 0.5186 | 24 | 0.1983 | 0.00 | -3.9206 |
| trade_pnl_reg | no_slice_passed_filters | 0.05 | -2.7215 | 24 | 0.1105 | 0.00 | -3.1042 |
| signal_archetype_cls | no_slice_passed_filters | 0.10 | 0.4800 | 48 | 0.1369 | 0.00 | -4.2492 |

## Frozen Winner

- No target family passed the shared trade-floor and yearly-stability filters.
- No frozen winner was created, so test evaluation must not be run.