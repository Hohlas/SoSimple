# =============================================================================
# Файл: fractal0_fixed11_internal_closure_rerun.py
# Назначение: Fixed-11 internal closure rerun для normalized rich-entry leaderboard.
# Обновлён: 2026-07-23
# Входные данные:
#   - ML/reports/fractal0_rich_entry_quality_normalized*.*
#   - ML/reports/leaderboard_closure_audit_rules.csv
#   - MT/MQL4/Files/XAUUSD_M5_OHLC.csv
# Выходные данные:
#   - ML/reports/fractal0_fixed11_internal_closure_rerun*.*
# Использование:
#   ./.venv/bin/python ML/baseline/fractal0_fixed11_internal_closure_rerun.py --threads 24
# Примечания:
#   - locked_test не открывается; максимум verdict = research_only.
# =============================================================================

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import pickle
import sys
from decimal import Decimal
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from pandas.errors import EmptyDataError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ML.baseline import audit_leaderboard_closure as closure
from ML.baseline import audit_leaderboard_robustness as leaderboard
from ML.baseline import benchmark_fractal0_entry_quality_filter as rich


CLOSURE_OUTPUT_PREFIX = Path("ML/reports/fractal0_fixed11_internal_closure_rerun")
SOURCE_INPUT_PREFIX = Path("ML/reports/fractal0_rich_entry_quality_normalized")
SOURCE_RULES_CSV = Path("ML/reports/leaderboard_closure_audit_rules.csv")
STRESS_SPREADS = (0.2, 0.4, 0.8)
TIMEZONE_SHIFT_HOURS = (0, -8, -4, 4, 8)
MULTISEED_SEEDS = (41, 42, 43, 44, 45)
SUPPORTED_RUN_GROUPS = ("stress_cost", "timezone_calendar", "multiseed")
CALENDAR_BASELINE_FAMILIES = ("hour", "weekday", "hour_weekday")
CALENDAR_PERMUTATION_REPEATS = 50
CALENDAR_SMALL_GROUP_MIN_ROWS = 5
CALENDAR_BUCKET_MIN_TRADES = 30
CALENDAR_BASELINE_MIN_PF = 1.20
CALENDAR_BASELINE_MIN_BS_P05 = 1.00
PF_ZERO_LOSS_POLICY = "gross_loss_zero_positive_profit_pf_99_matches_project_diagnostic_cap"
REQUIRED_STRESS_TRADE_COLUMNS = (
    "entry_effective_price",
    "fill_time",
    "exit_time",
    "close_reason",
    "r_value",
    "pnl_r",
    "spread",
)
STRESS_COST_CONVENTION = {
    "ohlc_price_convention": "bid_ohlc_with_spread_adjusted_sell_exit_bars",
    "spread_definition": "full_bid_ask_spread_in_price_units",
    "entry_price_rule": "buy_fill_when_low_plus_spread_le_limit_and_sell_fill_when_high_ge_limit; entry_effective_price_equals_limit_price",
    "sl_trigger_rule": "protective_stop_checked_on_effective_exit_bars; same_bar_tp_sl_without_execution_ohlc_resolves_sl_first",
    "tp_rule": "fixed_r_take_profit_from_entry_effective_price_plus_or_minus_tp_r_times_r_value",
    "timeout_pnl_rule": "time_exit_marks_to_close_price_of_hold_limit_bar_on_effective_exit_bars",
}


@dataclass(frozen=True)
class RunSpec:
    run_group: str
    original_rank: int
    rule_id: str
    profile_id: str
    model_id: str
    target_id: str
    filter_id: str
    seed: int
    spread: float
    timezone_shift_hours: int
    locked_test_status: str = "not_opened"
    provider_drift_status: str = "NOT_IN_SCOPE"
    transfer_status: str = "NOT_IN_SCOPE"


@dataclass
class CalendarDiagnosticState:
    original_rank: int
    rule_id: str
    profile_id: str
    model_id: str
    target_id: str
    filter_id: str
    target_kind: str
    cutoff: float
    model: object
    feature_frames: dict[str, pd.DataFrame]
    scored_entries: dict[str, pd.DataFrame]
    entry_cache: dict[str, pd.DataFrame]
    scored_decisions: dict[str, pd.DataFrame]
    run_base: dict[str, object]
    filter_rule: dict[str, object]
    summaries: dict[str, dict[str, object]]
    ohlc: pd.DataFrame
    execution_ohlc: pd.DataFrame | None
    model_path: Path
    scaler_path: Path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fixed_rule_manifest_frame() -> pd.DataFrame:
    rows = []
    for rule in leaderboard.LEADERBOARD_RULES:
        rows.append(
            {
                "original_rank": int(rule.original_rank),
                "rule_id": rule.rule_id,
                "profile_id": rule.profile_id,
                "model_id": rule.model_id,
                "target_id": rule.target_id,
                "filter_id": rule.filter_id,
                "locked_test_policy": "not_opened",
            }
        )
    return pd.DataFrame(rows)


def _run_rows(run_group: str, seed: int, spread: float, timezone_shift_hours: int) -> list[dict[str, object]]:
    rows = []
    for row in fixed_rule_manifest_frame().to_dict(orient="records"):
        rows.append(
            {
                **row,
                "run_group": run_group,
                "seed": int(seed),
                "spread": float(spread),
                "timezone_shift_hours": int(timezone_shift_hours),
                "provider_drift_status": "NOT_IN_SCOPE",
                "transfer_status": "NOT_IN_SCOPE",
                "locked_test_status": "not_opened",
            }
        )
    return rows


def build_internal_run_matrix(smoke_first_rule_only: bool = False) -> pd.DataFrame:
    rows = []
    for spread in STRESS_SPREADS:
        rows.extend(_run_rows("stress_cost", seed=42, spread=spread, timezone_shift_hours=0))
    for shift in TIMEZONE_SHIFT_HOURS:
        rows.extend(_run_rows("timezone_calendar", seed=42, spread=0.2, timezone_shift_hours=shift))
    for seed in MULTISEED_SEEDS:
        rows.extend(_run_rows("multiseed", seed=seed, spread=0.2, timezone_shift_hours=0))
    matrix = pd.DataFrame(rows)
    if smoke_first_rule_only:
        matrix = matrix.loc[matrix["original_rank"].eq(1)].copy()
    return matrix.reset_index(drop=True)


def load_saved_cutoffs(path: Path = SOURCE_RULES_CSV) -> dict[str, float]:
    frame = pd.read_csv(
        path,
        sep=";",
        usecols=["rule_id", "score_cutoff_on_val_select"],
        dtype={"rule_id": str, "score_cutoff_on_val_select": str},
    )
    if frame["rule_id"].duplicated().any():
        duplicates = frame.loc[frame["rule_id"].duplicated(), "rule_id"].astype(str).tolist()
        raise ValueError(f"duplicate saved cutoff rule_id values: {duplicates[:5]}")
    return {
        str(row["rule_id"]): float(Decimal(str(row["score_cutoff_on_val_select"])))
        for _, row in frame.iterrows()
    }


def calendar_feature_columns(profile_id: str) -> list[str]:
    if profile_id not in {"time_only", "movement_plus_time"}:
        return []
    return [
        "session_hour_unit",
        "weekday_unit",
        "hour_sin_unit",
        "hour_cos_unit",
        "weekday_sin_unit",
        "weekday_cos_unit",
    ]


