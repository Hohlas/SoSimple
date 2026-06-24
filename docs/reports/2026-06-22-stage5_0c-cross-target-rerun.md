# Stage 5.0c — повторная проверка гипотезы на двух целях

> **Дата**: 2026-06-22
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY — overall_pass: FAIL
> **Уровень этапа**: проверочный
> **Framing**: Повторная проверка гипотезы, порождённой Stage 5.0b (не независимое открытие)
> **Related plan**: `docs/superpowers/plans/2026-06-22-stage5_0c-cross-target-rerun.md`

## Context

Stage 5.0b выявил, что `all100_absolute_price_atr_scaled_time_asinh` стабильно оказался рядом с лидером на двух целевых (sell val_auc 0.6673 vs лидер 0.6719; buy val_auc 0.6752 vs лидер 0.6762). Stage 5.0c — заранее зафиксированная повторная проверка: один профиль, две цели, 5 seeds, XGBoost на тех же признаках, заранее зафиксированные числовые пороги.

## What Was Done

- Заморожены константы Stage 5.0c: один профиль `all100_absolute_price_atr_scaled_time_asinh`, две цели, 5 seeds, 4 решающих порога + `holdout_check` как предупреждение.
- Обучен Transformer (5 seeds × 2 цели = 10 прогонов) и XGBoost same-profile (1 seed × 2 цели) на честно одинаковых признаках (flattened).
- XGBoost same-profile обучен на тех же flattened признаках; transform params подбирались на train, не на val/holdout.
- Баг загрузчика исправлен в 5.0b; здесь buy target загружается корректно (22745 train rows).
- Проверки: OHLC verification, label sanity, XGBoost baselines (3 варианта).
- Holdout не входил в решение (`holdout_used_for_decision: false`).
- Trading winner не объявлялся.

## Multiple Testing Context

Search budget: 1 профиль × 2 цели × 1 модель (Transformer) × 5 seeds = 10 Transformer прогонов + 2 XGBoost same-profile + 2 × 3 XGBoost baselines = 18 training total.

Коррекция: этап проверочный, с заранее зафиксированными числовыми порогами (G1–G5). Дополнительной коррекции на множественный перебор не требуется — профиль один, без расширения сетки.

## Changed Files

- `ML/baseline/benchmark_stage5_transformer_breach.py` — Stage 5.0c constants, `build_flat_features` extended, `build_xgb_features_for_profile`, `compute_xgb_same_profile_baseline`, `stage5_0c_replication_decision`, `run_stage5_0c_cross_target_rerun`, `build_arg_parser()`, CLI `--stage5-0c-cross-target-rerun`.
- `tests/test_stage5_transformer_breach.py` — tests for all new functions (786 passed).
- `ML/reports/stage5_0c_cross_target_rerun.json` — structured artifact.
- `docs/ML/benchmark_stage5_transformer_breach.py.md` — module documentation updated.
- `CHANGELOG.md` — entry added.
- `docs/methodology/` — 8 files updated (поисковый/проверочный уровень).

## Verification

- Tests: `./.venv/bin/python -m pytest tests/ -q` — 786 passed, 0 failed.
- JSON artifact: `ML/reports/stage5_0c_cross_target_rerun.json` — записан, числа согласованы с отчётом.
- Seed 42 результаты идентичны 5.0b: sell 0.6673, buy 0.6752 — воспроизводимость single-seed подтверждена.
- G1–G5 gate логика проверена вручную по всем 5 seeds × 2 целям.

## Setup

- Profile: `all100_absolute_price_atr_scaled_time_asinh` (frozen, single)
- Targets: `sell_stop_broken_H6_off05_flag`, `buy_stop_broken_H6_off05_flag`
- Transform: `asinh`
- Scaler: train-only `StandardScaler`
- Seeds: `[42, 77, 123, 202, 777]` (безусловно, без single-seed gate)
- Dynamic corridor `seq_len`: disabled
- Holdout: 2023-2026, только раскрытие результата (`holdout_used_for_decision: false`)
- Trading winner: not declared

