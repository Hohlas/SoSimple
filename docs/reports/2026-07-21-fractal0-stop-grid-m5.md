# Fractal0 Stop Grid M5

> **Дата**: 2026-07-21
> **Статус**: Completed
> **Вердикт**: RESEARCH_ONLY
> **Цель**: Проверить, даёт ли stop-policy grid перспективную альтернативу текущей Fractal0 E1/E2/E3 entry/exit механике с M5 execution ordering, без открытия `locked_test` и без полного stress-spread на этапе выбора.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-21-fractal0-stop-grid-m5.md`

## Context

Предыдущий полный M5 Fractal0 entry/exit grid выбрал
`E3_open_pullback_1_0atr / M0_no_mask / X0_fixed_r_0_7` с `val_eval
PF=2.7247`, `BS_p05=2.4868`, stress PF `2.2945`. После анализа сделок
возникла гипотеза, что текущий stop часто слишком близок к цене входа:
`0.5 ATR` от entry/fractal anchor может выбивать позицию до проявления E3.

Этот этап является поисковым. Он расширяет stop policy, но не открывает
`locked_test`; результат не может быть торговым кандидатом.

## Уровень Этапа

Уровень: поисковый `research_only`.

Разрешено:

- выбирать winner только по `val_select`;
- проверять выбранный ключ на `val_eval`;
- сравнивать stop policies как исследовательскую гипотезу.

Запрещено:

- открывать `locked_test`;
- делать вывод `candidate`, `tradable`, `live-ready`, `production`;
- запускать полный stress-spread как часть выбора winner.

## What Was Done

- Добавлена stop-policy сетка:
  - `S0_current_0_5`;
  - `S1_fractal0_buffer_0_5_entry_floor_1`;
  - `S2_fractal0_buffer_0_5_entry_floor_2`;
  - `S3_fractal0_buffer_0_5_entry_floor_3`.
- `stop_policy_id` добавлен в `run_config_hash`, `resume_key`, summary,
  trades, JSON artifact, permutation key, winner eval, attribution и
  rule/trade matching.
- ML-exit обучается отдельно для каждой `stop_policy_id`, потому что меняются
  `R`, признаки в `R` и `target_exit_*`.
- Добавлен `--exit-shortlist stop_grid` с `X0_fixed_r_0_7`, X1/X2/X3
  threshold exits и `X7_time_6/12`.
- Добавлен `--skip-stress-spread`; полный stress-spread записан как
  `stress_spread_status = deferred_shortlist_only`.
- Добавлен файл stop diagnostics:
  `ML/reports/fractal0_stop_grid_m5_stop_diagnostics.csv`.

Команда полного запуска:

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

## Multiple Testing Context

Current search budget из JSON artifact:

| Поле | Значение |
|---|---:|
| selection_cells | 288 |
| expected_completed_without_stress | 576 |
| stress_cells | 0 |
| ml_exit_model_jobs | 48 |
| permutation_repeats | 200 |

Формула selection cells:

```text
4 stop policies x 3 entries x 2 masks x 12 exits = 288
```

Фактический progress:

```text
completed = 576
failed = 0
```

Permutation:

| Поле | Значение |
|---|---:|
| method | `block_shuffled_val_select_pnl_r` |
| grouping | `year+side_when_available` |
| observed_winner_bs_p05 | 3.032558 |
| null_repeats | 200 |
| empirical_p_value | 0.004975 |
| status | PASS |
| metric_bootstrap_samples | 200 |

Cumulative search budget: `disclosed_current_stage_only`. Это значит, что
ширина прошлых Fractal0 этапов раскрыта в истории проекта, но этот artifact
не претендует на полный глобальный счёт всех предыдущих гипотез.

## Changed Files

- `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- `tests/test_fractal0_entry_exit_grid.py`
- `docs/ML/benchmark_fractal0_entry_exit_grid.py.md`
- `docs/reports/2026-07-21-fractal0-stop-grid-m5.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `MODULE_INDEX.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

## Verification

Кодовые проверки:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Результат: `41 passed`.

Полный тестовый набор до последней малой правки summary:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Результат: `1332 passed, 52 warnings`.

Smoke run:

```text
preflight PASS
finished fractal0_entry_exit_grid
```

Полный stop-grid run:

```text
progress done_runs=576/576
finished fractal0_entry_exit_grid
```

Structured artifact содержит:

- `locked_test = not_opened`;
- `winner_selection_key = stop_policy_id + entry_id + mask_id + exit_id`;
- `permutation_key = stop_policy_id + entry_id + mask_id + exit_id`;
- `stress_spread_status = deferred_shortlist_only`;
- `stress_spread_interpretation = configured_but_not_computed`;
- `fixed_risk_interpretation = pnl_r assumes equal risk per trade, not equal lot size`.

## Results

Winner выбран только на `val_select`:

```text
S2_fractal0_buffer_0_5_entry_floor_2 /
E3_open_pullback_1_0atr /
M0_no_mask /
X2_ml_opposite_any_p0_50
```

`val_select` winner metrics:

| Метрика | Значение |
|---|---:|
| n_trades | 2294 |
| PF | 3.329117 |
| BS_p05 | 3.032558 |
| mean_pnl_r | 0.351106 |
| max_drawdown_r | 6.821666 |
| pf_without_best_year | 2.980603 |
| effective_profit_years | 2.195784 |
| risk_distance_atr | 2.000000 |

`val_eval` проверка того же winner:

| Метрика | Значение |
|---|---:|
| n_trades | 2298 |
| PF | 2.787295 |
| BS_p05 | 2.508541 |
| mean_pnl_r | 0.288315 |
| max_drawdown_r | 8.385976 |
| pf_without_best_year | 2.742403 |
| effective_profit_years | 1.979596 |
| ambiguous_same_bar_rate | 0.000000 |
| risk_distance_atr | 2.000000 |

Лучшие `val_select` строки по `stop_policy_id`:

| stop_policy_id | entry | mask | exit | PF | BS_p05 | risk_distance_atr | tp_distance_atr |
|---|---|---|---|---:|---:|---:|---:|
| S0_current_0_5 | E3 | M0 | X0_fixed_r_0_7 | 2.912718 | 2.695315 | 0.500000 | 0.350000 |
| S1_fractal0_buffer_0_5_entry_floor_1 | E3 | M0 | X2_ml_opposite_any_p0_55 | 2.943125 | 2.666621 | 1.000000 | n/a |
| S2_fractal0_buffer_0_5_entry_floor_2 | E3 | M0 | X2_ml_opposite_any_p0_50 | 3.329117 | 3.032558 | 2.000000 | n/a |
| S3_fractal0_buffer_0_5_entry_floor_3 | E3 | M0 | X2_ml_opposite_any_p0_50 | 2.717382 | 2.463476 | 3.000000 | n/a |

Лучшие `val_eval` строки по `stop_policy_id` как диагностическое сравнение,
не как правило выбора:

| stop_policy_id | entry | mask | exit | PF | BS_p05 | risk_distance_atr |
|---|---|---|---|---:|---:|---:|
| S0_current_0_5 | E3 | M0 | X0_fixed_r_0_7 | 2.724686 | 2.512015 | 0.500000 |
| S1_fractal0_buffer_0_5_entry_floor_1 | E1 | M0 | X2_ml_opposite_any_p0_55 | 2.398903 | 2.157680 | 1.000000 |
| S2_fractal0_buffer_0_5_entry_floor_2 | E1 | M0 | X2_ml_opposite_any_p0_50 | 2.941545 | 2.688693 | 2.000000 |
| S3_fractal0_buffer_0_5_entry_floor_3 | E1 | M0 | X2_ml_opposite_any_p0_50 | 2.424299 | 2.188463 | 3.000000 |

Сравнение с предыдущим полным M5 S0/current:

- прежний M5 full winner `S0` был фактически тем же текущим stop:
  `E3 / M0 / X0_fixed_r_0_7`;
- прежний full-run artifact содержит `val_eval PF=2.724686`,
  `BS_p05=2.486754`, stress PF `2.294511`;
- в текущем stop-grid summary та же S0 baseline строка имеет
  `val_eval PF=2.724686`, `BS_p05=2.512015`;
