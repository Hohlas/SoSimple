# Trading Expert Algorithm — $o$imple.mq4

> **Назначение**: Source of truth для ИИ-агента, модифицирующего торговый эксперт при внедрении ML-моделей. Документ описывает алгоритм торговых решений, а не вспомогательные функции.
>
> **Точка входа**: `EXPERT::MAIN()` — [MAIN.mqh:116](../../MT/MQL4/Include/MAIN.mqh#L116)
>
> **Активная стратегия**: `iSignal=3` → `ML_TRADE()` (по умолчанию в [$o$imple.mq4:40](../../MT/MQL4/Experts/$o$imple.mq4#L40))
>
> **Последнее обновление**: 2026-03-21

---

## 1. Основной цикл MAIN()

```
EXPERT::MAIN()                           [MAIN.mqh:116]
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
│       │     └── LOCAL_TREND()
│       └── POC_SIMPLE()               ← точка контроля (консолидация)
│
├── 5. if (FINE_TIME()) INPUT()         ← ГЕНЕРАЦИЯ ВХОДОВ [INPUT.mqh]
│       ├── Сброс set.BUY/SEL (обнуление)
│       ├── Трендовый фильтр: UP/DN
│       ├── switch(iSignal):
│       │     case 0: SIG_NULL()
│       │     case 1: SIG_FIRST_LEVELS()
│       │     case 2: SIG_FALSE_BREAK()
│       │     case 3: ML_TRADE() ★      ← ТЕКУЩАЯ СТРАТЕГИЯ [lib_ML_Signal.mqh]
│       │     case 4: SIG_TURTLE()
│       ├── Проверка set.BUY.Sig == GOGO (ML_TRADE не ставит → обход)
│       └── Валидация Stp/Val/Prf + замена ордеров (обходится для ML)
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

## 2. ML-сигналы — ML_TRADE() (iSignal=3)

**Файл**: [lib_ML_Signal.mqh](../../MT/MQL4/Include/lib_ML_Signal.mqh)

### 2.1 Архитектура файлового обмена

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

### 2.2 Формат ml_signals.csv

```
time;signal;pred_up;pred_dn;ratio_up;ratio_dn
2023.01.03 04:00;1;0.477;0.045;10.71;0.09
```

| Поле | Описание |
|------|----------|
| `signal` | 1 (BUY), -1 (SELL), 0 (FLAT) |
| `pred_up` / `pred_dn` | Предсказанные экскурсии вверх/вниз (нормализованные) |
| `ratio_up` | pred_up / pred_dn — чем больше, тем сильнее сигнал на BUY |

### 2.3 Торговая логика ML_TRADE()

```c
void EXPERT::ML_TRADE() {
   // Ленивая инициализация: загрузка CSV при первом вызове
   static bool ml_loaded = false;
   if (!ml_loaded) { ml_loaded = true; ML_INIT(); }
   if (ML_SignalCount <= 0) return;

   int idx = ML_FindSignal(Time[bar]);
   if (idx < 0) return;  // нет сигнала для этого бара

   char sig = ML_Signals[idx];
   if (sig == 0) return;  // FLAT

   // Торговля — напрямую заполняет set.BUY/SEL через DELTA()
   if (sig == 1 && BUY.Typ == 0) {        // BUY.Typ == NONE
      set.BUY.Val = (float)Ask + DELTA(D);
      set.BUY.Stp = set.BUY.Val - DELTA(Stp);
      set.BUY.Prf = set.BUY.Val + DELTA(Prf);
   }
   else if (sig == -1 && SEL.Typ == 0) {   // SEL.Typ == NONE
      set.SEL.Val = (float)Bid - DELTA(D);
      set.SEL.Stp = set.SEL.Val + DELTA(Stp);
      set.SEL.Prf = set.SEL.Val - DELTA(Prf);
   }
}
```

### 2.4 Как ML_TRADE() взаимодействует с INPUT()

ML_TRADE() вызывается внутри INPUT(). Это определяет контекст:

**Что INPUT() делает ДО вызова ML_TRADE():**
1. Сбрасывает `set.BUY/SEL` в ноль — чистый лист
2. Вычисляет трендовый фильтр:
   ```
   UP = (BUY.Typ != MARKET) AND (Trnd.Global >= 0) AND (Trnd.Local >= 0)
   DN = (SEL.Typ != MARKET) AND (Trnd.Global <= 0) AND (Trnd.Local <= 0)
   ```
3. Если `!UP && !DN` → return. ML_TRADE() **не вызывается**.

**Что INPUT() делает ПОСЛЕ вызова ML_TRADE():**
1. Проверяет `set.BUY.Sig != GOGO` → обнуляет UP
2. Проверяет `set.SEL.Sig != GOGO` → обнуляет DN
3. Если `!UP && !DN` → **return** (ранний выход)

ML_TRADE() **не устанавливает** `set.BUY.Sig = GOGO`, поэтому INPUT() выходит рано, **пропуская**:
- Валидацию Stp < Val < Prf
- Логику замены ордеров (ExpirationBars)
- Присвоение `BUY.Typ = SET`

Но `set.BUY.Val` уже заполнен ML_TRADE(), и в MAIN():
```c
if (set.BUY.Val || set.SEL.Val) ORDERS_SET();  // ← ордер БУДЕТ выставлен
```

### 2.5 Параметры, влияющие на ML_TRADE()

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
- `Prf=3` → DELTA(Prf)=1.6*ATR → тейк на 1.6*ATR от входа

**Итого для BUY**: Val=Ask, Stp=Ask-1.6\*ATR, Prf=Ask+1.6\*ATR (R:R = 1:1).

> **pred_up/pred_dn не используются** для расчёта стопов/профитов. Это ключевая точка для улучшения.

### 2.6 Трендовый фильтр и iSignal=3

При дефолтных значениях `iGlb=0`, `iFlt=0`, `iLoc=0`:
- `Trnd.Global` остаётся 0 (SET_BROKEN не обновляет при iGlb=0)
- `Trnd.Local` остаётся 0
- Фильтр: `UP = (BUY.Typ != MARKET && 0 >= 0 && 0 >= 0)` = **true**

→ **Трендовый фильтр фактически отключён** с дефолтными параметрами. ML_TRADE() может генерировать сигналы в обоих направлениях.

### 2.7 Защита от дублирования

ML_TRADE() проверяет `BUY.Typ == 0` (NONE) перед открытием. Поскольку ORDER_CHECK() обнуляет все при отсутствии реальных ордеров, а сигнал из CSV привязан к конкретному `Time[bar]`, дублирование невозможно: один бар → один сигнал.

### 2.8 Доступный контекст на момент вызова ML_TRADE()

К моменту вызова COUNT() уже выполнен, доступны:
- **ATR**: `Atr.Fast`, `Atr.Slow`, `ATR`, `Atr.Lim`
- **Фракталы**: массив `F[0..100]` со всеми характеристиками
- **Ключевые уровни**: `HI`, `LO`, `HI2`, `LO2`, `stpH`, `stpL`
- **Тренд**: `Trnd.Global`, `Trnd.Local`, `Trnd.PicBrk`, `Trnd.Flat`
- **POC**: `PocCnt`, `PocCenter`
- **Текущие ордера**: `BUY.Val/Typ/Stp/Prf`, `SEL.Val/Typ/Stp/Prf`
- **Цены**: `H`, `L`, `C`, `H1`, `L1`, `C1`, `ASK`, `BID`
- **ML-данные**: `ML_PredUp[idx]`, `ML_PredDn[idx]`, `ML_RatioUp[idx]`

---

## 3. Генерация выходных сигналов — OUTPUT()

**Файл**: [OUTPUT.mqh](../../MT/MQL4/Include/OUTPUT.mqh)

OUTPUT() работает для **всех** стратегий, включая ML_TRADE(). Проверяет оба типа ордеров — рыночные (`BUY.Val`) и готовящиеся (`set.BUY.Val`).

### 3.1 Условия закрытия BUY

| Условие | Параметр | Действие |
|---------|----------|----------|
| Импульс угас | `oImp < 0` | Закрытие по текущей, если `(H - BUY.Val) / noise < |oImp| * 0.1` |
| Импульс угас (мягко) | `oImp > 0` | Тейк в безубыток (price=4) |
| Глобальный тренд↓ | `oGlb > 0` AND `Trnd.Global < 0` | CLOSE_BUY(oGlb) — тип зависит от значения oGlb |
| Локальный тренд↓ | `oLoc > 0` AND `Trnd.Local < 0` | CLOSE_BUY(oLoc) |
| Цель достигнута | `Target != 0` AND `BUY.Val > TargetLo` | Закрытие по текущей |
| POC/пик рядом | `oFlt > 0` | Отмена отложенника, если консолидация/пик рядом |

> **Для ML**: Закрытие SEL симметрично. При дефолтных `oImp=0, oGlb=0, oLoc=0, oFlt=0, Target=1` — активен только Target. При `iGlb=0` Trnd.Global=0, условие oGlb/oLoc не срабатывает.

### 3.2 CLOSE_BUY(char price, string comment)

| price | Действие |
|-------|----------|
| > 0 | Подтягивание тейка: 1=закрыть, 2=безубыток, 3=по максимуму, 4+=с припуском |
| < 0 | Подтягивание стопа: -1=за последний пик, -2=в безубыток |
| == 0 | Отмена ордера (удаление отложенника) |

**Важно**: CLOSE_BUY первым делом проверяет `if (set.BUY.Val)` и **обнуляет** его. Это означает, что если OUTPUT() срабатывает на том же баре, что и ML_TRADE(), ордер может быть отменён до выставления.

### 3.3 TRAILING_STOP()

Работает от уровней `stpH`/`stpL` (найденных в LEVELS_FIND_AROUND):
- BUY: если `stpL > 0` и `F[stpL].P - Atr.Lim > BUY.Stp` → подтягиваем стоп
- SEL: зеркально для stpH
- `Trl > 0`: только в плюсе. `Trl < 0`: всегда. `Trl = 0`: отключён (дефолт)

---

## 4. Детекция фракталов — PIC()

**Файл**: [lib_PIC.mqh:140](../../MT/MQL4/Include/lib_PIC.mqh#L140)

### 4.1 ATR_COUNT()

**Файл**: [lib_ATR.mqh](../../MT/MQL4/Include/lib_ATR.mqh)

- **Atr.Fast** = среднее (High-Low) за `a²` баров (дефолт a=5 → 25 баров). Обновляется каждый бар.
- **Atr.Slow** = среднее (High-Low) за `A²` баров (дефолт A=15 → 225 баров). Обновляется раз в день.
- **ATR** = выбранный ATR (Ak=1 → Fast). Дефолт: `ATR = Atr.Fast`.
- **Atr.Lim** = `ATR * PicVal / 100` (дефолт PicVal=20 → `Atr.Lim = ATR * 0.20`) — порог "касания" уровня.

### 4.2 Детекция фракталов (Williams)

На каждом баре проверяется:
- `High[bar + PicPer]` — максимум из `2*PicPer + 1` баров → вершина (Dir=+1)
- `Low[bar + PicPer]` — минимум из `2*PicPer + 1` баров → впадина (Dir=-1)

При обнаружении → `NEW_LEVEL(Dir, Price)`.

### 4.3 NEW_LEVEL() — регистрация фрактала

[lib_PIC.mqh:178](../../MT/MQL4/Include/lib_PIC.mqh#L178). Алгоритм:

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

### 4.4 LEVELS_FIND_AROUND()

[lib_PIC.mqh:371](../../MT/MQL4/Include/lib_PIC.mqh#L371). Два ключевых блока:

**Блок 1: Инкрементальное накопление Up[]/Dn[] для ML** (строки 378-393):
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

### 4.5 Жизненный цикл уровня

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

### 4.6 LOCAL_TREND()

```
Trnd.Local = sign(Trnd.PicBrk) + Trnd.Flat * (iFlt > 0 ? 1 : 0)
```
- **PicBrk**: счётчик пробоев (>0 бычий, <0 медвежий). Обновляется в SET_BROKEN().
- **Flat**: направление выхода из флэта (вошли снизу → ожидаем выход вверх).

---

## 5. Управление ордерами (краткое)

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

## 6. Временные фильтры

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

## 7. Экспорт данных для ML — NERO_CSV_CREATE()

**Файл**: [lib_PIC.mqh:669](../../MT/MQL4/Include/lib_PIC.mqh#L669)

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

## 8. Внешние параметры эксперта

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

---

## 9. Точки улучшения ML-интеграции

### Текущее состояние

ML_TRADE() **работает**: ордера формируются и выставляются. Стопы и профиты рассчитываются через DELTA(Stp)/DELTA(Prf) — **фиксированное** соотношение R:R=1:1 при дефолтных параметрах. Предсказания `pred_up`/`pred_dn` **не используются** для расчётов.

### Рекомендуемые улучшения (по приоритету)

1. **Адаптивные SL/TP из pred_up/pred_dn**
   - `set.BUY.Prf = Ask + ML_PredUp[idx] * k` — тейк пропорционален предсказанной экскурсии вверх
   - `set.BUY.Stp = Ask - ML_PredDn[idx] * k` — стоп пропорционален предсказанной экскурсии вниз
   - Где `k` — коэффициент денормализации (pred нормализованы в pipeline)

2. **Добавить set.BUY.Sig = GOGO** в ML_TRADE()
   - Включает пропущенную валидацию Stp < Val < Prf в INPUT()
   - Включает `BUY.Typ = SET`
   - Включает логику замены ордеров (ExpirationBars)

3. **ML_TRADE() как фильтр классических стратегий**
   - При `iSignal=1`: SIG_FIRST_LEVELS() генерирует сигнал, ML разрешает/блокирует
   - Простая проверка: `if (ML_Signal_for_bar == opposite_direction) set.BUY.Val = 0;`

4. **Динамический OUTPUT на основе ML**
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
| Старый OPEN_BUY (с guard `input_price * target_price == 0`) | INPUT.mqh | Закомментирован (`/* ... */`) |
