from __future__ import annotations

# =============================================================================
# Файл: audit_fractal0_fixed11_candidate.py
# Назначение: Read-only аудит fixed-11 locked-test артефактов Fractal0.
# Язык: Python 3.10+
# Обновлён: 2026-07-26
# Зависимости:
#   Входные данные:
#     - ML/reports/fractal0_fixed11_rich_entry_locked_test*.json/csv
#   Выходные данные:
#     - ML/reports/fractal0_fixed11_candidate_audit.json
#     - ML/reports/fractal0_fixed11_candidate_audit_findings.csv
# Использование:
#   ./.venv/bin/python ML/baseline/audit_fractal0_fixed11_candidate.py --input-prefix ... --output-prefix ...
# Примечания:
#   - Не выполняет новый поиск и не выбирает winner по locked_test.
# =============================================================================

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

EXPECTED_RULE_COUNT = 11
EXPECTED_LOCKED_TEST_START = "2022-12-02"
EXPECTED_LOCKED_TEST_END = "2026-06-04"
EXPECTED_LOCKED_TEST_ROWS = 9463
MIN_PF = 1.20
MIN_BS_P05 = 1.00
MIN_TRADES = 100
MIN_YEAR_TRADES = 30
BS_P05_METHOD = "current_iid_trade_bootstrap_despite_block_bootstrap_pf_name"


@dataclass(frozen=True)
class AuditFinding:
    severity: str
    check_id: str
    message: str
    rule_id: str | None = None


@dataclass(frozen=True)
class AuditArtifacts:
    payload: dict[str, Any]
    summary: pd.DataFrame
    selection: pd.DataFrame
    yearly: pd.DataFrame
    side: pd.DataFrame
    trades: pd.DataFrame


def _csv_path(prefix: Path, suffix: str) -> Path:
    return prefix.with_name(f"{prefix.name}_{suffix}.csv")


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, sep=";")


def load_artifacts(prefix: Path) -> AuditArtifacts:
    json_path = prefix.with_suffix(".json")
    if not json_path.exists():
        raise FileNotFoundError(json_path)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    return AuditArtifacts(
        payload=payload,
        summary=_read_csv(_csv_path(prefix, "summary")),
        selection=_read_csv(_csv_path(prefix, "selection")),
        yearly=_read_csv(_csv_path(prefix, "yearly")),
        side=_read_csv(_csv_path(prefix, "side")),
        trades=_read_csv(_csv_path(prefix, "trades")),
    )


def _error(check_id: str, message: str, rule_id: str | None = None) -> AuditFinding:
    return AuditFinding("ERROR", check_id, message, rule_id)


def _warning(check_id: str, message: str, rule_id: str | None = None) -> AuditFinding:
    return AuditFinding("WARNING", check_id, message, rule_id)


def validate_artifact_contract(artifacts: AuditArtifacts) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    required_frames = {
        "summary": artifacts.summary,
        "selection": artifacts.selection,
        "yearly": artifacts.yearly,
        "side": artifacts.side,
        "trades": artifacts.trades,
    }
    for name, frame in required_frames.items():
        if frame.empty:
            findings.append(_error("empty_artifact", f"{name} CSV has no rows"))
        if name != "trades" and "rule_id" not in frame.columns:
            findings.append(_error("missing_rule_id_column", f"{name} CSV has no rule_id column"))

    rule_ids = set()
    for frame in (artifacts.summary, artifacts.selection, artifacts.yearly, artifacts.side):
        if "rule_id" in frame.columns:
            rule_ids.update(frame["rule_id"].dropna().astype(str).unique())
    if len(rule_ids) != EXPECTED_RULE_COUNT:
        findings.append(
            _error(
                "rule_id_count_mismatch",
                f"expected {EXPECTED_RULE_COUNT} unique rule_id values, got {len(rule_ids)}",
            )
        )
    if artifacts.payload.get("rule_count") != EXPECTED_RULE_COUNT:
        findings.append(_error("rule_count_mismatch", "payload rule_count is not 11"))
    return findings


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else Path.cwd() / path


def _time_bounds(frame: pd.DataFrame) -> tuple[str, str] | None:
    if "time" not in frame.columns:
        return None
    series = pd.to_datetime(frame["time"], errors="coerce").dropna()
    if series.empty:
        return None
    return str(series.min()), str(series.max())


