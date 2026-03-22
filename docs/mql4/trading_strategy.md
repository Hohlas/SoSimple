# Trading Expert Algorithm — $o$imple.mq4

> **Назначение этого документа**: Source of truth для ИИ-агента для модификации кода торгового эксперта. Документ описывает алгоритм торговых решений, ключевые структуры данных и контракты функций — чтобы минимизировать необходимость читать исходный код MQL4.

> **Контекст**: Торговый эксперт MT/MQL4/Experts/$o$imple.mq4 изначально создавался как автономная автоматическая торговая система. Но заложенные в него алгоритмы классической торговли от уровней не принесли удовлетворительных результатов. Поэтому было решено включить в торговую логику сигналы открытия позиций на предсказаниях ML.
>
> **Точка входа**: Основной цикл торговли выполняется в [MAIN.mqh](../../MT/MQL4/Include/MAIN.mqh), ф.MAIN().
>
> **Активная ML стратегия**: Интеграция сигналов ML реализована в [lib_ML_Signal.mqh](../../MT/MQL4/Include/lib_ML_Signal.mqh) ф. ML_TRADE().
>
> **Предупреждения**:
> В каталоге MT/MQL4/Include присутствуют не используемые mqh библиотеки.
> В коде остались рудиментарные функции от прошлой (убыточной) логики, которые не будут использоваться для торговли: SIG_FIRST_LEVELS(), SIG_FALSE_BREAK(), SIG_TURTLE(), TARGET_COUNT(), FLAT_DETECT(), ... и другие.
> Код может отличаться от описания в этом документе в связи с активной разработкой. Допускается вносить сюда исправления.

> **Последнее обновление**: 2026-03-22 (v2.0: асимметричный R:R, bypass тренда, диагностика)

---

## 1. Основной цикл MAIN()

```
EXPERT::MAIN()                           [MAIN.mqh]
│
├── 1. EXPERT_SET(ExpNum)               ← загрузка параметров из CSV-строки
├── 2. ORDER_CHECK()                    ← сканирование открытых ордеров MT4 [ORDERS.mqh]
├── 3. TIMER()                          ← закрытие по истечении Tper баров [COUNT.mqh]
├── 4. COUNT()                          ← ИНДИКАТОРНЫЕ РАСЧЁТЫ [COUNT.mqh]
│       ├── MARKET_UPDATE()             ← обновление ASK/BID/Spread
│       ├── PIC()                       ← детекция фракталов + тренд [lib_PIC.mqh]
│       │     ├── ATR_COUNT()           [lib_ATR.mqh]
│       │     ├── Fractal detection (Williams)
│       │     ├── NEW_LEVEL()           ← регистрация нового фрактала
│       │     ├── LEVELS_FIND_AROUND()  ← поиск ключевых уровней + Up[]/Dn[] для ML
│       │     ├── LOCAL_TREND()
│       │     └── NERO_CSV_CREATE() - Запись raw фракталов в Nero.csv для нейросети
│       └── POC_SIMPLE()               ← точка контроля (не используется)
│
├── 5. if (FINE_TIME()) INPUT()         ← ГЕНЕРАЦИЯ ВХОДОВ [INPUT.mqh]
│       ├── Сброс set.BUY/SEL (обнуление)
│       ├── Трендовый фильтр: UP/DN
│       ├── switch(iSignal):
│       │     case 0: SIG_NULL() - (не используется)
│       │     case 1: SIG_FIRST_LEVELS() - (не используется)
│       │     case 2: SIG_FALSE_BREAK() - (не используется)
│       │     case 3: ML_TRADE() ★      ← ТЕКУЩАЯ СТРАТЕГИЯ [lib_ML_Signal.mqh]
│       │     case 4: SIG_TURTLE() - (не используется)
│       ├── Проверка set.BUY.Sig == GOGO (ML_TRADE ставит → валидация проходит)
│       └── Валидация Stp/Val/Prf + замена ордеров
│
├── 6. OUTPUT()                         ← УСЛОВИЯ ЗАКРЫТИЯ [OUTPUT.mqh]
├── 7. TRAILING_STOP()                  ← трейлинг стопа по фракталам [OUTPUT.mqh]
├── 8. MODIFY()                         ← исполнение: close/modify MT4 ордеров [ORDERS.mqh]
├── 9. if (set.BUY.Val || set.SEL.Val)
│       ORDERS_SET()                    ← выставление новых ордеров [ORDERS.mqh]
└── 10. AFTER(ExpNum)                   ← сохранение состояния [SERVICE.mqh]
```

> **Ключевое**: ML_TRADE() вызывается **внутри INPUT()** как `case 3` переключателя `iSignal`. Это не отдельный шаг MAIN(). INPUT() предоставляет трендовый фильтр, сброс set-значений и временной контроль (FINE_TIME).

---

## 2. Ключевые структуры данных

### 2.1 class PRICE — состояние ордера

```c
class PRICE {
   datetime T, Exp;        // время открытия, экспирация
   char     Sig;           // фаза сигнала: NONE=0, WAIT=1, START=2, CONFIRM=3, GOGO=4, BREAK=5, DONE=6
   char     Typ;           // тип: NONE=0, MARKET=1, STOP=2, LIMIT=3, SET=4
   float    Val, Stp, Prf; // цена входа, стоп, тейк
   float    Max, Min;      // макс/мин цена за время жизни ордера
};
```

