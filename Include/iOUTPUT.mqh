void OUTPUT(){
   if (!BUY  && !SELL) return;
   Buy.Prf=0;  Sel.Prf=0; // значения тейков для обновления ордеров 
      
   if (BUY){  // A("BUY="+S4(BUY)+" Shift="+S0(SHIFT(BuyTime))+" MaxFromBuy="+S4(MaxFromBuy -BUY),  H-ATR*3, 0,  clrGray);
      if (oImp>0 && !IMP_UP(1))                 {CLOSE_BUY();   V("CloseBuy: NoImp",H, bar,  clrBlue);} // отсутствие резкого отскока на первом баре после входа
      if (oSig>0 && (UP<1 || Buy.Pattern==NONE)){CLOSE_BUY();   V("CloseBuy: NoSig UP<1", H, bar,  clrBlue);}  // отсутвствие лонгового сигнала
      if (oSig<0 && DN>0 && UP<1)               {CLOSE_BUY();   V("CloseBuy: OppSig DN>0", H, bar,  clrBlue);} // появление шортового сигнала
      }  
   if (SELL){ //V("SELL="+S4(SELL)+" DN="+S0(DN),  L+ATR*3, 0,  clrGray);// " Shift="+S0(SHIFT(SellTime))+" MinFromSell="+S4(SELL-MinFromSell)
      if (oImp>0 && !IMP_DN(0))                 {CLOSE_SELL();  A("CloseSELL NoImp", L, bar,  clrRed);} // отсутствие резкого отскока на первом баре после входа
      if (oSig>0 && (DN<1 || Sel.Pattern==NONE)){CLOSE_SELL();  A("CloseSELL: NoSig DN<1", L, bar,  clrRed);} // отсутствие шортового сигнала
      if (oSig<0 && UP>0 && DN<1)               {CLOSE_SELL();  A("CloseSELL: OppSig UP>0", L, bar,  clrRed);} // появление лонгового сигнала
      }
   if (Real) ERROR_CHECK("OUTPUT");   
   }  
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ      
char IMP_UP(char PosDir){// Проверка резкого отскока на первом баре лонга
   if (SHIFT(BuyTime) ==2 && MaxFromBuy -BUY <ATR*oImp/2)   return (false); else return (true); // Shift=1 бар входа, Shift=2 следующий
   }  
