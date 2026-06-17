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
- `docs/methodology/A6-fractal-feature-profile-catalog.md` — каталог вариантов представления фракталов и рекомендуемая стартовая матрица для Transformer.

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

**Why train <=2020** (not <=2016 as in Stage 4.2): Transformer needs more data than XGBoost to learn sequence patterns. 2019–2020 were previously XGBoost validation (not frozen test), so repurposing them for Transformer training does not leak test information. The cost is a shorter val_stop (2 years vs 4), which is acceptable because early stopping requires a clean signal, not a large sample.

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

All feature profiles must be fixed before training. Profile design follows `docs/methodology/A6-fractal-feature-profile-catalog.md`.

### Shared Input Rules

- Sequence order depends on profile: `fractal0` is newest token for `all100`/`newest` profiles; order by price distance for `nearest`/`corridor` profiles.
- `seq_len`: primary is `100` for `all100` profiles; `newest20` uses `20`; `nearest40`/`corridor` profiles pad or truncate to fixed length.
- Missing or malformed tokens must be represented by a mask, not silently converted into meaningful zeros.
- For `corridor_*` and `nearest_*` profiles: if fewer tokens than `seq_len`, pad with zeros + validity mask; if more, truncate by fixed rule (closest by price).
- Row-level features (`ATR`, hour, day-of-week) must be separate from fractal-token features so time-only and no-time controls are clean.
- Fit any scaler/normalizer on train only; apply to val_stop and holdout.

### Profile Matrix

| # | Profile | Selection | Order | Token Features | Row Features | Purpose |
|---|---|---|---|---|---|---|
| 1 | `all100_base10_time` | All 100 fractals | By freshness (newest first) | price, direction, front, back, strong, break, reverse, power, count, impulse | ATR + hour/dow sin/cos | Baseline comparable to Stage 4 XGBoost |
| 2 | `all100_base10_no_time` | All 100 fractals | By freshness | same 10 token features | ATR only | Calendar control: tests fractal signal without time |
| 3 | `newest20_base10_time` | 20 newest fractals | By freshness | same 10 token features | ATR + hour/dow sin/cos | Tests whether only recent fractals suffice |
| 4 | `nearest40_base10_time` | 40 fractals closest to fractal0.price | By price distance (ascending) | same 10 token features | ATR + hour/dow sin/cos | Tests price proximity vs freshness |
| 5 | `corridor_10atr_base10_time` | Fractals within ±10 ATR of fractal0.price | By price distance (ascending) | same 10 token features | ATR + hour/dow sin/cos | Tests wide market context around level |
| 6 | `corridor_ablation` | 3 sub-profiles: ±5, ±10, ±15 ATR | By price distance | same 10 token features | ATR + hour/dow sin/cos | Tests corridor width (5/10/15 ATR) |

Optional (only if compute budget allows and declared before run):

| # | Profile | Selection | Order | Token Features | Row Features | Purpose |
|---|---|---|---|---|---|---|
| 7 | `all100_full29_time` | All 100 fractals | By freshness | Full 29-feature contract from data_loader.py | ATR + hour/dow sin/cos | Tests whether extended features help Transformer |
| 8 | `all100_base10_no_price_time` | All 100 fractals | By freshness | direction, front, back, strong, break, reverse, power, count, impulse (9 features, no price) | ATR + hour/dow sin/cos | Stage 5-prep finding: removing price improved XGBoost AUC +32 bp |

### Fixed SeqLen Per Profile

| Profile | seq_len | Rationale |
|---|---|---|
| `all100_*` | 100 | Full fractal list |
| `newest20_*` | 20 | First 20 fractals |
| `nearest40_*` | 40 | Fixed k=40 |
| `corridor_5atr` | 30 | Conservative; refine after corridor validation stats |
| `corridor_10atr` | 40 | Based on A6 recommended corridor width; refine after validation |
| `corridor_15atr` | 50 | Wide corridor; refine after validation |

All corridor seq_len values may be adjusted after mandatory corridor validation (see Corridor Validation section). Rule: set seq_len = min(N, P80 of observed fractal count) where N is the pre-declared value above. If P80 < seq_len, reduce seq_len to P80 to avoid excessive padding. If P80 > seq_len, keep seq_len and truncate by closest-to-fractal0.

