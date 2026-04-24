# benchmark_cross_instrument_robustness.py

## Назначение

`ML/benchmark_cross_instrument_robustness.py` делает два связанных, но разных stress-test:

- `provider drift` на том же `XAUUSD`, но с другим провайдером котировок;
- `cross-instrument transfer` на новых инструментах без перенастройки frozen rules.

Модуль нужен для того, чтобы не смешивать вопрос "ломается ли система от смены котировок" с вопросом "переносится ли система на другой рынок".

## Входные данные

- `manifest.json` с наборами данных:
  - `dataset_name`
  - `instrument`
  - `provider`
  - `kind`
  - `ohlc_path`
  - `signals[]`
- optional `baseline_reference.json` с опорными метриками уже подтверждённых систем.
- signal CSV в формате `time;signal`.
- OHLC CSV в формате `time;open;high;low;close;atr14`.

Поддерживаемые `kind`:

- `provider_drift_baseline`
- `cross_instrument_transfer`

## Что делает

1. Валидирует manifest и наличие файлов.
2. Проверяет выравнивание signal-времён с OHLC.
3. Переиспользует execution semantics из `ML/benchmark_execution_policy_v2.py`.
4. Считает унифицированные метрики сделок.
5. При наличии baseline reference присваивает verdict и reason.
6. Пишет отдельные представления для `provider_drift` и `transfer`.

Для `entry_path` систем benchmark может использовать тот же fixed-hold protocol, что и MT4/runtime:

- `policy_name = hold_24_backstop_50`
- вход на следующем баре
- удержание `24` бара
- дальний защитный stop `50 ATR`

## Метрики

Основные метрики совпадают с `benchmark_execution_policy_v2.py`:

- `trades`
- `trades_per_year`
- `pf`
- `net_atr`
- `max_drawdown_atr`
- `ulcer_index_atr`
- `equity_linearity_r2`
- `profit_concentration_top_1/3/10`
- `negative_months`
- `negative_years`

Дополнительно пишутся alignment-диагностики:

- `rows_total`
- `nonzero_rows`
- `nonzero_unique_time`
- `duplicate_time_signal_rows`
- `missing_ohlc_times`
- `missing_ohlc_examples`

## Verdicts

Для `provider_drift_baseline`:

- `provider_stable`
- `provider_degraded`
- `provider_failed`

Для `cross_instrument_transfer`:

- `transfer_supported`
- `transfer_inconclusive`
- `transfer_failed`

Каждый verdict сопровождается `reason`.

## Запуск

```bash
python -m ML.benchmark_cross_instrument_robustness \
  --manifest ML/reports/cross_instrument_robustness/manifest.json \
  --baseline-reference ML/reports/cross_instrument_robustness/metaquotes_baseline_reference.json \
  --output-dir ML/reports/cross_instrument_robustness/full_matrix
```

## Выходные файлы

- `summary.csv`
- `summary.json`
- `provider_drift.csv`
- `transfer_matrix.csv`
- `trades.csv`
- `run_metadata.json`

## Ограничения

- Это research benchmark, а не замена MT4 forward-check.
- Модуль не переобучает модель и не ретюнит thresholds.
- Если signal timestamps не покрываются OHLC, benchmark должен падать с явной ошибкой, а не молча пропускать строки.
- `provider_drift` и `cross_instrument_transfer` надо читать как две разные таблицы: один и тот же output-dir может содержать оба вида verdict, но их нельзя смешивать в одну итоговую интерпретацию.
