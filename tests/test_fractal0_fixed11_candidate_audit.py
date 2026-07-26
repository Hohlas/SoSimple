import json
from pathlib import Path

import pandas as pd
import pytest

from ML.baseline.audit_fractal0_fixed11_candidate import (
    AuditArtifacts,
    audit_candidate_gates,
    audit_hashes,
    audit_pre_open_freeze,
    audit_split_policy,
    build_split_boundaries,
    load_artifacts,
    main,
    run_audit,
    validate_forensic_evidence,
    validate_artifact_contract,
)


def _write_csv(path: Path, rows: list[dict]) -> None:
    pd.DataFrame(rows).to_csv(path, sep=";", index=False)


def _minimal_payload(tmp_path: Path, rule_ids: list[str]) -> dict:
    source = tmp_path / "source.csv"
    source.write_text("a\n1\n", encoding="utf-8")
    digest = __import__("hashlib").sha256(source.read_bytes()).hexdigest()
    return {
        "rule_count": 11,
        "evaluated_rule_count": 11,
        "gate_pass_count": 11,
        "kept_candidates": 11,
        "source_rules_csv": str(source),
        "source_rules_csv_sha256": digest,
        "source_artifact": str(source),
        "source_artifact_sha256": digest,
        "locked_test_path": str(source),
        "locked_test_sha256": digest,
        "execution_ohlc_path": str(source),
        "execution_ohlc_sha256": digest,
        "h1_ohlc_path": str(source),
        "h1_ohlc_sha256": digest,
        "source_runner": str(source),
        "split_roles": {
            "train_core": {"row_count": 1000, "min_time": "2016-01-01", "max_time": "2020-12-31"},
            "val_select": {"row_count": 1000, "min_time": "2021-01-01", "max_time": "2021-06-30"},
            "val_eval": {"row_count": 1000, "min_time": "2021-07-01", "max_time": "2022-12-01"},
            "locked_test": {"row_count": 9463, "min_time": "2022-12-02", "max_time": "2026-06-04"},
        },
        "locked_test_not_used_for_selection": True,
        "correlation_pruning_status": "FOLLOW_UP_REQUIRED",
        "movement_score_restoration": {
            "affected_rule_count": 4,
            "target": "target_entry_ev_regression",
            "profile": "movement_plus_time",
            "model_family": "linear",
            "seeds": [0],
            "fit_split": "train_core",
            "locked_test_label_usage": "none",
            "scaler_fit_split": "train_core",
            "source_config_sha256": "abc",
        },
        "rule_ids": rule_ids,
    }


def _artifact_dir(tmp_path: Path, rule_ids: list[str] | None = None) -> Path:
    rule_ids = rule_ids or [f"rule_{i:02d}" for i in range(11)]
    prefix = tmp_path / "locked"
    (tmp_path / "locked.json").write_text(json.dumps(_minimal_payload(tmp_path, rule_ids)), encoding="utf-8")
    summary_rows = [
        {
            "rule_id": rule_id,
            "original_rank": i + 1,
            "pf": 1.25,
            "bs_p05": 1.05,
            "n_trades": 120,
            "profile_id": "time_only",
            "status": "OK",
        }
        for i, rule_id in enumerate(rule_ids)
    ]
    _write_csv(tmp_path / "locked_summary.csv", summary_rows)
    _write_csv(tmp_path / "locked_selection.csv", [dict(row, decision="KEEP_CANDIDATE") for row in summary_rows])
    _write_csv(
        tmp_path / "locked_yearly.csv",
        [
            {"rule_id": rule_id, "year": 2023, "n_trades": 40, "pf": 1.25, "year_status": "PASS"}
            for rule_id in rule_ids
        ],
    )
    _write_csv(
        tmp_path / "locked_side.csv",
        [
            {"rule_id": rule_id, "side": side, "n_trades": 60, "pf": 1.25}
            for rule_id in rule_ids
            for side in ("BUY", "SELL")
        ],
    )
    _write_csv(tmp_path / "locked_trades.csv", [{"rule_id": rule_ids[0], "pnl_r": 1.0}])
    return prefix


