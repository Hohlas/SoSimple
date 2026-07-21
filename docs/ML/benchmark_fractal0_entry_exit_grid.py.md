# benchmark_fractal0_entry_exit_grid.py

## Назначение

Research-runner для полной Fractal0 entry/exit сетки: OHLC-симуляция сделок,
ML-exit слой, frozen movement mask, stress-spread и перестановочная коррекция
множественного перебора.

## Команда

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_exit_grid.py \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_entry_exit_grid \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv
```

## Входы

- `DATA/XAUUSD_H1_OHLC.csv`
- `MT/MQL4/Files/XAUUSD_M5_OHLC.csv` опционально, только для порядка
  исполнения внутри H1-свечи
- `DATA/Nero_XAUUSD_train_labeled.csv`
- `DATA/Nero_XAUUSD_validation_labeled.csv`
- `ML/reports/entry_based_movement_filter_freeze.json`
- `ML/reports/entry_based_movement_filter_freeze_scores.csv`

## Выходы

- `ML/reports/fractal0_entry_exit_grid.json`
- `ML/reports/fractal0_entry_exit_grid_summary.csv`
- `ML/reports/fractal0_entry_exit_grid_spread_stress.csv`
- `ML/reports/fractal0_entry_exit_grid_trades.csv`
- `ML/reports/fractal0_entry_exit_grid_yearly.csv`
- `ML/reports/fractal0_entry_exit_grid_m5_winner_winner_yearly.csv`
- `ML/reports/fractal0_entry_exit_grid_attribution.csv`
- `ML/reports/fractal0_entry_exit_grid_permutation.csv`
- `ML/reports/fractal0_entry_exit_grid_progress.json`
- `ML/reports/fractal0_entry_exit_grid_m5_winner*.json/csv` для post-review
  winner-only пересчёта

## Контракт

- `locked_test` не открывается.
- `train_core` используется для обучения ML-exit моделей.
- `val_select` используется для выбора winner.
- `val_eval` используется для проверки уже выбранного winner.
- Canonical spread: `0.20`; stress spread: `0.40`.
- Сторона сделки: `fractal0.dir == -1 -> BUY`, `fractal0.dir == 1 -> SELL`.
- OHLC считается Bid; BUY exit по Bid, SELL exit по Ask.
- Если для exit rule с реальным fixed TP в одной H1-свече задеты TP и SL,
  порядок может уточняться через `--execution-ohlc-path`; если младший
  таймфрейм не задан или сам неоднозначен, применяется `SL first`.
- Для ML-exit правил не считается гипотетический fixed TP; ambiguity относится
  только к реально активным exit-условиям.
- В новых trades runner записывает `spread` на уровне сделки; это необходимо,
  чтобы yearly-разрезы не смешивали canonical и stress-spread сделки.

## Ограничения

- Verdict не выше `research_only`.
- Первичный full-grid artifact содержит устаревший `diagnostic_only` cap по
  ambiguity. После M5/bugfix winner-only пересчёта previous winner имеет
  `ambiguous_same_bar_rate = 0.0`, но полный grid ещё не пересчитан.
- `fractal0_entry_exit_grid_yearly.csv` является глобальной диагностикой по
  всем конфигурациям, а не yearly-разрезом winner. Для текущего M5
  winner-only пересчёта используется
  `fractal0_entry_exit_grid_m5_winner_winner_yearly.csv`.
- До review fix `effective_profit_years` считался как число прибыльных лет.
  Текущий runner считает методическую формулу `1 / sum(share_y^2)`.
- Перестановочная коррекция исправлена после первичного прогона: CSV содержит
  `200` строк, метод `block_shuffled_val_select_pnl_r`.
- Для практичного пересчёта перестановочной коррекции использовано `20`
  bootstrap-сэмплов на перестановочную метрику; это зафиксировано в JSON.
- M5 используется только для execution ordering после H1-входа, не как признак
  модели.
