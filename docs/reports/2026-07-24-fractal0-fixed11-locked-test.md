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
