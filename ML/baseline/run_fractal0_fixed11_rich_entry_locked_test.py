from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ML.baseline import benchmark_fractal0_entry_exit_grid as base
from ML.baseline import benchmark_fractal0_entry_quality_filter as rich


def load_locked_test_split(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep=";").reset_index(drop=True)
    frame["time"] = frame["time"].map(base.parse_project_time)
    frame["split"] = "locked_test"
    frame["split_row_id"] = np.arange(len(frame), dtype=int)
    return frame


def load_fixed_rules(path: Path) -> list[dict[str, Any]]:
    frame = pd.read_csv(path, sep=";")
    required = {
        "original_rank",
        "rule_id",
        "profile_id",
        "model_id",
        "target_id",
        "filter_id",
        "score_cutoff_on_val_select",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"fixed rules CSV missing columns: {missing}")
    if len(frame) != 11:
        raise ValueError(f"expected 11 fixed rules, got {len(frame)}")
    return frame.to_dict(orient="records")


def load_execution_contract(source_artifact_path: Path) -> dict[str, Any]:
    source = json.loads(source_artifact_path.read_text(encoding="utf-8"))
    winner = dict(source["selected_winner"])
    stop_policy = next(item for item in base.stop_policy_grid() if item["stop_policy_id"] == winner["stop_policy_id"])
    entry_rule = next(item for item in base.entry_grid() if item["entry_id"] == winner["entry_id"])
    mask_rule = next(item for item in base.mask_grid() if item["mask_id"] == winner["mask_id"])
    exit_rule = next(item for item in base.exit_grid(shortlist="stop_grid") if item["exit_id"] == winner["exit_id"])
    return {
        "source_selected_winner": winner,
        "stop_policy": stop_policy,
        "entry_rule": entry_rule,
        "mask_rule": mask_rule,
        "exit_rule": exit_rule,
        "spread": float(winner.get("spread", base.CONFIG.canonical_spread)),
    }


def compute_locked_movement_scores(
    locked_entries: pd.DataFrame,
    train_labeled: pd.DataFrame,
    locked_labeled: pd.DataFrame,
    threads: int,
) -> pd.DataFrame:
    from ML.baseline.benchmark_entry_based_amplitude_movement import (
        _align_feature_frames_to_train,
        _numeric_frame,
        build_feature_profile_with_metadata,
        build_movement_targets,
        make_model,
        seeds_for_model,
    )
    from sklearn.preprocessing import RobustScaler

    train_renamed = train_labeled.rename(
        columns={f"up_{h}": f"entry_up_{h}" for h in (3, 6, 12, 24, 48)}
        | {f"dn_{h}": f"entry_dn_{h}" for h in (3, 6, 12, 24, 48)}
    )
    locked_renamed = locked_labeled.rename(
        columns={f"up_{h}": f"entry_up_{h}" for h in (3, 6, 12, 24, 48)}
        | {f"dn_{h}": f"entry_dn_{h}" for h in (3, 6, 12, 24, 48)}
    )
    train_targets, thresholds = build_movement_targets(train_renamed)
    build_movement_targets(locked_renamed, thresholds)

    profile_bundle = build_feature_profile_with_metadata(
        {"train": train_labeled, "locked_test": locked_labeled},
        "simple_combined",
    )
    split_features = _align_feature_frames_to_train(profile_bundle["features"])
    scaler = RobustScaler()
    scaler.fit(_numeric_frame(profile_bundle["features"]["train"]))
    train_x = scaler.transform(split_features["train"])
    locked_x = scaler.transform(split_features["locked_test"])
    train_y = pd.to_numeric(train_targets["entry_movement_3"], errors="coerce").to_numpy(dtype=float)

    predictions = []
    for seed in seeds_for_model("extra_trees_small"):
        model = make_model("extra_trees_small", int(seed), int(threads))
        model.fit(train_x, train_y)
        predictions.append(np.asarray(model.predict(locked_x), dtype=float))
    score = np.median(np.vstack(predictions), axis=0)
    score_frame = pd.DataFrame({"movement_score": score}, index=locked_labeled.index)

    out = locked_entries.copy()
    out["movement_score"] = out["split_row_id"].map(score_frame["movement_score"])
    if out["movement_score"].isna().any():
        out["movement_score"] = out["movement_score"].fillna(float(np.nanmedian(score)))
    return out


