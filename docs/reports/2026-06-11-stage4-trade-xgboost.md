# Fractal Stop Stage 4 — XGBoost Trading Layer

> **Date**: 2026-06-11
> **Status**: Completed, updated with Stage 4.1 controls
> **Verdict**: FAIL — XGBoost breach-классификатор (AUC 0.68) не конвертируется в статистически значимый PF на validation. 7/8 Stage 4 primary-таргетов PF < 1.0. Winner `sell_H6_off05` (PF=1.106, BS_p05=0.923) не статистически значим. Stage 4.1 проверил два контрольных улучшения: XGBoost-fav ухудшил PF на всех 4 SELL-таргетах, combined breach H6+H12 дал PF=1.065 с `perm_p=0.050` и не превзошёл Stage 4 winner. Табличные модели на текущем представлении фракталов достигли практического потолка для этой торговой постановки.
> **Goal**: Проверить, транслируется ли прирост XGBoost breach-классификатора (Stage 3.2) в положительный торговый PF на validation. Primary: `base_raw_plus_time`, control: `relative_geometry_clean`.
> **Related**: Stage 1 (`2026-06-10-fractal-stop-breach-stage1.md`), Stage 2 (`2026-06-10-fractal-stop-fav-stage2.md`), Stage 3.x (`2026-06-10-feature-profiles-stage3.md`)
> **Related commit**: pending

## Context

Stage 2 (RF breach + RF fav) дал PF < 1.0 на всех 8 таргетах. Oracle-диагностика показала PF=∞ — проблема в модели, не в механике. Stage 3.1/3.2 довели AUC breach-классификатора с RF 0.645 до XGBoost 0.680 (+345 bp). Stage 4 проверяет, достаточно ли этого прироста для статистически значимого торгового PF и gate PF > 1.15.

Гипотеза: XGBoost breach + RF fav → торговое правило (как в Stage 2) → PF > 1.0 на validation. Fav-регрессор оставлен RF для изоляции вклада breach-классификатора.

После аудита Stage 4 выполнен Stage 4.1: XGBoost-fav вместо RF-fav, combined breach-фильтр H6 AND H12 и permutation test для проверки, насколько winner отличается от случайной перестановки breach-вероятностей.

## What Was Done

### 1. Модели

- **Breach**: XGBoost, `n_estimators=200`, `max_depth=6`, `learning_rate=0.05`, `subsample=0.8`, `colsample_bytree=0.8`, `scale_pos_weight`, early stopping по validation AUC.
- **Fav**: RandomForestRegressor, `n_estimators=200`, `max_depth=12`, `min_samples_leaf=50` (без изменений от Stage 2).

### 2. Профили признаков

| Профиль | N фич | Состав |
|---------|-------|--------|
| `base_raw_plus_time` (primary) | 1005 | 10 каналов × 100 фракталов + ATR + 4 time-фичи |
| `relative_geometry_clean` (control) | 1011 | base_raw с price→(price−f0_price)/ATR + density_excl_f0 + time |

### 3. Торговый симулятор

- Entry: Open следующего H1-бара
- Stop: за экстремум fractal0 + stop_offset × ATR
- TP: доля `tp_fraction` от `fav_pred`, потолок 5.0 ATR
- Spread: 0.20 (canonical)
- Выход: first-touch SL/TP/TIMEOUT по `evaluate_fractal_stop_trade()` (Stage 2)
- Вход только при: `breach_proba < p` (модель уверена — стоп НЕ пробьётся), `fav_pred ≥ min_fav_val`, `fav_pred / stop_val_actual ≥ min_rr`
- Направление: каждая сторона (buy/sell) торгуется изолированно

### 4. Grid search (малый, фиксированный)

| Параметр | Значения |
|----------|----------|
| p | [0.3, 0.4, 0.5] |
| min_fav_val | [0.3, 0.5] |
| min_rr | [1.0, 1.5] |
| tp_fraction | [0.4, 0.6] |

24 комбинации на таргет. Winner: максимальный PF при `trades/year ≥ 30`. Bootstrap PF: 500 итераций, median / p05 / p95.

### 5. Скрипт и данные

- **Скрипт**: `ML/baseline/benchmark_fractal_stop_stage4.py`
- **JSON base_raw_plus_time**: `ML/reports/stage4_trade.json`
- **JSON relative_geometry_clean**: `ML/reports/stage4_trade_geom.json`
- **Stage 4.1 скрипт**: `ML/baseline/benchmark_fractal_stop_stage4_1.py`
- **Stage 4.1 JSON**: `ML/reports/stage4_1.json`
- **Validation**: 2019–2022, 9451 строк, purge 12 баров
- **OHLC**: `DATA/XAUUSD_H1_OHLC.csv` (126 637 баров)
- **Test не открывался**

