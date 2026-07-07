# Entry-Based Fractal Sequence Transformer

> **Дата**: 2026-07-07
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY / PIVOT_AMPLITUDE
> **Цель**: Проверить, даёт ли ordered sequence-модель по `fractal0..fractal99` устойчивый directional-прирост для механики `entry-based next open`.
> **Related plan/spec**: [2026-07-06-entry-based-fractal-sequence-transformer plan](../superpowers/plans/2026-07-06-entry-based-fractal-sequence-transformer.md)

## Context

Предыдущий этап `Entry-Based Powerful Tabular Models` проверил, спасает ли направление более мощная табличная модель. Ответ был отрицательный: лучший чисто выбранный direction `nearest_k80 / hist_gradient_boosting_strong / H12` дал `val_select=0.0519`, но `val_eval=-0.0009`.

Оставалась последняя узкая гипотеза: возможно, плоская таблица теряет порядок и взаимодействия между 100 сериализованными фракталами. Этот этап проверил ту же механику входа `next open after signal_time`, те же target families и те же split-роли, но вход подавался как последовательность `[rows, 100 tokens, 29 token features]`.

Граница вывода важна: этап не доказывает, что порядок фракталов вообще бесполезен. Он проверяет только текущую ограниченную матрицу признаков, split, target families и моделей внутри `entry-based next open`.

Этап является поисково-диагностическим. Он не мог создать торгового кандидата, открыть `locked_test` или заменить отдельный replication-cycle.

## Уровень этапа

Уровень: `DIAGNOSTIC_ONLY` / поисковый.

Причина: гипотеза сформулирована после нескольких уже прочитанных отчетов по той же ветке `entry-based next open`. Поэтому даже положительный direction мог бы получить только статус `DIRECTION_REPLICATION_REQUIRED`, но не `CANDIDATE`, `FROZEN` или `READY_FOR_LOCKED_TEST`.

## What Was Done

Добавлен runner `ML/baseline/benchmark_entry_based_sequence_transformer.py`.

Проверены 3 representations:

- `all100_sequence`;
- `nearest_k80_sequence`;
- `nearest_k60_sequence`.

Проверены 3 модели:

- `transformer_small`;
- `transformer_medium`;
- `sequence_flat_hist_gradient_boosting`.

Горизонты: `H3`, `H6`, `H12`, `H24`.

Предсказываемые target families:

- `entry_log_ratio`;
- `entry_up`;
- `entry_dn`.

`simple_trade` считался только как грубая gross-диагностика по знаку `pred_entry_log_ratio`. Он не учитывает spread, commission, slippage, sizing и не может выбирать winner после просмотра `val_eval`.

## Multiple Testing Context

Текущий search width:

```text
3 representations * 3 models * 1 seed * 4 horizons * 3 predicted target families = 108 metric comparisons
```

Завершено 9 model/representation jobs. Все jobs предсказывали 12 target columns одновременно.

`all100_sequence` участвует в общей таблице, но является control baseline. Candidate-only direction исключает `all100_sequence`.

`val_select` является единственной selection-метрикой. `val_eval` используется только как проверка выбранной строки. `low_n_disclosure=2026` используется только для раскрытия поведения на малом свежем периоде и не участвует в gates, summary или verdict.

Кумулятивный контекст: этот этап продолжает уже исследованную ветку `Regression Up/Dn -> next open entry -> entry-based closeout -> powerful tabular`. Поэтому direction-порог нельзя трактовать как независимое открытие.

## Validation Split Disclosure

Split:

| Role | Calendar | Rows | Use |
|---|---:|---:|---|
| `train` | `2004-07-06` - `2019-06-20` | `44159` | fit model/scalers |
| `val_select` | `2021-01-04` - `2023-07-14` | `6648` | primary selection |
| `val_eval` | `2023-07-17` - `2025-12-31` | `6646` | check selected row |
| `low_n_disclosure` | `2026-01-02` - `2026-06-04` | `1162` | disclosure-only |
| `locked_test` | not opened | - | forbidden |

Checks:

- `entry_based_smoke_check.status = PASS`;
- `split_horizon_overlap_check.status = PASS`;
- horizon boundary checks for `H3/H6/H12/H24` all pass;
- `locked_test` не открыт;
- `low_n_disclosure=2026` не участвовал в выборе.

## Feature, Tensor And Normalization Contract

Sequence contract:

- `X.shape = [n_rows, 100, 29]`;
- token index `0 = fractal0 = newest`;
- token index `99 = fractal99 = oldest`;
- mask: valid token `True`, padding token `False`;
- padding value: `0.0`.

Token features:

```text
direction, front, back, strong, break, reverse, power, count, impulse,
up_3, dn_3, up_6, dn_6, up_12, dn_12, up_24, dn_24, up_48, dn_48,
log_fractal_atr_ratio, log_shift, log_delta_shift,
price_coord_atr, abs_price_coord_atr, dir_price_coord_atr,
hour_sin, hour_cos, dow_sin, dow_cos
```

`fractal0` `Up/Dn` принудительно занулены. `fractal1..fractal99` `Up/Dn` допускаются как сериализованное состояние MT4 producer, доступное в текущей строке, а не как top-level future target.

Normalization:

| Contract | Value |
|---|---|
| Input scaler | `median_iqr` |
| Input fit split | `train` |
| Valid tokens only | `true` |
| Padding excluded from fit | `true` |
| Clip | `[-10.0, 10.0]` |
| Target scaler | `median_iqr` |
| Target fit split | `train` |
| Input/target scalers separate | `true` |
| Metrics | inverse-transform before metrics |

Target order:

```text
entry_up_3, entry_dn_3, entry_log_ratio_3,
entry_up_6, entry_dn_6, entry_log_ratio_6,
entry_up_12, entry_dn_12, entry_log_ratio_12,
entry_up_24, entry_dn_24, entry_log_ratio_24
```

Tensor audit:

| Status | Errors | Warnings | Decision |
|---|---:|---:|---|
| `WARNING` | `0` | `12` | `accept_as_warning` |

Warnings:

| Split | Features | Family | Rate |
|---|---|---|---:|
| `train` | `price_coord_atr`, `abs_price_coord_atr`, `dir_price_coord_atr` | `TAIL_GT10` | `0.4077` |
| `val_select` | `price_coord_atr`, `abs_price_coord_atr`, `dir_price_coord_atr` | `TAIL_GT10` | `0.4202` |
| `val_eval` | `price_coord_atr`, `abs_price_coord_atr`, `dir_price_coord_atr` | `TAIL_GT10` | `0.4198` |
| `low_n_disclosure` | `price_coord_atr`, `abs_price_coord_atr`, `dir_price_coord_atr` | `TAIL_GT10` | `0.3828` |

Практическое влияние: это не блокирует отрицательный диагностический вывод по direction, потому что warnings раскрыты, одинаковы по смыслу на всех split и не используются для выбора trading candidate. Но это серьёзное ограничение для продолжения ветки: около 40% значений `price_coord_atr`-семейства попадает в `TAIL_GT10`, то есть значительная доля входов живёт в зоне экстремального масштаба или сильной обрезки. Следующий этап нельзя строить поверх этих координат как основного источника сигнала без отдельного аудита распределений, clipping/winsorization/log-преобразований и профилей без price-coordinate признаков.

Machine map JSON:

| Field | Location |
|---|---|
| Verdict | `verdict` and `summary.verdict` |
| Schema version | `schema_version` and `run_config.schema_version` |
| Dependency versions | `dependency_versions` and `run_config.dependency_versions` |
| Selection policy | `selection_policy` and `run_config.selection_policy` |
| Training policy | `training_policy` and `run_config.training_policy` |
| Normalization contract | `normalization_contract` |
| Target normalization | `target_normalization_contract` |
| Run scope hash | `run_config_hash` |

Dependency versions:

| Package | Version |
|---|---:|
| `python` | `3.10.12` |
| `numpy` | `2.2.6` |
| `pandas` | `2.3.3` |
| `scikit-learn` | `1.7.2` |
| `torch` | `2.11.0+cu130` |

## Changed Files

Созданы:

- `ML/baseline/benchmark_entry_based_sequence_transformer.py`;
- `tests/test_entry_based_sequence_transformer.py`;
- `docs/ML/benchmark_entry_based_sequence_transformer.py.md`;
- `docs/reports/2026-07-07-entry-based-fractal-sequence-transformer.md`;
- `ML/reports/entry_based_sequence_transformer.json`;
- `ML/reports/entry_based_sequence_transformer_metrics.csv`;
- `ML/reports/entry_based_sequence_transformer_rows.csv`;
- `ML/reports/entry_based_sequence_transformer_tensor_audit.csv`;
- `ML/reports/entry_based_sequence_transformer_run.log`.

Изменены:

- `docs/tests/tests.md`;
- `MODULE_INDEX.md`;
- `CHANGELOG.md`;
- `CONTEXT_HANDOFF.md`;
- `wiki/research/fractal-stop-research.md`;
- `wiki/index.md`;
- `wiki/log.md`;
- `wiki/REPO_integrity.md`.

