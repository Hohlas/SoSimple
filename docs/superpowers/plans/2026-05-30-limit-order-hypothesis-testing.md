# Hypothesis Testing Plan: Limit-Order BUY RF Baseline

**Date:** 2026-05-30
**Branch:** `feature/limit-order-entry-convention`
**Stage status:** not closed — testing hypotheses before MT4 execution decision

## Context

Limit-order entry convention baseline gate PASS for BUY buy_sl3_tp3 at canonical spread=0.20: RF PF=1.53 (RF: n_estimators=100, max_depth=10, 102 flat fractal features — see Feature breakdown below). SELL FAIL (XAUUSD bull market). Transformer AUC=0.5 (random). Three hypotheses to test before committing to MT4 execution.

## Data source

**Canonical spread data:** `DATA/spread_0.20/Nero_{train,validation,test}_labeled.csv`

Verified split (already chronological):
- train: 2004-07-06 → 2019-06-14
- validation: 2019-06-17 → 2022-11-24
- test: 2022-11-25 → 2026-05-26

Do NOT use `DATA/limit_order/` — that directory contains mixed-spread data.

## Feature reference (all available feature variants)

### Flat features (current baseline)

`parse_fractal_to_features()` in `benchmark_limit_order_entry.py:33-72`. Extracts via `split(':')`:

| Feature name | Fractal field index | Actual field | Count |
|-------------|---------------------|--------------|-------|
| f0_price .. f99_price | parts[2] | **direction** (1=up, -1=down) — названо price ошибочно | 100 |
| f0_dir | parts[3] (fractal0 only) | **front** (расстояние до фронтального бара) — названо dir ошибочно | 1 |
| ATR | row column | ATR (волатильность) строки | 1 |
| **Total** | | | **102** |

Note: fractal0 price, power, impulse, up/dn excursions NOT used in flat baseline.

### Engineered features

`build_grouped_features()` in `feature_importance_diagnostics.py:160-200`. Fractal fields grouped by meaning:

| Group | Fields | Meaning |
|-------|--------|---------|
| price_position | price | Цена (относительное положение) |
| direction | direction | Направление |
| geometry | front, back, reverse | Расстояния до соседей, сила разворота |
| strength | strong, power, count | Сила уровня, мощность импульса, подтверждения |
| break_impulse | break, impulse | Пробой, импульс |
| path_long | up_12, dn_12, up_24, dn_24, up_48, dn_48 | Экскурсии 12/24/48 баров |
| path_short | up_3, dn_3, up_6, dn_6 | Экскурсии 3/6 баров |
| atr | fractal_atr | Волатильность фрактала |

For each field × group, over each of 5 windows (5, 10, 20, 50, 100 most recent fractals), compute 4 aggregations: mean, std, max, last.

Example: `power_mean_w20` = средняя мощность по 20 последним фракталам. `impulse_max_w50` = максимальный импульс по 50 последним.

Plus row-level features: `row_atr`, `row_hour_sin/cos`, `row_weekday_sin/cos`, `row_range_atr_6`, `row_body_atr_3`, `row_ret_dir_atr_lag1` (UNSAFE — must exclude), `row_vol_regime_24`.

Total: ~233 features after excluding `ret_dir_atr_lag1`.

### SAFETY rule

`ret_dir_atr_lag1` is future-derived (directional return over the NEXT bar, must be known at current bar to compute). It appears in `build_grouped_features` if the column exists in the frame. **Must explicitly drop** both `ret_dir_atr_lag1` and `row_ret_dir_atr_lag1` before training. Otherwise performance gains may be from leakage, not signal.

## Targets reference

All 12 TB (Triple Barrier) binary columns. Each column answers: "did price reach TP before SL within 24 bars from fill?"

