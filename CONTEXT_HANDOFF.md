# Контекст для продолжения работы — Phase B.1 Signal Filtering

> Этот файл создан 2026-04-01 для передачи контекста новому ИИ-агенту.  
> Удалить после использования.

---

## Что это за проект

Автоматическая торговая система на XAUUSD (золото), H1 таймфрейм. MetaTrader 4 (MQL4) + Python ML pipeline.

**Архитектура:**
1. MQL4 библиотека `lib_PIC.mqh` собирает фракталы (ценовые уровни) и записывает CSV
2. Python `processing/normalize.py` (через `label_main.py`) нормализует данные и создаёт таргеты
3. Python `ML/train.py` обучает Transformer модель (regression_updn task)
4. Python `API/generate_signals.py` генерирует `ml_signals.csv` из обученной модели
5. MQL4 EA `$o$imple.mq4` + `lib_ML_Signal.mqh` читает CSV и торгует

**Ключевые файлы:**
- `ML/data_loader.py` — парсинг фракталов, 22-поля → 20 фичей (X), 10 таргетов (Y)
- `ML/train.py` — обучение, early stopping по pearson_r
- `ML/models.py` — архитектура Transformer
- `ML/losses.py` — DirectionalAsymmetricLoss
- `ML/utils.py` — метрики, UPDN_TARGET_NAMES
- `processing/normalize.py` — нормализация updn через p85, UPDN_FIELDS (6 длинных для пула)
- `API/generate_signals.py` — инференс + CSV генерация
- `API/signal_research.py` — **НОВЫЙ** — статистика MFE/MAE по сигналам
- `MT/MQL4/Include/lib_ML_Signal.mqh` — чтение CSV в EA, фильтры, SL/TP логика
- `MT/MQL4/Experts/$o$imple.mq4` — EA с extern параметрами
- `DATA/XAUUSD_H1_OHLC.csv` — OHLC данные для исследований (126K баров)

---

## Текущее состояние (2026-04-01)

### Модель
- **Задача:** regression_updn — предсказание 10 таргетов (up_3, dn_3, up_6, dn_6, up_12, dn_12, up_24, dn_24, up_48, dn_48)
- **Таргеты:** MFE (max favorable excursion) за N баров, нормализованные через p85 percentile. Значения [0, 1]
- **Архитектура:** Transformer, d_model=32, nhead=8, num_layers=3, dim_feedforward=128, dropout=0.166
- **Обучение:** lr=0.00228, batch=256, seq_len=20, epochs=100 (early stop at 36)
- **Результат:** pearson_r=0.5625 (средний по 10 таргетам). Per-target: up_3=0.80, up_6=0.67, up_12=0.54, up_24=0.43, up_48=0.35
- **Чекпоинт:** `ML/checkpoints/transformer_updn_best.pt`
- **MT4 PF:** 1.18 (584 сделки, просадка 12.66%) — на OOS тестовом периоде

### Формат CSV (v3.0)
```
time;signal;up_3;dn_3;up_6;dn_6;up_12;dn_12;up_24;dn_24;up_48;dn_48
2004.07.07 20:00;0;0.2041;0.0282;0.2573;0.0659;0.3215;0.1227;0.4013;0.1955;0.4829;0.281
```
- `signal`: 1 (BUY), -1 (SELL), 0 (FLAT) — на основе ratio_12 = up_12/(dn_12+eps) > theta (2.665)
- ratio вычисляется в EA на лету, не хранится в CSV

### Фракталы (22 поля)
```
T:P:Dir:Frnt:Back:Strong:Brk:Rev:Pwr:Cnt:Imp:Up12:Dn12:Up24:Dn24:Up48:Dn48:Up3:Dn3:Up6:Dn6:FractalAtr
```
- Поля 0-16 → X[0-15] (16 фичей фрактала, время отдельно)
- Поля 17-20 (up_3..dn_6) → пропускаются в X (это таргеты, не фичи)
- Поле 21 (fractal_atr) → X[16] (ATR_RATIO_IDX)
- X[17-19] = time features (sin/cos hour, day_of_week)
- Итого: 20 фичей на фрактал, 100 фракталов → X shape (batch, 100, 20), seq_len=20 → (batch, 20, 20)

