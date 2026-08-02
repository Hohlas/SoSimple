#define MAX_RISK  10
#define VERSION "260.327"
#property copyright  "Hohla"
#property link       "hohla.ru"
#property version  VERSION
#property tester_file "mt5_entry_signals.csv"

input short   InpBackTest=0;
input char    InpOpt_Trades=10; // Opt_Trades Влияет только на оптимизацию, остальные параметры и на опт ина бэктест
input float   InpRF_=0.5;       // RF При оптимизациях отбрасываем
input float   InpPF_=1.5;       // PF резы с худшими показателями
input char    InpMO_=0;         // MO множитель спреда, т.е. MO=MO_ * Spred
input float   InpRisk= 0;       // Risk процент депо в сделке (на реале задается в файле #.csv)
input char    InpMM_Mode=1;     // 1..4 см. ММ:
input bool    InpReal=false;    // Real
input char    InpCustMax=0;     // 0-Bal, 1-RF, 2-iRF, 3-MO/SD - максимизируемый при оптимизации параметр
input string  InpSkipPer="";    // 08-12 пропустить период при оптимизации
      sinput string  z1="          -  P I C    L E V E L S  - ";
input char InpPicPer=1;   // PicPer=1..3 период фракталов (самый узхкий)
input char InpFltLen=10;  // FltLen=5..15/5 минимальная длина флэта; и бары от пробиваемого пика до его ложняка в SIG_MIRROR_LEVELS()
input char InpPicCnt=2;   // PicCnt=0..7 кол-во совпадений с пиками для Первого, флэтa и ложняка
input char InpPicPwr=9;   // PicPwr=3..12 FrontVal>АТР*Power,
input char InpPicImp=1;   // PicImp=0..7 уровень с макс импульсом
input char InpRev=0;      // Rev=0..2 1-Пробивший хоть один пик, 2-Back>Front
input char InpDays=0;     // Days=-6..6 поиск на периоде Days ближайших (<0 дальних) первых уровней
input char InpMidTyp=1;   // MidTyp=0..4 0-FirstLev, 1-MaxFront, 2-MaxFront*MaxPics, 3-MaxPics, 4-PwrSum
      sinput string  z3="          -  T R E N D   S I G N A L S  - ";
input char InpiGlb=0;     // iGlb=0..2 Глоб.Тренд=пробой: 1-Первых Уровней, 2-Уровней серединки 0-без Глобала
input char InpiFlt=0;     // iFlt=0..1  Выход из флэта противоположно входу
input char InpiLoc=0;     // iLoc=0..3  Кол-во пробитых пиков для изменения локального тренда
//input char iImp=0;     // unused! iImp=0..2  Импульс больше Atr.Fast*(iImp+2)
      sinput string  z5="          -  A  T  R  - ";
input char  InpA=15;    // A=10..30  кол-во бар^2 для медленного АТР
input char  Inpa=5;     // a=2..6  кол-во бар^2 для быстрого atr
input char  InpAk=1;    // Ak=0..3 ATR: 0~slow, 1~fast, 2~min, 3~max
input char  InpPicVal=20;  // PicVal=10..50  Допуск  Atr.Lim: АТР%
      sinput string  z6="          -  I N P U T S - ";
//input char  iFrstLev=1;// iFrstLev=-3..3 вход в районе Первых Уровней: |iFrstLev|*ATR / <0 уровня серединки
//input char  Del=1;   // Del=0..2 удаление отложников 0=не трогаем;  1=при появлении нового сигнала удаляем; 2=при появлении нового сигнала удаляем противоположный или если ордер остался один;
input char  InpTarget=0;   // Target=-2..2 целевой уровень: >0~макс. <0~средн движение от 1-последнего, 2-разворотного пика
input char  InpiSignal=3; // iSignal=0..5 1-FIRST_LEVELS, 2-FALSE_BREAK, 3-ML_TRADE, 4-TURTLE, 5-ML_TRADE_TB
input char  InpiParam=1;  // iParam=1..4 параметры сигнала
input char  InpD=0;       // D=-7..5 >0: BUY=Stop+ATR*D/2, <=0: stop/profit=2/3 1/2 2/5 1/3 2/7 1/4
input char  InpStp=3;  // Stp=0..4 Stop=input_price-Atr.Lim*Stp;
input char  InpPrf=3;  // Prf=-5..5  >0~Back/4*Prf <=0~ATR*(0.9 .. 6.4)
   sinput string  z9="          -  O U T P U T  - ";
