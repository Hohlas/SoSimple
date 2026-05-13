# =============================================================================
# Файл: telemetry_signal_watcher.py
# Назначение: Наблюдаемый watcher online telemetry-контура MT4 -> Nero.csv -> ML -> ml_signals.csv для запуска в tmux.
# Обновлён: 2026-05-13
# Входные данные:
#   - MT/MQL4/Files/Nero.csv (откуда: MT4 expert)
#   - checkpoint.pt для entry_path_v1_live_safe или legacy take_skip diagnostic contour
#   - rule JSON для выбранного watcher mode
# Выходные данные:
#   - preprocessed runtime CSV (куда: ML/reports/entry_path_v1_live_safe/runtime/ или legacy runtime/)
#   - prediction CSV (куда: runtime dir)
#   - ml_signals.csv (куда: MT/MQL4/Files и MT/tester/files)
#   - runtime_input_snapshot.csv (куда: runtime dir)
#   - metadata JSON + state JSON + log
# Использование:
#   python -m API.telemetry_signal_watcher --once
#   python -m API.telemetry_signal_watcher --poll-interval-sec 1 --heartbeat-sec 60 --verbose
# Примечания:
#   - Пересчёт запускается только при появлении нового последнего `time` в Nero.csv.
#   - Перед inference watcher строит runtime snapshot и применяет causal preprocessing:
#     сортировка фракталов по времени + rowwise-нормализация без future labels.
#   - Online MT4 ml_signals.csv публикуется append-only: старые строки не меняются.
#   - Для server-эксплуатации основной режим - отдельное окно tmux с heartbeat в stdout.
#   - Legacy original_baseline online заблокирован contract guard по умолчанию.
# =============================================================================

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from API.export_entry_path_v1_signals import export_signals as export_entry_path_signals
from API.export_take_skip_trailing_stop_v2_signals import export_signals as export_signals
from ML.entry_path_task import ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS
from ML.export_entry_path_predictions import export_predictions as export_entry_path_predictions
from ML.export_take_skip_v2_predictions import export_predictions as export_predictions
from processing.online_causal_preprocessing import preprocess_online_csv


DEFAULT_INPUT_CSV = Path("MT/MQL4/Files/Nero.csv")
DEFAULT_ENTRY_PATH_CHECKPOINT = Path(
    "ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/"
    "transformer_entry_path_v1_features_entry_path_v1_live_safe_best.pt"
)
DEFAULT_ENTRY_PATH_RULE_PATH = Path(
    "ML/reports/mt4_entry_path_v1_live_safe_parity/entry_path_v1_live_safe_a075_rule.json"
)
DEFAULT_LEGACY_CHECKPOINT = Path("ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/checkpoint.pt")
DEFAULT_LEGACY_RULE_PATH = Path("ML/reports/telemetry_frequency_v1/calibration/selected_rule.json")
DEFAULT_CHECKPOINT = DEFAULT_ENTRY_PATH_CHECKPOINT
DEFAULT_RULE_PATH = DEFAULT_ENTRY_PATH_RULE_PATH
DEFAULT_OUTPUT_DIR = Path("ML/reports/entry_path_v1_live_safe/runtime")
DEFAULT_PREDICTIONS_PATH = DEFAULT_OUTPUT_DIR / "runtime_predictions.csv"
DEFAULT_SIGNALS_PATH = DEFAULT_OUTPUT_DIR / "runtime_ml_signals.csv"
DEFAULT_METADATA_PATH = DEFAULT_OUTPUT_DIR / "runtime_export_metadata.json"
DEFAULT_STATE_PATH = DEFAULT_OUTPUT_DIR / "runtime_state.json"
DEFAULT_LOG_PATH = DEFAULT_OUTPUT_DIR / "telemetry_signal_watcher.log"
DEFAULT_RUNTIME_INPUT_SNAPSHOT = DEFAULT_OUTPUT_DIR / "runtime_input_snapshot.csv"
DEFAULT_RUNTIME_INPUT_PREPROCESSED = DEFAULT_OUTPUT_DIR / "runtime_input_preprocessed.csv"
ENTRY_PATH_RUNTIME_REQUIRED_HISTORY_ROWS = 1
DEFAULT_MAX_RUNTIME_ROWS = ENTRY_PATH_RUNTIME_REQUIRED_HISTORY_ROWS
WATCHER_MODE_ENTRY_PATH = "entry_path_v1_live_safe_online"
WATCHER_MODE_LEGACY_TELEMETRY = "telemetry_frequency_v1_legacy"
UNSAFE_ORIGINAL_BASELINE_ROW_FEATURES = (
    "predict",
    "ret_dir_atr_lag1",
    "ret_6_dir_atr",
    "ret_12_dir_atr",
    "ret_24_dir_atr",
    "fav_3_atr",
    "adv_3_atr",
    "fav_6_atr",
    "adv_6_atr",
    "fav_12_atr",
    "adv_12_atr",
    "fav_24_atr",
    "adv_24_atr",
)


