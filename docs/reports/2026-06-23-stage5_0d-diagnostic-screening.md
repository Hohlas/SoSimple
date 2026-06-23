# Stage 5.0d — диагностический скрининг профилей

> **Дата**: 2026-06-23
> **Статус**: Completed
> **Вердикт**: h6_off05_target_exhausted
> **Цель**: Понять, какие фрактальные профили и группы признаков несут сигнал сверх raw features, без обучения Transformer
> **Уровень этапа**: поисковый
> **Related plan**: `docs/superpowers/plans/2026-06-23-stage5_0d-diagnostic-screening.md`

## Context

Stage 5.0c показал, что Transformer не превосходит XGBoost на тех же признаках (0 из 5 seeds выше порога на обеих целях). Stage 5.0d — диагностический скрининг: XGBoost и Logistic Regression на всех 9 профилях из 5.0b, без обучения Transformer. Цель — понять, какие профили и группы признаков несут сигнал сверх raw features.

## What Was Done

- Обучен XGBoost same-profile на 9 профилях × 2 цели × 3 seeds (median).
- Обучена Logistic Regression (class_weight="balanced") на тех же признаках, 1 seed.
- Абляция групп признаков (price / structure / ATR / time) для лучшего профиля по каждой цели.
- Transformer не обучался.

## Multiple Testing Context

Search budget: XGBoost same-profile 9 профилей × 2 цели × 3 seeds = 54 прогона; Logistic Regression 9 профилей × 2 цели = 18 прогонов; плюс 2 абляции групп признаков для лучших профилей.
Коррекция: этап поисковый, результат — диагностический, не кандидат. Множественный перебор не корректируется, но вердикт не претендует на подтверждённую гипотезу. Переход к проверочному циклу (5.0e) требует нового плана с заранее зафиксированными порогами.

## Changed Files

- `ML/baseline/benchmark_stage5_transformer_breach.py` — Stage 5.0d constants, `compute_logistic_same_profile_baseline`, `compute_feature_group_ablation`, `run_stage5_0d_diagnostic_screening`, CLI `--stage5-0d-diagnostic-screening`.
- `tests/test_stage5_transformer_breach.py` — 5 новых тестов Stage 5.0d (791 passed).
- `ML/reports/stage5_0d_diagnostic_screening.json` — structured artifact.
- `docs/ML/benchmark_stage5_transformer_breach.py.md` — module documentation updated.
- `CHANGELOG.md` — entry added.

## Verification

- Tests: `./.venv/bin/python -m pytest tests/ -q` — 791 passed, 0 failed.
- JSON artifact: `ML/reports/stage5_0d_diagnostic_screening.json` — 37 KB, записан.

## Setup

- Profiles: все 9 из 5.0b (4 confirmatory + 5 diagnostic)
- Targets: sell + buy
- Models: XGBoost (3 seeds, median) + Logistic Regression (1 seed, class_weight="balanced")
- Transform: asinh для всех 9 профилей (наследие 5.0b)
- Scaler: train-only StandardScaler
- Seeds: `[42, 77, 123]`
- Holdout: 2023-2026, только раскрытие результата
- Transformer: не обучается

## XGBoost Screening Results

### Sell (base_raw_plus_time val AUC = 0.6631)

| Profile | xgb median val_auc | delta | xgb median lift_30 | base lift_30 | logistic val_auc | xgb vs logistic |
|---|---:|---:|---:|---:|---:|---:|
| all100_relative_price_time | 0.6742 | +0.0111 | 0.5415 | 0.5539 | 0.6230 | +0.0511 |
| all100_absolute_price_atr_scaled_time_asinh | 0.6723 | +0.0092 | 0.5291 | 0.5539 | 0.6262 | +0.0462 |
| nearest40_relative_price_time | 0.6338 | −0.0293 | 0.6436 | 0.5539 | 0.5946 | +0.0392 |
| all100_relative_price_no_time | 0.6271 | −0.0361 | 0.6405 | 0.5539 | 0.5953 | +0.0317 |
| corridor_5atr_relative_price_atr_full | 0.6134 | −0.0498 | 0.6529 | 0.5539 | 0.5856 | +0.0278 |
| corridor_5atr_price_unit_atr_full | 0.6115 | −0.0516 | 0.6529 | 0.5539 | 0.5860 | +0.0256 |
| corridor_10atr_relative_price_atr_full | 0.6091 | −0.0540 | 0.6900 | 0.5539 | 0.5981 | +0.0110 |
| corridor_10atr_price_unit_atr_full | 0.6081 | −0.0551 | 0.6808 | 0.5539 | 0.5989 | +0.0092 |
| nearest40_relative_price_no_time | 0.5238 | −0.1393 | 0.9716 | 0.5539 | 0.5308 | −0.0069 |

### Buy (base_raw_plus_time val AUC = 0.6894)