input char  InpoImp=0;    // oImp=-5..5 отсутвствие отскока (H -BUY.Val)/noise<oImp/10 после входа = закрытие NoLoss, (<0-bid)
input char  InpoFlt=0;    // oFlt=0..4 удаление отложника при пике ближе oFlt*ATR/2
input char  InpoGlb=0;    // oGlb=-4..5 глобал тренд: 1~Bid, 2~BUY.Val, 3~BUY.Max, >3~Atr*(oGlb-3)/2, -1~стоп за последний пик, -2~стоп в БУ)
input char  InpoLoc=0;    // oLoc=-4..5 локал тренд 1~Bid, 2~BUY.Val, 3~BUY.Max, >3~Atr*(oPic-3)/2, -1~стоп за последний пик, -2~стоп в БУ)
input char  InpTrl=0;     // Trl=-4..4 MinBack=Trl*|ATR|. <0~от стопа; >0~от входа
input char  InpWknd=0;  // Wknd=0..2 закрытие поз 1-FOMC, 2-Weekend
      sinput string  z10="          -  T I M E  - ";
input char  Inptk=0;    // tk=0..3  (1)  (0..6 для 30минуток) 0-без временного фильтра,  >0-разрешена торговля с Tin=(tk-1)*8+T0 до Tin+T1, потом все позы херятся. Каждая единица прибавляет 8 часов к времени Т0
input char  InpT0=7;    // T0=1..8  (1)  при tk=0 expiration: 1,2,3,5,8,12,21,0. При tk>0 время входа Tin=((8*(tk-1)+T0-1). Все в БАРАХ
input char  InpT1=6;    // T1=1..8  (1)  при tk=0 скока баров держать открытую позу: 1,2,3,5,8,13,21,0. При tk>0 количество баров в течении которых разрешена работа  с момента T0. При T1=0 || T1=8 ограничения по времени не работают
input char  Inptp=1;    // tp=1..5  (1)  выход по времени:  1~Bid, 2~BUY.Val, 3~BUY.Max, >3~Atr*(tp-3)/2 -1~стоп за последний пик, -2~стоп в БУ
      sinput string  zML="          -  M L   O P T I M I Z A T I O N  - ";
input double InpML_MinRatio      = 3.5;
input double InpML_MaxRatio      = 0;
input double InpML_MaxRR         = 4.0;
input int    InpML_RR_Mode       = 0;
input double InpML_RR_Cap        = 2.5;
input double InpML_ScaleK        = 20.0;
input double InpML_Min_SL_ATR    = 2.0;
input bool   InpML_BypassTrend   = true;
input bool   InpML_ExitEnabled   = true;
input double InpML_ExitThreshold = 2.0;
input double InpML_Filter3       = 0.0;
input double InpML_Filter6       = 0.0;
input double InpML_Trl_Start_ATR = 1.0;
input double InpML_Trl_Step_ATR  = 1.5;
input bool   InpMT5_ExportNero   = false;
input string InpMT5_NeroFile     = "Nero_MT5.csv";
input bool   InpMT5_DiagnosticExecutor = false;
input string InpMT5_EntrySignalFile    = "mt5_entry_signals.csv";
input string InpMT5_EventFile          = "mt5_trade_events.csv";
input bool   InpMT5_BlockBarsSinceFill0Exit = true;
input int    InpMT5_MaxPositions            = 1;  // multi-position cap; 1 = single-position canonical

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

short   BackTest=0;
char    Opt_Trades=10, MO_=0, MM_Mode=1, CustMax=0;
float   RF_=0.5, PF_=1.5, Risk=0;
bool    Real=false;
string  SkipPer="";
char    PicPer=1, FltLen=10, PicCnt=2, PicPwr=9, PicImp=1, Rev=0, Days=0, MidTyp=1,
        iGlb=0, iFlt=0, iLoc=0, A=15, a=5, Ak=1, PicVal=20,
        Target=0, iSignal=3, iParam=1, D=0, Stp=3, Prf=3,
        oImp=0, oFlt=0, oGlb=0, oLoc=0, Trl=0, Wknd=0,
        tk=0, T0=7, T1=6, tp=1;
double  ML_MinRatio=3.5, ML_MaxRatio=0, ML_MaxRR=4.0, ML_RR_Cap=2.5, ML_ScaleK=20.0,
        ML_Min_SL_ATR=2.0, ML_ExitThreshold=2.0, ML_Filter3=0.0, ML_Filter6=0.0,
        ML_Trl_Start_ATR=1.0, ML_Trl_Step_ATR=1.5;
