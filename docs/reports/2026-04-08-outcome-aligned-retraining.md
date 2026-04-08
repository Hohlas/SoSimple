# Outcome-Aligned Retraining: validation-first verdict

> **Date**: 2026-04-08
> **Status**: Completed
> **Goal**: Построить outcome-aligned target families, сравнить их на validation по единым правилам отбора и выходить на test только при наличии честного winner-а
> **Related plan/spec**: `docs/superpowers/plans/2026-04-07-outcome-aligned-retraining.md`
> **Related commit**: pending

## Context

Старый `regression_updn` предсказывает directional excursions, но отчёты `2026-04-04-signal-path-atlas-readout.md`, `2026-04-04-archetype-filter-bridge.md` и `2026-04-04-signal-quality-filter.md` показали более важный сдвиг: edge находится не в экстремуме `up_12/dn_12` как таковом, а в отборе меньшинства сигналов с положительным drift и низким adverse excursion.

Из этого следовала новая исследовательская ветка:

1. построить row-level outcome labels, ближе к реальному торговому исходу;
2. добавить эти задачи в training/evaluation stack;
3. сравнить три семейства таргетов только на validation;
4. на test идти только с одним frozen winner-ом.

## What Was Done

1. Добавлены новые row-level outcome targets в preprocessing:
   - `trade_outcome_h12`
   - `trade_pnl_h12_atr`
   - `archetype_target`
2. В `ML`-стек добавлены три новые задачи:
   - `trade_outcome_cls`
   - `trade_pnl_reg`
   - `signal_archetype_cls`
3. Собран validation-first benchmark `ML/benchmark_outcome_targets.py`, который:
   - оценивает все три семейства на одних и тех же `top_pct`-срезах;
   - применяет общий `trade floor` и yearly stability filter;
   - создаёт frozen winner только если хотя бы одна семья проходит эти фильтры.
4. Во время первого запуска benchmark выяснилось, что outcome-задачи ошибочно обучались на полном universe, хотя их торговой смысл существует только на `signal != 0` строках.
5. После отладки outcome-task loaders переведены на signal-only профиль с отдельным кэшем `*_signal_rows.npy`, и все три семьи переобучены заново уже на правильной торговой популяции.
6. Benchmark доработан так, чтобы:
   - не падать, если одна семья не проходит фильтры;
   - корректно фиксировать сценарий, когда winner-а нет совсем.

## Changed Files

- `processing/label_signals.py`
- `processing/label_main.py`
- `ML/data_loader.py`
- `ML/train.py`
- `ML/evaluate_test.py`
- `ML/utils.py`
- `ML/benchmark_outcome_targets.py`
- `tests/test_trade_target_labels.py`
- `tests/test_outcome_tasks.py`
- `tests/test_benchmark_outcome_targets.py`

## Verification

```bash
./.venv/bin/python -m pytest tests/test_label_updn.py tests/test_trade_target_labels.py tests/test_outcome_tasks.py tests/test_benchmark_outcome_targets.py -q
./.venv/bin/python -m py_compile ML/data_loader.py ML/benchmark_outcome_targets.py ML/train.py ML/evaluate_test.py

PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib ./.venv/bin/python -m ML.train --model transformer --task trade_outcome_cls --epochs 30 --seed 42
PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib ./.venv/bin/python -m ML.train --model transformer --task trade_pnl_reg --epochs 30 --seed 42
PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib ./.venv/bin/python -m ML.train --model transformer --task signal_archetype_cls --epochs 30 --seed 42

PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib ./.venv/bin/python -m ML.benchmark_outcome_targets --model transformer
```

## Results

### Signal-only training population

- Train signal rows: `2208`
- Validation signal rows: `473`

### Model-level validation metrics after signal-only retraining

- `trade_outcome_cls`: best val `AUC=0.6534`
- `trade_pnl_reg`: best val `pearson_r=0.1099`
- `signal_archetype_cls`: best val `AUC=0.6260`

### Validation benchmark under shared selection rules

Rules were the same for all families:

- `min_trades = 80`
- `min_stability_ratio = 0.75`
- `min_year_trades = 10`
- score rule: keep only signal rows with `score >= threshold`, threshold chosen on validation only

Best rejected slice for each family:

| Family | top_pct | threshold | trades | PF | stability | mean_pnl_atr | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| `trade_outcome_cls` | 0.05 | 0.5186 | 24 | 0.1983 | 0.00 | -3.9206 | `no_slice_passed_filters` |
| `trade_pnl_reg` | 0.05 | -2.7215 | 24 | 0.1105 | 0.00 | -3.1042 | `no_slice_passed_filters` |
| `signal_archetype_cls` | 0.10 | 0.4800 | 48 | 0.1369 | 0.00 | -4.2492 | `no_slice_passed_filters` |

### Final verdict

- Ни одно семейство не прошло общий `trade floor + yearly stability` filter.
- `ML/reports/frozen_outcome_target.json` не создан.
- Финальная проверка на `test` не запускалась, потому что validation-first protocol не дал winner-а.

## Conclusions

1. Исправление objective mismatch было необходимо: outcome-задачи действительно надо учить на `signal != 0` строках, а не на полном universe.
2. Даже после этого исправления текущие outcome-aligned labels не дали переносимого winner-а на validation.
3. `signal_archetype_cls` не принёс дополнительного преимущества поверх `trade_outcome_cls`: обе семьи показали схожую слабость в ranking-срезах.
4. `trade_pnl_reg` оказался самым слабым семейством после перехода на signal-only population.
5. При текущем validation-first протоколе правильный практический вывод не “выбрать лучшего из плохих”, а “winner отсутствует, test не трогать”.

## Limitations / Open Questions

1. Текущие labels всё ещё завязаны на `close-to-close` исход через 12 баров и не повторяют реальные MT4 execution rules (`next-bar entry`, `single open position`, `HoldOverTime`, `PosBlock`, exit logic).
2. `trade_outcome_h12` и `archetype_target` почти схлопываются в одну и ту же бинарную задачу на текущих split-файлах.
3. Сильная отрицательность `trade_pnl_h12_atr` на validation signal rows говорит, что текущая label-схема по сути описывает “жёстко плохой” baseline universe, а не рабочий selection problem.
4. Без winner-а нельзя делать честный вывод о test performance. Любой test-run сейчас был бы нарушением validation-first discipline.

## Next Step

1. Не запускать `test` для outcome-aligned семей, пока на validation не появится хотя бы один target family, прошедший shared filters.
2. Следующую итерацию строить ближе к реальному торговому исходу MT4:
   - entry на следующем баре;
   - только одна открытая позиция;
   - явная exit policy;
   - при необходимости timeout/position-blocking как часть label definition.
3. Проверить, не стоит ли заменить текущий `close-at-12h` outcome на execution-aware target, который ближе к реальному decision loop, а не к постфактум закрытию по `close[t+12]`.

## Related Materials

- `docs/superpowers/plans/2026-04-07-outcome-aligned-retraining.md`
- `docs/reports/2026-04-04-signal-path-atlas-readout.md`
- `docs/reports/2026-04-04-archetype-filter-bridge.md`
- `docs/reports/2026-04-04-signal-quality-filter.md`
- `ML/reports/outcome_target_validation_benchmark.md`
- `ML/reports/outcome_target_validation_benchmark.csv`
