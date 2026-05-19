# План: Устойчивое улучшение Direct Direction (Phase II)

> **Дата**: 2026-05-18
> **Статус**: Утверждён (на основе аудита `docs/reports/2026-05-18-independent-audit-direct-direction.md`)
> **Цель**: Достичь `validation PF > 2.0`, `sequential PF > 2.0` на BUY-направлении; либо честно доказать невозможность.
> **Контекст**: Текущий лучший результат — Binary RF Test PF=1.23, BUY PF=1.90, SELL PF=0.62. SELL направление систематически убыточно и хуже случайного.

---

## 1. Философия плана

- **Не использовать test split** для подбора гипотез, порогов или моделей.
- **Frozen test — ровно один раз**, для финального кандидата после прохождения всех gates.
- **Нет косметического подбора**: если признаки/таргет не несут сигнала — меняем постановку, а не пороги.
- **Честный stop**: если после Phase A validation PF < 1.5 — закрываем исследование с вердиктом.
- **BUY-only приоритет**: SELL отключаем до доказательства, что он добавляет value.

---

## 2. Критерии успеха и stop-conditions

### Gate на каждый эксперимент (validation only):
- `validation_trades >= 500` (достаточная статистика)
- `validation PF >= 1.5` (минимальный viable edge)
- `validation sequential PF >= 1.3`
- `negative_years == 0` на validation (2019–2022)
- `BUY PF >= 1.3` (направление не проваливается)
- `one_sided_candidate == False` (balance >= 0.20)
- `overfitting_risk == False` (features/candidates < 0.10)

### Gate на Phase (агрегатный):
- Phase A gate: лучший BUY-only конфиг на validation имеет PF >= 1.5 и seq PF >= 1.3.
- Phase B gate: лучший конфиг на validation имеет PF >= 1.8 и seq PF >= 1.5.
- Phase C gate: лучший конфиг на validation имеет PF >= 2.0 и seq PF >= 2.0.
- Если Phase gate не пройден — stop, отчёт, вердикт.

### Final frozen test gate:
- `test PF >= 2.0`
- `test sequential PF >= 2.0`
- `test BUY PF >= 1.5` (BUY не проваливается)
- `negative_years <= 1` (допустима одна слабость)
- `test trades >= 500`

---

## 3. Архитектура решения

```
┌─────────────────────────────────────────────────────────────┐
│  Phase A: BUY-only + Alternative Target + Regime Features   │
│  ├─ A1: BUY-vs-SKIP с directional close target              │
│  ├─ A2: Добавление regime признаков (volatility, trend)     │
│  ├─ A3: Добавление временных признаков (session, weekday)   │
│  └─ A4: Rolling validation stability check                  │
├─────────────────────────────────────────────────────────────┤
│  Phase B: Transformer Feature Extractor                     │
│  ├─ B1: Извлечение hidden reps из transformer_updn          │
│  ├─ B2: Обучение lightweight classifier поверх reps         │
│  └─ B3: Ablation: reps vs tabular features                  │
├─────────────────────────────────────────────────────────────┤
│  Phase C: Ensemble + Final Frozen Test                      │
│  ├─ C1: Ensemble tabular + transformer (stacking)           │
│  ├─ C2: Threshold calibration на validation                 │
│  └─ C3: Frozen test (единственный запуск)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Phase A: BUY-only + Alternative Target + Regime Features

### A1: BUY-vs-SKIP с Directional Close Target

**Проблема**: текущий Target D (trailing profit) слишком шумный; precision BUY = 28%, recall = 14%.

**Новый таргет**:
```python
# Directional Close Target (DCT)
return_24 = (Close[t+25] - Open[t+1]) / ATR[t]  # 24-bar directional return
buy_good = (return_24 >= profit_threshold) & (max_adverse_24 <= adverse_threshold)
```
- `profit_threshold ∈ {0.5, 1.0, 1.5} ATR`
- `adverse_threshold ∈ {1.0, 1.5, 2.0} ATR`
- Проверить на меньшем шуме и более высокой разделимости.

**Модель**: RandomForest BUY-vs-SKIP (binary).
**Признаки**: nearest_k4 (97 features) + ATR + fractal0_direction.
**Оценка**: validation PF, precision, recall, calibration curve.

**Gate A1**: validation PF >= 1.3 (ниже основного gate, это baseline для Phase A).

### A2: Regime-Aware Features

**Признаки**:
```python
# Trend regime
price_ma_50 = SMA(Close, 50)
trend_strength = (Close - price_ma_50) / ATR  # >0 = uptrend, <0 = downtrend

