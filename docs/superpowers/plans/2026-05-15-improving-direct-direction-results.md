# Improving Direct Direction Results: Iterative Improvement Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Iteratively improve the fractal-level SELL/SKIP/BUY direct-direction model, which currently fails validation gates (best standalone PF=1.11 < 1.15 gate), by testing binary models, alternative ML algorithms, zone features, tighter targets, and score-filtered direction.

**Architecture:** A sequence of independent experiments sharing existing infrastructure (feature builder, target builder, benchmark runner). Each experiment produces its own output directory under `ML/reports/`. Experiments run one at a time; each freezes its validation result before deciding whether to continue or stop.

**Tech Stack:** Python 3.12, pandas, numpy, scikit-learn (RandomForestClassifier, HistGradientBoostingClassifier), pytest, existing `processing.label_signals`, existing entry-path benchmark helpers.

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
- Create a new branch from current `entry-path-all-rows-spec` or current branch.
- Use `./.venv/bin/python`.
- Each experiment uses its own output directory: `ML/reports/entry_path_v1_<experiment_name>/`.
- Do not modify existing working code without tests.
- Stop an experiment early if validation PF < 1.0 for all thresholds.
- All trading evaluation: next-bar open entry, 24-bar close exit, sequential hold, no spread/commission/slippage.
- Test runs only once after validation winner is frozen.
- Do not run test before validation winner is frozen.

---

## Experiment 1: Binary BUY-vs-REST and SELL-vs-REST Models

**Rationale:** 3-class SELL/SKIP/BUY barely separates direction from skip. Binary models focus on one direction at a time with better class balance (30% positive vs 70% negative instead of 23%/24%/53%).

### Hypothesis

Separate BUY-vs-REST and SELL-vs-REST classifiers produce clearer probability signals. A trade is taken only when the direction-specific model exceeds its threshold and the opposing model is below its threshold.

### Files

- Create: `ML/benchmark_entry_path_binary_direction.py`
- Create: `tests/test_benchmark_entry_path_binary_direction.py`
- Create: `docs/ML/benchmark_entry_path_binary_direction.py.md`
- Output: `ML/reports/entry_path_v1_binary_direction/`

### Shared Inputs (same as current)

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
```

### Target Construction (Target D only; reuse existing builder)

- BUY target: `build_target_d_masks(...)[0]` (buy_good boolean)
- SELL target: `build_target_d_masks(...)[1]` (sell_good boolean)
- SKIP for each side: complement of the positive class

### Signal Decision Rule

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

Threshold grid: `0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60`

### Validation Grid Columns

Same as current plan: `mode, target_family, target_params, input_family, buy_threshold, sell_threshold, validation_trades, validation_pf, validation_sequential_pf, validation_sequential_trades, buy_trades, sell_trades, buy_pf, sell_pf, buy_win_rate, sell_win_rate, buy_mean_pnl_atr, sell_mean_pnl_atr, buy_sell_balance, one_sided_candidate, yearly_pf, negative_years, feature_count, features_per_validation_candidates, overfitting_risk`

### Old-Score Diagnostic

Same rule as current: `mode="old_score_diagnostic"`, cannot become winner.

### Winner Gate

Same as current plan:
- standalone mode
- validation trades >= 100
- validation PF >= 1.15
- validation sequential PF >= 1.1
- no obvious yearly instability
- overfitting_risk == False
- if one side has < 20% of selected trades: `one_sided_candidate=True`

### Steps

- [ ] **E1-S1: Write failing tests for BUY-vs-REST and SELL-vs-REST target construction**

```python
def test_buy_target_matches_target_d_buy_side():
    # BUY target = first element of build_target_d_masks
    ...

def test_sell_target_matches_target_d_sell_side():
    # SELL target = second element of build_target_d_masks
    ...

def test_binary_signal_logic():
    # If P_buy >= 0.5 and P_sell < 0.3 -> BUY
    # If P_sell >= 0.5 and P_buy < 0.3 -> SELL
    # Otherwise SKIP
    ...
