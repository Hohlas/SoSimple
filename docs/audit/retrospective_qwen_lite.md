# Ретроспектива проекта SoSimple

**Период**: 2026-02-24 — 2026-08-13
**Порог успеха**: PF ≥ 1.3 на out-of-sample с учётом спреда и проскальзываний, подтверждённый bootstrap CI (нижняя граница > 1.0).

---

## 1. Вердикт по проекту

Порог успеха не достигнут. Ни одна из исследованных систем не продемонстрировала устойчивый PF ≥ 1.3 на out-of-sample с подтверждённым bootstrap CI. Главная причина — фундаментально низкая предсказуемость направления движения цены XAUUSD на H1: mutual information(direction) ≈ 0.003–0.004 bits, пермутационный тест p=0.229 на validation. Сигнал существует (amplitude MI значим, p=0.005), но его недостаточно для устойчивой торговли с учётом транзакционных издержек. Все попытки усилить сигнал — сменой архитектуры, таргетов, признаков, горизонтов — упирались в информационный потолок ~3% R².

---

## 2. Направления исследований

### 2.1. Baseline ML & Architecture Selection

**Цель**: выбрать архитектуру для задачи классификации и регрессии сигналов.

- **2026-02-24, Classification**: Transformer — Macro F1 0.577 (лучший), BiLSTM 0.568. Accuracy ~90%, но F1(1) 0.32–0.38. PASS.
- **2026-03-11, Regression**: BiLSTM — Pearson r 0.324, R² 0.103 (лучший); Transformer — r 0.114, R² ≈ 0. PASS.
- **2026-03-11, Reproducibility**: детерминизм diff 0.000, seed std 0.002. PASS.
- **2026-03-16, Optuna**: Pearson r улучшен с 0.324 до 0.339 (+4.6%). PASS.
- **2026-05-25, Methodology Cycle Stages 00–10**: pipeline построен (63006 строк), но Stage 09 дал 0 eligible правил при R-multiple PnL + Open[row+1] entry. Stage 10 INVALID. FAIL.

**Итог**: BiLSTM лучше для регрессии, Transformer — для классификации. Гиперпараметрическая оптимизация даёт умеренный прирост. Live-executable протокол не позволяет использовать Close[row] entry.

### 2.2. Regression Targets & Threshold Analysis

**Цель**: найти оптимальный торговый порог для регрессионных предсказаний.

- **2026-03-19, REGRESSION_UPDN**: Transformer Pearson r 0.4265, R² 0.183 (лучший). PASS.
- **2026-03-19, Threshold H12/H24/H48**: θ=2.665/2.151/1.926, PF=2.95/2.34/1.98. Test H12: PF=4.51 (2203 сделки, WR 86.2%). PASS.
- **2026-04-08, Triple Barrier**: θ=0.475, PF=1.53 (121 сделка). PASS (условно).
- **2026-06-30, Target Foundation**: H3 Spearman ~0.82 — лучший, не H12. DIAGNOSTIC.
- **2026-07-01, Ratio Audit**: Spearman pred vs next-open ≈ 0. DIAGNOSTIC.
- **2026-07-02, Already Moved Audit**: 57% строк H3 ≥50% движения уже произошло до входа. DIAGNOSTIC.

**Итог**: Fixed-horizon таргеты дают высокий PF на test, но entry на next open разрушает связь. Сигнал работает как фильтр зоны, не как немедленная сделка.

### 2.3. ME Integration & Trading Layer

- **2026-03-20, Conformal Prediction**: PF без CP 4.5056, с CP 4.4891 (Δ −0.02). DIAGNOSTIC.
- **2026-05-18, Direct Direction Rebuild**: Phase A val PF=1.77, Phase D test PF=0.99. FAIL.

**Итог**: CP не помогает при агрессивном θ. Validation PF не переносится на test.

### 2.4. Signal Research & Variant Exploration

- **2026-04-01, Variant 2**: базовый PF=1.05, лучший бакет ratio_12=4-5. PASS.
- **2026-04-02, Variant 3**: pullback entry PF=3.69 (36 fills), но контроли тоже улучшаются. PASS (условно).
- **2026-04-03/04, Signal Path Atlas**: 64% сигналов — провальный архетип. DIAGNOSTIC.
- **2026-04-04, Signal Quality Filter**: лучший лист PF=1.98 (172 сделки), но score-подход НЕ ПОДТВЕРЖДЁН. PASS (частичный).
- **2026-04-04, Archetype-Filter Bridge**: fav_3_vs_12 ≤ 0.653 + откат 1ATR — PF=2.64 (43 сделки). PASS.

