from __future__ import annotations

import inspect
import json
from pathlib import Path

import pandas as pd

from ML.baseline.mt5_execution_diagnostics import (
    build_error_inventory,
    build_event_anomaly_outputs,
    classify_error_message,
    discover_batch_event_paths,
    extract_error_code,
    load_event_rows,
    load_json_if_exists,
    load_error_rows,
    read_error_csv_sample,
    summarize_batch_failure,
    summarize_event_anomalies,
    summarize_error_rows,
    trade_count_bucket,
    write_error_outputs,
    _source_bucket,
)
from ML.baseline.mt5_signal_schema import MT5_EVENT_COLUMNS


HEADER = "INFO;SymPer;ServerTime;Ask/Bid/StpLev;Spred;Lot/Ticket;Error;Expir BUY/SEL\n"


def test_read_error_csv_sample_uses_semicolon(tmp_path: Path) -> None:
    path = tmp_path / "ERROR_SoSimple_1.csv"
    path.write_text(
        HEADER
        + "run;XAUUSD60;-2022.12.20 06:00:00;1792.48/1792.28/1;0.20;0.00/13;MLP_OpenLimitOrder: invalid stops! ERROR-130;2022.12.21 03:00/2022.12.21 03:00\n",
        encoding="utf-8",
    )

    sample = read_error_csv_sample(path, nrows=1)

    assert sample.columns.tolist()[:7] == [
        "INFO",
        "SymPer",
        "ServerTime",
        "Ask/Bid/StpLev",
        "Spred",
        "Lot/Ticket",
        "Error",
    ]
    assert sample.loc[0, "Error"] == "MLP_OpenLimitOrder: invalid stops! ERROR-130"


def test_error_inventory_records_missing_expected_file(tmp_path: Path) -> None:
    path = tmp_path / "ERROR_SoSimple_1.csv"
    path.write_text(HEADER, encoding="utf-8")

    inventory = build_error_inventory(tmp_path)

    assert inventory["status"] == "DIAGNOSTIC_ONLY"
    assert inventory["files"][0]["path"].endswith("ERROR_SoSimple_1.csv")
    assert "ERROR_SoSimple_163856259.csv" in inventory["unknowns"]["not_found_expected_files"]
    assert "ERROR_SoSimple_1.csv" in inventory["unknowns"]["missing_magic_column_files"][0]


def test_source_bucket_uses_path_parts(tmp_path: Path) -> None:
    tester_path = tmp_path / "MT" / "tester" / "files" / "ERROR_SoSimple_1.csv"
    mt4_path = tmp_path / "MT" / "MQL4" / "Files" / "ERROR_SoSimple_2.csv"

    assert _source_bucket(tester_path) == "mt_tester_files"
    assert _source_bucket(mt4_path) == "mt4_files"


def test_extract_and_classify_error_message() -> None:
    assert extract_error_code("Trade request send failed ERROR-4756") == 4756
    assert classify_error_message("MLP_OpenLimitOrder: invalid stops! ERROR-130") == "INVALID_STOPS"
    assert classify_error_message(
        "MLP_Close Ticket=235: modification denied because order is too close to market! ERROR-145"
    ) == "MODIFICATION_TOO_CLOSE"
    assert classify_error_message("Trade request send failed ERROR-4756") == "TRADE_REQUEST_SEND_FAILED"
    assert classify_error_message("MLP_OpenMarketOrder: requote! ERROR-138") == "REQUOTE"
    assert classify_error_message("MLP_OpenMarketOrder: market is closed! ERROR-132") == "MARKET_CLOSED"
    assert classify_error_message("MLP_OpenMarketOrder: invalid price! ERROR-129") == "INVALID_PRICE"
    assert classify_error_message("MAIL_SEND-702: function is not confirmed! ERROR-4060") == "OTHER"


