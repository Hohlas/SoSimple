# Ретроспектива проекта SoSimple

> Период: февраль 2026 -- август 2026
> Дата формирования: август 2026
> Порог успеха: PF >= 1.3 на out-of-sample с учётом спреда и проскальзываний,
> подтверждённый bootstrap CI (нижняя граница > 1.0)

---

## 1. Вердикт по проекту

Порог успеха **не достигнут**. Ни одна из исследованных систем не показала устойчивый PF >= 1.3 с нижней границей bootstrap CI > 1.0 на строгом out-of-sample периоде с полным учётом транзакционных издержек. Главная причина -- отсутствие переносимого directional-сигнала: фрактальные признаки предсказывают амплитуду движения, но не его направление. Все системы с высоким PF на исторических данных либо опирались на малые выборки (20--96 сделок), либо теряли прибыльность при переходе к forward-данным, смене провайдера данных или исправлении ошибки исполнения (chronology fix). Наиболее сильная линия (`entry_path_v1_quantile`, PF=8.18 на 48 сделках test) остаётся неподтверждённой на strictly-forward данных -- scaffold готов, но prediction CSV после production decision пока не собран. MT5 batch из 32 кандидатов дал BATCH_NO_WINNER: все 11 eligible имеют PF > 1.0, но BS_p05 < 1.0.

---

## 2. Направления исследований

### 2.1 Нейросетевая основа (февраль--март 2026)

**Цель:** определить базовую архитектуру и режим обучения для предсказания фрактальных признаков.

**Гипотеза:** deep learning модели (Transformer, BiLSTM, CNN1D, Hybrid) извлекут торговый сигнал из последовательности фракталов.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Baseline ML (02-18) | PASS | 5 baselines: Dummy, LogReg, RF, XGBoost, LightGBM |
| Regression mode (02-23) | PASS | HuberLoss, pearson_r early stopping |
| Architecture comparison -- regression (02-27) | PASS | BiLSTM Pearson r=0.324, Transformer r=0.114 |
| Class imbalance trap (02-27) | PASS | Macro F1=0.57 обманчив: F1(0)=0.95, F1(+/-1)=0.35 |
| Optuna BiLSTM regression (03-12) | PASS | Pearson r: 0.323 -> 0.342 |
| Ablation study (03-12) | PASS | seq_len=20 оптимально (r=0.328 vs 0.324 при 100) |
| Feature engineering (03-12) | FAIL | 16 признаков, PF=0.59 |
| Custom trading loss (03-16) | FAIL | Asymmetric loss не помог |
| Up/Dn targets (03-18) | PASS | direction-independent таргеты up_12..dn_48 |
| Multi-task regression (03-19) | PASS | Transformer r=0.427; up_12=0.502, dn_12=0.538 |
| OOS evaluation (03-19) | PASS | H12 PF=4.50 (val), θ=2.665 |
| Phase B.1: 3H/6H targets (03-31) | FAIL | Pearson r: 0.433->0.565, но PF: 1.20->0.87 |
| Directional asymmetric loss (03-31) | FAIL | PF=1.04 (alpha=2.5), PF=0.97 (alpha=5.0) |

**Итог:** Определена оптимальная архитектура (Transformer/BiLSTM), длина последовательности (seq_len=20), режим регрессии (HuberLoss, Up/Dn targets). Pearson r вырос с 0.11 до 0.43. Переход к MT4 Strategy Tester выявил структурный разрыв: Python PF=4.50 vs MT4 PF=0.53.

### 2.2 Торговая конвертация сигнала (март--апрель 2026)

**Цель:** подключить ML-модель к MT4 Strategy Tester и оценить реальную торговую прибыльность.

**Гипотеза:** Python OOS PF=4.50 транслируется в прибыльную MT4-систему.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| MT4<->ML integration (03-20) | PASS | 58540 signals loaded |
| Conformal Prediction (03-20) | FAIL | Не добавляет ценности при θ=2.665 |
| MT4 Strategy Tester debug (03-21) | FAIL | WR~46%, PF<1 при R:R=1:1 |
| Asymmetric R:R diagnostics (03-22) | DIAGNOSTIC_ONLY | Python PF=4.50 vs MT4 PF<1: look-ahead bias + position blocking 51.3% |
| signal_tracer v2.0 (03-24) | DIAGNOSTIC_ONLY | MFE/MAE иллюзия: 33 сделки -- Python TP, MT4 SL |
| 922-trade analysis (03-26) | DIAGNOSTIC_ONLY | PF(SL/TP)=0.53; ratio>4.5 -- убыточная зона |
| Trailing stop + optimization (03-23) | PASS | WR: 34.55%->54.07%; PF=1.03, 922 сделки |
| EA optimization Phase A (03-27) | PASS | PF: 0.53->1.23; ML_MaxRatio=4.5 |

