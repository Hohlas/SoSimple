# Fractal Stop Stage 3 — Feature Profile Comparison

> **Date**: 2026-06-10
> **Status**: Completed
> **Verdict**: `relative_geometry` +57…+258 bp AUC uplift over base_raw и является текущим победителем среди feature profile на validation. `base_plus_path` −64…−166 bp (hurt). Перед XGBoost нужен Stage 3.1: разложить `relative_geometry` на компоненты и понять, что именно даёт uplift.
> **Goal**: Проверить 3 feature profile на uplift в breach AUC/lift. Разделить эффект признаков на уровне RF-классификатора до торгового слоя.
> **Related**: Stage 1 (`docs/reports/2026-06-10-fractal-stop-breach-stage1.md`), Stage 2 (`docs/reports/2026-06-10-fractal-stop-fav-stage2.md`), EDA normalisation stats (10 Jun)
> **Related commit**: pending

## Context

Stage 2 oracle-диагностика показала: проблема в текущей RF-модели (AUC около 0.65), не в полном отсутствии диагностического потолка у механики (oracle PF=∞). Stage 3 — первый шаг к улучшению классификатора: сравнение 3 профилей признаков на breach-таргетах без торгового слоя. Метрика: AUC, lift, годовая устойчивость.

## What Was Done

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

## Методологические примечания

### Артефакт parse_fractal() не затрагивает Stage 3

После дополнительной проверки выяснено: в CSV нет пустых фрактальных ячеек. Все 100 `fractal*` ячеек каждой строки заполнены валидными 23-полевыми строками.

Ранняя оценка fill rate около 39.5% была артефактом функции `parse_fractal()` в диагностическом коде: после `normalize_rowwise()` поля вроде `break`, `strong`, `count` могут быть float-значениями (`0.1700000018`, `0.85`, ...), а parser ожидал integer и падал на `int(parts[6])`. Дальше `_parse_fractal_levels()` останавливался на первом `None`, поэтому оставшиеся фракталы строки ошибочно считались отсутствующими.

Stage 3 benchmark этой ошибкой не затронут: `ML/baseline/benchmark_fractal_stop_stage3.py` извлекает поля через `pd.to_numeric(..., errors='coerce').fillna(0.0)`, поэтому корректно читает нормализованные float-значения.

Практическое следствие:
- `parse_fractal()` годится для сырых данных до нормализации или должен быть исправлен под float-поля;
- для нормализованных `_labeled.csv` безопаснее использовать pandas-экстрактор Stage 3 либо чинить parser;
- вывод про `base_plus_path` и `relative_geometry` не объясняется пустыми CSV-ячейками.

### Оставшиеся ограничения признаков

1. В `relative_geometry` одновременно изменены три группы: `price` заменён на ATR-relative price, добавлены `density`, добавлены `time`. Поэтому текущий отчёт доказывает пользу всего профиля, но не доказывает отдельно пользу `density` или `time`.
2. Текущая реализация `density` считает сам `fractal0` в плотности уровней вокруг `f0_price`. Это не future leakage, но делает density частично тривиальным признаком. Нужно проверить вариант `density_excl_f0`, где счёт начинается с `fractal1`.
3. `base_plus_path` проверял folded `mov_h`, `shift` и `atr_ratio` вместе. Отрицательный результат профиля не равен строгому запрету на каждый из этих признаков отдельно.

## Conclusions

1. **base_plus_path — FAIL для RF breach.** Комбинированный профиль folded `mov_h` (mov_3…mov_48), `shift`, `log(fractal_atr/ATR)` ухудшает AUC на 64–166 bp консистентно по всем 8 таргетам. Рабочая гипотеза: фиксированные h-окна движения от фрактала плохо согласованы с моментом принятия решения и дают шум для RF, особенно когда смешаны со `shift` и `atr_ratio` по всем 100 уровням.

2. **relative_geometry — PASS как целый профиль.** Замена price→(price−f0_price)/ATR + density(6) + time(4) даёт средний uplift +119 bp AUC. Самый сильный прирост на off05-таргетах (+225–258 bp), где breach rate ниже (~38–53%) и классификация сложнее. Price-in-ATR делает фрактальные уровни сопоставимыми вне зависимости от абсолютной цены золота ($1000 vs $2000).

3. **Density перспективен, но не изолирован.** Счётчики фракталов в ±1/2/3 ATR вокруг f0_price могут добавлять структурную информацию о «плотности облака» уровней. Но текущий эксперимент не отделяет вклад density от замены price и time-фич. Нужна абляция `relative_price_only` vs `relative_price+density_excl_f0`.

4. **Time-фичи перспективны, но не изолированы.** sin/cos часа и дня недели могут отражать сессионную структуру пробоев. Но текущий профиль не доказывает их отдельный вклад. Нужна абляция `relative_price_only` vs `relative_price+time`.

5. **Gap до целевого AUC≥0.75 остаётся большим.** relative_geometry поднимает AUC до 0.643–0.678. До 0.75 остаётся около 7.2 процентного пункта по лучшему target и около 9.2 процентного пункта по среднему AUC. Это 720–920 bp, не 7–8 bp. Рост AUC сам по себе не гарантирует PF>1.0 в торговом слое: Stage 2 уже показал, что breach-сигнал должен быть проверен через execution-aware simulation.

## Итоговые цифры

| Метрика | base_raw | base_plus_path | relative_geometry |
|---------|----------|----------------|-------------------|
| N фич | 1001 | 1701 | 1011 |
| AUC min | 0.6200 | 0.6098 | 0.6425 |
| AUC max | 0.6812 | 0.6682 | 0.6775 |
| AUC mean | 0.6454 | 0.6335 | 0.6580 |
| ΔAUC mean (bp) | — | −119 | **+119** |
| Δlift mean | — | −0.10 | **+0.08** |
| Yearly fails | 0/32 | 0/32 | 0/32 |

## Next Step

Перед XGBoost нужен короткий Stage 3.1: очистить и разложить `relative_geometry` на компоненты.

Минимальная матрица:

| Профиль | Цель |
|---------|------|
| `base_raw` | Контрольный baseline |
| `relative_price_only` | Проверить, даёт ли uplift сама замена raw price на `(price-f0_price)/ATR` |
| `relative_price_plus_density_excl_f0` | Проверить вклад density без тривиального счёта `fractal0` |
| `relative_price_plus_time` | Проверить вклад временных признаков |
| `relative_geometry_clean` | Итоговый профиль: relative price + `density_excl_f0` + time |

Если `relative_geometry_clean` сохраняет большую часть uplift Stage 3, следующий шаг — XGBoost/LightGBM на этом очищенном профиле с небольшим grid search только на validation. Test не открывать. При AUC около 0.70+ и сохранении годовой устойчивости — вернуться к торговому слою с новым breach-классификатором.

## Related Materials

- `ML/baseline/benchmark_fractal_stop_stage3.py` — скрипт сравнения профилей
- `ML/reports/stage3_profiles.json` — полные результаты (AUC, lift, yearly)
- `docs/reports/2026-06-10-fractal-stop-breach-stage1.md` — Stage 1 breach baseline
- `docs/reports/2026-06-10-fractal-stop-fav-stage2.md` — Stage 2 trading layer + oracle
- `docs/reports/2026-04-19-current-feature-importance-diagnostics.md` — feature importance (geometry dominates)
- `docs/reports/2026-06-04-fractal-ablation.md` — 29-channel ablation