def test_load_and_summarize_error_rows(tmp_path: Path) -> None:
    path = tmp_path / "ERROR_SoSimple_2.csv"
    path.write_text(
        HEADER
        + "run;XAUUSD60;-2022.12.20 06:00:00;1792.48/1792.28/1;0.20;0.00/13;MLP_OpenLimitOrder: invalid stops! ERROR-130;2022.12.21 03:00/2022.12.21 03:00\n"
        + "run;XAUUSD60;-2022.12.20 07:00:00;1792.48/1792.28/1;0.20;0.00/14;Trade request send failed ERROR-4756;2022.12.21 04:00/2022.12.21 04:00\n",
        encoding="utf-8",
    )

    rows = load_error_rows([path])
    summary = summarize_error_rows(rows)

    assert rows["error_code"].tolist() == [130, 4756]
    assert rows["error_class"].tolist() == ["INVALID_STOPS", "TRADE_REQUEST_SEND_FAILED"]
    assert rows["Magic"].tolist() == ["13", "14"]
    assert rows["source_bucket"].tolist() == ["other", "other"]
    assert summary["total_rows"] == 2
    assert summary["by_error_class"]["INVALID_STOPS"] == 1
    assert summary["by_error_class"]["TRADE_REQUEST_SEND_FAILED"] == 1
    assert summary["by_magic"]["13"] == 1
    assert summary["by_magic"]["14"] == 1
    assert summary["by_source_file"]["ERROR_SoSimple_2.csv"] == 2
    assert summary["by_source_bucket"]["other"] == 2
    assert summary["unknowns"]["missing_magic_column_files"] == []


def test_summarize_event_anomalies(tmp_path: Path) -> None:
    from tests.test_parse_mt5_execution_report import _event_row, _tx_row

    path = tmp_path / "events.csv"
    pd.DataFrame(
        [
            _event_row("ORDER_PLACED", "2023.01.02 10:00", comment="placed"),
            _event_row(
                "OPEN_FAILED",
                "2023.01.02 10:00",
                comment="position_or_pending_order_exists",
            ),
            _event_row(
                "ORDER_EXPIRED",
                "2023.01.02 16:00",
                comment="pending order not active after max_fill_lag_bars",
            ),
            _tx_row("TX_OPEN", "2023.01.03 10:05", 100, 1001, "EXPERT"),
            _tx_row("TX_CLOSE", "2023.01.03 10:40", 100, 1002, "SL"),
        ],
        columns=MT5_EVENT_COLUMNS,
    ).to_csv(path, sep=";", index=False)

    events = load_event_rows([path])
    summary = summarize_event_anomalies(events)

    assert summary["event_counts"]["ORDER_PLACED"] == 1
    assert summary["event_counts"]["OPEN_FAILED"] == 1
    assert summary["event_counts"]["ORDER_EXPIRED"] == 1
    assert summary["open_failed_reasons"]["position_or_pending_order_exists"] == 1
    assert summary["linkage_status"] == "REQUEST_CONTEXT_AVAILABLE"


def test_summarize_event_anomalies_keeps_unknown_for_legacy_event_context(tmp_path: Path) -> None:
    from tests.test_parse_mt5_execution_report import _event_row

    events = pd.DataFrame(
        [
            _event_row(
                "OPEN_FAILED",
                "2023.01.02 10:00",
                request_seq=-1,
                magic=0,
                symbol="",
                entry_type="",
            ),
        ],
        columns=MT5_EVENT_COLUMNS,
    )

    summary = summarize_event_anomalies(events)

    assert summary["linkage_status"] == "UNKNOWN"


def test_summarize_timing_contract_excludes_tx_rows_with_empty_timing_fields() -> None:
    from tests.test_parse_mt5_execution_report import _event_row, _tx_row
    from ML.baseline.mt5_execution_diagnostics import summarize_timing_contract

    events = pd.DataFrame(
        [
            _event_row(
                "ORDER_PLACED",
                "2023.01.02 10:00",
                feature_time="2023.01.02 09:00",
                signal_time="2023.01.02 09:00",
                feature_available_time="2023.01.02 10:00",
                decision_time="2023.01.02 10:00",
                execution_time="2023.01.02 10:00",
            ),
            _tx_row("TX_OPEN", "2023.01.02 10:05", 100, 1001, "EXPERT"),
            _tx_row("TX_CLOSE", "2023.01.02 10:40", 100, 1002, "SL"),
        ],
        columns=MT5_EVENT_COLUMNS,
    )

    summary = summarize_timing_contract(events)

    assert summary["checked_rows"] == 1
    assert summary["violation_rows"] == 0
    assert summary["tx_rows_excluded"] == 2


