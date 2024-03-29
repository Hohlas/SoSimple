
void EXPERT::SIG_FALSE_BREAK(){// при iSignal=1  
   // iParam=0..3 - Максимальный вылет ложняка = ATR*(iParam+1). /lib_flat.mqh
   // П Р О Б О Й   В Е Р Ш И Н Ы  =  Ш О Р Т    ////////////////////////////////////////////////////////////////////////////
   if (mem.SEL.Val!=FlsUp && F[FlsUp].Fls.Phase==GOGO && set.SEL.Sig!=GOGO){// образовался новый ложняк, он подтвердился, нет сигнала от прошлого ложняка
      mem.SEL.Val=FlsUp;  // фиксим номер ложняка
      set.SEL.Sig=GOGO;    // сигнал на открытие позы
      set.SEL.T=Time[bar];// время формирования сигнала
      /*    D   */   // цена входа (c подтверждением)
      /*  5.. 3 */   if (D> 2)   set.SEL.Val = F[FlsUp].P       +float((D-4)*ATR/2); else  // лимитник от пробитой вершины  -0.5 .. +0.5 ATR
      /*  2.. 0 */   if (D>=0)   set.SEL.Val = F[FlsUp].Fls.Base+float((D-1)*ATR/2); else  // лимитник от базы ложняка      -0.5 .. +0.5 ATR
      // без подтверждения - сразу ставим ордер на пробой при D<0
      /* -1..-2 */   if (D>-3)   set.SEL.Val = F[FlsUp].P       +float((D+1)*ATR/2); else  // обратный пробой пробитой вершины  -0.5 .. +0 ATR
      /* -3..-5 */               set.SEL.Val = F[FlsUp].Fls.Base+float((D+4)*ATR/2);       // пробой базы ложняка           -0.5 .. +0.5 ATR
      set.SEL.Stp=F[FlsUp].Fls.P+DELTA(Stp);// за пик ложняка
      set.SEL.Prf=F[FlsUp].Back;// тейк на величину движения, которое дал уровень
      //V("GOGO "+S0(FlsUp), set.SEL.Val, bar,  clrGreen);
      }  
   if (set.SEL.Sig==GOGO && F[FlsUp].Fls.Phase==NONE){// отмена сигнала при отмене ложняка 
      set.SEL.Sig=NONE;
      }       
      
   // П Р О Б О Й   В П А Д И Н Ы  =  Л О Н Г   ////////////////////////////////////////////////////////////////////////////
   if (mem.BUY.Val!=FlsDn && F[FlsDn].Fls.Phase==GOGO && set.BUY.Sig!=GOGO){// образовался новый ложняк, он подтвердился, нет сигнала от прошлого ложняка 
      mem.BUY.Val=FlsDn;  // фиксим номер ложняка
      set.BUY.Sig=GOGO;    // сигнал на открытие позы
      set.BUY.T=Time[bar];// время формирования сигнала
      /*    D   */   // цена входа (c подтверждением)
      /*  5.. 3 */   if (D> 2)   set.BUY.Val = F[FlsDn].P       -float((D-4)*ATR/2); else  // лимитник от пробитой впадины  -0.5 .. +0.5 ATR
      /*  2.. 0 */   if (D>=0)   set.BUY.Val = F[FlsDn].Fls.Base-float((D-1)*ATR/2); else  // лимитник от базы ложняка      -0.5 .. +0.5 ATR
      // без подтверждения - сразу ставим ордер на пробой при D<0
      /* -1..-2 */   if (D>-3)   set.BUY.Val = F[FlsDn].P       -float((D+1)*ATR/2); else  // обратный пробой пробитой впадины  -0.5 .. +0 ATR
      /* -3..-5 */               set.BUY.Val = F[FlsDn].Fls.Base-float((D+4)*ATR/2);       // пробой базы ложняка           -0.5 .. +0.5 ATR
      set.BUY.Stp=F[FlsDn].Fls.P-DELTA(Stp);  // за первый пик
      set.BUY.Prf=F[FlsDn].Back;// тейк на величину движения, которое дал уровень
      //A("GOGO "+S0(FlsDn), set.BUY.Val, bar,  clrGreen);
      }
   if (set.BUY.Sig==GOGO && F[FlsDn].Fls.Phase==NONE){     // отмена ложняка
      set.BUY.Sig=NONE;
      }
   if (Real) ERROR_CHECK("FALSE_BREAK_SIG");
   }
   
   
   
