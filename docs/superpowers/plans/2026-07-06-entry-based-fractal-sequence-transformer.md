# Entry-Based Fractal Sequence Transformer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, даёт ли Transformer на последовательности `fractal0..fractal99` устойчивый directional-прирост для `entry-based next open`, не меняя target, split и правило входа.

**Architecture:** Новый runner строит не плоскую таблицу, а тензор `[rows, 100, token_features]`, где каждый token — один фрактал в порядке от свежего `fractal0` к старому `fractal99`. Transformer обучается на этом тензоре с mask/padding, train-only нормализацией и теми же `entry_*` targets, что closeout/powerful-tabular этапы. Результат сравнивается с мощным табличным прогоном как с baseline, но не может открыть `locked_test`: положительный direction после уже увиденных отчётов означает только `DIRECTION_REPLICATION_REQUIRED`.

**Tech Stack:** Python 3.10+, pandas, numpy, scikit-learn, PyTorch, существующие `ML/data_loader.py`, `ML/models/transformer.py`, `ML/baseline/benchmark_entry_based_next_open_closeout.py`, `ML/baseline/benchmark_entry_based_powerful_tabular.py`, `./.venv/bin/python`, pytest.

## Global Constraints

- Work on the current branch; do not use git worktree.
- Use `./.venv/bin/python` for every Python command.
- Do not run `git commit` unless the user explicitly asks for commits or the stage is being closed through `stage-reporting`.
- This stage is `DIAGNOSTIC_ONLY` / `RESEARCH_ONLY`; it cannot create a live trading candidate.
- Do not open `locked_test`.
- Do not include EURUSD or any cross-pair validation.
- Do not overwrite previous artifacts:
  - `ML/reports/entry_based_next_open_closeout.*`
  - `ML/reports/entry_based_powerful_tabular.*`
- Write new artifacts under the prefix `entry_based_sequence_transformer`.
- Entry rule remains frozen: signal exists at `signal_time`; entry is the next available `entry_open`.
- Use the same split policy as powerful-tabular:
  - `train <= 2020`
  - `validation = 2021-2025`, split into `val_select` and `val_eval`
  - `2026 = low_n_disclosure`, selection-forbidden
  - `locked_test = not_opened`
- First run training policy is fixed epochs: train for `60` epochs and do not use validation for early stopping. If early stopping is later enabled, it must use a train-internal stop split carved out of `train <= 2020`, not `val_select`, `val_eval` or 2026.
- Use the same target horizons: `H3`, `H6`, `H12`, `H24`.
- Use the same predicted target families:
  - `entry_log_ratio_H`
  - `entry_up_H`
  - `entry_dn_H`
- Use `simple_trade_H` only as a rough diagnostic derived from predictions. It is not a trading signal and cannot select a winner after viewing `val_eval`.
- Top-level target/label/future-derived columns remain forbidden as input features:
  - `up_*`, `dn_*`
  - `entry_up_*`, `entry_dn_*`, `entry_log_ratio_*`
  - `ret_*`, `fav_*`, `adv_*`
  - `target_*`, `label_*`, `outcome_*`
  - `predict`, `signal`
- Serialized `Up/Dn` fields inside `fractal1..fractal99` are allowed as token features only because `docs/dataset_description.md` and `docs/methodology/A8-feature-target-catalog.md` describe them as MT4 producer state available in the current row. The runner must still prove it reads them from `fractal*`, not from top-level target columns.
- `fractal0` `Up/Dn` must be forced to `0.0` in the main tensor contract. Newly born `fractal0` reaction fields are not treated as historical state and must not drive the main verdict.
- Feature order must be explicit and written to JSON.
- Sequence order must be explicit: token index `0 = fractal0 = newest`, token index `99 = fractal99 = oldest`.
- Padding/mask contract: valid token `True`; padding token `False`; padding values are `0.0`; padding is excluded from scaler fit.
- Normalization contract: scaler fit only on valid train tokens; validation and 2026 disclosure are transform-only.
- Target normalization contract: target scaler fit only on train targets; input scaler and target scaler are separate; JSON must record target order, center/scale strategy and inverse-transform policy for metrics.
- If final tensor audit contains `ERROR`, abort before fitting.
- If final tensor audit contains `WARNING`, continue only when every warning has an `audit_decision` of `accept_as_warning`, `fix_and_rerun`, `reject_profile`, or `block`.
- Support `--resume` / `--no-resume`; default is `--resume`.
- `--resume` must compare `run_config_hash` and refuse to continue if representations, token fields, models, horizons, target families, seeds, dependency versions, split policy, normalization config or output schema differ.
- Print heartbeat for long runs: preflight, tensor build, audit, each run start/end, `done_runs/total_runs`, elapsed, ETA.
- Save JSON after every completed run.
- Write `failed_runs` to JSON with representation/model/seed, elapsed time, exception type and text. One failed model must not hide completed results.
- Write runtime metadata per run: elapsed time, rows, token count, token feature count, batch size, device, torch thread count, seed, status.
- Write `yearly_metrics` for `val_select` and `val_eval` by years 2021, 2022, 2023, 2024, 2025.
- `low_n_disclosure=2026` is disclosure-only. Summary, winner selection, gates and verdict must not read it.
- Write top-level `selection_policy` to JSON:
  - `winner_metric = val_select`
  - `val_eval = check_only`
  - `low_n_disclosure_2026 = disclosure_only`
  - `locked_test = not_opened`
- Write top-level `training_policy` to JSON:
  - `mode = fixed_epochs`
  - `epochs = 60`
  - `early_stopping = disabled`
  - `validation_used_for_early_stopping = false`

