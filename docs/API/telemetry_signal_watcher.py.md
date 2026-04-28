# telemetry_signal_watcher.py

## Назначение

Связанные документы:

- [../MT/trading_strategy.md](../MT/trading_strategy.md) - общая логика online-контура, `#.csv`, MQL-исполнение и operational checklist;
- [../MT/ml_signal_integration.md](../MT/ml_signal_integration.md) - контракт `ml_signals.csv` и роль watcher-а в общей MT4-интеграции;
- [../ML/telemetry_daily_reconciliation.py.md](../ML/telemetry_daily_reconciliation.py.md) - ежедневная сверка expected/open/close/skip после online/test прогона.

`API/telemetry_signal_watcher.py` - фоновый Python-процесс для online telemetry-контура:

`MT4 -> Nero.csv -> prediction CSV -> ml_signals.csv -> MT4`

Скрипт не обучает модель и не меняет frozen rule. Он только:

- ждёт новый закрытый бар в `Nero.csv`;
- строит компактный `runtime_input_snapshot.csv` из хвоста `Nero.csv`;
- строит свежий prediction CSV через `ML.export_take_skip_v2_predictions`;
- применяет frozen telemetry rule через `API.export_take_skip_trailing_stop_v2_signals`;
- атомарно обновляет `ml_signals.csv` в runtime/tester каталогах;
- пишет state/log/metadata.

Важно: watcher не повторяет весь offline pipeline `processing/label_main.py`.
Для текущего telemetry-контура это не нужно. Он работает через
`ML.export_take_skip_v2_predictions`, который сам строит вход модели из raw
`Nero.csv` в режиме `original_contour` / `original_baseline` / `seq_len=50`.

## Что именно он использует

- входной CSV: `MT/MQL4/Files/Nero.csv`
- checkpoint: `ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/checkpoint.pt`
- frozen rule: `ML/reports/telemetry_frequency_v1/calibration/selected_rule.json`
- inference contract: `mode=original_contour`, `feature_mode=original_baseline`, `seq_len=50`

Текущий watcher заточен под diagnostic профиль `telemetry_frequency_v1_highfreq500`.

### Что из preprocessing реально нужно online

Offline training использовал более длинный pipeline:

- сортировка;
- разметка target-колонок;
- нормализация;
- split train/validation/test.

Но online watcher для текущего telemetry take/skip v2 контура не запускает этот
pipeline явно. Он ожидает, что MT4 уже пишет `Nero.csv` в рабочем runtime
формате:

- `time`
- `signal`
- `predict`
- `ATR`
- `fractal0..fractal99`

После этого `ML.export_take_skip_v2_predictions` сам:

- парсит fractal-структуру;
- собирает `original_contour` входы (`20 fractal features + summaries + row-wise features = 539`);
- прогоняет checkpoint;
- выдаёт `pred_take_*` для frozen telemetry rule.

Направление diagnostic-сделки в online-режиме берётся не из `predict`, а из
`fractal0.direction` с обратным знаком:

```text
fractal0.direction = -1 -> BUY
fractal0.direction =  1 -> SELL
```

Причина: offline `predict` является обучающей меткой с просмотром будущих строк
(`predict = -back * direction`). В live `Nero.csv` будущего ещё нет, поэтому
watcher использует текущий `fractal0.direction` как online-эквивалент знака
старого diagnostic `predict`.

## Почему это отдельный процесс

MT4 не должен запускать модель внутри MQL. Его роль:

- дописывать `Nero.csv`;
- читать готовый `ml_signals.csv`;
- исполнять сделки;
- писать MLP-лог.

Python отвечает за inference, frozen rule, атомарную запись и служебные артефакты.

## Поведение

Watcher хранит `runtime_state.json` и сравнивает:

- последнее значение `time` в `Nero.csv`;
- `mtime` исходного файла.

Если нового закрытого бара нет, пересчёт не делается.

Если `Nero.csv` уже создан, но пока содержит только заголовок без строк данных,
watcher не считает это ошибкой. Он пишет в `runtime_state.json`
`last_status=waiting_for_first_row`, делает запись в лог и продолжает ждать
первый закрытый бар.

Если новый бар появился:

1. из полного `Nero.csv` собирается `runtime_input_snapshot.csv` только по последним `max_runtime_rows`;
2. по snapshot строится `runtime_predictions.csv`;
3. по snapshot строится `runtime_ml_signals.csv`;
4. exporter атомарно копирует готовый `ml_signals.csv` в:
   - `MT/MQL4/Files/ml_signals.csv`
   - `MT/tester/files/ml_signals.csv`
