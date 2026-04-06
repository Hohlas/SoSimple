//+------------------------------------------------------------------+
//| MQL4Compat.mqh — MQL4→MQL5 compatibility layer                  |
//| Provides MQL4-style functions/macros for ported code             |
//+------------------------------------------------------------------+
#ifndef MQL4_COMPAT_MQH
#define MQL4_COMPAT_MQH

// ─── Order type constants (MQL4-style) ─────��────────────────────────
#define OP_BUY       0
#define OP_SELL      1
#define OP_BUYLIMIT  2
#define OP_SELLLIMIT 3
#define OP_BUYSTOP   4
#define OP_SELLSTOP  5

// ─── MarketInfo MODE_* constants ────────────────────────────────────
#define MODE_LOW         1
#define MODE_HIGH        2
#define MODE_BID         9
#define MODE_ASK         10
#define MODE_POINT       11
#define MODE_DIGITS      12
#define MODE_SPREAD      13
#define MODE_STOPLEVEL   14
#define MODE_LOTSIZE     15
#define MODE_TICKVALUE   16
#define MODE_TICKSIZE    17
#define MODE_SWAPLONG    18
#define MODE_SWAPSHORT   19
#define MODE_MINLOT      23
#define MODE_LOTSTEP     24
#define MODE_MAXLOT      25
#define MODE_MARGINREQUIRED 31
#define MODE_FREEZELEVEL 33

// ─── Order select modes (MQL4-style) ───────────────────────────────
#define SELECT_BY_POS    0
#define SELECT_BY_TICKET 1
#define MODE_TRADES      0
#define MODE_HISTORY     1

// ─── MQL4 compatibility: Bars ───────────────────────────────────────
int Bars_() { return iBars(_Symbol, _Period); }
#define Bars Bars_()

// ─── Price arrays simulation ────────────────────────────────────────
// MQL5 doesn't have built-in Open[], Close[], High[], Low[], Time[], Volume[]
// We provide them as global arrays that must be refreshed each tick

double _Open[];
double _Close[];
double _High[];
double _Low[];
long   _Volume[];
datetime _Time[];
int    _price_arrays_size = 0;

void RefreshPriceArrays(int count=10000) {
   ArraySetAsSeries(_Open,  true);
   ArraySetAsSeries(_Close, true);
   ArraySetAsSeries(_High,  true);
   ArraySetAsSeries(_Low,   true);
   ArraySetAsSeries(_Volume,true);
   ArraySetAsSeries(_Time,  true);
   int bars = iBars(_Symbol, _Period);
   if (count > bars) count = bars;
   _price_arrays_size = count;
   CopyOpen  (_Symbol, _Period, 0, count, _Open);
   CopyClose (_Symbol, _Period, 0, count, _Close);
   CopyHigh  (_Symbol, _Period, 0, count, _High);
   CopyLow   (_Symbol, _Period, 0, count, _Low);
   CopyTickVolume(_Symbol, _Period, 0, count, _Volume);
   CopyTime  (_Symbol, _Period, 0, count, _Time);
}

// MQL4-style array access via macros
#define Open   _Open
#define Close  _Close
#define High   _High
#define Low    _Low
#define Volume _Volume
#define Time   _Time

// ─── RefreshRates (no-op in MQL5) ──────────────────────────────────
void RefreshRates() { RefreshPriceArrays(_price_arrays_size > 0 ? _price_arrays_size : 10000); }

// ─── Ask / Bid ─────────────────────────────────────────────────────
double Ask_() { return SymbolInfoDouble(_Symbol, SYMBOL_ASK); }
double Bid_() { return SymbolInfoDouble(_Symbol, SYMBOL_BID); }
#define Ask Ask_()
#define Bid Bid_()

// ─── Point / Digits ────────���───────────────────────────────────────
#define Point  _Point
#define Digits _Digits

