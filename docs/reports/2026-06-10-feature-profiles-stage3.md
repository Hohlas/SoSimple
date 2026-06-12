# Fractal Stop Stage 3.x — Feature Profiles and XGBoost Breach Classifier

> **Date**: 2026-06-10
> **Status**: Completed
> **Verdict**: Stage 3.2 дал новый лучший breach-классификатор: XGBoost `base_raw_plus_time` AUC mean 0.6799, lift mean 2.00, +345 bp к RF `base_raw`. `relative_geometry_clean` почти равен ему (0.6808), но сложнее; основной практический кандидат для Stage 4 — XGBoost `base_raw_plus_time`.
> **Goal**: Проверить feature profile на uplift в breach AUC/lift, разложить вклад `relative_geometry`, затем проверить XGBoost как более сильную табличную модель до возврата к торговому слою.
> **Related**: Stage 1 (`docs/reports/2026-06-10-fractal-stop-breach-stage1.md`), Stage 2 (`docs/reports/2026-06-10-fractal-stop-fav-stage2.md`), EDA normalisation stats (10 Jun)
> **Related commit**: pending

## Context

Stage 2 oracle-диагностика показала: проблема в текущей RF-модели (AUC около 0.65), не в полном отсутствии диагностического потолка у механики (oracle PF=∞). Stage 3.x — линия улучшения breach-классификатора без торгового слоя: сначала feature profiles на RF, затем абляция компонентов, затем XGBoost. Метрики: AUC, lift, годовая устойчивость. Test не открывался.

## What Was Done

### Stage 3 — RF feature profile comparison

Три feature profile, все извлекаются из CSV (без OHLC, без выявленной future leakage):

| Профиль | N фич | Состав |
|---------|-------|--------|
| `base_raw` | 1001 | 10 каналов × 100 фракталов + ATR (текущий Stage 1/2) |
| `base_plus_path` | 1701 | base_raw + folded `mov_h` (5×100) + `shift` (100) + `log(fractal_atr/ATR)` (100) |
| `relative_geometry` | 1011 | price → (price−f0_price)/ATR + density(6) + time(4) + base channels + ATR |

**Почему именно эти 3:**
- `base_raw` — baseline, с чем сравниваем
- `base_plus_path` — проверка folded `mov_h` концепта (из обсуждения EDA up/dn)
- `relative_geometry` — проверка price-in-ATR + density + time (из рекомендаций feature importance diagnostics)

**Модель**: RandomForestClassifier(n_estimators=200, max_depth=12, min_samples_leaf=50, random_state=42). 8 breach таргетов (H6/H12 × off02/off05 × buy/sell). Train: 2004–2019, Val: 2019–2022 (purge 12 баров).

**Скрипт**: `ML/baseline/benchmark_fractal_stop_stage3.py`
**JSON**: `ML/reports/stage3_profiles.json`

### Stage 3.1 — RF ablation of relative geometry

Проверено, какой компонент даёт uplift в `relative_geometry`:

| Профиль | N фич | Цель |
|---------|-------|------|
| `base_raw` | 1001 | Контрольный baseline |
| `relative_price_only` | 1001 | Только замена `price` на `(price-f0_price)/ATR` |
| `relative_price_plus_density_excl_f0` | 1007 | Relative price + density без счёта `fractal0` |
| `relative_price_plus_time` | 1005 | Relative price + 4 time-фичи |
| `relative_geometry_clean` | 1011 | Relative price + `density_excl_f0` + time |

**Скрипт**: `ML/baseline/benchmark_fractal_stop_stage3_1.py`
**JSON**: `ML/reports/stage3_1_profiles.json`

### Stage 3.2 — XGBoost comparison

Проверено, даёт ли более сильная табличная модель прирост над RF:

| Профиль | N фич | Цель |
|---------|-------|------|
| `time_only` | 4 | Проверка, достаточно ли только час/день недели |
| `base_raw` | 1001 | XGBoost на базовых фрактальных признаках |
| `base_raw_plus_time` | 1005 | Базовые фракталы + time-фичи |
| `relative_geometry_clean` | 1011 | Clean geometry из Stage 3.1 |

