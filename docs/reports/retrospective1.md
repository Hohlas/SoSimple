# Ретроспектива проекта SoSimple

> Период: июль 2025 -- август 2026
> Дата формирования: август 2026
> Порог успеха: PF >= 1.3 на out-of-sample с учётом спреда и проскальзываний,
> подтверждённый bootstrap CI (нижняя граница > 1.0)

---

## 1. Вердикт по проекту

Порог успеха **не достигнут**. Ни одна из исследованных систем не показала устойчивый PF >= 1.3 с нижней границей bootstrap CI > 1.0 на строгом out-of-sample периоде с полным учётом транзакционных издержек. Главная причина -- отсутствие переносимого directional-сигнала: фрактальные признаки предсказывают амплитуду движения, но не его направление. Все системы с высоким PF на исторических данных либо опирались на малые выборки (20--96 сделок), либо теряли прибыльность при переходе к forward-данным, смене провайдера или chronology-fix. Наиболее сильная линия (`entry_path_v1_quantile`, PF=8.18 на 48 сделках test) остаётся неподтверждённой на strictly-forward данных. MT5 batch из 32 кандидатов дал BATCH_NO_WINNER: все 11 eligible имеют PF > 1.0, но BS_p05 < 1.0.

---

## 2. Направления исследований

### 2.1 Regression Up/Dn foundation

**Цель:** проверить, предсказывают ли top-level `up_*/dn_*` чистую основу для регрессионной постановки без привязки к breach/TP/SL.

**Гипотеза:** регрессия на будущие величины favorable/adverse movement даст устойчивый сигнал для торгового решения.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Target Foundation (06-30) | DIAGNOSTIC_ONLY | structure_full H3: Spearman 0.76--0.80, improvement 0.47 |
| Ratio Audit (07-01) | DIAGNOSTIC_ONLY | log_ratio подтверждён |
| Already Moved Audit (07-02) | DIAGNOSTIC_ONLY | Часть сигнала -- уже произошедшее движение |
| Price Feature Matrix (07-02) | DIAGNOSTIC_ONLY | Цена входа влияет на target |

**Итог:** Target foundation подтверждён для коротких горизонтов (H3/H6), сигнал не артефакт одной модели (Ridge тоже работает). Но часть сигнала объясняется движением, уже произошедшим до входа. Перевод в торговое правило не выполнен. 75 обучений, 5 профилей, 5 model families, 3 seed.

### 2.2 Entry-based direction search

**Цель:** проверить, можно ли предсказать направление от точки входа на следующем баре (entry-based next open).

**Гипотеза:** табличные модели достаточной мощности извлекут directional сигнал из entry-based постановки.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Next open closeout (07-04) | PIVOT | direction слаб, amplitude сильнее |
| Powerful tabular (07-06) | PIVOT_AMPLITUDE | direction Spearman val_eval=-0.001; amplitude H3 Spearman 0.34->0.44 |
| Movement filter design (07-07) | RESEARCH_ONLY | Фильтр "есть/нет движение" |
| Movement filter freeze (07-08) | FROZEN | Заморожен для следующего плана |
| Sequence transformer (07-07) | DIAGNOSTIC_ONLY | Последовательное представление |
| Amplitude movement regime (07-07) | DIAGNOSTIC_ONLY | Amplitude trace подтверждён |
| Direction inside frozen regime (07-08, 07-09, 07-10) | DIAGNOSTIC_ONLY | Direction внутри masked regime остаётся слабым |

**Итог:** Direction-постановка в entry-based контуре стабильно проваливается на всех моделях (XGBoost, LightGBM, CatBoost, Extra Trees, Hist GBM). Amplitude-сигнал устойчив: Spearman 0.34--0.45 на H3. Перевод amplitude в торговое правило не выполнен.

### 2.3 Movement regime and amplitude

**Цель:** понять, предсказывается ли режим "есть движение / нет движения" и амплитуда этого движения.

**Гипотеза:** фильтрация сигналов по режиму движения даст устойчивый торговый слой.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Entry-based amplitude movement (07-07) | DIAGNOSTIC_ONLY | Amplitude Spearman 0.34--0.44 на H3 |
| Movement filter freeze (07-08) | FROZEN | Заморожен |
| Direction inside frozen mask (07-08) | DIAGNOSTIC_ONLY | Direction слаб внутри mask |
| Rich features inside mask (07-09) | DIAGNOSTIC_ONLY | Богатые признаки не улучшили direction |
| Narrow replication (07-10) | DIAGNOSTIC_ONLY | Подтверждение: direction остаётся coin flip |

**Итог:** Amplitude предсказывается устойчиво, direction -- нет. Режим "замороженных" сигналов (без движения) хорошо отделяется, но внутри него направление остаётся случайным.

