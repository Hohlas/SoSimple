# Context Handoff

Дата: 2026-06-23

## Текущий этап

Fractal Stop после Stage 5.0c (cross-target replication rerun, overall_pass: FAIL). Готов к Stage 5.0d (диагностический скрининг, без Transformer).

Статус проекта: **DIAGNOSTIC_ONLY**. Ни один этап не дал кандидата.

## Что сделано

### Stage 5.0a (2026-06-20) — feature distribution audit
- log1p(ATR) + signed-log(price_coord_atr) реализованы, per-position stats
- Все 7 профилей: 0 ERROR, 0 TAIL_GT10, остаточный REGIME_SHIFT delta=3.14 (WARNING)
- 762 tests passed
- Отчёт: `docs/reports/2026-06-20-stage5_0a-feature-distribution-audit.md`

### Stage 5.0b (2026-06-21) — asinh rerun
- `asinh` выбран как единый transform (замена log1p + signed-log)
- CLI `--stage5-0b-asinh-rerun`
- Sell: лучший Transformer val_auc=0.6719 vs gate 0.6731 (gap=0.0012, single-seed)
- Buy: viable (22745 строк); лучший Transformer val_auc=0.6762 vs XGBoost 0.6894
- Баг загрузчика исправлен: `load_splits` фильтрует по `target_col.notna()`
- 777 tests passed
- Отчёт: `docs/reports/2026-06-21-stage5_0b-asinh-rerun.md`

### Stage 5.0c (2026-06-22) — cross-target replication rerun
- Один профиль `all100_absolute_price_atr_scaled_time_asinh`, sell+buy, 5 seeds
- XGBoost на тех же flattened признаках (честное сравнение)
- 4 решающих порога + `holdout_check` как предупреждение
- **overall_pass: FAIL** — Transformer уступил XGBoost по AUC и lift_30 на обеих целях
- Seed spread узкий (sell 0.0054, buy 0.0104) — стабильно, но слабо
- Transformer переобучается: val AUC падает после epoch 9
- 786 tests passed
- Отчёт: `docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md`

### Методология (2026-06-22)
- 8 файлов обновлены: введены «поисковый» / «проверочный» уровень исследования
- Transfer ≠ overfitting check, replication test framing, verdict-уровни, типовые ошибки

## Главные выводы

1. **Transformer не превосходит XGBoost ни на одном проверенном профиле.** На 5.0b (9 профилей, single-seed) и 5.0c (1 профиль, multi-seed) — ни разу.
2. **Transformer переобучается на 25k строках** (seed 42 sell: val AUC падает с 0.6673 на epoch 9 до 0.6445 на epoch 17).
3. **Причины не ясны:** слабый сигнал в признаках, переобучение, или обе.
4. **Buy target жизнеспособен** (22745 train строк, pos_rate 0.37), но Transformer на нём тоже уступает XGBoost.

## Где мы сейчас

Stage 5.0c закрыт. Готов план Stage 5.0d.

### Stage 5.0d — диагностический скрининг (поисковый уровень)
- План: `docs/superpowers/plans/2026-06-23-stage5_0d-diagnostic-screening.md`
- XGBoost + Logistic Regression на всех 9 профилях, без Transformer
- Абляция групп признаков (price / structure / ATR / time)
- Критерий: AUC +0.02 AND lift_30 ≤ base → гипотеза для 5.0e
- Если ни один профиль не проходит → постановка H6_off05 исчерпана (Fractal Stop как семейство не закрыт)

## Ключевые файлы

Код:
- `ML/baseline/benchmark_stage5_transformer_breach.py` (~3700 строк)
- `tests/test_stage5_transformer_breach.py` (786 tests)

Методология:
- `docs/methodology/00-research-management.md` — уровни исследования
- `docs/methodology/07-baseline-first.md` — baseline-gate по уровням
- `docs/methodology/09-validation-freeze.md` — replication test framing
- `docs/methodology/11-robustness.md` — transfer ≠ overfitting
- `docs/methodology/A3-typical-false-conclusions.md` — типовые ошибки
- `docs/methodology/A4-verdicts-stop-conditions.md` — verdict ↔ уровни
- `docs/methodology/16-reporting-audit.md` — шаблон отчёта

Отчёты:
- `docs/reports/2026-06-20-stage5_0a-feature-distribution-audit.md`
- `docs/reports/2026-06-21-stage5_0b-asinh-rerun.md`
- `docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md`

Планы:
- `docs/superpowers/plans/2026-06-22-stage5_0c-cross-target-rerun.md`
- `docs/superpowers/plans/2026-06-23-stage5_0d-diagnostic-screening.md`

Артефакты:
- `ML/reports/stage5_0b_asinh_rerun.json`
- `ML/reports/stage5_0b_asinh_rerun_buy_stop_broken_H6_off05_flag.json`
- `ML/reports/stage5_0c_cross_target_rerun.json`

## Ключевые технические решения

- **asinh** — единый transform для ATR и price_coord_atr (замена log1p + signed-log)
- **build_flat_features** — принимает `transform_variant` + `transform_params`
- **build_xgb_features_for_profile** — XGBoost на произвольном профиле, опциональные `transform_params`
- **compute_xgb_same_profile_baseline** — fit transform params на train, передача в val/holdout
- **build_arg_parser()** — вынесен из main(), тестируем
- **Loader fix**: `load_splits` фильтрует по `target_col.notna()` (не всегда sell)
- **Holdout не используется для решения**: `holdout_used_for_decision: false`
- **Промежуточные git commit** — не делаются; закрытие через stage-reporting

## Ограничения / открытые вопросы

- Transformer переобучается на 25k строках — причина не выяснена
- Все профили 5.0b были single-seed; multi-seed — только один профиль
- XGBoost same-profile не проверялся на остальных 8 профилях (это задача 5.0d)
- Buy и sell считаются на разных строках; их метрики нельзя напрямую сравнивать
