import json
import sys

import pytest

from ML import benchmark_cross_instrument_robustness as robustness


def _write_csv(path, content="time;signal\n2025.01.01 00:00;1\n"):
    path.write_text(content, encoding="utf-8")


def test_manifest_validation_rejects_unknown_kind(tmp_path):
    ohlc = tmp_path / "ohlc.csv"
    signals = tmp_path / "signals.csv"
    _write_csv(ohlc, "time;open;high;low;close;atr14\n2025.01.01 00:00;1;1;1;1;1\n")
    _write_csv(signals)

    manifest = {
        "datasets": [
            {
                "dataset_name": "xauusd_alpari",
                "instrument": "XAUUSD",
                "provider": "Alpari",
                "kind": "unexpected_kind",
                "ohlc_path": str(ohlc),
                "signals": [
                    {
                        "system_name": "quality",
                        "signal_csv": str(signals),
                        "policy_name": "trail_x8_tp12",
                    }
                ],
            }
        ]
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="unknown dataset kind"):
        robustness.load_manifest(manifest_path)


def test_benchmark_reuses_execution_policy_metrics(tmp_path):
    ohlc = tmp_path / "ohlc.csv"
    ohlc.write_text(
        "\n".join(
            [
                "time;open;high;low;close;atr14",
                "2025.01.01 00:00;100;100;100;100;1",
                "2025.01.01 01:00;100;100;100;100;1",
                "2025.01.01 02:00;100;110;104.5;109;1",
                "2025.01.01 03:00;109;110;103.5;104;1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    signals = tmp_path / "signals.csv"
    signals.write_text("time;signal\n2025.01.01 00:00;1\n", encoding="utf-8")

    manifest = {
        "datasets": [
            {
                "dataset_name": "xauusd_alpari",
                "instrument": "XAUUSD",
                "provider": "Alpari",
                "kind": "provider_drift_baseline",
                "ohlc_path": str(ohlc),
                "signals": [
                    {
                        "system_name": "quality",
                        "signal_csv": str(signals),
                        "policy_name": "shrinking_trail_8_6_4_3",
                    }
                ],
            }
        ]
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = robustness.run_benchmark(manifest_path=manifest_path, output_dir=tmp_path / "out")

    assert len(result["summary"]) == 1
    row = result["summary"][0]
    assert row["dataset"] == "xauusd_alpari"
    assert row["system_name"] == "quality"
    assert row["policy"] == "shrinking_trail_8_6_4_3"
    assert row["trades"] == 1
    assert row["pf"] == "inf"
    assert row["max_drawdown_atr"] == 0.0
    assert row["net_atr"] == 4.0
    assert (tmp_path / "out" / "summary.csv").exists()
    assert (tmp_path / "out" / "summary.json").exists()
    assert (tmp_path / "out" / "trades.csv").exists()


def test_verdict_logic_separates_provider_and_transfer_failures():
    baseline = {
        "trades": 20,
        "pf": 10.0,
        "max_drawdown_atr": 5.0,
        "profit_concentration_top_1": 0.12,
    }

    stable_row = {
        "kind": "provider_drift_baseline",
        "trades": 18,
        "pf": 3.2,
        "max_drawdown_atr": 7.5,
        "profit_concentration_top_1": 0.20,
    }
    degraded_row = {
        "kind": "provider_drift_baseline",
        "trades": 12,
        "pf": 1.3,
        "max_drawdown_atr": 11.0,
        "profit_concentration_top_1": 0.28,
    }
    failed_row = {
        "kind": "provider_drift_baseline",
        "trades": 8,
        "pf": 0.9,
        "max_drawdown_atr": 14.0,
        "profit_concentration_top_1": 0.41,
    }
    transfer_supported = {
        "kind": "cross_instrument_transfer",
        "trades": 14,
        "pf": 1.8,
        "max_drawdown_atr": 9.0,
        "profit_concentration_top_1": 0.22,
    }
    transfer_inconclusive = {
        "kind": "cross_instrument_transfer",
        "trades": 11,
        "pf": 1.05,
        "max_drawdown_atr": 10.5,
        "profit_concentration_top_1": 0.31,
    }
    transfer_failed = {
        "kind": "cross_instrument_transfer",
        "trades": 6,
        "pf": 0.8,
        "max_drawdown_atr": 15.0,
        "profit_concentration_top_1": 0.45,
    }

    assert robustness.evaluate_verdict(stable_row, baseline)["verdict"] == "provider_stable"
    assert robustness.evaluate_verdict(degraded_row, baseline)["verdict"] == "provider_degraded"
    assert robustness.evaluate_verdict(failed_row, baseline)["verdict"] == "provider_failed"
    assert robustness.evaluate_verdict(transfer_supported, baseline)["verdict"] == "transfer_supported"
    assert robustness.evaluate_verdict(transfer_inconclusive, baseline)["verdict"] == "transfer_inconclusive"
    assert robustness.evaluate_verdict(transfer_failed, baseline)["verdict"] == "transfer_failed"


def test_alignment_guard_rejects_out_of_range_signals(tmp_path):
    ohlc = tmp_path / "ohlc.csv"
    ohlc.write_text(
        "\n".join(
            [
                "time;open;high;low;close;atr14",
                "2025.01.01 00:00;100;101;99;100;1",
                "2025.01.01 01:00;100;102;99;101;1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    signals = tmp_path / "signals.csv"
    signals.write_text(
        "\n".join(
            [
                "time;signal",
                "2025.01.01 00:00;1",
                "2025.01.01 00:00;1",
                "2025.01.01 02:00;-1",
                "2025.01.01 03:00;0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    diagnostics = robustness.analyze_signal_alignment(signals_path=signals, ohlc_path=ohlc)

    assert diagnostics["rows_total"] == 4
    assert diagnostics["nonzero_rows"] == 3
    assert diagnostics["nonzero_unique_time"] == 2
    assert diagnostics["duplicate_time_signal_rows"] == 1
    assert diagnostics["missing_ohlc_times"] == 1
    assert diagnostics["missing_ohlc_examples"] == ["2025.01.01 02:00"]

    with pytest.raises(ValueError, match="signals contain timestamps outside ohlc coverage"):
        robustness.assert_signal_alignment_ok(diagnostics)


def test_run_benchmark_writes_provider_and_transfer_views(tmp_path):
    ohlc = tmp_path / "ohlc.csv"
    ohlc.write_text(
        "\n".join(
            [
                "time;open;high;low;close;atr14",
                "2025.01.01 00:00;100;100;100;100;1",
                "2025.01.01 01:00;100;100;100;100;1",
                "2025.01.01 02:00;100;110;104.5;109;1",
                "2025.01.01 03:00;109;110;103.5;104;1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    provider_signals = tmp_path / "provider.csv"
    provider_signals.write_text("time;signal\n2025.01.01 00:00;1\n", encoding="utf-8")
    transfer_signals = tmp_path / "transfer.csv"
    transfer_signals.write_text("time;signal\n2025.01.01 00:00;1\n", encoding="utf-8")

    manifest = {
        "datasets": [
            {
                "dataset_name": "xauusd_alpari",
                "instrument": "XAUUSD",
                "provider": "Alpari",
                "kind": "provider_drift_baseline",
                "ohlc_path": str(ohlc),
                "signals": [
                    {
                        "system_name": "quality",
                        "signal_csv": str(provider_signals),
                        "policy_name": "shrinking_trail_8_6_4_3",
                    }
                ],
            },
            {
                "dataset_name": "eurusd_alpari",
                "instrument": "EURUSD",
                "provider": "Alpari",
                "kind": "cross_instrument_transfer",
                "ohlc_path": str(ohlc),
                "signals": [
                    {
                        "system_name": "quality",
                        "signal_csv": str(transfer_signals),
                        "policy_name": "shrinking_trail_8_6_4_3",
                    }
                ],
            },
        ]
    }
    baseline_reference = {
        "quality": {
            "trades": 1,
            "pf": "inf",
            "max_drawdown_atr": 0.0,
            "profit_concentration_top_1": 1.0,
        }
    }

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(baseline_reference), encoding="utf-8")

    result = robustness.run_benchmark(
        manifest_path=manifest_path,
        baseline_reference_path=baseline_path,
        output_dir=tmp_path / "out",
    )

    assert len(result["provider_drift"]) == 1
    assert len(result["transfer_matrix"]) == 1
    assert result["provider_drift"][0]["verdict"] == "provider_stable"
    assert result["transfer_matrix"][0]["verdict"] == "transfer_supported"
    assert (tmp_path / "out" / "provider_drift.csv").exists()
    assert (tmp_path / "out" / "transfer_matrix.csv").exists()
    assert (tmp_path / "out" / "run_metadata.json").exists()


def test_parse_args_reads_manifest_and_baseline_reference(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "benchmark_cross_instrument_robustness.py",
            "--manifest",
            "manifest.json",
            "--baseline-reference",
            "baseline.json",
            "--output-dir",
            "outdir",
        ],
    )

    args = robustness.parse_args()

    assert args.manifest == "manifest.json"
    assert args.baseline_reference == "baseline.json"
    assert args.output_dir == "outdir"
