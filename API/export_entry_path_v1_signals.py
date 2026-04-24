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
#   - production path поддерживает только frozen winner A по pred_ret_24_dir_atr
# =============================================================================

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


MT4_TESTER_SIGNALS = Path("MT/tester/files/ml_signals.csv")
MT4_RUNTIME_SIGNALS = Path("MT/MQL4/Files/ml_signals.csv")


def load_prediction_frame(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(Path(path), sep=";")
    required = {"time", "signal", "pred_ret_24_dir_atr"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"prediction CSV missing columns: {sorted(missing)}")
    return frame


def load_rule_payload_from_file(rule_path: str | Path) -> dict:
    raw = json.loads(Path(rule_path).read_text(encoding="utf-8"))
    winner = raw.get("winner", {})
    candidate = str(winner.get("candidate", "")).strip()
    if candidate != "A":
        raise ValueError(f"Unsupported entry_path_v1 winner: {candidate}")
    return {
        "winner": {
            "candidate": candidate,
            "score_threshold": float(winner.get("score_threshold", 0.0)),
        }
    }


def apply_rule(frame: pd.DataFrame, rule_payload: dict) -> pd.Series:
    threshold = float(rule_payload["winner"]["score_threshold"])
    scores = pd.to_numeric(frame["pred_ret_24_dir_atr"], errors="coerce").fillna(float("-inf"))
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


def export_signals(
    *,
    predictions_path: str | Path,
    rule_path: str | Path,
    output_path: str | Path,
    copy_to_mt4: bool = False,
) -> Path:
    frame = load_prediction_frame(predictions_path)
    rule_payload = load_rule_payload_from_file(rule_path)
    selected_mask = apply_rule(frame, rule_payload)

    selected = frame[["time", "signal"]].copy()
    selected.loc[~selected_mask, "signal"] = 0
    export = _deduplicate_runtime_rows(selected)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(output, sep=";", index=False)

    if copy_to_mt4:
        MT4_TESTER_SIGNALS.parent.mkdir(parents=True, exist_ok=True)
        MT4_RUNTIME_SIGNALS.parent.mkdir(parents=True, exist_ok=True)
        export.to_csv(MT4_TESTER_SIGNALS, sep=";", index=False)
        export.to_csv(MT4_RUNTIME_SIGNALS, sep=";", index=False)

    return output


def parse_args():
    parser = argparse.ArgumentParser(description="Apply frozen entry_path_v1 rule to prediction CSV and export time;signal.")
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--rule-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--copy-to-mt4", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    path = export_signals(
        predictions_path=args.predictions,
        rule_path=args.rule_path,
        output_path=args.output,
        copy_to_mt4=args.copy_to_mt4,
    )
    print(path)
    return path


if __name__ == "__main__":
    main()
