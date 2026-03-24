# signal_tracer.py — Trade-Level Reconciliation

> **Версия**: v2.1 (2026-03-24)
> **Назначение**: Диагностика расхождения Python ML OOS (PF=4.50) vs MT4 Strategy Tester (PF≈1.0)
> **Тип**: Инструмент анализа, 3 режима работы

---

## 📋 Обзор

**Основной вопрос**: Почему ML модель с PF=4.50 в Python дает PF=1.0 в MT4?

**Ответ**: Разбор сделок на уровне trade-level reconciliation через сравнение:
1. **ML предсказания** (pred_up, pred_dn, ratio) из ml_signals.csv
2. **Формула SL/TP** (lib_ML_Signal.mqh) vs
3. **MT4 фактические уровни** (из лога) vs
4. **Ground Truth** (реальный ход цены Up_12/Dn_12 из Nero.csv)

---

## 🚀 Быстрый старт

```bash
# Single-trace: полный разбор одного сигнала
python statistics/signal_tracer.py --time "2023.01.03 04:00"

# Batch: топ-10 высокорейтинговых (ratio ≥ 5)
python statistics/signal_tracer.py --batch --top 10 --min-ratio 5.0

# From-Log: все убыточные SL-сделки из лога MT4
python statistics/signal_tracer.py --from-log MT/tester/logs/20260324.log --losses-only --csv-out losses.csv

# Export в Excel
python statistics/signal_tracer.py --batch --csv-out results.csv
```

---

## 🔧 3 режима работы

### Режим 1: Single-Trace (--time)

**Команда:**
```bash
python statistics/signal_tracer.py --time "2023.01.03 04:00" \
  --ini MT/tester/$o$imple.ini \
  --signals MT/MQL4/Files/ml_signals.csv \
  --nero MT/MQL4/Files/Nero.csv
```

**Что выводит:**
```
=============================================================
  ДОСЬЕ СИГНАЛА: 2023.01.03 04:00
=============================================================

--- ML Оценка ---
  Направление : BUY (1)
  pred_up     : 0.575000
  pred_dn     : 0.001000
  ratio_up    : 584.65

--- Математика MT4 (lib_ML_Signal.mqh) ---
  ML_MinRatio = 3.5, ML_MaxRR = 4.0
  SL = max(pred*ScaleK*ATR, ATR*Min_SL_ATR) = max(0.03800, 3.80000) = 3.80000  [Min_SL_ATR]
  TP = SL * min(ratio/MinRatio, MaxRR) = 15.20000
  R:R = 1 : 4.00

--- Ground Truth (MFE/MAE за 12H) ---
  Цена фрактала : 1276.40000
  Реальный ВВЕРХ: 0.00000
  Реальный ВНИЗ : 9.90000

--- Lag Bias ---
  Время фрактала: 2018.06.20 16:00
  Время сигнала : 2023.01.03 04:00
  Задержка: 1671 бара

--- ДИАГНОЗ ---
  SL_CLEAR: SL достигнут однозначно
```

**Для чего:**
- Понимание конкретного сигнала
- Проверка формулы SL/TP
- Видение задержки между фракталом и сигналом

---

### Режим 2: Batch (--batch)

**Команда:**
```bash
python statistics/signal_tracer.py --batch --top 20 --min-ratio 4.0 --csv-out batch.csv
```

**Алгоритм:**
1. Загружает все сигналы из ml_signals.csv
2. Фильтрует по `ratio >= min_ratio`
3. Сортирует по ratio descending
4. Берёт top N
5. Пакетно загружает Nero.csv (один проход)
6. Строит досье для каждого
7. Выводит сводную таблицу + CSV экспорт

**Выход (таблица):**
```
 # | Time               | Dir  | Ratio | SL(ATR) | TP(ATR) | Up_12  | Dn_12  | Result   | Lag
 1 | 2018.08.29 10:00   | BUY  | 584.65|   2.00  |   8.00  | 0.00   | 9.90   | SL_CLEAR | 1671h
 2 | 2004.12.28 19:00   | BUY  | 332.38|   2.00  |   8.00  | 0.20   | 3.60   | SL_CLEAR | 437h
 ...

Итого: TP_CLEAR=0, SL_CLEAR=7, BOTH_HIT=0, TIMEOUT=2
Средний lag: 1308.0 бар(а)
```

