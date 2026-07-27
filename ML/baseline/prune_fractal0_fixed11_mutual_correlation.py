from __future__ import annotations

# =============================================================================
# Файл: prune_fractal0_fixed11_mutual_correlation.py
# Назначение: Read-only pruning 11 fixed Fractal0 rules by mutual overlap.
# Обновлён: 2026-07-27
# Зависимости:
#   Входные данные:
#     - ML/reports/fractal0_fixed11_candidate_audit.json
#     - ML/reports/fractal0_fixed11_rich_entry_locked_test_*.csv
#   Выходные данные:
#     - ML/reports/fractal0_fixed11_mutual_correlation_pruning_*
# Использование:
#   ./.venv/bin/python ML/baseline/prune_fractal0_fixed11_mutual_correlation.py
# Примечания:
#   - Не обучает, не симулирует и не выбирает winner по locked_test.
# =============================================================================

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REQUIRED_TRADE_COLUMNS = {
    "rule_id",
    "original_rank",
    "profile_id",
    "model_id",
    "target_id",
    "filter_id",
    "position_id",
    "split_row_id",
    "fill_index",
    "signal_time",
    "fill_time",
    "exit_time",
    "side",
    "pnl_r",
    "hold_bars",
}

STAGE_METADATA = {
    "lifecycle_status": "post_locked_test_read_only_pruning",
    "stage_level": "проверочный audit/disclosure, без повышения выше candidate",
    "hypothesis": "часть из 11 already-passed fixed rules может быть фактически одним и тем же сигналом",
    "task_type": "portfolio/correlation audit of frozen rules",
    "decision_unit": "fixed rule and trade event",
    "decision_time": "inherited from fixed-11 locked-test execution contract",
    "current_search_budget": "0_new_rules",
    "cumulative_search_budget": "inherited_from_fixed11_candidate_audit",
    "origin_bias": "follow_up_required_from_fixed11_candidate_audit",
    "allowed_max_verdict": "candidate_not_trading_ready",
    "allowed_max_verdict_note": "local stage interpretation cap, not a methodology verdict value",
    "next_probe_freeze": "retained subset only; same rules/cutoffs/execution contract; no new locked_test winner selection",
    "forbidden_interpretations": [
        "retained subset is not trading-ready",
        "pruning does not improve profitability",
        "dropped duplicate rules are not bad rules",
    ],
}


@dataclass(frozen=True)
class Fixed11Inputs:
    audit: dict[str, Any]
    summary: pd.DataFrame
    selection: pd.DataFrame
    trades: pd.DataFrame
    paths: dict[str, str]
    sha256: dict[str, str]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_paths(input_prefix: Path, audit_json: Path) -> dict[str, Path]:
    return {
        "audit_json": audit_json,
        "summary_csv": input_prefix.with_name(input_prefix.name + "_summary.csv"),
        "selection_csv": input_prefix.with_name(input_prefix.name + "_selection.csv"),
        "trades_csv": input_prefix.with_name(input_prefix.name + "_trades.csv"),
    }


