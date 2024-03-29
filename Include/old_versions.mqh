void EXPERT::NEW_LEVEL_230202(char NewPicDir, float NewFractal){// ФОРМИРОВАНИЕ И УДАЛЕНИЕ УРОВНЕЙ
   //Print("Version=",Version);
   Dir=NewPicDir;    // направление последнего пика
   New=NewFractal;
   datetime ExPicTime=Time[Bars-1];// время ближайшшего превосходящего пика из массива...
   char  FltNum=1;      // кол-во совпадений c флэтовыми непробитыми пиками
   char Cnt=0;        // кол-во совпадений со всеми пиками
   uchar FlatBegin=0;   // время начала флэта
   float FltLev=New; // средний уровень совпавших пиков
   float PwrSum=0;  // Сумма сил пиков, совпадающих с этим по уровню
   uchar LowestWeightCell=0;   // номер ячейки и 
   float LowestWeight=99999;  // сила самого слабого уровня для удаления на случай, если не найдется свободной ячейки
   float Weight=0; // критерий удаления
   uchar e; // ExPicTime array index
   uchar Oldest=n;
   for (uchar f=1; f<LevelsAmount; f++){// перебираем весь массив фракталов от большего к меньшему
      if (F[f].P==0){ // незаполненная ячейка
         LowestWeight=0; 
         LowestWeightCell=f; 
         continue;
         } 
      if (F[f].T<F[Oldest].T) Oldest=f;   
      Weight = F[f].Pwr * F[f].Flt.Num / (SHIFT(F[f].T)-bar) /(F[f].Brk+1); // критерий удаления = минимальный фронт * кол-во отскоков / удаление от текущего бара / число пробоев(пропилов)
      if (Weight<LowestWeight && F[f].Fls.Phase<START && f!=HI && f!=LO && f!=stpH && f!=stpL){// самый слабый уровень для удаления. Должен быть старше двух дней и не не стадии ложного пробития. 
         LowestWeight=Weight; 
         LowestWeightCell=f;
         } //  if (Time[bar+PicPer]==StringToTime(TEST_DATE)) V(S0(F[f].Pwr)+" x "+S0(F[f].Flt.Num)+" / "+S0(SHIFT(F[f].T)-bar)+" / "+S0(F[f].Brk+1)+" = "+S3(Weight),  f, clrBlue);  
      if (MathAbs(New-F[f].P)<Atr.Lim){ // совпадение уровней
         PwrSum+=F[f].Pwr;  // Сумма сил пиков, совпадающих с этим по уровню
         F[f].Cnt++;   // кол-во совпадений со всеми пиками (пробитыми и зеркальными) 
         Cnt++;        // для поиска уровня с максимальным количеством отскоков
         } 
      if (F[f].Brk==BROKEN){  // подтверждение зеркального уровня - достаточно глубокий пробой 
         if (F[f].Dir>0 && New>F[f].P+Atr.Max*2) {F[f].Brk=MIRROR;} // глубокий пробой   V(DTIME(Time[bar+PicPer])+"/"+S4(FrntVal), F[f].P, SHIFT(F[f].T), clrBlue);
         if (F[f].Dir<0 && New<F[f].P-Atr.Max*2) {F[f].Brk=MIRROR;} // сонаправленным пиком  
         }
      FALSE_BREAK(f);// проверка ложного пробоя при iSignal=1 (lib_Flat.mqh)
      //if (Time[bar+PicPer]==StringToTime(TEST_DATE)) V("Weight="+S4(Weight/Point/10)+" Pwr="+S0(F[f].Pwr/Point/10)+" Flt="+S0(F[f].Flt.Num)+" Brk="+S0(F[f].Brk)+" Сount= "+S0(F[f].Count), f, clrRed); 
      //if (F[f].T==StringToTime(TEST_DATE)) V(" Brk="+S0(F[f].Brk)+" Back="+S4(F[f].Back)+" Frnt="+S4(F[f].Frnt),  bar+1, New, clrRed);
      if (F[f].Brk>CLEAR ) continue;   // далее рассматриваются непробитые уровни 0-CLEAR, 1-TOUCH, 2-MIRROR, 3-BROKEN, 5-USED
      if (Dir==F[f].Dir){ // сонаправленный пик
         if (MathAbs(New-F[f].P)<Atr.Lim){// сравниваемые фракталы в пределах Lim и это не пробитый пик, т.е. между отобранным и новым пиками ничего не выступает  
            F[f].Flt.Num++; FltNum++;   // поиск совпадающих уровней, увеличиваем кол-во совпадений
            FltLev+=F[f].P;   // и их сумма для усреднения LINE(S0(f)+" Lim="+S5(Atr.Lim)+" a="+S4(Atr.Fast)+" A="+S4(Atr.Slow), bar+PicPer,New,  SHIFT(F[f].T),F[f].P,clrLightBlue,0);
            if (FlatBegin==0 || F[f].T<F[FlatBegin].T) FlatBegin=f;// самый старый пик флэта, для противоположной границы
            //if (FltNum>1) SQUARE_TRIANGLE(f, F[f].TRG.N); // если было совпадение вершин, обрабатывается прямоугольный треугольник (библиотека отключена пока)
            }
         else if (LEV_BREAK(f, New)) continue; // иногда пробой баром "не срабатывает" => доп проверка пробоя фракталом 
         if (F[f].T>ExPicTime)   {ExPicTime=F[f].T; e=f;} // время ближайшего превосходящего пика для поиска фронта
         if (Dir>0 && New>F[f].Near)  {F[f].Near=New; F[f].NearVal=New-F[f].Back;} // самый близкий подход цены к уровню - его цена и амплидуда
         if (Dir<0 && New<F[f].Near)  {F[f].Near=New; F[f].NearVal=F[f].Back-New;} // if (Time[bar+PicPer]==StringToTime(TEST_DATE))  A(DTIME(F[f].T)+" / "+DTIME(ExPicTime), f,  clrGreen);    
         }     
      else{ // противолежащий пик
         if (F[f].Dir>0){ // вершина
            if (New<F[f].Back){  // очередное удаление от пика
               F[f].Back=New;    // обновление заднего фронта
               F[f].BackVal=F[f].P-New; // и его амплитуды
               F[f].BackT=Time[bar+PicPer]; // время последней вершины Back уровня
               F[f].Pwr=MathMin(F[f].FrntVal,F[f].BackVal);
               F[f].Near=New; // и самого близкого подхода 
               F[f].NearVal=0;  
               if (F[f].FrntVal>ATR*PicPwr &&       // при большом переднем фронте 
                  //F[f].FrntVal>F[f].BackVal/3 &&   // относительная пропорция
                  F[f].BackVal>F[f].FrntVal)       // задний фронт больше переднего (признак тренда)
                  F[f].First=true; else F[f].First=false; // ставится флаг первого уровня   
            }  }  
         else{// впадина
            if (New>F[f].Back){           // очередное удаление от пика
               F[f].Back=New;             // обновление заднего фронта
               F[f].BackVal=New-F[f].P;   // и его амплитуды
               F[f].BackT=Time[bar+PicPer]; // время последней вершины Back уровня
               F[f].Pwr=MathMin(F[f].FrntVal,F[f].BackVal); 
               F[f].Near=New;   // if (f==LO) V(S4(New), New, bar+PicPer, clrBlue); 
               F[f].NearVal=0;  
               if (F[f].FrntVal>ATR*PicPwr &&       // при большом переднем фронте 
                  //F[f].FrntVal>F[f].BackVal/3 &&   // относительная пропорция
                  F[f].BackVal>F[f].FrntVal)       // задний фронт больше переднего  (признак тренда)
                  F[f].First=true; else F[f].First=false;   // ставится флаг первого уровня     
         }  }  }  
      if (F[f].TrBrk==CLEAR){ // трендовый уровень сформирован
         if (F[f].Dir>0)   {if (New>F[f].TrMid) F[f].TrBrk=BROKEN;} // пробитие трендового уровня    
         else              {if (New<F[f].TrMid) F[f].TrBrk=BROKEN;} // пробитие трендового уровня        
         }
      //if (F[f].Brk==2 || F[f].Brk==3){  // отмена зеркального уровня - касание, либо обратный пробой
      //   if (F[f].Dir>0 && Dir<0 && New<F[f].P+Atr.Lim) {F[f].Brk=4; X(DTIME(Time[bar+PicPer]), F[f].P, SHIFT(F[f].T), clrRed);} // пробой, либо касание противоположным пиком,  
      //   if (F[f].Dir<0 && Dir>0 && New>F[f].P-Atr.Lim) {F[f].Brk=4;} // маркируем отработавшим   
      //   }         
      //if (F[f].T==StringToTime(TEST_DATE)) Print(Time[bar]," Brk=",F[f].Brk," Frnt=",F[f].Frnt," Back=",F[f].Back);
      
      } 
   n=LowestWeightCell; // if (Time[bar+PicPer]==StringToTime(TEST_DATE))  V("XX-"+BTIME(bar)+" LowestWeight="+S0(LowestWeight),n, clrRed);
   F[n].P=New;            // пишем в свободную ячейку значение фрактала
   F[n].T=Time[bar+PicPer];      // время возникновения фрактала
   F[n].Flt.T=Time[bar+PicPer];  // время формирования первого (дальнего) пика флэта
   F[n].Flt.Num=FltNum;  // кол-во совпадений с предыдущими непробитыми уровнями
   F[n].Cnt=Cnt;// кол-во совпадений со всеми уровнями  
   F[n].Dir=Dir;   // направление фрактала: 1=ВЕРШИНА, -1=ВПАДИНА
   F[n].ExT=ExPicTime; // время ближайшего превосходящего пика для поиска фронта
   F[n].Per=PicPer; // кол-во бар до пробоя пика
   F[n].Brk=CLEAR;   // Признак пробитости: -1~NEW, 0~CLEAR, -1-MIRROR, +1-BROKEN
   F[n].Rev=0; // Разворотный(повышающийся) - превосходящий предыдущий пик, только из разворотных выбираются Первые Уровни 
   F[n].First=false; // Признак сильного "Первого" уровня (большой передний и задний фронты, задний фронт еще не сформирован, поэтому false)
   F[n].TrBrk=NEW; // статус трендового уровня: (-1)-не сформирован,  CLEAR(0)-сформирован,  BROKEN(1)-пробит  Пока хай не опустится под трендовый, он будет не действителен.
   F[n].Fls.Phase=NONE; // стадия ложняка: NONE, START, CONFIRM, BREAK
   F[n].TRG.N=0;  // кол-во вершин в треугольнике
   F[n].PwrSum=PwrSum;  // Сумма сил пиков, совпадающих с этим по уровню
   //F[n].MaxMov=0; // максимальный откат с момента формирования пика для измеренных движений (для Первых уровней)
   F[n].Imp=MathAbs(New-C); // максимальный импульс из пика для определения тренда.   
   if (Dir>0){ // вершина  
      F[n].Tr=New-Atr.Fast;// для вершины трендовый уровень не продажу (пока хай не опустится под трендовый, он будет не действителен)     LINE("PicHi="+S4(F[hi].P)+" F[hi].Trd="+S4(F[hi].Trd), bar+PicPer*2, F[hi].Trd,  bar, F[hi].Trd, clrRed);
      F[n].TrMid=(F[n].P+F[n].Tr)/2;     // серединка на пробой  F[n].Mid=F[n].P-(F[n].P-F[n].Tr)/3;
      F[n].Frnt=LOWEST(SHIFT(ExPicTime)-(bar+PicPer), bar+PicPer+1);   // Передний Фронт уровня (величина развернутого им движения) = минимум, лежащий между новым пиком и превосходящим его баром.    
      F[n].Back=LOWEST(PicPer,bar);// задний фронт = минимальная цена после пика. Будет постепенно увеличиваться по мере удаления цены от уровня       
      F[n].FrntVal=New-F[n].Frnt; // амплитуды
      F[n].BackVal=New-F[n].Back; // этих значений
      F[n].NearVal=0; // Near - уровень, до которого цена приближалась к пику. NearVal - расстояние от Back до Near, т.е. Back от Back
      if (New>F[hi].P)    {F[n].Rev=1;   RevHi=n;}  // "повышающийся пик"  нужен для формирования измеренных движений X("RevHi="+DoubleToString(Rev.F[hi].P,4), Rev.F[hi].P, bar+PicPer, clrRed);    
      hi3=hi2; hi2=hi; hi=n; //   if (F[n].FrntVal>ATR*Pwr) V(S0(n)+","+S4(F[n].FrntVal), New, bar+PicPer, clrRed);
      float ImpHi=F[hi].Imp/(F[lo].Imp+F[lo2].Imp+F[lo3].Imp+float(Point))*3; //V("Imp="+S4(F[hi].Imp)+" dImp="+S4(ImpHi),hi,clrRed);
   }else{      // впадина                                                             
      F[n].Tr=New+Atr.Fast;// для впадины трендовый уровень на покупку (пока лоу не поднимется над трендовым, он будет недействительным)
      F[n].TrMid=(F[n].P+F[n].Tr)/2;    // серединка на пробой    F[n].Mid=F[n].P+(F[n].Tr-F[n].P)/3;
      F[n].Frnt=HIGHEST(SHIFT(ExPicTime)-(bar+PicPer), bar+PicPer+1);   // Передний Фронт уровня (величина развернутого им движения) = максимум, лежащий между новым пиком и нижележащим его баром. 
      F[n].Back=HIGHEST(PicPer,bar);// задний фронт = максимальная цена после пика. Будет постепенно увеличиваться по мере удаления цены от уровня        
      F[n].FrntVal=F[n].Frnt-New; // амплитуды
      F[n].BackVal=F[n].Back-New; // этих значений
      F[n].NearVal=0; // Near - уровень, до которого цена приближалась к пику. NearVal - расстояние от Back до Near, т.е. Back от Back
      if (New<F[lo].P)    {F[n].Rev=1;   RevLo=n;} // "понижающаяся впадина"  нужен для формирования измеренных движений X("RevLo="+DoubleToString(F[RevLo].P,4), F[RevLo].P, bar+PicPer, clrGreen);
      lo3=lo2; lo2=lo; lo=n;  //  if (F[n].T==StringToTime("2022.08.03 17:00"))  A(" Frnt="+S4(F[n].Frnt)+" ExPicTime="+DTIME(ExPicTime)+" "+S0(F[e].Brk), New, bar+PicPer+1, clrBlue);
      float ImpLo=F[lo].Imp/(F[hi].Imp+F[hi2].Imp+F[hi3].Imp+float(Point))*3; 
      } 
   F[n].BackT=Time[bar+PicPer];
   F[n].Pwr=MathMin(F[n].FrntVal,F[n].BackVal); // Pwr=MIN(FrntVal,BackVal)   
   FLAT_DETECT(FltLev/FltNum, FlatBegin); // if (F[n].T==StringToTime("2022.11.22 13:00"))  V(S4(F[n].FrntVal)+"/"+S4(F[n].BackVal)+"/"+S4(F[n].Pwr)+" "+S0(F[n].Flt.Num), n, clrGreen); //
   } 