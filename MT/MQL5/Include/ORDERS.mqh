


  
void EXPERT_PARENT_CLASS::ORDERS_SET(){
   if (Real){
      ORDERS_COLLECT();
      return;}
   if (Risk==0)   Lot=float(0.1);
   else           Lot=MM(MathMax(set.BUY.Val-set.BUY.Stp, set.SEL.Stp-set.SEL.Val), CurExp);     
   SET_BUY();
   SET_SEL();
   }  
void EXPERT_PARENT_CLASS::SET_BUY(){
   if (set.BUY.Val<=0) return;
   int ticket;   double TradeRisk=0;  string str;
   char repeat=3; // три попытки у тебя  
   if (MathAbs(set.BUY.Val-ASK)<=StopLevel) set.BUY.Val=ASK;  
   if (set.BUY.Val-set.BUY.Stp <= StopLevel)                   {X("Stop="  +S5(set.BUY.Stp,Sym)+" too close to set.BUY="+S5(set.BUY.Val,Sym), set.BUY.Val, bar, clrRed); repeat=0;}  // слишком близкий/неправильный стоп
   if (set.BUY.Prf-set.BUY.Val <= StopLevel && set.BUY.Prf>0)  {X("Profit="+S5(set.BUY.Prf,Sym)+" too close to set.BUY="+S5(set.BUY.Val,Sym), set.BUY.Val, bar, clrRed); repeat=0;}  // слишком близкий/неправильный тейк
   WAITING(Mgc,"Terminal",20); // ждем 20сек освобождения терминала
   while (repeat>0 && CanPlaceBuyOrder()){ 
      if (Real){Print("SET_BUY(): ",Sym," set.BUY.Val=",S5(set.BUY.Val,Sym),"/",S5(set.BUY.Stp,Sym),"/",S5(set.BUY.Prf,Sym)," Lot=",Lot," Mgc=",Mgc," set.BUY.Exp=",set.BUY.Exp," ASK/BID/StopLevel=",S5(ASK,Sym),"/",S5(BID,Sym),"/",S5(StopLevel,Sym));
         MARKET_UPDATE(Sym);
         TradeRisk=CHECK_RISK(Lot, set.BUY.Val-set.BUY.Stp, Sym); 
         if (TradeRisk>MaxRisk) {REPORT(ExpNum,"CHECK_RISK="+S2(TradeRisk)+"% too BIG!!! Lot="+S2(Lot)+" Balance="+S0(AccountBalance())+" Stop="+S4(set.BUY.Val-set.BUY.Stp)+" Sym="+Sym); break;}
         }
      if (set.BUY.Val-ASK>StopLevel)  {str="Set BuyStp ";   ticket=OrderSend(Sym,OP_BUYSTOP, NormalizeDouble(Lot,LotDigits), N5(set.BUY.Val,Sym), 3, N5(set.BUY.Stp,Sym), N5(set.BUY.Prf,Sym), S0(Mgc)+"-"+Name+S3(Ver), Mgc,set.BUY.Exp, clrGreen);}   else
      if (ASK-set.BUY.Val>StopLevel)  {str="Set BuyLim ";   ticket=OrderSend(Sym,OP_BUYLIMIT,NormalizeDouble(Lot,LotDigits), N5(set.BUY.Val,Sym), 3, N5(set.BUY.Stp,Sym), N5(set.BUY.Prf,Sym), S0(Mgc)+"-"+Name+S3(Ver), Mgc,set.BUY.Exp, clrGreen);}   else
                   {set.BUY.Val=ASK;   str="Set BUY ";      ticket=OrderSend(Sym,OP_BUY,     NormalizeDouble(Lot,LotDigits), N5(set.BUY.Val,Sym), 3, N5(set.BUY.Stp,Sym), N5(set.BUY.Prf,Sym), S0(Mgc)+"-"+Name+S3(Ver), Mgc,    0      , clrGreen);}
      REPORT(ExpNum,str+S4(set.BUY.Val,Sym)+"/"+S4(set.BUY.Stp,Sym)+"/"+S4(set.BUY.Prf,Sym)+"/"+S2(Lot)+"x"+S1(TradeRisk)+"%");
      ORDER_CHECK();
      if (ticket>0) break; // Ордеру назначен номер тикета. В случае неудачи ticket=-1   
      if (ERROR_CHECK("SET_BUY",ExpNum)) repeat--; else repeat=0; // ERROR_CHECK() возвращает необходимость повтора торговой операции
      }
   FREE(Mgc,"Terminal");   
   }  
