//+------------------------------------------------------------------+
//!                           lib_PIC.mqh
//!
//! @file     lib_PIC.mqh
//! @brief    Библиотека анализа ценовых уровней (Price Item Calculator)
//! @author   [Автор не указан]
//! @version  230.525+
//! @date     Создан: Неизвестно
//! @date     Обновлён: 2026-03-18
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
//!   - Инкрементальное накопление Up[3]/Dn[3] для каждого фрактала (горизонты H12/H24/H48)
//!   - Экспорт данных в CSV: 18 полей на фрактал (+ Up/Dn/Atr); строка-ATR = Atr.Slow
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
   for (uchar f = 1; f < LevelsAmount; f++) { // перебираем весь массив фракталов от большего к меньшему
      if (F[f].P == 0) { // незаполненная ячейка
         LowestWeight = 0;
         LowestWeightCell = f;
         continue;
      }
      char dir = F[f].Dir;
      if (F[f].T < F[Oldest].T)
         Oldest = f;
      // Критерий удаления = минимальный фронт * кол-во отскоков / дистанция / число пробоев
      Weight = F[f].Pwr * F[f].Flt.Num / (SHIFT(F[f].T) - bar) / (F[f].Brk + 1);
      if (Weight < LowestWeight && F[f].Fls.Phase < START && f != HI && f != LO && f != stpH && f != stpL) {
         LowestWeight = Weight; // самый слабый уровень для удаления, 
         LowestWeightCell = f;  
      }
      if (MathAbs(New - F[f].P) < Atr.Lim) { // совпадение уровней
         PwrSum += F[f].Pwr; // Сумма сил пиков, совпадающих с этим по уровню
         F[f].Cnt++; // кол-во совпадений со всеми пиками (пробитыми и зеркальными)
         Cnt++;      // для поиска уровня с максимальным количеством отскоков
      }
      if (F[f].Brk == BROKEN && New * dir > (F[f].P + Atr.Max * 2) * dir)
         F[f].Brk = MIRROR; // подтверждение зеркального уровня - достаточно глубокий пробой 
      FALSE_BREAK(f);      // проверка ложного пробоя при iSignal=1 (lib_Flat.mqh)
      if (Ver < 230.525 && F[f].Brk > CLEAR) continue;
      if (F[f].Brk > TOUCH) continue;
      if (Dir == dir) { // сонаправленный пик
         if (MathAbs(New - F[f].P) < Atr.Lim) {// поиск совпадающих уровней (в пределах Lim) 
            F[f].Flt.Num++; FltNum++; // увеличиваем кол-во совпадений
            FltLev += F[f].P; // и их сумма для усреднения 
            if (FlatBegin == 0 || F[f].T < F[FlatBegin].T)
               FlatBegin = f; // самый старый пик флэта, для противоположной границы
         } 
         else if (LEV_BREAK(f, New)) continue; // иногда пробой баром "не срабатывает" => доп проверка пробоя фракталом 
         if (F[f].T > ExPicTime) { // время ближайшего превосходящего пика для поиска фронта
            ExPicTime = F[f].T; 
            e = f;
         }
         if (New * dir > F[f].Near * dir) { // самый близкий подход цены к уровню 
            F[f].Near = New; //- его цена
            F[f].NearVal = (New - F[f].Back) * dir; // и амплидуда
         }
      } else { // противолежащий пик
         if (New * dir < F[f].Back * dir) {
            F[f].Back = New; // обновление заднего фронта
            F[f].BackVal = (F[f].P - New) * dir; // и его амплитуды
            F[f].BackT = Time[bar + PicPer]; // время последней вершины Back уровня
            F[f].Pwr = MathMin(F[f].FrntVal, F[f].BackVal);
            F[f].Near = New; // цена самого близкого подхода к уровню
            F[f].NearVal = 0; // амплитуда самого близкого подхода к уровню
            if (F[f].Pwr > ATR * PicPwr && // достаточный передний фронт
               F[f].StrongImp) { // сильный импульс из пика  
               F[f].Strong = 1;
            }
         }
      }
   }
  
   n=LowestWeightCell; // if (Time[bar+PicPer]==StringToTime(TEST_DATE))  V("XX-"+BTIME(bar)+" LowestWeight="+S0(LowestWeight),n, clrRed);
   F[n].P=New;            // пишем в свободную ячейку значение фрактала
   F[n].T=Time[bar+PicPer];      // время возникновения фрактала
   F[n].Flt.T=Time[bar+PicPer];  // время формирования первого (дальнего) пика флэта
   F[n].Flt.Num=FltNum;  // кол-во совпадений с предыдущими непробитыми уровнями
   F[n].Cnt=Cnt;// кол-во совпадений со всеми уровнями  
   F[n].BarTch=0;  // кол-во касаний с барами
   F[n].Dir=Dir;   // направление фрактала: 1=ВЕРШИНА, -1=ВПАДИНА
   F[n].ExT=ExPicTime; // время ближайшего превосходящего пика для поиска фронта
   F[n].Per=PicPer; // кол-во бар до пробоя пика
   F[n].Brk=CLEAR;   // Признак пробитости: -1~NEW, 0~CLEAR, -1-MIRROR, +1-BROKEN
   F[n].Rev=0; // Разворотный(повышающийся) - превосходящий предыдущий пик, только из разворотных выбираются Первые Уровни 
   F[n].Strong=false; // Признак сильного "Первого" уровня (большой передний и задний фронты, задний фронт еще не сформирован, поэтому false)
   F[n].StrongImp=false;
   F[n].TrBrk=NEW; // статус трендового уровня: (-1)-не сформирован,  CLEAR(0)-сформирован,  BROKEN(1)-пробит  Пока хай не опустится под трендовый, он будет не действителен.
   F[n].Fls.Phase=NONE; // стадия ложняка: NONE, START, CONFIRM, BREAK
   F[n].TRG.N=0;  // кол-во вершин в треугольнике
   F[n].PwrSum=PwrSum;  // Сумма сил пиков, совпадающих с этим по уровню
   F[n].Up[H12]=0.0f; F[n].Up[H24]=0.0f; F[n].Up[H48]=0.0f;
   F[n].Dn[H12]=0.0f; F[n].Dn[H24]=0.0f; F[n].Dn[H48]=0.0f;
   F[n].Atr=Atr.Fast; // значение быстрого atr на момент формирования пика 
   if (Dir>0){ // вершина  
      F[n].Tr=New-Atr.Fast;// для вершины трендовый уровень не продажу (пока хай не опустится под трендовый, он будет не действителен)     LINE("PicHi="+S4(F[hi].P)+" F[hi].Trd="+S4(F[hi].Trd), bar+PicPer*2, F[hi].Trd,  bar, F[hi].Trd, clrRed);
      F[n].TrMid=(F[n].P+F[n].Tr)/2;     // серединка на пробой  F[n].Mid=F[n].P-(F[n].P-F[n].Tr)/3;
      F[n].Frnt=LOWEST(SHIFT(ExPicTime)-(bar+PicPer), bar+PicPer+1);   // Передний Фронт уровня (величина развернутого им движения) = минимум, лежащий между новым пиком и превосходящим его баром.    
      F[n].Back=LOWEST(PicPer,bar);// задний фронт = минимальная цена после пика. Будет постепенно увеличиваться по мере удаления цены от уровня       
      F[n].FrntVal=New-F[n].Frnt; // амплитуды
      F[n].BackVal=New-F[n].Back; // этих значений
      F[n].NearVal=0; // Near - уровень, до которого цена приближалась к пику. NearVal - расстояние от Back до Near, т.е. Back от Back
      if (New>F[hi].P)    {F[n].Rev=1;   RevHi=n;}  // "повышающийся пик"  нужен для формирования измеренных движений X("RevHi="+DoubleToString(Rev.F[hi].P,4), Rev.F[hi].P, bar+PicPer, clrRed);    
      hi3=hi2; hi2=hi; hi=n; //   if (F[n].FrntVal>ATR*Pwr) V(S0(n)+","+S4(F[n].FrntVal), New, bar+PicPer, clrRed);
      float ImpHi=F[hi].Imp/(F[lo].Imp+F[lo2].Imp+F[lo3].Imp+float(Point))*3; //V("Imp="+S4(F[hi].Imp)+" dImp="+S4(ImpHi),hi,clrRed);
      base1=LOWEST(PicPer,bar);           // основание справа от пика
      base2=LOWEST(PicPer,bar+PicPer+1);  // основание слева от пика
      F[n].Imp=New*2-base1-base2;  // импульс из пика
      PicColor=DNCLR;
   }else{      // впадина                                                             
      F[n].Tr=New+Atr.Fast;// для впадины трендовый уровень на покупку (пока лоу не поднимется над трендовым, он будет недействительным)
      F[n].TrMid=(F[n].P+F[n].Tr)/2;    // серединка на пробой    F[n].Mid=F[n].P+(F[n].Tr-F[n].P)/3;
      F[n].Frnt=HIGHEST(SHIFT(ExPicTime)-(bar+PicPer), bar+PicPer+1);   // Передний Фронт уровня (величина развернутого им движения) = максимум, лежащий между новым пиком и нижележащим его баром. 
      F[n].Back=HIGHEST(PicPer,bar);// задний фронт = максимальная цена после пика. Будет постепенно увеличиваться по мере удаления цены от уровня        
      F[n].FrntVal=F[n].Frnt-New; // амплитуды
      F[n].BackVal=F[n].Back-New; // этих значений
      F[n].NearVal=0; // Near - уровень, до которого цена приближалась к пику. NearVal - расстояние от Back до Near, т.е. Back от Back
      if (New<F[lo].P)    {F[n].Rev=1;   RevLo=n;} // "понижающаяся впадина"  нужен для формирования измеренных движений X("RevLo="+DoubleToString(F[RevLo].P,4), F[RevLo].P, bar+PicPer, clrGreen);
      lo3=lo2; lo2=lo; lo=n;  //  if (F[n].T==StringToTime("2022.08.03 17:00"))  A(" Frnt="+S4(F[n].Frnt)+" ExPicTime="+DTIME(ExPicTime)+" "+S0(F[e].Brk), New, bar+PicPer+1, clrBlue);
      float ImpLo=F[lo].Imp/(F[hi].Imp+F[hi2].Imp+F[hi3].Imp+float(Point))*3; 
      base1=HIGHEST(PicPer,bar);
      base2=HIGHEST(PicPer,bar+PicPer+1);
      F[n].Imp=base1+base2-New*2;  // импульс из пика
      PicColor=UPCLR; 
      } 
   if (F[n].Imp/F[n].Atr>PicImp){ // резкий отскок, и до предыдущего пика больше суток && SHIFT(ExPicTime)-bar>FltLen*PerAdapter
      F[n].StrongImp=true;//LINE(S0(n)+": Imp="+S4(F[n].Imp/F[n].Atr)+" b1="+S4(base1)+" b2="+S4(base2)+" dt="+S0((SHIFT(ExPicTime)-bar))+" PerAdapter="+S0(PerAdapter), bar+PicPer,High[bar+PicPer], bar+PicPer,Low[bar+PicPer], PicColor,4);
      } // V(S0(n)+": Imp="+S4(F[n].Imp/F[n].Atr), n, clrGreen);  
   F[n].BackT=Time[bar+PicPer];
   F[n].Pwr=MathMin(F[n].FrntVal,F[n].BackVal); // Pwr=MIN(FrntVal,BackVal)   
   FLAT_DETECT(FltLev/FltNum, FlatBegin);
   NERO_CSV_CREATE(bar);
}

