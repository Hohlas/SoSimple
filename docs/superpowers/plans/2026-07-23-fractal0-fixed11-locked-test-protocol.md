# Fractal0 Fixed-11 Locked Test Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Open `locked_test` exactly once for the 11 frozen Fractal0 fixed-rule systems, then decide reject / keep 1-3 portfolio candidates by predefined gates without changing rules after seeing the result.

**Architecture:** Add a dedicated locked-test runner that reuses the frozen 11-rule contract, saved validation cutoffs and existing rich-entry/exit simulation code. The runner must produce machine-readable artifacts first, then a report that explicitly states that `locked_test` was used as a predefined 11-system portfolio selection test, not as confirmation of one preselected winner.

**Tech Stack:** Python, pandas, existing `ML/baseline/benchmark_fractal0_entry_quality_filter.py`, existing `ML/baseline/benchmark_fractal0_entry_exit_grid.py`, pytest, project CSV separator `;`.

## Global Constraints

- Work on the current feature branch; do not use a separate worktree.
- Use `./.venv/bin/python` for all Python commands.
- Execute tasks strictly in order.
- Do not change the 11 frozen systems' entry, stop, mask, exit, model profile, target, filter, saved cutoff, canonical spread or fill/PnL convention after `locked_test` is opened.
- `locked_test` is opened once for the fixed set of 11 systems; no rerun after metric-driven edits.
- `locked_test` may be used to choose up to 3 portfolio candidates only by the predefined gates in this plan.
- Use `DATA/Nero_XAUUSD_test_labeled.csv` as the locked-test split unless preflight proves it was previously used for selection.
- Use `DATA/XAUUSD_H1_OHLC.csv` as canonical H1 OHLC for this runner; it is byte-identical to `MT/MQL4/Files/XAUUSD_H1_OHLC.csv` in the current workspace.
- Use `MT/MQL4/Files/XAUUSD_M5_OHLC.csv` only for execution-order diagnostic artifacts; M5 must not be used as a feature source or to change candidate ranking after seeing locked-test results.
- If the locked-test file was already used for model/rule/threshold selection, stop with `UNKNOWN_LOCKED_TEST_CONTRACT` and do not run the test.
- Provider drift, transfer and MT4 parity are not prerequisites for this locked-test decision; they become follow-up checks only for kept candidates.
- Maximum verdict after this stage is `candidate`, never `production` or `live_ready`.

## Methodology Map

Applicable methodology sections:

- `docs/methodology/06-temporal-split.md`: locked-test identity, date/index boundaries, sample-size gate, no temporal shuffle.
- `docs/methodology/09-validation-freeze.md`: frozen rule contract, saved thresholds, no changes after seeing locked-test results.
- `docs/methodology/10-frozen-test-oos.md`: one locked-test run, model/trading metrics, time slices, BUY/SELL slices, predefined gates.
- `docs/methodology/11-robustness.md`: correlation/portfolio diagnostics and weak-regime disclosure.
- `docs/methodology/12-backtest-costs.md`: canonical spread, gross/net disclosure, stress-cost interpretation.
- `docs/methodology/13-export-mt4-parity.md`: follow-up parity scope for kept candidates, not a proof of profitability.
- `docs/methodology/16-reporting-audit.md`: reproducible report, current/cumulative search budget, hashes, limitations, model-card requirement for kept candidates.

No additional methodology section is required. Demo-account verification belongs after MT4 parity/forward-test and is outside this plan.

## Preflight Facts And Remaining Unknowns

- Confirmed local locked-test candidate path: `DATA/Nero_XAUUSD_test_labeled.csv`.
- Confirmed local OHLC inputs: `DATA/XAUUSD_H1_OHLC.csv`, `MT/MQL4/Files/XAUUSD_H1_OHLC.csv`, `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`.
- Fact checked local boundaries: `DATA/Nero_XAUUSD_test_labeled.csv` covers `2022.12.02 11:00` through `2026.06.04 12:00`; `DATA/XAUUSD_H1_OHLC.csv` and `MT/MQL4/Files/XAUUSD_H1_OHLC.csv` cover `2004.06.11 07:00` through `2026.07.01 09:00`; `MT/MQL4/Files/XAUUSD_M5_OHLC.csv` covers `2004.06.11 07:15` through `2026.07.21 07:00`.
- User-provided coverage note: H1/M5 OHLC is available at least through `2026-06-01`; local preflight must still require coverage through the actual locked-test max timestamp `2026.06.04 12:00`.
- Whether the chosen test file has ever been used for selecting features, models, thresholds, entries, exits, stops, spreads or normalization decisions.
- M5 execution-order diagnostic is mandatory as a disclosure artifact in this stage, but cannot affect keep/reject. If the existing simulator cannot compute a field, record `NOT_COMPUTABLE` with reason instead of changing the trading result.