**Итог**: Преимущество — в отборе 36% хороших сигналов, а не в механике входа. Фильтры работают через отбор, не через entry-механику.

### 2.5. Entry Path v1 & Quantile Track

- **2026-04-08, Baseline**: test ret_pearson_r=0.2732 (исправлен баг кэша). DIAGNOSTIC.
- **2026-04-08, Outcome-Aligned**: ни одно семейство не прошло. FAIL.
- **2026-04-09, Loss Weighting**: вес 5.0 для активных строк — лучший. PASS.
- **2026-04-09, Trade Filter**: test PF=4.29 (862 сделки), sequential PF=2.87 (30 сделок). PASS.
- **2026-04-10, Quantile**: test PF=inf (24 сделки), sequential PF=inf (11 сделок). PASS.
- **2026-04-12, Quantile Status**: N=48, PF=8.18, win rate 81.25%. PASS (production-ready).
- **2026-05-05, Live-Safe Audit**: все 5 систем FAIL — future-derived inputs. Перестроение: median sequential PF=2.34. FAIL → rebuild.
- **2026-05-14, All-Rows Ranking**: val PF=0.97, test PF=0.91. FAIL.

**Итог**: От честного baseline через quantile-layer к PF=8.18, затем live-safe аудит обнаружил leakage. Перестроение дало median PF=2.34. Production-переход отложен.

### 2.6. Triple Barrier & Exit Policy

- **2026-04-08, Hardening**: val PF=1.53 (121 сделка), test PF=1.11 (253 сделки). Completed.
- **2026-04-08, Runtime Verdict**: MT4 PF=1.27 (92 сделки), совпадение TP/SL 93.8%. Completed.
- **2026-04-08, ML Exit Validation-First**: winner timeout_only: val PF=1.17, test PF=1.12. Completed (отрицательный).
- **2026-04-12, TB Production Verdict**: критический баг — int(outcome) сливал SL и Timeout. После фикса: test PF=1.28 (69 сделок), gate FAIL.
- **2026-04-13, Label Convention Audit**: 2 бага исправлены, verdict подтверждён. Completed.

**Итог**: TB-слой не подключается к MT4. Production остаётся на regression_updn + entry_path_v1_quantile.

### 2.7. Trailing Stop & Take/Skip Features

- **2026-04-16/17, Trailing Stop Target**: лучший val PF=0.42, quantile PF=0.175. FAIL.
- **2026-04-17, Take/Skip v1**: лучший PF=0.274. FAIL.
- **2026-04-18, Frequency Follow-Up**: quality test PF=39.74, frequency test PF=7.18. PASS.
- **2026-04-19, Execution Policy v2**: quality trail_x8+tp12 PF=50.4 (Python), frequency trail_x8 PF=3.77 (MT4). PASS.
- **2026-04-20, Feature Ablation**: original_plus_path_seq50 PF=38.78. PASS.
- **2026-04-20, Dual-Stream lib_PIC**: все 9 reject. FAIL.

**Итог**: Take/Skip v2 дал рабочие quality и frequency режимы. Dual-stream не воспроизводит прибыльную область.

### 2.8. Track A Max-Out & Composition

- **2026-04-15, Max-Out**: лучший val PF=0.4784, test PF=0.9212. FAIL.
- **2026-04-13, PF Uplift Discovery**: 3 гипотезы отобраны (исключить NY, early timeout, pred_adv12 cap). DIAGNOSTIC.
- **2026-04-13, FAV 3 vs 12 Standalone**: PF намного ниже 1.0. REJECT.

**Итог**: Track A исчерпан. Проблема не решается увеличением истории или dual-stream.

### 2.9. Cross-Instrument Robustness & Portfolio

- **2026-04-22, Signal Export Parity**: расхождение объяснено дубликатами timestamp. DIAGNOSTIC.
- **2026-04-24, Cross-Instrument**: XAUUSD provider_stable; EURUSD transfer_failed для всех. MIXED.
- **2026-04-24, Entry Path Cross-Instrument**: entry_path_v1_quantile живучее baseline. MIXED.
- **2026-04-24, Portfolio Check**: frequency × original_plus_path = portfolio_redundant; quality × entry_path_v1 = complementary. COMPLETED.

