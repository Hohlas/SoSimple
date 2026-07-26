from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from ML.baseline import audit_fractal0_fixed11_candidate as audit


def _input_prefix() -> Path:
    return Path("ML/reports/fractal0_fixed11_rich_entry_locked_test")


def _clone_artifacts(artifacts: audit.AuditArtifacts, *, payload: dict | None = None) -> audit.AuditArtifacts:
    return audit.AuditArtifacts(
        payload=dict(artifacts.payload if payload is None else payload),
        summary=artifacts.summary.copy(),
        selection=artifacts.selection.copy(),
        yearly=artifacts.yearly.copy(),
        side=artifacts.side.copy(),
        trades=artifacts.trades.copy(),
    )


def test_load_artifacts_reads_locked_test_bundle() -> None:
    artifacts = audit.load_artifacts(_input_prefix())

    assert isinstance(artifacts.payload, dict)
    assert len(artifacts.summary) == 11
    assert len(artifacts.selection) == 11
    assert len(artifacts.yearly) > 0
    assert len(artifacts.side) > 0
    assert len(artifacts.trades) > 0


def test_validate_artifact_contract_accepts_current_bundle() -> None:
    findings = audit.validate_artifact_contract(audit.load_artifacts(_input_prefix()))

    assert findings == []


def test_load_artifacts_rejects_missing_csv(tmp_path: Path) -> None:
    src_prefix = _input_prefix()
    dst_prefix = tmp_path / src_prefix.name
    dst_prefix.with_suffix(".json").write_text(src_prefix.with_suffix(".json").read_text(encoding="utf-8"), encoding="utf-8")
    for suffix in ("_summary.csv", "_selection.csv", "_yearly.csv", "_side.csv"):
        (dst_prefix.parent / f"{dst_prefix.name}{suffix}").write_text(
            (src_prefix.parent / f"{src_prefix.name}{suffix}").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    with pytest.raises(FileNotFoundError, match="trades"):
        audit.load_artifacts(dst_prefix)


def test_validate_artifact_contract_requires_exactly_11_unique_rule_ids(tmp_path: Path) -> None:
    artifacts = audit.load_artifacts(_input_prefix())
    broken_summary = pd.concat([artifacts.summary, artifacts.summary.iloc[[0]]], ignore_index=True)
    broken_summary.loc[11, "rule_id"] = artifacts.summary.iloc[0]["rule_id"]
    broken_selection = artifacts.selection.iloc[:-1].copy()
    broken_selection.loc[:, "rule_id"] = artifacts.selection.iloc[0]["rule_id"]
    broken = audit.AuditArtifacts(
        payload=artifacts.payload,
        summary=broken_summary,
        selection=broken_selection,
        yearly=artifacts.yearly,
        side=artifacts.side,
        trades=artifacts.trades,
    )

    findings = audit.validate_artifact_contract(broken)

    assert {(item.severity, item.check_id) for item in findings} >= {
        ("ERROR", "summary_rule_count_invalid"),
        ("ERROR", "selection_rule_count_invalid"),
    }


def test_audit_pre_open_freeze_reports_missing_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifacts = audit.load_artifacts(_input_prefix())
    monkeypatch.setattr(audit, "FREEZE_JSON_PATH", tmp_path / "missing_freeze.json")
    monkeypatch.setattr(audit, "SELECTION_POLICY_JSON_PATH", tmp_path / "missing_policy.json")

    findings = audit.audit_pre_open_freeze(artifacts)

    assert ("ERROR", "pre_open_freeze_artifact_missing") in {(item.severity, item.check_id) for item in findings}


def test_audit_hashes_reports_hash_mismatch_and_missing_hash(tmp_path: Path) -> None:
    artifacts = audit.load_artifacts(_input_prefix())
    source_rules_copy = tmp_path / "rules.csv"
    source_rules_copy.write_text(Path(artifacts.payload["source_rules_csv"]).read_text(encoding="utf-8"), encoding="utf-8")
    h1_copy = tmp_path / "h1.csv"
    h1_copy.write_text(Path(artifacts.payload["h1_ohlc_path"]).read_text(encoding="utf-8"), encoding="utf-8")

    payload = dict(artifacts.payload)
    payload["source_rules_csv"] = str(source_rules_copy)
    payload["source_rules_csv_sha256"] = "0" * 64
    payload["h1_ohlc_path"] = str(h1_copy)
    payload.pop("h1_ohlc_sha256", None)

    findings = audit.audit_hashes(_clone_artifacts(artifacts, payload=payload))

    assert {(item.severity, item.check_id) for item in findings} >= {
        ("ERROR", "source_rules_csv_hash_mismatch"),
        ("ERROR", "h1_ohlc_sha256_missing"),
        ("WARNING", "source_runner_hash_missing_from_locked_test_json"),
    }


def test_audit_split_policy_reports_missing_roles_and_wrong_locked_test_rows(tmp_path: Path) -> None:
    artifacts = audit.load_artifacts(_input_prefix())
    locked_copy = tmp_path / "locked_test.csv"
    locked_frame = pd.read_csv(artifacts.payload["locked_test_path"], sep=";").iloc[:-1].copy()
    locked_frame.to_csv(locked_copy, sep=";", index=False)

    payload = dict(artifacts.payload)
    payload["locked_test_path"] = str(locked_copy)
    payload["locked_test_sha256"] = audit.sha256_file(locked_copy)
    payload["split_roles"] = {"train_core": "model_training_only", "locked_test": "one_shot_evaluation_only"}
    payload.pop("split_boundaries", None)

    findings = audit.audit_split_policy(_clone_artifacts(artifacts, payload=payload))

    assert {(item.severity, item.check_id) for item in findings} >= {
        ("ERROR", "locked_test_row_count_invalid"),
        ("ERROR", "split_role_missing"),
        ("ERROR", "split_boundaries_missing"),
    }


def test_audit_candidate_gates_reports_core_threshold_failures() -> None:
    artifacts = audit.load_artifacts(_input_prefix())
    broken = _clone_artifacts(artifacts)
    broken.selection.loc[0, "pf"] = 1.19
    broken.selection.loc[1, "bs_p05"] = 0.99
    broken.selection.loc[2, "n_trades"] = 99

    findings = audit.audit_candidate_gates(broken)

    assert {(item.severity, item.check_id) for item in findings} >= {
        ("ERROR", "pf_below_threshold"),
        ("ERROR", "bs_p05_below_threshold"),
        ("ERROR", "n_trades_below_threshold"),
        ("WARNING", "bs_p05_iid_bootstrap_limitation"),
        ("ERROR", "correlation_pruning_status_missing"),
    }


def test_audit_candidate_gates_reports_side_and_yearly_failures() -> None:
    artifacts = audit.load_artifacts(_input_prefix())
    broken = _clone_artifacts(artifacts)
    rule_id = str(broken.selection.iloc[0]["rule_id"])
    broken_side = broken.side.loc[~(
        broken.side["rule_id"].astype(str).eq(rule_id)
        & broken.side["side"].astype(str).eq("SELL")
    )].copy()
    second_rule = str(broken.selection.iloc[1]["rule_id"])
    broken_side.loc[
        broken_side["rule_id"].astype(str).eq(second_rule) & broken_side["side"].astype(str).eq("BUY"),
        "pf",
    ] = 1.10
    third_rule = str(broken.selection.iloc[2]["rule_id"])
    broken_yearly = broken.yearly.copy()
    broken_yearly.loc[
        broken_yearly["rule_id"].astype(str).eq(third_rule) & broken_yearly["year"].eq(2024),
        "pf",
    ] = 1.10
    fourth_rule = str(broken.selection.iloc[3]["rule_id"])
    broken_yearly.loc[
        broken_yearly["rule_id"].astype(str).eq(fourth_rule) & broken_yearly["year"].eq(2024),
        ["gross_profit", "gross_loss"],
    ] = [0.0, 1.0]
    broken = audit.AuditArtifacts(
        payload=broken.payload,
        summary=broken.summary,
        selection=broken.selection,
        yearly=broken_yearly,
        side=broken_side,
        trades=broken.trades,
    )

    findings = audit.audit_candidate_gates(broken)

    assert {(item.severity, item.check_id) for item in findings} >= {
        ("ERROR", "side_row_missing"),
        ("ERROR", "side_pf_below_threshold"),
        ("ERROR", "yearly_pf_below_threshold"),
        ("ERROR", "yearly_negative_result"),
    }


def test_audit_candidate_gates_reports_low_n_year_and_movement_disclosure_failures() -> None:
    artifacts = audit.load_artifacts(_input_prefix())
    payload = dict(artifacts.payload)
    payload["correlation_pruning_status"] = "FOLLOW_UP_REQUIRED"
    payload["movement_score_restoration"] = {
        "affected_rule_count": 4,
        "target": "entry_movement_3",
        "profile": "simple_combined",
        "model_family": "extra_trees_small",
        "seeds": [42, 43, 44],
        "fit_split": "train_core",
        "locked_test_label_usage": False,
        "source_config_hashes": "UNKNOWN",
    }
    broken = _clone_artifacts(artifacts, payload=payload)
    target_rule = str(broken.selection.iloc[0]["rule_id"])
    broken_yearly = broken.yearly.copy()
    broken_yearly.loc[
        broken_yearly["rule_id"].astype(str).eq(target_rule) & broken_yearly["year"].eq(2024),
        "n_trades",
    ] = 12
    broken = audit.AuditArtifacts(
        payload=broken.payload,
        summary=broken.summary,
        selection=broken.selection,
        yearly=broken_yearly,
        side=broken.side,
        trades=broken.trades,
    )

    findings = audit.audit_candidate_gates(broken)

    assert {(item.severity, item.check_id) for item in findings} >= {
        ("ERROR", "yearly_low_n_not_diagnostic"),
        ("ERROR", "movement_score_source_hashes_unknown"),
    }


def test_cli_writes_audit_json_and_findings_csv(tmp_path: Path) -> None:
    output_prefix = tmp_path / "fractal0_fixed11_candidate_audit"

    exit_code = audit.main(
        [
            "--input-prefix",
            str(_input_prefix()),
            "--output-prefix",
            str(output_prefix),
        ]
    )

    assert exit_code == 2
    audit_json = json.loads(output_prefix.with_suffix(".json").read_text(encoding="utf-8"))
    findings_csv = pd.read_csv(output_prefix.with_name(f"{output_prefix.name}_findings.csv"), sep=";")
    assert audit_json["overall_decision"] in {"candidate_audit_blocked", "research_only_downgrade_required"}
    assert audit_json["source_runner_sha256"]
    assert not findings_csv.empty