---

### Task 1: Freeze The 11-System Locked-Test Contract

**Files:**
- Create: `ML/baseline/fractal0_fixed11_locked_test.py`
- Create: `ML/reports/fractal0_fixed11_locked_test_freeze.json`
- Create: `ML/reports/fractal0_fixed11_locked_test_selection_policy.json`
- Test: `tests/test_fractal0_fixed11_locked_test.py`

**Interfaces:**
- Consumes: `ML/reports/leaderboard_closure_audit_rules.csv`, `ML/reports/fractal0_fixed11_internal_closure_rerun.json`, `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv`, `audit_leaderboard_robustness.LEADERBOARD_RULES`, `audit_leaderboard_robustness.verify_leaderboard_contract`.
- Produces: freeze JSON with `rules`, `execution_contract`, `selection_policy`, `rule_hash_sha256`, `locked_test_opened=false`.

**Applicable Methodology:** `09-validation-freeze.md`, `16-reporting-audit.md`.

**Mandatory Checks:**
- Exactly 11 rules.
- The exact 11 rules match `audit_leaderboard_robustness.LEADERBOARD_RULES`: `original_rank`, `rule_id`, `profile_id`, `model_id`, `target_id`, `filter_id`, saved cutoff and source metrics.
- Full execution contract is verified through `audit_leaderboard_robustness.verify_leaderboard_contract` on `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv`; do not use `leaderboard_closure_audit_rules.csv` as the sole source of execution contract.
- All rules have fixed `S2/E3/M0/X2`, `canonical_spread=0.2`, `entry_filter_score_col=rich_entry_score`.
- Every rule has saved `score_cutoff_on_val_select`.
- `ML/reports/fractal0_fixed11_internal_closure_rerun.json` has `status=completed`, `verdict=research_only`, `leaderboard_rule_count=11`, `locked_test=not_opened`, and `source_rules_csv_sha256` matching `ML/reports/leaderboard_closure_audit_rules.csv`.
- Freeze artifact records source file hashes.
- Freeze artifact records `execution_ohlc_path=DATA/XAUUSD_H1_OHLC.csv`, `execution_ohlc_sha256`, `m5_execution_ohlc_path=MT/MQL4/Files/XAUUSD_M5_OHLC.csv`, `m5_execution_ohlc_sha256`, price convention, spread definition, entry/fill/SL/exit/timeout rules and same-bar fallback.
- Freeze artifact records `rule_hash_sha256` as canonical SHA256 over rules, execution contract and selection policy.
- Selection policy is written before opening `locked_test`.

**Completion Criterion:** Freeze and policy artifacts exist and tests prove that changing any frozen contract field fails validation.

- [ ] **Step 1: Add failing tests for freeze contract**

Create `tests/test_fractal0_fixed11_locked_test.py` with tests that call planned helper functions:

```python
from pathlib import Path

import pytest

from ML.baseline import fractal0_fixed11_locked_test as locked


def test_freeze_contract_requires_exactly_11_rules(tmp_path):
    rules = locked.load_fixed11_rules(
        Path("ML/reports/leaderboard_closure_audit_rules.csv"),
        summary_path=Path("ML/reports/fractal0_rich_entry_quality_normalized_summary.csv"),
    )
    freeze = locked.build_locked_test_freeze(
        rules,
        locked_test_path=Path("DATA/Nero_XAUUSD_test_labeled.csv"),
        source_rerun_json=Path("ML/reports/fractal0_fixed11_internal_closure_rerun.json"),
    )
    assert freeze["rule_count"] == 11
    assert freeze["locked_test_opened"] is False
    assert freeze["selection_policy"]["max_kept_candidates"] == 3
    assert freeze["rule_hash_sha256"]
    assert freeze["execution_contract"]["execution_ohlc_path"] == "DATA/XAUUSD_H1_OHLC.csv"


def test_freeze_contract_rejects_changed_rule_identity():
    rules = locked.load_fixed11_rules(
        Path("ML/reports/leaderboard_closure_audit_rules.csv"),
        summary_path=Path("ML/reports/fractal0_rich_entry_quality_normalized_summary.csv"),
    )
    rules[0]["filter_id"] = "top50"
    with pytest.raises(ValueError, match="fixed rule identity"):
        locked.build_locked_test_freeze(
            rules,
            locked_test_path=Path("DATA/Nero_XAUUSD_test_labeled.csv"),
            source_rerun_json=Path("ML/reports/fractal0_fixed11_internal_closure_rerun.json"),
        )
```

