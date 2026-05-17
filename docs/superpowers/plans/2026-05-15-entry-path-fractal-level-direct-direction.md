# Entry Path Fractal Level Direct Direction Implementation Plan

> **For agentic workers:** If the environment and user instructions allow subagents, use superpowers:subagent-driven-development. Otherwise use superpowers:executing-plans in the current session. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a live-safe fractal-level model that chooses `SELL / SKIP / BUY` from the current fractal row without using `fractal0.direction` as fixed trade direction.

**Architecture:** This is a fork after the failed direction gate from `2026-05-15-entry-path-all-rows-level-signal.md`. It reuses the live-safe feature audit and fractal-level feature builder, but replaces fixed-direction targets with BUY-vs-SELL target construction and a three-class model. Validation chooses one standalone winner; test runs once after the winner is frozen.

**Tech Stack:** Python 3.12, pandas, numpy, scikit-learn, pytest, existing `processing.label_signals`, existing entry-path benchmark helpers.

---

## Execution Rules

- Do not use a git worktree; project rules forbid it.
- Use current feature branch or create a new branch from `entry-path-all-rows-spec`.
- Use `./.venv/bin/python`.
- Do not use `source["signal"]` as a model input or target source.
- Do not use `fractal0.direction` as fixed trade direction.
- `fractal0.direction` may be used only as one live-safe input feature.
- Old score mode is diagnostic only.
- Trading validation/test uses next-bar open entry, 24-bar close exit, no spread/commission/slippage, and sequential hold of 24 bars unless a step explicitly says diagnostic trailing mode.
- Top-level `up_*` / `dn_*` columns are target-only fields. Feature builder must not read them.
- Do not run test before validation winner is frozen.
- Checkpoint commits are optional. If commits are not approved in the execution session, report changed files and test status instead.

## Default Inputs

The runner must expose CLI arguments for these paths and use these defaults:

- Train source CSV: `DATA/Nero_XAUUSD_train_labeled.csv`
- Validation source CSV: `DATA/Nero_XAUUSD_validation_labeled.csv`
- Test source CSV: `DATA/Nero_XAUUSD_test_labeled.csv`
- Validation old-score predictions: `ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/validation_predictions.csv`
- Test old-score predictions: `ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/test_predictions.csv`
- OHLC path: `DATA/XAUUSD_H1_OHLC.csv`
- Output dir: `ML/reports/entry_path_v1_fractal_level_direct_direction`

## Read First

- `docs/superpowers/specs/2026-05-15-entry-path-fractal-level-direct-direction-design.md`
- `docs/superpowers/plans/2026-05-15-entry-path-all-rows-level-signal.md`
- `docs/reports/2026-05-14-entry-path-direct-bar-model.md`
- `docs/DATA_FLOW.md`
- `processing/label_signals.py`
- `ML/benchmark_entry_path_direct_bar_model.py`
- `ML/benchmark_entry_path_all_rows_ranking.py`

## File Structure

### Create

- `ML/fractal_level_feature_builder.py`
  - Reuse or finish the feature builder from the failed-gate branch if it already exists.
  - Parse `fractal0..fractal99`.
  - Build `nearest_k16`, `zones`, and mixed features.
  - Write `feature_contract.json`.

- `ML/entry_path_direct_direction_targets.py`
  - Build BUY future outcomes.
  - Build SELL future outcomes.
  - Build target families A/C/D for each side.
  - Convert BUY/SELL target pairs into `SELL / SKIP / BUY`.

- `ML/benchmark_entry_path_fractal_level_direct_direction.py`
  - Run live-safe audit.
  - Run target frequency checks.
  - Train three-class classifiers.
  - Select standalone validation winner.
  - Run old-score diagnostic separately.
  - Run frozen test once.
  - Write reports.

- `tests/test_fractal_level_feature_builder.py`
- `tests/test_entry_path_direct_direction_targets.py`
- `tests/test_benchmark_entry_path_fractal_level_direct_direction.py`
- `docs/ML/fractal_level_feature_builder.py.md`
- `docs/ML/entry_path_direct_direction_targets.py.md`
- `docs/ML/benchmark_entry_path_fractal_level_direct_direction.py.md`
- `docs/reports/2026-05-15-entry-path-fractal-level-direct-direction.md`

### Modify

- `ML/README.md`
- `MODULE_INDEX.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/REPO_integrity.md`

