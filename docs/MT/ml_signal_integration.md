# ML Signal Integration: Python -> CSV -> MQL4

> **Назначение**: операционный гайд для текущего `iSignal=3`, где MT4 исполняет уже подготовленный CSV и нужен для parity-check.
>
> Подробная логика эксперта описана в [trading_strategy.md](trading_strategy.md).
> Daily reconciliation описан в [telemetry_daily_reconciliation.py.md](../ML/telemetry_daily_reconciliation.py.md).
> Online watcher описан в [telemetry_signal_watcher.py.md](../API/telemetry_signal_watcher.py.md).
> Если нужен один документ с общим operational-контекстом, начинать лучше с [trading_strategy.md](trading_strategy.md): он связывает MQL, `#.csv`, watcher и сверку.

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

### Для `entry_path_v1`

Для текущего live-safe кандидата `entry_path_v1_live_safe + A @ 7.5%` не
использовать seed-specific `entry_path_trade_filter_selected_rule.json`
напрямую: у seed 42 он может содержать auto-winner `B`, а production baseline
зафиксирован как `A`.

Каноническая подготовка MT4 parity export:

```bash
./.venv/bin/python -m ML.prepare_entry_path_mt4_parity \
  --output-dir ML/reports/mt4_entry_path_v1_live_safe_parity \
  --copy-to-mt4
```

Эта команда:

- строит frozen rule `A @ 7.5%` по validation predictions;
- применяет его к test predictions;
- пишет `ML/reports/mt4_entry_path_v1_live_safe_parity/ml_signals.csv`;
- копирует тот же файл в `MT/tester/files/ml_signals.csv` и
  `MT/MQL4/Files/ml_signals.csv`;
- пишет metadata с threshold, counts и sha256.

Legacy/general consumer для уже готового frozen rule:

```bash
./.venv/bin/python -m API.export_entry_path_v1_signals \
  --predictions ML/reports/entry_path_test_predictions.csv \
  --rule-path ML/reports/entry_path_trade_filter_selected_rule.json \
  --output MT/tester/files/ml_signals.csv \
  --copy-to-mt4
```

Что делает этот CLI:

- читает `entry_path_trade_filter_selected_rule.json`;
- поддерживает winners `A`, `B`, `B_no_path6`;
- для `A` использует `pred_ret_24_dir_atr`;
- для `B` / `B_no_path6` использует frozen validation-нормировку из
  `validation_csv`, указанного в rule JSON;
- обнуляет строки вне frozen rule;
- схлопывает runtime до единого `time;signal` с приоритетом ненулевого сигнала на баре;
- при `--copy-to-mt4` пишет одинаковый export в tester/runtime paths.

### Для `entry_path_v1_quantile`

Актуальный путь после прохождения n-boost gate (2026-04-12) — production rule
`ML/reports/entry_path_v1_quantile_selected_rule.json` (winner `lb_gt_m_q35`,
median m/w/correction по 5 сидам). Экспорт в MT4 выполняется так:

```bash
./.venv/bin/python -m API.export_entry_path_v1_quantile_signals \
  --seed-dir ML/reports/entry_path_v1_quantile_robustness/seed_007 \
  --split test \
  --rule-path ML/reports/entry_path_v1_quantile_selected_rule.json \
  --output MT/tester/files/ml_signals.csv \
  --copy-to-mt4
```

Что делает этот CLI в production-режиме (`--rule-path` задан):

- читает `entry_path_v1_quantile_selected_rule.json` и берёт оттуда
  `winner.rule`, `winner.m`, `winner.w`, `winner.correction`, `baseline_threshold`;
- читает baseline predictions CSV из `baseline_rule_path` внутри rule-файла
  (`ML/reports/entry_path_test_predictions.csv` для split=test),
  чтобы получить `baseline_score` (это принципиально: baseline score берётся
  от baseline-модели, а не из предсказаний самой quantile-сети);
- берёт quantile predictions выбранного seed (`seed_007` — primary, median
  параметры совпадают с его значениями);
- применяет conformal correction, строит `lb`/`width`, накладывает правило;
- для времён с дублирующимися строками оставляет запись с выбранным
  ненулевым сигналом (а не слепо `keep='last'`);
- пишет полный `time;signal`.

Legacy-режим (без `--rule-path`) остался для старого single-seed пути
`entry_path_v1_quantile_filter_selected_rule.json` внутри каждого `seed_*` и
для обратной совместимости; в текущем production-контуре он не используется.