Do not add profiles after seeing holdout results.

### Corridor Validation (mandatory for corridor profiles)

Before training any `corridor_*` profile, compute and report:

```python
corridor_stats = {
    "profile": str,
    "n_rows_total": int,
    "n_fractals_p5": float,
    "n_fractals_p25": float,
    "n_fractals_median": float,
    "n_fractals_p75": float,
    "n_fractals_p95": float,
    "pct_empty": float,      # 0 fractals after selection
    "pct_single": float,     # 1 fractal
    "pct_two": float,        # 2 fractals
    "pct_three_plus": float, # 3+ fractals
}
```

Status rules:

- If `pct_empty > 5%` or `median < 3`: profile gets `LOW_COVERAGE` status; result is diagnostic only.
- If `pct_empty > 20%` or `median < 2`: profile is `REJECTED` before training.
- Report corridor stats separately for train, val_stop, holdout.

### Phased Execution

Do not launch all profiles at once. Follow phases:

**Phase 1 — Baseline check:**
1. `all100_base10_time` + `all100_base10_no_time`
2. Compare with XGBoost baselines
3. Stop condition: halt only if Transformer AUC on val_stop trails XGBoost by >0.03 (clear underperformance). If gap is within ±0.02 (near-parity), continue — val_stop is only 2 years and may not be representative.

**Phase 2 — Selection variations:**
4. `newest20_base10_time`
5. `nearest40_base10_time`
6. `corridor_10atr_base10_time` (with corridor validation)

**Phase 3 — Corridor ablation (only if corridor_10atr looks promising):**
7. `corridor_ablation` (5/10/15 ATR)

**Phase 4 — Optional extended features (only if Phase 1-2 show clear benefit):**
8. `all100_full29_time`
9. `all100_base10_no_price_time` — tests Stage 5-prep finding (removing price improved AUC +32 bp for XGBoost)

**Expected training budget:**
- Phase 1-2: 5 profiles × 3 seeds = 15 Transformer runs
- Phase 3: 2 additional sub-profiles × 3 seeds = 6 runs
- Phase 4: 2 optional profiles × 3 seeds = 6 runs
- XGBoost baselines: 3 refits (time_only, base_raw_plus_time, no_time)
- Total worst-case: ~27 Transformer runs + 3 XGBoost refits
- With single seed (GPU unavailable): ~9 Transformer runs

### Feature Interpretation Requirements

Report separately:

- whether time features dominate (compare profile 1 vs 2);
- whether selection strategy matters (compare profiles 1 vs 3 vs 4 vs 5);
- whether corridor width matters (compare sub-profiles in profile 6);
- whether extended features help (compare profile 1 vs 7 if run);
- whether removing price helps Transformer (compare profile 1 vs 8 if run — Stage 5-prep hypothesis);
- whether Transformer beats `time_only` by enough margin to justify sequence modeling.

Note: `zones_plus_nearest` (A6 recommendation) is omitted because zones are aggregated table features, not sequence input — they don't test Transformer's sequence-modeling capability. May be added in Stage 5.1 if Transformer shows promise.

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

For `nearest_*` and `corridor_*` profiles: positional encoding is learned position (0..seq_len-1), not fractal index. This allows the model to learn relative position within the selected subset.

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
  - Assert all 6 required profile names are present.
  - Assert each profile declares: `selection`, `order`, `token_fields`, `row_fields`, `uses_time`, `seq_len`.
  - Assert no profile is created dynamically from results.

- [ ] **Step 2: Write tests for tensor shapes**
  - Small DataFrame with `fractal0..fractal5`, `ATR`, `time`.
  - For each profile type, feature builder returns:
    - `tokens`: `(n, seq_len, dim)`;
    - `row_features`: `(n, row_dim)`;
    - `mask`: `(n, seq_len)`.
  - For `corridor_*` profiles: test with 0, 1, 5, 10 fractals in corridor.

- [ ] **Step 3: Write tests for profile contracts**
  - `all100_base10_no_time` must not include hour/dow fields.
  - `nearest40_base10_time` must order tokens by price distance.
  - `corridor_10atr_base10_time` must exclude fractals outside ±10 ATR.
  - `newest20_base10_time` must use only first 20 fractals.

