//+------------------------------------------------------------------+
//!                           lib_PIC.mqh
//!
//! @file     lib_PIC.mqh
//! @brief    Библиотека анализа ценовых уровней (Price Item Calculator)
//! @author   [Автор не указан]
//! @version  230.525+
//! @date     Создан: Неизвестно
//! @date     Обновлён: 2026-02-06
//!
//! @details
//! Основное назначение:
//!   Анализ и классификация ценовых уровней (фракталов) на исторических
//!   данных с последующим экспортом для обучения нейросетей.
//!
//! Функциональность:
//!   - Обнаружение ценовых экстремумов (вершин и впадин)
//!   - Расчёт характеристик уровней (фронты, импульсы, сила)
//!   - Определение статусов уровней (CLEAR, TOUCH, MIRROR, BROKEN)
//!   - Детекция ложных пробоев и флэтов
//!   - Определение локального/глобального тренда
//!   - Экспорт данных в CSV для нейросетевого обучения (Nero)
//!
//! Архитектура:
//!   - Расширяет класс EXPERT, добавляя методы работы с уровнями
//!   - Использует массив F[] структуры уровней (LevelsAmount элементов)
//!   - Интегрируется с ATR-индикаторами для адаптивных порогов
//!
//! @note Кодировка исходного файла: UTF-16LE
//! @warning Требуется компиляция вместе с expert-классом, содержащим F[]
//!
//! Зависимости:
//! @par Входные данные:
//!   - Массивы High[], Low[], Close[], Time[] (MT4 built-in)
//!   - Структура Atr с полями Fast, Slow, Lim, Max (из lib_ATR.mqh)
//!   - Массив уровней F[] типа FRACTAL (LevelsAmount элементов)
//!
//! @par Выходные данные:
//!   - CSV файл "Nero_{SYMBOL}{PERIOD}.csv" в директории MQL4/Files/
//!   - Формат: time;signal;predict;ATR;fractal0;fractal1;...
//!
//! @par Внешние зависимости:
//!   - lib_ATR.mqh  - расчёт ATR-индикаторов
//!   - lib_Flat.mqh - определение флэтов и ложных пробоев
//!   - (опционально) lib_TRG.mqh - треугольные формации (отключено)
//!
//! @par Конфигурация:
//!   - NORMALIZATION_PERCENTILE (double) = 0.95 - перцентиль для piecewise
//!   нормализации
//!   - USE_NORMALIZED_OUTPUT (bool) = true - вывод нормализованных/сырых данных
//!   - PicPer - период обнаружения пиков (внешняя переменная)
//!   - PicPwr, PicCnt, PicImp - пороги силы/количества/импульса
//!   - Days - глубина анализа в днях (>0 ближние, <0 дальние уровни)
//!
//! Использование:
//! @code
//!   #include <lib_PIC.mqh>
//!   // В OnTick() или OnCalculate():
//!   if (exp.PIC()) {
//!       // Доступны: exp.HI, exp.LO, exp.HI2, exp.LO2 - индексы ключевых
//!       уровней
//!       // exp.Trnd.Local, exp.Trnd.Global - направление тренда
//!   }
//! @endcode
//!
//! @see EXPERT::INIT() для инициализации
//! @see EXPERT::PIC() для основного цикла
//! @see EXPERT::NERO_CSV_CREATE() для экспорта данных
//+------------------------------------------------------------------+

// #include <lib_TRG.mqh>
#include <lib_ATR.mqh>
#include <lib_Flat.mqh>

#ifdef PIC_INDICATOR // код компилируется только в индикаторе
void EXPERT::CONSTANT_COUNTER() {
  Print("ok");
} // ф-я эксперта отсутствует в индикаторе
#endif

//====================================================================
// НАСТРОЙКИ НОРМАЛИЗАЦИИ
//====================================================================
double NORMALIZATION_PERCENTILE =
    0.95f; // Перцентиль для piecewise нормализации (0.85, 0.90, 0.95, ...)
bool USE_NORMALIZED_OUTPUT =
    false; // true - нормализованные значения, false - сырые значения
//====================================================================

/// @brief Инициализация модуля PIC
/// @details Выполняет проверки ATR-параметров и настройку констант.
///          Создаёт начальный CSV-файл для Nero.
/// @return INIT_SUCCEEDED при успехе, INIT_FAILED при ошибках конфигурации
/// @note Вызывается один раз при запуске эксперта
int EXPERT::INIT() {
  // ATR INIT
  if (a <= 0) {
    Print("ATR_INIT(): a<=0");
    return (INIT_FAILED);
  }
  if (A <= 0) {
    Print("ATR_INIT(): A<=0");
    return (INIT_FAILED);
  }
  if (a > A) {
    Print("ATR_INIT(): a>A");
    return (INIT_FAILED);
  }
  SlowAtrPer = A * A;
  FastAtrPer = a * a;
  Print(__FILE__, "/", __FUNCTION__, " ExpNum=", ExpNum, "  Ver", Ver);
  Print(__FILE__, "/", __FUNCTION__, " ATR_INIT(): FastAtrPer=", FastAtrPer,
        " SlowAtrPer=", SlowAtrPer);
  // PIC INIT
  SET_CHART_SETTINGS(CHART_WHITE);
  BarSeconds = datetime(Period() * 60); // кол-во секунд в баре
  PicPerSeconds =
      datetime(BarSeconds * PicPer *
               1.5); // период расчета пика с запасом для временных лагов
  BarsInDay = ushort(24 * 60 / Period()); // Кол-во бар в сутках
  PerAdapter = float(60.00 / Period());   // Print("PerAdapter=",PerAdapter);
  Print(__FILE__, "/", __FUNCTION__, " PIC INIT:  Bars=", Bars, " bar=", bar,
        " Time[bar]=", DTIME(Time[bar]),
        " Time[Bars-1]=", DTIME(Time[Bars - 1]),
        "  compilation time: ", __DATETIME__);
  CONSTANT_COUNTER();
  NERO_CSV_CREATE();
  return (INIT_SUCCEEDED);
}