/// @brief Поиск ближайшей вершины выше базового уровня
/// @param BaseLev базовый уровень для сравнения
/// @param Delta текущая минимальная дистанция (in/out)
/// @param f индекс проверяемого уровня
/// @param Nearest индекс найденного ближайшего уровня (out)
void EXPERT::LOWEST_HI(float BaseLev, float &Delta, uchar f, uchar &Nearest) {// ближайший к BaseLev уровень CheckLev, возвращается его номер NearestNum и расстояние между ними
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
void EXPERT::HIGHEST_LO(float BaseLev, float &Delta, uchar f, uchar &Nearest) {// ближайший к BaseLev уровень CheckLev, возвращается его номер NearestNum и расстояние между ними
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
void EXPERT::LEVELS_FIND_AROUND(){ // П О И С К   Б Л И З Л Е Ж А Щ И Х   У Р О В Н Е Й 
   float minTrgHi=99999, minTrgLo=99999, minHI=999999, minLO=999999, minH=999999, minL=999999, StpVal=ATR*MathAbs(Trl), 
         PwrImpCntHi=0, PwrImpCntLo=0, Highest=0, Lowest=999999; 
   TrgHi=0; TrgLo=0; stpH=0; stpL=0; // номера уровней в массиве
   HI=0; LO=0;
   for (uchar f=1; f<LevelsAmount; f++){// в нулевом хранится последнее значение, оно же записывается в массив вместо самого слабого пика 
      if (F[f].P==0)    continue; // пустые значения
      int dist = SHIFT(F[f].T) - bar;
      if (dist < 0 || dist > 48) continue;  // вне горизонта — пропускаем
      float hmp = H - F[f].P;   // upward excursion from fractal price
      float pml = F[f].P - L;   // downward excursion from fractal price
      if (dist <= 48) {
         if (hmp > F[f].Up[H48]) F[f].Up[H48] = hmp;
         if (pml > F[f].Dn[H48]) F[f].Dn[H48] = pml;
      }
      if (dist <= 24) {
         if (hmp > F[f].Up[H24]) F[f].Up[H24] = hmp;
         if (pml > F[f].Dn[H24]) F[f].Dn[H24] = pml;
      }
      if (dist <= 12) {
         if (hmp > F[f].Up[H12]) F[f].Up[H12] = hmp;
         if (pml > F[f].Dn[H12]) F[f].Dn[H12] = pml;
      }
      //if (F[f].T==StringToTime(TEST_DATE)) V(" Brk="+S0(F[f].Brk)+" Back="+S4(F[f].Back)+" Frnt="+S4(F[f].Frnt),  bar+1, New, clrRed);
      //if (ABS(F[f].P-H)<Atr.Lim || ABS(F[f].P-L)<Atr.Lim) F[f].BarTch++;  // кол-во касаний с барами
      if (LEV_CHECK(f)>TOUCH) continue;
      F[f].Per++;  // увеличение периода уровня до момента пробития  
      if (F[f].TrBrk==NEW){// трендовый уровень еще не сформирован
         if (F[f].Dir>0 && H<F[f].TrMid) {F[f].TrBrk=CLEAR;}  // окончательнрое формирование трендового, когда хоть один хай опустился ниже его уровня.
         if (F[f].Dir<0 && L>F[f].TrMid) {F[f].TrBrk=CLEAR;}
         }
      if (F[f].TrBrk==CLEAR){ // трендовый уровень сформирован
         if (F[f].Dir>0 && H>F[f].TrMid) F[f].TrBrk=BROKEN; // пробитие трендового уровня    
         if (F[f].Dir<0 && L<F[f].TrMid) F[f].TrBrk=BROKEN; // пробитие трендового уровня        
         }
      if (Target!=0){
         if (F[f].Dir>0)   LOWEST_HI(TargetHi, minTrgHi, f, TrgHi);  // ближайший пик к расчитанному целевому уровню   
         else              HIGHEST_LO(TargetLo, minTrgLo, f, TrgLo);    
         }
      // if (Tch==0 && F[f].Brk==TOUCH)   continue; // Пик дб без касаний при Tch=0
      // if (F[f].TrBrk!=CLEAR) continue; // только с непробитым cформированным трендовым   Trd>0  && 
      if (Rev==1 && F[f].Rev==0)       continue; // уровень должен пробить хотябы один пик (REV=1)   
      if (Rev==2 && F[f].FrntVal>F[f].BackVal+Atr.Lim) continue; // задний фронт д.б. больше переднего  (признак тренда)
      // TRAILING/STOP LEVELS
      if (F[f].BackVal>StpVal){
         if (F[f].Dir>0){  if (F[f].T>SEL.T) LOWEST_HI (H, minH, f, stpH);  // ближайший пик к текущей цене для шортового стопа
         }else{            if (F[f].T>BUY.T) HIGHEST_LO(L, minL, f, stpL);  // ближайший пик к текущей цене для лонгового стопа    
         }  }
      // П Е Р В Ы E    У Р О В Н И   
      if (F[f].Strong!=true) continue; 
      if (F[f].T<TimeFrom) continue; // первые уровни - любые экстремумы за Days
      if (Days<0){ // работа от дальних уровней на периоде Days с заданными Pwr, Cnt, Imp
         if (F[f].Dir>0)   HIGHEST_HI(Highest,f,HI);
         else              LOWEST_LO (Lowest ,f,LO);
      }else{ // работа от ближних уровней на |Days| (0~на всей истории) с заданными Pwr, Cnt, Imp
         if (F[f].Dir>0)   LOWEST_HI (H, minHI, f, HI);  // ближайший к текущей цене
         else              HIGHEST_LO(L, minLO, f, LO);  // первый  уровень
         }  
      }
   // У Р О В Н И    С Е Р Е Д И Н К И
   if (HI!=lastHI)   {lastHI=HI; HI2=0;}
   if (LO!=lastLO)   {lastLO=LO; LO2=0;}
   if (HI>0 && Hi_checksum!=F[HI].P+F[HI].Back && H>F[HI].Back+F[HI].BackVal/4){ // обновилась вершина, либо Back  && F[HI].NearVal>F[HI].BackVal/4
      Hi_checksum=F[HI].P+F[HI].Back; // обновление контрольной суммы          
      HI2=MID_LEV(HI); 
      LINE("HI="+S0(HI)+" P="+S4(F[HI].P)+" Frnt/Back="+S4(F[HI].FrntVal)+"/"+S4(F[HI].BackVal)+" Atr.F/S="+S5(Atr.Fast)+"/"+S5(Atr.Slow), F[HI].T,F[HI].P, F[HI].BackT,F[HI].Back,DNCLR,0);
      //LINE("HI2="+S0(HI2)+" HI="+S0(HI)+" Back="+S4(F[HI].Back)+"/"+DTIME(F[HI].BackT)+" HI2="+S4(HI2), SHIFT(F[HI].T),F[HI2].P,  bar,F[HI2].P, DNCLR,0);
      } 
   if (LO >0 && Lo_checksum!=F[LO].P+F[LO].Back && L<F[LO].Back-F[LO].BackVal/4){ // обновилась вершина, либо ее Back  && F[LO].NearVal>F[LO].BackVal/4
      Lo_checksum=F[LO].P+F[LO].Back; // обновление контрольной суммы   
      LO2=MID_LEV(LO); 
      LINE("LO="+S0(LO)+" P="+S4(F[LO].P)+" Frnt/Back="+S4(F[LO].FrntVal)+"/"+S4(F[LO].BackVal)+" Atr.F/S="+S5(Atr.Fast)+"/"+S5(Atr.Slow), F[LO].T,F[LO].P, F[LO].BackT, F[LO].Back,UPCLR,0); 
      //LINE("LO2="+S0(LO2)+" LO="+S0(LO)+" Back="+S4(F[LO].Back)+"/"+DTIME(F[LO].BackT)+" LO2="+S4(LO2), SHIFT(F[LO].T),F[LO2].P,  bar,F[LO2].P, UPCLR,0); //V("mid="+S0(LO2),F[LO2].P,bar,clrBlue);
      }
   if (HI)  LINE("HI="+S0(HI)+" HI2="+S0(HI2)+" Pwr="+S4(F[HI].Pwr)+" Imp="+S4(F[HI].Imp/F[HI].Atr)+" Cnt="+S0(F[HI].Cnt), bar,F[HI].P,   bar+1,F[HI].P, DNCLR,2);
   if (LO)  LINE("LO="+S0(LO)+" LO2="+S0(LO2)+" Pwr="+S4(F[LO].Pwr)+" Imp="+S4(F[LO].Imp/F[LO].Atr)+" Cnt="+S0(F[LO].Cnt), bar,F[LO].P,   bar+1,F[LO].P, UPCLR,2);
   if (HI2) LINE("HI2="+S0(HI2)+" HI="+S0(HI)+" Back="+S4(F[HI].Back)+"/"+DTIME(F[HI].BackT)+" HI2="+S4(HI2),              bar,F[HI2].P,  bar+1,F[HI2].P,DNCLR,0);
   if (LO2) LINE("LO2="+S0(LO2)+" LO="+S0(LO)+" Back="+S4(F[LO].Back)+"/"+DTIME(F[LO].BackT)+" LO2="+S4(LO2),              bar,F[LO2].P,  bar+1,F[LO2].P,UPCLR,0);
   LINE("HI="+S0(HI)+" LO="+S0(LO)+" Back[28]="+S4(F[28].BackVal)+" PicPwr="+S4(ATR*PicPwr)+" frst="+S0(F[28].Strong), bar+1, Close[bar+1], bar, Close[bar],  clrSilver,0); 
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
bool EXPERT::LEV_TOUCH(uchar f){ // touching
   if (F[f].TrBrk<CLEAR) return(false); // Трендовый уровень не успел сформироваться, соответсвенно пик тоже 
   //if (F[f].T==StringToTime(TEST_DATE)) V(" Brk="+S0(F[f].Brk)+" Back="+S4(F[f].Back)+" Frnt="+S4(F[f].Frnt),  bar+1, New, clrRed);
   if (F[f].Dir>0 && H>F[f].P-Atr.Lim && H<F[f].P+Atr.Lim)  {F[f].Brk=TOUCH; return (true);} //LINE("LO=", SHIFT(F[f].T),F[f].P,  bar,H, UPCLR,0);
   if (F[f].Dir<0 && L<F[f].P+Atr.Lim && L>F[f].P-Atr.Lim)  {F[f].Brk=TOUCH; return (true);}
   return(false);
   }

/// @brief Проверка пробоя уровня баром
/// @param f индекс уровня в массиве
/// @return true если текущий бар пробивает уровень
/// @note Вызывает SET_BROKEN() при пробое
bool EXPERT::LEV_BREAK(uchar f){ // breaking by bar
   if (F[f].Dir>0 && H>=F[f].P+Atr.Lim)   {SET_BROKEN(f); return (true); } // A("BREAK "+S0(f), H, bar, clrBlack); 
   if (F[f].Dir<0 && L<=F[f].P-Atr.Lim)   {SET_BROKEN(f); return (true);}
   return(false);
   }  

/// @brief Проверка пробоя уровня новым фракталом
/// @param f индекс уровня в массиве
/// @param pic цена нового фрактала
/// @return true если фрактал пробивает уровень
bool EXPERT::LEV_BREAK(uchar f, float pic){ // breaking by new pic
   if (F[f].Dir>0 && pic>=F[f].P+Atr.Lim)   {SET_BROKEN(f); return (true);}
   if (F[f].Dir<0 && pic<=F[f].P-Atr.Lim)   {SET_BROKEN(f); return (true);}
   return(false);
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
void EXPERT::SET_BROKEN(uchar f){
   F[f].BrkT=Time[bar]; // время пробития
   F[f].Brk=BROKEN;     // статус
   if (F[f].Dir>0){// A("f="+S0(f)+" HI= "+S0(HI)+" P="+S4(F[f].P), F[f].P, bar, clrBlack); 
      if (f==HI)   {HI=0;  if (iGlb==1) Trnd.Global= 1;} //   X("break HI "+S0(f),F[f].P,bar,DNCLR);
      if (f==HI2)  {HI2=0; if (iGlb==2) Trnd.Global= 1;} //   X("break HI2 "+S0(f),F[f].P,bar,DNCLR);
      Trnd.PicBrk++; if (Trnd.PicBrk> iLoc) Trnd.PicBrk= iLoc; // кол-во пробитых подряд пиков для фильтра входа
   }else{
      if (f==LO)   {LO=0;  if (iGlb==1) Trnd.Global=-1;} //   X("break LO "+S0(f),F[f].P,bar,UPCLR);
      if (f==LO2)  {LO2=0; if (iGlb==2) Trnd.Global=-1;} //   X("break LO2 "+S0(f),F[f].P,bar,UPCLR);
      Trnd.PicBrk--; if (Trnd.PicBrk<-iLoc) Trnd.PicBrk=-iLoc;
   }
   if (F[f].Pwr>ATR*PicPwr) {  // был пробит сильный уровень
      F[f].Fls.Phase=WAIT;} // его ложняк будет интересен: ставим начальный флаг. Флаг сбрасывается на "BREAK"  при формировании уровня в FLAT_DETECT()
   //if (F[f].Flt.Len>0){// если это был флэт шириной более FltLen бар,
   //   if (F[f].Dir>0) Trnd.FltBrk=F[f].P; else Trnd.FltBrk=-F[f].P;//  генерится сигнал "пробой флэта"
   //   }
   
   }  

/// @brief Определение локального тренда
/// @details Использует:
///   - Trnd.PicBrk - счётчик пробитых вершин/впадин
///   - Trnd.Flat - выход из флэта
/// @note Записывает результат в Trnd.Local: +1 UP, -1 DOWN, 0 неопределён
void EXPERT::LOCAL_TREND(){
   // Проверка прошлого тренда
   if (Trnd.Flat>0 && L<F[nFlt].Flt.DnLev-Atr.Lim) {Trnd.Flat=0; }//X(" Trnd.Flat=0, Dn="+S4(F[nFlt].Flt.DnLev),L,bar,clrBlue);  // Если цена вышла из флэта в ту же сторону, с которой зашла,
   if (Trnd.Flat<0 && H>F[nFlt].Flt.UpLev+Atr.Lim) {Trnd.Flat=0; }//X(" Trnd.Flat=0, Up="+S4(F[nFlt].Flt.UpLev),H,bar,clrBlue); // Прошлый тренд анулируется.
   
   if (!hi || !lo) return;
   Trnd.Local=0;
   if (Trnd.PicBrk>0) Trnd.Local=1;   
   if (Trnd.PicBrk<0) Trnd.Local=-1; 
   if (iFlt>0) Trnd.Local+=Trnd.Flat; // Выход из флэта напротив входа
   if (Trnd.Local>0)    LINE("Trnd.Local="+S0(Trnd.Local)+" Dn="+S4(F[nFlt].Flt.DnLev),  bar,L,   bar,H, UPCLR,3); 
   if (Trnd.Local<0)    LINE("Trnd.Local="+S0(Trnd.Local),  bar,L,   bar,H, DNCLR,3);
   }

/// @brief Простое определение точки контроля (POC)
/// @details Находит плотное скопление баров без пропусков.
/// @note Обновляет PocCnt (длина), PocCenter (серединка), HiZone, DnZone
void EXPERT::POC_SIMPLE(){    // определение плотного скопления бар без пропусков
   HiZone=MIN(H,HiZone); // С каждым новым баром края диапазона h и l
   DnZone=MAX(L,DnZone); // обрезаются с учетом новых High и Low
   if (HiZone>DnZone) {PocCnt++; PocCenter=float((HiZone+DnZone)/2);} // считаем длину сформированного диапазона и его серединку
   else{// Диапазон прервался (сузился до нуля)
      //LINE("POC="+S0(PocCnt) ,bar+PocCnt,PocCenter, bar,PocCenter, PocColor,0);
      PocCnt=1;    
      HiZone=H; 
      DnZone=L; 
   }  }  

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
float EXPERT::PIC_PWR(uchar PowerType, uchar f){
   float Power;
   switch(PowerType){
      case 1:  Power=F[f].Pwr;            break;  // пик с максимальным фронтом      
      case 2:  Power=F[f].Pwr*F[f].Cnt;   break;  // и макс кол-вом отскоков
      case 3:  Power=F[f].Cnt;            break;  // зона с максимальным кол-вом отскоков
      case 4:  Power=F[f].PwrSum;         break;  // зона с максимальной силой отскоков
      case 5:  Power=F[f].Imp/F[f].Atr;   break;  // пик с максимальным импульсом
      case 6:  Power=F[f].Imp/F[f].Atr*F[f].Cnt;   break; // и макс. кол-вом отскоков
      default: Power=0; 
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
uchar EXPERT::MID_LEV(uchar f, float UpLev, float DnLev, datetime time0, datetime time1){// уровень серединки: 1-пик с макс. фонтом, 2-макс фронт с макс кол-вом пиков, 3-макс. кол-во отскоков, 4-макс. сила отскоков
   float Power=0, MaxPower=0;
   uchar Pic=0;
   if (UpLev<DnLev)  SWAP(UpLev,DnLev);
	for (f=1; f<LevelsAmount; f++){  // 
      if (F[f].Brk>TOUCH || F[f].P<=DnLev || F[f].P>=UpLev || F[f].T<time0 || F[f].T>time1) continue; // пик за пределами интересующего нас диапазона 
      Power=PIC_PWR(MidTyp, f);   
	   if (Power>MaxPower){   //Power
         MaxPower=Power; 
         Pic=f;
      }  }   	//if (f1==84) LINE("2: f1="+S0(f1)+" Back="+S4(F[f1].Back)+"/"+DTIME(F[f1].BackT), time0,F[Pic].P,  time1,F[Pic].P, clrBlack,0); 
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
void EXPERT::TARGET_COUNT(){// расчет целевых уровней окончания движения на основании измерения предыдущих безоткатных движений
   if (Target==0) return; // Target=-2..2: >0~макс. <0~средн движение от 1-последнего, 2-разворотного пика  
   if (Dir>0 && Time[bar]-F[hi].T<PicPerSeconds){ // только что сформированная вершина (разница с текущим баром в пределах периода пика с запасом)
      if (RevLo2!=RevLo){// пересортировка, если были понижающиеся Lo, иначе обновляется лишь последнее движение LastMovUp
         RevLo2=RevLo;
         ADD_TO_ARRAY(LastMovUp,MovUp); // пересортировка массива  и добавление последнее движение
         if (Target<0)  MidMovUp=(MovUp[0]+MovUp[1]+MovUp[2])/3; // среднее движение
         LastMovUp=0;      
         }
      if (F[hi].P-F[RevLo].P>LastMovUp) {LastMovUp=F[hi].P-F[RevLo].P;}// обновляем последнее движение, если новый пик дальше от разворотной впадины, чем предыдущий   LINE("LastMovUp="+S4(LastMovUp)+" F[RevLo].P="+S4(F[RevLo].P), SHIFT(F[RevLo].T), F[RevLo].P,  bar+PicPer, F[hi].P, clrRed);
      if (Target>0) MidMovUp=MathMax(MovUp[ArrayMaximum(MovUp,WHOLE_ARRAY,0)],LastMovUp);  // среднее максимальных значений прошлых и последнего движения
      if (MathAbs(Target)==1 || (MathAbs(Target)==2 && hi==RevHi)){ // отмеряем целевое движение вниз от последнего пика, или только от разворотного пика
         TargetLo=F[hi].P-MidMovDn;} //LINE(S4(MidMovDn), F[hi].T, F[hi].P,  F[hi].T, TargetLo, clrOrange,0);
   }else if (Dir<0 && Time[bar]-F[lo].T<PicPerSeconds){// // только что сформированная впадина (разница с текущим баром в пределах периода пика с запасом)
      if (RevHi2!=RevHi){// пересортировка, если были повышающиеся Hi, иначе обновляется лишь последнее движение LastMovDn
         RevHi2=RevHi;   
         ADD_TO_ARRAY(LastMovDn,MovDn);
         if (Target<0)  MidMovDn=(MovDn[0]+MovDn[1]+MovDn[2])/3; // среднее движение
         LastMovDn=0;
         }    
      if (F[RevHi].P-F[lo].P>LastMovDn)  {LastMovDn=F[RevHi].P-F[lo].P;}// обновляем последнее движение, если новый пик дальше от разворотной впадины, чем предыдущий   LINE("LastMovDn="+S4(LastMovDn)+" MidMovDn="+S4(MidMovDn), SHIFT(F[RevHi].T), F[RevHi].P,  bar+PicPer, F[lo].P, clrGreen);  
      if (Target>0) MidMovDn=MathMax(MovDn[ArrayMaximum(MovDn,WHOLE_ARRAY,0)],LastMovDn);  // среднее максимальных значений прошлых и последнего движения
      if (MathAbs(Target)==1 || (MathAbs(Target)==2 && lo==RevLo)){ // отмеряем целевое движение вверх от последнего пика, или только от разворотного пика
         TargetHi=F[lo].P+MidMovUp; //LINE("Mid="+S4(MidMovUp)+" Last="+S4(LastMovUp)+", 012="+S4(MovUp[0])+", "+S4(MovUp[1])+", "+S4(MovUp[2]), F[lo].T, F[lo].P,  F[lo].T, TargetHi, clrCornflowerBlue,0); 
   }  }  }   

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
string S_NORM(float value) {
   return (DoubleToString(value, 8));
}

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
   string NeroInfo = BTIME(cur_bar) + ";0;0;" + S4(Atr.Slow);
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
                    S_NORM(normImp) + ":" +
                    S4(F[f].Up[H12]) + ":" + S4(F[f].Dn[H12]) + ":" +
                    S4(F[f].Up[H24]) + ":" + S4(F[f].Dn[H24]) + ":" +
                    S4(F[f].Up[H48]) + ":" + S4(F[f].Dn[H48]) + ":" + S4(F[f].Atr);
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
                    S4(F[f].Imp) + ":" +
                    S4(F[f].Up[H12]) + ":" + S4(F[f].Dn[H12]) + ":" +
                    S4(F[f].Up[H24]) + ":" + S4(F[f].Dn[H24]) + ":" +
                    S4(F[f].Up[H48]) + ":" + S4(F[f].Dn[H48]) + ":" + S4(F[f].Atr);
      }
      cnt++;
   }

   if (cnt == LevelsAmount && File > 0) {
      FileSeek(File, 0, SEEK_END);
      FileWrite(File, NeroInfo);
   }
   FileClose(File);
}
//+------------------------------------------------------------------+
