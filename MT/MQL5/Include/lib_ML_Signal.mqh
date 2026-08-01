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

// ─── MT5 diagnostic entry-only executor ────────────────────────────

int      MT5_EntrySignalCount = 0;
datetime MT5_EntryTimes[];
datetime MT5_FeatureTimes[];
datetime MT5_FeatureAvailableTimes[];
datetime MT5_DecisionTimes[];
string   MT5_RuleIds[];
string   MT5_Sides[];
string   MT5_EntryTypes[];
double   MT5_LimitPrices[];
double   MT5_StopPrices[];
double   MT5_Atrs[];
int      MT5_MaxFillLagBars[];

bool     MT5_DiagSignalsLoaded = false;
bool     MT5_EventFilePrepared = false;
int      MT5_LastPlacedIdx = -1;
int      MT5_LastPlacedMagic = 0;
datetime MT5_LastPlacedExpiry = 0;
ulong    MT5_TrackedTicket = 0;
int      MT5_TrackedMagic = 0;
int      MT5_TrackedIdx = -1;
bool     MT5_TrackedOpenLogged = false;

// position id -> signal index map (linkage is done in Python via OPEN rows;
// this map keeps the association available on the MQL side as well)
int   MT5_PosMapCount = 0;
ulong MT5_PosMapIds[];
int   MT5_PosMapIdx[];

void MT5_RegisterPosition(ulong position_id, int idx) {
   if (position_id == 0 || idx < 0) return;
   for (int i = 0; i < MT5_PosMapCount; i++) {
      if (MT5_PosMapIds[i] == position_id) { MT5_PosMapIdx[i] = idx; return; }
   }
   ArrayResize(MT5_PosMapIds, MT5_PosMapCount + 1);
   ArrayResize(MT5_PosMapIdx, MT5_PosMapCount + 1);
   MT5_PosMapIds[MT5_PosMapCount] = position_id;
   MT5_PosMapIdx[MT5_PosMapCount] = idx;
   MT5_PosMapCount++;
}

string MT5_TimeText(datetime value) {
   if (value <= 0) return "";
   return TimeToString(value, TIME_DATE | TIME_MINUTES);
}

void MT5_PrepareEventFileIfNeeded() {
   if (MT5_EventFilePrepared) return;
   if (IsTesting()) FileDelete(MT5_EventFile);
   MT5_EventFilePrepared = true;
}

int MT5_OpenPositionsForMagic(int magic) {
   int count = 0;
   for (int i = 0; i < OrdersTotal(); i++) {
      if (OrderSelect(i, SELECT_BY_POS, MODE_TRADES) != true) continue;
      if (OrderMagicNumber() != magic) continue;
      int typ = OrderType();
      if (typ == OP_BUY || typ == OP_SELL) count++;
   }
   return count;
}

ulong MT5_FindActiveTicket(int magic, int typ1, int typ2) {
   for (int i = 0; i < OrdersTotal(); i++) {
      if (OrderSelect(i, SELECT_BY_POS, MODE_TRADES) != true) continue;
      if (OrderMagicNumber() != magic) continue;
      int typ = OrderType();
      if (typ == typ1 || typ == typ2) return (ulong)OrderTicket();
   }
   return 0;
}

int MT5_FindEntrySignal(datetime barTime) {
   for (int i = 0; i < MT5_EntrySignalCount; i++) {
      if (MT5_EntryTimes[i] == barTime) return i;
   }
   return -1;
}

bool MT5_IsEntryTimingValid(datetime feature_time, datetime entry_time, datetime feature_available_time, datetime decision_time) {
   return (feature_time <= entry_time &&
           entry_time < feature_available_time &&
           feature_available_time <= decision_time);
}

