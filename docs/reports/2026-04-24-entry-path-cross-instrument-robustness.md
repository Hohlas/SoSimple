# Entry Path Cross-Instrument Robustness

> **Date**: 2026-04-24 18:30
> **Status**: Completed
> **Goal**: Проверить перенос frozen execution-систем `entry_path_v1` и `entry_path_v1_quantile` без переобучения, без нового threshold search и с отдельными verdict для `provider drift` и `cross-instrument transfer`
> **Related plan/spec**: `docs/superpowers/plans/2026-04-24-entry-path-cross-instrument-robustness.md`
> **Related commit**: pending

## Context

После завершения `cross-instrument robustness check` для `quality`, `frequency`, `original_plus_path` следующий шаг был более узким: проверить, держатся ли две зрелые `entry_path` execution-системы на том же methodological protocol.

Для этого этапа были зафиксированы четыре жёстких ограничения:

- не переобучать модели;
- не подбирать новые пороги;
- не менять frozen rules;
- сначала проверить `XAUUSD provider drift baseline`, только потом делать `cross-instrument transfer`.

Канонический план этапа был зафиксирован в `docs/superpowers/plans/2026-04-24-entry-path-cross-instrument-robustness.md`. Работа выполнена по той же дисциплине, что и предыдущий robustness-check: отдельные verdict для `provider_drift_baseline` и `cross_instrument_transfer`, без смешивания таблиц.

## What Was Done

- Добавлен fixed-hold execution adapter `hold_24_backstop_50` в `ML/benchmark_execution_policy_v2.py`, чтобы benchmark повторял реальный runtime protocol `entry_path` систем.
- Добавлен exporter `API/export_entry_path_v1_signals.py`, который применяет frozen rule `ML/reports/entry_path_trade_filter_selected_rule.json` и пишет единый контракт `time;signal`.
- Добавлен модуль `ML/export_entry_path_predictions.py` для inference frozen `entry_path_v1` и `entry_path_v1_quantile` на arbitrary labeled CSV.
- Для обоих execution-систем собран provider-drift baseline:
  - baseline reference на `XAUUSD / MetaQuotes`;
  - новый run на `XAUUSD / Alpari`.
- Без retraining выполнен transfer benchmark на:
  - `EURUSD`
  - `GBPUSD`
  - `USDCHF`
  - `XAGUSD`
- Для `USDCHF` использован `DATA/Nero_USDCHF_test_labeled_enriched.csv`, потому что исходный `DATA/Nero_USDCHF_test_labeled.csv` не содержал entry-path target columns.
- Для `XAUUSD Alpari` был отдельно дочитан и финализирован labeled split из уже имеющихся project inputs, после чего provider-drift benchmark был повторён на корректном input-контракте.
- Все benchmark-запуски выполнены через канонический `ML/benchmark_cross_instrument_robustness.py`.
- Stage artifacts сохранены в отдельный каталог `ML/reports/entry_path_cross_instrument_robustness/`.

## Changed Files

- `ML/benchmark_execution_policy_v2.py`
- `API/export_entry_path_v1_signals.py`
- `ML/export_entry_path_predictions.py`
- `tests/test_benchmark_execution_policy_v2.py`
- `tests/test_export_entry_path_v1_signals.py`
- `tests/test_export_entry_path_predictions.py`
- `docs/ML/export_entry_path_predictions.py.md`
- `docs/ML/benchmark_execution_policy_v2.py.md`
- `docs/ML/benchmark_cross_instrument_robustness.py.md`
- `docs/MT/ml_signal_integration.md`
- `ML/README.md`
- `API/README.md`
- `MODULE_INDEX.md`

## Verification

```bash
./.venv/bin/python -m ML.export_entry_path_predictions --task entry_path_v1 --input-csv DATA/Nero_XAUUSD_test_labeled.csv --checkpoint ML/checkpoints/transformer_entry_path_v1_best.pt --output ML/reports/entry_path_cross_instrument_robustness/generated/XAUUSD_ALPARI/entry_path_v1_test_predictions.csv
./.venv/bin/python -m ML.export_entry_path_predictions --task entry_path_v1_quantile --input-csv DATA/Nero_XAUUSD_test_labeled.csv --checkpoint ML/checkpoints/transformer_entry_path_v1_quantile_best.pt --output ML/reports/entry_path_cross_instrument_robustness/generated/XAUUSD_ALPARI/entry_path_v1_quantile_test_predictions.csv
./.venv/bin/python -m API.export_entry_path_v1_signals --predictions ML/reports/entry_path_cross_instrument_robustness/generated/XAUUSD_ALPARI/entry_path_v1_test_predictions.csv --rule-path ML/reports/entry_path_trade_filter_selected_rule.json --output ML/reports/entry_path_cross_instrument_robustness/generated/XAUUSD_ALPARI/entry_path_v1_test_signals.csv
./.venv/bin/python -m API.export_entry_path_v1_quantile_signals --seed-dir ML/reports/entry_path_cross_instrument_robustness/generated/XAUUSD_ALPARI --split test --rule-path ML/reports/entry_path_v1_quantile_selected_rule.json --baseline-predictions ML/reports/entry_path_cross_instrument_robustness/generated/XAUUSD_ALPARI/entry_path_v1_test_predictions.csv --output ML/reports/entry_path_cross_instrument_robustness/generated/XAUUSD_ALPARI/entry_path_v1_quantile_test_signals.csv
./.venv/bin/python -m ML.benchmark_cross_instrument_robustness --manifest ML/reports/entry_path_cross_instrument_robustness/generated/XAUUSD_ALPARI/xauusd_provider_drift_manifest.json --baseline-reference ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline_reference.json --output-dir ML/reports/entry_path_cross_instrument_robustness/xauusd_provider_drift
./.venv/bin/python -m compileall ML/benchmark_execution_policy_v2.py API/export_entry_path_v1_signals.py ML/export_entry_path_predictions.py ML/benchmark_cross_instrument_robustness.py
./.venv/bin/python -m pytest tests/test_export_entry_path_predictions.py tests/test_export_entry_path_v1_signals.py tests/test_benchmark_execution_policy_v2.py -q
```

