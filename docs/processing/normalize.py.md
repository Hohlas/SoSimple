# normalize.py

## Назначение
Нормализация признаков для нейросети. Реализует специфичные методы для финансовых данных с тяжелыми хвостами распределений.

Поддерживает текущий 23-польный формат фрактала и legacy 18/22-польные форматы:
для старых строк `fractal_atr` из позиции 17 переносится в современную позицию
21 перед записью в рабочий массив, `shift` добавляется как NaN.

## Методы нормализации

| Метод | Признаки | Диапазон | Особенности |
|-------|----------|----------|-------------|
| **Piecewise Linear-Log** | `predict`, `front`, `back`, `impulse`, `count`, `reverse`, `power`, `break` | [0, 1] | Линейная часть до 85-го перцентиля, логарифмическое сжатие хвоста до 99-го. |
| **Piecewise Linear-Log (per-pair Up/Dn)** | 5 пар: up_3/dn_3, up_6/dn_6, up_12/dn_12, up_24/dn_24, up_48/dn_48 | [0, 1] | 200 значений на пару (100 фракталов × 2 поля), per-pair p85/p99 из фракталов. Таргеты строки нормализуются теми же параметрами, не входят в расчёт. |
| **Min-Max** | `price` | [0, 1] | Классическое масштабирование. |
| **Без изменений** | `direction`, `strong`, `fractal_atr` | {-1, 0, 1} / raw | Категориальные и служебные признаки. |

## Ключевые функции
- `normalize_rowwise(df, return_updn_params=False, verbose=True, include_predict_in_front_back_pool=True)`: Построчная нормализация (fractals, predict, Up/Dn таргеты). Старый режим по умолчанию считает общий пул `|predict| + front + back`. Для live-safe контуров нужно передавать `include_predict_in_front_back_pool=False`, чтобы future-derived `predict` не влиял на нормализацию `front/back`. При `return_updn_params=True` возвращает `(df, updn_params)`, где `updn_params` — массив shape `(N, 5, 2)` с per-row per-pair `[brk, cap]` (пары: up_3/dn_3, up_6/dn_6, up_12/dn_12, up_24/dn_24, up_48/dn_48).
- `piecewise_linear_log_transform()`: Реализация алгоритма PLL.
- `normalize_atr_train()` / `normalize_atr_inference()`: Устаревшие, не используются (ATR не нормализуется, используется как знаменатель для ATR_ratio в data_loader.py).

## Per-row параметры нормализации (brk/cap)

При нормализации up/dn таргетов каждая пара up_X/dn_X нормализуется независимо:
- Параметры p85/p99 вычисляются только по 100 фракталам текущей строки для этой пары (200 значений)
- Строковые таргеты (row-level columns) **не входят** в расчёт параметров
- Нормализованные значения таргетов получаются применением тех же параметров

Эти параметры необходимы для **точной инверсии** (денормализации) — без них невозможно восстановить исходные значения в пунктах. Сохраняются через `label_main.py` в `DATA/Nero_*_updn_params.npy` как shape `(N, 5, 2)`.

## Алгоритм Piecewise Linear-Log
1. **Линейная зона**: Значения от `min` до `p85` маппятся в `[0, 0.85]`.
2. **Логарифмическая зона**: Значения от `p85` до `p99` маппятся в `(0.85, 1.0]` через `log1p`.
3. **Цель**: Сохранить чувствительность в нормальном диапазоне и сжать экстремальные выбросы.

## Использование
```python
from normalize import normalize_rowwise

# Построчная нормализация (безопасно до сплита)
df = normalize_rowwise(df, stats_path="stats.csv")

# С сохранением per-row brk/cap для последующей денормализации
df, updn_params = normalize_rowwise(df, stats_path="stats.csv", return_updn_params=True)
# updn_params.shape == (N, 5, 2), updn_params[i, pair] = [brk, cap] для строки i, пары pair

# Тихий режим для runtime/inference-процессов
df = normalize_rowwise(df, verbose=False)

# Live-safe режим: predict не участвует в пуле front/back
df = normalize_rowwise(df, include_predict_in_front_back_pool=False, verbose=False)

# ... сплит на train/val/test ...
# ATR не нормализуется — используется как знаменатель для ATR_ratio в data_loader.py
```
