# Entry-Based Powerful Tabular Models

> **Дата**: 2026-07-06
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY / PIVOT_AMPLITUDE
> **Цель**: Проверить, извлекают ли более мощные табличные модели полезный directional signal из закрытой ветки `entry-based next open`, без открытия `locked_test` и без изменения механики входа.
> **Related plan/spec**: [2026-07-05-entry-based-powerful-tabular-models plan](../superpowers/plans/2026-07-05-entry-based-powerful-tabular-models.md)

## Context

Closeout ветки `entry-based next open` завершился вердиктом `PIVOT`: направленный `entry_log_ratio` остался слабым, а amplitude trace (`entry_up` / `entry_dn`) был заметно сильнее.

Этот этап проверяет последнюю узкую гипотезу внутри той же mechanics: не была ли слабость direction вызвана недостаточной мощностью прежних табличных моделей. Проверка остаётся post-hoc diagnostic: профили, горизонты и модели выбраны после чтения предыдущих результатов, поэтому положительный direction мог бы стать только `DIRECTION_REPLICATION_REQUIRED`, не freeze/candidate.

## What Was Done

Добавлен runner `ML/baseline/benchmark_entry_based_powerful_tabular.py`.

Проверены 4 representation profiles:

- `all100`;
- `corridor_5atr`;
- `nearest_k60`;
- `nearest_k80`.

Проверены 10 моделей:

- `xgboost_depth3_baseline`;
- `xgboost_depth5_baseline`;
- `xgboost_depth7_regularized`;
- `xgboost_depth9_regularized`;
- `lightgbm_depth7_regularized`;
- `lightgbm_leaves63_regularized`;
- `catboost_depth6_regularized`;
- `catboost_depth8_regularized`;
- `extra_trees_regressor`;
- `hist_gradient_boosting_strong`.

Горизонты: `H3`, `H6`, `H12`, `H24`.

Предсказываемые target families: `entry_log_ratio`, `entry_up`, `entry_dn`.

Derived trading diagnostic: `simple_trade`.

## Multiple Testing Context

Текущий search width:

```text
4 representations * 10 models * 1 seed * 4 horizons * 3 predicted target families = 480 metric comparisons
```

40 model/profile jobs завершены. `simple_trade` раскрывается отдельно как derived diagnostic и не считается четвёртым predicted target family.

`all100` участвует в общем сравнении, но является control baseline. Candidate-only summary и direction verdict исключают `all100`.

Положительный direction result не мог стать freeze/candidate на этом этапе. Максимально допустимый положительный direction status: `DIRECTION_REPLICATION_REQUIRED`.

## Validation Split Disclosure

Split:

| Role | Calendar | Use |
|---|---:|---|
| `train` | `<=2020` | fit model |
| `validation` | `2021-2025` | selection/evaluation |
| `val_select` | внутри validation | primary selection |
| `val_eval` | внутри validation | check selected row |
| `low_n_disclosure` | `2026` | disclosure-only |
| `locked_test` | not opened | forbidden |

Rows from smoke-check:

| Split | Rows |
|---|---:|
| `train` | 44159 |
| `validation` | 13296 |
| `low_n_disclosure` | 1162 |

`split_horizon_overlap_check.status = PASS`, включая `H24`.

`low_n_disclosure=2026` не участвовал в summary, gates или verdict.

## Feature Contract And Audit

Runner переиспользует feature builder closeout-этапа:

- structure fields;
- shift/age и ATR-координаты;
- price/distance относительно `fractal0.price`;
- serialized `Up/Dn` внутри slot-признаков;
- row time context.

Запрещённые top-level target/label поля не входят во входные признаки.

Audit:

- `entry_based_smoke_check.status = PASS`;
- `scale_audit.status = WARNING`;
- `audit_decisions` записаны;
- `normalization_contract.fit_split = train`;
- validation/disclosure не fit-ят scaler;
- `run_config_hash = 7a67a59aa22a5d153ae541a8f9fc3eb3698ba3172a4217eb8572058d3ebb518e`.

Scale warnings не стали блокером для диагностического вывода, но они запрещают выбирать конкретный profile winner по этому прогону. Причина: предупреждения есть у всех проверенных профилей, а у `corridor_5atr` дополнительно есть dominance warning по `structure_fields`.