def _findings_by_id(findings):
    return {finding.check_id: finding for finding in findings}


def test_load_artifacts_reads_json_and_all_csv_files(tmp_path: Path) -> None:
    prefix = _artifact_dir(tmp_path)
    artifacts = load_artifacts(prefix)

    assert isinstance(artifacts, AuditArtifacts)
    assert len(artifacts.summary) == 11
    assert len(artifacts.selection) == 11
    assert not artifacts.yearly.empty
    assert not artifacts.side.empty
    assert not artifacts.trades.empty


def test_load_artifacts_rejects_missing_files(tmp_path: Path) -> None:
    prefix = _artifact_dir(tmp_path)
    (tmp_path / "locked_side.csv").unlink()

    with pytest.raises(FileNotFoundError):
        load_artifacts(prefix)


def test_validate_artifact_contract_requires_11_unique_rule_ids(tmp_path: Path) -> None:
    prefix = _artifact_dir(tmp_path, ["same_rule"] * 11)
    findings = validate_artifact_contract(load_artifacts(prefix))

    assert _findings_by_id(findings)["rule_id_count_mismatch"].severity == "ERROR"


def test_audit_pre_open_freeze_requires_freeze_and_policy(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    prefix = _artifact_dir(tmp_path)

    findings = audit_pre_open_freeze(load_artifacts(prefix))

    assert _findings_by_id(findings)["pre_open_freeze_artifact_missing"].severity == "ERROR"


def test_audit_pre_open_freeze_accepts_forensic_report_evidence(tmp_path: Path) -> None:
    prefix = _artifact_dir(tmp_path)
    artifacts = load_artifacts(prefix)
    artifacts.payload["forensic_evidence"] = {
        "locked_test_report": True,
        "protocol_plan": True,
        "source_rules_csv_committed_before_locked_test": True,
        "locked_test_no_new_selection_reported": True,
    }

    findings = audit_pre_open_freeze(artifacts)

    assert _findings_by_id(findings)["pre_open_freeze_machine_artifact_missing"].severity == "WARNING"
    assert "pre_open_freeze_artifact_missing" not in _findings_by_id(findings)


def test_audit_pre_open_freeze_requires_rule_hash(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "ML" / "reports"
    reports.mkdir(parents=True)
    (reports / "fractal0_fixed11_locked_test_freeze.json").write_text("{}", encoding="utf-8")
    (reports / "fractal0_fixed11_locked_test_selection_policy.json").write_text(
        json.dumps({"rule_hash_sha256": "abc"}), encoding="utf-8"
    )
    prefix = _artifact_dir(tmp_path)

    findings = audit_pre_open_freeze(load_artifacts(prefix))

    assert _findings_by_id(findings)["pre_open_freeze_rule_hash_missing"].severity == "ERROR"


def test_audit_hashes_detects_changed_sha_and_missing_hash(tmp_path: Path) -> None:
    prefix = _artifact_dir(tmp_path)
    artifacts = load_artifacts(prefix)
    artifacts.payload["source_rules_csv_sha256"] = "bad"
    artifacts.payload.pop("source_artifact_sha256")

    findings = _findings_by_id(audit_hashes(artifacts))

    assert findings["source_hash_mismatch"].severity == "ERROR"
    assert findings["source_hash_missing"].severity == "ERROR"


def test_audit_split_policy_requires_locked_period_rows_and_validation_roles(tmp_path: Path) -> None:
    prefix = _artifact_dir(tmp_path)
    artifacts = load_artifacts(prefix)
    artifacts.payload["split_roles"].pop("val_select")
    artifacts.payload["split_roles"].pop("val_eval")
    artifacts.payload["split_roles"]["locked_test"]["row_count"] = 1
    artifacts.payload["split_roles"]["locked_test"]["min_time"] = "2020-01-01"
    artifacts.payload.pop("locked_test_not_used_for_selection")

    findings = _findings_by_id(audit_split_policy(artifacts))

    assert findings["split_role_missing"].severity == "ERROR"
    assert findings["locked_test_row_count_mismatch"].severity == "ERROR"
    assert findings["locked_test_period_mismatch"].severity == "ERROR"
    assert findings["locked_test_selection_disclosure_missing"].severity == "ERROR"


def test_audit_split_policy_requires_split_disclosure(tmp_path: Path) -> None:
    prefix = _artifact_dir(tmp_path)
    artifacts = load_artifacts(prefix)
    artifacts.payload.pop("split_roles")

    findings = audit_split_policy(artifacts)

    assert findings[0].check_id == "split_disclosure_missing"
    assert findings[0].severity == "ERROR"


def test_audit_split_policy_rejects_non_mapping_role_details(tmp_path: Path) -> None:
    prefix = _artifact_dir(tmp_path)
    artifacts = load_artifacts(prefix)
    artifacts.payload["split_roles"]["locked_test"] = "one_shot_evaluation_only"

    findings = _findings_by_id(audit_split_policy(artifacts))

    assert findings["split_role_detail_missing"].severity == "ERROR"


def test_audit_split_policy_accepts_computed_forensic_boundaries(tmp_path: Path) -> None:
    prefix = _artifact_dir(tmp_path)
    artifacts = load_artifacts(prefix)
    artifacts.payload["split_roles"] = {"train_core": "model_training_only", "locked_test": "one_shot_evaluation_only"}
    artifacts.payload["forensic_evidence"] = {
        "computed_split_boundaries": {
            "train_core": {"row_count": 1000, "min_time": "2016-01-01", "max_time": "2020-12-31"},
            "val_select": {"row_count": 1000, "min_time": "2021-01-01", "max_time": "2021-06-30"},
            "val_eval": {"row_count": 1000, "min_time": "2021-07-01", "max_time": "2022-12-01"},
            "locked_test": {"row_count": 9463, "min_time": "2022-12-02", "max_time": "2026-06-04"},
        },
        "locked_test_no_new_selection_reported": True,
    }

    findings = _findings_by_id(audit_split_policy(artifacts))

    assert findings["split_disclosure_reconstructed_from_forensic_evidence"].severity == "WARNING"
    assert "split_role_missing" not in findings
    assert "locked_test_row_count_mismatch" not in findings


def test_audit_candidate_gates_detects_pf_bs_and_trade_failures(tmp_path: Path) -> None:
    prefix = _artifact_dir(tmp_path)
    artifacts = load_artifacts(prefix)
    artifacts.summary.loc[0, "pf"] = 1.19
    artifacts.summary.loc[1, "bs_p05"] = 0.99
    artifacts.summary.loc[2, "n_trades"] = 99

    findings = _findings_by_id(audit_candidate_gates(artifacts))

    assert findings["pf_below_gate"].severity == "ERROR"
    assert findings["bs_p05_below_gate"].severity == "ERROR"
    assert findings["trade_count_below_gate"].severity == "ERROR"
    assert findings["bs_p05_iid_bootstrap_limitation"].severity == "WARNING"


def test_audit_candidate_gates_accepts_forensic_correlation_followup(tmp_path: Path) -> None:
    prefix = _artifact_dir(tmp_path)
    artifacts = load_artifacts(prefix)
    artifacts.payload.pop("correlation_pruning_status")
    artifacts.payload["forensic_evidence"] = {"correlation_pruning_followup_reported": True}

    findings = _findings_by_id(audit_candidate_gates(artifacts))

    assert findings["correlation_pruning_status_reconstructed_from_report"].severity == "WARNING"
    assert "correlation_pruning_status_invalid" not in findings


def test_audit_candidate_gates_detects_side_and_yearly_failures(tmp_path: Path) -> None:
    prefix = _artifact_dir(tmp_path)
    artifacts = load_artifacts(prefix)
    rule_id = artifacts.summary.loc[0, "rule_id"]
    object.__setattr__(
        artifacts,
        "side",
        artifacts.side[~((artifacts.side["rule_id"] == rule_id) & (artifacts.side["side"] == "SELL"))],
    )
    artifacts.side.loc[artifacts.side["rule_id"] == rule_id, "pf"] = 1.19
    artifacts.yearly.loc[artifacts.yearly["rule_id"] == rule_id, "pf"] = 1.19

    findings = _findings_by_id(audit_candidate_gates(artifacts))

    assert findings["side_coverage_missing"].severity == "ERROR"
    assert findings["side_pf_below_gate"].severity == "ERROR"
    assert findings["yearly_pf_below_gate"].severity == "ERROR"


def test_audit_candidate_gates_requires_low_n_year_classification(tmp_path: Path) -> None:
    prefix = _artifact_dir(tmp_path)
    artifacts = load_artifacts(prefix)
    artifacts.yearly.loc[0, "n_trades"] = 29
    artifacts.yearly.loc[0, "year_status"] = "PASS"

    findings = _findings_by_id(audit_candidate_gates(artifacts))

    assert findings["yearly_low_n_unclassified"].severity == "ERROR"


def test_audit_candidate_gates_marks_low_n_edge_year_as_diagnostic_when_period_known(tmp_path: Path) -> None:
    prefix = _artifact_dir(tmp_path)
    artifacts = load_artifacts(prefix)
    artifacts.yearly.loc[0, "year"] = 2022
    artifacts.yearly.loc[0, "n_trades"] = 29
    artifacts.payload["forensic_evidence"] = {
        "computed_split_boundaries": {
            "locked_test": {"min_time": "2022-12-02 11:00:00", "max_time": "2026-06-04 12:00:00"}
        }
    }

    findings = _findings_by_id(audit_candidate_gates(artifacts))

    assert findings["yearly_low_n_edge_year_diagnostic"].severity == "WARNING"
    assert "yearly_low_n_unclassified" not in findings


def test_audit_candidate_gates_allows_diagnostic_edge_year_low_n(tmp_path: Path) -> None:
    prefix = _artifact_dir(tmp_path)
    artifacts = load_artifacts(prefix)
    artifacts.yearly.loc[0, "n_trades"] = 29
    artifacts.yearly.loc[0, "year_status"] = "DIAGNOSTIC_ONLY"

    check_ids = {finding.check_id for finding in audit_candidate_gates(artifacts)}

    assert "yearly_low_n_unclassified" not in check_ids


def test_audit_candidate_gates_requires_movement_score_disclosure(tmp_path: Path) -> None:
    ids = [f"rule_{i:02d}" for i in range(10)] + ["rank11_movement_plus_time_linear_target_top30"]
    prefix = _artifact_dir(tmp_path, ids)
    artifacts = load_artifacts(prefix)
    artifacts.payload["movement_score_restoration"] = {
        "affected_rule_count": 4,
        "target": "UNKNOWN",
        "profile": "movement_plus_time",
        "model_family": "linear",
        "seeds": [0],
        "fit_split": "train_core",
        "locked_test_label_usage": "none",
        "scaler_fit_split": "train_core",
    }

    findings = _findings_by_id(audit_candidate_gates(artifacts))

    assert findings["movement_score_restoration_disclosure_missing"].severity == "ERROR"
    assert findings["movement_score_source_hash_unknown"].severity == "WARNING"


def test_audit_candidate_gates_accepts_reported_movement_score_protocol(tmp_path: Path) -> None:
    ids = [f"rule_{i:02d}" for i in range(10)] + ["rank11_movement_plus_time_linear_target_top30"]
    prefix = _artifact_dir(tmp_path, ids)
    artifacts = load_artifacts(prefix)
    artifacts.payload["movement_score_restoration"] = {
        "affected_rule_count": 1,
        "target": "entry_movement_3",
        "profile": "simple_combined",
        "model_family": "extra_trees_small",
        "seeds": [42, 43, 44],
        "fit_split": "train_core",
        "locked_test_label_usage": "none",
        "scaler_fit_split": "train_core",
        "source_config_sha256": "abc",
    }

    findings = _findings_by_id(audit_candidate_gates(artifacts))

    assert "movement_score_restoration_disclosure_missing" not in findings


def test_validate_forensic_evidence_reads_project_reports() -> None:
    evidence = validate_forensic_evidence(
        Path("ML/reports/fractal0_fixed11_rich_entry_locked_test"),
        load_artifacts(Path("ML/reports/fractal0_fixed11_rich_entry_locked_test")),
    )

    assert evidence["locked_test_report"] is True
    assert evidence["protocol_plan"] is True
    assert evidence["locked_test_no_new_selection_reported"] is True
    assert sorted(evidence["computed_split_boundaries"]) == ["locked_test", "train_core", "val_eval", "val_select"]


def test_cli_writes_audit_json_and_findings_csv(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "ML" / "reports"
    reports.mkdir(parents=True)
    (reports / "fractal0_fixed11_locked_test_freeze.json").write_text(
        json.dumps({"rule_hash_sha256": "abc"}), encoding="utf-8"
    )
    (reports / "fractal0_fixed11_locked_test_selection_policy.json").write_text(
        json.dumps({"rule_hash_sha256": "abc"}), encoding="utf-8"
    )
    prefix = _artifact_dir(tmp_path)
    output_prefix = tmp_path / "audit"

    exit_code = main(["--input-prefix", str(prefix), "--output-prefix", str(output_prefix)])

    assert exit_code == 0
    payload = json.loads((tmp_path / "audit.json").read_text(encoding="utf-8"))
    findings = pd.read_csv(tmp_path / "audit_findings.csv", sep=";")
    assert payload["overall_decision"] in {"candidate_audit_passed", "candidate_audit_blocked"}
    assert payload["finding_counts"]["WARNING"] == 2
    assert {finding["check_id"] for finding in payload["findings"]} >= {
        "source_runner_hash_missing_from_locked_test_json",
        "bs_p05_iid_bootstrap_limitation",
    }
    assert not findings.empty


def test_run_audit_records_full_structured_context(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "ML" / "reports"
    reports.mkdir(parents=True)
    (reports / "fractal0_fixed11_locked_test_freeze.json").write_text(
        json.dumps({"rule_hash_sha256": "abc"}), encoding="utf-8"
    )
    (reports / "fractal0_fixed11_locked_test_selection_policy.json").write_text(
        json.dumps({"rule_hash_sha256": "abc"}), encoding="utf-8"
    )
    prefix = _artifact_dir(tmp_path)

    result, findings = run_audit(prefix)

    assert result["input_prefix"] == str(prefix)
    assert result["status"] == "completed"
    assert result["rule_count"] == 11
    assert result["evaluated_rule_count"] == 11
    assert result["gate_pass_count"] == 11
    assert result["kept_candidates"] == 11
    assert result["finding_counts"] == {"WARNING": 2}
    assert result["findings"] == [
        {
            "severity": finding.severity,
            "check_id": finding.check_id,
            "message": finding.message,
            "rule_id": finding.rule_id,
        }
        for finding in findings
    ]


def test_build_split_boundaries_computes_locked_test_rows_from_csv(tmp_path: Path) -> None:
    prefix = _artifact_dir(tmp_path)
    artifacts = load_artifacts(prefix)
    locked_test = tmp_path / "locked_source.csv"
    pd.DataFrame(
        {
            "time": ["2022-12-02 11:00:00", "2026-06-04 12:00:00"],
            "value": [1, 2],
        }
    ).to_csv(locked_test, sep=";", index=False)
    artifacts.payload["locked_test_path"] = str(locked_test)

    boundaries = build_split_boundaries(artifacts)

    assert boundaries["locked_test"] == {
        "row_count": 2,
        "min_time": "2022-12-02 11:00:00",
        "max_time": "2026-06-04 12:00:00",
        "source": "computed_from_local_csv",
    }
