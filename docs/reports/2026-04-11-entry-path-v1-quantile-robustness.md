# Entry Path v1 Quantile: multi-seed robustness pass завершён

> **Date**: 2026-04-11 14:14
> **Status**: Completed
> **Goal**: Проверить, устойчив ли `entry_path_v1_quantile` как реальный апгрейд над frozen baseline `A @ 7.5%` на нескольких `seed`, годовых срезах и sequential-проверке
> **Related plan/spec**: `docs/superpowers/plans/2026-04-11-entry-path-v1-quantile-robustness.md`, `docs/superpowers/plans/2026-04-11-triple-barrier-mt4-matched-python-eval.md`
> **Related commit**: 11b7005

## Context

Этап `2026-04-10-entry-path-v1-quantile` показал сильный single-run результат для quantile-layer поверх frozen baseline `A @ 7.5%`, но support был слишком малым для практического решения.  
Следующий шаг уже не был поиском новых правил: нужно было проверить, держится ли один и тот же quantile winner на нескольких `seed`, и убрать технические препятствия для repeatable multi-run контура.

## What Was Done

- Реализован repeatable robustness-контур для `entry_path_v1_quantile`:
  - `ML.train` получил `--checkpoint-dir` и `--result-dir`;
  - `ML.evaluate_test` получил `--output-dir`;
  - артефакты теперь можно выпускать по seed-изолированным директориям без перезаписи основного run.
- Исправлен blocker в `ML/export_entry_path_v1_quantile_predictions.py`:
  - export больше не создаёт loaders и split-ы для незапрошенных наборов;
  - это сняло лишний rebuild и позволило честно добивать `validation/test` по отдельности.
- Добавлен robustness-анализатор:
  - `ML/entry_path_v1_quantile_robustness.py`
  - `ML/benchmark_entry_path_v1_quantile_robustness.py`
  - агрегируются per-seed итоги, yearly slices, rolling/sequential summary и итоговый verdict.
- Исправлена важная ошибка интерпретации robustness-метрик:
  - yearly/rolling summary теперь считаются по winner-selected сделкам, а не по всей active universe.
- Собран полный 5-seed pass для `seed = 7, 17, 42, 77, 123`.
- Параллельно подготовлен следующий secondary track:
  - `ML/triple_barrier_mt4_execution.py`
  - `ML/benchmark_triple_barrier_mt4_execution.py`
  Эти модули реализуют Python-режим, который должен повторять MT4-исполнение, но их реальные benchmark-артефакты в этом этапе ещё не выпускались.

## Changed Files

- `ML/train.py`
- `ML/evaluate_test.py`
- `ML/export_entry_path_v1_quantile_predictions.py`
- `ML/entry_path_v1_quantile_robustness.py`
- `ML/benchmark_entry_path_v1_quantile_robustness.py`
- `ML/triple_barrier_mt4_execution.py`
- `ML/benchmark_triple_barrier_mt4_execution.py`
- `tests/test_entry_path_v1_quantile_training.py`
- `tests/test_entry_path_v1_quantile_reports.py`
- `tests/test_entry_path_v1_quantile_robustness.py`
- `tests/test_triple_barrier_mt4_execution.py`
- `ML/checkpoints/entry_path_v1_quantile_robustness/`
- `ML/reports/entry_path_v1_quantile_robustness/`

## Verification

