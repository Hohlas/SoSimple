float LOWEST (datetime time)              {return (float(Low [iLowest (NULL,0,MODE_LOW ,SHIFT(time)-bar,bar)]));} 
float LOWEST (int shift)                  {return (float(Low [iLowest (NULL,0,MODE_LOW ,shift-bar,      bar)]));} 
float LOWEST (int shift,     int from_bar){return (float(Low [iLowest (NULL,0,MODE_LOW ,shift,          from_bar)]));} 
float LOWEST (datetime time, int from_bar){return (float(Low [iLowest (NULL,0,MODE_LOW ,SHIFT(time)-from_bar,from_bar)]));}

float HIGHEST(datetime time)              {return (float(High[iHighest(NULL,0,MODE_HIGH,SHIFT(time)-bar,bar)]));} 
float HIGHEST(int shift)                  {return (float(High[iHighest(NULL,0,MODE_HIGH,shift-bar,      bar)]));} 
float HIGHEST(int shift,     int from_bar){return (float(High[iHighest(NULL,0,MODE_HIGH,shift,          from_bar)]));} 
float HIGHEST(datetime time, int from_bar){return (float(High[iHighest(NULL,0,MODE_HIGH,SHIFT(time)-from_bar,from_bar)]));}     
    
template <typename type1> // шаблон функций для любых типов входных переменных
type1 MAX(type1 n1, type1 n2){  
   if (n1>n2) return(n1);
   else return(n2); 
   }
   
template <typename type2>   
type2 MAX(type2 n1, type2 n2, type2 n3){  
   if (n1>=n2 && n1>=n3) return(n1); else 
   if (n2>=n1 && n2>=n3) return(n2); else
   return (n3); 
   }   
   
template <typename type3> // шаблон функций
type3 MIN(type3 n1, type3 n2){  
   if (n1<n2) return(n1);
   else return(n2); 
   }   

template <typename type4>   
type4 MIN(type4 n1, type4 n2, type4 n3){  
   if (n1<=n2 && n1<=n3) return(n1); else 
   if (n2<=n1 && n2<=n3) return(n2); else
   return (n3); 
   }   
   
template <typename type5>    
type5 ABS(type5 num){
   if (num<0) return (-num);       else return (num); 
   } 

template <typename type6>
void SWAP(type6 &n1, type6 &n2){
   type6 temp=n1;
   n1=n2; n2=temp;
   } 
   
template <typename type7>
void ADD_TO_ARRAY(type7 num, type7 &array[]){ 
   uint arr_size=ArraySize(array); 
   if (arr_size<2) return;            
   for (uint i=arr_size-1; i>0; i--) array[i]=array[i-1];
   array[0]=num;  
   } 
   
template <typename type8> 
type8 ARRAY_MAX(type8 &array[]){ 
   uint arr_size=ArraySize(array); 
   if (arr_size==0) return(0);           
   type8 max=array[0]; 
   for (uint i=1; i<arr_size; i++) if(max<array[i]) max=array[i]; 
   return(max); 
   }        
   
template <typename type9>
void INCREASE(type9 &num, type9 increment, type9 limit){ 
   if (num>limit-increment) num=limit;
   else num+=increment; 
   }  
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
bool NEW_DAY(int b)    {if (TimeDay(Time[b])!=TimeDay(Time[b+1]))             return (true); else return (false);}
bool NEW_WEEK(int b)   {if (TimeDayOfWeek(Time[b])<TimeDayOfWeek(Time[b+1]))  return (true); else return (false);}
bool NEW_MONTH(int b)  {if (TimeMonth(Time[b])!=TimeMonth(Time[b+1]))         return (true); else return (false);}
datetime DAYS_TIME(uchar CountDays){
   int b=0;
   while (CountDays>0){
      b++;  if (bar+b>=Bars-1) break;
      if (NEW_DAY(bar+b)) CountDays--; // if (Time[bar]==StringToTime("2022.11.04 00:00"))  Print("Time[",bar,"+",b,"]=",Time[bar+b]," CountDays=",CountDays);
      }
   return (Time[bar+b]);
   }   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
//void VERSION(){ 
//   uchar chr; 
//   for (chr=0; chr<StringLen(NAME_VER); chr++)  if (StringGetChar(NAME_VER,chr)>47 && StringGetChar(NAME_VER,chr)<58) break; // в имени ищем число ("0"-48, "1"-49, "2"-50,..., "9"-57)
//   NAME=StringSubstr(NAME_VER,0,chr);
//   VER=StringSubstr(NAME_VER,chr,7);
//   }

// типы ордеров  
#define NONE   0
#define MARKET 1 
#define STOP   2     
#define LIMIT  3  // 
#define SET    4  // устанавливаемый 

class PRICE{    // 
   public:
   datetime T, Exp;  // последнее время обновления зоны
   char Sig;         // отслеживаемый паттерн
   char Typ;         // тип ордера
   float Val,Stp,Prf,Max,Min;  // 
   }; 
class ORD_TYPE{
   public:
   PRICE BUY, SEL;
   };
