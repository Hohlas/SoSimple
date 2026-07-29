//+------------------------------------------------------------------+
//| lib_ML_Signal.mqh                                 v4.3           |
//| Назначение: Прямое исполнение ML-сигналов для parity-check        |
//|             без старого INPUT/OUTPUT контура                      |
//| Автор: SoSimple                                                  |
//| Обновлён: 2026-05-13                                             |
//| Входные данные:                                                  |
//|   - MQL4/Files/ml_signals.csv or fixed11 rule-slot file          |
//| Поддерживаемые форматы CSV:                                      |
//|   - time;signal                                                  |
//|   - time;signal;atr                                              |
//|   - time;signal;atr;stop                                         |
//|   - time;signal;...;pred_ret_24_dir_atr;...                      |
//| Логика:                                                          |
//|   - сигнал на баре t -> E3 pullback limit на следующем баре      |
//|   - одна или несколько открытых позиций, если ML_MaxPositions > 1|
//|   - режим 0: закрытие по удержанию либо по обратному сигналу     |
//|   - режим 1: отдельный bar-based trailing-stop по X*ATR          |
//+------------------------------------------------------------------+
#property strict

#define MLP_DEFAULT_SIGNALS_FILE "ml_signals.csv"
#define MLP_EVENTS_FILE_PREFIX "ML_Trade_Events_"
#define MLP_MAX_SIGNALS  200000
#define MLP_Ver          4.3
#define MLP_EXIT_TIMEOUT 0
#define MLP_EXIT_TRAIL   1
#define MLP_WAIT_SIGNAL_SEC 120
#define MLP_TRADE_RETRIES 5
#define MLP_MAX_SLIPPAGE_ATR 0.25
#define MLP_ENTRY_FILL_LAG_BARS 6
#define MLP_EXPECTED_SPREAD 0.20

int      MLP_SignalCount = 0;
datetime MLP_Times[];
char     MLP_Signals[];
float    MLP_Scores[];
float    MLP_ATRs[];
float    MLP_Stops[];
bool     MLP_HasScoreColumn = false;
bool     MLP_HasAtrColumn = false;
bool     MLP_HasStopColumn = false;
bool     MLP_Loaded = false;
bool     MLP_SpreadWarned = false;
datetime MLP_LoadedFileModifyTime = 0;
datetime MLP_RuntimeStartTime = 0;
int      MLP_ExitCount = 0;
datetime MLP_ExitSignalTimes[];
datetime MLP_ExitTimes[];

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
int MLP_cnt_mlclose  = 0;
int MLP_cnt_broker_take = 0;
int MLP_cnt_broker_stop = 0;
int MLP_cnt_broker_other = 0;

int MLP_LoggedCloseTickets[];
int MLP_LoggedCloseCount = 0;
int MLP_LoggedOpenTickets[];
int MLP_LoggedOpenCount = 0;
int MLP_PlacedOrderTickets[];
datetime MLP_PlacedOrderSignalTimes[];
double MLP_PlacedOrderCalculationOpens[];
double MLP_PlacedOrderRequestedPrices[];
double MLP_PlacedOrderATRs[];
double MLP_PlacedOrderScores[];
int MLP_PlacedOrderCount = 0;
int MLP_EventsFilePrepared[];
int MLP_EventsFilePreparedCount = 0;

string MLP_EventsFileName(int magic) {
   return MLP_EVENTS_FILE_PREFIX + NAME + "_" + S0(magic) + ".csv";
}

string MLP_SignalsFileName() {
   if (ML_RuleSlot == 1) return "ml_signals_fixed11_rule01.csv";
   if (ML_RuleSlot == 2) return "ml_signals_fixed11_rule02.csv";
   if (ML_RuleSlot == 3) return "ml_signals_fixed11_rule03.csv";
   if (ML_RuleSlot == 4) return "ml_signals_fixed11_rule04.csv";
   if (ML_RuleSlot == 5) return "ml_signals_fixed11_rule05.csv";
   return MLP_DEFAULT_SIGNALS_FILE;
}

string MLP_ExitsFileName() {
   if (ML_RuleSlot == 1) return "ml_exits_fixed11_rule01.csv";
   if (ML_RuleSlot == 2) return "ml_exits_fixed11_rule02.csv";
   if (ML_RuleSlot == 3) return "ml_exits_fixed11_rule03.csv";
   if (ML_RuleSlot == 4) return "ml_exits_fixed11_rule04.csv";
   if (ML_RuleSlot == 5) return "ml_exits_fixed11_rule05.csv";
   return "";
}

void MLP_WriteEventHeaderIfNeeded(int handle) {
   if (FileSize(handle) > 0) return;
   FileWrite(handle,
      "event",
      "ticket",
      "direction",
      "signal_time",
      "entry_time",
      "exit_time",
      "reason",
      "score",
      "atr",
      "bid",
      "ask",
      "spread",
      "spread_atr",
      "bar_open",
      "bar_high",
      "bar_low",
      "bar_close",
      "calculation_open",
      "requested_price",
      "order_open_price",
      "order_close_price",
      "slippage_points",
      "entry",
      "stop",
      "take_profit",
      "close",
      "profit",
      "swap",
      "commission",
      "hold_bars",
      "ml_exit_time",
      "decision_bar_time",
      "bars_late",
      "open_positions",
      "max_positions",
      "balance",
      "equity");
}

bool MLP_EventFileWasPrepared(int magic) {
   for (int i = 0; i < MLP_EventsFilePreparedCount; i++) {
      if (MLP_EventsFilePrepared[i] == magic) return true;
   }
   return false;
}

void MLP_MarkEventFilePrepared(int magic) {
   if (MLP_EventFileWasPrepared(magic)) return;
   ArrayResize(MLP_EventsFilePrepared, MLP_EventsFilePreparedCount + 1);
   MLP_EventsFilePrepared[MLP_EventsFilePreparedCount] = magic;
   MLP_EventsFilePreparedCount++;
}

void MLP_PrepareEventFileIfNeeded(int magic) {
   if (MLP_EventFileWasPrepared(magic)) return;
   if (IsTesting()) FileDelete(MLP_EventsFileName(magic));
   MLP_MarkEventFilePrepared(magic);
}

void MLP_LogTradeEvent(
   int magic,
   string event_name,
   int ticket,
   string direction,
   datetime signal_time,
   datetime entry_time,
   datetime exit_time,
   string reason,
   double score,
   double atr_value,
   double calculation_open,
   double requested_price,
   double order_open_price,
   double stop_price,
   double take_profit_price,
   double order_close_price,
   double profit_value,
   double swap_value,
   double commission_value,
   int hold_bars,
   datetime ml_exit_time,
   datetime decision_bar_time,
   int open_positions,
   int max_positions
) {
   MLP_PrepareEventFileIfNeeded(magic);
   int handle = FileOpen(MLP_EventsFileName(magic), FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_SHARE_READ | FILE_SHARE_WRITE, ';');
   if (handle < 0) return;

   MLP_WriteEventHeaderIfNeeded(handle);
   FileSeek(handle, 0, SEEK_END);
   RefreshRates();

   double spread_value = Ask - Bid;
   double spread_atr = 0.0;
   if (atr_value > 0) spread_atr = spread_value / atr_value;
   double point_value = MarketInfo(Symbol(), MODE_POINT);
   double slippage_points = 0.0;
   if (point_value > 0 && requested_price > 0) {
      if (event_name == "OPEN" && order_open_price > 0) {
         slippage_points = (order_open_price - requested_price) / point_value;
         if (direction == "SELL") slippage_points = -slippage_points;
      }
      else if (event_name == "CLOSE" && order_close_price > 0) {
         slippage_points = (order_close_price - requested_price) / point_value;
         if (direction == "BUY") slippage_points = -slippage_points;
      }
   }

   FileWrite(handle,
      event_name,
      ticket,
      direction,
      TimeToString(signal_time),
      TimeToString(entry_time),
      TimeToString(exit_time),
      reason,
      DoubleToString(score, 6),
      DoubleToString(atr_value, Digits),
      DoubleToString(Bid, Digits),
      DoubleToString(Ask, Digits),
      DoubleToString(spread_value, Digits),
      DoubleToString(spread_atr, 4),
      DoubleToString(Open[bar], Digits),
      DoubleToString(High[bar], Digits),
      DoubleToString(Low[bar], Digits),
      DoubleToString(Close[bar], Digits),
      DoubleToString(calculation_open, Digits),
      DoubleToString(requested_price, Digits),
      DoubleToString(order_open_price, Digits),
      DoubleToString(order_close_price, Digits),
      DoubleToString(slippage_points, 1),
      DoubleToString(order_open_price, Digits),
      DoubleToString(stop_price, Digits),
      DoubleToString(take_profit_price, Digits),
      DoubleToString(order_close_price, Digits),
      DoubleToString(profit_value, 2),
      DoubleToString(swap_value, 2),
      DoubleToString(commission_value, 2),
      hold_bars,
      TimeToString(ml_exit_time),
      TimeToString(decision_bar_time),
      (ml_exit_time > 0 && decision_bar_time > 0 ? (int)((decision_bar_time - ml_exit_time) / (Period() * 60)) : 0),
      open_positions,
      max_positions,
      DoubleToString(AccountBalance(), 2),
      DoubleToString(AccountEquity(), 2));
   FileClose(handle);
}

