# Feature Bank Comparison Diagnostics Plan

> **For agentic workers:** REQUIRED: Use `.codex/skills/using-superpowers/SKILL.md` before starting, then use the most specific available superpowers skill for execution. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Сравнить baseline, clean-baseline, geometry-bank, path-reaction-bank и их сочетания на одной дешёвой диагностике до запуска нового training track.

**Architecture:** Read-only. Не менять `lib_PIC`, `Nero.csv`, targets или MT4. Все варианты используют одну train/validation выборку, одну цель и одинаковую лёгкую модель.

**Tech Stack:** Python 3, pandas, NumPy, scikit-learn, existing feature-bank modules.

---

## File Structure

### Read First

- `ML/feature_importance_diagnostics.py`
- `ML/lib_pic_geometry_feature_bank.py`
- `ML/lib_pic_path_reaction_feature_bank.py`
- `docs/reports/2026-04-19-lib-pic-geometry-feature-bank.md`
- `docs/reports/2026-04-19-lib-pic-path-reaction-feature-bank.md`

### Files To Create

- `ML/feature_bank_comparison_diagnostics.py`
- `tests/test_feature_bank_comparison_diagnostics.py`
- `docs/ML/feature_bank_comparison_diagnostics.py.md`
- `docs/reports/2026-04-19-feature-bank-comparison-diagnostics.md`
- `ML/reports/feature_bank_comparison/`

### Files To Modify

- `MODULE_INDEX.md`
- `docs/superpowers/roadmap.md`

---

## Acceptance Rules

- Не запускать нейросетевое обучение.
- Не менять `lib_PIC.mqh`.
- Не менять формат данных.
- Сравнивать только заранее заданные варианты:
  - baseline_full;
  - baseline_clean;
  - baseline_full + path;
  - baseline_clean + path;
  - baseline_clean + geometry + path.
- Результат считать диагностикой признаков, не торговым verdict.

---

## Task 1: Implement Comparison Runner

- [x] Reuse existing baseline grouped features.
- [x] Add clean baseline by removing weak/noisy raw groups.
- [x] Reuse geometry feature-bank.
- [x] Reuse path-reaction feature-bank.
- [x] Train the same cheap model for each variant.
- [x] Export `summary.csv`, `summary.json`, `report.md`.

## Task 2: Test

- [x] Verify feature counts grow by variant.
- [x] Verify report artifacts are written.

## Task 3: Run Bounded Diagnostic

- [x] Target: `trail_24_pnl_atr_x8`.
- [x] seq_len: `20`.
- [x] train rows: `12000`.
- [x] validation rows: `6000`.
- [x] n_estimators: `80`.

## Task 4: Document Decision

- [x] Write canonical report.
- [x] Update roadmap.
- [x] Add module to index.
