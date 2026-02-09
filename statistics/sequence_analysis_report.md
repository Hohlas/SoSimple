# Sequence Analysis Summary

**Дата создания:** 2026-02-09 18:57:56

## Data Quality

- **Successfully parsed:** 0 строк (0.00%)
- **Missing values:** Обнаружены
- **Causal consistency:** ⚠️ ISSUES DETECTED
  - Нарушения порядка: 2030 строк


## Key Findings

### Топ-10 наиболее дискриминативных позиций фракталов:



### Топ-20 engineered features по важности:

169. **price_slope_2** (correlation=-0.431, MI=0.204)
172. **price_slope_3** (correlation=-0.405, MI=0.164)
175. **price_slope_4** (correlation=-0.403, MI=0.151)
200. **price_zscore_w10** (correlation=0.437, MI=0.140)
213. **price_momentum_5** (correlation=0.363, MI=0.123)
178. **price_slope_5** (correlation=-0.365, MI=0.117)
5. **front_mean_w1** (correlation=0.178, MI=0.148)
8. **front_max_w1** (correlation=0.178, MI=0.146)
7. **front_min_w1** (correlation=0.178, MI=0.146)
201. **price_percentile_w10** (correlation=0.360, MI=0.095)
187. **majority_direction_match_w3** (correlation=-0.363, MI=0.077)
204. **price_zscore_w20** (correlation=0.355, MI=0.069)
224. **front_back_interaction** (correlation=0.121, MI=0.104)
205. **price_percentile_w20** (correlation=0.280, MI=0.063)
217. **price_momentum_10** (correlation=0.262, MI=0.061)
4. **price_max_w1** (correlation=0.122, MI=0.079)
3. **price_min_w1** (correlation=0.122, MI=0.078)
1. **price_mean_w1** (correlation=0.122, MI=0.072)
29. **front_mean_w2** (correlation=0.092, MI=0.078)
59. **back_min_w3** (correlation=-0.080, MI=0.079)


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
- `price_slope_2` (importance=0.7156)
- `price_slope_3` (importance=0.6038)
- `price_slope_4` (importance=0.5719)
- `price_zscore_w10` (importance=0.5615)
- `price_momentum_5` (importance=0.4826)
- `price_slope_5` (importance=0.4694)
- `front_mean_w1` (importance=0.4517)
- `front_max_w1` (importance=0.4465)
- `front_min_w1` (importance=0.4452)
- `price_percentile_w10` (importance=0.4123)


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
- Redundant features (correlation > 0.95): 21
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