- [ ] **Step 4: Write tests for corridor validation**
  - Empty corridor (0 fractals) produces valid mask.
  - Single-fractal corridor does not produce NaN.
  - `LOW_COVERAGE` threshold triggers correctly.
  - `REJECTED` threshold triggers correctly.

- [ ] **Step 5: Write tests for split guard**
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
  - Support variable `seq_len` (100 for all100, 20 for newest20, 40 for nearest40/corridor).

- [ ] **Step 2: Implement masked pooling**
  - Masked mean over valid tokens (mask=1).
  - Concat with newest valid token representation.
  - Handle edge case: all tokens masked (use zero vector + row features only).

- [ ] **Step 3: Implement corridor/nearest token selection**
  - `select_by_corridor(fractals, fractal0_price, atr, corridor_atr)`: returns indices within ±corridor_atr.
  - `select_by_nearest(fractals, fractal0_price, k)`: returns k closest by price.
  - Order selected tokens by distance (ascending) for corridor/nearest profiles.

- [ ] **Step 4: Add unit tests**
  - Forward pass works with partial mask.
  - Fully invalid token row does not produce NaN.
  - Output shape stable for all profile types.
  - Corridor selection correctly excludes tokens outside ATR range.

---

## Task 4: Train/Evaluate Fixed Feature Profiles

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`

- [ ] **Step 1: Implement train loop**
  - Train on <=2020.
  - Early stopping on 2021-2022 only.
  - No holdout feedback.

- [ ] **Step 2: Run Phase 1 (baseline check)**
  - `all100_base10_time`
  - `all100_base10_no_time`
  - Compare with XGBoost baselines on val_stop.
  - **Stop condition:** halt only if Transformer AUC on val_stop trails XGBoost by >0.03. If gap is within ±0.02, continue — val_stop is only 2 years and may not be representative.

- [ ] **Step 3: Run Phase 2 (selection variations)**
  - `newest20_base10_time`
  - `nearest40_base10_time`
  - `corridor_10atr_base10_time` (with mandatory corridor validation)

- [ ] **Step 4: Run Phase 3 (corridor ablation, conditional)**
  - Only if `corridor_10atr` shows promise in Phase 2.
  - Run `corridor_5atr`, `corridor_15atr` as sub-profiles.

- [ ] **Step 5: Run Phase 4 (optional, conditional)**
  - Only if Phase 1-2 show clear Transformer benefit.
  - `all100_full29_time`
  - `all100_base10_no_price_time`

- [ ] **Step 6: Run seeds**
  - Primary: seeds `[42, 77, 123]`.
  - If compute limited, run seed `42` first, mark result `single_seed_diagnostic`, and do not promote to pass.

- [ ] **Step 7: Evaluate on holdout 2023-2026**
  - AUC, PR-AUC, lift bottom 10/20/30.
  - yearly AUC / PR-AUC / lift.
  - calibration buckets.
  - prediction distribution summary.
  - For corridor profiles: corridor stats on holdout.

- [ ] **Step 8: Aggregate**
  - Mean and min across seeds.
  - Compare each Transformer profile with all baselines.
  - Rank profiles by holdout AUC and lift.

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
    - `feature_profiles` (with corridor_stats for corridor profiles);
    - `baselines`;
    - `transformer_results`;
    - `holdout_gate`;
    - `optional_walk_forward` if run;
    - `interpretation_guards`.

- [ ] **Step 2: Report sections**
  - Context.
  - Why holdout first and walk-forward optional.
  - Feature profiles and phased execution rationale (per A6).
  - Corridor validation results.
  - Baselines.
  - Transformer results by phase.
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

- Feature profiles are fixed before running and follow A6 recommendations.
- Corridor profiles have mandatory validation stats.
- Phased execution is respected (stop early if Phase 1 fails).
- Baselines include `time_only`, `xgb_base_raw_plus_time`, and `xgb_no_time`.
- Main verdict is based on 2023-2026 holdout, not on best historical window.
- Walk-forward is optional and only diagnostic.
- No trading rule is selected.
- All artifacts are indexed and verified.