void MT5_LogTimingViolation(datetime feature_time,
                            datetime entry_time,
                            datetime feature_available_time,
                            datetime decision_time,
                            string rule_id,
                            string side,
                            string entry_type,
                            double limit_price,
                            double stop_price,
                            double atr_value,
                            string comment) {
   MT5_ML_LogEvent(
      "TIMING_VIOLATION",
      TimeCurrent(),
      feature_time,
      feature_available_time,
      decision_time,
      TimeCurrent(),
      rule_id,
      MT5_TimeText(entry_time),
      0,
      side,
      limit_price,
      0.0,
      0.0,
      0.0,
      stop_price,
      "",
      0.0,
      -1,
      atr_value,
      0,
      0,
      0.0,
      0.0,
      0.0,
      0.0,
      0,
      comment,
      0,
      "",
      0,
      "",
      -1,
      MT5_TrackedMagic,
      Symbol(),
      entry_type
   );
}

double DiagnosticMlExitScore(int bars_since_fill, double unrealized_r, double favorable_r, double adverse_r)
{
   if(bars_since_fill <= 0)
      return 0.0;
   if(adverse_r >= 0.75 && unrealized_r <= 0.0)
      return 1.0;
   if(bars_since_fill >= 24)
      return 1.0;
   return 0.0;
}

bool MT5_CalculateOpenPositionFeatures(
   int order_type,
   double entry_price,
   double stop_price,
   int bars_since_fill,
   double &unrealized_r,
   double &favorable_r,
   double &adverse_r
) {
   unrealized_r = 0.0;
   favorable_r = 0.0;
   adverse_r = 0.0;

   if (bars_since_fill <= 0) return false;
   double risk_r = MathAbs(entry_price - stop_price);
   if (risk_r <= 0.0) return false;

   int fill_shift = bar + bars_since_fill;
   if (fill_shift > Bars) return false;

   bool has_known_bar = false;
   double max_high = 0.0;
   double min_low = 0.0;
   for (int shift = bar; shift < fill_shift; shift++) {
      if (shift < 1 || shift >= Bars) continue;
      if (!has_known_bar) {
         max_high = High[shift];
         min_low = Low[shift];
         has_known_bar = true;
      } else {
         if (High[shift] > max_high) max_high = High[shift];
         if (Low[shift] < min_low) min_low = Low[shift];
      }
   }
   if (!has_known_bar) return false;

   if (order_type == OP_BUY) {
      unrealized_r = (Close[bar] - entry_price) / risk_r;
      favorable_r = (max_high - entry_price) / risk_r;
      adverse_r = (entry_price - min_low) / risk_r;
      return true;
   }
   if (order_type == OP_SELL) {
      unrealized_r = (entry_price - Close[bar]) / risk_r;
      favorable_r = (entry_price - min_low) / risk_r;
      adverse_r = (max_high - entry_price) / risk_r;
      return true;
   }
   return false;
}

