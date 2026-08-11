# Ретроспектива проекта SoSimple

> Период: февраль 2026 -- август 2026
> Дата формирования: август 2026
> Порог успеха: PF >= 1.3 на out-of-sample с учётом спреда и проскальзываний,
> подтверждённый bootstrap CI (нижняя граница > 1.0)

---

## 1. Вердикт по проекту

Порог успеха **не достигнут**. Ни одна система не показала устойчивый PF >= 1.3 с нижней границей bootstrap CI > 1.0 на строгом out-of-sample с полным учётом транзакционных издержек. Главная причина -- отсутствие переносимого directional-сигнала: фрактальные признаки предсказывают амплитуду, но не направление. Все системы с высоким PF на истории либо опирались на малые выборки (20--96 сделок), либо теряли прибыльность при переходе к forward-данным или исправлении ошибок исполнения. Сильнейшая линия (entry_path_v1_quantile, PF=8.18, 48 сделок) неподтверждена на forward данных. Все take/skip системы провалили live-safe audit из-за future-derived входов. Fractal0 Fixed-11 (PF=3.0--4.1) уничтожен исправлением chronology (PF max=0.94). MT5 batch: все BS_p05 < 1.0.

---

## 2. Направления исследований

### 2.1 Ранний регрессионный baseline

**Цель:** определить базовую архитектуру для предсказания фрактальных признаков.
**Гипотеза:** deep learning модели извлекут торговый сигнал из последовательности фракталов.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Baseline ML (02-18) | PASS | 5 baselines: Dummy, LogReg, RF, XGBoost, LightGBM |
| Regression mode (02-23) | PASS | HuberLoss, pearson_r early stopping |
| Architecture comparison (02-27) | PASS | BiLSTM r=0.324, Transformer r=0.114 |
| Optuna BiLSTM (03-12) | PASS | r: 0.323 -> 0.342 |
| Feature engineering (03-12) | FAIL | 16 признаков, PF=0.59 |
| Custom trading loss (03-16) | FAIL | Asymmetric loss не помог |

**Итог:** Определена архитектура (BiLSTM/Transformer), seq_len=20, режим регрессии. Pearson r вырос с 0.11 до 0.34. Переход к MT4 выявил разрыв: Python PF=4.50 vs MT4 PF=0.53.

### 2.2 Up/Dn мульти-таргетная регрессия

**Цель:** direction-independent таргеты для предсказания амплитуды.
**Гипотеза:** раздельное предсказание up/down устранит direction bias.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Up/Dn targets (03-18) | PASS | direction-independent up_12..dn_48 |
| Multi-task regression (03-19) | PASS | Transformer r=0.427; up_12=0.502, dn_12=0.538 |
| OOS evaluation (03-19) | PASS | H12 PF=4.50 (val), theta=2.665 |
| 3H/6H targets (03-31) | FAIL | r: 0.433->0.565, но PF: 1.20->0.87 |

**Итог:** PASS. Up/Dn таргеты стали основой для всех последующих линий. Multi-task r=0.427. Переход к длинным горизонтам ухудшил PF.

### 2.3 Triple Barrier разметка

**Цель:** TB-система с калибровкой и MT4 runtime.
**Гипотеза:** first-touch labeling + isotonic calibration дадут устойчивый PF.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Hardening (04-08) | PASS | Python test: PF=1.11, 253 сделки |
| MT4 Runtime (04-08) | PASS | MT4: PF=1.27, 92 сделки, SL/TP match 93.8% |
| MT4 Verdict (04-12) | FAIL | Test PF=1.28, 69 сделок; 2023 PF=0.55, 2026 PF=0.00 |

**Итог:** FAIL. Regime shift между validation (2019--2022 все +) и test. Gate: PF < 2.0, 2 отрицательных года.

### 2.4 Signal Quality и Archetype

