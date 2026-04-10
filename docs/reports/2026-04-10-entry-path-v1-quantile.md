# Entry Path v1 Quantile: гибридный трек с quantile-головами

> **Date**: 2026-04-10 21:40
> **Status**: Completed
> **Goal**: Проверить, может ли гибридный `entry_path_v1_quantile` улучшить рабочую базу `A @ 7.5%` через слой `trade / no-trade` на основе `LB/UB`
> **Related plan/spec**: `docs/superpowers/specs/2026-04-10-entry-path-v1-quantile-design.md`, `docs/superpowers/plans/2026-04-10-entry-path-v1-quantile.md`
> **Related commit**: pending

## Context

До этого отдельные conformal/CQR-попытки поверх старого экспорта не давали устойчивого улучшения.  
Новый этап проверял более сильный путь: не внешний пост-слой, а quantile-головы внутри рабочего `entry_path_v1`-представления.

## What Was Done

- Добавлен новый трек `entry_path_v1_quantile`:
  - сохранены рабочие головы `entry_path_v1`;
  - добавлены `ret_24_q10` и `ret_24_q90`.
- Доработан train/eval/export/filter-контур:
  - `entry_path_v1_quantile` встроен в loader/train/evaluate CLI;
  - отдельный экспорт `train/validation/test` для quantile-трека;
  - benchmark фильтра поверх уже замороженной базы `A @ 7.5%`.
- Усилены проверки после code-review:
  - на `test` проверяется только frozen winner с `validation`;
  - conformal correction переведён на finite-sample формулу;
  - quantile summary в отчёте считается по active rows;
  - в артефактах явно выводится `crossed_quantile_rows`;
  - в benchmark добавлена последовательная проверка c `sequential_hold_bars` из frozen baseline.

## Changed Files

- `ML/models/entry_path_v1_quantile_transformer.py`
- `ML/entry_path_v1_quantile_task.py`
- `ML/data_loader.py`
- `ML/train.py`
- `ML/evaluate_test.py`
- `ML/export_entry_path_v1_quantile_predictions.py`
- `ML/benchmark_entry_path_v1_quantile_filter.py`
- `tests/test_entry_path_v1_quantile_model.py`
- `tests/test_entry_path_v1_quantile_task.py`
- `tests/test_entry_path_v1_quantile_training.py`
- `tests/test_entry_path_v1_quantile_reports.py`
- `tests/test_entry_path_v1_quantile_filter.py`
- `ML/checkpoints/transformer_entry_path_v1_quantile_best.pt`
- `ML/checkpoints/transformer_entry_path_v1_quantile_result.json`
- `ML/reports/entry_path_v1_quantile_validation_predictions.csv`
- `ML/reports/entry_path_v1_quantile_test_predictions.csv`
- `ML/reports/evaluate_test_entry_path_v1_quantile.md`
- `ML/reports/entry_path_v1_quantile_filter_report.md`
- `ML/reports/entry_path_v1_quantile_filter_selected_rule.json`
- `ML/reports/entry_path_v1_quantile_filter_validation_summary.csv`
- `ML/reports/entry_path_v1_quantile_filter_test_summary.csv`

## Verification

```bash
./.venv/bin/python -m pytest tests/test_entry_path_v1_quantile_model.py tests/test_entry_path_v1_quantile_task.py tests/test_entry_path_v1_quantile_training.py tests/test_entry_path_v1_quantile_reports.py tests/test_entry_path_v1_quantile_filter.py -q
# 17 passed

./.venv/bin/python -m ML.train --model transformer --task entry_path_v1_quantile --epochs 5 --seed 42 --clear_cache

./.venv/bin/python -m ML.export_entry_path_v1_quantile_predictions --checkpoint ML/checkpoints/transformer_entry_path_v1_quantile_best.pt

./.venv/bin/python -m ML.evaluate_test --task entry_path_v1_quantile --checkpoint ML/checkpoints/transformer_entry_path_v1_quantile_best.pt

./.venv/bin/python -m ML.benchmark_entry_path_v1_quantile_filter --validation-csv ML/reports/entry_path_v1_quantile_validation_predictions.csv --test-csv ML/reports/entry_path_v1_quantile_test_predictions.csv --baseline_rule ML/reports/entry_path_trade_filter_selected_rule.json --output_dir ML/reports
```

## Results

### Model (`entry_path_v1_quantile`)

- Validation (`transformer_entry_path_v1_quantile_result.json`):
  - `best_val_score = -0.1915`
  - `ret_pearson_r = 0.1981`
  - `interval_coverage = 0.8013`
  - `median_interval_width = 7.1442`
- Test (`evaluate_test_entry_path_v1_quantile.md`):
  - `active_rows = 480`
  - `ret_pearson_r = 0.1455`
  - `interval_coverage = 0.7562`
  - `median_interval_width = 7.0826`
  - `crossed_quantile_rows = 0`

### Quantile filter over frozen base `A @ 7.5%`

- Winner on validation: `lb_gt_m`
  - `trades = 25`
  - `PF = 11.0465`
- Frozen test check:
  - `trades = 24`
  - `PF = inf`
- Sequential check (`hold_bars = 24`):
  - `trades = 11`
  - `PF = inf`
  - `win_rate = 100%`

### Success gate

- `winner != baseline`: pass
- `winner trades >= 25`: pass
- `test PF > 4.2936`: pass
- sequential check не хуже старой базы: pass

## Conclusions

Гибридный `entry_path_v1_quantile` в текущем прогоне проходит заданный success gate и даёт рабочий confidence-layer поверх базы `A @ 7.5%`.  
Этап можно считать завершённым как технически и исследовательски подтверждённый baseline этого под-трека.

## Limitations / Open Questions

- Проверка выполнена как один фиксированный run с заданным seed; устойчивость на дополнительных seeds ещё не проверялась.
- По `path_6_class` класс `+1` остаётся слабым в предыдущих этапах; в этом этапе фокус был на `ret_24` и quantile-layer.
- Решение пока не прогонялось через MT4 execution parity для нового quantile-layer.

## Next Step

1. Слить ветку `entry-path-v1-quantile` в `main`.
2. Отдельным этапом проверить устойчивость на нескольких seeds и годовых срезах.
3. После этого решать, переносить ли quantile confidence-layer в контур MT4.

## Related Materials

- `docs/reports/2026-04-09-entry-path-trade-filter.md`
- `ML/reports/entry_path_v1_quantile_filter_selected_rule.json`
- `ML/reports/evaluate_test_entry_path_v1_quantile.md`