Экземпляры: `BUY`, `SEL` — текущие реальные ордера. `set.BUY`, `set.SEL` — подготовленные к выставлению.

### 2.2 class PICS (F[0..100]) — фрактальный уровень

```c
class PICS {
   float    P;             // цена уровня
   datetime T;             // время формирования
   char     Dir;           // +1=вершина, -1=впадина
   float    FrntVal;       // амплитуда переднего фронта
   float    BackVal;       // амплитуда заднего фронта
   float    Pwr;           // сила = MIN(FrntVal, BackVal)
   float    PwrSum;        // сумма сил совпадающих пиков
   char     Cnt;           // количество совпадений
   float    Imp;           // импульс = 2*Peak - base1 - base2
   bool     StrongImp;     // Imp/Atr > PicImp
   char     Strong;        // сильный уровень (0/1)
   char     Brk;           // CLEAR=0, TOUCH=1, MIRROR=2, BROKEN=3, ...10
   float    Rev;           // разворотная вершина (0/1)
   float    Tr;            // трендовый уровень (P ± Atr.Fast)
   char     TrBrk;        // статус трендового уровня: NEW=-1, CLEAR=0, BROKEN=1
   float    Atr;           // Atr.Fast на момент формирования
   float    Up[3];         // макс. экскурсия вверх [H12, H24, H48]
   float    Dn[3];         // макс. экскурсия вниз [H12, H24, H48]
   // ... + Back, Near, Frnt (цены), Mir, FLS_BRK Fls, FLT_LEV Flt, TRIANGLE TRG
};
```

### 2.3 class TREND_SIGNALS (Trnd)

```c
class TREND_SIGNALS {
   char  Global;    // глобальный тренд: -1/0/+1
   char  Local;     // локальный тренд: -1/0/+1
   char  PicBrk;    // счётчик пробитых пиков (>0 бычий, <0 медвежий)
   char  Flat;      // направление выхода из флэта
   float DblTop;    // уровень двойной вершины
};
```

### 2.4 class ATR_CLASS (Atr)

```c
class ATR_CLASS {
   float Fast;   // среднее (H-L) за a² баров (дефолт 25)
   float Slow;   // среднее (H-L) за A² баров (дефолт 225), пересчёт раз в день
   float Lim;    // ATR * PicVal / 100 — порог "касания" уровня
   float Max;    // MAX(Fast, Slow)
   float Min;    // MIN(Fast, Slow)
};
```

### 2.5 Глобальные ML-переменные [lib_ML_Signal.mqh]

```c
double   ML_MinRatio    = 2.665; // порог ratio (совпадает с Python θ=2.665)
double   ML_MaxRR       = 4.0;   // максимальный множитель R:R (cap)
bool     ML_BypassTrend = true;  // true = ML-сигналы игнорируют трендовый фильтр

int      ML_SignalCount = 0;     // количество загруженных сигналов
datetime ML_Times[];             // время каждого сигнала (сортировано)
char     ML_Signals[];           // направление: 1=BUY, -1=SELL, 0=FLAT
float    ML_PredUp[], ML_PredDn[];   // предсказанные экскурсии
float    ML_RatioUp[], ML_RatioDn[]; // ratio = pred_up/pred_dn и наоборот

// Диагностические счётчики
int ML_cnt_total, ML_cnt_trend, ML_cnt_lowratio, ML_cnt_posblock;
int ML_cnt_executed, ML_cnt_buy, ML_cnt_sell;
```

### 2.6 Ключевые переменные EXPERT

```c
// Фракталы
PICS F[101];                    // массив уровней (F[0] = текущий новый)
uchar HI, LO;                  // первые уровни сопротивления/поддержки
uchar HI2, LO2;                // серединные уровни
uchar stpH, stpL;              // уровни для трейлинга

// Цены (обновляются в PIC каждый бар)
float H, L, C;                 // High, Low, Close текущего бара
float H1, L1, C1;              // предыдущий бар
float H2, L2, C2;              // пред-предыдущий бар
float ASK, BID;                // текущие котировки
float ATR;                     // выбранный ATR (Fast/Slow/Min/Max по Ak)

// Тренд
TREND_SIGNALS Trnd;
ATR_CLASS Atr;

// Ордера
PRICE BUY, SEL;                // текущие реальные ордера
ORD_TYPE set, mem;             // set = новые к выставлению, mem = бэкап
```

---

## 3. ML-сигналы — ML_TRADE() (iSignal=3)

**Файл**: [lib_ML_Signal.mqh](../../MT/MQL4/Include/lib_ML_Signal.mqh)

### 3.1 Архитектура файлового обмена

```
Python                                    MQL4
─────────                                 ────────
Nero_*_labeled.csv                        ml_signals.csv
  + Transformer model         ──CSV──►      │
  + θ = 2.665 (horizon 12H)                 ▼
                                       ML_INIT()       ← lazy init при первом вызове
                                       ML_FindSignal() ← бинарный поиск по Time[bar]
                                       ML_TRADE()      ← заполнение set.BUY/SEL
```

### 3.2 Формат ml_signals.csv

```
time;signal;pred_up;pred_dn;ratio_up;ratio_dn
2023.01.03 04:00;1;0.477;0.045;10.71;0.09
```

