# Live-Safe ML Audit

> **Date**: 2026-05-05
> **Goal**: Re-audit profitable ML systems before any online trading decision.
> **Gate**: [`docs/ML/ml_leakage_preflight_checklist.md`](../ML/ml_leakage_preflight_checklist.md)

## Context

The project had several profitable historical ML systems. After the online
inference contract hardening, high PF is no longer enough: every system must
prove that its model inputs are available at the trading decision time.

This audit separates two things:

- legacy result: old frozen artifact metrics, without retraining or changing thresholds;
- live-safe verdict: whether the same checkpoint/rule can be trusted for online ML quality.

Generated evidence lives in:

- `ML/reports/live_safe_ml_audit/manifest.json`
- `ML/reports/live_safe_ml_audit/<system>/artifact_inventory.json`
- `ML/reports/live_safe_ml_audit/<system>/feature_contract.csv`
- `ML/reports/live_safe_ml_audit/<system>/source_trace.csv`
- `ML/reports/live_safe_ml_audit/<system>/legacy_reproduction.json`
- `ML/reports/live_safe_ml_audit/<system>/legacy_export.csv`
- `ML/reports/live_safe_ml_audit/<system>/legacy_export_metadata.json`
- `ML/reports/live_safe_ml_audit/<system>/verdict.json`

## What Was Done

- Registered five mature systems: `quality`, `frequency`, `original_plus_path`,
  `entry_path_v1`, `entry_path_v1_quantile`.
- Built artifact inventories for checkpoints, rules, predictions, and reports.
- Built feature/source trace tables.
- Applied the leakage/preflight gate.
- Summarized old frozen metrics from existing artifacts only.
- Replayed legacy signal export from old predictions and old frozen rules.
- Wrote explicit verdicts for each system.

No model was retrained. No threshold was changed. No online trading was run.

The follow-up `entry_path_v1_live_safe` retrain below was added after the audit
verdict. It is part of the same decision chain: first reject the unsafe old
checkpoint, then test whether the same trading idea survives without the
future-derived input.

## Legacy Results

These numbers are historical artifact summaries. They are useful for comparing
ideas, but not by themselves enough for online approval.

| System | Legacy test PF | Trades / frequency | Source |
|---|---:|---:|---|
| `quality` | `39.74` | 41 trades | `take_skip_trailing_stop_v2_quality_selected_rule.json` |
| `frequency` | `13.12` | 16.4 trades/year | `take_skip_trailing_stop_v2_frequency_selected_rule.json` |
| `original_plus_path` | `38.78` | 51 trades | `take_skip_trailing_stop_v2_original_plus_path_selected_rule.json` |
| `entry_path_v1` | `2.87` sequential | 30 trades | `entry_path_trade_filter_selected_rule.json` |
| `entry_path_v1_quantile` | `8.18` frozen test, `3.64` sequential | 48 / 22 trades | `entry_path_v1_quantile_selected_rule.json` |

## Audit Tracker

Purpose: keep every profitable historical system visible while the live-safe
rebuild proceeds.

| Historical system | Old verdict | Live-safe state | Next action |
|---|---|---|---|
| `quality` | `FAIL` | Covered by take/skip family rebuilds; direct baseline/path/geometry probes rejected. | Do not use old checkpoint online; revisit only with a new live-safe hypothesis. |
| `frequency` | `FAIL` | Covered by take/skip family rebuilds; direct baseline/path/geometry probes rejected. | Do not use old checkpoint online; revisit only with a new live-safe hypothesis. |
| `original_plus_path` | `FAIL` | Covered by take/skip family rebuilds; direct baseline/path/geometry probes rejected. | Optional closure: run `live_safe_geometry_path` only to complete the feature-mode matrix. |
| `entry_path_v1` | `FAIL` | Rebuilt as `entry_path_v1_live_safe`; still profitable across five seeds, but weaker and variable. | Freeze `A` as the baseline rule family; decide later whether MT4 parity is worth running. |
| `entry_path_v1_quantile` | `FAIL` | Rebuilt over frozen live-safe baseline `A`; profitable pockets remain, but rule selection is unstable. | Keep as research-only; do not promote as the next production layer. |

