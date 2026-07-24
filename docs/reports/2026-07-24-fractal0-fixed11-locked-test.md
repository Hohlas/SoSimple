# Fractal0 Fixed-11 Locked Test

> **Дата**: 2026-07-24
> **Статус**: Completed
> **Вердикт**: candidate_check_required
> **Цель**: проверить на новом `locked_test` периоде 11 frozen normalized rich-entry leaderboard rules без нового подбора.
> **Related plan**: `docs/superpowers/plans/2026-07-23-fractal0-fixed11-locked-test-protocol.md`

## Context

Проверяется ровно набор из 11 fixed normalized rich-entry leaderboard rules из `ML/reports/leaderboard_closure_audit_rules.csv`. Базовый execution contract взят из M5 stop-grid winner-а `ML/reports/fractal0_stop_grid_m5.json`.

`locked_test` split: `DATA/Nero_XAUUSD_test_labeled.csv`, период `2022-12-02` - `2026-06-04`, `9463` строк.

## Уровень Этапа

Проверочный locked-test запуск заранее выбранных 11 fixed rules.

Это не новый поиск: `current_search_budget = 11 frozen rules`, новых profile/model/target/filter/cutoff/entry/stop/exit/mask/spread вариантов не выбиралось.

## Frozen Rules

Источники:

- rules/cutoffs: `ML/reports/leaderboard_closure_audit_rules.csv`
- execution contract: `ML/reports/fractal0_stop_grid_m5.json`

Execution contract:

- `stop_policy_id = S2_fractal0_buffer_0_5_entry_floor_2`
- `entry_id = E3_open_pullback_1_0atr`
- `mask_id = M0_no_mask`
- `exit_id = X2_ml_opposite_any_p0_50`
- `spread = 0.20`
- execution OHLC: `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`

## What Was Done

- Добавлен воспроизводимый harness `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`.
- Harness использует торговую механику и rich-entry code из `ML/baseline/benchmark_fractal0_entry_quality_filter.py`.
- ML-exit слой обучен на `train_core`.
- Rich-entry модели обучены на `train_core`.
- Сохранённые `score_cutoff_on_val_select` применены к `locked_test`.
- `DATA/Nero_XAUUSD_test_labeled.csv` использован только как `locked_test`.
- M5 execution ordering использован для порядка исполнения внутри H1-свечи.
- Full-grid на `locked_test` не запускался.

## Reproduction

```bash
./.venv/bin/python ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py \
  --threads 24 \
  --source-rules-csv ML/reports/leaderboard_closure_audit_rules.csv \
  --source-artifact ML/reports/fractal0_stop_grid_m5.json \
  --locked-test-path DATA/Nero_XAUUSD_test_labeled.csv \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --output-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test
```

