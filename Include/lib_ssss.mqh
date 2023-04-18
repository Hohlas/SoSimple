#define SessionsAmount 10 
class SESSIONS_CLASS{
   public:
   float H;
   float L;
   char D;
   datetime T;
   };
SESSIONS_CLASS S[SessionsAmount];    

void SESSIONS(){
   DRAW_SESSION();
   if (TimeMinute(Time[bar])==0){
      if (TimeHour(Time[bar])==3) NEW_SESSION();
      if (TimeHour(Time[bar])==10) NEW_SESSION();
      if (TimeHour(Time[bar])==17) NEW_SESSION();
      }
   
   
   }

void NEW_SESSION(){
   uchar n=0, oldest=0;
   datetime OldestTime=Time[bar];
   float o=float(Open[bar]);
   float c=float(Close[bar]);
   float h,l;
   char d=0;
   if (o<c) {d=1; h=c; l=o;} else {d=-1; h=o; l=c;}
   
   for (uchar i=1; i<SessionsAmount; i++){
      
      if (h>S[i].H || l<S[i].L) {n=i; S[i].T=0;}
      if (S[i].T<OldestTime) {OldestTime=S[i].T; oldest=i;}
      }
   if (n==0) n=oldest;   
   S[n].D=d;
   S[n].H=h;
   S[n].L=l;
   S[n].T=Time[bar];
   
   
   }

void DRAW_SESSION(){
   color clr=clrBlack;
   LINE(" ", bar+1, S[2].H, bar, S[2].H,  clrBlack,0);
   for (uchar i=1; i<SessionsAmount; i++){
      if (S[i].T==0) continue;
      if (S[i].D>0) clr=UPCLR; else clr=DNCLR; 
      RECT(S0(i)+": H="+S4(S[i].H)+" L="+S4(S[i].L), bar+1, S[i].H, bar, S[i].L,  clr,0);
      //LINE(" ", bar+1, S[i].L, bar, S[i].L,  clr,0);
      }
   }