**Итог**: Provider drift не ломает системы. Перенос не универсален. Портфель: quality + entry_path_v1_quantile.

### 2.10. Direct Direction & Transformer Encoder

- **2026-05-15, Improvement**: binary RF margin=0.10 PF=1.25 (1923 сделки). FAIL (gate 1.15 не пройден на test).
- **2026-05-18, Rebuild**: val PF=1.77, test PF=0.99. FAIL.
- **2026-05-21, Transformer Encoder**: лучший Trail PF=2.41 (58 сделок, 0.6% utilisation). FAIL.
- **2026-05-29, Limit-Order Entry**: RF BUY PF=1.53, Transformer AUC=0.50. DIAGNOSTIC.
- **2026-06-04, Fractal Channel Ablation**: edge_6 PF=11.3 (диагностическая). DIAGNOSTIC.

**Итог**: BUY PF=1.31, SELL PF=0.99. Сигнал крайне слаб, распределён по геометрии фракталов.

### 2.11. Entry-Based Next Open & Up/Dn Targets

- **2026-07-02, Next-Open Foundation**: Spearman максимум 0.0203. NO_SIGNAL_FOUND.
- **2026-07-02, Price-Feature Matrix**: лучший distance_atr 0.0354. WEAK_TRACE.
- **2026-07-03, Fractal Selection Ablation**: лучший corridor_5atr 0.0795. WEAK_TRACE.
- **2026-07-04, Closeout**: лучший direction 0.0129, amplitude 0.4449. PIVOT.
- **2026-07-06, Powerful Tabular**: лучший direction -0.0009, amplitude 0.3248. PIVOT.
- **2026-07-07, Fractal Sequence Transformer**: лучший direction 0.0050. PIVOT.

**Итог**: Direction gate не пройден. Amplitude trace сильнее direction. Вся ветка закрыта; pivot на amplitude/movement-regime.

### 2.12. Movement Filter & Frozen Mask

- **2026-07-07, Amplitude Audit**: простой baseline Spearman 0.693, sequence не побили. DIAGNOSTIC.
- **2026-07-07, Filter Design**: val_eval movement_lift 2.48 (333 сделки). RESEARCH_ONLY.
- **2026-07-08, Replication Freeze**: val_eval lift 2.48, yearly pass rate 1.00. FROZEN.
- **2026-07-08, Direction Inside Mask**: val_eval BA 0.529. FAIL.
- **2026-07-09, Rich Features**: val_eval BA 0.529. DIAGNOSTIC.
- **2026-07-10, Narrow Replication**: H3 median BA 0.499. FAIL.

**Итог**: Amplitude предсказуема, но объясняется простыми признаками. Direction внутри маски нестабилен. Ветка закрыта.

### 2.13. Fractal0 Fixed-11 & Rich Entry Quality

- **2026-07-10, Oracle-Preflight**: gate не пройден. DIAGNOSTIC.
- **2026-07-21, Entry/Exit Grid**: winner val_eval PF=2.72 (2298 сделок). RESEARCH_ONLY.
- **2026-07-21, Stop Grid M5**: winner val_eval PF=2.79. RESEARCH_ONLY.
- **2026-07-21, Entry Quality Filter**: val_eval PF=1.95 (53 сделки). RESEARCH.
- **2026-07-21/22, Rich Entry Quality**: winner time_only val_eval PF=4.03 (660 сделок). RESEARCH_HINT.
- **2026-07-23, Robustness Audit**: time_only не провалился, но stricter cutoff даёт 139 сделок. RESEARCH_ONLY.
- **2026-07-23/24, Fixed-11 Closure**: spread 0.8 min PF=1.32, 7 flags. RESEARCH_ONLY.
- **2026-07-24, Locked Test**: все 11 прошли gate (PF 2.67–3.37). CANDIDATE_CHECK.
- **2026-07-25, Candidate Audit**: 14 findings, 0 errors, 13 warnings. PASS.
- **2026-07-27, Mutual-Correlation Pruning**: 11 → 5 retained. PASS.
- **2026-07-27/29, MT4 Parity**: fill mismatch, Python может записывать ML_CLOSE на тот же H1 timestamp. DIAGNOSTIC.
- **2026-07-29, Current History Rerun**: OHLC refresh materially changed results. DIAGNOSTIC.
- **2026-07-29, Python H1 Chronology Fix**: после фикса PF 0.82–0.94, kept_candidates=0. REJECT.

