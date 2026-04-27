# =============================================================================
# Файл: telemetry_signal_watcher.py
# Назначение: Наблюдаемый watcher online telemetry-контура MT4 -> Nero.csv -> ML -> ml_signals.csv для запуска в tmux.
# Обновлён: 2026-04-27
# Входные данные:
#   - MT/MQL4/Files/Nero.csv (откуда: MT4 expert)
#   - checkpoint.pt для take_skip_v2 contour (откуда: ML/reports/*/checkpoint.pt)
#   - telemetry rule JSON (откуда: ML/reports/telemetry_frequency_v1/calibration/selected_rule.json)
# Выходные данные:
#   - prediction CSV (куда: ML/reports/telemetry_frequency_v1/runtime/)
#   - ml_signals.csv (куда: MT/MQL4/Files и MT/tester/files)
#   - metadata JSON + state JSON + log
# Использование:
#   python -m API.telemetry_signal_watcher --once
#   python -m API.telemetry_signal_watcher --poll-interval-sec 10 --heartbeat-sec 30 --verbose
# Примечания:
#   - Пересчёт запускается только при появлении нового последнего `time` в Nero.csv.
#   - Готовый ml_signals.csv пишется атомарно через существующий exporter.
#   - Для server-эксплуатации основной режим - отдельное окно tmux с heartbeat в stdout.
# =============================================================================

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from API.export_take_skip_trailing_stop_v2_signals import export_signals
from ML.export_take_skip_v2_predictions import export_predictions


DEFAULT_INPUT_CSV = Path("MT/MQL4/Files/Nero.csv")
DEFAULT_CHECKPOINT = Path("ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/checkpoint.pt")
DEFAULT_RULE_PATH = Path("ML/reports/telemetry_frequency_v1/calibration/selected_rule.json")
DEFAULT_OUTPUT_DIR = Path("ML/reports/telemetry_frequency_v1/runtime")
DEFAULT_PREDICTIONS_PATH = DEFAULT_OUTPUT_DIR / "runtime_predictions.csv"
DEFAULT_SIGNALS_PATH = DEFAULT_OUTPUT_DIR / "runtime_ml_signals.csv"
DEFAULT_METADATA_PATH = DEFAULT_OUTPUT_DIR / "runtime_export_metadata.json"
DEFAULT_STATE_PATH = DEFAULT_OUTPUT_DIR / "runtime_state.json"
DEFAULT_LOG_PATH = DEFAULT_OUTPUT_DIR / "telemetry_signal_watcher.log"


@dataclass
class WatcherState:
    last_processed_time: str = ""
    source_mtime_ns: int = 0
    updated_at_unix: int = 0
    last_status: str = ""


def configure_logging(log_path: Path, verbose: bool) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [logging.FileHandler(log_path, encoding="utf-8")]
    if verbose:
        handlers.append(logging.StreamHandler(sys.stdout))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=handlers,
        force=True,
    )


def load_state(path: Path) -> WatcherState:
    if not path.exists():
        return WatcherState()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return WatcherState(
        last_processed_time=str(payload.get("last_processed_time", "")),
        source_mtime_ns=int(payload.get("source_mtime_ns", 0)),
        updated_at_unix=int(payload.get("updated_at_unix", 0)),
        last_status=str(payload.get("last_status", "")),
    )


