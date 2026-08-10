# Ретроспектива проекта SoSimple

> Период: апрель 2026 -- август 2026
> Дата формирования: август 2026
> Порог успеха: PF >= 1.3 на out-of-sample с учётом спреда и проскальзываний,
> подтверждённый bootstrap CI (нижняя граница > 1.0)

---

## 1. Вердикт по проекту

Порог успеха **не достигнут**. Ни одна из исследованных систем не показала
устойчивый PF >= 1.3 с нижней границей bootstrap CI > 1.0 на строгом
out-of-sample периоде с полным учётом транзакционных издержек. Главная
причина -- отсутствие переносимого directional-сигнала: фрактальные признаки
предсказывают амплитуду движения (amplitude), но не его направление. Все
системы с высоким PF на исторических данных либо опирались на малые выборки
(44--96 сделок), либо теряли прибыльность при переходе к forward-данным,
смене провайдера или cross-instrument переносе. Наиболее сильная линия
(`entry_path_v1_quantile`, PF=8.18 на 48 сделках test) остаётся
неподтверждённой на strictly-forward данных -- scaffold готов, но самого
prediction CSV после production decision пока нет.

---

## 2. Направления исследований

### 2.1 MT5 execution loop

**Цель:** перенести диагностический execution-контур с MT4 на MT5 Strategy
Tester для независимой проверки кандидатов.

**Гипотеза:** MT5 tester даст воспроизводимый execution-контур, способный
подтвердить или опровергнуть PF frozen-кандидатов.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Feasibility + runbook (07-29) | DIAGNOSTIC_ONLY | Инфраструктура готова |
| Single-rule diagnostic run (07-30) | DIAGNOSTIC_ONLY | Lifecycle неполный |
| OnTradeTransaction lifecycle (07-31) | PASS | 269 positions, UNEXPLAINED=0 |
| Nero parity (07-31) | PASS | match rate 99.05%, direction 99.24% |
| Batch selection 32 runs (07-31) | BATCH_NO_WINNER | 11 eligible, best PF=1.23, BS_p05=0.89 |
| Execution hygiene (08-01) | PARTIAL | 1879 error rows classified |
| Timing contract (08-01) | PASS | 32/32 signal files, 0 violations |
| Multi-position closeout (08-03) | DIAGNOSTIC_ONLY | max=1 parity 32/32, max=64 ~9.6x placements |

**Итог:** MT5-контур построен и работает для диагностики, но batch из 32
кандидатов не дал ни одного с BS_p05 > 1.0. Fill-rate probe показал, что
99.2% OPEN_FAILED -- это single-position policy, а не broker no-fill.
Основная проблема -- малое число сделок на кандидата (median fill_rate=0.094).

### 2.2 Entry-based signal search

**Цель:** проверить, можно ли предсказать направление и амплитуду движения
от точки входа на следующем баре (entry-based next open).

**Гипотеза:** табличные модели достаточной мощности извлекут directional
сигнал из entry-based постановки.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Next open closeout (07-04) | PIVOT | direction слаб, amplitude сильнее |
| Powerful tabular (07-06) | PIVOT_AMPLITUDE | direction Spearman val_eval=-0.001; amplitude H3 Spearman 0.34->0.44 |
| Movement filter design (07-07) | RESEARCH_ONLY | Фильтр "есть/нет движение" |
| Movement filter freeze (07-08) | FROZEN | Заморожен для следующего плана |
| Fractal selection ablation (07-03) | DIAGNOSTIC_ONLY | Амплитуда устойчивее направления |
| Amplitude movement regime (07-07) | DIAGNOSTIC_ONLY | Amplitude trace подтверждён |
| Sequence transformer (07-07) | DIAGNOSTIC_ONLY | Последовательное представление |

**Итог:** Direction-постановка в entry-based контуре стабильно проваливается
на всех моделях (XGBoost, LightGBM, CatBoost, Extra Trees, Hist GBM).
Amplitude-сигнал (предсказание величины движения) устойчив: Spearman 0.34--0.45
на H3. Но перевод amplitude в торговое правило не выполнен.

### 2.3 Direction prediction

**Цель:** построить модель, предсказывающую BUY/SELL направление
непосредственно из фрактальных признаков.

