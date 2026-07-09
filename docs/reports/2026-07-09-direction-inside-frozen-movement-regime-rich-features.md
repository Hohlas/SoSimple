# Direction Inside Frozen Movement Regime Rich Features

> **Дата**: 2026-07-09
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: Проверить, появляется ли direction-сигнал внутри заранее замороженной movement-mask после исправления обучения на full-train и расширения feature/target/model grid.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-08-direction-inside-frozen-mask-rich-features.md`, `docs/superpowers/specs/2026-07-08-direction-inside-frozen-mask-rich-features-design.md`

## Context

Предыдущий direction-inside-mask runner был отвергнут: он обучал модель только
на строках `frozen_selected=True` и использовал бедные признаки. Этот этап
проверяет более честную постановку:

- frozen movement-mask заранее заморожена и не меняется;
- direction-модель обучается на полном `train`;
- frozen-mask используется только для оценочных срезов;
- winner выбирается только на `val_select` внутри frozen-mask;
- `val_eval` используется только как подтверждение.

Frozen movement rule не менялся:

```text
simple_combined / extra_trees_small / H3 / top_fraction=0.05 / seeds=[42,43,44]
```

## Уровень этапа

Этап проверочный внутри уже замороженной movement-mask, но результат остаётся
`DIAGNOSTIC_ONLY`: найден слабый direction-effect, который требует отдельной
репликации. Это не trading candidate, не live-rule и не разрешение открывать
`locked_test`.

## What Was Done

- Runner подключён к реальным entry-based split-ам и frozen scores.
- Join frozen-mask выполняется по `split + split_row_id`, а не по неуникальному
  `split + time`.
- Обучение direction-моделей идёт на полном `train`; frozen-mask не используется
  для fit.
- Запущен полный grid `5 feature profiles x 4 horizons x 3 target families x 4 model keys = 240`.
- Добавлены `--resume` / `--no-resume`, progress JSON, heartbeat, per-run
  runtime и thread metadata.
- Для `ExtraTrees` и `XGBoost` фактически использованы `24` потока; `HistGradientBoostingClassifier`
  не имеет `n_jobs`, и это раскрыто в JSON как `not_supported_by_estimator`.
- После обнаружения legacy-строк от раннего smoke артефакты были восстановлены
  чистым повторным прогоном; итоговые CSV не содержат пустых `resume_key`.

## Multiple Testing Context

Current search budget:

```text
5 feature profiles x 4 horizons x 3 target families x 4 model keys x 1 seed = 240 runs
```

Фактический JSON содержит `progress.done_runs=240`, `progress.total_runs=240`,
`failed_runs=[]`.

Это широкий диагностический grid. Коррекция за множественный перебор не
применялась, поэтому положительный исход нельзя повышать до candidate-status.
Итоговый verdict `DIRECTION_REPLICATION_REQUIRED` означает: направление внутри
маски найдено как слабый след, но следующий шаг должен быть заранее
зафиксированной репликацией, а не тюнингом по текущему `val_eval`.

## Changed Files

- `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- `tests/test_direction_inside_frozen_movement_regime_rich_features.py`
- `docs/ML/benchmark_direction_inside_frozen_movement_regime_rich_features.py.md`
- `docs/tests/tests.md`
- `MODULE_INDEX.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `docs/reports/2026-07-09-direction-inside-frozen-movement-regime-rich-features.md`

## Verification

Focused tests:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py -q
```

Result after runner/progress/resume fixes: `30 passed`.

Full test suite after implementation:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Result: `1254 passed, 30 warnings`.

Full run command:

```bash
MPLCONFIGDIR=/tmp/matplotlib \
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  --threads 24 \
  --no-resume
```

Final artifact audit:

- metrics CSV: `1440` data rows, exactly `240 runs x 3 splits x 2 slices`;
- rows CSV: `3,469,440` data rows;
- metric keys: `240`;
- row keys: `240`;
- empty `resume_key` rows: `0` in both CSV files.

## Results

Structured artifact:

- `verdict = DIRECTION_REPLICATION_REQUIRED`;
- `contract_status = PASS`;
- `training_scope = full_train`;
- `frozen_mask_usage = evaluation_only`;
- `selection_metric = val_select_inside_mask`;
- `locked_test = not_opened`;
- `progress.done_runs = 240`;
- `progress.total_runs = 240`;
- `elapsed_sec = 4187.815994`;
- `requested_threads = 24`;
- `effective_threads = 24`;
- `failed_runs = 0`;
- `train_rows = 44159`;
- frozen-mask rows: `train=2208`, `val_select=333`, `val_eval=333`, `low_n_disclosure=59`.

