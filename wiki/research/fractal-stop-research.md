---
last_updated: 2026-06-18
sources: 8
status: completed
---

# Fractal Stop Research

> Фрактальные признаки предсказывают пробой уровня, oracle (проверка потолка) показывает высокий диагностический потолок механики, но RF/XGBoost на текущем табличном представлении не дают устойчиво прибыльный торговый PF; Stage 4.3 уточнил, что провал связан с совместной слабостью breach-ранжирования и fav/TP слоя.

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

### Stage 4.1: XGBoost-fav + combined breach controls (2026-06-11/12) — ❌ FAIL

Stage 4.1 проверил два быстрых контрольных улучшения из аудита Stage 4:
- XGBoostRegressor вместо RF fav;
- combined breach H6 AND H12, где вход разрешён только если обе модели считают риск пробоя низким.

Также добавлен permutation test: перестановка breach-вероятностей и повторная симуляция, чтобы проверить, насколько наблюдаемый PF отделяется от случайного выбора.

Оба направления не прошли validation gate. Test не открывался.

### Stage 4.2: corrected diagnostic recalc (2026-06-12) — ⚠️ DIAGNOSTIC

Stage 4.2 пересчитал унаследованный winner `sell_H6_off05` с теми же параметрами (`p=0.4`, `min_fav=0.3`, `min_rr=1.0`, `tp_fraction=0.4`), но с исправленным диагностическим протоколом: train 2004-2016, `val_stop` 2017-2018 для early stopping, `val_eval` 2019-2022 для оценки, spread-коррекция под OHLC=Bid, block bootstrap и permutation test.

Статус Stage 4.2 — `DIAGNOSTIC_ONLY`: winner был выбран ранее на Stage 4 по validation 2019-2022, поэтому historical selection bias не устранён. Test не открывался.

### Stage 4.3: post-mortem diagnostics (2026-06-15) — ⚠️ DIAGNOSTIC

Stage 4.3 не выбирал нового winner и не открывал test. Он воспроизвёл Stage 4.2 baseline (`sell_H6_off05`, `p=0.4`, `min_fav=0.3`, `min_rr=1.0`, `tp_fraction=0.4`) и разложил сделки по loss attribution, breach buckets, fav buckets, cumulative 2D map, фактическому RR, TP-policy variants и oracle-deviation regimes.

Цель Stage 4.3 — понять, где теряется PF между oracle-потолком и фактическим Stage 4.2 PF, а не доказать прибыльность новой торговой зоны. Найденные прибыльные зоны имеют только статус `hypothesis_only`.

### Stage 4.4: diagnostic micro-check перед Transformer (2026-06-15) — ⚠️ DIAGNOSTIC

Stage 4.4 не выбирал нового winner и не открывал test. Проверил три гипотезы на фиксированных Stage 4.2 моделях:

1. **Relax breach p=0.5**: PF=0.862 (vs baseline 1.015), +938 сделок (57% oracle-безопасны, 43% oracle-плохие). Ослабление фильтра ухудшает PF.
2. **Fixed TP (R ∈ {0.5, 0.7, 1.0})**: лучший PF=1.038 (R=0.7), BS_p05=0.886. Fixed TP не хуже fav-based TP; fav-based TP не даёт преимущества как прямая цена TP.
3. **Breach-only entry + Fixed TP**: все PF < 0.91, permutation p ≈ 0.09. Breach без fav-фильтра убыточен; fav-фильтр добавляет +0.05 до +0.14 PF.

Выводы для Stage 5.0 Transformer: fav не нужно учить как цену TP (fixed TP достаточно), но fav необходим как фильтр входа. Основной фокус Transformer — улучшение breach-классификации.

### Stage 5.0-prep: feature ablation + AUC→PF sensitivity (2026-06-15) — ⚠️ DIAGNOSTIC

Проверялись две гипотезы перед Transformer Stage 5.0 на том же split/target/signals, что Stage 4.4.

