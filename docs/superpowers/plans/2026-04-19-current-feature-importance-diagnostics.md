# Current Feature Importance Diagnostics Plan

> **For agentic workers:** REQUIRED: Use `.codex/skills/using-superpowers/SKILL.md` before starting, then use the most specific available superpowers skill for execution. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, какие группы уже экспортируемых `Nero_*_labeled.csv` признаков реально помогают объяснять торгово-близкую цель до изменения `lib_PIC.mqh`.

**Architecture:** Read-only diagnostic. Не менять `lib_PIC`, не менять формат `Nero.csv`, не запускать нейросетевое обучение. Построить дешёвую модель поверх групповых признаков и оценить group permutation importance на validation.

**Tech Stack:** Python 3, pandas, NumPy, scikit-learn, existing `DATA/Nero_train_labeled.csv`, `DATA/Nero_validation_labeled.csv`.

---

## File Structure

### Read First

- `docs/reports/2026-04-19-lib-pic-feature-source-audit.md`
- `docs/DATA_FLOW.md`
- `ML/data_loader.py`
- `ML/entry_path_feature_bank.py`

### Files To Create

- `ML/feature_importance_diagnostics.py`
- `tests/test_feature_importance_diagnostics.py`
- `docs/ML/feature_importance_diagnostics.py.md`
- `docs/reports/2026-04-19-current-feature-importance-diagnostics.md`
- `ML/reports/current_feature_importance/`

### Files To Modify

- `MODULE_INDEX.md`

---

## Acceptance Rules

- Не менять `lib_PIC.mqh`.
- Не менять `Nero.csv`.
- Не запускать новый training cycle.
- Читать большие CSV только чанками и только нужные колонки.
- Считать результаты диагностикой входов, а не торговым verdict.

---

## Task 1: Implement Diagnostic Feature Builder

- [x] Parse current 22-field fractal format.
- [x] Build grouped features by windows 5/10/20/50/100.
- [x] Separate feature groups by meaning.
- [x] Include row-level context fields if present.

## Task 2: Implement Group Importance

- [x] Train a cheap `RandomForestRegressor`.
- [x] Measure validation R2, MAE and directional accuracy.
- [x] Shuffle whole feature groups on validation.
- [x] Export `group_importance.csv`, `feature_importance.csv`, `summary.json`, `report.md`.

## Task 3: Test

- [x] Unit-test feature construction.
- [x] Unit-test tail sampling.
- [x] Unit-test end-to-end diagnostic output.

## Task 4: Run First Diagnostic

- [x] Run on `trail_24_pnl_atr_x8`.
- [x] Use `seq_len=20`.
- [x] Save outputs to `ML/reports/current_feature_importance/`.
- [x] Summarize results in `docs/reports/`.
