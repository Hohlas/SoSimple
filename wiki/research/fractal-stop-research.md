---
last_updated: 2026-06-29
sources: 27
status: active
---

# Fractal Stop Research

> Фрактальные признаки предсказывают пробой уровня, oracle (проверка потолка) показывает высокий диагностический потолок механики, но RF/XGBoost/Transformer пока не дают устойчивого торгового или модельного превосходства. Stage 5.0d закрыл постановку `H6_off05` на текущих профилях. Stage 5.0e показал: меньший Transformer действительно уменьшает признаки переобучения, но не догоняет XGBoost на тех же признаках. Stage 5.0f добавил: H2 (temporal decay) скорее опровергнута — `fixed` последовательно превосходит `rolling`, старые данные не вредят; H1 (слабый сигнал) тоже не подтверждена — некоторые AUC выше 0.68. Stage 5.1 выделил `back` (`back_val`, сила тыловой границы уровня) как единственное устойчивое структурное поле. Stage 5.1b подтвердил, что сигнал `back` не сводится к возрасту фрактала (`shift`), а Up/Dn поля дают только слабую самостоятельную добавку и не улучшают `structure_full`. Stage 5.2 после bugfix показал содержательное ранжирование времени до пробоя (`Spearman≈0.31-0.33`, `AUC≈0.70`), снова вокруг `back`, но не прошёл candidate-gate из-за MAE хуже constant baseline и невалидного oracle comparison. Stage 5.3 показал, что дискретная bucket-цель `fast` сильнее обычной регрессии: sell проходит target-reformulation gate, buy пограничен и проходит порог delta только в 1/3 seed. Stage 5.4 проверил price/ATR вокруг `fast` и отверг `price_coord_atr`: дельты малы, per-seed порог не пройден ни на sell, ни на buy. [Stage 6.0](../../docs/reports/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md) проверил outcome-based triple-barrier (TP/SL/timeout) и получил MODEL_GATE_FAILED: AUC 0.585, PF ~0.96, permutation p-value 1.0. Итог остаётся диагностическим. Все подходы на основе `clock_shift_back` исчерпаны — нужны признаки, учитывающие режим волатильности, уровни накопления, или мульти-таймфрейм.

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

### Stage 4 deep diagnostics + trailing stop (2026-06-14) — ⚠️ DIAGNOSTIC

Глубокая диагностика Stage 4 на инфраструктуре Stage 4.2 проверила, что слабее: breach-модель, fav-модель или механика выхода.

- Partial Oracle: baseline PF=1.015; perfect_breach PF=6.613; perfect_fav PF=14.720; perfect_both PF=104.879. Fav — большее узкое место, но оба компонента усиливают друг друга.
- Сканирование параметров показало, что текущие `off=0.5`, `tp_fraction=0.4`, `min_rr=1.0` уже являются локальным оптимумом.
- Strong fractal, ATR regime, combined H6/H12 breach и quantile fav не улучшили результат.
- Dynamic TP как идеальный выход дал PF=3.462, то есть основной потолок лежит в механике выхода.
- Реалистичный `trail_atr_0_2` дал PF=1.655 против baseline 1.015: средний убыток снизился с 0.872 до 0.365 ATR, TIMEOUT исчезли.

Практический вывод Stage 4 deep diagnostics: фиксированный TP/SL не фиксирует благоприятное движение до разворота. Но результат `trail_atr_0_2` ещё диагностический и требует чистого candidate-cycle.

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

### Stage 4.7: walk-forward diagnostics (2026-06-15) — ⚠️ DIAGNOSTIC

Stage 4.7 проверил, спасает ли расширение обучения или walk-forward подход провал `trail_atr_0_2` на 2023-2026.

- Expanding Window с темпоральным early stopping воспроизвёл Stage 4.6: train≤2016 → 2023-2026 PF=0.897, BS_p05=0.679, 357 сделок.
- Добавление поздних данных не спасло: train≤2020 PF=0.917, train≤2022 PF=0.840 на 2023-2026.
- Anchored и Rolling WFO прибыльны на 2019-2022, но снова проваливаются на 2023-2026: Anchored train≤2022 PF=0.897, Rolling 2013-2022 PF=0.942.
- Self-val даёт намного больше сделок (1364-1973 против 357), поэтому абсолютные PF не сопоставимы с темпоральным протоколом.
- XGBoost warm-start не дал преимущества: PF 0.882-0.939 на 2023-2026.

Вывод: проблема Stage 4.6 не в объёме данных. Паттерн совместим с календарным риском и сменой режима после 2022, но причинность не доказана.

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

### Stage 5.0a A7 distribution audit + transform comparison (2026-06-20/21) — ⚠️ DIAGNOSTIC

Stage 5.0a A7-аудит проверил распределения признаков до обучения: хвосты, сдвиг между годами, padding, corridor bounds и статистику по позициям токенов. Обучение не запускалось.

- Для 7 rerun-кандидатов после `log1p(ATR)` + signed-log(`price_coord_atr`) исчезли `TAIL_GT10/TAIL_GT20`.
- Остался `REGIME_SHIFT in ATR`: train p95=1.66, holdout p95=4.80, delta=3.14. Это зафиксировано как сдвиг режима, а не подгоняется.
- Per-position audit нашёл скрытый хвост старого `price_coord_atr` на позиции 99 у `all100_relative_price_*`; signed-log убрал этот хвост.
- Сравнение способов сжатия на 11 профилях: `current` = 11 WARNING / 0 OK, `asinh` = 0 WARNING / 11 OK, `piecewise_tail` = 0 WARNING / 11 OK.
- `all100_absolute_price_atr_scaled_time_raw` не имел хвоста `abs>10` даже без `asinh`; `asinh(price/ATR)` дополнительно снизил train max с 6.67 до 3.39.
- Решение для следующего обучения: использовать `asinh` как основной заранее зафиксированный transform-кандидат; `piecewise_tail` оставить как диагностический контроль.