## Results

### base_raw_plus_time (primary)

| Target | AUC | PF | T/Yr | BS_median | BS_p05 | PF_buy | PF_sell | Best grid |
|--------|-----|-----|------|-----------|--------|--------|---------|-----------|
| **sell_H6_off05** | 0.6741 | **1.106** | 86.0 | 1.105 | **0.923** | — | 1.106 | p=0.4 mf=0.3 rr=1.0 tf=0.4 |
| sell_H6_off02 | 0.6872 | 0.984 | 78.2 | 0.982 | 0.813 | — | 0.984 | p=0.4 mf=0.3 rr=1.5 tf=0.6 |
| sell_H12_off02 | 0.6956 | 0.976 | 308.2 | 0.974 | 0.886 | — | 0.976 | p=0.5 mf=0.3 rr=1.5 tf=0.4 |
| buy_H12_off05 | 0.6644 | 0.936 | 94.2 | 0.935 | 0.795 | 0.936 | — | p=0.5 mf=0.3 rr=1.5 tf=0.6 |
| sell_H12_off05 | 0.6789 | 0.912 | 409.5 | 0.911 | 0.838 | — | 0.912 | p=0.5 mf=0.3 rr=1.0 tf=0.6 |
| buy_H6_off02 | 0.6835 | 0.902 | 99.5 | 0.906 | 0.763 | 0.902 | — | p=0.5 mf=0.3 rr=1.5 tf=0.6 |
| buy_H12_off02 | 0.6828 | 0.849 | 315.2 | 0.848 | 0.772 | 0.849 | — | p=0.5 mf=0.3 rr=1.0 tf=0.6 |
| buy_H6_off05 | 0.6730 | 0.790 | 195.8 | 0.788 | 0.683 | 0.790 | — | p=0.5 mf=0.3 rr=1.0 tf=0.6 |

### relative_geometry_clean (control)

| Target | AUC | PF | T/Yr | BS_median | BS_p05 | PF_buy | PF_sell | Best grid |
|--------|-----|-----|------|-----------|--------|--------|---------|-----------|
| **sell_H6_off05** | 0.6758 | **1.142** | 54.5 | 1.162 | **0.906** | — | 1.142 | p=0.4 mf=0.3 rr=1.0 tf=0.4 |
| buy_H12_off05 | 0.6662 | 1.015 | 85.0 | 1.021 | 0.844 | 1.015 | — | p=0.5 mf=0.3 rr=1.5 tf=0.6 |
| sell_H6_off02 | 0.6911 | 0.998 | 123.2 | 0.999 | 0.844 | — | 0.998 | p=0.5 mf=0.3 rr=1.5 tf=0.6 |
| sell_H12_off02 | 0.6925 | 0.971 | 190.2 | 0.973 | 0.861 | — | 0.971 | p=0.5 mf=0.3 rr=1.5 tf=0.6 |
| sell_H12_off05 | 0.6797 | 0.914 | 301.2 | 0.921 | 0.826 | — | 0.914 | p=0.5 mf=0.3 rr=1.0 tf=0.6 |
| buy_H6_off02 | 0.6824 | 0.877 | 92.5 | 0.871 | 0.729 | 0.877 | — | p=0.5 mf=0.3 rr=1.5 tf=0.6 |
| buy_H12_off02 | 0.6890 | 0.828 | 296.5 | 0.827 | 0.747 | 0.828 | — | p=0.5 mf=0.3 rr=1.0 tf=0.6 |
| buy_H6_off05 | 0.6696 | 0.825 | 188.5 | 0.823 | 0.726 | 0.825 | — | p=0.5 mf=0.3 rr=1.0 tf=0.6 |

### Сравнение профилей

| Метрика | base_raw_plus_time | relative_geometry_clean |
|---------|-------------------|-------------------------|
| Winner target | sell_H6_off05 | sell_H6_off05 |
| Winner PF | 1.106 | 1.142 |
| Winner BS_p05 | 0.923 | 0.906 |
| Таргетов с PF ≥ 1.0 | 1/8 | 2/8 |
| Таргетов с PF ≥ 1.15 | 0/8 | 0/8 |
| Buy targets PF range | 0.79–0.94 | 0.83–1.02 |
| Sell targets PF range | 0.91–1.11 | 0.91–1.14 |
| Разница winner PF | — | +0.036 (шум) |

### Sell H6 off05 — единственный кандидат

