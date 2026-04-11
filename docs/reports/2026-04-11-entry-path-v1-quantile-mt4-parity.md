# Entry Path v1 Quantile: MT4 parity подтверждён

> **Date**: 2026-04-11 17:35
> **Status**: Completed
> **Goal**: Подтвердить `entry_path_v1_quantile` в реальном MT4-контуре для frozen winner `lb_gt_m`, убрать расхождения Python ↔ MT4 и сохранить trade-level reconciliation artifact
> **Related plan/spec**: `docs/superpowers/specs/2026-04-11-entry-path-v1-quantile-mt4-export-design.md`, `docs/superpowers/plans/2026-04-11-entry-path-v1-quantile-mt4-export.md`, `docs/reports/2026-04-11-entry-path-v1-quantile-robustness.md`
> **Related commit**: pending

## Context

Этап `2026-04-11-entry-path-v1-quantile-robustness` уже дал verdict `go_mt4`: quantile-layer выдержал полный 5-seed robustness-pass, и winner `lb_gt_m` оказался одинаковым во всех seed.

После этого главный открытый вопрос был уже не исследовательским, а execution-level: сможет ли MT4 честно исполнить именно тот frozen quantile winner, который был подтверждён в Python.

Для этого не хватало двух вещей:

- канонического exporter-а `seed artifacts -> ml_signals.csv` без ручной сборки;
- автоматической сверки direct `MLP`-логов из MT4 на уровне отдельных сделок.

## What Was Done

- Добавлен отдельный exporter `API/export_entry_path_v1_quantile_signals.py`:
  - читает frozen `entry_path_v1_quantile_filter_selected_rule.json`;
  - берёт `validation` или `test` prediction CSV;
  - восстанавливает `lb/ub/width` через сохранённый conformal correction;
  - применяет frozen winner без re-fit;
  - пишет полный `time;signal`;
  - по флагу `--copy-to-mt4` обновляет и `MT/tester/files/ml_signals.csv`, и `MT/MQL4/Files/ml_signals.csv`.
- На первом реальном MT4-прогоне обнаружено расхождение: Python exporter выпускал `9378` строк и `16` активных сигналов, а MT4 открывал только `8` сделок.
- Разобран активный MQL-код и подтверждена настоящая семантика `lib_ML_Signal.mqh`: при дубликатах `time` MT4 оставляет последнюю строку.
- Exporter исправлен под эту семантику:
  - prediction frame теперь дедуплицируется по `time` с `keep='last'`;
  - после исправления канонический экспорт стал точно совпадать с тем, что реально загружает MT4.
- `statistics/signal_tracer.py` расширен под direct `MLP`-лог:
  - разбор `MLP CLOSE BUY/SELL reason=...`;
  - отдельный `mlp` dossier path;
  - печать и CSV-export для direct parity-трека.
- Выпущен trade-level reconciliation artifact:
  - `ML/reports/entry_path_v1_quantile_mt4_reconciliation.csv`
- Обновлены операционные docs:
  - `docs/MT/trading_strategy.md`
  - `docs/MT/ml_signal_integration.md`
  - `docs/statistics/signal_tracer.py.md`
  - `statistics/README.md`
- В tester config для quantile parity зафиксированы реальные рабочие параметры:
  - `ML_HoldBars=24`
  - `ML_AllowReversal=0`
  - `ML_UseScoreFilter=0`
- Пользователь выполнил ручной MT4 tester run по финальному `ml_signals.csv`, после чего лог `MT/tester/logs/20260411.log` был разобран и сверен с Python.

## Changed Files

- `API/export_entry_path_v1_quantile_signals.py`
- `tests/test_export_entry_path_v1_quantile_signals.py`
- `statistics/signal_tracer.py`
- `tests/test_signal_tracer_mlp.py`
- `MT/tester/$o$imple.ini`
- `docs/MT/trading_strategy.md`
- `docs/MT/ml_signal_integration.md`
- `docs/statistics/signal_tracer.py.md`
- `statistics/README.md`
- `MODULE_INDEX.md`
- `ML/reports/entry_path_v1_quantile_mt4_reconciliation.csv`

## Verification