// ─── MarketInfo ─────���──────────────────────────────────────────────
double MarketInfo(string symbol, int mode) {
   switch(mode) {
      case MODE_LOW:        return SymbolInfoDouble(symbol, SYMBOL_LASTLOW);
      case MODE_HIGH:       return SymbolInfoDouble(symbol, SYMBOL_LASTHIGH);
      case MODE_BID:        return SymbolInfoDouble(symbol, SYMBOL_BID);
      case MODE_ASK:        return SymbolInfoDouble(symbol, SYMBOL_ASK);
      case MODE_POINT:      return SymbolInfoDouble(symbol, SYMBOL_POINT);
      case MODE_DIGITS:     return (double)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
      case MODE_SPREAD:     return (double)SymbolInfoInteger(symbol, SYMBOL_SPREAD);
      case MODE_STOPLEVEL:  return (double)SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL);
      case MODE_LOTSIZE:    return SymbolInfoDouble(symbol, SYMBOL_TRADE_CONTRACT_SIZE);
      case MODE_TICKVALUE:  return SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
      case MODE_TICKSIZE:   return SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
      case MODE_SWAPLONG:   return SymbolInfoDouble(symbol, SYMBOL_SWAP_LONG);
      case MODE_SWAPSHORT:  return SymbolInfoDouble(symbol, SYMBOL_SWAP_SHORT);
      case MODE_MINLOT:     return SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
      case MODE_LOTSTEP:    return SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
      case MODE_MAXLOT:     return SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
      case MODE_MARGINREQUIRED: {
         double margin = 0;
         if (!::OrderCalcMargin(ORDER_TYPE_BUY, symbol, 1.0, SymbolInfoDouble(symbol, SYMBOL_ASK), margin)) return 0;
         return margin;
      }
      case MODE_FREEZELEVEL: return (double)SymbolInfoInteger(symbol, SYMBOL_TRADE_FREEZE_LEVEL);
   }
   return 0;
}

// ─── Time functions ────────────────────────────────────────────────
int TimeDay(datetime time)       { MqlDateTime dt; TimeToStruct(time, dt); return dt.day; }
int TimeMonth(datetime time)     { MqlDateTime dt; TimeToStruct(time, dt); return dt.mon; }
int TimeYear(datetime time)      { MqlDateTime dt; TimeToStruct(time, dt); return dt.year; }
int TimeHour(datetime time)      { MqlDateTime dt; TimeToStruct(time, dt); return dt.hour; }
int TimeMinute(datetime time)    { MqlDateTime dt; TimeToStruct(time, dt); return dt.min; }
int TimeSeconds(datetime time)   { MqlDateTime dt; TimeToStruct(time, dt); return dt.sec; }
int TimeDayOfWeek(datetime time) { MqlDateTime dt; TimeToStruct(time, dt); return dt.day_of_week; }
int TimeDayOfYear(datetime time) { MqlDateTime dt; TimeToStruct(time, dt); return dt.day_of_year; }
int DayOfYear()                  { return TimeDayOfYear(TimeCurrent()); }
int Minute()                     { MqlDateTime dt; TimeToStruct(TimeCurrent(), dt); return dt.min; }

// ─── String functions ─────────��────────────────────────────────────
ushort StringGetChar(string str, int pos) { return StringGetCharacter(str, pos); }
string CharToStr(uchar code)             { return CharToString(code); }
#define StrToDouble  StringToDouble
#define StrToInteger StringToInteger
#define StrToTime    StringToTime
string TimeToStr(datetime time, int mode=TIME_DATE|TIME_MINUTES) { return TimeToString(time, mode); }
string DoubleToStr(double value, int digits) { return DoubleToString(value, digits); }

// ─── StringSetChar (MQL4→MQL5) ─────────────────────────────────────
string StringSetChar(string str, int pos, ushort code) {
   uchar arr[];
   StringToCharArray(str, arr);
   if (pos >= 0 && pos < ArraySize(arr)-1) arr[pos] = (uchar)code;
   string result = CharArrayToString(arr);
   return result;
}

// ─── Account functions ─────��───────────────────────────────────────
double AccountBalance()     { return AccountInfoDouble(ACCOUNT_BALANCE); }
double AccountEquity()      { return AccountInfoDouble(ACCOUNT_EQUITY); }
double AccountFreeMargin()  { return AccountInfoDouble(ACCOUNT_MARGIN_FREE); }
string AccountCompany()     { return AccountInfoString(ACCOUNT_COMPANY); }
string AccountCurrency()    { return AccountInfoString(ACCOUNT_CURRENCY); }

