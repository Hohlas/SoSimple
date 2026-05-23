# Take/Skip Trailing Stop Matrix Verdict

> **Date**: 2026-04-17 13:35
> **Status**: Completed
> **Goal**: Проверить, даст ли новая бинарная постановка `take/skip` торгового кандидата на готовых данных без смены базовой архитектуры.
> **Related plan/spec**: `docs/superpowers/specs/2026-04-17-take-skip-trailing-stop-design.md`, `docs/superpowers/plans/2026-04-17-take-skip-trailing-stop.md`
> **Related commit**: 79954ef

## Context

Предыдущие треки `trailing_stop_target_v1` и `trailing_stop_target_quantile_v1` не нашли кандидата даже с мягким порогом `PF > 1` на validation. Следующий шаг был направлен на смену целевой постановки: вместо предсказания непрерывного результата сделки модель должна была отвечать, стоит ли вообще брать вход при trailing-stop логике.

Цель этапа была двойной:

- проверить новую постановку `take_skip_trailing_stop_v1`;
- отделить слабость selection layer от слабости самого обучающего сигнала.

## What Was Done

- Добавлен новый task `take_skip_trailing_stop_v1` с таргетом:
  - `take = 1`, если `trail_48_pnl_atr_xN >= 0.5`
  - `take = 0` иначе
- Расширена сетка trailing-stop параметров:
  - `X = 2, 3, 4, 6, 8`
- Протянут новый task через train/evaluate/export stack.
- Реализован benchmark `ML/benchmark_take_skip_trailing_stop.py`:
  - candidate families: `prob_ge_threshold`, `top_k_probability`
  - метрики: `PF`, `trades_per_year`, `negative_year_slices`, `profit_concentration_top_10`, `ulcer_index_atr`, `max_drawdown_atr`
  - frozen selection: winner выбирается только на validation
- Реализован matrix runner `ML/run_take_skip_trailing_stop_matrix.py` для `seq_len = 20 / 50 / 100`.
- Выполнен локальный smoke-run и полный remote matrix run.
- После remote run локально подняты `validation_grid.csv` для полного разбора candidate set.

## Changed Files

- `ML/take_skip_trailing_stop_task.py`
- `ML/benchmark_take_skip_trailing_stop.py`
- `ML/run_take_skip_trailing_stop_matrix.py`
- `ML/data_loader.py`
- `ML/train.py`
- `ML/evaluate_test.py`
- `API/generate_signals.py`
- `processing/label_signals.py`
- `tests/test_take_skip_trailing_stop_task.py`
- `tests/test_benchmark_take_skip_trailing_stop.py`
- `tests/test_run_take_skip_trailing_stop_matrix.py`
- `docs/reports/2026-04-17-take-skip-trailing-stop-matrix.md`

## Verification

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_take_skip_trailing_stop_task.py \
  tests/test_benchmark_take_skip_trailing_stop.py \
  tests/test_run_take_skip_trailing_stop_matrix.py -q
# 20 passed

/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_trailing_stop_target_labels.py \
  tests/test_trailing_stop_target_task.py \
  tests/test_take_skip_trailing_stop_task.py \
  tests/test_benchmark_take_skip_trailing_stop.py \
  tests/test_run_take_skip_trailing_stop_matrix.py -q
# 37 passed

MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_take_skip_trailing_stop_matrix \
  --output-dir ML/reports/take_skip_trailing_stop_matrix \
  --seq-lens 20 50 100 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6