def build_split_boundaries(artifacts: AuditArtifacts) -> dict[str, dict[str, Any]]:
    boundaries: dict[str, dict[str, Any]] = {}
    locked_path_text = artifacts.payload.get("locked_test_path")
    if locked_path_text:
        locked_path = _resolve(str(locked_path_text))
        if locked_path.exists():
            locked = pd.read_csv(locked_path, sep=";")
            bounds = _time_bounds(locked)
            if bounds is not None:
                boundaries["locked_test"] = {
                    "row_count": int(len(locked)),
                    "min_time": bounds[0],
                    "max_time": bounds[1],
                    "source": "computed_from_local_csv",
                }

    try:
        from ML.baseline import benchmark_fractal0_entry_exit_grid as base
    except ImportError:
        return boundaries

    try:
        splits = base.load_role_splits()
    except Exception:
        return boundaries

    for role, frame in splits.items():
        bounds = _time_bounds(frame)
        if bounds is None:
            continue
        boundaries[role] = {
            "row_count": int(len(frame)),
            "min_time": bounds[0],
            "max_time": bounds[1],
            "source": "computed_from_local_csv",
        }
    return boundaries


def audit_pre_open_freeze(artifacts: AuditArtifacts) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for path in (
        Path("ML/reports/fractal0_fixed11_locked_test_freeze.json"),
        Path("ML/reports/fractal0_fixed11_locked_test_selection_policy.json"),
    ):
        if not path.exists():
            findings.append(_error("pre_open_freeze_artifact_missing", f"missing {path}"))
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if "rule_hash_sha256" not in data:
            findings.append(_error("pre_open_freeze_rule_hash_missing", f"{path} lacks rule_hash_sha256"))
    return findings


def audit_hashes(artifacts: AuditArtifacts) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    hash_pairs = [
        ("source_rules_csv", "source_rules_csv_sha256"),
        ("source_artifact", "source_artifact_sha256"),
        ("locked_test_path", "locked_test_sha256"),
        ("execution_ohlc_path", "execution_ohlc_sha256"),
        ("h1_ohlc_path", "h1_ohlc_sha256"),
    ]
    for path_key, hash_key in hash_pairs:
        path_text = artifacts.payload.get(path_key)
        declared = artifacts.payload.get(hash_key)
        if not path_text or not declared:
            findings.append(_error("source_hash_missing", f"missing {path_key} or {hash_key}"))
            continue
        path = _resolve(str(path_text))
        if not path.exists():
            findings.append(_error("source_file_missing", f"missing source file {path_text}"))
            continue
        actual = _sha256(path)
        if actual != declared:
            findings.append(_error("source_hash_mismatch", f"{path_key} hash mismatch"))
    if "source_runner_sha256" not in artifacts.payload:
        findings.append(_warning("source_runner_hash_missing_from_locked_test_json", "locked-test JSON lacks runner hash"))
    runner = artifacts.payload.get("source_runner") or artifacts.payload.get("source_runner_declared_path")
    if runner and _resolve(str(runner)).exists():
        artifacts.payload["source_runner_sha256"] = _sha256(_resolve(str(runner)))
        artifacts.payload["source_runner_declared_path"] = str(runner)
    return findings


def audit_split_policy(artifacts: AuditArtifacts) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    roles = artifacts.payload.get("split_roles")
    if not isinstance(roles, dict):
        return [_error("split_disclosure_missing", "payload lacks split_roles disclosure")]
    for role in ("train_core", "val_select", "val_eval", "locked_test"):
        if role not in roles:
            findings.append(_error("split_role_missing", f"missing split role {role}"))
        elif not isinstance(roles.get(role), dict):
            findings.append(_error("split_role_detail_missing", f"split role {role} lacks row_count/min_time/max_time details"))
    locked = roles.get("locked_test", {})
    if not isinstance(locked, dict):
        locked = {}
    if locked.get("row_count") != EXPECTED_LOCKED_TEST_ROWS:
        findings.append(_error("locked_test_row_count_mismatch", "locked_test row_count is not 9463"))
    if str(locked.get("min_time", ""))[:10] != EXPECTED_LOCKED_TEST_START:
        findings.append(_error("locked_test_period_mismatch", "locked_test min_time mismatch"))
    if str(locked.get("max_time", ""))[:10] != EXPECTED_LOCKED_TEST_END:
        findings.append(_error("locked_test_period_mismatch", "locked_test max_time mismatch"))
    if artifacts.payload.get("locked_test_not_used_for_selection") is not True:
        findings.append(
            _error("locked_test_selection_disclosure_missing", "missing disclosure that locked_test was not used for selection")
        )
    return findings