### Output Artifacts

- `ML/reports/entry_path_v1_fractal_level_direct_direction/feature_audit.json`
- `ML/reports/entry_path_v1_fractal_level_direct_direction/feature_contract.json`
- `ML/reports/entry_path_v1_fractal_level_direct_direction/target_frequency.csv`
- `ML/reports/entry_path_v1_fractal_level_direct_direction/validation_grid.csv`
- `ML/reports/entry_path_v1_fractal_level_direct_direction/feature_importance.csv`
- `ML/reports/entry_path_v1_fractal_level_direct_direction/score_distribution.csv`
- `ML/reports/entry_path_v1_fractal_level_direct_direction/summary.json`
- `ML/reports/entry_path_v1_fractal_level_direct_direction/summary.md`
- `ML/reports/entry_path_v1_fractal_level_direct_direction/test_selected_rows.csv`

---

## Task A: Live-Safe Feature Audit

**Purpose:** Reuse the safe parts of the previous plan and prove that model inputs come only from the current row.

**Files:**
- Create/Modify: `ML/fractal_level_feature_builder.py`
- Test: `tests/test_fractal_level_feature_builder.py`
- Output: `feature_audit.json`, `feature_contract.json`

- [ ] **Step A1: Write failing tests for time parsing**

```python
def test_parse_row_time_and_fractal_time_use_same_unit():
    row_time = parse_row_time("2024.01.01 10:00")
    fractal_time = parse_fractal_time("2024.01.01 09:00")

    assert fractal_time <= row_time
```

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal_level_feature_builder.py::test_parse_row_time_and_fractal_time_use_same_unit -q
```

Expected: FAIL until helpers exist.

- [ ] **Step A2: Implement parse and audit helpers**

Implement:

```python
def parse_fractal(value: object) -> dict[str, float | int | None]:
    ...

def parse_row_time(value: object) -> pd.Timestamp | None:
    ...

def parse_fractal_time(value: object) -> pd.Timestamp | None:
    ...

def audit_fractal_rows(frame: pd.DataFrame) -> dict[str, int | float]:
    ...
```

Rules:

- compare row/fractal time only after converting both to the same timestamp type;
- unknown numeric fractal time format is reported as `unknown_time_format_rows`;
- audit reads only `time`, `ATR`, and `fractal0..fractal99`;
- `source["signal"]`, `predict`, `ret_*`, `fav_*`, `adv_*` are ignored.

- [ ] **Step A3: Write feature contract**

Write `feature_contract.json` with each feature:

- `name`;
- `source_column`;
- `source_type`;
- `available_at`;
- `live_safe`;
- `normalization`;
- `model_input`.

Required `available_at` values:

- `current_row`;
- `historical_fractal_state`;
- `target_only`;
- `diagnostic_only`.

`source["signal"]` must be `diagnostic_only`, `model_input=false`.
Top-level `up_*`, `dn_*`, generated `fav_*`, `adv_*`, and trailing outcomes must be `target_only`, `model_input=false`.

- [ ] **Step A4: Add CLI stage**

Run:

```bash
./.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage feature-audit
```

Expected outputs:

- `feature_audit.json`;
- `feature_contract.json`.

- [ ] **Step A5: Checkpoint Task A**

Commit only if checkpoint commits are approved. Otherwise report changed files and test status.

---

## Task B: BUY/SELL Target Builder

**Purpose:** Build targets without fixed direction from `fractal0.direction`.

**Files:**
- Create: `ML/entry_path_direct_direction_targets.py`
- Test: `tests/test_entry_path_direct_direction_targets.py`
- Output: `target_frequency.csv`

- [ ] **Step B1: Write failing tests for BUY/SELL future moves**

```python
def test_buy_and_sell_fav_adv_are_built_independently():
    frame = pd.DataFrame({"ATR": [2.0], "up_6": [6.0], "dn_6": [2.0]})

    moves = build_buy_sell_fav_adv(frame, horizons=(6,))

    assert moves.loc[0, "buy_fav_6_atr"] == 3.0
    assert moves.loc[0, "buy_adv_6_atr"] == 1.0
    assert moves.loc[0, "sell_fav_6_atr"] == 1.0
    assert moves.loc[0, "sell_adv_6_atr"] == 3.0
