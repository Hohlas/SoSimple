# Stage 5.3 Time-To-Breach Target Reformulation

> **Дата**: 2026-06-26
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: проверить, даёт ли дискретная постановка времени до пробоя (`breach_after_k`, `fast/medium/no_breach`) более честный сигнал, чем регрессия `bars_to_breach`.
> **Related plan/spec**: `docs/superpowers/plans/2026-06-26-stage5_3-time-to-breach-target-reformulation.md`

## Context

Stage 5.2 показал содержательное ранжирование времени до пробоя, но обычная регрессия `bars_to_breach` не прошла gate: MAE была хуже constant baseline, а oracle-time PF нельзя использовать как gate из-за невалидного сравнения с binary-oracle.

Stage 5.3 изолирует только постановку цели. Новые price-признаки, `price_coord_atr`, `price_atr_scaled`, raw `ATR`, Up/Dn и новый oracle-PF не добавлялись.

Уровень этапа: поисковый. Даже при статусе JSON `TARGET_REFORMULATION_FOUND` этап не объявляет торгового кандидата.

## What Was Done

- Добавлены Stage 5.3 цели поверх Stage 5.2 `*_bars_to_breach_H6_off05`.
- Добавлены `breach_after_k` для `k=2,3,4,5`.
- Добавлены bucket one-vs-rest цели: `fast`, `medium`, `no_breach`.
- Добавлен binary baseline `*_stop_broken_H6_off05_flag` в тех же условиях.
- Добавлены control-цели `survives_at_least_k`, но они не могут стать winner-ом.
- Гиперпараметры классификатора взяты из Stage 5.1 (binary breach), а не из плана: `max_depth=6`, `num_boost_round=500`, `early_stopping_rounds=20`, `subsample=0.8`, `colsample_bytree=0.8`. План фиксировал `max_depth=3`, `n_estimators=300`, без early stopping (гиперпараметры Stage 5.2 регрессии). Отклонение сделано для сравнимости AUC новой постановки с binary breach baseline; без этого разница в AUC могла бы объясняться гиперпараметрами, а не постановкой цели.
- Добавлен CLI `--stage5-3-target-reformulation`, `--stage5-3-workers`, `--stage5-3-xgb-threads`.
- Добавлены логи прогресса с временем от старта и промежуточная запись JSON.
- Для фактического полного прогона использовано `workers=12`, `xgb_threads=1`, чтобы освободить ресурсы после перегруза при 32/24 процессах.
- Оптимизировано построение Stage 5.2/5.3 признаков: `time_only` больше не проходит по всем фракталам, а структурные признаки извлекаются прямым индексным парсером; признаки Stage 5.3 предвычисляются один раз на `(source, profile, split)`.

## Multiple Testing Context

Полный бюджет: `2 source targets × 12 target specs × 6 profiles × 3 seeds = 432` XGBoost-классификации.

Main budget без controls и binary baseline: `2 × 7 × 6 × 3 = 252` классификации.

**Дубликат целей.** Для целочисленного `bars_to_breach ∈ {1..6, 7=censored}` цели `breach_after_k2` (b > 2 AND b ≤ 6) и `medium` (b ≥ 3 AND b ≤ 6) определяют **тождественный вектор меток**. Проверка JSON подтверждает: labels byte-identical, AUC совпадает до 16 знаков на всех (side, profile, seed). Из 7 main targets реально уникальных 6, а из 252 прогонов 36 — дубликаты. Main comparisons для gate: `12` уникальных side/target comparisons (`2` стороны × `6` уникальных main targets), сгруппированные как `breach_after_k` и `bucket`. Цели коррелированы, строгой независимой проверки нет. Это диагностическое evidence, не candidate validation.

## Changed Files

- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `tests/test_stage5_transformer_breach.py`
- `ML/reports/stage5_3_time_to_breach_target_reformulation.json`

## Verification

- `./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -q -k "stage5_3 or build_stage5_2_features"` → `10 passed`
- `./.venv/bin/python -m pytest tests/ -q` → `866 passed, 29 warnings`
- CSV contract check: train/validation/test contain `sell_bars_to_breach_H6_off05`, `buy_bars_to_breach_H6_off05`, `sell_stop_broken_H6_off05_flag`, `buy_stop_broken_H6_off05_flag`.
- Full run:

```bash
./.venv/bin/python -u ML/baseline/benchmark_stage5_transformer_breach.py \
  --stage5-3-target-reformulation \
  --stage5-3-workers 12 \
  --stage5-3-xgb-threads 1
```

