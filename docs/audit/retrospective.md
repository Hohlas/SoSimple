# Ретроспектива проекта SoSimple
**Период:** начало проекта — август 2026
**Порог успеха:** PF ≥ 1.3 на out-of-sample с bootstrap CI (нижняя граница > 1.0)

---

## 1. Вердикт по проекту

**Порог успеха не достигнут.** Ни одна система не показала PF ≥ 1.3 на строгом OOS с bootstrap CI > 1.0. Пять ретроспектив (retrospective0–4, август 2026) подтверждают: directional signal не переносим. Главная причина — already-moved проблема: ML-модели захватывают уже произошедшее движение до входа, а не будущее направление. После вычитания already-moved Spearman падает с 0.76–0.80 до 0.29–0.54. Все прибыльные исторические системы (PF до 39.74) используют future-derived данные — leakage делает их метрики неприменимыми для live.

---

## 2. Направления исследований

### 2.1. ML-модели и пороговый анализ

BiLSTM/Transformer регрессия для предсказания направления на горизонтах 12/24/48H. Архитектуры: BiLSTM (Pearson r=0.32, R²=0.10), Transformer на up/dn (r=0.43, R²=0.18). Threshold analysis Transformer H12: **PF=2.95** (val, 2502 сделки), 24H: PF=2.34 (2115), 48H: PF=1.98 (1870). Evaluate test: PF=4.51 (2203 сделки) — но на validation-подобном распределении. Conformal prediction: нет эффекта при θ=2.665. Reproducibility: PASS (seed std=0.0023). **Итог:** модели предсказывают амплитуду (R²=0.10–0.18), directional accuracy ~97.5% — предсказание нейтрального класса. Threshold PF высокие на val, но не переносятся на OOS.

### 2.2. Signal Research и PF uplift

Поиск фильтров и режимов входа вне ML-слоя. Variant 2: базовый PF=1.05 (2603 сигнала), BUY PF_12=1.35. Variant 3: ratio 4-5 × ATR Q4 + pullback **PF=3.69** (36 fills) — PASS, один квалифицированный кандидат. Signal Path Atlas: 31 holdout-наблюдение реплицировано, 45 нет — DIAGNOSTIC_ONLY. Variant 4: `fav_3_vs_12<=0.653` + market **PF=1.78** (84 сделки, holdout) — PASS. PF Uplift Discovery: baseline N=48, PF=8.18; исключить NY: PF→20.28 (N=34) — PASS, три механизма роста. Fav standalone: ни один порог PF≥1.0 — FAIL. Quantile × Fav composition: отрицательный год 2023 (PF=0.48) — FAIL. **Итог:** pullback и multi-horizon filters дают uplift на holdout, но не устойчивы. `fav_3_vs_12` — единственный фильтр, связанный с выигрышным архетипом, но не standalone.

### 2.3. Entry Path и cross-instrument

Entry_path_v1 с trade filter и quantile layer. Baseline: test `ret_pearson_r=0.2450`. Outcome-aligned retraining: val AUC=0.6534, PF<0.2 — FAIL. Trade filter `A @ 7.5%`: test **PF=4.29** (44 сделки, WR=72.7%) — PASS. MT4 parity: 22 сделки, **PF=8.47** — PASS. Quantile `lb_gt_m_q35`: test **PF=8.18** (N=48) — PASS, production-ready. Forward validation: trades=0 — WATCH (нет forward-данных). Frequency: PF=0.22 — FAIL. Cross-instrument: provider drift stable, transfer избирательный (XAGUSD PF=inf, EURUSD failed). CPU/GPU: веса расходятся на ~0.2 — production CPU-only. Live-safe: production baseline median seq PF=2.32, 4/5 >2.0 — PASS. MT4 parity: 26 сделок, **PF=9.03** — PASS. All-rows ranking: PF=0.97 — FAIL. Direct bar model: PF=1.17 val, слабый test — FAIL. Direct direction rebuild: val PF=1.77, test PF=0.99 — FAIL. Transformer direction: лучший BUY PF=1.35 (73 сделки) — FAIL. **Итог:** entry_path_v1 и quantile дают PF 8.18–9.03 на test (26–48 сделок), но не подтверждены forward. Direct direction модели не достигают PF>1.5.