// ─── Environment checks ────────────────────────────────────────────
bool IsTesting()      { return (bool)MQLInfoInteger(MQL_TESTER); }
bool IsOptimization() { return (bool)MQLInfoInteger(MQL_OPTIMIZATION); }
bool IsVisualMode()   { return (bool)MQLInfoInteger(MQL_VISUAL_MODE); }
bool IsDemo()         { return AccountInfoInteger(ACCOUNT_TRADE_MODE) == ACCOUNT_TRADE_MODE_DEMO; }
bool IsConnected()    { return (bool)TerminalInfoInteger(TERMINAL_CONNECTED); }
bool IsTradeContextBusy() { return false; } // MQL5 handles this differently

// ─── iLowest / iHighest ──────────────��────────────────────────��────
int iLowest(string symbol, ENUM_TIMEFRAMES tf, int mode_unused, int count, int start) {
   if (symbol == NULL || symbol == "") symbol = _Symbol;
   if (tf == 0) tf = _Period;
   if (count <= 0) return start;
   double arr[];
   ArraySetAsSeries(arr, true);
   int copied = CopyLow(symbol, tf, start, count, arr);
   if (copied <= 0) return start;
   int idx = ArrayMinimum(arr, 0, copied);
   return start + idx;
}

int iHighest(string symbol, ENUM_TIMEFRAMES tf, int mode_unused, int count, int start) {
   if (symbol == NULL || symbol == "") symbol = _Symbol;
   if (tf == 0) tf = _Period;
   if (count <= 0) return start;
   double arr[];
   ArraySetAsSeries(arr, true);
   int copied = CopyHigh(symbol, tf, start, count, arr);
   if (copied <= 0) return start;
   int idx = ArrayMaximum(arr, 0, copied);
   return start + idx;
}

// ─── ErrorDescription (basic) ──────────────────────────────────────
string ErrorDescription(int code) {
   switch(code) {
      case 0:     return "No error";
      case 4756:  return "Trade request send failed";
      case 10004: return "Requote";
      case 10006: return "Request rejected";
      case 10007: return "Request canceled by trader";
      case 10008: return "Order placed";
      case 10009: return "Request completed";
      case 10010: return "Only part of the request was completed";
      case 10011: return "Request processing error";
      case 10012: return "Request canceled by timeout";
      case 10013: return "Invalid request";
      case 10014: return "Invalid volume in the request";
      case 10015: return "Invalid price in the request";
      case 10016: return "Invalid stops in the request";
      case 10017: return "Trade is disabled";
      case 10018: return "Market is closed";
      case 10019: return "There is not enough money";
      case 10020: return "Prices changed";
      case 10021: return "There are no quotes to process";
      case 10022: return "Invalid order expiration date";
      case 10023: return "Order state changed";
      case 10024: return "Too frequent requests";
      case 10025: return "No changes in request";
      case 10026: return "Autotrading disabled by server";
      case 10027: return "Autotrading disabled by client";
      case 10028: return "Request locked for processing";
      case 10029: return "Order or position frozen";
      case 10030: return "Invalid order filling type";
      case 10031: return "No connection with the trade server";
      case 10032: return "Operation allowed only for live accounts";
      case 10033: return "Pending orders limit reached";
      case 10034: return "Volume limit reached";
      case 10035: return "Invalid or prohibited order type";
      case 10036: return "Position with specified POSITION_IDENTIFIER already closed";
      case 10038: return "Close volume exceeds the current position volume";
      case 10039: return "Close order already exists";
      case 10040: return "Limit of positions reached";
      case 10041: return "Pending order activation request rejected, order canceled";
      case 10042: return "Only long positions allowed";
      case 10043: return "Only short positions allowed";
      case 10044: return "Only position close operations allowed";
      default:    return "Error " + IntegerToString(code);
   }
}

// ─── MQL4 error codes mapped to MQL5 ───────────────────────────────
#define ERR_NO_ERROR                    0
#define ERR_NOT_ENOUGH_MONEY            10019
#define ERR_INVALID_STOPS               10016

// ─── Order functions (MQL4-compatibility layer) ────────────────────
// State for "selected" order/position
struct MQL4OrderState {
   ulong  ticket;
   int    type;        // OP_BUY..OP_SELLSTOP
   double openPrice;
   double stopLoss;
   double takeProfit;
   double lots;
   long   magic;
   string symbol;
   datetime openTime;
   datetime closeTime;
   datetime expiration;
   double profit;
   double swap;
   double commission;
   string comment;
   bool   isHistory;
};
MQL4OrderState g_selectedOrder;

