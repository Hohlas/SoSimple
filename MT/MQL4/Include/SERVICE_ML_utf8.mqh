
string ReportFile="Reports.csv";
ushort ExpPause; // индивидуальная пауза для рассинхронизации равна порядковому номеру строки настроек эксперта
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
int OnInit() {
   if (!IsTesting() && !IsOptimization()) Real = true;
   ExpTotal = 1;
   CurExp = 0;
   InitDeposit = float(AccountBalance());
   DayMinEquity = InitDeposit;
   MaxRisk = MAX_RISK;
   if (MarketInfo(Symbol(),MODE_LOTSTEP)<0.1) LotDigits=2; else LotDigits=1;
   CHART_SETTINGS();
   EXP[0].Mgc = 777777;
   EXP[0].Sym = Symbol();
   EXP[0].Per = (short)Period();
   EXP[0].Rsk = Risk;
   if (EXP[0].Rsk <= 0) EXP[0].Rsk = 1.0; 
   EXP[0].CLASS_INIT(0);
   if (EXP[0].INIT() == INIT_FAILED) return (INIT_FAILED);
   // Принудительная инициализация Atr.Slow (в оригинале это делается при проходе истории в MAIN())
   if (EXP[0].Atr.Slow <= 0) {
      int slowPer = A * A; // SlowAtrPer
      if (1 + slowPer < Bars) {
         float slowAtr = 0;
         for (int b = 1; b < 1 + slowPer; b++) slowAtr += float(High[b] - Low[b]);
         EXP[0].Atr.Slow = slowAtr / slowPer;
         Print("SERVICE_ML: Forced Atr.Slow=", EXP[0].Atr.Slow);
      }
   }
   BarTime = 0; // сброс, чтобы первый тик обработался как новый бар
   return (INIT_SUCCEEDED);
}
void TESTER_FILE_CREATE(uchar e, string FileName) {}
int MAGIC_GENERATOR() { return 777777; }
void INPUT_PARAMETERS_PRINT() {}
bool INPUT_FILE_READ () { return true; }
void EXPERT_PARENT_CLASS::EMPTY_EXPERTS_DELETE() {}
bool EXPERT_SET(uchar e) { 
   CurExp = e;
   EXP[e].RESTORE(); 
   return(true); 
}
bool CHECKSUM(uchar e) { return true; }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
void AFTER(uchar e){// запуск в конце функции Start 
   if (!Real) return; 
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   //EXP[e].mem=mem; // mem.BUY.Val, mem.BUY.Stp, mem.BUY.Prf, mem.BUY.e, ...// сохраняем индивидуальные переменные эксперта
   //EXP[e].Bar=Time[0];
   EXP[e].BACKUP(); // сохранение индивидуальных переменных (HI,LO,DM,DayBar) на каждом баре в режиме последовательного запуска
   EXP[e].CHECK_VARIABLES();   // сравнение значений индикаторов Real/Test
   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ      
void END(){// запуск после прохода всех экспертов 
   if (!Real) return; 
   //if (CurExp>=ExpTotal) CurExp=ExpTotal-1; Print(__FUNCTION__,": CurExp=",CurExp," ExpTotal=",ExpTotal);
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   GlobalVariableSet(NAME+Symbol()+S0(Period()), Time[0]); // флаг завершения обработки своих ордеров маркируем временем открытия текущего бара для дальнейшей прверки общей готовности
   WAITING(EXP[CurExp].Mgc,"GlobalOrdersSet",60);            // захват доступа к функции "GlobalOrdersSet"
   if (GlobalVariableGet(NAME+Symbol()+S0(Period())) == Time[0]){// собственный глобал готовности НЕ изменился, т.е. не участвовал в ф. GLOBAL_ORDERS_SET() 
      string   WarningExperts;
      datetime StartWaiting=TimeLocal();
      for (int i=0; i<300; i++){// на протяжении 30 секунд ждем флаги готовноси всех экспертов проверяя их каждые 100мс
         WarningExperts=""; // список опоздавших
         for (uchar e=0; e<ExpTotal; e++){ // сверяем время готовности каждого эксперта с текущим времением с учетом его ТФ   
            string NameSymPer=EXP[e].Name+EXP[e].Sym+S0(EXP[e].Per); // текстовый идентификатор эксперта,
            if (EXP[e].Name=="Ye$$") continue; // не обращаем внимание на него, т.к. постоянно опаздывает
            if (TimeCurrent() - GlobalVariableGet(NameSymPer) < EXP[e].Per*60 - 300)    continue; // флаг готовности эксперта был выставлен менее (Период-5мин) назад, т.е. он "свежий"
            if (WarningExperts=="" || StringFind(WarningExperts,NameSymPer,0)<0){// Список опоздавших пуст, либо там нет записи об этом эксперте
               WarningExperts=WarningExperts+" \n"+NameSymPer;                     // обновляем список "опоздавших"
            }  }   
         if (WarningExperts==""){ // если список "опоздавших" пуст, заканчиваем ожидание
            Print(EXP[CurExp].Mgc,": ExpertsWaitingTime=",i*100,"ms, All ",ExpTotal," Experts Ready");
            break;}   
         Sleep(100); // мс
         if (TimeLocal()-StartWaiting>120) break; // при зависании компа цикл может длиться намного больше 30сек
         } 
      ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
      if (WarningExperts!="") REPORT("Warning!!! ExpertsNotReady:"+WarningExperts);
      for (uchar e=0; e<ExpTotal; e++)  // маркируем все обрабатываемые эксперты, увеличивая их флаг на 1
         GlobalVariableSet(EXP[e].Name+EXP[e].Sym+S0(EXP[e].Per), GlobalVariableGet(EXP[e].Name+EXP[e].Sym+S0(EXP[e].Per)) + 1); 
      GLOBAL_ORDERS_SET();    //  
      }
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));   
   FREE(EXP[CurExp].Mgc,"GlobalOrdersSet");   
   Sleep(ExpPause); //
   Print(EXP[CurExp].Mgc,": END/Sleep(",ExpPause,")ms");
   SAVE_ALL_EXPERTS_VARIABLES_TO_FILE(); // Сохранение глобальных переменных экспертов данного чарта в файл, доклад о их последних сделках
   SAVE_HISTORY();  
   MAIL_SEND(); 
   if (TimeHour(Time[bar])<TimeHour(Time[bar+1])){// раз в сутки обновляем инфу о экспертах
      REPORT("MIDNIGHT CSV FILE RELOAD");
      INPUT_FILE_READ();} 
   MaxSpred=0; // для статистики пишем макс спред в функции ValueCheck()
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
void WAITING(int magic, string GlobalName, double MaxWaitingTime){// ожидание освобождения глобальной переменнной не более MaxWaitingTime секунд
   if (!Real) return; // 
   if (!GlobalVariableCheck(GlobalName))   GlobalVariableSet(GlobalName,0); 
   while (1){ // захват потока  
      GlobalVariableSetOnCondition(GlobalName,magic,0);
      if (GlobalVariableGet(GlobalName)==magic) break;  // если захвачен
      Sleep(ExpPause); //
      if (BUSY_TIME(GlobalName)>MaxWaitingTime){ // прождали, насильно захватываем торговый поток, т.к. что-то значит не в порядке
         REPORT("Expert "+S0(GlobalVariableGet(GlobalName))+" hold global '"+GlobalName+"' "+TimeToString(BUSY_TIME(GlobalName),TIME_SECONDS)+"!!! Set own flag: "+S0(magic)); // докладываем о занятом торговом потоке
         GlobalVariableSet(GlobalName,0); // принудительный захват
      }  }
   Print(magic,": '",GlobalName,"' BusyTime=",TimeToString(BUSY_TIME(GlobalName),TIME_SECONDS));   
   GlobalVariableSet(GlobalName+"Busy",TimeLocal());// обновляем время последнего изменения глобала
   }
