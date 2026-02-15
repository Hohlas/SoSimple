# Sequence Analysis Summary

**Дата создания:** 2026-02-15 17:45:54

## Data Quality

- **Successfully parsed:** 0 строк (0.00%)
- **Missing values:** Обнаружены
- **Causal consistency:** ⚠️ ISSUES DETECTED
  - Нарушения порядка: 26152 строк


## Key Findings

### Топ-10 наиболее дискриминативных позиций фракталов:



### Топ-20 engineered features по важности:

200. **price_zscore_w10** (correlation=0.306, MI=0.069)
172. **price_slope_3** (correlation=-0.284, MI=0.061)
201. **price_percentile_w10** (correlation=0.272, MI=0.059)
204. **price_zscore_w20** (correlation=0.300, MI=0.057)
175. **price_slope_4** (correlation=-0.276, MI=0.058)
178. **price_slope_5** (correlation=-0.267, MI=0.055)
213. **price_momentum_5** (correlation=0.265, MI=0.054)
205. **price_percentile_w20** (correlation=0.254, MI=0.053)
169. **price_slope_2** (correlation=-0.250, MI=0.052)
8. **front_max_w1** (correlation=0.026, MI=0.066)
7. **front_min_w1** (correlation=0.026, MI=0.066)
5. **front_mean_w1** (correlation=0.026, MI=0.066)
224. **front_back_interaction** (correlation=0.021, MI=0.061)
217. **price_momentum_10** (correlation=0.228, MI=0.039)
181. **price_slope_10** (correlation=-0.222, MI=0.037)
32. **front_max_w2** (correlation=0.016, MI=0.043)
187. **majority_direction_match_w3** (correlation=-0.191, MI=0.030)
29. **front_mean_w2** (correlation=0.028, MI=0.041)
193. **peak_valley_ratio_w10** (correlation=-0.153, MI=0.027)
192. **direction_changes_w10** (correlation=-0.021, MI=0.036)


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
- `price_zscore_w10` (importance=0.6529)
- `price_slope_3` (importance=0.5800)
- `price_percentile_w10` (importance=0.5638)
- `price_zscore_w20` (importance=0.5603)
- `price_slope_4` (importance=0.5562)
- `price_slope_5` (importance=0.5296)
- `price_momentum_5` (importance=0.5212)
- `price_percentile_w20` (importance=0.5115)
- `price_slope_2` (importance=0.5013)
- `front_max_w1` (importance=0.4889)


### 3. Temporal features

Рекомендуется добавить:
- `hour_sin`, `hour_cos` (из времени)
- `day_of_week_sin`, `day_of_week_cos` (из времени)

### 4. Data Leakage Check

**Status:** ❌ ISSUES DETECTED

**Details:**

- Требуется дополнительный анализ: возможно, это особенность структуры данных
- Рекомендуется проверить логику формирования фракталов

### 5. Feature Selection

- Всего создано: 233 признаков
- Redundant features (correlation > 0.95): 7
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
