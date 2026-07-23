from __future__ import annotations

# =============================================================================
# Файл: audit_time_only_robustness.py
# Назначение: Validation-slice audit fixed normalized time_only winner.
# Обновлён: 2026-07-23
# Зависимости:
#   Входные данные:
#     - ML/reports/fractal0_rich_entry_quality_normalized.json/csv
#   Выходные данные:
#     - ML/reports/time_only_robustness_audit*.json/csv
# Использование:
#   ./.venv/bin/python ML/baseline/audit_time_only_robustness.py --input-prefix ML/reports/fractal0_rich_entry_quality_normalized --output-prefix ML/reports/time_only_robustness_audit
# Примечания:
#   - locked_test не открывается; результат не выше research_only.
# =============================================================================

import argparse
import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ML.baseline import benchmark_fractal0_entry_exit_grid as base


DEFAULT_INPUT_PREFIX = Path("ML/reports/fractal0_rich_entry_quality_normalized")
DEFAULT_OUTPUT_PREFIX = Path("ML/reports/time_only_robustness_audit")


@dataclass(frozen=True)
class FixedRule:
    stop_policy_id: str
    entry_id: str
    mask_id: str
    exit_id: str
    spread: float
    profile_id: str
    model_id: str
    target_id: str
    filter_id: str
    entry_filter_score_col: str
    score_cutoff_on_val_select: float


EXPECTED_RULE = FixedRule(
    stop_policy_id="S2_fractal0_buffer_0_5_entry_floor_2",
    entry_id="E3_open_pullback_1_0atr",
    mask_id="M0_no_mask",
    exit_id="X2_ml_opposite_any_p0_50",
    spread=0.2,
    profile_id="time_only",
    model_id="linear",
    target_id="target_entry_ev_regression",
    filter_id="top30",
    entry_filter_score_col="rich_entry_score",
    score_cutoff_on_val_select=-0.026718184259660646,
)


SUMMARY_USECOLS = [
    "stop_policy_id",
    "entry_id",
    "mask_id",
    "exit_id",
    "split",
    "spread",
    "n_trades",
    "gross_profit",
    "gross_loss",
    "pf",
    "mean_pnl_r",
    "median_pnl_r",
    "max_drawdown_r",
    "win_rate",
    "bs_p05",
    "negative_years",
    "pf_without_best_year",
    "effective_profit_years",
    "n_years",
    "filter_id",
    "score_cutoff_on_val_select",
    "entry_filter_score_col",
    "profile_id",
    "model_id",
    "target_id",
]

TRADES_USECOLS = [
    "position_id",
    "split",
    "profile_id",
    "model_id",
    "target_id",
    "filter_id",
    "stop_policy_id",
    "entry_id",
    "mask_id",
    "exit_id",
    "spread",
    "side",
    "signal_time",
    "fill_time",
    "exit_time",
    "close_reason",
    "pnl_r",
    "hold_bars",
    "ambiguous",
]

SCORES_USECOLS = [
    "position_id",
    "split",
    "profile_id",
    "model_id",
    "target_id",
    "filter_id",
    "rich_entry_score",
]


def _csv(path: Path, usecols: list[str]) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", usecols=usecols)


def _resolve_project_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _file_metadata(path: Path) -> dict[str, object]:
    resolved = _resolve_project_path(path)
    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(path), "size_bytes": int(resolved.stat().st_size), "sha256": digest.hexdigest()}


def input_artifact_metadata(prefix: Path = DEFAULT_INPUT_PREFIX) -> dict[str, object]:
    return {
        "json": _file_metadata(prefix.with_suffix(".json")),
        "summary_csv": _file_metadata(prefix.with_name(prefix.name + "_summary.csv")),
        "trades_csv": _file_metadata(prefix.with_name(prefix.name + "_trades.csv")),
        "scores_csv": _file_metadata(prefix.with_name(prefix.name + "_scores.csv")),
    }


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


def _float_matches(value: object, expected: float) -> bool:
    try:
        return math.isclose(float(value), expected, rel_tol=0.0, abs_tol=1e-12)
    except (TypeError, ValueError):
        return False


