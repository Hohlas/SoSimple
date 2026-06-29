# Stage 6.0 Outcome-Based Triple-Barrier Foundation

> **Дата**: 2026-06-29
> **Статус**: Completed
> **Вердикт**: TRADING_GATE_FAILED (DIAGNOSTIC_ONLY)
> **Цель**: Проверить, даёт ли trade-like TP/SL/timeout target полезный сигнал после закрытия ветки `H6_off05`, включая короткий горизонт 6 часов.
> **Related plan/spec**: `docs/superpowers/plans/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md`

## Context

Stage 5.4 отверг price/ATR расширение для `fast` и закрыл продолжение поиска вокруг `H6_off05`. Stage 6.0 перенёс вопрос ближе к торговой постановке: что раньше случится после входа `Open[row+1]` — TP, SL или timeout.

После ревью первоначального Stage 6.0 были исправлены ошибки проверки: gate читал не те поля summary, permutation baseline использовал constant score, diagnostic threshold не применялся к реальным score, а `INVALID` строки попадали в yearly/by-side счётчики. Также добавлен короткий горизонт `H6`, потому что на 6 H1-барах движение потенциально проще предсказывать, чем на 24.

Уровень этапа: поисковый. Результат не может быть торговым кандидатом без отдельного проверочного цикла и runtime parity.

## What Was Done

- Runner расширен до двух горизонтов: `H6` как primary и `H24` как disclosure-сравнение.
- Для каждого горизонта обучены профили `clock_shift_back` и `clock_shift_back_impulse`, по 3 seed: всего `12/12` runs.
- JSON теперь хранит реальные predictions/labels для post-mortem.
- Permutation baseline считает перестановку реальных model scores.
- `INVALID` rows исключены из threshold, yearly и by-side торговых счётчиков.
- Gate смотрит primary key `H6_clock_shift_back` и median metrics.

## Multiple Testing Context

Search budget: 2 горизонта x 2 профиля x 3 seed = 12 XGBoost прогонов. `H6` был добавлен по явному требованию после ревью как короткий fixed horizon, не как широкий перебор. Пороговая сетка осталась заранее ограниченной: `0.50..0.90`, step `0.025`.

Коррекция множественного тестирования не применялась. Статус остаётся `DIAGNOSTIC_ONLY`; `2023-2025` и `2026` не использовались для выбора.

## Changed Files

- `ML/baseline/benchmark_stage6_outcome_based.py`
- `tests/test_stage6_outcome_based.py`
- `ML/reports/stage6_0_outcome_based_triple_barrier.json`
- `docs/reports/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

## Verification

Commands:

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py -q
./.venv/bin/python -u -m ML.baseline.benchmark_stage6_outcome_based --stage6-0-outcome-based
./.venv/bin/python -m pytest tests/ -q
```

JSON invariants checked:

- `done_runs == total_runs == 12`
- `len(raw_runs) == 12`
- summary keys: `H6_clock_shift_back`, `H6_clock_shift_back_impulse`, `H24_clock_shift_back`, `H24_clock_shift_back_impulse`
- yearly/by-side trade counts match valid trade count for all all-trade baselines

## Results

### Preflight

| Horizon | Val valid | TP rate | Timeout rate | All-trade val PF | Spread 0.20 PF |
|---|---:|---:|---:|---:|---:|
| H6 | 5,412 | 16.6% | 46.4% | 0.942 | 0.861 |
| H24 | 5,412 | 36.8% | 4.6% | 0.959 | 0.899 |

H6 делает задачу модельно проще, но увеличивает timeout-долю почти до половины сделок.

### Model Metrics

| Key | Median val AUC | Median PR AUC lift | Threshold status | Val PF median |
|---|---:|---:|---|---:|
| `H6_clock_shift_back` | 0.689 | 0.114 | NO_THRESHOLD | — |
| `H6_clock_shift_back_impulse` | 0.694 | 0.129 | NO_THRESHOLD | — |
| `H24_clock_shift_back` | 0.585 | 0.079 | SELECTED | 0.933 |
| `H24_clock_shift_back_impulse` | 0.586 | 0.080 | SELECTED | 1.023 |