| Profile | Status | Flags | Main warning family | Dominance warning | Practical impact |
|---|---|---:|---|---|---|
| `all100` | `WARNING` | 686 | `NEAR_CONSTANT` | none | control-only baseline, не candidate |
| `corridor_5atr` | `WARNING` | 1411 | `NEAR_CONSTANT` | `structure_fields max_to_median_p99 = 104.38` | нельзя объявлять profile winner; top eval rows читаются только как заднее disclosure |
| `nearest_k60` | `WARNING` | 180 | `NEAR_CONSTANT` | none | можно использовать только как диагностический trace |
| `nearest_k80` | `WARNING` | 240 | `NEAR_CONSTANT` | none | выбранный direction trace не получает candidate status |

JSON machine map:

| Field | Location |
|---|---|
| Verdict | `verdict` and `summary.verdict` |
| Schema version | `schema_version` and `run_config.schema_version` |
| Dependency versions | `dependency_versions` and `run_config.dependency_versions` |
| Normalization contract | `normalization_contract` and `runs[].normalization_contract` |
| Run scope hash | `run_config_hash` |

Dependency versions:

| Package | Version |
|---|---:|
| `catboost` | `1.2.8` |
| `lightgbm` | `4.6.0` |
| `scikit-learn` | `1.7.2` |
| `xgboost` | `3.2.0` |

## Changed Files

Созданы:

- `ML/baseline/benchmark_entry_based_powerful_tabular.py`;
- `tests/test_entry_based_powerful_tabular.py`;
- `docs/ML/benchmark_entry_based_powerful_tabular.py.md`;
- `docs/reports/2026-07-06-entry-based-powerful-tabular-models.md`;
- `ML/reports/entry_based_powerful_tabular.json`;
- `ML/reports/entry_based_powerful_tabular_metrics.csv`;
- `ML/reports/entry_based_powerful_tabular_rows.csv`;
- `ML/reports/entry_based_powerful_tabular_scale_audit.csv`.

Изменены:

- `requirements.txt`: добавлен `catboost==1.2.8`;
- `docs/tests/tests.md`;
- `MODULE_INDEX.md`;
- `CHANGELOG.md`;
- `CONTEXT_HANDOFF.md`;
- `wiki/research/fractal-stop-research.md`;
- `wiki/index.md`;
- `wiki/log.md`;
- `wiki/REPO_integrity.md`.

## Verification

Чистый запуск:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_powerful_tabular.py \
  --entry-based-powerful-tabular --no-resume
```

Результат:

- `progress.done_runs = 40`;
- `progress.total_runs = 40`;
- `failed_runs = []`;
- `started_at = 2026-07-05T14:21:56+00:00`;
- `finished_at = 2026-07-06T00:50:16+00:00`;
- `elapsed_sec = 37777.7`;
- `thread_count = 24`.

Тесты:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_powerful_tabular.py -q
```

Результат: `30 passed`.

Полный regression после Python-изменений:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Результат: `1101 passed, 30 warnings`.

## Results

### Direction

Лучший directional result overall:

| Profile | Model | Horizon | `val_select` Spearman | `val_eval` Spearman |
|---|---|---:|---:|---:|
| `nearest_k80` | `hist_gradient_boosting_strong` | `H12` | `0.0519` | `-0.0009` |

Top candidate-only direction rows:

| Profile | Model | Horizon | `val_select` | `val_eval` |
|---|---|---:|---:|---:|
| `nearest_k80` | `hist_gradient_boosting_strong` | `H12` | `0.0519` | `-0.0009` |
| `nearest_k80` | `catboost_depth8_regularized` | `H24` | `0.0513` | `-0.0066` |
| `nearest_k80` | `lightgbm_leaves63_regularized` | `H24` | `0.0475` | `-0.0060` |
| `nearest_k80` | `catboost_depth6_regularized` | `H24` | `0.0471` | `-0.0125` |
| `nearest_k80` | `lightgbm_leaves63_regularized` | `H12` | `0.0413` | `0.0245` |

Direction gates не пройдены:

- `val_select` ниже gate `0.10`;
- выбранная строка падает на `val_eval`;
- same-model `all100` comparison на `val_eval` хуже: candidate minus all100 `-0.0084`;
- yearly check на `val_eval` не проходит;
- `simple_trade_eval_mean = -0.0609`.

Сравнение с предыдущим closeout candidate-only baseline:

| Metric | Previous closeout baseline | Powerful tabular best candidate | Delta |
|---|---:|---:|---:|
| `entry_log_ratio val_select` | `0.0373` | `0.0519` | `+0.0146` |
| `entry_log_ratio val_eval` | `0.0274` | `-0.0009` | `-0.0283` |
| `simple_trade val_select` | `0.0381` | `0.0732` | `+0.0351` |
| `simple_trade val_eval` | `-0.0148` | `-0.0609` | `-0.0461` |

Best candidate-only direction by `val_eval` is disclosure-only for interpretation. It did not participate in selection:

| Profile | Model | Horizon | `val_select` | `val_eval` | Interpretation |
|---|---|---:|---:|---:|---|
| `corridor_5atr` | `extra_trees_regressor` | `H12` | `0.0042` | `0.0475` | good eval appears only after looking at eval |
| `corridor_5atr` | `extra_trees_regressor` | `H6` | `0.0083` | `0.0427` | same profile/model, weak select |
| `corridor_5atr` | `extra_trees_regressor` | `H3` | `-0.0010` | `0.0280` | not selectable |

This supports the verdict: if a row is found only by sorting `val_eval`, it is hindsight disclosure, not a clean winner.

### Amplitude

Amplitude trace подтверждён:

| Profile | Model | Target | Horizon | `val_select` Spearman | `val_eval` Spearman |
|---|---|---|---:|---:|---:|
| `nearest_k60` | `hist_gradient_boosting_strong` | `entry_up` | `H3` | `0.3412` | `0.4419` |
| `nearest_k60` | `catboost_depth8_regularized` | `entry_up` | `H3` | `0.3405` | `0.4521` |
| `nearest_k60` | `catboost_depth6_regularized` | `entry_up` | `H3` | `0.3399` | `0.4541` |
| `corridor_5atr` | `catboost_depth8_regularized` | `entry_up` | `H3` | `0.3397` | `0.4539` |
| `nearest_k80` | `catboost_depth8_regularized` | `entry_up` | `H3` | `0.3395` | `0.4554` |

Yearly diagnostics for selected amplitude row:

| Split | Year scores | Positive years | Best-year share | Without-best-year score | Pass |
|---|---|---:|---:|---:|---|
| `val_select` | `0.3378 / 0.3419 / 0.3339` | 3 | `0.3373` | `0.3358` | true |
| `val_eval` | `0.2999 / 0.2632 / 0.3248` | 3 | `0.3658` | `0.2816` | true |

### Simple Trade Diagnostic

Top `simple_trade` by `val_select`:

| Profile | Model | Horizon | Select mean | Eval mean | Trades |
|---|---|---:|---:|---:|---:|
| `nearest_k80` | `lightgbm_leaves63_regularized` | `H24` | `0.0762` | `-0.1318` | 6648 |
| `nearest_k80` | `hist_gradient_boosting_strong` | `H12` | `0.0732` | `-0.0609` | 6648 |
| `corridor_5atr` | `xgboost_depth9_regularized` | `H12` | `0.0691` | `0.0179` | 6648 |

Top `simple_trade` by `val_eval`:

| Profile | Model | Horizon | Select mean | Eval mean | Trades |
|---|---|---:|---:|---:|---:|
| `corridor_5atr` | `extra_trees_regressor` | `H6` | `0.0223` | `0.0418` | 6646 |
| `corridor_5atr` | `extra_trees_regressor` | `H12` | `0.0156` | `0.0237` | 6646 |
| `corridor_5atr` | `lightgbm_leaves63_regularized` | `H3` | `0.0191` | `0.0198` | 6646 |

`simple_trade` остаётся gross diagnostic: без spread, commission, slippage, fill policy, position sizing и MT4 simulator.

Positive `simple_trade val_eval` rows are not a trading signal. The leader selected by `val_select` failed on `val_eval`, while the best `val_eval` row can be found only after looking at `val_eval`; using it as a rule would be post-hoc selection.

