"""Frozen rule contract and CLI for the entry-based movement filter."""

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
from ML.baseline.benchmark_entry_based_movement_filter import (
    _build_runtime_context,
    _source_search_budget,
    _yearly_filter_rows,
    evaluate_top_fraction_filter,
    materialize_candidate_score_frames,
    validate_low_n_disclosure_years,
)

FROZEN_RULE: dict[str, object] = {
    "profile": "simple_combined",
    "model_key": "extra_trees_small",
    "horizon": 3,
    "target_family": "entry_movement",
    "threshold_type": "top_fraction",
    "selected_fraction": 0.05,
    "score_aggregation": "median_across_rerun_seeds",
    "seeds": [42, 43, 44],
}

ALLOWED_VERDICTS = (
    "FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN",
    "RESEARCH_ONLY_REPLICATED",
    "REJECT_MOVEMENT_FILTER_FREEZE",
    "ABORT_CONTRACT_FAIL",
)
SELECTION_POLICY = {
    "winner_metric": "val_select",
    "winner_unit": "top_fraction_filter",
    "val_eval": "check_only",
    "low_n_disclosure_2026": "disclosure_only",
    "locked_test": "not_opened",
    "direction_selection": "forbidden",
    "decision_time": "pre_entry_decision",
}
CANONICAL_MOVEMENT_FILTER_SOURCE = Path("ML/reports/entry_based_movement_filter.json")
CANONICAL_AMPLITUDE_SOURCE = Path("ML/reports/entry_based_amplitude_movement.json")


def frozen_rule() -> dict[str, object]:
    return dict(FROZEN_RULE)