char IMP_DN(char PosDir){// Проверка резкого отскока на первом баре шорта
   if (SHIFT(SellTime)==2 && SELL-MinFromSell<ATR*oImp/2)   return (false); else return (true); // *SHIFT(SellTime)
   }    
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
void CLOSE_BUY(){
   float NewProfit; 
   switch (oPrice){    
      default: NewProfit=(float)Bid;               break; // закрытие по рынку
      case 1:  NewProfit=(float)Bid +DELTA(0);  break; // тейк перед текущей ценой
      case 2:  NewProfit=BUY        +DELTA(0);  break; // тейк перед входом
      case 3:  NewProfit=MaxFromBuy +DELTA(0);  break; // тейк на максимальную цену с момента открытия позы
      }
   if (NewProfit-Bid<StopLevel) {BUY=0;   Modify=true; return;} // тейк недопустимо близко к цене, просто закрываемся
   if (NewProfit>0 && (NewProfit<PROFIT_BUY || PROFIT_BUY==0)) {PROFIT_BUY=NewProfit;     Modify=true;}  V("CLOSE: PROFIT_BUY="+S4(PROFIT_BUY), PROFIT_BUY, bar,  clrGray);
   }  
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ     
void CLOSE_SELL(){
   float NewProfit;
   switch (oPrice){    
      default: NewProfit=(float)Ask;               break; // закрытие по рынку
      case 1:  NewProfit=(float)Ask -DELTA(0);  break; // тейк перед текущей ценой
      case 2:  NewProfit=SELL       -DELTA(0);  break; // тейк перед входом
      case 3:  NewProfit=MinFromSell-DELTA(0);  break; // тейк на максимальную цену с момента открытия позы
      }
   if (Ask-NewProfit<StopLevel) {SELL=0; Modify=true; return;} // тейк недопустимо близко к цене, просто закрываемся  
   if (NewProfit>0 && (NewProfit>PROFIT_SELL || PROFIT_SELL==0)) {PROFIT_SELL=NewProfit;   Modify=true;}   
   }     
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ          
void TRAILING(){//    - T R A I L I N G   S T O P -
   if (Trl==0) return;
   float StpBuy=0, StpSel=0, minHI=999999, minLO=999999, MinBack=Atr.Max*MathAbs(Trl);    // и заднего фронтов; 
   uchar TrlHi=0, TrlLo=0; 
   switch (MathAbs(Trl)){ 
      case 1: // Первые Уровни
         if (LO>0)   StpBuy=F[LO].P-Atr.Lim;    
         if (HI>0)   StpSel=F[HI].P+Atr.Lim;      
      break;
      default:// Пики с достаточным отскоком Back
         for (uchar f=1; f<LevelsAmount; f++){ 
            if (F[f].P==0)    continue; // пустые значения пропускаем
            if (F[f].Brk>0)  continue; // только непробитые,        
            if (MathAbs(F[f].P-F[f].Back)<MinBack) continue; // уровень должен быть с достаточным отскоком 
            if (F[f].Dir>0 && F[f].T>SellTime)  LOWEST_HI (H, minHI, f, TrlHi);  // пик, образовавшийся после продажи
            if (F[f].Dir<0 && F[f].T>BuyTime)   HIGHEST_LO(L, minLO, f, TrlLo);  // впадина, образовавшаяся после покупки
            }
         if (TrlLo>0)   StpBuy=F[TrlLo].P-Atr.Lim;    
         if (TrlHi>0)   StpSel=F[TrlHi].P+Atr.Lim;      
      break;
      } //Print("TRAILING: SetSTOP_SELL=",SetSTOP_SELL," hi=",F[hi].P," H=",H);
   if (BUY  && StpBuy>0 && StpBuy-STOP_BUY>ATR  && (StpBuy>BUY  || Trl<0)){ // 
      A("TRAILING_BUY="+S4(StpBuy), StpBuy, bar, clrGreen);
      STOP_BUY=StpBuy; Modify=true;}            
   if (SELL && StpSel>0 && STOP_SELL-StpSel>ATR && (StpSel<SELL || Trl<0)){//
      V("TRAILING_SELL="+S4(StpSel), StpSel, bar, clrGreen);
      STOP_SELL=StpSel; Modify=true;} 
   if (Real) ERROR_CHECK("TRAILING");     
   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ     
void POC_CLOSE_TO_ORDER(){// УДАЛЕНИЕ ОТЛОЖНИКА ЕСЛИ ПЕРЕД НИМ ФОРМИРУЕТСЯ ФЛЭТ. Проверяется в COUNT()
   if (oFlt==0) return;   // 
   float Near=float(ATR*0.5*oFlt);
   if (SELLLIMIT>0){ // пик (poc) перед зоной продажи = цена "отдохнула"
      if (PocCnt>2 && SELLLIMIT-PocCenter<Near)       {Sel.Pattern=0; SELLLIMIT=0; Modify=true; X("PocNearSel",PocCenter, bar, clrRed);}         // перед лимиткой cформировалось уплотнение из нескольких бар
      if (SELLLIMIT-F[hi].P<Near && F[hi].T>SellTime) {Sel.Pattern=0; SELLLIMIT=0; Modify=true; X("HiNearSel", F[hi].P, SHIFT(F[hi].T), clrRed);}  // или вершина
      if (SELLLIMIT-F[lo].P<Near && F[lo].T>SellTime) {Sel.Pattern=0; SELLLIMIT=0; Modify=true; X("LoNearSel", F[lo].P, SHIFT(F[lo].T), clrRed);}  // или впадина
      }   
   if (BUYLIMIT>0){  // пик перед зоной продажи = цена "отдохнула"
      if (PocCnt>2 && PocCenter-BUYLIMIT<Near)        {Buy.Pattern=0; BUYLIMIT=0;  Modify=true; X("PocNearBuy",PocCenter, bar, clrRed);}
      if (F[lo].P-BUYLIMIT<Near && F[lo].T>BuyTime)   {Buy.Pattern=0; BUYLIMIT=0;  Modify=true; X("LoNearBuy", F[lo].P, SHIFT(F[lo].T), clrRed);} 
      if (F[hi].P-BUYLIMIT<Near && F[hi].T>BuyTime)   {Buy.Pattern=0; BUYLIMIT=0;  Modify=true; X("HiNearBuy", F[hi].P, SHIFT(F[hi].T), clrRed);}
   }  } 
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ            



   