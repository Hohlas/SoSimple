---
last_updated: 2026-05-14
sources: 2
status: active
---

# Execution Tracks: Telemetry Demo + MQL Runtime Architecture (04-27 — 04-29)

## 8. Telemetry Frequency Demo Launch (04-27)

После portfolio/correlation этапа появился операционный риск: самые качественные режимы слишком редкие, поэтому на demo-счёте техническая статистика исполнения будет накапливаться годами. Для проверки цепочки `MT -> Nero.csv -> ML -> ml_signals.csv -> MT` выделен отдельный diagnostic режим `telemetry_frequency_v1`.

### Решение и финальный статус

- Частота сделок важнее PF: режим может быть убыточным, потому что его цель - диагностика pipeline.
- Итоговый diagnostic profile: `telemetry_frequency_v1_highfreq500`.
- Для online/forward запуска используется `BackTest=0`: советник читает все
  строки `#.csv` и выбирает строку текущего графика сам. `BackTest=2`
  относится к Strategy Tester, где вручную выбирается одна строка параметров.
- High-frequency export даёт `8872` строк, `495` ненулевых сигналов в 2025, дублей времени `0`.
- SL/TP сохранены в масштабе исходной идеи: `SL=3 ATR`, `TP=5 ATR`, чтобы влияние spread было сопоставимо с нормальной стратегией.
- `max_hold_bars=24`, `max_positions=20` для long-run online diagnostic.
- Export пишет atomically через временный файл и замену целевого `ml_signals.csv`.
- В MQL diagnostic multi-position режим расширяет существующую `EXPERT::ML_TRADE()`, а не создаёт новый контур.

### Reuse decision по MQL

`ORDERS.mqh` полезен как источник проверенных паттернов (`MARKET_UPDATE`, retry/error/reporting style), но его core contract хранит только один `BUY` и один `SELL`. Поэтому прямой multi-position executor оставлен на ticket-level helpers внутри `lib_ML_Signal.mqh`. `SERVICE.mqh` остаётся источником reporting/tester/monitoring helpers для совместимого расширения.

### Diagnostic observability

`MLP BUY/SELL` и `MLP CLOSE` теперь несут поля, достаточные для ежедневной сверки:

- `ticket`;
- `signal_time`, `entry_time`, `exit_time`;
- `atr`, `spread`, `spread_atr`;
- `open_positions`, `MaxPositions`;
- `hold_bars`, `pnl_atr`, `profit`.

Добавлен `ML.telemetry_daily_reconciliation`: сверяет `ml_signals.csv` с MT4 `MLP` log, пишет `signals_diff.csv`, `trades_reconciliation.csv`, `summary.json`, `summary.md`, и возвращает exit code `1` при критичных расхождениях (`missing_open`, `wrong_direction`, `unexpected_open`).

Для закрытий, которые выполнил брокер/тестер по `TakeProfit` или `StopLoss`, `lib_ML_Signal.mqh` сканирует историю ордеров и пишет структурированную строку `MLP CLOSE ... source=broker_history`. Это убирает зависимость daily reconciliation от нестабильного формата стандартных строк MT4 tester log.

Для последующего объяснения расхождений online/test добавлен отдельный
машинный журнал `MT/MQL4/Files/ml_trade_events.csv`: `OPEN`/`CLOSE`, `Bid/Ask`,
spread, OHLC бара, фактические цены ордера, проскальзывание, SL/TP, profit,
swap, commission, balance/equity.

### Tester proof

Финальный MT4 tester proof на `XAUUSD,H1`, 2025:

| Metric | Value |
|---|---:|
| expected_signals | 495 |
| opened_trades | 468 |
| position_blocked | 27 |
| broker_tp_closes | 77 |
| broker_sl_closes | 138 |
| critical_mismatch_count | 0 |
| missing_close_count | 1 |
| OnTester returns | 15064.255859375 |

`missing_close_count=1` объясняется открытой позицией на конце периода. На
дату 2026-04-27 diagnostic-контур считался готовым к online demo launch как
механическая цепочка. Этот вывод позже уточнён contract hardening-ом
2026-04-29: legacy `original_baseline` не является ML-корректным online
контрактом. Прибыльность tester-прогона не считать production-доказательством
качества стратегии.

