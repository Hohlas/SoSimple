# Stage 5.4 Fast Price/ATR Ablation Report

**Date:** 2026-06-29
**Status:** `DIAGNOSTIC_ONLY` — price/ATR coordinate does not improve `fast` breach prediction.

## Context

Stage 5.3 identified `fast` (bars_to_breach ∈ {1,2}) as the most promising target for sell. The hypothesis for Stage 5.4: ATR-normalized distance to fractal level (`price_coord_atr`) should help predict _early_ breach specifically, because the physical distance to the level expressed in ATR units has a direct timing interpretation.

This is a narrow retest of `price_coord_atr`, which was previously tested in Stage 5.0a/5.0b on binary breach profiles and did not produce a candidate. Stage 5.4 is justified only by the fixed `fast` target (not binary breach).

## What Was Done

- **Target:** `fast` (bars_to_breach ∈ {1,2})
- **Profiles:** 12 (2 baselines, 2 primary, 2 secondary, 6 diagnostic)
- **Sides:** sell + buy
- **Seeds:** 3 (42, 77, 123)
- **Total models:** 2 × 12 × 3 = 72 XGBoost classifiers
- **Workers:** 12 parallel, 1 XGBoost thread each
- **Elapsed time:** ~36 minutes

### Profiles

| Profile | Role | Description |
|---------|------|-------------|
| `clock_shift_back` | sell baseline | shift + back (log1p) |
| `clock_shift_back_price_coord_atr` | sell primary | + price_coord_atr (signed_log1p) |
| `clock_shift_back_price_coord_atr_price_atr_scaled` | secondary | + price_atr_scaled (asinh) |
| `clock_shift_back_atr_log1p` | diagnostic | + ATR row (log1p) |
| `clock_shift_back_atr_asinh` | diagnostic | + ATR row (asinh) |
| `clock_shift_back_updn` | diagnostic | + all Up/Dn fields |
| `clock_shift_back_impulse` | buy baseline | shift + back + impulse (log1p) |
| `clock_shift_back_impulse_price_coord_atr` | buy primary | + price_coord_atr (signed_log1p) |
| `clock_shift_back_impulse_price_coord_atr_price_atr_scaled` | secondary | + price_atr_scaled (asinh) |
| `clock_shift_back_impulse_atr_log1p` | diagnostic | + ATR row (log1p) |
| `clock_shift_back_impulse_atr_asinh` | diagnostic | + ATR row (asinh) |
| `clock_shift_back_impulse_updn` | diagnostic | + all Up/Dn fields |

## A7 Preflight Audit

All 24 profile-source-target combinations passed A7 audit with `WARNING` status (no `ERROR` blockers).

- **Flags:** `ZERO_GT95` only — expected because `shift` is 0 for most dormant fractal positions
- **No `TAIL_GT10`/`TAIL_GT20`:** price_coord_atr has clean distributions without extreme tails even on old positions (fractal90..fractal99)
- **No `REGIME_SHIFT`:** train/holdout distributions are consistent
- **No `PRICE_COORD_BACK_CORR_GT_0_8`:** max Spearman correlation between `price_coord_atr` and `back` is 0.70 (sell) / 0.74 (buy) — below the 0.8 warning threshold

## Results

### Sell Side

| Profile | Role | Median Val AUC | Delta vs Baseline | Per-Seed Pass ≥0.02 | Holdout Drop |
|---------|------|:-:|:-:|:-:|:-:|
| clock_shift_back | baseline | 0.6859 | — | — | +0.0017 |
| **clock_shift_back_price_coord_atr** | **primary** | **0.6925** | **+0.0066** | **0/3** | +0.0050 |
| clock_shift_back_price_coord_atr_price_atr_scaled | secondary | 0.6907 | +0.0048 | 0/3 | +0.0026 |
| clock_shift_back_atr_log1p | diagnostic | 0.6968 | +0.0108 | 0/3 | +0.0088 |
| clock_shift_back_atr_asinh | diagnostic | 0.6968 | +0.0108 | 0/3 | +0.0088 |
| clock_shift_back_updn | diagnostic | 0.6937 | +0.0077 | 0/3 | +0.0100 |
| clock_shift_back_impulse | baseline | 0.6938 | +0.0078 | 0/3 | +0.0101 |
| clock_shift_back_impulse_price_coord_atr | primary | 0.6882 | +0.0023 | 0/3 | -0.0039 |
| clock_shift_back_impulse_price_coord_atr_price_atr_scaled | secondary | 0.6929 | +0.0070 | 0/3 | +0.0031 |
| clock_shift_back_impulse_atr_log1p | diagnostic | 0.6930 | +0.0071 | 0/3 | +0.0058 |
| clock_shift_back_impulse_atr_asinh | diagnostic | 0.6930 | +0.0071 | 0/3 | +0.0058 |
| clock_shift_back_impulse_updn | diagnostic | 0.6970 | +0.0110 | 0/3 | +0.0116 |

**Per-seed deltas for sell primary `clock_shift_back_price_coord_atr`:**

| Seed | Primary AUC | Baseline AUC | Delta | Pass ≥0.02 |
|:----:|:-----------:|:------------:|:-----:|:----------:|
| 42 | 0.6936 | 0.6850 | +0.0086 | No |
| 77 | 0.6830 | 0.6984 | -0.0153 | No |
| 123 | 0.6925 | 0.6859 | +0.0066 | No |

### Buy Side

