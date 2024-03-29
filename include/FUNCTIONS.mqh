   
 
   
template <typename type0> 
type0 ArrMax(type0 &arr[]){ 
   uint size=ArraySize(arr); 
   if (size==0) return(0);           
   type0 max=arr[0]; 
   for (uint i=1; i<size; i++) 
      if(max<arr[i]) max=arr[i]; 
   return(max); 
   }
   
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
     
#define  LOAD  1     
#define  SAVE  2
   
class COPY_CLASS{
   #define  MAX_PARAMETERS_AMOUNT 100 
   #define  EXPERTS_TOTAL 100 
   private:
         uchar ExpNum, cnt, cnt_arr, mode; 
   public:
      void SET_MODE(uchar SetMode, uchar SetExpertNum) {
         ExpNum=SetExpertNum; 
         cnt=0; cnt_arr=0;
         mode=SetMode; 
         if (mode==LOAD) Print("MODE=LOAD");
         if (mode==SAVE) Print("MODE=SAVE");
         }
         
      template <typename type1>     
      void DATA(type1 &Data){ // Copy any type of data
         static type1 copy_data[MAX_PARAMETERS_AMOUNT][EXPERTS_TOTAL];
         if (mode==SAVE)   copy_data[cnt][ExpNum]=Data;
         if (mode==LOAD)   Data=copy_data[cnt][ExpNum];
         Print("cnt=",cnt);
         cnt++; 
         }; 
         
      template <typename type0> 
      void DATA(type0 &arr[]){ // Copy arrays
         uint size=ArraySize(arr); 
         static type0 copy[][MAX_PARAMETERS_AMOUNT][EXPERTS_TOTAL];
         ArrayResize(copy,size,0);
         if (mode==SAVE)   for (uint i=0; i<size; i++) copy[i][cnt_arr][ExpNum]=arr[i];
         if (mode==LOAD)   for (uint i=0; i<size; i++) arr[i]=copy[i][cnt_arr][ExpNum];
         Print("cnt_arr=",cnt_arr);
         cnt_arr++;
         }      
 
   }COPY(); 