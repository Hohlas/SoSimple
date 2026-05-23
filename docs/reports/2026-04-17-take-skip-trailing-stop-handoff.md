# Take/Skip Trailing Stop Handoff

> **Date**: 2026-04-17
> **Status**: Ready for remote training

## Local Verification

Commands and results:

- `/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_trailing_stop_task.py tests/test_benchmark_take_skip_trailing_stop.py tests/test_run_take_skip_trailing_stop_matrix.py -q`
- smoke run via `ML.run_take_skip_trailing_stop_matrix` on `seq_len=20`, `epochs=1`, `patience=1`
- smoke run finished end-to-end: `train -> evaluate_test -> generate_signals -> benchmark`
- smoke result: `transformer_seq20` produced `final_verdict = reject`, which is acceptable for this stage because the goal was pipeline validation rather than model quality

## Data Prerequisite

Before remote training, the server-side labeled splits in `DATA/` must already contain the widened trailing-stop columns used by the new track:

- `trail_48_pnl_atr_x2`
- `trail_48_pnl_atr_x3`
- `trail_48_pnl_atr_x4`
- `trail_48_pnl_atr_x6`
- `trail_48_pnl_atr_x8`

If these columns are missing, remote training will fail during dataset loading. In that case, refresh the labeled splits first with the current trailing-stop labeling code before launching the matrix run.

## Remote Command

```bash
MPLCONFIGDIR=/tmp/matplotlib /path/to/.venv/bin/python \
  -m ML.run_take_skip_trailing_stop_matrix \
  --output-dir ML/reports/take_skip_trailing_stop_matrix \
  --seq-lens 20 50 100 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6
```

## Expected Artifacts

- `ML/reports/take_skip_trailing_stop_matrix/manifest.json`
- per-run `summary.json`
- per-run `benchmark/final_verdict.json`
- per-run `benchmark/validation_grid.csv`
- prediction CSVs for validation/test