## Verification

Команда полного прогона:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_sequence_transformer.py \
  --entry-based-sequence-transformer --resume --device auto --threads 24
```

Результат:

- `progress.done_runs = 9`;
- `progress.total_runs = 9`;
- `failed_runs = []`;
- `finished_at = 2026-07-07T00:06:08+00:00`;
- `elapsed_sec = 45477.6`, примерно `12 ч 38 мин`;
- `run_config_hash = d2b6f0d61cab59409fe7c6b67406599643eb8c3d0b5524cb6f91552d8875fae0`.

Runtime:

| Job | Status | Elapsed sec |
|---|---|---:|
| `all100_sequence / transformer_small` | completed | `4335.6` |
| `all100_sequence / transformer_medium` | completed | `12595.6` |
| `all100_sequence / sequence_flat_hist_gradient_boosting` | completed | `236.6` |
| `nearest_k80_sequence / transformer_small` | completed | `3495.1` |
| `nearest_k80_sequence / transformer_medium` | completed | `12393.3` |
| `nearest_k80_sequence / sequence_flat_hist_gradient_boosting` | completed | `239.2` |
| `nearest_k60_sequence / transformer_small` | completed | `3478.0` |
| `nearest_k60_sequence / transformer_medium` | completed | `12693.7` |
| `nearest_k60_sequence / sequence_flat_hist_gradient_boosting` | completed | `233.0` |

Focused tests:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py -q
```

Результат: `23 passed`.

## Results

### Direction

Лучший candidate-only direction по `val_select`:

| Representation | Model | Horizon | `val_select` | `val_eval` | `2026 disclosure` | Yearly pass |
|---|---|---:|---:|---:|---:|---|
| `nearest_k80_sequence` | `transformer_medium` | `H24` | `0.0539` | `0.0050` | `0.1993` | `false` |

Direction gates не пройдены:

- `val_select=0.0539` ниже gate `0.10`;
- `val_eval=0.0050` ниже gate `0.05`;
- yearly check не пройден;
- результат не является независимым discovery;
- `low_n_disclosure=0.1993` не меняет вывод, потому что 2026 малый и selection-forbidden.

Top candidate-only direction rows by `val_select`:

| Representation | Model | H | `val_select` | `val_eval` | Simple select | Simple eval | Yearly |
|---|---|---:|---:|---:|---:|---:|---|
| `nearest_k80_sequence` | `transformer_medium` | 24 | `0.0539` | `0.0050` | `0.0459` | `0.0273` | false |
| `nearest_k60_sequence` | `transformer_medium` | 24 | `0.0520` | `0.0335` | `0.0523` | `0.0881` | true |
| `nearest_k80_sequence` | `transformer_medium` | 12 | `0.0490` | `0.0001` | `0.0483` | `0.0154` | false |
| `nearest_k80_sequence` | `transformer_medium` | 6 | `0.0388` | `-0.0061` | `0.0410` | `0.0114` | false |
| `nearest_k60_sequence` | `transformer_medium` | 12 | `0.0332` | `0.0285` | `0.0396` | `0.0752` | true |

Best-by-`val_eval` direction is disclosure-only for interpretation:

| Representation | Model | H | `val_select` | `val_eval` | Interpretation |
|---|---|---:|---:|---:|---|
| `nearest_k80_sequence` | `transformer_small` | 24 | `0.0167` | `0.0374` | good eval appears only after sorting by eval |
| `nearest_k60_sequence` | `transformer_medium` | 24 | `0.0520` | `0.0335` | below direction gates |
| `nearest_k80_sequence` | `transformer_small` | 6 | `0.0232` | `0.0319` | below direction gates |
| `nearest_k80_sequence` | `transformer_small` | 12 | `0.0240` | `0.0302` | below direction gates |

Сравнение с предыдущими baselines:

| Baseline | Row | `val_select` | `val_eval` |
|---|---|---:|---:|
| powerful-tabular selected | `nearest_k80 / hist_gradient_boosting_strong / H12` | `0.0519` | `-0.0009` |
| powerful-tabular best-by-eval disclosure | `corridor_5atr / extra_trees_regressor / H12` | `0.0042` | `0.0475` |
| closeout candidate baseline | `nearest_k60 / xgboost_depth5 / H12` | `0.0373` | `0.0274` |
| sequence best by select | `nearest_k80_sequence / transformer_medium / H24` | `0.0539` | `0.0050` |

Вывод: sequence Transformer дал небольшой прирост на `val_select` относительно выбранного powerful-tabular baseline (`0.0539` против `0.0519`), но не дал переносимого direction на `val_eval`.

