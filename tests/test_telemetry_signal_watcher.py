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


def test_read_last_time_reads_last_non_empty_line_without_pandas_frame(tmp_path):
    csv_path = tmp_path / "Nero.csv"
    csv_path.write_text(
        "time;signal;predict\n"
        "2025.01.01 00:00;1;1\n"
        "\n"
        "2025.01.01 01:00;-1;-1\n"
        "\n",
        encoding="utf-8",
    )

    assert watcher.read_last_time(csv_path) == "2025.01.01 01:00"


def test_read_last_time_returns_none_for_header_only_csv(tmp_path):
    csv_path = tmp_path / "Nero.csv"
    csv_path.write_text("time;signal;predict\n", encoding="utf-8")

    assert watcher.read_last_time(csv_path) is None


def test_build_runtime_input_snapshot_keeps_header_and_tail_rows(tmp_path):
    input_csv = tmp_path / "Nero.csv"
    input_csv.write_text(
        "time;signal;predict\n"
        "2025.01.01 00:00;1;1\n"
        "2025.01.01 01:00;1;1\n"
        "2025.01.01 02:00;-1;-1\n"
        "2025.01.01 03:00;0;0\n",
        encoding="utf-8",
    )
    snapshot_csv = tmp_path / "snapshot.csv"

    rows = watcher.build_runtime_input_snapshot(
        input_csv=input_csv,
        snapshot_csv=snapshot_csv,
        max_rows=2,
    )

    assert rows == 2
    assert snapshot_csv.read_text(encoding="utf-8").splitlines() == [
        "time;signal;predict",
        "2025.01.01 02:00;-1;-1",
        "2025.01.01 03:00;0;0",
    ]


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


def test_parse_args_uses_fast_poll_and_slower_heartbeat_defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["telemetry_signal_watcher"])

    args = watcher.parse_args()

    assert args.poll_interval_sec == 1
    assert args.heartbeat_sec == 60


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
        runtime_input_snapshot_path=tmp_path / "snapshot.csv",
        checkpoint_path=tmp_path / "ckpt.pt",
        rule_path=tmp_path / "rule.json",
        predictions_path=tmp_path / "predictions.csv",
        signals_output_path=tmp_path / "signals.csv",
        metadata_output_path=tmp_path / "metadata.json",
        state_path=state_path,
        diagnostic_target_signals_per_year=500,
        batch_size=256,
        max_runtime_rows=100,
    )

    assert changed is True
    assert calls["rebuilt"] == 1
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["last_processed_time"] == "2025.01.01 00:00"
    assert state["last_status"] == "rebuilt"


def test_rebuild_signals_uses_original_contour_baseline(monkeypatch, tmp_path):
    captured: dict[str, object] = {}
    input_csv = tmp_path / "Nero.csv"
    input_csv.write_text(
        "time;signal;predict\n"
        "2025.01.01 00:00;1;1\n",
        encoding="utf-8",
    )

    def _fake_export_predictions(**kwargs):
        captured.update(kwargs)
        Path(kwargs["output_path"]).write_text("pred", encoding="utf-8")

    def _fake_export_signals(**kwargs):
        Path(kwargs["output_path"]).write_text("sig", encoding="utf-8")
        Path(kwargs["metadata_output"]).write_text("{}", encoding="utf-8")

    monkeypatch.setattr(watcher, "export_predictions", _fake_export_predictions)
    monkeypatch.setattr(watcher, "export_signals", _fake_export_signals)

    watcher.rebuild_signals(
        input_csv=input_csv,
        runtime_input_snapshot_path=tmp_path / "snapshot.csv",
        checkpoint_path=tmp_path / "ckpt.pt",
        predictions_path=tmp_path / "pred.csv",
        rule_path=tmp_path / "rule.json",
        signals_output_path=tmp_path / "signals.csv",
        metadata_output_path=tmp_path / "metadata.json",
        diagnostic_target_signals_per_year=500,
        batch_size=256,
        max_runtime_rows=100,
    )

    assert captured["mode"] == "original_contour"
    assert captured["feature_mode"] == "original_baseline"
    assert captured["seq_len"] == 50
    assert captured["include_true_targets"] is False


def test_rebuild_signals_uses_runtime_snapshot_for_exports(monkeypatch, tmp_path):
    captured_predictions: dict[str, object] = {}
    captured_signals: dict[str, object] = {}
    input_csv = tmp_path / "Nero.csv"
    input_csv.write_text(
        "time;signal;predict\n"
        "2025.01.01 00:00;1;1\n"
        "2025.01.01 01:00;-1;-1\n",
        encoding="utf-8",
    )

    def _fake_export_predictions(**kwargs):
        captured_predictions.update(kwargs)
        Path(kwargs["output_path"]).write_text("pred", encoding="utf-8")

    def _fake_export_signals(**kwargs):
        captured_signals.update(kwargs)
        Path(kwargs["output_path"]).write_text("sig", encoding="utf-8")
        Path(kwargs["metadata_output"]).write_text("{}", encoding="utf-8")

    monkeypatch.setattr(watcher, "export_predictions", _fake_export_predictions)
    monkeypatch.setattr(watcher, "export_signals", _fake_export_signals)

    watcher.rebuild_signals(
        input_csv=input_csv,
        runtime_input_snapshot_path=tmp_path / "snapshot.csv",
        checkpoint_path=tmp_path / "ckpt.pt",
        predictions_path=tmp_path / "pred.csv",
        rule_path=tmp_path / "rule.json",
        signals_output_path=tmp_path / "signals.csv",
        metadata_output_path=tmp_path / "metadata.json",
        diagnostic_target_signals_per_year=500,
        batch_size=256,
        max_runtime_rows=1,
    )

    snapshot_path = Path(captured_predictions["input_csv"])
    assert snapshot_path == tmp_path / "snapshot.csv"
    assert snapshot_path.read_text(encoding="utf-8").splitlines() == [
        "time;signal;predict",
        "2025.01.01 01:00;-1;-1",
    ]
    assert Path(captured_signals["base_csv"]) == snapshot_path
    assert captured_signals["diagnostic_direction_source"] == "fractal0_direction"


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
        runtime_input_snapshot_path=tmp_path / "snapshot.csv",
        checkpoint_path=tmp_path / "ckpt.pt",
        rule_path=tmp_path / "rule.json",
        predictions_path=tmp_path / "predictions.csv",
        signals_output_path=tmp_path / "signals.csv",
        metadata_output_path=tmp_path / "metadata.json",
        state_path=state_path,
        diagnostic_target_signals_per_year=500,
        batch_size=256,
        max_runtime_rows=100,
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
        runtime_input_snapshot_path=tmp_path / "snapshot.csv",
        checkpoint_path=tmp_path / "ckpt.pt",
        rule_path=tmp_path / "rule.json",
        predictions_path=tmp_path / "predictions.csv",
        signals_output_path=tmp_path / "signals.csv",
        metadata_output_path=tmp_path / "metadata.json",
        state_path=state_path,
        diagnostic_target_signals_per_year=500,
        batch_size=256,
        max_runtime_rows=100,
    )

    assert changed is False
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["last_status"] == "waiting_for_first_row"