def audit_candidate_gates(artifacts: AuditArtifacts) -> list[AuditFinding]:
    findings: list[AuditFinding] = [
        _warning("bs_p05_iid_bootstrap_limitation", "BS_p05 is diagnostic until block/stationary/timestamp-cluster bootstrap exists")
    ]
    summary_ids = set(artifacts.summary["rule_id"].astype(str)) if "rule_id" in artifacts.summary else set()
    selection_ids = set(artifacts.selection["rule_id"].astype(str)) if "rule_id" in artifacts.selection else set()
    if summary_ids != selection_ids:
        findings.append(_error("summary_selection_rule_mismatch", "summary and selection rule_id sets differ"))

    if artifacts.payload.get("correlation_pruning_status") != "FOLLOW_UP_REQUIRED":
        findings.append(_error("correlation_pruning_status_invalid", "correlation pruning must remain FOLLOW_UP_REQUIRED"))

    for _, row in artifacts.summary.iterrows():
        rule_id = str(row.get("rule_id"))
        if float(row.get("pf", 0)) < MIN_PF:
            findings.append(_error("pf_below_gate", "PF below 1.20", rule_id))
        if float(row.get("bs_p05", 0)) < MIN_BS_P05:
            findings.append(_error("bs_p05_below_gate", "BS_p05 below 1.00", rule_id))
        if int(row.get("n_trades", 0)) < MIN_TRADES:
            findings.append(_error("trade_count_below_gate", "n_trades below 100", rule_id))

    for rule_id in summary_ids:
        sides = set(artifacts.side.loc[artifacts.side["rule_id"].astype(str) == rule_id, "side"].astype(str))
        if sides != {"BUY", "SELL"}:
            findings.append(_error("side_coverage_missing", "BUY and SELL rows required", rule_id))
        for _, row in artifacts.side.loc[artifacts.side["rule_id"].astype(str) == rule_id].iterrows():
            if float(row.get("pf", 0)) < MIN_PF:
                findings.append(_error("side_pf_below_gate", "side PF below 1.20", rule_id))

        yearly = artifacts.yearly.loc[artifacts.yearly["rule_id"].astype(str) == rule_id]
        if yearly.empty:
            findings.append(_error("yearly_coverage_missing", "yearly rows required", rule_id))
        for _, row in yearly.iterrows():
            n_trades = int(row.get("n_trades", 0))
            status = str(row.get("year_status", row.get("status", "")))
            if n_trades < MIN_YEAR_TRADES:
                if status != "DIAGNOSTIC_ONLY":
                    findings.append(_error("yearly_low_n_unclassified", "low-N year must be DIAGNOSTIC_ONLY", rule_id))
                continue
            if float(row.get("pf", 0)) < MIN_PF:
                findings.append(_error("yearly_pf_below_gate", "yearly PF below 1.20", rule_id))
            if float(row.get("gross_profit", 0)) - float(row.get("gross_loss", 0)) < 0:
                findings.append(_error("yearly_negative_result", "non-diagnostic yearly result is negative", rule_id))

    movement_rules = [rid for rid in summary_ids if "movement_plus_time" in rid]
    if movement_rules:
        disclosure = artifacts.payload.get("movement_score_restoration")
        required = [
            "affected_rule_count",
            "target",
            "profile",
            "model_family",
            "seeds",
            "fit_split",
            "locked_test_label_usage",
            "scaler_fit_split",
        ]
        if not isinstance(disclosure, dict) or any(disclosure.get(key) in (None, "", "UNKNOWN") for key in required):
            findings.append(_error("movement_score_restoration_disclosure_missing", "movement-score restoration disclosure incomplete"))
        if isinstance(disclosure, dict) and not any(k.endswith("_sha256") for k in disclosure):
            findings.append(_warning("movement_score_source_hash_unknown", "movement-score source hash is UNKNOWN"))
    return findings