### 2.4 Fractal0 entry/exit grid

**Цель:** проверить, даёт ли сетка входов/выходов вокруг зоны fract0_price устойчивый PF.

**Гипотеза:** limit-order entry в зоне fract0 + ML exit дадут прибыльную систему.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Fractal0 price entry oracle (07-10) | DIAGNOSTIC_ONLY | Oracle-preflight механики |
| Entry-exit grid M1 (07-21) | RESEARCH_ONLY | PF=2.79, BS_p05=2.51 на val_eval |
| Entry quality filter (07-21) | FAIL | val_eval PF=1.95, BS_p05=0.97 |
| Rich entry quality (07-21) | RESEARCH_HINT | val_eval PF=4.03, BS_p05=3.40 |
| Stop grid M5 (07-21) | RESEARCH_ONLY | M5-версия с расширенными данными |
| Normalized rerun (07-22) | RESEARCH_HINT | Winner: time_only |

**Итог:** Сетка дала сильные числа на val_eval, но winner -- `time_only` (календарно-временной эффект), не фрактальный сигнал. Перевод в торговое правило не завершён.

### 2.5 Fixed-11 leaderboard

**Цель:** проверить 11 frozen normalized rich-entry правил на locked_test периоде 2022-12 -- 2026-06.

**Гипотеза:** frozen rules покажут PF > 1.0 с BS_p05 > 1.0 на locked_test.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Internal closure rerun (07-23) | RESEARCH_ONLY | Multiseed 5 seeds, stress cost 3 spreads |
| Locked test (07-24) | candidate_check_required | 11 rules, сильные PF/BS |
| MT4 parity + chronology audit (07-27--07-29) | FAIL | Fill-chronology audit нашёл ошибку |
| Current history rerun (07-29) | FAIL | Chronology fix уничтожил edge: PF max=0.94 |

**Итог:** Locked test дал сильные числа, но subsequent chronology-fix уничтожил edge: PF max=0.94, kept_candidates=0. Positive locked-test chain invalidated. Это ключевой момент: исправление ошибки исполнения (same-H1 ML_CLOSE до fill) полностью убрало прибыльность.

### 2.6 Fractal Stop breach

**Цель:** проверить цепочку breach -> fav -> trade для предсказания пробоя фрактального уровня.

**Гипотеза:** цепочка breach -> fav -> trade даст устойчивый PF > 1.3.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Stage 1: Breach (06-10) | PASS (диагност.) | Пробой предсказывается |
| Stage 2: Fav (06-10) | FAIL | PF < 1.0 на canonical spread |
| Stage 4: Trade XGBoost (06-11) | FAIL | val_eval PF=0.897 |
| Walk-forward (06-15) | FAIL | PF=0.84--0.92 на 2023-2026 |
| Stage 5: Transformer (06-17) | FAIL | Preprocessing bug; после исправления -- без улучшения |
| Signal stationarity (06-24) | DIAGNOSTIC_ONLY | Сигнал деградирует на 2023+ |

**Итог:** Breach предсказывается, но торговый слой (fav + trade) не работает. Walk-forward показал структурный перелом 2022/2023: модель прибыльна на 2017--2022 (PF=1.42--1.91), убыточна на 2023-2026 (PF=0.73--0.90). Transformer не преодолел ceiling табличных моделей (нормализация выявила, что `price` доминировал в attention). Signal stationarity показала деградацию на 2023+.

### 2.7 Structural field ablation

**Цель:** проверить, какие из 9 структурных полей фрактала дают устойчивый добавочный сигнал сверх clock-only baseline.

**Гипотеза:** структурные поля (direction/front/back/strong/break/reverse/power/count/impulse) дают добавочный сигнал.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Stage 5.1 structural field (06-24) | DIAGNOSTIC_ONLY | 20 профилей x 2 цели x 3 seed = 120 моделей |
| Stage 5.1b Up/Dn field ablation (06-25) | DIAGNOSTIC_ONLY | Подтверждение на Up/Dn targets |
| Stage 5.2 time-to-breach regression (06-25) | DIAGNOSTIC_ONLY | Время до пробоя |
| Stage 5.3 time-to-breach target reformulation (06-26) | DIAGNOSTIC_ONLY | Реформулировка target |
| Stage 5.4 fast price ATR ablation (06-29) | DIAGNOSTIC_ONLY | Price/ATR не главный источник |

**Итог:** `time_only` (4 clock-признака: hour_sin, hour_cos, dow_sin, dow_cos) даёт сравнимый или лучший сигнал, чем structure_full. Это указывает на режимный календарно-временной эффект, а не фрактальный сигнал. Price и ATR не выглядят главным источником.

### 2.8 Stage 6 feature families