**Итог:** Ключевой разрыв: Python OOS PF=4.50 (MFE-based, без SL/TP) vs MT4 PF=0.53 (фиксированные SL/TP). Причины: (1) look-ahead bias в Python, (2) position blocking -- 51.3% сигналов теряются, (3) MFE/MAE иллюзия. Trailing stop поднял WR с 34.55% до 54.07%. EA-оптимизация подняла PF до 1.23, но ниже порога 1.3.

### 2.3 Entry Path и production-кандидаты (апрель 2026)

**Цель:** построить слой "торговать / не торговать" поверх regression_updn базы, используя quantile-головы для отбора лучших входов.

**Гипотеза:** quantile-layer (ret_24_q10, ret_24_q90) поверх entry_path_v1 даст устойчивый PF > 2.0.

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
| Live-safe reproducibility (05-07) | PASS | CPU/GPU parity подтверждена |

**Итог:** Сильнейшая линия проекта. PF=8.18 на 48 сделках test, подтверждён MT4 parity (20/20, PF=11.91 в деньгах). Multi-seed устойчив. Но: (1) малая выборка, (2) forward validation не выполнен, (3) cross-instrument перенос ограничен.

### 2.4 Исследование качества сигнала (апрель 2026)

**Цель:** понять постсигнальную геометрию цены и найти фильтры качества сигнала.

**Гипотеза:** signal quality filter по `fav_3_vs_12` отберёт прибыльные сигналы.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Variant 2 (04-01) | DIAGNOSTIC | PF_12=1.95, BUY>SELL |
| Variant 3 (04-02) | DIAGNOSTIC | Pullback улучшает, но и отрицательные контроли |
| Atlas Readout (04-04) | PASS | Медиана = монетка, двумодальная структура |
| Quality Filter (04-04) | PASS | fav_3_vs_12 <= 0.653, PF=1.78 на 84 holdout |
| Archetype Bridge (04-04) | PASS | Единственный validated фильтр |
| Fav Standalone (04-13) | FAIL | threshold не найден, PF=0.14--0.31 |

**Итог:** Парадигмальный сдвиг: "слабый drift" -> "монетка на медиане, двумодальная структура". Задача переформулирована от "как войти" к "какие сигналы торговать". `fav_3_vs_12` полезен как вспомогательный фактор, но не как самостоятельная система.

### 2.5 Прямое предсказание направления (май 2026)

**Цель:** построить модель, предсказывающую BUY/SELL направление непосредственно из фрактальных признаков.

**Гипотеза:** binary BUY/SELL классификатор на фрактальных признаках даст PF > 1.3 на OOS.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Direct Direction Improvement (05-15) | DIAGNOSTIC | Binary RF: test PF=1.226, BUY PF=1.904, SELL PF=0.618 |
| Chain Audit (05-18) | FAIL | 6 ошибок в chain: нормализация, единицы, targets |
| Direct Direction Rebuild (05-21) | FAIL | Test PF=0.99, BUY win rate=50.5% |
| Transformer Direction (05-21) | FAIL | Trail PF=2.41 на 58 сделках, 0.6% utilisation |
| Direction-only TB (06-03) | FAIL | Лучший TB PF=1.113, 3 отрицательных года |

**Итог:** Направление закрыто окончательно. Фрактальные признаки не несут direction-сигнала. Test win rate 50.5% неотличим от случайного. SeqPF признан невалидной метрикой (shuffle-тест: разброс 0.68--4728 при PF=1.10).

### 2.6 Fractal Stop pipeline (июнь 2026)

**Цель:** проверить цепочку breach -> fav -> trade для предсказания пробоя фрактального уровня.