## Заранее зафиксированные пороги

### Решающие пороги (входят в `overall_pass`)

| Gate | Критерий | Sell | Buy | Pass |
|---|---|---|---|---|
| G1 AUC | median val AUC > xgb_same AUC, ≥4 seeds above xgb−0.005 | 0.6643 vs 0.6723 (0 seeds above) | 0.6752 vs 0.6873 (0 seeds above) | FAIL |
| G2 lift_30 | median val lift_30 < xgb_same lift_30 | 0.5570 vs 0.5229 | 0.5423 vs 0.5147 | FAIL |
| G3 cross_target | both targets pass G1+G2 | sell: FAIL, buy: FAIL | FAIL |
| G5 seed_spread | max−min val AUC < 0.03 | 0.0054 | 0.0104 | PASS |

**overall_pass: FAIL**

### Предупреждение по holdout (не входит в `overall_pass`)

| Проверка | Критерий | Sell | Buy | Статус |
|---|---|---|---|---|
| holdout_check | median holdout AUC ≥ median val AUC − 0.05 | drop 0.024 | drop 0.028 | OK |

## Mandatory Checks

| Check | Sell | Buy |
|---|---|---|
| OHLC verification | PASS (50/50, 0 mismatches) | PASS (50/50, 0 mismatches) |
| Label sanity | SANITY_ONLY, pos_rate 0.4065 | SANITY_ONLY, pos_rate 0.3701 |
| Train rows | 25672 | 22745 |
| Val rows | 2832 | 2580 |
| Holdout rows | 4527 | 4125 |

### XGBoost Baselines

| Variant | Sell val AUC | Sell holdout AUC | Buy val AUC | Buy holdout AUC |
|---|---|---|---|---|
| base_raw_plus_time | 0.6631 | 0.6524 | 0.6894 | 0.6552 |
| no_time | 0.6273 | 0.6456 | 0.6489 | 0.6298 |
| time_only | 0.6314 | 0.6059 | 0.6423 | 0.6233 |

## XGBoost Same-Profile Baseline

| Target | val AUC | val lift_30 | holdout AUC | holdout lift_30 |
|---|---|---|---|---|
| sell | 0.6723 | 0.5229 | 0.6558 | 0.5354 |
| buy | 0.6873 | 0.5147 | 0.6589 | 0.5429 |

## Transformer Multi-Seed Results

### Sell

| Seed | val_auc | val_lift_30 | holdout_auc | holdout_lift_30 |
|---:|---:|---:|---:|---:|
| 42 | 0.6673 | 0.5632 | 0.6448 | 0.6225 |
| 77 | 0.6643 | 0.5508 | 0.6430 | 0.6410 |
| 123 | 0.6629 | 0.5384 | 0.6369 | 0.6416 |
| 202 | 0.6619 | 0.5786 | 0.6404 | 0.6054 |
| 777 | 0.6645 | 0.5570 | 0.6341 | 0.6297 |

Summary: median val AUC = 0.6643, median val lift_30 = 0.5570, median holdout AUC = 0.6404, spread = 0.0054

### Buy

| Seed | val_auc | val_lift_30 | holdout_auc | holdout_lift_30 |
|---:|---:|---:|---:|---:|
| 42 | 0.6752 | 0.5423 | 0.6435 | 0.6079 |
| 77 | 0.6808 | 0.5527 | 0.6469 | 0.6350 |
| 123 | 0.6704 | 0.5561 | 0.6458 | 0.6437 |
| 202 | 0.6732 | 0.5285 | 0.6474 | 0.6135 |
| 777 | 0.6806 | 0.5250 | 0.6480 | 0.6482 |

Summary: median val AUC = 0.6752, median val lift_30 = 0.5423, median holdout AUC = 0.6469, spread = 0.0104