```bash
./.venv/bin/python -m pytest tests/test_entry_path_v1_quantile_model.py tests/test_entry_path_v1_quantile_task.py tests/test_entry_path_v1_quantile_training.py tests/test_entry_path_v1_quantile_reports.py tests/test_entry_path_v1_quantile_filter.py tests/test_entry_path_v1_quantile_robustness.py tests/test_triple_barrier_first_touch.py tests/test_triple_barrier_calibration.py tests/test_triple_barrier_training.py tests/test_signal_tracer_tb.py tests/test_triple_barrier_mt4_execution.py -q
# 39 passed

./.venv/bin/python -m ML.benchmark_entry_path_v1_quantile_filter --validation-csv ML/reports/entry_path_v1_quantile_robustness/seed_077/entry_path_v1_quantile_validation_predictions.csv --test-csv ML/reports/entry_path_v1_quantile_robustness/seed_077/entry_path_v1_quantile_test_predictions.csv --baseline-rule ML/reports/entry_path_trade_filter_selected_rule.json --output-dir ML/reports/entry_path_v1_quantile_robustness/seed_077

./.venv/bin/python -m ML.benchmark_entry_path_v1_quantile_filter --validation-csv ML/reports/entry_path_v1_quantile_robustness/seed_123/entry_path_v1_quantile_validation_predictions.csv --test-csv ML/reports/entry_path_v1_quantile_robustness/seed_123/entry_path_v1_quantile_test_predictions.csv --baseline-rule ML/reports/entry_path_trade_filter_selected_rule.json --output-dir ML/reports/entry_path_v1_quantile_robustness/seed_123

./.venv/bin/python -m ML.benchmark_entry_path_v1_quantile_robustness --root-dir ML/reports/entry_path_v1_quantile_robustness --seeds 7 17 42 77 123 --baseline-rule ML/reports/entry_path_trade_filter_selected_rule.json --output-dir ML/reports/entry_path_v1_quantile_robustness/aggregate_5seed
```

## Results

### Aggregate verdict

- `seed_count = 5`
- `same_rule_count = 5`
- `median_test_pf = inf`
- `median_sequential_pf = inf`
- `worst_seed_test_trades = 20`
- `negative_year_slices = 0`
- final verdict: `go_mt4`

### Per-seed frozen results

| Seed | Winner | Validation | Frozen Test | Sequential |
|---|---|---:|---:|---:|
| `007` | `lb_gt_m` | `24 trades`, `PF=11.71` | `20 trades`, `PF=inf` | `11 trades`, `PF=inf` |
| `017` | `lb_gt_m` | `25 trades`, `PF=45.53` | `26 trades`, `PF=inf` | `8 trades`, `PF=inf` |
| `042` | `lb_gt_m` | `25 trades`, `PF=11.05` | `24 trades`, `PF=inf` | `11 trades`, `PF=inf` |
| `077` | `lb_gt_m` | `24 trades`, `PF=11.75` | `20 trades`, `PF=inf` | `9 trades`, `PF=inf` |
| `123` | `lb_gt_m` | `25 trades`, `PF=11.05` | `26 trades`, `PF=25.17` | `12 trades`, `PF=44.77` |

### Robustness notes

- Во всех 5 seed validation winner совпал: `lb_gt_m`.
- Ни один eligible yearly slice не ушёл в отрицательный результат.
- Худший support на frozen test остался рабочим: `20` сделок.
- `seed_123` дал не бесконечный, а конечный `test PF=25.17`, что полезно как подтверждение того, что линия не держится только на “идеальном lucky run”.

## Conclusions

`entry_path_v1_quantile` прошёл тот robustness-pass, которого не хватало после single-run отчёта от `2026-04-10`.  
На текущем уровне доказательств это уже не preliminary low-N находка, а подтверждённый multi-seed upgrade над frozen baseline `A @ 7.5%`.

Практический вывод этапа жёсткий: следующий главный шаг теперь не новый поиск и не новые seed, а отдельный `MT4 parity-check` именно для quantile-layer winner `lb_gt_m`.

## Limitations / Open Questions

- MT4 parity-check для quantile-layer ещё не выполнен; подтверждение пока только в Python robustness-контуре.
- Число сделок всё ещё умеренное: линия выглядит сильной, но остаётся low-frequency режимом относительно старой базы.
- `triple_barrier_mt4_execution` реализован как secondary track, но его реальные `validation/test` benchmark-артефакты ещё не выпущены.

## Next Step

1. Выполнить `MT4 parity-check` для `entry_path_v1_quantile` с frozen winner `lb_gt_m`.
2. Зафиксировать, совпадает ли practical edge в MT4 с Python-robustness verdict.
3. После этого решить, становится ли quantile-layer новым основным execution mode.
4. Отдельным secondary stage прогнать `triple_barrier_mt4_execution` на `validation/test`, чтобы честно измерить силу TB в MT4-matched Python-режиме.

## Related Materials

- `docs/reports/2026-04-10-entry-path-v1-quantile.md`
- `docs/reports/2026-04-09-entry-path-trade-filter.md`
- `ML/reports/entry_path_v1_quantile_robustness/aggregate_5seed/summary.json`
- `ML/reports/entry_path_v1_quantile_robustness/aggregate_5seed/runs.csv`