This table separates historical systems from follow-up feature modes. For
example, `live_safe_path`, `live_safe_geometry`, and `live_safe_geometry_path`
are probes for the take/skip family, not separate production systems.

## Legacy Export Replay

This is a diagnostic check with old inputs and old rules. Its goal is to prove
that the saved prediction/rule/export path still runs and produces trade
signals. It does not prove that the model is valid for online trading.

| System | Export rows | Non-zero signals | BUY | SELL |
|---|---:|---:|---:|---:|
| `quality` | 8887 | 30 | 21 | 9 |
| `frequency` | 8887 | 78 | 50 | 28 |
| `original_plus_path` | 8887 | 37 | 24 | 13 |
| `entry_path_v1` | 8872 | 23 | 17 | 6 |
| `entry_path_v1_quantile` | 8872 | 18 | 13 | 5 |

All replay outputs are marked `diagnostic_only=true` in
`ML/reports/live_safe_ml_audit/legacy_export_summary.json`.

## Feature Findings

The three take/skip systems share the old row-feature family. Their input set
contains future-derived fields:

- `predict`
- `ret_6_dir_atr`, `ret_12_dir_atr`, `ret_24_dir_atr`
- `fav_3_atr`, `adv_3_atr`, `fav_6_atr`, `adv_6_atr`
- `fav_12_atr`, `adv_12_atr`, `fav_24_atr`, `adv_24_atr`

They also contain `ret_dir_atr_lag1`. Follow-up source audit closed this as
future-derived: `processing/label_signals.py:add_entry_path_frequency_features`
builds it as `ret_6_dir_atr.shift(1)`, while `label_entry_path_targets()` builds
`ret_6_dir_atr` from future bars after the signal row.

`entry_path_v1` does not include the take/skip forbidden row fields, but it does
include `ret_dir_atr_lag1`. Therefore the current checkpoint is not live-safe.

`entry_path_v1_quantile` depends on the `entry_path_v1` baseline score in the
production rule. Therefore it inherits the failed baseline risk.

## Verdicts

| System | Verdict | Reason | Allowed next step |
|---|---|---|---|
| `quality` | `FAIL` | future-derived model inputs | reject old checkpoint for online or retrain/rebuild |
| `frequency` | `FAIL` | future-derived model inputs | reject old checkpoint for online or retrain/rebuild |
| `original_plus_path` | `FAIL` | future-derived model inputs | reject old checkpoint for online or retrain/rebuild |
| `entry_path_v1` | `FAIL` | `ret_dir_atr_lag1` is derived from future `ret_6_dir_atr` | rebuild/retrain without that input |
| `entry_path_v1_quantile` | `FAIL` | production rule depends on failed `entry_path_v1` baseline score | rebuild baseline dependency first |

No audited system currently has `PASS`.

## Entry Path v1 Live-Safe Retrain

The first rebuild target was `entry_path_v1`, because it failed only on
`ret_dir_atr_lag1`, while the rest of its built-in feature profile could be
kept.

New profile: `entry_path_v1_live_safe`.

Feature change:

- old profile: `session_hour`, `weekday`, `range_atr_6`, `body_atr_3`,
  `ret_dir_atr_lag1`, `vol_regime_24`, row feature-bank columns;
- new profile: same columns, but without `ret_dir_atr_lag1`.

The old `entry_path_v1` profile is kept for legacy reproduction only.

### Single-Seed Result

Seed `42` retrain:

| Check | Trades | PF | Win rate | Notes |
|---|---:|---:|---:|---|
| validation winner `A @ 7.5%` | 36 | 2.8881 | 66.67% | selected on validation |
| frozen test | 37 | 3.6567 | 72.97% | same validation threshold |
| sequential test | 25 | 2.3419 | 68.00% | fixed 24-bar single-position check |

Signal export:

| File | Rows | Non-zero | BUY | SELL |
|---|---:|---:|---:|---:|
| `entry_path_v1_live_safe_test_signals.csv` | 8872 | 26 | 19 | 7 |

