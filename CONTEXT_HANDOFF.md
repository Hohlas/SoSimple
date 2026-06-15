# Context Handoff

Дата: 2026-06-15 (Stage 4.x remaining hypotheses завершён).

## Текущий этап

Stage 4 «XGBoost Trading Layer», Stage 4.1 controls и Stage 4.2 diagnostic завершены. Табличные модели (RF, XGBoost) на плоских фрактальных признаках достигли потолка в текущей торговой постановке. Breach-модель добавляет реальный сигнал для фиксированного правила (0/500 перестановок, p ≈ 0.002, +0.20 PF над случайным), но его силы недостаточно для устойчивой прибыльности (PF после коррекции = 1.015, gate > 1.15 не пройден, исторический selection bias winner не исправлен).

### Полный путь Stage 3.x → Stage 4

| Этап | Модель | Лучший профиль | AUC mean | ΔAUC vs RF base_raw | Торговый PF | Вердикт |
|------|--------|----------------|----------|----------------------|-------------|---------|
| Stage 3 | RF | `relative_geometry` | 0.6580 | +119 bp | — | Profile comparison only |
| Stage 3.1 | RF | `relative_geometry_clean` | 0.6581 | +127 bp | — | Uplift = time, not density |
| Stage 3.2 | XGBoost | `base_raw_plus_time` | 0.6799 | +345 bp | — | Best table-model classifier |
| Stage 4 | XGBoost breach + RF fav | `base_raw_plus_time` | 0.6741 | — | **1.106** (BS_p05=0.923) | ❌ FAIL — PF завышен старым протоколом |
| Stage 4.1 | XGBoost-fav / combined breach | `base_raw_plus_time` | — | — | **1.065** combined (BS_p05=0.883, perm_p=0.050) | ❌ FAIL |
| Stage 4.2 | Corrected methodology | `base_raw_plus_time` | 0.6674 | — | **1.015** (BS_p05=0.837, 0/500 perm) | ⚠️ DIAGNOSTIC: signal is real but too weak |

### Результаты Stage 4.2 (DIAGNOSTIC)

| Метрика | Stage 4 (inflated) | Stage 4.2 (corrected) | Δ |
|---------|:------------------:|:---------------------:|:--:|
| PF | 1.106 | **1.015** | **−0.091** |
| BS_p05 | 0.923 | **0.837** | −0.086 |
| Breach AUC | 0.6741 | 0.6674 | −0.0067 |
| Perm p-value | — | **0/500 (p ≈ 0.002)** | — |
| Perm median PF | — | 0.817 | — |
| Neg years | 3/4 | 1/4 | −2 |

Stage 4.2 показал снижение PF 1.106 → 1.015. Это совокупный эффект исправленного диагностического протокола, а не изолированная оценка вклада каждой ошибки.
Stage 4.2 одновременно меняет train-период, слой early stopping, spread-модель, отказ от нового grid search и число сделок (344 → 503). Разложить вклад отдельных факторов без абляции нельзя.

**Ключевой результат:** breach-модель добавляет реальный сигнал для фиксированного правила — 0/500 перестановок breach-вероятностей достигли PF ≥ 1.015 (консервативная оценка p ≈ 1/501 ≈ 0.002), ΔPF ~ +0.20 над случайным (1.015 vs 0.817). Однако winner был выбран ранее на Stage 4 по validation 2019–2022, и permutation test не исправляет этот исторический selection bias. Проблема НЕ в отсутствии сигнала, а в его недостаточной силе для покрытия спреда и шума fav-предсказаний.

### Исправления методики Stage 4.2

1. Трёхслойный split: train (2004–2016) → val_stop (2017–2018, early stopping) → val_eval (2019–2022, оценка)
2. Early stopping на val_stop, не на val_eval
3. Один target, одна унаследованная конфигурация, без нового grid search; исторический selection bias остаётся
4. Spread-коррекция под OHLC=Bid: SELL bars shifted +spread (exit at Ask), BUY entry+spread (entry at Ask)
5. Block bootstrap (block_size=15)
6. Permutation test для одного target

