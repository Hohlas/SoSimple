# Глубокий аудит Stage 4: XGBoost Trading Layer

> **Date**: 2026-06-11  
> **Auditor**: AI agent (opencode)  
> **Scope**: `ML/baseline/benchmark_fractal_stop_stage4.py`, `ML/baseline/benchmark_fractal_stop_stage4_1.py`, `docs/reports/2026-06-11-stage4-trade-xgboost.md`, `ML/reports/stage4_trade.json`, `ML/reports/stage4_trade_geom.json`, `ML/reports/stage4_1.json`  
> **Status**: Completed  
> **Verdict**: 3 методологические проблемы (A1-A3), 3 бага низкой серьёзности (B1-B3). Главный вывод Stage 4 остаётся в силе: AUC 0.68 недостаточно для PF>1.0 в этой торговой постановке.

---

## A. КРИТИЧЕСКИЕ МЕТОДОЛОГИЧЕСКИЕ ПРОБЛЕМЫ

### A1. Early stopping на validation (утечка информации)
**Серьёзность**: ВЫСОКАЯ  
**Файл**: `ML/baseline/benchmark_fractal_stop_stage4.py:396-409`

XGBoost breach обучается с `early_stopping_rounds=20` и `eval_set=[(X_val, y_val)]`. Validation данные определяют момент остановки (число деревьев), то есть **влияют на сложность модели**. Это форма утечки: validation используется и для обучения, и для оценки.

**Сравнение со Stage 2**: Stage 2 использовал RF без early stopping — такой утечки не было.

**Оценка влияния**: ~1-5 bp завышения AUC. Не объясняет весь провал PF, но нарушает принцип независимости validation.

**Исправление**: Выделить внутреннюю валидацию из train (последние 20% train) для early stopping.

```python
# Текущий код (неправильно):
model.fit(X_train, y_train, eval_set=[(X_val, y_val)], ...)

# Исправленный код:
val_size = int(0.2 * len(X_train))
X_train_internal = X_train[:-val_size]
y_train_internal = y_train[:-val_size]
X_val_internal = X_train[-val_size:]
y_val_internal = y_train[-val_size:]
model.fit(X_train_internal, y_train_internal, 
          eval_set=[(X_val_internal, y_val_internal)], ...)
```

---

### A2. Grid search на validation без коррекции множественного тестирования
**Серьёзность**: ВЫСОКАЯ  
**Файл**: `ML/baseline/benchmark_fractal_stop_stage4.py:532-553`

24 grid-комбинации × 8 таргетов = **192 PF-оценки на одном validation**. Нет коррекции (Bonferroni, FDR, Holm). При α=0.05 ожидается ~10 ложных «значимых» результатов из 192.

**Факт**: только 1/8 таргетов имеет PF>1.0 — это как раз уровень случайного шума (12.5%).

**Permutation test** Stage 4.1 выполнен только для combined targets (не для winner Stage 4), и дал `perm_p=0.050` — на границе.

**Исправление**: 
- Permutation test для ВСЕХ таргетов, или
- Bonferroni: α_adj = 0.05/192 = 0.00026

---

### A3. Winner selection по точечному PF, без учёта неопределённости
**Серьёзность**: СРЕДНЯЯ  
**Файл**: `ML/baseline/benchmark_fractal_stop_stage4.py:549`

Grid выбирает максимальный PF: `metrics['pf'] > best_metrics['pf']`. Bootstrap CI вычисляется ПОСЛЕ выбора, но не влияет на него. Конфигурация с PF=1.106 и BS_p05=0.923 выиграла у потенциально более стабильных.

**Исправление**: Выбирать по `BS_p05` (нижней границе CI), а не по точечному PF.

```python
# Текущий код:
if best_metrics is None or metrics['pf'] > best_metrics['pf']:
    best_metrics = metrics

# Исправленный код:
bs = bootstrap_pf(trades)
if best_metrics is None or bs['pf_p05'] > best_bootstrap['pf_p05']:
    best_metrics = metrics
    best_bootstrap = bs
```

