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

## Rich Entry Quality Mode

Команда:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --rich-entry-quality \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_rich_entry_quality \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id S2_fractal0_buffer_0_5_entry_floor_2 \
  --permutation-repeats 200
```

Rich mode проверяет качество planned limit entry до отправки заявки:
`decision_time=pre_order_after_signal_before_limit_order_send`.

Phase A eligible winner использует 9 feature profiles, 3 модели, 3 цели и
3 primary filters: `243` ranked configurations. `top20`, `top10`,
`structure_nearest_k80`, `structure_all100`, XGBoost и LightGBM не участвуют
в выборе winner Phase A. XGBoost/LightGBM можно запускать только как
diagnostic-only в Phase A после проверки зависимостей, либо как eligible
модели в отдельной заранее зафиксированной Phase B.

Основные артефакты:

- `ML/reports/fractal0_rich_entry_quality.json`
- `ML/reports/fractal0_rich_entry_quality_summary.csv`
- `ML/reports/fractal0_rich_entry_quality_feature_contract.csv`
- `ML/reports/fractal0_rich_entry_quality_target_distribution.csv`
- `ML/reports/fractal0_rich_entry_quality_planned_order_diagnostics.csv`
- `ML/reports/fractal0_rich_entry_quality_split_manifest.csv`
- `ML/reports/fractal0_rich_entry_quality_feature_distribution_audit.csv`
- `ML/reports/fractal0_rich_entry_quality_feature_distribution_flags.csv`
- `ML/reports/fractal0_rich_entry_quality_forbidden_column_audit.csv`
- `ML/reports/fractal0_rich_entry_quality_score_diagnostics.csv`
- `ML/reports/fractal0_rich_entry_quality_selected_score_diagnostics.csv`
- `ML/reports/fractal0_rich_entry_quality_permutation.csv`
- `ML/reports/fractal0_rich_entry_quality_winner_yearly.csv`

Maximum verdict: `RESEARCH_HINT_RICH_FEATURES`. `locked_test` не открывается.

Итог corrected full rerun `2026-07-21` после аудита:

- executed configs: `243`;
- selected on `val_select`: `time_only / linear / target_entry_ev_regression / top30`;
- fixed `val_eval`: `n_trades=660`, `PF=4.0268`, `BS_p05=3.3955`;
- control `S2/E3/M0/X2 no-mask`: `n_trades=2298`, `PF=2.7873`,
  `BS_p05=2.5085`;
- control `S0/E3/M0/X0_fixed_r_0_7`: `n_trades=2298`, `PF=2.7247`,
  `BS_p05=2.5120`.

Audit fixes: `fractal0..fractal99` теперь переносятся в `entry_cache`,
`structure_nearest_k20/k40` сортируют уровни по расстоянию к `planned_limit`,
score diagnostics включают `rich_entry_score`, target distribution содержит
`year`, а movement provenance проверяет hash `movement_freeze_scores`.
Feature-contract gates прошли все 9 профилей.

Вывод остаётся исследовательским: rich/structural профили больше не сломаны
контрактно, но не победили `time_only`; winner выбран после wide validation
search, полная коррекция множественного перебора не выполнена, `locked_test`
не открыт. `--permutation-repeats 200` не запускал full-selection
permutation; `_permutation.csv` содержит только заголовок, а JSON фиксирует
`permutation_null_repeats_executed_for_full_selection=0`.
`feature_importance_by_profile.csv` не производится, потому что runner не
сохраняет fitted per-profile модели и этот artifact не участвовал в selection.

## Time Only Robustness Audit

After normalized rich-entry rerun, `ML/baseline/audit_time_only_robustness.py`
audits the fixed `time_only / linear / target_entry_ev_regression / top30`
winner from saved normalized artifacts. It does not retrain, does not select a
new rule and does not open `locked_test`.

## Leaderboard Robustness Audit

`ML/baseline/audit_leaderboard_robustness.py` checks the 11 fixed audit input rows from
the normalized `Candidate Shortlist / Leaderboard`. It does not retrain, does
not select a new winner and does not open `locked_test`.

## Normalized Rich Entry Quality Mode

Команда:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --rich-entry-quality \
  --normalized-rich-features \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_rich_entry_quality_normalized \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id S2_fractal0_buffer_0_5_entry_floor_2 \
  --permutation-repeats 200
```

Normalized rich mode не заменяет legacy rich mode. Он добавляет отдельный
feature contract:

- raw price-like inputs запрещены;
- price-like values переводятся в ATR-координаты до unit scaling;
- unit scaler fit выполняется только на `train_core`;
- `val_select` и `val_eval` применяют train-core scaler bounds;
- финальные model inputs должны быть finite и в диапазоне `0..1`;
- missing indicators входят в fixed schema заранее;
- padded fractal token values остаются `0.0` и исключаются из scaler fit через
  `fractalN_present`.

Новые diagnostic-only profiles:

- `atr_only`
- `time_plus_atr`
- `planned_geometry_no_atr`

Они исполняются в normalized run, но не участвуют в winner selection. Поэтому
ranked budget остаётся `243`, а фактически выполненных jobs в full run может
быть `324`.

Основные normalized artifacts:

- `ML/reports/fractal0_rich_entry_quality_normalized.json`
- `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_feature_contract.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_feature_distribution_audit.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_normalized_feature_distribution_audit.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_token_coverage.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_normalization_config.json`
- `ML/reports/fractal0_rich_entry_quality_normalized_forbidden_column_audit.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_protocol_comparison.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_diagnostic_best_val_eval_by_profile.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_updn_provenance_gate.csv`

Итог normalized rerun `2026-07-22`:

- `status=completed`;
- `locked_test=not_opened`;
- `feature_contract_variant=normalized_atr_unit`;
- `ranked_search_budget=243`;
- `n_total_executed_configs=324`;
- selected on `val_select`: `time_only / linear / target_entry_ev_regression / top30`;
- fixed `val_eval`: `n_trades=660`, `PF=4.0268`, `BS_p05=3.3955`;
- final normalized audit: `below_zero_rate.max=0.0`, `above_one_rate.max=0.0`;
- forbidden raw-price audit: `0` forbidden columns;
- Up/Dn provenance gate: `PASS`;
- full-selection permutation not run:
  `permutation_null_repeats_executed_for_full_selection=0`,
  `permutation_gate=NOT_RUN_FOR_FULL_SELECTION`.

Protocol comparison against legacy rich shows that normalized contract improves
`rich_combined_k40`, `price_action_h1` and `structure_f0_only`, but formal
winner remains `time_only`. Result remains `RESEARCH_HINT_RICH_FEATURES`, not a
candidate and not permission to open `locked_test`.

## Ограничения rich-entry corrected rerun

- `locked_test` не открывается.
- Максимальный verdict: `RESEARCH_HINT_RICH_FEATURES`.
- Результат не является торговым кандидатом: он найден после validation search
  по `243` ranked configurations плюс предшествующие stop-grid/narrow решения.
- Rich/structural профили прошли feature-contract gates, но не доказали
  добавочную пользу над `time_only`.
- Следующий шаг должен быть pre-registered replication/probe, не freeze и не
  locked-test.

## Legacy narrow entry-quality limitations

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