---

## Research Contract

**Main question:** Did flat tabular representation lose useful ordering/interaction information in the 100-fractal history, or does `entry-based next open` still fail after a sequence model sees the ordered history?

**Secondary question:** If sequence modeling strengthens amplitude but not direction, should the project stop spending compute on `next open` direction and move to movement-regime/amplitude or fractal-price entry mechanics?

**Interpretation rule:** This is not an independent discovery. The idea follows multiple previous reports. Any positive direction result is a hypothesis requiring a separate replication plan; it is not a frozen rule and not a reason to open `locked_test`.

## Input Representation

The primary input is a 3D sequence tensor:

```text
X.shape = [n_rows, 100, token_feature_count]
mask.shape = [n_rows, 100]
```

Each token corresponds to one serialized fractal column:

```text
token 0  <- fractal0  newest
token 1  <- fractal1
...
token 99 <- fractal99 oldest
```

Main representation:

| Representation | Token count | Selection rule | Role |
|---|---:|---|---|
| `all100_sequence` | 100 | all valid `fractal0..fractal99` in original order | Primary sequence hypothesis |
| `nearest_k80_sequence` | 80 + padding to 100 | 80 price-nearest valid fractals, then preserve recency order inside selected set | Candidate comparison to powerful-tabular `nearest_k80` |
| `nearest_k60_sequence` | 60 + padding to 100 | 60 price-nearest valid fractals, then preserve recency order inside selected set | Candidate comparison to closeout baseline |

Do not include `corridor_5atr_sequence` in the first run. Previous audits showed corridor profiles often create distribution warnings and sparse/shifted coverage. Add it only in a later plan if all100/nearest sequence gives a reason to continue.

Token fields for the main contract:

| Field | Formula / source | Reason |
|---|---|---|
| `direction` | fractal field idx 2 | type of level: peak/valley |
| `front` | idx 3 | movement before fractal |
| `back` | idx 4 | movement after fractal, current-row state |
| `strong` | idx 5 | current-row level state |
| `break` | idx 6 | current-row break count |
| `reverse` | idx 7 | reverse strength |
| `power` | idx 8 | accumulated level power |
| `count` | idx 9 | level coincidence count |
| `impulse` | idx 10 | local impulse |
| `up_3`, `dn_3`, `up_6`, `dn_6`, `up_12`, `dn_12`, `up_24`, `dn_24`, `up_48`, `dn_48` | idx 17..20 and 11..16 inside `fractal1..fractal99`; forced `0.0` for token 0 / `fractal0` | historical reaction state from older MT4 producer levels |
| `log_fractal_atr_ratio` | `log(fractal_atr / row_ATR)` | volatility regime of the level |
| `log_shift` | `log1p(shift)` | age of the level |
| `log_delta_shift` | `log1p(abs(shift_i - shift_{i+1}))` | irregular event spacing |
| `price_coord_atr` | `(price_i - fractal0_price) / row_ATR` | relative geometry around current level |
| `abs_price_coord_atr` | `abs(price_coord_atr)` | distance magnitude |
| `dir_price_coord_atr` | `price_coord_atr * direction_i` | direction-aware geometry |
| `hour_sin`, `hour_cos` | row `time` | calendar control shared across tokens |
| `dow_sin`, `dow_cos` | row `time` | calendar control shared across tokens |

The plan intentionally does not use raw absolute price as a main field. Absolute price can encode historical regime; if needed, add a separate later diagnostic profile, not this first sequence run.

Calendar control profiles:

| Control | Input | Requirement |
|---|---|---|
| `time_only_clean` | `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` only | Run a cheap non-neural control and disclose whether calendar alone is close to the selected direction result |
| `no_time_sequence` | same sequence fields as main profile, excluding `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` | Run at least for the selected representation/model after main scoring, or explain why it was skipped |

These controls are not part of the main winner search and do not expand the candidate matrix. They prevent a false conclusion that Transformer learned fractal structure when the gain is mostly calendar regime.

## Model Matrix

Use two Transformer configurations and one non-neural baseline on the same sequence tensor:

| Model key | Type | Purpose |
|---|---|---|
| `transformer_small` | PyTorch Transformer, `d_model=64`, `nhead=4`, `layers=2`, dropout `0.20` | Bounded first check |
| `transformer_medium` | PyTorch Transformer, `d_model=128`, `nhead=8`, `layers=3`, dropout `0.20` | Capacity stress without huge sweep |
| `sequence_flat_hist_gradient_boosting` | flatten normalized tokens + mask summary into HGB | Sanity baseline: same tensor information with explicit positional columns but without attention |

Interpretation rule for `sequence_flat_hist_gradient_boosting`: if it matches or beats Transformer, the conclusion is not “order does not matter”. The correct conclusion is narrower: attention did not add value over a flat positional table that already exposes token order through column positions.

Seeds:

```text
42
```

If any candidate-only direction row passes diagnostic gates, the runner must immediately schedule or report `replication_required` with seeds:

```text
42, 43, 44
```

The first pass search width is:

```text
3 representations * 3 models * 1 seed * 4 horizons * 3 predicted target families = 108 metric comparisons
```

There are 9 model/representation jobs. Each job predicts the same 12 target columns.

## Gate Policy

Allowed verdicts:

- `REJECT_SEQUENCE_CAPACITY_EXPLANATION`: sequence Transformer does not materially improve direction.
- `PIVOT_AMPLITUDE`: amplitude remains stronger than direction; direction fails gates.
- `DIRECTION_REPLICATION_REQUIRED`: candidate-only direction passes diagnostic gates but needs a separate multi-seed replication plan.
- `ABORT_CONTRACT_FAIL`: smoke-check, leakage, split, tensor audit or normalization contract fails before trustworthy training.

Forbidden verdicts:

- `FREEZE_PROPOSAL_ONLY`
- `CANDIDATE`
- `FROZEN`
- `READY_FOR_LOCKED_TEST`

Direction gates:

- candidate-only representation, not `all100_sequence`;
- selected by `val_select`, not by `val_eval` or 2026;
- `entry_log_ratio` selected row on `val_select >= 0.10`;
- same selected row on `val_eval >= 0.05`;
- beats powerful-tabular selected candidate `nearest_k80 / hist_gradient_boosting_strong / H12`: `val_select=0.0519`, `val_eval=-0.0009`;
- report separately discloses the previous powerful-tabular best-by-`val_eval` row `corridor_5atr / extra_trees_regressor / H12`: `val_select=0.0042`, `val_eval=0.0475`, marked `selection_forbidden`;
- beats older closeout candidate baseline `nearest_k60 / xgboost_depth5 / H12`: `val_select=0.0373`, `val_eval=0.0274`;
- same representation/model/horizon direction sign is positive on `val_select` and `val_eval`;
- yearly metrics do not show the result concentrated in one year;
- selected row does not lose to matching `all100_sequence` on both `val_select` and `val_eval`;
- `simple_trade` is positive on both `val_select` and `val_eval`, or the report must mark the result as non-tradable ranking-only evidence;
- no blocker in smoke-check, feature contract, split check, tensor scale audit or normalization contract.

Amplitude pivot gates:

- best amplitude `entry_up` or `entry_dn` on `val_select >= 0.25`;
- same selected row on `val_eval >= 0.15`;
- direction gates not passed.

Amplitude confirmation is not a new trading result. It only strengthens the already observed pivot toward movement-regime/amplitude research.

What falsifies the sequence-capacity explanation:

- If no candidate-only sequence row reaches `entry_log_ratio val_select >= 0.10` and `val_eval >= 0.05`, the explanation “flat table lost the useful fractal order” is rejected for the current `next open` target.
- If a positive `val_eval` row appears only after sorting by `val_eval`, it is disclosure-only and does not rescue the sequence-capacity explanation.
- If `time_only_clean` is close to the best sequence direction row, the result is calendar/regime evidence, not fractal-sequence evidence.
- If `sequence_flat_hist_gradient_boosting` matches Transformer, the result does not prove that order is irrelevant; it means attention was not the missing component above explicit positional flattening.

## File Structure

**Create**

- `ML/baseline/benchmark_entry_based_sequence_transformer.py` - runner for sequence tensor build, audit, Transformer training and report JSON.
- `tests/test_entry_based_sequence_transformer.py` - focused tests for input contract, leakage, normalization, resume, verdict policy and output isolation.
- `docs/ML/benchmark_entry_based_sequence_transformer.py.md` - module documentation.
- `docs/reports/2026-07-06-entry-based-fractal-sequence-transformer.md` - final report after execution.

**Modify**

- `CHANGELOG.md` - only after final report is complete.
- `CONTEXT_HANDOFF.md` - only after final report is complete.
- `docs/tests/tests.md` - add focused test command.
- `MODULE_INDEX.md` - add new runner/doc/test entries if current index conventions require it.
- `wiki/research/fractal-stop-research.md`, `wiki/log.md`, `wiki/REPO_integrity.md` - update through wiki tooling after report is final.

**Generated**

- `ML/reports/entry_based_sequence_transformer.json`
- `ML/reports/entry_based_sequence_transformer_metrics.csv`
- `ML/reports/entry_based_sequence_transformer_rows.csv`
- `ML/reports/entry_based_sequence_transformer_tensor_audit.csv`
- `ML/reports/entry_based_sequence_transformer_run.log`

**Read Before Implementation**

- `docs/methodology/README.md`
- `docs/methodology/03-feature-contract-leakage.md`
- `docs/methodology/06-temporal-split.md`
- `docs/methodology/08-model-development.md`
- `docs/methodology/09-validation-freeze.md`
- `docs/methodology/16-reporting-audit.md`
- `docs/methodology/A7-feature-distribution-audit.md`
- `docs/methodology/A8-feature-target-catalog.md`
- `docs/dataset_description.md`
- `docs/reports/2026-07-04-entry-based-next-open-closeout.md`
- `docs/reports/2026-07-06-entry-based-powerful-tabular-models.md`
- `ML/data_loader.py`
- `ML/models/transformer.py`
- `ML/baseline/benchmark_entry_based_next_open_closeout.py`
- `ML/baseline/benchmark_entry_based_powerful_tabular.py`
- `tests/test_entry_based_powerful_tabular.py`

---

### Task 1: Runner Scope And Output Isolation

**Files:**
- Create: `ML/baseline/benchmark_entry_based_sequence_transformer.py`
- Create: `tests/test_entry_based_sequence_transformer.py`

**Interfaces:**
- Produces `SEQUENCE_TRANSFORMER_REPRESENTATIONS: tuple[str, ...]`.
- Produces `SEQUENCE_TRANSFORMER_MODEL_KEYS: tuple[str, ...]`.
- Produces `SEQUENCE_TRANSFORMER_SEEDS: tuple[int, ...]`.
- Produces `SEQUENCE_TRANSFORMER_OUTPUT_PREFIX: str`.
- Produces `enumerate_sequence_transformer_jobs() -> list[dict[str, object]]`.

