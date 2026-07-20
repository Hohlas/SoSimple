# benchmark_entry_based_sequence_transformer.py

## Назначение

`ML/baseline/benchmark_entry_based_sequence_transformer.py` проверяет, спасает ли ordered sequence-представление `fractal0..fractal99` ветку `entry-based next open`.

Этап остаётся `DIAGNOSTIC_ONLY`: runner не открывает `locked_test`, не создаёт live-кандидата и не проверяет другие торговые инструменты.

## Scope

Representations:

- `all100_sequence` как control baseline;
- `nearest_k80_sequence`;
- `nearest_k60_sequence`.

Модели:

- `transformer_small`;
- `transformer_medium`;
- `sequence_flat_hist_gradient_boosting`.

Горизонты: `H3`, `H6`, `H12`, `H24`.

Предсказываемые target families:

- `entry_log_ratio`;
- `entry_up`;
- `entry_dn`.

`simple_trade_H` считается как derived gross diagnostic по знаку `pred_entry_log_ratio_H`.

## Входной контракт

Runner строит тензор:

```text
X.shape = [n_rows, 100, 29]
mask.shape = [n_rows, 100]
```

Порядок последовательности:

- token `0` = `fractal0`, самый свежий уровень;
- token `99` = `fractal99`, самый старый уровень.

`fractal0` `Up/Dn` принудительно занулены. `fractal1..fractal99` `Up/Dn` допускаются как сериализованное состояние MT4 producer, доступное в текущей строке.

## Контракт честности

- `all100_sequence` участвует в overall ranking, но excluded из candidate-only verdict.
- `low_n_disclosure=2026` только disclosure, не selection.
- `locked_test` не открывается.
- `entry_based_smoke_check.status` должен быть `PASS`.
- `split_horizon_overlap_check.status` должен быть `PASS`.
- `tensor_audit.status=WARNING` допустим только при наличии `audit_decisions`.
- Input scaler fit-ится только на valid train tokens.
- Target scaler fit-ится только на train targets.
- `val_select` выбирает winner; `val_eval` только проверяет выбранную строку.
- `FREEZE_PROPOSAL_ONLY`, `CANDIDATE`, `FROZEN`, `READY_FOR_LOCKED_TEST` запрещены.

## Запуск

Чистый запуск:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_sequence_transformer.py \
  --entry-based-sequence-transformer --no-resume --device auto --threads 24
```

Resume:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_sequence_transformer.py \
  --entry-based-sequence-transformer --resume --device auto --threads 24
```

`--resume` проверяет `run_config_hash` и отказывается продолжать JSON с несовместимым scope.

## Артефакты

- `ML/reports/entry_based_sequence_transformer.json`
- `ML/reports/entry_based_sequence_transformer_metrics.csv`
- `ML/reports/entry_based_sequence_transformer_rows.csv`
- `ML/reports/entry_based_sequence_transformer_tensor_audit.csv`
- `ML/reports/entry_based_sequence_transformer_run.log`

JSON содержит верхнеуровневые машинные поля:

- `schema_version`;
- `verdict`;
- `dependency_versions`;
- `selection_policy`;
- `training_policy`;
- `normalization_contract`;
- `target_normalization_contract`;
- `run_config_hash`.

## Тесты

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py -q
```

Фокусированные тесты проверяют scope, job matrix, feature contract, зануление `fractal0` `Up/Dn`, forbidden target columns, split policy, normalization contract, resume hash, output isolation, yearly metrics, low-N disclosure exclusion и запрет freeze-like verdict.
