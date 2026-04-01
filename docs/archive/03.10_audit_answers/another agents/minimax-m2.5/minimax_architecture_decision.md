# Architecture Decision Record (ADR)

## Status: Proposed (ожидает реализации)

**Дата**: 2026-03-09  
**Решение**: REGRESSION как основная задача с исправлением target

---

## Резюме

После аудита проекта выбрана стратегия **REGRESSION** как основная задача вместо классификации, поскольку:

1. **Лучшие метрики**: Pearson r = 0.55 vs F1_minority = 0.35
2. **Практическая ценность**: Предсказание magnitude движения полезно для position sizing
3. **Потолок классификации**: Все архитектуры упираются в ~0.57 macro F1 — проблема в данных/признаках, не в архитектуре

**НО**: Текущая реализация regression содержит критический баг — Directional Accuracy = 97.5% — это артефакт обработки данных, а не реальная метрика.

---

## Рекомендуемая архитектура

### Для Regression (приоритет)

| Компонент | Выбор | Обоснование |
|-----------|-------|-------------|
| **Модель** | Transformer | Лучший pearson_r = 0.563, но медленный (1549 сек) |
| **Альтернатива** | BiLSTM | r = 0.555, быстрее (128 сек), меньше overfitting |
| **Lightweight** | CNN1D | r = 0.519, быстрый (60 сек), хорошо для экспериментов |

**Финальный выбор**: BiLSTM — лучшее соотношение качество/скорость после исправления target.

### Гиперпараметры (текущие)

| Параметр | Значение | Рекомендация |
|----------|----------|--------------|
| lr | 1e-3 | Оставить |
| weight_decay | 1e-4 | Увеличить до 1e-3 для борьбы с overfitting |
| batch_size | 256 | Оставить |
| epochs | 50 | Оставить (early stopping) |
| patience | 10 | Уменьшить до 5 |
| dropout | 0.3 | Увеличить до 0.4-0.5 |
| loss | HuberLoss (delta=1.0) | Оставить |

---

## Known Issues

### 1. Direction Leakage (КРИТИЧЕСКИЙ)

**Проблема**: [`ML/data_loader.py`](../../../../../ML/data_loader.py) (строки 269-271)
```python
y_train = np.abs(df_train[target].values)  # Убирает sign!
```

**Влияние**: Directional Accuracy = 97.5% — бессмысленная метрика

**Решение**: 
- Вариант A: Предсказывать sign и magnitude отдельно
- Вариант B: Убрать np.abs(), использовать signed target
- Вариант C: Исключить fractal[0].direction из features

### 2. Overfitting

**Проблема**: Best epoch = 3-5 для большинства моделей

**Решение**:
- Увеличить dropout до 0.4-0.5
- Увеличить weight_decay до 1e-3
- Early stopping с patience = 5

### 3. Потолок качества

**Проблема**: Все архитектуры дают r = 0.52-0.56

**Гипотеза**: Потолок данных/признаков, не архитектуры

**Решение**: Feature engineering (rolling stats, momentum, multi-scale)

---

## План исправлений

### Шаг 1: Исправить regression target

```python
# data_loader.py - изменить логику для regression

# Вариант B (простой):
def get_regression_target(df, target='predict'):
    # НЕ использовать abs()
    y = df[target].values.astype(np.float32)
    return y  # Сохраняет sign!
```

### Шаг 2: Обновить метрики

```python
# utils.py - directional_accuracy теперь осмысленная
# Оставить как есть - она будет работать правильно с signed target
```

### Шаг 3: Переобучить модели

```bash
# После исправления - переобучить
python -m ML.train --model bilstm --task regression
python -m ML.train --model transformer --task regression
```

### Шаг 4: Ожидаемые результаты

| Метрика | До исправления | Ожидается после |
|---------|----------------|-----------------|
| DirAcc | 97.5% (артефакт) | ~50-55% (реально) |
| Pearson r | 0.55 | 0.50-0.58 |
| MAE | 0.10-0.11 | ~0.10 |

**Важно**: DirAcc СНИЗИТСЯ после исправления — это нормально!

---

## Сравнение с Baseline

### Regression (текущее состояние)

| Модель | Pearson r | R² | MAE | Время |
|--------|-----------|-----|-----|-------|
| **Transformer** | **0.563** | 0.306 | 0.114 | 1549c |
| BiLSTM | 0.555 | 0.306 | 0.103 | 128c |
| Hybrid | 0.546 | 0.283 | 0.115 | 75c |
| CNN1D | 0.519 | 0.232 | 0.103 | 60c |

### Classification (для сравнения)

| Модель | F1_macro | F1(-1) | F1(1) |
|--------|----------|--------|-------|
| **Hybrid** | **0.568** | 0.417 | 0.353 |
| Transformer | 0.567 | 0.392 | 0.359 |
| BiLSTM | 0.553 | 0.370 | 0.340 |
| CNN1D | 0.346* | 0.368 | 0.325 |

*CNN1D обучался с f1_minority metric

---

## Риски и Mitigation

| Риск | Вероятность | Mitigation |
|------|-------------|------------|
| Исправление target ухудшит r | Средняя | Это честная метрика — лучше знать правду |
| Overfitting не решится | Высокая | Попробовать более простую архитектуру |
| Данные не несут сигнал | Средняя | Добавить feature engineering |

---

## Следующие шаги

1. ✅ Принять это ADR
2. 🔄 Исправить regression target в data_loader.py
3. 🔄 Переобучить модели
4. 🔄 Запустить Optuna HPO для regression
5. 📅 Финальная оценка на test set

---

## References

- [Project Audit and Plan](minimax_project_audit_and_plan.md)
- [Implementation Plan](../../../../plans/ml_implementation_plan.md)
- [Neural Networks Pipeline](../../../../ML/neural_networks.md)