**Цель:** понять постсигнальную геометрию цены, найти фильтры качества.
**Гипотеза:** часть сигналов имеет continuation pattern, который можно отфильтровать.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Variant 2 (04-01) | DIAGNOSTIC | Сигнал -- слабый drift, BUY PF=1.35 vs SELL PF=0.95 |
| Variant 3 (04-02) | DIAGNOSTIC | Pullback улучшает PF, но и отрицательные контроли |
| Atlas Readout (04-04) | PASS | Медиана -- монетка (-0.064 ATR за 12 баров), 64% провал |
| Quality Filter (04-04) | PASS | fav_3_vs_12 <= 0.653: PF=1.78, 84 holdout сделки |
| Standalone (04-13) | FAIL | Threshold не найден, PF=0.14--0.31 |

**Итог:** PASS как research instrument. Парадигмальный сдвиг: задача -- отбор 36% хороших сигналов, не оптимизация входа. FAIL как standalone система.

### 2.5 Entry Path V1 трансформер

**Цель:** слой "торговать / не торговать" поверх regression_updn.
**Гипотеза:** trade filter по pred_ret_24_dir_atr отберёт прибыльные входы.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Baseline (04-08) | PASS | ret_pearson_r=0.245 |
| Loss Weighting (04-09) | PASS | Вес 5.0: test PF=4.29, 44 сделки |
| Trade Filter A @ 7.5% (04-09) | PASS | Test PF=4.29, WR=72.73% |
| MT4 Winner (04-09) | PASS | MT4: 22 сделки, PF=8.47 |
| Live-safe retrain (05-07) | PASS | Median seq PF=2.32, min=1.82, 5 seeds |

**Итог:** PASS на frozen test. Superseded quantile-layer. Live-safe baseline A @ 7.5% подтверждён multi-seed.

### 2.6 Quantile слой и production

**Цель:** quantile-головы ret_24_q10/ret_24_q90 поверх entry_path_v1.
**Гипотеза:** quantile-layer даст устойчивый PF > 2.0.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Quantile Layer (04-10) | PASS | Test: 24 сделки, PF=inf |
| Multi-seed (04-11) | PASS | 5/5 seeds, same rule, median PF=inf |
| Status Decision (04-12) | PASS | N=48, PF=8.18, MT4 parity 20/20 |
| MT4 Parity (04-12) | PASS | 20/20, net=4477, PF=11.91 |
| Forward Validation (04-13) | WATCH | no_forward_data, 0 trades |
| Cross-Instrument (04-24) | MIXED | XAGUSD supported, EURUSD/GBPUSD failed |
| Live-safe audit (05-05) | FAIL | Future-derived входы в baseline |
| CPU retrain (05-07) | PASS | Median seq PF=2.32, min=1.82 |

**Итог:** Сильнейшая линия проекта. PF=8.18 на 48 сделках, MT4 PF=11.91. Но: малая выборка, forward validation не выполнен, live-safe audit выявил future-derived входы.

### 2.7 Take/Skip и trailing stop

**Цель:** бинарное решение "брать / не брать" сигнал с trailing-stop выходом.
**Гипотеза:** take/skip v2 с multi-horizon targets даст устойчивый PF.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| v1 matrix (04-17) | FAIL | Все reject, PF < 1.0 |
| v2 scaffold (04-17) | PASS | Validation winner: take_48_x4, PF=6.39, 24 сделки |
| Quality-first (04-18) | PASS | Test PF=39.74, 41 сделка, neg_years=0 |
| Frequency (04-18) | PASS | Test PF=13.12, 56 сделок, neg_years=0 |
| MT4 frequency (04-19) | PASS | TrailATR=8, TP=0: PF=3.77, 56 сделок, net=24521 |
| lib_PIC selection (04-20) | DIAGNOSTIC | Не улучшил quality, убрал отрицательный год |
| Live-safe (05-05) | FAIL | Future-derived входы: predict, ret_*, fav_*, adv_* |

**Итог:** PASS на frozen test. FAIL для online trading: все системы используют future-derived входы. Live-safe rebuild не воспроизвёл прибыльность (reject).

### 2.8 lib_PIC банк признаков

**Цель:** dual-stream модель с lib_PIC geometry/reaction features.
**Гипотеза:** внешние признаки усилят selection layer.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| External selection (04-20) | DIAGNOSTIC | Не улучшил quality; убрал neg year у frequency |
| Feature training (04-20) | FAIL | 9/9 reject; 0 rows PF>1 при >=6 trades/year |
| Original contour ablation (04-20) | PASS | path-признаки: test PF=38.78, 10.2 trades/yr |
| MT4 confirmation (04-22) | PASS | TrailATR=8: PF=23.79, 29 сделок |

