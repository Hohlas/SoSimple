#property copyright "Hohla"
#property link      "mail@hohla.ru"
#property description "При совпадении PowerCheck вершин начинается верхний флэтовый уровень" 
#property description "Нижний флэтовый уровень чертится по мимимуму между ними." 
#property description "При пробитии одного из этих уровней на LevAccuracy*atr фиксируется начало импульса ложняка и чертится соответствующпй уровень." 
#property strict // Указание компилятору на применение особого строгого режима проверки ошибок 
#property indicator_chart_window 
#property indicator_buffers 2
#property indicator_color1 clrCadetBlue      // Flt.Hi.P: Флэтовые уровни с кол-вом    
#property indicator_color2 clrCadetBlue      // Flt.Lo.P: отскоков больше PowerCheck  
      sinput string  z1="          -  P I C    L E V E L S  - ";
extern char PicPer=1;   // PicPer=1..3 период фракталов (самый ухкий)
extern char FltLen=10;  // FltLen=5..15/5 минимальная длина флэта; и бары от пробиваемого пика до его ложняка в SIG_MIRROR_LEVELS()
extern char PicCnt=1;   // PicCnt=0..7 кол-во совпадений с пиками для Первого, флэтa и ложняка
extern char PicPwr=5;   // PicPwr=3..12 FrontVal>АТР*Power, 
extern char PicImp=1;   // PicImp=0..7 уровень с макс импульсом 
extern char Rev=0;      // Rev=0..2 1-Пробивший хоть один пик, 2-Back>Front
extern char Days=0;     // Days=-6..6 поиск на периоде Days ближайших (<0 дальних) первых уровней   
extern char MidTyp=1;   // MidTyp=0..4 0-FirstLev, 1-MaxFront, 2-MaxFront*MaxPics, 3-MaxPics, 4-PwrSum
      sinput string  z3="          -  T R E N D   S I G N A L S  - ";
extern char iGlb=0;     // iGlb=0..2 Глоб.Тренд=пробой: 1-Первых Уровней, 2-Уровней серединки 0-без Глобала       
extern char iFlt=0;     // iFlt=0..1  Выход из флэта противоположно входу 
extern char iLoc=0;     // iLoc=0..3  Кол-во пробитых пиков для изменения локального тренда
//extern char iImp=0;     // unused! iImp=0..2  Импульс больше Atr.Fast*(iImp+2)                           
      sinput string  z5="          -  A  T  R  - ";       
extern char  A=15;    // A=10..30  кол-во бар^2 для медленного АТР
extern char  a=5;     // a=2..6  кол-во бар^2 для быстрого atr
extern char  Ak=1;    // Ak=0..3 ATR: 0~slow, 1~fast, 2~min, 3~max
extern char  PicVal=20;  // PicVal=10..50  Допуск  Atr.Lim: АТР%
      sinput string  z6="          -  I N P U T S - ";
//extern char  iFrstLev=1;// iFrstLev=-3..3 вход в районе Первых Уровней: |iFrstLev|*ATR / <0 уровня серединки
//extern char  Del=1;   // Del=0..2 удаление отложников 0=не трогаем;  1=при появлении нового сигнала удаляем; 2=при появлении нового сигнала удаляем противоположный или если ордер остался один;
extern char  Target=1;   // Target=-2..2 целевой уровень: >0~макс. <0~средн движение от 1-последнего, 2-разворотного пика      
extern char  iSignal=1; // iSignal=0..4 1-FIRST_LEVELS, 2-FALSE_BREAK, 3-..., 4-TURTLE
extern char  iParam=1;  // iParam=1..4 параметры сигнала   
extern char  D=0;       // D=-7..5 >0: BUY=Stop+ATR*D/2, <=0: stop/profit=2/3 1/2 2/5 1/3 2/7 1/4
extern char  Stp=1;  // Stp=0..4 Stop=input_price-Atr.Lim*Stp;
extern char  Prf=3;  // Prf=-5..5  >0~Back/4*Prf <=0~ATR*(0.9 .. 6.4) 
   sinput string  z9="          -  O U T P U T  - ";
extern char  oImp=0;    // oImp=-5..5 отсутвствие отскока (H -BUY.Val)/noise<oImp/10 после входа = закрытие NoLoss, (<0-bid) 
extern char  oFlt=0;    // oFlt=0..4 удаление отложника при пике ближе oFlt*ATR/2 
extern char  oGlb=0;    // oGlb=-4..5 глобал тренд: 1~Bid, 2~BUY.Val, 3~BUY.Max, >3~Atr*(oGlb-3)/2, -1~стоп за последний пик, -2~стоп в БУ)
extern char  oLoc=0;    // oLoc=-4..5 локал тренд 1~Bid, 2~BUY.Val, 3~BUY.Max, >3~Atr*(oPic-3)/2, -1~стоп за последний пик, -2~стоп в БУ)
extern char  Trl=0;     // Trl=-4..4 MinBack=Trl*|ATR|. <0~от стопа; >0~от входа  
extern char  Wknd=0;  // Wknd=0..2 закрытие поз 1-FOMC, 2-Weekend 
      sinput string  z10="          -  T I M E  - ";
