#ifndef SOSIMPLE_MQL5_ERRORS_MQH
#define SOSIMPLE_MQL5_ERRORS_MQH

void REPORT(string Missage);
void REPORT(uchar e, string Missage);
bool CONNECT(uchar ExpNum);
bool BUSY(uchar ExpNum);
void ERROR_LOG(string ErrTxt, uchar ExpNum);

bool ERROR_CHECK(string ErrTxt){ return( ERROR_CHECK(ErrTxt,CurExp));}
bool ERROR_CHECK(string ErrTxt, uchar ExpNum){ // Проверка проведения операций с ордерами. Возвращает необходимость повтора торговой операции
   int err=GetLastError(); //
   if (err==0) return(false); // Ошибок нет. Повтор не нужен
   if (err==ERR_NOT_ENOUGH_MONEY && !Real) return(false); // при оптимизации оч много таких ошибок ))
   if (err==4200) return(false); // "object already exist"
   ErrTxt=ErrTxt+": "+ErrorDescription(err)+"! ERROR-"+S0(err);
   REPORT(ErrTxt); //
   ERROR_LOG(ErrTxt,ExpNum); // фиксируем ошибки в файл с указанием типа ордера, при котором она возникла 
   switch (err){   
      case 1:                    return(false); // Expert пытается изменить уже установленные значения такими же значениями. Необходимо изменить одно или несколько значений и повторить попытку.
      case 2:                    return(false); // Общая ошибка. Прекратить все попытки торговых операций до выяснения обстоятельств. Возможно перезагрузить операционную систему и клиентский терминал. 
      case 3:                    return(false); // В торговую функцию переданы неправильные параметры, например, неправильный символ, неопознанная торговая операция, отрицательное допустимое отклонение цены, несуществующий номер тикета и т.п. Необходимо изменить логику программы.
      case 4:                    return(!BUSY(ExpNum));  // Торговый сервер занят. Можно повторить попытку через достаточно большой промежуток времени (от нескольких минут).
      case 5:                    return(false); // Старая версия клиентского терминала. Необходимо установить последнюю версию клиентского терминала.
      case 6:                    return(CONNECT(ExpNum));   // Нет связи с торговым сервером. Необходимо убедиться, что связь не нарушена (например, при помощи функции IsConnected) и через небольшой промежуток времени (от 5 секунд) повторить попытку.
      case 7:                    return(false); // Недостаточно прав
      case 8:    Sleep(5000);    return(true);  // Слишком частые запросы. Необходимо уменьшить частоту запросов, изменить логику программы.
      case 9:                    return(false); // Недопустимая операция нарушающая функционирование сервера
      case 64:                   return(false); //Счет заблокирован/ Необходимо прекратить все попытки торговых операций.
      case 65:                   return(false); //Неправильный номер счета. Необходимо прекратить все попытки торговых операций
      case 128:  Sleep(5000);    EXP[ExpNum].ORDER_CHECK(); return(true);   // Истек срок ожидания совершения сделки. Прежде, чем производить повторную попытку (не менее, чем через 1 минуту), необходимо убедиться, что торговая операция действительно не прошла (новая позиция не была открыта, либо существующий ордер не был изменён или удалён, либо существующая позиция не была закрыта)
      case 129:  Sleep(5000);    return(true);   // Неправильная цена bid или ask, возможно, ненормализованная цена. Необходимо после задержки от 5 секунд обновить данные при помощи функции RefreshRates и повторить попытку. Если ошибка не исчезает, необходимо прекратить все попытки торговых операций и изменить логику программы. 
      case 130:  Sleep(5000);    return(true);  // Слишком близкие стопы или неправильно рассчитанные или ненормализованные цены в стопах (или в цене открытия отложенного ордера). Попытку можно повторять только в том случае, если ошибка произошла из-за устаревания цены. Необходимо после задержки от 5 секунд обновить данные при помощи функции RefreshRates и повторить попытку. Если ошибка не исчезает, необходимо прекратить все попытки торговых операций и изменить логику программы.  
      case 131:                  return(false); // Неправильный объем, ошибка в грануляции объема. Необходимо прекратить все попытки торговых операций и изменить логику программы.
      case 132:                  return(false); // Рынок закрыт. Можно повторить попытку через достаточно большой промежуток времени (от нескольких минут).
      case 133:                  return(false); // Торговля запрещена. Необходимо прекратить все попытки торговых операций.
      case 134:                  return(false); // Недостаточно денег для совершения операции. Повторять сделку с теми же параметрами нельзя. Попытку можно повторить после задержки от 5 секунд, уменьшив объем, но надо быть уверенным в достаточности средств для совершения операции.
      case 135:                  return(true);  // Цена изменилась. Можно без задержки обновить данные при помощи функции RefreshRates и повторить попытку.
      case 136:  Sleep(5000);    return(true);  // Нет цен. Брокер по какой-то причине (например, в начале сессии цен нет, неподтвержденные цены, быстрый рынок) не дал цен или отказал. Необходимо после задержки от 5 секунд обновить данные при помощи функции RefreshRates и повторить попытку.
      case 137:  Sleep(5000);    return(true);  // Брокер занят
      case 138:                  return(true);  // Запрошенная цена устарела, либо перепутаны bid и ask. Можно без задержки обновить данные при помощи функции RefreshRates и повторить попытку. Если ошибка не исчезает, необходимо прекратить все попытки торговых операций и изменить логику программы.   
      case 139:                  return(false); // Ордер заблокирован и уже обрабатывается. Необходимо прекратить все попытки торговых операций и изменить логику программы.
      case 140:                  return(false); // Разрешена только покупка. Повторять операцию SELL нельзя.
      case 141:  Sleep(5000);    return(true);   // Слишком много запросов. Необходимо уменьшить частоту запросов, изменить логику программы.
      case 142:  Sleep(5000);    EXP[ExpNum].ORDER_CHECK(); return(true); // Ордер поставлен в очередь. Это не ошибка, а один из кодов взаимодействия между клиентским терминалом и торговым сервером. Этот код может быть получен в редком случае, когда во время выполнения торговой операции произошёл обрыв и последующее восстановление связи. Необходимо обрабатывать так же как и ошибку 128.
      case 143:  Sleep(5000);    EXP[ExpNum].ORDER_CHECK(); return(true); // Ордер принят дилером к исполнению. Один из кодов взаимодействия между клиентским терминалом и торговым сервером. Может возникнуть по той же причине, что и код 142. Необходимо обрабатывать так же как и ошибку 128.
      case 144:  Sleep(5000);    EXP[ExpNum].ORDER_CHECK(); return(true); // Ордер аннулирован самим клиентом при ручном подтверждении сделки. Один из кодов взаимодействия между клиентским терминалом и торговым сервером.
      case 145:  Sleep(5000);    return(true);   // Модификация запрещена, так как ордер слишком близок к рынку и заблокирован из-за возможного скорого исполнения. Можно не ранее, чем через 15 секунд, обновить данные при помощи функции RefreshRates и повторить попытку.
      case 146:                  return(!BUSY(ExpNum)); // Подсистема торговли занята. Повторить попытку только после того, как функция IsTradeContextBusy вернет FALSE. 
      case 147:                  return(false); // Использование даты истечения ордера запрещено брокером. Операцию можно повторить только в том случае, если обнулить параметр expiration.
      case 148:                  return(false); // Количество открытых и отложенных ордеров достигло предела, установленного брокером. Новые открытые позиции и отложенные ордера возможны только после закрытия или удаления существующих позиций или ордеров.
      case 149:                  return(false); // Попытка открыть противоположный ордер в случае, если хеджирование запрещено
      case 150:                  return(false); // Попытка закрыть позицию по инструменту в противоречии с правилом FIFO
      case 4000:                 return(true);  // Нет ошибки
      case 4105:                 return(false); // Ни один ордер не выбран 
      case 4106:                 return(false); // Неизвестный символ
      case 4107:                 return(false); // Неправильный параметр цены для торговой функции
      case 4108:                 return(false); // Неверный номер тикета 
      case 4109:                 return(false); // Торговля не разрешена. Необходимо включить опцию "Разрешить советнику торговать" в свойствах эксперта
      case 4110:                 return(false); // Ордера на покупку не разрешены. Необходимо проверить свойства эксперта
      case 4111:                 return(false); // Ордера на продажу не разрешены. Необходимо проверить свойства эксперта
      default: return(false);
   }  } // в этих функциях нелья вызывать ERROR_CHECK:  ERROR_LOG / TESTER_FILE_CREATE / DATA_PROCESSING / DATA / FREE / REPORT т.к. происходит переполнение стека
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
bool CONNECT(uchar ExpNum){ // Проверка связи длится 5 минут, потом решаем что ее нет////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
   FREE(EXP[ExpNum].Mgc,"Terminal"); // освобождение торгового потока на время ожидания
   datetime  StartWaiting=TimeLocal(); 
   while (!IsConnected()){
      Sleep(1000); 
      if (TimeLocal()-StartWaiting>120) {REPORT("Connect Waiting Time > 2 minutes!");  return(false);} // ждали 2 мин, не дождались
      }////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
   return(true); // связь есть
   }  
   
