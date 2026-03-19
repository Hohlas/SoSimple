//+------------------------------------------------------------------+
//|                                                   lib_ML_API.mqh |
//|                                                   SoSimple       |
//|                                                                  |
//| Библиотека для связи с Python ML API через WebRequest            |
//+------------------------------------------------------------------+
#property strict

#include <MAIN.mqh>

// URL локального сервера ML_API
#define ML_API_URL "http://127.0.0.1:8000/predict"

// Структура ответа от API
struct ML_Response {
    int signal;       // 1 BUY, -1 SELL, 0 FLAT
    double pred_up;
    double pred_dn;
    double ratio_up;
    double ratio_dn;
    double theta;
};

//+------------------------------------------------------------------+
//| Парсинг простого JSON ответа без сторонних библиотек             |
//+------------------------------------------------------------------+
double ParseJsonValue(string json, string key) {
    string search = "\"" + key + "\":";
    int start = StringFind(json, search);
    if (start < 0) return 0.0;
    
    start += StringLen(search);
    int end1 = StringFind(json, ",", start);
    int end2 = StringFind(json, "}", start);
    
    int end = -1;
    if (end1 > 0 && end2 > 0) end = MathMin(end1, end2);
    else if (end1 > 0) end = end1;
    else if (end2 > 0) end = end2;
    
    if (end < 0) return 0.0;
    
    string val_str = StringSubstr(json, start, end - start);
    StringTrimLeft(val_str);
    StringTrimRight(val_str);
    return StringToDouble(val_str);
}

//+------------------------------------------------------------------+
//| Функция запроса сигнала от ML модели                             |
//+------------------------------------------------------------------+
bool Get_ML_Signal(EXPERT &exp, ML_Response &out_response) {
    // 1. Формируем JSON payload вручную для отправки в Python API
    string json = "{\"atr_slow\": " + DoubleToString(exp.Atr.Slow, 8) + ", \"fractals\": [";
    
    for(uchar f = 1; f < 101; f++) {
        string frac_str = "";
        if (exp.F[f].P != 0) {
            frac_str = 
              IntegerToString((int)exp.F[f].T) + ":" +
              DoubleToString(exp.F[f].P, 5) + ":" +
              IntegerToString(exp.F[f].Dir) + ":" +
              DoubleToString(exp.F[f].FrntVal, 5) + ":" +
              DoubleToString(exp.F[f].BackVal, 5) + ":" +
              IntegerToString(exp.F[f].Strong) + ":" +
              IntegerToString(exp.F[f].Brk) + ":" +
              IntegerToString((int)exp.F[f].Rev) + ":" +
              DoubleToString(exp.F[f].PwrSum, 5) + ":" +
              IntegerToString(exp.F[f].Cnt) + ":" +
              DoubleToString(exp.F[f].Imp, 5) + ":" +
              DoubleToString(exp.F[f].Up[0], 5) + ":" + 
              DoubleToString(exp.F[f].Dn[0], 5) + ":" +
              DoubleToString(exp.F[f].Up[1], 5) + ":" + 
              DoubleToString(exp.F[f].Dn[1], 5) + ":" +
              DoubleToString(exp.F[f].Up[2], 5) + ":" + 
              DoubleToString(exp.F[f].Dn[2], 5) + ":" +
              DoubleToString(exp.F[f].Atr, 5);
        }
        json += "\"" + frac_str + "\"";
        if (f < 100) json += ", ";
    }
    json += "]}";
    
    // 2. Параметры для WebRequest
    char post[], result[];
    string headers = "Content-Type: application/json\r\n";
    StringToCharArray(json, post, 0, WHOLE_ARRAY, CP_UTF8);
    // Удаляем null-terminator
    ArrayResize(post, ArraySize(post) - 1); 
    
    string result_headers;
    int timeout = 5000; // 5 секунд таймаут
    
    // 3. Отправка POST запроса
    ResetLastError();
    int res = WebRequest("POST", ML_API_URL, headers, timeout, post, result, result_headers);
    
    if (res != 200) {
        Print("ML API Error: WebRequest failed with code ", res, ". Check 'Allow WebRequest' in MT4 options. Last Error: ", GetLastError());
        return false;
    }
    
    // 4. Парсинг ответа
    string response_str = CharArrayToString(result, 0, WHOLE_ARRAY, CP_UTF8);
    
    out_response.signal   = (int)ParseJsonValue(response_str, "signal");
    out_response.pred_up  = ParseJsonValue(response_str, "pred_up");
    out_response.pred_dn  = ParseJsonValue(response_str, "pred_dn");
    out_response.ratio_up = ParseJsonValue(response_str, "ratio_up");
    out_response.ratio_dn = ParseJsonValue(response_str, "ratio_dn");
    out_response.theta    = ParseJsonValue(response_str, "theta");
    
    return true;
}
