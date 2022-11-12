#property copyright "Copyright © 2008, Hohla"
#property link      "mail@hohla.ru"
#property show_inputs
extern string InputFileName="#.txt";
extern int Norm=2;
int   SourceFile, TargetFile, time=0, time1=0, Log;
int start(){
   int   i, j, hour, min, min1, year, month, day; 
   double O,H,L,C,V, O1,H1,L1,C1,V1;  
   string str, sym, sYear,sMonth,sDay,sHour,sMin,sSec,sO,sH,sL,sC,sV;
   

   SourceFile=FileOpen(InputFileName, FILE_READ, ',');
   if(SourceFile<0) {Alert("Не могу открыть файл",InputFileName); return;}
   TargetFile=FileOpen("History.csv", FILE_CSV | FILE_WRITE, ',');
   //FileWrite(TargetFile,"<TICKER>","<DTYYYYMMDD>","<TIME>","<OPEN>","<HIGH>","<LOW>","<CLOSE>","<VOL>"); 
   if (TargetFile < 0) {Alert("Не могу создать файл для сохранения котировок ");     return;}   
   while (!FileIsLineEnding(SourceFile))  str=FileReadString(SourceFile); // читаем первую строку с параметрами
   while (!FileIsEnding(SourceFile)){
   //for (i=1; i<100; i++){
      sym=FileReadString(SourceFile); // читаем символ
      str=FileReadString(SourceFile); // читаем дату
      year =StrToDouble(StringSubstr(str, 0, 4)); // расписываем
      month=StrToDouble(StringSubstr(str, 4, 2)); // дату
      day  =StrToDouble(StringSubstr(str, 6, 2)); // на составляющие
      str=FileReadString(SourceFile); // читаем время
      hour=StrToDouble(StringSubstr(str, 0, 2)); //разбираем на часы и
      min=StrToDouble(StringSubstr(str, 2, 2));  // минуты
      O=StrToDouble(FileReadString(SourceFile)); // читаем данные
      H=StrToDouble(FileReadString(SourceFile));
      L=StrToDouble(FileReadString(SourceFile));
      C=StrToDouble(FileReadString(SourceFile));
      V=StrToDouble(FileReadString(SourceFile));
      while (!FileIsLineEnding(SourceFile)) str=FileReadString(SourceFile); // читаем остатки если есть
      
      time1=time;
      while(TimeYear (time)<year)   time+=60; // узнаем количество 
      while(TimeMonth(time)<month)  time+=60;  // секунд 
      while(TimeDay  (time)<day)    time+=60;  // для
      while(TimeHour (time)<hour)   time+=60;  // текущей
      while(TimeMinute(time)<min)   time+=60;  // даты
      if (time1==0) time1=time; // для первого прохода
      //Print("date=",year,".",month,".",day," ",hour,":",min,"  time=",time," time1=",time1," TimeYear=",TimeYear(time)," TimeMonth=",TimeMonth(time)," TimeDay=",TimeDay(time)," TimeHour=",TimeHour(time)," TimeMinute=",TimeMinute(time));
         
      for (j=time1+60; j<=time; j+=60){// если имеются пропущенные дни
         if (TimeDayOfWeek(j)==6 ||TimeDayOfWeek(j)==0)  continue;
         //FileWrite(TargetFile,TimeYear(j)+"."+TimeMonth(j)+"."+TimeDay(j),TimeHour(j)+":"+TimeMinute(j),O,H,L,C,V); // один из вариантов записи (не считывается терминалом)
         
         // Представим данные в виде: xxxxxx,20010103,000300,268.9000,268.9000,268.9000,268.9000,4
         sYear=DoubleToStr(TimeYear(j),0);
         if (TimeMonth(j)==0) sMonth="00"; else {if (TimeMonth(j)<10)   sMonth="0"+DoubleToStr(TimeMonth(j),0);   else  sMonth=DoubleToStr(TimeMonth(j),0);}
         if (TimeDay(j)==0)   sDay="00";   else {if (TimeDay(j)<10)     sDay  ="0"+DoubleToStr(TimeDay(j),0);     else  sDay =DoubleToStr(TimeDay(j),0);}
         if (TimeHour(j)==0)  sHour="00";  else {if (TimeHour(j)<10)    sHour ="0"+DoubleToStr(TimeHour(j),0);    else  sHour=DoubleToStr(TimeHour(j),0);}
         if (TimeMinute(j)==0)sMin="00";   else {if (TimeMinute(j)<10)  sMin  ="0"+DoubleToStr(TimeMinute(j),0);  else  sMin =DoubleToStr(TimeMinute(j),0);}
         sO=DoubleToStr(O,Norm);
         sH=DoubleToStr(H,Norm);
         sL=DoubleToStr(L,Norm);
         sC=DoubleToStr(C,Norm);
         sV=DoubleToStr(V,0);
         //FileWrite(TargetFile, sym, sYear+sMonth+sDay, sHour+sMin+"00",sO,sH,sL,sC,sV);
         FileWrite(TargetFile, sYear+"."+sMonth+"."+sDay, sHour+":"+sMin,sO,sH,sL,sC,sV);
      }  } 
   // Будем писать историю операций с подробностями   
   
   
   FileClose(SourceFile);
   FileClose(TargetFile);
   }
/*
void deinit(){
  if(SourceFile>=0) FileClose(SourceFile);
  if(TargetFile>=0) FileClose(TargetFile);
  }
*/