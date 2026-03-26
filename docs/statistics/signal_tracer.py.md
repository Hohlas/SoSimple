# signal_tracer.py — Trade-Level Reconciliation

> **Версия**: v2.2 (2026-03-25)
> **Назначение**: Диагностика расхождения Python ML OOS (PF=4.50) vs MT4 Strategy Tester (PF≈1.0)
> **Тип**: Инструмент анализа, 3 режима работы

---

## 📋 Обзор

**Основной вопрос**: Почему ML модель с PF=4.50 в Python дает PF=1.0 в MT4?

### Гипотезы расхождения

**1. MFE/MAE иллюзия (BOTH_HIT)** — главная гипотеза
Python OOS оценивал качество предсказания через `up_12/dn_12` — максимальное продвижение цены за 12 баров в каждую сторону. Если `up_12 >= TP` и `dn_12 >= SL`, Python засчитывал профит (цена дошла до TP). Но MT4 закрывает первый достигнутый барьер: если SL был задет раньше TP — убыток. При k%=BOTH_HIT записей Python "видел профит", MT4 — убыток.

**2. TIMEOUT (50% убытков)**
Сделки, где ни SL ни TP не достигнуты за 12H — закрываются по трейлингу или HoldOverTime. Python OOS эти случаи учитывал иначе.

### Как устроен разбор

Сравниваются 4 источника для каждой сделки:
1. **ML предсказания** (pred_up, pred_dn, ratio) из `ml_signals.csv`
2. **Формула SL/TP** (реплика `lib_ML_Signal.mqh`)
3. **MT4 фактические уровни** (Val/Stp/Prf/ATR из лога тестера)
4. **Ground Truth** (up_12/dn_12 из `DATA/Nero_*_labeled.csv` cols[104-109], денормализованные через `Nero_*_updn_params.npy`)

**Важно**: Время сигнала в `ml_signals.csv` на 1 бар раньше времени открытия сделки в MT4.
EA читает сигнал закрытого бара T, открывает сделку на баре T+1.
Пример: `bar=2025.12.29 16:00` в логе → ищем сигнал `2025.12.29 16:00` в ml_signals.csv, сделка открыта в `17:00`.

---

## 🚀 Быстрый старт

```bash
# Single-trace: полный разбор одного сигнала (время = bar_time из лога MT4)
python statistics/signal_tracer.py --time "2023.01.03 04:00"

# Batch: топ-10 высокорейтинговых (ratio ≥ 5)
python statistics/signal_tracer.py --batch --top 10 --min-ratio 5.0

# From-Log: все убыточные SL-сделки из лога MT4
python statistics/signal_tracer.py --from-log MT/tester/logs/20260324.log --losses-only --csv-out losses.csv

# From-Log: все сделки
python statistics/signal_tracer.py --from-log MT/tester/logs/20260324.log --csv-out all_trades.csv
```

---

## 🔧 3 режима работы

### Режим 1: Single-Trace (--time)

**Что выводит:**
```
============================================================
  ДОСЬЕ СИГНАЛА: 2025.12.29 16:00
============================================================

--- ML Оценка ---
  Направление : SELL (-1)
  pred_up     : 0.080100
  pred_dn     : 0.611500
  ratio_dn    : 7.63

--- Математика MT4 (lib_ML_Signal.mqh) ---
  ML_MinRatio = 3.5, ML_MaxRR = 4.0
  SL = max(pred*ScaleK*ATR, ATR*Min_SL_ATR) = max(26.59, 33.20) = 33.20  [Min_SL_ATR]
  TP = SL * min(ratio/MinRatio, MaxRR) = 72.39
  R:R = 1 : 2.18

--- Ground Truth (MFE/MAE за 12H после фрактала) ---
  Цена фрактала : 3930.60
  Реальный ВВЕРХ: 56.50
  Реальный ВНИЗ : 1.60

--- ДИАГНОЗ ---
  SL_CLEAR: SL достигнут, TP недосягаем
```

---

### Режим 2: Batch (--batch)

**Команда:**
```bash
python statistics/signal_tracer.py --batch --top 20 --min-ratio 4.0 --csv-out batch.csv
```

**Алгоритм:**
1. Загружает все сигналы из `ml_signals.csv`
2. Фильтрует по `ratio >= min_ratio`
3. Сортирует по ratio descending, берёт top N
4. Находит ground truth из `DATA/Nero_*_labeled.csv` cols[104-109], денормализует через `Nero_*_updn_params.npy`
5. Строит досье для каждого, выводит сводную таблицу + CSV

---

### Режим 3: From-Log (--from-log)

**Команда:**
```bash
python statistics/signal_tracer.py --from-log MT/tester/logs/20260324.log \
  --losses-only \
  --csv-out losses.csv
```

**Алгоритм:**
1. `parse_log()` — парсит лог MT4, извлекает все ML BUY/SELL сделки
2. Для каждой сделки: `bar_time` из лога → ищет сигнал по этому времени в `ml_signals.csv`
3. Сравнивает: **MT4 actual (Val/Stp/Prf/ATR из лога) vs Формула vs Ground Truth**
4. Классифицирует результат: LOSS(SL), WIN(TP), WIN(MKT), OPEN

**Парсинг лога:**
```
ML SELL ratio=7.63 Val=4360.88 Stp=4414.32 Prf=4244.35 ATR=26.72 bar=2025.12.29 16:00
                          ↓
2025.12.29 17:00: open #922 sell at 4360.88 sl: 4414.32 tp: 4244.35
```