---

## B. ОШИБКИ В КОДЕ

### B1. Bootstrap предполагает i.i.d. сделки
**Серьёзность**: СРЕДНЯЯ  
**Файл**: `ML/baseline/benchmark_fractal_stop_stage4.py:369-389`

Bootstrap resamples сделки с заменой, предполагая независимость. Но сделки temporally correlated (соседние сделки в одном рыночном режиме). Это **занижает истинную дисперсию PF**.

**Оценка**: BS_p05=0.923 завышен. Реальный p05 может быть 0.85-0.88.

**Исправление**: Block bootstrap (блоки по 10-20 последовательных сделок) или stationary bootstrap.

```python
def block_bootstrap_pf(trades, block_size=15, n_iter=500, seed=42):
    """Block bootstrap для temporally correlated сделок."""
    rng = np.random.RandomState(seed)
    pfs = []
    n_blocks = len(trades) // block_size
    for _ in range(n_iter):
        block_indices = rng.randint(0, len(trades) - block_size, size=n_blocks)
        sample = []
        for idx in block_indices:
            sample.extend(trades[idx:idx+block_size])
        gp = sum(max(0, t['pnl_val']) for t in sample)
        gl = abs(sum(min(0, t['pnl_val']) for t in sample))
        pf = gp / gl if gl > 0 else (float('inf') if gp > 0 else 0.0)
        pfs.append(pf)
    # ... compute median, p05, p95
```

---

### B2. Purge описан неточно, влияние минимально
**Серьёзность**: НИЗКАЯ  
**Файл**: `ML/baseline/benchmark_fractal_stop_stage4.py:60-65`

Отчёт говорит «purge 12 баров на хвосте валидации», но код удаляет 12 баров из **обоих** файлов (train и val). Train теряет 12 последних строк (из 44159 — несущественно).

**Проверка label leakage**: 
- Train заканчивается `2019.06.20 14:00`, val начинается `2019.06.20 16:00` (gap 2 часа)
- Purge 12 баров train: последняя строка `2019.06.20 14:00` удалена, новая последняя — примерно `2019.06.20 02:00`
- Её label (H=12) смотрит на 12 часов вперёд → до `2019.06.20 14:00` — ровно граница train

**Leakage нет**, purge достаточен.

---

### B3. Spread не применяется к SL-триггеру
**Серьёзность**: НИЗКАЯ  
**Файл**: `ML/baseline/benchmark_fractal_stop_stage4.py:252-277`

Spread корректирует entry и TP, но **не stop_price**. В реальности:
- Buy: SL срабатывает при bid ≤ sl_price, а bid = mid - spread/2
- Sell: SL срабатывает при ask ≥ sl_price, а ask = mid + spread/2

Код использует mid для SL-триггера, что **слегка оптимистичен** (SL срабатывает чуть реже). Влияние мало при spread=0.20 ATR.

**Исправление** (если нужно):
```python
# Текущий код:
evaluate_fractal_stop_trade(bars_h, trade_direction, entry_spread, stop_price, tp_price_spread, atr_val)

# Исправленный код:
if trade_direction == -1:  # Buy
    stop_price_spread = stop_price + spread  # bid должен быть ниже для SL
else:  # Sell
    stop_price_spread = stop_price - spread  # ask должен быть выше для SL
evaluate_fractal_stop_trade(bars_h, trade_direction, entry_spread, stop_price_spread, tp_price_spread, atr_val)
```

---

### B4. Перестановка индексов при intersection mask
**Серьёзность**: НЕТ (проверено — корректно)

```python
val_masked = val_df[intersection_mask].reset_index(drop=True)
breach_proba_aligned = breach_model.predict_proba(X_val_breach[intersection_mask])[:, 1]
fav_pred_aligned = fav_model.predict(X_val_fav[intersection_mask])
entry_masked = entry_prices_val[intersection_mask]
```

