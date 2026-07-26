# =============================================================================
# Файл: audit_fractal0_fixed11_candidate.py
# Назначение: Read-only аудит fixed11 locked-test артефактов перед повышением статуса выше `candidate_check_required`
# Обновлён: 2026-07-26
# Зависимости:
#   Входные данные:
#     - ML/reports/fractal0_fixed11_rich_entry_locked_test.json
#     - ML/reports/fractal0_fixed11_rich_entry_locked_test_*.csv
#     - ML/reports/fractal0_fixed11_locked_test_freeze.json
#     - ML/reports/fractal0_fixed11_locked_test_selection_policy.json
#   Выходные данные:
#     - ML/reports/fractal0_fixed11_candidate_audit.json
#     - ML/reports/fractal0_fixed11_candidate_audit_findings.csv
# Использование:
#   ./.venv/bin/python ML/baseline/audit_fractal0_fixed11_candidate.py --input-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test --output-prefix ML/reports/fractal0_fixed11_candidate_audit
# Примечания:
#   - не выполняет новый search и не переоткрывает locked_test
#   - максимум решения: candidate_audit_passed / candidate_audit_blocked / research_only_downgrade_required
# =============================================================================

from __future__ import annotations

import hashlib
import json
import sys
from argparse import ArgumentParser
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

EXPECTED_RULE_COUNT = 11
EXPECTED_LOCKED_TEST_ROWS = 9463
EXPECTED_LOCKED_TEST_MIN_TIME = "2022-12-02 11:00:00"
EXPECTED_LOCKED_TEST_MAX_TIME = "2026-06-04 12:00:00"
FREEZE_JSON_PATH = Path("ML/reports/fractal0_fixed11_locked_test_freeze.json")
SELECTION_POLICY_JSON_PATH = Path("ML/reports/fractal0_fixed11_locked_test_selection_policy.json")


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _required_path(path: Path, label: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"missing {label} artifact: {path}")
    return path


def _read_csv(path: Path, label: str) -> pd.DataFrame:
    frame = pd.read_csv(_required_path(path, label), sep=";")
    if frame.empty:
        raise ValueError(f"empty {label} artifact: {path}")
    return frame


def load_artifacts(prefix: Path) -> AuditArtifacts:
    json_path = _required_path(prefix.with_suffix(".json"), "json")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    return AuditArtifacts(
        payload=payload,
        summary=_read_csv(prefix.with_name(f"{prefix.name}_summary.csv"), "summary"),
        selection=_read_csv(prefix.with_name(f"{prefix.name}_selection.csv"), "selection"),
        yearly=_read_csv(prefix.with_name(f"{prefix.name}_yearly.csv"), "yearly"),
        side=_read_csv(prefix.with_name(f"{prefix.name}_side.csv"), "side"),
        trades=_read_csv(prefix.with_name(f"{prefix.name}_trades.csv"), "trades"),
    )


def _rule_count_findings(frame: pd.DataFrame, artifact_name: str) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    if "rule_id" not in frame.columns:
        return [
            AuditFinding(
                severity="ERROR",
                check_id=f"{artifact_name}_rule_id_missing",
                message=f"{artifact_name} artifact is missing rule_id column",
            )
        ]
    row_count = int(len(frame))
    unique_count = int(frame["rule_id"].astype(str).nunique())
    if row_count != 11 or unique_count != 11:
        findings.append(
            AuditFinding(
                severity="ERROR",
                check_id=f"{artifact_name}_rule_count_invalid",
                message=(
                    f"{artifact_name} artifact must contain exactly 11 rows and 11 unique rule_id values, "
                    f"got rows={row_count}, unique_rule_ids={unique_count}"
                ),
            )
        )
    return findings


def validate_artifact_contract(artifacts: AuditArtifacts) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    findings.extend(_rule_count_findings(artifacts.summary, "summary"))
    findings.extend(_rule_count_findings(artifacts.selection, "selection"))
    return findings


def _error(check_id: str, message: str, rule_id: str | None = None) -> AuditFinding:
    return AuditFinding(severity="ERROR", check_id=check_id, message=message, rule_id=rule_id)