def add_timezone_risk_flags(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    anchors = (
        out.loc[out["timezone_shift_hours"].eq(0), ["rule_id", "pf"]]
        .rename(columns={"pf": "pf_shift0"})
    )
    out = out.merge(anchors, on="rule_id", how="left")
    out["pf_drop_from_shift0_ratio"] = (
        (pd.to_numeric(out["pf_shift0"], errors="coerce") - pd.to_numeric(out["pf"], errors="coerce"))
        / pd.to_numeric(out["pf_shift0"], errors="coerce")
    ).clip(lower=0.0)
    out["risk_flag"] = (
        out["timezone_shift_hours"].ne(0)
        & (
            (out["pf_drop_from_shift0_ratio"] > 0.30)
            | (pd.to_numeric(out["pf"], errors="coerce") < 1.20)
            | (pd.to_numeric(out["bs_p05"], errors="coerce") < 1.00)
            | (pd.to_numeric(out["n_trades"], errors="coerce") < 300)
        )
    )
    return out


def source_rules_metadata(path: Path) -> dict[str, str]:
    return {
        "source_rules_csv": str(path),
        "source_rules_csv_sha256": _sha256_file(path),
    }


def _guard_locked_test_not_opened(source_prefix: Path = SOURCE_INPUT_PREFIX) -> dict[str, object]:
    loaded = closure.verify_closure_inputs(source_prefix)
    artifact = loaded["loaded"]["artifact"]
    if artifact.get("locked_test") != "not_opened":
        raise ValueError("locked_test must remain not_opened before any run")
    return loaded


def _run_prefix(output_prefix: Path, group: str, seed: int, spread: float, timezone_shift_hours: int) -> Path:
    spread_tag = str(spread).replace(".", "p")
    return output_prefix.with_name(
        f"{output_prefix.name}_{group}_seed{int(seed)}_spread{spread_tag}_tz{int(timezone_shift_hours):+d}"
    )


def _parse_run_groups(raw_value: str) -> tuple[str, ...]:
    groups = tuple(item.strip() for item in str(raw_value).split(",") if item.strip())
    if not groups:
        return ("stress_cost",)
    unknown = sorted(set(groups) - set(SUPPORTED_RUN_GROUPS))
    if unknown:
        raise ValueError(f"unsupported run_groups: {unknown}")
    return groups


def _child_completed_artifact(run_prefix: Path) -> dict[str, object] | None:
    path = run_prefix.with_suffix(".json")
    if not path.exists():
        return None
    try:
        artifact = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if str(artifact.get("status")) != "completed":
        return None
    return artifact


def _run_rich_fixed_once_or_resume(
    output_prefix: Path,
    seed: int,
    spread: float,
    timezone_shift_hours: int,
    fixed_cutoffs_csv: Path,
    threads: int,
    smoke_first_rule_only: bool,
    no_resume: bool,
) -> dict[str, object]:
    if not no_resume and _child_completed_artifact(output_prefix) is not None:
        return {
            "run_prefix": str(output_prefix),
            "status": "resume_skipped",
            "child_status": "completed",
            "child_json": str(output_prefix.with_suffix(".json")),
        }
    result = run_rich_fixed_once(
        output_prefix=output_prefix,
        seed=seed,
        spread=spread,
        timezone_shift_hours=timezone_shift_hours,
        fixed_cutoffs_csv=fixed_cutoffs_csv,
        threads=threads,
        smoke_first_rule_only=smoke_first_rule_only,
    )
    return {
        "run_prefix": str(output_prefix),
        "status": "executed",
        "child_status": str(result.get("status")),
        "child_json": str(output_prefix.with_suffix(".json")),
    }


def run_rich_fixed_once(
    output_prefix: Path,
    seed: int,
    spread: float,
    timezone_shift_hours: int,
    fixed_cutoffs_csv: Path,
    threads: int,
    smoke_first_rule_only: bool = False,
) -> dict[str, object]:
    args = SimpleNamespace(
        threads=int(threads),
        no_resume=False,
        output_prefix=str(output_prefix),
        execution_ohlc_path="MT/MQL4/Files/XAUUSD_M5_OHLC.csv",
        stop_policy_id="",
        stop_grid_artifact="ML/reports/fractal0_entry_exit_grid_stop_policy.json",
        permutation_repeats=0,
        smoke_limit_filters=0,
        rich_entry_quality=True,
        include_diagnostic_models=True,
        normalized_rich_features=True,
        rich_entry_seed=int(seed),
        fixed_leaderboard_rules_only=True,
        fixed_cutoffs_csv=str(fixed_cutoffs_csv),
        spread=float(spread),
        timezone_shift_hours=int(timezone_shift_hours),
        smoke_first_rule_only=bool(smoke_first_rule_only),
    )
    return rich.run_rich_entry_quality(args)


def _read_trade_columns(run_prefix: Path) -> list[str]:
    trades_path = run_prefix.with_name(run_prefix.name + "_trades.csv")
    try:
        return pd.read_csv(trades_path, sep=";", nrows=0).columns.tolist()
    except EmptyDataError:
        return []


def collect_stress_cost(run_prefix: Path, matrix: pd.DataFrame) -> pd.DataFrame:
    summary = pd.read_csv(run_prefix.with_name(run_prefix.name + "_summary.csv"), sep=";")
    required_summary_columns = ["original_rank", "rule_id", "spread", "split", "n_trades", "pf", "bs_p05", "max_drawdown_r"]
    missing_summary_columns = [column for column in required_summary_columns if column not in summary.columns]
    if missing_summary_columns:
        raise ValueError(f"stress summary missing required columns: {missing_summary_columns}")
    summary = summary.loc[summary["split"].astype(str).eq("val_eval")].copy()
    if summary.empty:
        raise ValueError(f"stress summary has no val_eval rows: {run_prefix}")
    summary["run_group"] = "stress_cost"
    trade_columns = set(_read_trade_columns(run_prefix))
    trade_file_status = "HEADER_PRESENT"
    if trade_columns:
        missing_trade_columns = [column for column in REQUIRED_STRESS_TRADE_COLUMNS if column not in trade_columns]
        if missing_trade_columns:
            raise ValueError(f"stress trades missing required columns: {missing_trade_columns}")
    elif pd.to_numeric(summary["n_trades"], errors="coerce").fillna(0).gt(0).any():
        raise ValueError(f"stress trades file is empty despite non-zero trades: {run_prefix}")
    else:
        trade_file_status = "EMPTY_ZERO_TRADE_RUN"

    expected = matrix.loc[matrix["run_group"].astype(str).eq("stress_cost")].copy()
    if expected.empty:
        raise ValueError("stress run matrix is empty")

    merged = expected.merge(
        summary,
        on=["original_rank", "rule_id", "spread"],
        how="left",
        validate="one_to_one",
        suffixes=("", "_summary"),
    )
    if merged[["n_trades", "max_drawdown_r"]].isna().any().any():
        raise ValueError(f"stress summary rows missing for expected matrix: {run_prefix}")
    positive_trade_rows = pd.to_numeric(merged["n_trades"], errors="coerce").fillna(0).gt(0)
    if merged.loc[positive_trade_rows, ["pf", "bs_p05"]].isna().any().any():
        raise ValueError(f"stress summary rows missing pf/bs_p05 for non-zero trades: {run_prefix}")

    merged["split"] = "val_eval"
    merged["status"] = "COMPUTED"
    merged["cost_component"] = "spread"
    merged["stress_multiplier"] = pd.to_numeric(merged["spread"], errors="coerce") / float(STRESS_SPREADS[0])
    merged["locked_test"] = "not_opened"
    merged["locked_test_status"] = "not_opened"
    merged["reason"] = "producer_level_rich_runner_resimulation"
    threshold_fail = (
        (pd.to_numeric(merged["n_trades"], errors="coerce") < 300)
        | (pd.to_numeric(merged["pf"], errors="coerce") < 1.20)
        | (pd.to_numeric(merged["bs_p05"], errors="coerce") < 1.00)
    )
    merged["canonical_gate_flag"] = pd.to_numeric(merged["spread"], errors="coerce").eq(0.2) & threshold_fail
    merged["stress_2x_4x_flag"] = pd.to_numeric(merged["spread"], errors="coerce").isin([0.4, 0.8]) & threshold_fail
    merged["risk_flag"] = merged["stress_2x_4x_flag"]
    merged["ohlc_price_convention"] = STRESS_COST_CONVENTION["ohlc_price_convention"]
    merged["spread_definition"] = STRESS_COST_CONVENTION["spread_definition"]
    merged["entry_price_rule"] = STRESS_COST_CONVENTION["entry_price_rule"]
    merged["sl_trigger_rule"] = STRESS_COST_CONVENTION["sl_trigger_rule"]
    merged["tp_rule"] = STRESS_COST_CONVENTION["tp_rule"]
    merged["timeout_pnl_rule"] = STRESS_COST_CONVENTION["timeout_pnl_rule"]
    merged["trade_file_status"] = trade_file_status
    return merged.sort_values(["original_rank", "spread"]).reset_index(drop=True)


def collect_timezone_rescore(run_prefix: Path, matrix: pd.DataFrame) -> pd.DataFrame:
    summary = pd.read_csv(run_prefix.with_name(run_prefix.name + "_summary.csv"), sep=";")
    required_summary_columns = [
        "original_rank",
        "rule_id",
        "spread",
        "timezone_shift_hours",
        "split",
        "n_trades",
        "pf",
        "bs_p05",
        "max_drawdown_r",
    ]
    missing_summary_columns = [column for column in required_summary_columns if column not in summary.columns]
    if missing_summary_columns:
        raise ValueError(f"timezone summary missing required columns: {missing_summary_columns}")
    summary = summary.loc[summary["split"].astype(str).eq("val_eval")].copy()
    if summary.empty:
        raise ValueError(f"timezone summary has no val_eval rows: {run_prefix}")
    summary["run_group"] = "timezone_calendar"

    expected = matrix.loc[matrix["run_group"].astype(str).eq("timezone_calendar")].copy()
    if expected.empty:
        raise ValueError("timezone run matrix is empty")

    merge_keys = ["original_rank", "rule_id", "spread", "timezone_shift_hours"]
    merged = expected.merge(
        summary,
        on=merge_keys,
        how="left",
        validate="one_to_one",
        suffixes=("", "_summary"),
    )
    if merged[["n_trades", "max_drawdown_r"]].isna().any().any():
        raise ValueError(f"timezone summary rows missing for expected matrix: {run_prefix}")
    positive_trade_rows = pd.to_numeric(merged["n_trades"], errors="coerce").fillna(0).gt(0)
    if merged.loc[positive_trade_rows, ["pf", "bs_p05"]].isna().any().any():
        raise ValueError(f"timezone summary rows missing pf/bs_p05 for non-zero trades: {run_prefix}")

    merged["split"] = "val_eval"
    merged["status"] = "COMPUTED"
    merged["locked_test"] = "not_opened"
    merged["locked_test_status"] = "not_opened"
    merged["reason"] = "feature_rescore_rich_runner_fixed_saved_cutoffs"
    merged["fixed_cutoff_policy"] = "source_rules_csv_score_cutoff_on_val_select"
    merged["saved_scores_mutated"] = False
    merged = add_timezone_risk_flags(merged)
    timezone_order = {shift: idx for idx, shift in enumerate(TIMEZONE_SHIFT_HOURS)}
    merged["_timezone_order"] = merged["timezone_shift_hours"].map(timezone_order).fillna(len(timezone_order))
    return merged.sort_values(["original_rank", "_timezone_order"]).drop(columns=["_timezone_order"]).reset_index(drop=True)


def collect_multiseed(run_prefix: Path, matrix: pd.DataFrame) -> pd.DataFrame:
    summary = pd.read_csv(run_prefix.with_name(run_prefix.name + "_summary.csv"), sep=";")
    required_summary_columns = ["original_rank", "rule_id", "split", "n_trades", "pf", "bs_p05"]
    missing_summary_columns = [column for column in required_summary_columns if column not in summary.columns]
    if missing_summary_columns:
        raise ValueError(f"multiseed summary missing required columns: {missing_summary_columns}")
    summary = summary.loc[summary["split"].astype(str).eq("val_eval")].copy()
    if summary.empty:
        raise ValueError(f"multiseed summary has no val_eval rows: {run_prefix}")
    summary["run_group"] = "multiseed"

    expected = matrix.loc[matrix["run_group"].astype(str).eq("multiseed")].copy()
    if expected.empty:
        raise ValueError("multiseed run matrix is empty")

    merge_keys = ["original_rank", "rule_id"]
    for optional_key in ("spread", "timezone_shift_hours"):
        if optional_key in summary.columns:
            merge_keys.append(optional_key)
    merged = expected.merge(
        summary,
        on=merge_keys,
        how="left",
        validate="one_to_one",
        suffixes=("", "_summary"),
    )
    required_numeric_columns = ["n_trades"]
    missing_numerics = [column for column in required_numeric_columns if column not in merged.columns]
    if missing_numerics:
        raise ValueError(f"multiseed merged rows missing required columns: {missing_numerics}")
    if merged["n_trades"].isna().any():
        raise ValueError(f"multiseed summary rows missing for expected matrix: {run_prefix}")
    positive_trade_rows = pd.to_numeric(merged["n_trades"], errors="coerce").fillna(0).gt(0)
    if merged.loc[positive_trade_rows, ["pf", "bs_p05"]].isna().any().any():
        raise ValueError(f"multiseed summary rows missing pf/bs_p05 for non-zero trades: {run_prefix}")

    merged["split"] = "val_eval"
    merged["status"] = "COMPUTED"
    merged["diagnostic"] = "frozen_cutoff_seed_stress"
    merged["fixed_cutoff_policy"] = "source_rules_csv_score_cutoff_on_val_select"
    merged["saved_scores_mutated"] = False
    merged["winner_selected"] = False
    merged["locked_test"] = "not_opened"
    merged["locked_test_status"] = "not_opened"
    merged["reason"] = "frozen_cutoff_seed_stress_saved_cutoff_reuse"
    return merged.sort_values(["original_rank", "seed"]).reset_index(drop=True)


def aggregate_multiseed(multiseed: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for rule_id, group in multiseed.groupby("rule_id", sort=False):
        computed = group.loc[group["status"].astype(str).eq("COMPUTED")].copy()
        pf = pd.to_numeric(computed["pf"], errors="coerce")
        bs_p05 = pd.to_numeric(computed["bs_p05"], errors="coerce")
        n_trades = pd.to_numeric(computed["n_trades"], errors="coerce")
        passing = computed.loc[
            pf.ge(1.20)
            & bs_p05.ge(1.00)
            & n_trades.ge(300)
        ]
        first = group.iloc[0]
        row = {
            "rule_id": str(rule_id),
            "computed_seed_count": int(len(computed)),
            "passing_seed_count": int(len(passing)),
            "pf_min": float(pf.min()) if len(computed) else None,
            "pf_median": float(pf.median()) if len(computed) else None,
            "bs_p05_min": float(bs_p05.min()) if len(computed) else None,
            "n_trades_min": int(n_trades.min()) if len(computed) and pd.notna(n_trades.min()) else None,
            "risk_flag": bool(len(computed) != len(MULTISEED_SEEDS) or len(passing) < 4),
            "status": "COMPUTED" if len(computed) == len(group) else "INCOMPLETE",
            "diagnostic": "frozen_cutoff_seed_stress",
            "fixed_cutoff_policy": "source_rules_csv_score_cutoff_on_val_select",
            "winner_selected": False,
            "locked_test": "not_opened",
            "locked_test_status": "not_opened",
        }
        for optional_column in ("original_rank", "profile_id", "model_id", "target_id", "filter_id"):
            if optional_column in group.columns:
                row[optional_column] = first[optional_column]
        rows.append(row)
    if not rows:
        return pd.DataFrame(
            columns=[
                "rule_id",
                "computed_seed_count",
                "passing_seed_count",
                "pf_min",
                "pf_median",
                "bs_p05_min",
                "n_trades_min",
                "risk_flag",
                "status",
                "diagnostic",
                "fixed_cutoff_policy",
                "winner_selected",
                "locked_test",
                "locked_test_status",
            ]
        )
    out = pd.DataFrame(rows)
    if "original_rank" in out.columns:
        out = out.sort_values("original_rank").reset_index(drop=True)
    return out


def _truthy(value: object) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _classification_artifact_state(name: str, frame: pd.DataFrame, rule_id: str) -> tuple[list[str], bool, int]:
    if frame.empty or "rule_id" not in frame.columns:
        return [f"missing_{name}"], False, 0
    rows = frame.loc[frame["rule_id"].astype(str).eq(rule_id)].copy()
    if rows.empty:
        return [f"missing_{name}"], False, 0

    reasons: list[str] = []
    if "status" not in rows.columns:
        reasons.append(f"missing_status_{name}")
    else:
        statuses = rows["status"].astype(str).fillna("").tolist()
        bad_statuses = sorted({status for status in statuses if status != "COMPUTED"})
        if bad_statuses:
            reasons.append(f"noncomputed_{name}:{'|'.join(bad_statuses)}")

    risk_flagged = bool(rows["risk_flag"].map(_truthy).any()) if "risk_flag" in rows.columns else False
    return reasons, risk_flagged, int(len(rows))


def build_classification(
    manifest: pd.DataFrame,
    stress: pd.DataFrame,
    timezone: pd.DataFrame,
    permutation: pd.DataFrame,
    baseline: pd.DataFrame,
    multiseed: pd.DataFrame,
) -> pd.DataFrame:
    diagnostics = [
        ("stress_cost", stress),
        ("timezone_rescore", timezone),
        ("calendar_permutation", permutation),
        ("calendar_no_ml_baseline", baseline),
        ("multiseed", multiseed),
    ]
    records: list[dict[str, object]] = []
    for _, row in manifest.sort_values("original_rank").iterrows():
        rule_id = str(row["rule_id"])
        reasons: list[str] = []
        risk_reasons: list[str] = []
        row_counts: dict[str, int] = {}
        for name, frame in diagnostics:
            diagnostic_reasons, risk_flagged, row_count = _classification_artifact_state(name, frame, rule_id)
            reasons.extend(diagnostic_reasons)
            if risk_flagged:
                risk_reasons.append(f"risk_{name}")
            row_counts[f"{name}_row_count"] = row_count

        if reasons:
            decision = "INTERNAL_CLOSURE_INCOMPLETE"
        elif risk_reasons:
            decision = "INTERNAL_CLOSURE_RISK_FLAGGED"
        else:
            decision = "INTERNAL_CLOSURE_COMPUTED_RESEARCH_ONLY"

        records.append(
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": rule_id,
                "decision": decision,
                "reasons": ",".join(reasons),
                "risk_reasons": ",".join(risk_reasons),
                "risk_flag": bool(risk_reasons),
                "allowed_max_verdict": "research_only",
                "new_winner_selected": False,
                "locked_test": "not_opened",
                "locked_test_status": "not_opened",
                **row_counts,
            }
        )
    return pd.DataFrame(records)


def build_overall_decision(
    classification: pd.DataFrame,
    *,
    stress_status: str,
    timezone_rescore_status: str,
    calendar_permutation_status: str,
    calendar_baseline_status: str,
    multiseed_status: str,
) -> str:
    expected_statuses = [
        stress_status,
        timezone_rescore_status,
        calendar_permutation_status,
        calendar_baseline_status,
        multiseed_status,
    ]
    if any(str(status) != "COMPUTED" for status in expected_statuses):
        return "FIXED11_INTERNAL_CLOSURE_FAILED_RESEARCH_ONLY"
    decisions = set(classification["decision"].astype(str)) if "decision" in classification.columns else set()
    if not decisions or "INTERNAL_CLOSURE_INCOMPLETE" in decisions:
        return "FIXED11_INTERNAL_CLOSURE_FAILED_RESEARCH_ONLY"
    if "INTERNAL_CLOSURE_RISK_FLAGGED" in decisions:
        return "FIXED11_INTERNAL_CLOSURE_RISK_FLAGS_RESEARCH_ONLY"
    return "FIXED11_INTERNAL_CLOSURE_COMPLETE_RESEARCH_ONLY"


def _selected_leaderboard_rules(smoke_first_rule_only: bool) -> tuple[object, ...]:
    return leaderboard.LEADERBOARD_RULES[:1] if smoke_first_rule_only else leaderboard.LEADERBOARD_RULES


def _safe_float(value: object) -> float | None:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return None
    return float(numeric)


def _pf_drop_ratio(original_pf: object, changed_pf: object) -> float | None:
    original = _safe_float(original_pf)
    changed = _safe_float(changed_pf)
    if original is None or changed is None or original <= 0.0:
        return None
    return float(max(0.0, (original - changed) / original))


def _diagnostic_pf(summary: dict[str, object]) -> tuple[float | None, str]:
    pf = _safe_float(summary.get("pf"))
    gross_profit = _safe_float(summary.get("gross_profit")) or 0.0
    gross_loss = _safe_float(summary.get("gross_loss")) or 0.0
    if gross_loss == 0.0 and gross_profit > 0.0:
        return 99.0, PF_ZERO_LOSS_POLICY
    if gross_loss == 0.0 and gross_profit <= 0.0 and pf is None:
        return None, "gross_loss_zero_no_positive_profit_pf_null"
    return pf, "standard_gross_profit_div_gross_loss"


def _calendar_bucket_values(entries: pd.DataFrame, family: str) -> pd.Series:
    times = pd.to_datetime(entries["time"], errors="coerce")
    hour = times.dt.hour.astype("Int64")
    weekday = times.dt.weekday.astype("Int64")
    if family == "hour":
        return hour
    if family == "weekday":
        return weekday
    if family == "hour_weekday":
        return weekday.astype(str) + "_" + hour.astype(str)
    raise ValueError(f"unknown calendar baseline family: {family}")


def _write_feature_frame(path: Path, state: CalendarDiagnosticState, split: str) -> None:
    frame = state.feature_frames[split].copy()
    entries = state.entry_cache[split]
    frame.insert(0, "position_id", entries["position_id"].astype(str).to_numpy())
    frame.insert(1, "split_row_id", entries["split_row_id"].to_numpy())
    frame.insert(2, "split", split)
    frame.to_csv(path, sep=";", index=False)


def _score_and_summarize_state(
    state: CalendarDiagnosticState,
    split: str,
    feature_frame: pd.DataFrame,
) -> tuple[dict[str, object], pd.DataFrame]:
    scored = state.entry_cache[split].copy()
    scored["rich_entry_score"] = rich.score_rich_entry_model(state.model, feature_frame, state.target_kind)
    selected = rich.apply_entry_filter(scored, state.filter_rule, mode="eval", score_cutoff=state.cutoff)
    run = {
        **state.run_base,
        "split": split,
        "filter_id": state.filter_id,
        "filter_family": "rich_entry_quality",
        "top_fraction": state.filter_rule["top_fraction"],
        "score_cutoff_on_val_select": state.cutoff,
        "entry_filter_score_col": "rich_entry_score",
        "available_trades_before_filter": int(scored["filled"].sum()) if "filled" in scored else len(scored),
    }
    trades = rich._simulate_for_filter(selected, state.ohlc, run, state.scored_decisions[split], state.execution_ohlc)
    summary = rich._summary_for_filter(trades, run, split)
    summary.update(
        {
            "original_rank": state.original_rank,
            "rule_id": state.rule_id,
            "profile_id": state.profile_id,
            "model_id": state.model_id,
            "target_id": state.target_id,
            "filter_id": state.filter_id,
            "score_cutoff_on_val_select": state.cutoff,
        }
    )
    return summary, trades


def _build_calendar_diagnostic_states(
    output_prefix: Path,
    source_rules_csv: Path,
    threads: int,
    smoke_first_rule_only: bool,
) -> list[CalendarDiagnosticState]:
    fixed_cutoffs = load_saved_cutoffs(source_rules_csv)
    state_dir = output_prefix.with_name(output_prefix.name + "_canonical_feature_state")
    state_dir.mkdir(parents=True, exist_ok=True)

    choice = rich.load_stop_grid_choice("ML/reports/fractal0_entry_exit_grid_stop_policy.json", "")
    config = dataclasses.replace(
        rich.base.CONFIG,
        output_prefix=str(output_prefix),
        execution_ohlc_path="MT/MQL4/Files/XAUUSD_M5_OHLC.csv",
    )
    preflight = rich.base.preflight_inputs(config)
    if preflight["status"] != "PASS":
        raise ValueError(f"calendar diagnostic preflight failed: {preflight['errors']}")

    active_spread = 0.2
    ohlc = rich.base.load_ohlc(config)
    execution_ohlc = rich.base.prepare_execution_ohlc_index(rich.base.load_ohlc_path(config.execution_ohlc_path))
    splits = rich.base.load_role_splits(config)
    frozen_scores = rich.base._read_frozen_scores(config)

    stop_policy = choice["stop_policy"]
    exit_rule = choice["exit_rule"]
    run_base = {**stop_policy, **rich._entry_rule(), **{"mask_id": rich.MASK_ID, "kind": "none"}, **exit_rule, "spread": active_spread}
    entry_cache: dict[str, pd.DataFrame] = {}
    labels_by_split: dict[str, pd.DataFrame] = {}
    for split, rows in splits.items():
        entries = rich.base.build_entry_rows(rows, ohlc, rich._entry_rule(), active_spread, stop_policy)
        entries = rich.attach_movement_scores(entries, frozen_scores, split)
        entry_cache[split] = entries
        simulated = rich.base._simulate_entries(entries, ohlc, run_base, active_spread, pd.DataFrame(), execution_ohlc)
        labels = rich.build_rich_entry_labels(entries, simulated)
        labels["split"] = split
        labels["side"] = entries["side"].to_numpy() if "side" in entries else pd.NA
        labels["time"] = entries["time"].to_numpy() if "time" in entries else pd.NaT
        labels_by_split[split] = labels

    exit_cache = {("train_core", str(stop_policy["stop_policy_id"]), rich.ENTRY_ID, rich.MASK_ID): entry_cache["train_core"]}
    ml_models, _target_rates = rich.base._train_ml_exit_layer(
        exit_cache,
        ohlc,
        int(threads),
        seeds=rich.base.EXIT_MODEL_SEEDS,
        n_estimators=200,
    )
    scored_decisions: dict[str, pd.DataFrame] = {}
    for split in ("val_select", "val_eval"):
        decisions = rich.base.build_exit_decision_rows(entry_cache[split].loc[entry_cache[split]["filled"].astype(bool)], ohlc)
        scored_decisions[split] = rich.base.score_exit_models({rich.MASK_ID: ml_models[str(stop_policy["stop_policy_id"])][rich.MASK_ID]}, decisions)

    profiles = rich.rich_feature_profile_grid()
    models = rich.rich_model_grid(include_diagnostic_models=True)
    targets = rich.rich_target_grid()
    filters = rich.rich_filter_grid()
    rules = _selected_leaderboard_rules(smoke_first_rule_only)
    job_list = rich.build_fixed_leaderboard_job_list(profiles, models, targets, filters, rules)

    normalized_schemas_by_profile: dict[str, rich.NormalizedFeatureSchema] = {}
    normalized_scalers_by_profile: dict[str, dict[str, dict[str, float]]] = {}
    normalized_feature_frame_cache: dict[tuple[str, str], pd.DataFrame] = {}

    def get_feature_frame(split: str, profile_id: str) -> pd.DataFrame:
        cache_key = (split, profile_id)
        if cache_key in normalized_feature_frame_cache:
            return normalized_feature_frame_cache[cache_key]
        if profile_id not in normalized_schemas_by_profile:
            raw_profile_frames: dict[str, pd.DataFrame] = {}
            for split_name in ("train_core", "val_select", "val_eval"):
                raw_frame, _contract_rows = rich.build_normalized_rich_feature_frame(
                    entry_cache[split_name],
                    ohlc,
                    profile_id,
                    timezone_shift_hours=0,
                )
                raw_profile_frames[split_name] = raw_frame
            schema = rich.build_normalized_feature_schema(profile_id, raw_profile_frames["train_core"])
            scaler = rich.fit_unit_scaler({"train_core": raw_profile_frames["train_core"]}, schema)
            normalized_schemas_by_profile[profile_id] = schema
            normalized_scalers_by_profile[profile_id] = scaler
            for split_name, raw_frame in raw_profile_frames.items():
                scaled = rich.apply_unit_scaler(raw_frame, scaler, schema)
                rich.assert_unit_scaled_frame(scaled, profile_id)
                normalized_feature_frame_cache[(split_name, profile_id)] = scaled
        return normalized_feature_frame_cache[cache_key]

    states: list[CalendarDiagnosticState] = []
    manifest_rows: list[dict[str, object]] = []
    for profile, model_spec, target_spec, filter_spec, job_meta in job_list:
        profile_id = str(profile["profile_id"])
        model_id = str(model_spec["model_id"])
        target_id = str(target_spec["target_id"])
        target_kind = str(target_spec["kind"])
        rule_id = str(job_meta["rule_id"])
        original_rank = int(job_meta["original_rank"])
        x_train = get_feature_frame("train_core", profile_id)
        x_fit, y_train = rich.prepare_rich_training_target(entry_cache["train_core"], x_train, labels_by_split["train_core"], target_id)
        model = rich.train_rich_entry_model(x_fit, y_train, target_kind, model_id, int(threads), seed=42)
        feature_frames = {split: get_feature_frame(split, profile_id) for split in ("train_core", "val_select", "val_eval")}
        scored_entries: dict[str, pd.DataFrame] = {}
        for split in ("val_select", "val_eval"):
            scored = entry_cache[split].copy()
            scored["rich_entry_score"] = rich.score_rich_entry_model(model, feature_frames[split], target_kind)
            scored["split"] = split
            scored["profile_id"] = profile_id
            scored["model_id"] = model_id
            scored["target_id"] = target_id
            scored["filter_id"] = filter_spec["filter_id"]
            scored_entries[split] = scored

        filter_rule = rich._rich_filter_rule(filter_spec)
        preview_selected = rich.apply_entry_filter(scored_entries["val_select"], filter_rule, mode="select")
        cutoff = rich.resolve_fixed_cutoff(rule_id, fixed_cutoffs, preview_selected)
        summaries: dict[str, dict[str, object]] = {}
        for split in ("val_select", "val_eval"):
            selected = rich.apply_entry_filter(scored_entries[split], filter_rule, mode="eval", score_cutoff=cutoff)
            run = {
                **run_base,
                "split": split,
                "filter_id": filter_spec["filter_id"],
                "filter_family": "rich_entry_quality",
                "top_fraction": filter_spec["top_fraction"],
                "score_cutoff_on_val_select": cutoff,
                "entry_filter_score_col": "rich_entry_score",
                "available_trades_before_filter": int(scored_entries[split]["filled"].sum()) if "filled" in scored_entries[split] else len(scored_entries[split]),
            }
            trades = rich._simulate_for_filter(selected, ohlc, run, scored_decisions[split], execution_ohlc)
            summary = rich._summary_for_filter(trades, run, split)
            summary.update(
                {
                    "original_rank": original_rank,
                    "rule_id": rule_id,
                    "profile_id": profile_id,
                    "model_id": model_id,
                    "target_id": target_id,
                    "filter_id": filter_spec["filter_id"],
                    "score_cutoff_on_val_select": cutoff,
                }
            )
            summaries[split] = summary

        model_path = state_dir / f"rank{original_rank:02d}_{rule_id}_model.pkl"
        with model_path.open("wb") as handle:
            pickle.dump(model, handle)
        scaler_path = state_dir / f"rank{original_rank:02d}_{rule_id}_scaler.json"
        scaler_payload = {
            "rule_id": rule_id,
            "profile_id": profile_id,
            "scaler_scope": "train_core_only",
            "unit_scaler": normalized_scalers_by_profile.get(profile_id, {}),
            "feature_schema": asdict(normalized_schemas_by_profile[profile_id]),
        }
        scaler_path.write_text(json.dumps(scaler_payload, ensure_ascii=True, indent=2, default=str), encoding="utf-8")

        state = CalendarDiagnosticState(
            original_rank=original_rank,
            rule_id=rule_id,
            profile_id=profile_id,
            model_id=model_id,
            target_id=target_id,
            filter_id=str(filter_spec["filter_id"]),
            target_kind=target_kind,
            cutoff=float(cutoff),
            model=model,
            feature_frames=feature_frames,
            scored_entries=scored_entries,
            entry_cache=entry_cache,
            scored_decisions=scored_decisions,
            run_base=run_base,
            filter_rule=filter_rule,
            summaries=summaries,
            ohlc=ohlc,
            execution_ohlc=execution_ohlc,
            model_path=model_path,
            scaler_path=scaler_path,
        )
        states.append(state)
        for split in ("train_core", "val_select", "val_eval"):
            feature_frame_path = state_dir / f"rank{original_rank:02d}_{rule_id}_{split}_features.csv"
            _write_feature_frame(feature_frame_path, state, split)
            manifest_rows.append(
                {
                    "rule_id": rule_id,
                    "original_rank": original_rank,
                    "split": split,
                    "profile_id": profile_id,
                    "model_id": model_id,
                    "target_id": target_id,
                    "feature_frame_path": str(feature_frame_path),
                    "feature_frame_sha256": _sha256_file(feature_frame_path),
                    "scaler_scope": "train_core_only",
                    "scaler_path": str(scaler_path),
                    "model_seed": 42,
                    "model_path": str(model_path),
                    "status": "COMPUTED",
                    "locked_test": "not_opened",
                    "locked_test_status": "not_opened",
                }
            )

    manifest = pd.DataFrame(manifest_rows)
    manifest.to_csv(output_prefix.with_name(output_prefix.name + "_canonical_feature_state_manifest.csv"), sep=";", index=False)
    return states


def _permuted_calendar_frame(
    frame: pd.DataFrame,
    entries: pd.DataFrame,
    calendar_columns: list[str],
    seed: int,
) -> tuple[pd.DataFrame, int, int]:
    out = frame.copy()
    available_columns = [column for column in calendar_columns if column in out.columns]
    if not available_columns:
        return out, 0, 0

    group_frame = pd.DataFrame(index=out.index)
    if "year" in entries.columns:
        group_frame["year"] = pd.to_numeric(entries["year"], errors="coerce").fillna(-1).astype(int).to_numpy()
    else:
        group_frame["year"] = pd.to_datetime(entries["time"], errors="coerce").dt.year.fillna(-1).astype(int).to_numpy()
    if "side" in entries.columns:
        group_frame["side"] = entries["side"].astype(str).fillna("").to_numpy()
    group_columns = ["year", "side"] if "side" in group_frame.columns else ["year"]

    rng = np.random.default_rng(seed)
    small_group_skipped_count = 0
    permuted_group_count = 0
    for _keys, group in group_frame.groupby(group_columns, dropna=False, sort=False):
        indexer = group.index
        if len(indexer) < CALENDAR_SMALL_GROUP_MIN_ROWS:
            small_group_skipped_count += int(len(indexer))
            continue
        permuted_group_count += 1
        for column in available_columns:
            values = out.loc[indexer, column].to_numpy(copy=True)
            rng.shuffle(values)
            out.loc[indexer, column] = values
    return out, small_group_skipped_count, permuted_group_count


def calendar_permutation_sensitivity(
    output_prefix: Path,
    source_rules_csv: Path = SOURCE_RULES_CSV,
    threads: int = 24,
    smoke_first_rule_only: bool = False,
    permutation_repeats: int = CALENDAR_PERMUTATION_REPEATS,
    states: list[CalendarDiagnosticState] | None = None,
) -> pd.DataFrame:
    output_prefix = Path(output_prefix)
    diagnostic_states = states if states is not None else _build_calendar_diagnostic_states(
        output_prefix,
        Path(source_rules_csv),
        threads=int(threads),
        smoke_first_rule_only=bool(smoke_first_rule_only),
    )
    rows: list[dict[str, object]] = []
    for state in diagnostic_states:
        calendar_columns = calendar_feature_columns(state.profile_id)
        original_summary = state.summaries["val_eval"]
        pf_original = _safe_float(original_summary.get("pf"))
        if not calendar_columns:
            rows.append(
                {
                    "original_rank": state.original_rank,
                    "rule_id": state.rule_id,
                    "profile_id": state.profile_id,
                    "model_id": state.model_id,
                    "target_id": state.target_id,
                    "filter_id": state.filter_id,
                    "status": "COMPUTED",
                    "permutation_status": "NO_CALENDAR_FEATURES",
                    "permutation_repeats": int(permutation_repeats),
                    "calendar_feature_count": 0,
                    "pf_original": pf_original,
                    "pf_permuted_median": pf_original,
                    "pf_drop_ratio": 0.0,
                    "risk_flag": False,
                    "row_count_preserved": True,
                    "small_group_skipped_count": 0,
                    "locked_test": "not_opened",
                    "locked_test_status": "not_opened",
                }
            )
            continue

        permuted_pfs: list[float] = []
        small_group_skipped_total = 0
        permuted_group_total = 0
        for repeat_index in range(int(permutation_repeats)):
            seed = 1000 + int(state.original_rank) + repeat_index
            permuted, small_group_skipped_count, permuted_group_count = _permuted_calendar_frame(
                state.feature_frames["val_eval"],
                state.entry_cache["val_eval"],
                calendar_columns,
                seed=seed,
            )
            small_group_skipped_total += small_group_skipped_count
            permuted_group_total += permuted_group_count
            summary, _trades = _score_and_summarize_state(state, "val_eval", permuted)
            permuted_pf = _safe_float(summary.get("pf"))
            if permuted_pf is not None:
                permuted_pfs.append(permuted_pf)
        pf_permuted_median = float(np.median(permuted_pfs)) if permuted_pfs else None
        pf_drop_ratio = _pf_drop_ratio(pf_original, pf_permuted_median)
        rows.append(
            {
                "original_rank": state.original_rank,
                "rule_id": state.rule_id,
                "profile_id": state.profile_id,
                "model_id": state.model_id,
                "target_id": state.target_id,
                "filter_id": state.filter_id,
                "status": "COMPUTED",
                "permutation_status": "COMPUTED",
                "permutation_repeats": int(permutation_repeats),
                "permutation_repeats_with_pf": int(len(permuted_pfs)),
                "calendar_features": ",".join(calendar_columns),
                "calendar_feature_count": int(len(calendar_columns)),
                "pf_original": pf_original,
                "pf_permuted_median": pf_permuted_median,
                "pf_drop_ratio": pf_drop_ratio,
                "risk_flag": bool(pf_drop_ratio is not None and pf_drop_ratio > 0.30),
                "row_count_preserved": True,
                "index_alignment_preserved": True,
                "non_calendar_features_preserved": True,
                "grouping": "year_side",
                "small_group_min_rows": CALENDAR_SMALL_GROUP_MIN_ROWS,
                "small_group_skipped_count": int(small_group_skipped_total),
                "permuted_group_count": int(permuted_group_total),
                "deterministic_seed_formula": "1000 + original_rank + repeat_index",
                "locked_test": "not_opened",
                "locked_test_status": "not_opened",
            }
        )
    out = pd.DataFrame(rows).sort_values("original_rank").reset_index(drop=True)
    out.to_csv(output_prefix.with_name(output_prefix.name + "_calendar_permutation_importance.csv"), sep=";", index=False)
    return out


def _calendar_baseline_summary(
    state: CalendarDiagnosticState,
    split: str,
    family: str,
    bucket_value: object,
) -> dict[str, object]:
    entries = state.entry_cache[split].copy()
    buckets = _calendar_bucket_values(entries, family)
    selected = entries.loc[buckets.eq(bucket_value)].copy()
    run = {
        **state.run_base,
        "split": split,
        "filter_id": f"calendar_{family}",
        "filter_family": "calendar_no_ml_baseline",
        "top_fraction": None,
        "score_cutoff_on_val_select": None,
        "entry_filter_score_col": "calendar_bucket_only_no_rich_entry_score",
        "available_trades_before_filter": int(entries["filled"].sum()) if "filled" in entries else len(entries),
    }
    trades = rich._simulate_for_filter(selected, state.ohlc, run, state.scored_decisions[split], state.execution_ohlc)
    summary = rich._summary_for_filter(trades, run, split)
    pf, policy = _diagnostic_pf(summary)
    summary["pf"] = pf
    summary.update(
        {
            "calendar_family": family,
            "calendar_bucket": str(bucket_value),
            "calendar_bucket_raw": bucket_value,
            "pf_zero_loss_policy": policy,
        }
    )
    return summary


def calendar_no_ml_baseline(
    output_prefix: Path,
    source_rules_csv: Path = SOURCE_RULES_CSV,
    threads: int = 24,
    smoke_first_rule_only: bool = False,
    states: list[CalendarDiagnosticState] | None = None,
) -> pd.DataFrame:
    output_prefix = Path(output_prefix)
    diagnostic_states = states if states is not None else _build_calendar_diagnostic_states(
        output_prefix,
        Path(source_rules_csv),
        threads=int(threads),
        smoke_first_rule_only=bool(smoke_first_rule_only),
    )
    rows: list[dict[str, object]] = []
    for state in diagnostic_states:
        candidate_rows: list[dict[str, object]] = []
        for family in CALENDAR_BASELINE_FAMILIES:
            buckets = _calendar_bucket_values(state.entry_cache["val_select"], family).dropna().drop_duplicates().tolist()
            for bucket_value in buckets:
                summary = _calendar_baseline_summary(state, "val_select", family, bucket_value)
                candidate_rows.append(
                    {
                        "calendar_family": family,
                        "calendar_bucket": str(bucket_value),
                        "calendar_bucket_raw": bucket_value,
                        "n_trades_val_select": int(summary.get("n_trades") or 0),
                        "pf_val_select": _safe_float(summary.get("pf")),
                        "bs_p05_val_select": _safe_float(summary.get("bs_p05")),
                        "pf_zero_loss_policy": summary.get("pf_zero_loss_policy"),
                    }
                )
        candidates = pd.DataFrame(candidate_rows)
        if not candidates.empty:
            eligible = candidates.loc[
                (pd.to_numeric(candidates["n_trades_val_select"], errors="coerce") >= CALENDAR_BUCKET_MIN_TRADES)
                & (pd.to_numeric(candidates["pf_val_select"], errors="coerce") >= CALENDAR_BASELINE_MIN_PF)
                & (pd.to_numeric(candidates["bs_p05_val_select"], errors="coerce") >= CALENDAR_BASELINE_MIN_BS_P05)
            ].copy()
        else:
            eligible = pd.DataFrame()

        ml_pf = _safe_float(state.summaries["val_eval"].get("pf"))
        base_row = {
            "original_rank": state.original_rank,
            "rule_id": state.rule_id,
            "profile_id": state.profile_id,
            "model_id": state.model_id,
            "target_id": state.target_id,
            "filter_id": state.filter_id,
            "status": "COMPUTED",
            "baseline_family_count": int(len(CALENDAR_BASELINE_FAMILIES)),
            "bucket_min_trades_val_select": CALENDAR_BUCKET_MIN_TRADES,
            "bucket_min_pf_val_select": CALENDAR_BASELINE_MIN_PF,
            "bucket_min_bs_p05_val_select": CALENDAR_BASELINE_MIN_BS_P05,
            "ml_pf_val_eval": ml_pf,
            "ml_n_trades_val_eval": int(state.summaries["val_eval"].get("n_trades") or 0),
            "selection_split": "val_select",
            "evaluation_split": "val_eval",
            "uses_rich_entry_score": False,
            "locked_test": "not_opened",
            "locked_test_status": "not_opened",
        }
        if eligible.empty:
            rows.append(
                {
                    **base_row,
                    "baseline_selection_status": "NO_ELIGIBLE_BUCKETS",
                    "eligible_bucket_count": 0,
                    "selected_family": None,
                    "selected_bucket": None,
                    "baseline_pf_val_eval": None,
                    "baseline_n_trades_val_eval": 0,
                    "baseline_to_ml_pf_ratio": None,
                    "pf_zero_loss_policy": None,
                    "risk_flag": False,
                }
            )
            continue

        eligible = eligible.sort_values(
            ["bs_p05_val_select", "pf_val_select", "n_trades_val_select", "calendar_family", "calendar_bucket"],
            ascending=[False, False, False, True, True],
        )
        selected = eligible.iloc[0].to_dict()
        eval_summary = _calendar_baseline_summary(
            state,
            "val_eval",
            str(selected["calendar_family"]),
            selected["calendar_bucket_raw"],
        )
        baseline_pf = _safe_float(eval_summary.get("pf"))
        ratio = float(baseline_pf / ml_pf) if baseline_pf is not None and ml_pf is not None and ml_pf > 0.0 else None
        rows.append(
            {
                **base_row,
                "baseline_selection_status": "SELECTED_ON_VAL_SELECT",
                "eligible_bucket_count": int(len(eligible)),
                "selected_family": selected["calendar_family"],
                "selected_bucket": selected["calendar_bucket"],
                "selected_pf_val_select": selected["pf_val_select"],
                "selected_bs_p05_val_select": selected["bs_p05_val_select"],
                "selected_n_trades_val_select": selected["n_trades_val_select"],
                "baseline_pf_val_eval": baseline_pf,
                "baseline_bs_p05_val_eval": _safe_float(eval_summary.get("bs_p05")),
                "baseline_n_trades_val_eval": int(eval_summary.get("n_trades") or 0),
                "baseline_to_ml_pf_ratio": ratio,
                "pf_zero_loss_policy": eval_summary.get("pf_zero_loss_policy"),
                "risk_flag": bool(ratio is not None and ratio >= 0.80),
            }
        )
    out = pd.DataFrame(rows).sort_values("original_rank").reset_index(drop=True)
    out.to_csv(output_prefix.with_name(output_prefix.name + "_calendar_no_ml_baselines.csv"), sep=";", index=False)
    return out


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    if not frame.empty:
        frame.to_csv(path, sep=";", index=False)
    else:
        pd.DataFrame().to_csv(path, sep=";", index=False)


def _classification_manifest(smoke_first_rule_only: bool) -> pd.DataFrame:
    manifest = fixed_rule_manifest_frame()
    if smoke_first_rule_only:
        manifest = manifest.loc[manifest["original_rank"].eq(1)].copy()
    return manifest.reset_index(drop=True)


def _status_counts(frame: pd.DataFrame) -> dict[str, int]:
    if frame.empty or "status" not in frame.columns:
        return {}
    return {str(status): int(count) for status, count in frame["status"].astype(str).value_counts().sort_index().items()}


def _risk_summary(frame: pd.DataFrame) -> dict[str, object]:
    if frame.empty or "risk_flag" not in frame.columns:
        return {"any": False, "flagged_count": 0, "row_count": int(len(frame))}
    flags = frame["risk_flag"].map(_truthy)
    return {
        "any": bool(flags.any()),
        "flagged_count": int(flags.sum()),
        "row_count": int(len(frame)),
    }


def _source_input_metadata(source_prefix: Path, verified: dict[str, object]) -> dict[str, object]:
    loaded = verified.get("loaded", {}) if isinstance(verified, dict) else {}
    artifact = loaded.get("artifact", {}) if isinstance(loaded, dict) else {}
    source_json = source_prefix.with_suffix(".json")
    metadata: dict[str, object] = {
        "source_input_prefix": str(source_prefix),
        "source_input_json": str(source_json),
        "source_input_artifact_hashes": artifact.get("input_artifact_hashes", {}) if isinstance(artifact, dict) else {},
    }
    if source_json.exists():
        metadata["source_input_json_sha256"] = _sha256_file(source_json)
    return metadata


def run_internal_closure(args: argparse.Namespace) -> dict[str, object]:
    output_prefix = Path(args.output_prefix)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    source_prefix = Path(args.source_prefix)
    source_rules_csv = Path(args.source_rules_csv)
    run_groups = _parse_run_groups(args.run_groups)
    verified = _guard_locked_test_not_opened(source_prefix)
    load_saved_cutoffs(source_rules_csv)

    matrix = build_internal_run_matrix(smoke_first_rule_only=bool(args.smoke_first_rule_only))
    matrix = matrix.loc[matrix["run_group"].astype(str).isin(run_groups)].copy().reset_index(drop=True)
    matrix_path = output_prefix.with_name(output_prefix.name + "_run_matrix.csv")
    matrix.to_csv(matrix_path, sep=";", index=False)

    child_runs: list[dict[str, object]] = []
    resume_enabled = not bool(args.no_resume)
    stress = pd.DataFrame()
    stress_status = "NOT_REQUESTED"
    if "stress_cost" in run_groups:
        stress_matrix = matrix.loc[matrix["run_group"].eq("stress_cost")].copy()
        stress_frames = []
        for spread in STRESS_SPREADS:
            run_prefix = _run_prefix(output_prefix, "stress_cost", 42, float(spread), 0)
            child_runs.append(
                _run_rich_fixed_once_or_resume(
                    output_prefix=run_prefix,
                    seed=42,
                    spread=float(spread),
                    timezone_shift_hours=0,
                    fixed_cutoffs_csv=source_rules_csv,
                    threads=int(args.threads),
                    smoke_first_rule_only=bool(args.smoke_first_rule_only),
                    no_resume=bool(args.no_resume),
                )
            )
            stress_frames.append(
                collect_stress_cost(
                    run_prefix,
                    stress_matrix.loc[stress_matrix["spread"].astype(float).eq(float(spread))].copy(),
                )
            )
        stress = pd.concat(stress_frames, ignore_index=True) if stress_frames else pd.DataFrame()
        stress_status = "COMPUTED_SMOKE" if args.smoke_first_rule_only else "COMPUTED"

    timezone_rescore = pd.DataFrame()
    calendar_permutation = pd.DataFrame()
    calendar_baseline = pd.DataFrame()
    multiseed = pd.DataFrame()
    multiseed_aggregate = pd.DataFrame()
    timezone_rescore_status = "NOT_REQUESTED"
    calendar_permutation_status = "NOT_REQUESTED"
    calendar_baseline_status = "NOT_REQUESTED"
    multiseed_status = "NOT_REQUESTED"
    if "timezone_calendar" in run_groups:
        timezone_matrix = matrix.loc[matrix["run_group"].eq("timezone_calendar")].copy()
        timezone_frames = []
        for shift in TIMEZONE_SHIFT_HOURS:
            run_prefix = _run_prefix(output_prefix, "timezone_calendar", 42, 0.2, int(shift))
            child_runs.append(
                _run_rich_fixed_once_or_resume(
                    output_prefix=run_prefix,
                    seed=42,
                    spread=0.2,
                    timezone_shift_hours=int(shift),
                    fixed_cutoffs_csv=source_rules_csv,
                    threads=int(args.threads),
                    smoke_first_rule_only=bool(args.smoke_first_rule_only),
                    no_resume=bool(args.no_resume),
                )
            )
            timezone_frames.append(
                collect_timezone_rescore(
                    run_prefix,
                    timezone_matrix.loc[timezone_matrix["timezone_shift_hours"].astype(int).eq(int(shift))].copy(),
                )
            )
        timezone_rescore = pd.concat(timezone_frames, ignore_index=True) if timezone_frames else pd.DataFrame()
        timezone_rescore_status = "COMPUTED_SMOKE" if args.smoke_first_rule_only else "COMPUTED"
        calendar_states = _build_calendar_diagnostic_states(
            output_prefix=output_prefix,
            source_rules_csv=source_rules_csv,
            threads=int(args.threads),
            smoke_first_rule_only=bool(args.smoke_first_rule_only),
        )
        calendar_permutation = calendar_permutation_sensitivity(
            output_prefix=output_prefix,
            source_rules_csv=source_rules_csv,
            threads=int(args.threads),
            smoke_first_rule_only=bool(args.smoke_first_rule_only),
            permutation_repeats=int(args.calendar_permutation_repeats),
            states=calendar_states,
        )
        calendar_baseline = calendar_no_ml_baseline(
            output_prefix=output_prefix,
            source_rules_csv=source_rules_csv,
            threads=int(args.threads),
            smoke_first_rule_only=bool(args.smoke_first_rule_only),
            states=calendar_states,
        )
        calendar_permutation_status = "COMPUTED_SMOKE" if args.smoke_first_rule_only else "COMPUTED"
        calendar_baseline_status = "COMPUTED_SMOKE" if args.smoke_first_rule_only else "COMPUTED"

    if "multiseed" in run_groups:
        multiseed_matrix = matrix.loc[matrix["run_group"].eq("multiseed")].copy()
        multiseed_frames = []
        for seed in MULTISEED_SEEDS:
            run_prefix = _run_prefix(output_prefix, "multiseed", int(seed), 0.2, 0)
            child_runs.append(
                _run_rich_fixed_once_or_resume(
                    output_prefix=run_prefix,
                    seed=int(seed),
                    spread=0.2,
                    timezone_shift_hours=0,
                    fixed_cutoffs_csv=source_rules_csv,
                    threads=int(args.threads),
                    smoke_first_rule_only=bool(args.smoke_first_rule_only),
                    no_resume=bool(args.no_resume),
                )
            )
            multiseed_frames.append(
                collect_multiseed(
                    run_prefix,
                    multiseed_matrix.loc[multiseed_matrix["seed"].astype(int).eq(int(seed))].copy(),
                )
            )
        multiseed = pd.concat(multiseed_frames, ignore_index=True) if multiseed_frames else pd.DataFrame()
        multiseed_aggregate = aggregate_multiseed(multiseed)
        multiseed_status = "COMPUTED_SMOKE" if args.smoke_first_rule_only else "COMPUTED"

    stress_path = output_prefix.with_name(output_prefix.name + "_stress_cost.csv")
    timezone_path = output_prefix.with_name(output_prefix.name + "_timezone_rescore.csv")
    calendar_permutation_path = output_prefix.with_name(output_prefix.name + "_calendar_permutation_importance.csv")
    calendar_baseline_path = output_prefix.with_name(output_prefix.name + "_calendar_no_ml_baselines.csv")
    multiseed_path = output_prefix.with_name(output_prefix.name + "_multiseed.csv")
    multiseed_aggregate_path = output_prefix.with_name(output_prefix.name + "_multiseed_aggregate.csv")
    canonical_state_manifest_path = output_prefix.with_name(output_prefix.name + "_canonical_feature_state_manifest.csv")
    classification_path = output_prefix.with_name(output_prefix.name + "_classification.csv")

    _write_csv(stress, stress_path)
    _write_csv(timezone_rescore, timezone_path)
    _write_csv(calendar_permutation, calendar_permutation_path)
    _write_csv(calendar_baseline, calendar_baseline_path)
    _write_csv(multiseed, multiseed_path)
    _write_csv(multiseed_aggregate, multiseed_aggregate_path)

    classification = build_classification(
        _classification_manifest(bool(args.smoke_first_rule_only)),
        stress,
        timezone_rescore,
        calendar_permutation,
        calendar_baseline,
        multiseed_aggregate,
    )
    classification.to_csv(classification_path, sep=";", index=False)
    overall_decision = build_overall_decision(
        classification,
        stress_status=stress_status,
        timezone_rescore_status=timezone_rescore_status,
        calendar_permutation_status=calendar_permutation_status,
        calendar_baseline_status=calendar_baseline_status,
        multiseed_status=multiseed_status,
    )

    metadata = source_rules_metadata(source_rules_csv)
    source_metadata = _source_input_metadata(source_prefix, verified)
    statuses = {
        "stress_cost": stress_status,
        "timezone_rescore": timezone_rescore_status,
        "timezone_calendar": timezone_rescore_status,
        "calendar_permutation": calendar_permutation_status,
        "calendar_no_ml_baseline": calendar_baseline_status,
        "multiseed": multiseed_status,
    }
    risk_flags = {
        "stress_cost": _risk_summary(stress),
        "timezone_rescore": _risk_summary(timezone_rescore),
        "calendar_permutation": _risk_summary(calendar_permutation),
        "calendar_no_ml_baseline": _risk_summary(calendar_baseline),
        "multiseed": _risk_summary(multiseed_aggregate),
        "classification": _risk_summary(classification),
    }
    input_artifact_hashes = {
        "source_rules_csv": metadata["source_rules_csv_sha256"],
        "source_input_json": source_metadata.get("source_input_json_sha256"),
        "source_input_artifact_hashes": source_metadata.get("source_input_artifact_hashes", {}),
    }
    run_matrix = {
        "path": str(matrix_path),
        "row_count": int(len(matrix)),
        "group_counts": {str(group): int(count) for group, count in matrix["run_group"].value_counts().sort_index().items()},
    }
    artifacts = {
        "json": str(output_prefix.with_suffix(".json")),
        "run_matrix_csv": str(matrix_path),
        "stress_cost_csv": str(stress_path),
        "timezone_rescore_csv": str(timezone_path),
        "calendar_permutation_importance_csv": str(calendar_permutation_path),
        "calendar_no_ml_baselines_csv": str(calendar_baseline_path),
        "multiseed_csv": str(multiseed_path),
        "multiseed_aggregate_csv": str(multiseed_aggregate_path),
        "classification_csv": str(classification_path),
        "canonical_feature_state_manifest_csv": str(canonical_state_manifest_path) if canonical_state_manifest_path.exists() else None,
    }
    artifact = {
        "status": "completed_smoke" if args.smoke_first_rule_only else "completed",
        "decision": overall_decision,
        "overall_decision": overall_decision,
        "verdict": "research_only",
        "locked_test": "not_opened",
        "locked_test_status": "not_opened",
        "allowed_max_verdict": "research_only",
        "new_winner_selected": False,
        "provider_drift_status": "NOT_IN_SCOPE",
        "transfer_status": "NOT_IN_SCOPE",
        "leaderboard_rule_count": int(len(_selected_leaderboard_rules(bool(args.smoke_first_rule_only)))),
        "run_groups": list(run_groups),
        "run_matrix": run_matrix,
        **source_metadata,
        "fixed_cutoff_source": str(source_rules_csv),
        "threads_requested": int(args.threads),
        "smoke_first_rule_only": bool(args.smoke_first_rule_only),
        "resume_enabled": resume_enabled,
        "resume_skipped_run_count": int(sum(1 for run in child_runs if run["status"] == "resume_skipped")),
        "child_runs": child_runs,
        "statuses": statuses,
        "risk_flags": risk_flags,
        "status_counts": {
            "stress_cost": _status_counts(stress),
            "timezone_rescore": _status_counts(timezone_rescore),
            "calendar_permutation": _status_counts(calendar_permutation),
            "calendar_no_ml_baseline": _status_counts(calendar_baseline),
            "multiseed": _status_counts(multiseed),
            "multiseed_aggregate": _status_counts(multiseed_aggregate),
            "classification": _status_counts(classification),
        },
        "classification_decision_counts": {
            str(decision): int(count)
            for decision, count in classification["decision"].value_counts().sort_index().items()
        },
        "input_artifact_hashes": input_artifact_hashes,
        "stress_cost_status": stress_status,
        "timezone_rescore_status": timezone_rescore_status,
        "timezone_calendar_status": timezone_rescore_status,
        "calendar_permutation_status": calendar_permutation_status,
        "calendar_no_ml_baseline_status": calendar_baseline_status,
        "multiseed_status": multiseed_status,
        "stress_spreads": list(STRESS_SPREADS),
        "timezone_shift_hours": list(TIMEZONE_SHIFT_HOURS),
        "multiseed_seeds": list(MULTISEED_SEEDS),
        "stress_row_count": int(len(stress)),
        "timezone_rescore_row_count": int(len(timezone_rescore)),
        "calendar_permutation_row_count": int(len(calendar_permutation)),
        "calendar_no_ml_baseline_row_count": int(len(calendar_baseline)),
        "multiseed_row_count": int(len(multiseed)),
        "multiseed_aggregate_row_count": int(len(multiseed_aggregate)),
        "classification_row_count": int(len(classification)),
        "calendar_permutation_repeats": int(args.calendar_permutation_repeats),
        "baseline_family_count": int(len(CALENDAR_BASELINE_FAMILIES)),
        "producer_level_computation": "rich.run_rich_entry_quality",
        "timezone_rescore_computation": "feature_rescore_rich_runner_fixed_saved_cutoffs",
        "calendar_diagnostics_computation": "computed_from_fresh_canonical_train_val_state_no_locked_test",
        "multiseed_computation": "frozen_cutoff_seed_stress_saved_cutoff_reuse",
        "stress_trade_required_columns": list(REQUIRED_STRESS_TRADE_COLUMNS),
        **metadata,
        **STRESS_COST_CONVENTION,
        "artifacts": artifacts,
    }
    output_prefix.with_suffix(".json").write_text(json.dumps(artifact, ensure_ascii=True, indent=2, default=str), encoding="utf-8")
    return artifact


def _write_unknown_contract_artifact(output_prefix: Path, exc: BaseException) -> None:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "status": "unknown_input_or_contract",
        "run_status": "failed",
        "decision": "UNKNOWN_INPUT_OR_CONTRACT",
        "locked_test": "not_opened",
        "locked_test_status": "not_opened",
        "allowed_max_verdict": "research_only",
        "new_winner_selected": False,
        "error_type": type(exc).__name__,
        "error": str(exc),
        "artifacts": {
            "json": str(output_prefix.with_suffix(".json")),
        },
    }
    output_prefix.with_suffix(".json").write_text(json.dumps(artifact, ensure_ascii=True, indent=2, default=str), encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fixed-11 internal closure rerun")
    parser.add_argument("--source-prefix", default=str(SOURCE_INPUT_PREFIX))
    parser.add_argument("--source-rules-csv", default=str(SOURCE_RULES_CSV))
    parser.add_argument("--output-prefix", default=str(CLOSURE_OUTPUT_PREFIX))
    parser.add_argument("--run-groups", default="stress_cost,timezone_calendar,multiseed")
    parser.add_argument("--threads", type=int, default=24)
    parser.add_argument("--smoke-first-rule-only", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--calendar-permutation-repeats", type=int, default=CALENDAR_PERMUTATION_REPEATS)
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return _build_parser().parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        run_internal_closure(args)
    except SystemExit as exc:
        _write_unknown_contract_artifact(Path(args.output_prefix), exc)
        return 1
    except Exception as exc:
        _write_unknown_contract_artifact(Path(args.output_prefix), exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