# Volatility regime
atr_ratio = ATR[0] / ATR[20]  # текущая vs 20-баровая
vol_percentile = percentile(ATR[0], window=100)  # где текущая ATR в истории

# Fractal regime
fractal_density = count(non_empty fractals in last 20 bars)
strong_fractal_ratio = count(strong==1) / count(valid)
```

**Обоснование**: текущая модель не знает, находится ли рынок в тренде или в боковике. 2022 год — transition from bear to bull; модель без regime info не адаптируется.

**Gate A2**: добавление regime features улучшает validation PF минимум на +0.10 относительно A1.

### A3: Session / Temporal Features

**Признаки**:
- `hour_sin`, `hour_cos` (циклическое время суток)
- `weekday` (0–6)
- `month` (1–12, сезонность золота)
- `days_since_last_strong_fractal`

**Обоснование**: XAUUSD имеет сессионные паттерны (London open, NY open, Asian session). Статистика signal_research показала нелинейность по ratio в зависимости от времени.

**Gate A3**: temporal features добавляют +0.05 к validation PF.

### A4: Rolling Validation Stability

**Методика**:
- Разбить train (2004–2019) на 5 rolling folds по 3 года каждый.
- Обучить на fold N, проверить на fold N+1.
- Требование: PF >= 1.3 на всех folds.

**Обоснование**: текущий single split может скрывать нестабильность. Rolling validation обнаружит regime-dependent слабости до frozen test.

**Gate A4**: стабильность на 4 из 5 rolling folds (PF >= 1.3).

### Phase A Aggregate Gate
- Лучший конфиг: validation PF >= 1.5, seq PF >= 1.3, 0 negative years, BUY balance >= 0.20.
- Если не пройден → stop, отчёт: "Постановка не позволяет достичь PF>1.5 без новых данных".

---

## 5. Phase B: Transformer Feature Extractor

### B1: Извлечение Hidden Representations

**Метод**:
```python
# Загрузить transformer_updn_best.pt
# Пропустить train+validation через encoder (без classification head)
# Получить hidden state для каждой строки: shape (batch, d_model)
# Использовать как признаки для downstream classifier
```

**Обоснование**: Transformer обучен на 10 up/dn таргетах с Pearson r=0.56. Его hidden representations содержат temporal patterns из 20-фрактальной последовательности, которые табличный RF не видит.

**Gate B1**: hidden reps дают validation PF >= 1.3 на BUY-vs-SKIP с DCT target.

### B2: Lightweight Classifier поверх Representations

**Архитектура**:
- Input: transformer hidden reps (d_model=32) + tabular regime features (~10)
- Classifier: 1–2 слоя MLP или RF
- Target: BUY-vs-SKIP (DCT)

**Gate B2**: classifier на reps превосходит лучший Phase A результат на +0.15 PF.

### B3: Ablation Study

- reps only vs tabular only vs reps + tabular
- Оценить вклад каждого источника.

**Gate B3**: комбинация reps + tabular > max(reps_only, tabular_only).

### Phase B Aggregate Gate
- Лучший конфиг: validation PF >= 1.8, seq PF >= 1.5.
- Если не пройден → переход к Phase C с текущим лучшим (но вероятность PF>2.0 низкая).

---

## 6. Phase C: Ensemble + Final Frozen Test

### C1: Stacking Ensemble

**Архитектура**:
- Level 0: Phase A tabular model + Phase B transformer model (независимые предикторы)
- Level 1: meta-classifier (logistic regression или RF) на объединённых probabilities
- Target: BUY-vs-SKIP (DCT)

**Gate C1**: ensemble превосходит лучшего индивидуального участника на +0.05 PF.

### C2: Threshold Calibration

**Метод**:
- Построить calibration curve на validation.
- Выбрать порог, максимизирующий PF (не accuracy).
- Проверить monotonicity: higher confidence → higher win rate (не инверсия, как у SELL в текущей модели).

**Gate C2**: calibration curve монотонна; top-decile precision >= 0.40.

### C3: Final Frozen Test

**Процедура**:
1. Выбрать единственного кандидата: лучший конфиг по validation PF + seq PF + stability.
2. Переобучить на train+validation (53,349 строк).
3. Запустить один frozen test на test (2022-2026).
4. Зафиксировать все артефакты: `ML/reports/entry_path_v2_*/`.

**Final Gate**:
- `test PF >= 2.0`
- `test sequential PF >= 2.0`
- `test BUY PF >= 1.5`
- `negative_years <= 1`
- `test trades >= 500`

---

## 7. Риски и mitigation

| Риск | Вероятность | Влияние | Mitigation |
|------|-------------|---------|------------|
| Phase A gate не пройден | Средняя | Высокое | Честный stop с отчётом. Вердикт: постановка нежизнеспособна. |
| Transformer reps не переносятся на BUY/SKIP | Низкая | Среднее | Fallback к tabular-only + regime features. |
| Regime features нестабильны в live | Средняя | Среднее | Использовать только causal features (rolling на прошлых барах). |
| Overfitting на validation при threshold tuning | Средняя | Высокое | Фиксированный grid, нет оптимизации под конкретную метрику. |
| 2022 test period слишком стрессовый | Высокая | Высокое | Rolling validation включает аналогичные stress periods (2008, 2020). |

---

## 8. Подзадачи для субагентов

### Субагент 1: Phase A — Alternative Target + BUY-only
**Задача**: Реализовать Directional Close Target (DCT), BUY-vs-SKIP модель, regime features, temporal features. Провести A1–A4. Вернуть лучший конфиг и validation артефакты.
**Вход**: `DATA/Nero_*_labeled.csv`, `DATA/XAUUSD_H1_OHLC.csv`
**Выход**: `ML/reports/entry_path_v2_phase_a/`, validation_grid.csv, summary.json
**Gate**: Phase A aggregate gate.

### Субагент 2: Phase B — Transformer Feature Extractor
**Задача**: Извлечь hidden representations из `transformer_updn_best.pt`. Обучить lightweight classifier. Провести ablation B3. Вернуть лучший конфиг.
**Вход**: `ML/checkpoints/transformer_updn_best.pt`, `DATA/Nero_*_labeled.csv`
**Выход**: `ML/reports/entry_path_v2_phase_b/`, reps CSV, ablation summary
**Gate**: Phase B aggregate gate.

### Субагент 3: Phase C — Ensemble + Frozen Test
**Задача**: Объединить лучшие модели из Phase A и B (stacking). Провести calibration C2. Запустить frozen test. Сформировать финальный отчёт.
**Вход**: Артефакты Phase A и B.
**Выход**: `ML/reports/entry_path_v2_final/`, frozen_test.json, docs/reports/
**Gate**: Final gate.

### Субагент 4: Инфраструктура + Тесты
**Задача**: Написать unit-тесты для новых модулей (DCT target builder, regime features, transformer rep extractor). Обеспечить воспроизводимость.
**Вход**: Код Phase A–C.
**Выход**: `tests/test_entry_path_v2_*.py`, CI-прогон.

---

## 9. Расписание (ориентировочное)

| Phase | Эксперименты | Оценка времени | Gate |
|-------|-------------|----------------|------|
| A1 | DCT target grid | 2–3 часа | PF >= 1.3 |
| A2 | Regime features | 2–3 часа | +0.10 к A1 |
| A3 | Temporal features | 1–2 часа | +0.05 к A2 |
| A4 | Rolling validation | 3–4 часа | 4/5 folds PF >= 1.3 |
| **A total** | | **8–12 часов** | **PF >= 1.5** |
| B1 | Transformer reps | 2–3 часа | PF >= 1.3 |
| B2 | Classifier on reps | 2–3 часа | +0.15 к Phase A |
| B3 | Ablation | 1–2 часа | combo > single |
| **B total** | | **5–8 часов** | **PF >= 1.8** |
| C1 | Stacking | 1–2 часа | +0.05 |
| C2 | Calibration | 1 час | monotonic |
| C3 | Frozen test | 1 час | PF >= 2.0 |
| **C total** | | **3–4 часов** | **PF >= 2.0** |

**Общее время**: 16–24 часа агентного времени.

---

## 10. Артефакты

### Код (новые/изменённые файлы)
- `ML/entry_path_v2_targets.py` — Directional Close Target builder
- `ML/entry_path_v2_features.py` — regime + temporal features
- `ML/entry_path_v2_buy_only.py` — BUY-vs-SKIP benchmark runner
- `ML/entry_path_v2_transformer_reps.py` — hidden rep extractor
- `ML/entry_path_v2_ensemble.py` — stacking + frozen test
- `tests/test_entry_path_v2_*.py` — тесты

### Отчёты
- `ML/reports/entry_path_v2_phase_a/` — Phase A артефакты
- `ML/reports/entry_path_v2_phase_b/` — Phase B артефакты
- `ML/reports/entry_path_v2_final/` — frozen test + финальный отчёт
- `docs/reports/2026-05-1X-entry-path-v2-results.md` — канонический отчёт

---

## 11. Честный вердикт (если gates не пройдены)

Если после Phase A validation PF < 1.5:
> **Вердикт**: Табличные геометрические признаки fractal0..99 + любой из проверенных таргетов (trailing profit, directional close) не содержат достаточного сигнала для достижения PF>1.5 на XAUUSD H1 в период 2019–2022. Следующий шаг: либо (а) добавление новых источников данных (order flow, макро-ивенты), либо (б) переход на другой таймфрейм или инструмент.

Если Phase A пройдена, но Phase B не даёт PF >= 1.8:
> **Вердикт**: BUY-only с regime features даёт жизнеспособный edge (PF~1.5–1.7), но PF>2.0 требует более мощного feature extractor или дополнительных данных. Рекомендуется production-деплой BUY-only с conservative risk management и дальнейшее исследование Transformer + multi-task learning.

Если Phase C frozen test PF < 2.0:
> **Вердикт**: Модель имеет edge, но не достаточный для целевого PF>2.0 на OOS. Рекомендуется: (а) accept текущий лучший как production baseline, (б) продолжить сбор live данных для online learning, (в) исследовать portfolio-level комбинацию с другими системами (quality, frequency).

---

## 12. Связь с предыдущим планом

| Элемент | Предыдущий план (E0–E5) | Новый план (Phase A–C) |
|---------|------------------------|------------------------|
| Формулировка | 3-class SELL/SKIP/BUY | BUY-only (SELL disabled) |
| Таргет | Target D (trailing profit) | Directional Close Target |
| Признаки | nearest_k4 (97 features) | nearest_k4 + regime + temporal |
| Модель | RF / HGB табличные | RF табличный + Transformer reps |
| Валидация | Single split | Rolling validation |
| Ensemble | Нет | Stacking tabular + transformer |
| SELL направление | Проблема, не решена | Отключено до доказательства value |
| Gate | PF >= 1.15 | PF >= 1.5 → 1.8 → 2.0 |

---

**Утверждено**: Аудитор + пользователь (pending).
**Следующий шаг**: Запуск Субагента 1 (Phase A) после утверждения плана.