| Profile | Role | Median Val AUC | Delta vs Baseline | Per-Seed Pass ≥0.02 | Holdout Drop |
|---------|------|:-:|:-:|:-:|:-:|
| clock_shift_back | baseline | 0.7151 | +0.0029 | 0/3 | +0.0574 |
| clock_shift_back_price_coord_atr | primary | 0.7131 | +0.0009 | 0/3 | +0.0542 |
| clock_shift_back_price_coord_atr_price_atr_scaled | secondary | 0.7151 | +0.0030 | 0/3 | +0.0568 |
| clock_shift_back_atr_log1p | diagnostic | 0.7128 | +0.0006 | 0/3 | +0.0576 |
| clock_shift_back_atr_asinh | diagnostic | 0.7128 | +0.0006 | 0/3 | +0.0576 |
| clock_shift_back_updn | diagnostic | 0.7114 | -0.0008 | 0/3 | +0.0527 |
| clock_shift_back_impulse | baseline | 0.7122 | — | — | +0.0541 |
| **clock_shift_back_impulse_price_coord_atr** | **primary** | **0.7136** | **+0.0014** | **0/3** | +0.0551 |
| clock_shift_back_impulse_price_coord_atr_price_atr_scaled | secondary | 0.7165 | +0.0043 | 0/3 | +0.0601 |
| clock_shift_back_impulse_atr_log1p | diagnostic | 0.7134 | +0.0013 | 0/3 | +0.0587 |
| clock_shift_back_impulse_atr_asinh | diagnostic | 0.7134 | +0.0013 | 0/3 | +0.0587 |
| clock_shift_back_impulse_updn | diagnostic | 0.7069 | -0.0053 | 0/3 | +0.0484 |

**Per-seed deltas for buy primary `clock_shift_back_impulse_price_coord_atr`:**

| Seed | Primary AUC | Baseline AUC | Delta | Pass ≥0.02 |
|:----:|:-----------:|:------------:|:-----:|:----------:|
| 42 | 0.7104 | 0.7115 | -0.0011 | No |
| 77 | 0.7154 | 0.7142 | +0.0012 | No |
| 123 | 0.7136 | 0.7122 | +0.0014 | No |

## Gate Results

### Sell: `DIAGNOSTIC_ONLY`

| Check | Result |
|-------|:------:|
| Target is `fast` | ✅ |
| Evaluated candidate is primary | ✅ |
| Val AUC ≥ 0.65 | ✅ (0.6925) |
| PR AUC lift ≥ 0.03 | ✅ (0.321 - 0.150 = 0.171) |
| Median delta vs baseline ≥ 0.02 | ❌ (+0.0066) |
| Per-seed delta ≥ 0.02 in ≥ 2/3 | ❌ (0/3) |
| Yearly ≥ 2 years ≥ 0.60 | ✅ |
| Holdout drop ≤ 0.06 | ✅ (0.0050) |

### Buy: `DIAGNOSTIC_ONLY`

| Check | Result |
|-------|:------:|
| Target is `fast` | ✅ |
| Evaluated candidate is primary | ✅ |
| Val AUC ≥ 0.65 | ✅ (0.7136) |
| PR AUC lift ≥ 0.03 | ✅ (0.318 - 0.156 = 0.162) |
| Median delta vs baseline ≥ 0.02 | ❌ (+0.0014) |
| Per-seed delta ≥ 0.02 in ≥ 2/3 | ❌ (0/3) |
| Yearly ≥ 2 years ≥ 0.60 | ✅ |
| Holdout drop ≤ 0.04 | ❌ (0.0551 — critical warning) |

## Interpretation

### Primary Hypothesis: Rejected

`price_coord_atr` does not improve `fast` breach prediction on either side. The AUC deltas are marginal (+0.0066 sell, +0.0014 buy) and no single seed reaches the 0.02 threshold.

This is consistent with the Stage 5.0a/5.0b findings that price/ATR features do not help breach prediction, even when narrowed to the `fast` bucket. The prior caveat from the plan is confirmed: the physical argument (distance to level in ATR → earlier breach) does not materialize in the data.

### Secondary/Diagnostic Profiles

- **ATR row profiles** (`atr_log1p`, `atr_asinh`): show slightly higher median AUC on sell (0.6968), but remain diagnostic-only. Their per-seed deltas do not pass the ≥0.02 rule, so this is not a promotable signal.
- **Up/Dn group**: no meaningful improvement. Max delta +0.011 (sell `impulse_updn`), 0/3 seeds.
- **`price_atr_scaled`** (secondary): no improvement over `price_coord_atr` alone. The regime-sensitivity concern is moot because neither candidate approaches the gate.

### Buy Side

Buy remains borderline as expected from Stage 5.3 (`delta ≥ 0.02` in only 1/3 seed). The `price_coord_atr` does not rescue it. The holdout drop of 0.055 exceeds the 0.04 critical threshold, confirming that buy `fast` is not a reliable signal.

## Next Steps

**Decision: `REJECT_PRICE_COORD`** (sell) + **`BUY_DISCLOSURE_ONLY`** (buy)

- Price/ATR features do not explain the missing `fast` signal. Do not expand to broader price search.
- ATR regime features (row-level `log1p`/`asinh`) show weak diagnostic signal but insufficient to pursue.
- Stage 5.4 closes without a candidate. Stage 5.3 `fast` sell remains the best available signal but with the limitation that `price_coord_atr` does not fill the gap.

## Limitations

- **2023-2025** is diagnostic disclosure only, not independent confirmation.
- 12 profiles × 3 seeds = 72 model comparisons without multiple-testing correction.
- No trading PF evaluation, no survival-loss check.
- `price_atr_scaled` is non-stationary by construction; its failure does not require additional regime analysis.
