# =============================================================================
# Файл: benchmark_cross_instrument_robustness.py
# Назначение: Benchmark устойчивости систем при смене провайдера и переносе на новые инструменты.
# Обновлён: 2026-04-23
# Входные данные:
#   - manifest JSON с датасетами и signal CSV (откуда: ML/reports/cross_instrument_robustness/*)
# Выходные данные:
#   - summary.csv/json, provider_drift.csv, transfer_matrix.csv, trades.csv (куда: output_dir)
# Использование:
#   python -m ML.benchmark_cross_instrument_robustness --manifest ... --output-dir ...
# Примечания:
#   - текущая версия реализует загрузку и валидацию manifest
# =============================================================================

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from ML.benchmark_execution_policy_v2 import DEFAULT_POLICIES
from ML.benchmark_execution_policy_v2 import ExitPolicy
from ML.benchmark_execution_policy_v2 import _summarize
from ML.benchmark_execution_policy_v2 import load_ohlc
from ML.benchmark_execution_policy_v2 import load_signals
from ML.benchmark_execution_policy_v2 import simulate_policy
from ML.benchmark_signal_export_parity import analyze_signal_export


KNOWN_DATASET_KINDS = {"provider_drift_baseline", "cross_instrument_transfer"}
DEFAULT_VERDICT_THRESHOLDS = {
    "provider_min_pf": 1.0,
    "provider_stable_min_trades_ratio": 0.5,
    "provider_stable_max_drawdown_ratio": 2.0,
    "provider_stable_max_top1_increase": 0.12,
    "provider_degraded_min_trades_ratio": 0.4,
    "provider_degraded_max_drawdown_ratio": 2.5,
    "provider_degraded_max_top1_increase": 0.20,
    "transfer_supported_min_pf": 1.2,
    "transfer_supported_min_trades_ratio": 0.5,
    "transfer_supported_max_drawdown_ratio": 2.0,
    "transfer_supported_max_top1_increase": 0.15,
    "transfer_inconclusive_min_pf": 1.0,
    "transfer_inconclusive_min_trades_ratio": 0.4,
    "transfer_inconclusive_max_drawdown_ratio": 2.5,
    "transfer_inconclusive_max_top1_increase": 0.22,
}


@dataclass(frozen=True)
class RobustnessSignalSpec:
    system_name: str
    signal_csv: Path
    policy_name: str


@dataclass(frozen=True)
class RobustnessDataset:
    dataset_name: str
    instrument: str
    provider: str
    kind: str
    ohlc_path: Path
    signals: tuple[RobustnessSignalSpec, ...]


def validate_manifest(payload: dict) -> tuple[RobustnessDataset, ...]:
    datasets_raw = payload.get("datasets")
    if not isinstance(datasets_raw, list) or not datasets_raw:
        raise ValueError("manifest must contain non-empty datasets list")

    datasets: list[RobustnessDataset] = []
    seen_names: set[str] = set()

    for item in datasets_raw:
        dataset_name = str(item.get("dataset_name", "")).strip()
        if not dataset_name:
            raise ValueError("dataset_name is required")
        if dataset_name in seen_names:
            raise ValueError(f"duplicate dataset_name: {dataset_name}")
        seen_names.add(dataset_name)

        kind = str(item.get("kind", "")).strip()
        if kind not in KNOWN_DATASET_KINDS:
            raise ValueError(f"unknown dataset kind: {kind}")

        ohlc_path = Path(str(item.get("ohlc_path", "")).strip())
        if not ohlc_path.exists():
            raise ValueError(f"missing ohlc_path: {ohlc_path}")

        signals_raw = item.get("signals")
        if not isinstance(signals_raw, list) or not signals_raw:
            raise ValueError(f"dataset {dataset_name} must contain non-empty signals list")

        signals: list[RobustnessSignalSpec] = []
        for signal_item in signals_raw:
            system_name = str(signal_item.get("system_name", "")).strip()
            signal_csv = Path(str(signal_item.get("signal_csv", "")).strip())
            policy_name = str(signal_item.get("policy_name", "")).strip()
            if not system_name:
                raise ValueError(f"dataset {dataset_name} has signal with empty system_name")
            if not policy_name:
                raise ValueError(f"dataset {dataset_name} has signal with empty policy_name")
            if not signal_csv.exists():
                raise ValueError(f"missing signal_csv: {signal_csv}")
            signals.append(
                RobustnessSignalSpec(
                    system_name=system_name,
                    signal_csv=signal_csv,
                    policy_name=policy_name,
                )
            )

        datasets.append(
            RobustnessDataset(
                dataset_name=dataset_name,
                instrument=str(item.get("instrument", "")).strip(),
                provider=str(item.get("provider", "")).strip(),
                kind=kind,
                ohlc_path=ohlc_path,
                signals=tuple(signals),
            )
        )

    return tuple(datasets)