**Итог:** Dual-stream FAIL. Path-признаки в старом контуре PASS (больше сделок при сохранении PF). Но live-safe audit закрыл весь take/skip контур.

### 2.9 Прямое предсказание направления

**Цель:** binary BUY/SELL классификатор на фрактальных признаках.
**Гипотеза:** фрактальные признаки несут direction-сигнал.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| 3-class RF (05-15) | FAIL | Val PF=1.01--1.11 |
| Binary RF (05-15) | PASS | Test PF=1.226, BUY PF=1.904, SELL PF=0.618 |
| Chain audit (05-18) | FAIL | 6 ошибок: contamination, units, targets |
| Rebuild (05-21) | FAIL | Test PF=0.99, win rate=50.5% |
| Transformer direction (05-21) | FAIL | Trail PF=2.41 на 58 сделках, 0.6% utilisation |

**Итог:** FAIL. Закрыто окончательно. Фрактальные признаки не несут direction-сигнала. Test win rate=50.5% -- случайный.

### 2.10 Live-safe и воспроизводимость

**Цель:** проверить CPU/GPU parity, server reproducibility, live-safe gate.
**Гипотеза:** production retrain воспроизводим на CPU.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| CPU/GPU (05-07) | PASS | CPU-trained inference: overlap 100%, corr 1.0 |
| Live-safe audit (05-05) | FAIL | Все 5 систем: future-derived входы |
| Server multi-seed (05-07) | PASS | Baseline A: median seq PF=2.32, min=1.82 |
| MT4 parity (05-07) | PASS | 26/26 сделок, PF=9.03, net=5217 |

**Итог:** PASS как инфраструктура. Production retrain CPU-only. Все прибыльные системы провалили live-safe gate.

### 2.11 Кросс-инструментальная робастность

**Цель:** проверить перенос систем на другие инструменты.
**Гипотеза:** системы работают на разных Forex-парах.

| Инструмент | quality | frequency | original_plus_path |
|------------|---------|-----------|-------------------|
| XAGUSD | failed | supported | failed |
| EURUSD | failed | failed | failed |
| GBPUSD | inconclusive | inconclusive | supported |
| USDCHF | supported | supported | supported |

**Итог:** MIXED. EURUSD -- жёсткий negative case. USDCHF -- strongest positive. frequency -- самый живучий по переносу. Provider drift не разрушает системы на том же инструменте.

### 2.12 Fractal Stop Breach сигнал

**Цель:** цепочка breach -> fav -> trade для предсказания пробоя фрактального уровня.
**Гипотеза:** breach_signal + pred_fav даст PF > 1.0.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Stage 1 breach (06-10) | PASS | 12 breach-таргетов, диагностически предсказывается |
| Stage 2 fav (06-10) | FAIL | PF < 1.0 |
| Stage 4 XGBoost (06-11) | FAIL | Val_eval PF=0.897 |
| Deep diagnostics (06-14) | DIAGNOSTIC | trail_atr_0_2 PF=1.831, но диагностический |
| Walk-forward | FAIL | PF=0.73--0.92 на 2023-2026 |

**Итог:** FAIL. Breach предсказывается, fav -- нет. Структурный перелом 2022/2023 уничтожает edge.

### 2.13 Transformer для фрактального пробоя

**Цель:** Transformer encoder как feature extractor для breach-классификации.
**Гипотеза:** Transformer улучшит AUC breach-классификатора.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Stage 5.0-prep (06-15) | DIAGNOSTIC | time_only AUC=0.6286 > fractal AUC=0.6143 |
| Stage 5.0 Transformer (06-17) | DIAGNOSTIC | Full model AUC=0.6674, time +561bp, fractal +388bp |
| AUC->PF sensitivity | DIAGNOSTIC | Требуемый AUC=0.8442, разрыв +1768bp |

