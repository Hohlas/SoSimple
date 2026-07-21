# =============================================================================
# Файл: benchmark_fractal0_entry_quality_filter.py
# Назначение: Research-runner ML-entry фильтра для E3 Fractal0 поверх
#   существующего stop-grid/M5 runner без отдельной копии симулятора.
# Обновлён: 2026-07-21
# Примечания:
#   - locked_test не открывается; максимальный verdict — research_only.
# =============================================================================
from __future__ import annotations

import argparse
import dataclasses
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import ML.baseline.benchmark_fractal0_entry_exit_grid as base


DEFAULT_STOP_GRID_ARTIFACT = "ML/reports/fractal0_stop_grid_m5.json"
DEFAULT_OUTPUT_PREFIX = "ML/reports/fractal0_entry_quality_filter"
ENTRY_ID = "E3_open_pullback_1_0atr"
MASK_ID = "M0_no_mask"

ENTRY_FEATURE_COLUMNS = [
    "side_buy",
    "ATR",
    "entry_to_fractal0_atr",
    "stop_distance_atr",
    "r_value_atr",
]
SCORE_DIAGNOSTIC_COLUMNS = [
    "movement_score",
    "stop_distance_atr",
    "r_value_atr",
    "entry_quality_score",
    "entry_avoid_sl_score",
]


def _path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def entry_filter_grid() -> list[dict[str, object]]:
    filters: list[dict[str, object]] = [
        {"filter_id": "M0_no_mask", "family": "none", "score_col": None, "top_fraction": 1.0}
    ]
    for fraction in (0.50, 0.30, 0.20, 0.10):
        filters.append({"filter_id": f"movement_top{int(fraction * 100)}", "family": "movement", "score_col": "movement_score", "top_fraction": fraction})
    for fraction in (0.50, 0.30):
        filters.append({"filter_id": f"simple_stop_distance_top{int(fraction * 100)}", "family": "simple_stop_distance", "score_col": "stop_distance_atr", "top_fraction": fraction})
    for fraction in (0.50, 0.30):
        filters.append({"filter_id": f"simple_r_value_top{int(fraction * 100)}", "family": "simple_r_value", "score_col": "r_value_atr", "top_fraction": fraction})
    for fraction in (0.50, 0.30, 0.20, 0.10):
        filters.append({"filter_id": f"entry_quality_top{int(fraction * 100)}", "family": "entry_quality", "score_col": "entry_quality_score", "top_fraction": fraction})
    for fraction in (0.50, 0.30, 0.20, 0.10):
        filters.append({"filter_id": f"entry_avoid_sl_top{int(fraction * 100)}", "family": "entry_avoid_sl", "score_col": "entry_avoid_sl_score", "top_fraction": fraction})
    return filters


def score_cutoff_for_top_fraction(rows: pd.DataFrame, score_col: str, fraction: float) -> float:
    if score_col not in rows.columns:
        return math.nan
    scores = pd.to_numeric(rows[score_col], errors="coerce").dropna()
    if scores.empty:
        return math.nan
    count = max(1, int(math.ceil(len(scores) * float(fraction))))
    return float(scores.sort_values(ascending=False).iloc[count - 1])


def select_top_fraction(rows: pd.DataFrame, score_col: str, fraction: float) -> pd.DataFrame:
    if score_col not in rows.columns:
        return rows.iloc[0:0].copy()
    scored = rows.assign(_score=pd.to_numeric(rows[score_col], errors="coerce")).dropna(subset=["_score"])
    if scored.empty:
        return rows.copy()
    count = max(1, int(math.ceil(len(scored) * float(fraction))))
    return scored.sort_values("_score", ascending=False).head(count).drop(columns=["_score"]).copy()


def build_entry_labels(trades: pd.DataFrame) -> pd.DataFrame:
    out = trades.copy()
    out["target_entry_good"] = (pd.to_numeric(out["pnl_r"], errors="coerce") > 0.0).astype(int)
    out["target_entry_avoid_sl"] = (~out["close_reason"].astype(str).eq("SL")).astype(int)
    return out