- новый stop-grid winner `S2/E3/M0/X2 p0.50` даёт `val_eval PF=2.787295`,
  `BS_p05=2.508541`;
- по PF новый winner выше S0 baseline, но по более консервативной метрике
  `BS_p05` он практически равен и чуть ниже текущей S0 baseline строки
  (`2.508541` против `2.512015`);
- полный stress-spread не выполнен, поэтому это перспективная гипотеза, а не
  доказанное превосходство и не замена frozen rule.

Stop diagnostics на `val_eval` ниже — это `all-grid simulated trade rows`,
то есть агрегат по всем симуляциям сетки для соответствующей stop policy, а
не число уникальных сделок winner-а:

| stop_policy_id | stop_source | n_trades | SL-rate | median_stop_distance_atr | mean_r_value |
|---|---|---:|---:|---:|---:|
| S0_current_0_5 | current_entry_or_fractal_anchor | 99996 | 0.574963 | 0.500000 | 3.562233 |
| S1_fractal0_buffer_0_5_entry_floor_1 | entry_floor | 82128 | 0.490296 | 1.000000 | 4.604383 |
| S1_fractal0_buffer_0_5_entry_floor_1 | fractal0_buffer | 17868 | 0.384822 | 1.469231 | 8.060846 |
| S2_fractal0_buffer_0_5_entry_floor_2 | entry_floor | 95532 | 0.347611 | 2.000000 | 9.103731 |
| S2_fractal0_buffer_0_5_entry_floor_2 | fractal0_buffer | 4464 | 0.283602 | 2.714223 | 13.645054 |
| S3_fractal0_buffer_0_5_entry_floor_3 | entry_floor | 98292 | 0.241424 | 3.000000 | 13.602368 |
| S3_fractal0_buffer_0_5_entry_floor_3 | fractal0_buffer | 1704 | 0.196009 | 3.643967 | 18.329930 |

Focused stop diagnostics на `val_eval`:

| diagnostic_scope | stop_source | n_trades | SL-rate | median_stop_distance_atr | mean_r_value |
|---|---|---:|---:|---:|---:|
| winner_S2_E3_M0_X2 | entry_floor | 2183 | 0.059551 | 2.000000 | 9.094732 |
| winner_S2_E3_M0_X2 | fractal0_buffer | 115 | 0.078261 | 2.726316 | 13.663565 |
| baseline_S0_E3_M0_X0 | current_entry_or_fractal_anchor | 2298 | 0.201044 | 0.500000 | 3.517032 |

Rejected alternatives в JSON artifact:

| alternative_id | split | rule | PF | BS_p05 | reason |
|---|---|---|---:|---:|---|
| current_s0_fixed_r_baseline | val_eval | S0/E3/M0/X0 | 2.724686 | 2.512015 | baseline retained for comparison; not selected by stop-grid val_select winner key |
| s1_neighbor_same_family | val_select | S1/E3/M0/X2 p0.55 | 2.943125 | 2.666621 | neighbor stop policy had lower val_select BS_p05 than S2 winner |
| s3_neighbor_same_key | val_select | S3/E3/M0/X2 p0.50 | 2.717382 | 2.463476 | wider stop reduced SL rate but had lower val_select BS_p05 than S2 |
| diagnostic_best_val_eval_s2_e1 | val_eval | S2/E1/M0/X2 p0.50 | 2.941545 | 2.688693 | best S2 row on val_eval is diagnostic-only; winner selection is restricted to val_select |

## Conclusions

Гипотеза о слишком близком текущем stop получила частичную поддержку на
validation: `S2` победил на `val_select` и сохранил сильный PF на `val_eval`,
но не доказал явного превосходства над текущим `S0/X0` baseline по
консервативной метрике `BS_p05`.

Самый важный практический вывод не в том, что `S2` можно торговать, а в том,
что stop policy является существенной частью исследуемой механики. Её нельзя
считать вторичной настройкой после выбора entry/exit: она меняет `R`,
ML-exit targets, признаки и итоговый ranking.

`S3` снижает SL-rate сильнее, но хуже `S2` по `BS_p05`. Это похоже на
компромисс: слишком широкий stop уменьшает частоту SL, но может размывать
`R`-нормированные преимущества.

