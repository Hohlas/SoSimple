// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
void LONG_FIRST_LEV(){
   // ПРОВЕРКА НЕОБХОДИМЫХ УСЛОВИЙ
   if (Buy.Zone.time!=F.Lo.time){// при смене первых уровней
      Buy.Pattern=WAIT;          // сигнал сбрасывается на стадию ожидания,
      BUYSTOP=0; BUYLIMIT=0;}    // установленные ордера отменяются
   Buy.Zone.time=F.Lo.time;      // запоминаем время формирования первых уровней
   if (Lo.Pic<Buy.Sig1.Pic) {Buy.Pattern=WAIT;} // при обновлении пика перезаход
   if (BUY) {Buy.Pattern=BLOCK;} // X(" ", Close[bar], bar, clrBlue);
   
   // ПООЧЕРЕДНОЕ ОТСЛЕЖИВАНИЕ ПАТТЕРНОВ
   switch (Buy.Pattern){
   case WAIT:  // ОЖИДАНИЕ КАСАНИЯ ЗОНЫ ПОКУПКИ
      X("Lo.Pic="+S4(Lo.Pic), Lo.Pic, bar, clrGray);
      if (Lo.Pic<Buy.Zone.Up && Lo.Pic>Buy.Zone.Dn && Lo.time>F.Lo.time){ // последний пик в зоне продажи и возник после ее формирования
         Buy.Pattern=START;   // переключение на следующий паттерн - "откат"
         Buy.Sig1=Lo;         // копирование структуры пиков в структуру сигналов (все уровни и времена)
         X("WAIT Frnt="+S4(Buy.Sig1.Frnt), Buy.Sig1.Pic, SHIFT(Buy.Sig1.time), clrOrangeRed);
         }
   break;
   case START: // ОТКАТ = формирование уровня, пробой которого даст подтверждение
      // I вариант
      if (Hi.time>Buy.Sig1.time){// после нижнего пика возник пик и он в зоне покупки    && Lo.Pic>Buy.Zone.Dn
         Buy.Pattern=CONFIRM;    // подтверждение пробоем ближайшего трендового
         Buy.Sig2=Hi;    //  копирование структуры пиков в структуру сигналов (все уровни и времена)
         X("START Pic="+S4(Buy.Sig1.Pic), Buy.Sig2.Pic, bar, clrYellow);
         }
      // II вариант
      if (Low[bar]<Low[bar+1]){ // из хаев образовалась впадина (трендовый уровень на покупку)
         Buy.Pattern=CONFIRM;      // подтверждение пробоем ближайшего трендового
         Buy.Sig2.Pic=High[bar+1]; // значение самого пика и 
         Buy.Sig2.Mid=High[bar+1]-(High[bar+1]-Low[bar+1])/3; // его серединки
         Buy.Sig2.time=Time[bar+1];// момент отката
         X("START Pic="+S4(Buy.Sig1.Pic), Buy.Sig2.Pic, bar, clrYellow);
         }     
   break;
   case CONFIRM:// ПОДТВЕРЖДЕНИЕ
      if (High[bar]>Buy.Sig2.Mid && Time[bar]-Buy.Sig2.time<BarSeconds*10){   // противоположный пик подтверждения пробит не позже 10бар
         Buy.Pattern=GOGO;         // сигнал на открытие позы
         Buy.Opn=Buy.Sig1.Trd;   // трендовый уровень первого пика
         Buy.Opn=Buy.Sig2.Mid;   // серединка второго пика (подтверждающего)
         Buy.Stp=F.Lo.Pic;       // за первый пик (уровень) 
         Buy.Prf=Buy.Sig1.Pic+Buy.Sig1.Frnt/3; // треть движения, коснувшегося зоны покупки
         X("CONF Pic.Front="+S4(Lo.Pic+Buy.Sig1.Frnt)+"Stp="+S4(Buy.Stp), Buy.Opn, bar,  clrWhite);
         }
   break;
   case GOGO:  break;//Buy.Pattern=WAIT;      
   }  }