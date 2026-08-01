# CONTEXT HANDOFF

## Current Active State

- active track: `MT5 batch selection → post-batch diagnostics`
- latest report: `docs/reports/2026-07-31-mt5-batch-selection.md`
- latest plan: `docs/superpowers/plans/2026-07-31-mt5-batch-selection.md`
- primary MT5 expert: `MT/MQL5/Experts/$o$imple.mq5`
- batch script: `ML/baseline/run_mt5_batch.py`
- batch summary: `ML/reports/mt5_execution_loop/batch/batch_summary.json`
- MT5 execution methodology: `docs/methodology/13b-mt5-execution-parity.md`

## Decision

Batch selection завершён. Verdict: **BATCH_NO_WINNER**.

- 32 кандидата прогнаны через MT5 Strategy Tester (Model 1, XAUUSD H1)
- Validation period: 2021.01.04–2022.12.02
- Все 32: UNEXPLAINED=0 (reconciliation PASS)
- 11 eligible (trades>=100): ни один не прошёл BS_p05 > 1.0
- Лучший: time_plus_atr_extra_trees_small_12h_thr0.2 (PF=1.232, BS_p05=0.887)
- Holm-Bonferroni: 0 отклонённых гипотез
- Status: DIAGNOSTIC_ONLY (no trading conclusions)

## Current Diagnostic Facts

- Entry CSV копируется в **Terminal** MQL5/Files (не Tester Agent Files):
  `~/.mt5/drive_c/Program Files/MetaTrader 5/MQL5/Files/mt5_entry_signals.csv`.
  `#property tester_file` копирует оттуда в agent при старте.
- INI кладётся на Wine C: drive: `~/.mt5/drive_c/mt5_batch_{run_id}.ini`,
  запуск: `/config:C:\mt5_batch_{run_id}.ini`.
- LiveUpdate: гипотеза/наблюдение оператора — после ~14-го кандидата терминал
  мог попытаться автообновиться; каталог впоследствии заблокирован (chmod 555).
  Факт не покрыт batch artifact (логом, `ls/stat`); при разблокировке терминал
  скачивает обновление и перехватывает запуски.
- Fill rate низкий: из 265–1737 сигналов исполняется 16–151 сделка.
- Smoke test: Model 2, 2021.01–2021.03, ~1 сек. Full: Model 1, ~1 мин/кандидат.

## Do Not Do

- Do not interpret tester run as profitable/production-ready or as rule quality proof.
- Do not use tester PnL for selection or quality claims without locked_test.
- Do not treat timing-contract PASS as leakage-safety proof.
- Do not treat the diagnostic scorer as ML-quality proof.
- Do not unblock liveupdate directory without moving payload files first.

## Next Step

1. Диагностический анализ: почему top-кандидаты (PF 1.17–1.23) не проходят
   bootstrap — мало сделок или высокая дисперсия.
2. Расширение периода (полный order mechanics 2019.06–2022.12) для выборки.
3. Cost model: swap/commission по docs/methodology/12-backtest-costs.md.
4. Отдельный val-eval split для снятия потолка RESEARCH_ONLY.

## Verification

Completed:

- 32/32 entry CSV: schema PASS (`validate_mt5_signal_frame`)
- 32/32 events: UNEXPLAINED=0, 32 unique hashes
- MetaEditor compile: `0 errors, 0 warnings`
- Smoke test (Model 2): UNEXPLAINED=0
- Block bootstrap + Holm-Bonferroni: BATCH_NO_WINNER
