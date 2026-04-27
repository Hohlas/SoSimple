# telemetry_signal_watcher.py

## Назначение

`API/telemetry_signal_watcher.py` - фоновый Python-процесс для online telemetry-контура:

`MT4 -> Nero.csv -> prediction CSV -> ml_signals.csv -> MT4`

Скрипт не обучает модель и не меняет frozen rule. Он только:

- ждёт новый закрытый бар в `Nero.csv`;
- строит свежий prediction CSV через `ML.export_take_skip_v2_predictions`;
- применяет frozen telemetry rule через `API.export_take_skip_trailing_stop_v2_signals`;
- атомарно обновляет `ml_signals.csv` в runtime/tester каталогах;
- пишет state/log/metadata.

Важно: watcher не повторяет весь offline pipeline `processing/label_main.py`.
Для текущего telemetry-контура это не нужно. Он работает через
`ML.export_take_skip_v2_predictions`, который сам строит вход модели из raw
`Nero.csv`.

## Что именно он использует

- входной CSV: `MT/MQL4/Files/Nero.csv`
- checkpoint: `ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/checkpoint.pt`
- frozen rule: `ML/reports/telemetry_frequency_v1/calibration/selected_rule.json`

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
- собирает тензор входов;
- прогоняет checkpoint;
- выдаёт `pred_take_*` для frozen telemetry rule.

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

Если новый бар появился:

1. строится `runtime_predictions.csv`;
2. строится `runtime_ml_signals.csv`;
3. exporter атомарно копирует готовый `ml_signals.csv` в:
   - `MT/MQL4/Files/ml_signals.csv`
   - `MT/tester/files/ml_signals.csv`
4. state обновляется только после успешного rebuild.

## Запуск

Один проход:

```bash
./.venv/bin/python -m API.telemetry_signal_watcher --once --verbose
```

Фоновый polling:

```bash
nohup ./.venv/bin/python -m API.telemetry_signal_watcher \
  --poll-interval-sec 10 \
  --verbose \
  > ML/reports/telemetry_frequency_v1/runtime/watcher.stdout.log 2>&1 &
```

## Выходные файлы

- `ML/reports/telemetry_frequency_v1/runtime/runtime_predictions.csv`
- `ML/reports/telemetry_frequency_v1/runtime/runtime_ml_signals.csv`
- `ML/reports/telemetry_frequency_v1/runtime/runtime_export_metadata.json`
- `ML/reports/telemetry_frequency_v1/runtime/runtime_state.json`
- `ML/reports/telemetry_frequency_v1/runtime/telemetry_signal_watcher.log`

## Ограничения

- watcher сейчас реализует только telemetry take/skip v2 contour;
- используется polling, а не OS-level file events;
- если `Nero.csv` испорчен или checkpoint/rule недоступны, rebuild не завершится, а ошибка уйдёт в log.
