# Stage 5.0 Prep Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking. Do not commit unless the user explicitly asks.

**Goal:** Проверить две подготовительные гипотезы перед Stage 5.0 Transformer: на каких признаках держится breach-модель и какой прирост breach-ранжирования теоретически нужен для PF-gate.

**Architecture:** Один diagnostic runner воспроизводит Stage 4.2/4.4 baseline (`sell_H6_off05`) и выполняет две группы проверок: feature ablation для XGBoost breach и oracle-like AUC→PF sensitivity. Результат имеет только статус `DIAGNOSTIC_ONLY`: test не открывать, winner не выбирать.

**Tech Stack:** Python 3.10+, pandas, numpy, XGBoost, scikit-learn. Использовать `~/git/SoSimple/.venv/bin/python`.

---

## Source Of Truth

- `docs/audit/to_do.md` — пункты `Stage 5.0-prep: breach feature ablation` и `Stage 5.0-prep: AUC→PF sensitivity`.
- `docs/reports/2026-06-15-stage4_4-micro-check.md` — текущий baseline и выводы.
- `ML/baseline/diagnose_stage4_4.py` — эталонный runner Stage 4.4.
- `docs/methodology/11-robustness.md` — проверка календарных признаков и permutation.
- `docs/methodology/A5-post-mortem-diagnostics.md` — статус `DIAGNOSTIC_ONLY`.

## Hard Boundaries

- Не открывать test.
- Не выбирать нового торгового winner.
- Не менять execution contract.
- Не запускать новый trading grid search.
- Не трактовать oracle-like sensitivity как достижимое качество модели.
- Все выводы использовать только для дизайна Stage 5.0 Transformer.

## Files

| File | Action | Purpose |
|---|---|---|
| `ML/baseline/diagnose_stage5_prep.py` | Create | Feature ablation + AUC→PF sensitivity runner |
| `ML/reports/stage5_prep_diagnostics.json` | Generate | Structured diagnostic artifact |
| `docs/reports/2026-06-15-stage5-prep-diagnostics.md` | Create | Canonical report |
| `docs/ML/diagnose_stage5_prep.py.md` | Create | Module docs |
| `tests/test_diagnose_stage5_prep.py` | Create | Smoke/helper tests |
| `MODULE_INDEX.md` | Modify | Add new module |
| `docs/audit/to_do.md` | Modify | Add plan link; mark items only after execution |
| `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md` | Modify after report | Wiki ingest |

---

### Task 1: Runner Skeleton And Baseline Reproduction

**Files:**
- Create: `ML/baseline/diagnose_stage5_prep.py`
- Test: `tests/test_diagnose_stage5_prep.py`

- [ ] **Step 1: Write smoke tests**
  - Test feature group resolver returns stable groups: `time`, `fractal_core`, `price`, `atr`, `all`.
  - Test oracle-mix function keeps probabilities in `[0, 1]`.
  - Test runner JSON schema helper includes `status == DIAGNOSTIC_ONLY`.

- [ ] **Step 2: Create file header**
  - Inputs: train/validation labeled CSV + OHLC.
  - Output: `ML/reports/stage5_prep_diagnostics.json`.
  - Status: `DIAGNOSTIC_ONLY`.

- [ ] **Step 3: Reuse Stage 4.4 infrastructure**
  - Import from `ML/baseline/diagnose_stage4_4.py` where possible.
  - Reproduce baseline: target `sell_H6_off05`, `p=0.4`, `min_fav=0.3`, `min_rr=1.0`, fixed TP `R=0.7` and baseline fav TP.

- [ ] **Step 4: Baseline gates**
  - Verify breach AUC `0.6674 ± 0.001`.
  - Verify Stage 4.4 baseline PF `1.015`, n `503`.
  - Verify fixed TP R=0.7 PF `1.038`, n `503`.
  - Stop if baseline does not reproduce.

---

### Task 2: Breach Feature Ablation

**Files:**
- Modify: `ML/baseline/diagnose_stage5_prep.py`

- [ ] **Step 1: Define fixed feature profiles**
  - `all_base_raw_plus_time`: current Stage 4.4 profile.
  - `no_time`: remove hour/day sin/cos.
  - `time_only`: only time features.
  - `fractal_core_only`: 100 fractals × core channels, no time.
  - `no_price`: remove raw price-like fields if locally separable.
  - `no_atr`: remove ATR feature if locally separable.

