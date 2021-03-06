#property copyright "Hohla"
#property link      "mail@hohla.ru"
#property version    "170.316" // yym.mdd
#property strict // Указание компилятору на применение особого строгого режима проверки ошибок 
#property  indicator_separate_window
#property indicator_buffers 2
#property indicator_color1 clrDarkGray  // быстрый
#property indicator_color2 clrDimGray   // медленный


// ATR текущий, циклический, средний. Быстрый считается с отбросом случайных выбросов.
extern char a=4; // кол-во бар для быстрого.
extern char A=5; // кол-во бар для  медленного
extern char dAtr=10; // dAtr=6..12  ATR=ATR*dAtr*0.1 - минимальное приращение для расчета стопа, тейка и дельты входа: 
extern char Ak=1;    // Ak=1..3 используемый в подсчете стопов ATR:  1-(atr,ATR)/2  2-min(atr,ATR)  3-max(atr,ATR)
extern char PicVal=20;  // PicVal=10..50  Допуск  Atr.Lim: АТР%
double   I0[], I1[]; 
float ATR;
bool Real=true,Prn;
int bar;
string ExpertName="iATR";  // идентификатор графических объектов для их удаления
#include <lib_ATR.mqh>  // 
#include <iGRAPH.mqh>
int OnInit(void){//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
   IndicatorBuffers(3); IndicatorDigits(Digits);
   SetIndexStyle(0,DRAW_LINE);   SetIndexBuffer(0,I0); 
   SetIndexStyle(1,DRAW_LINE);   SetIndexBuffer(1,I1);
   if (A<1 || a<1)    {Print("!!!!!!!!! Wrong input parameters a=",a,", A=",A);  return(INIT_FAILED);}
   ExpertName=ExpertName+"("+DoubleToStr(a*a,0)+","+DoubleToStr(A*A,0)+")";  //  
   IndicatorShortName(ExpertName);
   SetIndexLabel(0,ExpertName);
   Print("iATR OnInit(): Bars=",Bars," IndicatorCounted=",IndicatorCounted());
   return(ATR_INIT());  // (0)=Успешная инициализация. Результат выполнения функции OnInit() анализируется терминалом только если программа скомпилирована с использованием #property strict      
   }                    // НЕнулевой код возврата означает неудачную инициализацию и генерирует событие Deinit с кодом причины деинициализации REASON_INITFAILED

void start(){
   int UnCounted=Bars-IndicatorCounted()-1;
   if (IndicatorCounted()==0) Print(DTIME(Time[bar])," S T A R T   bar=",bar," Bars=",Bars," IndicatorCounted=",IndicatorCounted()," UnCounted=",UnCounted," Atr.Fast=",S5(Atr.Fast));
   for (bar=UnCounted; bar>0; bar--){
       if (!ATR_COUNT()) continue;
       I0[bar]=Atr.Fast; 
       I1[bar]=Atr.Slow;     
   }  }
     