```bash
./.venv/bin/python -m pytest tests/test_export_entry_path_v1_quantile_signals.py tests/test_signal_tracer_mlp.py tests/test_signal_tracer_tb.py -q
# 13 passed

./.venv/bin/python -m API.export_entry_path_v1_quantile_signals --seed-dir ML/reports/entry_path_v1_quantile_robustness/seed_123 --split test --output MT/tester/files/ml_signals.csv --copy-to-mt4

./.venv/bin/python statistics/signal_tracer.py --from-log MT/tester/logs/20260411.log --signals MT/MQL4/Files/ml_signals.csv --csv-out ML/reports/entry_path_v1_quantile_mt4_reconciliation.csv

rg -n "MLP_INIT|Opened:|Timeout closes|Score filtered|Position blocked" MT/tester/logs/20260411.log
rg -c "open #[0-9]+ " MT/tester/logs/20260411.log
rg -c "close #[0-9]+ " MT/tester/logs/20260411.log
```

Observed:

- `pytest`: `13 passed`
- exporter after dedupe fix writes canonical `ml_signals.csv` with `8872` rows and `8` active signals
- `signal_tracer.py` successfully parses direct `MLP` log and exports reconciliation CSV
- log counters match the exported CSV:
  - `MLP_INIT: Loaded V4.0 8872 rows`
  - `Opened: 8`
  - `Timeout closes: 8`
  - `Score filtered: 0`
  - `Position blocked: 0`
- `open #`: `8`
- `close #`: `8`
- MT4 compile/tester execution was performed manually by the user outside this environment

## Results

### Canonical MT4 export after dedupe fix

| Metric | Value |
|---|---:|
| Rows in `ml_signals.csv` | `8872` |
| Active signals | `8` |
| BUY | `4` |
| SELL | `4` |
| Range | `2022.09.29 18:00` -> `2026.03.20 06:00` |

Активные сигналы:

- `2023.05.15 17:00` `SELL`
- `2024.07.01 17:00` `BUY`
- `2025.02.14 23:00` `BUY`
- `2025.04.09 02:00` `BUY`
- `2025.06.16 01:00` `SELL`
- `2025.07.17 15:00` `BUY`
- `2025.08.08 01:00` `SELL`
- `2025.10.31 01:00` `SELL`

### MT4 tester result

| Metric | Value |
|---|---:|
| Net profit | `2951.63` |
| Gross profit | `3002.63` |
| Gross loss | `-51.00` |
| Profit Factor | `58.88` |
| Max drawdown | `326.60` |
| Relative drawdown | `2.85%` |
| Total trades | `8` |
| BUY | `4` |
| SELL | `4` |
| Win trades | `7` |
| Loss trades | `1` |

### Trade-level reconciliation artifact

`ML/reports/entry_path_v1_quantile_mt4_reconciliation.csv` содержит все `8` MT4-сделок direct `MLP`-режима.

Ключевые сводные числа:

- `8` сделок
- `7` wins
- `1` loss
- `mean_pnl_atr = 3.4104`
- `sum_pnl_atr = 27.2834`
- все закрытия в этом прогоне были `Timeout`

## Conclusions

`entry_path_v1_quantile` прошёл не только Python robustness-pass, но и честную MT4 parity-проверку.

Ключевой технический вывод этапа: расхождение между Python и MT4 было вызвано не MQL-логикой, а ошибкой exporter-а. После приведения Python к реальной семантике `keep='last'` для дубликатов `time` канонический CSV, счётчики в MT4-логе и trade-level reconciliation совпали.

Практически это означает следующее:

- quantile winner `lb_gt_m` действительно воспроизводим в реальном MT4 execution loop;
- frozen параметры `HoldBars=24`, `Reversal=false`, prefiltered `time;signal` ведут себя как ожидалось;
- у линии теперь есть и multi-seed robustness verdict, и MT4 confirmation.

## Limitations / Open Questions

- MT4-подтверждение пока опирается на один честный quantile run с `8` сделками; это уже достаточно для parity, но support всё ещё low-frequency.
- В этом окружении MT4 не запускался автоматически; compile/tester шаг остаётся ручным.
- Secondary track `triple_barrier_mt4_execution` по-прежнему не доведён до реального benchmark verdict.

## Next Step

1. Решить, переводится ли `entry_path_v1_quantile` в статус основного execution mode поверх `entry_path_v1`.
2. Если да, зафиксировать для него основной production/export path без research-обвязки.
3. Отдельным этапом прогнать `ML/benchmark_triple_barrier_mt4_execution.py` на `validation/test`, чтобы закрыть вопрос о реальной силе TB в MT4-matched Python-режиме.

## Related Materials

- `docs/reports/2026-04-11-entry-path-v1-quantile-robustness.md`
- `docs/reports/2026-04-10-entry-path-v1-quantile.md`
- `docs/MT/trading_strategy.md`
- `docs/MT/ml_signal_integration.md`
- `MT/tester/logs/20260411.log`
- `ML/reports/entry_path_v1_quantile_mt4_reconciliation.csv`