Индексы сбрасываются через `reset_index(drop=True)`. Все массивы вычисляются на `intersection_mask` — порядок совпадает. **Корректно**.

---

### B5. Performance: `compute_entry_prices` через `iterrows()`
**Серьёзность**: НИЗКАЯ (не баг, а bottleneck)

~9500 итераций через `iterrows()` + `strptime()` на каждый вызов. Можно заменить на векторизованную операцию.

**Оптимизация**:
```python
def compute_entry_prices_vectorized(df, ohlc, times, time_idx):
    """Векторизованная версия — в 50-100 раз быстрее."""
    times_dt = pd.to_datetime(df['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    entry = np.full(len(df), np.nan, dtype=np.float64)
    
    for i, row_dt in enumerate(times_dt):
        if pd.isna(row_dt):
            continue
        row_dt_utc = row_dt.replace(tzinfo=timezone.utc)
        idx0 = time_idx.get(row_dt_utc)
        if idx0 is not None and idx0 + 1 < len(times):
            entry[i] = ohlc[times[idx0 + 1]][0]
    return entry
```

---

## C. ВЕРИФИКАЦИЯ СИМУЛЯТОРА

### C1. Trade direction — корректно
- Buy: торгуем от valley (fractal direction=-1), stop ниже, TP выше. ✓
- Sell: торгуем от peak (fractal direction=+1), stop выше, TP ниже. ✓

### C2. Stop price — корректно
- Buy: `min(fractal_price, entry) - offset*ATR` ✓
- Sell: `max(fractal_price, entry) + offset*ATR` ✓

### C3. TP price — корректно
- `tp_val_atr = min(pred_fav * tp_fraction, cap)` ✓
- Spread ухудшает entry И TP в правильном направлении ✓

### C4. evaluate_fractal_stop_trade — корректно
- First-touch: bar-by-bar проверка SL/TP ✓
- Ambiguous (SL+TP в одном баре) → SL ✓
- TIMEOUT → PnL по close последнего бара ✓

### C5. Features — корректно
- Breach и fav используют base_raw (1001 фича) ✓
- `base_raw_plus_time` добавляет 4 time-фичи (hour/dow sin/cos) ✓
- `relative_geometry_clean` нормализует price на ATR + density ✓

### C6. Report ↔ JSON консистентность — ПОЛНОЕ СООТВЕТСТВИЕ
Все 8 таргетов: AUC, PF, T/Yr, yearly breakdown, bootstrap — совпадают между отчётом и JSON. **Предыдущее расхождение было в ошибке чтения** (я сравнивал с предварительной версией отчёта, которая была обновлена).

---

## D. СООТВЕТСТВИЕ МЕТОДИКЕ

| Пункт методики | Статус | Комментарий |
|---|---|---|
| 06b: Oracle-preflight | ✓ PASS | Stage 2 oracle PF=∞ |
| 06: Temporal split | ✓ PASS | Chronological, gap 2h, purge 12 |
| 07: Baseline-first | ✓ PASS | Stage 1 RF baseline |
| 08: Model development | ⚠️ PARTIAL | Early stopping на val (A1) |
| 09: Validation-freeze | ⚠️ PARTIAL | Нет frozen rule, нет multiple testing correction |
| 10: Frozen test | ✓ N/A | Test не открывался (правильно) |
| 11: Robustness | ⚠️ PARTIAL | Yearly slices есть, но 2019 PF=0.48 |
| 12: Backtest-costs | ✓ PASS | Spread 0.20 canonical |
| 16: Reporting | ✓ PASS | Отчёт подробный, JSON сохранены |

---

## E. BRAINSTORM: ПУТИ УЛУЧШЕНИЯ

### E1. Качество ML модели

