# Fractal0 Entry/Exit Grid

> **Дата**: 2026-07-21
> **Статус**: Completed
> **Вердикт**: RESEARCH_ONLY
> **Цель**: выполнить полный research-прогон Fractal0 entry/exit grid с OHLC-симуляцией сделок, ML-exit обучением, stress-spread и коррекцией множественного перебора.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-20-fractal0-entry-exit-grid.md`, `docs/superpowers/specs/2026-07-20-fractal0-entry-exit-grid-design.md`

## Context

Этап продолжает ветку Fractal0 price entry mechanics и проверяет уже не только
механику входа, а полную связку `entry -> fill -> exit -> PnL` на H1 OHLC.
Это поисковый research-этап, а не проверочный candidate-cycle.

`locked_test` не открыт. Максимально допустимый вывод этапа:
`allowed_max_verdict = research_only`.

Запрещённые интерпретации: production ready, live-ready, tradable,
готовность к торговому запуску, разрешение открыть `locked_test`.

## What Was Done

- Добавлен runner `ML/baseline/benchmark_fractal0_entry_exit_grid.py`.
- Реализована сетка `4 entry rules x 2 masks x 48 exits = 384`
  canonical-spread конфигурации.
- Выполнен stress-spread disclosure для `384` конфигураций.
- Обучен ML-exit слой: `4` target family x `3` seed = `12` model jobs.
- Выполнена OHLC-симуляция сделок с Bid/Ask convention и `SL first` для
  TP+SL внутри одной H1-свечи.
- Исправлена перестановочная коррекция: вместо синтетического сэмплирования
  `summary.bs_p05` теперь перемешиваются реальные `pnl_r` внутри `val_select`
  с группировкой `year+side_when_available`, затем заново выбирается winner.
- Post-review добавлен `execution_ohlc_path` для M5 execution ordering и
  исправлена ошибка `ambiguous_same_bar_rate`: для ML-exit правил больше не
  считается гипотетический fixed TP `0.7R`, если TP не является реальным
  условием выхода.
- После этого выполнен полный M5 full-grid rerun на тех же `384`
  canonical-spread конфигурациях и `384` stress-spread конфигурациях. Текущий
  канонический full-grid artifact: `ML/reports/fractal0_entry_exit_grid_m5_full.json`.

## Multiple Testing Context

Current search budget:

- `selection_cells = 384`;
- `stress_cells = 384`;
- `ml_exit_model_jobs = 12`;
- `permutation_repeats = 200`.

Cumulative search budget в артефакте раскрыт как
`disclosed_current_stage_only`; полный сквозной бюджет предыдущих research
циклов не пересчитан, поэтому результат не может быть выше `research_only`.

Перестановочная коррекция:

- method: `block_shuffled_val_select_pnl_r`;
- null repeats: `200`;
- empirical p-value: `0.004975124378109453`;
- status: `PASS`;
- metric bootstrap samples: `20`.

`metric_bootstrap_samples = 20` — практичное ограничение пересчёта итоговой
коррекции после полного прогона. Это лучше первичной ошибочной реализации,
которая сэмплировала агрегаты `summary`, но не является поводом повышать
verdict выше `research_only`.

В полном M5 full-grid rerun permutation correction пересчитана с
`metric_bootstrap_samples = 200`; empirical p-value остался
`0.004975124378109453`, status `PASS`.

## Changed Files

- `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- `tests/test_fractal0_entry_exit_grid.py`
- `docs/ML/benchmark_fractal0_entry_exit_grid.py.md`
- `docs/reports/2026-07-21-fractal0-entry-exit-grid.md`
- `ML/reports/fractal0_entry_exit_grid.json`
- `ML/reports/fractal0_entry_exit_grid_summary.csv`
- `ML/reports/fractal0_entry_exit_grid_spread_stress.csv`
- `ML/reports/fractal0_entry_exit_grid_trades.csv`
- `ML/reports/fractal0_entry_exit_grid_yearly.csv`
- `ML/reports/fractal0_entry_exit_grid_m5_winner_winner_yearly.csv`
- `ML/reports/fractal0_entry_exit_grid_attribution.csv`
- `ML/reports/fractal0_entry_exit_grid_permutation.csv`
- `ML/reports/fractal0_entry_exit_grid_progress.json`
- `ML/reports/fractal0_entry_exit_grid_m5_winner.json`
- `ML/reports/fractal0_entry_exit_grid_m5_winner_summary.csv`
- `ML/reports/fractal0_entry_exit_grid_m5_winner_trades.csv`
- `ML/reports/fractal0_entry_exit_grid_m5_full.json`
- `ML/reports/fractal0_entry_exit_grid_m5_full_summary.csv`
- `ML/reports/fractal0_entry_exit_grid_m5_full_spread_stress.csv`
- `ML/reports/fractal0_entry_exit_grid_m5_full_trades.csv`
- `ML/reports/fractal0_entry_exit_grid_m5_full_yearly.csv`
- `ML/reports/fractal0_entry_exit_grid_m5_full_winner_yearly.csv`
- `ML/reports/fractal0_entry_exit_grid_m5_full_attribution.csv`
- `ML/reports/fractal0_entry_exit_grid_m5_full_permutation.csv`
- `ML/reports/fractal0_entry_exit_grid_m5_full_progress.json`