int OrdersTotal_MQL4() {
   return PositionsTotal() + OrdersTotal();
}

bool SelectPendingOrderByTicket_MQL4(ulong ticket) {
   int ordCount = OrdersTotal();
   for (int i = 0; i < ordCount; i++) {
      ulong curTicket = OrderGetTicket(i);
      if (curTicket != ticket) continue;
      g_selectedOrder.ticket    = curTicket;
      g_selectedOrder.openPrice = OrderGetDouble(ORDER_PRICE_OPEN);
      g_selectedOrder.stopLoss  = OrderGetDouble(ORDER_SL);
      g_selectedOrder.takeProfit= OrderGetDouble(ORDER_TP);
      g_selectedOrder.lots      = OrderGetDouble(ORDER_VOLUME_CURRENT);
      g_selectedOrder.magic     = OrderGetInteger(ORDER_MAGIC);
      g_selectedOrder.symbol    = OrderGetString(ORDER_SYMBOL);
      g_selectedOrder.openTime  = (datetime)OrderGetInteger(ORDER_TIME_SETUP);
      g_selectedOrder.expiration= (datetime)OrderGetInteger(ORDER_TIME_EXPIRATION);
      g_selectedOrder.profit    = 0;
      g_selectedOrder.swap      = 0;
      g_selectedOrder.commission= 0;
      g_selectedOrder.comment   = OrderGetString(ORDER_COMMENT);
      g_selectedOrder.isHistory = false;
      long ordType = OrderGetInteger(ORDER_TYPE);
      switch((int)ordType) {
         case ORDER_TYPE_BUY_LIMIT:   g_selectedOrder.type = OP_BUYLIMIT;  break;
         case ORDER_TYPE_SELL_LIMIT:  g_selectedOrder.type = OP_SELLLIMIT; break;
         case ORDER_TYPE_BUY_STOP:    g_selectedOrder.type = OP_BUYSTOP;   break;
         case ORDER_TYPE_SELL_STOP:   g_selectedOrder.type = OP_SELLSTOP;  break;
         case ORDER_TYPE_BUY:         g_selectedOrder.type = OP_BUY;       break;
         case ORDER_TYPE_SELL:        g_selectedOrder.type = OP_SELL;      break;
         default:                     g_selectedOrder.type = -1;           break;
      }
      return true;
   }
   return false;
}