5. state обновляется только после успешного rebuild.

По умолчанию `max_runtime_rows=12000`.

Зачем это сделано:

- цель: не перечитывать и не держать в памяти весь многолетний `Nero.csv` на каждом новом уровне;
- причина: полный single-tensor inference на десятках тысяч строк легко уходит в двузначные гигабайты RAM;
- последствие: watcher стал пригоден для более дешёвого сервера;
- ограничение: `runtime_predictions.csv` и `ml_signals.csv` теперь содержат только рабочее окно snapshot-а, а не всю историю `Nero.csv`.

Практический смысл ограничения:

- для планового online H1-режима это безопасно, если окно заметно больше фактического числа runtime-строк за год;
- для M1 debug-режима это осознанный компромисс ради памяти;
- если понадобится полный исторический export, его нужно запускать отдельным offline/one-shot прогоном, а не постоянным watcher-ом.

## Запуск

Один проход:

```bash
./.venv/bin/python -m API.telemetry_signal_watcher --once --verbose
```

Основной режим эксплуатации: отдельное окно `tmux`:

```bash
mkdir -p ML/reports/telemetry_frequency_v1/runtime

tmux new -s telemetry-watcher
```

Внутри открывшегося окна `tmux`:

```bash
./.venv/bin/python -m API.telemetry_signal_watcher \
  --poll-interval-sec 1 \
  --heartbeat-sec 60 \
  --max-runtime-rows 12000 \
  --verbose
```

Для выхода без остановки процесса:

- `Ctrl+B`, затем `D`

Для возврата в окно:

```bash
tmux attach -t telemetry-watcher
```

## Короткий operational checklist

1. Убедиться, что expert уже запущен и создал `MT/MQL4/Files/Nero.csv`.
2. Проверить, что в `Nero.csv` появилась хотя бы одна строка данных помимо заголовка.
3. Создать runtime-каталог:

```bash
mkdir -p ML/reports/telemetry_frequency_v1/runtime
```

4. Для первой проверки безопаснее выполнить один проход:

```bash
./.venv/bin/python -m API.telemetry_signal_watcher --once --verbose
```

5. Если одноразовый запуск прошёл, запускать watcher в отдельном окне `tmux`.
6. При необходимости проверить процесс:

```bash
ps -eo pid,cmd | rg telemetry_signal_watcher
```

7. Проверить файл-лог:

```bash
tail -n 50 ML/reports/telemetry_frequency_v1/runtime/telemetry_signal_watcher.log
```

8. Нормальные состояния на экране:
   - `WATCHER HEARTBEAT: status=WAIT ...`
   - `WATCHER HEARTBEAT: status=IDLE ...`
   - `WATCHER rebuild start: ...`
   - `WATCHER rebuild done: ...`

9. После первого rebuild проверить, что обновились:
   - `MT/MQL4/Files/ml_signals.csv`
   - `MT/tester/files/ml_signals.csv`
   - `ML/reports/telemetry_frequency_v1/runtime/runtime_state.json`

10. В MT4 на следующем баре проверить строки вида:
   - `MLP_RELOAD: file changed`
   - `MLP BUY` / `MLP SELL`
   - затем `MLP CLOSE` / `MLP SKIP`

## Выходные файлы

- `ML/reports/telemetry_frequency_v1/runtime/runtime_predictions.csv`
- `ML/reports/telemetry_frequency_v1/runtime/runtime_ml_signals.csv`
- `ML/reports/telemetry_frequency_v1/runtime/runtime_input_snapshot.csv`
- `ML/reports/telemetry_frequency_v1/runtime/runtime_export_metadata.json`
- `ML/reports/telemetry_frequency_v1/runtime/runtime_state.json`
- `ML/reports/telemetry_frequency_v1/runtime/telemetry_signal_watcher.log`

## Ограничения

- watcher сейчас реализует только telemetry take/skip v2 contour;
- используется polling, а не OS-level file events;
- если `Nero.csv` испорчен или checkpoint/rule недоступны, rebuild не завершится, а ошибка уйдёт в log;
- `header-only` состояние `Nero.csv` допустимо сразу после старта expert: это не ошибка, а ожидание первого завершённого бара;
- для наблюдаемого server-режима основным способом запуска считается `tmux`, а не `nohup`;
- практические дефолты для сильного сервера: `poll=1s`, `heartbeat=60s`.
- практический лимит памяти задаётся через `--max-runtime-rows`; по умолчанию watcher держит только последние `12000` строк `Nero.csv`.
