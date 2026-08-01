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
    (out_dir / "entry_signals.csv").write_text("time\n2023.01.02 09:00\n", encoding="utf-8")
    stale = tester_files / f"mt5_trade_events_{run_id}.csv"
    stale.write_text("stale", encoding="utf-8")

    monkeypatch.setattr(run_mt5_batch, "BATCH_DIR", batch_dir)
    monkeypatch.setattr(run_mt5_batch, "TERMINAL_FILES", terminal_files)
    monkeypatch.setattr(run_mt5_batch, "TESTER_FILES", tester_files)
    monkeypatch.setattr(run_mt5_batch, "make_run_id", lambda candidate: run_id)
    monkeypatch.setattr(run_mt5_batch, "create_set_file", lambda run_id: tmp_path / "settings.set")
    monkeypatch.setattr(run_mt5_batch, "create_ini_file", lambda run_id, set_name: tmp_path / "tester.ini")
    monkeypatch.setattr(run_mt5_batch, "run_tester", lambda ini_path: False)

    run_mt5_batch.run_batch([{"profile": "candidate"}])

    assert not stale.exists()
    assert not (out_dir / "events.csv").exists()


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
