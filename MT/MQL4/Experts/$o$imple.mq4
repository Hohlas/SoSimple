#define MAX_RISK  10
#define VERSION "260.328"
#property copyright  "Hohla"
#property link       "hohla.ru"
#property strict // Указание компилятору на применение особого строгого режима проверки ошибок 
#property version  VERSION

extern short   BackTest=0;
sinput char    Opt_Trades=10; // Opt_Trades Влияет только на оптимизацию, остальные параметры и на опт ина бэктест
sinput float   RF_=0.5;       // RF При оптимизациях отбрасываем
sinput float   PF_=1.5;       // PF резы с худшими показателями
sinput char    MO_=0;         // MO множитель спреда, т.е. MO=MO_ * Spred
extern float   Risk= 0;       // Risk процент депо в сделке (на реале задается в файле #.csv) 
sinput char    MM=1;          // 1..4 см. ММ: 
extern bool    Real=false;    // Real
extern char    CustMax=0;     // 0-Bal, 1-RF, 2-iRF, 3-MO/SD - максимизируемый при оптимизации параметр
extern string  SkipPer="";    // 08-12 пропустить период при оптимизации 
      sinput string  z1="          -  P I C    L E V E L S  - ";
extern char PicPer=1;   // PicPer=1..3 период фракталов (самый узхкий)
extern char FltLen=10;  // FltLen=5..15/5 минимальная длина флэта; и бары от пробиваемого пика до его ложняка в SIG_MIRROR_LEVELS()
extern char PicCnt=2;   // PicCnt=0..7 кол-во совпадений с пиками для Первого, флэтa и ложняка
extern char PicPwr=9;   // PicPwr=3..12 FrontVal>АТР*Power, 
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
extern char  Target=0;   // Target=-2..2 целевой уровень: >0~макс. <0~средн движение от 1-последнего, 2-разворотного пика      
extern char  iSignal=3; // iSignal=0..5 1-FIRST_LEVELS, 2-FALSE_BREAK, 3-ML_TRADE, 4-TURTLE, 5-ML_TRADE_TB
extern char  iParam=1;  // iParam=1..4 параметры сигнала   
extern char  D=0;       // D=-7..5 >0: BUY=Stop+ATR*D/2, <=0: stop/profit=2/3 1/2 2/5 1/3 2/7 1/4
extern char  Stp=3;  // Stp=0..4 Stop=input_price-Atr.Lim*Stp;
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
extern char  T0=7;    // T0=1..8  (1)  при tk=0 expiration: 1,2,3,5,8,12,21,0. При tk>0 время входа Tin=((8*(tk-1)+T0-1). Все в БАРАХ
extern char  T1=6;    // T1=1..8  (1)  при tk=0 скока баров держать открытую позу: 1,2,3,5,8,13,21,0. При tk>0 количество баров в течении которых разрешена работа  с момента T0. При T1=0 || T1=8 ограничения по времени не работают  
extern char  tp=1;    // tp=1..5  (1)  выход по времени:  1~Bid, 2~BUY.Val, 3~BUY.Max, >3~Atr*(tp-3)/2 -1~стоп за последний пик, -2~стоп в БУ
      sinput string  zML="          -  M L   O P T I M I Z A T I O N  - ";
