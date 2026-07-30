from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from ML.baseline.mt5_signal_schema import MT5_SIGNAL_COLUMNS
from ML.baseline.mt5_signal_schema import validate_mt5_signal_frame

DEFAULT_REPORT_DIR = Path("ML/reports/mt5_execution_loop")
FORBIDDEN_SOURCE_COLUMNS = {
    "fill_time",
    "exit_time",
    "future_exit_time",
    "future_favorable_r_3",
    "future_adverse_r_3",
    "hold_3_pnl_r",
    "pnl_r",
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stable_json_hash(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(encoded)


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _read_csv_hash(frame: pd.DataFrame) -> str:
    serialized = frame.to_csv(sep=";", index=False).encode("utf-8")
    return _sha256_bytes(serialized)


def _require_column(source: pd.DataFrame, candidates: list[str], *, label: str) -> pd.Series:
    for candidate in candidates:
        if candidate in source.columns:
            return source[candidate]
    available = ", ".join(candidates)
    raise ValueError(f"missing {label} column; expected one of: {available}")


def _coerce_rule_metadata(
    rule_metadata: dict[str, Any] | str | Path | None,
) -> tuple[dict[str, Any] | None, str | None, str | None]:
    if rule_metadata is None:
        return None, None, None

    if isinstance(rule_metadata, (str, Path)):
        path = Path(rule_metadata)
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".csv":
            payload = {
                "kind": "selected_rule_csv",
                "path": str(path),
                "sha256": _sha256_bytes(text.encode("utf-8")),
                "rows": int(len(pd.read_csv(path, sep=";"))),
            }
        else:
            payload = json.loads(text)
            if not isinstance(payload, dict):
                raise ValueError("rule metadata file must contain a JSON object")
            payload = dict(payload)
            payload.setdefault("path", str(path))
        return payload, str(path), _stable_json_hash(payload)

    payload = dict(rule_metadata)
    return payload, None, _stable_json_hash(payload)


def _build_export_frame(source: pd.DataFrame, *, max_fill_lag_bars: int) -> pd.DataFrame:
    side = _require_column(source, ["side"], label="side").astype(str).str.upper().str.strip()
    entry_type = side.map({"BUY": "BUY_LIMIT", "SELL": "SELL_LIMIT"})

    export = pd.DataFrame(
        {
            "time": _require_column(source, ["time"], label="time").astype(str),
            "feature_time": _require_column(source, ["feature_time"], label="feature_time").astype(str),
            "feature_available_time": _require_column(
                source,
                ["feature_available_time"],
                label="feature_available_time",
            ).astype(str),
            "decision_time": _require_column(source, ["decision_time"], label="decision_time").astype(str),
            "rule_id": _require_column(source, ["rule_id"], label="rule_id").astype(str)
            if "rule_id" in source.columns
            else "rule01",
            "side": side,
            "entry_type": entry_type.astype(str),
            "limit_price": pd.to_numeric(_require_column(source, ["limit_price"], label="limit_price"), errors="raise"),
            "stop_price": pd.to_numeric(
                _require_column(
                    source,
                    ["stop_price", "protective_stop_price"],
                    label="stop_price",
                ),
                errors="raise",
            ),
            "atr": pd.to_numeric(_require_column(source, ["atr", "ATR"], label="atr"), errors="raise"),
            "max_fill_lag_bars": int(max_fill_lag_bars),
        }
    )

    if export["rule_id"].eq("rule01").all() and "rule_id" in source.columns:
        export["rule_id"] = source["rule_id"].astype(str)

    export = export[MT5_SIGNAL_COLUMNS].copy()
    validate_mt5_signal_frame(export)
    return export


def _build_metadata(
    *,
    source: pd.DataFrame,
    export: pd.DataFrame,
    output_csv: Path,
    output_json: Path,
    max_fill_lag_bars: int,
    source_csv: str | Path | None,
    rule_metadata: dict[str, Any] | None,
    rule_metadata_path: str | None,
    rule_metadata_sha256: str | None,
    run_id: str | None,
    label: str,
) -> dict[str, Any]:
    side = export["side"].astype(str)
    time_counts = export["time"].astype(str).value_counts()
    opposite_groups = 0
    if not export.empty:
        by_time = export.groupby("time")["side"].nunique()
        opposite_groups = int((by_time > 1).sum())

    source_hash = None
    source_path_str = None
    if source_csv is not None:
        source_path = Path(source_csv)
        source_path_str = str(source_path)
        source_hash = _sha256_file(source_path)
    else:
        source_hash = _read_csv_hash(source)

    run_config = {
        "label": label,
        "run_id": run_id,
        "max_fill_lag_bars": int(max_fill_lag_bars),
        "columns": MT5_SIGNAL_COLUMNS,
        "rule_metadata_sha256": rule_metadata_sha256,
        "source_csv_sha256": source_hash,
    }
    metadata = {
        "label": label,
        "status": "DIAGNOSTIC_ONLY",
        "run_id": run_id,
        "rows_total": int(len(export)),
        "active_signal_rows": int(side.isin(["BUY", "SELL"]).sum()),
        "nonzero_rows": int(side.ne("").sum()),
        "buy_rows": int(side.eq("BUY").sum()),
        "sell_rows": int(side.eq("SELL").sum()),
        "unique_time_rows": int(export["time"].nunique()),
        "duplicate_time_rows": int(len(export) - export["time"].nunique()),
        "unique_time_side_rows": int(export.drop_duplicates(subset=["time", "side"]).shape[0]),
        "same_time_opposite_signal_groups": opposite_groups,
        "side_counts": side.value_counts().to_dict(),
        "source_csv": source_path_str,
        "source_csv_sha256": source_hash,
        "rule_metadata": rule_metadata,
        "rule_metadata_path": rule_metadata_path,
        "rule_metadata_sha256": rule_metadata_sha256,
        "run_config_hash": _stable_json_hash(run_config),
        "run_config": run_config,
        "output_csv": str(output_csv),
        "output_csv_sha256": _sha256_file(output_csv),
        "output_json": str(output_json),
        "forbidden_source_columns": sorted(set(source.columns).intersection(FORBIDDEN_SOURCE_COLUMNS)),
        "forbidden_future_lifecycle_columns_removed": True,
        "exported_columns": list(export.columns),
    }
    return metadata


def export_mt5_entry_signals(
    source: pd.DataFrame,
    output_csv: str | Path,
    output_json: str | Path,
    max_fill_lag_bars: int,
    *,
    source_csv: str | Path | None = None,
    rule_metadata: dict[str, Any] | str | Path | None = None,
    run_id: str | None = None,
    label: str = "mt5_execution_loop",
) -> pd.DataFrame:
    export = _build_export_frame(source, max_fill_lag_bars=max_fill_lag_bars)

    output_csv_path = Path(output_csv)
    output_json_path = Path(output_json)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(output_csv_path, sep=";", index=False)

    rule_payload, rule_metadata_path, rule_metadata_sha256 = _coerce_rule_metadata(rule_metadata)
    metadata = _build_metadata(
        source=source,
        export=export,
        output_csv=output_csv_path,
        output_json=output_json_path,
        max_fill_lag_bars=max_fill_lag_bars,
        source_csv=source_csv,
        rule_metadata=rule_payload,
        rule_metadata_path=rule_metadata_path,
        rule_metadata_sha256=rule_metadata_sha256,
        run_id=run_id,
        label=label,
    )
    output_json_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return export


def _resolve_output_paths(run_id: str) -> tuple[Path, Path]:
    output_csv = DEFAULT_REPORT_DIR / f"mt5_entry_signals_{run_id}.csv"
    output_json = DEFAULT_REPORT_DIR / f"mt5_entry_signals_{run_id}.json"
    return output_csv, output_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export entry-only MT5 signals and diagnostic metadata.")
    parser.add_argument("--source-csv", "--input-csv", dest="source_csv", required=True)
    parser.add_argument("--output-csv", dest="output_csv", default=None)
    parser.add_argument("--output-json", dest="output_json", default=None)
    parser.add_argument("--rule-metadata", default=None, help="JSON rule metadata or selected-rule CSV.")
    parser.add_argument("--run-id", default="manual")
    parser.add_argument("--label", default="mt5_execution_loop")
    parser.add_argument("--max-fill-lag-bars", type=int, default=6)
    return parser.parse_args()


def main() -> Path:
    args = parse_args()
    source = pd.read_csv(Path(args.source_csv), sep=";")
    output_csv = Path(args.output_csv) if args.output_csv is not None else None
    output_json = Path(args.output_json) if args.output_json is not None else None
    if output_csv is None or output_json is None:
        default_csv, default_json = _resolve_output_paths(args.run_id)
        output_csv = output_csv or default_csv
        output_json = output_json or default_json
    return export_mt5_entry_signals(
        source,
        output_csv,
        output_json,
        args.max_fill_lag_bars,
        source_csv=args.source_csv,
        rule_metadata=args.rule_metadata,
        run_id=args.run_id,
        label=args.label,
    )


if __name__ == "__main__":
    main()
