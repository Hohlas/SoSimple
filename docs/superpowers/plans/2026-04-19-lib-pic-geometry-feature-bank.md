# lib_PIC Geometry Feature Bank Plan

> **For agentic workers:** REQUIRED: Use `.codex/skills/using-superpowers/SKILL.md` before starting, then use the most specific available superpowers skill for execution. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить безопасный набор входных признаков вокруг геометрии уровня `front/back/reverse`, потому что текущая диагностика показала эту группу как самый сильный источник сигнала для `trail_24_pnl_atr_x8`.

**Architecture:** Не менять `lib_PIC.mqh` и формат `Nero.csv`. Новый слой строится на уже экспортируемых 22-полевых фракталах и добавляет производные признаки по свежим окнам 5/10/20/50/100. Поля `Up/Dn` не используются, чтобы не смешивать геометрию уровня с отдельной информацией о реакции цены после уровня.

**Tech Stack:** Python 3, pandas, NumPy, existing labeled CSV format.

---

## File Structure

### Read First

- `docs/reports/2026-04-19-current-feature-importance-diagnostics.md`
- `docs/DATA_FLOW.md`
- `ML/entry_path_feature_bank.py`
- `ML/feature_importance_diagnostics.py`

### Files To Create

- `ML/lib_pic_geometry_feature_bank.py`
- `tests/test_lib_pic_geometry_feature_bank.py`
- `docs/ML/lib_pic_geometry_feature_bank.py.md`
- `docs/reports/2026-04-19-lib-pic-geometry-feature-bank.md`

### Files To Modify

- `MODULE_INDEX.md`
- `docs/superpowers/roadmap.md`

---

## Acceptance Rules

- Не менять `lib_PIC.mqh`.
- Не менять `Nero.csv`.
- Не использовать `Up/Dn` поля в этом geometry-bank; для них нужен отдельный path-reaction слой.
- Не запускать новый train.
- Признаки должны быть детерминированными, конечными и устойчивыми к пустым/битым фракталам.

---

## Task 1: Implement Geometry Feature Bank

- [ ] Parse `front`, `back`, `reverse`, `fractal_atr` from current 22-field fractal strings.
- [ ] Build window summaries for windows 5/10/20/50/100.
- [ ] Add ratio/balance features:
  - `front_back_ratio`;
  - `front_back_balance`;
  - `front_share`;
  - `geometry_size`.
- [ ] Add shape-quality features:
  - share of front-dominant levels;
  - share of balanced levels;
  - recent-vs-window shifts.
- [ ] Return original frame joined with new features.

## Task 2: Test

- [ ] Verify output columns are present.
- [ ] Verify no `Up/Dn` fields are required.
- [ ] Verify empty/broken fractals produce finite zero-safe features.
- [ ] Verify window order uses freshest fractals first.

## Task 3: Documentation

- [ ] Document module purpose and limitations.
- [ ] Add module to `MODULE_INDEX.md`.
- [ ] Add report with feature list and next usage recommendation.