**Feature ablation (6 профилей):**
- `time_only` (4 признака, AUC=0.6286) превосходит `no_time` (1001 признак, AUC=0.6113) — время кодирует больше breach-сигнала, чем все 1000 фрактальных признаков
- `fractal_core_only` (1000 признаков, AUC=0.6143) уступает `time_only` — календарный риск подтверждён
- `no_price` (удаление ценовых каналов) улучшает AUC на 32 bp — ценовые признаки могут шуметь в breach-классификации
- Полная модель: 0.6674, где time добавляет 561 bp, fractal добавляет 388 bp поверх time

**AUC→PF sensitivity (oracle mix):**
- Первый проход PF-gate > 1.15 при alpha=0.1, AUC=0.8442
- Требуемый прирост AUC от текущих 0.6674 до 0.8442: +1768 bp — масштаб разрыва велик
- Зона alpha ∈ [0.0, 0.1] — самый крутой участок кривой PF = f(AUC)

**Выводы для Stage 5.0:** Transformer оправдан (фрактальная структура добавляет 388 bp), но календарный baseline обязателен. Ценовые признаки можно исключить из breach-головы.

### Stage 4.5: trailing / breakeven / partial exit mechanics (2026-06-15) — ⚠️ DIAGNOSTIC

Фиксированные Stage 4.4 breach/fav модели + 5 pre-defined exit-политик. Синтетические тесты симулятора пройдены.

- `breakeven_0_3`: PF=0.717 — убивает PF, преждевременные выходы
- `trail_atr_0_2`: PF=1.831, BS_p05=1.462, neg_years=1 — лучший результат всех Fractal Stop этапов; 71% выходов по трейлингу
- `trail_atr_0_3`: PF=1.296, BS_p05=1.048 — всё ещё лучше baseline, менее агрессивный
- `partial_50_at_0_5R_then_trail`: PF=1.051 — минимальное улучшение над baseline

`trail_atr_0_2` проходит spread stress (PF=1.501 при spread=0.40). Первый diagnostic-результат, заслуживающий чистого Stage 4.6 candidate-cycle.

### Stage 4.6: clean candidate-cycle (2026-06-15, ext to 2026) — ⚠️ FAIL

Extended clean cycle: val_select 2019-2022 (4 года), val_eval 2023-2026 (из Nero.csv, без target-меток):
- `trail_atr_0_2`: val_select PF=2.041, BS_p05=1.618, concentration=0.434 — прошёл gate
- `trail_atr_0_2`: val_eval PF=0.897, BS_p05=0.679 — провал на новых данных
- Breach-модель ≤2016 не обобщается на +7 лет (2023-2026)
- Permutation test: exit-политика доминирует над breach-сигналом — выбор трейлинга не зависит от качества breach-ранжирования

### Stage 5.0: Transformer breach holdout (2026-06-17) — ❌ FAIL

Полноразмерный Transformer (d_model=64, nhead=4, 40 эпох, train ≤2020) на 5 фрактальных профилях (A6-каталог) против XGBoost baseline на том же сплите. Diagnostic holdout 2023-2026. Только модельный слой, без торгового grid search.

- Transformer primary profile holdout AUC=0.6018 vs XGBoost=0.6524 (gap −0.051)
- Все Transformer профили проигрывают XGBoost на holdout
- `no_time` профиль AUC=0.4987 (ниже случайного) — без времени Transformer бесполезен
- `time_only` XGBoost AUC=0.6059 — почти догоняет Transformer с фракталами
- Yearly degradation: 0.646→0.513 от 2023 к 2026
- Transformer показывает ХУДШИЙ lift в low-risk зоне (0.766 vs XGBoost 0.620 — lift=доля пробоев в нижних 30%; меньше=лучше)
- Вердикт: FAIL. Transformer не бьёт XGBoost в текущей реализации. Методический risk: признаки не масштабированы под нейросеть

### Stage 5.0a: feature preflight (2026-06-18) — ⚠️ DIAGNOSTIC

Stage 5.0a не обучал модель. Он проверял final tensors до нового прогона Transformer: contracts профилей, clean-controls, relative-price координату, padding/mask, fit scaler только на train и распределения после нормализации.