- [ ] **Step 1: Write the failing scope test**

```python
import ML.baseline.benchmark_entry_based_sequence_transformer as runner


def test_sequence_transformer_scope_is_bounded_and_isolated():
    assert runner.SEQUENCE_TRANSFORMER_OUTPUT_PREFIX == "entry_based_sequence_transformer"
    assert runner.SEQUENCE_TRANSFORMER_REPRESENTATIONS == (
        "all100_sequence",
        "nearest_k80_sequence",
        "nearest_k60_sequence",
    )
    assert runner.SEQUENCE_TRANSFORMER_MODEL_KEYS == (
        "transformer_small",
        "transformer_medium",
        "sequence_flat_hist_gradient_boosting",
    )
    assert runner.SEQUENCE_TRANSFORMER_SEEDS == (42,)


def test_job_matrix_has_expected_size():
    jobs = runner.enumerate_sequence_transformer_jobs()
    assert len(jobs) == 9
    assert {(job["representation"], job["model_key"], job["seed"]) for job in jobs}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py::test_sequence_transformer_scope_is_bounded_and_isolated -q
```

Expected: FAIL because `benchmark_entry_based_sequence_transformer.py` does not exist.

- [ ] **Step 3: Implement minimal scope constants**

Create `ML/baseline/benchmark_entry_based_sequence_transformer.py` with:

```python
from __future__ import annotations

from itertools import product


SEQUENCE_TRANSFORMER_OUTPUT_PREFIX = "entry_based_sequence_transformer"
SEQUENCE_TRANSFORMER_REPRESENTATIONS = (
    "all100_sequence",
    "nearest_k80_sequence",
    "nearest_k60_sequence",
)
SEQUENCE_TRANSFORMER_MODEL_KEYS = (
    "transformer_small",
    "transformer_medium",
    "sequence_flat_hist_gradient_boosting",
)
SEQUENCE_TRANSFORMER_SEEDS = (42,)
TARGET_HORIZONS = (3, 6, 12, 24)
PREDICTED_TARGET_FAMILIES = ("entry_log_ratio", "entry_up", "entry_dn")


def enumerate_sequence_transformer_jobs() -> list[dict[str, object]]:
    return [
        {"representation": representation, "model_key": model_key, "seed": seed}
        for representation, model_key, seed in product(
            SEQUENCE_TRANSFORMER_REPRESENTATIONS,
            SEQUENCE_TRANSFORMER_MODEL_KEYS,
            SEQUENCE_TRANSFORMER_SEEDS,
        )
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py -q
```

Expected: PASS for the initial tests.

### Task 2: Sequence Tensor Builder Contract

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_sequence_transformer.py`
- Modify: `tests/test_entry_based_sequence_transformer.py`

**Interfaces:**
- Produces `TOKEN_FEATURE_NAMES: tuple[str, ...]`.
- Produces `build_sequence_tensor(frame: pandas.DataFrame, representation: str) -> SequenceTensor`.
- Produces dataclass `SequenceTensor(tokens: np.ndarray, mask: np.ndarray, feature_names: tuple[str, ...], representation: str)`.

- [ ] **Step 1: Write failing tests for shape, order and mask**

```python
import numpy as np
import pandas as pd

import ML.baseline.benchmark_entry_based_sequence_transformer as runner


def _fractal(t: int, price: float, direction: int, shift: int, up3: float = 0.1, dn3: float = 0.2) -> str:
    fields = [
        t, price, direction, 1.0, 2.0, 0, 1, 0.0, 3.0, 1, 0.5,
        0.4, 0.5, 0.6, 0.7, 0.8, 0.9, up3, dn3, 0.3, 0.35, 10.0, shift,
    ]
    return ":".join(str(x) for x in fields)


def test_build_sequence_tensor_uses_fractal_order_and_padding_mask():
    frame = pd.DataFrame(
        {
            "time": ["2020-01-01 12:00:00"],
            "ATR": [2.0],
            "fractal0": [_fractal(1000, 100.0, 1, 1)],
            "fractal1": [_fractal(900, 98.0, -1, 5)],
        }
    )
    for idx in range(2, 100):
        frame[f"fractal{idx}"] = [""]

    tensor = runner.build_sequence_tensor(frame, "all100_sequence")

    assert tensor.tokens.shape == (1, 100, len(runner.TOKEN_FEATURE_NAMES))
    assert tensor.mask.shape == (1, 100)
    assert tensor.mask[0, 0]
    assert tensor.mask[0, 1]
    assert not tensor.mask[0, 2]
    price_idx = runner.TOKEN_FEATURE_NAMES.index("price_coord_atr")
    direction_idx = runner.TOKEN_FEATURE_NAMES.index("direction")
    assert np.isclose(tensor.tokens[0, 0, price_idx], 0.0)
    assert np.isclose(tensor.tokens[0, 1, price_idx], -1.0)
    assert np.isclose(tensor.tokens[0, 0, direction_idx], 1.0)
    assert np.isclose(tensor.tokens[0, 1, direction_idx], -1.0)
    assert np.allclose(tensor.tokens[0, 2:, :], 0.0)


