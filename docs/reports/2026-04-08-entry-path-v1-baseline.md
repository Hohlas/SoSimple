# Entry Path v1: первый baseline и рабочие артефакты

> **Date**: 2026-04-08 22:19 MSK
> **Status**: Completed
> **Goal**: Добавить новый ML-трек `entry_path_v1`, собрать первый baseline с реальным входом на следующем баре, выпустить исследовательские артефакты и честно зафиксировать первые результаты
> **Related plan/spec**: `docs/superpowers/specs/2026-04-08-entry-path-v1-design.md`, `docs/superpowers/plans/2026-04-08-entry-path-v1.md`
> **Related commit**: pending

## Context

После этапа с Triple Barrier стало ясно, что проекту нужен ещё один трек между двумя крайностями:

- `regression_updn` слишком слабо связан с реальной сделкой;
- `triple_barrier` слишком жёстко привязывает обучение к одной схеме выхода.

`entry_path_v1` задуман как более гибкий слой. Он должен смотреть на реальный вход со следующего бара, отдельно оценивать общий итог идеи и отдельно путь цены после входа.

Главный вопрос этого baseline был простой: можно ли на текущих признаках получить рабочий первый прогноз для новых `ret_*`, `fav/adv` и `path_6_class`.

## What Was Done

- В `processing/label_signals.py` добавлены новые цели:
  - `ret_6_dir_atr`, `ret_12_dir_atr`, `ret_24_dir_atr`
  - `fav_3_atr`, `adv_3_atr`
  - `fav_6_atr`, `adv_6_atr`
  - `fav_12_atr`, `adv_12_atr`
  - `fav_24_atr`, `adv_24_atr`
  - `path_6_class`
- В `processing/label_main.py` новый слой разметки подключён в основной pipeline.
- Добавлен контракт нового трека в `ML/entry_path_task.py`:
  - списки таргетов;
  - mapping классов;
  - export frame для исследовательских CSV;
  - helper для markdown-отчёта по test.
- В `ML/data_loader.py` добавлен режим `entry_path_v1` с отдельными регрессионными и классификационными целями.
- Создана новая модель `ML/models/entry_path_transformer.py`:
  - общий transformer encoder;
  - общая голова;
  - три выхода: `ret`, `path_reg`, `path_cls`.
- В `ML/train.py` добавлен полный цикл обучения `entry_path_v1`.
- В `ML/evaluate_test.py` добавлена test-оценка нового трека и подробный markdown-отчёт.
- В `API/generate_signals.py` добавлен research-only export для `entry_path_v1` без выпуска MT4 CSV.
- Добавлены тесты:
  - `tests/test_entry_path_labels.py`
  - `tests/test_entry_path_task.py`
  - `tests/test_entry_path_model.py`
  - `tests/test_entry_path_reports.py`
- Выпущены baseline-артефакты:
  - checkpoint;
  - result JSON;
  - test-report;
  - validation/test prediction exports.

Дополнительно по ходу этапа:

- test split был отдельно доведён до того же формата `entry_path_v1`, что и train/validation;
- итоговый `transformer_entry_path_v1_result.json` синхронизирован с реальным лучшим checkpoint после отдельного validation-pass.

## Changed Files

- `processing/label_signals.py` (обновлён)
- `processing/label_main.py` (обновлён)
- `ML/entry_path_task.py` (создан)
- `ML/data_loader.py` (обновлён)
- `ML/models/entry_path_transformer.py` (создан)
- `ML/train.py` (обновлён)
- `ML/evaluate_test.py` (обновлён)
- `API/generate_signals.py` (обновлён)
- `tests/test_entry_path_labels.py` (создан)
- `tests/test_entry_path_task.py` (создан)
- `tests/test_entry_path_model.py` (создан)
- `tests/test_entry_path_reports.py` (создан)
- `ML/checkpoints/transformer_entry_path_v1_best.pt` (создан)
- `ML/checkpoints/transformer_entry_path_v1_result.json` (создан)
- `ML/reports/evaluate_test_entry_path_v1.md` (создан)
- `ML/reports/entry_path_test_predictions.csv` (создан)
- `ML/reports/entry_path_v1_validation_predictions.csv` (создан)
- `ML/reports/entry_path_v1_test_predictions.csv` (создан)
- `docs/superpowers/plans/2026-04-08-entry-path-v1.md` (создан)

## Verification

