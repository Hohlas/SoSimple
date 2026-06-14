# Stage 4 Brainstorm: Диагностика причин провала и пути усиления

> **Date**: 2026-06-14  
> **Author**: AI agent (Qwen3.7-max)  
> **Status**: Brainstorm / Planning  
> **Related**: Stage 4 audit (`2026-06-11-stage4-deep-audit.md`), Stage 4 report (`docs/reports/2026-06-11-stage4-trade-xgboost.md`)

---

## Ключевое открытие: фактический RR в 2.5 раза ниже заявленного

Winner `sell_H6_off05` использует `tp_fraction=0.4` и `min_rr=1.0`. Но фильтр проверяет `fav_pred / stop_val >= 1.0`, а TP ставится на `fav_pred * 0.4`. Значит:

```
actual_RR = (fav_pred × 0.4) / stop_val = 0.4 × (fav_pred / stop_val) >= 0.4
```

**Фактический floor RR = 0.4, а не 1.0.** TP ловит только 40% предсказанного благоприятного хода. Это означает, что системе нужна win rate >70% среди resolved trades только чтобы держаться на PF=1.0.

---

## Oracle уже дал частичный ответ (Stage 2)

| Режим | Breach | Fav | PF (sell_H6_off05) |
|---|---|---|---|
| perfect_breach | ground-truth | RF | **8.02** |
| perfect_fav | RF | ground-truth | **9.39** |
| perfect_both | ground-truth | ground-truth | **∞** |
| model (Stage 4) | XGBoost | RF | **1.106** |

Оба компонента — узкие места. Но разрыв `8.02 → 1.106` (breach) vs `9.39 → 1.106` (fav) говорит, что **breach-модель вносит больший вклад в деградацию**, хотя оба критичны.

Проблема: oracle Stage 2 использовал RF, а Stage 4 — XGBoost. Нужны oracle-абляции с XGBoost.

---

## План диагностических экспериментов

### Блок 1: Ablation oracle × XGBoost (главный эксперимент)

Скрипт: новый `benchmark_fractal_stop_stage4_diag.py`, адаптация `oracle_fractal_stop_fav.py` с XGBoost.

**4 режима для sell_H6_off05:**

| # | Breach | Fav | Что проверяет |
|---|---|---|---|
| D1 | XGBoost | ground-truth | «Идеальный TP, модельный фильтр» |
| D2 | ground-truth | RF | «Идеальный фильтр, модельный TP» |
| D3 | ground-truth | XGBoost-fav | «Идеальный фильтр, XGBoost TP» |
| D4 | XGBoost | XGBoost-fav | «Полная модель Stage 4.1» (контроль) |

**Ожидаемые результаты и интерпретация:**

| D1 PF | D2 PF | Вывод |
|---|---|---|
| высокий (>3) | низкий (~1) | Breach — главный bottleneck, TP работает нормально |
| низкий (~1) | высокий (>3) | Fav — главный bottleneck, breach фильтр работает |
| оба ~2-3 | оба ~2-3 | Оба вносят равный вклад |
| оба низкие (~1) | оба низкие (~1) | Проблема не в моделях, а в их взаимодействии |

---

### Блок 2: Precision/Recall breach-модели на пороге p=0.4

Текущий winner использует `p=0.4`. Нужно измерить:

```python
y_true = val_df['sell_stop_broken_H6_off05_flag']
y_pred = breach_proba < 0.4  # вход = модель считает "не пробьёт"

precision = TP / (TP + FP)  # среди вошедших — какая доля действительно не пробита
recall = TP / (TP + FN)     # сколько "хороших" сделок мы не пропустили
```

**Если precision < 70%**: модель пропускает слишком много сделок, которые на самом деле пробьют стоп → SL losses.  
**Если recall < 50%**: модель слишком консервативна, отбрасывает прибыльные сделки.

---

### Блок 3: Анализ калибровки fav-регрессора

```python
# Для сделок, прошедших breach-фильтр:
residual = fav_pred - fav_actual  # fav_actual = target_sell_H6_val
bias = mean(residual)            # систематическое завышение/занижение
mae = mean(|residual|)           # средняя ошибка в ATR
```

**Если bias > 0 (завышение)**: TP ставится дальше реального → больше TIMEOUT и SL.  
**Если bias < 0 (занижение)**: TP ставится ближе → больше TP-hit, но меньше profit per trade.