def test_fractal0_updn_fields_are_forced_to_zero_but_older_tokens_keep_values():
    frame = pd.DataFrame(
        {
            "time": ["2020-01-01 12:00:00"],
            "ATR": [2.0],
            "fractal0": [_fractal(1000, 100.0, 1, 1, up3=9.0, dn3=8.0)],
            "fractal1": [_fractal(900, 98.0, -1, 5, up3=0.7, dn3=0.8)],
        }
    )
    for idx in range(2, 100):
        frame[f"fractal{idx}"] = [""]

    tensor = runner.build_sequence_tensor(frame, "all100_sequence")

    up3_idx = runner.TOKEN_FEATURE_NAMES.index("up_3")
    dn3_idx = runner.TOKEN_FEATURE_NAMES.index("dn_3")
    assert tensor.tokens[0, 0, up3_idx] == 0.0
    assert tensor.tokens[0, 0, dn3_idx] == 0.0
    assert np.isclose(tensor.tokens[0, 1, up3_idx], 0.7)
    assert np.isclose(tensor.tokens[0, 1, dn3_idx], 0.8)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py::test_build_sequence_tensor_uses_fractal_order_and_padding_mask -q
```

Expected: FAIL because `build_sequence_tensor` is missing.

- [ ] **Step 3: Implement tensor builder**

Implement parser in the runner, reusing `ML.data_loader.parse_fractals_to_3d()` only if its output matches the contract. If reusing it, wrap it so the new runner owns the explicit `TOKEN_FEATURE_NAMES`, representation selection and audit metadata.

Required behavior:

```python
@dataclass(frozen=True)
class SequenceTensor:
    tokens: np.ndarray
    mask: np.ndarray
    feature_names: tuple[str, ...]
    representation: str


TOKEN_FEATURE_NAMES = (
    "direction",
    "front",
    "back",
    "strong",
    "break",
    "reverse",
    "power",
    "count",
    "impulse",
    "up_3",
    "dn_3",
    "up_6",
    "dn_6",
    "up_12",
    "dn_12",
    "up_24",
    "dn_24",
    "up_48",
    "dn_48",
    "log_fractal_atr_ratio",
    "log_shift",
    "log_delta_shift",
    "price_coord_atr",
    "abs_price_coord_atr",
    "dir_price_coord_atr",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
)
```

Implementation requirements:

- Parse only `time`, `ATR`, `fractal0..fractal99`.
- Treat missing/invalid fractal as padding.
- Require `ATR > 0` and valid `fractal0` for a row; invalid rows must be counted in preflight and excluded or abort according to the smoke-check rule.
- For `nearest_k80_sequence` and `nearest_k60_sequence`, select by absolute `price_coord_atr`, then restore original recency order before writing tokens.
- Pad back to 100 tokens with zeros and `mask=False`.
- Force `up_*`/`dn_*` token fields to `0.0` for token 0 / `fractal0`; preserve these fields for valid older tokens `fractal1..fractal99`.

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py -q
```

Expected: all current tests PASS.

### Task 3: Leakage, Split And Smoke-Check

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_sequence_transformer.py`
- Modify: `tests/test_entry_based_sequence_transformer.py`

**Interfaces:**
- Produces `FORBIDDEN_INPUT_COLUMN_PATTERNS: tuple[str, ...]`.
- Produces `run_sequence_smoke_check(splits: dict[str, pandas.DataFrame]) -> dict[str, object]`.
- Produces `split_horizon_overlap_check(splits: dict[str, pandas.DataFrame], horizons: tuple[int, ...]) -> dict[str, object]`.

- [ ] **Step 1: Write failing leakage and disclosure tests**

```python
import pandas as pd

import ML.baseline.benchmark_entry_based_sequence_transformer as runner


def test_forbidden_top_level_targets_are_not_sequence_inputs():
    forbidden_examples = [
        "up_24",
        "dn_24",
        "entry_up_24",
        "entry_dn_24",
        "entry_log_ratio_24",
        "ret_24_dir_atr",
        "fav_24_atr",
        "adv_24_atr",
        "predict",
        "signal",
    ]
    for column in forbidden_examples:
        assert runner.is_forbidden_input_column(column)


def test_low_n_disclosure_is_not_used_by_verdict():
    summary = runner.decide_sequence_verdict(
        rows=[
            {"representation": "nearest_k80_sequence", "target_family": "entry_log_ratio", "horizon": 24, "val_select": 0.01, "val_eval": -0.01, "low_n_disclosure": 0.50},
        ],
        smoke_check={"status": "PASS"},
        tensor_audit={"status": "PASS"},
    )
    assert summary["verdict"] == "REJECT_SEQUENCE_CAPACITY_EXPLANATION"


def test_low_n_disclosure_is_not_used_by_winner_selection():
    rows = [
        {"representation": "nearest_k80_sequence", "target_family": "entry_log_ratio", "horizon": 12, "val_select": 0.02, "val_eval": 0.01, "low_n_disclosure": 0.50},
        {"representation": "nearest_k60_sequence", "target_family": "entry_log_ratio", "horizon": 12, "val_select": 0.03, "val_eval": -0.01, "low_n_disclosure": -0.20},
    ]
    winner = runner.select_winner_by_policy(rows, selection_policy=runner.SELECTION_POLICY)
    assert winner["representation"] == "nearest_k60_sequence"
    assert winner["val_select"] == 0.03
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py::test_forbidden_top_level_targets_are_not_sequence_inputs tests/test_entry_based_sequence_transformer.py::test_low_n_disclosure_is_not_used_by_verdict -q
```

Expected: FAIL because helpers are missing.

- [ ] **Step 3: Implement smoke-check and verdict helper**

Required checks:

- no forbidden top-level columns in input allowlist;
- `entry_time > signal_time`;
- split time order is monotonic and non-overlapping;
- `train`, `val_select`, `val_eval`, `low_n_disclosure` row counts are recorded;
- target columns exist and have finite values;
- target variation is non-zero in train and validation;
- `low_n_disclosure` is never read in `decide_sequence_verdict()`.
- `low_n_disclosure` is never read in any winner-selection helper.
- `selection_policy` is written to JSON and used by selection helpers.

Required output:

```python
{
    "status": "PASS" | "FAIL",
    "checks": {...},
    "failures": [...],
}
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py -q
```

Expected: PASS.

### Task 4: Train-Only Normalization And Tensor Audit

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_sequence_transformer.py`
- Modify: `tests/test_entry_based_sequence_transformer.py`

