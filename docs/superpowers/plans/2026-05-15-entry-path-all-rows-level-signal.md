# Entry Path All-Rows Level Signal Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить гипотезу live-safe `signal_candidate` по всей строке фракталов: найти сильный уровень вокруг `fractal0.price`, взять направление из `fractal0.direction`, оценить candidate отдельно и только потом диагностически проверить старый score-фильтр.

**Architecture:** Один master-plan с последовательными early gates A/B/C. Если gates проходят, строится новый feature layer (`zones`, nearest `K=16`, mixed), новый target layer (A/C/D), и один benchmark runner с validation-first выбором winner и single frozen test. Старый `label_all().signal` остаётся только сравнительной меткой, старый score — только диагностическим фильтром.

**Tech Stack:** Python 3.12, pandas, numpy, scikit-learn, pytest, существующие `processing.label_signals`, `processing.fractal_preprocessing`, `ML.entry_path_trade_filter`, `ML.benchmark_entry_path_all_rows_ranking`

---

## Execution Rules

- Do not use a git worktree; project rules forbid it.
- Use branch `entry-path-all-rows-spec` or create a new branch from it before execution.
- Use `./.venv/bin/python`.
- Use TDD for new modules.
- Tasks A, B, C are sequential blockers, not parallel tasks.
- Do not run full benchmark before A/B/C pass.
- Do not run test set before validation winner is frozen.
- Do not push without explicit user request.

## Read First

- `docs/superpowers/specs/2026-05-14-entry-path-all-rows-level-signal-design.md`
- `docs/reports/2026-05-14-entry-path-all-rows-ranking.md`
- `docs/reports/2026-05-14-entry-path-causal-surrogate.md`
- `docs/reports/2026-05-14-entry-path-direct-bar-model.md`
- `docs/DATA_FLOW.md`
- `processing/label_signals.py`
- `processing/fractal_preprocessing.py`
- `ML/benchmark_entry_path_all_rows_ranking.py`
- `ML/benchmark_entry_path_causal_surrogate.py`
- `ML/benchmark_entry_path_direct_bar_model.py`

## File Structure

### Create

- `ML/fractal_level_feature_builder.py`
  - Parse `fractal*` strings.
  - Build `raw_distance_atr`, `directed_distance_atr`.
  - Build Input A zones.
  - Build Input B nearest `K=16` by price.
  - Build mixed Input A+B.
  - Exclude `fractal0.Up/Dn` from features.
  - Include `fractal1..fractal99.Up/Dn` as old-fractal reaction features.

- `ML/entry_path_level_targets.py`
  - Build direction from `fractal0.direction`.
  - Build reverse-direction baseline.
  - Build target families A/C/D.
  - Build OHLC path trailing target D using next-bar entry.
  - Compute target frequency summaries.

- `ML/benchmark_entry_path_fractal_level_signal.py`
  - Run gates A/B/C.
  - Train simple classifiers only after gates pass.
  - Select candidate threshold on validation.
  - Run standalone candidate check.
  - Run old score distribution diagnostics.
  - Run old score diagnostic filter.
  - Compare with 2026-05-14 baselines.
  - Write reports.

- `tests/test_fractal_level_feature_builder.py`
- `tests/test_entry_path_level_targets.py`
- `tests/test_benchmark_entry_path_fractal_level_signal.py`
- `docs/ML/fractal_level_feature_builder.py.md`
- `docs/ML/entry_path_level_targets.py.md`
- `docs/ML/benchmark_entry_path_fractal_level_signal.py.md`
- `docs/reports/2026-05-15-entry-path-fractal-level-signal.md`

### Modify

- `ML/README.md`
- `MODULE_INDEX.md`
- `CHANGELOG.md`
- `wiki/REPO_integrity.md`

### Output Artifacts

