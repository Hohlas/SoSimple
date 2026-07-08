# Context Handoff

**Дата:** 2026-07-07

## Текущее состояние

Подэтап `Entry-Based Movement Filter Design` синхронизирован по docs/wiki/handoff.

Итог текущей ветки:

- amplitude audit уже завершён с verdict `DIAGNOSTIC_ONLY / AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES`;
- поверх него построен отдельный bounded movement-filter CLI;
- корректный итог нового шага: `SIMPLE_MOVEMENT_FILTER_RESEARCH_ONLY`.

Final verification выполнен контроллером: полный `tests/` прошёл (`1180 passed, 30 warnings`).

## Главные артефакты

- `docs/reports/2026-07-07-entry-based-movement-filter-design.md`
- `ML/reports/entry_based_movement_filter.json`
- `ML/reports/entry_based_movement_filter_candidates.csv`
- `ML/reports/entry_based_movement_filter_yearly.csv`
- `ML/reports/entry_based_movement_filter_selected_rows.csv`
- `ML/baseline/benchmark_entry_based_movement_filter.py`
- `docs/ML/benchmark_entry_based_movement_filter.py.md`
- `tests/test_entry_based_movement_filter.py`

Контекст-источник, который нужно держать рядом:

- `docs/reports/2026-07-07-entry-based-amplitude-movement-regime.md`
- `ML/reports/entry_based_amplitude_movement.json`

## Главный вывод

Выбран ровно один допустимый filter:

- `simple_combined / extra_trees_small / H3 / top_fraction=0.05`

Его числа:

- `val_select`: `selected_n=333`, `movement_lift=2.1528`
- `val_eval`: `selected_n=333`, `movement_lift=2.4806`, `yearly_lift_pass_rate=1.0`
- `2026 disclosure`: `selected_n=59`, `movement_lift=1.6292`

Границы интерпретации:

- это только pre-entry movement filter;
- direction не выбирается;
- BUY/SELL выводов нет;
- PnL/PF нет;
- `locked_test` не открыт;
- `2026` не использовался для выбора.

## Что уже синхронизировано

- `docs/ML/benchmark_entry_based_movement_filter.py.md`
- `docs/tests/tests.md`
- `MODULE_INDEX.md`
- `CHANGELOG.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`

## Следующий шаг

Следующим агентом читать:

- `docs/reports/2026-07-07-entry-based-movement-filter-design.md`
- `docs/ML/benchmark_entry_based_movement_filter.py.md`
- `ML/reports/entry_based_movement_filter.json`

Практический следующий шаг:

- не расширять search space;
- если продолжать ветку, то только отдельным plan на узкую репликацию/заморозку
  одного filter-а `simple_combined / extra_trees_small / H3 / top_fraction=0.05`.

## Запрещённые направления

- Не трактовать movement filter как direction signal.
- Не считать его trading candidate без отдельного replication/freeze плана.
- Не открывать `locked_test`.
- Не возвращаться к wide search по новым профилям/моделям в этой же ветке.
- Не добавлять PnL/PF интерпретацию задним числом.
