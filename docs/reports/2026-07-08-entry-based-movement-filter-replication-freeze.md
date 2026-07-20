# Entry-Based Movement Filter Replication Freeze

> **Дата**: 2026-07-08
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Research freeze verdict**: FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN
> **Цель**: Реплицировать и заморозить ровно один заранее выбранный entry-based movement filter без расширения search space, без direction, без PnL/PF и без открытия `locked_test`.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-08-entry-based-movement-filter-replication-freeze.md`

## Context

Предыдущий этап уже сузил amplitude / movement-regime ветку до одного допустимого research-only правила:

- `profile = simple_combined`
- `model_key = extra_trees_small`
- `horizon = 3`
- `target_family = entry_movement`
- `threshold_type = top_fraction`
- `selected_fraction = 0.05`
- `score_aggregation = median_across_rerun_seeds`
- `seeds = [42, 43, 44]`

Task 6 требовал зафиксировать итог этого узкого replication/freeze шага в каноническом отчёте, docs, wiki и handoff без изменения structured CSV/JSON результатов.

## Research Level

Уровень этапа: `RESEARCH_ONLY`.

Причина: здесь не было нового wide search, но и не было независимого подтверждения через `locked_test`. Этап честно замораживает research segmentation rule для следующего отдельного плана. Он не повышает результат до direction-кандидата, не даёт торгового статуса и не разрешает открывать `locked_test`.

## What Was Done

1. Сверен structured artifact `ML/reports/entry_based_movement_filter_freeze.json` и связанные CSV.
2. Написан канонический stage report с exact frozen rule, hash-ами, gate-таблицами и явными запретами на интерпретацию.
3. Создана module doc для `ML/baseline/benchmark_entry_based_movement_filter_freeze.py`.
4. Обновлены `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `MODULE_INDEX.md`, `docs/tests/tests.md`, `docs/superpowers/roadmap.md`.
5. Обновлены `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`; после этого запущен `wiki status -> generate -> status`.
6. Выполнена focused verification freeze-тестов.

## Multiple Testing Context

Source lineage для текущего freeze-артефакта:

- amplitude search: `356` completed metric runs, `0` failed runs, `132` seed aggregate rows;
- bounded movement-filter search: `32` planned candidates, `32` evaluated candidates, `8` rerun score families;
- freeze rerun: `candidate_search_performed=false`, `score_families_rerun=1`, `selected_rule_only=true`.

Текущий этап не выбирал новый winner. Он только реплицировал уже выбранное правило из `ML/reports/entry_based_movement_filter.json` и проверил, что:

- source hash совпадает;
- frozen rule совпадает побайтно по stable JSON hash;
- `locked_test` остался `not_opened`;
- `2026` остаётся только disclosure.

Следствие: корректный статус этого шага не может быть выше research freeze для следующего плана. Это не independent replication и не новое основание для торговых выводов.

## Changed Files