**Гипотеза:** binary BUY/SELL классификатор на фрактальных признаках даст
PF > 1.3 на OOS.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Direct Direction Improvement (05-15) | DIAGNOSTIC | Binary RF: test PF=1.226, BUY PF=1.904, SELL PF=0.618 |
| Chain Audit (05-18) | FAIL | 6 ошибок в chain: нормализация, единицы, targets |
| Rebuild (05-21) | FAIL | Test PF=0.99, BUY win rate=50.5% (случайный) |
| Transformer Direction (05-21) | FAIL | Trail PF=2.41 на 58 сделках, 0.6% utilisation; SeqPF невалидна |

**Итог:** Направление закрыто. Фрактальные признаки не несут
direction-сигнала. Test win rate 50.5% неотличим от случайного. SeqPF
признан невалидной метрикой (shuffle-тест: разброс 0.68--4728 при PF=1.10).

### 2.4 Regression Up/Dn movement

**Цель:** проверить, предсказывают ли top-level `up_*/dn_*` чистую основу
для регрессионной постановки без привязки к breach/TP/SL.

**Гипотеза:** регрессия на будущие величины favorable/adverse movement
даст устойчивый сигнал для торгового решения.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Target Foundation (06-30) | DIAGNOSTIC_ONLY | structure_full H3: Spearman 0.76--0.80, improvement 0.47 |
| Ratio Audit (07-01) | DIAGNOSTIC_ONLY | log_ratio подтверждён |
| Already Moved Audit (07-02) | DIAGNOSTIC_ONLY | Часть сигнала -- уже произошедшее движение |
| Price Feature Matrix (07-02) | DIAGNOSTIC_ONLY | Цена входа влияет на target |

**Итог:** Target foundation подтверждён для коротких горизонтов (H3/H6),
сигнал не артефакт одной модели (Ridge тоже работает). Но часть сигнала
объясняется движением, уже произошедшим до входа. Перевод в торговое
правило не выполнен. Статус: DIAGNOSTIC_ONLY.

### 2.5 Fractal stop breach prediction

**Цель:** проверить, предсказывают ли фрактальные признаки пробой уровня
fractal0 и последующий благоприятный ход цены.

**Гипотеза:** цепочка breach -> fav -> trade даст устойчивый PF > 1.3.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Stage 1: Breach (06-10) | PASS (диагност.) | Пробой предсказывается |
| Stage 2: Fav (06-10) | FAIL | PF < 1.0 на canonical spread |
| Stage 3: Time-to-breach regression (06-25) | DIAGNOSTIC_ONLY | Время до пробоя |
| Stage 4: Trade XGBoost (06-11) | FAIL | val_eval PF=0.897 |
| Stage 5: Transformer breach (06-17) | DIAGNOSTIC_ONLY | Transformer не дал устойчивого улучшения |
| Walk-forward (06-15) | FAIL | Expanding Window PF=0.84--0.92 на 2023-2026 |

**Итог:** Breach предсказывается, но торговый слой (fav + trade) не работает.
Walk-forward показал структурный перелом 2022/2023: модель прибыльна на
2017--2022 (PF=1.42--1.91), убыточна на 2023-2026 (PF=0.73--0.90).

### 2.6 Entry path and quantile selection

**Цель:** построить слой "торговать / не торговать" поверх regression_updn
базы, используя quantile-головы для отбора лучших входов.

**Гипотеза:** quantile-layer (ret_24_q10, ret_24_q90) поверх entry_path_v1
даст устойчивый PF > 2.0.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Baseline (04-08) | PASS | ret_pearson_r=0.245 |
| Loss Weighting (04-09) | PASS | Вес 5.0: test PF=4.29, 44 сделки |
| Trade Filter (04-09) | PASS | Filter A @ 7.5%: test PF=4.29, 72.73% WR |
| MT4 Winner (04-09) | PASS | MT4: 22 сделки, PF=8.47 |
| Quantile Layer (04-10) | PASS | test: 24 сделки, PF=inf |
| Multi-seed Robustness (04-11) | PASS | 5/5 seeds, same rule, median PF=inf |
| Status Decision (04-12) | PASS | N=48, PF=8.18, MT4 parity 20/20 |
| MT4 Parity (04-12) | PASS | 20/20 сделок, net=4477, PF=11.91 |
| Forward Validation (04-13) | WATCH | no_forward_data, 0 trades |
| Cross-Instrument (04-24) | MIXED | XAGUSD supported, EURUSD/GBPUSD failed |