- Добавлен режим `--feature-preflight-only`
- `time_only_clean` отделён от `time_plus_atr`
- `nearest40_*`: `fractal0` теперь anchor и не входит в 40 соседей
- Технических ошибок нет: `NaN`, `Inf`, `PADDING_NOT_ZERO`, contract-break не найдены
- `all100_absolute_price_time` получил holdout shift по абсолютной цене — оставлен только как диагностический контроль
- Лучшие кандидаты на rerun: `all100_relative_price_*` и `nearest40_relative_price_*`
- Главная проблема corridor-профилей не пустота, а сильная truncation при `seq_len=40`:
  - `corridor_5atr`: ~52%
  - `corridor_10atr`: ~88%
  - `corridor_15atr`: ~97%
- Вывод: следующий rerun нужно строить вокруг clean-controls, no-price, relative-price и nearest40; широкие corridor-профили в текущем виде методически нечисты

### Stage 5.0a addendum: corridor full preflight (2026-06-18) — ⚠️ DIAGNOSTIC

Допроверка corridor отделила честный raw coverage до cap от уже выбранных токенов после `seq_len`. Builder теперь возвращает `candidate_count_before_cap`, `selected_count_after_cap`, `is_truncated`.

- `corridor_5atr_relative_price_atr_full` vs старый `corridor_5atr_relative_price_no_time`:
  - median raw candidates остаётся `40`
  - true truncation падает `0.491 -> 0.000`
  - снятие cap убирает искажение, но не меняет медиану профиля
- `corridor_10atr_relative_price_atr_full` vs старый `corridor_10atr_relative_price_no_time`:
  - median selected растёт `40 -> 62`
  - true truncation падает `0.871 -> 0.000`
  - старый capped-вариант реально терял заметную часть corridor
- Чистые профили без ATR-входа:
  - `corridor_5atr_relative_price_no_time_full`
  - `corridor_10atr_relative_price_no_time_full`
  - оба `DIAGNOSTIC_ONLY`, потому что имеют `row_dim=0`
- Full corridor не превратился в `all100`:
  - для `corridor_10atr_relative_price_no_time_full` доля строк с `candidate_count_before_cap >= 90` всего `~1.05%`
- Новый практический вывод:
  - обсуждать для rerun имеет смысл `corridor_5atr_relative_price_atr_full` и `corridor_10atr_relative_price_atr_full`
  - старые capped corridor-профили больше не нужны как основные кандидаты

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
| 2019 | 52 | 0.480 |
| 2020 | 145 | 1.279 |
| 2021 | 59 | 1.748 |
| 2022 | 88 | 1.138 |

Ключевые уточнения:
- 7/8 таргетов primary-профиля остались ниже PF 1.0.
- Ни один таргет не прошёл gate PF > 1.15.
- Bootstrap p05 ниже 1.0 у winner обоих профилей, поэтому результат не статистически значим.
- Лучший AUC не равен лучшему PF: `sell_H12_off02` AUC 0.6956, но PF 0.976; winner `sell_H6_off05` AUC 0.6741, но PF 1.106.

### Stage 4.1

XGBoost-fav против Stage 4 RF-fav на SELL-таргетах:

| Target | Stage 4 RF-fav PF | Stage 4.1 XGBoost-fav PF | Delta PF |
|---|---:|---:|---:|
| sell_H6_off05 | 1.106 | 0.904 | -0.202 |
| sell_H6_off02 | 0.984 | 0.899 | -0.085 |
| sell_H12_off02 | 0.976 | 0.915 | -0.061 |
| sell_H12_off05 | 0.912 | 0.901 | -0.011 |

XGBoost-fav ухудшил PF на всех 4 SELL-таргетах. Гипотеза "достаточно заменить fav-регрессор" не подтвердилась.

Combined breach H6 AND H12:

| Target | PF | Trades/yr | BS_p05 | Perm p-value | Perm median PF | Negative years |
|---|---:|---:|---:|---:|---:|---:|
| sell_comb_off05 | 1.065 | 88.5 | 0.883 | 0.050 | 0.837 | 1/4 |
| sell_comb_off02 | 0.875 | 413.5 | 0.807 | 0.160 | 0.833 | 4/4 |