def _winner_contract_checks(winner: dict[str, object], expected: FixedRule) -> dict[str, bool]:
    return {
        "stop_policy_id": winner.get("stop_policy_id") == expected.stop_policy_id,
        "entry_id": winner.get("entry_id") == expected.entry_id,
        "mask_id": winner.get("mask_id") == expected.mask_id,
        "exit_id": winner.get("exit_id") == expected.exit_id,
        "spread": _float_matches(winner.get("spread"), expected.spread),
        "profile_id": winner.get("profile_id") == expected.profile_id,
        "model_id": winner.get("model_id") == expected.model_id,
        "target_id": winner.get("target_id") == expected.target_id,
        "filter_id": winner.get("filter_id") == expected.filter_id,
        "entry_filter_score_col": winner.get("entry_filter_score_col") == expected.entry_filter_score_col,
        "score_cutoff_on_val_select": _float_matches(
            winner.get("score_cutoff_on_val_select"),
            expected.score_cutoff_on_val_select,
        ),
    }


def verify_fixed_rule_contract(artifact: dict[str, object], expected: FixedRule = EXPECTED_RULE) -> dict[str, object]:
    checks: dict[str, object] = {
        "locked_test": artifact.get("locked_test") == "not_opened",
        "feature_contract_variant": artifact.get("feature_contract_variant") == "normalized_atr_unit",
    }
    failed = [name for name, ok in checks.items() if not ok]
    actual: dict[str, object] = {}

    for source_name in ("selected_winner", "selected_winner_val_eval"):
        winner = artifact.get(source_name)
        if not isinstance(winner, dict):
            failed.append(f"{source_name}.missing")
            checks[source_name] = {"status": "FAIL", "checks": {}}
            actual[source_name] = None
            continue

        source_checks = _winner_contract_checks(winner, expected)
        source_failed = [f"{source_name}.{name}" for name, ok in source_checks.items() if not ok]
        failed.extend(source_failed)
        checks[source_name] = {"status": "PASS" if not source_failed else "FAIL", "checks": source_checks}
        actual[source_name] = {field: winner.get(field) for field in expected.__dataclass_fields__}

    if failed:
        raise ValueError(f"fixed rule contract failed: {failed}; expected={asdict(expected)}; actual={actual}")
    return {"status": "PASS", "checks": checks, "expected_rule": asdict(expected)}


def filter_fixed_rule_rows(frame: pd.DataFrame, rule: FixedRule = EXPECTED_RULE, split: str | None = None) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    mask = pd.Series(True, index=frame.index)
    exact_fields = {
        "stop_policy_id": rule.stop_policy_id,
        "entry_id": rule.entry_id,
        "mask_id": rule.mask_id,
        "exit_id": rule.exit_id,
        "profile_id": rule.profile_id,
        "model_id": rule.model_id,
        "target_id": rule.target_id,
        "filter_id": rule.filter_id,
    }
    for column, expected in exact_fields.items():
        if column in frame.columns:
            mask &= frame[column].astype(str).eq(str(expected))
    if "spread" in frame.columns:
        mask &= pd.to_numeric(frame["spread"], errors="coerce").eq(rule.spread)
    if split is not None and "split" in frame.columns:
        mask &= frame["split"].astype(str).eq(split)
    return frame.loc[mask].copy()


def _period_series(values: pd.Series, freq: str) -> pd.Series:
    dates = pd.to_datetime(values, errors="coerce")
    if freq == "Y":
        return dates.dt.year.astype("Int64").astype(str)
    if freq == "Q":
        return dates.dt.to_period("Q").astype(str)
    raise ValueError(f"unsupported freq: {freq}")


def _metrics_row(group: pd.DataFrame) -> dict[str, object]:
    return base.compute_trade_metrics(group)


def metrics_by_period(trades: pd.DataFrame, freq: str) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    frame = trades.copy()
    frame["period"] = _period_series(frame["exit_time"], freq)
    rows = [{"period": str(period), **_metrics_row(group)} for period, group in frame.groupby("period", dropna=False)]
    return pd.DataFrame(rows).sort_values("period").reset_index(drop=True)