**Гипотеза:** цепочка breach -> fav -> trade даст устойчивый PF > 1.3.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Stage 1: Breach (06-10) | PASS (диагност.) | Пробой предсказывается |
| Stage 2: Fav (06-10) | FAIL | PF < 1.0 на canonical spread |
| Stage 4: Trade XGBoost (06-11) | FAIL | val_eval PF=0.897 |
| Walk-forward (06-15) | FAIL | PF=0.84--0.92 на 2023-2026 |
| Stage 5: Transformer (06-17) | FAIL | Без улучшения после исправления бага |
| Signal stationarity (06-24) | DIAGNOSTIC_ONLY | Сигнал деградирует на 2023+ |

**Итог:** Breach предсказывается, но торговый слой не работает. Walk-forward показал структурный перелом 2022/2023: модель прибыльна на 2017--2022 (PF=1.42--1.91), убыточна на 2023-2026 (PF=0.73--0.90).

### 2.7 Реформа таргетов (июнь--июль 2026)

**Цель:** проверить новые семейства признаков и target-постановок для TP/SL touch prediction.

**Гипотеза:** недавнее OHLC price action и локальная геометрия фракталов улучшают предсказание.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Regression Up/Dn Foundation (06-30) | DIAGNOSTIC_ONLY | structure_full H3: Spearman 0.76--0.80 |
| Already Moved Audit (07-02) | DIAGNOSTIC_ONLY | Часть сигнала -- уже произошедшее движение |
| Entry-based next open (07-04) | PIVOT | direction слаб, amplitude сильнее |
| Powerful tabular (07-06) | PIVOT | direction Spearman val_eval=-0.001 |
| Amplitude movement regime (07-07) | DIAGNOSTIC_ONLY | Amplitude Spearman 0.34--0.44 на H3 |
| Direction inside frozen regime (07-08--07-10) | DIAGNOSTIC_ONLY | Direction слаб внутри mask |

**Итог:** Direction-постановка стабильно проваливается на всех моделях. Amplitude-сигнал устойчив: Spearman 0.34--0.45 на H3. Перевод amplitude в торговое правило не выполнен.

### 2.8 Fractal0 механика входа (июль 2026)

**Цель:** проверить, даёт ли сетка входов/выходов вокруг зоны fract0_price устойчивый PF.

**Гипотеза:** limit-order entry в зоне fract0 + ML exit дадут прибыльную систему.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Entry-exit grid M1 (07-21) | RESEARCH_ONLY | PF=2.79, BS_p05=2.51 на val_eval |
| Entry quality filter (07-21) | FAIL | val_eval PF=1.95, BS_p05=0.97 |
| Rich entry quality (07-21) | RESEARCH_HINT | val_eval PF=4.03, BS_p05=3.40 |
| Normalized rerun (07-22) | RESEARCH_HINT | Winner: time_only |
| Internal closure rerun (07-23) | RESEARCH_ONLY | Multiseed 5 seeds, stress cost 3 spreads |
| Locked test (07-24) | candidate_check_required | 11 rules, сильные PF/BS |
| Current history rerun (07-29) | FAIL | Chronology fix уничтожил edge: PF max=0.94 |

**Итог:** Locked test дал сильные числа, но subsequent chronology-fix (исправление same-H1 ML_CLOSE до fill) уничтожил edge: PF max=0.94, kept_candidates=0. Winner -- `time_only` (календарно-временной эффект), не фрактальный сигнал.

### 2.9 MT5 миграция (июль--август 2026)

**Цель:** перенести диагностический execution-контур с MT4 на MT5 Strategy Tester.

**Гипотеза:** MT5 tester даст воспроизводимый execution-контур для независимой проверки кандидатов.

**Ключевые этапы:**

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Feasibility + Nero parity (07-29--07-31) | PASS | match rate 99.05%, direction 99.24% |
| OnTradeTransaction lifecycle (07-31) | PASS | 269 positions, UNEXPLAINED=0 |
| Batch selection 32 runs (07-31) | BATCH_NO_WINNER | 11 eligible, best PF=1.23, BS_p05=0.89 |
| Timing contract (08-01) | PASS | 32/32 signal files, 0 violations |
| Fill-rate probe (08-01) | DIAGNOSTIC_ONLY | 99.2% OPEN_FAILED -- single-position policy |
| Multi-position closeout (08-03) | DIAGNOSTIC_ONLY | max=1 parity 32/32; max=64 ~9.6x placements |
| Position-ordinal PnL (08-10) | DIAGNOSTIC_ONLY | Non-monotonic: ord1 PF=1.013, ord5+=3.205 |

