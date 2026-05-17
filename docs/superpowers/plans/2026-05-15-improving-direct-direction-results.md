# Improving Direct Direction Results: Iterative Improvement Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Iteratively improve the fractal-level SELL/SKIP/BUY direct-direction model, which currently fails validation gates (best standalone PF=1.11 < 1.15 gate), by testing binary models, alternative ML algorithms, zone features, tighter targets, and score-filtered direction.

**Architecture:** A sequence of experiments sharing existing infrastructure (feature builder, target builder, benchmark runner). Each experiment produces its own output directory under `ML/reports/`. Experiments run one at a time. **All experiments use only train/validation. Frozen test runs exactly once after selecting the single best validation winner across all experiments.**

**Tech Stack:** Python 3.12, pandas, numpy, scikit-learn (RandomForestClassifier, HistGradientBoostingClassifier, LogisticRegression), pytest, existing `processing.label_signals`, existing entry-path benchmark helpers.

---

## Current Baseline (2026-05-15)

| Config | PF | Seq PF | Trades | BUY/SELL | Gate fail |
|--------|-----|--------|--------|----------|-----------|
| D_nearest_k4 0.1 | 1.11 | 1.15 | 9415 | 3656/5759 | PF < 1.15 |
| D_nearest_k4 0.3 | 1.11 | 0.99 | 9280 | 3583/5697 | PF < 1.15 |
| D_nearest_k4 0.4 | 1.05 | 1.17 | 417 | 116/301 | overfitting |
| A_nearest_k4 0.1 | 1.00 | 1.29 | 9415 | 4440/4975 | PF < 1.15 |
| C_nearest_k4 0.1 | 0.99 | 1.19 | 9415 | 4339/5076 | PF < 1.15 |

Feature count: 97 (nearest_k4). All 3-class models produce direction probabilities barely above random (~0.35). Best BUY PF = 1.31 (D @ 0.1), but SELL PF = 0.99.

---

## Execution Rules

- Do not use a git worktree; project rules forbid it.
- Create a new branch from current `entry-path-all-rows-spec` or current branch. Recommended branch name: `improve-direct-direction-results`.
- Use `./.venv/bin/python`.
- Each experiment uses its own output directory: `ML/reports/entry_path_v1_<experiment_name>/`.
- Do not modify existing working code without tests.
- Stop an experiment early if validation PF < 1.0 for all thresholds.
- All trading evaluation: next-bar open entry, 24-bar close exit, sequential hold, no spread/commission/slippage.
- **CRITICAL: All experiments E1–E5 use only train/validation. Frozen test runs exactly once after choosing the overall best validation winner across all experiments. No experiment runs frozen test independently.**
- Do not run test before the overall validation winner is frozen.
- After each experiment: checkpoint commit or report changed files. Code changes to shared modules use CLI arguments (`--model`, `--input-family`, `--target-d-params`), not code branching.
- Do not use `source["signal"]` as production candidate gate. It is offline/unsafe and can only appear as a diagnostic baseline.

---

## Experiment 0: Feature Ablation

**Rationale:** Before trying new models or architectures, check whether current features carry signal at all. This is a cheap diagnostic that runs on existing code with minor parameter changes. If even the best feature/model combo barely beats random, the problem is in features or target, not in the model.

### Ablation Matrix

Run existing `benchmark_entry_path_fractal_level_direct_direction.py` with the following variants. All use Target D, RandomForest, threshold grid `[0.10, 0.20, 0.30, 0.40]`:

| Variant | input_family | k | Notes |
|---------|-------------|---|-------|
| E0a | nearest_k | 4 | Current baseline (already run) |
| E0b | nearest_k | 6 | More neighbors |
| E0c | nearest_k | 8 | Even more neighbors |
| E0d | nearest_k | 16 | Original plan k (389 features, overfitting risk) |
| E0e | nearest_k | 4, geometry_only | k=4 without up_*/dn_* fields |

### What E0e (geometry_only) Removes

From nearest_k4, remove all `nearest_XX_up_*` and `nearest_XX_dn_*` columns (up_3, dn_3, up_6, dn_6, up_12, dn_12, up_24, dn_24, up_48, dn_48 per slot = 10 columns per slot × 4 slots = 40 columns). Keeps model inputs: atr, fractal0_direction, fractal0_price_rank, fractals_above/below_count, nearest_XX_valid, raw_distance_atr, abs_distance_atr, direction, front, back, strong, break, reverse, power, count, impulse, fractal_atr. `source_index` may remain in diagnostic output but must not be included in model input.