/// @brief Основной цикл поиска и анализа уровней
/// @details Вызывается на каждом баре. Выполняет:
///   1. Обновление ATR-значений
///   2. Обнаружение новых фрактальных экстремумов
///   3. Поиск близлежащих уровней
///   4. Определение локального тренда
/// @return true если ATR готов, false если ожидается накопление данных
/// @note Результаты доступны через поля HI, LO, HI2, LO2, Trnd
bool EXPERT::PIC() { // ОСНОВНОЙ ЦИКЛ ПОИСКА УРОВНЕЙ
  if (!ATR_COUNT()) {
    return (false);
  } // Print(DTIME(Time[bar]),": ATR don't ready");
  H2 = H1;
  H1 = H;
  L2 = L1;
  L1 = L;
  C2 = C1;
  C1 = C;
  H = (float)High[bar];
  L = (float)Low[bar];
  C = (float)Close[bar]; // O0=(float)Open[bar-1]; // Open[0]=Bid
  if (Days && NEW_DAY(bar))
    TimeFrom = DAYS_TIME(ABS(Days)); // временной предел расчета уровней в днях
  if ((float)High[bar + PicPer] == HIGHEST(PicPer * 2 + 1, bar)) { // Новый hi
    NEW_LEVEL(1, (float)High[bar + PicPer]); // ФОРМИРОВАНИЕ И УДАЛЕНИЕ УРОВНЕЙ
  }
  if ((float)Low[bar + PicPer] == LOWEST(PicPer * 2 + 1, bar)) { // Новый lo
    NEW_LEVEL(-1, (float)Low[bar + PicPer]); // ФОРМИРОВАНИЕ И УДАЛЕНИЕ УРОВНЕЙ
  }
  LEVELS_FIND_AROUND(); // ПОИСК СИЛЬНЫХ УРОВНЕЙ
  LOCAL_TREND();
  return (true);
}

#define TEST_DATE "2020.11.10 10:00" // "2022.09.07 18:00"

