
//#include <lib_TRG.mqh>
#include <lib_ATR.mqh> 
#include <lib_Flat.mqh>   
#ifdef PIC_INDICATOR // код компилируется только в индикаторе
         void EXPERT::CONSTANT_COUNTER() {Print("ok");} // ф-я эксперта отсутствует в индикаторе 
#endif          
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ      
int EXPERT::INIT(){
   // ATR INIT
   if (a<=0)   {Print("ATR_INIT(): a<=0");   return(INIT_FAILED);}
   if (A<=0)   {Print("ATR_INIT(): A<=0");   return(INIT_FAILED);}
   if (a>A)    {Print("ATR_INIT(): a>A");    return(INIT_FAILED);}
   SlowAtrPer=A*A;
   FastAtrPer=a*a;
   Print(__FILE__,"/",__FUNCTION__," ExpNum=",ExpNum,"  Ver",Ver);
   Print(__FILE__,"/",__FUNCTION__," ATR_INIT(): FastAtrPer=",FastAtrPer," SlowAtrPer=",SlowAtrPer);
   // PIC INIT
   SET_CHART_SETTINGS(CHART_WHITE);
   BarSeconds=datetime(Period()*60);  // кол-во секунд в баре
   PicPerSeconds=datetime(BarSeconds*PicPer*1.5); // период расчета пика с запасом для временных лагов
   BarsInDay=ushort(24*60/Period()); // Кол-во бар в сутках 
   PerAdapter=float(60.00/Period()); //Print("PerAdapter=",PerAdapter);
   Print(__FILE__,"/",__FUNCTION__," PIC INIT:  Bars=",Bars," bar=",bar," Time[bar]=",DTIME(Time[bar])," Time[Bars-1]=",DTIME(Time[Bars-1]),"  compilation time: ",__DATETIME__);
   CONSTANT_COUNTER();
   NERO_CSV_CREATE();
   return(INIT_SUCCEEDED);
   }    

