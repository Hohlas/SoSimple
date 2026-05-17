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


def test_read_csv_tail_lines_keeps_header_and_last_data_rows(tmp_path):
    csv_path = tmp_path / "Nero.csv"
    csv_path.write_text(
        "time;signal;predict\n"
        "2025.01.01 00:00;1;1\n"
        "2025.01.01 01:00;-1;-1\n"
        "2025.01.01 02:00;0;0\n"
        "\n",
        encoding="utf-8",
    )

    header, rows = watcher.read_csv_tail_lines(csv_path, max_data_rows=2)

    assert header == "time;signal;predict"
    assert rows == [
        "2025.01.01 01:00;-1;-1",
        "2025.01.01 02:00;0;0",
    ]


def test_read_csv_tail_lines_expands_window_until_header_is_available(tmp_path):
    csv_path = tmp_path / "Nero.csv"
    csv_path.write_text(
        "time;signal;predict\n"
        + "".join(f"2025.01.01 {hour:02d}:00;1;1\n" for hour in range(12)),
        encoding="utf-8",
    )

    header, rows = watcher.read_csv_tail_lines(csv_path, max_data_rows=3, initial_block_size=32)

    assert header == "time;signal;predict"
    assert rows == [
        "2025.01.01 09:00;1;1",
        "2025.01.01 10:00;1;1",
        "2025.01.01 11:00;1;1",
    ]


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

    assert args.watcher_mode == "entry_path_v1_live_safe_online"
    assert args.poll_interval_sec == 1
    assert args.heartbeat_sec == 60


def test_resolve_mode_paths_uses_entry_path_defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["telemetry_signal_watcher"])
    args = watcher.parse_args()

    resolved = watcher.resolve_mode_paths(args)

    assert resolved.checkpoint_path == watcher.DEFAULT_ENTRY_PATH_CHECKPOINT
    assert resolved.rule_path == watcher.DEFAULT_ENTRY_PATH_RULE_PATH
    assert resolved.max_runtime_rows == watcher.DEFAULT_ENTRY_PATH_MAX_RUNTIME_ROWS


def test_entry_path_default_runtime_rows_use_latest_row_with_atr_substitution():
    assert watcher.ENTRY_PATH_RUNTIME_REQUIRED_HISTORY_ROWS == 1
    assert watcher.DEFAULT_ENTRY_PATH_MAX_RUNTIME_ROWS == watcher.ENTRY_PATH_RUNTIME_REQUIRED_HISTORY_ROWS


def test_resolve_mode_paths_uses_legacy_defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["telemetry_signal_watcher", "--watcher-mode", "telemetry_frequency_v1_legacy"])
    args = watcher.parse_args()

    resolved = watcher.resolve_mode_paths(args)

    assert resolved.checkpoint_path == watcher.DEFAULT_LEGACY_CHECKPOINT
    assert resolved.rule_path == watcher.DEFAULT_LEGACY_RULE_PATH
    assert resolved.max_runtime_rows == watcher.ENTRY_PATH_RUNTIME_REQUIRED_HISTORY_ROWS


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
        runtime_input_preprocessed_path=tmp_path / "preprocessed.csv",
        checkpoint_path=tmp_path / "ckpt.pt",
        rule_path=tmp_path / "rule.json",
        predictions_path=tmp_path / "predictions.csv",
        signals_output_path=tmp_path / "signals.csv",
        metadata_output_path=tmp_path / "metadata.json",
        state_path=state_path,
        diagnostic_target_signals_per_year=500,
        entry_path_score_threshold_override=None,
        entry_path_diagnostic_all_rows=False,
        watcher_mode="entry_path_v1_live_safe_online",
        batch_size=256,
        max_runtime_rows=100,
    )

    assert changed is True
    assert calls["rebuilt"] == 1
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["last_processed_time"] == "2025.01.01 00:00"
    assert state["last_status"] == "rebuilt"


