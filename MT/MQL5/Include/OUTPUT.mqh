#define MAX_REACH 3        // максимальная с открытия
#define NO_LOSS 2          // тейк в безубыток
#define CUR_PRICE 1        // текущая цена
#define LAST_PIC_STOP -1   // стоп за последний пик
#define BREAK_EVEN_STOP -2 // стоп в безубыток
void EXPERT::OUTPUT() {
    // Multi-pos path: iterate every active BUY-side / SELL-side position.
    if (MT5_MaxPositions > 1) {
        for (int i = 0; i < PosCount; i++) {
            if (!Pos[i].active || Pos[i].data.Typ == NONE) continue;
            if (!PositionSelectByTicket(Pos[i].ticket)) continue;
            ENUM_POSITION_TYPE pt = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
            if (pt == POSITION_TYPE_BUY) {              // -------- BUY side --------
                if (iSignal == 3) {
                    if (SHIFT(Pos[i].data.T) >= 12) {
                        CloseBuySide(1, "ML_Timeout(12H)");
                    } else if (BID > Pos[i].data.Val + ATR * ML_Trl_Start_ATR) {
                        float new_sl = (float)(BID - ATR * ML_Trl_Step_ATR);
                        if (new_sl > Pos[i].data.Stp && BID - new_sl > StopLevel) {
                            Pos[i].data.Stp = new_sl;
                            V("ML_TrailBuy_pos" + S0(i), new_sl, bar, clrBlue);
                        }
                    }
                }
                continue;
            }
            if (pt == POSITION_TYPE_SELL) {             // -------- SELL side -------
                if (iSignal == 3) {
                    if (SHIFT(Pos[i].data.T) >= 12) {
                        CloseSellSide(1, "ML_Timeout(12H)");
                    } else if (ASK < Pos[i].data.Val - ATR * ML_Trl_Start_ATR) {
                        float new_sl = (float)(ASK + ATR * ML_Trl_Step_ATR);
                        if (new_sl < Pos[i].data.Stp && new_sl - ASK > StopLevel) {
                            Pos[i].data.Stp = new_sl;
                            AV("ML_TrailSel_pos" + S0(i), new_sl, bar, clrRed);
                        }
                    }
                }
                continue;
            }
        }
        ERROR_CHECK(__FUNCTION__);
        return;
    }
    // CLOSE BUY
    if (BUY.Val || set.BUY.Val) { // если есть (рыночные / отложные / готовящиеся к открытию) ордера
        if (iSignal != 3) {
            if (oImp < 0 && !IMPULSE_UP())
                CLOSE_BUY(1, "ImpulseOver"); // отсутствие резкого отскока после входа = закрытие по текущей цене
            if (oImp > 0 && !IMPULSE_UP())
                CLOSE_BUY(4, "ImpulseOver"); // отсутствие резкого отскока после входа = тейк в безубыток
            if (oGlb && Trnd.Global < 0)
                CLOSE_BUY(oGlb, "Global<0"); // смена глобального тренда
            if (oLoc && Trnd.Local < 0)
                CLOSE_BUY(oLoc, "Local<0"); // смена локального тренда (пробитие нескольких пиков)
            if (Target && BUY.Val > TargetLo)
                CLOSE_BUY(1, "TargetLo");
            if (oFlt && POC_CLOSE_TO_BUY())
                CLOSE_BUY(1, reason + "NearBuy");
        } else if (BUY.Typ == MARKET) {
            if (SHIFT(BUY.T) >= 12) {
                CLOSE_BUY(1, "ML_Timeout(12H)");
            } else if (BID > BUY.Val + ATR * ML_Trl_Start_ATR) {
                float new_sl = (float)(BID - ATR * ML_Trl_Step_ATR);
                if (new_sl > BUY.Stp && BID - new_sl > StopLevel) {
                    BUY.Stp = new_sl;
                    V("ML_TrailBuy", new_sl, bar, clrBlue);
                }
            }
        }
    }
    // CLOSE SELL
    if (SEL.Val || set.SEL.Val) {
        if (iSignal != 3) {
            if (oImp < 0 && !IMPULSE_DN())
                CLOSE_SEL(1, "ImpulseOver"); // отсутствие резкого отскока после входа = закрытие по текущей цене
            if (oImp > 0 && !IMPULSE_DN())
                CLOSE_SEL(4, "ImpulseOver"); // отсутствие резкого отскока после входа = тейк в безубыток
            if (oGlb && Trnd.Global > 0)
                CLOSE_SEL(oGlb, "Global>0"); // смена глобального тренда
            if (oLoc && Trnd.Local > 0)
                CLOSE_SEL(oLoc, "Local>0"); // смена локального тренда
            if (Target && SEL.Val < TargetHi)
                CLOSE_SEL(1, "TargetHi");
            if (oFlt && POC_CLOSE_TO_SEL())
                CLOSE_SEL(1, reason + "NearSell");
        } else if (SEL.Typ == MARKET) {
            if (SHIFT(SEL.T) >= 12) {
                CLOSE_SEL(1, "ML_Timeout(12H)");
            } else if (ASK < SEL.Val - ATR * ML_Trl_Start_ATR) {
                float new_sl = (float)(ASK + ATR * ML_Trl_Step_ATR);
                if (new_sl < SEL.Stp && new_sl - ASK > StopLevel) {
                    SEL.Stp = new_sl;
                    AV("ML_TrailSel", new_sl, bar, clrRed);
                }
            }
        }
    }
    ERROR_CHECK(__FUNCTION__);
}
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
bool EXPERT::IMPULSE_UP() { // наличие импульса после открытия.
    if (BUY.Typ != MARKET || SHIFT(BUY.T) == 1)
        return (true);                          // только для открытых ордеров начиная со второго бара
    double noise = BUY.Val - Low[SHIFT(BUY.T)]; // импульс после открытия  (Shift=1 бар входа, Shift=2 следующий)
    for (int i = bar; i < SHIFT(BUY.T); i++)
        noise += (High[i] - Low[i]);                                         // шум  в барах
    AV("BuyImpulse=" + S4(H - BUY.Val) + " / " + S4(noise), L, bar, clrGray); //
    if ((H - BUY.Val) / noise > MathAbs(oImp) * 0.1)
        return (true); // сигнал/шум в норме
    else
        return (false);
}
bool EXPERT::IMPULSE_DN() { // наличие импульса после открытия
    if (SEL.Typ != MARKET || SHIFT(SEL.T) == 1)
        return (true);                           // только для открытых ордеров начиная со второго бара
    double noise = High[SHIFT(SEL.T)] - SEL.Val; // импульс после открытия
    for (int i = bar; i < SHIFT(SEL.T); i++)
        noise += (High[i] - Low[i]); // шум  в барах
    V("SelImpulse=" + S4(SEL.Val - L) + " / " + S4(noise), H, bar, clrGray);
    if ((SEL.Val - L) / noise > MathAbs(oImp) * 0.1)
        return (true); // сигнал/шум в норме
    else
        return (false);
}
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
bool EXPERT::POC_CLOSE_TO_BUY() { // цена "отдохнула" (пик или консолидация) перед ордером
    if (BUY.Typ == MARKET)
        return (false);                         // рыночные ордера не трогаем
    float OrdPrice = MAX(BUY.Val, set.BUY.Val), // либо установленная лимитка, либо новый ордер до выставления
        delta = float(oFlt * Atr.Fast / 2);
    if (OrdPrice == 0)
        return (false);
    if (PocCnt > 3 && PocCenter - OrdPrice < delta + Atr.Fast) {
        reason = "Poc";
        V("Poc", PocCenter, bar, clrGray);
        return (true);
    }
    if (F[n].P - OrdPrice < delta && F[n].T > BUY.T) {
        reason = "Pic";
        V("Pic", F[n].P, bar, clrGray);
        return (true);
    }
    return (false);
}
bool EXPERT::POC_CLOSE_TO_SEL() { // цена "отдохнула" (пик или консолидация) перед ордером
    if (SEL.Typ == MARKET)
        return (false);
    float OrdPrice = MAX(SEL.Val, set.SEL.Val),
          delta = float(oFlt * Atr.Fast / 2);
    if (OrdPrice == 0)
        return (false);
    if (PocCnt > 3 && OrdPrice - PocCenter < delta + Atr.Fast) {
        reason = "Poc";
        V("Poc", PocCenter, bar, clrGray);
        return (true);
    }
    if (OrdPrice - F[n].P < delta && F[n].T > SEL.T) {
        reason = "Pic";
        V("Pic", F[n].P, bar, clrGray);
        return (true);
    }
    return (false);
}
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// Multi-position close-side helpers (active when MT5_MaxPositions > 1).
// Iterate all matching side positions and apply the same close/move logic.
// 'price' code semantics match CLOSE_BUY/SEL (1=current, 2=break-even, 3=max,
// default=offset from current; negative = trailing stop offsets).
void EXPERT::CloseBuySide(char price, string comment) {
   for (int i = 0; i < PosCount; i++) {
      if (!Pos[i].active || Pos[i].data.Typ == NONE) continue;
      if (price == 0) { Pos[i].data.Val = 0; continue; }
      // Get live side via PositionSelectByTicket (MT5) — works for multi-pos
      if (!PositionSelectByTicket(Pos[i].ticket)) continue;
      ENUM_POSITION_TYPE pt = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      if (pt != POSITION_TYPE_BUY) continue;
      if (Pos[i].data.Typ != MARKET) {           // pending -> mark for delete
         X("DelPosBUY" + ORDTYP(Pos[i].data.Typ) + ": " + comment, Pos[i].data.Val, bar - 1, clrRed);
         Pos[i].data.Val = 0;
         continue;
      }
      if (price > 0) {                  // adjust take-profit
         float NewProfit = BID;
         switch (price) {
            case 1:  Pos[i].data.Val = 0; break;
            case 2:  NewProfit = float(MAX(BID, Pos[i].data.Val)); break;
            case 3:  NewProfit = Pos[i].data.Max; break;
            default: NewProfit = float(MAX(BID + Atr.Lim * (price - 3), Pos[i].data.Val + Atr.Lim));
         }
         if (NewProfit < Pos[i].data.Prf || Pos[i].data.Prf == 0) Pos[i].data.Prf = NewProfit;
         if (NewProfit - BID < StopLevel) Pos[i].data.Val = 0;
         X("CloseBuySide moveProfit: " + comment, NewProfit, bar - 1, clrRed);
      } else {                          // trailing stop
         float NewStop = 0;
         switch (price) {
            case -1: NewStop = F[lo].P - Atr.Lim; break;
            case -2: NewStop = Pos[i].data.Val; break;
            default: NewStop = float(BID + Atr.Lim * price);
         }
         if (NewStop > Pos[i].data.Stp && BID - NewStop > StopLevel) Pos[i].data.Stp = NewStop;
         X("CloseBuySide moveStop: " + comment, NewStop, bar - 1, clrRed);
      }
   }
}
void EXPERT::CloseSellSide(char price, string comment) {
   for (int i = 0; i < PosCount; i++) {
      if (!Pos[i].active || Pos[i].data.Typ == NONE) continue;
      if (price == 0) { Pos[i].data.Val = 0; continue; }
      if (!PositionSelectByTicket(Pos[i].ticket)) continue;
      ENUM_POSITION_TYPE pt = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      if (pt != POSITION_TYPE_SELL) continue;
      if (Pos[i].data.Typ != MARKET) {
         X("DelPosSELL" + ORDTYP(Pos[i].data.Typ) + ": " + comment, Pos[i].data.Val, bar - 1, clrRed);
         Pos[i].data.Val = 0;
         continue;
      }
      if (price > 0) {
         float NewProfit = ASK;
         switch (price) {
            case 1:  Pos[i].data.Val = 0; break;
            case 2:  NewProfit = float(MIN(ASK, Pos[i].data.Val)); break;
            case 3:  NewProfit = Pos[i].data.Min; break;
            default: NewProfit = float(MIN(ASK - Atr.Lim * (price - 3), Pos[i].data.Val - Atr.Lim));
         }
         if (NewProfit > Pos[i].data.Prf || Pos[i].data.Prf == 0) Pos[i].data.Prf = NewProfit;
         if (ASK - NewProfit < StopLevel) Pos[i].data.Val = 0;
         X("CloseSellSide moveProfit: " + comment, NewProfit, bar - 1, clrRed);
      } else {
         float NewStop = 0;
         switch (price) {
            case -1: NewStop = F[hi].P + Atr.Lim; break;
            case -2: NewStop = Pos[i].data.Val; break;
            default: NewStop = float(ASK - Atr.Lim * price);
         }
         if (Pos[i].data.Stp < NewStop && NewStop - ASK > StopLevel) Pos[i].data.Stp = NewStop;
         X("CloseSellSide moveStop: " + comment, NewStop, bar - 1, clrRed);
      }
   }
}

