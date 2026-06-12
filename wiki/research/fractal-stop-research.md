---
last_updated: 2026-06-11
sources: 4
status: active
---

# Fractal Stop Research

> Фрактальные признаки предсказывают пробой уровня, oracle (проверка потолка) показывает высокий диагностический потолок механики, но ни RF, ни XGBoost breach+fav торговый слой не дают статистически значимый PF > 1.0 на validation.

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

### Stage 3.x: feature profiles + XGBoost (2026-06-10/11) — ✅ PASS model-level, trading unproven

Stage 3 сравнил три профиля признаков на RF breach-классификаторе без торгового слоя:
- `base_raw`: 10 каналов × 100 фракталов + ATR;
- `base_plus_path`: `base_raw` + folded `mov_h` + `shift` + `log(fractal_atr/ATR)`;
- `relative_geometry`: замена raw price на `(price-f0_price)/ATR` + density + time.

Stage 3.1 разложил `relative_geometry` на компоненты: `relative_price_only`, `density_excl_f0`, time, clean geometry. Stage 3.2 проверил XGBoost на `time_only`, `base_raw`, `base_raw_plus_time`, `relative_geometry_clean`.

Цель Stage 3.x — улучшить breach AUC/lift до возврата к торговому слою. Test не открывался, сравнение выполнено на validation.

### Stage 4: XGBoost trading layer (2026-06-11) — ❌ FAIL

Stage 4 проверил, конвертируется ли улучшение breach-классификатора в торговый PF. Breach заменён на XGBoost, fav-регрессор оставлен RF из Stage 2, чтобы изолировать вклад breach-модели.

Проверены два профиля:
- `base_raw_plus_time`: 1005 фич, основной профиль;
- `relative_geometry_clean`: 1011 фич, контроль.

Торговое правило осталось тем же: вход на `Open` следующего H1-бара, canonical spread 0.20, first-touch SL/TP/TIMEOUT, grid search только на validation, test не открывался.

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

### Stage 3.x

Первичное сравнение RF feature profiles на validation:

| Профиль | N фич | AUC mean | ΔAUC mean | Вердикт |
|---|---:|---:|---:|---|
| `base_raw` | 1001 | 0.6454 | — | baseline |
| `base_plus_path` | 1701 | 0.6335 | −119 bp | FAIL для RF breach |
| `relative_geometry` | 1011 | 0.6580 | +119 bp | PASS как целый профиль |

Stage 3.1 RF ablation:

| Профиль | AUC mean | ΔAUC vs RF base_raw | Вывод |
|---|---:|---:|---|
| `relative_price_only` | 0.6414 | −40 bp | Не помогает RF |
| `relative_price_plus_density_excl_f0` | 0.6422 | −32 bp | Density не даёт самостоятельной пользы |
| `relative_price_plus_time` | 0.6575 | +121 bp | Основной uplift от time |
| `relative_geometry_clean` | 0.6581 | +127 bp | Почти то же, что time |

Stage 3.2 XGBoost:

| Профиль | AUC mean | ΔAUC vs RF base_raw | Вывод |
|---|---:|---:|---|
| `time_only` | 0.6300 | −154 bp | Время само по себе слабее фракталов |
| `base_raw` | 0.6594 | +140 bp | XGBoost лучше RF на тех же признаках |
| `base_raw_plus_time` | 0.6799 | +345 bp | Лучший простой кандидат для Stage 4 |
| `relative_geometry_clean` | 0.6808 | +354 bp | На 9 bp выше, но сложнее |

Ключевые уточнения:
- `relative_geometry` улучшил 7 из 8 таргетов на Stage 3, но Stage 3.1 показал, что практический вклад был от time-фичей.
- `base_plus_path` ухудшил все 8 таргетов, но профиль проверял folded `mov_h`, `shift` и `atr_ratio` вместе; это не доказывает, что каждый компонент вреден отдельно.
- Ранняя оценка “пустых фракталов” была артефактом `parse_fractal()` на нормализованных float-полях. Stage 3 pandas-экстрактор читает все 100 фракталов корректно.
- Mean AUC 0.70 формально не достигнут: лучший mean 0.6808, разрыв около 192 bp. Лучший отдельный target `sell_H12_off02` у `base_raw_plus_time` AUC 0.6956.

### Stage 4

Validation-only торговая проверка XGBoost breach + RF fav:

| Метрика | `base_raw_plus_time` | `relative_geometry_clean` |
|---|---:|---:|
| Winner target | sell_H6_off05 | sell_H6_off05 |
| Winner PF | 1.106 | 1.142 |
| Winner BS_p05 | 0.923 | 0.906 |
| Winner trades/year | 86.0 | 54.5 |
| Таргетов PF ≥ 1.0 | 1/8 | 2/8 |
| Таргетов PF ≥ 1.15 | 0/8 | 0/8 |
| Buy mean PF | 0.869 | 0.886 |
| Sell mean PF | 0.995 | 1.006 |

Winner `sell_H6_off05` выбран обоими профилями с одинаковыми параметрами: `p=0.4`, `min_fav=0.3`, `min_rr=1.0`, `tp_fraction=0.4`.

Годовая устойчивость winner `base_raw_plus_time`:

| Год | Сделок | PF |
|---|---:|---:|
| 2019 | 120 | 1.164 |
| 2020 | 87 | 1.327 |
| 2021 | 84 | 0.788 |
| 2022 | 53 | 1.287 |

Ключевые уточнения:
- 7/8 таргетов primary-профиля остались ниже PF 1.0.
- Ни один таргет не прошёл gate PF > 1.15.
- Bootstrap p05 ниже 1.0 у winner обоих профилей, поэтому результат не статистически значим.
- Лучший AUC не равен лучшему PF: `sell_H12_off02` AUC 0.6956, но PF 0.976; winner `sell_H6_off05` AUC 0.6741, но PF 1.106.

## Выводы

1. Breach-классификатор работает стабильно (AUC 0.65 на OOS), но текущая RF-связка breach+fav не транслируется в положительное матожидание.
2. Fav-регрессия слаба (MSE ~3-5 в ATR²) — RF не может надёжно предсказать амплитуду хода от фрактальных признаков.
3. На diagnostic spread (0.0) PF достигает 1.06, но сразу падает до 0.84–0.98 при спреде 0.20. Маржинальность текущей RF-модели не переживает издержки.
4. 3/5 лет OOS убыточны при достаточном количестве сделок.
5. Oracle-диагностика не является торговым доказательством, но показывает высокий потолок механики: проблема текущего Stage 2 — извлечение сигнала моделью.
6. Stage 3.x показал, что XGBoost `base_raw_plus_time` существенно улучшает breach-классификацию: +345 bp к RF `base_raw`.
7. Stage 4 показал, что этот прирост AUC не конвертируется в устойчивый торговый PF: лучший primary PF 1.106 имеет BS_p05 0.923, а 7/8 таргетов убыточны.
8. AUC breach-классификатора плохо ранжирует торговые таргеты по PF; торговый слой нужно оценивать только через execution-aware simulation.
9. `relative_geometry_clean` немного лучше по AUC/PF, но преимущество мало и не проходит gate; простой `base_raw_plus_time` остаётся предпочтительным, если линия будет продолжена.

**RF Stage 2 и XGBoost Stage 4 отклонены.** Fractal-stop research не закрыт окончательно, но плоское табличное представление фракталов достигло практического потолка для текущей торговой постановки. Следующий разумный путь — Transformer encoder на sequence-представлении или пересмотр торговой логики.

## Открытые вопросы

- Может ли Transformer улучшить breach-классификатор и торговый PF за счёт sequence-представления фракталов.
- Остаётся ли fav-регрессия слабым звеном после замены RF breach на XGBoost breach.
- Поможет ли XGBoost/другая модель для fav-регрессии, если breach оставить XGBoost.
- Работает ли комбинированный buy+sell выбор стороны лучше, чем изолированные стороны.
- Даст ли trailing stop или partial TP положительное матожидание при том же breach-сигнале.
- Помогут ли новые признаки (спред, волатильность, корреляции) улучшить fav-регрессию.
- Работает ли концепт на других активах или таймфреймах.

## Источники

- [2026-06-10-fractal-stop-breach-stage1.md](../../docs/reports/2026-06-10-fractal-stop-breach-stage1.md) — Stage 1 report (AUC, lift, frozen test)
- [2026-06-10-fractal-stop-fav-stage2.md](../../docs/reports/2026-06-10-fractal-stop-fav-stage2.md) — Stage 2 report (PF, grid search, frozen test, FAIL verdict)
- [2026-06-10-feature-profiles-stage3.md](../../docs/reports/2026-06-10-feature-profiles-stage3.md) — Stage 3.x report (feature profiles, Stage 3.1 ablation, Stage 3.2 XGBoost)
- [2026-06-11-stage4-trade-xgboost.md](../../docs/reports/2026-06-11-stage4-trade-xgboost.md) — Stage 4 report (XGBoost breach + RF fav trading layer, FAIL verdict)
