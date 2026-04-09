//+------------------------------------------------------------------+
//| lib_ML_Signal.mqh                                 v3.0           |
//| Назначение: Чтение предрассчитанных ML-сигналов из CSV           |
//|             для тестера стратегий и торговли                      |
//| Автор: SoSimple                                                  |
//| Создан: 2026-03-20                                               |
//| Обновлён: 2026-04-01 — все 10 предсказаний, ratio вычисляется    |
//|           на лету, фильтры Filter3/Filter6                       |
//| Зависимости:                                                     |
//|   Входные данные:                                                |
//|     - MQL4/Files/ml_signals.csv (откуда: API/generate_signals.py)|
//|   Формат CSV:                                                    |
//|     time;signal;up_3;dn_3;up_6;dn_6;up_12;dn_12;up_24;dn_24;up_48;dn_48 |
//|   signal: 1 (BUY), -1 (SELL), 0 (FLAT)                          |
//+------------------------------------------------------------------+
#property strict

// ─── Настройки ──────────────────────────────────────────────────────

#define ML_SIGNALS_FILE  "ml_signals.csv"
#define ML_MAX_SIGNALS   200000
#define ML_Ver   3.0
#define ML_N_PRED_COLS   10  // up_3,dn_3,up_6,dn_6,up_12,dn_12,up_24,dn_24,up_48,dn_48

// ─── Диагностические счётчики ─────────────────────────────────────

int ML_cnt_total    = 0;
int ML_cnt_trend    = 0;
int ML_cnt_lowratio = 0;
int ML_cnt_filter3  = 0;
int ML_cnt_filter6  = 0;
int ML_cnt_posblock = 0;
int ML_cnt_executed = 0;
int ML_cnt_buy      = 0;
int ML_cnt_sell     = 0;

// ─── Хранилище сигналов ─────────────────────────────────────────────

int      ML_SignalCount = 0;
datetime ML_Times[];
char     ML_Signals[];
float    ML_Up3[];
float    ML_Dn3[];
float    ML_Up6[];
float    ML_Dn6[];
float    ML_Up12[];
float    ML_Dn12[];
float    ML_Up24[];
float    ML_Dn24[];
float    ML_Up48[];
float    ML_Dn48[];

// ─── Инициализация: загрузка CSV ────────────────────────────────────