def build_entry_feature_frame(entries: pd.DataFrame) -> pd.DataFrame:
    out = entries.copy()
    atr = pd.to_numeric(out["ATR"], errors="coerce").replace(0, pd.NA)
    entry_bid_equivalent = pd.to_numeric(
        out["planned_entry_bid_equivalent"] if "planned_entry_bid_equivalent" in out else out["entry_bid_equivalent"],
        errors="coerce",
    )
    protective_stop = pd.to_numeric(
        out["planned_protective_stop_price"] if "planned_protective_stop_price" in out else out["protective_stop_price"],
        errors="coerce",
    )
    r_value = pd.to_numeric(out["planned_r_value"] if "planned_r_value" in out else out["r_value"], errors="coerce")
    out["side_buy"] = out["side"].astype(str).eq("BUY").astype(int)
    out["entry_to_fractal0_atr"] = (
        entry_bid_equivalent - pd.to_numeric(out["fractal0_price"], errors="coerce")
    ) / atr
    out["stop_distance_atr"] = (
        entry_bid_equivalent - protective_stop
    ).abs() / atr
    out["r_value_atr"] = r_value / atr
    return out


def train_entry_models(
    train_rows: pd.DataFrame,
    threads: int,
    seeds: tuple[int, ...] = (42, 43, 44),
    n_estimators: int = 200,
) -> dict[str, object]:
    frame = build_entry_feature_frame(train_rows)
    x = frame[ENTRY_FEATURE_COLUMNS].fillna(0.0)
    models: dict[str, object] = {}
    targets = {"entry_quality_score": "target_entry_good", "entry_avoid_sl_score": "target_entry_avoid_sl"}
    for score_col, target_col in targets.items():
        y = frame[target_col].astype(int)
        if y.nunique() < 2:
            models[score_col] = [float(y.iloc[0]) if len(y) else 0.0]
            continue
        fitted = []
        for seed in seeds:
            clf = ExtraTreesClassifier(n_estimators=n_estimators, max_depth=8, min_samples_leaf=50, random_state=seed, n_jobs=threads)
            clf.fit(x, y)
            fitted.append(clf)
        models[score_col] = fitted
    return models


def score_entry_models(models: dict[str, object], rows: pd.DataFrame) -> pd.DataFrame:
    out = build_entry_feature_frame(rows)
    x = out[ENTRY_FEATURE_COLUMNS].fillna(0.0)
    for score_col, fitted in models.items():
        values = []
        for model in fitted:
            values.append(np.full(len(out), model) if isinstance(model, float) else model.predict_proba(x)[:, 1])
        out[score_col] = np.median(np.vstack(values), axis=0) if values else 0.0
    return out


def apply_entry_filter(
    entries: pd.DataFrame,
    filter_rule: dict[str, object],
    mode: str = "select",
    score_cutoff: float | None = None,
) -> pd.DataFrame:
    if filter_rule["family"] == "none":
        out = entries.copy()
        out["entry_filter_selected"] = True
        out["entry_filter_score_cutoff"] = None
        out.attrs["score_cutoff_on_val_select"] = None
        return out
    score_col = str(filter_rule["score_col"])
    if mode == "select":
        cutoff = score_cutoff_for_top_fraction(entries, score_col, float(filter_rule["top_fraction"]))
    elif mode == "eval":
        if score_cutoff is None:
            raise ValueError("score_cutoff is required when applying filter in eval mode")
        cutoff = float(score_cutoff)
    else:
        raise ValueError(f"unknown filter mode: {mode}")
    out = entries.loc[pd.to_numeric(entries[score_col], errors="coerce") >= cutoff].copy()
    out["entry_filter_selected"] = True
    out["entry_filter_score_cutoff"] = cutoff
    out.attrs["score_cutoff_on_val_select"] = cutoff
    return out