```

- [ ] **Step B2: Implement BUY/SELL future moves**

Implement:

```python
def build_buy_sell_fav_adv(
    source: pd.DataFrame,
    horizons: tuple[int, ...] = (3, 6, 12, 24, 48),
) -> pd.DataFrame:
    ...
```

Rules:

- BUY favorable = `up_H / ATR`;
- BUY adverse = `dn_H / ATR`;
- SELL favorable = `dn_H / ATR`;
- SELL adverse = `up_H / ATR`;
- do not read `source["signal"]`.

- [ ] **Step B3: Write failing tests for class conversion**

```python
def test_target_pair_to_class_skips_ambiguous_rows():
    out = target_pair_to_class(
        buy_good=pd.Series([True, False, True, False]),
        sell_good=pd.Series([False, True, True, False]),
    )

    assert out.tolist() == [1, -1, 0, 0]
```

- [ ] **Step B4: Implement target families A and C**

Implement:

```python
def build_target_a_classes(moves: pd.DataFrame, stop_n: float, take_y: float) -> pd.Series:
    ...

def build_target_c_classes(moves: pd.DataFrame, take_x: float, adverse_y: float) -> pd.Series:
    ...
```

Class convention:

```text
-1 = SELL
 0 = SKIP
 1 = BUY
```

- [ ] **Step B5: Write failing tests for Target D**

Use a small OHLC fixture. Assert that BUY and SELL trailing targets are computed independently and that same-bar ambiguity uses the conservative result.

- [ ] **Step B6: Implement Target D**

Implement:

```python
def build_target_d_classes(
    source: pd.DataFrame,
    ohlc_path: str | Path,
    trail_n: float,
    profit_z: float,
    horizon: int,
) -> pd.Series:
    ...
```

Rules:

- entry is next-bar open;
- compute BUY and SELL paths separately;
- same-bar ambiguity is conservative;
- if both BUY and SELL are positive, class is SKIP.

- [ ] **Step B7: Target frequency stage**

Run:

```bash
./.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage target-frequency
```

Output columns:

- target family and params;
- split;
- BUY count;
- SELL count;
- SKIP count;
- ambiguous count;
- ambiguous rate;
- positive rate;
- min yearly BUY/SELL count;
- overlap with old `source["signal"]`;
- gate pass.

Gate:

- train BUY + SELL positives >= 500;
- validation BUY + SELL positives >= 100;
- both sides have at least 50 validation positives unless explicitly running one-sided diagnostic;
- major year = year with at least 500 rows in the split;
- each major validation year has at least 20 BUY+SELL positives;
- each major validation year has at least 5 BUY positives and 5 SELL positives, otherwise mark `one_sided_or_sparse_year=True`.

If `ambiguous_rate > 0.20`, do not use that target family as winner without explicit user approval.

- [ ] **Step B8: Checkpoint Task B**

Commit only if checkpoint commits are approved. Otherwise report changed files and test status.

---

## Task C: Feature Builder

**Purpose:** Build model inputs for direct direction classification.

**Files:**
- Modify: `ML/fractal_level_feature_builder.py`
- Test: `tests/test_fractal_level_feature_builder.py`

- [ ] **Step C1: Write nearest K test**

```python
def test_nearest_k_sorts_by_price_distance_not_fractal_index():
    frame = make_frame_with_fractal1_far_and_fractal9_near()
    features = build_fractal_level_features(frame, input_family="nearest_k", k=1)
    assert features.loc[0, "nearest_00_source_index"] == 9