**Итог:** Сильнейшая линия проекта. PF=8.18 на 48 сделках test, подтверждён
MT4 parity (20/20, PF=11.91 в деньгах). Multi-seed устойчив. Но: (1) малая
выборка, (2) forward validation не выполнен (нет данных), (3) cross-instrument
перенос ограничен (EURUSD/GBPUSD провалены).

### 2.7 Signal quality and path atlas

**Цель:** понять постсигнальную геометрию цены и найти фильтры качества
сигнала.

**Гипотеза:** signal quality filter по `fav_3_vs_12` отберёт прибыльные
сигналы.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Variant 2 (04-01) | DIAGNOSTIC | PF_12=1.95, BUY>SELL |
| Variant 3 (04-02) | DIAGNOSTIC | Pullback улучшает, но и отрицательные контроли |
| Atlas Readout (04-04) | PASS | Медиана = монетка, двумодальная структура |
| Quality Filter (04-04) | PASS | fav_3_vs_12 <= 0.653, PF=1.78 на 84 holdout |
| Archetype Bridge (04-04) | PASS | Единственный validated фильтр |
| Fav Standalone (04-13) | FAIL | threshold не найден, PF=0.14--0.31 |

**Итог:** Парадигмальный сдвиг: "слабый drift" -> "монетка на медиане,
двумодальная структура". Задача переформулирована от "как войти" к "какие
сигналы торговать". `fav_3_vs_12` полезен как вспомогательный фактор, но
не как самостоятельная система.

### 2.8 Exit mechanics and take/skip validation

**Цель:** проверить, даёт ли бинарное решение take/skip поверх trailing-stop
логики устойчивый PF > 1.3.

**Гипотеза:** модель, решающая "брать ли вход при trailing-stop", даст
более устойчивый результат, чем regression/quantile.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Take/Skip v1 Matrix (04-17) | FAIL | Все reject, PF < 1.0 |
| Take/Skip v2 Scaffold (04-17) | PASS | Validation PF=6.39, 24 сделки |
| Frequency Follow-up (04-18) | PASS | quality: test PF=39.74, 41 сделок |
| Anchor Expansion (04-18) | PASS | frequency: test PF=7.17, 96 сделок |
| Sweet Spot 17% (04-18) | PASS | 16.4 trades/yr, PF=13.12, neg_years=0 |
| MT4 Trailing Execution (04-18) | PASS | TrailATR=8, TP=0: PF=3.77, 56 сделок |
| Execution Policy v2 (04-19) | PASS | quality MT4: PF=51.95, 20 сделок |
| lib_PIC Selection (04-20) | DIAGNOSTIC | Внешний фильтр не улучшил quality |
| lib_PIC Feature Training (04-20) | FAIL | 9/9 reject, 0 rows с PF>1 при >=6 trades/yr |
| Original Contour Ablation (04-20) | PASS | +path: 10.2 trades/yr, PF=38.78 |
| MT4 Confirmation (04-22) | PASS | 29 сделок, PF=23.79 |

**Итог:** Вторая по силе линия. Take/skip v2 дал несколько MT4-подтверждённых
режимов: quality (PF=39.74--51.95), frequency (PF=3.77--7.18),
original_plus_path (PF=23.79--38.78). Все -- на малых выборках (20--96
сделок). Bootstrap CI не построен для MT4-режимов.

### 2.9 Triple barrier foundation

**Цель:** построить TB-схему вне MT4 с isotonic calibration и проверить
на test.

**Гипотеза:** TB с first-touch labeling даст устойчивый PF > 1.3.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Hardening (04-08) | PASS | Test PF=1.11, 253 сделки |
| Runtime Verdict (04-08) | PASS | MT4 PF=1.27, SL/TP match 93.8% |
| MT4 Verdict (04-12) | FAIL | Gate: PF=1.28 < 2.0, 2 negative years |

**Итог:** Закрыто. TB-схема показала regime shift между validation (все
4 года положительные) и test (2023 PF=0.55, 2026 PF=0.00). Gate провален:
PF=1.28 < 2.0, negative_year_slices=2.