def _stable_json_payload(value: dict[str, object]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_rule_hash(rule: dict[str, object]) -> str:
    payload = _stable_json_payload(rule)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_source_artifacts(movement_filter_path: Path, amplitude_path: Path) -> dict[str, object]:
    movement_filter_artifact = json.loads(Path(movement_filter_path).read_text(encoding="utf-8"))
    amplitude_artifact = json.loads(Path(amplitude_path).read_text(encoding="utf-8"))
    return {
        "movement_filter_artifact": movement_filter_artifact,
        "amplitude_artifact": amplitude_artifact,
        "movement_filter_path": str(movement_filter_path),
        "amplitude_path": str(amplitude_path),
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_source_hashes(movement_filter_artifact: dict, amplitude_path: Path) -> dict[str, object]:
    reasons: list[str] = []
    source_amplitude_hash = sha256_file(amplitude_path)

    if not isinstance(movement_filter_artifact, dict):
        reasons.append("artifact_type")
    elif movement_filter_artifact.get("source_artifact_hash") != source_amplitude_hash:
        reasons.append("source_amplitude_hash_mismatch")

    return {
        "status": "ABORT_CONTRACT_FAIL" if reasons else "PASS",
        "reasons": reasons,
        "source_amplitude_hash": source_amplitude_hash,
    }


def frozen_config_hash(config: dict[str, object]) -> str:
    payload = _stable_json_payload(config)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def validate_canonical_source_path(
    path: Path,
    canonical_relative_path: Path,
    *,
    label: str,
    allow_noncanonical_source: bool = False,
) -> None:
    if allow_noncanonical_source:
        return

    expected = (_repo_root() / canonical_relative_path).resolve()
    actual = path.expanduser().resolve()
    if actual != expected:
        raise ValueError(
            f"{label} must be {canonical_relative_path}; got {path}. "
            "Use --allow-noncanonical-source only for tests/fixtures."
        )


def _rule_subset(row: dict[str, Any] | None) -> dict[str, object]:
    if not isinstance(row, dict):
        return {}

    observed = {key: row.get(key) for key in FROZEN_RULE if key != "seeds"}
    observed["seeds"] = [42, 43, 44] if row.get("seed_count") == 3 else row.get("seeds")
    return observed


def validate_frozen_rule(source_artifact: dict) -> dict[str, object]:
    reasons: list[str] = []

    if not isinstance(source_artifact, dict):
        reasons.append("artifact_type")
        return {
            "status": "ABORT_CONTRACT_FAIL",
            "reasons": reasons,
            "rule_hash": stable_rule_hash(FROZEN_RULE),
        }

    if source_artifact.get("locked_test") != "not_opened":
        reasons.append("locked_test")

    selected_filter = source_artifact.get("selected_filter")
    if _rule_subset(selected_filter) != frozen_rule():
        reasons.append("frozen_rule_mismatch")

    return {
        "status": "ABORT_CONTRACT_FAIL" if reasons else "PASS",
        "reasons": reasons,
        "rule_hash": stable_rule_hash(FROZEN_RULE),
    }


def materialize_frozen_score_frames(movement_filter_artifact: dict) -> dict[str, object]:
    verdict = validate_frozen_rule(movement_filter_artifact)
    if verdict["status"] != "PASS":
        raise ValueError(f"frozen rule validation failed: {verdict['reasons']}")

    runtime_context = _build_runtime_context(movement_filter_artifact)
    cached = materialize_candidate_score_frames(
        dict(movement_filter_artifact["selected_filter"]),
        runtime_context,
    )
    frames = dict(cached["frames"])
    if "train" not in frames:
        frames["train"] = _materialize_train_score_frame(
            dict(movement_filter_artifact["selected_filter"]),
            runtime_context,
        )
    validate_low_n_disclosure_years(frames["low_n_disclosure"])

    return {
        "frames": frames,
        "selected_filter": dict(movement_filter_artifact["selected_filter"]),
        "seed_count": cached["seed_count"],
        "score_aggregation": cached["score_aggregation"],
        "rule_hash": verdict["rule_hash"],
    }


def _materialize_train_score_frame(candidate: dict, runtime_context: dict[str, Any]) -> pd.DataFrame:
    """Rebuild the frozen score for train so score exports cover every split."""

    splits = runtime_context["splits"]
    targets_by_split = runtime_context["targets_by_split"]
    profile_key = str(candidate["profile"])
    profile_bundle = runtime_context["profile_cache"].get(profile_key)
    if profile_bundle is None:
        profile_bundle = amplitude.build_feature_profile_with_metadata(
            {name: splits[name] for name in ("train", "val_select", "val_eval", "low_n_disclosure")},
            profile_key,
        )
        runtime_context["profile_cache"][profile_key] = profile_bundle

    split_features = amplitude._align_feature_frames_to_train(profile_bundle["features"])
    scaler = RobustScaler()
    scaler.fit(amplitude._numeric_frame(profile_bundle["features"]["train"]))
    train_x = scaler.transform(split_features["train"])
    target_col = f"entry_movement_{int(candidate['horizon'])}"
    train_y = pd.to_numeric(targets_by_split["train"][target_col], errors="coerce").to_numpy(dtype=float)
    predictions: list[np.ndarray] = []
    for seed in amplitude.seeds_for_model(str(candidate["model_key"])):
        model = amplitude.make_model(
            str(candidate["model_key"]),
            int(seed),
            int(runtime_context["effective_threads"]),
        )
        model.fit(train_x, train_y)
        predictions.append(np.asarray(model.predict(train_x), dtype=float))

    score = np.median(np.vstack(predictions), axis=0)
    frame = pd.DataFrame(
        {
            "score": score,
            target_col: train_y,
        },
        index=splits["train"].index,
    )
    if "time" in splits["train"].columns:
        frame["time"] = splits["train"]["time"].values
    return frame


def _selected_mask(frame: pd.DataFrame, score_col: str, selected_fraction: float) -> pd.Series:
    numeric_score = pd.to_numeric(frame[score_col], errors="coerce")
    valid = numeric_score.notna()
    ordered = (
        frame.loc[valid]
        .assign(_numeric_score=numeric_score.loc[valid])
        .sort_values("_numeric_score", ascending=False, kind="mergesort")
    )
    selected_n = min(int(math.ceil(len(ordered) * selected_fraction)), len(ordered))
    selected_index = ordered.index[:selected_n]
    return frame.index.isin(selected_index)


def evaluate_frozen_rule(frames: dict[str, pd.DataFrame]) -> dict[str, object]:
    score_col = "score"
    target_col = "entry_movement_3"
    selected_fraction = 0.05

    result: dict[str, object] = {}
    for split_name in ("val_select", "val_eval"):
        if split_name not in frames:
            continue
        result[split_name] = evaluate_top_fraction_filter(
            frames[split_name],
            score_col,
            target_col,
            selected_fraction,
        )

    if "val_eval" in frames:
        result["val_eval_yearly"] = _yearly_filter_rows(
            "val_eval",
            frames["val_eval"],
            score_col,
            target_col,
            selected_fraction,
        )

    if "low_n_disclosure" in frames:
        validate_low_n_disclosure_years(frames["low_n_disclosure"])
        years = sorted(
            int(year)
            for year in pd.to_datetime(frames["low_n_disclosure"]["time"], errors="coerce").dt.year.dropna().unique()
        )
        result["low_n_disclosure_2026"] = {
            **evaluate_top_fraction_filter(
                frames["low_n_disclosure"],
                score_col,
                target_col,
                selected_fraction,
            ),
            "years": years,
            "status": "DISCLOSURE_ONLY",
        }

    return result


def build_score_export(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    score_col = "score"
    target_col = "entry_movement_3"
    selected_fraction = 0.05

    exported: list[pd.DataFrame] = []
    for split_name in ("train", "val_select", "val_eval", "low_n_disclosure"):
        frame = frames.get(split_name)
        if frame is None:
            continue

        working = frame.copy()
        working["split"] = split_name
        if "time" in working.columns:
            timestamps = pd.to_datetime(working["time"], errors="coerce")
            working["year"] = timestamps.dt.year.astype("Int64")
        else:
            working["time"] = pd.NA
            working["year"] = pd.Series(pd.array([pd.NA] * len(working), dtype="Int64"), index=working.index)
        working["selected"] = _selected_mask(working, score_col, selected_fraction)
        exported.append(
            working[["split", "time", "year", score_col, target_col, "selected"]].copy()
        )

    if not exported:
        return pd.DataFrame(columns=["split", "time", "year", score_col, target_col, "selected"])
    return pd.concat(exported, ignore_index=True)


def build_selected_rows_export(scores: pd.DataFrame) -> pd.DataFrame:
    if scores.empty:
        return scores.copy()
    return scores.loc[scores["selected"]].reset_index(drop=True)


def score_cutoff_diagnostics(frames: dict[str, pd.DataFrame]) -> dict[str, object]:
    score_col = "score"
    target_col = "entry_movement_3"
    selected_fraction = 0.05

    by_split: list[dict[str, object]] = []
    by_year: list[dict[str, object]] = []
    warnings: list[str] = []

    for split_name, frame in frames.items():
        metrics = evaluate_top_fraction_filter(frame, score_col, target_col, selected_fraction)
        by_split.append(
            {
                "split": split_name,
                "score_cutoff": metrics["score_cutoff"],
                "selected_n": metrics["selected_n"],
                "total_n": metrics["total_n"],
            }
        )

        yearly_rows = _yearly_filter_rows(split_name, frame, score_col, target_col, selected_fraction)
        for row in yearly_rows:
            by_year.append(
                {
                    "split": split_name,
                    "year": row["year"],
                    "score_cutoff": row["score_cutoff"],
                    "selected_n": row["selected_n"],
                    "total_n": row["total_n"],
                }
            )

        if "time" not in frame.columns:
            warnings.append(f"{split_name}:missing_time")

    return {
        "status": "WARNING" if warnings else "PASS",
        "warnings": warnings,
        "by_split": by_split,
        "by_year": by_year,
    }


def build_score_cutoff_rows(diagnostics: dict[str, object]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in diagnostics.get("by_split", []):
        if isinstance(row, dict):
            rows.append({"scope": "split", **row})
    for row in diagnostics.get("by_year", []):
        if isinstance(row, dict):
            rows.append({"scope": "year", **row})
    return pd.DataFrame(rows)


def _metric_block(metrics: dict[str, object], key: str) -> dict[str, object]:
    value = metrics.get(key, {})
    return value if isinstance(value, dict) else {}


def _as_float(value: object, default: float = float("nan")) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def freeze_gate_failures(metrics: dict[str, object]) -> list[str]:
    failures: list[str] = []

    val_select = _metric_block(metrics, "val_select")
    val_eval = _metric_block(metrics, "val_eval")
    if _as_float(val_select.get("selected_n")) < 300:
        failures.append("val_select.selected_n")
    if _as_float(val_select.get("movement_lift")) < 1.80:
        failures.append("val_select.movement_lift")
    if not _as_float(val_select.get("selected_p80")) > _as_float(val_select.get("skipped_p80")):
        failures.append("val_select.selected_p80_gt_skipped_p80")

    if _as_float(val_eval.get("selected_n")) < 300:
        failures.append("val_eval.selected_n")
    if _as_float(val_eval.get("movement_lift")) < 1.50:
        failures.append("val_eval.movement_lift")
    if not _as_float(val_eval.get("selected_p80")) > _as_float(val_eval.get("skipped_p80")):
        failures.append("val_eval.selected_p80_gt_skipped_p80")
    if _as_float(val_eval.get("yearly_lift_pass_rate")) < 0.80:
        failures.append("val_eval.yearly_lift_pass_rate")

    yearly = val_eval.get("yearly")
    if not isinstance(yearly, list):
        failures.append("val_eval.yearly")
    else:
        for row in yearly:
            if not isinstance(row, dict):
                failures.append("val_eval.yearly.selected_n")
                break
            if _as_float(row.get("selected_n")) < 50:
                failures.append("val_eval.yearly.selected_n")
                break

    disclosure = _metric_block(metrics, "low_n_disclosure_2026")
    if disclosure.get("years") != [2026]:
        failures.append("low_n_disclosure_2026.years")

    return failures


def _freeze_verdict_warnings(metrics: dict[str, object]) -> list[str]:
    warnings: list[str] = []

    val_eval = _metric_block(metrics, "val_eval")
    random_baseline = _metric_block(metrics, "random_baseline")

    if _as_float(val_eval.get("spearman")) < 0.50:
        warnings.append("val_eval.spearman")

    yearly = val_eval.get("yearly")
    if isinstance(yearly, list):
        for row in yearly:
            if not isinstance(row, dict) or _as_float(row.get("movement_lift")) < 1.25:
                warnings.append("val_eval.yearly.movement_lift")
                break
    else:
        warnings.append("val_eval.yearly.movement_lift")

    frozen_rule_movement_lift = _as_float(val_eval.get("movement_lift"))
    random_same_size_p95 = _as_float(random_baseline.get("p95_movement_lift"))
    if random_same_size_p95 >= frozen_rule_movement_lift:
        warnings.append("random_same_size_p95")

    yearly_random = random_baseline.get("yearly")
    if isinstance(yearly, list) and isinstance(yearly_random, list):
        yearly_random_map = {
            row.get("year"): _as_float(row.get("p95_movement_lift"))
            for row in yearly_random
            if isinstance(row, dict)
        }
        for row in yearly:
            if not isinstance(row, dict):
                continue
            if _as_float(row.get("movement_lift")) <= 0:
                warnings.append("val_eval.yearly.random_same_size_p95")
                break
            if yearly_random_map.get(row.get("year"), float("-inf")) >= _as_float(row.get("movement_lift")):
                warnings.append("val_eval.yearly.random_same_size_p95")
                break

    score_cutoff = _metric_block(metrics, "score_cutoff_diagnostics")
    if score_cutoff.get("status") == "WARNING":
        warnings.append("score_cutoff_diagnostics.status")

    return warnings


def decide_freeze_verdict(contract: dict[str, object], metrics: dict[str, object]) -> str:
    if not isinstance(contract, dict):
        return "ABORT_CONTRACT_FAIL"

    if contract.get("status") != "PASS":
        return "ABORT_CONTRACT_FAIL"
    if contract.get("frozen_rule_hash_match", True) is not True:
        return "ABORT_CONTRACT_FAIL"
    if contract.get("locked_test", "not_opened") != "not_opened":
        return "ABORT_CONTRACT_FAIL"

    failures = freeze_gate_failures(metrics)
    if failures:
        return "REJECT_MOVEMENT_FILTER_FREEZE"

    if _freeze_verdict_warnings(metrics):
        return "RESEARCH_ONLY_REPLICATED"

    return "FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN"


def _dependency_versions() -> dict[str, str]:
    versions = {"python": sys.version.split()[0]}
    for mod_name in ("numpy", "pandas", "scipy", "sklearn"):
        try:
            mod = __import__(mod_name)
            versions[mod_name] = getattr(mod, "__version__", "unknown")
        except ImportError:
            versions[mod_name] = "not_installed"
    return versions


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _extract_model_config(movement_filter_artifact: dict, movement_source_path: Path) -> dict[str, object]:
    selected_filter = movement_filter_artifact.get("selected_filter") or {}
    model_key = str(selected_filter.get("model_key", FROZEN_RULE["model_key"]))
    run_config = movement_filter_artifact.get("source_artifact_path")
    effective_threads = 24
    if isinstance(run_config, str):
        del run_config
    source_run_config = movement_filter_artifact.get("selected_filter") or {}
    if isinstance(source_run_config, dict):
        effective_threads = int(source_run_config.get("effective_threads", effective_threads) or effective_threads)
    estimator = amplitude.make_model(model_key, seed=42, threads=effective_threads)
    params = estimator.get_params(deep=False) if hasattr(estimator, "get_params") else {}
    if "random_state" in params:
        params["random_state"] = "seed_from_frozen_rule"
    return {
        "model_key": model_key,
        "estimator_class": type(estimator).__name__,
        "hyperparameters": _json_ready(dict(sorted(params.items()))),
        "thread_settings": _json_ready(amplitude.model_thread_settings(model_key, effective_threads)),
        "deterministic": bool(amplitude.is_model_deterministic(model_key)),
        "model_source": "ML.baseline.benchmark_entry_based_amplitude_movement.make_model",
        "movement_filter_source": str(movement_source_path),
    }


def build_frozen_config(
    movement_filter_artifact: dict,
    amplitude_artifact: dict,
    movement_source_path: Path,
    materialized: dict[str, object],
) -> dict[str, object]:
    run_config = amplitude_artifact.get("run_config") or {}
    selected_filter = materialized.get("selected_filter") or {}
    return {
        "frozen_rule": frozen_rule(),
        "model_config": _extract_model_config(movement_filter_artifact, movement_source_path),
        "profile_feature_contract": {
            "profile": FROZEN_RULE["profile"],
            "feature_contract_verdict": selected_filter.get("feature_contract_verdict", "PASS"),
            "available_at_decision_time": bool(selected_filter.get("available_at_decision_time", True)),
            "selection_eligible": bool(selected_filter.get("selection_eligible", True)),
        },
        "target_contract": _json_ready(amplitude_artifact.get("target_contract") or {}),
        "split_contract": _json_ready(run_config.get("split_policy") or {}),
        "dependency_versions": _dependency_versions(),
    }


def _with_spearman(metrics: dict[str, object], frame: pd.DataFrame, target_col: str = "entry_movement_3") -> dict[str, object]:
    enriched = dict(metrics)
    enriched["spearman"] = amplitude.compute_spearman(
        pd.to_numeric(frame[target_col], errors="coerce").to_numpy(dtype=float),
        pd.to_numeric(frame["score"], errors="coerce").to_numpy(dtype=float),
    )
    return enriched


def _yearly_lift_pass_rate(rows: list[dict[str, object]], *, threshold: float = 1.50) -> float:
    valid = [row for row in rows if isinstance(row, dict)]
    if not valid:
        return float("nan")
    passed = sum(1 for row in valid if _as_float(row.get("movement_lift")) >= threshold)
    return float(passed / len(valid))


def compute_random_same_size_baseline(
    frame: pd.DataFrame,
    *,
    score_col: str = "score",
    target_col: str = "entry_movement_3",
    selected_fraction: float = 0.05,
    seed: int = 20260708,
    n_repeats: int = 1000,
) -> dict[str, object]:
    working = frame[[score_col, target_col]].copy()
    working[score_col] = pd.to_numeric(working[score_col], errors="coerce")
    working[target_col] = pd.to_numeric(working[target_col], errors="coerce")
    working = working.dropna(subset=[score_col, target_col]).reset_index(drop=True)
    total_n = int(len(working))
    selected_n = min(int(math.ceil(total_n * selected_fraction)), total_n)
    if total_n == 0 or selected_n == 0 or selected_n == total_n:
        return {
            "seed": seed,
            "n_repeats": n_repeats,
            "selected_fraction": selected_fraction,
            "selected_n": selected_n,
            "total_n": total_n,
            "p05_movement_lift": None,
            "p50_movement_lift": None,
            "p95_movement_lift": None,
        }

    rng = np.random.default_rng(seed)
    targets = working[target_col].to_numpy(dtype=float)
    lifts = np.empty(n_repeats, dtype=float)
    for repeat in range(n_repeats):
        selected_idx = rng.choice(total_n, size=selected_n, replace=False)
        mask = np.zeros(total_n, dtype=bool)
        mask[selected_idx] = True
        selected = targets[mask]
        skipped = targets[~mask]
        skipped_mean = float(np.mean(skipped)) if len(skipped) else float("nan")
        selected_mean = float(np.mean(selected)) if len(selected) else float("nan")
        lifts[repeat] = float(selected_mean / skipped_mean) if skipped_mean not in (0.0,) and np.isfinite(skipped_mean) else np.nan

    finite = lifts[np.isfinite(lifts)]
    if len(finite) == 0:
        p05 = p50 = p95 = None
    else:
        p05 = float(np.quantile(finite, 0.05))
        p50 = float(np.quantile(finite, 0.50))
        p95 = float(np.quantile(finite, 0.95))
    return {
        "seed": seed,
        "n_repeats": n_repeats,
        "selected_fraction": selected_fraction,
        "selected_n": selected_n,
        "total_n": total_n,
        "p05_movement_lift": p05,
        "p50_movement_lift": p50,
        "p95_movement_lift": p95,
    }


def compute_random_baseline(
    frame: pd.DataFrame,
    yearly_rows: list[dict[str, object]],
    *,
    seed: int = 20260708,
    n_repeats: int = 1000,
) -> dict[str, object]:
    baseline = compute_random_same_size_baseline(frame, seed=seed, n_repeats=n_repeats)
    yearly: list[dict[str, object]] = []
    if "time" in frame.columns:
        working = frame.copy()
        working["_year"] = pd.to_datetime(working["time"], errors="coerce").dt.year
        for row in yearly_rows:
            year = row.get("year")
            if year is None:
                continue
            year_frame = working.loc[working["_year"] == int(year), ["score", "entry_movement_3"]].copy()
            year_baseline = compute_random_same_size_baseline(
                year_frame,
                seed=seed,
                n_repeats=n_repeats,
            )
            year_baseline["year"] = int(year)
            yearly.append(year_baseline)
    baseline["yearly"] = yearly
    return baseline


def build_random_baseline_rows(random_baseline: dict[str, object]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    base_row = {key: value for key, value in random_baseline.items() if key != "yearly"}
    rows.append({"scope": "global", **base_row})
    for row in random_baseline.get("yearly", []):
        if isinstance(row, dict):
            rows.append({"scope": "year", **row})
    return pd.DataFrame(rows)


def _output_paths(prefix: Path) -> dict[str, Path]:
    return {
        "json": Path(f"{prefix}.json"),
        "yearly": Path(f"{prefix}_yearly.csv"),
        "selected_rows": Path(f"{prefix}_selected_rows.csv"),
        "scores": Path(f"{prefix}_scores.csv"),
        "random_baseline": Path(f"{prefix}_random_baseline.csv"),
        "score_cutoffs": Path(f"{prefix}_score_cutoffs.csv"),
    }


def write_freeze_artifacts(
    report: dict[str, object],
    yearly_rows: list[dict[str, object]],
    selected_rows: pd.DataFrame,
    scores: pd.DataFrame,
    random_baseline_rows: pd.DataFrame,
    score_cutoff_rows: pd.DataFrame,
    output_prefix: Path,
) -> None:
    paths = _output_paths(output_prefix)
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    paths["json"].write_text(json.dumps(_json_ready(report), ensure_ascii=True, indent=2, default=str), encoding="utf-8")
    pd.DataFrame(yearly_rows).to_csv(paths["yearly"], index=False)
    selected_rows.to_csv(paths["selected_rows"], index=False)
    scores.to_csv(paths["scores"], index=False)
    random_baseline_rows.to_csv(paths["random_baseline"], index=False)
    score_cutoff_rows.to_csv(paths["score_cutoffs"], index=False)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Entry-based movement filter freeze CLI")
    parser.add_argument("--movement-filter-source", required=True, help="Path to entry_based_movement_filter.json")
    parser.add_argument("--amplitude-source", required=True, help="Path to entry_based_amplitude_movement.json")
    parser.add_argument("--output-prefix", required=True, help="Output prefix, e.g. ML/reports/entry_based_movement_filter_freeze")
    parser.add_argument(
        "--allow-noncanonical-source",
        action="store_true",
        help="Allow non-canonical source paths for tests/fixtures only.",
    )
    return parser


def run_cli(args: argparse.Namespace) -> dict[str, object]:
    movement_source = Path(args.movement_filter_source)
    amplitude_source = Path(args.amplitude_source)
    output_prefix = Path(args.output_prefix)
    allow_noncanonical = bool(getattr(args, "allow_noncanonical_source", False))

    validate_canonical_source_path(
        movement_source,
        CANONICAL_MOVEMENT_FILTER_SOURCE,
        label="movement filter source",
        allow_noncanonical_source=allow_noncanonical,
    )
    validate_canonical_source_path(
        amplitude_source,
        CANONICAL_AMPLITUDE_SOURCE,
        label="amplitude source",
        allow_noncanonical_source=allow_noncanonical,
    )

    loaded = load_source_artifacts(movement_source, amplitude_source)
    movement_filter_artifact = loaded["movement_filter_artifact"]
    amplitude_artifact = loaded["amplitude_artifact"]
    source_hash_status = validate_source_hashes(movement_filter_artifact, amplitude_source)
    rule_status = validate_frozen_rule(movement_filter_artifact)
    movement_source_hash = sha256_file(movement_source)
    contract_reasons = list(source_hash_status["reasons"]) + list(rule_status["reasons"])
    contract_status = {
        "status": "ABORT_CONTRACT_FAIL" if contract_reasons else "PASS",
        "reasons": contract_reasons,
        "source_hash_status": source_hash_status["status"],
        "frozen_rule_status": rule_status["status"],
        "frozen_rule_hash_match": not rule_status["reasons"] and not source_hash_status["reasons"],
        "locked_test": movement_filter_artifact.get("locked_test", "not_opened"),
    }

    frames: dict[str, pd.DataFrame] = {}
    validation_metrics: dict[str, object] = {}
    disclosure_metrics: dict[str, object] = {}
    yearly_rows: list[dict[str, object]] = []
    score_cutoffs = {"status": "WARNING", "warnings": ["contract_not_passed"], "by_split": [], "by_year": []}
    random_baseline = {
        "seed": 20260708,
        "n_repeats": 1000,
        "selected_fraction": 0.05,
        "selected_n": 0,
        "total_n": 0,
        "p05_movement_lift": None,
        "p50_movement_lift": None,
        "p95_movement_lift": None,
        "yearly": [],
    }
    scores = pd.DataFrame(columns=["split", "time", "year", "score", "entry_movement_3", "selected"])
    selected_rows = pd.DataFrame(columns=["split", "time", "year", "score", "entry_movement_3", "selected"])
    materialized: dict[str, object] = {"selected_filter": dict(movement_filter_artifact.get("selected_filter") or {})}

    if contract_status["status"] == "PASS":
        materialized = materialize_frozen_score_frames(movement_filter_artifact)
        frames = dict(materialized["frames"])
        metrics = evaluate_frozen_rule(frames)
        val_eval_yearly = metrics.pop("val_eval_yearly", [])
        yearly_rows = [dict(row) for row in val_eval_yearly]

        val_select = _with_spearman(dict(metrics.get("val_select", {})), frames["val_select"])
        val_eval = _with_spearman(dict(metrics.get("val_eval", {})), frames["val_eval"])
        val_eval["yearly"] = yearly_rows
        val_eval["yearly_lift_pass_rate"] = _yearly_lift_pass_rate(yearly_rows)
        disclosure = _with_spearman(dict(metrics.get("low_n_disclosure_2026", {})), frames["low_n_disclosure"])

        validation_metrics = {"val_select": val_select, "val_eval": val_eval}
        disclosure_metrics = {"low_n_disclosure_2026": disclosure}
        score_cutoffs = score_cutoff_diagnostics(frames)
        random_baseline = compute_random_baseline(frames["val_eval"], yearly_rows)
        scores = build_score_export(frames)
        selected_rows = build_selected_rows_export(scores)

    metrics_for_verdict = {
        **validation_metrics,
        **disclosure_metrics,
        "score_cutoff_diagnostics": score_cutoffs,
        "random_baseline": random_baseline,
    }
    verdict = decide_freeze_verdict(contract_status, metrics_for_verdict)
    frozen_config = build_frozen_config(movement_filter_artifact, amplitude_artifact, movement_source, materialized)
    report = {
        "schema_version": 1,
        "stage_status": "RESEARCH_ONLY" if verdict != "FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN" else "FROZEN_FOR_NEXT_RESEARCH_PLAN_ONLY",
        "verdict": verdict,
        "allowed_verdicts": list(ALLOWED_VERDICTS),
        "source_movement_filter_path": str(movement_source),
        "source_movement_filter_hash": movement_source_hash,
        "source_amplitude_path": str(amplitude_source),
        "source_amplitude_hash": source_hash_status["source_amplitude_hash"],
        "frozen_rule": frozen_rule(),
        "rule_hash": rule_status["rule_hash"],
        "frozen_config": frozen_config,
        "frozen_config_hash": frozen_config_hash(frozen_config),
        "selection_policy": SELECTION_POLICY,
        "locked_test": "not_opened",
        "contract_status": contract_status,
        "validation_metrics": validation_metrics,
        "disclosure_metrics": disclosure_metrics,
        "search_budget": {
            "source_amplitude_search": _source_search_budget(amplitude_artifact),
            "movement_filter_search": {
                "source_search_budget": movement_filter_artifact.get("source_search_budget"),
                "filter_search_budget": movement_filter_artifact.get("filter_search_budget"),
            },
            "freeze_rerun": {
                "candidate_search_performed": False,
                "score_families_rerun": 0 if not frames else 1,
                "selected_rule_only": True,
            },
        },
        "score_cutoff_diagnostics": score_cutoffs,
        "random_baseline": random_baseline,
        "constraints": {
            "direction": "forbidden",
            "pnl_pf": "forbidden",
            "buy_sell": "forbidden",
            "locked_test": "not_opened",
            "decision_time": "pre_entry_decision",
        },
        "yearly_csv": str(_output_paths(output_prefix)["yearly"]),
        "selected_rows_csv": str(_output_paths(output_prefix)["selected_rows"]),
        "scores_csv": str(_output_paths(output_prefix)["scores"]),
        "random_baseline_csv": str(_output_paths(output_prefix)["random_baseline"]),
        "score_cutoffs_csv": str(_output_paths(output_prefix)["score_cutoffs"]),
    }
    write_freeze_artifacts(
        report,
        yearly_rows,
        selected_rows,
        scores,
        build_random_baseline_rows(random_baseline),
        build_score_cutoff_rows(score_cutoffs),
        output_prefix,
    )
    return report


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    run_cli(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