**Цель:** проверить новые семейства признаков (H12 relative geometry, price action, H6 parity) для TP/SL touch prediction.

**Гипотеза:** недавнее OHLC price action и локальная геометрия фракталов улучшают предсказание H12 TP/SL touch.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Stage 6.0 outcome-based TB (06-29) | DIAGNOSTIC_ONLY | Outcome-based triple barrier |
| Stage 6.1 H12 relative geometry (06-29) | DIAGNOSTIC_ONLY | Локальная геометрия не даёт сигнала |
| Stage 6.2 H12 price action (06-30) | DIAGNOSTIC_ONLY | `range_w1_atr` доминирует, но permutation gate провален |
| Stage 6.2 range W1 postmortem (06-30) | DIAGNOSTIC_ONLY | `range_w1_atr` -- артефакт масштаба |
| Stage 6.3 H6 parity check (06-30) | DIAGNOSTIC_ONLY | H6 не дал parity |

**Итог:** Новые семейства признаков не дали устойчивого торгового сигнала. `range_w1_atr` доминировал в важности, но не прошёл permutation gate. Локальная геометрия фракталов не информативна для H12 TP/SL touch.

### 2.9 Direction prediction

**Цель:** построить модель, предсказывающую BUY/SELL направление непосредственно из фрактальных признаков.

**Гипотеза:** binary BUY/SELL классификатор на фрактальных признаках даст PF > 1.3 на OOS.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Direct Direction Improvement (05-15) | DIAGNOSTIC | Binary RF: test PF=1.226, BUY PF=1.904, SELL PF=0.618 |
| Chain Audit (05-18) | FAIL | 6 ошибок в chain |
| Direct Direction Rebuild (05-21) | FAIL | Test PF=0.99, BUY win rate=50.5% |
| Transformer Direction (05-21) | FAIL | Trail PF=2.41 на 58 сделках, 0.6% utilisation |
| Direction-only TB (06-03) | FAIL | Лучший TB PF=1.113, 3 отрицательных года |

**Итог:** Направление закрыто окончательно. Фрактальные признаки не несут direction-сигнала. Test win rate 50.5% неотличим от случайного. SeqPF признан невалидной метрикой (shuffle-тест: разброс 0.68--4728 при PF=1.10). Diagnostic edge_6 PF=6.427 не переводится в торговое правило.

### 2.10 Entry path v1 + Quantile layer

**Цель:** построить слой "торговать / не торговать" поверх regression_updn базы, используя quantile-головы для отбора лучших входов.

**Гипотеза:** quantile-layer (ret_24_q10, ret_24_q90) поверх entry_path_v1 даст устойчивый PF > 2.0.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Baseline (04-08) | PASS | ret_pearson_r=0.245 |
| Loss Weighting (04-09) | PASS | test PF=4.29, 44 сделки |
| Quantile Layer (04-10) | PASS | test: 24 сделки, PF=inf |
| Multi-seed (04-11) | PASS | 5/5 seeds, median PF=inf |
| Status Decision + MT4 Parity (04-12) | PASS | N=48, PF=8.18; MT4 20/20, PF=11.91 |
| Forward Validation (04-13) | WATCH | no_forward_data, 0 trades |
| Cross-Instrument (04-24) | MIXED | XAGUSD supported, EURUSD/GBPUSD failed |
| Live-safe reproducibility (05-07) | PASS | CPU/GPU parity подтверждена |
| Fav composition (04-13) | FAIL | No uplift, worsens yearly stability |

**Итог:** Сильнейшая линия проекта. PF=8.18 на 48 сделках test, подтверждён MT4 parity (20/20, PF=11.91 в деньгах). Multi-seed устойчив. Добавление fav_3_vs_12 поверх quantile не улучшило результат. Но: (1) малая выборка 48 сделок, (2) forward validation не выполнен (нет данных), (3) cross-instrument перенос ограничен (EURUSD/GBPUSD провалены).

### 2.11 Take/skip trailing stop

**Цель:** проверить, даёт ли бинарное решение take/skip поверх trailing-stop логики устойчивый PF > 1.3.

**Гипотеза:** модель, решающая "брать ли вход при trailing-stop", даст более устойчивый результат.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Take/Skip v1 Matrix (04-17) | FAIL | Все reject, PF < 1.0 |
| Take/Skip v2 Scaffold (04-17) | PASS | Validation PF=6.39, 24 сделки |
| Quality Follow-up (04-18) | PASS | test PF=39.74, 41 сделок |
| Frequency + Sweet Spot (04-18) | PASS | 16.4 trades/yr, PF=13.12, neg_years=0 |
| MT4 Trailing (04-18) | PASS | TrailATR=8, TP=0: PF=3.77, 56 сделок |
| Execution Policy v2 (04-19) | PASS | quality MT4: PF=51.95, 20 сделок |
| lib_PIC Feature Training (04-20) | FAIL | 9/9 reject, 0 rows с PF>1 |
| Original Contour Ablation (04-20) | PASS | +path: 10.2 trades/yr, PF=38.78 |
| MT4 Confirmation (04-22) | PASS | 29 сделок, PF=23.79 |