Winner by `val_select` inside frozen-mask:

```text
nearest_k60 | H3 | entry_log_ratio | extra_trees
```

Winner metrics:

- `val_select_inside_mask`: balanced accuracy `0.570170`, accuracy `0.576577`, `n=333`, gate `PASS`;
- `val_eval_inside_mask`: balanced accuracy `0.529056`, accuracy `0.528529`, `n=333`, gate `PASS`;
- full `val_select`: balanced accuracy `0.510736`, accuracy `0.510987`, `n=6644`;
- full `val_eval`: balanced accuracy `0.498814`, accuracy `0.495636`, `n=6646`;
- `low_n_disclosure` is disclosure-only; frozen-mask rows `n=59`, sample-size gate is too small for selection.

The top `val_select` frozen-mask result is shared by three target-family
encodings for the same profile/horizon/model because those encodings collapse
to the same active direction labels in this slice:

- `nearest_k60|H3|entry_log_ratio|extra_trees`;
- `nearest_k60|H3|entry_up_dn_delta|extra_trees`;
- `nearest_k60|H3|entry_up_dn_classifier|extra_trees`.

## Conclusions

The previous broad conclusion "direction inside frozen movement-mask is absent"
is softened, but not overturned into a candidate. Rich features found a weak
direction trace inside the frozen movement regime:

- selection split is above random by a visible margin: `0.570170`;
- confirmation split remains only slightly above random: `0.529056`;
- the full-split diagnostic is near random, so the effect is specific to the
  frozen movement-mask slice;
- the result came from a 240-run search, so it needs replication before any
  stronger claim.

The correct interpretation is: `DIRECTION_REPLICATION_REQUIRED`.

## Limitations / Open Questions

- Only one seed is used in this runner (`seed=42`).
- No yearly/block stability check is implemented for this rich runner.
- No correction for the 240-run search was applied.
- `low_n_disclosure` has only `59` frozen-mask rows and is not eligible for
  selection.
- The best `val_eval` result by raw score is not the selected winner; selecting
  by `val_eval` remains forbidden.
- No PnL/PF/trading interpretation is allowed.
- No model card is created because there is no accepted candidate.

## Split Disclosure

Split roles:

- `train`: full train rows for fit;
- `val_stop`: not used; early stopping is not used;
- `val_select`: selection only inside frozen-mask;
- `val_eval`: confirmation only inside frozen-mask;
- `low_n_disclosure`: disclosure-only and low-N;
- `locked_test`: not opened.

Sample-size gates:

- `val_select_inside_mask`: `n=333`, gate `PASS`;
- `val_eval_inside_mask`: `n=333`, gate `PASS`;
- `low_n_disclosure_inside_mask`: `n=59`, gate `FAIL` by low sample size.

`locked_test` and `low_n_disclosure` were not used for selection. `val_eval`
was not used to choose the winner.

## Next Step

Allowed next step: write a narrow replication plan before running more models.
The replication should freeze the successful family of settings first, for
example `nearest_k60 / H3 / extra_trees` with fixed direction target handling,
then test robustness by seed/year/block without opening `locked_test`.

Forbidden next steps:

- do not tune on `val_eval`;
- do not pick the best raw `val_eval` run after the fact;
- do not change the frozen movement-mask in this branch;
- do not add PnL/PF or trading claims;
- do not open `locked_test`;
- do not call this a production signal.

## Related Materials

- `ML/reports/direction_inside_frozen_movement_regime_rich_features.json`
- `ML/reports/direction_inside_frozen_movement_regime_rich_features_metrics.csv`
- `ML/reports/direction_inside_frozen_movement_regime_rich_features_rows.csv`
- `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- `tests/test_direction_inside_frozen_movement_regime_rich_features.py`
- `docs/ML/benchmark_direction_inside_frozen_movement_regime_rich_features.py.md`
- `docs/superpowers/specs/2026-07-08-direction-inside-frozen-mask-rich-features-design.md`
- `docs/superpowers/plans/2026-07-08-direction-inside-frozen-mask-rich-features.md`
- `docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md`
