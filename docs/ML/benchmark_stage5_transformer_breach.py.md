# benchmark_stage5_transformer_breach.py

**Назначение:** Основной раннер Stage 5.0 Transformer Breach Holdout и diagnostic runner Stage 5.0a Feature Preflight / проверка распределения признаков. Умеет либо обучать/оценивать Transformer-модели breach-классификации, либо без обучения строить финальные входы, нормализовать их, считать raw corridor coverage до cap, агрегированные и per-position статистики распределений по профилям признаков.

**Статус:** Завершён (Stage 5.0 FAIL); Stage 5.0a проверка распределения признаков — `DIAGNOSTIC_ONLY` (2026-06-20). Сравнение transform-ов 2026-06-21 — `DIAGNOSTIC_ONLY`, без обучения.

**Вход:**
- `DATA/Nero_XAUUSD_train_labeled.csv` — обучающая выборка 2004-2020
- `DATA/Nero_XAUUSD_validation_labeled.csv` — валидационная выборка 2019-2022
- `DATA/Nero_XAUUSD_test_labeled.csv` — holdout 2023-2026

**Выход:**
- `ML/reports/stage5_transformer_breach.json` — структурированный результат Stage 5.0
- `ML/reports/stage5_0a_feature_preflight.json` — structured artifact Stage 5.0a
- `ML/reports/stage5_0a_feature_stats_normalized.csv` — статистики финальных нормализованных признаков (aggregated по позициям)
- `ML/reports/stage5_0a_feature_stats_per_position.csv` — per-position token статистики (A7, для sequence-профилей с осмысленным порядком)
- `ML/reports/stage5_0a_profile_summary.csv` — сводка по профилям Stage 5.0a
- `ML/reports/stage5_0a_transform_comparison.json` — сравнение `current` / `asinh` / `piecewise_tail`, без обучения
- `ML/reports/stage5_0a_transform_comparison_summary.csv` — краткая сводка сравнения transform-ов
- `ML/reports/stage5_0a_transform_comparison_stats.csv` — агрегированные статистики transform-сравнения
- `ML/reports/stage5_0a_transform_comparison_per_position.csv` — per-position статистики transform-сравнения

**Сплит:** train ≤2020, val_stop 2021-2022, holdout ≥2023

**Профили признаков:**
- Stage 5.0 training: legacy-профили `all100_base10_time`, `all100_base10_no_time`, `newest20_base10_time`, `nearest40_base10_time`, `corridor_10atr_base10_time`
- Stage 5.0a preflight: clean-controls `time_only_clean`, `atr_only`, `time_plus_atr`, а также матрица `all100_*`, `nearest40_*`, `corridor_*` с `relative_price`, включая `corridor_*_full`
- Дополнительные диагностические профили transform-сравнения: `all100_absolute_price_atr_scaled_time_raw`, `all100_absolute_price_atr_scaled_time_asinh`, `corridor_5atr_price_unit_atr_full`, `corridor_10atr_price_unit_atr_full`

**Особенности preflight:**
- builder возвращает `selection_meta` с `candidate_count_before_cap`, `selected_count_after_cap`, `is_truncated`
- truncation для corridor считается только по правилу `candidate_count_before_cap > seq_len`
- `corridor_*_no_time_full` имеют `row_dim=0` и допустимы только как `DIAGNOSTIC_ONLY`

**Transform-ы (A7 feature distribution audit, 2026-06-20):**
- ATR (row): `log1p(x)` перед StandardScaler — ATR неотрицательный с длинным правым хвостом; без log1p holdout regime shift до +32.9 std
- `price_coord_atr` (token): `sign(x)·log1p(abs(x))` (signed-log) перед token scaler — signed price coordinate с длинным хвостом (all100 pos99); raw max 13.9 → 2.78
- остальные token-признаки (direction, front, back, и т.д.): raw → StandardScaler (чистые распределения)
- `transform_type` в profile_summary: `log1p_atr_or_price_coord_atr`
- raw corridor bounds в coverage восстанавливаются через обратное преобразование `expm1` (A7 требует raw bounds check, signed-log их скрывает)

**Сравнение transform-ов (проверка распределения признаков, 2026-06-21):**
- `current`: текущий вариант `log1p(ATR)` + `sign(x)·log1p(abs(x))` для `price_coord_atr`
- `asinh`: `asinh(x)` для `ATR` и `price_coord_atr`; около нуля почти линейный, хвосты сжимаются похоже на логарифм
- `piecewise_tail`: пороги `p05/p95` fit только на train; середина остаётся линейной, хвосты ниже `p05` и выше `p95` сжимаются логарифмически
- сравнение выполняется для 7 rerun-кандидатов и 4 дополнительных диагностических профилей `price/ATR`; обучение не запускается
- `all100_absolute_price_atr_scaled_time_raw`: token `price_atr_scaled = price/ATR`, без дополнительного сжатия token-признака
- `all100_absolute_price_atr_scaled_time_asinh`: token `price_atr_scaled = asinh(price/ATR)`
- `corridor_5atr_price_unit_atr_full` / `corridor_10atr_price_unit_atr_full`: token `price_coord_unit = (price-fractal0)/(ATR*corridor_atr)`

**Per-position token stats (A7):**
- `compute_per_position_token_stats` — per-feature stats для каждой позиции 0..seq_len−1, только valid (mask=True) samples
- fully-padded позиции (n_valid=0) сохраняются (padding coverage — отдельный diagnostic)
- собирается для всех профилей с `token_dim>0`; row_only профили возвращают []

**Baseline:** XGBoost на тех же признаках (base_raw_plus_time, no_time, time_only) с тем же сплитом.

**Gate (primary profile only):**
- holdout AUC ≥ max(XGBoost+0.02, time_only+0.04)
- holdout lift_bottom30 ≥ XGBoost lift_bottom30 + 0.10
- yearly AUC ≥ 0.55 в ≥3 из 4 лет holdout

**Использование:**
```bash
python -m ML.baseline.benchmark_stage5_transformer_breach --single-seed
python -m ML.baseline.benchmark_stage5_transformer_breach --single-seed --phase 1
python -m ML.baseline.benchmark_stage5_transformer_breach --single-seed --skip-phase1
python -m ML.baseline.benchmark_stage5_transformer_breach --feature-preflight-only
python -m ML.baseline.benchmark_stage5_transformer_breach --transform-comparison-only
```

**Связанные файлы:**
- `ML/models/fractal_breach_transformer.py` — модель
- `tests/test_stage5_transformer_breach.py` — тесты (83 теста, включая log1p/signed-log/per-position и `price/ATR` профили)
- `docs/methodology/A7-feature-distribution-audit.md` — методика feature distribution audit
- `docs/reports/2026-06-17-stage5-transformer-breach.md` — канонический отчёт Stage 5.0
- `docs/reports/2026-06-18-stage5_0a-feature-preflight.md` — канонический отчёт Stage 5.0a preflight
- `docs/reports/2026-06-20-stage5_0a-feature-distribution-audit.md` — канонический отчёт feature distribution audit
- `docs/superpowers/plans/2026-06-16-stage5_0-transformer-breach-holdout.md` — план
- `docs/superpowers/plans/2026-06-18-stage5_0a-feature-preflight.md` — план preflight