**Interfaces:**
- Produces `fit_sequence_normalizer(train: SequenceTensor) -> SequenceNormalizer`.
- Produces `apply_sequence_normalizer(tensor: SequenceTensor, normalizer: SequenceNormalizer) -> SequenceTensor`.
- Produces `audit_sequence_tensor(tensors: dict[str, SequenceTensor]) -> dict[str, object]`.

- [ ] **Step 1: Write failing normalization tests**

```python
import numpy as np

import ML.baseline.benchmark_entry_based_sequence_transformer as runner


def test_normalizer_fits_only_valid_train_tokens_and_keeps_padding_zero():
    tokens = np.zeros((2, 3, 2), dtype=np.float32)
    tokens[0, 0] = [1.0, 10.0]
    tokens[0, 1] = [2.0, 20.0]
    tokens[1, 0] = [3.0, 30.0]
    mask = np.array([[True, True, False], [True, False, False]])
    train = runner.SequenceTensor(tokens=tokens, mask=mask, feature_names=("a", "b"), representation="unit")

    normalizer = runner.fit_sequence_normalizer(train)
    normalized = runner.apply_sequence_normalizer(train, normalizer)

    assert normalizer.fit_split == "train"
    assert normalizer.n_fit_tokens == 3
    assert np.allclose(normalized.tokens[~mask], 0.0)
    assert np.isfinite(normalized.tokens[mask]).all()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py::test_normalizer_fits_only_valid_train_tokens_and_keeps_padding_zero -q
```

Expected: FAIL because normalizer is missing.

- [ ] **Step 3: Implement normalization and audit**

Required normalizer contract:

```python
@dataclass(frozen=True)
class SequenceNormalizer:
    feature_names: tuple[str, ...]
    center: np.ndarray
    scale: np.ndarray
    fit_split: str
    n_fit_tokens: int
```

Use robust train-only scaling:

```text
center = train valid-token median
scale = train valid-token p75 - p25
scale floor = 1e-6
clip normalized values to [-10, 10]
padding remains exactly 0.0
```

Audit must include:

- split-level NaN/inf count;
- valid token rate;
- padding rate;
- per-field train/validation/2026 tail rates `abs(x)>3`, `abs(x)>5`, `abs(x)>10`;
- near-constant fields;
- `PADDING_NOT_ZERO` as `ERROR`;
- NaN/inf as `ERROR`;
- tail warnings as `WARNING`;
- explicit `audit_decisions`.

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py -q
```

Expected: PASS.

### Task 5: Transformer Training Loop

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_sequence_transformer.py`
- Modify: `tests/test_entry_based_sequence_transformer.py`

**Interfaces:**
- Produces `SequenceTransformerRegressor`.
- Produces `train_sequence_model(job: dict[str, object], data: PreparedSequenceData) -> dict[str, object]`.
- Produces predictions for all 12 target columns.

- [ ] **Step 1: Write failing model contract test**

```python
import torch

import ML.baseline.benchmark_entry_based_sequence_transformer as runner


def test_transformer_regressor_output_shape():
    model = runner.SequenceTransformerRegressor(input_features=5, output_dim=12, d_model=16, nhead=4, num_layers=1, dropout=0.0)
    x = torch.zeros((4, 100, 5), dtype=torch.float32)
    mask = torch.ones((4, 100), dtype=torch.bool)
    out = model(x, mask)
    assert out.shape == (4, 12)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py::test_transformer_regressor_output_shape -q
```

Expected: FAIL because `SequenceTransformerRegressor` is missing.

- [ ] **Step 3: Implement bounded model and loop**

Implementation requirements:

- Reuse `ML.models.transformer.PositionalEncoding`.
- Use one CLS token.
- Use `torch.nn.TransformerEncoder`.
- Output dimension is 12 target columns.
- Loss is MSE over normalized or raw target values, but target normalization must be separate from input normalization and fit only on train.
- First run uses fixed epochs and does not early-stop on validation.
- If a future implementation enables early stopping, it may use only a train-internal split from `train <= 2020`; it must not use `val_select`, `val_eval` or 2026.
- Default epochs: `60`.
- Batch size: `512` CPU, reduce only on memory failure and record actual value.
- Set `torch.set_num_threads(24)` by default and write actual thread count to JSON.
- Device default: CPU unless CUDA is explicitly available and selected by CLI.

Model skeleton:

```python
class SequenceTransformerRegressor(torch.nn.Module):
    def __init__(self, input_features: int, output_dim: int, d_model: int, nhead: int, num_layers: int, dropout: float):
        ...

    def forward(self, x: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
        ...
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py -q
```

Expected: PASS.

### Task 6: Metrics, Yearly Breakdown And Verdict

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_sequence_transformer.py`
- Modify: `tests/test_entry_based_sequence_transformer.py`

**Interfaces:**
- Produces `score_sequence_predictions(...) -> list[dict[str, object]]`.
- Produces `compute_yearly_metrics(...) -> dict[str, object]`.
- Produces `decide_sequence_verdict(...) -> dict[str, object]`.

- [ ] **Step 1: Write failing verdict tests**

```python
import ML.baseline.benchmark_entry_based_sequence_transformer as runner