extern double ML_MinRatio      = 3.5;  // ML_MinRatio: Порог ratio (фильтр слабых сигналов)
extern double ML_MaxRatio      = 0;    // ML_MaxRatio: Верхний порог ratio (0=без ограничения, рек. 4.5)
extern double ML_MaxRR         = 4.0;  // ML_MaxRR: Макс множитель R:R (используется при ML_RR_Mode=0)
extern int    ML_RR_Mode       = 0;    // ML_RR_Mode: 0=min(ratio/MinRatio,MaxRR), 1=log+cap, 2=sqrt+cap
extern double ML_RR_Cap        = 2.5;  // ML_RR_Cap: Потолок R:R для режимов 1,2
extern double ML_ScaleK        = 20.0; // ML_ScaleK: Множитель pred -> ATR
extern double ML_Min_SL_ATR    = 2.0;  // ML_Min_SL_ATR: Минимальный стартовый SL в ATR
extern bool   ML_BypassTrend   = true; // ML_BypassTrend: Игнорировать трендовый фильтр
extern bool   ML_ExitEnabled   = true; // ML_ExitEnabled: Закрывать позицию при reverse-сигнале
extern double ML_ExitThreshold = 2.0;  // ML_ExitThreshold: Мин. ratio для ML-exit (< ML_MinRatio)
extern double ML_Filter3       = 0.0;  // ML_Filter3: Фильтр up_3/dn_3 (0=выкл, 1.0=совпадение направления, >1=усиленный)
extern double ML_Filter6       = 0.0;  // ML_Filter6: Фильтр up_6/dn_6 (0=выкл, 1.0=совпадение направления, >1=усиленный)
extern double ML_Trl_Start_ATR = 1.0;  // ML_Trl_Start_ATR: Активация ML-трала при профите в ATR (от 0.5 до 2.0)
extern double ML_Trl_Step_ATR  = 1.5;  // ML_Trl_Step_ATR: Дистанция ML-трала в ATR (от 0.3 до 1.5)
extern int    ML_ExitMode      = 0;    // ML_ExitMode: 0=timeout parity-check, 1=trailing-stop по X*ATR
extern double ML_TrailATR      = 8.0;  // ML_TrailATR: X в трейлинг-стопе; одновременно стартовый стоп и trailing-gap
extern double ML_TakeProfitATR = 0.0;  // ML_TakeProfitATR: take profit в ATR от входа; 0=выключен
extern int    ML_MaxPositions  = 1;    // ML_MaxPositions: 1=старый режим, >1=несколько одновременных ML-позиций
extern int    ML_HoldBars      = 12;   // ML_HoldBars: сколько баров держать сделку в parity-check
extern bool   ML_AllowReversal = false;// ML_AllowReversal: закрывать по обратному сигналу из CSV
extern bool   ML_UseScoreFilter = true;// ML_UseScoreFilter: применять порог по pred_ret_24_dir_atr, если колонка есть
extern double ML_ScoreThreshold = -0.03594103; // ML_ScoreThreshold: текущий порог отбора winner A@7.5%
extern double ML_BackStopATR   = 50.0; // ML_BackStopATR: дальний страховочный SL для корректного выставления ордера

datetime BarTime;
uchar    ExpTotal;
short    LotDigits, DIGITS,  SkipFrom=0, SkipTo=0;       
int      bar=1, Today, TesterFile;
float    PS[20], ch[10], MaxSpred, Lot, Aggress, CurDD,
         ASK, BID, StopLevel, Spred, MaxRisk, MaxMargin=float(0.7),  // максимальный суммарный риск всех позиций в одну сторону (все лонги или все шорты), максимальная загрузка маржи    
         InitDeposit, DayMinEquity, DrawDown, MaxEquity, MinEquity, Equity;  
string   ChartHistory="", Company, NAME="SoSimple", VER=VERSION,
         Prm1,Prm2,Prm3,Prm4,Prm5,Prm6,Prm7,Prm8,Prm9,Prm10,Prm11,Prm12,Prm13, 
         Str1,Str2,Str3,Str4,Str5,Str6,Str7,Str8,Str9,Str10,Str11,Str12,Str13; 
ulong    MagicLong;

#define  SO_SIMLE_EXPERT  1 // для добавления в компиляцию библиотек A,V,LINE в функции iGRAPH   
#include <stdlib.mqh> 
#include <stderror.mqh> 
#include <StdLibErr.mqh> 

#include <FUNCTIONS.mqh>
#include <MAIN.mqh>
#include <ORDERS.mqh>
#include <iGRAPH.mqh>
#include <SERVICE.mqh>       // сохранение/восстановление параметров, отчеты и др. заморочки
#include <ERRORS.mqh>    // проверка исполнения
#include <MM.mqh> 
 
#include <lib_PIC.mqh>  // сортировка фракталов
#include <COUNT.mqh>
#include <INPUT.mqh>
#include <OUTPUT.mqh>
//#include <iSIG_FALSE_BREAK.mqh>
//#include <iSIG_FIRST_LEVELS_CONFIRM.mqh>
//#include <iSIG_FIRST_LEVELS.mqh>
//#include <iSIG_TURTLE.mqh>

//#include <lib_REZENKO.mqh> // 
//#include <iREPORT.mqh>       // сохранение/восстановление параметров, отчеты и др. заморочки

#include <ERRORs.mqh>    // проверка исполнения
#include <MM.mqh> 

void OnTick(){ // 2015.10.22. 23:00 
   if (Real && float(Ask-Bid)>MaxSpred) MaxSpred=float(Ask-Bid);
   if (Time[0]==BarTime){
      CHECK_OUT(); 
      return;}  // Сравниваем время открытия текущего(0) бара 
   DAY_STATISTIC(); // расчет параметров DD, Trades, массив с резами сделок
   for (uchar e=0; e<ExpTotal; e++)     EXP[e].MAIN();
   END(); // отчет о проведенных операциях, сохранение текущих параметров       
   BarTime=Time[0];  
   }  
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
/*    T O   D O
выход при повторном подходе к цене входа
вход на ложняке чуть дальше серединки от движения после ложняка
второй отскок от уровня не отраьбатываем, закрываемся


*/   
     