**Итог:** DIAGNOSTIC_ONLY. Transformer оправдан (fractal +388bp), но календарный baseline обязателен. Ценовые признаки шумят.

### 2.14 Time-to-breach регрессия

**Цель:** предсказать время до пробоя уровня вместо бинарной классификации.
**Гипотеза:** регрессия на время даст более богатый сигнал.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Stage 5.2 (06-25) | FAIL | Не улучшил binary breach PF |
| Stage 5.3 reformulation (06-26) | FAIL | Target reformulation не помогла |

**Итог:** FAIL. Регрессия на время не дала преимущества над бинарной классификацией.

### 2.15 Stage 6 outcome-based таргеты

**Цель:** новые семейства признаков и target-постановок для TP/SL touch prediction.
**Гипотеза:** outcome-based targets улучшат торговый сигнал.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Triple barrier foundation (06-29) | DIAGNOSTIC | H12 relative geometry |
| H12 price action (06-30) | FAIL | range_w1_atr -- артефакт |
| H6 parity check (06-30) | FAIL | Не дал устойчивого сигнала |
| Regression Up/Dn ratio (07-01) | DIAGNOSTIC | Already-moved audit |

**Итог:** FAIL. Direction-постановка стабильно проваливается (Spearman val_eval=-0.001). Amplitude-сигнал устойчив (Spearman 0.34--0.45), но не переводим в торговлю.

### 2.16 Entry-based next-open направление

**Цель:** проверить direction-сигнал от next open entry.
**Гипотеза:** табличные модели извлекут direction от next open.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Price feature matrix (07-02) | FAIL | Direction Spearman val_eval=-0.001 |
| Fractal selection ablation (07-03) | FAIL | Не улучшил direction |
| Next open closeout (07-04) | FAIL | Direction не предсказывается |
| Powerful tabular (07-06) | FAIL | 10 моделей, все провалили direction gates |

**Итог:** FAIL. 10 моделей (XGBoost, LightGBM, CatBoost, Extra Trees, Hist GBM), 4 профиля, 4 горизонта -- все провалили direction. Amplitude Spearman 0.34--0.44.

### 2.17 Amplitude и movement режим

**Цель:** проверить amplitude и movement filter как основу для торговли.
**Гипотеза:** amplitude предсказывается устойчиво и может быть основой для фильтра.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Amplitude movement (07-07) | PASS | Spearman 0.34--0.44 на H3/H6 |
| Movement filter design (07-07) | PASS | Lift на val_eval |
| Movement filter freeze (07-08) | PASS | 64 конфигурации -> 32 кандидата |

**Итог:** PASS как диагностический сигнал. Amplitude предсказывается устойчиво. Movement filter показывает lift. Перевод в торговое правило не выполнен.

### 2.18 Direction inside frozen mask

**Цель:** проверить direction-сигнал внутри frozen movement regime mask.
**Гипотеза:** direction усиливается внутри movement mask.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Base (07-08) | FAIL | Direction не усиливается |
| Rich features (07-09) | FAIL | Не улучшил |
| Narrow replication (07-10) | FAIL | Подтверждено на smoke |

**Итог:** FAIL. Direction не усиливается внутри movement mask. Подтверждено на трёх независимых проверках.

### 2.19 Fractal0 entry/exit сетка

**Цель:** проверить limit-order entry в зоне fractal0_price с M5 execution ordering.
**Гипотеза:** entry/exit grid найдёт устойчивую механику входа.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Oracle preflight (07-10) | DIAGNOSTIC | 108 конфигураций, active_years=2 |
| Entry-exit grid H1 (07-21) | PASS | PF=1.94, BS_p05=1.76, val_eval |
| Entry-exit grid M5 (07-21) | PASS | PF=2.72, BS_p05=2.49, val_eval |
| Stop-policy grid (07-21) | PASS | S2/E3/M0/X2: PF=2.79, BS_p05=2.51 |

**Итог:** PASS как research. Entry-exit grid дал сильные числа на val_eval. Но winner выбран после широкого validation search, locked_test не открыт.

### 2.20 Fractal0 rich entry quality

