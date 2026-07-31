# CONTEXT HANDOFF

## Current Active State

- active track: `MT5 execution-loop prototype`
- latest report: `docs/reports/2026-07-30-mt5-single-rule-diagnostic-run.md`
- latest plan: `docs/superpowers/plans/2026-07-30-mt5-single-rule-diagnostic-run.md`
- primary MT5 expert: `MT/MQL5/Experts/$o$imple.mq5`
- MT5 signal schema validator: `ML/baseline/mt5_signal_schema.py`
- MT5 execution methodology: `docs/methodology/13b-mt5-execution-parity.md`
- MT5 open-position feature contract: `docs/schemas/mt5_open_position_feature_contract.md`
- MT5 producer contract: `docs/schemas/mt5_nero_csv_contract.md`
- Python exporter: `ML/baseline/export_mt5_entry_signals.py`
- Python event parser: `ML/baseline/parse_mt5_execution_report.py`
- run manifest: `ML/reports/mt5_execution_loop/mt5_single_rule_run_manifest_20260730_entry_quality_filter.json`
- event CSV: `ML/reports/mt5_execution_loop/mt5_trade_events_20260730_entry_quality_filter.csv`
- metrics JSON: `ML/reports/mt5_execution_loop/mt5_execution_metrics_20260730_entry_quality_filter.json`

## Decision

Single-rule MT5 diagnostic tester run is COMPLETED end-to-end, status stays
`DIAGNOSTIC_ONLY`. Decision: continue.

- verdict: `DIAGNOSTIC_ONLY`
- compile status: MetaEditor reports `0 errors, 0 warnings`
- tester runtime status: full run passed (XAUUSD H1, 2019.06.20–2022.12.03,
  Model=1, 20427 bars, `Test passed in 0:08:00`)
- event metrics: 294 ORDER_PLACED / 252 OPEN / 18 CLOSE / 53 ML_CLOSE;
  timing contract PASS 2532/2532 trade rows
- MT5 `Nero.csv` producer parity: `NOT TESTED` (`Nero_MT5.csv` создан, 191 МБ)
- same_h1_lifecycle_status: `UNKNOWN` (нет independent deals/tester report)

## Current Diagnostic Facts

- Headless запуск tester работает: `WINEPREFIX=~/.mt5 xvfb-run -a wine
  terminal64.exe /portable /config:C:\mt5_test.ini` (путь конфига без пробелов;
  путь с пробелами парсится с лишней кавычкой).
- LiveUpdate payload в `.../AppData/Roaming/MetaQuotes/Terminal/<id>/liveupdate/`
  заставляет терминал выйти сразу после старта; перед запуском убрать `mt5*.NNNN`.
- Runtime Files каталог — tester agent:
  `~/.mt5/drive_c/Program Files/MetaTrader 5/Tester/Agent-127.0.0.1-3000/MQL5/Files/`;
  сигнальный CSV доставляется туда только через
  `#property tester_file "mt5_entry_signals.csv"` (добавлен в `$o$imple.mq5`).
- Исправлена серия `array out of range` (SERVICE.mqh, MAIN.mqh, lib_PIC.mqh,
  MQL4Compat.mqh): compat-массивы теперь заполняются в OnInit и копируют всю
  историю; `Time[Bars-1]` заменён на `iTime()`; `EXP[]` расширяется в tester-ветке.
- CLOSE восстановление ограничено (`broker_history_limited`), 234 OPEN без
  CLOSE не классифицированы построчно.
- Tester HTML report не создаётся (`Report=` с относительным путём в INI не
  сработал под wine).

## Do Not Do

- Do not interpret tester run as profitable/production-ready or as rule quality proof.
- Do not use tester PnL for selection; lifecycle events are incomplete (18 CLOSE vs 252 OPEN).
- Do not treat timing-contract PASS as leakage-safety proof: bridge копирует
  `signal_time` во все временные поля (trivial contract).
- Do not run batch selection until OPEN-without-CLOSE classified and Nero parity
  tested or explicitly bounded.
- Do not treat the diagnostic scorer as ML-quality proof.

## Next Step

1. Классифицировать 234 OPEN-без-CLOSE (ticket-трассировка или
   `OnTradeTransaction`-логирование).
2. Проверить `Nero_MT5.csv` parity против MT4 `Nero.csv` или явно ограничить
   диагностическим статусом.
3. После этого — переход к `MT5 batch selection for 20-50 candidates`
   (roadmap `NEXT_AFTER_MT5_SINGLE_RULE`).

## Verification

Completed:

- `./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py tests/test_parse_mt5_execution_report.py -q` → 13 passed
- MetaEditor compile of `MT/MQL5/Experts/$o$imple.mq5`: `Result: 0 errors, 0 warnings`
- `validate_mt5_event_frame` PASS on real event CSV
- sha256 hashes recorded in `docs/reports/2026-07-30-mt5-single-rule-diagnostic-run.md`

Full `./.venv/bin/python -m pytest tests/ -q` was not run because the plan
explicitly forbids the full suite.