## Per-Target Verdict

| target | transformer median val_auc | xgb same-profile val_auc | auc_pass | lift_pass | seed_spread | target_pass |
|---|---|---|---|---|---|---|
| sell | 0.6643 | 0.6723 | FAIL | FAIL | PASS (0.0054) | FAIL |
| buy | 0.6752 | 0.6873 | FAIL | FAIL | PASS (0.0104) | FAIL |

**sell_pass**: false, **buy_pass**: false, **cross_target_pass**: false

## Replication Decision

| Gate | Pass | Detail |
|---|---|---|
| G1 AUC | FAIL | Transformer не превосходит XGBoost same-profile: 0 из 5 seeds выше порога для обеих целей |
| G2 lift_30 | FAIL | Transformer lift_30 выше XGBoost (меньше = лучше): sell 0.557 vs 0.523, buy 0.542 vs 0.515 |
| G3 cross_target | FAIL | Ни одна цель не прошла G1+G2 |
| G5 seed_spread | PASS | Sell spread 0.0054, buy spread 0.0104 (< 0.03) |
| Holdout check | OK | Sell drop 0.024, buy drop 0.028 (< 0.05) |

**overall_pass: false**

## Conclusions

Гипотеза 5.0b о профиле `all100_absolute_price_atr_scaled_time_asinh` **не воспроизвелась** при multi-seed повторной проверке с честным сравнением против XGBoost на тех же признаках.

Ключевой факт: Transformer на тех же признаках **систематически уступает XGBoost** по AUC и lift_30 на обеих целях. XGBoost показывает, что в профиле есть умеренный сигнал, но текущая Transformer-реализация извлекает его хуже, чем табличная модель.

Хорошая новость: seed spread узкий (sell 0.0054, buy 0.0104) — результаты стабильны, но стабильность слабого сигнала не создаёт полезный сигнал.

## Limitations / Open Questions

- Holdout 2023-2026 — только раскрытие результата, не использовался для решения (`holdout_used_for_decision: false`).
- `holdout_check` — OK, дропы в пределах толеранса (sell 0.024, buy 0.028).
- 5 seeds дают ограниченный CI; для торгового решения нужен block bootstrap CI.
- Buy и sell считаются на разных строках; AUC/lift не сравнимы между целями напрямую.
- XGBoost на этих же признаках показывает скромные результаты (val AUC 0.672-0.687) — сам профиль имеет ограниченную предсказательную силу.
- Transformer показывает переобучение: seed 42 sell, валидационная AUC растёт до 0.6673 на epoch 9, затем падает до 0.6445 на epoch 17 при продолжающемся падении train loss. На 25k строках Transformer систематически переобучается. Текущий эксперимент не различает причины: слабый сигнал, переобучение, или обе.

## Validation Split Disclosure

- val_stop: 2021-2022, использовался для всех метрик решения (AUC, lift_30, seed spread). Scaler, transform params и early stopping — только на train.
- holdout: 2023-2026, только раскрытие (`holdout_used_for_decision: false`), в overall_pass не входит.
- Split: train ≤2020 (sell 25672 строк, buy 22745), val_stop 2021-2022, holdout ≥2023.

## Next Step

Stage 5.0d — диагностический скрининг профилей (XGBoost + Logistic, без Transformer). План: `docs/superpowers/plans/2026-06-23-stage5_0d-diagnostic-screening.md`.

Цель: понять, какие фрактальные профили и группы признаков несут сигнал сверх raw features. Если ни один профиль не показывает улучшения — постановка H6_off05 stop broken на текущих профилях исчерпана.

## Related Materials

- `ML/reports/stage5_0c_cross_target_rerun.json`
- `docs/reports/2026-06-21-stage5_0b-asinh-rerun.md`
- `docs/superpowers/plans/2026-06-22-stage5_0c-cross-target-rerun.md`