### 2.4. Triple Barrier

TB-разметка с реальным первым касанием барьеров. Hardening: val **PF=1.53** (121 сделка, WR=57.9%), test PF=1.11 (253 сделки). MT4 runtime: PF=1.27 (92 сделки), совпадение TP/SL 93.8% — PASS. Production verdict: val PF=4.33 (28 сделок), test **PF=1.28** (69 сделок, 2 отрицательных года) — FAIL (PF<2.0, 2 убыточных года). **Итог:** TB-схема согласуется с MT4, но test PF=1.11–1.28 не проходит gate.

### 2.5. Take/Skip, trailing stop и feature bank

Track A max-out: PF=0.43–0.48 — FAIL. Trailing stop target: PF<1 — FAIL. Multi-horizon v2: smoke PF=6.39–34.77 — DIAGNOSTIC. Frequency follow-up: quality test **PF=39.74** (8.2 сделок/год), frequency **PF=13.12** (16.4 сделок/год, 0 отрицательных лет) — PASS. Execution Policy V2: quality trail_x8 **PF=55.87** (20 сделок) — PASS. Feature bank: `baseline_clean` R²=0.084 — чистка эффективнее расширения. Feature importance: geometry r2_drop=0.22 (доминирует). Original contour ablation: `original_plus_path_seq50` **PF=38.78** (10.2 сделок/год) — PASS. lib_PIC dual-stream: 0 кандидатов PF>1 — FAIL. **Итог:** quality PF=39.74 и frequency PF=13.12 — высокие метрики, но все системы используют future-derived данные. Geometry — основной источник сигнала, но R² низкий (~0.08).

### 2.6. Online execution и live-safe

Telemetry demo: 495 сигналов в 2025 — контур готов. Online inference contract: legacy checkpoint не production-ready. **Live-Safe ML Audit: все 5 систем FAIL** (future-derived inputs). `quality` PF=39.74 (41 сделка), `frequency` PF=13.12, `entry_path_v1` PF=2.87 (30 сделок) — все исторические артефакты. `entry_path_v1_live_safe`: 25 сделок, **PF=2.34**, WR=68% — прибыльность снизилась, но не коллапсировала. Online/tester reconciliation: 65 парных сделок, PF online 0.84 / tester 0.88, матожидание -10.15R / -7.69R — сигнальная цепочка идентична, исполнение убыточно. **Итог:** все прибыльные системы — FAIL для production. Live-safe PF=2.34 на 25 сделках.

### 2.7. Methodology Cycle

Live-safe candidate-source pipeline. Stages 00-10: RF baseline PF=1.58 (281 сделка, val), Transformer PF=11.60 (63 сделки, val). Stage 09: R-multiple PnL + Open[row+1] entry дал 0 eligible правил — FAIL. Limit-order entry: BUY spread 0.20 **PF=1.53** (55.3 trades/yr, 0 neg years) — PASS; spread 0.40: PF=1.23 — FAIL. Candidate-source audit: `signal != 0` FAIL для production (future-derived). **Итог:** pipeline построен, но исполнимый entry протокол уничтожил рабочую конфигурацию. Limit-order валиден для BUY на spread 0.20.

### 2.8. Fractal Stop и Stage 4

Feature ablation: flat PF=1.069 (FAIL), `path_long` **PF=1.538** (52.4 trades/yr) — PASS. Direction-only: edge_6 **PF=11.30** (5939 сделок, 0 neg years) — PASS для edge_h, FAIL для TB. RF GridSearch: val PF=12.96 — DIAGNOSTIC. Stage 1 breach: test AUC 0.640–0.649, lift 1.60–1.69 — PASS. Stage 2 trading: test PF=0.84 — FAIL. Stage 3: XGBoost `base_raw_plus_time` AUC=0.6799, lift=2.00 — PASS. **Stage 4: winner PF=1.015, BS_p05=0.837** (503 сделки) — FAIL. Deep diagnostics: oracle perfect_both PF=104.9, trailing atr_02 PF=1.655 — DIAGNOSTIC. Stage 4.6 clean cycle: val_eval **PF=0.897** (357 сделок, 3/4 neg years) — FAIL. Walk-forward: Expanding PF=0.840, Rolling PF=0.942 — breach работал на 2017-2022, перестал на 2023-2026. **Итог:** breach classification PASS, trading layer FAIL. Regime drift: сигнал исчез после 2022.