bool EXPERT::PIC(){// ОСНОВНОЙ ЦИКЛ ПОИСКА УРОВНЕЙ
   if (!ATR_COUNT())  {return(false);}   // Print(DTIME(Time[bar]),": ATR don't ready");
   H2=H1; H1=H; L2=L1; L1=L; C2=C1; C1=C;
   H=(float)High[bar];
   L=(float)Low [bar];
   C=(float)Close[bar];   //O0=(float)Open[bar-1]; // Open[0]=Bid    V("O="+S4(Open[bar-1])+" Ask="+S4(ASK)+" Bid="+S4(BID)+" Spr="+S4(Spred),O0,bar-1,clrGreen); //V("close",C,bar,clrBlue);
   if (Days && NEW_DAY(bar)) TimeFrom=DAYS_TIME(ABS(Days));  // временной предел расчета уровней в днях
   if ((float)High[bar+PicPer]==HIGHEST(PicPer*2+1,bar)){ // Новый hi  ///////////////////////////////////////////////////////    
      NEW_LEVEL( 1, (float)High[bar+PicPer]); // ФОРМИРОВАНИЕ И УДАЛЕНИЕ УРОВНЕЙ
      }
   if ((float)Low [bar+PicPer]==LOWEST (PicPer*2+1,bar)){ // Новый lo  /////////////////////////////////////////////////////////     
      NEW_LEVEL(-1, (float)Low[bar+PicPer]); // ФОРМИРОВАНИЕ И УДАЛЕНИЕ УРОВНЕЙ
      }
   //NEW_W();             // Сигнал "Голова/Плечи" (стоит до GLOBAL_TREND(), т.к. проверяется пробитие Первых Уровней
   TARGET_COUNT();// РАСЧЕТ ЦЕЛЕВЫХ УРОВНЕЙ ОКОНЧАНИЯ ДВИЖЕНИЯ НА ОСНОВАНИИ ИЗМЕРЕНИЯ ПРЕДЫДУЩИХ ДВИЖЕНИЙ   
   //GLOBAL_TREND();      // ОПРЕДЕЛЕНИЕ ТРЕНДА (стоит до LEVELS_FIND_AROUND(), т.к. пробой уровней проверяется до их обновления    
   LEVELS_FIND_AROUND();// ПОИСК СИЛЬНЫХ УРОВНЕЙ      
   LOCAL_TREND();
   //SESSIONS();
   return(true);
   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ    
#define TEST_DATE   "2020.11.10 10:00" // "2022.09.07 18:00"
void EXPERT::NEW_LEVEL(char NewPicDir, float NewFractal){// ФОРМИРОВАНИЕ И УДАЛЕНИЕ УРОВНЕЙ
   Dir=NewPicDir;    // направление последнего пика
   New=NewFractal;
   datetime ExPicTime=Time[Bars-1];// время ближайшшего превосходящего пика из массива...
   char  FltNum=1;      // кол-во совпадений c флэтовыми непробитыми пиками
   char  Cnt=1;        // кол-во совпадений со всеми пиками
   uchar FlatBegin=0;   // время начала флэта
   float FltLev=New; // средний уровень совпавших пиков
   float PwrSum=0;  // Сумма сил пиков, совпадающих с этим по уровню
   uchar LowestWeightCell=0;   // номер ячейки и 
   float LowestWeight=99999;  // сила самого слабого уровня для удаления на случай, если не найдется свободной ячейки
   float Weight=0; // критерий удаления
   float base1,base2;
   uchar e; // ExPicTime array index
   uchar Oldest=n;
   color PicColor;
   for (uchar f=1; f<LevelsAmount; f++){// перебираем весь массив фракталов от большего к меньшему
      if (F[f].P==0){ // незаполненная ячейка
         LowestWeight=0; 
         LowestWeightCell=f; 
         continue;
         } 
      char dir=F[f].Dir;
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
      if (F[f].Brk==BROKEN && New*dir>(F[f].P+Atr.Max*2)*dir) F[f].Brk=MIRROR; // подтверждение зеркального уровня - достаточно глубокий пробой 
      FALSE_BREAK(f);// проверка ложного пробоя при iSignal=1 (lib_Flat.mqh)
      //if (Time[bar+PicPer]==StringToTime(TEST_DATE)) V("Fst="+S0(F[f].First)+" Pwr="+S0(F[f].Pwr/Point/10), f, clrRed); 
      //if (F[f].First && F[f].T==StringToTime(TEST_DATE)){ 
      //   V("Fst="+S0(F[f].First)+" Pwr="+S0(F[f].Pwr/Point/10), New,bar+PicPer, clrRed); // V(" Brk="+S0(F[f].Brk)+" Lim="+S4(Atr.Lim)+" Frnt-Back="+S4(F[f].FrntVal-F[f].BackVal),  bar, New, clrRed);
      //   LINE("Fst="+S0(F[f].First)+" f="+S0(f)+" Back="+S4(F[f].BackVal)+" Pwr="+S4(ATR*Pwr), F[f].T,F[f].P, F[f].BackT,F[f].Back,clrBlue,0);
      //   }
      if (Ver<230.525 && F[f].Brk>CLEAR ) continue;   // далее рассматриваются непробитые уровни 0-CLEAR, 1-TOUCH, 2-MIRROR, 3-BROKEN, 5-USED
      if (F[f].Brk>TOUCH) continue;
      if (Dir==dir){ // сонаправленный пик
         if (MathAbs(New-F[f].P)<Atr.Lim){// сравниваемые фракталы в пределах Lim и это не пробитый пик, т.е. между отобранным и новым пиками ничего не выступает  
            F[f].Flt.Num++; FltNum++;   // поиск совпадающих уровней, увеличиваем кол-во совпадений
            FltLev+=F[f].P;   // и их сумма для усреднения LINE(S0(f)+" Lim="+S5(Atr.Lim)+" a="+S4(Atr.Fast)+" A="+S4(Atr.Slow), bar+PicPer,New,  SHIFT(F[f].T),F[f].P,clrLightBlue,0);
            if (FlatBegin==0 || F[f].T<F[FlatBegin].T) FlatBegin=f;// самый старый пик флэта, для противоположной границы
            //if (FltNum>1) SQUARE_TRIANGLE(f, F[f].TRG.N); // если было совпадение вершин, обрабатывается прямоугольный треугольник (библиотека отключена пока)
            }
         else if (LEV_BREAK(f, New)) continue; // иногда пробой баром "не срабатывает" => доп проверка пробоя фракталом 
         if (F[f].T>ExPicTime)   {ExPicTime=F[f].T; e=f;} // время ближайшего превосходящего пика для поиска фронта
         if (New*dir>F[f].Near*dir)  {F[f].Near=New; F[f].NearVal=(New-F[f].Back)*dir;} // самый близкий подход цены к уровню - его цена и амплидуда
         }     
      else{ // противолежащий пик
         if (New*dir<F[f].Back*dir){
            F[f].Back=New;    // обновление заднего фронта
            F[f].BackVal=(F[f].P-New)*dir; // и его амплитуды
            F[f].BackT=Time[bar+PicPer]; // время последней вершины Back уровня
            F[f].Pwr=MathMin(F[f].FrntVal,F[f].BackVal);
            F[f].Near=New; // и самого близкого подхода 
            F[f].NearVal=0; 
            if (F[f].BackVal<ATR*PicPwr) continue; // достаточный задний фронт должен быть в любом случае
            if (F[f].FrntVal>ATR*PicPwr && // достаточный передний фронт
                F[f].Cnt>=PicCnt && // кол-во совпадений со всеми пиками (пробитыми и зеркальными) 
                F[f].StrongImp){     // сильный импульс из пика       
               F[f].First=true;     // V(S4(F[n].FrntVal)+"_"+S0(F[n].Cnt)+"_"+S4(F[n].Imp/F[n].Atr), n, clrGreen); ////   
      }  }  }  }       
   n=LowestWeightCell; // if (Time[bar+PicPer]==StringToTime(TEST_DATE))  V("XX-"+BTIME(bar)+" LowestWeight="+S0(LowestWeight),n, clrRed);
   F[n].P=New;            // пишем в свободную ячейку значение фрактала
   F[n].T=Time[bar+PicPer];      // время возникновения фрактала
   F[n].Flt.T=Time[bar+PicPer];  // время формирования первого (дальнего) пика флэта
   F[n].Flt.Num=FltNum;  // кол-во совпадений с предыдущими непробитыми уровнями
   F[n].Cnt=Cnt;// кол-во совпадений со всеми уровнями  
   F[n].BarTch=0;  // кол-во касаний с барами
   F[n].Dir=Dir;   // направление фрактала: 1=ВЕРШИНА, -1=ВПАДИНА
   F[n].ExT=ExPicTime; // время ближайшего превосходящего пика для поиска фронта
   F[n].Per=PicPer; // кол-во бар до пробоя пика
   F[n].Brk=CLEAR;   // Признак пробитости: -1~NEW, 0~CLEAR, -1-MIRROR, +1-BROKEN
   F[n].Rev=0; // Разворотный(повышающийся) - превосходящий предыдущий пик, только из разворотных выбираются Первые Уровни 
   F[n].First=false; // Признак сильного "Первого" уровня (большой передний и задний фронты, задний фронт еще не сформирован, поэтому false)
   F[n].StrongImp=false;
   F[n].TrBrk=NEW; // статус трендового уровня: (-1)-не сформирован,  CLEAR(0)-сформирован,  BROKEN(1)-пробит  Пока хай не опустится под трендовый, он будет не действителен.
   F[n].Fls.Phase=NONE; // стадия ложняка: NONE, START, CONFIRM, BREAK
   F[n].TRG.N=0;  // кол-во вершин в треугольнике
   F[n].PwrSum=PwrSum;  // Сумма сил пиков, совпадающих с этим по уровню
   F[n].Atr=Atr.Fast; // значение быстрого atr на момент формирования пика 
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
      base1=LOWEST(PicPer,bar);           // основание справа от пика
      base2=LOWEST(PicPer,bar+PicPer+1);  // основание слева от пика
      F[n].Imp=New*2-base1-base2;  // импульс из пика
      PicColor=DNCLR;
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
      base1=HIGHEST(PicPer,bar);
      base2=HIGHEST(PicPer,bar+PicPer+1);
      F[n].Imp=base1+base2-New*2;  // импульс из пика
      PicColor=UPCLR; 
      } 
   if (F[n].Imp/F[n].Atr>PicImp){ // резкий отскок, и до предыдущего пика больше суток && SHIFT(ExPicTime)-bar>FltLen*PerAdapter
      F[n].StrongImp=true;//LINE(S0(n)+": Imp="+S4(F[n].Imp/F[n].Atr)+" b1="+S4(base1)+" b2="+S4(base2)+" dt="+S0((SHIFT(ExPicTime)-bar))+" PerAdapter="+S0(PerAdapter), bar+PicPer,High[bar+PicPer], bar+PicPer,Low[bar+PicPer], PicColor,4);
      } // V(S0(n)+": Imp="+S4(F[n].Imp/F[n].Atr), n, clrGreen);  
   F[n].BackT=Time[bar+PicPer];
   F[n].Pwr=MathMin(F[n].FrntVal,F[n].BackVal); // Pwr=MIN(FrntVal,BackVal)   
   FLAT_DETECT(FltLev/FltNum, FlatBegin); // if (F[n].T==StringToTime("2022.11.22 13:00"))  V(S4(F[n].FrntVal)+"/"+S4(F[n].BackVal)+"/"+S4(F[n].Pwr)+" "+S0(F[n].Flt.Num), n, clrGreen); //
   NERO_CSV_CREATE(bar);
   }         
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ       
void EXPERT::LOWEST_HI(float BaseLev, float& Delta, uchar f, uchar& Nearest){// ближайший к BaseLev уровень CheckLev, возвращается его номер NearestNum и расстояние между ними
   if (F[f].P+Atr.Lim>BaseLev && F[f].P-BaseLev<Delta)  {Delta=F[f].P-BaseLev;  Nearest=f;}
   }   