//+-------------------------------------------------------------+
//| родительский класс с общими функциями                       |
//| для разных экспертов                                        |
//+-------------------------------------------------------------+  
uchar CurExp=0;
class EXPERT_PARENT_CLASS { // общие функции во всех последующих версиях 
   #define LOAD 1
   #define SAVE 2
   #define PARAMS 80 // максимальное количество входных параметров эксперта
   #define MAX_EXPERTS_AMOUNT 100 // 
   private: // переменные только этого класса
      uchar    cnt1, cnt2, mode;
   
   protected: // переменные этого и дочерних классов
      uchar    ExpNum; // порядковый номер в массиве (номер экземпляра класса)  эксперта       
      ushort   BarsInDay, FastAtrPer, SlowAtrPer, Tout, Tin, Tper,  ExpirBars;
      float    Present, PerAdapter;
      
   public: // переменные доступные отовсюду
      short    Per, HistDD, LastTestDD, Back;
      datetime Bar, TestEndTime, ExpMemory, BarSeconds, PicPerSeconds; // кол-во секунд в баре, в периоде расчета пика     
      double   PRM[PARAMS];
      string   ID, Sym, Name, Hist, OptPer;
      float    ATR, atr, Rsk;
      double   Ver;
      int      Mgc; 
      PRICE SEL, BUY;
      ORD_TYPE set,mem;
      
      void EXPERT_PARENT_CLASS(){
         Per=short(Period());
         Sym=Symbol();
         HistDD=0;
         LastTestDD=0;
         Back=0;
         Rsk=Risk;
         //VERSION();
         Name=NAME; 
         Ver=StringToDouble(VER);
         Print("EXPERT_PARENT_CLASS constructor: CurExp=",CurExp," Name=",Name," Ver=",Ver); 
         }
        
      void ORDERS_COLLECT();
      void ORDERS_SET();
      void SET_BUY();
      void SET_SEL();        
      void MODIFY();
      void ORDER_CHECK();
      void EMPTY_EXPERTS_DELETE();
      void GLOBAL_VARIABLES_LIST();    // функция со списком глобальных переменных. Запускается в COUNT()
      void CHECK_VARIABLES();
      void CLASS_INIT(uchar e){ExpNum=e;}
     // void ERROR_LOG(string ErrTxt);
      
      void BACKUP(){ // сохранение списка переменных заданного эксперта
         cnt1=0; cnt2=0;
         mode=SAVE; //Print("MODE=SAVE, expert=",SetExpertNum);
         GLOBAL_VARIABLES_LIST();
         }
   
      void RESTORE(){ // восстановление списка переменных заданного эксперта
         cnt1=0; cnt2=0;
         mode=LOAD; //Print("MODE=LOAD, expert=",SetExpertNum);
         GLOBAL_VARIABLES_LIST();
         }   
      
      template <typename type1>     
      void EXPERT_PARENT_CLASS::COPY(type1 &Data){ // сохранение/восстановление любого типа переменных
         static type1 copy_data[PARAMS][MAX_EXPERTS_AMOUNT];
         if (mode==SAVE)   copy_data[cnt1][ExpNum]=Data;
         if (mode==LOAD)   Data=copy_data[cnt1][ExpNum];
         cnt1++; 
         }; 
         
      template <typename type0> 
      void EXPERT_PARENT_CLASS::COPY(type0 &array[]){ // сохранение/восстановление массива любого типа переменных
         uint arr_size=ArraySize(array); 
         static type0 copy[][PARAMS][MAX_EXPERTS_AMOUNT];
         ArrayResize(copy,arr_size,0);
         if (mode==SAVE)   for (uint i=0; i<arr_size; i++) copy[i][cnt2][ExpNum]=array[i];
         if (mode==LOAD)   for (uint i=0; i<arr_size; i++) array[i]=copy[i][cnt2][ExpNum];
         cnt2++;
         } 
              
      void EXTERN_VARS(); // ф. обработки внешних переменных (модифицируется в дочерних классах)
      virtual void DATA(string head){} // в разных дочерних классах выполняются разные функции DATA
      virtual void DATA(string name, char& value){} // в разных дочерних классах выполняются разные функции DATA
      virtual void DATA(string name, int& value){}
      virtual void DATA(string name, double& value){}
      virtual void DATA(string name, bool& value){}


   }; 

// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 
//+---------------------------------------------------------------+
//| дочерние классы по соднанию и обработке                       |
//| списка внешних переменных                                     |
//+---------------------------------------------------------------+            
class PRINT_TO_CHART_CLASS : public EXPERT_PARENT_CLASS { // дочерний класс печати внешних переменных на график
   public:     
      virtual void DATA(string head)               {LABEL(head);}                // печать заголовка (... - O U T P U T - ...)
      virtual void DATA(string name, char& value)  {LABEL(name+"="+S0(value));}  // печать списка входных параметров (ATR=4)     
      virtual void DATA(string name, int& value)   {LABEL(name+"="+S0(value));}
      virtual void DATA(string name, double& value){LABEL(name+"="+DoubleToString(value, 6));}
      virtual void DATA(string name, bool& value)  {LABEL(name+"="+S0(value));}
   }PRINT_TO_CHART;

