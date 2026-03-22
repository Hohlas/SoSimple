#define MAX_REACH          3  // максимальная с открытия
#define NO_LOSS            2  // тейк в безубыток
#define CUR_PRICE          1  // текущая цена
#define LAST_PIC_STOP     -1  // стоп за последний пик 
#define BREAK_EVEN_STOP   -2  // стоп в безубыток 
void EXPERT::OUTPUT(){
   // CLOSE BUY
   if (BUY.Val || set.BUY.Val){ // если есть (рыночные / отложные / готовящиеся к открытию) ордера
      if (iSignal != 3) {
         if (oImp<0 && !IMPULSE_UP())     CLOSE_BUY( 1  ,"ImpulseOver");// отсутствие резкого отскока после входа = закрытие по текущей цене
         if (oImp>0 && !IMPULSE_UP())     CLOSE_BUY( 4  ,"ImpulseOver");// отсутствие резкого отскока после входа = тейк в безубыток
         if (oGlb   && Trnd.Global<0)     CLOSE_BUY(oGlb,"Global<0");      // смена глобального тренда
         if (oLoc   && Trnd.Local<0)      CLOSE_BUY(oLoc,"Local<0");       // смена локального тренда (пробитие нескольких пиков)
         if (oFlt   && POC_CLOSE_TO_BUY())CLOSE_BUY( 1  ,reason+"NearBuy");
         if (Target && BUY.Val>TargetLo)  CLOSE_BUY( 1  ,"TargetLo");
      }
      if (iSignal == 3 && BUY.Typ == MARKET && SHIFT(BUY.T) >= 12) CLOSE_BUY( 1 , "ML_Timeout(12H)"); // Выход по ML горизонту
      }
   // CLOSE SELL
   if (SEL.Val || set.SEL.Val){
      if (iSignal != 3) {
         if (oImp<0 && !IMPULSE_DN())     CLOSE_SEL( 1  ,"ImpulseOver");// отсутствие резкого отскока после входа = закрытие по текущей цене
         if (oImp>0 && !IMPULSE_DN())     CLOSE_SEL( 4  ,"ImpulseOver");// отсутствие резкого отскока после входа = тейк в безубыток
         if (oGlb   && Trnd.Global>0)     CLOSE_SEL(oGlb,"Global>0");      // смена глобального тренда
         if (oLoc   && Trnd.Local>0)      CLOSE_SEL(oLoc,"Local>0");       // смена локального тренда
         if (oFlt   && POC_CLOSE_TO_SEL())CLOSE_SEL( 1  ,reason+"NearSell");
         if (Target && SEL.Val<TargetHi)  CLOSE_SEL( 1  ,"TargetHi");
      }
      if (iSignal == 3 && SEL.Typ == MARKET && SHIFT(SEL.T) >= 12) CLOSE_SEL( 1 , "ML_Timeout(12H)"); // Выход по ML горизонту
      }
   ERROR_CHECK(__FUNCTION__);   
   }  
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ      
bool EXPERT::IMPULSE_UP(){// наличие импульса после открытия. 
   if (BUY.Typ!=MARKET || SHIFT(BUY.T)==1) return(true); // только для открытых ордеров начиная со второго бара 
   double noise=BUY.Val-Low[SHIFT(BUY.T)]; // импульс после открытия  (Shift=1 бар входа, Shift=2 следующий)
   for (int i=bar; i<SHIFT(BUY.T); i++) noise+=(High[i]-Low[i]); // шум  в барах
   A("BuyImpulse="+S4(H-BUY.Val)+" / "+S4(noise), L, bar,  clrGray); // 
   if ((H -BUY.Val)/noise>MathAbs(oImp)*0.1)   return(true); // сигнал/шум в норме
   else return(false);
   }  
