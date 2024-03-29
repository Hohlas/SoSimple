#property copyright "Hohla"
#property link      "http://www.mql5.com"
#property version   "1.00"
#property strict

#define  EXPERTS_LIM  255  // максимальное кол-во проверяемых экспертов
#define  ORDERS_LIM   65535  // максимальное кол-во сделок одного эксперта за последние два года
#define  Real         true

struct AllExperts{  //  C Т Р У К Т У Р А   P I C
   int      magic;
   short    trade[ORDERS_LIM];
   datetime time[ORDERS_LIM];
   float    tickval;
   };
AllExperts Expert[EXPERTS_LIM];   
uchar Experts=0; // общее количество экспертов   
datetime HistoryPeriod=3600*24*365*2; // анализ истории не глубже 2 лет

void OnStart(){
   short profit=0;
   ushort TradeCnt[EXPERTS_LIM]; // счетчик сделок
   string FileName; 
   ArrayInitialize(TradeCnt,0);
   if (Real) {FileName="MatLab"+AccountCurrency()+".csv"; FileDelete(FileName);} // каждый час создаем новый файл
   else      {FileName="MatLabTest.csv";}//  
   int MgcFile, File=FileOpen(FileName, FILE_READ | FILE_WRITE); 
   if (File<0) {Alert("MatLabLog(): Can not open file "+ FileName+"! for history saving"); return;}
   FileWrite(File, "Magic","TickVal","Risk","Deal/Time..."); // прописываем в первую строку названия столбцов
   for(int i=0; i<OrdersHistoryTotal(); i++){// перебераем историю сделок эксперта
      if (OrderSelect(i, SELECT_BY_POS,MODE_HISTORY)==false || OrderMagicNumber()==0 || OrderCloseTime()==0 || OrderProfit()==0) continue;
      //if (OrderMagicNumber()!=63339804) continue;
      if (Time[0]-OrderCloseTime()>HistoryPeriod) continue; // Пропускаем все ордера старше двух лет, чтобы не переполнять масссив. Для гарфического анализа они не пригодятся.  
      uchar e=0;
      EXPERTS_PARAMS(e, OrderMagicNumber(), MgcFile);
      Expert[e].trade[TradeCnt[e]]=short((OrderProfit()+OrderSwap()+OrderCommission())/OrderLots()/MarketInfo(OrderSymbol(),MODE_TICKVALUE));
      Expert[e].time[TradeCnt[e]]=OrderCloseTime();  //Print(" TrdCnt[",e,"]=",TradeCnt[e]," trade=",Expert[e].trade[TradeCnt[e]]," time=",Expert[e].time[TradeCnt[e]]);
      //Print("TradeCnt[",e,"]=",TradeCnt[e]," Expert[",e,"].trade[",TradeCnt[e],"]=",Expert[e].trade[TradeCnt[e]]);
      TradeCnt[e]++; 
      }    
   for (uchar e=0; e<=Experts; e++){
      short order=1; // Alert("magic[",e,"]=",magic[e]);
      FileSeek (File,0,SEEK_END); // перемещаемся в конец файла MatLabTest.csv
      FileWrite(File, DoubleToStr(Expert[e].magic,0)+";"+DoubleToStr(Expert[e].tickval,5)+";"+"0.1"); // прописываем в первую ячейку magic,
      for (ushort t=0; t<=TradeCnt[e]; t++){ //
         if (Expert[e].trade[t]==0) continue;  
         FileSeek (File,-2,SEEK_END); // потом дописываем
         FileWrite(File,  ""    , DoubleToStr(Expert[e].trade[t],0)+"/"+TimeToStr(Expert[e].time[t],TIME_DATE|TIME_MINUTES));    // ежедневные профиты/время сделки из созданного массива    
      }  }
   FileClose(File); 
   }  
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
void EXPERTS_PARAMS(uchar& ExpCnt, int ExpMagic, int& File){// создание массива параметров для всех экспертов
   string FileName="Trades"+DoubleToStr(ExpMagic,0)+".csv"; 
   for (ExpCnt=0; ExpCnt<EXPERTS_LIM; ExpCnt++){
      if (Expert[ExpCnt].magic==ExpMagic) break;
      if (Expert[ExpCnt].magic==0){// first time 
         //отдельный для каждого эксперта файл со списком сделок
         FileDelete(FileName);
         File=FileOpen(FileName, FILE_READ | FILE_WRITE); 
         FileWrite(File, "ticket","OpenTime","CloseTime","OpenPrice","ClosePrice","ProfitPips","Profit$","Comission");
         FileClose(File);
         Expert[ExpCnt].magic=ExpMagic;
         Expert[ExpCnt].tickval=float(MarketInfo(OrderSymbol(),MODE_TICKVALUE));
         Experts=ExpCnt;
         break;
         }
      if (ExpCnt>=EXPERTS_LIM) {Alert("WARNING!!! Experts>",EXPERTS_LIM, " Can't create MatLabLog File"); }   
      }
   //отдельный для каждого эксперта файл со списком сделок
   File=FileOpen(FileName, FILE_READ | FILE_WRITE);
   FileSeek (File,0,SEEK_END); // потом дописываем
   FileWrite(File,OrderTicket(), OrderOpenTime(),OrderCloseTime(),OrderOpenPrice(),OrderClosePrice(),(OrderProfit()+OrderSwap()+OrderCommission())/OrderLots()/MarketInfo(OrderSymbol(),MODE_TICKVALUE),OrderProfit()+OrderSwap()+OrderCommission(),OrderSwap()+OrderCommission());     
   FileClose(File);
   }    
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
//ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
string OrdToStr(int Type){ 
   switch(Type){
      case 0:  return ("BUY"); 
      case 1:  return ("SELL");
      case 2:  return ("BUYLIMIT"); 
      case 3:  return ("SELLLIMIT");
      case 4:  return ("BUYSTOP");
      case 5:  return ("SELLSTOP");
      case 6:  return ("RollOver");
      case 10: return ("SetBUY");
      case 11: return ("SetSELL");
      default: return ("-");
   }  }