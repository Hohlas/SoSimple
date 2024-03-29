#define VERSION   "230.516"
#property version    VERSION // yym.mdd
#property copyright  "Hohla"
#property link       "www.hohla.ru"
#property strict // Указание компилятору на применение особого строгого режима проверки ошибок 
#property description "Average True Range"

//--- indicator settings
#property indicator_separate_window
#property indicator_buffers 1
#property indicator_color1  clrBlue
//--- input parameter
input int AtrPer=14; // ATR Period
//--- buffers
double ATR[];
double HL[];
//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit(void){
   string short_name;
//--- 1 additional buffer used for counting.
   IndicatorBuffers(2);
   IndicatorDigits(Digits);
//--- indicator line
   SetIndexStyle(0,DRAW_LINE);
   SetIndexBuffer(0,ATR);
   SetIndexBuffer(1,HL);
//--- name for DataWindow and indicator subwindow label
   short_name="ATR("+IntegerToString(AtrPer)+")";
   IndicatorShortName(short_name);
   SetIndexLabel(0,short_name);
//--- check for input parameter
   if(AtrPer<=0){
      Print("Wrong input parameter ATR Period=",AtrPer);
      return(INIT_FAILED);
      }
//---
   SetIndexDrawBegin(0,AtrPer);
//---
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Average True Range                                               |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
  {
   int CountedBars;
//--- check for bars count and input parameter
   if(rates_total<=AtrPer || AtrPer<=0) return(0);
//--- counting from 0 to rates_total
   ArraySetAsSeries(ATR,false);
   ArraySetAsSeries(HL,false);
   ArraySetAsSeries(open,false);
   ArraySetAsSeries(high,false);
   ArraySetAsSeries(low,false);
   ArraySetAsSeries(close,false);

   Print("rates_total=",rates_total," prev_calculated=",prev_calculated);
   if (prev_calculated==0){
      HL[0]=0.0;
      ATR[0]=0.0; Print(" first time: ");
      for (int i=1; i<rates_total; i++)  HL[i]=MathMax(high[i],close[i-1])-MathMin(low[i],close[i-1]);//--- filling out the array of True Range values for each period
      //--- first AtrPeriod values of the indicator are not calculated
      double firstValue=0.0;
      for (int i=1; i<=AtrPer; i++){
         ATR[i]=0.0;
         firstValue+=HL[i];
         }
      ATR[AtrPer]=firstValue/AtrPer;//--- calculating the first value of the indicator
      CountedBars=AtrPer+1;
      }
   else
      CountedBars=prev_calculated-1;
//--- the main loop of calculations
   for (int i=CountedBars; i<rates_total; i++){
      HL[i]=MathMax(high[i],close[i-1])-MathMin(low[i],close[i-1]);
      ATR[i]=ATR[i-1]+(HL[i]-HL[i-AtrPer])/AtrPer;
      }
   return(rates_total);//--- return value of prev_calculated for next call
  }
//+------------------------------------------------------------------+
