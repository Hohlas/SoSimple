# System Correlation And Portfolio Check

> **Date**: 2026-04-24 23:40
> **Status**: Completed
> **Goal**: Построить канонический pairwise benchmark по сделкам и PnL-рядам, чтобы понять, какие зрелые `XAUUSD` системы можно объединять в портфель без дублирования риска
> **Related plan/spec**: `docs/superpowers/plans/2026-04-24-system-correlation-and-portfolio-check.md`
> **Related commit**: `2642834`

## Context

После двух robustness-этапов оставался другой вопрос. Уже было понятно:

- какие системы держат `provider drift`;
- какие системы переносятся на новые инструменты.

Но это ещё не отвечало на portfolio-level задачу. Для портфеля важен не только отдельный `PF`, а то:

- насколько системы входят в рынок в одно и то же время;
- совпадает ли направление;
- синхронны ли прибыль и просадки;
- даёт ли новая система реально другой риск-профиль.

По плану главный verdict нужно было строить сначала только на `XAUUSD`, где все пять зрелых execution-систем сравнимы в одном frozen baseline-контуре:

- `quality`
- `frequency`
- `original_plus_path`
- `entry_path_v1`
- `entry_path_v1_quantile`

## What Was Done

- Добавлен manifest-driven benchmark `ML/benchmark_system_correlation.py`.
- Зафиксирован единый trade-level контракт для всех систем:
  - `system_name`
  - `instrument`
  - `provider`
  - `entry_time`
  - `exit_time`
  - `direction`
  - `pnl_atr`
  - `holding_bars`
- Для `quality`, `frequency`, `original_plus_path` переиспользован готовый `trades.csv` из `cross_instrument_robustness` baseline.
- Для `entry_path_v1` и `entry_path_v1_quantile` trade-level baseline был честно восстановлен из frozen checkpoints, prediction CSV, frozen rules и того же fixed-hold execution protocol, потому что в baseline-каталоге не было готового `trades.csv`.
- В коде зафиксированы воспроизводимые pairwise verdict rules:
  - `portfolio_complementary`
  - `portfolio_partially_overlapping`
  - `portfolio_redundant`
  - `portfolio_unclear`
- Собран канонический `XAUUSD` manifest на пять систем.
- Выполнен benchmark-run в `ML/reports/system_correlation_portfolio/xauusd_system_correlation/`.

## Changed Files

- `ML/benchmark_system_correlation.py`
- `tests/test_benchmark_system_correlation.py`
- `docs/ML/benchmark_system_correlation.py.md`
- `ML/reports/system_correlation_portfolio/manifest_xauusd_systems.json`
- `ML/reports/system_correlation_portfolio/generated/entry_path_v1_test_predictions.csv`
- `ML/reports/system_correlation_portfolio/generated/entry_path_v1_quantile_test_predictions.csv`
- `ML/reports/system_correlation_portfolio/xauusd_system_correlation/*`
- `ML/README.md`
- `MODULE_INDEX.md`

## Verification

```bash
./.venv/bin/python -m pytest tests/test_benchmark_system_correlation.py -q
./.venv/bin/python -m ML.benchmark_system_correlation \
  --manifest ML/reports/system_correlation_portfolio/manifest_xauusd_systems.json \
  --dry-run
./.venv/bin/python -m ML.export_entry_path_predictions \
  --task entry_path_v1 \
  --input-csv DATA/Nero_test_labeled.csv \
  --checkpoint ML/checkpoints/transformer_entry_path_v1_best.pt \
  --output ML/reports/system_correlation_portfolio/generated/entry_path_v1_test_predictions.csv
./.venv/bin/python -m ML.export_entry_path_predictions \
  --task entry_path_v1_quantile \
  --input-csv DATA/Nero_test_labeled.csv \
  --checkpoint ML/checkpoints/transformer_entry_path_v1_quantile_best.pt \
  --output ML/reports/system_correlation_portfolio/generated/entry_path_v1_quantile_test_predictions.csv
./.venv/bin/python -m ML.benchmark_system_correlation \
  --manifest ML/reports/system_correlation_portfolio/manifest_xauusd_systems.json \
  --output-dir ML/reports/system_correlation_portfolio/xauusd_system_correlation
```

## Results

### 1. System baselines on XAUUSD

| System | Trades | Net ATR | Mean PnL ATR | Win rate |
|---|---:|---:|---:|---:|
| `quality` | 26 | 205.69 | 7.91 | 84.62% |
| `frequency` | 72 | 171.19 | 2.38 | 51.39% |
| `original_plus_path` | 33 | 227.04 | 6.88 | 81.82% |
| `entry_path_v1` | 23 | 68.34 | 2.97 | 86.96% |
| `entry_path_v1_quantile` | 13 | 38.82 | 2.99 | 92.31% |

### 2. Pairwise verdict matrix