**Цель:** ML-фильтр качества входа поверх stop-grid winner.
**Гипотеза:** rich-entry features улучшат PF.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Entry-quality filter (07-21) | FAIL | val_eval PF=1.95, BS_p05=0.97 |
| Rich entry search (07-21) | PASS | val_eval PF=4.03, BS_p05=3.40 |
| Normalized rerun (07-22) | PASS | Winner: time_only, PF=4.03 |
| Time-only robustness (07-23) | DIAGNOSTIC | best_year_share=0.53 |
| Leaderboard audit (07-23) | DIAGNOSTIC | 11 rows, все RULE_ROBUSTNESS_INCOMPLETE |

**Итог:** Winner -- time_only (календарно-временной эффект), не фрактальный сигнал. Rich features не дали аддитивного доказательства.

### 2.21 Fixed-11 замороженные правила

**Цель:** проверить 11 frozen normalized rich-entry leaderboard rules.
**Гипотеза:** 11 frozen rules выдержат locked_test.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Internal closure rerun (07-23) | PASS | Multiseed PF=3.0--4.1, BS_p05=2.6--3.4 |
| Locked test (07-24) | PASS | Сильные PF/BS numbers |
| Candidate audit (07-25) | PASS | candidate_audit_passed |
| Mutual correlation pruning (07-27) | PASS | Retained subset: 5 правил |
| MT4 parity (07-27) | PASS | Per-rule diagnostic route |
| Chronology fix (07-29) | FAIL | PF max=0.939, kept_candidates=0 |

**Итог:** FAIL. Locked test дал сильные числа, но исправление Python execution contract (same-H1 ML_CLOSE до fill) уничтожило весь edge. PF max=0.939, PnL sum=-530.51.

### 2.22 MT5 execution loop миграция

**Цель:** перенести диагностический execution-контур с MT4 на MT5 Strategy Tester.
**Гипотеза:** MT5 даст более честный execution-контур.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Feasibility (07-29) | PASS | Expert компилируется, signal schema |
| OnTradeTransaction (07-31) | PASS | UNEXPLAINED=0, 269 positions |
| Nero parity (07-31) | PASS | Match rate 99.05%, direction 99.24% |
| Batch selection (07-31) | FAIL | 32 candidates, BATCH_NO_WINNER, все BS_p05 < 1.0 |
| Timing contract (08-01) | PASS | 32/32 candidates, 0 violations |

**Итог:** MT5-контур построен (Nero parity 99.05%, timing contract 32/32). Batch: BATCH_NO_WINNER. Fill-rate probe: 99.2% OPEN_FAILED -- single-position policy. Position-ordinal PnL: non-monotonic pattern.

---

## 3. Что работает

### 3.1 Quantile-layer entry selection
- **Метрика до:** entry_path_v1 baseline test PF=4.29, 44 сделки
- **Метрика после:** quantile test PF=8.18, 48 сделок, win_rate=0.81
- **Размер выборки:** 48 сделок test, 5 seeds (все прошли)
- **Вердикт:** PASS на frozen test; MT4 PF=11.91, 20/20 сделок. Forward validation не выполнен.

### 3.2 Take/Skip v2 quality-first
- **Метрика до:** take/skip v1 matrix -- все reject, PF < 1.0
- **Метрика после:** quality test PF=39.74, 41 сделка, neg_years=0
- **Размер выборки:** 41 сделка test, 20 сделок MT4
- **Вердикт:** PASS на frozen test + MT4 (PF=51.95). Live-safe FAIL.

### 3.3 Take/Skip v2 frequency execution
- **Метрика до:** original_baseline test PF=49.58, 8.4 trades/yr
- **Метрика после:** frequency test PF=13.12, 56 сделок, neg_years=0
- **Размер выборки:** 56 сделок test
- **Вердикт:** PASS на frozen test. MT4 PF=3.77, net=24521. Live-safe FAIL.

### 3.4 Entry Path v1 live-safe baseline
- **Метрика до:** entry_path_v1 с future-derived ret_dir_atr_lag1
- **Метрика после:** live-safe baseline A @ 7.5%, median seq PF=2.32, min=1.82
- **Размер выборки:** 5 seeds server multi-seed
- **Вердикт:** PASS как live-safe кандидат. MT4 parity: 26/26 сделок, PF=9.03.