```bash
./.venv/bin/python -m pytest tests/test_entry_path_labels.py tests/test_entry_path_task.py tests/test_entry_path_model.py tests/test_entry_path_reports.py -q
./.venv/bin/python -m ML.train --model transformer --task entry_path_v1 --epochs 50 --seed 42 --clear_cache
./.venv/bin/python -m ML.evaluate_test --task entry_path_v1 --model transformer
./.venv/bin/python -m API.generate_signals --task entry_path_v1 --model transformer --research-out-prefix ML/reports/entry_path_v1
```

Observed:

- `pytest`: `14 passed`
- В обучении лучший checkpoint был получен на `epoch=5`
- `ML/reports/evaluate_test_entry_path_v1.md` создан
- `ML/reports/entry_path_v1_validation_predictions.csv` создан
- `ML/reports/entry_path_v1_test_predictions.csv` создан

## Results

### Лучший checkpoint на validation

| Metric | Value |
|---|---:|
| Best epoch | `5` |
| `best_ret_pearson_r` | `0.5253` |
| `path_reg_pearson_r` | `0.1641` |
| `path_cls_f1_macro` | `0.3247` |

### Test summary

| Metric | Value |
|---|---:|
| Rows | `9378` |
| `ret_pearson_r` | `-0.0216` |
| `path_reg_pearson_r` | `0.1694` |
| `path_cls_f1_macro` | `0.3259` |

### Return targets on test

| Target | Pearson r | MAE |
|---|---:|---:|
| `ret_6_dir_atr` | `-0.0296` | `0.1719` |
| `ret_12_dir_atr` | `-0.0264` | `0.1795` |
| `ret_24_dir_atr` | `-0.0086` | `0.2248` |

### Path targets on test

| Target group | Range of Pearson r |
|---|---:|
| `fav_*` | `0.0715 .. 0.1362` |
| `adv_*` | `0.1779 .. 0.2660` |

### Срез по `pred_ret_24_dir_atr`

| Slice | Rows | mean `true_ret_24_dir_atr` | positive share |
|---|---:|---:|---:|
| Bottom 10% | `937` | `-0.4176` | `2.6%` |
| Top 10% | `937` | `-0.1612` | `0.2%` |

### `path_6_class` на test

| Class | F1 |
|---|---:|
| `-1` | `0.0000` |
| `0` | `0.9777` |
| `1` | `0.0000` |

## Conclusions

Этап дал рабочий baseline и полезный честный вывод.

Что уже получилось:

- новый трек `entry_path_v1` собран end-to-end;
- train / evaluation / export работают;
- путь цены после входа модель уже ловит лучше, чем общий итог сделки;
- исследовательские CSV готовы для будущего слоя `trade / no-trade`.

Что пока не получилось:

- главные `ret_*` цели хорошо выглядят на validation, но не держатся на test;
- ранний класс `path_6_class` почти вырождается в один класс `0`;
- даже верхний слой по `pred_ret_24_dir_atr` на test остаётся отрицательным.

Иными словами: baseline уже полезен как исследовательский инструмент, но пока не годится как готовый основной сигнал.

## Limitations / Open Questions

- В этой ветке полный `label_main` на всём наборе не был доведён до штатного финала одним проходом: train/validation уже были локально пересчитаны, а test был отдельно дополнен новым слоем `entry_path_v1`. Для merge в main нужен ещё один чистый полный rebuild.
- Обучение было остановлено после получения устойчивого лучшего checkpoint на `epoch=5`, поэтому `training_time` в `transformer_entry_path_v1_result.json` не заполнен.
- Главный открытый вопрос этапа: почему `ret_*` выглядит сильно на validation и слабо на test.
- Отдельно нужно понять, это проблема:
  - самих новых таргетов;
  - перекоса train/validation/test;
  - веса loss между `ret`, `path_reg`, `path_cls`;
  - или слабости текущих входных признаков именно для `ret_*`.

## Next Step

Не менять таргеты вслепую. Следующий шаг:

1. разобрать разрыв между validation и test именно по `ret_*`;
2. сравнить распределения `ret_*` и ranking quality по split;
3. проверить, не тянет ли модель к ложному улучшению на validation при слабом переносе;
4. только после этого решать, править loss / архитектуру или менять сам главный таргет.

## Related Materials

- `docs/superpowers/specs/2026-04-08-entry-path-v1-design.md`
- `docs/superpowers/plans/2026-04-08-entry-path-v1.md`
- `ML/checkpoints/transformer_entry_path_v1_result.json`
- `ML/reports/evaluate_test_entry_path_v1.md`
- `ML/reports/entry_path_v1_validation_predictions.csv`
- `ML/reports/entry_path_v1_test_predictions.csv`