Практический вывод: абсолютную цену нельзя исключать только потому, что старый `all100_absolute_price_time` кодировал эпоху. Дешёвая проверка `price/ATR` показала, что `all100_absolute_price_atr_scaled_time_asinh` методически чистый и заслуживает отдельной проверки в обучении.

### Stage 5.0b: asinh Transformer rerun (2026-06-21/22) — ⚠️ DIAGNOSTIC

Stage 5.0b выполнил отдельный Transformer-прогон с заранее зафиксированным `asinh`, обязательными проверками перед обучением и сравнением с XGBoost. Holdout 2023-2026 использовался только для раскрытия результата. Торговый winner не объявлялся.

Sell target `sell_stop_broken_H6_off05_flag`:

- Лучший основной Transformer `all100_relative_price_time`: val AUC=0.6719, val lift_30=0.5044, holdout AUC=0.6373, holdout lift_30=0.6468.
- XGBoost `base_raw_plus_time`: val AUC=0.6631, val lift_30=0.5539.
- AUC-порог для продолжения был 0.6731; разрыв 0.0012 мал и не считается устойчивым сигналом в single-seed режиме.
- `all100_absolute_price_atr_scaled_time_asinh` как проверочный профиль был близко к лидеру: sell val AUC=0.6673.

Buy target `buy_stop_broken_H6_off05_flag`:

- Первоначально buy-цели выглядели пустыми из-за бага загрузчика: Stage 5 всегда фильтровал строки по `sell_stop_broken_H6_off05_flag`.
- После исправления загрузки фильтр идёт по выбранной цели; buy-цель непустая: train rows=22745, positive_rate=0.3701, OHLC verification `PASS 50/50`.
- Buy-прогон был диагностическим: все 9 профилей рассмотрены как основные только для сравнения, автоматические пороги отключены.
- Лучший Transformer `all100_relative_price_time`: val AUC=0.6762, holdout AUC=0.6462.
- Лучший XGBoost `base_raw_plus_time`: val AUC=0.6894, holdout AUC=0.6552.
- Если применить sell-логику AUC-порога, buy-порог был бы 0.6994; разрыв лучшего Transformer = 0.0232.
- `all100_absolute_price_atr_scaled_time_asinh` снова рядом с лидером: buy val AUC=0.6752 против лидера 0.6762.

Общий вывод Stage 5.0b: Transformer не превзошёл XGBoost по AUC ни на sell, ни на buy. В нижней зоне риска (`lift_30`, меньше лучше) Transformer иногда лучше на `val_stop`, но перенос в holdout слабее: sell `0.5044 -> 0.6468`, buy `0.5112 -> 0.6217`. Следующий разумный шаг — не расширять сетку профилей, а оформить отдельный заранее зафиксированный прогон `all100_absolute_price_atr_scaled_time_asinh` по sell и buy с теми же строками для XGBoost и Transformer.

### Stage 5.0c: cross-target replication rerun (2026-06-22) — ❌ FAIL

Stage 5.0c — проверочный этап, повторная проверка гипотезы 5.0b. Один профиль `all100_absolute_price_atr_scaled_time_asinh`, две цели sell+buy, 5 seeds, XGBoost на тех же flattened признаках, 4 решающих заранее зафиксированных порога + `holdout_check` как предупреждение. Holdout не входил в решение.

Sell (`sell_stop_broken_H6_off05_flag`):
- Transformer median val AUC: 0.6643 (seeds: 0.6619–0.6673)
- XGBoost same-profile val AUC: 0.6723
- G1 AUC: FAIL — 0 из 5 seeds выше порога (xgb−0.005)
- G2 lift_30: FAIL — transformer 0.5570 vs xgb 0.5229 (меньше=лучше)
- G5 seed spread: PASS — 0.0054 (<0.03)
- Holdout check: OK — drop 0.024 (<0.05)

Buy (`buy_stop_broken_H6_off05_flag`):
- Transformer median val AUC: 0.6752 (seeds: 0.6704–0.6808)
- XGBoost same-profile val AUC: 0.6873
- G1 AUC: FAIL — 0 seeds выше порога
- G2 lift_30: FAIL — transformer 0.5423 vs xgb 0.5147
- G5 seed spread: PASS — 0.0104 (<0.03)
- Holdout check: OK — drop 0.028 (<0.05)

**overall_pass: FAIL.** Transformer систематически уступает XGBoost на одних и тех же признаках. Seed 42 результаты идентичны 5.0b (sell 0.6673, buy 0.6752) — воспроизводимость single-seed подтверждена. Seed spread узкий — результат стабилен, но стабильно слаб.

Transformer показывает классическое переобучение: seed 42 sell, val AUC достигает 0.6673 на epoch 9, затем падает до 0.6445 на epoch 17 при продолжающемся падении train loss. На 25k строках Transformer систематически переобучается.

Вывод: гипотеза 5.0b не воспроизвелась. Причины неудачи могут быть в признаках (слабый сигнал), в модели (переобучение), или в обоих. Текущий эксперимент не различает эти причины. Следующий шаг — диагностический скрининг (Stage 5.0d): XGBoost + Logistic на всех 9 профилях, без Transformer, с абляцией групп признаков.

### Stage 5.0d: диагностический скрининг профилей (2026-06-23) — ⚠️ h6_off05_target_exhausted

Stage 5.0d — поисковый скрининг: XGBoost (3 seeds) + Logistic Regression на всех 9 профилях из 5.0b × sell + buy, без Transformer. Абляция групп признаков (price / structure / ATR / time) для лучшего профиля по каждой цели.

**Sell (base val AUC = 0.6631):**
- Лучший: `all100_relative_price_time` delta +0.0111 (lift_pass OK, AUC_pass FAIL — порог 0.02)
- Все остальные дельты ≤ +0.0092 или отрицательные
- `nearest40_relative_price_no_time` AUC 0.5238 — практически случайно

**Buy (base val AUC = 0.6894):**
- Все 9 дельт ≤ −0.0006 — ни один профиль не превосходит base