**Итог:** Вторая по силе линия. Take/skip v2 дал несколько MT4-подтверждённых режимов: quality (PF=39.74--51.95), frequency (PF=3.77--7.18), original_plus_path (PF=23.79--38.78). Все -- на малых выборках (20--96 сделок). Bootstrap CI не построен для MT4-режимов. lib_PIC dual-stream feature training провалился (9/9 reject).

### 2.12 Signal research and atlas

**Цель:** понять постсигнальную геометрию цены и найти фильтры качества сигнала.

**Гипотеза:** signal quality filter по `fav_3_vs_12` отберёт прибыльные сигналы.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Variant 2 (04-01) | DIAGNOSTIC | PF_12=1.95, BUY>SELL |
| Variant 3 Prep (04-02) | DIAGNOSTIC | ATR Q4 нестабилен |
| Variant 3 (04-02) | DIAGNOSTIC | Pullback улучшает, но и отрицательные контроли |
| Atlas Readout (04-04) | PASS | Медиана = монетка, двумодальная структура |
| Quality Filter (04-04) | PASS | fav_3_vs_12 <= 0.653, PF=1.78 на 84 holdout |
| Archetype Bridge (04-04) | PASS | Единственный validated фильтр |
| Fav Standalone (04-13) | FAIL | threshold не найден, PF=0.14--0.31 |

**Итог:** Парадигмальный сдвиг: "слабый drift" -> "монетка на медиане, двумодальная структура". Задача переформулирована от "как войти" к "какие сигналы торговать". `fav_3_vs_12` полезен как вспомогательный фактор, но не как самостоятельная система.

### 2.13 Triple Barrier

**Цель:** построить TB-схему вне MT4 с isotonic calibration и проверить на test.

**Гипотеза:** TB с first-touch labeling даст устойчивый PF > 1.3.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Hardening (04-08) | PASS | Test PF=1.11, 253 сделки |
| Runtime Verdict (04-08) | PASS | MT4 PF=1.27, SL/TP match 93.8% |
| MT4 Verdict (04-12) | FAIL | Gate: PF=1.28 < 2.0, 2 negative years |
| TB Verdict (04-12) | FAIL | 2023 PF=0.55, 2026 PF=0.00 |

**Итог:** Закрыто. TB-схема показала regime shift между validation (все 4 года положительные) и test (2023 PF=0.55, 2026 PF=0.00). Gate провален: PF=1.28 < 2.0, negative_year_slices=2.

### 2.14 Live-safe and execution

**Цель:** обеспечить live-execution совместимость и воспроизводимость ML-систем.

**Гипотеза:** live-safe audit подтвердит production-readiness лучших систем.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Live-safe ML audit (05-05) | PASS | Feature contract проверен |
| CPU/GPU reproducibility (05-07) | PASS | Паритет подтверждён |
| Entry path MT4 parity (05-07) | PASS | 20/20 сделок |
| Signal export parity (04-22) | PASS | Export подтверждён |
| Online inference contract (04-29) | PASS | Hardening |

**Итог:** Live-safe контур построен и работает. CPU/GPU reproducibility подтверждена. MT4 parity для entry_path_v1_quantile: 20/20 сделок. Signal export parity подтверждён.

### 2.15 MT5 migration

**Цель:** перенести диагностический execution-контур с MT4 на MT5 Strategy Tester.

**Гипотеза:** MT5 tester даст воспроизводимый execution-контур для независимой проверки кандидатов.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Feasibility + Nero parity (07-29--07-31) | PASS | match rate 99.05%, direction 99.24% |
| OnTradeTransaction lifecycle (07-31) | PASS | 269 positions, UNEXPLAINED=0 |
| Batch selection 32 runs (07-31) | BATCH_NO_WINNER | 11 eligible, best PF=1.23, BS_p05=0.89 |
| Timing contract (08-01) | PASS | 32/32 signal files, 0 violations |
| Fill-rate probe (08-01) | DIAGNOSTIC_ONLY | Fill rate NOT primary cause; 99.2% single-position policy |
| Full batch 32x2 (08-07) | DIAGNOSTIC_ONLY | max=1 паритет 32/32; max=64 ~9.6x placements |
| Position-ordinal PnL (08-10) | DIAGNOSTIC_ONLY | Non-monotonic: ord1 PF=1.013, ord3=0.854, ord5+=3.205 |