Comparison with old invalid `entry_path_v1`:

- old sequential: 30 trades, PF 2.87, win rate 66.67%;
- new live-safe sequential: 25 trades, PF 2.3419, win rate 68.00%.

Meaning: profitability did not survive unchanged. Trade count and PF are lower,
but the system did not collapse after removing the unsafe input.

### Multi-Seed Follow-Up

The retrain was repeated with seeds `7`, `17`, `42`, `77`, `123`.

`seed` means the starting number for controlled randomness. With the same seed,
training is repeatable. With different seeds, the model starts differently, so
the check shows whether a result is stable or just lucky.

| Seed | Val ret r | Winner | Test PF | Sequential trades | Sequential PF | Export supported |
|---:|---:|---|---:|---:|---:|---|
| 7 | 0.2792 | `B_no_path6` | 4.3044 | 32 | 2.7922 | yes |
| 17 | 0.2796 | `B` | 6.3893 | 25 | 4.5985 | yes |
| 42 | 0.2681 | `A` | 3.6567 | 25 | 2.3419 | yes |
| 77 | 0.2844 | `A` | 2.0024 | 32 | 1.5171 | yes |
| 123 | 0.2767 | `A` | 2.7762 | 33 | 1.8633 | yes |

Summary:

- median sequential PF: `2.3419`;
- min sequential PF: `1.5171`;
- max sequential PF: `4.5985`;
- PF > 2.0: `3 / 5` seeds;
- PF <= 1.0: `0 / 5` seeds;
- same winner: `A` in `3 / 5` seeds;
- MT4 signal export is now supported for `A`, `B`, and `B_no_path6` winners.
  `B` / `B_no_path6` use the frozen validation CSV referenced by the rule to
  reproduce the same score normalization.

Updated retrain verdict: the live-safe `entry_path_v1` idea is alive but not
fully stable. Removing `ret_dir_atr_lag1` did not destroy profitability, but the
result is weaker and more variable than the old invalid system. The previous
exporter limitation for `B` / `B_no_path6` is removed; the remaining issue is
rule-family stability, not signal export capability. MT4 parity is intentionally
deferred.

Rule-family decision: freeze `A` as the live-safe baseline rule family. Reason:
`A` is the simplest rule and repeats in `3 / 5` seeds. `B` and `B_no_path6`
remain valid research variants and are exportable, but they are not the primary
baseline for the next step.

### Follow-Up Audit: `A` Rule Family

After freezing `A`, two checks were separated:

1. **A-family robustness**: use `A` in every seed, but let each seed take its
   own validation-only `7.5%` threshold. This asks whether the idea "use
   `pred_ret_24_dir_atr` only" is stable.
2. **Exact frozen rule transfer**: apply the exact seed `42` threshold
   `-0.131882885` to every seed. This asks whether one numeric threshold
   transfers across independently trained checkpoints.

`A` family, per-seed validation threshold:

| Check | Result |
|---|---:|
| validation PF range | `2.2117 .. 2.8881` |
| frozen test PF range | `2.0024 .. 6.2050` |
| sequential PF range | `1.5171 .. 4.1370` |
| sequential median PF | `2.8425` |
| sequential trades range | `25 .. 32` |
| sequential PF > 2.0 | `4 / 5` seeds |
| sequential PF <= 1.0 | `0 / 5` seeds |
| median pairwise sequential signal overlap | `0.7759` |
| sequential signals selected by all 5 seeds | `21` |

Meaning: the `A` rule family is much more stable than the mixed winner table
suggested. Most accepted sequential signals repeat across seeds.

Exact seed `42` threshold applied to all seeds:

| Check | Result |
|---|---:|
| frozen test median PF | `1.3991` |
| sequential median PF | `0.9032` |
| sequential PF > 2.0 | `1 / 5` seeds |
| sequential PF <= 1.0 | `3 / 5` seeds |

Meaning: the `A` idea is robust, but the numeric score scale is not fully
calibrated across different checkpoints. The production candidate remains the
specific frozen seed `42` rule, not "reuse seed `42` threshold on any retrained
checkpoint". Before MT4 parity, treat calibration as a known ML risk.