void EXPERT_PARENT_CLASS::SET_SEL(){   
   if (set.SEL.Val<=0) return; 
   int ticket;   double TradeRisk=0;  string str;
   char repeat=3; // три попытки у тебя  
   if (MathAbs(BID-set.SEL.Val)<=StopLevel) set.SEL.Val=BID;
   if (set.SEL.Stp-set.SEL.Val <= StopLevel) {X("Stop="  +S5(set.SEL.Stp,Sym)+" too close to set.SEL="+S5(set.SEL.Val,Sym), set.SEL.Val, bar, clrRed); repeat=0;}  // слишком близкий/неправильный стоп
   if (set.SEL.Val-set.SEL.Prf <= StopLevel) {X("Profit="+S5(set.SEL.Prf,Sym)+" too close to set.SEL="+S5(set.SEL.Val,Sym), set.SEL.Val, bar, clrRed); repeat=0;}  // слишком близкий/неправильный тейк
   WAITING(Mgc,"Terminal",20); // ждем 20сек освобождения терминала
   while (repeat>0 && CanPlaceSellOrder()){
      if (Real){ Print("SET_SEL(): ",Sym," set.SEL.Val=",S5(set.SEL.Val,Sym),"/",S5(set.SEL.Stp,Sym),"/",S5(set.SEL.Prf,Sym)," Lot=",Lot," Mgc=",Mgc," set.BUY.Exp=",set.SEL.Exp," ASK/BID/StopLevel=",S5(ASK,Sym),"/",S5(BID,Sym),"/",S5(StopLevel,Sym));
         MARKET_UPDATE(Sym);
         TradeRisk=CHECK_RISK(Lot, set.SEL.Stp-set.SEL.Val, Sym);
         if (TradeRisk>MaxRisk) {REPORT(ExpNum,"CHECK_RISK="+S2(TradeRisk)+"% too BIG!!! Lot="+S2(Lot)+" Balance="+S0(AccountBalance())+" Stop="+S4(set.SEL.Stp-set.SEL.Val)+" Sym="+Sym); break;}
         }
      if (BID-set.SEL.Val>StopLevel) {str="Set SellStp ";   ticket=OrderSend(Sym,OP_SELLSTOP, NormalizeDouble(Lot,LotDigits), N5(set.SEL.Val,Sym), 3, N5(set.SEL.Stp,Sym), N5(set.SEL.Prf,Sym), S0(Mgc)+"-"+Name+S3(Ver), Mgc,set.SEL.Exp, clrGreen);}   else
      if (set.SEL.Val-BID>StopLevel) {str="Set SellLim ";   ticket=OrderSend(Sym,OP_SELLLIMIT,NormalizeDouble(Lot,LotDigits), N5(set.SEL.Val,Sym), 3, N5(set.SEL.Stp,Sym), N5(set.SEL.Prf,Sym), S0(Mgc)+"-"+Name+S3(Ver), Mgc,set.SEL.Exp, clrGreen);}   else
                   {set.SEL.Val=BID;  str="Set Sell ";      ticket=OrderSend(Sym,OP_SELL,     NormalizeDouble(Lot,LotDigits), N5(set.SEL.Val,Sym), 3, N5(set.SEL.Stp,Sym), N5(set.SEL.Prf,Sym), S0(Mgc)+"-"+Name+S3(Ver), Mgc,      0    , clrGreen);}
      REPORT(ExpNum,str+S4(set.SEL.Val,Sym)+"/"+S4(set.SEL.Stp,Sym)+"/"+S4(set.SEL.Prf,Sym)+"/"+S2(Lot)+"x"+S1(TradeRisk)+"%");
      ORDER_CHECK();
      if (ticket>0) break;  // Ордеру назначен номер тикета. В случае неудачи ticket=-1   
      if (ERROR_CHECK("SET_SEL",ExpNum)) repeat--; else repeat=0; // ERROR_CHECK() возвращает необходимость повтора торговой операции
      }
   FREE(Mgc,"Terminal");  
   }  
   
     
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
void EXPERT_PARENT_CLASS::MODIFY(){   // Закрытие/модификация ордеров по Pos[] (массив) и legacy BUY/SEL singleton
   bool ReSelect=true;
   WAITING(Mgc,"Terminal",20);
   while (ReSelect){
      ReSelect=false; int Orders=OrdersTotal();
      for(int Ord=0; Ord<Orders; Ord++){
         if (OrderSelect(Ord, SELECT_BY_POS, MODE_TRADES)!=true || OrderMagicNumber()!=Mgc) continue;
         int Order=OrderType();
         bool make=true;
         uchar repeat=3;
         // Найти entry в Pos[] по тикету (если нет — multi-pos не имеет инструкции для этого ордера).
         // При MT5_MaxPositions==1 Pos[] НЕ используется: все close/modify-пути
         // legacy-режима (CLOSE_BUY/CLOSE_SEL, TRAILING_STOP, ML-выход) пишут в
         // BUY/SEL singleton, а ORDER_CHECK() каждый бар перезаполняет Pos[].data
         // ценой открытия — чтение Pos[] здесь тихо отбрасывало бы эти запросы.
         int posIdx = (MT5_MaxPositions == 1 ? -1 : FindPosIndexByTicket(OrderTicket()));
         // Флаг «закрыть этот ордер»: в multi-pos — Pos[i].data.Val==0; в legacy — BUY.Val==0/SEL.Val==0
         bool shouldClose = false;
         if (posIdx >= 0) {
            shouldClose = (Pos[posIdx].data.Val == 0);
         } else {
            // backcompat path (MT5_MaxPositions==1, или Pos[] ещё не синхронизирован)
            if (Order==OP_BUY  || Order==OP_BUYSTOP  || Order==OP_BUYLIMIT)  shouldClose = (BUY.Val==0);
            if (Order==OP_SELL || Order==OP_SELLSTOP || Order==OP_SELLLIMIT) shouldClose = (SEL.Val==0);
         }
         // Источник SL/TP для модификации: из Pos[] (если есть); иначе legacy singleton
         float srcStp = (posIdx>=0 ? Pos[posIdx].data.Stp : (Order==OP_BUY||Order==OP_BUYSTOP||Order==OP_BUYLIMIT ? BUY.Stp : SEL.Stp));
         float srcPrf = (posIdx>=0 ? Pos[posIdx].data.Prf : (Order==OP_BUY||Order==OP_BUYSTOP||Order==OP_BUYLIMIT ? BUY.Prf : SEL.Prf));
         while (repeat){
            MARKET_UPDATE(OrderSymbol());
            switch(Order){
               case OP_SELL:           //  C L O S E     S E L L
                  if (shouldClose){
                     make=OrderClose(OrderTicket(),OrderLots(),ASK,3,clrRed);
                     REPORT(ExpNum,"Close SELL/"+S4(OrderOpenPrice(),OrderSymbol()));
                     break;
                     }                 //  M O D I F Y     S E L L
                  if (MathAbs(srcStp-OrderStopLoss())>MarketInfo(OrderSymbol(),MODE_POINT) && srcStp-ASK>StopLevel){
                     make=OrderModify(OrderTicket(), OrderOpenPrice(), srcStp, OrderTakeProfit(),OrderExpiration(),clrBlue);  REPORT(ExpNum,"ModifySellStop/"+S4(srcStp,OrderSymbol()));}
                  if (MathAbs(srcPrf-OrderTakeProfit())>MarketInfo(OrderSymbol(),MODE_POINT) && ASK-srcPrf>StopLevel){
                     make=OrderModify(OrderTicket(), OrderOpenPrice(), OrderStopLoss(), srcPrf,OrderExpiration(),clrBlue);    REPORT(ExpNum,"ModifySellProfit/"+S4(srcPrf,OrderSymbol()));}
                  break;
               case OP_SELLSTOP:       //  D E L   S E L L S T O P
                  if (shouldClose){
                     if (BID-OrderOpenPrice()>StopLevel){   make=OrderDelete(OrderTicket(),clrRed);   REPORT(ExpNum,"Del SellStop/"+S4(OrderOpenPrice(),OrderSymbol()));}
                     else                                                                             REPORT(ExpNum,"Can't Del SELLSTOP near market! BID="+S5(BID,OrderSymbol())+" OpenPrice="+S5(OrderOpenPrice(),OrderSymbol())+" StopLevel="+S5(StopLevel,OrderSymbol()));}
                  break;
               case OP_SELLLIMIT:      //  D E L   S E L L L I M I T
                  if (shouldClose){
                     if (OrderOpenPrice()-BID>StopLevel){   make=OrderDelete(OrderTicket(),clrRed);   REPORT(ExpNum,"Del SellLimit/"+S4(OrderOpenPrice(),OrderSymbol()));}
                     else                                                                             REPORT(ExpNum,"Can't Del SELLLIMIT! near market, BID="+S5(BID,OrderSymbol())+" OpenPrice="+S5(OrderOpenPrice(),OrderSymbol())+" StopLevel="+S5(StopLevel,OrderSymbol()));}
                  break;
               case OP_BUY:            //  C L O S E    B U Y
                  if (shouldClose){
                     make=OrderClose(OrderTicket(),OrderLots(),BID,3,clrRed);
                     REPORT(ExpNum,"Close BUY/"+S4(OrderOpenPrice(),OrderSymbol()));
                     break;
                     }                 // M O D I F Y      B U Y
                  if (MathAbs(srcStp-OrderStopLoss())>MarketInfo(OrderSymbol(),MODE_POINT) && BID-srcStp>StopLevel){
                     make=OrderModify(OrderTicket(), OrderOpenPrice(), srcStp, OrderTakeProfit(),OrderExpiration(),clrBlue); REPORT(ExpNum,"ModifyBuyStop/"+S4(srcStp,OrderSymbol()));}
                  if (MathAbs(srcPrf-OrderTakeProfit())>MarketInfo(OrderSymbol(),MODE_POINT) && srcPrf-BID>StopLevel){
                     make=OrderModify(OrderTicket(), OrderOpenPrice(), OrderStopLoss(), srcPrf,OrderExpiration(),clrBlue);   REPORT(ExpNum,"ModifyBuyProfit/"+S4(srcPrf,OrderSymbol()));}
                  break;
               case OP_BUYSTOP:        //  D E L   B U Y S T O P
                  if (shouldClose){
                     if (OrderOpenPrice()-ASK>StopLevel){   make=OrderDelete(OrderTicket(),clrRed);   REPORT(ExpNum,"Del BuyStop/"+S4(OrderOpenPrice(),OrderSymbol()));}
                     else                                                                             REPORT(ExpNum,"Can't Del BUYSTOP near market! ASK="+S5(ASK,OrderSymbol())+" OpenPrice="+S5(OrderOpenPrice(),OrderSymbol())+" StopLevel="+S5(StopLevel,OrderSymbol()));}
                  break;
               case OP_BUYLIMIT:       //  D E L   B U Y L I M I T
                  if (shouldClose){
                     if (ASK-OrderOpenPrice()>StopLevel){   make=OrderDelete(OrderTicket(),clrRed);   REPORT(ExpNum,"Del BuyLimit/"+S4(OrderOpenPrice(),OrderSymbol()));}
                     else                                                                             REPORT(ExpNum,"Can't Del BUYLIMIT near market! ASK="+S5(ASK,OrderSymbol())+" OpenPrice="+S5(OrderOpenPrice(),OrderSymbol())+" StopLevel="+S5(StopLevel,OrderSymbol()));}
                  break;
               }// switch(Order)
            if (make) break;
            if (ERROR_CHECK("MODIFY "+ORD2STR(Order)+" Ticket="+S0(OrderTicket())+" repeat="+S0(repeat),ExpNum)) repeat--; else repeat=0;
            }  //while(repeat)
         if (Orders!=OrdersTotal()) {ReSelect=true; break;}
         }// for(Ord=0; Ord<Orders; Ord++){
      }// while(ReSelect)
   ORDER_CHECK();
   FREE(Mgc,"Terminal");
   }
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
void MARKET_UPDATE(string SYM){ // ASK, BID, DIGITS, Spred, StopLevel
   RefreshRates(); 
   ASK      =float(MarketInfo(SYM,MODE_ASK)); 
   BID      =float(MarketInfo(SYM,MODE_BID));    // в функции GLOBAL_ORDERS_SET() ордера ставятся с одного графика на разные пары, поэтому надо знать данные пары выставляемого ордера     
   DIGITS   =short(MarketInfo(SYM,MODE_DIGITS)); // поэтому надо знать данные пары выставляемого ордера
   Spred    =float(MarketInfo(SYM,MODE_SPREAD) * MarketInfo(SYM,MODE_POINT));
   StopLevel=float((MarketInfo(SYM,MODE_STOPLEVEL) + MarketInfo(SYM,MODE_SPREAD)) * MarketInfo(SYM,MODE_POINT));  // Спред необходимо учитывать, т.к. вход и выход из позы происходят по разным ценам (ask/bid)
   }      
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
void EXPERT_PARENT_CLASS::ORDER_CHECK(){   // ПАРАМЕТРЫ ОТКРЫТЫХ И ОТЛОЖЕННЫХ ПОЗ
   // --- multi-position array: canonical source of truth ---
   PosCount = 0;
   for (int i=0; i<MAX_MULTIPOS; i++) Pos[i].active=false;
   // --- legacy BUY/SEL singleton: kept blank, repopulated for backcompat below ---
   BUY.Val=0; BUY.Typ=NONE; BUY.Stp=0; BUY.Prf=0; BUY.T=0;
   SEL.Val=0; SEL.Typ=NONE; SEL.Stp=0; SEL.Prf=0; SEL.T=0;
   for (int i=0; i<OrdersTotal(); i++){
      if (OrderSelect(i, SELECT_BY_POS, MODE_TRADES)!=true || OrderMagicNumber()!=Mgc) continue;
      if (OrderType()==6) continue; // ролловеры не записываем
      POSITION_TRACKER p; p.active=true; p.ticket=OrderTicket();
      p.data.T   =OrderOpenTime();
      p.data.Val =float(OrderOpenPrice());
      p.data.Stp =float(OrderStopLoss());
      p.data.Prf =float(OrderTakeProfit());
      switch(OrderType()){
         case OP_BUYSTOP:  p.data.Typ=STOP;  AddPosition(p); break;
         case OP_BUYLIMIT: p.data.Typ=LIMIT; AddPosition(p); break;
         case OP_BUY:      p.data.Typ=MARKET;AddPosition(p); break;
         case OP_SELLSTOP: p.data.Typ=STOP;  AddPosition(p); break;
         case OP_SELLLIMIT:p.data.Typ=LIMIT; AddPosition(p); break;
         case OP_SELL:     p.data.Typ=MARKET;AddPosition(p); break;
      }
      // Backcompat shim: when PosCount<=1 mirror into legacy singleton BUY/SEL.
      // At MT5_MaxPositions=1 this keeps the rest of the advisor (OUTPUT/COUNT/INPUT/
      // lib_ML_Signal) reading `BUY.Typ`/`SEL.Typ` working unchanged until Tasks 3-5
      // route them through Pos[].
      if (OrderType()==OP_BUYSTOP  || OrderType()==OP_BUYLIMIT || OrderType()==OP_BUY) {
         BUY=p.data;
      } else if (OrderType()==OP_SELLSTOP || OrderType()==OP_SELLLIMIT || OrderType()==OP_SELL) {
         SEL=p.data;
      }
   }
   }  // в этой функции нельзя вызывать ERROR_CHECK(), т.к. она сама вызывается в ERROR_CHECK и при возникновении повторной ошибки происходит переполнение стека
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
void EXPERT_PARENT_CLASS::ORDERS_COLLECT(){// Запишем ордера для выставления в массив. 
   if (set.BUY.Val>0){ // запланировано открытие лонга
      GlobalVariableSet(S0(Mgc)+"set.BUY.Val",   set.BUY.Val);
      GlobalVariableSet(S0(Mgc)+"set.BUY.Stp",   set.BUY.Stp);
      GlobalVariableSet(S0(Mgc)+"set.BUY.Prf",   set.BUY.Prf);
      GlobalVariableSet(S0(Mgc)+"set.BUY.Exp",   set.BUY.Exp);
      Print(Mgc,": ORDERS_COLLECT: set.BUY=",S4(set.BUY.Val),"/",S4(set.BUY.Stp),"/",S4(set.BUY.Prf)," Expir=",DTIME(set.BUY.Exp)); 
      }
   if (set.SEL.Val>0){
      GlobalVariableSet(S0(Mgc)+"set.SEL.Val",   set.SEL.Val);
      GlobalVariableSet(S0(Mgc)+"set.SEL.Stp",   set.SEL.Stp);
      GlobalVariableSet(S0(Mgc)+"set.SEL.Prf",   set.SEL.Prf);
      GlobalVariableSet(S0(Mgc)+"set.SEL.Exp",   set.SEL.Exp);
      Print(Mgc,": ORDERS_COLLECT: SetSell=",S4(set.SEL.Val),"/",S4(set.SEL.Stp),"/",S4(set.SEL.Prf)," Expir=",DTIME(set.SEL.Exp));   
   }  }// 
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ  
struct ORDER_DATA{// данные эксперта
   uchar    E; // порядковый номер эксперта ордера
   int      Mgc, Typ;
   datetime Exp; 
   float    Val, Stp, Prf, Lot, NewLot;   
   };  
