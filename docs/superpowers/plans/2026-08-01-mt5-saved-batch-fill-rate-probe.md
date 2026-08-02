# MT5 Saved-Batch Fill-Rate Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompose the failed MT5 batch's signal-to-trade conversion rate using only already saved batch artifacts, separating position-policy blocking from real broker no-fill and from any still-unexplained residual.

**Non-goal (explicit):** This probe does not measure "broker fill rate" in the order-submission sense. The existing `fill_rate` field in `post_batch_diagnostics.json` is `trades_count / active_signal_rows` (a signal-to-trade conversion rate), not `placed / (placed + broker_refused)`. The probe keeps the existing `fill_rate` field as-is and reports its decomposition, instead of re-defining the field.

**Architecture:** Extend the existing read-only MT5 diagnostics module with one focused `fill-rate` phase. The phase joins `batch_summary.json`, per-run `entry_signals.json`, per-run `events.csv`, and available per-run `metrics.json` when present, then writes compact JSON/CSV diagnostics and a report. The work is diagnostic only: it can produce a next research hypothesis, but cannot select a winner or change the trading rule. Note the data lives in two layers that must not be conflated: `active_signal_rows` comes from the pre-tester `entry_signals.json`, while `ORDER_PLACED` and `OPEN_FAILED` come from the MT5 tester event stream; their totals need not match 1:1 (one signal can raise several `OPEN_FAILED` retries, and several same-bar active signals after one open can all be blocked by the one-position policy).

**Tech Stack:** Python via `./.venv/bin/python`, `pandas`, `json`, `pytest`, existing module `ML/baseline/mt5_execution_diagnostics.py`, saved artifacts in `ML/reports/mt5_execution_loop/batch/`.

## Global Constraints

- Work from repository root `/home/hohla/git/SoSimple`.
- Use `./.venv/bin/python` for Python commands.
- Read `docs/methodology/README.md` first, then only the relevant methodology files listed below.
- Use only current saved batch artifacts; do not rerun MT5 tester in this plan.
- Do not open or use `locked_test`.
- Do not select a new winner, threshold, model, profile, side, horizon, entry/exit rule, stop, spread, cost, or PnL convention.
- Maximum verdict is `DIAGNOSTIC_ONLY`; optional next-step status may be `research_hypothesis` only if evidence supports it.
- Treat local ignored candidate `metrics.json` files as optional derived inputs: if missing, regenerate metrics from `events.csv` or mark missing fields as `UNKNOWN`.
- Reports must separate facts from hypotheses and must not use trading claims such as profitable, ready, live-ready, tradable.
- `git push` is forbidden unless the user explicitly asks.

---

## Cold-Start Context

Current facts to verify from source files before implementation:

- `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md`: timing-contract rerun completed; LiveUpdate recovery handled; fresh batch has `n_candidates=32`, `n_valid=32`, `n_eligible=11`, `verdict=BATCH_NO_WINNER`.
- `docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md`: top candidate `time_plus_atr_extra_trees_small_12h_thr0.2` has PF `1.2323`, `BS_p05=0.8867479736061653`, `trades_count=102`, fill rate `0.09444444444444444`; all 11 eligible top candidates failed low bootstrap lower bound.
- `ML/reports/mt5_execution_loop/diagnostics/post_batch_diagnostics.json` top candidate `event_summary`: `active_signal_rows=1080`, `ORDER_PLACED=105`, `TX_OPEN=102`, `OPEN_FAILED=859` with `open_failed_reasons.position_or_pending_order_exists=853` and `open_failed_reasons.pending_order_not_found_after_order_placed=6`. The advisor is single-position, so `position_or_pending_order_exists` is the policy blocking branch, not a broker refusal.
- Known accounting residual to resolve inside this probe: `ORDER_PLACED + OPEN_FAILED = 964` vs `active_signal_rows = 1080` leaves 116 signals (10.7%) that raised neither `ORDER_PLACED` nor `OPEN_FAILED` in the event stream. The probe should disclose this residual and break it down where possible (same-bar duplicate signals, `ML_CLOSE` pre-emptions, `TIMING_VIOLATION`, other), and leave it as `UNKNOWN` if the saved artifacts do not support a breakdown.
- `ML/reports/mt5_execution_loop/batch/batch_summary.json`: canonical structured batch summary.
- `ML/reports/mt5_execution_loop/batch/{run_id}/entry_signals.json`: active, buy, and sell signal counts.
- `ML/reports/mt5_execution_loop/batch/{run_id}/events.csv`: event stream for each candidate.
- `ML/reports/mt5_execution_loop/batch/{run_id}/metrics.json`: optional local derived metrics; ignored for candidate dirs by `.gitignore`.

Known unknowns:

- Per-signal no-fill attribution may be incomplete because `events.csv` records events, not every signal row that never became an order. The 116-signal residual (`active_signal_rows - ORDER_PLACED - OPEN_FAILED`) is explicitly within this limit and may remain `UNKNOWN`.
- Row-level linkage between `ERROR_SoSimple_*.csv` and events is still `UNKNOWN`; do not infer causality from error CSVs.
- Cost model is incomplete for final trading verdict: swap, commission, slippage, latency, and stress-cost checks remain unresolved.

## Methodology Map