**Итог:** MT5-контур построен и работает для диагностики. Batch из 32 кандидатов не дал ни одного с BS_p05 > 1.0. Fill-rate probe показал, что 99.2% OPEN_FAILED -- single-position policy, не broker no-fill. Position-ordinal PnL показал non-monotonic pattern (ordinal 1: PF=1.013, ordinal 3: PF=0.854, ordinal 5+: PF=3.205).

### 2.16 Early ML baselines and architecture selection (февраль--март 2026)

**Цель:** определить базовую архитектуру нейросети и режим обучения для предсказания фрактальных признаков.

**Гипотеза:** deep learning модели (Transformer, BiLSTM, CNN1D, Hybrid) извлекут торговый сигнал из последовательности фракталов.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| Baseline ML (02-18) | COMPLETED | 5 baselines: Dummy, LogReg, RF, XGBoost, LightGBM |
| Regression mode (02-23) | COMPLETED | HuberLoss, pearson_r early stopping |
| Optuna HPO (02-25) | COMPLETED | Classification (macro F1) + regression (pearson_r) |
| Architecture comparison -- classification (02-27) | COMPLETED | Transformer Macro F1=0.577, но F1(-1)=0.41, F1(1)=0.38 |
| Architecture comparison -- regression (02-27) | COMPLETED | BiLSTM Pearson r=0.324, Transformer r=0.114 |
| Class imbalance trap (02-27) | COMPLETED | Macro F1=0.57 обманчив: F1(0)=0.95, F1(+-1)=0.35 |
| Project audit (03-10) | COMPLETED | DirAcc=97.5% -- артефакт abs(target), не leakage |
| Reproducibility (03-11) | COMPLETED | Seed stability: max diff=0.00000, std=0.00228 |
| Optuna BiLSTM regression (03-12) | COMPLETED | Pearson r: 0.323 -> 0.342 |
| Ablation study (03-12) | COMPLETED | seq_len=20 оптимально (r=0.328 vs 0.324 при 100) |
| Feature engineering (03-12) | FAIL | 16 признаков, PF=0.59 |
| Custom trading loss (03-16) | COMPLETED | Asymmetric loss не помог: "основной лимит -- в слабых признаках" |
| Up/Dn targets (03-18) | COMPLETED | direction-independent таргеты up_12..dn_48 |
| Multi-task regression (03-19) | COMPLETED | Transformer r=0.427; up_12=0.502, dn_12=0.538 |
| OOS evaluation + threshold (03-19) | COMPLETED | H12 PF=4.50 (val), θ=2.665 |
| Threshold analysis H12/H24/H48 (03-19) | COMPLETED | H12 PF=2.95, H24 PF=2.34, H48 PF=1.98 (val) |
| Phase B.1: 3H/6H targets (03-31) | FAIL | Pearson r: 0.433->0.565 (+30%), но PF: 1.20->0.87 |
| Directional asymmetric loss (03-31) | FAIL | α=2.5: PF=1.04; α=5.0: PF=0.97 (убыточно) |
| ATR-index bugfix (03-31) | COMPLETED | PF восстановлен 1.24 после исправления сдвига индекса |

**Итог:** Фундаментальный этап: определена оптимальная архитектура (Transformer/BiLSTM), оптимальная длина последовательности (seq_len=20), режим регрессии (HuberLoss, Up/Dn targets). Pearson r вырос с 0.11 (Transformer regression) до 0.43 (Transformer regression_updn). Threshold analysis на validation дал PF=2.95 (H12), но это Python MFE-based метрика без SL/TP. Feature engineering (11->16 признаков) не поднял PF выше 0.59 в регрессии. Directional asymmetric loss провален. Class imbalance: Macro F1 обманчив при 95% neutral.

### 2.17 MT4 integration and Strategy Tester diagnostics (март 2026)

**Цель:** подключить ML-модель к MT4 Strategy Tester и оценить реальную торговую прибыльность.

**Гипотеза:** Python OOS PF=4.50 транслируется в прибыльную MT4-систему с PF > 1.3.

