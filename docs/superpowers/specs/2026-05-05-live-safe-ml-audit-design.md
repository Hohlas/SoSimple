# Live-Safe ML Audit — Design Spec

> **Date**: 2026-05-05
> **Status**: Approved design
> **Track**: ML result validation before online trading
> **Goal**: Re-audit all profitable ML trading systems, separate mechanically reproduced historical results from live-safe results, and decide which systems can proceed to online testing.

---

## 1. Context

The project has several historical ML trading systems with strong reported
profitability. The strongest visible results are concentrated in five mature
systems:

- `quality`
- `frequency`
- `original_plus_path`
- `entry_path_v1`
- `entry_path_v1_quantile`

Recent online work showed that the old `original_baseline` online contract is
not safe: it used row-wise inputs derived from future bars, including
`predict`, `ret_*`, `fav_*`, and `adv_*`. The current leakage checklist also
marks `ret_dir_atr_lag1` as forbidden until proven safe.

Normative gate for this audit:
[`docs/ML/ml_leakage_preflight_checklist.md`](../../ML/ml_leakage_preflight_checklist.md).
Every ML quality claim in this plan must pass that checklist. If a check is
`FAIL` or `UNKNOWN`, the result can only be marked `DIAGNOSTIC_ONLY` until the
cause is resolved.

Feature names are not enough for a verdict. The audit must trace where each
field is calculated in code and when its value becomes known. A field is
live-safe only if the source code proves it is available at the decision time.

Therefore high PF alone is not enough. Each system must be re-audited from
source artifacts and feature contracts before its result can be trusted for
online trading.

---

## 2. Main Decision

Run a repeatable audit for every mature profitable system, not just the most
promising one.

Each system gets two separate checks:

1. **Legacy reproduction**: reproduce the old result with the original
   checkpoint, rule, predictions, export, and MT4/test evidence.
2. **Live-safe audit**: publish and classify all model inputs, then determine
   whether the old checkpoint can be trusted, must be rejected, or requires a
   live-safe rebuild/retrain.

If a checkpoint was trained with future-derived input columns, it must not be
tested online as an ML-valid system. It can only be used for mechanical
diagnostics, or it must be retrained with a live-safe input set.

---

## 3. Scope

### In Scope

- Audit the five mature systems:
  - `quality`
  - `frequency`
  - `original_plus_path`
  - `entry_path_v1`
  - `entry_path_v1_quantile`
- Reproduce old reported results from existing artifacts where possible.
- Publish full feature lists before any live-safe re-test.
- Classify features as:
  - live-safe
  - future-derived
  - unknown
- Produce a verdict for each system.
- Recommend which systems proceed to live-safe rebuild/retrain.
- Define the path from offline validation to MT4 tester parity and online dry-run.

### Out of Scope

- New model research.
- New trading modes.
- New portfolio allocation logic.
- Risk sizing or money management.
- Online trading before the audit and dry-run gates pass.
- Reviving rejected systems such as Triple Barrier unless a separate task asks
  for it.

---

## 4. Audit Principles

### 4.1. Reproduce Before Judging

For each system, first prove that the old result is reproducible or that the
needed artifacts are missing.

Required reproduction evidence:

- checkpoint path
- rule JSON path
- prediction CSV path
- exported `ml_signals.csv` path, if present
- validation/test metrics
- MT4 tester or parity evidence, if present
- command or script used to regenerate the result

If the old result cannot be reproduced, mark the system `UNKNOWN` and stop
before live-safe claims.

### 4.2. Publish Feature Contract Before Retest

Before any retest, write a table with:

- feature name
- raw field index or raw source field, if applicable
- source file/function
- source group: fractal, row-wise, model prediction, label, execution metric
- producer code path: where the value is calculated or exported
- consumer code path: where the model reads the value
- transformation path: parsing, sorting, normalization, aggregation, lagging
- role: model input, target, label, filter input, normalization-only field
- availability time: current bar, past-only history, future bars, unknown
- live-safe status
- evidence: code path and report/doc path used for the classification
- notes

The feature list must be reviewed before running live-safe training or online
tests.

Use `docs/reports/2026-04-19-lib-pic-feature-source-audit.md` as the pattern
for this table. That report maps each `Nero.csv` fractal field to its MQL4
source, for example CSV index, field name, `F[f]` source, and current meaning.
The same idea must be applied to every audited ML system, including fields that
are created later in Python.

The practical question for every field is:

- where is this number created?
- from which earlier numbers is it created?
- at which bar time is it first known?
- is it used directly by the model, or only to build a target/report?

### 4.3. No Zero-Fill Compatibility

If the old checkpoint expects a feature that live runtime cannot honestly
create, do not fill it with `0` and call the result valid.

Allowed outcomes:

- reject the checkpoint for online use;
- retrain the same idea with a live-safe feature set;
- keep it only as `DIAGNOSTIC_ONLY` for file-chain testing.

### 4.4. Validation-First

All thresholds, top-k values, rules, exits, and filters must be selected on
validation. Test is only a final frozen check.

If a rule was changed after looking at test, the result is not a valid final
test result.

### 4.5. Classify by Source and Timing, Not by Name Alone

Do not mechanically ban or approve a field only by its name.

Examples:

- `ret_*`, `fav_*`, and `adv_*` are usually future outcome fields in the
  current labeling code, so they are unsafe as inputs unless code proves a
  different meaning.
- `Up/Dn` fields inside exported fractal strings may be accumulated historical
  state for an older fractal, or they may act like a future outcome for the
  current decision. The verdict depends on the producer code and decision time.
- `ret_dir_atr_lag1` is not automatically safe just because it is lagged. The
  audit must check whether the pre-lag source already contains future bars
  relative to the current decision.

For each doubtful field, inspect the calculation site in code before assigning
the verdict.

---

## 5. Candidate Systems

### 5.1. `quality`

Current known result:

- test PF around `39.74`
- MT4 results were strong under trailing execution

Known risk:

- uses the `original_baseline` checkpoint family;
- this family includes future-derived row inputs.

Expected initial verdict:

- likely `FAIL` for old checkpoint as live-safe ML;
- still useful as a reference for a live-safe rebuild.

### 5.2. `frequency`

Current known result:

- test PF around `13.12` for the anchored frequent rule;
- MT4 frequent candidate exists.

Known risk:

- shares the same `original_baseline` checkpoint family as `quality`.

Expected initial verdict:

- likely `FAIL` for old checkpoint as live-safe ML;
- candidate for retrain if the live-safe version keeps useful frequency.

### 5.3. `original_plus_path`

Current known result:

- test PF around `38.78`;
- MT4 PF around `23.79`.

Known risk:

- explicitly covered by the 2026-04-29 unsafe contract finding.

Expected initial verdict:

- likely `FAIL` for old checkpoint;
- useful as a controlled comparison because it added path features on top of
  the old unsafe baseline.

### 5.4. `entry_path_v1`

Current known result:

- selected baseline rule `A @ 7.5%`;
- test PF around `4.29`.

Known risk:

- current feature contract includes `ret_dir_atr_lag1`, which the leakage
  checklist marks as forbidden until proven safe.

Expected initial verdict:

- `UNKNOWN` until `ret_dir_atr_lag1` is audited from source code and data.

### 5.5. `entry_path_v1_quantile`

Current known result:

- n-boost gate PF around `8.18`;
- MT4 parity showed matching trade events;
- MT4 tester PF around `11.91`.

Known risk:

- the quantile checkpoint itself appears cleaner, but the production rule
  depends on baseline `entry_path_v1` score.

Expected initial verdict:

- best first candidate for live-safe audit;
- cannot be marked `PASS` until the baseline dependency is audited.

---

## 6. Verdict Model

Each system receives one of four verdicts.

| Verdict | Meaning | Allowed next step |
|---|---|---|
| `PASS` | Inputs are live-safe, split/rules are valid, and MT4/export parity is understood | Online dry-run |
| `FAIL` | Future-derived or otherwise invalid inputs affect the result | Retrain/rebuild or reject |
| `UNKNOWN` | Evidence is incomplete or feature timing is unclear | Gather evidence before testing |
| `DIAGNOSTIC_ONLY` | Useful for testing MT4/Python/CSV mechanics, not ML quality | Mechanical dry-run only |

`UNKNOWN` must be treated as `FAIL` for online trading until resolved.

---

## 7. Audit Flow

### Phase A: Artifact Inventory

For each system, collect:

- checkpoint
- rule JSON
- validation/test predictions
- export script
- signal CSV
- MT4 log/tester output
- report paths
- selected thresholds and exits

Output:

- one manifest per system;
- one combined audit index.

### Phase B: Legacy Reproduction

Try to regenerate the old predictions and selected signal export.

Output:

- reproduced metrics;
- diff against historical report;
- reason if reproduction is not possible.

### Phase C: Feature Contract Audit

Build a feature table for each system.

Mandatory checks:

- exact model input count
- exact feature names where available
- raw source field or raw CSV index where applicable
- calculation site for every row-wise field
- row-wise feature list
- fractal feature parser contract
- target/label columns
- normalization path
- scaler behavior, if any
- train/validation/test split order
- proof that source and decision time were inspected for doubtful fields

Output:

- published feature tables;
- source trace table for fields with non-obvious timing;
- per-feature live-safe classification;
- system verdict draft.

### Phase D: Live-Safe Rebuild Decision

For each `FAIL` or `UNKNOWN` system, decide:

- reject as historical-only;
- rebuild with live-safe features;
- retrain with live-safe features;
- keep only for diagnostics.

No model should proceed to online test from this phase unless it is `PASS`.

### Phase E: Live-Safe Validation/Test

For each rebuilt/retrained system:

- train or run only with approved features;
- select rules on validation;
- freeze rule before test;
- run test once as final check;
- compare with old result without pretending they are the same checkpoint.

Output:

- validation/test report;
- explicit old-vs-live-safe comparison.

### Phase F: MT4 Tester Parity

For systems that pass Phase E:

- export `ml_signals.csv`;
- run MT4 tester or consume existing tester evidence;
- run signal/export parity;
- explain any mismatch by period boundaries, duplicate timestamps, spread,
  ATR differences, or execution timing.

### Phase G: Forward Validation

Before online dry-run, run a frozen rule on data that is strictly newer than the
data used to select that rule.

Purpose:

- prove that the selected rule still works after the research decision;
- avoid treating an old test slice as fresh forward evidence;
- decide whether the system is strong enough to justify an online dry-run.

Output:

- forward prediction/export evidence;
- forward metrics;
- explicit pass/fail reason.

### Phase H: Online Dry-Run

Before trading:

- run watcher/exporter in foreground or managed mode;
- do not open real risk until dry-run is understood;
- log `WAIT`, `NO_SIGNAL`, `ZERO_SIGNAL`, `BUY`, `SELL`, `CLOSE`;
- verify latest `time` in `ml_signals.csv` reaches MT4 bar time;
- compare online preprocessing with offline builder.

Only after this dry-run can a real online trading test be proposed.

---

## 8. Output Artifacts

The audit should produce:

- `ML/reports/live_safe_ml_audit/manifest.json`
- `ML/reports/live_safe_ml_audit/<system>/artifact_inventory.json`
- `ML/reports/live_safe_ml_audit/<system>/feature_contract.csv`
- `ML/reports/live_safe_ml_audit/<system>/source_trace.csv`
- `ML/reports/live_safe_ml_audit/<system>/legacy_reproduction.json`
- `ML/reports/live_safe_ml_audit/<system>/forward_validation.json`, if applicable
- `ML/reports/live_safe_ml_audit/<system>/verdict.json`
- `docs/reports/YYYY-MM-DD-live-safe-ml-audit.md`

If retraining is performed later, each retrain should get its own subdirectory
and separate report, not overwrite the original audit evidence.

---

## 9. Recommended Order

1. `entry_path_v1_quantile`
2. `entry_path_v1`
3. `quality`
4. `frequency`
5. `original_plus_path`

Reason:

- `entry_path_v1_quantile` is the most promising production candidate but
  depends on `entry_path_v1`.
- `entry_path_v1` must be resolved to judge that dependency.
- `quality` and `frequency` are portfolio-relevant, but likely share the same
  unsafe base checkpoint.
- `original_plus_path` is likely unsafe but should be formally closed because
  it had very strong historical and MT4 numbers.

---

## 10. Success Criteria

The audit succeeds when:

- every mature profitable system has a written verdict;
- every verdict links to concrete evidence;
- no future-derived checkpoint is accidentally promoted to online trading;
- at least one system is selected for either live-safe online dry-run or
  live-safe retrain;
- the user can see old result vs live-safe result without ambiguity.

---

## 11. Non-Negotiable Rules

- Do not call a system production-ready only because PF is high.
- Do not fill missing live features with zero and call it compatible.
- Do not choose thresholds on test.
- Do not approve or reject doubtful fields by name alone; inspect their source
  code and decision-time availability.
- Do not run online trading before feature contract, test, and MT4 parity are
  clear.
- Treat `UNKNOWN` as unsafe until proven otherwise.