---

## 🎯 4-категорийная классификация

### TP_CLEAR
✅ **TP достигнут, SL не задет**
- У BUY: `up_12 >= tp_dist` И `dn_12 < sl_dist`

### SL_CLEAR
❌ **SL достигнут, TP недосягаем**
- У BUY: `dn_12 >= sl_dist` И `up_12 < tp_dist`

### BOTH_HIT
⚠️ **Оба барьера достигнуты (порядок неизвестен)**
- У BUY: `up_12 >= tp_dist` И `dn_12 >= sl_dist`
- **КЛЮЧ К MFE/MAE ИЛЛЮЗИИ**: Python видел оба как профит, MT4 выбило SL первым

### TIMEOUT
⏳ **Ни SL ни TP за 12H**
- Сделка закрыта по трейлингу или таймауту HoldOverTime

---

## 🔍 Входные данные

### ml_signals.csv — ML предсказания
```
time;signal;pred_up;pred_dn;ratio_up;ratio_dn
2025.12.29 16:00;-1;0.0801;0.6115;0.131;7.6312
```
- `time` = время бара, на котором сгенерирован сигнал (= `bar=` в логе MT4)

### DATA/Nero_*_labeled.csv — фрактальные данные
- Источник: `DATA/Nero_train_labeled.csv`, `DATA/Nero_validation_labeled.csv`, `DATA/Nero_test_labeled.csv`
- Фракталы отсортированы: `fractal[i][0]` (cols[4]) = новейший = триггерный фрактал
- Из `fractal[i][0]` берётся: `price`, `fractal_atr`, `direction`
- **up_12/dn_12 из fractal[i][0] всегда = 0** (фрактал только что сформирован)

### DATA/Nero_*_labeled.csv — up_12/dn_12 (нормализованные)
- Формат: `time;signal;predict;ATR;fractal0..fractal99;up_12;dn_12;up_24;dn_24;up_48;dn_48;...`
- `cols[104]=up_12`, `cols[105]=dn_12` — нормализованные значения [0,1]
- Денормализация выполняется через per-row `brk/cap` из `Nero_*_updn_params.npy`

### DATA/Nero_*_updn_params.npy — Per-row параметры нормализации
- `Nero_train_updn_params.npy`, `Nero_validation_updn_params.npy`, `Nero_test_updn_params.npy`
- Shape: `(N, 2)` — `[brk, cap]` для каждой строки
- Вычисляются в `normalize_rowwise()` из пула 606 значений: 100 фракталов × 6 updn полей + 6 row targets
- `brk = p85(non-zero pool)`, `cap = p99(non-zero pool)`
- Генерируются при запуске `label_main.py` (pipeline должен быть перезапущен после обновления)
- Соответствие строк: `updn_params[i]` ↔ строка `i` в labeled CSV (один к одному)

### MT/tester/logs/YYYYMMDD.log (только для --from-log)
```
ML BUY ratio=10.71 Val=1838.59 Stp=1830.28 Prf=1864.02 ATR=4.15 bar=2023.01.03 04:00
Tester: stop loss #1 at 1840.50
```

### MT/tester/$o$imple.ini — параметры MT4
```
ML_MinRatio = 3.5      # Порог ratio для входа
ML_MaxRR = 4.0         # Макс множитель R:R
ML_ScaleK = 20.0       # Множитель pred → ATR
ML_Min_SL_ATR = 2.0    # Минимальный SL (в ATR)
```

---

## ⚙️ Формула SL/TP (lib_ML_Signal.mqh)

```
// BUY:
SL = max(pred_dn * ML_ScaleK * ATR, ATR * ML_Min_SL_ATR)
TP = SL * min(ratio_up / ML_MinRatio, ML_MaxRR)

// SELL:
SL = max(pred_up * ML_ScaleK * ATR, ATR * ML_Min_SL_ATR)
TP = SL * min(ratio_dn / ML_MinRatio, ML_MaxRR)
```

**ATR в формуле**: MT4 использует `Atr.Fast` на баре входа. Скрипт использует `fractal_atr` из `fractal[i][0]` — значение ниже, отсюда погрешность SL/TP Δ ≈ −4/−7 пунктов.

---

## 💾 CSV Экспорт

```
time, direction, ratio, sl_dist, tp_dist, sl_atr, tp_atr, sl_source,
up_12, dn_12, category,
[для --from-log]:
val, stp, prf, atr_mt4, mt4_sl_dist, mt4_tp_dist, mt4_sl_atr, mt4_tp_atr,
sl_delta, tp_delta, atr_delta, mt4_result, close_type, close_price
```

**Разделитель**: `;` (совместимо с Excel)

---

## 📚 Дополнительно

- **Исходный код**: [statistics/signal_tracer.py](../../statistics/signal_tracer.py)
- **Формула MT4**: [MT/MQL4/Include/lib_ML_Signal.mqh](../../MT/MQL4/Include/lib_ML_Signal.mqh)
- **Нормализация**: [processing/normalize.py](../../processing/normalize.py) (`piecewise_linear_log_transform`)
- **Поток данных**: [docs/DATA_FLOW.md](../DATA_FLOW.md)

---

**Версия**: v2.2 (2026-03-25)
**Статус**: ✅ Готов
**Автор**: Antigravity + Claude