def test_positive_direction_requires_replication_not_freeze():
    rows = [
        {
            "representation": "nearest_k80_sequence",
            "model_key": "transformer_small",
            "target_family": "entry_log_ratio",
            "horizon": 12,
            "val_select": 0.12,
            "val_eval": 0.06,
            "matching_all100_val_select": 0.03,
            "matching_all100_val_eval": 0.01,
            "simple_trade_val_select": 0.02,
            "simple_trade_val_eval": 0.01,
            "yearly_check_pass": True,
        }
    ]
    summary = runner.decide_sequence_verdict(rows, {"status": "PASS"}, {"status": "PASS"})
    assert summary["verdict"] == "DIRECTION_REPLICATION_REQUIRED"
    assert "FREEZE" not in summary["verdict"]


def test_all100_cannot_create_direction_replication_verdict():
    rows = [
        {
            "representation": "all100_sequence",
            "model_key": "transformer_small",
            "target_family": "entry_log_ratio",
            "horizon": 12,
            "val_select": 0.20,
            "val_eval": 0.10,
            "simple_trade_val_select": 0.02,
            "simple_trade_val_eval": 0.02,
            "yearly_check_pass": True,
        }
    ]
    summary = runner.decide_sequence_verdict(rows, {"status": "PASS"}, {"status": "PASS"})
    assert summary["verdict"] != "DIRECTION_REPLICATION_REQUIRED"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py::test_positive_direction_requires_replication_not_freeze tests/test_entry_based_sequence_transformer.py::test_all100_cannot_create_direction_replication_verdict -q
```

Expected: FAIL until verdict logic exists.

- [ ] **Step 3: Implement metrics and verdict**

Metric requirements:

- For each model/representation/seed/horizon/family compute:
  - `val_select`;
  - `val_eval`;
  - `low_n_disclosure`, stored but selection-forbidden;
  - `simple_trade_val_select`;
  - `simple_trade_val_eval`;
  - `yearly_metrics` for 2021-2025;
  - comparison to matching `all100_sequence`;
  - comparison to powerful-tabular and closeout baselines.
- Winner selection uses only `val_select` and gates.
- `best_by_val_eval` is written only as disclosure with `selection_forbidden=True`.

Verdict requirements:

- Smoke/tensor `FAIL` -> `ABORT_CONTRACT_FAIL`.
- Direction gates pass -> `DIRECTION_REPLICATION_REQUIRED`.
- Amplitude gates pass and direction fails -> `PIVOT_AMPLITUDE`.
- Otherwise -> `REJECT_SEQUENCE_CAPACITY_EXPLANATION`.

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py -q
```

Expected: PASS.

### Task 7: Resume, Config Hash And JSON Schema

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_sequence_transformer.py`
- Modify: `tests/test_entry_based_sequence_transformer.py`

**Interfaces:**
- Produces `build_run_config() -> dict[str, object]`.
- Produces `compute_run_config_hash(config: dict[str, object]) -> str`.
- Produces `save_sequence_report(report: dict[str, object], path: pathlib.Path) -> None`.
- Produces `load_resume_report(path: pathlib.Path, current_hash: str) -> dict[str, object]`.

- [ ] **Step 1: Write failing resume/schema tests**

```python
import json

import pytest

import ML.baseline.benchmark_entry_based_sequence_transformer as runner