**Итог:** MT5-контур построен и работает для диагностики. Batch из 32 кандидатов не дал ни одного с BS_p05 > 1.0. Fill-rate probe показал, что 99.2% OPEN_FAILED -- single-position policy, не broker no-fill.

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

### 3.3 Take/Skip v2 original_plus_path

- **Метрика до:** original_baseline test PF=49.58, 8.4 trades/yr
- **Метрика после:** +path: PF=38.78, 10.2 trades/yr, neg_years=0
- **Размер выборки:** 29 сделок MT4
- **Вердикт:** PASS -- больше сделок при сохранении PF
- **MT4:** TrailATR=8, TP=0: PF=23.79, net=22294

### 3.4 Signal Path Atlas + fav_3_vs_12 фильтр

- **Метрика до:** "слабый drift", PF~1.0 на медиане
- **Метрика после:** PF=1.78 на 84 holdout сделках с фильтром fav_3_vs_12 <= 0.653
- **Размер выборки:** 84 holdout сделки
- **Вердикт:** PASS как research instrument; FAIL как standalone система

### 3.5 MT5 execution infrastructure

- **Метрика до:** нет MT5-контура
- **Метрика после:** 32/32 candidates с timing contract, 0 violations
- **Размер выборки:** 32 batch runs, multi-position parity 32/32
- **Вердикт:** PASS как диагностический инструмент

### 3.6 Amplitude prediction (H3/H6)

- **Метрика до:** нет amplitude baseline
- **Метрика после:** Spearman 0.34--0.80 на H3/H6, устойчив на Ridge и XGBoost
- **Размер выборки:** 63006 Nero rows, 5 профилей, 5 model families
- **Вердикт:** PASS как диагностический сигнал; FAIL как торговое правило (не переведён)

---

## 4. Что не работает

### 4.1 Direction prediction из фрактальных признаков

- **Что пробовали:** 3-class RF/HGB/LR, binary RF, Transformer encoder, direct bar model, causal surrogate, direction-only TB
- **Числа:** test win rate=50.5% (случайный), SELL PF=0.618, rebuild test PF=0.99, SeqPF разброс 0.68--4728, TB direction-only PF=1.113 с 3 отрицательными годами
- **Почему:** фрактальные признаки несут информацию об амплитуде, но не о направлении. Направление -- coin flip на медиане.

### 4.2 Triple Barrier как production-система

- **Что пробовали:** TB hardening + isotonic calibration + MT4 runtime
- **Числа:** test PF=1.28, 69 сделок; 2023 PF=0.55, 2026 PF=0.00
- **Почему:** regime shift между validation (2019--2022 все +) и test. TB-схема не устойчива к смене режима.

### 4.3 Entry-based next open direction

- **Что пробовали:** 10 табличных моделей (XGBoost, LightGBM, CatBoost, Extra Trees, Hist GBM), 4 profile, 4 горизонта
- **Числа:** direction Spearman val_eval=-0.001; amplitude Spearman 0.34->0.44
- **Почему:** постановка "предскажи направление от next open" не извлекает сигнал. Амплитуда предсказывается, но не направление.

### 4.4 Fractal stop breach -> fav -> trade chain

- **Что пробовали:** Stage 1 breach (PASS), Stage 2 fav (FAIL), Stage 4 trade XGBoost, walk-forward
- **Числа:** walk-forward PF=0.73--0.92 на 2023-2026; Stage 2 PF < 1.0; Stage 4 val_eval PF=0.897
- **Почему:** breach предсказывается, но благоприятный ход -- нет. Структурный перелом 2022/2023 уничтожает edge.

### 4.5 fav_3_vs_12 как standalone система

- **Что пробовали:** standalone benchmark с frozen threshold selection
- **Числа:** stable threshold не найден; PF=0.14 (validation), PF=0.31 (test)
- **Почему:** признак работает только как вспомогательный фильтр внутри другой сильной системы, не как самостоятельный источник прибыли.

### 4.6 lib_PIC dual-stream feature training