void FREE(int magic, string GlobalName){ // освобождение глобальной переменной
   if (!Real) return;         // в этой функции нельзя вызывать ERROR_CHECK(), т.к. она сама вызывается в ERROR_CHECK и при возникновении повторной ошибки происходит переполнение стека
   if (GlobalVariableSetOnCondition(GlobalName,0,magic)){ // Print(magic,": '",GlobalName,"' FREE");
      return;} // если глобал по прежнему со своим мэджиком, освобождаем 
   REPORT("Expert "+S0(GlobalVariableGet(GlobalName))+" already get global '"+GlobalName+"' !!! BusyTime="+TimeToString(BUSY_TIME(GlobalName),TIME_SECONDS)); 
   } 
datetime BUSY_TIME(string GlobalName){ 
   if (TimeLocal()-datetime(GlobalVariableGet(GlobalName+"Busy"))<0) return(TimeLocal());
   return (TimeLocal()-datetime(GlobalVariableGet(GlobalName+"Busy")));
   }    
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
void OnDeinit(const int reason){
   Print(__FUNCTION__,": CurExp=",CurExp," ExpTotal=",ExpTotal);
   //if (CurExp>=ExpTotal) CurExp=ExpTotal-1;
   if (!Real) return;
   if (!IsTesting() && !IsOptimization()) EventKillTimer();
   switch (reason){ // вместо reason можно использовать UninitializeReason()
      //case 0: str="Эксперт самостоятельно завершил свою работу"; break;
      case 1: REPORT("Program "+NAME+" removed from chart"); break;
      case 2: REPORT("Program "+NAME+" recompile"); break;
      case 3: REPORT("Symbol or Period was CHANGED!"); break;
      case 4: REPORT("Chart closed!"); break;
      case 5: REPORT("Input Parameters Changed!"); break;
      case 6: REPORT("Another Account Activate!"); break; 
      case 9: REPORT("Terminal closed!"); break;   
      }
   if (IsTesting() || IsOptimization()) SAVE_ALL_EXPERTS_VARIABLES_TO_FILE(); // (только при тестировании реала) пропишем в конец файла историю совершенных сделок и кривую баланса 
   //CLEAR_CHART();
   GlobalVariableSet("GlobalOrdersSet",0); // освобождение глобалов, 
   GlobalVariableSet("Terminal",0);        // если были заняты на момент выключения
   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ    
double OnTester(){////  Ф О Р М И Р О В А Н И Е   Ф А Й Л А    О Т Ч Е Т А   /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
   float CustomMax=0;
   if (Real)  for (uchar e=0; e<ExpTotal; e++){
      READ_ARRAY.EXTERN_VARS(e);
      CustomMax=TEST_RESULT(e); 
      }
   else CustomMax=TEST_RESULT(0);
   Print ("OnTester(): ExpTotal=",ExpTotal," CurExp=",CurExp," EXP[0].Mgc=",EXP[0].Mgc," EXP[0].Ver=",EXP[0].Ver," CustomMax=",CustomMax);
   return (CustomMax); // возвращаем критерий оптимизации 
   }
float TEST_RESULT(uchar e){
   float   CustomMax, SD=0,  iDD=0, GrossProfit=0, GrossLoss=0, MidWin, MidLoss,  profit, MaxWin[5], FullProfit=0, MaxProfit=0, Years, MO,RF=555, iRF=555, PF=555, Sharp=555;  
   short LossesCnt=0, WinCnt=0;       
   double MinDepo=InitDeposit; 
   ArrayInitialize(MaxWin,0);
   Years=float(day/260.0)-(SkipTo-SkipFrom); //Print("days=",day," Years=",Years, " SkipYears=",SkipTo-SkipFrom);
   ushort Trades=0;
   //InitDeposit=TesterStatistics(STAT_INITIAL_DEPOSIT);
   //PF=TesterStatistics(STAT_PROFIT_FACTOR);
   for(int Ord=0; Ord<OrdersHistoryTotal(); Ord++){   // поиск MO, PF, iRF, kDD
      if (OrderSelect(Ord, SELECT_BY_POS, MODE_HISTORY)!=true || OrderMagicNumber()!=EXP[e].Mgc) continue; // выясним текущие бай/селл позы и гарантированную прибыль по ним, закрепленную стопами
      int Order=OrderType();
      if (Order==OP_BUY || Order==OP_SELL){
         Trades++; 
         profit=float((OrderProfit()+OrderSwap()+OrderCommission())/MarketInfo(Symbol(),MODE_TICKVALUE));///MarketInfo(Symbol(),MODE_TICKVALUE); //Print(Symbol(),": Pips profit=",profit," OrderProfit()=",OrderProfit()," OrderSwap()=",OrderSwap()," OrderCommission()=",OrderCommission()," TICKVALUE=",MarketInfo(Symbol(),MODE_TICKVALUE));
         FullProfit+=profit; // Значение депо после очередной сделки
         if (profit>MaxWin[0]){ // ищем пять самых крупных выигрышей, чтобы вычесть их потом из профита, т.к. уверены, что они не повторятся 
            for (uchar i=4; i>0; i--) MaxWin[i]=MaxWin[i-1];
            MaxWin[0]=profit;  // т.е. резы тестера будут отличаться в худшую сторону
            } //if (EXP[e].Mgc==788659840) Print(DTIME(OrderCloseTime()),": profit=",profit," FullProfit=",FullProfit," Magic=",OrderMagicNumber()," ",EXP[e].Mgc);
         if (profit>0) {GrossProfit+=profit; WinCnt++;}
         if (profit<0) {GrossLoss-=profit;   LossesCnt++;}
         if (FullProfit>=MaxProfit) MaxProfit=FullProfit;// подсчет iRF - прибыль делим на среднюю просадку
         else  iDD+=MaxProfit-FullProfit;// нахождение в очередной просадке.   площадь просадочной части эквити в период просадки (подсчет по сделкам)      
      }  }     
   if (Trades<1 || day<1) return(0);
   if (WinCnt>0)    MidWin=GrossProfit/WinCnt;   else MidWin=0;
   if (LossesCnt>0) MidLoss=GrossLoss/LossesCnt; else MidLoss=float(0.01);
   EXP[0].LastTestDD=short(MaxEquity-Equity); // последняя незакрытая просадка на тесте
   for (uchar i=1; i<5; i++) MaxWin[0]+=MaxWin[i]; // суммируем все члены массива в первый член
   FullProfit-=MaxWin[0]; //Print("MaxWin=",MaxWin[0]," FullProfit=",FullProfit);// вычитаем из полного профита пять максимальных винов 
   GrossProfit-=MaxWin[0];
   MaxProfit-=MaxWin[0];
   MO=float(FullProfit/Trades); // МатОжидание или Наклон Эквити     
   if (iDD>0) iRF=float(MaxProfit/iDD*100); //  Своя формула для фактора восстановления 
   iDD=iDD/Trades*10;
   for(int Ord=0; Ord<OrdersHistoryTotal(); Ord++){   // поиск MO, PF, iRF, kDD
      if (OrderSelect(Ord, SELECT_BY_POS, MODE_HISTORY)==true && OrderMagicNumber()==EXP[e].Mgc){ // выясним текущие бай/селл позы и гарантированную прибыль по ним, закрепленную стопами
         int Order=OrderType();
         if (Order==OP_BUY || Order==OP_SELL){
            profit=float((OrderProfit()+OrderSwap()+OrderCommission())/MarketInfo(Symbol(),MODE_TICKVALUE));
            SD+=MathAbs(MO-profit); // Суммарное отклонение
      }  }  } 
   SD/=Trades; // Отклонение результата сделки от MO
   MO/=(float)MarketInfo(Symbol(),MODE_SPREAD);
   if (GrossLoss>0)  PF=float(GrossProfit/GrossLoss);  
   if (DrawDown>0)   RF=float(MaxProfit/Years/DrawDown); // Фактор восстановления (% в год!)
   if (SD>0)  Sharp=float(MO*1000/SD); // Своя формула для к.Шарпа 
   switch(CustMax){// Критерий оптимизации
      default: CustomMax=FullProfit; break;
      case 1:  CustomMax=RF;         break;
      case 2:  CustomMax=iRF;        break;
      case 3:  CustomMax=Sharp;      break;
      }
   string FileName="";
   if (IsOptimization()){ // Оптимизация / РеОптимизация
      if (BackTest==0) FileName="Opt"; else FileName="ReOpt";
      FileName=FileName+"_"+Symbol()+DoubleToStr(Period(),0);
      if (PF<PF_ && PF_>0) return (CustomMax); //return(PF/PF_*CustomMax);  // если при оптимизации резы не катят, 
      if (RF<RF_ && RF_>0) return (CustomMax); //return(RF/RF_*CustomMax);  // не пишем их в файл отчета
      if (MO<MO_ && MO_>0) return (CustomMax); //return(MO/cMO*CustomMax);  // и пропорционально уменьшаем критерий оптимизации
      if (Trades/Years<Opt_Trades)  return(CustomMax);                                                     
      }
   else  {if (BackTest==0) FileName="Test"; else FileName="Back";} // тест / бэктест
//// формируем файл со статистикой текущей оптимизации    
   FileName=FileName+"_"+ NAME+".csv"; 
   Str1="Pip/Y";           Prm1=S0(FullProfit/Years); // Профит пункты / год 
   Str2="Trd/Y";           Prm2=S0(Trades/Years); 
   Str3="RF=MaxPrf/Y/DD";  Prm3=S2(RF);    // Фактор восстановления = профит в месяц / просадку 
   Str4="PF";              Prm4=S2(PF);    // Профит фактор
   Str5="DD/LastDD";       Prm5=" "+S0(DrawDown)+"_"+S0(EXP[0].LastTestDD);  // Максимальная историческая просадка / последняя незакрытая просадка
   Str6="iDD";             Prm6=S0(iDD);   // Средняя площадь всех просадок
   Str7="MO/Spred";        Prm7=S2(MO);    // Мат Ожидание
   Str8="SD";              Prm8=S0(SD);    // Стандартное отклонение SD
   Str9="MO/SD";           Prm9=S1(Sharp); // 
   Str10="iRF=MaxPrf/iDD"; Prm10=S0(iRF);  // Модиф. фактора восстановления
   Str11="W/L*W%";         Prm11=" "+S1(MidWin/MidLoss)+"*"+S0(WinCnt*100/Trades)+" ="; // (Средний профит / Средний лосс ) * процент выигрышных сделок = ...Робастность(см. ниже)
   Str12="  = ";           Prm12=S0(MidWin/MidLoss*WinCnt*100/Trades); //    DoubleToStr(MidWin/MidLoss*(WinCnt/Trades)*100,0);  // Робастность =  (Средний профит / Средний лосс ) * процент выигрышных сделок либо  FullProfit*260*1000/day/MaxDD/Trades  
   Str13="RISK=PF*RF";     Prm13=S1(PF*RF);// выравнивает просадки в портфеле  // старый R I S K = 50*day/MaxDD/Trades
   if (DayTime[day]<DayTime[day-1]) day--; // данные последнего дня не всегда корректны 
   TESTER_FILE_CREATE(e,FileName); // создание файла отчета со всеми характеристиками  //
   //Print(EXP[e].Mgc, ": FullProfit=",S0(FullProfit)," RF=",S1(RF)," PF=",S1(PF)," DD/LastDD=",Prm5, " Trades=",Trades);  
   for (short i=0; i<day; i++){ // допишем в конец каждой строки еженедельные балансы  
      FileSeek (TesterFile,-2,SEEK_END); // перемещаемся в конец строки
      FileWrite(TesterFile, "",DayBal[i]/MarketInfo(Symbol(),MODE_TICKVALUE));    // пишем ежедневные Эквити из созданного массива
      }
   FileClose(TesterFile); 
   if (BackTest>0) MATLAB_LOG();
   return (CustomMax); // возвращаем критерий оптимизации   
   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ    
short LastYear, day;
int      DayBal[10000];
datetime DayTime[10000];
void DAY_STATISTIC(){ // расчет параметров DD, Trades, массив с резами сделок // ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
   if (Today!=DayOfYear()){ // начался новый день
      Today=DayOfYear(); //Print("DayMinEquity=",DayMinEquity," DayOfYear()=",DayOfYear());
      DayTime[day]=TimeCurrent();
      DayBal[day]=int((DayMinEquity-InitDeposit)); // сперва умножим на 1000, а в OnTester() разделим. Это для более точного отображения на графике.    
      day++;
      DayMinEquity=float(AccountEquity());
      }
   if (AccountEquity()<DayMinEquity) DayMinEquity=float(AccountEquity());
   // вычисление DD
   double tickVal = MarketInfo(Symbol(),MODE_TICKVALUE);
   if (tickVal <= 0) tickVal = 1.0;
   Equity=float(AccountEquity()/tickVal); 
   if (Equity>=MaxEquity) MaxEquity=Equity;  // Новый максимум депо
   else{ 
      if (MaxEquity-Equity>DrawDown) DrawDown=MaxEquity-Equity;
   }  } 
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
void READ_EXPERT_VARIABLES_FROM_FILE(uchar e){ // Восстановление на реале глобальных переменных // ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
   if (!Real) return;
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   datetime StartWaiting=TimeLocal();
   int File=-1;  
   string FileName=Company+"_"+AccountCurrency()+"_"+DoubleToStr(EXP[e].Mgc,0)+".csv";
   while (File<0){ // ждем, пока не откроется, т.к. без этих данных торговлю лучше не начинать
      File=FileOpen(FileName, FILE_READ | FILE_WRITE);  
      if (File<0) {Sleep(100); ResetLastError();}
      if (TimeLocal()-StartWaiting>2){
         if (!IsTesting() && !IsOptimization()) 
         MessageBox(__FUNCTION__+" Can't open file "+FileName);
         ERROR_CHECK(__FUNCTION__+" Can't open file "+FileName); 
         StartWaiting=TimeLocal();
      }  }
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   if (FileReadString(File)==""){ // файл только что создан, заполним
      BarTime=Time[bar+1];  EXP[e].ExpMemory=0;
      FileWrite(File,"BarTime", "mem.BUY",   "BUY.Stp",  "BUY.Prf",  "BUY.Exp",   "mem.SEL",   "SEL.Stp",  "SEL.Prf",  "SEL.Exp",  "ExpMemory"); // ниже заголовок для глобальных переменных
      FileWrite(File, BarTime ,  EXP[e].mem.BUY.Val, EXP[e].mem.BUY.Stp, EXP[e].mem.BUY.Prf, EXP[e].mem.BUY.Exp,  EXP[e].mem.SEL.Val, EXP[e].mem.SEL.Stp, EXP[e].mem.SEL.Prf, EXP[e].mem.SEL.Exp, EXP[e].ExpMemory); // сохраняем глобальные переменные в файл
      FileWrite(File,"Expert History");
      Alert("Create file ",FileName," to save expert params"); 
      }
   else{ // чтение переменных из файла
      FileSeek(File,0,SEEK_SET);     // перемещаемся в начало   
      FileReadString(File); while (!FileIsLineEnding(File)) FileReadString(File); // читаем заголовок
      BarTime                 =StringToTime(FileReadString(File));  // Преобразование строки, содержащей время в формате "yyyy.mm.dd [hh:mi]", в число типа datetime.  
      EXP[e].mem.BUY.Val =float(StrToDouble(FileReadString(File))); 
      EXP[e].mem.BUY.Stp =float(StrToDouble(FileReadString(File)));
      EXP[e].mem.BUY.Prf =float(StrToDouble(FileReadString(File)));
      EXP[e].mem.BUY.Exp =StringToTime(FileReadString(File));
      EXP[e].mem.SEL.Val =float(StrToDouble(FileReadString(File)));
      EXP[e].mem.SEL.Stp =float(StrToDouble(FileReadString(File)));
      EXP[e].mem.SEL.Prf =float(StrToDouble(FileReadString(File)));
      EXP[e].mem.SEL.Exp =StringToTime(FileReadString(File));
      EXP[e].ExpMemory   =StringToTime(FileReadString(File));
      Print(__FUNCTION__," ",FileName," BarTime=",BarTime," BUY.Val=",EXP[e].mem.BUY.Val," BUY.Stp=",EXP[e].mem.BUY.Stp," BUY.Prf=",EXP[e].mem.BUY.Prf," BUY.Exp=",EXP[e].mem.BUY.Exp," SEL.Val=",EXP[e].mem.SEL.Val," SEL.Stp=",EXP[e].mem.SEL.Stp," SEL.Prf=",EXP[e].mem.SEL.Prf," SEL.Exp=",EXP[e].mem.SEL.Exp," ExpMemory=",EXP[e].ExpMemory);
      ResetLastError(); // после ф. StringToTime появляется ошибка, т.к. Exel переворачивает дату. Тем не менее дата считывается корректно
      }
   FileClose(File);
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   }  
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
void REPORT(string Missage){REPORT(CurExp, Missage);}
void REPORT(uchar e, string Missage){  // собираем все сообщения экспертов в одну кучу 
   //if (!Real)        return;  // в этой функции нельзя вызывать ERROR_CHECK(), т.к. она сама вызывается в ERROR_CHECK и при возникновении повторной ошибки происходит переполнение стека
   if (Missage=="")  return;
   if (EXP[e].Hist=="")  EXP[e].Hist=Missage;
   else                       EXP[e].Hist=EXP[e].Hist+"\n "+Missage; // без разделителя ";" при записи в RestoreFileName (MailSender()) все сообщения лепятся в одну строку.
   Print(EXP[e].Mgc,":: ",Missage);
   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
void SAVE_HISTORY(){ // пишем собранные сообщения в один общий файл   
   Print("SAVE_HISTORY: ChartHistory=",ChartHistory);
   if (ChartHistory=="") return; 
   WAITING(EXP[CurExp].Mgc,ReportFile,60);// ожидание освобождения общего фала со всеми репортами
   int File=FileOpen(ReportFile, FILE_READ | FILE_WRITE);
   if (File>0){
      FileSeek (File,0,SEEK_END);     // перемещаемся в конец
      FileWrite(File, ChartHistory);
      FileClose(File);
      ChartHistory="";
      }
   else ERROR_CHECK(__FUNCTION__+" Can't open file "+ReportFile+"!!!");  
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   FREE(EXP[CurExp].Mgc,ReportFile);   
   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ    
void SAVE_ALL_EXPERTS_VARIABLES_TO_FILE(){// Сохранение глобальных переменных в файл, доклад о последних сделках  ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ  
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   for (uchar e=0; e<ExpTotal; e++){    
      if (EXP[e].Name!=NAME || EXP[e].Sym!=Symbol() || EXP[e].Per!=Period() || EXP[e].Rsk==0) continue; // имя+ТФ+период  совпадают, выбали эксперта с того же чарта
      ushort Trades=0;
      datetime OrdMemory=0;
      string ExpParams="";
      float MaxBal=0, DD=0, PF=555, RF=555, Plus=0, Minus=0, TradePrf=0, Profit=0, CheckRisk=0;
      for (int Ord=0; Ord<OrdersHistoryTotal(); Ord++){// перебераем историю сделок эксперта
         if (OrderSelect(Ord,SELECT_BY_POS,MODE_HISTORY)==true && OrderMagicNumber()==EXP[e].Mgc && OrderCloseTime()>0 && OrderLots()>0){
            TradePrf=float(OrderProfit()+OrderSwap()+OrderCommission()); // прибыль от выбранного ордера в валюте депозита 
            if (TradePrf==0) continue; 
            Trades++;
            Profit +=TradePrf; 
            if (TradePrf>0)  Plus+=TradePrf;  else  Minus-=TradePrf;
            if (Profit>MaxBal) MaxBal=Profit;
            else if (MaxBal-Profit>DD) DD=MaxBal-Profit;
            OrdMemory=OrderCloseTime();  
         }  }    
      ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
      if (OrdMemory>0 && OrdMemory!=EXP[e].ExpMemory){// если время последней сделки обновилось,
         Print(__FUNCTION__,": NewTrade: Magic=",EXP[e].Mgc," TradePrf=",TradePrf," OrdMemory=",OrdMemory," ExpMemory=",EXP[e].ExpMemory); 
         EXP[e].ExpMemory=OrdMemory; // Print("Update "+"Mem"+S0(Magic)+":",GlobalVariableGet("Mem"+S0(Magic)));
         if (DD>0) RF=MaxBal/DD;  // фактор восстановления
         float Stop=100*float(Point); // возьмем любой стоп для расчета риска
         Lot = MM(Stop,e);   // расчет пробного лота для стопа в 100п
         CheckRisk=CHECK_RISK(Lot,Stop,EXP[e].Sym); //расчет текущего риска в связи с просадкой
         //string CurrentRisk; // запишем, на сколько истинный риск (с учетом просадки) отличается от заданного в настройках 
         //if (CheckRisk>EXP[e].Risk) CurrentRisk="+"+S1(CheckRisk-EXP[e].Risk);
         //if (CheckRisk<EXP[e].Risk) CurrentRisk=    S1(CheckRisk-EXP[e].Risk);
         if ( Minus>0)  PF= Plus/ Minus;
         if (TradePrf>0) ExpParams="\n WIN="; else ExpParams="\n LOSS="; // запомним значение баланса на случай, если этот лось для данного эксперта - начало ДД (пригодится потом в ММ)
         ExpParams=ExpParams+S1(TradePrf*100/AccountBalance())+"% "+
            "\r Prf="+S0(Profit)+"$ Risk="+S1(EXP[e].Rsk)+" CheckRisk="+S1(CheckRisk)+ // 
            "\r RF="+S1(RF)+" PF="+S1(PF)+" Trades="+ S0(Trades)+    // 
            "\n Hist/CurDD="+S0(EXP[e].HistDD)+"/"+S0(CUR_DD(e))+"pips";    //
         REPORT(e,ExpParams); // шлем миссагу
         }  
      // Сохранение глобальных переменных на случай выключения программы   
      string FileName=Company+"_"+AccountCurrency()+"_"+S0(EXP[e].Mgc)+".csv";
      ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
      int File=FileOpen(FileName, FILE_READ|FILE_WRITE);  
      if (File<0){
         ERROR_CHECK(__FUNCTION__+" Can't open file "+FileName+"!!!");  
         continue;}
      FileReadString(File); while (!FileIsLineEnding(File)) FileReadString(File); // читаем строку с заголовком
      //Print(__FUNCTION__," wite to file ",FileName," ",EXP[e].Bar, EXP[e].mem.BUY.Val, EXP[e].mem.BUY.Stp, EXP[e].mem.BUY.Prf ,EXP[e].mem.BUY.Exp, EXP[e].mem.SEL.Val, EXP[e].mem.SEL.Stp, EXP[e].mem.SEL.Prf, EXP[e].mem.SEL.Exp, EXP[e].ExpMemory); 
      FileWrite (File, EXP[e].Bar, EXP[e].mem.BUY.Val, EXP[e].mem.BUY.Stp, EXP[e].mem.BUY.Prf ,EXP[e].mem.BUY.Exp, EXP[e].mem.SEL.Val, EXP[e].mem.SEL.Stp, EXP[e].mem.SEL.Prf, EXP[e].mem.SEL.Exp, EXP[e].ExpMemory); // сохраняем переменные эксперта в файл
      if (EXP[e].Hist!=""){
         FileSeek (File,0,SEEK_END); 
         FileWrite (File, TIME(TimeCurrent())+";"+EXP[e].Hist); 
         ChartHistory+="\n  "+S0(EXP[e].Mgc)+": "+EXP[e].Hist;
         //Print("IndividualSaving: EXP[",e,"].Hist=",EXP[e].Hist);
         EXP[e].Hist="";
         }
      FileClose(File); 
      }   
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));  
   }   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
void MAIL_SEND(){ // отправляем мыло из файла Reports.csv с отчетами
   if (IsTesting() || IsOptimization()) return;
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   while (TimeLocal()-GlobalVariableTime("GlobalOrdersSet")<60) Sleep(ExpPause); // ждем, пока после последнего обращения к глобалу пройдет больше минуты, т.е. все отчитались
   WAITING(EXP[CurExp].Mgc,"Mail",120);
   if (!GlobalVariableCheck("MailTime")) GlobalVariableSet("MailTime",TimeCurrent()-4000); // при первом запуске эксперта время поиска сделок для отчета чуть больше часа
   if (GlobalVariableGet("MailTime")<TimeCurrent()-4000) GlobalVariableSet("MailTime",TimeCurrent()-4000); // если давно не обновлялось, тоже освежим
   if (TimeHour(datetime(GlobalVariableGet("MailTime")))==TimeHour(TimeCurrent())){// за этот час мыло уже отправлено 
      //Print(Magic,": Mail already sent"); 
      FREE(EXP[CurExp].Mgc,"Mail"); 
      return;}   
   float MaxBal=0, MinBal=0, AccDD=0, AccCDD=0, AccPF=555, Plus=0, Minus=0, AccRF=555, AccPrf=0,  profit=0, Roll=0, LastHourProfit=0;
   int  Trades=0;  
   for(int i=0; i<OrdersHistoryTotal(); i++){// перебераем историю сделок эксперта
      if (OrderSelect(i,SELECT_BY_POS,MODE_HISTORY)==false) continue; // история всех экспертов
      profit=float(OrderProfit()+OrderSwap()+OrderCommission()); // прибыль от выбранного ордера в валюте депозита 
      if (profit==0) continue;
      if (OrderType()==6 && iTime(NULL,60,0)-OrderOpenTime()<3300)   Roll+=profit;// 6-ролловер, т.е. инвестиции. За прошлый час с небольшим запасом в 55мин = 3300с 
      if (OrderOpenPrice()>0){ // ордер открыт экспертом
         Trades++;   // подсчет показателей работы эксперта
         AccPrf+=profit; 
         if (profit>0) Plus+=profit; else Minus-=profit;
         if (AccPrf>MaxBal) {MaxBal=AccPrf; MinBal=MaxBal;}
         if (AccPrf<MinBal) {MinBal=AccPrf; if (MaxBal-MinBal>AccDD) AccDD=MaxBal-MinBal;}   // DD
         if (OrderCloseTime()>GlobalVariableGet("MailTime")) LastHourProfit+=profit; // суммируем всю прибыль за последний час
      }  }       
   // Суммарный риск открытых позиций и отложенных ордеров
   double OpenOrdMargNeed=0, LongRisk=0, ShortRisk=0, MargNeed=0, PerCent=0;
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   for (int i=0; i<OrdersTotal(); i++){// перебераем все открытые и отложенные ордера всех экспертов счета Ролловеры (OrderType=6) туда не пишем.
      if (OrderSelect(i, SELECT_BY_POS, MODE_TRADES)==false) continue;
      if (OrderType()==6) continue; // ролловеры не нужны
      if (OrderType()<2)   OpenOrdMargNeed+=float(OrderLots()*MarketInfo(OrderSymbol(),MODE_MARGINREQUIRED)); // кол-во маржи, необходимой для открытия лотов
      else                 MargNeed       +=float(OrderLots()*MarketInfo(OrderSymbol(),MODE_MARGINREQUIRED));//маржа отложников
      if (OrderType()==0 || OrderType()==2 || OrderType()==4)  LongRisk +=CHECK_RISK(float(OrderLots()), float(MathAbs(OrderOpenPrice()-OrderStopLoss())), OrderSymbol());
      if (OrderType()==1 || OrderType()==3 || OrderType()==5)  ShortRisk+=CHECK_RISK(float(OrderLots()), float(MathAbs(OrderOpenPrice()-OrderStopLoss())), OrderSymbol());   
      }    // теперь массив ORD содержит список всех открытых, отложенных и предстоящих установке ордеров   
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   AccCDD=MaxBal-AccPrf;
   if (AccDD>0) AccRF=AccPrf/AccDD;
   if (Minus>0) AccPF=Plus/Minus;
   string AccountParams= "\n"+//"\nAccountParams:"+
   "\n  RISK: Long+Short = "+S1(LongRisk)+"%+"+S1(ShortRisk)+"%"+
   "\n  MARGIN: Open+Depend="+S0(OpenOrdMargNeed/AccountFreeMargin()*100)+"%+"+S0(MargNeed/AccountFreeMargin()*100)+"%"+
   "\n  EQUITY="+S0(AccountEquity())+" FreeMargin="+S0(AccountFreeMargin())+
   "\n  MarketInfo "+Symbol()+":"+
   "\nMaxSpred="+S4(MaxSpred)+
   "\nSwap/StpLev = "+S4(MarketInfo(Symbol(),MODE_SWAPLONG)+MarketInfo(Symbol(),MODE_SWAPSHORT)) + "/" + S4(MarketInfo(Symbol(),MODE_STOPLEVEL));   
   string CurPrf, Agr="";
   if (Aggress>1) Agr="x"+S0(Aggress);
   if (AccountProfit()>0) CurPrf="+"+S1(AccountProfit()*100/AccountBalance())+"%"; // текущая незакрытая прибыль в процентах
   if (AccountProfit()<0) CurPrf=    S1(AccountProfit()*100/AccountBalance())+"%";
   CurPrf=AccountCurrency()+Agr+"  "+MONEY2STR(AccountBalance())+CurPrf;
   string Warning, MailText;
   if (Roll!=0){// были роловеры
      CurPrf=CurPrf+" Roll="+MONEY2STR(Roll);
      MailText=MailText+"\n"+"Roll="+S0(Roll)+AccountCurrency(); 
      }
   if (BarTime!=Time[1]) // проверка пропущенных баров: разница с прошлым баром (в барах)   
      REPORT("Missed Bars!  LastOnLine="+DTIME(BarTime)+",  CurTime="+DTIME(Time[0]));   
   if (LastHourProfit>0){
      PerCent=LastHourProfit/((float)AccountBalance()-LastHourProfit)*100;
      CurPrf=CurPrf+" Win="+S2(PerCent)+"%";
      }
   if (LastHourProfit<0){
      PerCent=LastHourProfit/((float)AccountBalance()+LastHourProfit)*100;
      CurPrf=CurPrf+" Loss="+S2(PerCent)+"%"; //
      }
   // открытие файла Reports.csv
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));  
   WAITING(EXP[CurExp].Mgc,ReportFile,30);// ожидание освобождения общего фала со всеми репортами
   int File=FileOpen(ReportFile, FILE_READ | FILE_WRITE);  
   if (File>0){   
      while (!FileIsEnding(File)) MailText=MailText+"\n"+ FileReadString(File); // пихаем все в мыло 
      FileClose(File); 
      FileDelete(ReportFile);
      }  
   else ResetLastError(); 
   FREE(EXP[CurExp].Mgc,ReportFile);  
   if (StringLen(MailText)>0 && StringFind(MailText,"!",0)>0) Warning="WARNING"; 
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   SendMail(CurPrf, ORDERS_INF(Warning) + MailText + AccountParams); 
   GlobalVariableSet("MailTime",TimeCurrent()); // время отправки "мыла" 
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   MATLAB_LOG();
   FREE(EXP[CurExp].Mgc,"Mail"); 
   Print(EXP[CurExp].Mgc,":      *   S E N D   M A I L   * ",MailText,"\n");
   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ    
string MONEY2STR(double Balance){
   if (MathAbs(Balance)<1000)       return(S1(Balance));
   if (MathAbs(Balance)<10000)      return(S2(Balance/1000)+"K");  
   if (MathAbs(Balance)<1000000)    return(S1(Balance/1000)+"K"); 
   if (MathAbs(Balance)<10000000)   return(S2(Balance/1000000)+"M"); 
   return (S1(Balance/1000000)+"M"); 
   } 
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ    
string ORDERS_INF(string Warning){ // инфа о текущих рыночных характеристиках и профите 
   string MarketOrders=TIME(TimeCurrent())+" "+Company+" "+Warning;
   if (OrdersTotal()==0) return (MarketOrders);
   for(int Ord=0; Ord<OrdersTotal(); Ord++){// проверка отложенных ордеров 
      if (OrderSelect(Ord, SELECT_BY_POS, MODE_TRADES)!=true) continue;
      if (OrderType()==6) continue;
      float POINT =(float)MarketInfo(OrderSymbol(),MODE_POINT); 
      MARKET_UPDATE(OrderSymbol());
      float TakeProfit=(float)OrderTakeProfit();
      if (OrderTakeProfit()==0) TakeProfit=(float)OrderOpenPrice();
      if (OrderType()==OP_BUYSTOP)  {MarketOrders =MarketOrders+"\n"+S0(OrderMagicNumber())+": BS/"  +S4(OrderOpenPrice())+               "/"+S0((OrderStopLoss()-OrderOpenPrice())/POINT/10)+"/"+S0((TakeProfit-OrderOpenPrice())/POINT/10)+"x"+DoubleToStr(OrderLots(),2)+"="+S1(CHECK_RISK((float)OrderLots(),float(OrderStopLoss()-OrderOpenPrice()),OrderSymbol()))+"%";}
      if (OrderType()==OP_SELLSTOP) {MarketOrders =MarketOrders+"\n"+S0(OrderMagicNumber())+": SS/"  +S4(OrderOpenPrice())+               "/"+S0((OrderOpenPrice()-OrderStopLoss())/POINT/10)+"/"+S0((OrderOpenPrice()-TakeProfit)/POINT/10)+"x"+DoubleToStr(OrderLots(),2)+"="+S1(CHECK_RISK((float)OrderLots(),float(OrderOpenPrice()-OrderStopLoss()),OrderSymbol()))+"%";} 
      if (OrderType()==OP_BUYLIMIT) {MarketOrders =MarketOrders+"\n"+S0(OrderMagicNumber())+": BL/"  +S4(OrderOpenPrice())+               "/"+S0((OrderStopLoss()-OrderOpenPrice())/POINT/10)+"/"+S0((TakeProfit-OrderOpenPrice())/POINT/10)+"x"+DoubleToStr(OrderLots(),2)+"="+S1(CHECK_RISK((float)OrderLots(),float(OrderStopLoss()-OrderOpenPrice()),OrderSymbol()))+"%";}
      if (OrderType()==OP_SELLLIMIT){MarketOrders =MarketOrders+"\n"+S0(OrderMagicNumber())+": SL/"  +S4(OrderOpenPrice())+               "/"+S0((OrderOpenPrice()-OrderStopLoss())/POINT/10)+"/"+S0((OrderOpenPrice()-TakeProfit)/POINT/10)+"x"+DoubleToStr(OrderLots(),2)+"="+S1(CHECK_RISK((float)OrderLots(),float(OrderOpenPrice()-OrderStopLoss()),OrderSymbol()))+"%";}  
      if (OrderType()==OP_BUY)      {MarketOrders =MarketOrders+"\n"+S0(OrderMagicNumber())+": BUY/" +S0((BID-OrderOpenPrice())/POINT/10)+"/"+S0((OrderStopLoss()-OrderOpenPrice())/POINT/10)+"/"+S0((TakeProfit-OrderOpenPrice())/POINT/10)+"x"+DoubleToStr(OrderLots(),2)+"="+S1(CHECK_RISK((float)OrderLots(),float(OrderStopLoss()-OrderOpenPrice()),OrderSymbol()))+"%";}   // профит в пунктах / закрепленный стопом профит в пунктах х лот    
      if (OrderType()==OP_SELL)     {MarketOrders =MarketOrders+"\n"+S0(OrderMagicNumber())+": SELL/"+S0((OrderOpenPrice()-ASK)/POINT/10)+"/"+S0((OrderOpenPrice()-OrderStopLoss())/POINT/10)+"/"+S0((OrderOpenPrice()-TakeProfit)/POINT/10)+"x"+DoubleToStr(OrderLots(),2)+"="+S1(CHECK_RISK((float)OrderLots(),float(OrderOpenPrice()-OrderStopLoss()),OrderSymbol()))+"%";}   // профит в пунктах / закрепленный стопом профит в пунктах х лот 
      }   
   return (MarketOrders);
   } 
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ    
#define  MAX_TRADES  10000    // максимальное кол-во глубины проверяемых сделок
void MATLAB_LOG (){// Сохранение истории сделок в файл 
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   int      Prt[MAX_TRADES];  ArrayInitialize(Prt,0);
   datetime Tme[MAX_TRADES];  ArrayInitialize(Tme,0);
   int      Mgc[MAX_TRADES];  ArrayInitialize(Mgc,0);
   string FileName="MatLabTest.csv"; 
   if (Real){ 
      FileName="MatLab"+AccountCurrency()+".csv";
      if (FileIsExist(FileName))  if (!FileDelete(FileName)) ERROR_CHECK("MATLAB_LOG_Delete "+FileName);
      }    
   int File=FileOpen(FileName, FILE_READ | FILE_WRITE); 
   if (File<0){
      ERROR_CHECK(__FUNCTION__+" Can't open file "+FileName+"!!!");
      return;}
   ushort cnt=0; // max=65535
   int StartCount=0;
   if (OrdersHistoryTotal()>=MAX_TRADES) StartCount=OrdersHistoryTotal()-MAX_TRADES+1;
   for(int i=StartCount; i<OrdersHistoryTotal(); i++){// копируем историю сделок эксперта один раз для сокращения обращений к серверу 
      if (OrderSelect(i, SELECT_BY_POS,MODE_HISTORY)==false || OrderMagicNumber()==0 || OrderProfit()==0 || OrderCloseTime()==0 || OrderLots()==0 || MarketInfo(OrderSymbol(),MODE_TICKVALUE)==0) continue; // 
      Prt[cnt]=int((OrderProfit()+OrderSwap()+OrderCommission())/OrderLots()/MarketInfo(OrderSymbol(),MODE_TICKVALUE));
      Tme[cnt]=OrderCloseTime();
      Mgc[cnt]=OrderMagicNumber();
      cnt++; if (cnt>=MAX_TRADES) break;
      }
   FileWrite(File, "Magic","TickVal","Risk","Deal/Time..."); // прописываем в первую строку названия столбцов
   for (uchar e=0; e<ExpTotal; e++){
      FileSeek (File,0,SEEK_END); // перемещаемся в конец файла MatLabTest.csv
      FileWrite(File, S0(EXP[e].Mgc)+";"+DoubleToString(MarketInfo(EXP[e].Sym,MODE_TICKVALUE),int(MarketInfo(EXP[e].Sym,MODE_DIGITS)))+";"+S1(EXP[e].Rsk)); // прописываем в первую ячейку magic,  
      for(int i=0; i<cnt; i++){// перебераем созданный массив истории сделок всех экспертов
         if (Mgc[i]!=EXP[e].Mgc) continue; // сделка другого эксперта
         FileSeek (File,-2,SEEK_END); // потом дописываем
         FileWrite(File,  ""    , S0(Prt[i])+"/"+DTIME(Tme[i]));    // ежедневные профиты/время сделки из созданного массива    
      }  }
   FileClose(File);
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__)); 
   }  
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
void EXPERT_PARENT_CLASS::CHECK_VARIABLES(){  // сравнение значений индикаторов Real/Test
   string   FileName=Company+"_Check_"+NAME+"_"+S0(Mgc)+".csv",
            OHlC=S5(Open[0])+" | "+S5(High[1])+" | "+S5(Low[1])+" | "+S5(Close[1]),  
            AskBid=S5(Ask)+" | "+S5(Bid), buy, sel;
   if (BUY.Val>0)       buy=S4(BUY.Val)+" | "+S4(BUY.Stp)+" | "+S4(BUY.Prf);
   if (set.BUY.Val>0)   buy+=" set"+S4(set.BUY.Val)+" | "+S4(set.BUY.Stp)+" | "+S4(set.BUY.Prf); // открытие лонга
   if (SEL.Val>0)       sel=S4(SEL.Val)+" | "+S4(SEL.Stp)+" | "+S4(SEL.Prf);
   if (set.SEL.Val>0)   sel+=" set"+S4(set.SEL.Val)+" | "+S4(set.SEL.Stp)+" | "+S4(set.SEL.Prf); 
   
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   int File=FileOpen(FileName, FILE_READ|FILE_WRITE); 
   if (File<0){
      ERROR_CHECK(__FUNCTION__+" Can't open file "+FileName+"!!!");  
      return;} 
   if (FileReadString(File)=="")// пропишем заголовки столбцов   
      FileWrite (File,"OHLC","ask bid",  "Spread"  ,  "atr"  ,  "ATR"  ,  "HI"   ,  "LO"   ,"BUY","SELL","ServerTime","TrUp","TrDn","InUp","InDn","OutUp","OutDn","Tr0","Tr1","Tr2","Tr3","In0","In1","In2","In3","Out0","Out1","Out2","Out3"); // сохраняем переменные в файл
   FileSeek(File,0,SEEK_END);     // перемещаемся в конец
   FileWrite    (File, OHlC ,  AskBid ,S5(MaxSpred),S5(ch[6]),S5(ch[7]),S5(ch[8]),S5(ch[9]), buy , sel  , BTIME(bar) , ch[0], ch[1], ch[2], ch[3], ch[4] , ch[5] ,PS[0],PS[1],PS[2],PS[3],PS[4],PS[5],PS[6],PS[7], PS[8], PS[9],PS[10],PS[11]);
   FileClose(File); 
   ArrayInitialize (PS,0); // обнулим значения массива перед следующим запуском  
   ERROR_CHECK(__FUNCTION__+"-"+S0(__LINE__));
   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ    