Годовое разложение выбранного direction:

| Split | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| `val_select` Spearman | `0.0729` | `0.0503` | `0.0256` | - | - |
| `val_eval` Spearman | - | - | `0.0228` | `-0.0182` | `0.0171` |

Этот профиль зависит от годов и не является устойчивым directional signal.

### Amplitude

Лучший amplitude result:

| Representation | Model | Target | H | `val_select` | `val_eval` | `2026 disclosure` | Yearly |
|---|---|---|---:|---:|---:|---:|---|
| `nearest_k60_sequence` | `sequence_flat_hist_gradient_boosting` | `entry_up` | 3 | `0.3229` | `0.3337` | `0.2204` | true |

Top amplitude rows by `val_select`:

| Representation | Model | Target | H | `val_select` | `val_eval` |
|---|---|---|---:|---:|---:|
| `nearest_k60_sequence` | `sequence_flat_hist_gradient_boosting` | `entry_up` | 3 | `0.3229` | `0.3337` |
| `nearest_k80_sequence` | `sequence_flat_hist_gradient_boosting` | `entry_up` | 3 | `0.3228` | `0.3091` |
| `all100_sequence` | `transformer_small` | `entry_up` | 3 | `0.3109` | `0.3010` |
| `nearest_k60_sequence` | `transformer_small` | `entry_up` | 3 | `0.3021` | `0.3099` |
| `nearest_k80_sequence` | `transformer_small` | `entry_dn` | 6 | `0.3016` | `0.3262` |

Годовое разложение выбранной amplitude-строки:

| Split | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| `val_select` `entry_up H3` | `0.3114` | `0.3200` | `0.3379` | - | - |
| `val_eval` `entry_up H3` | - | - | `0.2527` | `0.2763` | `0.2992` |

Amplitude проходит pivot gates: `val_select >= 0.25`, `val_eval >= 0.15`, yearly check true. Но это не направление сделки. Это подтверждает только то, что признаки лучше ранжируют величину движения, чем сторону движения.

Ограничение интерпретации: такой amplitude trace может быть не “тонким рыночным сигналом”, а простым следствием текущей волатильности, расстояния до уровня, времени суток, плотности ближайших фракталов или других простых режимных признаков. Поэтому следующий amplitude-план должен сравнить sequence-модель с простыми baselines: ATR-only, time-only, distance-to-level-only и last-N-fractal-counts-only.

### Post-Hoc Simple Trade Sanity Check

`simple_trade` здесь не является evidence и не является торговой проверкой. Это post-hoc sanity check: грубая проверка знака предсказания без spread, commission, slippage, fill policy, position sizing и MT4 simulator. Таблицы ниже нужны только для обнаружения очевидного противоречия; выбирать правило по ним запрещено.

Top `simple_trade` by `val_select`:

| Representation | Model | H | `val_select` direction | `val_eval` direction | Simple select | Simple eval |
|---|---|---:|---:|---:|---:|---:|
| `nearest_k60_sequence` | `transformer_medium` | 24 | `0.0520` | `0.0335` | `0.0523` | `0.0881` |
| `nearest_k80_sequence` | `sequence_flat_hist_gradient_boosting` | 24 | `0.0312` | `-0.0031` | `0.0512` | `-0.0107` |
| `nearest_k80_sequence` | `transformer_medium` | 12 | `0.0490` | `0.0001` | `0.0483` | `0.0154` |
| `nearest_k80_sequence` | `transformer_medium` | 24 | `0.0539` | `0.0050` | `0.0459` | `0.0273` |

Top `simple_trade` by `val_eval` is disclosure-only:

| Representation | Model | H | `val_select` direction | `val_eval` direction | Simple select | Simple eval |
|---|---|---:|---:|---:|---:|---:|
| `nearest_k80_sequence` | `transformer_small` | 24 | `0.0167` | `0.0374` | `0.0147` | `0.1458` |
| `nearest_k60_sequence` | `transformer_small` | 24 | `-0.0181` | `0.0169` | `0.0063` | `0.1317` |
| `nearest_k60_sequence` | `transformer_small` | 12 | `-0.0090` | `0.0216` | `0.0137` | `0.1293` |

Положительные строки `simple_trade val_eval` не являются торговым сигналом и не являются evidence в пользу candidate. Лучшие eval-строки находятся только после просмотра `val_eval`, а выбранные по протоколу direction-строки не проходят gates.

## Conclusions

Вердикт: `PIVOT_AMPLITUDE`.

Что подтверждено:

- sequence-представление построено и прошло smoke/split/normalization контракты;
- в текущей ограниченной матрице `entry-based next open` два Transformer-профиля и flattened sequence baseline не спасли direction;
- лучший direction дал только `0.0539 -> 0.0050`, то есть почти исчез на `val_eval`;
- объяснение “именно плоская таблица потеряла полезный порядок фракталов” не подтвердилось для этой ограниченной постановки `next open`;
- amplitude trace снова сильнее и устойчивее: `0.3229 -> 0.3337`.

Что не подтверждено:

- устойчивое направление сделки;
- trading candidate;
- право открывать `locked_test`;
- право выбирать по 2026;
- право трактовать positive simple_trade eval как правило входа.

Invalidated assumptions:

- “В этой постановке нужен Transformer, потому что табличная модель потеряла порядок”: не подтвердилось.
- “Более сложная sequence-модель должна усилить direction”: не подтвердилось.
- “Высокий 2026 disclosure может спасти winner”: запрещено методикой и не влияет на verdict.

## Limitations / Open Questions

- Один seed `42` достаточен для отрицательного direction-вывода, но слабоват даже для будущего положительного amplitude-вывода. Если следующий этап опирается на amplitude, лучший amplitude-профиль нужно повторить на нескольких seeds или близких моделях.
- `tensor_audit.status=WARNING` по ATR-координатам требует отдельного feature-audit перед следующим этапом: сколько значений обрезается, как меняется результат без этих признаков, и держится ли signal после другого tail-transform.
- `time_only_clean` и `no_time_sequence` как отдельные control-профили не попали в финальную 9-job матрицу артефакта; это ограничивает силу утверждения “модель выучила именно фрактальную структуру”.
- `no_price_coord_sequence` не проверялся; поэтому нельзя отделить вклад фрактальной структуры от вклада хвостатых price-coordinate признаков.
- `sequence_flat_hist_gradient_boosting` видит позиционный порядок через flattened columns, поэтому его успех не доказывает, что порядок не нужен; он показывает только, что attention не дал преимущества поверх явной позиционной таблицы.
- Amplitude пока не превращена в торговое решение. Нужен отдельный план: movement/no-movement filter, выбор горизонта, независимый direction/exit слой, затем только gross/backtest.

## Next Step

Рекомендуемый следующий этап: отдельный `amplitude / movement-regime` plan.

Минимальные правила следующего плана:

- не формулировать задачу как “торговать amplitude”;
- сначала определить, как amplitude превращается в решение: фильтр движения, горизонт, запрет брать направление из того же результата;
- включить обязательные control-профили: `time_only_clean`, `no_time_sequence`, `no_price_coord_sequence`;
- включить простые amplitude baselines: ATR-only, time-only, distance-to-level-only, last-N-fractal-counts-only;
- проверить movement/no-movement отдельно от направления: сначала “будет ли достаточно движения после входа”, без выбора стороны;
- для amplitude добавить quantile-таблицы: верхние 5/10/20% предсказаний против остальных, по годам;
- не использовать `entry_log_ratio` как главный target;
- не открывать `locked_test`;
- не выбирать по `low_n_disclosure=2026`;
- обязательно включить yearly checks и disclosure-only таблицы;
- решить warning по `price_coord_atr` до сильного вывода: distribution audit, clipping/winsorization/log-transform comparison и результат без этих признаков.

Запрещённые следующие шаги:

- freeze direction по текущему `next open`;
- выбирать `nearest_k80_sequence / transformer_medium / H24` как торговое правило;
- выбирать лучший `simple_trade val_eval` после просмотра `val_eval`;
- считать 2026 evidence основанием для продолжения direction без replication.
- закрывать всю идею фрактальной последовательности глобально; закрыта только текущая ограниченная `entry-based next open` ветка.

## Related Materials

- [Plan: Entry-Based Fractal Sequence Transformer](../superpowers/plans/2026-07-06-entry-based-fractal-sequence-transformer.md)
- [Entry-Based Powerful Tabular Models](2026-07-06-entry-based-powerful-tabular-models.md)
- [Entry-Based Next Open Closeout](2026-07-04-entry-based-next-open-closeout.md)
- [Fractal Selection Ablation On Entry-Based Target](2026-07-03-fractal-selection-ablation-entry-based-target.md)
- `ML/reports/entry_based_sequence_transformer.json`
- `ML/reports/entry_based_sequence_transformer_metrics.csv`
- `ML/reports/entry_based_sequence_transformer_rows.csv`
- `ML/reports/entry_based_sequence_transformer_tensor_audit.csv`
- `ML/baseline/benchmark_entry_based_sequence_transformer.py`
- `tests/test_entry_based_sequence_transformer.py`
