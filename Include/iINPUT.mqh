struct SIG{    // Buy, Sell  СИГНАЛЫ 
   datetime T;    // последнее время обновления зоны
   char Pattern;         // отслеживаемый паттерн
   float Mem,Inp,Stp,Prf;  // цена сигнала, цены ордеров
   PICS Sig1,Sig2;      // вложенная структура предварительных сигналов и сигналов подтверждения
   }; 
SIG Sel,Buy;
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
void INPUT(){
   //if (LO==0 || HI==0)  return; // если первые уровни не определены все сигналы блокируются
   Buy.Inp=0; Buy.Stp=0; Buy.Prf=0;    Sel.Inp=0; Sel.Stp=0; Sel.Prf=0; // значения ордеров 
   MinStop=MathAbs(sMin)*Atr.Max/2;
   MaxStop=MathAbs(sMax)*Atr.Max+MinStop; 
   if (BUY)    UP=0; // UP,DN могут принимать значения -1..2
   if (SELL)   DN=0;  
   //SIG_LINES(UP==1," UP="+S0(UP)+" Buy="+S4(BUY) +" BuyLim="+S4(BUYLIMIT), 
   //          DN==1," DN="+S0(DN)+" Sel="+S4(SELL)+" SelLim="+S4(SELLLIMIT),clrSIG1);
   // ПЕРЕКЛЮЧАТЕЛЬ ГЛОБАЛЬНЫХ СИГНАЛОВ.
   switch(iSignal){ 
      case 1:  FALSE_BREAK_SIG();   break;   // работает в lib_PIC
      case 2:  SIG_FIRST_LEVELS();        break;   // ОТСКОК  (iParam=0..4~лимитка удаляется при приближении цены  ATR*Back*2/(iParam+1)
      case 3:  SIG_FIRST_LEVELS_CONFIRM();   break;   // LONG_FIRST_LEV(); 
      case 4:  SIG_TURTLE();        break;
      default: SIG_NULL();          break;   // БЕЗ ГЛОБАЛОВ
      }
   if (Buy.Pattern!=GOGO) UP=0;
   if (Sel.Pattern!=GOGO) DN=0;   
   SIG_LINES(Buy.Pattern==GOGO,"GOGO: UP="+S0(UP)+" Buy="+S4(BUY) +" BuyLim="+S4(BUYLIMIT), 
             Sel.Pattern==GOGO,"GOGO: DN="+S0(DN)+" Sel="+S4(SELL)+" SelLim="+S4(SELLLIMIT),clrSIG1);  // линии сиглалов MovUP и MovDN: (сигналы, смещение от H/L, цвет)      
   if (ExpirBars<0){// удаление отложника при пропадании сигнала
      if (DN<1 && (SELLSTOP>0 || SELLLIMIT>0))  {SELLSTOP=0; SELLLIMIT=0; Modify=true;}
      if (UP<1 && (BUYSTOP>0  ||  BUYLIMIT>0))  {BUYSTOP=0;  BUYLIMIT=0;  Modify=true;} 
      }
   //LINE("Up/Dn="+S0(UP)+"/"+S0(DN)+" FlsUpDn="+S0(FlsUp)+"/"+S0(FlsDn)+" FlsPhase="+S0(F[FlsUp].Fls.Phase)+"/"+S0(F[FlsDn].Fls.Phase)+" PtrnBuy/Sel="+S0(Buy.Pattern)+"/"+S0(Sel.Pattern), bar+1, Close[bar+1], bar, Close[bar],  clrSilver,0); 
   LINE("FlsUp/Dn="+S0(FlsUp)+"/"+S0(FlsDn)+" PhaseUp/Dn"+S0(F[FlsUp].Fls.Phase)+"/"+S0(F[FlsDn].Fls.Phase)+" PatternBuy/Sel="+S0(Buy.Pattern)+"/"+S0(Sel.Pattern), bar+1, Close[bar+1], bar, Close[bar],  clrSilver,0);
   if (UP<1 && DN<1) return; // UP,DN могут принимать значения -1..2
   //  SET  INPUT
   switch (Iprice){   
      case  2: // от Первых Уровней    V("F[HI].P"+S4(F[HI].P),F[HI].P, bar, clrWhite);
         SET_OPEN(LO, HI);       
         SET_STOP(F[LO].P, F[HI].P); // установка и проверка стопов                          
      break;                                    
      case  1: // из функций сигналов V("Sel.Inp="+S4(Sel.Inp),Sel.Inp, bar, clrYellow);       
         SET_STOP(Buy.Stp,    Sel.Stp); // проверка стопов                       
      break;             
      case  0: // по текущей цене
         if (UP>0) Buy.Inp=float(Ask)-DELTA(D);  
         if (DN>0) Sel.Inp=float(Bid)+DELTA(D);  
         SET_STOP(F[stpL].P, F[stpH].P); // за ближайшие сильные пики               
      break;   
      case -1: // Пробой первых уровней
         SET_OPEN(HI, LO);       
         SET_STOP(Buy.Inp-MinStop, Sel.Inp+MinStop);  
      break;
      }//LINE("Up/Dn="+S0(UP)+"/"+S0(DN)+" BUY/Stp-SELL/Stp="+S4(Buy.Inp)+"/"+S4(Buy.Stp)+"-"+S4(Sel.Inp)+"/"+S4(Sel.Stp), bar+1, Close[bar+1], bar, Close[bar],  clrGray,0);   
   // SET  PROFIT
   switch (Prf){
      default: Buy.Prf=Buy.Inp+DELTA(Prf+1);   Sel.Prf=Sel.Inp-DELTA(Prf+1);  break;   // ATR
      case  0: Buy.Prf=Buy.Inp+50*ATR;         Sel.Prf=Sel.Inp-50*ATR;        break;   // в бесконечность
      case -1: ;                                                              break;   // из функции сигналов
      case -2: Buy.Prf=F[HI].Tr;              Sel.Prf=F[LO].Tr;              break;   // трендовый уровень первого
      case -3: Buy.Prf=F[LO].Back;            Sel.Prf=F[HI].Back;            break;   // задний фронт первого уровня
      }     
   if (pDiv>0){// приближаем тейк на:  3/4, 1/2, 1/4
      Buy.Prf=Buy.Inp+(Buy.Prf-Buy.Inp)*(4-pDiv)/4; 
      Sel.Prf=Sel.Inp-(Sel.Inp-Sel.Prf)*(4-pDiv)/4; 
      }
   if (Target!=0){// Целевые уровни 
      if (TrgHi>0 && F[TrgHi].P<Buy.Prf) Buy.Prf=F[TrgHi].P; // если целевой уровень ближе установленного тейка,
      if (TrgLo>0 && F[TrgLo].P>Sel.Prf) Sel.Prf=F[TrgLo].P; // просто приближаем тейк на целевой уровень
      } 
   SIG_LINES(UP,"2 Buy.Inp=" +S4(Buy.Inp) +" Buy.Inp="+S4(Buy.Inp), 
             DN,"2 Sel.Inp="+S4(Sel.Inp)+" Sel.Inp="+S4(Sel.Inp),clrSIG2);     
   PL_CHECK();// ПРОВЕРКА СООТНОШЕНИЯ Profit/Loss        //if (Prn) Print("2 Sel.Inp=",S4(Sel.Inp)," Sel.Prf=",S4(Sel.Prf)," HI=",F[HI].P," StrLo=",F[StrLo].P," FltLo=",F[FltLo].P);   
   // УДАЛЕНИЕ СТАРЫХ ОРДЕРОВ
   if (ExpirBars==0){// Удаление отложников при появлении нового сигнала
      if (Buy.Inp >0 && (MathAbs(Buy.Inp -MathMax(BUYSTOP ,BUYLIMIT ))>ATR/2 || MathAbs(Buy.Stp -STOP_BUY)>ATR/2))    {BUYSTOP=0;    BUYLIMIT=0;   Modify=true;}  //    X("BUYLIMIT=" +S4(BUYLIMIT)+ " Buy.Inp=" +S4(Buy.Inp), BUYLIMIT, 0, clrBlack);
      if (Sel.Inp>0 && (MathAbs(Sel.Inp-MathMax(SELLSTOP,SELLLIMIT))>ATR/2 || MathAbs(Sel.Stp-STOP_SELL)>ATR/2))   {SELLSTOP=0;   SELLLIMIT=0;  Modify=true;}   //  X("SELLLIMIT="+S4(SELLLIMIT)+" Sel.Inp="+S4(Sel.Inp),SELLLIMIT,0, clrBlack);
   }else{// новый сигнал игнорируется, пока стоит старый отложник, который удалится по экспирации (>0) либо при пропадании сигнала (<0)
      if (BUYSTOP  || BUYLIMIT)  Buy.Inp=0;
      if (SELLSTOP || SELLLIMIT) Sel.Inp=0;
      }
   //if (Sel.Inp)   Sel.Pattern=DONE; // ордер готов,
   //if (Buy.Inp)    Buy.Pattern=DONE; // сбрасываем паттерн   
   SIG_LINES(Buy.Inp ,"3 Buy.Inp="+S4(Buy.Inp)+" BUYLIMIT="+S4(BUYLIMIT), 
             Sel.Inp,"3 Sel.Inp="+S4(Sel.Inp)+" SELLLIMIT="+S4(SELLLIMIT),clrSIG3); // линии сиглалов UP и DN: (сигналы, цвет)
   if (Real) ERROR_CHECK("INPUT");
   }    
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
void SET_OPEN (uchar b, uchar s){// УСТАНОВКА ЦЕНЫ ОТКРЫТИЯ  
   if (UP>0 && b>0){ // UP,DN могут принимать значения -1..2
      if (D>0)  Buy.Inp=F[b].P+DELTA(1-D); // пик и ниже
      if (D==0) Buy.Inp=F[b].Mid;
      if (D<0)  Buy.Inp=F[b].Tr-DELTA(1+D);// трендовый и выше
      } //V("DN="+S0(DN)+" s="+S0(s)+" Sel="+S4(F[s].Mid),H, bar, clrSilver);  
   if (DN>0 && s>0){
      if (D>0)  Sel.Inp=F[s].P-DELTA(1-D);// пик и выше
      if (D==0) Sel.Inp=F[s].Mid;
      if (D<0)  Sel.Inp=F[s].Tr+DELTA(1+D);// трендовый и ниже
   }  }  
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
void SET_STOP (float BuyStop,  float SelStop) {// УСТАНОВКА СТОПА дальше, чем предыдущий вариант с проверками 
   if (UP>0 && Buy.Inp>0 && BuyStop>0){ // OrdSet-тип ордера (1-выставление, 0-модификация)
      Buy.Stp=BuyStop-DELTA(Stp);
      if (sMin!=0 && Buy.Inp -Buy.Stp<MinStop){// стоп слишком близко
         if (sMin<0)  Buy.Stp=Buy.Inp -MinStop; else Buy.Inp=Buy.Stp+MinStop;}// отодвигаем стоп, либо вход от стопа
      if (sMax!=0 && Buy.Inp -Buy.Stp>MaxStop){// стоп слишком далеко 
         if (sMax<0)  Buy.Inp=0; else Buy.Inp=Buy.Stp+MaxStop;}  // не ставим, либо пододвигаем вход к стопу   A("stop "+S0(OrdSet),Buy.Stp,0,clrBlue);
      }  
   if (DN>0 && Sel.Inp>0 && SelStop>0){// OrdSet-тип ордера (1-выставление, 0-модификация)
      Sel.Stp=SelStop+DELTA(Stp);
      if (sMin!=0 && Sel.Stp-Sel.Inp<MinStop){// стоп слишком близко
         if (sMin<0)  Sel.Stp=Sel.Inp+MinStop; else Sel.Inp=Sel.Stp-MinStop;}// отодвигаем стоп, либо вход от стопа
      if (sMax!=0 && Sel.Stp-Sel.Inp>MaxStop){// стоп слишком далеко
         if (sMax<0)  Sel.Inp=0; else Sel.Inp=Sel.Stp-MaxStop;}  // не ставим, либо пододвигаем вход к стопу  V("stop "+S0(OrdSet),Sel.Stp,0,clrRed);
   }  }  
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
void TARGET_ZONE_CHECK(float& buy, float& sel){// ЗАКРЫТИЕ ОРДЕРОВ, ПОПАДАЮЩИХ В ЗОНУ ЦЕЛЕВОГО ДВИЖЕНИЯ
   if (Target==0) return;
   if (buy>0 && buy>TargetLo) {X("OFF TargetLo", buy, bar, clrBlue);  buy=0; Modify=true;}   LINE("TargetLo", bar+1, TargetLo, bar, TargetLo,  clrGray,0); //      
   if (sel>0 && sel<TargetHi) {X("OFF TargetHi", sel, bar, clrRed);   sel=0; Modify=true;}   LINE("TargetHi", bar+1, TargetHi, bar, TargetHi,  clrGray,0); //    
   }   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
