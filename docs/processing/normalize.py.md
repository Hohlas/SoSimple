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
| **Piecewise Linear-Log (joint Up/Dn)** | `up_12`, `dn_12`, `up_24`, `dn_24`, `up_48`, `dn_48` | [0, 1] | По умолчанию p85/p99 считаются только по фрактальным Up/Dn текущей строки; legacy-режим может добавить top-level таргеты через `include_targets_in_updn_pool=True`. |
| **Min-Max** | `price` | [0, 1] | Классическое масштабирование. |
| **Без изменений** | `direction`, `strong`, `fractal_atr` | {-1, 0, 1} / raw | Категориальные и служебные признаки. |

## Ключевые функции
- `normalize_rowwise(df, return_updn_params=False, verbose=True, include_predict_in_front_back_pool=True, include_targets_in_updn_pool=False)`: Построчная нормализация (fractals, predict, Up/Dn таргеты). Старый front/back режим по умолчанию считает общий пул `|predict| + front + back`; live-safe контуры передают `include_predict_in_front_back_pool=False`. Up/Dn параметры по умолчанию считаются без top-level target columns, чтобы target-only значения не меняли нормализованные фрактальные признаки. При `return_updn_params=True` возвращает `(df, updn_params)`, где `updn_params` — массив shape `(N, 2)` с per-row `[brk, cap]`. Для runtime watcher-а используется `verbose=False`, чтобы не писать progress в stdout.
- `piecewise_linear_log_transform()`: Реализация алгоритма PLL.
- `normalize_atr_train()` / `normalize_atr_inference()`: Устаревшие, не используются (ATR не нормализуется, используется как знаменатель для ATR_ratio в data_loader.py).

## Per-row параметры нормализации (brk/cap)

При нормализации up/dn таргетов каждая строка использует **собственные** `brk` (p85) и `cap` (p99). По умолчанию они вычисляются только из фрактальных Up/Dn полей текущей строки:
- 100 фракталов × 6 up/dn полей = 600 значений

Legacy-режим `include_targets_in_updn_pool=True` дополнительно добавляет top-level row targets, но для direct-direction/live-safe исследований он запрещён, потому что target-only значения начинают влиять на model inputs.

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

# Live-safe режим: predict не участвует в пуле front/back,
# а top-level targets не участвуют в пуле Up/Dn-фичей
df = normalize_rowwise(
    df,
    include_predict_in_front_back_pool=False,
    include_targets_in_updn_pool=False,
    verbose=False,
)

# ... сплит на train/val/test ...
# ATR не нормализуется — используется как знаменатель для ATR_ratio в data_loader.py
```
