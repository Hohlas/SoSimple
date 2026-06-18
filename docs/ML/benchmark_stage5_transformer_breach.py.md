# benchmark_stage5_transformer_breach.py

**Назначение:** Основной раннер Stage 5.0 Transformer Breach Holdout и diagnostic runner Stage 5.0a Feature Preflight. Умеет либо обучать/оценивать Transformer-модели breach-классификации, либо без обучения строить финальные входы, нормализовать их и сохранять аудит распределений по профилям признаков.

**Статус:** Завершён (Stage 5.0 FAIL)

**Вход:**
- `DATA/Nero_XAUUSD_train_labeled.csv` — обучающая выборка 2004-2020
- `DATA/Nero_XAUUSD_validation_labeled.csv` — валидационная выборка 2019-2022
- `DATA/Nero_XAUUSD_test_labeled.csv` — holdout 2023-2026

**Выход:**
- `ML/reports/stage5_transformer_breach.json` — структурированный результат Stage 5.0
- `ML/reports/stage5_0a_feature_preflight.json` — structured artifact Stage 5.0a
- `ML/reports/stage5_0a_feature_stats_normalized.csv` — статистики финальных нормализованных признаков
- `ML/reports/stage5_0a_profile_summary.csv` — сводка по профилям Stage 5.0a

**Сплит:** train ≤2020, val_stop 2021-2022, holdout ≥2023

**Профили признаков:**
- Stage 5.0 training: legacy-профили `all100_base10_time`, `all100_base10_no_time`, `newest20_base10_time`, `nearest40_base10_time`, `corridor_10atr_base10_time`
- Stage 5.0a preflight: clean-controls `time_only_clean`, `atr_only`, `time_plus_atr`, а также матрица `all100_*`, `nearest40_*`, `corridor_*` с `relative_price`

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
```

**Связанные файлы:**
- `ML/models/fractal_breach_transformer.py` — модель
- `tests/test_stage5_transformer_breach.py` — тесты
- `docs/reports/2026-06-17-stage5-transformer-breach.md` — канонический отчёт
- `docs/reports/2026-06-18-stage5_0a-feature-preflight.md` — канонический отчёт Stage 5.0a
- `docs/superpowers/plans/2026-06-16-stage5_0-transformer-breach-holdout.md` — план
- `docs/superpowers/plans/2026-06-18-stage5_0a-feature-preflight.md` — план preflight
