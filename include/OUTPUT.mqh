void OUTPUT(){ 
   //if (!BUY.Val && !SEL.Val) return;
   float CloseSel=0, CloseBuy=0; // цена, по которой планируется закрываться
   bool  OutUp=0, OutDn=0;   
   if (OTr>0){// пропадание тренда - удаляем отложники, закрываем позы 
      if (!TrUp) {OutUp=1;}
      if (!TrDn) {OutDn=1;}
      }
   if (OTr<0){// появление противоположного тренда - удаляем отложники, закрываем позы 
      if (TrDn) {OutUp=1;}
      if (TrUp) {OutDn=1;}
      } 
   if (Out){// появление противоположного сигнала
      if (InDn) {OutUp=1;}  
      if (InUp) {OutDn=1;}  
      }  
   
   float Delta =ATR*OD/2; 
   if (Mod>0) Delta=ATR*FIBO(OD); // 0, 0.5, 1, 2, 3, 5
   switch (Oprc){  // расчет цены выходов: 
      case  1: // по рынку немедленно
         CloseBuy=float(Bid)+Delta;     
         CloseSel=float(Ask)-Delta;    
      break;   
      case  2: // профит на максимально достигнутой в сделке цене
         CloseBuy=BUY.Max+ATR/2-Delta; 
         CloseSel=SEL.Min-ATR/2+Delta; 
      break;   
      case  3: // на текущий экстремум
         CloseBuy=HI+ATR/2-Delta; 
         CloseSel=LO-ATR/2+Delta; 
      break; 
      }        
   if (OutUp) CLOSE_BUY(CloseBuy,Present,"OUT");// Выходим из длинной  
   if (OutDn) CLOSE_SEL(CloseSel,Present,"OUT");// Выходим из короткой  
   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ      
void CLOSE_BUY(float ClosePrice, float MinProfit, string Reason){
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
   
void CLOSE_SEL(float ClosePrice, float MinProfit, string Reason){
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
          
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ    
void TRAILING_STOP(){   // 
   if (Tk==0) return;
   float TrlBuy=0, TrlSel=0;
   if (Mod>1){ // Mod=2 пока не используется
      // Print("Mod=2");
   }else if (Mod>0){ // Mod=1
      if (Tk>1){  TrlBuy=H-Tk*ATR;                       TrlSel=L+Tk*ATR;}          // классика через ATR
      if (Tk==1){ TrlBuy=LO-ATR/2;                       TrlSel=HI+ATR/2;}          // текущий HI/LO с допуском ATR/2
      if (Tk==-1){set.BUY.Val=H;  SET_BUY_STOP();         TrlBuy=set.BUY.Stp;         // стандартная функция стопов
                  set.SEL.Val=L;  SET_SEL_STOP();         TrlSel=set.SEL.Stp;}
      if (Tk<-1){ TrlBuy=PIC_LO(bar,0,H+Tk*ATR)-ATR/2;   TrlSel=PIC_HI(bar,0,L-Tk*ATR)+ATR/2;} // пик удаленный на ATR*Tk                                 
   }else TRAILING_OLD(TrlBuy,TrlSel); // Mod=0
   if (BUY.Typ==MARKET && TrlBuy>BUY.Stp && TrlBuy<Bid-StopLevel && (TrlBuy>BUY.Val || TS==0)) {BUY.Stp=TrlBuy;  LINE("TrlBuy", bar,TrlBuy, bar+1,TrlBuy, clrPink,0);}
   if (SEL.Typ==MARKET && TrlSel<SEL.Stp && TrlSel>Ask+StopLevel && (TrlSel<SEL.Val || TS==0)) {SEL.Stp=TrlSel;  LINE("TrlSel", bar,TrlSel, bar+1,TrlSel, clrPink,0);} //{Print("SELL=",SEL.Val," TrlSel=",TrlSel);}  
   ERROR_CHECK(__FUNCTION__);
   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
void TRAILING_PROFIT(){ // модификации профита (профитТаргет тока приближается к цене открытия)  
   if (PM1){// приближение профита при каждом откате
      if (BUY.Typ==MARKET && High[2]>High[1] && SHIFT(BUY.T)>1){// если был обратный откат против позы
         if (BUY.Prf==0)   BUY.Prf=BUY.Max;  // ставим тейк, если не было
         else              BUY.Prf-=float((High[2]-High[1])*(MathAbs(PM1)+1)*(MathAbs(PM1)+1)*0.1); // приближаем на величину каждого отката                              
         if (PM1<0 && BUY.Prf<BUY.Max) BUY.Prf=BUY.Max; // не ближе BUY.Max
         if (BUY.Prf-Bid<ATR/4) {BUY.Val=0;  X("PM1: CloseBuy", BUY.Prf, 0, clrRed);}// тейк слишком близко к рынку, закрываем позу  
         LINE("PM1: BUY.Prf", bar,BUY.Prf, bar+1,BUY.Prf, clrBlue,1);
         }  
      if (SEL.Typ==MARKET &&  Low[2]<Low[1] && SHIFT(SEL.T)>1){
         if (SEL.Prf==0)   SEL.Prf=SEL.Min; 
         else              SEL.Prf+=float((Low[1]-Low [2])*(MathAbs(PM1)+1)*(MathAbs(PM1)+1)*0.1);
         if (Mod==0 && SEL.Prf>=SEL.Val)  SEL.Val=0; // очепятка из прошлых релизов
         if (PM1<0 && SEL.Prf>SEL.Min) SEL.Prf=SEL.Min;
         if (Ask-SEL.Prf<ATR/4) {SEL.Val=0;  X("PM1: CloseSel", SEL.Prf, 0, clrRed);}
         LINE("PM1: SEL.Prf", bar,SEL.Prf, bar+1,SEL.Prf, clrBlue,1);
      }  }
   if (PM2){// если цена провалится от максимальнодостигнутого на xATR, выставляется тейк на максимальнодостигнутый уровень
      float delta=ATR*(PM2+1); // 2  3  4  
      if (BUY.Typ==MARKET && L<BUY.Max-delta && (BUY.Prf>BUY.Max || BUY.Prf==0))   {BUY.Prf=BUY.Max;   LINE("PM2: BUY.Prf", bar,BUY.Prf, bar+1,BUY.Prf, clrBlue,1);}   //     V("MaxFromBuy", MaxFromBuy, bar, clrRed);
      if (SEL.Typ==MARKET && H>SEL.Min+delta && (SEL.Prf<SEL.Min || SEL.Prf==0))   {SEL.Prf=SEL.Min;   LINE("PM2: SEL.Prf", bar,SEL.Prf, bar+1,SEL.Prf, clrBlue,1);}  //     A("MinFromSell", MinFromSell, bar, clrRed);
      }  
   ERROR_CHECK(__FUNCTION__);
   }  
   
    
   
              



