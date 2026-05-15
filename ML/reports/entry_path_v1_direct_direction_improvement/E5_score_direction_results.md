# Experiment 5: Score Direction Results

Date: 2026-05-15

## Architecture

Stage 1: Score gate (`pred_ret_24_dir_atr >= -0.0716`) selects ~6174 candidate rows (same universe as production entry_path_v1_live_safe).
Stage 2: Binary HGB BUY-vs-SELL classifier chooses direction.

## Results

| Config | Mode | Trades | PF | Seq PF | BUY trades | SELL trades | BUY PF | SELL PF | Balance |
|--------|------|--------|------|--------|------------|-------------|--------|---------|---------|
| 0.30 | standalone | 6127 | 1.08 | 1.07 | 2402 | 3725 | 1.29 | 0.96 | 0.39 |
| 0.40 | standalone | 5510 | 1.09 | 1.16 | 2402 | 3108 | 1.29 | 0.95 | 0.44 |
| 0.50 | standalone | 2402 | 1.29 | 1.06 | 2402 | 0 | 1.29 | 0.00 | 0.00 |
| 0.60 | standalone | 435 | 1.16 | 1.21 | 435 | 0 | 1.16 | 0.00 | 0.00 |
| 0.30 | fractal0_diagnostic | 6174 | 0.98 | 0.99 | 3337 | 2837 | 1.09 | 0.86 | 0.46 |

## Key Findings

1. **HGB direction resolver improves over fractal0.direction baseline** (PF=1.09 vs 0.98), confirming the ML model adds value over naive direction.
2. **Score-filtered universe produces PF=1.09** at threshold=0.40, SeqPF=1.16 — close to but not exceeding the 1.15 gate.
3. **At high thresholds (0.50+), sell signals disappear** — the model becomes BUY-only, which is one-sided and cannot pass the balance gate.
4. **The score gate provides a fundamentally different candidate universe** — only ~6174 rows vs 9415 in standalone. This restricts diversification.

## Comparison of All Experiments

| Experiment | Best PF | Best Seq PF | Trades | BUY/SELL Balance | Passes Gate? |
|------------|---------|-------------|--------|------------------|--------------|
| E0a k=4 baseline (3-class RF) | 1.11 | 1.15 | 9415 | 0.37 | No (PF<1.15) |
| E1 Binary RF margin=0.10 | 1.25 | 1.30 | 1923 | 0.37 | **Yes** |
| E1 Binary HGB margin=0.05 (one-sided) | 1.38 | 1.29 | 1931 | 0.09 | No (one-sided) |
| E2 HGB 3-class | 1.01 | 1.05 | 3294 | ~0.39 | No |
| E2 LR 3-class | 1.05 | 0.83 | 9415 | ~0.38 | No |
| E3 Zones | 1.08 | 0.87 | 2469 | 0.26 | No |
| E5 Score direction HGB | 1.09 | 1.16 | 5510 | 0.44 | No (PF<1.15) |

**Best balanced winner: E1 Binary RF with margin=0.10** (PF=1.25, SeqPF=1.30, balance=0.37).

## Recommendation

The single best validation configuration is E1 Binary RF `buy_threshold=0.4, sell_threshold=0.6, margin=0.10`:
- PF=1.25, SeqPF=1.30, 1923 trades, 711 BUY / 1212 SELL
- Balance=0.37, 0 negative years
- Passes all validation gates except PF check would need ≥ 1.15 (which it passes with 1.25)

This should proceed to frozen test per the plan's overall test procedure.