### 2.10 Fixed-11 frozen rules validation

**Цель:** проверить 11 frozen normalized rich-entry правил на locked_test
периоде 2022-12 -- 2026-06.

**Гипотеза:** frozen rules покажут PF > 1.0 с BS_p05 > 1.0 на locked_test.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Stop grid M5 winner (07-21) | RESEARCH_ONLY | PF=2.79, BS_p05=2.51 на val_eval |
| Entry quality filter (07-21) | FAIL | val_eval PF=1.95, BS_p05=0.97 |
| Rich entry quality (07-21) | RESEARCH_HINT | val_eval PF=4.03, BS_p05=3.40 |
| Normalized rerun (07-22) | RESEARCH_HINT | Winner: time_only |
| Internal closure rerun (07-23) | RESEARCH_ONLY | Multiseed, stress cost |
| Leaderboard closure (07-23) | RESEARCH_ONLY | 11 fixed rules |
| Locked test (07-24) | candidate_check_required | 11 rules, сильные PF/BS |
| Current history rerun (07-29) | FAIL | Chronology fix уничтожил edge: PF max=0.94 |
| MT4 parity (07-27) | FAIL | Fill-chronology audit нашёл ошибку |

**Итог:** Locked test дал сильные числа (PF/BS), но subsequent chronology-fix
(исправление Python execution contract) уничтожил edge: PF max=0.94,
kept_candidates=0. Positive locked-test chain invalidated.

### 2.11 Early regression foundation

**Цель:** первая рабочая ML-система на regression_updn target с exit-слоем.

**Гипотеза:** regression_updn + timeout exit даст PF > 1.3 на OOS.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Regression Up/Dn baseline | PASS (истор.) | PF~1.05 OOS |
| Exit Policy Research (04-08) | FAIL | timeout_only winner, PF=1.17, нет uplift |
| Outcome-Aligned (04-08) | FAIL | Ни одно семейство не прошло validation |

**Итог:** Production baseline PF~1.05 -- ниже порога. Exit layer не дал
uplift. Outcome-aligned retraining провалился из-за close-at-12h labels,
не повторяющих реальную execution.

---

## 3. Что работает

### 3.1 Quantile-layer entry selection

- **Метрика до:** entry_path_v1 baseline test PF=4.29, 44 сделки
- **Метрика после:** quantile test PF=8.18, 48 сделок, win_rate=0.81
- **Размер выборки:** 48 сделок test, 5 seeds (все прошли)
- **Вердикт:** PASS на frozen test; forward validation не выполнен
- **MT4 подтверждение:** 20/20 сделок совпадают, PF=11.91 в деньгах

### 3.2 Take/Skip v2 quality-first

- **Метрика до:** take/skip v1 matrix -- все reject, PF < 1.0
- **Метрика после:** quality test PF=39.74, 41 сделка, neg_years=0
- **Размер выборки:** 41 сделка test, 20 сделок MT4
- **Вердикт:** PASS на frozen test + MT4 confirmation
- **MT4:** TrailATR=8, TP=0: PF=51.95, 20 сделок, net=18037

### 3.3 Take/Skip v2 original_plus_path (lib_PIC path-признаки)

- **Метрика до:** original_baseline test PF=49.58, 8.4 trades/yr
- **Метрика после:** +path: PF=38.78, 10.2 trades/yr, neg_years=0
- **Размер выборки:** 29 сделок MT4
- **Вердикт:** PASS -- больше сделок при сохранении PF
- **MT4:** TrailATR=8, TP=0: PF=23.79, net=22294

### 3.4 Signal Path Atlas + fav_3_vs_12 фильтр

- **Метрика до:** "слабый drift", PF~1.0 на медиане
- **Метрика после:** PF=1.78 на 84 holdout сделках с фильтром
- **Размер выборки:** 84 holdout сделки
- **Вердикт:** PASS как research instrument; FAIL как standalone система

### 3.5 MT5 execution infrastructure

- **Метрика до:** нет MT5-контура
- **Метрика после:** 32/32 candidates с timing contract, 0 violations
- **Размер выборки:** 32 batch runs, multi-position parity 32/32
- **Вердикт:** PASS как диагностический инструмент

