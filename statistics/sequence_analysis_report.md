# Sequence Analysis Summary

**Дата создания:** 2026-02-17 19:28:22

## Data Quality

- **Successfully parsed:** 0 строк (0.00%)
- **Missing values:** Обнаружены
- **Causal consistency:** ⚠️ ISSUES DETECTED
  - Нарушения порядка: 32136 строк


## Key Findings

### Топ-10 наиболее дискриминативных позиций фракталов:



### Топ-20 engineered features по важности:

169. **price_slope_2** (correlation=-0.465, MI=0.262)
172. **price_slope_3** (correlation=-0.457, MI=0.250)
175. **price_slope_4** (correlation=-0.424, MI=0.232)
200. **price_zscore_w10** (correlation=0.461, MI=0.206)
178. **price_slope_5** (correlation=-0.387, MI=0.212)
213. **price_momentum_5** (correlation=0.385, MI=0.207)
204. **price_zscore_w20** (correlation=0.364, MI=0.161)
7. **front_min_w1** (correlation=0.066, MI=0.225)
5. **front_mean_w1** (correlation=0.066, MI=0.224)
8. **front_max_w1** (correlation=0.066, MI=0.224)
217. **price_momentum_10** (correlation=0.285, MI=0.164)
181. **price_slope_10** (correlation=-0.265, MI=0.141)
201. **price_percentile_w10** (correlation=0.378, MI=0.111)
224. **front_back_interaction** (correlation=0.041, MI=0.196)
19. **impulse_min_w1** (correlation=-0.028, MI=0.168)
20. **impulse_max_w1** (correlation=-0.028, MI=0.167)
17. **impulse_mean_w1** (correlation=-0.028, MI=0.167)
187. **majority_direction_match_w3** (correlation=-0.353, MI=0.081)
221. **price_momentum_20** (correlation=0.174, MI=0.119)
29. **front_mean_w2** (correlation=0.030, MI=0.152)


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
- `price_slope_2` (importance=0.7327)
- `price_slope_3` (importance=0.7060)
- `price_slope_4` (importance=0.6555)
- `price_zscore_w10` (importance=0.6240)
- `price_slope_5` (importance=0.5980)
- `price_momentum_5` (importance=0.5879)
- `price_zscore_w20` (importance=0.4890)
- `front_min_w1` (importance=0.4620)
- `front_mean_w1` (importance=0.4598)
- `front_max_w1` (importance=0.4594)


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
2. Выбрать архитектуру модели (LSTM/Transformer vs Feature-based)
3. Подготовить train/test split с учётом временной структуры
4. Применить техники балансировки классов (SMOTE, class weights)
5. Обучить модель и оценить на тестовой выборке
