# Fractal0 Entry Quality Filter

> **Дата**: 2026-07-21
> **Статус**: Completed
> **Вердикт**: RESEARCH_ONLY
> **Цель**: Проверить, может ли pre-order ML-entry фильтр для `E3_open_pullback_1_0atr` улучшить stop-grid winner без открытия `locked_test`, с выбором cutoff только на `val_select`.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-21-fractal0-entry-quality-filter.md`

## Context

Предыдущий stop-grid M5 этап выбрал:

```text
S2_fractal0_buffer_0_5_entry_floor_2 /
E3_open_pullback_1_0atr /
M0_no_mask /
X2_ml_opposite_any_p0_50
```

Этот этап проверил, можно ли до отправки limit-заявки ранжировать E3 сигналы
по ожидаемому качеству будущей сделки. Аудит промежуточного отчёта выявил две
проблемы: simple top50 baselines выбирали 0 сделок из-за NaN cutoff, а feature
contract был описан как entry-time, хотя часть признаков бралась из post-fill
полей. После исправления runner пересчитан заново.

Этап поисковый. `locked_test` не открыт, результат не является торговым
кандидатом.

## Уровень Этапа

Уровень: поисковый `research_only`.

Разрешено:

- обучать ML-exit и ML-entry на `train_core`;
- выбирать filter family и topX только на `val_select`;
- проверять зафиксированный cutoff на `val_eval`.

Запрещено:

- открывать `locked_test`;
- пересчитывать topX/cutoff на `val_eval`;
- делать вывод `candidate`, `tradable`, `live-ready`, `production`;
- использовать будущие PnL/exit/outcome поля как признаки entry-модели.

## What Was Done

- Создан `ML/baseline/benchmark_fractal0_entry_quality_filter.py`.
- Добавлен registry из 17 фильтров:
  `M0_no_mask`, movement top50/30/20/10, simple stop-distance top50/30,
  simple r-value top50/30, `entry_quality` top50/30/20/10 и
  `entry_avoid_sl` top50/30/20/10.
- Entry labels построены по фактическим E3 сделкам на `train_core`:
  `target_entry_good = pnl_r > 0`, `target_entry_avoid_sl = close_reason != "SL"`.
- Entry features переведены на pre-order planned contract:
  `side_buy`, `ATR`, `entry_to_fractal0_atr`, `stop_distance_atr`,
  `r_value_atr` считаются от planned limit/stop/R полей, а не от post-fill
  outcome.
- Simple topX cutoff считается только по строкам с валидным score, поэтому
  top50 больше не может схлопнуться в 0 из-за NaN.
- JSON artifact расширен top-level полями `status`, `verdict`,
  `lifecycle_status`, `split_roles`, `forbidden_interpretations`,
  `entry_feature_columns`, `entry_label_contract`, `filter_contract` и
  score distribution diagnostics.

Команда полного запуска:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_entry_quality_filter \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id S2_fractal0_buffer_0_5_entry_floor_2 \
  --permutation-repeats 200
```

## Multiple Testing Context

Current search budget из JSON artifact:

| Поле | Значение |
|---|---:|
| filters | 17 |
| splits | 2 |
| completed | 34 |
| permutation_repeats | 200 |

Search space:

```text
1 stop policy x 1 entry x 1 mask x 1 exit x 17 filters = 17 selection cells
```

Parent search budget inherited from stop-grid:

- stop-grid selection cells: `288`;
- stop-grid completed without stress: `576`;
- stop-grid winner used here: `S2/E3/M0/X2_ml_opposite_any_p0_50`.

Permutation:

| Поле | Значение |
|---|---:|
| method | `block_shuffled_val_select_pnl_r` |
| observed_winner_bs_p05 | 3.937030 |
| null_repeats | 200 |
| empirical_p_value | 0.059701 |
| status | PASS |

Permutation PASS относится только к `val_select` selection process. Он не
отменяет факт, что выбранный filter провалился на `val_eval` по `BS_p05`.

## Changed Files

- `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- `tests/test_fractal0_entry_quality_filter.py`
- `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
- `docs/reports/2026-07-21-fractal0-entry-quality-filter.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `MODULE_INDEX.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

## Verification

TDD checks added for:

- filter registry;
- topX/cutoff behavior;
- NaN-safe top fraction selection;
- label definitions;
- feature contract excluding future/target columns;
- planned direction/distance features;
- model train/score smoke;
- val_select cutoff reuse on val_eval;
- empty trade summary.

Smoke run:

```text
preflight PASS
finished fractal0_entry_quality_filter
```

Full corrected run:

```text
preflight PASS
finished fractal0_entry_quality_filter
```

Structured checks:

- `locked_test = not_opened`;
- `status = completed`;
- `verdict = research_only`;
- `lifecycle_status = research_hint`;
- `summary_shape = (34, 30)`;
- `splits = {'val_select': 17, 'val_eval': 17}`;
- simple top50 rows are non-zero;
- input hashes include H1, M5, train, validation, movement freeze and stop-grid artifact.

## Results

Winner выбран только на `val_select`:

```text
entry_quality_top10
score_cutoff_on_val_select = 0.36753163277225726
```

`val_select` winner metrics:

| Метрика | Значение |
|---|---:|
| n_trades | 196 |
| PF | 5.496736 |
| BS_p05 | 3.937030 |
| mean_pnl_r | 0.483193 |
| max_drawdown_r | 2.061307 |
| win_rate | 0.581633 |
| selected_fraction | 0.085440 |
| SL-rate | 0.030612 |

`val_eval` проверка того же cutoff:

| Метрика | Значение |
|---|---:|
| n_trades | 53 |
| PF | 1.954347 |
| BS_p05 | 0.971312 |
| mean_pnl_r | 0.167059 |
| max_drawdown_r | 2.582476 |
| win_rate | 0.433962 |
| selected_fraction | 0.023064 |
| SL-rate | 0.094340 |
| pf_without_best_year | 1.883326 |
| effective_profit_years | 1.468471 |

No-mask baseline in this same run:

| Split | n_trades | PF | BS_p05 | mean_pnl_r | max_drawdown_r | SL-rate |
|---|---:|---:|---:|---:|---:|---:|
| val_select | 2294 | 3.203460 | 2.909425 | 0.339555 | 7.810379 | 0.052746 |
| val_eval | 2298 | 2.531716 | 2.286458 | 0.263844 | 9.135903 | 0.062663 |

Previous S0/X0 baseline from stop-grid `val_eval`:

| Rule | n_trades | PF | BS_p05 | mean_pnl_r | max_drawdown_r |
|---|---:|---:|---:|---:|---:|
| S0/E3/M0/X0_fixed_r_0_7 | 2298 | 2.724686 | 2.512015 | 0.350482 | 7.300000 |

Top `val_select` filters by `BS_p05`:

| filter_id | n_trades | PF | BS_p05 | selected_fraction | SL-rate |
|---|---:|---:|---:|---:|---:|
| entry_quality_top10 | 196 | 5.496736 | 3.937030 | 0.085440 | 0.030612 |
| entry_avoid_sl_top30 | 648 | 4.751115 | 3.897698 | 0.282476 | 0.040123 |
| entry_avoid_sl_top20 | 426 | 4.623661 | 3.640701 | 0.185702 | 0.032864 |
| entry_quality_top30 | 630 | 4.243969 | 3.612710 | 0.274629 | 0.065079 |
| entry_quality_top20 | 411 | 4.634219 | 3.584640 | 0.179163 | 0.060827 |

Best `val_eval` rows are diagnostic only:

| filter_id | n_trades | PF | BS_p05 | selected_fraction | SL-rate |
|---|---:|---:|---:|---:|---:|
| entry_avoid_sl_top50 | 932 | 2.993090 | 2.510392 | 0.405570 | 0.066524 |
| entry_quality_top50 | 995 | 2.818962 | 2.406599 | 0.432985 | 0.069347 |
| entry_quality_top30 | 485 | 3.003092 | 2.357128 | 0.211053 | 0.074227 |
| simple_r_value_top50 | 1146 | 2.697953 | 2.335049 | 0.498695 | 0.068935 |
| simple_r_value_top30 | 984 | 2.695823 | 2.321801 | 0.428198 | 0.074187 |
| M0_no_mask | 2298 | 2.531716 | 2.286458 | 1.000000 | 0.062663 |

Simple baseline sanity check after fix:

| filter_id | Split | n_trades | BS_p05 |
|---|---|---:|---:|
| simple_stop_distance_top50 | val_select | 1481 | 2.983099 |
| simple_stop_distance_top30 | val_select | 731 | 2.830909 |
| simple_r_value_top50 | val_select | 1135 | 2.977655 |
| simple_r_value_top30 | val_select | 708 | 3.145100 |

Winner yearly on `val_eval`:

| year | n_trades | PF | mean_pnl_r | max_drawdown_r | win_rate |
|---|---:|---:|---:|---:|---:|
| 2021 | 10 | 2.303609 | 0.204378 | 1.010205 | 0.500000 |
| 2022 | 43 | 1.883326 | 0.158380 | 2.582476 | 0.418605 |

Score distribution diagnostics are saved in:

```text
ML/reports/fractal0_entry_quality_filter_score_diagnostics.csv
```

Key warning: `entry_quality_score` p90 shifts from `0.367532` on
`val_select` to `0.364440` on `val_eval`, so the selected top10 cutoff leaves
only `2.31%` of filled `val_eval` trades.

## Conclusions

The corrected result is weaker than the first report.

Facts:

- `entry_quality_top10` wins on `val_select` by `BS_p05`.
- Permutation over `val_select` selection is PASS: `p=0.059701`.
- On `val_eval`, the frozen cutoff leaves only `53` trades.
- On `val_eval`, winner PF is lower than no-mask: `1.9543` vs `2.5317`.
- On `val_eval`, winner `BS_p05` is much lower than no-mask: `0.9713` vs `2.2865`.
- On `val_eval`, winner also loses to previous S0/X0 baseline: `BS_p05=0.9713` vs `2.5120`.

Correct interpretation: the entry-quality score has a strong `val_select`
ranking trace, but the selected rule does not survive `val_eval`. This is
`research_hint`, not a frozen rule and not a candidate.

## Limitations / Open Questions

- No full stress-spread was run for this entry-quality shortlist.
- The selected top10 rule is too narrow on `val_eval`: only `53` trades.
- Fixed cutoff caused a large fraction shift: `8.54%` filled trades on
  `val_select` versus `2.31%` on `val_eval`.
- Diagnostic `val_eval` rows such as `entry_avoid_sl_top50` and
  `entry_quality_top50` look stronger, but they were not selected on
  `val_select`; they cannot replace winner after seeing `val_eval`.
- Simple baselines are now technically valid, and they remain competitive:
  `simple_r_value_top50` has `val_eval BS_p05=2.3350`, above no-mask and far
  above the selected winner.
- `locked_test` remains closed.

## Validation Split Disclosure

Splits:

- `train_core`: trains ML-exit and ML-entry;
- `val_select`: selects filter family and cutoff;
- `val_eval`: checks the selected filter without recalculating cutoff;
- `locked_test`: `not_opened`.

Sample sizes before entry-quality filtering:

| Split | E3 rows | Filled trades |
|---|---:|---:|
| train_core | 44159 | 21343 |
| val_select | 4731 | 2294 |
| val_eval | 4732 | 2298 |

Winner after filtering:

| Split | Trades |
|---|---:|
| val_select | 196 |
| val_eval | 53 |

## Next Step

Do not open `locked_test` from this result.

The current selected rule should not move forward as a frozen rule. A valid
next plan would be a new bounded shortlist/stress probe with pre-registered
controls:

- `S0/E3/M0/X0_fixed_r_0_7`;
- `S2/E3/M0/X2/M0_no_mask`;
- selected `S2/E3/M0/X2/entry_quality_top10` as a failed winner disclosure;
- at most a small pre-registered diagnostic shortlist such as
  `entry_avoid_sl_top50`, `entry_quality_top50`, `simple_r_value_top50`.

The plan must define a minimum selected trade count and a calibration rule
before looking at new data.

## Related Materials

- `docs/superpowers/plans/2026-07-21-fractal0-entry-quality-filter.md`
- `docs/superpowers/audit.md`
- `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- `ML/reports/fractal0_entry_quality_filter.json`
- `ML/reports/fractal0_entry_quality_filter_summary.csv`
- `ML/reports/fractal0_entry_quality_filter_score_diagnostics.csv`
- `ML/reports/fractal0_entry_quality_filter_yearly.csv`
- `docs/reports/2026-07-21-fractal0-stop-grid-m5.md`
- `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
