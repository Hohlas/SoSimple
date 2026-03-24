

// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ  

void EXPERT::SIG_FIRST_LEVELS(){ // От первых уровней и уровней серединки.  iSignal=1;   
   //LINE(DTIME(F[LO].T)+" LO="+S4(F[LO].P)+" LO2="+S0(LO2), bar+1, Close[bar+1]+Atr.Lim, bar, Close[bar]+Atr.Lim,  clrRed,0);
   uchar PIC;
   if (UP){
      if (MidTyp==0) PIC=LO;  // работа от первых уровней с максимальным Pwr Imp Cnt за Days  дней   
      else           PIC=LO2;  // работа от уровней серединки: MidTyp=  1-MaxFront, 2-MaxFront*MaxPics, 3-MaxPics, 4-PwrSum
      if (PIC>0 && mem.BUY.Val!=PIC){  // F[PIC].P+F[PIC].BackVal+F[PIC].Mid   
         mem.BUY.Val=PIC;
         set.BUY.T=Time[bar]; // время формирования сигнала
         set.BUY.Sig=GOGO;    // сигнал на открытие позы
         OPEN_BUY(PIC);    
         A("BUY "+S0(PIC),F[PIC].P,bar,  clrGreen); // 
      }  }  
   if (DN){
      if (MidTyp==0) PIC=HI;
      else           PIC=HI2; 
      if (PIC>0 && mem.SEL.Val!=PIC){  // 
         mem.SEL.Val=PIC;
         set.SEL.T=Time[bar]; // время формирования сигнала
         set.SEL.Sig=GOGO;    // сигнал на открытие позы
         OPEN_SELL(PIC);  
         V("SEL "+S0(PIC),F[PIC].P, bar,  clrGreen); // 
      }  } 
   if (Real) ERROR_CHECK(__FUNCTION__);
   }