### Ключевые находки (все этапы)

1. Улучшение breach с RF 0.645 до XGBoost 0.680 (+345 bp) дало лишь +0.04 PF над Stage 2 (0.975 → 1.015 corrected).
2. AUC не предсказывает PF: sell_H12_off02 AUC=0.696 → PF=0.976; sell_H6_off05 AUC=0.667 → PF=1.015.
3. Buy-сторона структурно невыгодна: все 4 buy-таргета PF < 0.94.
4. `base_raw_plus_time` и `relative_geometry_clean` идентичны — простой профиль предпочтительнее.
5. XGBoost-fav хуже RF-fav на всех 4 SELL-таргетах (Stage 4.1).
6. Combined breach H6+H12 не превосходит индивидуальный winner (PF=1.065, perm_p=0.050).
7. Stage 4.2 дал ΔPF = −0.091 относительно Stage 4. Это совокупный эффект исправленного диагностического протокола (одновременно изменены train-период, early stopping, spread-модель, grid search, число сделок), а не точная декомпозиция завышения.
8. Breach-модель даёт реальный, но слабый сигнал для фиксированного правила (0/500 перестановок, p ≈ 0.002, +0.20 PF над случайным). Permutation test не исправляет исторический selection bias winner.

### Файлы

Скрипты:
- `ML/baseline/benchmark_fractal_stop_stage4.py` — Stage 4
- `ML/baseline/benchmark_fractal_stop_stage4_1.py` — Stage 4.1
- `ML/baseline/benchmark_fractal_stop_stage4_2.py` — Stage 4.2 diagnostic (NEW)

Результаты:
- `ML/reports/stage4_trade.json`, `stage4_trade_geom.json`
- `ML/reports/stage4_1.json`
- `ML/reports/stage4_2_diagnostic.json` (NEW)

Отчёты и аудиты:
- `docs/reports/2026-06-11-stage4-trade-xgboost.md` — канонический отчёт (обновлён Stage 4.2)
- `docs/audit/2026-06-11-stage4-trade-xgboost-audit.md` — первоначальный аудит
- `docs/audit/2026-06-11-stage4-GLM-audit.md` — глубокий аудит GLM
- `docs/audit/2026-06-11-stage4-Qwen-audit.md` — аудит Qwen

### Git

Ветка: `feature/fractal-stop-fav-spec`.

## Следующий шаг

После Stage 4.6 FAIL: завершён master-план оставшихся гипотез Stage 4.x.

**Выполненные гипотезы:**
- Stage 5.0-prep: feature ablation (календарный риск подтверждён, time_only AUC=0.6286 > no_time 0.6113) + AUC→PF sensitivity (gate при AUC=0.8442, gap +1768 bp)
- Stage 4.5 exit mechanics: trail_atr_0_2 PF=1.831, BS_p05=1.462 — лучший diagnostic-сигнал Fractal Stop
- Stage 4.6 clean candidate-cycle (extended to 2026): trail_atr_0_2 прошёл val_select 2019-2022 (PF=2.041, conc=0.434), но провалил val_eval 2023-2026 (PF=0.897) — breach-модель ≤2016 не обобщается на +7 лет; exit-политика доминирует над breach-сигналом в протоколе выбора

**Приоритет: Stage 5.0 Transformer.**

На входе:
- Календарный baseline обязателен (time features несут 56% breach-сигнала)
- Требуемый AUC-прирост для PF-gate = 1768 bp (значительный масштаб)
- Trail_atr_0_2 даёт улучшающий сигнал как execution-политика, но требует более длинного сплита для clean-валидации
- Stage 4.4 fixed TP R=0.7 + fav-фильтр — текущий baseline для торгового слоя

**Альтернатива:** пересмотр торговой постановки или закрытие Fractal Stop ветки.