Оба профиля выбрали один и тот же таргет с одинаковыми оптимальными параметрами: `p=0.4, min_fav=0.3, min_rr=1.0, tp_fraction=0.4`. Это таргет с самым низким breach_rate среди sell (off05 — более широкий стоп, реже пробивается) и одновременно с самым низким порогом входа (`p=0.4` — входим только когда модель ОЧЕНЬ уверена, что стоп НЕ пробьётся).

### Годовая устойчивость winner (base_raw_plus_time, sell_H6_off05)

| Год | Сделок | PF |
|-----|--------|-----|
| 2019 | 52 | **0.480** |
| 2020 | 145 | 1.279 |
| 2021 | 59 | 1.748 |
| 2022 | 88 | 1.138 |

1/4 лет — катастрофический (PF=0.48 при 52 сделках). 2021 имеет PF=1.748, но всего 59 сделок — шумная оценка. Совокупный PF=1.106 достигается за счёт одного сильного года (2020, 145 сделок). Стабильности нет.

### Stage 4.1 — контрольные эксперименты после аудита

Stage 4.1 проверил две гипотезы из аудита Stage 4:

1. **XGBoost-fav вместо RF-fav**: если слабым звеном был fav-регрессор, более гибкая модель должна была улучшить PF.
2. **Combined breach H6 AND H12**: вход разрешён только если обе breach-модели считают риск пробоя низким. Цель — повысить точность отбора сделок.

Конфигурация Stage 4.1:

| Параметр | Значение |
|----------|----------|
| Feature profile | `base_raw_plus_time` |
| Breach model | XGBoostClassifier |
| Fav model | XGBoostRegressor |
| Spread | 0.20 |
| Grid | p=[0.3,0.4,0.5], min_fav=[0.3,0.5], min_rr=[1.0,1.5], tp_fraction=[0.4,0.6] |
| Permutation test | 500 перестановок breach-вероятностей |
| Test | Не открывался |

#### XGBoost-fav vs Stage 4 RF-fav

| Target | Stage 4 RF-fav PF | Stage 4.1 XGBoost-fav PF | Delta PF | T/Yr | BS_p05 | Negative years |
|--------|------------------:|--------------------------:|---------:|-----:|-------:|---------------:|
| sell_H6_off05 | 1.106 | 0.904 | -0.202 | 74.0 | 0.746 | 3/4 |
| sell_H6_off02 | 0.984 | 0.899 | -0.085 | 182.5 | 0.800 | 3/4 |
| sell_H12_off02 | 0.976 | 0.915 | -0.061 | 37.2 | 0.667 | 2/4 |
| sell_H12_off05 | 0.912 | 0.901 | -0.011 | 120.2 | 0.767 | 4/4 |

XGBoost-fav хуже RF-fav на всех 4 проверенных SELL-таргетах. Гипотеза "простая замена fav-регрессора решит проблему" не подтвердилась. Более точная формулировка: XGBoost-fav не устраняет слабость fav-слоя на текущих признаках; это не доказывает, что fav-цель сама по себе не является шумным узким местом.

#### Combined breach H6 AND H12

| Target | PF | T/Yr | BS_p05 | Perm p-value | Perm median PF | Perm p95 PF | Negative years | Best grid |
|--------|---:|-----:|-------:|-------------:|---------------:|------------:|---------------:|-----------|
| sell_comb_off05 | 1.065 | 88.5 | 0.883 | 0.050 | 0.837 | 1.061 | 1/4 | p=0.4 mf=0.3 rr=1.0 tf=0.4 |
| sell_comb_off02 | 0.875 | 413.5 | 0.807 | 0.160 | 0.833 | 0.903 | 4/4 | p=0.5 mf=0.3 rr=1.0 tf=0.6 |

`sell_comb_off05` формально близок к границе, но не проходит trading gate:

- PF=1.065 ниже Stage 4 winner PF=1.106.
- Bootstrap p05=0.883 включает сильный провал ниже PF=1.0.
- `perm_p=0.050`: в 5% перестановок breach-вероятностей PF был не хуже наблюдаемого. С учётом перебора правил это слабое доказательство, а не подтверждённый edge.
- Permutation p95=1.061 почти равен наблюдаемому PF=1.065, то есть результат находится на верхней границе случайного распределения, но не отделяется от него с запасом.

Годовая устойчивость `sell_comb_off05`:

| Год | Сделок | PF |
|-----|-------:|---:|
| 2019 | 60 | 1.238 |
| 2020 | 144 | 1.121 |
| 2021 | 58 | 1.081 |
| 2022 | 92 | 0.893 |