class WRITE_TO_FILE_CLASS : public EXPERT_PARENT_CLASS { // дочерний класс записи внешних переменных в файл
   private: int file;
   public:
      void EXTERN_VARS(int file_index){   // создание дочерней функции с тем же именем, 
         file=file_index;                 // но с внешним параметром индекса файла
         EXTERN_VARS();
         }   
      virtual void DATA(string name, char& value)  {FileWrite(file,name+"=",S0(value));}
      virtual void DATA(string name, int& value)   {FileWrite(file,name+"=",S0(value));}
      virtual void DATA(string name, double& value){FileWrite(file,name+"=",DoubleToString(value, 8));}
      virtual void DATA(string name, bool& value)  {FileWrite(file,name+"=",S0(value));}
   }CREATE_SET_FILE;

class READ_ARRAY_CLASS : public EXPERT_PARENT_CLASS { // дочерний класс создания массива внешних переменных
   private: int index; uchar ExpertNum;
   public:
      void EXTERN_VARS(uchar SetExpertNum){   // создание дочерней функции с тем же именем, 
         index=0;                // но с внешним параметром индекса 
         ExpertNum=SetExpertNum;
         EXTERN_VARS();
         }        
      virtual void DATA(string name, char& value){ // ф. DATA выполняет разные функции в зависимости от дочернего класса
         value=char(EXP[ExpertNum].PRM[index]);    index++;
         }
      virtual void DATA(string name, int& value)   {value=int(EXP[ExpertNum].PRM[index]); index++;}
      virtual void DATA(string name, double& value){value=EXP[ExpertNum].PRM[index]; index++;}
      virtual void DATA(string name, bool& value)  {value=(EXP[ExpertNum].PRM[index] != 0.0); index++;}
   }READ_ARRAY;

class READ_FROM_FILE_CLASS : public EXPERT_PARENT_CLASS {// дочерний класс чтения внешних переменных из файла 
   private: int file;
   public:
      void EXTERN_VARS(int file_index){
         file=file_index;
         EXTERN_VARS();
         }   
      virtual void DATA(string name, char& value)  {value=char(StrToDouble(FileReadString(file)));}
      virtual void DATA(string name, int& value)   {value=int(StrToDouble(FileReadString(file)));}
      virtual void DATA(string name, double& value){value=StrToDouble(FileReadString(file));}
      virtual void DATA(string name, bool& value)  {value=(StrToDouble(FileReadString(file)) != 0.0);}
   }READ_FROM_FILE;  
   
class WRITE_HEAD_CLASS : public EXPERT_PARENT_CLASS { // дочерний класс записи в файл заголовков внешних переменных
   private: int file;
   public:
      void EXTERN_VARS(int file_index){
         file=file_index;
         EXTERN_VARS();
         }   
      virtual void DATA(string name, char& value)  {FileSeek (file,-2,SEEK_END); FileWrite(file,"",name);}
      virtual void DATA(string name, int& value)   {FileSeek (file,-2,SEEK_END); FileWrite(file,"",name);}
      virtual void DATA(string name, double& value){FileSeek (file,-2,SEEK_END); FileWrite(file,"",name);}
      virtual void DATA(string name, bool& value)  {FileSeek (file,-2,SEEK_END); FileWrite(file,"",name);}
   }WRITE_HEAD_TO_FILE;    

class WRITE_PARAM_CLASS : public EXPERT_PARENT_CLASS { // дочерний класс записи в файо значений внешних переменных
   private: int file;
   public:
      void EXTERN_VARS(int file_index){
         file=file_index;
         EXTERN_VARS();
         }   
      virtual void DATA(string name, char& value)  {FileSeek (file,-2,SEEK_END); FileWrite(file,"",value);}
      virtual void DATA(string name, int& value)   {FileSeek (file,-2,SEEK_END); FileWrite(file,"",value);}
      virtual void DATA(string name, double& value){FileSeek (file,-2,SEEK_END); FileWrite(file,"",DoubleToString(value, 8));}
      virtual void DATA(string name, bool& value)  {FileSeek (file,-2,SEEK_END); FileWrite(file,"",value);}
   }WRITE_TO_FILE;

class MAGIC_GEN_CLASS : public EXPERT_PARENT_CLASS { // дочерний класс генерации Magic из внешних переменных
   public:
      void MAGIC_ADD(double value){
         long scaled=(long)MathRound(value*100000.0);
         ulong add=(ulong)(scaled+2147483647);
         MagicLong=MagicLong*1315423911+add+1;
         }
      virtual void DATA(string name, char& value){ // ф. DATA выполняет разные функции в зависимости от дочернего класса
         MAGIC_ADD(value);
         }
      virtual void DATA(string name, int& value)   {MAGIC_ADD(value);}
      virtual void DATA(string name, double& value){MAGIC_ADD(value);}
      virtual void DATA(string name, bool& value)  {MAGIC_ADD(value ? 1 : 0);}
   }MAGIC_GENERATE;
   
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ 

   