| Поле | Описание |
|------|----------|
| `signal` | 1 (BUY), -1 (SELL), 0 (FLAT) |
| `pred_up` / `pred_dn` | Предсказанные экскурсии вверх/вниз (нормализованные) |
| `ratio_up` | pred_up / pred_dn — чем больше, тем сильнее сигнал на BUY |
| `ratio_dn` | pred_dn / pred_up — чем больше, тем сильнее сигнал на SELL |

### 3.3 Торговая логика ML_TRADE()

```c
void EXPERT::ML_TRADE() {
   // Ленивая инициализация
   static bool ml_loaded = false;
   if (!ml_loaded) { ml_loaded = true; ML_INIT(); }
   if (ML_SignalCount <= 0) return;

   int idx = ML_FindSignal(Time[bar]);
   if (idx < 0) return;

   char sig = ML_Signals[idx];
   if (sig == 0) return;  // FLAT

   ML_cnt_total++;

   // Трендовый фильтр (опциональный bypass)
   if (sig == 1 && !UP)  { ML_cnt_trend++; if (!ML_BypassTrend) return; }
   if (sig == -1 && !DN) { ML_cnt_trend++; if (!ML_BypassTrend) return; }

   // BUY с асимметричным R:R
   if (sig == 1 && BUY.Typ == NONE && SEL.Typ == NONE
       && ML_RatioUp[idx] >= ML_MinRatio) {
      float sl_dist = DELTA(Stp);
      float rr = min(ML_RatioUp[idx] / ML_MinRatio, ML_MaxRR);  // R:R масштабируется по ratio
      if (rr < 1.0) rr = 1.0;
      set.BUY.Sig = GOGO;
      set.BUY.Val = (float)Ask + DELTA(D);
      set.BUY.Stp = set.BUY.Val - sl_dist;
      set.BUY.Prf = set.BUY.Val + sl_dist * rr;  // TP = SL × rr
      ML_cnt_executed++; ML_cnt_buy++;
   }
   // SELL аналогично
   else if (sig == -1 && SEL.Typ == NONE && BUY.Typ == NONE
            && ML_RatioDn[idx] >= ML_MinRatio) {
      float sl_dist = DELTA(Stp);
      float rr = min(ML_RatioDn[idx] / ML_MinRatio, ML_MaxRR);
      if (rr < 1.0) rr = 1.0;
      set.SEL.Sig = GOGO;
      set.SEL.Val = (float)Bid - DELTA(D);
      set.SEL.Stp = set.SEL.Val + sl_dist;
      set.SEL.Prf = set.SEL.Val - sl_dist * rr;
      ML_cnt_executed++; ML_cnt_sell++;
   }
   else { /* SKIP: LowRatio или PosBlock, инкремент счётчиков */ }
}
```

**Ключевые отличия от v1.1:**
- **Асимметричный R:R**: TP = SL × min(ratio / ML_MinRatio, ML_MaxRR). При ratio=10 и ML_MinRatio=2.665 → R:R=1:3.75. Нужен только ~21% win rate для PF>1
- **Bypass трендового фильтра**: ML_BypassTrend=true позволяет ML_TRADE() работать при заблокированном UP/DN
- **Диагностические счётчики**: ML_cnt_total/trend/lowratio/posblock/executed для анализа фильтрации
- Устанавливает `set.BUY.Sig = GOGO` — включает валидацию Stp/Val/Prf в INPUT()
- Проверяет `BUY.Typ == NONE && SEL.Typ == NONE` — запрет одновременных позиций

### 3.4 Как ML_TRADE() взаимодействует с INPUT()

ML_TRADE() вызывается внутри INPUT(). Это определяет контекст:

**Что INPUT() делает ДО вызова ML_TRADE():**
1. Сбрасывает `set.BUY/SEL` в ноль — чистый лист
2. Вычисляет трендовый фильтр:
   ```
   UP = (BUY.Typ != MARKET) AND (Trnd.Global >= 0) AND (Trnd.Local >= 0)
   DN = (SEL.Typ != MARKET) AND (Trnd.Global <= 0) AND (Trnd.Local <= 0)
   ```
3. Если `!UP && !DN` → для iSignal=3: ML_TRADE() **вызывается** (bypass), трендовая проверка выполняется внутри ML_TRADE() с учётом ML_BypassTrend. Для остальных стратегий → return.

**Что INPUT() делает ПОСЛЕ вызова ML_TRADE():**
1. Проверяет `set.BUY.Sig == GOGO` → UP остаётся true (ML_TRADE() ставит GOGO)
2. Проверяет `set.SEL.Sig == GOGO` → DN остаётся true
3. Валидирует: `Stp < Val < Prf`, устанавливает `Typ = SET`
4. Логика замены ордеров (ExpirationBars) — если уже есть отложенник

В MAIN():
```c
if (set.BUY.Val || set.SEL.Val) ORDERS_SET();  // ← ордер выставляется
```

### 3.5 Параметры, влияющие на ML_TRADE()

ML_TRADE() использует ту же параметрическую систему `DELTA()`, что и legacy-стратегии:

```
DELTA(n) = (n+1)² / 10 * ATR    (для n > 0)
DELTA(0) = 0
DELTA(n) = -(n-1)² / 10 * ATR   (для n < 0)
```

| n | DELTA(n) / ATR |
|---|----------------|
| 0 | 0.0 |
| 1 | 0.4 |
| 2 | 0.9 |
| 3 | 1.6 |
| 4 | 2.5 |
| 5 | 3.6 |