- `ML/reports/entry_path_v1_fractal_level_signal/feature_audit.json`
- `ML/reports/entry_path_v1_fractal_level_signal/direction_baseline.json`
- `ML/reports/entry_path_v1_fractal_level_signal/target_frequency.csv`
- `ML/reports/entry_path_v1_fractal_level_signal/validation_grid.csv`
- `ML/reports/entry_path_v1_fractal_level_signal/score_distribution.csv`
- `ML/reports/entry_path_v1_fractal_level_signal/summary.json`
- `ML/reports/entry_path_v1_fractal_level_signal/summary.md`
- `ML/reports/entry_path_v1_fractal_level_signal/test_selected_rows.csv`

---

## Task A: Live-Safe Feature Audit

**Agent mode:** sequential blocker. Do not run Task B until this passes.

**Purpose:** Prove that features come from the current sorted row and that old-fractal `Up/Dn` are safe to use as historical reaction features.

**Files:**
- Create: `ML/fractal_level_feature_builder.py`
- Create: `tests/test_fractal_level_feature_builder.py`
- Output: `ML/reports/entry_path_v1_fractal_level_signal/feature_audit.json`

- [ ] **Step A1: Write failing tests for fractal parsing**

Add tests that show:

```python
from ML.fractal_level_feature_builder import parse_fractal


def test_parse_fractal_reads_price_direction_time_and_updn():
    parsed = parse_fractal(
        "123:2010.5:-1:0.1:0.2:1:0:0.3:0.4:2:0.5:"
        "1.0:0.2:1.5:0.3:2.0:0.4:0.6:0.1:0.8:0.2:1.1"
    )

    assert parsed["time"] == 123
    assert parsed["price"] == 2010.5
    assert parsed["direction"] == -1
    assert parsed["up_24"] == 1.5
    assert parsed["dn_24"] == 0.3
```

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal_level_feature_builder.py::test_parse_fractal_reads_price_direction_time_and_updn -q
```

Expected: FAIL because module does not exist.

- [ ] **Step A2: Implement `parse_fractal()`**

Implement in `ML/fractal_level_feature_builder.py`:

```python
FRACTAL_FIELDS = {
    "time": 0,
    "price": 1,
    "direction": 2,
    "front": 3,
    "back": 4,
    "strong": 5,
    "break": 6,
    "reverse": 7,
    "power": 8,
    "count": 9,
    "impulse": 10,
    "up_12": 11,
    "dn_12": 12,
    "up_24": 13,
    "dn_24": 14,
    "up_48": 15,
    "dn_48": 16,
    "up_3": 17,
    "dn_3": 18,
    "up_6": 19,
    "dn_6": 20,
    "fractal_atr": 21,
}
```

Use tolerant parsing: invalid or missing values become `None`/`0.0` according to existing `processing.label_signals.parse_fractal` behavior.

- [ ] **Step A3: Write failing tests for feature audit**

Tests:

```python
def test_audit_rejects_future_fractal_time():
    frame = make_source_frame(
        row_time="2024.01.01 10:00",
        fractal0="100:2000:-1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1",
        fractal1="9999999999:2001:1:0:0:0:0:0:0:0:0:1:1:1:1:1:1:1:1:1:1:1",
    )

    result = audit_fractal_rows(frame)

    assert result["future_fractal_rows"] == 1
```

```python
def test_old_updn_features_skip_fractal0_and_use_fractal1():
    features = build_zone_features(make_source_frame_with_fractal0_and_fractal1_updn())

    assert "fractal0_up_24" not in features.columns
    assert features.filter(like="old_up_24").sum(axis=1).iloc[0] > 0
```

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal_level_feature_builder.py -q
```

Expected: FAIL until audit/features are implemented.

- [ ] **Step A4: Implement audit helpers**

Implement:

```python
def audit_fractal_rows(frame: pd.DataFrame) -> dict[str, int | float]:
    ...
```

Checks:

- row count;
- rows with missing/invalid `fractal0`;
- rows where any used fractal has `fractal_time > row_time`;
- rows where `fractal0.Up/Dn` nonzero;
- share of rows where `fractal1..fractal99.Up/Dn` are nonzero;
- sort sanity: `fractal0` exists after preprocessing.

- [ ] **Step A5: Add CLI audit mode**

In `ML/benchmark_entry_path_fractal_level_signal.py`, add a minimal CLI mode:

