# benchmark_stage5_transformer_breach.py

**Назначение:** Основной раннер Stage 5.0 Transformer Breach Holdout и диагностических подпотоков 5.0a-5.3. Умеет обучать/оценивать Transformer breach-модели, строить preflight/audit артефакты признаков, выполнять XGBoost/Logistic screening, проверять устойчивость сигнала, запускать structural/UpDn ablation, а также Stage 5.2/5.3 time-to-breach диагностики.

**Статус:** Активный исследовательский раннер Fractal Stop Stage 5.x. Последний завершённый этап: Stage 5.3 `DIAGNOSTIC_ONLY` report, JSON status `TARGET_REFORMULATION_FOUND`.

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
- `ML/reports/stage5_0b_asinh_rerun.json` — structured artifact Stage 5.0b diagnostic training rerun
- `ML/reports/stage5_0f_signal_stationarity.json` — structured artifact Stage 5.0f: годовые окна `rolling/fixed/anchored`, прогресс прогона, итоговое диагностическое решение
- `ML/reports/stage5_1_structural_field_ablation.json` — structured artifact Stage 5.1: `time_only` / `structure_full` / `drop_*` / `add_*`, field verdicts и paired bootstrap deltas
- `ML/reports/stage5_1b_updn_field_ablation.json` — structured artifact Stage 5.1b: Up/Dn field ablation, `clock_shift` baseline, raw-shadow preflight
- `ML/reports/stage5_2_time_to_breach_regression.json` — structured artifact Stage 5.2: регрессия `bars_to_breach`
- `ML/reports/stage5_3_time_to_breach_target_reformulation.json` — structured artifact Stage 5.3: дискретные цели `breach_after_k`, `fast/medium/no_breach`, baseline и controls

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
python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-0b-asinh-rerun --single-seed
python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-0c-cross-target-rerun
python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-0f-signal-stationarity
python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-1-structural-field-ablation
python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-1b-updn-field-ablation --stage5-1b-workers 8 --stage5-1b-xgb-threads 4
python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-2-time-to-breach-regression --stage5-2-workers 8 --stage5-2-xgb-threads 4
python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-3-target-reformulation --stage5-3-workers 12 --stage5-3-xgb-threads 1
```

- `--stage5-0b-asinh-rerun` — Stage 5.0b diagnostic training run: `asinh`, frozen profile sets, mandatory label checks, XGBoost/time-only baselines, no trading winner.
- `--stage5-0c-cross-target-rerun` — Stage 5.0c: повторная проверка гипотезы об одном профиле `all100_absolute_price_atr_scaled_time_asinh` на sell + buy, 5 seeds, XGBoost на тех же признаках, заранее зафиксированные пороги, no trading winner.
- `ML/reports/stage5_0c_cross_target_rerun.json` — структурированный артефакт Stage 5.0c.
- `--stage5-0d-diagnostic-screening` — Stage 5.0d: диагностический скрининг 9 профилей (XGBoost + Logistic, без Transformer), абляция групп признаков.
- `ML/reports/stage5_0d_diagnostic_screening.json` — структурированный артефакт Stage 5.0d.
- `--stage5-0f-signal-stationarity` — Stage 5.0f: диагностика устойчивости сигнала во времени на двух целях, четырёх наборах признаков и трёх схемах годовых окон.
- `--stage5-1-structural-field-ablation` — Stage 5.1: диагностическая абляция 9 структурных полей `direction/front/back/strong/break/reverse/power/count/impulse` для `H6_off05 stop broken` на XGBoost.
- `--stage5-1b-updn-field-ablation` — Stage 5.1b: Up/Dn ablation с baseline `clock_shift`, raw-shadow preflight и progressive JSON.
- `--stage5-2-time-to-breach-regression` — Stage 5.2: регрессия `bars_to_breach` для `sell/buy_bars_to_breach_H6_off05`; результат диагностический.
- `--stage5-3-target-reformulation` — Stage 5.3: дискретная постановка time-to-breach (`breach_after_k`, `fast/medium/no_breach`), binary baseline и control `survives_at_least_k`.
- `build_flat_features` — расширен параметром `transform_variant` для XGBoost на том же профиле.
- `build_xgb_features_for_profile` — новый helper для признаков XGBoost на произвольном профиле.
- `compute_xgb_same_profile_baseline` — baseline XGBoost на тех же признаках, что и Transformer; transform params подбираются на train.
- `compute_logistic_same_profile_baseline` — Logistic Regression на тех же признаках (linear baseline).
- `compute_feature_group_ablation` — абляция групп признаков (price / structure / ATR / time).
- `stage5_0c_replication_decision` — функция решения по заранее зафиксированным порогам (4 решающих gate + holdout_check как предупреждение).
- `build_stage5_0f_window` / `build_stage5_0f_windows` — сборка годовых окон:
  - `rolling`: 8-летнее окно разработки = 7 лет `train_core` + 1 год `val_stop`
  - `fixed`: фиксированная база `2004..2019` + `val_stop=2020`
  - `anchored`: растущее окно от 2004 до `test_year-2` + `val_stop=test_year-1`
- `fit_stage5_0f_transform_params` / `build_stage5_0f_features` — сборка признаков Stage 5.0f для `base_raw_plus_time`, `structure_only`, `time_only`, `all100_relative_price_time`.
- `bootstrap_stage5_0f_metric_ci` — доверительные интервалы AUC и `lift_30` на тестовом году.
- `summarize_stage5_0f_seed_runs` / `stage5_0f_stationarity_decision` — агрегация по seed и итоговое диагностическое решение.
- `run_stage5_0f_signal_stationarity` — раннер Stage 5.0f: поэтапная запись JSON, лог прогресса `[n/456]`, финальное решение по устойчивости сигнала.
- `build_stage5_1_split` — фиксированный Stage 5.1 split: `train_core <= 2020`, `val_stop = 2021-2022`, `diagnostic_holdout = 2023-2025`, `low_n_disclosure = 2026`.
- `build_stage5_1_features` / `fit_stage5_1_transform_params` — Stage 5.1 признаки без `price`/`ATR`; `transform_variant="asinh"` сохраняется только как декларация, `transform_params = {}`.
- `evaluate_stage5_1_profile_seed` — один XGBoost прогон для profile/target/seed с yearly metrics, bootstrap CI и локальными prediction arrays для paired delta.
- `bootstrap_stage5_1_delta_ci` / `summarize_stage5_1_target` / `stage5_1_field_verdicts` — paired bootstrap deltas и диагностические verdicts `likely_useful` / `likely_noise` / `mixed_or_unclear`.
- `run_stage5_1_structural_field_ablation` — раннер Stage 5.1: `2 цели × 20 профилей × 3 seed = 120` XGBoost моделей, progressive JSON, field verdicts, multiple-testing disclosure.
- `run_stage5_2_time_to_breach_regression` — раннер Stage 5.2: `2 цели × 7 профилей × 3 seed = 42` XGBoost-регрессии, censoring/oracle/model gates.
- `run_stage5_3_target_reformulation` — раннер Stage 5.3: `2 цели × 12 target specs × 6 профилей × 3 seed = 432` XGBoost-классификации, precomputed feature cache, heartbeat/ETA JSON progress.

**Связанные файлы:**
- `ML/models/fractal_breach_transformer.py` — модель
- `tests/test_stage5_transformer_breach.py` — тесты Stage 5.x, включая Stage 5.2/5.3 target builders, metrics, runner и CLI checks
- `docs/methodology/A7-feature-distribution-audit.md` — методика feature distribution audit
- `docs/reports/2026-06-17-stage5-transformer-breach.md` — канонический отчёт Stage 5.0
- `docs/reports/2026-06-18-stage5_0a-feature-preflight.md` — канонический отчёт Stage 5.0a preflight
- `docs/reports/2026-06-20-stage5_0a-feature-distribution-audit.md` — канонический отчёт feature distribution audit
- `docs/reports/2026-06-24-stage5_0f-signal-stationarity.md` — канонический отчёт Stage 5.0f
- `docs/reports/2026-06-24-stage5_1-structural-field-ablation.md` — канонический отчёт Stage 5.1
- `docs/reports/2026-06-25-stage5_1b-updn-field-ablation.md` — канонический отчёт Stage 5.1b
- `docs/reports/2026-06-25-stage5_2-time-to-breach-regression.md` — канонический отчёт Stage 5.2
- `docs/reports/2026-06-26-stage5_3-time-to-breach-target-reformulation.md` — канонический отчёт Stage 5.3
- `docs/superpowers/plans/2026-06-16-stage5_0-transformer-breach-holdout.md` — план
- `docs/superpowers/plans/2026-06-18-stage5_0a-feature-preflight.md` — план preflight
- `docs/superpowers/plans/2026-06-22-stage5_0c-cross-target-rerun.md` — план Stage 5.0c
