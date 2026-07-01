# Context Handoff

**Дата:** 2026-06-30

## Текущий этап

Regression Up/Dn target foundation выполнен, пересчитан после post-review правок и закрыт как **DIAGNOSTIC_ONLY**.

Внутренний research gate на ограниченном поиске прошёл:

- `selected_profile = structure_full`
- `selected_horizon = 3`
- `research_gate_status = TARGET_FOUNDATION_PASSED`
- `artifact_status = DIAGNOSTIC_ONLY`

Это не торговый winner и не готовый target для production. Это только подтверждение, что семейство top-level `up_*/dn_*` содержит сильный короткий horizon signal при корректном feature contract.

Post-review уточнения уже внесены в код и JSON:

- `feature_read_audit` теперь честно разделяет `declared_feature_sources` и технические чтения `raw_columns_touched` / `raw_fractal_subfields_touched`;
- для профилей на фрактальных строках раскрыто, что reused builder технически трогает `ATR` и `price`, хотя эти поля не обязаны становиться признаками текущего профиля;
- добавлены `log_ratio` и расширенный `calendar_dependence`.

## Главные артефакты

- `ML/reports/regression_updn_target_foundation.json`
- `docs/reports/2026-06-30-regression-updn-target-foundation.md`
- `ML/baseline/benchmark_regression_updn_target_foundation.py`
- `tests/test_regression_updn_target_foundation.py`

## Главный вывод

Короткие горизонты (`H3`, затем `H6`) заметно сильнее legacy `H12`.

На bounded feature search лучший сигнал даёт `structure_full`, причём он виден уже на `Ridge` и затем усиливается на tree/forest/XGBoost. Это означает, что top-level `up_*/dn_*` можно считать рабочей target foundation, но только в диагностическом статусе и без готового trading mapping.

Отдельный риск остаётся в общем data-contract tooling: `statistics/data_contract_smoke_check.py` на текущих XAUUSD split-файлах падает на историческом ожидании колонки `target_buy_H6_val`. Новый Up/Dn runner от этого напрямую не ломается, но project-level smoke-check нужно синхронизировать.

## Следующий шаг

Нужен новый узкий confirmatory cycle:

- зафиксировать один short-horizon candidate (`H3` или `H6`);
- держать `H12` только как legacy reference;
- заранее заморозить mapping `up_h/dn_h -> trading decision`;
- не расширять feature search.

Отдельный открытый технический долг:

- `statistics/data_contract_smoke_check.py` по-прежнему ожидает историческую колонку `target_buy_H6_val`; это уже не проблема нового runner-а, но это несинхронизированный project-level contract check.

## Запрещённые направления

- Не открывать новый широкий перебор horizon/ATR/TP/SL.
- Не выбирать horizon/profile/model по `diagnostic_holdout` (`2023-2025`) или `low_n_disclosure` (`2026`).
- Не объявлять `H3` торговым winner только по итогам target-foundation этапа.
- Не игнорировать FAIL общего `data_contract_smoke_check.py`; его нужно либо починить, либо явно ограничить область применения.
