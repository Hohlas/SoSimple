# Fixed-11 Metric-Based Mutual-Correlation Pruning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce the 11 already passed fixed rules to a smaller working subset by measured mutual overlap, keeping the strongest working representative inside each duplicate group by trading metrics.

**Architecture:** Add and maintain one focused pruning runner under `ML/baseline/`. The runner reads already saved fixed-11 CSV/JSON artifacts, validates the contract, computes pairwise overlap/correlation, groups strong duplicates, and writes a retained-subset manifest plus report inputs. It must not train models, search new rules, change cutoffs, change execution settings, or open a new test period.

**Tech Stack:** Python 3, `pandas`, `numpy`, existing project CSV artifacts with `sep=";"`, `pytest`, `wiki/wiki.py`.

## Global Constraints

- Work on the current feature branch.
- Use `./.venv/bin/python`.
- After Python changes, run `./.venv/bin/python -m pytest tests/ -q`.
- Read CSV files with explicit `sep=";"`.
- Do not change `rule_id`, cutoffs, profile/model/target/filter, entry/exit/stop, spread, fill policy, or PnL convention.
- Do not run a new search.
- Do not create new candidate rules.
- Use only the 11 rules that already have `candidate_audit_passed`.
- Use `locked_test` trades to measure whether rules duplicate each other.
- Use saved `locked_test` trading metrics only to choose one representative inside an already identified strong-duplicate group.
- Representative metric: `BS_p05 / max_drawdown_r`.
- Tie-breakers, in order: higher `pf_without_best_year`, higher `effective_profit_years`, lower `max_drawdown_r`, higher `n_trades`, higher PF, higher net PnL, stable `rule_id`.
- Do not use `original_rank` as a representative-selection policy.
- `original_rank` may remain only as an input/traceability field because existing CSV artifacts contain it.
- The report must clearly disclose that `locked_test` metrics were used for representative choice inside duplicate groups.
- The retained subset is a working set for follow-up parity/stress/model-card work, not proof of production readiness.

## Methodology Scope

Read first:

- `docs/methodology/README.md`

Applicable sections:

- `docs/methodology/00-research-management.md`: fixes hypothesis, allowed verdict, search budget, forbidden changes.
- `docs/methodology/06-temporal-split.md`: confirms `locked_test` role and sample-size disclosure.
- `docs/methodology/09-validation-freeze.md`: protects frozen rules and prevents unreported winner reselection.
- `docs/methodology/10-frozen-test-oos.md`: keeps `locked_test` as one-shot evaluation and requires disclosure if it affects selection.
- `docs/methodology/11-robustness.md`: covers correlation, overlap, drawdown overlap, time slices, side slices, and temporal bootstrap limits.
- `docs/methodology/12-backtest-costs.md`: keeps execution/cost convention unchanged.
- `docs/methodology/16-reporting-audit.md`: defines report, structured artifacts, limitations, and handoff.
- `docs/methodology/A2-checklist-audit.md`: final audit checklist before raising candidate status.

Methodology note:

- There is no dedicated methodology file for pruning already opened fixed-rule `locked_test` results.
- This plan therefore defines the local policy explicitly before the report is interpreted: first identify duplicate groups by overlap/correlation evidence, then choose one working representative by `BS_p05 / max_drawdown_r`.
- Because `locked_test` metrics are used for representative choice, the result must stay at `candidate_not_trading_ready` and must be disclosed in follow-up materials.

## Stage Registration

```text
lifecycle_status: post_locked_test_read_only_pruning
stage_level: audit/disclosure, without raising above candidate
hypothesis: some of the 11 already-passed fixed rules may be effectively duplicate signals
task_type: portfolio/correlation audit of frozen rules
decision_unit: fixed rule and trade event
decision_time: inherited from fixed-11 locked-test execution contract
current_search_budget: 0_new_rules
cumulative_search_budget: inherited_from_fixed11_candidate_audit
origin_bias: follow_up_required_from_fixed11_candidate_audit
allowed_max_verdict: candidate_not_trading_ready
allowed_max_verdict_note: working subset selected from already-passed candidates for operational follow-up
next_probe_freeze: retained subset only; same rules/cutoffs/execution contract; no new rules
forbidden_interpretations: retained subset is not trading-ready; pruning does not prove improved profitability; dropped duplicate rules are not bad rules
locked_test_policy: overlap_measurement_and_metric_representative_selection_within_passed_duplicates
representative_policy: best_bs_p05_per_drawdown_then_robustness_metrics
representative_metric: BS_p05 / max_drawdown_r
locked_test_performance_used_for_representative_choice: true
```

---

### Task 1: Validate Inputs And Normalize Trades

**Files:**
- Create/modify: `ML/baseline/prune_fractal0_fixed11_mutual_correlation.py`
- Create/modify: `tests/test_fractal0_fixed11_mutual_correlation_pruning.py`