| Target column | Side | SL (ATR) | TP (ATR) | Interpretation |
|--------------|------|----------|----------|----------------|
| buy_sl2_tp3 | BUY | 2 | 3 | Широкий стоп, близкий профит |
| buy_sl2_tp6 | BUY | 2 | 6 | Широкий стоп, средний профит |
| buy_sl2_tp9 | BUY | 2 | 9 | Широкий стоп, дальний профит |
| buy_sl3_tp3 | BUY | 3 | 3 | **Baseline** — узкий стоп, близкий профит |
| buy_sl3_tp6 | BUY | 3 | 6 | Узкий стоп, средний профит |
| buy_sl3_tp9 | BUY | 3 | 9 | Узкий стоп, дальний профит |
| sell_sl2_tp3 | SELL | 2 | 3 | (исключён — SELL FAIL) |
| ... | ... | ... | ... | ... |
| sell_sl3_tp9 | SELL | 3 | 9 | (исключён) |

Values: `1.0` = TP reached first, `0.0` = SL reached first, `-999` = limit order not filled.

SL and TP are NOT targets — they are parameters defining WHICH target column. Model predicts a score in [0, 1]; trading system sets fixed SL/TP values.

Accompanying columns per target: `{target}_pnl_r` = R-multiple PnL (includes timeout PnL). Used for PF computation, not for training.

Per-side fill columns: `buy_fill_lag`, `sell_fill_lag` — which bar after signal the limit order filled (-1 = not filled).

## Hypothesis 1: Engineered features vs flat features

**Question:** does RF on engineered features outperform flat features, controlling for hyperparameters?

### Variant matrix

| Code | Features | RF params (trees, depth, min_leaf) | Purpose |
|------|----------|-------------------------------------|---------|
| H1a | Flat 102 | 100, 10, 1 (baseline) | Reproduce baseline — control |
| H1b | Flat 102 | 160, 15, 20 (tuned) | Isolate HP effect: does tuning alone improve PF? |
| H1c | Engineered ~233 (no leak) | 100, 10, 1 (same as baseline) | Isolate feature effect: do engineered features help? |
| H1d | Engineered ~233 (no leak) | 160, 15, 20 (tuned) | Combined: best features + best params |

All train on `buy_sl3_tp3` labels from canonical spread=0.20 data.

### Task

1. Load `DATA/spread_0.20/Nero_{train,validation}_labeled.csv`
2. Build flat features: `parse_fractal_to_features` (optional: add `fractal0_price_raw` for price info)
3. Build engineered features: `build_grouped_features(df, seq_len=100)`, drop `ret_dir_atr_lag1`, `row_ret_dir_atr_lag1`
4. Run H1a–H1d
5. Evaluate each on validation: PF, fill_rate, trades/year, negative_years, yearly PF slices
6. Additional check: **single-day profit concentration**. For the best threshold of each variant:
   - Group filled PnL by day, find top-1 day and top-5 days profit share
   - If >30% of total profit from one day → flag as unstable regardless of PF

### Success criteria

| Criterion | Threshold | Priority |
|-----------|-----------|----------|
| Gate (PF, fill_rate, trades/yr, neg_years) | PF ≥ 1.3, fill ≥ 20%, trades/yr ≥ 6, neg_years = 0 | Required |
| Single-day concentration | Top-1 day < 30% of total profit | Required |
| Yearly PF std | Lower than baseline → better stability | Bonus |
| Max drawdown year | Not worse than baseline | Bonus |
| H1d PF ≥ H1a PF (1.53) | Improvement over flat baseline | Bonus |

## Hypothesis 2: Split/purge audit

**Question:** is there any data leakage across train/val/test boundaries?

### Task

1. Read `DATA/spread_0.20/Nero_{train,validation,test}_labeled.csv`
2. Verify boundary integrity:
   - `train_max_time < val_min_time` and `val_max_time < test_min_time` (no overlap)
   - `val_min_time - train_max_time ≥ 30h` (purge applied at train/val boundary)
   - `test_min_time - val_max_time ≥ 30h` (purge applied at val/test boundary)