### Diagnostic Questions E0 Answers

1. Does increasing k (4→6→8→16) improve PF or just increase overfitting?
2. Do up/dn fields inside fractals help or hurt? (E0e vs E0a)
3. Is the signal in features at all, or is it all in `fractal0_direction`? (Feature importance already shows `fractal0_direction` = 17.3% for Target A — does geometry_only match this?)

### Steps

- [ ] **E0-S1: Add `--k` and `--geometry-only` arguments to benchmark CLI**

Modify `ML/benchmark_entry_path_fractal_level_direct_direction.py`:
- Add `--k` argument (default: 4, choices: [4, 6, 8, 16])
- Add `--geometry-only` flag (default: False, removes up_*/dn_* from features)
- Both affect `build_fractal_level_features` call and output directory

- [ ] **E0-S2: Write tests for k variants and geometry_only flag**

```python
def test_k4_produces_97_features():
    ...

def test_k6_produces_expected_feature_count():
    ...

def test_geometry_only_removes_updn_columns():
    # Verify no up_*/dn_* columns in output
    ...
```

- [ ] **E0-S3: Run ablation matrix**

```bash
.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage validation-matrix --k 6
.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage validation-matrix --k 8
.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage validation-matrix --k 16
.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage validation-matrix --k 4 --geometry-only
```

- [ ] **E0-S4: Analyze ablation results**

For each variant, record:
- Best standalone validation PF and sequential PF
- Feature count and overfitting risk
- BUY/SELL PF separately
- Top-5 feature importances

Decide whether to proceed to E1 or adjust feature selection.

---

## Experiment 1: Binary BUY-vs-REST and SELL-vs-REST Models

**Rationale:** 3-class SELL/SKIP/BUY barely separates direction from skip. Binary models focus on one direction at a time with better class balance (~30% positive vs ~70% negative instead of 23%/24%/53%).

### Hypothesis

Separate BUY-vs-REST and SELL-vs-REST classifiers produce clearer probability signals. A trade is taken only when the direction-specific model exceeds its threshold and the opposing model is below its threshold.

### Ambiguous Target Handling

For Target D, `buy_good & sell_good` rows (ambiguous) have ~0% rate, but the rule must be explicit:

- **Ambiguous rows remain positive for both models** during training. This preserves natural class distribution.
- In validation grid, compute and report `both_high_rate` = fraction of selected rows where P_buy >= threshold AND P_sell >= threshold.
- Compute and report `conflict_rate` = fraction of selected trade rows where both classifiers fire simultaneously.

### Files

- Create: `ML/benchmark_entry_path_binary_direction.py`
- Create: `tests/test_benchmark_entry_path_binary_direction.py`
- Create: `docs/ML/benchmark_entry_path_binary_direction.py.md`
- Output: `ML/reports/entry_path_v1_binary_direction/`

### Shared Inputs

- Train: `DATA/Nero_XAUUSD_train_labeled.csv`
- Validation: `DATA/Nero_XAUUSD_validation_labeled.csv`
- Test: `DATA/Nero_XAUUSD_test_labeled.csv`
- OHLC: `DATA/XAUUSD_H1_OHLC.csv`
- Old score predictions: `ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/`

### Model

```python
# Two independent binary classifiers
buy_model = HistGradientBoostingClassifier(
    max_iter=200, max_depth=5, min_samples_leaf=40,
    learning_rate=0.05, random_state=42,
)
sell_model = HistGradientBoostingClassifier(
    max_iter=200, max_depth=5, min_samples_leaf=40,
    learning_rate=0.05, random_state=42,
)
# Also RF variant for comparison:
# RandomForestClassifier(n_estimators=160, min_samples_leaf=20, class_weight="balanced_subsample")
```

### Target Construction (Target D only; reuse existing builder)

- BUY target: `build_target_d_masks(...)[0]` (buy_good boolean)
- SELL target: `build_target_d_masks(...)[1]` (sell_good boolean)
- SKIP for each side: complement of the positive class

### Signal Decision Rule

Two variants in the threshold grid:

**Variant A (simple threshold):**
```text
if P(BUY | buy_model) >= buy_threshold
   and not (P(SELL | sell_model) >= sell_threshold):
    signal = 1
elif P(SELL | sell_model) >= sell_threshold
   and not (P(BUY | buy_model) >= buy_threshold):
    signal = -1
else:
    signal = 0
```

**Variant B (margin rule):**
```text
if P(BUY | buy_model) >= buy_threshold
   and (P(BUY | buy_model) - P(SELL | sell_model)) >= margin:
    signal = 1
elif P(SELL | sell_model) >= sell_threshold
   and (P(SELL | sell_model) - P(BUY | buy_model)) >= margin:
    signal = -1
else:
    signal = 0
```

Threshold grid: `0.30, 0.40, 0.50, 0.60`
Margin grid: `0.00, 0.05, 0.10, 0.15`
(margin=0.00 is Variant A)

Early stop: if both model variants produce near-degenerate probabilities (for example, fewer than 100 selected validation trades at all thresholds/margins) or all standalone configs have validation PF < 1.0, stop E1 and record a negative result without running the full remaining diagnostic grid.

### Validation Grid Columns

`mode, target_family, target_params, input_family, model_type, buy_threshold, sell_threshold, margin, validation_trades, validation_pf, validation_sequential_pf, validation_sequential_trades, buy_trades, sell_trades, buy_pf, sell_pf, buy_win_rate, sell_win_rate, buy_mean_pnl_atr, sell_mean_pnl_atr, buy_sell_balance, one_sided_candidate, both_high_rate, conflict_rate, yearly_pf, negative_years, feature_count, features_per_validation_candidates, overfitting_risk`

### Old-Score Diagnostic

Same rule as current: `mode="old_score_diagnostic"`, cannot become winner.

### Winner Gate

- standalone mode
- validation trades >= 100
- validation PF >= 1.15
- validation sequential PF >= 1.1
- no obvious yearly instability
- overfitting_risk == False
- if one side has < 20% of selected trades: `one_sided_candidate=True`
- **No frozen test at this stage.** Only validation results are recorded for later comparison.

### Steps

- [ ] **E1-S1: Write failing tests for BUY-vs-REST and SELL-vs-REST target construction**

```python
def test_buy_target_matches_target_d_buy_side():
    # BUY target = first element of build_target_d_masks
    ...

def test_sell_target_matches_target_d_sell_side():
    # SELL target = second element of build_target_d_masks
    ...

def test_binary_signal_logic_simple_threshold():
    # Variant A: P_buy >= 0.5 and P_sell < 0.5 -> BUY
    ...

def test_binary_signal_logic_margin_rule():
    # Variant B: P_buy >= 0.5 and (P_buy - P_sell) >= 0.1 -> BUY
    ...

def test_binary_ambiguous_rows_remain_positive():
    # Rows where buy_good=True and sell_good=True are positive for both models
    ...
```

- [ ] **E1-S2: Implement binary direction benchmark runner**

Implement `ML/benchmark_entry_path_binary_direction.py` with:
- CLI `--stage` choices: `target-frequency`, `validation-matrix`
- Reuse `ML/fractal_level_feature_builder.py` for `nearest_k4` features
- Reuse `ML/entry_path_direct_direction_targets.py` for target D
- Reuse `ML/benchmark_entry_path_all_rows_ranking.run_sequential_all_rows`
- Two `HistGradientBoostingClassifier` models (plus RF variant)
- Threshold and margin grids as above
- Compute `both_high_rate` and `conflict_rate` in validation grid
- Winner selection same gates as current plan
- **No `frozen-test` stage.**

- [ ] **E1-S3: Run validation-matrix stage**

```bash
.venv/bin/python -m ML.benchmark_entry_path_binary_direction --stage target-frequency
.venv/bin/python -m ML.benchmark_entry_path_binary_direction --stage validation-matrix
```

- [ ] **E1-S4: Analyze results and record for comparison**

Record validation results. Do NOT run frozen test. Move to E2.

---

## Experiment 2: HistGradientBoosting for 3-Class Model

**Rationale:** RandomForest with flat feature importance may miss non-linear interactions. HistGradientBoosting often performs better on tabular data with limited features. This tests the same 3-class formulation with a stronger learner.

### Files

