# CONTEXT HANDOFF

## Current Completed Stage

- report: `docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md`
- script: `ML/baseline/audit_fractal0_fixed11_candidate.py`
- source artifacts: `ML/reports/fractal0_fixed11_rich_entry_locked_test*`
- audit artifacts: `ML/reports/fractal0_fixed11_candidate_audit.json`, `ML/reports/fractal0_fixed11_candidate_audit_findings.csv`

## Decision

Independent audit of the fixed-11 locked-test bundle is complete.

- Verdict: `candidate_audit_blocked`
- evaluated rules: 11
- gate_pass_count in source bundle: 11
- findings: `15 ERROR`, `2 WARNING`

## Key Result

The locked-test metrics themselves remain intact, but the audit blocked any status promotion because the surrounding proof/disclosure contract is incomplete.

- missing `fractal0_fixed11_locked_test_freeze.json` and selection-policy artifact
- source JSON does not disclose `val_select` / `val_eval` roles or split boundaries
- 6 yearly edge slices (`2022`) have `n_trades < 30` without `DIAGNOSTIC_ONLY` classification
- 4 `movement_plus_time` rules lack structured `movement_score_restoration` disclosure
- `correlation_pruning_status` is missing from the source bundle

## Implementation Notes

- Audit runner hash recorded in artifact:
  `793f18b49e06f815f8144ac6ec1fb9eff1acb67d264a002874b00039e2f0911f`
- Computed split boundaries:
  - `train_core`: `2004-07-06 20:00:00` -> `2019-06-20 14:00:00`, `44159` rows
  - `val_select`: `2019-06-20 16:00:00` -> `2021-03-08 03:00:00`, `4731` rows
  - `val_eval`: `2021-03-08 05:00:00` -> `2022-12-02 07:00:00`, `4732` rows
  - `locked_test`: `2022-12-02 11:00:00` -> `2026-06-04 12:00:00`, `9463` rows

## Next Step

Do not proceed to correlation pruning, MT4/tester parity or model card yet.

The next allowed work is a narrow blocker-resolution step without changing frozen rules:

1. recover or explicitly disclose missing pre-open freeze / selection-policy evidence;
2. add structured split disclosure for `val_select` and `val_eval`;
3. add structured `movement_score_restoration` disclosure for the 4 `movement_plus_time` rules;
4. classify low-N yearly edge slices as `DIAGNOSTIC_ONLY`;
5. rerun the candidate audit only after those disclosures are in place.
