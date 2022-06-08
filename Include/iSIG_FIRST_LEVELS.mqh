
void SIG_NULL(){
   Buy.Pattern=GOGO;    // сигнал на открытие позы
   Buy.Inp=(float)Ask;// трендовый уровень первого пика
   Buy.Stp=(float)Ask-Atr.Max*2; // 
   Buy.Prf=(float)Ask+Atr.Max*5; // 
   Sel.Pattern=GOGO;    // сигнал на открытие позы
   Sel.Inp=(float)Bid;// трендовый уровень первого пика
   Sel.Stp=(float)Bid+Atr.Max*2; // 
   Sel.Prf=(float)Bid-Atr.Max*5; // 
   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ  
void SIG_FIRST_LEVELS(){   // 
   float FarAway=float(ATR*Front/2);     
   // Ш О Р Т О В Ы Е   П А Т Т Е Р Н Ы   ////////////////////////////////////////////////////////////////////////////
   if (Sel.Mem!=F[HI].P){// при обновлении Первого Уровня на Продажу
      Sel.Mem=F[HI].P;
      Sel.Pattern=WAIT;          // сигнал переходит на стадию ожидания,
      }//V("HI="+S0(HI), F[HI].P, bar, clrPink);
   if (SELL) {Sel.Pattern=NONE;}
   switch (Sel.Pattern){ 
      case WAIT:  // удаление от ЗОНЫ ПРОДАЖИ
         if (F[HI].P-H>FarAway){// цена опустилась от уровня продажи достаточно далеко
            Sel.T=Time[bar];// время формирования сигнала
            Sel.Pattern=GOGO;    // сигнал на открытие позы
            V("GOGO", H, bar,  clrGreen);
            Sel.Inp=F[HI].Tr+DELTA(D);    // вход в зоне продажи
            Sel.Stp=F[HI].P+DELTA(Stp);   // за первый пик
            Sel.Prf=F[HI].Back;           // тейк на величину движения, которое дал уровень
            }  
      break;
      case GOGO:// после выставления ордеров при начале приближения к точке входа снимаем сигнал  
         if (F[HI].P-H<FarAway) {Sel.Pattern=WAIT;   V("WAIT", H, bar,  clrGreen);}           
      break;
      }     
   // Л О Н Г О В Ы Е   П А Т Т Е Р Н Ы   ////////////////////////////////////////////////////////////////////////////
   if (Buy.Mem!=F[LO].P){// при обновлении Первого Уровня на Покупку
      Buy.Mem=F[LO].P;
      Buy.Pattern=WAIT;          // сигнал переходит на стадию ожидания,
      }  // A("LO="+S0(LO), F[LO].P, bar, clrLightBlue);
   if (BUY) {Buy.Pattern=NONE;} // X(" ", Close[bar], bar, clrBlue);
   switch (Buy.Pattern){ 
      case WAIT:  // удаление от ЗОНЫ ПОКУПКИ
         if (L-F[LO].P>FarAway){// цена поднялась над уровнем покупки достаточно высоко
            Buy.T=Time[bar];// время формирования сигнала
            Buy.Pattern=GOGO;    // сигнал на открытие позы
            A("GOGO", L, bar,  clrGreen);
            Buy.Inp=F[LO].Tr-DELTA(D); // верх зоны покупки
            Buy.Stp=F[LO].P-DELTA(Stp);  // за первый пик
            Buy.Prf=F[LO].Back;  
            }  
      break;
      case GOGO:// после выставления ордеров снимаем сигнал   
         if (L-F[LO].P<FarAway) {Buy.Pattern=WAIT; A("WAIT", L, bar,  clrGreen);}          
      break;//       
      }  
   if (Real) ERROR_CHECK("SIG_SIMPLE");
   }