**Абляция (лучший профиль по каждой цели):**
- `no_structure` обрушивает AUC: sell 0.674→0.534 (−0.14), buy 0.687→0.500 (−0.19) — структурные признаки (`direction`…`impulse`) главный носитель сигнала
- `no_price`, `no_atr` delta < 0.005 — ценовые и ATR-признаки почти не влияют
- `no_time` delta −0.04…−0.05 — время умеренно значимо

**XGBoost >> Logistic** (gap 0.04–0.05) — сигнал нелинейный, но слабый.

**Вердикт: `h6_off05_target_exhausted`** — ни один профиль не достиг порога +0.02 AUC над base на val 2021-2022.

**Ключевая оговорка:** вердикт основан на сравнении профилей на val 2021-2022. Базовая модель деградирует на holdout по годам (sell 2023=0.676 → 2026=0.556; buy 2023=0.695 → 2025=0.609), что согласуется с Stage 5.0 и Stage 4.7. Природа отрицательного результата не установлена: (H1) сигнал слабый/отсутствует, или (H2) сигнал затухает во времени. Stage 5.0f (диагностика стационарности) нужен для разделения этих гипотез перед сменой target или закрытием Fractal Stop.

### Stage 5.0e: проверка переобучения после провала (2026-06-23) — ⚠️ DIAGNOSTIC_ONLY

Stage 5.0e — узкая посмертная проверка внутри уже закрытой ветки `H6_off05`. Один профиль `all100_relative_price_time`, одна цель `sell_stop_broken_H6_off05_flag`, 2 конфигурации Transformer × 3 seeds. Цель — проверить, объясняет ли слишком большая модель часть провала 5.0c.

**XGBoost на тех же признаках:**
- XGBoost: val AUC `0.6742`, val lift_30 `0.5260`

**Transformer `current`:**
- median val AUC `0.6685`
- median lift_30 `0.5260`
- median overfit_drop_after_best `0.0170`

**Transformer `small_regularized`:**
- median val AUC `0.6657`
- median lift_30 `0.5663`
- median overfit_drop_after_best `0.0009`
- seed spread `0.0022`

**Вывод Stage 5.0e:**
- `overfit_hypothesis_supported = yes`
- `transformer_reopens_h6_off05 = no`

Меньшая модель почти убирает просадку `val_auc` после лучшей эпохи, но не улучшает итоговое качество относительно XGBoost. Ни один seed Transformer не прошёл сравнение с XGBoost на тех же признаках одновременно по `val_auc` и `val_lift_30`. Значит, переобучение было реальным, но не главным объяснением слабого результата Transformer.

### Stage 5.0f: диагностика устойчивости сигнала во времени (2026-06-24) — ⚠️ DIAGNOSTIC_ONLY

Stage 5.0f не открывал нового кандидата и не переоткрывал `H6_off05`. Он проверял, достаточно ли данных, чтобы честно сказать: сигнал распадается во времени (H2), или картина сложнее.

Протокол:

- 2 цели: `sell_stop_broken_H6_off05_flag`, `buy_stop_broken_H6_off05_flag`
- 4 набора признаков: `base_raw_plus_time`, `structure_only`, `time_only`, `all100_relative_price_time`
- 3 схемы годовых окон:
  - `rolling`: 8-летнее окно разработки = 7 лет `train_core` + 1 год `val_stop`
  - `fixed`: фиксированная база `2004..2019` + `val_stop=2020`
  - `anchored`: нарастающее окно от 2004 до `test_year-2`
- 3 seed
- всего `456` прогонов XGBoost
- decision years: `2023-2025`; `2026` — low_n disclosure (sell `n=316`, buy `n=293`)

Результаты:

- Для обеих целей `rolling` не дал ни одного решающего года, где его нижняя граница качества была бы выше верхней границы `fixed`. Более того, `fixed` последовательно численно превосходил `rolling` (sell 6/6 лет, buy 4/6 лет), что скорее противоречит H2 (temporal decay), чем поддерживает её.
- `time_only` деградирует сильнее фрактальных профилей при переходе от fixed к rolling (decision-флаг `False`); по абсолютному AUC стабильно ниже `structure_only` (sell +0.036…+0.071, buy +0.017…+0.050). Гипотеза "всё объясняется только календарём" не подтверждена.
- `structure_only` (фрактальные поля + clock, без price/ATR) остался близок к `base_raw_plus_time`; в 12 из 18 сравнений ≥ базы. Сигнал не сводится к одному `time_only`, но `structure_only` не является "чистой структурой без времени" — он сохраняет hour/dow.
- По buy виден монотонный нисходящий рисунок в `anchored` на 2023-2025, но Spearman на n=3 статистически неинформативен (`p=0.0` — артефакт t-аппроксимации scipy при `rho=±1.0`, истинный p≈0.33). На 7 точках (2019-2025) тренд исчезает для обеих целей.
- `all100_relative_price_time` стабильно рядом с базой (±0.01-0.02), подтверждает вывод 5.0d.
- Снижение anchored AUC конфаундировано: может объясняться как temporal decay, так и объективной сложностью test-лет. Поскольку `fixed` > `rolling`, второе объяснение более вероятно. Перекрёстная ссылка: Stage 4.7 также нашёл PF<1.0 на 2023-2026.

Итог Stage 5.0f:

- не доказан распад сигнала, который лечится более близким по времени обучением (H2 скорее опровергнута направлением fixed>rolling);
- не доказана и устойчивость сигнала;
- вердикт `temporal_decay` был структурно невозможен (требует `rho > 0`, обе цели имеют `rho ≤ 0`);
- природа отрицательного результата (H1 vs H2) остаётся неустановленной;
- без нового независимого периода `2026+` большой перебор по `H6_off05` не оправдан.

### Stage 5.1: структурная абляция фрактальных полей (2026-06-24) — ⚠️ DIAGNOSTIC_ONLY