def test_rebuild_signals_uses_entry_path_live_safe_by_default(monkeypatch, tmp_path):
    captured: dict[str, object] = {}
    captured_signals: dict[str, object] = {}
    input_csv = tmp_path / "Nero.csv"
    input_csv.write_text(
        "time;signal;predict\n"
        "2025.01.01 00:00;1;1\n",
        encoding="utf-8",
    )

    def _fake_export_entry_path_predictions(**kwargs):
        captured.update(kwargs)
        Path(kwargs["output_csv"]).write_text("pred", encoding="utf-8")

    def _fake_export_entry_path_signals(**kwargs):
        captured_signals.update(kwargs)
        Path(kwargs["output_path"]).write_text("sig", encoding="utf-8")
        Path(kwargs["metadata_output"]).write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        watcher,
        "preprocess_online_csv",
        lambda **kwargs: Path(kwargs["output_csv"]).write_text(
            Path(kwargs["input_csv"]).read_text(encoding="utf-8"),
            encoding="utf-8",
        ),
    )
    monkeypatch.setattr(watcher, "export_entry_path_predictions", _fake_export_entry_path_predictions)
    monkeypatch.setattr(watcher, "export_entry_path_signals", _fake_export_entry_path_signals)

    watcher.rebuild_signals(
        input_csv=input_csv,
        runtime_input_snapshot_path=tmp_path / "snapshot.csv",
        runtime_input_preprocessed_path=tmp_path / "preprocessed.csv",
        checkpoint_path=tmp_path / "ckpt.pt",
        predictions_path=tmp_path / "pred.csv",
        rule_path=tmp_path / "rule.json",
        signals_output_path=tmp_path / "signals.csv",
        metadata_output_path=tmp_path / "metadata.json",
        diagnostic_target_signals_per_year=500,
        entry_path_score_threshold_override=None,
        entry_path_diagnostic_all_rows=False,
        watcher_mode="entry_path_v1_live_safe_online",
        batch_size=256,
        max_runtime_rows=100,
    )

    assert captured["task"] == "entry_path_v1"
    assert captured["feature_profile"] == "entry_path_v1_live_safe"
    assert captured["include_true_targets"] is False
    assert captured["vol_regime_24_mode"] == "atr"
    assert captured_signals["diagnostic_only"] is False


def test_rebuild_signals_legacy_mode_uses_runtime_snapshot_for_exports(monkeypatch, tmp_path):
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

    monkeypatch.setattr(
        watcher,
        "preprocess_online_csv",
        lambda **kwargs: Path(kwargs["output_csv"]).write_text(
            Path(kwargs["input_csv"]).read_text(encoding="utf-8"),
            encoding="utf-8",
        ),
    )
    monkeypatch.setattr(watcher, "export_predictions", _fake_export_predictions)
    monkeypatch.setattr(watcher, "export_signals", _fake_export_signals)

    watcher.rebuild_signals(
        input_csv=input_csv,
        runtime_input_snapshot_path=tmp_path / "snapshot.csv",
        runtime_input_preprocessed_path=tmp_path / "preprocessed.csv",
        checkpoint_path=tmp_path / "ckpt.pt",
        predictions_path=tmp_path / "pred.csv",
        rule_path=tmp_path / "rule.json",
        signals_output_path=tmp_path / "signals.csv",
        metadata_output_path=tmp_path / "metadata.json",
        diagnostic_target_signals_per_year=500,
        entry_path_score_threshold_override=None,
        entry_path_diagnostic_all_rows=False,
        watcher_mode="telemetry_frequency_v1_legacy",
        batch_size=256,
        max_runtime_rows=1,
        allow_unsafe_future_features=True,
    )

    preprocessed_path = Path(captured_predictions["input_csv"])
    assert preprocessed_path == tmp_path / "preprocessed.csv"
    assert (tmp_path / "snapshot.csv").read_text(encoding="utf-8").splitlines() == [
        "time;signal;predict",
        "2025.01.01 01:00;-1;-1",
    ]
    assert preprocessed_path.read_text(encoding="utf-8").splitlines() == [
        "time;signal;predict",
        "2025.01.01 01:00;-1;-1",
    ]
    assert Path(captured_signals["base_csv"]) == preprocessed_path
    assert captured_signals["diagnostic_direction_source"] == "fractal0_direction"
    assert captured_signals["append_to_mt4"] is True


