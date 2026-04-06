float MM(float Stop, uchar e){// ММ ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
   float risk=EXP[e].Rsk*Aggress; //Print("risk=",risk," Rsk=",EXP[e].Rsk," Aggress=",Aggress," MaxRisk=",MaxRisk);
   if (risk==0) {Lot=0;   return(Lot);} 
   float    MinLot =float(MarketInfo(EXP[e].Sym,MODE_MINLOT)), // CurDD - глобальная, т.к. передается в ф. TradeHistoryWrite() 
            MaxLot =float(MarketInfo(EXP[e].Sym,MODE_MAXLOT));        
   if (risk>MaxRisk) risk=float(MaxRisk*0.95/Aggress);// проверка на ошибочное значение риска
   CurDD=CUR_DD(e); // последняя незакрытая просадка эксперта (не максимальной) 
   if (Stop<=0)                                  {REPORT(e,"MM: Stop<=0!");    return (0);}
   if (MarketInfo(EXP[e].Sym,MODE_POINT)<=0)     {REPORT(e,"MM: POINT<=0!");   return (0);}
   if (MarketInfo(EXP[e].Sym,MODE_TICKVALUE)<=0) {REPORT(e,"MM: TICKVAL<0!");  return (0);}
   if (Real && CurDD>EXP[e].HistDD)              {REPORT(e,"MM: CurDD>HistDD!: "+S0(CurDD)+">"+S0(EXP[e].HistDD)); return (0);}
   // см.Расчет залога http://www.alpari.ru/ru/help/forex/?tab=1&slider=margins#margin1
   // Margin = Contract*Lot/Leverage = 100000*Lot/100  
   // MaxLotForMargin=NormalizeDouble(AccountFreeMargin()/MarketInfo(SYM,MODE_MARGINREQUIRED),LotDigits) // Макс. кол-во лотов для текущей маржи
   Lot = float(NormalizeDouble(DEPO(MM_Mode,e)*risk*Aggress*0.01 / (Stop/MarketInfo(EXP[e].Sym,MODE_POINT)*MarketInfo(EXP[e].Sym,MODE_TICKVALUE)), LotDigits)); // размер стопа через Стоимость пункта. См. калькулятор трейдера http://www.alpari.ru/ru/calculator/
   //Print("Count Lot=",Lot," risk=",risk," DEPO=",DEPO(MM_Mode,e)," Stop=",Stop," Point=",MarketInfo(EXP[e].Sym,MODE_POINT)," tick=",MarketInfo(EXP[e].Sym,MODE_TICKVALUE));
   //Print("count=",DEPO(MM_Mode,e)*risk*Aggress*0.01 / (Stop/MarketInfo(EXP[e].Sym,MODE_POINT)*MarketInfo(EXP[e].Sym,MODE_TICKVALUE)));
   if (Lot<MinLot){  // Проверка на соответствие условиям ДЦ
      REPORT(e,"MM: counted Lot="+S3(Lot)+"! Lot<"+S3(MinLot)+" DEPO="+S0(DEPO(MM_Mode,e))+" Stop="+S4(Stop,EXP[e].Sym)+" Point="+S4(MarketInfo(EXP[e].Sym,MODE_POINT),EXP[e].Sym)+" Tick="+S4(MarketInfo(EXP[e].Sym,MODE_TICKVALUE),EXP[e].Sym)); 
      Lot=MinLot;} 
   if (Lot>MaxLot){
      REPORT(e,"MM: counted Lot="+S3(Lot)+"! Lot>"+S3(MaxLot)+" DEPO="+S0(DEPO(MM_Mode,e))+" Stop="+S4(Stop,EXP[e].Sym)+" Point="+S4(MarketInfo(EXP[e].Sym,MODE_POINT),EXP[e].Sym)+" Tick="+S4(MarketInfo(EXP[e].Sym,MODE_TICKVALUE),EXP[e].Sym)); 
      Lot=MaxLot;} 
   if (CHECK_RISK(Lot,Stop,EXP[e].Sym)>MaxRisk){
      REPORT(e,"MM: RiskChecker="+S1(CHECK_RISK(Lot,Stop,EXP[e].Sym))+"% - Trade Disable!"); 
      return (0);// Не позволяем превышать риск MaxRisk%! 
      }
   Print("MM[",EXP[e].Mgc,"]: RiskChecker(",Lot,")="+S2(CHECK_RISK(Lot,Stop,EXP[e].Sym))+"%");
   return (Lot);
   }
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
float CHECK_RISK(double lot, double Stop, string SYM){// Проверим, какому риску будет соответствовать расчитанный Лот:  
   if (MarketInfo(SYM,MODE_TICKVALUE)<=0) {REPORT("RiskChecker(): "+SYM+" TickValue<0"); return (100);}
   if (MarketInfo(SYM,MODE_POINT)<=0)     {REPORT("RiskChecker(): POINT<=0!"); return (-1);}
   return (float(NormalizeDouble(lot * (Stop/MarketInfo(SYM,MODE_POINT)*MarketInfo(SYM,MODE_TICKVALUE)) / AccountBalance()*100,2)));
   }
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
float CUR_DD(uchar    e){// расчет последней незакрытой просадки эксперта (не максимальной) 
   float MaxExpertProfit=EXP[e].LastTestDD, ExpertProfit=0, profit=0;
   for(int Ord=0; Ord<OrdersHistoryTotal(); Ord++){// находим среди всей истории сделок эксперта ПОСЛЕДНЮЮ просадку и измеряем ее от макушки баланса до текущего значения (Не до минимального!)
      if (OrderSelect(Ord,SELECT_BY_POS,MODE_HISTORY)==true && OrderMagicNumber()==EXP[e].Mgc && OrderCloseTime()>EXP[e].TestEndTime){
         profit=float((OrderProfit()+OrderSwap()+OrderCommission())/OrderLots()/MarketInfo(EXP[e].Sym,MODE_TICKVALUE)*0.1); // прибыль от выбранного ордера в пунктах
         if (profit!=0){ 
            ExpertProfit+=profit; // текущая прибыль эксперта
            if (ExpertProfit>MaxExpertProfit) MaxExpertProfit=ExpertProfit; // Print(" CurDD(): magic=",Magic," profit=",profit," MaxExpertProfit=",MaxExpertProfit," ExpertProfit=",ExpertProfit," OrderCloseTime()=",TimeToStr(OrderCloseTime(),TIME_SECONDS));// максимальная прибыль эксперта                  
      }  }  } 
   return float(MaxExpertProfit-ExpertProfit); // значение последней незакрытой просадки эксперта (не максимальной)
   }
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
float DEPO(char TypeMM, uchar    e){ // Расчет части депозита, от которой берется процент для совершения сделки  
   double Depo, ExpMaxBalance=AccountBalance(); // индивидуальная переменная, должна храниться в файле с временными параметрами
   switch (TypeMM){
      case 1: // Классический Антимартингейл
         Depo=AccountBalance();         
      break; 
      case 2: // уменьшение риска эксперта пропорционально глубине его текущей просадки
          if (EXP[e].HistDD>0) Depo=AccountBalance()*(EXP[e].HistDD-CurDD)/EXP[e].HistDD;  
          else                      Depo=AccountBalance();
      break; 
      case 3: // Индивидуальный баланс. Фиксируется начало индивидуальной просадки и риск начинает увеличиваться до выхода из нее за счет прироста баланса от прибыльных систем. 
         // Но не превышает установленного риска для данной системы, если баланс продолжает снижаться.  
         if (CUR_DD(e)==0 && AccountBalance()>ExpMaxBalance) ExpMaxBalance=AccountBalance(); // Лот увеличивается только если система в плюсе и общий баланс растет. Т.е. если другие системы не сливают. 
         Depo=MathMin(ExpMaxBalance,AccountBalance()); // Не превышаем установленного риска
      break; 
      case 4: // Процент от общего максимально достигнутого баланса.
         // При просадке экспертов лот не понижается (риск растет вплоть до 10%). 
         // Выход из просадки осуществляется с большей скоростью за счет растущего баланса от друхих систем. 
         // При этом оказывается значителььное влияние убыточных систем на общий баланс. 
         Depo=GlobalVariableGet("MaxBalance");
         if (AccountBalance()>Depo) Depo=AccountBalance();
         GlobalVariableSet("MaxBalance",Depo);
      break;
      default: Depo=AccountBalance(); // Классический Антимартингейл
      }
   return (float(Depo));
   }
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