3. Count rows removed by purge at each boundary
4. Verify no future leakage in features:
   - For each train row, ensure fractal0.time ≤ row.time (no fractal from the future)
   - Check that `buy_fill_lag` column's fill_idx doesn't point to a bar in val/test
5. Write audit manifest to `docs/reports/`

### Success criteria

- No timestamp overlap between splits
- Purge gap ≥ 30h at both boundaries
- No future fractal timestamps
- No fill_idx crossing split boundaries

## Hypothesis 3: Adjacent barrier robustness

**Question:** does the edge hold for neighboring SL/TP combinations?

**Important:** each target trains a NEW model. `--target buy_sl2_tp3` trains RF on buy_sl2_tp3 labels and evaluates on buy_sl2_tp3 outcomes. No model reuse across targets.

### Barrier interpretation

| Target | SL | TP | What it tests | If FAIL |
|--------|----|----|---------------|---------|
| buy_sl3_tp3 | 3 | 3 | Baseline — PASS | — |
| buy_sl2_tp3 | 2 | 3 | Wider SL (easier to stay, more SL hits) | Edge sensitive to SL choice → buy_sl3_tp3 is "narrow candidate" |
| buy_sl3_tp6 | 3 | 6 | Longer TP (harder to reach) — diagnostic only | Expected difficulty — not a blocker |

### Task

1. Run `benchmark_limit_order_entry.py --train DATA/spread_0.20/Nero_train_labeled.csv --val DATA/spread_0.20/Nero_validation_labeled.csv --target buy_sl2_tp3`
2. Run same with `--target buy_sl3_tp6`
3. Gate evaluation per target: PF ≥ 1.3, fill_rate ≥ 20%, trades/yr ≥ 6, negative_years = 0
4. Yearly PF slice comparison across targets

### Success criteria

| Outcome | Classification | Decision |
|---------|---------------|----------|
| buy_sl2_tp3 PASS + buy_sl3_tp3 PASS | "broad candidate" — barrier-robust | Strong signal → MT4 |
| buy_sl3_tp3 PASS, buy_sl2_tp3 FAIL | "narrow candidate" — specific to SL=3 | Document sensitivity → MT4 with SL=3 only |
| Both FAIL | Edge not reproducible | Retract Phase 2 PASS, no MT4 |

buy_sl3_tp6 is diagnostic only — its FAIL does not block.

## Overall decision matrix

| H1 (features) | H2 (audit) | H3 (barriers) | Action |
|--------------|------------|---------------|--------|
| Gate PASS + stable | PASS | Broad candidate | Proceed to MT4 pending-order execution |
| Gate PASS + stable | PASS | Narrow candidate | Proceed to MT4, document SL=3 constraint |
| Gate PASS but unstable (single-day) | PASS | Any | Do NOT proceed. Fix concentration before MT4. |
| Gate FAIL | PASS | Any | Document, close experiment, no MT4 |
| Any | FAIL | Any | Fix data leakage, retest |

## Key files for context

Read in order:
1. `CONTEXT_HANDOFF.md` — current state, what was done
2. `docs/superpowers/specs/2026-05-27-limit-order-entry-design.md` — design spec (7 sections)
3. `ML/baseline/reports/limit_order_spread_grid.md` — Phase 1+2 results (72 lines)
4. `ML/baseline/benchmark_limit_order_entry.py` — RF/HGB baseline: features:33-72, models:188-195, eval:85-148
5. `ML/feature_importance_diagnostics.py:67-80` — GROUP_FIELDS (engineered feature groups)
6. `ML/feature_importance_diagnostics.py:160-200` — `build_grouped_features()` implementation
7. `processing/label_signals.py:1180-1390` — `label_limit_order_barriers()` column names, fill/target/PnL logic
8. `processing/purge_split.py` — 30-bar time-based purge logic
9. `ML/reports/limit_order_transformer.json` — Phase 3 Transformer results (AUC~0.5)
10. `ML/limit_order_train.py` — Phase 3 training code (for reference, not to rerun)
11. `DATA/spread_0.20/` — canonical spread labelled data
