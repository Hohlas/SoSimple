# Telemetry Frequency Demo Launch

> **Date**: 2026-04-27 21:25
> **Status**: Completed
> **Goal**: Подготовить частый diagnostic-режим `telemetry_frequency_v1` для онлайн demo-проверки цепочки `MT -> Nero.csv -> ML -> ml_signals.csv -> MT`
> **Related plan/spec**: `docs/superpowers/specs/2026-04-27-telemetry-frequency-demo-launch-design.md`, `docs/superpowers/plans/2026-04-27-telemetry-frequency-demo-launch.md`
> **Related commit**: `32d7c41`

## Context

Проект подошёл к этапу demo-запуска. Production-кандидаты остаются редкими, поэтому на реальном demo-счёте техническая статистика исполнения накапливалась бы слишком долго.

Для проверки транспорта, параметров, сигналов, исполнения, логов и ежедневной сверки выделен отдельный diagnostic-режим `telemetry_frequency_v1`. Его задача - не доказать прибыльность стратегии, а быстро набрать события для проверки online pipeline.

## What Was Done

- Введён high-frequency export поверх `API/export_take_skip_trailing_stop_v2_signals.py`.
- Добавлен diagnostic режим `--diagnostic-all-rows` / `--diagnostic-target-signals-per-year`, который строит частый поток сигналов из ML score и направления `predict`.
- Зафиксирован профиль `highfreq500`: `495` ненулевых сигналов в 2025 году.
- Runtime-файл `ml_signals.csv` пишется атомарно через временный файл и замену целевого файла.
- `lib_ML_Signal.mqh` расширен внутри существующей `EXPERT::ML_TRADE()`, без отдельного нового торгового path.
- Для diagnostic режима разрешены несколько одновременных позиций через `ML_MaxPositions`.
- Добавлена перезагрузка `ml_signals.csv` по времени изменения файла.
- Добавлено подробное MQL-логирование `MLP BUY`, `MLP SELL`, `MLP CLOSE`, `MLP SKIP`.
- Добавлено логирование закрытий, выполненных брокером/тестером по `TakeProfit` и `StopLoss`, через `source=broker_history`.
- Добавлен `ML/telemetry_daily_reconciliation.py` для ежедневной сверки `ml_signals.csv` и MT4 log.
- Описана схема `MT -> Python watcher/exporter -> ml_signals.csv -> MT` в MT-документации.
- Описана логика `#.csv`: файл внешних параметров, выбор строки через `BackTest`, magic/hash, запуск нескольких стратегий с одного графика.
- Watcher переведён в наблюдаемый operational-режим: основной запуск теперь в отдельном окне `tmux`, а не скрытым `nohup`-процессом.
- Добавлен heartbeat в stdout watcher-а: `WAIT`, `IDLE`, `REBUILT`, чтобы оператор видел, что процесс жив.
- `header-only` состояние `Nero.csv` признано штатным: watcher ждёт первый закрытый бар, а не падает с ошибкой.

## Changed Files

- `API/export_take_skip_trailing_stop_v2_signals.py`
- `ML/telemetry_daily_reconciliation.py`
- `MT/MQL4/Include/lib_ML_Signal.mqh`
- `MT/MQL4/Files/#.csv`
- `ML/reports/telemetry_frequency_v1/ml_signals_telemetry_frequency_v1_highfreq500.csv`
- `ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025_final/*`
- `docs/MT/trading_strategy.md`
- `docs/MT/ml_signal_integration.md`
- `docs/ML/telemetry_daily_reconciliation.py.md`
- `tests/test_export_take_skip_trailing_stop_v2_signals.py`
- `tests/test_mql_telemetry_params_csv_contract.py`
- `tests/test_telemetry_daily_reconciliation.py`
- `tests/test_signal_export_parity.py`
- `API/telemetry_signal_watcher.py`
- `tests/test_telemetry_signal_watcher.py`
- `docs/API/telemetry_signal_watcher.py.md`

## Verification

```bash
./.venv/bin/python -m pytest \
  tests/test_export_take_skip_trailing_stop_v2_signals.py \
  tests/test_mql_telemetry_params_csv_contract.py \
  tests/test_telemetry_daily_reconciliation.py \
  tests/test_signal_export_parity.py -q
# 28 passed in 0.70s

./.venv/bin/python -m pytest \
  tests/test_telemetry_signal_watcher.py \
  tests/test_export_take_skip_v2_predictions.py \
  tests/test_export_take_skip_trailing_stop_v2_signals.py \
  tests/test_telemetry_daily_reconciliation.py -q
# 32 passed, 1 warning

./.venv/bin/python -m ML.telemetry_daily_reconciliation \
  --signals MT/tester/files/ml_signals.csv \
  --mt4-log MT/tester/logs/20260427.log \
  --output-dir ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025_final \
  --label telemetry_frequency_v1_highfreq500_final \
  --start-time "2025.01.01 00:00" \
  --end-time "2025.12.31 23:59"
```