def test_summarize_timing_contract_reports_signal_time_violation() -> None:
    from tests.test_parse_mt5_execution_report import _event_row
    from ML.baseline.mt5_execution_diagnostics import summarize_timing_contract

    events = pd.DataFrame(
        [
            _event_row(
                "ORDER_PLACED",
                "2023.01.02 10:00",
                feature_time="2023.01.02 09:00",
                signal_time="2023.01.02 10:00",
                feature_available_time="2023.01.02 10:00",
                decision_time="2023.01.02 10:00",
                execution_time="2023.01.02 10:00",
            )
        ],
        columns=MT5_EVENT_COLUMNS,
    )

    summary = summarize_timing_contract(events)

    assert summary["checked_rows"] == 1
    assert summary["violation_rows"] == 1
    assert summary["violations_by_rule"]["signal_time < feature_available_time"] == 1


def test_summarize_timing_contract_reports_invalid_timestamp_separately() -> None:
    from tests.test_parse_mt5_execution_report import _event_row
    from ML.baseline.mt5_execution_diagnostics import summarize_timing_contract

    events = pd.DataFrame(
        [
            _event_row(
                "ORDER_PLACED",
                "2023.01.02 10:00",
                feature_time="not-a-time",
                signal_time="2023.01.02 09:00",
                feature_available_time="2023.01.02 10:00",
                decision_time="2023.01.02 10:00",
                execution_time="2023.01.02 10:00",
            )
        ],
        columns=MT5_EVENT_COLUMNS,
    )

    summary = summarize_timing_contract(events)

    assert summary["checked_rows"] == 1
    assert summary["invalid_timestamp_rows"] == 1
    assert summary["violations_by_rule"]["invalid_timestamp"] == 1


def test_summarize_timing_contract_counts_timing_violation_events_separately() -> None:
    from tests.test_parse_mt5_execution_report import _event_row
    from ML.baseline.mt5_execution_diagnostics import summarize_timing_contract

    events = pd.DataFrame(
        [
            _event_row(
                "ORDER_PLACED",
                "2023.01.02 10:00",
                feature_time="2023.01.02 09:00",
                signal_time="2023.01.02 09:30",
                feature_available_time="2023.01.02 10:00",
                decision_time="2023.01.02 10:00",
                execution_time="2023.01.02 10:00",
            ),
            _event_row(
                "TIMING_VIOLATION",
                "2023.01.02 10:01",
                feature_time="2023.01.02 09:00",
                signal_time="2023.01.02 10:00",
                feature_available_time="2023.01.02 10:00",
                decision_time="2023.01.02 10:00",
                execution_time="2023.01.02 10:01",
            ),
        ],
        columns=MT5_EVENT_COLUMNS,
    )

    summary = summarize_timing_contract(events)

    assert summary["checked_rows"] == 1
    assert summary["violation_rows"] == 0
    assert summary["timing_violation_event_count"] == 1


def test_summarize_timing_contract_reports_legacy_violation_without_signal_time() -> None:
    from tests.test_parse_mt5_execution_report import _event_row
    from ML.baseline.mt5_execution_diagnostics import summarize_timing_contract

    events = pd.DataFrame(
        [
            _event_row(
                "ORDER_PLACED",
                "2023.01.02 10:00",
                feature_time="2023.01.02 11:00",
                signal_time="",
                feature_available_time="2023.01.02 10:00",
                decision_time="2023.01.02 10:00",
                execution_time="2023.01.02 10:00",
            )
        ],
        columns=MT5_EVENT_COLUMNS,
    )

    summary = summarize_timing_contract(events)

    assert summary["checked_rows"] == 1
    assert summary["violation_rows"] == 1
    assert summary["violations_by_rule"]["feature_time <= feature_available_time (legacy_no_signal_time)"] == 1


