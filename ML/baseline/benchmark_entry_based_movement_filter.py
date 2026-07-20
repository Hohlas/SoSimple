# =============================================================================
# File: benchmark_entry_based_movement_filter.py
# Purpose: bounded CLI for a simple no-direction movement filter derived from
#   the entry-based amplitude movement audit.
# Language: Python 3.10+
# =============================================================================

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler

from ML.baseline import benchmark_entry_based_amplitude_movement as amplitude


ALLOWED_PROFILES = ("time_plus_atr", "simple_combined")
ALLOWED_FRACTIONS = (0.05, 0.10, 0.20, 0.30)
ALLOWED_TARGET_FAMILY = "entry_movement"
ALLOWED_VERDICTS = (
    "ABORT_CONTRACT_FAIL",
    "MOVEMENT_FILTER_REJECTED",
    "SIMPLE_MOVEMENT_FILTER_RESEARCH_ONLY",
)
REQUIRED_PROFILES = ("time_plus_atr", "simple_combined")
REQUIRED_SPLITS = ("train", "val_select", "val_eval", "low_n_disclosure")
CANONICAL_SOURCE_PATH = Path("ML/reports/entry_based_amplitude_movement.json")
PROFILE_ORDER = {"time_plus_atr": 1, "simple_combined": 0}
HORIZON_ORDER = {3: 3, 6: 2, 12: 1, 24: 0}
SELECTION_POLICY = {
    "winner_metric": "val_select",
    "winner_unit": "top_fraction_filter",
    "val_eval": "check_only",
    "low_n_disclosure_2026": "disclosure_only",
    "locked_test": "not_opened",
    "direction_selection": "forbidden",
    "decision_time": "pre_entry_decision",
}