**Итог**: Locked test прошёл, но хронология исправлена — прибыльность полностью исчезла. Fixed-11 mechanics invalidation confirmed.

### 2.14. Stage 5: Transformer Breach & Feature Ablation

- **2026-06-17, Transformer Breach Holdout**: AUC 0.6018 vs XGBoost 0.6524. MODEL_FAIL.
- **2026-06-20/21, Asinh Rerun**: лучший val AUC 0.6719, holdout 0.6373. DIAGNOSTIC.
- **2026-06-22, Cross-Target Rerun**: Transformer систематически уступает XGBoost. FAIL.
- **2026-06-23, Diagnostic Screening**: ни один профиль не превосходит base на ≥0.02 AUC. EXHAUSTED.
- **2026-06-24, Signal Stationarity**: не удалось доказать ни распад, ни устойчивость. INCONCLUSIVE.
- **2026-06-24/25, Structural Field Ablation**: `back` — единственное устойчиво полезное поле. DIAGNOSTIC.
- **2026-06-25, Time-To-Breach Regression**: Spearman >0.30, но MAE FAIL. DIAGNOSTIC.
- **2026-06-26, Target Reformulation**: sell `fast` val AUC 0.6967, delta +0.0279. REFORMULATION_FOUND.
- **2026-06-29, Fast Price/ATR Ablation**: price_coord_atr не улучшает. REJECT.

**Итог**: Transformer не извлекает сигнал из последовательной структуры. Stage 5 закрыт без кандидата.

### 2.15. Stage 6: Outcome-Based Triple Barrier & Price Action

- **2026-06-29, Foundation**: H6 median AUC 0.689, H24 PF 0.933–1.023. TRADING_GATE_FAILED.
- **2026-06-29, H12 Relative Geometry**: AUC 0.53. MODEL_GATE_FAILED.
- **2026-06-30, Price Action**: permutation p=0.160. TRADING_GATE_FAILED.
- **2026-06-30, Range W1 Post-Mortem**: range_w1_atr vs PnL correlation 0.008. WEAK.
- **2026-06-30, H6 Feature Parity**: permutation p=0.27–0.37. NO_ADDITIVE_VALUE.

**Итог**: H6 делает задачу проще, но не даёт торгового кандидата.

### 2.16. Stage 4: Fractal Stop Trading Layer

- **2026-06-10, Stage 1 Breach**: AUC 0.62–0.68, lift 1.52–1.77. PASS.
- **2026-06-10, Stage 2 Trading**: ни одна комбинация не достигла PF > 1.0. FAIL.
- **2026-06-10/12, Stage 3/4 XGBoost**: AUC 0.680, но PF winner снизился до 1.015. FAIL.
- **2026-06-14, Deep Diagnostics**: трейлинг-стоп trail_atr_0_2 PF=1.655. DIAGNOSTIC.
- **2026-06-15, Micro-Check**: fixed TP PF=1.038. DIAGNOSTIC.
- **2026-06-15, Walk-Forward**: expanding window PF 0.73–0.92. DIAGNOSTIC.

**Итог**: Breach-сигнал реален, но не конвертируется в PF > 1.15. Execution-политика важнее breach-прогноза.

### 2.17. MT5 Execution Loop & Migration

- **2026-07-29, Migration**: контур работает статически. DIAGNOSTIC.
- **2026-07-30, Single Rule Diagnostic**: 294 ORDER_PLACED, 18 CLOSE. DIAGNOSTIC.
- **2026-07-31, Nero.csv Parity**: match 99.05%. PARITY_PASS.
- **2026-07-31, OnTradeTransaction**: TX-поток покрывает 100% закрытий. DIAGNOSTIC.
- **2026-08-01, Batch Selection**: 11 eligible, все провалили BS_p05>1.0. BATCH_NO_WINNER.
- **2026-08-01/02, Fill-Rate Probe**: 99.19% OPEN_FAILED от single-position policy. DIAGNOSTIC.
- **2026-08-02/03, Multi-Position**: max=64 PF=0.895 (23932 размещений). PASS.