Годовой профиль лучше, чем у Stage 4 winner, но общий PF ниже, а статистическая значимость всё равно не пройдена.

## Verification

- Test не использовался ни на одном этапе Stage 4.
- Stage 4.1 также использует только validation; test не открывался.
- OHLC загружается один раз, entry_prices вычисляются до grid search.
- Все 8 breach targets проверены для обоих профилей: 192 симуляции сделок (24 grid × 8 targets).
- Stage 4.1 проверил 4 SELL individual targets с XGBoost-fav и 2 combined SELL targets.
- Bootstrap PF: 500 итераций на winner каждого таргета.
- Permutation test Stage 4.1: 500 перестановок breach-вероятностей для combined winner.
- Fav-регрессор оставлен RF (Stage 2) для изоляции вклада breach-классификатора.
- В Stage 4.1 fav-регрессор заменён на XGBoostRegressor как отдельный контрольный эксперимент.
- Торговый симулятор воспроизводит логику Stage 2: first-touch SL/TP/TIMEOUT, ambiguous bar = SL, spread 0.20.
- Purge 12 баров на хвосте валидации.

## Методологические примечания

1. **PF proxy из Stage 3.2 не заменил торговый PF.** Stage 3.2 показывал PF=10–30 для всех таргетов — это был диагностический PF, использующий `fav_val` как perfect exit knowledge. Реальный торговый PF в 20–30 раз ниже.
2. **AUC не предсказывает PF на уровне отдельных таргетов.** `sell_H12_off02` имеет лучший AUC (0.696) но PF=0.976. `sell_H6_off05` имеет AUC=0.674 но PF=1.106. Асимметрия breach_rate и распределения fav_val создаёт нелинейность между качеством ранжирования и торговым результатом.
3. **Buy-сторона структурно невыгодна для этой механики.** XAUUSD находится в долгосрочном восходящем тренде (2004–2022). Buy-фракталы (поддержки) реже ломаются с профитом — цена чаще отскакивает от поддержки и идёт вверх без пробоя стопа. Sell-фракталы (сопротивления) в аптренде пробиваются чаще, но когда НЕ пробиваются — дают более сильное движение. Это объясняет асимметрию PF: sell 0.91–1.11 vs buy 0.79–0.94.
4. **Замена RF-fav на XGBoost-fav не решила проблему.** RF fav имеет MSE 1.6–3.8 ATR², что означает ошибку предсказания 1.3–1.9 ATR при типичном стопе 0.2–0.5 ATR. Stage 4.1 показал, что более гибкий XGBoostRegressor ухудшает PF на всех проверенных SELL-таргетах. Это снимает гипотезу "достаточно заменить fav-модель", но не доказывает, что fav-цель не шумная.
5. **Time-фичи несут риск календарного фильтра.** +205 bp AUC от 4 time-признаков — крупнейший единичный вклад. Но это может означать торговлю по сессиям (London open, Asian), а не по фрактальной структуре. Такие паттерны неустойчивы при смене провайдера или ликвидности. Нужна проверка per-year stability time-важности и permutation-тест.
6. **Winner не проходит тест на статистическую значимость.** BS_p05=0.923 означает: 5% бутстрап-выборок дают PF≤0.92. Доверительный интервал (0.92–1.36) включает 1.0. С учётом 192 протестированных конфигураций (24 grid × 8 таргетов) без коррекции на множественное тестирование, 1–2 таргета с PF≥1.0 — это уровень случайного шума. Stage 4.1 permutation test подтвердил этот риск: лучший combined-кандидат имеет `perm_p=0.050`, то есть не отделяется от случайной перестановки с достаточным запасом.
7. **Годовая устойчивость отсутствует.** 2019: PF=0.48 (52 сделки) — катастрофический убыток. Совокупный PF=1.106 держится на одном сильном годе (2020, 145 сделок, PF=1.279).

## Conclusions

1. **Улучшение breach-классификатора с RF (AUC 0.645) до XGBoost (AUC 0.680) не конвертируется в статистически значимый торговый PF.** Рост AUC на +345 bp дал лишь маргинальное улучшение PF (с ~0.975 Stage 2 до ~1.106 Stage 4 на лучшем таргете). 7/8 таргетов по-прежнему убыточны, а gate PF > 1.15 не прошёл ни один таргет.

2. **PF статистически неотличим от 1.0.** Winner `sell_H6_off05` имеет BS_p05=0.923 — более 5% вероятности получить PF < 1.0 при повторной выборке. Ни один таргет не проходит gate PF > 1.15.