class OnlineInferenceContractError(RuntimeError):
    """Raised when an online model contract needs future-derived fields."""


@dataclass
class WatcherState:
    last_processed_time: str = ""
    source_mtime_ns: int = 0
    updated_at_unix: int = 0
    last_status: str = ""


@dataclass(frozen=True)
class ModePaths:
    checkpoint_path: Path
    rule_path: Path
    max_runtime_rows: int


DEFAULT_ENTRY_PATH_MAX_RUNTIME_ROWS = ENTRY_PATH_RUNTIME_REQUIRED_HISTORY_ROWS
DEFAULT_LEGACY_MAX_RUNTIME_ROWS = DEFAULT_MAX_RUNTIME_ROWS


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


def live_safe_entry_path_feature_columns() -> tuple[str, ...]:
    return tuple(ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS)


def resolve_mode_paths(args: argparse.Namespace) -> ModePaths:
    watcher_mode = str(args.watcher_mode)
    if watcher_mode == WATCHER_MODE_ENTRY_PATH:
        default_checkpoint = DEFAULT_ENTRY_PATH_CHECKPOINT
        default_rule = DEFAULT_ENTRY_PATH_RULE_PATH
        default_rows = DEFAULT_ENTRY_PATH_MAX_RUNTIME_ROWS
    elif watcher_mode == WATCHER_MODE_LEGACY_TELEMETRY:
        default_checkpoint = DEFAULT_LEGACY_CHECKPOINT
        default_rule = DEFAULT_LEGACY_RULE_PATH
        default_rows = DEFAULT_LEGACY_MAX_RUNTIME_ROWS
    else:
        raise ValueError(f"unsupported watcher_mode: {watcher_mode}")

    return ModePaths(
        checkpoint_path=Path(args.checkpoint) if args.checkpoint else default_checkpoint,
        rule_path=Path(args.rule_path) if args.rule_path else default_rule,
        max_runtime_rows=int(args.max_runtime_rows) if args.max_runtime_rows is not None else int(default_rows),
    )


def _read_csv_header(input_csv: Path) -> str | None:
    with input_csv.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if line:
                return line
    return None


def read_csv_tail_lines(
    input_csv: Path,
    *,
    max_data_rows: int,
    initial_block_size: int = 64 * 1024,
) -> tuple[str | None, list[str]]:
    """Reads CSV header and last non-empty data rows without scanning the full file."""
    if max_data_rows <= 0:
        raise ValueError("max_data_rows must be positive")
    if initial_block_size <= 0:
        raise ValueError("initial_block_size must be positive")

    header = _read_csv_header(input_csv)
    if header is None:
        return None, []

    file_size = input_csv.stat().st_size
    window_size = int(initial_block_size)
    rows: list[str] = []

    with input_csv.open("rb") as handle:
        while True:
            offset = max(0, file_size - window_size)
            handle.seek(offset)
            chunk = handle.read()
            lines = chunk.decode("utf-8", errors="replace").splitlines()
            non_empty = [line.strip() for line in lines if line.strip()]
            if offset > 0 and non_empty:
                non_empty = non_empty[1:]
            if offset == 0 and non_empty and non_empty[0] == header:
                non_empty = non_empty[1:]
            rows = non_empty[-max_data_rows:]
            if len(rows) >= max_data_rows or offset == 0:
                break
            window_size *= 2

    return header, rows[-max_data_rows:]


def read_last_time(input_csv: Path) -> str | None:
    _, rows = read_csv_tail_lines(input_csv, max_data_rows=1)
    if not rows:
        return None
    return rows[-1].split(";", 1)[0]


def build_runtime_input_snapshot(*, input_csv: Path, snapshot_csv: Path, max_rows: int) -> int:
    header, tail_rows = read_csv_tail_lines(input_csv, max_data_rows=max_rows)

    if header is None:
        raise ValueError(f"{input_csv} is missing CSV header")

    snapshot_csv.parent.mkdir(parents=True, exist_ok=True)
    with snapshot_csv.open("w", encoding="utf-8") as handle:
        handle.write(header + "\n")
        for row in tail_rows:
            handle.write(row + "\n")
    return len(tail_rows)