def test_resume_rejects_different_config_hash(tmp_path):
    path = tmp_path / "report.json"
    path.write_text(json.dumps({"run_config_hash": "old", "runs": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="run_config_hash"):
        runner.load_resume_report(path, current_hash="new")


def test_report_has_top_level_machine_fields(tmp_path):
    path = tmp_path / "report.json"
    report = {
        "run_config": {"schema_version": 1, "dependency_versions": {"torch": "x"}},
        "summary": {"verdict": "REJECT_SEQUENCE_CAPACITY_EXPLANATION"},
        "normalization_contract": {"fit_split": "train"},
    }
    runner.save_sequence_report(report, path)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["schema_version"] == 1
    assert saved["verdict"] == "REJECT_SEQUENCE_CAPACITY_EXPLANATION"
    assert saved["dependency_versions"]["torch"] == "x"
    assert saved["normalization_contract"]["fit_split"] == "train"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py::test_resume_rejects_different_config_hash tests/test_entry_based_sequence_transformer.py::test_report_has_top_level_machine_fields -q
```

Expected: FAIL until JSON helpers exist.

- [ ] **Step 3: Implement resume and schema**

JSON must contain top-level:

```text
schema_version
verdict
dependency_versions
normalization_contract
target_normalization_contract
selection_policy
training_policy
run_config_hash
summary
run_config
progress
runs
failed_runs
entry_based_smoke_check
split_horizon_overlap_check
tensor_audit
metrics
best_by_val_select
best_by_val_eval_disclosure
yearly_metrics
```

Dependency versions must include:

```text
python
numpy
pandas
sklearn
torch
```

`selection_policy` must contain:

```text
winner_metric = val_select
val_eval = check_only
low_n_disclosure_2026 = disclosure_only
locked_test = not_opened
```

`training_policy` must contain:

```text
mode = fixed_epochs
epochs = 60
early_stopping = disabled
validation_used_for_early_stopping = false
```

`target_normalization_contract` must contain:

```text
fit_split = train
target_order = [12 target names in prediction order]
input_and_target_scalers_separate = true
inverse_transform_before_metrics = true
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py -q
```

Expected: PASS.

### Task 8: CLI Runner And Full Diagnostic Run

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_sequence_transformer.py`
- Modify: `tests/test_entry_based_sequence_transformer.py`

**Interfaces:**
- Produces CLI:
  - `--entry-based-sequence-transformer`
  - `--resume`
  - `--no-resume`
  - `--device {cpu,cuda,auto}`
  - `--threads`
  - `--max-epochs`
  - `--batch-size`

- [ ] **Step 1: Write CLI smoke test**

```python
import subprocess


def test_cli_help_lists_sequence_transformer_flag():
    result = subprocess.run(
        ["./.venv/bin/python", "ML/baseline/benchmark_entry_based_sequence_transformer.py", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "--entry-based-sequence-transformer" in result.stdout
    assert "--resume" in result.stdout
    assert "--no-resume" in result.stdout
```

- [ ] **Step 2: Run CLI smoke test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py::test_cli_help_lists_sequence_transformer_flag -q
```

Expected: PASS after CLI exists.

- [ ] **Step 3: Run focused tests before long training**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py -q
```

Expected: PASS.

- [ ] **Step 4: Start clean full run**

Before full run, ensure no stale sequence artifacts are reused. Do not delete closeout or powerful-tabular artifacts.

Run:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_sequence_transformer.py --entry-based-sequence-transformer --no-resume --device auto --threads 24
```

Expected:

- JSON exists at `ML/reports/entry_based_sequence_transformer.json`;
- `progress.done_runs == 9`;
- `failed_runs` is present even if empty;
- `entry_based_smoke_check.status == PASS`;
- `split_horizon_overlap_check.status == PASS`;
- `tensor_audit.status in {"PASS", "WARNING"}`;
- no `ERROR` in tensor audit;
- summary verdict is one of the allowed verdicts.

- [ ] **Step 5: Resume smoke test after completion**

Run:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_sequence_transformer.py --entry-based-sequence-transformer --resume --device auto --threads 24
```

Expected:

- already completed jobs are skipped;
- JSON remains schema-compatible;
- no duplicate runs are appended.

### Task 9: Report, Docs And Wiki Sync

**Files:**
- Create: `docs/reports/2026-07-06-entry-based-fractal-sequence-transformer.md`
- Create: `docs/ML/benchmark_entry_based_sequence_transformer.py.md`
- Modify: `docs/tests/tests.md`
- Modify: `MODULE_INDEX.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

**Interfaces:**
- Produces final human report and documentation cross-links.

- [ ] **Step 1: Write report from JSON, not by memory**

The report must include:

- context and stage level;
- exact command;
- split disclosure;
- input tensor contract;
- token feature table;
- normalization contract;
- tensor audit summary;
- full search width;
- dependency versions;
- progress and failed runs;
- best selected row by `val_select`;
- overall table including `all100_sequence`;
- candidate-only table excluding `all100_sequence`;
- best by `val_eval` as disclosure-only;
- comparison against powerful-tabular protocol-selected baseline;
- disclosure of previous powerful-tabular best-by-`val_eval` row as selection-forbidden;
- comparison against closeout baseline;
- `time_only_clean` / `no_time_sequence` control section;
- section “What would falsify the sequence-capacity explanation”;
- yearly metrics table;
- 2026 disclosure section explaining why it cannot change verdict;
- simple_trade warning;
- verdict and next step;
- limitations.

- [ ] **Step 2: Add module documentation**

Document:

- what the runner does;
- how sequence input differs from flat tabular input;
- allowed and forbidden input fields;
- output artifacts;
- CLI examples;
- resume behavior;
- interpretation limits.

- [ ] **Step 3: Update test docs and module index**

Add:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py -q
```

Add new runner and test entries to `MODULE_INDEX.md` following current format.

- [ ] **Step 4: Update changelog, handoff and wiki**

Use project wiki tooling:

```bash
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

- [ ] **Step 5: Final verification**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py -q
./.venv/bin/python -m pytest tests/ -q
git diff --check
./.venv/bin/python wiki/wiki.py status
```

Expected:

- focused tests pass;
- full tests pass;
- `git diff --check` clean;
- wiki status clean.

## Discussion Points Before Implementation

These are the only design choices worth discussing before coding:

1. Whether to keep `nearest_k60_sequence` and `nearest_k80_sequence` in the first run, or start with `all100_sequence` only. My recommendation is to keep all three: it directly answers whether the best tabular candidates lost sequence information.
2. Whether to include `fractal0` `Up/Dn` in the main token fields. My recommendation is no: keep them excluded or separately zeroed for `fractal0`, because newly born `fractal0` reaction fields are not a useful historical state.
3. Whether to use CUDA if available. My recommendation is `--device auto`, but record the device and keep CPU fallback mandatory.
4. Whether to add `corridor_5atr_sequence`. My recommendation is no for this first run: it adds coverage/distribution risk and widens the search after a post-hoc stage.

## Self-Review

- Spec coverage: plan covers sequence input, feature contract, split policy, train-only normalization, tensor audit, Transformer training, metrics, yearly breakdown, disclosure-only 2026, JSON schema, resume and reporting.
- Placeholder scan: no `TBD`, no open-ended “add tests” step without concrete tests, no freeze-like verdict.
- Type consistency: `SequenceTensor`, `SequenceNormalizer`, `build_sequence_tensor`, `fit_sequence_normalizer`, `apply_sequence_normalizer`, `audit_sequence_tensor`, `decide_sequence_verdict` are introduced before later tasks use them.
