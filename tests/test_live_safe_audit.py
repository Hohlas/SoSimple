from ML.live_safe_audit import FeatureTrace, LiveSafeStatus, verdict_from_features


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