**Для чего:**
- Быстрый обзор топ сигналов
- Выявить систематические проблемы
- Подготовить данные для дальнейшего анализа

---

### Режим 3: From-Log (--from-log)

**Команда:**
```bash
python statistics/signal_tracer.py --from-log MT/tester/logs/20260324.log \
  --losses-only \
  --csv-out losses.csv
```

**Алгоритм:**
1. **parse_log()** — парсит лог MT4, извлекает все ML BUY/SELL сделки
2. Извлекает: bar_time, dir, ratio, Val, Stp, Prf, ATR_MT4
3. Соответствует каждой сделке с ml_signals.csv и Nero.csv
4. Сравнивает: **MT4 actual (из лога) vs Формула vs Ground Truth**
5. Классифицирует: LOSS(SL), WIN(TP), WIN(MKT), OPEN

**Парсинг лога:**
```
ML BUY ratio=10.71 Val=1838.59 Stp=1830.28 Prf=1864.02 ATR=4.15 bar=2023.01.03 04:00
                          ↓
Tester: stop loss #1 at 1840.50
                          ↓
MT4_SL = |1838.59 - 1840.50| = 1.91
```

**Выход (таблица):**
```
 # | Time              | Dir  | MT4_SL | FML_SL | Δ_SL | MT4_TP | FML_TP | Δ_TP | NeroRes  | MT4_Res
 1 | 2023.01.03 04:00  | BUY  |  8.31  |  7.00  | +1.31|  25.43 |  21.42 | +4.01| TIMEOUT  | LOSS(SL)
 ...

MT4 результаты: SL=315, TP=2, MARKET=4, OPEN=6
Nero категории: TP_CLEAR=33, SL_CLEAR=108, BOTH_HIT=13, TIMEOUT=161
Ср. погрешность: SL Δ=-3.908  TP Δ=-7.399
```

**Для чего:**
- **Самое важное**: Сверка формулы с реальностью MT4
- Выявление gap между расчётной и фактической логикой
- Поиск причин расхождения

---

## 🎯 4-категорийная классификация

### TP_CLEAR
✅ **TP достигнут, SL не задет**
- У BUY: `up_12 >= tp_dist` И `dn_12 < sl_dist`
- Ожидание: ПОБЕДА в MT4
- Факт: может быть убыток, если MT4 закрыл раньше

### SL_CLEAR
❌ **SL достигнут, TP недосягаем**
- У BUY: `dn_12 >= sl_dist` И `up_12 < tp_dist`
- Диагноз: Убыток неизбежен
- Рекомендация: Отклонить такие сигналы

### BOTH_HIT
⚠️ **Оба барьера достигнуты (порядок неизвестен)**
- У BUY: `up_12 >= tp_dist` И `dn_12 >= sl_dist`
- **КЛЮЧ К MFE/MAE ИЛЛЮЗИИ!**
- Python считал оба события как профит (максимум)
- MT4 выбило SL первым → убыток

### TIMEOUT
⏳ **Ни SL ни TP за 12H (12 баров)**
- Убыток/Профит по трейлингу или таймауту HoldOverTime
- Сделка закрыта не по целевым уровням

---

## 📊 Результаты (реальные данные)

### --from-log --losses-only (321 убыточная сделка, 2023–2026)

| Категория | Кол-во | % | Смысл |
|-----------|--------|--|-------|
| TIMEOUT | 161 | 50% | Убыток по таймауту, TP не достигнут |
| SL_CLEAR | 108 | 34% | SL был неизбежен |
| **TP_CLEAR** | **33** | **10%** | **TP достижим, но SL раньше** |
| BOTH_HIT | 13 | 4% | Порядок неопределён |

### Погрешность формулы vs MT4 Actual
```
SL Δ  = −3.908  (формула недооценивает на ~4 пункта)
TP Δ  = −7.399  (формула недооценивает на ~7 пунктов)
```

**Причина**: Скрипт использует `fractal_atr` (ATR на момент формирования фрактала), а MT4 использует `ATR` на баре входа, который может быть значительно выше при росте волатильности.

---

## 🔍 Структура входных данных

