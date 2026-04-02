//+------------------------------------------------------------------+
//|                                                   ExportOHLC.mq4 |
//|                                                            Hohla |
//| Экспорт H1 OHLC+ATR14 в CSV для анализа path-ordering барьеров.  |
//| Запускать на графике XAUUSD H1.                                  |
//| Результат: MQL4/Files/XAUUSD_H1_OHLC.csv                        |
//| Потом скопировать в DATA/XAUUSD_H1_OHLC.csv                     |
//+------------------------------------------------------------------+
#property copyright "Hohla"
#property strict
#property show_inputs

extern string FileName = "XAUUSD_H1_OHLC.csv";
extern int AtrPeriod = 14;

void OnStart()
{
   int total = Bars;
   if (total <= 0) {
      Alert("ExportOHLC: нет баров на графике!");
      return;
   }

   int file = FileOpen(FileName, FILE_WRITE | FILE_CSV, ';');
   if (file < 0) {
      Alert("ExportOHLC: не удалось открыть ", FileName, " Error=", GetLastError());
      return;
   }

   // Header
   FileWrite(file, "time", "open", "high", "low", "close", "volume", "atr14");

   // Пишем от старых к новым (bar[Bars-1] → bar[0])
   int count = 0;
   for (int i = total - 1; i >= 0; i--) {
      double atr14 = iATR(Symbol(), PERIOD_H1, AtrPeriod, i);
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
   Alert("ExportOHLC: записано ", count, " баров в ", FileName);
}