**Текущие дефолты** (из $o$imple.mq4):
- `D=0` → DELTA(D)=0 → вход по рыночной цене
- `Stp=3` → DELTA(Stp)=1.6*ATR → стоп на 1.6*ATR от входа

**Асимметричный R:R (v2.0):**
- SL = DELTA(Stp) = 1.6*ATR (фиксирован)
- TP = SL × min(ratio / ML_MinRatio, ML_MaxRR)
- Примеры: ratio=5.33 → R:R=1:2, ratio=10.66 → R:R=1:4 (cap)

**Итого для BUY**: Val=Ask, Stp=Ask-1.6\*ATR, Prf=Ask+1.6\*ATR\*rr (R:R = 1:rr).

### 3.6 Трендовый фильтр и iSignal=3

ML_TRADE() имеет собственную обработку трендового фильтра (v2.0):
- `ML_BypassTrend = true` (дефолт) → трендовый фильтр **не блокирует** ML-сигналы, но считает заблокированные в ML_cnt_trend
- `ML_BypassTrend = false` → классическое поведение: UP/DN блокируют BUY/SELL

В INPUT.mqh добавлен bypass: при `!UP && !DN && iSignal==3` → ML_TRADE() вызывается напрямую.

При дефолтных значениях `iGlb=0`, `iFlt=0`, `iLoc=0` трендовый фильтр фактически неактивен (Trnd.Global=0, Trnd.Local=0 → UP=true, DN=true).

### 3.7 Защита от дублирования

ML_TRADE() проверяет `BUY.Typ == NONE && SEL.Typ == NONE` перед открытием любой позиции. Это значит:
- Нельзя открыть BUY при открытом SELL (и наоборот)
- Нельзя открыть BUY при уже открытом BUY
- Дополнительно: сигнал из CSV привязан к конкретному `Time[bar]`, один бар → один сигнал

### 3.8 Доступный контекст на момент вызова ML_TRADE()

К моменту вызова COUNT() уже выполнен, доступны:
- **ATR**: `Atr.Fast`, `Atr.Slow`, `ATR`, `Atr.Lim`
- **Фракталы**: массив `F[0..100]` со всеми характеристиками
- **Ключевые уровни**: `HI`, `LO`, `HI2`, `LO2`, `stpH`, `stpL`
- **Тренд**: `Trnd.Global`, `Trnd.Local`, `Trnd.PicBrk`, `Trnd.Flat`
- **POC**: `PocCnt`, `PocCenter`
- **Текущие ордера**: `BUY.Val/Typ/Stp/Prf`, `SEL.Val/Typ/Stp/Prf`
- **Цены**: `H`, `L`, `C`, `H1`, `L1`, `C1`, `ASK`, `BID`
- **ML-данные**: `ML_PredUp[idx]`, `ML_PredDn[idx]`, `ML_RatioUp[idx]`, `ML_RatioDn[idx]`

---

## 4. Генерация выходных сигналов — OUTPUT()

**Файл**: [OUTPUT.mqh](../../MT/MQL4/Include/OUTPUT.mqh)

OUTPUT() работает для **всех** стратегий, включая ML_TRADE(). Проверяет оба типа ордеров — рыночные (`BUY.Val`) и готовящиеся (`set.BUY.Val`).

### 4.1 Условия закрытия BUY

| Условие | Параметр | Действие |
|---------|----------|----------|
| Импульс угас | `oImp < 0` | Закрытие по текущей, если `(H - BUY.Val) / noise < |oImp| * 0.1` |
| Импульс угас (мягко) | `oImp > 0` | Тейк в безубыток (price=4) |
| Глобальный тренд↓ | `oGlb > 0` AND `Trnd.Global < 0` | CLOSE_BUY(oGlb) — тип зависит от значения oGlb |
| Локальный тренд↓ | `oLoc > 0` AND `Trnd.Local < 0` | CLOSE_BUY(oLoc) |
| Цель достигнута | `Target != 0` AND `BUY.Val > TargetLo` | Закрытие по текущей |
| POC/пик рядом | `oFlt > 0` | Отмена отложенника, если консолидация/пик рядом |

> **Для ML**: Закрытие SEL симметрично. При дефолтных `oImp=0, oGlb=0, oLoc=0, oFlt=0, Target=0` — OUTPUT() не активен. Позиции закрываются только по SL/TP или TIMER.

### 4.2 CLOSE_BUY(char price, string comment)

| price | Действие |
|-------|----------|
| > 0 | Подтягивание тейка: 1=закрыть, 2=безубыток, 3=по максимуму, 4+=с припуском |
| < 0 | Подтягивание стопа: -1=за последний пик, -2=в безубыток |
| == 0 | Отмена ордера (удаление отложенника) |

**Важно**: CLOSE_BUY первым делом проверяет `if (set.BUY.Val)` и **обнуляет** его. Это означает, что если OUTPUT() срабатывает на том же баре, что и ML_TRADE(), ордер может быть отменён до выставления.

### 4.3 TRAILING_STOP()

Работает от уровней `stpH`/`stpL` (найденных в LEVELS_FIND_AROUND):
- BUY: если `stpL > 0` и `F[stpL].P - Atr.Lim > BUY.Stp` → подтягиваем стоп
- SEL: зеркально для stpH
- `Trl > 0`: только в плюсе. `Trl < 0`: всегда. `Trl = 0`: отключён (дефолт)

---

## 5. Детекция фракталов — PIC()

**Файл**: [lib_PIC.mqh](../../MT/MQL4/Include/lib_PIC.mqh)

