# Sequence Analysis Summary

**Дата создания:** 2026-01-26 10:43:09

## Data Quality

- **Successfully parsed:** 5042 строк (100.00%)
- **Missing values:** Не обнаружены
- **Causal consistency:** ⚠️ ISSUES DETECTED
  - Нарушения порядка: 5042 строк
  - Систематические нарушения на позициях: [11, 22, 33, 44, 55] (требует дополнительного анализа)

## Key Findings

### Топ-10 наиболее дискриминативных позиций фракталов:


**Класс -1:**
- Позиция 0: средний |Cohen's d| = 0.380
- Позиция 1: средний |Cohen's d| = 0.261
- Позиция 12: средний |Cohen's d| = 0.141
- Позиция 34: средний |Cohen's d| = 0.099
- Позиция 45: средний |Cohen's d| = 0.091
- Позиция 2: средний |Cohen's d| = 0.085
- Позиция 23: средний |Cohen's d| = 0.082
- Позиция 20: средний |Cohen's d| = 0.079
- Позиция 40: средний |Cohen's d| = 0.076
- Позиция 56: средний |Cohen's d| = 0.074

**Класс 1:**
- Позиция 0: средний |Cohen's d| = 0.406
- Позиция 1: средний |Cohen's d| = 0.278
- Позиция 12: средний |Cohen's d| = 0.137
- Позиция 23: средний |Cohen's d| = 0.099
- Позиция 98: средний |Cohen's d| = 0.098
- Позиция 9: средний |Cohen's d| = 0.096
- Позиция 16: средний |Cohen's d| = 0.092
- Позиция 67: средний |Cohen's d| = 0.088
- Позиция 34: средний |Cohen's d| = 0.088
- Позиция 27: средний |Cohen's d| = 0.087


### Топ-20 engineered features по важности:

169. **price_slope_2** (correlation=-0.347, MI=0.085)
5. **front_mean_w1** (correlation=0.044, MI=0.067)
7. **front_min_w1** (correlation=0.044, MI=0.066)
8. **front_max_w1** (correlation=0.044, MI=0.066)
201. **price_percentile_w10** (correlation=0.201, MI=0.041)
200. **price_zscore_w10** (correlation=0.224, MI=0.034)
227. **impulse_direction_interaction** (correlation=0.231, MI=0.028)
17. **impulse_mean_w1** (correlation=-0.056, MI=0.041)
20. **impulse_max_w1** (correlation=-0.056, MI=0.040)
205. **price_percentile_w20** (correlation=0.176, MI=0.028)
19. **impulse_min_w1** (correlation=-0.056, MI=0.038)
226. **count_reverse_interaction** (correlation=-0.028, MI=0.039)
44. **impulse_max_w2** (correlation=-0.051, MI=0.035)
204. **price_zscore_w20** (correlation=0.190, MI=0.022)
172. **price_slope_3** (correlation=-0.168, MI=0.021)
65. **impulse_mean_w3** (correlation=-0.062, MI=0.030)
68. **impulse_max_w3** (correlation=-0.054, MI=0.030)
41. **impulse_mean_w2** (correlation=-0.062, MI=0.025)
213. **price_momentum_5** (correlation=0.151, MI=0.016)
43. **impulse_min_w2** (correlation=-0.067, MI=0.020)


## Recommendations for Modeling

### 1. Архитектура модели

- **Вариант A:** Использовать full sequence (99 фракталов) с LSTM/Transformer
  - Преимущества: сохранение временной структуры
  - Недостатки: требует больше вычислительных ресурсов

- **Вариант B:** Feature-based модель с engineered features (233 признаков)
  - Преимущества: быстрее обучение, интерпретируемость
  - Недостатки: потеря части временной информации

### 2. Критичные признаки

Топ-10 признаков для включения в модель:
- `price_slope_2` (importance=0.6735)
- `front_mean_w1` (importance=0.4143)
- `front_min_w1` (importance=0.4087)
- `front_max_w1` (importance=0.4068)
- `price_percentile_w10` (importance=0.3392)
- `price_zscore_w10` (importance=0.3081)
- `impulse_direction_interaction` (importance=0.2793)
- `impulse_mean_w1` (importance=0.2690)
- `impulse_max_w1` (importance=0.2630)
- `price_percentile_w20` (importance=0.2531)


### 3. Temporal features

Рекомендуется добавить:
- `hour_sin`, `hour_cos` (из времени)
- `day_of_week_sin`, `day_of_week_cos` (из времени)

### 4. Data Leakage Check

**Status:** ❌ ISSUES DETECTED

**Details:**
- Нарушения упорядоченности по времени обнаружены на позициях [11, 22, 33, 44, 55]
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
1. Провести дополнительный анализ нарушений на позициях [11, 22, 33, 44, 55]
2. Выбрать архитектуру модели (LSTM/Transformer vs Feature-based)
3. Подготовить train/test split с учётом временной структуры
4. Применить техники балансировки классов (SMOTE, class weights)
5. Обучить модель и оценить на тестовой выборке