def load_manifest(path: str | Path) -> tuple[RobustnessDataset, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_manifest(payload)


def load_baseline_reference(path: str | Path | None) -> dict:
    if path is None:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("baseline reference must be a JSON object")
    return payload


def _policy_registry(policies: Iterable[ExitPolicy] = DEFAULT_POLICIES) -> dict[str, ExitPolicy]:
    return {policy.name: policy for policy in policies}


def _metric_float(value: object) -> float:
    if isinstance(value, str):
        if value.lower() == "inf":
            return float("inf")
        return float(value)
    return float(value)


def evaluate_verdict(row: dict, baseline: dict, thresholds: dict | None = None) -> dict:
    thresholds = thresholds or DEFAULT_VERDICT_THRESHOLDS

    pf = _metric_float(row["pf"])
    trades_ratio = float(row["trades"]) / max(float(baseline["trades"]), 1.0)
    drawdown_ratio = float(row["max_drawdown_atr"]) / max(float(baseline["max_drawdown_atr"]), 1e-9)
    top1_increase = float(row["profit_concentration_top_1"]) - float(baseline["profit_concentration_top_1"])
    kind = row["kind"]

    result = {
        "trades_ratio": trades_ratio,
        "drawdown_ratio": drawdown_ratio,
        "top1_increase": top1_increase,
        "reason": "",
        "verdict": "",
    }

    if kind == "provider_drift_baseline":
        if (
            pf <= thresholds["provider_min_pf"]
            or trades_ratio < thresholds["provider_degraded_min_trades_ratio"]
            or drawdown_ratio > thresholds["provider_degraded_max_drawdown_ratio"]
        ):
            result["verdict"] = "provider_failed"
            result["reason"] = "provider drift broke practical baseline"
            return result
        if (
            trades_ratio >= thresholds["provider_stable_min_trades_ratio"]
            and drawdown_ratio <= thresholds["provider_stable_max_drawdown_ratio"]
            and top1_increase <= thresholds["provider_stable_max_top1_increase"]
        ):
            result["verdict"] = "provider_stable"
            result["reason"] = "provider drift remains inside stable band"
            return result

        result["verdict"] = "provider_degraded"
        result["reason"] = "provider drift stays tradable but leaves stable band"
        return result

    if kind == "cross_instrument_transfer":
        if (
            pf < thresholds["transfer_inconclusive_min_pf"]
            or trades_ratio < thresholds["transfer_inconclusive_min_trades_ratio"]
            or drawdown_ratio > thresholds["transfer_inconclusive_max_drawdown_ratio"]
            or top1_increase > thresholds["transfer_inconclusive_max_top1_increase"]
        ):
            result["verdict"] = "transfer_failed"
            result["reason"] = "transfer metrics fall below practical floor"
            return result
        if (
            pf >= thresholds["transfer_supported_min_pf"]
            and trades_ratio >= thresholds["transfer_supported_min_trades_ratio"]
            and drawdown_ratio <= thresholds["transfer_supported_max_drawdown_ratio"]
            and top1_increase <= thresholds["transfer_supported_max_top1_increase"]
        ):
            result["verdict"] = "transfer_supported"
            result["reason"] = "transfer keeps practical quality without blow-up"
            return result

        result["verdict"] = "transfer_inconclusive"
        result["reason"] = "transfer stays above failure floor but support is weak"
        return result

    raise ValueError(f"unknown verdict kind: {kind}")


def analyze_signal_alignment(signals_path: str | Path, ohlc_path: str | Path) -> dict:
    export = analyze_signal_export(signals_path)
    ohlc = pd.read_csv(Path(ohlc_path), sep=";", usecols=["time"])
    ohlc_times = set(ohlc["time"].astype(str))

    signals = pd.read_csv(Path(signals_path), sep=";", usecols=["time", "signal"])
    signals["time"] = signals["time"].astype(str)
    signals["signal"] = pd.to_numeric(signals["signal"], errors="coerce").fillna(0).astype(int)
    nonzero = signals[signals["signal"] != 0].copy()
    missing_times = sorted(set(nonzero["time"]) - ohlc_times)

    return {
        **export,
        "ohlc_path": str(ohlc_path),
        "ohlc_unique_time_total": int(len(ohlc_times)),
        "missing_ohlc_times": int(len(missing_times)),
        "missing_ohlc_examples": missing_times[:20],
    }


def assert_signal_alignment_ok(diagnostics: dict) -> None:
    if diagnostics["missing_ohlc_times"] > 0:
        raise ValueError("signals contain timestamps outside ohlc coverage")


def run_benchmark(
    manifest_path: str | Path,
    output_dir: str | Path,
    baseline_reference_path: str | Path | None = None,
) -> dict:
    datasets = load_manifest(manifest_path)
    baseline_reference = load_baseline_reference(baseline_reference_path)
    policy_registry = _policy_registry()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summaries: list[dict] = []
    all_trades: list[pd.DataFrame] = []

    for dataset in datasets:
        bars, index_by_time = load_ohlc(dataset.ohlc_path)
        for signal_spec in dataset.signals:
            if signal_spec.policy_name not in policy_registry:
                raise ValueError(f"unknown policy_name: {signal_spec.policy_name}")
            policy = policy_registry[signal_spec.policy_name]
            alignment = analyze_signal_alignment(signal_spec.signal_csv, dataset.ohlc_path)
            assert_signal_alignment_ok(alignment)
            signals = load_signals(signal_spec.signal_csv)
            trades = simulate_policy(signals, bars, index_by_time, policy)
            if not trades.empty:
                trades = trades.copy()
                trades.insert(0, "system_name", signal_spec.system_name)
                trades.insert(0, "dataset_name", dataset.dataset_name)
                all_trades.append(trades)
            summary = _summarize(dataset.dataset_name, policy, trades)
            summary["system_name"] = signal_spec.system_name
            summary["instrument"] = dataset.instrument
            summary["provider"] = dataset.provider
            summary["kind"] = dataset.kind
            summary["alignment"] = alignment
            baseline = baseline_reference.get(signal_spec.system_name)
            if baseline is not None:
                verdict_info = evaluate_verdict(summary, baseline)
                summary.update(verdict_info)
            summaries.append(summary)

    summary_frame = pd.DataFrame(summaries)
    summary_frame.to_csv(output_dir / "summary.csv", index=False)
    trades_frame = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()
    trades_frame.to_csv(output_dir / "trades.csv", index=False)
    provider_drift_frame = summary_frame[summary_frame["kind"] == "provider_drift_baseline"].copy()
    transfer_matrix_frame = summary_frame[summary_frame["kind"] == "cross_instrument_transfer"].copy()
    provider_drift_frame.to_csv(output_dir / "provider_drift.csv", index=False)
    transfer_matrix_frame.to_csv(output_dir / "transfer_matrix.csv", index=False)

    result = {
        "manifest_path": str(manifest_path),
        "baseline_reference_path": str(baseline_reference_path) if baseline_reference_path is not None else None,
        "summary": summaries,
        "provider_drift": provider_drift_frame.to_dict("records"),
        "transfer_matrix": transfer_matrix_frame.to_dict("records"),
    }
    (output_dir / "summary.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    run_metadata = {
        "dataset_count": len(datasets),
        "summary_rows": len(summaries),
        "provider_drift_rows": int(len(provider_drift_frame)),
        "transfer_rows": int(len(transfer_matrix_frame)),
    }
    (output_dir / "run_metadata.json").write_text(json.dumps(run_metadata, indent=2), encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark provider drift and cross-instrument transfer with frozen rules.")
    parser.add_argument("--manifest", required=True, help="Manifest JSON with datasets, OHLC paths and signal CSV paths.")
    parser.add_argument(
        "--baseline-reference",
        default=None,
        help="Optional JSON with baseline metrics for verdict evaluation.",
    )
    parser.add_argument("--output-dir", required=True, help="Output directory for benchmark artifacts.")
    return parser.parse_args()


def main() -> dict:
    args = parse_args()
    result = run_benchmark(
        manifest_path=args.manifest,
        baseline_reference_path=args.baseline_reference,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return result


if __name__ == "__main__":
    main()