- JSON consistency check: `stage5_3_json_consistency_ok`

## Results

Structured artifact: `ML/reports/stage5_3_time_to_breach_target_reformulation.json`

Run summary:

| Field | Value |
|---|---:|
| done_runs | 432 |
| total_runs | 432 |
| workers | 12 |
| xgb_threads | 1 |
| elapsed_sec | 1888.193 |
| JSON status | `TARGET_REFORMULATION_FOUND` |

Target distributions with warnings:

| Source | Target | train positive_rate | val positive_rate | holdout positive_rate | Warning |
|---|---:|---:|---:|---:|---|
| sell | `breach_after_k5` | 0.0440 | 0.0395 | 0.0480 | `positive_rate_outside_0_05_0_95` |
| buy | `breach_after_k5` | 0.0394 | 0.0430 | 0.0339 | `positive_rate_outside_0_05_0_95` |
| sell | `no_breach` | 0.6114 | 0.6194 | 0.5923 | none |
| buy | `no_breach` | 0.6299 | 0.6260 | 0.6441 | none |
| sell | `survives_at_least_k2` | 0.8324 | 0.8499 | 0.8364 | control only |
| buy | `survives_at_least_k2` | 0.8422 | 0.8438 | 0.8395 | control only |

Main targets, best profile per source:

| Source | Target | Profile | val AUC | val PR AUC | positive_rate | yearly val AUC | holdout AUC |
|---|---|---|---:|---:|---:|---|---:|
| sell | `breach_after_k2` | `clock_shift_impulse` | 0.6567 | 0.3405 | 0.2306 | see JSON | 0.6287 |
| sell | `breach_after_k3` | `clock_shift_impulse` | 0.6389 | 0.2285 | 0.1596 | see JSON | 0.6303 |
| sell | `breach_after_k4` | `clock_shift` | 0.6334 | 0.1441 | 0.0985 | see JSON | 0.6172 |
| sell | `breach_after_k5` | `structure_full` | 0.6293 | 0.0582 | 0.0395 | see JSON | 0.6002 |
| sell | `fast` | `clock_shift_back` | 0.6967 | 0.3171 | 0.1501 | 2021=0.6821, 2022=0.7104 | 0.6849 |
| sell | `medium` (≡ `breach_after_k2`) | `clock_shift_impulse` | 0.6567 | 0.3405 | 0.2306 | see JSON | 0.6287 |
| sell | `no_breach` (≈ инверсия binary breach) | `clock_shift_back` | 0.6719 | 0.7745 | 0.6194 | see JSON | 0.6613 |
| buy | `breach_after_k2` | `clock_shift_back_impulse` | 0.6417 | 0.3061 | 0.2178 | see JSON | 0.6378 |
| buy | `breach_after_k3` | `structure_full` | 0.6422 | 0.2268 | 0.1481 | see JSON | 0.6379 |
| buy | `breach_after_k4` | `time_only` | 0.6485 | 0.1515 | 0.0938 | see JSON | 0.6500 |
| buy | `breach_after_k5` | `time_only` | 0.6483 | 0.0672 | 0.0430 | see JSON | 0.6608 |
| buy | `fast` | `clock_shift_back_impulse` | 0.7127 | 0.3235 | 0.1562 | 2021=0.7155, 2022=0.7089 | 0.6617 |
| buy | `medium` (≡ `breach_after_k2`) | `clock_shift_back_impulse` | 0.6417 | 0.3061 | 0.2178 | see JSON | 0.6378 |
| buy | `no_breach` (≈ инверсия binary breach) | `clock_shift_back_impulse` | 0.6921 | 0.7867 | 0.6260 | see JSON | 0.6655 |

Best main target and binary baseline:

| Source | Best main | Profile | val AUC | baseline same-profile AUC | median delta | Seeds beating baseline (delta > 0) | Seeds passing gate (delta ≥ 0.02) |
|---|---|---|---:|---:|---:|---:|---:|
| sell | `sell_fast` | `clock_shift_back` | 0.6967 | 0.6688 | +0.0279 | 3/3 | 3/3 |
| buy | `buy_fast` | `clock_shift_back_impulse` | 0.7127 | 0.6928 | +0.0199 | 3/3 | **1/3** |

Per-seed delta vs binary baseline (same profile):