**Модель**: XGBoost, `n_estimators=200`, `max_depth=6`, `learning_rate=0.05`, `subsample=0.8`, `colsample_bytree=0.8`, `scale_pos_weight`, early stopping по validation AUC.

**Скрипт**: `ML/baseline/benchmark_fractal_stop_stage3_2.py`
**JSON**: `ML/reports/stage3_2_xgboost.json`

## Changed Files

- `ML/baseline/benchmark_fractal_stop_stage3.py` — Stage 3 RF profile comparison.
- `ML/baseline/benchmark_fractal_stop_stage3_1.py` — Stage 3.1 RF ablation.
- `ML/baseline/benchmark_fractal_stop_stage3_2.py` — Stage 3.2 XGBoost comparison.
- `ML/reports/stage3_profiles.json` — Stage 3 full metrics.
- `ML/reports/stage3_1_profiles.json` — Stage 3.1 full metrics.
- `ML/reports/stage3_2_xgboost.json` — Stage 3.2 full metrics.

## Verification

- Все сравнения выполнены только на train/validation; test не использовался.
- Для всех Stage 3.x профилей проверены 8 breach targets: H6/H12 × off02/off05 × buy/sell.
- Для Stage 3 и 3.2 проверена годовая устойчивость: 0 срезов с AUC<0.55.
- Stage 3.2 использует early stopping только по validation; это допустимо для model development, но winner для торгового слоя всё равно должен выбираться отдельно по validation PF.

## Results

### base_raw (1001 фич — baseline)

| Target | AUC | lift | PR-AUC |
|--------|-----|------|--------|
| buy_H6_off02 | 0.6363 | 1.61 | 0.5806 |
| sell_H6_off02 | 0.6514 | 1.73 | 0.6154 |
| buy_H6_off05 | 0.6200 | 1.62 | 0.4564 |
| sell_H6_off05 | 0.6224 | 1.71 | 0.4764 |
| buy_H12_off02 | 0.6561 | 1.55 | 0.7119 |
| sell_H12_off02 | 0.6812 | 1.66 | 0.7570 |
| buy_H12_off05 | 0.6346 | 1.52 | 0.6096 |
| sell_H12_off05 | 0.6612 | 1.77 | 0.6669 |

Годовая разбивка (AUC): все срезы 2019–2022 выше 0.59, без провалов.

### base_plus_path (1701 фич)

| Target | AUC | ΔAUC (bp) | Δlift |
|--------|-----|-----------|-------|
| buy_H6_off02 | 0.6246 | −117 | −0.12 |
| sell_H6_off02 | 0.6348 | −166 | −0.11 |
| buy_H6_off05 | 0.6098 | −102 | −0.10 |
| sell_H6_off05 | 0.6129 | −95 | −0.08 |
| buy_H12_off02 | 0.6497 | −64 | −0.09 |
| sell_H12_off02 | 0.6682 | −130 | −0.09 |
| buy_H12_off05 | 0.6222 | −124 | −0.07 |
| sell_H12_off05 | 0.6458 | −154 | −0.16 |

**Все 8 таргетов — отрицательный delta. Комбинированный профиль folded `mov_h` + `shift` + `atr_ratio` ухудшает breach-классификатор RF.** Из этого результата нельзя отдельно доказать, что каждый из трёх компонентов вреден сам по себе.

### relative_geometry (1011 фич)

| Target | AUC | ΔAUC (bp) | Δlift |
|--------|-----|-----------|-------|
| buy_H6_off02 | 0.6564 | **+201** | +0.17 |
| sell_H6_off02 | 0.6571 | **+57** | −0.04 |
| buy_H6_off05 | 0.6425 | **+225** | +0.19 |
| sell_H6_off05 | 0.6482 | **+258** | +0.12 |
| buy_H12_off02 | 0.6656 | **+95** | +0.05 |
| sell_H12_off02 | 0.6775 | −37 | +0.01 |
| buy_H12_off05 | 0.6428 | **+82** | +0.15 |
| sell_H12_off05 | 0.6685 | **+73** | +0.07 |