```bash
./.venv/bin/python -m ML.benchmark_entry_path_fractal_level_signal --stage feature-audit
```

It writes:

```text
ML/reports/entry_path_v1_fractal_level_signal/feature_audit.json
```

- [ ] **Step A6: Run real feature audit**

Run:

```bash
./.venv/bin/python -m ML.benchmark_entry_path_fractal_level_signal --stage feature-audit
```

Expected:

- no future fractal rows;
- `fractal0.Up/Dn` excluded from features even if present;
- old-fractal `Up/Dn` availability reported for `fractal1..fractal99`.

- [ ] **Step A7: Commit Task A**

```bash
git add ML/fractal_level_feature_builder.py ML/benchmark_entry_path_fractal_level_signal.py tests/test_fractal_level_feature_builder.py ML/reports/entry_path_v1_fractal_level_signal/feature_audit.json
git commit -m "Add entry path level feature audit"
```

---

## Task B: Direction Baseline Gate

**Agent mode:** sequential blocker. Do not run Task C until this passes.

**Purpose:** Decide whether fixed `fractal0.direction` is strong enough to justify the full level-candidate matrix.

**Files:**
- Create/Modify: `ML/entry_path_level_targets.py`
- Modify: `ML/benchmark_entry_path_fractal_level_signal.py`
- Test: `tests/test_entry_path_level_targets.py`
- Output: `ML/reports/entry_path_v1_fractal_level_signal/direction_baseline.json`

- [ ] **Step B1: Write failing tests for direction mapping**

```python
from ML.entry_path_level_targets import signal_from_fractal0_direction


def test_signal_from_fractal0_direction_uses_entry_path_convention():
    assert signal_from_fractal0_direction(-1) == 1
    assert signal_from_fractal0_direction(1) == -1
    assert signal_from_fractal0_direction(0) == 0
```

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_path_level_targets.py::test_signal_from_fractal0_direction_uses_entry_path_convention -q
```

Expected: FAIL until module exists.

- [ ] **Step B2: Implement direction helpers**

Implement:

```python
def signal_from_fractal0_direction(fractal_direction: int) -> int:
    if fractal_direction == -1:
        return 1
    if fractal_direction == 1:
        return -1
    return 0
```

Also implement reverse direction:

```python
def reverse_signal(signal: int) -> int:
    return -int(signal)
```

- [ ] **Step B3: Write tests for direction vs reverse PnL**

Use a tiny OHLC fixture and assert:

- direction signal PnL is computed;
- reverse signal PnL is computed;
- BUY-only/SELL-only buckets are reported separately.

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_path_level_targets.py -q
```

- [ ] **Step B4: Implement direction baseline summary**

Implement:

```python
def summarize_direction_baseline(
    source: pd.DataFrame,
    ohlc_path: str | Path,
    horizon: int = 24,
) -> dict[str, Any]:
    ...
```

It must report:

- trades by `fractal0.direction`;
- PF;
- win rate;
- mean PnL ATR;
- same stats for reverse direction;
- BUY-only stats;
- SELL-only stats;
- correct direction rate;
- gate verdict.

Gate fails if:

- `fractal0.direction` PF <= 1.0;
- reverse direction is better;
- correct direction rate is around 50%;
- BUY-only or SELL-only is clearly damaging the combined result.

- [ ] **Step B5: Add CLI direction stage**

Run:

```bash
./.venv/bin/python -m ML.benchmark_entry_path_fractal_level_signal --stage direction-baseline
```

Output:

```text
ML/reports/entry_path_v1_fractal_level_signal/direction_baseline.json
```

- [ ] **Step B6: Run real direction gate**

Run:

```bash
./.venv/bin/python -m ML.benchmark_entry_path_fractal_level_signal --stage direction-baseline
```

If gate fails, stop implementation and report. Do not continue to Task C until user decides whether to switch to `SELL/SKIP/BUY`.

- [ ] **Step B7: Commit Task B**

