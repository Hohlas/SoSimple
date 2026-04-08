# Entry Path v1: исправленный первый baseline

> **Date**: 2026-04-08 22:49 MSK
> **Status**: Completed
> **Goal**: Собрать первый честный baseline для `entry_path_v1`, найти причину ложных ранних цифр и зафиксировать уже очищенные результаты
> **Related plan/spec**: `docs/superpowers/specs/2026-04-08-entry-path-v1-design.md`, `docs/superpowers/plans/2026-04-08-entry-path-v1.md`
> **Related commit**: pending

## Context

`entry_path_v1` был собран как новый трек между `regression_updn` и `triple_barrier`: с реальным входом на следующем баре, отдельными целями для общего итога сделки и отдельными целями для пути цены.

Первый baseline уже был собран и даже зафиксирован в коммите, но сразу после этого выяснилось, что его главные числа нельзя считать честными. Причина оказалась не в самой идее `ret_*`, а в ошибке запуска обучения.

## What Was Done

- В `processing/label_signals.py` и `processing/label_main.py` осталась собранная схема `entry_path_v1`:
  - `ret_6_dir_atr`, `ret_12_dir_atr`, `ret_24_dir_atr`
  - `fav_3_atr`, `adv_3_atr`
  - `fav_6_atr`, `adv_6_atr`
  - `fav_12_atr`, `adv_12_atr`
  - `fav_24_atr`, `adv_24_atr`
  - `path_6_class`
- В `ML` остался весь новый трек:
  - `ML/entry_path_task.py`
  - `ML/data_loader.py`
  - `ML/models/entry_path_transformer.py`
  - `ML/train.py`
  - `ML/evaluate_test.py`
  - `API/generate_signals.py`
- После первого baseline был найден баг в `ML/train.py`:
  - CLI принимал `--clear_cache`, но не передавал его в `train_model()`
  - из-за этого обучение шло на старом `entry_path` кэше
- Добавлен тест `tests/test_entry_path_training.py`, который ловит именно этот баг.
- После исправления был сделан чистый rebuild train/validation кэша и повторное обучение.
- Заново выпущены:
  - `transformer_entry_path_v1_best.pt`
  - `transformer_entry_path_v1_result.json`
  - `evaluate_test_entry_path_v1.md`
  - `entry_path_v1_validation_predictions.csv`
  - `entry_path_v1_test_predictions.csv`
- В `ML/entry_path_task.py` markdown-отчёт расширен active-only секцией, чтобы отдельно видеть качество на реальных BUY/SELL строках.

## Root Cause

Главная причина ложных ранних результатов была такой:

- `--clear_cache` не доходил до `train_model()`;
- из-за этого `DATA/y_train_entry_path_v1_*.npy` и `DATA/y_val_entry_path_v1_*.npy` не пересобирались;
- в старом кэше у строк с `signal=0` были ненулевые `ret_*`, чего по текущему дизайну быть не должно.

Проверка это подтвердила прямо:

- до исправления в train `41556` строк с `signal=0` имели ненулевые `ret_*`;
- до исправления в validation `8905` строк с `signal=0` имели ненулевые `ret_*`;
- после честной пересборки в обоих split это стало `0`.

Именно поэтому старое значение `best_ret_pearson_r=0.5253` оказалось ложным.

## Changed Files

- `ML/train.py` (обновлён)
- `tests/test_entry_path_training.py` (создан)
- `ML/checkpoints/transformer_entry_path_v1_best.pt` (обновлён)
- `ML/checkpoints/transformer_entry_path_v1_result.json` (обновлён)
- `ML/reports/evaluate_test_entry_path_v1.md` (обновлён)
- `ML/reports/entry_path_test_predictions.csv` (обновлён)
- `ML/reports/entry_path_v1_validation_predictions.csv` (обновлён)
- `ML/reports/entry_path_v1_test_predictions.csv` (обновлён)
- `ML/entry_path_task.py` (обновлён; добавлен active-only блок в markdown-report)
- `tests/test_entry_path_reports.py` (обновлён)

Ниже перечислены и файлы самого baseline, которые остаются актуальными после исправления:

- `processing/label_signals.py`
- `processing/label_main.py`
- `ML/data_loader.py`
- `ML/models/entry_path_transformer.py`
- `ML/evaluate_test.py`
- `API/generate_signals.py`
- `tests/test_entry_path_labels.py`
- `tests/test_entry_path_task.py`
- `tests/test_entry_path_model.py`

## Verification

```bash
./.venv/bin/python -m pytest tests/test_entry_path_labels.py tests/test_entry_path_task.py tests/test_entry_path_model.py tests/test_entry_path_reports.py tests/test_entry_path_training.py -q
./.venv/bin/python -m ML.train --model transformer --task entry_path_v1 --epochs 5 --seed 42
./.venv/bin/python -m ML.evaluate_test --task entry_path_v1 --model transformer
./.venv/bin/python -m API.generate_signals --task entry_path_v1 --model transformer --research-out-prefix ML/reports/entry_path_v1
```

Observed:

- `pytest`: `15 passed`
- чистый retrain завершён на `epoch=5`
- новый `transformer_entry_path_v1_result.json` сохранён
- новый `evaluate_test_entry_path_v1.md` сохранён
- новые validation/test exports сохранены

## Results

### Что было ложным в старом baseline

| Metric | Старое значение |
|---|---:|
| `best_ret_pearson_r` на validation | `0.5253` |
| `ret_pearson_r` на test | `-0.0216` |

Эти числа больше не актуальны и не должны использоваться.

### Чистый baseline после исправления

| Metric | Validation | Test |
|---|---:|---:|
| `ret_pearson_r` | `0.2656` | `0.2450` |
| `path_reg_pearson_r` | `0.3004` | `0.2745` |
| `path_cls_f1_macro` | `0.3261` | `0.3259` |

### Return targets на test

| Target | Pearson r | MAE |
|---|---:|---:|
| `ret_6_dir_atr` | `0.2317` | `0.0991` |
| `ret_12_dir_atr` | `0.2486` | `0.1327` |
| `ret_24_dir_atr` | `0.2546` | `0.2027` |

### Path targets на test

| Target | Pearson r | MAE |
|---|---:|---:|
| `fav_6_atr` | `0.2219` | `0.0574` |
| `adv_6_atr` | `0.3434` | `0.1306` |
| `fav_12_atr` | `0.1955` | `0.0690` |
| `adv_12_atr` | `0.3446` | `0.1749` |
| `fav_24_atr` | `0.1811` | `0.0877` |
| `adv_24_atr` | `0.3605` | `0.2569` |

### Active-only на test

Это более честный срез только по строкам, где есть BUY или SELL.

| Metric | Value |
|---|---:|
| active rows | `480` |
| active `ret_pearson_r` | `0.2039` |

| Target | Pearson r | MAE |
|---|---:|---:|
| `ret_6_dir_atr` | `0.2075` | `1.4417` |
| `ret_12_dir_atr` | `0.2025` | `1.9800` |
| `ret_24_dir_atr` | `0.2016` | `3.3222` |

### Active-only срез по `pred_ret_24_dir_atr`

| Slice | Rows | mean `true_ret_24_dir_atr` | positive share |
|---|---:|---:|---:|
| Bottom 10% | `48` | `-2.2741` | `20.8%` |
| Top 10% | `48` | `0.2442` | `56.2%` |

### `path_6_class`

Общий F1 по этому слою почти не меняется, но есть важное ограничение:

- на validation и test модель почти всегда предсказывает класс `0`;
- на реальных активных строках это видно ещё лучше:
  - validation active true classes: `{-1: 307, 0: 73, 1: 93}`
  - validation active predicted classes: `{0: 473}`
  - test active true classes: `{-1: 309, 0: 70, 1: 101}`
  - test active predicted classes: `{0: 480}`

## Conclusions

После исправления картина стала гораздо понятнее.

Что выяснилось:

- главная старая проблема была не в самих `ret_*`, а в старом кэше обучения;
- после честной пересборки `ret_*` уже не выглядит ни “чудесно сильным”, ни сломанным;
- на test `ret_*` и `fav/adv` теперь переносятся похоже на validation;
- отдельный active-only срез показывает, что в реальных сделках модель уже разделяет плохие и относительно лучшие случаи.

Что остаётся слабым:

- `path_6_class` пока почти не работает как отдельная цель;
- обучение всё ещё сильно разбавлено строками `signal=0`, которых около `95%`;
- поэтому общие метрики по всем строкам надо читать осторожно, а не как прямую меру качества реальных сделок.

Итог этапа теперь такой: `entry_path_v1` имеет смысл как рабочий baseline и как исследовательский трек. Старый отчёт с отрицательным выводом про `ret_*` больше не актуален.

## Limitations / Open Questions

- Ветка всё ещё нуждается в одном чистом полном rebuild через штатный `label_main` до merge в main.
- `path_6_class` почти целиком проигрывает из-за перекоса данных.
- В loss сейчас все строки участвуют одинаково, хотя активных сигналов только около `5%`.
- Следующий вопрос уже не “сломаны ли `ret_*`?”, а “как лучше учить реальную сделку при таком сильном перекосе нулевых строк?”

## Next Step

Следующий шаг я считаю таким:

1. проверить вариант обучения, где `ret_*` и `path_6_class` считаются только по активным строкам;
2. сравнить этот вариант с текущим baseline на validation и test;
3. отдельно решить, нужен ли `path_6_class` в `v1` вообще или его лучше временно ослабить / убрать;
4. перед merge в main сделать один чистый полный rebuild датасета и артефактов.

## Related Materials

- `docs/superpowers/specs/2026-04-08-entry-path-v1-design.md`
- `docs/superpowers/plans/2026-04-08-entry-path-v1.md`
- `ML/checkpoints/transformer_entry_path_v1_result.json`
- `ML/reports/evaluate_test_entry_path_v1.md`
- `ML/reports/entry_path_v1_validation_predictions.csv`
- `ML/reports/entry_path_v1_test_predictions.csv`