def run_locked_test(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    source_rules_csv = Path(args.source_rules_csv)
    source_artifact_path = Path(args.source_artifact)
    locked_test_path = Path(args.locked_test_path)
    output_prefix = Path(args.output_prefix)
    rules = load_fixed_rules(source_rules_csv)
    contract = load_execution_contract(source_artifact_path)
    config = dataclasses.replace(base.CONFIG, execution_ohlc_path=args.execution_ohlc_path)

    preflight = base.preflight_inputs(config)
    if preflight["status"] != "PASS":
        raise SystemExit(f"preflight failed: {preflight['errors']}")

    ohlc = base.load_ohlc(config)
    execution_ohlc = base.prepare_execution_ohlc_index(base.load_ohlc_path(config.execution_ohlc_path))
    splits = base.load_role_splits(config)
    splits["locked_test"] = load_locked_test_split(locked_test_path)
    frozen_scores = base._read_frozen_scores(config)

    stop_policy = contract["stop_policy"]
    entry_rule = contract["entry_rule"]
    exit_rule = contract["exit_rule"]
    active_spread = float(contract["spread"])
    run_base = {**stop_policy, **entry_rule, **contract["mask_rule"], **exit_rule, "spread": active_spread}

    entry_cache: dict[str, pd.DataFrame] = {}
    labels_by_split: dict[str, pd.DataFrame] = {}
    for split in ("train_core", "val_select", "locked_test"):
        entries = base.build_entry_rows(splits[split], ohlc, entry_rule, active_spread, stop_policy, execution_ohlc)
        if split == "locked_test":
            entries = compute_locked_movement_scores(entries, splits["train_core"], splits["locked_test"], int(args.threads))
        else:
            entries = rich.attach_movement_scores(entries, frozen_scores, split)
        entry_cache[split] = entries
        simulated = base._simulate_entries(entries, ohlc, run_base, active_spread, pd.DataFrame(), execution_ohlc)
        labels = rich.build_rich_entry_labels(entries, simulated)
        labels["split"] = split
        labels_by_split[split] = labels
        print(f"prepared split={split} rows={len(entries)} filled={int(entries['filled'].sum()) if len(entries) else 0}", flush=True)

    exit_cache = {("train_core", str(stop_policy["stop_policy_id"]), rich.ENTRY_ID, rich.MASK_ID): entry_cache["train_core"]}
    ml_models, target_rates = base._train_ml_exit_layer(exit_cache, ohlc, int(args.threads), seeds=base.EXIT_MODEL_SEEDS, n_estimators=200)
    scored_decisions: dict[str, pd.DataFrame] = {}
    for split in ("locked_test",):
        decisions = base.build_exit_decision_rows(entry_cache[split].loc[entry_cache[split]["filled"].astype(bool)], ohlc)
        scored_decisions[split] = base.score_exit_models({rich.MASK_ID: ml_models[str(stop_policy["stop_policy_id"])][rich.MASK_ID]}, decisions)

    summary_rows: list[dict[str, Any]] = []
    trade_frames: list[pd.DataFrame] = []
    yearly_frames: list[pd.DataFrame] = []
    side_rows: list[dict[str, Any]] = []

    for index, rule in enumerate(rules, start=1):
        profile_id = str(rule["profile_id"])
        model_id = str(rule["model_id"])
        target_id = str(rule["target_id"])
        filter_id = str(rule["filter_id"])
        cutoff = float(rule["score_cutoff_on_val_select"])
        print(f"rule {index}/11 {rule['rule_id']}", flush=True)

        x_train, _ = rich.build_normalized_rich_feature_frame(entry_cache["train_core"], ohlc, profile_id)
        schema = rich.build_normalized_feature_schema(profile_id, x_train)
        scaler = rich.fit_unit_scaler({"train_core": x_train}, schema)
        x_train_scaled = rich.apply_unit_scaler(x_train, scaler, schema)
        x_fit, y_train = rich.prepare_rich_training_target(entry_cache["train_core"], x_train_scaled, labels_by_split["train_core"], target_id)
        target_spec = next(item for item in rich.rich_target_grid() if item["target_id"] == target_id)
        rich_model = rich.train_rich_entry_model(x_fit, y_train, str(target_spec["kind"]), model_id, int(args.threads), seed=42)

        x_locked_raw, _ = rich.build_normalized_rich_feature_frame(entry_cache["locked_test"], ohlc, profile_id)
        x_locked_scaled = rich.apply_unit_scaler(x_locked_raw, scaler, schema)
        scored_locked = entry_cache["locked_test"].copy()
        scored_locked["rich_entry_score"] = rich.score_rich_entry_model(rich_model, x_locked_scaled, str(target_spec["kind"]))
        scored_locked["split"] = "locked_test"
        scored_locked["profile_id"] = profile_id
        scored_locked["model_id"] = model_id
        scored_locked["target_id"] = target_id
        scored_locked["filter_id"] = filter_id
        filter_spec = next(item for item in rich.rich_filter_grid() if item["filter_id"] == filter_id)
        selected_locked = rich.apply_entry_filter(scored_locked, rich._rich_filter_rule(filter_spec), mode="eval", score_cutoff=cutoff)

        run = {
            **run_base,
            "split": "locked_test",
            "filter_id": filter_id,
            "filter_family": "rich_entry_quality",
            "top_fraction": filter_spec["top_fraction"],
            "score_cutoff_on_val_select": cutoff,
            "entry_filter_score_col": "rich_entry_score",
            "available_trades_before_filter": int(scored_locked["filled"].sum()),
        }
        trades = rich._simulate_for_filter(selected_locked, ohlc, run, scored_decisions["locked_test"], execution_ohlc)
        if not trades.empty:
            metadata = {
                "original_rank": int(rule["original_rank"]),
                "rule_id": str(rule["rule_id"]),
                "profile_id": profile_id,
                "model_id": model_id,
                "target_id": target_id,
                "filter_id": filter_id,
                "score_cutoff_on_val_select": cutoff,
            }
            for key, value in metadata.items():
                trades[key] = value
            trade_frames.append(trades)
            yearly = pd.DataFrame(base.yearly_metrics(trades))
            if not yearly.empty:
                yearly.insert(0, "rule_id", str(rule["rule_id"]))
                yearly.insert(0, "original_rank", int(rule["original_rank"]))
                yearly_frames.append(yearly)
            for side_name, group in trades.groupby("side"):
                side_rows.append({
                    "original_rank": int(rule["original_rank"]),
                    "rule_id": str(rule["rule_id"]),
                    "side": side_name,
                    **base.compute_trade_metrics(group),
                })

        summary = rich._summary_for_filter(trades, run, "locked_test")
        summary.update(
            {
                "original_rank": int(rule["original_rank"]),
                "rule_id": str(rule["rule_id"]),
                "profile_id": profile_id,
                "model_id": model_id,
                "target_id": target_id,
                "filter_id": filter_id,
                "score_cutoff_on_val_select": cutoff,
                "status": "OK",
            }
        )
        summary_rows.append(summary)

    summary_df = pd.DataFrame(summary_rows).sort_values("original_rank")
    trades_df = pd.concat(trade_frames, ignore_index=True) if trade_frames else pd.DataFrame()
    yearly_df = pd.concat(yearly_frames, ignore_index=True) if yearly_frames else pd.DataFrame()
    side_df = pd.DataFrame(side_rows)
    selection_df = summary_df.copy()
    selection_df["decision"] = np.where(
        (pd.to_numeric(selection_df["pf"], errors="coerce") >= 1.20)
        & (pd.to_numeric(selection_df["bs_p05"], errors="coerce") >= 1.00)
        & (pd.to_numeric(selection_df["n_trades"], errors="coerce") >= 100),
        "KEEP_CANDIDATE",
        "REJECT",
    )
    selection_df["reason"] = np.where(
        selection_df["decision"].eq("KEEP_CANDIDATE"),
        "",
        "failed predefined PF/BS/sample-size gate",
    )
    if args.diagnostic_only:
        selection_df["legacy_gate_decision"] = selection_df["decision"]
        selection_df["decision"] = selection_df["decision"].map(
            {
                "KEEP_CANDIDATE": "DIAGNOSTIC_GATE_PASSED",
                "REJECT": "DIAGNOSTIC_GATE_FAILED",
            }
        ).fillna(selection_df["decision"])
        selection_df["allowed_max_verdict"] = "DIAGNOSTIC_ONLY"
        selection_df["decision_reason"] = (
            "ML-exit feature contract and execution convention changed after fixed11 locked_test; "
            "gate is diagnostic only"
        )

    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary_csv": output_prefix.with_name(output_prefix.name + "_summary.csv"),
        "trades_csv": output_prefix.with_name(output_prefix.name + "_trades.csv"),
        "yearly_csv": output_prefix.with_name(output_prefix.name + "_yearly.csv"),
        "side_csv": output_prefix.with_name(output_prefix.name + "_side.csv"),
        "selection_csv": output_prefix.with_name(output_prefix.name + "_selection.csv"),
    }
    summary_df.to_csv(paths["summary_csv"], sep=";", index=False)
    trades_df.to_csv(paths["trades_csv"], sep=";", index=False)
    yearly_df.to_csv(paths["yearly_csv"], sep=";", index=False)
    side_df.to_csv(paths["side_csv"], sep=";", index=False)
    selection_df.to_csv(paths["selection_csv"], sep=";", index=False)

    gate_decision_col = "legacy_gate_decision" if "legacy_gate_decision" in selection_df.columns else "decision"
    kept = selection_df.loc[selection_df[gate_decision_col].eq("KEEP_CANDIDATE")]
    runner_verdict = "candidate_check_required" if len(kept) else "reject"
    artifact = {
        "status": "completed",
        "verdict": "DIAGNOSTIC_ONLY" if args.diagnostic_only else runner_verdict,
        "original_runner_verdict": runner_verdict if args.diagnostic_only else None,
        "decision": "FIXED11_H1_CHRONOLOGY_FIX_DIAGNOSTIC_ONLY" if args.diagnostic_only else "FIXED11_RICH_ENTRY_LOCKED_TEST",
        "allowed_max_verdict": "DIAGNOSTIC_ONLY" if args.diagnostic_only else None,
        "diagnostic_reason": (
            "ML-exit feature contract and execution convention changed after fixed11 locked_test; "
            "rerun is for simulator chronology validation, not candidate selection"
        )
        if args.diagnostic_only
        else None,
        "source_runner": "ML/baseline/benchmark_fractal0_entry_quality_filter.py",
        "source_rules_csv": str(source_rules_csv),
        "source_rules_csv_sha256": base.sha256_file(source_rules_csv),
        "source_artifact": str(source_artifact_path),
        "source_artifact_sha256": base.sha256_file(source_artifact_path),
        "locked_test_path": str(locked_test_path),
        "locked_test_sha256": base.sha256_file(locked_test_path),
        "execution_ohlc_path": config.execution_ohlc_path,
        "execution_ohlc_sha256": base.sha256_file(Path(config.execution_ohlc_path)),
        "h1_ohlc_path": config.ohlc_path,
        "h1_ohlc_sha256": base.sha256_file(Path(config.ohlc_path)),
        "rule_count": int(len(summary_df)),
        "kept_candidates": int(len(kept)),
        "best_pf": float(pd.to_numeric(summary_df["pf"], errors="coerce").max()),
        "best_bs_p05": float(pd.to_numeric(summary_df["bs_p05"], errors="coerce").max()),
        "execution_contract": {
            "stop_policy_id": stop_policy["stop_policy_id"],
            "entry_id": entry_rule["entry_id"],
            "mask_id": contract["mask_rule"]["mask_id"],
            "exit_id": exit_rule["exit_id"],
            "spread": active_spread,
        },
        "execution_ohlc_usage": "limit_fill_timestamp_and_same_h1_post_fill_event_order",
        "ml_exit_feature_contract_status": "PASS",
        "bars_since_fill_0_ml_exit_policy": "excluded_until_post_fill_decision_timestamp_exists",
        "ml_exit_timing_contract": "feature_time <= decision_time <= execution_time",
        "ml_exit_decision_time_columns": {
            "decision_bar_time": "H1 bar timestamp whose closed OHLC values produce ML-exit input features",
            "feature_available_time": "first H1 timestamp when decision-bar OHLC is available",
            "decision_time": "actual ML-exit decision timestamp, equal to feature_available_time",
            "ml_decision_time": "explicit alias for decision_time",
            "first_exit_execution_time": "first executable H1 timestamp for the decision",
        },
        "future_exit_fields_role": "target_or_diagnostic_only",
        "close_now_pnl_r_role": "target_or_diagnostic_only_backward_compatibility_name",
        "fill_execution_time_contract": {
            "column": "fill_execution_time",
            "source_column": "fill_execution_time_source",
            "confirmed_column": "fill_execution_confirmed",
            "confirmed_source": "m5_touch",
        },
        "same_h1_ml_close_policy": "disabled_on_fill_h1_until_real_post_fill_ml_decision_timestamp_exists",
        "missing_m5_fill_policy": "do_not_process_same_h1_exits_as_confirmed_post_fill_events",
        "fill_m5_double_touch_policy": "SL_first_with_ambiguous_true",
        "execution_chronology_counts": {
            "fill_execution_time_source": trades_df.get("fill_execution_time_source", pd.Series(dtype=object)).fillna("missing").value_counts().to_dict() if not trades_df.empty else {},
            "fill_execution_confirmed": int(trades_df.get("fill_execution_confirmed", pd.Series(dtype=bool)).astype(bool).sum()) if not trades_df.empty else 0,
            "same_h1_fill_exit": int((pd.to_datetime(trades_df.get("fill_time"), errors="coerce") == pd.to_datetime(trades_df.get("exit_time"), errors="coerce")).sum()) if not trades_df.empty else 0,
            "same_h1_ml_close": int(((pd.to_datetime(trades_df.get("fill_time"), errors="coerce") == pd.to_datetime(trades_df.get("exit_time"), errors="coerce")) & trades_df.get("close_reason", pd.Series(dtype=object)).eq("ML_CLOSE")).sum()) if not trades_df.empty else 0,
            "ambiguous": int(trades_df.get("ambiguous", pd.Series(dtype=bool)).astype(bool).sum()) if not trades_df.empty else 0,
        },
        "split_roles": {"train_core": "model_training_only", "locked_test": "one_shot_evaluation_only"},
        "current_search_budget": {"fixed_rules": 11, "new_thresholds": 0, "new_profiles": 0, "new_models": 0, "new_filters": 0},
        "movement_score_for_locked_test": "retrained_from_frozen_movement_protocol_for_movement_plus_time_profiles",
        "movement_score_model_contract": {
            "feature_profile": "simple_combined",
            "model": "extra_trees_small",
            "target": "entry_movement_3",
            "normalization_config": {
                "scaler": "RobustScaler",
                "fit_split": "train_core",
                "transform_splits": ["locked_test"],
                "locked_test_used_for_scaler_fit": False,
            },
            "scale_contract": "DIAGNOSTIC_ONLY",
            "normalized_feature_distribution_audit": "not rerun in this debug chronology rerun; inherited frozen movement protocol used for fixed11 compatibility",
        },
        "ml_target_positive_rate_by_split": target_rates,
        "artifacts": {key: str(path) for key, path in paths.items()},
        "elapsed_seconds": round(time.time() - started, 3),
    }
    output_prefix.with_suffix(".json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return artifact


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate 11 fixed normalized rich-entry rules on locked_test.")
    parser.add_argument("--source-rules-csv", default="ML/reports/leaderboard_closure_audit_rules.csv")
    parser.add_argument("--source-artifact", default="ML/reports/fractal0_stop_grid_m5.json")
    parser.add_argument("--locked-test-path", default="DATA/Nero_XAUUSD_test_labeled.csv")
    parser.add_argument("--execution-ohlc-path", default="MT/MQL4/Files/XAUUSD_M5_OHLC.csv")
    parser.add_argument("--output-prefix", default="ML/reports/fractal0_fixed11_rich_entry_locked_test")
    parser.add_argument("--threads", type=int, default=base.CONFIG.default_threads)
    parser.add_argument("--diagnostic-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    artifact = run_locked_test(parse_args())
    print(json.dumps({"verdict": artifact["verdict"], "best_pf": artifact["best_pf"], "kept": artifact["kept_candidates"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
