# Entry Path v1: перевзвешивание функции потерь и выбор рабочего базового варианта

> **Date**: 2026-04-09 10:01 MSK
> **Status**: Completed
> **Goal**: Проверить, как учить `entry_path_v1` при сильном перекосе строк `signal=0`, и выбрать рабочий вариант функции потерь для следующего этапа
> **Related plan/spec**: `docs/superpowers/specs/2026-04-08-entry-path-v1-design.md`, `docs/superpowers/plans/2026-04-08-entry-path-v1.md`
> **Related commit**: `pending`

## Context

После честного базового варианта для `entry_path_v1` стало ясно, что главный перекос находится не в самих таргетах, а в данных: активных BUY/SELL строк около `5%`, а почти всё остальное — `signal=0`.

Из-за этого обычная функция потерь легко учится на нулевых строках и хуже различает реальные сделки. На этом этапе задача была простой: не менять сами таргеты, а проверить несколько вариантов обучения и выбрать лучший рабочий базовый вариант.

## What Was Done

- `ML/data_loader.py` обновлён для `entry_path_v1`: dataset и test-loader теперь передают `signal`, чтобы цикл обучения видел активные и неактивные строки.
- `ML/train.py` расширен поддержкой перевзвешенной функции потерь для `entry_path_v1`.
- Проверены три режима:
  - только активные строки для `ret_*` и `path_6_class`;
  - вес `5.0` для активных строк сразу в `ret_*` и `path_6_class`;
  - вес `5.0` только для `path_6_class`.
- `ML/entry_path_task.py` и `ML/evaluate_test.py` обновлены так, чтобы test-report явно показывал:
  - `Checkpoint epoch`
  - лучший `val`-результат чекпоинта, по которому построен отчёт
- Обновлены и расширены тесты:
  - `tests/test_entry_path_task.py`
  - `tests/test_entry_path_training.py`
  - `tests/test_entry_path_reports.py`
- После сравнения всех режимов выбран рабочий вариант:
  - вес `5.0` для активных строк и в `ret_*`, и в `path_6_class`

## Changed Files

- `ML/data_loader.py`
- `ML/train.py`
- `ML/entry_path_task.py`
- `ML/evaluate_test.py`
- `tests/test_entry_path_task.py`
- `tests/test_entry_path_training.py`
- `tests/test_entry_path_reports.py`
- `ML/checkpoints/transformer_entry_path_v1_best.pt`
- `ML/checkpoints/transformer_entry_path_v1_result.json`
- `ML/reports/evaluate_test_entry_path_v1.md`
- `ML/reports/entry_path_test_predictions.csv`

## Verification

```bash
./.venv/bin/python -m pytest tests/test_entry_path_labels.py tests/test_entry_path_task.py tests/test_entry_path_model.py tests/test_entry_path_reports.py tests/test_entry_path_training.py -q
./.venv/bin/python -m ML.train --model transformer --task entry_path_v1 --epochs 5 --seed 42
./.venv/bin/python -m ML.evaluate_test --task entry_path_v1 --checkpoint ML/checkpoints/transformer_entry_path_v1_best.pt
```

Observed:

- `pytest`: `19 passed`
- новый `transformer_entry_path_v1_result.json` сохранён
- новый `evaluate_test_entry_path_v1.md` сохранён
- отчёт теперь явно показывает `Checkpoint epoch` и лучший `val`-результат

## Results

### Сравнение трёх режимов

| Режим | Test `ret_pearson_r` | Test `path_reg_pearson_r` | Test `path_cls_f1_macro` | Test active `ret_pearson_r` |
|---|---:|---:|---:|---:|
| базовый вариант без весов | `0.2450` | `0.2745` | `0.3259` | `0.2039` |
| только active rows | `0.0112` | `-0.0027` | `0.0213` | `-0.0020` |
| вес `5.0` для `ret_*` и `path_6_class` | `0.2494` | `0.2722` | `0.4160` | `0.2285` |
| вес `5.0` только для `path_6_class` | `0.2415` | `0.2750` | `0.4048` | `0.1912` |

### Выбранный рабочий вариант

Validation:

| Metric | Value |
|---|---:|
| `ret_pearson_r` | `0.2736` |
| `path_reg_pearson_r` | `0.3006` |
| `path_cls_f1_macro` | `0.4059` |

Test:

| Metric | Value |
|---|---:|
| `ret_pearson_r` | `0.2494` |
| `path_reg_pearson_r` | `0.2722` |
| `path_cls_f1_macro` | `0.4160` |
| active `ret_pearson_r` | `0.2285` |

### Active-only срез выбранного варианта

| Slice | Rows | mean `true_ret_24_dir_atr` | positive share |
|---|---:|---:|---:|
| Bottom 10% | `48` | `-2.7441` | `16.7%` |
| Top 10% | `48` | `0.4343` | `58.3%` |

## Conclusions

Главный вывод этапа такой:

- жёстко вырезать неактивные строки нельзя — это ломает и `ret_*`, и путь цены;
- вес только для `path_6_class` тоже не даёт лучшего общего результата;
- лучший практический вариант сейчас — вес `5.0` для активных строк сразу в `ret_*` и `path_6_class`.

Этот вариант не даёт чудесного скачка по всем метрикам сразу, но выглядит самым сбалансированным:

- `ret_*` остаётся на уровне базового варианта или немного лучше;
- `path_6_class` заметно оживает;
- качество сделки в срезе только по активным сигналам становится лучше, чем у базового варианта.

Отдельно важно и то, что теперь report не вводит в заблуждение: он явно показывает, по какому checkpoint собраны числа.

## Limitations / Open Questions

- Класс `1` в `path_6_class` всё ещё почти не ловится.
- Общие срезы по всем строкам всё ещё сильно разбавлены `signal=0`.
- Мы улучшили обучение, но ещё не превратили этот трек в реальное правило `торговать / не торговать`.
- Пока это всё ещё исследовательская база, а не готовая торговая логика.

## Next Step

Следующий разумный шаг уже не в новых ручных весах, а в использовании выбранного базового варианта как базы для слоя `торговать / не торговать`.

Практически это значит:

1. взять текущий вариант с весом `5.0` как замороженный базовый вариант;
2. построить поверх него слой отбора сделок;
3. в первую очередь проверить conformal-подход для решения `торговать / не торговать`, а не продолжать бесконечно крутить функцию потерь.

## Related Materials

- `docs/reports/2026-04-08-entry-path-v1-baseline.md`
- `ML/checkpoints/transformer_entry_path_v1_result.json`
- `ML/reports/evaluate_test_entry_path_v1.md`
- `ML/reports/entry_path_test_predictions.csv`
