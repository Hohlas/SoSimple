//+------------------------------------------------------------------+
//| lib_ML_Signal.mqh                                 v1.1           |
//| Назначение: Чтение предрассчитанных ML-сигналов из CSV           |
//|             для тестера стратегий и торговли                      |
//| Автор: SoSimple                                                  |
//| Создан: 2026-03-20                                               |
//| Зависимости:                                                     |
//|   Входные данные:                                                |
//|     - MQL4/Files/ml_signals.csv (откуда: API/generate_signals.py)|
//|   Формат CSV:                                                    |
//|     time;signal;pred_up;pred_dn;ratio_up;ratio_dn                |
//|     2004.07.07 20:00;0;1.2;0.8;1.5;0.67                         |
//|   signal: 1 (BUY), -1 (SELL), 0 (FLAT)                          |
//+------------------------------------------------------------------+
#property strict

// ─── Настройки ──────────────────────────────────────────────────────

#define ML_SIGNALS_FILE  "ml_signals.csv"
#define ML_MAX_SIGNALS   200000  // максимум строк в CSV

// ─── Хранилище сигналов ─────────────────────────────────────────────

int      ML_SignalCount = 0;
datetime ML_Times[];
char     ML_Signals[];
float    ML_PredUp[];
float    ML_PredDn[];
float    ML_RatioUp[];
float    ML_RatioDn[];

// ─── Инициализация: загрузка CSV ────────────────────────────────────

bool ML_INIT() {
   int handle = FileOpen(ML_SIGNALS_FILE, FILE_READ | FILE_CSV | FILE_ANSI, ';');
   if (handle < 0) {
      Print("ML_INIT: Cannot open ", ML_SIGNALS_FILE, " Error=", GetLastError());
      return false;
   }
   
   // Пропускаем заголовок
   FileReadString(handle); // time
   FileReadString(handle); // signal
   FileReadString(handle); // pred_up
   FileReadString(handle); // pred_dn
   FileReadString(handle); // ratio_up
   FileReadString(handle); // ratio_dn
   
   // Предварительное выделение памяти
   ArrayResize(ML_Times,   ML_MAX_SIGNALS);
   ArrayResize(ML_Signals, ML_MAX_SIGNALS);
   ArrayResize(ML_PredUp,  ML_MAX_SIGNALS);
   ArrayResize(ML_PredDn,  ML_MAX_SIGNALS);
   ArrayResize(ML_RatioUp, ML_MAX_SIGNALS);
   ArrayResize(ML_RatioDn, ML_MAX_SIGNALS);
   
   ML_SignalCount = 0;
   
   while (!FileIsEnding(handle) && ML_SignalCount < ML_MAX_SIGNALS) {
      string time_str = FileReadString(handle);
      if (time_str == "") break;
      
      ML_Times[ML_SignalCount]   = StringToTime(time_str);
      ML_Signals[ML_SignalCount] = (char)StringToInteger(FileReadString(handle));
      ML_PredUp[ML_SignalCount]  = (float)StringToDouble(FileReadString(handle));
      ML_PredDn[ML_SignalCount]  = (float)StringToDouble(FileReadString(handle));
      ML_RatioUp[ML_SignalCount] = (float)StringToDouble(FileReadString(handle));
      ML_RatioDn[ML_SignalCount] = (float)StringToDouble(FileReadString(handle));
      
      ML_SignalCount++;
   }
   
   FileClose(handle);
   
   // Обрезаем массивы до реального размера
   ArrayResize(ML_Times,   ML_SignalCount);
   ArrayResize(ML_Signals, ML_SignalCount);
   ArrayResize(ML_PredUp,  ML_SignalCount);
   ArrayResize(ML_PredDn,  ML_SignalCount);
   ArrayResize(ML_RatioUp, ML_SignalCount);
   ArrayResize(ML_RatioDn, ML_SignalCount);
   
   Print("ML_INIT: Loaded ", ML_SignalCount, " signals from ", ML_SIGNALS_FILE,
         "  Range: ", TimeToString(ML_Times[0]), " — ", TimeToString(ML_Times[ML_SignalCount-1]));
   
   return true;
}

// ─── Бинарный поиск сигнала по времени ──────────────────────────────

int ML_FindSignal(datetime barTime) {
   int lo = 0, hi = ML_SignalCount - 1;
   
   while (lo <= hi) {
      int mid = (lo + hi) / 2;
      if (ML_Times[mid] == barTime) return mid;
      else if (ML_Times[mid] < barTime) lo = mid + 1;
      else hi = mid - 1;
   }
   
   return -1; // не найден
}

// ─── Торговая функция (вызывается из MAIN) ──────────────────────────

void EXPERT::ML_TRADE() {
   // Ленивая инициализация: загрузка CSV при первом вызове
   static bool ml_loaded = false;
   if (!ml_loaded) {
      ml_loaded = true;  // однократная попытка
      ML_INIT();
   }
   if (ML_SignalCount <= 0) return;
   
   int idx = ML_FindSignal(Time[bar]);
   if (idx < 0) return;  // нет сигнала для этого бара
   
   char sig = ML_Signals[idx];
   if (sig == 0) return;  // FLAT
   
   // Лог сигнала
   Print(Mgc, ":: ML Signal=", sig,
         " pred_up=", DoubleToString(ML_PredUp[idx], 3),
         " pred_dn=", DoubleToString(ML_PredDn[idx], 3),
         " ratio_up=", DoubleToString(ML_RatioUp[idx], 2),
         " ratio_dn=", DoubleToString(ML_RatioDn[idx], 2),
         " bar_time=", TimeToString(Time[bar]));
   
   // Торговля
   if (sig == 1 && BUY.Typ == NONE) {
      set.BUY.Val=(float)Ask+DELTA(D); // V("BUY="+S4(set.BUY.Stp+Stop)+"/"+S4(Stop),bar,Low[bar],clrBlack); 
      set.BUY.Stp=set.BUY.Val-DELTA(Stp);
      set.BUY.Prf=set.BUY.Val+DELTA(Prf);
   }
   else if (sig == -1 && SEL.Typ == NONE) {
      set.SEL.Val=(float)Bid-DELTA(D); // 
      set.SEL.Stp=set.SEL.Val+DELTA(Stp);
      set.SEL.Prf=set.SEL.Val-DELTA(Prf);
   }
}
