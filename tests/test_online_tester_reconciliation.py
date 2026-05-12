import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ML import online_tester_reconciliation as recon


EVENT_COLUMNS = [
    "event",
    "ticket",
    "direction",
    "signal_time",
    "entry_time",
    "exit_time",
    "reason",
    "score",
    "atr",
    "bid",
    "ask",
    "spread",
    "spread_atr",
    "bar_open",
    "bar_high",
    "bar_low",
    "bar_close",
    "requested_price",
    "order_open_price",
    "order_close_price",
    "slippage_points",
    "entry",
    "stop",
    "take_profit",
    "close",
    "profit",
    "swap",
    "commission",
    "hold_bars",
    "open_positions",
    "max_positions",
    "balance",
    "equity",
]


def _event(**overrides):
    row = {
        "event": "OPEN",
        "ticket": 101,
        "direction": "BUY",
        "signal_time": "2025.01.01 00:00",
        "entry_time": "2025.01.01 00:05",
        "exit_time": "1970.01.01 00:00",
        "reason": "",
        "score": 0.0,
        "atr": 10.0,
        "bid": 100.0,
        "ask": 100.2,
        "spread": 0.2,
        "spread_atr": 0.02,
        "bar_open": 100.0,
        "bar_high": 101.0,
        "bar_low": 99.0,
        "bar_close": 100.0,
        "requested_price": 100.2,
        "order_open_price": 100.2,
        "order_close_price": 0.0,
        "slippage_points": 0.0,
        "entry": 100.2,
        "stop": 90.0,
        "take_profit": 120.0,
        "close": 0.0,
        "profit": 0.0,
        "swap": 0.0,
        "commission": 0.0,
        "hold_bars": 0,
        "open_positions": 0,
        "max_positions": 20,
        "balance": 10000.0,
        "equity": 10000.0,
    }
    row.update(overrides)
    return row


def _write_events(path: Path, rows: list[dict]) -> Path:
    pd.DataFrame(rows, columns=EVENT_COLUMNS).to_csv(path, sep=";", index=False)
    return path


def _write_signals(path: Path) -> Path:
    pd.DataFrame(
        [
            {"time": "2025.01.01 00:00", "signal": 1},
            {"time": "2025.01.01 00:00", "signal": -1},
            {"time": "2025.01.01 01:00", "signal": 0},
            {"time": "2025.01.01 02:00", "signal": 1},
        ]
    ).to_csv(path, sep=";", index=False)
    return path


def test_load_signals_filters_zero_and_keeps_last_duplicate(tmp_path):
    signals = recon.load_signals(_write_signals(tmp_path / "ml_signals.csv"))

    assert signals[["signal_time", "signal", "direction"]].to_dict("records") == [
        {"signal_time": pd.Timestamp("2025-01-01 00:00:00"), "signal": -1, "direction": "SELL"},
        {"signal_time": pd.Timestamp("2025-01-01 02:00:00"), "signal": 1, "direction": "BUY"},
    ]


def test_match_signals_distinguishes_open_failed_from_missing_open(tmp_path):
    signals = recon.load_signals(_write_signals(tmp_path / "ml_signals.csv"))
    events = recon.load_events(
        _write_events(
            tmp_path / "events.csv",
            [
                _event(event="OPEN_FAILED", ticket=0, direction="SELL", signal_time="2025.01.01 00:00", reason="OrderSendError138"),
            ],
        )
    )

    diff = recon.match_signals_to_trades(signals, events)

    assert diff[["signal_time", "direction", "status"]].to_dict("records") == [
        {"signal_time": pd.Timestamp("2025-01-01 00:00:00"), "direction": "SELL", "status": "open_failed"},
        {"signal_time": pd.Timestamp("2025-01-01 02:00:00"), "direction": "BUY", "status": "missing_open"},
    ]