```bash
git add ML/entry_path_level_targets.py ML/benchmark_entry_path_fractal_level_signal.py tests/test_entry_path_level_targets.py ML/reports/entry_path_v1_fractal_level_signal/direction_baseline.json
git commit -m "Add entry path level direction gate"
```

---

## Task C: Target Frequency Gate

**Agent mode:** sequential blocker. Do not build full features or train classifiers until this passes.

**Purpose:** Decide which target families have enough positive examples to be worth training.

**Files:**
- Modify: `ML/entry_path_level_targets.py`
- Modify: `ML/benchmark_entry_path_fractal_level_signal.py`
- Test: `tests/test_entry_path_level_targets.py`
- Output: `ML/reports/entry_path_v1_fractal_level_signal/target_frequency.csv`

- [ ] **Step C1: Write failing tests for target A and C**

```python
def test_target_a_fast_bounce_uses_fav_and_adv_thresholds():
    frame = pd.DataFrame({"signal": [1, -1], "ATR": [2.0, 2.0], "up_6": [5.0, 1.0], "dn_6": [1.0, 5.0]})

    target = build_target_a_fast_bounce(frame, stop_n=2.0, take_y=2.0)

    assert target.tolist() == [1, 1]
```

```python
def test_target_c_rejects_large_early_adverse_move():
    frame = pd.DataFrame({"signal": [1], "ATR": [2.0], "up_24": [10.0], "dn_12": [8.0]})

    target = build_target_c_limited_risk(frame, take_x=4.0, adverse_y=2.0)

    assert target.tolist() == [0]
```

- [ ] **Step C2: Implement target A and C**

Rules:

```text
A: adv_6 < N * ATR and fav_6 >= Y * ATR
C: fav_24 >= X * ATR and adv_12 <= Y * ATR
```

Use `signal` as the candidate direction:

- BUY: `fav=up`, `adv=dn`;
- SELL: `fav=dn`, `adv=up`.

- [ ] **Step C3: Write failing test for Target D OHLC path**

Test that Target D cannot be built from only `fav/adv`; it needs OHLC path.

Use a small OHLC file where:

- next-bar open is entry;
- price reaches a new best high;
- trailing stop closes with profit.

Assert:

```python
target = build_target_d_trailing_profit(source, ohlc_path, trail_n=2.0, profit_z=1.0, horizon=6)
assert target.iloc[0] == 1
```

- [ ] **Step C4: Implement Target D using OHLC path**

Use the same semantics as `processing.label_signals.simulate_trailing_stop_exit()`:

```text
entry = open of next bar
BUY: best_high, stop = best_high - N * ATR
SELL: best_low, stop = best_low + N * ATR
```

Target D positive only when trailing closes with profit `>= Z * ATR`.

If existing simulator returns only PnL and not exit reason, implement a local helper in `ML/entry_path_level_targets.py` that returns:

```python
{"pnl_atr": float, "exit_reason": "trailing_stop" | "timeout"}
```

- [ ] **Step C5: Implement target frequency summary**

Implement:

```python
def summarize_target_frequencies(train, validation, target_builders) -> pd.DataFrame:
    ...
```

Columns:

- `target_name`;
- `split`;
- `positive_rate`;
- `positive_count`;
- `row_count`;
- `buy_positive_count`;
- `sell_positive_count`;
- `min_year_positive_count`;
- `gate_pass`.

Gate passes if:

```text
positive_rate >= 3%
train positives >= 500
validation positives >= 100
major validation/test years >= 20 positives
```

- [ ] **Step C6: Add CLI target-frequency stage**

Run:

```bash
./.venv/bin/python -m ML.benchmark_entry_path_fractal_level_signal --stage target-frequency
```

Output:

```text
ML/reports/entry_path_v1_fractal_level_signal/target_frequency.csv
```

- [ ] **Step C7: Run real target frequency gate**

Run:

```bash
./.venv/bin/python -m ML.benchmark_entry_path_fractal_level_signal --stage target-frequency
```

If all A/C/D fail, stop and report. If only one or two pass, benchmark only passing target families.

- [ ] **Step C8: Commit Task C**

