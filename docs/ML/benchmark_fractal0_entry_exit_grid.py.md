# benchmark_fractal0_entry_exit_grid.py

## Назначение

Research-runner для полной Fractal0 entry/exit сетки: OHLC-симуляция сделок,
ML-exit слой, frozen movement mask, stress-spread и перестановочная коррекция
множественного перебора.
Runner также поддерживает stop-policy grid для Fractal0: stop policy входит в
ключ run, resume, summary/trades, permutation и выбор winner.

## Команда

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_exit_grid.py \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_entry_exit_grid \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv
```

Stop-grid shortlist без полного stress-spread:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_exit_grid.py \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_stop_grid_m5 \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-grid-mode full \
  --exit-shortlist stop_grid \
  --skip-stress-spread \
  --permutation-repeats 200
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
- `ML/reports/fractal0_entry_exit_grid_all_grid_yearly.csv` / stop-grid
  equivalent для явного all-grid yearly scope
- `ML/reports/fractal0_entry_exit_grid_m5_winner_winner_yearly.csv`
- `ML/reports/fractal0_entry_exit_grid_attribution.csv`
- `ML/reports/fractal0_entry_exit_grid_permutation.csv`
- `ML/reports/fractal0_entry_exit_grid_progress.json`
- `ML/reports/fractal0_stop_grid_m5_stop_diagnostics.csv` для stop-grid
  диагностики по `stop_policy_id`, `split`, `stop_source`
- `ML/reports/fractal0_entry_exit_grid_m5_winner*.json/csv` для post-review
  winner-only пересчёта
- `ML/reports/fractal0_entry_exit_grid_m5_full*.json/csv` для полного M5
  full-grid rerun

## Контракт

- `locked_test` не открывается.
- `train_core` используется для обучения ML-exit моделей.
- `val_select` используется для выбора winner.
- `val_eval` используется для проверки уже выбранного winner.
- В stop-grid режиме `val_select` выбирает winner, а `val_eval` только
  проверяет уже выбранный ключ `stop_policy_id + entry_id + mask_id + exit_id`.
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
- Stop policy меняет `protective_stop_price`, `R`, ML-exit признаки в `R` и
  `target_exit_*`, поэтому ML-exit обучается отдельно для каждой
  `stop_policy_id`.
- Entry rows дополнительно сохраняют planned pre-order поля:
  `calculation_open`, `limit_price`, `planned_entry_price`,
  `planned_entry_bid_equivalent`, `planned_protective_stop_price`,
  `planned_r_value`. Они нужны downstream entry-filter runner-ам, чтобы
  строить признаки от планируемой заявки, а не от post-fill outcome.
- `pnl_r` означает одинаковый риск на сделку, а не одинаковый фиксированный
  лот. Более широкий stop при фиксированном лоте меняет денежный риск.

## Stop-grid CLI

- `--stop-grid-mode full|current-only`: четыре stop policies или только
  `S0_current_0_5`.
- `--exit-shortlist full|stop_grid`: `stop_grid` ограничивает exits до
  `X0_fixed_r_0_7`, X1/X2/X3 threshold shortlist и `X7_time_6/12`.
- `--skip-stress-spread`: не запускает полный stress-spread и записывает
  `stress_spread_status = deferred_shortlist_only`. В этом режиме
  `*_spread_stress.csv` содержит status row, а не рассчитанные stress-метрики;
  поле `stress_spread=0.40` в JSON означает настроенный сценарий stress, а не
  факт его выполнения.
- Для `--exit-shortlist stop_grid` используется дешёвый budget:
  `4 stop policies x 3 entries x 2 masks x 12 exits = 288` selection cells,
  `576` completed canonical split-runs без stress.

## Ограничения

- Verdict не выше `research_only`.
- Первичный H1 full-grid artifact содержит устаревший `diagnostic_only` cap по
  ambiguity. Текущий полный M5 artifact:
  `ML/reports/fractal0_entry_exit_grid_m5_full.json`.
- В полном M5 rerun winner сменился на
  `E3_open_pullback_1_0atr / M0_no_mask / X0_fixed_r_0_7`: `val_eval
  PF=2.7247`, `BS_p05=2.4868`, stress PF `2.2945`,
  `ambiguous_same_bar_rate=0.0074`.
- `fractal0_entry_exit_grid_yearly.csv` является глобальной диагностикой по
  all-grid simulated trade rows, а не yearly-разрезом winner. Для текущего full M5
  winner используется `fractal0_entry_exit_grid_m5_full_winner_yearly.csv`;
  для исторического M5 winner-only пересчёта используется
  `fractal0_entry_exit_grid_m5_winner_winner_yearly.csv`.
- До review fix `effective_profit_years` считался как число прибыльных лет.
  Текущий runner считает методическую формулу `1 / sum(share_y^2)`.
- Перестановочная коррекция исправлена после первичного прогона: CSV содержит
  `200` строк, метод `block_shuffled_val_select_pnl_r`.
- Для практичного пересчёта перестановочной коррекции использовано `20`
  bootstrap-сэмплов на перестановочную метрику; это зафиксировано в JSON.
  В полном M5 rerun использовано `200` bootstrap-сэмплов на перестановочную
  метрику.
- M5 используется только для execution ordering после H1-входа, не как признак
  модели.