def load_stop_grid_choice(path: str | Path, explicit_stop_policy_id: str | None) -> dict[str, object]:
    artifact_path = _path(path)
    if not artifact_path.exists():
        raise SystemExit(f"entry-quality full run requires completed stop-grid artifact: {artifact_path}")
    data = json.loads(artifact_path.read_text(encoding="utf-8"))
    if data.get("locked_test") != "not_opened":
        raise SystemExit("locked_test must remain not_opened")
    summary_path = artifact_path.with_name(artifact_path.stem + "_summary.csv")
    completed = int(data.get("progress", {}).get("completed", 0))
    if completed == 0 and summary_path.exists():
        completed = int(sum(1 for _ in summary_path.open("r", encoding="utf-8", errors="ignore")) - 1)
    expected = int(data.get("current_search_budget", {}).get("expected_completed_without_stress", 0))
    if expected and completed < expected:
        raise SystemExit("entry-quality full run requires completed stop-grid")
    winner = data.get("selected_winner", {})
    stop_policy_id = explicit_stop_policy_id or winner.get("stop_policy_id")
    if not stop_policy_id:
        raise SystemExit("entry-quality full run requires explicit stop_policy_id")
    stop_policy = next((item for item in base.stop_policy_grid() if item["stop_policy_id"] == stop_policy_id), None)
    if stop_policy is None:
        raise SystemExit(f"unknown stop_policy_id: {stop_policy_id}")
    exit_id = str(winner.get("exit_id") or "X0_fixed_r_0_7")
    exit_rule = next((item for item in base.exit_grid(shortlist="stop_grid") if item["exit_id"] == exit_id), None)
    if exit_rule is None:
        raise SystemExit(f"stop-grid winner exit_id is unavailable: {exit_id}")
    return {"artifact": data, "stop_policy": stop_policy, "exit_rule": exit_rule, "stop_policy_source": "fractal0_stop_grid_m5_selected_or_explicit"}


def attach_movement_scores(entries: pd.DataFrame, scores: pd.DataFrame, split: str) -> pd.DataFrame:
    split_name = "train" if split == "train_core" else split
    movement = scores.loc[scores["split"].astype(str).eq(split_name), ["split_row_id", "score"]].rename(columns={"score": "movement_score"})
    out = entries.drop(columns=["movement_score"], errors="ignore").merge(movement, on="split_row_id", how="left")
    out["movement_score_available"] = out["movement_score"].notna()
    return out


def _entry_rule() -> dict[str, object]:
    return next(item for item in base.entry_grid() if item["entry_id"] == ENTRY_ID)


def _simulate_for_filter(entries: pd.DataFrame, ohlc: pd.DataFrame, run: dict[str, object], scored_decisions: pd.DataFrame, execution_ohlc: pd.DataFrame | None) -> pd.DataFrame:
    trades = base._simulate_entries(entries, ohlc, run, base.CONFIG.canonical_spread, scored_decisions, execution_ohlc)
    if trades.empty:
        return trades
    trades["filter_id"] = run["filter_id"]
    trades["score_cutoff_on_val_select"] = run.get("score_cutoff_on_val_select")
    trades["entry_filter_score_col"] = run.get("entry_filter_score_col")
    trades["spread"] = base.CONFIG.canonical_spread
    return trades


def _summary_for_filter(trades: pd.DataFrame, run: dict[str, object], split: str) -> dict[str, object]:
    if trades.empty and "pnl_r" not in trades.columns:
        trades = pd.DataFrame(
            columns=[
                "pnl_r",
                "close_reason",
                "ambiguous",
                "risk_distance_atr",
                "tp_distance_atr",
                "exit_time",
            ]
        )
    summary = base._summary_from_trades(trades, run, split, base.CONFIG.canonical_spread)
    summary["filter_id"] = run["filter_id"]
    summary["filter_family"] = run["filter_family"]
    summary["top_fraction"] = run["top_fraction"]
    summary["score_cutoff_on_val_select"] = run.get("score_cutoff_on_val_select")
    summary["entry_filter_score_col"] = run.get("entry_filter_score_col")
    summary["selected_fraction"] = float(len(trades) / max(1, int(run.get("available_trades_before_filter", 0))))
    summary["sl_rate"] = float(trades["close_reason"].astype(str).eq("SL").mean()) if len(trades) else 0.0
    return summary