## Verification

Команды:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Результат после review fixes: `32 passed`.

Полный прогон runner-а завершился штатно:

```text
progress done_runs=1152/1152
finished fractal0_entry_exit_grid
```

Проверка артефактов:

- `summary.csv`: `768` строк;
- `spread_stress.csv`: `384` строки;
- `permutation.csv`: `200` строк;
- `progress.completed`: `1152`;
- `progress.failed`: `0`.
- M5 winner-only artifact: `status=PASS`, `scope=previous_winner_only`,
  `execution_ohlc_path=MT/MQL4/Files/XAUUSD_M5_OHLC.csv`.
- Primary JSON теперь содержит `canonical_current_artifact`,
  `post_review_artifacts` и `superseded_fields`, чтобы машинный читатель не
  принял устаревший H1 ambiguity cap за текущий verdict.
- M5 full-grid artifact: `status=PASS`, `progress.completed=1152`,
  `progress.failed=0`, `summary.csv=768` строк,
  `spread_stress.csv=384` строки, `permutation.csv=200` строк.

## Results

Winner выбран на `val_select`:

```text
entry_id = E3_open_pullback_1_0atr
mask_id  = M0_no_mask
exit_id  = X0_fixed_r_0_7
```

Текущий winner полного M5 rerun:

- `val_select`: trades `2294`, PF `2.9127176728597752`,
  BS p05 `2.6717396986296746`, ambiguous same-bar rate
  `0.013513513513513514`;
- `val_eval`: trades `2298`, PF `2.7246860862703013`,
  BS p05 `2.486754106484057`, stress PF `2.2945114989452584`,
  ambiguous same-bar rate `0.0073977371627502175`;
- `val_eval` yearly: 2021 PF `2.649154333064076`, 2022 PF
  `2.791791`; effective profit years `1.985599875865133`;
- exit counts on `val_eval`: `TP=1817`, `SL=462`, `TIME=19`;
- verdict: `PASS / research_only / research_hypothesis`, `locked_test` not opened.

Первичный полный H1-прогон записал такие значения `val_select`:

- trades: `2294`;
- PF: `2.211453757130436`;
- BS p05: `2.006294042924341`;
- ambiguous same-bar rate: `0.2471665213600697`.

Первичный полный H1-прогон записал такие значения `val_eval`:

- trades: `2298`;
- PF: `1.943813746344068`;
- BS p05: `1.7601441464181098`;
- stress PF: `1.5742797668285895`;
- ambiguous same-bar rate: `0.2249782419495213`;
- negative years: `0`;
- PF without best year: `1.938942831108843`;
- effective profit years: `2.0` в первичном artifact было старой семантикой
  "число прибыльных лет", а не формулой концентрации;
- years: `2`.

Итоговый structured verdict:

```text
status = PASS
verdict = research_only
lifecycle_status = diagnostic_only  # устаревший cap первичного H1 artifact
reasons = ["ambiguous_same_bar_rate_gt_0_10"]
```

Post-review winner-only пересчёт с M5 execution ordering:

- `val_select`: trades `2294`, PF `2.211453757130436`,
  BS p05 `2.0062940429243414`, ambiguous same-bar rate `0.0`;
- `val_eval`: trades `2298`, PF `1.943813746344068`,
  BS p05 `1.7601441464181098`, ambiguous same-bar rate `0.0`,
  effective profit years `1.9863777053685452`;
- stress spread `0.40`: trades `2247`, PF `1.5742797668285895`,
  BS p05 `1.4025462198808076`, ambiguous same-bar rate `0.0`.

