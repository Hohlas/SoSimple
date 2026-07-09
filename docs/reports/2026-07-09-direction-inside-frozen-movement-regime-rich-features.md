# Direction Inside Frozen Movement Regime Rich Features

> **Дата**: 2026-07-09
> **Статус**: Completed
> **Вердикт**: FAIL
> **Цель**: Проверить direction внутри frozen movement-mask с обучением на полном `train` и богатыми признаками.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-08-direction-inside-frozen-mask-rich-features.md`, `docs/superpowers/specs/2026-07-08-direction-inside-frozen-mask-rich-features-design.md`

## Context

Старый direction-inside-mask runner был слабой проверкой: он использовал бедные
признаки и обучал модель только на строках внутри frozen-mask. Новый план
требовал честную постановку: обучать на полном `train`, использовать богатые
feature-профили из предыдущих исследований, а winner выбирать только на
`val_select_inside_mask`.

Frozen movement rule не менялся:

```text
simple_combined / extra_trees_small / H3 / top_fraction=0.05 / seeds=[42,43,44]
```

## Уровень этапа

Проверочный этап частично состоялся. Runner теперь подключён к реальным
split/freeze артефактам и пишет непустые metrics/rows. Однако полный плановый
grid `5 x 4 x 3 x 4 = 240` run не запускался; выполнен ограниченный smoke
`simple_combined / H3 / entry_log_ratio / extra_trees`.

## What Was Done

- Создан runner `benchmark_direction_inside_frozen_movement_regime_rich_features.py`.
- Добавлен строгий join frozen-mask по `split + split_row_id`.
- Зафиксировано, что обучение должно идти на полном `train`.
- Добавлены rich feature profiles: `simple_combined`, `nearest_k60`,
  `nearest_k80`, `corridor_5atr`, `all100`.
- Добавлены target families: `entry_log_ratio`, `entry_up_dn_delta`,
  `entry_up_dn_classifier`.
- Добавлены sample-size gate, full/frozen evaluation helpers, model keys,
  selection helper, verdict helper и CLI artifact writer.
- Исправлен end-to-end CLI path: реальные split-ы и freeze scores теперь
  загружаются, общий `validation` split исключается из mask join, потому что
  scores содержат `val_select`/`val_eval`.

## Multiple Testing Context

Плановый search width: `5 feature profiles x 4 horizons x 3 target families x 4 model keys`.
Плановый максимум: `240` комбинаций до учёта baseline-сравнений.

Фактический run после исправления содержит `cumulative_search_budget = 1`.
Это доказывает, что runner больше не пустой scaffold, но не заменяет полный
rich-features grid. Результат smoke можно читать только как контроль старого
простого профиля, а не как закрытие всей rich-features гипотезы.

## Changed Files

- `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- `tests/test_direction_inside_frozen_movement_regime_rich_features.py`
- `docs/ML/benchmark_direction_inside_frozen_movement_regime_rich_features.py.md`
- `docs/reports/2026-07-09-direction-inside-frozen-movement-regime-rich-features.md`

## Verification

Focused tests:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py -q
```

Result: `21 passed`.

Canonical smoke CLI:

```bash
MPLCONFIGDIR=/tmp/matplotlib \
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  --profiles simple_combined \
  --horizons 3 \
  --target-families entry_log_ratio \
  --model-keys extra_trees
```

Result: `verdict = REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME`.

Full suite was started with:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Result after runner fix: `1246 passed, 30 warnings in 279.17s`.

## Results

Structured artifact after runner fix:

- `verdict = REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME`;
- `contract_status = PASS`;
- `training_scope = full_train`;
- `frozen_mask_usage = evaluation_only`;
- `selection_metric = val_select_inside_mask`;
- `locked_test = not_opened`;
- `train_rows = 44159`;
- frozen-mask rows: `train=2208`, `val_select=333`, `val_eval=333`,
  `low_n_disclosure=59`;
- `cumulative_search_budget = 1`.

Smoke metrics:

- `val_select_inside_mask`: balanced accuracy `0.528851`, `n=333`, gate `PASS`;
- `val_eval_inside_mask`: balanced accuracy `0.472188`, `n=333`, gate `PASS`;
- `low_n_disclosure_inside_mask`: balanced accuracy `0.412069`, `n=59`, gate `FAIL`.

CSV artifacts are non-empty:

- metrics CSV: `7` lines including header;
- rows CSV: `14457` lines including header.

## Conclusions

Direction inside frozen movement-mask was re-tested only for the old simple
control profile. That smoke rejects the simple control again and confirms the
runner can produce real metrics. It does not test the full rich-features
hypothesis.

The old weak direction result is not overturned. The rich-features branch still
needs a full grid run before making any broader claim.

## Limitations / Open Questions

- Full `240`-run grid was not executed.
- Yearly masked metrics are still not implemented.
- Only one smoke configuration was run.
- No model card is allowed because there is no candidate.

## Split Disclosure

Planned split roles:

- `train`: full train rows for fit;
- `val_stop`: not used, because early stopping is forbidden;
- `val_select`: selection only inside frozen-mask;
- `val_eval`: confirmation only inside frozen-mask;
- `low_n_disclosure`: disclosure-only;
- `locked_test`: not opened.

Actual smoke used real split materialization and real freeze scores. Full grid
run remains pending.

## Next Step

Run the full planned grid if this branch remains important. Otherwise, treat
the fixed runner as available infrastructure and return to `fractal0_price`
entry mechanics. Do not tune direction on `val_eval`, do not open `locked_test`,
and do not make trading/PnL/PF claims from the smoke result.

## Related Materials

- `docs/superpowers/specs/2026-07-08-direction-inside-frozen-mask-rich-features-design.md`
- `docs/superpowers/plans/2026-07-08-direction-inside-frozen-mask-rich-features.md`
- `docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md`
- `ML/reports/direction_inside_frozen_movement_regime_rich_features.json`