Artifacts:

- `ML/reports/entry_path_v1_live_safe/audit_a/`

Artifacts:

- `ML/checkpoints/transformer_entry_path_v1_features_entry_path_v1_live_safe_best.pt`
- `ML/checkpoints/transformer_entry_path_v1_features_entry_path_v1_live_safe_result.json`
- `ML/reports/entry_path_v1_live_safe/`
- `ML/reports/entry_path_v1_live_safe/multi_seed_summary.csv`
- `ML/reports/entry_path_v1_live_safe/multi_seed_summary.json`
- `ML/reports/entry_path_v1_live_safe/seed_*/`

## Entry Path v1 Quantile Over Live-Safe Baseline

The next rebuild target was `entry_path_v1_quantile`.

Old quantile results were invalid for online approval because the production
quantile rule used the old `entry_path_v1` baseline score. This follow-up kept
the quantile model family, but replaced the baseline dependency with the new
`entry_path_v1_live_safe` baseline rule.

Baseline dependency:

- `ML/reports/entry_path_v1_live_safe/entry_path_trade_filter_selected_rule.json`
- baseline winner: `A`
- baseline threshold: `-0.131882885`

Five quantile retrains were run with seeds `7`, `17`, `42`, `77`, `123`.

| Seed | Val ret r | Validation winner | Frozen test trades | Frozen test PF | Sequential trades | Sequential PF |
|---:|---:|---|---:|---:|---:|---:|
| 7 | 0.2335 | `lb_gt_m_width_le_w` | 0 | 0.0000 | 0 | 0.0000 |
| 17 | 0.2570 | `lb_gt_m` | 28 | `inf` | 10 | `inf` |
| 42 | 0.1925 | `lb_gt_m` | 23 | 7.1133 | 13 | 3.0604 |
| 77 | 0.0935 | `baseline` | 58 | 5.3972 | 25 | 2.3419 |
| 123 | 0.2506 | `lb_gt_m` | 17 | `inf` | 8 | `inf` |

Summary:

- PF > 2.0 on sequential check: `4 / 5` seeds;
- PF <= 1.0 on sequential check: `1 / 5` seeds;
- sequential trade count range: `0..25`;
- one seed selected no frozen test trades;
- one seed fell back to the live-safe baseline rather than a quantile rule.

N-boost follow-up:

| Check | Candidate | Trades | PF | Win rate | Verdict |
|---|---|---:|---:|---:|---|
| frozen test | `lb_gt_m_q40` | 35 | 32.4125 | 88.57% | `gate_fail` |
| sequential | `lb_gt_m_q40` | 14 | 48.7214 | 92.86% | diagnostic |

The n-boost gate failed only on stability:
`same_winner_ratio=0.60 < 0.80`.

Updated quantile verdict after freezing baseline `A`: the quantile layer remains
promising, but it is not validated as a production candidate over the new
live-safe baseline. The profitability signal did not disappear, but the selected
rule is unstable, one seed produces no trades, one seed falls back to baseline,
and the sequential trade count is still low. Keep this track as research-only
until a rule repeats more reliably across seeds.

Artifacts:

- `ML/entry_path_v1_quantile_ensemble.py`
- `ML/reports/entry_path_v1_quantile_live_safe_baseline/`
- `ML/reports/entry_path_v1_quantile_live_safe_baseline/multi_seed_summary.csv`
- `ML/reports/entry_path_v1_quantile_live_safe_baseline/multi_seed_summary.json`
- `ML/reports/entry_path_v1_quantile_live_safe_baseline/n_boost/`

## Take/Skip v2 Live-Safe Baseline Probe

The next system family was the old take/skip group: `quality`, `frequency`,
and `original_plus_path`.

The first probe kept the old single-tensor runner shape, but added a new
feature mode: `live_safe_baseline`.

Feature change:

- old row inputs: `predict`, `ATR`, `session_hour`, `weekday`, `range_atr_6`,
  `body_atr_3`, `ret_dir_atr_lag1`, `vol_regime_24`, `ret_*`, `fav_*`,
  `adv_*`;
