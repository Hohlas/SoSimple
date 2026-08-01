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
    load_error_rows,
    read_error_csv_sample,
    summarize_event_anomalies,
    summarize_error_rows,
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
    assert summary["linkage_status"] == "UNKNOWN"


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
