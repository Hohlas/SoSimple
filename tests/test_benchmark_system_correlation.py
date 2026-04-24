import json
import textwrap

import pandas as pd
import pytest

from ML import benchmark_system_correlation as correlation


def _write_json(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_csv(path, content):
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def test_normalize_trade_frame_accepts_trade_csv_and_entry_path_predictions(tmp_path):
    trade_csv = tmp_path / "trades.csv"
    _write_csv(
        trade_csv,
        """
        dataset_name,system_name,signal_time,entry_time,exit_time,signal,policy,entry,exit,entry_atr,exit_atr,pnl_price,pnl_atr,max_profit_atr,max_adverse_atr,hold_hours,exit_reason
        xauusd_metaquotes,quality,2025-01-01 00:00:00,2025-01-01 01:00:00,2025-01-01 03:00:00,1,trail_x8_tp12,100,104,1,1,4,4,5,1,2,hold_timeout
        """,
    )
    quality_spec = {
        "system_name": "quality",
        "instrument": "XAUUSD",
        "provider": "MetaQuotes",
        "source_type": "trade_csv",
        "trade_csv": str(trade_csv),
        "dataset_name": "xauusd_metaquotes",
        "policy_name": "trail_x8_tp12",
    }

    quality = correlation.load_trade_frame(quality_spec)

    assert list(quality.columns) == correlation.NORMALIZED_TRADE_COLUMNS
    assert quality.iloc[0]["system_name"] == "quality"
    assert quality.iloc[0]["instrument"] == "XAUUSD"
    assert quality.iloc[0]["provider"] == "MetaQuotes"
    assert quality.iloc[0]["direction"] == 1
    assert quality.iloc[0]["pnl_atr"] == 4.0
    assert quality.iloc[0]["holding_bars"] == 2

    ohlc_csv = tmp_path / "ohlc.csv"
    _write_csv(
        ohlc_csv,
        """
        time;open;high;low;close;atr14
        2025.01.01 00:00;100;100;100;100;1
        2025.01.01 01:00;100;100;100;100;1
        2025.01.01 02:00;100;102;99;101;1
        2025.01.01 03:00;101;104;100;103;1
        """,
    )
    predictions_csv = tmp_path / "entry_path_v1_test_predictions.csv"
    _write_csv(
        predictions_csv,
        """
        time;signal;pred_ret_24_dir_atr
        2025.01.01 00:00;1;2.0
        2025.01.01 01:00;0;0.0
        """,
    )
    rule_json = tmp_path / "entry_path_rule.json"
    _write_json(
        rule_json,
        {
            "winner": {
                "candidate": "A",
                "score_threshold": 1.0,
            }
        },
    )

    entry_path_spec = {
        "system_name": "entry_path_v1",
        "instrument": "XAUUSD",
        "provider": "MetaQuotes",
        "source_type": "entry_path_predictions",
        "prediction_csv": str(predictions_csv),
        "ohlc_csv": str(ohlc_csv),
        "entry_path_kind": "entry_path_v1",
        "rule_path": str(rule_json),
        "policy_name": "hold_2_backstop_50",
        "hold_bars": 2,
    }

    entry_path = correlation.load_trade_frame(entry_path_spec)

    assert list(entry_path.columns) == correlation.NORMALIZED_TRADE_COLUMNS
    assert entry_path.iloc[0]["system_name"] == "entry_path_v1"
    assert entry_path.iloc[0]["direction"] == 1
    assert entry_path.iloc[0]["pnl_atr"] == 1.0
    assert entry_path.iloc[0]["holding_bars"] == 1


def test_validate_trade_frame_rejects_missing_required_columns():
    frame = pd.DataFrame(
        {
            "system_name": ["quality"],
            "instrument": ["XAUUSD"],
            "provider": ["MetaQuotes"],
            "entry_time": [pd.Timestamp("2025-01-01 00:00:00")],
            "direction": [1],
            "pnl_atr": [1.0],
            "holding_bars": [1],
        }
    )

    with pytest.raises(ValueError, match="missing required trade columns"):
        correlation.validate_trade_frame(frame)


def test_load_manifest_rejects_mixed_instrument_systems(tmp_path):
    _write_csv(tmp_path / "quality.csv", "entry_time,exit_time,direction,pnl_atr,holding_bars\n2025-01-01,2025-01-02,1,1.0,1")
    _write_csv(tmp_path / "frequency.csv", "entry_time,exit_time,direction,pnl_atr,holding_bars\n2025-01-01,2025-01-02,1,1.0,1")
    manifest_path = tmp_path / "manifest.json"
    _write_json(
        manifest_path,
        {
            "systems": [
                {
                    "system_name": "quality",
                    "instrument": "XAUUSD",
                    "provider": "MetaQuotes",
                    "source_type": "trade_csv",
                    "trade_csv": str(tmp_path / "quality.csv"),
                },
                {
                    "system_name": "frequency",
                    "instrument": "USDCHF",
                    "provider": "MetaQuotes",
                    "source_type": "trade_csv",
                    "trade_csv": str(tmp_path / "frequency.csv"),
                },
            ]
        },
    )

    with pytest.raises(ValueError, match="single instrument"):
        correlation.load_manifest(manifest_path)


def test_pair_metrics_detect_redundant_and_sparse_pairs():
    identical_a = pd.DataFrame(
        {
            "system_name": ["quality", "quality"],
            "instrument": ["XAUUSD", "XAUUSD"],
            "provider": ["MetaQuotes", "MetaQuotes"],
            "entry_time": pd.to_datetime(["2025-01-01 00:00:00", "2025-01-02 00:00:00"]),
            "exit_time": pd.to_datetime(["2025-01-01 12:00:00", "2025-01-02 12:00:00"]),
            "direction": [1, -1],
            "pnl_atr": [2.0, -1.0],
            "holding_bars": [12, 12],
        }
    )
    identical_b = identical_a.assign(system_name="frequency")

    redundant = correlation.compute_pair_metrics(identical_a, identical_b)

    assert redundant["trade_overlap_ratio"] == 1.0
    assert redundant["entry_time_jaccard"] == 1.0
    assert redundant["same_direction_ratio"] == 1.0
    assert redundant["trade_pnl_corr"] == 1.0
    assert redundant["daily_pnl_corr"] == 1.0
    assert redundant["weekly_pnl_corr"] == 1.0
    assert redundant["drawdown_overlap_ratio"] == 1.0
    assert redundant["co_loss_ratio"] == 1.0
    assert redundant["portfolio_verdict"] == "portfolio_redundant"

    sparse_a = pd.DataFrame(
        {
            "system_name": ["quality", "quality"],
            "instrument": ["XAUUSD", "XAUUSD"],
            "provider": ["MetaQuotes", "MetaQuotes"],
            "entry_time": pd.to_datetime(["2025-01-01 00:00:00", "2025-01-03 00:00:00"]),
            "exit_time": pd.to_datetime(["2025-01-01 12:00:00", "2025-01-03 12:00:00"]),
            "direction": [1, 1],
            "pnl_atr": [2.0, 3.0],
            "holding_bars": [12, 12],
        }
    )
    sparse_b = pd.DataFrame(
        {
            "system_name": ["entry_path_v1", "entry_path_v1"],
            "instrument": ["XAUUSD", "XAUUSD"],
            "provider": ["MetaQuotes", "MetaQuotes"],
            "entry_time": pd.to_datetime(["2025-01-02 00:00:00", "2025-01-04 00:00:00"]),
            "exit_time": pd.to_datetime(["2025-01-02 12:00:00", "2025-01-04 12:00:00"]),
            "direction": [-1, -1],
            "pnl_atr": [1.5, 2.5],
            "holding_bars": [12, 12],
        }
    )

    complementary = correlation.compute_pair_metrics(sparse_a, sparse_b)

    assert complementary["trade_overlap_ratio"] == 0.0
    assert complementary["entry_time_jaccard"] == 0.0
    assert complementary["same_direction_ratio"] == 0.0
    assert complementary["trade_pnl_corr"] == 0.0
    assert complementary["drawdown_overlap_ratio"] == 0.0
    assert complementary["co_loss_ratio"] == 0.0
    assert complementary["staggered_gain_ratio"] == 1.0
    assert complementary["portfolio_verdict"] == "portfolio_complementary"


def test_same_timestamp_opposite_direction_reduces_direction_agreement():
    left = pd.DataFrame(
        {
            "system_name": ["quality"],
            "instrument": ["XAUUSD"],
            "provider": ["MetaQuotes"],
            "entry_time": pd.to_datetime(["2025-01-01 00:00:00"]),
            "exit_time": pd.to_datetime(["2025-01-01 12:00:00"]),
            "direction": [1],
            "pnl_atr": [2.0],
            "holding_bars": [12],
        }
    )
    right = left.assign(system_name="frequency", direction=-1, pnl_atr=-2.0)

    metrics = correlation.compute_pair_metrics(left, right)

    assert metrics["trade_overlap_ratio"] == 1.0
    assert metrics["same_direction_ratio"] == 0.0
    assert metrics["entry_time_jaccard"] == 1.0
    assert metrics["portfolio_verdict"] in {
        "portfolio_partially_overlapping",
        "portfolio_unclear",
    }


def test_run_benchmark_writes_pairwise_outputs(tmp_path):
    trade_csv = tmp_path / "trades.csv"
    _write_csv(
        trade_csv,
        """
        dataset_name,system_name,signal_time,entry_time,exit_time,signal,policy,entry,exit,entry_atr,exit_atr,pnl_price,pnl_atr,max_profit_atr,max_adverse_atr,hold_hours,exit_reason
        xauusd_metaquotes,quality,2025-01-01 00:00:00,2025-01-01 01:00:00,2025-01-01 03:00:00,1,trail_x8_tp12,100,104,1,1,4,4,5,1,2,hold_timeout
        xauusd_metaquotes,frequency,2025-01-02 00:00:00,2025-01-02 01:00:00,2025-01-02 03:00:00,1,trail_x8,100,102,1,1,2,2,3,1,2,hold_timeout
        """,
    )
    manifest_path = tmp_path / "manifest.json"
    _write_json(
        manifest_path,
        {
            "systems": [
                {
                    "system_name": "quality",
                    "instrument": "XAUUSD",
                    "provider": "MetaQuotes",
                    "source_type": "trade_csv",
                    "trade_csv": str(trade_csv),
                    "dataset_name": "xauusd_metaquotes",
                    "policy_name": "trail_x8_tp12",
                },
                {
                    "system_name": "frequency",
                    "instrument": "XAUUSD",
                    "provider": "MetaQuotes",
                    "source_type": "trade_csv",
                    "trade_csv": str(trade_csv),
                    "dataset_name": "xauusd_metaquotes",
                    "policy_name": "trail_x8",
                },
            ]
        },
    )

    result = correlation.run_benchmark(manifest_path, tmp_path / "out")

    assert len(result["pairwise_matrix"]) == 1
    assert result["pairwise_matrix"][0]["left_system"] == "quality"
    assert result["pairwise_matrix"][0]["right_system"] == "frequency"
    assert (tmp_path / "out" / "pairwise_matrix.csv").exists()
    assert (tmp_path / "out" / "system_summary.csv").exists()
    assert (tmp_path / "out" / "daily_pnl_matrix.csv").exists()
    assert (tmp_path / "out" / "weekly_pnl_matrix.csv").exists()
    assert (tmp_path / "out" / "drawdown_overlap.csv").exists()
    assert (tmp_path / "out" / "summary.json").exists()
    assert (tmp_path / "out" / "run_metadata.json").exists()