void EXPERT::HIGHEST_LO(float BaseLev, float& Delta, uchar f, uchar& Nearest){// ближайший к BaseLev уровень CheckLev, возвращается его номер NearestNum и расстояние между ними
   if (F[f].P-Atr.Lim<BaseLev && BaseLev-F[f].P<Delta)  {Delta=BaseLev-F[f].P;  Nearest=f;}  
   }   
void EXPERT::LOWEST_LO (float& lowest,  uchar f, uchar& f_lowest)    {if (F[f].P<lowest)  {lowest=F[f].P; f_lowest=f;}}
void EXPERT::HIGHEST_HI(float& highest, uchar f, uchar& f_highest)   {if (F[f].P>highest) {highest=F[f].P; f_highest=f;}}   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
void EXPERT::LEVELS_FIND_AROUND(){ // П О И С К   Б Л И З Л Е Ж А Щ И Х   У Р О В Н Е Й 
   float minTrgHi=99999, minTrgLo=99999, minHI=999999, minLO=999999, minH=999999, minL=999999, StpVal=ATR*MathAbs(Trl), 
         PwrImpCntHi=0, PwrImpCntLo=0, Highest=0, Lowest=999999; 
   TrgHi=0; TrgLo=0; stpH=0; stpL=0; // номера уровней в массиве
   HI=0; LO=0;
   for (uchar f=1; f<LevelsAmount; f++){// в нулевом хранится последнее значение, оно же записывается в массив вместо самого слабого пика 
      if (F[f].P==0)    continue; // пустые значения
      //if (F[f].T==StringToTime(TEST_DATE)) V(" Brk="+S0(F[f].Brk)+" Back="+S4(F[f].Back)+" Frnt="+S4(F[f].Frnt),  bar+1, New, clrRed);
      //if (ABS(F[f].P-H)<Atr.Lim || ABS(F[f].P-L)<Atr.Lim) F[f].BarTch++;  // кол-во касаний с барами
      if (LEV_CHECK(f)>TOUCH) continue;
      F[f].Per++;  // увеличение периода уровня до момента пробития  
      if (F[f].TrBrk==NEW){// трендовый уровень еще не сформирован
         if (F[f].Dir>0 && H<F[f].TrMid) {F[f].TrBrk=CLEAR;}  // окончательнрое формирование трендового, когда хоть один хай опустился ниже его уровня.
         if (F[f].Dir<0 && L>F[f].TrMid) {F[f].TrBrk=CLEAR;}
         }
      if (F[f].TrBrk==CLEAR){ // трендовый уровень сформирован
         if (F[f].Dir>0 && H>F[f].TrMid) F[f].TrBrk=BROKEN; // пробитие трендового уровня    
         if (F[f].Dir<0 && L<F[f].TrMid) F[f].TrBrk=BROKEN; // пробитие трендового уровня        
         }
      if (Target!=0){
         if (F[f].Dir>0)   LOWEST_HI(TargetHi, minTrgHi, f, TrgHi);  // ближайший пик к расчитанному целевому уровню   
         else              HIGHEST_LO(TargetLo, minTrgLo, f, TrgLo);    
         }
      // if (Tch==0 && F[f].Brk==TOUCH)   continue; // Пик дб без касаний при Tch=0
      // if (F[f].TrBrk!=CLEAR) continue; // только с непробитым cформированным трендовым   Trd>0  && 
      if (Rev==1 && F[f].Rev==0)       continue; // уровень должен пробить хотябы один пик (REV=1)   
      if (Rev==2 && F[f].FrntVal>F[f].BackVal+Atr.Lim) continue; // задний фронт д.б. больше переднего  (признак тренда)
      // TRAILING/STOP LEVELS
      if (F[f].BackVal>StpVal){
         if (F[f].Dir>0){  if (F[f].T>SEL.T) LOWEST_HI (H, minH, f, stpH);  // ближайший пик к текущей цене для шортового стопа
         }else{            if (F[f].T>BUY.T) HIGHEST_LO(L, minL, f, stpL);  // ближайший пик к текущей цене для лонгового стопа    
         }  }
      // П Е Р В Ы E    У Р О В Н И   
      if (F[f].First!=true) continue; 
      if (F[f].T<TimeFrom) continue; // первые уровни - любые экстремумы за Days
      if (Days<0){ // работа от дальних уровней на периоде Days с заданными Pwr, Cnt, Imp
         if (F[f].Dir>0)   HIGHEST_HI(Highest,f,HI);
         else              LOWEST_LO (Lowest ,f,LO);
      }else{ // работа от ближних уровней на |Days| (0~на всей истории) с заданными Pwr, Cnt, Imp
         if (F[f].Dir>0)   LOWEST_HI (H, minHI, f, HI);  // ближайший к текущей цене
         else              HIGHEST_LO(L, minLO, f, LO);  // первый  уровень
         }  
      }
   // У Р О В Н И    С Е Р Е Д И Н К И
   if (HI!=lastHI)   {lastHI=HI; HI2=0;}
   if (LO!=lastLO)   {lastLO=LO; LO2=0;}
   if (HI>0 && Hi_checksum!=F[HI].P+F[HI].Back && H>F[HI].Back+F[HI].BackVal/4){ // обновилась вершина, либо Back  && F[HI].NearVal>F[HI].BackVal/4
      Hi_checksum=F[HI].P+F[HI].Back; // обновление контрольной суммы          
      HI2=MID_LEV(HI); 
      LINE("HI="+S0(HI)+" P="+S4(F[HI].P)+" Frnt/Back="+S4(F[HI].FrntVal)+"/"+S4(F[HI].BackVal)+" Atr.F/S="+S5(Atr.Fast)+"/"+S5(Atr.Slow), F[HI].T,F[HI].P, F[HI].BackT,F[HI].Back,DNCLR,0);
      //LINE("HI2="+S0(HI2)+" HI="+S0(HI)+" Back="+S4(F[HI].Back)+"/"+DTIME(F[HI].BackT)+" HI2="+S4(HI2), SHIFT(F[HI].T),F[HI2].P,  bar,F[HI2].P, DNCLR,0);
      } 
   if (LO >0 && Lo_checksum!=F[LO].P+F[LO].Back && L<F[LO].Back-F[LO].BackVal/4){ // обновилась вершина, либо ее Back  && F[LO].NearVal>F[LO].BackVal/4
      Lo_checksum=F[LO].P+F[LO].Back; // обновление контрольной суммы   
      LO2=MID_LEV(LO); 
      LINE("LO="+S0(LO)+" P="+S4(F[LO].P)+" Frnt/Back="+S4(F[LO].FrntVal)+"/"+S4(F[LO].BackVal)+" Atr.F/S="+S5(Atr.Fast)+"/"+S5(Atr.Slow), F[LO].T,F[LO].P, F[LO].BackT, F[LO].Back,UPCLR,0); 
      //LINE("LO2="+S0(LO2)+" LO="+S0(LO)+" Back="+S4(F[LO].Back)+"/"+DTIME(F[LO].BackT)+" LO2="+S4(LO2), SHIFT(F[LO].T),F[LO2].P,  bar,F[LO2].P, UPCLR,0); //V("mid="+S0(LO2),F[LO2].P,bar,clrBlue);
      }
   if (HI)  LINE("HI="+S0(HI)+" HI2="+S0(HI2)+" Pwr="+S4(F[HI].Pwr)+" Imp="+S4(F[HI].Imp/F[HI].Atr)+" Cnt="+S0(F[HI].Cnt), bar,F[HI].P,   bar+1,F[HI].P, DNCLR,2);
   if (LO)  LINE("LO="+S0(LO)+" LO2="+S0(LO2)+" Pwr="+S4(F[LO].Pwr)+" Imp="+S4(F[LO].Imp/F[LO].Atr)+" Cnt="+S0(F[LO].Cnt), bar,F[LO].P,   bar+1,F[LO].P, UPCLR,2);
   if (HI2) LINE("HI2="+S0(HI2)+" HI="+S0(HI)+" Back="+S4(F[HI].Back)+"/"+DTIME(F[HI].BackT)+" HI2="+S4(HI2),              bar,F[HI2].P,  bar+1,F[HI2].P,DNCLR,0);
   if (LO2) LINE("LO2="+S0(LO2)+" LO="+S0(LO)+" Back="+S4(F[LO].Back)+"/"+DTIME(F[LO].BackT)+" LO2="+S4(LO2),              bar,F[LO2].P,  bar+1,F[LO2].P,UPCLR,0);
   LINE("HI="+S0(HI)+" LO="+S0(LO)+" Back[28]="+S4(F[28].BackVal)+" PicPwr="+S4(ATR*PicPwr)+" frst="+S0(F[28].First), bar+1, Close[bar+1], bar, Close[bar],  clrSilver,0); 
   }     
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ    
//  CLEAR    0 // новый непробитый
//  TOUCH    1 // с касанием флэтовый
//  MIRROR   2 // зеркальный
//  BROKEN   3 // пробитый
//  USED     5 // отработанный
bool EXPERT::LEV_TOUCH(uchar f){ // touching
   if (F[f].TrBrk<CLEAR) return(false); // Трендовый уровень не успел сформироваться, соответсвенно пик тоже 
   //if (F[f].T==StringToTime(TEST_DATE)) V(" Brk="+S0(F[f].Brk)+" Back="+S4(F[f].Back)+" Frnt="+S4(F[f].Frnt),  bar+1, New, clrRed);
   if (F[f].Dir>0 && H>F[f].P-Atr.Lim && H<F[f].P+Atr.Lim)  {F[f].Brk=TOUCH; return (true);} //LINE("LO=", SHIFT(F[f].T),F[f].P,  bar,H, UPCLR,0);
   if (F[f].Dir<0 && L<F[f].P+Atr.Lim && L>F[f].P-Atr.Lim)  {F[f].Brk=TOUCH; return (true);}
   return(false);
   }
