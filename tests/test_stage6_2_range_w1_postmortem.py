import math

import pandas as pd

import ML.baseline.analyze_stage6_2_range_w1_postmortem as pm


def test_bucketize_quantiles_is_stable_with_duplicate_values():
    values = pd.Series([1.0, 1.0, 2.0, 3.0, 4.0, 4.0])

    buckets = pm.bucketize_quantiles(values, n_bins=3)

    assert len(buckets) == 6
    assert buckets.isna().sum() == 0
    assert set(buckets.astype(str)).issubset({"q1", "q2", "q3"})


def test_safe_corr_returns_none_for_constant_input():
    assert pm.safe_corr(pd.Series([1.0, 1.0, 1.0]), pd.Series([0.0, 1.0, 0.0])) is None


def test_safe_corr_returns_float_for_varying_input():
    value = pm.safe_corr(pd.Series([1.0, 2.0, 3.0]), pd.Series([0.0, 0.5, 1.0]))

    assert value is not None
    assert math.isclose(value, 1.0)


def test_summarize_binary_by_bucket_counts_and_rates():
    df = pd.DataFrame({
        "bucket": ["q1", "q1", "q2", "q2"],
        "target": [0, 1, 1, 1],
    })

    rows = pm.summarize_binary_by_bucket(df, "bucket", "target")

    assert rows == [
        {"bucket": "q1", "n": 2, "positive_rate": 0.5},
        {"bucket": "q2", "n": 2, "positive_rate": 1.0},
    ]


def test_summarize_numeric_by_period_uses_calendar_year():
    df = pd.DataFrame({
        "time": ["2021.01.01 00:00", "2021.06.01 00:00", "2022.01.01 00:00"],
        "value": [1.0, 3.0, 5.0],
    })

    rows = pm.summarize_numeric_by_period(df, "value")

    assert rows == [
        {"year": 2021, "n": 2, "mean": 2.0, "median": 2.0},
        {"year": 2022, "n": 1, "mean": 5.0, "median": 5.0},
    ]


def test_build_diagnostic_frame_marks_zero_vector_rows():
    split = {
        "val_stop": pd.DataFrame({
            "time": ["2021.01.01 01:00", "2021.01.01 02:00"],
            "ATR": [2.0, 2.0],
            "stage6_side": ["buy", "sell"],
            "stage6_definitive_tp_vs_sl_flag": [1, 0],
            "stage6_pnl_r": [1.5, -1.0],
        })
    }
    ohlc = pd.DataFrame({
        "time": pd.to_datetime(["2021.01.01 00:00", "2021.01.01 01:00"]),
        "open": [100.0, 101.0],
        "high": [101.0, 103.0],
        "low": [99.0, 100.0],
        "close": [100.0, 102.0],
        "volume": [10.0, 11.0],
        "atr14": [2.0, 2.0],
    })

    frame = pm.build_diagnostic_frame(split, ohlc, "val_stop")

    assert list(frame["split"]) == ["val_stop", "val_stop"]
    assert frame.loc[0, "range_w1_atr"] == 2.0
    assert not bool(frame.loc[0, "price_action_zero_vector"])
    assert bool(frame.loc[1, "price_action_zero_vector"])
    assert frame.loc[1, "range_w1_atr"] == 0.0


def test_build_postmortem_reports_dominance_and_stability_shape():
    report = {
        "summary": {
            "h12_price_action_core": {
                "top_feature_importance": [
                    {"feature": "range_w1_atr", "auc_drop": 0.0525},
                    {"feature": "close_to_low_w1_atr", "auc_drop": 0.0069},
                ],
                "seed_runs": [
                    {
                        "seed": 42,
                        "val_auc": 0.6233,
                        "permutation_p_value": 0.160,
                        "threshold": 0.700,
                        "pf": 1.307,
                    },
                    {
                        "seed": 77,
                        "val_auc": 0.6213,
                        "permutation_p_value": 0.350,
                        "threshold": 0.725,
                        "pf": 1.180,
                    },
                    {
                        "seed": 123,
                        "val_auc": 0.6238,
                        "permutation_p_value": 0.155,
                        "threshold": 0.725,
                        "pf": 1.359,
                    },
                ],
                "permutation_baseline": {
                    "empirical_p_value": 0.16,
                    "observed_pf_median": 1.307,
                    "per_seed": [
                        {
                            "seed": 42,
                            "observed_pf": 1.307,
                            "permuted_pf_median": 1.100,
                            "permuted_pf_p95": 1.420,
                        },
                        {
                            "seed": 77,
                            "observed_pf": 1.180,
                            "permuted_pf_median": 1.080,
                            "permuted_pf_p95": 1.390,
                        },
                        {
                            "seed": 123,
                            "observed_pf": 1.359,
                            "permuted_pf_median": 1.120,
                            "permuted_pf_p95": 1.460,
                        },
                    ],
                },
            }
        },
        "gate": {"status": "TRADING_GATE_FAILED"},
    }
    frame = pd.DataFrame({
        "time": ["2021.01.01 00:00", "2021.01.01 01:00", "2022.01.01 00:00"],
        "stage6_side": ["buy", "buy", "sell"],
        "stage6_definitive_tp_vs_sl_flag": [0, 1, 1],
        "stage6_pnl_r": [-1.0, 2.0, 1.5],
        "range_w1_atr": [0.5, 2.0, 3.0],
        "range_w1_bucket": ["q1", "q2", "q3"],
        "bar_range_1_atr": [0.5, 2.0, 3.0],
        "ATR": [1.0, 2.0, 3.0],
        "y_score_core_seed42": [0.65, 0.72, 0.80],
        "price_action_zero_vector": [False, False, False],
    })

    result = pm.build_postmortem(report, {"val_stop": frame})

    assert result["source_stage62_status"] == "TRADING_GATE_FAILED"
    assert result["artifact_consistency"]["primary_p_value"] == 0.16
    assert result["dominance"]["top_feature"] == "range_w1_atr"
    assert result["dominance"]["top_to_second_auc_drop_ratio"] > 1.0
    assert result["stability"]["seed_count"] == 3
    assert result["selected_trade_analysis"]["seed_count"] == 3
    assert result["selected_trade_analysis"]["per_seed"][0]["selected_known_n"] == 2
    assert result["selected_trade_analysis"]["per_seed"][0]["tp_rate_denominator"] == (
        "known_stage6_definitive_tp_vs_sl_flag_rows"
    )
    assert result["side_analysis"][0]["side"] in {"buy", "sell"}
    assert result["year_side_matrix"][0]["year"] in {2021, 2022}
    assert "range_w1_vs_bar_range_1_corr" in result["activity_proxy_checks"]
    assert result["permutation_context"]["primary_p_value"] == 0.16
    assert result["evidence_strength"] in {
        "weak",
        "insufficient",
        "artifact_suspected",
        "not_artifact_detected",
    }
    assert result["verdict"]["artifact_status"] == "DIAGNOSTIC_ONLY"