- `docs/methodology/00-research-management.md`: applies to scope, level, allowed verdict, search budget, `locked_test` policy, and forbidden interpretations. Mandatory checks: fixed diagnostic level; no hidden selection; no `locked_test`; explicit `allowed_max_verdict`.
- `docs/methodology/A5-post-mortem-diagnostics.md`: applies because batch ended `BATCH_NO_WINNER`. Mandatory checks: reproduce baseline, decompose result, separate model weakness from rule/execution/sample-size weakness, keep output `DIAGNOSTIC_ONLY`.
- `docs/methodology/11-robustness.md`: applies to yearly and BUY/SELL concentration. Mandatory checks: aggregate PF is not enough; side-specific weakness is not hidden; profit concentration is checked as a package.
- `docs/methodology/12-backtest-costs.md`: applies only via its fill/no-fill and missed-opens policy (`12-backtest-costs.md:50`, `:127`, `:130`); the stage does not compute a production cost model (spread, commission, swap, slippage, requote). Fill-rate attribution itself follows `A5-post-mortem-diagnostics`, not the backtest cost model.
- `docs/methodology/13b-mt5-execution-parity.md`: applies to MT5 event rows and execution anomaly classes. Mandatory checks: event discrepancies are classified; tester result is not model quality; timing contract remains checked.
- `docs/methodology/16-reporting-audit.md`: applies to final report and documentation sync. Mandatory checks: facts vs hypotheses; commands, paths, artifact hashes; limitations; next step; report numbers match JSON/CSV artifacts.

No methodology section exactly covers "fill-rate attribution from saved MT5 batch events". Use `A5` as the main post-mortem method, with `12` only for fill/no-fill policy risk and `13b` for event interpretation.

### Sample size gate for this probe

This is a `DIAGNOSTIC_ONLY` post-mortem probe over already saved batch artifacts, not a model/selection run, so the numeric `min_*` thresholds from `00-research-management.md` map to disclosure rather than to gating:

- Each candidate row discloses `active_signal_rows`, `trades_count`, `buy_signal_rows`, `sell_signal_rows`.
- `fill_rate_by_status.eligible_top.count` is the working sample size for the decision rule. If fewer than 6 eligible candidates have a non-null `fill_rate`, the decision is `UNKNOWN` regardless of the median.
- 16 `DIAGNOSTIC_ONLY` candidates (with `trades_count=0` for many of them) are reported separately in `fill_rate_by_status.diagnostic_only` and do not enter the decision rule, so they cannot bias the median.
- No `min_trades_per_year` is applied because this probe does not select a winner or a tradable rule; per-year trades remain visible via the existing `pf_by_year` already in `batch_summary.json`.

## File Structure

- Modify `ML/baseline/mt5_execution_diagnostics.py`: add pure functions for fill-rate diagnostics and a CLI phase `fill-rate`.
- Modify `tests/test_mt5_execution_diagnostics.py`: add focused tests for fill-rate calculations, missing optional metrics, event reason buckets, and no-winner guard.
- Create `ML/reports/mt5_execution_loop/diagnostics/fill_rate_diagnostics.json`: structured summary.
- Create `ML/reports/mt5_execution_loop/diagnostics/fill_rate_candidates.csv`: per-candidate table.
- Create `docs/reports/2026-08-01-mt5-saved-batch-fill-rate-probe.md`: final diagnostic report.
- Modify `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, and `docs/superpowers/roadmap.md` only after the report changes project state.

---

### Task 1: Artifact Contract And Fill-Rate Core

**Files:**
- Modify: `ML/baseline/mt5_execution_diagnostics.py`
- Modify: `tests/test_mt5_execution_diagnostics.py`

**Applicable Methodology:** `00-research-management.md`, `A5-post-mortem-diagnostics.md`, `16-reporting-audit.md`.

**Mandatory Checks:**
- Uses saved artifacts only.
- Keeps batch verdict unchanged as `BATCH_NO_WINNER`.
- Handles missing optional `metrics.json` without failing.
- Does not rank candidates into a new winner.

**Completion Criterion:** focused unit tests fail before implementation and pass after implementation.

**Interfaces:**
- Produces: `count_event_names(events: pd.DataFrame) -> dict[str, int]`
- Produces: `summarize_candidate_fill_rate(run_id: str, batch_root: Path, batch_row: dict[str, object]) -> dict[str, object]`
- Produces: `build_fill_rate_diagnostics(batch_summary_path: Path, batch_root: Path = BATCH_ROOT) -> tuple[dict[str, object], pd.DataFrame]`

- [ ] **Step 1: Write failing tests**

Append these tests to `tests/test_mt5_execution_diagnostics.py`:

```python
def test_summarize_candidate_fill_rate_uses_entry_signal_denominator(tmp_path: Path) -> None:
    from tests.test_parse_mt5_execution_report import _event_row
    from ML.baseline.mt5_execution_diagnostics import summarize_candidate_fill_rate

    run_dir = tmp_path / "candidate_a"
    run_dir.mkdir()
    (run_dir / "entry_signals.json").write_text(
        json.dumps({"active_signal_rows": 100, "buy_rows": 40, "sell_rows": 60}),
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            _event_row("ORDER_PLACED", "2022.01.01 10:00"),
            _event_row("OPEN", "2022.01.01 11:00", side="BUY"),
            _event_row("CLOSE", "2022.01.01 15:00", side="BUY", profit=12.0),
            _event_row("ORDER_EXPIRED", "2022.01.02 10:00", comment="pending order not active after max_fill_lag_bars"),
            _event_row("OPEN_FAILED", "2022.01.03 10:00", comment="position_or_pending_order_exists"),
        ],
        columns=MT5_EVENT_COLUMNS,
    ).to_csv(run_dir / "events.csv", sep=";", index=False)

    row = {"run_id": "candidate_a", "trades_count": 1, "profit_factor": 1.2, "bs_p05": 0.8}
    summary = summarize_candidate_fill_rate("candidate_a", tmp_path, row)

    assert summary["active_signal_rows"] == 100
    assert summary["trades_count"] == 1
    assert summary["fill_rate"] == 0.01
    assert summary["order_placed_count"] == 1
    assert summary["open_failed_count"] == 1
    assert summary["order_expired_count"] == 1
    assert summary["open_failed_reasons"]["position_or_pending_order_exists"] == 1
    assert summary["order_expired_reasons"]["pending_order_not_active_after_max_fill_lag_bars"] == 1
    assert summary["unknowns"] == []