def test_summarize_event_anomalies_handles_non_empty_frame_without_event_column() -> None:
    events = pd.DataFrame(
        [
            {
                "feature_time": "2023.01.02 09:00",
                "signal_time": "2023.01.02 09:30",
            }
        ]
    )

    summary = summarize_event_anomalies(events)

    assert summary["status"] == "DIAGNOSTIC_ONLY"
    assert summary["total_rows"] == 0
    assert summary["event_counts"] == {}
    assert summary["timing_contract"] == {
        "status": "DIAGNOSTIC_ONLY",
        "contract": "feature_time <= signal_time < feature_available_time <= decision_time <= execution_time",
        "checked_rows": 0,
        "violation_rows": 0,
        "tx_rows_excluded": 0,
        "timing_violation_event_count": 0,
        "invalid_timestamp_rows": 0,
        "violations_by_rule": {},
    }


def test_discover_batch_event_paths_excludes_smoke(tmp_path: Path) -> None:
    from tests.test_parse_mt5_execution_report import _event_row

    batch_root = tmp_path / "batch"
    candidate = batch_root / "candidate_a"
    smoke = batch_root / "_smoke"
    candidate.mkdir(parents=True)
    smoke.mkdir(parents=True)
    pd.DataFrame([_event_row("ORDER_PLACED", "2023.01.02 10:00")], columns=MT5_EVENT_COLUMNS).to_csv(
        candidate / "events.csv",
        sep=";",
        index=False,
    )
    pd.DataFrame([_event_row("ORDER_PLACED", "2023.01.02 10:00")], columns=MT5_EVENT_COLUMNS).to_csv(
        smoke / "events.csv",
        sep=";",
        index=False,
    )

    assert discover_batch_event_paths(batch_root) == [candidate / "events.csv"]
    assert load_event_rows([candidate / "events.csv"])["run_id"].tolist() == ["candidate_a"]


def test_build_event_anomaly_outputs_reports_batch_run_count(tmp_path: Path) -> None:
    from tests.test_parse_mt5_execution_report import _event_row

    reference = tmp_path / "reference.csv"
    batch_root = tmp_path / "batch"
    candidate = batch_root / "candidate_a"
    smoke = batch_root / "_smoke"
    candidate.mkdir(parents=True)
    smoke.mkdir(parents=True)
    pd.DataFrame([_event_row("ORDER_EXPIRED", "2023.01.02 10:00")], columns=MT5_EVENT_COLUMNS).to_csv(
        reference,
        sep=";",
        index=False,
    )
    pd.DataFrame([_event_row("OPEN_FAILED", "2023.01.02 11:00")], columns=MT5_EVENT_COLUMNS).to_csv(
        candidate / "events.csv",
        sep=";",
        index=False,
    )
    pd.DataFrame([_event_row("OPEN_FAILED", "2023.01.02 12:00")], columns=MT5_EVENT_COLUMNS).to_csv(
        smoke / "events.csv",
        sep=";",
        index=False,
    )

    summary, anomalies = build_event_anomaly_outputs([reference], batch_root)

    assert summary["batch_run_count"] == 1
    assert summary["batch_event_path_count"] == 1
    assert summary["excluded_service_dirs"] == ["_smoke"]
    assert summary["batch_runs"]["event_counts"]["OPEN_FAILED"] == 1
    assert len(anomalies) == 2