extern char  tk=0;    // tk=0..3  (1)  (0..6 для 30минуток) 0-без временного фильтра,  >0-разрешена торговля с Tin=(tk-1)*8+T0 до Tin+T1, потом все позы херятся. Каждая единица прибавляет 8 часов к времени Т0  
extern char  T0=7;    // T0=1..8  (1)  при tk=0 expiration: 1,2,3,5,8,13,21,0. При tk>0 время входа Tin=((8*(tk-1)+T0-1). Все в БАРАХ
extern char  T1=8;    // T1=1..8  (1)  при tk=0 скока баров держать открытую позу: 1,2,3,5,8,13,21,0. При tk>0 количество баров в течении которых разрешена работа  с момента T0. При T1=0 || T1=8 ограничения по времени не работают  
extern char  tp=1;    // tp=1..5  (1)  выход по времени:  1~Bid, 2~BUY.Val, 3~BUY.Max, >3~Atr*(tp-3)/2 -1~стоп за последний пик, -2~стоп в БУ


ushort   PocScale = 5;  // PocScale=1..10 множитель длины РОС
double   I0[],I1[]; //  ложняки    
bool    PocAllocation=1, Real=false, Modify;  // PocAllocation=0..1 показывать/скрыть распределение POC

datetime BarTime,  TestEndTime;
uchar    ExpTotal;
short    Per, LotDigits, DIGITS,  HistDD,  LastTestDD, SkipFrom=0, SkipTo=0;       
int      bar=1, Magic, Today, TesterFile;
float    PS[20], ch[10], Present, MaxSpred, Lot, Aggress, CurDD, Risk= 0,
         ASK, BID, StopLevel, Spred, MaxRisk, MaxMargin=float(0.7),  // максимальный суммарный риск всех позиций в одну сторону (все лонги или все шорты), максимальная загрузка маржи    
         InitDeposit, DayMinEquity, DrawDown, MaxEquity, MinEquity, Equity;  
string   SYMBOL=Symbol(), Company, NAME_VER=__FILE__+"230.525";  
ulong    MagicLong; 
string ExpertName="iPIC";  // идентификатор графических объектов для их удаления


#define  SO_SIMLE_EXPERT  1 // для добавления в компиляцию библиотек A(), V(), LINE() в функции iGRAPH
#define  PIC_INDICATOR    1 // для исключиния из компиляции библиотек эксперта MAIN(), CAN_TRADE(), PENDING_ORDERS_DEL() 
#include <stdlib.mqh> 
#include <stderror.mqh> 
#include <StdLibErr.mqh> 
#include <FUNCTIONS.mqh>
#include <MAIN.mqh>
#include <iGRAPH.mqh>

//#include <lib_POC.mqh>     // 
#include <lib_PIC.mqh>     // 
#include <lib_ssss.mqh>
//#include <old_versions.mqh>
//#include <lib_TRG.mqh> 
//#include <lib_REZENKO.mqh> 
//#include <lib_Triangle.mqh>

int OnInit(){//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
   IndicatorBuffers(20);  IndicatorDigits(Digits);
   SetIndexStyle(0,DRAW_LINE);   SetIndexBuffer(0,I0);   // UP2: сильные уровни с кол-вом 
   SetIndexStyle(1,DRAW_LINE);   SetIndexBuffer(1,I1);   // DN2: отскоков больше PowerCheck 
   // iName=iName+"("+DoubleToStr(A,0)+") ";   
   CHART_SETTINGS(); // настройки вненшего вида графика 
   IndicatorShortName(ExpertName);
   SetIndexLabel(0,ExpertName);
   PRINT_TO_CHART.EXTERN_VARS();
   EXP[0].CLASS_INIT(1); 
   VER="230.525"; Print("Indicator Init");
   return (EXP[0].INIT());  // (0)=Успешная инициализация. Результат выполнения функции OnInit() анализируется терминалом только если программа скомпилирована с использованием #property strict      
   }                    // НЕнулевой код возврата означает неудачную инициализацию и генерирует событие Deinit с кодом причины деинициализации REASON_INITFAILED



void start(){
   int UnCounted=Bars-IndicatorCounted()-PicPer-1;
   for (bar=UnCounted; bar>0; bar--){ // Print(" Bars=",Bars," IndicatorCounted=",IndicatorCounted()," UnCounted=",UnCounted, " bar=",bar, " Time[bar]=",Time[bar], " BarTime=",BarTime);
      if (Time[bar]>BarTime){
         BarTime=Time[bar];
         if (!EXP[0].PIC()) continue; // ОСНОВНОЙ ЦИКЛ ПОИСКА УРОВНЕЙ 
         if (TimeDayOfWeek(Time[bar])==1 && TimeHour(Time[bar])<TimeHour(Time[bar+1])) LINE("NewWeek",  bar, EXP[0].L,   bar,EXP[0].H, clrDeepSkyBlue,2);
         EXP[0].POC_SIMPLE();  // ОПРЕДЕЛЕНИЕ ПЛОТНОГО СКОПЛЕНИЯ БАР БЕЗ ПРОПУСКОВ
         }
      
     
   }  }/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ    
int deinit(){
	CLEAR_CHART();// удаляем все свои линии
	return(0);
   }
void REPORT(string Missage){ // собираем все сообщения экспертов в одну кучу 
   Print("REPORT of ",Magic,": ",Missage);
   }
float MAX(double price1, double price2){
   if (price1>price2) return (float(price1)); else return (float(price2));
   } 
float MIN(double price1, double price2){// возвращает меньшее, но не нулевое значение
   if (price1==0) return (float(price2));
   if (price2==0) return (float(price1));
   if (price1<price2) return (float(price1)); else return (float(price2));
   } 
bool ERROR_CHECK(string ErrTxt){ return( ERROR_CHECK(ErrTxt,CurExp));}   
bool ERROR_CHECK(string ErrTxt, uchar ExpNum){ // Проверка проведения операций с ордерами. Возвращает необходимость повтора торговой операции
   int err=GetLastError(); //
   if (err==0) return(false); // Ошибок нет. Повтор не нужен
   else return(true);
   } // в этих функциях      

   
   