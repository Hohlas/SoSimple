# CONTEXT HANDOFF

## Current Active State

- active track: `MT5 execution-loop prototype`
- latest report: `docs/reports/2026-07-31-mt5-ontradetransaction-lifecycle.md`
- latest plan: `docs/superpowers/plans/2026-07-31-mt5-ontradetransaction-lifecycle.md`
- primary MT5 expert: `MT/MQL5/Experts/$o$imple.mq5`
- MT5 transaction logger: `MT/MQL5/Include/lib_ML_Signal.mqh` (`MT5_OnTradeTransaction`)
- MT5 signal schema validator: `ML/baseline/mt5_signal_schema.py` (event-name whitelist)
- MT5 execution methodology: `docs/methodology/13b-mt5-execution-parity.md`
- MT5 open-position feature contract: `docs/schemas/mt5_open_position_feature_contract.md`
- MT5 producer contract: `docs/schemas/mt5_nero_csv_contract.md`
- Python exporter: `ML/baseline/export_mt5_entry_signals.py`
- Python event parser + reconciliation: `ML/baseline/parse_mt5_execution_report.py`
- run manifest: `ML/reports/mt5_execution_loop/mt5_tx_lifecycle_run_manifest_20260731.json`
- event CSV: `ML/reports/mt5_execution_loop/mt5_trade_events_20260731_tx_lifecycle.csv`
- metrics JSON: `ML/reports/mt5_execution_loop/mt5_execution_metrics_20260731_tx_lifecycle.json`

## Decision

OnTradeTransaction lifecycle closure is COMPLETED, status stays
`DIAGNOSTIC_ONLY`. Decision: continue (to Nero parity).

- verdict: `DIAGNOSTIC_ONLY`
- compile status: MetaEditor reports `0 errors, 0 warnings`
- tester runtime status: full run passed (XAUUSD H1, 2019.06.20–2022.12.03,
  Model=1, 20427 bars, `Test passed in 0:08:04`)
- event metrics: 294 ORDER_PLACED / 252 OPEN / 18 CLOSE / 269 TX_OPEN /
  269 TX_CLOSE; polling stream identical to 2026-07-30 run
- reconciliation: `CLOSED_TX=269`, `OPEN_AT_END=0`, `UNEXPLAINED=0`
- same_h1_lifecycle_status: `MEASURED:17` (17 позиций открылись и закрылись
  внутри одного H1 бара — ровно разрыв OPEN 252 vs TX_OPEN 269)
- TX close reasons: `EXPERT=145`, `SL=124`
- MT5 `Nero.csv` producer parity: `NOT TESTED`

## Current Diagnostic Facts

- Headless запуск tester работает: `WINEPREFIX=~/.mt5 xvfb-run -a wine
  terminal64.exe /config:C:\mt5_tx_full.ini` (путь конфига без пробелов).
- Перед запуском проверять: (а) `liveupdate/` payload отсутствует,
  (б) нет уже работающего `terminal64.exe` — второй экземпляр молча выходит.
- Runtime Files каталог — tester agent:
  `~/.mt5/drive_c/Program Files/MetaTrader 5/Tester/Agent-127.0.0.1-3000/MQL5/Files/`.
- TX-строки не несут timing-полей (по дизайну); связь позиция→сигнал делает
  Python reconciliation через polling OPEN-строки (252/269 связаны, 17 —
  same-H1 позиции без OPEN, объяснены).
- Причина слепоты старого polling-CLOSE (18 из 269) — гипотеза
  (ticket vs position id в MODE_HISTORY через MQL4-компат слой), не доказана.
- Tester HTML report не создаётся (`Report=` с относительным путём в INI не
  сработал под wine).

## Do Not Do

- Do not interpret tester run as profitable/production-ready or as rule quality proof.
- Do not use tester PnL (`profit_sum=242.5`) for selection or quality claims.
- Do not treat timing-contract PASS as leakage-safety proof: bridge копирует
  `signal_time` во все временные поля (trivial contract).
- Do not run batch selection until Nero parity tested or explicitly bounded.
- Do not treat the diagnostic scorer as ML-quality proof.

## Next Step

1. Проверить `Nero_MT5.csv` parity против MT4 `Nero.csv` или явно ограничить
   диагностическим статусом.
2. Классифицировать `ERROR-4756` и `ERROR_SoSimple_*.csv`; связать с
   15 отменёнными отложниками + 9 ORDER_EXPIRED из reconciliation 31.07.
3. После этого — переход к `MT5 batch selection for 20-50 candidates`
   (roadmap `NEXT_AFTER_MT5_SINGLE_RULE`).

## Verification

Completed:

- `./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py tests/test_parse_mt5_execution_report.py -q` → 16 passed
- MetaEditor compile of `MT/MQL5/Experts/$o$imple.mq5`: `Result: 0 errors, 0 warnings`
  (`ML/reports/mt5_execution_loop/mt5_compile_20260731_tx_lifecycle.log`)
- smoke run 2019.06.20–2019.07.20: TX events fire under Model 1, UNEXPLAINED=0
- `validate_mt5_event_frame` PASS on real event CSV (incl. event-name whitelist)
- sha256 hashes recorded in
  `ML/reports/mt5_execution_loop/mt5_tx_lifecycle_run_manifest_20260731.json`

Full `./.venv/bin/python -m pytest tests/ -q` was not run because the plan
explicitly forbids the full suite.
