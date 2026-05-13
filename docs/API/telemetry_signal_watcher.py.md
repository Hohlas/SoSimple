# telemetry_signal_watcher.py

## Назначение

Связанные документы:

- [../MT/trading_strategy.md](../MT/trading_strategy.md) - общая логика online-контура, `#.csv`, MQL-исполнение и operational checklist;
- [../MT/ml_signal_integration.md](../MT/ml_signal_integration.md) - контракт `ml_signals.csv` и роль watcher-а в общей MT4-интеграции;
- [../ML/telemetry_daily_reconciliation.py.md](../ML/telemetry_daily_reconciliation.py.md) - ежедневная сверка expected/open/close/skip после online/test прогона.

`API/telemetry_signal_watcher.py` - фоновый Python-процесс для online telemetry-контура:

`MT4 -> Nero.csv -> causal preprocessing -> prediction CSV -> ml_signals.csv -> MT4`

Скрипт не обучает модель и не меняет frozen rule. Он только:

- ждёт новый закрытый бар в `Nero.csv`;
- строит компактный `runtime_input_snapshot.csv` из хвоста `Nero.csv`;
- строит `runtime_input_preprocessed.csv`: сортирует фракталы и выполняет rowwise-нормализацию без future labels;
- проверяет online inference contract и блокирует legacy модели, которым нужны
  future-derived row features;
- в режиме по умолчанию строит prediction CSV через
  `ML.export_entry_path_predictions` с `feature_profile=entry_path_v1_live_safe`;
- применяет frozen rule `entry_path_v1_live_safe + A @ 7.5%` через
  `API.export_entry_path_v1_signals`;
- публикует новые строки `ml_signals.csv` в runtime/tester каталогах в
  append-only режиме через временный файл и замену;
- пишет state/log/metadata.

Важно: watcher не повторяет весь offline pipeline `processing/label_main.py`.
Он выполняет только live-safe subset через
`processing.online_causal_preprocessing`: сортировку `fractal0..fractal99` по
времени убыванию и `normalize_rowwise()`. Разметка `signal/predict` через
будущие строки online не выполняется.

## Что именно он использует

- входной CSV: `MT/MQL4/Files/Nero.csv`
- default checkpoint:
  `ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/transformer_entry_path_v1_features_entry_path_v1_live_safe_best.pt`
- default frozen rule:
  `ML/reports/mt4_entry_path_v1_live_safe_parity/entry_path_v1_live_safe_a075_rule.json`
- preprocessing contract: `fractal0` = самый свежий фрактал после сортировки, rowwise-normalized признаки;
- default inference contract: `task=entry_path_v1`,
  `feature_profile=entry_path_v1_live_safe`, true targets disabled.

Важно: этот legacy contract теперь заблокирован по умолчанию для online-запуска.
Причина - `original_baseline` обучался и проверялся с row-wise признаками
`predict`, `ret_*`, `fav_*`, `adv_*`, часть которых формируется через будущие
бары и не может честно существовать в live `Nero.csv`. Чтобы не подменять эти
поля нулями и не имитировать корректный online ML, watcher выдаёт
`OnlineInferenceContractError`. Для старой механической диагностики можно явно
передать `--allow-unsafe-future-features`, но такой запуск нельзя считать
проверкой соответствия online и test.

Legacy `telemetry_frequency_v1_legacy` оставлен только для старой механической
диагностики и требует `--allow-unsafe-future-features`.

### Что из preprocessing реально нужно online

Offline training использовал более длинный pipeline:

- сортировка;
- разметка target-колонок;
- нормализация;
- split train/validation/test.

Online watcher запускает только causal часть этого pipeline. Он ожидает, что
MT4 пишет raw `Nero.csv` в рабочем runtime формате:

- `time`
- `signal`
- `predict`
- `ATR`
- `fractal0..fractal99`

После этого `processing.online_causal_preprocessing`:

- сортирует фракталы в каждой строке по `fractal_time` descending;
- проверяет, что фракталы отсортированы;
- применяет `normalize_rowwise(verbose=False, include_predict_in_front_back_pool=False)`,
  чтобы runtime log не засорялся progress-выводом нормализации и чтобы
  `predict=0` не менял масштаб `front/back`;
- сохраняет `runtime_input_preprocessed.csv`.

Затем default mode запускает `ML.export_entry_path_predictions`:

- парсит fractal-структуру;
- строит `entry_path_v1_live_safe` feature profile;
- использует runtime compatibility mode `vol_regime_24 := ATR`;
- не требует future target columns (`--no-true-targets` path);
- прогоняет seed 42 live-safe checkpoint;
- выдаёт `pred_ret_24_dir_atr` и другие prediction columns для frozen rule.

Направление сигнала в production и threshold-diagnostic режимах берётся только
из prediction/export frame: `API.export_entry_path_v1_signals` сохраняет
исходный `signal` для строк, прошедших score threshold, и обнуляет остальные.
`fractal0.direction` в этих режимах не используется.

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

Если `mtime` не изменился, watcher сразу пишет `IDLE` и не читает хвост
`Nero.csv`. Если `mtime` изменился, watcher читает последнюю непустую строку
через seek от конца файла, а не полным проходом по многолетнему CSV. Если
нового закрытого бара нет, пересчёт не делается.

Если `Nero.csv` уже создан, но пока содержит только заголовок без строк данных,
watcher не считает это ошибкой. Он пишет в `runtime_state.json`
`last_status=waiting_for_first_row`, делает запись в лог и продолжает ждать
первый закрытый бар.

Если новый бар появился:

1. из хвоста `Nero.csv` собирается raw `runtime_input_snapshot.csv` только по последним `max_runtime_rows`;
2. из snapshot строится `runtime_input_preprocessed.csv`;
3. contract guard проверяет, можно ли честно запускать выбранный checkpoint
   online;
4. по preprocessed snapshot строится `runtime_predictions.csv`;
5. exporter строит `runtime_ml_signals.csv`;
6. exporter публикует новые строки в append-only режиме в:
   - `MT/MQL4/Files/ml_signals.csv`
   - `MT/tester/files/ml_signals.csv`
7. state обновляется только после успешного rebuild.

Mode-dependent default:

- `entry_path_v1_live_safe_online`: `max_runtime_rows=1`;
- `telemetry_frequency_v1_legacy`: `max_runtime_rows=1`.

Зачем это сделано:

- цель: не перечитывать и не держать в памяти весь многолетний `Nero.csv` на каждом новом уровне;
- причина: полный single-tensor inference на десятках тысяч строк легко уходит в двузначные гигабайты RAM;
- последствие: watcher стал пригоден для более дешёвого сервера;
- ограничение: `runtime_predictions.csv` и `runtime_ml_signals.csv` содержат только рабочее окно snapshot-а, а не всю историю `Nero.csv`;
- online `MT/MQL4/Files/ml_signals.csv` и `MT/tester/files/ml_signals.csv`
  сохраняют старые строки и добавляют только строки новее текущего хвоста файла.
  Это защищает сверку от заднего изменения уже прожитых баров.

Практический смысл ограничения:

- для исходного training/offline контракта одной строки было недостаточно из-за
  `vol_regime_24 = rolling_mean(ATR, 24 rows)`;
- для frozen training/offline contract `vol_regime_24` считался как
  `rolling_mean(ATR, 24 rows)`, но watcher применяет runtime compatibility
  substitution `vol_regime_24 := ATR`;
- validation/test сравнение подтвердило `signal_mismatch_rows=0`, поэтому
  текущий production-like online/tester watcher читает только последнюю строку;
- legacy mode не получает скрытый большой default: если нужен старый
  batch/stress top-N по большому окну, `--max-runtime-rows 12000` нужно указать
  явно;
- для планового online H1-режима это безопасно, если окно заметно больше фактического числа runtime-строк за год;
- для M1 debug-режима это осознанный компромисс ради памяти;
- если понадобится полный исторический export, его нужно запускать отдельным offline/one-shot прогоном, а не постоянным watcher-ом.

