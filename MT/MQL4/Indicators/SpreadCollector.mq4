//+------------------------------------------------------------------+
//|                                          SpreadCollector.mq4      |
//|  collecting per-bar spread min+max in points for calibration      |
//+------------------------------------------------------------------+
#property copyright "SoSimple"
#property link      ""
#property description "Collects spread_min and spread_max per bar in points, writes CSV"
#property strict

#property indicator_separate_window
#property indicator_buffers 2
#property indicator_color1 clrBlack
#property indicator_color2 clrGainsboro
#property indicator_width1 3

string g_fileName;
int g_fileHandle;
double ExtSpreadMin[];
double ExtSpreadMax[];
datetime g_currentBarTime;
double g_barSpreadMin;
double g_barSpreadMax;
bool g_hasBarData;

int OnInit() {
   IndicatorBuffers(2);
   IndicatorDigits(1);

   SetIndexBuffer(0, ExtSpreadMax);
   SetIndexBuffer(1, ExtSpreadMin);
   SetIndexStyle(0, DRAW_HISTOGRAM);
   SetIndexStyle(1, DRAW_NONE);
   SetIndexLabel(0, "Max");
   SetIndexLabel(1, "Min");

   IndicatorShortName("SpreadCollector");

   // all arrays as non-series (0 = oldest) for consistency with time[]
   ArraySetAsSeries(ExtSpreadMin, false);
   ArraySetAsSeries(ExtSpreadMax, false);

   g_currentBarTime = 0;
   g_hasBarData = false;
   g_barSpreadMin = 0;
   g_barSpreadMax = 0;

   g_fileName = "spread_" + Symbol() + "_stats.csv";
   g_fileHandle = FileOpen(g_fileName, FILE_READ | FILE_WRITE | FILE_ANSI);
   if (g_fileHandle != INVALID_HANDLE) {
      if (FileSize(g_fileHandle) == 0) {
         string header = "Time;Min;Max\r\n";
         FileWriteString(g_fileHandle, header, -1);
         FileFlush(g_fileHandle);
      }
      FileSeek(g_fileHandle, 0, SEEK_END);
   }

   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason) {
   if (g_hasBarData) {
      writeCurrentBar();
   }
   if (g_fileHandle != INVALID_HANDLE) {
      FileFlush(g_fileHandle);
      FileClose(g_fileHandle);
      g_fileHandle = INVALID_HANDLE;
   }
}

int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[]) {

   if (rates_total < 2) return 0;

   ArraySetAsSeries(time, false);  // 0 = oldest, rates_total-1 = newest

   int cur = rates_total - 1;  // current (newest) bar index

   if (prev_calculated == 0) {
      for (int i = 0; i < rates_total; i++) {
         ExtSpreadMin[i] = 0;
         ExtSpreadMax[i] = 0;
      }
      RefreshRates();
      g_currentBarTime = time[cur];
      g_barSpreadMin = (Ask - Bid) / Point;
      g_barSpreadMax = g_barSpreadMin;
      g_hasBarData = true;
      ExtSpreadMin[cur] = g_barSpreadMin;
      ExtSpreadMax[cur] = g_barSpreadMax;
      return rates_total;
   }

   RefreshRates();
   double now_pts = (Ask - Bid) / Point;

   if (time[cur] != g_currentBarTime) {
      if (g_hasBarData) {
         writeCurrentBar();
      }
      g_currentBarTime = time[cur];
      g_barSpreadMin = now_pts;
      g_barSpreadMax = now_pts;
   } else {
      if (now_pts < g_barSpreadMin) g_barSpreadMin = now_pts;
      if (now_pts > g_barSpreadMax) g_barSpreadMax = now_pts;
   }
   g_hasBarData = true;

   ExtSpreadMin[cur] = g_barSpreadMin;
   ExtSpreadMax[cur] = g_barSpreadMax;

   return rates_total;
}

void writeCurrentBar() {
   if (g_fileHandle == INVALID_HANDLE) return;
   string row = TimeToString(g_currentBarTime, TIME_DATE | TIME_MINUTES)
              + ";" + DoubleToString(g_barSpreadMin, 1)
              + ";" + DoubleToString(g_barSpreadMax, 1)
              + "\r\n";
   FileWriteString(g_fileHandle, row, -1);
   FileFlush(g_fileHandle);
}
//+------------------------------------------------------------------+
