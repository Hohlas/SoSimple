# =============================================================================
# Файл: export_entry_path_v1_signals.py
# Назначение: Применение frozen entry_path_v1 rule к prediction CSV и экспорт time;signal.
# Обновлён: 2026-04-24
# Входные данные:
#   - prediction CSV с колонками time, signal, pred_ret_24_dir_atr (откуда: ML/reports/*)
#   - rule JSON из ML/reports/entry_path_trade_filter_selected_rule.json
# Выходные данные:
#   - CSV time;signal (куда: output_path, optional MT/tester/files и MT/MQL4/Files)
# Использование:
#   python -m API.export_entry_path_v1_signals --predictions ... --rule-path ... --output ...
# Примечания:
#   - A использует pred_ret_24_dir_atr напрямую
#   - B/B_no_path6 используют frozen validation-нормировку из rule JSON
# =============================================================================

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import pandas as pd

from ML.entry_path_trade_filter import apply_candidate_b_score
from ML.entry_path_trade_filter import build_candidate_a_score
from ML.entry_path_trade_filter import fit_candidate_b_score


MT4_TESTER_SIGNALS = Path("MT/tester/files/ml_signals.csv")
MT4_RUNTIME_SIGNALS = Path("MT/MQL4/Files/ml_signals.csv")
PRODUCTION_BASELINE_LABEL = "entry_path_v1_live_safe + A @ 7.5%"
SUPPORTED_DIAGNOSTIC_DIRECTION_SOURCES = {"fractal0_direction"}


