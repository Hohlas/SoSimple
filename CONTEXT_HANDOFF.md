# Context Handoff

**Дата:** 2026-07-02

## Текущий этап

Связка `Regression Up/Dn target foundation` → `ratio audit` → `already moved audit` теперь закрыта как диагностическая линия.

Главный факт больше не в том, что target family `up_*/dn_*` содержит сигнал. Это уже подтверждено. Главный новый вывод в другом: этот сигнал **не переносится** в схему немедленного входа `next open after signal_time`.

Итоговый structured artifact:

- `ML/reports/regression_updn_already_moved_audit.json`
- статус runner: `PASS_DIAGNOSTIC`
- verdict этапа: `DIAGNOSTIC_ONLY`

## Главные артефакты

- `docs/reports/2026-07-02-regression-updn-already-moved-audit.md`
- `docs/reports/2026-07-01-regression-updn-ratio-audit.md`
- `ML/reports/regression_updn_already_moved_audit.json`
- `ML/reports/regression_updn_already_moved_audit_rows.csv`
- `ML/reports/regression_updn_ratio_audit.json`

## Главный вывод

От цены `fractal0_price` сигнал остаётся сильным, особенно на коротких горизонтах:

- `val_stop` Spearman `pred vs actual from fractal`:
  - `H3 = 0.8786`
  - `H6 = 0.7815`
  - `H12 = 0.6749`

Но после реально доступного входа на следующий `open` связь практически исчезает и это повторяется на всех трёх split:

- `val_stop`: `-0.0149 / -0.0174 / 0.0010`
- `diagnostic_holdout=2023-2025`: `-0.0336 / -0.0252 / -0.0173`
- `low_n_disclosure=2026`: `-0.0040 / -0.0038 / 0.0043`

Это значит:

- `Regression Up/Dn` как target family не опровергнут;
- но `market-entry` на ближайшем следующем H1 `open` для этого target **отклонён**.

Отдельно подтверждено, что заметная часть движения часто уже произошла до входа:

- доля строк, где уже прошло не меньше половины движения хотя бы по одной стороне target:
  - `H3 = 57.29%`
  - `H6 = 42.15%`
  - `H12 = 29.80%`

## Следующий шаг

Разрешён только узкий follow-up по entry-механике, а не новый широкий поиск модели:

- вход, привязанный к `fractal0_price`;
- `retest-entry` / `limit-entry`;
- новый target, измеряемый прямо от `entry_open`, если задача именно про немедленный вход.

## Запрещённые направления

- Не использовать `pred_log_ratio`, `pred_up - pred_dn` или `pred_up / pred_dn` как немедленный `market-entry` на следующем `open`.
- Не возвращаться к оптимизации `Stop/Profit` вокруг этой схемы входа: она уже диагностически отклонена.
- Не выбирать новые правила по `diagnostic_holdout` (`2023-2025`) или `low_n_disclosure` (`2026`).
- Не смешивать два разных объекта:
  - сигнал движения от `fractal0_price`;
  - сигнал остаточного движения после фактически доступного входа.