**7/8 таргетов — положительный delta.** Средний uplift +119 bp. sell_H12_off02 −37 bp (в пределах шума).

Годовая разбивка relative_geometry (AUC):

| Target | 2019 | 2020 | 2021 | 2022 |
|--------|------|------|------|------|
| buy_H6_off02 | 0.636 | 0.627 | 0.684 | 0.670 |
| sell_H6_off02 | 0.663 | 0.660 | 0.662 | 0.647 |
| buy_H6_off05 | 0.630 | 0.620 | 0.655 | 0.659 |
| sell_H6_off05 | 0.637 | 0.667 | 0.655 | 0.628 |
| buy_H12_off02 | 0.672 | 0.631 | 0.688 | 0.675 |
| sell_H12_off02 | 0.694 | 0.667 | 0.677 | 0.681 |
| buy_H12_off05 | 0.643 | 0.608 | 0.666 | 0.654 |
| sell_H12_off05 | 0.682 | 0.691 | 0.639 | 0.665 |

Все 32 годовых среза AUC ≥ 0.59 — без провалов.

### Yearly stability (сводка)

| Профиль | Срезов с AUC<0.55 |
|---------|-------------------|
| base_raw | 0/32 |
| base_plus_path | 0/32 |
| relative_geometry | 0/32 |

### Stage 3.1 — что реально дало uplift

| Профиль | N фич | AUC mean | ΔAUC vs RF base_raw (bp) | Δlift | Δlow-risk breach rate (bp) |
|---------|-------|----------|---------------------------|-------|-----------------------------|
| `base_raw` | 1001 | 0.6454 | — | — | — |
| `relative_price_only` | 1001 | 0.6414 | −40 | −0.03 | +52 |
| `relative_price_plus_density_excl_f0` | 1007 | 0.6422 | −32 | −0.06 | +106 |
| `relative_price_plus_time` | 1005 | 0.6575 | +121 | +0.11 | −197 |
| `relative_geometry_clean` | 1011 | 0.6581 | +127 | +0.11 | −186 |

Ключевой вывод Stage 3.1: uplift в `relative_geometry` был почти целиком от time-фичей. `price/ATR` сам по себе ухудшил RF AUC, `density_excl_f0` не дал самостоятельной пользы. Поэтому старое название `relative_geometry` оказалось слишком сильной интерпретацией: рабочий компонент — сессионное время, а не плотность фрактальной геометрии.

### Stage 3.2 — XGBoost

| Профиль | N фич | AUC mean | ΔAUC vs XGB base_raw (bp) | ΔAUC vs RF base_raw (bp) | lift mean | Yearly fails |
|---------|-------|----------|----------------------------|---------------------------|-----------|--------------|
| `time_only` | 4 | 0.6300 | −294 | −154 | 1.60 | 0 |
| `base_raw` | 1001 | 0.6594 | — | +140 | 1.82 | 0 |
| `base_raw_plus_time` | 1005 | 0.6799 | +205 | +345 | 2.00 | 0 |
| `relative_geometry_clean` | 1011 | 0.6808 | +214 | +354 | 1.99 | 0 |

Ответы Stage 3.2:

1. **Фракталы несут сигнал поверх времени.** `base_raw` 0.6594 против `time_only` 0.6300: +294 bp.
2. **XGBoost лучше RF на тех же base_raw признаках.** +140 bp к RF `base_raw`.
3. **Лучшее рабочее сочетание — фракталы + time.** `base_raw_plus_time` даёт +345 bp к RF `base_raw`.
4. **`relative_geometry_clean` не даёт практически значимого преимущества.** 0.6808 против 0.6799 у `base_raw_plus_time`: разница 9 bp, это шум для выбора более сложного профиля.