Primary `H6_clock_shift_back` проходит model gate (`AUC >= 0.60`, PR lift `>= 0.05`), но не проходит trading gate: на фиксированной сетке `0.50..0.90` нет порога с достаточным числом сделок.

### Permutation / Diagnostic Disclosure

Permutation считается только там, где threshold был выбран.

| Key | Observed PF | Permuted median PF | p-value |
|---|---:|---:|---:|
| `H24_clock_shift_back` | 0.990 | 1.071 | 0.635 |
| `H24_clock_shift_back_impulse` | 1.093 | 0.994 | 0.305 |

H24 threshold не превосходит случайное ранжирование. Для H6 permutation отсутствует, потому что нет выбранного threshold.

Diagnostic all-trade PF:

- H6 `2023-2025`: 0.995
- H24 `2023-2025`: 0.980

## Conclusions

1. Короткий H6 target действительно легче для модели: AUC вырос с `~0.585` до `~0.689`.
2. Этот model-signal не превращается в торговое правило при текущем протоколе: threshold не выбран на заранее заданной сетке `0.50..0.90`.
3. H24 повторно подтверждает старый вывод: модельный сигнал слабый, а threshold PF не лучше permutation baseline.
4. Старый вердикт `MODEL_GATE_FAILED` для всего Stage 6.0 устарел. После H6 исправленный итог: `TRADING_GATE_FAILED`.
5. Основная проблема H6 — не отсутствие ранжирования, а калибровка/частота сделок: score не даёт пригодного фиксированного порога в текущей сетке.

Invalidated assumptions:

- `permutation p-value = 1.0` из предыдущего отчёта был артефактом constant score.
- `pr_auc_lift_ge_0_05 = FAIL` в старом JSON был ошибкой чтения summary.
- Старые yearly/by-side counts включали `INVALID` rows.

## Limitations / Open Questions

- `Open[row+1]` остаётся диагностическим допущением; runtime timing не доказан.
- Основной PnL gross; spread stress показан отдельно.
- OHLC source: `DATA/XAUUSD_H1_OHLC.csv`, локальный CSV-вход, игнорируемый git как и остальные CSV данные.
- Threshold grid не расширялась ниже `0.50`, чтобы не превращать исправление в новый parameter search.
- Нет model card, потому что кандидат не принят.
- A5 post-mortem не выполнялся отдельно: провал объяснён trading-gate после model-gate, следующий шаг должен быть новым проверочным дизайном, а не углублением текущего threshold.

## Validation Split Disclosure

- `train_core`: `<= 2020`
- `val_stop`: `2021-2022`
- `diagnostic_holdout`: `2023-2025`, не использовался для выбора
- `low_n_disclosure`: `2026`, не использовался для выбора

Выбор профиля и gate считаются по primary `H6_clock_shift_back` на `val_stop`.

## Next Step

Разрешённый следующий шаг: отдельный bounded follow-up для H6 calibration/threshold protocol, если цель — проверить, можно ли превратить AUC `~0.69` в торговое правило без подгонки. Он должен заранее задать новую пороговую схему, например quantile/top-N или calibrated probability threshold, и не использовать `2023-2025` для выбора.

Запрещено делать дальше:

- объявлять Stage 6.0 кандидатом;
- использовать H6 diagnostic holdout для выбора порога;
- открывать широкий перебор horizon/ATR/TP/SL;
- чинить результат снижением threshold post-hoc без нового плана.

## Related Materials

- `ML/reports/stage6_0_outcome_based_triple_barrier.json`
- `ML/baseline/benchmark_stage6_outcome_based.py`
- `tests/test_stage6_outcome_based.py`
- `docs/superpowers/plans/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md`
- `docs/reports/2026-06-29-stage5_4-fast-price-atr-ablation.md`
