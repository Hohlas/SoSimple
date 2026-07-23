from __future__ import annotations

# =============================================================================
# Файл: audit_leaderboard_closure.py
# Назначение: Closure audit for 11 fixed normalized leaderboard rows.
# Обновлен: 2026-07-23
# Зависимости:
#   Входные данные:
#     - ML/reports/fractal0_rich_entry_quality_normalized.json/csv
#   Выходные данные:
#     - ML/reports/leaderboard_closure_audit*.json/csv
# Использование:
#   ./.venv/bin/python ML/baseline/audit_leaderboard_closure.py --input-prefix ML/reports/fractal0_rich_entry_quality_normalized --output-prefix ML/reports/leaderboard_closure_audit
# Примечания:
#   - locked_test не открывается; provider drift и transfer не входят в scope.
# =============================================================================

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ML.baseline import audit_leaderboard_robustness as leaderboard
from ML.baseline import benchmark_fractal0_entry_exit_grid as entry_exit


DEFAULT_INPUT_PREFIX = leaderboard.DEFAULT_INPUT_PREFIX
CLOSURE_OUTPUT_PREFIX = Path("ML/reports/leaderboard_closure_audit")
CLOSURE_SCOPE = "validation_artifact_leaderboard_cost_calendar_sequential_multiseed_closure"
LEADERBOARD_RULES = leaderboard.LEADERBOARD_RULES
verify_leaderboard_contract = leaderboard.verify_leaderboard_contract

STRESS_MULTIPLIERS = (1.0, 2.0, 3.0, 4.0)
CANONICAL_SPREAD = leaderboard.CANONICAL_SPREAD
TIMEZONE_SHIFT_HOURS = (-8, -4, 4, 8)
POSITION_POLICIES = {"single_position": 1, "max_positions_2": 2, "max_positions_3": 3}
MULTISEED_SEEDS = (41, 42, 43, 44, 45)
CALENDAR_MIN_TRADES_FOR_STABILITY = 30


def default_closure_statuses() -> dict[str, object]:
    return {
        "locked_test_status": "not_opened",
        "stress_costs_status": "PENDING",
        "time_calendar_status": "PENDING",
        "timezone_shift_status": "PENDING",
        "sequential_position_constraint_status": "PENDING",
        "multi_seed_status": "PENDING",
        "provider_drift_status": "NOT_IN_SCOPE",
        "transfer_status": "NOT_IN_SCOPE",
        "allowed_max_verdict": "research_only",
    }


def verify_closure_inputs(input_prefix: Path = DEFAULT_INPUT_PREFIX) -> dict[str, object]:
    loaded = leaderboard.load_normalized_artifacts(input_prefix)
    global_contract = leaderboard.verify_global_artifact_contract(loaded["artifact"])
    rule_contract = leaderboard.verify_leaderboard_contract(loaded["summary"], LEADERBOARD_RULES)
    return {"loaded": loaded, "global_contract": global_contract, "rule_contract": rule_contract}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def input_artifacts_for_prefix(input_prefix: Path) -> dict[str, dict[str, object]]:
    paths = {
        "artifact_json": input_prefix.with_suffix(".json"),
        "summary_csv": input_prefix.with_name(input_prefix.name + "_summary.csv"),
        "trades_csv": input_prefix.with_name(input_prefix.name + "_trades.csv"),
        "scores_csv": input_prefix.with_name(input_prefix.name + "_scores.csv"),
    }
    return {
        key: {
            "path": str(path),
            "sha256": _sha256_file(path),
            "size_bytes": int(path.stat().st_size),
        }
        for key, path in paths.items()
    }


def _row_dict(contract_row: pd.Series | dict[str, object]) -> dict[str, object]:
    return contract_row.to_dict() if isinstance(contract_row, pd.Series) else dict(contract_row)


