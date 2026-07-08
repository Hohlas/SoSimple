"""Direction diagnostics inside the frozen entry-based movement regime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler

from ML.baseline import benchmark_entry_based_amplitude_movement as amplitude
from ML.baseline.benchmark_entry_based_movement_filter_freeze import (
    frozen_rule,
    sha256_file,
    stable_rule_hash,
)

REQUIRED_SCORE_COLUMNS = (
    "split",
    "time",
    "year",
    "score",
    "entry_movement_3",
    "selected",
)
SELECTED_VALUE_MAP = {
    "true": True,
    "1": True,
    "yes": True,
    "false": False,
    "0": False,
    "no": False,
}
ALLOWED_VERDICTS = (
    "FROZEN_DIRECTION_RULE_FOR_NEXT_PLAN",
    "RESEARCH_ONLY_DIRECTION_SIGNAL",
    "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME",
    "ABORT_CONTRACT_FAIL",
)
REQUIRED_ROBUSTNESS_PASS_CHECKS = (
    "yearly_stability",
    "block_stability",
    "confidence_interval_lower_bound",
    "class_balance_disclosure",
    "exact_search_budget",
)
ROWS_EXPORT_COLUMNS = (
    "split",
    "time",
    "target_direction_3",
    "target_is_tie_3",
    "target_up_3",
    "target_dn_3",
)


def frozen_direction_config() -> dict[str, object]:
    rule = frozen_rule()
    return {
        "movement_rule": rule,
        "movement_rule_hash": stable_rule_hash(rule),
        "direction_horizon": 3,
        "locked_test": "not_opened",
        "forbidden_input_columns": [
            "score",
            "entry_movement_3",
            "entry_up_3",
            "entry_dn_3",
            "target_direction_3",
            "target_is_tie_3",
            "target_up_3",
            "target_dn_3",
            "label_direction_3",
        ],
    }


def validate_frozen_movement_contract(
    freeze_report: dict[str, object],
    scores: pd.DataFrame,
) -> dict[str, object]:
    reasons: list[str] = []
    config = frozen_direction_config()

    freeze_config = freeze_report.get("frozen_config")
    frozen_rule_value = freeze_config.get("frozen_rule") if isinstance(freeze_config, dict) else None
    if frozen_rule_value != config["movement_rule"]:
        reasons.append("movement_rule_mismatch")

    if freeze_report.get("frozen_rule_hash") not in (None, config["movement_rule_hash"]):
        reasons.append("movement_rule_hash")

    contract_status = freeze_report.get("contract_status")
    contract_status = contract_status if isinstance(contract_status, dict) else {}
    if contract_status.get("locked_test", "not_opened") != "not_opened":
        reasons.append("locked_test")
    if contract_status.get("status", "PASS") != "PASS":
        reasons.append("movement_contract_status")

    missing = [column for column in REQUIRED_SCORE_COLUMNS if column not in scores.columns]
    if missing:
        reasons.append("scores_schema")
    elif "selected" in scores.columns:
        selected_raw = scores["selected"].astype(str).str.strip().str.lower()
        if sorted(set(selected_raw) - set(SELECTED_VALUE_MAP)):
            reasons.append("scores.selected_format")

    return {
        "status": "ABORT_CONTRACT_FAIL" if reasons else "PASS",
        "reasons": reasons,
        "movement_rule_hash": config["movement_rule_hash"],
    }


def load_frozen_mask(freeze_report_path: Path, scores_path: Path) -> dict[str, object]:
    freeze_report = json.loads(Path(freeze_report_path).read_text(encoding="utf-8"))
    scores = pd.read_csv(scores_path)

    if "selected" in scores.columns:
        selected_raw = scores["selected"].astype(str).str.strip().str.lower()
        if not sorted(set(selected_raw) - set(SELECTED_VALUE_MAP)):
            scores["selected"] = selected_raw.map(SELECTED_VALUE_MAP).astype(bool)

    contract = validate_frozen_movement_contract(freeze_report, scores)
    return {
        "freeze_report": freeze_report,
        "scores": scores,
        "scores_hash": sha256_file(Path(scores_path)),
        "contract": contract,
    }


def build_direction_targets(frame: pd.DataFrame, horizon: int = 3) -> pd.DataFrame:
    up = pd.to_numeric(frame[f"entry_up_{horizon}"], errors="coerce")
    dn = pd.to_numeric(frame[f"entry_dn_{horizon}"], errors="coerce")
    direction = pd.Series(pd.array([pd.NA] * len(frame), dtype="Int64"), index=frame.index)
    valid = up.notna() & dn.notna()
    direction.loc[valid & (up > dn)] = 1
    direction.loc[valid & (dn > up)] = -1

    targets = pd.DataFrame(index=frame.index)
    targets[f"target_direction_{horizon}"] = direction
    targets[f"target_is_tie_{horizon}"] = ~(valid & (up != dn))
    targets[f"target_up_{horizon}"] = up
    targets[f"target_dn_{horizon}"] = dn
    return targets


def _time_key(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")


def validate_mask_join_keys(
    splits: dict[str, pd.DataFrame],
    scores: pd.DataFrame,
) -> dict[str, object]:
    reasons: list[str] = []

    if {"split", "time"} <= set(scores.columns):
        score_keys = scores[["split", "time"]].copy()
        score_keys["_time_key"] = _time_key(score_keys["time"])
        if score_keys[["split", "_time_key"]].duplicated().any():
            reasons.append("scores.duplicate_split_time")
        if score_keys["_time_key"].isna().any():
            reasons.append("scores.invalid_time")
    else:
        score_keys = pd.DataFrame(columns=["split", "_time_key", "selected"])

    for split_name, frame in splits.items():
        if "time" not in frame.columns:
            reasons.append(f"splits.{split_name}.missing_time")
            continue
        split_keys = pd.DataFrame({"_time_key": _time_key(frame["time"])})
        if split_keys["_time_key"].duplicated().any():
            reasons.append(f"splits.{split_name}.duplicate_time")
        if split_keys["_time_key"].isna().any():
            reasons.append(f"splits.{split_name}.invalid_time")
        if {"split", "time", "selected"} <= set(scores.columns):
            selected_scores = score_keys.loc[
                (score_keys["split"] == split_name) & (scores["selected"].astype(bool).to_numpy())
            ]
            missing_selected = ~selected_scores["_time_key"].isin(split_keys["_time_key"])
            if missing_selected.any():
                reasons.append(f"splits.{split_name}.selected_count_mismatch")

    return {"status": "ABORT_CONTRACT_FAIL" if reasons else "PASS", "reasons": reasons}


def join_mask_to_splits(
    splits: dict[str, pd.DataFrame],
    scores: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    key_contract = validate_mask_join_keys(splits, scores)
    if key_contract["status"] != "PASS":
        raise ValueError(f"mask join key validation failed: {key_contract['reasons']}")

    joined: dict[str, pd.DataFrame] = {}
    selected_scores = scores.loc[scores["selected"].astype(bool)].copy()
    selected_scores["_time_key"] = _time_key(selected_scores["time"])

    for split_name, frame in splits.items():
        split_scores = selected_scores.loc[selected_scores["split"] == split_name, ["_time_key"]].copy()
        split_scores["_mask_selected"] = True

        working = frame.copy()
        working["_time_key"] = _time_key(working["time"])
        merged = working.merge(split_scores.drop_duplicates(), on="_time_key", how="left")
        merged = merged.loc[merged["_mask_selected"].eq(True)].drop(columns=["_time_key", "_mask_selected"])

        if len(merged) != len(split_scores):
            raise ValueError(
                f"mask join count mismatch for {split_name}: expected {len(split_scores)}, got {len(merged)}"
            )
        joined[split_name] = merged.reset_index(drop=True)

    return joined


def build_masked_direction_dataset(
    splits: dict[str, pd.DataFrame],
    scores: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    masked = join_mask_to_splits(splits, scores)
    forbidden = set(frozen_direction_config()["forbidden_input_columns"])
    dataset: dict[str, pd.DataFrame] = {}

    for split_name, frame in masked.items():
        targets = build_direction_targets(frame)
        feature_frame = frame.drop(columns=[column for column in forbidden if column in frame.columns])
        combined = pd.concat([feature_frame.reset_index(drop=True), targets.reset_index(drop=True)], axis=1)
        combined = combined.loc[combined["target_direction_3"].notna()].reset_index(drop=True)
        dataset[split_name] = combined

    return dataset


def build_feature_matrices(
    masked: dict[str, pd.DataFrame],
    profile: str = "simple_combined",
) -> dict[str, object]:
    forbidden = set(frozen_direction_config()["forbidden_input_columns"])
    sanitized: dict[str, pd.DataFrame] = {}

    for split_name, frame in masked.items():
        sanitized[split_name] = frame.drop(columns=[column for column in forbidden if column in frame.columns])

    profile_bundle = amplitude.build_feature_profile_with_metadata(sanitized, profile)
    features = amplitude._align_feature_frames_to_train(profile_bundle["features"])
    return {"features": features, "metadata": profile_bundle["metadata"], "profile": profile}


def evaluate_direction_predictions(y_true: pd.Series, y_pred: pd.Series) -> dict[str, object]:
    truth = pd.to_numeric(y_true, errors="coerce")
    pred = pd.to_numeric(y_pred, errors="coerce")
    valid = truth.notna() & pred.notna()
    truth_np = truth.loc[valid].astype(int).to_numpy()
    pred_np = pred.loc[valid].astype(int).to_numpy()

    if len(truth_np) == 0:
        return {
            "total_n": 0,
            "up_support": 0,
            "dn_support": 0,
            "accuracy": None,
            "balanced_accuracy": None,
            "macro_f1": None,
            "mcc": None,
            "up_precision": None,
            "up_recall": None,
            "dn_precision": None,
            "dn_recall": None,
        }

    truth_labels = set(truth_np.tolist())
    pred_labels = set(pred_np.tolist())
    return {
        "total_n": int(len(truth_np)),
        "up_support": int(np.sum(truth_np == 1)),
        "dn_support": int(np.sum(truth_np == -1)),
        "accuracy": float(accuracy_score(truth_np, pred_np)),
        "balanced_accuracy": float(balanced_accuracy_score(truth_np, pred_np)),
        "macro_f1": float(f1_score(truth_np, pred_np, average="macro", zero_division=0)),
        "mcc": float(matthews_corrcoef(truth_np, pred_np))
        if len(truth_labels) > 1 and len(pred_labels) > 1
        else 0.0,
        "up_precision": float(precision_score(truth_np, pred_np, pos_label=1, zero_division=0)),
        "up_recall": float(recall_score(truth_np, pred_np, pos_label=1, zero_division=0)),
        "dn_precision": float(precision_score(truth_np, pred_np, pos_label=-1, zero_division=0)),
        "dn_recall": float(recall_score(truth_np, pred_np, pos_label=-1, zero_division=0)),
    }


def _majority_prediction(train_y: pd.Series, n_rows: int) -> pd.Series:
    majority = int(train_y.value_counts().sort_values(ascending=False).index[0])
    return pd.Series([majority] * n_rows)


def fit_direction_models(
    models: dict[str, object],
    train_x: pd.DataFrame,
    train_y: pd.Series,
) -> dict[str, object]:
    fitted: dict[str, object] = {}
    train_numeric = amplitude._numeric_frame(train_x)
    train_target = pd.to_numeric(train_y, errors="coerce").astype(int)

    for model_name, model in models.items():
        model.fit(train_numeric, train_target)
        fitted[model_name] = model
    return fitted


def _predict_classifier(model: object, eval_x: pd.DataFrame) -> pd.Series:
    eval_numeric = amplitude._numeric_frame(eval_x)
    return pd.Series(model.predict(eval_numeric), index=eval_x.index)


def run_direction_baselines(masked: dict[str, pd.DataFrame]) -> dict[str, object]:
    matrices = build_feature_matrices(masked, profile="simple_combined")
    features: dict[str, pd.DataFrame] = matrices["features"]
    train_y = pd.to_numeric(masked["train"]["target_direction_3"], errors="coerce").astype(int)
    models = {
        "logistic_regression": make_pipeline(
            RobustScaler(),
            LogisticRegression(max_iter=500, class_weight="balanced"),
        ),
        "random_forest_small": RandomForestClassifier(
            n_estimators=64,
            max_depth=6,
            min_samples_leaf=20,
            random_state=42,
            n_jobs=1,
            class_weight="balanced_subsample",
        ),
        "extra_trees_small": ExtraTreesClassifier(
            n_estimators=64,
            max_depth=6,
            min_samples_leaf=20,
            random_state=42,
            n_jobs=1,
            class_weight="balanced",
        ),
    }
    fitted_models = fit_direction_models(models, features["train"], train_y)
    results: dict[str, object] = {}

    for model_name in ("majority_class", *fitted_models.keys()):
        split_metrics: dict[str, object] = {}
        for split_name in ("train", "val_select", "val_eval", "low_n_disclosure"):
            if split_name not in masked or split_name not in features:
                continue
            if model_name == "majority_class":
                pred = _majority_prediction(train_y, len(masked[split_name]))
            else:
                pred = _predict_classifier(fitted_models[model_name], features[split_name])
            split_metrics[split_name] = evaluate_direction_predictions(
                masked[split_name]["target_direction_3"],
                pred,
            )
        results[model_name] = split_metrics

    return {
        "profile": matrices["profile"],
        "target": "target_direction_3",
        "metadata": matrices["metadata"],
        "baselines": results,
    }


def _metric(metrics: dict[str, object], name: str) -> float:
    value = metrics.get(name)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("-inf")


def _metric_int(metrics: dict[str, object], name: str) -> int:
    value = _metric(metrics, name)
    return int(value) if np.isfinite(value) else 0


def _recall_ci95_lower(recall: float, support: float) -> float:
    if not np.isfinite(recall) or not np.isfinite(support) or support <= 0:
        return float("-inf")
    variance = max(recall * (1.0 - recall), 0.0)
    standard_error = float(np.sqrt(variance / support))
    return float(recall - 1.96 * standard_error)


def _json_ready(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_ready(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def select_direction_rule(results: dict[str, object]) -> dict[str, object]:
    baselines = results.get("baselines")
    baselines = baselines if isinstance(baselines, dict) else {}
    candidates: list[tuple[float, float, str]] = []

    for model_name, split_metrics in baselines.items():
        if model_name == "majority_class" or not isinstance(split_metrics, dict):
            continue
        val_select = split_metrics.get("val_select")
        if not isinstance(val_select, dict):
            continue
        candidates.append(
            (
                _metric(val_select, "balanced_accuracy"),
                _metric(val_select, "mcc"),
                str(model_name),
            )
        )

    if not candidates:
        return {
            "status": "NO_CANDIDATE",
            "winner": None,
            "selection_metric": "val_select.balanced_accuracy_then_mcc",
            "selection_policy": "winner_only_from_val_select",
        }

    candidates.sort(key=lambda item: (-item[0], -item[1], item[2]))
    _, _, winner = candidates[0]
    winner_metrics = baselines.get(winner)
    winner_metrics = winner_metrics if isinstance(winner_metrics, dict) else {}
    val_select = winner_metrics.get("val_select")
    val_select = val_select if isinstance(val_select, dict) else {}
    val_eval = winner_metrics.get("val_eval")
    val_eval = val_eval if isinstance(val_eval, dict) else {}
    low_n_disclosure = winner_metrics.get("low_n_disclosure")
    low_n_disclosure = low_n_disclosure if isinstance(low_n_disclosure, dict) else {}
    majority_metrics = baselines.get("majority_class")
    majority_metrics = majority_metrics if isinstance(majority_metrics, dict) else {}
    majority_val_eval = majority_metrics.get("val_eval")
    majority_val_eval = majority_val_eval if isinstance(majority_val_eval, dict) else {}

    return {
        "status": "SELECTED",
        "winner": winner,
        "selection_metric": "val_select.balanced_accuracy_then_mcc",
        "selection_policy": "winner_only_from_val_select",
        "val_eval_policy": "check_only",
        "low_n_disclosure_policy": "disclosure_only",
        "val_select": val_select,
        "val_eval": val_eval,
        "low_n_disclosure": low_n_disclosure,
        "beats_majority_on_val_eval": _metric(val_eval, "balanced_accuracy")
        > _metric(majority_val_eval, "balanced_accuracy"),
    }


def compute_direction_robustness(
    masked: dict[str, pd.DataFrame],
    baseline_results: dict[str, object],
    selection: dict[str, object],
) -> dict[str, object]:
    reasons: list[str] = []
    winner = selection.get("winner")
    checks = {
        "minimum_active_val_eval_years": 2,
        "minimum_rows_per_active_year": 30,
        "val_eval_balanced_accuracy_gate": 0.56,
        "val_eval_mcc_gate": 0.08,
        "val_eval_balanced_accuracy_ci95_lower_gate": 0.52,
        "yearly_stability": "required",
        "block_stability": "required",
        "confidence_interval_lower_bound": "required",
        "class_balance_disclosure": "required",
        "exact_search_budget": "required",
    }

    baselines = baseline_results.get("baselines")
    baselines = baselines if isinstance(baselines, dict) else {}
    selected_metrics = baselines.get(str(winner))
    selected_metrics = selected_metrics if isinstance(selected_metrics, dict) else {}
    val_eval = selected_metrics.get("val_eval")
    val_eval = val_eval if isinstance(val_eval, dict) else {}

    val_eval_rows = masked.get("val_eval")
    active_years: dict[int, int] = {}
    if winner is None:
        reasons.append("winner")
    if val_eval_rows is None or val_eval_rows.empty or "time" not in val_eval_rows.columns:
        reasons.append("val_eval.rows")
    else:
        years = pd.to_datetime(val_eval_rows["time"], errors="coerce").dt.year.dropna().astype(int)
        year_counts = years.value_counts().sort_index()
        active_years = {
            int(year): int(count)
            for year, count in year_counts.items()
            if int(count) >= checks["minimum_rows_per_active_year"]
        }
        if len(active_years) < checks["minimum_active_val_eval_years"]:
            reasons.append("val_eval.active_years")

    if _metric(val_eval, "balanced_accuracy") < checks["val_eval_balanced_accuracy_gate"]:
        reasons.append("val_eval.balanced_accuracy")
    if _metric(val_eval, "mcc") < checks["val_eval_mcc_gate"]:
        reasons.append("val_eval.mcc")

    up_lower = _recall_ci95_lower(_metric(val_eval, "up_recall"), _metric(val_eval, "up_support"))
    dn_lower = _recall_ci95_lower(_metric(val_eval, "dn_recall"), _metric(val_eval, "dn_support"))
    balanced_accuracy_ci95_lower = float((up_lower + dn_lower) / 2.0)
    if balanced_accuracy_ci95_lower < checks["val_eval_balanced_accuracy_ci95_lower_gate"]:
        reasons.append("val_eval.balanced_accuracy_ci95_lower")
    reasons.append("val_eval.block_stability_not_run")

    class_balance = {
        "val_eval_up_support": _metric_int(val_eval, "up_support"),
        "val_eval_dn_support": _metric_int(val_eval, "dn_support"),
    }
    required_pass_checks = {
        "yearly_stability": {
            "status": "PASS" if "val_eval.active_years" not in reasons and "val_eval.rows" not in reasons else "FAIL",
            "evidence": {"active_years": active_years},
        },
        "block_stability": {
            "status": "NOT_RUN",
            "evidence": {"method": "not_implemented_in_this_plan"},
        },
        "confidence_interval_lower_bound": {
            "status": "PASS" if "val_eval.balanced_accuracy_ci95_lower" not in reasons else "FAIL",
            "evidence": {"balanced_accuracy_ci95_lower": balanced_accuracy_ci95_lower},
        },
        "class_balance_disclosure": {
            "status": "PASS" if class_balance["val_eval_up_support"] > 0 and class_balance["val_eval_dn_support"] > 0 else "FAIL",
            "evidence": class_balance,
        },
        "exact_search_budget": {
            "status": "PASS",
            "evidence": {"selection_split": "val_select", "trained_baselines_from_results": True},
        },
    }
    return {
        "status": "PASS" if not reasons else "RESEARCH_ONLY",
        "reasons": reasons,
        "checks": checks,
        "required_pass_checks": required_pass_checks,
        "block_stability": {
            "status": "PASS" if not reasons else "RESEARCH_ONLY",
            "method": "predeclared_year_block_proxy",
            "minimum_active_val_eval_years": checks["minimum_active_val_eval_years"],
        },
        "class_balance_disclosure": class_balance,
        "exact_search_budget": {"selection_split": "val_select"},
        "val_eval_active_years": active_years,
        "confidence_interval": {
            "method": "normal_approximation_per_class_recall",
            "balanced_accuracy_ci95_lower": balanced_accuracy_ci95_lower,
        },
    }


def decide_direction_verdict(
    contract: dict[str, object],
    selection: dict[str, object],
    robustness: dict[str, object] | None = None,
) -> str:
    if not isinstance(contract, dict) or contract.get("status") != "PASS":
        return "ABORT_CONTRACT_FAIL"

    if not isinstance(selection, dict) or selection.get("status") != "SELECTED":
        return "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME"

    val_select = selection.get("val_select")
    val_select = val_select if isinstance(val_select, dict) else {}
    val_eval = selection.get("val_eval")
    val_eval = val_eval if isinstance(val_eval, dict) else {}

    if _metric(val_select, "total_n") < 100 or _metric(val_eval, "total_n") < 100:
        return "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME"
    if _metric(val_select, "balanced_accuracy") < 0.56 or _metric(val_select, "mcc") < 0.08:
        return "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME"
    if _metric(val_eval, "balanced_accuracy") < 0.54 or _metric(val_eval, "mcc") < 0.05:
        return "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME"
    if selection.get("beats_majority_on_val_eval") is not True:
        return "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME"
    required_checks = (robustness or {}).get("required_pass_checks")
    required_checks = required_checks if isinstance(required_checks, dict) else {}
    has_required_checks = all(
        isinstance(required_checks.get(name), dict)
        and required_checks[name].get("status") == "PASS"
        and isinstance(required_checks[name].get("evidence"), dict)
        and bool(required_checks[name]["evidence"])
        for name in REQUIRED_ROBUSTNESS_PASS_CHECKS
    )
    if robustness is None or robustness.get("status") != "PASS" or not has_required_checks:
        return "RESEARCH_ONLY_DIRECTION_SIGNAL"
    return "FROZEN_DIRECTION_RULE_FOR_NEXT_PLAN"


def build_report(
    contract: dict[str, object],
    baseline_results: dict[str, object],
    selection: dict[str, object],
    robustness: dict[str, object],
    verdict: str,
) -> dict[str, object]:
    config = frozen_direction_config()
    trained_baseline_count = int(
        sum(1 for model_name in (baseline_results.get("baselines") or {}) if model_name != "majority_class")
    )
    return {
        "schema_version": 1,
        "stage_status": "RESEARCH_ONLY",
        "verdict": verdict,
        "allowed_verdicts": list(ALLOWED_VERDICTS),
        "frozen_direction_config": _json_ready(config),
        "contract": _json_ready(contract),
        "baseline_results": _json_ready(baseline_results),
        "selection": _json_ready(selection),
        "robustness": _json_ready(robustness),
        "search_budget": {
            "direction_baselines_trained": trained_baseline_count,
            "selection_split": "val_select",
            "disclosure_splits_not_used_for_selection": ["val_eval", "low_n_disclosure"],
        },
        "forbidden_interpretations": [
            "not_pnl",
            "not_pf",
            "not_trading_candidate",
            "not_live_rule",
            "not_locked_test_permission",
        ],
    }


def build_rows_export(masked: dict[str, pd.DataFrame]) -> pd.DataFrame:
    exported: list[pd.DataFrame] = []

    for split_name in ("train", "val_select", "val_eval", "low_n_disclosure"):
        frame = masked.get(split_name)
        if frame is None or frame.empty:
            continue
        working = frame.copy()
        working["split"] = split_name
        for column in ROWS_EXPORT_COLUMNS:
            if column not in working.columns:
                working[column] = pd.NA
        exported.append(working.loc[:, list(ROWS_EXPORT_COLUMNS)].copy())

    if not exported:
        return pd.DataFrame(columns=list(ROWS_EXPORT_COLUMNS))
    return pd.concat(exported, ignore_index=True)


def write_artifacts(report: dict[str, object], rows: pd.DataFrame, output_prefix: Path) -> None:
    json_path = Path(f"{output_prefix}.json")
    rows_path = Path(f"{output_prefix}_rows.csv")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    rows_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(_json_ready(report), ensure_ascii=True, indent=2, default=str), encoding="utf-8")
    rows.to_csv(rows_path, index=False)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Direction diagnostics inside frozen movement regime")
    parser.add_argument("--freeze-report", required=True, help="Path to entry_based_movement_filter_freeze.json")
    parser.add_argument("--freeze-scores", required=True, help="Path to entry_based_movement_filter_freeze_scores.csv")
    parser.add_argument("--output-prefix", required=True, help="Output prefix for JSON/CSV artifacts")
    return parser


def _merge_contract_statuses(*contracts: dict[str, object]) -> dict[str, object]:
    reasons: list[str] = []
    movement_rule_hash = None

    for contract in contracts:
        if not isinstance(contract, dict):
            continue
        if movement_rule_hash is None and contract.get("movement_rule_hash") is not None:
            movement_rule_hash = contract.get("movement_rule_hash")
        contract_reasons = contract.get("reasons")
        if isinstance(contract_reasons, list):
            for reason in contract_reasons:
                reason_str = str(reason)
                if reason_str not in reasons:
                    reasons.append(reason_str)

    status = "ABORT_CONTRACT_FAIL" if reasons else "PASS"
    return {
        "status": status,
        "reasons": reasons,
        "movement_rule_hash": movement_rule_hash,
    }


def run_cli(args: argparse.Namespace) -> dict[str, object]:
    freeze_report_path = Path(args.freeze_report)
    scores_path = Path(args.freeze_scores)
    output_prefix = Path(args.output_prefix)

    loaded = load_frozen_mask(freeze_report_path, scores_path)
    splits = amplitude.load_entry_based_splits()
    join_contract = validate_mask_join_keys(splits, loaded["scores"])
    contract = _merge_contract_statuses(loaded["contract"], join_contract)

    if contract["status"] != "PASS":
        baseline_results = {"baselines": {}}
        selection = {
            "status": "NO_CANDIDATE",
            "winner": None,
            "selection_metric": "val_select.balanced_accuracy_then_mcc",
            "selection_policy": "winner_only_from_val_select",
        }
        robustness = {"status": "NOT_RUN"}
        verdict = decide_direction_verdict(contract, selection, robustness)
        rows = build_rows_export({})
    else:
        masked = build_masked_direction_dataset(splits, loaded["scores"])
        baseline_results = run_direction_baselines(masked)
        selection = select_direction_rule(baseline_results)
        robustness = (
            compute_direction_robustness(masked, baseline_results, selection)
            if selection.get("status") == "SELECTED"
            else {"status": "NOT_RUN"}
        )
        verdict = decide_direction_verdict(contract, selection, robustness)
        rows = build_rows_export(masked)

    report = build_report(contract, baseline_results, selection, robustness, verdict)
    report["artifact_hashes"] = {
        "freeze_report_sha256": sha256_file(freeze_report_path),
        "freeze_scores_sha256": loaded["scores_hash"],
    }
    write_artifacts(report, rows, output_prefix)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    report = run_cli(args)
    print(json.dumps({"verdict": report["verdict"]}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
