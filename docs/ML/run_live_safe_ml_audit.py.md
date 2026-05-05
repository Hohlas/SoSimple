# ML/run_live_safe_ml_audit.py

Command-line runner for the live-safe ML audit.

Main command:

```bash
./.venv/bin/python -m ML.run_live_safe_ml_audit --phase all --output-dir ML/reports/live_safe_ml_audit
```

Phases:
- `inventory` writes artifact inventories and the manifest;
- `features` writes feature/source trace CSV files;
- `legacy` summarizes frozen historical metrics from old artifacts;
- `legacy-export` replays old signal export from old prediction/rule inputs;
- `verdict` writes `PASS` / `FAIL` / `UNKNOWN` verdicts;
- `all` runs the full audit.

`legacy-export` is diagnostic only. It proves the old export path still runs,
but it does not prove that the model is valid for online trading.
