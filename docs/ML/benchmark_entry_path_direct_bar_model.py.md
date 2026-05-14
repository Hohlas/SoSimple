# benchmark_entry_path_direct_bar_model.py

`ML/benchmark_entry_path_direct_bar_model.py` проверяет прямую модель
`BUY / SELL / SKIP` для каждого бара без использования offline `signal != 0`
как условия входа.

## Назначение

Модуль обучает простой классификатор:

- train: цель строится по будущей доходности BUY и SELL от следующего бара;
- validation: выбирается порог вероятности активной сделки;
- test: frozen-порог проверяется без подбора.

В отличие от causal surrogate, этот benchmark не пытается повторить
`label_all().signal`. Модель сама выбирает и факт сделки, и направление.

## Live-safe признаки

Используются только:

- `ATR`;
- час и день недели из `time`;
- поля текущего `fractal0`: direction, front, back, strong, break, reverse,
  power, count, impulse, fractal ATR.

Python future-derived поля `predict`, `ret_*`, `fav_*`, `adv_*` не используются
как признаки. Будущая доходность используется только как обучающая цель.

## Выходы

По умолчанию:

```text
ML/reports/entry_path_v1_direct_bar_model/
```

Файлы:

- `summary.json`
- `summary.md`
- `validation_summary.csv`
- `test_selected_rows.csv`

## Запуск

```bash
./.venv/bin/python -m ML.benchmark_entry_path_direct_bar_model
```

## Ограничение

Это исследовательский benchmark. Он не меняет production export и не создаёт
готовый `ml_signals.csv`. Для production нужен отдельный retrain/калибровка и
проверка в MT4.