### 3.5 Amplitude prediction (H3/H6)
- **Метрика до:** нет amplitude baseline
- **Метрика после:** Spearman 0.34--0.80 на H3/H6, устойчив на Ridge и XGBoost
- **Размер выборки:** 63006 Nero rows, 5 профилей, 5 model families
- **Вердикт:** PASS как диагностический сигнал; FAIL как торговое правило.

### 3.6 CPU/GPU reproducibility
- **Метрика до:** CPU/GPU расхождение в training
- **Метрика после:** CPU-trained checkpoint inference: top-5% overlap 100%, correlation 1.0
- **Размер выборки:** 5 seeds, server multi-seed
- **Вердикт:** PASS. Production retrain CPU-only.

---

## 4. Что не работает

### 4.1 Direction prediction из фрактальных признаков
- **Что пробовали:** 3-class RF/HGB/LR, binary RF, Transformer encoder, direct bar model, causal surrogate, direction-only TB, 10 табличных моделей
- **Числа:** test win rate=50.5% (случайный), SELL PF=0.618, rebuild test PF=0.99, TB direction-only PF=1.113 с 3 отрицательными годами
- **Почему:** фрактальные признаки несут информацию об амплитуде, но не о направлении. Направление -- coin flip на медиане.

### 4.2 Triple Barrier как production-система
- **Что пробовали:** TB hardening + isotonic calibration + MT4 runtime
- **Числа:** test PF=1.28, 69 сделок; 2023 PF=0.55, 2026 PF=0.00
- **Почему:** regime shift между validation (2019--2022 все +) и test.

### 4.3 Fractal stop breach -> fav -> trade chain
- **Что пробовали:** Stage 1 breach (PASS), Stage 2 fav (FAIL), Stage 4 trade XGBoost, walk-forward
- **Числа:** walk-forward PF=0.73--0.92 на 2023-2026; Stage 2 PF < 1.0
- **Почему:** breach предсказывается, но благоприятный ход -- нет. Структурный перелом 2022/2023.

### 4.4 lib_PIC dual-stream feature training
- **Что пробовали:** dual-stream модель (sequence + engineered), 9 configs
- **Числа:** 9/9 reject; 0 rows с PF>1 при >=6 trades/year
- **Почему:** простое добавление lib_PIC внутрь модели ломает старый прибыльный контур.

### 4.5 Fixed-11 frozen rules после chronology fix
- **Что пробовали:** 11 frozen rules на locked_test, затем chronology fix
- **Числа:** до fix -- multiseed PF=3.0--4.1; после fix -- PF max=0.939, kept=0
- **Почему:** Python execution contract содержал ошибку same-H1 ML_CLOSE до fill.

### 4.6 Outcome-aligned retraining
- **Что пробовали:** 3 семейства targets (trade_outcome_cls, trade_pnl_reg, signal_archetype_cls)
- **Числа:** ни одно не прошло validation floor + yearly stability
- **Почему:** close-at-12h labels не повторяют реальную MT4 execution.

### 4.7 MT5 batch selection
- **Что пробовали:** 32 кандидата movement-filter через MT5 tester, block bootstrap
- **Числа:** 11 eligible, все PF > 1.0, но все BS_p05 < 1.0; best PF=1.23
- **Почему:** PF > 1.0 сосуществует с BS_p05 < 1.0 из-за low trade count noise. Single-position policy блокирует 99.2% сигналов.

### 4.8 Python-to-MT4 performance gap
- **Что пробовали:** threshold analysis на OOS (PF=4.50), интеграция с MT4
- **Числа:** Python PF=4.50 vs MT4 PF=0.53; после trailing stop -- PF=1.03--1.23
- **Почему:** position blocking теряет 51.3% сигналов, MFE/MAE иллюзия, SL/TP fixed.

---

## 5. Эволюция понимания

**Февраль--март 2026:** Проект начинался с raw regression (BiLSTM r=0.324, PF=0.59). Ключевые находки: DirAcc=97.5% -- артефакт abs(target); Macro F1=0.57 обманчив при 95% neutral классе; seq_len=20 оптимально. Up/Dn direction-independent таргеты подняли r с 0.32 до 0.43. Переход к MT4 выявил структурный разрыв: Python PF=4.50 vs MT4 PF=0.53.