def test_build_fill_rate_diagnostics_preserves_no_winner_and_no_selection(tmp_path: Path) -> None:
    from tests.test_parse_mt5_execution_report import _event_row
    from ML.baseline.mt5_execution_diagnostics import build_fill_rate_diagnostics

    batch_summary = {
        "status": "DIAGNOSTIC_ONLY",
        "verdict": "BATCH_NO_WINNER",
        "winner": None,
        "n_candidates": 2,
        "n_valid": 2,
        "n_eligible": 1,
        "n_diagnostic_only": 1,
        "winners_ranked": [
            {"run_id": "candidate_a", "bs_p05": 0.8, "trades_count": 1},
        ],
        "table": [
            {"run_id": "candidate_a", "trades_count": 1, "profit_factor": 1.2, "bs_p05": 0.8},
            {"run_id": "candidate_b", "trades_count": 0, "profit_factor": 0.0, "bs_p05": 0.0},
        ],
    }
    path = tmp_path / "batch_summary.json"
    path.write_text(json.dumps(batch_summary), encoding="utf-8")
    for run_id, active_rows in [("candidate_a", 100), ("candidate_b", 50)]:
        run_dir = tmp_path / run_id
        run_dir.mkdir()
        (run_dir / "entry_signals.json").write_text(
            json.dumps({"active_signal_rows": active_rows}),
            encoding="utf-8",
        )
        pd.DataFrame([_event_row("ORDER_PLACED", "2022.01.01 10:00")], columns=MT5_EVENT_COLUMNS).to_csv(
            run_dir / "events.csv",
            sep=";",
            index=False,
        )

    summary, table = build_fill_rate_diagnostics(path, tmp_path)

    assert summary["status"] == "DIAGNOSTIC_ONLY"
    assert summary["verdict"] == "BATCH_NO_WINNER"
    assert summary["forbidden_interpretation_guard"] == "no_new_winner_selected"
    assert summary["candidate_count"] == 2
    assert summary["n_diagnostic_only"] == 1
    assert summary["fill_rate_distribution"]["min"] == 0.0
    assert summary["fill_rate_by_status"]["eligible_top"]["count"] == 1
    assert summary["fill_rate_by_status"]["diagnostic_only"]["count"] == 1
    assert summary["fill_rate_by_status"]["eligible_top"]["min"] == 0.01
    assert summary["fill_rate_by_status"]["diagnostic_only"]["min"] == 0.0
    assert len(table) == 2
```

> Note for new contributors: `_event_row` is a private test helper defined in `tests/test_parse_mt5_execution_report.py:12` (and `_tx_row` at `:134`). `test_mt5_execution_diagnostics.py` already imports this helper for existing diagnostics tests, so the import path is established; the helper does not live in `ml5_execution_diagnostics.py`.

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py::test_summarize_candidate_fill_rate_uses_entry_signal_denominator tests/test_mt5_execution_diagnostics.py::test_build_fill_rate_diagnostics_preserves_no_winner_and_no_selection -q
```

Expected: FAIL because the new functions do not exist.

- [ ] **Step 3: Implement core functions**

Add the functions near `summarize_batch_failure` in `ML/baseline/mt5_execution_diagnostics.py`:

```python
def count_event_names(events: pd.DataFrame) -> dict[str, int]:
    if events.empty or "event" not in events.columns:
        return {}
    return _value_counts(events["event"].astype(str))


def _numeric_summary(values: list[float]) -> dict[str, float | None]:
    clean = sorted(value for value in values if value == value)
    if not clean:
        return {"min": None, "p25": None, "median": None, "p75": None, "max": None}
    series = pd.Series(clean, dtype="float64")
    return {
        "min": float(series.min()),
        "p25": float(series.quantile(0.25)),
        "median": float(series.quantile(0.50)),
        "p75": float(series.quantile(0.75)),
        "max": float(series.max()),
    }


def summarize_candidate_fill_rate(
    run_id: str,
    batch_root: Path,
    batch_row: dict[str, object],
) -> dict[str, object]:
    run_dir = batch_root / run_id
    entry_signals = load_json_if_exists(run_dir / "entry_signals.json") or {}
    metrics = load_json_if_exists(run_dir / "metrics.json")
    events_path = run_dir / "events.csv"
    events = load_event_rows([events_path]) if events_path.exists() else _empty_event_frame()
    event_summary = summarize_event_anomalies(events)
    event_counts = count_event_names(events)

    active_signal_rows = _to_int(entry_signals.get("active_signal_rows")) or 0
    trades_count = _to_int(batch_row.get("trades_count")) or _to_int((metrics or {}).get("trades_count")) or 0
    fill_rate = float(trades_count / active_signal_rows) if active_signal_rows > 0 else None

    unknowns = []
    if not entry_signals:
        unknowns.append("entry_signals.json")
    if not events_path.exists():
        unknowns.append("events.csv")
    if metrics is None:
        unknowns.append("metrics.json")

    return {
        "run_id": run_id,
        "profile": batch_row.get("profile"),
        "model_key": batch_row.get("model_key"),
        "horizon": batch_row.get("horizon"),
        "threshold_value": batch_row.get("threshold_value"),
        "profit_factor": batch_row.get("profit_factor"),
        "bs_p05": batch_row.get("bs_p05"),
        "trades_count": trades_count,
        "active_signal_rows": active_signal_rows,
        "buy_signal_rows": _to_int(entry_signals.get("buy_rows")),
        "sell_signal_rows": _to_int(entry_signals.get("sell_rows")),
        "fill_rate": fill_rate,
        "order_placed_count": event_counts.get("ORDER_PLACED", 0),
        "open_count": event_counts.get("OPEN", 0),
        "close_count": event_counts.get("CLOSE", 0),
        "open_failed_count": event_counts.get("OPEN_FAILED", 0),
        "order_expired_count": event_counts.get("ORDER_EXPIRED", 0),
        "open_failed_reasons": event_summary.get("open_failed_reasons", {}),
        "order_expired_reasons": event_summary.get("order_expired_reasons", {}),
        "reconciliation": compute_mt5_metrics(events)["reconciliation"] if not events.empty else {},
        "unknowns": unknowns,
    }


def build_fill_rate_diagnostics(
    batch_summary_path: Path,
    batch_root: Path = BATCH_ROOT,
) -> tuple[dict[str, object], pd.DataFrame]:
    data = json.loads(batch_summary_path.read_text(encoding="utf-8"))
    rows = []
    for row in data.get("table", []):
        run_id = str(row.get("run_id", "")).strip()
        if run_id:
            rows.append(summarize_candidate_fill_rate(run_id, batch_root, row))

    table = pd.DataFrame(rows)
    fill_rates = [
        float(value)
        for value in table.get("fill_rate", pd.Series(dtype="float64")).dropna().tolist()
    ]
    eligible_run_ids = {
        str(item.get("run_id", "")).strip()
        for item in data.get("winners_ranked", [])
        if item.get("run_id")
    }
    eligible_fill_rates = [
        float(row["fill_rate"])
        for row in rows
        if row.get("run_id") in eligible_run_ids and row.get("fill_rate") is not None
    ]
    diagnostic_fill_rates = [
        float(row["fill_rate"])
        for row in rows
        if row.get("run_id") not in eligible_run_ids and row.get("fill_rate") is not None
    ]
    def _by_status(values: list[float]) -> dict[str, object]:
        summary_status = _numeric_summary(values)
        return {
            "count": len(values),
            **summary_status,
            "low_fill_rate_count_lt_0_20": int(sum(value < 0.20 for value in values)),
        }
    summary = {
        "status": "DIAGNOSTIC_ONLY",
        "verdict": data.get("verdict", "UNKNOWN"),
        "winner": data.get("winner"),
        "candidate_count": len(rows),
        "n_candidates": data.get("n_candidates"),
        "n_valid": data.get("n_valid"),
        "n_eligible": data.get("n_eligible"),
        "n_diagnostic_only": data.get("n_diagnostic_only"),
        "fill_rate_distribution": _numeric_summary(fill_rates),
        "fill_rate_by_status": {
            "eligible_top": _by_status(eligible_fill_rates),
            "diagnostic_only": _by_status(diagnostic_fill_rates),
            "all": _by_status(fill_rates),
        },
        "low_fill_rate_count_lt_0_10": int(sum(value < 0.10 for value in fill_rates)),
        "low_fill_rate_count_lt_0_20": int(sum(value < 0.20 for value in fill_rates)),
        "low_fill_rate_count_lt_0_20_eligible": int(
            sum(value < 0.20 for value in eligible_fill_rates)
        ),
        "total_active_signal_rows": int(sum(row.get("active_signal_rows") or 0 for row in rows)),
        "total_trades": int(sum(row.get("trades_count") or 0 for row in rows)),
        "total_open_failed": int(sum(row.get("open_failed_count") or 0 for row in rows)),
        "total_order_expired": int(sum(row.get("order_expired_count") or 0 for row in rows)),
        "unknowns": {
            "missing_per_run_inputs": {
                row["run_id"]: row["unknowns"]
                for row in rows
                if row.get("unknowns")
            }
        },
        "forbidden_interpretation_guard": "no_new_winner_selected",
    }
    return summary, table
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit task**

Run:

```bash
git add ML/baseline/mt5_execution_diagnostics.py tests/test_mt5_execution_diagnostics.py
git commit -m "feat: add mt5 fill rate diagnostics"
```

---

### Task 2: CLI Phase And Diagnostic Artifacts

**Files:**
- Modify: `ML/baseline/mt5_execution_diagnostics.py`
- Output: `ML/reports/mt5_execution_loop/diagnostics/fill_rate_diagnostics.json`
- Output: `ML/reports/mt5_execution_loop/diagnostics/fill_rate_candidates.csv`

**Applicable Methodology:** `A5-post-mortem-diagnostics.md`, `12-backtest-costs.md`, `13b-mt5-execution-parity.md`, `16-reporting-audit.md`.

**Mandatory Checks:**
- CLI writes both JSON and CSV.
- CSV is semicolon-separated.
- `_smoke` and service directories are excluded because the table comes from `batch_summary.json`.
- Missing optional `metrics.json` is disclosed, not fatal.

**Completion Criterion:** `fill_rate_diagnostics.json` and `fill_rate_candidates.csv` are created and match the saved batch candidate count.

**Interfaces:**
- Consumes: `build_fill_rate_diagnostics(batch_summary_path: Path, batch_root: Path) -> tuple[dict[str, object], pd.DataFrame]`
- Produces CLI: `./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics --phase fill-rate --output-json ... --output-csv ...`

- [ ] **Step 1: Write failing CLI test**

Append this test to `tests/test_mt5_execution_diagnostics.py`:

```python
def test_cli_phase_choices_include_fill_rate() -> None:
    import argparse
    import inspect
    from ML.baseline import mt5_execution_diagnostics as diag

    source = inspect.getsource(diag.main)
    assert '"fill-rate"' in source
    assert "build_fill_rate_diagnostics" in source
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py::test_cli_phase_choices_include_fill_rate -q
```

Expected: FAIL because CLI phase does not exist yet.

- [ ] **Step 3: Add CLI branch**

Modify `main()` in `ML/baseline/mt5_execution_diagnostics.py`:

```python
parser.add_argument("--phase", choices=["inventory", "errors", "events", "batch", "fill-rate"], required=True)
```

Add branch before the final `elif` chain ends:

```python
elif args.phase == "fill-rate":
    summary, table = build_fill_rate_diagnostics(
        REPO_ROOT / "ML/reports/mt5_execution_loop/batch/batch_summary.json"
    )
    write_json(summary, args.output_json)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([_csv_safe_row(row) for row in table.to_dict("records")]).to_csv(
        args.output_csv,
        sep=";",
        index=False,
    )