| Этап | Вердикт | Метрики |
|------|---------|---------|
| MT4<->ML integration (03-20) | PASS | Файловый обмен, 58540 signals loaded |
| Conformal Prediction (03-20) | COMPLETED | Не добавляет ценности при θ=2.665 |
| MT4 Strategy Tester debug (03-21) | COMPLETED | WR~46%, PF<1 при R:R=1:1 |
| Asymmetric R:R diagnostics (03-22) | DIAGNOSTIC_ONLY | Python PF=4.50 vs MT4 PF<1: look-ahead bias + position blocking 51.3% |
| signal_tracer v2.0 (03-24) | COMPLETED | MFE/MAE иллюзия: 33 сделки -- Python TP, MT4 SL |
| Per-row updn denorm (03-25) | COMPLETED | Исправлена классификация TP/SL/TIMEOUT |
| 922-trade analysis (03-26) | DIAGNOSTIC_ONLY | PF(SL/TP)=0.53; ratio>4.5 -- убыточная зона |
| Trailing stop + optimization (03-23) | PASS | WR: 34.55%->54.07%; лучший PF=1.03, 922 сделки |
| Triple Barrier classification (03-23) | COMPLETED | Val AUC=0.717, transfer learning обязателен |
| EA optimization Phase A (03-27) | PASS | PF: 0.53->1.23; ML_MaxRatio=4.5 |

**Итог:** Ключевой разрыв: Python OOS PF=4.50 (MFE-based, без SL/TP) vs MT4 PF=0.53 (фиксированные SL/TP). Причины: (1) look-ahead bias в Python -- считает сырые экскурсии без учёта SL/TP, (2) position blocking -- 51.3% сигналов теряются из-за уже открытой позиции, (3) MFE/MAE иллюзия -- Python видит TP достижимым, MT4 выбивает SL первым. Trailing stop поднял WR с 34.55% до 54.07%. EA-оптимизация подняла PF до 1.23, но это ниже порога 1.3. Conformal Prediction не добавил ценности при агрессивном θ.

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
- **Вердикт:** PASS как research instrument

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
- **Почему:** фрактальные признаки несут информацию об амплитуде, но не о направлении. Направление -- coin flip на медиане. Diagnostic edge_6 PF=6.427 не переводится в торговое правило.

### 4.2 Triple Barrier как production-система

- **Что пробовали:** TB hardening + isotonic calibration + MT4 runtime
- **Числа:** test PF=1.28, 69 сделок; 2023 PF=0.55, 2026 PF=0.00
- **Почему:** regime shift между validation (2019--2022 все +) и test. TB-схема не устойчива к смене режима.

### 4.3 Entry-based next open direction

- **Что пробовали:** 10 табличных моделей, 4 profile, 4 горизонта, sequence transformer
- **Числа:** direction Spearman val_eval=-0.001; amplitude Spearman 0.34->0.44
- **Почему:** постановка "предскажи направление от next open" не извлекает сигнал. Амплитуда предсказывается, но не направление.

### 4.4 Fractal stop breach -> fav -> trade chain

- **Что пробовали:** Stage 1 breach (PASS), Stage 2 fav (FAIL), Stage 4 trade XGBoost, walk-forward, Transformer
- **Числа:** walk-forward PF=0.73--0.92 на 2023-2026; Stage 2 PF < 1.0; Stage 4 val_eval PF=0.897
- **Почему:** breach предсказывается, но благоприятный ход -- нет. Структурный перелом 2022/2023 уничтожает edge.

### 4.5 fav_3_vs_12 как standalone система

- **Что пробовали:** standalone benchmark с frozen threshold selection
- **Числа:** stable threshold не найден; PF=0.14 (validation), PF=0.31 (test)
- **Почему:** признак работает только как вспомогательный фильтр внутри другой сильной системы, не как самостоятельный источник прибыли.

### 4.6 lib_PIC dual-stream feature training

- **Что пробовали:** dual-stream модель (sequence + engineered), 9 configs
- **Числа:** 9/9 reject; 0 rows с PF>1 при >=6 trades/year
- **Почему:** простое добавление lib_PIC внутрь модели ломает старый прибыльный контур. Признаки полезнее как внешний фильтр или ablation поверх старого контура.

### 4.7 Fixed-11 frozen rules после chronology fix

- **Что пробовали:** 11 frozen rules на locked_test, затем chronology fix
- **Числа:** до fix -- сильные PF/BS; после fix -- PF max=0.94, kept=0
- **Почему:** Python execution contract содержал ошибку (same-H1 ML_CLOSE до fill), исправление которой уничтожило весь edge.

### 4.8 Outcome-aligned retraining

- **Что пробовали:** 3 семейства targets (trade_outcome_cls, trade_pnl_reg, signal_archetype_cls)
- **Числа:** ни одно не прошло validation floor + yearly stability
- **Почему:** close-at-12h labels не повторяют реальную MT4 execution.

### 4.9 Raw regression baseline (февраль--март 2026)

- **Что пробовали:** 4 архитектуры (BiLSTM, CNN1D, Transformer, Hybrid), Optuna HPO, feature engineering (11->16 признаков), custom asymmetric loss, ablation seq_len
- **Числа:** лучшая regression Pearson r=0.324 (BiLSTM), PF=0.59 при threshold analysis; feature engineering не поднял PF выше 0.59; Optuna поднял r с 0.323 до 0.342
- **Почему:** сырые фрактальные признаки (11 features, 100-барные последовательности) слишком шумны для прямого предсказания. Переход к Up/Dn targets (direction-independent) поднял r до 0.427, но это всё ещё regression, не торговля.