bool EXPERT::LEV_BREAK(uchar f){ // breaking by bar
   if (F[f].Dir>0 && H>=F[f].P+Atr.Lim)   {SET_BROKEN(f); return (true); } // A("BREAK "+S0(f), H, bar, clrBlack); 
   if (F[f].Dir<0 && L<=F[f].P-Atr.Lim)   {SET_BROKEN(f); return (true);}
   return(false);
   }  
bool EXPERT::LEV_BREAK(uchar f, float pic){ // breaking by new pic
   if (F[f].Dir>0 && pic>=F[f].P+Atr.Lim)   {SET_BROKEN(f); return (true);}
   if (F[f].Dir<0 && pic<=F[f].P-Atr.Lim)   {SET_BROKEN(f); return (true);}
   return(false);
   }         
bool EXPERT::LEV_CROSS(uchar f){
   if (H>F[f].P && L<F[f].P){ 
      if (F[f].Brk<BROKEN) F[f].Brk=BROKEN;
      F[f].Brk++; if (F[f].Brk>126) F[f].Brk=126; 
      return (true);}
   return(false);
   }            
char EXPERT::LEV_CHECK(uchar f){ 
   if (F[f].Brk==CLEAR && (LEV_TOUCH(f) || LEV_BREAK(f)))  return(F[f].Brk);
   if (F[f].Brk==TOUCH  && LEV_BREAK(f)) return(F[f].Brk);
   if (F[f].Brk==MIRROR && LEV_CROSS(f)) return(F[f].Brk);
   if (F[f].Brk>=BROKEN && LEV_CROSS(f)) return(F[f].Brk);          
   return(F[f].Brk);
   }    