---

## 4. Что не работает

### 4.1 Direction prediction из фрактальных признаков

- **Что пробовали:** 3-class RF/HGB/LR, binary RF, Transformer encoder,
  direct bar model, causal surrogate
- **Числа:** test win rate=50.5% (случайный), SELL PF=0.618, rebuild
  test PF=0.99, SeqPF невалиден (разброс 0.68--4728)
- **Почему:** фрактальные признаки несут информацию об амплитуде, но не о
  направлении. Направление -- coin flip на медиане.

### 4.2 Triple Barrier как production-система

- **Что пробовали:** TB hardening + isotonic calibration + MT4 runtime
- **Числа:** test PF=1.28, 69 сделок; 2023 PF=0.55, 2026 PF=0.00
- **Почему:** regime shift между validation (2019--2022 все +) и test.
  TB-схема не устойчива к смене режима.

### 4.3 Entry-based next open direction

- **Что пробовали:** 10 табличных моделей (XGBoost, LightGBM, CatBoost,
  Extra Trees, Hist GBM), 4 profile, 4 горизонта
- **Числа:** direction Spearman val_eval=-0.001; amplitude Spearman 0.34->0.44
- **Почему:** постановка "предскажи направление от next open" не извлекает
  сигнал. Амплитуда предсказывается, но не направление.

### 4.4 Fractal stop breach -> fav -> trade chain

- **Что пробовали:** Stage 1 breach (PASS), Stage 2 fav (FAIL), Stage 4
  trade XGBoost, walk-forward
- **Числа:** walk-forward PF=0.73--0.92 на 2023-2026; Stage 2 PF < 1.0
- **Почему:** breach предсказывается, но благоприятный ход -- нет. Структурный
  перелом 2022/2023 уничтожает edge.

### 4.5 fav_3_vs_12 как standalone система

- **Что пробовали:** standalone benchmark с frozen threshold selection
- **Числа:** stable threshold не найден; PF=0.14 (validation), PF=0.31 (test)
- **Почему:** признак работает только как вспомогательный фильтр внутри
  другой сильной системы, не как самостоятельный источник прибыли.

### 4.6 lib_PIC dual-stream feature training

- **Что пробовали:** dual-stream модель (sequence + engineered), 9 configs
- **Числа:** 9/9 reject; 0 rows с PF>1 при >=6 trades/year
- **Почему:** простое добавление lib_PIC внутрь модели ломает старый
  прибыльный контур. Признаки полезнее как внешний фильтр или ablation
  поверх старого контура.

### 4.7 Fixed-11 frozen rules после chronology fix

- **Что пробовали:** 11 frozen rules на locked_test, затем chronology fix
- **Числа:** до fix -- сильные PF/BS; после fix -- PF max=0.94, kept=0
- **Почему:** Python execution contract содержал ошибку (same-H1 ML_CLOSE),
  исправление которой уничтожило весь edge.

### 4.8 Outcome-aligned retraining

- **Что пробовали:** 3 семейства targets (trade_outcome_cls, trade_pnl_reg,
  signal_archetype_cls)
- **Числа:** ни одно не прошло validation floor + yearly stability
- **Почему:** close-at-12h labels не повторяют реальную MT4 execution
  (next-bar entry, single position, exit policy).

---

## 5. Эволюция понимания

**Апрель 2026:** Проект начинался с гипотезы "слабый положительный drift"
(Variant 2). Pullback entry улучшал PF, но это был общий execution-эффект,
а не cohort-specific преимущество.

**Апрель 2026 (середина):** Signal Path Atlas совершил парадигмальный сдвиг:
медианный сигнал -- монетка (возврат -0.064 ATR за 12 баров). Двумодальная
структура: 64% провал, 36% плоский drift. Задача переформулирована: от
"как войти" к "какие сигналы торговать".

**Апрель--май 2026:** Entry path v1 + quantile layer показали, что
quantile-головы дают сильный отбор (PF=8.18). Take/skip v2 подтвердил,
что бинарное решение "брать/не брать" работает лучше, чем regression target.

**Май 2026:** Direct direction rebuild и audit показали, что фрактальные
признаки не несут direction-сигнала. Test win rate 50.5% -- случайный.
Это закрыло целую ветку исследований.