Verification:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py tests/test_fractal0_fixed11_rich_entry_locked_test.py -q
```

## Execution Log / Method

Этот раздел фиксирует полный ход пересчёта, чтобы результат можно было независимо воспроизвести и проверить.

### 1. Выбор источников

Использованы только заранее зафиксированные источники:

- `ML/reports/leaderboard_closure_audit_rules.csv` — список 11 правил, их `profile_id`, `model_id`, `target_id`, `filter_id` и сохранённые `score_cutoff_on_val_select`;
- `ML/reports/fractal0_stop_grid_m5.json` — source artifact для execution contract;
- `DATA/Nero_XAUUSD_test_labeled.csv` — новый `locked_test` split;
- `DATA/XAUUSD_H1_OHLC.csv` — H1 OHLC для построения входов и признаков;
- `MT/MQL4/Files/XAUUSD_M5_OHLC.csv` — M5 OHLC только для восстановления порядка исполнения внутри H1-свечи.

Файл `ML/reports/leaderboard_closure_audit_rules.csv` проверяется harness-ом на наличие обязательных колонок и ровно 11 строк. Execution contract загружается из `selected_winner` в `ML/reports/fractal0_stop_grid_m5.json`.

### 2. Зафиксированный execution contract

Для всех 11 правил использовался один и тот же торговый contract:

- `stop_policy_id = S2_fractal0_buffer_0_5_entry_floor_2`;
- `entry_id = E3_open_pullback_1_0atr`;
- `mask_id = M0_no_mask`;
- `exit_id = X2_ml_opposite_any_p0_50`;
- `spread = 0.20`;
- price convention inherited from source runner: H1 OHLC as bid, spread as full bid-ask spread.

M5 не используется как источник признаков, target-ов, фильтров или выбора параметров. M5 применяется только после факта открытия сделки, чтобы уточнить, что произошло раньше внутри H1-свечи: SL/TP/exit event по правилам старого runner-а.

### 3. Подготовка split-ов

Harness вызывает `base.load_role_splits(config)` из `ML/baseline/benchmark_fractal0_entry_exit_grid.py` и получает стандартные project split-ы:

- `train_core`;
- `val_select`;
- `val_eval`.

Затем `locked_test` добавляется отдельной загрузкой из `DATA/Nero_XAUUSD_test_labeled.csv`:

- CSV читается с `sep=";"`;
- `time` парсится через `base.parse_project_time`;
- `split` принудительно выставляется в `locked_test`;
- `split_row_id` назначается как последовательный индекс строк.

В расчёте итоговых метрик используются `train_core`, `val_select` и `locked_test`. `val_eval` не используется для нового выбора.

### 4. Построение entry rows

Для `train_core`, `val_select` и `locked_test` вызывается:

```python
base.build_entry_rows(rows, ohlc, entry_rule, active_spread, stop_policy)
```

Это строит planned entry rows по frozen entry/stop contract. В этом запуске получено:

- `train_core`: `44159` rows, `21343` filled entries;
- `val_select`: `4731` rows, `2294` filled entries;
- `locked_test`: `9463` rows, `4763` filled entries.

### 5. Movement score

Для `time_only` правил `movement_score` не является входом модели.

Для `movement_plus_time` правил нужен `movement_score`. Source freeze scores artifact не содержит `locked_test`, поэтому для `locked_test` score восстановлен через тот же frozen movement protocol:

- movement scorer обучается на `train_core`;
- target: `entry_movement_3`;
- feature profile: `simple_combined`;
- model family: `extra_trees_small`;
- seeds берутся из `seeds_for_model("extra_trees_small")`;
- итоговый score — медиана предсказаний по seed-ам;
- scaler для movement scorer fit-ится только на train split внутри movement protocol.

`locked_test` используется только для применения уже обученного movement scorer-а и получения `movement_score`.

### 6. Разметка train labels для rich-entry моделей

Для каждого split-а строятся simulated trades через:

```python
base._simulate_entries(entries, ohlc, run_base, active_spread, pd.DataFrame(), execution_ohlc)
```

Из этих сделок строятся rich-entry labels через:

```python
rich.build_rich_entry_labels(entries, simulated)
```

Для обучения rich-entry моделей используются только labels из `train_core`. Labels на `locked_test` не используются для обучения, выбора или cutoff.

### 7. ML-exit слой

ML-exit слой обучается один раз на `train_core`:

```python
base._train_ml_exit_layer(exit_cache, ohlc, threads, seeds=base.EXIT_MODEL_SEEDS, n_estimators=200)
```

Вход `exit_cache` содержит только `train_core` entries для frozen execution contract. Затем для `locked_test` строятся exit decision rows и scoring:

```python
base.build_exit_decision_rows(entry_cache["locked_test"], ohlc)
base.score_exit_models(...)
```

`locked_test` не участвует в fit-е ML-exit моделей.

### 8. Обучение 11 rich-entry моделей

Для каждой строки из `leaderboard_closure_audit_rules.csv` выполняется отдельный frozen-rule run:

1. Берутся `profile_id`, `model_id`, `target_id`, `filter_id`, `score_cutoff_on_val_select`.
2. Для `train_core` строится normalized rich feature frame через `rich.build_normalized_rich_feature_frame`.
3. Normalization schema и scaler fit-ятся только на `train_core`:

```python
schema = rich.build_normalized_feature_schema(profile_id, x_train)
scaler = rich.fit_unit_scaler({"train_core": x_train}, schema)
```

4. `train_core` features масштабируются этим scaler-ом.
5. Training target готовится из `train_core` labels:

```python
rich.prepare_rich_training_target(...)
```

6. Rich-entry model обучается на `train_core`:

```python
rich.train_rich_entry_model(..., seed=42)
```

7. Для `locked_test` строятся признаки тем же profile-id и масштабируются train-only scaler-ом.
8. Модель выдаёт `rich_entry_score` для `locked_test`.

### 9. Применение frozen cutoff

Для каждой из 11 строк cutoff берётся из `score_cutoff_on_val_select` в `leaderboard_closure_audit_rules.csv`.

На `locked_test` cutoff не пересчитывается. Фильтр применяется в eval mode:

```python
rich.apply_entry_filter(scored_locked, rich._rich_filter_rule(filter_spec), mode="eval", score_cutoff=cutoff)
```

Это ключевой anti-leakage шаг: `locked_test` score distribution не используется для выбора нового top-fraction threshold.

### 10. Симуляция locked-test сделок

Для отобранных locked-test entries каждой строки вызывается:

```python
rich._simulate_for_filter(selected_locked, ohlc, run, scored_decisions["locked_test"], execution_ohlc)
```

Здесь:

- `ohlc` = H1 OHLC;
- `execution_ohlc` = M5 OHLC;
- `run` содержит frozen execution contract и fixed cutoff;
- `scored_decisions["locked_test"]` — ML-exit scores, полученные моделью, обученной на `train_core`.

### 11. Расчёт метрик и selection

Для каждой строки считается summary через:

```python
rich._summary_for_filter(trades, run, "locked_test")
```

Она использует метрики из старого runner-а, включая:

- `n_trades`;
- `gross_profit`;
- `gross_loss`;
- `pf`;
- `max_drawdown_r`;
- `win_rate`;
- `ambiguous_same_bar_rate`;
- `bs_p05`;
- `negative_years`;
- `pf_without_best_year`;
- `effective_profit_years`.

Дополнительно сохраняются:

- per-trade rows;
- yearly metrics;
- BUY/SELL side metrics;
- selection table.

Selection не выбирает нового winner-а. Она только помечает каждую заранее заданную строку по gates:

- `PF >= 1.20`;
- `BS p05 >= 1.00`;
- `n_trades >= 100`.

### 12. Записанные артефакты

Harness записывает:

- `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`;
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_summary.csv`;
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`;
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_yearly.csv`;
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_side.csv`;
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_selection.csv`.