### EA параметры (lib_ML_Signal.mqh v3.0)
```mql4
extern double ML_MinRatio      = 3.5;   // Порог ratio для входа
extern double ML_MaxRatio      = 0;     // Верхний порог (0=без ограничения)
extern double ML_MaxRR         = 4.0;   // Макс множитель R:R
extern int    ML_RR_Mode       = 0;     // 0=min(ratio/MinRatio,MaxRR)
extern double ML_ScaleK        = 20.0;  // Множитель pred -> ATR для SL
extern double ML_Min_SL_ATR    = 2.0;   // Минимальный SL в ATR
extern bool   ML_BypassTrend   = true;  // Игнорировать трендовый фильтр
extern bool   ML_ExitEnabled   = true;  // Закрывать при reverse-сигнале
extern double ML_ExitThreshold = 2.0;   // Мин ratio для exit
extern double ML_Filter3       = 0.0;   // Фильтр up_3/dn_3 (0=выкл)
extern double ML_Filter6       = 0.0;   // Фильтр up_6/dn_6 (0=выкл)
extern double ML_Trl_Start_ATR = 1.0;   // Активация трала
extern double ML_Trl_Step_ATR  = 1.5;   // Дистанция трала
```

SL/TP логика (текущая):
- BUY: sl_dist = max(dn_12 * ML_ScaleK * ATR, ATR * ML_Min_SL_ATR), tp_dist = sl_dist * CalcRR(ratio)
- SELL: sl_dist = max(up_12 * ML_ScaleK * ATR, ATR * ML_Min_SL_ATR), tp_dist = sl_dist * CalcRR(ratio)

---

## Исследование качества сигналов (API/signal_research.py)

Запуск: `python -m API.signal_research --test-only`

### Ключевые находки (OOS период):

**1. MFE/MAE по горизонтам (2603 сигнала):**
| Horizon | MFE/MAE | Net_mean | WinRate | PF   |
|---------|---------|----------|---------|------|
| 3H      | 1.01    | 0.0      | 48.5%   | 1.00 |
| 6H      | 1.03    | 0.5      | 50.1%   | 1.08 |
| 12H     | 1.05    | 1.1      | 49.2%   | 1.13 |
| 24H     | 1.06    | 2.0      | 50.9%   | 1.17 |
| 48H     | 1.08    | 2.6      | 50.8%   | 1.15 |

**2. Нелинейность ratio (12H):**
| ratio | N   | PF   | TotalNet |
|-------|-----|------|----------|
| 2-3   | 635 | 1.26 | +1289    |
| 3-4   | 941 | 0.87 | **-1109**|
| 4-5   | 369 | 1.95 | +2367    |
| 5+    | 652 | 1.05 | +216     |

Бакет ratio 3-4 **убыточен** (PF=0.87). Текущий ML_MinRatio=3.5 попадает в середину этого бакета.

**3. Filter3/Filter6 бесполезны:**
96% сигналов имеют ratio_3 > 5.0. Модель всегда согласна по направлению на всех горизонтах. Любой порог ML_Filter3 от 1.0 до 5.0 отсекает одни и те же 4% сигналов.

**4. Лучшие SL/TP (фиксированные):**
- SL=5, TP=30: PF=1.43, R:R=6x, WinRate=35.8%
- SL=5, TP=20: PF=1.38, R:R=4x
- Текущий адаптивный SL/TP даёт PF=1.18 — хуже фиксированного

**5. Корреляция pred vs reality:**
- Слабая (0.13-0.21). Модель хороша в направлении, плоха в амплитуде

---

## Активные планы (обязательно прочитать)

Работа ведётся в рамках единого плана повышения PF. Три документа:

| Документ | Назначение |
|----------|-----------|
| [`docs/superpowers/specs/2026-03-27-pf-improvement-design.md`](docs/superpowers/specs/2026-03-27-pf-improvement-design.md) | Общая архитектура улучшений, диагностика корневых причин, цели (PF ≥ 2.0) |
| [`docs/superpowers/plans/2026-03-27-pf-improvement-phase-a.md`](docs/superpowers/plans/2026-03-27-pf-improvement-phase-a.md) | Phase A: исследования + EA оптимизация (цель PF ≥ 1.2–1.5 как baseline) |
| [`docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md`](docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md) | Phase B: новые таргеты + лимитный вход (цель PF ≥ 2.0) |

**Где мы сейчас:** Phase A завершена (PF вырос с 0.53 → 1.18). Phase B.1 (добавление up_3/dn_3/up_6/dn_6 как таргетов и фильтров) технически реализована, но фильтры оказались статистически бесполезны в текущей форме. Продолжаем Phase B — ищем способ использовать short-term предсказания или улучшить SL/TP логику.

---

## Что нужно сделать дальше (не начато)

### Приоритет 1: Улучшить PF через фильтрацию/SL/TP

**Вариант A — Исключить убыточный ratio-бакет:**
Текущий ML_MinRatio=3.5 → попадаем в бакет 3-4 (PF=0.87). Варианты:
- ML_MinRatio=4.0 (отсечь 3-4, оставить 4-5 и 5+)
- ML_MinRatio=2.0 + ML_MaxRatio=3.0 (только бакет 2-3, PF=1.26)
- ML_MinRatio=4.0 + ML_MaxRatio=5.0 (только бакет 4-5, PF=1.95 но мало сделок)

**Вариант B — Фиксированный SL/TP:**
Заменить адаптивный SL/TP на фиксированный (SL=5, TP=30 в пунктах). Это потребует изменений в lib_ML_Signal.mqh. Но пункты — это не ATR-нормализованные значения, нужно пересчитать в ATR.

**Вариант C — Амплитудный фильтр:**
Вместо ratio up_3/dn_3, фильтровать по абсолютной величине up_3 (или up_6). Например: BUY только если up_3 > 0.15. Требует дополнительного исследования в signal_research.py.

**Вариант D — Комбинация:**
Наиболее перспективно: ML_MinRatio=4.0 (исключить бакет 3-4) + оптимизация SL/TP.

### Приоритет 2: Phase B.1 в EA (отложено)
Добавить up_3/dn_3 как реальный фильтр в EA. Текущая реализация (ratio threshold) не работает. Нужен новый алгоритм использования коротких горизонтов.

---

## Исторический контекст (для понимания решений)

1. **Баг ATR-индекса (закрыт):** При расширении с 18 до 22 полей fractal_atr сдвинулся с idx 17 → 21. Проверка `== 18` стала ложной → X=нули → модель на пустых данных. Исправлено + 3-уровневая валидация в data_loader.py.

2. **Нормализация updn:** Используется p85 percentile от UPDN_FIELDS (6 длинных горизонтов: up_12..dn_48). Короткие горизонты (up_3..dn_6) нормализуются этими же значениями, но НЕ входят в пул расчёта p85. Это сделано намеренно, чтобы не сдвигать перцентили вниз.

3. **Ветки git:** `main` — рабочее состояние. `phase-b-debug` — сохранён для истории отладки.

---

## Запуск ключевых команд

```bash
# Обучение модели (10 таргетов, текущие лучшие параметры)
python -m ML.train --model transformer --task regression_updn --epochs 100 \
  --lr 0.0022829 --batch_size 256 --seq_len 20 \
  --model_kwargs '{"d_model":32,"nhead":8,"num_layers":3,"dim_feedforward":128,"dropout":0.166}'

# Генерация сигналов (горизонт 12, порог 2.665)
python -m API.generate_signals --horizon 12

# Исследование качества сигналов (OOS)
python -m API.signal_research --test-only

# Перенормализация (если менялись данные)
python -m processing.label_main
```