---

### Блок 4: Влияние tp_fraction на PF

Текущий `tp_fraction=0.4` ловит только 40% predicted fav. Протестировать:

```
tp_fraction ∈ [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0]
```

Гипотеза: при `tp_fraction=0.7-0.8` (как в oracle) PF может вырасти, потому что TP будет ближе к реальному favorable move.

---

### Блок 5: Дополнительные фильтры (усиление результата)

| Фильтр | Идея | Реализация |
|---|---|---|
| **Multi-horizon breach** | Вход только если breach_H6 < p AND breach_H12 < p | Stage 4.1 уже проверил (PF=1.065, perm_p=0.05) — слабый эффект |
| **Volatility regime** | Не торговать при ATR > 2×median (кризис) | Простой фильтр по ATR-перцентили |
| **Fractal strength** | Вход только при `fractal0.strong > threshold` | Использовать существующий канал `strong` |
| **Fractal density** | Вход только при высокой плотности фракталов вокруг стопа | Использовать density-фичи из `relative_geometry_clean` |
| **Consecutive confirmation** | Вход только если 2+ последовательных фрактала подтверждают направление | Проверить `fractal0.direction == fractal1.direction` |
| **Time-of-day** | Торговать только в London+NY overlap (13:00-17:00 UTC) | Time-фичи уже есть, добавить фильтр |

---

### Блок 6: Декомпозиция PnL по exit type

Добавить в скрипт подсчёт:

```python
exits = {'TP': [], 'SL': [], 'TIMEOUT': []}
for trade in trades:
    exits[trade['exit']].append(trade['pnl_val'])

# Результат:
# TP:  n=??, mean_pnl=+??, total=+??
# SL:  n=??, mean_pnl=-??, total=-??
# TIMEOUT: n=??, mean_pnl=+/-??, total=+/-??
```

Это покажет, **какой тип выхода генерирует убытки**:
- Если SL total >> TP total → breach-фильтр пропускает плохие сделки
- Если TIMEOUT mean_pnl отрицательный → TP ставится слишком далеко
- Если TP mean_pnl малый → tp_fraction слишком консервативен

---

## Приоритетность

| # | Эксперимент | Время | Ценность |
|---|---|---|---|
| 1 | Блок 6: декомпозиция PnL по exit type | 1 час | Максимальная — сразу покажет, где теряются деньги |
| 2 | Блок 1: oracle ablation D1-D4 | 2-3 часа | Высокая — количественно разделит вклад breach и fav |
| 3 | Блок 2: precision/recall breach | 30 мин | Высокая — покажет calibration breach-модели |
| 4 | Блок 3: калибровка fav | 30 мин | Средняя — покажет bias fav-регрессора |
| 5 | Блок 4: sweep tp_fraction | 1 час | Средняя — может дать quick win |
| 6 | Блок 5: доп. фильтры | 2-3 часа | Опционально — после понимания bottleneck |

---

## Вопросы для принятия решения

Прежде чем формировать финальный план:

1. **Хотите все 6 блоков** или сфокусироваться на блоках 1-3 (диагностика) и отложить блоки 5-6 (усиление) до понимания результатов?

2. **Блок 1 (oracle ablation)** требует нового скрипта. Делать его как расширение `oracle_fractal_stop_fav.py` или как отдельный `benchmark_fractal_stop_stage4_diag.py`?

3. **Блок 5 (фильтры)**: какие из 6 фильтров вам наиболее интересны? Я бы рекомендовал начать с **volatility regime** (простой, может объяснить 2019 PF=0.48) и **fractal strength** (использует существующий канал).

---

## Связанные материалы

- `docs/audit/2026-06-11-stage4-deep-audit.md` — глубокий аудит Stage 4
- `docs/reports/2026-06-11-stage4-trade-xgboost.md` — отчёт Stage 4
- `ML/baseline/oracle_fractal_stop_fav.py` — oracle Stage 2
- `ML/baseline/benchmark_fractal_stop_stage4.py` — скрипт Stage 4
- `ML/reports/stage4_trade.json` — результаты Stage 4

---

**Последнее обновление**: 2026-06-14  
**Автор**: AI agent (Qwen3.7-max)