JSON содержит:

- source paths;
- SHA256 для source rules CSV, source M5 artifact, locked_test CSV, H1 OHLC, M5 OHLC;
- execution contract;
- split roles;
- current search budget;
- rule count;
- kept candidates;
- best PF / best BS p05;
- links на CSV artifacts.

### 13. Что не делалось

- Не запускался full-grid на `locked_test`.
- Не выбирался новый winner по `locked_test`.
- Не пересчитывались `score_cutoff_on_val_select` по `locked_test`.
- Не добавлялись новые profiles/models/targets/filters.
- Не менялись `entry_id`, `stop_policy_id`, `mask_id`, `exit_id`, `spread`.
- Не выполнялся MT4/tester parity.
- Не выполнялся locked-test stress-spread disclosure.

## Artifacts

- `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_summary.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_yearly.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_side.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_selection.csv`

Structured artifact содержит SHA256 для source rules CSV, source M5 artifact, locked_test CSV, H1 OHLC и M5 OHLC.

## Results

| Rank | Profile | Model | Target | Filter | Trades | PF | BS p05 | Max DD | SL Rate |
|---:|---|---|---|---|---:|---:|---:|---:|---:|
| 1 | time_only | linear | target_entry_ev_regression | top30 | 1207 | 3.3667 | 2.8299 | 8.0132 | 0.0257 |
| 2 | time_only | linear | target_entry_ev_regression | top40 | 1782 | 3.0922 | 2.7632 | 5.7820 | 0.0286 |
| 3 | time_only | linear | target_entry_ev_regression | top50 | 2214 | 3.1649 | 2.8805 | 6.8507 | 0.0330 |
| 4 | time_only | linear | target_entry_good_0_5r | top40 | 1707 | 3.2880 | 2.9239 | 8.3891 | 0.0287 |
| 5 | time_only | linear | target_entry_avoid_sl | top30 | 1196 | 3.2957 | 2.8492 | 5.6398 | 0.0284 |
| 6 | time_only | linear | target_entry_good_0_5r | top50 | 2235 | 3.0649 | 2.6998 | 6.8507 | 0.0327 |
| 7 | movement_plus_time | linear | target_entry_good_0_5r | top40 | 549 | 2.8500 | 2.2696 | 5.2798 | 0.0291 |
| 8 | movement_plus_time | linear | target_entry_good_0_5r | top30 | 418 | 2.6747 | 2.0340 | 4.4975 | 0.0359 |
| 9 | time_only | hist_gradient_boosting | target_entry_good_0_5r | top50 | 2265 | 2.8957 | 2.6221 | 7.6578 | 0.0468 |
| 10 | movement_plus_time | linear | target_entry_ev_regression | top50 | 241 | 2.6939 | 1.9273 | 3.3695 | 0.0373 |
| 11 | movement_plus_time | linear | target_entry_good_0_5r | top50 | 693 | 3.1125 | 2.6128 | 5.8921 | 0.0289 |