`sell_comb_off05` лучше случайной медианы перестановок примерно на +0.23 PF, но не проходит gate: PF ниже Stage 4 winner, bootstrap p05 ниже 1.0, а `perm_p=0.050` слишком слаб для результата после перебора правил.

### Stage 4.2

Исправленный диагностический пересчёт унаследованного winner:

| Метрика | Stage 4 | Stage 4.2 | Комментарий |
|---|---:|---:|---|
| PF | 1.106 | 1.015 | снижение — совокупный эффект исправленного протокола |
| BS_p05 | 0.923 | 0.837 | доверительная нижняя граница остаётся ниже 1.0 |
| Breach AUC | 0.6741 | 0.6674 | разница −0.0067 после исправленного протокола |
| Trades | 344 | 503 | изменились spread-модель и фильтрация сделок |
| Negative years | 3/4 | 1/4 | годовой профиль ровнее, но не уверенно прибыльный |
| Permutation | — | 0/500 | p ≈ 0.002 только для фиксированного правила |

Годовой профиль Stage 4.2:

| Год | Сделок | PF |
|---|---:|---:|
| 2019 | 107 | 0.774 |
| 2020 | 172 | 1.071 |
| 2021 | 99 | 1.267 |
| 2022 | 125 | 1.011 |

Stage 4.2 показывает, что breach-модель добавляет реальный сигнал для фиксированного правила: ни одна из 500 перестановок breach-вероятностей не достигла PF ≥ 1.015, медианный случайный PF = 0.817. Но это не является доказательством торговой пригодности: PF не проходит gate > 1.15, BS_p05 ниже 1.0, а historical selection bias winner остаётся.

### Stage 4.3

Stage 4.3 воспроизвёл Stage 4.2 baseline с теми же числами: PF `1.015`, `503` сделки, BS_p05 `0.837`, AUC `0.6674`, 4 года validation. Основные результаты:

| Блок | Результат | Интерпретация |
|---|---:|---|
| Loss attribution | SL = 87.4% gross loss | Основные потери приходят от пробоя стопа, а не от TIMEOUT |
| Breach buckets | `[0.20,0.30)` PF 1.109, breach-rate 0.355; `[0.30,0.40)` PF 0.999, breach-rate 0.330 | Рейтинг `predict_break` на уже отобранных сделках немонотонен |
| Fav quantiles | Spearman `pred_fav` vs `true_fav` = 0.218 | Fav-регрессия слабо ранжирует будущий благоприятный ход |
| `pred_fav/stop_val` | `[1.0,1.3)` PF 1.286, BS_p05 1.036; более высокие ratio ухудшают PF | Ratio работает не как положительный фильтр; низкий фактический RR чаще достигает TP |
| Actual RR | median 0.495R, win rate 60.8%, required win rate 62.3% | Торговая система находится около нуля, но запас слабый |
| TP policy | fixed R 0.5/0.7 чуть выше current, но BS_p05 ниже 1.0 | Fixed TP не решает проблему как готовое правило |
| 2D map | нет устойчивых hypothesis_candidate ячеек | Нет готовой зоны для прямого переноса в торговое правило |

Oracle-deviation regimes:

| Regime | PF | Сделок | BS_p05 |
|---|---:|---:|---:|
| model breach + model fav | 1.015 | 503 | 0.837 |
| oracle breach + model fav | 6.613 | 1737 | 5.732 |
| model breach + oracle fav | 14.720 | 367 | 10.328 |
| oracle breach + oracle fav | 104.879 | 1560 | 73.872 |

Эти режимы подтверждают высокий диагностический потолок, но не являются торговым доказательством: oracle labels используют будущую информацию. Сравнивать PF режимов как точную аддитивную декомпозицию нельзя, потому что режимы открывают разные наборы сделок. Практический вывод: fav/TP слой является главным подозреваемым по oracle-потолку, но breach-фильтр тоже ограничивает результат.

Oracle Deviation Attribution после доработки считает PnL/yearly/bootstrap по категориям. Breach-категории взаимно исключающие; fav-категории считаются только на строках, где вход разрешён model breach или oracle breach, и могут пересекаться.

