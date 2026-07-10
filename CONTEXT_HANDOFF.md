# Context Handoff

**Дата:** 2026-07-10

## Текущее состояние

Direction внутри frozen movement-mask закрыт как ближайшая исследовательская
ветка. Узкая seed-stability репликация заранее зафиксированной семьи
`nearest_k60 / extra_trees / entry_log_ratio` завершилась
`REJECT_DIRECTION_REPLICATION`.

Текущая линия:

- amplitude audit: `DIAGNOSTIC_ONLY / AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES`;
- movement-filter design: `SIMPLE_MOVEMENT_FILTER_RESEARCH_ONLY`;
- movement-filter freeze: `FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN`;
- old direction inside frozen movement: `REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME`;
- rich direction full grid: `DIAGNOSTIC_ONLY / DIRECTION_REPLICATION_REQUIRED`;
- narrow direction replication: `FAIL / REJECT_DIRECTION_REPLICATION`.

## Главный вывод

H3 weak direction-effect из full-grid не воспроизвёлся по seed stability:

- matrix: `nearest_k60 / extra_trees / entry_log_ratio`;
- planned horizons: `H3`, `H6`, `H9`;
- executed horizons: `H3`, `H6`;
- H9: `SKIPPED_MISSING_TARGET_COLUMNS`;
- seeds: `41`, `42`, `43`, `44`, `45`;
- progress: `10/10`, `failed_runs=0`, `contract_status=PASS`;
- H3 median `val_eval_inside_mask balanced_accuracy = 0.499080`;
- H3 seeds `val_eval_inside_mask >= 0.52`: `2/5`;
- H3 same positive sign on `val_select` and `val_eval`: `1/5`;
- H6 median `val_eval_inside_mask balanced_accuracy = 0.528590`, but H6 was
  secondary robustness and cannot replace failed H3.

Итог: direction-inside-frozen-mask не является near-term branch. Это не trading
signal и не candidate.

## Главные артефакты

- `docs/reports/2026-07-10-direction-inside-frozen-mask-narrow-replication.md`
- `ML/reports/direction_inside_frozen_movement_regime_narrow_replication.json`
- `ML/reports/direction_inside_frozen_movement_regime_narrow_replication_metrics.csv`
- `ML/reports/direction_inside_frozen_movement_regime_narrow_replication_rows.csv`
- `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- `tests/test_direction_inside_frozen_movement_regime_rich_features.py`
- `docs/ML/benchmark_direction_inside_frozen_movement_regime_rich_features.py.md`
- `docs/superpowers/roadmap.md`

## Runner Status

Rich-features runner теперь поддерживает:

- обычный full-grid режим без H9;
- `--replication-mode narrow`;
- narrow default horizons `H3/H6/H9`;
- `--replication-seeds`;
- H9 target preflight;
- `replication_summary`, `replication_verdict`, `time_diagnostics`;
- search-budget disclosure для narrow replication;
- default `--resume`, progress JSON и heartbeat.

Тесты:

- focused: `44 passed`;
- full suite: `1272 passed`;
- smoke narrow: `contract_status=PASS`, `progress=1/1`;
- full narrow run: `contract_status=PASS`, `progress=10/10`.

## Exact Frozen Rule

Frozen movement rule не менялся:

- `simple_combined / extra_trees_small / H3 / top_fraction=0.05`
- `score_aggregation = median_across_rerun_seeds`
- `seeds = [42, 43, 44]`
- `rule_hash = 56361f12104b55c4cac6bd04426349f71d8944c139563a8c9b68d3b25e97deaf`

## Следующий Шаг

Следующим агентом сначала читать:

- `docs/reports/2026-07-10-direction-inside-frozen-mask-narrow-replication.md`
- `docs/superpowers/roadmap.md`
- `docs/reports/2026-07-09-direction-inside-frozen-movement-regime-rich-features.md`
- `docs/reports/2026-07-02-regression-updn-already-moved-audit.md`
- `docs/reports/2026-07-02-next-open-entry-updn-foundation.md`

Практический следующий шаг: отдельный план для execution-aware механики входа
от `fractal0_price`: exact `decision_time`, entry eligibility, first executable
price, oracle-preflight и новые targets от фактической точки входа.

## Запрещённые Направления

- Не продолжать wide direction search внутри frozen movement-mask без новой
  заранее обоснованной гипотезы.
- Не продвигать H6 post-hoc как replacement primary horizon.
- Не тюнить по `val_eval` или `low_n_disclosure`.
- Не менять frozen movement-mask в рамках закрытой ветки.
- Не добавлять PnL/PF, BUY/SELL или trading claims к этому результату.
- Не открывать `locked_test`.