Selection:

- `KEEP_CANDIDATE`: 11
- `REJECT`: 0
- gate: `PF >= 1.20`, `BS p05 >= 1.00`, `n_trades >= 100`

Side PF range:

- BUY: `3.6196` - `5.1218`
- SELL: `1.9485` - `3.0798`

Yearly minimum PF by rule is positive for all 11 rules. The weakest yearly PF is `1.9938`.

## Conclusions

1. Все 11 fixed normalized rich-entry rules passed locked_test PF/BS/sample-size gates.
2. Best locked_test PF: `3.3667` (`rank01_time_only_linear_target_entry_ev_regression_top30`).
3. Lowest locked_test PF among the 11 rules: `2.6747` (`rank08_movement_plus_time_linear_target_entry_good_0_5r_top30`).
4. BUY and SELL sides are both profitable by PF; SELL is weaker but not failed.
5. Статус не выше `candidate_check_required`, потому что перед повышением статуса нужны независимый audit, MT4/tester parity, stress-spread locked-test disclosure и model card.

## Limitations / Open Questions

- Для `movement_plus_time` locked-test movement scores восстановлены через frozen movement protocol, потому что source freeze scores не содержат `locked_test`.
- ML-exit и rich-entry модели обучаются заново на `train_core`; checkpoint bundle не сохранялся в source artifacts.
- M5 используется только для порядка исполнения внутри H1-свечи, не как источник признаков.
- MT4/tester parity для нового locked-test периода ещё не выполнен.
- Stress-spread на `locked_test` ещё не пересчитан.

## Split Disclosure

- `train_core`: обучение ML-exit и rich-entry моделей.
- `val_select`: source split для frozen cutoffs; в этом запуске не используется для нового выбора.
- `locked_test`: `DATA/Nero_XAUUSD_test_labeled.csv`, `2022-12-02` - `2026-06-04`, `9463` строк.
- `sample_size_gate`: пройден всеми 11 правилами.
- `locked_test` не использовался для выбора winner-а, порогов, признаков, моделей или фильтров.

## Multiple Testing Context

- current_search_budget: `11 fixed rules x 1 locked_test split x 1 canonical spread x 1 M5 execution convention`.
- cumulative_search_budget: inherited from Fractal0 research arc; source rules выбраны в широком validation research-контуре, поэтому результат требует candidate audit, а не немедленного trading status.

## Next Step

Провести независимый аудит `ML/reports/fractal0_fixed11_rich_entry_locked_test.json` и связанных CSV, затем при отсутствии блокеров выполнить MT4/tester parity и оформить model card.

## Related Materials

- Fixed rules: `ML/reports/leaderboard_closure_audit_rules.csv`
- Source M5 execution contract: `ML/reports/fractal0_stop_grid_m5.json`
- Source rich-entry runner: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Locked-test harness: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`
- Locked-test data: `DATA/Nero_XAUUSD_test_labeled.csv`
- M5 OHLC: `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`
