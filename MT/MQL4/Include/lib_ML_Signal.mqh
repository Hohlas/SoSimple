//+------------------------------------------------------------------+
//| lib_ML_Signal.mqh                                 v4.0           |
//| Назначение: Прямое исполнение ML-сигналов для parity-check        |
//|             без старого INPUT/OUTPUT контура                      |
//| Автор: SoSimple                                                  |
//| Обновлён: 2026-04-09                                             |
//| Входные данные:                                                  |
//|   - MQL4/Files/ml_signals.csv                                    |
//| Поддерживаемые форматы CSV:                                      |
//|   - time;signal                                                  |
//|   - time;signal;...;pred_ret_24_dir_atr;...                      |
//| Логика:                                                          |
//|   - сигнал на баре t -> вход по рынку на следующем баре          |
//|   - одна открытая позиция                                        |
//|   - закрытие по удержанию либо по обратному сигналу              |
//+------------------------------------------------------------------+
#property strict

#define MLP_SIGNALS_FILE "ml_signals.csv"
#define MLP_MAX_SIGNALS  200000
#define MLP_Ver          4.0

int      MLP_SignalCount = 0;
datetime MLP_Times[];
char     MLP_Signals[];
float    MLP_Scores[];
bool     MLP_HasScoreColumn = false;

datetime MLP_BuySignalTime = 0;
datetime MLP_SellSignalTime = 0;
double   MLP_BuyScore = 0.0;
double   MLP_SellScore = 0.0;

int MLP_cnt_total    = 0;
int MLP_cnt_filtered = 0;
int MLP_cnt_posblock = 0;
int MLP_cnt_opened   = 0;
int MLP_cnt_buy      = 0;
int MLP_cnt_sell     = 0;
int MLP_cnt_timeout  = 0;
int MLP_cnt_reverse  = 0;

bool MLP_PassScore(int idx) {
   if (!ML_UseScoreFilter || !MLP_HasScoreColumn) return true;
   return MLP_Scores[idx] >= ML_ScoreThreshold;
}

int MLP_FindSignal(datetime barTime) {
   int lo = 0;
   int hi = MLP_SignalCount - 1;

   while (lo <= hi) {
      int mid = (lo + hi) / 2;
      if (MLP_Times[mid] == barTime) return mid;
      if (MLP_Times[mid] < barTime) lo = mid + 1;
      else hi = mid - 1;
   }

   return -1;
}