**Итог**: MT5 мигрирован с полной паритетностью. Batch selection не дал победителя. Single-position gate — главный ограничитель.

### 2.18. MI Upper Bound: Information Ceiling (singleton)

**2026-08-11**: Amplitude MI 0.010–0.022 bits (p=0.005), direction MI 0.003–0.004 bits (p=0.229). Предсказуемость амплитуды значима, но крайне мала (R² ceiling ~3%). Направление не предсказуемо значимо.

### 2.19. Online Inference & Telemetry

- **2026-04-27, Telemetry Demo**: 495 сигналов в 2025. Completed.
- **2026-04-28, MQL Runtime Snapshot**: 63009+ строк Nero.csv, 0 mismatches. Completed.
- **2026-04-29, Contract Hardening**: live-safe preprocessing, legacy заблокирован. Completed.
- **2026-05-12, Online/Tester Reconciliation**: 79 сигналов совпали, 6 пропусков = requote. PASS.

**Итог**: Контур hardened, сигнальный слой воспроизводится.

### 2.20. Methodology Cycle & Pipeline Foundation

- **2026-05-14, Causal Surrogate**: PF 1.1537 (36 сделок). DIAGNOSTIC.
- **2026-05-14, Direct Bar Model**: PF 1.1141 (1277 сделок). DIAGNOSTIC.
- **2026-05-25, Stages 00–10**: pipeline построен, но 0 eligible stable rules. FAIL.

**Итог**: Pipeline foundation построен, production-кандидат не заморожен.

---

## 3. Что работает

- **BiLSTM для регрессии** (см. 2.1): Pearson r 0.324 → 0.339 после Optuna.
- **Take/Skip v2 quality/frequency** (см. 2.7): test PF 39.74 / 7.18.
- **Signal Path Atlas** (см. 2.4): инструмент готов, 31 holdout replicated.
- **MT5 execution loop** (см. 2.17): паритетность подтверждена, multi-position работает.
- **Online inference contract** (см. 2.19): live-safe preprocessing, 0 mismatches.

---

## 4. Что не работает

- **Transformer для регрессии** (см. 2.1): R² ≈ 0, хуже BiLSTM.
- **Conformal Prediction** (см. 2.3): PF Δ −0.02, не помогает.
- **Validation → test перенос** (см. 2.3, 2.5, 2.10): PF 1.77 → 0.99, 8.18 → 2.34.
- **All-rows ranking** (см. 2.5): PF 0.91–0.97, нельзя снять signal!=0 gate.
- **Triple Barrier production** (см. 2.6): test PF 1.28, gate FAIL.
- **Trailing stop target regression** (см. 2.7): PF 0.175–0.42.
- **Track A max-out** (см. 2.8): val PF 0.4784, исчерпан.
- **Cross-instrument transfer** (см. 2.9): EURUSD transfer_failed.
- **Direct direction test** (см. 2.10): PF 0.99, SELL PF 0.99.
- **Entry-based next open direction** (см. 2.11): Spearman 0.0129, gate не пройден.
- **Direction inside movement mask** (см. 2.12): BA 0.499, нестабилен.
- **Fixed-11 после фикса хронологии** (см. 2.13): PF 0.82–0.94, kept=0.
- **Transformer breach** (см. 2.14): AUC 0.6018, хуже XGBoost.
- **Stage 6 price action** (см. 2.15): permutation p=0.160.
- **Stage 4 trading layer** (см. 2.16): PF 1.015, не конвертируется.
- **MT5 batch selection** (см. 2.17): все 11 eligible провалили BS_p05>1.0.
- **Direction prediction** (см. 2.18): MI p=0.229, не значимо.

---

## 5. Эволюция понимания

**2026-02-24 — 2026-03-16**: Убеждение, что deep learning (Transformer) даст превосходство. Эксперименты показали: BiLSTM лучше для регрессии, Transformer — для классификации, но разница минимальна. Optuna даёт умеренный прирост (+4.6%).

**2026-03-19 — 2026-04-08**: Переход к threshold-анализу. Обнаружен высокий PF на test (4.51), но это illusion — entry на next open разрушает связь (см. 2.2, 2.11). Conformal Prediction не помогает.

