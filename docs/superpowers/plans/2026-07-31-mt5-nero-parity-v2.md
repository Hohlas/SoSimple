# MT5 Nero.csv Parity v2

**Goal:** Доказать числовую совместимость MT5 Nero.csv producer с MT4
на идентичных параметрах и периоде. Сравнение по T внутри строки
(не по индексу fractalN).

**Status:** COMPLETED

## Контекст

Предыдущий прогон (v1, 2026-07-31) дал PARITY_PARTIAL по двум причинам:
1. Разный критерий `Strong` в MT4/MT5 `lib_PIC.mqh` — каскадно перемешивал
   кольцевой буфер F[] → fractal0 указывал на разные уровни.
2. Сравнение по индексу fractalN невалидно: порядок ячеек детерминирован,
   но зависит от стартовых условий. Даже разница в 2 бара на старте даёт
   другой порядок при том же наборе уровней.

## Что сделано

- [x] Обнаружен и исправлен баг: MT5 `Strong` критерий приведён к MT4
      (`MT/MQL5/Include/lib_PIC.mqh:246`).
      Было: `Pwr > ATR*PicPwr && StrongImp`
      Стало: `FrntVal > ATR*PicPwr*0.5 && BackVal > ATR*PicPwr`
- [x] MT5 скомпилирован: 0 errors, 0 warnings.
- [x] Создан MT4 .set (`MT/tester/files/nero_parity_mt4.set`) с параметрами,
      идентичными MT5 дефолтам (все 12 PIC-параметров проверены).
- [x] Пользователь сгенерировал MT4 `MT/tester/files/Nero.csv` (FromDate=2019.06.20).
- [x] Написан скрипт `ML/baseline/compare_nero_by_time.py` — сравнение по T.
- [x] MT5 тестер: перегенерация Nero_MT5.csv с фиксом Strong.
- [x] Запуск сравнения по T.
- [x] Verdict: PARITY_PASS. Отчёт + handoff + changelog обновлены.

## Методология сравнения

Для каждой строки с одинаковым `time`:
1. Извлечь все непустые fractal0..fractal99 из MT4 и MT5.
2. Сматчить по полю T (timestamp формирования уровня).
3. Для сматченных пар сравнить: P, Dir, FrntVal, BackVal, Strong, Brk,
   Rev, PwrSum, Cnt, Imp, Up/Dn, ATR.
4. Зафиксировать: match rate, direction agreement, price diff,
   количество уровней только в одном файле.

Вердикты:
- PASS: match rate >= 95%, direction agreement >= 95%, price p95 <= 5.0
- PARTIAL: match rate >= 50%, расхождения объяснимы
- FAIL: match rate < 50% или необъяснимые расхождения

## Параметры (идентичны MT4/MT5)

PicPer=1, FltLen=10, PicCnt=2, PicPwr=9, PicImp=1, Rev=0, Days=0,
MidTyp=1, A=15, a=5, Ak=1, PicVal=20

## Период

FromDate=2019.06.20, ToDate=2022.12.03, XAUUSD, H1, Model=1 (1-min OHLC)

## Известные ограничения

- MT4 файл начинается с 2019.05.16 (272 строки до FromDate) — MT4 тестер
  даёт предобработку. MT5 начинает с ~2019.07.02 (прогрев буфера).
  Пересечение по time корректно обрабатывает это.
- Порядок ячеек в строке НЕ сравнивается — только множество уровней.
- USE_NORMALIZED_OUTPUT=false в обоих кодах.

## Файлы

- MT4 эталон: `MT/tester/files/Nero.csv`
- MT5 результат: `ML/reports/mt5_nero_parity/Nero_MT5_v2.csv`
- Скрипт: `ML/baseline/compare_nero_by_time.py`
- JSON: `ML/reports/mt5_nero_parity/nero_parity_by_time.json`
- Отчёт: `docs/reports/2026-07-31-mt5-nero-parity.md` (будет перезаписан)