### 2026 Low-N Disclosure

2026 не использовался для выбора.

Top 2026 disclosure direction rows:

| Profile | Model | Horizon | Spearman |
|---|---|---:|---:|
| `nearest_k60` | `lightgbm_leaves63_regularized` | `H24` | `0.1236` |
| `nearest_k60` | `catboost_depth8_regularized` | `H24` | `0.1225` |
| `nearest_k80` | `lightgbm_leaves63_regularized` | `H24` | `0.1195` |
| `nearest_k60` | `xgboost_depth9_regularized` | `H24` | `0.1128` |
| `nearest_k60` | `xgboost_depth7_regularized` | `H24` | `0.1061` |

Positive 2026 H24 rows do not change verdict:

- `low_n_disclosure` has only 1162 rows;
- 2026 is disclosure-only and not used by gates, ranking or verdict;
- top 2026 rows are mostly H24, which may reflect a different regime/horizon than the selected H12 row;
- selecting a 2026 H24 row after viewing this table would be another post-hoc choice.

## Conclusions

Мощные табличные модели не спасли directional постановку `entry-based next open`.

Лучший direction стал немного выше на `val_select` относительно closeout candidate-only baseline, но не удержался на `val_eval`, проиграл same-model `all100` на `val_eval`, не прошёл yearly gate и дал отрицательный `simple_trade` на `val_eval`.

Мощность табличных моделей не была главным ограничением direction; ограничение, вероятно, в постановке входа `next open`, в самой directed-цели или в том, что плоское табличное представление теряет последовательную структуру фракталов.

Amplitude trace подтверждён сильнее и устойчивее direction: `entry_up H3` на `nearest_k60 / hist_gradient_boosting_strong` даёт `0.3412 -> 0.4419` и проходит yearly diagnostics.

Вердикт: `PIVOT_AMPLITUDE`.

Scope note: этот отчет закрывает только powerful tabular closeout. Он не закрывает отдельную roadmap-гипотезу `Fractal-sequence transformer on serialized 100-fractal history`, где вход меняется с плоской таблицы на последовательность `[rows, 100 fractals, fields]`.

## Limitations / Open Questions

- Этап post-hoc: модели и профили выбраны после предыдущих результатов.
- Один seed достаточен только для diagnostic pass, не для сильного вывода.
- `locked_test` не открыт.
- `EURUSD` и cross-pair validation не запускались.
- `scale_audit.status = WARNING`; warnings раскрыты, но запрещают сильный вывод о конкретном profile winner.
- `simple_trade` gross-only, не backtest.
- Amplitude confirmation не новое открытие; closeout уже показывал сильный amplitude trace.
- `PIVOT_AMPLITUDE` не означает "торговать amplitude": отдельный follow-up должен заранее определить, как amplitude превращается в решение.

## Next Step

Не продолжать direction search внутри текущей `entry-based next open` постановки как табличный candidate-cycle.

Ближайший незакрытый roadmap-шаг: отдельный bounded plan для fractal-sequence transformer на serialized 100-fractal history. Это не “ещё одна мощная табличная модель”, а проверка другого входного представления.

Дополнительный допустимый план после этого: отдельная bounded amplitude / movement-regime постановка, где основной вопрос заранее формулируется вокруг `entry_up` / `entry_dn` / movement potential, а не вокруг `entry_log_ratio`.

До backtest-слоя нужно заранее зафиксировать: movement/no-movement filter, выбор горизонта, запрет брать направление из текущего direction result и отдельный gross/backtest слой только после чистого отбора.

## Related Materials

- [Plan: Entry-Based Powerful Tabular Models](../superpowers/plans/2026-07-05-entry-based-powerful-tabular-models.md)
- [Closeout report](2026-07-04-entry-based-next-open-closeout.md)
- [Runner docs](../ML/benchmark_entry_based_powerful_tabular.py.md)
- `ML/reports/entry_based_powerful_tabular.json`
- `ML/reports/entry_based_powerful_tabular_metrics.csv`
- `ML/reports/entry_based_powerful_tabular_rows.csv`
- `ML/reports/entry_based_powerful_tabular_scale_audit.csv`