def _warning(check_id: str, message: str, rule_id: str | None = None) -> AuditFinding:
    return AuditFinding(severity="WARNING", check_id=check_id, message=message, rule_id=rule_id)


def _payload_path(payload: dict[str, Any], key: str) -> Path | None:
    value = payload.get(key)
    if not value:
        return None
    path = Path(str(value))
    return path if path.is_absolute() else PROJECT_ROOT / path


def _check_declared_hash(payload: dict[str, Any], path_key: str, hash_key: str) -> list[AuditFinding]:
    path = _payload_path(payload, path_key)
    if path is None:
        return [_error(f"{path_key}_missing", f"locked-test JSON is missing {path_key}")]
    if not path.exists():
        return [_error(f"{path_key}_not_found", f"declared source path does not exist: {path}")]
    expected_hash = payload.get(hash_key)
    if not expected_hash:
        return [_error(f"{hash_key}_missing", f"locked-test JSON is missing {hash_key}")]
    actual_hash = sha256_file(path)
    if str(expected_hash) != actual_hash:
        return [
            _error(
                f"{path_key}_hash_mismatch",
                f"hash mismatch for {path_key}: declared={expected_hash} actual={actual_hash}",
            )
        ]
    return []


def audit_hashes(artifacts: AuditArtifacts) -> list[AuditFinding]:
    payload = artifacts.payload
    findings: list[AuditFinding] = []
    findings.extend(_check_declared_hash(payload, "source_rules_csv", "source_rules_csv_sha256"))
    findings.extend(_check_declared_hash(payload, "source_artifact", "source_artifact_sha256"))
    findings.extend(_check_declared_hash(payload, "locked_test_path", "locked_test_sha256"))
    findings.extend(_check_declared_hash(payload, "h1_ohlc_path", "h1_ohlc_sha256"))
    findings.extend(_check_declared_hash(payload, "execution_ohlc_path", "execution_ohlc_sha256"))

    runner_path = _payload_path(payload, "source_runner")
    if runner_path is None:
        findings.append(_error("source_runner_missing", "locked-test JSON is missing source_runner"))
    elif not runner_path.exists():
        findings.append(_error("source_runner_not_found", f"declared source runner does not exist: {runner_path}"))

    if not payload.get("source_runner_sha256"):
        findings.append(
            _warning(
                "source_runner_hash_missing_from_locked_test_json",
                "locked-test JSON does not record source_runner_sha256; audit must record it separately",
            )
        )
    return findings


def audit_pre_open_freeze(artifacts: AuditArtifacts) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    freeze_exists = FREEZE_JSON_PATH.exists()
    policy_exists = SELECTION_POLICY_JSON_PATH.exists()
    if not freeze_exists or not policy_exists:
        findings.append(
            _error(
                "pre_open_freeze_artifact_missing",
                f"pre-open freeze artifacts are missing: freeze={FREEZE_JSON_PATH} policy={SELECTION_POLICY_JSON_PATH}",
            )
        )
        return findings

    freeze_payload = json.loads(FREEZE_JSON_PATH.read_text(encoding="utf-8"))
    policy_payload = json.loads(SELECTION_POLICY_JSON_PATH.read_text(encoding="utf-8"))
    if not freeze_payload.get("rule_hash_sha256"):
        findings.append(_error("freeze_rule_hash_missing", "freeze artifact is missing rule_hash_sha256"))
    if "execution_contract" not in freeze_payload:
        findings.append(_error("freeze_execution_contract_missing", "freeze artifact is missing execution_contract"))
    if "selection_policy" not in freeze_payload:
        findings.append(_error("freeze_selection_policy_missing", "freeze artifact is missing selection_policy"))
    if "selection_policy" in policy_payload:
        policy_body = policy_payload["selection_policy"]
    else:
        policy_body = policy_payload
    if not isinstance(policy_body, dict) or not policy_body:
        findings.append(_error("selection_policy_invalid", "selection policy artifact is empty or invalid"))
    return findings


