# benchmark_fractal0_entry_quality_filter.py

## Назначение

Research-runner для ML-entry фильтра поверх выбранной Fractal0 E3 механики:
`E3_open_pullback_1_0atr / M0_no_mask` с stop policy из stop-grid и тем же
M5 execution ordering. Runner не копирует торговый симулятор: он использует
`ML/baseline/benchmark_fractal0_entry_exit_grid.py` для загрузки данных,
сборки entry rows, обучения ML-exit, симуляции сделок, метрик и bootstrap.

## Команда

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_entry_quality_filter \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id S2_fractal0_buffer_0_5_entry_floor_2 \
  --permutation-repeats 200
```

Smoke/debug:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --threads 2 \
  --no-resume \
  --output-prefix /tmp/fractal0_entry_quality_filter_smoke \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id S0_current_0_5 \
  --smoke-limit-filters 3 \
  --permutation-repeats 5
```

## Входы

- `DATA/XAUUSD_H1_OHLC.csv`
- `MT/MQL4/Files/XAUUSD_M5_OHLC.csv` — только для порядка исполнения внутри
  H1-свечи
- `DATA/Nero_XAUUSD_train_labeled.csv`
- `DATA/Nero_XAUUSD_validation_labeled.csv`
- `ML/reports/entry_based_movement_filter_freeze.json`
- `ML/reports/entry_based_movement_filter_freeze_scores.csv`
- `ML/reports/fractal0_stop_grid_m5.json`

Project CSV читаются с `sep=";"`; generated CSV с неизвестным разделителем
читаются через detection в базовом runner.

## Выходы

- `ML/reports/fractal0_entry_quality_filter.json`
- `ML/reports/fractal0_entry_quality_filter_summary.csv`
- `ML/reports/fractal0_entry_quality_filter_trades.csv`
- `ML/reports/fractal0_entry_quality_filter_scores.csv`
- `ML/reports/fractal0_entry_quality_filter_yearly.csv`
- `ML/reports/fractal0_entry_quality_filter_score_diagnostics.csv`
- `ML/reports/fractal0_entry_quality_filter_permutation.csv`

JSON сохраняет `input_artifact_hashes`, `current_search_budget`,
`cumulative_search_budget`, `stop_policy_id`,
`exit_policy_id_used_for_entry_labels`, `filter_id`,
`score_cutoff_on_val_select`, `actual_val_eval_selected_fraction`,
`actual_val_eval_selected_trades` и `locked_test=not_opened`.

## Entry Targets

Entry labels строятся по фактическим E3 сделкам на `train_core`:

- `target_entry_good = 1`, если `pnl_r > 0`;
- `target_entry_avoid_sl = 1`, если `close_reason != "SL"`.

Эти цели не равны: сделка может избежать SL, но закрыться в минус через
`ML_CLOSE` или `TIME`.

## Feature Contract

Decision time: `pre_order_after_signal_before_limit_order_send`.

Разрешённые признаки entry-модели доступны до отправки limit-заявки и
считаются от planned limit/stop/R полей:

- `side_buy`;
- `ATR`;
- `entry_to_fractal0_atr`;
- `stop_distance_atr`;
- `r_value_atr`;
- frozen `movement_score` используется только для movement baseline, не как
  вход ML-entry модели.

Запрещены будущие и post-fill поля: `pnl_r`, `close_reason`, `hold_bars`,
`exit_time`, `future_*`, `target_*`, `target_exit_*`, `target_entry_*` и любые
outcome OHLC поля после fill.

## Selection Contract

- `train_core` обучает ML-exit и ML-entry.
- `val_select` выбирает filter family и topX threshold.
- Для topX сохраняется фактический `score_cutoff_on_val_select`; cutoff
  считается только по строкам с валидным finite score.
- `val_eval` применяет только сохранённый cutoff; topX не пересчитывается по
  распределению `val_eval`.
- Primary selection family: `entry_quality_topX`.
- `entry_avoid_sl_topX` остаётся secondary/diagnostic, если явно не проходит
  stronger gates.

## Ограничения

- `locked_test` не открывается.
- Максимальный verdict: `research_only`.
- Используется только `E3_open_pullback_1_0atr`.
- M5 не является признаком модели; он только уточняет порядок исполнения
  внутри H1-свечи.
- Результат не является торговым кандидатом: он найден после validation search
  по 17 фильтрам и должен идти в отдельный заранее зафиксированный probe.
- Исправленный прогон выбрал `entry_quality_top10` на `val_select`, но на
  `val_eval` этот rule оставил только `53` сделки и провалил no-mask baseline
  по `BS_p05`; текущий lifecycle — `research_hint`.