bool ML_INIT() {
   int handle = FileOpen(ML_SIGNALS_FILE, FILE_READ | FILE_CSV | FILE_ANSI, ';');
   if (handle < 0) {
      Print("ML_INIT: Cannot open ", ML_SIGNALS_FILE, " Error=", GetLastError());
      return false;
   }

   // Пропускаем заголовок (time + signal + 10 предсказаний = 12 полей)
   for (int h = 0; h < 2 + ML_N_PRED_COLS; h++)
      FileReadString(handle);

   // Предварительное выделение памяти
   ArrayResize(ML_Times,   ML_MAX_SIGNALS);
   ArrayResize(ML_Signals, ML_MAX_SIGNALS);
   ArrayResize(ML_Up3,     ML_MAX_SIGNALS);
   ArrayResize(ML_Dn3,     ML_MAX_SIGNALS);
   ArrayResize(ML_Up6,     ML_MAX_SIGNALS);
   ArrayResize(ML_Dn6,     ML_MAX_SIGNALS);
   ArrayResize(ML_Up12,    ML_MAX_SIGNALS);
   ArrayResize(ML_Dn12,    ML_MAX_SIGNALS);
   ArrayResize(ML_Up24,    ML_MAX_SIGNALS);
   ArrayResize(ML_Dn24,    ML_MAX_SIGNALS);
   ArrayResize(ML_Up48,    ML_MAX_SIGNALS);
   ArrayResize(ML_Dn48,    ML_MAX_SIGNALS);

   ML_SignalCount = 0;

   while (!FileIsEnding(handle) && ML_SignalCount < ML_MAX_SIGNALS) {
      string time_str = FileReadString(handle);
      if (time_str == "") break;

      int i = ML_SignalCount;
      ML_Times[i]   = StringToTime(time_str);
      ML_Signals[i] = (char)StringToInteger(FileReadString(handle));
      ML_Up3[i]     = (float)StringToDouble(FileReadString(handle));
      ML_Dn3[i]     = (float)StringToDouble(FileReadString(handle));
      ML_Up6[i]     = (float)StringToDouble(FileReadString(handle));
      ML_Dn6[i]     = (float)StringToDouble(FileReadString(handle));
      ML_Up12[i]    = (float)StringToDouble(FileReadString(handle));
      ML_Dn12[i]    = (float)StringToDouble(FileReadString(handle));
      ML_Up24[i]    = (float)StringToDouble(FileReadString(handle));
      ML_Dn24[i]    = (float)StringToDouble(FileReadString(handle));
      ML_Up48[i]    = (float)StringToDouble(FileReadString(handle));
      ML_Dn48[i]    = (float)StringToDouble(FileReadString(handle));

      ML_SignalCount++;
   }

   FileClose(handle);

   // Обрезаем массивы до реального размера
   ArrayResize(ML_Times,   ML_SignalCount);
   ArrayResize(ML_Signals, ML_SignalCount);
   ArrayResize(ML_Up3,     ML_SignalCount);
   ArrayResize(ML_Dn3,     ML_SignalCount);
   ArrayResize(ML_Up6,     ML_SignalCount);
   ArrayResize(ML_Dn6,     ML_SignalCount);
   ArrayResize(ML_Up12,    ML_SignalCount);
   ArrayResize(ML_Dn12,    ML_SignalCount);
   ArrayResize(ML_Up24,    ML_SignalCount);
   ArrayResize(ML_Dn24,    ML_SignalCount);
   ArrayResize(ML_Up48,    ML_SignalCount);
   ArrayResize(ML_Dn48,    ML_SignalCount);

   Print("ML_INIT: Loaded V",ML_Ver, " ", ML_SignalCount, " signals from ", ML_SIGNALS_FILE,
         "  Range: ", TimeToString(ML_Times[0]), " — ", TimeToString(ML_Times[ML_SignalCount-1]),
         "  MinRatio=", DoubleToString(ML_MinRatio,2),
         "  MaxRatio=", (ML_MaxRatio>0 ? DoubleToString(ML_MaxRatio,2) : "off"),
         "  RR_Mode=", ML_RR_Mode,
         "  MaxRR/Cap=", DoubleToString(ML_RR_Mode==0?ML_MaxRR:ML_RR_Cap,1),
         "  Filter3=", DoubleToString(ML_Filter3,1),
         "  Filter6=", DoubleToString(ML_Filter6,1),
         "  Exit=", ML_ExitEnabled, "(thr=", DoubleToString(ML_ExitThreshold,1), ")",
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

   return -1;
}

// ─── Вспомогательная функция: расчёт R:R по режиму ─────────────────

float ML_CalcRR(double ratio) {
   double r = ratio / ML_MinRatio;
   switch(ML_RR_Mode) {
      case 1:  return (float)MathMin(MathLog(r) + 1.0, ML_RR_Cap);
      case 2:  return (float)MathMin(MathSqrt(r),      ML_RR_Cap);
      default: return (float)MathMin(r,                ML_MaxRR);
   }
}

// ─── Торговая функция (вызывается из INPUT) ─────────────────────────

void EXPERT::ML_TRADE() {
   static bool ml_loaded = false;
   if (!ml_loaded) {
      ml_loaded = true;
      ML_INIT();
   }
   if (ML_SignalCount <= 0) return;

   int idx = ML_FindSignal(Time[bar]);
   if (idx < 0) return;

   char sig = ML_Signals[idx];
   if (sig == 0) return;

   // ratio вычисляется на лету из up_12/dn_12
   float ratio_up = ML_Up12[idx] / (ML_Dn12[idx] + 1e-6f);
   float ratio_dn = ML_Dn12[idx] / (ML_Up12[idx] + 1e-6f);

   // ─── ML-exit: закрытие позиции при reverse-сигнале ───────────────
   if (ML_ExitEnabled) {
      if (sig == -1 && BUY.Typ != NONE && ratio_dn >= ML_ExitThreshold) {
         CLOSE_BUY(1, "ML_Exit");
         Print(Mgc,":: ML EXIT BUY reason=ReverseSignal ratio_dn=",
               DoubleToString(ratio_dn,2), " bar=", TimeToString(Time[bar]));
      }
      if (sig == 1 && SEL.Typ != NONE && ratio_up >= ML_ExitThreshold) {
         CLOSE_SEL(1, "ML_Exit");
         Print(Mgc,":: ML EXIT SELL reason=ReverseSignal ratio_up=",
               DoubleToString(ratio_up,2), " bar=", TimeToString(Time[bar]));
      }
   }

   ML_cnt_total++;

   // ─── Трендовый фильтр ─────────────────────────────────────────────
   if (sig == 1 && !UP) {
      ML_cnt_trend++;
      if (!ML_BypassTrend) {
         Print(Mgc,":: ML SKIP reason=TrendFilter sig=1 ratio=",DoubleToString(ratio_up,2),
               " bar=",TimeToString(Time[bar]));
         return;
      }
   }
   if (sig == -1 && !DN) {
      ML_cnt_trend++;
      if (!ML_BypassTrend) {
         Print(Mgc,":: ML SKIP reason=TrendFilter sig=-1 ratio=",DoubleToString(ratio_dn,2),
               " bar=",TimeToString(Time[bar]));
         return;
      }
   }

   // ─── Фильтр up_3/dn_3 ────────────────────────────────────────────
   if (ML_Filter3 > 0) {
      if (sig == 1  && ML_Up3[idx] / (ML_Dn3[idx] + 1e-6f) < ML_Filter3) {
         ML_cnt_filter3++;
         Print(Mgc,":: ML SKIP reason=Filter3 sig=1 up_3=",DoubleToString(ML_Up3[idx],4),
               " dn_3=",DoubleToString(ML_Dn3[idx],4)," bar=",TimeToString(Time[bar]));
         return;
      }
      if (sig == -1 && ML_Dn3[idx] / (ML_Up3[idx] + 1e-6f) < ML_Filter3) {
         ML_cnt_filter3++;
         Print(Mgc,":: ML SKIP reason=Filter3 sig=-1 dn_3=",DoubleToString(ML_Dn3[idx],4),
               " up_3=",DoubleToString(ML_Up3[idx],4)," bar=",TimeToString(Time[bar]));
         return;
      }
   }

   // ─── Фильтр up_6/dn_6 ────────────────────────────────────────────
   if (ML_Filter6 > 0) {
      if (sig == 1  && ML_Up6[idx] / (ML_Dn6[idx] + 1e-6f) < ML_Filter6) {
         ML_cnt_filter6++;
         Print(Mgc,":: ML SKIP reason=Filter6 sig=1 up_6=",DoubleToString(ML_Up6[idx],4),
               " dn_6=",DoubleToString(ML_Dn6[idx],4)," bar=",TimeToString(Time[bar]));
         return;
      }
      if (sig == -1 && ML_Dn6[idx] / (ML_Up6[idx] + 1e-6f) < ML_Filter6) {
         ML_cnt_filter6++;
         Print(Mgc,":: ML SKIP reason=Filter6 sig=-1 dn_6=",DoubleToString(ML_Dn6[idx],4),
               " up_6=",DoubleToString(ML_Up6[idx],4)," bar=",TimeToString(Time[bar]));
         return;
      }
   }

   // ─── Торговля с адаптивным SL/TP ─────────────────────────────────
   if (sig == 1 && BUY.Typ == NONE && ratio_up >= ML_MinRatio
       && (ML_MaxRatio <= 0 || ratio_up <= ML_MaxRatio)) {
      if (SEL.Typ != NONE) {
         CLOSE_SEL(1, "ML_Reversal");
      }
      ML_cnt_executed++; ML_cnt_buy++;
      float sl_dist = (float)MathMax(ML_Dn12[idx] * ML_ScaleK * ATR, ATR * ML_Min_SL_ATR);
      float tp_dist = sl_dist * ML_CalcRR(ratio_up);

      set.BUY.Sig=GOGO;
      set.BUY.Val=(float)Ask+DELTA(D);
      set.BUY.Stp=set.BUY.Val-sl_dist;
      set.BUY.Prf=set.BUY.Val+tp_dist;
      Print(Mgc,":: ML BUY"
            " ratio=",  DoubleToString(ratio_up,2),
            " Val=",    DoubleToString(set.BUY.Val,Digits),
            " Stp=",    DoubleToString(set.BUY.Stp,Digits),
            " Prf=",    DoubleToString(set.BUY.Prf,Digits),
            " ATR=",    DoubleToString(ATR,Digits),
            " bar=",    TimeToString(Time[bar]));
   }
   else if (sig == -1 && SEL.Typ == NONE && ratio_dn >= ML_MinRatio
            && (ML_MaxRatio <= 0 || ratio_dn <= ML_MaxRatio)) {
      if (BUY.Typ != NONE) {
         CLOSE_BUY(1, "ML_Reversal");
      }
      ML_cnt_executed++; ML_cnt_sell++;
      float sl_dist = (float)MathMax(ML_Up12[idx] * ML_ScaleK * ATR, ATR * ML_Min_SL_ATR);
      float tp_dist = sl_dist * ML_CalcRR(ratio_dn);

      set.SEL.Sig=GOGO;
      set.SEL.Val=(float)Bid-DELTA(D);
      set.SEL.Stp=set.SEL.Val+sl_dist;
      set.SEL.Prf=set.SEL.Val-tp_dist;
      Print(Mgc,":: ML SELL"
            " ratio=",  DoubleToString(ratio_dn,2),
            " Val=",    DoubleToString(set.SEL.Val,Digits),
            " Stp=",    DoubleToString(set.SEL.Stp,Digits),
            " Prf=",    DoubleToString(set.SEL.Prf,Digits),
            " ATR=",    DoubleToString(ATR,Digits),
            " bar=",    TimeToString(Time[bar]));
   }
   else {
      float ratio = (sig == 1) ? ratio_up : ratio_dn;
      string skip_reason;
      if      (ratio < ML_MinRatio)                     { skip_reason = "LowRatio";  ML_cnt_lowratio++; }
      else if (ML_MaxRatio > 0 && ratio > ML_MaxRatio) { skip_reason = "HighRatio"; ML_cnt_lowratio++; }
      else                                              { skip_reason = "PosBlock";  ML_cnt_posblock++; }
      Print(Mgc,":: ML SKIP reason=", skip_reason,
            " sig=",sig," ratio=",DoubleToString(ratio,2),
            " BUY.Typ=",BUY.Typ," SEL.Typ=",SEL.Typ,
            " bar=",TimeToString(Time[bar]));
   }
}

// ─── Диагностический отчёт (вызывается из OnTester) ─────────────────

void ML_DIAG_PRINT() {
   Print("=== ML DIAGNOSTICS ===");
   Print("  Total signals:    ", ML_cnt_total);
   Print("  Trend blocked:    ", ML_cnt_trend,
         "  (", ML_cnt_total>0 ? DoubleToString(100.0*ML_cnt_trend/ML_cnt_total,1) : "0", "%)");
   Print("  Filter3 blocked:  ", ML_cnt_filter3,
         "  (", ML_cnt_total>0 ? DoubleToString(100.0*ML_cnt_filter3/ML_cnt_total,1) : "0", "%)");
   Print("  Filter6 blocked:  ", ML_cnt_filter6,
         "  (", ML_cnt_total>0 ? DoubleToString(100.0*ML_cnt_filter6/ML_cnt_total,1) : "0", "%)");
   Print("  LowRatio blocked: ", ML_cnt_lowratio,
         "  (", ML_cnt_total>0 ? DoubleToString(100.0*ML_cnt_lowratio/ML_cnt_total,1) : "0", "%)");
   Print("  Position blocked: ", ML_cnt_posblock,
         "  (", ML_cnt_total>0 ? DoubleToString(100.0*ML_cnt_posblock/ML_cnt_total,1) : "0", "%)");
   Print("  Executed:         ", ML_cnt_executed,
         "  (BUY=",ML_cnt_buy," SELL=",ML_cnt_sell,")");
   Print("  ML_MinRatio=", DoubleToString(ML_MinRatio,3),
         "  ML_ScaleK=", DoubleToString(ML_ScaleK,1),
         "  ML_Filter3=", DoubleToString(ML_Filter3,1),
         "  ML_Filter6=", DoubleToString(ML_Filter6,1),
         "  ML_BypassTrend=", ML_BypassTrend);
   Print("======================");
}