@lru_cache(maxsize=4)
def _load_split_snapshot(locked_test_path_str: str) -> dict[str, dict[str, Any]]:
    from ML.baseline import benchmark_fractal0_entry_exit_grid as base

    splits = base.load_role_splits()
    locked_test_path = Path(locked_test_path_str)
    locked_test = pd.read_csv(locked_test_path, sep=";").reset_index(drop=True)
    locked_test["time"] = locked_test["time"].map(base.parse_project_time)
    splits["locked_test"] = locked_test
    snapshot: dict[str, dict[str, Any]] = {}
    for role, frame in splits.items():
        min_time, max_time = _normalized_time_bounds(frame)
        snapshot[role] = {
            "row_count": int(len(frame)),
            "min_time": min_time,
            "max_time": max_time,
        }
    return snapshot


def _normalized_time_bounds(frame: pd.DataFrame) -> tuple[str, str]:
    series = pd.to_datetime(frame["time"], errors="coerce").dropna()
    return (str(series.min()), str(series.max()))


def audit_split_policy(artifacts: AuditArtifacts) -> list[AuditFinding]:
    payload = artifacts.payload
    findings: list[AuditFinding] = []
    roles = payload.get("split_roles")
    if not isinstance(roles, dict):
        findings.append(_error("split_roles_missing", "locked-test JSON is missing split_roles disclosure"))
    else:
        for role in ("train_core", "val_select", "val_eval", "locked_test"):
            if role not in roles:
                findings.append(_error("split_role_missing", f"locked-test JSON is missing split role: {role}"))

    boundaries = payload.get("split_boundaries")
    if not isinstance(boundaries, dict):
        findings.append(_error("split_boundaries_missing", "locked-test JSON is missing split_boundaries disclosure"))

    locked_test_path = _payload_path(payload, "locked_test_path")
    if locked_test_path is None or not locked_test_path.exists():
        findings.append(_error("locked_test_path_missing", "locked-test JSON does not point to an existing locked_test CSV"))
        return findings

    snapshot = _load_split_snapshot(str(locked_test_path.resolve()))
    locked_test = snapshot["locked_test"]
    locked_rows = int(locked_test["row_count"])
    if locked_rows != EXPECTED_LOCKED_TEST_ROWS:
        findings.append(
            _error(
                "locked_test_row_count_invalid",
                f"locked_test must contain {EXPECTED_LOCKED_TEST_ROWS} rows, got {locked_rows}",
            )
        )

    min_time = str(locked_test["min_time"])
    max_time = str(locked_test["max_time"])
    if min_time != EXPECTED_LOCKED_TEST_MIN_TIME or max_time != EXPECTED_LOCKED_TEST_MAX_TIME:
        findings.append(
            _error(
                "locked_test_period_invalid",
                "locked_test period does not match the frozen contract",
            )
        )

    if isinstance(boundaries, dict):
        for role, expected in snapshot.items():
            disclosed = boundaries.get(role)
            if not isinstance(disclosed, dict):
                findings.append(_error("split_boundary_missing", f"split_boundaries is missing {role}"))
                continue
            if int(disclosed.get("row_count", -1)) != int(expected["row_count"]):
                findings.append(_error("split_boundary_row_count_mismatch", f"{role} row_count disclosure mismatch"))
            if str(disclosed.get("min_time")) != str(expected["min_time"]) or str(disclosed.get("max_time")) != str(expected["max_time"]):
                findings.append(_error("split_boundary_time_mismatch", f"{role} time disclosure mismatch"))
    return findings


def _to_float(value: object) -> float:
    return float(pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0])


def _to_int(value: object) -> int:
    return int(pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0])


def _movement_rule_ids(summary: pd.DataFrame) -> list[str]:
    if "profile_id" not in summary.columns or "rule_id" not in summary.columns:
        return []
    mask = summary["profile_id"].astype(str).eq("movement_plus_time")
    return summary.loc[mask, "rule_id"].astype(str).tolist()