```

The `to_dict("records")` write is the minimal required behavior; no `table.apply(...)` line is included in the template.

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py -q
```

Expected: PASS.

- [ ] **Step 5: Generate artifacts**

Run:

```bash
./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics \
  --phase fill-rate \
  --output-json ML/reports/mt5_execution_loop/diagnostics/fill_rate_diagnostics.json \
  --output-csv ML/reports/mt5_execution_loop/diagnostics/fill_rate_candidates.csv
```

Expected:

- command exits `0`;
- JSON file exists;
- CSV file exists;
- JSON has `status=DIAGNOSTIC_ONLY`;
- JSON has `candidate_count=32`;
- JSON has `verdict=BATCH_NO_WINNER`.

- [ ] **Step 6: Verify artifact content**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd

summary = json.loads(Path("ML/reports/mt5_execution_loop/diagnostics/fill_rate_diagnostics.json").read_text())
table = pd.read_csv("ML/reports/mt5_execution_loop/diagnostics/fill_rate_candidates.csv", sep=";")

assert summary["status"] == "DIAGNOSTIC_ONLY"
assert summary["verdict"] == "BATCH_NO_WINNER"
assert summary["candidate_count"] == 32
assert len(table) == 32
assert table["fill_rate"].notna().any()
print("fill_rate_artifacts_ok")
PY
```

Expected: prints `fill_rate_artifacts_ok`.

- [ ] **Step 7: Commit task**

Run:

```bash
git add ML/baseline/mt5_execution_diagnostics.py tests/test_mt5_execution_diagnostics.py ML/reports/mt5_execution_loop/diagnostics/fill_rate_diagnostics.json ML/reports/mt5_execution_loop/diagnostics/fill_rate_candidates.csv
git commit -m "chore: write mt5 fill rate artifacts"
```

---

### Task 3: Evidence Review And Hypothesis Decision

**Files:**
- Read: `ML/reports/mt5_execution_loop/diagnostics/fill_rate_diagnostics.json`
- Read: `ML/reports/mt5_execution_loop/diagnostics/fill_rate_candidates.csv`
- Read: `ML/reports/mt5_execution_loop/diagnostics/post_batch_diagnostics.json`
- Read: `ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json`

**Applicable Methodology:** `A5-post-mortem-diagnostics.md`, `11-robustness.md`, `12-backtest-costs.md`, `16-reporting-audit.md`.

**Mandatory Checks:**
- Decompose signal-to-trade conversion into branches: position-policy blocking (`OPEN_FAILED.reasons.position_or_pending_order_exists`), real broker no-fill (`OPEN_FAILED.reasons.pending_order_not_found_after_order_placed` plus `ORDER_EXPIRED`), and still-unexplained residual (`active_signal_rows - ORDER_PLACED - OPEN_FAILED`).
- Do NOT treat `position_or_pending_order_exists` as a broker refusal; it is the advisor's single-position policy.
- Do NOT call `fill_rate` a "broker fill rate"; the existing field is `trades_count / active_signal_rows`.
- Compare the decomposition with `BS_p05`, trades count, PF, BUY/SELL trade counts, `OPEN_FAILED`, and `ORDER_EXPIRED`.
- Do not infer cause from correlation alone.
- Mark row-level causes as `UNKNOWN` if saved artifacts do not contain stable signal-level linkage.
- If conversion-rate evidence is weak (residual dominates, or position-policy blocking dominates and BS_p05 is still below 1.0 for many eligible candidates with PF > 1.0), reject conversion rate as the primary cause and propose a different next diagnostic that targets trade count and entry mechanics instead.

**Completion Criterion:** there is a written decision: `fill_rate_primary_hypothesis`, `fill_rate_secondary_hypothesis`, or `fill_rate_rejected`, with supporting artifact references.

**Interfaces:**
- Consumes: JSON/CSV artifacts from Task 2.
- Produces: report-ready decision text and tables.

- [ ] **Step 1: Inspect key fields**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd

summary = json.loads(Path("ML/reports/mt5_execution_loop/diagnostics/fill_rate_diagnostics.json").read_text())
table = pd.read_csv("ML/reports/mt5_execution_loop/diagnostics/fill_rate_candidates.csv", sep=";")
cols = ["run_id", "trades_count", "active_signal_rows", "fill_rate", "profit_factor", "bs_p05", "open_failed_count", "order_expired_count"]
print(json.dumps(summary, indent=2, ensure_ascii=False)[:4000])
print(table[cols].sort_values(["bs_p05", "profit_factor"], ascending=[False, False]).head(11).to_string(index=False))
PY
```