void FSTLEV_ZONE_CHECK(float& buy, float& sel){// ОГРАНИЧЕНИЕ ТОРГОВОГО ДИАПАЗОНА ВБЛИЗИ ПЕРВЫХ УРОВНЕЙ
   if (iFrstLev==0) return;
   float delta=MathAbs(iFrstLev)*ATR;
   if (iFrstLev>0){  // ВХОД В РАЙОНЕ ПЕРВЫХ УРОВНЕЙ 
      if (buy>F[LO].P+delta)   {X("BuyZoneOut", buy, bar, clrBlue); buy=0;}  // LINE("BuyUp", bar+1,F[LO].P+delta,bar,F[LO].P+delta,clrLightBlue,0);   
      if (sel<F[HI].P-delta)   {X("SelZoneOut", sel, bar, clrRed);  sel=0;}  // LINE("SelDn", bar+1,F[HI].P-delta,bar,F[HI].P-delta,clrPink,0);           
   }else{            // В РАЙОНЕ УРОВНЯ СЕРЕДИНКИ
      if (buy>F[LO].Mid+delta) {X("BuyZoneOut", buy, bar, clrBlue); buy=0;}    
      if (sel<F[HI].Mid-delta) {X("SelZoneOut", sel, bar, clrRed);  sel=0;} 
   }  }  
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
void PL_CHECK(){// ПРОВЕРКА СООТНОШЕНИЯ Profit/Loss
   if (minPL==0) return;
   float PL=(float)MathAbs(minPL)/2;   
   if (Buy.Inp>0){
      float Stop=Buy.Inp-Buy.Stp;
      float Profit=Buy.Prf-Buy.Inp;
      if (Stop>0 && Profit/Stop <PL){// при худшем соотношении P/L:
         if (minPL<0)   Buy.Inp=0;                                 // поза не открывается, либо   
         if (minPL>0)   {Buy.Inp=Buy.Stp+(Stop+Profit)/(1+PL);    if (Buy.Inp-Buy.Stp<MinStop) Buy.Inp=0;}// цена открытия перемещается для удовлетворения отношения PL
      }  }
   if (Sel.Inp>0){ 
      float Stop=Sel.Stp-Sel.Inp;   
      float Profit=Sel.Inp-Sel.Prf;
      if (Stop>0 && Profit/Stop<PL){// при худшем соотношении P/L:
         if (minPL<0)   Sel.Inp=0;                                // поза не открывается, либо 
         if (minPL>0)   {Sel.Inp=Sel.Stp-(Stop+Profit)/(1+PL);  if (Sel.Stp-Sel.Inp<MinStop) Sel.Inp=0;}// цена открытия перемещается для удовлетворения отношения PL
   }  }  } 
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ      
float DELTA(int delta){  // 0.4  0.9  1.6  2.5  3.6
   if (delta>0) return( (float)MathPow(delta+1,2)/10*ATR);    
   if (delta<0) return(-(float)MathPow(delta-1,2)/10*ATR); //  ATR = ATR*dAtr*0.1,     
   return (0);
   }    
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
float MAX(float price1, float price2){
   if (price1>price2) return (price1); else return (price2);
   } 
float MIN(float price1, float price2){// возвращает меньшее, но не нулевое значение
   if (price1==0) return (price2);
   if (price2==0) return (price1);
   if (price1<price2) return (price1); else return (price2);
   }  
     