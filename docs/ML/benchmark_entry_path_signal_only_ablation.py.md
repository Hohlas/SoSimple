# benchmark_entry_path_signal_only_ablation.py

`ML/benchmark_entry_path_signal_only_ablation.py` измеряет вклад offline
`signal != 0` в `entry_path_v1_live_safe` без ML score-фильтра.

## Назначение

Модуль сравнивает два режима на одном prediction CSV:

- `signal_only`: выбираются все строки `signal != 0`;
- `current_score_gate`: выбираются строки `(signal != 0) & (pred_ret_24_dir_atr >= threshold)`.

Это read-only benchmark. Он не переобучает модель, не меняет frozen rule и не
публикует `ml_signals.csv` в MT4.

## Входы

По умолчанию используется:

```text
ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/test_predictions.csv
```

CSV должен содержать:

- `time`
- `signal`
- `pred_ret_24_dir_atr`
- `true_ret_24_dir_atr`

## Выходы

По умолчанию артефакты пишутся в:

```text
ML/reports/entry_path_v1_signal_only_ablation/
```

Файлы:

- `summary.json` — машинно-читаемая сводка;
- `summary.md` — краткий отчёт;
- `selected_rows.csv` — все `signal != 0` строки с пометкой, прошли ли они current score gate.

## Запуск

```bash
./.venv/bin/python -m ML.benchmark_entry_path_signal_only_ablation
```

С явными параметрами:

```bash
./.venv/bin/python -m ML.benchmark_entry_path_signal_only_ablation \
  --predictions ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/test_predictions.csv \
  --threshold -0.07158749 \
  --output-dir ML/reports/entry_path_v1_signal_only_ablation \
  --sequential-hold-bars 24
```

## Интерпретация

Если `signal_only` уже даёт сильный PF, значит основная часть edge приходит из
offline candidate universe. Если `current_score_gate` заметно лучше, модель
вносит самостоятельный фильтрующий вклад, но всё равно поверх недоступного live
`signal`.