def score_distribution_diagnostics(scores: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for split, group in scores.groupby("split", dropna=False):
        for score_col in SCORE_DIAGNOSTIC_COLUMNS:
            if score_col not in group.columns:
                continue
            series = pd.to_numeric(group[score_col], errors="coerce")
            valid = series.dropna()
            row: dict[str, object] = {
                "split": split,
                "score_col": score_col,
                "rows": int(len(series)),
                "valid_rows": int(len(valid)),
                "nan_rate": float(series.isna().mean()) if len(series) else 0.0,
                "zero_rate": float(series.fillna(0.0).eq(0.0).mean()) if len(series) else 0.0,
            }
            for q in (0.10, 0.30, 0.50, 0.70, 0.90):
                row[f"p{int(q * 100):02d}"] = float(valid.quantile(q)) if len(valid) else None
            rows.append(row)
    return rows


def previous_s0_x0_baseline(stop_grid_artifact: dict[str, object]) -> dict[str, object] | None:
    artifacts = stop_grid_artifact.get("artifacts", {}) if isinstance(stop_grid_artifact.get("artifacts"), dict) else {}
    summary_path = artifacts.get("summary_csv") or "ML/reports/fractal0_stop_grid_m5_summary.csv"
    path = _path(str(summary_path))
    if not path.exists():
        return None
    summary = pd.read_csv(path, sep=";", usecols=["stop_policy_id", "entry_id", "mask_id", "exit_id", "split", "n_trades", "pf", "bs_p05", "mean_pnl_r", "max_drawdown_r"])
    row = summary.loc[
        summary["stop_policy_id"].eq("S0_current_0_5")
        & summary["entry_id"].eq(ENTRY_ID)
        & summary["mask_id"].eq(MASK_ID)
        & summary["exit_id"].eq("X0_fixed_r_0_7")
        & summary["split"].eq("val_eval")
    ]
    return row.iloc[0].to_dict() if not row.empty else None


def select_entry_filter_winner(summary: pd.DataFrame) -> dict[str, object]:
    val_select = summary.loc[summary["split"].eq("val_select")].copy()
    primary = val_select.loc[val_select["filter_id"].astype(str).str.startswith("entry_quality_")].copy()
    candidates = primary if not primary.empty else val_select
    gated = candidates[(candidates["n_trades"] >= 100) & (candidates["mean_pnl_r"] > 0)].copy()
    if gated.empty:
        gated = candidates.copy()
    gated = gated.sort_values(["bs_p05", "pf", "n_trades"], ascending=[False, False, False])
    winner = gated.iloc[0].to_dict()
    winner["selection_metric"] = "val_select BS_p05 within primary entry_quality family"
    return winner


def evaluate_winner_on_val_eval(winner: dict[str, object], summary: pd.DataFrame) -> dict[str, object]:
    rows = summary.loc[(summary["split"].eq("val_eval")) & (summary["filter_id"].eq(winner["filter_id"]))]
    return rows.iloc[0].to_dict() if not rows.empty else {}


def run_selection_permutation(summary: pd.DataFrame, trades: pd.DataFrame, repeats: int, seed: int) -> dict[str, object]:
    observed = float(select_entry_filter_winner(summary).get("bs_p05") or 0.0)
    val_select = trades.loc[trades["split"].eq("val_select")].reset_index(drop=True)
    if val_select.empty or repeats <= 0:
        return {"method": "block_shuffled_val_select_pnl_r", "null_repeats": int(repeats), "observed_winner_bs_p05": observed, "empirical_p_value": None, "status": "SKIPPED"}
    rng = np.random.default_rng(seed)
    pnl = pd.to_numeric(val_select["pnl_r"], errors="coerce").fillna(0.0).to_numpy()
    null = []
    for _ in range(repeats):
        shuffled = val_select.copy()
        shuffled["pnl_r"] = rng.permutation(pnl)
        rows = []
        for filter_id, group in shuffled.groupby("filter_id", sort=False):
            run = {"stop_policy_id": group["stop_policy_id"].iloc[0], "entry_id": ENTRY_ID, "mask_id": MASK_ID, "exit_id": group["exit_id"].iloc[0], "filter_id": filter_id}
            row = base._summary_from_trades(group, run, "val_select", base.CONFIG.canonical_spread, n_bootstrap=50)
            row["filter_id"] = filter_id
            rows.append(row)
        null.append(float(select_entry_filter_winner(pd.DataFrame(rows)).get("bs_p05") or 0.0))
    p_value = (1 + sum(value >= observed for value in null)) / (1 + len(null))
    return {"method": "block_shuffled_val_select_pnl_r", "null_repeats": int(repeats), "observed_winner_bs_p05": observed, "empirical_p_value": float(p_value), "status": "PASS" if p_value <= 0.10 else "RESEARCH_HINT", "null_best_bs_p05": null}


def run_entry_quality(args: argparse.Namespace) -> dict[str, object]:
    started = time.time()
    print("start fractal0_entry_quality_filter", flush=True)
    choice = load_stop_grid_choice(args.stop_grid_artifact, args.stop_policy_id)
    config = dataclasses.replace(base.CONFIG, output_prefix=args.output_prefix, execution_ohlc_path=args.execution_ohlc_path)
    preflight = base.preflight_inputs(config)
    preflight["stop_grid_artifact"] = {"path": str(_path(args.stop_grid_artifact)), "sha256": base.sha256_file(_path(args.stop_grid_artifact))}
    preflight["input_artifact_hashes"]["stop_grid_artifact"] = preflight["stop_grid_artifact"]["sha256"]
    print(f"preflight {preflight['status']}", flush=True)
    if preflight["status"] != "PASS":
        raise SystemExit(f"preflight failed: {preflight['errors']}")

    ohlc = base.load_ohlc(config)
    execution_ohlc = base.prepare_execution_ohlc_index(base.load_ohlc_path(config.execution_ohlc_path)) if config.execution_ohlc_path else None
    splits = base.load_role_splits(config)
    if args.smoke_limit_filters:
        splits = {name: frame.head(700).copy().reset_index(drop=True) for name, frame in splits.items()}
        for name, frame in splits.items():
            frame["split"] = name
            frame["split_row_id"] = np.arange(len(frame), dtype=int)
    frozen_scores = base._read_frozen_scores(config)

    stop_policy = choice["stop_policy"]
    exit_rule = choice["exit_rule"]
    run_base = {**stop_policy, **_entry_rule(), **{"mask_id": MASK_ID, "kind": "none"}, **exit_rule, "spread": base.CONFIG.canonical_spread}
    entry_cache = {}
    for split, rows in splits.items():
        entries = base.build_entry_rows(rows, ohlc, _entry_rule(), base.CONFIG.canonical_spread, stop_policy)
        entries = attach_movement_scores(entries, frozen_scores, split)
        entry_cache[split] = entries
        print(f"prepared entries split={split} rows={len(entries)} filled={int(entries['filled'].sum()) if len(entries) else 0}", flush=True)

    train_trade_labels = base._simulate_entries(entry_cache["train_core"], ohlc, run_base, base.CONFIG.canonical_spread, pd.DataFrame(), execution_ohlc)
    labelled = build_entry_labels(train_trade_labels)
    train_rows = entry_cache["train_core"].merge(labelled[["position_id", "target_entry_good", "target_entry_avoid_sl"]], on="position_id", how="inner")
    models = train_entry_models(train_rows, int(args.threads), seeds=(42,) if args.smoke_limit_filters else (42, 43, 44), n_estimators=25 if args.smoke_limit_filters else 200)

    scored_entries = {split: score_entry_models(models, rows) for split, rows in entry_cache.items()}
    scored_entries = {split: build_entry_feature_frame(rows) for split, rows in scored_entries.items()}

    exit_cache = {("train_core", str(stop_policy["stop_policy_id"]), ENTRY_ID, MASK_ID): entry_cache["train_core"]}
    ml_models, target_rates = base._train_ml_exit_layer(exit_cache, ohlc, int(args.threads), seeds=(42,) if args.smoke_limit_filters else base.EXIT_MODEL_SEEDS, n_estimators=25 if args.smoke_limit_filters else 200)
    scored_decisions = {}
    for split in ("val_select", "val_eval"):
        decisions = base.build_exit_decision_rows(scored_entries[split].loc[scored_entries[split]["filled"].astype(bool)], ohlc)
        scored_decisions[split] = base.score_exit_models({MASK_ID: ml_models[str(stop_policy["stop_policy_id"])][MASK_ID]}, decisions)

    filters = entry_filter_grid()[: args.smoke_limit_filters] if args.smoke_limit_filters else entry_filter_grid()
    summary_rows: list[dict[str, object]] = []
    trade_frames: list[pd.DataFrame] = []
    score_rows: list[pd.DataFrame] = []
    cutoffs: dict[str, float | None] = {}
    for split in ("val_select", "val_eval"):
        score_rows.append(scored_entries[split].assign(split=split))
    for filter_rule in filters:
        selected_by_split: dict[str, pd.DataFrame] = {}
        selected = apply_entry_filter(scored_entries["val_select"], filter_rule, mode="select")
        cutoffs[str(filter_rule["filter_id"])] = selected.attrs.get("score_cutoff_on_val_select")
        selected_by_split["val_select"] = selected
        selected_by_split["val_eval"] = apply_entry_filter(scored_entries["val_eval"], filter_rule, mode="eval", score_cutoff=cutoffs[str(filter_rule["filter_id"])]) if filter_rule["family"] != "none" else apply_entry_filter(scored_entries["val_eval"], filter_rule)
        for split, selected_entries in selected_by_split.items():
            run = {
                **run_base,
                "split": split,
                "filter_id": filter_rule["filter_id"],
                "filter_family": filter_rule["family"],
                "top_fraction": filter_rule["top_fraction"],
                "score_cutoff_on_val_select": cutoffs[str(filter_rule["filter_id"])],
                "entry_filter_score_col": filter_rule["score_col"],
                "available_trades_before_filter": int(scored_entries[split]["filled"].sum()) if "filled" in scored_entries[split] else len(scored_entries[split]),
            }
            trades = _simulate_for_filter(selected_entries, ohlc, run, scored_decisions[split], execution_ohlc)
            if not trades.empty:
                trade_frames.append(trades)
            summary_rows.append(_summary_for_filter(trades, run, split))
        print(f"filter done {filter_rule['filter_id']} elapsed={time.time() - started:.1f}", flush=True)

    summary = pd.DataFrame(summary_rows)
    non_empty_trade_frames = [frame.dropna(axis=1, how="all") for frame in trade_frames if not frame.empty]
    trades = pd.concat(non_empty_trade_frames, ignore_index=True) if non_empty_trade_frames else pd.DataFrame()
    for column in ("tp_distance_atr",):
        if column not in trades.columns:
            trades[column] = np.nan
    scores = pd.concat(score_rows, ignore_index=True) if score_rows else pd.DataFrame()
    winner = select_entry_filter_winner(summary)
    val_eval = evaluate_winner_on_val_eval(winner, summary)
    winner_trades = trades.loc[(trades["split"].eq("val_eval")) & (trades["filter_id"].eq(winner["filter_id"]))].copy() if not trades.empty else pd.DataFrame()
    yearly = pd.DataFrame([{**{"filter_id": winner["filter_id"], "split": "val_eval"}, **row} for row in base.yearly_metrics(winner_trades)])
    permutation = run_selection_permutation(summary, trades, int(args.permutation_repeats), base.CONFIG.permutation_seed)
    score_diagnostics = score_distribution_diagnostics(scores)
    previous_baseline = previous_s0_x0_baseline(choice["artifact"])

    prefix = _path(args.output_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(prefix.with_name(prefix.name + "_summary.csv"), sep=";", index=False)
    trades.to_csv(prefix.with_name(prefix.name + "_trades.csv"), sep=";", index=False)
    scores.to_csv(prefix.with_name(prefix.name + "_scores.csv"), sep=";", index=False)
    yearly.to_csv(prefix.with_name(prefix.name + "_yearly.csv"), sep=";", index=False)
    pd.DataFrame(score_diagnostics).to_csv(prefix.with_name(prefix.name + "_score_diagnostics.csv"), sep=";", index=False)
    pd.DataFrame(permutation.get("null_best_bs_p05", []), columns=["null_best_bs_p05"]).to_csv(prefix.with_name(prefix.name + "_permutation.csv"), sep=";", index=False)
    artifact = {
        "status": "completed",
        "experiment": "fractal0_entry_quality_filter",
        "verdict": "research_only",
        "lifecycle_status": "research_hint" if float(val_eval.get("bs_p05") or 0.0) < float(summary.loc[(summary["split"].eq("val_eval")) & (summary["filter_id"].eq("M0_no_mask")), "bs_p05"].iloc[0]) else "research_hypothesis",
        "allowed_max_verdict": "research_only",
        "locked_test": "not_opened",
        "stop_policy_id": stop_policy["stop_policy_id"],
        "stop_policy_source": choice["stop_policy_source"],
        "exit_policy_id_used_for_entry_labels": exit_rule["exit_id"],
        "entry_id": ENTRY_ID,
        "selected_winner": winner,
        "val_select_winner_metrics": winner,
        "val_eval_winner_metrics": val_eval,
        "filter_id": winner.get("filter_id"),
        "score_cutoff_on_val_select": winner.get("score_cutoff_on_val_select"),
        "actual_val_eval_selected_fraction": val_eval.get("selected_fraction"),
        "actual_val_eval_selected_trades": val_eval.get("n_trades"),
        "split_roles": {
            "train_core": "trains ML-exit and ML-entry",
            "val_select": "chooses filter family and score_cutoff_on_val_select",
            "val_eval": "evaluates fixed filter and fixed cutoff without reselection",
            "locked_test": "not_opened",
        },
        "forbidden_interpretations": ["candidate", "tradable", "live_ready", "production", "permission_to_open_locked_test"],
        "entry_feature_columns": ENTRY_FEATURE_COLUMNS,
        "entry_feature_contract": {
            "decision_time": "pre_order_after_signal_before_limit_order_send",
            "price_basis": "planned limit/stop/R fields, not post-fill outcome fields",
            "forbidden_columns": ["pnl_r", "close_reason", "hold_bars", "exit_time", "future_*", "target_*", "target_exit_*", "target_entry_*"],
        },
        "entry_label_contract": {
            "target_entry_good": "1 if pnl_r > 0 else 0, built from train_core simulated trades only",
            "target_entry_avoid_sl": "1 if close_reason != 'SL' else 0, built from train_core simulated trades only",
        },
        "filter_contract": {
            "val_select": "top fraction chooses score_cutoff_on_val_select using finite score rows only",
            "val_eval": "applies score >= score_cutoff_on_val_select; does not recalculate top fraction on val_eval",
            "simple_baselines": "simple top fractions are computed on finite planned geometry scores",
        },
        "input_artifact_hashes": preflight["input_artifact_hashes"],
        "current_search_budget": {"filters": len(filters), "splits": 2, "completed": int(len(summary)), "permutation_repeats": int(args.permutation_repeats)},
        "cumulative_search_budget": {"parent_stop_grid": choice["artifact"].get("cumulative_search_budget"), "entry_quality_filters": len(filters)},
        "target_rates": {"train_core": {col: float(train_rows[col].mean()) for col in ("target_entry_good", "target_entry_avoid_sl") if col in train_rows}},
        "permutation": permutation,
        "score_distribution_diagnostics": score_diagnostics,
        "comparison_controls": {
            "s2_e3_m0_x2_no_mask": summary.loc[(summary["split"].eq("val_eval")) & (summary["filter_id"].eq("M0_no_mask"))].iloc[0].to_dict(),
            "previous_s0_e3_m0_x0_baseline": previous_baseline,
        },
        "preflight": preflight,
        "artifacts": {
            "summary_csv": str(prefix.with_name(prefix.name + "_summary.csv")),
            "trades_csv": str(prefix.with_name(prefix.name + "_trades.csv")),
            "scores_csv": str(prefix.with_name(prefix.name + "_scores.csv")),
            "yearly_csv": str(prefix.with_name(prefix.name + "_yearly.csv")),
            "score_diagnostics_csv": str(prefix.with_name(prefix.name + "_score_diagnostics.csv")),
            "permutation_csv": str(prefix.with_name(prefix.name + "_permutation.csv")),
        },
    }
    prefix.with_suffix(".json").write_text(json.dumps(artifact, ensure_ascii=True, indent=2, default=str), encoding="utf-8")
    print("finished fractal0_entry_quality_filter", flush=True)
    return artifact


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--threads", type=int, default=base.CONFIG.default_threads)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--output-prefix", default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument("--execution-ohlc-path", default="MT/MQL4/Files/XAUUSD_M5_OHLC.csv")
    parser.add_argument("--stop-policy-id", default="")
    parser.add_argument("--stop-grid-artifact", default=DEFAULT_STOP_GRID_ARTIFACT)
    parser.add_argument("--permutation-repeats", type=int, default=200)
    parser.add_argument("--smoke-limit-filters", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    run_entry_quality(parse_args(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