/// @brief Формирование нового уровня и удаление устаревших
/// @param NewPicDir направление пика: +1 = вершина, -1 = впадина
/// @param NewFractal цена нового фрактала
/// @details Алгоритм:
///   1. Поиск совпадающих уровней в пределах Atr.Lim
///   2. Расчёт переднего/заднего фронтов
///   3. Определение сильных уровней (Strong) по критериям Pwr, Cnt, Imp
///   4. Удаление самого слабого уровня при переполнении массива
///   5. Вызов детектора флэтов и экспорт в CSV
/// @note Критерий удаления: Weight = Pwr * FltNum / Distance / (Brk+1)
void EXPERT::NEW_LEVEL(char NewPicDir,
                       float NewFractal) { // ФОРМИРОВАНИЕ И УДАЛЕНИЕ УРОВНЕЙ
  Dir = NewPicDir;                         // направление последнего пика
  New = NewFractal;
  datetime ExPicTime =
      Time[Bars - 1];  // время ближайшшего превосходящего пика из массива...
  char FltNum = 1;     // кол-во совпадений c флэтовыми непробитыми пиками
  char Cnt = 1;        // кол-во совпадений со всеми пиками
  uchar FlatBegin = 0; // время начала флэта
  float FltLev = New;  // средний уровень совпавших пиков
  float PwrSum = 0;    // Сумма сил пиков, совпадающих с этим по уровню
  uchar LowestWeightCell = 0; // номер ячейки и
  float LowestWeight = 99999; // сила самого слабого уровня для удаления на
                              // случай, если не найдется свободной ячейки
  float Weight = 0; // критерий удаления
  float base1, base2;
  uchar e; // ExPicTime array index
  uchar Oldest = n;
  color PicColor;
  for (uchar f = 1; f < LevelsAmount;
       f++) { // перебираем весь массив фракталов от большего к меньшему
    if (F[f].P == 0) { // незаполненная ячейка
      LowestWeight = 0;
      LowestWeightCell = f;
      continue;
    }
    char dir = F[f].Dir;
    if (F[f].T < F[Oldest].T)
      Oldest = f;
    // Критерий удаления = минимальный фронт * кол-во отскоков / дистанция /
    // число пробоев
    Weight = F[f].Pwr * F[f].Flt.Num / (SHIFT(F[f].T) - bar) / (F[f].Brk + 1);
    if (Weight < LowestWeight && F[f].Fls.Phase < START && f != HI && f != LO &&
        f != stpH && f != stpL) {
      LowestWeight = Weight;
      LowestWeightCell = f;
    }
    if (MathAbs(New - F[f].P) < Atr.Lim) { // совпадение уровней
      PwrSum += F[f].Pwr; // Сумма сил пиков, совпадающих с этим по уровню
      F[f].Cnt++; // кол-во совпадений со всеми пиками (пробитыми и зеркальными)
      Cnt++;      // для поиска уровня с максимальным количеством отскоков
    }
    if (F[f].Brk == BROKEN && New * dir > (F[f].P + Atr.Max * 2) * dir)
      F[f].Brk = MIRROR; // подтверждение зеркального уровня
    FALSE_BREAK(f);      // проверка ложного пробоя при iSignal=1 (lib_Flat.mqh)
    if (Ver < 230.525 && F[f].Brk > CLEAR)
      continue;
    if (F[f].Brk > TOUCH)
      continue;
    if (Dir == dir) { // сонаправленный пик
      if (MathAbs(New - F[f].P) < Atr.Lim) {
        F[f].Flt.Num++;
        FltNum++;
        FltLev += F[f].P;
        if (FlatBegin == 0 || F[f].T < F[FlatBegin].T)
          FlatBegin = f;
      } else if (LEV_BREAK(f, New))
        continue;
      if (F[f].T > ExPicTime) {
        ExPicTime = F[f].T;
        e = f;
      }
      if (New * dir > F[f].Near * dir) {
        F[f].Near = New;
        F[f].NearVal = (New - F[f].Back) * dir;
      }
    } else { // противолежащий пик
      if (New * dir < F[f].Back * dir) {
        F[f].Back = New;
        F[f].BackVal = (F[f].P - New) * dir;
        F[f].BackT = Time[bar + PicPer];
        F[f].Pwr = MathMin(F[f].FrntVal, F[f].BackVal);
        F[f].Near = New;
        F[f].NearVal = 0;
        if (F[f].BackVal < ATR * PicPwr)
          continue;
        if (F[f].FrntVal > ATR * PicPwr && F[f].StrongImp) {
          F[f].Strong = 1;
        }
      }
    }
  }
  n = LowestWeightCell;
  F[n].P = New;
  F[n].T = Time[bar + PicPer];
  F[n].Flt.T = Time[bar + PicPer];
  F[n].Flt.Num = FltNum;
  F[n].Cnt = Cnt;
  F[n].BarTch = 0;
  F[n].Dir = Dir;
  F[n].ExT = ExPicTime;
  F[n].Per = PicPer;
  F[n].Brk = CLEAR;
  F[n].Rev = 0;
  F[n].Strong = false;
  F[n].StrongImp = false;
  F[n].TrBrk = NEW;
  F[n].Fls.Phase = NONE;
  F[n].TRG.N = 0;
  F[n].PwrSum = PwrSum;
  F[n].Atr = Atr.Fast;
  if (Dir > 0) { // вершина
    F[n].Tr = New - Atr.Fast;
    F[n].TrMid = (F[n].P + F[n].Tr) / 2;
    F[n].Frnt = LOWEST(SHIFT(ExPicTime) - (bar + PicPer), bar + PicPer + 1);
    F[n].Back = LOWEST(PicPer, bar);
    F[n].FrntVal = New - F[n].Frnt;
    F[n].BackVal = New - F[n].Back;
    F[n].NearVal = 0;
    if (New > F[hi].P) {
      F[n].Rev = F[hi].Pwr;
      RevHi = n;
    }
    hi3 = hi2;
    hi2 = hi;
    hi = n;
    float ImpHi =
        F[hi].Imp / (F[lo].Imp + F[lo2].Imp + F[lo3].Imp + float(Point)) * 3;
    base1 = LOWEST(PicPer, bar);
    base2 = LOWEST(PicPer, bar + PicPer + 1);
    F[n].Imp = New * 2 - base1 - base2;
    PicColor = DNCLR;
  } else { // впадина
    F[n].Tr = New + Atr.Fast;
    F[n].TrMid = (F[n].P + F[n].Tr) / 2;
    F[n].Frnt = HIGHEST(SHIFT(ExPicTime) - (bar + PicPer), bar + PicPer + 1);
    F[n].Back = HIGHEST(PicPer, bar);
    F[n].FrntVal = F[n].Frnt - New;
    F[n].BackVal = F[n].Back - New;
    F[n].NearVal = 0;
    if (New < F[lo].P) {
      F[n].Rev = F[lo].Pwr;
      RevLo = n;
    }
    lo3 = lo2;
    lo2 = lo;
    lo = n;
    float ImpLo =
        F[lo].Imp / (F[hi].Imp + F[hi2].Imp + F[hi3].Imp + float(Point)) * 3;
    base1 = HIGHEST(PicPer, bar);
    base2 = HIGHEST(PicPer, bar + PicPer + 1);
    F[n].Imp = base1 + base2 - New * 2;
    PicColor = UPCLR;
  }
  if (F[n].Imp / F[n].Atr > PicImp) {
    F[n].StrongImp = true;
  }
  F[n].BackT = Time[bar + PicPer];
  F[n].Pwr = MathMin(F[n].FrntVal, F[n].BackVal);
  FLAT_DETECT(FltLev / FltNum, FlatBegin);
  NERO_CSV_CREATE(bar);
}

/// @brief Поиск ближайшей вершины выше базового уровня
/// @param BaseLev базовый уровень для сравнения
/// @param Delta текущая минимальная дистанция (in/out)
/// @param f индекс проверяемого уровня
/// @param Nearest индекс найденного ближайшего уровня (out)
void EXPERT::LOWEST_HI(float BaseLev, float &Delta, uchar f, uchar &Nearest) {
  if (F[f].P + Atr.Lim > BaseLev && F[f].P - BaseLev < Delta) {
    Delta = F[f].P - BaseLev;
    Nearest = f;
  }
}

/// @brief Поиск ближайшей впадины ниже базового уровня
/// @param BaseLev базовый уровень для сравнения
/// @param Delta текущая минимальная дистанция (in/out)
/// @param f индекс проверяемого уровня
/// @param Nearest индекс найденного ближайшего уровня (out)
void EXPERT::HIGHEST_LO(float BaseLev, float &Delta, uchar f, uchar &Nearest) {
  if (F[f].P - Atr.Lim < BaseLev && BaseLev - F[f].P < Delta) {
    Delta = BaseLev - F[f].P;
    Nearest = f;
  }
}

/// @brief Поиск минимальной впадины
/// @param lowest текущий минимум (in/out)
/// @param f индекс проверяемого уровня
/// @param f_lowest индекс минимального уровня (out)
void EXPERT::LOWEST_LO(float &lowest, uchar f, uchar &f_lowest) {
  if (F[f].P < lowest) {
    lowest = F[f].P;
    f_lowest = f;
  }
}

