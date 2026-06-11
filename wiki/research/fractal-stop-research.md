---
last_updated: 2026-06-11
sources: 3
status: active
---

# Fractal Stop Research

> Фрактальные признаки предсказывают пробой уровня (AUC около 0.65), RF-торговый слой не даёт PF > 1.0, oracle (проверка потолка) показывает высокий диагностический потолок механики, а Stage 3 нашёл лучший validation-профиль признаков: `relative_geometry`.

## Хронология

### Stage 1: пробой уровня (2026-06-10) — ✅ PASS

Stage 1 проверял только один вопрос: можно ли по текущим фрактальным признакам предсказать, будет ли пробит уровень `fractal0` против предполагаемой сделки за горизонт `H`.

Разметка добавила 12 breach-таргетов:
- `H = 6` и `H = 12`;
- `stop_offset_val = 0.0`, `0.2`, `0.5`;
- BUY и SELL отдельно;
- `stop_offset_val = 0.0` используется только как диагностика.

### Stage 2: торговый слой (2026-06-10) — ❌ FAIL

Stage 2 добавил fav-регрессию (предсказание амплитуды благоприятного хода), торговый симулятор (first-touch SL/TP/TIMEOUT), grid search порогов входа и oracle-диагностику. Проверял гипотезу: breach_signal + pred_fav → PF > 1.0.

Добавлены 4 H-specific fav-таргета (H6/H12, BUY/SELL), 9 тестов, RF baseline с grid search 81 комбинации порогов на val, frozen test на test 2022–2026 и oracle-скрипт для проверки потолка механики.

### Stage 3: feature profile comparison (2026-06-10) — ✅ PASS profile-level

Stage 3 сравнил три профиля признаков на RF breach-классификаторе без торгового слоя:
- `base_raw`: 10 каналов × 100 фракталов + ATR;
- `base_plus_path`: `base_raw` + folded `mov_h` + `shift` + `log(fractal_atr/ATR)`;
- `relative_geometry`: замена raw price на `(price-f0_price)/ATR` + density + time.

Цель Stage 3 — улучшить breach AUC/lift до возврата к торговому слою. Test не открывался, сравнение выполнено на validation.

## Ключевые результаты

### Stage 1

Validation RF baseline на 8 primary-таргетах показал:

| Срез | Результат |
|---|---|
| AUC | `0.62`-`0.68` |
| lift низкого риска | `1.52`-`1.77` |
| BUY/SELL | показаны отдельно |
| Годовые срезы | без полного провала к `0.5` |

Frozen test для правила `H=6`, `stop_offset_val=0.2`, BUY+SELL:

| Таргет | Test AUC | PR-AUC | Lift |
|---|---:|---:|---:|
| BUY H6 off02 | `0.640` | `0.560` | `1.60` |
| SELL H6 off02 | `0.649` | `0.630` | `1.69` |

### Stage 2

Grid search на val (8 комбинаций H×off×side, 81 порог):

| Комбинация | PF (canonical) | PF (diag 0.0) | PF (stress 0.4) | Trades/yr |
|---|---|---|---|---|
| buy_H6_off02 | 0.867 | 0.963 | 0.840 | 61.0 |
| sell_H6_off02 | 0.894 | 1.035 | 0.914 | 53.8 |
| buy_H6_off05 | 0.878 | 0.976 | 0.779 | 467.8 |
| sell_H6_off05 | 0.879 | 0.975 | 0.771 | 516.2 |
| buy_H12_off02 | 0.680 | 0.761 | 0.630 | 47.8 |
| sell_H12_off02 | 0.592 | 0.642 | 0.580 | 36.5 |
| buy_H12_off05 | 0.895 | 1.038 | 0.778 | 51.8 |
| **sell_H12_off05** | **0.975** | **1.060** | **0.891** | **141.2** |

**Ни одна комбинация не достигла PF > 1.0 на каноническом спреде 0.20.**

Frozen test (sell_H12_off05, test 2022–2026):

| Spread | PF | Trades | Trades/yr | Негативных лет |
|---|---|---|---|---|
| canonical 0.20 | 0.837 | 414 | 82.8 | 3/5 |
| stress 0.40 | 0.792 | 400 | 80.0 | 3/5 |
| diagnostic 0.00 | 0.819 | 434 | 86.8 | 3/5 |