- [ ] **Step 2: Train XGBoost breach per profile**
  - Same train/val_stop/val_eval split as Stage 4.4.
  - Early stopping only on val_stop.
  - Same seed and hyperparameters.

- [ ] **Step 3: Report model metrics**
  - AUC, PR-AUC, lift in working low-risk zone.
  - Calibration buckets for `predict_break`.
  - Yearly AUC.
  - Feature importance summary.

- [ ] **Step 4: Report trading diagnostic**
  - Use same RF fav and same execution rule.
  - Evaluate fav-based TP baseline and fixed TP R=0.7.
  - Compute PF, BS_p05, yearly PF, trades/year.
  - Status remains `DIAGNOSTIC_ONLY`.

- [ ] **Step 5: Calendar risk conclusion**
  - If time-only is close to full model or time importance >30%, report that Transformer must be tested against calendar baselines.

---

### Task 3: AUC→PF Sensitivity

**Files:**
- Modify: `ML/baseline/diagnose_stage5_prep.py`

- [ ] **Step 1: Build oracle-like mixed scores**
  - Use true breach label only as diagnostic future information.
  - Create scores for alpha values: `{0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0}`.
  - `alpha=0.0` is model score, `alpha=1.0` is oracle-like perfect ranking.

- [ ] **Step 2: Preserve working rule**
  - Keep fixed Stage 4.4 rule: `p=0.4`, `min_fav=0.3`, `min_rr=1.0`.
  - Run with fav-based TP and fixed TP R=0.7.

- [ ] **Step 3: Measure sensitivity**
  - AUC, lift, PF, BS_p05, yearly PF, n_trades.
  - Find the first alpha where PF > 1.15 and BS_p05 >= 1.0.
  - Mark result as theoretical diagnostic, not target performance.

- [ ] **Step 4: Translate to Stage 5.0 design target**
  - Estimate required AUC/lift improvement over XGBoost.
  - If required improvement is implausibly high, recommend changing exit mechanics before/alongside Transformer.

---

### Task 4: JSON And Report

**Files:**
- Generate: `ML/reports/stage5_prep_diagnostics.json`
- Create: `docs/reports/2026-06-15-stage5-prep-diagnostics.md`

- [ ] **Step 1: JSON schema**
  - Include `status`, `config`, `baseline_reproduction`, `feature_ablation`, `auc_pf_sensitivity`, `interpretation_guards`.

- [ ] **Step 2: Report sections**
  - Context.
  - Methodology and split.
  - Baseline reproduction.
  - Feature ablation table.
  - AUC→PF sensitivity table.
  - What can and cannot be concluded.
  - Implications for Stage 5.0 Transformer.

- [ ] **Step 3: Non-conclusions**
  - No test opened.
  - No winner selected.
  - Oracle-like mixed scores use future information.
  - Feature ablation does not prove live profitability.

---

### Task 5: Docs, Wiki, And Verification

**Files:**
- Create: `docs/ML/diagnose_stage5_prep.py.md`
- Modify: `MODULE_INDEX.md`
- Modify after report: `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`

- [ ] **Step 1: Module docs**
  - Purpose, inputs, outputs, command, status, limitations.

- [ ] **Step 2: MODULE_INDEX**
  - Add `ML/baseline/diagnose_stage5_prep.py`.

- [ ] **Step 3: Wiki ingest**
  - Update `wiki/research/fractal-stop-research.md`.
  - Update `wiki/index.md` coverage.
  - Append `wiki/log.md`.
  - Run `wiki/wiki.py generate` and `wiki/wiki.py verify`.

- [ ] **Step 4: Verification**
  - Run tests: `~/git/SoSimple/.venv/bin/python -m pytest tests/test_diagnose_stage5_prep.py -q`.
  - Run diagnostic.
  - Validate JSON schema.
  - Run `git diff --check`.

## Acceptance Criteria

- Baseline reproduces Stage 4.4.
- Feature ablation answers whether breach signal is mostly time/calendar or fractal structure.
- AUC→PF sensitivity estimates the model-quality gap needed for PF gate.
- All outputs are marked `DIAGNOSTIC_ONLY`.
- Test is not opened.
- Report gives concrete Stage 5.0 design implications.