def test_rebuild_signals_preprocesses_snapshot_before_inference(monkeypatch, tmp_path):
    captured_predictions: dict[str, object] = {}
    captured_signals: dict[str, object] = {}
    captured_preprocess: dict[str, object] = {}
    input_csv = tmp_path / "Nero.csv"
    input_csv.write_text(
        "time;signal;predict\n"
        "2025.01.01 00:00;1;1\n",
        encoding="utf-8",
    )
    preprocessed_csv = tmp_path / "preprocessed.csv"

    def _fake_preprocess_online_csv(**kwargs):
        captured_preprocess.update(kwargs)
        Path(kwargs["output_csv"]).write_text(
            "time;signal;predict\n2025.01.01 00:00;0;0\n",
            encoding="utf-8",
        )

    def _fake_export_predictions(**kwargs):
        captured_predictions.update(kwargs)
        Path(kwargs["output_path"]).write_text("pred", encoding="utf-8")

    def _fake_export_signals(**kwargs):
        captured_signals.update(kwargs)
        Path(kwargs["output_path"]).write_text("sig", encoding="utf-8")
        Path(kwargs["metadata_output"]).write_text("{}", encoding="utf-8")

    monkeypatch.setattr(watcher, "preprocess_online_csv", _fake_preprocess_online_csv)
    monkeypatch.setattr(watcher, "export_predictions", _fake_export_predictions)
    monkeypatch.setattr(watcher, "export_signals", _fake_export_signals)

    watcher.rebuild_signals(
        input_csv=input_csv,
        runtime_input_snapshot_path=tmp_path / "snapshot.csv",
        runtime_input_preprocessed_path=preprocessed_csv,
        checkpoint_path=tmp_path / "ckpt.pt",
        predictions_path=tmp_path / "pred.csv",
        rule_path=tmp_path / "rule.json",
        signals_output_path=tmp_path / "signals.csv",
        metadata_output_path=tmp_path / "metadata.json",
        diagnostic_target_signals_per_year=500,
        entry_path_score_threshold_override=None,
        entry_path_diagnostic_all_rows=False,
        watcher_mode="telemetry_frequency_v1_legacy",
        batch_size=256,
        max_runtime_rows=100,
        allow_unsafe_future_features=True,
    )

    assert Path(captured_preprocess["input_csv"]) == tmp_path / "snapshot.csv"
    assert Path(captured_preprocess["output_csv"]) == preprocessed_csv
    assert Path(captured_predictions["input_csv"]) == preprocessed_csv
    assert Path(captured_signals["base_csv"]) == preprocessed_csv


def test_rebuild_signals_blocks_unsafe_original_baseline_by_default(monkeypatch, tmp_path):
    input_csv = tmp_path / "Nero.csv"
    input_csv.write_text(
        "time;signal;predict\n"
        "2025.01.01 00:00;1;1\n",
        encoding="utf-8",
    )
    called = {"preprocess": 0, "predictions": 0}

    def _fake_preprocess_online_csv(**kwargs):
        called["preprocess"] += 1

    def _fake_export_predictions(**kwargs):
        called["predictions"] += 1

    monkeypatch.setattr(watcher, "preprocess_online_csv", _fake_preprocess_online_csv)
    monkeypatch.setattr(watcher, "export_predictions", _fake_export_predictions)

    try:
        watcher.rebuild_signals(
            input_csv=input_csv,
            runtime_input_snapshot_path=tmp_path / "snapshot.csv",
            runtime_input_preprocessed_path=tmp_path / "preprocessed.csv",
            checkpoint_path=tmp_path / "ckpt.pt",
            predictions_path=tmp_path / "pred.csv",
            rule_path=tmp_path / "rule.json",
            signals_output_path=tmp_path / "signals.csv",
            metadata_output_path=tmp_path / "metadata.json",
            diagnostic_target_signals_per_year=500,
            entry_path_score_threshold_override=None,
            entry_path_diagnostic_all_rows=False,
            watcher_mode="telemetry_frequency_v1_legacy",
            batch_size=256,
            max_runtime_rows=100,
        )
    except watcher.OnlineInferenceContractError as exc:
        assert "original_baseline" in str(exc)
        assert "future-derived" in str(exc)
    else:
        raise AssertionError("expected OnlineInferenceContractError")

    assert called == {"preprocess": 0, "predictions": 0}


