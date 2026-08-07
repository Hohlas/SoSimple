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
    monkeypatch.setattr(run_mt5_batch, "create_set_file", lambda run_id, *, max_positions=1: tmp_path / "settings.set")
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


def test_main_accepts_force_rerun_flag() -> None:
    from ML.baseline import run_mt5_batch

    parser = run_mt5_batch.build_arg_parser()
    args = parser.parse_args(["--phase", "tester", "--max-positions", "1", "--force-rerun"])

    assert args.phase == "tester"
    assert args.max_positions == 1
    assert args.force_rerun is True


def test_smoke_only_flag_is_recognised() -> None:
    """Audit V1: `--phase tester` runs the full batch; the lightweight gate in
    Task 6 needs a smoke-only path. `--smoke-only` must parse to True and (when
    wired in main()) must stop after smoke instead of entering run_batch."""
    from ML.baseline import run_mt5_batch

    parser = run_mt5_batch.build_arg_parser()
    args = parser.parse_args(["--phase", "tester", "--max-positions", "2", "--smoke-only"])

    assert args.smoke_only is True


def test_run_batch_force_rerun_overrides_skip_when_unexplained_zero(
    monkeypatch, tmp_path
) -> None:
    """Behavioral contract: when force_rerun=True and metrics.json already exists
    with UNEXPLAINED=0, run_batch must NOT skip and must invoke run_tester.

    Audit item 4: backcompat was wrongly proved by 32/32 SKIP. force_rerun must
    make the skip-path inert.
    """
    from ML.baseline import run_mt5_batch
    import json

    run_id = "candidate_skip"
    batch_dir = tmp_path / "batch"
    tester_files = tmp_path / "tester_files"
    out_dir = batch_dir / run_id
    out_dir.mkdir(parents=True)
    tester_files.mkdir()

    # Pre-existing metrics claiming success -> normally causes SKIP.
    metrics_with_zero = {"reconciliation": {"class_counts": {"UNEXPLAINED": 0}}}
    (out_dir / "metrics.json").write_text(json.dumps(metrics_with_zero), encoding="utf-8")
    # events.csv must exist for the skip guard; content doesn't matter for force_rerun.
    (out_dir / "events.csv").write_text("event\nINIT\n", encoding="utf-8")
    (out_dir / "entry_signals.csv").write_text("time\n2023.01.02 09:00\n", encoding="utf-8")

    calls = {"run_tester": 0}

    def fake_run_tester(ini_path):
        calls["run_tester"] += 1
        # Simulate tester producing an events file.
        events_src = tester_files / f"mt5_trade_events_{run_id}.csv"
        events_src.write_text("event\nINIT\n", encoding="utf-8")
        return True

    monkeypatch.setattr(run_mt5_batch, "BATCH_DIR", batch_dir)
    monkeypatch.setattr(run_mt5_batch, "TESTER_FILES", tester_files)
    monkeypatch.setattr(run_mt5_batch, "TERMINAL_FILES", tmp_path / "terminal")
    monkeypatch.setattr(run_mt5_batch, "make_run_id", lambda candidate: run_id)
    monkeypatch.setattr(run_mt5_batch, "create_set_file", lambda run_id, *, max_positions=1: tmp_path / "settings.set")
    monkeypatch.setattr(run_mt5_batch, "create_ini_file", lambda run_id, set_name: tmp_path / "tester.ini")
    monkeypatch.setattr(run_mt5_batch, "wait_for_liveupdate_clear", lambda: True)
    monkeypatch.setattr(run_mt5_batch, "copy_entry_signal_file", lambda src: None)
    monkeypatch.setattr(run_mt5_batch, "run_tester", fake_run_tester)
    # parse_events returns a minimal metrics dict so run_batch records n_done.
    monkeypatch.setattr(run_mt5_batch, "parse_events", lambda run_id, events_dst: {"reconciliation": {"class_counts": {"UNEXPLAINED": 0, "CLOSED_TX": 1}}})

    run_mt5_batch.run_batch([{"profile": "candidate"}], force_rerun=True)

    assert calls["run_tester"] == 1, "force_rerun=True must override SKIP and invoke run_tester"


def test_run_batch_skips_when_unexplained_zero_and_no_force_rerun(
    monkeypatch, tmp_path
) -> None:
    """Inverse: without force_rerun, existing metrics.json with UNEXPLAINED=0
    must still SKIP (backcompat regression guard)."""
    from ML.baseline import run_mt5_batch
    import json

    run_id = "candidate_skip_normally"
    batch_dir = tmp_path / "batch"
    out_dir = batch_dir / run_id
    out_dir.mkdir(parents=True)

    (out_dir / "metrics.json").write_text(
        json.dumps({"reconciliation": {"class_counts": {"UNEXPLAINED": 0}}}),
        encoding="utf-8",
    )
    (out_dir / "events.csv").write_text("event\nINIT\n", encoding="utf-8")

    calls = {"run_tester": 0}
    monkeypatch.setattr(run_mt5_batch, "BATCH_DIR", batch_dir)
    monkeypatch.setattr(run_mt5_batch, "make_run_id", lambda candidate: run_id)
    monkeypatch.setattr(run_mt5_batch, "run_tester", lambda ini_path: calls.__setitem__("run_tester", calls["run_tester"] + 1) or True)

    run_mt5_batch.run_batch([{"profile": "candidate"}], force_rerun=False)

    assert calls["run_tester"] == 0, "force_rerun=False with UNEXPLAINED=0 must SKIP"