Stage 5.1 не открывал нового кандидата и не выбирал торговое правило. Он декомпозировал `structure_full` на 9 отдельных структурных полей:

- `direction`
- `front`
- `back`
- `strong`
- `break`
- `reverse`
- `power`
- `count`
- `impulse`

Протокол:

- 2 цели: `sell_stop_broken_H6_off05_flag`, `buy_stop_broken_H6_off05_flag`
- 20 профилей: `time_only`, `structure_full`, 9 `drop_*`, 9 `add_*`
- 3 seed
- fixed split:
  - `train_core <= 2020`
  - `val_stop = 2021-2022`
  - `diagnostic_holdout = 2023-2025`
  - `low_n_disclosure = 2026`
- всего `120` прогонов XGBoost
- Stage 5.1 полностью исключает `price` и `ATR`; `time_only` содержит только 4 clock-признака

Результаты:

- `structure_full` уверенно выше `time_only` на обеих целях:
  - sell val AUC `0.6693` vs `0.6351`, holdout `0.6662` vs `0.6144`
  - buy val AUC `0.6879` vs `0.6418`, holdout `0.6610` vs `0.6252`
- Единственное поле с согласованным итогом на обеих целях: `back`
  - sell: `drop_back` ухудшает val AUC на `-0.0100`, `add_back` улучшает на `+0.0213`
  - buy: `drop_back` ухудшает val AUC на `-0.0209`, `add_back` улучшает на `+0.0359`
  - overall verdict: `likely_useful`
- Предметная интерпретация `back`: это `back_val`, сила тыловой границы фрактального уровня. Гипотеза: уровень с сильной тыловой границей труднее пробить сзади, поэтому поле может быть связано с устойчивостью stop-пробоя. Это объяснение правдоподобно, но не доказано.
- У `back` самый согласованный годовой рисунок: удаление ухудшает AUC на всех 5 годах `2021-2025` на обеих целях. По CI buy сильнее sell: buy drop CI `[-0.0317, -0.0101]`, sell drop CI `[-0.0228, +0.0009]`; sell держится на согласии 3/3 seed, а не на полностью отрицательном CI.
- `back` одиночно захватывает примерно 64% структурной премии на sell и 74% на buy, но не заменяет весь `structure_full`; прямой тест `time+back` vs `structure_full` не проводился.
- `impulse` выглядит потенциально интересным (`add_impulse` положителен на обеих целях), но не собирает достаточно согласованности и остаётся `mixed_or_unclear`: на sell holdout drop-signs `[+1, +1, -1]`, на buy CI пересекает 0 и `neg_seeds = 2`.
- Большинство полей не имеют самостоятельного сигнала над clock: только `back` и `impulse` дают положительный `add_val` на обеих целях. Остальные могут быть полезны только в контексте полного профиля или быть коррелированными дублями.
- Остальные поля (`direction`, `front`, `strong`, `break`, `reverse`, `power`, `count`) не дают согласованного рисунка
- Полей с `likely_noise` не найдено
- `direction` дал аномальный паттерн: удаление улучшает sell val AUC (`+0.0026`), но вредит на всех годах holdout. Это может быть связано с взаимодействием знака фрактала и стороны цели, но Stage 5.1 этого не проверял.
- Ранний `2026` не подтверждает сильный sell-сигнал: `structure_full` sell AUC `0.5597` при `n=316`, а `time_only` `0.5294`. На buy 2026 лучше (`0.6498` vs `0.5999`). Это low-N disclosure, не решающий вывод.

Итог Stage 5.1:

- Stage 5.1 показывает диагностическую прибавку структурных полей над clock-only baseline, но не доказывает чисто структурный сигнал без времени;
- внутри структуры самое сильное диагностическое поле — `back`;
- Stage 5.1 **не переоткрывает** `H6_off05` как кандидата;
- `2023-2025` здесь — только diagnostic disclosure, а не новый frozen test.

### Stage 5.1b: Up/Dn поля и baseline `clock + shift` (2026-06-25) — ⚠️ DIAGNOSTIC_ONLY

Stage 5.1b был узким уточнением Stage 5.1. Он добавил `shift` в baseline, чтобы проверить, не объяснялся ли сигнал структурных полей возрастом фрактала, и отдельно проверил 10 Up/Dn полей:

- `up_3`, `dn_3`
- `up_6`, `dn_6`
- `up_12`, `dn_12`
- `up_24`, `dn_24`
- `up_48`, `dn_48`

Протокол:

- 2 цели: `sell_stop_broken_H6_off05_flag`, `buy_stop_broken_H6_off05_flag`
- 43 профиля: `clock_shift`, `structure_full`, `updn_full`, `structure_plus_updn`, `back_impulse_combo`, 19 `drop_*`, 19 `add_*`
- 3 seed
- всего `258` прогонов XGBoost
- split повторяет Stage 5.1: `train_core=2004-2020`, `val_stop=2021-2022`, `diagnostic_holdout=2023-2025`, `low_n_disclosure=2026`
- Up/Dn preflight проверял монотонность на raw-shadow `MT/MQL4/Files/Nero.csv`, потому что labeled CSV уже нормализует пары `up_X/dn_X` отдельно по горизонту
- raw-shadow split совпал с модельным split; нарушений монотонности Up/Dn не найдено

Результаты:

- `updn_full` даёт слабую добавку над `clock_shift`: sell `+0.0048` AUC, buy `+0.0059`
- `structure_full` намного сильнее: sell `+0.0460`, buy `+0.0561` AUC над `clock_shift`
- `structure_plus_updn` не улучшает `structure_full` на validation: sell `-0.0017`, buy `-0.0021`
- `back` сохранил `overall_likely_useful`:
  - sell: drop `-0.0171`, add `+0.0408`
  - buy: drop `-0.0186`, add `+0.0575`
