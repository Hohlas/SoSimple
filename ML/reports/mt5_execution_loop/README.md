# MT5 Execution Loop Reports

This directory stores diagnostic exports for the MT5 entry-only execution loop.

Artifacts follow the naming pattern:

- `mt5_entry_signals_<run_id>.csv`
- `mt5_entry_signals_<run_id>.json`

The CSV is entry-only by contract:

- keeps entry decision columns only;
- includes static risk parameters such as `limit_price`, `stop_price`, `atr`, `max_fill_lag_bars`;
- does not carry `fill_time`, `exit_time`, `pnl_r`, or other future outcome fields.

The JSON sidecar records:

- row counts;
- side counts;
- duplicate-time counts;
- input and output hashes;
- rule metadata hashes;
- run configuration hash.

This directory is for reproducible diagnostics and parity checks, not for storing live trading state.