- **Что пробовали:** dual-stream модель (sequence + engineered), 9 configs
- **Числа:** 9/9 reject; 0 rows с PF>1 при >=6 trades/year
- **Почему:** простое добавление lib_PIC внутрь модели ломает старый прибыльный контур.

### 4.7 Fixed-11 frozen rules после chronology fix

- **Что пробовали:** 11 frozen rules на locked_test, затем chronology fix
- **Числа:** до fix -- сильные PF/BS; после fix -- PF max=0.94, kept=0
- **Почему:** Python execution contract содержал ошибку (same-H1 ML_CLOSE до fill), исправление которой уничтожило весь edge.

### 4.8 Outcome-aligned retraining

- **Что пробовали:** 3 семейства targets (trade_outcome_cls, trade_pnl_reg, signal_archetype_cls)
- **Числа:** ни одно не прошло validation floor + yearly stability
- **Почему:** close-at-12h labels не повторяют реальную MT4 execution.

### 4.9 Raw regression baseline

- **Что пробовали:** 4 архитектуры (BiLSTM, CNN1D, Transformer, Hybrid), Optuna HPO, feature engineering (11->16 признаков), custom asymmetric loss
- **Числа:** лучшая regression Pearson r=0.324 (BiLSTM), PF=0.59; feature engineering не поднял PF выше 0.59
- **Почему:** сырые фрактальные признаки слишком шумны для прямого предсказания.

### 4.10 Python-to-MT4 performance gap

- **Что пробовали:** threshold analysis на OOS (PF=4.50), интеграция с MT4 Strategy Tester, trailing stop, EA-оптимизация
- **Числа:** Python PF=4.50 (MFE-based) vs MT4 PF=0.53 (SL/TP fixed); после trailing stop + оптимизации -- PF=1.03--1.23
- **Почему:** три структурных разрыва: (1) Python считает сырые экскурсии без SL/TP, (2) position blocking теряет 51.3% сигналов, (3) MFE/MAE иллюзия.

---

## 5. Эволюция понимания

**Февраль--март 2026:** Проект начинался с raw regression на 11 признаках (BiLSTM Pearson r=0.324, PF=0.59). Ключевые находки: (1) DirAcc=97.5% -- артефакт abs(target), не реальный сигнал; (2) Macro F1=0.57 обманчив при 95% neutral классе; (3) seq_len=20 оптимально -- "старые" данные шум; (4) Up/Dn direction-independent таргеты подняли r с 0.32 до 0.43. Переход к MT4 Strategy Tester выявил структурный разрыв: Python PF=4.50 vs MT4 PF=0.53 из-за look-ahead bias, position blocking (51.3%) и MFE/MAE иллюзии. Trailing stop + EA-оптимизация подняли MT4 PF до 1.23, но ниже порога 1.3.

**Апрель 2026:** Signal Path Atlas совершил парадигмальный сдвиг: медианный сигнал -- монетка (возврат -0.064 ATR за 12 баров). Двумодальная структура: 64% провал, 36% плоский drift. Задача переформулирована: от "как войти" к "какие сигналы торговать". Entry path v1 + quantile layer показали сильный отбор (PF=8.18). Take/skip v2 подтвердил, что бинарное решение "брать/не брать" работает лучше, чем regression target.

**Май 2026:** Direct direction rebuild и audit показали, что фрактальные признаки не несут direction-сигнала. Test win rate 50.5% -- случайный. Это закрыло целую ветку исследований.

**Июнь 2026:** Fractal stop breach chain провалилась на торговом слое. Walk-forward показал структурный перелом 2022/2023. Regression Up/Dn подтвердил силу коротких горизонтов (H3/H6), но не дал торгового правила. Structural field ablation выявила доминирование time_only.

**Июль 2026:** Entry-based tabular models окончательно закрыли direction. Fixed-11 locked test дал сильные числа, но chronology fix уничтожил edge (PF max=0.94). Stage 6 feature families не дали устойчивого сигнала.

**Август 2026:** MT5 batch -- BATCH_NO_WINNER. Fill-rate probe: проблема не в broker no-fill, а в single-position policy. Position-ordinal PnL показал non-monotonic pattern.

**Главные изменения убеждений:**

