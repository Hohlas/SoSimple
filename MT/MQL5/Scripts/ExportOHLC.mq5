//+------------------------------------------------------------------+
//| ExportOHLC.mq5 — экспорт OHLC в CSV для этапа pair-spread        |
//| Запускать дважды: PERIOD_M5/InpSubdir=M5 и PERIOD_H1/InpSubdir=H1|
//| v3: чанки по 5 лет + подробный Print для диагностики             |
//+------------------------------------------------------------------+
#property script_show_inputs
input string        InpSymbols = "AUDUSD,NZDUSD,USDCAD,EURUSD,GBPUSD,USDCHF,XAUUSD,XAGUSD";
input ENUM_TIMEFRAMES InpTF    = PERIOD_M5;
input datetime      InpFrom    = D'1993.01.01 00:00';
input string        InpSubdir  = "M5";

void OnStart()
{
   string parts[];
   int cnt = StringSplit(InpSymbols, ',', parts);
   datetime now = TimeCurrent();
   Print("=== ExportOHLC start: now=", TimeToString(now), " from=", TimeToString(InpFrom), " tf=", EnumToString(InpTF));
   for(int k = 0; k < cnt; k++)
   {
      string sym = parts[k];
      if(!SymbolSelect(sym, true)) { Print("SymbolSelect failed: ", sym); continue; }
      int dig = (int)SymbolInfoInteger(sym, SYMBOL_DIGITS);
      string fname = InpSubdir + "\\" + sym + "_OHLC.csv";
      int h = FileOpen(fname, FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
      if(h == INVALID_HANDLE) { Print("FileOpen failed: ", fname); continue; }
      FileWrite(h, "time", "open", "high", "low", "close", "volume");
      FileClose(h);

      long totalBars = 0;
      datetime chunkStart = InpFrom;
      datetime prevLastTime = 0;
      int chunkNo = 0;
      while(chunkStart < now)
      {
         chunkNo++;
         datetime chunkEnd = chunkStart + 5 * 366 * 86400;
         if(chunkEnd > now) chunkEnd = now + 86400;

         MqlRates rates[];
         ArraySetAsSeries(rates, false);
         int copied = CopyRates(sym, InpTF, chunkStart, chunkEnd, rates);
         if(copied <= 0)
         {
            Print(sym, " chunk #", chunkNo, " [", TimeToString(chunkStart), " - ", TimeToString(chunkEnd), "] copied=", copied, " err=", GetLastError());
            chunkStart = chunkEnd;
            continue;
         }

         int h2 = FileOpen(fname, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
         if(h2 == INVALID_HANDLE) { Print("FileOpen append failed: ", fname); break; }
         FileSeek(h2, 0, SEEK_END);
         int startIdx = 0;
         if(prevLastTime != 0 && copied > 0 && rates[0].time <= prevLastTime)
            startIdx = 1;
         for(int i = startIdx; i < copied; i++)
         {
            FileWrite(h2, TimeToString(rates[i].time, TIME_DATE | TIME_MINUTES),
                      DoubleToString(rates[i].open, dig),
                      DoubleToString(rates[i].high, dig),
                      DoubleToString(rates[i].low, dig),
                      DoubleToString(rates[i].close, dig),
                      IntegerToString((long)rates[i].tick_volume));
         }
         prevLastTime = rates[copied - 1].time;
         totalBars += (copied - startIdx);
         FileClose(h2);
         Print(sym, " chunk #", chunkNo, " [", TimeToString(chunkStart), " - ", TimeToString(chunkEnd), "] copied=", copied, " appended=", (copied - startIdx), " lastTime=", TimeToString(prevLastTime), " total=", totalBars);
         chunkStart = chunkEnd;
      }
      Print("Exported ", sym, " ", totalBars, " bars -> ", fname, " (", chunkNo, " chunks)");
   }
   Print("=== ExportOHLC finished");
}
