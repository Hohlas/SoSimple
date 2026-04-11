# ML Signal Integration: Python -> CSV -> MQL4

> **Назначение**: операционный гайд для текущего `iSignal=3`, где MT4 исполняет уже подготовленный CSV и нужен для parity-check.
>
> Подробная логика эксперта описана в [trading_strategy.md](trading_strategy.md).

---

## 1. Что сейчас считается рабочим путём

Текущий [lib_ML_Signal.mqh](../../MT/MQL4/Include/lib_ML_Signal.mqh):

- не строит больше торговое решение из `up_3..dn_48`;
- не использует старый `ratio`-контур;
- исполняет уже подготовленный `ml_signals.csv`.

Поэтому для `iSignal=3` сейчас правильный вопрос такой:

**какой CSV мы даём в MT4 и насколько его исполнение совпадает с Python?**

---

## 2. Какие CSV понимает MT4

### Вариант A: минимальный CSV

```text
time;signal
2025.01.01 00:00;1
2025.01.01 01:00;0
2025.01.01 02:00;-1
```

Использовать, если отбор уже сделан в Python и MT4 должен только открыть и закрыть сделки.

### Вариант B: полный prediction CSV

Подходит и файл вида:

```text
time;signal;pred_ret_6_dir_atr;pred_ret_12_dir_atr;pred_ret_24_dir_atr;...
```

В этом случае:

- MT4 найдёт `pred_ret_24_dir_atr`;
- при `ML_UseScoreFilter=true` сам применит порог `ML_ScoreThreshold`;
- если колонки нет, score-фильтр для этого файла автоматически отключится.

Важно: этот вариант подходит для простого score-based runtime, но **не заменяет** quantile winner `lb_gt_m`.

Причина:

- quantile winner зависит не только от `pred_ret_24_dir_atr`;
- он зависит от `lb`, восстановленного через `q10/q90 + correction`.

Поэтому для `entry_path_v1_quantile` в MT4 нужно подавать уже заранее отфильтрованный `time;signal`, а не рассчитывать, что `ML_ScoreThreshold` внутри эксперта повторит ту же логику.

---

## 3. Какой CSV класть в тестер

Strategy Tester читает файл:

- `MT/tester/files/ml_signals.csv`

Обычно рабочая последовательность такая:

```bash
# 1. Подготовить CSV в проекте
#    это может быть либо минимальный time;signal,
#    либо полный prediction CSV

# 2. Положить его в tester/files
cp <ваш_источник>.csv MT/tester/files/ml_signals.csv
```

Если у тебя уже настроен симлинк на каталог проекта, достаточно обновить сам источник.

### Для `entry_path_v1_quantile`

Для quantile parity-check правильный путь теперь такой:

```bash
./.venv/bin/python -m API.export_entry_path_v1_quantile_signals \
  --seed-dir ML/reports/entry_path_v1_quantile_robustness/seed_123 \
  --split test \
  --output MT/tester/files/ml_signals.csv \
  --copy-to-mt4
```

Что делает этот CLI:

- читает frozen rule из `entry_path_v1_quantile_filter_selected_rule.json`;
- берёт prediction CSV выбранного split;
- применяет уже замороженный quantile winner без re-fit;
- пишет полный `time;signal`.

Это и есть канонический способ готовить CSV для MT4 по quantile winner.

---

## 4. Как сейчас исполняется сигнал

При `iSignal=3`:

1. эксперт ищет строку по `Time[bar]`;
2. если на баре есть сигнал, открывает сделку на следующем баре по рынку;
3. одновременно держит только одну позицию;
4. закрывает её:
   - по `ML_HoldBars`;
   - либо по обратному сигналу, если включён `ML_AllowReversal`.

Старые `INPUT()`, `OUTPUT()`, `TRAILING_STOP()` и старый `TIMER()` в этом режиме не участвуют.

---

## 5. Рекомендуемые параметры для parity-check

Для базового score-only parity-check:

| Параметр | Значение | Зачем |
|---|---:|---|
| `iSignal` | `3` | включает прямой режим |
| `Risk` | `0` | фиксированный лот в тестере |
| `ML_HoldBars` | `12` | базовое удержание для старого score-only прогона |
| `ML_AllowReversal` | `false` | сначала без досрочного reverse-close |
| `ML_UseScoreFilter` | `true` | если подаётся полный prediction CSV |
| `ML_ScoreThreshold` | `-0.03594103` | текущий frozen-порог winner A@7.5% |
| `ML_BackStopATR` | `50.0` | дальний страховочный SL |

Если подаётся уже заранее отфильтрованный `time;signal`, можно:

- оставить `ML_UseScoreFilter=true` — он сам выключится, если колонки score нет;
- либо явно поставить `ML_UseScoreFilter=false`.

Для `entry_path_v1_quantile` предпочтителен именно этот режим: уже заранее отфильтрованный `time;signal`.

Для текущего quantile parity-check используйте:

| Параметр | Значение | Почему |
|---|---:|---|
| `iSignal` | `3` | прямой parity-mode |
| `ML_HoldBars` | `24` | совпадает с frozen `sequential_hold_bars` |
| `ML_AllowReversal` | `false` | соответствует текущему benchmark-контуру |
| `ML_UseScoreFilter` | `false` | CSV уже предфильтрован в Python |
| `ML_ScoreThreshold` | не используется | quantile winner не сводится к одному score threshold |

---

## 6. Что в этом режиме уже не важно

Для текущего `iSignal=3` больше не являются рабочими параметрами входа:

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

Они остались в эксперте ради совместимости, но не определяют поведение нового прямого режима.

---

## 7. Какие строки искать в логе

Для последующего разбора полезны строки:

```text
MLP BUY ...
MLP SELL ...
MLP CLOSE BUY reason=Timeout ...
MLP CLOSE SELL reason=Timeout ...
MLP CLOSE BUY reason=ReverseSignal ...
MLP CLOSE SELL reason=ReverseSignal ...
MLP SKIP reason=ScoreFilter ...
MLP SKIP reason=PosBlock ...
```

Именно они нужны для сравнения MT4 и Python сделка-в-сделку.

---

## 8. Что делать, если нужен старый runtime

Старый `regression_updn` runtime сохранён отдельно:

- [lib_ML_Signal_back.mqh](../../MT/MQL4/Include/lib_ML_Signal_back.mqh)

Он нужен только для исторических исследований и старых reconciliation-сценариев.

Текущий активный `lib_ML_Signal.mqh` уже описывает другой режим и для old-style `ratio` диагностики не подходит.
