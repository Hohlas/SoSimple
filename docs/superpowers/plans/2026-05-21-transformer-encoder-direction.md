# Transformer Fine-Tune Direction: Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Достичь BUY и SELL test PF > 1.5 через full fine-tune Transformer-энкодера на direction-таргетах с сырыми up_N/dn_N из OHLC.

**Architecture:** `transformer_updn_best.pt` (Pearson r=0.56, d_model=32, 3 layers, 8 heads) → замена регрессионной головы на классификационную (1 или 2 выхода) → full fine-tune на direction labels. Параллельно: frozen encoder → 640 признаков → RF/HGB baseline. Три семейства таргетов из сырых up/dn (TB, Trail, Reg). BUY и SELL — отдельные бинарные модели. Winner selection → один frozen test.

**Tech Stack:** Python 3.12, PyTorch (уже установлен в .venv), scikit-learn, pandas, numpy. Переиспользуем: `ML/data_loader.py`, `ML/prepare_raw_features.py`.

**Ветка:** `DeepSeek-direct-direction-results`

---

## Дизайн

### Таргеты (3 семейства)

Строятся из сырых up_N/dn_N (OHLC-derived, не нормализованных). Для BUY и SELL — симметрично.

**Target TB (Triple Barrier):**
```
BUY если up_H/ATR >= tp_level И dn_H/ATR < sl_level
SELL если dn_H/ATR >= tp_level И up_H/ATR < sl_level
```
Grid: H ∈ {6, 12, 24}, tp ∈ {2, 4, 6}, sl ∈ {1, 2}
18 комбинаций. Отсеять sparse (<500 примеров на train).

**Target Trail (Trailing Stop OHLC):**
```
BUY если trailing-stop-profit за H баров >= profit_z × ATR
SELL если trailing-stop-profit за H баров >= profit_z × ATR (обратное направление)
```
Механика: стоп следует за ценой на расстоянии trail_n × ATR (только в сторону профита).
Grid: H ∈ {12, 24, 48}, trail_n ∈ {2, 4, 6}, profit_z ∈ {2, 4, 6}
27 комбинаций. Отсеять sparse.

**Target Reg (Regression up/dn):**
Предсказание up_H/ATR, dn_H/ATR (2 continuous выхода, MSE loss). Модель обучается один раз, margin перебирается постфактум.
Сигнал:
```
BUY если up_pred − dn_pred > margin  (в ATR)
SELL если dn_pred − up_pred > margin
```
Grid: H ∈ {6, 12}, margin ∈ {2, 4, 6}
6 комбинаций (1 обучение × 6 порогов).

**Итого**: ~16 целевых комбинаций.

### Признаки

Два варианта (сравниваем):
1. **Frozen encoder (640)**: извлечь hidden states (20×32) → RF/HGB классификатор. Быстрый baseline.
2. **Full fine-tune**: заменить regression head (Linear(32,10)) на classification head (Linear(32,1) или Linear(32,2)), обучать весь энкодер + голову end-to-end.

### Модель

Для BUY: бинарный классификатор (0=SKIP, 1=BUY)
Для SELL: бинарный классификатор (0=SKIP, 1=SELL)

Fine-tune гиперпараметры:
- Optimizer: AdamW, lr ∈ {1e-4, 5e-5} (encoder), lr × 10 для головы
- Epochs: 20, early stopping (patience=5 на val F1)
- Batch size: 256 (весь train помещается)
- Loss: BCEWithLogitsLoss с pos_weight (class balance)
- Scheduler: ReduceLROnPlateau (patience=3, factor=0.5)

### Split

Train (70%): 2004–2017, Validation (15%): 2017–2021, Test (15%): 2021–2026.

### Winner Selection

1. validation_trades >= 50 для каждого направления
2. BUY negative_years == 0 И SELL negative_years == 0
3. one_sided не фильтруем (допустимо BUY-heavy, главное чтоб не zero)
4. Сортировка по `min(buy_seq_pf, sell_seq_pf)` — консервативно
5. Либо отдельные winner для BUY и SELL, комбинируем сигналы через margin rule

### Gate

- Gate A: val PF >= 1.5, seq PF >= 1.5, negative_years <= 1
- Gate D (Frozen Test): test PF >= 1.5, test seq PF >= 1.5, negative_years <= 1

---

