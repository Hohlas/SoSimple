# Sequence Analysis Summary

**Дата создания:** 2026-02-03 20:03:50

## Data Quality

- **Successfully parsed:** 10142 строк (100.00%)
- **Missing values:** Не обнаружены
- **Causal consistency:** ✅ PASSED
  - Нарушения порядка: 0 строк


## Key Findings

### Топ-10 наиболее дискриминативных позиций фракталов:


**Класс -1:**
- Позиция 0: средний |Cohen's d| = 0.703
- Позиция 1: средний |Cohen's d| = 0.368
- Позиция 3: средний |Cohen's d| = 0.280
- Позиция 2: средний |Cohen's d| = 0.227
- Позиция 17: средний |Cohen's d| = 0.182
- Позиция 12: средний |Cohen's d| = 0.164
- Позиция 21: средний |Cohen's d| = 0.150
- Позиция 10: средний |Cohen's d| = 0.134
- Позиция 9: средний |Cohen's d| = 0.131
- Позиция 50: средний |Cohen's d| = 0.128

**Класс 1:**
- Позиция 0: средний |Cohen's d| = 0.733
- Позиция 1: средний |Cohen's d| = 0.276
- Позиция 39: средний |Cohen's d| = 0.166
- Позиция 2: средний |Cohen's d| = 0.139
- Позиция 3: средний |Cohen's d| = 0.124
- Позиция 60: средний |Cohen's d| = 0.123
- Позиция 11: средний |Cohen's d| = 0.121
- Позиция 32: средний |Cohen's d| = 0.118
- Позиция 5: средний |Cohen's d| = 0.118
- Позиция 52: средний |Cohen's d| = 0.117


### Топ-20 engineered features по важности:

205. **price_percentile_w20** (correlation=0.176, MI=0.036)
204. **price_zscore_w20** (correlation=0.218, MI=0.029)
200. **price_zscore_w10** (correlation=0.216, MI=0.028)
201. **price_percentile_w10** (correlation=0.180, MI=0.029)
224. **front_back_interaction** (correlation=0.094, MI=0.032)
7. **front_min_w1** (correlation=0.050, MI=0.032)
8. **front_max_w1** (correlation=0.050, MI=0.032)
5. **front_mean_w1** (correlation=0.050, MI=0.031)
169. **price_slope_2** (correlation=-0.225, MI=0.022)
172. **price_slope_3** (correlation=-0.201, MI=0.019)
175. **price_slope_4** (correlation=-0.199, MI=0.018)
227. **impulse_direction_interaction** (correlation=0.218, MI=0.017)
213. **price_momentum_5** (correlation=0.190, MI=0.017)
217. **price_momentum_10** (correlation=0.177, MI=0.017)
32. **front_max_w2** (correlation=0.030, MI=0.022)
29. **front_mean_w2** (correlation=0.039, MI=0.021)
178. **price_slope_5** (correlation=-0.169, MI=0.014)
221. **price_momentum_20** (correlation=0.161, MI=0.014)
30. **front_std_w2** (correlation=0.017, MI=0.019)
53. **front_mean_w3** (correlation=0.030, MI=0.016)


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
- `price_zscore_w20` (importance=0.5103)
- `price_zscore_w10` (importance=0.5034)
- `price_percentile_w10` (importance=0.4984)
- `front_back_interaction` (importance=0.4967)
- `front_min_w1` (importance=0.4785)
- `front_max_w1` (importance=0.4737)
- `front_mean_w1` (importance=0.4646)
- `price_slope_2` (importance=0.4226)
- `price_slope_3` (importance=0.3645)


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
- Redundant features (correlation > 0.95): 17
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
