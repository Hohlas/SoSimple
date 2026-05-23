# Multi-Horizon Take/Skip Feature Track Handoff

> **Date**: 2026-04-17
> **Status**: Completed
> **Goal**: Подготовить новый research track `take_skip_trailing_stop_v2` к полному matrix run на сервере и проверить локально, что весь контур train → export → benchmark работает end-to-end.
> **Related plan/spec**: `docs/superpowers/specs/2026-04-17-multi-horizon-take-skip-feature-track-design.md`, `docs/superpowers/plans/2026-04-17-multi-horizon-take-skip-feature-track.md`
> **Related commit**: pending

## Context

Предыдущий этап `take_skip_trailing_stop_v1` завершился жёстким `reject`: ни один candidate не дал даже `PF > 1` на validation. Следующая гипотеза была не в новом selection layer, а в более сильном представлении тех же данных: полные 100 фракталов, сводки по нескольким длинам истории и multi-horizon binary target.

Задача этого этапа была инженерной: собрать новый контур `take_skip_trailing_stop_v2`, проверить его тестами и локальным smoke-run, но не запускать полный matrix локально.

## What Was Done

- `processing/label_signals.py` расширен до multi-horizon trailing-stop labels:
  - горизонты `12 / 24 / 48`
  - trailing-stop `X = 2 / 4 / 8`
- Добавлен `ML/multi_scale_fractal_features.py`:
  - сводки по окнам `5 / 10 / 20 / 50 / 100`
  - mean, std, last-minus-mean, slope proxy, range
- Добавлен task `ML/take_skip_trailing_stop_v2_task.py`:
  - 9 бинарных targets `take_H_xX`
  - positive class: `trail_pnl >= 0.5 ATR`
- `ML/data_loader.py` расширен:
  - строит full 100-fractal tensor
  - считает multi-scale summaries
  - добавляет row-wise numeric features
  - собирает вход `seq + engineered channels`
- `ML/train.py`, `ML/evaluate_test.py`, `API/generate_signals.py` протянуты под `take_skip_trailing_stop_v2`
- Добавлен benchmark `ML/benchmark_take_skip_trailing_stop_v2.py`
- Добавлен runner `ML/run_take_skip_trailing_stop_v2_matrix.py`
- После smoke-run исправлены два operational defect-а:
  - для обычного `Transformer` убран лишний `seq_len` kwarg в v2-ветке обучения;
  - для v2 отключена попытка строить confusion matrix, которой у multi-label BCE-задачи нет

## Changed Files

- `processing/label_signals.py`
- `ML/multi_scale_fractal_features.py`
- `ML/take_skip_trailing_stop_v2_task.py`
- `ML/benchmark_take_skip_trailing_stop_v2.py`
- `ML/run_take_skip_trailing_stop_v2_matrix.py`
- `ML/data_loader.py`
- `ML/train.py`
- `ML/evaluate_test.py`
- `API/generate_signals.py`
- `tests/test_trailing_stop_target_labels.py`
- `tests/test_multi_scale_fractal_features.py`
- `tests/test_take_skip_trailing_stop_v2_task.py`
- `tests/test_benchmark_take_skip_trailing_stop_v2.py`
- `tests/test_run_take_skip_trailing_stop_v2_matrix.py`
- `MODULE_INDEX.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`

## Verification

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_trailing_stop_target_labels.py -q
# 8 passed

/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_multi_scale_fractal_features.py -q
# 4 passed

/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_trailing_stop_v2_task.py -q
# 11 passed

/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_take_skip_trailing_stop_v2.py -q
# 5 passed

/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_multi_scale_fractal_features.py \
  tests/test_take_skip_trailing_stop_v2_task.py \
  tests/test_benchmark_take_skip_trailing_stop_v2.py \
  tests/test_run_take_skip_trailing_stop_v2_matrix.py -q
# 23 passed

MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_take_skip_trailing_stop_v2_matrix \
  --output-dir ML/reports/take_skip_trailing_stop_v2_matrix_smoke \
  --seq-lens 20 \
  --epochs 1 \
  --patience 1 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6
# completed locally
```

## Results

### Smoke-Run Verdict

Smoke-run `transformer_seq20` завершился успешно и прошёл весь контур:

- train
- evaluate_test
- validation/test prediction export
- benchmark

Сводка smoke-run:

- input shape: `X=(43764, 100, 539)`
- best validation BCE: `0.01548`
- best epoch: `1`
- parameters: `103945`

Validation winner:

- target: `take_48_x4`
- candidate: `top_k_probability`
- threshold: `0.05`
- trades: `24`
- trades_per_year: `6.0`
- `PF=6.39`
- `negative_year_slices=0`

Frozen test check:

- trades: `24`
- trades_per_year: `4.8`
- `PF=34.77`
- `negative_year_slices=0`

Практический смысл smoke-run: новый контур не развалился технически и способен выдавать не только `reject`, в отличие от предыдущего v1 smoke-path.

### Important Operational Note

Локальный smoke потребовал, чтобы split CSV уже содержали новые continuous columns:

- `trail_12_pnl_atr_x2/x4/x8`
- `trail_24_pnl_atr_x2/x4/x8`
- `trail_48_pnl_atr_x2/x4/x8`

Если на сервере в `DATA/Nero_{train,validation,test}_labeled.csv` этих колонок нет, matrix run упадёт на загрузке данных. Перед удалённым запуском `DATA/` должен быть синхронизирован в уже пересчитанном виде.

## Conclusions

- Новый feature-track реализован и локально подтверждён end-to-end.
- Главный инженерный риск прошлых этапов был не в кодовом контуре: train/evaluate/export/benchmark теперь собраны стабильно и воспроизводимо.
- Первый smoke-run дал достаточно сильный сигнал, чтобы оправдать полный matrix run на сервере.
- При этом делать вывод о жизнеспособности трека по smoke-run нельзя: он слишком короткий, только для `seq20`, и нужен лишь как техническая инициализация.

## Limitations / Open Questions

- Полный matrix `seq_len = 20 / 50 / 100` локально не запускался.
- Smoke-run использовал один epoch и не является исследовательским verdict-ом.
- `validation_grid.csv` и prediction CSV по-прежнему gitignored; для итогового этапа их нужно переносить или коммитить осознанно.

## Next Step

Запустить полный bounded matrix на сервере:

```bash
MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_take_skip_trailing_stop_v2_matrix \
  --output-dir ML/reports/take_skip_trailing_stop_v2_matrix \
  --seq-lens 20 50 100 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6
```

После remote run вернуть в репозиторий как минимум:

- `manifest.json`
- `summary.json`
- `benchmark/final_verdict.json`
- `benchmark/validation_grid.csv`
- prediction CSV, если потребуется повторный benchmark без переобучения

## Related Materials

- `ML/reports/take_skip_trailing_stop_v2_matrix_smoke/manifest.json`
- `ML/reports/take_skip_trailing_stop_v2_matrix_smoke/transformer_seq20/summary.json`
- `ML/reports/take_skip_trailing_stop_v2_matrix_smoke/transformer_seq20/benchmark/final_verdict.json`
- `docs/reports/2026-04-17-take-skip-trailing-stop-matrix.md`
- `docs/superpowers/specs/2026-04-17-multi-horizon-take-skip-feature-track-design.md`
- `docs/superpowers/plans/2026-04-17-multi-horizon-take-skip-feature-track.md`
