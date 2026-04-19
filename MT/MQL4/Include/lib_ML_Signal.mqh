//+------------------------------------------------------------------+
//| lib_ML_Signal.mqh                                 v4.1           |
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
//|   - одна или несколько открытых позиций, если ML_MaxPositions > 1|
//|   - режим 0: закрытие по удержанию либо по обратному сигналу     |
//|   - режим 1: отдельный bar-based trailing-stop по X*ATR          |
//+------------------------------------------------------------------+
#property strict

#define MLP_SIGNALS_FILE "ml_signals.csv"
#define MLP_MAX_SIGNALS  200000
#define MLP_Ver          4.1
#define MLP_EXIT_TIMEOUT 0
#define MLP_EXIT_TRAIL   1

int      MLP_SignalCount = 0;
datetime MLP_Times[];
char     MLP_Signals[];
float    MLP_Scores[];
bool     MLP_HasScoreColumn = false;

datetime MLP_BuySignalTime = 0;
datetime MLP_SellSignalTime = 0;
double   MLP_BuyScore = 0.0;
double   MLP_SellScore = 0.0;
double   MLP_BuyBestPrice = 0.0;
double   MLP_SellBestPrice = 0.0;

int MLP_cnt_total    = 0;
int MLP_cnt_filtered = 0;
int MLP_cnt_posblock = 0;
int MLP_cnt_opened   = 0;
int MLP_cnt_buy      = 0;
int MLP_cnt_sell     = 0;
int MLP_cnt_timeout  = 0;
int MLP_cnt_trailing = 0;
int MLP_cnt_reverse  = 0;

string MLP_ExitModeName() {
   if (ML_ExitMode == MLP_EXIT_TRAIL) return "trailing_stop";
   return "timeout";
}

void MLP_ResetBuyState() {
   MLP_BuySignalTime = 0;
   MLP_BuyScore = 0.0;
   MLP_BuyBestPrice = 0.0;
}

void MLP_ResetSellState() {
   MLP_SellSignalTime = 0;
   MLP_SellScore = 0.0;
   MLP_SellBestPrice = 0.0;
}

bool MLP_PassScore(int idx) {
   if (!ML_UseScoreFilter || !MLP_HasScoreColumn) return true;
   return MLP_Scores[idx] >= ML_ScoreThreshold;
}

bool MLP_IsOwnMarketOrder(int magic, string sym) {
   if (OrderMagicNumber() != magic) return false;
   if (OrderSymbol() != sym) return false;
   int typ = OrderType();
   return (typ == OP_BUY || typ == OP_SELL);
}