def metrics_by_side(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = [{"side": str(side), **_metrics_row(group)} for side, group in trades.groupby("side", dropna=False)]
    return pd.DataFrame(rows).sort_values("side").reset_index(drop=True)


def metrics_by_year_side(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    frame = trades.copy()
    frame["year"] = _period_series(frame["exit_time"], "Y")
    rows = [{"year": str(year), "side": str(side), **_metrics_row(group)} for (year, side), group in frame.groupby(["year", "side"], dropna=False)]
    return pd.DataFrame(rows).sort_values(["year", "side"]).reset_index(drop=True)


def profit_concentration(trades: pd.DataFrame) -> dict[str, object]:
    yearly = base.yearly_metrics(trades)
    gross = np.array([max(0.0, float(row.get("gross_profit") or 0.0)) for row in yearly], dtype=float)
    total = float(gross.sum())
    shares = gross / total if total > 0 else np.zeros_like(gross)
    best_year_share = float(shares.max()) if len(shares) else 0.0
    return {
        "n_years": int(len(yearly)),
        "effective_profit_years": base.effective_profit_years_from_yearly(yearly),
        "best_year_share": best_year_share,
        "profitable_years": int(sum(float(row.get("mean_pnl_r") or 0.0) > 0.0 for row in yearly)),
        "min_year_pf": min([float(row["pf"]) for row in yearly if row.get("pf") is not None], default=None),
    }


def _sequential_block_sample_indices(n: int, seed: int, block_size: int) -> np.ndarray:
    if n <= 0:
        return np.array([], dtype=int)
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n, size=int(np.ceil(n / block_size)))
    blocks = [np.arange(start, start + block_size, dtype=int) % n for start in starts]
    return np.concatenate(blocks)[:n]


def sequential_block_bootstrap_pf(
    trades: pd.DataFrame,
    seed: int = 20260723,
    n_bootstrap: int = 1000,
    block_size: int = 20,
) -> dict[str, object]:
    pnl = pd.to_numeric(trades.get("pnl_r"), errors="coerce").dropna().to_numpy()
    if len(pnl) == 0:
        return {"bs_p05": None, "samples": 0, "bootstrap_method": "sequential_block", "block_size": block_size}
    values = []
    for i in range(n_bootstrap):
        idx = _sequential_block_sample_indices(len(pnl), seed + i, block_size)
        sample = pnl[idx]
        gross_profit = sample[sample > 0].sum()
        gross_loss = -sample[sample < 0].sum()
        values.append(float(gross_profit / gross_loss) if gross_loss > 0 else 99.0)
    return {
        "bs_p05": float(np.quantile(values, 0.05)),
        "samples": int(n_bootstrap),
        "bootstrap_method": "sequential_block",
        "block_size": int(block_size),
        "seed": int(seed),
    }


def score_shift(scores: pd.DataFrame, rule: FixedRule = EXPECTED_RULE) -> pd.DataFrame:
    fixed = filter_fixed_rule_rows(scores, rule)
    rows = []
    for split, group in fixed.groupby("split", dropna=False):
        values = pd.to_numeric(group["rich_entry_score"], errors="coerce").dropna()
        rows.append(
            {
                "split": str(split),
                "rows": int(len(group)),
                "valid_rows": int(len(values)),
                "mean_score": float(values.mean()) if len(values) else None,
                "p10": float(values.quantile(0.10)) if len(values) else None,
                "p50": float(values.quantile(0.50)) if len(values) else None,
                "p90": float(values.quantile(0.90)) if len(values) else None,
                "fraction_above_fixed_cutoff": float((values >= rule.score_cutoff_on_val_select).mean()) if len(values) else None,
            }
        )
    return pd.DataFrame(rows)


def stricter_cutoff_sensitivity(
    scores: pd.DataFrame,
    trades: pd.DataFrame,
    rule: FixedRule = EXPECTED_RULE,
    offsets: list[float] | None = None,
) -> pd.DataFrame:
    offsets = offsets or [0.0, 0.005, 0.01, 0.02]
    fixed_scores = filter_fixed_rule_rows(scores, rule, split="val_eval")
    fixed_trades = filter_fixed_rule_rows(trades, rule, split="val_eval")
    rows = []
    for offset in offsets:
        if offset < 0.0:
            raise ValueError("saved top30 trades cannot support looser cutoff; use topk_sensitivity instead")
        cutoff = rule.score_cutoff_on_val_select + float(offset)
        keep_ids = set(fixed_scores.loc[pd.to_numeric(fixed_scores["rich_entry_score"], errors="coerce") >= cutoff, "position_id"].astype(str))
        selected = fixed_trades.loc[fixed_trades["position_id"].astype(str).isin(keep_ids)].copy()
        rows.append({"cutoff": cutoff, "cutoff_offset": float(offset), **base.compute_trade_metrics(selected)})
    return pd.DataFrame(rows)


def topk_sensitivity(trades: pd.DataFrame, rule: FixedRule = EXPECTED_RULE) -> pd.DataFrame:
    rows = []
    for filter_id in ["top30", "top40", "top50"]:
        top_rule = FixedRule(**{**asdict(rule), "filter_id": filter_id})
        group = filter_fixed_rule_rows(trades, top_rule, split="val_eval")
        rows.append({"filter_id": filter_id, **base.compute_trade_metrics(group)})
    return pd.DataFrame(rows)


DECISION_GATE_CONFIG = {
    "side": {
        "min_pf": 1.0,
        "min_n_trades": 30,
        "max_drawdown_r": 8.5,
        "min_mean_pnl_r": 0.0,
    },
    "concentration": {
        "min_effective_profit_years_formula": "max(1.5, 0.6 * n_years)",
        "min_pf_without_best_year": 1.0,
    },
    "block_bootstrap": {
        "method": "sequential_block",
        "min_bs_p05": 1.0,
        "seed": 20260723,
        "n_bootstrap": 1000,
        "block_size": 20,
    },
    "stress_costs": {
        "required_for_slice_ok": True,
        "status_when_saved_artifacts_lack_resimulation": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
    },
    "stricter_cutoff": {
        "offsets": [0.0, 0.005, 0.01, 0.02],
        "min_n_trades": 300,
        "looser_cutoff_supported": False,
    },
    "topk": {
        "filter_ids": ["top30", "top40", "top50"],
        "min_required_rows": 3,
        "min_pf": 1.0,
        "min_n_trades": 300,
    },
    "sequential_position_constraint": {
        "required_for_slice_ok": False,
    },
}


def _calendar_rows(trades: pd.DataFrame, time_column: str) -> list[dict[str, object]]:
    if time_column not in trades.columns:
        return []
    frame = trades.copy()
    frame["_calendar_dt"] = pd.to_datetime(frame[time_column], errors="coerce")
    frame["month"] = frame["_calendar_dt"].dt.month
    frame["quarter"] = frame["_calendar_dt"].dt.quarter
    rows = []
    for field in ["month", "quarter"]:
        for value, group in frame.groupby(field, dropna=False):
            rows.append(
                {
                    "time_basis": time_column,
                    "calendar_field": field,
                    "calendar_value": int(value) if pd.notna(value) else None,
                    **base.compute_trade_metrics(group),
                }
            )
    return rows


def calendar_slices(trades: pd.DataFrame, rule: FixedRule = EXPECTED_RULE) -> pd.DataFrame:
    fixed_trades = filter_fixed_rule_rows(trades, rule, split="val_eval").copy()
    if fixed_trades.empty:
        return pd.DataFrame()
    rows = []
    for time_column in ["signal_time", "fill_time", "exit_time"]:
        rows.extend(_calendar_rows(fixed_trades, time_column))
    return pd.DataFrame(rows)


def calendar_no_ml_baselines(trades: pd.DataFrame, rule: FixedRule = EXPECTED_RULE) -> pd.DataFrame:
    base_rows = filter_fixed_rule_rows(trades, rule, split="val_eval")
    if "filter_id" in trades.columns:
        base_rows = filter_fixed_rule_rows(trades.drop(columns=["filter_id"]), rule, split="val_eval").join(trades["filter_id"])
    available_filters = sorted(str(value) for value in base_rows.get("filter_id", pd.Series(dtype=object)).dropna().unique())
    unfiltered_ids = {"all", "all_entries", "no_filter", "none", "unfiltered"}
    matching_ids = [filter_id for filter_id in available_filters if filter_id.lower() in unfiltered_ids]
    if not matching_ids:
        return pd.DataFrame(
            [
                {
                    "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
                    "reason": "unfiltered no-ML calendar baseline is not present in saved artifacts",
                    "available_filter_ids": ",".join(available_filters),
                }
            ]
        )
    rows = base_rows.loc[base_rows["filter_id"].astype(str).str.lower().isin(unfiltered_ids)].copy()
    rows["exit_dt"] = pd.to_datetime(rows["exit_time"], errors="coerce")
    rows["month"] = rows["exit_dt"].dt.month
    rows["weekday"] = rows["exit_dt"].dt.weekday
    rows["hour"] = rows["exit_dt"].dt.hour
    out = [{"baseline": "all_no_ml_entries", **base.compute_trade_metrics(rows)}]
    for field in ["hour", "weekday", "month"]:
        for value, group in rows.groupby(field, dropna=False):
            out.append({"baseline": f"no_ml_{field}", "calendar_value": int(value) if pd.notna(value) else None, **base.compute_trade_metrics(group)})
    return pd.DataFrame(out)


def spread_stress_status() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
                "reason": "saved trades contain realized pnl for canonical spread only; stress spread requires explicit resimulation",
            }
        ]
    )


