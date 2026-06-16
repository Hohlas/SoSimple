# Stage 5.0 Transformer Breach Holdout Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking. Do not commit unless the user explicitly asks.

**Goal:** Проверить, даёт ли Transformer на последовательности фракталов устойчивое улучшение `breach`-ранжирования на holdout 2023-2026 по сравнению с XGBoost и календарными baseline.

**Architecture:** Stage 5.0 — только модельный слой, без торгового grid search и без выбора production winner. Основной gate — один честный holdout 2023-2026. Walk-forward выполняется только как optional diagnostics, если Transformer выглядит перспективно или результат неоднозначен.

**Tech Stack:** Python 3.10+, pandas, numpy, scikit-learn, XGBoost, PyTorch. Использовать `~/git/SoSimple/.venv/bin/python`.

---

## Source Of Truth

- `docs/reports/2026-06-15-walk-forward-diagnostics.md` — дообучение XGBoost не спасло 2023-2026.
- `docs/reports/2026-06-15-stage5-prep-diagnostics.md` — календарный риск и AUC→PF gap.
- `docs/reports/2026-06-15-stage4_6-clean-candidate-cycle.md` — `trail_atr_0_2` прошёл 2019-2022, провалил 2023-2026.
- `ML/baseline/diagnose_stage5_prep.py` — XGBoost/time baseline extraction.
- `ML/baseline/diagnose_walk_forward.py` — текущая логика holdout 2023-2026.
- `ML/data_loader.py` — существующий parser `fractal0..fractal99` в 3D tensor.
- `ML/models/transformer.py` и похожие модели в `ML/models/` — существующие Transformer patterns.
- `docs/methodology/08-model-development.md` — обучение моделей.
- `docs/methodology/09-validation-freeze.md` — selection/freeze.
- `docs/methodology/11-robustness.md` — calendar risk, walk-forward interpretation.
- `docs/methodology/16-reporting-audit.md` — отчётность и сверка JSON.

## Hard Boundaries

- Не запускать торговый слой в Stage 5.0.
- Не подбирать `p`, `min_fav`, `min_rr`, TP, trailing или spread-политику.
- Не объявлять production/frozen winner.
- Не расширять feature profiles после просмотра holdout.
- Не использовать 2023-2026 для ручной подгонки архитектуры. Все профили и gates фиксируются до запуска.
- Результат Stage 5.0 получает максимум `MODEL_PASS_DIAGNOSTIC`; торговый candidate требует отдельного Stage 5.1.

## Key Decision

Stage 5.0 использует **обычный holdout 2023-2026 как главный gate**, а не полный walk-forward.

Walk-forward — optional Task:

- выполнять только если Transformer проходит или почти проходит holdout gate;
- выполнять только для подтверждения переносимости;
- не выбирать winner по лучшему walk-forward окну.

## Files

| File | Action | Purpose |
|---|---|---|
| `ML/baseline/benchmark_stage5_transformer_breach.py` | Create | Main Stage 5.0 runner |
| `ML/models/fractal_breach_transformer.py` | Create | Small Transformer encoder for breach classification |
| `ML/reports/stage5_transformer_breach.json` | Generate | Structured results |
| `docs/reports/2026-06-16-stage5-transformer-breach.md` | Create | Canonical report |
| `docs/ML/benchmark_stage5_transformer_breach.py.md` | Create | Runner documentation |
| `docs/ML/fractal_breach_transformer.py.md` | Create | Model documentation |
| `tests/test_stage5_transformer_breach.py` | Create | Feature/profile/model smoke tests |
| `MODULE_INDEX.md` | Modify | Register new runner/model/docs |
| `wiki/research/fractal-stop-research.md` | Modify after report | Wiki ingest |
| `wiki/index.md`, `wiki/log.md` | Modify after report | Wiki navigation/log |

---

## Experimental Design

### Target

Primary target:

```text
sell_H6_off05
```

Reason:

- inherited from Stage 4.2/4.4/4.6;
- same target where trailing diagnostics were evaluated;
- avoids opening a new target search.

Optional secondary target metrics may be computed for the same model family only if already fixed before run:

```text
sell_H6_off02
sell_H12_off02
sell_H12_off05
```

But secondary targets are diagnostic only and cannot override the primary verdict.

### Split

Primary holdout protocol:

| Role | Years | Source | Use |
|---|---|---|---|
| train | <=2020 | labeled CSVs | fit model weights |
| val_stop | 2021-2022 | labeled CSVs | early stopping / epoch selection |
| holdout_eval | 2023-2026 | `MT/MQL4/Files/Nero.csv` + generated breach labels or equivalent OHLC-derived labels | final Stage 5.0 model diagnostic |

Important:

- If 2023-2026 breach labels are not already present, generate them deterministically from OHLC using the same Stage 1 `breach` label contract.
- Do not use 2023-2026 to tune architecture, feature profile, threshold, or training hyperparameters.
- Report must state that 2023-2026 is a diagnostic holdout already used in Stage 4.6/walk-forward; it is not a clean future test for later manual tuning.

### Baselines

Every Transformer profile is compared against:

1. `dummy_prior`: constant probability / class prior.
2. `time_only_xgb`: 4 row-level time features.
3. `xgb_base_raw_plus_time`: current best tabular baseline.
4. `xgb_no_time`: tabular baseline without row-level time features.

### Main Metrics

Model metrics only:

- AUC;
- PR-AUC;
- lift in low-risk working zone for `predict_break`:
  - bottom 10%;
  - bottom 20%;
  - bottom 30%;
- yearly AUC and yearly lift;
- calibration buckets;
- prediction coverage and valid-row count.

No PF gate in Stage 5.0.

### Primary Gate

Transformer passes Stage 5.0 only if the primary profile satisfies all:

```text
holdout AUC >= max(xgb_base_raw_plus_time_auc + 0.02, time_only_auc + 0.04)
holdout lift_bottom30 >= xgb_base_raw_plus_time_lift_bottom30 + 0.10
yearly AUC >= 0.55 in at least 3 of 4 holdout years with enough samples
calibration not inverted in working low-risk zone
```

If AUC improves but lift in the working zone does not improve, verdict is `MODEL_FAIL_FOR_TRADING_USE`.

If 2026 has too few rows, report 2026 separately and do not let it dominate the yearly gate.

### Near-Pass

Near-pass means:

```text
holdout AUC improvement over XGBoost is 0.01-0.02
or
lift improves but yearly slices are mixed
```

Near-pass does not allow trading. It only allows optional walk-forward diagnostics.

---

## Feature Profiles

All feature profiles must be fixed before training.

### Shared Input Rules

- Sequence order: `fractal0` is newest token, `fractal99` oldest token.
- `seq_len`: run fixed profiles with `20` and `100` only if compute budget allows. Primary is `seq_len=100`; `seq_len=20` is a compact diagnostic.
- Missing or malformed tokens must be represented by a mask, not silently converted into meaningful zeros.
- Row-level features (`ATR`, hour, day-of-week) must be separate from fractal-token features so time-only and no-time controls are clean.
- Fit any scaler/normalizer on train only; apply to val_stop and holdout.

### Profile Matrix

| Profile | Tokens | Token Features | Row Features | Purpose |
|---|---:|---|---|---|
| `T_base10_time` | 100 | price, direction, front, back, strong, break, reverse, power, count, impulse | ATR + hour/dow sin/cos | Main Transformer profile comparable to Stage 4 XGBoost |
| `T_base10_no_time` | 100 | same 10 token features | ATR only | Tests whether Transformer extracts fractal signal without calendar |
| `T_no_price_time` | 100 | direction, front, back, strong, break, reverse, power, count, impulse | ATR + hour/dow sin/cos | Tests Stage 5-prep finding that raw price may add noise |
| `T_geometry_only` | 100 | direction, front, back, strong, break, power, impulse, relative price to fractal0 in ATR if available | ATR only | Tests structural fractal geometry without calendar dominance |
| `T_path_compact` | 100 | base10 + folded `mov_3/6/12/24/48` + shift + fractal_atr/current_ATR | ATR + hour/dow sin/cos | Optional high-dimensional profile; run only after fixed budget approval |
| `T_time_token_only` | 100 | direction only or zero token payload | ATR + hour/dow sin/cos | Negative control: ensures Transformer is not just a time wrapper |

Do not add profiles after seeing holdout results.

### Feature Interpretation Requirements

Report separately:

- whether time features dominate;
- whether removing price helps;
- whether path/shift/ATR-ratio helps or adds noise;
- whether Transformer beats `time_only` by enough margin to justify sequence modeling.

