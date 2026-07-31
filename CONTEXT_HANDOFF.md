# CONTEXT HANDOFF

## Current Active State

- active track: `MT5 execution-loop → batch selection`
- latest report: `docs/reports/2026-07-31-mt5-nero-parity.md`
- latest plan: `docs/superpowers/plans/2026-07-31-mt5-nero-parity-v2.md`
- primary MT5 expert: `MT/MQL5/Experts/$o$imple.mq5`
- MT5 producer contract: `docs/schemas/mt5_nero_csv_contract.md`
- MT5 execution methodology: `docs/methodology/13b-mt5-execution-parity.md`
- Nero parity script: `ML/baseline/compare_nero_by_time.py`
- Nero parity JSON: `ML/reports/mt5_nero_parity/nero_parity_by_time.json`
- MT4 reference: `MT/tester/files/Nero.csv`
- MT5 output: `ML/reports/mt5_nero_parity/Nero_MT5_v2.csv`

## Decision

Nero.csv producer parity is PROVEN (PARITY_PASS). MT5 может служить
источником feature stream для ML. Status остаётся `DIAGNOSTIC_ONLY`
(no trading conclusions).

- verdict: `PARITY_PASS`
- match rate: 99.05% (по T внутри строки)
- direction agreement: 99.24%
- price p95 diff: 0.003
- bug fixed: MT5 Strong criterion aligned to MT4 (`lib_PIC.mqh:246`)
- compile status: `0 errors, 0 warnings`

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
- Do not use tester PnL for selection or quality claims.
- Do not treat timing-contract PASS as leakage-safety proof.
- Do not treat the diagnostic scorer as ML-quality proof.
- Do not compare fractals by index (fractalN) — only by T within row.

## Next Step

1. Переход к `MT5 batch selection for 20-50 candidates`
   (roadmap `NEXT_AFTER_MT5_SINGLE_RULE`).
2. Классифицировать `ERROR-4756` и `ERROR_SoSimple_*.csv` (диагностические
   файлы тестера, не blocker).

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
