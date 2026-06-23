# Context Handoff

Дата: 2026-06-23

## Текущий этап

Stage 5.0d завершён. Вердикт: **h6_off05_target_exhausted** — постановка H6_off05 stop broken на текущих 9 профилях исчерпана. Fractal Stop как семейство целей не закрыт.

Статус проекта: **DIAGNOSTIC_ONLY**. Ни один этап не дал кандидата.

## Что сделано

### Stage 5.0d (2026-06-23) — диагностический скрининг профилей
- Новый CLI `--stage5-0d-diagnostic-screening`
- XGBoost (3 seeds) + Logistic Regression на всех 9 профилях × 2 цели
- Абляция групп признаков (price / structure / ATR / time) для лучшего профиля
- `compute_logistic_same_profile_baseline` — linear baseline (Logistic Regression)
- `compute_feature_group_ablation` — абляция с XGBoost retrain
- **Вердикт**: ни один профиль не достиг порога +0.02 AUC над base_raw_plus_time
- Лучший: sell `all100_relative_price_time` (delta +0.0111); lift_pass OK, но AUC_pass FAIL
- Buy: все профили уступают базе (дельты ≤ 0)
- Абляция: structure-признаки критичны (AUC −0.14/−0.19), price/ATR почти не влияют
- XGBoost >> Logistic (gap 0.04–0.05) — сигнал нелинейный
- 791 tests passed
- Отчёт: `docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md`

### Предыдущие этапы (кратко)
- 5.0a: feature distribution audit, asinh выбран
- 5.0b: single-seed asinh rerun, 9 профилей, Transformer не превзошёл XGBoost
- 5.0c: multi-seed replication, 1 профиль, overall_pass: FAIL

## Главные выводы

1. **Фрактальные признаки на H6_off05 не добавляют полезной информации сверх raw.** Ни на одном профиле XGBoost не превосходит base_raw_plus_time на ≥0.02 AUC.
2. **Структурные признаки (direction, front, back, ...) — главный носитель сигнала.** Их удаление обрушивает AUC на 0.14–0.19.
3. **Ценовые и ATR-признаки почти не влияют** на результат XGBoost.
4. **Corridor-профили систематически хуже all100** — фильтрация теряет сигнал.
5. **Fractal Stop как семейство не закрыт** — остаются другие цели (сторона, время до пробоя, выход, режим).

## Где мы сейчас

Stage 5.0d закрыт. Постановка H6_off05 stop broken исчерпана. Следующий шаг — смена target или смена признаков, не смена модели.

## Ключевые файлы

Код:
- `ML/baseline/benchmark_stage5_transformer_breach.py` (~4070 строк, 791 test)
- `tests/test_stage5_transformer_breach.py`

Методология:
- `docs/methodology/README.md`
- `docs/methodology/16-reporting-audit.md`

Отчёты:
- `docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md`
- `docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md`

Артефакты:
- `ML/reports/stage5_0d_diagnostic_screening.json`
- `ML/reports/stage5_0c_cross_target_rerun.json`

## Ключевые технические решения

- **asinh** — единый transform для ATR и price_coord_atr
- **compute_xgb_same_profile_baseline** — XGBoost на тех же flattened признаках
- **compute_logistic_same_profile_baseline** — Logistic Regression linear baseline
- **compute_feature_group_ablation** — абляция групп с retrain XGBoost
- **_build_feature_group_masks** — маски по token_fields/row_fields, не позиционные
- **build_arg_parser()** — CLI с `--stage5-0d-diagnostic-screening`

## Ограничения / открытые вопросы

- 3 seeds — скрининг, не CI. 5-seed проверка не делалась (не было кандидата).
- Абляция только для лучшего профиля, не для всех.
- Holdout — только раскрытие, не входит в решение.
- Причина, почему фракталы не добавляют сигнала, не установлена. Возможные гипотезы: (a) raw-признаки уже содержат всю информацию; (b) фрактальные признаки шумные; (c) модель не извлекает взаимодействия (но XGBoost >> Logistic говорит об обратном).
