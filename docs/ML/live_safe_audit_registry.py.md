# ML/live_safe_audit_registry.py

Registry of profitable ML systems included in the live-safe audit.

It lists the frozen checkpoint, rule, prediction files, and source reports for:
- `quality`;
- `frequency`;
- `original_plus_path`;
- `entry_path_v1`;
- `entry_path_v1_quantile`.

The registry is used by `ML/run_live_safe_ml_audit.py` to build inventories,
feature contracts, verdicts, and legacy export replay artifacts.

Changing this file changes the audit scope.
