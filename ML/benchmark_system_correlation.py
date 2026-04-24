# =============================================================================
# Файл: benchmark_system_correlation.py
# Назначение: Канонический pairwise benchmark совместимости торговых систем по сделкам и PnL-рядам.
# Обновлён: 2026-04-24
# Входные данные:
#   - manifest JSON с источниками trade CSV или entry_path prediction CSV (откуда: ML/reports/*)
# Выходные данные:
#   - pairwise_matrix.csv, system_summary.csv, daily_pnl_matrix.csv, weekly_pnl_matrix.csv,
#     drawdown_overlap.csv, run_metadata.json, summary.json (куда: output_dir)
# Использование:
#   python -m ML.benchmark_system_correlation --manifest ... --output-dir ...
# Примечания:
#   - XAUUSD baseline должен запускаться отдельным manifest без смешивания инструментов.
# =============================================================================

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from API import export_entry_path_v1_quantile_signals as export_entry_path_v1_quantile
from API import export_entry_path_v1_signals as export_entry_path_v1
from ML.benchmark_execution_policy_v2 import DEFAULT_POLICIES
from ML.benchmark_execution_policy_v2 import ExitPolicy
from ML.benchmark_execution_policy_v2 import load_ohlc
from ML.benchmark_execution_policy_v2 import simulate_policy


NORMALIZED_TRADE_COLUMNS = [
    "system_name",
    "instrument",
    "provider",
    "entry_time",
    "exit_time",
    "direction",
    "pnl_atr",
    "holding_bars",
]

SUPPORTED_SOURCE_TYPES = {"trade_csv", "entry_path_predictions"}
SUPPORTED_ENTRY_PATH_KINDS = {"entry_path_v1", "entry_path_v1_quantile"}


@dataclass(frozen=True)
class SystemSpec:
    system_name: str
    instrument: str
    provider: str
    source_type: str
    payload: dict[str, Any]


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _as_timestamp(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="raise")


def _safe_corr(left: pd.Series, right: pd.Series) -> float:
    if len(left) == 0 or len(right) == 0 or len(left) != len(right):
        return 0.0
    if len(left) == 1:
        if np.isclose(float(left.iloc[0]), float(right.iloc[0])):
            return 1.0
        return 0.0
    if np.isclose(float(left.std(ddof=0)), 0.0) or np.isclose(float(right.std(ddof=0)), 0.0):
        if np.allclose(left.to_numpy(dtype=float), right.to_numpy(dtype=float)):
            return 1.0
        return 0.0
    value = float(left.corr(right))
    if np.isnan(value):
        return 0.0
    return max(-1.0, min(1.0, value))


def _jaccard_ratio(left: pd.Series, right: pd.Series) -> float:
    left_set = set(left.tolist())
    right_set = set(right.tolist())
    union = left_set | right_set
    if not union:
        return 0.0
    return float(len(left_set & right_set) / len(union))