void EXPERT::SET_BROKEN(uchar f){
   F[f].BrkT=Time[bar]; // время пробития
   F[f].Brk=BROKEN;     // статус
   if (F[f].Dir>0){// A("f="+S0(f)+" HI= "+S0(HI)+" P="+S4(F[f].P), F[f].P, bar, clrBlack); 
      if (f==HI)   {HI=0;  if (iGlb==1) Trnd.Global= 1;} //   X("break HI "+S0(f),F[f].P,bar,DNCLR);
      if (f==HI2)  {HI2=0; if (iGlb==2) Trnd.Global= 1;} //   X("break HI2 "+S0(f),F[f].P,bar,DNCLR);
      Trnd.PicBrk++; if (Trnd.PicBrk> iLoc) Trnd.PicBrk= iLoc; // кол-во пробитых подряд пиков для фильтра входа
   }else{
      if (f==LO)   {LO=0;  if (iGlb==1) Trnd.Global=-1;} //   X("break LO "+S0(f),F[f].P,bar,UPCLR);
      if (f==LO2)  {LO2=0; if (iGlb==2) Trnd.Global=-1;} //   X("break LO2 "+S0(f),F[f].P,bar,UPCLR);
      Trnd.PicBrk--; if (Trnd.PicBrk<-iLoc) Trnd.PicBrk=-iLoc;
   }
   if (F[f].Pwr>ATR*PicPwr) {  // был пробит сильный уровень
      F[f].Fls.Phase=WAIT;} // его ложняк будет интересен: ставим начальный флаг. Флаг сбрасывается на "BREAK"  при формировании уровня в FLAT_DETECT()
   //if (F[f].Flt.Len>0){// если это был флэт шириной более FltLen бар,
   //   if (F[f].Dir>0) Trnd.FltBrk=F[f].P; else Trnd.FltBrk=-F[f].P;//  генерится сигнал "пробой флэта"
   //   }
   
   }     
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ     
void EXPERT::LOCAL_TREND(){
   // Проверка прошлого тренда
   if (Trnd.Flat>0 && L<F[nFlt].Flt.DnLev-Atr.Lim) {Trnd.Flat=0; }//X(" Trnd.Flat=0, Dn="+S4(F[nFlt].Flt.DnLev),L,bar,clrBlue);  // Если цена вышла из флэта в ту же сторону, с которой зашла,
   if (Trnd.Flat<0 && H>F[nFlt].Flt.UpLev+Atr.Lim) {Trnd.Flat=0; }//X(" Trnd.Flat=0, Up="+S4(F[nFlt].Flt.UpLev),H,bar,clrBlue); // Прошлый тренд анулируется.
   
   if (!hi || !lo) return;
   Trnd.Local=0;
   if (Trnd.PicBrk>0) Trnd.Local=1;   
   if (Trnd.PicBrk<0) Trnd.Local=-1; 
   if (iFlt>0) Trnd.Local+=Trnd.Flat; // Выход из флэта напротив входа
   if (Trnd.Local>0)    LINE("Trnd.Local="+S0(Trnd.Local)+" Dn="+S4(F[nFlt].Flt.DnLev),  bar,L,   bar,H, UPCLR,3); 
   if (Trnd.Local<0)    LINE("Trnd.Local="+S0(Trnd.Local),  bar,L,   bar,H, DNCLR,3);
   }

// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
void EXPERT::POC_SIMPLE(){    // определение плотного скопления бар без пропусков
   HiZone=MIN(H,HiZone); // С каждым новым баром края диапазона h и l
   DnZone=MAX(L,DnZone); // обрезаются с учетом новых High и Low
   if (HiZone>DnZone) {PocCnt++; PocCenter=float((HiZone+DnZone)/2);} // считаем длину сформированного диапазона и его серединку
   else{// Диапазон прервался (сузился до нуля)
      //LINE("POC="+S0(PocCnt) ,bar+PocCnt,PocCenter, bar,PocCenter, PocColor,0);
      PocCnt=1;    
      HiZone=H; 
      DnZone=L; 
   }  }    
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
float EXPERT::PIC_PWR(uchar PowerType, uchar f){
   float Power;
   switch(PowerType){
      case 1:  Power=F[f].Pwr;            break;  // пик с максимальным фронтом      
      case 2:  Power=F[f].Pwr*F[f].Cnt;   break;  // и макс кол-вом отскоков
      case 3:  Power=F[f].Cnt;            break;  // зона с максимальным кол-вом отскоков
      case 4:  Power=F[f].PwrSum;         break;  // зона с максимальной силой отскоков
      case 5:  Power=F[f].Imp/F[f].Atr;   break;  // пик с максимальным импульсом
      case 6:  Power=F[f].Imp/F[f].Atr*F[f].Cnt;   break; // и макс. кол-вом отскоков
      default: Power=0; 
      }
   return (Power);
   }
   