/// @brief Поиск максимальной вершины
/// @param highest текущий максимум (in/out)
/// @param f индекс проверяемого уровня
/// @param f_highest индекс максимального уровня (out)
void EXPERT::HIGHEST_HI(float &highest, uchar f, uchar &f_highest) {
  if (F[f].P > highest) {
    highest = F[f].P;
    f_highest = f;
  }
}

/// @brief Поиск близлежащих уровней и "первых" уровней
/// @details Обновляет:
///   - HI, LO - индексы ближайших/дальних сильных уровней
///   - HI2, LO2 - уровни серединки между основным и Back
///   - TrgHi, TrgLo - целевые уровни (если Target != 0)
///   - stpH, stpL - уровни стопов/трейлинга
/// @note Логика зависит от параметра Days:
///   - Days > 0: работа от ближних уровней
///   - Days < 0: работа от дальних уровней
///   - Days = 0: на всей истории
void EXPERT::LEVELS_FIND_AROUND() { // ПОИСК БЛИЗЛЕЖАЩИХ УРОВНЕЙ
  float minTrgHi = 99999, minTrgLo = 99999, minHI = 999999, minLO = 999999,
        minH = 999999, minL = 999999, StpVal = ATR * MathAbs(Trl),
        PwrImpCntHi = 0, PwrImpCntLo = 0, Highest = 0, Lowest = 999999;
  TrgHi = 0;
  TrgLo = 0;
  stpH = 0;
  stpL = 0;
  HI = 0;
  LO = 0;
  for (uchar f = 1; f < LevelsAmount; f++) {
    if (F[f].P == 0)
      continue;
    if (LEV_CHECK(f) > TOUCH)
      continue;
    F[f].Per++;
    if (F[f].TrBrk == NEW) {
      if (F[f].Dir > 0 && H < F[f].TrMid) {
        F[f].TrBrk = CLEAR;
      }
      if (F[f].Dir < 0 && L > F[f].TrMid) {
        F[f].TrBrk = CLEAR;
      }
    }
    if (F[f].TrBrk == CLEAR) {
      if (F[f].Dir > 0 && H > F[f].TrMid)
        F[f].TrBrk = BROKEN;
      if (F[f].Dir < 0 && L < F[f].TrMid)
        F[f].TrBrk = BROKEN;
    }
    if (Target != 0) {
      if (F[f].Dir > 0)
        LOWEST_HI(TargetHi, minTrgHi, f, TrgHi);
      else
        HIGHEST_LO(TargetLo, minTrgLo, f, TrgLo);
    }
    if (Rev == 1 && F[f].Rev == 0)
      continue;
    if (Rev == 2 && F[f].FrntVal > F[f].BackVal + Atr.Lim)
      continue;
    // TRAILING/STOP LEVELS
    if (F[f].BackVal > StpVal) {
      if (F[f].Dir > 0) {
        if (F[f].T > SEL.T)
          LOWEST_HI(H, minH, f, stpH);
      } else {
        if (F[f].T > BUY.T)
          HIGHEST_LO(L, minL, f, stpL);
      }
    }
    // ПЕРВЫЕ УРОВНИ
    if (F[f].Strong != true)
      continue;
    if (F[f].T < TimeFrom)
      continue;
    if (Days < 0) {
      if (F[f].Dir > 0)
        HIGHEST_HI(Highest, f, HI);
      else
        LOWEST_LO(Lowest, f, LO);
    } else {
      if (F[f].Dir > 0)
        LOWEST_HI(H, minHI, f, HI);
      else
        HIGHEST_LO(L, minLO, f, LO);
    }
  }
  // УРОВНИ СЕРЕДИНКИ
  if (HI != lastHI) {
    lastHI = HI;
    HI2 = 0;
  }
  if (LO != lastLO) {
    lastLO = LO;
    LO2 = 0;
  }
  if (HI > 0 && Hi_checksum != F[HI].P + F[HI].Back &&
      H > F[HI].Back + F[HI].BackVal / 4) {
    Hi_checksum = F[HI].P + F[HI].Back;
    HI2 = MID_LEV(HI);
    LINE("HI=" + S0(HI) + " P=" + S4(F[HI].P) +
             " Frnt/Back=" + S4(F[HI].FrntVal) + "/" + S4(F[HI].BackVal) +
             " Atr.F/S=" + S5(Atr.Fast) + "/" + S5(Atr.Slow),
         F[HI].T, F[HI].P, F[HI].BackT, F[HI].Back, DNCLR, 0);
  }
  if (LO > 0 && Lo_checksum != F[LO].P + F[LO].Back &&
      L < F[LO].Back - F[LO].BackVal / 4) {
    Lo_checksum = F[LO].P + F[LO].Back;
    LO2 = MID_LEV(LO);
    LINE("LO=" + S0(LO) + " P=" + S4(F[LO].P) +
             " Frnt/Back=" + S4(F[LO].FrntVal) + "/" + S4(F[LO].BackVal) +
             " Atr.F/S=" + S5(Atr.Fast) + "/" + S5(Atr.Slow),
         F[LO].T, F[LO].P, F[LO].BackT, F[LO].Back, UPCLR, 0);
  }
  if (HI)
    LINE("HI=" + S0(HI) + " HI2=" + S0(HI2) + " Pwr=" + S4(F[HI].Pwr) +
             " Imp=" + S4(F[HI].Imp / F[HI].Atr) + " Cnt=" + S0(F[HI].Cnt),
         bar, F[HI].P, bar + 1, F[HI].P, DNCLR, 2);
  if (LO)
    LINE("LO=" + S0(LO) + " LO2=" + S0(LO2) + " Pwr=" + S4(F[LO].Pwr) +
             " Imp=" + S4(F[LO].Imp / F[LO].Atr) + " Cnt=" + S0(F[LO].Cnt),
         bar, F[LO].P, bar + 1, F[LO].P, UPCLR, 2);
  if (HI2)
    LINE("HI2=" + S0(HI2) + " HI=" + S0(HI) + " Back=" + S4(F[HI].Back) + "/" +
             DTIME(F[HI].BackT) + " HI2=" + S4(HI2),
         bar, F[HI2].P, bar + 1, F[HI2].P, DNCLR, 0);
  if (LO2)
    LINE("LO2=" + S0(LO2) + " LO=" + S0(LO) + " Back=" + S4(F[LO].Back) + "/" +
             DTIME(F[LO].BackT) + " LO2=" + S4(LO2),
         bar, F[LO2].P, bar + 1, F[LO2].P, UPCLR, 0);
  LINE("HI=" + S0(HI) + " LO=" + S0(LO) + " Back[28]=" + S4(F[28].BackVal) +
           " PicPwr=" + S4(ATR * PicPwr) + " frst=" + S0(F[28].Strong),
       bar + 1, Close[bar + 1], bar, Close[bar], clrSilver, 0);
}