## Results

### 1. Provider drift baseline

| System | Baseline | Drift run | Trades | PF | Max DD ATR | Verdict |
|---|---|---|---:|---:|---:|---|
| `entry_path_v1` | `XAUUSD / MetaQuotes` | `XAUUSD / Alpari` | 27 | 25.02 | 1.63 | `provider_stable` |
| `entry_path_v1_quantile` | `XAUUSD / MetaQuotes` | `XAUUSD / Alpari` | 10 | `inf` | 0.00 | `provider_stable` |

Provider-drift diagnostics against MetaQuotes reference:

| System | Trades ratio | Drawdown ratio | Top1 increase |
|---|---:|---:|---:|
| `entry_path_v1` | 1.17 | 1.13 | -0.0078 |
| `entry_path_v1_quantile` | 0.77 | 0.00 | 0.1148 |

### 2. Cross-instrument transfer

| Instrument | `entry_path_v1` | `entry_path_v1_quantile` |
|---|---|---|
| `EURUSD` | `transfer_failed` | `transfer_failed` |
| `GBPUSD` | `transfer_failed` | `transfer_failed` |
| `USDCHF` | `transfer_failed` | `transfer_supported` |
| `XAGUSD` | `transfer_supported` | `transfer_supported` |

Key transfer numbers:

| Instrument | System | Trades | PF | Max DD ATR | Verdict |
|---|---|---:|---:|---:|---|
| `EURUSD` | `entry_path_v1` | 31 | 2.33 | 7.36 | `transfer_failed` |
| `EURUSD` | `entry_path_v1_quantile` | 9 | 4.86 | 1.68 | `transfer_failed` |
| `GBPUSD` | `entry_path_v1` | 28 | 3.76 | 5.00 | `transfer_failed` |
| `GBPUSD` | `entry_path_v1_quantile` | 10 | 2.25 | 5.00 | `transfer_failed` |
| `USDCHF` | `entry_path_v1` | 31 | 12.67 | 5.02 | `transfer_failed` |
| `USDCHF` | `entry_path_v1_quantile` | 16 | 378.69 | 0.13 | `transfer_supported` |
| `XAGUSD` | `entry_path_v1` | 20 | `inf` | 0.00 | `transfer_supported` |
| `XAGUSD` | `entry_path_v1_quantile` | 8 | `inf` | 0.00 | `transfer_supported` |

Breadth by system:

| System | supported | inconclusive | failed |
|---|---:|---:|---:|
| `entry_path_v1` | 1 | 0 | 3 |
| `entry_path_v1_quantile` | 2 | 0 | 2 |

## Conclusions

- `provider drift` не сломал ни одну из двух `entry_path` систем на `XAUUSD`: обе остались в зоне `provider_stable`.
- Главная проблема этапа оказалась не в смене провайдера, а именно в переносе на новые рынки.
- `entry_path_v1` переносится слабо: только `XAGUSD` остался в зоне `transfer_supported`, а `EURUSD`, `GBPUSD`, `USDCHF` получили `transfer_failed`.
- `entry_path_v1_quantile` заметно живучее baseline-системы: он удержал `transfer_supported` на `USDCHF` и `XAGUSD`, но не прошёл `EURUSD` и `GBPUSD`.
- Separate verdict discipline себя оправдала: `XAUUSD Alpari` остаётся рабочим, значит неудачи на `EURUSD/GBPUSD` нельзя списать на один лишь provider drift.

## Limitations / Open Questions

- Transfer benchmark остаётся stress-test, а не заменой полноценного forward-validation на каждом новом инструменте.
- Для `USDCHF` пришлось использовать enriched labeled split, потому что исходный `test_labeled` не содержал полного entry-path contract.
- Для `USDCHF` часть контура опирается на enriched test-split, поэтому этот инструмент остаётся чуть более технически чувствительным, чем остальные.

## Next Step

Следующий рациональный этап — `System correlation and portfolio check` уже на множестве зрелых execution-систем:

1. сопоставить сделки `quality`, `frequency`, `original_plus_path`, `entry_path_v1`, `entry_path_v1_quantile`;
2. измерить пересечение по времени, совпадение направления и корреляцию PnL;
3. понять, какие системы действительно добавляют новый риск-профиль, а какие дублируют уже существующий слой.

## Related Materials

- `docs/superpowers/plans/2026-04-24-entry-path-cross-instrument-robustness.md`
- `ML/reports/entry_path_cross_instrument_robustness/xauusd_provider_drift/provider_drift.csv`
- `ML/reports/entry_path_cross_instrument_robustness/eurusd_transfer/transfer_matrix.csv`
- `ML/reports/entry_path_cross_instrument_robustness/gbpusd_transfer/transfer_matrix.csv`
- `ML/reports/entry_path_cross_instrument_robustness/usdchf_transfer/transfer_matrix.csv`
- `ML/reports/entry_path_cross_instrument_robustness/xagusd_transfer/transfer_matrix.csv`