### Для `take_skip_trailing_stop_v2`

Для нового take/skip-контура можно применять уже зафиксированные rule JSON
на готовый prediction CSV без ручного разбора параметров правила.

Quality-режим:

```bash
./.venv/bin/python -m API.export_take_skip_trailing_stop_v2_signals \
  --predictions ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/test.csv \
  --rule-path ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json \
  --output MT/tester/files/ml_signals.csv \
  --copy-to-mt4
```

Frequent-режим:

```bash
./.venv/bin/python -m API.export_take_skip_trailing_stop_v2_signals \
  --predictions ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/test.csv \
  --rule-path ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json \
  --output MT/tester/files/ml_signals.csv \
  --copy-to-mt4
```

Что делает этот CLI:

- читает rule JSON и берёт оттуда `score_target`, `selector`, `threshold`;
- находит колонку `pred_<score_target>` в prediction CSV;
- применяет frozen selector:
  - `prob_ge_threshold`
  - или `top_k_probability`;
- пишет `time;signal` с обнулением невыбранных строк;
- при `--base-csv` может развернуть sparse predictions обратно в полный временной ряд;
- при `--copy-to-mt4` атомарно копирует один и тот же результат в
  `MT/tester/files` и `MT/MQL4/Files`: сначала пишет `.tmp`, затем заменяет
  `ml_signals.csv`;
- при `--metadata-output` пишет JSON с hash выходного CSV, числом ненулевых строк,
  BUY/SELL-счётчиками, дублями времени и группами с противоположными сигналами.

Telemetry diagnostic export:

```bash
./.venv/bin/python -m API.export_take_skip_trailing_stop_v2_signals \
  --predictions ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/test.csv \
  --rule-path ML/reports/telemetry_frequency_v1/calibration/selected_rule.json \
  --output MT/tester/files/ml_signals.csv \
  --metadata-output ML/reports/telemetry_frequency_v1/export_metadata.json \
  --label telemetry_frequency_v1 \
  --copy-to-mt4
```

Этот режим намеренно увеличивает частоту сделок. Его задача - проверить
операционную цепочку и логи, а не доказать прибыльность стратегии.

High-frequency diagnostic export:

```bash
./.venv/bin/python -m API.export_take_skip_trailing_stop_v2_signals \
  --predictions ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/test.csv \
  --rule-path ML/reports/telemetry_frequency_v1/calibration/selected_rule.json \
  --base-csv DATA/Nero_test_labeled.csv \
  --output MT/tester/files/ml_signals.csv \
  --metadata-output ML/reports/telemetry_frequency_v1/tester_export_metadata_highfreq500.json \
  --label telemetry_frequency_v1_highfreq500 \
  --diagnostic-all-rows \
  --diagnostic-target-signals-per-year 500 \
  --copy-to-mt4
```

Этот режим выбирает кандидатов не только из старых строк `signal != 0`, а из
всех строк. Направление берётся из знака `predict` в `base-csv`, сила отбора -
из ML-score `pred_<score_target>`. Для 2025 года текущий профиль даёт 495
сигналов без дублей времени.

Для online-режима MQL-библиотека не держит `ml_signals.csv` неизменным до
перезапуска советника: на новом баре она проверяет время изменения файла и
перезагружает сигналы при изменении. Поэтому внешний Python-процесс может быть
постоянным наблюдателем за `Nero.csv`: при появлении нового завершенного бара он
пересчитывает прогноз, атомарно обновляет `ml_signals.csv`, а MT4 подхватывает
это на следующем баре.

Практический способ запустить такой процесс сейчас:

```bash
mkdir -p ML/reports/telemetry_frequency_v1/runtime

./.venv/bin/python -m API.telemetry_signal_watcher --once --verbose
tmux new -s telemetry-watcher
```

Внутри окна `tmux`:

```bash
./.venv/bin/python -m API.telemetry_signal_watcher \
  --poll-interval-sec 1 \
  --heartbeat-sec 60 \
  --verbose
```

Если `Nero.csv` пока содержит только заголовок, watcher не должен падать. Это
штатное состояние ожидания первого закрытого бара. В логах будет строка вида:

```text
WATCHER HEARTBEAT: status=WAIT input=MT/MQL4/Files/Nero.csv
```

Если новых баров пока нет, watcher должен продолжать жить и периодически писать
heartbeat, например:

```text
WATCHER HEARTBEAT: status=IDLE last_bar=2025.01.01 00:00 input=MT/MQL4/Files/Nero.csv
```
---

