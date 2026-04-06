#define  DrawFlat    0
void EXPERT::FLAT_DETECT(float FltLev, uchar FlatBegin){
   //if (Prn) Print(DTIME(Time[bar])," F[14].Fls.Phase",F[14].Fls.Phase);
   F[n].Flt.Len=0;   // для начала обнулим значения на случай, 
   F[n].Flt.Lev=0;   // если флэт не состоится
   F[n].Fls.Phase=NONE;   // сброс флага (ложняка для данного пика не будет проверяться)
   F[n].Fls.P=F[n].P;    // максимум ложнаяка, пробившего этот пик, пока приравняем к самому пику
   if (FlatBegin==0) return; // у пика небыло совпадений с предыдущими
   if (F[n].Flt.Num<ABS(PicCnt) || F[n].Flt.Num<2)  return; // не набралось кол-во отскоков, либо в условии задано <2 
   int len=SHIFT(F[FlatBegin].T)-bar; // длина флэта
   if (len>125) F[n].Flt.Len=125; else F[n].Flt.Len=char(len); // длина = кол-во бар между крайними пиками (ограничиваем до разумных пределов)  
   if (F[n].Flt.Len<FltLen) return; // слишком короткий флэт
   F[n].Flt.T=F[FlatBegin].T;       // время формирования первого (дальнего) пика флэта
   F[n].Flt.Frnt=F[FlatBegin].Frnt; // фронт первого пика флэта (движение предшествующее флэту) 
   F[n].Flt.Back=F[FlatBegin].Back; // противоположная граница флэта это Back первого пика флэта
   F[n].Flt.Lev=FltLev;   // усредненная граница флэта  
   F[n].Flt.UpLev=MAX(F[n].Flt.Lev,F[n].Flt.Back);
   F[n].Flt.DnLev=MIN(F[n].Flt.Lev,F[n].Flt.Back);
   F[n].Flt.Range=F[n].Flt.UpLev-F[n].Flt.DnLev;
   F[n].Flt.Center=(F[n].Flt.UpLev+F[n].Flt.DnLev)/2;
   datetime t=0; // время и номер ближайшего пика перед флэтом, 
   uchar p=0;    // выходящего за его пределы
   for (uchar f=1; f<LevelsAmount; f++){ // поиск, с какого направления цена зашла во флэт. (Выйдет с противоположного - направление предполагаемого тренда)
      if (F[f].T>F[n].Flt.T || F[f].Brk>CLEAR) continue; // должен быть старше начала флэта
      if (MathAbs(F[f].P-F[n].Flt.Center)>F[n].Flt.Range){ // должен быть за пределами флэта
         if (F[f].T>t) {t=F[f].T; p=f;}
      }  }
   if (p==0 || iFlt==0) Trnd.Flat=0; //V("Flat "+DTIME(F[n].Flt.T),p,clrBlue);
   color Clr=clrYellow;
   //if (F[p].P>F[n].Flt.UpLev) {Trnd.Flat=-1; Clr=clrRed;}    // если цена зашла во флэт сверху, выйдет снизу
   //if (F[p].P<F[n].Flt.DnLev) {Trnd.Flat=1;  Clr=clrGreen;}     
   
   if (F[n].Flt.Frnt>F[n].Flt.Center) {Trnd.Flat=-1; Clr=clrRed;}    // фронт первого пика над флэтом 
   if (F[n].Flt.Frnt<F[n].Flt.Center) {Trnd.Flat=1;  Clr=clrGreen;}  // фронт первого пика под флэтом
   
   F[n].Flt.Trnd=Trnd.Flat; // доп. сохранение тренда индивидуально для каждого флэта
   nFlt=n;       // индекс последнего флэта
   if (DrawFlat){ 
      LINE("First Pic Front", F[n].Flt.T, F[n].Flt.Frnt, F[n].Flt.T, F[n].Flt.Lev, clrBlue, 0);
      LINE("Begin: "+DTIME(F[p].T)+" Flt.Trnd="+S0(F[n].Flt.Trnd), SHIFT(F[n].Flt.T), F[n].Flt.Lev, bar+PicPer,F[n].Flt.Lev, Clr,2);// уровень с несколькими отскоками, который сформировал флэт - жирнее рисуется
      LINE("Begin: "+DTIME(F[p].T)+" Flt.Trnd="+S0(F[n].Flt.Trnd), SHIFT(F[n].Flt.T), F[n].Flt.Back, bar+PicPer,F[n].Flt.Back, Clr,0);
   }  }  
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ       
#define  DrawFalseBreak     0
#define  FLCLR clrDeepSkyBlue
void EXPERT::FALSE_BREAK(uchar f){// проверка ложного пробоя
   // iParam=0 - с подтверждением пробоем базы 
   // iParam=1 - без подтверждения пробоем базы
   int i;
   if (iSignal!=2)            return;  // обработка сигнала ложняка при iSignal=2 (функция INPUT())
   if (F[f].Fls.Phase==NONE)  return;  // ложняк уровня либо отработался, либо не годен
   if (PicCnt>1 && F[f].Flt.Len<FltLen)   return;  // Пробитый флэт д.б. достаточно широким
   if (F[f].Per<FltLen)       return;  // Между пиком и пробоем достаточно бар (>12 по Баженову)
   if (F[f].Flt.Num<PicCnt)       return;  // количество отскоков от уровня не достаточно
   if (F[f].Dir>0){// Вершина
      if (New>F[f].P+Atr.Max*2){// слишком далеко вылетело 
         if (DrawFalseBreak) X("TooBig"+S0(f), New, bar+PicPer, FLCLR);
         F[f].Fls.Phase=NONE; // отменяем слишком большой ложняк  
         return;} 
      if (F[f].Fls.Phase>WAIT && New<F[f].Back+F[f].BackVal/3){ // ложняк зародился и цена вернулась слишком глубоко
         if (DrawFalseBreak) X("TooFar"+S0(f), New, bar+PicPer, FLCLR);
         F[f].Fls.Phase=NONE; // ложняк отработался
         return;}
      //if (F[f].Fls.Phase>START && New>F[f].P+Atr.Lim){// новый пик над пробитым уровнем
      //   if (DrawFalseBreak) X("Double Break "+S0(f), New, bar+PicPer, clrRed);
      //   F[f].Fls.Phase=NONE; // отменяем, ложняк должен состоять из одного фрактала   
      //   return;}
      if (F[f].Fls.Phase==WAIT && New>F[f].P+Atr.Lim){// уровень только что пробит 
         if (DrawFalseBreak) LINE(S0(f)+" Per="+S0(F[f].Per), bar+PicPer,New,  bar+PicPer,F[f].Back,FLCLR,0);// вертикаль из ложняка до Back пробитого уровня (потенциал)
         if (DrawFalseBreak) LINE(S0(f)+" Back="+S4(F[f].Back)+" "+DTIME(F[f].Flt.T)+" Len="+S0(F[f].Flt.Len), bar+PicPer,F[f].P,  SHIFT(F[f].Flt.T),F[f].P,FLCLR,0); // Соединяет пробитый пик с ложняком       
         F[f].Fls.Phase=START;// начало формирования ложняка V(S0(f), F[f].P, SHIFT(F[f].T), clrBlack);
         F[f].Fls.P=New;      // запоминаем пик ложняка
         F[f].Fls.T=Time[bar+PicPer];// и время его 
         double minH=High[bar+PicPer+1],  minL=Low [bar+PicPer+1];
         for (i=bar+PicPer+2; i<SHIFT(F[f].T); i++){// поиск базы ложняка от ложняка до пробитого пика  
            if (Low[i] <minL) minL=Low[i];  
            if (High[i]<minH) minH=High[i]; 
            if (High[i]<High[i+1] || Low[i]<Low[i+1]) break;} // минимум по High или Low между пробитой вершиной и новым пиком  
         F[f].Fls.Base=float(minL+minH)/2;  // базa ложняка - пик из которого он выстрелил
         if (DrawFalseBreak) LINE("Base "+S0(f), bar+PicPer,F[f].Fls.Base, i,F[f].Fls.Base,FLCLR,0); // горизонталь по уровню базы
         }
      if (F[f].Fls.Phase==START){// ложняк начал формироваться
         if (New>F[f].Fls.P){ // обновление пика
            if (DrawFalseBreak) V("NewPic "+S0(f), New, bar+PicPer, FLCLR);
            F[f].Fls.P=New;
            F[f].Fls.T=Time[bar+PicPer];}
         if (New<F[f].P-Atr.Lim){ // возврат под пробитый уровень 
            F[f].Fls.Phase=CONFIRM; 
            if (DrawFalseBreak) LINE("CONFIRM "+S0(FlsUp), bar+PicPer,New, SHIFT(F[f].Fls.T),New,FLCLR,0);
         }  }
      if (F[f].Fls.Phase==CONFIRM && New<F[f].Fls.Base){ // подтверждение ложняка пробоем его базы (уровня на покупку, из которого он выстрелил) 
         F[f].Fls.Phase=GOGO; 
         FlsUp=f;    // индекс ложняка
         if (DrawFalseBreak) LINE("GOGO "+S0(FlsUp), bar+PicPer,New, SHIFT(F[f].Fls.T),New,FLCLR,2);
         }
      if (F[f].Fls.Phase==GOGO && New>F[f].P-Atr.Lim){ // отработался
         if (DrawFalseBreak) V("FlsSig "+S0(f), New, bar+PicPer, DNCLR);
         F[f].Fls.Phase=NONE;}       
   }else{//  Впадина /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
      if (New<F[f].P-Atr.Max*2){// слишком далеко вылетело 
         if (DrawFalseBreak) X("TooBig"+S0(f), New, bar+PicPer, FLCLR);
         F[f].Fls.Phase=NONE; // отменяем слишком большой ложняк  
         return;} 
      if (F[f].Fls.Phase>WAIT && New>F[f].Back-F[f].BackVal/3){ // ложняк зародился и цена вернулась слишком глубоко
         if (DrawFalseBreak) X("TooFar"+S0(f), New, bar+PicPer, FLCLR); 
         F[f].Fls.Phase=NONE; // ложняк отработался
         return;}
      //if (F[f].Fls.Phase>START && New<F[f].P-Atr.Lim){// новый пик под пробитым уровнем
      //   if (DrawFalseBreak) X("Double Break "+S0(f), New, bar+PicPer, clrRed);
      //   F[f].Fls.Phase=NONE; // отменяем, ложняк должен состоять из одного фрактала   
      //   return;}
      if (F[f].Fls.Phase==WAIT && New<F[f].P-Atr.Lim){// уровень только что пробит 
         if (DrawFalseBreak) LINE(S0(f)+" Per="+S0(F[f].Per), bar+PicPer,New,  bar+PicPer,F[f].Back,FLCLR,0);// вертикаль из ложняка до Back пробитого уровня (потенциал)
         if (DrawFalseBreak) LINE(S0(f)+" Back="+S4(F[f].Back)+" "+DTIME(F[f].Flt.T)+" Len="+S0(F[f].Flt.Len), bar+PicPer,F[f].P,  SHIFT(F[f].Flt.T),F[f].P,FLCLR,0); // Соединяет пробитый пик с ложняком       
         F[f].Fls.Phase=START;// начало формирования ложняка V(S0(f), F[f].P, SHIFT(F[f].T), clrBlack);
         F[f].Fls.P=New;      // запоминаем пик ложняка
         F[f].Fls.T=Time[bar+PicPer];// и время его 
         double maxH=High[bar+PicPer+1],  maxL=Low [bar+PicPer+1];
         for (i=bar+PicPer+2; i<SHIFT(F[f].T); i++){// поиск базы ложняка от ложняка до пробитого пика  
            if (Low[i] >maxL) maxL=Low[i];  
            if (High[i]>maxH) maxH=High[i]; 
            if (High[i]>High[i+1] || Low[i]>Low[i+1]) break;} // максимум по High или Low между пробитой вершиной и новым пиком  
         F[f].Fls.Base=float(maxL+maxH)/2;  // базa ложняка - пик из которого он выстрелил
         if (DrawFalseBreak) LINE("Base "+S0(f), bar+PicPer,F[f].Fls.Base, i,F[f].Fls.Base,FLCLR,0); // горизонталь по уровню базы
         }
      if (F[f].Fls.Phase==START){// ложняк начал формироваться
         if (New<F[f].Fls.P){ // обновление пика
            if (DrawFalseBreak) AV("NewPic "+S0(f), New, bar+PicPer, FLCLR);
            F[f].Fls.P=New;
            F[f].Fls.T=Time[bar+PicPer];}
         if (New>F[f].P+Atr.Lim){ // возврат над пробитым уровнем 
            F[f].Fls.Phase=CONFIRM; 
            if (DrawFalseBreak) LINE("CONFIRM "+S0(FlsUp), bar+PicPer,New, SHIFT(F[f].Fls.T),New,FLCLR,0);
         }  }
      if (F[f].Fls.Phase==CONFIRM && New>F[f].Fls.Base){ // подтверждение ложняка пробоем его базы (уровня на покупку, из которого он выстрелил) 
         F[f].Fls.Phase=GOGO; 
         FlsUp=f;    // индекс ложняка
         if (DrawFalseBreak) LINE("GOGO "+S0(FlsUp), bar+PicPer,New, SHIFT(F[f].Fls.T),New,FLCLR,2);
         }
      if (F[f].Fls.Phase==GOGO && New<F[f].P+Atr.Lim){ // отработался
         if (DrawFalseBreak) AV("FlsSig "+S0(f), New, bar+PicPer, UPCLR);
         F[f].Fls.Phase=NONE;}       
      
   }  }  
   
//float CENTER(int i){    // определение центра пересечения трех бар (i-й и два по краям)
//   double Hi=MathMin(High[i],High[i+1]); // крайние значения между
//   double Lo=MathMax(Low [i],Low [i+1]); // i-м и предыдущим
//   Hi=MathMin(Hi,High[i-1]);  // крайние значения между
//   Lo=MathMax(Lo,Low [i-1]);  // i-м и последующим
//   return (float(Hi+Lo)/2);
//   }    
            
            
