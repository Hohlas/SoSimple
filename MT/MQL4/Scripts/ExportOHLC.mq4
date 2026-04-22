//+------------------------------------------------------------------+
//|                                                   ExportOHLC.mq4 |
//|                                                            Hohla |
//| Экспорт OHLC+ATR14 в CSV для анализа path-ordering барьеров.     |
//| Запускать на нужном графике: инструмент и таймфрейм берутся с него.|
//| Результат: MQL4/Files/<SYMBOL>_<TF>_OHLC.csv                    |
//| Потом скопировать в DATA/<SYMBOL>_<TF>_OHLC.csv                 |
//+------------------------------------------------------------------+
#property copyright "Hohla"
#property strict
#property show_inputs

extern int AtrPeriod = 14;

string PeriodToName(int period)
{
   switch (period) {
      case PERIOD_M1:  return "M1";
      case PERIOD_M5:  return "M5";
      case PERIOD_M15: return "M15";
      case PERIOD_M30: return "M30";
      case PERIOD_H1:  return "H1";
      case PERIOD_H4:  return "H4";
      case PERIOD_D1:  return "D1";
      case PERIOD_W1:  return "W1";
      case PERIOD_MN1: return "MN1";
      default:         return "M" + IntegerToString(period);
   }
}

string ExportFileName()
{
   return Symbol() + "_" + PeriodToName(Period()) + "_OHLC.csv";
}

void OnStart()
{
   string file_name = ExportFileName();
   int total = Bars;
   if (total <= 0) {
      Alert("ExportOHLC: нет баров на графике!");
      return;
   }

   int file = FileOpen(file_name, FILE_WRITE | FILE_CSV, ';');
   if (file < 0) {
      Alert("ExportOHLC: не удалось открыть ", file_name, " Error=", GetLastError());
      return;
   }

   // Header
   FileWrite(file, "time", "open", "high", "low", "close", "volume", "atr14");

   // Пишем от старых к новым (bar[Bars-1] → bar[0])
   int count = 0;
   for (int i = total - 1; i >= 0; i--) {
      double atr14 = iATR(Symbol(), Period(), AtrPeriod, i);
      FileWrite(file,
         TimeToString(Time[i], TIME_DATE | TIME_MINUTES),
         DoubleToString(Open[i], Digits),
         DoubleToString(High[i], Digits),
         DoubleToString(Low[i], Digits),
         DoubleToString(Close[i], Digits),
         (long)Volume[i],
         DoubleToString(atr14, Digits)
      );
      count++;
   }

   FileClose(file);
   Alert("ExportOHLC: записано ", count, " баров в ", file_name);
}
