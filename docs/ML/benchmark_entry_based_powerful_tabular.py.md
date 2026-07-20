# benchmark_entry_based_powerful_tabular.py

## Назначение

`ML/baseline/benchmark_entry_based_powerful_tabular.py` проверяет, спасает ли рост мощности табличных моделей ветку `entry-based next open`.

Этап остаётся `DIAGNOSTIC_ONLY`: runner не открывает `locked_test`, не создаёт live-кандидата и не проверяет другие инструменты.

## Scope

Профили:

- `all100` как control baseline;
- `corridor_5atr`;
- `nearest_k60`;
- `nearest_k80`.

Модели:

- XGBoost depth 3/5/7/9;
- LightGBM depth7 и leaves63;
- CatBoost depth6/depth8;
- ExtraTrees;
- HistGradientBoosting.

Горизонты: `H3`, `H6`, `H12`, `H24`.

Предсказываемые target families:

- `entry_log_ratio_H`;
- `entry_up_H`;
- `entry_dn_H`.

`simple_trade_H` считается как derived gross diagnostic по знаку `pred_entry_log_ratio_H`.

## Контракт честности

- `all100` участвует в обучении и overall ranking, но excluded из candidate-only verdict.
- `low_n_disclosure=2026` только disclosure, не selection.
- `split_horizon_overlap_check` должен быть `PASS`.
- `entry_based_smoke_check.status` должен быть `PASS`.
- `scale_audit.status=WARNING` допустим только при наличии `audit_decisions`.
- `normalization_contract.fit_split = train`; validation/disclosure не fit-ят scaler.
- `FREEZE_PROPOSAL_ONLY`, `CANDIDATE`, `FROZEN`, `READY_FOR_LOCKED_TEST` запрещены.

## Запуск

Чистый запуск:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_powerful_tabular.py \
  --entry-based-powerful-tabular --no-resume
```

Resume:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_powerful_tabular.py \
  --entry-based-powerful-tabular --resume
```

`--resume` проверяет `run_config_hash` и отказывается продолжать JSON с несовместимым scope.

## Артефакты

- `ML/reports/entry_based_powerful_tabular.json`
- `ML/reports/entry_based_powerful_tabular_metrics.csv`
- `ML/reports/entry_based_powerful_tabular_rows.csv`
- `ML/reports/entry_based_powerful_tabular_scale_audit.csv`

JSON содержит верхнеуровневые машинные поля:

- `schema_version`;
- `verdict`;
- `dependency_versions`;
- `normalization_contract`;
- `run_config_hash`.

Полные детали остаются в `summary`, `run_config` и `runs[].normalization_contract`.

## Тесты

```bash
./.venv/bin/python -m pytest tests/test_entry_based_powerful_tabular.py -q
```

Фокусированные тесты проверяют scope, model factory, `all100` control separation, forbidden target columns, split-overlap guard, audit decisions, normalization contract, run metadata, yearly metrics и запрет freeze-like verdict.