- Modify: `ML/benchmark_entry_path_fractal_level_direct_direction.py` (add `--model` argument)
- Modify: `tests/test_benchmark_entry_path_fractal_level_direct_direction.py`
- Output: `ML/reports/entry_path_v1_fractal_level_direct_direction_hgb/`

### Models

```python
# Primary: HistGradientBoostingClassifier
HistGradientBoostingClassifier(
    max_iter=300, max_depth=5, min_samples_leaf=40,
    learning_rate=0.05, random_state=42,
)

# Balanced classes via sample_weight:
from sklearn.utils.class_weight import compute_sample_weight
sample_weight = compute_sample_weight("balanced", y_train)
# Pass to .fit(X, y, sample_weight=sample_weight)

# Linear control: LogisticRegression (diagnostic only, cannot become winner)
LogisticRegression(max_iter=1000, C=1.0, solver="lbfgs", multi_class="multinomial")
```

**LR diagnostic purpose:** If LR achieves similar PF to RF/HGB, the signal is in simple linear combinations and complex models are unnecessary. If LR is much worse, non-linear interactions matter. LR rows are marked `mode=lr_standalone` in the validation grid and cannot become frozen winner.

### Feature Importance for HGB

`HistGradientBoostingClassifier` does not expose `.feature_importances_`. For HGB:

- Compute permutation importance on validation (top-20, one pass).
- If permutation importance is too slow (>5 minutes), write `feature_importance.csv` with `importance=0` and `method=not_available` and a note in `summary.json`.

### Steps

- [ ] **E2-S1: Add model variant to existing benchmark**

Add `--model` CLI argument to `benchmark_entry_path_fractal_level_direct_direction.py`:
- `rf` (default, current RandomForest) — existing behavior unchanged
- `hgb` — HistGradientBoostingClassifier with balanced sample_weight
- `lr` — LogisticRegression (diagnostic only)

When `--model hgb`:
- Use `HistGradientBoostingClassifier` with `sample_weight=compute_sample_weight("balanced", y_train)`
- Output to `ML/reports/entry_path_v1_fractal_level_direct_direction_hgb/`
- Same threshold grid, validation gates, feature set (nearest_k4, Target D only)

- [ ] **E2-S2: Write test for model variant**

```python
def test_hgb_model_produces_three_class_probabilities():
    # Verify HGB produces probabilities for -1, 0, 1
    ...

def test_hgb_uses_balanced_sample_weights():
    # Verify compute_sample_weight("balanced", y) is used
    ...
```

- [ ] **E2-S3: Run 3-class HGB validation**

```bash
.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage validation-matrix --model hgb
```

First pass uses Target D only. If HGB materially improves Target D versus the RF baseline (for example, standalone PF increases by at least 0.03 or crosses a gate boundary), repeat the same HGB validation for A and C before overall winner selection.

- [ ] **E2-S4: Record validation results and move to next experiment**

No frozen test. Compare against RF baseline from current results.

---

## Experiment 3: Zone Features (Input A)

**Rationale:** `nearest_k4` gives 97 features but misses the cluster structure of fractals around `fractal0.price`. Zone features aggregate fractal density, direction balance, and Up/Dn sums by price zone, providing a complementary view.

### Files

- Modify: `ML/fractal_level_feature_builder.py` (add `build_zone_features` and `input_family="zones"`)
- Modify: `ML/benchmark_entry_path_fractal_level_direct_direction.py` (add `--input-family zones` and `--input-family zones_plus_nearest_k4`)
- Modify/add tests
- Output directories: `ML/reports/entry_path_v1_fractal_level_zone/`, `ML/reports/entry_path_v1_fractal_level_zone_plus_k4/`

### Zone Definition

Price zones relative to `fractal0.price` in ATR units:

```text
zone_0:  0.00..0.25 ATR above
zone_1:  0.00..0.25 ATR below
zone_2:  0.25..0.50 ATR above
zone_3:  0.25..0.50 ATR below
zone_4:  0.50..1.00 ATR above
zone_5:  0.50..1.00 ATR below
zone_6:  1.00..2.00 ATR above
zone_7:  1.00..2.00 ATR below
zone_8:  2.00..4.00 ATR above
zone_9:  2.00..4.00 ATR below
zone_10: >4.00 ATR (above and below combined)
```

### Zone Aggregates per Zone

For each zone:

```text
count: number of fractals in zone
direction_sum: sum of direction field (net direction balance)
direction_abs_sum: sum of |direction|
strong_count: number of strong fractals
break_count: number of fractured fractals
power_sum: sum of power
power_max: max power
impulse_sum: sum of impulse
impulse_max: max impulse
up_24_sum: sum of up_24 for fractal1..fractal99 in zone (live-safe)
dn_24_sum: sum of dn_24 for fractal1..fractal99 in zone (live-safe)
```

Plus global features:

```text
fractals_above_count
fractals_below_count
fractal0_price_rank
total_count
closest_above_distance_atr
closest_below_distance_atr
```

### Estimated Feature Count

~11 zones × 12 aggregates = ~132 features + ~6 global = ~138 features for `zones`.
`zones_plus_nearest_k4` = ~138 + ~97 = ~235 features.

### Overfitting Risk Gate

Before running validation for any config, check:

```python
if feature_count / estimated_validation_candidates >= 0.10:
    mark overfitting_risk = True
    if feature_count / estimated_validation_candidates >= 0.20:
        skip config entirely  # only when the estimate is clearly reliable
```

For `zones` (~138 features): need at least 1380 candidates. For `zones_plus_nearest_k4` (~235 features): need at least 2350 candidates.

`estimated_validation_candidates` is only a pre-training filter. Use it conservatively: skip only when the candidate universe is clearly too small from target-frequency results or prior threshold behavior. If the estimate is uncertain, run validation and let the actual `feature_count / validation_candidates` winner gate reject overfit configs.

### Steps

- [ ] **E3-S1: Write failing tests for zone features**

```python
def test_zone_features_count_fractals_in_zones():
    # Verify zone_0 count matches fractals within 0.25 ATR above
    ...

def test_zone_features_exclude_fractal0_updn():
    # Verify fractal0 up/dn are not used as zone features
    ...

def test_zone_features_feature_count():
    # Verify total feature count matches expected ~138
    ...
```

- [ ] **E3-S2: Implement build_zone_features**

Add to `ML/fractal_level_feature_builder.py`:
- `build_zone_features(frame, atr_zones=ATR_ZONE_BOUNDS)` returning DataFrame of zone features
- Update `build_fractal_level_features` to support `input_family="zones"` and `input_family="zones_plus_nearest_k4"`
- Update feature contract accordingly

- [ ] **E3-S3: Add zone input family to benchmark**

Modify `benchmark_entry_path_fractal_level_direct_direction.py`:
- `--input-family` choices: `nearest_k4`, `zones`, `zones_plus_nearest_k4`
- Default remains `nearest_k4`
- Add overfitting risk early check before training

- [ ] **E3-S4: Run zone validation (3-class Target D with RF)**

```bash
.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction \
  --stage validation-matrix --input-family zones
```

Then, if overfitting risk gate passes:

```bash
.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction \
  --stage validation-matrix --input-family zones_plus_nearest_k4
```

- [ ] **E3-S5: Record validation results and move to next experiment**

No frozen test. Compare against nearest_k4 baseline.

---

## Experiment 4: Target Parameter Grid

**Rationale:** Current Target D (`trail_n=2.0, profit_z=1.0, horizon=24`) yields 46.7% positive rate, making SKIP too easy to predict. A/C now also pass frequency gates after the normalization fix. This experiment checks whether tighter or softer target thresholds produce a learning signal better aligned with the 24-bar trading validation metric.

### Parameter Grid

```text
# Target D (existing and tighter)
D0: trail_n=2.0, profit_z=1.0, horizon=24  (current baseline)
D1: trail_n=1.5, profit_z=1.5, horizon=24  (tighter stop, larger profit)
D2: trail_n=2.0, profit_z=2.0, horizon=24  (same stop, larger profit)
D3: trail_n=1.5, profit_z=1.0, horizon=48  (tighter stop, longer horizon)

# Target A (now passes frequency gate)
A0: stop_n=0.2, take_y=0.3  (current)
A1: stop_n=0.15, take_y=0.25  (softer)
A2: stop_n=0.25, take_y=0.35  (tighter adverse)

# Target C (now passes frequency gate)
C0: take_x=0.5, adverse_y=0.3  (current)
C1: take_x=0.4, adverse_y=0.25  (softer take)
C2: take_x=0.6, adverse_y=0.35  (tighter adverse)
```