### 2.9. Stage 5-6: Transformer breach и outcome-based таргеты

Transformer breach: holdout AUC 0.6018 vs XGBoost 0.6524 (gap -0.051) — MODEL_FAIL. Asinh rerun: val AUC 0.6719 vs XGBoost 0.6631 — не прошёл decision policy. Cross-target 5 seeds: 0/5 выше порога — FAIL. Small Transformer: overfit drop уменьшился, но обе хуже XGBoost. Signal stationarity: rolling AUC 2023=0.664, 2024=0.675, 2025=0.629 — inconclusive. Structural ablation: только `back` устойчив на обеих целях. Time-to-breach regression: Spearman ~0.30, MAE хуже constant baseline. `fast` breach: sell val AUC 0.6967, holdout 0.6849 — наиболее перспективная цель. Outcome-based TB H6: AUC 0.689, но threshold не найден. H12 geometry: AUC 0.51–0.55 — FAIL. Price action: perm p=0.16 > 0.10 — FAIL. **Итог:** Transformer не превосходит XGBoost. Только `back` устойчив. `fast` breach перспективен для sell, но не доказывает пригодность для торговли.

### 2.10. Regression Up/Dn и Entry-Based таргеты

Target foundation: targets существуют, но связь с entry не исследована. Ratio audit: Spearman vs next-open log-ratio: H3=−0.011, H6=−0.017, H12=0.001 — предсказанное отношение не связано с движением после входа. **Already-moved audit: residual Spearman H3=0.54, H6=0.39, H12=0.29** — большая часть сигнала уже произошедшее. Next open entry: `structure_full` не сохраняет связь вне обучения. Entry-based closeout: лучший direction Spearman val_eval=0.0248; amplitude survives: 0.3414→0.4449 — **PIVOT на amplitude**. Powerful tabular models: direction val_eval=−0.0009 — мощность не главное ограничение. Fractal sequence Transformer: direction val_eval=0.0050 — порядок фракталов не помогает. Direction inside frozen mask: balanced_accuracy=0.499 — FAIL, не воспроизводится. **Итог:** сигнал — already-moved. Direction от next open непредсказуем. Amplitude устойчивее, но объясняется простыми baseline.

### 2.11. Fractal0 Fixed11

Entry/exit grid: 768 конфигураций, val_eval PF=2.72, BS p05=2.49 (2298 сделок). Entry quality filter: val_eval PF=1.95, BS p05=0.97 — winner не выживает. Rich entry quality: val_eval PF=4.03 (660 сделок), winner — time_only. **Locked test: все 11 rules passed** (PF 2.67–3.37, n_trades≥100). Candidate audit: PASS. Mutual-correlation pruning: 11→5 retained. MT4 parity: PF=9.03 (26 сделок). **Chronology fix: PF 0.82–0.94**, PnL R sum -530.51 — fix invalidates старые PF. History rerun: slot 1 lost 140 trades, gained 37. Fill chronology: Python/MT4 execution contract сломан. **Итог:** 11 rules — time_only или movement_plus_time. Calendar dominance: no-ML baseline достигает 85.9% ML PF. Chronology fix обнулил результаты.

### 2.12. MT5 Execution Loop

