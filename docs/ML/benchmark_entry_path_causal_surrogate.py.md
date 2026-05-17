# benchmark_entry_path_causal_surrogate.py

`ML/benchmark_entry_path_causal_surrogate.py` проверяет, можно ли заменить
offline `label_all().signal` причинной моделью по live-доступным полям
текущего `fractal0`.

## Назначение

Модуль обучает простой классификатор `BUY / SELL / SKIP`:

- train: учится воспроизводить offline `signal`;
- validation: выбирает порог вероятности active-сигнала;
- test: проверяет frozen-порог без подбора.

После surrogate-сигнала применяется старый score gate
`pred_ret_24_dir_atr >= -0.07158749`.

## Live-safe признаки

Используются только:

- `ATR`;
- час и день недели из `time`;
- поля текущего `fractal0`: direction, front, back, strong, break, reverse,
  power, count, impulse, fractal ATR.

Python future-derived поля `predict`, `ret_*`, `fav_*`, `adv_*` не используются.

## Выходы

По умолчанию:

```text
ML/reports/entry_path_v1_causal_surrogate/
```

Файлы:

- `summary.json`
- `summary.md`
- `validation_summary.csv`
- `test_selected_rows.csv`

## Запуск

```bash
./.venv/bin/python -m ML.benchmark_entry_path_causal_surrogate
```

## Ограничение

Это не новая production-система. Проверка показывает, есть ли смысл дальше
развивать причинный candidate-source. Для production нужен отдельный retrain
или forward-проверка.
