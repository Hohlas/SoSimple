from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

import pandas as pd

from ML.entry_path_task import ENTRY_PATH_V1_FEATURE_COLUMNS
from ML.live_safe_audit import FeatureTrace, classify_feature_name, verdict_from_features
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
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
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
        elif name in {"pred_ret_24_q10", "pred_ret_24_q90"}:
            traces.append(
                FeatureTrace(
                    name=name,
                    role="filter_input",
                    source_path="ML/checkpoints/transformer_entry_path_v1_quantile_best.pt",
                    producer="entry_path_v1_quantile model output",
                    consumer="API/export_entry_path_v1_quantile_signals.py",
                    transformation="quantile model prediction used by frozen rule",
                    availability_time="after_model_inference",
                    live_safe_status=classify_feature_name("session_hour").live_safe_status,
                    evidence="ML/reports/entry_path_v1_quantile_selected_rule.json",
                    notes="This is a model output, not a raw future-derived training input; final system still fails through baseline dependency.",
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


def build_system_verdict(system: AuditedSystem) -> dict:
    traces = build_feature_contract(system)
    verdict = verdict_from_features(traces)
    forbidden_features = verdict.failing_features
    unknown_features = verdict.unknown_features
    allowed_next_step = {
        "PASS": "MT4 tester parity, forward validation, then online dry-run",
        "FAIL": "Reject old checkpoint for online use or retrain/rebuild with live-safe features",
        "UNKNOWN": "Gather source/timing evidence before any ML-quality online test",
    }[verdict.verdict]
    return {
        "system_name": system.system_name,
        "verdict": verdict.verdict,
        "reason": verdict.reason,
        "failed_checks": ["future_derived_input_features"] if forbidden_features else [],
        "unknown_checks": ["unresolved_feature_timing"] if unknown_features else [],
        "forbidden_features": forbidden_features,
        "unknown_features": unknown_features,
        "allowed_next_step": allowed_next_step,
        "leakage_gate_path": "docs/audit/ml_trading_methodology.md#3-feature-contract-и-leakage-gate",
    }


def run_verdicts(output_dir: Path, systems: Iterable[AuditedSystem] | None = None) -> dict:
    selected_systems = tuple(systems or get_audited_systems())
    verdicts = []
    for system in selected_systems:
        verdict = build_system_verdict(system)
        verdicts.append(verdict)
        write_json(output_dir / system.system_name / "verdict.json", verdict)
    summary = {"systems": verdicts}
    write_json(output_dir / "verdict_summary.json", summary)
    return summary


def _read_json_if_present(path: str) -> dict:
    if not path or not Path(path).exists():
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_legacy_reproduction(system: AuditedSystem) -> dict:
    rule_payload = _read_json_if_present(system.rule_path)
    source = rule_payload.get("source", {})
    frozen_validation = rule_payload.get("frozen_validation", {})
    frozen_test = rule_payload.get("frozen_test", {})
    if not frozen_test and "sequential_summary" in rule_payload:
        frozen_test = rule_payload["sequential_summary"]

    return {
        "system_name": system.system_name,
        "reproduction_mode": "artifact_only",
        "model_changed": False,
        "threshold_changed": False,
        "rule_path": system.rule_path,
        "checkpoint_path": system.checkpoint_path or source.get("checkpoint_path", ""),
        "source_report_paths": list(system.report_paths),
        "frozen_validation": frozen_validation,
        "frozen_test": frozen_test,
        "winner": rule_payload.get("winner", {}),
        "mt4_or_parity_evidence": {
            "known_from_reports": list(system.report_paths),
        },
        "notes": "Legacy result was summarized from frozen artifacts only; no retrain or threshold search was run.",
    }


def summarize_signal_csv(path: Path) -> dict:
    frame = pd.read_csv(path, sep=";")
    signals = pd.to_numeric(frame["signal"], errors="coerce").fillna(0).astype(int)
    nonzero = signals != 0
    return {
        "rows_total": int(len(frame)),
        "nonzero_rows": int(nonzero.sum()),
        "buy_rows": int((signals[nonzero] > 0).sum()),
        "sell_rows": int((signals[nonzero] < 0).sum()),
    }


def build_legacy_export(system: AuditedSystem, output_dir: Path) -> dict:
    system_dir = output_dir / system.system_name
    output_path = system_dir / "legacy_export.csv"
    metadata_path = system_dir / "legacy_export_metadata.json"

    if system.system_name in {"quality", "frequency", "original_plus_path"}:
        from API.export_take_skip_trailing_stop_v2_signals import export_signals

        predictions_path = system.prediction_paths[-1]
        export_signals(
            predictions_path=predictions_path,
            rule_path=system.rule_path,
            output_path=output_path,
            metadata_output=metadata_path,
            label=f"{system.system_name}_legacy_export",
        )
    elif system.system_name == "entry_path_v1":
        from API.export_entry_path_v1_signals import export_signals

        predictions_path = system.prediction_paths[-1]
        export_signals(
            predictions_path=predictions_path,
            rule_path=system.rule_path,
            output_path=output_path,
        )
        write_json(
            metadata_path,
            {
                "label": f"{system.system_name}_legacy_export",
                "predictions_path": predictions_path,
                "rule_path": system.rule_path,
                "output_path": str(output_path),
                **summarize_signal_csv(output_path),
            },
        )
    elif system.system_name == "entry_path_v1_quantile":
        from API.export_entry_path_v1_quantile_signals import export_signals

        seed_dir = Path(system.prediction_paths[-1]).parent
        baseline_predictions_path = "ML/reports/entry_path_test_predictions.csv"
        export_signals(
            seed_dir=seed_dir,
            split="test",
            output_path=output_path,
            rule_path=system.rule_path,
            baseline_predictions_path=baseline_predictions_path,
        )
        write_json(
            metadata_path,
            {
                "label": f"{system.system_name}_legacy_export",
                "seed_dir": str(seed_dir),
                "baseline_predictions_path": baseline_predictions_path,
                "rule_path": system.rule_path,
                "output_path": str(output_path),
                **summarize_signal_csv(output_path),
            },
        )
    else:
        raise ValueError(f"unsupported legacy export system: {system.system_name}")

    metadata = _read_json_if_present(str(metadata_path))
    return {
        "system_name": system.system_name,
        "mode": "legacy_inputs_old_features",
        "diagnostic_only": True,
        "output_path": str(output_path),
        "metadata_path": str(metadata_path),
        "metadata": metadata,
    }


def run_legacy_reproduction(output_dir: Path, systems: Iterable[AuditedSystem] | None = None) -> dict:
    selected_systems = tuple(systems or get_audited_systems())
    reproductions = []
    for system in selected_systems:
        legacy = build_legacy_reproduction(system)
        reproductions.append(legacy)
        write_json(output_dir / system.system_name / "legacy_reproduction.json", legacy)
    summary = {"systems": reproductions}
    write_json(output_dir / "legacy_reproduction_summary.json", summary)
    return summary


def run_legacy_exports(output_dir: Path, systems: Iterable[AuditedSystem] | None = None) -> dict:
    selected_systems = tuple(systems or get_audited_systems())
    exports = [build_legacy_export(system, output_dir) for system in selected_systems]
    summary = {"systems": exports}
    write_json(output_dir / "legacy_export_summary.json", summary)
    return summary


def run_all(output_dir: Path) -> dict:
    manifest = run_inventory(output_dir)
    feature_summary = run_feature_contract(output_dir)
    verdict_summary = run_verdicts(output_dir)
    legacy_summary = run_legacy_reproduction(output_dir)
    export_summary = run_legacy_exports(output_dir)
    return {
        "manifest": manifest,
        "feature_contract": feature_summary,
        "verdicts": verdict_summary,
        "legacy_reproduction": legacy_summary,
        "legacy_exports": export_summary,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run live-safe ML audit phases.")
    parser.add_argument(
        "--phase",
        choices=("inventory", "feature-contract", "verdicts", "legacy-reproduction", "legacy-export", "all"),
        required=True,
    )
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
    elif args.phase == "verdicts":
        summary = run_verdicts(output_dir)
        print(json.dumps({"phase": args.phase, "output_dir": str(output_dir), "systems": summary["systems"]}))
    elif args.phase == "legacy-reproduction":
        summary = run_legacy_reproduction(output_dir)
        print(json.dumps({"phase": args.phase, "output_dir": str(output_dir), "systems": summary["systems"]}))
    elif args.phase == "legacy-export":
        summary = run_legacy_exports(output_dir)
        print(json.dumps({"phase": args.phase, "output_dir": str(output_dir), "systems": summary["systems"]}))
    elif args.phase == "all":
        summary = run_all(output_dir)
        print(
            json.dumps(
                {
                    "phase": args.phase,
                    "output_dir": str(output_dir),
                    "systems": summary["manifest"]["systems"],
                }
            )
        )


if __name__ == "__main__":
    main()