## Limitations / Open Questions

- Полный stress-spread намеренно не запускался:
  `stress_spread_status = deferred_shortlist_only`.
- `locked_test` не открыт: `locked_test = not_opened`.
- Winner выбран после новой validation-сетки, поэтому результат не является
  frozen candidate.
- `pnl_r` предполагает одинаковый риск на сделку, а не одинаковый фиксированный
  лот. При фиксированном лоте широкий stop меняет денежный риск.
- `val_eval` лучшие строки по каждой stop policy приведены только как
  диагностика; winner выбирался по `val_select`.
- `M1_frozen_movement_top5` является control-only в этом прогоне: на
  `val_eval` у M1 минимум `9` сделок, медиана `11`, у E3 во всех M1
  строках `9` сделок. M1 нельзя сравнивать с M0 как равный по размеру sample.
- `ML/reports/fractal0_stop_grid_m5_yearly.csv` является общим yearly
  агрегатом по all-grid simulated trade rows. Для winner использовать
  `ML/reports/fractal0_stop_grid_m5_winner_yearly.csv`; для явного all-grid
  имени добавлен alias `ML/reports/fractal0_stop_grid_m5_all_grid_yearly.csv`.
- Нет model card, потому что кандидат не принят.
- Scale/normalization audit не применим: runner использует табличный
  `ExtraTreesClassifier` без отдельного scaler.

## Validation Split Disclosure

Split contract:

- `train_core`: обучение ML-exit;
- `val_select`: выбор stop/entry/mask/exit winner;
- `val_eval`: проверка уже выбранного ключа;
- `locked_test`: `not_opened`.

Raw rows до entry:

| split | raw_rows_before_entry |
|---|---:|
| train_core | 44159 |
| val_select | 13296 |
| val_eval | 13296 |

Для winner `S2/E3/M0/X2 p0.50`:

| split | trades |
|---|---:|
| val_select | 2294 |
| val_eval | 2298 |

Sample size gate по числу сделок проходит минимальный порог `>=300`, но статус
не повышается выше `research_only`, потому что правило найдено в новом
validation search.

## Research-first Disclosure

```text
lifecycle_status: research_hypothesis
origin_bias: validation_grid_search
research_priority: stop_policy_follow_up
current_search_budget: 288 selection cells, 48 ML-exit jobs, 200 permutation repeats
cumulative_search_budget: disclosed_current_stage_only
next_probe_freeze: shortlist stress-spread and bounded pre-registered follow-up
allowed_max_verdict: research_only
forbidden_interpretations: production ready, live-ready, tradable, ready_for_locked_test
```

Почему PF/PnL здесь не торговый вывод:

- winner выбран после расширения validation search;
- полный stress-spread отложен;
- `locked_test` не открыт;
- нет замороженного правила для проверочного цикла.

## Next Step

Следующий допустимый шаг: shortlist-only stress-spread для небольшого набора:

- текущий stop-grid winner `S2/E3/M0/X2 p0.50`;
- прежний M5 full baseline `S0/E3/M0/X0_fixed_r_0_7`;
- ближайшие stop-policy соседи `S1` и `S3` по тому же entry/mask/exit family.

После этого можно решать, есть ли смысл в отдельном frozen-плане. Открывать
`locked_test` по текущему результату нельзя.

## Related Materials

- `docs/superpowers/plans/2026-07-21-fractal0-stop-grid-m5.md`
- `docs/reports/2026-07-21-fractal0-entry-exit-grid.md`
- `ML/reports/fractal0_stop_grid_m5.json`
- `ML/reports/fractal0_stop_grid_m5_summary.csv`
- `ML/reports/fractal0_stop_grid_m5_stop_diagnostics.csv`
- `ML/reports/fractal0_stop_grid_m5_focused_stop_diagnostics.csv`
- `ML/reports/fractal0_stop_grid_m5_permutation.csv`
- `ML/reports/fractal0_stop_grid_m5_all_grid_yearly.csv`
- `ML/reports/fractal0_stop_grid_m5_trades.csv`
- `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- `tests/test_fractal0_entry_exit_grid.py`