```

- [ ] **Step C2: Implement first feature family**

Implement `nearest_k16` first.

Rules:

- distance is relative to `fractal0.price`;
- include `fractal0.direction` as a normal input feature, not as direction;
- exclude `fractal0.Up/Dn`;
- include old `fractal1..fractal99.Up/Dn` if present in current row;
- pad missing nearest slots with zeros and `valid=0`.

- [ ] **Step C3: Add runtime measurement**

Write feature build seconds and rows per second to summary output.

- [ ] **Step C4: Add train-frozen normalization**

Fit statistics only on train. Apply frozen stats to validation/test.

- [ ] **Step C5: Checkpoint Task C**

Commit only if checkpoint commits are approved. Otherwise report changed files and test status.

---

## Task D: Validation Benchmark

**Purpose:** Train direct `SELL / SKIP / BUY` models and choose a standalone validation winner.

**Files:**
- Create: `ML/benchmark_entry_path_fractal_level_direct_direction.py`
- Test: `tests/test_benchmark_entry_path_fractal_level_direct_direction.py`
- Output: `validation_grid.csv`, `feature_importance.csv`, `score_distribution.csv`

Trading metrics in this task use the baseline benchmark execution:

```text
entry = open of next bar
exit = close after 24 bars
hold_bars = 24
spread/commission/slippage = 0
sequential test = skip overlapping signals for 24 bars
```

Target D may additionally write a diagnostic trailing-exit metric, but winner selection uses the baseline 24-bar trading metric unless the user explicitly approves changing execution mode.

- [ ] **Step D1: Write failing test for winner selection**

```python
def test_pick_winner_rejects_old_score_and_tiny_trade_count():
    grid = pd.DataFrame(
        [
            {"config": "old_score", "mode": "old_score_diagnostic", "validation_pf": 3.0, "validation_trades": 500, "validation_sequential_pf": 2.0, "overfitting_risk": False},
            {"config": "tiny", "mode": "standalone", "validation_pf": 4.0, "validation_trades": 12, "validation_sequential_pf": 2.0, "overfitting_risk": False},
            {"config": "weak", "mode": "standalone", "validation_pf": 1.05, "validation_trades": 500, "validation_sequential_pf": 1.2, "overfitting_risk": False},
            {"config": "stable", "mode": "standalone", "validation_pf": 1.4, "validation_trades": 500, "validation_sequential_pf": 1.2, "negative_years": 1, "overfitting_risk": False},
        ]
    )

    assert pick_validation_winner(grid)["config"] == "stable"
