#define MAX_RISK  10
#property copyright  "Hohla"
#property link       "hohla.ru"
#property strict

extern short   BackTest=0;
sinput char    Opt_Trades=10; 
sinput float   RF_=0.5;       
sinput float   PF_=1.5;       
sinput char    MO_=0;         
extern float   Risk= 0;       
sinput char    MM=1;          
extern bool    Real=false;    
extern char    CustMax=0;     
extern string  SkipPer="";    
      sinput string  z1="          -  P I C    L E V E L S  - ";
extern char PicPer=1;   
extern char FltLen=10;  
extern char PicCnt=2;   
extern char PicPwr=9;   
extern char PicImp=1;   
extern char Rev=0;      
extern char Days=0;     
extern char MidTyp=1;   
      sinput string  z3="          -  T R E N D   S I G N A L S  - ";
extern char iGlb=0;     
extern char iFlt=0;     
extern char iLoc=0;     
      sinput string  z5="          -  A  T  R  - ";       
extern char  A=15;    
extern char  a=5;     
extern char  Ak=1;    
extern char  PicVal=20;  
      sinput string  z6="          -  I N P U T S - ";
extern char  Target=1;   
extern char  iSignal=1; 
extern char  iParam=1;  
extern char  D=0;       
extern char  Stp=1;  
extern char  Prf=3;  
   sinput string  z9="          -  O U T P U T  - ";
extern char  oImp=0;    
extern char  oFlt=0;    
extern char  oGlb=0;    
extern char  oLoc=0;    
extern char  Trl=0;     
extern char  Wknd=0;  
      sinput string  z10="          -  T I M E  - ";
extern char  tk=0;    
extern char  T0=7;    
extern char  T1=8;    
extern char  tp=1;    

datetime BarTime;
uchar    ExpTotal;
short    LotDigits, DIGITS,  SkipFrom=0, SkipTo=0;       
int      bar=1, Today, TesterFile;
float    PS[20], ch[10], MaxSpred, Lot, Aggress, CurDD,
         ASK, BID, StopLevel, Spred, MaxRisk, MaxMargin=float(0.7),      
         InitDeposit, DayMinEquity, DrawDown, MaxEquity, MinEquity, Equity;  
string   ChartHistory="", Company, NAME_VER=__FILE__,
         Prm1,Prm2,Prm3,Prm4,Prm5,Prm6,Prm7,Prm8,Prm9,Prm10,Prm11,Prm12,Prm13, 
         Str1,Str2,Str3,Str4,Str5,Str6,Str7,Str8,Str9,Str10,Str11,Str12,Str13; 
ulong    MagicLong;

#define  SO_SIMLE_EXPERT  1 
#include <stdlib.mqh> 
#include <stderror.mqh> 
#include <StdLibErr.mqh> 

#include <FUNCTIONS.mqh>
#include <MAIN.mqh>
#include <ORDERS.mqh>
#include <iGRAPH.mqh>
#include <SERVICE_ML.mqh>       
#include <ERRORS.mqh>    
#include <MM.mqh> 
 
#include <lib_PIC.mqh>  
#include <lib_ssss.mqh>
#include <COUNT.mqh>
#include <INPUT.mqh>
#include <OUTPUT.mqh>
#include <iSIG_FALSE_BREAK.mqh>
#include <iSIG_FIRST_LEVELS.mqh>
#include <iSIG_TURTLE.mqh>

#include <ERRORs.mqh>    
#include <MM.mqh> 

#include <lib_ML_API.mqh> // Наш ML коннектор

void OnTick() { 
    if (Real && float(Ask-Bid)>MaxSpred) MaxSpred=float(Ask-Bid);
    
    if (Time[0]==BarTime){
        CHECK_OUT(); 
        return;
    }  

    DAY_STATISTIC(); 
    
    for (uchar e=0; e<ExpTotal; e++) {
        if (!EXPERT_SET((char)e)) continue;
        
        EXP[e].ORDER_CHECK();  
        
        // Обновляем фракталы F[]
        if (!EXP[e].PIC()) continue;
        
        // Получаем прогноз ML
        ML_Response resp;
        if (Get_ML_Signal(EXP[e], resp)) {
            Print(EXP[e].Mgc, ":: ML Signal=", resp.signal, 
                  " pred_up=", DoubleToString(resp.pred_up, 3),
                  " pred_dn=", DoubleToString(resp.pred_dn, 3),
                  " ratio_up=", DoubleToString(resp.ratio_up, 2),
                  " ratio_dn=", DoubleToString(resp.ratio_dn, 2));
            
            // Торговая логика ML
            if (resp.signal == 1 && EXP[e].BUY.Typ == 0) {
                EXP[e].OPEN_BUY((float)Ask, 0.0f); 
            } 
            else if (resp.signal == -1 && EXP[e].SEL.Typ == 0) {
                EXP[e].OPEN_SELL((float)Bid, 0.0f);
            }
        }
        
        EXP[e].OUTPUT();
        EXP[e].TRAILING_STOP();
        EXP[e].MODIFY();  
        
        if (EXP[e].set.BUY.Val || EXP[e].set.SEL.Val) EXP[e].ORDERS_SET(); 
        
        AFTER((char)e);
    }
    
    END();       
    BarTime=Time[0];  
}
