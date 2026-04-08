# Validation-First ML Exit And Position Management

> **Date**: 2026-04-08 10:03 MSK
> **Status**: Completed
> **Goal**: Построить offline-симулятор выходов поверх существующего `regression_updn` трека, честно сравнить политики выхода на `validation`, перенести в runtime только validation-winner и сделать одну финальную проверку на `test`
> **Related plan/spec**: `docs/superpowers/plans/2026-04-07-ml-exit-and-position-management.md`, `docs/superpowers/plans/ME13_Diagnostics_Plan.md`
> **Related commit**: d861ca6

## Context

После validation-first разворота процесса следующий шаг roadmap был узко определён: улучшить текущий `regression_updn` трек не через новое обучение, а через более умный выход и управление позицией. Исторический контекст из ME-13 показывал, что gap между Python и MT4 может объясняться таймаутом, position blocking и path dependency, но на этом этапе требовалась честная проверка именно exit-policy layer без leakage из `test`.

До этого в репозитории не было отдельного инструмента, который:
- читал бы уже существующий `ml_signals.csv`;
- резал исследование строго по временам из `Nero_validation_labeled.csv` / `Nero_test_labeled.csv`;
- сравнивал бы семейства правил выхода без переобучения модели;
- замораживал бы winner в JSON для one-shot финальной проверки.

## What Was Done

- Создан новый research CLI `API/exit_policy_research.py`.
- Реализован offline simulator, который моделирует последовательность сделок по уже сгенерированным ML-сигналам и учитывает:
  - `reverse_ratio` exit;
  - `weak_edge` exit после минимального удержания;
  - `profit_guard` exit после накопленного favorable excursion;
  - same-bar flip при сильном reverse signal;
  - blocked signals внутри периода удержания.
- Реализован жёсткий split boundary:
  - `validation_research` использует только времена из `DATA/Nero_validation_labeled.csv`;
  - `test_final` использует только времена из `DATA/Nero_test_labeled.csv`;
  - запуск search loop на `test_final` запрещён без frozen policy JSON.
- Добавлена policy library для comparison-run:
  - `timeout_only`;
  - grid по `reverse_close`;
  - grid по `weak_edge_close`;
  - grid по `profit_guard_close`;
  - layered combinations.
- Добавлен экспорт frozen winner в `ML/reports/frozen_exit_policy.json`.
- Проведён validation-only ranking и отдельная final one-shot проверка на `test`.
- Принято решение не менять MQL4 runtime:
  - validation winner совпал с уже существующим `ML_Timeout(12H)` baseline;
  - поэтому переносить новое правило в `lib_ML_Signal.mqh` / `$o$imple.mq4` было бы нечестным “улучшением на бумаге”.

## Changed Files

- `API/exit_policy_research.py` (создан)
- `tests/test_exit_policy_research.py` (создан)
- `ML/reports/frozen_exit_policy.json` (создан)
- `API/README.md` (обновлён)
- `tests/README.md` (обновлён)
- `CHANGELOG.md` (обновлён)
- `CONTEXT_HANDOFF.md` (обновлён)

## Verification

```bash
./.venv/bin/python -m pytest tests/test_exit_policy_research.py -q
./.venv/bin/python -m API.exit_policy_research --split-profile validation_research --save-best ML/reports/frozen_exit_policy.json
./.venv/bin/python -m API.exit_policy_research --split-profile test_final --policy ML/reports/frozen_exit_policy.json
grep -n "ML_Timeout(12H)" MT/MQL4/Include/OUTPUT.mqh
```

Observed:
- `10 passed`
- validation ranking completed and rewrote `ML/reports/frozen_exit_policy.json`
- test final confirmation completed with the frozen policy only
- `ML_Timeout(12H)` confirmed for BUY and SELL in `OUTPUT.mqh`

## Results

Validation ranking (`split_profile=validation_research`, trade floor active):

| Policy | Trades | PF | Win Rate | Avg Hold Bars | Avg Blocked Signals | Net ATR |
|---|---:|---:|---:|---:|---:|---:|
| `timeout_only` | 567 | **1.1699** | 50.97% | 11.998 | 3.732 | 139.76 |
| `profit_guard_p1.5_k1.8_h2` | 777 | 1.1593 | 61.26% | 7.807 | 2.453 | 130.44 |
| `profit_guard_p1.5_k1.6_h2` | 777 | 1.1568 | 61.39% | 7.807 | 2.453 | 128.20 |
| `profit_guard_p1.5_k1.4_h3` | 759 | 1.1531 | 60.21% | 8.038 | 2.535 | 127.64 |

Validation frozen winner:

```json
{
  "policy": {
    "name": "timeout_only"
  }
}
```

Final one-shot confirmation on `test` (`split_profile=test_final`, no search loop):

| Policy | Trades | PF | Win Rate | Avg Hold Bars | Avg Blocked Signals | Net ATR |
|---|---:|---:|---:|---:|---:|---:|
| `timeout_only` | 558 | **1.11622** | 50.72% | 11.980 | 3.337 | 98.61 |

Runtime implication:
- `mql_inputs` in frozen JSON are all zero because no new exit thresholds survived validation.
- Existing runtime behavior already matches frozen policy via `ML_Timeout(12H)`.

## Conclusions

Этап завершился честным отрицательным результатом в смысле “новой exit-логики”, но положительным результатом в смысле процесса:

- offline simulator и validation-first protocol для exit-policy layer теперь существуют;
- `test` действительно использован только один раз, после freeze;
- новые early-exit rules не показали validated uplift против baseline timeout behavior;
- перенос “проверенного правила” в MQL4 выродился в “ничего не менять”, и это правильный итог.

Это означает, что в текущем `regression_updn` треке проблема не решается простым ранним закрытием из исследованного семейства правил. Если нужен новый uplift, его вероятнее искать либо в другом execution track, либо в outcome-aligned target, а не в локальном search по exit thresholds.

## Limitations / Open Questions

- Search space был осознанно ограничен тремя семействами (`reverse`, `weak_edge`, `profit_guard`) и их простыми комбинациями; это stage-complete, но не exhaustive optimization.
- MT4 Strategy Tester не перезапускался, потому что runtime logic не менялась и frozen winner уже совпал с текущим behavior.
- Position blocking остаётся высоким даже у validation winner (`avg_blocked_signals ≈ 3.73`), но попытки решить это только через exit-layer в рамках данного этапа не улучшили PF.
- В frozen policy `timeout_only` длинное удержание почти максимально (`~12` баров), так что direction-level edge по-прежнему ближе к slow drift, чем к fast impulse capture.

## Next Step

Не продолжать локальный search по тем же exit rules. Следующий содержательный шаг:
- либо перейти к `Triple Barrier hardening` как к более outcome-aligned execution track;
- либо идти в новый target / objective, если цель — реально сократить gap между ML signal quality и executable trading outcome.

## Related Materials

- `docs/superpowers/plans/2026-04-07-ml-exit-and-position-management.md`
- `docs/superpowers/plans/ME13_Diagnostics_Plan.md`
- `ML/reports/frozen_exit_policy.json`
- `MT/MQL4/Include/OUTPUT.mqh`
- `docs/reports/2026-04-04-archetype-filter-bridge.md`
