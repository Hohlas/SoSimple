# Stage 6.1 Baseline Plus Geometry Delta Design

> **Дата**: 2026-06-29  
> **Статус**: Draft for implementation  
> **Цель**: Проверить, добавляет ли локальная геометрия фракталов пользу поверх `h12_clock_shift_back` на H12 TP/SL touch.

## Context

Stage 6.1 показал, что geometry-only профили вокруг `fractal0` слабы: median `val_stop` AUC 0.51-0.55 и `NO_THRESHOLD`. При этом `h12_clock_shift_back` даёт более сильное ранжирование (`AUC=0.6174`), хотя его trading threshold не прошёл permutation check (`empirical_p_value=0.225`).

Новая проверка не должна открывать широкий поиск. Она отвечает на один вопрос: есть ли добавочная ценность геометрии поверх baseline-признаков.

## Scope

Добавить три заранее выбранных combined-профиля:

- `h12_clock_shift_back_plus_nearest_time40_geometry`
- `h12_clock_shift_back_plus_corridor3_geometry`
- `h12_clock_shift_back_plus_corridor10_geometry`

Эти три профиля выбраны как лучшие geometry-only профили Stage 6.1 по median `val_stop` AUC:

1. `h12_nearest_time40_relative_geometry` — 0.5500
2. `h12_corridor3_relative_geometry` — 0.5316
3. `h12_corridor10_relative_geometry` — 0.5211

Не добавлять `nearest_price40` и `zones10`, чтобы не превращать проверку в полный повтор всех geometry-only вариантов.

## Method

Каждый combined-профиль строится как конкатенация:

1. `build_stage5_4_features(clean_df, "clock_shift_back")`
2. соответствующие geometry features из `stage61_build_geometry_features(clean_df, geometry_profile)`

`stage6_*` target/outcome columns должны удаляться до построения обеих частей признаков.

## Selection And Gate

Primary comparison remains anchored to `h12_clock_shift_back`. Combined-профиль считается полезным только если на `val_stop`:

- median AUC improves over baseline by at least `+0.02`;
- median PR AUC lift is not lower than baseline;
- threshold status is `SELECTED`;
- selected PF is at least baseline selected PF;
- permutation `empirical_p_value <= 0.10`.

`diagnostic_holdout` and `low_n_disclosure` remain disclosure-only. They must not select profile, seed, threshold, or gate.

## Reporting

Update the Stage 6.1 report with a new section `Baseline + Geometry Delta Test`:

- explain the fixed three-profile choice;
- show baseline vs combined median `val_stop` metrics;
- show diagnostic holdout AUC/PR lift as disclosure-only;
- state whether geometry adds incremental value;
- preserve the existing Stage 6.1 geometry-only conclusion.

## Runtime Contract

The existing runner contract remains required:

- `xgb_n_jobs=24`
- heartbeat output
- checkpoint before preflight
- checkpoint after every run
- `--resume` / `--no-resume`
- top-level and per-run `elapsed_sec`

## Non-Goals

- Do not change horizon, stop/TP formula, split policy, or target.
- Do not add new geometry encodings.
- Do not tune thresholds using holdout.
- Do not promote the result to `CANDIDATE`; this remains `DIAGNOSTIC_ONLY`.

## Expected Outcome

If all combined profiles fail the delta gate, the report should say: geometry-only and baseline+geometry tests both failed to justify further Stage 6.1 investment.

If one combined profile passes the delta gate, the report should say: geometry may add incremental ranking/trading value, but it remains diagnostic until a separate validation cycle is designed.
