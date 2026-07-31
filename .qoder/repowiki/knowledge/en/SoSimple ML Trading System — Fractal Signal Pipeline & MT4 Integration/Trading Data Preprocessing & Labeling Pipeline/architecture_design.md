The module is a flat collection of Python scripts organized as a sequential pipeline with clear dependency direction:
- `fractal_preprocessing.py` provides the foundational `sort_fractals_in_dataframe()` used by both offline and online paths.
- `label_signals.py` implements all labeling logic (`label_all`, `label_updn`, `label_triple_barrier`, etc.) and is imported by the orchestrator.
- `normalize.py` implements piecewise linear-log normalization per fractal pair (per-row brk/cap parameters saved as `*_updn_params.npy`) and ATR RobustScaler; it is consumed by both `label_main.py` and `online_causal_preprocessing.py`.
- `label_main.py` is the CLI orchestrator that chains sort → label → normalize → split → save into `DATA/{stem}_train/validation/test_labeled.csv`.
- `online_causal_preprocessing.py` exposes a live-safe subset (`preprocess_online_frame`, `preprocess_online_csv`) that deliberately excludes any future-bar labeling steps.
- Utility scripts (`purge_split.py`, `denormalize_updn.py`, `rebuild_xauusd_top_level_updn.py`, `label_audit.py`) operate on already-produced artifacts without importing each other, keeping them independent tools.

Data flows through pandas DataFrames with semicolon-delimited CSV I/O. The canonical fractal format is a fixed 23-field colon-separated string stored in `fractal0..fractalN` columns, parsed via shared `parse_fractal` functions. Normalization parameters are persisted as NumPy `.npy` arrays alongside the CSV splits.