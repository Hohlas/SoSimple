---
last_updated: 2026-05-14
sources: 2
status: active
---

# Execution Tracks: Cross-Instrument Robustness + Portfolio Check (04-24)

## 6. Cross-Instrument Robustness Check (04-24)

Этап был специально разделён на две независимые проверки:

- `provider_drift_baseline` на том же `XAUUSD`;
- `cross_instrument_transfer` на `XAGUSD`, `EURUSD`, `GBPUSD`, `USDCHF`.

Это убрало главную методологическую ошибку: нельзя объяснять провал переноса на новом рынке только сменой провайдера котировок.

### Provider drift baseline

Для `XAUUSD MetaQuotes -> Alpari` все три системы сохранили статус `provider_stable`:

- `quality`
- `frequency`
- `original_plus_path`

Практический вывод: drift котировок заметен в сыром `OHLC/Nero`, но сам по себе не разрушает текущие frozen execution-tracks на том же инструменте.

### Cross-instrument transfer

| Instrument | `quality` | `frequency` | `original_plus_path` |
|---|---|---|---|
| `XAGUSD` | failed | supported | failed |
| `EURUSD` | failed | failed | failed |
| `GBPUSD` | inconclusive | inconclusive | supported |
| `USDCHF` | supported | supported | supported |

Итог по breadth:

- `quality`: `1 supported / 1 inconclusive / 2 failed`
- `frequency`: `2 supported / 1 inconclusive / 1 failed`
- `original_plus_path`: `2 supported / 0 inconclusive / 2 failed`

Ключевые наблюдения:

- `EURUSD` — самый жёсткий negative case: все три режима провалились.
- `USDCHF` — strongest positive case: все три режима сохранили practical viability.
- `frequency` оказался самым живучим по ширине переноса.
- `original_plus_path` не универсален, но по breadth выглядит сильнее `quality`.
- `quality` остаётся самым строгим режимом по качеству отдельных прогонов, но не самым устойчивым по переносу.

Структурный вывод: после этого этапа главный следующий вопрос уже не “переносится ли система вообще”, а “какие из подтверждённых систем достаточно независимы, чтобы их объединять в portfolio-layer”.

Источник: [2026-04-24-cross-instrument-robustness-check.md](../../docs/reports/2026-04-24-cross-instrument-robustness-check.md)

## 7. System Correlation And Portfolio Check (04-24)

После provider-drift и transfer-проверок главный вопрос стал portfolio-level: какие из пяти зрелых `XAUUSD` систем действительно добавляют новый risk profile, а какие просто дублируют тот же слой входов.

Проверялись:

- `quality`
- `frequency`
- `original_plus_path`
- `entry_path_v1`
- `entry_path_v1_quantile`

Канонический benchmark считался по двум видам фактов:

- overlap сделок и совпадение направления;
- корреляция trade/daily/weekly PnL и overlap просадок.

Для `entry_path_v1` и `entry_path_v1_quantile` baseline пришлось честно восстановить из frozen checkpoints и fixed-hold execution, потому что готового `trades.csv` в baseline-артефактах не было.

### Pairwise verdict split on XAUUSD

| Pair | Verdict | Why |
|---|---|---|
| `frequency × original_plus_path` | `redundant` | overlap `1.00`, trade PnL corr `1.00`, daily corr `0.95`, weekly corr `0.94` |
| `quality × entry_path_v1` | `complementary` | daily corr `-0.33`, weekly corr `-0.32`, drawdown overlap `0.00` |
| `quality × entry_path_v1_quantile` | `complementary` | daily corr `-0.28`, weekly corr `-0.25`, drawdown overlap `0.00` |
| `original_plus_path × entry_path_v1` | `complementary` | daily corr `-0.26`, weekly corr `-0.27`, staggered gains `1.00` |
| `original_plus_path × entry_path_v1_quantile` | `complementary` | daily corr `-0.24`, weekly corr `-0.25`, staggered gains `1.00` |
| `quality × frequency` | `partially_overlapping` | time overlap very high, но daily corr около нуля |
| `quality × original_plus_path` | `partially_overlapping` | overlap `0.73`, при этом daily/weekly corr отрицательные |
| `frequency × entry_path_v1` | `partially_overlapping` | overlap `0.78`, но daily/weekly corr слегка отрицательные |
| `frequency × entry_path_v1_quantile` | `partially_overlapping` | overlap `0.77`, но daily/weekly corr слегка отрицательные |
| `entry_path_v1 × entry_path_v1_quantile` | `partially_overlapping` | overlap `1.00`, trade PnL corr `~1.00`, daily/weekly corr `0.55` |

### Practical portfolio reading

- `frequency` и `original_plus_path` не надо считать двумя независимыми sleeves. На `XAUUSD` это почти один и тот же поток сделок.
- `entry_path_v1_quantile` даёт другой risk profile относительно `quality` и `original_plus_path`, но не выглядит независимой третьей системой поверх baseline `entry_path_v1`.
- Самая прагматичная первая portfolio-basis:
  - `quality + entry_path_v1_quantile`
  - плюс optional третий sleeve: либо `frequency`, либо `original_plus_path`, но не обе сразу.

Это важный сдвиг в roadmap: после этого этапа вопрос уже не “найти ещё один красивый single-system backtest”, а “собрать bounded portfolio-layer без скрытого дублирования риска”.

Источник: [2026-04-24-system-correlation-and-portfolio-check.md](../../docs/reports/2026-04-24-system-correlation-and-portfolio-check.md)