### 4.10 Python-to-MT4 performance gap (март 2026)

- **Что пробовали:** threshold analysis на OOS (PF=4.50), интеграция с MT4 Strategy Tester, trailing stop, EA-оптимизация
- **Числа:** Python PF=4.50 (MFE-based) vs MT4 PF=0.53 (SL/TP fixed); после trailing stop + оптимизации -- PF=1.03--1.23
- **Почему:** три структурных разрыва: (1) Python считает сырые экскурсии без SL/TP, MT4 -- фиксированные уровни; (2) position blocking теряет 51.3% сигналов; (3) MFE/MAE иллюзия -- Python видит TP достижимым, MT4 выбивает SL первым (33 сделки из 922).

---

## 5. Эволюция понимания

**Февраль--март 2026:** Проект начинался с raw regression на 11 признаках (BiLSTM Pearson r=0.324, PF=0.59). Ключевые находки: (1) DirAcc=97.5% -- артефакт abs(target), не реальный сигнал; (2) Macro F1=0.57 обманчив при 95% neutral классе; (3) seq_len=20 оптимально -- "старые" данные шум; (4) Up/Dn direction-independent таргеты подняли r с 0.32 до 0.43. Переход к MT4 Strategy Tester выявил структурный разрыв: Python PF=4.50 vs MT4 PF=0.53 из-за look-ahead bias, position blocking (51.3%) и MFE/MAE иллюзии. Trailing stop + EA-оптимизация подняли MT4 PF до 1.23, но ниже порога 1.3. Это определило вектор апреля: нужен не regression target, а торговый контур с правильной механикой исполнения.

**Апрель 2026:** Проект начинался с гипотезы "слабый положительный drift" (Variant 2). Signal Path Atlas совершил парадигмальный сдвиг: медианный сигнал -- монетка (возврат -0.064 ATR за 12 баров). Двумодальная структура: 64% провал, 36% плоский drift. Задача переформулирована: от "как войти" к "какие сигналы торговать".

**Апрель--май 2026:** Entry path v1 + quantile layer показали сильный отбор (PF=8.18). Take/skip v2 подтвердил, что бинарное решение "брать/не брать" работает лучше, чем regression target. Direct direction rebuild показал win rate 50.5% -- случайный.

**Июнь 2026:** Fractal stop breach chain провалилась на торговом слое. Walk-forward показал структурный перелом 2022/2023. Regression Up/Dn подтвердил силу H3/H6, но не дал торгового правила. Structural field ablation выявила доминирование time_only.

**Июль 2026:** Entry-based tabular models окончательно закрыли direction. Fixed-11 locked test дал сильные числа, но chronology fix уничтожил edge (PF max=0.94). Stage 6 feature families не дали устойчивого сигнала.

**Август 2026:** MT5 batch -- BATCH_NO_WINNER. Fill-rate probe: проблема не в broker no-fill, а в single-position policy. Position-ordinal PnL показал non-monotonic pattern.

**Главные изменения убеждений:**

1. "Raw regression" -> "Up/Dn direction-independent targets" (март, ME-6/ME-8)
2. "Python PF=4.50" -> "MT4 PF=0.53: execution gap, не сила модели" (март, ME-13)
3. "Macro F1" -> "обманчив при 95% neutral" (февраль, class imbalance trap)
4. "DirAcc=97.5%" -> "артефакт abs(target), не реальный сигнал" (март, audit)
5. "seq_len=100" -> "seq_len=20 оптимально, старые данные -- шум" (март, ablation)
6. "Слабый drift" -> "монетка на медиане" (Atlas Readout, апрель)
7. "Direction из фракталов" -> "только amplitude, не direction" (май--июль)
8. "Regression target" -> "binary take/skip лучше" (апрель)
9. "Pullback entry" -> "механика, не архетип" (Atlas Readout)
10. "ATR квартили" -> "нестационарны, не использовать" (Variant 3 Prep)
11. "Time-only edge" -> "возможно режимный эффект, не фрактальный сигнал" (rich entry normalized rerun)
12. "Structural fields" -> "time_only доминирует" (Stage 5.1 ablation)
13. "H12 price action" -> "range_w1_atr -- артефакт" (Stage 6.2 postmortem)

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

**Предлагаемый подход:** Сначала подтвердить устойчивость внутри XAUUSD, потом проверять перенос.

### 6.5 Time-only edge