void EXPERT::CLOSE_BUY(char price, string comment) { //
    if (MT5_MaxPositions > 1) { CloseBuySide(price, comment); return; }
    if (set.BUY.Val) {                               // отмена ордера до установки
        X("Del set.Buy: " + comment, set.BUY.Val, bar - 1, clrRed);
        set.BUY.Val = 0;
    }
    if (BUY.Typ == NONE || price == 0)
        return;
    if (BUY.Typ != MARKET) { // отложенный ордер
        X("Del BUY" + ORDTYP(BUY.Typ) + ": " + comment, BUY.Val, bar - 1, clrRed);
        BUY.Val = 0;
        return;
    }
    if (price > 0) {           // двигаем тейк
        float NewProfit = BID; //
        switch (price) {       // тип цены закрытия
        case 1:
            BUY.Val = 0;
            break; // по текущей
        case 2:
            NewProfit = MAX(BID, BUY.Val);
            break; // безубыток или лучше
        case 3:
            NewProfit = BUY.Max;
            break; // по максимально достигнутой цене
        default:
            NewProfit = MAX(BID + Atr.Lim * (price - 3), BUY.Val + Atr.Lim); // c припуском от текущей, но в плюс
        }
        if (NewProfit < BUY.Prf || BUY.Prf == 0)
            BUY.Prf = NewProfit; // подтягиваем тейк
        if (NewProfit - BID < StopLevel)
            BUY.Val = 0; // тейк недопустимо близко к цене, просто закрываемся
        X("CloseBuy by moveProfit: " + comment, NewProfit, bar - 1, clrRed);
    } else { // подтягиваем стоп
        float NewStop = 0;
        switch (price) {
        case -1:
            NewStop = F[lo].P - Atr.Lim;
            break; // стоп за последний пик
        case -2:
            NewStop = BUY.Val;
            break; // стоп в безубыток
        default:
            NewStop = BID + Atr.Lim * price; // подтягиваем стоп на 3..5 Atr.Lim
        }
        if (NewStop > BUY.Stp && BID - NewStop > StopLevel)
            BUY.Stp = NewStop;
        X("CloseBuy by moveStop: " + comment, NewStop, bar - 1, clrRed);
    }
}
void EXPERT::CLOSE_SEL(char price, string comment) {
    if (MT5_MaxPositions > 1) { CloseSellSide(price, comment); return; }
    if (set.SEL.Val) { // отмена ордера до установки
        X("Del set.Sel: " + comment, set.SEL.Val, bar - 1, clrRed);
        set.SEL.Val = 0;
    }
    if (SEL.Typ == NONE || price == 0)
        return;
    if (SEL.Typ != MARKET) { // отложник
        X("Del SELL" + ORDTYP(SEL.Typ) + ": " + comment, SEL.Val, bar - 1, clrRed);
        SEL.Val = 0;
        return;
    }
    if (price > 0) { // двигаем тейк
        float NewProfit = ASK;
        switch (price) {
        case 1:
            SEL.Val = 0;
            break; // по текущей
        case 2:
            NewProfit = MIN(ASK, SEL.Val);
            break; // не хуже чем безубыток
        case 3:
            NewProfit = SEL.Min;
            break; // по минимально достигнутой цене
        default:
            NewProfit = MIN(ASK - Atr.Lim * (price - 3), SEL.Val - Atr.Lim); // с припуском от текущей
        }
        if (NewProfit > SEL.Prf || SEL.Prf == 0)
            SEL.Prf = NewProfit;
        if (ASK - NewProfit < StopLevel)
            SEL.Val = 0;
        X("CloseSELL by moveProfit: " + comment, NewProfit, bar - 1, clrRed);
    } else { // подтягиваем стоп
        float NewStop = 0;
        switch (price) {
        case -1:
            NewStop = F[hi].P + Atr.Lim;
            break; // стоп за последний пик
        case -2:
            NewStop = SEL.Val;
            break; // стоп в безубыток
        default:
            NewStop = ASK - Atr.Lim * price; // подтягиваем стоп на 3..5 Atr.Lim
        }
        if (SEL.Stp < NewStop && NewStop - ASK > StopLevel)
            SEL.Stp = NewStop;
        X("CloseSELL by moveStop: " + comment, NewStop, bar - 1, clrRed);
    }
}

// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
void EXPERT::TRAILING_STOP() { //    - T R A I L I N G   S T O P -
    if (Trl == 0) return;
    // Multi-pos path: iterate all positions, apply per-position trailing.
    if (MT5_MaxPositions > 1) {
        float TrlBuy = 0, TrlSel = 0;
        if (stpL > 0) TrlBuy = F[stpL].P - Atr.Lim;
        if (stpH > 0) TrlSel = F[stpH].P + Atr.Lim;
        for (int i = 0; i < PosCount; i++) {
            if (!Pos[i].active || Pos[i].data.Typ != MARKET) continue;
            if (!PositionSelectByTicket(Pos[i].ticket)) continue;
            ENUM_POSITION_TYPE pt = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
            if (pt == POSITION_TYPE_BUY && TrlBuy > 0 &&
                TrlBuy > Pos[i].data.Stp && (TrlBuy > Pos[i].data.Val || Trl < 0)) {
                AV("TRAILING_BUY_pos" + S0(i) + ", Back=" + S4(F[stpL].BackVal), TrlBuy, bar, clrBlue);
                Pos[i].data.Stp = TrlBuy;
            } else if (pt == POSITION_TYPE_SELL && TrlSel > 0 &&
                       TrlSel < Pos[i].data.Stp && (TrlSel < Pos[i].data.Val || Trl < 0)) {
                V("TRAILING_SELL_pos" + S0(i) + " " + DTIME(F[stpH].T), TrlSel, bar, clrRed);
                Pos[i].data.Stp = TrlSel;
            }
        }
        ERROR_CHECK(__FUNCTION__);
        return;
    }
    // Backcompat path (MT5_MaxPositions == 1): legacy singleton BUY/SEL.
    if (BUY.Typ != MARKET && SEL.Typ != MARKET)
        return;
    float TrlBuy = 0, TrlSel = 0; //
    if (stpL > 0)
        TrlBuy = F[stpL].P - Atr.Lim;
    if (stpH > 0)
        TrlSel = F[stpH].P + Atr.Lim;

    if (BUY.Typ == MARKET && TrlBuy > 0 && TrlBuy > BUY.Stp && (TrlBuy > BUY.Val || Trl < 0)) { //
        AV("TRAILING_BUY, Back=" + S4(F[stpL].BackVal), TrlBuy, bar, clrBlue);
        BUY.Stp = TrlBuy;
    }
    if (SEL.Typ == MARKET && TrlSel > 0 && TrlSel < SEL.Stp && (TrlSel < SEL.Val || Trl < 0)) { //
        V("TRAILING_SELL " + DTIME(F[stpH].T), TrlSel, bar, clrRed);
        SEL.Stp = TrlSel;
    }
    ERROR_CHECK(__FUNCTION__);
}

// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
/*
void EXPERT::POC_CLOSE_TO_ORDER(){// УДАЛЕНИЕ ОТЛОЖНИКА ЕСЛИ ПЕРЕД НИМ ФОРМИРУЕТСЯ ФЛЭТ.
   if (oFlt==0) return;   //
   float Near=float(oFlt*Atr.Fast/2);
   if (SEL.Typ==LIMIT || set.SEL.Val){ // пик (poc) перед зоной продажи = цена "отдохнула"
      float price=set.SEL.Val+SEL.Val;
      if (price-PocCenter<Near+ATR/2 && PocCnt>2)   CLOSE_SEL(0,"PocNear"); //{set.SEL.Sig=0; SEL.Val=0; set.SEL.Val=0;  X("PocNearSel", PocCenter, bar+1, clrPurple);} // перед лимиткой cформировалось уплотнение из нескольких бар
      if (price-F[n].P<Near && F[n].T>SEL.T)        CLOSE_SEL(0,"PicNear"); //{set.SEL.Sig=0; SEL.Val=0; set.SEL.Val=0;  X("PicNearSel", F[n].P,    bar+1, clrRed);}    // или пик
      }
   if (BUY.Typ==LIMIT || set.BUY.Val){  // пик перед зоной продажи = цена "отдохнула"
      float price=set.BUY.Val+BUY.Val;
      if (PocCenter-price<Near+ATR/2 && PocCnt>2)   CLOSE_BUY(0,"PocNear"); //{set.BUY.Sig=0; BUY.Val=0; set.BUY.Val=0;  X("PocNearBuy", PocCenter, bar+1, clrPurple);}
      if (F[n].P-price<Near && F[n].T>BUY.T)        CLOSE_BUY(0,"PicNear"); //{set.BUY.Sig=0; BUY.Val=0; set.BUY.Val=0;  X("PicNearBuy", F[n].P,    bar+1, clrRed);}
   }  }
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ
// ЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖЖ


void EXPERT::CLOSE_BUY(float ClosePrice, float MinProfit, string Reason){
   float mark=BUY.Val+mem.BUY.Val;   // запоминаем для постановки крестика
   mem.BUY.Val=0;  // удаление отложников
   if (BUY.Typ!=MARKET) BUY.Val=0;
   else{
      if (ClosePrice<BUY.Val+MinProfit) ClosePrice=BUY.Val+MinProfit; // двинем выход вверх, если требует жаба
      mark=ClosePrice;
      if (ClosePrice<BUY.Prf || BUY.Prf==0){ // если выход ниже профит таргета, или таргета нет вовсе
         if (ClosePrice-Bid<ATR/4)  BUY.Val=0;
         else                       BUY.Prf=ClosePrice;
      }  }
   if (mark) X(Reason+"/CloseBuy", mark, 0, clrRed);   // Print("CloseBuy=",CloseBuy," Buy.Val=",BUY.Val);
   }//ERROR_CHECK(__FUNCTION__+Reason);

void EXPERT::CLOSE_SEL(float ClosePrice, float MinProfit, string Reason){
   float mark=SEL.Val+mem.SEL.Val;   // запоминаем для постановки крестика
   mem.SEL.Val=0;  // удаление отложников
   if (SEL.Typ!=MARKET) SEL.Val=0;
   else{
      if (ClosePrice>SEL.Val-MinProfit) ClosePrice=SEL.Val-MinProfit; // двинем выход вверх, если требует жаба
      mark=ClosePrice;
      if (ClosePrice>SEL.Prf || SEL.Prf==0){ // если выход ниже профит таргета, или таргета нет вовсе
         if (Ask-ClosePrice<ATR/4)  SEL.Val=0;
         else                       SEL.Prf=ClosePrice;
      }  }
   if (mark) X(Reason+"/CloseSel", mark, 0, clrRed);   // Print("CloseBuy=",CloseBuy," Buy.Val=",BUY.Val);
   }//ERROR_CHECK(__FUNCTION__+Reason);
*/
