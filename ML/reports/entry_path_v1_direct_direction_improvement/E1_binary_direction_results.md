# Experiment 1: Binary BUY/SELL Direction Results

Date: 2026-05-15

## Summary

Two independent binary classifiers (BUY-vs-REST and SELL-vs-REST) with HistGradientBoosting and RandomForest.

## Best Balanced Winners (PF >= 1.15, SeqPF >= 1.1, trades >= 100, buy_sell >= 0.20)

| Config | Model | BUY thr | SELL thr | Margin | Trades | PF | Seq PF | BUY PF | SELL PF | BUY/SELL Balance | Neg Years |
|--------|-------|---------|----------|--------|--------|------|--------|--------|---------|------------------|-----------|
| rf_buy0.60_sell0.60_m0.10 | RF | 0.6 | 0.6 | 0.10 | 1828 | 1.257 | 1.192 | 1.342 | 1.209 | 0.337 | 0 |
| rf_buy0.40_sell0.60_m0.10 | RF | 0.4 | 0.6 | 0.10 | 1923 | 1.251 | 1.300 | 1.315 | 1.209 | 0.370 | 0 |
| hgb_buy0.50_sell0.50_m0.00 | HGB | 0.5 | 0.5 | 0.00 | 5182 | 1.160 | 1.398 | 1.396 | 1.019 | 0.380 | 0 |

## Key Findings

1. **RF margin=0.10 with sell_threshold=0.6 is the best balanced configuration** (PF=1.26, SeqPF=1.30). The sell model requires high threshold (0.6) to produce actionable signals.

2. **HGB produces skewed BUY-dominant signals**. Top HGB configs have buy_sell_balance < 0.10, meaning SELL signals are nearly absent.

3. **Margin rule matters for HGB**: simple threshold (margin=0.00) gives one-sided results. Margin=0.05 produces the highest PF (1.38) but extremely unbalanced (91% BUY).

4. **RF with margin=0.10 produces genuinely balanced BUY/SELL** and passes the validation gate with PF >= 1.15 and SeqPF >= 1.1.

5. **Best RF winner**: `rf_buy0.40_sell0.60_m0.10` — PF=1.25, SeqPF=1.30, 711 BUY / 1212 SELL, balance=0.37, 0 negative years.

## Top One-Sided HGB Winners

| Config | Trades | PF | Seq PF | BUY PF | SELL PF | Balance |
|--------|--------|------|--------|--------|---------|---------|
| hgb_buy0.30_sell0.60_m0.05 | 1931 | 1.38 | 1.29 | 1.36 | 1.54 | 0.09 |

Marked as one_sided_candidate=True.

## Comparison to E0 Baseline

| Variant | PF | Seq PF | BUY PF | SELL PF |
|---------|------|--------|--------|---------|
| E0a k=4 baseline (3-class) | 1.11 | 1.15 | 1.31 | 0.99 |
| E1 rf_buy0.40_sell0.60_m0.10 (binary balanced) | 1.25 | 1.30 | 1.32 | 1.21 |
| E1 hgb_buy0.30_sell0.60_m0.05 (binary one-sided) | 1.38 | 1.29 | 1.36 | 1.54 |

Binary models materially improve over 3-class. Best balanced binary (RF, margin=0.10) improves PF from 1.11 to 1.25 and SeqPF from 1.15 to 1.30.