from __future__ import annotations

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
