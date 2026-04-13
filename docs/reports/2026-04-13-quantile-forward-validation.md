# Quantile Forward Validation

> **Date**: 2026-04-13
> **Status**: Completed — watch / no forward data
> **Goal**: Проверить устойчивость frozen `entry_path_v1_quantile` на новых данных без перенастройки
> **Related plan/spec**: [plan](../superpowers/plans/2026-04-13-quantile-forward-validation.md), [spec](../superpowers/specs/2026-04-13-quantile-forward-validation-design.md)
> **Related commit**: pending

## Context

Текущий production-режим `entry_path_v1_quantile` уже был принят по frozen test:

- rule: `lb_gt_m_q35`
- test `N=48`
- test `PF=8.178675196069868`

Цель этого этапа была другой: не повторить старый test, а проверить тот же frozen rule на новом временном куске после production decision.

## What Was Done

Добавлен отдельный benchmark для forward validation:

- считает `trades`, `PF`, win_rate и mean PnL в ATR;
- строит квартальные временные срезы;
- выдаёт operational verdict `confirmed / watch / revisit`;
- пишет `summary.json`, `time_slices.csv`, `run_metadata.json`;
- не меняет quantile rule и не ищет новый winner.

Также проверены доступные prediction-источники в репозитории. Найдены только historical validation/test prediction-файлы, но не найден отдельный strictly newer forward CSV.

## Changed Files

- `ML/benchmark_quantile_forward_validation.py`
- `tests/test_benchmark_quantile_forward_validation.py`
- `ML/reports/quantile_forward_validation/summary.json`
- `ML/reports/quantile_forward_validation/time_slices.csv`
- `ML/reports/quantile_forward_validation/run_metadata.json`

## Verification

Запущена проверка нового benchmark:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_forward_validation.py -q
```

Результат:

```text
16 passed
```

## Results

Operational verdict:

```text
watch
```

Reason:

```text
no_forward_data
```

Forward metrics:

| Metric | Value |
|---|---:|
| trades | 0 |
| PF | n/a |
| win_rate | n/a |
| negative_slices | 0 |

Временные срезы пустые, потому что новый forward prediction CSV отсутствует.

## Conclusions

Нельзя честно подтвердить или отклонить `quantile` на новых данных в текущем состоянии репозитория.

Практический статус: `watch`, не потому что качество `quantile` ухудшилось, а потому что новых данных для проверки пока нет.

Старый frozen test нельзя использовать как forward validation: это была бы повторная проверка на уже принятом окне, а не новая проверка устойчивости.

## Limitations / Open Questions

- Нет нового prediction CSV после production decision.
- Raw `MT/MQL4/Files/Nero.csv` в рабочем дереве отсутствует, поэтому в этом этапе нельзя сгенерировать свежий forward-набор из сырья.
- Для настоящего `confirmed / revisit` нужен новый строго более поздний prediction-файл с колонками `time`, `signal`, `true_ret_24_dir_atr`.

## Next Step

Собрать новый forward prediction CSV тем же frozen quantile pipeline, затем запустить:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_quantile_forward_validation \
  --forward-predictions <forward_predictions_csv> \
  --output-dir ML/reports/quantile_forward_validation \
  --historical-pf 8.178675196069868
```

После этого verdict можно заменить на фактический `confirmed`, `watch` или `revisit`.

## Related Materials

- [Quantile status decision report](2026-04-12-quantile-status-decision.md)
- [Forward validation design](../superpowers/specs/2026-04-13-quantile-forward-validation-design.md)
- `ML/reports/entry_path_v1_quantile_selected_rule.json`