def should_rebuild(*, current_last_time: str, source_mtime_ns: int, state: WatcherState) -> bool:
    if current_last_time != state.last_processed_time:
        return True
    if source_mtime_ns != state.source_mtime_ns:
        return True
    return False


def validate_online_inference_contract(
    *,
    mode: str,
    feature_mode: str,
    allow_unsafe_future_features: bool = False,
) -> None:
    if allow_unsafe_future_features:
        logging.warning(
            "WATCHER unsafe online contract override enabled: mode=%s feature_mode=%s",
            mode,
            feature_mode,
        )
        return
    if mode == "original_contour" and feature_mode == "original_baseline":
        fields = ", ".join(UNSAFE_ORIGINAL_BASELINE_ROW_FEATURES)
        raise OnlineInferenceContractError(
            "original_contour/original_baseline is blocked for online inference: "
            "the training/test input contract includes future-derived row features "
            f"that live Nero.csv cannot know ({fields}). Retrain with a live-safe "
            "feature set before using this watcher for ML-correct online checks."
        )


def rebuild_legacy_telemetry_signals(
    *,
    runtime_input_preprocessed_path: Path,
    checkpoint_path: Path,
    predictions_path: Path,
    rule_path: Path,
    signals_output_path: Path,
    metadata_output_path: Path,
    diagnostic_target_signals_per_year: int,
    batch_size: int,
) -> None:
    export_predictions(
        input_csv=runtime_input_preprocessed_path,
        checkpoint_path=checkpoint_path,
        output_path=predictions_path,
        mode="original_contour",
        seq_len=50,
        feature_mode="original_baseline",
        include_true_targets=False,
        batch_size=batch_size,
    )
    export_signals(
        predictions_path=predictions_path,
        rule_path=rule_path,
        output_path=signals_output_path,
        base_csv=runtime_input_preprocessed_path,
        copy_to_mt4=True,
        metadata_output=metadata_output_path,
        label="telemetry_frequency_v1_online",
        diagnostic_all_rows=True,
        diagnostic_direction_source="fractal0_direction",
        diagnostic_target_signals_per_year=diagnostic_target_signals_per_year,
        append_to_mt4=True,
    )


def rebuild_entry_path_live_safe_signals(
    *,
    runtime_input_preprocessed_path: Path,
    checkpoint_path: Path,
    predictions_path: Path,
    rule_path: Path,
    signals_output_path: Path,
    metadata_output_path: Path,
    diagnostic_target_signals_per_year: int,
    batch_size: int,
    score_threshold_override: float | None,
    diagnostic_all_rows: bool,
) -> None:
    diagnostic_only = score_threshold_override is not None or diagnostic_all_rows
    label = (
        "entry_path_v1_live_safe_highfreq_diagnostic"
        if diagnostic_only
        else "entry_path_v1_live_safe_online"
    )
    diagnostic_reason = (
        "Diagnostic-only threshold override. Same checkpoint/rule/gate/direction as production; "
        "do not use this run as profitability evidence. Production baseline remains A @ 7.5%."
        if score_threshold_override is not None
        else "Mechanical stress mode, not production parity: ignores signal gate and uses fractal0.direction. Do not use this run as profitability evidence; production baseline remains A @ 7.5%."
        if diagnostic_all_rows
        else ""
    )
    export_entry_path_predictions(
        input_csv=runtime_input_preprocessed_path,
        checkpoint=checkpoint_path,
        output_csv=predictions_path,
        task="entry_path_v1",
        batch_size=batch_size,
        num_workers=0,
        feature_profile="entry_path_v1_live_safe",
        include_true_targets=False,
        vol_regime_24_mode="atr",
    )
    export_kwargs = {
        "predictions_path": predictions_path,
        "rule_path": rule_path,
        "output_path": signals_output_path,
        "copy_to_mt4": True,
        "append_to_mt4": True,
        "metadata_output": metadata_output_path,
        "label": label,
        "score_threshold_override": score_threshold_override,
        "diagnostic_all_rows": diagnostic_all_rows,
        "diagnostic_only": diagnostic_only,
        "diagnostic_reason": diagnostic_reason,
    }
    if diagnostic_all_rows:
        export_kwargs.update(
            {
                "base_csv": runtime_input_preprocessed_path,
                "diagnostic_target_signals_per_year": diagnostic_target_signals_per_year,
                "diagnostic_direction_source": "fractal0_direction",
            }
        )
    export_entry_path_signals(**export_kwargs)