string MLP_ExitModeName() {
   if (ML_ExitMode == MLP_EXIT_TRAIL) return "trailing_stop";
   return "timeout";
}

void MLP_CheckExpectedSpread(int magic, string sym) {
   if (MLP_SpreadWarned) return;
   if (ML_RuleSlot <= 0) return;

   RefreshRates();
   double spread_value = Ask - Bid;
   double tolerance = MathMax(MarketInfo(sym, MODE_POINT), 0.0000001);
   if (MathAbs(spread_value - MLP_EXPECTED_SPREAD) <= tolerance) return;

   Print(magic, ":: MLP SPREAD_MISMATCH expected=", DoubleToString(MLP_EXPECTED_SPREAD, Digits),
         " actual=", DoubleToString(spread_value, Digits),
         " tester_spread_points=", MarketInfo(sym, MODE_SPREAD),
         " rule_slot=", ML_RuleSlot,
         " status=invalid_for_fixed11_parity");
   MLP_SpreadWarned = true;
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

datetime MLP_FileModifyTime() {
   string signals_file = MLP_SignalsFileName();
   int handle = FileOpen(signals_file, FILE_READ | FILE_BIN);
   if (handle < 0) return 0;
   datetime modified = (datetime)FileGetInteger(handle, FILE_MODIFY_DATE);
   FileClose(handle);
   return modified;
}

bool MLP_IsOwnMarketOrder(int magic, string sym) {
   if (OrderMagicNumber() != magic) return false;
   if (OrderSymbol() != sym) return false;
   int typ = OrderType();
   return (typ == OP_BUY || typ == OP_SELL);
}

bool MLP_IsOwnWorkingOrder(int magic, string sym) {
   if (OrderMagicNumber() != magic) return false;
   if (OrderSymbol() != sym) return false;
   int typ = OrderType();
   return (typ == OP_BUY || typ == OP_SELL || typ == OP_BUYLIMIT || typ == OP_SELLLIMIT);
}

bool MLP_IsOwnPendingOrder(int magic, string sym) {
   if (OrderMagicNumber() != magic) return false;
   if (OrderSymbol() != sym) return false;
   int typ = OrderType();
   return (typ == OP_BUYLIMIT || typ == OP_SELLLIMIT);
}

int MLP_CountOwnMarketOrders(int magic, string sym) {
   int count = 0;
   for (int i = 0; i < OrdersTotal(); i++) {
      if (!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if (MLP_IsOwnMarketOrder(magic, sym)) count++;
   }
   return count;
}

int MLP_CountOwnWorkingOrders(int magic, string sym) {
   int count = 0;
   for (int i = 0; i < OrdersTotal(); i++) {
      if (!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if (MLP_IsOwnWorkingOrder(magic, sym)) count++;
   }
   return count;
}

bool MLP_CloseTicketWasLogged(int ticket) {
   for (int i = 0; i < MLP_LoggedCloseCount; i++) {
      if (MLP_LoggedCloseTickets[i] == ticket) return true;
   }
   return false;
}

void MLP_MarkCloseTicketLogged(int ticket) {
   if (ticket <= 0 || MLP_CloseTicketWasLogged(ticket)) return;
   ArrayResize(MLP_LoggedCloseTickets, MLP_LoggedCloseCount + 1);
   MLP_LoggedCloseTickets[MLP_LoggedCloseCount] = ticket;
   MLP_LoggedCloseCount++;
}

bool MLP_OpenTicketWasLogged(int ticket) {
   for (int i = 0; i < MLP_LoggedOpenCount; i++) {
      if (MLP_LoggedOpenTickets[i] == ticket) return true;
   }
   return false;
}

void MLP_MarkOpenTicketLogged(int ticket) {
   if (ticket <= 0 || MLP_OpenTicketWasLogged(ticket)) return;
   ArrayResize(MLP_LoggedOpenTickets, MLP_LoggedOpenCount + 1);
   MLP_LoggedOpenTickets[MLP_LoggedOpenCount] = ticket;
   MLP_LoggedOpenCount++;
}

int MLP_FindPlacedOrder(int ticket) {
   for (int i = 0; i < MLP_PlacedOrderCount; i++) {
      if (MLP_PlacedOrderTickets[i] == ticket) return i;
   }
   return -1;
}

void MLP_RememberPlacedOrder(
   int ticket,
   datetime signal_time,
   double calculation_open,
   double requested_price,
   double atr_value,
   double score
) {
   if (ticket <= 0) return;

   int idx = MLP_FindPlacedOrder(ticket);
   if (idx < 0) {
      idx = MLP_PlacedOrderCount;
      ArrayResize(MLP_PlacedOrderTickets, MLP_PlacedOrderCount + 1);
      ArrayResize(MLP_PlacedOrderSignalTimes, MLP_PlacedOrderCount + 1);
      ArrayResize(MLP_PlacedOrderCalculationOpens, MLP_PlacedOrderCount + 1);
      ArrayResize(MLP_PlacedOrderRequestedPrices, MLP_PlacedOrderCount + 1);
      ArrayResize(MLP_PlacedOrderATRs, MLP_PlacedOrderCount + 1);
      ArrayResize(MLP_PlacedOrderScores, MLP_PlacedOrderCount + 1);
      MLP_PlacedOrderCount++;
   }

   MLP_PlacedOrderTickets[idx] = ticket;
   MLP_PlacedOrderSignalTimes[idx] = signal_time;
   MLP_PlacedOrderCalculationOpens[idx] = calculation_open;
   MLP_PlacedOrderRequestedPrices[idx] = requested_price;
   MLP_PlacedOrderATRs[idx] = atr_value;
   MLP_PlacedOrderScores[idx] = score;
}

int MLP_BarsSinceOrderOpen(string sym) {
   int shift = iBarShift(sym, Period(), OrderOpenTime(), false);
   if (shift < 0) return 0;
   return shift;
}

bool MLP_IsFixed11TesterMode() {
   return (IsTesting() && ML_RuleSlot > 0);
}

void MLP_DeleteExpiredPendingOrders(int magic, uchar exp_num, string sym, double atr_value) {
   for (int i = OrdersTotal() - 1; i >= 0; i--) {
      if (!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if (!MLP_IsOwnPendingOrder(magic, sym)) continue;

      int bars_since_order = MLP_BarsSinceOrderOpen(sym);
      int ticket = OrderTicket();
      int typ = OrderType();
      datetime signal_time = MLP_OrderSignalTime();
      datetime order_time = OrderOpenTime();
      double requested_price = OrderOpenPrice();
      datetime ml_exit_time = MLP_ExitTimeForSignal(signal_time);
      datetime decision_bar_time = MLP_MLCloseDecisionTime();
      bool stale_pending = (MLP_IsFixed11TesterMode() && ml_exit_time > 0 && decision_bar_time >= ml_exit_time);

      if (!stale_pending && bars_since_order <= MLP_ENTRY_FILL_LAG_BARS) continue;

      bool deleted = OrderDelete(ticket, clrGray);
      if (deleted) {
         string reason = stale_pending ? "StalePendingAfterMLClose" : "LimitExpired";
         Print(magic, ":: MLP LIMIT_DELETED",
               " reason=", reason,
               " ticket=", ticket,
               " direction=", (typ == OP_BUYLIMIT ? "BUY" : "SELL"),
               " signal_time=", TimeToString(signal_time),
               " ml_exit_time=", TimeToString(ml_exit_time),
               " decision_bar_time=", TimeToString(decision_bar_time),
               " bars_late=", (ml_exit_time > 0 && decision_bar_time > 0 ? (int)((decision_bar_time - ml_exit_time) / (Period() * 60)) : 0),
               " order_time=", TimeToString(order_time),
               " delete_time=", TimeToString(Time[0]),
               " bars_since_order=", bars_since_order,
               " fill_lag_bars=", MLP_ENTRY_FILL_LAG_BARS,
               " requested_price=", DoubleToString(requested_price, Digits));
         MLP_LogTradeEvent(magic,
               "OPEN_FAILED",
               ticket,
               (typ == OP_BUYLIMIT ? "BUY" : "SELL"),
               signal_time,
               order_time,
               Time[0],
               reason,
               0.0,
               atr_value,
               0.0,
               requested_price,
               requested_price,
               OrderStopLoss(),
               OrderTakeProfit(),
               0.0,
               0.0,
               0.0,
               0.0,
               0,
               ml_exit_time,
               decision_bar_time,
               MLP_CountOwnMarketOrders(magic, sym),
               ML_MaxPositions);
      }
      else {
         ERROR_CHECK("MLP_DeleteExpiredPendingOrders", exp_num);
      }
   }
}

string MLP_BrokerCloseReason(int typ, double close_price, double stop_loss, double take_profit, string sym) {
   double tolerance = MathMax(MarketInfo(sym, MODE_POINT) * 5.0, 0.0000001);
   if (take_profit > 0) {
      if (typ == OP_BUY && close_price >= take_profit - tolerance) return "TakeProfit";
      if (typ == OP_SELL && close_price <= take_profit + tolerance) return "TakeProfit";
   }
   if (stop_loss > 0) {
      if (typ == OP_BUY && close_price <= stop_loss + tolerance) return "StopLoss";
      if (typ == OP_SELL && close_price >= stop_loss - tolerance) return "StopLoss";
   }
   return "BrokerClose";
}

int MLP_HoldBars(datetime entry_time, datetime exit_time, string sym) {
   int entry_shift = iBarShift(sym, Period(), entry_time, false);
   int exit_shift = iBarShift(sym, Period(), exit_time, false);
   if (entry_shift < 0 || exit_shift < 0) return 0;
   return MathMax(0, entry_shift - exit_shift);
}

string MLP_OrderComment(int magic, datetime signal_time) {
   return S0(magic) + "-MLP-" + TimeToString(signal_time, TIME_DATE | TIME_MINUTES);
}

datetime MLP_OrderSignalTime() {
   string comment = OrderComment();
   int pos = StringFind(comment, "-MLP-", 0);
   if (pos < 0) return 0;
   return StringToTime(StringSubstr(comment, pos + 5, 16));
}

void MLP_LogFilledMarketOrders(int magic, uchar exp_num, string sym, double atr_value) {
   for (int i = 0; i < OrdersTotal(); i++) {
      if (!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if (!MLP_IsOwnMarketOrder(magic, sym)) continue;

      int ticket = OrderTicket();
      if (MLP_OpenTicketWasLogged(ticket)) continue;

      int typ = OrderType();
      datetime signal_time = MLP_OrderSignalTime();
      double entry_price = OrderOpenPrice();
      double stop_loss = OrderStopLoss();
      double take_profit = OrderTakeProfit();
      datetime entry_time = OrderOpenTime();
      double lots = OrderLots();
      double calculation_open = 0.0;
      double requested_price = entry_price;
      double event_atr = atr_value;
      double score = 0.0;
      int placed_idx = MLP_FindPlacedOrder(ticket);
      if (placed_idx >= 0) {
         signal_time = MLP_PlacedOrderSignalTimes[placed_idx];
         calculation_open = MLP_PlacedOrderCalculationOpens[placed_idx];
         requested_price = MLP_PlacedOrderRequestedPrices[placed_idx];
         event_atr = MLP_PlacedOrderATRs[placed_idx];
         score = MLP_PlacedOrderScores[placed_idx];
      }
      double spread_value = Ask - Bid;
      double spread_atr = 0.0;
      if (event_atr > 0) spread_atr = spread_value / event_atr;
      int open_positions = MLP_CountOwnMarketOrders(magic, sym);

      MLP_cnt_opened++;
      if (typ == OP_BUY) MLP_cnt_buy++;
      else MLP_cnt_sell++;

      Print(magic, ":: MLP ", (typ == OP_BUY ? "BUY" : "SELL"),
            " mode=e3_pullback_limit_v1",
            " ticket=", ticket,
            " signal_time=", TimeToString(signal_time),
            " entry_time=", TimeToString(entry_time),
            " calculation_open=", DoubleToString(calculation_open, Digits),
            " requested_price=", DoubleToString(requested_price, Digits),
            " atr=", DoubleToString(event_atr, Digits),
            " spread=", DoubleToString(spread_value, Digits),
            " spread_atr=", DoubleToString(spread_atr, 4),
            " exit_mode=", MLP_ExitModeName(),
            " TrailATR=", DoubleToString(ML_TrailATR, 2),
            " TakeProfitATR=", DoubleToString(ML_TakeProfitATR, 2),
            " open_positions=", open_positions,
            " MaxPositions=", ML_MaxPositions,
            " Val=", DoubleToString(entry_price, Digits),
            " Stp=", DoubleToString(stop_loss, Digits),
            " Prf=", DoubleToString(take_profit, Digits),
            " Lot=", DoubleToString(lots, 2));
      MLP_LogTradeEvent(magic,
            "OPEN",
            ticket,
            (typ == OP_BUY ? "BUY" : "SELL"),
            signal_time,
            entry_time,
            0,
            "",
            score,
            event_atr,
            calculation_open,
            requested_price,
            entry_price,
            stop_loss,
            take_profit,
            0.0,
            0.0,
            0.0,
            0.0,
            0,
            0,
            0,
            open_positions,
            ML_MaxPositions);

      MLP_MarkOpenTicketLogged(ticket);

      datetime ml_exit_time = MLP_ExitTimeForSignal(signal_time);
      if (MLP_IsFixed11TesterMode() && ml_exit_time > 0 && ml_exit_time < entry_time) {
         Print(magic, ":: MLP STALE_FILL_AFTER_MLCLOSE",
               " ticket=", ticket,
               " direction=", (typ == OP_BUY ? "BUY" : "SELL"),
               " signal_time=", TimeToString(signal_time),
               " entry_time=", TimeToString(entry_time),
               " ml_exit_time=", TimeToString(ml_exit_time),
               " close_check_time=", TimeToString(Time[0]));
         MLP_CloseSelectedOrder(magic, exp_num, event_atr, "StaleFillAfterMLClose", entry_price, entry_price, ml_exit_time, Time[0]);
      }
   }
}

void MLP_LogHistoryOpenIfNeeded(
   int magic,
   string sym,
   int ticket,
   int typ,
   datetime signal_time,
   double entry_price,
   double stop_loss,
   double take_profit,
   double atr_value
) {
   if (MLP_OpenTicketWasLogged(ticket)) return;

   double calculation_open = 0.0;
   double requested_price = entry_price;
   double event_atr = atr_value;
   double score = 0.0;
   int placed_idx = MLP_FindPlacedOrder(ticket);
   if (placed_idx >= 0) {
      signal_time = MLP_PlacedOrderSignalTimes[placed_idx];
      calculation_open = MLP_PlacedOrderCalculationOpens[placed_idx];
      requested_price = MLP_PlacedOrderRequestedPrices[placed_idx];
      event_atr = MLP_PlacedOrderATRs[placed_idx];
      score = MLP_PlacedOrderScores[placed_idx];
   }

   MLP_cnt_opened++;
   if (typ == OP_BUY) MLP_cnt_buy++;
   else MLP_cnt_sell++;

   Print(magic, ":: MLP ", (typ == OP_BUY ? "BUY" : "SELL"),
         " mode=e3_pullback_limit_v1",
         " source=broker_history_missing_open",
         " ticket=", ticket,
         " signal_time=", TimeToString(signal_time),
         " entry_time=", TimeToString(OrderOpenTime()),
         " calculation_open=", DoubleToString(calculation_open, Digits),
         " requested_price=", DoubleToString(requested_price, Digits),
         " atr=", DoubleToString(event_atr, Digits),
         " Val=", DoubleToString(entry_price, Digits),
         " Stp=", DoubleToString(stop_loss, Digits),
         " Prf=", DoubleToString(take_profit, Digits),
         " Lot=", DoubleToString(OrderLots(), 2));
   MLP_LogTradeEvent(magic,
         "OPEN",
         ticket,
         (typ == OP_BUY ? "BUY" : "SELL"),
         signal_time,
         OrderOpenTime(),
         0,
         "broker_history_missing_open",
         score,
         event_atr,
         calculation_open,
         requested_price,
         entry_price,
         stop_loss,
         take_profit,
         0.0,
         0.0,
         0.0,
         0.0,
         0,
         0,
         0,
         0,
         ML_MaxPositions);
   MLP_MarkOpenTicketLogged(ticket);
}

void MLP_LogBrokerClosedOrders(int magic, string sym, double atr_value) {
   for (int i = OrdersHistoryTotal() - 1; i >= 0; i--) {
      if (!OrderSelect(i, SELECT_BY_POS, MODE_HISTORY)) continue;
      if (OrderMagicNumber() != magic || OrderSymbol() != sym) continue;

      int typ = OrderType();
      if (typ != OP_BUY && typ != OP_SELL) continue;

      int ticket = OrderTicket();
      if (MLP_CloseTicketWasLogged(ticket)) continue;

      datetime close_time = OrderCloseTime();
      if (close_time <= 0) continue;
      if (MLP_RuntimeStartTime > 0 && close_time < MLP_RuntimeStartTime) continue;

      double entry_price = OrderOpenPrice();
      double close_price = OrderClosePrice();
      double stop_loss = OrderStopLoss();
      double take_profit = OrderTakeProfit();
      double profit_value = OrderProfit() + OrderSwap() + OrderCommission();
      datetime signal_time = MLP_OrderSignalTime();
      MLP_LogHistoryOpenIfNeeded(magic, sym, ticket, typ, signal_time, entry_price, stop_loss, take_profit, atr_value);
      double pnl_atr = 0.0;
      if (atr_value > 0) {
         if (typ == OP_BUY) pnl_atr = (close_price - entry_price) / atr_value;
         else pnl_atr = (entry_price - close_price) / atr_value;
      }

      string reason = MLP_BrokerCloseReason(typ, close_price, stop_loss, take_profit, sym);
      if (reason == "TakeProfit") MLP_cnt_broker_take++;
      else if (reason == "StopLoss") MLP_cnt_broker_stop++;
      else MLP_cnt_broker_other++;

      Print(magic, ":: MLP CLOSE ", (typ == OP_BUY ? "BUY" : "SELL"),
            " reason=", reason,
            " source=broker_history",
            " ticket=", ticket,
            " entry_time=", TimeToString(OrderOpenTime()),
            " exit_time=", TimeToString(close_time),
            " hold_bars=", MLP_HoldBars(OrderOpenTime(), close_time, sym),
            " entry=", DoubleToString(entry_price, Digits),
            " stop=", DoubleToString(stop_loss, Digits),
            " take_profit=", DoubleToString(take_profit, Digits),
            " exit=", DoubleToString(close_price, Digits),
            " atr=", DoubleToString(atr_value, Digits),
            " pnl_atr=", DoubleToString(pnl_atr, 4),
            " profit=", DoubleToString(profit_value, 2));
      MLP_LogTradeEvent(magic,
            "CLOSE",
            ticket,
            (typ == OP_BUY ? "BUY" : "SELL"),
            signal_time,
            OrderOpenTime(),
            close_time,
            reason,
            0.0,
            atr_value,
            0.0,
            close_price,
            entry_price,
            stop_loss,
            take_profit,
            close_price,
            profit_value,
            OrderSwap(),
            OrderCommission(),
            MLP_HoldBars(OrderOpenTime(), close_time, sym),
            0,
            0,
            0,
            ML_MaxPositions);

      MLP_MarkCloseTicketLogged(ticket);
   }
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

bool MLP_IsTimeoutDue(int hold_bars) {
   return (ML_HoldBars > 0 && hold_bars >= ML_HoldBars);
}

int MLP_TradeSlippagePoints(string sym, double atr_value) {
   int spread_points = (int)MarketInfo(sym, MODE_SPREAD);
   int slippage = spread_points + 5;
   if (slippage < 3) slippage = 3;

   double point = MarketInfo(sym, MODE_POINT);
   if (atr_value > 0 && point > 0) {
      int atr_cap = (int)MathFloor(atr_value * MLP_MAX_SLIPPAGE_ATR / point);
      if (atr_cap < 3) atr_cap = 3;
      if (slippage > atr_cap) slippage = atr_cap;
   }
   return slippage;
}

bool MLP_CloseSelectedOrder(int magic, uchar exp_num, double atr_value, string reason, double best_price, double trail_price, datetime ml_exit_time, datetime decision_bar_time) {
   int ticket = OrderTicket();
   int typ = OrderType();
   double lots = OrderLots();
   double entry_price = OrderOpenPrice();
   datetime entry_time = OrderOpenTime();
   int hold_bars = SHIFT(entry_time);
   bool ok = false;

   WAITING(magic, "Terminal", 20);
   for (int repeat = MLP_TRADE_RETRIES; repeat > 0 && !ok; repeat--) {
      RefreshRates();
      double close_price = (typ == OP_BUY) ? Bid : Ask;
      ok = OrderClose(ticket, lots, close_price, MLP_TradeSlippagePoints(OrderSymbol(), atr_value), clrRed);
      if (ok) break;
      if (!ERROR_CHECK("MLP_Close Ticket=" + S0(ticket), exp_num)) break;
   }
   FREE(magic, "Terminal");

   RefreshRates();
   double exit_price = (typ == OP_BUY) ? Bid : Ask;
   double spread_value = Ask - Bid;
   double spread_atr = 0.0;
   if (atr_value > 0) spread_atr = spread_value / atr_value;
   double pnl_atr = 0.0;
   if (atr_value > 0) {
      if (typ == OP_BUY) pnl_atr = (exit_price - entry_price) / atr_value;
      else pnl_atr = (entry_price - exit_price) / atr_value;
   }
   double profit_value = OrderProfit() + OrderSwap() + OrderCommission();
   double swap_value = OrderSwap();
   double commission_value = OrderCommission();
   double actual_close_price = exit_price;
   double close_stop_price = OrderStopLoss();
   double close_take_profit_price = OrderTakeProfit();
   datetime signal_time = MLP_OrderSignalTime();
   if (ok && OrderSelect(ticket, SELECT_BY_TICKET, MODE_HISTORY)) {
      actual_close_price = OrderClosePrice();
      close_stop_price = OrderStopLoss();
      close_take_profit_price = OrderTakeProfit();
      profit_value = OrderProfit() + OrderSwap() + OrderCommission();
      swap_value = OrderSwap();
      commission_value = OrderCommission();
   }

   if (ok) {
      MLP_MarkCloseTicketLogged(ticket);
      if (reason == "TrailingStop") MLP_cnt_trailing++;
      else if (reason == "Timeout") MLP_cnt_timeout++;
      else if (reason == "ReverseSignal") MLP_cnt_reverse++;
      else if (reason == "MLClose") MLP_cnt_mlclose++;
      Print(magic, ":: MLP CLOSE ", (typ == OP_BUY ? "BUY" : "SELL"),
            " reason=", reason,
            " ticket=", ticket,
            " signal_time=", TimeToString(signal_time),
            " ml_exit_time=", TimeToString(ml_exit_time),
            " decision_bar_time=", TimeToString(decision_bar_time),
            " bars_late=", (ml_exit_time > 0 && decision_bar_time > 0 ? (int)((decision_bar_time - ml_exit_time) / (Period() * 60)) : 0),
            " entry_time=", TimeToString(entry_time),
            " exit_time=", TimeToString(Time[0]),
            " hold_bars=", hold_bars,
            " entry=", DoubleToString(entry_price, Digits),
            " best=", DoubleToString(best_price, Digits),
            " trail=", DoubleToString(trail_price, Digits),
            " exit=", DoubleToString(exit_price, Digits),
            " atr=", DoubleToString(atr_value, Digits),
            " spread=", DoubleToString(spread_value, Digits),
            " spread_atr=", DoubleToString(spread_atr, 4),
            " trail_atr=", DoubleToString(ML_TrailATR, 2),
            " pnl_atr=", DoubleToString(pnl_atr, 4),
            " profit=", DoubleToString(profit_value, 2));
      MLP_LogTradeEvent(magic,
            "CLOSE",
            ticket,
            (typ == OP_BUY ? "BUY" : "SELL"),
            signal_time,
            entry_time,
            Time[0],
            reason,
            0.0,
            atr_value,
            0.0,
            exit_price,
            entry_price,
            close_stop_price,
            close_take_profit_price,
            actual_close_price,
            profit_value,
            swap_value,
            commission_value,
            hold_bars,
            ml_exit_time,
            decision_bar_time,
            MLP_CountOwnMarketOrders(magic, Symbol()),
            ML_MaxPositions);
   }
   return ok;
}

void MLP_ManageMultiPositions(int magic, uchar exp_num, string sym, double atr_value, int current_sig) {
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
      datetime signal_time = MLP_OrderSignalTime();
      datetime ml_exit_time = MLP_ExitTimeForSignal(signal_time);
      datetime decision_bar_time = MLP_MLCloseDecisionTime();

      int hold_bars = SHIFT(OrderOpenTime());
      if (MLP_ShouldCloseByML(signal_time, decision_bar_time)) {
         should_close = true;
         close_reason = "MLClose";
      }
      else if (ML_AllowReversal && current_sig == -1 && typ == OP_BUY) {
         should_close = true;
         close_reason = "ReverseSignal";
      }
      else if (ML_AllowReversal && current_sig == 1 && typ == OP_SELL) {
         should_close = true;
         close_reason = "ReverseSignal";
      }
      else if (ML_ExitMode == MLP_EXIT_TIMEOUT && MLP_IsTimeoutDue(hold_bars)) {
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
         if (close_reason != "MLClose") {
            ml_exit_time = 0;
            decision_bar_time = 0;
         }
         MLP_CloseSelectedOrder(magic, exp_num, atr_value, close_reason, best_price, trail_price, ml_exit_time, decision_bar_time);
      }
   }
}

bool MLP_OpenLimitOrder(int magic, uchar exp_num, string sym, int sig, double score, datetime signal_time, double calculation_open, double atr_value, double csv_stop_price, int open_positions_before) {
   if (atr_value <= 0) return false;
   if (sig != 1 && sig != -1) return false;

   RefreshRates();
   double min_price = MarketInfo(sym, MODE_POINT);
   double limit_price = (sig == 1) ? calculation_open - atr_value : calculation_open + atr_value;
   double stop_distance = MathMax(atr_value * ML_BackStopATR, StopLevel * 2.0);
   if (csv_stop_price > 0.0) stop_distance = MathMax(MathAbs(limit_price - csv_stop_price), StopLevel * 2.0);
   double lot_to_send = Lot;
   if (Risk == 0 || IsTesting()) lot_to_send = 0.1;
   else lot_to_send = MM((float)stop_distance, CurExp);
   lot_to_send = NormalizeDouble(lot_to_send, LotDigits);
   if (lot_to_send <= 0) return false;

   bool market_after_limit_passed = (sig == 1 && Ask <= limit_price) || (sig == -1 && Bid >= limit_price);
   int order_type = market_after_limit_passed ? (sig == 1 ? OP_BUY : OP_SELL) : (sig == 1 ? OP_BUYLIMIT : OP_SELLLIMIT);
   double order_price = market_after_limit_passed ? (sig == 1 ? Ask : Bid) : limit_price;
   double stop_price = (sig == 1)
      ? MathMax(min_price, order_price - stop_distance)
      : order_price + stop_distance;
   if (csv_stop_price > 0.0) stop_price = csv_stop_price;
   double take_profit_price = 0.0;
   datetime expiration = 0;

   if (Real && Risk > 0) {
      double trade_risk = CHECK_RISK(lot_to_send, stop_distance, sym);
      if (trade_risk > MaxRisk) {
         REPORT(exp_num, "MLP risk too big: " + S2(trade_risk) + "% Lot=" + S2(lot_to_send));
         return false;
      }
   }

   int ticket = -1;
   bool ok = false;
   WAITING(magic, "Terminal", 20);
   for (int repeat = MLP_TRADE_RETRIES; repeat > 0 && !ok; repeat--) {
      RefreshRates();
      limit_price = (sig == 1) ? calculation_open - atr_value : calculation_open + atr_value;
      market_after_limit_passed = (sig == 1 && Ask <= limit_price) || (sig == -1 && Bid >= limit_price);
      order_type = market_after_limit_passed ? (sig == 1 ? OP_BUY : OP_SELL) : (sig == 1 ? OP_BUYLIMIT : OP_SELLLIMIT);
      order_price = market_after_limit_passed ? (sig == 1 ? Ask : Bid) : limit_price;
      stop_distance = MathMax(atr_value * ML_BackStopATR, StopLevel * 2.0);
      if (csv_stop_price > 0.0) stop_distance = MathMax(MathAbs(order_price - csv_stop_price), StopLevel * 2.0);
      stop_price = (sig == 1)
         ? MathMax(min_price, order_price - stop_distance)
         : order_price + stop_distance;
      if (csv_stop_price > 0.0) stop_price = csv_stop_price;
      if (market_after_limit_passed && ((sig == 1 && stop_price >= order_price) || (sig == -1 && stop_price <= order_price))) {
         Print(magic, ":: MLP OPEN_FAILED",
               " reason=MarketAfterLimitPassedStopInvalid",
               " sig=", sig,
               " signal_time=", TimeToString(signal_time),
               " entry_time=", TimeToString(Time[0]),
               " score=", DoubleToString(score, 6),
               " atr=", DoubleToString(atr_value, Digits),
               " spread=", DoubleToString(Ask - Bid, Digits),
               " open_positions=", open_positions_before,
               " MaxPositions=", ML_MaxPositions,
               " calculation_open=", DoubleToString(calculation_open, Digits),
               " requested_price=", DoubleToString(limit_price, Digits),
               " order_price=", DoubleToString(order_price, Digits),
               " stop_source=", (csv_stop_price > 0.0 ? "csv_stop" : "fallback_backstop_atr"),
               " fill_lag_bars=", MLP_ENTRY_FILL_LAG_BARS,
               " Val=", DoubleToString(limit_price, Digits),
               " Stp=", DoubleToString(stop_price, Digits),
               " Prf=", DoubleToString(take_profit_price, Digits),
               " Lot=", DoubleToString(lot_to_send, 2));
         MLP_LogTradeEvent(magic,
               "OPEN_FAILED",
               -1,
               (sig == 1 ? "BUY" : "SELL"),
               signal_time,
               Time[0],
               0,
               "MarketAfterLimitPassedStopInvalid",
               score,
               atr_value,
               calculation_open,
               limit_price,
               0.0,
               stop_price,
               take_profit_price,
               0.0,
               0.0,
               0.0,
               0.0,
               0,
               0,
               0,
               open_positions_before,
               ML_MaxPositions);
         FREE(magic, "Terminal");
         return false;
      }
      take_profit_price = 0.0;
      if (ML_TakeProfitATR > 0) {
         take_profit_price = (sig == 1)
            ? order_price + atr_value * ML_TakeProfitATR
            : order_price - atr_value * ML_TakeProfitATR;
         if (MathAbs(take_profit_price - order_price) <= StopLevel) take_profit_price = 0.0;
      }
      ticket = OrderSend(sym, order_type, lot_to_send, N5(order_price, sym), MLP_TradeSlippagePoints(sym, atr_value),
                         N5(stop_price, sym), N5(take_profit_price, sym), MLP_OrderComment(magic, signal_time), magic, expiration,
                         (sig == 1 ? clrGreen : clrRed));
      ok = (ticket > 0);
      if (ok) break;
      if (!ERROR_CHECK("MLP_OpenLimitOrder", exp_num)) break;
   }
   FREE(magic, "Terminal");

   if (ok) {
      RefreshRates();
      double actual_open_price = order_price;
      double actual_stop_price = stop_price;
      double actual_take_profit_price = take_profit_price;
      if (OrderSelect(ticket, SELECT_BY_TICKET, MODE_TRADES)) {
         actual_open_price = OrderOpenPrice();
         actual_stop_price = OrderStopLoss();
         actual_take_profit_price = OrderTakeProfit();
      }
      double spread_value = Ask - Bid;
      double spread_atr = 0.0;
      if (atr_value > 0) spread_atr = spread_value / atr_value;
      Print(magic, ":: MLP ", (market_after_limit_passed ? "MARKET_AFTER_LIMIT_PASSED" : "LIMIT"),
            " direction=", (sig == 1 ? "BUY" : "SELL"),
            " ticket=", ticket,
            " signal_time=", TimeToString(signal_time),
            " order_time=", TimeToString(Time[0]),
            " expires=manual_bar_window",
            " score=", DoubleToString(score, 6),
            " atr=", DoubleToString(atr_value, Digits),
            " spread=", DoubleToString(spread_value, Digits),
            " spread_atr=", DoubleToString(spread_atr, 4),
            " exit_mode=", MLP_ExitModeName(),
            " TrailATR=", DoubleToString(ML_TrailATR, 2),
            " TakeProfitATR=", DoubleToString(ML_TakeProfitATR, 2),
            " open_positions=", open_positions_before,
            " MaxPositions=", ML_MaxPositions,
            " calculation_open=", DoubleToString(calculation_open, Digits),
            " requested_price=", DoubleToString(limit_price, Digits),
            " order_price=", DoubleToString(order_price, Digits),
            " stop_source=", (csv_stop_price > 0.0 ? "csv_stop" : "fallback_backstop_atr"),
            " fill_lag_bars=", MLP_ENTRY_FILL_LAG_BARS,
            " Val=", DoubleToString(limit_price, Digits),
            " Stp=", DoubleToString(stop_price, Digits),
            " Prf=", DoubleToString(take_profit_price, Digits),
            " Lot=", DoubleToString(lot_to_send, 2));
      MLP_LogTradeEvent(magic,
            "ORDER_PLACED",
            ticket,
            (sig == 1 ? "BUY" : "SELL"),
            signal_time,
            Time[0],
            0,
            "",
            score,
            atr_value,
            calculation_open,
            limit_price,
            actual_open_price,
            actual_stop_price,
            actual_take_profit_price,
            0.0,
            0.0,
            0.0,
            0.0,
            0,
            0,
            0,
            open_positions_before,
            ML_MaxPositions);
      MLP_RememberPlacedOrder(ticket, signal_time, calculation_open, limit_price, atr_value, score);
   }
   else {
      double fail_spread = Ask - Bid;
      double fail_spread_atr = 0.0;
      if (atr_value > 0) fail_spread_atr = fail_spread / atr_value;
      Print(magic, ":: MLP OPEN_FAILED",
            " reason=OrderSendFailed",
            " sig=", sig,
            " signal_time=", TimeToString(signal_time),
            " entry_time=", TimeToString(Time[0]),
            " score=", DoubleToString(score, 6),
            " atr=", DoubleToString(atr_value, Digits),
            " spread=", DoubleToString(fail_spread, Digits),
            " spread_atr=", DoubleToString(fail_spread_atr, 4),
            " open_positions=", open_positions_before,
            " MaxPositions=", ML_MaxPositions,
            " calculation_open=", DoubleToString(calculation_open, Digits),
            " requested_price=", DoubleToString(limit_price, Digits),
            " order_price=", DoubleToString(order_price, Digits),
            " stop_source=", (csv_stop_price > 0.0 ? "csv_stop" : "fallback_backstop_atr"),
            " fill_lag_bars=", MLP_ENTRY_FILL_LAG_BARS,
            " Val=", DoubleToString(limit_price, Digits),
            " Stp=", DoubleToString(stop_price, Digits),
            " Prf=", DoubleToString(take_profit_price, Digits),
            " Lot=", DoubleToString(lot_to_send, 2));
      MLP_LogTradeEvent(magic,
            "OPEN_FAILED",
            ticket,
            (sig == 1 ? "BUY" : "SELL"),
            signal_time,
            Time[0],
            0,
            "OrderSendFailed",
            score,
            atr_value,
            calculation_open,
            limit_price,
            0.0,
            stop_price,
            take_profit_price,
            0.0,
            0.0,
            0.0,
            0.0,
            0,
            0,
            0,
            open_positions_before,
            ML_MaxPositions);
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

int MLP_FindSignalInsertPos(datetime barTime) {
   int lo = 0;
   int hi = MLP_SignalCount;

   while (lo < hi) {
      int mid = (lo + hi) / 2;
      if (MLP_Times[mid] < barTime) lo = mid + 1;
      else hi = mid;
   }

   return lo;
}

int MLP_FindExit(datetime signal_time) {
   int lo = 0;
   int hi = MLP_ExitCount - 1;
   while (lo <= hi) {
      int mid = (lo + hi) / 2;
      if (MLP_ExitSignalTimes[mid] == signal_time) return mid;
      if (MLP_ExitSignalTimes[mid] < signal_time) lo = mid + 1;
      else hi = mid - 1;
   }
   return -1;
}

datetime MLP_MLCloseDecisionTime() {
   if (IsTesting() && ML_RuleSlot > 0) return Time[0];
   return Time[bar];
}

datetime MLP_ExitTimeForSignal(datetime signal_time) {
   int idx = MLP_FindExit(signal_time);
   if (idx < 0) return 0;
   return MLP_ExitTimes[idx];
}

bool MLP_ShouldCloseByML(datetime signal_time, datetime decision_time) {
   datetime exit_time = MLP_ExitTimeForSignal(signal_time);
   if (exit_time <= 0) return false;
   return decision_time >= exit_time;
}

bool MLP_LoadExits() {
   MLP_ExitCount = 0;
   ArrayResize(MLP_ExitSignalTimes, 0);
   ArrayResize(MLP_ExitTimes, 0);

   string exits_file = MLP_ExitsFileName();
   if (exits_file == "") return true;

   int handle = FileOpen(exits_file, FILE_READ | FILE_CSV | FILE_ANSI, ';');
   if (handle < 0) {
      Print("MLP_INIT: Cannot open ", exits_file, " Error=", GetLastError(), " ML_CLOSE disabled");
      return true;
   }

   string header_signal_time = FileReadString(handle);
   string header_exit_time = FileReadString(handle);
   if (header_signal_time != "signal_time" || header_exit_time != "exit_time") {
      Print("MLP_INIT: Unexpected header in ", exits_file,
            " first=", header_signal_time, " second=", header_exit_time, " ML_CLOSE disabled");
      FileClose(handle);
      return true;
   }
   while (!FileIsLineEnding(handle)) FileReadString(handle);

   ArrayResize(MLP_ExitSignalTimes, MLP_MAX_SIGNALS);
   ArrayResize(MLP_ExitTimes, MLP_MAX_SIGNALS);

   while (!FileIsEnding(handle) && MLP_ExitCount < MLP_MAX_SIGNALS) {
      string signal_time_str = FileReadString(handle);
      if (signal_time_str == "") {
         while (!FileIsEnding(handle) && !FileIsLineEnding(handle)) FileReadString(handle);
         continue;
      }
      string exit_time_str = FileReadString(handle);
      while (!FileIsLineEnding(handle)) FileReadString(handle);

      datetime parsed_signal_time = StringToTime(signal_time_str);
      datetime parsed_exit_time = StringToTime(exit_time_str);
      if (parsed_signal_time <= 0 || parsed_exit_time <= 0) continue;

      if (MLP_ExitCount > 0 && MLP_ExitSignalTimes[MLP_ExitCount - 1] == parsed_signal_time) {
         MLP_ExitTimes[MLP_ExitCount - 1] = parsed_exit_time;
         continue;
      }
      MLP_ExitSignalTimes[MLP_ExitCount] = parsed_signal_time;
      MLP_ExitTimes[MLP_ExitCount] = parsed_exit_time;
      MLP_ExitCount++;
   }
   FileClose(handle);

   ArrayResize(MLP_ExitSignalTimes, MLP_ExitCount);
   ArrayResize(MLP_ExitTimes, MLP_ExitCount);
   return true;
}

void MLP_LogNoSignal(int magic, datetime barTime) {
   if (!ML_LogNoSignal) return;

   if (MLP_SignalCount <= 0) {
      Print(magic, ":: MLP NO_SIGNAL"
            " bar_time=", TimeToString(barTime),
            " count=0");
      return;
   }

   int pos = MLP_FindSignalInsertPos(barTime);
   string prev_time = "none";
   string next_time = "none";
   int prev_sig = 0;
   int next_sig = 0;

   if (pos > 0) {
      prev_time = TimeToString(MLP_Times[pos - 1]);
      prev_sig = MLP_Signals[pos - 1];
   }
   if (pos < MLP_SignalCount) {
      next_time = TimeToString(MLP_Times[pos]);
      next_sig = MLP_Signals[pos];
   }

   Print(magic, ":: MLP NO_SIGNAL"
         " bar_time=", TimeToString(barTime),
         " first=", TimeToString(MLP_Times[0]),
         " last=", TimeToString(MLP_Times[MLP_SignalCount - 1]),
         " count=", MLP_SignalCount,
         " prev=", prev_time,
         " prev_sig=", prev_sig,
         " next=", next_time,
         " next_sig=", next_sig);
}

void MLP_LogZeroSignal(int magic, datetime barTime, int idx) {
   Print(magic, ":: MLP ZERO_SIGNAL"
         " bar_time=", TimeToString(barTime),
         " signal_time=", TimeToString(MLP_Times[idx]),
         " count=", MLP_SignalCount);
}

bool MLP_INIT() {
   string signals_file = MLP_SignalsFileName();
   datetime file_modify_time = MLP_FileModifyTime();
   int handle = FileOpen(signals_file, FILE_READ | FILE_CSV | FILE_ANSI, ';');
   if (handle < 0) {
      Print("MLP_INIT: Cannot open ", signals_file, " Error=", GetLastError());
      return false;
   }

   string header_time = FileReadString(handle);
   string header_signal = FileReadString(handle);
   if (header_time != "time" || header_signal != "signal") {
      Print("MLP_INIT: Unexpected header in ", signals_file,
            " first=", header_time, " second=", header_signal);
      FileClose(handle);
      return false;
   }

   MLP_HasScoreColumn = false;
   MLP_HasAtrColumn = false;
   MLP_HasStopColumn = false;
   string col3 = "";
   string col4 = "";
   string col5 = "";
   if (!FileIsLineEnding(handle)) col3 = FileReadString(handle);
   if (!FileIsLineEnding(handle)) col4 = FileReadString(handle);
   if (!FileIsLineEnding(handle)) col5 = FileReadString(handle);
   if (col3 == "atr" || col3 == "ATR") MLP_HasAtrColumn = true;
   if (col4 == "stop" || col4 == "protective_stop_price") MLP_HasStopColumn = true;
   if (col5 == "pred_ret_24_dir_atr") MLP_HasScoreColumn = true;
   while (!FileIsLineEnding(handle)) FileReadString(handle);

   ArrayResize(MLP_Times, MLP_MAX_SIGNALS);
   ArrayResize(MLP_Signals, MLP_MAX_SIGNALS);
   ArrayResize(MLP_Scores, MLP_MAX_SIGNALS);
   ArrayResize(MLP_ATRs, MLP_MAX_SIGNALS);
   ArrayResize(MLP_Stops, MLP_MAX_SIGNALS);
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
      double parsed_atr = 0.0;
      double parsed_stop = 0.0;

      if (!FileIsLineEnding(handle)) {
         string value3 = FileReadString(handle);
         if (MLP_HasAtrColumn) parsed_atr = StringToDouble(value3);
      }
      if (!FileIsLineEnding(handle)) {
         string value4 = FileReadString(handle);
         if (MLP_HasStopColumn) parsed_stop = StringToDouble(value4);
      }
      if (!FileIsLineEnding(handle)) {
         string value5 = FileReadString(handle);
         if (MLP_HasScoreColumn) parsed_score = StringToDouble(value5);
      }
      while (!FileIsLineEnding(handle)) FileReadString(handle);

      if (MLP_SignalCount > 0 && MLP_Times[MLP_SignalCount - 1] == parsed_time) {
         MLP_Signals[MLP_SignalCount - 1] = parsed_signal;
         MLP_Scores[MLP_SignalCount - 1] = (float)parsed_score;
         MLP_ATRs[MLP_SignalCount - 1] = (float)parsed_atr;
         MLP_Stops[MLP_SignalCount - 1] = (float)parsed_stop;
         continue;
      }

      MLP_Times[MLP_SignalCount] = parsed_time;
      MLP_Signals[MLP_SignalCount] = parsed_signal;
      MLP_Scores[MLP_SignalCount] = (float)parsed_score;
      MLP_ATRs[MLP_SignalCount] = (float)parsed_atr;
      MLP_Stops[MLP_SignalCount] = (float)parsed_stop;
      MLP_SignalCount++;
   }

   FileClose(handle);

   ArrayResize(MLP_Times, MLP_SignalCount);
   ArrayResize(MLP_Signals, MLP_SignalCount);
   ArrayResize(MLP_Scores, MLP_SignalCount);
   ArrayResize(MLP_ATRs, MLP_SignalCount);
   ArrayResize(MLP_Stops, MLP_SignalCount);
   MLP_LoadExits();
   MLP_Loaded = true;
   MLP_LoadedFileModifyTime = file_modify_time;
   if (MLP_RuntimeStartTime <= 0) MLP_RuntimeStartTime = Time[0];

   if (MLP_SignalCount <= 0) {
      Print("MLP_INIT: Loaded 0 rows from ", signals_file);
      return true;
   }

   Print("MLP_INIT: rule_slot=", ML_RuleSlot,
         " Loaded V", MLP_Ver, " ", MLP_SignalCount, " rows from ", signals_file,
         " Range: ", TimeToString(MLP_Times[0]), " — ", TimeToString(MLP_Times[MLP_SignalCount - 1]),
         " AtrCol=", MLP_HasAtrColumn,
         " StopCol=", MLP_HasStopColumn,
         " ScoreCol=", MLP_HasScoreColumn,
         " ScoreFilter=", ML_UseScoreFilter,
         " Threshold=", DoubleToString(ML_ScoreThreshold, 6),
         " ExitRows=", MLP_ExitCount,
         " ExitMode=", MLP_ExitModeName(),
         " TrailATR=", DoubleToString(ML_TrailATR, 2),
         " TakeProfitATR=", DoubleToString(ML_TakeProfitATR, 2),
         " MaxPositions=", ML_MaxPositions,
         " HoldBars=", ML_HoldBars,
         " Reversal=", ML_AllowReversal);
   if (ML_UseScoreFilter && !MLP_HasScoreColumn) {
      Print("MLP_INIT: pred_ret_24_dir_atr column not found, score filter disabled for this file.");
   }

   return true;
}

void MLP_RELOAD_IF_CHANGED() {
   string signals_file = MLP_SignalsFileName();
   datetime file_modify_time = MLP_FileModifyTime();
   if (!MLP_Loaded) {
      MLP_INIT();
      return;
   }
   if (file_modify_time > 0 && file_modify_time != MLP_LoadedFileModifyTime) {
      Print("MLP_RELOAD: file changed ", signals_file,
            " old=", TimeToString(MLP_LoadedFileModifyTime),
            " new=", TimeToString(file_modify_time));
      MLP_INIT();
   }
}

void MLP_WAIT_RELOAD_IF_NEEDED(datetime barTime) {
   if (Real) {
      datetime start_time = TimeLocal();
      bool ready = false;
      while (TimeLocal() - start_time < MLP_WAIT_SIGNAL_SEC) {
         datetime file_modify_time = MLP_FileModifyTime();
         if (!MLP_Loaded || (file_modify_time > 0 && file_modify_time != MLP_LoadedFileModifyTime)) {
            int waited_sec = (int)(TimeLocal() - start_time);
            Print("MLP_WAIT: file changed after ", waited_sec,
                  " sec bar_time=", TimeToString(barTime),
                  " file_time=", TimeToString(file_modify_time));
            MLP_RELOAD_IF_CHANGED();
            if (MLP_SignalCount > 0 && MLP_Times[MLP_SignalCount - 1] >= barTime) {
               ready = true;
               break;
            }
            if (MLP_SignalCount > 0) {
               Print("MLP_WAIT: file still behind"
                     " bar_time=", TimeToString(barTime),
                     " last=", TimeToString(MLP_Times[MLP_SignalCount - 1]),
                     " count=", MLP_SignalCount);
            }
         }
         Sleep(1000);
      }
      if (!ready && MLP_SignalCount > 0 && MLP_Times[MLP_SignalCount - 1] < barTime) {
         Print("MLP_WAIT: timeout"
               " bar_time=", TimeToString(barTime),
               " last=", TimeToString(MLP_Times[MLP_SignalCount - 1]),
               " count=", MLP_SignalCount);
      }
      return;
   }
   MLP_RELOAD_IF_CHANGED();
}

void EXPERT::ML_TRADE() {
   MLP_WAIT_RELOAD_IF_NEEDED(Time[bar]);
   if (MLP_SignalCount <= 0) {
      return;
   }
   MLP_CheckExpectedSpread(Mgc, Sym);
   MLP_LogBrokerClosedOrders(Mgc, Sym, ATR);
   MLP_LogFilledMarketOrders(Mgc, ExpNum, Sym, ATR);
   MLP_DeleteExpiredPendingOrders(Mgc, ExpNum, Sym, ATR);

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
      if (sig != 0 && ML_MaxPositions <= 1) MLP_cnt_total++;
   }

   if (ML_MaxPositions > 1) {
      MLP_ManageMultiPositions(Mgc, ExpNum, Sym, ATR, sig);

      int entry_idx = -1;
      datetime entry_signal_bar_time = 0;
      double entry_calculation_open = 0.0;
      if (Bars > bar + 1) {
         entry_signal_bar_time = Time[bar + 1];
         entry_idx = MLP_FindSignal(entry_signal_bar_time);
         entry_calculation_open = Open[bar];
      }

      if (entry_idx < 0) {
         MLP_LogNoSignal(Mgc, entry_signal_bar_time);
         return;
      }
      char entry_sig = MLP_Signals[entry_idx];
      double entry_score = MLP_Scores[entry_idx];
      bool entry_score_ok = MLP_PassScore(entry_idx);
      if (entry_sig != 0) MLP_cnt_total++;

      if (entry_sig == 0) {
         MLP_LogZeroSignal(Mgc, entry_signal_bar_time, entry_idx);
         return;
      }

      if (!entry_score_ok) {
         MLP_cnt_filtered++;
         Print(Mgc, ":: MLP SKIP reason=ScoreFilter"
               " sig=", entry_sig,
               " signal_time=", TimeToString(MLP_Times[entry_idx]),
               " score=", DoubleToString(entry_score, 6),
               " threshold=", DoubleToString(ML_ScoreThreshold, 6));
         return;
      }

      int open_positions = MLP_CountOwnWorkingOrders(Mgc, Sym);
      if (open_positions >= ML_MaxPositions) {
         MLP_cnt_posblock++;
         Print(Mgc, ":: MLP SKIP reason=MaxPositions"
               " sig=", entry_sig,
               " signal_time=", TimeToString(MLP_Times[entry_idx]),
               " score=", DoubleToString(entry_score, 6),
               " open_positions=", open_positions,
               " max_positions=", ML_MaxPositions);
         return;
      }

      double entry_atr = ATR;
      if (MLP_ATRs[entry_idx] > 0) entry_atr = MLP_ATRs[entry_idx];
      double entry_stop = 0.0;
      if (MLP_Stops[entry_idx] > 0) entry_stop = MLP_Stops[entry_idx];
      MLP_OpenLimitOrder(Mgc, ExpNum, Sym, entry_sig, entry_score, MLP_Times[entry_idx], entry_calculation_open, entry_atr, entry_stop, open_positions);
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

   if (idx < 0) {
      MLP_LogNoSignal(Mgc, Time[bar]);
      return;
   }
   if (sig == 0) {
      MLP_LogZeroSignal(Mgc, Time[bar], idx);
      return;
   }

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
      if (ML_TakeProfitATR > 0) set.BUY.Prf = (float)(set.BUY.Val + ATR * ML_TakeProfitATR);

      Print(Mgc, ":: MLP BUY"
            " signal_time=", TimeToString(MLP_BuySignalTime),
            " entry_time=", TimeToString(Time[0]),
            " score=", DoubleToString(score, 6),
            " exit_mode=", MLP_ExitModeName(),
            " take_profit_atr=", DoubleToString(ML_TakeProfitATR, 2),
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
      if (ML_TakeProfitATR > 0) set.SEL.Prf = (float)(set.SEL.Val - ATR * ML_TakeProfitATR);

      Print(Mgc, ":: MLP SELL"
            " signal_time=", TimeToString(MLP_SellSignalTime),
            " entry_time=", TimeToString(Time[0]),
            " score=", DoubleToString(score, 6),
            " exit_mode=", MLP_ExitModeName(),
            " take_profit_atr=", DoubleToString(ML_TakeProfitATR, 2),
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
   Print("  ML closes:        ", MLP_cnt_mlclose);
   Print("  Broker TP closes: ", MLP_cnt_broker_take);
   Print("  Broker SL closes: ", MLP_cnt_broker_stop);
   Print("  Broker other closes: ", MLP_cnt_broker_other);
   Print("  ExitMode=", MLP_ExitModeName(),
         "  HoldBars=", ML_HoldBars,
         "  TrailATR=", DoubleToString(ML_TrailATR, 2),
         "  TakeProfitATR=", DoubleToString(ML_TakeProfitATR, 2),
         "  MaxPositions=", ML_MaxPositions,
         "  ScoreFilter=", ML_UseScoreFilter,
         "  Threshold=", DoubleToString(ML_ScoreThreshold, 6),
         "  Reversal=", ML_AllowReversal,
         "  ScoreCol=", MLP_HasScoreColumn);
   Print("======================");
}