//  CLEAR    0 // новый непробитый
//  TOUCH    1 // с касанием флэтовый
//  MIRROR   2 // зеркальный
//  BROKEN   3 // пробитый
//  USED     5 // отработанный

/// @brief Проверка касания уровня
/// @param f индекс уровня в массиве
/// @return true если текущий бар касается уровня в пределах Atr.Lim
/// @note Устанавливает F[f].Brk=TOUCH при касании
bool EXPERT::LEV_TOUCH(uchar f) {
  if (F[f].TrBrk < CLEAR)
    return (false);
  if (F[f].Dir > 0 && H > F[f].P - Atr.Lim && H < F[f].P + Atr.Lim) {
    F[f].Brk = TOUCH;
    return (true);
  }
  if (F[f].Dir < 0 && L < F[f].P + Atr.Lim && L > F[f].P - Atr.Lim) {
    F[f].Brk = TOUCH;
    return (true);
  }
  return (false);
}

/// @brief Проверка пробоя уровня баром
/// @param f индекс уровня в массиве
/// @return true если текущий бар пробивает уровень
/// @note Вызывает SET_BROKEN() при пробое
bool EXPERT::LEV_BREAK(uchar f) {
  if (F[f].Dir > 0 && H >= F[f].P + Atr.Lim) {
    SET_BROKEN(f);
    return (true);
  }
  if (F[f].Dir < 0 && L <= F[f].P - Atr.Lim) {
    SET_BROKEN(f);
    return (true);
  }
  return (false);
}

/// @brief Проверка пробоя уровня новым фракталом
/// @param f индекс уровня в массиве
/// @param pic цена нового фрактала
/// @return true если фрактал пробивает уровень
bool EXPERT::LEV_BREAK(uchar f, float pic) {
  if (F[f].Dir > 0 && pic >= F[f].P + Atr.Lim) {
    SET_BROKEN(f);
    return (true);
  }
  if (F[f].Dir < 0 && pic <= F[f].P - Atr.Lim) {
    SET_BROKEN(f);
    return (true);
  }
  return (false);
}

/// @brief Проверка пересечения уровня (для пробитых/зеркальных)
/// @param f индекс уровня в массиве
/// @return true если цена пересекает уровень
/// @note Увеличивает счётчик пробоев F[f].Brk (макс. 10)
bool EXPERT::LEV_CROSS(uchar f) {
  if (H > F[f].P && L < F[f].P) {
    if (F[f].Brk < BROKEN)
      F[f].Brk = BROKEN;
    F[f].Brk++;
    if (F[f].Brk > 10)
      F[f].Brk = 10;
    return (true);
  }
  return (false);
}

/// @brief Комплексная проверка статуса уровня
/// @param f индекс уровня в массиве
/// @return текущий статус уровня (CLEAR, TOUCH, MIRROR, BROKEN+)
/// @details Проверяет касания/пробои в зависимости от текущего статуса
char EXPERT::LEV_CHECK(uchar f) {
  if (F[f].Brk == CLEAR && (LEV_TOUCH(f) || LEV_BREAK(f)))
    return (F[f].Brk);
  if (F[f].Brk == TOUCH && LEV_BREAK(f))
    return (F[f].Brk);
  if (F[f].Brk == MIRROR && LEV_CROSS(f))
    return (F[f].Brk);
  if (F[f].Brk >= BROKEN && LEV_CROSS(f))
    return (F[f].Brk);
  return (F[f].Brk);
}

/// @brief Установка статуса пробитого уровня
/// @param f индекс уровня в массиве
/// @details Обновляет глобальный/локальный тренд при пробое HI/LO/HI2/LO2.
///          Запускает отслеживание ложного пробоя для сильных уровней.
void EXPERT::SET_BROKEN(uchar f) {
  F[f].BrkT = Time[bar];
  F[f].Brk = BROKEN;
  if (F[f].Dir > 0) {
    if (f == HI) {
      HI = 0;
      if (iGlb == 1)
        Trnd.Global = 1;
    }
    if (f == HI2) {
      HI2 = 0;
      if (iGlb == 2)
        Trnd.Global = 1;
    }
    Trnd.PicBrk++;
    if (Trnd.PicBrk > iLoc)
      Trnd.PicBrk = iLoc;
  } else {
    if (f == LO) {
      LO = 0;
      if (iGlb == 1)
        Trnd.Global = -1;
    }
    if (f == LO2) {
      LO2 = 0;
      if (iGlb == 2)
        Trnd.Global = -1;
    }
    Trnd.PicBrk--;
    if (Trnd.PicBrk < -iLoc)
      Trnd.PicBrk = -iLoc;
  }
  if (F[f].Pwr > ATR * PicPwr) {
    F[f].Fls.Phase = WAIT;
  }
}

