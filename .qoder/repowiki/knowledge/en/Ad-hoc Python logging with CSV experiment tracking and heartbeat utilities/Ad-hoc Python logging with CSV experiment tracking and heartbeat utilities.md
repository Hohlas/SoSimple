---
kind: logging_system
name: Ad-hoc Python logging with CSV experiment tracking and heartbeat utilities
category: logging_system
scope:
    - '**'
source_files:
    - API/telemetry_signal_watcher.py
    - ML/experiment_logger.py
    - ML/baseline/benchmark_stage5_transformer_breach.py
---

The repository does not use a centralized logging framework. Instead, it relies on ad-hoc, per-module logging patterns built on the Python standard library `logging` module and plain `print()` statements.

**Runtime process logging (telemetry watcher)**
- `API/telemetry_signal_watcher.py` is the only place that configures a structured logger via `logging.basicConfig`. It sets up two handlers: a `FileHandler` writing to a configurable `.log` file under the runtime output directory, and an optional `StreamHandler` to stdout when `--verbose` is passed. The format is `%(asctime)s %(levelname)s %(message)s`, level defaults to `INFO`, and `force=True` ensures reconfiguration even if other code already configured logging. All operational messages (`WATCHER rebuild start/done`, heartbeats, warnings about unsafe future features) go through this logger.

**Experiment result logging (CSV-based)**
- `ML/experiment_logger.py` defines `CSVExperimentLogger`, which appends one row per training run to `ML/reports/experiments_log.csv`. Each row captures model name, task, seed, git commit, hyperparameters, metrics (MAE/RMSE/R2 for regression, F1 macro/class-specific for classification), training time, best epoch, and checkpoint path. The class auto-creates the CSV header on first use and migrates columns when the schema changes. This logger is used by `ML/train.py` and `ML/baseline/baseline_experiments.py`.

**Heartbeat / progress helpers**
- `ML/baseline/benchmark_stage5_transformer_breach.py` defines a lightweight `HeartbeatLogger` class that rate-limits `print()` calls to stdout at a configurable interval, producing lines like `[heartbeat] ts=... | label | elapsed=...s | message`. A helper `log_step(step)` is also present in the same file for step-level status updates.

**Scattered print() usage**
- Many scripts (e.g., `API/api_server.py`, `API/generate_signals.py`, various benchmark scripts) use bare `print()` for startup/shutdown messages, progress indicators, and table outputs. These are unstructured console logs without levels or sinks.

**No global configuration**
- There is no shared logging configuration module, no log rotation, no structured JSON logging, and no central log aggregation. Each component that needs logging initializes its own handler or prints directly. Log levels are informal — mostly `INFO` and `WARNING` in the watcher, with `ERROR` logged via `logging.exception` on unexpected exceptions.