### 5.1 ATR_COUNT()

**Файл**: [lib_ATR.mqh](../../MT/MQL4/Include/lib_ATR.mqh)

- **Atr.Fast** = среднее (High-Low) за `a²` баров (дефолт a=5 → 25 баров). Обновляется каждый бар.
- **Atr.Slow** = среднее (High-Low) за `A²` баров (дефолт A=15 → 225 баров). Обновляется раз в день.
- **ATR** = выбранный ATR (Ak=1 → Fast). Дефолт: `ATR = Atr.Fast`.
- **Atr.Lim** = `ATR * PicVal / 100` (дефолт PicVal=20 → `Atr.Lim = ATR * 0.20`) — порог "касания" уровня.

### 5.2 Детекция фракталов (Williams)

На каждом баре проверяется:
- `High[bar + PicPer]` — максимум из `2*PicPer + 1` баров → вершина (Dir=+1)
- `Low[bar + PicPer]` — минимум из `2*PicPer + 1` баров → впадина (Dir=-1)

При обнаружении → `NEW_LEVEL(Dir, Price)`.

### 5.3 NEW_LEVEL() — регистрация фрактала

Алгоритм:

1. **Обход всех слотов F[1..100]**:
   - Вес уровня: `Weight = Pwr * FltNum / Distance / (Brk+1)`
   - Слот с минимальным весом = кандидат на вытеснение (защита: HI, LO, stpH, stpL, активные ложные пробои)
   - Совпадающие уровни (в пределах `Atr.Lim`): накопление `PwrSum`, `Cnt`
   - Глубокий пробой (> `Atr.Max*2`) → MIRROR
   - `FALSE_BREAK(f)` для каждого уровня
   - Обновление `Back`/`BackVal` противолежащих пиков

2. **Запись нового уровня** в слот с минимальным весом:
   - Для вершин: `Frnt = LOWEST(...)`, `Tr = P - Atr.Fast`
   - Для впадин: `Frnt = HIGHEST(...)`, `Tr = P + Atr.Fast`
   - `Imp = 2*Peak - base1 - base2` (симметрия пика)
   - `StrongImp = (Imp/Atr > PicImp)`

3. `FLAT_DETECT()` → `NERO_CSV_CREATE(bar)`

### 5.4 LEVELS_FIND_AROUND()

Два ключевых блока:

**Блок 1: Инкрементальное накопление Up[]/Dn[] для ML**:
```c
int dist = SHIFT(F[f].T) - bar;
if (dist < 0 || dist > 48) continue;  // вне горизонта
if (dist <= 48) { if (hmp > F[f].Up[H48]) F[f].Up[H48] = hmp; ... }
if (dist <= 24) { if (hmp > F[f].Up[H24]) F[f].Up[H24] = hmp; ... }
if (dist <= 12) { if (hmp > F[f].Up[H12]) F[f].Up[H12] = hmp; ... }
```
Эти значения экспортируются в Nero.csv через NERO_CSV_CREATE() и используются как ML-таргеты.

**Блок 2: Поиск ключевых уровней**:

| Переменная | Описание |
|------------|----------|
| **HI** / **LO** | Первые уровни сопротивления/поддержки (Strong, непробитые) |
| **HI2** / **LO2** | Серединные уровни (MidTyp определяет критерий силы) |
| **stpH** / **stpL** | Уровни для трейлинга (достаточный BackVal) |

### 5.5 Жизненный цикл уровня

```
NEW_LEVEL() → CLEAR ──LEV_TOUCH()──► TOUCH ──LEV_BREAK()──► BROKEN ──LEV_CROSS()──► 4..10
                 │                                              │
                 └──────LEV_BREAK()─────────────────────────────┘
                                                                │
              MIRROR ◄── из NEW_LEVEL(), если глубокий пробой ──┘
```

`SET_BROKEN()` при пробое:
- Если пробит HI (при iGlb==1) или HI2 (при iGlb==2) → `Trnd.Global = +1`
- Если пробит LO/LO2 → `Trnd.Global = -1`
- Инкремент `Trnd.PicBrk` (ограничен `iLoc`)
- Запуск `Fls.Phase = WAIT` для сильных уровней

### 5.6 LOCAL_TREND()

```
Trnd.Local = sign(Trnd.PicBrk) + Trnd.Flat * (iFlt > 0 ? 1 : 0)
```
- **PicBrk**: счётчик пробоев (>0 бычий, <0 медвежий). Обновляется в SET_BROKEN().
- **Flat**: направление выхода из флэта (вошли снизу → ожидаем выход вверх).

---

## 6. Управление ордерами

### ORDER_CHECK() [ORDERS.mqh]
Сканирует MT4 ордера по MagicNumber. Заполняет `BUY.Val/Stp/Prf/Typ/T`, `SEL.*`. Вызывается первым в MAIN() — даёт актуальное состояние позиций.

### ORDERS_SET() [ORDERS.mqh]
Вызывается если `set.BUY.Val || set.SEL.Val`:
- `Lot = MM(Stop, CurExp)` — money management по размеру стопа и Risk
- Тип ордера: `Val > ASK` → BUYSTOP, `Val < ASK` → BUYLIMIT, `Val ≈ ASK` → BUY (market)
- `CHECK_RISK()` — проверка максимального риска
- Собственная валидация: `set.BUY.Val - set.BUY.Stp <= StopLevel` → отклонение