| Pair | Verdict | Key signal |
|---|---|---|
| `frequency` × `original_plus_path` | `portfolio_redundant` | `trade_overlap_ratio=1.00`, `trade_pnl_corr=1.00`, `daily_pnl_corr=0.95`, `weekly_pnl_corr=0.94` |
| `quality` × `entry_path_v1` | `portfolio_complementary` | `daily_pnl_corr=-0.33`, `weekly_pnl_corr=-0.32`, `drawdown_overlap_ratio=0.00` |
| `quality` × `entry_path_v1_quantile` | `portfolio_complementary` | `daily_pnl_corr=-0.28`, `weekly_pnl_corr=-0.25`, `drawdown_overlap_ratio=0.00` |
| `original_plus_path` × `entry_path_v1` | `portfolio_complementary` | `daily_pnl_corr=-0.26`, `weekly_pnl_corr=-0.27`, `staggered_gain_ratio=1.00` |
| `original_plus_path` × `entry_path_v1_quantile` | `portfolio_complementary` | `daily_pnl_corr=-0.24`, `weekly_pnl_corr=-0.25`, `staggered_gain_ratio=1.00` |
| `quality` × `frequency` | `portfolio_partially_overlapping` | `trade_overlap_ratio=1.00`, но `daily_pnl_corr=-0.09` |
| `quality` × `original_plus_path` | `portfolio_partially_overlapping` | `trade_overlap_ratio=0.73`, `daily_pnl_corr=-0.30` |
| `frequency` × `entry_path_v1` | `portfolio_partially_overlapping` | высокий trade overlap `0.78`, но слабая отрицательная дневная корреляция |
| `frequency` × `entry_path_v1_quantile` | `portfolio_partially_overlapping` | высокий trade overlap `0.77`, но слабая отрицательная дневная корреляция |
| `entry_path_v1` × `entry_path_v1_quantile` | `portfolio_partially_overlapping` | `trade_overlap_ratio=1.00`, `trade_pnl_corr≈1.00`, но daily/weekly correlation лишь `0.55` |

### 3. Category split

| Verdict | Pair count |
|---|---:|
| `portfolio_redundant` | 1 |
| `portfolio_complementary` | 4 |
| `portfolio_partially_overlapping` | 5 |
| `portfolio_unclear` | 0 |

### 4. Main portfolio facts

- `frequency` и `original_plus_path` нельзя считать двумя независимыми слоями. На `XAUUSD` это почти один и тот же trade stream с очень высокой синхронностью прибыли.
- `entry_path` линия действительно добавляет другой risk profile относительно `quality` и `original_plus_path`: у этих пар отрицательная дневная и недельная корреляция при нулевом overlap просадок.
- `entry_path_v1_quantile` не выглядит как новая независимая система поверх `entry_path_v1`; это скорее более сильный вариант той же линии, а не новый portfolio sleeve.

## Conclusions

- Канонический `XAUUSD` benchmark подтвердил, что сравнивать системы только по `PF` было бы ошибкой. Самый сильный вывод этапа даёт именно pairwise анализ сделок и PnL-ряда.
- Первый явный случай дублирования риска: `frequency` × `original_plus_path`. В портфеле нужно выбирать одну из них, а не считать их независимыми.
- `entry_path_v1_quantile` добавляет новый риск-профиль относительно `quality` и `original_plus_path`, но не относительно baseline `entry_path_v1`.
- Самый прагматичный первый portfolio-layer на `XAUUSD`:
  - базовая пара: `quality` + `entry_path_v1_quantile`;
  - `entry_path_v1` не добавлять рядом с quantile-версией как отдельный слой;
  - из пары `frequency` / `original_plus_path` брать только одну систему, если вообще нужен третий sleeve.

## Limitations / Open Questions

- Основной verdict построен только на `XAUUSD`, как и требовал план. Supplementary transfer extension на `USDCHF` / `XAGUSD` в этом этапе не запускался, чтобы не смешивать главный вывод с cross-instrument контуром.
- `quality` и `frequency` имеют сильный overlap по времени входа, но не положительную синхронность daily PnL. Это не ошибка benchmark, а диагностический факт: одна и та же идея входа может вести себя по-разному на агрегированном PnL-ряде.
- Pairwise benchmark пока не отвечает на вопрос распределения капитала между системами. Он отвечает только на вопрос совместимости и дублирования риска.

## Next Step

Следующий рациональный шаг — bounded portfolio-layer benchmark без новых торговых режимов:

1. взять `quality + entry_path_v1_quantile` как базовую независимую пару;
2. отдельно сравнить добавление третьего sleeve:
   - либо `frequency`,
   - либо `original_plus_path`,
   но не обе сразу;
3. проверить composite equity, drawdown и concentration уже на уровне портфеля;
4. только после этого переходить к любым risk filters, как и требует roadmap.

## Related Materials

- `docs/reports/2026-04-24-cross-instrument-robustness-check.md`
- `docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md`
- `ML/reports/system_correlation_portfolio/manifest_xauusd_systems.json`
- `ML/reports/system_correlation_portfolio/xauusd_system_correlation/pairwise_matrix.csv`
- `ML/reports/system_correlation_portfolio/xauusd_system_correlation/system_summary.csv`
- `ML/reports/system_correlation_portfolio/xauusd_system_correlation/daily_pnl_matrix.csv`
- `ML/reports/system_correlation_portfolio/xauusd_system_correlation/weekly_pnl_matrix.csv`
- `ML/reports/system_correlation_portfolio/xauusd_system_correlation/drawdown_overlap.csv`
