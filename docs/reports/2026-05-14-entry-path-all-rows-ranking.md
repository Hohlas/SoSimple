# Entry Path All-Rows Ranking

> **Date**: 2026-05-14
> **Status**: Completed
> **Goal**: Проверить, может ли `entry_path_v1_live_safe` работать без offline `signal != 0` gate, ранжируя все строки.
> **Related plan/spec**: direct user request
> **Related commit**: pending

## Context

После audit стало ясно, что текущий production-контур использует live-safe
признаки модели, но candidate gate `signal != 0` приходит из offline
`label_all()`. В live `Nero.csv` это поле равно нулю, поэтому нужно найти
новый live-safe источник кандидатов и направления.

Перед этим был сделан signal-only ablation:

- `signal_only`: 486 trades, PF `0.1757`;
- `signal_only` sequential: 237 trades, PF `0.1696`;
- текущий score gate: 41 trades, PF `7.5737`;
- текущий score gate sequential: 27 trades, PF `5.9352`.

Вывод ablation: offline `signal != 0` сам по себе не даёт edge. Основной
положительный вклад даёт model score, но он всё ещё применён поверх offline
candidate universe.

## What Was Done

Добавлен read-only benchmark:

- `ML/benchmark_entry_path_all_rows_ranking.py`;
- тесты `tests/test_benchmark_entry_path_all_rows_ranking.py`;
- документация `docs/ML/benchmark_entry_path_all_rows_ranking.py.md`.

Логика проверки:

1. Берём все строки validation/test prediction CSV.
2. Score: `pred_ret_24_dir_atr`.
3. Направление: `fractal0.direction` по существующей diagnostic all-rows
   конвенции.
4. Результат сделки пересчитывается заново по `DATA/XAUUSD_H1_OHLC.csv`:
   вход на open следующего бара, горизонт 24 бара, нормировка на ATR строки.
5. Порог выбирается на validation по сетке coverage.
6. Test проверяется с замороженным порогом.

## Changed Files

- `ML/benchmark_entry_path_all_rows_ranking.py`
- `tests/test_benchmark_entry_path_all_rows_ranking.py`
- `docs/ML/benchmark_entry_path_all_rows_ranking.py.md`
- `ML/reports/entry_path_v1_all_rows_ranking/summary.json`
- `ML/reports/entry_path_v1_all_rows_ranking/summary.md`
- `ML/reports/entry_path_v1_all_rows_ranking/validation_summary.csv`
- `ML/reports/entry_path_v1_all_rows_ranking/test_selected_rows.csv`
- `MODULE_INDEX.md`
- `ML/README.md`

## Verification

Команды:

```bash
./.venv/bin/python -m pytest tests/test_benchmark_entry_path_all_rows_ranking.py -q
./.venv/bin/python -m ML.benchmark_entry_path_all_rows_ranking
```

## Results

Validation winner:

| Metric | Value |
|---|---:|
| coverage | 5.0% |
| threshold | -0.00183110685 |
| trades | 471 |
| PF | 0.9661 |
| win rate | 47.77% |
| mean pnl ATR | -0.0503 |
| stable years | 1 / 4 |

Frozen test:

| Metric | Value |
|---|---:|
| trades | 329 |
| PF | 0.9134 |
| win rate | 46.20% |
| mean pnl ATR | -0.1275 |
| stable years | 1 / 4 |

Sequential test (`hold_bars=24`):

| Metric | Value |
|---|---:|
| trades | 133 |
| PF | 0.5908 |
| win rate | 40.60% |
| mean pnl ATR | -0.6768 |

## Conclusions

All-rows ranking с направлением из `fractal0.direction` не проходит даже как
research-кандидат. Лучший validation-срез уже слабый: PF ниже 1 и стабильность
только 1 год из 4. На frozen test результат остаётся убыточным, а
single-position sequential проверка ухудшает его ещё сильнее.

Практический вывод: нельзя просто снять `signal != 0` gate и заменить
направление `fractal0.direction`. Текущий `pred_ret_24_dir_atr` не переносится
на такой universe без новой постановки обучения.

## Limitations / Open Questions

- Проверен один источник направления: `fractal0.direction` в текущей
  diagnostic-конвенции.
- Модель обучалась не как all-rows direct scorer, поэтому отрицательный
  результат не закрывает пункт 3 из плана.
- Не проверены causal surrogate и модель с собственным направлением.

## Next Step

Перейти к пункту 2: causal surrogate для `label_all().signal`.

Цель следующего шага: понять, можно ли причинно воспроизвести offline candidate
universe по live-доступным признакам и затем снова применить текущий score gate.

## Related Materials

- `ML/reports/entry_path_v1_all_rows_ranking/summary.md`
- `ML/reports/entry_path_v1_signal_only_ablation/summary.md`
- `docs/API/telemetry_signal_watcher.py.md`
- `docs/reports/2026-05-05-live-safe-ml-audit.md`