```

- [ ] **E1-S2: Implement binary direction benchmark runner**

Implement `ML/benchmark_entry_path_binary_direction.py` with:
- CLI `--stage` choices: `target-frequency`, `validation-matrix`, `frozen-test`
- Reuse `ML/fractal_level_feature_builder.py` for `nearest_k4` features
- Reuse `ML/entry_path_direct_direction_targets.py` for target D
- Reuse `ML/benchmark_entry_path_all_rows_ranking.run_sequential_all_rows`
- Two `HistGradientBoostingClassifier` models
- Threshold grid as above
- Winner selection same gates as current plan
- Also include a `RandomForestClassifier(n_estimators=160, min_samples_leaf=20, class_weight="balanced_subsample")` variant as `model=rf` for comparison

- [ ] **E1-S3: Run validation-matrix stage**

```bash
.venv/bin/python -m ML.benchmark_entry_path_binary_direction --stage target-frequency
.venv/bin/python -m ML.benchmark_entry_path_binary_direction --stage validation-matrix
```

- [ ] **E1-S4: Analyze results**

If no standalone winner passes gates, report and decide whether to continue to Experiment 2.

- [ ] **E1-S5: Optional frozen-test if winner found**

```bash
.venv/bin/python -m ML.benchmark_entry_path_binary_direction --stage frozen-test
```

---

## Experiment 2: HistGradientBoosting for 3-Class Model

**Rationale:** RandomForest with flat feature importance may miss non-linear interactions. HistGradientBoosting often performs better on tabular data with limited features. This tests the same 3-class formulation with a stronger learner.

### Files

- Modify: `ML/benchmark_entry_path_fractal_level_direct_direction.py` (add `--model` argument)
- Modify: `tests/test_benchmark_entry_path_fractal_level_direct_direction.py`
- Output: `ML/reports/entry_path_v1_fractal_level_direct_direction_hgb/`

### Model

```python
HistGradientBoostingClassifier(
    max_iter=300, max_depth=5, min_samples_leaf=40,
    learning_rate=0.05, random_state=42,
)
```

Also test with `class_weight="balanced"` if supported by HGB (via `sample_weight`).

### Steps

- [ ] **E2-S1: Add model variant to existing benchmark**

Add `--model` CLI argument to `benchmark_entry_path_fractal_level_direct_direction.py`:
- `rf` (default, current RandomForest) - existing behavior unchanged
- `hgb` - HistGradientBoostingClassifier

When `--model hgb`:
- Use `HistGradientBoostingClassifier`
- Output to `ML/reports/entry_path_v1_fractal_level_direct_direction_hgb/`
- Same threshold grid, validation gates, feature set (nearest_k4)

- [ ] **E2-S2: Write test for model variant**

```python
def test_hgb_model_produces_three_class_probabilities():
    # Verify HGB produces probabilities for -1, 0, 1
    ...
```

- [ ] **E2-S3: Run 3-class HGB validation**

```bash
.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage validation-matrix --model hgb
```

Using Target D only (since A and C are available but D was the primary focus).

- [ ] **E2-S4: Analyze results**

Compare HGB 3-class results against RF 3-class baseline. If HGB produces a standalone winner, continue to frozen test.

- [ ] **E2-S5: Optional frozen-test if winner found**

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
zone_0: 0.00..0.25 ATR above
zone_1: 0.00..0.25 ATR below
zone_2: 0.25..0.50 ATR above
zone_3: 0.25..0.50 ATR below
zone_4: 0.50..1.00 ATR above
zone_5: 0.50..1.00 ATR below
zone_6: 1.00..2.00 ATR above
zone_7: 1.00..2.00 ATR below
zone_8: 2.00..4.00 ATR above
zone_9: 2.00..4.00 ATR below
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

~11 zones x 12 aggregates = ~132 features + ~6 global = ~138 features for `zones`.
`zones_plus_nearest_k4` = ~138 + ~97 = ~235 features.

### Steps

- [ ] **E3-S1: Write failing tests for zone features**

```python
def test_zone_features_count_fractals_in_zones():
    # Verify zone_0 count matches fractals within 0.25 ATR above
    ...

def test_zone_features_exclude_fractal0_updn():
    # Verify fractal0 up/dn are not used as zone features
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

- [ ] **E3-S4: Run zone validation (3-class Target D with RF)**

```bash
.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction \
  --stage validation-matrix --input-family zones
```

```bash
.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction \
  --stage validation-matrix --input-family zones_plus_nearest_k4
```

- [ ] **E3-S5: Analyze results and decide whether to run frozen test**

---

## Experiment 4: Tighter Target D Parameters

**Rationale:** Current Target D (`trail_n=2.0, profit_z=1.0, horizon=24`) yields 46.7% positive rate, making SKIP too easy to predict. Tighter targets produce fewer but potentially higher-quality positives.

### Parameter Grid

```text
D1: trail_n=1.5, profit_z=1.5, horizon=24  (tighter stop, larger profit)
D2: trail_n=2.0, profit_z=2.0, horizon=24  (same stop, larger profit)
D3: trail_n=1.5, profit_z=1.0, horizon=48  (tighter stop, longer horizon)
```

### Files

- Modify: `ML/benchmark_entry_path_fractal_level_direct_direction.py` (add `--target-d-params` or multi-target support)
- Modify: `ML/entry_path_direct_direction_targets.py` (parameterize `summarize_target_frequencies`)

### Steps

- [ ] **E4-S1: Run target-frequency for tighter D parameters**