Infrastructure: single-rule prototype, batch design, manual runbook — DIAGNOSTIC. Single rule run: 294 ORDER_PLACED, 252 OPEN — сквозной пайплайн работает. **Batch 32 кандидатов: top PF=1.232, N=102, BS_p05=0.887** — все 11 eligible провалили гейт BS_p05>1.0, Holm-Bonferroni: 0 отклонённых — **BATCH_NO_WINNER**. Nero.csv parity: match rate 99.05%, direction agreement 99.24% — PASS. OnTradeTransaction: CLOSED_TX=269, UNEXPLAINED=0 — lifecycle closure. Timing contract: explicit и enforce-ится. Fill-rate probe: 99.19% OPEN_FAILED — `position_or_pending_order_exists` — single-position policy главный ограничитель. Multi-position: smoke max=1/2/16 PASS. Full batch max=1: **PF=0.910** (2508 сделок), max=64: **PF=0.895** (23 932 сделки) — убыток в обоих. Position-ordinal: ordinal 1 PF=1.013 (n=3657), ordinal 5+ **PF=3.205** (n=682, CI [2.909, 3.650]) — PF не деградирует монотонно, но фильтр нереализуем в live. **Итог:** infrastructure готова, batch BATCH_NO_WINNER. Multi-position исполняет ~9.6× больше, но убыточен.

---

## 3. Что работает

3.1. **Threshold analysis на val** (см. 2.1): PF=2.95 (2502 сделки) — PASS на val, не OOS.
3.2. **entry_path_v1 quantile** (см. 2.3): PF=8.18–9.03 (26–48 сделок) — PASS на test, не forward.
3.3. **Take/Skip quality/frequency** (см. 2.5): PF=39.74/13.12 — PASS, но leakage.
3.4. **Breach classification** (см. 2.8): AUC 0.64–0.68, edge_6 PF=11.30 (5939 сделок) — PASS, trading FAIL.
3.5. **Limit-order BUY** (см. 2.7): PF=1.53 (55.3 trades/yr, spread 0.20) — PASS, не робастен при spread>0.40.
3.6. **MT5 infrastructure** (см. 2.12): parity 99.05%, lifecycle 100%, multi-pos — PASS, batch убыточен.
3.7. **Fixed11 locked-test** (см. 2.11): 11 rules PF 2.67–3.37 — PASS, но chronology fix обнулил.

---

## 4. Что не работает

4.1. **Directional signal на OOS** (все направления): лучшие in-sample PF 4.29–39.74 (25–48 сделок), OOS PF 0.84–1.28 (25–1072 сделок). MT5 batch: PF=1.232, BS_p05=0.887 (102 сделки). Причина: already-moved, regime drift, leakage.
4.2. **Outcome-aligned таргеты** (см. 2.3): AUC=0.6534, PF<0.2 (24–48 сделок). Не дают edge.
4.3. **Direct direction** (см. 2.3): val PF=1.17–1.77, test PF=0.91–0.99. Val не переносится.
4.4. **Triple Barrier** (см. 2.4): test PF=1.11–1.28 (69–253 сделки), 2 убыточных года.
4.5. **Transformer breach** (см. 2.9): AUC gap -0.051 vs XGBoost, 0/5 seeds выше порога.
4.6. **Entry-based direction** (см. 2.10): Spearman val_eval=0.0248. Непредсказуем.
4.7. **Fixed11 после fix** (см. 2.11): PF 0.82–0.94. Execution contract сломан.
4.8. **MT5 batch** (см. 2.12): BS_p05=0.887 < 1.0. Single-position policy блокирует 99.2%.
4.9. **Walk-forward breach** (см. 2.8): PF=0.840–0.942. Сигнал работал 2017-2022, перестал 2023-2026.

---

## 5. Эволюция понимания

**Апрель 2026:** ML-модели предсказывают направление. Threshold analysis даёт PF=2.95 на val. Signal Research показывает: сигнал — слабый drift. Pullback работает через механическое улучшение цены.

**Конец апреля:** Entry Path даёт PF=8.18 на test (48 сделок), но forward trades=0. Take/Skip PF=39.74 — но это артефакты.

**Май 2026 — перелом:** Live-Safe Audit — все 5 систем FAIL (leakage). entry_path_v1_live_safe PF=2.34 (25 сделок) — снизилась, но не коллапсировала. Понимание: исторические метрики неприменимы для live.

**Конец мая:** Methodology Cycle: исполнимый entry уничтожил рабочую конфигурацию. Limit-order валиден для BUY на spread 0.20.

**Июнь:** Fractal Stop: breach classification PASS, trading FAIL. Walk-forward: сигнал работал 2017-2022, перестал 2023-2026 — regime drift. Transformer не превосходит XGBoost.

