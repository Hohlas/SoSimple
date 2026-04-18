# Multi-Horizon Take/Skip Feature Track Verdict

> **Date**: 2026-04-18 01:10
> **Status**: Completed
> **Goal**: Проверить, даёт ли новый feature-track на 100 фракталах и multi-scale summaries живой `take/skip` candidate, который проходит мягкий trade gate и не разваливается по годам.
> **Related plan/spec**: `docs/superpowers/specs/2026-04-17-multi-horizon-take-skip-feature-track-design.md`, `docs/superpowers/plans/2026-04-17-multi-horizon-take-skip-feature-track.md`
> **Related commit**: pending

## Context

Предыдущая линия trailing-stop retraining дала три подряд отрицательных verdict-а:

- `trailing_stop_target_v1` — `reject`
- `trailing_stop_target_quantile_v1` — `reject`
- `take_skip_trailing_stop_v1` — `reject`

Главный вывод был такой: проблема уже не в selection layer, а в слабом представлении входа. Поэтому новый этап менял не только target, но и сам вход:

- все `100` фракталов;
- сводки по окнам `5 / 10 / 20 / 50 / 100`;
- multi-horizon binary target;
- сохранение простой модели `Transformer`.

## What Was Done

- `processing/label_signals.py` расширен до multi-horizon trailing-stop labels:
  - горизонты `12 / 24 / 48`
  - trailing-stop `X = 2 / 4 / 8`
- Добавлен `ML/multi_scale_fractal_features.py`:
  - mean, std, last-minus-mean, slope proxy, range
  - окна `5 / 10 / 20 / 50 / 100`
- Добавлен task `ML/take_skip_trailing_stop_v2_task.py`:
  - 9 бинарных targets
  - positive class: `trail_pnl >= 0.5 ATR`
- `ML/data_loader.py` расширен:
  - строит full 100-fractal tensor
  - добавляет multi-scale summaries
  - добавляет row-wise numeric features
- `ML/train.py`, `ML/evaluate_test.py`, `API/generate_signals.py` протянуты под `take_skip_trailing_stop_v2`
- Добавлены:
  - `ML/benchmark_take_skip_trailing_stop_v2.py`
  - `ML/run_take_skip_trailing_stop_v2_matrix.py`
- Выполнен локальный smoke-run.
- После первых server run выявлены и исправлены два bug-а, которые меняли интерпретацию matrix results:
  - runner переиспользовал общий кэш между `seq_len`, из-за чего sweep мог схлопываться;
  - `take_skip_trailing_stop_v2` насильно форсил `seq_len=100`, из-за чего `seq20/50/100` не были реальными разными прогонами.
- После фиксов выполнен повторный bounded matrix run на сервере.

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
- `docs/reports/2026-04-18-multi-horizon-take-skip-feature-track.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/research/execution-tracks.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

## Verification

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_trailing_stop_target_labels.py -q
# 8 passed

/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_multi_scale_fractal_features.py -q
# 4 passed

/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_trailing_stop_v2_task.py -q
# 12 passed

/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_take_skip_trailing_stop_v2.py -q
# 5 passed

/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_run_take_skip_trailing_stop_v2_matrix.py -q
# 3 passed

/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_multi_scale_fractal_features.py \
  tests/test_take_skip_trailing_stop_v2_task.py \
  tests/test_benchmark_take_skip_trailing_stop_v2.py \
  tests/test_run_take_skip_trailing_stop_v2_matrix.py -q
# 24 passed

MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_take_skip_trailing_stop_v2_matrix \
  --output-dir ML/reports/take_skip_trailing_stop_v2_matrix \
  --seq-lens 20 50 100 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6
# completed on remote server after bugfix rerun
```

## Results

### Smoke-Run

Локальный smoke-run `transformer_seq20` прошёл весь контур `train → evaluate_test → export → benchmark` и дал первый технический `go`. Он использовался только как проверка целостности контура, а не как итоговый verdict.

### Server Matrix Run

После двух bugfix-ов полный bounded run `seq_len = 20 / 50 / 100` завершился успешно.

Model quality:

| Config | Best epoch | Validation BCE |
|---|---:|---:|
| `transformer_seq20` | 7 | 0.01046 |
| `transformer_seq50` | 7 | 0.01046 |
| `transformer_seq100` | 7 | 0.01046 |

Validation winners:

| Config | Winner | Trades | Trades/year | Validation PF |
|---|---|---:|---:|---:|
| `seq20` | `take_24_x8 + prob_ge_threshold 0.75` | 26 | 6.5 | `inf` |
| `seq50` | `take_24_x8 + prob_ge_threshold 0.70` | 27 | 6.75 | `inf` |
| `seq100` | `take_24_x8 + prob_ge_threshold 0.75` | 27 | 6.75 | `inf` |

Frozen test check:

| Config | Winner | Trades | Trades/year | Test PF | Negative years |
|---|---|---:|---:|---:|---:|
| `seq20` | `take_24_x8 @ 0.75` | 38 | 7.6 | 36.86 | 0 |
| `seq50` | `take_24_x8 @ 0.70` | 41 | 8.2 | **39.74** | 0 |
| `seq100` | `take_24_x8 @ 0.75` | 39 | 7.8 | 37.45 | 0 |

Общий паттерн:

- winner во всех конфигурациях сидит в горизонте `24`
- лучший trailing-stop вариант: `X = 8`
- в отличие от `take_skip_trailing_stop_v1`, живой candidate найден именно в family `prob_ge_threshold`

## Conclusions

- Новый feature-track дал первый валидный положительный verdict после всей trailing-stop retraining chain.
- Ключевое отличие от `take_skip_trailing_stop_v1`: absolute probability threshold перестал быть пустым и стал реальным источником winner-а.
- Практически это означает, что richer representation действительно изменил картину, а не просто переставил "наименее плохие" сделки.
- Лучший текущий кандидат этапа:
  - `seq50`
  - `take_24_x8`
  - `prob_ge_threshold >= 0.70`
- Этот этап не доказывает production-ready статус, но он уверенно опровергает тезис, что линия исчерпана полностью.

## Limitations / Open Questions

- Validation BCE и history обучения у `seq20 / 50 / 100` остались почти одинаковыми; это уже не объясняется двумя исправленными багами, но требует отдельной короткой диагностики.
- `PF=inf` на validation означает отсутствие у winner-а отрицательных сделок в выбранном окне; это сильный сигнал, но его нужно трактовать осторожно.
- Артефакты `validation_grid.csv` и prediction CSV не коммитятся автоматически из-за `gitignore`; для будущих этапов их по-прежнему нужно переносить вручную.

## Next Step

Не менять сейчас target и не запускать новый большой research track. Рациональный следующий шаг:

1. Зафиксировать этот этап как первый положительный verdict `take_skip_trailing_stop_v2`.
2. Сделать короткую диагностику, почему train history почти совпадает по `seq_len`.
3. Отдельно проверить и задокументировать winner:
   - `seq50`
   - `take_24_x8`
   - `prob_ge_threshold >= 0.70`

## Related Materials

- `ML/reports/take_skip_trailing_stop_v2_matrix/manifest.json`
- `ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq20/summary.json`
- `ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/summary.json`
- `ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq100/summary.json`
- `docs/reports/2026-04-17-take-skip-trailing-stop-matrix.md`
- `docs/superpowers/specs/2026-04-17-multi-horizon-take-skip-feature-track-design.md`
- `docs/superpowers/plans/2026-04-17-multi-horizon-take-skip-feature-track.md`