```

- [ ] **Step D2: Implement staged matrix**

Stage 1:

```text
Input: nearest_k16
Targets: A, C, D
Model: RandomForestClassifier
Mode: standalone
```

Stage 2 only if Stage 1 has potential:

```text
Inputs: zones, zones_plus_nearest_k16
Targets: families that passed Stage 1
```

- [ ] **Step D3: Train model**

Use:

```python
RandomForestClassifier(
    n_estimators=160,
    min_samples_leaf=20,
    class_weight="balanced_subsample",
    random_state=42,
    n_jobs=-1,
)
```

The model predicts class probabilities for:

```text
SELL, SKIP, BUY
```

- [ ] **Step D4: Convert probabilities into candidate signal**

Validation threshold grid:

```text
0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90
```

Rule:

```text
if P(BUY) >= threshold and P(BUY) > P(SELL): candidate_signal = 1
elif P(SELL) >= threshold and P(SELL) > P(BUY): candidate_signal = -1
else: candidate_signal = 0
```

For diagnostics also compute:

```text
direction_margin = abs(P(BUY) - P(SELL))
max_direction_probability = max(P(BUY), P(SELL))
```

- [ ] **Step D5: Write validation grid**

Columns:

- `mode`;
- target family and params;
- input family;
- threshold;
- direction margin summary;
- max direction probability distribution;
- validation trades;
- validation PF;
- validation sequential PF;
- BUY trades;
- SELL trades;
- BUY PF;
- SELL PF;
- BUY win rate;
- SELL win rate;
- BUY mean PnL ATR;
- SELL mean PnL ATR;
- BUY/SELL balance by threshold;
- confusion-like target stats;
- yearly PF;
- negative years;
- feature count;
- `features / validation_candidates`;
- `overfitting_risk`;
- overlap with old `source["signal"]`.

Winner gates:

- `mode == "standalone"`;
- validation trades >= 100;
- validation PF >= 1.15;
- validation sequential PF >= 1.1;
- no obvious yearly instability;
- `overfitting_risk == False`.
- if validation direct-bar baseline is available, compare against it and report the result;
- if one side has < 20% of selected trades, mark `one_sided_candidate=True`.

`one_sided_candidate=True` is not a full `SELL/SKIP/BUY` success. It may still be useful, but the report must classify it as a one-sided candidate.

- [ ] **Step D6: Old-score diagnostic**

Run old score only after standalone validation:

```python
selected = (candidate_signal != 0) & (score >= old_score_threshold)
```

Default:

```text
old_score_threshold = -0.07158749
```

Source:

```text
ML/reports/mt4_entry_path_v1_live_safe_parity/entry_path_v1_live_safe_a075_rule.json
```

The runner must expose `--old-score-threshold`.

Write rows with:

```text
mode = old_score_diagnostic
```

These rows cannot become frozen winner.

- [ ] **Step D7: Feature importance**

Write top-20 feature importances per config to `feature_importance.csv`.

- [ ] **Step D8: Run validation stage**

```bash
./.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage validation-matrix
```

If no standalone winner passes gates, stop. Do not run test.

- [ ] **Step D9: Checkpoint Task D**

Commit only if checkpoint commits are approved. Otherwise report changed files and test status.

---

## Task E: Frozen Test And Report

**Purpose:** Run test once after validation winner is frozen and compare with existing baselines.

**Files:**
- Modify: `ML/benchmark_entry_path_fractal_level_direct_direction.py`
- Create: `docs/reports/2026-05-15-entry-path-fractal-level-direct-direction.md`
- Modify: `docs/ML/benchmark_entry_path_fractal_level_direct_direction.py.md`
- Modify: `docs/ML/entry_path_direct_direction_targets.py.md`
- Modify: `ML/README.md`
- Modify: `MODULE_INDEX.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`

- [ ] **Step E1: Freeze validation winner**

Write frozen config into `summary.json` before test. Include:

- target family and params;
- input family;
- model params;
- feature contract path;
- normalizer stats;
- threshold;
- input paths;
- old-score threshold for diagnostics only.
- execution mode: baseline 24-bar close exit, plus any diagnostic modes.

- [ ] **Step E2: Run frozen test once**

```bash
./.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage frozen-test
```

Outputs:

- `summary.json`;
- `summary.md`;
- `test_selected_rows.csv`.

- [ ] **Step E3: Compare with baselines**

Include:

| Baseline | Test PF | Sequential PF | Trades / sequential trades |
|---|---:|---:|---:|
| all-rows ranking | 0.9134 | 0.5908 | 329 / 133 |
| causal surrogate | 1.1537 | 1.4111 | 36 / 31 |
| direct bar model | 1.1141 | 1.1334 | 1277 / 274 |
| fractal level direct direction | computed | computed | computed |

Also include BUY/SELL separate metrics:

- trades;
- PF;
- win rate;
- mean PnL ATR;
- yearly stability.

If the winner is `one_sided_candidate=True`, classify the result as one-sided, not as a full `SELL/SKIP/BUY` success.

- [ ] **Step E4: Write ML Leakage Preflight**

Report PASS/FAIL:

- decision time;
- split;
- feature allowlist from `feature_contract.json`;
- target-only fields excluded;
- train-only normalization;
- ATR contract;
- execution contract: next-bar open entry, 24-bar close exit, sequential hold 24;
- no test tuning.

- [ ] **Step E5: Update docs**

Update:

- module docs;
- `ML/README.md`;
- `MODULE_INDEX.md`;
- `CHANGELOG.md`;
- `CONTEXT_HANDOFF.md`;
- `wiki/REPO_integrity.md`.
- wiki ingest/update if the new report is not covered by `wiki/index.md`.

- [ ] **Step E6: Verification**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_fractal_level_feature_builder.py \
  tests/test_entry_path_direct_direction_targets.py \
  tests/test_benchmark_entry_path_fractal_level_direct_direction.py -q
```

Run:

```bash
./.venv/bin/python -m py_compile \
  ML/fractal_level_feature_builder.py \
  ML/entry_path_direct_direction_targets.py \
  ML/benchmark_entry_path_fractal_level_direct_direction.py
```

Run:

```bash
git diff --check
```

Run:

```bash
./.venv/bin/python wiki/wiki.py generate
```

If `docs/reports/2026-05-15-entry-path-fractal-level-direct-direction.md` is created and not represented in `wiki/index.md`, run the project wiki ingest/update workflow before final status.

- [ ] **Step E7: Checkpoint final report**

Commit only if checkpoint commits are approved. Otherwise report changed files and test status.

---

## Stop Conditions

- If live-safe audit fails: stop and report the failed invariant.
- If target frequencies are too low: stop and propose simpler targets.
- If validation has no standalone winner: stop and do not run test.
- If winner only works with old score: report diagnostic result, not production progress.
- If standalone winner is `one_sided_candidate=True`: report it as one-sided candidate, not as general direct direction success.
- If frozen test is worse than direct-bar baseline: close as weak research result.
- If frozen test passes research criteria: write a follow-up plan for costs, drawdown, MT4 parity, and confidence intervals.
