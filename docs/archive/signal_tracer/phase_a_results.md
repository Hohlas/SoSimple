# Phase A Results — EA Optimization
**Дата:** 2026-03-27
**Цель:** Повысить PF с 0.53 → ≥1.5 через оптимизацию интерпретации ML-сигналов без переобучения модели

---

## Исходная проблема

PF=0.53 при 922 сделках. Причины (из trade_analysis_20260324.md):
1. **ratio>4.5 → нереалистичный TP** (4–8 ATR) — TP-bound trades почти никогда не достигают цели
2. **pred_dn ≈ 0 → SL-формула бесполезна** (корреляция pred_dn с реальным adverse excursion = 0.07)
3. **BOTH_HIT в 88% случаев даёт SL первым** — path-ordering проблема
4. **Вход по рыночной цене** — после прохода от фрактала, слипаж ≈ 0.034 ATR

---

## Исследования Phase A

### Study 1 — close_price & P&L (signal_tracer.py)
- Добавлены поля: `close_price`, `mt4_pnl_pips`, `mt4_pnl_atr` в CSV
- High/Low бара нужны для path-ordering — OHLC экспортирован отдельным скриптом

### Study 2 — Slippage Entry (DATA/XAUUSD_H1_OHLC.csv)
- Экспортировано 126,637 H1-баров через ExportOHLC.mq4
- BUY mean slippage = 0.034 ATR, SEL mean = –0.034 ATR
- Вывод: вход по лимиту на цену фрактала сэкономит ≈ 0.034 ATR на сделку

### Study 3 — ratio cap симуляция
- Фильтр ratio>4.5: SL-trades 321 → 91 (–72%)
- Фильтр ratio>4.0: SL-trades 321 → 54 (–83%), но сделок слишком мало
- Оптимум: ML_MaxRatio=4.5

### Study 4 — RR Mode симуляция
- Mode 0 (min/cap): грубое отсечение
- Mode 1 (log+cap): плавное — log(ratio/MinRatio)+1, cap=2.5
- Mode 2 (sqrt+cap): промежуточное
- Выбор: Mode=1 (log+cap) — наиболее стабильный

### Study 5 — Walk-forward валидация
| Период | Сделки | WR | PF |
|---|---|---|---|
| 2004–2010 | 31 | 55% | 1.42 |
| 2011–2015 | 89 | 51% | 1.38 |
| 2016–2019 | 74 | 52% | 1.21 |
| 2020–2022 | 65 | 48% | 1.18 |
| 2023–2024 | 58 | 49% | 1.15 |
| 2025H2 | 50 | 44% | **0.63** |

5/6 полугодий PF≥1.0. 2025H2 — слабость под investigation.

---

## EA изменения

### lib_ML_Signal.mqh
- `ML_CalcRR()` — функция динамического R:R (Mode 0/1/2)
- ML-exit блок (sig реверс → закрытие позиции)
- ML_MaxRatio фильтр для BUY и SELL
- ML_MaxRatio, ML_RR_Mode, ML_RR_Cap, ML_ExitEnabled, ML_ExitThreshold → extern в $o$imple.mq4

### ExportOHLC.mq4 (новый скрипт)
- Экспорт H1 OHLC в DATA/XAUUSD_H1_OHLC.csv для path-ordering анализа

---

## MT4 Тест результаты

| Параметр | v1 (baseline) | v2/v3 (Phase A) |
|---|---|---|
| PF | 0.53 | **1.23** |
| Сделок | 922 | 367 |
| WR | ~47% | 49.05% |
| Avg Win | ~$65 | $108.41 |
| Avg Loss | ~$70 | $84.92 |
| MaxDD | — | 18.37% |

**Конфиг v2/v3:**
- ML_MinRatio=3.5, ML_MaxRatio=4.5
- ML_RR_Mode=1, ML_RR_Cap=2.5
- ML_Min_SL_ATR=2.0
- ML_ExitEnabled=0 (не влияет при threshold<MinRatio)

**ML_Exit вывод:** При ML_ExitThreshold=2.0 < ML_MinRatio=3.5 логика некорректна — exit срабатывает на сигналах слабее фильтра входа. Для Phase B нужно ExitThreshold > MinRatio или отдельная модель выхода.

---

## Выводы

**Достигнуто:** PF 0.53 → 1.23 (+132%) без переобучения модели

**Не достигнуто:** Цель PF≥2.0

**Ограничения текущей архитектуры:**
1. `pred_dn` не предсказывает adverse excursion → SL наугад (всегда floor 2 ATR)
2. Path-independent targets → BOTH_HIT 88% даёт SL первым
3. Вход по рынку (не лимит) → слипаж –0.034 ATR

---

## Phase B план

1. **Path-ordered targets** — на основе H1 OHLC определить что ударило первым (High или Low), переобучить модель на реальный first-barrier-hit
2. **Лимитный ордер** — Buy Limit на цену фрактала с экспирацией
3. **Мультитаймфреймные сигналы** — добавить 3H/6H прогнозы как фичи
4. **Asymmetric loss** — штрафовать за pred_dn ошибки сильнее
5. **Pullback entry** — фильтр (up_12>X) + (dn_3<Y) перед входом

---

*Следующая фаза: docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md*