def stress_cost_grid_for_rule(trades: pd.DataFrame, contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = _row_dict(contract_row)
    records = []
    for multiplier in STRESS_MULTIPLIERS:
        records.append(
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": str(row["rule_id"]),
                "cost_component": "spread",
                "spread": float(CANONICAL_SPREAD * multiplier),
                "stress_multiplier": float(multiplier),
                "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
                "n_trades": int(len(trades)),
                "pf": None,
                "mean_pnl_r": None,
                "max_drawdown_r": None,
                "reason": "saved filtered trades contain realized pnl only; stress spread requires explicit resimulation from producer execution artifacts",
            }
        )
    return pd.DataFrame(records)


def cost_model_disclosure_for_rule(contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = _row_dict(contract_row)
    records = []
    components = ["spread", "commission", "swap", "slippage", "requote_open_failure", "latency", "next_bar_entry", "position_limits"]
    for component in components:
        records.append(
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": str(row["rule_id"]),
                "cost_component": component,
                "status": "DISCLOSED_BASELINE" if component == "spread" else "NOT_IN_SCOPE",
                "reason": "canonical spread is inherited from saved artifact"
                if component == "spread"
                else "this closure records non-spread cost disclosure; concrete values require a separate execution-cost model source",
            }
        )
    return pd.DataFrame(records)


def _calendar_values(frame: pd.DataFrame, time_column: str) -> pd.DataFrame:
    out = frame.copy()
    dt = pd.to_datetime(out[time_column], errors="coerce")
    out["_year"] = dt.dt.year
    out["_quarter"] = dt.dt.to_period("Q").astype(str)
    out["_month"] = dt.dt.month
    out["_weekday"] = dt.dt.weekday
    out["_hour"] = dt.dt.hour
    return out


