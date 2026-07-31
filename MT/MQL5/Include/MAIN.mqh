#include <head_PIC.mqh> // UTF8
class ATR_CLASS{  // 
   public:
   float Fast;   // 
   float Slow;   //
   float Lim;    // точность совпадения уровней
   float Max;
   float Min;
   };      
class EXPERT : public EXPERT_PARENT_CLASS { // дочерний класс печати внешних переменных на график{ // parent class
   protected:
      char  UP, DN, Dir;   
      uchar HI,LO, lastHI, lastLO, // Первый уровень
            HI2,LO2,    // уровни серединки
            hi,lo,hi2,lo2,hi3,lo3, // последний, предпоследний Hi/Lo
            stpH, stpL,    // уровни стопов
            RevHi,RevLo,RevHi2,RevLo2,// Разворотный
            FlsUp,FlsDn,// ложняки подтвержденные
            TrgHi,TrgLo,// целевой
            BrokenPic,  // последний из пробитых
            nFlt,       // индекс последнего флэта
            PocCnt,     // кол-во пересекающихся друг за другом бар
            n;          // индекс последнего пика
      float New, HiZone, DnZone, PocCenter,
         MidMovUp, MidMovDn, LastMovUp, LastMovDn,    // среднее значение нескольких пследних движений
         MovUp[Movements], MovDn[Movements],  // массивы безоткатных движений для определения целевого движения, инициализируюстя в init() на Movements членов
         TargetHi, TargetLo,  // целевые движения и их предварительные значения    
         Hi_checksum,Lo_checksum;         // проверочные значения последних "первых уровней"
      datetime TimeFrom;  // время начала нового цикла (новый день, неделя, месяц) 
      string   reason;  // причина закрытия ордера (Pic / Poc)
       
   public:  
      PICS F[LevelsAmount];  
      TREND_SIGNALS Trnd;    
      ATR_CLASS Atr;   
      
      float H, L, C, H1, L1, C1, H2, L2, C2; //    
      void EXPERT(){Print("EXPERT constructor: CurExp=",CurExp, " VER=",VER); // конструктор по умолчанию, 
         for (uchar f=0; f<LevelsAmount; f++) F[f].P=0;  
         Trnd.Global=0; // инициализация глобального тренда
         TimeFrom=iTime(_Symbol,_Period,Bars-1);
         } 
      // expert functions
      void MAIN();
      int  INIT(); 
      bool CAN_TRADE(); 
      bool FINE_TIME();
      void TIMER();
      void CONSTANT_COUNTER();
      bool COUNT();
      void ML_TRADE();   // ML-сигналы из CSV
      void ML_TRADE_TB(); 
      void INPUT();
      void OUTPUT();
      bool IMPULSE_UP();
      bool IMPULSE_DN();
      void ORDERS_CLOSE(uchar Position);
      void CLOSE_BUY(char price, string comment);
      void CLOSE_SEL(char price, string comment);
      void CLOSE_BUY(float ClosePrice, float MinProfit, string Reason);
      void CLOSE_SEL(float ClosePrice, float MinProfit, string Reason);
      void TRAILING_STOP();
      bool POC_CLOSE_TO_BUY();     
      bool POC_CLOSE_TO_SEL(); 
      float DELTA(int delta);
      void SIG_NULL();
      void SIG_FIRST_LEVELS();
      void SIG_TURTLE();
      void SIG_SESSIONS();
      //void SIG_FALSE_BREAK();
      void OPEN_BUY(uchar pic);
      void OPEN_BUY(float input_price, float target_price);
      void OPEN_SELL(uchar pic);
      void OPEN_SELL(float input_price, float target_price);
      void TARGET_ZONE_CHECK(float& buy, float& sel);
      
      // indicator functions
      bool ATR_COUNT();
      bool PIC();
      void LEVELS_FIND_AROUND();
      void NEW_LEVEL(char dir, float NewFractal);
      void NEW_LEVEL_230202(char NewPicDir, float NewFractal);
      bool LEV_TOUCH(uchar f);
      bool LEV_BREAK(uchar f);
      bool LEV_BREAK(uchar f, float pic);
      bool LEV_CROSS(uchar f);
      char LEV_CHECK(uchar f);
      void SET_BROKEN(uchar f); 
      void FLAT_DETECT(float FltLev, uchar FlatBegin);
      void POC_SIMPLE();
      float PIC_PWR(uchar PowerType, uchar f);
      uchar MID_LEV(uchar f1);
      uchar MID_LEV(uchar f1,  float UpLev, float DnLev, datetime Time0, datetime Time1);
      void HIGHEST_LO(float BaseLev, float& Delta, uchar f, uchar& Nearest);
      void LOWEST_HI(float BaseLev, float& Delta, uchar f, uchar& Nearest);
      void LOWEST_LO(float& lowest, uchar f, uchar& f_lowest);
      void HIGHEST_HI(float& highest, uchar f, uchar& f_highest);
      void POC_INDICATOR();
      void FALSE_BREAK(uchar f);
      void TARGET_COUNT();
      void LOCAL_TREND();
      void GLOBAL_TREND();
      void NERO_CSV_CREATE();
      void NERO_CSV_CREATE(int cur_bar);
      void AV(string txt, uchar f, color clr);
      void AV(string txt, double price, int bar0, color clr);
      void AV(string txt, int bar0, double price, color clr);
      void AV(string txt, datetime time, double price, color clr);
      void V(string txt, uchar f, color clr);
      void V(string txt, double price, int bar0, color clr);
      void V(string txt, int bar0, double price, color clr);
      void V(string txt, datetime time, double price, color clr);
      void X(string txt, uchar f, color clr);
      void X(string txt, double price, int bar0, color clr);
      void X(string txt, int bar0, double price, color clr);
      void X(string txt, datetime time, double price, color clr);
      void LINE(string txt, uchar f0, uchar f1, color clr, uchar Width);
      void LINE(string txt, int bar0, double price0, int bar1, double price1, color clr, char Width);
      void LINE(string txt, datetime time0, double price0, datetime time1, double price1, color clr, char Width);
      void LINE(string txt, double price0, int bar0, double price1, int bar1, color clr, char Width);
      void LINE(string txt, double price0, datetime time0, double price1, datetime time1, color clr, char Width);
   }EXP[];