1. "Raw regression" -> "Up/Dn direction-independent targets" (март)
2. "Python PF=4.50" -> "MT4 PF=0.53: execution gap" (март)
3. "Macro F1" -> "обманчив при 95% neutral" (февраль)
4. "DirAcc=97.5%" -> "артефакт abs(target)" (март)
5. "seq_len=100" -> "seq_len=20 оптимально" (март)
6. "Слабый drift" -> "монетка на медиане" (апрель, Atlas Readout)
7. "Direction из фракталов" -> "только amplitude, не direction" (май--июль)
8. "Regression target" -> "binary take/skip лучше" (апрель)
9. "Pullback entry" -> "механика, не архетип" (апрель, Atlas Readout)
10. "ATR квартили" -> "нестационарны, не использовать" (апрель)
11. "Time-only edge" -> "возможно режимный эффект" (июль)
12. "Structural fields" -> "time_only доминирует" (июнь)
13. "H12 price action" -> "range_w1_atr -- артефакт" (июнь)

---

## 6. Нерешённые проблемы

### 6.1 Forward validation отсутствует

**Что известно:** entry_path_v1_quantile frozen rule готов, scaffold для forward validation написан, но нет strictly-forward prediction CSV после production decision.

**Что нужно выяснить:** Держится ли PF=8.18 на новых данных после 2025-11 (конец test периода).

**Предлагаемый подход:** Запустить production inference на новых данных, собрать forward prediction CSV, дождаться накопления 30+ сделок для первого честного forward verdict.

### 6.2 Bootstrap CI для MT4-режимов

**Что известно:** MT4-режимы дают высокие PF (3.77--51.95), но bootstrap CI не построен ни для одного из них.

**Что нужно выяснить:** Нижняя граница 95% CI > 1.0?

**Предлагаемый подход:** Block bootstrap по daily PnL для каждого MT4-режима (quality, frequency, original_plus_path). Минимум 200 repeats.

### 6.3 Малое число сделок

**Что известно:** Все сильные результаты -- на 20--96 сделках. MT5 batch: single-position policy ограничивает число сделок.

**Что нужно выяснить:** Достаточно ли 48 сделок для статистически значимого вывода о PF > 1.3?

**Предлагаемый подход:** CI методами для малых выборок + anchor expansion (уже дал 96 сделок).

### 6.4 Cross-instrument перенос

**Что известно:** EURUSD/GBPUSD провалились. XAGUSD/USDCHF частично поддержали.

**Что нужно выяснить:** Можно ли построить instrument-specific системы или нужен fundamentally другой подход для major pairs?

**Предлагаемый подход:** Сначала подтвердить устойчивость внутри XAUUSD, потом проверять перенос.

### 6.5 Time-only edge

**Что известно:** Normalized rich-entry search выбрал `time_only` как winner. Calendar permutation importance показывает устойчивый эффект.

**Что нужно выяснить:** Это режимный фильтр (время суток / день недели) или артефакт данных?

**Предлагаемый подход:** Отдельный PARKED research direction. Требуется заранее заданный план без нового выбора по locked_test.

### 6.6 PF > 1.0 vs BS_p05 < 1.0 в MT5 batch

**Что известно:** 11 eligible кандидатов имеют PF > 1.0, но все BS_p05 < 1.0. Position-ordinal PnL показал non-monotonic pattern (ordinal 5+: PF=3.205, ordinal 1: PF=1.013).

**Что нужно выяснить:** Почему PF > 1.0 сосуществует с BS_p05 < 1.0? Является ли это следствием low trade count noise?

**Предлагаемый подход:** Frozen probe plan targeting entry mechanics and trade-count consolidation. Accept single-position policy as design constraint.

---

## 7. Накопленные ограничения

### Данные

- **Один инструмент:** XAUUSD H1 только. Cross-instrument не подтверждён.
- **Один провайдер:** MetaQuotes/Alpari. Provider drift проверен, но не является полной заменой forward validation.
- **Конечный объём:** 63006 Nero rows, sequential split 44104/9451/9451. 2026 секция -- только 1162 rows.
- **M5 OHLC:** доступен только для execution ordering, не для обучения.

### Модели

- **Direction signal отсутствует:** Фрактальные признаки не предсказывают направление. Все direction-модели дают win rate ~50%.
- **Amplitude signal есть, но не переводим в торговлю:** Spearman 0.34--0.80, но нет устойчивого правила "когда торговать" на основании amplitude.
- **Time-only edge:** Возможно режимный эффект, не фрактальный сигнал. Не может быть использован для выбора trading parameters.

