# Entry-Based Next Open Closeout

> **Дата**: 2026-07-04
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY / PIVOT
> **Цель**: Закрыть текущую ветку `entry-based next open` без `EURUSD`, проверить shortlist профилей на большом validation, разделить direction/amplitude trace и принять `STOP`, `PIVOT` или `CONTINUE`.
> **Related plan/spec**: [2026-07-04-entry-based-next-open-closeout plan](../superpowers/plans/2026-07-04-entry-based-next-open-closeout.md)

## Context

Предыдущий этап нашёл слабый `H12` trace на `entry-based next open`, но без отдельного entry-based smoke-check и без нового split-контракта `train` / large `validation`.

Этот closeout не открывает `locked_test`, не проверяет `EURUSD` и не расширяет поиск. Он отвечает на узкий вопрос: есть ли в уже выбранной механике входа на следующий доступный `entry_open` достаточно полезный direction signal, чтобы готовить отдельный frozen `locked_test` план.

## What Was Tested

Проверены только профили `all100`, `corridor_5atr`, `nearest_k20`, `nearest_k60`, `nearest_k80`.

Модели: `xgboost_depth3`, `xgboost_depth5`, `hist_gradient_boosting`, `ridge`.

Горизонты: `H3`, `H6`, `H12`, `H24`.

Target families:

- `entry_log_ratio_H` как направленный баланс;
- `entry_up_H` / `entry_dn_H` как амплитуда;
- `simple_trade_H` как gross diagnostic по знаку `pred_entry_log_ratio_H`.

## Search Width Disclosure

Текущий search width: `5 representations * 4 models * 1 seed * 4 horizons * 3 target families`.

Инструмент: текущий инструмент без cross-pair validation.

Entry/exit policy: сигнал существует на `signal_time`, вход только по следующему доступному `entry_open`; выход здесь не моделируется, `simple_trade` использует знак фактического `entry_log_ratio`.

Статус результата ограничен `DIAGNOSTIC_ONLY` / `RESEARCH_ONLY`, потому что `locked_test` не открыт.

## Entry-Based Smoke Check

Stage-specific smoke-check прошёл:

- `entry_based_smoke_check.status = PASS`;
- legacy target columns не требуются;
- проверены `entry_up`, `entry_dn`, `entry_log_ratio` для `H3/H6/H12/H24`;
- rows: `train=44159`, `validation=13296`, `low_n_disclosure=1162`.

Legacy `statistics/data_contract_smoke_check.py` не является stage verdict для этого closeout.

## Feature Contract

Closeout использует тот же representation builder, что и предыдущая абляция, но с отдельным runner-ом и отдельными артефактами.

Входные признаки:

- structure fields;
- shift/age и ATR-координаты;
- price/distance относительно `fractal0.price`, scaled by row `ATR`;
- serialized `Up/Dn` horizons `3/6/12/24/48` внутри фрактального snapshot;
- row time context через `row_hour_sin/cos`, `row_dow_sin/cos`.

Запрещённые top-level target/label поля не входят в feature matrix. Старый runner по умолчанию сохраняет прежний контракт `3/6/12`; полный `3/6/12/24/48` включается только новым closeout runner-ом.

## Scale Audit And Normalization Contract

`normalization_mode = none_tree_raw`: модели получают raw numeric feature matrix, но scale audit обязателен.

Input normalization groups и target groups разделены. Target columns запрещены во входных normalization pools.

Scale audit:

- overall status: `WARNING`;
- `all100`: `WARNING`, 716 flags;
- `corridor_5atr`: `WARNING`, 1441 flags;
- `nearest_k20`: `WARNING`, 90 flags;
- `nearest_k60`: `WARNING`, 210 flags;
- `nearest_k80`: `WARNING`, 270 flags.

Dominance checks не стали блокером, но большое число near-constant flags по широким профилям снижает силу интерпретации.

## Split Policy

Новый методический split:

| Role | Source | Calendar | Selection use |
|---|---|---|---|
| `train` | `train_core` | `<=2020` | fit model |
| `validation` | `val_stop + diagnostic_holdout` | `2021-2025` | selection/evaluation |
| `locked_test` | none | not opened | forbidden |
| `low_n_disclosure` | `low_n_disclosure` | `2026` | forbidden |

Validation roles были разделены внутри validation:

- `val_select`: 6648 rows;
- `val_eval`: 6648 rows.

`validation_roles_combined = false`.

## Best Directional Results

Лучший `val_select` directional score:

| Profile | Model | Horizon | `val_select` Spearman | `val_eval` Spearman |
|---|---|---:|---:|---:|
| `all100` | `xgboost_depth3` | `H24` | `0.0533` | `0.0335` |
| `all100` | `xgboost_depth5` | `H24` | `0.0438` | not selected |
| `nearest_k60` | `xgboost_depth5` | `H12` | `0.0373` | not selected |