Expected: output shows distribution and top 11 rows by existing batch metrics.

- [ ] **Step 2: Compute simple association diagnostics**

Run:

```bash
./.venv/bin/python - <<'PY'
import pandas as pd

table = pd.read_csv("ML/reports/mt5_execution_loop/diagnostics/fill_rate_candidates.csv", sep=";")
numeric = table[["fill_rate", "trades_count", "profit_factor", "bs_p05", "open_failed_count", "order_expired_count"]].apply(pd.to_numeric, errors="coerce")
print(numeric.corr(method="spearman").round(4).to_string())
PY
```

Expected: correlations print successfully. Interpret as diagnostic association only, not causality.

- [ ] **Step 3: Decide status**

Use this rule. The eligibility filter is applied BEFORE the decision: compare `fill_rate_by_status.eligible_top` against the thresholds, not the all-32 distribution, so that 16 `DIAGNOSTIC_ONLY` candidates with `trades_count=0` do not bias the median.

Note: the names refer to the existing `fill_rate` field (`trades_count / active_signal_rows`). It is a signal-to-trade conversion rate, not a broker fill rate.

```text
conversion_position_policy_dominant:
  across eligible_top candidates, the position-policy branch
  (OPEN_FAILED.reasons.position_or_pending_order_exists) accounts for
  >= 80% of OPEN_FAILED events, AND median fill_rate_by_status.eligible_top < 0.20,
  AND there is no eligible candidate whose non-policy OPEN_FAILED and
  ORDER_EXPIRED together exceed the position-policy count.
  -> Findings: the low "fill rate" is mostly the one-position policy, not a
     broker refusal. The probe cannot fix policy by selecting a rule change;
     do NOT raise this above research_hypothesis. The relevant next probe is
     trade-count and entry mechanics, not fill rate.

conversion_broker_no_fill_dominant:
  across eligible_top candidates, non-policy OPEN_FAILED
  (reasons.pending_order_not_found_after_order_placed) plus ORDER_EXPIRED
  together exceed the position-policy branch, AND median fill_rate_by_status.eligible_top < 0.20.
  -> Findings: real no-fill risk exists; report as research_hypothesis only,
     do not raise above DIAGNOSTIC_ONLY.

conversion_residual_dominant:
  median (active_signal_rows - ORDER_PLACED - OPEN_FAILED) across eligible_top
  candidates is >= 10% of median active_signal_rows.
  -> The artifacts cannot explain a large share of the conversion gap;
     report UNKNOWN and propose a row-level linkage probe as next step.

fill_rate_primary_hypothesis (legacy, applies only if none of the three
  decomposition branches above dominates cleanly):
  fill_rate_by_status.eligible_top.median < 0.20
  and fill_rate_by_status.eligible_top.low_fill_rate_count_lt_0_20 >= 8
  and fill_rate_by_status.eligible_top.count >= 6
  and top candidates still fail BS_p05 despite PF > 1.0

fill_rate_secondary_hypothesis:
  conversion rate is low for some eligible candidates, but BS_p05/trade count/
  year/side concentration is not mostly explained by conversion rate,
  and no decomposition branch dominates

fill_rate_rejected:
  fill_rate_by_status.eligible_top.median >= 0.20
  or no material relationship to trade count / BS_p05 / event anomalies
  or conversion_position_policy_dominant AND post-batch BS_p05 failure is
  also explained better by a different cause (e.g., trade count) than by the
  policy branch alone
```

