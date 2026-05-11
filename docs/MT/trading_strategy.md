# Trading Expert Algorithm — $o$imple.mq4

> **Назначение этого документа**: короткое и точное описание того, как сейчас работает торговый эксперт MT4 в активном MQL-коде.
>
> **Точка входа**: [MAIN.mqh](../../MT/MQL4/Include/MAIN.mqh), метод `EXPERT::MAIN()`.
>
> **Текущий статус на 2026-05-07**:
> - `iSignal=3` теперь означает **прямой parity-check режим** из [lib_ML_Signal.mqh](../../MT/MQL4/Include/lib_ML_Signal.mqh)
> - старый runtime `regression_updn` сохранён как backup в [lib_ML_Signal_back.mqh](../../MT/MQL4/Include/lib_ML_Signal_back.mqh)
> - `iSignal=5` по-прежнему использует [lib_ML_Signal_TB.mqh](../../MT/MQL4/Include/lib_ML_Signal_TB.mqh)

> **Последнее обновление**: 2026-04-28

Связанные документы:

- [ml_signal_integration.md](ml_signal_integration.md) - операционный Python -> `ml_signals.csv` -> MT4 контур;
- [telemetry_daily_reconciliation.py.md](../ML/telemetry_daily_reconciliation.py.md) - ежедневная сверка expected/open/close/skip;
- [telemetry_signal_watcher.py.md](../API/telemetry_signal_watcher.py.md) - фоновый online watcher `Nero.csv -> ml_signals.csv`.

Если нужен один основной документ, который связывает весь online diagnostic-контур
целиком, использовать именно эту страницу. Остальные два документа являются
специализированными приложениями:

- `ml_signal_integration.md` - про контракт и форматы `ml_signals.csv`;
- `telemetry_signal_watcher.py.md` - про отдельный Python watcher и его эксплуатацию.

---

## 0. Инструкция по тесту

После правок торговой логики:

1. Сменить `VERSION` в [\$o\$imple.mq4](../../MT/MQL4/Experts/$o$imple.mq4#L2).
2. Проверить строку параметров в [\#.csv](../../MT/MQL4/Files/#.csv).
3. Положить нужный CSV файл именно в `MT/tester/files/ml_signals.csv`.
4. В `MT/tester/$o$imple.ini` указать `BackTest`, соответствующий строке `#.csv`.
5. Запустить тестер вручную.
6. После теста открыть свежий лог `MT/tester/logs/*.log`.
7. Сверить `VERSION` из строки `OnInit() SoSimple.V...`.
8. Для parity-check извлечь строки:
   - `MLP BUY`
   - `MLP SELL`
   - `MLP CLOSE BUY`
   - `MLP CLOSE SELL`
   - `MLP SKIP`

---

## 0.1. Как используется `MT/MQL4/Files/#.csv`

`#.csv` - это основной файл внешних параметров эксперта для тестера и онлайн-торговли. Его цель - не вводить extern-переменные руками, потому что ошибка в одной цифре меняет алгоритм стратегии.

### Формат строки

Файл состоит из:

- первой строки-заголовка;
- одной или нескольких рабочих строк стратегий.

Рабочая строка начинается с поля `INFO`, где должно быть имя эксперта, версия и период, например:

```text
SoSimple260.330 2022.10.04-2026.03.10, Sprd=0, StpLev=0, OPT-telemetry_frequency_v1
```

Дальше идут:

- `SymPer`, например `XAUUSD60`;
- служебные статистические поля;
- `Risk`;
- `Magic`;
- все параметры из `EXPERT_PARENT_CLASS::EXTERN_VARS()`.
- резервные поля до общего размера `PARAMS`.

`Magic` не задаётся произвольно. Он является контрольной суммой параметров строки. При запуске `CHECKSUM()` пересчитывает magic через `MAGIC_GENERATOR()` и отключает строку, если значение не совпало.

### Тестер

В тестере `SERVICE.mqh::INPUT_FILE_READ()` читает `#.csv`. Если `BackTest > 0`, используется строка файла с этим номером.

Номер считается как обычный номер строки в файле:

- строка 1 - заголовок;
- строка 2 - первая строка параметров;
- строка 3 - вторая строка параметров.

Текущий telemetry preset находится в единственной рабочей строке `#.csv`, поэтому для тестера нужно ставить:

```text
BackTest=2
```

На 2026-05-11 текущая рабочая строка переключена на `XAUUSD5` для M5
diagnostic-контура `telemetry_frequency_v1_highfreq500`. Цель этого режима -
быстро набрать много событий и проверить тракт `MT -> ML -> MT`, а не
прибыльность.

Для этого diagnostic preset ключевые ML-параметры такие:

- `ML_ExitMode=0`;
- `ML_MaxPositions=10`;
- `ML_HoldBars=24`;
- `ML_TakeProfitATR=5`;
- `ML_BackStopATR=3`;
- `ML_AllowReversal=0`;
- `ML_UseScoreFilter=0`.

Смысл: MT4 должен часто открывать заранее отобранные diagnostic-сигналы,
закрывать их по timeout или broker SL/TP и писать достаточно подробные логи
для reconciliation. PF в этом режиме не используется как критерий успеха.

Для возврата к H1 parity `entry_path_v1_live_safe + A @ 7.5%` нужно вернуть
`SymPer=XAUUSD60`, `ML_MaxPositions=1`, `ML_TakeProfitATR=0`,
`ML_BackStopATR=999`.

После изменения `#.csv` обязательно перекомпилировать советник. Для этого
этапа ожидаемая версия в логе: `OnInit() SoSimple.V260.332`. Версии ниже могут
читать `PARAMS` как `char`, из-за чего большие значения вроде
`ML_BackStopATR=999` искажаются и `Magic` не совпадает.

### Онлайн-торговля

При `Real=true` файл читается целиком. Все строки, подходящие по:

- `Name == SoSimple`;
- `Symbol()`;
- `Period()`;
- `Risk > 0`;
- корректный `Magic`,

попадают в массив `EXP[]`. Затем на каждом новом баре `OnTick()` вызывает `EXP[e].MAIN()` для каждой строки. Перед выполнением `EXPERT_SET(e)` подставляет параметры строки в extern-переменные, восстанавливает индивидуальное состояние этой стратегии и проверяет `Magic`.

Так несколько стратегий могут работать на одном графике. Их ордера отделяются друг от друга через `Magic`.

### Исторический прогрев PIC при старте

С 2026-04-28 эксперт при запуске делает отдельный проход по доступной истории
через `RECOUNT_HISTORY()` ещё в `OnInit()`.

Схема такая:

1. `EXP[e].INIT()` создаёт новый `Nero.csv` с заголовком.
2. `RECOUNT_HISTORY()` проходит историю циклом `for (bar=UnCounted; bar>1; bar--)`.
3. Для каждого бара вызывается `EXP[e].PIC()` для всех активных строк `EXP[]`.
4. Внутри `PIC()` теперь сразу вызывается и `POC_SIMPLE()`, чтобы состояние
   после прогрева совпадало с обычным bar-by-bar проходом.
5. После прогрева эксперт возвращается в штатный online-режим с `bar=1` и
   `BarTime=Time[0]`.

Это нужно не только чтобы быстрее набрать первые `100` уровней, а чтобы
восстановить массив `F[]` с учётом очень старых сильных фракталов. Иначе после
перезапуска эксперт долго работает в "холодном" состоянии, не похожем на то,
на котором проводились обучение и тестирование.

### Где задаётся список параметров

Список параметров, которые сохраняются в `#.csv`, читаются обратно и участвуют в `Magic`, задаётся в:

```text
MT/MQL4/Include/MAIN.mqh::EXPERT_PARENT_CLASS::EXTERN_VARS()
```

Если новый extern-параметр не добавлен в `EXTERN_VARS()`, он не является частью runtime-contract:

- не читается из `#.csv`;
- не сохраняется в tester/report output;
- не участвует в `Magic`;
- может остаться случайным значением из `.ini` или ручного ввода.

Для `telemetry_frequency_v1` в `EXTERN_VARS()` включены активные параметры:

- `ML_ExitMode`;
- `ML_TrailATR`;
- `ML_TakeProfitATR`;
- `ML_MaxPositions`;
- `ML_HoldBars`;
- `ML_AllowReversal`;
- `ML_UseScoreFilter`;
- `ML_ScoreThreshold`;
- `ML_BackStopATR`.

Legacy `ML_*` параметры старого `regression_updn` runtime пока оставлены как extern в `$o$imple.mq4`, но не включены в активную telemetry-строку, потому что для текущего `iSignal=3` они не управляют исполнением.

Текущий `PARAMS=80`, а активных параметров в `EXTERN_VARS()` меньше. Поэтому в конце `#.csv` есть `Reserved01..Reserved40`. Их нельзя удалять без одновременного изменения `PARAMS` или логики чтения: `INPUT_FILE_READ()` читает ровно `PARAMS` значений после `Magic`.

После чтения рабочей строки `#.csv` эксперт пишет в лог строку:

```text
<Magic>:: CSV parameters loaded e=<N> PARAMS_LOADED ...
```

Эта строка является главным подтверждением, что параметры применились именно из `#.csv`. Стандартная строка MT4 `$o$imple inputs: ...` показывает исходные extern inputs из `.ini` на старте тестера и сама по себе не доказывает, что строка `#.csv` была выбрана.

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

1. Загружает `ml_signals.csv` и в online/runtime режиме проверяет изменение
   файла на новом баре.
2. Ищет строку по времени `Time[bar]`.
3. Если на баре есть сигнал:
   - при `ML_MaxPositions=1` работает в старом single-position режиме;
   - при `ML_MaxPositions>1` разрешает несколько одновременных ML-позиций;
   - при `ML_AllowReversal=true` может закрыть позицию по обратному сигналу.
4. Выбирает режим выхода:
   - `ML_ExitMode=0` -> таймаут по `ML_HoldBars`;
   - `ML_ExitMode=1` -> bar-based trailing-stop по `ML_TrailATR * ATR`.

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

Для диагностического профиля `telemetry_frequency_v1_highfreq500` exporter
сразу удаляет дубли времени, чтобы MT4 и Python-сверка видели один и тот же
ряд сигналов.

Для настоящей торговли дубли времени лучше считать ошибкой входного контура, а
не нормальным режимом. Причина простая: если на один бар пришли разные сигналы,
то результат зависит от порядка строк в файле. Текущее правило "последняя строка
побеждает" нужно как защитный fallback, чтобы MT4 вел себя детерминированно, но
правильная upstream-политика такая:

- exporter должен писать не больше одной строки на `time`;
- если несколько моделей/кандидатов дают сигналы на один бар, конфликт решается
  в Python до записи `ml_signals.csv`;
- при одинаковом направлении можно агрегировать силу сигнала или оставить
  strongest-score кандидата;
- при противоположных направлениях для боевого режима безопаснее писать `0`,
  либо выбирать сторону только по заранее описанному приоритету модели;
- metadata/report должен считать `duplicate_time_rows` и
  `same_time_opposite_signal_groups`; для online-режима оба значения должны быть
  `0`.

### 3.4 Online update без `ready`-файла

Для online-режима не нужен отдельный `ml_signals.ready`, если Python пишет
сигналы атомарно:

1. Python формирует новый файл во временный `ml_signals.csv.tmp`.
2. После полной записи заменяет им `ml_signals.csv`.
3. MT4 на новом баре проверяет время изменения `ml_signals.csv`.
4. Если файл изменился, `ML_TRADE()` перезагружает сигналы и пишет в лог
   `MLP_RELOAD: file changed`.

Так MT4 не должен читать частично записанный CSV. Отдельный manifest/ready-файл
можно добавить позже как диагностический отчёт, но для готовности файла он не
обязателен.

С 2026-04-28 online-ожидание в MQL проверяет не только факт изменения файла, но
и содержимое загруженного ряда. Файл считается пригодным для текущего бара
только если последний `time` внутри `ml_signals.csv` не меньше `Time[bar]`.

Причина: watcher может обновить `ml_signals.csv` новым по `mtime` файлом,
который всё ещё заканчивается раньше текущего `bar_time` - например после
первого запуска, во время/после `RECOUNT_HISTORY()` или если в `Nero.csv` ещё
нет новой строки для текущего бара. Поэтому один `mtime` недостаточен.

### 3.5 Online MT -> Python -> MT pipeline

Полная online-связка должна работать так:

1. При старте MT4 пересобирает `Nero.csv` по доступной истории через
   `RECOUNT_HISTORY()`, а затем дописывает новые строки при появлении новых
   уровней `PIC()`.
2. Отдельный Python-процесс постоянно запущен в фоне и следит за изменением
   `Nero.csv`.
3. Когда появляется новый завершённый бар, Python читает новые строки,
   пересчитывает признаки, применяет модель и формирует новый `ml_signals.csv`.
4. Python пишет файл атомарно: сначала `ml_signals.csv.tmp`, затем заменяет им
   `ml_signals.csv`.
5. MT4 на новом баре вызывает `ML_TRADE()`.
6. `ML_TRADE()` ждёт до `MLP_WAIT_SIGNAL_SEC` секунд, пока `ml_signals.csv`
   изменится и после перечитывания будет покрывать текущий `Time[bar]`.
7. Если файл дошёл до текущего бара, `ML_TRADE()` ищет точное совпадение времени
   через `MLP_FindSignal(Time[bar])`.
8. Сверка запускается отдельным Python CLI: `ML.telemetry_daily_reconciliation`
   сравнивает ожидаемые сигналы, MT4 open/close/skip строки и metadata export.

MQL не должен запускать ML-модель внутри себя. Его роль - записывать исходные
данные, читать готовый `ml_signals.csv`, открывать/закрывать сделки и подробно
логировать исполнение. Python отвечает за модель, нормализацию, отбор сигналов,
атомарную запись файла и диагностические отчёты.

Важное уточнение по preprocessing:

- полный offline pipeline проекта действительно включает сортировку, разметку,
  добавление target-колонок и нормализацию;
- но текущий online telemetry watcher не гоняет весь `processing/label_main.py`
  в реальном времени;
- для `telemetry_frequency_v1` он сначала применяет causal subset preprocessing:
  сортирует `fractal0..fractal99` по времени убыванию и выполняет
  `normalize_rowwise()`;
- после сортировки выполняется проверка порядка фракталов;
- `normalize_rowwise()` запускается в тихом режиме, чтобы не засорять runtime
  log watcher-а;
- legacy checkpoint в режиме `original_contour` / `original_baseline` теперь
  заблокирован online contract guard по умолчанию, потому что его training/test
  input включал future-derived row features (`predict`, `ret_*`, `fav_*`,
  `adv_*`). Такой checkpoint нельзя считать ML-корректным online.

То есть для будущего корректного online-контура нужно не "повторить весь train
preprocessing", а использовать один и тот же live-safe набор признаков в
training/test и online. Старый `original_baseline` можно запускать только с
явным `--allow-unsafe-future-features` для механической диагностики связи,
но не для вывода о качестве ML.

Важное уточнение по направлению online-сигнала, найденное 2026-04-28:

- эксперт пересобирает и дописывает `Nero.csv` по истории и новым уровням;
- `signal` и `predict` в raw online `Nero.csv` остаются нулевыми, и это не
  считается ошибкой MQL;
- offline `predict` создаётся Python-разметкой с просмотром будущих строк:
  `predict = -back * direction`;
- поэтому в live-контуре нельзя честно досчитать тот же `predict` в момент
  появления строки;
- для diagnostic online-export watcher использует `fractal0.direction` после
  сортировки как
  доступный текущий источник направления:
  - `fractal0.direction = -1 -> BUY`;
  - `fractal0.direction = 1 -> SELL`.

Так сохраняется знак старого diagnostic-подхода через `predict`, но без
использования будущих данных.

Ограничение этого решения: это diagnostic-режим для набора статистики
MT4↔ML↔MT4. Он не доказывает, что production-стратегия должна использовать
ровно тот же источник направления. Для production-перехода нужно отдельно
проверить соответствие выбранного online-направления обучающей постановке.

Для online-наблюдения ключевой operational смысл такой:

1. эксперт в MT4 сначала пересобирает `Nero.csv` по истории, затем пишет новые
   строки при появлении новых уровней;
2. отдельный Python watcher работает в фоне и ждёт новый закрытый бар;
3. если `Nero.csv` пока содержит только заголовок, watcher остаётся в состоянии
   `waiting_for_first_row`, пишет это в лог и ждёт первый закрытый бар;
4. после появления строки данных watcher сначала собирает raw
   `runtime_input_snapshot.csv` из хвоста `Nero.csv`, затем строит
   `runtime_input_preprocessed.csv`, пересчитывает prediction CSV и обновляет
   `ml_signals.csv`;
5. MT4 на новом баре видит изменение файла и пишет `MLP_RELOAD: file changed`;
6. дальше в логах нужно наблюдать уже торговые строки:
   - `MLP BUY`
   - `MLP SELL`
   - `MLP CLOSE`
   - `MLP SKIP`

Если в online-режиме нет `MLP_RELOAD: file changed`, проблема уже не в MQL
торговом исполнении, а в том, что внешний Python watcher не обновил runtime
`ml_signals.csv`.

### 3.6 Последовательность прохождения сигнала в MQL

Ниже текущий порядок вызовов на новом баре:

1. `OnTick()` видит новый `Time[0]` и вызывает `EXP[e].MAIN()` для каждой
   активной строки `EXP[]`.
2. `MAIN()` вызывает `EXPERT_SET(e)`, подставляет параметры строки `#.csv` и
   затем вызывает `COUNT()`.
3. `COUNT()` вызывает `PIC()`.
4. Если в `PIC()` найден новый уровень, `NEW_LEVEL()` обновляет массив `F[]`, а
   `NERO_CSV_CREATE(bar)` дописывает строку в `MT/MQL4/Files/Nero.csv`.
5. После успешного `COUNT()` и `FINE_TIME()` вызывается `ML_TRADE()`.
6. В начале `ML_TRADE()` вызывается `MLP_WAIT_RELOAD_IF_NEEDED(Time[bar])`.
7. В `Real=true` эта функция:
   - запоминает локальное время старта ожидания;
   - ждёт изменения `ml_signals.csv`;
   - при изменении пишет `MLP_WAIT: file changed after ...`;
   - перечитывает файл через `MLP_RELOAD_IF_CHANGED()` / `MLP_INIT()`;
   - принимает файл только если последний `time` в нём `>= Time[bar]`;
   - если файл ещё отстаёт, пишет `MLP_WAIT: file still behind ...`;
   - если за `MLP_WAIT_SIGNAL_SEC` файл так и не дошёл до бара, пишет
     `MLP_WAIT: timeout ...`.
8. После ожидания `ML_TRADE()` ищет точное время `Time[bar]` в массиве
   `MLP_Times[]`.
9. Возможные диагностические исходы:
   - `MLP NO_SIGNAL` - точной строки `Time[bar]` в `ml_signals.csv` нет;
   - `MLP ZERO_SIGNAL` - строка есть, но `signal=0`;
   - `MLP BUY` - найден `signal=1`, отправлен BUY;
   - `MLP SELL` - найден `signal=-1`, отправлен SELL;
   - `MLP SKIP` - сигнал найден, но отфильтрован или заблокирован правилом.

Важное следствие: `Nero.csv` не обязан дописываться на каждом M5/H1 баре. Он
пишется при появлении нового уровня. Поэтому `MLP NO_SIGNAL` и timeout на барах
без новой строки `Nero.csv` сами по себе не являются ошибкой исполнения. Ошибка
подозревается, если в `Nero.csv` уже есть строка с нужным `Time[bar]`, watcher
завершил rebuild, а `ml_signals.csv` всё равно не содержит эту строку.

### 3.7 Operational checklist для watcher на сервере

1. Убедиться, что expert уже создал `MT/MQL4/Files/Nero.csv`.
2. Проверить содержимое `Nero.csv`:
   - только заголовок -> это нормально сразу после старта;
   - есть хотя бы одна строка данных -> watcher уже может делать rebuild.
3. Создать runtime-каталог:

```bash
mkdir -p ML/reports/telemetry_frequency_v1/runtime
```

4. Для первой проверки выполнить один проход:

```bash
./.venv/bin/python -m API.telemetry_signal_watcher --once --verbose
```

5. Затем запустить watcher в отдельном окне `tmux`:

```bash
tmux new -s telemetry-watcher
```

Внутри окна `tmux`:

```bash
./.venv/bin/python -m API.telemetry_signal_watcher \
  --poll-interval-sec 1 \
  --heartbeat-sec 60 \
  --max-runtime-rows 12000 \
  --verbose
```

6. Отсоединиться от окна без остановки watcher-а:

```bash
Ctrl+B, затем D
```

7. Вернуться в окно watcher-а:

```bash
tmux attach -t telemetry-watcher
```

8. Проверить логи:

```bash
tail -n 50 ML/reports/telemetry_frequency_v1/runtime/telemetry_signal_watcher.log
```

9. Нормальные состояния на экране и в логах для live-safe checkpoint:
   - `WATCHER HEARTBEAT: status=WAIT ...`
   - `WATCHER HEARTBEAT: status=IDLE ...`
   - `WATCHER rebuild start: ...`
   - `WATCHER rebuild done: ...`

10. Если используется legacy `original_baseline`, нормальный исход - остановка
   на `OnlineInferenceContractError`: это защита от запуска модели, которая
   ждёт future-derived признаки. Для старой механической диагностики можно
   добавить `--allow-unsafe-future-features`, но такой прогон не является
   проверкой соответствия online и test.

11. После первого rebuild проверить обновление:
   - `ML/reports/telemetry_frequency_v1/runtime/runtime_input_snapshot.csv`
   - `ML/reports/telemetry_frequency_v1/runtime/runtime_input_preprocessed.csv`
   - `MT/MQL4/Files/ml_signals.csv`
   - `MT/tester/files/ml_signals.csv`
   - `ML/reports/telemetry_frequency_v1/runtime/runtime_state.json`

12. На следующем баре в MT4 проверить:
   - `MLP_RELOAD: file changed ...`
   - `MLP BUY` / `MLP SELL`
   - затем `MLP CLOSE` / `MLP SKIP`

Диагностический профиль `telemetry_frequency_v1_highfreq500` нужен только для
ускоренного набора статистики взаимодействия. Если он запущен через unsafe
override, его считать проверкой механической цепочки MT4 -> Python -> CSV ->
MT4, а не доказательством прибыльности или соответствия online/test.

---

## 4. Как сейчас открывается сделка

Для `iSignal=3`:

- `signal = 1` -> BUY по текущему `ASK`
- `signal = -1` -> SELL по текущему `BID`
- при `ML_MaxPositions=1` одновременно может быть только одна активная позиция
- при `ML_MaxPositions>1` открытие идёт напрямую через ticket-level order helper,
  и старое ограничение `BUY.Typ/SEL.Typ` не блокирует вторую позицию того же направления

В single-position режиме `set.BUY` / `set.SEL` заполняются прямо в `ML_TRADE()`,
затем сделка проходит через обычные `MODIFY()` и `ORDERS_SET()`. В multi-position
режиме используется локальный `MLP_OpenMarketOrder()`, чтобы работать по ticket,
а не через один общий `set.BUY` / `set.SEL`.

### Защитный стоп

Текущий режим ставит очень дальний технический стоп:

- BUY: `entry - ML_BackStopATR * ATR`
- SELL: `entry + ML_BackStopATR * ATR`

Он нужен не как торговая логика, а как безопасный способ:

- пройти внутренние проверки ордера;
- корректно посчитать риск и лот;
- не ломать parity-check нулевым `SL`.

Целевой выход при этом всё равно идёт не по этому стопу, а по таймауту или обратному сигналу.

В telemetry diagnostic режиме стоп можно сделать рабочим:

- `ML_BackStopATR=3.0`;
- `ML_TakeProfitATR=5.0`;
- `ML_MaxPositions=10`.

Так размер сделки в ATR остаётся сопоставимым с исходной стратегией, а влияние
спреда на результат не становится искусственно завышенным из-за слишком коротких
целей.

---

## 5. Как сейчас закрывается сделка

### 5.1 Таймаут (`ML_ExitMode=0`)

Если позиция открыта и:

- `SHIFT(BUY.T) >= ML_HoldBars`
- или `SHIFT(SEL.T) >= ML_HoldBars`

эксперт вызывает закрытие по рынку с причиной `MLP_Timeout`.

### 5.2 Trailing-stop (`ML_ExitMode=1`)

Для нового режима эксперт хранит отдельное состояние лучшего хода цены после входа:

- BUY:
  - обновляет лучший максимум по `High[bar]`;
  - считает уровень выхода `best_high - ATR * ML_TrailATR`;
  - закрывает позицию с причиной `MLP_TrailingStop`, если рынок ушёл ниже этого уровня.
- SELL:
  - обновляет лучший минимум по `Low[bar]`;
  - считает уровень выхода `best_low + ATR * ML_TrailATR`;
  - закрывает позицию с причиной `MLP_TrailingStop`, если рынок ушёл выше этого уровня.

Это bar-based приближение. Оно не повторяет внутрибаравое движение по тикам, но гораздо ближе к новой исследовательской постановке, чем старый timeout-only режим.

### 5.3 Обратный сигнал

Если включён `ML_AllowReversal=true`, то:

- открытый BUY закрывается при новом `signal=-1`;
- открытый SELL закрывается при новом `signal=1`.

Причина в логе: `MLP_ReverseSignal`.

### 5.4 Что в этом режиме НЕ используется

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
| `ML_ExitMode` | выбор между timeout и trailing-stop |
| `ML_TrailATR` | ширина trailing-stop в ATR |
| `ML_TakeProfitATR` | take profit в ATR; `0` выключает TP |
| `ML_MaxPositions` | лимит одновременных ML-позиций |
| `ML_HoldBars` | сколько баров держать сделку |
| `ML_AllowReversal` | закрывать ли позицию по обратному сигналу |
| `ML_UseScoreFilter` | применять ли порог по `pred_ret_24_dir_atr`, если колонка есть |
| `ML_ScoreThreshold` | порог score для текущего winner |
| `ML_BackStopATR` | дальний страховочный SL |

Практический нюанс для текущего `entry_path_v1_quantile` parity-check
(production `lb_gt_m_q35`, frozen 2026-04-12):

- в MT4 должен стоять `ML_HoldBars=24`, потому что frozen Python-rule
  использует `sequential_hold_bars=24`;
- `ML_UseScoreFilter=false`: CSV уже предфильтрован в Python — причём
  baseline score там берётся **от baseline-модели** (`A @ 7.5%`), а не от
  самой quantile-сети, поэтому воспроизвести этот фильтр внутри MT4
  одним `pred_ret_24_dir_atr`-порогом нельзя;
- старый `ML_ScoreThreshold=-0.03594103` остаётся релевантным для
  baseline `A @ 7.5%`, но в текущем quantile-контуре он в MT4 не
  применяется;
- канонический канал подготовки CSV:
  `API.export_entry_path_v1_quantile_signals --rule-path
  ML/reports/entry_path_v1_quantile_selected_rule.json`
  (подробности в [ml_signal_integration.md](ml_signal_integration.md)).
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

- `ticket`
- `signal_time`
- `entry_time`
- `score`
- `atr`
- `spread`
- `spread_atr`
- `open_positions`
- `MaxPositions`
- `Val`

### Выход

- `MLP CLOSE BUY reason=Timeout ...`
- `MLP CLOSE SELL reason=Timeout ...`
- `MLP CLOSE BUY reason=TrailingStop ...`
- `MLP CLOSE SELL reason=TrailingStop ...`
- `MLP CLOSE BUY reason=ReverseSignal ...`
- `MLP CLOSE SELL reason=ReverseSignal ...`
- `MLP CLOSE BUY reason=TakeProfit source=broker_history ...`
- `MLP CLOSE SELL reason=TakeProfit source=broker_history ...`
- `MLP CLOSE BUY reason=StopLoss source=broker_history ...`
- `MLP CLOSE SELL reason=StopLoss source=broker_history ...`

Поля:

- `ticket`
- `signal_time`
- `entry_time`
- `exit_time`
- `hold_bars`
- `entry`
- `exit`
- `atr`
- `spread`
- `spread_atr`
- `pnl_atr`
- `profit`

Закрытия `Timeout`, `TrailingStop` и `ReverseSignal` инициирует сам
`ML_TRADE()`. Закрытия `TakeProfit` и `StopLoss` выполняет сервер MT4/тестер
по выставленным уровням ордера, поэтому эксперт дополнительно сканирует историю
своих ордеров и разово пишет такую сделку как `source=broker_history`.

Если цена закрытия не совпала с `OrderTakeProfit()` или `OrderStopLoss()` в
допуске нескольких пунктов, причина пишется как `BrokerClose`. Это лучше, чем
угадывать причину: для сверки важен сам факт закрытия по `ticket`, а причину
можно разобрать отдельно.

### Пропуск сигнала

- `MLP SKIP reason=ScoreFilter ...`
- `MLP SKIP reason=MaxPositions ...`

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