**Апрель 2026:** Signal Path Atlas совершил парадигмальный сдвиг: медианный сигнал -- монетка (-0.064 ATR за 12 баров), двумодальная структура (64% провал, 36% плоский drift). Задача переформулирована: от "как войти" к "какие сигналы торговать". Entry path v1 + quantile layer показали сильный отбор (PF=8.18). Take/skip v2 подтвердил, что бинарное решение работает лучше regression target.

**Май 2026:** Direct direction rebuild и audit показали, что фрактальные признаки не несут direction-сигнала (win rate 50.5%). Live-safe audit выявил future-derived входы во всех прибыльных системах. Это закрыло целую ветку исследований.

**Июнь 2026:** Fractal stop breach chain провалилась на торговом слое. Walk-forward показал структурный перелом 2022/2023. Structural field ablation выявила доминирование time_only над фрактальными признаками.

**Июль 2026:** Entry-based tabular модели окончательно закрыли direction. Fixed-11 locked test дал сильные числа (PF=3.0--4.1), но chronology fix уничтожил edge (PF max=0.939). Winner -- time_only (календарно-временной эффект).

**Август 2026:** MT5 batch -- BATCH_NO_WINNER. Fill-rate probe: single-position policy, не broker no-fill.

**Главные изменения убеждений:**
1. "Слабый drift" -> "монетка на медиане" (апрель, Atlas Readout)
2. "Direction из фракталов" -> "только amplitude, не direction" (май--июль)
3. "Python PF=4.50" -> "MT4 PF=0.53: execution gap" (март)
4. "Regression target" -> "binary take/skip лучше" (апрель)
5. "Pullback entry" -> "механика, не архетип" (апрель)
6. "Structural fields" -> "time_only доминирует" (июнь)
7. "Fixed-11 прибыльны" -> "chronology fix уничтожил edge" (июль)
8. "Fill rate -- проблема" -> "single-position policy" (август)

---

## 6. Нерешённые проблемы

### 6.1 Forward validation отсутствует
**Что известно:** entry_path_v1_quantile frozen rule готов, scaffold написан, но нет strictly-forward prediction CSV.
**Что нужно выяснить:** Держится ли PF=8.18 на новых данных после 2025-11.
**Подход:** Запустить production inference, собрать 30+ сделок для первого честного forward verdict.

### 6.2 Bootstrap CI для MT4-режимов
**Что известно:** MT4-режимы дают высокие PF (3.77--51.95), но bootstrap CI не построен.
**Что нужно выяснить:** Нижняя граница 95% CI > 1.0?
**Подход:** Block bootstrap по daily PnL, минимум 200 repeats.

### 6.3 Time-only edge
**Что известно:** Normalized rich-entry выбрал time_only. Calendar permutation показывает устойчивый эффект. Multiseed PF=3.0--4.1.
**Что нужно выяснить:** Это режимный фильтр или артефакт данных?
**Подход:** Отдельный PARKED research direction с заранее заданным планом.

### 6.4 PF > 1.0 vs BS_p05 < 1.0 в MT5 batch
**Что известно:** 11 eligible имеют PF > 1.0, но все BS_p05 < 1.0. Position-ordinal PnL non-monotonic.
**Что нужно выяснить:** Почему PF > 1.0 сосуществует с BS_p05 < 1.0?
**Подход:** Frozen probe plan targeting entry mechanics and trade-count consolidation.

### 6.5 Cross-instrument перенос
**Что известно:** EURUSD/GBPUSD провалились. XAGUSD/USDCHF частично поддержали.
**Что нужно выяснить:** Можно ли построить instrument-specific системы?
**Подход:** Сначала подтвердить устойчивость внутри XAUUSD.

---

## 7. Накопленные ограничения

### Данные
- **Один инструмент:** XAUUSD H1 только. Cross-instrument не подтверждён.
- **Один провайдер:** MetaQuotes/Alpari. Provider drift проверен, но не заменяет forward validation.
- **Конечный объём:** 63006 Nero rows, sequential split 44104/9451/9451. 2026 -- только 1162 rows.
- **M5 OHLC:** доступен только для execution ordering, не для обучения.