bool MLP_INIT() {
   int handle = FileOpen(MLP_SIGNALS_FILE, FILE_READ | FILE_CSV | FILE_ANSI, ';');
   if (handle < 0) {
      Print("MLP_INIT: Cannot open ", MLP_SIGNALS_FILE, " Error=", GetLastError());
      return false;
   }

   string header_time = FileReadString(handle);
   string header_signal = FileReadString(handle);
   if (header_time != "time" || header_signal != "signal") {
      Print("MLP_INIT: Unexpected header in ", MLP_SIGNALS_FILE,
            " first=", header_time, " second=", header_signal);
      FileClose(handle);
      return false;
   }

   MLP_HasScoreColumn = false;
   string col3 = "";
   string col4 = "";
   string col5 = "";
   if (!FileIsLineEnding(handle)) col3 = FileReadString(handle);
   if (!FileIsLineEnding(handle)) col4 = FileReadString(handle);
   if (!FileIsLineEnding(handle)) col5 = FileReadString(handle);
   if (col5 == "pred_ret_24_dir_atr") MLP_HasScoreColumn = true;
   while (!FileIsLineEnding(handle)) FileReadString(handle);

   ArrayResize(MLP_Times, MLP_MAX_SIGNALS);
   ArrayResize(MLP_Signals, MLP_MAX_SIGNALS);
   ArrayResize(MLP_Scores, MLP_MAX_SIGNALS);
   MLP_SignalCount = 0;

   while (!FileIsEnding(handle) && MLP_SignalCount < MLP_MAX_SIGNALS) {
      string time_str = FileReadString(handle);
      if (time_str == "") {
         while (!FileIsEnding(handle) && !FileIsLineEnding(handle)) FileReadString(handle);
         continue;
      }

      string sig_str = FileReadString(handle);
      datetime parsed_time = StringToTime(time_str);
      char parsed_signal = (char)StringToInteger(sig_str);
      double parsed_score = 0.0;

      if (!FileIsLineEnding(handle)) FileReadString(handle);
      if (!FileIsLineEnding(handle)) FileReadString(handle);
      if (!FileIsLineEnding(handle)) {
         string value5 = FileReadString(handle);
         if (MLP_HasScoreColumn) parsed_score = StringToDouble(value5);
      }
      while (!FileIsLineEnding(handle)) FileReadString(handle);

      if (MLP_SignalCount > 0 && MLP_Times[MLP_SignalCount - 1] == parsed_time) {
         MLP_Signals[MLP_SignalCount - 1] = parsed_signal;
         MLP_Scores[MLP_SignalCount - 1] = (float)parsed_score;
         continue;
      }

      MLP_Times[MLP_SignalCount] = parsed_time;
      MLP_Signals[MLP_SignalCount] = parsed_signal;
      MLP_Scores[MLP_SignalCount] = (float)parsed_score;
      MLP_SignalCount++;
   }

   FileClose(handle);

   ArrayResize(MLP_Times, MLP_SignalCount);
   ArrayResize(MLP_Signals, MLP_SignalCount);
   ArrayResize(MLP_Scores, MLP_SignalCount);

   if (MLP_SignalCount <= 0) {
      Print("MLP_INIT: Loaded 0 rows from ", MLP_SIGNALS_FILE);
      return true;
   }

   Print("MLP_INIT: Loaded V", MLP_Ver, " ", MLP_SignalCount, " rows from ", MLP_SIGNALS_FILE,
         " Range: ", TimeToString(MLP_Times[0]), " — ", TimeToString(MLP_Times[MLP_SignalCount - 1]),
         " ScoreCol=", MLP_HasScoreColumn,
         " ScoreFilter=", ML_UseScoreFilter,
         " Threshold=", DoubleToString(ML_ScoreThreshold, 6),
         " HoldBars=", ML_HoldBars,
         " Reversal=", ML_AllowReversal);
   if (ML_UseScoreFilter && !MLP_HasScoreColumn) {
      Print("MLP_INIT: pred_ret_24_dir_atr column not found, score filter disabled for this file.");
   }

   return true;
}