If artifacts do not support one of these statuses, write `UNKNOWN` and state exactly which missing field blocks the decision.

- [ ] **Step 3.1: Record search budget disclosure**

This post-mortem probe touches only saved artifacts. Disclose the total number of diagnostic checks so the decision cannot later look like hidden multiple testing.

```text
total diagnostic checks =
  1 fill-rate probe over 32 saved candidates (32 candidate rows in fill_rate_candidates.csv)
  + 1 Spearman correlation matrix over the same 32 candidate rows
  + 1 decision rule check (median + low_fill_rate_count + top-candidate BS_p05)
  = 2 diagnostic groups, N = 34 total items, 0 new model/search configurations
```

- `N_signal_buckets = 0` (no signal-bucket re-split)
- `N_component_oracle_regimes = 0`
- `N_rule_variants = 0` (no rule variants tried; the single decision rule is fixed before viewing results)
- `N_2d_cells = 0`
- `N_period_feature_contrasts = 0`
- `N_optional_filters = 0`
- `N_negative_controls = 0` (per data-access constraints: no rerun, no permutation over signals)

Allowed max verdict for any output of this probe: `DIAGNOSTIC_ONLY` (or `research_hypothesis` only if the artifacts clearly support it and the user explicitly accepts it). The probe cannot select a winner.

- [ ] **Step 4: Record unknowns**

Include these known possible unknowns unless artifacts prove otherwise:

```text
- No stable per-signal key connects every active signal to ORDER_PLACED, OPEN_FAILED, ORDER_EXPIRED, OPEN, or CLOSE.
- Error/event row linkage remains UNKNOWN.
- Missing local ignored metrics.json files may reduce gross/loss or close-reason detail.
- Cost stress was not run and cannot be inferred from fill rate.
```

- [ ] **Step 5: Commit if any analysis helper was added**

If Task 3 changed code or added an artifact beyond Task 2, run:

```bash
git add ML/baseline/mt5_execution_diagnostics.py tests/test_mt5_execution_diagnostics.py ML/reports/mt5_execution_loop/diagnostics/
git commit -m "docs: decide mt5 fill rate hypothesis"
```

If no files changed, skip this commit.

---

### Task 4: Report And Project State Sync

**Files:**
- Create: `docs/reports/2026-08-01-mt5-saved-batch-fill-rate-probe.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/superpowers/roadmap.md`

**Applicable Methodology:** `00-research-management.md`, `16-reporting-audit.md`.

**Mandatory Checks:**
- Report contains stage level, search budget, commands, changed files, verification, results, conclusions, limitations, split disclosure, forbidden interpretations, and next step.
- Key numbers in the report match `fill_rate_diagnostics.json` and `fill_rate_candidates.csv`.
- Roadmap keeps only one `ACTIVE` track and removes completed fill-rate work after the report is closed.
- Handoff points to the next exact action.

**Completion Criterion:** documentation is synchronized and the next stage is explicit.

**Interfaces:**
- Consumes: artifacts and decision from Tasks 2-3.
- Produces: final report and updated project state.

- [ ] **Step 1: Draft report**

Create `docs/reports/2026-08-01-mt5-saved-batch-fill-rate-probe.md` with this structure:

```markdown
# MT5 Saved-Batch Fill-Rate Probe

> **Дата**: 2026-08-01
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: разложить signal-to-trade conversion rate по ветвям отсева (позиционный запрет, настоящий broker no-fill, необъяснённый остаток) по сохранённым артефактам MT5 batch без нового выбора winner.
> **Related plan**: `docs/superpowers/plans/2026-08-01-mt5-saved-batch-fill-rate-probe.md`

## Stage Level

Search/post-mortem diagnostic stage. This report does not create a candidate and cannot raise verdict above `DIAGNOSTIC_ONLY`.

## Research-first disclosure

- **lifecycle_status**: DIAGNOSTIC_ONLY
- **origin_bias**: post-mortem after `BATCH_NO_WINNER`
- **research_priority**: [fill from Task 3]
- **current_search_budget**: 0 new model/search configurations; 2 diagnostic groups over saved batch artifacts (1 fill-rate probe over 32 candidates + 1 Spearman correlation matrix + 1 fixed decision rule check; N=34 total items)
- **cumulative_search_budget**: inherited from 2026-07-31 batch and 2026-08-01 MT5 diagnostics
- **next_probe_freeze**: [fill from Task 3]
- **allowed_max_verdict**: DIAGNOSTIC_ONLY
- **forbidden_interpretations**: profitable, ready, live-ready, tradable, new winner, model-quality proof

## Context

[Summarize current batch facts and why fill-rate was checked.]

## Methodology

[List applied methodology files and mandatory checks.]

## What Was Done

[Commands from Tasks 2-3.]

## Changed Files

[List changed files.]

## Structured Artifact Cross-Check

[Copy key numbers from JSON/CSV and cite exact artifact paths.]

## Results

[Diagnostic facts only.]

## Conclusions

[Decision from Task 3: primary / secondary / rejected / UNKNOWN.]

## Limitations / Open Questions

[Unknowns from Task 3.]

## Split Disclosure

Validation batch only: XAUUSD H1 2021-01-04..2022-12-02. `locked_test` was not opened.

## Forbidden Interpretations

Do not treat this report as a new winner selection or as evidence that any candidate is tradable.

## Next Step

[One exact next action.]

## Related Materials

- `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md`
- `docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md`
- `ML/reports/mt5_execution_loop/diagnostics/fill_rate_diagnostics.json`
- `ML/reports/mt5_execution_loop/diagnostics/fill_rate_candidates.csv`
```

