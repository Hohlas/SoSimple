# benchmark_entry_based_movement_filter_freeze.py

`ML/baseline/benchmark_entry_based_movement_filter_freeze.py` реплицирует и
замораживает ровно один заранее выбранный entry-based movement filter.

Его задача узкая: проверить source hashes, exact frozen rule и заново
материализовать score-кадры только для одного выбранного правила. Скрипт не
делает новый search и не выбирает winner повторно.

## Назначение

- зафиксировать exact movement segmentation rule для следующего research plan;
- подтвердить, что source artifact не подменён;
- выписать reproducible JSON/CSV со split-метриками, yearly-срезами, random
  baseline и score cutoff diagnostics.

## Входы

CLI:

- `--movement-filter-source` — путь к `ML/reports/entry_based_movement_filter.json`;
- `--amplitude-source` — путь к `ML/reports/entry_based_amplitude_movement.json`;
- `--output-prefix` — префикс выходных файлов;
- `--allow-noncanonical-source` — только для тестов и fixture, не для
  исследовательского прогона.

По умолчанию runner требует только канонические source paths:

- `ML/reports/entry_based_movement_filter.json`
- `ML/reports/entry_based_amplitude_movement.json`

## Frozen rule

Замороженное правило жёстко задано в коде:

```json
{"profile":"simple_combined","model_key":"extra_trees_small","horizon":3,"target_family":"entry_movement","threshold_type":"top_fraction","selected_fraction":0.05,"score_aggregation":"median_across_rerun_seeds","seeds":[42,43,44]}
```

- `rule_hash`: `56361f12104b55c4cac6bd04426349f71d8944c139563a8c9b68d3b25e97deaf`
- `frozen_config_hash`: `ee2701d0566e910e8a0fb10c6d4f5a8916d2b4e5b903e9dc50f39354344e86b6`

## Source guards

Runner аварийно завершает шаг, если нарушено хотя бы одно условие:

- path source artifact не канонический;
- hash `entry_based_amplitude_movement.json` не совпадает с hash, записанным в
  `entry_based_movement_filter.json`;
- `selected_filter` в source artifact не совпадает с frozen rule;
- `locked_test != not_opened`.

Дополнительно сохраняется `contract_status` со статусами:

- `source_hash_status`
- `frozen_rule_status`
- `frozen_rule_hash_match`
- `locked_test`

## Выходы

- `ML/reports/entry_based_movement_filter_freeze.json`
- `ML/reports/entry_based_movement_filter_freeze_yearly.csv`
- `ML/reports/entry_based_movement_filter_freeze_selected_rows.csv`
- `ML/reports/entry_based_movement_filter_freeze_scores.csv`
- `ML/reports/entry_based_movement_filter_freeze_random_baseline.csv`
- `ML/reports/entry_based_movement_filter_freeze_score_cutoffs.csv`

## Score export schema

`*_scores.csv` и `*_selected_rows.csv` используют одинаковую схему:

| Column | Смысл |
|---|---|
| `split` | `train`, `val_select`, `val_eval`, `low_n_disclosure` |
| `split_row_id` | позиция строки внутри split-а после построения split-ов; стабильный ключ для join |
| `time` | исходный timestamp строки |
| `year` | календарный год |
| `score` | агрегированный score правила |
| `entry_movement_3` | фактическая величина движения для `H3` |
| `selected` | входит ли строка в top `5%` по своему split |

`time` не является уникальным ключом: один бар может дать несколько entry-строк
с разными фракталами. Для downstream join нужно использовать `split + split_row_id`,
а не `split + time`.

`*_score_cutoffs.csv`:

| Column | Смысл |
|---|---|
| `scope` | `split` или `year` |
| `split` | имя split |
| `score_cutoff` | cutoff top `5%` внутри набора |
| `selected_n` | число выбранных строк |
| `total_n` | полный размер набора |
| `year` | год для yearly-строк |

## Allowed verdicts

- `FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN`
- `RESEARCH_ONLY_REPLICATED`
- `REJECT_MOVEMENT_FILTER_FREEZE`
- `ABORT_CONTRACT_FAIL`

Сильнейший разрешённый verdict не делает результат торговым кандидатом. Он
означает только замороженный research segmentation mask для следующего плана.

## Логика verdict

Жёсткие gate:

- `val_select.selected_n >= 300`
- `val_select.movement_lift >= 1.80`
- `val_select.selected_p80 > skipped_p80`
- `val_eval.selected_n >= 300`
- `val_eval.movement_lift >= 1.50`
- `val_eval.selected_p80 > skipped_p80`
- `val_eval.yearly_lift_pass_rate >= 0.80`
- в каждом `val_eval` yearly slice `selected_n >= 50`
- disclosure years ровно `[2026]`

Предупреждения понижают verdict до `RESEARCH_ONLY_REPLICATED`, например:

- слабый `val_eval.spearman`;
- yearly lift слабее warning-порога;
- random baseline `p95` не ниже фактического lift;
- warning в `score_cutoff_diagnostics`.

## Запуск

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_movement_filter_freeze.py \
  --movement-filter-source ML/reports/entry_based_movement_filter.json \
  --amplitude-source ML/reports/entry_based_amplitude_movement.json \
  --output-prefix ML/reports/entry_based_movement_filter_freeze
```

## Тесты

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter_freeze.py -q
```

Покрытие тестов:

- exact frozen rule и stable hash;
- source hash validation;
- fixed top `5%` selection;
- score export schema;
- score cutoff diagnostics;
- verdict branching;
- CLI smoke на fixture artifacts.

## Ограничения

- runner не открывает `locked_test`;
- runner не выбирает direction;
- runner не считает PnL/PF;
- runner не даёт live cutoff, потому что `top_fraction=0.05` зависит от набора;
- `2026` используется только как disclosure;
- `selected_rows.csv` — это audit export, а не торговый сигнал.