def rebuild_signals(
    *,
    input_csv: Path,
    runtime_input_snapshot_path: Path,
    runtime_input_preprocessed_path: Path,
    checkpoint_path: Path,
    predictions_path: Path,
    rule_path: Path,
    signals_output_path: Path,
    metadata_output_path: Path,
    diagnostic_target_signals_per_year: int,
    entry_path_score_threshold_override: float | None,
    entry_path_diagnostic_all_rows: bool,
    watcher_mode: str,
    batch_size: int,
    max_runtime_rows: int,
    allow_unsafe_future_features: bool = False,
) -> None:
    if watcher_mode == WATCHER_MODE_LEGACY_TELEMETRY:
        validate_online_inference_contract(
            mode="original_contour",
            feature_mode="original_baseline",
            allow_unsafe_future_features=allow_unsafe_future_features,
        )
    elif watcher_mode != WATCHER_MODE_ENTRY_PATH:
        raise ValueError(f"unsupported watcher_mode: {watcher_mode}")

    snapshot_rows = build_runtime_input_snapshot(
        input_csv=input_csv,
        snapshot_csv=runtime_input_snapshot_path,
        max_rows=max_runtime_rows,
    )
    if snapshot_rows <= 0:
        raise ValueError(f"{input_csv} contains no data rows for runtime snapshot")

    preprocess_online_csv(
        input_csv=runtime_input_snapshot_path,
        output_csv=runtime_input_preprocessed_path,
    )

    if watcher_mode == WATCHER_MODE_LEGACY_TELEMETRY:
        rebuild_legacy_telemetry_signals(
            runtime_input_preprocessed_path=runtime_input_preprocessed_path,
            checkpoint_path=checkpoint_path,
            predictions_path=predictions_path,
            rule_path=rule_path,
            signals_output_path=signals_output_path,
            metadata_output_path=metadata_output_path,
            diagnostic_target_signals_per_year=diagnostic_target_signals_per_year,
            batch_size=batch_size,
        )
    else:
        rebuild_entry_path_live_safe_signals(
            runtime_input_preprocessed_path=runtime_input_preprocessed_path,
            checkpoint_path=checkpoint_path,
            predictions_path=predictions_path,
            rule_path=rule_path,
            signals_output_path=signals_output_path,
            metadata_output_path=metadata_output_path,
            diagnostic_target_signals_per_year=diagnostic_target_signals_per_year,
            batch_size=batch_size,
            score_threshold_override=entry_path_score_threshold_override,
            diagnostic_all_rows=entry_path_diagnostic_all_rows,
        )