### MODIFY() [ORDERS.mqh]
- `BUY.Val == 0` → закрытие рыночного / удаление отложенного
- Изменение SL/TP → `OrderModify()`

---

## 7. Временные фильтры

### FINE_TIME() [COUNT.mqh]
Контролирует разрешённое время торговли:
- `Wknd=1`: запрет в пятницу после 22:00
- `Wknd=2`: запрет в пятницу после 19:00
- `tk > 0`: торговля только в окне Tin..Tout

При запрете: закрывает все позиции, INPUT() **не вызывается** → ML_TRADE() тоже.

### TIMER() [COUNT.mqh]
Закрывает позиции, удерживаемые дольше `Tper` баров:
```
if BUY.Typ==MARKET AND SHIFT(BUY.T) >= Tper → CLOSE_BUY(1, "HoldOverTime")
```

---

## 8. Экспорт данных для ML — NERO_CSV_CREATE()

**Файл**: [lib_PIC.mqh](../../MT/MQL4/Include/lib_PIC.mqh)

Вызывается при формировании каждого нового фрактала. Формат строки:
```
time; signal; predict; ATR; fractal_0; fractal_1; ... fractal_99
```

Каждый `fractal_i` — **18 полей** через `:`:

| # | Поле | Описание |
|---|------|----------|
| 1 | T | Время формирования |
| 2 | P | Цена уровня |
| 3 | Dir | +1 (вершина), -1 (впадина) |
| 4 | FrntVal | Амплитуда переднего фронта |
| 5 | BackVal | Амплитуда заднего фронта |
| 6 | Strong | Признак сильного уровня (0/1) |
| 7 | Brk | Статус пробоя (0..10) |
| 8 | Rev | Разворотная вершина (0/1) |
| 9 | PwrSum | Суммарная сила совпадающих пиков |
| 10 | Cnt | Количество совпадений |
| 11 | Imp | Импульс (симметрия пика) |
| 12-13 | Up[H12], Dn[H12] | Экскурсии за 12 баров |
| 14-15 | Up[H24], Dn[H24] | Экскурсии за 24 бара |
| 16-17 | Up[H48], Dn[H48] | Экскурсии за 48 баров |
| 18 | Atr | Atr.Fast на момент формирования |

### ML pipeline

```
NERO_CSV_CREATE() → Nero.csv → label_main.py → Nero_*_labeled.csv → train.py
                                                                         ↓
                                           generate_signals.py ← transformer_updn_best.pt
                                                  ↓
                                           ml_signals.csv → ML_TRADE() → set.BUY/SEL
```

---

## 9. Внешние параметры эксперта

### Индикаторные (PIC)
| Параметр | Дефолт | Описание |
|----------|--------|----------|
| `PicPer` | 1 | Период детекции фракталов (Williams N-bar) |
| `FltLen` | 10 | Минимальная длина флэта (в барах) |
| `PicCnt` | 2 | Минимальное число совпадающих пиков для флэта |
| `PicPwr` | 9 | Порог силы (Pwr > ATR*PicPwr → Strong) |
| `PicImp` | 1 | Порог импульса (Imp/Atr > PicImp → StrongImp) |
| `Rev` | 0 | 0=все пики, 1=только повышающиеся, 2=BackVal>FrntVal |
| `Days` | 0 | Глубина поиска: >0 ближние, <0 дальние, 0=вся история |
| `MidTyp` | 1 | Серединный уровень: 0=нет, 1=MaxFront, 2=MaxFront*MaxPics, 3=MaxPics, 4=PwrSum |

### ATR
| Параметр | Дефолт | Описание |
|----------|--------|----------|
| `A` | 15 | SlowATR период = A² = 225 баров |
| `a` | 5 | FastATR период = a² = 25 баров |
| `Ak` | 1 | ATR: 0=Slow, 1=Fast, 2=Min, 3=Max |
| `PicVal` | 20 | Atr.Lim = ATR * PicVal / 100 |

### Трендовые
| Параметр | Дефолт | Описание |
|----------|--------|----------|
| `iGlb` | 0 | 0=отключён, 1=пробой первого, 2=пробой серединного → Global |
| `iFlt` | 0 | 0=отключён, >0=выход из флэта влияет на Local |
| `iLoc` | 0 | 0=отключён, max счётчик PicBrk |

### Входные (INPUT)
| Параметр | Дефолт | Описание |
|----------|--------|----------|
| `iSignal` | **3** | **0=null, 1=first_levels, 2=false_break, 3=ML_TRADE, 4=turtle** |
| `D` | 0 | Смещение входа от рыночной цены (DELTA) |
| `Stp` | 3 | Стоп = DELTA(Stp) = 1.6*ATR |
| `Prf` | 3 | Тейк = DELTA(Prf) = 1.6*ATR |
| `Target` | 1 | Целевые уровни: 0=нет, >0=max, <0=avg |

### Выходные (OUTPUT)
| Параметр | Дефолт | Описание |
|----------|--------|----------|
| `oImp` | 0 | 0=отключён. <0: закрытие при угасании импульса, >0: безубыток |
| `oFlt` | 0 | 0=отключён. >0: отмена ордера при POC/пике рядом |
| `oGlb` | 0 | 0=отключён. Закрытие при смене глобального тренда |
| `oLoc` | 0 | 0=отключён. Закрытие при смене локального тренда |
| `Trl` | 0 | 0=отключён. >0: трейлинг только в плюс, <0: всегда |
| `Wknd` | 0 | 0=нет запрета, 1=FOMC, 2=Weekend |

