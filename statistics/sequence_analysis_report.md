# Sequence Analysis Summary

**Дата создания:** 2026-02-02 14:32:40

## Data Quality

- **Successfully parsed:** 5082 строк (100.00%)
- **Missing values:** Не обнаружены
- **Causal consistency:** ✅ PASSED
  - Нарушения порядка: 0 строк


## Key Findings

### Топ-10 наиболее дискриминативных позиций фракталов:


**Класс -1:**
- Позиция 0: средний |Cohen's d| = 0.573
- Позиция 1: средний |Cohen's d| = 0.451
- Позиция 53: средний |Cohen's d| = 0.345
- Позиция 41: средний |Cohen's d| = 0.319
- Позиция 70: средний |Cohen's d| = 0.296
- Позиция 63: средний |Cohen's d| = 0.280
- Позиция 3: средний |Cohen's d| = 0.273
- Позиция 22: средний |Cohen's d| = 0.269
- Позиция 10: средний |Cohen's d| = 0.267
- Позиция 71: средний |Cohen's d| = 0.255

**Класс 1:**
- Позиция 0: средний |Cohen's d| = 0.456
- Позиция 34: средний |Cohen's d| = 0.405
- Позиция 2: средний |Cohen's d| = 0.387
- Позиция 55: средний |Cohen's d| = 0.385
- Позиция 1: средний |Cohen's d| = 0.297
- Позиция 50: средний |Cohen's d| = 0.293
- Позиция 21: средний |Cohen's d| = 0.292
- Позиция 60: средний |Cohen's d| = 0.283
- Позиция 4: средний |Cohen's d| = 0.278
- Позиция 29: средний |Cohen's d| = 0.272


### Топ-20 engineered features по важности:

204. **price_zscore_w20** (correlation=0.135, MI=0.012)
205. **price_percentile_w20** (correlation=0.112, MI=0.012)
201. **price_percentile_w10** (correlation=0.115, MI=0.012)
8. **front_max_w1** (correlation=0.034, MI=0.013)
7. **front_min_w1** (correlation=0.034, MI=0.013)
5. **front_mean_w1** (correlation=0.034, MI=0.013)
200. **price_zscore_w10** (correlation=0.131, MI=0.011)
172. **price_slope_3** (correlation=-0.126, MI=0.008)
175. **price_slope_4** (correlation=-0.113, MI=0.007)
32. **front_max_w2** (correlation=0.029, MI=0.008)
56. **front_max_w3** (correlation=0.029, MI=0.008)
169. **price_slope_2** (correlation=-0.135, MI=0.006)
36. **back_max_w2** (correlation=-0.062, MI=0.007)
84. **back_max_w4** (correlation=-0.062, MI=0.006)
30. **front_std_w2** (correlation=0.034, MI=0.007)
221. **price_momentum_20** (correlation=0.090, MI=0.006)
53. **front_mean_w3** (correlation=0.036, MI=0.006)
78. **front_std_w4** (correlation=0.030, MI=0.006)
80. **front_max_w4** (correlation=0.027, MI=0.006)
54. **front_std_w3** (correlation=0.032, MI=0.006)


## Recommendations for Modeling

### 1. Архитектура модели

- **Вариант A:** Использовать full sequence (100 фракталов) с LSTM/Transformer
  - Преимущества: сохранение временной структуры
  - Недостатки: требует больше вычислительных ресурсов

- **Вариант B:** Feature-based модель с engineered features (233 признаков)
  - Преимущества: быстрее обучение, интерпретируемость
  - Недостатки: потеря части временной информации

### 2. Критичные признаки

Топ-10 признаков для включения в модель:
- `price_zscore_w20` (importance=0.5528)
- `price_percentile_w20` (importance=0.5369)
- `price_percentile_w10` (importance=0.5193)
- `front_max_w1` (importance=0.5170)
- `front_min_w1` (importance=0.5170)
- `front_mean_w1` (importance=0.5170)
- `price_zscore_w10` (importance=0.4973)
- `price_slope_3` (importance=0.3923)
- `price_slope_4` (importance=0.3436)
- `front_max_w2` (importance=0.3424)


### 3. Temporal features

Рекомендуется добавить:
- `hour_sin`, `hour_cos` (из времени)
- `day_of_week_sin`, `day_of_week_cos` (из времени)

### 4. Data Leakage Check

**Status:** ✅ PASSED

**Details:**

- Требуется дополнительный анализ: возможно, это особенность структуры данных
- Рекомендуется проверить логику формирования фракталов

### 5. Feature Selection

- Всего создано: 233 признаков
- Redundant features (correlation > 0.95): 16
- Рекомендуется удалить избыточные признаки перед обучением

## Файлы результатов

- `nero_features_engineered.csv` - датасет с engineered features
- `feature_catalog.json` - метаданные признаков
- `feature_importance_sequence.csv` - ranking признаков
- `sequence_heatmaps_by_class.png` - heatmaps по классам
- `sample_sequences_minority_classes.png` - примеры последовательностей
- `differential_patterns.png` - дифференциальные паттерны
- `engineered_features_boxplots.png` - boxplots признаков

---

**Следующие шаги:**
2. Выбрать архитектуру модели (LSTM/Transformer vs Feature-based)
3. Подготовить train/test split с учётом временной структуры
4. Применить техники балансировки классов (SMOTE, class weights)
5. Обучить модель и оценить на тестовой выборке
