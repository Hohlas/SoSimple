# Telemetry Frequency Demo Launch

> **Date**: 2026-04-27
> **Status**: In Progress
> **Goal**: Подготовить частый diagnostic-режим `telemetry_frequency_v1` для проверки онлайн demo-контура `MT -> Nero.csv -> ML -> ml_signals.csv -> MT`
> **Related plan/spec**: `docs/superpowers/specs/2026-04-27-telemetry-frequency-demo-launch-design.md`, `docs/superpowers/plans/2026-04-27-telemetry-frequency-demo-launch.md`
> **Related commit**: pending

## Context

Проект дошёл до операционного этапа: есть frozen ML-rules, direct `time;signal` export для MT4 и несколько MT4-подтверждённых режимов. Но сильные режимы остаются редкими, поэтому они плохо подходят для быстрой проверки live pipeline на demo-счёте.

Для этого вводится отдельный diagnostic-режим `telemetry_frequency_v1`. Его цель — наработать статистику технического исполнения, сверки online/tester и влияния spread/slippage. Этот режим не является production verdict и не должен смешиваться с portfolio-метриками.

## What Was Done

### Diagnostic calibration

- Добавлен `ML/benchmark_telemetry_frequency_calibration.py`.
- Добавлены тесты `tests/test_benchmark_telemetry_frequency_calibration.py`.
- Выполнена calibration на `ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/test.csv`.
- Выбран diagnostic rule:
  - `score_target = take_24_x8`;
  - `selector = top_k_probability`;
  - `threshold = 1.0`;
  - `SL = 3 ATR`;
  - `TP = 5 ATR`;
  - `max_hold_bars = 24`;
  - `max_positions = 10`.

Выбор сделан по частоте, а не по PF. `PF` и same-time conflicts считаются только диагностикой.

### Export metadata

- `API/export_take_skip_trailing_stop_v2_signals.py` расширен optional metadata output.
- Metadata фиксирует пути, SHA256-хеши, число строк, число ненулевых сигналов, BUY/SELL и дубли времени.
- Созданы:
  - `ML/reports/telemetry_frequency_v1/ml_signals_telemetry_frequency_v1.csv`;
  - `ML/reports/telemetry_frequency_v1/export_metadata.json`.

### MQL reuse audit

Проверены `MT/MQL4/Include/lib_ML_Signal.mqh`, `MT/MQL4/Include/ORDERS.mqh`, `MT/MQL4/Include/SERVICE.mqh`.

| Area | Existing file/function | Verdict | Reason |
|---|---|---|---|
| Direct ML entry point | `lib_ML_Signal.mqh::EXPERT::ML_TRADE()` | `extend_existing_function` | Уже является активным `iSignal=3` контуром; менять нужно его, а не создавать новый path. |
| Multi-position open | `lib_ML_Signal.mqh::MLP_OpenMarketOrder(...)` | `keep_local_in_lib_ML_Signal_with_reason` | Работает с ticket-level market orders и не зависит от одиночного `set.BUY/set.SEL` состояния. |
| Multi-position close | `lib_ML_Signal.mqh::MLP_CloseSelectedOrder(...)` | `keep_local_in_lib_ML_Signal_with_reason` | Закрывает выбранный ticket; это лучше соответствует нескольким позициям одного направления. |
| Open wrappers | `ORDERS.mqh::SET_BUY()`, `SET_SEL()`, `ORDERS_SET()` | `keep_local_in_lib_ML_Signal_with_reason` | Контракт основан на одном `set.BUY` и одном `set.SEL`; для multi-position same-direction это слишком грубое состояние. |
| Modify/close wrapper | `ORDERS.mqh::MODIFY()` | `reuse_as_reference_only` | Полезен как паттерн retry/REPORT/ERROR_CHECK, но управляет всеми ордерами через одиночные `BUY/SEL` states. |
| Order state scan | `ORDERS.mqh::ORDER_CHECK()` | `reuse_as_reference_only` | Запоминает только один BUY и один SELL state, поэтому не может быть source-of-truth для нескольких позиций одного направления. |
| Market data | `ORDERS.mqh::MARKET_UPDATE(...)`, globals `Spred`, `StopLevel` | `reuse_as_is` | Подходит для расчёта spread/stop-level; можно использовать в MQL telemetry. |
| Reporting | `SERVICE.mqh::REPORT(...)` | `reuse_as_is` | Уже централизует сообщения и печатает `Magic:: message`; стоит использовать для service-level сообщений. |
| Tester file/report | `SERVICE.mqh::TESTER_FILE_CREATE(...)`, `OnTester()` | `reuse_or_extend_existing_function` | Подходит для tester-side summary/report metadata; расширять совместимо при необходимости. |
| Online monitoring | `SERVICE.mqh` missed-bars / persistence helpers | `reuse_or_extend_existing_function` | Полезно для demo monitoring; новые telemetry поля лучше добавлять совместимо. |

