from __future__ import annotations

import inspect
import json
from pathlib import Path

from ML.baseline.mt5_execution_diagnostics import (
    build_error_inventory,
    classify_error_message,
    extract_error_code,
    load_error_rows,
    read_error_csv_sample,
    summarize_error_rows,
    write_error_outputs,
    _source_bucket,
)


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