---

## Model Design

Use a small, regularized Transformer first.

Primary architecture:

```text
token_projection: Linear(input_dim -> d_model)
positional_encoding: learned position embedding for fractal level 0..99
encoder: 2 layers, d_model=64, nhead=4, dropout=0.15
pooling: masked mean + newest-token embedding concat
row_feature_mlp: small MLP for ATR/time row features
head: binary classifier, BCEWithLogitsLoss
```

Fixed training budget:

```text
seeds: [42, 77, 123]
max_epochs: 60
early_stopping_patience: 8
batch_size: 256 or max feasible
optimizer: AdamW
learning_rate: 1e-3
weight_decay: 1e-4
class_weight: pos_weight from train only
```

If GPU is unavailable, reduce seeds to `[42]` and state compute limitation in the report.

---

## Task 1: Feature Contract And Tests

**Files:**
- Create: `tests/test_stage5_transformer_breach.py`
- Create/modify: `ML/baseline/benchmark_stage5_transformer_breach.py`

- [ ] **Step 1: Write tests for feature profile definitions**
  - Assert all fixed profile names are present.
  - Assert each profile declares token fields, row fields, `uses_time`, `uses_price`.
  - Assert no profile is created dynamically from results.

- [ ] **Step 2: Write tests for tensor shapes**
  - Small DataFrame with `fractal0..fractal2`, `ATR`, `time`.
  - Feature builder returns:
    - `tokens`: `(n, seq_len, dim)`;
    - `row_features`: `(n, row_dim)`;
    - `mask`: `(n, seq_len)`.

- [ ] **Step 3: Write tests for no-time/no-price contracts**
  - `T_base10_no_time` must not include hour/dow fields.
  - `T_no_price_time` must not include token `price`.
  - `T_time_token_only` must not include rich fractal payload.

- [ ] **Step 4: Write tests for split guard**
  - Holdout rows must never be used in train or val_stop.
  - Any scaler fit metadata must report train-only fit period.

---

## Task 2: Baseline Reproduction

**Files:**
- Create: `ML/baseline/benchmark_stage5_transformer_breach.py`

- [ ] **Step 1: Load datasets**
  - labeled train/validation CSVs;
  - Nero.csv for 2023-2026;
  - OHLC for deterministic breach labels if needed.

- [ ] **Step 2: Reproduce XGBoost baselines**
  - `time_only_xgb`.
  - `xgb_base_raw_plus_time`.
  - `xgb_no_time`.

- [ ] **Step 3: Save baseline metrics**
  - AUC, PR-AUC, lift bottom 10/20/30, yearly AUC, calibration buckets.

- [ ] **Step 4: Stop on mismatch**
  - If `xgb_base_raw_plus_time` differs materially from the latest diagnostic baseline, stop and explain whether split/protocol changed.

---

## Task 3: Transformer Model Implementation

**Files:**
- Create: `ML/models/fractal_breach_transformer.py`
- Test: `tests/test_stage5_transformer_breach.py`

- [ ] **Step 1: Implement model class**
  - Inputs: `tokens`, `row_features`, `mask`.
  - Outputs: logits shape `(batch,)`.

- [ ] **Step 2: Implement masked pooling**
  - Masked mean over valid tokens.
  - Concat with newest valid token representation.

- [ ] **Step 3: Add unit tests**
  - Forward pass works with partial mask.
  - Fully invalid token row does not produce NaN.
  - Output shape stable.

---

## Task 4: Train/Evaluate Fixed Feature Profiles

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`

- [ ] **Step 1: Implement train loop**
  - Train on <=2020.
  - Early stopping on 2021-2022 only.
  - No holdout feedback.

- [ ] **Step 2: Run fixed profiles**
  - Required:
    - `T_base10_time`;
    - `T_base10_no_time`;
    - `T_no_price_time`;
    - `T_geometry_only`;
    - `T_time_token_only`.
  - Optional only if compute budget allows and declared before run:
    - `T_path_compact`.

- [ ] **Step 3: Run seeds**
  - Primary: seeds `[42, 77, 123]`.
  - If compute limited, run seed `42` first, mark result `single_seed_diagnostic`, and do not promote to pass.

- [ ] **Step 4: Evaluate on holdout 2023-2026**
  - AUC, PR-AUC, lift bottom 10/20/30.
  - yearly AUC / PR-AUC / lift.
  - calibration buckets.
  - prediction distribution summary.

- [ ] **Step 5: Aggregate**
  - Mean and min across seeds.
  - Compare each Transformer profile with all baselines.

---

## Task 5: Optional Walk-Forward Diagnostics

**Trigger:** Run this task only if Task 4 is `PASS` or `NEAR_PASS`.

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`

