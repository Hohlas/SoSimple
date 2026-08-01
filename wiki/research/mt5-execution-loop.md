---
last_updated: 2026-08-01
sources: 8
status: active
---

# MT5 Execution Loop

> MT5 стал текущим диагностическим execution-контуром после invalidation fixed11 chronology; доступные repo-артефакты классифицированы, старые saved artifacts сохраняют row-level error/event linkage `UNKNOWN`, а будущие `events.csv` получили поля execution context для проверки связи.

## Хронология

### 2026-07-29: MT5 feasibility, runbook and batch design

MT5 feasibility/runbook/design reports зафиксировали переход от MT4/fixed11
parity к MT5 Strategy Tester: primary expert `MT/MQL5/Experts/$o$imple.mq5`,
entry-only signal CSV, tester event log, headless Wine/MetaEditor workflow и
план batch-проверки заранее отобранных кандидатов. Эти документы являются
инфраструктурной подготовкой, не модельным verdict.

### 2026-07-30: Single-rule diagnostic tester run

Первый автономный MT5 tester diagnostic run выполнил entry-quality filter
scenario и сохранил `mt5_trade_events_20260730_entry_quality_filter.csv` и
metrics JSON. Timing contract был диагностически пройден, но lifecycle был
неполным: много `OPEN` без `CLOSE`, `same_h1_lifecycle_status=UNKNOWN`.
Отчёт также зафиксировал `ERROR-4756` lines во внешнем tester-agent log,
9 `ORDER_EXPIRED`, 32 pending-order-not-found observations и ожидаемый, но
непроанализированный `ERROR_SoSimple_163856259.csv`. Эти старые внешние
артефакты больше не используются как источник истины для текущих batch-решений.

### 2026-07-31: OnTradeTransaction lifecycle closure

Добавление `OnTradeTransaction` events закрыло lifecycle для diagnostic
executor: 269 positions, `CLOSED_TX=269`, `UNEXPLAINED=0`, `same_h1_count=17`.
Это доказывает event/deal reconciliation для данного diagnostic contour, но
не является trading/model-quality proof.

### 2026-07-31: Nero parity

MT5 `Nero.csv` producer parity report states `PARITY_PASS` with diagnostic
limitations: match rate 99.05%, direction agreement 99.24%, price p95 diff
0.003. Практический вывод: MT5 может быть source of feature stream for the
next diagnostic steps, but not a production verdict.

### 2026-07-31: Batch selection

32 MT5 Strategy Tester runs on XAUUSD H1 validation 2021.01.04-2022.12.02
ended `BATCH_NO_WINNER`. All 32 were valid; 11 eligible candidates all failed
`BS_p05 > 1.0`; Holm-Bonferroni rejected 0 hypotheses. The best point PF was
`1.2323`, but `BS_p05=0.8867`. Verdict remained `DIAGNOSTIC_ONLY`.

### 2026-08-01: Execution hygiene and post-batch diagnostics

The diagnostics module `ML/baseline/mt5_execution_diagnostics.py` now produces:
error inventory, classified error rows, event anomaly summaries and post-batch
failure attribution. Available repo `ERROR_SoSimple_*.csv` files: 6. Classified
error rows: 1879 (`INVALID_STOPS=670`, `OTHER=621`, `REQUOTE=550`,
`MODIFICATION_TOO_CLOSE=35`, `MARKET_CLOSED=2`, `INVALID_PRICE=1`). Source buckets are separated:
`mt4_files=1174`, `mt_tester_files=705`.

Batch event summary covers 32 candidate runs and excludes `_smoke`.
Batch event counts include `OPEN_FAILED=22767` and `ORDER_EXPIRED=67`.
Post-batch attribution preserves `BATCH_NO_WINNER`: top 11 all failed low
bootstrap lower bound; trade-count buckets are `100-149=9`, `150+=2`; one
candidate failed profit concentration.

Verdict: `DIAGNOSTIC_ONLY`. Execution hygiene status:
`EXECUTION_HYGIENE_PARTIAL`. Current saved repo artifacts are classified.
Historical missing `ERROR_SoSimple_163856259.csv` and cumulative tester-agent
`ERROR-4756` log are abandoned as non-reproducible inputs. The remaining limit is
row-level linkage status `UNKNOWN`.

After the hygiene discussion, future MT5 diagnostic `events.csv` rows were
expanded with `error_code`, `error_class`, `retcode`, `retcode_text`,
`request_seq`, `magic`, `symbol`, and `entry_type`. The parser backfills these
fields for legacy CSVs, so old saved artifacts stay readable but remain
`UNKNOWN` until a new MT5 run writes real request context.

## Ключевые результаты

| Area | Current fact | Source |
|------|--------------|--------|
| Lifecycle reconciliation | `UNEXPLAINED=0` on OnTradeTransaction run | `2026-07-31-mt5-ontradetransaction-lifecycle.md` |
| Nero parity | `PARITY_PASS` with diagnostic limitations | `2026-07-31-mt5-nero-parity.md` |
| Batch verdict | `BATCH_NO_WINNER`, 32 candidates, 11 eligible | `2026-07-31-mt5-batch-selection.md` |
| Error classification | 1879 rows classified, source buckets separated by artifact path | `2026-08-01-mt5-execution-hygiene-postbatch.md` |
| Event linkage | saved artifacts `UNKNOWN`; future expanded `events.csv` can report `REQUEST_CONTEXT_AVAILABLE` | `ML/baseline/mt5_signal_schema.py` |

## Выводы

MT5 diagnostic executor is usable for structured post-batch diagnostics, but
not for trading claims. Hypothesis: available evidence is consistent with low
bootstrap lower bound, small-to-moderate trade counts and low fill rate as
diagnostic failure modes. This is not a proven model conclusion. Historical
external `ERROR-4756` causality is abandoned and must not be used in future
conclusions.

## Открытые вопросы

- Do not use historical `ERROR_SoSimple_163856259.csv` or cumulative
  tester-agent `ERROR-4756` log in future conclusions.
- Plan the next frozen probe from current saved batch artifacts.
- Run the next MT5 diagnostic probe with expanded `events.csv` and check
  `linkage_status` before using row-level execution conclusions.
- Complete cost model: swap, commission, slippage, latency and stress costs.

## Источники

- [2026-07-29 MT5 feasibility](../../docs/reports/2026-07-29-mt5-feasibility.md)
- [2026-07-29 MT5 manual tester runbook](../../docs/reports/2026-07-29-mt5-manual-tester-runbook.md)
- [2026-07-29 MT5 batch selection design](../../docs/reports/2026-07-29-mt5-batch-selection-design.md)
- [2026-07-30 MT5 single-rule diagnostic run](../../docs/reports/2026-07-30-mt5-single-rule-diagnostic-run.md)
- [2026-07-31 MT5 OnTradeTransaction lifecycle](../../docs/reports/2026-07-31-mt5-ontradetransaction-lifecycle.md)
- [2026-07-31 MT5 Nero parity](../../docs/reports/2026-07-31-mt5-nero-parity.md)
- [2026-07-31 MT5 batch selection](../../docs/reports/2026-07-31-mt5-batch-selection.md)
- [2026-08-01 MT5 execution hygiene post-batch](../../docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md)