Лучший отдельный target: `sell_H12_off02`, XGBoost `base_raw_plus_time`, AUC 0.6956. Средний AUC всё ещё ниже gate 0.70: разрыв 0.0201 AUC, то есть около 201 bp, а не 20 bp.

## Методологические примечания

### Артефакт parse_fractal() не затрагивает Stage 3

После дополнительной проверки выяснено: в CSV нет пустых фрактальных ячеек. Все 100 `fractal*` ячеек каждой строки заполнены валидными 23-полевыми строками.

Ранняя оценка fill rate около 39.5% была артефактом функции `parse_fractal()` в диагностическом коде: после `normalize_rowwise()` поля вроде `break`, `strong`, `count` могут быть float-значениями (`0.1700000018`, `0.85`, ...), а parser ожидал integer и падал на `int(parts[6])`. Дальше `_parse_fractal_levels()` останавливался на первом `None`, поэтому оставшиеся фракталы строки ошибочно считались отсутствующими.

Stage 3 benchmark этой ошибкой не затронут: `ML/baseline/benchmark_fractal_stop_stage3.py` извлекает поля через `pd.to_numeric(..., errors='coerce').fillna(0.0)`, поэтому корректно читает нормализованные float-значения.

Практическое следствие:
- разметочный `parse_fractal()` нельзя использовать как универсальный float feature extractor для нормализованных `fractal*` полей;
- для нормализованных `_labeled.csv` безопаснее использовать pandas-экстрактор Stage 3.x или отдельный ML feature extractor;
- вывод про `base_plus_path` и `relative_geometry` не объясняется пустыми CSV-ячейками.

### Оставшиеся ограничения Stage 3.x

1. Stage 3.1 изолировал вклад `price`, `density_excl_f0` и `time` только для RF. Для XGBoost проверены `base_raw_plus_time` и `relative_geometry_clean`, но не отдельная XGBoost-абляция `relative_price_only` и `density_excl_f0`.
2. `relative_geometry_clean` на XGBoost выше `base_raw_plus_time` всего на 9 bp. Это не доказывает, что price/density бесполезны для любой модели, но не даёт практического основания усложнять Stage 4.
3. `base_plus_path` проверял folded `mov_h`, `shift` и `atr_ratio` вместе. Отрицательный результат профиля не равен строгому запрету на каждый из этих признаков отдельно.
4. Stage 3.x измеряет AUC/lift breach-классификатора. Торговый PF, просадка, концентрация прибыли и устойчивость по сделкам должны проверяться отдельно в Stage 4.

## Conclusions

1. **base_plus_path — FAIL для RF breach.** Комбинированный профиль folded `mov_h` (mov_3…mov_48), `shift`, `log(fractal_atr/ATR)` ухудшает AUC на 64–166 bp консистентно по всем 8 таргетам. Рабочая гипотеза: фиксированные h-окна движения от фрактала плохо согласованы с моментом принятия решения и дают шум для RF, особенно когда смешаны со `shift` и `atr_ratio` по всем 100 уровням.

2. **Первичный `relative_geometry` был полезен как профиль, но интерпретация изменилась.** Stage 3 показал +119 bp, но Stage 3.1 разложил uplift: `relative_price_only` −40 bp, `density_excl_f0` не спасает профиль, а `relative_price_plus_time` даёт +121 bp. Следовательно, практический вклад был от time-фичей.

3. **Time-фичи полезны, но не заменяют фракталы.** `time_only` AUC mean 0.6300, тогда как XGBoost `base_raw` даёт 0.6594. Значит модель не свелась к календарному фильтру; фрактальная структура несёт отдельный сигнал.

4. **XGBoost существенно улучшает breach-классификатор.** На `base_raw` XGBoost даёт +140 bp к RF, а `base_raw_plus_time` даёт +345 bp к RF `base_raw`. Это лучший на данный момент табличный breach-классификатор.

5. **`base_raw_plus_time` предпочтительнее `relative_geometry_clean` для Stage 4.** `relative_geometry_clean` имеет чуть больший mean AUC (0.6808 vs 0.6799), но преимущество 9 bp не оправдывает более сложный feature contract. Основной кандидат: XGBoost `base_raw_plus_time`; `relative_geometry_clean` можно оставить как контроль.