- `back_impulse_combo` почти догоняет `structure_full` на sell и превосходит его на buy, но это diagnostic control, не winner
- единственный частный Up/Dn-сигнал: `dn_24` получил `target_likely_useful` только на sell; общий verdict = `target_specific_signal`, но drop delta всего `-0.0030` и CI отсутствует
- `clock_shift` хуже Stage 5.1 `time_only` на обеих целях, поэтому add-one дельты Stage 5.1b считаются от более слабого baseline

Итог Stage 5.1b:

- вывод Stage 5.1 про `back` стал сильнее: он не исчез после добавления `shift`;
- Up/Dn не стоит включать в следующий стартовый профиль по умолчанию;
- модельные Up/Dn нормализованы per-pair; raw-shadow preflight не описывает их модельную шкалу;
- field verdicts слабее Stage 5.1 из-за отсутствующих delta CI;
- если делать ещё один шаг по `H6_off05`, он должен быть узким: `clock_shift`, `clock_shift+back`, `clock_shift+impulse`, `clock_shift+back+impulse`, `structure_full`, `structure_full_without_back`;
- Stage 5.1b **не переоткрывает** `H6_off05` как кандидата.

### Stage 5.2: регрессия времени до пробоя (2026-06-25) — ⚠️ DIAGNOSTIC_ONLY

Stage 5.2 проверил новую постановку той же ветки: предсказывать не бинарный пробой стопа, а время до пробоя (`bars_to_breach`).

Контракт цели:

- `bars_to_breach = 1..H` — первый бар пробоя;
- `bars_to_breach = H + 1` — пробоя не было в пределах горизонта;
- основной горизонт `H=6`, значит censored value = `7`;
- основные цели: `sell_bars_to_breach_H6_off05`, `buy_bars_to_breach_H6_off05`.

Протокол:

- 2 цели;
- 7 профилей: `time_only`, `clock_shift`, `clock_shift_back`, `clock_shift_impulse`, `clock_shift_back_impulse`, `structure_full`, `structure_full_without_back`;
- 3 seed;
- всего `42` XGBoost-регрессии;
- `2023-2025` только diagnostic holdout, не frozen test.

Результаты после bugfix/rerun:

- root cause старой аномалии: `reg:pseudohubererror` выдавал константу вне диапазона, clipping превращал все предсказания в `1.0`;
- objective заменён на `reg:squarederror`, полный rerun `42/42`;
- censoring gate прошёл: train censoring sell `0.6114`, buy `0.6299`;
- oracle gate теперь честно падает: `oracle_binary_pf = inf`, `pf_delta_vs_binary = None`, comparison невалиден;
- model gate провален на обеих целях только из-за MAE-improvement над constant baseline;
- лучший sell: `clock_shift_back`, val Spearman `0.3072`, val AUC `0.7005`, holdout Spearman `0.2942`, holdout AUC `0.6784`;
- лучший buy: `clock_shift_back_impulse`, val Spearman `0.3280`, val AUC `0.7071`, holdout Spearman `0.2660`, holdout AUC `0.6613`;
- MAE модели хуже constant baseline:
  - sell: model `1.6942` vs constant `1.4439`;
  - buy: model `1.6434` vs constant `1.4329`.

Итог Stage 5.2:

- идея времени до пробоя не закрыта; ранжирование есть;
- `back` снова главный компактный сигнал: `clock_shift_back` лучший на sell, `clock_shift_back_impulse` лучший на buy;
- обычная регрессия одного числа `bars_to_breach` не проходит candidate-gate, потому что censored value `7` делает constant baseline сильным по MAE;
- следующий шаг, если продолжать, — дискретная/цензурированная постановка (`breach_after_k`, `survives_at_least_k`, ordinal buckets), а не новый широкий перебор по `H6_off05`.

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
16. Stage 4.7 показал, что расширение обучения до 2022, rolling/anchored walk-forward и warm-start не спасают 2023-2026. Проблема не в объёме данных.
17. Stage 5.0 полноразмерный Transformer (d_model=64, 40 эпох) не бьёт XGBoost на holdout 2023-2026: AUC 0.6018 vs 0.6524, lift_30 0.766 vs 0.620 (меньше = лучше). **Методический risk:** признаки не масштабированы под нейросеть (цена в сотнях/тысячах, остальные ~0..1) — вывод относится к текущей реализации и нормализации.
18. Stage 5.0a показал, что повторный прогон Transformer ещё имеет смысл, но только после проверки распределений признаков по A7, без динамического выбора профилей по holdout.
19. Stage 5.0a A7-аудит изменил вывод по абсолютной цене: raw absolute price кодировал эпоху, но `price/ATR` и `asinh(price/ATR)` методически чисты и не имеют длинных хвостов после нормализации.
20. Stage 5.0b показал, что Transformer с `asinh` не превзошёл XGBoost по AUC ни на sell, ни на buy. Buy-цель оказалась жизнеспособной после исправления загрузки, но buy-прогон был диагностическим.
21. `all100_absolute_price_atr_scaled_time_asinh` повторно оказался рядом с лидером на sell и buy; это главный кандидат для следующего заранее зафиксированного диагностического прогона, но не winner Stage 5.0b.
22. **Stage 5.0c: гипотеза 5.0b не воспроизвелась.** Transformer на одних и тех же признаках систематически уступает XGBoost по AUC и lift_30 на обеих целях. 0 из 5 seeds выше порога. Seed spread узкий (0.005–0.010) — результат стабилен, но стабильно слаб.
23. **Transformer переобучается на 25k строках:** val AUC падает после epoch 9 (0.6673 → 0.6445 на seed 42 sell). Причины неудачи не различены: слабый сигнал в признаках, переобучение модели, или обе.
24. **XGBoost same-profile добавляет ~0.009 AUC на sell** (0.6723 vs base 0.6631), но не на buy (0.6873 vs base 0.6894). Профиль помогает только на sell — и то в пределах шума.
25. **6 последовательных этапов Fractal Stop провалились как торговые или модельные кандидаты.** Breach-сигнал статистически подтверждён, но недостаточен для устойчивого ML-превосходства ни в табличной, ни в sequence-реализации.
26. **Stage 5.0d: скрининг всех 9 профилей.** XGBoost (3 seeds) + Logistic Regression на всех профилях 5.0b × sell + buy. **Ни один профиль не достиг порога +0.02 AUC** над `base_raw_plus_time` на val 2021-2022. Лучший: sell `all100_relative_price_time` (delta +0.0111, lift_pass OK). Buy: все дельты ≤ 0. Абляция: structure-признаки критичны (AUC −0.14/−0.19 при удалении), price/ATR почти не влияют. XGBoost >> Logistic (gap 0.04–0.05) — сигнал нелинейный, но слабый. Вердикт `h6_off05_target_exhausted` — разные способы кодирования фракталов (relative price, absolute price/ATR, corridor, nearest40) не превосходят стандартное base-кодирование. Базовый профиль сам содержит 9 структурных фрактальных признаков — вывод относится к способам кодирования, не к отсутствию фрактального сигнала.