def _finding_counts(findings: list[AuditFinding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    return counts


def _findings_payload(findings: list[AuditFinding]) -> list[dict[str, Any]]:
    return [
        {
            "severity": finding.severity,
            "check_id": finding.check_id,
            "message": finding.message,
            "rule_id": finding.rule_id,
        }
        for finding in findings
    ]


def run_audit(prefix: Path) -> tuple[dict[str, Any], list[AuditFinding]]:
    artifacts = load_artifacts(prefix)
    contract_findings = validate_artifact_contract(artifacts)
    freeze_findings = audit_pre_open_freeze(artifacts)
    hash_findings = audit_hashes(artifacts)
    split_findings = audit_split_policy(artifacts)
    gate_findings = audit_candidate_gates(artifacts)
    findings = contract_findings + freeze_findings + hash_findings + split_findings + gate_findings
    blocker_errors = any(
        finding.severity == "ERROR" for finding in contract_findings + freeze_findings + hash_findings + split_findings
    )
    gate_errors = any(finding.severity == "ERROR" for finding in gate_findings)
    if blocker_errors:
        decision = "candidate_audit_blocked"
    elif gate_errors:
        decision = "research_only_downgrade_required"
    else:
        decision = "candidate_audit_passed"
    finding_counts = _finding_counts(findings)
    computed_boundaries = build_split_boundaries(artifacts)
    result = {
        "input_prefix": str(prefix),
        "overall_decision": decision,
        "status": "completed",
        "source_locked_test_verdict": artifacts.payload.get("verdict"),
        "source_runner_declared_path": artifacts.payload.get("source_runner_declared_path") or artifacts.payload.get("source_runner"),
        "source_runner_sha256": artifacts.payload.get("source_runner_sha256"),
        "rule_count": int(artifacts.payload.get("rule_count") or len(artifacts.summary)),
        "evaluated_rule_count": int(artifacts.payload.get("evaluated_rule_count") or len(artifacts.summary)),
        "gate_pass_count": int(artifacts.payload.get("gate_pass_count") or len(artifacts.selection)),
        "kept_candidates": int(artifacts.payload.get("kept_candidates") or len(artifacts.selection)),
        "correlation_pruning_status": artifacts.payload.get("correlation_pruning_status", "MISSING"),
        "bs_p05_method": BS_P05_METHOD,
        "split_roles": artifacts.payload.get("split_roles", {}),
        "split_boundaries": computed_boundaries,
        "source_hashes": {
            key: artifacts.payload.get(key)
            for key in (
                "source_rules_csv_sha256",
                "source_artifact_sha256",
                "locked_test_sha256",
                "execution_ohlc_sha256",
                "h1_ohlc_sha256",
            )
        },
        "pre_open_freeze_paths": {
            "freeze_json": "ML/reports/fractal0_fixed11_locked_test_freeze.json",
            "selection_policy_json": "ML/reports/fractal0_fixed11_locked_test_selection_policy.json",
        },
        "finding_counts": finding_counts,
        "findings": _findings_payload(findings),
        "finding_count": len(findings),
        "error_count": finding_counts.get("ERROR", 0),
        "warning_count": finding_counts.get("WARNING", 0),
    }
    return result, findings


def write_outputs(output_prefix: Path, result: dict[str, Any], findings: list[AuditFinding]) -> None:
    output_prefix.with_suffix(".json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    findings_path = output_prefix.with_name(f"{output_prefix.name}_findings.csv")
    with findings_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["severity", "check_id", "message", "rule_id"], delimiter=";")
        writer.writeheader()
        for finding in findings:
            writer.writerow(asdict(finding))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-prefix", required=True, type=Path)
    parser.add_argument("--output-prefix", required=True, type=Path)
    args = parser.parse_args(argv)
    result, findings = run_audit(args.input_prefix)
    write_outputs(args.output_prefix, result, findings)
    return 0 if result["overall_decision"] == "candidate_audit_passed" else 2


if __name__ == "__main__":
    sys.exit(main())