/// @brief Определение локального тренда
/// @details Использует:
///   - Trnd.PicBrk - счётчик пробитых вершин/впадин
///   - Trnd.Flat - выход из флэта
/// @note Записывает результат в Trnd.Local: +1 UP, -1 DOWN, 0 неопределён
void EXPERT::LOCAL_TREND() {
  // Проверка прошлого тренда
  if (Trnd.Flat > 0 && L < F[nFlt].Flt.DnLev - Atr.Lim) {
    Trnd.Flat = 0;
  }
  if (Trnd.Flat < 0 && H > F[nFlt].Flt.UpLev + Atr.Lim) {
    Trnd.Flat = 0;
  }

  if (!hi || !lo)
    return;
  Trnd.Local = 0;
  if (Trnd.PicBrk > 0)
    Trnd.Local = 1;
  if (Trnd.PicBrk < 0)
    Trnd.Local = -1;
  if (iFlt > 0)
    Trnd.Local += Trnd.Flat;
  if (Trnd.Local > 0)
    LINE("Trnd.Local=" + S0(Trnd.Local) + " Dn=" + S4(F[nFlt].Flt.DnLev), bar,
         L, bar, H, UPCLR, 3);
  if (Trnd.Local < 0)
    LINE("Trnd.Local=" + S0(Trnd.Local), bar, L, bar, H, DNCLR, 3);
}

/// @brief Простое определение точки контроля (POC)
/// @details Находит плотное скопление баров без пропусков.
/// @note Обновляет PocCnt (длина), PocCenter (серединка), HiZone, DnZone
void EXPERT::POC_SIMPLE() {
  HiZone = MIN(H, HiZone);
  DnZone = MAX(L, DnZone);
  if (HiZone > DnZone) {
    PocCnt++;
    PocCenter = float((HiZone + DnZone) / 2);
  } else {
    PocCnt = 1;
    HiZone = H;
    DnZone = L;
  }
}

/// @brief Расчёт силы пика по заданному типу
/// @param PowerType тип расчёта:
///   - 1: Pwr (минимальный фронт)
///   - 2: Pwr * Cnt (фронт * отскоки)
///   - 3: Cnt (количество отскоков)
///   - 4: PwrSum (сумма сил совпадающих пиков)
///   - 5: Imp/Atr (нормализованный импульс)
///   - 6: Imp/Atr * Cnt (импульс * отскоки)
/// @param f индекс уровня
/// @return значение силы
float EXPERT::PIC_PWR(uchar PowerType, uchar f) {
  float Power;
  switch (PowerType) {
  case 1:
    Power = F[f].Pwr;
    break;
  case 2:
    Power = F[f].Pwr * F[f].Cnt;
    break;
  case 3:
    Power = F[f].Cnt;
    break;
  case 4:
    Power = F[f].PwrSum;
    break;
  case 5:
    Power = F[f].Imp / F[f].Atr;
    break;
  case 6:
    Power = F[f].Imp / F[f].Atr * F[f].Cnt;
    break;
  default:
    Power = 0;
  }
  return (Power);
}

/// @brief Поиск уровня серединки (короткая форма)
/// @param f индекс базового уровня
/// @return индекс наиболее сильного уровня между P и (P+Back)/2
uchar EXPERT::MID_LEV(uchar f) {
  return (MID_LEV(f, F[f].Tr, (F[f].P + F[f].Back) / 2, F[f].T, F[f].BackT));
}

/// @brief Поиск уровня серединки в заданном диапазоне
/// @param f индекс базового уровня (не используется напрямую)
/// @param UpLev верхняя граница диапазона
/// @param DnLev нижняя граница диапазона
/// @param time0 минимальное время уровня
/// @param time1 максимальное время уровня
/// @return индекс наиболее сильного уровня в диапазоне (по MidTyp)
uchar EXPERT::MID_LEV(uchar f, float UpLev, float DnLev, datetime time0,
                      datetime time1) {
  float Power = 0, MaxPower = 0;
  uchar Pic = 0;
  if (UpLev < DnLev)
    SWAP(UpLev, DnLev);
  for (f = 1; f < LevelsAmount; f++) {
    if (F[f].Brk > TOUCH || F[f].P <= DnLev || F[f].P >= UpLev ||
        F[f].T < time0 || F[f].T > time1)
      continue;
    Power = PIC_PWR(MidTyp, f);
    if (Power > MaxPower) {
      MaxPower = Power;
      Pic = f;
    }
  }
  return (Pic);
}

/// @brief Расчёт целевых уровней на основе измеренных движений
/// @details Анализирует исторические безоткатные движения для прогнозирования
/// целей.
/// @note Параметр Target:
///   - Target > 0: максимальное движение
///   - Target < 0: среднее движение
///   - |Target| = 1: от последнего пика
///   - |Target| = 2: от разворотного пика
/// @warning Результаты записываются в TargetHi, TargetLo
void EXPERT::TARGET_COUNT() {
  if (Target == 0)
    return;
  if (Dir > 0 && Time[bar] - F[hi].T < PicPerSeconds) {
    if (RevLo2 != RevLo) {
      RevLo2 = RevLo;
      ADD_TO_ARRAY(LastMovUp, MovUp);
      if (Target < 0)
        MidMovUp = (MovUp[0] + MovUp[1] + MovUp[2]) / 3;
      LastMovUp = 0;
    }
    if (F[hi].P - F[RevLo].P > LastMovUp) {
      LastMovUp = F[hi].P - F[RevLo].P;
    }
    if (Target > 0)
      MidMovUp = MathMax(MovUp[ArrayMaximum(MovUp, WHOLE_ARRAY, 0)], LastMovUp);
    if (MathAbs(Target) == 1 || (MathAbs(Target) == 2 && hi == RevHi)) {
      TargetLo = F[hi].P - MidMovDn;
    }
  } else if (Dir < 0 && Time[bar] - F[lo].T < PicPerSeconds) {
    if (RevHi2 != RevHi) {
      RevHi2 = RevHi;
      ADD_TO_ARRAY(LastMovDn, MovDn);
      if (Target < 0)
        MidMovDn = (MovDn[0] + MovDn[1] + MovDn[2]) / 3;
      LastMovDn = 0;
    }
    if (F[RevHi].P - F[lo].P > LastMovDn) {
      LastMovDn = F[RevHi].P - F[lo].P;
    }
    if (Target > 0)
      MidMovDn = MathMax(MovDn[ArrayMaximum(MovDn, WHOLE_ARRAY, 0)], LastMovDn);
    if (MathAbs(Target) == 1 || (MathAbs(Target) == 2 && lo == RevLo)) {
      TargetHi = F[lo].P + MidMovUp;
    }
  }
}

