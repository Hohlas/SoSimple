//+------------------------------------------------------------------+
//| lib_ML_Signal_TB.mqh                              v1.0           |
//| Назначение: Чтение Triple Barrier ML-сигналов из CSV             |
//|             для тестера стратегий и торговли                      |
//| Автор: SoSimple                                                  |
//| Создан: 2026-03-23                                               |
//| Зависимости:                                                     |
//|   Входные данные:                                                |
//|     - MQL4/Files/ml_signals_tb.csv                               |
//|       (откуда: API/generate_signals.py --task triple_barrier)    |
//|   Формат CSV:                                                    |
//|     time;signal;sl_atr;tp_atr;prob;ev                            |
//|     2023.01.03 04:00;1;2.0;6.0;0.73;3.42                        |
//|   signal: 1 (BUY), -1 (SELL), 0 (FLAT)                          |
//|   sl_atr/tp_atr: SL/TP в единицах ATR (фиксированные)           |
//+------------------------------------------------------------------+
#property strict

// ─── Настройки ──────────────────────────────────────────────────────

#define TB_SIGNALS_FILE  "ml_signals_tb.csv"
#define TB_MAX_SIGNALS   200000
#define TB_Ver   1.0

// ─── Диагностические счётчики ─────────────────────────────────────

int TB_cnt_total    = 0;  // всего TB-сигналов (sig!=0) в диапазоне теста
int TB_cnt_trend    = 0;  // заблокировано трендовым фильтром
int TB_cnt_posblock = 0;  // заблокировано открытой позицией
int TB_cnt_executed = 0;  // выставлено ордеров
int TB_cnt_buy      = 0;
int TB_cnt_sell     = 0;

// ─── Хранилище сигналов ─────────────────────────────────────────────

int      TB_SignalCount = 0;
datetime TB_Times[];
char     TB_Signals[];
float    TB_SL[];
float    TB_TP[];
float    TB_Prob[];
float    TB_EV[];

// ─── Инициализация: загрузка CSV ────────────────────────────────────

bool TB_INIT() {
   int handle = FileOpen(TB_SIGNALS_FILE, FILE_READ | FILE_CSV | FILE_ANSI, ';');
   if (handle < 0) {
      Print("TB_INIT: Cannot open ", TB_SIGNALS_FILE, " Error=", GetLastError());
      return false;
   }

   // Пропускаем заголовок
   FileReadString(handle); // time
   FileReadString(handle); // signal
   FileReadString(handle); // sl_atr
   FileReadString(handle); // tp_atr
   FileReadString(handle); // prob
   FileReadString(handle); // ev

   // Предварительное выделение памяти
   ArrayResize(TB_Times,   TB_MAX_SIGNALS);
   ArrayResize(TB_Signals, TB_MAX_SIGNALS);
   ArrayResize(TB_SL,      TB_MAX_SIGNALS);
   ArrayResize(TB_TP,      TB_MAX_SIGNALS);
   ArrayResize(TB_Prob,    TB_MAX_SIGNALS);
   ArrayResize(TB_EV,      TB_MAX_SIGNALS);

   TB_SignalCount = 0;

   while (!FileIsEnding(handle) && TB_SignalCount < TB_MAX_SIGNALS) {
      string time_str = FileReadString(handle);
      if (time_str == "") break;

      TB_Times[TB_SignalCount]   = StringToTime(time_str);
      TB_Signals[TB_SignalCount] = (char)StringToInteger(FileReadString(handle));
      TB_SL[TB_SignalCount]      = (float)StringToDouble(FileReadString(handle));
      TB_TP[TB_SignalCount]      = (float)StringToDouble(FileReadString(handle));
      TB_Prob[TB_SignalCount]    = (float)StringToDouble(FileReadString(handle));
      TB_EV[TB_SignalCount]      = (float)StringToDouble(FileReadString(handle));

      TB_SignalCount++;
   }

   FileClose(handle);

   // Обрезаем массивы до реального размера
   ArrayResize(TB_Times,   TB_SignalCount);
   ArrayResize(TB_Signals, TB_SignalCount);
   ArrayResize(TB_SL,      TB_SignalCount);
   ArrayResize(TB_TP,      TB_SignalCount);
   ArrayResize(TB_Prob,    TB_SignalCount);
   ArrayResize(TB_EV,      TB_SignalCount);

   Print("TB_INIT: Loaded V", TB_Ver, " ", TB_SignalCount, " signals from ", TB_SIGNALS_FILE,
         "  Range: ", TimeToString(TB_Times[0]), " — ", TimeToString(TB_Times[TB_SignalCount-1]));

   return true;
}