#include <lib_ML_Signal.mqh>     // ML-сигналы из предрассчитанного CSV (regression_updn)
#include <lib_ML_Signal_TB.mqh>  // ML Triple Barrier сигналы (фиксированные SL/TP)

   
// -----------------------------------------------------------------------------------------------------------------------------------------------------------     
#ifndef PIC_INDICATOR // код компилируется только в эксперте
   
void EXPERT::MAIN(){
   if (!EXPERT_SET(ExpNum)) return; // выбор параметров эксперта из строки Exp массива CSV, сформированного из файла #.csv
   ORDER_CHECK();  // подробности открытых и отложенных поз  Print("SELLSTOP=",SELLSTOP," BUYSTOP=",BUYSTOP);
   TIMER(); // // ВРЕМЯ УДЕРЖАНИЯ ОТКРЫТЫХ ПОЗ Tper (В Барах)
   if (!COUNT()) return;
   //TRAILING_PROFIT();
   if (FINE_TIME()) INPUT();// не торгуем и закрываем все позы в период запрета торговли
   OUTPUT();
   TRAILING_STOP();
   MODIFY();  
   if (set.BUY.Val || set.SEL.Val) ORDERS_SET(); 
   AFTER(ExpNum); // сохранение на каждом баре переменных HI,LO,DM,DayBar... и значений индикаторов Real/Test    
   }  
#endif // -------------------------------------------------------------------------------------------------------------------------------------------------------     
   
//+------------------------------------------------------------------+
//| функция родительского класса по соднанию и обработке 
//| списка внешних переменных             
//+------------------------------------------------------------------+
void EXPERT_PARENT_CLASS::EXTERN_VARS(){// функция родительского класса 
   DATA(" - P I C   L E V E L S - ");///////////
   DATA("PicPer", PicPer);
   DATA("FltLen", FltLen);
   DATA("PicCnt", PicCnt);
   DATA("PicPwr",  PicPwr);
   DATA("PicImp", PicImp);
   DATA("Rev",    Rev);
   DATA("Days",   Days);
   DATA("MidTyp", MidTyp);
   DATA(" -  T R E N D   S I G N A L S  - ");////////////////
   DATA("iGlb",   iGlb);
   DATA("iFlt",   iFlt);
   DATA("iLoc",   iLoc);
   DATA(" - A  T  R -");////////////////
   DATA("A",         A);
   DATA("a",         a);
   DATA("Ak",        Ak);
   DATA("PicVal",    PicVal);
   DATA(" -  I N P U T S -");////////////////
   DATA("Target", Target);
   DATA("iSignal",iSignal);
   DATA("iParam", iParam);
   DATA("D",      D);
   DATA("Stp",    Stp);
   DATA("Prf",    Prf);
   DATA(" -  O U T P U T  -");////////////////
   DATA("oImp",   oImp);
   DATA("oFlt",   oFlt);
   DATA("oGlb",   oGlb);
   DATA("oLoc",   oLoc);
   DATA("Trl",    Trl);
   DATA("Wknd",   Wknd);
   DATA(" -  T I M E  -");////////////////
   DATA("tk",  tk);
   DATA("T0",  T0);
   DATA("T1",  T1);
   DATA("tp",  tp);
   }  
        
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ  
//void EXPERT::PENDING_ORDERS_DEL(){// УДАЛЕНИЕ ОТЛОЖНИКА, ЕСЛИ ОСТАЛСЯ ОДИН  
//   if (Del!=2)  return;
//   if (BUY.Typ==MARKET){ 
//      if (SEL.Typ==STOP && SEL.Val!=mem.SEL.Val)  SEL.Val=0;   
//      if (SEL.Typ==LIMIT)                         SEL.Val=0;  
//      }
//   if (SEL.Typ==MARKET){
//      if (BUY.Typ==STOP && BUY.Val!=mem.BUY.Val)  BUY.Val=0;    
//      if (BUY.Typ==LIMIT)                         BUY.Val=0;   
//   }  }