# completed on remote server
```

## Results

### Model Quality

Validation / test BCE:

| Config | Best epoch | Validation BCE | Test BCE |
|---|---:|---:|---:|
| `transformer_seq20` | 1 | 0.03841 | 0.0427 |
| `transformer_seq50` | 5 | 0.03834 | 0.0427 |
| `transformer_seq100` | 8 | 0.03788 | 0.0420 |

Class prevalence on validation:

- `take_48_x2`: `0.0037`
- `take_48_x3`: `0.0044`
- `take_48_x4`: `0.0052`
- `take_48_x6`: `0.0082`
- `take_48_x8`: `0.0092`

### Benchmark Verdict

Во всех трёх конфигурациях:

- `verdict = reject`
- `validation_winner = null`
- `test_result = null`

То есть ни один кандидат не прошёл gate:

- `PF >= 1.0`
- `trades_per_year >= 6`

### Candidate Set Diagnostics

По полным `validation_grid.csv`:

- семейство `prob_ge_threshold` полностью мёртвое:
  - `50/50` строк в каждом run дали `0` сделок
  - ни один абсолютный probability threshold `0.50..0.95` не отобрал trades
- весь benchmark фактически жил только на `top_k_probability`

Лучшие validation-кандидаты среди строк с `trades_per_year >= 6`:

| Config | Best candidate | PF | Trades | Trades/year |
|---|---|---:|---:|---:|
| `transformer_seq20` | `take_48_x2 + top_k_probability 0.05` | 0.2740 | 24 | 6.0 |
| `transformer_seq50` | `take_48_x2 + top_k_probability 0.05` | 0.2023 | 24 | 6.0 |
| `transformer_seq100` | `take_48_x8 + top_k_probability 0.10` | 0.1526 | 48 | 12.0 |

Лучшие validation-кандидаты без ограничения по частоте:

| Config | Best candidate | PF | Trades |
|---|---|---:|---:|
| `transformer_seq20` | `take_48_x2 + top_k_probability 0.05` | 0.2740 | 24 |
| `transformer_seq50` | `take_48_x2 + top_k_probability 0.05` | 0.2023 | 24 |
| `transformer_seq100` | `take_48_x8 + top_k_probability 0.01` | 0.2587 | 5 |

Across all runs:

- кандидатов с `PF > 1`: `0`
- кандидатов с `PF > 1` и `trades_per_year >= 6`: `0`

## Conclusions

- Смена постановки с regression/quantile на бинарный `take/skip` не решила проблему.
- Абсолютный probability threshold неработоспособен: модель выдаёт слишком слабый и сжатый скор.
- Относительный отбор `top-k` выбирает только "наименее плохие" сделки, но не создаёт торгового преимущества.
- На `seq20` и `seq50` наименее плохим был узкий trailing-stop `X=2`.
- На `seq100` немного лучше выглядел широкий trailing-stop `X=6/8`, но это всё равно глубокий reject.
- Практически это означает, что текущий Track A почти исчерпан не только на уровне selection layer, но и на уровне самого обучающего сигнала.

## Limitations / Open Questions

- `validation_grid.csv` не коммитились в git из-за `gitignore`, поэтому полный candidate-level разбор был сделан локально после ручного копирования CSV.
- Этап не проверял новую архитектуру признаков; использовалось текущее представление данных.
- Высокий дисбаланс positive-class (`0.37% .. 0.92%`) может сам по себе быть существенным ограничением для этой постановки.

## Next Step

Перейти к новому обучающему треку, а не к ещё одному benchmark-only циклу:

- пересобрать входные признаки на всех 100 фракталах;
- добавить multi-scale summary по нескольким длинам истории;
- сохранить простую и робастную торговую логику;
- запускать уже новый train на обновлённом представлении данных.

## Related Materials

- `ML/reports/take_skip_trailing_stop_matrix/manifest.json`
- `ML/reports/take_skip_trailing_stop_matrix/transformer_seq20/summary.json`
- `ML/reports/take_skip_trailing_stop_matrix/transformer_seq50/summary.json`
- `ML/reports/take_skip_trailing_stop_matrix/transformer_seq100/summary.json`
- `docs/reports/2026-04-16-trailing-stop-target-first-wave.md`
- `docs/reports/2026-04-16-trailing-stop-target-quantile-first-wave.md`