- `docs/reports/2026-07-08-entry-based-movement-filter-replication-freeze.md`
- `docs/ML/benchmark_entry_based_movement_filter_freeze.py.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `MODULE_INDEX.md`
- `docs/tests/tests.md`
- `docs/superpowers/roadmap.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`
- `.superpowers/sdd/task-6-report.md`

## Verification

- `./.venv/bin/python -m pytest tests/test_entry_based_movement_filter_freeze.py -q` -> `21 passed in 1.90s`
- `./.venv/bin/python wiki/wiki.py status` -> до `generate` показал `24 items need attention`
- `./.venv/bin/python wiki/wiki.py generate` -> `Generated wiki/REPO_integrity.md — 3044 files tracked.`
- `./.venv/bin/python wiki/wiki.py status` -> `Wiki is up to date. No gaps found.`

## Results

### Frozen rule and hashes

Frozen rule:

```json
{"profile":"simple_combined","model_key":"extra_trees_small","horizon":3,"target_family":"entry_movement","threshold_type":"top_fraction","selected_fraction":0.05,"score_aggregation":"median_across_rerun_seeds","seeds":[42,43,44]}
```

- `rule_hash`: `56361f12104b55c4cac6bd04426349f71d8944c139563a8c9b68d3b25e97deaf`
- `frozen_config_hash`: `ee2701d0566e910e8a0fb10c6d4f5a8916d2b4e5b903e9dc50f39354344e86b6`
- `source_movement_filter_hash`: `b72f088c31e9327fdc5f089ef59da0dafeebe6a4641b7a3571b82461e8e3f6cd`
- `source_amplitude_hash`: `b79c7cc61cd72de08ca54953fa811edad4932253584a1183833971092e8ea5d9`

Frozen config contract:

- estimator class: `ExtraTreesRegressor`
- `model_key = extra_trees_small`
- seeds: `42, 43, 44`
- threads: `n_jobs = 24`
- target contract: `entry_movement_H = max(entry_up_H, entry_dn_H)`
- split contract: `train <= 2020`, `validation = 2021-2025`, `low_n_disclosure = 2026`, `locked_test = not_opened`, `embargo_hours = 24`

Generated artifact hashes:

| Artifact | SHA-256 |
|---|---|
| `ML/reports/entry_based_movement_filter_freeze.json` | `9f3133cc1994428d28245c2a7cbb4d34d006633c93adddff9265e22cd07f6668` |
| `ML/reports/entry_based_movement_filter_freeze_yearly.csv` | `82d55f819d19964f0a4529ba716a8ba4d04de7d52fbe75a018d5f61f6cd6c24a` |
| `ML/reports/entry_based_movement_filter_freeze_selected_rows.csv` | `1fc0b5015247f9253ba8553f20bb6341f7f63137f069a1d4ec1809b997dcee54` |
| `ML/reports/entry_based_movement_filter_freeze_scores.csv` | `5d55be1e950c83dcda88f02050046f8b372185a1f162d0f695579935f9737af8` |
| `ML/reports/entry_based_movement_filter_freeze_random_baseline.csv` | `b5a9d1e9f17d3adfab106d154027f147ec6d21ded97805cffa3c6f8f5a7c1501` |
| `ML/reports/entry_based_movement_filter_freeze_score_cutoffs.csv` | `a4f04aec3eb621ecbe5d8699b998ccd305d6a92a53ef619d468f2d20e8420f43` |

### Gate table

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| source hash match | exact match | PASS | PASS |
| frozen rule match | exact match | PASS | PASS |
| `locked_test` | `not_opened` | `not_opened` | PASS |
| `val_select.selected_n` | `>= 300` | `333` | PASS |
| `val_select.movement_lift` | `>= 1.80` | `2.1528` | PASS |
| `val_select.selected_p80 > skipped_p80` | strict | `17.576 > 8.220` | PASS |
| `val_eval.selected_n` | `>= 300` | `333` | PASS |
| `val_eval.movement_lift` | `>= 1.50` | `2.4806` | PASS |
| `val_eval.selected_p80 > skipped_p80` | strict | `35.634 > 14.456` | PASS |
| `val_eval.yearly_lift_pass_rate` | `>= 0.80` | `1.00` | PASS |
| yearly `selected_n` | `>= 50` for each year | `62 / 137 / 135` | PASS |
| disclosure years | exactly `[2026]` | `[2026]` | PASS |

### Validation metrics

| Split | Selected N | Skipped N | Mean movement selected | Mean movement skipped | Movement lift | Spearman |
|---|---:|---:|---:|---:|---:|---:|
| `val_select` | 333 | 6315 | 12.9791 | 6.0290 | 2.1528 | 0.5734 |
| `val_eval` | 333 | 6313 | 25.6609 | 10.3447 | 2.4806 | 0.6945 |
| `low_n_disclosure` | 59 | 1103 | 62.4305 | 38.3186 | 1.6292 | 0.1609 |

### Random baseline table

| Scope | Selected N | Total N | p05 lift | p50 lift | p95 lift |
|---|---:|---:|---:|---:|---:|
| global `val_eval` | 333 | 6646 | 0.9213 | 1.0030 | 1.0910 |
| year 2023 | 62 | 1236 | 0.8230 | 0.9694 | 1.2263 |
| year 2024 | 137 | 2723 | 0.8911 | 0.9974 | 1.1089 |
| year 2025 | 135 | 2687 | 0.8874 | 0.9960 | 1.1146 |

Наблюдаемый `val_eval movement_lift = 2.4806` значительно выше `random_same_size p95 = 1.0910`. То же верно для каждого `val_eval` года.

### Score cutoff diagnostics

By split:

| Split | Score cutoff | Selected N | Total N |
|---|---:|---:|---:|
| `train` | 7.7712 | 2208 | 44159 |
| `val_select` | 9.0154 | 333 | 6648 |
| `val_eval` | 14.3131 | 333 | 6646 |
| `low_n_disclosure` | 15.4764 | 59 | 1162 |

By year:

| Split | Year | Score cutoff | Selected N | Total N |
|---|---:|---:|---:|---:|
| `val_select` | 2021 | 8.5761 | 135 | 2686 |
| `val_select` | 2022 | 9.4883 | 126 | 2519 |
| `val_select` | 2023 | 9.0010 | 73 | 1443 |
| `val_eval` | 2023 | 7.8966 | 62 | 1236 |
| `val_eval` | 2024 | 11.1594 | 137 | 2723 |
| `val_eval` | 2025 | 15.1364 | 135 | 2687 |
| `low_n_disclosure` | 2026 | 15.4764 | 59 | 1162 |

Diagnostic status: `PASS`, warnings: none.

### Top-fraction limitation

`top_fraction = 0.05` означает batch segmentation rule, а не фиксированный исполнимый live cutoff. Практическое следствие:

- в каждом split и году порог score получается разным;
- правило выделяет верхние `5%` строк по rank внутри набора;
- его нельзя честно трактовать как готовое live-правило с одним фиксированным абсолютным cutoff без нового отдельного плана.

### Explicit forbidden interpretations

Ниже перечислено, что этот freeze **не** означает:

- это не direction-модель;
- это не BUY/SELL rule;
- это не PnL/PF результат;
- это не trading candidate;
- это не live rule;
- это не independent replication;
- это не permission to open `locked_test`;
- это не разрешение расширять search space задним числом.

## Conclusions

Task 6 подтвердил, что freeze artifact согласован с source artifacts и что заранее выбранный movement segmentation rule честно воспроизводится без contract failure. Максимально сильная корректная интерпретация результата:

`FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN`

Но уровень доказательности всего этапа остаётся `DIAGNOSTIC_ONLY / RESEARCH_ONLY` в смысле дальнейшей интерпретации проекта: заморожено исследовательское segmentation rule для следующего узкого плана, а не торговое решение.

## Limitations / Open Questions

1. `selected_rows.csv` содержит выбранные строки из `train`, `val_select`, `val_eval` и `low_n_disclosure`; это export для аудита, а не отдельный live export.
2. `top_fraction=0.05` не даёт единого абсолютного score cutoff между годами и split-ами.
3. `2026` остаётся low-N disclosure и не использовался для выбора.
4. Без нового отдельного плана нельзя переходить к direction, PnL/PF или `locked_test`.

## Validation Split Disclosure

Validation contract:

- `train <= 2020` — fit модели и внутренней подготовки признаков;
- `val_select = 2021-2023` — единственный split выбора frozen rule;
- `val_eval = 2023-2025` — проверка уже выбранного правила без замены;
- `low_n_disclosure = 2026` — disclosure only;
- `locked_test = not_opened`.

Sample size disclosure:

| Split | Role | Total N | Selected N | Skipped N |
|---|---|---:|---:|---:|
| `val_select` | select | 6648 | 333 | 6315 |
| `val_eval` | check-only | 6646 | 333 | 6313 |
| `low_n_disclosure` | disclosure-only | 1162 | 59 | 1103 |

`sample_size_gate` фактически пройден на `val_select`, `val_eval` и на каждом `val_eval` yearly slice (`62`, `137`, `135` выбранных строк).

## Next Step

Следующий допустимый шаг: отдельный узкий research plan, который использует уже замороженную movement segmentation mask как входной контракт для новой постановки. Этот следующий план должен оставаться вне PnL/PF и не должен открывать `locked_test`, пока новая постановка не получит собственный frozen contract.

## Related Materials

- `ML/baseline/benchmark_entry_based_movement_filter_freeze.py`
- `tests/test_entry_based_movement_filter_freeze.py`
- `ML/reports/entry_based_movement_filter_freeze.json`
- `ML/reports/entry_based_movement_filter_freeze_yearly.csv`
- `ML/reports/entry_based_movement_filter_freeze_selected_rows.csv`
- `ML/reports/entry_based_movement_filter_freeze_scores.csv`
- `ML/reports/entry_based_movement_filter_freeze_random_baseline.csv`
- `ML/reports/entry_based_movement_filter_freeze_score_cutoffs.csv`
- `ML/reports/entry_based_movement_filter.json`
- `ML/reports/entry_based_amplitude_movement.json`