bool OrderSelect_MQL4(int index, int selectMode, int pool=MODE_TRADES) {
   g_selectedOrder.ticket = 0;

   if (selectMode == SELECT_BY_TICKET) {
      ulong ticket = (ulong)index;
      if (pool == MODE_TRADES) {
         if (PositionSelectByTicket(ticket)) {
            g_selectedOrder.ticket    = ticket;
            g_selectedOrder.openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
            g_selectedOrder.stopLoss  = PositionGetDouble(POSITION_SL);
            g_selectedOrder.takeProfit= PositionGetDouble(POSITION_TP);
            g_selectedOrder.lots      = PositionGetDouble(POSITION_VOLUME);
            g_selectedOrder.magic     = PositionGetInteger(POSITION_MAGIC);
            g_selectedOrder.symbol    = PositionGetString(POSITION_SYMBOL);
            g_selectedOrder.openTime  = (datetime)PositionGetInteger(POSITION_TIME);
            g_selectedOrder.expiration= 0;
            g_selectedOrder.profit    = PositionGetDouble(POSITION_PROFIT);
            g_selectedOrder.swap      = PositionGetDouble(POSITION_SWAP);
            g_selectedOrder.commission= 0;
            g_selectedOrder.comment   = PositionGetString(POSITION_COMMENT);
            g_selectedOrder.isHistory = false;
            g_selectedOrder.type      = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? OP_BUY : OP_SELL;
            return true;
         }
         return SelectPendingOrderByTicket_MQL4(ticket);
      }
      if (!HistorySelect(0, TimeCurrent())) return false;
      long dealEntry = HistoryDealGetInteger(ticket, DEAL_ENTRY);
      if (dealEntry != DEAL_ENTRY_OUT && dealEntry != DEAL_ENTRY_INOUT) return false;
      g_selectedOrder.ticket    = ticket;
      g_selectedOrder.openPrice = HistoryDealGetDouble(ticket, DEAL_PRICE);
      g_selectedOrder.stopLoss  = 0;
      g_selectedOrder.takeProfit= 0;
      g_selectedOrder.lots      = HistoryDealGetDouble(ticket, DEAL_VOLUME);
      g_selectedOrder.magic     = HistoryDealGetInteger(ticket, DEAL_MAGIC);
      g_selectedOrder.symbol    = HistoryDealGetString(ticket, DEAL_SYMBOL);
      g_selectedOrder.openTime  = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
      g_selectedOrder.closeTime = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
      g_selectedOrder.profit    = HistoryDealGetDouble(ticket, DEAL_PROFIT);
      g_selectedOrder.swap      = HistoryDealGetDouble(ticket, DEAL_SWAP);
      g_selectedOrder.commission= HistoryDealGetDouble(ticket, DEAL_COMMISSION);
      g_selectedOrder.comment   = HistoryDealGetString(ticket, DEAL_COMMENT);
      g_selectedOrder.isHistory = true;
      g_selectedOrder.type      = (HistoryDealGetInteger(ticket, DEAL_TYPE) == DEAL_TYPE_BUY) ? OP_BUY : OP_SELL;
      return true;
   }

   if (pool == MODE_TRADES) {
      int posCount = PositionsTotal();
      int ordCount = OrdersTotal();

      if (index < posCount) {
         ulong ticket = PositionGetTicket(index);
         if (ticket == 0) return false;
         g_selectedOrder.ticket    = ticket;
         g_selectedOrder.openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
         g_selectedOrder.stopLoss  = PositionGetDouble(POSITION_SL);
         g_selectedOrder.takeProfit= PositionGetDouble(POSITION_TP);
         g_selectedOrder.lots      = PositionGetDouble(POSITION_VOLUME);
         g_selectedOrder.magic     = PositionGetInteger(POSITION_MAGIC);
         g_selectedOrder.symbol    = PositionGetString(POSITION_SYMBOL);
         g_selectedOrder.openTime  = (datetime)PositionGetInteger(POSITION_TIME);
         g_selectedOrder.expiration= 0;
         g_selectedOrder.profit    = PositionGetDouble(POSITION_PROFIT);
         g_selectedOrder.swap      = PositionGetDouble(POSITION_SWAP);
         g_selectedOrder.commission= 0; // MQL5: commission is in deals
         g_selectedOrder.comment   = PositionGetString(POSITION_COMMENT);
         g_selectedOrder.isHistory = false;
         long posType = PositionGetInteger(POSITION_TYPE);
         g_selectedOrder.type = (posType == POSITION_TYPE_BUY) ? OP_BUY : OP_SELL;
         return true;
      }
      else if (index - posCount < ordCount) {
         return SelectPendingOrderByTicket_MQL4(OrderGetTicket(index - posCount));
      }
      return false;
   }
   else { // MODE_HISTORY
      if (!HistorySelect(0, TimeCurrent())) return false;
      int dealsTotal = HistoryDealsTotal();
      int dealIndex = 0;
      for (int i = 0; i < dealsTotal; i++) {
         ulong ticket = HistoryDealGetTicket(i);
         if (ticket == 0) continue;
         long dealEntry = HistoryDealGetInteger(ticket, DEAL_ENTRY);
         if (dealEntry != DEAL_ENTRY_OUT && dealEntry != DEAL_ENTRY_INOUT) continue;
         if (dealIndex == index) {
            g_selectedOrder.ticket    = ticket;
            g_selectedOrder.openPrice = HistoryDealGetDouble(ticket, DEAL_PRICE);
            g_selectedOrder.stopLoss  = 0;
            g_selectedOrder.takeProfit= 0;
            g_selectedOrder.lots      = HistoryDealGetDouble(ticket, DEAL_VOLUME);
            g_selectedOrder.magic     = HistoryDealGetInteger(ticket, DEAL_MAGIC);
            g_selectedOrder.symbol    = HistoryDealGetString(ticket, DEAL_SYMBOL);
            g_selectedOrder.openTime  = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
            g_selectedOrder.closeTime = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
            g_selectedOrder.profit    = HistoryDealGetDouble(ticket, DEAL_PROFIT);
            g_selectedOrder.swap      = HistoryDealGetDouble(ticket, DEAL_SWAP);
            g_selectedOrder.commission= HistoryDealGetDouble(ticket, DEAL_COMMISSION);
            g_selectedOrder.comment   = HistoryDealGetString(ticket, DEAL_COMMENT);
            g_selectedOrder.isHistory = true;
            long dealType = HistoryDealGetInteger(ticket, DEAL_TYPE);
            g_selectedOrder.type = (dealType == DEAL_TYPE_BUY) ? OP_BUY : OP_SELL;
            return true;
         }
         dealIndex++;
      }
      return false;
   }
}