```bash
# Add D1, D2, D3 parameter sets to summarize_target_frequencies
.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage target-frequency
```

Gate: at least 100 validation BUY + 100 validation SELL positives for each new D variant.

- [ ] **E4-S2: If gate passes, run validation-matrix for each passing D variant**

Using best input family from previous experiments (default: nearest_k4).

- [ ] **E4-S3: Analyze results**

---

## Experiment 5: Score-Filtered Direction (Direction Resolver)

**Rationale:** The old score gate (`pred_ret_24_dir_atr >= threshold`) already identifies rows with strong directional tendency. The new model's job is only to decide **which direction** for those rows, not whether to trade. This is a fundamentally different task: binary direction on a pre-filtered universe.

### Architecture

Stage 1: Use existing `signal != 0` or `score >= old_threshold` as candidate gate (same universe as production entry_path_v1_live_safe).

Stage 2: On the ~500 candidate rows, train a binary BUY-vs-SELL classifier to choose direction. This replaces the hardcoded `fractal0.direction`.

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
```

### Evaluation

On validation, restrict to rows where `score >= old_score_threshold`. Compute:
- direction accuracy
- BUY PF, SELL PF, combined PF
- sequential PF with 24-bar hold
- Compare against `fractal0.direction` baseline on the same universe

### Steps

- [ ] **E5-S1: Write failing tests**

```python
def test_score_direction_filters_to_candidate_universe():
    # Only rows with score >= threshold are evaluated
    ...

def test_binary_direction_beats_fractal0_direction():
    # On candidate universe, model direction accuracy > fractal0.direction accuracy
    ...
```

- [ ] **E5-S2: Implement score-direction benchmark**

- [ ] **E5-S3: Run validation**

```bash
.venv/bin/python -m ML.benchmark_entry_path_score_direction --stage validation-matrix
```

- [ ] **E5-S4: Compare direction accuracy against fractal0.direction baseline**

- [ ] **E5-S5: If winner, run frozen test**

---

## Experiment 6: Sequence Features from Fractal Order

**Rationale:** `nearest_k` flattens fractal structure by proximity, losing temporal ordering. Adding features that capture the *sequence* of fractal events (time gaps, directional alternation, acceleration) may provide signal that spatial proximity alone misses.

**This is a research experiment** - higher risk, only pursued if Experiments 1-3 show some directional signal but insufficient PF.

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

- [ ] **E6-S1: Research experiment - implement only if Experiments 1-3 show promise but insufficient**

Only execute if direction signal exists (PF > 1.05 for at least one config) but needs improvement.

---

## Stop Conditions

Apply per experiment:

1. If validation PF < 1.0 for all thresholds: stop the experiment, report negative result.
2. If best standalone validation PF < 1.15 and sequential PF < 1.1: no winner, report weak result and move to next experiment.
3. If `one_sided_candidate=True`: report as one-sided, not as general SELL/SKIP/BUY success.
4. If frozen test PF is worse than direct-bar baseline (PF 1.11, seq PF 1.13, 1277/274 trades): close as weak research result for that experiment.
5. If frozen test passes all gates and PF > direct-bar baseline: write follow-up plan for MT4 parity and confidence intervals.

---

## Expected Artifacts Per Experiment

Each experiment produces:

- `ML/reports/entry_path_v1_<experiment>/target_frequency.csv` (if applicable)
- `ML/reports/entry_path_v1_<experiment>/validation_grid.csv`
- `ML/reports/entry_path_v1_<experiment>/feature_importance.csv`
- `ML/reports/entry_path_v1_<experiment>/score_distribution.csv` (if using old score)
- `ML/reports/entry_path_v1_<experiment>/summary.json`
- `ML/reports/entry_path_v1_<experiment>/summary.md` (if frozen test)

After each experiment, update:

- `MODULE_INDEX.md`
- `ML/README.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`

---

## Experiment Priority and Dependencies

```text
Experiment 1 (binary models) ────────────────────────────┐
Experiment 2 (HGB 3-class) ──────────────────────────────┤
Experiment 3 (zone features) ────────────────────────────┤─→ E6 only if E1-E3 show promise
Experiment 4 (tighter Target D) ─────────────────────────┤
Experiment 5 (score-filtered direction) ─────────────────┘
```

Experiments 1-5 are independent and can run in any order. Experiment 6 is conditional on results from 1-3.

**Recommended order:** E1 → E2 → E5 → E3 → E4 → E6

- E1 (binary) addresses the core problem (3-class too hard)
- E2 (HGB) is quick to add and tests model capacity
- E5 (score direction) tests the most practical architecture
- E3 (zones) adds feature engineering
- E4 (tighter targets) adjusts the learning signal
- E6 (sequence) is speculative research