void EXPERT::ML_TRADE() {
   static bool ml_loaded = false;
   if (!ml_loaded) {
      ml_loaded = true;
      MLP_INIT();
   }
   if (MLP_SignalCount <= 0) return;

   set.BUY.Sig = NONE;
   set.SEL.Sig = NONE;
   set.BUY.Val = 0;
   set.BUY.Stp = 0;
   set.BUY.Prf = 0;
   set.SEL.Val = 0;
   set.SEL.Stp = 0;
   set.SEL.Prf = 0;

   int idx = MLP_FindSignal(Time[bar]);
   char sig = 0;
   double score = 0.0;
   bool score_ok = true;

   if (idx >= 0) {
      sig = MLP_Signals[idx];
      score = MLP_Scores[idx];
      score_ok = MLP_PassScore(idx);
      if (sig != 0) MLP_cnt_total++;
   }

   if (BUY.Typ == MARKET) {
      if (ML_HoldBars > 0 && SHIFT(BUY.T) >= ML_HoldBars) {
         double exit_price = BID;
         double pnl_atr = 0.0;
         if (ATR > 0) pnl_atr = (exit_price - BUY.Val) / ATR;
         MLP_cnt_timeout++;
         Print(Mgc, ":: MLP CLOSE BUY"
               " reason=Timeout"
               " signal_time=", TimeToString(MLP_BuySignalTime),
               " entry_time=", TimeToString(BUY.T),
               " exit_time=", TimeToString(Time[0]),
               " hold_bars=", SHIFT(BUY.T),
               " entry=", DoubleToString(BUY.Val, Digits),
               " exit=", DoubleToString(exit_price, Digits),
               " atr=", DoubleToString(ATR, Digits),
               " pnl_atr=", DoubleToString(pnl_atr, 4),
               " score=", DoubleToString(MLP_BuyScore, 6));
         CLOSE_BUY(1, "MLP_Timeout");
         MLP_BuySignalTime = 0;
         MLP_BuyScore = 0.0;
         return;
      }
      if (sig == -1 && score_ok && ML_AllowReversal) {
         double exit_price = BID;
         double pnl_atr = 0.0;
         if (ATR > 0) pnl_atr = (exit_price - BUY.Val) / ATR;
         MLP_cnt_reverse++;
         Print(Mgc, ":: MLP CLOSE BUY"
               " reason=ReverseSignal"
               " signal_time=", TimeToString(MLP_BuySignalTime),
               " reverse_time=", TimeToString(MLP_Times[idx]),
               " entry_time=", TimeToString(BUY.T),
               " exit_time=", TimeToString(Time[0]),
               " entry=", DoubleToString(BUY.Val, Digits),
               " exit=", DoubleToString(exit_price, Digits),
               " atr=", DoubleToString(ATR, Digits),
               " pnl_atr=", DoubleToString(pnl_atr, 4),
               " score=", DoubleToString(MLP_BuyScore, 6),
               " reverse_score=", DoubleToString(score, 6));
         CLOSE_BUY(1, "MLP_ReverseSignal");
         MLP_BuySignalTime = 0;
         MLP_BuyScore = 0.0;
         return;
      }
      if (sig != 0 && score_ok) {
         MLP_cnt_posblock++;
         Print(Mgc, ":: MLP SKIP reason=PosBlock"
               " sig=", sig,
               " signal_time=", TimeToString(MLP_Times[idx]),
               " score=", DoubleToString(score, 6),
               " open=BUY");
      }
      return;
   }

   if (SEL.Typ == MARKET) {
      if (ML_HoldBars > 0 && SHIFT(SEL.T) >= ML_HoldBars) {
         double exit_price = ASK;
         double pnl_atr = 0.0;
         if (ATR > 0) pnl_atr = (SEL.Val - exit_price) / ATR;
         MLP_cnt_timeout++;
         Print(Mgc, ":: MLP CLOSE SELL"
               " reason=Timeout"
               " signal_time=", TimeToString(MLP_SellSignalTime),
               " entry_time=", TimeToString(SEL.T),
               " exit_time=", TimeToString(Time[0]),
               " hold_bars=", SHIFT(SEL.T),
               " entry=", DoubleToString(SEL.Val, Digits),
               " exit=", DoubleToString(exit_price, Digits),
               " atr=", DoubleToString(ATR, Digits),
               " pnl_atr=", DoubleToString(pnl_atr, 4),
               " score=", DoubleToString(MLP_SellScore, 6));
         CLOSE_SEL(1, "MLP_Timeout");
         MLP_SellSignalTime = 0;
         MLP_SellScore = 0.0;
         return;
      }
      if (sig == 1 && score_ok && ML_AllowReversal) {
         double exit_price = ASK;
         double pnl_atr = 0.0;
         if (ATR > 0) pnl_atr = (SEL.Val - exit_price) / ATR;
         MLP_cnt_reverse++;
         Print(Mgc, ":: MLP CLOSE SELL"
               " reason=ReverseSignal"
               " signal_time=", TimeToString(MLP_SellSignalTime),
               " reverse_time=", TimeToString(MLP_Times[idx]),
               " entry_time=", TimeToString(SEL.T),
               " exit_time=", TimeToString(Time[0]),
               " entry=", DoubleToString(SEL.Val, Digits),
               " exit=", DoubleToString(exit_price, Digits),
               " atr=", DoubleToString(ATR, Digits),
               " pnl_atr=", DoubleToString(pnl_atr, 4),
               " score=", DoubleToString(MLP_SellScore, 6),
               " reverse_score=", DoubleToString(score, 6));
         CLOSE_SEL(1, "MLP_ReverseSignal");
         MLP_SellSignalTime = 0;
         MLP_SellScore = 0.0;
         return;
      }
      if (sig != 0 && score_ok) {
         MLP_cnt_posblock++;
         Print(Mgc, ":: MLP SKIP reason=PosBlock"
               " sig=", sig,
               " signal_time=", TimeToString(MLP_Times[idx]),
               " score=", DoubleToString(score, 6),
               " open=SELL");
      }
      return;
   }

   if (BUY.Typ != NONE || SEL.Typ != NONE) {
      if (sig != 0 && score_ok) {
         MLP_cnt_posblock++;
         Print(Mgc, ":: MLP SKIP reason=PosBlock"
               " sig=", sig,
               " signal_time=", TimeToString(MLP_Times[idx]),
               " score=", DoubleToString(score, 6),
               " open=pending");
      }
      return;
   }

   if (idx < 0 || sig == 0) return;

   if (!score_ok) {
      MLP_cnt_filtered++;
      Print(Mgc, ":: MLP SKIP reason=ScoreFilter"
            " sig=", sig,
            " signal_time=", TimeToString(MLP_Times[idx]),
            " score=", DoubleToString(score, 6),
            " threshold=", DoubleToString(ML_ScoreThreshold, 6));
      return;
   }

   if (sig == 1) {
      float back_stop = (float)MathMax(ATR * ML_BackStopATR, StopLevel * 2.0);
      float min_price = (float)MarketInfo(Symbol(), MODE_POINT);
      MLP_cnt_opened++;
      MLP_cnt_buy++;
      MLP_BuySignalTime = MLP_Times[idx];
      MLP_BuyScore = score;
      MLP_SellSignalTime = 0;
      MLP_SellScore = 0.0;

      set.BUY.Sig = GOGO;
      set.BUY.Val = (float)ASK;
      set.BUY.Stp = (float)MathMax(min_price, set.BUY.Val - back_stop);
      set.BUY.Prf = 0;

      Print(Mgc, ":: MLP BUY"
            " signal_time=", TimeToString(MLP_BuySignalTime),
            " entry_time=", TimeToString(Time[0]),
            " score=", DoubleToString(score, 6),
            " Val=", DoubleToString(set.BUY.Val, Digits));
      return;
   }

   if (sig == -1) {
      float back_stop = (float)MathMax(ATR * ML_BackStopATR, StopLevel * 2.0);
      MLP_cnt_opened++;
      MLP_cnt_sell++;
      MLP_SellSignalTime = MLP_Times[idx];
      MLP_SellScore = score;
      MLP_BuySignalTime = 0;
      MLP_BuyScore = 0.0;

      set.SEL.Sig = GOGO;
      set.SEL.Val = (float)BID;
      set.SEL.Stp = set.SEL.Val + back_stop;
      set.SEL.Prf = 0;

      Print(Mgc, ":: MLP SELL"
            " signal_time=", TimeToString(MLP_SellSignalTime),
            " entry_time=", TimeToString(Time[0]),
            " score=", DoubleToString(score, 6),
            " Val=", DoubleToString(set.SEL.Val, Digits));
   }
}

void ML_DIAG_PRINT() {
   Print("=== MLP DIAGNOSTICS ===");
   Print("  Total signals:    ", MLP_cnt_total);
   Print("  Score filtered:   ", MLP_cnt_filtered,
         "  (", MLP_cnt_total > 0 ? DoubleToString(100.0 * MLP_cnt_filtered / MLP_cnt_total, 1) : "0", "%)");
   Print("  Position blocked: ", MLP_cnt_posblock,
         "  (", MLP_cnt_total > 0 ? DoubleToString(100.0 * MLP_cnt_posblock / MLP_cnt_total, 1) : "0", "%)");
   Print("  Opened:           ", MLP_cnt_opened,
         "  (BUY=", MLP_cnt_buy, " SELL=", MLP_cnt_sell, ")");
   Print("  Timeout closes:   ", MLP_cnt_timeout);
   Print("  Reverse closes:   ", MLP_cnt_reverse);
   Print("  HoldBars=", ML_HoldBars,
         "  ScoreFilter=", ML_UseScoreFilter,
         "  Threshold=", DoubleToString(ML_ScoreThreshold, 6),
         "  Reversal=", ML_AllowReversal,
         "  ScoreCol=", MLP_HasScoreColumn);
   Print("======================");
}