// Order property access (MQL4-style)
int    OrderType()          { return g_selectedOrder.type; }
double OrderOpenPrice()     { return g_selectedOrder.openPrice; }
double OrderStopLoss()      { return g_selectedOrder.stopLoss; }
double OrderTakeProfit()    { return g_selectedOrder.takeProfit; }
double OrderLots()          { return g_selectedOrder.lots; }
long   OrderMagicNumber()   { return g_selectedOrder.magic; }
string OrderSymbol()        { return g_selectedOrder.symbol; }
datetime OrderOpenTime()    { return g_selectedOrder.openTime; }
datetime OrderCloseTime()   { return g_selectedOrder.isHistory ? g_selectedOrder.closeTime : 0; }
datetime OrderExpiration()  { return g_selectedOrder.expiration; }
ulong  OrderTicket()        { return g_selectedOrder.ticket; }
double OrderProfit()        { return g_selectedOrder.profit; }
double OrderSwap()          { return g_selectedOrder.swap; }
double OrderCommission()    { return g_selectedOrder.commission; }
string OrderComment()       { return g_selectedOrder.comment; }

int OrdersHistoryTotal_MQL4() {
   if (!HistorySelect(0, TimeCurrent())) return 0;
   int count = 0;
   int dealsTotal = HistoryDealsTotal();
   for (int i = 0; i < dealsTotal; i++) {
      ulong ticket = HistoryDealGetTicket(i);
      if (ticket == 0) continue;
      long dealEntry = HistoryDealGetInteger(ticket, DEAL_ENTRY);
      if (dealEntry == DEAL_ENTRY_OUT || dealEntry == DEAL_ENTRY_INOUT) count++;
   }
   return count;
}

bool SendTradeRequest_MQL5(MqlTradeRequest &request, MqlTradeResult &result) {
   return OrderSend(request, result);
}

// Redirect MQL4 names
#define OrdersTotal     OrdersTotal_MQL4
#define OrderSelect     OrderSelect_MQL4
#define OrdersHistoryTotal OrdersHistoryTotal_MQL4

// ─── OrderSend (MQL4-style) ────────────────────────────────────────
int OrderSend_MQL4(string symbol, int cmd, double volume, double price,
                    int slippage, double stoploss, double takeprofit,
                    string comment="", int magic=0, datetime expiration=0, color arrow_color=clrNONE) {
   MqlTradeRequest request;
   MqlTradeResult  result;
   ZeroMemory(request);
   ZeroMemory(result);

   request.symbol       = symbol;
   request.volume       = volume;
   request.price        = price;
   request.sl           = stoploss;
   request.tp           = takeprofit;
   request.deviation    = slippage;
   request.magic        = magic;
   request.comment      = comment;
   request.type_filling = ORDER_FILLING_FOK;
   request.type_time    = (expiration > 0) ? ORDER_TIME_SPECIFIED : ORDER_TIME_GTC;
   request.expiration   = expiration;

   switch(cmd) {
      case OP_BUY:       request.action = TRADE_ACTION_DEAL;   request.type = ORDER_TYPE_BUY;        break;
      case OP_SELL:      request.action = TRADE_ACTION_DEAL;   request.type = ORDER_TYPE_SELL;       break;
      case OP_BUYSTOP:   request.action = TRADE_ACTION_PENDING;request.type = ORDER_TYPE_BUY_STOP;   break;
      case OP_SELLSTOP:  request.action = TRADE_ACTION_PENDING;request.type = ORDER_TYPE_SELL_STOP;  break;
      case OP_BUYLIMIT:  request.action = TRADE_ACTION_PENDING;request.type = ORDER_TYPE_BUY_LIMIT;  break;
      case OP_SELLLIMIT: request.action = TRADE_ACTION_PENDING;request.type = ORDER_TYPE_SELL_LIMIT; break;
      default: return -1;
   }

   if (SendTradeRequest_MQL5(request, result)) {
      if (result.order > 0) return (int)result.order;
      if (result.deal > 0)  return (int)result.deal;
   }
   return -1;
}
#define OrderSend OrderSend_MQL4