def run_once(
    *,
    input_csv: Path,
    runtime_input_snapshot_path: Path,
    runtime_input_preprocessed_path: Path,
    checkpoint_path: Path,
    rule_path: Path,
    predictions_path: Path,
    signals_output_path: Path,
    metadata_output_path: Path,
    state_path: Path,
    diagnostic_target_signals_per_year: int,
    entry_path_score_threshold_override: float | None,
    entry_path_diagnostic_all_rows: bool,
    watcher_mode: str,
    batch_size: int,
    max_runtime_rows: int,
    allow_unsafe_future_features: bool = False,
) -> bool:
    state = load_state(state_path)
    source_mtime_ns = input_csv.stat().st_mtime_ns
    if state.last_processed_time and source_mtime_ns == state.source_mtime_ns:
        idle_state = WatcherState(
            last_processed_time=state.last_processed_time,
            source_mtime_ns=source_mtime_ns,
            updated_at_unix=int(time.time()),
            last_status="idle",
        )
        save_state(state_path, idle_state)
        return False

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
        runtime_input_snapshot_path=runtime_input_snapshot_path,
        runtime_input_preprocessed_path=runtime_input_preprocessed_path,
        checkpoint_path=checkpoint_path,
        predictions_path=predictions_path,
        rule_path=rule_path,
        signals_output_path=signals_output_path,
        metadata_output_path=metadata_output_path,
        diagnostic_target_signals_per_year=diagnostic_target_signals_per_year,
        entry_path_score_threshold_override=entry_path_score_threshold_override,
        entry_path_diagnostic_all_rows=entry_path_diagnostic_all_rows,
        watcher_mode=watcher_mode,
        batch_size=batch_size,
        max_runtime_rows=max_runtime_rows,
        allow_unsafe_future_features=allow_unsafe_future_features,
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
    parser.add_argument(
        "--watcher-mode",
        choices=[WATCHER_MODE_ENTRY_PATH, WATCHER_MODE_LEGACY_TELEMETRY],
        default=WATCHER_MODE_ENTRY_PATH,
    )
    parser.add_argument("--input-csv", default=str(DEFAULT_INPUT_CSV))
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--rule-path", default=None)
    parser.add_argument("--predictions-output", default=str(DEFAULT_PREDICTIONS_PATH))
    parser.add_argument("--signals-output", default=str(DEFAULT_SIGNALS_PATH))
    parser.add_argument("--metadata-output", default=str(DEFAULT_METADATA_PATH))
    parser.add_argument("--state-path", default=str(DEFAULT_STATE_PATH))
    parser.add_argument("--log-path", default=str(DEFAULT_LOG_PATH))
    parser.add_argument("--runtime-input-snapshot", default=str(DEFAULT_RUNTIME_INPUT_SNAPSHOT))
    parser.add_argument("--runtime-input-preprocessed", default=str(DEFAULT_RUNTIME_INPUT_PREPROCESSED))
    parser.add_argument("--poll-interval-sec", type=int, default=1)
    parser.add_argument("--heartbeat-sec", type=int, default=60)
    parser.add_argument("--max-runtime-rows", type=int, default=None)
    parser.add_argument("--diagnostic-target-signals-per-year", type=int, default=500)
    parser.add_argument(
        "--entry-path-diagnostic-all-rows",
        action="store_true",
        help=(
            "Mechanical stress mode, not production parity: ignore production signal!=0 gate "
            "and pick top-N rows per year by entry_path score, with direction from fractal0.direction."
        ),
    )
    parser.add_argument(
        "--entry-path-score-threshold-override",
        type=float,
        default=None,
        help=(
            "Diagnostic-only threshold override for entry_path_v1_live_safe. "
            "Production baseline remains the frozen A @ 7.5%% rule."
        ),
    )
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument(
        "--allow-unsafe-future-features",
        action="store_true",
        help=(
            "Explicitly bypass online contract guard for legacy diagnostics. "
            "Do not use for ML-correct online validation."
        ),
    )
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(Path(args.log_path), verbose=bool(args.verbose))
    resolved = resolve_mode_paths(args)

    input_csv = Path(args.input_csv)
    checkpoint_path = resolved.checkpoint_path
    rule_path = resolved.rule_path
    runtime_input_snapshot_path = Path(args.runtime_input_snapshot)
    runtime_input_preprocessed_path = Path(args.runtime_input_preprocessed)
    predictions_path = Path(args.predictions_output)
    signals_output_path = Path(args.signals_output)
    metadata_output_path = Path(args.metadata_output)
    state_path = Path(args.state_path)

    if args.once:
        run_once(
            input_csv=input_csv,
            runtime_input_snapshot_path=runtime_input_snapshot_path,
            runtime_input_preprocessed_path=runtime_input_preprocessed_path,
            checkpoint_path=checkpoint_path,
            rule_path=rule_path,
            predictions_path=predictions_path,
            signals_output_path=signals_output_path,
            metadata_output_path=metadata_output_path,
            state_path=state_path,
            diagnostic_target_signals_per_year=int(args.diagnostic_target_signals_per_year),
            entry_path_score_threshold_override=args.entry_path_score_threshold_override,
            entry_path_diagnostic_all_rows=bool(args.entry_path_diagnostic_all_rows),
            watcher_mode=str(args.watcher_mode),
            batch_size=int(args.batch_size),
            max_runtime_rows=resolved.max_runtime_rows,
            allow_unsafe_future_features=bool(args.allow_unsafe_future_features),
        )
        return 0

    last_heartbeat_at = 0.0
    while True:
        try:
            run_once(
                input_csv=input_csv,
                runtime_input_snapshot_path=runtime_input_snapshot_path,
                runtime_input_preprocessed_path=runtime_input_preprocessed_path,
                checkpoint_path=checkpoint_path,
                rule_path=rule_path,
                predictions_path=predictions_path,
                signals_output_path=signals_output_path,
                metadata_output_path=metadata_output_path,
                state_path=state_path,
                diagnostic_target_signals_per_year=int(args.diagnostic_target_signals_per_year),
                entry_path_score_threshold_override=args.entry_path_score_threshold_override,
                entry_path_diagnostic_all_rows=bool(args.entry_path_diagnostic_all_rows),
                watcher_mode=str(args.watcher_mode),
                batch_size=int(args.batch_size),
                max_runtime_rows=resolved.max_runtime_rows,
                allow_unsafe_future_features=bool(args.allow_unsafe_future_features),
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
