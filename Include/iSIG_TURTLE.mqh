


void EXPERT::SIG_TURTLE(){
   // УДАЛЕНИЕ ОТЛОЖНИКА ПРИ "ПЕРЕДЫШКЕ" ЦЕНЫ ПЕРЕД НИМ
   //if (Update==True){
      if (SEL.Typ==STOP && High[bar]>mem.SEL.Val) {set.SEL.Sig=0; SEL.Val=0;} // повторный пробой пробивающего пика (ложняк пробился), 
      if (BUY.Typ==STOP  && Low [bar]<mem.BUY.Val) {set.BUY.Sig=0; BUY.Val=0;} // отменяем сигнал
      
      if (BrokenPic>0 && // номер последнего пробитого пика
         F[BrokenPic].Back>=ATR*PicPwr && // с достаточным отскоком
         F[BrokenPic].TrBrk >-1 &&  // сформированным трендовым уровнем
         F[BrokenPic].Per>FltLen*5 && SHIFT(F[BrokenPic].T)>FltLen){   // период последнего пробитого пика достаточно велик и с момента его формирования до пробоя больше FltLen бар
         
         if (F[BrokenPic].Dir>0){// пробита вершина
            set.SEL.Sig=WAIT; // ждем окончания формирования пробивающего пика
            set.SEL.T=Time[bar];         // время пробивающего бара
            mem.SEL.Val=F[BrokenPic].P;  // значение пробитой вершины
            //if (D>-2) {BUY_PRICE(F[lo].P);}// низ зоны продажи
            //else     set.SEL.Val=F[BrokenPic].P+DELTA(D+2);  // стоп ордер на возврат к пробитой вершине 
            set.SEL.Prf=set.SEL.Val-ATR*5; 
            //V(" Per="+S0(F[BrokenPic].Per)+" Shift="+S0(SHIFT(F[BrokenPic].T)), H, bar, clrRed);
            LINE(" ", SHIFT(F[BrokenPic].T),F[BrokenPic].P, bar,H, clrGray,0); 
         }else{// пробитая впадина
            set.BUY.Sig=WAIT;
            set.BUY.T=Time[bar];
            //if (D>-2) {SELL_PRICE(F[hi].P);}     // последняя вершинка, из которой был выстрел
            //else     set.BUY.Val=F[BrokenPic].P-DELTA(D+2); // пробитая впадина
            set.BUY.Prf=set.BUY.Val+ATR*5;
            //A(" Per="+S0(F[BrokenPic].Per)+" Shift="+S0(SHIFT(F[BrokenPic].T)), L, bar, clrBlue);
            LINE("  Tbuy="+DTIME(set.BUY.T)+" New="+S4(set.BUY.Val), SHIFT(F[BrokenPic].T),F[BrokenPic].P, bar,L, clrGray,0);
            }
         }
      if (set.SEL.Sig==WAIT && F[hi].T>=set.SEL.T){  // дождались формирования пробивающего пика
         set.SEL.Sig=GOGO;    // сигнал на открытие позы
         mem.SEL.Val=F[hi].P; // запомним теперь значение пробивающей вершины
         set.SEL.Stp=F[hi].P;  // за первый пик
         V(" GOGO Mem="+S4(mem.SEL.Val), F[hi].P, SHIFT(F[hi].T), clrRed);
         }
      if (set.BUY.Sig==WAIT && F[lo].T>=set.BUY.T){ 
         set.BUY.Sig=GOGO;
         mem.BUY.Val=F[lo].P; // запомним значение пробивающей впадины
         set.BUY.Stp=F[lo].P;  // за первый пик
         A(" GOGO Mem="+S4(mem.BUY.Val), F[lo].P, SHIFT(F[lo].T), clrBlue);
         }       
   //if (Real) ERROR_CHECK("SIG_TURTLE");
   }