// ──��� OrderClose (MQL4-style) ────────────────���──────────────────────
bool OrderClose_MQL4(ulong ticket, double lots, double price, int slippage, color arrow_color=clrNONE) {
   if (!PositionSelectByTicket(ticket)) return false;

   MqlTradeRequest request;
   MqlTradeResult  result;
   ZeroMemory(request);
   ZeroMemory(result);

   request.action       = TRADE_ACTION_DEAL;
   request.position     = ticket;
   request.symbol       = PositionGetString(POSITION_SYMBOL);
   request.volume       = lots;
   request.deviation    = slippage;
   request.magic        = (ulong)PositionGetInteger(POSITION_MAGIC);
   request.type_filling = ORDER_FILLING_FOK;
   request.price        = price;
   request.type         = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   return SendTradeRequest_MQL5(request, result);
}
#define OrderClose OrderClose_MQL4

// ─── OrderDelete (MQL4-style) ──────────��───────────────────────────
bool OrderDelete_MQL4(ulong ticket, color arrow_color=clrNONE) {
   MqlTradeRequest request;
   MqlTradeResult  result;
   ZeroMemory(request);
   ZeroMemory(result);

   request.action = TRADE_ACTION_REMOVE;
   request.order  = ticket;
   return SendTradeRequest_MQL5(request, result);
}
#define OrderDelete OrderDelete_MQL4

// ─── OrderModify (MQL4-style) ──────���───────────────────────────────
bool OrderModify_MQL4(ulong ticket, double price, double stoploss, double takeprofit,
                       datetime expiration, color arrow_color=clrNONE) {
   if (PositionSelectByTicket(ticket)) {
      MqlTradeRequest request;
      MqlTradeResult  result;
      ZeroMemory(request);
      ZeroMemory(result);

      request.action   = TRADE_ACTION_SLTP;
      request.position = ticket;
      request.symbol   = PositionGetString(POSITION_SYMBOL);
      request.sl       = stoploss;
      request.tp       = takeprofit;
      return SendTradeRequest_MQL5(request, result);
   }
   if (SelectPendingOrderByTicket_MQL4(ticket)) {
      MqlTradeRequest request;
      MqlTradeResult  result;
      ZeroMemory(request);
      ZeroMemory(result);

      request.action     = TRADE_ACTION_MODIFY;
      request.order      = ticket;
      request.symbol     = g_selectedOrder.symbol;
      request.price      = price;
      request.sl         = stoploss;
      request.tp         = takeprofit;
      request.type_time  = (expiration > 0) ? ORDER_TIME_SPECIFIED : ORDER_TIME_GTC;
      request.expiration = expiration;
      return SendTradeRequest_MQL5(request, result);
   }
   return false;
}
#define OrderModify OrderModify_MQL4

// ─── WindowFind ────────────────────────────────────────────────────
int WindowFind(string name) { return ChartWindowFind(0, name); }

int ObjectsTotal_MQL4() { return ObjectsTotal(0, -1, -1); }

#define ObjectsTotal ObjectsTotal_MQL4
bool ObjectDelete(string name) { return ObjectDelete(0, name); }
string ObjectName(int index) { return ObjectName(0, index, -1, -1); }

// ─── Alert (same in MQL5) ──────────────────────────────────────────
// Alert() works the same in MQL5

// ─── MessageBox (same in MQL5) ─────────────────────────────────────
// MessageBox() works the same in MQL5

// ─── Init/Deinit return codes ──────��───────────────────────────────
#ifndef INIT_SUCCEEDED
#define INIT_SUCCEEDED 0
#endif
#ifndef INIT_FAILED
#define INIT_FAILED    1
#endif

#endif // MQL4_COMPAT_MQH
