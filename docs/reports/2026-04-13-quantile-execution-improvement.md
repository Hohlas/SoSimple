# Quantile Execution Improvement

> **Date**: 2026-04-13
> **Status**: Blocked — unmatched quantile universe
> **Goal**: Проверить простые варианты выхода вокруг frozen `entry_path_v1_quantile`, не меняя сам сигнал
> **Related plan/spec**: [plan](../superpowers/plans/2026-04-13-quantile-execution-improvement.md), [spec](../superpowers/specs/2026-04-13-quantile-execution-improvement-design.md)
> **Related commit**: 53a29c1

## Context

`entry_path_v1_quantile` уже принят как production-ready parallel mode. После закрытия `fav_3_vs_12` как overlay и standalone следующий разумный вопрос был: можно ли улучшить не сам сигнал, а исполнение сделки вокруг него.

Первый проверяемый слой — выход. Сам `quantile` rule должен оставаться frozen.

## What Was Done

Добавлен отдельный benchmark execution-вариантов:

- `baseline_24`: текущий 24H выход через `true_ret_24_dir_atr`;
- `timeout_12`: более ранний 12H выход через `true_ret_12_dir_atr`;
- расчёт `trades`, `PF`, win_rate, mean PnL в ATR;
- выбор winner только на validation;
- CLI с записью `validation_grid.csv`, `test_grid.csv`, `selected_variant.json`, `run_metadata.json`.

Во время проверки найден критический риск плана: простой фильтр `signal != 0` не равен frozen `quantile`-выборке. Поэтому benchmark был усилен: перед расчётом он применяет frozen production rule и дополнительно проверяет, что test universe совпадает с `entry_path_v1_quantile_selected_rule.json`.

## Changed Files

- `ML/benchmark_quantile_execution_improvement.py`
- `tests/test_benchmark_quantile_execution_improvement.py`

## Verification

Тесты нового benchmark:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_execution_improvement.py -q
```

Результат:

```text
7 passed
```

Пробный запуск на доступных локальных `seed_007` prediction-файлах:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_quantile_execution_improvement \
  --validation-predictions /home/hohla/git/SoSimple/ML/reports/entry_path_v1_quantile_robustness/seed_007/entry_path_v1_quantile_validation_predictions.csv \
  --test-predictions /home/hohla/git/SoSimple/ML/reports/entry_path_v1_quantile_robustness/seed_007/entry_path_v1_quantile_test_predictions.csv \
  --output-dir ML/reports/quantile_execution_improvement
```

Результат:

```text
exit code 2
```

Это ожидаемое поведение защиты.

## Results

Честный execution verdict пока не получен.

Причина:

| Source | Validation selected | Test selected |
|---|---:|---:|
| Frozen production rule expected | 32 | 48 |
| Available local root CSV | 17 | 20 |
| Available local `seed_007` CSV | 20 | 33 |

Доступные файлы не воспроизводят frozen production universe `32/48`. Значит расчёт uplift на них был бы сравнением другой выборки, а не текущего production `quantile`.

## Conclusions

Текущий статус этапа:

```text
blocked_by_unmatched_universe
```

Это не провал идеи `timeout_12` и не подтверждение uplift. Это защита от ложного вывода.

Правильное решение: не принимать `execution_uplift_candidate`, пока не восстановлен prediction universe, который точно воспроизводит frozen `validation N=32` и `test N=48`.

## Limitations / Open Questions

- В текущем worktree нет полного набора артефактов, который воспроизводит frozen `32/48`.
- Локальные `seed_007` файлы есть в основном дереве, но дают только `20/33` при применении production rule.
- Пробные числа по `timeout_12` на `20/33` не являются каноническим результатом и не должны использоваться для product decision.

## Next Step

Сначала восстановить или сгенерировать канонический frozen quantile prediction universe:

- validation должен давать `N=32`;
- test должен давать `N=48`;
- расчёт должен совпадать с `ML/reports/entry_path_v1_quantile_selected_rule.json`.

Только после этого повторить execution benchmark и уже тогда решать:

- `no_execution_uplift`;
- или `execution_uplift_candidate`.

## Related Materials

- [Quantile status decision](2026-04-12-quantile-status-decision.md)
- [Quantile forward validation](2026-04-13-quantile-forward-validation.md)
- [Quantile execution improvement design](../superpowers/specs/2026-04-13-quantile-execution-improvement-design.md)
- `ML/reports/entry_path_v1_quantile_selected_rule.json`