def save_state(path: Path, state: WatcherState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8")


def format_heartbeat_message(state: WatcherState, *, input_csv: Path) -> str:
    status_map = {
        "waiting_for_first_row": "WAIT",
        "idle": "IDLE",
        "rebuilt": "REBUILT",
    }
    label = status_map.get(state.last_status, state.last_status.upper() or "UNKNOWN")
    parts = [f"WATCHER HEARTBEAT: status={label}"]
    if state.last_processed_time:
        parts.append(f"last_bar={state.last_processed_time}")
    parts.append(f"input={input_csv}")
    return " ".join(parts)


def read_last_time(input_csv: Path) -> str | None:
    frame = pd.read_csv(input_csv, sep=";", usecols=["time"], dtype={"time": str}, low_memory=False)
    if frame.empty:
        return None
    return str(frame.iloc[-1]["time"])


def should_rebuild(*, current_last_time: str, source_mtime_ns: int, state: WatcherState) -> bool:
    if current_last_time != state.last_processed_time:
        return True
    if source_mtime_ns != state.source_mtime_ns:
        return True
    return False


def rebuild_signals(
    *,
    input_csv: Path,
    checkpoint_path: Path,
    predictions_path: Path,
    rule_path: Path,
    signals_output_path: Path,
    metadata_output_path: Path,
    diagnostic_target_signals_per_year: int,
    batch_size: int,
) -> None:
    export_predictions(
        input_csv=input_csv,
        checkpoint_path=checkpoint_path,
        output_path=predictions_path,
        mode="plain_transformer",
        seq_len=50,
        include_true_targets=False,
        batch_size=batch_size,
    )
    export_signals(
        predictions_path=predictions_path,
        rule_path=rule_path,
        output_path=signals_output_path,
        base_csv=input_csv,
        copy_to_mt4=True,
        metadata_output=metadata_output_path,
        label="telemetry_frequency_v1_online",
        diagnostic_all_rows=True,
        diagnostic_target_signals_per_year=diagnostic_target_signals_per_year,
    )


def run_once(
    *,
    input_csv: Path,
    checkpoint_path: Path,
    rule_path: Path,
    predictions_path: Path,
    signals_output_path: Path,
    metadata_output_path: Path,
    state_path: Path,
    diagnostic_target_signals_per_year: int,
    batch_size: int,
) -> bool:
    state = load_state(state_path)
    source_mtime_ns = input_csv.stat().st_mtime_ns
    current_last_time = read_last_time(input_csv)

    if current_last_time is None:
        waiting_state = WatcherState(
            last_processed_time="",
            source_mtime_ns=source_mtime_ns,
            updated_at_unix=int(time.time()),
            last_status="waiting_for_first_row",
        )
        save_state(state_path, waiting_state)
        return False

    if not should_rebuild(
        current_last_time=current_last_time,
        source_mtime_ns=source_mtime_ns,
        state=state,
    ):
        idle_state = WatcherState(
            last_processed_time=current_last_time,
            source_mtime_ns=source_mtime_ns,
            updated_at_unix=int(time.time()),
            last_status="idle",
        )
        save_state(state_path, idle_state)
        return False

    logging.info("WATCHER rebuild start: time=%s input=%s", current_last_time, input_csv)
    rebuild_signals(
        input_csv=input_csv,
        checkpoint_path=checkpoint_path,
        predictions_path=predictions_path,
        rule_path=rule_path,
        signals_output_path=signals_output_path,
        metadata_output_path=metadata_output_path,
        diagnostic_target_signals_per_year=diagnostic_target_signals_per_year,
        batch_size=batch_size,
    )
    new_state = WatcherState(
        last_processed_time=current_last_time,
        source_mtime_ns=source_mtime_ns,
        updated_at_unix=int(time.time()),
        last_status="rebuilt",
    )
    save_state(state_path, new_state)
    logging.info("WATCHER rebuild done: time=%s signals=%s", current_last_time, signals_output_path)
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Observable watcher for telemetry MT4 -> Nero.csv -> ML -> ml_signals.csv.")
    parser.add_argument("--input-csv", default=str(DEFAULT_INPUT_CSV))
    parser.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    parser.add_argument("--rule-path", default=str(DEFAULT_RULE_PATH))
    parser.add_argument("--predictions-output", default=str(DEFAULT_PREDICTIONS_PATH))
    parser.add_argument("--signals-output", default=str(DEFAULT_SIGNALS_PATH))
    parser.add_argument("--metadata-output", default=str(DEFAULT_METADATA_PATH))
    parser.add_argument("--state-path", default=str(DEFAULT_STATE_PATH))
    parser.add_argument("--log-path", default=str(DEFAULT_LOG_PATH))
    parser.add_argument("--poll-interval-sec", type=int, default=10)
    parser.add_argument("--heartbeat-sec", type=int, default=30)
    parser.add_argument("--diagnostic-target-signals-per-year", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(Path(args.log_path), verbose=bool(args.verbose))

    input_csv = Path(args.input_csv)
    checkpoint_path = Path(args.checkpoint)
    rule_path = Path(args.rule_path)
    predictions_path = Path(args.predictions_output)
    signals_output_path = Path(args.signals_output)
    metadata_output_path = Path(args.metadata_output)
    state_path = Path(args.state_path)

    if args.once:
        run_once(
            input_csv=input_csv,
            checkpoint_path=checkpoint_path,
            rule_path=rule_path,
            predictions_path=predictions_path,
            signals_output_path=signals_output_path,
            metadata_output_path=metadata_output_path,
            state_path=state_path,
            diagnostic_target_signals_per_year=int(args.diagnostic_target_signals_per_year),
            batch_size=int(args.batch_size),
        )
        return 0

    last_heartbeat_at = 0.0
    while True:
        try:
            run_once(
                input_csv=input_csv,
                checkpoint_path=checkpoint_path,
                rule_path=rule_path,
                predictions_path=predictions_path,
                signals_output_path=signals_output_path,
                metadata_output_path=metadata_output_path,
                state_path=state_path,
                diagnostic_target_signals_per_year=int(args.diagnostic_target_signals_per_year),
                batch_size=int(args.batch_size),
            )
            now = time.time()
            if now - last_heartbeat_at >= max(1, int(args.heartbeat_sec)):
                state = load_state(state_path)
                logging.info(format_heartbeat_message(state, input_csv=input_csv))
                last_heartbeat_at = now
        except Exception as exc:
            logging.exception("WATCHER error: %s", exc)
        time.sleep(max(1, int(args.poll_interval_sec)))


if __name__ == "__main__":
    raise SystemExit(main())
