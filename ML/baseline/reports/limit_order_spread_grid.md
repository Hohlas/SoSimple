# Limit-Order Entry Convention — Phase 1+2 Final Report

**Date:** 2026-05-28
**Branch:** `feature/limit-order-entry-convention`
**Spec:** `docs/superpowers/specs/2026-05-27-limit-order-entry-design.md`

## Summary

Verdict: **Phase 1+2 PASS** for canonical BUY limit-order baseline at spread=0.20. SELL FAIL. Zero-spread diagnostic only. 2× spread breaks robustness.

## What was tested

Limit-order entry convention: pending BUY/SELL LIMIT at `Close[row]` level, fill window 6 bars, barrier window 24 bars from fill. Model: RF and HGB baseline (sklearn). Target: `buy_sl3_tp3` / `sell_sl3_tp3`. Gate: PF ≥ 1.3, fill_rate ≥ 20%, trades/year ≥ 6, negative_years = 0.

## Spread grid: BUY buy_sl3_tp3

| Spread | Status | Fill % | PF (best) | Trades/yr | Neg Yrs | Mismatch |
|--------|--------|--------|-----------|-----------|---------|----------|
| 0 | **DIAGNOSTIC_ONLY** | 98.6% | 1.556 (HGB) | 169.4 | 0 | 0/0/0 |
| **0.20 (canonical)** | **PASS** | 96.4% | **1.531 (RF)** | 55.3 | 0 | 0/0/0 |
| 0.40 (2× baseline) | FAIL | 93.9% | 1.232 (RF) | 53.8 | 1 | 0/0/0 |
| 0.80 (4× baseline) | FAIL | 90.5% | 1.018 (HGB) | 406.0 | 2 | 0/0/0 |

Spread units: XAUUSD price units (0.20 ≈ 20 points on 5-digit broker). Baseline from MT symbol metadata.

## SELL sell_sl3_tp3 (spread=0, diagnostic reference)

| Model | PF | Neg Yrs | Gate |
|-------|-----|---------|------|
| HGB | 1.36 | 1 | FAIL |
| RF | 0.91 | 3 | FAIL |

SELL consistently fails due to historical XAUUSD bull market. Directions are asymmetric.

## Fill statistics (spread=0, train set)

| Metric | BUY | SELL |
|--------|-----|------|
| Fill rate | 98.5% | 98.6% |
| Instant (lag=0) | 97.4% | 97.8% |
| Quick (lag=1-2) | 1.8% | 1.7% |
| Slow/Tail (lag=3-5) | 0.7% | 0.6% |

Almost all fills happen instantaneously (first bar after signal). Fill rate drops ~2pp per 0.20 spread increment.

## Ambiguity (spread=0, train set, buy_sl3_tp3)

| Type | Count | % of filled |
|------|-------|-------------|
| Clean | 16,830 | 98.4% |
| Fill+SL same bar | 148 | 0.9% |
| Fill+TP same bar | 90 | 0.5% |
| Fill+TP+SL same bar | 2 | 0.01% |
| TP+SL barrier bar | 26 | 0.2% |

Avg PnL: clean = -0.06R, ambiguous = -1.16R (conservative mode correctly penalizes ambiguous rows).

## Implementation

| Artifact | Status |
|----------|--------|
| `label_limit_order_barriers()` in `processing/label_signals.py` | Done |
| Tests (15) covering BUY/SELL fill, spread, ambiguity, PnL, skipped rows | Done |
| `--limit-order --spread` flags in `label_main.py` | Done |
| `processing/purge_split.py` (30-bar time-based purge) | Done |
| `processing/label_audit.py` (fill_lag, ambiguity, comparison audit) | Done |
| `ML/baseline/benchmark_limit_order_entry.py` (RF/HGB baseline) | Done |
| MT4 execution (pending orders) | Deferred |

## Conclusion

Limit-order entry convention at canonical spread passes Phase 2 gate for BUY direction. PF=1.53 with 0 negative years and 55.3 filled trades/year. Robustness margin: breaks at 2× spread (0.40), not at canonical. Phase 3 (Transformer) is justified for BUY only. SELL should be excluded from further investment.
