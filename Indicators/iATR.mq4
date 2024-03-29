#define VERSION   "230.516"
#property version    VERSION // yym.mdd
#property copyright  "Hohla"
#property link       "www.hohla.ru"
#property strict // Указание компилятору на применение особого строгого режима проверки ошибок 
#property description "Average True Range"
#property strict
//--- indicator settings
//#property indicator_separate_window
#property indicator_chart_window
#property indicator_height  30   // Фиксированная высота подокна индикатора в пикселях 
#property indicator_buffers 2
#property indicator_color1  clrBlue
#property indicator_color2  clrGreen
//--- input parameters
input int FastAtrPer=5;  // Fast ATR Period
input int SlowAtrPer=25; // Slow ATR Period
//--- buffers
double FastAtr[],SlowAtr[],HL[];

int OnInit(void){
   string FastAtrName, SlowAtrName;
//--- 1 additional buffer used for counting.
   IndicatorBuffers(3);
   IndicatorDigits(Digits);
//--- indicator line
   SetIndexStyle(0,DRAW_LINE);
   SetIndexBuffer(0,FastAtr);
   SetIndexStyle(1,DRAW_LINE);
   SetIndexBuffer(1,SlowAtr);
   SetIndexBuffer(2,HL);
//--- name for DataWindow and indicator subwindow label
   FastAtrName="FastAtr("+IntegerToString(FastAtrPer)+")";
   SlowAtrName="SlowAtr("+IntegerToString(SlowAtrPer)+")";
   SetIndexLabel(0,FastAtrName);
   SetIndexLabel(1,SlowAtrName);
   IndicatorShortName("ATR("+IntegerToString(FastAtrPer)+","+IntegerToString(SlowAtrPer)+") v"+VERSION);
   if(FastAtrPer<=0 || FastAtrPer>=SlowAtrPer){//--- check for input parameter
      Print("Wrong input parameter ATR Period");
      return(INIT_FAILED);
      }
   SetIndexDrawBegin(0,SlowAtrPer);
   return(INIT_SUCCEEDED);
   }

int OnCalculate(const int     rates_total,
                const int     prev_calculated,
                const datetime &time[],
                const double  &open[],
                const double  &high[],
                const double  &low[],
                const double  &close[],
                const long    &tick_volume[],
                const long    &volume[],
                const int     &spread[])
               {
   int CountedBars;
   if (rates_total<=SlowAtrPer)   return(0);
   //Print("rates_total=",rates_total," prev_calculated=",prev_calculated);
   ArraySetAsSeries(FastAtr,false);    // counting from 0 to rates_total
   ArraySetAsSeries(SlowAtr,false);
   ArraySetAsSeries(HL,false);
   ArraySetAsSeries(high,false);
   ArraySetAsSeries(low,false);
   //ArraySetAsSeries(open,false);
   //ArraySetAsSeries(close,false);

   if (prev_calculated==0){   // preliminary calculations
      HL[0]=0.0;
      FastAtr[0]=0.0;
      SlowAtr[0]=0.0;
      for (int i=1; i<rates_total; i++)   HL[i]=high[i]-low[i]; // high[i]-low[i];  //--- filling out the array of True Range values for each period
      double InitFast=0.0, InitSlow=0.0;
      for (int i=1; i<=SlowAtrPer; i++){
         FastAtr[i]=0.0;
         SlowAtr[i]=0.0;
         InitSlow+=HL[i];
         if (i>SlowAtrPer-FastAtrPer)  InitFast+=HL[i];
         }
      InitFast/=FastAtrPer;
      InitSlow/=SlowAtrPer;
      FastAtr[SlowAtrPer]=InitFast;   
      SlowAtr[SlowAtrPer]=InitSlow;
      CountedBars=SlowAtrPer+1;
      }
   else
      CountedBars=prev_calculated-1;
      
   for (int i=CountedBars; i<rates_total; i++){ // the main loop of calculations
      HL[i]=high[i]-low[i];
      FastAtr[i]=FastAtr[i-1]+(HL[i]-HL[i-FastAtrPer])/FastAtrPer;
      SlowAtr[i]=SlowAtr[i-1]+(HL[i]-HL[i-SlowAtrPer])/SlowAtrPer;
      }
   //Print("Calculate ATR");
   return (rates_total);//--- return value of prev_calculated for next call
   }
//+------------------------------------------------------------------+
