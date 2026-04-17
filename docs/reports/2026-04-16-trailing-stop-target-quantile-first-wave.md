# Trailing Stop Target Quantile First Wave

> **Date**: 2026-04-17
> **Status**: Completed
> **Goal**: Проверить, даёт ли quantile-постановка для `trail_48_pnl_atr_x3` рабочую validation-zone лучше обычной регрессии
> **Related spec/plan**: `docs/superpowers/specs/2026-04-16-trailing-stop-target-quantile-design.md`, `docs/superpowers/plans/2026-04-16-trailing-stop-target-quantile.md`

## Context

После первой волны `trailing_stop_target_v1` лучший обычный regression candidate был `transformer_seq20 + trail_48_pnl_atr_x3`, но он остановился на validation `PF=0.4206`. Следующий bounded шаг проверил не новый target и не длинную матрицу, а другую постановку обучения для того же исполнимого target-а: модель предсказывает три оценки результата сделки (`q10/q50/q90`) для `trail_48_pnl_atr_x3`.

Смысл проверки: если нижняя оценка результата (`q10`) всё ещё положительная или достаточно высокая, такой вход должен быть более устойчивым, чем отбор по одной средней регрессионной оценке.

## What Was Done

- Добавлен task `trailing_stop_target_quantile_v1` для `trail_48_pnl_atr_x3`.
- Добавлена модель `TrailingStopTargetQuantileTransformer` с тремя независимыми головами `q10/q50/q90`.
- Train/evaluate/export stack протянут через `ML/train.py`, `ML/evaluate_test.py`, `API/generate_signals.py`, `ML/data_loader.py`.
- Добавлен validation-first benchmark по candidate families:
  - `q10_gt_zero`;
  - `q10_gt_m`;
  - `q10_q50_positive`;
  - `spread_score = q10 / max(q90 - q10, eps)`.
- Benchmark считает не только PF, но и `trades_per_year`, `negative_year_slices`, `profit_concentration_top_10`, `ulcer_index_atr`, `max_drawdown_atr`.
- При review закрыты silent-failure риски:
  - checkpoint копируется как обязательный артефакт, stale checkpoint не может быть использован;
  - даты prediction export проверяются fail-fast;
  - `trades_per_year` нормируется на полный validation/test split, включая строки без сделки.

## Verification

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_trailing_stop_target_quantile_task.py \
  tests/test_trailing_stop_target_quantile_model.py \
  tests/test_benchmark_trailing_stop_target_quantile.py \
  tests/test_run_trailing_stop_target_quantile.py -q
# 23 passed
```

Focused Task 3 regression suite after benchmark hardening:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_benchmark_trailing_stop_target_quantile.py \
  tests/test_run_trailing_stop_target_quantile.py -q
# 12 passed
```

## Results

### Train / Validation Summary

| Config | Best val `q50_pearson_r` | Best epoch | Test `q50_pearson_r` | Verdict |
|---|---:|---:|---:|---|
| `transformer_seq20_x3_quantile` | `0.0389` | `2` | `0.0541` | reject |

Training details:

- `q50_mae`: `0.1032`
- interval coverage: `0.9496`
- median interval width: `0.0065`
- runtime: `264.2s` on CPU

### Validation Benchmark

| Candidate | Threshold | Trades | Trades/year | Validation PF | Negative year slices | Profit concentration top 10 | Max drawdown ATR |
|---|---:|---:|---:|---:|---:|---:|---:|
| `q10_gt_m` | `-0.002657` | `95` | `23.75` | `0.1750` | `4` | `0.1692` | `138.99` |
| `q10_gt_m` | `-0.002654` | `48` | `12.00` | `0.1426` | `3` | `0.3341` | `74.97` |
| `q10_gt_m` | `-0.002655` | `71` | `17.75` | `0.1233` | `4` | `0.2592` | `109.85` |
| `spread_score` | `-0.409465` | `95` | `23.75` | `0.1110` | `4` | `0.2057` | `155.29` |
| `spread_score` | `-0.408936` | `48` | `12.00` | `0.0901` | `4` | `0.4800` | `84.35` |
| `q10_gt_m` | `-0.002652` | `24` | `6.00` | `0.0849` | `4` | `0.6939` | `40.87` |
| `q10_gt_zero` | `0.000000` | `0` | `0.00` | `0.0000` | `0` | `0.0000` | `0.00` |
| `q10_q50_positive` | `0.000000` | `0` | `0.00` | `0.0000` | `0` | `0.0000` | `0.00` |

Ключевой факт:

- ни один candidate не достиг `PF >= 1.0` на validation;
- `q10_gt_zero` и `q10_q50_positive` не дали ни одной сделки, потому что нижняя quantile-оценка почти всегда отрицательная;
- лучший candidate оказался вынужден брать отрицательный `q10` threshold, то есть модель не формирует положительную нижнюю оценку результата.

## Comparison With Plain Regression

Обычная regression-постановка на том же лучшем target-е `seq20 + trail_48_pnl_atr_x3` была слабой, но всё же лучше по trading benchmark:

| Approach | Best validation PF | Best candidate trades | Verdict |
|---|---:|---:|---|
| `trailing_stop_target_v1`, `seq20 + x3` | `0.4206` | `24` | reject |
| `trailing_stop_target_quantile_v1`, `seq20 + x3` | `0.1750` | `95` | reject |

Quantile-постановка не улучшила trading selection layer. Она дала более слабый best-PF и не приблизилась к мягкому gate `PF > 1`.

## Conclusion

Первый quantile wave для trailing-stop target-а даёт отрицательный verdict.

Главный вывод: проблема не в том, что обычная regression-модель плохо выражает неопределённость. Даже когда модель учится предсказывать нижнюю/среднюю/верхнюю оценку результата сделки, validation benchmark не находит рабочую зону отбора.

Практический вывод:

- `trailing_stop_target_quantile_v1` не стоит расширять в длинную матрицу `seq_len=50/100` без новой идеи;
- текущий `trail_48_pnl_atr_x3` как непрерывный target, даже в quantile-форме, не вытягивает вход;
- следующий содержательный шаг лучше делать в другой целевой постановке: бинарное `брать/не брать` или ranking внутри периода, а не ещё один rerun той же regression/quantile family.

## Related Materials

- `ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/summary.json`
- `ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/benchmark/validation_grid.csv`
- `ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/benchmark/final_verdict.json`
- `ML/trailing_stop_target_quantile_task.py`
- `ML/benchmark_trailing_stop_target_quantile.py`
- `ML/run_trailing_stop_target_quantile.py`
