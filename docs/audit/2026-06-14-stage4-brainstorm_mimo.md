# Stage 4 Diagnostic Brainstorm: Oracle vs Stage 4 Gap Analysis

> **Date**: 2026-06-14
> **Status**: Planning
> **Goal**: Диагностический анализ разрыва между Oracle (PF=∞) и Stage 4 (PF=1.015)
> **Author**: MiMo Code Agent

---

## Контекст

Oracle показывает PF=∞ при идеальном знании breach/fav, а Stage 4.2 — PF=1.015. Нужно понять: **что конкретно не работает — breach-классификатор или fav-регрессия?**

---

## Ключевые данные из отчётов

### Oracle ($val$, canonical spread=0.20)

| Режим | sell_H6_off02 | sell_H6_off05 | sell_H12_off02 | sell_H12_off05 |
|-------|---------------|---------------|----------------|----------------|
| **perfect_breach** (true breach, RF fav) | PF=12.78 | PF=8.02 | PF=22.01 | PF=13.94 |
| **perfect_fav** (RF breach, true fav) | PF=7.02 | PF=9.39 | PF=23.55 | PF=12.16 |
| **perfect_both** (both true) | PF=∞ | PF=∞ | PF=∞ | PF=∞ |

### Stage 4 (val, winner sell_H6_off05)

| Компонент | Метрика | Значение |
|-----------|---------|----------|
| Breach classifier | AUC | 0.6741 |
| Fav regressor (RF) | MSE | ~1.8 (H6), ~3.8 (H12) |
| Trading (grid search) | PF | 1.106 |
| Stage 4.2 corrected | PF | 1.015 |

### Stage 2 Fav Regression质量问题

| Комбинация | MSE fav | MAE fav | RMSE fav |
|-----------|---------|---------|----------|
| sell_H6_off02 | 1.825 | 0.935 | 1.351 |
| sell_H6_off05 | 1.825 | 0.935 | 1.351 |
| sell_H12_off02 | 3.776 | 1.420 | 1.943 |
| sell_H12_off05 | 3.776 | 1.420 | 1.943 |

---

## Анализ: что хуже — breach или fav?

### 1. Breach — главный bottleneck

**Аргументы:**
- `perfect_breach` даёт PF=8–28 при ожидаемом fav-предсказании (RF)
- `perfect_fav` даёт PF=7–24 при ожидаемом breach-предсказании (RF)
- Оба дают巨大PF, но perfect_breach стабильно выше для H6 комбинаций

**Числа для sell_H6_off05 (наиболее исследованная комбинация):**
- Oracle perfect_breach: PF=8.02 (1561 сделок, canonical)
- Oracle perfect_fav: PF=9.39 (1726 сделок, canonical)
- Stage 4 RF: PF=1.106 (344 сделки)

**Gap analysis:**
- breach-only gap: 1.106 / 8.02 = **0.14x** (RF использует только 14% потенциала perfect breach)
- fav-only gap: 1.106 / 9.39 = **0.12x** (RF использует только 12% потенциала perfect fav)
- **Оба компонента теряют ~85-88% сигнала**

### 2. Fav regression слабая, но не критичная

- MSE=1.825 при H6 fav_val意味着 типичная ошибка ~1.35 ATR
- Средний fav_val ~1.0–1.5 ATR → ошибка = типичное значение
- **Но**: даже с такой ошибкой oracle показывает PF=9.39 — значит, fav-фильтр работает, когда breach точный

### 3. Breach AUC=0.674 — недостаточно

- AUC 0.674 → при p=0.4 breach rate ~40% → много false positives и false negatives
- Oracle perfect_breach означает 0% ошибок breach-классификации
- **Gap 0.674 vs 1.0 (oracle)** = основная потеря сигнала

---

## Варианты диагностики причин провала

### Вариант A: Изоляция breach vs fav

**Цель**: измерить вклад каждого компонента отдельно