void MT5_ML_LogEvent(
   string event_name,
   datetime event_time,
   datetime feature_time,
   datetime feature_available_time,
   datetime decision_time,
   datetime execution_time,
   string rule_id,
   string signal_time,
   ulong ticket,
   string side,
   double requested_price,
   double fill_price,
   double order_open_price,
   double order_close_price,
   double stop_price,
   string close_reason,
   double profit,
   int bars_since_fill,
   double atr_value,
   datetime entry_time,
   datetime exit_time,
   double unrealized_r,
   double favorable_r,
   double adverse_r,
   double ml_exit_score,
   int ml_exit_decision,
   string comment,
   int error_code = 0,
   string error_class = "",
   int retcode = 0,
   string retcode_text = "",
   int request_seq = -1,
   int magic = 0,
   string symbol_name = "",
   string entry_type = ""
) {
   if (!MT5_DiagnosticExecutor) return;
   MT5_PrepareEventFileIfNeeded();

   int handle = FileOpen(MT5_EventFile, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if (handle == INVALID_HANDLE) {
      Print("MT5_ML_LogEvent: Cannot open ", MT5_EventFile, " Error=", GetLastError());
      return;
   }

   if (FileSize(handle) == 0) {
      FileWrite(handle, "event", "time", "feature_time", "feature_available_time", "decision_time", "execution_time", "rule_id", "signal_time", "error_code", "error_class", "retcode", "retcode_text", "request_seq", "magic", "symbol", "entry_type", "ticket", "side", "requested_price", "fill_price", "order_open_price", "order_close_price", "stop_price", "close_reason", "profit", "bars_since_fill", "bid", "ask", "spread", "spread_atr", "bar_open", "bar_high", "bar_low", "bar_close", "calculation_open", "slippage_points", "entry", "take_profit", "close", "swap", "commission", "hold_bars", "open_positions", "max_positions", "balance", "equity", "entry_time", "exit_time", "unrealized_pnl_r_before_decision", "max_favorable_r_before_decision", "max_adverse_r_before_decision", "ml_exit_score", "ml_exit_decision", "comment");
   }

   FileSeek(handle, 0, SEEK_END);
   RefreshRates();
   double spread_value = Ask - Bid;
   double spread_atr = (atr_value > 0.0 ? spread_value / atr_value : 0.0);
   double slippage_points = (Point > 0.0 ? MathAbs(fill_price - requested_price) / Point : 0.0);
   int open_positions = MT5_OpenPositionsForMagic(MT5_TrackedMagic);
   int event_magic = (magic != 0 ? magic : MT5_TrackedMagic);
   string event_symbol = (symbol_name != "" ? symbol_name : Symbol());

   FileWrite(handle,
      event_name,
      MT5_TimeText(event_time),
      MT5_TimeText(feature_time),
      MT5_TimeText(feature_available_time),
      MT5_TimeText(decision_time),
      MT5_TimeText(execution_time),
      rule_id,
      signal_time,
      error_code,
      error_class,
      retcode,
      retcode_text,
      request_seq,
      event_magic,
      event_symbol,
      entry_type,
      (string)ticket,
      side,
      requested_price,
      fill_price,
      order_open_price,
      order_close_price,
      stop_price,
      close_reason,
      profit,
      bars_since_fill,
      Bid,
      Ask,
      spread_value,
      spread_atr,
      Open[bar],
      High[bar],
      Low[bar],
      Close[bar],
      Open[bar],
      slippage_points,
      order_open_price,
      0.0,
      order_close_price,
      0.0,
      0.0,
      bars_since_fill,
      open_positions,
      1,
      AccountBalance(),
      AccountEquity(),
      MT5_TimeText(entry_time),
      MT5_TimeText(exit_time),
      unrealized_r,
      favorable_r,
      adverse_r,
      ml_exit_score,
      ml_exit_decision,
      comment
   );
   FileClose(handle);
}

void MT5_LogSignalEvent(string event_name, int idx, ulong ticket, string comment) {
   if (idx < 0 || idx >= MT5_EntrySignalCount) return;
   string error_class = (event_name == "OPEN_FAILED" ? comment : "");
   MT5_ML_LogEvent(
      event_name,
      TimeCurrent(),
      MT5_FeatureTimes[idx],
      MT5_FeatureAvailableTimes[idx],
      MT5_DecisionTimes[idx],
      TimeCurrent(),
      MT5_RuleIds[idx],
      MT5_TimeText(MT5_EntryTimes[idx]),
      ticket,
      MT5_Sides[idx],
      MT5_LimitPrices[idx],
      0.0,
      0.0,
      0.0,
      MT5_StopPrices[idx],
      "",
      0.0,
      -1,
      MT5_Atrs[idx],
      0,
      0,
      0.0,
      0.0,
      0.0,
      0.0,
      0,
      comment,
      0,
      error_class,
      0,
      "",
      idx,
      MT5_TrackedMagic,
      Symbol(),
      MT5_EntryTypes[idx]
   );
}

string MT5_DealReasonText(long reason) {
   switch ((int)reason) {
      case DEAL_REASON_CLIENT:   return "CLIENT";
      case DEAL_REASON_MOBILE:   return "MOBILE";
      case DEAL_REASON_WEB:      return "WEB";
      case DEAL_REASON_EXPERT:   return "EXPERT";
      case DEAL_REASON_SL:       return "SL";
      case DEAL_REASON_TP:       return "TP";
      case DEAL_REASON_SO:       return "SO";
      case DEAL_REASON_ROLLOVER: return "ROLLOVER";
      case DEAL_REASON_VMARGIN:  return "VMARGIN";
      case DEAL_REASON_SPLIT:    return "SPLIT";
      default:                   return "REASON_" + (string)reason;
   }
}

void MT5_LogTxRow(string event_name, ulong deal_ticket, long position_id, string side,
                  double deal_price, double deal_profit, string reason_text,
                  datetime deal_time, string close_reason) {
   string tx_comment = "position_id=" + (string)position_id +
                       "|deal=" + (string)deal_ticket +
                       "|reason=" + reason_text;
   MT5_ML_LogEvent(
      event_name,
      deal_time,
      0, 0, 0,
      deal_time,
      "",              // rule_id: linkage done in Python reconciliation
      "",              // signal_time
      deal_ticket,
      side,
      0.0,             // requested_price
      deal_price,      // fill_price
      deal_price,      // order_open_price
      (event_name == "TX_CLOSE" ? deal_price : 0.0),
      0.0,             // stop_price
      close_reason,
      deal_profit,
      -1,              // bars_since_fill: INIT convention
      0.0,             // atr_value
      (event_name == "TX_OPEN" ? deal_time : 0),
      (event_name == "TX_CLOSE" ? deal_time : 0),
      0.0, 0.0, 0.0, 0.0, 0,
      tx_comment
   );
}

void MT5_OnTradeTransaction(const MqlTradeTransaction &trans) {
   if (!MT5_DiagnosticExecutor) return;
   if (trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
   if (trans.deal == 0) return;
   if (!HistoryDealSelect(trans.deal)) {
      Print("MT5_OnTradeTransaction: HistoryDealSelect failed for deal ", trans.deal, " Error=", GetLastError());
      return;
   }

   long deal_entry = HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
   long deal_type = HistoryDealGetInteger(trans.deal, DEAL_TYPE);
   if (deal_type != DEAL_TYPE_BUY && deal_type != DEAL_TYPE_SELL) return; // balance/credit deals

   long position_id = HistoryDealGetInteger(trans.deal, DEAL_POSITION_ID);
   long reason = HistoryDealGetInteger(trans.deal, DEAL_REASON);
   double deal_price = HistoryDealGetDouble(trans.deal, DEAL_PRICE);
   double deal_profit = HistoryDealGetDouble(trans.deal, DEAL_PROFIT);
   datetime deal_time = (datetime)HistoryDealGetInteger(trans.deal, DEAL_TIME);
   string side = (deal_type == DEAL_TYPE_BUY ? "BUY" : "SELL");
   string reason_text = MT5_DealReasonText(reason);

   if (deal_entry == DEAL_ENTRY_IN) {
      MT5_LogTxRow("TX_OPEN", trans.deal, position_id, side, deal_price, deal_profit, reason_text, deal_time, "");
   } else if (deal_entry == DEAL_ENTRY_OUT || deal_entry == DEAL_ENTRY_OUT_BY) {
      MT5_LogTxRow("TX_CLOSE", trans.deal, position_id, side, deal_price, deal_profit, reason_text, deal_time, reason_text);
   } else if (deal_entry == DEAL_ENTRY_INOUT) {
      // reversal: expected impossible in this executor; log both legs and flag in report
      MT5_LogTxRow("TX_CLOSE", trans.deal, position_id, side, deal_price, deal_profit, reason_text, deal_time, reason_text);
      MT5_LogTxRow("TX_OPEN", trans.deal, position_id, side, deal_price, deal_profit, reason_text, deal_time, "");
      Print("MT5_OnTradeTransaction: unexpected DEAL_ENTRY_INOUT deal=", trans.deal, " position_id=", position_id);
   }
}

bool MT5_ENTRY_INIT() {
   int handle = FileOpen(MT5_EntrySignalFile, FILE_READ | FILE_CSV | FILE_ANSI, ';');
   if (handle < 0) {
      Print("MT5_ENTRY_INIT: Cannot open ", MT5_EntrySignalFile, " Error=", GetLastError());
      MT5_ML_LogEvent("INIT", TimeCurrent(), 0, 0, 0, TimeCurrent(), "", "", 0, "", 0.0, 0.0, 0.0, 0.0, 0.0, "", 0.0, -1, 0.0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0, "entry_signal_file_open_failed");
      return false;
   }

   for (int h = 0; h < 11; h++) FileReadString(handle);

   ArrayResize(MT5_EntryTimes,  ML_MAX_SIGNALS);
   ArrayResize(MT5_FeatureTimes, ML_MAX_SIGNALS);
   ArrayResize(MT5_FeatureAvailableTimes, ML_MAX_SIGNALS);
   ArrayResize(MT5_DecisionTimes, ML_MAX_SIGNALS);
   ArrayResize(MT5_RuleIds, ML_MAX_SIGNALS);
   ArrayResize(MT5_Sides, ML_MAX_SIGNALS);
   ArrayResize(MT5_EntryTypes, ML_MAX_SIGNALS);
   ArrayResize(MT5_LimitPrices, ML_MAX_SIGNALS);
   ArrayResize(MT5_StopPrices, ML_MAX_SIGNALS);
   ArrayResize(MT5_Atrs, ML_MAX_SIGNALS);
   ArrayResize(MT5_MaxFillLagBars, ML_MAX_SIGNALS);

   MT5_EntrySignalCount = 0;
   while (!FileIsEnding(handle) && MT5_EntrySignalCount < ML_MAX_SIGNALS) {
      string time_str = FileReadString(handle);
      if (time_str == "") break;

      datetime entry_time = StringToTime(time_str);
      datetime feature_time = StringToTime(FileReadString(handle));
      datetime feature_available_time = StringToTime(FileReadString(handle));
      datetime decision_time = StringToTime(FileReadString(handle));
      string rule_id = FileReadString(handle);
      string side = FileReadString(handle);
      string entry_type = FileReadString(handle);
      double limit_price = StringToDouble(FileReadString(handle));
      double stop_price = StringToDouble(FileReadString(handle));
      double atr_value = StringToDouble(FileReadString(handle));
      int max_fill_lag_bars = (int)StringToInteger(FileReadString(handle));

      if (!MT5_IsEntryTimingValid(feature_time, entry_time, feature_available_time, decision_time)) {
         MT5_LogTimingViolation(
            feature_time,
            entry_time,
            feature_available_time,
            decision_time,
            rule_id,
            side,
            entry_type,
            limit_price,
            stop_price,
            atr_value,
            "feature_time <= time < feature_available_time <= decision_time"
         );
         continue;
      }

      int i = MT5_EntrySignalCount;
      MT5_EntryTimes[i] = entry_time;
      MT5_FeatureTimes[i] = feature_time;
      MT5_FeatureAvailableTimes[i] = feature_available_time;
      MT5_DecisionTimes[i] = decision_time;
      MT5_RuleIds[i] = rule_id;
      MT5_Sides[i] = side;
      MT5_EntryTypes[i] = entry_type;
      MT5_LimitPrices[i] = limit_price;
      MT5_StopPrices[i] = stop_price;
      MT5_Atrs[i] = atr_value;
      MT5_MaxFillLagBars[i] = max_fill_lag_bars;
      MT5_EntrySignalCount++;
   }
   FileClose(handle);

   ArrayResize(MT5_EntryTimes, MT5_EntrySignalCount);
   ArrayResize(MT5_FeatureTimes, MT5_EntrySignalCount);
   ArrayResize(MT5_FeatureAvailableTimes, MT5_EntrySignalCount);
   ArrayResize(MT5_DecisionTimes, MT5_EntrySignalCount);
   ArrayResize(MT5_RuleIds, MT5_EntrySignalCount);
   ArrayResize(MT5_Sides, MT5_EntrySignalCount);
   ArrayResize(MT5_EntryTypes, MT5_EntrySignalCount);
   ArrayResize(MT5_LimitPrices, MT5_EntrySignalCount);
   ArrayResize(MT5_StopPrices, MT5_EntrySignalCount);
   ArrayResize(MT5_Atrs, MT5_EntrySignalCount);
   ArrayResize(MT5_MaxFillLagBars, MT5_EntrySignalCount);

   Print("MT5_ENTRY_INIT: Loaded ", MT5_EntrySignalCount, " diagnostic entry signals from ", MT5_EntrySignalFile);
   MT5_ML_LogEvent("INIT", TimeCurrent(), 0, 0, 0, TimeCurrent(), "", "", 0, "", 0.0, 0.0, 0.0, 0.0, 0.0, "", 0.0, -1, 0.0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0, "loaded=" + S0(MT5_EntrySignalCount));
   return true;
}

void MT5_LogLifecycleForCurrentState(int magic, int &ml_close_order_type) {
   ml_close_order_type = -1;

   if (MT5_LastPlacedIdx >= 0 && MT5_LastPlacedMagic == magic) {
      ulong buy_pending = MT5_FindActiveTicket(magic, OP_BUYLIMIT, OP_BUYSTOP);
      ulong sell_pending = MT5_FindActiveTicket(magic, OP_SELLLIMIT, OP_SELLSTOP);
      ulong buy_market = MT5_FindActiveTicket(magic, OP_BUY, OP_BUY);
      ulong sell_market = MT5_FindActiveTicket(magic, OP_SELL, OP_SELL);
      if (buy_market > 0 || sell_market > 0) {
         MT5_TrackedTicket = (buy_market > 0 ? buy_market : sell_market);
         MT5_TrackedMagic = magic;
         MT5_TrackedIdx = MT5_LastPlacedIdx;
         MT5_TrackedOpenLogged = false;
         MT5_RegisterPosition(MT5_TrackedTicket, MT5_TrackedIdx);
         MT5_LastPlacedIdx = -1;
      } else if (buy_pending == 0 && sell_pending == 0 && MT5_LastPlacedExpiry > 0 && TimeCurrent() > MT5_LastPlacedExpiry) {
         MT5_LogSignalEvent("ORDER_EXPIRED", MT5_LastPlacedIdx, 0, "pending order not active after max_fill_lag_bars");
         MT5_LastPlacedIdx = -1;
      } else if (buy_pending == 0 && sell_pending == 0) {
         MT5_LogSignalEvent("OPEN_FAILED", MT5_LastPlacedIdx, 0, "pending order was not found after ORDER_PLACED");
         MT5_LastPlacedIdx = -1;
      }
   }

   if (MT5_TrackedTicket > 0 && OrderSelect((int)MT5_TrackedTicket, SELECT_BY_TICKET, MODE_TRADES) == true) {
      int typ = OrderType();
      if (typ == OP_BUY || typ == OP_SELL) {
         int idx = MT5_TrackedIdx;
         int bars_since_fill = (int)MathMax(0, SHIFT(OrderOpenTime()) - bar);
         if (!MT5_TrackedOpenLogged) {
            MT5_ML_LogEvent("OPEN", TimeCurrent(), MT5_FeatureTimes[idx], MT5_FeatureAvailableTimes[idx], MT5_DecisionTimes[idx], OrderOpenTime(), MT5_RuleIds[idx], MT5_TimeText(MT5_EntryTimes[idx]), MT5_TrackedTicket, MT5_Sides[idx], MT5_LimitPrices[idx], OrderOpenPrice(), OrderOpenPrice(), 0.0, OrderStopLoss(), "", 0.0, bars_since_fill, MT5_Atrs[idx], OrderOpenTime(), 0, 0.0, 0.0, 0.0, 0.0, 0, "tester fill observed", 0, "", 0, "", idx, magic, Symbol(), MT5_EntryTypes[idx]);
            MT5_TrackedOpenLogged = true;
         }
         double unrealized_r = 0.0;
         double favorable_r = 0.0;
         double adverse_r = 0.0;
         bool features_ready = MT5_CalculateOpenPositionFeatures(typ, OrderOpenPrice(), OrderStopLoss(), bars_since_fill, unrealized_r, favorable_r, adverse_r);
         int ml_exit_decision = 0;
         double ml_exit_score = 0.0;
         if (MT5_BlockBarsSinceFill0Exit && bars_since_fill <= 0) {
            ml_exit_decision = 0;
         } else if (features_ready) {
            ml_exit_score = DiagnosticMlExitScore(bars_since_fill, unrealized_r, favorable_r, adverse_r);
            ml_exit_decision = (ml_exit_score >= 1.0 ? 1 : 0);
         }
         string eval_comment = (features_ready ? "diagnostic eval only" : "diagnostic eval skipped: post-fill features not ready");
         MT5_ML_LogEvent("ML_EVAL", TimeCurrent(), MT5_FeatureTimes[idx], MT5_FeatureAvailableTimes[idx], MT5_DecisionTimes[idx], TimeCurrent(), MT5_RuleIds[idx], MT5_TimeText(MT5_EntryTimes[idx]), MT5_TrackedTicket, MT5_Sides[idx], MT5_LimitPrices[idx], OrderOpenPrice(), OrderOpenPrice(), 0.0, OrderStopLoss(), "", OrderProfit(), bars_since_fill, MT5_Atrs[idx], OrderOpenTime(), 0, unrealized_r, favorable_r, adverse_r, ml_exit_score, ml_exit_decision, eval_comment, 0, "", 0, "", idx, magic, Symbol(), MT5_EntryTypes[idx]);
         if (ml_exit_decision == 1) {
            double close_price = (typ == OP_BUY ? Bid : Ask);
            MT5_ML_LogEvent("ML_CLOSE", TimeCurrent(), MT5_FeatureTimes[idx], MT5_FeatureAvailableTimes[idx], MT5_DecisionTimes[idx], TimeCurrent(), MT5_RuleIds[idx], MT5_TimeText(MT5_EntryTimes[idx]), MT5_TrackedTicket, MT5_Sides[idx], MT5_LimitPrices[idx], OrderOpenPrice(), OrderOpenPrice(), close_price, OrderStopLoss(), "ML_CLOSE", OrderProfit(), bars_since_fill, MT5_Atrs[idx], OrderOpenTime(), TimeCurrent(), unrealized_r, favorable_r, adverse_r, ml_exit_score, ml_exit_decision, "diagnostic ml exit requested", 0, "", 0, "", idx, magic, Symbol(), MT5_EntryTypes[idx]);
            ml_close_order_type = typ;
         }
      }
      return;
   }

   if (MT5_TrackedTicket > 0 && OrderSelect((int)MT5_TrackedTicket, SELECT_BY_TICKET, MODE_HISTORY) == true) {
      int idx = MT5_TrackedIdx;
      if (idx >= 0 && idx < MT5_EntrySignalCount) {
         int bars_since_fill = (int)MathMax(0, SHIFT(OrderOpenTime()) - SHIFT(OrderCloseTime()));
         MT5_ML_LogEvent("CLOSE", TimeCurrent(), MT5_FeatureTimes[idx], MT5_FeatureAvailableTimes[idx], MT5_DecisionTimes[idx], OrderCloseTime(), MT5_RuleIds[idx], MT5_TimeText(MT5_EntryTimes[idx]), MT5_TrackedTicket, MT5_Sides[idx], MT5_LimitPrices[idx], OrderOpenPrice(), OrderOpenPrice(), OrderOpenPrice(), OrderStopLoss(), "broker_history_limited", OrderProfit(), bars_since_fill, MT5_Atrs[idx], OrderOpenTime(), OrderCloseTime(), 0.0, 0.0, 0.0, 0.0, 0, "history price/reason is limited in Task 4", 0, "", 0, "", idx, magic, Symbol(), MT5_EntryTypes[idx]);
      }
      MT5_TrackedTicket = 0;
      MT5_TrackedIdx = -1;
      MT5_TrackedOpenLogged = false;
   }
}

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
   if (MT5_DiagnosticExecutor) {
      if (!MT5_DiagSignalsLoaded) {
         MT5_DiagSignalsLoaded = true;
         MT5_ENTRY_INIT();
      }
      MT5_TrackedMagic = Mgc;
      int mt5_close_order_type = -1;
      MT5_LogLifecycleForCurrentState(Mgc, mt5_close_order_type);
      if (mt5_close_order_type == OP_BUY) {
         BUY.Val = 0;
         return;
      }
      if (mt5_close_order_type == OP_SELL) {
         SEL.Val = 0;
         return;
      }
      if (MT5_EntrySignalCount <= 0) return;

      int mt5_idx = MT5_FindEntrySignal(Time[bar]);
      if (mt5_idx < 0) return;
      if (BUY.Typ != NONE || SEL.Typ != NONE) {
         MT5_LogSignalEvent("OPEN_FAILED", mt5_idx, 0, "position_or_pending_order_exists");
         return;
      }

      string side = MT5_Sides[mt5_idx];
      string entry_type = MT5_EntryTypes[mt5_idx];
      double limit_price = MT5_LimitPrices[mt5_idx];
      double stop_price = MT5_StopPrices[mt5_idx];
      int max_fill_lag_bars = MT5_MaxFillLagBars[mt5_idx];
      datetime expiry = 0;
      if (max_fill_lag_bars > 0) expiry = MT5_DecisionTimes[mt5_idx] + datetime(max_fill_lag_bars * Period() * 60);

      bool is_buy_limit = (side == "BUY" || side == "LONG" || side == "1") && (entry_type == "BUY_LIMIT" || entry_type == "LIMIT");
      bool is_sell_limit = (side == "SELL" || side == "SHORT" || side == "-1") && (entry_type == "SELL_LIMIT" || entry_type == "LIMIT");

      if (limit_price <= 0.0 || stop_price <= 0.0) {
         MT5_LogSignalEvent("OPEN_FAILED", mt5_idx, 0, "limit_price_or_stop_price_not_positive");
         return;
      }

      if (is_buy_limit) {
         if (limit_price >= Ask - StopLevel || stop_price >= limit_price) {
            MT5_LogSignalEvent("OPEN_FAILED", mt5_idx, 0, "BUY_LIMIT price/stop invalid for current market");
            return;
         }
         set.BUY.Sig = GOGO;
         set.BUY.Val = (float)limit_price;
         set.BUY.Stp = (float)stop_price;
         set.BUY.Prf = 0;
         set.BUY.Exp = expiry;
         UP = 1;
         MT5_LastPlacedIdx = mt5_idx;
         MT5_LastPlacedMagic = Mgc;
         MT5_LastPlacedExpiry = expiry;
         MT5_LogSignalEvent("ORDER_PLACED", mt5_idx, 0, "set.BUY path prepared");
         return;
      }

      if (is_sell_limit) {
         if (limit_price <= Bid + StopLevel || stop_price <= limit_price) {
            MT5_LogSignalEvent("OPEN_FAILED", mt5_idx, 0, "SELL_LIMIT price/stop invalid for current market");
            return;
         }
         set.SEL.Sig = GOGO;
         set.SEL.Val = (float)limit_price;
         set.SEL.Stp = (float)stop_price;
         set.SEL.Prf = 0;
         set.SEL.Exp = expiry;
         DN = 1;
         MT5_LastPlacedIdx = mt5_idx;
         MT5_LastPlacedMagic = Mgc;
         MT5_LastPlacedExpiry = expiry;
         MT5_LogSignalEvent("ORDER_PLACED", mt5_idx, 0, "set.SEL path prepared");
         return;
      }

      MT5_LogSignalEvent("OPEN_FAILED", mt5_idx, 0, "unsupported side or entry_type");
      return;
   }

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