## Runtime window benchmark 2026-05-13

Benchmark выполнен на `MT/MQL4/Files/Nero.csv` с последним временем
`2026.05.11 22:35`. Полный режим на `60178` строк был остановлен после 5 минут
без результата, поэтому он непригоден для online rebuild на каждом новом баре.

Production baseline `A @ 7.5%` на M5-хвосте дал `0` ненулевых сигналов во всех
проверенных окнах, потому что production export уважает исходный gate
`signal != 0`. Threshold override сохраняет этот же gate и направление из
prediction/export frame; если в runtime window нет строк `signal != 0`, он тоже
не создаст сделок.

Предыдущий all-rows stress benchmark (`top-N=5000/year`) не является parity с
production candidate, потому что игнорирует `signal != 0` и берёт direction из
`fractal0.direction`:

| Runtime window | Total rebuild | Preprocess | Prediction | Non-zero | Last time | Last signal |
|---:|---:|---:|---:|---:|---|---:|
| 1000 | 17.2170s | 10.8151s | 5.3111s | 953 | 2026.05.11 22:35 | -1 |
| 100 | 3.5414s | 1.0904s | 1.2909s | 98 | 2026.05.11 22:35 | -1 |
| 24 | 2.1494s | 0.2653s | 0.7697s | 24 | 2026.05.11 22:35 | -1 |
| 1 | 2.0840s | 0.0458s | 1.0477s | 1 | 2026.05.11 22:35 | -1 |

Последний сигнал совпал с окном `1000` для окон `100`, `24` и `1`.
Тяжёлые intermediate CSV benchmark не сохраняются в репозитории; итоговые числа
зафиксированы в этой секции.

Минимальный контекст:

- модель использует текущую строку `Nero.csv` и до `100` фракталов внутри этой
  строки; это не требует тысяч прошлых строк;
- в training/offline contract `vol_regime_24` использует rolling mean `ATR` по
  последним 24 строкам;
- в runtime watcher `vol_regime_24` заполняется текущим `ATR`; имя и позиция
  колонки сохраняются, поэтому frozen checkpoint можно использовать без
  переобучения;
- `session_hour` и `weekday` берутся из `time`;
- `range_atr_6` и `body_atr_3` остаются `0`, если в runtime `Nero.csv` нет
  OHLC rolling columns;
- окно `1` является текущим production-like runtime default. Для следующего
  retrain нужно либо честно обучать с `vol_regime_24 := ATR`, либо удалить этот
  признак из feature profile и заново выбрать rule.

## Запуск

Один проход live-safe production baseline `A @ 7.5%`:

```bash
./.venv/bin/python -m API.telemetry_signal_watcher --once --verbose
```

M5 high-frequency diagnostic, рекомендуемый путь: тот же checkpoint, та же
rule, тот же feature profile, тот же production gate `signal != 0`, то же
направление из prediction/export frame. Отличается только score threshold:

```bash
./.venv/bin/python -m API.telemetry_signal_watcher \
  --poll-interval-sec 1 \
  --heartbeat-sec 60 \
  --entry-path-score-threshold-override -0.50 \
  --verbose
```

Это diagnostic-only threshold. Его нельзя трактовать как проверку прибыльности;
production baseline остаётся `entry_path_v1_live_safe + A @ 7.5%`.

Отдельный mechanical stress mode, не parity с production candidate:

```bash
./.venv/bin/python -m API.telemetry_signal_watcher \
  --entry-path-diagnostic-all-rows \
  --diagnostic-target-signals-per-year 5000 \
  --verbose
```

Этот режим игнорирует production gate `signal != 0`, выбирает top-N строк по
score внутри года и берёт direction из `fractal0.direction`. Его нельзя
использовать как основной M5 diagnostic для `entry_path_v1_live_safe`.

Основной режим эксплуатации: отдельное окно `tmux`:

```bash
mkdir -p ML/reports/entry_path_v1_live_safe/runtime

tmux new -s telemetry-watcher
```

