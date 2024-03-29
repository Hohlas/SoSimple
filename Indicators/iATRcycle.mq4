#property copyright "Hohla"
#property link      "hohla@mail.ru"
#property strict // Указание компилятору на применение особого строгого режима проверки ошибок 
#property indicator_separate_window
#property indicator_buffers 1
#property indicator_color1 clrOrange

extern uchar CountedDays=20;
double Buffer0[];
float HL[][100]; // массив значений HL [номер бара от начала суток для времени i] [счетчик посчитанных бар с заданным номером]
int bar,BarsInDay; 

struct PICS{ // структура  PICS для совместимости с $o$imple в файле ORDERS.mqh 
   float P;       // price
   datetime T;       // время формирования пика 
   } F[1]; 


#include <iGRAPH.mqh>
int init(){//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
   string IndName="iATRcyc("+S0(CountedDays)+")" ;
   IndicatorBuffers(1);
   IndicatorDigits(Digits);
   SetIndexStyle(0,DRAW_LINE);
   SetIndexBuffer(0,Buffer0);
   IndicatorShortName(IndName);
   SetIndexLabel(0,IndName);
   BarsInDay=1440/Period(); Print("BarsInDay=",BarsInDay); // кол-во бар в сутках
   ArrayResize(HL, BarsInDay+1); // Зададим размерность первому измерению массива
   return (INIT_SUCCEEDED);
   }//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 

void start(){//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
   uchar DayBar, DayCnt=0;
   float ATR;
   int UnCounted=Bars-IndicatorCounted()-BarsInDay*CountedDays-10;
   for (bar=UnCounted; bar>0; bar--){
      DayBar=uchar((TimeHour(iTime(NULL,0,bar))*60+TimeMinute(iTime(NULL,0,bar)))/Period()); // счетчик бар от начала суток для текущего времени i
      HL[DayBar][DayCnt]=float(High[bar]-Low[bar]); // заполнение основного массива значениями HL
      DayCnt++; if (DayCnt>CountedDays) DayCnt=0;
      ATR=0; for (uchar i=0; i<CountedDays; i++) ATR+=HL[DayBar][i];
      Buffer0[bar]=ATR/CountedDays;  // High[bar+BarsInDay*CountedDays]; 
      }
   }  
           
   