def test_entry_path_contract_forbids_known_future_derived_features():
    forbidden = {"predict", "ret_dir_atr_lag1", "ret_6_dir_atr", "ret_12_dir_atr", "ret_24_dir_atr"}
    forbidden.update({"fav_3_atr", "adv_3_atr", "fav_6_atr", "adv_6_atr", "fav_12_atr", "adv_12_atr"})

    features = set(watcher.live_safe_entry_path_feature_columns())

    assert forbidden.isdisjoint(features)


def test_rebuild_signals_threshold_override_is_diagnostic_only(monkeypatch, tmp_path):
    captured_signals: dict[str, object] = {}
    input_csv = tmp_path / "Nero.csv"
    input_csv.write_text(
        "time;signal;predict\n"
        "2025.01.01 00:00;1;1\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        watcher,
        "preprocess_online_csv",
        lambda **kwargs: Path(kwargs["output_csv"]).write_text(
            Path(kwargs["input_csv"]).read_text(encoding="utf-8"),
            encoding="utf-8",
        ),
    )
    monkeypatch.setattr(
        watcher,
        "export_entry_path_predictions",
        lambda **kwargs: Path(kwargs["output_csv"]).write_text("pred", encoding="utf-8"),
    )

    def _fake_export_entry_path_signals(**kwargs):
        captured_signals.update(kwargs)
        Path(kwargs["output_path"]).write_text("time;signal\n2025.01.01 00:00;1\n", encoding="utf-8")
        Path(kwargs["metadata_output"]).write_text("{}", encoding="utf-8")

    monkeypatch.setattr(watcher, "export_entry_path_signals", _fake_export_entry_path_signals)

    watcher.rebuild_signals(
        input_csv=input_csv,
        runtime_input_snapshot_path=tmp_path / "snapshot.csv",
        runtime_input_preprocessed_path=tmp_path / "preprocessed.csv",
        checkpoint_path=tmp_path / "ckpt.pt",
        predictions_path=tmp_path / "pred.csv",
        rule_path=tmp_path / "rule.json",
        signals_output_path=tmp_path / "signals.csv",
        metadata_output_path=tmp_path / "metadata.json",
        diagnostic_target_signals_per_year=500,
        entry_path_score_threshold_override=-0.5,
        entry_path_diagnostic_all_rows=False,
        watcher_mode="entry_path_v1_live_safe_online",
        batch_size=256,
        max_runtime_rows=100,
    )

    assert captured_signals["score_threshold_override"] == -0.5
    assert captured_signals["diagnostic_all_rows"] is False
    assert "base_csv" not in captured_signals
    assert "diagnostic_direction_source" not in captured_signals
    assert captured_signals["diagnostic_only"] is True
    assert "diagnostic" in captured_signals["label"]