**Метод**:
1. **Breach-only diagnostic**: perfect_breach + RF fav → PF
2. **Fav-only diagnostic**: RF breach + perfect_fav → PF
3. **Sensitivity analysis**: как PF меняется при varies breach AUC (0.60, 0.65, 0.70, 0.75, 0.80)

**Реализация**: `ML/baseline/diagnose_breach_vs_fav.py`

### Вариант B: Анализ feature importance для breach

**Цель**: понять, какие признаки несут breach-сигнал

**Метод**:
1. Feature importance из XGBoost breach classifier (Stage 3.2 winner)
2. Ablation: удаление групп признаков → изменение AUC
3. Correlation analysis: какие фрактальные каналы коррелируют с breach

**Реализация**: `ML/baseline/feature_ablation_breach.py`

### Вариант C: Threshold sensitivity для breach

**Цель**: проверить, как точность breach-фильтра влияет на PF

**Метод**:
1. Breach probability threshold sweep (0.3, 0.4, 0.5, 0.6, 0.7)
2. При каждом пороге: precision, recall, trades/yr, PF
3. Построить кривую PF от breach precision

**Реализация**: `ML/baseline/breach_threshold_sensitivity.py`

### Вариант D: Fav prediction error analysis

**Цель**: понять, почему fav regression ошибается

**Метод**:
1. Scatter: predicted fav vs true fav
2. Error distribution: когда модель ошибается больше?
3. Feature importance для fav regressor

**Реализация**: `ML/baseline/fav_error_analysis.py`

---

## Рекомендуемый план действий

### Этап 1: Quick diagnostic (Вариант A)
- Запустить изоляцию breach vs fav
- Определить, какой компонент теряет больше сигнала
- **Время**: 1-2 часа

### Этап 2: Feature analysis (Вариант B)
- Понять, какие признаки важны для breach
- Определить, что не хватает текущему RF
- **Время**: 2-3 часа

### Этап 3: Sensitivity analysis (Вариант C)
- Построить кривую PF от breach precision
- Определить целевой AUC для положительного PF
- **Время**: 1-2 часа

### Этап 4: Fav error analysis (Вариант D)
- Понять природу fav-ошибок
- Определить, можно ли улучшить fav regressor
- **Время**: 1-2 часа

---

## Ожидаемые результаты

1. **Количественная оценка**: какой компонент (breach/fav) теряет больше сигнала
2. **Целевой AUC**: какой breach AUC нужен для PF > 1.5
3. **Feature priorities**: какие признаки добавить для улучшения breach
4. **Fav improvement potential**: можно ли улучшить fav regression

---

## Критерии успеха

1. Разложены вклады breach и fav в итоговый PF
2. Определены приоритеты для улучшения
3. Есть план следующих шагов (Stage 5.0 с фокусом на breach)

---

## Файлы для создания

```
ML/baseline/diagnose_breach_vs_fav.py      # Вариант A
ML/baseline/feature_ablation_breach.py     # Вариант B
ML/baseline/breach_threshold_sensitivity.py # Вариант C
ML/baseline/fav_error_analysis.py          # Вариант D
```

## Верификация

```bash
# Этап 1
python -m ML.baseline.diagnose_breach_vs_fav

# Этап 2
python -m ML.baseline.feature_ablation_breach

# Этап 3
python -m ML.baseline.breach_threshold_sensitivity

# Этап 4
python -m ML.baseline.fav_error_analysis
```

---

## Связанные материалы

- `ML/reports/oracle_fractal_stop_fav.json` — oracle-результаты
- `ML/reports/stage4_trade.json` — Stage 4 результаты
- `ML/reports/stage4_2_diagnostic.json` — Stage 4.2 corrected
- `ML/baseline/oracle_fractal_stop_fav.py` — oracle-скрипт
- `ML/baseline/benchmark_fractal_stop_fav.py` — RF baseline
- `ML/baseline/benchmark_fractal_stop_stage4.py` — Stage 4 скрипт
- `docs/reports/2026-06-10-fractal-stop-fav-stage2.md` — Stage 2 отчёт
- `docs/reports/2026-06-11-stage4-trade-xgboost.md` — Stage 4 отчёт
