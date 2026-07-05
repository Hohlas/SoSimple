# benchmark_entry_based_next_open_closeout.py

## Назначение

Closeout runner для ветки `entry-based next open`.

Он проверяет только frozen shortlist профилей после предыдущей абляции и принимает решение `STOP`, `PIVOT` или `CONTINUE` без открытия `locked_test` и без cross-pair validation. `all100` входит только как control baseline и не может дать `CONTINUE`.

## Запуск

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_next_open_closeout.py \
  --entry-based-next-open-closeout \
  --resume
```

Чистый запуск:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_next_open_closeout.py \
  --entry-based-next-open-closeout \
  --no-resume
```

## Входные данные

- split-ы foundation runner-а через `benchmark_entry_based_updn_fractal_selection_ablation.load_entry_based_splits(target_mode="rebuilt")`;
- `fractal0..fractal99`;
- row-level `ATR`;
- `entry_up_*`, `entry_dn_*`, `entry_log_ratio_*` для `H3/H6/H12/H24`.

Если старый loaded split не содержит `H24`, runner пересобирает entry-targets через foundation builder с horizons `(3, 6, 12, 24)`.

## Выходные данные

- `ML/reports/entry_based_next_open_closeout.json`
- `ML/reports/entry_based_next_open_closeout_metrics.csv`
- `ML/reports/entry_based_next_open_closeout_rows.csv`
- `ML/reports/entry_based_next_open_closeout_scale_audit.csv`

## Shortlist Scope

Представления:

- `all100`
- `corridor_5atr`
- `nearest_k20`
- `nearest_k60`
- `nearest_k80`

Модели:

- `xgboost_depth3`
- `xgboost_depth5`
- `hist_gradient_boosting`
- `ridge`

Seed: только `42`.

Горизонты target: `H3/H6/H12/H24`.

## Feature Contract

Runner переиспользует builder старой абляции, но вызывает его с serialized `Up/Dn` horizons `3/6/12/24/48`.

Отдельные добавочные `fractal0_up_*` / `fractal0_dn_*` не создаются: в clean run они были полностью нулевыми. Живые serialized `Up/Dn` берутся из `slot_*_up_*` / `slot_*_dn_*`.

Старый runner сохраняет default `3/6/12`, поэтому исторический результат 2026-07-03 не меняется.

Top-level target/label columns запрещены во входной feature matrix:

- `entry_up_*`
- `entry_dn_*`
- `entry_log_ratio_*`
- `target_*`
- `label_*`
- `outcome_*`
- `ret_*`
- `fav_*`
- `adv_*`

## Почему EURUSD исключён

План closeout проверяет только текущий инструмент и не делает cross-pair validation. Это осознанное ограничение search width: цель этапа — закрыть или перенаправить текущую механику, а не открыть новый robustness cycle.

## Почему locked_test не открыт

Этап использует `train` и large `validation` для research/diagnostic решения. `locked_test` остаётся пустым в `SPLIT_POLICY`.

Runner не создаёт frozen candidate. Даже при `CONTINUE` результат был бы только предложением отдельного locked-test плана.

## Normalization And Scale Audit

`normalization_mode = none_tree_raw`.

Модели получают raw numeric feature matrix, но перед fit выполняется scale audit:

- per-feature stats по `train`, `validation`, `low_n_disclosure`;
- near-constant и missing flags;
- dominance checks по feature groups;
- CSV artifact `entry_based_next_open_closeout_scale_audit.csv`.

Input normalization groups и target normalization groups разделены. Target columns не участвуют во входных normalization pools.

## Verdict Logic

`CONTINUE` требует одновременно:

- directional select score `>= 0.10`;
- directional eval score `>= 0.02`;
- positive simple trade mean на `val_select` и `val_eval`;
- validation roles not combined.
- best directional representation must be candidate, not `all100` control.

`PIVOT` ставится, если direction слабый, но amplitude select score `>= 0.15` и eval score `>= 0.02`.

Иначе runner возвращает `STOP`.

## Ограничения

- Этап `DIAGNOSTIC_ONLY`.
- `simple_trade` gross-only и не заменяет backtest с costs.
- `low_n_disclosure=2026` запрещён для выбора.
- Ridge может выдавать `LinAlgWarning`; эти строки являются sanity-control.
