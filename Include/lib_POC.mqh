#include <head_PIC.mqh> 
float minHi,maxLo; // самая нижняя впадина сверху и самая высокая снизу в формирующемся диапазоне
short PocSum, LastPoc;   // инкремент РОС для формирования массива распределения 

// способы вычисления зоны POC: 
#define MAX_FRONT       1  // пик с максимальным фронтом
#define FRONT_X_PICS    2  // макс фронт с макс кол-вом пиков
#define PICS            3  // макс кол-вом пиков
#define PWR_SUM         4  // макс суммарная сила
#define PICS_PWR_KICK   5  // зона с максимальной силой отскоков/разворотов. Суммируются Power=MIN(FrntVal,BackVal)
#define BARS_KICK       6  // зона, проходящая через максимальное кол-во пиков бар
 


color    PocColor    = clrGray, MaxPocColor = clrRed;  // цвет гистограммы POC,  цвет максимального POC



   	
//   	case BARS_CROSS: // 3: зона, пересекающая максимальное кол-во бар
//         for (int b=FromBar; b<=ToBar; b++){// перебор диапазона по барам справа налево
//      		int Hi=int(High[b]/point); // H свечи
//      		int Lo=int(Low [b]/point); // L свечи (в целых числах)
//      		if (Hi<DnEdge || Lo>UpEdge) continue; // свеча за пределами диапазона
//      		if (Hi>UpEdge) Hi=UpEdge;
//		      if (Lo<DnEdge) Lo=DnEdge;
//      		for (int p=Lo; p<=Hi; p++){// перебор свечи от L к H с шагом point=Point*10
//      		   PocArr[p-DnEdge]+=1;    // заполняем массив на каждом уровне, где попадается свеча
//            }  }
//      break;
//   	
//      
//      
//      case BARS_KICK: // 6: зона, проходящая через максимальное кол-во пиков бар
//      	for (int b=FromBar; b<=ToBar; b++){// перебор диапазона по барам справа налево
//      		int Hi=int(High[b]/point); // H свечи
//      		int Lo=int(Low [b]/point); // L свечи (в целых числах)
//      	   if (Hi<UpEdge && Hi>DnEdge)  PocArr[Hi-DnEdge]+=1; // for (int p=Hi-DnEdge-1; p<=Hi-DnEdge+1; p++) PocArr[p]+=1;  // Если кончик свечи в пределах диапазона,
//      	   if (Lo<UpEdge && Lo>DnEdge)  PocArr[Lo-DnEdge]+=1; // for (int p=Lo-DnEdge-1; p<=Lo-DnEdge+1; p++) PocArr[p]+=1;  // увеличиваем количество его попаданий в массиве уровней 
//      	   } 
//      break;

//void EXPERT::POC_INDICATOR(){
//   float  MaxPoc;        // максимальное значение POC
//   float   MaxPocPrice;   // уровень с максимальным значением POC
//   minHi=float(MathMin(High[bar],minHi)); // С каждым новым баром края диапазона minHi и maxLo с учетом новых High и Low
//   maxLo=float(MathMax(Low [bar],maxLo)); // обрезаются, стремясь к его середине. 
//   PocSum++;
//   LastPoc++;
//   if (minHi > maxLo) return;// диапазон пересечения последних нескольких бар положителен, т.е. ни один бар не "выскочил" за него: считаем кол-во идущих подряд бар с общим ценовым диапазоном 
//   
//   if (PocSum>5){// совпало достаточное кол-во бар
//      float UpBorder=float(iHigh(NULL, 0, iHighest(NULL, 0, MODE_HIGH, LastPoc+1, bar+1)));
//      float DnBorder=float(iLow (NULL, 0, iLowest (NULL, 0, MODE_LOW,  LastPoc+1, bar+1)));
//      MaxPocPrice=POC(UpBorder,DnBorder,bar+LastPoc+1, bar+1, MaxPoc,  PICS, true); 
//      //POC_COUNT(bar+LastPoc+1, bar+1, MaxPoc, MaxPocPrice); // расчет уровня и значения РОС в сформированном диапазоне
//      if (MaxPoc>uchar(FltLen) && bar+MaxPoc<Bars){
//         LINE("Up=" ,bar+1,MaxPocPrice, bar+int(MaxPoc),MaxPocPrice, MaxPocColor,1);
//         LastPoc=0;
//      }  }
//   PocSum=0; // кол-во совпавших бар = текущий и предыдущий
//   float mHi=float(High[bar]);   minHi=mHi;
//   float mLo=float(Low [bar]);   maxLo=mLo;
//   for (int i=bar+1; i<Bars; i++){
//      mHi=float(MathMin(High[i],mHi)); // С каждым новым баром края диапазона minHi и maxLo с учетом новых High и Low
//      mLo=float(MathMax(Low [i],mLo)); // обрезаются, стремясь к его середине. 
//      if (mHi<mLo) break;
//      else{
//         PocSum++;
//         minHi=mHi;   // для дальнейшего
//         maxLo=mLo;   // отслеживания  
//      }  }
//            
//   }

// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ  
//float EXPERT::POC_HI(float UpBorder, float DnBorder, int ToBar, int From, float& MaxPoc,  char PocType, bool DrawHistogram){// самая верхняя из посчитанных тремя способами РОС
//   float Poc1=POC(UpBorder,DnBorder,ToBar, From, MaxPoc,  BARS_CROSS, false);  // зона, пересекающая максимальное кол-во бар
//   if (bar+MaxPoc<Bars) LINE("BARS_CROSS "+S4(MaxPoc),bar+1,Poc1, bar+(int)MaxPoc/3,Poc1, clrMediumSeaGreen,0);    
//   float Poc2=POC(UpBorder,DnBorder,ToBar, From, MaxPoc,  PICS_KICK, false);  // зона с максимальным кол-вом отскоков
//   if (bar+MaxPoc<Bars) LINE("PICS_KICK "+S4(MaxPoc),bar+1,Poc2, bar+(int)MaxPoc*2,Poc2, clrRed,2);  
//   float Poc3=POC(UpBorder,DnBorder,ToBar, From, MaxPoc,  BARS_KICK, false); // зона, проходящая через максимальное кол-во пиков бар
//   if (bar+MaxPoc<Bars) LINE("BARS_KICK "+S4(MaxPoc),bar+1,Poc3, bar+(int)MaxPoc,Poc3, clrBlue,0);  
//   float MaxPocPrice=MathMax(Poc1,Poc2);
//   MaxPocPrice=MathMax(Poc3,MaxPocPrice);
//   return (MaxPocPrice);
//   }
//float EXPERT::POC_LO(float UpBorder, float DnBorder, int ToBar, int From, float& MaxPoc,  char PocType, bool DrawHistogram){// самая нижняя из посчитанных тремя способами РОС
//   float Poc1=POC(UpBorder,DnBorder,ToBar, From, MaxPoc,  BARS_CROSS, false);  // зона, пересекающая максимальное кол-во бар
//   if (bar+MaxPoc<Bars) LINE("BARS_CROSS "+S4(MaxPoc),bar+1,Poc1, bar+(int)MaxPoc/3,Poc1, clrMediumSeaGreen,0);    
//   float Poc2=POC(UpBorder,DnBorder,ToBar, From, MaxPoc,  PICS_KICK, false);  // зона с максимальным кол-вом отскоков
//   if (bar+MaxPoc<Bars) LINE("PICS_KICK "+S4(MaxPoc),bar+1,Poc2, bar+(int)MaxPoc*2,Poc2, clrRed,2);  
//   float Poc3=POC(UpBorder,DnBorder,ToBar, From, MaxPoc,  BARS_KICK, false); // зона, проходящая через максимальное кол-во пиков бар
//   if (bar+MaxPoc<Bars) LINE("BARS_KICK "+S4(MaxPoc),bar+1,Poc3, bar+(int)MaxPoc, Poc3, clrBlue,0);  
//   float MaxPocPrice=MathMin(Poc1,Poc2);
//   MaxPocPrice=MathMin(Poc3,MaxPocPrice);
//   return (MaxPocPrice);
//   }   