def test_build_event_anomaly_outputs_tolerates_timing_violation_in_diagnostic_load(tmp_path: Path) -> None:
    from tests.test_parse_mt5_execution_report import _event_row

    reference = tmp_path / "reference.csv"
    batch_root = tmp_path / "batch"
    candidate = batch_root / "candidate_a"
    candidate.mkdir(parents=True)
    pd.DataFrame(
        [
            _event_row(
                "ORDER_PLACED",
                "2023.01.02 10:00",
                signal_time="2023.01.02 10:00",
                feature_available_time="2023.01.02 10:00",
            )
        ],
        columns=MT5_EVENT_COLUMNS,
    ).to_csv(reference, sep=";", index=False)
    pd.DataFrame([_event_row("OPEN_FAILED", "2023.01.02 11:00")], columns=MT5_EVENT_COLUMNS).to_csv(
        candidate / "events.csv",
        sep=";",
        index=False,
    )

    summary, _ = build_event_anomaly_outputs([reference], batch_root)

    timing = summary["reference_runs"]["timing_contract"]
    assert timing["checked_rows"] == 1
    assert timing["violation_rows"] == 1
    assert timing["violations_by_rule"]["signal_time < feature_available_time"] == 1


def test_write_error_outputs_summarizes_without_concat(tmp_path: Path) -> None:
    path = tmp_path / "ERROR_SoSimple_3.csv"
    path.write_text(
        HEADER
        + "run;XAUUSD60;-2022.12.20 06:00:00;1792.48/1792.28/1;0.20;0.00/13;MLP_OpenLimitOrder: invalid stops! ERROR-130;2022.12.21 03:00/2022.12.21 03:00\n",
        encoding="utf-8",
    )
    output_csv = tmp_path / "classified.csv"
    output_json = tmp_path / "summary.json"

    source = inspect.getsource(write_error_outputs)
    assert "pd.concat" not in source

    write_error_outputs([path], output_csv, output_json)

    summary = json.loads(output_json.read_text(encoding="utf-8"))
    assert output_csv.exists()
    assert summary["total_rows"] == 1
    assert summary["by_error_class"]["INVALID_STOPS"] == 1


def test_trade_count_bucket_uses_fixed_ranges() -> None:
    assert trade_count_bucket(0) == "<100"
    assert trade_count_bucket(99) == "<100"
    assert trade_count_bucket(100) == "100-149"
    assert trade_count_bucket(149) == "100-149"
    assert trade_count_bucket(150) == "150+"


def test_load_json_if_exists_returns_none_for_missing_file(tmp_path: Path) -> None:
    assert load_json_if_exists(tmp_path / "missing.json") is None


