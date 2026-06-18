# benchmark_stage5_transformer_breach.py

**Назначение:** Основной раннер Stage 5.0 Transformer Breach Holdout. Обучает и оценивает Transformer-модели breach-классификации на фрактальных последовательностях XAUUSD H1 в сравнении с XGBoost baseline.

**Статус:** Завершён (Stage 5.0 FAIL)

**Вход:**
- `DATA/Nero_XAUUSD_train_labeled.csv` — обучающая выборка 2004-2020
- `DATA/Nero_XAUUSD_validation_labeled.csv` — валидационная выборка 2019-2022
- `DATA/Nero_XAUUSD_test_labeled.csv` — holdout 2023-2026

**Выход:**
- `ML/reports/stage5_transformer_breach.json` — структурированный результат

**Сплит:** train ≤2020, val_stop 2021-2022, holdout ≥2023

**Профили признаков (A6-нотация):**
5 обязательных профилей: all100_base10_time (primary), all100_base10_no_time, newest20_base10_time, nearest40_base10_time, corridor_10atr_base10_time. Gate применяется только к primary.

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
```

**Связанные файлы:**
- `ML/models/fractal_breach_transformer.py` — модель
- `tests/test_stage5_transformer_breach.py` — тесты
- `docs/reports/2026-06-17-stage5-transformer-breach.md` — канонический отчёт
- `docs/superpowers/plans/2026-06-16-stage5_0-transformer-breach-holdout.md` — план