**Что известно:** Normalized rich-entry search выбрал `time_only` как winner. Stage 5.1 structural field ablation подтвердил, что 4 clock-признака (hour_sin, hour_cos, dow_sin, dow_cos) сравнимы или лучше structure_full. Calendar permutation importance показывает устойчивый эффект.

**Что нужно выяснить:** Это режимный фильтр (время суток / день недели) или артефакт данных?

**Предлагаемый подход:** Отдельный PARKED research direction в roadmap. Требуется заранее заданный план без нового выбора по locked_test.

### 6.6 PF > 1.0 vs BS_p05 < 1.0 в MT5 batch

**Что известно:** 11 eligible кандидатов имеют PF > 1.0, но все BS_p05 < 1.0. Position-ordinal PnL показал non-monotonic pattern (ordinal 5+: PF=3.205, ordinal 1: PF=1.013).

**Что нужно выяснить:** Почему PF > 1.0 сосуществует с BS_p05 < 1.0? Является ли это следствием low trade count noise?

**Предлагаемый подход:** Frozen probe plan targeting entry mechanics and trade-count consolidation. Accept single-position policy as design constraint.

---

## 7. Накопленные ограничения

### Данные

- **Один инструмент:** XAUUSD H1 только. Cross-instrument не подтверждён.
- **Один провайдер:** MetaQuotes/Alpari.
- **Конечный объём:** 63006 Nero rows, sequential split 44104/9451/9451. 2026 -- только 1162 rows.
- **M5 OHLC:** доступен только для execution ordering, не для обучения.

### Модели

- **Direction signal отсутствует:** win rate ~50% на всех моделях.
- **Amplitude signal есть, но не переводим в торговлю:** Spearman 0.34--0.80.
- **Time-only edge:** Возможно режимный эффект, не фрактальный сигнал.

### Пайплайн

- **Нет forward data:** Production inference не запущен.
- **Single-position policy:** MT5 блокирует 99.2% сигналов.
- **Chronology fix:** Python execution contract содержал ошибку, исправление уничтожило fixed11 edge.

### Методология

- **Множественное тестирование:** 75--480 comparisons без коррекции.
- **SeqPF невалиден:** Shuffle-тест: разброс 0.68--4728.
- **locked_test protocol:** Строгие правила запрета нового выбора.

---

## 8. Рекомендации

### Что пробовать дальше

1. **Forward data collection (приоритет 1).** Запустить production inference на entry_path_v1_quantile и take/skip v2 quality. Собрать 30+ сделок для forward verdict.

2. **Bootstrap CI для MT4-режимов (приоритет 2).** Block bootstrap по daily PnL для quality, frequency, original_plus_path.

3. **Portfolio-layer (приоритет 3).** quality + entry_path_v1_quantile как основа, frequency или original_plus_path как третий sleeve. Portfolio analysis: daily corr -0.24 -- -0.33.

4. **MT5 entry mechanics probe (приоритет 4).** Понять, почему PF > 1.0 сосуществует с BS_p05 < 1.0.

5. **Amplitude-based trading (приоритет 5, исследовательский).** Amplitude как target, не direction. Spearman 0.34--0.80 -- единственный устойчивый сигнал.

### Что закрыть окончательно

1. **Direction prediction из фрактальных признаков.** Win rate ~50% на всех моделях.

2. **Triple Barrier как production-система.** Regime shift 2022/2023, PF=0.00 на 2026.

3. **fav_3_vs_12 как standalone система.** Threshold не найден, PF=0.14--0.31.

4. **Fractal stop breach -> fav -> trade chain.** Walk-forward: структурный перелом, Stage 2 PF < 1.0.

5. **Outcome-aligned retraining.** Labels не повторяют реальную execution.

6. **Entry-based next open direction.** 10 моделей, все провалили direction gates.

7. **Stage 6 feature families.** range_w1_atr -- артефакт, geometry не даёт сигнала.

8. **Structural field ablation как источник торгового сигнала.** time_only доминирует -- режимный эффект.

### Приоритеты на следующий квартал

| Приоритет | Направление | Ожидаемый результат |
|-----------|-------------|---------------------|
| 1 | Forward data collection | First forward verdict (confirmed/watch/revisit) |
| 2 | Bootstrap CI для MT4 | Lower bound > 1.0 или явный провал |
| 3 | Portfolio-layer | Combined PF + CI на forward данных |
| 4 | MT5 entry mechanics probe | Понимание PF > 1.0 vs BS_p05 < 1.0 |
| 5 | Time-only regime (PARKED) | Отделить режимный эффект от фрактального |

---

*Документ сформирован на основе 100+ отчётов в `docs/reports/` и `ML/reports/`, записей CHANGELOG.md за июль 2025 -- август 2026, wiki-страниц в `wiki/research/`, roadmap и CONTEXT_HANDOFF.md.*