**Interfaces:**
- Consumes: `ML/reports/fractal0_fixed11_candidate_audit.json`
- Consumes: `ML/reports/fractal0_fixed11_rich_entry_locked_test_summary.csv`
- Consumes: `ML/reports/fractal0_fixed11_rich_entry_locked_test_selection.csv`
- Consumes: `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`
- Produces: `load_inputs(input_prefix: Path, audit_json: Path) -> Fixed11Inputs`
- Produces: `normalize_fixed11_trades(trades: pd.DataFrame) -> pd.DataFrame`

Mandatory checks:

- Prior audit JSON has `overall_decision=candidate_audit_passed`.
- Selection CSV has exactly 11 unique `rule_id`.
- All 11 rows have `decision=KEEP_CANDIDATE`.
- Summary, selection, and trades have the same 11 `rule_id`.
- `summary.n_trades` equals actual trade counts from trades CSV.
- Every rule has at least 100 locked-test trades.
- Trades CSV has required columns and no missing `rule_id`, `signal_time`, `fill_time`, `exit_time`, `side`, or `pnl_r`.
- `side` maps only to BUY/SELL directions.
- `original_rank` is unique per rule and consistent across input artifacts, but is not used for representative selection.

- [x] **Step 1: Add tests for input contract failures and deterministic normalization**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_mutual_correlation_pruning.py -q
```

Expected after implementation: all tests in this file pass.

- [x] **Step 2: Implement fail-closed input loading and normalization**

Implementation lives in:

```text
ML/baseline/prune_fractal0_fixed11_mutual_correlation.py
```

Completion criterion:

- Invalid fixed-11 artifacts fail before pruning.
- Normalized trades are deterministic and preserve the original trading contract.

---

### Task 2: Compute Pairwise Overlap And Correlation

**Files:**
- Modify: `ML/baseline/prune_fractal0_fixed11_mutual_correlation.py`
- Modify: `tests/test_fractal0_fixed11_mutual_correlation_pruning.py`

**Interfaces:**
- Consumes: normalized trades from Task 1.
- Produces: `compute_pair_metrics(left: pd.DataFrame, right: pd.DataFrame) -> dict[str, Any]`
- Produces: `build_pairwise_matrix(trades: pd.DataFrame) -> pd.DataFrame`

Required metrics:

- fill overlap ratio;
- signal overlap ratio;
- fill Jaccard;
- signal Jaccard;
- same-direction ratio;
- fill-bucket PnL correlation;
- daily and weekly PnL correlation by fill time;
- daily and weekly PnL correlation by exit time;
- drawdown-overlap ratio;
- co-loss ratio;
- staggered-gain ratio.

Verdict thresholds:

- `strong_duplicate` if fill overlap >= 0.75, signal overlap >= 0.75, same direction >= 0.95, and fill-bucket PnL correlation >= 0.95.
- `partial_overlap` if any relevant overlap/correlation warning threshold is crossed but the pair is not a strong duplicate.
- `unclear_or_complementary` otherwise.

- [x] **Step 1: Add focused tests for metric calculations and verdict thresholds**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_mutual_correlation_pruning.py -q
```

Expected after implementation: all pairwise tests pass.

- [x] **Step 2: Implement pairwise metric calculation and matrix export**

Completion criterion:

- All 55 pairs across the 11 rules are represented exactly once.
- Matrix artifacts are deterministic.

---

### Task 3: Select Metric-Based Representatives

**Files:**
- Modify: `ML/baseline/prune_fractal0_fixed11_mutual_correlation.py`
- Modify: `tests/test_fractal0_fixed11_mutual_correlation_pruning.py`

**Interfaces:**
- Consumes: pairwise matrix from Task 2.
- Consumes summary metrics from `ML/reports/fractal0_fixed11_rich_entry_locked_test_summary.csv`.
- Produces: `build_duplicate_clusters(pairwise: pd.DataFrame, rule_order: pd.DataFrame) -> pd.DataFrame`
- Produces: `build_retained_subset(inputs: Fixed11Inputs, pairwise: pd.DataFrame) -> dict[str, Any]`

Representative policy:

1. Build groups only from direct `strong_duplicate` edges.
2. Retain one representative per duplicate group.
3. Choose representative by highest `BS_p05 / max_drawdown_r`.
4. If tied, use: higher `pf_without_best_year`, higher `effective_profit_years`, lower `max_drawdown_r`, higher `n_trades`, higher PF, higher net PnL, stable `rule_id`.
5. Drop a rule only when it has a direct `strong_duplicate` edge to its retained representative.
6. Record partial overlaps and non-representative strong duplicate edges as warnings/disclosure.

- [x] **Step 1: Add regression test proving representative choice is metric-based**

