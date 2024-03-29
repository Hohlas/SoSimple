#define SessionsAmount 20 
class SESSIONS_CLASS{
   public:
   float H,L,Range,Stp,Mid;
   char Typ;
   datetime T;
   };
SESSIONS_CLASS S[SessionsAmount];    

bool SessionsInit=true;
void SESSIONS(){
   if (iSignal!=3) return;
   if (SessionsInit){
      SET_CHART_SETTINGS(CHART_WHITE);
      SessionsInit=false;}
   CHECK_SESSION();
   if (TimeMinute(Time[bar])==0){
      //if (TimeHour(Time[bar])==3)   NEW_SESSION();
      if (TimeHour(Time[bar])==10)  NEW_SESSION();
      if (TimeHour(Time[bar])==17)  NEW_SESSION();
      }
   
   
   }

void NEW_SESSION(){
   uchar n=0, oldest=0;
   datetime OldestTime=Time[bar];
   float o=float(Open[bar]);
   float c=float(Close[bar]);
   float h,l,stp;
   char Typ=0;
   if (o<c) {Typ= 2; h=c; l=o; stp=EXP[CurExp].L;} // last bar = bull(UP)
   else     {Typ=-2; h=o; l=c; stp=EXP[CurExp].H;} // last bar = bear(DN)
   
   for (uchar i=1; i<SessionsAmount; i++){
      if (S[i].T<OldestTime) {OldestTime=S[i].T; oldest=i;}
      if (S[i].Typ==0) n=i;
      }
   if (n==0) n=oldest;   
   S[n].Typ=Typ;
   S[n].H=h;
   S[n].L=l;
   S[n].Stp=stp;
   S[n].Range=h-l;
   S[n].Mid=(h+l)/2;
   S[n].T=Time[bar];
   }
uchar sUp,sDn;
void CHECK_SESSION(){
   color clr=clrBlack, Up1=clrLightGreen, Up0=clrGreen, Dn1=clrPink, Dn0=clrCrimson;
   datetime TimeShift=86400*5;
   float BodyLow=float(MIN(Open[bar],Close[bar]));
   float BodyHigh=float(MAX(Open[bar],Close[bar]));
   float NearestUpSession=999999;
   float NearestDnSession=0;
   int DrawStartBar;
   int skip_bars=3*24*60/Period();
   sUp=0; sDn=0;
   for (uchar i=1; i<SessionsAmount; i++){
      if (S[i].T==0) continue;
      DrawStartBar=bar+1;
      if (S[i].Typ>0){ // зона снизу - green
         clr=Up1;     // от нее лимитные лонги 
         if (BodyLow<S[i].L) {S[i].Typ=0; continue;}// пробой зоны вниз телом свечи
         
         }
      if (S[i].Typ<0){ // зона сверху
         clr=Dn1;    // от нее лимитные шорты
         if (BodyHigh>S[i].H) {S[i].Typ=0; continue;}// пробой зоны вверх телом свечи
         
         }
      if (S[i].Typ==0)  continue; 
      if (SHIFT(S[i].T)-bar<skip_bars) continue;
      if (S[i].Typ>0 && S[i].H>NearestDnSession) {NearestDnSession=S[i].H; sDn=i;}
      if (S[i].Typ<0 && S[i].L<NearestUpSession) {NearestUpSession=S[i].L; sUp=i;}
      // draw indicator lines
      if (SHIFT(S[i].T)-bar==skip_bars) DrawStartBar=SHIFT(S[i].T);
      RECT(S0(i)+": H="+S4(S[i].H)+" L="+S4(S[i].L)+" SHIFT="+S0(SHIFT(S[i].T)-bar)+" StartBar="+S0(DrawStartBar-bar), DrawStartBar, S[i].H, bar, S[i].L,  clr,0);
      LINE(S0(i)+": H="+S4(S[i].H)+" L="+S4(S[i].L)+" Stp="+S4(S[i].Stp)+" Typ="+S0(S[i].Typ), bar+1, S[i].Stp, bar, S[i].Stp,  clr,-1);
      }
   LINE("NearestUp",bar+1,NearestUpSession,bar,NearestUpSession,Dn0,2);   
   LINE("NearestDn",bar+1,NearestDnSession,bar,NearestDnSession,Up0,2);
   }
   
void EXPERT::SIG_SESSIONS(){
   if (UP && sDn>0 && mem.BUY.Val!=S[sDn].Range){// L O N G   ////////////////////////////////////////////////////////////////////////////   
      //if (iCnt && F[LO].Mid
      mem.BUY.Val=S[sDn].Range;
      set.BUY.T=Time[bar]; // время формирования сигнала
      set.BUY.Sig=GOGO;    // сигнал на открытие позы
      set.BUY.Val=S[sDn].H;
      set.BUY.Prf=set.BUY.Val+ATR*Prf;
      set.BUY.Stp=set.BUY.Val-ATR*Stp;  
      if (Prf<0) set.BUY.Prf=S[sUp].L;
      if (Stp<0) set.BUY.Stp=S[sDn].Stp;
      A("BUY:"+S4(set.BUY.Val)+"/"+S4(set.BUY.Stp)+"/"+S4(set.BUY.Prf), set.BUY.Val, bar,  clrGreen);
      }  
   if (DN && sUp>0 && mem.SEL.Val!=S[sUp].Range){
      mem.SEL.Val=S[sUp].Range;
      set.SEL.T=Time[bar];
      set.SEL.Sig=GOGO;
      set.SEL.Val=S[sUp].L;
      set.SEL.Prf=set.SEL.Val-ATR*Prf;
      set.SEL.Stp=set.SEL.Val+ATR*Stp;
      if (Prf<0) set.SEL.Prf=S[sDn].H;
      if (Stp<0) set.SEL.Stp=S[sUp].Stp;
      A("SELL:"+S4(set.SEL.Val)+"/"+S4(set.SEL.Stp)+"/"+S4(set.SEL.Prf), set.SEL.Val, bar,  clrGreen);
      }
   }   