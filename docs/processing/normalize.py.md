# normalize.py

## Назначение
Нормализация признаков для нейросети. Реализует специфичные методы для финансовых данных с тяжелыми хвостами распределений.

Поддерживает текущий 22-польный формат фрактала и legacy 18-польный формат:
для старых строк `fractal_atr` из позиции 17 переносится в современную позицию
21 перед записью в рабочий массив.

## Методы нормализации

| Метод | Признаки | Диапазон | Особенности |
|-------|----------|----------|-------------|
| **Piecewise Linear-Log** | `predict`, `front`, `back`, `impulse`, `count`, `reverse`, `power`, `break` | [0, 1] | Линейная часть до 85-го перцентиля, логарифмическое сжатие хвоста до 99-го. |
| **Piecewise Linear-Log (joint Up/Dn)** | `up_12`, `dn_12`, `up_24`, `dn_24`, `up_48`, `dn_48` | [0, 1] | 606 значений на строку (100 фракталов × 6 + 6 таргетов), общие p85/p99. |
| **Min-Max** | `price` | [0, 1] | Классическое масштабирование. |
| **Без изменений** | `direction`, `strong`, `fractal_atr` | {-1, 0, 1} / raw | Категориальные и служебные признаки. |

## Ключевые функции
- `normalize_rowwise(df, return_updn_params=False, verbose=True)`: Построчная нормализация (fractals, predict, Up/Dn таргеты) — **без утечки данных (No Data Leakage)**. При `return_updn_params=True` возвращает `(df, updn_params)`, где `updn_params` — массив shape `(N, 2)` с per-row `[brk, cap]`. Для runtime watcher-а используется `verbose=False`, чтобы не писать progress в stdout.
- `piecewise_linear_log_transform()`: Реализация алгоритма PLL.
- `normalize_atr_train()` / `normalize_atr_inference()`: Устаревшие, не используются (ATR не нормализуется, используется как знаменатель для ATR_ratio в data_loader.py).

## Per-row параметры нормализации (brk/cap)

При нормализации up/dn таргетов каждая строка использует **собственные** `brk` (p85) и `cap` (p99), вычисленные из пула 606 значений:
- 100 фракталов × 6 up/dn полей = 600 значений
- 6 row-level таргетов (up_12..dn_48) = 6 значений

Эти параметры необходимы для **точной инверсии** (денормализации) — без них невозможно восстановить исходные значения в пунктах. Сохраняются через `label_main.py` в `DATA/Nero_*_updn_params.npy`.

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
# updn_params.shape == (N, 2), updn_params[i] = [brk, cap] для строки i

# Тихий режим для runtime/inference-процессов
df = normalize_rowwise(df, verbose=False)

# ... сплит на train/val/test ...
# ATR не нормализуется — используется как знаменатель для ATR_ratio в data_loader.py
```
