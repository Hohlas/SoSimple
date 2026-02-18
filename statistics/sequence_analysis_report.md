# Sequence Analysis Summary

**Дата создания:** 2026-02-18 17:15:38

## Data Quality

- **Successfully parsed:** 0 строк (0.00%)
- **Missing values:** Обнаружены
- **Causal consistency:** ⚠️ ISSUES DETECTED
  - Нарушения порядка: 43593 строк


## Key Findings

### Топ-10 наиболее дискриминативных позиций фракталов:



### Топ-20 engineered features по важности:

200. **price_zscore_w10** (correlation=0.303, MI=0.068)
204. **price_zscore_w20** (correlation=0.299, MI=0.057)
201. **price_percentile_w10** (correlation=0.268, MI=0.058)
172. **price_slope_3** (correlation=-0.270, MI=0.058)
205. **price_percentile_w20** (correlation=0.251, MI=0.056)
175. **price_slope_4** (correlation=-0.269, MI=0.054)
178. **price_slope_5** (correlation=-0.258, MI=0.052)
7. **front_min_w1** (correlation=0.049, MI=0.064)
8. **front_max_w1** (correlation=0.049, MI=0.064)
5. **front_mean_w1** (correlation=0.049, MI=0.064)
213. **price_momentum_5** (correlation=0.255, MI=0.049)
169. **price_slope_2** (correlation=-0.240, MI=0.048)
181. **price_slope_10** (correlation=-0.219, MI=0.037)
217. **price_momentum_10** (correlation=0.223, MI=0.036)
29. **front_mean_w2** (correlation=0.036, MI=0.042)
32. **front_max_w2** (correlation=0.031, MI=0.042)
187. **majority_direction_match_w3** (correlation=-0.178, MI=0.030)
20. **impulse_max_w1** (correlation=-0.028, MI=0.038)
19. **impulse_min_w1** (correlation=-0.028, MI=0.038)
17. **impulse_mean_w1** (correlation=-0.028, MI=0.037)


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
- `price_zscore_w10` (importance=0.6517)
- `price_zscore_w20` (importance=0.5693)
- `price_percentile_w10` (importance=0.5636)
- `price_slope_3` (importance=0.5613)
- `price_percentile_w20` (importance=0.5376)
- `price_slope_4` (importance=0.5349)
- `price_slope_5` (importance=0.5141)
- `front_min_w1` (importance=0.4989)
- `front_max_w1` (importance=0.4983)
- `front_mean_w1` (importance=0.4981)


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
- Redundant features (correlation > 0.95): 22
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
