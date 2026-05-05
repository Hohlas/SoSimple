from ML.live_safe_audit import FeatureTrace, LiveSafeStatus, verdict_from_features
from ML.live_safe_audit_registry import get_audited_systems
from ML.run_live_safe_ml_audit import build_artifact_inventory


def test_unknown_feature_blocks_online_pass():
    features = [
        FeatureTrace(name="session_hour", live_safe_status=LiveSafeStatus.PASS),
        FeatureTrace(name="ret_dir_atr_lag1", live_safe_status=LiveSafeStatus.UNKNOWN),
    ]

    assert verdict_from_features(features).verdict == "UNKNOWN"


def test_future_feature_fails_live_safe_audit():
    features = [
        FeatureTrace(name="predict", live_safe_status=LiveSafeStatus.FAIL),
    ]

    assert verdict_from_features(features).verdict == "FAIL"


def test_audit_registry_contains_expected_systems():
    systems = get_audited_systems()

    assert [system.system_name for system in systems] == [
        "quality",
        "frequency",
        "original_plus_path",
        "entry_path_v1",
        "entry_path_v1_quantile",
    ]


def test_audit_registry_entries_have_required_fields():
    for system in get_audited_systems():
        assert system.system_name
        assert system.prediction_paths is not None
        assert system.report_paths
        assert system.expected_risk_note
        assert system.checkpoint_path or system.rule_path


def test_artifact_inventory_reports_existing_and_missing_paths(tmp_path):
    existing = tmp_path / "rule.json"
    existing.write_text("{}", encoding="utf-8")
    missing = tmp_path / "missing.pt"
    system = get_audited_systems()[0]
    patched = type(system)(
        system_name=system.system_name,
        checkpoint_path=str(missing),
        rule_path=str(existing),
        prediction_paths=(),
        report_paths=(),
        expected_risk_note=system.expected_risk_note,
    )

    inventory = build_artifact_inventory(patched)

    assert inventory["system_name"] == "quality"
    assert str(existing) in inventory["existing_paths"]
    assert str(missing) in inventory["missing_paths"]
    assert inventory["checkpoint_path"] == str(missing)
    assert inventory["rule_path"] == str(existing)
    assert inventory["prediction_paths"] == []
    assert inventory["report_paths"] == []
