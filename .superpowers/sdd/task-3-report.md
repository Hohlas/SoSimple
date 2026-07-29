# Task 3 Report: fixed11 current-history comparison

## Context

Task 3 compares the original fixed11 locked-test result against the new current-history locked-test result and writes a structured comparison artifact at `ML/reports/fractal0_fixed11_current_history_comparison.json`.

Scope stayed diagnostic only. I did not change execution logic, runner rules, cutoffs, profiles, models, targets, filters, stops, entry/exit policies, spread, or PnL convention.

## Commands

1. Read the task brief:
   `sed -n '1,260p' /home/hohla/git/SoSimple/.superpowers/sdd/task-3-brief.md`
2. Read methodology:
   `sed -n '1,260p' docs/methodology/10-frozen-test-oos.md`
   `sed -n '1,260p' docs/methodology/16-reporting-audit.md`
3. Create the comparison artifact with the inline read-only script from the brief:
   `./.venv/bin/python - <<'PY' ... PY`
4. Verify the comparison structure:
   `./.venv/bin/python - <<'PY' ... PY`
5. Inspect retained slot 1 same-H1 risk:
   `./.venv/bin/python - <<'PY' ... PY`

## Key Results

- Comparison artifact created: `ML/reports/fractal0_fixed11_current_history_comparison.json`
- Input hashes recorded in the artifact for both JSON and trade CSV inputs.
- All 11 fixed rules are covered.
- Aggregate old vs current:
  - old: 14,507 trades, `pnl_r_sum=4429.782419`, `pf=3.09752`, `hold_bars_0=5100`
  - current: 13,039 trades, `pnl_r_sum=4065.034595`, `pf=3.116313`, `hold_bars_0=4495`
- Aggregate close reasons:
  - old: `ML_CLOSE=10448`, `TIME=3582`, `SL=477`
  - current: `ML_CLOSE=9345`, `TIME=3230`, `SL=464`
- Retained slot 1 (`rank05_time_only_linear_target_entry_avoid_sl_top30`):
  - old: 1,196 trades, `pnl_r_sum=395.026902`, `pf=3.295678`, `hold_bars_0=406`
  - current: 1,091 trades, `pnl_r_sum=339.192111`, `pf=3.113871`, `hold_bars_0=368`
- Same-H1 / zero-hold risk for retained slot 1 in current-history:
  - `slot1_trades=1091`
  - `slot1_same_h1_fill_exit=368`
  - `slot1_hold_bars_0=368`
  - `slot1_hold0_close_reasons={'ML_CLOSE': 335, 'SL': 33}`
  - `slot1_hold0_pnl_r_sum=-98.196808`

## Changed Files

- `ML/reports/fractal0_fixed11_current_history_comparison.json`
- `.superpowers/sdd/task-3-report.md`

## Self-check

- Confirmed the comparison JSON exists and is valid JSON.
- Confirmed `len(per_rule) == 11`.
- Confirmed `logic_change == "none"` and `status == "DIAGNOSTIC_ONLY"`.
- Confirmed all four recorded input hashes are 64 hex characters.
- Confirmed the retained slot 1 diagnostic was run on `fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv` with `sep=';'`.
- Confirmed no full `pytest` run was executed.
- Re-ran Task 3 Step 2 after correcting the `comparison_key` label to `signal_time + side + rule_id`; output stayed `comparison_ok` with `rules 11`.

## Notes

- The comparison is structural only and does not choose a new winner.
- The slot 1 same-H1 / hold_bars=0 concentration is material and should be carried into the next report stage.
