# Entry Path Causal Surrogate

> **Date**: 2026-05-14
> **Status**: Completed
> **Goal**: Проверить, можно ли заменить offline `label_all().signal` причинным surrogate-сигналом.
> **Related plan/spec**: direct user request
> **Related commit**: pending

## Context

All-rows ranking без offline `signal != 0` gate не прошёл: frozen test PF
`0.9134`, sequential PF `0.5908`. Следующий вариант - не снимать candidate
layer полностью, а попытаться причинно воспроизвести offline candidate universe
по live-доступным признакам.

## What Was Done

Добавлен benchmark:

- `ML/benchmark_entry_path_causal_surrogate.py`;
- `tests/test_benchmark_entry_path_causal_surrogate.py`;
- `docs/ML/benchmark_entry_path_causal_surrogate.py.md`.

Surrogate обучается на `DATA/Nero_XAUUSD_train_labeled.csv` и пытается
предсказать `signal` как `BUY / SELL / SKIP`.

Признаки:

- `ATR`;
- `session_hour`;
- `weekday`;
- текущий `fractal0`: direction, front, back, strong, break, reverse, power,
  count, impulse, fractal ATR.

Не используются: `predict`, `ret_*`, `fav_*`, `adv_*`.

## Changed Files

- `ML/benchmark_entry_path_causal_surrogate.py`
- `tests/test_benchmark_entry_path_causal_surrogate.py`
- `docs/ML/benchmark_entry_path_causal_surrogate.py.md`
- `ML/reports/entry_path_v1_causal_surrogate/summary.json`
- `ML/reports/entry_path_v1_causal_surrogate/summary.md`
- `ML/reports/entry_path_v1_causal_surrogate/validation_summary.csv`
- `ML/reports/entry_path_v1_causal_surrogate/test_selected_rows.csv`
- `MODULE_INDEX.md`
- `ML/README.md`

## Verification

Команды:

```bash
./.venv/bin/python -m pytest tests/test_benchmark_entry_path_causal_surrogate.py -q
./.venv/bin/python -m ML.benchmark_entry_path_causal_surrogate
```

## Results

Validation winner:

| Metric | Value |
|---|---:|
| probability threshold | 0.50 |
| trades | 43 |
| PF | 1.0507 |
| win rate | 53.49% |
| mean pnl ATR | 0.0753 |
| active precision | 21.11% |
| active recall | 88.28% |

Frozen test:

| Metric | Value |
|---|---:|
| trades | 36 |
| PF | 1.1537 |
| win rate | 58.33% |
| mean pnl ATR | 0.2319 |
| active precision | 20.41% |
| active recall | 89.09% |

Sequential test (`hold_bars=24`):

| Metric | Value |
|---|---:|
| trades | 31 |
| PF | 1.4111 |
| win rate | 64.52% |
| mean pnl ATR | 0.5854 |

## Conclusions

Causal surrogate лучше all-rows ranking и даёт слабоположительный frozen test.
Это не production-ready результат, но направление не провалилось.

Главный риск: surrogate очень широко ловит active-события. Recall высокий
(`~89%` на test), но precision низкий (`~20%`). То есть он часто видит
candidate там, где offline `label_all().signal` его не ставил. Score gate
частично очищает это, но запас прочности пока небольшой.

## Limitations / Open Questions

- Использован простой RandomForestClassifier.
- Проверен один профиль live-safe признаков.
- Старый score gate `pred_ret_24_dir_atr >= -0.07158749` не переобучался под
  surrogate universe.
- Нужна проверка прямой модели, которая сама выдаёт score и direction для
  каждого бара.

## Next Step

Перейти к пункту 3: модель как прямой score для каждого бара + direction из
модели.

## Related Materials

- `ML/reports/entry_path_v1_causal_surrogate/summary.md`
- `docs/reports/2026-05-14-entry-path-all-rows-ranking.md`
- `docs/reports/2026-05-05-live-safe-ml-audit.md`