**Июль — перелом:** Regression Up/Dn: сигнал — already-moved. Spearman падает с 0.76–0.80 до 0.29–0.54. Direction от next open непредсказуем. Amplitude устойчивее, но объясняется простыми baseline.

**Конец июля:** Fixed11: 11 rules — time_only. Calendar dominance: no-ML baseline 85.9% ML PF. Chronology fix обнулил PF.

**Август:** MT5 batch 32 кандидатов: BATCH_NO_WINNER. Multi-position исполняет больше, но убыточен. Пять ретроспектив: порог не достигнут.

---

## 6. Нерешённые проблемы

**6.1. Directional signal не переносим.** Все системы дают высокие PF на in-sample, но не OOS. Нужно выяснить: фундаментальное ограничение данных или методологии? Подход: amplitude-based вместо direction-only.

**6.2. Already-moved проблема.** Сигнал — уже произошедшее движение. Spearman после вычитания 0.29–0.54. Нужно: выделить residual signal. Подход: amplitude decision layer.

**6.3. Regime drift (2023-2026).** Breach работал 2017-2022, перестал 2023-2026. Walk-forward не помогает. Нужно: regime-aware модели.

**6.4. Execution contract.** Python/MT4 timestamps не сохраняют M5-порядок. Нужно: MT5 execution loop с явным timing-контрактом.

**6.5. Single-position policy.** 99.2% OPEN_FAILED — position policy. Multi-position исполняет больше, но PF=0.895–0.910 (убыток). Нужно: найти способ сделать multi-position прибыльным.

---

## 7. Накопленные ограничения

**7.1. Future-derived leakage.** Все прибыльные исторические системы используют future-derived данные. Сужает поиск до live-safe моделей с более низкими PF.

**7.2. Малые выборки.** Лучшие системы: 25–48 сделок. MT5 batch: 102 сделки. Bootstrap CI широкие, lower bound < 1.0.

**7.3. Regime drift.** Сигнал работал 2017-2022, перестал 2023-2026. Сужает период обучения.

**7.4. Execution contract.** Python/MT4 сломан. Сужает до MT5 execution loop.

**7.5. Low R².** Модели объясняют 10–18% дисперсии. Фундаментальное ограничение предсказуемости.

**7.6. Time-only dominance.** Все 11 Fixed11 rules — time_only. No-ML baseline 85.9% ML PF. Time-признаки доминируют.

**7.7. Single-position policy.** 99.2% OPEN_FAILED. Multi-position убыточен.

---

## 8. Рекомендации

### Пробовать дальше

**Amplitude-based подходы (высокий приоритет).** Amplitude устойчивее direction (0.34→0.44). Модель предсказывает amplitude, decision layer: торговать если predicted amplitude > threshold. Избежит already-moved.

**MT5 execution loop (высокий приоритет).** Infrastructure готова. Batch selection с multi-position. Forward validation через Strategy Tester — единственный способ.

**Regime-aware модели (средний приоритет).** Breach работал 2017-2022, перестал 2023-2026. Модели с явным учётом regime.

**Limit-order BUY (средний приоритет).** PF=1.53 на spread 0.20. Проверить робастность на разных spread.

### Закрыть окончательно

**Direction-only модели.** Direction от next open непредсказуем (Spearman ~0.0). Все direction-only PF<1.5 на OOS. Already-moved.

**Breach-based trading.** Classification PASS, trading FAIL (PF=0.84–1.015). Regime drift.

**Triple Barrier.** Test PF=1.11–1.28, 2 убыточных года.

**Fractal0 Fixed11.** 11 rules — time_only. Calendar dominance 85.9%. Chronology fix обнулил.

**Take/Skip quality/frequency.** PF=39.74/13.12 — leakage. Live-safe FAIL.

### Приоритеты на следующий квартал

Q3: (1) Amplitude-based модели + decision layer. (2) MT5 batch с multi-position. (3) Forward validation. (4) Regime-aware модели.
Q4: (1) Limit-order BUY робастность. (2) Multi-position прибыльность. (3) Time-aware модели.