### Sparsity Gates

Before running validation for each D variant:

- validation BUY positives >= 100
- validation SELL positives >= 100
- validation major-year min BUY positives >= 10
- validation major-year min SELL positives >= 10
- ambiguous_rate <= 0.20

If any gate fails, skip that variant entirely and report in target_frequency output.

### Files

- Modify: `ML/benchmark_entry_path_fractal_level_direct_direction.py` (add `--target-d-params` or multi-target support)
- Modify: `ML/entry_path_direct_direction_targets.py` (parameterize `summarize_target_frequencies`)

### Steps

- [ ] **E4-S1: Run target-frequency for tighter D parameters**

Add D1, D2, D3 parameter sets to `summarize_target_frequencies`:

```bash
.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage target-frequency
```

Check sparsity gates for each variant.

- [ ] **E4-S2: If gates pass, run validation-matrix for each passing D variant**

Using best input family from previous experiments (default: nearest_k4).

```bash
.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage validation-matrix --target-d-params D1,...
```

- [ ] **E4-S3: Record validation results**

No frozen test.

---

## Experiment 5: Score-Filtered Direction (Direction Resolver) — Hybrid/Diagnostic

**Rationale:** The old score gate (`pred_ret_24_dir_atr >= threshold`) already identifies rows with strong directional tendency. The new model's job is only to decide **which direction** for those rows, not whether to trade. This is a fundamentally different task: binary direction on a pre-filtered universe.

**Important classification:** This is a **hybrid/diagnostic architecture**, not a standalone fractal-level solution. It depends on the existing score model for candidate selection. The score model itself uses offline-trained `pred_ret_24_dir_atr` which is live-safe for runtime (computed from current row features), but the candidate universe is fundamentally different from a standalone fractal-level gate.

**Candidate gate:** Only `score >= old_score_threshold`. `source["signal"] != 0` is used exclusively as a diagnostic baseline for comparison, never as a production gate.

### Architecture

Stage 1: Use `score >= old_score_threshold` as candidate gate (same universe as production entry_path_v1_live_safe).

Stage 2: On the ~500 candidate rows, train a binary BUY-vs-SELL classifier to choose direction. This replaces the hardcoded `fractal0.direction`.

### Diagnostic Baseline

For comparison, also compute metrics using `fractal0.direction` as the direction source on the same candidate universe. This is not a separate experiment; it is a baseline within E5.

### Files

- Create: `ML/benchmark_entry_path_score_direction.py`
- Create: `tests/test_benchmark_entry_path_score_direction.py`
- Output: `ML/reports/entry_path_v1_score_direction/`

### Model

```python
HistGradientBoostingClassifier(
    max_iter=200, max_depth=5, min_samples_leaf=20,
    learning_rate=0.05, random_state=42,
)
# Binary: BUY(1) vs SELL(-1), trained only on rows where target != SKIP
# sample_weight=compute_sample_weight("balanced", y_non_skip)
```

### Evaluation

On validation, restrict to rows where `score >= old_score_threshold`. Compute:
- direction accuracy (model vs target)
- BUY PF, SELL PF, combined PF
- sequential PF with 24-bar hold
- Compare against `fractal0.direction` baseline on the same universe
- Compare against standalone fractal-level model results from E1–E4

### Steps

- [ ] **E5-S1: Write failing tests**

```python
def test_score_direction_filters_to_candidate_universe():
    # Only rows with score >= threshold are evaluated
    ...

def test_score_direction_uses_only_score_gate_not_signal():
    # Verify source["signal"] is not used as candidate gate
    # source["signal"] may appear only in diagnostic baseline comparison
    ...
```

- [ ] **E5-S2: Implement score-direction benchmark**

- [ ] **E5-S3: Run validation**

```bash
.venv/bin/python -m ML.benchmark_entry_path_score_direction --stage validation-matrix
```

- [ ] **E5-S4: Compare direction accuracy against fractal0.direction baseline**

No frozen test at this stage.

---

## Experiment 6: Sequence Features from Fractal Order

**Rationale:** `nearest_k` flattens fractal structure by proximity, losing temporal ordering. Adding features that capture the *sequence* of fractal events (time gaps, directional alternation, acceleration) may provide signal that spatial proximity alone misses.

