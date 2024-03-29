void INPUT(){ // Ф И Л Ь Т Р Ы    В Х О Д А    ///////////////////////////////////////////////////////
   set.BUY.Val=0; set.BUY.Stp=0; set.BUY.Prf=0; 
   set.SEL.Val=0; set.SEL.Stp=0; set.SEL.Prf=0; 
   bool SigUp=(InUp && TrUp && BUY.Typ!=MARKET && (!mem.BUY.Val || Mod>0)); // 
   bool SigDn=(InDn && TrDn && SEL.Typ!=MARKET && (!mem.SEL.Val || Mod>0)); //   
   if (!SigUp && !SigDn) return; // Print(" Up=",Up," Dn=",Dn);   
   float Delta =ATR*D/2;   // 0 .. 2.5 
   if (Mod>0) Delta=ATR*FIBO(D); // 0, 0.5, 1, 2, 3, 5
   //Print("ATR=",ATR," Delta=",Delta," FIBO=",FIBO(D));    
   switch (Iprice){  // расчет цены входов:         
      case 1:  // по рынку + ATR          
         set.BUY.Val=float(Open[0])+Spred+Delta;     // ask и bid формируем из Open[0],
         set.SEL.Val=float(Open[0])-Delta;          // чтоб отложники не зависели от шустрых движух   
      break;
      case 2:  // HI / LO
         set.BUY.Val=HI+Delta;    
         set.SEL.Val=LO-Delta;    
      break; 
      case 3: // по ФИБО уровням       
         set.BUY.Val=FIBO_LEVELS( D);       
         set.SEL.Val=FIBO_LEVELS(-D); 
           
      break;
      case 4:  // LO / HI (was Not used in previous release)
         set.BUY.Val = LO+Delta;     
         set.SEL.Val = HI-Delta;     
      break;
      }    
   if (SigUp){  // 
      if (!BrkBck) SET_BUY_STOP(); // ставим стоп, если не включен режим "виртуальных" ордеров
      if (Del==1){      // удаление старого ордера при появлении нового сигнала  
         if (BUY.Val     && MathAbs(set.BUY.Val-BUY.Val)>ATR/2)      {X("ReSet Order",BUY.Val,bar,clrRed);     BUY.Val=0;}     // если старый ордер далеко от нового
         if (mem.BUY.Val && MathAbs(set.BUY.Val-mem.BUY.Val)>ATR/2)  {X("ReSet Order",mem.BUY.Val,bar,clrRed); mem.BUY.Val=0;}
         }
      if (Del==2) CLOSE_SEL(float(Ask),Present,"LongSignal");   // при появлении нового сигнала удаляем противоположный или если ордер остался один;
      }    
   if (SigDn){  // 
      if (!BrkBck) SET_SEL_STOP();
      if (Del==1){
         if (SEL.Val     && MathAbs(set.SEL.Val-SEL.Val)>ATR/2)      {X("ReSet Order",SEL.Val,bar,clrRed);     SEL.Val=0;} 
         if (mem.SEL.Val && MathAbs(set.SEL.Val-mem.SEL.Val)>ATR/2)  {X("ReSet Order",mem.SEL.Val,bar,clrRed); mem.SEL.Val=0;}  
         }
      if (Del==2) CLOSE_BUY(float(Bid),Present,"ShortSignal");   
      }    
   if (!SigUp || BUY.Val || mem.BUY.Val) set.BUY.Val=0;  // если остались старые ордера,
   if (!SigDn || SEL.Val || mem.SEL.Val) set.SEL.Val=0;  // новые не выставляем 
   ERROR_CHECK(__FUNCTION__);
   }
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
void SET_BUY_STOP(){// стопы в отдельную ф., чтобы использовать в откатах VIRTUAL_ORDERS() 
   if (Mod==0)    SET_BUY_OLD();
   else{
      if (S>0)    set.BUY.Stp=set.BUY.Val-ATR*FIBO(S);   
      else        set.BUY.Stp=PIC_LO(bar,-S,set.BUY.Val-ATR*FIBO(-S));   
      if (P==0)   set.BUY.Prf =0;                      else
      if (P>0)    set.BUY.Prf=set.BUY.Val+ATR*FIBO(P);  else
      if (P<0)    set.BUY.Prf=set.BUY.Val-(set.BUY.Val-set.BUY.Stp)/2*P;    
      if (Iprice==3){  // вход и стоп по фибам
         set.BUY.Stp=FIBO_LEVELS( D-S);  
         set.BUY.Prf=FIBO_LEVELS( D+P);
   }  }  }   
