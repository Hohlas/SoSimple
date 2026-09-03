//+------------------------------------------------------------------+
//| ExportSymbolSpecs.mq5 — снимок спредов/свопов для cost model     |
//+------------------------------------------------------------------+
void OnStart()
{
   string syms[8] = {"AUDUSD","NZDUSD","USDCAD","EURUSD","GBPUSD","USDCHF","XAUUSD","XAGUSD"};
   int h = FileOpen("pair_spread_costs_snapshot.csv", FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if(h == INVALID_HANDLE) { Print("FileOpen failed"); return; }
   FileWrite(h, "symbol", "point", "spread_points", "spread_price", "swap_long", "swap_short", "digits");
   for(int k = 0; k < 8; k++)
   {
      string sym = syms[k];
      if(!SymbolSelect(sym, true)) continue;
      double pt = SymbolInfoDouble(sym, SYMBOL_POINT);
      long   sp = SymbolInfoInteger(sym, SYMBOL_SPREAD);
      FileWrite(h, sym,
                DoubleToString(pt, 8),
                IntegerToString(sp),
                DoubleToString(sp * pt, 8),
                DoubleToString(SymbolInfoDouble(sym, SYMBOL_SWAP_LONG), 2),
                DoubleToString(SymbolInfoDouble(sym, SYMBOL_SWAP_SHORT), 2),
                IntegerToString(SymbolInfoInteger(sym, SYMBOL_DIGITS)));
   }
   FileClose(h);
   Print("Specs exported");
}