Test breach AUC: 0.653 (на уровне Stage 1 frozen test 0.649).

Oracle-диагностика на validation:

| Режим | Диапазон PF canonical | Вывод |
|---|---:|---|
| perfect_breach | 8-28 | Идеальное знание пробоя даёт высокий PF при ≥30 сделок/год во всех срезах |
| perfect_fav | 7-24 | Идеальное знание fav тоже сильное, но один H12 SELL-срез ниже 30 сделок/год |
| perfect_both | ∞ | При идеальном знании обоих labels на val нет убыточных сделок |

### Stage 3

Сравнение feature profiles на validation:

| Профиль | N фич | AUC mean | ΔAUC mean | Вердикт |
|---|---:|---:|---:|---|
| `base_raw` | 1001 | 0.6454 | — | baseline |
| `base_plus_path` | 1701 | 0.6335 | −119 bp | FAIL для RF breach |
| `relative_geometry` | 1011 | 0.6580 | +119 bp | PASS как целый профиль |

Ключевые уточнения:
- `relative_geometry` улучшил 7 из 8 таргетов; годовых провалов нет (`0/32` year-slices с AUC < 0.55).
- `base_plus_path` ухудшил все 8 таргетов, но профиль проверял folded `mov_h`, `shift` и `atr_ratio` вместе; это не доказывает, что каждый компонент вреден отдельно.
- Вклад `density` и `time` не изолирован: они проверялись вместе с заменой raw price на ATR-relative price.
- Текущая density-реализация считает сам `fractal0`; нужен вариант `density_excl_f0`.
- Ранняя оценка “пустых фракталов” была артефактом `parse_fractal()` на нормализованных float-полях. Stage 3 pandas-экстрактор читает все 100 фракталов корректно.

## Выводы

1. Breach-классификатор работает стабильно (AUC 0.65 на OOS), но текущая RF-связка breach+fav не транслируется в положительное матожидание.
2. Fav-регрессия слаба (MSE ~3-5 в ATR²) — RF не может надёжно предсказать амплитуду хода от фрактальных признаков.
3. На diagnostic spread (0.0) PF достигает 1.06, но сразу падает до 0.84–0.98 при спреде 0.20. Маржинальность текущей RF-модели не переживает издержки.
4. 3/5 лет OOS убыточны при достаточном количестве сделок.
5. Oracle-диагностика не является торговым доказательством, но показывает высокий потолок механики: проблема текущего Stage 2 — извлечение сигнала моделью.
6. Stage 3 показал, что перевод raw price в ATR-relative geometry улучшает breach-классификацию, но текущий результат ещё не готов к XGBoost без Stage 3.1 абляции.

**RF Stage 2 отклонён, но fractal-stop research не закрыт окончательно.** Следующая разумная гипотеза — Stage 3.1: очистить `relative_geometry`, исключить `fractal0` из density, разложить вклад price/density/time и только затем переходить к XGBoost/LightGBM.

## Открытые вопросы

- Сохранится ли uplift после очистки `relative_geometry`: `relative_price_only`, `density_excl_f0`, `time`, `relative_geometry_clean`.
- Может ли более сложная модель (Transformer, XGBoost/LightGBM) улучшить breach-классификатор и fav-прогноз.
- Даст ли trailing stop или partial TP положительное матожидание при том же breach-сигнале.
- Помогут ли новые признаки (спред, волатильность, корреляции) улучшить fav-регрессию.
- Работает ли концепт на других активах или таймфреймах.

## Источники

- [2026-06-10-fractal-stop-breach-stage1.md](../../docs/reports/2026-06-10-fractal-stop-breach-stage1.md) — Stage 1 report (AUC, lift, frozen test)
- [2026-06-10-fractal-stop-fav-stage2.md](../../docs/reports/2026-06-10-fractal-stop-fav-stage2.md) — Stage 2 report (PF, grid search, frozen test, FAIL verdict)
- [2026-06-10-feature-profiles-stage3.md](../../docs/reports/2026-06-10-feature-profiles-stage3.md) — Stage 3 report (feature profiles, relative geometry uplift, Stage 3.1 next step)
