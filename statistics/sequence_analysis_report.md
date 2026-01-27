# Sequence Analysis Summary

**Дата создания:** 2026-01-27 00:17:44

## Data Quality

- **Successfully parsed:** 5042 строк (100.00%)
- **Missing values:** Не обнаружены
- **Causal consistency:** ✅ PASSED
  - Нарушения порядка: 0 строк
  - Систематические нарушения на позициях: [11, 22, 33, 44, 55] (требует дополнительного анализа)

## Key Findings

### Топ-10 наиболее дискриминативных позиций фракталов:


**Класс -1:**
- Позиция 0: средний |Cohen's d| = 0.380
- Позиция 1: средний |Cohen's d| = 0.261
- Позиция 2: средний |Cohen's d| = 0.141
- Позиция 4: средний |Cohen's d| = 0.099
- Позиция 5: средний |Cohen's d| = 0.091
- Позиция 10: средний |Cohen's d| = 0.085
- Позиция 3: средний |Cohen's d| = 0.082
- Позиция 27: средний |Cohen's d| = 0.079
- Позиция 45: средний |Cohen's d| = 0.076
- Позиция 6: средний |Cohen's d| = 0.074

**Класс 1:**
- Позиция 0: средний |Cohen's d| = 0.406
- Позиция 1: средний |Cohen's d| = 0.278
- Позиция 2: средний |Cohen's d| = 0.137
- Позиция 3: средний |Cohen's d| = 0.099
- Позиция 98: средний |Cohen's d| = 0.098
- Позиция 17: средний |Cohen's d| = 0.096
- Позиция 23: средний |Cohen's d| = 0.092
- Позиция 7: средний |Cohen's d| = 0.088
- Позиция 4: средний |Cohen's d| = 0.088
- Позиция 33: средний |Cohen's d| = 0.087


### Топ-20 engineered features по важности:

169. **price_slope_2** (correlation=-0.347, MI=0.085)
200. **price_zscore_w10** (correlation=0.357, MI=0.081)
201. **price_percentile_w10** (correlation=0.336, MI=0.079)
8. **front_max_w1** (correlation=0.044, MI=0.067)
172. **price_slope_3** (correlation=-0.255, MI=0.049)
7. **front_min_w1** (correlation=0.044, MI=0.066)
5. **front_mean_w1** (correlation=0.044, MI=0.065)
205. **price_percentile_w20** (correlation=0.258, MI=0.046)
204. **price_zscore_w20** (correlation=0.265, MI=0.043)
213. **price_momentum_5** (correlation=0.228, MI=0.044)
175. **price_slope_4** (correlation=-0.218, MI=0.040)
227. **impulse_direction_interaction** (correlation=0.252, MI=0.035)
20. **impulse_max_w1** (correlation=-0.056, MI=0.044)
224. **front_back_interaction** (correlation=0.022, MI=0.045)
19. **impulse_min_w1** (correlation=-0.056, MI=0.042)
17. **impulse_mean_w1** (correlation=-0.056, MI=0.040)
178. **price_slope_5** (correlation=-0.177, MI=0.029)
44. **impulse_max_w2** (correlation=-0.051, MI=0.035)
180. **impulse_slope_5** (correlation=0.047, MI=0.032)
41. **impulse_mean_w2** (correlation=-0.062, MI=0.030)


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
- `price_zscore_w10` (importance=0.6516)
- `price_percentile_w10` (importance=0.6284)
- `front_max_w1` (importance=0.4125)
- `price_slope_3` (importance=0.4125)
- `front_min_w1` (importance=0.4087)
- `front_mean_w1` (importance=0.4047)
- `price_percentile_w20` (importance=0.3997)
- `price_zscore_w20` (importance=0.3870)
- `price_momentum_5` (importance=0.3738)


### 3. Temporal features

Рекомендуется добавить:
- `hour_sin`, `hour_cos` (из времени)
- `day_of_week_sin`, `day_of_week_cos` (из времени)

### 4. Data Leakage Check

**Status:** ✅ PASSED

**Details:**
- Нарушения упорядоченности по времени обнаружены на позициях [11, 22, 33, 44, 55]
- Требуется дополнительный анализ: возможно, это особенность структуры данных
- Рекомендуется проверить логику формирования фракталов

### 5. Feature Selection

- Всего создано: 233 признаков
- Redundant features (correlation > 0.95): 13
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
