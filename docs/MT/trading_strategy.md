# Trading Expert Algorithm — $o$imple.mq4

> **Назначение этого документа**: короткое и точное описание того, как сейчас работает торговый эксперт MT4 в активном MQL-коде.
>
> **Точка входа**: [MAIN.mqh](../../MT/MQL4/Include/MAIN.mqh), метод `EXPERT::MAIN()`.
>
> **Текущий статус на 2026-04-09**:
> - `iSignal=3` теперь означает **прямой parity-check режим** из [lib_ML_Signal.mqh](../../MT/MQL4/Include/lib_ML_Signal.mqh)
> - старый runtime `regression_updn` сохранён как backup в [lib_ML_Signal_back.mqh](../../MT/MQL4/Include/lib_ML_Signal_back.mqh)
> - `iSignal=5` по-прежнему использует [lib_ML_Signal_TB.mqh](../../MT/MQL4/Include/lib_ML_Signal_TB.mqh)

> **Последнее обновление**: 2026-04-09

---

## 0. Инструкция по тесту

После правок торговой логики:

1. Сменить `VERSION` в [\$o\$imple.mq4](../../MT/MQL4/Experts/$o$imple.mq4#L2).
2. Проверить входные параметры эксперта в `MT/tester/$o$imple.ini`.
3. Положить нужный CSV файл именно в `MT/tester/files/ml_signals.csv`.
4. Запустить тестер вручную.
5. После теста открыть свежий лог `MT/tester/logs/*.log`.
6. Сверить `VERSION` из строки `OnInit() SoSimple.V...`.
7. Для parity-check извлечь строки:
   - `MLP BUY`
   - `MLP SELL`
   - `MLP CLOSE BUY`
   - `MLP CLOSE SELL`
   - `MLP SKIP`

---

## 1. Что сейчас делает `MAIN()`

Актуальный цикл в [MAIN.mqh](../../MT/MQL4/Include/MAIN.mqh#L118):

```c
void EXPERT::MAIN() {
   if (!EXPERT_SET(ExpNum)) return;
   bool ml_direct_mode = (iSignal == 3);
   ORDER_CHECK();

   if (!ml_direct_mode) TIMER();
   if (!COUNT()) return;

   if (FINE_TIME()) {
      if (ml_direct_mode) ML_TRADE();
      else INPUT();
   }

   if (!ml_direct_mode) {
      OUTPUT();
      TRAILING_STOP();
   }

   MODIFY();
   if (set.BUY.Val || set.SEL.Val) ORDERS_SET();
   AFTER(ExpNum);
}
```

Главное отличие от прежнего режима:

- `iSignal` для `ml_direct_mode` читается только после `EXPERT_SET()`, чтобы строка эксперта успевала подменить параметры;
- при `iSignal=3` эксперт **не идёт** через `INPUT()`;
- при `iSignal=3` старые `TIMER()`, `OUTPUT()` и `TRAILING_STOP()` **не участвуют** в управлении сделкой;
- вся логика входа и выхода для parity-check живёт внутри `ML_TRADE()` из текущего [lib_ML_Signal.mqh](../../MT/MQL4/Include/lib_ML_Signal.mqh).

---

## 2. Активный режим `iSignal=3`

### 2.1 Что это за режим

Это прямой исполнитель уже подготовленного CSV для проверки совпадения Python и MT4.

Его задача:

- взять сигнал из `ml_signals.csv`;
- открыть сделку на следующем баре;
- держать не больше `ML_HoldBars`;
- по желанию закрывать по обратному сигналу;
- писать в лог достаточно данных для сверки сделка-в-сделку.

Это **не** старый runtime, где MT4 сам строил `ratio`, `SL` и `TP` из `up_3..dn_48`.

### 2.2 Где вызывается

Функция [ML_TRADE()](../../MT/MQL4/Include/lib_ML_Signal.mqh) вызывается прямо из [MAIN.mqh](../../MT/MQL4/Include/MAIN.mqh#L125) при `iSignal=3`.

### 2.3 Что она делает

1. Один раз загружает `ml_signals.csv`.
2. Ищет строку по времени `Time[bar]`.
3. Если на баре есть сигнал:
   - при пустой позиции готовит рыночный вход;
   - при уже открытой позиции не открывает новую;
   - при `ML_AllowReversal=true` может закрыть позицию по обратному сигналу.
4. Если позиция удерживается дольше `ML_HoldBars`, закрывает её по таймауту.

### 2.4 Временное выравнивание

Практический смысл текущей реализации такой:

- строка CSV с временем `t` относится к только что закрытому бару;
- вход выполняется на новом баре, то есть по сути на `t+1`;
- поэтому этот режим соответствует схеме: **сигнал на баре `t` -> вход на следующем баре**.

---

## 3. Форматы `ml_signals.csv`

Текущий [lib_ML_Signal.mqh](../../MT/MQL4/Include/lib_ML_Signal.mqh) понимает два формата.

### 3.1 Минимальный формат

```text
time;signal
2025.01.01 00:00;1
2025.01.01 01:00;0
2025.01.01 02:00;-1
```

Подходит, если отбор уже сделан в Python и в MT4 нужно только исполнение.

### 3.2 Полный prediction CSV

Подходит и файл вида:

```text
time;signal;pred_ret_6_dir_atr;pred_ret_12_dir_atr;pred_ret_24_dir_atr;...
```

Важно:

- библиотека ищет `pred_ret_24_dir_atr` как 5-ю колонку;
- если колонка есть и включён `ML_UseScoreFilter`, в MT4 дополнительно применяется порог `ML_ScoreThreshold`;
- если колонки нет, score-фильтр автоматически отключается для этого файла.

### 3.3 Дубликаты времени

Если в CSV есть несколько строк с одним и тем же `time`, библиотека оставляет **последнюю**.

---

## 4. Как сейчас открывается сделка

Для `iSignal=3`:

- `signal = 1` -> BUY по текущему `ASK`
- `signal = -1` -> SELL по текущему `BID`
- одновременно может быть только одна активная позиция

`set.BUY` / `set.SEL` заполняются прямо в `ML_TRADE()`, затем сделка проходит через обычные `MODIFY()` и `ORDERS_SET()`.

### Защитный стоп

Текущий режим ставит очень дальний технический стоп:

- BUY: `entry - ML_BackStopATR * ATR`
- SELL: `entry + ML_BackStopATR * ATR`

Он нужен не как торговая логика, а как безопасный способ:

- пройти внутренние проверки ордера;
- корректно посчитать риск и лот;
- не ломать parity-check нулевым `SL`.

Целевой выход при этом всё равно идёт не по этому стопу, а по таймауту или обратному сигналу.

---

## 5. Как сейчас закрывается сделка

### 5.1 Таймаут

Если позиция открыта и:

- `SHIFT(BUY.T) >= ML_HoldBars`
- или `SHIFT(SEL.T) >= ML_HoldBars`

эксперт вызывает закрытие по рынку с причиной `MLP_Timeout`.

### 5.2 Обратный сигнал

Если включён `ML_AllowReversal=true`, то:

- открытый BUY закрывается при новом `signal=-1`;
- открытый SELL закрывается при новом `signal=1`.

Причина в логе: `MLP_ReverseSignal`.

### 5.3 Что в этом режиме НЕ используется

При `iSignal=3` не работают старые выходы из [OUTPUT.mqh](../../MT/MQL4/Include/OUTPUT.mqh):

- `oImp`
- `oGlb`
- `oLoc`
- `oFlt`
- `Target`
- `TRAILING_STOP()`
- старый `TIMER()`

Это сделано специально, чтобы parity-check не искажался старым управлением позицией.

---

## 6. Основные параметры parity-check

Актуальные `extern` в [\$o\$imple.mq4](../../MT/MQL4/Experts/$o$imple.mq4#L58):

| Параметр | Смысл |
|---|---|
| `iSignal=3` | включает прямой parity-check режим |
| `ML_HoldBars` | сколько баров держать сделку |
| `ML_AllowReversal` | закрывать ли позицию по обратному сигналу |
| `ML_UseScoreFilter` | применять ли порог по `pred_ret_24_dir_atr`, если колонка есть |
| `ML_ScoreThreshold` | порог score для текущего winner |
| `ML_BackStopATR` | дальний страховочный SL |

Параметры старого runtime в этом режиме больше не определяют торговое решение:

- `ML_MinRatio`
- `ML_MaxRatio`
- `ML_MaxRR`
- `ML_RR_Mode`
- `ML_RR_Cap`
- `ML_ScaleK`
- `ML_Min_SL_ATR`
- `ML_Filter3`
- `ML_Filter6`
- `ML_Trl_Start_ATR`
- `ML_Trl_Step_ATR`

Они могут оставаться в `.ini`, но для текущего `iSignal=3` не являются рабочими рычагами логики.

---

## 7. Что писать в лог

Новый режим даёт такие строки:

### Вход

- `MLP BUY ...`
- `MLP SELL ...`

Поля:

- `signal_time`
- `entry_time`
- `score`
- `Val`

### Выход

- `MLP CLOSE BUY reason=Timeout ...`
- `MLP CLOSE SELL reason=Timeout ...`
- `MLP CLOSE BUY reason=ReverseSignal ...`
- `MLP CLOSE SELL reason=ReverseSignal ...`

Поля:

- `signal_time`
- `entry_time`
- `exit_time`
- `entry`
- `exit`
- `atr`
- `pnl_atr`

### Пропуск сигнала

- `MLP SKIP reason=ScoreFilter ...`
- `MLP SKIP reason=PosBlock ...`

Эти строки и являются основой для последующего разбора parity-check.

---

## 8. Что осталось в проекте из старого режима

Старый `regression_updn` runtime не удалён, а сохранён как backup:

- [lib_ML_Signal_back.mqh](../../MT/MQL4/Include/lib_ML_Signal_back.mqh)

Именно там осталась старая логика:

- чтение `up_3..dn_48`;
- расчёт `ratio_up / ratio_dn`;
- адаптивные `SL/TP`;
- `Filter3/Filter6`;
- старый `ML_Exit`.

Если понадобится вернуться к старому сценарию, это нужно делать явно и отдельно.

---

## 9. Другие режимы

### `iSignal=5`

Остаётся Triple Barrier режимом через [lib_ML_Signal_TB.mqh](../../MT/MQL4/Include/lib_ML_Signal_TB.mqh).

### `iSignal != 3` и `iSignal != 5`

Идут через старый диспетчер [INPUT.mqh](../../MT/MQL4/Include/INPUT.mqh), затем через обычные `OUTPUT()` и `TRAILING_STOP()`.

---

## 10. Практический вывод

Если цель теста — проверить совпадение MT4 с новым execution loop, ориентироваться нужно только на:

- текущий [lib_ML_Signal.mqh](../../MT/MQL4/Include/lib_ML_Signal.mqh)
- ветку `iSignal=3` в [MAIN.mqh](../../MT/MQL4/Include/MAIN.mqh#L118)
- параметры `ML_HoldBars`, `ML_AllowReversal`, `ML_UseScoreFilter`, `ML_ScoreThreshold`
- лог-строки `MLP BUY / SELL / CLOSE / SKIP`

Если цель — разбирать старые расхождения `regression_updn`, смотреть нужно уже на [lib_ML_Signal_back.mqh](../../MT/MQL4/Include/lib_ML_Signal_back.mqh), а не на активный runtime.
