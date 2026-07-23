from __future__ import annotations

# =============================================================================
# Файл: audit_leaderboard_robustness.py
# Назначение: Validation-slice audit 11 fixed normalized rich-entry leaderboard rows.
# Обновлён: 2026-07-23
# Зависимости:
#   Входные данные:
#     - ML/reports/fractal0_rich_entry_quality_normalized.json/csv
#   Выходные данные:
#     - ML/reports/leaderboard_robustness_audit*.json/csv
# Использование:
#   ./.venv/bin/python ML/baseline/audit_leaderboard_robustness.py --input-prefix ML/reports/fractal0_rich_entry_quality_normalized --output-prefix ML/reports/leaderboard_robustness_audit
# Примечания:
#   - locked_test не открывается; результат не выше research_only.
# =============================================================================

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ML.baseline import audit_time_only_robustness as base_audit


DEFAULT_INPUT_PREFIX = Path("ML/reports/fractal0_rich_entry_quality_normalized")
DEFAULT_OUTPUT_PREFIX = Path("ML/reports/leaderboard_robustness_audit")

STOP_POLICY_ID = "S2_fractal0_buffer_0_5_entry_floor_2"
ENTRY_ID = "E3_open_pullback_1_0atr"
MASK_ID = "M0_no_mask"
EXIT_ID = "X2_ml_opposite_any_p0_50"
CANONICAL_SPREAD = 0.2
ENTRY_FILTER_SCORE_COL = "rich_entry_score"


class LeaderboardAuditError(ValueError):
    decision = "UNKNOWN"


class GlobalArtifactContractError(LeaderboardAuditError):
    decision = "UNKNOWN_ARTIFACT_CONTRACT"


class LeaderboardContractError(LeaderboardAuditError):
    decision = "UNKNOWN_LEADERBOARD_CONTRACT"


@dataclass(frozen=True)
class RuleSpec:
    original_rank: int
    profile_id: str
    model_id: str
    target_id: str
    filter_id: str

    @property
    def rule_id(self) -> str:
        return f"rank{self.original_rank:02d}_{self.profile_id}_{self.model_id}_{self.target_id}_{self.filter_id}"


LEADERBOARD_RULES: tuple[RuleSpec, ...] = (
    RuleSpec(1, "time_only", "linear", "target_entry_ev_regression", "top30"),
    RuleSpec(2, "time_only", "linear", "target_entry_ev_regression", "top40"),
    RuleSpec(3, "time_only", "linear", "target_entry_ev_regression", "top50"),
    RuleSpec(4, "time_only", "linear", "target_entry_good_0_5r", "top40"),
    RuleSpec(5, "time_only", "linear", "target_entry_avoid_sl", "top30"),
    RuleSpec(6, "time_only", "linear", "target_entry_good_0_5r", "top50"),
    RuleSpec(7, "movement_plus_time", "linear", "target_entry_good_0_5r", "top40"),
    RuleSpec(8, "movement_plus_time", "linear", "target_entry_good_0_5r", "top30"),
    RuleSpec(9, "time_only", "hist_gradient_boosting", "target_entry_good_0_5r", "top50"),
    RuleSpec(10, "movement_plus_time", "linear", "target_entry_ev_regression", "top50"),
    RuleSpec(11, "movement_plus_time", "linear", "target_entry_good_0_5r", "top50"),
)