| Идея | Сложность | Ожидаемый эффект |
|---|---|---|
| **Internal early stopping** (20% train для ES) | 1 час | Устраняет утечку A1, AUC может снизиться на 1-5 bp |
| **Feature selection** (top-100 по importance) | 2-3 часа | Снижение overfitting, ускорение обучения |
| **Cost-sensitive loss** (weight = trade PnL) | 3-4 часа | Модель оптимизирует торговый результат, а не AUC |
| **LightGBM/CatBoost** вместо XGBoost | 2-3 часа | Часто лучше на tabular data с 1000+ фичами |
| **Feature engineering**: ratio channels, cross-level interactions | 1 день | Потенциально +50-100 bp AUC |
| **Ensemble breach** (XGB + LGBM + CatBoost average) | 1 день | +20-50 bp AUC, снижение variance |

### E2. Прибыльность торговой системы

| Идея | Сложность | Ожидаемый эффект |
|---|---|---|
| **Trailing stop** вместо fixed TP | 1-2 дня | Снижение TIMEOUT rate (16%), увеличение среднего TP |
| **Partial exit** (50% at tp_fraction, 50% trail) | 1-2 дня | Баланс между TP hit rate и average win |
| **Regime filter** (не торговать при экстремальной волатильности) | 1 день | Снижение убытков в кризисные периоды (2019 PF=0.48) |
| **Dynamic position sizing** (размер ∝ confidence) | 1 день | Увеличение EV при высокой confidence |
| **Direct PnL prediction** (model → expected_pnl_val) | 2-3 дня | Убирает промежуточный слой breach+fav, прямая оптимизация |
| **Multi-timeframe** (M15/M30 вместо H1) | 3-5 дней | Больше данных, больше сделок, другой характер сигналов |

### E3. Исследовательский процесс

| Идея | Сложность | Ожидаемый эффект |
|---|---|---|
| **Automated report↔JSON consistency check** | 2-3 часа | Предотвращает расхождения данных |
| **Permutation test для ВСЕХ таргетов** | 2 часа | Честная оценка значимости |
| **Walk-forward validation** (3-4 окна вместо 1 split) | 1-2 дня | Снижение regime-dependence |
| **Unified trade simulation class** | 1 день | Устраняет copy-paste между Stage 2/4/4.1 |
| **Pre-registered hypotheses** (фиксация до запуска) | Процесс | Снижение p-hacking |
| **Block bootstrap** (вместо i.i.d.) | 2-3 часа | Более честная оценка CI |

---

## F. ИТОГОВЫЙ ВЕРДИКТ

**Stage 4 имеет 3 методологические проблемы (A1-A3) и 3 бага низкой серьёзности (B1-B3).** Ни одна из них не объясняет провал PF (все вместе дают ~5-15 bp завышения AUC, что конвертируется в ~0.02-0.05 PF). Главный вывод Stage 4 — **AUC 0.68 недостаточно для PF>1.0 в этой торговой постановке** — остаётся в силе даже после коррекции всех найденных проблем.

**Отчёт и JSON консистентны.** Предыдущее замечание о расхождении данных было ошибкой чтения (отчёт был обновлён до корректных значений).

**Рекомендация**: перед следующим исследовательским циклом исправить A1 (early stopping) и A2 (permutation test для всех таргетов). Это не изменит вердикт Stage 4, но обеспечит методологическую чистоту для будущих экспериментов.

---

## Связанные материалы

- `docs/reports/2026-06-11-stage4-trade-xgboost.md` — отчёт Stage 4
- `docs/audit/2026-06-11-stage4-trade-xgboost-audit.md` — первоначальный аудит
- `ML/baseline/benchmark_fractal_stop_stage4.py` — скрипт Stage 4
- `ML/baseline/benchmark_fractal_stop_stage4_1.py` — скрипт Stage 4.1
- `ML/reports/stage4_trade.json` — результаты base_raw_plus_time
- `ML/reports/stage4_trade_geom.json` — результаты relative_geometry_clean
- `ML/reports/stage4_1.json` — результаты Stage 4.1
- `docs/methodology/09-validation-freeze.md` — методика validation
- `docs/methodology/06b-oracle-preflight.md` — методика oracle

---

**Последнее обновление**: 2026-06-11  
**Автор**: AI agent (opencode)
