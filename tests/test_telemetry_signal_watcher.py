import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from API import telemetry_signal_watcher as watcher


def test_read_last_time_returns_last_csv_row(tmp_path):
    csv_path = tmp_path / "Nero.csv"
    csv_path.write_text(
        "time;signal;predict\n"
        "2025.01.01 00:00;1;1\n"
        "2025.01.01 01:00;-1;-1\n",
        encoding="utf-8",
    )

    assert watcher.read_last_time(csv_path) == "2025.01.01 01:00"


def test_read_last_time_returns_none_for_header_only_csv(tmp_path):
    csv_path = tmp_path / "Nero.csv"
    csv_path.write_text("time;signal;predict\n", encoding="utf-8")

    assert watcher.read_last_time(csv_path) is None


def test_should_rebuild_when_last_time_changed():
    state = watcher.WatcherState(last_processed_time="2025.01.01 00:00", source_mtime_ns=100)

    assert watcher.should_rebuild(
        current_last_time="2025.01.01 01:00",
        source_mtime_ns=100,
        state=state,
    ) is True


def test_should_not_rebuild_when_time_and_mtime_unchanged():
    state = watcher.WatcherState(last_processed_time="2025.01.01 01:00", source_mtime_ns=100)

    assert watcher.should_rebuild(
        current_last_time="2025.01.01 01:00",
        source_mtime_ns=100,
        state=state,
    ) is False


def test_format_heartbeat_message_for_wait_state(tmp_path):
    message = watcher.format_heartbeat_message(
        watcher.WatcherState(last_status="waiting_for_first_row"),
        input_csv=tmp_path / "Nero.csv",
    )

    assert "WATCHER HEARTBEAT" in message
    assert "status=WAIT" in message


def test_format_heartbeat_message_for_idle_state(tmp_path):
    message = watcher.format_heartbeat_message(
        watcher.WatcherState(last_processed_time="2025.01.01 00:00", last_status="idle"),
        input_csv=tmp_path / "Nero.csv",
    )

    assert "status=IDLE" in message
    assert "last_bar=2025.01.01 00:00" in message


def test_run_once_rebuilds_and_updates_state(tmp_path, monkeypatch):
    input_csv = tmp_path / "Nero.csv"
    input_csv.write_text(
        "time;signal;predict\n"
        "2025.01.01 00:00;1;1\n",
        encoding="utf-8",
    )
    state_path = tmp_path / "state.json"
    calls = {"rebuilt": 0}

    def _fake_rebuild(**kwargs):
        calls["rebuilt"] += 1
        Path(kwargs["predictions_path"]).write_text("pred", encoding="utf-8")
        Path(kwargs["signals_output_path"]).write_text("sig", encoding="utf-8")
        Path(kwargs["metadata_output_path"]).write_text("{}", encoding="utf-8")

    monkeypatch.setattr(watcher, "rebuild_signals", _fake_rebuild)

    changed = watcher.run_once(
        input_csv=input_csv,
        checkpoint_path=tmp_path / "ckpt.pt",
        rule_path=tmp_path / "rule.json",
        predictions_path=tmp_path / "predictions.csv",
        signals_output_path=tmp_path / "signals.csv",
        metadata_output_path=tmp_path / "metadata.json",
        state_path=state_path,
        diagnostic_target_signals_per_year=500,
        batch_size=256,
    )

    assert changed is True
    assert calls["rebuilt"] == 1
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["last_processed_time"] == "2025.01.01 00:00"
    assert state["last_status"] == "rebuilt"


def test_run_once_skips_when_no_new_bar(tmp_path, monkeypatch):
    input_csv = tmp_path / "Nero.csv"
    input_csv.write_text(
        "time;signal;predict\n"
        "2025.01.01 00:00;1;1\n",
        encoding="utf-8",
    )
    stat = input_csv.stat()
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "last_processed_time": "2025.01.01 00:00",
                "source_mtime_ns": stat.st_mtime_ns,
                "updated_at_unix": 0,
                "last_status": "rebuilt",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(watcher, "rebuild_signals", lambda **kwargs: (_ for _ in ()).throw(AssertionError("should not rebuild")))

    changed = watcher.run_once(
        input_csv=input_csv,
        checkpoint_path=tmp_path / "ckpt.pt",
        rule_path=tmp_path / "rule.json",
        predictions_path=tmp_path / "predictions.csv",
        signals_output_path=tmp_path / "signals.csv",
        metadata_output_path=tmp_path / "metadata.json",
        state_path=state_path,
        diagnostic_target_signals_per_year=500,
        batch_size=256,
    )

    assert changed is False
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["last_status"] == "idle"
    assert state["last_processed_time"] == "2025.01.01 00:00"


def test_run_once_skips_and_updates_state_for_header_only_csv(tmp_path, monkeypatch):
    input_csv = tmp_path / "Nero.csv"
    input_csv.write_text("time;signal;predict\n", encoding="utf-8")
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(watcher, "rebuild_signals", lambda **kwargs: (_ for _ in ()).throw(AssertionError("should not rebuild")))

    changed = watcher.run_once(
        input_csv=input_csv,
        checkpoint_path=tmp_path / "ckpt.pt",
        rule_path=tmp_path / "rule.json",
        predictions_path=tmp_path / "predictions.csv",
        signals_output_path=tmp_path / "signals.csv",
        metadata_output_path=tmp_path / "metadata.json",
        state_path=state_path,
        diagnostic_target_signals_per_year=500,
        batch_size=256,
    )

    assert changed is False
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["last_status"] == "waiting_for_first_row"