def _align_trade_overlap(left: pd.DataFrame, right: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    shared = sorted(set(left["entry_time"]) & set(right["entry_time"]))
    if not shared:
        empty = left.iloc[0:0].copy()
        return empty, empty
    left_aligned = (
        left[left["entry_time"].isin(shared)]
        .sort_values("entry_time", kind="stable")
        .drop_duplicates("entry_time", keep="last")
        .reset_index(drop=True)
    )
    right_aligned = (
        right[right["entry_time"].isin(shared)]
        .sort_values("entry_time", kind="stable")
        .drop_duplicates("entry_time", keep="last")
        .reset_index(drop=True)
    )
    return left_aligned, right_aligned


def _aggregate_period_pnl(frame: pd.DataFrame, period: str) -> pd.Series:
    if frame.empty:
        return pd.Series(dtype=float)
    grouped = (
        frame.assign(period=frame["exit_time"].dt.to_period(period).dt.to_timestamp())
        .groupby("period", sort=True)["pnl_atr"]
        .sum()
    )
    return grouped.astype(float)


def _daily_state(frame: pd.DataFrame) -> pd.DataFrame:
    daily = _aggregate_period_pnl(frame, "D")
    if daily.empty:
        return pd.DataFrame(columns=["pnl", "equity", "in_drawdown"])
    state = daily.to_frame(name="pnl")
    state["equity"] = state["pnl"].cumsum()
    state["peak"] = state["equity"].cummax()
    state["in_drawdown"] = state["equity"] < state["peak"]
    return state


def _ratio_with_union(mask_left: pd.Series, mask_right: pd.Series) -> float:
    union = mask_left | mask_right
    if int(union.sum()) == 0:
        return 0.0
    return float((mask_left & mask_right).sum() / union.sum())


def _direction_int(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).astype(int)


def validate_trade_frame(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in NORMALIZED_TRADE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"missing required trade columns: {missing}")
    if frame.empty:
        raise ValueError("trade frame is empty after normalization")
    if frame["entry_time"].isna().any() or frame["exit_time"].isna().any():
        raise ValueError("trade frame contains invalid timestamps")
    return frame


def normalize_trade_frame(
    frame: pd.DataFrame,
    *,
    system_name: str,
    instrument: str,
    provider: str,
) -> pd.DataFrame:
    normalized = pd.DataFrame(
        {
            "system_name": system_name,
            "instrument": instrument,
            "provider": provider,
            "entry_time": _as_timestamp(frame["entry_time"]),
            "exit_time": _as_timestamp(frame["exit_time"]),
            "direction": _direction_int(frame["direction"]),
            "pnl_atr": pd.to_numeric(frame["pnl_atr"], errors="raise").astype(float),
            "holding_bars": pd.to_numeric(frame["holding_bars"], errors="raise").astype(int),
        }
    )
    normalized = normalized.sort_values("entry_time", kind="stable").reset_index(drop=True)
    return validate_trade_frame(normalized)


def _resolve_policy(spec: dict[str, Any]) -> ExitPolicy:
    policy_name = str(spec.get("policy_name", "")).strip()
    registry = {policy.name: policy for policy in DEFAULT_POLICIES}
    if policy_name in registry:
        return registry[policy_name]
    hold_bars = spec.get("hold_bars")
    if hold_bars is not None:
        return ExitPolicy(
            name=policy_name or f"hold_{int(hold_bars)}_backstop_50",
            stop_atr=float(spec.get("stop_atr", 50.0)),
            trail_atr=None,
            hold_bars=int(hold_bars),
        )
    raise ValueError(f"unknown policy_name: {policy_name}")


def _deduplicate_runtime_rows(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame[["time", "signal"]].copy()
    output["_abs"] = output["signal"].abs()
    output = (
        output.sort_values(["time", "_abs"], ascending=[True, False], kind="stable")
        .drop_duplicates(subset=["time"], keep="first")
        .drop(columns="_abs")
        .sort_values("time", kind="stable")
        .reset_index(drop=True)
    )
    return output


def _build_entry_path_signals(spec: dict[str, Any]) -> pd.DataFrame:
    kind = str(spec.get("entry_path_kind", "")).strip()
    if kind not in SUPPORTED_ENTRY_PATH_KINDS:
        raise ValueError(f"unsupported entry_path_kind: {kind}")

    prediction_csv = Path(str(spec.get("prediction_csv", "")).strip())
    if not prediction_csv.exists():
        raise ValueError(f"missing prediction_csv: {prediction_csv}")
    rule_path = Path(str(spec.get("rule_path", "")).strip())
    if not rule_path.exists():
        raise ValueError(f"missing rule_path: {rule_path}")

    if kind == "entry_path_v1":
        frame = export_entry_path_v1.load_prediction_frame(prediction_csv)
        rule_payload = export_entry_path_v1.load_rule_payload_from_file(rule_path)
        selected_mask = export_entry_path_v1.apply_rule(frame, rule_payload)
        selected = frame[["time", "signal"]].copy()
        selected.loc[~selected_mask, "signal"] = 0
        return _deduplicate_runtime_rows(selected)

    raw_frame = pd.read_csv(prediction_csv, sep=";")
    rule_payload = export_entry_path_v1_quantile.load_rule_payload_from_file(rule_path)
    baseline_predictions_path = spec.get("baseline_predictions_path")
    if baseline_predictions_path is None:
        baseline_predictions_path = export_entry_path_v1_quantile._resolve_baseline_predictions_path(
            rule_path,
            str(spec.get("split", "test")),
        )
    baseline_frame = pd.read_csv(Path(baseline_predictions_path), sep=";")
    selected_mask = export_entry_path_v1_quantile.apply_production_rule(
        raw_frame,
        baseline_frame,
        rule_payload,
    )
    selected = raw_frame[["time", "signal"]].copy()
    selected.loc[~selected_mask, "signal"] = 0
    return _deduplicate_runtime_rows(selected)


def _simulate_entry_path_trades(spec: dict[str, Any]) -> pd.DataFrame:
    signals = _build_entry_path_signals(spec)
    signals["time"] = pd.to_datetime(signals["time"], format="%Y.%m.%d %H:%M")
    signals["signal"] = _direction_int(signals["signal"])
    signals = signals[signals["signal"] != 0].copy()

    ohlc_path = Path(str(spec.get("ohlc_csv", "")).strip())
    if not ohlc_path.exists():
        raise ValueError(f"missing ohlc_csv: {ohlc_path}")
    bars, index_by_time = load_ohlc(ohlc_path)
    trades = simulate_policy(signals, bars, index_by_time, _resolve_policy(spec))
    if trades.empty:
        raise ValueError("entry_path simulation produced no trades")
    simulated = trades.rename(columns={"signal": "direction"}).copy()
    simulated["holding_bars"] = simulated["hold_hours"].round().astype(int)
    return simulated


def load_trade_frame(spec: SystemSpec | dict[str, Any]) -> pd.DataFrame:
    if isinstance(spec, SystemSpec):
        raw_spec = {
            "system_name": spec.system_name,
            "instrument": spec.instrument,
            "provider": spec.provider,
            "source_type": spec.source_type,
            **spec.payload,
        }
    else:
        raw_spec = dict(spec)

    source_type = str(raw_spec.get("source_type", "")).strip()
    system_name = str(raw_spec.get("system_name", "")).strip()
    instrument = str(raw_spec.get("instrument", "")).strip()
    provider = str(raw_spec.get("provider", "")).strip()

    if source_type == "trade_csv":
        trade_csv = Path(str(raw_spec.get("trade_csv", "")).strip())
        frame = pd.read_csv(trade_csv)
        if "system_name" in frame.columns:
            frame = frame[frame["system_name"].astype(str) == system_name]
        dataset_name = str(raw_spec.get("dataset_name", "")).strip()
        if dataset_name and "dataset_name" in frame.columns:
            frame = frame[frame["dataset_name"].astype(str) == dataset_name]
        policy_name = str(raw_spec.get("policy_name", "")).strip()
        if policy_name and "policy" in frame.columns:
            frame = frame[frame["policy"].astype(str) == policy_name]
        if frame.empty:
            raise ValueError(f"trade_csv resolved to empty frame for system {system_name}")
        frame = frame.rename(columns={"signal": "direction"})
        if "holding_bars" not in frame.columns:
            if "hold_hours" not in frame.columns:
                raise ValueError("trade_csv missing hold_hours/holding_bars")
            frame["holding_bars"] = pd.to_numeric(frame["hold_hours"], errors="raise").round().astype(int)
        return normalize_trade_frame(
            frame,
            system_name=system_name,
            instrument=instrument,
            provider=provider,
        )

    if source_type == "entry_path_predictions":
        simulated = _simulate_entry_path_trades(raw_spec)
        return normalize_trade_frame(
            simulated,
            system_name=system_name,
            instrument=instrument,
            provider=provider,
        )

    raise ValueError(f"unsupported source_type: {source_type}")


def load_manifest(path: str | Path) -> tuple[SystemSpec, ...]:
    payload = _load_json(path)
    systems_raw = payload.get("systems")
    if not isinstance(systems_raw, list) or not systems_raw:
        raise ValueError("manifest must contain non-empty systems list")

    specs: list[SystemSpec] = []
    system_names: set[str] = set()
    instruments: set[str] = set()
    for item in systems_raw:
        system_name = str(item.get("system_name", "")).strip()
        instrument = str(item.get("instrument", "")).strip()
        provider = str(item.get("provider", "")).strip()
        source_type = str(item.get("source_type", "")).strip()

        if not system_name:
            raise ValueError("system_name is required")
        if system_name in system_names:
            raise ValueError(f"duplicate system_name in manifest: {system_name}")
        if not instrument:
            raise ValueError(f"instrument is required for system {system_name}")
        if not provider:
            raise ValueError(f"provider is required for system {system_name}")
        if source_type not in SUPPORTED_SOURCE_TYPES:
            raise ValueError(f"unsupported source_type: {source_type}")

        system_names.add(system_name)
        instruments.add(instrument)

        if source_type == "trade_csv":
            trade_csv = Path(str(item.get("trade_csv", "")).strip())
            if not trade_csv.exists():
                raise ValueError(f"missing trade_csv: {trade_csv}")
        if source_type == "entry_path_predictions":
            for required_path in ("prediction_csv", "rule_path", "ohlc_csv"):
                candidate = Path(str(item.get(required_path, "")).strip())
                if not candidate.exists():
                    raise ValueError(f"missing {required_path}: {candidate}")
            kind = str(item.get("entry_path_kind", "")).strip()
            if kind not in SUPPORTED_ENTRY_PATH_KINDS:
                raise ValueError(f"unsupported entry_path_kind: {kind}")

        payload_copy = dict(item)
        payload_copy.pop("system_name", None)
        payload_copy.pop("instrument", None)
        payload_copy.pop("provider", None)
        payload_copy.pop("source_type", None)
        specs.append(
            SystemSpec(
                system_name=system_name,
                instrument=instrument,
                provider=provider,
                source_type=source_type,
                payload=payload_copy,
            )
        )

    if len(instruments) != 1:
        raise ValueError("manifest must describe a single instrument per run")
    return tuple(specs)


def compute_trade_overlap(left: pd.DataFrame, right: pd.DataFrame) -> tuple[float, float]:
    left_times = pd.Series(sorted(set(left["entry_time"])))
    right_times = pd.Series(sorted(set(right["entry_time"])))
    intersection = len(set(left_times) & set(right_times))
    minimum = min(len(left_times), len(right_times))
    overlap_ratio = float(intersection / minimum) if minimum else 0.0
    return overlap_ratio, _jaccard_ratio(left_times, right_times)


def compute_direction_agreement(left: pd.DataFrame, right: pd.DataFrame) -> float:
    left_aligned, right_aligned = _align_trade_overlap(left, right)
    if left_aligned.empty:
        return 0.0
    return float((left_aligned["direction"].to_numpy() == right_aligned["direction"].to_numpy()).mean())


def compute_trade_pnl_corr(left: pd.DataFrame, right: pd.DataFrame) -> float:
    left_aligned, right_aligned = _align_trade_overlap(left, right)
    if left_aligned.empty:
        return 0.0
    return _safe_corr(left_aligned["pnl_atr"], right_aligned["pnl_atr"])


def compute_period_pnl_corr(left: pd.DataFrame, right: pd.DataFrame, period: str) -> float:
    left_period = _aggregate_period_pnl(left, period)
    right_period = _aggregate_period_pnl(right, period)
    union = sorted(set(left_period.index) | set(right_period.index))
    if not union:
        return 0.0
    left_aligned = left_period.reindex(union, fill_value=0.0)
    right_aligned = right_period.reindex(union, fill_value=0.0)
    return _safe_corr(left_aligned, right_aligned)


def compute_drawdown_overlap(left: pd.DataFrame, right: pd.DataFrame) -> float:
    left_state = _daily_state(left)
    right_state = _daily_state(right)
    union = sorted(set(left_state.index) | set(right_state.index))
    if not union:
        return 0.0
    left_mask = left_state.reindex(union, fill_value=False)["in_drawdown"].astype(bool)
    right_mask = right_state.reindex(union, fill_value=False)["in_drawdown"].astype(bool)
    return _ratio_with_union(left_mask, right_mask)


def compute_co_loss_ratio(left: pd.DataFrame, right: pd.DataFrame) -> float:
    left_daily = _aggregate_period_pnl(left, "D")
    right_daily = _aggregate_period_pnl(right, "D")
    union = sorted(set(left_daily.index) | set(right_daily.index))
    if not union:
        return 0.0
    left_mask = left_daily.reindex(union, fill_value=0.0) < 0.0
    right_mask = right_daily.reindex(union, fill_value=0.0) < 0.0
    return _ratio_with_union(left_mask, right_mask)


def compute_staggered_gain_ratio(left: pd.DataFrame, right: pd.DataFrame) -> float:
    left_daily = _aggregate_period_pnl(left, "D")
    right_daily = _aggregate_period_pnl(right, "D")
    union = sorted(set(left_daily.index) | set(right_daily.index))
    if not union:
        return 0.0
    left_aligned = left_daily.reindex(union, fill_value=0.0)
    right_aligned = right_daily.reindex(union, fill_value=0.0)
    positive_union = (left_aligned > 0.0) | (right_aligned > 0.0)
    if int(positive_union.sum()) == 0:
        return 0.0
    staggered = ((left_aligned > 0.0) & (right_aligned <= 0.0)) | ((right_aligned > 0.0) & (left_aligned <= 0.0))
    return float(staggered.sum() / positive_union.sum())


def classify_pair_verdict(metrics: dict[str, float]) -> str:
    if (
        metrics["trade_overlap_ratio"] >= 0.75
        and metrics["same_direction_ratio"] >= 0.90
        and metrics["trade_pnl_corr"] >= 0.85
        and metrics["daily_pnl_corr"] >= 0.75
        and metrics["weekly_pnl_corr"] >= 0.75
    ):
        return "portfolio_redundant"

    if (
        metrics["trade_overlap_ratio"] <= 0.70
        and metrics["daily_pnl_corr"] <= 0.0
        and metrics["weekly_pnl_corr"] <= 0.0
        and metrics["drawdown_overlap_ratio"] <= 0.10
        and metrics["co_loss_ratio"] <= 0.15
        and metrics["staggered_gain_ratio"] >= 0.75
    ):
        return "portfolio_complementary"

    if (
        metrics["trade_overlap_ratio"] >= 0.35
        or metrics["entry_time_jaccard"] >= 0.20
        or metrics["daily_pnl_corr"] >= 0.35
        or metrics["weekly_pnl_corr"] >= 0.45
        or metrics["drawdown_overlap_ratio"] >= 0.35
        or metrics["same_direction_ratio"] >= 0.60
    ):
        return "portfolio_partially_overlapping"

    return "portfolio_unclear"


def compute_pair_metrics(left: pd.DataFrame, right: pd.DataFrame) -> dict[str, float | str]:
    trade_overlap_ratio, entry_time_jaccard = compute_trade_overlap(left, right)
    metrics = {
        "trade_overlap_ratio": trade_overlap_ratio,
        "same_direction_ratio": compute_direction_agreement(left, right),
        "entry_time_jaccard": entry_time_jaccard,
        "trade_pnl_corr": compute_trade_pnl_corr(left, right),
        "daily_pnl_corr": compute_period_pnl_corr(left, right, "D"),
        "weekly_pnl_corr": compute_period_pnl_corr(left, right, "W"),
        "drawdown_overlap_ratio": compute_drawdown_overlap(left, right),
        "co_loss_ratio": compute_co_loss_ratio(left, right),
        "staggered_gain_ratio": compute_staggered_gain_ratio(left, right),
    }
    metrics["portfolio_verdict"] = classify_pair_verdict(metrics)
    return metrics


def _summarize_system(frame: pd.DataFrame) -> dict[str, Any]:
    pnl = frame["pnl_atr"]
    return {
        "system_name": str(frame["system_name"].iloc[0]),
        "instrument": str(frame["instrument"].iloc[0]),
        "provider": str(frame["provider"].iloc[0]),
        "trades": int(len(frame)),
        "entry_start": frame["entry_time"].min().isoformat(),
        "entry_end": frame["entry_time"].max().isoformat(),
        "net_atr": float(pnl.sum()),
        "mean_pnl_atr": float(pnl.mean()),
        "win_rate": float((pnl > 0.0).mean()),
    }


def _build_metric_matrix(pairwise_rows: list[dict[str, Any]], systems: list[str], field: str) -> pd.DataFrame:
    matrix = pd.DataFrame(index=systems, columns=systems, dtype=float)
    for system_name in systems:
        matrix.loc[system_name, system_name] = 1.0
    for row in pairwise_rows:
        left = row["left_system"]
        right = row["right_system"]
        value = float(row[field])
        matrix.loc[left, right] = value
        matrix.loc[right, left] = value
    return matrix.fillna(0.0)


def run_benchmark(manifest_path: str | Path, output_dir: str | Path, dry_run: bool = False) -> dict[str, Any]:
    systems = list(load_manifest(manifest_path))
    resolved = [
        {
            "system_name": spec.system_name,
            "instrument": spec.instrument,
            "provider": spec.provider,
            "source_type": spec.source_type,
            **spec.payload,
        }
        for spec in systems
    ]
    if dry_run:
        return {
            "manifest_path": str(manifest_path),
            "systems": resolved,
            "instrument": systems[0].instrument,
        }

    frames = {spec.system_name: load_trade_frame(spec) for spec in systems}
    pairwise_rows: list[dict[str, Any]] = []
    system_summaries = [_summarize_system(frames[spec.system_name]) for spec in systems]

    for idx, left_spec in enumerate(systems):
        for right_spec in systems[idx + 1 :]:
            metrics = compute_pair_metrics(frames[left_spec.system_name], frames[right_spec.system_name])
            pairwise_rows.append(
                {
                    "left_system": left_spec.system_name,
                    "right_system": right_spec.system_name,
                    **metrics,
                }
            )

    system_names = [spec.system_name for spec in systems]
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pairwise_frame = pd.DataFrame(pairwise_rows)
    pairwise_frame.to_csv(output_path / "pairwise_matrix.csv", index=False)

    system_summary_frame = pd.DataFrame(system_summaries)
    system_summary_frame.to_csv(output_path / "system_summary.csv", index=False)

    daily_matrix = _build_metric_matrix(pairwise_rows, system_names, "daily_pnl_corr")
    daily_matrix.to_csv(output_path / "daily_pnl_matrix.csv", index_label="system_name")

    weekly_matrix = _build_metric_matrix(pairwise_rows, system_names, "weekly_pnl_corr")
    weekly_matrix.to_csv(output_path / "weekly_pnl_matrix.csv", index_label="system_name")

    drawdown_matrix = _build_metric_matrix(pairwise_rows, system_names, "drawdown_overlap_ratio")
    drawdown_matrix.to_csv(output_path / "drawdown_overlap.csv", index_label="system_name")

    run_metadata = {
        "manifest_path": str(manifest_path),
        "instrument": systems[0].instrument,
        "system_count": len(systems),
        "pair_count": len(pairwise_rows),
    }
    (output_path / "run_metadata.json").write_text(json.dumps(run_metadata, indent=2), encoding="utf-8")

    summary = {
        "manifest_path": str(manifest_path),
        "instrument": systems[0].instrument,
        "systems": resolved,
        "pairwise_matrix": pairwise_rows,
        "system_summary": system_summaries,
    }
    (output_path / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark pairwise system correlation and portfolio overlap.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> dict[str, Any]:
    args = parse_args()
    result = run_benchmark(
        manifest_path=args.manifest,
        output_dir=args.output_dir or "ML/reports/system_correlation_portfolio/run",
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2, default=str))
    return result


if __name__ == "__main__":
    main()