Main directional gate `0.10` не пройден. Даже лучший score остаётся слабым.

## Direction Versus Amplitude

Amplitude trace заметно сильнее direction trace:

| Profile | Model | Target | Horizon | `val_select` Spearman | `val_eval` Spearman |
|---|---|---|---:|---:|---:|
| `nearest_k80` | `hist_gradient_boosting` | `entry_up` | `H3` | `0.3414` | `0.4449` |
| `nearest_k60` | `hist_gradient_boosting` | `entry_up` | `H3` | `0.3410` | not selected |
| `nearest_k60` | `xgboost_depth5` | `entry_up` | `H3` | `0.3398` | not selected |

Это главный содержательный результат closeout: направление слабое, но будущая амплитуда движения ранжируется устойчивее.

## Simple Trading Diagnostic

Лучший gross `simple_trade` на `val_select`:

| Profile | Model | Horizon | Trades | Long | Short | Select mean | Eval mean | Select win rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `all100` | `xgboost_depth3` | `H24` | 6648 | 3303 | 3345 | `0.0833` | `0.0129` | `0.5269` |
| `all100` | `xgboost_depth5` | `H12` | 6648 | 2665 | 3983 | `0.0614` | `-0.0079` | `0.5162` |
| `all100` | `xgboost_depth5` | `H24` | 6648 | 3293 | 3355 | `0.0565` | `0.0248` | `0.5215` |

Это gross diagnostic без spread, commission, slippage, position limits и executable MT4 simulator. Его нельзя читать как trading candidate.

## Validation Role Check

Роли validation разведены, но `CONTINUE` всё равно невозможен:

- direction gate не пройден: `0.0533 < 0.10`;
- amplitude survives: `0.3414` на select и `0.4449` на eval;
- simple trade diagnostic местами положительный, но он не заменяет направленный gate.

Итоговое решение runner-а: `PIVOT`.

## 2026 Low-N Disclosure

2026 использовался только как low-N disclosure и не участвовал в выборе.

Лучшие directional disclosure строки:

| Profile | Model | Horizon | Spearman |
|---|---|---:|---:|
| `all100` | `hist_gradient_boosting` | `H24` | `0.1229` |
| `nearest_k20` | `ridge` | `H3` | `0.0899` |
| `nearest_k60` | `hist_gradient_boosting` | `H6` | `0.0799` |

Так как 2026 selection-forbidden и имеет только 1162 строки, эти числа не меняют verdict.

## Verdict: PIVOT

`CONTINUE` не разрешён: лучший directional validation score ниже `0.10`.

`STOP` тоже не лучший вывод: amplitude trace заметно сильнее и проходит заданный amplitude gate.

Вердикт closeout: `PIVOT`.

Следующая постановка не должна продолжать спрашивать "up or down" для текущей `entry-based next open` mechanics. Если линия продолжается, цель нужно менять на movement regime / amplitude / range potential.

## Limitations

- Этап остаётся `DIAGNOSTIC_ONLY`; `locked_test` не открыт.
- Нет `EURUSD` и любой другой cross-pair validation по плану.
- Simple trading diagnostic gross-only, без costs и без MT4 execution.
- Ridge выдавал `LinAlgWarning: Ill-conditioned matrix`; ridge-строки только диагностический линейный контроль.
- Scale audit и distribution audit имеют `WARNING`, поэтому сильный вывод о конкретном profile winner запрещён.
- `next open` всё ещё означает следующий доступный OHLC open, а не доказанную live-executable цену с учётом watcher/inference/order-send latency.

## Next Step

Закрыть текущую направленную ветку `entry-based next open` как непрошедшую directional gate.

Разрешённый следующий шаг: отдельный bounded plan для amplitude / movement-regime target, заранее задающий:

- target family без `entry_log_ratio` как главного вопроса;
- split policy и validation roles до запуска;
- простые gates по амплитуде и достаточному N;
- запрет использовать 2026 для выбора;
- отдельный locked-test план только после freeze.

## Related Materials

- [JSON artifact](../../ML/reports/entry_based_next_open_closeout.json)
- [Metrics CSV](../../ML/reports/entry_based_next_open_closeout_metrics.csv)
- [Rows CSV](../../ML/reports/entry_based_next_open_closeout_rows.csv)
- [Scale audit CSV](../../ML/reports/entry_based_next_open_closeout_scale_audit.csv)
- [Runner](../../ML/baseline/benchmark_entry_based_next_open_closeout.py)
- [Tests](../../tests/test_entry_based_next_open_closeout.py)
- [Previous fractal selection report](2026-07-03-fractal-selection-ablation-entry-based-target.md)
