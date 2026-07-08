# benchmark_direction_inside_frozen_movement_regime.py

`ML/baseline/benchmark_direction_inside_frozen_movement_regime.py` проверяет direction target только внутри заранее замороженной movement-mask.

## Purpose

Runner отвечает на узкий вопрос: можно ли честно построить direction baseline внутри frozen movement regime, не меняя сам movement filter.

Текущий canonical result: `REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME`.
После repair frozen score export использует `split + split_row_id` как join key.
`split + time` остаётся неуникальным и используется только как диагностическое поле.

## Inputs

- `ML/reports/entry_based_movement_filter_freeze.json`
- `ML/reports/entry_based_movement_filter_freeze_scores.csv`
- split-ы из `ML.baseline.benchmark_entry_based_amplitude_movement.load_entry_based_splits()`

Frozen rule must remain:

```text
simple_combined / extra_trees_small / H3 / top_fraction=0.05 / seeds=[42,43,44]
```

## Outputs

- `ML/reports/direction_inside_frozen_movement_regime.json`
- `ML/reports/direction_inside_frozen_movement_regime_rows.csv`

On contract fail, rows CSV is empty but keeps canonical columns:

```text
split,time,target_direction_3,target_is_tie_3,target_up_3,target_dn_3
```

В canonical run после repair rows CSV содержит выбранные строки frozen movement
mask после удаления direction ties.

## Target Convention

For horizon `3`:

- `target_direction_3 = 1` when `entry_up_3 > entry_dn_3`;
- `target_direction_3 = -1` when `entry_dn_3 > entry_up_3`;
- ties and missing target rows are excluded from supervised rows.

## Forbidden Input Columns

These columns must not enter direction feature matrices:

- `score`
- `entry_movement_3`
- `entry_up_3`
- `entry_dn_3`
- `target_direction_3`
- `target_is_tie_3`
- `target_up_3`
- `target_dn_3`
- `label_direction_3`

## CLI

```bash
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime.py \
  --freeze-report ML/reports/entry_based_movement_filter_freeze.json \
  --freeze-scores ML/reports/entry_based_movement_filter_freeze_scores.csv \
  --output-prefix ML/reports/direction_inside_frozen_movement_regime
```

## Tests

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime.py -q
```

Coverage:

- frozen rule and `locked_test` guards;
- `selected` format contract;
- unique `split + split_row_id` join contract;
- legacy `split + time` duplicate guard when `split_row_id` is absent;
- direction target and tie exclusion;
- leakage guard for forbidden columns;
- classification-only metrics;
- val-select-only winner selection;
- robustness gate prevents premature frozen verdict;
- CLI smoke and artifact writing.

## Limitations

- `split + time` is not unique because one bar may produce multiple entry rows.
- Current canonical run trains direction baselines but rejects the direction signal.
- No PnL/PF, spread, stop-loss, take-profit, BUY/SELL or trading-candidate claim is produced.
- `locked_test` remains closed.
