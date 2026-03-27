# Path-Ordering Analysis
**Дата:** 2026-03-27  
**Данные:** all_trades.csv (v3 log, 367 сделок)  
**OHLC:** XAUUSD_H1_OHLC.csv (126637 баров)

## Метод
Для каждой сделки из TP_CLEAR/BOTH_HIT/SL_CLEAR: bar-by-bar scan H1 OHLC[bar+1..bar+12].
Если High≥TP и Low≤SL в одном баре — порядок по Open: ближе к SL=SL_FIRST, иначе TP_FIRST.

## Результаты

### BOTH_HIT (24 сделок)
- Path order:  SL_FIRST=22 (92%)  TP_FIRST=2 (8%)  TIMEOUT=0
- MT4 results: {'LOSS(SL)': 14, 'LOSS(MKT)': 8, 'WIN(TP)': 2}
- Cross-table (path_order × mt4_result):
  - SL_FIRST: {'LOSS(SL)': 14, 'LOSS(MKT)': 8}
  - TP_FIRST: {'WIN(TP)': 2}

### TP_CLEAR (237 сделок)
- Path order:  SL_FIRST=33 (24%)  TP_FIRST=104 (76%)  TIMEOUT=100
- MT4 results: {'LOSS(MKT)': 50, 'LOSS(SL)': 36, 'WIN(TP)': 91, 'WIN(MKT)': 60}
- Cross-table (path_order × mt4_result):
  - SL_FIRST: {'LOSS(MKT)': 14, 'LOSS(SL)': 18, 'WIN(MKT)': 1}
  - TP_FIRST: {'WIN(TP)': 91, 'LOSS(MKT)': 5, 'WIN(MKT)': 5, 'LOSS(SL)': 3}
  - TIMEOUT: {'LOSS(MKT)': 31, 'WIN(MKT)': 54, 'LOSS(SL)': 15}

### SL_CLEAR (30 сделок)
- Path order:  SL_FIRST=28 (100%)  TP_FIRST=0 (0%)  TIMEOUT=2
- MT4 results: {'LOSS(MKT)': 7, 'LOSS(SL)': 23}
- Cross-table (path_order × mt4_result):
  - SL_FIRST: {'LOSS(MKT)': 5, 'LOSS(SL)': 23}
  - TIMEOUT: {'LOSS(MKT)': 2}

## Общий итог

- SL_FIRST: 83 (44%)
- TP_FIRST: 106 (56%)

## Ключевой диагноз

TP_CLEAR + SL_FIRST = **33** сделок — модель права (TP достижим), но путь идёт через SL.
Это основная цель для first-barrier-hit лейблинга.

## Консистентность path_order vs MT4

Совпадение: 180/291 = 62%
(Несовпадение = сделка закрыта по MARKET-таймауту до достижения SL/TP)