bool EXPERT::IMPULSE_DN(){// наличие импульса после открытия
   if (SEL.Typ!=MARKET || SHIFT(SEL.T)==1) return(true); // только для открытых ордеров начиная со второго бара 
   double noise=High[SHIFT(SEL.T)]-SEL.Val; // импульс после открытия
   for (int i=bar; i<SHIFT(SEL.T); i++) noise+=(High[i]-Low[i]); // шум  в барах
   V("SelImpulse="+S4(SEL.Val-L)+" / "+S4(noise), H, bar,  clrGray);
   if ((SEL.Val-L)/noise>MathAbs(oImp)*0.1)   return(true); // сигнал/шум в норме
   else return(false);
   }      
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
bool EXPERT::POC_CLOSE_TO_BUY(){ // цена "отдохнула" (пик или консолидация) перед ордером
   if (BUY.Typ==MARKET) return(false); // рыночные ордера не трогаем
   float OrdPrice=MAX(BUY.Val,set.BUY.Val),  // либо установленная лимитка, либо новый ордер до выставления
         delta=float(oFlt*Atr.Fast/2);
   if (OrdPrice==0) return(false);
   if (PocCnt>3 && PocCenter-OrdPrice<delta+Atr.Fast)    {reason="Poc"; V("Poc",PocCenter,bar,clrGray); return(true);}
   if (F[n].P-OrdPrice<delta && F[n].T>BUY.T)            {reason="Pic"; V("Pic",F[n].P,   bar,clrGray); return(true);}
   return (false);
   }  
