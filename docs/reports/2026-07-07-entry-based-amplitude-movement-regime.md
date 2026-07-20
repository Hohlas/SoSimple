# Entry-Based Amplitude Movement Regime Audit

> **Дата**: 2026-07-07
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY / AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES
> **Цель**: проверить, даёт ли постановка `entry_movement_H = max(entry_up_H, entry_dn_H)` устойчивый режим движения, который нельзя объяснить простыми baseline-признаками.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-07-entry-based-amplitude-movement-regime-audit.md`

## Context

Предыдущие этапы закрыли текущую ветку `entry-based next open` как направленный сигнал. При этом amplitude-диагностики повторно показывали сильную связь с будущей величиной движения. Этот этап проверяет более строгую гипотезу: не направление сделки, а режим "будет ли заметное движение" после входа.

Ключевое ограничение: это не торговый сигнал и не freeze-кандидат. Этап диагностический, `locked_test` не открывался, `low_n_disclosure=2026` не участвовал в выборе verdict.

## What Was Done

Добавлен runner `ML/baseline/benchmark_entry_based_amplitude_movement.py`.

Он:

- строит targets `entry_movement_3/6/12/24 = max(entry_up_H, entry_dn_H)`;
- считает train-only quantile-флаги `q80/q90/q95`;
- сравнивает простые профили (`ATR`, время, `time+ATR`, плотность фракталов, simple combined) с табличными и sequence-представлениями;
- явно фиксирует, что `distance_to_level_pre_entry_only` не получил безопасной цены решения и был пропущен как `SKIPPED_NO_DECISION_PRICE`;
- отдельно помечает post-entry diagnostic профиль как `selection_eligible=false`;
- сохраняет raw metrics, seed aggregate, quantile lift, yearly diagnostics, target distribution и feature audit;
- принимает verdict только из разрешённого набора.

## Changed Files

- `ML/baseline/benchmark_entry_based_amplitude_movement.py`
- `tests/test_entry_based_amplitude_movement.py`
- `ML/reports/entry_based_amplitude_movement.json`
- `ML/reports/entry_based_amplitude_movement_metrics.csv`
- `ML/reports/entry_based_amplitude_movement_rows.csv`
- `ML/reports/entry_based_amplitude_movement_seed_aggregate.csv`
- `ML/reports/entry_based_amplitude_movement_quantiles.csv`
- `ML/reports/entry_based_amplitude_movement_yearly.csv`
- `ML/reports/entry_based_amplitude_movement_target_distribution.csv`
- `ML/reports/entry_based_amplitude_movement_feature_audit.csv`

## Verification

Команды:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_amplitude_movement.py -q
git diff --check
./.venv/bin/python ML/baseline/benchmark_entry_based_amplitude_movement.py --entry-based-amplitude-movement --no-resume --threads 24
```

Результат:

- focused tests: `39 passed`;
- `git diff --check`: без ошибок;
- clean run: `384/384`, `failed_runs = 0`, `elapsed_sec = 4008.4`, `effective_threads = 24`.

## Results

Итоговый verdict structured artifact:

```text
AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES
```

Лучший eligible профиль по `val_select_spearman_median`:

- `simple_combined / extra_trees_small / H3`
- `val_select_spearman_median = 0.571142`
- `val_eval_spearman_median = 0.693452`
- `val_select_top10_lift_median = 2.076212`
- `val_eval_top10_lift_median = 2.289916`
- `n_seeds = 3`
- `yearly_check_pass = True`

Близкие простые варианты:

- `simple_combined / hist_gradient_boosting / H3`: `0.569425 -> 0.652100`;
- `time_plus_atr / hist_gradient_boosting / H3`: `0.568970 -> 0.622571`;
- `time_plus_atr / extra_trees_small / H3`: `0.566066 -> 0.687145`.

Лучший no-price/no-time sequence вариант:

- `nearest_k60_no_price_coord_sequence_flat / extra_trees_small / H3`;
- `val_select_spearman_median = 0.544603`;
- `val_eval_spearman_median = 0.436387`;
- не побил лучший simple baseline.