### Временные (TIME)
| Параметр | Дефолт | Описание |
|----------|--------|----------|
| `tk` | 0 | 0=без временного фильтра (GTC), >0=внутридневное окно |
| `T0` | 7 | При tk=0: ExpirationBars=21. При tk>0: начало торгового окна |
| `T1` | 8 | При tk=0: Tper=∞. При tk>0: длительность окна |
| `tp` | 1 | Тип закрытия при запрете: 1=по текущей, 2=безубыток, ... |

### ML
| Параметр | Дефолт | Описание |
|----------|--------|----------|
| `ML_MinRatio` | 5.0 | Минимальный ratio_up/ratio_dn для открытия сделки. Глобальная переменная в lib_ML_Signal.mqh |

---

## 10. Контракты функций

Сигнатуры и описание входов/выходов функций, имеющих прямое отношение к торговому алгоритму.

### Основной цикл

| Сигнатура | Файл | Описание |
|-----------|------|----------|
| `void EXPERT::MAIN()` | MAIN.mqh | Главный цикл: EXPERT_SET → ORDER_CHECK → TIMER → COUNT → INPUT → OUTPUT → TRAILING_STOP → MODIFY → ORDERS_SET → AFTER |
| `bool EXPERT::COUNT()` | COUNT.mqh | Индикаторные расчёты. Вызывает MARKET_UPDATE, PIC, POC_SIMPLE. **Возврат**: false если ATR не готов (недостаточно баров) |
| `bool EXPERT::PIC()` | lib_PIC.mqh | Детекция фракталов Williams. Вызывает ATR_COUNT, NEW_LEVEL, LEVELS_FIND_AROUND, LOCAL_TREND. **Возврат**: false если ATR не готов |

### ML-сигналы

| Сигнатура | Файл | Описание |
|-----------|------|----------|
| `bool ML_INIT()` | lib_ML_Signal.mqh | Загружает ml_signals.csv в глобальные массивы. **Возврат**: true=успех, false=ошибка файла |
| `int ML_FindSignal(datetime barTime)` | lib_ML_Signal.mqh | Бинарный поиск сигнала по времени бара. **Вход**: время бара. **Возврат**: индекс в ML_* массивах или -1 |
| `void EXPERT::ML_TRADE()` | lib_ML_Signal.mqh | Ищет ML-сигнал для Time[bar], заполняет set.BUY/SEL. Проверяет: нет открытых позиций, ratio >= ML_MinRatio. Ставит Sig=GOGO |

### Генерация входов

| Сигнатура | Файл | Описание |
|-----------|------|----------|
| `void EXPERT::INPUT()` | INPUT.mqh | Сброс set, трендовый фильтр UP/DN, диспетчер сигналов (iSignal), валидация Stp/Val/Prf. Вызывает ML_TRADE() при iSignal=3 |
| `void EXPERT::OPEN_BUY(float input_price, float target_price)` | INPUT.mqh | Расчёт Val/Stp/Prf для BUY от уровня. **Вход**: цена уровня, цена цели. **Побочный эффект**: заполняет set.BUY |
| `void EXPERT::OPEN_SELL(float input_price, float target_price)` | INPUT.mqh | Зеркало OPEN_BUY для SEL |
| `float EXPERT::DELTA(int delta)` | INPUT.mqh | Нелинейное смещение цены. **Вход**: целое n. **Возврат**: (n+1)²/10*ATR (n>0), 0 (n=0), -(n-1)²/10*ATR (n<0) |

### Выходы и закрытие

| Сигнатура | Файл | Описание |
|-----------|------|----------|
| `void EXPERT::OUTPUT()` | OUTPUT.mqh | Проверяет условия закрытия: импульс, тренд, цель, POC. Вызывает CLOSE_BUY/SEL |
| `void EXPERT::CLOSE_BUY(char price, string comment)` | OUTPUT.mqh | Закрытие/модификация BUY. **price**: >0=тейк (1=close,2=BE,3=max), <0=стоп (-1=пик,-2=BE), 0=отмена. Обнуляет set.BUY.Val |
| `void EXPERT::CLOSE_SEL(char price, string comment)` | OUTPUT.mqh | Зеркало CLOSE_BUY |
| `void EXPERT::TRAILING_STOP()` | OUTPUT.mqh | Подтягивание стопа по фрактальным уровням stpL/stpH. Trl>0: в плюсе, Trl<0: всегда |
| `bool EXPERT::IMPULSE_UP()` | OUTPUT.mqh | **Возврат**: true если импульс BUY не угас: (H-BUY.Val)/noise > \|oImp\|*0.1 |

### Управление ордерами

| Сигнатура | Файл | Описание |
|-----------|------|----------|
| `void ORDER_CHECK()` | ORDERS.mqh | Сканирует MT4 ордера по MagicNumber. **Побочный эффект**: заполняет BUY/SEL (.Val, .Typ, .Stp, .Prf, .T) |
| `void ORDERS_SET()` | ORDERS.mqh | Выставляет ордера из set.BUY/SEL. Рассчитывает лот через MM(). Определяет тип: BUYSTOP/BUYLIMIT/BUY(market) |
| `void SET_BUY()` | ORDERS.mqh | Размещает один BUY ордер в MT4. 3 попытки. Валидирует дистанции stop/profit |
| `void SET_SEL()` | ORDERS.mqh | Зеркало SET_BUY |
| `void MODIFY()` | ORDERS.mqh | Итерирует ордера по magic. Val==0 → close/delete. Иначе → OrderModify(SL,TP) |
| `void MARKET_UPDATE(string SYM)` | ORDERS.mqh | Обновляет ASK, BID, DIGITS, Spred, StopLevel для символа |