bool EXPERT::POC_CLOSE_TO_SEL(){ // цена "отдохнула" (пик или консолидация) перед ордером
   if (SEL.Typ==MARKET) return(false);
   float OrdPrice=MAX(SEL.Val,set.SEL.Val), 
         delta=float(oFlt*Atr.Fast/2);
   if (OrdPrice==0) return(false);
   if (PocCnt>3 && OrdPrice-PocCenter<delta+Atr.Fast)    {reason="Poc"; V("Poc",PocCenter,bar,clrGray); return(true);}  
   if (OrdPrice-F[n].P<delta && F[n].T>SEL.T)            {reason="Pic"; V("Pic",F[n].P,   bar,clrGray); return(true);} 
   return(false);
   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
void EXPERT::CLOSE_BUY(char price, string comment){// 
   if (set.BUY.Val){ // отмена ордера до установки
      X("Del set.Buy: "+comment, set.BUY.Val, bar-1, clrRed);
      set.BUY.Val=0;}
   if (BUY.Typ==NONE || price==0) return;
   if (BUY.Typ==MARKET) Print(Mgc,":: CLOSE_BUY reason=",comment," BUY=",DoubleToString(BUY.Val,Digits));
   if (BUY.Typ!=MARKET){ // отложенный ордер
      X("Del BUY"+ORDTYP(BUY.Typ)+": "+comment, BUY.Val, bar-1, clrRed);
      BUY.Val=0;
      return;}
   if (price>0){ // двигаем тейк 
      float NewProfit=BID; // 
      switch (price){// тип цены закрытия
         case 1:  BUY.Val=0;                       break;   // по текущей
         case 2:  NewProfit=MAX(BID,BUY.Val);      break;   // безубыток или лучше
         case 3:  NewProfit=BUY.Max;               break;   // по максимально достигнутой цене
         default: NewProfit=MAX(BID+Atr.Lim*(price-3),BUY.Val+Atr.Lim);    // c припуском от текущей, но в плюс
         }
      if (NewProfit<BUY.Prf || BUY.Prf==0)   BUY.Prf=NewProfit;  // подтягиваем тейк    
      if (NewProfit-BID<StopLevel)           BUY.Val=0;  // тейк недопустимо близко к цене, просто закрываемся
      X("CloseBuy by moveProfit: "+comment, NewProfit, bar-1,  clrRed);
   }else{// подтягиваем стоп
      float NewStop=0;
      switch (price){
         case -1: NewStop=F[lo].P-Atr.Lim;   break;   // стоп за последний пик 
         case -2: NewStop=BUY.Val;           break;   // стоп в безубыток
         default: NewStop=BID+Atr.Lim*price;          // подтягиваем стоп на 3..5 Atr.Lim
         }   
      if (NewStop>BUY.Stp && BID-NewStop>StopLevel)  BUY.Stp=NewStop;    
      X("CloseBuy by moveStop: "+comment, NewStop, bar-1, clrRed);
   }  }     
void EXPERT::CLOSE_SEL(char price, string comment){
   if (set.SEL.Val){ // отмена ордера до установки
      X("Del set.Sel: "+comment, set.SEL.Val, bar-1, clrRed);
      set.SEL.Val=0;} 
   if (SEL.Typ==NONE || price==0) return;
   if (SEL.Typ==MARKET) Print(Mgc,":: CLOSE_SEL reason=",comment," SEL=",DoubleToString(SEL.Val,Digits));
   if (SEL.Typ!=MARKET){// отложник
      X("Del SELL"+ORDTYP(SEL.Typ)+": "+comment, SEL.Val, bar-1, clrRed);
      SEL.Val=0;
      return;}
   if (price>0){ // двигаем тейк 
      float NewProfit=ASK;
      switch (price){
         case 1:  SEL.Val=0;                       break;   // по текущей
         case 2:  NewProfit=MIN(ASK,SEL.Val);      break;   // не хуже чем безубыток
         case 3:  NewProfit=SEL.Min;               break;   // по минимально достигнутой цене 
         default: NewProfit=MIN(ASK-Atr.Lim*(price-3),SEL.Val-Atr.Lim);    // с припуском от текущей
         }
      if (NewProfit>SEL.Prf || SEL.Prf==0)   SEL.Prf=NewProfit;  
      if (ASK-NewProfit<StopLevel)           SEL.Val=0;     
      X("CloseSELL by moveProfit: "+comment, NewProfit, bar-1,  clrRed);  
   }else{// подтягиваем стоп
      float NewStop=0;       
      switch (price){
         case -1: NewStop=F[hi].P+Atr.Lim;   break;   // стоп за последний пик 
         case -2: NewStop=SEL.Val;           break;   // стоп в безубыток
         default: NewStop=ASK-Atr.Lim*price;          // подтягиваем стоп на 3..5 Atr.Lim
         }   
      if (SEL.Stp<NewStop && NewStop-ASK>StopLevel)  SEL.Stp=NewStop;     
      X("CloseSELL by moveStop: "+comment, NewStop, bar-1, clrRed);
   }  }  
   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ          
void EXPERT::TRAILING_STOP(){//    - T R A I L I N G   S T O P -
   if (Trl==0) return;
   if (BUY.Typ!=MARKET && SEL.Typ!=MARKET) return; 
   float TrlBuy=0, TrlSel=0;    // 
   if (stpL>0)   TrlBuy=F[stpL].P-Atr.Lim;    
   if (stpH>0)   TrlSel=F[stpH].P+Atr.Lim;      
   
   if (BUY.Typ==MARKET && TrlBuy>0 && TrlBuy>BUY.Stp && (TrlBuy>BUY.Val  || Trl<0)){ // 
      A("TRAILING_BUY, Back="+S4(F[stpL].BackVal), TrlBuy, bar, clrBlue);
      BUY.Stp=TrlBuy; }            
   if (SEL.Typ==MARKET && TrlSel>0 && TrlSel<SEL.Stp && (TrlSel<SEL.Val || Trl<0)){//
      V("TRAILING_SELL "+DTIME(F[stpH].T), TrlSel, bar, clrRed); 
      SEL.Stp=TrlSel; } 
   ERROR_CHECK(__FUNCTION__);     
   }

   
     
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ     
/*
void EXPERT::POC_CLOSE_TO_ORDER(){// УДАЛЕНИЕ ОТЛОЖНИКА ЕСЛИ ПЕРЕД НИМ ФОРМИРУЕТСЯ ФЛЭТ.
   if (oFlt==0) return;   // 
   float Near=float(oFlt*Atr.Fast/2);
   if (SEL.Typ==LIMIT || set.SEL.Val){ // пик (poc) перед зоной продажи = цена "отдохнула"
      float price=set.SEL.Val+SEL.Val;
      if (price-PocCenter<Near+ATR/2 && PocCnt>2)   CLOSE_SEL(0,"PocNear"); //{set.SEL.Sig=0; SEL.Val=0; set.SEL.Val=0;  X("PocNearSel", PocCenter, bar+1, clrPurple);} // перед лимиткой cформировалось уплотнение из нескольких бар
      if (price-F[n].P<Near && F[n].T>SEL.T)        CLOSE_SEL(0,"PicNear"); //{set.SEL.Sig=0; SEL.Val=0; set.SEL.Val=0;  X("PicNearSel", F[n].P,    bar+1, clrRed);}    // или пик
      }   
   if (BUY.Typ==LIMIT || set.BUY.Val){  // пик перед зоной продажи = цена "отдохнула"
      float price=set.BUY.Val+BUY.Val;
      if (PocCenter-price<Near+ATR/2 && PocCnt>2)   CLOSE_BUY(0,"PocNear"); //{set.BUY.Sig=0; BUY.Val=0; set.BUY.Val=0;  X("PocNearBuy", PocCenter, bar+1, clrPurple);}
      if (F[n].P-price<Near && F[n].T>BUY.T)        CLOSE_BUY(0,"PicNear"); //{set.BUY.Sig=0; BUY.Val=0; set.BUY.Val=0;  X("PicNearBuy", F[n].P,    bar+1, clrRed);} 
   }  }  
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ     

   
void EXPERT::CLOSE_BUY(float ClosePrice, float MinProfit, string Reason){
   float mark=BUY.Val+mem.BUY.Val;   // запоминаем для постановки крестика 
   mem.BUY.Val=0;  // удаление отложников
   if (BUY.Typ!=MARKET) BUY.Val=0;
   else{
      if (ClosePrice<BUY.Val+MinProfit) ClosePrice=BUY.Val+MinProfit; // двинем выход вверх, если требует жаба
      mark=ClosePrice;
      if (ClosePrice<BUY.Prf || BUY.Prf==0){ // если выход ниже профит таргета, или таргета нет вовсе
         if (ClosePrice-Bid<ATR/4)  BUY.Val=0;   
         else                       BUY.Prf=ClosePrice;
      }  }
   if (mark) X(Reason+"/CloseBuy", mark, 0, clrRed);   // Print("CloseBuy=",CloseBuy," Buy.Val=",BUY.Val); 
   }//ERROR_CHECK(__FUNCTION__+Reason);
   
void EXPERT::CLOSE_SEL(float ClosePrice, float MinProfit, string Reason){
   float mark=SEL.Val+mem.SEL.Val;   // запоминаем для постановки крестика
   mem.SEL.Val=0;  // удаление отложников
   if (SEL.Typ!=MARKET) SEL.Val=0;
   else{
      if (ClosePrice>SEL.Val-MinProfit) ClosePrice=SEL.Val-MinProfit; // двинем выход вверх, если требует жаба
      mark=ClosePrice;
      if (ClosePrice>SEL.Prf || SEL.Prf==0){ // если выход ниже профит таргета, или таргета нет вовсе
         if (Ask-ClosePrice<ATR/4)  SEL.Val=0;   
         else                       SEL.Prf=ClosePrice;
      }  }
   if (mark) X(Reason+"/CloseSel", mark, 0, clrRed);   // Print("CloseBuy=",CloseBuy," Buy.Val=",BUY.Val); 
   }//ERROR_CHECK(__FUNCTION__+Reason);   
*/    
    