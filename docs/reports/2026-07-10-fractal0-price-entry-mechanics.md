# Fractal0 Price Entry Mechanics Oracle-Preflight

> **Дата**: 2026-07-10
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: Проверить диагностический потолок входа через возврат цены к зоне около `fractal0_price`.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-10-fractal0-price-entry-mechanics.md`

## Context

`next open after signal_time` был отклонён, но старый Up/Dn signal остаётся
сильным относительно `fractal0_price`. Этот этап проверил другую механику:
вход только после возврата цены к зоне около `fractal0_price`.

Уровень этапа: поисковый. Это oracle-preflight механики входа, а не проверка
готовой торговой системы.

## What Was Done

Добавлен runner `ML/baseline/benchmark_fractal0_price_entry_mechanics.py`.
Он строит fill/no-fill для `limit_at_fractal0` и `zone_edge`, считает targets
от фактической достижимой цены входа и пишет JSON/CSV артефакты.

Сторона берётся по контракту `direction = -fractal0.dir`:
`fractal0.dir == -1 -> BUY`, `fractal0.dir == 1 -> SELL`.

## Multiple Testing Context

```text
lifecycle_status: exploratory_result
origin_bias: post_mortem
research_priority: high
current_search_budget: 108 oracle configurations
cumulative_search_budget_lower_bound: 184
cumulative_search_budget_status: lower_bound_disclosed
next_probe_freeze: none
allowed_max_verdict: research_only
forbidden_interpretations: PnL, PF, прибыльно, готово, можно запускать, live-ready, tradable
```

Gate не использует `spread=0.00`. Правило выбирается только на `train_core`
и проверяется на `val_stop`.

## Changed Files

- `ML/baseline/benchmark_fractal0_price_entry_mechanics.py`
- `tests/test_fractal0_price_entry_mechanics.py`
- `docs/ML/benchmark_fractal0_price_entry_mechanics.py.md`
- `ML/reports/fractal0_price_entry_mechanics.json`
- `ML/reports/fractal0_price_entry_mechanics_rows.csv`

## Verification

```bash
./.venv/bin/python -m pytest tests/test_fractal0_price_entry_mechanics.py -q
./.venv/bin/python ML/baseline/benchmark_fractal0_price_entry_mechanics.py --fractal0-entry-mechanics
```

Focused tests: `16 passed`.

Full runner output:

```text
{'verdict': 'diagnostic_only', 'json': '/home/hohla/git/SoSimple/ML/reports/fractal0_price_entry_mechanics.json', 'rows': '/home/hohla/git/SoSimple/ML/reports/fractal0_price_entry_mechanics_rows.csv'}
```

## Results

Selected train rule:

```text
entry_zone_edge_zone_0.5_lag_6_h3_spread_0.2
```

`train_core` selected summary:

```text
rows_total: 44159
filled_events: 32729
no_fill_rate: 0.25883738309291426
favorable_to_adverse_ratio: 1.20615838702499
active_years: 16
filled_events_per_year_min: 938
ratio_without_best_year: 1.2010025156708224
```

`val_stop` summary for the selected rule:

```text
rows_total: 5205
filled_events: 3854
no_fill_rate: 0.25955811719500477
favorable_to_adverse_ratio: 1.2421118400499844
active_years: 2
filled_events_per_year_min: 1864
ratio_without_best_year: 1.2397913622895531
stress_favorable_to_adverse_ratio: 1.1895354754041108
```

Side contract audit: `PASS`, direction counts `-1: 20740`, `1: 23419`.

Research gate: `passes = false`. Единственный failed check:
`min_years_or_windows_val_stop = false`, потому что `val_stop` содержит 2
активных года при требовании 3.

## Conclusions

Механика показывает высокий диагностический oracle-потолок на выбранном
правиле, но gate не пройден из-за недостаточного числа активных лет в
`val_stop`. Поэтому итог остаётся `diagnostic_only`, lifecycle —
`exploratory_result`.

Этап не даёт права делать вывод о торговой пригодности. Выход из сделки не
задан, порядок благоприятного и неблагоприятного движения внутри окна не
моделируется.

## Limitations / Open Questions

- Нет exit contract.
- `locked_test` не открыт.
- `diagnostic_holdout` и `low_n_disclosure` не использовались для выбора.
- Точный широкий cumulative search budget прошлой ветки не восстановлен,
  поэтому указан только lower bound.
- Нужен отдельный frozen probe-plan, если эту механику продолжать.

## Split Disclosure

- `train_core`: выбор правила.
- `val_stop`: проверка выбранного правила.
- `diagnostic_holdout`: disclosure-only.
- `low_n_disclosure`: disclosure-only.
- `locked_test`: не открыт.

Sample-size gate не пройден по `min_years_or_windows_val_stop`: найдено 2
активных года, требуется 3.

## Next Step

Не повышать статус текущего результата. Допустимый следующий шаг только один:
отдельный frozen probe-plan, где заранее фиксируются правило входа, горизонты,
split-роли, критерии устойчивости и дальнейший contract. До такого плана нет
candidate, нет открытия `locked_test` и нет торговых выводов.

## Related Materials

- `docs/reports/2026-06-30-regression-updn-target-foundation.md`
- `docs/reports/2026-07-01-regression-updn-ratio-audit.md`
- `docs/reports/2026-07-02-regression-updn-already-moved-audit.md`
- `docs/reports/2026-07-02-next-open-entry-updn-foundation.md`
- `docs/reports/2026-07-09-direction-inside-frozen-movement-regime-rich-features.md`
- `docs/reports/2026-07-10-direction-inside-frozen-mask-narrow-replication.md`