| Категория | N | Forced PnL | Вывод |
|---|---:|---:|---|
| breach: model enters, oracle blocks | 372 | -383.8 | Модель допускает часть явно плохих входов |
| breach: model misses, oracle allows | 2115 | +804.8 | Модельный breach-фильтр слишком грубо блокирует oracle-безопасные строки |
| fav: false accept | 408 | -410.4 | Модель fav разрешает фильтр там, где oracle-fav его не разрешил бы |
| fav: overpredict | 1932 | -223.5 | TP ставится слишком далеко |
| fav: underpredict | 1336 | +699.6 | Не основной источник убытка, но оставляет большой oracle-потенциал |
| fav: near oracle | 571 | +271.0 | Когда fav близок к oracle, сделки прибыльны |

### Stage 4.5 + 4.6

Stage 4.5 trailing exit mechanics:
- `trail_atr_0_2`: PF=1.831, BS_p05=1.462 — лучший diagnostic-сигнал Fractal Stop
- 71% выходов по трейлингу, neg_years=1
- Проходит spread stress (PF=1.501 при spread=0.40)

Stage 4.6 clean candidate-cycle:
- val_select 2019-2022: trail_atr_0_2 PF=2.041, concentration=0.434
- val_eval 2023-2026: trail_atr_0_2 PF=0.897 — провал на новых данных
- Permutation test: exit-политика доминирует над breach-сигналом

### Stage 5.0

Transformer против XGBoost на holdout 2023-2026 (5 профилей, single seed CPU):

| Профиль | Val AUC | Holdout AUC | Δ vs XGBoost |
|---|---:|---:|---:|
| all100_base10_time (primary) | 0.6432 | 0.6018 | −0.0506 |
| nearest40_base10_time | 0.6432 | 0.6034 | −0.0490 |
| corridor_10atr_base10_time | 0.6426 | 0.6025 | −0.0499 |
| newest20_base10_time | 0.6420 | 0.5953 | −0.0571 |
| all100_base10_no_time | 0.5291 | 0.4987 | −0.1537 |

XGBoost baselines:
- base_raw_plus_time: Holdout AUC 0.6524, lift_30 0.620
- no_time (XGBoost без времени): Holdout AUC 0.6456
- time_only: Holdout AUC 0.6059

Gate verdict (primary profile): FAIL. Все три gate не пройдены (AUC, lift_30, yearly). Transformer проигрывает XGBoost и по AUC (−0.051), и в безопасной зоне (lift_30 0.766 vs 0.620 — меньше = лучше).

Годовой разрез (primary): 2023 AUC=0.646, 2024 AUC=0.626, 2025 AUC=0.570, 2026 AUC=0.514.

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
10. Stage 4.1 закрыл быстрые контрольные гипотезы: XGBoost-fav ухудшил PF, combined breach не превзошёл Stage 4 winner и не прошёл permutation test с запасом.
11. Stage 4.2 уточнил интерпретацию Stage 4: после исправленного диагностического протокола PF унаследованного winner снижается до 1.015. Это совокупный эффект изменений протокола, не изолированная декомпозиция ошибки.
12. Breach-сигнал реален для фиксированного правила (0/500 перестановок, p ≈ 0.002), но слаб: он не даёт gate PF > 1.15 и не устраняет selection bias.
13. Stage 4.3 показал, что fav/TP слой и breach-ранжирование ломают систему вместе. Прямые отрицательные категории сопоставимы: breach false-safe около -383.8 ATR, fav false-accept около -410.4 ATR. При этом `pred_fav` слабо коррелирует с истинным fav, а высокий `pred_fav/stop_val` ухудшает PF.
14. Низкий фактический RR (median около 0.5R) объясняет, почему стратегия требует высокий win rate и остаётся около PF=1.0 даже при реальном breach-сигнале.
15. Stage 4.5 показал, что trail_atr_0_2 как exit-политика даёт PF=1.831 на diagnostic — лучший результат Fractal Stop. Но Stage 4.6 чистый candidate-cycle показал, что этот результат не обобщается на 2023-2026.
16. Stage 5.0 полноразмерный Transformer (d_model=64, 40 эпох) не бьёт XGBoost на holdout 2023-2026: AUC 0.6018 vs 0.6524, lift_30 0.766 vs 0.620 (меньше = лучше). **Методический risk:** признаки не масштабированы под нейросеть (цена в сотнях/тысячах, остальные ~0..1) — вывод относится к текущей реализации и нормализации.
17. Stage 5.0a показал, что повторный прогон Transformer ещё имеет смысл, но только на суженной матрице профилей: clean-controls, `all100_no_price_time`, `all100_relative_price_*`, `nearest40_relative_price_*`. Абсолютную цену как основной вход и широкие corridor-профили использовать нельзя.
18. **5 последовательных этапов Fractal Stop провалились как торговые кандидаты.** Breach-сигнал статистически подтверждён, но недостаточен для устойчивого ML-превосходства ни в табличной, ни в текущей sequence-реализации.