def time_calendar_for_rule(trades: pd.DataFrame, contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = _row_dict(contract_row)
    records = []
    for time_basis in ["signal_time", "fill_time", "exit_time"]:
        if time_basis not in trades.columns:
            records.append(
                {
                    "original_rank": int(row["original_rank"]),
                    "rule_id": str(row["rule_id"]),
                    "time_basis": time_basis,
                    "calendar_field": "missing",
                    "calendar_value": None,
                    "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
                    "reason": f"{time_basis} missing from saved trades",
                }
            )
            continue
        frame = _calendar_values(trades, time_basis)
        for field in ["year", "quarter", "month", "weekday", "hour"]:
            column = f"_{field}"
            for value, group in frame.groupby(column, dropna=False):
                metrics = entry_exit.compute_trade_metrics(group)
                n_trades = int(metrics["n_trades"])
                records.append(
                    {
                        "original_rank": int(row["original_rank"]),
                        "rule_id": str(row["rule_id"]),
                        "time_basis": time_basis,
                        "calendar_field": field,
                        "calendar_value": str(value),
                        "status": "COMPUTED",
                        "n_trades_gate_status": "LOW_N_LT_30" if n_trades < CALENDAR_MIN_TRADES_FOR_STABILITY else "PASS",
                        "low_n_calendar_slice": n_trades < CALENDAR_MIN_TRADES_FOR_STABILITY,
                        **metrics,
                    }
                )
    return pd.DataFrame(records)


def calendar_permutation_importance_for_rule(artifact: dict[str, object], contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = _row_dict(contract_row)
    return pd.DataFrame(
        [
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": str(row["rule_id"]),
                "diagnostic": "calendar_permutation_importance",
                "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
                "reason": "fitted estimator and frozen rescore path are not persisted in saved normalized artifacts",
            }
        ]
    )


def calendar_no_ml_baseline_for_rule(trades: pd.DataFrame, contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = _row_dict(contract_row)
    return pd.DataFrame(
        [
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": str(row["rule_id"]),
                "diagnostic": "calendar_no_ml_baseline",
                "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
                "reason": "saved filtered leaderboard trades do not include unfiltered no-ML calendar baseline rows",
                "rows_available": int(len(trades)),
            }
        ]
    )


def timezone_shift_for_rule(scores: pd.DataFrame, contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = _row_dict(contract_row)
    return pd.DataFrame(
        [
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": str(row["rule_id"]),
                "shift_hours": int(shift),
                "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
                "reason": "timezone-shift check requires frozen rescore of time features; saved scores cannot be shifted honestly",
                "rows_available": int(len(scores)),
            }
            for shift in TIMEZONE_SHIFT_HOURS
        ]
    )


def _select_non_overlapping(trades: pd.DataFrame, max_positions: int) -> pd.DataFrame:
    frame = trades.copy()
    frame["_signal_dt"] = pd.to_datetime(frame["signal_time"], errors="coerce")
    frame["_fill_dt"] = pd.to_datetime(frame["fill_time"], errors="coerce")
    frame["_exit_dt"] = pd.to_datetime(frame["exit_time"], errors="coerce")
    frame["_fill_dt"] = frame["_fill_dt"].fillna(frame["_signal_dt"])
    frame = frame.sort_values(["_fill_dt", "_signal_dt", "_exit_dt", "position_id"], kind="mergesort")
    active_exits: list[pd.Timestamp] = []
    keep_indices = []
    for idx, row in frame.iterrows():
        fill_dt = row["_fill_dt"]
        active_exits = [exit_dt for exit_dt in active_exits if pd.notna(exit_dt) and exit_dt > fill_dt]
        if len(active_exits) < max_positions:
            keep_indices.append(idx)
            active_exits.append(row["_exit_dt"])
    return trades.loc[keep_indices].copy()


def sequential_positions_for_rule(trades: pd.DataFrame, contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = _row_dict(contract_row)
    required_base = {"signal_time", "exit_time", "position_id", "pnl_r"}
    records = []
    for policy, max_positions in POSITION_POLICIES.items():
        if not required_base.issubset(set(trades.columns)):
            records.append(
                {
                    "original_rank": int(row["original_rank"]),
                    "rule_id": str(row["rule_id"]),
                    "position_policy": policy,
                    "max_positions": int(max_positions),
                    "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
                    "n_trades": 0,
                    "dropped_trades": None,
                    "reason": "signal_time, fill_time, exit_time, position_id and pnl_r are required; position interval starts at fill_time",
                }
            )
            continue
        has_fill_time = "fill_time" in trades.columns
        frame = trades.copy()
        if not has_fill_time:
            frame["fill_time"] = frame["signal_time"]
        selected = _select_non_overlapping(frame, max_positions)
        interval_basis = "fill_time" if has_fill_time else "signal_time_fallback"
        records.append(
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": str(row["rule_id"]),
                "position_policy": policy,
                "max_positions": int(max_positions),
                "interval_basis": interval_basis,
                "status": "COMPUTED" if has_fill_time else "COMPUTED_WITH_SIGNAL_TIME_FALLBACK",
                "dropped_trades": int(len(trades) - len(selected)),
                "reason": "" if has_fill_time else "fill_time missing from saved trades; used signal_time as conservative fallback",
                **entry_exit.compute_trade_metrics(selected),
            }
        )
    return pd.DataFrame(records)


def bounded_multiseed_rerun_contract() -> dict[str, object]:
    return {
        "seeds": [int(seed) for seed in MULTISEED_SEEDS],
        "rule_count": len(LEADERBOARD_RULES),
        "rule_ids": [rule.rule_id for rule in LEADERBOARD_RULES],
        "new_search_allowed": False,
        "locked_test": "not_opened",
        "fixed_universe": "same 11 LEADERBOARD_RULES, same profiles/models/targets/filters, saved val_select cutoff only",
        "required_outputs": [
            "per_seed_summary_csv",
            "per_seed_trades_csv",
            "per_seed_scores_csv",
            "per_rule_seed_aggregate_csv",
        ],
    }


def multiseed_for_rule(artifact: dict[str, object], contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = _row_dict(contract_row)
    seed_artifacts = artifact.get("multiseed_artifacts") if isinstance(artifact, dict) else None
    if not isinstance(seed_artifacts, dict):
        return pd.DataFrame(
            [
                {
                    "original_rank": int(row["original_rank"]),
                    "rule_id": str(row["rule_id"]),
                    "seed": int(seed),
                    "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
                    "pf": None,
                    "bs_p05": None,
                    "n_trades": None,
                    "reason": "persisted per-seed artifacts are absent; rerun must be explicitly bounded to the same 11 fixed rule families",
                }
                for seed in MULTISEED_SEEDS
            ]
        )
    records = []
    for seed in MULTISEED_SEEDS:
        seed_key = str(seed)
        seed_row = seed_artifacts.get(seed_key)
        if not isinstance(seed_row, dict):
            records.append(
                {
                    "original_rank": int(row["original_rank"]),
                    "rule_id": str(row["rule_id"]),
                    "seed": int(seed),
                    "status": "MISSING_SEED_ARTIFACT",
                    "pf": None,
                    "bs_p05": None,
                    "n_trades": None,
                    "reason": f"missing persisted seed artifact {seed_key}",
                }
            )
            continue
        records.append(
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": str(row["rule_id"]),
                "seed": int(seed),
                "status": "LOADED",
                "pf": seed_row.get("pf"),
                "bs_p05": seed_row.get("bs_p05"),
                "n_trades": seed_row.get("n_trades"),
                "reason": "",
            }
        )
    return pd.DataFrame(records)


def _concat(frames: list[pd.DataFrame]) -> pd.DataFrame:
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _statuses_for_rule(rule_id: str, frame: pd.DataFrame) -> set[str]:
    if frame.empty or "rule_id" not in frame.columns or "status" not in frame.columns:
        return {"UNKNOWN"}
    values = set(frame.loc[frame["rule_id"].astype(str).eq(rule_id), "status"].astype(str))
    return values if values else {"MISSING_DIAGNOSTIC_ROW"}


def build_closure_classification(
    rules: pd.DataFrame,
    stress: pd.DataFrame,
    calendar: pd.DataFrame,
    calendar_permutation: pd.DataFrame,
    calendar_no_ml: pd.DataFrame,
    timezone: pd.DataFrame,
    sequential: pd.DataFrame,
    multiseed: pd.DataFrame,
) -> pd.DataFrame:
    records = []
    for _, row in rules.sort_values("original_rank").iterrows():
        rule_id = str(row["rule_id"])
        reasons = []
        disclosures = []
        if "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS" in _statuses_for_rule(rule_id, stress):
            reasons.append("stress_costs_not_computable")
        if _statuses_for_rule(rule_id, stress) & {"MISSING_DIAGNOSTIC_ROW", "UNKNOWN"}:
            reasons.append("stress_costs_missing")
        if "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS" in _statuses_for_rule(rule_id, calendar_permutation):
            disclosures.append("calendar_permutation_importance_not_computable")
        if "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS" in _statuses_for_rule(rule_id, calendar_no_ml):
            disclosures.append("calendar_no_ml_baseline_not_computable")
        if _statuses_for_rule(rule_id, calendar) & {"MISSING_DIAGNOSTIC_ROW", "UNKNOWN"}:
            disclosures.append("time_calendar_missing")
        if "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS" in _statuses_for_rule(rule_id, timezone):
            disclosures.append("timezone_shift_not_computable")
        if "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS" in _statuses_for_rule(rule_id, multiseed):
            disclosures.append("multi_seed_not_computable")
        if _statuses_for_rule(rule_id, sequential) & {"MISSING_DIAGNOSTIC_ROW", "UNKNOWN"}:
            disclosures.append("sequential_position_missing")
        elif "COMPUTED" not in _statuses_for_rule(rule_id, sequential):
            disclosures.append("sequential_position_not_computed")
        decision = "CLOSURE_INCOMPLETE" if reasons or disclosures else "CLOSURE_DIAGNOSTICS_COMPUTED_RESEARCH_ONLY"
        records.append(
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": rule_id,
                "decision": decision,
                "reasons": ",".join(reasons),
                "disclosures": ",".join(disclosures),
                "allowed_max_verdict": "research_only",
                "new_winner_selected": False,
            }
        )
    return pd.DataFrame(records)


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, sep=";", index=False)


