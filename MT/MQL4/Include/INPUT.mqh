// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
void EXPERT::INPUT(){
   //if (LO==0 || HI==0)  return; // если первые уровни не определены все сигналы блокируются
   if (SEL.Val)   set.SEL.Sig=NONE; // открыт ордер (STOP, LIMIT или MARKET)
   if (BUY.Val)   set.BUY.Sig=NONE; // сбрасываем паттерн   
   set.BUY.Val=0; set.BUY.Stp=0; set.BUY.Prf=0; // сбрасываем     
   set.SEL.Val=0; set.SEL.Stp=0; set.SEL.Prf=0; // значения приказов
   UP=(BUY.Typ!=MARKET && Trnd.Global>=0 && Trnd.Local>=0); 
   DN=(SEL.Typ!=MARKET && Trnd.Global<=0 && Trnd.Local<=0);
   if (!UP && !DN) return;
   //SIG_LINES(UP==1," UP="+S0(UP)+" Buy="+S4(BUY.Val)+" BuyLim="+S4(BUYLIM), 
   //          DN==1," DN="+S0(DN)+" Sel="+S4(SEL.Val)+" SelLim="+S4(SELLIM),clrSIG1);
   ML_TRADE(); // ML-сигналы из файла (тестовое подключение)
//   switch(iSignal){// ГЛОБАЛЬНЫЕ СИГНАЛОЫ 
//      case 1:  SIG_FIRST_LEVELS();  break;   // ОТСКОК 
//      case 2:  SIG_FALSE_BREAK();   break;   // работает в lib_PIC
//      case 3:  ML_TRADE();          break;   // ML-сигналы из файла (тестовое подключение)
//      case 4:  SIG_TURTLE();        break;
//      default: SIG_NULL();          break;   // БЕЗ ГЛОБАЛОВ
//      }
   if (set.BUY.Sig!=GOGO) UP=0;
   if (set.SEL.Sig!=GOGO) DN=0;   
   //SIG_LINES(set.BUY.Sig==GOGO,"GOGO: UP="+S0(UP)+" Buy="+S4(BUY.Val)+" BuyLim="+S4(BUYLIM), 
   //          set.SEL.Sig==GOGO,"GOGO: DN="+S0(DN)+" Sel="+S4(SEL.Val)+" SelLim="+S4(SELLIM),clrSIG1);  // линии сиглалов MovUP и MovDN: (сигналы, смещение от H/L, цвет)      
   
   color clrBUY=clrSilver, clrSEL=clrSilver;
   if (set.BUY.Sig==GOGO) clrBUY=clrRed;
   if (set.SEL.Sig==GOGO) clrSEL=clrRed;
   //LINE("Up/Dn="+S0(UP)+"/"+S0(DN)+" FlsUpDn="+S0(FlsUp)+"/"+S0(FlsDn)+" FlsPhase="+S0(F[FlsUp].Fls.Phase)+"/"+S0(F[FlsDn].Fls.Phase)+" PtrnBuy/Sel="+S0(set.BUY.Sig)+"/"+S0(set.SEL.Sig), bar+1, Close[bar+1], bar, Close[bar],  clrSilver,0); 
   //LINE(" BUY.Sig="+SIG2TXT(set.BUY.Sig)+" UP="+S0(UP)+"/"+S0(Trnd.Global)+"/"+S0(Trnd.Local)+" "+ORDTYP(BUY.Typ)+"/"+S4(BUY.Val)+" set.BUY="+S4(set.BUY.Val)+" Mid="+S4(F[LO2].P)+" LO2="+S0(LO2), bar+1, Close[bar+1]+Atr.Lim, bar, Close[bar]+Atr.Lim,  clrBUY,0); //"FlsUp/Dn="+S0(FlsUp)+"/"+S0(FlsDn)+" PhaseUp/Dn"+S0(F[FlsUp].Fls.Phase)+"/"+S0(F[FlsDn].Fls.Phase)+
   //LINE(" SEL.Sig="+SIG2TXT(set.SEL.Sig)+" DN="+S0(DN)+"/"+S0(Trnd.Global)+"/"+S0(Trnd.Local)+" "+ORDTYP(SEL.Typ)+"/"+S4(SEL.Val)+" set.SEL="+S4(set.SEL.Val)+" Mid="+S4(F[HI2].P)+" HI2="+S0(HI2), bar+1, Close[bar+1]-Atr.Lim, bar, Close[bar]-Atr.Lim,  clrSEL,0); //"FlsUp/Dn="+S0(FlsUp)+"/"+S0(FlsDn)+" PhaseUp/Dn"+S0(F[FlsUp].Fls.Phase)+"/"+S0(F[FlsDn].Fls.Phase)+
   if (!UP && !DN) return; // UP,DN могут принимать значения 0..1
   if (set.SEL.Val>0 && (set.SEL.Stp<=set.SEL.Val || set.SEL.Prf<0 || set.SEL.Prf>=set.SEL.Val))                        {X("Wrong Sel/Stop/Profit: "+S4(set.SEL.Val)+"/"+S4(set.SEL.Stp)+"/"+S4(set.SEL.Prf),bar,High[bar],clrRed);    set.SEL.Val=0;}
   if (set.BUY.Val>0 && (set.BUY.Stp>=set.BUY.Val || set.BUY.Stp<=0 || (set.BUY.Prf!=0 && set.BUY.Prf<=set.BUY.Val)))   {X("Wrong Buy/Stop/Profit: "+S4(set.BUY.Val)+"/"+S4(set.BUY.Stp)+"/"+S4(set.BUY.Prf),bar,Low [bar],clrRed);    set.BUY.Val=0;}
   
   //SIG_LINES(UP,"2 set.BUY.Val="+S4(set.BUY.Val), 
   //          DN,"2 set.SEL.Val="+S4(set.SEL.Val),clrSIG2);     
   // УДАЛЕНИЕ СТАРЫХ ОРДЕРОВ    // ExpirBars=-x..23 <0~удаление отложника при пропадании сигнала. 0~при новом. >0~новый ордер не ставится, пока старый не удалится по экспирации  
   if (ExpirBars==0){// Удаление отложников при появлении нового сигнала
      if (set.BUY.Val>0 && (MathAbs(set.BUY.Val-BUY.Val)>ATR/2 || MathAbs(set.BUY.Stp-BUY.Stp)>ATR/2 || MathAbs(set.BUY.Prf-BUY.Prf)>ATR/2)){
         X("Replace "+ORDTYP(BUY.Typ)+" to "+S4(set.BUY.Val), BUY.Val, bar, clrBlack);    BUY.Val=0;}
      if (set.SEL.Val>0 && (MathAbs(set.SEL.Val-SEL.Val)>ATR/2 || MathAbs(set.SEL.Stp-SEL.Stp)>ATR/2 || MathAbs(set.SEL.Prf-SEL.Prf)>ATR/2)){
         X("Replace "+ORDTYP(SEL.Typ)+" to "+S4(set.SEL.Val), SEL.Val, bar, clrBlack);    SEL.Val=0;}
   }else {// новый сигнал игнорируется, пока старый отложник не удалится по экспирации
      if (BUY.Val)  set.BUY.Val=0;
      if (SEL.Val)  set.SEL.Val=0;
      }
   if (set.SEL.Val)   {set.SEL.Sig=DONE; SEL.Typ=SET;}   // ордер готов: сбрасываем паттерн, 
   if (set.BUY.Val)   {set.BUY.Sig=DONE; BUY.Typ=SET;}   // меняем тип  
   //SIG_LINES(set.BUY.Val ,"3 set.BUY.Val="+S4(set.BUY.Val)+" BUYLIM="+S4(BUYLIM), 
   //          set.SEL.Val,"3 set.SEL.Val="+S4(set.SEL.Val)+" SELLIM="+S4(SELLIM),clrSIG3); // линии сиглалов UP и DN: (сигналы, цвет)
   if (Real) ERROR_CHECK(__FUNCTION__);
   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
void EXPERT::OPEN_BUY(uchar pic)  {OPEN_BUY(F[pic].P, F[pic].Back);}
void EXPERT::OPEN_BUY(float input_price, float target_price){
   if (input_price*target_price==0) {X("BUY_price=0",bar,Low[bar],clrBlack); return;}
   float Stop=ATR*D/2; // 0.5 1 1.5 2 2.5
   set.BUY.Stp=input_price-Atr.Lim*Stp;
   set.BUY.Val=set.BUY.Stp+Stop;// V("BUY="+S4(set.BUY.Stp+Stop)+"/"+S4(Stop),bar,Low[bar],clrBlack); // если точка входа выше текущей цены, входим по текущей, но не стоп ордером
   if (Prf>0)  set.BUY.Prf=input_price+(target_price-input_price)*Prf/4; // 1/4 1/2 3/4 1 5/4 движения
   else        set.BUY.Prf=set.BUY.Val+DELTA(2-Prf); // 0.9  1.6  2.5  3.6  4.9  6.4   
   if (D<=0)   set.BUY.Val=set.BUY.Stp+(set.BUY.Prf-set.BUY.Stp)*2/(3-D);   // вход переносится в соответствии с риском   2/3  1/2  2/5  1/3  2/7  1/4  2/9  1/5     (1/2  1/3  1/4  1/5  1/6  1/7 )
   if (ASK<set.BUY.Val) set.BUY.Val=ASK;
   }  
void EXPERT::OPEN_SELL(uchar pic) {OPEN_SELL(F[pic].P, F[pic].Back); }     // V("pic="+S0(pic)+" P="+S4(F[pic].P)+" Back="+S4(F[pic].Back),H,bar,clrRed);
void EXPERT::OPEN_SELL(float input_price, float target_price){
   if (input_price*target_price==0) {X("SELL_price=0",bar,High[bar],clrBlack); return;}
   float Stop=ATR*D/2; // 0.5 1 1.5 2 2.5
   set.SEL.Stp=input_price+Atr.Lim*Stp;
   set.SEL.Val=set.SEL.Stp-Stop; // если точка входа ниже текущей цены, входим по текущей, но не стоп ордером
   if (Prf>0)  set.SEL.Prf=input_price-(input_price-target_price)*Prf/4; 
   else        set.SEL.Prf=set.SEL.Val-DELTA(2-Prf); // 0.9  1.6  2.5  3.6  4.9  6.4   
   if (D<=0)   set.SEL.Val=set.SEL.Stp-(set.SEL.Stp-set.SEL.Prf)*2/(3-D);  // вход переносится в соответствии с риском 
   if (BID>set.SEL.Val) set.SEL.Val=BID;
   }       
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ      
float EXPERT::DELTA(int delta){  // 0.4  0.9  1.6  2.5  3.6  4.9  6.4
   if (delta>0) return( (float)MathPow(delta+1,2)/10*ATR);    
   if (delta<0) return(-(float)MathPow(delta-1,2)/10*ATR); //  ATR = ATR*dAtr*0.1,     
   return (0);
   }    
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
string SIG2TXT(char sig){
   switch(sig){
      case -1: return("BLOCK");  // блокировка 
      case  0: return("NONE");
      case  1: return("WAIT");   // ожидание
      case  2: return("START");  // начало
      case  3: return("CONFIRM");// подтверждение
      case  4: return("GOGO");   // сигнал на открытие позы
      case  5: return("BREAK");  // отмена
      case  6: return("DONE");   // поза открыта 
      default: return(DoubleToStr(sig));
   }  }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
/*   

 
      

void EXPERT::OPEN_BUY(float input_price, float target_price){
   if (input_price==0) {X("BUY_price=0",bar,Low[bar],clrBlack); return;}
   set.BUY.Val=input_price+DELTA(D); // V("BUY="+S4(set.BUY.Stp+Stop)+"/"+S4(Stop),bar,Low[bar],clrBlack); 
   set.BUY.Stp=set.BUY.Val-DELTA(Stp);
   set.BUY.Prf=target_price; 
   }  
void EXPERT::OPEN_SELL(float input_price, float target_price){
   if (input_price==0) {X("SELL_price=0",bar,High[bar],clrBlack); return;}
   set.SEL.Val=input_price-DELTA(D); // 
   set.SEL.Stp=set.SEL.Val+DELTA(Stp);
   set.SEL.Prf=target_price; 
   } 

void SELL_PRICE (float price){// шорт от уровня
   if (price==0) return;
   float Delta=ATR/2;
   if (D>0){// вход от пиков в заданном диапазоне
      float StpPwr=0, UpBorder=price+Delta*D, DnBorder=price-Delta; // поиск пика в диапазоне -0.5ATR/+0.5...2.5ATR
      uchar s=0;
      for (uchar f=1; f<LevelsAmount; f++){  // 
         if (F[f].Dir<0 || F[f].Brk>TOUCH || F[f].P==0 || F[f].P<DnBorder || F[f].P>UpBorder) continue; // самый сильный непробитый пик в заданном диапазоне
         if (F[f].Power>StpPwr){ // *F[f].Pics
            s=f;
            StpPwr=F[f].Power; // *F[f].Pics
         }  }
      if (s>0){ 
         set.SEL.Stp=F[s].P+Atr.Lim;
         set.SEL.Val=MAX(F[s].P-Delta*Stp, Open[0]+Atr.Lim); // если точка входа ниже текущей цены, входим по текущей, но не стоп ордером
         V("StopPic Power="+S4(F[s].Power)+" Pics="+S0(F[s].Pics), F[s].P, SHIFT(F[s].T), clrRed);
      }else set.SEL.Val=0; // если пик НЕ был найден
   }else{ // вход от заданной цены +/- Delta
      set.SEL.Val=price+Delta*(3+D); // price+3Delta...price-2Delta  
      set.SEL.Stp=set.SEL.Val+Delta*Stp;
      }
   //V("S="+S0(s)+"("+S4(StpPwr)+")", set.SEL.Stp, bar, clrRed);
   //PRN("HI="+S4(F[HI].P)+" "+DTIME(F[HI].T)+" Back="+S4(F[HI].Back));
   }  
void BUY_PRICE (float price){// лонг от уровня
   if (price==0) return;
   float Delta=ATR/2;
   if (D>0){// вход от пиков в заданном диапазоне
      float StpPwr=0, UpBorder=price+Delta, DnBorder=price-Delta*D; // поиск пика в диапазоне 0.5ATR/-0.5...-2.5ATR
      uchar s=0;
      for (uchar f=1; f<LevelsAmount; f++){  // 
         if (F[f].Dir>0 || F[f].Brk>TOUCH || F[f].P==0 || F[f].P<DnBorder || F[f].P>UpBorder) continue; // самый сильный непробитый пик в заданном диапазоне
         if (F[f].Power>StpPwr){// *F[f].Pics
            s=f;
            StpPwr=F[f].Power; // *F[f].Pics
         }  }
      if (s>0){ 
         set.BUY.Stp=F[s].P-Atr.Lim;
         set.BUY.Val=MIN(F[s].P+Delta*Stp, Open[0]-Atr.Lim); // если точка входа выше текущей цены, входим по текущей, но не стоп ордером
         A("StopPic Power="+S4(F[s].Power)+" Pics="+S0(F[s].Pics), F[s].P, SHIFT(F[s].T), clrBlue);
      }else set.BUY.Val=0; // если пик НЕ был найден
   }else{
      set.BUY.Val=price-Delta*(3+D); // price-3Delta...price+2Delta 
      set.BUY.Stp=set.BUY.Val-Delta*Stp;
      }
   
   }    
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ       
void BUY_PROFIT(){
   if (set.BUY.Val==0) return;   // PROFIT FOR LONG //////////////////////////////////////////////////
   switch(Prf){
      case  1: set.BUY.Prf=set.BUY.Val+(F[LO].Back-set.BUY.Val)*1/4; break;
      case  2: set.BUY.Prf=set.BUY.Val+(F[LO].Back-set.BUY.Val)*1/3; break; 
      case  3: set.BUY.Prf=set.BUY.Val+(F[LO].Back-set.BUY.Val)*1/2; break; 
      case  4: set.BUY.Prf=set.BUY.Val+(F[LO].Back-set.BUY.Val)*2/3; break;
      case  5: set.BUY.Prf=set.BUY.Val+(F[LO].Back-set.BUY.Val)*3/4; break;
      case  6: set.BUY.Prf=F[LO].Back-ATR; break;
      case  7: set.BUY.Prf=F[HI].P   -ATR; break;
      default: set.BUY.Prf=set.BUY.Val+20*ATR;
      }        
   if (Prf<0)  set.BUY.Prf=set.BUY.Val+DELTA(1-Prf); // 0.9  1.6  2.5  3.6  4.9
   //if (Target!=0 && TrgHi>0 && F[TrgHi].P<set.BUY.Prf) set.BUY.Prf=F[TrgHi].P; // если целевой уровень ближе установленного тейка, просто приближаем тейк на целевой уровень     
   if (minPL!=0){   
      float Stop  =set.BUY.Val-set.BUY.Stp;
      float Profit=set.BUY.Prf-set.BUY.Val;
      if (Stop>0 && Profit/Stop <PL){// при худшем соотношении P/L:
         X("P/L="+S4(Profit/Stop)+" CHANGE set.BUY.Val", set.BUY.Val, bar, clrRed);
         if (minPL<0)   set.BUY.Val=0;                                // поза не открывается, либо   
         if (minPL>0)   set.BUY.Val=set.BUY.Stp+(Stop+Profit)/(1+PL);  // переносится вход     
   }  }  }  
void SELL_PROFIT(){   
   if (set.SEL.Val==0) return;// PROFIT FOR SHORT ///////////////////////////////////////////////////
   switch(Prf){  
      case  1: set.SEL.Prf=set.SEL.Val-(set.SEL.Val-F[HI].Back)*1/4; break;   
      case  2: set.SEL.Prf=set.SEL.Val-(set.SEL.Val-F[HI].Back)*1/3; break;
      case  3: set.SEL.Prf=set.SEL.Val-(set.SEL.Val-F[HI].Back)*1/2; break;
      case  4: set.SEL.Prf=set.SEL.Val-(set.SEL.Val-F[HI].Back)*2/3; break;
      case  5: set.SEL.Prf=set.SEL.Val-(set.SEL.Val-F[HI].Back)*3/4; break;
      case  6: set.SEL.Prf=F[HI].Back+ATR; break;
      case  7: set.SEL.Prf=F[LO].P   +ATR; break; 
      default: set.SEL.Prf=set.SEL.Val-20*ATR; 
      }
   if (Prf<0)  set.SEL.Prf=set.SEL.Val-DELTA(1-Prf); // 0.9  1.6  2.5  3.6  4.9  6.4    
   //if (Target!=0 && TrgLo>0 && F[TrgLo].P>set.SEL.Prf) set.SEL.Prf=F[TrgLo].P; // если целевой уровень ближе установленного тейка, просто приближаем тейк на целевой уровень
   if (minPL!=0){
      float Stop=set.SEL.Stp-set.SEL.Val;   
      float Profit=set.SEL.Val-set.SEL.Prf;
      if (Stop>0 && Profit/Stop<PL){// при худшем соотношении P/L:
         X("P/L="+S4(Profit/Stop)+" CHANGE set.SEL.Val", set.BUY.Val, bar, clrRed);
         if (minPL<0)   set.SEL.Val=0;                                // поза не открывается, либо 
         if (minPL>0)   set.SEL.Val=set.SEL.Stp-(Stop+Profit)/(1+PL);  // цена открытия перемещается для удовлетворения отношения PL
   }  }  }  
*/   
               
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
//void SELL_STOP (float SetStop) {// УСТАНОВКА СТОПА дальше, чем предыдущий вариант с проверками        
//   if (set.SEL.Val==0 || SetStop==0) return;
//   set.SEL.Stp=SetStop+DELTA(Stp); //   0.4  0.9  1.6  2.5  3.6  4.9  6.4
//   if (sMin!=0 && set.SEL.Stp-set.SEL.Val<MinStop){// стоп слишком близко
//      if (sMin<0)  set.SEL.Stp=set.SEL.Val+MinStop; else set.SEL.Val=set.SEL.Stp-MinStop;}// отодвигаем стоп, либо вход от стопа
//   if (sMax!=0 && set.SEL.Stp-set.SEL.Val>MaxStop){// стоп слишком далеко
//      if (sMax<0)  set.SEL.Val=0; else set.SEL.Val=set.SEL.Stp-MaxStop;  // не ставим, либо пододвигаем вход к стопу  V("stop "+S0(OrdSet),set.SEL.Stp,0,clrRed);
//   }  }   
//void BUY_STOP (float SetStop) {// УСТАНОВКА СТОПА дальше, чем предыдущий вариант с проверками 
//   if (set.BUY.Val==0 || SetStop==0) return;
//   set.BUY.Stp=SetStop-DELTA(Stp);
//   if (sMin!=0 && set.BUY.Val -set.BUY.Stp<MinStop){// стоп слишком близко
//      if (sMin<0)  set.BUY.Stp=set.BUY.Val -MinStop; else set.BUY.Val=set.BUY.Stp+MinStop;}// отодвигаем стоп, либо вход от стопа
//   if (sMax!=0 && set.BUY.Val -set.BUY.Stp>MaxStop){// стоп слишком далеко 
//      if (sMax<0)  set.BUY.Val=0; else set.BUY.Val=set.BUY.Stp+MaxStop;  // не ставим, либо пододвигаем вход к стопу   A("stop "+S0(OrdSet),set.BUY.Stp,0,clrBlue);
//   }  }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   

      
      
      
      
     