Полный M5 rerun изменил winner: fixed TP `X0_fixed_r_0_7` стал лучше ML-exit
вариантов. Это ожидаемо для fixed TP exits: M5 уточняет порядок TP/SL внутри
H1-свечи, тогда как первичный H1-only прогон слишком часто применял
консервативное `SL first`.

## Conclusions

Сетка технически выполнена полностью, runner воспроизводим, прогресс и resume
контракт работают, ML-exit слой обучается на `train_core`, а winner выбирается
только на `val_select` и проверяется на `val_eval`.

Первичный вывод `DIAGNOSTIC_ONLY` из-за `ambiguous_same_bar_rate_gt_0_10`
считается устаревшим. Root cause для ML-exit winner: симулятор считал
same-bar ambiguity против гипотетического fixed TP `0.7R` даже для ML-exit
правил, где такого TP нет. Для fixed TP exits M5 full rerun показал другой
эффект: M5 execution ordering существенно улучшает оценку fixed TP вариантов,
потому что часть H1 TP/SL конфликтов разрешается по младшему таймфрейму.

Повышение до candidate всё равно запрещено: это поисковый research-этап,
winner выбран после широкого validation grid-search, а `locked_test` не открыт.

## Limitations / Open Questions

- Primary H1 artifact `fractal0_entry_exit_grid.json` содержит устаревший
  `diagnostic_only` cap по ambiguity. Текущий full-grid источник:
  `ML/reports/fractal0_entry_exit_grid_m5_full.json`.
- Старый полный `_trades.csv` был создан до записи `spread` на уровне каждой
  сделки, поэтому строгий canonical/stress yearly-разрез winner из него не
  восстанавливается. Для текущего M5 winner-only artifact сохранён отдельный
  `fractal0_entry_exit_grid_m5_winner_winner_yearly.csv`.
- `fractal0_entry_exit_grid_yearly.csv` — глобальная диагностика по всем
  конфигурациям/сплитам, не годовой разрез выбранного winner.
- Для fixed TP exits остаётся небольшая настоящая TP/SL ambiguity даже на M5:
  у текущего winner `ambiguous_same_bar_rate=0.0073977371627502175` на
  `val_eval`. Это не блокирующий уровень, но его нужно раскрывать.
- `locked_test` не открыт.
- Cumulative search budget раскрыт только для текущего этапа.
- Primary H1 / winner-only post-review permutation disclosure использовал
  `20` bootstrap-сэмплов на перестановочную метрику. Текущий M5 full-grid
  artifact пересчитан с `200` bootstrap-сэмплами.
- Результат нельзя называть trading candidate.

## Split Disclosure

- `train_core`: обучение ML-exit моделей.
- `val_select`: выбор entry/mask/exit winner.
- `val_eval`: проверка уже выбранного winner.
- `locked_test`: `not_opened`.

Входные артефакты зафиксированы hash-ами в
`ML/reports/fractal0_entry_exit_grid.json`:

- `ohlc`: `4bf7a23ab79f41824713fa881078d06fb84fd7c484b2840c3cdec0bfdfda5aff`;
- `train_core`: `5cc0c1180d96966ac08c4832947be6b2770f1d14b0b572a4f63f0f28b3e49b62`;
- `validation`: `f31d54f8e47b29675cbd21f78f457ee4b135936480698baac54180c5a83f14fd`;
- `movement_freeze_json`: `52c3340150dde391e94db3d9023150275d94777ac76da6647505b4741155abaa`;
- `movement_freeze_scores`: `385dc1c125e9b2ba9ec9a278e4a56f60fe3f2c10a66a425ff92fd5b9cb105eae`.

## Next Step

Следующий честный шаг — не открывать `locked_test`, а провести заранее
зафиксированный follow-up вокруг risk-механики:

- добавить stop-policy grid, включая entry-floor варианты
  `fractal0 ± 0.5 ATR` с минимальной дистанцией от входа `1/2/3 ATR`;
- сначала можно пропустить stress-spread и потом прогнать stress только для
  shortlist winners;
- отдельно спроектировать entry-quality ML filter для E3, который учится на
  PnL/SL-исходах конкретной E3-сделки, а не на абстрактном movement target.

## Related Materials

- `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- `tests/test_fractal0_entry_exit_grid.py`
- `docs/ML/benchmark_fractal0_entry_exit_grid.py.md`
- `ML/reports/fractal0_entry_exit_grid.json`
- `docs/reports/2026-07-10-fractal0-price-entry-mechanics.md`
- `docs/reports/2026-07-08-entry-based-movement-filter-replication-freeze.md`