**2026-04-08 — 2026-04-20**: Entry Path v1 и Take/Skip дают рабочие режимы (PF 8.18 — см. 2.5, 39.74 — см. 2.7). Убеждение, что нужно усилить ML-слой. Live-safe аудит (2026-05-05) обнаружил future-derived leakage — переломный момент. Перестроение без `ret_dir_atr_lag1` дало PF 2.34 (см. 2.5).

**2026-04-13 — 2026-05-18**: Поиск PF uplift вне ML-слоя. Track A исчерпан (PF 0.4784 — см. 2.8). Direct direction rebuild: val PF 1.77 → test PF 0.99 (см. 2.3, 2.10) — overfitting на validation.

**2026-05-25 — 2026-06-30**: Methodology cycle показал: фрактальные признаки не несут directional signal. Stage 4/5/6 систематически проваливают trading gate. Transformer breach уступает XGBoost.

**2026-07-02 — 2026-07-10**: Entry-based next open ветка закрыта — direction не работает, amplitude сильнее. Movement filter frozen, но direction внутри маски нестабилен.

**2026-07-10 — 2026-07-29**: Fractal0 Fixed-11 прошёл locked test, но фикс хронологии (2026-07-29) обрушил PF до 0.82–0.94 (см. 2.13). Ключевой инсайт: same-H1 fill/exit — механическая проблема, но даже после фикса прибыльность исчезла.

**2026-08-11**: MI upper bound подтвердил фундаментальный предел: direction MI не значим (p=0.229 — см. 2.18), amplitude MI значим, но крайне мал (R² ceiling ~3% — см. 2.18).

**Граф знаний** (graphify path): Regression Up/Dn → fractal-stop-research → Entry-Based Next Open показывает связь через fractal-stop-research.md. Entry Path v1 → execution-tracks → Fractal0 Fixed-11 показывает эволюцию от entry-механики к fixed-price entry.

---

## 6. Нерешённые проблемы

- **Direction prediction**: MI показывает фундаментальный предел (см. 2.18). Что известно: amplitude предсказуема, direction — нет. Что нужно выяснить: существует ли другой target, несущий directional signal. Предлагаемый подход: смена парадигмы (не direction, а regime/volatility).

- **Entry mechanics**: Fixed-11 mechanics invalidation (см. 2.13) показал, что даже после фикса хронологии PF исчезает. Что известно: same-H1 fill/exit — проблема. Что нужно выяснить: существует ли live-executable entry protocol, сохраняющий прибыльность. Предлагаемый подход: execution-aware entry, не привязанный к close[row].

- **Validation → test перенос**: систематический overfitting (см. 2.3, 2.5, 2.10). Что известно: val PF не переносится. Что нужно выяснить: почему. Предлагаемый подход: walk-forward validation, более строгие gate.

- **MT5 production**: batch selection не дал победителя (см. 2.17). Что известно: single-position gate — ограничитель, multi-position снимает его, но PF < 1. Что нужно выяснить: существует ли конфигурация, дающая PF > 1.3. Предлагаемый подход: trade-count consolidation, entry mechanics probe.

---

## 7. Накопленные ограничения

- **Информационный потолок**: MI direction не значим (p=0.229), amplitude R² ceiling ~3% (см. 2.18). Это сужает пространство поиска — direction prediction на H1 XAUUSD фундаментально ограничен.

- **Entry protocol**: Close[row] entry не live-executable (см. 2.1, 2.13). Open[row+1] + R-multiple PnL даёт 0 eligible правил. Это сужает пространство торговых механик.

- **Validation-тест расхождение**: систематический overfitting (см. 2.3, 2.5, 2.10). Это требует более строгих gate, walk-forward validation, но сужает пространство моделей.

- **Same-H1 fill/exit**: механическая проблема Python-симулятора (см. 2.13). Даже после фикса PF исчезает. Это ограничивает достоверность backtest.

- **Single-position policy**: 99.2% OPEN_FAILED от single-position (см. 2.17). Multi-position снимает ограничитель, но PF < 1. Это сужает пространство исполнения.

- **Cross-instrument transfer**: EURUSD transfer_failed (см. 2.9). Это ограничивает универсальность систем.

- **Future-derived leakage**: historical test загрязнён (см. 2.19). Это требует live-safe preprocessing, но сужает пространство признаков.