void SET_SEL_STOP(){
   if (Mod==0)    SET_SEL_OLD();    
   else{
      if (S>0)    set.SEL.Stp=set.SEL.Val+ATR*FIBO(S);  
      else        set.SEL.Stp=PIC_HI(bar,-S,set.SEL.Val+ATR*FIBO(-S));    
      if (P==0)   set.SEL.Prf =0;                      else
      if (P>0)    set.SEL.Prf=set.SEL.Val-ATR*FIBO(P);  else
      if (P<0)    set.SEL.Prf=set.SEL.Val+(set.SEL.Stp-set.SEL.Val)/2*P;   
      if (set.SEL.Prf<0) set.SEL.Prf=0;
      if (Iprice==3){  // вход и стоп по фибам
         set.SEL.Stp=FIBO_LEVELS(-D+S);  
         set.SEL.Prf=FIBO_LEVELS(-D-P);  
   }  }  }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
void VIRTUAL_ORDERS(){ // виртуальные ордера для откатов после пробоя
   if (BrkBck==0) {mem.BUY.Val=0; mem.SEL.Val=0; return;}  
   if (set.BUY.Val){  // выставлен/обновлен лонг                              L O N G
      mem.BUY=set.BUY; // запоминаем его параметры в виртуальник
      set.BUY.Val=0;  // и удаляем сам ордер
      V("mem.BUY "+S4(mem.BUY.Val),mem.BUY.Val,bar,clrBlue);
      }
   if (ExpirBars && mem.BUY.Val && Time[0]>mem.BUY.Exp){ // Экспирация виртуального ордера проверяется вручную
      X("BUY_Expiration",mem.BUY.Val,bar,clrBlue);
      mem.BUY.Val=0;                     // удаляем виртуальник
      }
   float delta=ATR*BrkBck;   
   if (Mod>0) delta=ATR*BrkBck/2;
   if (mem.BUY.Val){ // стоит виртуальник (стоп либо лимит)
      int B=bar;
      if (High[1]>mem.BUY.Val && High[2]<mem.BUY.Val){ // пересечение стоп-ордера снизу вверх, стваим лимитник ниже
         if (BrkBck==-1)   for (B=bar+1; B<Bars-2; B++)  if (High[B]<High[B+1]) break; // ближайшая впадина
         if (BrkBck<=-2)   for (B=bar+1; B<Bars-2; B++)  if (High[B]>High[B+1] && High[B]>High[B-1] && High[B]<mem.BUY.Val-(ATR*FIBO(-BrkBck-2))) break; // ближайший пик
         if (BrkBck>0)     set.BUY.Val=mem.BUY.Val-delta;   // откат ниже пробитого уровня
         else{ 
            if (B<Bars-3)  set.BUY.Val=(float)High[B];
         }  }
      if (Low[1]<mem.BUY.Val && Low[2]>mem.BUY.Val){ // пересечение лимитника сверху вниз, ставим стоп ордер выше
         if (BrkBck==-1)   for (B=bar+1; B<Bars-2; B++)  if (Low[B]>Low[B+1] && Low[B]>mem.BUY.Val) break;
         if (BrkBck<=-2)   for (B=bar+1; B<Bars-2; B++)  if (Low[B]<Low[B+1] && Low[B]<Low[B-1] && Low[B]>mem.BUY.Val+(ATR*FIBO(-BrkBck-2))) break;
         if (BrkBck>0)     set.BUY.Val=mem.BUY.Val+delta;
         else{  
            if (B<Bars-3)  set.BUY.Val=(float)Low[B]; 
         }  }
      if (set.BUY.Val){  // если виртуальник зацепило, т.е. выставлен реальный ордер  
         SET_BUY_STOP();// ставим к нему стоп
         V("BUY "+S4(set.BUY.Val),mem.BUY.Val,bar,clrBlue);
         mem.BUY.Val=0; // удаляем виртуальник
      }  }          
   if (set.SEL.Val){ //                                                        S H O R T        
      mem.SEL=set.SEL;
      set.SEL.Val=0;
      A("mem.SEL "+S4(mem.SEL.Val),mem.SEL.Val,bar,clrGreen);
      }
   if (ExpirBars && mem.SEL.Val && Time[0]>mem.SEL.Exp){
      X("SEL_Expiration",mem.SEL.Val,bar,clrGreen);
      mem.SEL.Val=0;
      }
   if (mem.SEL.Val){
      int B=bar;
      if (Low[1]<mem.SEL.Val && Low[2]>mem.SEL.Val){
         if (BrkBck==-1)   for (B=bar+1; B<Bars-2; B++)  if (Low[B]>Low[B+1]) break;
         if (BrkBck<=-2)   for (B=bar+1; B<Bars-2; B++)  if (Low[B]<Low[B+1] && Low[B]<Low[B-1] && Low[B]>mem.SEL.Val+(ATR*FIBO(-BrkBck-2))) break;
         if (BrkBck>0)     set.SEL.Val=mem.SEL.Val+delta;  
         else{             
            if (B<Bars-3)  set.SEL.Val=(float)Low[B]; 
         }  }
      if (High[1]>mem.SEL.Val && High[2]<mem.SEL.Val){
         if (BrkBck==-1)   for (B=bar+1; B<Bars-2; B++)  if (High[B]<High[B+1] && High[B]<mem.SEL.Val) break; // ближайшая впадина 
         if (BrkBck<=-2)   for (B=bar+1; B<Bars-2; B++)  if (High[B]>High[B+1] && High[B]>High[B-1] && High[B]<mem.SEL.Val-(ATR*FIBO(-BrkBck-2))) break;   // ближайший пик
         if (BrkBck>0)     set.SEL.Val=mem.SEL.Val-delta;
         else{              
            if (B<Bars-3)  set.SEL.Val=(float)High[B];  
         }  }
      if (set.SEL.Val){   
         SET_SEL_STOP();
         A("SEL "+S4(set.SEL.Val),mem.SEL.Val,bar,clrGreen);
         mem.SEL.Val=0;   
   }  }  } 
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
float FIBO(int Val){  
   if (Mod==0) return(short(Val));
   float sign=1;
   if (Val<0) sign=-1;
   switch(MathAbs(Val)){
      case 1: if (Mod<2) return(0); else return(sign/2); 
      case 2: return(sign*1);   
      case 3: return(sign*2);   
      case 4: return(sign*3);   
      case 5: return(sign*5);   
      case 6: return(sign*8);   
      case 7: return(sign*13);  
      case 8: return(sign*21);  
      case 9: return(sign*34);  
      case 10:return(sign*55);  
      default:return (0);
   }  }
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
float FIBO_LEVELS(int FiboLevel){ // Считаем ФИБУ:  Разбиваем диапазон HL   0   11.8   23.6   38.2  50  61.8   76.4  88.2   100 
   double Fib=0;
   switch(FiboLevel){
      case 16: Fib= (HI-LO)*2.500; break;
      case 15: Fib= (HI-LO)*2.382; break;
      case 14: Fib= (HI-LO)*2.236; break;
      case 13: Fib= (HI-LO)*2.118; break;
      case 12: Fib= (HI-LO)*2.000; break;
      case 11: Fib= (HI-LO)*1.882; break;
      case 10: Fib= (HI-LO)*1.764; break;
      case  9: Fib= (HI-LO)*1.618; break;
      case  8: Fib= (HI-LO)*1.500; break;
      case  7: Fib= (HI-LO)*1.382; break;
      case  6: Fib= (HI-LO)*1.236; break;
      case  5: Fib= (HI-LO)*1.118; break;
      case  4: Fib= (HI-LO)*1.000; break; // Hi
      case  3: Fib= (HI-LO)*0.882; break;
      case  2: Fib= (HI-LO)*0.764; break; 
      case  1: Fib= (HI-LO)*0.618; break; // Золотое сечение
      case  0: Fib= (HI-LO)*0.500; break; 
      case -1: Fib= (HI-LO)*0.382; break; // Золотое сечение 
      case -2: Fib= (HI-LO)*0.236; break;
      case -3: Fib= (HI-LO)*0.118; break; 
      case -4: Fib= (HI-LO)*0;     break; // Lo   
      case -5: Fib=-(HI-LO)*0.118; break; 
      case -6: Fib=-(HI-LO)*0.236; break;
      case -7: Fib=-(HI-LO)*0.382; break; 
      case -8: Fib=-(HI-LO)*0.500; break; 
      case -9: Fib=-(HI-LO)*0.618; break; 
      case-10: Fib=-(HI-LO)*0.764; break;
      case-11: Fib=-(HI-LO)*0.882; break;
      case-12: Fib=-(HI-LO)*1.000; break;
      case-13: Fib=-(HI-LO)*1.118; break;
      case-14: Fib=-(HI-LO)*1.236; break;
      case-15: Fib=-(HI-LO)*1.382; break;
      case-16: Fib=-(HI-LO)*1.500; break;
      } //Print("FIBO: HI=",S4(HI)," LO=",S4(LO));
   return(N5(LO+Fib));
   }


   
   
         
         
         
         
         
         
         
         
      