**Июнь 2026:** Fractal stop breach chain (breach -> fav -> trade) провалилась
на торговом слое. Walk-forward показал структурный перелом 2022/2023.
Regression Up/Dn target foundation подтвердил силу коротких горизонтов
(H3/H6), но не дал торгового правила.

**Июль 2026:** Entry-based powerful tabular models окончательно закрыли
direction в entry-based постановке. Amplitude подтверждён, но не direction.
Fixed-11 locked test дал сильные числа, но chronology fix уничтожил edge.

**Август 2026:** MT5 batch из 32 кандидатов -- BATCH_NO_WINNER. Все
eligible имеют PF > 1.0, но BS_p05 < 1.0. Fill-rate probe показал, что
проблема не в broker no-fill, а в single-position policy и малом числе
сделок.

**Главное изменение убеждений:**

1. "Слабый drift" -> "монетка на медиане" (Atlas Readout, апрель)
2. "Direction из фракталов" -> "только amplitude, не direction" (май--июль)
3. "Regression target" -> "binary take/skip лучше" (апрель)
4. "Pullback entry" -> "механика, не архетип" (Atlas Readout)
5. "ATR квартили" -> "нестационарны, не использовать" (Variant 3 Prep)
6. "Time-only edge" -> "возможно режимный эффект, не фрактальный сигнал"
   (rich entry normalized rerun: winner = time_only)

---

## 6. Нерешённые проблемы

### 6.1 Forward validation отсутствует

**Что известно:** entry_path_v1_quantile frozen rule готов, scaffold для
forward validation написан, но нет strictly-forward prediction CSV после
production decision.

**Что нужно выяснить:** Держится ли PF=8.18 на новых данных после
2025-11 (конец test периода).

**Предлагаемый подход:** Запустить production inference на новых данных,
собрать forward prediction CSV, дождаться накопления 30+ сделок для
первого честного forward verdict.

### 6.2 Bootstrap CI для MT4-режимов

**Что известно:** MT4-режимы дают высокие PF (3.77--51.95), но bootstrap CI
не построен ни для одного из них.

**Что нужно выяснить:** Нижняя граница 95% CI > 1.0?

**Предлагаемый подход:** Block bootstrap по daily PnL для каждого MT4-режима
(quality, frequency, original_plus_path). Минимум 200 repeats.

### 6.3 Малое число сделок

**Что известно:** Все сильные результаты -- на 20--96 сделках. MT5 batch
показал, что single-position policy ограничивает число сделок.

**Что нужно выяснить:** Достаточно ли 48 сделок для статистически значимого
вывода о PF > 1.3?

**Предлагаемый подход:** (1) Принять малое N как ограничение и строить CI
методами для малых выборок. (2) Параллельно искать способы увеличить
частоту без потери качества (anchor expansion уже дал 96 сделок).

### 6.4 Cross-instrument перенос

**Что известно:** EURUSD и GBPUSD провалились для всех систем. XAGUSD и
USDCHF -- частично поддержали.

**Что нужно выяснить:** Можно ли построить instrument-specific системы или
нужен fundamentally другой подход для major pairs?

**Предлагаемый подход:** Не использовать cross-instrument как замену
защите от переобучения. Сначала подтвердить устойчивость внутри XAUUSD,
потом проверять перенос.

### 6.5 Time-only edge

**Что известно:** Normalized rich-entry search выбрал `time_only` как winner.
Calendar permutation importance показывает устойчивый эффект.

**Что нужно выяснить:** Это режимный фильтр (время суток / день недели)
или артефакт данных?

**Предлагаемый подход:** Отдельный PARKED research direction в roadmap.
Требуется заранее заданный план без нового выбора по locked_test.

---

## 7. Накопленные ограничения

### Данные

- **Один инструмент:** XAUUSD H1 только. Cross-instrument не подтверждён.
- **Один провайдер:** MetaQuotes/Alpari. Provider drift проверен, но не
  является полной заменой forward validation.
- **Конечный объём:** 63006 Nero rows, sequential split 44104/9451/9451.
  2026 секция -- только 1162 rows.
- **M5 OHLC:** доступен только для execution ordering, не для обучения.

### Модели

- **Direction signal отсутствует:** Фрактальные признаки не предсказывают
  направление. Все direction-модели дают win rate ~50%.