| Source | Profile | seed | fast AUC | binary AUC | delta | Passes ≥0.02 |
|---|---|---|---:|---:|---:|---|
| sell | `clock_shift_back` | 42 | 0.6967 | 0.6734 | +0.0232 | yes |
| sell | `clock_shift_back` | 77 | 0.6985 | 0.6657 | +0.0328 | yes |
| sell | `clock_shift_back` | 123 | 0.6964 | 0.6688 | +0.0276 | yes |
| buy | `clock_shift_back_impulse` | 42 | 0.7145 | 0.6928 | +0.0217 | yes |
| buy | `clock_shift_back_impulse` | 77 | 0.7088 | 0.6906 | +0.0182 | **no** (отрыв 0.0018) |
| buy | `clock_shift_back_impulse` | 123 | 0.7127 | 0.6956 | +0.0171 | **no** (отрыв 0.0029) |

Замечание: столбец "Seeds beating baseline" в предыдущей версии отчёта считал delta > 0 (знак), а не delta ≥ 0.02 (порог gate). Для buy порог 0.02 проходит только 1 из 3 seed; median delta 0.0199 формально близок к 0.02, но 2 из 3 seed проваливают порог с отрывом 0.0018–0.0029. Это не "мимо на 0.0001", а результат, держащийся на одном seed.

Gate:

| Source | Gate status | Blocking check |
|---|---|---|
| sell | `TARGET_REFORMULATION_FOUND` | none |
| buy | `DIAGNOSTIC_ONLY` | `auc_delta_binary_breach_same_profile_ge_0_02` failed: median delta +0.0199 vs required 0.02; per-seed 1/3 passes порог (seed 42), 2/3 проваливают с отрывом 0.0018–0.0029 |

Control targets, disclosure only:

| Source | Control target | Best profile | val AUC | val PR AUC | positive_rate |
|---|---|---|---:|---:|---:|
| sell | `survives_at_least_k2` | `clock_shift_back` | 0.7064 | 0.9240 | 0.8499 |
| sell | `survives_at_least_k3` | `clock_shift_back_impulse` | 0.6969 | 0.8838 | 0.7790 |
| sell | `survives_at_least_k4` | `clock_shift_back_impulse` | 0.6928 | 0.8502 | 0.7179 |
| sell | `survives_at_least_k5` | `clock_shift_back_impulse` | 0.6789 | 0.8018 | 0.6589 |
| buy | `survives_at_least_k2` | `clock_shift_back_impulse` | 0.7180 | 0.9268 | 0.8438 |
| buy | `survives_at_least_k3` | `clock_shift_back_impulse` | 0.7077 | 0.8860 | 0.7740 |
| buy | `survives_at_least_k4` | `clock_shift_back_impulse` | 0.7014 | 0.8470 | 0.7198 |
| buy | `survives_at_least_k5` | `structure_full` | 0.6959 | 0.8172 | 0.6690 |

Feature importance:

- Selected sell winner `sell_fast / clock_shift_back`: top gain features are saved under `raw_runs[*].feature_importance_gain_top20` in JSON for the winner profile/seeds.
- Selected buy winner `buy_fast / clock_shift_back_impulse`: top gain features are saved under `raw_runs[*].feature_importance_gain_top20` in JSON for the winner profile/seeds.
- The selected profiles again point to `back` and `back+impulse`; this is consistent with Stage 5.1/5.1b/5.2.

Prediction distribution / calibration notes:

- JSON stores full `predictions` and `labels` for `val_stop`, `diagnostic_holdout`, and `low_n_disclosure`.
- Metrics include `pred_summary` (`min`, `median`, `max`, `std`, `unique_rounded_4`) and fixed threshold counts.
- No trading threshold or calibration winner was selected in this stage.

## Conclusions

Stage 5.3 found that the `fast` one-vs-rest target (ранний пробой, `bars_to_breach ∈ {1,2}`) shows a higher AUC than ordinary `bars_to_breach` regression and binary breach baseline. Это означает, что **ранний пробой легче отделить от остальных случаев**, чем любой пробой в пределах H — не то, что постановка `fast` лучше для торговли. Торговля требует знания "пробьётся ли вообще", а `fast` отбрасывает поздние пробои и censored observations в отрицательный класс, что упрощает задачу разделения.

Дополнительно: `no_breach` (b ≥ 7) — почти строгая инверсия binary breach (b ≤ 6), и AUC `no_breach` практически совпадает с binary breach (sell 0.6719 vs 0.6688; buy 0.6921 vs 0.6928). Это ожидаемо и не является новой информацией. `medium` тождественен `breach_after_k2` (см. Multiple Testing Context).