- [ ] **Step 2: Update project state**

Update:

```text
CHANGELOG.md
CONTEXT_HANDOFF.md
docs/superpowers/roadmap.md
```

Use these rules:

```text
CHANGELOG.md: add one top entry with report path, verdict, and decision.
CONTEXT_HANDOFF.md: replace active task with the next exact action from the report.
roadmap.md: remove completed fill-rate probe from ACTIVE; set the next ACTIVE track only if the report identifies one.
```

- [ ] **Step 3: Verify report numbers against artifacts**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd

report = Path("docs/reports/2026-08-01-mt5-saved-batch-fill-rate-probe.md").read_text(encoding="utf-8")
summary = json.loads(Path("ML/reports/mt5_execution_loop/diagnostics/fill_rate_diagnostics.json").read_text())
table = pd.read_csv("ML/reports/mt5_execution_loop/diagnostics/fill_rate_candidates.csv", sep=";")

required = [
    str(summary["candidate_count"]),
    str(summary["verdict"]),
    "DIAGNOSTIC_ONLY",
    "locked_test was not opened",
]
missing = [value for value in required if value not in report]
assert not missing, missing
assert len(table) == summary["candidate_count"]
print("report_artifact_crosscheck_ok")
PY
```

Expected: prints `report_artifact_crosscheck_ok`.

- [ ] **Step 4: Run final checks**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py tests/test_parse_mt5_execution_report.py tests/test_mt5_signal_executor_schema.py tests/test_mt5_batch_runtime_contract.py -q
git diff --check
git status --short
```

Expected:

- focused tests PASS;
- `git diff --check` PASS;
- `git status --short` shows only intended files.

- [ ] **Step 5: Commit task**

Run:

```bash
git add docs/reports/2026-08-01-mt5-saved-batch-fill-rate-probe.md CHANGELOG.md CONTEXT_HANDOFF.md docs/superpowers/roadmap.md
git commit -m "docs: report mt5 fill rate probe"
```

---

## Final Verification

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py tests/test_parse_mt5_execution_report.py tests/test_mt5_signal_executor_schema.py tests/test_mt5_batch_runtime_contract.py -q
./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics \
  --phase fill-rate \
  --output-json ML/reports/mt5_execution_loop/diagnostics/fill_rate_diagnostics.json \
  --output-csv ML/reports/mt5_execution_loop/diagnostics/fill_rate_candidates.csv
git diff --check
```

Expected:

- focused tests PASS;
- diagnostic CLI exits `0`;
- `fill_rate_diagnostics.json` has `status=DIAGNOSTIC_ONLY`, `verdict=BATCH_NO_WINNER`, `candidate_count=32`;
- `fill_rate_candidates.csv` has 32 candidate rows;
- whitespace check PASS.

Do not run full project `pytest tests/ -q` as the required gate for this plan unless the user asks. The known unrelated failure remains: `tests/test_mql_telemetry_params_csv_contract.py::test_tester_ini_selects_telemetry_backtest_row` expects `BackTest=2`, while `MT/tester/$o$imple.ini` currently has `BackTest=0`.

## Self-Review Checklist

- Spec coverage: plan covers fill-rate diagnostics over saved artifacts, methodology mapping, checks, report, and project-state sync.
- Implementation gap documented: the `fill-rate` CLI phase and `build_fill_rate_diagnostics` / `summarize_candidate_fill_rate` / `count_event_names` functions do not exist in `ML/baseline/mt5_execution_diagnostics.py` yet. Adding them is the explicit goal of Tasks 1–2; the plan states "no TBD/TODO" relative to planned work, not relative to existing code.
- Placeholder scan: no `TBD`, `TODO`, "implement later", or unspecified tests in the planned work.
- Type consistency: produced functions and CLI phase names are consistent across tasks.
- Scope guard: no MT5 rerun, no `locked_test`, no model/rule selection, no trading verdict.
- Sample size gate: this is a `DIAGNOSTIC_ONLY` post-mortem probe over already saved batch artifacts, not a model/selection run, so the numeric `min_trades_total` / `min_trades_per_year` gates from `00-research-management.md` apply to eligibility rather than to this probe. The probe discloses sample size per candidate (`active_signal_rows`, `trades_count`) and reports `fill_rate_distribution` separately for eligible top candidates vs diagnostic-only candidates (see `fill_rate_by_status` in Task 1). If fewer than 11 eligible candidates have a non-null `fill_rate`, the Task 3 decision falls back to `UNKNOWN` rather than `fill_rate_primary_hypothesis`.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-01-mt5-saved-batch-fill-rate-probe.md`. Two execution options:

1. Subagent-Driven (recommended) - dispatch a fresh subagent per task, review between tasks, faster iteration.
2. Inline Execution - execute tasks in this session using `executing-plans`, batch execution with checkpoints.

Which approach?