```bash
git add ML/entry_path_level_targets.py ML/benchmark_entry_path_fractal_level_signal.py tests/test_entry_path_level_targets.py ML/reports/entry_path_v1_fractal_level_signal/target_frequency.csv
git commit -m "Add entry path level target gates"
```

---

## Task D: Level Feature Builder

**Agent mode:** can be assigned to a subagent after A/B/C pass.

**Purpose:** Build the three first-pass input representations: zones, nearest `K=16`, and mixed.

**Files:**
- Modify: `ML/fractal_level_feature_builder.py`
- Test: `tests/test_fractal_level_feature_builder.py`

- [ ] **Step D1: Write failing tests for raw and directed distances**

```python
def test_build_distance_features_mirrors_sell_direction():
    frame = make_frame(fractal0_price=100.0, fractal0_direction=1, fractal1_price=95.0, atr=2.5)

    features = build_fractal_level_features(frame, input_family="nearest_k", k=1)

    assert features.loc[0, "nearest_00_raw_distance_atr"] == -2.0
    assert features.loc[0, "nearest_00_directed_distance_atr"] == 2.0
```

- [ ] **Step D2: Implement distance features**

Do not use absolute price as model input except via:

- `raw_distance_atr`;
- `directed_distance_atr`;
- rank/count context around `fractal0.price`.

- [ ] **Step D3: Write failing tests for Input A zones**

Assert that:

- zones aggregate by price distance;
- old-fractal `Up/Dn` from `fractal1..` is included;
- `fractal0.Up/Dn` is excluded;
- `outside_4atr_*` features are present.

- [ ] **Step D4: Implement Input A zones**

Required zone bands:

```text
0.00..0.25 ATR
0.25..0.50 ATR
0.50..1.00 ATR
1.00..2.00 ATR
2.00..4.00 ATR
```

Required aggregate families:

- count;
- direction balance;
- same/opposite direction;
- strong;
- break/unbroken;
- power sum/max;
- count mean/max;
- impulse max;
- old-fractal `Up/Dn` favorable/adverse summaries.

- [ ] **Step D5: Write failing tests for Input B nearest K=16**

Assert that nearest K sorts by price distance, not column number:

```python
def test_nearest_k_sorts_by_price_distance_not_fractal_index():
    frame = make_frame_with_fractal1_far_and_fractal9_near()
    features = build_fractal_level_features(frame, input_family="nearest_k", k=1)
    assert features.loc[0, "nearest_00_source_index"] == 9
```

- [ ] **Step D6: Implement nearest K=16**

Use fixed width:

- exactly 16 slots;
- missing slots padded with zeros;
- each slot has `nearest_XX_valid`;
- include `source_index` for diagnostics, but do not train on it unless explicitly included as diagnostic-only.

- [ ] **Step D7: Implement train-frozen normalization**

Add:

```python
def fit_feature_normalizer(train_features: pd.DataFrame) -> dict[str, Any]:
    ...

def apply_feature_normalizer(features: pd.DataFrame, stats: dict[str, Any]) -> pd.DataFrame:
    ...
```

Rules:

- fit only on train;
- apply to validation/test;
- leave already local ratio/distance features unscaled if no scaling is needed;
- if scaling is used, save stats in summary JSON.

- [ ] **Step D8: Run feature tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal_level_feature_builder.py -q
```

- [ ] **Step D9: Commit Task D**

```bash
git add ML/fractal_level_feature_builder.py tests/test_fractal_level_feature_builder.py
git commit -m "Add entry path level feature builder"
```

---

## Task E: Validation Benchmark Runner

**Agent mode:** can be assigned to a subagent after Task D.

**Purpose:** Train simple classifiers on validation-safe targets and choose one winner on validation.

**Files:**
- Modify: `ML/benchmark_entry_path_fractal_level_signal.py`
- Test: `tests/test_benchmark_entry_path_fractal_level_signal.py`
- Output: `ML/reports/entry_path_v1_fractal_level_signal/validation_grid.csv`

- [ ] **Step E1: Write failing test for validation-only winner selection**

```python
def test_pick_validation_winner_prefers_pf_then_trade_count():
    grid = pd.DataFrame(
        [
            {"config": "a", "validation_pf": 1.1, "validation_trades": 500},
            {"config": "b", "validation_pf": 1.3, "validation_trades": 120},
        ]
    )

    winner = pick_validation_winner(grid)

    assert winner["config"] == "b"
