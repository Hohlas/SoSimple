# api_server.py

## Назначение
Экспериментальный FastAPI-сервер для запроса ML-сигнала по одному набору
фракталов из MT4.

## Текущий статус
`API/api_server.py` не является основным production online-контуром. Основной
наблюдаемый путь сейчас - `API.telemetry_signal_watcher`.

Если сервер всё же используется для inference, он обязан повторять ту же
live-safe подготовку, что и watcher:

- сортировка `fractal0..fractal99` по `fractal_time` descending;
- проверка порядка фракталов;
- `normalize_rowwise(verbose=False, include_predict_in_front_back_pool=False)`;
- без `label_all()` и без future-derived target-разметки.

Для этого endpoint `/predict` вызывает
`processing.online_causal_preprocessing.preprocess_online_frame()`, а не
`normalize_rowwise()` напрямую.

## Вход
`POST /predict`:

- `atr_slow`: ATR для строки;
- `fractals`: ровно 100 строк формата фрактала.

## Ограничение
Сервер по-прежнему относится к старому `regression_updn` API-контракту. Перед
любым production-использованием нужно отдельно проверить, что checkpoint и
набор признаков live-safe и не требуют future-derived row features.