ORDER_DATA ORD[255];  
   
void GLOBAL_ORDERS_SET(){ // выставление ордеров с учетом риска остальных экспертов 
   if (!Real) return;  // mode=0 режим выставления своих ордеров,  mode=1 режим проверки рисков
   double  OpenRisk=0, OpenMargin=0, NewOrdersRisk=0, NewOrdersMargin=0, MarginCorrect=1, RiskCorrect=1;
   uchar Orders=0;
   GlobalVariableSet("LastBalance",AccountBalance()); // для ф. CHECK_OUT()
   GlobalVariableSet("CHECK_OUT",TimeCurrent());
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__)); 
   Print(EXP[CurExp].Mgc,":                 *   G L O B A L   O R D E R S   S E T   B E G I N   *"); 
   // перепишем из глобальных переменных в массивы ПАРАМЕТРЫ НОВЫХ ОРДЕРОВ
   for (uchar e=0; e<ExpTotal; e++){            // перебор массива с параметрами всех экспертов
      string magic=S0(EXP[e].Mgc);
      if (GlobalVariableCheck(magic+"set.BUY.Val")){// есть ордер для выставления
         ORD[Orders].Mgc   =EXP[e].Mgc;
         ORD[Orders].Typ   =10; // значит set.BUY.Val
         ORD[Orders].Lot   =0;   // лот расчитается ниже, исходя из индивидуального риска
         ORD[Orders].Val   =float(GlobalVariableGet(magic+"set.BUY.Val"));        GlobalVariableDel(magic+"set.BUY.Val"); // тут же  
         ORD[Orders].Stp   =float(GlobalVariableGet(magic+"set.BUY.Stp"));        GlobalVariableDel(magic+"set.BUY.Stp"); // удаляем
         ORD[Orders].Prf   =float(GlobalVariableGet(magic+"set.BUY.Prf"));        GlobalVariableDel(magic+"set.BUY.Prf"); // считанный
         ORD[Orders].Exp   =datetime(GlobalVariableGet(magic+"set.BUY.Exp"));     GlobalVariableDel(magic+"set.BUY.Exp"); // глобал
         Orders++;    //  Print("NewOrder ",magic," ",S4(ORD[Orders].Val),"/",S4(ORD[Orders].Stp),"/",S4(ORD[Orders].Prf));
         }      
      if (GlobalVariableCheck(magic+"set.SEL.Val")){// есть ордер для выставления
         ORD[Orders].Mgc   =EXP[e].Mgc;
         ORD[Orders].Typ   =11; // значит set.SEL.Val
         ORD[Orders].Lot   =0;   // лот расчитается ниже, исходя из индивидуального риска
         ORD[Orders].Val   =float(GlobalVariableGet(magic+"set.SEL.Val"));        GlobalVariableDel(magic+"set.SEL.Val"); // тут же  
         ORD[Orders].Stp   =float(GlobalVariableGet(magic+"set.SEL.Stp"));        GlobalVariableDel(magic+"set.SEL.Stp"); // удаляем
         ORD[Orders].Prf   =float(GlobalVariableGet(magic+"set.SEL.Prf"));        GlobalVariableDel(magic+"set.SEL.Prf"); // считанный
         ORD[Orders].Exp   =datetime(GlobalVariableGet(magic+"set.SEL.Exp"));     GlobalVariableDel(magic+"set.SEL.Exp"); // глобал
         Orders++;    //  Print("NewOrder ",magic," ",S4(ORD[Orders].Val),"/",S4(ORD[Orders].Stp),"/",S4(ORD[Orders].Prf));
      }  }
   // запишем в массивы параметры имеющихся ордеров  (рыночных и отложенных) 
   for (int i=0; i<OrdersTotal(); i++){// перебераем все открытые и отложенные ордера всех экспертов счета и дописываем их в массив ORD. Ролловеры (OrderType=6) туда не пишем.
      if (OrderSelect(i, SELECT_BY_POS, MODE_TRADES)!=true) continue;
      if (OrderType()==6) continue; // ролловеры не записываем
      ORD[Orders].Typ   =OrderType();             
      ORD[Orders].Val   =float(OrderOpenPrice());
      ORD[Orders].Stp   =float(OrderStopLoss());
      ORD[Orders].Prf   =float(OrderTakeProfit());
      ORD[Orders].Lot   =float(OrderLots());
      ORD[Orders].Mgc   =(int)OrderMagicNumber();
      ORD[Orders].Exp   =OrderExpiration();   //Print("CurrentOrder-",Ord," ",ORD[Ord].Mgc,": ",ORD2STR(ORD[Ord].Typ)," ",ORD[Ord].Sym," ",S4(ORD[Ord].Val),"/",S4(ORD[Ord].Stp),"/",S4(ORD[Ord].Prf)," Expir=",TimeToStr(ORD[Ord].Exp,TIME_DATE|TIME_MINUTES)," CurLot=",S2(ORD[Ord].Lot));                   
      Orders++; // Print("Отложенные ордера = ",Ord," OrderType()=",OrderType());
      }   // теперь массив ORD содержит список всех открытых, отложенных и предстоящих установке ордеров
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   if (Orders==0){
      Print(EXP[CurExp].Mgc,":                 *           N O   O R D E R S                   *"); 
      Print(EXP[CurExp].Mgc,":                 *   G L O B A L   O R D E R S   S E T   E N D   *");
      GlobalVariableSet("ORDERS_STATE",ORDERS_STATE());
      return;}            
   // Пересчитаем РЕАЛЬНЫЙ РИСК КАЖДОГО ЭКСПЕРТА ЧЕРЕЗ MM(), с учетом нового баланса 
   for (uchar i=0; i<Orders; i++){
      for (uchar e=0; e<ExpTotal; e++){            // из массива с параметрами всех экспертов
         if (ORD[i].Mgc==EXP[e].Mgc){
            ORD[i].E=e; // номер эксперта в общем массиве
            break;    
         }  } 
      float Stop=MathAbs(ORD[i].Val-ORD[i].Stp);
      uchar E=ORD[i].E;
      string SYM=EXP[E].Sym;
      if (ORD[i].Typ<2){// открытый ордер
         OpenMargin+=ORD[i].Lot*MarketInfo(SYM,MODE_MARGINREQUIRED); // кол-во маржи, необходимой для открытия лотов
         if (ORD[i].Typ==0 && ORD[i].Val-ORD[i].Stp>0)  OpenRisk+=CHECK_RISK(ORD[i].Lot,Stop,SYM); // если стоп еще не ушел в безубыток, считаем риск. В противном случае риск позы равен нулю
         if (ORD[i].Typ==1 && ORD[i].Stp-ORD[i].Val>0)  OpenRisk+=CHECK_RISK(ORD[i].Lot,Stop,SYM); // суммарный риск открытых ордеров 
         Print("Order-",i," ",ORD[i].Mgc,": ",ORD2STR(ORD[i].Typ)," ",SYM," ",S4(ORD[i].Val,SYM),"/",S4(ORD[i].Stp,SYM),"/",S4(ORD[i].Prf,SYM)," Expir=",DTIME(ORD[i].Exp)," Lot=",ORD[i].Lot);
         continue;// считать лот для открытых ордеров не надо
         }
      ORD[i].NewLot =MM(Stop, E);
      if (IsTesting() && Risk==0) ORD[i].NewLot=float(0.1);
      // if (ORD[i].NewLot==0) EXP[e].Risk=0; // MM: CurDD>HistDD!  помечаем в массиве, чтобы больше не возвращаться к этому эксперту.
      Print("Order-",i," ",ORD[i].Mgc,": ",ORD2STR(ORD[i].Typ)," ",SYM," ",S4(ORD[i].Val,SYM),"/",S4(ORD[i].Stp,SYM),"/",S4(ORD[i].Prf,SYM)," Expir=",DTIME(ORD[i].Exp)," Lot=",ORD[i].Lot," NewLot=",ORD[i].NewLot," CHECK_RISK=",CHECK_RISK(ORD[i].NewLot,Stop,SYM),"% CurDD=",S0(CurDD)," HistDD=",S0(EXP[E].HistDD)," LastTestDD=",S0(EXP[E].LastTestDD));      
      NewOrdersRisk+=CHECK_RISK(ORD[i].NewLot,Stop,SYM); // найдем суммарный риск всех новых и отложенных ордеров
      NewOrdersMargin+=ORD[i].NewLot*MarketInfo(SYM,MODE_MARGINREQUIRED); // кол-во маржи, необходимой для открытия новых и отложенных ордеров
      }  //Print ("GLOBAL_ORDERS_SET()/ РИСКИ:  Маржа открытых = ",OpenOrdMargNeed/AccountFreeMargin()*100,",  Маржа отложников и новых = ",MargNeed/AccountFreeMargin()*100,", LongRisk=",LongRisk,"%, OpenLongRisk=",OpenLongRisk,"%, ShortRisk=",ShortRisk,"%, OpenShortRisk=",OpenShortRisk,"%, Orders=",Orders);   
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   // П Р О В Е Р К А   Р И С К О В  /
   if (OpenRisk+NewOrdersRisk>MaxRisk && NewOrdersRisk!=0){// суммарный риск открытых и новых позиций превышает допустимый и риск новых позиций>0, т.е. есть что сократить
      if (OpenRisk<MaxRisk){// риск открытых позиций меньше предельного, т.е. остался запас для новых ордеров
         RiskCorrect=0.95*(MaxRisk-OpenRisk)/NewOrdersRisk; 
         REPORT("SumRisk="+S1(OpenRisk+NewOrdersRisk)+"% reduce Risk on "+S1(RiskCorrect*100)+"%");   
      }else{// риск открытых составляет весь допустимый риск,
         RiskCorrect=0;   // т.е. удаляем все новые неоткрытые ордера 
         REPORT("Open Orders Risk="+S1(OpenRisk)+"%! delete another pending Orders!"); // если риск открытых ордеров превышает MaxRisk, то RiskDecrease будет отрицательным. Значит оставшиеся ордера надо удалить, обнуляя лоты.
      }  }   
   // П Р О В Е Р К А   М А Р Ж И  ///
   if (OpenMargin+NewOrdersMargin>AccountFreeMargin()*MaxMargin && NewOrdersMargin!=0){// перегрузили маржу 
      if (OpenMargin<AccountFreeMargin()*MaxMargin){// маржа открытых позиций меньше предельной, т.е. остался запас для новых ордеров
         MarginCorrect=0.95*(AccountFreeMargin()*MaxMargin-OpenMargin)/NewOrdersMargin; // расчитаем коэффициент уменьшения риска/лота отложенных и новых ордеров (умножаеам на 0.95 для гистерезиса)
         REPORT("Margin="+S1(OpenMargin+NewOrdersMargin)+"% Decrease MarginRisk on "+S1(MarginCorrect*100)+"%"); 
      }else{
         MarginCorrect=0; // если риск открытых ордеров превышает MaxRisk, то RiskDecrease будет отрицательным. Значит оставшиеся ордера надо удалить, обнуляя лоты.
         REPORT("Open Orders Margin="+S1(OpenMargin)+"%! delete all pending Orders!");
      }  }
   double LotDecrease=MathMin(MarginCorrect,RiskCorrect); // из возможных корректировок риска и маржи берем максимальное сокращение
   if (LotDecrease<1){ // при инициализации MarginCorrect=1 и RiskCorrect=1. Если потребовалась одна из корректировок
      for (short i=0; i<Orders; i++){// пересчитаем все лоты
         if (ORD[i].Typ<2 || ORD[i].NewLot==0) continue; // открытые (Type=0..1) НЕ ТРОГАЕМ
         ORD[i].NewLot=float(NormalizeDouble(ORD[i].NewLot*LotDecrease, LotDigits));// на всех отложниках и новых ордерах уменьшаем риск/лот, чтобы вписаться в маржу
         if (LotDecrease>0 && ORD[i].NewLot<MarketInfo(EXP[ORD[i].E].Sym,MODE_MINLOT)){// лот меньше допустимого
            // Print("GLOBAL_ORDERS_SET NewLot<MINLOT ",i,". ",ORD[i].Mgc,"/",ORD2STR(ORD[i].Typ)," i.e. ",ORD[i].NewLot,"<",MarketInfo(ORD[i].Sym,MODE_MINLOT)," NewLot=",MarketInfo(ORD[i].Sym,MODE_MINLOT));
            ORD[i].NewLot=float(MarketInfo(EXP[ORD[i].E].Sym,MODE_MINLOT));
      }  }  }
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   // В Ы С Т А В Л Е Н И Е   О Р Д Е Р О В  
   for (short i=0; i<Orders; i++){
      if (ORD[i].Typ<2) continue; // открытые (Type=0..1) НЕ ТРОГАЕМ
      uchar E=ORD[i].E;
      string SYM=EXP[E].Sym;
      //if (ORD[i].Lot>0 && ORD[i].NewLot>0 && MathAbs(ORD[i].Lot-ORD[i].NewLot)<MarketInfo(ORD[i].Sym,MODE_LOTSTEP)){
      if (ORD[i].Lot==ORD[i].NewLot){
         Print("GLOBAL_ORDERS_SET ",i,". ",ORD[i].Mgc,"/",ORD2STR(ORD[i].Typ)," SkipModify i.e. Lot=NewLot=",ORD[i].Lot);
         continue;} 
      if (ORD[i].Typ<10 && ORD[i].Exp>0 && ORD[i].Exp-TimeCurrent()<EXP[E].Per*60){ // экспирация отложника истекает на этом баре, его модификация приведет к ошибке
         Print("GLOBAL_ORDERS_SET ",i,". ",ORD[i].Mgc,"/",ORD2STR(ORD[i].Typ)," SkipModify i.e. Order Expiration finish soon ",DTIME(ORD[i].Exp));
         continue;}
      MARKET_UPDATE(SYM); // ASK, BID, DIGITS, Spred, StopLevel
      EXP[E].ORDER_CHECK();
      EXP[E].set.BUY.Val=0;  EXP[E].set.BUY.Stp=ORD[i].Stp; EXP[E].set.BUY.Prf=ORD[i].Prf; EXP[E].set.BUY.Exp=ORD[i].Exp;
      EXP[E].set.SEL.Val=0;  EXP[E].set.SEL.Stp=ORD[i].Stp; EXP[E].set.SEL.Prf=ORD[i].Prf; EXP[E].set.SEL.Exp=ORD[i].Exp;
      switch(ORD[i].Typ){
         case 2:  EXP[E].set.BUY.Val=ORD[i].Val; EXP[E].BUY.Val=0;   break; // выбираем тип
         case 3:  EXP[E].set.SEL.Val=ORD[i].Val; EXP[E].SEL.Val=0;   break; // ордера
         case 4:  EXP[E].set.BUY.Val=ORD[i].Val; EXP[E].BUY.Val=0;   break; // который
         case 5:  EXP[E].set.SEL.Val=ORD[i].Val; EXP[E].SEL.Val=0;   break; // нужно удалить
         case 10: EXP[E].set.BUY.Val=ORD[i].Val;              break;
         case 11: EXP[E].set.SEL.Val=ORD[i].Val;              break;
         } 
      Lot  =ORD[i].NewLot;     if (IsTesting()) Lot=float(0.1); 
      if (Lot>0)  Print("GLOBAL_ORDERS_SET ",i,": ",EXP[E].Mgc,"/",ORD2STR(ORD[i].Typ)," ",SYM," ",S4(ORD[i].Val,SYM),"/",S4(ORD[i].Stp,SYM),"/",S4(ORD[i].Prf,SYM),"  Risk=",EXP[E].Rsk,"%  Lot=",Lot,"  Expir=",DTIME(ORD[i].Exp));
      else        REPORT(E,"Delete "+S0(EXP[E].Mgc)+", CurDD>HistDD");
      if (ORD[i].Typ<6)   EXP[E].MODIFY();      // Удаление отложников 
      if (Lot>0){
         EXP[E].SET_BUY();
         EXP[E].SET_SEL();
      }  }    
   GlobalVariableSet("ORDERS_STATE",ORDERS_STATE());
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   Print(EXP[CurExp].Mgc,":                 *   G L O B A L   O R D E R S   S E T   E N D   * ");    
   }
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
void CHECK_OUT(){// Проверка недавних ордеров и состояния баланса для изменения лота текущих отложников  (При инвестировании или после крупных сделок) ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
   if (!Real) return; 
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   if (TimeLocal()-GlobalVariableGet("CHECK_OUT")<600) return;
   GlobalVariableSet("CHECK_OUT",TimeLocal());         // обновляем время последнего изменения глобала  "CHECK_OUT"
   if (!GlobalVariableSetOnCondition("GlobalOrdersSet",EXP[CurExp].Mgc,0)) return; // попытка захвата флага доступа к ф. "GlobalOrdersSet"    
   GlobalVariableSet("GlobalOrdersSet"+"Busy",TimeLocal()); // обновляем время последнего изменения глобала "GlobalOrdersSet"
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   for (int i=0; i<TimeLocal()-GlobalVariableTime("ORDERS_STATE"); i+=300){ // кол-во пустых строк равно
      Print(" ");                                                          // количеству десятиминуток с последнего обращения к глобалу "ORDERS_STATE"
      if (i>3000) break;}  // берегем бумагу - не более 5 строк
   bool NeedToCheckOrders=false;
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   if (GlobalVariableGet("ORDERS_STATE")!=ORDERS_STATE()){ // время последнего выставленного ордера изменилось
      REPORT("CHECK_OUT(): ORDERS_STATE changed, recount orders");
      NeedToCheckOrders=true;
      }  
   double BalanceChange=(AccountBalance()-GlobalVariableGet("LastBalance"))*100/AccountBalance();
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   if (MathAbs(BalanceChange)>5){
      REPORT("CHECK_OUT(): BalanceChange="+ S0(BalanceChange) +"%, recount orders");  Print("LastBalance=",S0(GlobalVariableGet("LastBalance"))," AccountBalance=",S0(AccountBalance()));
      NeedToCheckOrders=true;
      }
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   for (short e=0; e<ExpTotal; e++){// перебор массива с параметрами всех экспертов
      string magic=S0(EXP[e].Mgc);
      if (GlobalVariableCheck(magic+"set.BUY.Val") || GlobalVariableCheck(magic+"set.SEL.Val")){ // поиск ордеров для выставления через глобалы
         REPORT("CHECK_OUT(): find NewOrder of "+magic+" to set");
         NeedToCheckOrders=true;
      }  }   
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   if (NeedToCheckOrders){
      Print(EXP[CurExp].Mgc,": CHECK_OUT(): Need to start function 'GLOBAL_ORDERS_SET()'");
      GLOBAL_ORDERS_SET();} // расставляем ордера
   else Print(EXP[CurExp].Mgc,": CHECK_OUT(): ORDERS_STATE not changed, BalanceChange=",S1(BalanceChange),"%"); 
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   FREE(EXP[CurExp].Mgc,"GlobalOrdersSet");
   } 
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
string ORD2STR(int Type){ 
   switch(Type){
      case OP_BUY:      return ("BUY"); 
      case OP_SELL:     return ("SELL");
      case OP_BUYLIMIT: return ("BUYLIMIT"); 
      case OP_SELLLIMIT:return ("SELLLIMIT");
      case OP_BUYSTOP:  return ("BUYSTOP");
      case OP_SELLSTOP: return ("SELLSTOP");
      case 6:  return ("RollOver");
      case 10: return ("setBUY");
      case 11: return ("setSELL");
      default: return ("-");
   }  }
   
string ORDTYP(int Type){ 
switch(Type){
      case NONE:  return ("NONE"); 
      case MARKET:return ("MARKET");
      case STOP:  return ("STOP"); 
      case LIMIT: return ("LIMIT");
      case SET:   return ("SET");  // устанавливаемый 
      default:    return ("UNKNOWN");
   }  }   
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
datetime ORDERS_STATE(){ // состояние ордеров: время последнего + общее кол-во.
   datetime LastOrdTime=0;
   for (int i=0; i<OrdersTotal(); i++){// перебераем все открытые и отложенные ордера всех экспертов счета
      if (OrderSelect(i, SELECT_BY_POS, MODE_TRADES)==false) continue; 
      if (OrderType()==6) continue; // ролловеры пропускаем
      if (OrderOpenTime()>LastOrdTime) LastOrdTime=OrderOpenTime(); //Print("Order ",ORD2STR(OrderType())," time=",TimeToStr(OrderOpenTime(),TIME_DATE | TIME_MINUTES), " LastOrdTime=",TimeToStr(LastOrdTime,TIME_DATE | TIME_MINUTES));
      }      
   return (LastOrdTime+OrdersTotal()); 
   }
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
