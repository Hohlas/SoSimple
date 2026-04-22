import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ML import benchmark_signal_export_parity as parity


def test_analyze_signal_export_counts_duplicate_timestamps(tmp_path):
    signals = tmp_path / "ml_signals.csv"
    pd.DataFrame(
        [
            {"time": "2025.01.01 00:00", "signal": 1},
            {"time": "2025.01.01 00:00", "signal": 1},
            {"time": "2025.01.01 01:00", "signal": -1},
            {"time": "2025.01.01 02:00", "signal": 0},
            {"time": "2025.01.01 03:00", "signal": 1},
            {"time": "2025.01.01 03:00", "signal": -1},
        ]
    ).to_csv(signals, sep=";", index=False)

    summary = parity.analyze_signal_export(signals)

    assert summary["rows_total"] == 6
    assert summary["nonzero_rows"] == 5
    assert summary["nonzero_unique_time"] == 3
    assert summary["nonzero_unique_time_signal"] == 4
    assert summary["duplicate_time_rows"] == 2
    assert summary["duplicate_time_signal_rows"] == 1
    assert summary["same_time_opposite_signal_groups"] == 1
    assert summary["duplicate_time_signal_examples"] == [
        {"time": "2025.01.01 00:00", "signal": 1, "rows": 2}
    ]


def test_parse_mt4_log_counts_opened_trades_and_diagnostics(tmp_path):
    log = tmp_path / "tester.log"
    log.write_text(
        "\n".join(
            [
                "0 2025.01.01 01:00 MLP BUY mode=multi_position ticket=1 signal_time=2025.01.01 00:00 entry_time=2025.01.01 01:00",
                "0 2025.01.01 02:00 MLP SELL mode=multi_position ticket=2 signal_time=2025.01.01 01:00 entry_time=2025.01.01 02:00",
                "0 2025.01.02 00:00   Total signals:    2",
                "0 2025.01.02 00:00   Score filtered:   1  (33.3%)",
                "0 2025.01.02 00:00   Position blocked: 0  (0.0%)",
                "0 2025.01.02 00:00   Opened:           2  (BUY=1 SELL=1)",
                "0 2025.01.02 00:00   Trailing closes:  2",
                "0 2025.01.02 00:00 === TB DIAGNOSTICS ===",
                "0 2025.01.02 00:00   Total signals:    0",
                "0 2025.01.02 00:00   Position blocked: 0  (0%)",
            ]
        ),
        encoding="utf-8",
    )

    summary = parity.parse_mt4_log(log)

    assert summary["opened_trades_from_events"] == 2
    assert summary["opened_buy_from_events"] == 1
    assert summary["opened_sell_from_events"] == 1
    assert summary["unique_signal_times_opened"] == 2
    assert summary["diagnostics"]["total_signals"] == 2
    assert summary["diagnostics"]["score_filtered"] == 1
    assert summary["diagnostics"]["position_blocked"] == 0
    assert summary["diagnostics"]["opened"] == 2
    assert summary["diagnostics"]["trailing_closes"] == 2


def test_run_parity_benchmark_writes_json_and_markdown(tmp_path):
    signals = tmp_path / "ml_signals.csv"
    pd.DataFrame(
        [
            {"time": "2025.01.01 00:00", "signal": 1},
            {"time": "2025.01.01 00:00", "signal": 1},
            {"time": "2025.01.01 01:00", "signal": -1},
        ]
    ).to_csv(signals, sep=";", index=False)
    log = tmp_path / "tester.log"
    log.write_text(
        "MLP BUY signal_time=2025.01.01 00:00\n"
        "MLP SELL signal_time=2025.01.01 01:00\n"
        "Opened:           2  (BUY=1 SELL=1)\n",
        encoding="utf-8",
    )

    summary = parity.run_benchmark(
        signals_path=signals,
        mt4_log_path=log,
        output_dir=tmp_path / "out",
        label="demo",
    )

    assert summary["label"] == "demo"
    assert summary["export"]["nonzero_rows"] == 3
    assert summary["export"]["nonzero_unique_time_signal"] == 2
    assert summary["mt4"]["opened_trades_from_events"] == 2
    assert (tmp_path / "out" / "summary.json").exists()
    assert (tmp_path / "out" / "summary.md").exists()
    saved = json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))
    assert saved["export"]["duplicate_time_signal_rows"] == 1