- [ ] **Step 2: Run tests and confirm they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_locked_test.py -q
```

Expected: FAIL because `ML.baseline.fractal0_fixed11_locked_test` does not exist.

- [ ] **Step 3: Implement freeze helper**

Create `ML/baseline/fractal0_fixed11_locked_test.py` with:

```python
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from ML.baseline import audit_leaderboard_robustness as leaderboard

MAX_KEPT_CANDIDATES = 3


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_sha256(value: dict[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_fixed11_rules(path: Path, summary_path: Path) -> list[dict[str, Any]]:
    rules_frame = pd.read_csv(path, sep=";")
    summary = pd.read_csv(summary_path, sep=";")
    verified = leaderboard.verify_leaderboard_contract(summary)
    expected_cols = [
        "original_rank",
        "rule_id",
        "profile_id",
        "model_id",
        "target_id",
        "filter_id",
        "score_cutoff_on_val_select",
    ]
    expected = verified[expected_cols].reset_index(drop=True)
    actual = rules_frame[expected_cols].reset_index(drop=True)
    if not actual.equals(expected):
        raise ValueError("fixed rule identity mismatch between rules CSV and verified summary contract")
    return rules_frame.to_dict(orient="records")


def validate_fixed11_rules(rules: list[dict[str, Any]]) -> None:
    if len(rules) != 11:
        raise ValueError(f"expected 11 fixed rules, got {len(rules)}")
    for row, rule in zip(rules, leaderboard.LEADERBOARD_RULES):
        if int(row.get("original_rank")) != rule.original_rank or str(row.get("rule_id")) != rule.rule_id:
            raise ValueError(f"fixed rule identity mismatch for rank {rule.original_rank}")
        for key in ("profile_id", "model_id", "target_id", "filter_id"):
            if str(row.get(key)) != str(getattr(rule, key)):
                raise ValueError(f"fixed rule identity mismatch for {rule.rule_id}: {key}")
        if pd.isna(row.get("score_cutoff_on_val_select")):
            raise ValueError(f"missing score_cutoff_on_val_select for {row.get('rule_id')}")


def build_selection_policy() -> dict[str, Any]:
    return {
        "max_kept_candidates": MAX_KEPT_CANDIDATES,
        "selection_basis": "predefined_locked_test_gates_then_correlation_pruning",
        "gates": {
            "min_locked_test_trades_after_filters": 100,
            "min_active_side_trades": 30,
            "min_net_pf": 1.20,
            "min_bs_p05": 1.00,
            "yearly_or_quarterly_fail_policy": "downgrade_to_research_only_unless_predefined_exception_is_recorded",
            "side_fail_policy": "reject_side_specific_reformulation_without_new_validation_cycle",
            "profit_concentration_policy": "warning_or_reject_by_effective_profit_years_pf_without_best_year_and_bs_p05",
            "stress_cost_policy": "disclose_validation_stress_flags; locked-test run remains canonical spread only",
        },
        "bs_p05_protocol": {
            "method": "existing benchmark_fractal0_entry_exit_grid.block_bootstrap_pf",
            "observation_unit": "trade_pnl_r_sequence",
            "n_bootstrap": 1000,
            "block_size_parameter_recorded": 20,
            "known_limitation": "current helper records block_size but samples individual trades; report must disclose this unless replaced by true block bootstrap before execution",
            "seed": "deterministic from frozen rule/run key",
        },
        "correlation": {"unit": "daily_pnl_by_fill_time", "threshold": 0.90},
        "forbidden_after_open": [
            "entry_id",
            "exit_id",
            "stop_policy_id",
            "mask_id",
            "spread",
            "filter_id",
            "score_cutoff_on_val_select",
            "profile_id",
            "model_id",
            "target_id",
        ],
    }


def build_locked_test_freeze(rules: list[dict[str, Any]], locked_test_path: Path, source_rerun_json: Path) -> dict[str, Any]:
    validate_fixed11_rules(rules)
    rerun = json.loads(source_rerun_json.read_text(encoding="utf-8"))
    if rerun.get("status") != "completed" or rerun.get("locked_test") != "not_opened" or int(rerun.get("leaderboard_rule_count", 0)) != 11:
        raise ValueError("source rerun JSON is not a completed fixed11 not_opened artifact")
    execution_contract = {
        "stop_policy_id": leaderboard.STOP_POLICY_ID,
        "entry_id": leaderboard.ENTRY_ID,
        "mask_id": leaderboard.MASK_ID,
        "exit_id": leaderboard.EXIT_ID,
        "canonical_spread": leaderboard.CANONICAL_SPREAD,
        "entry_filter_score_col": leaderboard.ENTRY_FILTER_SCORE_COL,
        "execution_ohlc_path": "DATA/XAUUSD_H1_OHLC.csv",
        "m5_execution_ohlc_path": "MT/MQL4/Files/XAUUSD_M5_OHLC.csv",
        "ohlc_price_type": "bid",
        "spread_definition": "full bid-ask spread",
        "same_bar_tp_sl_policy": "copy from base.CONFIG before run",
        "m5_role": "execution_order_diagnostic_only",
    }
    selection_policy = build_selection_policy()
    freeze = {
        "status": "frozen_before_locked_test",
        "locked_test_opened": False,
        "locked_test_path": str(locked_test_path),
        "rule_count": len(rules),
        "rules": rules,
        "execution_contract": execution_contract,
        "selection_policy": selection_policy,
        "source_rerun_json": str(source_rerun_json),
        "source_rerun_json_sha256": sha256_file(source_rerun_json),
    }
    freeze["rule_hash_sha256"] = _canonical_json_sha256({
        "rules": rules,
        "execution_contract": execution_contract,
        "selection_policy": selection_policy,
    })
    return freeze
```

- [ ] **Step 4: Run tests and confirm they pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_locked_test.py -q
```

Expected: PASS.

- [ ] **Step 5: Write freeze artifacts**

Add CLI support to write:

```text
ML/reports/fractal0_fixed11_locked_test_freeze.json
ML/reports/fractal0_fixed11_locked_test_selection_policy.json
```

The policy must include these gates:

```text
reject if locked_test_trades_after_filters < 100
reject active side if side_trades < 30
reject if net_pf < 1.20
reject if bs_p05 < 1.00
reject if max_drawdown_r is materially worse than validation without explanation
keep at most 3 candidates
if pairwise daily-PnL correlation >= 0.90, keep only the higher-ranked candidate by bs_p05, then PF, then lower drawdown
yearly/quarterly/BUY/SELL/profit-concentration/stress-cost checks produce PASS/WARNING/FAIL and can downgrade `candidate` to `research_only`
each KEEP_CANDIDATE requires a model-card artifact in Task 5
```

Run:

```bash
./.venv/bin/python ML/baseline/fractal0_fixed11_locked_test.py \
  --mode freeze \
  --source-rules-csv ML/reports/leaderboard_closure_audit_rules.csv \
  --source-summary-csv ML/reports/fractal0_rich_entry_quality_normalized_summary.csv \
  --source-rerun-json ML/reports/fractal0_fixed11_internal_closure_rerun.json \
  --locked-test-path DATA/Nero_XAUUSD_test_labeled.csv \
  --output-prefix ML/reports/fractal0_fixed11_locked_test
```

Expected: both freeze artifacts are written and contain the same `rule_hash_sha256`.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/fractal0_fixed11_locked_test.py tests/test_fractal0_fixed11_locked_test.py ML/reports/fractal0_fixed11_locked_test_freeze.json ML/reports/fractal0_fixed11_locked_test_selection_policy.json
git commit -m "Freeze fixed11 locked test protocol"
```

---

### Task 2: Verify Locked-Test Split Eligibility Without Running Models

**Files:**
- Modify: `ML/baseline/fractal0_fixed11_locked_test.py`
- Create: `ML/reports/fractal0_fixed11_locked_test_split_preflight.json`
- Test: `tests/test_fractal0_fixed11_locked_test.py`

**Interfaces:**
- Consumes: freeze JSON, candidate locked-test CSV.
- Produces: preflight JSON with `locked_test_eligible=true|false`, date boundaries, row count, hash, reason.

**Applicable Methodology:** `06-temporal-split.md`, `10-frozen-test-oos.md`.

**Mandatory Checks:**
- Locked-test file exists at `DATA/Nero_XAUUSD_test_labeled.csv`.
- It has required columns: `time`, `ATR`, `fractal0`.
- Time parsing uses strict project format `"%Y.%m.%d %H:%M"` with `errors="raise"`; reject ISO-only or mixed timestamp formats unless explicitly converted before this stage.
- Parsed times are non-null, monotonic increasing and duplicate policy is recorded.
- H1 OHLC exists and covers the actual locked-test timestamp range, currently expected through `2026.06.04 12:00`.
- M5 OHLC exists and covers the actual locked-test timestamp range; it is execution-order diagnostic only.
- It has not been recorded as used by the source validation artifacts.
- Time range is after validation range.
- No shuffle or random row sampling.
- Preflight JSON includes `alternate_locked_test_candidates` for `DATA/Nero_test_labeled.csv` with path, exists, size, sha256 and decision `not_used_without_explicit_human_choice`.

**Completion Criterion:** Preflight exits non-zero with `UNKNOWN_LOCKED_TEST_CONTRACT` if eligibility cannot be proven; otherwise writes `locked_test_eligible=true`.

- [ ] **Step 1: Add tests for missing and valid locked-test files**

Add tests:

```python
def test_locked_test_preflight_rejects_missing_file(tmp_path):
    result = locked.locked_test_preflight(tmp_path / "missing.csv")
    assert result["locked_test_eligible"] is False
    assert result["decision"] == "UNKNOWN_LOCKED_TEST_CONTRACT"


def test_locked_test_preflight_accepts_minimal_sorted_file(tmp_path):
    path = tmp_path / "locked.csv"
    path.write_text(
        "time;ATR;fractal0\n"
        "2023.01.01 00:00;1;1:2:-1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1:0\n"
        "2023.01.01 01:00;1;1:3:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1:0\n",
        encoding="utf-8",
    )
    result = locked.locked_test_preflight(path)
    assert result["locked_test_eligible"] is True
    assert result["raw_rows"] == 2
```

- [ ] **Step 2: Implement preflight**

Implement `locked_test_preflight(path: Path) -> dict[str, Any]` using `pd.read_csv(path, sep=";", usecols=["time", "ATR", "fractal0"])`, `pd.to_datetime(frame["time"], format="%Y.%m.%d %H:%M", errors="raise")`, sorted timestamp checks, duplicate count, H1/M5 coverage checks and alternate candidate metadata.

- [ ] **Step 3: Run tests**

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_locked_test.py -q
```

Expected: PASS.

- [ ] **Step 4: Run preflight on the real locked-test path**

Run only the confirmed project path. Do not silently switch to the generic test file.

```bash
./.venv/bin/python ML/baseline/fractal0_fixed11_locked_test.py \
  --mode preflight \
  --locked-test-path DATA/Nero_XAUUSD_test_labeled.csv \
  --output-prefix ML/reports/fractal0_fixed11_locked_test
```

Expected: JSON written. Do not silently switch to `DATA/Nero_test_labeled.csv`; use it only after an explicit human decision because `DATA/Nero_XAUUSD_test_labeled.csv` exists locally.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/fractal0_fixed11_locked_test.py tests/test_fractal0_fixed11_locked_test.py ML/reports/fractal0_fixed11_locked_test_split_preflight.json
git commit -m "Add fixed11 locked test preflight"
```

---

### Task 3: Run The 11 Frozen Systems On Locked Test Once

**Files:**
- Modify: `ML/baseline/fractal0_fixed11_locked_test.py`
- Create: `ML/reports/fractal0_fixed11_locked_test.json`
- Create: `ML/reports/fractal0_fixed11_locked_test_summary.csv`
- Create: `ML/reports/fractal0_fixed11_locked_test_trades.csv`
- Create: `ML/reports/fractal0_fixed11_locked_test_yearly.csv`
- Create: `ML/reports/fractal0_fixed11_locked_test_quarterly.csv`
- Create: `ML/reports/fractal0_fixed11_locked_test_side.csv`
- Create: `ML/reports/fractal0_fixed11_locked_test_execution_order_diagnostic.csv`
- Create: `ML/reports/fractal0_fixed11_locked_test_execution_order_diagnostic.json`
- Test: `tests/test_fractal0_fixed11_locked_test.py`

**Interfaces:**
- Consumes: freeze JSON, preflight JSON, frozen rules, train/validation data, locked-test data.
- Produces: locked-test summaries and trades for exactly 11 fixed systems.

**Applicable Methodology:** `10-frozen-test-oos.md`, `12-backtest-costs.md`.

**Mandatory Checks:**
- Run only if preflight says `locked_test_eligible=true`.
- Use saved validation cutoffs; do not recalculate top30/top40/top50 on locked-test rows.
- Train/scaler fit remains on `train_core`; validation/locked-test do not fit scaler.
- Use canonical spread `0.2`.
- Use H1 OHLC as the primary execution convention. Use M5 only for execution-order disclosure in `fractal0_fixed11_locked_test_execution_order_diagnostic.*`; do not use M5 as a feature source or to change candidate ranking after seeing locked-test results.
- Record execution diagnostic fields: H1 coverage, M5 coverage, `ambiguous_same_bar_rate_h1`, `ambiguous_same_bar_rate_m5` or `NOT_COMPUTABLE`, unresolved rate and fallback policy.
- Output records `locked_test_opened=true` and `opened_at_utc`.
- If any frozen field changes, abort with `INVALID_FROZEN_RULE_CONTRACT`.

**Completion Criterion:** One locked-test run produces 11 summary rows and a non-empty trades CSV, or a structured failure artifact explaining why the test was not opened.

- [ ] **Step 1: Add tests for saved-cutoff reuse**

Add a test that creates fake scored rows and proves `apply_entry_filter(..., mode="eval", score_cutoff=saved_cutoff)` is used, not locked-test percentile selection.

- [ ] **Step 2: Implement locked-test split loading**

Add a loader that returns:

```python
{
    "train_core": train_frame,
    "val_select": val_select_frame,
    "val_eval": val_eval_frame,
    "locked_test": locked_test_frame,
}
```

Training may use `train_core`; selection may read validation cutoffs only from frozen rules; evaluation metrics are computed only on `locked_test`.

- [ ] **Step 3: Implement locked-test scoring and simulation**

Reuse existing rich helpers:

```python
rich.build_entry_rows(...)
rich.attach_movement_scores(...)
rich.build_normalized_rich_feature_frame(...)
rich.train_rich_entry_model(...)
rich.score_rich_entry_model(...)
rich.apply_entry_filter(..., mode="eval", score_cutoff=frozen_cutoff)
rich._simulate_for_filter(...)
rich._summary_for_filter(...)
```

Do not add new model profiles, targets, filters, spreads or exits.

- [ ] **Step 4: Run smoke test on one rule only**

```bash
./.venv/bin/python ML/baseline/fractal0_fixed11_locked_test.py \
  --mode run \
  --locked-test-path DATA/Nero_XAUUSD_test_labeled.csv \
  --source-rules-csv ML/reports/leaderboard_closure_audit_rules.csv \
  --output-prefix /tmp/fractal0_fixed11_locked_test_smoke \
  --smoke-first-rule-only
```

Expected: one summary row, `locked_test_opened=true`, no contract mutation. The runner should default to `min(os.cpu_count() or 1, 24)` threads; pass `--threads 24` only when the current machine can safely run 24 workers.

- [ ] **Step 5: Run full locked test once**

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/fractal0_fixed11_locked_test.py \
  --mode run \
  --locked-test-path DATA/Nero_XAUUSD_test_labeled.csv \
  --source-rules-csv ML/reports/leaderboard_closure_audit_rules.csv \
  --output-prefix ML/reports/fractal0_fixed11_locked_test
```

Expected: 11 summary rows and execution-order diagnostic artifacts. Do not rerun after looking at results unless the first run ended before opening locked-test metrics and produced `UNKNOWN`.

- [ ] **Step 6: Run tests**

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_locked_test.py -q
./.venv/bin/python -m pytest tests/ -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add ML/baseline/fractal0_fixed11_locked_test.py tests/test_fractal0_fixed11_locked_test.py ML/reports/fractal0_fixed11_locked_test.json ML/reports/fractal0_fixed11_locked_test_summary.csv ML/reports/fractal0_fixed11_locked_test_trades.csv ML/reports/fractal0_fixed11_locked_test_yearly.csv ML/reports/fractal0_fixed11_locked_test_quarterly.csv ML/reports/fractal0_fixed11_locked_test_side.csv ML/reports/fractal0_fixed11_locked_test_execution_order_diagnostic.csv ML/reports/fractal0_fixed11_locked_test_execution_order_diagnostic.json
git commit -m "Run fixed11 locked test"
```

---

### Task 4: Apply Predefined Keep/Reject And Correlation Selection

**Files:**
- Modify: `ML/baseline/fractal0_fixed11_locked_test.py`
- Create: `ML/reports/fractal0_fixed11_locked_test_selection.csv`
- Create: `ML/reports/fractal0_fixed11_locked_test_correlation.csv`
- Test: `tests/test_fractal0_fixed11_locked_test.py`

**Interfaces:**
- Consumes: locked-test summary/trades.
- Produces: selection artifact with `decision` per rule: `REJECT`, `KEEP_CANDIDATE`, `CORRELATED_DROP`, `DIAGNOSTIC_ONLY_SMALL_N`.

**Applicable Methodology:** `10-frozen-test-oos.md`, `11-robustness.md`.

**Mandatory Checks:**
- Reject rules with too few trades before ranking.
- Compute yearly, quarterly, BUY/SELL and profit concentration statuses before candidate ranking.
- Use `PASS/WARNING/FAIL` status columns for each gate; aggregate PF cannot hide a failing year, quarter or side without verdict downgrade.
- Do not create a new threshold, side-only variant or hour-only variant from locked-test observations.
- Correlation is used only to reduce kept candidates, not to rescue failed candidates.
- If all kept rules have pairwise correlation `>=0.90`, keep only one.

**Completion Criterion:** At most 3 candidates have `KEEP_CANDIDATE`; all rejects/downgrades include a machine-readable reason and every kept candidate has a model-card artifact in Task 5.

- [ ] **Step 1: Add selection tests**

Add tests for:

```text
low N -> DIAGNOSTIC_ONLY_SMALL_N
PF < 1.20 -> REJECT
BS_p05 < 1.00 -> REJECT
negative yearly/quarterly/side gate -> verdict downgrade or REJECT by predefined policy
profit concentration fail -> verdict downgrade or REJECT by predefined policy
two passing rules with correlation 0.95 -> only one KEEP_CANDIDATE
two passing rules with correlation 0.40 -> both can remain, up to max 3
```

- [ ] **Step 2: Implement daily PnL correlation**

Build daily PnL by `fill_time.date()` from `fractal0_fixed11_locked_test_trades.csv`, pivot by `rule_id`, fill missing days with `0.0`, compute Pearson correlation.

- [ ] **Step 3: Implement selection order**

Sort eligible rules by:

```text
bs_p05 descending
pf descending
max_drawdown_r ascending
n_trades descending
original_rank ascending
```

Then prune candidates with correlation `>=0.90` to any already-kept candidate.

Before final `KEEP_CANDIDATE`, apply downgrade rules:

```text
if yearly_status == FAIL or quarterly_status == FAIL -> verdict at most research_only unless policy marks reject
if side_status == FAIL -> reject side-specific rewrite; full rule may stay only as research_only
if profit_concentration_status == FAIL and bs_p05 < 1.00 or pf_without_best_year < 1.00 -> REJECT
if execution_order_diagnostic_status == NOT_COMPUTABLE -> verdict at most research_only for execution claims
```

- [ ] **Step 4: Run selection**

```bash
./.venv/bin/python ML/baseline/fractal0_fixed11_locked_test.py \
  --mode select \
  --output-prefix ML/reports/fractal0_fixed11_locked_test
```

Expected: selection and correlation CSVs written.

- [ ] **Step 5: Run tests and commit**

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_locked_test.py -q
git add ML/baseline/fractal0_fixed11_locked_test.py tests/test_fractal0_fixed11_locked_test.py ML/reports/fractal0_fixed11_locked_test_selection.csv ML/reports/fractal0_fixed11_locked_test_correlation.csv
git commit -m "Select fixed11 locked test candidates"
```

---

### Task 5: Report, Documentation, And Follow-Up Gates

**Files:**
- Create: `docs/ML/fractal0_fixed11_locked_test.py.md`
- Create: `docs/reports/2026-07-23-fractal0-fixed11-locked-test.md`
- Create: `ML/reports/fractal0_fixed11_locked_test_model_card_rankXX.json` for every `KEEP_CANDIDATE`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `MODULE_INDEX.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`

**Interfaces:**
- Consumes: locked-test JSON/CSV artifacts and selection CSV.
- Produces: canonical report with final verdict and next actions.

**Applicable Methodology:** `13-export-mt4-parity.md`, `16-reporting-audit.md`.

**Mandatory Checks:**
- Report states whether `locked_test` was used for selecting 1-3 from 11.
- Report states that no rule changes are allowed from locked-test observations.
- If candidates are kept, report says next required checks: MT4 parity, provider drift, demo/forward.
- Every kept candidate has a model card with instrument/timeframe, decision time, feature contract, target/label contract, train/validation/locked-test windows, rule/export paths, cumulative search budget, cost assumptions, validation/locked-test verdicts, known risks and monitoring/retraining policy.
- If all fail, report closes the branch and forbids further tuning on this locked-test result.
- Report includes commands, hashes, split boundaries, sample-size gates, yearly/side/correlation tables and limitations.

**Completion Criterion:** Report and sync docs allow the next agent to reproduce the run and understand whether the branch is rejected or has 1-3 candidates for MT4 parity.

- [ ] **Step 1: Write report**

Create `docs/reports/2026-07-23-fractal0-fixed11-locked-test.md` with sections required by `16-reporting-audit.md`:

```text
Context
Уровень этапа
What Was Done
Multiple Testing Context
Changed Files
Verification
Results
Conclusions
Limitations / Open Questions
Split Disclosure
Next Step
Related Materials
```

For every `KEEP_CANDIDATE`, create `ML/reports/fractal0_fixed11_locked_test_model_card_rankXX.json`. If there are no kept candidates, write `model_card_status=NOT_APPLICABLE_NO_KEEP_CANDIDATES` in the report and primary JSON.

- [ ] **Step 2: Add module docs**

Create `docs/ML/fractal0_fixed11_locked_test.py.md` explaining CLI modes:

```text
preflight
freeze
run
select
```

- [ ] **Step 3: Sync project docs**

Update `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `docs/superpowers/roadmap.md`, `MODULE_INDEX.md` and wiki pages with the final verdict.

- [ ] **Step 4: Run verification**

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_locked_test.py -q
./.venv/bin/python -m pytest tests/ -q
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

Expected: tests pass and wiki status has no gaps.

- [ ] **Step 5: Commit**

```bash
git add docs/ML/fractal0_fixed11_locked_test.py.md docs/reports/2026-07-23-fractal0-fixed11-locked-test.md ML/reports/fractal0_fixed11_locked_test_model_card_rank*.json CHANGELOG.md CONTEXT_HANDOFF.md docs/superpowers/roadmap.md MODULE_INDEX.md wiki/research/fractal-stop-research.md wiki/index.md wiki/log.md
git commit -m "Document fixed11 locked test verdict"
```

---

## Final Decision Rules

If no rule passes locked-test gates:

```text
verdict=reject
decision=FIXED11_LOCKED_TEST_REJECTED
next_action=close_branch_no_locked_test_tuning
```

If 1-3 low-correlation rules pass:

```text
verdict=candidate
decision=FIXED11_LOCKED_TEST_CANDIDATES_FOR_MT4_PARITY
next_action=MT4 parity, provider drift, demo/forward
```

This `candidate` verdict is allowed only if sample-size, side/year/quarter/profit-concentration gates are not `FAIL`, execution-order diagnostic is either computed or explicitly non-blocking, and model cards exist for every kept candidate. Otherwise downgrade to `research_only` with machine-readable reasons.

If rules pass but sample-size gate fails:

```text
verdict=research_only
decision=LOCKED_TEST_DIAGNOSTIC_ONLY_SMALL_N
next_action=do_not_trade; require more forward data or new cycle
```

If locked-test contract cannot be proven clean:

```text
verdict=unknown
decision=UNKNOWN_LOCKED_TEST_CONTRACT
next_action=do not open test; identify clean holdout or forward-only period
```

## Self-Review

- Spec coverage: plan covers fixed 11 systems, one locked-test opening, predefined keep/reject, correlation pruning, and follow-up parity/provider/demo checks.
- Placeholder scan: no placeholder markers or unspecified implementation step remains.
- Type consistency: helper names are consistent across tasks: `load_fixed11_rules`, `build_locked_test_freeze`, `locked_test_preflight`.
- Known unknowns are explicit and gated before opening `locked_test`.
