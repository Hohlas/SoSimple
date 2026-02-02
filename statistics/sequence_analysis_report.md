# Sequence Analysis Summary

**Дата создания:** 2026-02-02 19:18:37

## Data Quality

- **Successfully parsed:** 10136 строк (100.00%)
- **Missing values:** Не обнаружены
- **Causal consistency:** ✅ PASSED
  - Нарушения порядка: 0 строк


## Key Findings

### Топ-10 наиболее дискриминативных позиций фракталов:


**Класс -1:**
- Позиция 0: средний |Cohen's d| = 0.778
- Позиция 1: средний |Cohen's d| = 0.366
- Позиция 3: средний |Cohen's d| = 0.279
- Позиция 2: средний |Cohen's d| = 0.254
- Позиция 17: средний |Cohen's d| = 0.203
- Позиция 12: средний |Cohen's d| = 0.176
- Позиция 21: средний |Cohen's d| = 0.166
- Позиция 16: средний |Cohen's d| = 0.150
- Позиция 9: средний |Cohen's d| = 0.144
- Позиция 50: средний |Cohen's d| = 0.144

**Класс 1:**
- Позиция 0: средний |Cohen's d| = 0.793
- Позиция 1: средний |Cohen's d| = 0.291
- Позиция 39: средний |Cohen's d| = 0.166
- Позиция 2: средний |Cohen's d| = 0.154
- Позиция 3: средний |Cohen's d| = 0.131
- Позиция 5: средний |Cohen's d| = 0.121
- Позиция 60: средний |Cohen's d| = 0.120
- Позиция 35: средний |Cohen's d| = 0.119
- Позиция 52: средний |Cohen's d| = 0.115
- Позиция 11: средний |Cohen's d| = 0.113


### Топ-20 engineered features по важности:

205. **price_percentile_w20** (correlation=0.176, MI=0.035)
204. **price_zscore_w20** (correlation=0.218, MI=0.029)
200. **price_zscore_w10** (correlation=0.216, MI=0.029)
201. **price_percentile_w10** (correlation=0.180, MI=0.030)
8. **front_max_w1** (correlation=0.040, MI=0.032)
5. **front_mean_w1** (correlation=0.040, MI=0.031)
7. **front_min_w1** (correlation=0.040, MI=0.031)
224. **front_back_interaction** (correlation=0.040, MI=0.027)
169. **price_slope_2** (correlation=-0.199, MI=0.020)
172. **price_slope_3** (correlation=-0.179, MI=0.020)
175. **price_slope_4** (correlation=-0.178, MI=0.020)
227. **impulse_direction_interaction** (correlation=0.218, MI=0.016)
32. **front_max_w2** (correlation=0.024, MI=0.022)
213. **price_momentum_5** (correlation=0.172, MI=0.017)
217. **price_momentum_10** (correlation=0.159, MI=0.015)
29. **front_mean_w2** (correlation=0.035, MI=0.019)
56. **front_max_w3** (correlation=0.021, MI=0.019)
178. **price_slope_5** (correlation=-0.154, MI=0.013)
221. **price_momentum_20** (correlation=0.141, MI=0.013)
53. **front_mean_w3** (correlation=0.027, MI=0.015)


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
- `price_percentile_w20` (importance=0.5882)
- `price_zscore_w20` (importance=0.5218)
- `price_zscore_w10` (importance=0.5176)
- `price_percentile_w10` (importance=0.5108)
- `front_max_w1` (importance=0.4695)
- `front_mean_w1` (importance=0.4630)
- `front_min_w1` (importance=0.4624)
- `front_back_interaction` (importance=0.4032)
- `price_slope_2` (importance=0.3859)
- `price_slope_3` (importance=0.3757)


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
- Redundant features (correlation > 0.95): 15
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