def load_prediction_frame(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(Path(path), sep=";")
    required = {"time", "signal", "pred_ret_24_dir_atr"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"prediction CSV missing columns: {sorted(missing)}")
    return frame


def load_rule_payload_from_file(rule_path: str | Path) -> dict:
    path = Path(rule_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    winner = raw.get("winner", {})
    candidate = str(winner.get("candidate", "")).strip()
    if candidate not in {"A", "B", "B_no_path6"}:
        raise ValueError(f"Unsupported entry_path_v1 winner: {candidate}")
    payload = {
        "winner": {
            "candidate": candidate,
            "score_threshold": float(winner.get("score_threshold", 0.0)),
        }
    }
    if candidate in {"B", "B_no_path6"}:
        validation_csv = raw.get("validation_csv")
        if not validation_csv:
            raise ValueError(f"entry_path_v1 winner {candidate} requires validation_csv for frozen scaler")
        validation_path = Path(validation_csv)
        if not validation_path.is_absolute():
            validation_path = Path.cwd() / validation_path
        payload["validation_csv"] = str(validation_path)
    return payload


def _score_for_rule(frame: pd.DataFrame, rule_payload: dict) -> pd.Series:
    candidate = rule_payload["winner"]["candidate"]
    if candidate == "A":
        score = build_candidate_a_score(frame)
    elif candidate in {"B", "B_no_path6"}:
        validation_frame = load_prediction_frame(rule_payload["validation_csv"])
        include_path6 = candidate == "B"
        scaler = fit_candidate_b_score(validation_frame, include_path6=include_path6)
        score = apply_candidate_b_score(frame, scaler, include_path6=include_path6)
    else:
        raise ValueError(f"Unsupported entry_path_v1 winner: {candidate}")
    return pd.Series(score, index=frame.index, dtype="float64")


def apply_rule(frame: pd.DataFrame, rule_payload: dict) -> pd.Series:
    threshold = float(rule_payload["winner"]["score_threshold"])
    return apply_rule_with_threshold(frame, rule_payload, threshold=threshold)


def apply_rule_with_threshold(frame: pd.DataFrame, rule_payload: dict, *, threshold: float) -> pd.Series:
    scores = _score_for_rule(frame, rule_payload).fillna(float("-inf"))
    active = pd.to_numeric(frame["signal"], errors="coerce").fillna(0).astype(int) != 0
    return active & (scores >= threshold)


def _deduplicate_runtime_rows(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame[["time", "signal"]].copy()
    out["_abs"] = out["signal"].abs()
    out = (
        out.sort_values(["time", "_abs"], ascending=[True, False], kind="stable")
        .drop_duplicates(subset=["time"], keep="first")
        .drop(columns="_abs")
        .sort_values("time", kind="stable")
        .reset_index(drop=True)
    )
    return out


def diagnostic_signal_from_fractal0(fractal0: pd.Series) -> pd.Series:
    direction = fractal0.astype(str).str.split(":", n=3).str[2]
    direction = pd.to_numeric(direction, errors="coerce").fillna(0).astype(int)
    diagnostic_signal = pd.Series(0, index=fractal0.index, dtype="int64")
    diagnostic_signal.loc[direction == -1] = 1
    diagnostic_signal.loc[direction == 1] = -1
    return diagnostic_signal


def build_diagnostic_all_rows_export(
    *,
    frame: pd.DataFrame,
    base: pd.DataFrame,
    rule_payload: dict,
    target_signals_per_year: int,
    direction_source: str,
    score_threshold_override: float | None,
) -> pd.DataFrame:
    if direction_source not in SUPPORTED_DIAGNOSTIC_DIRECTION_SOURCES:
        supported = ", ".join(sorted(SUPPORTED_DIAGNOSTIC_DIRECTION_SOURCES))
        raise ValueError(f"unsupported diagnostic_direction_source: {direction_source}. Supported: {supported}")
    if "fractal0" not in base.columns:
        raise ValueError("diagnostic_all_rows requires base_csv with fractal0 column")
    if target_signals_per_year <= 0 and score_threshold_override is None:
        raise ValueError("diagnostic_all_rows requires positive diagnostic_target_signals_per_year or threshold override")

    scores = _score_for_rule(frame, rule_payload).fillna(float("-inf"))
    merged = frame[["time"]].copy()
    merged["score"] = scores.to_numpy(dtype="float64")
    base = base.drop_duplicates(subset=["time"], keep="last").reset_index(drop=True)
    merged = merged.merge(base[["time", "fractal0"]], on="time", how="left", validate="many_to_one")
    merged["diagnostic_signal"] = diagnostic_signal_from_fractal0(merged["fractal0"])
    merged["year"] = pd.to_datetime(merged["time"], format="%Y.%m.%d %H:%M", errors="coerce").dt.year

    selected = pd.Series(False, index=merged.index)
    candidates = merged.loc[(merged["diagnostic_signal"] != 0) & merged["year"].notna()].copy()
    if score_threshold_override is not None:
        selected.loc[candidates.index] = candidates["score"] >= float(score_threshold_override)
    else:
        for _, group in candidates.groupby("year", sort=False):
            top_idx = group.nlargest(int(target_signals_per_year), "score").index
            selected.loc[top_idx] = True

    export = frame[["time"]].copy()
    export["signal"] = 0
    export.loc[selected, "signal"] = merged.loc[selected, "diagnostic_signal"].astype(int)
    return export.drop_duplicates(subset=["time"], keep="last").reset_index(drop=True)


def _write_csv_atomic(frame: pd.DataFrame, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + ".tmp")
    frame.to_csv(temp, sep=";", index=False)
    os.replace(temp, target)


def _append_newer_signal_rows_atomic(frame: pd.DataFrame, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or target.stat().st_size == 0:
        _write_csv_atomic(frame, target)
        return

    existing = pd.read_csv(target, sep=";")
    if {"time", "signal"}.difference(existing.columns):
        raise ValueError(f"existing signal CSV must contain time and signal columns: {target}")
    if existing.empty:
        merged = frame
    else:
        last_time = str(existing["time"].astype(str).iloc[-1])
        new_rows = frame.loc[frame["time"].astype(str) > last_time].copy()
        if new_rows.empty:
            return
        merged = pd.concat([existing, new_rows], ignore_index=True)
    _write_csv_atomic(merged, target)


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_export_metadata(
    *,
    label: str,
    predictions_path: str | Path,
    rule_path: str | Path,
    output_path: str | Path,
    export: pd.DataFrame,
    rule_score_threshold: float,
    effective_score_threshold: float,
    diagnostic_only: bool,
    diagnostic_reason: str,
) -> dict:
    signals = pd.to_numeric(export["signal"], errors="coerce").fillna(0).astype(int)
    nonzero = signals.loc[signals != 0]
    return {
        "label": label,
        "production_baseline": PRODUCTION_BASELINE_LABEL,
        "diagnostic_only": bool(diagnostic_only),
        "diagnostic_reason": diagnostic_reason,
        "predictions_path": str(predictions_path),
        "rule_path": str(rule_path),
        "output_path": str(output_path),
        "predictions_sha256": _sha256(predictions_path),
        "rule_sha256": _sha256(rule_path),
        "output_sha256": _sha256(output_path),
        "rule_score_threshold": float(rule_score_threshold),
        "effective_score_threshold": float(effective_score_threshold),
        "rows_total": int(len(export)),
        "nonzero_rows": int(len(nonzero)),
        "buy_rows": int((nonzero > 0).sum()),
        "sell_rows": int((nonzero < 0).sum()),
    }


def export_signals(
    *,
    predictions_path: str | Path,
    rule_path: str | Path,
    output_path: str | Path,
    base_csv: str | Path | None = None,
    copy_to_mt4: bool = False,
    append_to_mt4: bool = False,
    metadata_output: str | Path | None = None,
    label: str = "entry_path_v1_live_safe",
    score_threshold_override: float | None = None,
    diagnostic_all_rows: bool = False,
    diagnostic_target_signals_per_year: int | None = None,
    diagnostic_direction_source: str = "fractal0_direction",
    diagnostic_only: bool = False,
    diagnostic_reason: str = "",
) -> Path:
    if append_to_mt4 and not copy_to_mt4:
        raise ValueError("append_to_mt4 requires copy_to_mt4")

    frame = load_prediction_frame(predictions_path)
    rule_payload = load_rule_payload_from_file(rule_path)
    rule_threshold = float(rule_payload["winner"]["score_threshold"])
    effective_threshold = rule_threshold if score_threshold_override is None else float(score_threshold_override)

    if diagnostic_all_rows:
        if base_csv is None:
            raise ValueError("diagnostic_all_rows requires base_csv")
        if diagnostic_target_signals_per_year is None:
            raise ValueError("diagnostic_all_rows requires diagnostic_target_signals_per_year")
        base = pd.read_csv(Path(base_csv), sep=";", usecols=["time", "fractal0"])
        export = build_diagnostic_all_rows_export(
            frame=frame,
            base=base,
            rule_payload=rule_payload,
            target_signals_per_year=int(diagnostic_target_signals_per_year),
            direction_source=diagnostic_direction_source,
            score_threshold_override=score_threshold_override,
        )
    else:
        selected_mask = apply_rule_with_threshold(frame, rule_payload, threshold=effective_threshold)
        selected = frame[["time", "signal"]].copy()
        selected.loc[~selected_mask, "signal"] = 0
        export = _deduplicate_runtime_rows(selected)

    output = Path(output_path)
    _write_csv_atomic(export, output)

    if metadata_output is not None:
        metadata = build_export_metadata(
            label=label,
            predictions_path=predictions_path,
            rule_path=rule_path,
            output_path=output,
            export=export,
            rule_score_threshold=rule_threshold,
            effective_score_threshold=effective_threshold,
            diagnostic_only=diagnostic_only,
            diagnostic_reason=diagnostic_reason,
        )
        metadata_path = Path(metadata_output)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    if copy_to_mt4:
        writer = _append_newer_signal_rows_atomic if append_to_mt4 else _write_csv_atomic
        writer(export, MT4_TESTER_SIGNALS)
        writer(export, MT4_RUNTIME_SIGNALS)

    return output


def parse_args():
    parser = argparse.ArgumentParser(description="Apply frozen entry_path_v1 rule to prediction CSV and export time;signal.")
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--rule-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--copy-to-mt4", action="store_true")
    parser.add_argument("--append-to-mt4", action="store_true")
    parser.add_argument("--metadata-output", default=None)
    parser.add_argument("--label", default="entry_path_v1_live_safe")
    parser.add_argument("--score-threshold-override", type=float, default=None)
    parser.add_argument("--base-csv", default=None)
    parser.add_argument("--diagnostic-all-rows", action="store_true")
    parser.add_argument("--diagnostic-target-signals-per-year", type=int, default=None)
    parser.add_argument("--diagnostic-direction-source", choices=sorted(SUPPORTED_DIAGNOSTIC_DIRECTION_SOURCES), default="fractal0_direction")
    parser.add_argument("--diagnostic-only", action="store_true")
    parser.add_argument("--diagnostic-reason", default="")
    return parser.parse_args()


def main():
    args = parse_args()
    path = export_signals(
        predictions_path=args.predictions,
        rule_path=args.rule_path,
        output_path=args.output,
        base_csv=args.base_csv,
        copy_to_mt4=args.copy_to_mt4,
        append_to_mt4=args.append_to_mt4,
        metadata_output=args.metadata_output,
        label=args.label,
        score_threshold_override=args.score_threshold_override,
        diagnostic_all_rows=args.diagnostic_all_rows,
        diagnostic_target_signals_per_year=args.diagnostic_target_signals_per_year,
        diagnostic_direction_source=args.diagnostic_direction_source,
        diagnostic_only=args.diagnostic_only,
        diagnostic_reason=args.diagnostic_reason,
    )
    print(path)
    return path


if __name__ == "__main__":
    main()