27. **Сигнал базовой модели деградирует на holdout по годам.** `base_raw_plus_time` yearly AUC: sell 2023=0.676 → 2026=0.556; buy 2023=0.695 → 2025=0.609. Согласуется с Stage 5.0 (0.646→0.514) и Stage 4.7 walk-forward (PF<1.0 на 2023-2026 во всех режимах). Вердикт 5.0d основан на val 2021-2022; темпоральная нестационарность не проверялась и не учитывается в вердикте.

28. **Природа отрицательного результата не установлена.** Вердикт `h6_off05_target_exhausted` не различает: (H1) сигнал слабый/отсутствует, или (H2) сигнал затухает во времени и сравнение на одном val-окне локально. Stage 5.0f добавил важное уточнение: H2 скорее опровергнута направлением `fixed` > `rolling` (старые данные не вредят), но H1 тоже не подтверждена (`all_profiles_low_auc = False` — некоторые AUC выше 0.68). Жёсткого вывода не получилось ни в пользу H1, ни в пользу H2.

29. **Stage 5.0e: меньший Transformer уменьшает переобучение, но не меняет решение.** `small_regularized` снизил median `overfit_drop_after_best` с `0.0170` до `0.0009`, но остался хуже XGBoost на тех же признаках по `val_auc` (`0.6657` vs `0.6742`) и по `lift_30` (`0.5663` vs `0.5260`, меньше лучше). Значит, переобучение — часть проблемы, но не её корень.

30. **Ветка `H6_off05` закрыта не только как поисковая, но и как гипотеза про размер модели.** После 5.0e нет оснований продолжать настройку Transformer на той же цели и том же профиле. Следующий осмысленный шаг — новая цель, новые признаки или объяснение, почему табличное представление лучше последовательной модели на тех же данных.
31. **Stage 5.0f: H2 скорее опровергнута, H1 не подтверждена, итог неопределённый.** `fixed` последовательно численно превосходил `rolling` (sell 6/6, buy 4/6 лет) — старые данные не вредят, что противоречит temporal decay (H2). `time_only` деградирует сильнее фракталов и ниже по AUC (structure − time_only: sell +0.036…+0.071, buy +0.017…+0.050) — календарь не объясняет всё. `structure_only` (фракталы + clock, без price/ATR) в 12/18 ≥ базы. Spearman на n=3 неинформативен (`p=0.0` для buy — артефакт, истинный p≈0.33); на 7 точках тренд исчезает. Вердикт `temporal_decay` был структурно невозможен (требует `rho > 0`). Без нового периода `2026+` большой перебор по `H6_off05` не оправдан.
32. **Stage 5.1: внутри structural-профиля устойчиво выделяется только `back`.** `structure_full` уверенно превосходит `time_only` на обеих целях, значит структурные поля дают диагностическую прибавку над clock-only. При этом только `back` (`back_val`, сила тыловой границы уровня) даёт согласованный рисунок `drop-one hurts / add-one helps` на sell и buy и получает `likely_useful`. Удаление `back` ухудшает AUC на всех 5 годах `2021-2025` на обеих целях. Но `back` не заменяет полный профиль: одиночно он захватывает около 64% структурной премии на sell и 74% на buy. `impulse` остаётся вторым по интересу, но не проходит `likely_useful`. Полей `likely_noise` не найдено. Это узкий диагностический вывод, а не новое открытие кандидата.
33. **Stage 5.1b: `shift` не объяснил сигнал `back`, а Up/Dn не улучшили структуру.** После усиления baseline до `clock + shift` поле `back` осталось `overall_likely_useful`: sell add `+0.0408`, buy add `+0.0575`; drop ухудшает обе цели. Группа Up/Dn даёт только слабую добавку над baseline (`+0.0048/+0.0059` AUC), тогда как `structure_full` даёт `+0.0460/+0.0561`. `structure_plus_updn` хуже `structure_full` на validation (`-0.0017/-0.0021`), поэтому Up/Dn не являются обязательным стартовым профилем для следующего шага. Единственный частный след — `dn_24` на sell, но это слабый `target_specific_signal` после множественных сравнений: drop delta `-0.0030`, CI отсутствует. Stage 5.1b add-one дельты нужно читать осторожно, потому что `clock_shift` оказался хуже Stage 5.1 `time_only`.
34. **Stage 5.2: time-to-breach даёт ранжирование, но не candidate.** После bugfix `reg:squarederror` лучший sell-профиль `clock_shift_back` даёт val Spearman `0.3072`, AUC `0.7005`, holdout Spearman `0.2942`; лучший buy `clock_shift_back_impulse` даёт val Spearman `0.3280`, AUC `0.7071`, holdout Spearman `0.2660`. Это подтверждает, что `back` связан не только с бинарным пробоем, но и с временем жизни уровня. Однако MAE хуже constant baseline (`7`) на обеих целях, а oracle comparison невалиден (`oracle_binary_pf = inf`), поэтому Stage 5.2 остаётся `DIAGNOSTIC_ONLY`. Следующий шаг — censored/ordinal formulation, не обычная регрессия.
35. **Stage 5.3: дискретизация time-to-breach нашла полезную target family, но не кандидата.** Лучший main target на обеих сторонах — `fast`: sell `sell_fast / clock_shift_back` val AUC `0.6967`, delta vs same-profile binary baseline `+0.0279`, per-seed delta проходит порог `≥0.02` в `3/3` seed; buy `buy_fast / clock_shift_back_impulse` val AUC `0.7127`, delta `+0.0199`, но порог `≥0.02` проходит только `1/3` seed. Sell проходит target-reformulation gate, buy остаётся пограничным и держится на seed 42. Main comparisons для gate — `12` уникальных side/target comparisons, потому что `breach_after_k2` и `medium` тождественны. Control `survives_at_least_k` показывает высокие AUC/PR AUC, но не может быть winner-ом: censored rows становятся positive и модель может учить "не пробито", а не время жизни уровня.