Post-entry diagnostic:

- лучший `distance_to_entry_open_post_entry_diagnostic_only / extra_trees_small / H3`;
- `val_select_spearman_median = 0.200225`;
- `selection_eligible = False`;
- `post_entry_diagnostic_only = True`.

Размеры основных таблиц:

- metrics: `384 x 30`;
- rows: `384 x 30`;
- seed aggregate: `132 x 31`;
- quantiles: `3204 x 15`;
- yearly: `2136 x 11`;
- target distribution: `16 x 7`;
- feature audit: `102208 x 7`.
- `feature_audit.status = PASS`, но `tail_warning_count = 42568` и `price_coord_comparison_required = true`.

`yearly.csv` содержит идентификатор конкретного запуска: `profile`, `model_key`, `seed`, `target_family`, `split`, `year`, `horizon`, `spearman`, `top10_lift`, `top_n`, `rest_n`.

### Simple Baseline vs Complex

`H3`, seed aggregate:

| Профиль | Модель | `val_select_spearman_median` | `val_eval_spearman_median` | `val_select_top10_lift_median` | `val_eval_top10_lift_median` |
|---|---:|---:|---:|---:|---:|
| `simple_combined` | `extra_trees_small` | `0.571142` | `0.693452` | `2.076212` | `2.289916` |
| `simple_combined` | `hist_gradient_boosting` | `0.569425` | `0.652100` | `2.013088` | `2.086171` |
| `time_plus_atr` | `hist_gradient_boosting` | `0.568970` | `0.622571` | `2.032228` | `1.977024` |
| `time_plus_atr` | `extra_trees_small` | `0.566066` | `0.687145` | `2.051969` | `2.146760` |
| `time_only_clean` | `extra_trees_small` | `0.496233` | `0.298686` | `2.041446` | `1.613941` |
| `atr_only` | `extra_trees_small` | `0.256860` | `0.595027` | `1.412695` | `1.620063` |
| `fractal_density_only` | `extra_trees_small` | `0.067140` | `0.110999` | `1.240525` | `1.218829` |
| `nearest_k60_no_price_coord_sequence_flat` | `extra_trees_small` | `0.544603` | `0.436387` | `2.047231` | `1.874590` |

Смысл: amplitude объясняется в первую очередь временем и ATR. Фрактальная плотность сама по себе слаба, а лучший no-price/no-time sequence профиль не побил простой baseline. `simple_combined` фактически состоит из `ATR + time + fractal_density`: безопасный `distance_to_level_pre_entry_only` не был выполнен из-за отсутствия цены, доступной в момент решения.

### Feature Audit Detail

`feature_audit.status = PASS` означает отсутствие блокирующей ошибки, а не отсутствие предупреждений.

| Семья признаков | Проверка | Решение | Строк |
|---|---|---|---:|
| `price_coord` | `TAIL_GT10` | `requires_no_price_coord_comparison` | `58104` |
| `non_price_coord` | `TAIL_GT10` | `accept_as_warning` | `42568` |

Крупнейшие профили с `price_coord` warning:

| Профиль | Семья | Решение | Строк | Max rate |
|---|---|---|---:|---:|
| `nearest_k80_sequence_flat` | `price_coord` | `requires_no_price_coord_comparison` | `18216` | `0.609540` |
| `nearest_k60_sequence_flat` | `price_coord` | `requires_no_price_coord_comparison` | `11736` | `0.269485` |
| `nearest_k60_no_time_sequence_flat` | `price_coord` | `requires_no_price_coord_comparison` | `11736` | `0.269485` |
| `nearest_k80_tabular` | `price_coord` | `requires_no_price_coord_comparison` | `10128` | `0.988718` |
| `nearest_k60_tabular` | `price_coord` | `requires_no_price_coord_comparison` | `6288` | `0.507371` |

### Target Distribution Interpretation

Для `entry_movement_3` распределение заметно сдвигается:

| Split | N | p50 | p80 | p90 | p95 |
|---|---:|---:|---:|---:|---:|
| `train` | `44159` | `3.00` | `6.020` | `8.652` | `11.7800` |
| `val_select` | `6648` | `5.01` | `8.742` | `11.880` | `15.5730` |
| `val_eval` | `6646` | `7.99` | `15.740` | `22.465` | `31.1975` |
| `low_n_disclosure` | `1162` | `28.59` | `51.948` | `73.828` | `101.4675` |

Это не ломает Spearman, потому что Spearman проверяет порядок, а не абсолютный масштаб. Но это важное ограничение интерпретации: поздняя validation и 2026 disclosure живут в другом режиме движения, поэтому высокий `val_eval` нельзя трактовать как стабильную торговую пригодность.

### Winner Disclosure

Для выбранного `simple_combined / extra_trees_small / H3`:

| Seed | `val_select_spearman` | `val_eval_spearman` | `low_n_disclosure_spearman` | `val_select_top10_lift` | `val_eval_top10_lift` | `low_n_disclosure_top10_lift` |
|---:|---:|---:|---:|---:|---:|---:|
| `42` | `0.567554` | `0.685360` | `0.154219` | `2.076212` | `2.287535` | `1.571980` |
| `43` | `0.571142` | `0.698511` | `0.169164` | `2.079473` | `2.298744` | `1.567015` |
| `44` | `0.575829` | `0.693452` | `0.162681` | `2.075601` | `2.289916` | `1.676254` |

2026 disclosure не меняет verdict, но показывает ограничение: ранжирование по Spearman слабое, хотя lift остаётся выше 1.

## Conclusions

Гипотеза "amplitude требует сложной фрактальной последовательности" не подтвердилась. Сигнал движения существует как сильная диагностическая связь, но он объясняется простыми baseline-признаками, прежде всего временем и ATR. Фрактальная структура в этой постановке не дала самостоятельного преимущества.

Практический вывод: нельзя использовать этот результат как основание для торгового direction/freeze. Следующий честный шаг должен быть не наращиванием модели, а постановкой decision layer: movement/no-movement filter, отдельный direction/exit слой и заранее зафиксированные правила выбора.

## Limitations / Open Questions

- Широкий search остаётся diagnostic-only и требует отдельной репликации перед любым freeze.
- `feature_audit` содержит `TAIL_GT10` warnings; для `price_coord` это требует no-price сравнения, которое выполнено и не побило simple baseline.
- `low_n_disclosure=2026` раскрыт только как disclosure.
- `distance_to_level_pre_entry_only` пропущен как `SKIPPED_NO_DECISION_PRICE`; значит distance-control без post-entry цены не выполнен.
- Результат говорит о predictability режима движения, а не о прибыли сделки.

## Multiple Testing Context

Search width:

- 15 feature profiles;
- 3 model families с pruning для ridge;
- 3 seed;
- 4 horizons;
- 1 target family;
- 384 model runs: deterministic ridge collapsed to one seed, non-deterministic models use 3 seed.

Verdict выбирался по seed aggregate на `val_select`; `val_eval` и yearly diagnostics использовались как проверка устойчивости. Post-entry diagnostic profiles исключены из выбора.

## Validation Split Disclosure

Использованы те же entry-based split-ы, что в предыдущих этапах. Train используется для fit, порогов quantile target и normalization. `val_select` используется для выбора verdict. `val_eval` используется для проверки. `low_n_disclosure=2026` не влияет на verdict.

## Next Step

Не запускать freeze и не открывать `locked_test`.

Ближайший допустимый план: отдельный bounded audit для decision layer поверх movement regime:

- зафиксировать movement threshold заранее;
- отделить movement filter от direction/exit policy;
- добавить простую репликацию против `time+ATR` и `simple_combined`;
- явно запретить выбор по `val_eval` и `low_n_disclosure`.

## Related Materials

- `ML/reports/entry_based_amplitude_movement.json`
- `docs/ML/benchmark_entry_based_amplitude_movement.py.md`
- `tests/test_entry_based_amplitude_movement.py`
- `docs/reports/2026-07-07-entry-based-fractal-sequence-transformer.md`
- `docs/reports/2026-07-06-entry-based-powerful-tabular-models.md`