/// @brief Создание заголовков CSV-файла для нейросети
/// @details Создаёт файл Nero_{SYMBOL}{PERIOD}.csv с заголовками.
/// @note Вызывается один раз при инициализации
void EXPERT::NERO_CSV_CREATE() {
  string FileName = "Nero" + ".csv"; //  + "_"+Symbol() + S0(Period())
  if (FileIsExist(FileName)) {
    if (!FileDelete(FileName))
      ERROR_CHECK("Delete " + FileName);
  }
  int File = FileOpen(FileName, FILE_READ | FILE_WRITE);
  if (File < 0)
    ERROR_CHECK(__FUNCTION__ + " Can't open file " + FileName + "!!!");
  string headers = "time;signal;predict;ATR";
  for (uchar f = 0; f < LevelsAmount - 1; f++)
    headers = headers + ";fractal" + S0(f);
  FileWrite(File, headers);
  FileClose(File);
  Print("write headers", FileName);
}

/// @brief Min-Max нормализация значения в [0, 1]
/// @param value исходное значение
/// @param min_val минимум выборки
/// @param max_val максимум выборки
/// @return нормализованное значение (0.5 если min==max)
float NORMALIZE_MINMAX(float value, float min_val, float max_val) {
  if (max_val == min_val)
    return (0.5f);
  return ((value - min_val) / (max_val - min_val));
}

/// @brief Вычисление перцентиля для отсортированного массива
/// @param values массив значений (будет отсортирован)
/// @param count количество элементов
/// @param percentile перцентиль [0.0, 1.0]
/// @return значение на заданном перцентиле (линейная интерполяция)
float CALCULATE_PERCENTILE(float &values[], int count, double percentile) {
  if (count <= 0)
    return (0.0);
  if (count == 1)
    return (values[0]);

  ArraySort(values, count);

  double pos = percentile * (count - 1);
  int idx = (int)MathFloor(pos);

  if (idx >= count - 1)
    return (values[count - 1]);

  double fraction = pos - idx;
  return ((float)(values[idx] * (1.0 - fraction) + values[idx + 1] * fraction));
}

/// @brief Piecewise нормализация с логарифмическим сжатием хвоста
/// @param x исходное значение
/// @param minVal минимум выборки
/// @param percentile значение на заданном перцентиле
/// @param maxVal максимум выборки
/// @return нормализованное значение в [0, 1]
/// @details Алгоритм:
///   - x <= percentile: линейное масштабирование в [0,
///   NORMALIZATION_PERCENTILE]
///   - x > percentile: логарифмическое сжатие в [NORMALIZATION_PERCENTILE, 1.0]
/// @note Предотвращает искажение от выбросов (outliers)
double PiecewiseNormalize(double x, double minVal, double percentile,
                          double maxVal) {
  if (maxVal <= minVal || percentile <= minVal || percentile >= maxVal)
    return 0.0;

  if (x <= minVal)
    return 0.0;
  if (x >= maxVal)
    return 1.0;

  if (x <= percentile) {
    return NORMALIZATION_PERCENTILE * (x - minVal) / (percentile - minVal);
  }

  // z ∈ [1; 10] на хвосте для логарифмирования
  double z = 1.0 + 9.0 * (x - percentile) / (maxVal - percentile);
  double z_max = 10.0;

  double tail = MathLog(z) / MathLog(z_max);

  return NORMALIZATION_PERCENTILE + (1.0 - NORMALIZATION_PERCENTILE) * tail;
}

/// @brief Форматирование нормализованного значения для CSV
/// @param value значение [0, 1]
/// @return строка с 8 знаками после запятой
string S_NORM(float value) { return (DoubleToString(value, 8)); }