### Пайплайн

- **Нет forward data:** Production inference не запущен. Forward validation scaffold готов, но данных нет.
- **MT5 batch event files:** 30/32 runs первоначально не дали event files (LiveUpdate interference). Перезапуск решил проблему, но full runtime rerun не выполнен.
- **Single-position policy:** MT5 tester блокирует 99.2% сигналов из-за открытой позиции. Это design constraint, не bug.

### Методология

- **Множественное тестирование:** Не закрыто для большинства DIAGNOSTIC_ONLY этапов. 75--480 metric comparisons без коррекции.
- **SeqPF невалиден:** Shuffle-тест показал разброс 0.68--4728. Не может использоваться как gate metric.
- **locked_test protocol:** Строгие правила запрета нового выбора. Все frozen rules должны быть зафиксированы до открытия locked_test.
- **val_select/val_eval split:** Введён для предотвращения peeking, но ограничивает силу выводов до DIAGNOSTIC_ONLY без полного gate.

---

## 8. Рекомендации

### Что пробовать дальше

1. **Forward data collection (приоритет 1).** Запустить production inference на entry_path_v1_quantile и take/skip v2 quality. Собрать 30+ сделок для первого forward verdict. Обоснование: это единственный способ перевести лучшие системы из статуса "frozen test" в "confirmed".

2. **Bootstrap CI для MT4-режимов (приоритет 2).** Block bootstrap по daily PnL для quality, frequency, original_plus_path. Обоснование: без CI нельзя утверждать, что PF > 1.3 статистически значим.

3. **Portfolio-layer (приоритет 3).** quality + entry_path_v1_quantile как основа. frequency или original_plus_path как третий sleeve (не обе). Обоснование: portfolio analysis показал complementary пары (daily corr -0.24 -- -0.33).

4. **MT5 entry mechanics probe (приоритет 4).** Понять, почему PF > 1.0 сосуществует с BS_p05 < 1.0. Обоснование: это ключ к пониманию статистической значимости результатов.

5. **Amplitude-based trading (приоритет 5, исследовательский).** Отдельный bounded plan: amplitude как target, не direction. Заранее зафиксировать movement filter, horizon, запрет direction. Обоснование: amplitude Spearman 0.34--0.80 -- единственный устойчивый сигнал.

### Что закрыть окончательно

1. **Direction prediction из фрактальных признаков.** Закрыто. Три независимых проверки (rebuild, transformer, entry-based tabular) дали win rate ~50%. Дальнейшие попытки -- переобучение.

2. **Triple Barrier как production-система.** Закрыто. Regime shift 2022/2023, PF=0.00 на 2026. Пересмотр только после накопления forward-данных post-2026-06.

3. **fav_3_vs_12 как standalone система.** Закрыто. Threshold не найден, PF=0.14--0.31.

4. **Fractal stop breach -> fav -> trade chain.** Закрыто. Walk-forward показал структурный перелом. Stage 2 PF < 1.0.

5. **Outcome-aligned retraining с close-at-12h labels.** Закрыто. Labels не повторяют реальную execution.

6. **Entry-based next open direction (табличный).** Закрыто. 10 моделей, все провалили direction gates.

7. **Stage 6 feature families.** Закрыто. range_w1_atr -- артефакт, geometry не даёт сигнала.

8. **Structural field ablation как источник торгового сигнала.** Закрыто. time_only доминирует -- режимный эффект.

### Приоритеты на следующий квартал

| Приоритет | Направление | Ожидаемый результат |
|-----------|-------------|---------------------|
| 1 | Forward data collection | First forward verdict (confirmed/watch/revisit) |
| 2 | Bootstrap CI для MT4 | Lower bound > 1.0 или явный провал |
| 3 | Portfolio-layer | Combined PF + CI на forward данных |
| 4 | MT5 entry mechanics probe | Понимание PF > 1.0 vs BS_p05 < 1.0 |
| 5 | Time-only regime (PARKED) | Отделить режимный эффект от фрактального |

---

*Документ сформирован на основе 100+ отчётов в `docs/reports/` и `ML/reports/`, записей CHANGELOG.md за февраль--август 2026, wiki-страниц в `wiki/research/`, roadmap и CONTEXT_HANDOFF.md.*
