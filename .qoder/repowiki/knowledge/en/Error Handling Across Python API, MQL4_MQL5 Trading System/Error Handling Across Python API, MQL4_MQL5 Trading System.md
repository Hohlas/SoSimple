---
kind: error_handling
name: Error Handling Across Python API, MQL4/MQL5 Trading System
category: error_handling
scope:
    - '**'
source_files:
    - API/api_server.py
    - API/telemetry_signal_watcher.py
    - ML/baseline/audit_leaderboard_robustness.py
    - MT/MQL4/Include/stderror.mqh
    - MT/MQL4/Include/StdLibErr.mqh
    - MT/MQL4/Indicators/iPIC.mq4
    - MT/MQL4/Experts/$o$imple.mq4
---

This repository implements error handling across two distinct runtime environments — a Python FastAPI service and telemetry watcher, and MetaTrader MQL4/MQL5 expert advisors — with no unified cross-language error framework. Each layer follows its platform's idioms.

**Python side (API + telemetry)**
- Custom exception hierarchy: `OnlineInferenceContractError` (subclass of `RuntimeError`) is raised when the online inference contract is violated (e.g., future-derived features in legacy mode). A parallel hierarchy `LeaderboardAuditError`, `GlobalArtifactContractError`, `LeaderboardContractError` (all subclasses of `ValueError`) is used by audit scripts to signal contract/schema failures.
- Validation-driven errors: `validate_online_inference_contract()` raises `OnlineInferenceContractError` for unsafe feature sets; parameter validation raises plain `ValueError` for unsupported modes or invalid arguments.
- HTTP-level errors: The FastAPI server (`api_server.py`) uses `HTTPException` with explicit status codes (400 for malformed requests, 500 for misconfiguration) inside request handlers.
- Telemetry watcher loop: The main polling loop wraps each `run_once()` call in a bare `try/except Exception` that logs via `logging.exception(...)` and continues — ensuring the watcher survives transient failures without crashing.
- Logging: All modules use Python's `logging` module configured per-process; the watcher writes to both file and optional stdout, emitting structured heartbeat messages.

**MQL4/MQL5 side**
- Error constants: MQL4 includes `stderror.mqh` and `StdLibErr.mqh` which define hundreds of numeric error codes for trade server responses, runtime errors, file I/O, objects, notifications, etc. These are `#define` constants rather than typed exceptions.
- Runtime error checking: The codebase uses an `ERROR_CHECK(__FUNCTION__)` macro pattern (defined in indicators like `iPIC.mq4`) that calls `GetLastError()` after trade operations and returns whether retry is needed. This is called at key points (e.g., end of `INPUT()`, after order operations).
- Diagnostic output: Errors and diagnostics are emitted through `Print(...)`, `Alert(...)`, and `Comment(...)` — the standard MQL4 logging mechanisms. There is no structured logging framework.
- No `panic/recover` equivalent: MQL4/MQL5 does not support try/catch or panic/recover; error propagation relies on return codes and global `GetLastError()` state.

**Architecture and conventions**
- Python errors are either domain-specific custom exceptions (for contract violations) or standard exceptions (`ValueError`, `FileNotFoundError`, JSON/parse errors), caught at appropriate boundaries (handler level for HTTP, loop level for watchers).
- MQL4 errors are treated as numeric status codes checked after each critical operation, with human-readable diagnostics printed to the terminal/log.
- The two layers communicate via CSV files (`Nero.csv`, `ml_signals.csv`) and a REST API — errors crossing this boundary are represented as HTTP status codes (Python) and file-not-found / parse errors (MQL4 reading CSVs).

**Conventions and constraints**
- Online inference contract guard is enforced by default for legacy modes; bypass requires an explicit `--allow-unsafe-future-features` flag.
- Audit scripts consistently wrap their main logic in try/catch blocks that map specific exception types to structured JSON output with `status: "UNKNOWN"` and `contract_errors` fields.
- The telemetry watcher treats all exceptions as non-fatal, logging and continuing — appropriate for a long-running monitoring process.