- new row inputs: `ATR`, `session_hour`, `weekday`, `range_atr_6`,
  `body_atr_3`, `vol_regime_24`.

Run:

- feature mode: `live_safe_baseline`;
- sequence length: `50`;
- seed: `42`;
- targets available in current labeled CSV: 9 (`x2/x4/x8`, horizons
  `12/24/48`);
- best epoch: `4`;
- validation BCE: `0.036112`.

Frozen benchmark result:

| Check | Result |
|---|---|
| validation winner | none |
| final verdict | `reject` |
| best observed validation PF | `1.5178` |
| best observed validation trades | `3` |
| best observed validation trades/year | `0.75` |
| best observed negative year slices | `1` |

Meaning: this was not a near miss. After removing future-derived row inputs,
the old take/skip baseline did not reproduce a tradable validation region under
the existing benchmark gate.

Artifacts:

- `ML/reports/take_skip_live_safe_baseline/live_safe_baseline_seq50/`

Follow-up source decision:

- `Up/Dn` values inside `fractal*` are treated as live-safe when they come from
  MT `Nero.csv` as accumulated `lib_PIC` state already known at the row time.
- Python-added future labels remain forbidden model inputs: `predict`,
  `ret_dir_atr_lag1`, `ret_*`, `fav_*`, `adv_*`.
- New runner modes were added for the next server-side probe:
  `live_safe_path`, `live_safe_geometry`, `live_safe_geometry_path`.
- The local full path/geometry probes were stopped before training because
  feature construction is too slow on this workstation. This is a compute
  placement issue, not a model/training change.

Confirmed Python future-derived inputs:

| Input family | Code source | Why it is not live-safe as model input |
|---|---|---|
| `predict` | `processing/label_signals.py:272-303` | For row `i`, Python walks rows strictly after `i` for the same `fractal0.time` and stores the maximum future `back` before break/drop. |
| `ret_*` | `processing/label_signals.py:930-951` | Uses future OHLC bars from `base_idx + 1` through the target horizon and stores the future return. |
| `fav_*`, `adv_*` | `processing/label_signals.py:930-954` | Uses future highs/lows inside the post-entry window and stores favorable/adverse future path movement. |
| `ret_dir_atr_lag1` | `processing/label_signals.py:863-869` | It is a one-row lag of `ret_6_dir_atr`; the source value is already a future outcome. |
| old take/skip row inputs | `ML/run_take_skip_original_contour_feature_matrix.py:56-75` | The old baseline included those Python future-derived fields directly as model inputs. |

Important distinction: MT-origin `Up/Dn` in `Nero.csv` and Python-added
`up_*/dn_*` labels are not the same source. The former can be known at the row
time as accumulated MT state; the latter must be audited separately if used.

Remote run:

- feature mode: `live_safe_path`;
- sequence length: `50`;
- seed: `42`;
- input features: `770`;
- engineered features: `750`;
- best epoch: `5`;
- validation BCE: `0.034260`;
- runtime on Ryzen 9 7950X3D server: `~369s`.

`live_safe_path` result:

| Check | Result |
|---|---|
| validation winner | none |
| final verdict | `reject` |
| best observed validation PF | `0.9893` |
| best observed validation trades | `15` |
| best observed validation trades/year | `3.75` |
| best candidate meeting 6 trades/year | `take_12_x2`, top_k `5%`, PF `0.6155` |

Meaning: adding MT-accumulated `Up/Dn` path-reaction features did not restore
the old take/skip profitability. This was worse than the direct
`live_safe_baseline` probe by validation PF.

Artifacts:

- `ML/reports/take_skip_live_safe_path/live_safe_path_seq50/`

Second remote run:

- feature mode: `live_safe_geometry`;
- sequence length: `50`;
- seed: `42`;
- input features: `642`;
- engineered features: `622`;
- best epoch: `7`;
- validation BCE: `0.033775`;
- runtime on Ryzen 9 7950X3D server: `~358s`.

`live_safe_geometry` result:

| Check | Result |
|---|---|
| validation winner | none |
| final verdict | `reject` |
| best observed validation PF | `0.5726` |
| best observed validation trades | `5` |
| best observed validation trades/year | `1.25` |
| best candidate meeting 6 trades/year | `take_48_x8`, top_k `5%`, PF `0.4125` |

Meaning: adding MT-accumulated geometry features also did not restore the old
take/skip profitability. This result is not a close miss: among candidates with
the required minimum trade frequency, validation losses were much larger than
profits.

Artifacts:

- `ML/reports/take_skip_live_safe_geometry/live_safe_geometry_seq50/`

## Conclusions

The old high-PF take/skip checkpoints are not valid online candidates as-is.
They can still guide a live-safe rebuild, but they must not be used as proof of
online ML quality. The first three take/skip rebuilds now support the stricter
interpretation: old take/skip profitability did not survive removal of
future-derived Python row inputs, even after adding MT-accumulated `Up/Dn`
path-reaction or geometry features.

The first live-safe rebuild of `entry_path_v1` has now been run. It is not a
production approval, but it is enough to reject the worst fear: removing
`ret_dir_atr_lag1` did not make the system unprofitable.

`entry_path_v1_quantile` was then rebuilt over that live-safe baseline. The
result is not a production approval either: some runs are very profitable, but
the selected quantile rule is not stable enough across seeds.

Next decision, before any MT4 work: treat the old take/skip row-feature family
as rejected for direct live-safe rebuild. Further work should only continue if
we define a materially different live-safe feature family or a narrower
hypothesis.

## Verification

Commands run:

```bash
./.venv/bin/python -m pytest tests/test_live_safe_audit.py -q
./.venv/bin/python -m ML.run_live_safe_ml_audit --phase all --output-dir ML/reports/live_safe_ml_audit
./.venv/bin/python -m pytest tests/test_entry_path_task.py tests/test_entry_path_training.py tests/test_entry_path_v1_quantile_reports.py tests/test_live_safe_audit.py -q
./.venv/bin/python -m ML.benchmark_entry_path_v1_quantile_n_boost --root-dir ML/reports/entry_path_v1_quantile_live_safe_baseline --seeds 7 17 42 77 123 --baseline-rule ML/reports/entry_path_v1_live_safe/entry_path_trade_filter_selected_rule.json --output-dir ML/reports/entry_path_v1_quantile_live_safe_baseline/n_boost
./.venv/bin/python -m pytest tests/test_take_skip_original_contour_feature_matrix.py -q
./.venv/bin/python -m ML.run_take_skip_original_contour_feature_matrix --output-dir ML/reports/take_skip_live_safe_baseline --feature-modes live_safe_baseline --seq-lens 50 --epochs 10 --patience 4 --batch-size 256 --seed 42 --min-pf 1.0 --min-trades-per-year 6.0 --jobs 1 --torch-threads 4
./.venv/bin/python -m ML.run_take_skip_original_contour_feature_matrix --output-dir ML/reports/take_skip_live_safe_path --feature-modes live_safe_path --seq-lens 50 --epochs 10 --patience 4 --batch-size 256 --seed 42 --min-pf 1.0 --min-trades-per-year 6.0 --jobs 1 --torch-threads 16
./.venv/bin/python -m ML.run_take_skip_original_contour_feature_matrix --output-dir ML/reports/take_skip_live_safe_geometry --feature-modes live_safe_geometry --seq-lens 50 --epochs 10 --patience 4 --batch-size 256 --seed 42 --min-pf 1.0 --min-trades-per-year 6.0 --jobs 1 --torch-threads 16
```

Results:

- `12 passed`
- `34 passed`
- audit files generated for all five systems
- legacy export replay generated for all five systems
- live-safe `entry_path_v1` retrain and multi-seed artifacts generated
- live-safe-baseline `entry_path_v1_quantile` retrain, multi-seed artifacts,
  and n-boost gate generated
- take/skip `live_safe_baseline_seq50` probe generated; verdict `reject`
- take/skip `live_safe_path_seq50` generated on remote server; verdict `reject`
- take/skip `live_safe_geometry_seq50` generated on remote server; verdict
  `reject`