```

- [ ] **Step E2: Implement classifier matrix**

First-pass matrix:

```text
Inputs:
- zones
- nearest_k16
- zones_plus_nearest_k16

Targets:
- A
- C
- D

Feature variants:
- with old-fractal Up/Dn
- geometry-only
```

Do not include Target B, K=8, K=32, Input C, or Input D in first-pass matrix.

Use a simple, bounded model first:

```python
RandomForestClassifier(
    n_estimators=160,
    min_samples_leaf=20,
    class_weight="balanced_subsample",
    random_state=42,
    n_jobs=-1,
)
```

- [ ] **Step E3: Candidate threshold selection**

Select threshold on validation only. Grid:

```text
0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90
```

For each config write:

- target family;
- input family;
- with/without old-fractal `Up/Dn`;
- threshold;
- validation trades;
- validation PF;
- validation sequential PF;
- yearly PF;
- feature count;
- `features / validation_candidates`.

- [ ] **Step E4: Standalone candidate validation**

Validate first without old score:

```python
selected = signal_candidate != 0
```

This is the main evidence for level-candidate quality.

- [ ] **Step E5: Old score distribution diagnostic**

For each validation candidate universe compare:

- old `signal != 0`;
- new `signal_candidate != 0`;
- all rows.

Write:

```text
ML/reports/entry_path_v1_fractal_level_signal/score_distribution.csv
```

Columns:

- universe;
- count;
- mean;
- median;
- std;
- p10/p25/p75/p90;
- share_above_original_threshold;
- median_shift_over_old_std;
- transfer_warning.

- [ ] **Step E6: Old score diagnostic filter**

Run:

```python
selected = (signal_candidate != 0) & (score >= original_threshold)
```

Mark it as diagnostic. Do not treat as production approval.

- [ ] **Step E7: Run validation benchmark**

Run:

```bash
./.venv/bin/python -m ML.benchmark_entry_path_fractal_level_signal --stage validation-matrix
```

Expected outputs:

- `validation_grid.csv`;
- `score_distribution.csv`;
- no test metrics yet.

- [ ] **Step E8: Commit Task E**

```bash
git add ML/benchmark_entry_path_fractal_level_signal.py tests/test_benchmark_entry_path_fractal_level_signal.py ML/reports/entry_path_v1_fractal_level_signal/validation_grid.csv ML/reports/entry_path_v1_fractal_level_signal/score_distribution.csv
git commit -m "Add entry path level validation benchmark"
```

---

## Task F: Frozen Test And Report

**Agent mode:** integration task. Should be done by the coordinator, not a side agent.

**Purpose:** Run test once after validation winner is frozen and compare to existing baselines.

**Files:**
- Modify: `ML/benchmark_entry_path_fractal_level_signal.py`
- Create: `docs/reports/2026-05-15-entry-path-fractal-level-signal.md`
- Modify: `ML/README.md`
- Modify: `MODULE_INDEX.md`
- Modify: `CHANGELOG.md`
- Output: `ML/reports/entry_path_v1_fractal_level_signal/summary.json`
- Output: `ML/reports/entry_path_v1_fractal_level_signal/summary.md`
- Output: `ML/reports/entry_path_v1_fractal_level_signal/test_selected_rows.csv`

- [ ] **Step F1: Freeze validation winner**

Load `validation_grid.csv`, choose one winner, and write frozen config into `summary.json` before running test.

The frozen config must include:

- target family;
- target parameters;
- input family;
- old-fractal `Up/Dn` on/off;
- model params;
- feature normalizer stats path or inline stats;
- candidate threshold;
- old score threshold used only for diagnostics.

- [ ] **Step F2: Run frozen test once**

Run:

```bash
./.venv/bin/python -m ML.benchmark_entry_path_fractal_level_signal --stage frozen-test
```

Expected outputs:

- standalone test metrics;
- diagnostic old-score-filter test metrics;
- sequential metrics;
- yearly metrics;
- selected rows.

- [ ] **Step F3: Compare with baselines**

Include comparison table:

| Baseline | Test PF | Sequential PF | Trades / sequential trades |
|---|---:|---:|---:|
| all-rows ranking | 0.9134 | 0.5908 | 329 / 133 |
| causal surrogate | 1.1537 | 1.4111 | 36 / 31 |
| direct bar model | 1.1141 | 1.1334 | 1277 / 274 |
| fractal level signal winner | computed | computed | computed |

- [ ] **Step F4: Classify outcome**

Use spec criteria:

Research-pass:

- test PF > 1.2;
- sequential PF > 1.1;
- test trades >= 100;
- not worse than direct-bar baseline by meaningful metrics.

Production-candidate requires more and is not expected in this phase:

- spread/commission/slippage;
- MT4 parity;
- drawdown;
- bootstrap/confidence interval;
- execution parity.

- [ ] **Step F5: Write report**

Create `docs/reports/2026-05-15-entry-path-fractal-level-signal.md` with:

- context;
- gates A/B/C results;
- validation matrix;
- frozen test;
- baseline comparison;
- verdict;
- next step.

- [ ] **Step F6: Update docs and indexes**

Update:

- `docs/ML/fractal_level_feature_builder.py.md`;
- `docs/ML/entry_path_level_targets.py.md`;
- `docs/ML/benchmark_entry_path_fractal_level_signal.py.md`;
- `ML/README.md`;
- `MODULE_INDEX.md`;
- `CHANGELOG.md`.

- [ ] **Step F7: Run verification**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_fractal_level_feature_builder.py \
  tests/test_entry_path_level_targets.py \
  tests/test_benchmark_entry_path_fractal_level_signal.py -q
```

