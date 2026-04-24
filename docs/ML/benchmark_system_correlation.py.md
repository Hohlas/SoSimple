# benchmark_system_correlation.py

## Назначение

`ML/benchmark_system_correlation.py` строит канонический pairwise benchmark совместимости зрелых торговых систем.

Модуль нужен для отдельного portfolio-level вопроса:

- какие системы открываются почти в одно и то же время и фактически дублируют риск;
- какие системы дают похожий или разный профиль прибыли по дням и неделям;
- какие пары можно считать `complementary`, а какие уже `redundant`.

Главный baseline строится отдельно по одному инструменту. Для текущего этапа source of truth — `XAUUSD`.

## Входные данные

- `manifest.json` с описанием систем одного инструмента.
- Для `trade_csv`-источников:
  - готовый `trades.csv`;
  - optional фильтры `dataset_name`, `policy_name`.
- Для `entry_path_predictions`:
  - prediction CSV;
  - frozen rule JSON;
  - OHLC CSV;
  - fixed-hold policy (`hold_24_backstop_50` или явный `hold_bars`).

Поддерживаемые `source_type`:

- `trade_csv`
- `entry_path_predictions`

Это позволяет честно восстановить trade-level baseline даже там, где готовый `trades.csv` не сохранён в отчётном каталоге.

## Нормализованный контракт

После загрузки все системы приводятся к одному trade-level формату:

- `system_name`
- `instrument`
- `provider`
- `entry_time`
- `exit_time`
- `direction`
- `pnl_atr`
- `holding_bars`

## Что считает

Для каждой пары систем модуль пишет:

- `trade_overlap_ratio`
- `same_direction_ratio`
- `entry_time_jaccard`
- `trade_pnl_corr`
- `daily_pnl_corr`
- `weekly_pnl_corr`
- `drawdown_overlap_ratio`
- `co_loss_ratio`
- `staggered_gain_ratio`

## Verdict vocabulary

Каждая пара получает ровно один воспроизводимый verdict:

- `portfolio_complementary`
- `portfolio_partially_overlapping`
- `portfolio_redundant`
- `portfolio_unclear`

Логика verdict зафиксирована в коде, а не в отчёте:

- `redundant` — высокий overlap по входам и высокая корреляция trade/daily/weekly PnL;
- `complementary` — отрицательная или слабая синхронность PnL при низком overlap просадок и высоком `staggered_gain_ratio`;
- `partially_overlapping` — середина между этими полюсами;
- `unclear` — случаи, где сигнал слабый и не тянет ни на overlap, ни на complementarity.

## Запуск

Dry-run валидации manifest:

```bash
python -m ML.benchmark_system_correlation \
  --manifest ML/reports/system_correlation_portfolio/manifest_xauusd_systems.json \
  --dry-run
```

Полный benchmark:

```bash
python -m ML.benchmark_system_correlation \
  --manifest ML/reports/system_correlation_portfolio/manifest_xauusd_systems.json \
  --output-dir ML/reports/system_correlation_portfolio/xauusd_system_correlation
```

## Выходные файлы

- `pairwise_matrix.csv`
- `system_summary.csv`
- `daily_pnl_matrix.csv`
- `weekly_pnl_matrix.csv`
- `drawdown_overlap.csv`
- `run_metadata.json`
- `summary.json`

## Ограничения

- Главный verdict нельзя строить на pooled mixed-instrument manifest.
- Модуль не переобучает модели и не меняет frozen rules.
- `entry_path` baseline при отсутствии готового `trades.csv` восстанавливается тем же frozen execution-контуром, а не summary-числами.
- Supplementary transfer-analysis нужно запускать отдельным manifest на каждом инструменте, не смешивая его с `XAUUSD` baseline.