uchar EXPERT::MID_LEV(uchar f)  {return(MID_LEV(f, F[f].Tr, (F[f].P+F[f].Back)/2, F[f].T, F[f].BackT));}
uchar EXPERT::MID_LEV(uchar f, float UpLev, float DnLev, datetime time0, datetime time1){// уровень серединки: 1-пик с макс. фонтом, 2-макс фронт с макс кол-вом пиков, 3-макс. кол-во отскоков, 4-макс. сила отскоков
   float Power=0, MaxPower=0;
   uchar Pic=0;
   if (UpLev<DnLev)  SWAP(UpLev,DnLev);
	for (f=1; f<LevelsAmount; f++){  // 
      if (F[f].Brk>TOUCH || F[f].P<=DnLev || F[f].P>=UpLev || F[f].T<time0 || F[f].T>time1) continue; // пик за пределами интересующего нас диапазона 
      Power=PIC_PWR(MidTyp, f);   
	   if (Power>MaxPower){   //Power
         MaxPower=Power; 
         Pic=f;
      }  }   	//if (f1==84) LINE("2: f1="+S0(f1)+" Back="+S4(F[f1].Back)+"/"+DTIME(F[f1].BackT), time0,F[Pic].P,  time1,F[Pic].P, clrBlack,0); 
	return (Pic);
   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ  
void EXPERT::TARGET_COUNT(){// расчет целевых уровней окончания движения на основании измерения предыдущих безоткатных движений
   if (Target==0) return; // Target=-2..2: >0~макс. <0~средн движение от 1-последнего, 2-разворотного пика  
   if (Dir>0 && Time[bar]-F[hi].T<PicPerSeconds){ // только что сформированная вершина (разница с текущим баром в пределах периода пика с запасом)
      if (RevLo2!=RevLo){// пересортировка, если были понижающиеся Lo, иначе обновляется лишь последнее движение LastMovUp
         RevLo2=RevLo;
         ADD_TO_ARRAY(LastMovUp,MovUp); // пересортировка массива  и добавление последнее движение
         if (Target<0)  MidMovUp=(MovUp[0]+MovUp[1]+MovUp[2])/3; // среднее движение
         LastMovUp=0;      
         }
      if (F[hi].P-F[RevLo].P>LastMovUp) {LastMovUp=F[hi].P-F[RevLo].P;}// обновляем последнее движение, если новый пик дальше от разворотной впадины, чем предыдущий   LINE("LastMovUp="+S4(LastMovUp)+" F[RevLo].P="+S4(F[RevLo].P), SHIFT(F[RevLo].T), F[RevLo].P,  bar+PicPer, F[hi].P, clrRed);
      if (Target>0) MidMovUp=MathMax(MovUp[ArrayMaximum(MovUp,WHOLE_ARRAY,0)],LastMovUp);  // среднее максимальных значений прошлых и последнего движения
      if (MathAbs(Target)==1 || (MathAbs(Target)==2 && hi==RevHi)){ // отмеряем целевое движение вниз от последнего пика, или только от разворотного пика
         TargetLo=F[hi].P-MidMovDn;} //LINE(S4(MidMovDn), F[hi].T, F[hi].P,  F[hi].T, TargetLo, clrOrange,0);
   }else if (Dir<0 && Time[bar]-F[lo].T<PicPerSeconds){// // только что сформированная впадина (разница с текущим баром в пределах периода пика с запасом)
      if (RevHi2!=RevHi){// пересортировка, если были повышающиеся Hi, иначе обновляется лишь последнее движение LastMovDn
         RevHi2=RevHi;   
         ADD_TO_ARRAY(LastMovDn,MovDn);
         if (Target<0)  MidMovDn=(MovDn[0]+MovDn[1]+MovDn[2])/3; // среднее движение
         LastMovDn=0;
         }    
      if (F[RevHi].P-F[lo].P>LastMovDn)  {LastMovDn=F[RevHi].P-F[lo].P;}// обновляем последнее движение, если новый пик дальше от разворотной впадины, чем предыдущий   LINE("LastMovDn="+S4(LastMovDn)+" MidMovDn="+S4(MidMovDn), SHIFT(F[RevHi].T), F[RevHi].P,  bar+PicPer, F[lo].P, clrGreen);  
      if (Target>0) MidMovDn=MathMax(MovDn[ArrayMaximum(MovDn,WHOLE_ARRAY,0)],LastMovDn);  // среднее максимальных значений прошлых и последнего движения
      if (MathAbs(Target)==1 || (MathAbs(Target)==2 && lo==RevLo)){ // отмеряем целевое движение вверх от последнего пика, или только от разворотного пика
         TargetHi=F[lo].P+MidMovUp; //LINE("Mid="+S4(MidMovUp)+" Last="+S4(LastMovUp)+", 012="+S4(MovUp[0])+", "+S4(MovUp[1])+", "+S4(MovUp[2]), F[lo].T, F[lo].P,  F[lo].T, TargetHi, clrCornflowerBlue,0); 
   }  }  }   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
void EXPERT::NERO_CSV_CREATE(){
   string FileName="Nero_"+Symbol()+S0(Period())+".csv"; 
   if (FileIsExist(FileName)){  
      if (!FileDelete(FileName)) ERROR_CHECK("Delete "+FileName);
      }
   int File=FileOpen(FileName, FILE_READ | FILE_WRITE); 
   if (File<0) ERROR_CHECK(__FUNCTION__+" Can't open file "+FileName+"!!!");
   string headers="time";
   for (uchar f=1; f<LevelsAmount; f++) headers=headers+" ; fractal"+S0(f);
   FileWrite(File, headers);
   FileClose(File);
   Print("write headers",FileName);
   
   }

void EXPERT::NERO_CSV_CREATE(int cur_bar){
   string FileName="Nero_"+Symbol()+S0(Period())+".csv"; 
   int File=FileOpen(FileName, FILE_READ | FILE_WRITE);
   string NeroInfo=BTIME(cur_bar);
   uchar cnt=1;
   for (uchar f=1; f<LevelsAmount; f++){// в нулевом хранится последнее значение, оно же записывается в массив вместо самого слабого пика 
      if (F[f].P==0)    continue; // пустые значения
      NeroInfo=NeroInfo+";"+
         S0(SHIFT(F[f].T)-bar)+":"+
         S4(F[f].P)+":"+
         S0(F[f].Dir)+":"+
         S4(F[f].FrntVal)+":"+
         S4(F[f].BackVal)+":"+
         S0(F[f].First)+":"+
         S0(F[f].Brk)+":"+
         S0(F[f].Rev)+":"+
         S4(F[f].PwrSum)+":"+
         S0(F[f].Cnt)+":"+
         S0(TimeHour(F[f].T)*60+TimeMinute(F[f].T))+":"+
         S4(F[f].Atr)+":"+
         S4(F[f].Imp/F[f].Atr)+":"+
         S0(F[f].T); // F[f].T+":"+F[f].TrBrk+":"+F[f].Dir+":"+F[f].Rev+":"+
      cnt++;
      }
   if (cnt==LevelsAmount && File>0){ // массив полностью заполнился
      FileSeek (File,0,SEEK_END);     // перемещаемся в конец
      FileWrite(File, NeroInfo);
      Print("write",FileName);
      }
   FileClose(File);
   }
//void EXPERT::GLOBAL_TREND(){ // Cмена глоб. тренда при пробитии Первых Уровней. 
//   if (HI>0 && H>F[HI].P-Atr.Lim)   {HI2=HI; HI=0;  if (iGlb==2) Trnd.Global= 1;}  // V(" HI="+S4(H), F[HI2].P, bar, clrOrange);   
//   if (LO>0 && L<F[LO].P+Atr.Lim)   {LO2=LO; LO=0;  if (iGlb==2) Trnd.Global=-1;}  // A(" LO="+S4(H), F[LO2].P, bar, clrOrange); 
//   if (iGlb==1){ // Cмена глоб. тренда при пробитии "Уровней серединки", определяемого максимальным скоплением бар
//      if (Trnd.Global!= 1 && H>F[HI2].P && H1<F[HI2].P)   Trnd.Global= 1;   
//      if (Trnd.Global!=-1 && L<F[LO2].P && L1>F[LO2].P)   Trnd.Global=-1;   
//      }
//   //if (Trnd.Global== 1)    LINE("Trnd.Global>0",  bar,L,   bar,H, UPCLR,3); 
//   //if (Trnd.Global==-1)    LINE("Trnd.Global<0",  bar,L,   bar,H, DNCLR,3);
//   }  
//uchar EXPERT::MID_LEV(uchar f, float UpLev, float DnLev, datetime time0, datetime time1){// уровень серединки: 1-пик с макс. фонтом, 2-макс фронт с макс кол-вом пиков, 3-макс. кол-во отскоков, 4-макс. сила отскоков
//   float PocVal=0, MaxPoc=0;
//   uchar Pic=0;
//   if (UpLev<DnLev)  SWAP(UpLev,DnLev);
//   if (LevTyp==0) return (f);                // по умолчанию зона серединки на первом уровне
//	for (f=1; f<LevelsAmount; f++){  // 
//      if (F[f].Brk>TOUCH || F[f].P<=DnLev || F[f].P>=UpLev || F[f].T<time0 || F[f].T>time1) continue; // пик за пределами интересующего нас диапазона 
//      switch (LevTyp){ // разные способы нахождения РОС
//   	   case 1:  PocVal=F[f].Pwr;             break;  // пик с максимальным фронтом      
//	      case 2:  PocVal=F[f].Pwr*F[f].Cnt;   break;  // макс фронт с макс кол-вом пиков
//	      case 3:  PocVal=F[f].Cnt;              break;  // зона с максимальным кол-вом отскоков
//	      case 4:  PocVal=F[f].PwrSum;            break;  // зона с максимальной силой отскоков
//	      default: PocVal=0;                      break;  
//	      }
//	   if (PocVal>MaxPoc){   //Power
//         MaxPoc=PocVal; 
//         Pic=f;
//      }  }      
//	//if (f1==84) LINE("2: f1="+S0(f1)+" Back="+S4(F[f1].Back)+"/"+DTIME(F[f1].BackT), time0,F[Pic].P,  time1,F[Pic].P, clrBlack,0); 
//	return (Pic);
//   }

//int POC_DETECT(){// кол-во бар, образующих объем пика
//   double UpZone=P.New, DnZone=P.New-ATR, Zone=P.New-ATR/2;  // верхняя и нижняя границы поиска бар, формирующих POC
//   int BarOut=0, PocBars=0;
//   if (Dir<0) {UpZone=P.New+ATR; DnZone=P.New; Zone=P.New+ATR/2;} // при нижнем пике границы меняются местами
//   for (int p=bar; p<Bars; p++){// поиск назад от текущего бара
//      if (High[p]<DnZone || Low[p]>UpZone) BarOut++; else {PocBars++; } // бар или не попадает, или попадает в границы РОС   if (Prn) X(" PocBars="+DoubleToString(PocBars,0)+" p="+DoubleToString(p,0), (UpZone+DnZone)/2, p, clrRed);
//      if (p-bar>PicPer && BarOut>PocBars) break;}  // if (Prn) Print("p=",p," High[p]=",High[p]," Low[p]=",Low[p]," UpZone=",UpZone," DnZone=",DnZone);
//   //if (PocBars>PocPer){ 
//   //   LINE("Up: POC="+DoubleToString(PocBars,0), bar+PocBars, UpZone,  bar, UpZone, clrGreen); //+BarOut
//   //   LINE("Dn: POC="+DoubleToString(PocBars,0), bar+PocBars, DnZone,  bar, DnZone, clrGreen); //+BarOut
//   //   }
//   return (PocBars);
//   }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ     
   
   
   //void DAY_ATR(){// Д Н Е В Н О Й   Д И А П А З О Н   З А   П О С Л Е Д Н И Е   П Я Т Ь   Д Н Е Й 
//   if (TimeHour(Time[bar])>TimeHour(Time[bar+1])) return; // новый день     
//   double DayHigh=High[iHighest(NULL,0,MODE_HIGH,BarsInDay,bar)], DayLow=Low[iLowest(NULL,0,MODE_LOW ,BarsInDay,bar)];
//   DayMov[DaysCnt]=DayHigh-DayLow; DaysCnt++; if (DaysCnt>=5) DaysCnt=0;
//   DayAtr=0; for (int i=0; i<5; i++) DayAtr+=DayMov[i]; DayAtr/=5; 
//   } //Print(ttt,"NewDay ","  ",DTIME(Time[bar])," DayHigh-DayLow=",DayHigh-DayLow,"   ",NormalizeDouble(DayMov[0],Digits-1)," ",NormalizeDouble(DayMov[1],Digits-1)," ",NormalizeDouble(DayMov[2],Digits-1)," ",NormalizeDouble(DayMov[3],Digits-1)," ",NormalizeDouble(DayMov[4],Digits-1),"      DayAtr=",NormalizeDouble(DayAtr,Digits-1));    

   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ   
//void TREND_FILTER(char DblTop, char Imp, char FltBrk, char& Up, char& Dn){// суммирование входных сигналов  
//   Up=1; Dn=1; 
//   if (Trnd.Global>0) Dn=0;    // глобальный
//   if (Trnd.Global<0) Up=0;    // тренд
//   SIG_SUM(DblTop, Trnd.DblTop,   Up, Dn); // двойной отскок
//   SIG_SUM(FltBrk, Trnd.FltBrk,   Up, Dn); // пробой флэта
//   SIG_SUM(Imp,    Trnd.Imp,      Up, Dn); // резкий импульс
//   
//   if (iGlb   && Trnd.Global>0)   LINE("Up="+S0(Up)+" Global="  +S0(Trnd.Global), bar+1, Low [bar+1]-Atr.Slow, bar, Low [bar]-Atr.Slow, clrBlack,0);
//   if (iGlb   && Trnd.Global<0)   LINE("Dn="+S0(Dn)+" Global="  +S0(Trnd.Global), bar+1, High[bar+1]+Atr.Slow, bar, High[bar]+Atr.Slow, clrBlack,0); 
//   if (DblTop && Trnd.DblTop>0)   LINE("Up="+S0(Up)+" DblTop", bar+1, Low [bar+1]-Atr.Slow*1.2, bar, Low [bar]-Atr.Slow*1.2, clrRed,0);
//   if (DblTop && Trnd.DblTop<0)   LINE("Dn="+S0(Dn)+" DblTop", bar+1, High[bar+1]+Atr.Slow*1.2, bar, High[bar]+Atr.Slow*1.2, clrRed,0); 
//   if (FltBrk && Trnd.FltBrk>0)   LINE("Up="+S0(Up)+" BrkFlat",   bar+1, Low [bar+1]-Atr.Slow*1.4, bar, Low [bar]-Atr.Slow*1.4, clrGreen,0);
//   if (FltBrk && Trnd.FltBrk<0)   LINE("Dn="+S0(Dn)+" BrkFlat",   bar+1, High[bar+1]+Atr.Slow*1.4, bar, High[bar]+Atr.Slow*1.4, clrGreen,0); 
//   if (Imp    && Trnd.Imp>0)      LINE("Up="+S0(Up)+" Imp="     +S0(Trnd.Imp),    bar+1, Low [bar+1]-Atr.Slow*1.6, bar, Low [bar]-Atr.Slow*1.6, clrMagenta,0);
//   if (Imp    && Trnd.Imp<0)      LINE("Dn="+S0(Dn)+" Imp="     +S0(Trnd.Imp),    bar+1, High[bar+1]+Atr.Slow*1.6, bar, High[bar]+Atr.Slow*1.6, clrMagenta,0); 
//   }    // if (Prn) X("Flt="+DoubleToString(Trnd.Flt,0)+" Global="+DoubleToString(Trnd.Global,0)+" Trnd.Dn="+DoubleToString(1,0), Close[bar], bar, clrGray);
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ    
//void SIG_SUM(char SumMethod, float Sig, char& Up, char& Dn){// trend signals sum: "NO", "AND", "OR"
//   if (SumMethod==0) return;
//   if (SumMethod<0){   // signal reverse
//      if (Sig>0) Sig=-1;
//      if (Sig<0) Sig= 1;
//      } 
//   switch (MathAbs(SumMethod)){   
//      case 1:  // "NO" отмена противоположного
//         if (Sig>0)  {Dn=0;}  // 
//         if (Sig<0)  {Up=0;}  //
//      break;   
//      case 2: // "AND" - сложение сигналов
//         if (Sig<=0 && Up>0) Up=0; // 
//         if (Sig>=0 && Dn>0) Dn=0; //
//      break;
//      case 3:  // "OR" доминирующий над "AND" сигнал c отменой противоположного
//         if (Sig>0 && Trnd.Global>=0)  Up=1;   // 
//         if (Sig<0 && Trnd.Global<=0)  Dn=1;   // 
//      break;
//   }  }           