**This is a conditional research experiment** — only pursued if E1/E2/E3 show direction signal (PF > 1.05) but insufficient PF (< 1.15).

### Potential Features

```text
fractal_time_gap_mean: average time between consecutive fractals
fractal_time_gap_std: std of time between consecutive fractals
direction_changes: number of direction changes in nearest K
direction_run_length: longest run of same direction in nearest K
acceleration: price change between consecutive fractals (velocity)
acceleration_change: second derivative of price movement
price_reversal_count: number of reversals (direction change + price level)
zone_consolidation: fraction of nearest fractals within 0.5 ATR
```

### Steps

- [ ] **E6-S1: Implement only if E1/E2/E3 show PF > 1.05 but < 1.15**

Only execute if direction signal exists but needs improvement. Otherwise skip entirely.

---

## Overall Frozen Test

After ALL experiments E1–E5 complete:

1. Compare all validation results across experiments.
2. Write aggregate comparison artifacts:
   - `ML/reports/entry_path_v1_direct_direction_improvement/validation_leaderboard.csv`
   - `ML/reports/entry_path_v1_direct_direction_improvement/summary.json`
3. Select the single best validation winner (highest sequential PF among configs passing all gates).
4. If no config passes all gates: report aggregate results, close as weak research, update CHANGELOG.md and CONTEXT_HANDOFF.md.
5. If a winner exists: freeze its configuration and run **one** frozen test.

```bash
# Example: if E1 binary HGB with margin=0.10 wins
.venv/bin/python -m ML.benchmark_entry_path_binary_direction --stage frozen-test \
  --config "<frozen_config>"
```

6. Compare frozen test against baselines:

| Baseline | Test PF | Sequential PF | Trades / sequential trades |
|---|---:|---:|---:|
| all-rows ranking | 0.9134 | 0.5908 | 329 / 133 |
| causal surrogate | 1.1537 | 1.4111 | 36 / 31 |
| direct bar model | 1.1141 | 1.1334 | 1277 / 274 |
| fractal level direct direction (D nearest_k4) | computed | computed | computed |
| **new winner** | computed | computed | computed |

---

## Stop Conditions

Apply per experiment:

1. If validation PF < 1.0 for all thresholds: stop the experiment, report negative result.
2. If best standalone validation PF < 1.15 and sequential PF < 1.1: no winner for that experiment, report weak result and move to next.
3. If `one_sided_candidate=True`: report as one-sided, not as general SELL/SKIP/BUY success.
4. If overall frozen test PF is worse than direct-bar baseline (PF 1.11, seq PF 1.13, 1277/274 trades): close as weak research result.
5. If overall frozen test passes all gates and PF > direct-bar baseline: write follow-up plan for MT4 parity and confidence intervals.

---

## Documentation Updates

- **After adding a new module** (new .py file): update `MODULE_INDEX.md` and `ML/README.md`.
- **After each experiment**: report changed files and validation results, but do NOT update `CHANGELOG.md` or `CONTEXT_HANDOFF.md` yet.
- **After each experiment**: append its best validation rows to the aggregate leaderboard inputs, so overall winner selection is reproducible rather than manual.
- **After all experiments complete or at stop point**: update `CHANGELOG.md` and `CONTEXT_HANDOFF.md`.
- **After frozen test** (if winner found): write `docs/reports/2026-05-1X-entry-path-<experiment>.md` with full results.

---

## Experiment Execution Order

```text
E0 (ablation) ─→ E1 (binary) ─→ E2 (HGB + LR) ─→ E3 (zones) ─→ E4 (target grid) ─→ E5 (score dir)
                                                                                           │
                                                                                E6 only if E0-E3 show PF 1.05-1.15
```

**Recommended execution order:** E0 → E1 → E2 → E3 → E4 → E5 → E6 (conditional)

- **E0 (ablation)** is the cheapest diagnostic: clarify whether features carry signal before investing in new models
- E1 (binary) addresses the core problem (3-class too hard)
- E2 (HGB) tests model capacity; LR shows whether signal is linearly separable
- E3 (zones) adds complementary feature engineering
- E4 (target grid) adjusts the learning signal for all three target families (A/C/D with parameter grids)
- E5 (score direction) tests the most practical hybrid architecture
- E6 (sequence) is speculative research, conditional on E0-E3
- **One frozen test** after all experiments, for the single best validation winner