## 4. Как сейчас исполняется сигнал

При `iSignal=3`:

1. эксперт ищет строку по `Time[bar]`;
2. если на баре есть сигнал, открывает сделку на следующем баре по рынку;
3. при `ML_MaxPositions=1` держит только одну позицию, при `ML_MaxPositions>1`
   включает диагностический multi-position режим;
4. закрывает её:
   - по `ML_HoldBars`, если `ML_ExitMode=0`;
   - по bar-based trailing-stop `X * ATR`, если `ML_ExitMode=1`;
   - по broker-side take profit, если `ML_TakeProfitATR>0`;
   - либо по обратному сигналу, если включён `ML_AllowReversal`.

Старые `INPUT()`, `OUTPUT()`, `TRAILING_STOP()` и старый `TIMER()` в этом режиме не участвуют.

### Режимы выхода

| Параметр | Значение | Смысл |
|---|---:|---|
| `ML_ExitMode` | `0` | старый parity-check по `ML_HoldBars` |
| `ML_ExitMode` | `1` | отдельный trailing-stop по `ML_TrailATR * ATR` |
| `ML_TrailATR` | `8.0` | ширина trailing-stop; одновременно стартовый стоп и trailing-gap |
| `ML_TakeProfitATR` | `0.0` | broker-side take profit; `0` = выключен |
| `ML_MaxPositions` | `1` | старый single-position режим; `>1` = diagnostic multi-position |

Практический смысл trailing-режима такой:

- для BUY эксперт хранит лучший максимум после входа;
- стоп идёт на уровне `best_high - ATR * ML_TrailATR`;
- для SELL зеркально хранится лучший минимум и стоп `best_low + ATR * ML_TrailATR`;
- если благоприятного хода почти не было, правило работает как обычный стоп того же размера.

---

## 5. Рекомендуемые параметры для parity-check

Для первого прогона:

| Параметр | Значение | Зачем |
|---|---:|---|
| `iSignal` | `3` | включает прямой режим |
| `ML_ExitMode` | `0` | сначала baseline timeout-mode |
| `ML_TrailATR` | `8.0` | базовое значение для trailing-mode |
| `Risk` | `0` | фиксированный лот в тестере |
| `ML_HoldBars` | `12` | базовое удержание |
| `ML_AllowReversal` | `false` | сначала без досрочного reverse-close |
| `ML_UseScoreFilter` | `true` | если подаётся полный prediction CSV |
| `ML_ScoreThreshold` | `-0.03594103` | текущий frozen-порог winner A@7.5% |
| `ML_BackStopATR` | `50.0` | дальний страховочный SL |

Если подаётся уже заранее отфильтрованный `time;signal`, можно:

- оставить `ML_UseScoreFilter=true` — он сам выключится, если колонки score нет;
- либо явно поставить `ML_UseScoreFilter=false`.

Для `entry_path_v1_quantile` предпочтителен именно этот режим: уже заранее отфильтрованный `time;signal`.

Для обоих `entry_path` execution-систем канонический runtime protocol сейчас одинаковый:

| Параметр | Значение | Почему |
|---|---:|---|
| `iSignal` | `3` | direct CSV execution |
| `ML_ExitMode` | `0` | fixed-hold parity mode |
| `ML_HoldBars` | `24` | frozen sequential horizon |
| `ML_BackStopATR` | `50.0` | дальний страховочный stop |
| `ML_AllowReversal` | `false` | benchmark и MT4 parity без reverse-close |
| `ML_UseScoreFilter` | `false` | CSV уже предфильтрован в Python |

Для чистой проверки нового trailing-stop execution:

| Параметр | Значение |
|---|---:|
| `iSignal` | `3` |
| `ML_ExitMode` | `1` |
| `ML_TrailATR` | `8.0` |
| `ML_HoldBars` | можно оставить как есть, в этом режиме он не используется |
| `ML_AllowReversal` | `false` |
| `ML_UseScoreFilter` | `false`, если CSV уже предфильтрован в Python |

Для telemetry diagnostic launch:

| Параметр | Значение | Почему |
|---|---:|---|
| `iSignal` | `3` | прямое исполнение `ml_signals.csv` |
| `SymPer` | `XAUUSD5` | M5 нужен для быстрого набора событий |
| `ML_MaxPositions` | `20` | уменьшает пропуски `MaxPositions` в долгом online diagnostic |
| `ML_ExitMode` | `0` | основной выход через timeout или broker SL/TP |
| `ML_TakeProfitATR` | `5.0` | размер цели сопоставим с исходной стратегией |
| `ML_BackStopATR` | `3.0` | стоп в ATR сопоставим с исходной стратегией |
| `ML_HoldBars` | `24` | ограничение времени жизни диагностической сделки |
| `ML_AllowReversal` | `false` | не смешивать reversal-close с проверкой исполнения |
| `ML_UseScoreFilter` | `false` | CSV уже отобран frozen telemetry rule |

Успех этого режима измеряется не PF, а совпадением механики:

- watcher обновляет `ml_signals.csv` после новых строк `Nero.csv`;
- MT4 перезагружает файл;
- ожидаемые сигналы открываются или получают объяснимый `MLP SKIP`;
- закрытия соответствуют выбранной тактике: timeout, broker SL или broker TP.

Для текущего quantile parity-check (production `lb_gt_m_q35`, frozen 2026-04-12):

| Параметр | Значение | Почему |
|---|---:|---|
| `iSignal` | `3` | прямой parity-mode |
| `ML_HoldBars` | `24` | совпадает с frozen `sequential_hold_bars` |
| `ML_AllowReversal` | `false` | соответствует текущему benchmark-контуру |
| `ML_UseScoreFilter` | `false` | CSV уже предфильтрован в Python через baseline-score |
| `ML_ScoreThreshold` | не используется | quantile winner берёт baseline score не из самого quantile CSV |

Ожидаемое число сделок на test-слое: **22 уникальных bars** (16 BUY / 6 SELL),
Python sequential PF=3.64, win_rate=72.7%. Эти числа нужно использовать как
точку отсчёта для MT4 parity-check.
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
MLP CLOSE BUY reason=TrailingStop ...
MLP CLOSE SELL reason=TrailingStop ...
MLP CLOSE BUY reason=ReverseSignal ...
MLP CLOSE SELL reason=ReverseSignal ...
MLP CLOSE BUY reason=TakeProfit source=broker_history ...
MLP CLOSE SELL reason=TakeProfit source=broker_history ...
MLP CLOSE BUY reason=StopLoss source=broker_history ...
MLP CLOSE SELL reason=StopLoss source=broker_history ...
MLP SKIP reason=ScoreFilter ...
MLP SKIP reason=MaxPositions ...
```

Именно они нужны для сравнения MT4 и Python сделка-в-сделку.

`Timeout`, `TrailingStop` и `ReverseSignal` пишет код закрытия внутри
`ML_TRADE()`. `TakeProfit` и `StopLoss` закрываются брокером/тестером по уровням
ордера, поэтому [lib_ML_Signal.mqh](../../MT/MQL4/Include/lib_ML_Signal.mqh)
дополнительно читает историю ордеров и разово логирует такие закрытия с
`source=broker_history`.

Для daily reconciliation обязательны поля:

- вход: `ticket`, `signal_time`, `entry_time`, `atr`, `spread`, `spread_atr`,
  `open_positions`, `MaxPositions`;
- выход: `ticket`, `entry_time`, `exit_time`, `hold_bars`, `pnl_atr`, `profit`.

Для более точного сравнения online/test эксперт также пишет
`MT/MQL4/Files/ml_trade_events.csv`. Это CSV-журнал торговых событий с
`OPEN`/`CLOSE`, `Bid/Ask`, spread, OHLC бара, запрошенной и фактической ценой,
проскальзыванием, SL/TP, profit, swap, commission, balance и equity. Его
использовать, когда простой reconciliation показывает расхождение в торговых
метриках и нужно понять причину.

Ежедневная автоматическая сверка:

```bash
./.venv/bin/python -m ML.telemetry_daily_reconciliation \
  --signals MT/tester/files/ml_signals.csv \
  --mt4-log MT/tester/logs/20260427.log \
  --export-metadata ML/reports/telemetry_frequency_v1/export_metadata.json \
  --output-dir ML/reports/telemetry_frequency_v1/daily/2026-04-27 \
  --label telemetry_frequency_v1
```

---

## 8. Что делать, если нужен старый runtime

Старый `regression_updn` runtime сохранён отдельно:

- [lib_ML_Signal_back.mqh](../../MT/MQL4/Include/lib_ML_Signal_back.mqh)

Он нужен только для исторических исследований и старых reconciliation-сценариев.

Текущий активный `lib_ML_Signal.mqh` уже описывает другой режим и для old-style `ratio` диагностики не подходит.