### Модели
- **Direction signal отсутствует:** фрактальные признаки не предсказывают направление. Win rate ~50%.
- **Amplitude signal есть, но не переводим в торговлю:** Spearman 0.34--0.80, но нет устойчивого правила.
- **Time-only edge:** возможно режимный эффект, не фрактальный сигнал.
- **Future-derived входы:** все прибыльные take/skip системы используют запрещённые входы.

### Пайплайн
- **Нет forward data:** production inference не запущен.
- **Single-position policy:** MT5 tester блокирует 99.2% сигналов.
- **Chronology fix:** Python execution contract содержал ошибку, уничтожившую edge Fixed-11.

### Методология
- **Множественное тестирование:** не закрыто для большинства DIAGNOSTIC_ONLY этапов.
- **SeqPF невалиден:** shuffle-тест показал разброс 0.68--4728.
- **Live-safe gate:** все прибыльные системы провалили audit.
- **val_select/val_eval split:** ограничивает силу выводов до DIAGNOSTIC_ONLY.

---

## 8. Рекомендации

### Что пробовать дальше

1. **Forward data collection (приоритет 1).** Запустить production inference на entry_path_v1_quantile и entry_path_v1_live_safe. Собрать 30+ сделок для первого forward verdict. Обоснование: единственный способ перевести лучшие системы из "frozen test" в "confirmed".

2. **Bootstrap CI для MT4-режимов (приоритет 2).** Block bootstrap по daily PnL для entry_path_v1_live_safe. Обоснование: без CI нельзя утверждать, что PF > 1.3 статистически значим.

3. **Amplitude-based trading (приоритет 3, исследовательский).** Amplitude как target, не direction. Заранее зафиксировать movement filter, horizon, запрет direction. Обоснование: amplitude Spearman 0.34--0.80 -- единственный устойчивый сигнал.

4. **Time-only regime (приоритет 4, PARKED).** Отделить режимный эффект от фрактального. Заранее заданный план без нового выбора. Обоснование: time_only доминирует в normalized rich-entry, но природа эффекта неясна.

5. **MT5 entry mechanics probe (приоритет 5).** Понять, почему PF > 1.0 сосуществует с BS_p05 < 1.0. Обоснование: ключ к пониманию статистической значимости.

### Что закрыть окончательно

1. **Direction prediction из фрактальных признаков.** Три независимых проверки дали win rate ~50%. Дальнейшие попытки -- переобучение.

2. **Triple Barrier как production-система.** Regime shift 2022/2023, PF=0.00 на 2026. Пересмотр только после forward-данных post-2026-06.

3. **fav_3_vs_12 как standalone система.** Threshold не найден, PF=0.14--0.31.

4. **Fractal stop breach -> fav -> trade chain.** Walk-forward показал структурный перелом. Stage 2 PF < 1.0.

5. **Outcome-aligned retraining с close-at-12h labels.** Labels не повторяют реальную execution.

6. **Entry-based next open direction (табличный).** 10 моделей, все провалили direction gates.

7. **Fixed-11 frozen rules.** Chronology fix уничтожил edge: PF max=0.939, kept=0.

8. **lib_PIC dual-stream feature training.** 9/9 reject.

### Приоритеты на следующий квартал

| Приоритет | Направление | Ожидаемый результат |
|-----------|-------------|---------------------|
| 1 | Forward data collection | First forward verdict (confirmed/watch/revisit) |
| 2 | Bootstrap CI для MT4 | Lower bound > 1.0 или явный провал |
| 3 | Amplitude-based trading | Устойчивое торговое правило или закрытие |
| 4 | Time-only regime (PARKED) | Отделить режимный эффект от артефакта |
| 5 | MT5 entry mechanics probe | Понимание PF > 1.0 vs BS_p05 < 1.0 |

---

*Документ сформирован на основе 100+ отчётов в docs/reports/ и ML/reports/, записей CHANGELOG.md за февраль--август 2026, wiki-страниц в wiki/research/.*