def timezone_shift_status() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "status": "NOT_RUN",
                "reason": "requires predefined timezone-shift resimulation of time-only features; not available from this saved-artifact slice",
            }
        ]
    )


def calendar_permutation_importance_status() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "status": "NOT_RUN",
                "reason": "requires model-level permutation importance or a predefined calendar-feature ablation; not part of this fixed-rule artifact audit",
            }
        ]
    )


def sequential_position_status() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "status": "NOT_RUN",
                "reason": "plan records this diagnostic as missing unless an implementation adds position-overlap simulation",
            }
        ]
    )


def robustness_decision(
    selected_summary: dict[str, object],
    concentration: dict[str, object],
    side: pd.DataFrame,
    stricter_cutoff: pd.DataFrame,
    topk: pd.DataFrame,
    spread_stress: pd.DataFrame,
    sequential: pd.DataFrame,
) -> dict[str, object]:
    reasons: list[str] = []
    disclosures: list[str] = []
    gate = DECISION_GATE_CONFIG
    n_years = int(concentration.get("n_years") or 0)
    min_effective_years = max(1.5, 0.6 * n_years)
    if float(concentration.get("effective_profit_years") or 0.0) < min_effective_years:
        reasons.append("profit_concentration_fail")
    if float(selected_summary.get("bs_p05") or 0.0) < gate["block_bootstrap"]["min_bs_p05"]:
        reasons.append("block_bootstrap_fail")
    if float(selected_summary.get("pf_without_best_year") or 0.0) < gate["concentration"]["min_pf_without_best_year"]:
        reasons.append("pf_without_best_year_fail")
    if side.empty or (pd.to_numeric(side.get("mean_pnl_r"), errors="coerce") <= gate["side"]["min_mean_pnl_r"]).any():
        reasons.append("side_mean_fail")
    if side.empty or (pd.to_numeric(side.get("pf"), errors="coerce") < gate["side"]["min_pf"]).any():
        reasons.append("side_pf_fail")
    if side.empty or (pd.to_numeric(side.get("n_trades"), errors="coerce") < gate["side"]["min_n_trades"]).any():
        reasons.append("side_sample_fail")
    if side.empty or (pd.to_numeric(side.get("max_drawdown_r"), errors="coerce") > gate["side"]["max_drawdown_r"]).any():
        reasons.append("side_drawdown_warning")
    if stricter_cutoff.empty or pd.to_numeric(stricter_cutoff.get("n_trades"), errors="coerce").min() < gate["stricter_cutoff"]["min_n_trades"]:
        reasons.append("stricter_cutoff_sample_fragile")
    if topk.empty or len(topk) < gate["topk"]["min_required_rows"]:
        reasons.append("topk_sensitivity_missing")
    elif (
        (pd.to_numeric(topk.get("pf"), errors="coerce") < gate["topk"]["min_pf"]).any()
        or (pd.to_numeric(topk.get("n_trades"), errors="coerce") < gate["topk"]["min_n_trades"]).any()
    ):
        reasons.append("topk_sensitivity_fragile")
    if not spread_stress.empty and str(spread_stress.iloc[0].get("status")) == "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS":
        reasons.append("stress_costs_not_computable")
    if not sequential.empty and str(sequential.iloc[0].get("status")) == "NOT_RUN":
        if gate["sequential_position_constraint"]["required_for_slice_ok"]:
            reasons.append("sequential_position_constraint_not_run")
        else:
            disclosures.append("sequential_position_constraint_not_run")

    if any(reason in reasons for reason in ["block_bootstrap_fail", "pf_without_best_year_fail"]):
        decision = "REJECT_TIME_ONLY_AS_UNSTABLE"
    elif reasons:
        decision = "REGIME_REFORMULATION_REQUIRED"
    else:
        decision = "TIME_ONLY_ROBUSTNESS_SLICE_OK_FOR_NEXT_PROBE_DESIGN"
    return {"decision": decision, "reasons": reasons, "disclosures": disclosures, "decision_gate_config": gate}