### Временные фильтры

| Сигнатура | Файл | Описание |
|-----------|------|----------|
| `bool FINE_TIME()` | COUNT.mqh | **Возврат**: true=торговля разрешена. Проверяет Wknd (пятница) и tk (окно). При запрете закрывает позиции |
| `void TIMER()` | COUNT.mqh | Закрывает позиции по таймауту: SHIFT(BUY.T) >= Tper → CLOSE_BUY(1, "HoldOverTime") |

### Фрактальный анализ

| Сигнатура | Файл | Описание |
|-----------|------|----------|
| `bool ATR_COUNT()` | lib_ATR.mqh | Расчёт Atr.Fast/Slow/ATR/Lim. **Возврат**: false пока недостаточно баров |
| `void NEW_LEVEL(char Dir, float Price)` | lib_PIC.mqh | Регистрация нового фрактала. **Вход**: Dir=+1/-1, Price. Ищет слабейший слот, записывает F[n], вызывает NERO_CSV_CREATE |
| `void LEVELS_FIND_AROUND()` | lib_PIC.mqh | Обход F[]. Накапливает Up/Dn для ML, находит HI/LO/HI2/LO2/stpH/stpL, обрабатывает пробои через LEV_CHECK |
| `char LEV_CHECK(uchar f)` | lib_PIC.mqh | Диспетчер проверки уровня. Вызывает LEV_TOUCH/LEV_BREAK/LEV_CROSS в зависимости от Brk. **Возврат**: текущий Brk |
| `void SET_BROKEN(uchar f)` | lib_PIC.mqh | Фиксирует пробой уровня. Обновляет Trnd.Global/Local при пробое HI/LO |
| `void LOCAL_TREND()` | lib_PIC.mqh | Trnd.Local = sign(PicBrk) + Flat*(iFlt>0) |
| `void NERO_CSV_CREATE(int cur_bar)` | lib_PIC.mqh | Пишет строку фрактальных данных в Nero.csv. 18 полей на фрактал × 100 фракталов |
| `void POC_SIMPLE()` | lib_PIC.mqh | Трекинг консолидации (Point of Control). PocCnt=длина, PocCenter=центр |

### Инициализация и сервис

| Сигнатура | Файл | Описание |
|-----------|------|----------|
| `int EXPERT::INIT()` | lib_PIC.mqh | Валидация ATR параметров, расчёт периодов, вызов CONSTANT_COUNTER |
| `bool EXPERT_SET(uchar e)` | SERVICE.mqh | Загрузка параметров эксперта из CSV-массива. Валидация Mgc/Name/Sym/Per |
| `float TEST_RESULT(uchar e)` | SERVICE.mqh | Расчёт PF/RF/MO/DD из истории ордеров для оптимизатора. Вычитает 5 крупнейших выигрышей |

---

## 11. Точки улучшения ML-интеграции

### Текущее состояние

ML_TRADE() **работает**: ордера формируются и выставляются. `set.BUY.Sig = GOGO` установлен — валидация в INPUT() проходит корректно. Стопы и профиты рассчитываются через DELTA(Stp)/DELTA(Prf) — **фиксированное** соотношение R:R=1:1 при дефолтных параметрах. Предсказания `pred_up`/`pred_dn` **не используются** для расчётов. `ML_MinRatio=5.0` фильтрует слабые сигналы.

### Рекомендуемые улучшения (по приоритету)

1. **Адаптивные SL/TP из pred_up/pred_dn**
   - `set.BUY.Prf = Ask + ML_PredUp[idx] * k` — тейк пропорционален предсказанной экскурсии вверх
   - `set.BUY.Stp = Ask - ML_PredDn[idx] * k` — стоп пропорционален предсказанной экскурсии вниз
   - Где `k` — коэффициент денормализации (pred нормализованы в pipeline)

2. **ML_TRADE() как фильтр классических стратегий**
   - При `iSignal=1`: SIG_FIRST_LEVELS() генерирует сигнал, ML разрешает/блокирует
   - Простая проверка: `if (ML_Signal_for_bar == opposite_direction) set.BUY.Val = 0;`

3. **Динамический OUTPUT на основе ML**
   - Использовать pred_up/pred_dn для адаптивного трейлинга
   - При pred_up >> pred_dn для открытого BUY: расширить тейк, подтянуть стоп

### Известные неиспользуемые функции

| Функция | Файл | Статус |
|---------|------|--------|
| `SIG_FIRST_LEVELS()` | iSIG_FIRST_LEVELS.mqh | Legacy (iSignal=1) |
| `SIG_FALSE_BREAK()` | iSIG_FALSE_BREAK.mqh | Legacy (iSignal=2) |
| `SIG_TURTLE()` | iSIG_TURTLE.mqh | Legacy (iSignal=4) |
| `TARGET_COUNT()` | lib_PIC.mqh | Определена, но не вызывается в PIC() |
| `FLAT_DETECT()` | lib_Flat.mqh | Вызывается (часть NEW_LEVEL), но для legacy-стратегий |