36. **Stage 5.4: price/ATR не объяснил `fast`-сигнал.** Проверка fixed target `fast` на 12 профилях × 2 стороны × 3 seeds показала: primary `price_coord_atr` даёт только +0.0066 AUC на sell и +0.0014 на buy, оба 0/3 seeds по порогу `≥0.02`. A7 preflight чистый по blocker-ошибкам: все 24 комбинации WARNING из-за ожидаемого `ZERO_GT95`, без `TAIL_GT10/TAIL_GT20`, `REGIME_SHIFT` и сильной корреляции `price_coord_atr` с `back`. Диагностические ATR/Up-Dn профили местами выше primary по median AUC, но не проходят per-seed gate и не могут продвинуть статус. Вывод: **REJECT_PRICE_COORD**; расширять price-поиск вокруг `fast` не нужно.

**Все этапы (Stage 2→5.4) отклонены как торговые кандидаты.** Табличные модели достигли потолка, Transformer не дал устойчивого улучшения, а диагностика устойчивости сигнала во времени не дала жёсткого решения. Stage 5.1/5.1b уточнили носитель структурного сигнала, Stage 5.2/5.3 проверили time-to-breach постановки и нашли полезную дискретную цель `fast`, но Stage 5.4 не нашёл признаков, которые усиливают этот след до кандидата. Ветка остаётся диагностической.

## Открытые вопросы

- ~~Проверить `all100_absolute_price_atr_scaled_time_asinh` как заранее выбранный основной профиль в отдельном Stage 5.0c-прогоне по sell и buy~~ — Stage 5.0c завершён: FAIL.
- ~~Какие фрактальные профили и группы признаков вообще несут сигнал сверх raw features — Stage 5.0d~~ — Stage 5.0d завершён: h6_off05_target_exhausted. Разные кодирования не превосходят base; structure-признаки критичны, price/ATR не влияют.
- ~~Был ли провал Transformer в 5.0c просто следствием слишком большой модели?~~ — Stage 5.0e завершён: частично да, переобучение было, но это не меняет итогового проигрыша XGBoost.
- **Нужен ли отдельный подтверждающий цикл на новом периоде `2026+`?** Stage 5.0f не дал жёсткого ответа, но сжёг `2023-2025` для диагностического решения. H2 скорее опровергнута (fixed > rolling), H1 не подтверждена (AUC не uniformly слабый). Без нового периода большой перебор по `H6_off05` не оправдан; максимум — узкий разбор структурных групп как диагностика без статуса кандидата.
- **Заслуживает ли `back+impulse` отдельного узкого follow-up?** Stage 5.1b показал, что `back_impulse_combo` почти догоняет `structure_full` на sell и превосходит его на buy, но это diagnostic control, а не чистый кандидат. Если по `H6_off05` вообще делать ещё один диагностический шаг, он должен быть узким и заранее ограниченным: `clock_shift`, `clock_shift+back`, `clock_shift+impulse`, `clock_shift+back+impulse`, `structure_full`, `structure_full_without_back`.
- **Что делать с Up/Dn?** Stage 5.1b не поддержал включение всей группы по умолчанию. `dn_24` на sell — только частный след после множественных сравнений; отдельная проверка имеет смысл только если будет новая постановка, где sell-only логика заранее обоснована.
- ~~Почему Stage 5.2 дал одинаковые нулевые метрики для всех профилей?~~ Root cause найден: `reg:pseudohubererror` + clipping; rerun выполнен.
- ~~Как лучше поставить time-to-breach после rerun?~~ Stage 5.3 показал, что bucket `fast` — лучший next target family. `survives_at_least_k` остаётся control-only, `breach_after_k5` слишком sparse.
- ~~Поможет ли price/ATR ablation усилить Stage 5.3 `fast`?~~ Stage 5.4 завершён: `price_coord_atr` rejected, `price_atr_scaled` не добавил устойчивого сигнала, расширение price-поиска не требуется.
- **Является ли слабый sell 2026 ранним признаком ослабления?** `structure_full` sell AUC `0.5597` при `n=316` не используется для verdict, но это риск для будущего подтверждения на `2026+`.
- **Противоречие с Stage 5.0-prep:** prep показывал `time_only` AUC=0.6286 > `no_time` AUC=0.6113. В 5.0d `no_structure` (price+ATR+time, без 9 структурных) = 0.534 — ниже `time_only` на 0.094. Причина не разобрана: разные transforms (asinh vs current), или price-токены шумят.
- Почему XGBoost извлекает умеренный сигнал из flattened-представления, а Transformer на тех же данных — нет.
- Может ли другая постановка fav/exit-таргета снизить шум сильнее, чем простая замена RF-fav на XGBoost-fav.
- Работает ли выбор стороны/режима лучше, чем изолированные BUY/SELL и combined H6/H12.
- Помогут ли новые признаки (спред, волатильность, корреляции) улучшить fav-регрессию.
- Работает ли концепт на других активах или таймфреймах.
- Стоит ли окончательно закрыть Fractal Stop ветку и вернуться к основному направлению (regression_updn, triple barrier), или всё же проводить ещё один подтверждающий цикл на новом периоде.