Внутри открывшегося окна `tmux`:

```bash
./.venv/bin/python -m API.telemetry_signal_watcher \
  --poll-interval-sec 1 \
  --heartbeat-sec 60 \
  --verbose
```

Только для старой механической диагностики связи MT4 -> Python -> CSV -> MT4:

```bash
./.venv/bin/python -m API.telemetry_signal_watcher \
  --watcher-mode telemetry_frequency_v1_legacy \
  --poll-interval-sec 1 \
  --heartbeat-sec 60 \
  --diagnostic-target-signals-per-year 5000 \
  --allow-unsafe-future-features \
  --verbose
```

Если нужен именно старый тяжёлый batch/stress-прогон legacy top-N по большому
окну, добавь `--max-runtime-rows 12000` явно. Это не production default.

MT4 online при этом запускается с `BackTest=0`, чтобы советник перебрал все
строки `#.csv` и выбрал строку `XAUUSD5`. `BackTest=2` оставлять только для
Strategy Tester.

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

4. Для первой проверки безопаснее выполнить один проход. С legacy
   `original_baseline` ожидаемый результат - `OnlineInferenceContractError`,
   потому что checkpoint требует future-derived входные признаки:

```bash
./.venv/bin/python -m API.telemetry_signal_watcher --once --verbose
```

5. Если используется live-safe checkpoint и одноразовый запуск прошёл,
   запускать watcher в отдельном окне `tmux`. Для старой механической
   диагностики можно явно добавить `--allow-unsafe-future-features`, но такой
   запуск не является ML-корректной проверкой.
6. При необходимости проверить процесс:

```bash
ps -eo pid,cmd | rg telemetry_signal_watcher
```

7. Проверить файл-лог:

```bash
tail -n 50 ML/reports/telemetry_frequency_v1/runtime/telemetry_signal_watcher.log
```

8. Нормальные состояния на экране для live-safe checkpoint:
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

11. Для точного разбора торговых расхождений дополнительно забирать per-magic
    файл `MT/MQL4/Files/ML_Trade_Events_<NAME>_<magic>.csv`: в нём есть
    `OPEN`, `OPEN_FAILED`, `CLOSE`, `Bid/Ask`, spread, OHLC бара, фактические
    цены ордера, profit, swap и commission.

## Выходные файлы

- `ML/reports/telemetry_frequency_v1/runtime/runtime_input_snapshot.csv`
- `ML/reports/telemetry_frequency_v1/runtime/runtime_input_preprocessed.csv`
- `ML/reports/telemetry_frequency_v1/runtime/runtime_predictions.csv`
- `ML/reports/telemetry_frequency_v1/runtime/runtime_ml_signals.csv`
- `ML/reports/telemetry_frequency_v1/runtime/runtime_export_metadata.json`
- `ML/reports/telemetry_frequency_v1/runtime/runtime_state.json`
- `ML/reports/telemetry_frequency_v1/runtime/telemetry_signal_watcher.log`
- `MT/MQL4/Files/ml_signals.csv` и `MT/tester/files/ml_signals.csv`
  обновляются append-only через временный файл и замену.

## Ограничения

- watcher поддерживает основной `entry_path_v1_live_safe_online` contour и
  отдельный legacy `telemetry_frequency_v1_legacy` diagnostic/stress contour;
- используется polling, а не OS-level file events;
- если `Nero.csv` испорчен или checkpoint/rule недоступны, rebuild не завершится, а ошибка уйдёт в log;
- `header-only` состояние `Nero.csv` допустимо сразу после старта expert: это не ошибка, а ожидание первого завершённого бара;
- для наблюдаемого server-режима основным способом запуска считается `tmux`, а не `nohup`;
- практические дефолты для сильного сервера: `poll=1s`, `heartbeat=60s`.
- практический лимит памяти задаётся через `--max-runtime-rows`; по умолчанию
  watcher держит последние `24` строки; большие legacy stress-окна задаются
  только явно через CLI.