def _float_matches(value: object, expected: float) -> bool:
    try:
        return math.isclose(float(value), expected, rel_tol=0.0, abs_tol=1e-12)
    except (TypeError, ValueError):
        return False


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def verify_global_artifact_contract(artifact: dict[str, object]) -> dict[str, object]:
    checks = {
        "locked_test": artifact.get("locked_test") == "not_opened",
        "feature_contract_variant": artifact.get("feature_contract_variant") == "normalized_atr_unit",
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise GlobalArtifactContractError(f"global artifact contract failed: {failed}")
    return {"status": "PASS", "checks": checks}


def _summary_rows_for_rule(summary: pd.DataFrame, rule: RuleSpec, split: str) -> pd.DataFrame:
    mask = (
        summary["stop_policy_id"].astype(str).eq(STOP_POLICY_ID)
        & summary["entry_id"].astype(str).eq(ENTRY_ID)
        & summary["mask_id"].astype(str).eq(MASK_ID)
        & summary["exit_id"].astype(str).eq(EXIT_ID)
        & pd.to_numeric(summary["spread"], errors="coerce").eq(CANONICAL_SPREAD)
        & summary["split"].astype(str).eq(split)
        & summary["profile_id"].astype(str).eq(rule.profile_id)
        & summary["model_id"].astype(str).eq(rule.model_id)
        & summary["target_id"].astype(str).eq(rule.target_id)
        & summary["filter_id"].astype(str).eq(rule.filter_id)
        & summary["entry_filter_score_col"].astype(str).eq(ENTRY_FILTER_SCORE_COL)
    )
    return summary.loc[mask].copy()


def verify_leaderboard_contract(summary: pd.DataFrame, rules: tuple[RuleSpec, ...] = LEADERBOARD_RULES) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for rule in rules:
        val_select = _summary_rows_for_rule(summary, rule, "val_select")
        val_eval = _summary_rows_for_rule(summary, rule, "val_eval")
        if len(val_select) != 1 or len(val_eval) != 1:
            raise LeaderboardContractError(
                f"missing leaderboard summary row for {rule.rule_id}: "
                f"val_select={len(val_select)}, val_eval={len(val_eval)}"
            )
        selected = val_select.iloc[0].to_dict()
        evaluated = val_eval.iloc[0].to_dict()
        if not _as_bool(selected.get("eligible_for_winner")) or _as_bool(selected.get("not_eligible_for_winner")):
            raise LeaderboardContractError(f"leaderboard row is not source-eligible: {rule.rule_id}")
        if not _as_bool(evaluated.get("eligible_for_winner")) or _as_bool(evaluated.get("not_eligible_for_winner")):
            raise LeaderboardContractError(f"leaderboard val_eval row is not source-eligible: {rule.rule_id}")
        rows.append(
            {
                "original_rank": rule.original_rank,
                "rule_id": rule.rule_id,
                "profile_id": rule.profile_id,
                "model_id": rule.model_id,
                "target_id": rule.target_id,
                "filter_id": rule.filter_id,
                "score_cutoff_on_val_select": float(selected["score_cutoff_on_val_select"]),
                "val_select_n_trades": int(selected["n_trades"]),
                "val_eval_n_trades": int(evaluated["n_trades"]),
                "val_eval_pf": float(evaluated["pf"]),
                "val_eval_bs_p05_source": float(evaluated["bs_p05"]),
                "contract_status": "PASS",
                "split_pair_status": "PASS",
            }
        )
    return pd.DataFrame(rows)


SUMMARY_USECOLS = list(
    dict.fromkeys(
        [
            *base_audit.SUMMARY_USECOLS,
            "eligible_for_winner",
            "not_eligible_for_winner",
            "not_eligible_reason",
        ]
    )
)
TRADES_USECOLS = base_audit.TRADES_USECOLS
SCORES_USECOLS = base_audit.SCORES_USECOLS


def _csv(path: Path, usecols: list[str]) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", usecols=usecols)


def load_normalized_artifacts(prefix: Path = DEFAULT_INPUT_PREFIX) -> dict[str, object]:
    json_path = prefix.with_suffix(".json")
    with json_path.open("r", encoding="utf-8") as handle:
        artifact = json.load(handle)
    return {
        "artifact": artifact,
        "summary": _csv(prefix.with_name(prefix.name + "_summary.csv"), SUMMARY_USECOLS),
        "trades": _csv(prefix.with_name(prefix.name + "_trades.csv"), TRADES_USECOLS),
        "scores": _csv(prefix.with_name(prefix.name + "_scores.csv"), SCORES_USECOLS),
    }


def fixed_rule_from_contract_row(row: pd.Series | dict[str, object]) -> base_audit.FixedRule:
    data = row.to_dict() if isinstance(row, pd.Series) else dict(row)
    return base_audit.FixedRule(
        stop_policy_id=STOP_POLICY_ID,
        entry_id=ENTRY_ID,
        mask_id=MASK_ID,
        exit_id=EXIT_ID,
        spread=CANONICAL_SPREAD,
        profile_id=str(data["profile_id"]),
        model_id=str(data["model_id"]),
        target_id=str(data["target_id"]),
        filter_id=str(data["filter_id"]),
        entry_filter_score_col=ENTRY_FILTER_SCORE_COL,
        score_cutoff_on_val_select=float(data["score_cutoff_on_val_select"]),
    )


def _tag_frame(frame: pd.DataFrame, contract_row: dict[str, object]) -> pd.DataFrame:
    out = frame.copy()
    if out.empty:
        return out
    insert_cols = {
        "original_rank": int(contract_row["original_rank"]),
        "rule_id": str(contract_row["rule_id"]),
        "profile_id": str(contract_row["profile_id"]),
        "model_id": str(contract_row["model_id"]),
        "target_id": str(contract_row["target_id"]),
        "filter_id": str(contract_row["filter_id"]),
    }
    for column, value in reversed(list(insert_cols.items())):
        if column not in out.columns:
            out.insert(0, column, value)
        else:
            out[column] = value
    return out


def _summary_for_rule(summary: pd.DataFrame, rule: base_audit.FixedRule) -> dict[str, object]:
    row = base_audit.filter_fixed_rule_rows(summary, rule, split="val_eval")
    if len(row) != 1:
        raise ValueError(f"val_eval summary expected once for {rule}, got {len(row)}")
    return row.iloc[0].to_dict()


def audit_one_rule(
    summary: pd.DataFrame,
    trades: pd.DataFrame,
    scores: pd.DataFrame,
    contract_row: pd.Series | dict[str, object],
) -> dict[str, object]:
    row = contract_row.to_dict() if isinstance(contract_row, pd.Series) else dict(contract_row)
    rule = fixed_rule_from_contract_row(row)
    fixed_trades = base_audit.filter_fixed_rule_rows(trades, rule, split="val_eval")
    selected_summary = _summary_for_rule(summary, rule)
    bootstrap = base_audit.sequential_block_bootstrap_pf(
        fixed_trades,
        seed=20260723 + int(row["original_rank"]),
        n_bootstrap=1000,
        block_size=20,
    )
    selected_summary["source_bs_p05"] = selected_summary.get("bs_p05")
    selected_summary["sequential_block_bs_p05"] = bootstrap.get("bs_p05")
    selected_summary["bs_p05"] = bootstrap.get("bs_p05")
    selected_summary["original_rank"] = int(row["original_rank"])
    selected_summary["rule_id"] = str(row["rule_id"])
    selected_summary["rule_family_tag"] = "time_heavy" if "time" in str(row["profile_id"]) else "non_time"

    concentration = base_audit.profit_concentration(fixed_trades)
    selected_summary.update({f"concentration_{key}": value for key, value in concentration.items()})

    return {
        "summary": selected_summary,
        "yearly": _tag_frame(base_audit.metrics_by_period(fixed_trades, "Y"), row),
        "quarterly": _tag_frame(base_audit.metrics_by_period(fixed_trades, "Q"), row),
        "side": _tag_frame(base_audit.metrics_by_side(fixed_trades), row),
        "year_side": _tag_frame(base_audit.metrics_by_year_side(fixed_trades), row),
        "score_shift": _tag_frame(base_audit.score_shift(scores, rule), row),
        "stricter_cutoff": _tag_frame(base_audit.stricter_cutoff_sensitivity(scores, trades, rule), row),
        "topk_sensitivity": _tag_frame(base_audit.topk_sensitivity(trades, rule), row),
        "calendar_slices": _tag_frame(base_audit.calendar_slices(trades, rule), row),
        "block_bootstrap": bootstrap,
    }


LEADERBOARD_DECISION_GATE_CONFIG = {
    "min_bs_p05": 1.0,
    "min_pf_without_best_year": 1.0,
    "min_side_pf": 1.0,
    "min_side_n_trades": 30,
    "max_side_drawdown_r": 8.5,
    "stricter_cutoff_min_n_trades": 300,
    "topk_min_pf": 1.0,
    "topk_min_n_trades": 300,
    "effective_profit_years_formula": "max(1.5, 0.6 * n_years)",
}


def missing_diagnostics_for_rule(contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = contract_row.to_dict() if isinstance(contract_row, pd.Series) else dict(contract_row)
    profile_id = str(row["profile_id"])
    records = [
        {
            "rule_id": str(row["rule_id"]),
            "diagnostic": "stress_costs",
            "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
            "reason": "saved trades contain realized pnl for canonical spread only; stress spread requires explicit resimulation",
        },
        {
            "rule_id": str(row["rule_id"]),
            "diagnostic": "sequential_position_constraint",
            "status": "NOT_RUN",
            "reason": "position-overlap simulation is not implemented in this saved-artifact audit",
        },
    ]
    if "time" in profile_id:
        records.extend(
            [
                {
                    "rule_id": str(row["rule_id"]),
                    "diagnostic": "timezone_shift",
                    "status": "NOT_RUN",
                    "reason": "requires frozen rescore of time features under predefined timezone shifts",
                },
                {
                    "rule_id": str(row["rule_id"]),
                    "diagnostic": "calendar_permutation_importance",
                    "status": "NOT_RUN",
                    "reason": "fitted per-profile estimator is not persisted for model-level permutation importance",
                },
            ]
        )
    return pd.DataFrame(records)


def rule_decision(
    summary_row: dict[str, object],
    side: pd.DataFrame,
    stricter_cutoff: pd.DataFrame,
    topk: pd.DataFrame,
    missing: pd.DataFrame,
) -> dict[str, object]:
    gate = LEADERBOARD_DECISION_GATE_CONFIG
    reasons: list[str] = []
    disclosures: list[str] = []
    n_years = int(summary_row.get("concentration_n_years") or summary_row.get("n_years") or 0)
    effective_years = float(summary_row.get("concentration_effective_profit_years") or summary_row.get("effective_profit_years") or 0.0)
    if effective_years < max(1.5, 0.6 * n_years):
        reasons.append("profit_concentration_fail")
    if float(summary_row.get("sequential_block_bs_p05") or summary_row.get("bs_p05") or 0.0) < gate["min_bs_p05"]:
        reasons.append("block_bootstrap_fail")
    if float(summary_row.get("pf_without_best_year") or 0.0) < gate["min_pf_without_best_year"]:
        reasons.append("pf_without_best_year_fail")
    if side.empty or (pd.to_numeric(side.get("pf"), errors="coerce") < gate["min_side_pf"]).any():
        reasons.append("side_pf_fail")
    if side.empty or (pd.to_numeric(side.get("n_trades"), errors="coerce") < gate["min_side_n_trades"]).any():
        reasons.append("side_sample_fail")
    if side.empty or (pd.to_numeric(side.get("max_drawdown_r"), errors="coerce") > gate["max_side_drawdown_r"]).any():
        reasons.append("side_drawdown_warning")
    if stricter_cutoff.empty or pd.to_numeric(stricter_cutoff.get("n_trades"), errors="coerce").min() < gate["stricter_cutoff_min_n_trades"]:
        reasons.append("stricter_cutoff_sample_fragile")
    if topk.empty or (pd.to_numeric(topk.get("pf"), errors="coerce") < gate["topk_min_pf"]).any():
        reasons.append("topk_pf_fragile")
    if topk.empty or (pd.to_numeric(topk.get("n_trades"), errors="coerce") < gate["topk_min_n_trades"]).any():
        reasons.append("topk_sample_fragile")

    missing_status = {(str(row["diagnostic"]), str(row["status"])) for _, row in missing.iterrows()}
    if ("stress_costs", "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS") in missing_status:
        reasons.append("stress_costs_not_computable")
    if ("sequential_position_constraint", "NOT_RUN") in missing_status:
        disclosures.append("sequential_position_constraint_not_run")
    if ("timezone_shift", "NOT_RUN") in missing_status:
        disclosures.append("timezone_shift_not_run")
    if ("calendar_permutation_importance", "NOT_RUN") in missing_status:
        disclosures.append("calendar_permutation_importance_not_run")

    if "block_bootstrap_fail" in reasons or "pf_without_best_year_fail" in reasons:
        decision = "REJECT_RULE_AS_UNSTABLE"
    elif reasons:
        decision = "RULE_ROBUSTNESS_INCOMPLETE"
    else:
        decision = "RULE_ROBUSTNESS_SLICE_OK_FOR_RESEARCH_COMPARISON"
    return {
        "decision": decision,
        "reasons": reasons,
        "disclosures": disclosures,
        "allowed_max_verdict": "research_only",
        "decision_gate_config": gate,
    }


def aggregate_limitation_statuses(missing: pd.DataFrame) -> dict[str, object]:
    statuses = {
        "locked_test_status": "not_opened",
        "stress_costs_status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
        "timezone_shift_status": "NOT_RUN",
        "calendar_permutation_importance_status": "NOT_RUN",
        "sequential_position_constraint_status": "NOT_RUN",
        "multi_seed_status": "NOT_RUN",
        "provider_drift_status": "NOT_RUN",
        "transfer_status": "NOT_RUN",
    }
    if not missing.empty:
        for diagnostic, group in missing.groupby("diagnostic"):
            statuses[f"{diagnostic}_status"] = ",".join(sorted(set(group["status"].astype(str))))
    statuses["limitations"] = [
        "locked_test remains closed",
        "broad-search origin bias remains",
        "stress-cost resimulation is not computed from saved filtered artifacts",
        "timezone-shift rescore is not run for time-heavy profiles",
        "calendar permutation importance is not run because fitted estimators are not persisted",
        "multi-seed, provider-drift and transfer checks are not run",
    ]
    return statuses


def build_classification(summaries: pd.DataFrame, decisions: dict[str, dict[str, object]]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in summaries.sort_values("original_rank").iterrows():
        rule_id = str(row["rule_id"])
        decision = decisions[rule_id]
        profile_id = str(row["profile_id"])
        if profile_id == "time_only":
            interpretation = "stable_but_time_explained"
        elif "time" in profile_id:
            interpretation = "time_heavy_not_additive_evidence"
        else:
            interpretation = "non_time_profile_not_in_top11"
        if decision["decision"] == "REJECT_RULE_AS_UNSTABLE":
            interpretation = "fragile_by_robustness_gate"
        elif "stress_costs_not_computable" in decision.get("reasons", []):
            interpretation = f"{interpretation}_needs_cost_resimulation"
        rows.append(
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": rule_id,
                "profile_id": profile_id,
                "model_id": str(row["model_id"]),
                "target_id": str(row["target_id"]),
                "filter_id": str(row["filter_id"]),
                "decision": str(decision["decision"]),
                "interpretation": interpretation,
                "reasons": ",".join(str(x) for x in decision.get("reasons", [])),
                "disclosures": ",".join(str(x) for x in decision.get("disclosures", [])),
                "allowed_max_verdict": "research_only",
                "new_winner_selected": False,
            }
        )
    return pd.DataFrame(rows)


def overall_decision_from_classification(classification: pd.DataFrame, missing: pd.DataFrame) -> dict[str, object]:
    decisions = set(classification["decision"].astype(str))
    profiles = set(classification["profile_id"].astype(str))
    missing_pairs = {(str(row["diagnostic"]), str(row["status"])) for _, row in missing.iterrows()}
    reasons: list[str] = []
    if decisions == {"REJECT_RULE_AS_UNSTABLE"}:
        return {
            "overall_decision": "ALL_RULES_REJECTED_AS_UNSTABLE_RESEARCH_ONLY",
            "overall_decision_reasons": ["all_rules_rejected_as_unstable"],
        }
    if ("stress_costs", "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS") in missing_pairs:
        reasons.append("stress_costs_not_computable")
    if ("timezone_shift", "NOT_RUN") in missing_pairs:
        reasons.append("timezone_shift_not_run")
    if ("calendar_permutation_importance", "NOT_RUN") in missing_pairs:
        reasons.append("calendar_permutation_importance_not_run")
    if ("sequential_position_constraint", "NOT_RUN") in missing_pairs:
        reasons.append("sequential_position_constraint_not_run")
    reasons.extend(["multi_seed_not_run", "provider_drift_not_run", "transfer_not_run"])
    if reasons:
        return {
            "overall_decision": "LEADERBOARD_ROBUSTNESS_INCOMPLETE_NEEDS_COST_TIME_CHECKS",
            "overall_decision_reasons": list(dict.fromkeys(reasons)),
        }
    if profiles.issubset({"time_only", "movement_plus_time"}):
        return {
            "overall_decision": "NO_STANDALONE_NON_TIME_EVIDENCE_RESEARCH_ONLY",
            "overall_decision_reasons": ["leaderboard_contains_only_time_heavy_profiles"],
        }
    return {
        "overall_decision": "LEADERBOARD_ROBUSTNESS_SLICE_REVIEW_REQUIRED_RESEARCH_ONLY",
        "overall_decision_reasons": ["non_time_profile_present_requires_manual_comparator_review"],
    }


def source_scale_contract(artifact: dict[str, object]) -> dict[str, object]:
    source_artifacts = artifact.get("artifacts", {}) if isinstance(artifact.get("artifacts"), dict) else {}
    flags = artifact.get("feature_distribution_flags") or []
    structural_statuses = {str(row.get("status", "")).upper() for row in flags if isinstance(row, dict)}
    normalized_audit_csv = source_artifacts.get("normalized_feature_distribution_audit_csv")
    normalized_flag_counts: dict[str, int] = {}
    if normalized_audit_csv:
        normalized_path = Path(str(normalized_audit_csv))
        if normalized_path.exists():
            audit_flags = pd.read_csv(normalized_path, sep=";", usecols=["flag"])
            normalized_flag_counts = {
                str(flag): int(count)
                for flag, count in audit_flags["flag"].value_counts(dropna=False).sort_index().items()
            }
    normalized_statuses = set(normalized_flag_counts)
    if {"FAIL", "ERROR"} & (structural_statuses | normalized_statuses):
        status = "FAIL"
    elif "WARNING" in (structural_statuses | normalized_statuses):
        status = "DIAGNOSTIC_ONLY"
    else:
        status = "PASS"
    return {
        "status": status,
        "structural_profile_gate_status": "FAIL" if {"FAIL", "ERROR"} & structural_statuses else "PASS",
        "feature_contract_variant": artifact.get("feature_contract_variant"),
        "normalization_config": artifact.get("normalization_config"),
        "normalization_config_json": source_artifacts.get("normalization_config_json"),
        "normalized_feature_distribution_audit_csv": normalized_audit_csv,
        "normalized_feature_distribution_flag_counts": normalized_flag_counts,
        "warning_action": "accept-as-warning" if normalized_flag_counts.get("WARNING", 0) > 0 else None,
        "warning_action_reason": (
            "constant or near-constant normalized feature columns are disclosed as preprocessing warnings; "
            "this audit remains research_only and cannot support stronger interpretation"
        )
        if normalized_flag_counts.get("WARNING", 0) > 0
        else None,
        "scale_contract_source": "source normalized artifact",
        "flag_statuses": sorted(status for status in structural_statuses if status),
    }


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, sep=";", index=False)


def _unknown(
    output_prefix: Path,
    decision: str,
    exc: Exception,
    source_artifact: dict[str, object] | None = None,
) -> dict[str, object]:
    source_locked_test = source_artifact.get("locked_test") if source_artifact else None
    if source_artifact is None:
        locked_test_status = "UNKNOWN_SOURCE_NOT_LOADED"
    elif source_locked_test == "not_opened":
        locked_test_status = "not_opened"
    else:
        locked_test_status = "SOURCE_CONTRACT_FAILED"
    result = {
        "experiment": "leaderboard_robustness_audit",
        "status": "UNKNOWN",
        "run_status": "failed",
        "verdict": "research_only",
        "locked_test": None,
        "locked_test_status": locked_test_status,
        "source_locked_test": source_locked_test,
        "allowed_max_verdict": "research_only",
        "decision": {"decision": decision, "reasons": [str(exc)]},
        "overall_decision": decision,
        "contract_errors": [str(exc)],
        "limitations": ["input or contract failure blocked leaderboard robustness audit"],
    }
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    output_prefix.with_suffix(".json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def run_audit(input_prefix: Path = DEFAULT_INPUT_PREFIX, output_prefix: Path = DEFAULT_OUTPUT_PREFIX) -> dict[str, object]:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    artifact: dict[str, object] | None = None
    try:
        loaded = load_normalized_artifacts(input_prefix)
        artifact = loaded["artifact"]
        summary = loaded["summary"]
        trades = loaded["trades"]
        scores = loaded["scores"]
        global_contract = verify_global_artifact_contract(artifact)
        rule_contract = verify_leaderboard_contract(summary, LEADERBOARD_RULES)
        input_artifacts = base_audit.input_artifact_metadata(input_prefix)
    except GlobalArtifactContractError as exc:
        return _unknown(output_prefix, exc.decision, exc, artifact)
    except LeaderboardContractError as exc:
        return _unknown(output_prefix, exc.decision, exc, artifact)
    except FileNotFoundError as exc:
        return _unknown(output_prefix, "UNKNOWN_INPUT_ARTIFACTS", exc, artifact)
    except (json.JSONDecodeError, pd.errors.ParserError, ValueError, KeyError) as exc:
        return _unknown(output_prefix, "UNKNOWN_INPUT_SCHEMA", exc, artifact)

    collected = {
        "summary": [],
        "yearly": [],
        "quarterly": [],
        "side": [],
        "year_side": [],
        "score_shift": [],
        "stricter_cutoff": [],
        "topk_sensitivity": [],
        "calendar_slices": [],
        "missing_diagnostics": [],
    }
    decisions: dict[str, dict[str, object]] = {}
    for _, contract_row in rule_contract.iterrows():
        diagnostics = audit_one_rule(summary, trades, scores, contract_row)
        missing = missing_diagnostics_for_rule(contract_row)
        decision = rule_decision(
            diagnostics["summary"],
            diagnostics["side"],
            diagnostics["stricter_cutoff"],
            diagnostics["topk_sensitivity"],
            missing,
        )
        decisions[str(contract_row["rule_id"])] = decision
        collected["summary"].append(pd.DataFrame([diagnostics["summary"]]))
        for key in ["yearly", "quarterly", "side", "year_side", "score_shift", "stricter_cutoff", "topk_sensitivity", "calendar_slices"]:
            collected[key].append(diagnostics[key])
        collected["missing_diagnostics"].append(missing)

    frames = {key: pd.concat(value, ignore_index=True) if value else pd.DataFrame() for key, value in collected.items()}
    classification = build_classification(frames["summary"], decisions)
    limitation_statuses = aggregate_limitation_statuses(frames["missing_diagnostics"])
    overall = overall_decision_from_classification(classification, frames["missing_diagnostics"])
    artifacts = {
        "rules_csv": output_prefix.with_name(output_prefix.name + "_rules.csv"),
        "summary_csv": output_prefix.with_name(output_prefix.name + "_summary.csv"),
        "yearly_csv": output_prefix.with_name(output_prefix.name + "_yearly.csv"),
        "quarterly_csv": output_prefix.with_name(output_prefix.name + "_quarterly.csv"),
        "side_csv": output_prefix.with_name(output_prefix.name + "_side.csv"),
        "year_side_csv": output_prefix.with_name(output_prefix.name + "_year_side.csv"),
        "score_shift_csv": output_prefix.with_name(output_prefix.name + "_score_shift.csv"),
        "stricter_cutoff_csv": output_prefix.with_name(output_prefix.name + "_stricter_cutoff.csv"),
        "topk_sensitivity_csv": output_prefix.with_name(output_prefix.name + "_topk_sensitivity.csv"),
        "calendar_slices_csv": output_prefix.with_name(output_prefix.name + "_calendar_slices.csv"),
        "missing_diagnostics_csv": output_prefix.with_name(output_prefix.name + "_missing_diagnostics.csv"),
        "classification_csv": output_prefix.with_name(output_prefix.name + "_classification.csv"),
    }
    _write_csv(rule_contract, artifacts["rules_csv"])
    for key, csv_key in [
        ("summary", "summary_csv"),
        ("yearly", "yearly_csv"),
        ("quarterly", "quarterly_csv"),
        ("side", "side_csv"),
        ("year_side", "year_side_csv"),
        ("score_shift", "score_shift_csv"),
        ("stricter_cutoff", "stricter_cutoff_csv"),
        ("topk_sensitivity", "topk_sensitivity_csv"),
        ("calendar_slices", "calendar_slices_csv"),
        ("missing_diagnostics", "missing_diagnostics_csv"),
    ]:
        _write_csv(frames[key], artifacts[csv_key])
    _write_csv(classification, artifacts["classification_csv"])

    result = {
        "experiment": "leaderboard_robustness_audit",
        "status": "completed",
        "run_status": "completed",
        "verdict": "research_only",
        "locked_test": "not_opened",
        "locked_test_status": "not_opened",
        "scope": "validation_artifact_leaderboard_robustness_slice",
        "global_contract": global_contract,
        "leaderboard_rule_count": len(LEADERBOARD_RULES),
        "leaderboard_rules": [asdict(rule) | {"rule_id": rule.rule_id} for rule in LEADERBOARD_RULES],
        "input_artifacts": input_artifacts,
        "source_input_artifact_hashes": artifact.get("input_artifact_hashes"),
        "scale_contract": source_scale_contract(artifact),
        "source_search_budget": {
            "ranked_configs": 243,
            "executed_jobs": artifact.get("n_total_executed_configs"),
            "diagnostic_configs": artifact.get("diagnostic_budget", {}).get("listed_diagnostic_configs")
            if isinstance(artifact.get("diagnostic_budget"), dict)
            else None,
        },
        "allowed_max_verdict": "research_only",
        "forbidden_interpretations": ["candidate", "tradable", "live_ready", "production", "permission_to_open_locked_test", "new_winner"],
        **limitation_statuses,
        "decisions_by_rule": decisions,
        **overall,
        "artifacts": {name: str(path) for name, path in artifacts.items()},
    }
    output_prefix.with_suffix(".json").write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit robustness of fixed normalized rich-entry leaderboard rows.")
    parser.add_argument("--input-prefix", default=str(DEFAULT_INPUT_PREFIX))
    parser.add_argument("--output-prefix", default=str(DEFAULT_OUTPUT_PREFIX))
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    result = run_audit(Path(args.input_prefix), Path(args.output_prefix))
    print(json.dumps({"status": result["status"], "overall_decision": result.get("overall_decision"), "decision": result.get("decision")}, ensure_ascii=False))
    if result.get("status") == "UNKNOWN":
        sys.exit(1)


if __name__ == "__main__":
    main()