3. **`base_raw_plus_time` и `relative_geometry_clean` эквивалентны для торговли.** Разница winner PF 1.106 vs 1.142 — шум. Для практического использования `base_raw_plus_time` предпочтительнее как более простой.

4. **Проблема не решается локальной заменой fav-регрессора или пересечением H6/H12.** Stage 4.1 ухудшил PF при XGBoost-fav и не улучшил Stage 4 winner через combined breach. Значит, следующий шаг не должен быть ещё одним малым перебором порогов внутри той же постановки.

5. **Текущий табличный кандидат закрыт как торговый.** Oracle (PF=∞) показал, что механика имеет диагностический потолок при идеальном знании будущего, но RF/XGBoost на плоских фрактальных признаках этот потолок не приближают. Дальше нужен новый исследовательский цикл: sequence-представление (Transformer) или пересмотр самой торговой постановки/таргета.

## Итоговые цифры Stage 4

| Метрика | base_raw_plus_time | relative_geometry_clean |
|---------|-------------------|-------------------------|
| Winner target | sell_H6_off05 | sell_H6_off05 |
| Winner AUC | 0.6741 | 0.6758 |
| Winner PF | 1.106 | 1.142 |
| Winner BS_p05 | 0.923 | 0.906 |
| Winner trades/year | 86.0 | 54.5 |
| Таргетов PF ≥ 1.0 | 1/8 | 2/8 |
| Таргетов PF ≥ 1.15 | 0/8 | 0/8 |
| Mean PF (all targets) | 0.932 | 0.946 |
| Buy mean PF | 0.869 | 0.886 |
| Sell mean PF | 0.995 | 1.006 |

## Next Step

Stage 4.1 закрыл быстрые контрольные эксперименты из аудита:

- XGBoost-fav — rejected: PF хуже RF-fav на всех 4 SELL-таргетах.
- Combined breach H6 AND H12 — rejected: PF=1.065, `perm_p=0.050`, хуже Stage 4 winner.

Test не открывать: validation gate не пройден.

Следующий разумный путь — новый исследовательский цикл, а не донастройка Stage 4:

### A. Transformer encoder на фрактальной sequence
Фракталы — естественная последовательность (100 уровней × 10 каналов или расширенный 23-полевой формат). Transformer может выжать сигнал из отношений между фракталами (ближний/дальний, плотность, кластеризация), который табличные модели не видят. Риски:
- CHANGELOG (2026-05-21): Transformer на fractal features не дал direction-сигнала (но breach — бинарная задача, может сработать иначе)
- AUC 0.70–0.72 может не закрыть gap до PF > 1.15
- Долгая разработка (5–7 дней)

### B. Пересмотр торговой постановки
Если Transformer не даёт явного прироста, текущую схему `breach -> fav -> fixed TP/SL` нужно закрывать и формулировать новый таргет: прямой `trade_positive_flag`, `expected_pnl_val`, порядок касания TP/SL или trailing/partial exit.

## Changed Files

- `ML/baseline/benchmark_fractal_stop_stage4.py` — Stage 4 trade simulation + XGBoost (NEW)
- `ML/reports/stage4_trade.json` — base_raw_plus_time results (NEW)
- `ML/reports/stage4_trade_geom.json` — relative_geometry_clean results (NEW)
- `ML/baseline/benchmark_fractal_stop_stage4_1.py` — Stage 4.1 XGBoost-fav + combined breach + permutation test (NEW)
- `ML/reports/stage4_1.json` — Stage 4.1 results (NEW)

## Related Materials

- `docs/reports/2026-06-10-feature-profiles-stage3.md` — Stage 3.x feature profiles + XGBoost classification
- `docs/reports/2026-06-10-fractal-stop-fav-stage2.md` — Stage 2 RF trading (PF < 1.0, oracle PF=∞)
- `docs/reports/2026-06-10-fractal-stop-breach-stage1.md` — Stage 1 breach baseline (RF, AUC 0.62–0.68)
- `ML/baseline/benchmark_fractal_stop_stage4.py` — скрипт Stage 4
- `ML/baseline/benchmark_fractal_stop_stage4_1.py` — скрипт Stage 4.1
- `ML/baseline/benchmark_fractal_stop_stage3_2.py` — Stage 3.2 XGBoost classification
- `ML/baseline/benchmark_fractal_stop_stage3_1.py` — Stage 3.1 RF ablation
- `ML/baseline/benchmark_fractal_stop_fav.py` — Stage 2 RF trade simulation
- `processing/label_signals.py` — `evaluate_fractal_stop_trade()`, `load_ohlc_index()`