## Results

High-frequency signal file:

| Metric | Value |
|---|---:|
| rows_total | 8872 |
| nonzero_signals_2025 | 495 |
| BUY_2025 | 242 |
| SELL_2025 | 253 |
| duplicate_time_rows | 0 |
| sha256 | `8728da8e71d78e2f6aba4ae0743b17300be6a102c117f0267fcb33a798f6ff57` |

MT4 tester proof on `XAUUSD,H1`, 2025:

| Metric | Value |
|---|---:|
| Total signals | 495 |
| Score filtered | 0 |
| Position blocked | 27 |
| Opened | 468 |
| BUY opened | 231 |
| SELL opened | 237 |
| Timeout closes | 252 |
| Broker TP closes | 77 |
| Broker SL closes | 138 |
| Broker other closes | 0 |
| OnTester returns | 15064.255859375 |

Final reconciliation:

| Metric | Value |
|---|---:|
| expected_signals | 495 |
| opened_trades | 468 |
| closed_trades | 467 |
| critical_mismatch_count | 0 |
| missing_close_count | 1 |

`missing_close_count=1` объясняется открытой сделкой на конце периода теста, а не ошибкой исполнения.

## Conclusions

Update 2026-05-11: этот diagnostic-контур выбран как следующий practical
online/forward шаг после MT4 proof `entry_path_v1_live_safe + A`. Активный
`#.csv` переключён на `XAUUSD5`, `ML_MaxPositions=10`,
`ML_TakeProfitATR=5`, `ML_BackStopATR=3`, `ML_HoldBars=24`.
Критерий успеха - не PF, а механическая сверка `MT -> ML -> MT`: rebuild
watcher-а, reload в MT4, открытие/пропуск сигналов и корректные закрытия.

- Контур `MT -> ML signal file -> MT` готов к demo-запуску в diagnostic режиме.
- Для оператора теперь есть наблюдаемый server-режим: watcher штатно живёт в `tmux` и регулярно пишет heartbeat в stdout.
- Несколько одновременных позиций работают: `ML_MaxPositions=10`, в тесте были реальные параллельные позиции и ожидаемые `MaxPositions` пропуски.
- Ошибок `OrderSend` и нехватки денег в тестовом логе не обнаружено.
- Закрытия по SL/TP теперь видны в структурированном `MLP CLOSE` формате, поэтому daily reconciliation больше не зависит от нестабильного формата стандартных строк тестера.
- Положительный результат тестера не является production-доказательством прибыльности: текущий профиль выбран для частоты и диагностики.

## Limitations / Open Questions

- Онлайн demo ещё не запущен; итоговое online/test соответствие нужно подтвердить на удалённом сервере.
- Для online-режима нужен всегда запущенный Python watcher/exporter или эквивалентный сервис, который атомарно обновляет `ml_signals.csv`.
- При переходе со старого `nohup`-запуска на `tmux` на сервере нужно отдельно остановить старый watcher-процесс, иначе можно получить два параллельных exporter-а.
- Runtime CSV-файлы в `MT/MQL4/Files/` и `MT/tester/files/` частично игнорируются git, поэтому их нужно синхронизировать отдельно.
- `knowledge-rag` reindex в конце этапа падал с `Transport closed`; индекс может отставать от последних правок.

## Next Step

1. Слить ветку `telemetry-frequency-demo-launch` в `main`.
2. Обновить удалённый сервер через `git pull`.
3. Отдельно скопировать ignored runtime files:
   - `MT/MQL4/Files/ml_signals.csv`
   - `MT/tester/files/#.csv`
   - `MT/tester/files/ml_signals.csv`
4. На сервере перекомпилировать MT4 expert и запустить online demo на `XAUUSD,M5`.
5. Если на сервере ещё жив старый watcher-процесс, остановить его перед новым запуском:
   - `ps -eo pid,cmd | rg telemetry_signal_watcher`
   - `kill <PID>`
6. Запускать watcher в отдельном окне `tmux`, а не через `nohup`.
7. Ежедневно запускать `ML.telemetry_daily_reconciliation` по свежему MT4 log.

## Related Materials

- `docs/MT/trading_strategy.md`
- `docs/MT/ml_signal_integration.md`
- `docs/ML/telemetry_daily_reconciliation.py.md`
- `docs/superpowers/specs/2026-04-27-telemetry-frequency-demo-launch-design.md`
- `docs/superpowers/plans/2026-04-27-telemetry-frequency-demo-launch.md`
- `ML/reports/telemetry_frequency_v1/ml_signals_telemetry_frequency_v1_highfreq500.csv`
- `ML/reports/telemetry_frequency_v1/tester_reconciliation_highfreq500_2025_final/summary.json`