/// @brief Запись строки данных уровней в CSV для нейросети
/// @param cur_bar текущий номер бара
/// @details Формат строки CSV (для каждого фрактала):
///   time;signal;predict;ATR;fractal0;fractal1;...
///   где fractal = T:P:Dir:FrntVal:BackVal:Strong:Brk:Rev:PwrSum:Cnt:Imp
/// @note При USE_NORMALIZED_OUTPUT=true применяется нормализация:
///   - Price, Brk: Min-Max нормализация
///   - FrntVal, BackVal, PwrSum, Rev, Imp, Cnt: Piecewise нормализация
/// @warning Файл записывается только после заполнения всего массива
/// (cnt==LevelsAmount)
void EXPERT::NERO_CSV_CREATE(int cur_bar) {
  string FileName = "Nero" + ".csv"; //  + "_"+Symbol() + S0(Period())
  int File = FileOpen(FileName, FILE_READ | FILE_WRITE);
  string NeroInfo = BTIME(cur_bar) + ";0;0;" + S4(Atr.Fast);
  uchar cnt = 1;

  // Первый проход: вычисление min/max и сбор значений для перцентилей
  float minPrice = 999999, maxPrice = 0;
  float minBrk = 999999, maxBrk = 0;
  float minFront = 999999, maxFront = 0;
  float minPwrSum = 999999, maxPwrSum = 0;
  float minRev = 999999, maxRev = 0;
  float minImp = 999999, maxImp = 0;
  float minCnt = 999999, maxCnt = 0;

  float frontValues[LevelsAmount*2];
  float pwrSumValues[LevelsAmount];
  float revValues[LevelsAmount];
  float impValues[LevelsAmount];
  float cntValues[LevelsAmount];
  int frontCount = 0, pwrSumCount = 0, revCount = 0, impCount = 0, cntCount = 0;

  float normPrice, normFrnt, normBack, normPwrSum, normRev, normImp, normCnt,
      normBrk;
  bool hasData = false;

  for (uchar f = 1; f < LevelsAmount; f++) {
    if (F[f].P == 0)
      continue;
    hasData = true;

    if (F[f].P < minPrice)
      minPrice = F[f].P;
    if (F[f].P > maxPrice)
      maxPrice = F[f].P;

    if (F[f].Brk < minBrk)
      minBrk = F[f].Brk;
    if (F[f].Brk > maxBrk)
      maxBrk = F[f].Brk;

    if (F[f].FrntVal < minFront)
      minFront = F[f].FrntVal;
    if (F[f].FrntVal > maxFront)
      maxFront = F[f].FrntVal;
    frontValues[frontCount++] = F[f].FrntVal;

    if (F[f].BackVal < minFront)
      minFront = F[f].BackVal;
    if (F[f].BackVal > maxFront)
      maxFront = F[f].BackVal;
    frontValues[frontCount++] = F[f].BackVal;

    if (F[f].PwrSum < minPwrSum)
      minPwrSum = F[f].PwrSum;
    if (F[f].PwrSum > maxPwrSum)
      maxPwrSum = F[f].PwrSum;
    pwrSumValues[pwrSumCount++] = F[f].PwrSum;

    if (F[f].Rev < minRev)
      minRev = F[f].Rev;
    if (F[f].Rev > maxRev)
      maxRev = F[f].Rev;
    revValues[revCount++] = F[f].Rev;

    if (F[f].Imp < minImp)
      minImp = F[f].Imp;
    if (F[f].Imp > maxImp)
      maxImp = F[f].Imp;
    impValues[impCount++] = F[f].Imp;

    if (F[f].Cnt < minCnt)
      minCnt = F[f].Cnt;
    if (F[f].Cnt > maxCnt)
      maxCnt = F[f].Cnt;
    cntValues[cntCount++] = F[f].Cnt;
  }

  float percentileFront =  CALCULATE_PERCENTILE(frontValues, frontCount, NORMALIZATION_PERCENTILE);
  float percentilePwrSum = CALCULATE_PERCENTILE(pwrSumValues, pwrSumCount, NORMALIZATION_PERCENTILE);
  float percentileRev =    CALCULATE_PERCENTILE(revValues, revCount, NORMALIZATION_PERCENTILE);
  float percentileImp =    CALCULATE_PERCENTILE(impValues, impCount, NORMALIZATION_PERCENTILE);
  float percentileCnt =    CALCULATE_PERCENTILE(cntValues, cntCount, NORMALIZATION_PERCENTILE);

  for (uchar f = 1; f < LevelsAmount; f++) {
    if (F[f].P == 0) continue;
    if (USE_NORMALIZED_OUTPUT) {
      normFrnt = hasData ? (float)PiecewiseNormalize(F[f].FrntVal, minFront,percentileFront, maxFront) : 0.5f;
      normBack = hasData ? (float)PiecewiseNormalize(F[f].BackVal, minFront,percentileFront, maxFront) : 0.5f;
  
      normPwrSum = hasData ? (float)PiecewiseNormalize(F[f].PwrSum, minPwrSum,percentilePwrSum, maxPwrSum) : 0.5f;
      normRev = hasData ? (float)PiecewiseNormalize(F[f].Rev, minRev,percentileRev, maxRev) : 0.5f;
      normImp = hasData ? (float)PiecewiseNormalize(F[f].Imp, minImp,percentileImp, maxImp) : 0.5f;
      normCnt = hasData ? (float)PiecewiseNormalize(F[f].Cnt, minCnt,percentileCnt, maxCnt) : 0.5f;
  
      normPrice = hasData ? NORMALIZE_MINMAX(F[f].P, minPrice, maxPrice) : 0.5f;
      normBrk = hasData ? NORMALIZE_MINMAX(F[f].Brk, minBrk, maxBrk) : 0.5f;

    
      NeroInfo = NeroInfo + ";" + 
         S0(F[f].T) + ":" + 
         S_NORM(normPrice) + ":" +
         S0(F[f].Dir) + ":" + 
         S_NORM(normFrnt) + ":" +
         S_NORM(normBack) + ":" + 
         S0(F[f].Strong) + ":" +
         S_NORM(normBrk) + ":" + 
         S_NORM(normRev) + ":" +
         S_NORM(normPwrSum) + ":" + 
         S_NORM(normCnt) + ":" +
         S_NORM(normImp);
    } else {
      NeroInfo = NeroInfo + ";" + 
         S0(F[f].T) + ":" + 
         S4(F[f].P) + ":" +
         S0(F[f].Dir) + ":" + 
         S4(F[f].FrntVal) + ":" +
         S4(F[f].BackVal) + ":" + 
         S0(F[f].Strong) + ":" + 
         S0(F[f].Brk) + ":" + 
         S4(F[f].Rev) + ":" + 
         S4(F[f].PwrSum) + ":" +
         S0(F[f].Cnt) + ":" + 
         S4(F[f].Imp);
    }
    cnt++;
  }

  if (cnt == LevelsAmount && File > 0) {
    FileSeek(File, 0, SEEK_END);
    FileWrite(File, NeroInfo);
  }
  FileClose(File);
}