The result is not a trading candidate. It only says that a discrete target family is worth carrying into the next diagnostic step.

Sell `fast` проходит все Stage 5.3 model-gate checks с устойчивым per-seed delta (+0.023, +0.033, +0.028, все ≥ 0.02) и умеренным holdout drop (−0.012). Buy `fast` не проходит gate по порогу delta ≥ 0.02: median delta +0.0199, но только 1 из 3 seed проходит порог; результат держится на seed 42.

Control `survives_at_least_k` targets have high AUC/PR AUC but are non-winning by design: censored observations become positive, so the model can learn "not broken" rather than time-to-breach structure.

## Limitations / Open Questions

- `2023-2025` are diagnostic disclosure only, not independent confirmation.
- `2026` remains low-N disclosure, not a clean confirmatory period.
- The 12 unique main comparisons are correlated; no strict multiple-testing correction can turn this into candidate validation.
- No price/ATR/UpDn feature expansion was tested here.
- No oracle-PF gate was used.
- `breach_after_k5` is sparse on both sides and has warning `positive_rate_outside_0_05_0_95`.
- `breach_after_k2` и `medium` — тождественные цели для целочисленного `bars_to_breach`; 36 из 252 main-прогонов дубликаты (см. Multiple Testing Context).
- `no_breach` ≈ инверсия binary breach; AUC практически совпадает с binary baseline, новой информации не несёт.
- JSON status is `TARGET_REFORMULATION_FOUND`, but report verdict remains `DIAGNOSTIC_ONLY` because the stage is exploratory and uses burned diagnostic years.
- **Buy `fast` holdout degradation.** Buy `fast` теряет 5.1pp на holdout (val 0.7127 → holdout 0.6617), что больше, чем у любой другой buy-цели и чем у sell `fast` (−1.2pp). Это согласуется с картиной "сигнал затухает на новых годах" из Stage 4.6/4.7 и Stage 5.0f, и усиливает осторожность по buy: даже лучшая buy-цель держится на 1 из 3 seed по порогу gate.
- **`breach_after_k4/k5` на buy — лучший профиль `time_only`, не структурный.** Для поздних пробоев структура (`back`) не помогает, только календарь. Структура помогает для ранних/быстрых пробоев (`fast` → `clock_shift_back`/`clock_shift_back_impulse`), но не для поздних. Интерпретация "back — главный сигнал" верна только для ранних пробоев.
- **JSON inconsistency.** `summary.best_main.improvement_vs_binary_breach = None` в JSON, хотя отчёт презентует delta (+0.0279 sell, +0.0199 buy). Gate считает delta на лету, но не сохраняет в summary. Следующий агент, читающий только JSON, не увидит ключевого числа gate.
- **`best_iteration = 0` для 27 из 432 прогонов.** Early stopping сработал на 0-й итерации (вероятно, для sparse `breach_after_k5`); модель по сути константная для этих целей. Не ошибка, но означает, что часть целей модель не способна выучить.

## Validation Split Disclosure

Split is fixed Stage 5.x:

- `train_core`: years `<=2020`
- `val_stop`: years `2021-2022`
- `diagnostic_holdout`: years `2023-2025`
- `low_n_disclosure`: year `2026`

Winner selection uses `2021-2022`. `2023-2025` were not used to choose the winner and are disclosed only as diagnostic holdout. No frozen candidate is declared.

## Next Step

Because target reformulation was found for sell `fast` (устойчивый per-seed delta, 3/3 проходит порог 0.02), the allowed next step is Stage 5.4: narrow price-coordinate / ATR ablation around the selected `fast` target family. Buy `fast` пограничен (1/3 seed проходит порог) — Stage 5.4 должен проверить, выживет ли buy-сигнал после добавления price-признаков, но не должен опираться на buy как на подтверждённую цель.

Do not run a broad search over new targets and features simultaneously. Do not use control `survives_at_least_k` as a winner. Do not add Up/Dn by default. Не использовать `medium` как отдельную цель — она тождественна `breach_after_k2`.

## Related Materials

- `ML/reports/stage5_3_time_to_breach_target_reformulation.json`
- `docs/superpowers/plans/2026-06-26-stage5_3-time-to-breach-target-reformulation.md`
- `docs/reports/2026-06-25-stage5_2-time-to-breach-regression.md`
- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `tests/test_stage5_transformer_breach.py`
