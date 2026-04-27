import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ML import telemetry_daily_reconciliation as daily


def _write_log(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "0 2025.01.01 01:00 MLP BUY mode=telemetry_frequency_v1 ticket=101 signal_time=2025.01.01 00:00 entry_time=2025.01.01 01:00 score=0.88 atr=12.34 spread=0.20 spread_atr=0.0162 open_positions=2 MaxPositions=10 Val=2500.00 Stp=2463.00 Prf=2561.70 Lot=0.10",
                "0 2025.01.01 07:00 MLP CLOSE BUY reason=TakeProfit ticket=101 entry_time=2025.01.01 01:00 exit_time=2025.01.01 07:00 hold_bars=6 entry=2500.00 exit=2561.70 atr=12.34 spread=0.20 spread_atr=0.0162 pnl_atr=5.0000 profit=123.45",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _write_log_with_skip(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "0 2025.01.01 01:00 MLP SKIP reason=MaxPositions sig=1 signal_time=2025.01.01 00:00 score=0.00 open_positions=10 max_positions=10",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _write_signals(path: Path) -> Path:
    pd.DataFrame(
        [
            {"time": "2025.01.01 00:00", "signal": 1},
            {"time": "2025.01.01 01:00", "signal": -1},
            {"time": "2025.01.01 02:00", "signal": 0},
        ]
    ).to_csv(path, sep=";", index=False)
    return path


def test_parse_mlp_open_close_events_links_by_ticket(tmp_path):
    log = _write_log(tmp_path / "tester.log")

    events = daily.parse_mlp_events(log)

    assert events["opens"].iloc[0]["ticket"] == 101
    assert events["opens"].iloc[0]["direction"] == "BUY"
    assert events["opens"].iloc[0]["signal_time"] == "2025.01.01 00:00"
    assert events["opens"].iloc[0]["spread_atr"] == 0.0162
    assert events["closes"].iloc[0]["ticket"] == 101
    assert events["closes"].iloc[0]["reason"] == "TakeProfit"
    linked = daily.reconcile_open_close(events["opens"], events["closes"])
    assert linked.iloc[0]["close_status"] == "closed"
    assert linked.iloc[0]["pnl_atr"] == 5.0


def test_reconciliation_flags_missing_opened_trade(tmp_path):
    signals = daily.load_signal_export(_write_signals(tmp_path / "ml_signals.csv"))
    events = daily.parse_mlp_events(_write_log(tmp_path / "tester.log"))

    diff = daily.reconcile_expected_vs_opened(signals, events["opens"])

    missing = diff.loc[diff["status"] == "missing_open"]
    assert missing["signal_time"].tolist() == ["2025.01.01 01:00"]
    assert missing.iloc[0]["critical"] is True


def test_reconciliation_treats_max_positions_skip_as_explained(tmp_path):
    signals = daily.load_signal_export(_write_signals(tmp_path / "ml_signals.csv"))
    events = daily.parse_mlp_events(_write_log_with_skip(tmp_path / "tester.log"))

    diff = daily.reconcile_expected_vs_opened(signals, events["opens"], events["skips"])

    skipped = diff.loc[diff["status"] == "skipped_max_positions"]
    assert skipped["signal_time"].tolist() == ["2025.01.01 00:00"]
    assert skipped.iloc[0]["critical"] is False


def test_run_daily_reconciliation_writes_required_outputs(tmp_path):
    signals = _write_signals(tmp_path / "ml_signals.csv")
    log = _write_log(tmp_path / "tester.log")
    metadata = tmp_path / "metadata.json"
    metadata.write_text(json.dumps({"output_sha256": "ignored"}), encoding="utf-8")

    summary = daily.run_daily_reconciliation(
        signals_path=signals,
        mt4_log_path=log,
        output_dir=tmp_path / "out",
        label="telemetry_frequency_v1",
        export_metadata_path=metadata,
    )

    assert summary["label"] == "telemetry_frequency_v1"
    assert summary["critical_mismatch_count"] == 1
    assert (tmp_path / "out" / "summary.json").exists()
    assert (tmp_path / "out" / "summary.md").exists()
    assert (tmp_path / "out" / "signals_diff.csv").exists()
    assert (tmp_path / "out" / "trades_reconciliation.csv").exists()


def test_run_daily_reconciliation_filters_expected_signals_by_time_range(tmp_path):
    signals = tmp_path / "ml_signals.csv"
    pd.DataFrame(
        [
            {"time": "2024.12.31 23:00", "signal": 1},
            {"time": "2025.01.01 00:00", "signal": 1},
            {"time": "2025.01.01 01:00", "signal": -1},
            {"time": "2026.01.01 00:00", "signal": -1},
        ]
    ).to_csv(signals, sep=";", index=False)
    log = _write_log(tmp_path / "tester.log")

    summary = daily.run_daily_reconciliation(
        signals_path=signals,
        mt4_log_path=log,
        output_dir=tmp_path / "out",
        label="telemetry_frequency_v1",
        start_time="2025.01.01 00:00",
        end_time="2025.01.01 23:59",
    )

    diff = pd.read_csv(tmp_path / "out" / "signals_diff.csv", sep=";")
    assert summary["expected_signals"] == 2
    assert diff["signal_time"].tolist() == ["2025.01.01 00:00", "2025.01.01 01:00"]


def test_load_signal_export_matches_mql_duplicate_time_keep_last(tmp_path):
    signals = tmp_path / "ml_signals.csv"
    pd.DataFrame(
        [
            {"time": "2025.01.01 00:00", "signal": 1},
            {"time": "2025.01.01 00:00", "signal": -1},
            {"time": "2025.01.01 01:00", "signal": 0},
        ]
    ).to_csv(signals, sep=";", index=False)

    loaded = daily.load_signal_export(signals)

    assert loaded[["signal_time", "signal", "direction"]].to_dict("records") == [
        {"signal_time": "2025.01.01 00:00", "signal": -1, "direction": "SELL"}
    ]


def test_critical_mismatch_sets_nonzero_exit_code(tmp_path):
    signals = _write_signals(tmp_path / "ml_signals.csv")
    log = _write_log(tmp_path / "tester.log")

    summary = daily.run_daily_reconciliation(
        signals_path=signals,
        mt4_log_path=log,
        output_dir=tmp_path / "out",
        label="telemetry_frequency_v1",
    )

    assert daily.exit_code_from_summary(summary) == 1