Источник: [2026-04-27-telemetry-frequency-demo-launch.md](../../docs/reports/2026-04-27-telemetry-frequency-demo-launch.md)

## 9. MQL Runtime Architecture Snapshot (04-28)

После локального M1-прогона стало понятно, что online demo требует отдельной фиксации runtime-архитектуры MQL и watcher-а.

### MQL startup state

Эксперт больше не стартует в холодном состоянии:

- `OnInit()` читает `#.csv`, создаёт активные `EXP[]` строки и вызывает `EXP[e].INIT()`;
- затем выполняется `RECOUNT_HISTORY()`;
- `RECOUNT_HISTORY()` прогоняет доступную историю от старых баров к новым через `EXP[e].PIC()`;
- после прогрева восстанавливаются `bar=1` и `BarTime=Time[0]`.

Цель не просто набрать первые 100 уровней, а восстановить `F[]` с учётом старых сильных фракталов, которые важны из-за критерия удаления слабых уровней.

### PIC as atomic calculation step

`POC_SIMPLE()` перенесён внутрь `PIC()` и выполняется после `NEW_LEVEL()`, `LEVELS_FIND_AROUND()` и `LOCAL_TREND()`. Поэтому historical warmup и online bar-by-bar проход теперь используют один расчётный шаг.

### Watcher memory contract

Watcher больше не держит весь `Nero.csv` в памяти на каждом новом уровне:

- строит `runtime_input_snapshot.csv` из хвоста `Nero.csv`;
- default window: `--max-runtime-rows 12000`;
- с 2026-04-29 строит `runtime_input_preprocessed.csv` через causal subset
  training pipeline: сортировка фракталов по времени и `normalize_rowwise()`
  без future-derived labels;
- проверяет сортировку фракталов после preprocessing;
- запускает `normalize_rowwise(verbose=False)`, чтобы runtime log не засорялся;
- блокирует legacy checkpoint в контракте
  `original_contour / original_baseline / seq_len=50` по умолчанию, потому что
  его training/test input включает future-derived row features (`predict`,
  `ret_*`, `fav_*`, `adv_*`);
- затем применяет frozen diagnostic rule и обновляет `ml_signals.csv`.

Full-vs-12000 проверка на хвосте:

| Metric | Value |
|---|---:|
| full prediction rows | 63010 |
| snapshot rows | 12000 |
| max `pred_*` abs diff | `<= 3.37e-7` |
| signal mismatches | 0 |

### Online diagnostic direction source

Live `Nero.csv` уже формируется и дописывается, но raw строки имеют:

- `signal=0`;
- `predict=0`.

Это не считается MQL-ошибкой: `predict` в offline pipeline формируется
разметкой с просмотром будущих строк (`predict = -back * direction`), поэтому
такой же `predict` нельзя честно получить в live-момент появления строки.

Для diagnostic online-export источник направления заменён на текущий
`fractal0.direction` после сортировки с обратным знаком:

- `fractal0.direction = -1` -> BUY;
- `fractal0.direction = 1` -> SELL.

Локальный watcher rebuild после изменения дал `11459` строк,
`500` ненулевых сигналов (`444` BUY, `56` SELL), без duplicate time rows и
same-time opposite-signal groups.

Ограничение: это решение относится к diagnostic telemetry-режиму для набора
статистики исполнения. Перед production-переходом нужно отдельно проверить,
что выбранный online-источник направления соответствует финальной обучающей
постановке.

2026-04-29 update: текущий watcher больше не подаёт raw `Nero.csv` напрямую в
модель. Raw snapshot сохраняется отдельно, затем online preprocessing приводит
фракталы и масштабы признаков к обучающему контракту в live-safe части.

2026-04-29 contract hardening: последующий аудит выявил, что
`original_baseline` использовал future-derived row features как вход модели.
Поэтому watcher теперь не запускает этот legacy contract online без явного
`--allow-unsafe-future-features`. Такой override допустим только для проверки
механической цепочки MT4 -> Python -> CSV -> MT4, а не для вывода о качестве
ML. Следующий ML-корректный шаг - live-safe retrain с тем же набором признаков
в training/test и online.

Источники: [2026-04-28-mql-runtime-architecture-snapshot.md](../../docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md),
[2026-04-29-online-inference-contract-hardening.md](../../docs/reports/2026-04-29-online-inference-contract-hardening.md)