- [ ] **Step 1: Fixed windows**
  - `train <=2016 -> eval 2017-2018`
  - `train <=2018 -> eval 2019-2020`
  - `train <=2020 -> eval 2021-2022`
  - `train <=2022 -> eval 2023-2026`

- [ ] **Step 2: Run only selected profile family**
  - Use the best pre-declared profile from Task 4.
  - Do not add new profiles.

- [ ] **Step 3: Interpret correctly**
  - Do not pick winner from best window.
  - Report how many windows beat XGBoost/time-only.
  - Report whether late window still improves.

- [ ] **Step 4: Stop condition**
  - If Transformer only improves 2019-2022 but not 2023-2026, reject trading progression.

---

## Task 6: JSON, Report, Docs

**Files:**
- Generate: `ML/reports/stage5_transformer_breach.json`
- Create: `docs/reports/2026-06-16-stage5-transformer-breach.md`
- Create: `docs/ML/benchmark_stage5_transformer_breach.py.md`
- Create: `docs/ML/fractal_breach_transformer.py.md`

- [ ] **Step 1: JSON schema**
  - Include:
    - `status`;
    - `config`;
    - `split`;
    - `feature_profiles`;
    - `baselines`;
    - `transformer_results`;
    - `holdout_gate`;
    - `optional_walk_forward` if run;
    - `interpretation_guards`.

- [ ] **Step 2: Report sections**
  - Context.
  - Why holdout first and walk-forward optional.
  - Feature profiles and fixed search budget.
  - Baselines.
  - Transformer results.
  - Gate verdict.
  - Non-conclusions.
  - Next step.

- [ ] **Step 3: Required non-conclusions**
  - No trading winner.
  - No trading PF claim.
  - 2023-2026 was used as diagnostic holdout and cannot be reused for tuning.
  - If optional walk-forward was skipped, state why.

---

## Task 7: Index, Wiki, Verification

**Files:**
- Modify: `MODULE_INDEX.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`

- [ ] **Step 1: MODULE_INDEX**
  - Add runner and model docs.

- [ ] **Step 2: Wiki ingest**
  - Add Stage 5.0 summary to `wiki/research/fractal-stop-research.md`.
  - Update `wiki/index.md`.
  - Append `wiki/log.md`.

- [ ] **Step 3: Verification commands**
  - `~/git/SoSimple/.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -q`
  - `~/git/SoSimple/.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach`
  - `~/git/SoSimple/.venv/bin/python -m json.tool ML/reports/stage5_transformer_breach.json`
  - `git diff --check`
  - `~/git/SoSimple/.venv/bin/python wiki/wiki.py generate`
  - `~/git/SoSimple/.venv/bin/python wiki/wiki.py verify`
  - `knowledge-rag reindex_documents(force=True)`

## Verdict Rules

### PASS

All primary gates pass on 2023-2026 holdout, and yearly slices are not concentrated in one year.

Next:

- write Stage 5.1 trading-layer plan;
- trading layer may test fixed TP R=0.7 baseline first;
- trailing remains separate execution-policy diagnostic unless explicitly included in Stage 5.1 plan.

### NEAR_PASS

Transformer improves over XGBoost but fails one non-critical gate.

Next:

- run optional walk-forward diagnostics;
- do not run trading layer yet.

### FAIL

Transformer does not beat XGBoost/time-only on 2023-2026, or improvement is only calendar/time-like.

Next:

- do not build Stage 5.1 trading layer;
- either redesign target/features or close Fractal Stop as a trading branch.

## Acceptance Criteria

- Feature profiles are fixed before running.
- Baselines include `time_only`, `xgb_base_raw_plus_time`, and `xgb_no_time`.
- Main verdict is based on 2023-2026 holdout, not on best historical window.
- Walk-forward is optional and only diagnostic.
- No trading rule is selected.
- All artifacts are indexed and verified.
