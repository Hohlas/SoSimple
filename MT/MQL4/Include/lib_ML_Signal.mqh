//+------------------------------------------------------------------+
//| lib_ML_Signal.mqh                                 v2.0           |
//| Назначение: Чтение предрассчитанных ML-сигналов из CSV           |
//|             для тестера стратегий и торговли                      |
//| Автор: SoSimple                                                  |
//| Создан: 2026-03-20                                               |
//| Обновлён: 2026-03-22 — асимметричный R:R, диагностика, bypass    |
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

double ML_MinRatio     = 2.665;  // порог ratio (совпадает с Python θ=2.665)
double ML_MaxRR        = 4.0;    // максимальный множитель R:R (cap)
double ML_ScaleK       = 20.0;   // множитель для перевода pred_up/dn в ATR (SL/TP)
bool   ML_BypassTrend  = true;   // true = ML-сигналы игнорируют трендовый фильтр

// ─── Диагностические счётчики ─────────────────────────────────────

int ML_cnt_total    = 0;  // всего ML-сигналов (sig!=0) в диапазоне теста
int ML_cnt_trend    = 0;  // заблокировано трендовым фильтром
int ML_cnt_lowratio = 0;  // заблокировано ratio < ML_MinRatio
int ML_cnt_posblock = 0;  // заблокировано открытой позицией
int ML_cnt_executed = 0;  // выставлено ордеров
int ML_cnt_buy      = 0;
int ML_cnt_sell     = 0;

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
         "  Range: ", TimeToString(ML_Times[0]), " — ", TimeToString(ML_Times[ML_SignalCount-1]),
         "  MinRatio=", DoubleToString(ML_MinRatio,3),
         "  MaxRR=", DoubleToString(ML_MaxRR,1),
         "  BypassTrend=", ML_BypassTrend);

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

// ─── Торговая функция (вызывается из INPUT) ─────────────────────────

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

   ML_cnt_total++;

   // ─── Трендовый фильтр (диагностика + опциональный bypass) ───
   if (sig == 1 && !UP) {
      ML_cnt_trend++;
      if (!ML_BypassTrend) {
         Print(Mgc,":: ML SKIP reason=TrendFilter sig=1 Global=",Trnd.Global,
               " Local=",Trnd.Local," ratio=",DoubleToString(ML_RatioUp[idx],2),
               " bar=",TimeToString(Time[bar]));
         return;
      }
   }
   if (sig == -1 && !DN) {
      ML_cnt_trend++;
      if (!ML_BypassTrend) {
         Print(Mgc,":: ML SKIP reason=TrendFilter sig=-1 Global=",Trnd.Global,
               " Local=",Trnd.Local," ratio=",DoubleToString(ML_RatioDn[idx],2),
               " bar=",TimeToString(Time[bar]));
         return;
      }
   }

   // ─── Торговля с адаптивным SL/TP ───
   if (sig == 1 && BUY.Typ == NONE && SEL.Typ == NONE && ML_RatioUp[idx] >= ML_MinRatio) {
      ML_cnt_executed++; ML_cnt_buy++;
      // Адаптивный расчёт дистанций (min 1.5 ATR для защиты от рыночного шума)
      float sl_dist = (float)MathMax(ML_PredDn[idx] * ML_ScaleK * ATR, ATR * 1.5); 
      float tp_dist = (float)MathMax(ML_PredUp[idx] * ML_ScaleK * ATR, sl_dist * 1.0); // R:R >= 1.0
      
      set.BUY.Sig=GOGO;
      set.BUY.Val=(float)Ask+DELTA(D);
      set.BUY.Stp=set.BUY.Val-sl_dist;
      set.BUY.Prf=set.BUY.Val+tp_dist;
      Print(Mgc,":: ML BUY"
            " ratio=",  DoubleToString(ML_RatioUp[idx],2),
            " Val=",    DoubleToString(set.BUY.Val,Digits),
            " Stp=",    DoubleToString(set.BUY.Stp,Digits),
            " Prf=",    DoubleToString(set.BUY.Prf,Digits),
            " ATR=",    DoubleToString(ATR,Digits),
            " bar=",    TimeToString(Time[bar]));
   }
   else if (sig == -1 && SEL.Typ == NONE && BUY.Typ == NONE && ML_RatioDn[idx] >= ML_MinRatio) {
      ML_cnt_executed++; ML_cnt_sell++;
      // Адаптивный расчёт дистанций (min 1.5 ATR для защиты от рыночного шума)
      float sl_dist = (float)MathMax(ML_PredUp[idx] * ML_ScaleK * ATR, ATR * 1.5); 
      float tp_dist = (float)MathMax(ML_PredDn[idx] * ML_ScaleK * ATR, sl_dist * 1.0); // R:R >= 1.0

      set.SEL.Sig=GOGO;
      set.SEL.Val=(float)Bid-DELTA(D);
      set.SEL.Stp=set.SEL.Val+sl_dist;
      set.SEL.Prf=set.SEL.Val-tp_dist;
      Print(Mgc,":: ML SELL"
            " ratio=",  DoubleToString(ML_RatioDn[idx],2),
            " Val=",    DoubleToString(set.SEL.Val,Digits),
            " Stp=",    DoubleToString(set.SEL.Stp,Digits),
            " Prf=",    DoubleToString(set.SEL.Prf,Digits),
            " ATR=",    DoubleToString(ATR,Digits),
            " bar=",    TimeToString(Time[bar]));
   }
   else {
      string skip_reason;
      if      (sig== 1 && ML_RatioUp[idx] < ML_MinRatio) { skip_reason = "LowRatio";  ML_cnt_lowratio++; }
      else if (sig==-1 && ML_RatioDn[idx] < ML_MinRatio) { skip_reason = "LowRatio";  ML_cnt_lowratio++; }
      else                                                 { skip_reason = "PosBlock";  ML_cnt_posblock++; }
      Print(Mgc,":: ML SKIP reason=", skip_reason,
            " sig=",    sig,
            " BUY.Typ=",BUY.Typ," SEL.Typ=",SEL.Typ,
            " ratio=",  DoubleToString(sig==1?ML_RatioUp[idx]:ML_RatioDn[idx],2),
            " bar=",    TimeToString(Time[bar]));
   }
}

// ─── Диагностический отчёт (вызывается из OnTester) ─────────────────

void ML_DIAG_PRINT() {
   Print("=== ML DIAGNOSTICS ===");
   Print("  Total signals:    ", ML_cnt_total);
   Print("  Trend blocked:    ", ML_cnt_trend,
         "  (", ML_cnt_total>0 ? DoubleToString(100.0*ML_cnt_trend/ML_cnt_total,1) : "0", "%)");
   Print("  LowRatio blocked: ", ML_cnt_lowratio,
         "  (", ML_cnt_total>0 ? DoubleToString(100.0*ML_cnt_lowratio/ML_cnt_total,1) : "0", "%)");
   Print("  Position blocked: ", ML_cnt_posblock,
         "  (", ML_cnt_total>0 ? DoubleToString(100.0*ML_cnt_posblock/ML_cnt_total,1) : "0", "%)");
   Print("  Executed:         ", ML_cnt_executed,
         "  (BUY=",ML_cnt_buy," SELL=",ML_cnt_sell,")");
   Print("  ML_MinRatio=", DoubleToString(ML_MinRatio,3),
         "  ML_ScaleK=", DoubleToString(ML_ScaleK,1),
         "  ML_BypassTrend=", ML_BypassTrend);
   Print("======================");
}
