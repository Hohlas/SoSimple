from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd

from ML.baseline.mt5_signal_schema import MT5_EVENT_COLUMNS


def test_run_tester_rejects_nonzero_exit(monkeypatch, tmp_path: Path) -> None:
    from ML.baseline import run_mt5_batch

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args[0], returncode=1, stdout=b"", stderr=b"failed")

    monkeypatch.setattr(run_mt5_batch.subprocess, "run", fake_run)

    assert run_mt5_batch.run_tester(tmp_path / "tester.ini") is False


def test_run_tester_rejects_liveupdate_redirect(monkeypatch, tmp_path: Path) -> None:
    from ML.baseline import run_mt5_batch

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_path = log_dir / "20260801.log"
    log_path.write_bytes("old\n".encode("utf-16-le"))
    ini_path = tmp_path / "tester.ini"
    ini_path.write_text("[Tester]\n", encoding="utf-8")

    def fake_run(*args, **kwargs):
        with log_path.open("ab") as fh:
            fh.write(
                (
                    'Startup\tsuccessfully initialized from start config "C:\\tester.ini"\n'
                    'LiveUpdate\tstart "C:\\users\\x\\liveupdate\\terminal64.exe" /config:"C:\\tester.ini"\n'
                    "Terminal\texit with code 0\n"
                ).encode("utf-16-le")
            )
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr(run_mt5_batch, "TERMINAL_LOG_DIR", log_dir)
    monkeypatch.setattr(run_mt5_batch, "TESTER_MAX_LIVEUPDATE_RETRIES", 0)
    monkeypatch.setattr(run_mt5_batch.subprocess, "run", fake_run)

    assert run_mt5_batch.run_tester(ini_path) is False


def test_run_tester_retries_after_liveupdate_redirect(monkeypatch, tmp_path: Path) -> None:
    from ML.baseline import run_mt5_batch

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_path = log_dir / "20260801.log"
    log_path.write_bytes("old\n".encode("utf-16-le"))
    ini_path = tmp_path / "tester.ini"
    ini_path.write_text("[Tester]\n", encoding="utf-8")
    calls = {"count": 0}

    def fake_run(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            line = 'LiveUpdate\tstart "C:\\users\\x\\liveupdate\\terminal64.exe" /config:"C:\\tester.ini"\n'
        else:
            line = 'Tester\tautomatic testing started from "C:\\tester.ini"\n'
        with log_path.open("ab") as fh:
            fh.write(line.encode("utf-16-le"))
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr(run_mt5_batch, "TERMINAL_LOG_DIR", log_dir)
    monkeypatch.setattr(run_mt5_batch, "TESTER_MAX_LIVEUPDATE_RETRIES", 1)
    monkeypatch.setattr(run_mt5_batch, "wait_for_liveupdate_clear", lambda: True)
    monkeypatch.setattr(run_mt5_batch.subprocess, "run", fake_run)

    assert run_mt5_batch.run_tester(ini_path) is True
    assert calls["count"] == 2


def test_run_batch_removes_stale_tester_event_file_before_run(monkeypatch, tmp_path: Path) -> None:
    from ML.baseline import run_mt5_batch

    run_id = "candidate_a"
    batch_dir = tmp_path / "batch"
    terminal_files = tmp_path / "terminal_files"
    tester_files = tmp_path / "tester_files"
    out_dir = batch_dir / run_id
    out_dir.mkdir(parents=True)
    terminal_files.mkdir()
    tester_files.mkdir()
    entry_text = "time\n2023.01.02 09:00\n"
    (out_dir / "entry_signals.csv").write_text(entry_text, encoding="utf-8")
    stale = tester_files / f"mt5_trade_events_{run_id}.csv"
    stale.write_text("stale", encoding="utf-8")

    monkeypatch.setattr(run_mt5_batch, "BATCH_DIR", batch_dir)
    monkeypatch.setattr(run_mt5_batch, "TERMINAL_FILES", terminal_files)
    monkeypatch.setattr(run_mt5_batch, "TESTER_FILES", tester_files)
    monkeypatch.setattr(run_mt5_batch, "make_run_id", lambda candidate: run_id)
    monkeypatch.setattr(run_mt5_batch, "create_set_file", lambda run_id: tmp_path / "settings.set")
    monkeypatch.setattr(run_mt5_batch, "create_ini_file", lambda run_id, set_name: tmp_path / "tester.ini")
    monkeypatch.setattr(run_mt5_batch, "wait_for_liveupdate_clear", lambda: True)
    monkeypatch.setattr(run_mt5_batch, "run_tester", lambda ini_path: False)

    run_mt5_batch.run_batch([{"profile": "candidate"}])

    assert not stale.exists()
    assert not (out_dir / "events.csv").exists()
    assert (terminal_files / "mt5_entry_signals.csv").read_text(encoding="utf-8") == entry_text
    assert (tester_files / "mt5_entry_signals.csv").read_text(encoding="utf-8") == entry_text


def test_diagnostics_load_counts_invalid_timestamp_rows(tmp_path: Path) -> None:
    from tests.test_parse_mt5_execution_report import _event_row
    from ML.baseline.mt5_execution_diagnostics import load_event_rows, summarize_timing_contract

    path = tmp_path / "events.csv"
    pd.DataFrame(
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
    ).to_csv(path, sep=";", index=False)

    events = load_event_rows([path])
    summary = summarize_timing_contract(events)

    assert summary["checked_rows"] == 1
    assert summary["invalid_timestamp_rows"] == 1
    assert summary["violations_by_rule"]["invalid_timestamp"] == 1