**Все этапы (Stage 2→5.0) отклонены как торговые кандидаты.** Табличные модели достигли потолка, Transformer не дал улучшения.

## Открытые вопросы

- Может ли Transformer улучшить breach-классификатор после Stage 5.0a rerun на `relative_price`/`nearest40` профилях, без абсолютной цены и с clean-controls.
- Что делать с corridor-профилями: увеличивать `seq_len`, сужать коридор или оставить corridor только как диагностику.
- Может ли другая постановка fav/exit-таргета снизить шум сильнее, чем простая замена RF-fav на XGBoost-fav.
- Работает ли выбор стороны/режима лучше, чем изолированные BUY/SELL и combined H6/H12.
- ~~Даст ли trailing stop положительное матожидание при том же breach-сигнале~~ — Stage 4.5/4.6 проверили: trail_atr_0_2 показывает высокий diagnostic PF, но не обобщается на 2023-2026.
- Помогут ли новые признаки (спред, волатильность, корреляции) улучшить fav-регрессию.
- Работает ли концепт на других активах или таймфреймах.
- Стоит ли закрыть Fractal Stop ветку и вернуться к основному направлению (regression_updn, triple barrier).

## Источники

- [2026-06-10-fractal-stop-breach-stage1.md](../../docs/reports/2026-06-10-fractal-stop-breach-stage1.md) — Stage 1 report (AUC, lift, frozen test)
- [2026-06-10-fractal-stop-fav-stage2.md](../../docs/reports/2026-06-10-fractal-stop-fav-stage2.md) — Stage 2 report (PF, grid search, frozen test, FAIL verdict)
- [2026-06-10-feature-profiles-stage3.md](../../docs/reports/2026-06-10-feature-profiles-stage3.md) — Stage 3.x report (feature profiles, Stage 3.1 ablation, Stage 3.2 XGBoost)
- [2026-06-11-stage4-trade-xgboost.md](../../docs/reports/2026-06-11-stage4-trade-xgboost.md) — Stage 4/4.1/4.2 report (XGBoost breach + RF fav trading layer, controls, diagnostic corrected recalc, FAIL verdict)
- [2026-06-15-stage4_3-diagnostics.md](../../docs/reports/2026-06-15-stage4_3-diagnostics.md) — Stage 4.3 diagnostic report (post-mortem loss attribution, fav/breach diagnostics, oracle-deviation regimes)
- [2026-06-15-stage4_5-exit-mechanics.md](../../docs/reports/2026-06-15-stage4_5-exit-mechanics.md) — Stage 4.5 exit mechanics (trailing/breakeven/partial)
- [2026-06-15-stage4_6-clean-candidate-cycle.md](../../docs/reports/2026-06-15-stage4_6-clean-candidate-cycle.md) — Stage 4.6 clean candidate-cycle (val_select 2019-2022, val_eval 2023-2026)
- [2026-06-17-stage5-transformer-breach.md](../../docs/reports/2026-06-17-stage5-transformer-breach.md) — Stage 5.0 Transformer holdout (5 профилей, FAIL verdict)
- [2026-06-18-stage5_0a-feature-preflight.md](../../docs/reports/2026-06-18-stage5_0a-feature-preflight.md) — Stage 5.0a preflight (contracts, normalization audit, relative-price vs absolute-price, corridor truncation)