6. **AUC gate 0.70 не достигнут по mean.** Лучший mean AUC 0.6808, разрыв до 0.70 около 192 bp. Лучший отдельный target 0.6956 близок к 0.70, но это не заменяет средний gate и не доказывает PF>1.0.

7. **Следующий вопрос — торговая конвертация, не ещё одна feature ablation.** Stage 3.x уже показал заметный прирост ранжирования. Теперь нужно проверить, превращается ли он в validation PF при canonical spread и том же execution-aware симуляторе, что использовался в Stage 2.

## Итоговые цифры Stage 3 RF

| Метрика | base_raw | base_plus_path | relative_geometry |
|---------|----------|----------------|-------------------|
| N фич | 1001 | 1701 | 1011 |
| AUC min | 0.6200 | 0.6098 | 0.6425 |
| AUC max | 0.6812 | 0.6682 | 0.6775 |
| AUC mean | 0.6454 | 0.6335 | 0.6580 |
| ΔAUC mean (bp) | — | −119 | **+119** |
| Δlift mean | — | −0.10 | **+0.08** |
| Yearly fails | 0/32 | 0/32 | 0/32 |

## Итоговые цифры Stage 3.1/3.2

| Этап | Лучший практический профиль | Модель | AUC mean | ΔAUC vs RF base_raw | Вывод |
|------|-----------------------------|--------|----------|----------------------|-------|
| Stage 3.1 | `relative_price_plus_time` / `relative_geometry_clean` | RF | 0.6575 / 0.6581 | +121 / +127 bp | Uplift даёт time, не density |
| Stage 3.2 | `base_raw_plus_time` | XGBoost | 0.6799 | +345 bp | Лучший простой кандидат для Stage 4 |
| Stage 3.2 control | `relative_geometry_clean` | XGBoost | 0.6808 | +354 bp | На 9 bp выше, но сложнее |

## Next Step

Stage 4 validation-only: проверить, транслируется ли XGBoost `base_raw_plus_time` в положительный торговый PF.

Рекомендуемый протокол:

1. Основной профиль: XGBoost `base_raw_plus_time`; `relative_geometry_clean` — только контроль.
2. Прогнать все 8 side/H/off, не только лучший по AUC.
3. Grid торговых правил держать небольшим и заранее фиксированным.
4. Winner выбирать только по validation PF при canonical spread 0.20.
5. Gate: PF > 1.15 на validation, достаточно сделок в год, не больше 1 отрицательного года, bootstrap/uncertainty check.
6. Test не открывать до freeze одного validation winner. Test 2022–2026 уже использовался в Stage 1/2, поэтому для production-вывода всё равно нужен отдельный forward-период.
7. Если Stage 4 не даст PF>1.0 на validation — переходить к Transformer encoder или пересмотру постановки.

## Related Materials

- `ML/baseline/benchmark_fractal_stop_stage3.py` — скрипт сравнения профилей
- `ML/baseline/benchmark_fractal_stop_stage3_1.py` — Stage 3.1 RF ablation
- `ML/baseline/benchmark_fractal_stop_stage3_2.py` — Stage 3.2 XGBoost comparison
- `ML/reports/stage3_profiles.json` — полные результаты (AUC, lift, yearly)
- `ML/reports/stage3_1_profiles.json` — Stage 3.1 полные результаты
- `ML/reports/stage3_2_xgboost.json` — Stage 3.2 полные результаты
- `docs/reports/2026-06-10-fractal-stop-breach-stage1.md` — Stage 1 breach baseline
- `docs/reports/2026-06-10-fractal-stop-fav-stage2.md` — Stage 2 trading layer + oracle
- `docs/reports/2026-04-19-current-feature-importance-diagnostics.md` — feature importance (geometry dominates)
- `docs/reports/2026-06-04-fractal-ablation.md` — 29-channel ablation
