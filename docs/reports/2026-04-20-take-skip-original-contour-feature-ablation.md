# Take/Skip Original Contour Feature Ablation

> **Date**: 2026-04-20
> **Status**: Completed
> **Goal**: Проверить `lib_PIC` path/geometry признаки в старом прибыльном single-tensor `take_skip_v2` контуре.
> **Related plan**: `docs/superpowers/plans/2026-04-20-take-skip-original-contour-feature-ablation.md`
> **Related commit**: pending

## Context

Этап `take_skip_lib_pic_feature_training` проверял новый dual-stream контур: фракталы и `lib_PIC` признаки подавались в модель двумя разными ветками. Все 9 конфигураций там получили `reject`.

Этот отрицательный результат не закрывал гипотезу пользователя: "добавить новые признаки к исходному baseline". Старый прибыльный `take_skip_v2` контур работал иначе: все engineered-признаки добавлялись внутрь одного sequence tensor как повторяющиеся каналы на каждом шаге последовательности.

Поэтому этот этап сделал controlled ablation:

1. Восстановить старый single-tensor контур.
2. Проверить, воспроизводит ли он старую прибыльную область.
3. Добавить `lib_PIC` path-признаки поверх старого baseline.
4. Добавить `lib_PIC` path + geometry признаки поверх старого baseline.

## What Was Done

Добавлен runner:

- `ML/run_take_skip_original_contour_feature_matrix.py`

Он строит один общий входной tensor:

- parsed fractals: `(N, seq_len, 20)`;
- старые multi-scale summaries;
- старые row-wise признаки;
- опциональные `lib_PIC` path/geometry признаки;
- все engineered-признаки повторяются на каждом шаге sequence.

Проверенные режимы:

- `original_baseline`;
- `original_plus_path`;
- `original_plus_geometry_path`.

Проверенные длины истории:

- `seq_len = 20 / 50 / 100`.

Runner автоматически использовал только доступные в DATA цели:

- `take_12_x2`, `take_12_x4`, `take_12_x8`;
- `take_24_x2`, `take_24_x4`, `take_24_x8`;
- `take_48_x2`, `take_48_x4`, `take_48_x8`.

## Verification

Фокусные тесты:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_take_skip_original_contour_feature_matrix.py \
  tests/test_take_skip_trailing_stop_v2_task.py \
  tests/test_take_skip_lib_pic_feature_matrix.py \
  -q
```

Результат:

```text
15 passed, 1 warning in 14.39s
```

Предупреждение PyTorch про nested tensors уже встречалось раньше и не меняет результат.

Wiki integrity:

```bash
/home/hohla/git/SoSimple/.venv/bin/python wiki/wiki.py verify
```

Результат:

```text
OK — index is up to date.
```

## Control Run

Перед полной матрицей был запущен контроль `original_baseline_seq50`.

Контроль прошёл gate:

| Metric | Value |
|---|---:|
| input_features | 539 |
| target | `take_24_x8` |
| selector | `prob_ge_threshold` |
| threshold | 0.70 |
| validation trades/year | 7.75 |
| validation PF | inf |
| test trades/year | 9.2 |
| test PF | 49.58 |
| test negative_year_slices | 0 |

Вывод: старый single-tensor контур восстановлен корректно. Можно было запускать feature-addition matrix.

## Full Matrix

Серверный запуск:

```bash
PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib python \
  -m ML.run_take_skip_original_contour_feature_matrix \
  --output-dir ML/reports/take_skip_original_contour_feature_matrix \
  --feature-modes original_baseline original_plus_path original_plus_geometry_path \
  --seq-lens 20 50 100 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6 \
  --jobs auto \
  --torch-threads auto \
  --cpu-load 0.5 \
  --clear-cache
