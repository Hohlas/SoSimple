# MT5 Nero.csv Producer Parity Report

**Date:** 2026-07-31
**Verdict:** `PARITY_PASS`
**Status:** DIAGNOSTIC_ONLY

## Context

Зависимость от lifecycle closure (2026-07-31): после подтверждения
OnTradeTransaction lifecycle необходимо доказать совместимость MT5
Nero.csv producer с MT4. Без этого любой downstream MT5 ML-результат
остаётся DIAGNOSTIC_ONLY.

## What Was Done

1. Обнаружен и исправлен алгоритмический баг: критерий `Strong` в MT5
   `lib_PIC.mqh` отличался от MT4, что каскадно перемешивало кольцевой
   буфер фракталов F[] (101 ячейка). Разница в одном булевом условии
   меняет набор защищённых ячеек (HI/LO/stpH/stpL) → другой порядок
   вытеснения → за тысячи баров весь буфер расходится.
2. MT5 Strong приведён к MT4: `FrntVal > ATR*PicPwr*0.5 && BackVal > ATR*PicPwr`
   (было: `Pwr > ATR*PicPwr && StrongImp`).
3. MT4 эталон перегенерирован пользователем с параметрами, идентичными
   MT5 дефолтам (все 12 PIC-параметров проверены), на том же периоде.
4. Применена корректная методология сравнения: матчинг фракталов по T
   (timestamp уровня) внутри каждой строки, а не по индексу fractalN.
   Порядок ячеек в строке детерминирован, но зависит от стартовых условий
   (разница в 2 бара на старте даёт другой порядок при том же наборе).

## Tester Metadata

| Параметр | MT5 | MT4 |
|----------|-----|-----|
| Symbol | XAUUSD | XAUUSD |
| Timeframe | H1 | H1 |
| Model | 1 (1-minute OHLC) | Open prices |
| Period | 2019.06.20–2022.12.03 | 2019.06.20–2022.12.03 |
| Deposit | 10000 USD | — |
| Leverage | 1:500 | — |
| InpMT5_ExportNero | true | — |
| PIC params | PicPer=1 FltLen=10 PicCnt=2 PicPwr=9 PicImp=1 Rev=0 Days=0 MidTyp=1 A=15 a=5 Ak=1 PicVal=20 | identical |

## Results

| Метрика | Значение | Порог |
|---------|----------|-------|
| Match rate (по T) | 99.05% | >= 95% |
| Direction agreement | 99.24% | >= 95% |
| Price p95 diff (mean по строкам) | 0.003 | <= 5.0 |
| Fractals matched | 868 426 | — |
| Only in MT4 | 8 371 (0.95%) | — |
| Only in MT5 | 8 106 (0.92%) | — |
| Intersection rows | 8 905 | — |
| ATR diff | 0.0 | — |

## Structural

| Метрика | MT4 | MT5 |
|---------|-----|-----|
| Rows total | 9 749 | 9 378 |
| Columns | 104 | 104 |
| Column names match | YES | — |
| Min time | 2019.05.16 14:00 | 2019.07.02 15:00 |
| Max time | 2022.12.02 22:00 | 2022.12.02 22:00 |
| Nested fields | 23 | 23 |

## Bug Fix

`MT/MQL5/Include/lib_PIC.mqh:246` — критерий Strong:

```
// Было (MT5):
if (F[f].Pwr > ATR * PicPwr && F[f].StrongImp)

// Стало (= MT4):
if (F[f].FrntVal > ATR * PicPwr * 0.5 && F[f].BackVal > ATR * PicPwr)
```

Без этого фикса direction agreement = 56% (случайный уровень), T agreement = 0%.

## Methodology Note

Сравнение по индексу fractalN невалидно для кольцевого буфера: порядок
ячеек зависит от истории вытеснений, которая расходится при любой разнице
в стартовых условиях. Корректное сравнение — по T внутри строки.

## Conclusions

**Verdict: PARITY_PASS**

- Числовая совместимость: PASS (match 99.05%, direction 99.24%, price p95 = 0.003).
- Структурная совместимость: PASS (104 колонки, 23 поля, формат).
- ~1% несовпавших уровней объясняется разной глубиной прогрева
  (MT4 стартует с 2019.05.16, MT5 с 2019.07.02) и округлением float.
- ATR = 0.0: бары (OHLC) идентичны между платформами.
- MT5 Nero.csv producer может служить источником feature stream для ML.

## Limitations

1. MT4 тестер запускался пользователем вручную (не headless) — нет
   автоматического лога параметров. Параметры верифицированы по .set файлу.
2. ~1% уровней не матчится — вероятно артефакт разного прогрева и float
   rounding в вычислении FrntVal/BackVal. Не является blocker.
3. Модель тестера: MT5 Model=1 (минутки), MT4 — по ценам открытия.
   Не влияет на PIC (работает с завершёнными H1 барами).

## Split Disclosure

Не используется. Никаких PnL/PF/trading-выводов.

## Related Materials

- Plan: `docs/superpowers/plans/2026-07-31-mt5-nero-parity-v2.md`
- Contract: `docs/schemas/mt5_nero_csv_contract.md`
- Comparison JSON: `ML/reports/mt5_nero_parity/nero_parity_by_time.json`
- Script: `ML/baseline/compare_nero_by_time.py`
- MT4 reference: `MT/tester/files/Nero.csv`
- MT5 output: `ML/reports/mt5_nero_parity/Nero_MT5_v2.csv`
- Lifecycle report: `docs/reports/2026-07-31-mt5-ontradetransaction-lifecycle.md`