Главный вывод аудита: старый `ORDERS.mqh` полезен как источник проверенных паттернов и service helpers, но его основной order contract не подходит как прямой исполнитель multi-position ML-сделок. Для `telemetry_frequency_v1` допустимо оставить ticket-level open/close в `lib_ML_Signal.mqh`, при этом использовать `REPORT(...)`, `MARKET_UPDATE(...)` и service/report механизмы там, где они совместимы.

## Changed Files

- `ML/benchmark_telemetry_frequency_calibration.py`
- `tests/test_benchmark_telemetry_frequency_calibration.py`
- `API/export_take_skip_trailing_stop_v2_signals.py`
- `tests/test_export_take_skip_trailing_stop_v2_signals.py`
- `ML/reports/telemetry_frequency_v1/calibration/*`
- `ML/reports/telemetry_frequency_v1/export_metadata.json`
- `ML/reports/telemetry_frequency_v1/ml_signals_telemetry_frequency_v1.csv`
- `docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`

## Verification

```bash
./.venv/bin/python -m pytest tests/test_benchmark_telemetry_frequency_calibration.py -q
./.venv/bin/python -m pytest tests/test_export_take_skip_trailing_stop_v2_signals.py -q
./.venv/bin/python -m pytest tests/test_benchmark_telemetry_frequency_calibration.py tests/test_export_take_skip_trailing_stop_v2_signals.py -q
./.venv/bin/python -m ML.benchmark_telemetry_frequency_calibration \
  --predictions ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/test.csv \
  --score-target take_24_x8 \
  --output-dir ML/reports/telemetry_frequency_v1/calibration
./.venv/bin/python -m API.export_take_skip_trailing_stop_v2_signals \
  --predictions ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/test.csv \
  --rule-path ML/reports/telemetry_frequency_v1/calibration/selected_rule.json \
  --output ML/reports/telemetry_frequency_v1/ml_signals_telemetry_frequency_v1.csv \
  --metadata-output ML/reports/telemetry_frequency_v1/export_metadata.json \
  --label telemetry_frequency_v1
```

## Results

Current telemetry export:

| Metric | Value |
|---|---:|
| rows_total | 8887 |
| nonzero_rows | 454 |
| buy_rows | 238 |
| sell_rows | 216 |
| duplicate_time_rows | 15 |
| same_time_opposite_signal_groups | 15 |

The selected preset intentionally maximizes diagnostic signal flow. Same-time conflicts are tracked in metadata and must be handled/understood before demo launch.

## Conclusions

- `telemetry_frequency_v1` now has a reproducible calibration/export path.
- The current diagnostic export is much denser than production candidates and is suitable for stress-testing the execution pipeline.
- `ORDERS.mqh` should not be forced into the multi-position ML open/close path because its core contract is one `BUY` and one `SELL` state.
- `SERVICE.mqh` should be reused for reporting/monitoring/tester metadata where compatible.

## Limitations / Open Questions

- MQL multi-position logging has not yet been hardened.
- Daily reconciliation CLI has not yet been implemented.
- MT4 tester proof has not yet been run.
- Same-time opposite signal groups are present in the diagnostic export; downstream MT4 behavior must be verified explicitly.

## Next Step

Implement Task 4 from the plan:

1. harden `lib_ML_Signal.mqh` multi-position logs;
2. include `ticket`, spread/ATR, open-position count and close details;
3. preserve `ML_MaxPositions=1` behavior;
4. then add daily reconciliation CLI.

## Related Materials

- `docs/superpowers/specs/2026-04-27-telemetry-frequency-demo-launch-design.md`
- `docs/superpowers/plans/2026-04-27-telemetry-frequency-demo-launch.md`
- `ML/reports/telemetry_frequency_v1/calibration/selected_rule.json`
- `ML/reports/telemetry_frequency_v1/export_metadata.json`