## Файлы

| Файл | Действие | Назначение |
|------|----------|------------|
| `ML/prepare_raw_features.py` | Modify | +raw up_N/dn_N из OHLC |
| `ML/transformer_direction_train.py` | Create | Fine-tune Transformer на direction |
| `ML/benchmark_transformer_direction.py` | Create | Frozen encoder RF/HGB baseline + evaluation |
| `ML/reports/transformer_direction/` | Create | Артефакты |
| `ML/models/transformer.py` | Read | Архитектура Transformer (переиспользуем) |
| `ML/data_loader.py` | Read | Парсинг и подготовка данных |

---

## Tasks

### Task 1: Raw up_N/dn_N from OHLC

**Files:** Modify `ML/prepare_raw_features.py`

- [ ] **Step 1: Реализовать `_compute_raw_updn_from_ohlc()`**

Для каждого из 100 фракталов и 5 горизонтов (3,6,12,24,48): вычислить up_N = max(0, max(High[T:T+N]) - P), dn_N = max(0, P - min(Low[T:T+N])). Оптимизация: предвычислить rolling max/min numpy-массивы по OHLC, затем O(1) lookup.

- [ ] **Step 2: Пересобрать `raw_features_for_direction.pkl`**

```bash
python -m ML.prepare_raw_features
```

Gate: проверить корреляцию raw up_24 с labeled up_24 (нормализованным), r > 0.5.

- [ ] **Step 3: Commit**

- [ ] **Step 4: Статистическая валидация признаков и таргетов**

Перед подачей в ML проверить всё, что идёт на вход модели.

**Признаки (640 Transformer hidden states):**

```bash
python statistics/statistics.py DATA/raw_features_for_direction.pkl
```

Проверить:
- Распределение каждого измерения: нет ли коллапса (std < 1e-6), нет ли NaN
- Корреляционная матрица: нет ли идеально скоррелированных признаков (r > 0.99 — redundant)
- Дисперсия: есть ли признаки с variance ≈ 0 (не несут информации)
- Outliers: Z-score > 5 — записать в лог
- Mutual information признак↔таргет: какие hidden dimensions сильнее всего связаны с BUY/SELL

**Таргеты (TB, Trail, Reg):**
- Распределение up_N/ATR и dn_N/ATR по горизонтам: min, max, p50, p95
- BUY rate, SELL rate, SKIP rate для каждой комбинации параметров
- Баланс классов: если BUY < 3% строк — таргет слишком жёсткий
- Корреляция raw up_N (OHLC-derived) с labeled up_N (из CSV): r > 0.5 — подтверждает корректность OHLC-расчёта
- Cross-check: среднее up_24/ATR по годам — нет ли тренда (non-stationarity)

**Артефакты валидации:**
- `ML/reports/transformer_direction/feature_statistics.json`
- `ML/reports/transformer_direction/target_statistics.json`

Gate: все проверки пройдены, аномалий нет. Если обнаружены проблемы (коллапс признаков, дисбаланс, низкая корреляция) — зафиксировать и принять решение: фиксить или продолжать с оговоркой.

**STOP: после этого шага — пауза, обсуждение результатов статвалидации с пользователем перед переходом к Task 2 (ML).**

- [ ] **Step 5: Commit**

### Task 2: Подготовка данных для Transformer

**Files:** Create `ML/transformer_direction_train.py`

- [ ] **Step 1: DataLoader для direction**

Переиспользовать `ML/data_loader.py` → парсинг фракталов, **та же нормализация `normalize_rowwise()` что при обучении Transformer** (для консистентности hidden states). Тензор: (N, seq_len=20, 20 features).

- [ ] **Step 2: Загрузка сырых up/dn таргетов**

Из обновлённого `raw_features_for_direction.pkl`: колонки `f0_up_{h}_raw`, `f0_dn_{h}_raw`. Таргеты в сырых ATR-единицах (up/ATR) — без дополнительной нормализации. Пороги SL/TP прямо в ATR.

- [ ] **Step 3: Конструкторы таргетов**

```python
def build_target_tb(up_atr, dn_atr, tp_level, sl_level) -> int:
    """BUY если up_atr >= tp И dn_atr < sl. up_atr = up_raw / ATR."""
    
def build_target_trail(ohlc, ...):  
    """Переиспользовать build_target_d_masks()."""
    
def build_target_reg(up_atr, dn_atr) -> tuple[float, float]:
    """(up_atr, dn_atr) — непрерывные таргеты."""
```

