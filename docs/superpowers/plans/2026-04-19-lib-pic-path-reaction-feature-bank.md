# lib_PIC Path-Reaction Feature Bank Plan

> **For agentic workers:** REQUIRED: Use `.codex/skills/using-superpowers/SKILL.md` before starting, then use the most specific available superpowers skill for execution. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить отдельный слой признаков по `Up/Dn`, который описывает историческую реакцию цены после уровней `lib_PIC`.

**Architecture:** Не менять `lib_PIC.mqh` и формат `Nero.csv`. Использовать уже экспортируемые `Up/Dn` как состояние, известное на момент строки. Слой отделён от geometry-bank, чтобы можно было сравнить вклад формы уровня и вклад реакции цены.

**Tech Stack:** Python 3, pandas, NumPy, existing labeled CSV format.

---

## File Structure

### Read First

- `docs/DATA_FLOW.md`
- `docs/reports/2026-04-19-lib-pic-geometry-feature-bank.md`
- `ML/lib_pic_geometry_feature_bank.py`

### Files To Create

- `ML/lib_pic_path_reaction_feature_bank.py`
- `tests/test_lib_pic_path_reaction_feature_bank.py`
- `docs/ML/lib_pic_path_reaction_feature_bank.py.md`
- `docs/reports/2026-04-19-lib-pic-path-reaction-feature-bank.md`

### Files To Modify

- `MODULE_INDEX.md`
- `docs/superpowers/roadmap.md`

---

## Acceptance Rules

- Не менять `lib_PIC.mqh`.
- Не менять `Nero.csv`.
- Не пересчитывать `Up/Dn` в Python.
- Использовать `Up/Dn` только как уже экспортированное состояние строки.
- Проверить, что `Dir < 0` корректно меняет местами favorable/adverse.

---

## Task 1: Implement Path-Reaction Feature Bank

- [x] Parse `Dir` and all `Up/Dn` horizons.
- [x] Convert raw Up/Dn into favorable/adverse movement by direction.
- [x] Build window summaries for windows 5/10/20/50/100.
- [x] Add edge, ratio and win-proxy features.
- [x] Add reaction slopes between 3/48 and 12/48 bars.

## Task 2: Test

- [x] Verify long direction mapping.
- [x] Verify short direction mapping.
- [x] Verify broken/legacy fractals are zero-safe.
- [x] Verify `fractal0` is treated as recent.

## Task 3: Documentation

- [x] Document module purpose and temporal semantics.
- [x] Add module to `MODULE_INDEX.md`.
- [x] Add report with feature list and next usage recommendation.
