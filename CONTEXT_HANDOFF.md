# Context Handoff

**Дата:** 2026-07-10

## Текущее состояние

Ветка `fractal0_price` entry mechanics выполнена как oracle-preflight.
Добавлен runner `ML/baseline/benchmark_fractal0_price_entry_mechanics.py`,
тесты и отчёт:

- `docs/reports/2026-07-10-fractal0-price-entry-mechanics.md`
- `ML/reports/fractal0_price_entry_mechanics.json`
- `ML/reports/fractal0_price_entry_mechanics_rows.csv`
- `docs/ML/benchmark_fractal0_price_entry_mechanics.py.md`

Итог: `diagnostic_only`, `lifecycle_status = exploratory_result`.

## Главный вывод

Выбранное на `train_core` правило:

```text
entry_zone_edge_zone_0.5_lag_6_h3_spread_0.2
```

На `val_stop` оно имеет высокий oracle-ratio:

- `filled_events = 3854`;
- `no_fill_rate = 0.25955811719500477`;
- `favorable_to_adverse_ratio = 1.2421118400499844`;
- `stress_favorable_to_adverse_ratio = 1.1895354754041108`;
- `ratio_without_best_year = 1.2397913622895531`.
- `dummy_or_simple_rule_comparison = PASS`;
- simple rule ratio `= 1.061228066744197`.

Но gate не прошёл: `active_years = 2`, а требуется минимум `3`.
Поэтому результат нельзя повышать до `research_only`.

## Контракты

- `locked_test` не открыт.
- `spread=0.00` только diagnostic, не gate.
- Сторона: `direction = -fractal0.dir`.
- Side audit: `PASS`, counts `-1: 20740`, `1: 23419`, обе стороны есть.
- Старые `up_*/dn_*` не используются как торговая разметка.
- Новые targets считаются только от фактической достижимой цены входа.
- Exit contract отсутствует.

## Следующий шаг

Не продолжать как candidate. Если ветку продолжать, нужен отдельный frozen
probe-plan: заранее фиксировать правило входа, split-роли, горизонты, критерии
устойчивости, sample-size gate и разрешённый максимум verdict.

## Читать следующему агенту

- `docs/reports/2026-07-10-fractal0-price-entry-mechanics.md`
- `ML/reports/fractal0_price_entry_mechanics.json`
- `docs/superpowers/plans/2026-07-10-fractal0-price-entry-mechanics.md`
- `docs/reports/2026-07-02-next-open-entry-updn-foundation.md`
- `docs/reports/2026-07-10-direction-inside-frozen-mask-narrow-replication.md`

## Запрещённые направления

- Не открывать `locked_test`.
- Не делать PnL/PF/trading claims по этому этапу.
- Не использовать `diagnostic_holdout` или `low_n_disclosure` для выбора.
- Не тюнить по `val_stop` после просмотра результата без нового плана.
- Не продвигать результат выше `diagnostic_only` без нового sample-size
  contract и frozen probe-cycle.