def test_compare_online_tester_pairs_by_signal_time_and_direction_without_legacy_column(tmp_path):
    online = recon.load_events(
        _write_events(
            tmp_path / "online.csv",
            [
                _event(ticket=10, direction="BUY", signal_time="2025.01.01 00:00", entry=100.0),
                _event(
                    event="CLOSE",
                    ticket=10,
                    direction="BUY",
                    signal_time="1970.01.01 00:00",
                    entry_time="2025.01.01 00:05",
                    exit_time="2025.01.01 01:00",
                    reason="Timeout",
                    close=105.0,
                    order_close_price=105.0,
                    profit=50.0,
                    hold_bars=12,
                ),
            ],
        )
    )
    tester = recon.load_events(
        _write_events(
            tmp_path / "tester.csv",
            [
                _event(ticket=20, direction="BUY", signal_time="2025.01.01 00:00", entry=100.0),
                _event(
                    event="CLOSE",
                    ticket=20,
                    direction="BUY",
                    signal_time="1970.01.01 00:00",
                    entry_time="2025.01.01 00:05",
                    exit_time="2025.01.01 01:00",
                    reason="Timeout",
                    close=104.0,
                    order_close_price=104.0,
                    profit=40.0,
                    hold_bars=12,
                ),
            ],
        )
    )

    comparison = recon.compare_online_tester(recon.build_trades(online), recon.build_trades(tester))

    assert comparison[["signal_time", "direction", "match_status", "pnl_diff"]].to_dict("records") == [
        {
            "signal_time": pd.Timestamp("2025-01-01 00:00:00"),
            "direction": "BUY",
            "match_status": "matched",
            "pnl_diff": 10.0,
        }
    ]


def test_run_reconciliation_writes_summary_with_expectancy_and_open_failed(tmp_path):
    signals_path = _write_signals(tmp_path / "ml_signals.csv")
    online_path = _write_events(
        tmp_path / "online.csv",
        [
            _event(event="OPEN_FAILED", ticket=0, direction="SELL", signal_time="2025.01.01 00:00", reason="OrderSendError138"),
            _event(ticket=11, direction="BUY", signal_time="2025.01.01 02:00", entry=100.0),
            _event(
                event="CLOSE",
                ticket=11,
                direction="BUY",
                signal_time="1970.01.01 00:00",
                entry_time="2025.01.01 02:05",
                exit_time="2025.01.01 03:00",
                reason="TakeProfit",
                close=110.0,
                order_close_price=110.0,
                profit=100.0,
            ),
        ],
    )
    tester_path = _write_events(
        tmp_path / "tester.csv",
        [
            _event(ticket=21, direction="SELL", signal_time="2025.01.01 00:00", entry=100.0),
            _event(
                event="CLOSE",
                ticket=21,
                direction="SELL",
                signal_time="1970.01.01 00:00",
                entry_time="2025.01.01 00:05",
                exit_time="2025.01.01 01:00",
                reason="StopLoss",
                close=105.0,
                order_close_price=105.0,
                profit=-50.0,
            ),
            _event(ticket=22, direction="BUY", signal_time="2025.01.01 02:00", entry=100.0),
            _event(
                event="CLOSE",
                ticket=22,
                direction="BUY",
                signal_time="1970.01.01 00:00",
                entry_time="2025.01.01 02:05",
                exit_time="2025.01.01 03:00",
                reason="TakeProfit",
                close=108.0,
                order_close_price=108.0,
                profit=80.0,
            ),
        ],
    )

    summary = recon.run_reconciliation(
        events_path=online_path,
        signals_path=signals_path,
        output_dir=tmp_path / "out",
        tester_events_path=tester_path,
    )

    assert summary["signals"]["open_failed"] == 1
    assert summary["online"]["closed_trades"]["expectancy"] == 100.0
    assert summary["online"]["signal_basis"]["expectancy"] == 50.0
    assert summary["paired"]["pnl_diff_total"] == 20.0
    assert json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))["signals"]["open_failed"] == 1
    assert (tmp_path / "out" / "trades_comparison.csv").exists()