def audit_candidate_gates(artifacts: AuditArtifacts) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    summary = artifacts.summary.copy()
    selection = artifacts.selection.copy()
    side = artifacts.side.copy()
    yearly = artifacts.yearly.copy()
    payload = artifacts.payload

    summary_rule_ids = set(summary["rule_id"].astype(str))
    selection_rule_ids = set(selection["rule_id"].astype(str))
    if summary_rule_ids != selection_rule_ids:
        findings.append(_error("summary_selection_rule_mismatch", "summary and selection rule sets differ"))

    bs_method = str(payload.get("bs_p05_method") or "current_iid_trade_bootstrap_despite_block_bootstrap_pf_name")
    if bs_method != "true_block_or_stationary_or_timestamp_cluster_bootstrap":
        findings.append(
            _warning(
                "bs_p05_iid_bootstrap_limitation",
                f"bs_p05 method is diagnostic-only until replaced by a real block bootstrap: {bs_method}",
            )
        )

    if str(payload.get("correlation_pruning_status") or "") != "FOLLOW_UP_REQUIRED":
        findings.append(
            _error(
                "correlation_pruning_status_missing",
                "audit payload must declare correlation_pruning_status=FOLLOW_UP_REQUIRED",
            )
        )

    for row in selection.to_dict(orient="records"):
        rule_id = str(row["rule_id"])
        if _to_float(row["pf"]) < 1.20:
            findings.append(_error("pf_below_threshold", "PF is below 1.20", rule_id=rule_id))
        if _to_float(row["bs_p05"]) < 1.00:
            findings.append(_error("bs_p05_below_threshold", "BS_p05 is below 1.00", rule_id=rule_id))
        if _to_int(row["n_trades"]) < 100:
            findings.append(_error("n_trades_below_threshold", "n_trades is below 100", rule_id=rule_id))

    for rule_id in sorted(selection_rule_ids):
        rule_side = side.loc[side["rule_id"].astype(str).eq(rule_id)].copy()
        present_sides = set(rule_side["side"].astype(str))
        for side_name in ("BUY", "SELL"):
            if side_name not in present_sides:
                findings.append(_error("side_row_missing", f"missing {side_name} side row", rule_id=rule_id))
                continue
            side_row = rule_side.loc[rule_side["side"].astype(str).eq(side_name)].iloc[0]
            if _to_float(side_row["pf"]) < 1.20:
                findings.append(_error("side_pf_below_threshold", f"{side_name} PF is below 1.20", rule_id=rule_id))

    for rule_id in sorted(selection_rule_ids):
        rule_yearly = yearly.loc[yearly["rule_id"].astype(str).eq(rule_id)].copy()
        if rule_yearly.empty:
            findings.append(_error("yearly_rows_missing", "missing yearly rows", rule_id=rule_id))
            continue
        for row in rule_yearly.to_dict(orient="records"):
            if _to_int(row["n_trades"]) < 30:
                findings.append(
                    _error(
                        "yearly_low_n_not_diagnostic",
                        f"year {row['year']} has n_trades < 30 and is not explicitly marked DIAGNOSTIC_ONLY",
                        rule_id=rule_id,
                    )
                )
                continue
            if _to_float(row["pf"]) < 1.20:
                findings.append(_error("yearly_pf_below_threshold", f"year {row['year']} PF is below 1.20", rule_id=rule_id))
            if _to_float(row["gross_loss"]) > 0 and _to_float(row["gross_profit"]) <= 0:
                findings.append(_error("yearly_negative_result", f"year {row['year']} is negative", rule_id=rule_id))

    movement_rules = _movement_rule_ids(summary)
    movement_disclosure = payload.get("movement_score_restoration")
    required_movement_fields = {
        "affected_rule_count",
        "target",
        "profile",
        "model_family",
        "seeds",
        "fit_split",
        "locked_test_label_usage",
        "source_config_hashes",
    }
    movement_disclosure_valid = isinstance(movement_disclosure, dict) and required_movement_fields.issubset(movement_disclosure)
    if movement_rules and not movement_disclosure_valid:
        for rule_id in movement_rules:
            findings.append(
                _error(
                    "movement_score_restoration_missing",
                    "movement_plus_time rule lacks structured movement_score restoration disclosure",
                    rule_id=rule_id,
                )
            )
    elif movement_rules:
        if int(movement_disclosure["affected_rule_count"]) != len(movement_rules):
            findings.append(_error("movement_score_affected_rule_count_mismatch", "movement_score affected_rule_count mismatch"))
        if str(movement_disclosure["fit_split"]) != "train_core":
            findings.append(_error("movement_score_fit_split_invalid", "movement_score fit_split must be train_core"))
        if bool(movement_disclosure["locked_test_label_usage"]):
            findings.append(_error("movement_score_locked_test_label_usage", "locked_test labels must not be used in movement restoration"))
        if movement_disclosure.get("source_config_hashes") == "UNKNOWN":
            for rule_id in movement_rules:
                findings.append(
                    _error(
                        "movement_score_source_hashes_unknown",
                        "movement_plus_time rule has UNKNOWN movement_score source hashes",
                        rule_id=rule_id,
                    )
                )
    return findings