def load_amplitude_artifact(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_source_path(path: Path, *, allow_noncanonical_source: bool = False) -> None:
    """Require the canonical amplitude artifact unless a fixture run opts out."""

    if allow_noncanonical_source:
        return

    repo_root = Path(__file__).resolve().parents[2]
    expected = (repo_root / CANONICAL_SOURCE_PATH).resolve()
    actual = path.expanduser().resolve()
    if actual != expected:
        raise ValueError(
            "movement filter source must be "
            f"{CANONICAL_SOURCE_PATH}; got {path}. "
            "Use --allow-noncanonical-source only for tests/fixtures."
        )


def validate_source_artifact(artifact: dict) -> dict:
    reasons: list[str] = []

    selection_policy = artifact.get("selection_policy") or {}
    if selection_policy.get("locked_test") != "not_opened":
        reasons.append("locked_test")

    if not artifact.get("run_config_hash"):
        reasons.append("run_config_hash")

    audit_rows = artifact.get("feature_audit_rows") or []
    for profile in REQUIRED_PROFILES:
        passed_splits = {
            row.get("split")
            for row in audit_rows
            if row.get("profile") == profile
            and row.get("family") == "metadata"
            and row.get("decision") == "PASS"
        }
        if passed_splits != set(REQUIRED_SPLITS):
            reasons.append(f"feature_audit_rows:{profile}")

    return {
        "status": "ABORT_CONTRACT_FAIL" if reasons else "PASS",
        "reasons": reasons,
    }


def enumerate_filter_candidates(artifact: dict) -> list[dict]:
    seed_aggregate = artifact.get("seed_aggregate") or []

    best_rows: dict[tuple[object, object], dict] = {}
    for row in seed_aggregate:
        if row.get("profile") not in ALLOWED_PROFILES:
            continue
        if row.get("target_family") != ALLOWED_TARGET_FAMILY:
            continue
        if row.get("selection_eligible") is not True:
            continue
        if row.get("post_entry_diagnostic_only") is not False:
            continue

        key = (row.get("profile"), row.get("horizon"))
        score = row.get("val_select_spearman_median")
        current = best_rows.get(key)
        if current is None or score > current.get("val_select_spearman_median"):
            best_rows[key] = row

    candidates: list[dict] = []
    for key in sorted(best_rows):
        row = best_rows[key]
        for selected_fraction in ALLOWED_FRACTIONS:
            candidate = dict(row)
            candidate["selected_fraction"] = selected_fraction
            candidate["threshold_type"] = "top_fraction"
            candidate["threshold_value"] = selected_fraction
            candidate["selection_split"] = "val_select"
            candidates.append(candidate)

    return candidates


def validate_low_n_disclosure_years(frame: pd.DataFrame) -> None:
    if "time" not in frame.columns:
        raise ValueError("low_n_disclosure must contain only 2026 rows; found years=[]")

    parsed = pd.to_datetime(frame["time"], errors="coerce")
    if parsed.isna().any():
        raise ValueError("low_n_disclosure must contain only 2026 rows; found years=[]")

    years = parsed.dt.year.astype(int)
    unique_years = sorted(int(year) for year in years.unique())
    if unique_years != [2026]:
        raise ValueError(f"low_n_disclosure must contain only 2026 rows; found years={unique_years}")


def evaluate_top_fraction_filter(
    frame: pd.DataFrame,
    score_col: str,
    target_col: str,
    selected_fraction: float,
) -> dict:
    working = frame[[score_col, target_col]].copy()
    working[score_col] = pd.to_numeric(working[score_col], errors="coerce")
    working[target_col] = pd.to_numeric(working[target_col], errors="coerce")
    working = working.dropna(subset=[score_col, target_col])
    working = working.sort_values(score_col, ascending=False, kind="mergesort")

    total_n = int(len(working))
    selected_n = int(math.ceil(total_n * selected_fraction)) if total_n else 0
    selected_n = min(selected_n, total_n)
    selected = working.iloc[:selected_n][target_col].to_numpy(dtype=float)
    skipped = working.iloc[selected_n:][target_col].to_numpy(dtype=float)
    threshold_value = None
    if selected_n > 0:
        threshold_value = float(working.iloc[selected_n - 1][score_col])

    def _mean(values: np.ndarray) -> float | None:
        return float(np.mean(values)) if len(values) else None

    def _quantile(values: np.ndarray, q: float) -> float | None:
        return float(np.quantile(values, q)) if len(values) else None

    selected_mean = _mean(selected)
    skipped_mean = _mean(skipped)
    if skipped_mean in (None, 0.0):
        movement_lift = None
    else:
        movement_lift = float(selected_mean / skipped_mean) if selected_mean is not None else None

    return {
        "selected_n": selected_n,
        "skipped_n": int(len(skipped)),
        "selected_mean_movement": selected_mean,
        "skipped_mean_movement": skipped_mean,
        "selected_p50": _quantile(selected, 0.50),
        "selected_p80": _quantile(selected, 0.80),
        "selected_p90": _quantile(selected, 0.90),
        "skipped_p50": _quantile(skipped, 0.50),
        "skipped_p80": _quantile(skipped, 0.80),
        "skipped_p90": _quantile(skipped, 0.90),
        "movement_lift": movement_lift,
        "score_cutoff": threshold_value,
        "total_n": total_n,
    }


def _metric_value(candidate: dict, key: str) -> float:
    value = candidate.get(key)
    if value is None:
        return float("-inf")
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return float("-inf")
    return numeric if math.isfinite(numeric) else float("-inf")


def _horizon_value(candidate: dict) -> int:
    horizon = candidate.get("horizon")
    if isinstance(horizon, str):
        text = horizon.strip().upper()
        if text.startswith("H"):
            text = text[1:]
        try:
            horizon = int(text)
        except ValueError:
            return -1
    try:
        return int(horizon)
    except (TypeError, ValueError):
        return -1


def _selection_key(candidate: dict) -> tuple[float, float, int, int]:
    profile = str(candidate.get("profile", ""))
    return (
        _metric_value(candidate, "movement_lift"),
        _metric_value(candidate, "selected_n"),
        PROFILE_ORDER.get(profile, -1),
        HORIZON_ORDER.get(_horizon_value(candidate), -1),
    )


def _passes_val_select_gate(candidate: dict) -> bool:
    return (
        _metric_value(candidate, "selected_n") >= 200
        and _metric_value(candidate, "movement_lift") >= 1.25
        and _metric_value(candidate, "selected_p80") > _metric_value(candidate, "skipped_p80")
    )


def select_filter(candidates: list[dict]) -> dict | None:
    eligible = [candidate for candidate in candidates if _passes_val_select_gate(candidate)]
    if not eligible:
        return None
    return max(eligible, key=_selection_key)


def decide_verdict(selected: dict | None, val_eval_metrics: dict | None, contract_status: dict) -> str:
    if contract_status.get("status") != "PASS":
        return "ABORT_CONTRACT_FAIL"
    if not selected or not val_eval_metrics:
        return "MOVEMENT_FILTER_REJECTED"

    selected_n = _metric_value(val_eval_metrics, "selected_n")
    movement_lift = _metric_value(val_eval_metrics, "movement_lift")
    selected_p80 = _metric_value(val_eval_metrics, "selected_p80")
    skipped_p80 = _metric_value(val_eval_metrics, "skipped_p80")
    yearly_lift_pass_rate = _metric_value(val_eval_metrics, "yearly_lift_pass_rate")

    if (
        selected_n >= 100
        and movement_lift >= 1.15
        and selected_p80 > skipped_p80
        and yearly_lift_pass_rate >= 0.60
    ):
        return "SIMPLE_MOVEMENT_FILTER_RESEARCH_ONLY"
    return "MOVEMENT_FILTER_REJECTED"


def _source_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _target_col(horizon: int) -> str:
    return f"entry_movement_{int(horizon)}"


def _output_paths(prefix: Path) -> dict[str, Path]:
    return {
        "json": Path(f"{prefix}.json"),
        "candidates": Path(f"{prefix}_candidates.csv"),
        "yearly": Path(f"{prefix}_yearly.csv"),
        "selected_rows": Path(f"{prefix}_selected_rows.csv"),
    }


def _build_runtime_context(source_artifact: dict) -> dict[str, Any]:
    splits = amplitude.load_entry_based_splits()
    validate_low_n_disclosure_years(splits["low_n_disclosure"])
    train_targets, thresholds = amplitude.build_movement_targets(splits["train"])
    targets_by_split = {"train": train_targets}
    for split_name in ("val_select", "val_eval", "low_n_disclosure"):
        targets_by_split[split_name], _ = amplitude.build_movement_targets(
            splits[split_name],
            train_thresholds=thresholds,
        )
    run_config = source_artifact.get("run_config") or {}
    return {
        "splits": splits,
        "targets_by_split": targets_by_split,
        "profile_cache": {},
        "score_family_cache": {},
        "requested_threads": int(run_config.get("requested_threads", 24) or 24),
        "effective_threads": int(run_config.get("effective_threads", 24) or 24),
    }


def _score_family_cache_key(candidate: dict) -> tuple[str, str, int, str]:
    return (
        str(candidate["profile"]),
        str(candidate["model_key"]),
        int(candidate["horizon"]),
        str(candidate["target_family"]),
    )


def materialize_candidate_score_frames(candidate: dict, runtime_context: dict[str, Any]) -> dict[str, Any]:
    cache_key = _score_family_cache_key(candidate)
    cached = runtime_context["score_family_cache"].get(cache_key)
    if cached is not None:
        return cached

    splits = runtime_context["splits"]
    targets_by_split = runtime_context["targets_by_split"]
    profile_key = str(candidate["profile"])
    profile_bundle = runtime_context["profile_cache"].get(profile_key)
    if profile_bundle is None:
        profile_bundle = amplitude.build_feature_profile_with_metadata(
            {name: splits[name] for name in REQUIRED_SPLITS},
            profile_key,
        )
        runtime_context["profile_cache"][profile_key] = profile_bundle

    split_features = amplitude._align_feature_frames_to_train(profile_bundle["features"])
    split_meta = profile_bundle["metadata"]
    train_meta = split_meta["train"]
    if split_features["train"].shape[1] == 0 or str(train_meta.get("status", "")).startswith("SKIPPED"):
        raise RuntimeError(f"Profile {profile_key} has no usable train features")

    scaler = RobustScaler()
    scaler.fit(amplitude._numeric_frame(profile_bundle["features"]["train"]))
    transformed = {
        split_name: scaler.transform(features)
        for split_name, features in split_features.items()
    }

    target_col = _target_col(int(candidate["horizon"]))
    train_y = pd.to_numeric(targets_by_split["train"][target_col], errors="coerce").to_numpy(dtype=float)
    per_seed_predictions = {split_name: [] for split_name in ("val_select", "val_eval", "low_n_disclosure")}
    seeds = amplitude.seeds_for_model(str(candidate["model_key"]))
    for seed in seeds:
        model = amplitude.make_model(
            str(candidate["model_key"]),
            int(seed),
            int(runtime_context["effective_threads"]),
        )
        model.fit(transformed["train"], train_y)
        for split_name in per_seed_predictions:
            prediction = np.asarray(model.predict(transformed[split_name]), dtype=float)
            per_seed_predictions[split_name].append(prediction)

    score_frames: dict[str, pd.DataFrame] = {}
    for split_name, predictions in per_seed_predictions.items():
        stacked = np.vstack(predictions)
        score = np.median(stacked, axis=0)
        base_frame = pd.DataFrame(
            {
                "score": score,
                target_col: pd.to_numeric(targets_by_split[split_name][target_col], errors="coerce").to_numpy(dtype=float),
            },
            index=splits[split_name].index,
        )
        if "time" in splits[split_name].columns:
            base_frame["time"] = splits[split_name]["time"].values
        score_frames[split_name] = base_frame

    cached = {
        "frames": score_frames,
        "seed_count": int(len(seeds)),
        "score_aggregation": "median_across_rerun_seeds",
        "feature_contract_verdict": train_meta.get("feature_contract_verdict", "PASS"),
        "available_at_decision_time": bool(train_meta.get("available_at_decision_time", True)),
        "selection_eligible": bool(train_meta.get("selection_eligible", True)),
    }
    runtime_context["score_family_cache"][cache_key] = cached
    return cached


def _yearly_filter_rows(
    split_name: str,
    frame: pd.DataFrame,
    score_col: str,
    target_col: str,
    selected_fraction: float,
) -> list[dict[str, Any]]:
    if "time" not in frame.columns:
        return []
    timestamps = pd.to_datetime(frame["time"], errors="coerce")
    years = timestamps.dt.year
    rows: list[dict[str, Any]] = []
    for year in sorted(int(value) for value in years.dropna().unique()):
        mask = years == year
        year_frame = frame.loc[mask].copy()
        metrics = evaluate_top_fraction_filter(year_frame, score_col, target_col, selected_fraction)
        rows.append(
            {
                "split": split_name,
                "year": int(year),
                "passes_yearly_lift_gate": bool(
                    metrics["selected_n"] > 0
                    and metrics["skipped_n"] > 0
                    and _metric_value(metrics, "movement_lift") > 1.0
                    and _metric_value(metrics, "selected_p80") > _metric_value(metrics, "skipped_p80")
                ),
                **metrics,
            }
        )
    return rows


def _yearly_lift_pass_rate(yearly_rows: list[dict[str, Any]], split_name: str) -> float | None:
    eligible = [row for row in yearly_rows if row.get("split") == split_name and int(row.get("selected_n", 0)) > 0]
    if not eligible:
        return None
    passed = sum(1 for row in eligible if bool(row.get("passes_yearly_lift_gate")))
    return float(passed / len(eligible))


def _selected_rows_export(
    split_name: str,
    frame: pd.DataFrame,
    score_col: str,
    target_col: str,
    selected_fraction: float,
    selected_filter: dict,
) -> pd.DataFrame:
    working = frame.copy()
    working[score_col] = pd.to_numeric(working[score_col], errors="coerce")
    working[target_col] = pd.to_numeric(working[target_col], errors="coerce")
    working = working.dropna(subset=[score_col, target_col])
    working = working.sort_values(score_col, ascending=False, kind="mergesort")
    selected_n = min(int(math.ceil(len(working) * selected_fraction)), len(working))
    selected = working.iloc[:selected_n].copy()
    selected["split"] = split_name
    selected["profile"] = selected_filter.get("profile")
    selected["model_key"] = selected_filter.get("model_key")
    selected["horizon"] = selected_filter.get("horizon")
    selected["selected_fraction"] = selected_fraction
    if "time" in selected.columns:
        selected["year"] = pd.to_datetime(selected["time"], errors="coerce").dt.year
    return selected


def _source_search_budget(source_artifact: dict) -> dict[str, Any]:
    metrics = source_artifact.get("metrics") or []
    seed_aggregate = source_artifact.get("seed_aggregate") or []
    explicit_value = source_artifact.get("cumulative_search_budget")
    return {
        "explicit_value_from_source": explicit_value,
        "derived_from_source_metrics": explicit_value is None,
        "completed_metric_runs": int(sum(1 for row in metrics if row.get("status") == "completed")),
        "failed_metric_runs": int(sum(1 for row in source_artifact.get("failed_runs") or [] if row.get("status") == "failed")),
        "seed_aggregate_rows": int(len(seed_aggregate)),
        "simple_profile_seed_aggregates": int(
            sum(
                1
                for row in seed_aggregate
                if row.get("profile") in ALLOWED_PROFILES and row.get("target_family") == ALLOWED_TARGET_FAMILY
            )
        ),
    }


def _candidate_metrics(candidate: dict, runtime_context: dict[str, Any]) -> dict[str, Any]:
    family = materialize_candidate_score_frames(candidate, runtime_context)
    target_col = _target_col(int(candidate["horizon"]))
    frame = family["frames"]["val_select"]
    metrics = evaluate_top_fraction_filter(frame, "score", target_col, float(candidate["selected_fraction"]))
    metrics["spearman"] = amplitude.compute_spearman(
        pd.to_numeric(frame[target_col], errors="coerce").to_numpy(dtype=float),
        pd.to_numeric(frame["score"], errors="coerce").to_numpy(dtype=float),
    )
    return {
        **candidate,
        **metrics,
        "selection_split": "val_select",
        "score_aggregation": family["score_aggregation"],
        "seed_count": family["seed_count"],
        "feature_contract_verdict": family["feature_contract_verdict"],
        "available_at_decision_time": family["available_at_decision_time"],
    }


def _build_abort_report(
    source_path: Path,
    output_prefix: Path,
    source_hash: str,
    contract_status: dict,
    source_artifact: dict,
) -> dict[str, Any]:
    paths = _output_paths(output_prefix)
    report = {
        "schema_version": 1,
        "stage_status": "RESEARCH_ONLY",
        "verdict": "ABORT_CONTRACT_FAIL",
        "allowed_verdicts": list(ALLOWED_VERDICTS),
        "source_artifact_path": str(source_path),
        "source_artifact_hash": source_hash,
        "source_artifact_hash_method": "sha256",
        "source_contract": contract_status,
        "selection_policy": SELECTION_POLICY,
        "locked_test": "not_opened",
        "constraints": {
            "direction": "forbidden",
            "pnl_pf": "forbidden",
            "locked_test": "not_opened",
        },
        "source_search_budget": _source_search_budget(source_artifact),
        "filter_search_budget": {
            "planned_candidates": len(ALLOWED_PROFILES) * len(amplitude.TARGET_HORIZONS) * len(ALLOWED_FRACTIONS),
            "evaluated_candidates": 0,
        },
        "candidates_csv": str(paths["candidates"]),
        "yearly_csv": str(paths["yearly"]),
        "selected_rows_csv": str(paths["selected_rows"]),
    }
    return report


def write_filter_artifacts(
    report: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    yearly_rows: list[dict[str, Any]],
    selected_rows: pd.DataFrame,
    output_prefix: Path,
) -> None:
    paths = _output_paths(output_prefix)
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    paths["json"].write_text(json.dumps(report, ensure_ascii=True, indent=2, default=str), encoding="utf-8")
    pd.DataFrame(candidate_rows).to_csv(paths["candidates"], index=False)
    pd.DataFrame(yearly_rows).to_csv(paths["yearly"], index=False)
    selected_rows.to_csv(paths["selected_rows"], index=False)


def run_cli(args: argparse.Namespace) -> dict[str, Any]:
    source_path = Path(args.source)
    output_prefix = Path(args.output_prefix)
    validate_source_path(
        source_path,
        allow_noncanonical_source=bool(getattr(args, "allow_noncanonical_source", False)),
    )
    source_artifact = load_amplitude_artifact(source_path)
    source_hash = _source_sha256(source_path)
    contract_status = validate_source_artifact(source_artifact)
    if contract_status["status"] != "PASS":
        report = _build_abort_report(source_path, output_prefix, source_hash, contract_status, source_artifact)
        write_filter_artifacts(report, [], [], pd.DataFrame(), output_prefix)
        return report

    runtime_context = _build_runtime_context(source_artifact)
    candidate_rows = [_candidate_metrics(candidate, runtime_context) for candidate in enumerate_filter_candidates(source_artifact)]
    selected = select_filter(candidate_rows)

    yearly_rows: list[dict[str, Any]] = []
    selected_rows = pd.DataFrame()
    val_eval_metrics: dict[str, Any] | None = None
    low_n_disclosure_metrics: dict[str, Any] | None = None
    rejection_reason = None

    if selected is not None:
        family = materialize_candidate_score_frames(selected, runtime_context)
        target_col = _target_col(int(selected["horizon"]))
        val_eval_frame = family["frames"]["val_eval"]
        val_eval_metrics = evaluate_top_fraction_filter(
            val_eval_frame,
            "score",
            target_col,
            float(selected["selected_fraction"]),
        )
        val_eval_metrics["spearman"] = amplitude.compute_spearman(
            pd.to_numeric(val_eval_frame[target_col], errors="coerce").to_numpy(dtype=float),
            pd.to_numeric(val_eval_frame["score"], errors="coerce").to_numpy(dtype=float),
        )
        yearly_rows.extend(
            {
                **selected,
                **row,
            }
            for row in _yearly_filter_rows(
                "val_select",
                family["frames"]["val_select"],
                "score",
                target_col,
                float(selected["selected_fraction"]),
            )
        )
        yearly_rows.extend(
            {
                **selected,
                **row,
            }
            for row in _yearly_filter_rows(
                "val_eval",
                val_eval_frame,
                "score",
                target_col,
                float(selected["selected_fraction"]),
            )
        )
        val_eval_metrics["yearly_lift_pass_rate"] = _yearly_lift_pass_rate(yearly_rows, "val_eval")

        low_n_frame = family["frames"]["low_n_disclosure"]
        low_n_disclosure_metrics = evaluate_top_fraction_filter(
            low_n_frame,
            "score",
            target_col,
            float(selected["selected_fraction"]),
        )
        low_n_disclosure_metrics["spearman"] = amplitude.compute_spearman(
            pd.to_numeric(low_n_frame[target_col], errors="coerce").to_numpy(dtype=float),
            pd.to_numeric(low_n_frame["score"], errors="coerce").to_numpy(dtype=float),
        )
        if "time" in low_n_frame.columns:
            disclosure_years = pd.to_datetime(low_n_frame["time"], errors="coerce").dt.year.dropna().astype(int).unique()
            low_n_disclosure_metrics["years"] = sorted(int(year) for year in disclosure_years)

        selected_rows = pd.concat(
            [
                _selected_rows_export(
                    "val_eval",
                    val_eval_frame,
                    "score",
                    target_col,
                    float(selected["selected_fraction"]),
                    selected,
                ),
                _selected_rows_export(
                    "low_n_disclosure",
                    low_n_frame,
                    "score",
                    target_col,
                    float(selected["selected_fraction"]),
                    selected,
                ),
            ],
            ignore_index=True,
        )
    else:
        rejection_reason = "no_val_select_candidate_passed_gate"

    verdict = decide_verdict(selected, val_eval_metrics, contract_status)
    if selected is not None and verdict == "MOVEMENT_FILTER_REJECTED":
        rejection_reason = "selected_filter_failed_val_eval_gate"

    report = {
        "schema_version": 1,
        "stage_status": "RESEARCH_ONLY",
        "verdict": verdict,
        "allowed_verdicts": list(ALLOWED_VERDICTS),
        "source_artifact_path": str(source_path),
        "source_artifact_hash": source_hash,
        "source_artifact_hash_method": "sha256",
        "source_contract": contract_status,
        "selection_policy": SELECTION_POLICY,
        "locked_test": "not_opened",
        "constraints": {
            "direction": "forbidden",
            "pnl_pf": "forbidden",
            "locked_test": "not_opened",
            "decision_time": "pre_entry_decision",
        },
        "source_search_budget": _source_search_budget(source_artifact),
        "filter_search_budget": {
            "planned_candidates": len(ALLOWED_PROFILES) * len(amplitude.TARGET_HORIZONS) * len(ALLOWED_FRACTIONS),
            "evaluated_candidates": int(len(candidate_rows)),
            "score_families_rerun": int(len(runtime_context.get("score_family_cache", {}))),
        },
        "selected_filter": selected,
        "selected_filter_val_eval": val_eval_metrics,
        "low_n_disclosure_2026": low_n_disclosure_metrics,
        "rejection_reason": rejection_reason,
        "candidates_csv": str(_output_paths(output_prefix)["candidates"]),
        "yearly_csv": str(_output_paths(output_prefix)["yearly"]),
        "selected_rows_csv": str(_output_paths(output_prefix)["selected_rows"]),
        "summary": {
            "candidate_count": int(len(candidate_rows)),
            "selected_candidate_count": 0 if selected is None else 1,
            "selected_profile": None if selected is None else selected.get("profile"),
            "selected_model_key": None if selected is None else selected.get("model_key"),
            "selected_horizon": None if selected is None else selected.get("horizon"),
            "selected_fraction": None if selected is None else selected.get("selected_fraction"),
            "score_aggregation": None
            if selected is None
            else materialize_candidate_score_frames(selected, runtime_context)["score_aggregation"],
        },
    }
    write_filter_artifacts(report, candidate_rows, yearly_rows, selected_rows, output_prefix)
    return report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Entry-based movement filter CLI")
    parser.add_argument("--source", required=True, help="Path to entry_based_amplitude_movement.json")
    parser.add_argument("--output-prefix", required=True, help="Output prefix, e.g. ML/reports/entry_based_movement_filter")
    parser.add_argument(
        "--allow-noncanonical-source",
        action="store_true",
        help="Allow a non-canonical source artifact path for tests/fixtures only.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    run_cli(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
