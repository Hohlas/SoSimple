# benchmark_fractal0_price_entry_mechanics.py

## Назначение

Диагностический runner для oracle-preflight входа через возврат цены к зоне
около `fractal0_price`.

## Команда

```bash
./.venv/bin/python ML/baseline/benchmark_fractal0_price_entry_mechanics.py --fractal0-entry-mechanics
```

## Входы

- `DATA/XAUUSD_H1_OHLC.csv`
- `DATA/Nero_XAUUSD_train_labeled.csv`
- `DATA/Nero_XAUUSD_validation_labeled.csv`
- `DATA/Nero_XAUUSD_test_labeled.csv`

## Выходы

- `ML/reports/fractal0_price_entry_mechanics.json`
- `ML/reports/fractal0_price_entry_mechanics_rows.csv`

## Ограничения

- `locked_test` не открывается.
- Verdict не выше `research_only`.
- `research_hypothesis` является `lifecycle_status`, а не verdict.
- Runner не считает PnL/PF, потому что exit contract не задан.
- `spread=0.00` только отладочный diagnostic и не участвует в gate.
- Сторона берётся из `fractal0.dir`: `fractal0.dir == -1 -> BUY`,
  `fractal0.dir == 1 -> SELL`.
- Side audit проходит только если в реальном split есть обе стороны.
- Gate требует сравнение с простым правилом `limit_at_fractal0 / zone 0.0`.
- `ratio_without_best_year` удаляет год с лучшим yearly ratio
  `favorable/adverse`.
- Старые `up_*/dn_*` от `fractal0_price` не используются как торговая
  разметка; новые target-поля считаются от фактической достижимой цены входа.
