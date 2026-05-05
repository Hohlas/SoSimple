from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from ML.entry_path_task import ENTRY_PATH_V1_FEATURE_COLUMNS
from ML.live_safe_audit import FeatureTrace, classify_feature_name
from ML.live_safe_audit_registry import AuditedSystem, get_audited_systems
from ML.run_take_skip_original_contour_feature_matrix import ORIGINAL_BASELINE_ROW_FEATURE_COLUMNS


def _system_paths(system: AuditedSystem) -> list[str]:
    paths: list[str] = []
    for path in (system.checkpoint_path, system.rule_path):
        if path:
            paths.append(path)
    paths.extend(system.prediction_paths)
    paths.extend(system.report_paths)
    return paths


def build_artifact_inventory(system: AuditedSystem) -> dict:
    existing_paths: list[str] = []
    missing_paths: list[str] = []
    for path in _system_paths(system):
        if Path(path).exists():
            existing_paths.append(path)
        else:
            missing_paths.append(path)

    return {
        "system_name": system.system_name,
        "checkpoint_path": system.checkpoint_path,
        "rule_path": system.rule_path,
        "prediction_paths": list(system.prediction_paths),
        "report_paths": list(system.report_paths),
        "existing_paths": existing_paths,
        "missing_paths": missing_paths,
        "expected_risk_note": system.expected_risk_note,
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_feature_csv(path: Path, traces: Iterable[FeatureTrace]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "feature_name",
        "raw_field_index",
        "raw_source_field",
        "producer_code_path",
        "consumer_code_path",
        "transformation_path",
        "role",
        "availability_time",
        "live_safe_status",
        "evidence",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for trace in traces:
            writer.writerow(
                {
                    "feature_name": trace.name,
                    "raw_field_index": "",
                    "raw_source_field": trace.name,
                    "producer_code_path": trace.producer,
                    "consumer_code_path": trace.consumer,
                    "transformation_path": trace.transformation,
                    "role": trace.role,
                    "availability_time": trace.availability_time,
                    "live_safe_status": str(trace.live_safe_status),
                    "evidence": trace.evidence,
                    "notes": trace.notes,
                }
            )


def feature_names_for_system(system: AuditedSystem) -> tuple[str, ...]:
    if system.system_name in {"quality", "frequency", "original_plus_path"}:
        return tuple(ORIGINAL_BASELINE_ROW_FEATURE_COLUMNS)
    if system.system_name == "entry_path_v1":
        return tuple(ENTRY_PATH_V1_FEATURE_COLUMNS)
    if system.system_name == "entry_path_v1_quantile":
        return ("baseline_dependency:entry_path_v1", "pred_ret_24_q10", "pred_ret_24_q90")
    return ()


def build_feature_contract(system: AuditedSystem) -> list[FeatureTrace]:
    traces = []
    for name in feature_names_for_system(system):
        if name == "baseline_dependency:entry_path_v1":
            traces.append(
                FeatureTrace(
                    name=name,
                    role="filter_dependency",
                    source_path="ML/reports/entry_path_trade_filter_selected_rule.json",
                    producer="entry_path_v1 baseline score",
                    consumer="API/export_entry_path_v1_quantile_signals.py",
                    transformation="baseline score gate before quantile rule",
                    availability_time="unknown",
                    live_safe_status=classify_feature_name("ret_dir_atr_lag1").live_safe_status,
                    evidence="docs/superpowers/specs/2026-05-05-live-safe-ml-audit-design.md",
                    notes="Production quantile rule depends on entry_path_v1, so it inherits unresolved baseline timing risk.",
                )
            )
        else:
            traces.append(classify_feature_name(name))
    return traces


def run_inventory(output_dir: Path, systems: Iterable[AuditedSystem] | None = None) -> dict:
    selected_systems = tuple(systems or get_audited_systems())
    inventories = []
    for system in selected_systems:
        inventory = build_artifact_inventory(system)
        inventories.append(inventory)
        write_json(output_dir / system.system_name / "artifact_inventory.json", inventory)

    manifest = {
        "systems": [system.system_name for system in selected_systems],
        "system_count": len(selected_systems),
        "artifacts": inventories,
        "registry": [asdict(system) for system in selected_systems],
    }
    write_json(output_dir / "manifest.json", manifest)
    return manifest


def run_feature_contract(output_dir: Path, systems: Iterable[AuditedSystem] | None = None) -> dict:
    selected_systems = tuple(systems or get_audited_systems())
    summary = {"systems": []}
    for system in selected_systems:
        traces = build_feature_contract(system)
        system_dir = output_dir / system.system_name
        write_feature_csv(system_dir / "feature_contract.csv", traces)
        write_feature_csv(system_dir / "source_trace.csv", traces)
        summary["systems"].append(
            {
                "system_name": system.system_name,
                "feature_count": len(traces),
                "fail_count": sum(1 for trace in traces if trace.live_safe_status == "FAIL"),
                "unknown_count": sum(1 for trace in traces if trace.live_safe_status == "UNKNOWN"),
            }
        )
    write_json(output_dir / "feature_contract_summary.json", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run live-safe ML audit phases.")
    parser.add_argument("--phase", choices=("inventory", "feature-contract"), required=True)
    parser.add_argument("--output-dir", default="ML/reports/live_safe_ml_audit")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if args.phase == "inventory":
        manifest = run_inventory(output_dir)
        print(json.dumps({"phase": args.phase, "output_dir": str(output_dir), "systems": manifest["systems"]}))
    elif args.phase == "feature-contract":
        summary = run_feature_contract(output_dir)
        print(json.dumps({"phase": args.phase, "output_dir": str(output_dir), "systems": summary["systems"]}))


if __name__ == "__main__":
    main()
