//+------------------------------------------------------------------+
//|                                                        trade.mq4 |
//|                      Copyright © 2004, MetaQuotes Software Corp. |
//|                                       http://www.metaquotes.net/ |
//+------------------------------------------------------------------+
#property copyright "Copyright © 2004, MetaQuotes Software Corp."
#property link      "http://www.metaquotes.net/"

#include <stdlib.mqh>
#include <WinUser32.mqh>
//+------------------------------------------------------------------+
//| script "trading for all money"                                   |
//+------------------------------------------------------------------+
int start()
  {
//----
   string FileName="MatLabUSD.csv";
   FileCopy(FileName,0,"Reports_"+TimeToStr(TimeCurrent(),TIME_DATE)+".csv",0);
   Print("OK");
    
   return(0);
  }
//+------------------------------------------------------------------+