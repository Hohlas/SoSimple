---
kind: external_dependency
name: MetaTrader 4 — execution platform and data source
slug: metatrader-4
category: external_dependency
category_hints:
    - vendor_identity
    - client_constraint
scope:
    - '**'
---

### MetaTrader 4 (MT4)
- Role in this repo: primary trading platform for live/forward testing, OHLC data source (`XAUUSD_H1_OHLC.csv`, `XAUUSD_M5_OHLC.csv`), and the runtime that executes ML-generated signals via MQL4 libraries (`lib_ML_Signal.mqh`, `lib_ML_Signal_back.mqh`).
- Integration points:
  - `API/generate_signals.py` exports `ml_signals.csv` consumed by MT4's `lib_ML_Signal.mqh` (iSignal=3) or legacy `lib_ML_Signal_back.mqh`.
  - `ML/prepare_entry_path_mt4_parity` copies parity-ready CSVs into `MT/MQL4/Files/` for tester/runtime verification.
  - `statistics/signal_tracer.py` reconciles Python OOS metrics against MT4 tester logs.
- Stable usage model: two incompatible `ml_signals.csv` formats coexist (legacy regression_updn vs current entry_path_v1_live_safe); parity requires frozen export format, hash, and reconciliation report per methodology 13.
- Constraint: M5 OHLC is allowed only as execution-order diagnostic inside H1 bars; it cannot be a feature source or change candidate ranking after seeing locked-test results.
- Verify exact MT4 tester commands, iSignal modes, and MQL4 library interfaces against official MetaQuotes documentation.