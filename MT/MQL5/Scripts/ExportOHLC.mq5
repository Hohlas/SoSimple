//+------------------------------------------------------------------+
//| ExportOHLC.mq5 — экспорт OHLC в CSV для этапа pair-spread        |
//| Запускать дважды: PERIOD_M5/InpSubdir=M5 и PERIOD_H1/InpSubdir=H1|
//+------------------------------------------------------------------+
#property script_show_inputs
input string        InpSymbols = "AUDUSD,NZDUSD,USDCAD,EURUSD,GBPUSD,USDCHF,XAUUSD,XAGUSD";
input ENUM_TIMEFRAMES InpTF    = PERIOD_M5;
input datetime      InpFrom    = D'2004.01.01 00:00';
input string        InpSubdir  = "M5";

void OnStart()
{
   string parts[];
   int cnt = StringSplit(InpSymbols, ',', parts);
   for(int k = 0; k < cnt; k++)
   {
      string sym = parts[k];
      if(!SymbolSelect(sym, true)) { Print("SymbolSelect failed: ", sym); continue; }
      int dig = (int)SymbolInfoInteger(sym, SYMBOL_DIGITS);
      MqlRates rates[];
      ArraySetAsSeries(rates, false);
      int copied = CopyRates(sym, InpTF, InpFrom, TimeCurrent(), rates);
      if(copied <= 0) { Print("CopyRates failed: ", sym, " err=", GetLastError()); continue; }
      string fname = InpSubdir + "\\" + sym + "_OHLC.csv";
      int h = FileOpen(fname, FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
      if(h == INVALID_HANDLE) { Print("FileOpen failed: ", fname); continue; }
      FileWrite(h, "time", "open", "high", "low", "close", "volume");
      for(int i = 0; i < copied; i++)
      {
         FileWrite(h, TimeToString(rates[i].time, TIME_DATE | TIME_MINUTES),
                   DoubleToString(rates[i].open, dig),
                   DoubleToString(rates[i].high, dig),
                   DoubleToString(rates[i].low, dig),
                   DoubleToString(rates[i].close, dig),
                   IntegerToString((long)rates[i].tick_volume));
      }
      FileClose(h);
      Print("Exported ", sym, " ", copied, " bars -> ", fname);
   }
}