def test_summarize_batch_failure_keeps_no_winner(tmp_path: Path) -> None:
    batch = {
        "status": "DIAGNOSTIC_ONLY",
        "verdict": "BATCH_NO_WINNER",
        "n_candidates": 2,
        "n_valid": 2,
        "n_eligible": 1,
        "n_diagnostic_only": 1,
        "winners_ranked": [
            {
                "run_id": "a",
                "bs_p05": 0.88,
                "trades_count": 102,
                "profit_concentration_pass": True,
                "all_gates_pass": False,
            }
        ],
        "table": [
            {
                "run_id": "a",
                "trades_count": 102,
                "profit_factor": 1.23,
                "trades_buy": 55,
                "trades_sell": 47,
                "win_rate": 0.41,
                "pf_buy": 1.10,
                "pf_sell": 1.05,
                "pf_by_year": {"2024": 1.20},
                "gross_profit_by_year": {"2024": 123.0},
                "pnl_by_trade": [50.0, -20.0, 73.0, -80.0],
            },
            {
                "run_id": "b",
                "trades_count": 40,
                "profit_factor": 1.50,
                "trades_buy": 20,
                "trades_sell": 20,
                "win_rate": 0.50,
                "pf_buy": 1.25,
                "pf_sell": 1.30,
                "pf_by_year": {"2024": 1.40},
                "gross_profit_by_year": {"2024": 80.0},
            },
        ],
    }
    path = tmp_path / "batch_summary.json"
    path.write_text(json.dumps(batch), encoding="utf-8")

    run_dir = tmp_path / "a"
    run_dir.mkdir()
    (run_dir / "entry_signals.json").write_text(
        json.dumps({"active_signal_rows": 204, "buy_rows": 110, "sell_rows": 94}),
        encoding="utf-8",
    )
    (run_dir / "metrics.json").write_text(
        json.dumps({"profit_sum": 23.0}),
        encoding="utf-8",
    )
    from tests.test_parse_mt5_execution_report import _event_row

    pd.DataFrame([_event_row("OPEN", "2024.01.01 00:00")], columns=MT5_EVENT_COLUMNS).to_csv(
        run_dir / "events.csv",
        sep=";",
        index=False,
    )

    summary = summarize_batch_failure(path, batch_root=tmp_path)

    assert summary["status"] == "DIAGNOSTIC_ONLY"
    assert summary["verdict"] == "BATCH_NO_WINNER"
    assert summary["top_failure_modes"]["low_bootstrap_lower_bound"] == 1
    assert summary["top_failure_modes"]["trade_count_buckets"] == {"100-149": 1}
    assert summary["top_candidates"][0]["run_id"] == "a"
    assert summary["top_candidates"][0]["trade_count_bucket"] == "100-149"
    assert summary["top_candidates"][0]["fill_rate"] == 0.5
    assert summary["top_candidates"][0]["active_signal_rows"] == 204
    assert summary["top_candidates"][0]["gross_profit"] == 123.0
    assert summary["top_candidates"][0]["gross_loss"] == 100.0
    assert summary["top_candidates"][0]["average_win"] == 61.5
    assert summary["top_candidates"][0]["average_loss_abs"] == 50.0
    assert summary["sample_sizes"]["candidate_runs"] == 2
    assert summary["sample_sizes"]["eligible_top_candidates"] == 1
    assert summary["sample_sizes"]["eligible_top_candidate_trades"] == 102
    assert summary["sample_sizes"]["eligible_top_candidate_active_signal_rows"] == 204
    assert summary["sample_sizes"]["eligible_top_candidate_buy_signal_rows"] == 110
    assert summary["sample_sizes"]["eligible_top_candidate_sell_signal_rows"] == 94
    assert summary["forbidden_interpretation_guard"] == "no_new_winner_selected"


def test_summarize_batch_failure_does_not_fill_missing_metrics(tmp_path: Path) -> None:
    batch = {
        "status": "DIAGNOSTIC_ONLY",
        "verdict": "BATCH_NO_WINNER",
        "n_candidates": 1,
        "n_valid": 1,
        "n_eligible": 1,
        "n_diagnostic_only": 0,
        "winners_ranked": [
            {
                "run_id": "a",
                "bs_p05": 0.88,
                "trades_count": 102,
                "profit_concentration_pass": True,
                "all_gates_pass": False,
            }
        ],
        "table": [
            {
                "run_id": "a",
                "trades_count": 102,
                "profit_factor": 1.23,
                "gross_profit": 999.0,
                "gross_loss": 888.0,
                "pf_by_year": {"2024": 1.23},
                "gross_profit_by_year": {"2024": 999.0},
                "pnl_by_trade": [1.0, -1.0],
            }
        ],
    }
    path = tmp_path / "batch_summary.json"
    path.write_text(json.dumps(batch), encoding="utf-8")
    run_dir = tmp_path / "a"
    run_dir.mkdir()
    (run_dir / "entry_signals.json").write_text(
        json.dumps({"active_signal_rows": 204}),
        encoding="utf-8",
    )
    from tests.test_parse_mt5_execution_report import _event_row

    pd.DataFrame([_event_row("OPEN", "2024.01.01 00:00")], columns=MT5_EVENT_COLUMNS).to_csv(
        run_dir / "events.csv",
        sep=";",
        index=False,
    )

    summary = summarize_batch_failure(path, batch_root=tmp_path)

    candidate = summary["top_candidates"][0]
    assert candidate["gross_profit"] is None
    assert candidate["gross_loss"] is None
    assert candidate["pf_by_year"] is None
    assert candidate["gross_profit_by_year"] is None
    assert candidate["pnl_by_trade"] is None
    assert summary["unknowns"]["missing_per_run_inputs"] == {"a": ["metrics.json"]}