def _count_status(frame: pd.DataFrame, column: str, value: object) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].eq(value).sum())


def run_closure(input_prefix: Path = DEFAULT_INPUT_PREFIX, output_prefix: Path = CLOSURE_OUTPUT_PREFIX) -> dict[str, object]:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    try:
        verified = verify_closure_inputs(input_prefix)
    except leaderboard.LeaderboardAuditError as exc:
        result = {
            "experiment": "leaderboard_closure_audit",
            "status": "UNKNOWN",
            "run_status": "failed",
            "decision": getattr(exc, "decision", "UNKNOWN_INPUT_OR_CONTRACT"),
            "locked_test": "not_opened",
            "locked_test_status": "not_opened",
            "error": str(exc),
        }
        output_prefix.with_suffix(".json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return result
    except Exception as exc:
        result = {
            "experiment": "leaderboard_closure_audit",
            "status": "UNKNOWN",
            "run_status": "failed",
            "decision": "UNKNOWN_INPUT_OR_CONTRACT",
            "locked_test": "not_opened",
            "locked_test_status": "not_opened",
            "error": str(exc),
        }
        output_prefix.with_suffix(".json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return result

    loaded = verified["loaded"]
    artifact = loaded["artifact"]
    trades = loaded["trades"]
    scores = loaded["scores"]
    rules = verified["rule_contract"]
    stress_frames = []
    cost_disclosure_frames = []
    calendar_frames = []
    calendar_permutation_frames = []
    calendar_no_ml_frames = []
    timezone_frames = []
    sequential_frames = []
    multiseed_frames = []
    for _, contract_row in rules.iterrows():
        fixed_rule = leaderboard.fixed_rule_from_contract_row(contract_row)
        fixed_trades = leaderboard.base_audit.filter_fixed_rule_rows(trades, fixed_rule, split="val_eval")
        fixed_scores = leaderboard.base_audit.filter_fixed_rule_rows(scores, fixed_rule)
        stress_frames.append(stress_cost_grid_for_rule(fixed_trades, contract_row))
        cost_disclosure_frames.append(cost_model_disclosure_for_rule(contract_row))
        calendar_frames.append(time_calendar_for_rule(fixed_trades, contract_row))
        calendar_permutation_frames.append(calendar_permutation_importance_for_rule(artifact, contract_row))
        calendar_no_ml_frames.append(calendar_no_ml_baseline_for_rule(fixed_trades, contract_row))
        timezone_frames.append(timezone_shift_for_rule(fixed_scores, contract_row))
        sequential_frames.append(sequential_positions_for_rule(fixed_trades, contract_row))
        multiseed_frames.append(multiseed_for_rule(artifact, contract_row))

    stress = _concat(stress_frames)
    cost_disclosure = _concat(cost_disclosure_frames)
    calendar = _concat(calendar_frames)
    calendar_permutation = _concat(calendar_permutation_frames)
    calendar_no_ml = _concat(calendar_no_ml_frames)
    timezone = _concat(timezone_frames)
    sequential = _concat(sequential_frames)
    multiseed = _concat(multiseed_frames)
    classification = build_closure_classification(
        rules,
        stress,
        calendar,
        calendar_permutation,
        calendar_no_ml,
        timezone,
        sequential,
        multiseed,
    )
    artifacts = {
        "rules_csv": output_prefix.with_name(output_prefix.name + "_rules.csv"),
        "stress_cost_csv": output_prefix.with_name(output_prefix.name + "_stress_cost.csv"),
        "cost_model_disclosure_csv": output_prefix.with_name(output_prefix.name + "_cost_model_disclosure.csv"),
        "calendar_csv": output_prefix.with_name(output_prefix.name + "_calendar.csv"),
        "calendar_permutation_importance_csv": output_prefix.with_name(output_prefix.name + "_calendar_permutation_importance.csv"),
        "calendar_no_ml_baselines_csv": output_prefix.with_name(output_prefix.name + "_calendar_no_ml_baselines.csv"),
        "timezone_shift_csv": output_prefix.with_name(output_prefix.name + "_timezone_shift.csv"),
        "sequential_positions_csv": output_prefix.with_name(output_prefix.name + "_sequential_positions.csv"),
        "multiseed_csv": output_prefix.with_name(output_prefix.name + "_multiseed.csv"),
        "classification_csv": output_prefix.with_name(output_prefix.name + "_classification.csv"),
    }
    for frame, path in [
        (rules, artifacts["rules_csv"]),
        (stress, artifacts["stress_cost_csv"]),
        (cost_disclosure, artifacts["cost_model_disclosure_csv"]),
        (calendar, artifacts["calendar_csv"]),
        (calendar_permutation, artifacts["calendar_permutation_importance_csv"]),
        (calendar_no_ml, artifacts["calendar_no_ml_baselines_csv"]),
        (timezone, artifacts["timezone_shift_csv"]),
        (sequential, artifacts["sequential_positions_csv"]),
        (multiseed, artifacts["multiseed_csv"]),
        (classification, artifacts["classification_csv"]),
    ]:
        _write_csv(frame, path)
    result = {
        "experiment": "leaderboard_closure_audit",
        "status": "completed",
        "run_status": "completed",
        "verdict": "research_only",
        "locked_test": "not_opened",
        "scope": CLOSURE_SCOPE,
        "leaderboard_rule_count": int(len(rules)),
        "input_artifacts": input_artifacts_for_prefix(input_prefix),
        **default_closure_statuses(),
        "stress_costs_status": ",".join(sorted(set(stress["status"].astype(str)))) if not stress.empty else "UNKNOWN",
        "cost_model_disclosure_status": ",".join(sorted(set(cost_disclosure["status"].astype(str)))) if not cost_disclosure.empty else "UNKNOWN",
        "time_calendar_status": ",".join(sorted(set(calendar["status"].astype(str)))) if not calendar.empty else "UNKNOWN",
        "calendar_permutation_importance_status": ",".join(sorted(set(calendar_permutation["status"].astype(str)))) if not calendar_permutation.empty else "UNKNOWN",
        "calendar_no_ml_baseline_status": ",".join(sorted(set(calendar_no_ml["status"].astype(str)))) if not calendar_no_ml.empty else "UNKNOWN",
        "timezone_shift_status": ",".join(sorted(set(timezone["status"].astype(str)))) if not timezone.empty else "UNKNOWN",
        "sequential_position_constraint_status": ",".join(sorted(set(sequential["status"].astype(str)))) if not sequential.empty else "UNKNOWN",
        "multi_seed_status": ",".join(sorted(set(multiseed["status"].astype(str)))) if not multiseed.empty else "UNKNOWN",
        "calendar_low_n_slice_count_lt_30": _count_status(calendar, "low_n_calendar_slice", True),
        "calendar_low_n_slice_count_lt_10": int(calendar.loc[pd.to_numeric(calendar.get("n_trades", pd.Series(dtype=float)), errors="coerce").lt(10)].shape[0])
        if not calendar.empty and "n_trades" in calendar.columns
        else 0,
        "calendar_n_trades_gate_status": "LOW_N_DIAGNOSTIC_ONLY" if _count_status(calendar, "low_n_calendar_slice", True) else "PASS",
        "overall_decision": "LEADERBOARD_CLOSURE_INCOMPLETE_RESEARCH_ONLY"
        if "CLOSURE_INCOMPLETE" in set(classification["decision"].astype(str))
        else "LEADERBOARD_CLOSURE_DIAGNOSTICS_COMPUTED_RESEARCH_ONLY",
        "bounded_multiseed_rerun_contract": bounded_multiseed_rerun_contract(),
        "artifacts": {key: str(value) for key, value in artifacts.items()},
    }
    output_prefix.with_suffix(".json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Closure audit for fixed normalized leaderboard rows.")
    parser.add_argument("--input-prefix", default=str(DEFAULT_INPUT_PREFIX))
    parser.add_argument("--output-prefix", default=str(CLOSURE_OUTPUT_PREFIX))
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    result = run_closure(Path(args.input_prefix), Path(args.output_prefix))
    print(json.dumps({"status": result["status"], "overall_decision": result.get("overall_decision")}, ensure_ascii=False))
    if result.get("status") == "UNKNOWN":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