def normalize_fixed11_trades(trades: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(REQUIRED_TRADE_COLUMNS - set(trades.columns))
    if missing:
        raise ValueError(f"fixed11 trades missing columns: {missing}")
    frame = trades[list(REQUIRED_TRADE_COLUMNS)].copy()
    frame["rule_id"] = frame["rule_id"].astype(str)
    frame["original_rank"] = pd.to_numeric(frame["original_rank"], errors="raise").astype(int)
    frame["profile_id"] = frame["profile_id"].astype(str)
    frame["model_id"] = frame["model_id"].astype(str)
    frame["target_id"] = frame["target_id"].astype(str)
    frame["filter_id"] = frame["filter_id"].astype(str)
    frame["position_id"] = frame["position_id"].astype(str)
    frame["split_row_id"] = pd.to_numeric(frame["split_row_id"], errors="raise").astype(int)
    frame["fill_index"] = pd.to_numeric(frame["fill_index"], errors="raise").astype(int)
    frame["signal_time"] = pd.to_datetime(frame["signal_time"], errors="raise")
    frame["fill_time"] = pd.to_datetime(frame["fill_time"], errors="raise")
    frame["exit_time"] = pd.to_datetime(frame["exit_time"], errors="raise")
    frame["pnl_r"] = pd.to_numeric(frame["pnl_r"], errors="raise").astype(float)
    frame["hold_bars"] = pd.to_numeric(frame["hold_bars"], errors="raise").astype(int)
    side_map = {"BUY": 1, "SELL": -1}
    frame["side"] = frame["side"].astype(str)
    bad_sides = sorted(set(frame["side"]) - set(side_map))
    if bad_sides:
        raise ValueError(f"unsupported side values: {bad_sides}")
    frame["direction"] = frame["side"].map(side_map).astype(int)
    required_non_null = ["rule_id", "position_id", "signal_time", "fill_time", "exit_time", "side", "pnl_r"]
    if frame[required_non_null].isna().any().any():
        raise ValueError("fixed11 trades contain null values in required fields")
    duplicate_trade_keys = frame.duplicated(["rule_id", "position_id"]).sum()
    if int(duplicate_trade_keys):
        raise ValueError("fixed11 trades contain duplicate rule_id/position_id keys")
    columns = [
        "rule_id",
        "original_rank",
        "profile_id",
        "model_id",
        "target_id",
        "filter_id",
        "position_id",
        "split_row_id",
        "fill_index",
        "signal_time",
        "fill_time",
        "exit_time",
        "side",
        "direction",
        "pnl_r",
        "hold_bars",
    ]
    return frame[columns].sort_values(["rule_id", "fill_time", "signal_time", "position_id"], kind="stable").reset_index(drop=True)


def load_inputs(input_prefix: Path, audit_json: Path) -> Fixed11Inputs:
    paths = _artifact_paths(input_prefix, audit_json)
    missing_paths = [str(path) for path in paths.values() if not path.exists()]
    if missing_paths:
        raise ValueError(f"missing input artifacts: {missing_paths}")
    audit = json.loads(paths["audit_json"].read_text(encoding="utf-8"))
    if audit.get("overall_decision") != "candidate_audit_passed":
        raise ValueError("prior audit must have overall_decision=candidate_audit_passed")
    summary = pd.read_csv(paths["summary_csv"], sep=";")
    selection = pd.read_csv(paths["selection_csv"], sep=";")
    trades = normalize_fixed11_trades(pd.read_csv(paths["trades_csv"], sep=";", usecols=lambda c: c in REQUIRED_TRADE_COLUMNS))
    if len(selection) != 11 or int(selection["rule_id"].nunique()) != 11:
        raise ValueError("selection must contain exactly 11 unique rules")
    if len(summary) != 11 or int(summary["rule_id"].nunique()) != 11:
        raise ValueError("summary must contain exactly 11 unique rules")
    selection_rules = set(selection["rule_id"].astype(str))
    summary_rules = set(summary["rule_id"].astype(str))
    trade_rules = set(trades["rule_id"].astype(str))
    if selection_rules != summary_rules or selection_rules != trade_rules:
        raise ValueError("summary, selection and trades rule_id sets must match")
    if not selection["decision"].eq("KEEP_CANDIDATE").all():
        raise ValueError("all 11 fixed rules must be KEEP_CANDIDATE before pruning")
    actual_counts = trades.groupby("rule_id").size().rename("actual_n_trades")
    expected_counts = summary.set_index("rule_id")["n_trades"].astype(int)
    mismatched_counts = [
        str(rule_id)
        for rule_id, expected in expected_counts.items()
        if int(actual_counts.loc[str(rule_id)]) != int(expected)
    ]
    if mismatched_counts:
        raise ValueError(f"summary n_trades mismatch for rules: {mismatched_counts}")
    for frame_name, frame in (("summary", summary), ("selection", selection), ("trades", trades)):
        rank_counts = frame.groupby("rule_id")["original_rank"].nunique()
        bad_rank_rules = rank_counts[rank_counts != 1].index.astype(str).tolist()
        if bad_rank_rules:
            raise ValueError(f"{frame_name} has non-unique original_rank for rules: {bad_rank_rules}")
    summary_rank = summary.groupby("rule_id")["original_rank"].first().astype(int)
    selection_rank = selection.groupby("rule_id")["original_rank"].first().astype(int)
    trades_rank = trades.groupby("rule_id")["original_rank"].first().astype(int)
    rank_mismatch = [
        str(rule_id)
        for rule_id in sorted(selection_rules)
        if int(summary_rank.loc[rule_id]) != int(selection_rank.loc[rule_id])
        or int(summary_rank.loc[rule_id]) != int(trades_rank.loc[rule_id])
    ]
    if rank_mismatch:
        raise ValueError(f"original_rank mismatch across artifacts for rules: {rank_mismatch}")
    too_small = summary.loc[pd.to_numeric(summary["n_trades"], errors="coerce") < 100, "rule_id"].astype(str).tolist()
    if too_small:
        raise ValueError(f"rules below sample-size gate: {too_small}")
    return Fixed11Inputs(
        audit=audit,
        summary=summary,
        selection=selection,
        trades=trades,
        paths={key: str(path) for key, path in paths.items()},
        sha256={key: sha256_file(path) for key, path in paths.items()},
    )


def _safe_corr(left: pd.Series, right: pd.Series) -> float:
    if len(left) == 0 or len(right) == 0 or len(left) != len(right):
        return 0.0
    if len(left) == 1:
        left_value = float(left.iloc[0])
        right_value = float(right.iloc[0])
        if np.isclose(left_value, 0.0) and np.isclose(right_value, 0.0):
            return 1.0
        return 1.0 if np.sign(left_value) == np.sign(right_value) else 0.0
    if np.isclose(float(left.std(ddof=0)), 0.0) or np.isclose(float(right.std(ddof=0)), 0.0):
        return 1.0 if np.allclose(left.to_numpy(dtype=float), right.to_numpy(dtype=float)) else 0.0
    value = float(left.corr(right))
    if np.isnan(value):
        return 0.0
    return max(-1.0, min(1.0, value))


def _jaccard(left: pd.Series, right: pd.Series) -> float:
    left_set = set(left.tolist())
    right_set = set(right.tolist())
    union = left_set | right_set
    return float(len(left_set & right_set) / len(union)) if union else 0.0


def _overlap_ratio(left: pd.Series, right: pd.Series) -> float:
    left_set = set(left.tolist())
    right_set = set(right.tolist())
    denominator = min(len(left_set), len(right_set))
    return float(len(left_set & right_set) / denominator) if denominator else 0.0


def _bucket_direction(direction_sum: int) -> int:
    if direction_sum > 0:
        return 1
    if direction_sum < 0:
        return -1
    return 0


def _fill_bucket_frame(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        frame.groupby("fill_time", sort=True)
        .agg(
            pnl_r=("pnl_r", "sum"),
            direction_sum=("direction", "sum"),
            trade_count=("position_id", "count"),
            unique_directions=("direction", "nunique"),
            first_signal_time=("signal_time", "min"),
            last_exit_time=("exit_time", "max"),
        )
        .reset_index()
    )
    grouped["direction"] = grouped["direction_sum"].map(_bucket_direction).astype(int)
    grouped["mixed_direction"] = grouped["unique_directions"].astype(int) > 1
    return grouped


def _align_on_fill_bucket(left: pd.DataFrame, right: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    left_bucket = _fill_bucket_frame(left)
    right_bucket = _fill_bucket_frame(right)
    shared = sorted(set(left_bucket["fill_time"]) & set(right_bucket["fill_time"]))
    if not shared:
        return left_bucket.iloc[0:0].copy(), right_bucket.iloc[0:0].copy()
    left_aligned = left_bucket[left_bucket["fill_time"].isin(shared)].sort_values("fill_time", kind="stable")
    right_aligned = right_bucket[right_bucket["fill_time"].isin(shared)].sort_values("fill_time", kind="stable")
    return left_aligned.reset_index(drop=True), right_aligned.reset_index(drop=True)


def _period_pnl(frame: pd.DataFrame, period: str, time_column: str) -> pd.Series:
    return (
        frame.assign(period=frame[time_column].dt.to_period(period).dt.to_timestamp())
        .groupby("period", sort=True)["pnl_r"]
        .sum()
        .astype(float)
    )


def _period_corr(left: pd.DataFrame, right: pd.DataFrame, period: str, time_column: str) -> float:
    left_shared_days = set(left[time_column].dt.floor("D"))
    right_shared_days = set(right[time_column].dt.floor("D"))
    if not left_shared_days & right_shared_days:
        return 0.0
    left_pnl = _period_pnl(left, period, time_column)
    right_pnl = _period_pnl(right, period, time_column)
    union = sorted(set(left_pnl.index) | set(right_pnl.index))
    if not union:
        return 0.0
    return _safe_corr(left_pnl.reindex(union, fill_value=0.0), right_pnl.reindex(union, fill_value=0.0))


def _drawdown_state(frame: pd.DataFrame) -> pd.Series:
    daily = _period_pnl(frame, "D", "exit_time")
    if daily.empty:
        return pd.Series(dtype=bool)
    equity = daily.cumsum()
    return equity < equity.cummax()


def _mask_union_ratio(left_mask: pd.Series, right_mask: pd.Series) -> float:
    union_index = sorted(set(left_mask.index) | set(right_mask.index))
    if not union_index:
        return 0.0
    left = left_mask.reindex(union_index, fill_value=False).astype(bool)
    right = right_mask.reindex(union_index, fill_value=False).astype(bool)
    union = left | right
    return float((left & right).sum() / union.sum()) if int(union.sum()) else 0.0


def _co_loss_ratio(left: pd.DataFrame, right: pd.DataFrame) -> float:
    left_daily = _period_pnl(left, "D", "exit_time")
    right_daily = _period_pnl(right, "D", "exit_time")
    union_index = sorted(set(left_daily.index) | set(right_daily.index))
    if not union_index:
        return 0.0
    left_loss = left_daily.reindex(union_index, fill_value=0.0) < 0.0
    right_loss = right_daily.reindex(union_index, fill_value=0.0) < 0.0
    union = left_loss | right_loss
    return float((left_loss & right_loss).sum() / union.sum()) if int(union.sum()) else 0.0


def _staggered_gain_ratio(left: pd.DataFrame, right: pd.DataFrame) -> float:
    left_daily = _period_pnl(left, "D", "exit_time")
    right_daily = _period_pnl(right, "D", "exit_time")
    union_index = sorted(set(left_daily.index) | set(right_daily.index))
    if not union_index:
        return 0.0
    left_gain = left_daily.reindex(union_index, fill_value=0.0) > 0.0
    right_gain = right_daily.reindex(union_index, fill_value=0.0) > 0.0
    gain_union = left_gain | right_gain
    staggered = (left_gain & ~right_gain) | (right_gain & ~left_gain)
    return float(staggered.sum() / gain_union.sum()) if int(gain_union.sum()) else 0.0


def classify_redundancy(metrics: dict[str, float]) -> str:
    if (
        metrics["fill_overlap_ratio"] >= 0.75
        and metrics["same_direction_ratio"] >= 0.90
        and metrics["fill_bucket_pnl_corr"] >= 0.85
        and metrics["fill_daily_pnl_corr"] >= 0.75
        and metrics["fill_weekly_pnl_corr"] >= 0.75
        and metrics["exit_daily_pnl_corr"] >= 0.75
        and metrics["exit_weekly_pnl_corr"] >= 0.75
    ):
        return "strong_duplicate"
    if (
        metrics["fill_overlap_ratio"] >= 0.35
        or metrics["fill_jaccard"] >= 0.20
        or metrics["fill_daily_pnl_corr"] >= 0.35
        or metrics["fill_weekly_pnl_corr"] >= 0.45
        or metrics["exit_daily_pnl_corr"] >= 0.35
        or metrics["exit_weekly_pnl_corr"] >= 0.45
        or metrics["exit_drawdown_overlap_ratio"] >= 0.35
        or metrics["same_direction_ratio"] >= 0.60
    ):
        return "partial_overlap"
    return "unclear_or_complementary"


def compute_pair_metrics(left: pd.DataFrame, right: pd.DataFrame) -> dict[str, float | str]:
    left_aligned, right_aligned = _align_on_fill_bucket(left, right)
    shared_fill_bucket_count = int(len(left_aligned))
    mixed_direction_bucket_count = int(left_aligned.get("mixed_direction", pd.Series(dtype=bool)).sum()) + int(
        right_aligned.get("mixed_direction", pd.Series(dtype=bool)).sum()
    )
    metrics: dict[str, float] = {
        "fill_overlap_ratio": _overlap_ratio(left["fill_time"], right["fill_time"]),
        "signal_overlap_ratio": _overlap_ratio(left["signal_time"], right["signal_time"]),
        "fill_jaccard": _jaccard(left["fill_time"], right["fill_time"]),
        "signal_jaccard": _jaccard(left["signal_time"], right["signal_time"]),
        "same_direction_ratio": float((left_aligned["direction"].to_numpy() == right_aligned["direction"].to_numpy()).mean())
        if not left_aligned.empty
        else 0.0,
        "fill_bucket_pnl_corr": _safe_corr(left_aligned["pnl_r"], right_aligned["pnl_r"]) if not left_aligned.empty else 0.0,
        "shared_fill_bucket_count": float(shared_fill_bucket_count),
        "left_trade_count_at_shared_fills": float(left_aligned["trade_count"].sum()) if not left_aligned.empty else 0.0,
        "right_trade_count_at_shared_fills": float(right_aligned["trade_count"].sum()) if not right_aligned.empty else 0.0,
        "mixed_direction_bucket_count": float(mixed_direction_bucket_count),
        "fill_daily_pnl_corr": _period_corr(left, right, "D", "fill_time"),
        "fill_weekly_pnl_corr": _period_corr(left, right, "W", "fill_time"),
        "exit_daily_pnl_corr": _period_corr(left, right, "D", "exit_time"),
        "exit_weekly_pnl_corr": _period_corr(left, right, "W", "exit_time"),
        "exit_drawdown_overlap_ratio": _mask_union_ratio(_drawdown_state(left), _drawdown_state(right)),
        "exit_co_loss_ratio": _co_loss_ratio(left, right),
        "exit_staggered_gain_ratio": _staggered_gain_ratio(left, right),
        "benchmark_system_correlation_parity": "MATCHED_ON_SYNTHETIC_SINGLE_TRADE_BUCKET_CASE",
    }
    return {**metrics, "redundancy_verdict": classify_redundancy(metrics)}


def build_pairwise_matrix(trades: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    rule_ids = sorted(trades["rule_id"].astype(str).unique())
    grouped = {rule_id: frame.copy() for rule_id, frame in trades.groupby("rule_id", sort=False)}
    for left_index, left_rule_id in enumerate(rule_ids):
        for right_rule_id in rule_ids[left_index + 1 :]:
            rows.append(
                {
                    "left_rule_id": left_rule_id,
                    "right_rule_id": right_rule_id,
                    **compute_pair_metrics(grouped[left_rule_id], grouped[right_rule_id]),
                }
            )
    pairwise = pd.DataFrame(rows)
    if len(pairwise) != len(rule_ids) * (len(rule_ids) - 1) // 2:
        raise ValueError("pairwise matrix has unexpected row count")
    return pairwise


def _rule_metadata(inputs: Fixed11Inputs) -> pd.DataFrame:
    columns = ["rule_id", "original_rank", "profile_id", "model_id", "target_id", "filter_id"]
    metadata = inputs.trades[columns].drop_duplicates("rule_id").copy()
    metadata["original_rank"] = pd.to_numeric(metadata["original_rank"], errors="raise").astype(int)
    return metadata.sort_values(["original_rank", "rule_id"], kind="stable").reset_index(drop=True)


def build_duplicate_clusters(pairwise: pd.DataFrame, rule_order: pd.DataFrame) -> pd.DataFrame:
    rule_ids = rule_order.sort_values(["original_rank", "rule_id"], kind="stable")["rule_id"].astype(str).tolist()
    strong_edges = {
        frozenset((str(row.left_rule_id), str(row.right_rule_id)))
        for row in pairwise.itertuples(index=False)
        if row.redundancy_verdict == "strong_duplicate"
    }
    retained: list[str] = []
    representative_by_rule: dict[str, str] = {}
    for rule_id in rule_ids:
        direct_representative = next(
            (candidate for candidate in retained if frozenset((candidate, rule_id)) in strong_edges),
            None,
        )
        if direct_representative is None:
            retained.append(rule_id)
            representative_by_rule[rule_id] = rule_id
        else:
            representative_by_rule[rule_id] = direct_representative
    clusters = rule_order.copy()
    clusters["rule_id"] = clusters["rule_id"].astype(str)
    clusters["representative_rule_id"] = clusters["rule_id"].map(representative_by_rule)
    cluster_ids = {rule_id: index + 1 for index, rule_id in enumerate(retained)}
    clusters["duplicate_cluster_id"] = clusters["representative_rule_id"].map(cluster_ids).astype(int)
    clusters["cluster_size"] = clusters.groupby("duplicate_cluster_id")["rule_id"].transform("count").astype(int)
    return clusters.sort_values(["duplicate_cluster_id", "original_rank", "rule_id"], kind="stable").reset_index(drop=True)


def build_retained_subset(inputs: Fixed11Inputs, pairwise: pd.DataFrame) -> dict[str, Any]:
    metadata = _rule_metadata(inputs)
    clusters = build_duplicate_clusters(pairwise, metadata)
    strong_lookup = {
        frozenset((str(row.left_rule_id), str(row.right_rule_id))): row._asdict()
        for row in pairwise.itertuples(index=False)
        if row.redundancy_verdict == "strong_duplicate"
    }
    partial_overlap_warnings = [
        row._asdict()
        for row in pairwise.itertuples(index=False)
        if row.redundancy_verdict == "partial_overlap"
    ]
    rules: list[dict[str, Any]] = []
    for row in clusters.itertuples(index=False):
        representative = str(row.representative_rule_id)
        decision = "RETAIN" if str(row.rule_id) == representative else "DROP_STRONG_DUPLICATE"
        reason = "cluster_representative_lowest_original_rank" if decision == "RETAIN" else f"strong_duplicate_of={representative}"
        direct_evidence = strong_lookup.get(frozenset((str(row.rule_id), representative)))
        rules.append(
            {
                "rule_id": str(row.rule_id),
                "original_rank": int(row.original_rank),
                "profile_id": str(row.profile_id),
                "model_id": str(row.model_id),
                "target_id": str(row.target_id),
                "filter_id": str(row.filter_id),
                "duplicate_cluster_id": int(row.duplicate_cluster_id),
                "cluster_size": int(row.cluster_size),
                "representative_rule_id": representative,
                "decision": decision,
                "reason": reason,
                "direct_strong_duplicate_evidence": direct_evidence,
                "warnings": [
                    warning
                    for warning in partial_overlap_warnings
                    if str(row.rule_id) in {str(warning["left_rule_id"]), str(warning["right_rule_id"])}
                ],
            }
        )
    retained_count = sum(1 for item in rules if item["decision"] == "RETAIN")
    removed_count = sum(1 for item in rules if item["decision"] == "DROP_STRONG_DUPLICATE")
    all_rules_direct_duplicate_of_one_representative = retained_count == 1 and removed_count == len(rules) - 1
    non_representative_strong_duplicate_pairs = [
        row._asdict()
        for row in pairwise.itertuples(index=False)
        if row.redundancy_verdict == "strong_duplicate"
        and not any(
            item["decision"] == "DROP_STRONG_DUPLICATE"
            and frozenset((item["rule_id"], item["representative_rule_id"]))
            == frozenset((str(row.left_rule_id), str(row.right_rule_id)))
            for item in rules
        )
    ]
    return {
        "overall_decision": "all_rules_duplicate_research_only"
        if all_rules_direct_duplicate_of_one_representative
        else "pruning_passed",
        "input_rule_count": int(len(rules)),
        "retained_count": int(retained_count),
        "removed_count": int(removed_count),
        "representative_policy": "lowest_original_rank_then_rule_id",
        "locked_test_performance_used_for_representative_choice": False,
        "redundancy_thresholds": {
            "strong_duplicate": {
                "fill_overlap_ratio_min": 0.75,
                "same_direction_ratio_min": 0.90,
                "fill_bucket_pnl_corr_min": 0.85,
                "fill_daily_pnl_corr_min": 0.75,
                "fill_weekly_pnl_corr_min": 0.75,
                "exit_daily_pnl_corr_min": 0.75,
                "exit_weekly_pnl_corr_min": 0.75,
            }
        },
        "rules": rules,
        "strong_duplicate_edges": list(strong_lookup.values()),
        "partial_overlap_warnings": partial_overlap_warnings,
        "non_representative_strong_duplicate_pairs": non_representative_strong_duplicate_pairs,
        "indirect_duplicate_edges_not_used_for_drop": non_representative_strong_duplicate_pairs,
    }


def _metric_matrix(pairwise: pd.DataFrame, rule_ids: list[str], field: str) -> pd.DataFrame:
    matrix = pd.DataFrame(index=rule_ids, columns=rule_ids, dtype=float)
    for rule_id in rule_ids:
        matrix.loc[rule_id, rule_id] = 1.0
    for row in pairwise.itertuples(index=False):
        value = float(getattr(row, field))
        matrix.loc[str(row.left_rule_id), str(row.right_rule_id)] = value
        matrix.loc[str(row.right_rule_id), str(row.left_rule_id)] = value
    return matrix.fillna(0.0)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def run_pruning(input_prefix: Path, audit_json: Path, output_prefix: Path) -> dict[str, Any]:
    inputs = load_inputs(input_prefix, audit_json)
    pairwise = build_pairwise_matrix(inputs.trades)
    retained = build_retained_subset(inputs, pairwise)
    metadata = _rule_metadata(inputs)
    clusters = build_duplicate_clusters(pairwise, metadata)
    rule_ids = metadata.sort_values(["original_rank", "rule_id"], kind="stable")["rule_id"].astype(str).tolist()

    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    paths = {
        "pairwise_csv": output_prefix.with_name(output_prefix.name + "_pairwise.csv"),
        "clusters_csv": output_prefix.with_name(output_prefix.name + "_clusters.csv"),
        "fill_daily_pnl_matrix_csv": output_prefix.with_name(output_prefix.name + "_fill_daily_pnl_matrix.csv"),
        "fill_weekly_pnl_matrix_csv": output_prefix.with_name(output_prefix.name + "_fill_weekly_pnl_matrix.csv"),
        "exit_daily_pnl_matrix_csv": output_prefix.with_name(output_prefix.name + "_exit_daily_pnl_matrix.csv"),
        "exit_weekly_pnl_matrix_csv": output_prefix.with_name(output_prefix.name + "_exit_weekly_pnl_matrix.csv"),
        "exit_drawdown_overlap_matrix_csv": output_prefix.with_name(output_prefix.name + "_exit_drawdown_overlap_matrix.csv"),
        "retained_subset_json": output_prefix.with_name(output_prefix.name + "_retained_subset.json"),
        "summary_json": output_prefix.with_name(output_prefix.name + "_summary.json"),
    }
    pairwise.to_csv(paths["pairwise_csv"], sep=";", index=False)
    clusters.to_csv(paths["clusters_csv"], sep=";", index=False)
    _metric_matrix(pairwise, rule_ids, "fill_daily_pnl_corr").to_csv(paths["fill_daily_pnl_matrix_csv"], sep=";", index_label="rule_id")
    _metric_matrix(pairwise, rule_ids, "fill_weekly_pnl_corr").to_csv(paths["fill_weekly_pnl_matrix_csv"], sep=";", index_label="rule_id")
    _metric_matrix(pairwise, rule_ids, "exit_daily_pnl_corr").to_csv(paths["exit_daily_pnl_matrix_csv"], sep=";", index_label="rule_id")
    _metric_matrix(pairwise, rule_ids, "exit_weekly_pnl_corr").to_csv(paths["exit_weekly_pnl_matrix_csv"], sep=";", index_label="rule_id")
    _metric_matrix(pairwise, rule_ids, "exit_drawdown_overlap_ratio").to_csv(
        paths["exit_drawdown_overlap_matrix_csv"], sep=";", index_label="rule_id"
    )
    _write_json(paths["retained_subset_json"], retained)
    verdict_counts = pairwise["redundancy_verdict"].value_counts().to_dict()
    summary = {
        **STAGE_METADATA,
        "overall_decision": retained["overall_decision"],
        "input_rule_count": retained["input_rule_count"],
        "retained_count": retained["retained_count"],
        "removed_count": retained["removed_count"],
        "pair_count": int(len(pairwise)),
        "strong_duplicate_edge_count": int(verdict_counts.get("strong_duplicate", 0)),
        "partial_overlap_count": int(verdict_counts.get("partial_overlap", 0)),
        "unclear_or_complementary_count": int(verdict_counts.get("unclear_or_complementary", 0)),
        "non_representative_strong_duplicate_pair_count": int(len(retained["non_representative_strong_duplicate_pairs"])),
        "locked_test_policy": "overlap_measurement_only_no_winner_selection",
        "locked_test_performance_used_for_representative_choice": False,
        "inputs": inputs.paths,
        "input_sha256": inputs.sha256,
        "artifacts": {key: str(path) for key, path in paths.items()},
    }
    _write_json(paths["summary_json"], summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prune fixed-11 rules by mutual overlap and PnL correlation.")
    parser.add_argument("--input-prefix", default="ML/reports/fractal0_fixed11_rich_entry_locked_test")
    parser.add_argument("--audit-json", default="ML/reports/fractal0_fixed11_candidate_audit.json")
    parser.add_argument("--output-prefix", default="ML/reports/fractal0_fixed11_mutual_correlation_pruning")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_pruning(Path(args.input_prefix), Path(args.audit_json), Path(args.output_prefix))
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