int     ML_RR_Mode=0;
bool    ML_BypassTrend=true, ML_ExitEnabled=true;
bool    MT5_ExportNero=false;
string  MT5_NeroFile="Nero_MT5.csv";
bool    MT5_DiagnosticExecutor=false;
string  MT5_EntrySignalFile="mt5_entry_signals.csv";
string  MT5_EventFile="mt5_trade_events.csv";
bool    MT5_BlockBarsSinceFill0Exit=true;
int     MT5_MaxPositions=1;   // multi-position cap; 1 = single-position (canonical)

void SyncInputs(){
   BackTest=InpBackTest; Opt_Trades=InpOpt_Trades; RF_=InpRF_; PF_=InpPF_; MO_=InpMO_; Risk=InpRisk; MM_Mode=InpMM_Mode; Real=InpReal; CustMax=InpCustMax; SkipPer=InpSkipPer;
   PicPer=InpPicPer; FltLen=InpFltLen; PicCnt=InpPicCnt; PicPwr=InpPicPwr; PicImp=InpPicImp; Rev=InpRev; Days=InpDays; MidTyp=InpMidTyp;
   iGlb=InpiGlb; iFlt=InpiFlt; iLoc=InpiLoc; A=InpA; a=Inpa; Ak=InpAk; PicVal=InpPicVal;
   Target=InpTarget; iSignal=InpiSignal; iParam=InpiParam; D=InpD; Stp=InpStp; Prf=InpPrf;
   oImp=InpoImp; oFlt=InpoFlt; oGlb=InpoGlb; oLoc=InpoLoc; Trl=InpTrl; Wknd=InpWknd;
   tk=Inptk; T0=InpT0; T1=InpT1; tp=Inptp;
   ML_MinRatio=InpML_MinRatio; ML_MaxRatio=InpML_MaxRatio; ML_MaxRR=InpML_MaxRR; ML_RR_Mode=InpML_RR_Mode; ML_RR_Cap=InpML_RR_Cap; ML_ScaleK=InpML_ScaleK;
   ML_Min_SL_ATR=InpML_Min_SL_ATR; ML_BypassTrend=InpML_BypassTrend; ML_ExitEnabled=InpML_ExitEnabled; ML_ExitThreshold=InpML_ExitThreshold;
   ML_Filter3=InpML_Filter3; ML_Filter6=InpML_Filter6; ML_Trl_Start_ATR=InpML_Trl_Start_ATR; ML_Trl_Step_ATR=InpML_Trl_Step_ATR;
   MT5_ExportNero=InpMT5_ExportNero; MT5_NeroFile=InpMT5_NeroFile;
    MT5_DiagnosticExecutor=InpMT5_DiagnosticExecutor; MT5_EntrySignalFile=InpMT5_EntrySignalFile; MT5_EventFile=InpMT5_EventFile; MT5_BlockBarsSinceFill0Exit=InpMT5_BlockBarsSinceFill0Exit;
    MT5_MaxPositions=InpMT5_MaxPositions;
}

#define  SO_SIMLE_EXPERT  1 // для добавления в компиляцию библиотек A,V,LINE в функции iGRAPH
#include <MQL4Compat.mqh>
#include <stdlib.mqh>

#include <FUNCTIONS.mqh>
#include <MAIN.mqh>
#include <ERRORs.mqh>    // проверка исполнения
#include <ORDERS.mqh>
#include <iGRAPH.mqh>
#include <SERVICE.mqh>       // сохранение/восстановление параметров, отчеты и др. заморочки
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

void OnTick(){ // 2015.10.22. 23:00
   RefreshPriceArrays();
   if (Real && float(Ask-Bid)>MaxSpred) MaxSpred=float(Ask-Bid);
   if (Time[0]==BarTime){
      CHECK_OUT();
      return;}  // Сравниваем время открытия текущего(0) бара
   DAY_STATISTIC(); // расчет параметров DD, Trades, массив с резами сделок
   for (uchar e=0; e<ExpTotal; e++)     EXP[e].MAIN();
   END(); // отчет о проведенных операциях, сохранение текущих параметров
   BarTime=Time[0];
   }

void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result){
   if (!MT5_DiagnosticExecutor) return;
   MT5_OnTradeTransaction(trans);
   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
/*    T O   D O
выход при повторном подходе к цене входа
вход на ложняке чуть дальше серединки от движения после ложняка
второй отскок от уровня не отраьбатываем, закрываемся


*/