def _findings_to_frame(findings: list[AuditFinding]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "severity": item.severity,
                "check_id": item.check_id,
                "rule_id": item.rule_id,
                "message": item.message,
            }
            for item in findings
        ]
    )


def _build_split_boundaries(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    locked_test_path = _payload_path(payload, "locked_test_path")
    if locked_test_path is None or not locked_test_path.exists():
        return {}
    snapshot = _load_split_snapshot(str(locked_test_path.resolve()))
    return {
        role: {
            "row_count": data["row_count"],
            "min_time": data["min_time"],
            "max_time": data["max_time"],
            "source": "computed_from_local_csv",
        }
        for role, data in snapshot.items()
    }


def run_audit(input_prefix: Path) -> tuple[dict[str, Any], pd.DataFrame]:
    artifacts = load_artifacts(input_prefix)
    contract_findings = validate_artifact_contract(artifacts)
    freeze_findings = audit_pre_open_freeze(artifacts)
    hash_findings = audit_hashes(artifacts)
    split_findings = audit_split_policy(artifacts)
    gate_findings = audit_candidate_gates(artifacts)
    findings = contract_findings + freeze_findings + hash_findings + split_findings + gate_findings

    blocker_checks = {
        item.check_id
        for item in contract_findings + freeze_findings + hash_findings + split_findings
        if item.severity == "ERROR"
    }
    gate_errors = {item.check_id for item in gate_findings if item.severity == "ERROR"}
    if blocker_checks:
        overall_decision = "candidate_audit_blocked"
    elif gate_errors:
        overall_decision = "research_only_downgrade_required"
    else:
        overall_decision = "candidate_audit_passed"

    payload = artifacts.payload
    runner_path = _payload_path(payload, "source_runner")
    result = {
        "input_prefix": str(input_prefix),
        "overall_decision": overall_decision,
        "status": "completed",
        "source_locked_test_verdict": payload.get("verdict"),
        "source_runner_declared_path": payload.get("source_runner"),
        "source_runner_sha256": sha256_file(runner_path) if runner_path and runner_path.exists() else None,
        "rule_count": int(payload.get("rule_count") or len(artifacts.summary)),
        "evaluated_rule_count": int(len(artifacts.summary)),
        "gate_pass_count": int(len(artifacts.selection)),
        "kept_candidates": int(payload.get("kept_candidates") or len(artifacts.selection)),
        "correlation_pruning_status": payload.get("correlation_pruning_status", "MISSING"),
        "bs_p05_method": payload.get("bs_p05_method", "current_iid_trade_bootstrap_despite_block_bootstrap_pf_name"),
        "split_roles": payload.get("split_roles", {}),
        "split_boundaries": _build_split_boundaries(payload),
        "pre_open_freeze_paths": {
            "freeze_json": str(FREEZE_JSON_PATH),
            "selection_policy_json": str(SELECTION_POLICY_JSON_PATH),
        },
        "finding_counts": _findings_to_frame(findings)["severity"].value_counts().to_dict() if findings else {},
        "findings": [
            {"severity": item.severity, "check_id": item.check_id, "rule_id": item.rule_id, "message": item.message}
            for item in findings
        ],
    }
    return result, _findings_to_frame(findings)


def write_audit_outputs(output_prefix: Path, result: dict[str, Any], findings: pd.DataFrame) -> None:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    output_prefix.with_suffix(".json").write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="utf-8")
    findings.to_csv(output_prefix.with_name(f"{output_prefix.name}_findings.csv"), sep=";", index=False)


def build_arg_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--input-prefix", type=Path, required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    result, findings = run_audit(args.input_prefix)
    write_audit_outputs(args.output_prefix, result, findings)
    return 0 if result["overall_decision"] == "candidate_audit_passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
