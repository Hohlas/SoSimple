from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from ML.live_safe_audit_registry import AuditedSystem, get_audited_systems


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run live-safe ML audit phases.")
    parser.add_argument("--phase", choices=("inventory",), required=True)
    parser.add_argument("--output-dir", default="ML/reports/live_safe_ml_audit")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if args.phase == "inventory":
        manifest = run_inventory(output_dir)
        print(json.dumps({"phase": args.phase, "output_dir": str(output_dir), "systems": manifest["systems"]}))


if __name__ == "__main__":
    main()