## Источники

- [2026-06-10-fractal-stop-breach-stage1.md](../../docs/reports/2026-06-10-fractal-stop-breach-stage1.md) — Stage 1 report (AUC, lift, frozen test)
- [2026-06-10-fractal-stop-fav-stage2.md](../../docs/reports/2026-06-10-fractal-stop-fav-stage2.md) — Stage 2 report (PF, grid search, frozen test, FAIL verdict)
- [2026-06-10-feature-profiles-stage3.md](../../docs/reports/2026-06-10-feature-profiles-stage3.md) — Stage 3.x report (feature profiles, Stage 3.1 ablation, Stage 3.2 XGBoost)
- [2026-06-11-stage4-trade-xgboost.md](../../docs/reports/2026-06-11-stage4-trade-xgboost.md) — Stage 4/4.1/4.2 report (XGBoost breach + RF fav trading layer, controls, diagnostic corrected recalc, FAIL verdict)
- [2026-06-15-stage4_3-diagnostics.md](../../docs/reports/2026-06-15-stage4_3-diagnostics.md) — Stage 4.3 diagnostic report (post-mortem loss attribution, fav/breach diagnostics, oracle-deviation regimes)
- [2026-06-14-stage4-deep-diagnostics.md](../../docs/reports/2026-06-14-stage4-deep-diagnostics.md) — Stage 4 deep diagnostics: Partial Oracle, improvement scans, trailing stop
- [2026-06-15-stage4_4-micro-check.md](../../docs/reports/2026-06-15-stage4_4-micro-check.md) — Stage 4.4 micro-check before Transformer: fixed TP, breach-only, fav-filter isolation
- [2026-06-15-stage5-prep-diagnostics.md](../../docs/reports/2026-06-15-stage5-prep-diagnostics.md) — Stage 5.0-prep: feature ablation, calendar risk, AUC→PF sensitivity
- [2026-06-15-stage4_5-exit-mechanics.md](../../docs/reports/2026-06-15-stage4_5-exit-mechanics.md) — Stage 4.5 exit mechanics (trailing/breakeven/partial)
- [2026-06-15-stage4_6-clean-candidate-cycle.md](../../docs/reports/2026-06-15-stage4_6-clean-candidate-cycle.md) — Stage 4.6 clean candidate-cycle (val_select 2019-2022, val_eval 2023-2026)
- [2026-06-15-walk-forward-diagnostics.md](../../docs/reports/2026-06-15-walk-forward-diagnostics.md) — Stage 4.7 walk-forward diagnostics: expanding/anchored/rolling/warm-start
- [2026-06-17-stage5-transformer-breach.md](../../docs/reports/2026-06-17-stage5-transformer-breach.md) — Stage 5.0 Transformer holdout (5 профилей, FAIL verdict)
- [2026-06-18-stage5_0a-feature-preflight.md](../../docs/reports/2026-06-18-stage5_0a-feature-preflight.md) — Stage 5.0a preflight (contracts, normalization audit, relative-price vs absolute-price, corridor truncation)
- [2026-06-20-stage5_0a-feature-distribution-audit.md](../../docs/reports/2026-06-20-stage5_0a-feature-distribution-audit.md) — Stage 5.0a A7-аудит распределения признаков, `asinh`/`piecewise_tail`, `price/ATR`
- [2026-06-21-stage5_0b-asinh-rerun.md](../../docs/reports/2026-06-21-stage5_0b-asinh-rerun.md) — Stage 5.0b asinh Transformer rerun, sell/buy, XGBoost comparison, buy loader fix
- [2026-06-22-stage5_0c-cross-target-rerun.md](../../docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md) — Stage 5.0c multi-seed replication test, FAIL verdict, Transformer переобучение
- [2026-06-23-stage5_0d-diagnostic-screening.md](../../docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md) — Stage 5.0d XGBoost + Logistic скрининг 9 профилей, абляция групп, вердикт: h6_off05_target_exhausted
- [2026-06-23-stage5_0e-small-transformer-check.md](../../docs/reports/2026-06-23-stage5_0e-small-transformer-check.md) — Stage 5.0e: малый Transformer уменьшает признаки переобучения, но не открывает ветку заново
- [2026-06-24-stage5_0f-signal-stationarity.md](../../docs/reports/2026-06-24-stage5_0f-signal-stationarity.md) — Stage 5.0f: диагностика устойчивости сигнала во времени, итог неопределённый
- [2026-06-24-stage5_1-structural-field-ablation.md](../../docs/reports/2026-06-24-stage5_1-structural-field-ablation.md) — Stage 5.1: structural field ablation, `back` = единственное `likely_useful` поле, `impulse` = второй интересный, но не подтверждённый след
- [2026-06-25-stage5_1b-updn-field-ablation.md](../../docs/reports/2026-06-25-stage5_1b-updn-field-ablation.md) — Stage 5.1b: Up/Dn field ablation с baseline `clock + shift`; `back` остаётся устойчивым, Up/Dn не улучшают `structure_full`
- [2026-06-25-stage5_2-time-to-breach-regression.md](../../docs/reports/2026-06-25-stage5_2-time-to-breach-regression.md) — Stage 5.2: регрессия времени до пробоя после bugfix/rerun; ранжирование есть, лучший сигнал снова вокруг `back`, но candidate-gate не пройден
- [2026-06-26-stage5_3-time-to-breach-target-reformulation.md](../../docs/reports/2026-06-26-stage5_3-time-to-breach-target-reformulation.md) — Stage 5.3: дискретная target reformulation; `fast` bucket найден как лучшая target family, controls раскрыты отдельно, статус остаётся диагностическим
- [2026-06-29-stage5_4-fast-price-atr-ablation.md](../../docs/reports/2026-06-29-stage5_4-fast-price-atr-ablation.md) — Stage 5.4: price/ATR ablation вокруг fixed `fast`; `price_coord_atr` rejected, buy остаётся disclosure-only