- [ ] **Step 4: Commit**

### Task 3: Full Fine-Tune Transformer

**Files:** Modify `ML/transformer_direction_train.py`

- [ ] **Step 1: Загрузка чекпоинта**

Загрузить `transformer_updn_best.pt`, извлечь encoder weights. Воссоздать архитектуру из `ML/models/transformer.py`.

- [ ] **Step 2: Classification head**

Заменить regression head (Linear(32,10)) на:
- Для TB/Trail: Linear(32,1) с BCEWithLogitsLoss + pos_weight
- Для Reg: Linear(32,2) с MSE (предсказание up_atr, dn_atr)

- [ ] **Step 3: Training loop**

```python
for epoch in range(20):
    for batch in train_loader:
        hidden = encoder(batch)  # (B, 20, 32)
        pooled = hidden.mean(dim=1)  # (B, 32) — средний пулинг
        logits = classifier(pooled)
        loss = criterion(logits, targets)
        loss.backward()
        optimizer.step()
```

Early stopping на validation F1 (patience=5). Scheduler: ReduceLROnPlateau.

- [ ] **Step 4: Grid search**

Для каждой комбинации (target_family, target_params, direction, lr):
1. Обучить модель
2. Оценить на validation (PF, seq PF, yearly PF)
3. Записать в validation_grid.csv

- [ ] **Step 5: Сравнение с frozen encoder baseline**

Обучить RF/HGB на 640 frozen-encoder признаках (без fine-tune). Сравнить PF c fine-tuned моделью.

- [ ] **Step 6: Winner selection**

Исправленный протокол. Выбрать лучшую конфигурацию для BUY и SELL отдельно. Комбинированный сигнал через margin rule.

- [ ] **Step 7: Проверить GATE A**

- [ ] **Step 8: Commit**

### Task 4: Frozen Test

**Files:** Modify `ML/transformer_direction_train.py`

- [ ] **Step 1: Переобучить winner на train+validation**

- [ ] **Step 2: Оценить на test**

PF, seq PF, BUY/SELL PF, yearly PF.

- [ ] **Step 3: Проверить GATE D**

Test PF >= 1.5.

- [ ] **Step 4: Commit**

### Task 5: Отчёт и синхронизация

- [ ] **Step 1: `docs/reports/2026-05-21-transformer-direction.md`**

Сравнение с Phase A/D, frozen encoder vs fine-tune, BUY vs SELL.

**Формат отчёта — таблица с результатами всех трёх семейств:**

| Target | Model | Best PF (val) | Best Seq PF | Test PF | Test Seq PF | Trades |
|--------|-------|---------------|-------------|---------|-------------|--------|
| TB (H=24, TP=6, SL=2) | RF frozen | ... | ... | ... | ... | ... |
| TB (H=24, TP=6, SL=2) | Fine-tune | ... | ... | ... | ... | ... |
| TB (H=12, TP=3, SL=1) | RF frozen | ... | ... | ... | ... | ... |
| Trail (H=24, n=4) | RF frozen | ... | ... | ... | ... | ... |
| Trail (H=24, n=4) | Fine-tune | ... | ... | ... | ... | ... |
| Reg (H=24, m=1.0) | RF frozen | ... | ... | ... | ... | ... |
| Reg (H=24, m=1.0) | Fine-tune | ... | ... | ... | ... | ... |

Плюс для frozen-test winner: полная yearly PF таблица, BUY/SELL breakdown, win rates.

- [ ] **Step 2: CHANGELOG.md, CONTEXT_HANDOFF.md**

- [ ] **Step 3: Wiki ingest**

- [ ] **Step 4: `python wiki/wiki.py generate`**

---

## Критерии успеха

| Уровень | BUY PF | SELL PF | Seq PF | Negative Years |
|---------|--------|---------|--------|----------------|
| Min (val) | > 1.5 | > 1.0 | > 1.5 | ≤ 1 |
| Target (test) | > 1.5 | > 1.2 | > 1.5 | ≤ 1 |

## Анти-паттерны

- Test для подбора параметров
- Frozen test > 1 раза
- 3-class формулировка
- Косметический подбор порогов
