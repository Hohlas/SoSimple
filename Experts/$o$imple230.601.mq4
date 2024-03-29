#define MAX_RISK  10
#property copyright  "Hohla"
#property link       "hohla.ru"
#property strict // Указание компилятору на применение особого строгого режима проверки ошибок 


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
      sinput string  z2="          -  P I C    L E V E L S  - ";
extern char PicPer=1;   // PicPer=1..3 период фракталов (самый ухкий)
extern char FltLen=10;  // FltLen=5..15/5 минимальная длина флэта; и бары от пробиваемого пика до его ложняка в SIG_MIRROR_LEVELS()
extern char PicCnt=2;   // PicCnt=1..3 кол-во отскоков для флэтa и ложняка
extern char PicPwr=9;    // Power=3..12 FrontVal>АТР*Power, 
extern char PicImp=1;   // PicImp=0..1 уровень с макс импульсом 
extern char Rev=0;      // Rev=0..2 1-Пробивший хоть один пик, 2-Back>Front
extern char Days=0;     // Days=0..4 
extern char Target=1;   // Target=-2..2 целевой уровень: >0~макс. <0~средн движение от 1-последнего, 2-разворотного пика  
      sinput string  z3="          -  T R E N D   S I G N A L S  - ";
extern char fGlb=0;     // fGlb=0..2 Глоб.Тренд=пробой: 2-Первых Уровней, 1-Уровней серединки 0-без Глобала       
extern char iFlt=0;     // iFlt=0..1  Выход из флэта противоположно входу 
extern char iPic=0;     // iPic=0..2  Кол-во пробитых пиков для изменения направления 
//extern char iImp=0;     // unused! iImp=0..2  Импульс больше Atr.Fast*(iImp+2)                           
      sinput string  z5="          -  A  T  R  - ";       
extern char  A=15;    // A=10..30  кол-во бар^2 для медленного АТР
extern char  a=5;     // a=2..6  кол-во бар^2 для быстрого atr
extern char  Ak=1;    // Ak=0..3 ATR: 0~slow, 1~fast, 2~min, 3~max
extern char  PicVal=20;  // PicVal=10..50  Допуск  Atr.Lim: АТР%
      sinput string  z6="          -  I N P U T S - ";
//extern char  iFrstLev=1;// iFrstLev=-3..3 вход в районе Первых Уровней: |iFrstLev|*ATR / <0 уровня серединки
//extern char  Del=1;   // Del=0..2 удаление отложников 0=не трогаем;  1=при появлении нового сигнала удаляем; 2=при появлении нового сигнала удаляем противоположный или если ордер остался один;
extern char  iSignal=3; // iSignal=0..4 1-FIRST_LEVELS, 2-FALSE_BREAK, 3-..., 4-TURTLE
extern char  iParam=1;  // iParam=0..4 параметры сигнала   
extern char iCnt=0; // iCnt=0 unused
extern char iPwr=0;    // iPwr=0 unused
//extern char  Iprice=2;  // unused! Iprice=1..2  1~FirstLev, 2~MidLev 
extern char  D=0;       // D=-7..5 >0: BUY=Stop+ATR*D/2, <=0: stop/profit=2/3 1/2 2/5 1/3 2/7 1/4
//extern char  sMin=0; // unused! sMin=-3..3 if (STOP<sMin*ATR/2) отодвигаем <0 стоп; >0-вход.
//extern char  sMax=0; // unused! sMax=-3..3 if (STOP>sMax*ATR) <0~NoTrade; >0-приближаем вход. Где ATR=ATR*dAtr*0.1;
extern char  Stp=1;  // Stp=0..4 Stop=input_price-Atr.Lim*Stp;
extern char  Prf=3;  // Prf=-5..5  >0~Back/4*Prf <=0~ATR*(0.9 .. 6.4) 
//extern char  minPL=0; // unused! minPL=-6..6/2 если P/L хуже minPL/2: <0 не открываемся; >0 вход отодвигается для улучшения P/L
   sinput string  z9="          -  O U T P U T  - ";
extern char  oImp=0;    // oImp=-5..5 отсутвствие отскока (H -BUY.Val)/noise<oImp/10 после входа = закрытие NoLoss, (<0-bid) 
extern char  oFlt=0;    // oFlt=0..4 удаление отложника при пике ближе oFlt*ATR/2 
extern char  oGlb=0;    // oGlb=0..3 смена глобального тренда (закрытие по 1-bid, 2-NoLoss, 2-MaxFromBuy)
extern char  oPic=0;    // oPic=0..3 смена локального тренда (закрытие по 1-bid, 2-NoLoss, 2-MaxFromBuy)
extern char  Trl=0;     // Trl=-4..4 MinBack=Trl*|ATR|. <0~от стопа; >0~от входа  
extern char  Wknd=0;  // Wknd=0..2 закрытие поз 1-FOMC, 2-Weekend 
      sinput string  z10="          -  T I M E  - ";
extern char  tk=0;    // tk=0..3  (1)  (0..6 для 30минуток) 0-без временного фильтра,  >0-разрешена торговля с Tin=(tk-1)*8+T0 до Tin+T1, потом все позы херятся. Каждая единица прибавляет 8 часов к времени Т0  
extern char  T0=7;    // T0=1..8  (1)  при tk=0 expiration: 1,2,3,5,8,13,21,0. При tk>0 время входа Tin=((8*(tk-1)+T0-1). Все в БАРАХ
extern char  T1=8;    // T1=1..8  (1)  при tk=0 скока баров держать открытую позу: 1,2,3,5,8,13,21,0. При tk>0 количество баров в течении которых разрешена работа  с момента T0. При T1=0 || T1=8 ограничения по времени не работают  
extern char  tp=1;    // tp=0..3  (1)  выход по времени:  0-по текущей, 1-безубыток, 2-MaxFromBuy,  -1~стоп за последний пик, -2~стоп в безубыток

datetime BarTime;
uchar    ExpTotal;
short    LotDigits, DIGITS,  SkipFrom=0, SkipTo=0;       
int      bar=1, Today, TesterFile;
float    PS[20], ch[10], MaxSpred, Lot, Aggress, CurDD,
         ASK, BID, StopLevel, Spred, MaxRisk, MaxMargin=float(0.7),  // максимальный суммарный риск всех позиций в одну сторону (все лонги или все шорты), максимальная загрузка маржи    
         InitDeposit, DayMinEquity, DrawDown, MaxEquity, MinEquity, Equity;  
string   ChartHistory="", Company, NAME_VER=__FILE__,
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
#include <lib_ssss.mqh>
#include <old_versions.mqh>
#include <COUNT.mqh>
#include <INPUT.mqh>
#include <OUTPUT.mqh>
#include <iSIG_FALSE_BREAK.mqh>
//#include <iSIG_FIRST_LEVELS_CONFIRM.mqh>
#include <iSIG_FIRST_LEVELS.mqh>
#include <iSIG_TURTLE.mqh>

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
   for (CurExp=0; CurExp<ExpTotal; CurExp++){// осуществление перебора всех строк с входными параметрами за один тик (только для реала) 
      EXP[CurExp].MAIN();
      }
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
     

   