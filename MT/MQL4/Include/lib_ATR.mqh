
bool EXPERT::ATR_COUNT(){  
   // ВАРИАНТ-I   ДАННЫЙ МЕТОД НЕ РАБОТАЕТ НА ТЕСТИРОВАНИИ  ИЗ-ЗА СБОЕВ НА ПРОПУЩЕННЫХ БАРАХ, т.е. 
   //             при разной длине истории получаются разные значения индикатора. 
   //float HL=float(High[bar]-Low[bar]);
   //fstBUF+=HL;   
   //slwBUF+=HL;  
   //cntAtrBars++;   
   //if (cntAtrBars<=FastAtrPer)  return(false);// набралось достаточно HL для усреднения
   //fstBUF-=float(High[bar+FastAtrPer]-Low[bar+FastAtrPer]);
   //Atr.Fast=fstBUF/FastAtrPer;    
   //if (cntAtrBars<=SlowAtrPer)  return(false);
   //slwBUF-=float(High[bar+SlowAtrPer]-Low[bar+SlowAtrPer]);
   //Atr.Slow=slwBUF/SlowAtrPer;   
   
   // ВАРИАНТ-II  Расчет ATR с помощью классических индюков, при этом в тестере появляется доп окно с графиками 
   
   if (bar+SlowAtrPer>=Bars){   // так и метод сдвига массива HL,  имеют расхождения Реал/Тест из-за пропусков бар и ХЗ знает от чего
      ATR=0;   Atr.Fast=0;  Atr.Slow=0;
      Print(__FUNCTION__,": Bars<SlowAtrPer Bars=",Bars," SlowAtrPer=",SlowAtrPer);
      return(false);}
   Atr.Fast=0; 
   for (int b=bar; b<bar+FastAtrPer; b++) Atr.Fast+=float(High[b]-Low[b]);    
   Atr.Fast/=FastAtrPer;
   if (Atr.Slow<=0 || TimeDay(Time[bar])!=TimeDay(Time[bar+1])){  // первый расчет нужен сразу после старта, дальше медленный АТР считается раз в сутки
      Atr.Slow=0;   
      for (int b=bar; b<bar+SlowAtrPer; b++) Atr.Slow+=float(High[b]-Low[b]);    
      Atr.Slow/=SlowAtrPer;
      }
   
   if (Atr.Slow<=0 || Atr.Fast<=0) return(false);
   if (Atr.Fast>Atr.Slow){
      Atr.Max=Atr.Fast;
      Atr.Min=Atr.Slow;
   }else{ // Atr.Fast<Atr.Slow
      Atr.Max=Atr.Slow;
      Atr.Min=Atr.Fast;
      }
   switch (Ak){// АТР для стопов: 
      default: ATR=Atr.Slow;  break; // 
      case  1: ATR=Atr.Fast;  break;
      case  2: ATR=Atr.Min;   break;
      case  3: ATR=Atr.Max;   break;
      }
   Atr.Lim=ATR*PicVal/100;   // допуск уровней в % ATR
   return(true);
   }

  
      
    

    
   
           