bool BUSY(uchar ExpNum){ // проверяет поток для выполнения торговых операций
   FREE(EXP[ExpNum].Mgc,"Terminal");   // освобождение торгового потока на время ожидания
   datetime  StartWaiting=TimeLocal();   
   while (IsTradeContextBusy()){ // Повторить попытку только после того, как функция IsTradeContextBusy вернет FALSE.
      Sleep(1000);                              
      if (TimeLocal()-StartWaiting>300) {REPORT("ContextBusy Waiting Time > 5 minutes!");  return(true);} // ждали 5 минут, не дождались
      }//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// 
   return(false); // поток не занят
   }   

void ERROR_LOG(string ErrTxt,uchar ExpNum){
   string ErrorFileName="ERROR_"+NAME+"_"+S0(EXP[ExpNum].Mgc)+".csv";
   string SYM=EXP[ExpNum].Sym;
   Str1="ServerTime";            Prm1="-"+TimeToStr(TimeCurrent(),TIME_DATE|TIME_SECONDS);
    Str2="Ask/Bid/StpLev";        Prm2=S5(ASK,SYM)+"/"+S5(BID,SYM)+"/"+S0(MarketInfo(SYM,MODE_STOPLEVEL));
    Str3="Spred";                 Prm3=S5(MarketInfo(SYM,MODE_SPREAD)*MarketInfo(SYM,MODE_POINT));
    Str4="Lot/Ticket";            Prm4=S2(Lot)+"/"+S0(OrderTicket());
    Str5="Error";                 Prm5=ErrTxt;
    Str6="Expir BUY/SEL";         Prm6=DTIME(EXP[ExpNum].set.BUY.Exp)+"/"+DTIME(EXP[ExpNum].set.SEL.Exp);
    Str7="H/L";                   Prm7=S5(EXP[ExpNum].H,SYM)+"/"+S5(EXP[ExpNum].L,SYM)+"/"+S4(EXP[ExpNum].ATR); //
    // multi-pos diagnostic: summarize active positions if >1, otherwise singleton.
    if (MT5_MaxPositions > 1 && PosCount > 0) {
       string buy_sum="", sel_sum="";
       for (int i = 0; i < PosCount; i++) {
          if (!Pos[i].active || Pos[i].data.Typ == NONE) continue;
          string label = S0(i)+":"+S5(Pos[i].data.Val,SYM)+"/"+S5(Pos[i].data.Stp,SYM)+"/"+S5(Pos[i].data.Prf,SYM)+" "+DTIME(Pos[i].data.T);
          if (Pos[i].data.Typ == MARKET || Pos[i].data.Typ == STOP || Pos[i].data.Typ == LIMIT) {
             // грубо разделяем сторону по типу цены (упрощённо): если Val>0 и BID/* — уточняется через PositionSelectByTicket
             // Здесь используем букву B/S префикса для детекции по prefix в summarу.
             if (!PositionSelectByTicket(Pos[i].ticket)) { buy_sum += "?"+label+" "; continue; }
             if ((ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) buy_sum += "B"+label+" ";
             else sel_sum += "S"+label+" ";
          }
       }
       Str9="BUY[sum]";     Str9 =buy_sum;
       Str10="set.BUY.Val/STP/PRF";  Prm10=S5(EXP[ExpNum].set.BUY.Val,SYM) +"/"+S5(EXP[ExpNum].set.BUY.Stp,SYM)  +"/"+S5(EXP[ExpNum].set.BUY.Prf,SYM);
       Str11="SELL[sum]";   Str11=sel_sum;
       Str12="set.SEL.Val/STP/PRF";  Prm12=S5(EXP[ExpNum].set.SEL.Val,SYM) +"/"+S5(EXP[ExpNum].set.SEL.Stp,SYM)  +"/"+S5(EXP[ExpNum].set.SEL.Prf,SYM);
    } else {
       Str9="BUY/STP/PRF";           Str9 =S5(EXP[ExpNum].BUY.Val,SYM)     +"/"+S5(EXP[ExpNum].BUY.Stp,SYM)      +"/"+S5(EXP[ExpNum].BUY.Prf,SYM);
       Str10="set.BUY.Val/STP/PRF";  Prm10=S5(EXP[ExpNum].set.BUY.Val,SYM) +"/"+S5(EXP[ExpNum].set.BUY.Stp,SYM)  +"/"+S5(EXP[ExpNum].set.BUY.Prf,SYM);
       Str11="SELL/STP/PRF";         Str11=S5(EXP[ExpNum].SEL.Val,SYM)     +"/"+S5(EXP[ExpNum].SEL.Stp,SYM)      +"/"+S5(EXP[ExpNum].SEL.Prf,SYM);
       Str12="set.SEL.Val/STP/PRF";  Prm12=S5(EXP[ExpNum].set.SEL.Val,SYM) +"/"+S5(EXP[ExpNum].set.SEL.Stp,SYM)  +"/"+S5(EXP[ExpNum].set.SEL.Prf,SYM);
    }
    Str13="RISK";                 Prm13=S1(EXP[ExpNum].Rsk);
   TESTER_FILE_CREATE(ExpNum, ErrorFileName); // создание файла отчета со всеми характеристиками  //
   FileClose(TesterFile);
   } // в этой функции нельзя вызывать ERROR_CHECK(), т.к. она сама вызывается в ERROR_CHECK  и при возникновении повторной ошибки происходит переполнение стека




/*   
void ERROR_LOG(string ErrOrder){
   string sB, sBS, sBP, sS, sSS, sSP, ServerTime, ErrorFileName,Expir,  ChkRsk;
   int ErrorFile;
   double Stop=0;
   ErrorFileName="ERROR_"+DoubleToStr(Magic,0)+"_"+ExpertName+".csv"; 
   ErrorFile=FileOpen(ErrorFileName, FILE_READ|FILE_WRITE, ';');  if(ErrorFile<0) {REPORT("ERROR! ErrorCheck(): Не могу открыть файл "+ErrorFileName); return;} 
   Expir =DoubleToStr(ExpirHours,0)+" ("+TimeToStr(ExpirHours,TIME_DATE|TIME_MINUTES)+")";
   if (set.BUY.Val>0){ // момент открытия позы в лонг
      Stop=set.BUY.Val-set.BUY.Stp;
      sB ="set"+DoubleToStr(set.BUY.Val,DIGITS); 
      sBS="set"+DoubleToStr(set.BUY.Stp,DIGITS); 
      sBP="set"+DoubleToStr(set.BUY.Prf,DIGITS);} 
   else { // поза в лонг уже открыта
      sB =DoubleToStr(BUY.Val+BUYSTOP+BUYLIMIT,DIGITS); 
      sBS=DoubleToStr(BUY.Stp,DIGITS); 
      sBP=DoubleToStr(BUY.Prf,DIGITS);}
   if (set.SEL.Val>0){// момент открытия позы в шорт
      Stop=set.SEL.Stp-set.SEL.Val;
      sS ="set"+DoubleToStr(set.SEL.Val,DIGITS); 
      sSS="set"+DoubleToStr(set.SEL.Stp,DIGITS); 
      sSP="set"+DoubleToStr(set.SEL.Prf,DIGITS);} 
   else { // поза в шорт уже открыта
      sS =DoubleToStr(SELL+SELLSTOP+SELLLIMIT,DIGITS); 
      sSS=DoubleToStr(SEL.Stp,DIGITS); 
      sSP=DoubleToStr(SEL.Prf,DIGITS);}
   ChkRsk=S2(RiskChecker(Lot,Stop,EXP[CurExp].Sym));
   ServerTime="-"+TimeToStr(Time[0],TIME_DATE|TIME_MINUTES);
   if (FileReadString(ErrorFile)=="")// прописываем заголовки столбцов 
      FileWrite (ErrorFile,"ServerTime", "Ask/Bid" ,"StpLev" ,"Spred","Ticket","BUY.Val","StpBUY","PrfBUY","SELL","StpSELL","PrfSELL","Expir","Lot",     "Sym/SYM"     ,"CheckRisk","Err");
   FileSeek(ErrorFile,0,SEEK_END);     // перемещаемся в конец
   FileWrite    (ErrorFile, ServerTime ,S4(Ask)+"/"+S4(Bid), S4(StopLevel), Spred , S0(OrderTicket()) , sB  ,  sBS   ,  sBP   ,  sS  ,   sSS   ,  sSP    , Expir , Lot ,Symbol()+"/"+EXP[CurExp].Sym,  ChkRsk   , ErrOrder);
   DATA_PROCESSING(ErrorFile, WRITE_PARAM);
   FileClose(ErrorFile);
   }////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////   
 */  
   // if (err==134) return; // 134-самая распространенная ошибка при оптимизации, 130-на NDD счетах, где стопы=0
   /*if (err==3){// Исключение ошибки тестера, когда сделки совершаются (в 14:28 на М30) или (в 13:59 на Н1).   
      temp=1.0/Period()*Minute(); // Для этого выделяем разницу между временем сделки и временем ТФ 
      temp-=MathRound(temp);      // (должна равняться 0), 
      if (temp!=0) return; // и игнорируем ошибку, если есть эта разница
      }*/

#endif