int MLP_CountOwnMarketOrders(int magic, string sym) {
   int count = 0;
   for (int i = 0; i < OrdersTotal(); i++) {
      if (!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if (MLP_IsOwnMarketOrder(magic, sym)) count++;
   }
   return count;
}

double MLP_BestBuySince(datetime open_time, double entry_price) {
   double best = entry_price;
   int start_shift = iBarShift(Symbol(), Period(), open_time, false);
   if (start_shift < bar) start_shift = bar;
   if (start_shift >= Bars) start_shift = Bars - 1;

   for (int s = start_shift; s >= bar; s--) {
      if (High[s] > best) best = High[s];
   }
   return best;
}

double MLP_BestSellSince(datetime open_time, double entry_price) {
   double best = entry_price;
   int start_shift = iBarShift(Symbol(), Period(), open_time, false);
   if (start_shift < bar) start_shift = bar;
   if (start_shift >= Bars) start_shift = Bars - 1;

   for (int s = start_shift; s >= bar; s--) {
      if (Low[s] < best) best = Low[s];
   }
   return best;
}

bool MLP_CloseSelectedOrder(int magic, uchar exp_num, double atr_value, string reason, double best_price, double trail_price) {
   int ticket = OrderTicket();
   int typ = OrderType();
   double lots = OrderLots();
   double entry_price = OrderOpenPrice();
   datetime entry_time = OrderOpenTime();
   bool ok = false;

   WAITING(magic, "Terminal", 20);
   for (int repeat = 3; repeat > 0 && !ok; repeat--) {
      RefreshRates();
      double close_price = (typ == OP_BUY) ? Bid : Ask;
      ok = OrderClose(ticket, lots, close_price, 3, clrRed);
      if (ok) break;
      if (!ERROR_CHECK("MLP_Close Ticket=" + S0(ticket), exp_num)) break;
   }
   FREE(magic, "Terminal");

   RefreshRates();
   double exit_price = (typ == OP_BUY) ? Bid : Ask;
   double pnl_atr = 0.0;
   if (atr_value > 0) {
      if (typ == OP_BUY) pnl_atr = (exit_price - entry_price) / atr_value;
      else pnl_atr = (entry_price - exit_price) / atr_value;
   }

   if (ok) {
      if (reason == "TrailingStop") MLP_cnt_trailing++;
      else if (reason == "Timeout") MLP_cnt_timeout++;
      else if (reason == "ReverseSignal") MLP_cnt_reverse++;
      Print(magic, ":: MLP CLOSE ", (typ == OP_BUY ? "BUY" : "SELL"),
            " reason=", reason,
            " ticket=", ticket,
            " entry_time=", TimeToString(entry_time),
            " exit_time=", TimeToString(Time[0]),
            " entry=", DoubleToString(entry_price, Digits),
            " best=", DoubleToString(best_price, Digits),
            " trail=", DoubleToString(trail_price, Digits),
            " exit=", DoubleToString(exit_price, Digits),
            " atr=", DoubleToString(atr_value, Digits),
            " trail_atr=", DoubleToString(ML_TrailATR, 2),
            " pnl_atr=", DoubleToString(pnl_atr, 4));
   }
   return ok;
}

void MLP_ManageMultiPositions(int magic, uchar exp_num, string sym, double atr_value) {
   if (atr_value <= 0) return;

   for (int i = OrdersTotal() - 1; i >= 0; i--) {
      if (!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if (!MLP_IsOwnMarketOrder(magic, sym)) continue;

      int typ = OrderType();
      double entry_price = OrderOpenPrice();
      double best_price = entry_price;
      double trail_price = entry_price;
      bool should_close = false;
      string close_reason = "";

      if (ML_ExitMode == MLP_EXIT_TIMEOUT && ML_HoldBars > 0 && SHIFT(OrderOpenTime()) >= ML_HoldBars) {
         should_close = true;
         close_reason = "Timeout";
      }
      else if (ML_ExitMode == MLP_EXIT_TRAIL && ML_TrailATR > 0 && typ == OP_BUY) {
         best_price = MLP_BestBuySince(OrderOpenTime(), entry_price);
         trail_price = best_price - atr_value * ML_TrailATR;
         should_close = (Bid <= trail_price);
         if (should_close) close_reason = "TrailingStop";
      }
      else if (ML_ExitMode == MLP_EXIT_TRAIL && ML_TrailATR > 0 && typ == OP_SELL) {
         best_price = MLP_BestSellSince(OrderOpenTime(), entry_price);
         trail_price = best_price + atr_value * ML_TrailATR;
         should_close = (Ask >= trail_price);
         if (should_close) close_reason = "TrailingStop";
      }

      if (should_close) {
         MLP_CloseSelectedOrder(magic, exp_num, atr_value, close_reason, best_price, trail_price);
      }
   }
}

bool MLP_OpenMarketOrder(int magic, uchar exp_num, string sym, int sig, double score, datetime signal_time, double atr_value) {
   if (atr_value <= 0) return false;
   if (sig != 1 && sig != -1) return false;

   RefreshRates();
   double back_stop = MathMax(atr_value * ML_BackStopATR, StopLevel * 2.0);
   double min_price = MarketInfo(sym, MODE_POINT);
   double lot_to_send = Lot;
   if (Risk == 0 || IsTesting()) lot_to_send = 0.1;
   else lot_to_send = MM((float)back_stop, CurExp);
   lot_to_send = NormalizeDouble(lot_to_send, LotDigits);
   if (lot_to_send <= 0) return false;

   int order_type = (sig == 1) ? OP_BUY : OP_SELL;
   double entry_price = (sig == 1) ? Ask : Bid;
   double stop_price = (sig == 1)
      ? MathMax(min_price, entry_price - back_stop)
      : entry_price + back_stop;

   if (Real && Risk > 0) {
      double trade_risk = CHECK_RISK(lot_to_send, back_stop, sym);
      if (trade_risk > MaxRisk) {
         REPORT(exp_num, "MLP risk too big: " + S2(trade_risk) + "% Lot=" + S2(lot_to_send));
         return false;
      }
   }

   int ticket = -1;
   bool ok = false;
   WAITING(magic, "Terminal", 20);
   for (int repeat = 3; repeat > 0 && !ok; repeat--) {
      RefreshRates();
      entry_price = (sig == 1) ? Ask : Bid;
      stop_price = (sig == 1)
         ? MathMax(min_price, entry_price - back_stop)
         : entry_price + back_stop;
      ticket = OrderSend(sym, order_type, lot_to_send, N5(entry_price, sym), 3,
                         N5(stop_price, sym), 0, S0(magic) + "-MLP", magic, 0,
                         (sig == 1 ? clrGreen : clrRed));
      ok = (ticket > 0);
      if (ok) break;
      if (!ERROR_CHECK("MLP_OpenMarketOrder", exp_num)) break;
   }
   FREE(magic, "Terminal");

   if (ok) {
      MLP_cnt_opened++;
      if (sig == 1) MLP_cnt_buy++;
      else MLP_cnt_sell++;
      Print(magic, ":: MLP ", (sig == 1 ? "BUY" : "SELL"),
            " mode=multi_position",
            " ticket=", ticket,
            " signal_time=", TimeToString(signal_time),
            " entry_time=", TimeToString(Time[0]),
            " score=", DoubleToString(score, 6),
            " exit_mode=", MLP_ExitModeName(),
            " TrailATR=", DoubleToString(ML_TrailATR, 2),
            " MaxPositions=", ML_MaxPositions,
            " Val=", DoubleToString(entry_price, Digits),
            " Stp=", DoubleToString(stop_price, Digits),
            " Lot=", DoubleToString(lot_to_send, 2));
   }
   return ok;
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
         " ExitMode=", MLP_ExitModeName(),
         " TrailATR=", DoubleToString(ML_TrailATR, 2),
         " MaxPositions=", ML_MaxPositions,
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

   if (ML_MaxPositions > 1) {
      MLP_ManageMultiPositions(Mgc, ExpNum, Sym, ATR);

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

      int open_positions = MLP_CountOwnMarketOrders(Mgc, Sym);
      if (open_positions >= ML_MaxPositions) {
         MLP_cnt_posblock++;
         Print(Mgc, ":: MLP SKIP reason=MaxPositions"
               " sig=", sig,
               " signal_time=", TimeToString(MLP_Times[idx]),
               " score=", DoubleToString(score, 6),
               " open_positions=", open_positions,
               " max_positions=", ML_MaxPositions);
         return;
      }

      MLP_OpenMarketOrder(Mgc, ExpNum, Sym, sig, score, MLP_Times[idx], ATR);
      return;
   }

   if (BUY.Typ == MARKET) {
      if (ML_ExitMode == MLP_EXIT_TRAIL) {
         double best_price = 0.0;
         double trail_price = 0.0;
         double pnl_atr = 0.0;
         bool close_trailing = false;
         if (ML_TrailATR > 0 && ATR > 0) {
            if (MLP_BuyBestPrice <= 0.0 || MLP_BuyBestPrice < BUY.Val) MLP_BuyBestPrice = BUY.Val;
            if (High[bar] > MLP_BuyBestPrice) MLP_BuyBestPrice = High[bar];
            best_price = MLP_BuyBestPrice;
            trail_price = best_price - ATR * ML_TrailATR;
            pnl_atr = (BID - BUY.Val) / ATR;
            close_trailing = (BID <= trail_price);
         }
         if (close_trailing) {
            double exit_price = BID;
            MLP_cnt_trailing++;
            Print(Mgc, ":: MLP CLOSE BUY"
                  " reason=TrailingStop"
                  " signal_time=", TimeToString(MLP_BuySignalTime),
                  " entry_time=", TimeToString(BUY.T),
                  " exit_time=", TimeToString(Time[0]),
                  " entry=", DoubleToString(BUY.Val, Digits),
                  " best=", DoubleToString(best_price, Digits),
                  " trail=", DoubleToString(trail_price, Digits),
                  " exit=", DoubleToString(exit_price, Digits),
                  " atr=", DoubleToString(ATR, Digits),
                  " trail_atr=", DoubleToString(ML_TrailATR, 2),
                  " pnl_atr=", DoubleToString(pnl_atr, 4),
                  " score=", DoubleToString(MLP_BuyScore, 6));
            CLOSE_BUY(1, "MLP_TrailingStop");
            MLP_ResetBuyState();
            return;
         }
      }
      else if (ML_HoldBars > 0 && SHIFT(BUY.T) >= ML_HoldBars) {
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
         MLP_ResetBuyState();
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
         MLP_ResetBuyState();
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
      if (ML_ExitMode == MLP_EXIT_TRAIL) {
         double best_price = 0.0;
         double trail_price = 0.0;
         double pnl_atr = 0.0;
         bool close_trailing = false;
         if (ML_TrailATR > 0 && ATR > 0) {
            if (MLP_SellBestPrice <= 0.0 || MLP_SellBestPrice > SEL.Val) MLP_SellBestPrice = SEL.Val;
            if (Low[bar] < MLP_SellBestPrice) MLP_SellBestPrice = Low[bar];
            best_price = MLP_SellBestPrice;
            trail_price = best_price + ATR * ML_TrailATR;
            pnl_atr = (SEL.Val - ASK) / ATR;
            close_trailing = (ASK >= trail_price);
         }
         if (close_trailing) {
            double exit_price = ASK;
            MLP_cnt_trailing++;
            Print(Mgc, ":: MLP CLOSE SELL"
                  " reason=TrailingStop"
                  " signal_time=", TimeToString(MLP_SellSignalTime),
                  " entry_time=", TimeToString(SEL.T),
                  " exit_time=", TimeToString(Time[0]),
                  " entry=", DoubleToString(SEL.Val, Digits),
                  " best=", DoubleToString(best_price, Digits),
                  " trail=", DoubleToString(trail_price, Digits),
                  " exit=", DoubleToString(exit_price, Digits),
                  " atr=", DoubleToString(ATR, Digits),
                  " trail_atr=", DoubleToString(ML_TrailATR, 2),
                  " pnl_atr=", DoubleToString(pnl_atr, 4),
                  " score=", DoubleToString(MLP_SellScore, 6));
            CLOSE_SEL(1, "MLP_TrailingStop");
            MLP_ResetSellState();
            return;
         }
      }
      else if (ML_HoldBars > 0 && SHIFT(SEL.T) >= ML_HoldBars) {
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
         MLP_ResetSellState();
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
         MLP_ResetSellState();
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
      MLP_BuyBestPrice = ASK;
      MLP_ResetSellState();

      set.BUY.Sig = GOGO;
      set.BUY.Val = (float)ASK;
      set.BUY.Stp = (float)MathMax(min_price, set.BUY.Val - back_stop);
      set.BUY.Prf = 0;

      Print(Mgc, ":: MLP BUY"
            " signal_time=", TimeToString(MLP_BuySignalTime),
            " entry_time=", TimeToString(Time[0]),
            " score=", DoubleToString(score, 6),
            " exit_mode=", MLP_ExitModeName(),
            " Val=", DoubleToString(set.BUY.Val, Digits));
      return;
   }

   if (sig == -1) {
      float back_stop = (float)MathMax(ATR * ML_BackStopATR, StopLevel * 2.0);
      MLP_cnt_opened++;
      MLP_cnt_sell++;
      MLP_SellSignalTime = MLP_Times[idx];
      MLP_SellScore = score;
      MLP_SellBestPrice = BID;
      MLP_ResetBuyState();

      set.SEL.Sig = GOGO;
      set.SEL.Val = (float)BID;
      set.SEL.Stp = set.SEL.Val + back_stop;
      set.SEL.Prf = 0;

      Print(Mgc, ":: MLP SELL"
            " signal_time=", TimeToString(MLP_SellSignalTime),
            " entry_time=", TimeToString(Time[0]),
            " score=", DoubleToString(score, 6),
            " exit_mode=", MLP_ExitModeName(),
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
   Print("  Trailing closes:  ", MLP_cnt_trailing);
   Print("  Reverse closes:   ", MLP_cnt_reverse);
   Print("  ExitMode=", MLP_ExitModeName(),
         "  HoldBars=", ML_HoldBars,
         "  TrailATR=", DoubleToString(ML_TrailATR, 2),
         "  MaxPositions=", ML_MaxPositions,
         "  ScoreFilter=", ML_UseScoreFilter,
         "  Threshold=", DoubleToString(ML_ScoreThreshold, 6),
         "  Reversal=", ML_AllowReversal,
         "  ScoreCol=", MLP_HasScoreColumn);
   Print("======================");
}