def _selected_summary(summary: pd.DataFrame, rule: FixedRule = EXPECTED_RULE) -> dict[str, object]:
    fixed = filter_fixed_rule_rows(summary, rule, split="val_eval")
    if len(fixed) != 1:
        raise ValueError(f"fixed rule summary row expected once, got {len(fixed)}")
    return fixed.iloc[0].to_dict()


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, sep=";", index=False)


def run_audit(input_prefix: Path = DEFAULT_INPUT_PREFIX, output_prefix: Path = DEFAULT_OUTPUT_PREFIX) -> dict[str, object]:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    try:
        loaded = load_normalized_artifacts(input_prefix)
        artifact = loaded["artifact"]
        summary = loaded["summary"]
        trades = loaded["trades"]
        scores = loaded["scores"]
        contract = verify_fixed_rule_contract(artifact, EXPECTED_RULE)
        input_artifacts = input_artifact_metadata(input_prefix)
    except Exception as exc:
        unknown = {
            "experiment": "time_only_robustness_audit",
            "status": "UNKNOWN",
            "verdict": "research_only",
            "locked_test": None,
            "decision": {"decision": "UNKNOWN_ARTIFACT_CONTRACT", "reasons": [str(exc)]},
        "contract_errors": [str(exc)],
        }
        output_prefix.with_suffix(".json").write_text(json.dumps(unknown, indent=2, ensure_ascii=False), encoding="utf-8")
        return unknown

    fixed_trades = filter_fixed_rule_rows(trades, EXPECTED_RULE, split="val_eval")
    yearly = metrics_by_period(fixed_trades, "Y")
    quarterly = metrics_by_period(fixed_trades, "Q")
    side = metrics_by_side(fixed_trades)
    year_side = metrics_by_year_side(fixed_trades)
    shift = score_shift(scores, EXPECTED_RULE)
    stricter_cutoff = stricter_cutoff_sensitivity(scores, trades, EXPECTED_RULE)
    topk = topk_sensitivity(trades, EXPECTED_RULE)
    calendar_no_ml = calendar_no_ml_baselines(trades, EXPECTED_RULE)
    calendar = calendar_slices(trades, EXPECTED_RULE)
    spread_stress = spread_stress_status()
    timezone_shift = timezone_shift_status()
    calendar_permutation = calendar_permutation_importance_status()
    sequential = sequential_position_status()
    selected_summary = _selected_summary(summary, EXPECTED_RULE)
    concentration = profit_concentration(fixed_trades)
    bootstrap = sequential_block_bootstrap_pf(fixed_trades, seed=20260723, n_bootstrap=1000, block_size=20)
    selected_summary["bs_p05"] = bootstrap.get("bs_p05")
    decision = robustness_decision(selected_summary, concentration, side, stricter_cutoff, topk, spread_stress, sequential)

    artifacts = {
        "yearly_csv": output_prefix.with_name(output_prefix.name + "_yearly.csv"),
        "quarterly_csv": output_prefix.with_name(output_prefix.name + "_quarterly.csv"),
        "side_csv": output_prefix.with_name(output_prefix.name + "_side.csv"),
        "year_side_csv": output_prefix.with_name(output_prefix.name + "_year_side.csv"),
        "score_shift_csv": output_prefix.with_name(output_prefix.name + "_score_shift.csv"),
        "stricter_cutoff_csv": output_prefix.with_name(output_prefix.name + "_stricter_cutoff.csv"),
        "topk_sensitivity_csv": output_prefix.with_name(output_prefix.name + "_topk_sensitivity.csv"),
        "calendar_no_ml_baselines_csv": output_prefix.with_name(output_prefix.name + "_calendar_no_ml_baselines.csv"),
        "calendar_slices_csv": output_prefix.with_name(output_prefix.name + "_calendar_slices.csv"),
        "spread_stress_csv": output_prefix.with_name(output_prefix.name + "_spread_stress.csv"),
        "timezone_shift_csv": output_prefix.with_name(output_prefix.name + "_timezone_shift.csv"),
        "calendar_permutation_importance_csv": output_prefix.with_name(output_prefix.name + "_calendar_permutation_importance.csv"),
        "sequential_csv": output_prefix.with_name(output_prefix.name + "_sequential.csv"),
    }
    for frame, path in [
        (yearly, artifacts["yearly_csv"]),
        (quarterly, artifacts["quarterly_csv"]),
        (side, artifacts["side_csv"]),
        (year_side, artifacts["year_side_csv"]),
        (shift, artifacts["score_shift_csv"]),
        (stricter_cutoff, artifacts["stricter_cutoff_csv"]),
        (topk, artifacts["topk_sensitivity_csv"]),
        (calendar_no_ml, artifacts["calendar_no_ml_baselines_csv"]),
        (calendar, artifacts["calendar_slices_csv"]),
        (spread_stress, artifacts["spread_stress_csv"]),
        (timezone_shift, artifacts["timezone_shift_csv"]),
        (calendar_permutation, artifacts["calendar_permutation_importance_csv"]),
        (sequential, artifacts["sequential_csv"]),
    ]:
        _write_csv(frame, path)

    result = {
        "experiment": "time_only_robustness_audit",
        "status": "completed",
        "verdict": "research_only",
        "locked_test": "not_opened",
        "fixed_rule_contract": contract,
        "input_artifacts": input_artifacts,
        "source_input_artifact_hashes": artifact.get("input_artifact_hashes"),
        "selected_summary": selected_summary,
        "profit_concentration": concentration,
        "block_bootstrap": bootstrap,
        "scope": "validation_artifact_robustness_slice",
        "multi_seed_status": "NOT_RUN",
        "provider_drift_status": "NOT_RUN",
        "transfer_status": "NOT_RUN",
        "locked_test_status": "not_opened",
        "stress_costs_status": str(spread_stress.iloc[0]["status"]) if not spread_stress.empty else "UNKNOWN",
        "timezone_shift_status": str(timezone_shift.iloc[0]["status"]) if not timezone_shift.empty else "UNKNOWN",
        "calendar_permutation_importance_status": str(calendar_permutation.iloc[0]["status"]) if not calendar_permutation.empty else "UNKNOWN",
        "sequential_position_constraint_status": str(sequential.iloc[0]["status"]) if not sequential.empty else "UNKNOWN",
        "decision": decision,
        "forbidden_interpretations": ["candidate", "tradable", "live_ready", "production", "permission_to_open_locked_test"],
        "artifacts": {name: str(path) for name, path in artifacts.items()},
    }
    output_prefix.with_suffix(".json").write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit robustness of the fixed normalized time_only winner.")
    parser.add_argument("--input-prefix", default=str(DEFAULT_INPUT_PREFIX))
    parser.add_argument("--output-prefix", default=str(DEFAULT_OUTPUT_PREFIX))
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    result = run_audit(Path(args.input_prefix), Path(args.output_prefix))
    print(json.dumps({"status": result["status"], "decision": result["decision"]}, ensure_ascii=False))
    if result.get("status") == "UNKNOWN":
        sys.exit(1)


if __name__ == "__main__":
    main()