```

Runtime: `2840.42 sec` (~47 min).

CPU schedule:

| cpu_count | cpu_load | target_threads | jobs | torch_threads |
|---:|---:|---:|---:|---:|
| 32 | 0.5 | 16 | 4 | 4 |

## Results

Все 9 конфигураций получили `verdict=go`.

| Run | Input features | Validation selector | Val trades/year | Val PF | Test trades/year | Test PF | Test neg years |
|---|---:|---|---:|---:|---:|---:|---:|
| `original_plus_path_seq50` | 844 | `take_24_x8`, `prob>=0.60` | 9.75 | 16.07 | 10.2 | 38.78 | 0 |
| `original_plus_path_seq20` | 844 | `take_24_x8`, `prob>=0.50` | 7.75 | 14.73 | 9.6 | 38.30 | 0 |
| `original_baseline_seq20` | 539 | `take_24_x8`, `prob>=0.80` | 7.25 | inf | 9.4 | 23.79 | 0 |
| `original_baseline_seq100` | 539 | `take_24_x8`, `prob>=0.90` | 7.00 | inf | 8.6 | 41.39 | 0 |
| `original_baseline_seq50` | 539 | `take_24_x8`, `prob>=0.90` | 7.25 | inf | 8.4 | 43.35 | 0 |
| `original_plus_path_seq100` | 844 | `take_24_x8`, `top_k=7.5%` | 9.00 | 14.55 | 7.2 | 31.52 | 0 |
| `original_plus_geometry_path_seq20` | 989 | `take_24_x8`, `top_k=5%` | 6.00 | 82.24 | 4.8 | 92.53 | 0 |
| `original_plus_geometry_path_seq100` | 989 | `take_24_x8`, `top_k=5%` | 6.00 | 30.01 | 4.8 | 88.08 | 0 |
| `original_plus_geometry_path_seq50` | 989 | `take_12_x8`, `top_k=5%` | 6.00 | 13.53 | 4.8 | 45.54 | 0 |

Additional grid diagnostics:

| Run | Eligible rows (`PF>1`, trades/year>=6) | Rows with `PF>1` |
|---|---:|---:|
| `original_baseline_seq100` | 69 | 114 |
| `original_baseline_seq50` | 69 | 112 |
| `original_baseline_seq20` | 57 | 105 |
| `original_plus_path_seq50` | 53 | 102 |
| `original_plus_path_seq100` | 36 | 85 |
| `original_plus_path_seq20` | 29 | 109 |
| `original_plus_geometry_path_seq20` | 24 | 90 |
| `original_plus_geometry_path_seq50` | 24 | 65 |
| `original_plus_geometry_path_seq100` | 23 | 68 |

## Conclusions

1. Старый контур восстановлен.

`original_baseline` снова даёт сильную область вокруг `take_24_x8`. Это подтверждает, что прошлый провал dual-stream этапа был связан не с данными как таковыми, а с другим training contour.

2. `path` признаки полезны в практическом смысле.

Лучший practical candidate:

- `original_plus_path_seq50`;
- `take_24_x8`;
- `prob_ge_threshold >= 0.60`;
- validation: `9.75` сделок/год, `PF=16.07`;
- test: `10.2` сделок/год, `PF=38.78`, `negative_year_slices=0`.

Относительно `original_baseline_seq50`:

- test trades/year выросли `8.4 -> 10.2`;
- test PF снизился `43.35 -> 38.78`, но остался очень высоким;
- отрицательные годовые срезы остались `0`;
- drawdown немного снизился `4.38 -> 3.89 ATR`.

Это не "революционное улучшение", но это полезный trade-off: больше сделок при сохранении качества.

3. `geometry` не выбран как practical candidate.

Geometry-конфигурации показывают очень высокий PF на test, но дают только `4.8` сделок/год на test. Это ниже практического порога `6` сделок/год, поэтому их нельзя продвигать как основной режим.

4. BCE не является достаточным критерием.

`original_plus_geometry_path` имеет заметно худший BCE (`~0.022-0.024`), но всё равно находит редкие хорошие сделки. Это ещё раз подтверждает: для trading-selection важен не только средний loss, а качество верхнего хвоста ранжирования.

## Decision

Для следующей практической проверки выбрать:

```text
run: original_plus_path_seq50
score: take_24_x8
selector: prob_ge_threshold
threshold: 0.60
exit: x8
```

Назначение кандидата: более частая версия quality-системы, а не замена всех текущих правил.

`original_baseline_seq50/100` оставить как quality anchor: меньше сделок, чуть выше PF.

`geometry` оставить как диагностическую ветку, но не двигать в MT4 без отдельной причины.

## Limitations

- Test остаётся историческим frozen split, не forward.
- Использована старая target-сетка `x2/x4/x8`; `x10/x12` не проверялись в этом training run.
- Результат нужно подтвердить через export signals и MT4 trailing execution.
- Разные запуски могут немного отличаться из-за PyTorch/CPU недетерминизма; критерий — область результата, а не идентичные числа.

## Next Step

Сформировать selected rule для `original_plus_path_seq50`, экспортировать сигналы и проверить в MT4:

- сначала `ML_TrailATR=8`, `ML_TakeProfitATR=0`;
- затем сравнить с текущими `quality` и `frequency` сигналами по тем же правилам execution.

Если MT4 подтверждает качество, новый кандидат становится третьей независимой системой рядом с `quality` и `frequency`.

## Related Materials

- `ML/run_take_skip_original_contour_feature_matrix.py`
- `ML/reports/take_skip_original_contour_feature_matrix/manifest.json`
- `ML/reports/take_skip_original_contour_feature_matrix/*/summary.json`
- `ML/reports/take_skip_original_contour_feature_matrix/*/benchmark/final_verdict.json`
- `ML/reports/take_skip_original_contour_feature_matrix/*/benchmark/validation_grid.csv`
- `docs/reports/2026-04-20-take-skip-lib-pic-feature-training.md`
- `docs/reports/2026-04-20-take-skip-lib-pic-selection.md`