- **Amplitude signal есть, но не переводим в торговлю:** Spearman 0.34--0.80,
  но нет устойчивого правила "когда торговать" на основании amplitude.
- **Time-only edge:** Возможно режимный эффект, не фрактальный сигнал.
  Не может быть использован для выбора trading parameters.

### Пайплайн

- **Нет forward data:** Production inference не запущен. Forward validation
  scaffold готов, но данных нет.
- **MT5 batch event files:** 30/32 runs первоначально не дали event files
  (LiveUpdate interference). Перезапуск решил проблему, но full runtime
  rerun не выполнен.
- **Single-position policy:** MT5 tester блокирует 99.2% сигналов из-за
  открытой позиции. Это design constraint, не bug.

### Методология

- **Множественное тестирование:** Не закрыто для большинства DIAGNOSTIC_ONLY
  этапов. 75--480 metric comparisons без коррекции.
- **SeqPF невалиден:** Shuffle-тест показал разброс 0.68--4728. Не может
  использоваться как gate metric.
- **locked_test protocol:** Строгие правила запрета нового выбора. Все
  frozen rules должны быть зафиксированы до открытия locked_test.
- **val_select/val_eval split:** Введён для предотвращения peeking, но
  ограничивает силу выводов до DIAGNOSTIC_ONLY без полного gate.

---

## 8. Рекомендации

### Что пробовать дальше

1. **Forward data collection (приоритет 1).** Запустить production inference
   на entry_path_v1_quantile и take/skip v2 quality. Собрать 30+ сделок
   для первого forward verdict. Обоснование: это единственный способ
   перевести лучшие системы из статуса "frozen test" в "confirmed".

2. **Bootstrap CI для MT4-режимов (приоритет 2).** Block bootstrap по
   daily PnL для quality, frequency, original_plus_path. Обоснование:
   без CI нельзя утверждать, что PF > 1.3 статистически значим.

3. **Portfolio-layer (приоритет 3).** quality + entry_path_v1_quantile
   как основа. frequency или original_plus_path как третий sleeve (не обе).
   Обоснование: portfolio analysis показал complementary пары
   (daily corr -0.24 -- -0.33).

4. **Amplitude-based trading (приоритет 4, исследовательский).** Отдельный
   bounded plan: amplitude как target, не direction. Заранее зафиксировать
   movement filter, horizon, запрет direction. Обоснование: amplitude
   Spearman 0.34--0.80 -- единственный устойчивый сигнал.

### Что закрыть окончательно

1. **Direction prediction из фрактальных признаков.** Закрыто. Три
   независимых проверки (rebuild, transformer, entry-based tabular) дали
   win rate ~50%. Дальнейшие попытки -- переобучение.

2. **Triple Barrier как production-система.** Закрыто. Regime shift
   2022/2023, PF=0.00 на 2026. Пересмотр только после накопления
   forward-данных post-2026-06.

3. **fav_3_vs_12 как standalone система.** Закрыто. Threshold не найден,
   PF=0.14--0.31.

4. **Fractal stop breach -> fav -> trade chain.** Закрыто. Walk-forward
   показал структурный перелом. Stage 2 PF < 1.0.

5. **Outcome-aligned retraining с close-at-12h labels.** Закрыто. Labels
   не повторяют реальную execution.

6. **Entry-based next open direction (табличный).** Закрыто. 10 моделей,
   все провалили direction gates.

### Приоритеты на следующий квартал

| Приоритет | Направление | Ожидаемый результат |
|-----------|-------------|---------------------|
| 1 | Forward data collection | First forward verdict (confirmed/watch/revisit) |
| 2 | Bootstrap CI для MT4 | Lower bound > 1.0 или явный провал |
| 3 | Portfolio-layer | Combined PF + CI на forward данных |
| 4 | MT5 entry mechanics probe | Понимание PF > 1.0 vs BS_p05 < 1.0 |
| 5 | Time-only regime (PARKED) | Отделить режимный эффект от фрактального |

---

*Документ сформирован на основе 100+ отчётов в `docs/reports/`,
15 wiki-страниц в `wiki/research/`, roadmap в `docs/superpowers/roadmap.md`
и CONTEXT_HANDOFF.md.*