// ─── Бинарный поиск сигнала по времени ──────────────────────────────

int TB_FindSignal(datetime barTime) {
   int lo = 0, hi = TB_SignalCount - 1;

   while (lo <= hi) {
      int mid = (lo + hi) / 2;
      if (TB_Times[mid] == barTime) return mid;
      else if (TB_Times[mid] < barTime) lo = mid + 1;
      else hi = mid - 1;
   }

   return -1;
}

// ─── Торговая функция (вызывается из INPUT) ─────────────────────────

void EXPERT::ML_TRADE_TB() {
   // Ленивая инициализация: загрузка CSV при первом вызове
   static bool tb_loaded = false;
   if (!tb_loaded) {
      tb_loaded = true;
      TB_INIT();
   }
   if (TB_SignalCount <= 0) return;

   int idx = TB_FindSignal(Time[bar]);
   if (idx < 0) return;

   char sig = TB_Signals[idx];
   if (sig == 0) return;

   TB_cnt_total++;

   // ─── Трендовый фильтр (диагностика + опциональный bypass) ───
   if (sig == 1 && !UP) {
      TB_cnt_trend++;
      if (!ML_BypassTrend) return;
      UP = 1;  // bypass: разрешаем BUY против тренда
   }
   if (sig == -1 && !DN) {
      TB_cnt_trend++;
      if (!ML_BypassTrend) return;
      DN = 1;  // bypass: разрешаем SELL против тренда
   }

   // ─── SL/TP из CSV (в ATR-единицах → абсолютные) ───
   float sl_dist = TB_SL[idx] * ATR;
   float tp_dist = TB_TP[idx] * ATR;

    int tb_buy_cnt = 0, tb_sel_cnt = 0;
    for (int tb_i = 0; tb_i < PosCount; tb_i++) {
       if (!Pos[tb_i].active || Pos[tb_i].data.Typ == NONE) continue;
       if (!PositionSelectByTicket(Pos[tb_i].ticket)) continue;
       ENUM_POSITION_TYPE tb_pt = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
       if (tb_pt == POSITION_TYPE_BUY)  tb_buy_cnt++;
       if (tb_pt == POSITION_TYPE_SELL) tb_sel_cnt++;
    }
    bool tb_buy_open = (MT5_MaxPositions==1 ? (BUY.Typ == NONE) : (tb_buy_cnt < MT5_MaxPositions));
    if (sig == 1 && tb_buy_open) {
       if (MT5_MaxPositions == 1) {
          if (SEL.Typ != NONE) {
             CLOSE_SEL(1, "TB_Reversal");
          }
       } else if (tb_sel_cnt > 0) {
          int tb_earliest = -1; datetime tb_min_T = 0;
          for (int tb_i = 0; tb_i < PosCount; tb_i++) {
             if (!Pos[tb_i].active || Pos[tb_i].data.Typ != MARKET) continue;
             if (!PositionSelectByTicket(Pos[tb_i].ticket)) continue;
             if ((ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_SELL &&
                 (tb_earliest < 0 || Pos[tb_i].data.T < tb_min_T)) {
                tb_earliest = tb_i; tb_min_T = Pos[tb_i].data.T;
             }
          }
          if (tb_earliest >= 0) {
             X("TB_Reversal_pos" + S0(tb_earliest) + " close earliest SELL",
               Pos[tb_earliest].data.Val, bar - 1, clrRed);
             Pos[tb_earliest].data.Val = 0;
          }
       }
       TB_cnt_executed++; TB_cnt_buy++;

      set.BUY.Sig=GOGO;
      set.BUY.Val=(float)Ask+DELTA(D);
      set.BUY.Stp=set.BUY.Val-sl_dist;
      set.BUY.Prf=set.BUY.Val+tp_dist;
      Print(Mgc,":: TB BUY"
            " prob=",  DoubleToString(TB_Prob[idx],3),
            " ev=",    DoubleToString(TB_EV[idx],2),
            " SL=",    DoubleToString(TB_SL[idx],1), "ATR"
            " TP=",    DoubleToString(TB_TP[idx],1), "ATR"
            " Val=",   DoubleToString(set.BUY.Val,Digits),
            " Stp=",   DoubleToString(set.BUY.Stp,Digits),
            " Prf=",   DoubleToString(set.BUY.Prf,Digits),
            " ATR=",   DoubleToString(ATR,Digits),
            " bar=",   TimeToString(Time[bar]));
   }
    bool tb_sell_open = (MT5_MaxPositions==1 ? (SEL.Typ == NONE) : (tb_sel_cnt < MT5_MaxPositions));
    if (sig == -1 && tb_sell_open) {
       if (MT5_MaxPositions == 1) {
          if (BUY.Typ != NONE) {
             CLOSE_BUY(1, "TB_Reversal");
          }
       } else if (tb_buy_cnt > 0) {
          int tb_earliest = -1; datetime tb_min_T = 0;
          for (int tb_i = 0; tb_i < PosCount; tb_i++) {
             if (!Pos[tb_i].active || Pos[tb_i].data.Typ != MARKET) continue;
             if (!PositionSelectByTicket(Pos[tb_i].ticket)) continue;
             if ((ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY &&
                 (tb_earliest < 0 || Pos[tb_i].data.T < tb_min_T)) {
                tb_earliest = tb_i; tb_min_T = Pos[tb_i].data.T;
             }
          }
          if (tb_earliest >= 0) {
             X("TB_Reversal_pos" + S0(tb_earliest) + " close earliest BUY",
               Pos[tb_earliest].data.Val, bar - 1, clrRed);
             Pos[tb_earliest].data.Val = 0;
          }
       }
       TB_cnt_executed++; TB_cnt_sell++;

      set.SEL.Sig=GOGO;
      set.SEL.Val=(float)Bid-DELTA(D);
      set.SEL.Stp=set.SEL.Val+sl_dist;
      set.SEL.Prf=set.SEL.Val-tp_dist;
      Print(Mgc,":: TB SELL"
            " prob=",  DoubleToString(TB_Prob[idx],3),
            " ev=",    DoubleToString(TB_EV[idx],2),
            " SL=",    DoubleToString(TB_SL[idx],1), "ATR"
            " TP=",    DoubleToString(TB_TP[idx],1), "ATR"
            " Val=",   DoubleToString(set.SEL.Val,Digits),
            " Stp=",   DoubleToString(set.SEL.Stp,Digits),
            " Prf=",   DoubleToString(set.SEL.Prf,Digits),
            " ATR=",   DoubleToString(ATR,Digits),
            " bar=",   TimeToString(Time[bar]));
   }
   else {
      TB_cnt_posblock++;
      Print(Mgc,":: TB SKIP reason=PosBlock"
            " sig=",    sig,
            " BUY.Typ=",BUY.Typ," SEL.Typ=",SEL.Typ,
            " bar=",    TimeToString(Time[bar]));
   }
}

// ─── Диагностический отчёт (вызывается из OnTester) ─────────────────

void TB_DIAG_PRINT() {
   Print("=== TB DIAGNOSTICS ===");
   Print("  Total signals:    ", TB_cnt_total);
   Print("  Trend blocked:    ", TB_cnt_trend,
         "  (", TB_cnt_total>0 ? DoubleToString(100.0*TB_cnt_trend/TB_cnt_total,1) : "0", "%)");
   Print("  Position blocked: ", TB_cnt_posblock,
         "  (", TB_cnt_total>0 ? DoubleToString(100.0*TB_cnt_posblock/TB_cnt_total,1) : "0", "%)");
   Print("  Executed:         ", TB_cnt_executed,
         "  (BUY=",TB_cnt_buy," SELL=",TB_cnt_sell,")");
   Print("======================");
}