Run:

```bash
./.venv/bin/python -m py_compile \
  ML/fractal_level_feature_builder.py \
  ML/entry_path_level_targets.py \
  ML/benchmark_entry_path_fractal_level_signal.py
```

Run:

```bash
git diff --check
```

Run:

```bash
./.venv/bin/python wiki/wiki.py generate
```

- [ ] **Step F8: Commit final report**

```bash
git add ML/fractal_level_feature_builder.py ML/entry_path_level_targets.py ML/benchmark_entry_path_fractal_level_signal.py tests/test_fractal_level_feature_builder.py tests/test_entry_path_level_targets.py tests/test_benchmark_entry_path_fractal_level_signal.py docs/ML/fractal_level_feature_builder.py.md docs/ML/entry_path_level_targets.py.md docs/ML/benchmark_entry_path_fractal_level_signal.py.md docs/reports/2026-05-15-entry-path-fractal-level-signal.md ML/reports/entry_path_v1_fractal_level_signal ML/README.md MODULE_INDEX.md CHANGELOG.md wiki/REPO_integrity.md
git commit -m "Add entry path fractal level signal benchmark"
```

---

## Task G: Stop Conditions And Branch Decisions

**Purpose:** Keep the research controlled and avoid wasting time on a failed branch.

- [ ] **If Task A fails**

Stop. Do not train. Report which live-safe invariant failed.

- [ ] **If Task B fails**

Stop before A/C/D matrix. Propose a separate plan for `SELL/SKIP/BUY` direct direction model or BUY-only/SELL-only sources.

- [ ] **If Task C finds no usable targets**

Stop. Report target frequencies and propose revised targets.

- [ ] **If validation matrix finds no PF > 1 candidate**

Do not run test. Report validation failure.

- [ ] **If frozen test is worse than direct-bar baseline**

Report as research failure or weak diagnostic result. Do not call it production-ready.

- [ ] **If frozen test passes research criteria**

Write follow-up plan for:

- spread/commission/slippage;
- bootstrap/confidence interval;
- MT4 parity;
- optional direct `SELL/SKIP/BUY` comparison under same feature set.