| Profile | xgb median val_auc | delta | xgb median lift_30 | base lift_30 | logistic val_auc | xgb vs logistic |
|---|---:|---:|---:|---:|---:|---:|
| all100_absolute_price_atr_scaled_time_asinh | 0.6888 | −0.0006 | 0.5078 | 0.5389 | 0.6476 | +0.0412 |
| all100_relative_price_time | 0.6865 | −0.0029 | 0.5009 | 0.5389 | 0.6403 | +0.0462 |
| all100_relative_price_no_time | 0.6488 | −0.0406 | 0.5907 | 0.5389 | 0.6048 | +0.0439 |
| nearest40_relative_price_time | 0.6363 | −0.0531 | 0.6390 | 0.5389 | 0.6078 | +0.0285 |
| corridor_5atr_relative_price_atr_full | 0.6295 | −0.0599 | 0.6528 | 0.5389 | 0.6011 | +0.0284 |
| corridor_5atr_price_unit_atr_full | 0.6295 | −0.0599 | 0.6528 | 0.5389 | 0.6009 | +0.0286 |
| corridor_10atr_price_unit_atr_full | 0.6264 | −0.0630 | 0.6528 | 0.5389 | 0.5794 | +0.0470 |
| corridor_10atr_relative_price_atr_full | 0.6203 | −0.0691 | 0.6598 | 0.5389 | 0.5792 | +0.0410 |
| nearest40_relative_price_no_time | 0.5253 | −0.1641 | 0.8981 | 0.5389 | 0.5138 | +0.0115 |

## Feature Group Ablation

### Sell (best profile: all100_relative_price_time)

| Group | val_auc | n_features | delta from full |
|---|---:|---:|---:|
| full | 0.6742 | 1005 | — |
| no_price | 0.6693 | 904 | −0.0050 |
| no_structure | 0.5341 | 101 | −0.1402 |
| no_atr | 0.6728 | 1004 | −0.0014 |
| no_time | 0.6250 | 1001 | −0.0492 |

### Buy (best profile: all100_absolute_price_atr_scaled_time_asinh)

| Group | val_auc | n_features | delta from full |
|---|---:|---:|---:|
| full | 0.6873 | 1005 | — |
| no_price | 0.6879 | 904 | +0.0006 |
| no_structure | 0.5003 | 101 | −0.1870 |
| no_atr | 0.6899 | 1004 | +0.0026 |
| no_time | 0.6497 | 1001 | −0.0376 |

## Screener Result

- **verdict**: `h6_off05_target_exhausted`
- **criteria**:
  - auc_threshold: 0.02
  - auc_delta (overall best): **+0.0111** (sell, `all100_relative_price_time`)
  - **auc_pass: false** (0.0111 < 0.02)
  - **lift_pass: true** (0.5415 ≤ 0.5539)
- **overall_best**: target=sell, profile=all100_relative_price_time, delta=+0.0111
- **sell_best**: all100_relative_price_time, delta=+0.0111, lift_30=0.5415
- **buy_best**: all100_absolute_price_atr_scaled_time_asinh, delta=−0.0006, lift_30=0.5078
- **next_step**: Постановка H6_off05 stop broken на текущих 9 профилях исчерпана. Fractal Stop как семейство целей не закрыт — остаются другие постановки (сторона, время до пробоя, выход). Результат 5.0d не открывает Transformer-обучение автоматически.

## Conclusions

Ни один из 9 профилей не показывает AUC-прироста ≥0.02 над базовым XGBoost на raw-признаках. Лучший профиль (`all100_relative_price_time`, sell) даёт дельту +0.0111 — в пределах шума, не дотягивает до порога.

Ключевые наблюдения:

1. **Фрактальные признаки не добавляют полезной информации сверх raw** на постановке H6_off05. Все 9 профилей либо слабо превосходят, либо уступают базовому XGBoost. На buy-цели ни один профиль не превосходит base вовсе (дельты ≤ −0.0006).

2. **Структурные признаки — главный носитель сигнала.** Абляция `no_structure` обрушивает AUC с 0.674 до 0.534 на sell и с 0.687 до 0.500 на buy. Ценовые и ATR-признаки почти не влияют на результат.

3. **XGBoost >> Logistic** на всех лидирующих профилях (gap 0.04–0.05). Сигнал — во взаимодействиях признаков, не линейный. Это подтверждает, что у Transformer теоретически был шанс, но 5.0c показал, что он его не реализует.

4. **Абляция no_time** снижает AUC на ~0.05 (sell) и ~0.04 (buy) — временные признаки значимы, но умеренно.

5. **`nearest40_relative_price_no_time`** даёт AUC ~0.52 — практически случайный. Это согласуется с тем, что без времени и с меньшей историей (40 вместо 100) фракталы почти бесполезны.

6. **Corridor-профили** систематически уступают all100 на обеих целях. Corridor-фильтрация не усиливает сигнал, а теряет его.

## Limitations / Open Questions

- 3 seeds — screening, не CI. Для кандидата нужен 5-seed проверочный прогон.
- Абляция выполнена только для лучшего профиля по XGBoost, не для всех.
- Holdout — только раскрытие, не входит в решение.
- Результат 5.0d не открывает Transformer-обучение автоматически — только формирует гипотезу для Stage 5.0e.
- Buy-дельты везде отрицательные или около нуля. Причина не ясна: возможно, buy-таргет проще предсказывается raw-признаками, и фракталы не добавляют информации.

## Validation Split Disclosure

- val_stop: 2021-2022, использовался для всех метрик решения.
- holdout: 2023-2026, только раскрытие (`holdout_used_for_decision: false`).
- Split: train ≤2020 (sell 25672 строк, buy 22745), val_stop 2021-2022, holdout ≥2023. Scaler и transform params fit на train только.

## Next Step

Закрыть постановку H6_off05 stop broken на текущих 9 профилях как исследовательски исчерпанную. Fractal Stop как семейство целей не закрыт — остаются другие постановки (сторона, время до пробоя, выход, режим). Рассмотреть смену target или смену признаков, не смену модели.

## Related Materials

- `ML/reports/stage5_0d_diagnostic_screening.json`
- `docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md`
- `docs/superpowers/plans/2026-06-23-stage5_0d-diagnostic-screening.md`
