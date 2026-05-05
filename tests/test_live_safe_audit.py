from ML.live_safe_audit import FeatureTrace, LiveSafeStatus, classify_feature_name, verdict_from_features
from ML.live_safe_audit_registry import get_audited_systems
from ML.run_live_safe_ml_audit import (
    build_artifact_inventory,
    build_feature_contract,
    build_legacy_reproduction,
    build_system_verdict,
)


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


def test_known_future_derived_features_are_classified_as_fail():
    for name in ("predict", "ret_6_dir_atr", "ret_12_dir_atr", "ret_24_dir_atr", "fav_6_atr", "adv_24_atr"):
        trace = classify_feature_name(name)
        assert trace.live_safe_status == LiveSafeStatus.FAIL


def test_ret_dir_atr_lag1_stays_unknown_until_source_timing_is_proven():
    trace = classify_feature_name("ret_dir_atr_lag1")

    assert trace.live_safe_status == LiveSafeStatus.UNKNOWN
    assert "shift" in trace.transformation


def test_current_bar_features_are_classified_as_pass():
    for name in ("session_hour", "weekday", "ATR"):
        assert classify_feature_name(name).live_safe_status == LiveSafeStatus.PASS


def test_feature_contract_for_original_plus_path_contains_forbidden_inputs():
    system = next(system for system in get_audited_systems() if system.system_name == "original_plus_path")

    traces = build_feature_contract(system)
    by_name = {trace.name: trace for trace in traces}

    assert by_name["predict"].live_safe_status == LiveSafeStatus.FAIL
    assert by_name["ret_dir_atr_lag1"].live_safe_status == LiveSafeStatus.UNKNOWN


def test_initial_system_verdicts_match_expected_risk_model():
    verdicts = {system.system_name: build_system_verdict(system)["verdict"] for system in get_audited_systems()}

    assert verdicts == {
        "quality": "FAIL",
        "frequency": "FAIL",
        "original_plus_path": "FAIL",
        "entry_path_v1": "UNKNOWN",
        "entry_path_v1_quantile": "UNKNOWN",
    }


def test_legacy_reproduction_reads_frozen_rule_metrics_without_retraining():
    system = next(system for system in get_audited_systems() if system.system_name == "quality")

    legacy = build_legacy_reproduction(system)

    assert legacy["system_name"] == "quality"
    assert legacy["reproduction_mode"] == "artifact_only"
    assert legacy["frozen_test"]["pf"] == 39.7420751708579
    assert legacy["model_changed"] is False