def test_rebuild_signals_entry_path_highfreq_uses_all_rows_diagnostic(monkeypatch, tmp_path):
    captured_signals: dict[str, object] = {}
    input_csv = tmp_path / "Nero.csv"
    input_csv.write_text(
        "time;signal;predict;fractal0\n"
        "2025.01.01 00:00;0;0;1:1:-1:1\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        watcher,
        "preprocess_online_csv",
        lambda **kwargs: Path(kwargs["output_csv"]).write_text(
            Path(kwargs["input_csv"]).read_text(encoding="utf-8"),
            encoding="utf-8",
        ),
    )
    monkeypatch.setattr(
        watcher,
        "export_entry_path_predictions",
        lambda **kwargs: Path(kwargs["output_csv"]).write_text("pred", encoding="utf-8"),
    )

    def _fake_export_entry_path_signals(**kwargs):
        captured_signals.update(kwargs)
        Path(kwargs["output_path"]).write_text("time;signal\n2025.01.01 00:00;1\n", encoding="utf-8")
        Path(kwargs["metadata_output"]).write_text("{}", encoding="utf-8")

    monkeypatch.setattr(watcher, "export_entry_path_signals", _fake_export_entry_path_signals)

    watcher.rebuild_signals(
        input_csv=input_csv,
        runtime_input_snapshot_path=tmp_path / "snapshot.csv",
        runtime_input_preprocessed_path=tmp_path / "preprocessed.csv",
        checkpoint_path=tmp_path / "ckpt.pt",
        predictions_path=tmp_path / "pred.csv",
        rule_path=tmp_path / "rule.json",
        signals_output_path=tmp_path / "signals.csv",
        metadata_output_path=tmp_path / "metadata.json",
        diagnostic_target_signals_per_year=5000,
        entry_path_score_threshold_override=None,
        entry_path_diagnostic_all_rows=True,
        watcher_mode="entry_path_v1_live_safe_online",
        batch_size=256,
        max_runtime_rows=100,
    )

    assert captured_signals["diagnostic_all_rows"] is True
    assert captured_signals["diagnostic_target_signals_per_year"] == 5000
    assert captured_signals["diagnostic_direction_source"] == "fractal0_direction"
    assert captured_signals["diagnostic_only"] is True


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
        runtime_input_preprocessed_path=tmp_path / "preprocessed.csv",
        checkpoint_path=tmp_path / "ckpt.pt",
        rule_path=tmp_path / "rule.json",
        predictions_path=tmp_path / "predictions.csv",
        signals_output_path=tmp_path / "signals.csv",
        metadata_output_path=tmp_path / "metadata.json",
        state_path=state_path,
        diagnostic_target_signals_per_year=500,
        entry_path_score_threshold_override=None,
        entry_path_diagnostic_all_rows=False,
        watcher_mode="entry_path_v1_live_safe_online",
        batch_size=256,
        max_runtime_rows=100,
    )

    assert changed is False
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["last_status"] == "idle"
    assert state["last_processed_time"] == "2025.01.01 00:00"


def test_run_once_skips_without_reading_tail_when_mtime_unchanged(tmp_path, monkeypatch):
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
    monkeypatch.setattr(watcher, "read_last_time", lambda _path: (_ for _ in ()).throw(AssertionError("should not read tail")))
    monkeypatch.setattr(watcher, "rebuild_signals", lambda **kwargs: (_ for _ in ()).throw(AssertionError("should not rebuild")))

    changed = watcher.run_once(
        input_csv=input_csv,
        runtime_input_snapshot_path=tmp_path / "snapshot.csv",
        runtime_input_preprocessed_path=tmp_path / "preprocessed.csv",
        checkpoint_path=tmp_path / "ckpt.pt",
        rule_path=tmp_path / "rule.json",
        predictions_path=tmp_path / "predictions.csv",
        signals_output_path=tmp_path / "signals.csv",
        metadata_output_path=tmp_path / "metadata.json",
        state_path=state_path,
        diagnostic_target_signals_per_year=500,
        entry_path_score_threshold_override=None,
        entry_path_diagnostic_all_rows=False,
        watcher_mode="entry_path_v1_live_safe_online",
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
        runtime_input_preprocessed_path=tmp_path / "preprocessed.csv",
        checkpoint_path=tmp_path / "ckpt.pt",
        rule_path=tmp_path / "rule.json",
        predictions_path=tmp_path / "predictions.csv",
        signals_output_path=tmp_path / "signals.csv",
        metadata_output_path=tmp_path / "metadata.json",
        state_path=state_path,
        diagnostic_target_signals_per_year=500,
        entry_path_score_threshold_override=None,
        entry_path_diagnostic_all_rows=False,
        watcher_mode="entry_path_v1_live_safe_online",
        batch_size=256,
        max_runtime_rows=100,
    )

    assert changed is False
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["last_status"] == "waiting_for_first_row"