The test must cover a case where the lower-ranked rule has the better `BS_p05 / max_drawdown_r` and is retained.

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_mutual_correlation_pruning.py -q
```

Expected after implementation:

```text
12 passed
```

- [x] **Step 2: Implement metric sorting and representative metadata**

Completion criterion:

- `representative_policy=best_bs_p05_per_drawdown_then_robustness_metrics`.
- `locked_test_performance_used_for_representative_choice=true`.
- Retained manifest includes `representative_score`, `BS_p05`, PF, robust PF, drawdown, trade count, and net PnL for each rule.

---

### Task 4: Run Pruning And Write Artifacts

**Files:**
- Modify/create: `ML/reports/fractal0_fixed11_mutual_correlation_pruning_pairwise.csv`
- Modify/create: `ML/reports/fractal0_fixed11_mutual_correlation_pruning_clusters.csv`
- Modify/create: `ML/reports/fractal0_fixed11_mutual_correlation_pruning_fill_daily_pnl_matrix.csv`
- Modify/create: `ML/reports/fractal0_fixed11_mutual_correlation_pruning_fill_weekly_pnl_matrix.csv`
- Modify/create: `ML/reports/fractal0_fixed11_mutual_correlation_pruning_exit_daily_pnl_matrix.csv`
- Modify/create: `ML/reports/fractal0_fixed11_mutual_correlation_pruning_exit_weekly_pnl_matrix.csv`
- Modify/create: `ML/reports/fractal0_fixed11_mutual_correlation_pruning_exit_drawdown_overlap_matrix.csv`
- Modify/create: `ML/reports/fractal0_fixed11_mutual_correlation_pruning_retained_subset.json`
- Modify/create: `ML/reports/fractal0_fixed11_mutual_correlation_pruning_summary.json`

- [x] **Step 1: Run pruning on saved fixed-11 artifacts**

Run:

```bash
./.venv/bin/python ML/baseline/prune_fractal0_fixed11_mutual_correlation.py \
  --input-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test \
  --audit-json ML/reports/fractal0_fixed11_candidate_audit.json \
  --output-prefix ML/reports/fractal0_fixed11_mutual_correlation_pruning
```

Expected summary:

```text
overall_decision=pruning_passed
input_rule_count=11
retained_count=5
removed_count=6
pair_count=55
strong_duplicate_edge_count=13
partial_overlap_count=42
unclear_or_complementary_count=0
```

- [x] **Step 2: Confirm retained subset**

Expected retained rules:

```text
rank10_movement_plus_time_linear_target_entry_ev_regression_top50
rank05_time_only_linear_target_entry_avoid_sl_top30
rank02_time_only_linear_target_entry_ev_regression_top40
rank11_movement_plus_time_linear_target_entry_good_0_5r_top50
rank09_time_only_hist_gradient_boosting_target_entry_good_0_5r_top50
```

Expected dropped rules:

```text
rank08_movement_plus_time_linear_target_entry_good_0_5r_top30 -> rank10_movement_plus_time_linear_target_entry_ev_regression_top50
rank03_time_only_linear_target_entry_ev_regression_top50 -> rank02_time_only_linear_target_entry_ev_regression_top40
rank06_time_only_linear_target_entry_good_0_5r_top50 -> rank02_time_only_linear_target_entry_ev_regression_top40
rank01_time_only_linear_target_entry_ev_regression_top30 -> rank02_time_only_linear_target_entry_ev_regression_top40
rank04_time_only_linear_target_entry_good_0_5r_top40 -> rank02_time_only_linear_target_entry_ev_regression_top40
rank07_movement_plus_time_linear_target_entry_good_0_5r_top40 -> rank11_movement_plus_time_linear_target_entry_good_0_5r_top50
```

---

### Task 5: Update Existing Report And Project Context

**Files:**
- Modify: `docs/reports/2026-07-27-fractal0-fixed11-mutual-correlation-pruning.md`
- Modify: `docs/ML/prune_fractal0_fixed11_mutual_correlation.py.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Generated/modify: `wiki/REPO_integrity.md`

Report requirements:

- Do not create a new report.
- Update the existing report to match the metric-based representative policy.
- Remove claims that representatives are chosen by `original_rank`.
- Clearly state that `locked_test` metrics are used only inside already-passed strong-duplicate groups.
- Keep the verdict capped at `candidate_not_trading_ready`.
- State that dropped duplicate rules are not bad rules.
- State that pruning does not prove improved profitability.

- [x] **Step 1: Update documentation and wiki context**

Run:

```bash
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

Expected:

```text
Wiki is up to date. No gaps found.
```

---

### Task 6: Final Verification

**Files:**
- Verify all files from Tasks 1-5.

- [x] **Step 1: Run target tests**

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_mutual_correlation_pruning.py -q
```

Expected:

```text
12 passed
```

- [x] **Step 2: Run full project tests**

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected:

```text
1480 passed, 52 warnings
```

- [x] **Step 3: Commit related files only**

Do not include unrelated local files unless explicitly requested.

Expected committed change:

```text
Use metric-based fixed11 pruning representatives
```

Completion criterion:

- Code, tests, generated pruning artifacts, existing report, handoff, changelog, and wiki agree on the same metric-based pruning policy.
- The old `original_rank` representative policy is not used.
