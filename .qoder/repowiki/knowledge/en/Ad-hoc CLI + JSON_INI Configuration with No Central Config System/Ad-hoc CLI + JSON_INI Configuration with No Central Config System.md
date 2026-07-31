---
kind: configuration_system
name: Ad-hoc CLI + JSON/INI Configuration with No Central Config System
category: configuration_system
scope:
    - '**'
source_files:
    - API/api_server.py
    - API/telemetry_signal_watcher.py
    - ML/train.py
    - statistics/signal_tracer.py
    - MT/tester/$o$imple.ini
    - ML/utils.py
---

This repository does not implement a centralized configuration system. Instead, configuration is scattered across three ad-hoc mechanisms that are each used by specific modules:

1. **Python `argparse` CLI arguments** — Nearly every entry point (`API/api_server.py`, `API/telemetry_signal_watcher.py`, `ML/train.py`, `statistics/signal_tracer.py`, and all benchmark/export scripts) defines its own `ArgumentParser` with `--flag` parameters for paths, thresholds, modes, and runtime switches. There is no shared config loader; each script parses its own flags independently.

2. **Hardcoded Python constants / dataclasses** — Runtime defaults live as module-level constants (e.g., `MODEL_NAME`, `TASK`, `HORIZON`, `THETA` in `api_server.py`; `DEFAULT_*` path constants in `telemetry_signal_watcher.py`; `DEFAULTS` dict in `train.py`) or lightweight `dataclass` settings like `MLServiceSettings` and `WatcherState`. These are the primary source of truth for production behavior when no CLI overrides are supplied.

3. **External JSON and INI files** — Model hyperparameters come from Optuna best-parameter JSONs under `ML/reports/optuna_best_params_transformer_regression_updn.json`, which the API server loads at startup to override model architecture kwargs. Rule/threshold JSONs (e.g., `entry_path_v1_live_safe_a075_rule.json`, `selected_rule.json`) are loaded by signal export/watcher scripts. Legacy MT4 tester parameters are read from `MT/tester/$o$imple.ini` via a custom `parse_ini()` function in `statistics/signal_tracer.py` that extracts `ML_*` keys from the `<inputs>` section.

There is no `.env` file, no `pydantic.BaseSettings`, no YAML/TOML/INI central loader, and no environment-variable-driven configuration layer beyond the single CUDA reproducibility variable `CUBLAS_WORKSPACE_CONFIG=:4096:8` set globally in `ML/utils.py` and several training scripts.

**Key conventions observed:**
- Path configuration is expressed as `Path` objects relative to `PROJECT_ROOT = Path(__file__).resolve().parent.parent`, never absolute paths.
- Production defaults are always defined inline in code; external files (JSON rules, Optuna params, INI) are optional overrides with explicit fallbacks.
- The telemetry watcher enforces an "online inference contract" guard that blocks feature sets requiring future-derived fields unless explicitly overridden via `--allow-unsafe-future-features`.
- State persistence between runs uses small JSON files (`runtime_state.json`, `runtime_export_metadata.json`) written by the watcher process itself.

**Enforced constraints (from code):**
- The FastAPI `/predict` endpoint rejects horizons not in `{12, 24, 48}` with an HTTP 500 error.
- The telemetry watcher raises `OnlineInferenceContractError` for the `original_contour/original_baseline` mode unless `--allow-unsafe-future-features` is passed.
- `read_csv_tail_lines` validates `max_data_rows > 0` and `initial_block_size > 0`, raising `ValueError` otherwise.
- The INI parser only accepts keys matching `ML_\w+` within the `<inputs>` section, ignoring other lines.