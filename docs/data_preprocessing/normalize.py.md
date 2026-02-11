# normalize.py

## Назначение
Нормализация признаков для нейросети. Реализует специфичные методы для финансовых данных с тяжелыми хвостами распределений.

## Методы нормализации

| Метод | Признаки | Диапазон | Особенности |
|-------|----------|----------|-------------|
| **Piecewise Linear-Log** | `predict`, `front`, `back`, `impulse`, `count`, `reverse`, `power`, `break` | [0, 1] | Линейная часть до 85-го перцентиля, логарифмическое сжатие хвоста до 99-го. |
| **Min-Max** | `price` | [0, 1] | Классическое масштабирование. |
| **RobustScaler** | `ATR` | — | Глобальная нормализация, устойчивая к выбросам (fit на Train). |
| **Без изменений** | `direction`, `strong` | {-1, 0, 1} | Категориальные признаки. |

## Ключевые функции
- `normalize_rowwise()`: Построчная нормализация (fractals, predict) — **без утечки данных (No Data Leakage)**.
- `normalize_atr_train()`: Fit + Transform RobustScaler для ATR на обучающей выборке.
- `normalize_atr_inference()`: Transform RobustScaler для ATR на валидации/тесте.
- `piecewise_linear_log_transform()`: Реализация алгоритма PLL.

## Алгоритм Piecewise Linear-Log
1. **Линейная зона**: Значения от `min` до `p85` маппятся в `[0, 0.85]`.
2. **Логарифмическая зона**: Значения от `p85` до `p99` маппятся в `(0.85, 1.0]` через `log1p`.
3. **Цель**: Сохранить чувствительность в нормальном диапазоне и сжать экстремальные выбросы.

## Использование
```python
from normalize import normalize_rowwise, normalize_atr_train

# 1. Построчная нормализация (безопасно до сплита)
df = normalize_rowwise(df)

# ... сплит на train/val ...

# 2. ATR нормализация (после сплита)
train_df = normalize_atr_train(train_df, "scaler.pkl")
val_df = normalize_atr_inference(val_df, "scaler.pkl")
```