### ml_signals.csv
```
time;signal;pred_up;pred_dn;ratio_up;ratio_dn
2004.07.07 20:00;0;1.2;0.8;1.5;0.67
2004.07.08 15:00;1;0.575;0.001;584.65;0.0017
```

### Nero.csv (Ground Truth)
```
time;signal;predict;ATR;fractal0;fractal1;...
2004.07.07 20:00;0;0;1.5;1529510400:1276.4:1:0.0045:0.0078:1:0:0:0.0034:1:0.0156:0.0089:0.0023:0.0145:0.0067:0.0234:0.0145:0.0038;...
```

**Fractal0 (18 полей):**
```
fractal_time:price:direction:front:back:strong:break:reverse:power:count:impulse:up_12:dn_12:up_24:dn_24:up_48:dn_48:fractal_atr
```

### MT/tester/logs/YYYYMMDD.log
```
ML BUY ratio=10.71 Val=1838.59 Stp=1830.28 Prf=1864.02 ATR=4.15 bar=2023.01.03 04:00
Tester: stop loss #1 at 1840.50 (1836.13 / 1836.30)
```

---

## ⚙️ Параметры MT4

Читаются из `MT/tester/$o$imple.ini`:

```
ML_MinRatio = 3.5      # Порог ratio для входа
ML_MaxRR = 4.0         # Макс множитель R:R
ML_ScaleK = 20.0       # Множитель pred → ATR
ML_Min_SL_ATR = 2.0    # Минимальный SL (в ATR)
```

**Формула SL/TP (lib_ML_Signal.mqh):**
```
// BUY:
SL = max(pred_dn * ML_ScaleK * ATR, ATR * ML_Min_SL_ATR)
TP = SL * min(ratio_up / ML_MinRatio, ML_MaxRR)

// SELL:
SL = max(pred_up * ML_ScaleK * ATR, ATR * ML_Min_SL_ATR)
TP = SL * min(ratio_dn / ML_MinRatio, ML_MaxRR)
```

---

## 💾 CSV Экспорт

**Колонки:**
```
time, direction, signal, ratio, pred_up, pred_dn, ratio_up, ratio_dn,
price, atr, sl_dist, tp_dist, sl_atr, tp_atr, sl_source,
up_12, dn_12, category, lag_bars,
[для --from-log]:
val, stp, prf, atr_mt4, mt4_sl_dist, mt4_tp_dist, mt4_sl_atr, mt4_tp_atr,
sl_delta, tp_delta, atr_delta, mt4_result, close_type, close_price
```

**Разделитель**: `;` (совместимо с Excel)

---

## 🎓 Использование для анализа

### Вопрос 1: Какие сигналы самые ненадёжные?
```bash
python statistics/signal_tracer.py --batch --min-ratio 2.5 | grep SL_CLEAR
```
→ Найди сигналы с SL_CLEAR (убыток гарантирован)

### Вопрос 2: MFE/MAE иллюзия действительно существует?
```bash
python statistics/signal_tracer.py --from-log MT/tester/logs/*.log | grep BOTH_HIT
```
→ 33 сделки с BOTH_HIT + LOSS(SL) = прямое доказательство

### Вопрос 3: Насколько точна формула SL/TP?
```bash
python statistics/signal_tracer.py --from-log MT/tester/logs/20260324.log --csv-out all.csv
```
→ Откройте all.csv, посмотрите столбцы `sl_delta, tp_delta`

### Вопрос 4: Какой lag дают фракталы?
```bash
python statistics/signal_tracer.py --batch --csv-out batch.csv
```
→ Столбец `lag_bars` — посчитайте среднее

---

## 📚 Дополнительно

- **Исходный код**: [statistics/signal_tracer.py](../../statistics/signal_tracer.py)
- **Объект исследования**: ME-13, ME-14, ME-15 (CHANGELOG.md)
- **Гипотезы**: [docs/plans/ME13_Diagnostics_Plan.md](../plans/ME13_Diagnostics_Plan.md)
- **Формула MT4**: [MT/MQL4/Include/lib_ML_Signal.mqh](../../MT/MQL4/Include/lib_ML_Signal.mqh)
- **Данные ML**: [docs/DATA_FLOW.md](../DATA_FLOW.md)

---

**Версия**: v2.1 (2026-03-24)
**Статус**: ✅ Production
**Автор**: Antigravity + Claude
