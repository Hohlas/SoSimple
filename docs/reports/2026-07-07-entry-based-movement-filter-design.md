# Entry-Based Movement Filter

> **Дата**: 2026-07-07
> **Статус**: Completed
> **Вердикт**: SIMPLE_MOVEMENT_FILTER_RESEARCH_ONLY
> **Цель**: Построить bounded CLI для простого фильтра "есть движение / нет движения" поверх `entry_based_amplitude_movement`, без выбора направления, без PnL/PF и без открытия `locked_test`.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-07-entry-based-movement-filter-design.md`

## Context

Task 5 требовал довести `ML/baseline/benchmark_entry_based_movement_filter.py` до рабочего CLI, который:

- читает `ML/reports/entry_based_amplitude_movement.json`;
- выбирает только разрешённые score family: `time_plus_atr` и `simple_combined`;
- ищет порог только на `val_select`;
- проверяет ровно один выбранный фильтр на `val_eval`;
- выводит `2026` только как disclosure;
- не использует direction, PnL, PF и `locked_test`.

Критический риск был в том, что source artifact не содержит готовых row-level predictions. Поэтому runner не имитирует score, а делает точный bounded rerun нужных score family через существующую логику `benchmark_entry_based_amplitude_movement.py`.

## Research Level

Уровень этапа: `RESEARCH_ONLY`.

Причина: гипотеза родилась из предыдущего diagnostic amplitude-audit, а текущий
этап выбирает threshold на `val_select` внутри уже изученной ветки. Поэтому даже
прошедший фильтр не становится trading candidate и не даёт права открывать
`locked_test`. Максимальный корректный вывод этого этапа —
`SIMPLE_MOVEMENT_FILTER_RESEARCH_ONLY`.

## What Was Done

1. Добавлен CLI `--source ... --output-prefix ...`.
2. Добавлен bounded rerun path для разрешённых `(profile, model_key, horizon)` family:
   - загружаются те же split-ы;
   - заново строятся те же movement targets;
   - заново обучаются только нужные модели для выбранной family;
   - row-level score агрегируется как `median_across_rerun_seeds`.
3. Добавлена запись артефактов:
   - `ML/reports/entry_based_movement_filter.json`
   - `ML/reports/entry_based_movement_filter_candidates.csv`
   - `ML/reports/entry_based_movement_filter_yearly.csv`
   - `ML/reports/entry_based_movement_filter_selected_rows.csv`
4. Добавлен smoke test CLI на fixture artifact.
5. Запущен реальный CLI на `ML/reports/entry_based_amplitude_movement.json`.

## Multiple Testing Context

Source amplitude-аудит был wide diagnostic search. В source artifact нет явного
поля `cumulative_search_budget`, поэтому новый JSON фиксирует производный
`source_search_budget`:

- completed metric runs в source artifact: `356`;
- failed metric runs: `0`;
- seed aggregate rows: `132`;
- simple profile seed aggregates: `24`.

Новый movement-filter search был заранее ограничен:

- profiles: `time_plus_atr`, `simple_combined`;
- horizons: `H3`, `H6`, `H12`, `H24`;
- threshold family: только `top_fraction`;
- fractions: `0.05`, `0.10`, `0.20`, `0.30`;
- planned/evaluated threshold candidates: `32`;
- rerun score families: `8`.

Коррекция множественного перебора не превращает результат в кандидата:
статус остаётся `RESEARCH_ONLY`. `val_eval` использован только как проверка
одного фильтра, выбранного на `val_select`; второй winner после просмотра
`val_eval` не выбирался.

## Changed Files

- `ML/baseline/benchmark_entry_based_movement_filter.py`
- `tests/test_entry_based_movement_filter.py`
- `ML/reports/entry_based_movement_filter.json`
- `ML/reports/entry_based_movement_filter_candidates.csv`
- `ML/reports/entry_based_movement_filter_yearly.csv`
- `ML/reports/entry_based_movement_filter_selected_rows.csv`
- `docs/reports/2026-07-07-entry-based-movement-filter-design.md`

## Verification

- `./.venv/bin/python -m pytest tests/test_entry_based_movement_filter.py -q` → `16 passed`
- `./.venv/bin/python -m pytest tests/ -q` → `1180 passed, 30 warnings`
- `./.venv/bin/python ML/baseline/benchmark_entry_based_movement_filter.py --source ML/reports/entry_based_amplitude_movement.json --output-prefix ML/reports/entry_based_movement_filter` → exit `0`
- `graphify update .` → completed, graph updated

## Results

Source artifact hash:

`b79c7cc61cd72de08ca54953fa811edad4932253584a1183833971092e8ea5d9`

Этот hash записан в поле `source_artifact_hash` файла `ML/reports/entry_based_movement_filter.json`
и совпадает с фактическим SHA-256 файла `ML/reports/entry_based_amplitude_movement.json`.

Source search budget:

- explicit field in source artifact: absent
- derived completed metric runs: `356`
- derived seed aggregate rows: `132`
- simple profile seed aggregates: `24`

New filter search budget:

- planned candidates: `32`
- evaluated candidates: `32`
- rerun score families: `8`

Selected filter on `val_select`:

| profile | model_key | horizon | selected_fraction | selected_n | movement_lift | selected_p80 | skipped_p80 | spearman |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `simple_combined` | `extra_trees_small` | 3 | 0.05 | 333 | 2.1528 | 17.576 | 8.220 | 0.5734 |

`val_select` table for the selected score family:

| selected_fraction | selected_n | movement_lift | selected_p80 | skipped_p80 |
|---:|---:|---:|---:|---:|
| 0.05 | 333 | 2.1528 | 17.576 | 8.220 |
| 0.10 | 665 | 2.0810 | 16.226 | 7.830 |
| 0.20 | 1330 | 2.0374 | 14.836 | 7.146 |
| 0.30 | 1995 | 1.9528 | 13.170 | 6.590 |

Single selected filter on `val_eval`:

| selected_n | skipped_n | movement_lift | selected_p80 | skipped_p80 | spearman | yearly_lift_pass_rate |
|---:|---:|---:|---:|---:|---:|---:|
| 333 | 6313 | 2.4806 | 35.634 | 14.456 | 0.6945 | 1.00 |

Yearly table:

| split | year | selected_n | movement_lift | passes_yearly_lift_gate |
|---|---:|---:|---:|---|
| `val_select` | 2021 | 135 | 1.9753 | True |
| `val_select` | 2022 | 126 | 2.1714 | True |
| `val_select` | 2023 | 73 | 2.1797 | True |
| `val_eval` | 2023 | 62 | 2.1005 | True |
| `val_eval` | 2024 | 137 | 1.8806 | True |
| `val_eval` | 2025 | 135 | 1.7712 | True |

2026 disclosure table:

| split | selected_n | skipped_n | movement_lift | selected_p80 | skipped_p80 | spearman |
|---|---:|---:|---:|---:|---:|---:|
| `low_n_disclosure` | 59 | 1103 | 1.6292 | 68.646 | 51.134 | 0.1609 |

Selected rows artifact:

- `ML/reports/entry_based_movement_filter_selected_rows.csv`
- rows: `392`
- composition: `val_eval` selected rows + `2026 low_n_disclosure` selected rows

Explicit scope statement:

- no direction model;
- no BUY/SELL selection;
- no PnL, PF, spread, stop-loss or take-profit metrics;
- no `locked_test` access.

## Conclusions

Task 5 completed successfully. В рамках разрешённого bounded search нашёлся один простой movement-filter, который проходит:

- `val_select` gate;
- `val_eval` survival gate;
- yearly stability check.

Поэтому текущий корректный вывод — `SIMPLE_MOVEMENT_FILTER_RESEARCH_ONLY`, а не торговый candidate.

## Limitations / Open Questions

1. Source artifact не содержал явного поля `cumulative_search_budget`, поэтому budget в movement-filter JSON пришлось выводить из уже записанных `metrics` и `seed_aggregate`. Это честная производная, но не исходное поле source artifact.
2. Реальный CLI не мгновенный: только подготовка split-ов через amplitude pipeline заняла около `79s`, после чего идёт bounded rerun восьми score family.
3. Порог здесь означает `top_fraction`, а не фиксированный абсолютный score cutoff между split-ами.

## Validation Split Disclosure

Split contract унаследован от source amplitude-аудита:

- `train <= 2020`: fit моделей и scaler/normalization внутри bounded rerun;
- `validation = 2021-2025`;
- `val_select`: единственный split для выбора profile/model/horizon/threshold;
- `val_eval`: check-only для одного выбранного фильтра;
- `low_n_disclosure = 2026`: disclosure-only, не участвует в выборе;
- `locked_test = not_opened`.

Sample sizes после фильтра:

| Split | Role | Selected N | Skipped N | Notes |
|---|---|---:|---:|---|
| `val_select` | selection | 333 | 6315 | winner chosen here |
| `val_eval` | check-only | 333 | 6313 | no replacement after evaluation |
| `low_n_disclosure` | disclosure-only | 59 | 1103 | validated as 2026-only |

Runner дополнительно проверяет, что `low_n_disclosure` содержит только 2026 год.
Если этот контракт нарушен, запуск считается contract failure.

## Next Step

Следующий разумный шаг — отдельный replication/freeze plan только для найденного `simple_combined / extra_trees_small / H3 / top 5%` movement-filter, без расширения search space и по-прежнему без перехода к direction/PnL.

## Related Materials

- `ML/baseline/benchmark_entry_based_movement_filter.py`
- `tests/test_entry_based_movement_filter.py`
- `ML/reports/entry_based_movement_filter.json`
- `ML/reports/entry_based_movement_filter_candidates.csv`
- `ML/reports/entry_based_movement_filter_yearly.csv`
- `ML/reports/entry_based_movement_filter_selected_rows.csv`
- `ML/reports/entry_based_amplitude_movement.json`
