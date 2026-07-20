from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ML.baseline import benchmark_regression_updn_target_foundation as legacy_foundation
from processing.denormalize_updn import denormalize_updn_pairs, load_updn_params


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "ML" / "reports"
DATA_DIR = PROJECT_ROOT / "DATA"
OHLC_PATH = DATA_DIR / "XAUUSD_H1_OHLC.csv"
REPORT_JSON_PATH = REPORTS_DIR / "next_open_entry_updn_foundation.json"
REPORT_ROWS_PATH = REPORTS_DIR / "next_open_entry_updn_rows.csv"
LABELED_PATHS = {
    "train": DATA_DIR / "Nero_XAUUSD_train_labeled.csv",
    "validation": DATA_DIR / "Nero_XAUUSD_validation_labeled.csv",
    "test": DATA_DIR / "Nero_XAUUSD_test_labeled.csv",
}


@dataclasses.dataclass(frozen=True)
class NextOpenEntryConfig:
    horizons: tuple[int, ...] = (3, 6, 12)
    primary_split: str = "val_stop"
    disclosure_splits: tuple[str, ...] = ("diagnostic_holdout", "low_n_disclosure")
    profile: str = "structure_full"
    model_key: str = "xgboost_depth3"
    seed: int = 42
    project_time_format: str = "%Y.%m.%d %H:%M"
    entry_target_columns: tuple[str, ...] = (
        "entry_up_3", "entry_dn_3", "entry_up_6", "entry_dn_6", "entry_up_12", "entry_dn_12"
    )


CONFIG = NextOpenEntryConfig()
ROWS_CSV_COLUMNS = [
    "split_name",
    "time",
    "signal_time",
    "entry_time",
    "entry_index",
    "entry_open",
    "has_full_h3",
    "has_full_h6",
    "has_full_h12",
    "entry_up_3",
    "entry_dn_3",
    "entry_up_6",
    "entry_dn_6",
    "entry_up_12",
    "entry_dn_12",
    "entry_log_ratio_3",
    "entry_log_ratio_6",
    "entry_log_ratio_12",
    "legacy_price_up_3",
    "legacy_price_dn_3",
    "legacy_price_up_6",
    "legacy_price_dn_6",
    "legacy_price_up_12",
    "legacy_price_dn_12",
]


def parse_project_time(value: object) -> pd.Timestamp:
    return pd.to_datetime(str(value), format=CONFIG.project_time_format, errors="raise")


def prepare_ohlc(ohlc: pd.DataFrame) -> pd.DataFrame:
    prepared = ohlc.copy()
    prepared["parsed_time"] = prepared["time"].map(parse_project_time)
    if prepared["parsed_time"].isna().any():
        raise ValueError("OHLC time parse failed")
    prepared = prepared.sort_values("parsed_time").reset_index(drop=True)
    if not prepared["parsed_time"].is_unique:
        raise ValueError("OHLC times are not unique")
    return prepared


def load_ohlc(path: Path = OHLC_PATH) -> pd.DataFrame:
    raw = pd.read_csv(path, sep=";", usecols=["time", "open", "high", "low"])
    return prepare_ohlc(raw)


def load_labeled_source(name: str) -> pd.DataFrame:
    df = pd.read_csv(LABELED_PATHS[name], sep=";")
    df["source_split"] = name
    df["source_row_idx"] = np.arange(len(df), dtype=int)
    return df


def build_research_splits(
    train_df: pd.DataFrame,
    validation_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    def parse_years(series: pd.Series) -> pd.Series:
        return pd.to_datetime(series, format=CONFIG.project_time_format, errors="coerce").dt.year

    train_year = parse_years(train_df["time"])
    validation_year = parse_years(validation_df["time"])
    test_year = parse_years(test_df["time"])
    return {
        "train_core": train_df.loc[train_year <= 2020].reset_index(drop=True),
        "val_stop": pd.concat(
            [train_df.loc[train_year.isin((2021, 2022))], validation_df.loc[validation_year.isin((2021, 2022))]],
            ignore_index=True,
        ),
        "diagnostic_holdout": pd.concat(
            [
                train_df.loc[train_year.isin((2023, 2024, 2025))],
                validation_df.loc[validation_year.isin((2023, 2024, 2025))],
                test_df.loc[test_year.isin((2023, 2024, 2025))],
            ],
            ignore_index=True,
        ),
        "low_n_disclosure": pd.concat(
            [
                train_df.loc[train_year == 2026],
                validation_df.loc[validation_year == 2026],
                test_df.loc[test_year == 2026],
            ],
            ignore_index=True,
        ),
    }


def load_research_splits() -> dict[str, pd.DataFrame]:
    return build_research_splits(
        train_df=load_labeled_source("train"),
        validation_df=load_labeled_source("validation"),
        test_df=load_labeled_source("test"),
    )


def resolve_entry_bar(signal_time: pd.Timestamp, ohlc_times: np.ndarray) -> int | None:
    pos = int(ohlc_times.searchsorted(signal_time.to_datetime64(), side="right"))
    if pos >= len(ohlc_times):
        return None
    return pos


def compute_entry_updn_from_ohlc(
    entry_index: int,
    horizon: int,
    highs: np.ndarray,
    lows: np.ndarray,
    entry_open: float,
) -> tuple[float, float]:
    end = entry_index + horizon
    future_high = float(np.max(highs[entry_index:end]))
    future_low = float(np.min(lows[entry_index:end]))
    up = max(future_high - entry_open, 0.0)
    dn = max(entry_open - future_low, 0.0)
    return up, dn


def safe_log_ratio(up: np.ndarray, dn: np.ndarray) -> np.ndarray:
    return np.log1p(np.clip(up, 0.0, None)) - np.log1p(np.clip(dn, 0.0, None))


def rebuild_entry_targets(
    df: pd.DataFrame,
    ohlc: pd.DataFrame,
    horizons: tuple[int, ...],
) -> pd.DataFrame:
    ohlc_times = ohlc["parsed_time"].to_numpy()
    highs = ohlc["high"].to_numpy(dtype=float)
    lows = ohlc["low"].to_numpy(dtype=float)
    opens = ohlc["open"].to_numpy(dtype=float)

    out = df.copy()
    out["signal_time"] = out["time"].map(parse_project_time)
    out["entry_time"] = pd.NaT
    out["entry_open"] = np.nan
    out["entry_index"] = pd.Series(pd.NA, index=out.index, dtype="Int64")

    for horizon in horizons:
        out[f"entry_up_{horizon}"] = np.nan
        out[f"entry_dn_{horizon}"] = np.nan
        out[f"entry_log_ratio_{horizon}"] = np.nan
        out[f"has_full_h{horizon}"] = False

    for row_index, signal_time in out["signal_time"].items():
        entry_idx = resolve_entry_bar(signal_time=signal_time, ohlc_times=ohlc_times)
        if entry_idx is None:
            continue

        entry_open = float(opens[entry_idx])
        out.at[row_index, "entry_time"] = pd.Timestamp(ohlc_times[entry_idx])
        out.at[row_index, "entry_open"] = entry_open
        out.at[row_index, "entry_index"] = int(entry_idx)

        for horizon in horizons:
            if entry_idx + horizon > len(ohlc):
                continue
            out.at[row_index, f"has_full_h{horizon}"] = True
            up, dn = compute_entry_updn_from_ohlc(
                entry_index=entry_idx,
                horizon=horizon,
                highs=highs,
                lows=lows,
                entry_open=entry_open,
            )
            out.at[row_index, f"entry_up_{horizon}"] = up
            out.at[row_index, f"entry_dn_{horizon}"] = dn
            out.at[row_index, f"entry_log_ratio_{horizon}"] = float(safe_log_ratio(np.array([up]), np.array([dn]))[0])

    return out


def validate_summary(summary: dict) -> list[str]:
    required = [
        "status",
        "artifact_status",
        "target_contract",
        "decision_time",
        "entry_rule",
        "horizons",
        "primary_split",
        "disclosure_splits",
        "coverage",
        "dummy_metrics",
        "model_metrics",
    ]
    return [key for key in required if key not in summary]


def build_runner_decision_gate(report: dict, threshold: float = 0.10) -> dict:
    """Summarize the fixed diagnostic gate over all declared evaluation splits."""
    split_names = [report["primary_split"], *report["disclosure_splits"]]
    checked = []
    max_spearman = None
    for split_name in split_names:
        for horizon in report["horizons"]:
            metric = report["model_metrics"][split_name]["log_ratio"][f"log_ratio_{horizon}"]["spearman"]
            checked.append(
                {
                    "split": split_name,
                    "horizon": int(horizon),
                    "spearman": _safe_float(metric),
                    "passes_threshold": bool(metric is not None and metric >= threshold),
                }
            )
            if metric is not None:
                max_spearman = metric if max_spearman is None else max(max_spearman, metric)
    return {
        "metric": "model Spearman(pred_entry_log_ratio_h, actual_entry_log_ratio_h)",
        "threshold": float(threshold),
        "rule": "PASS_DIAGNOSTIC only if any primary/disclosure horizon reaches threshold",
        "checked": checked,
        "max_checked_spearman": _safe_float(max_spearman),
        "passes": any(item["passes_threshold"] for item in checked),
    }


def decide_runner_status(report: dict, threshold: float = 0.10) -> str:
    gate = build_runner_decision_gate(report, threshold=threshold)
    return "PASS_DIAGNOSTIC" if gate["passes"] else "NO_SIGNAL_FOUND"


def _safe_float(value):
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if np.isnan(value) or np.isinf(value):
        return None
    return value


def _corr_or_none(fn, a: np.ndarray, b: np.ndarray):
    if len(a) < 2:
        return None
    if np.allclose(a, a[0]) or np.allclose(b, b[0]):
        return None
    return _safe_float(fn(a, b)[0])


def _target_pairs_by_horizon() -> dict[int, tuple[str, str]]:
    return {
        3: ("entry_up_3", "entry_dn_3"),
        6: ("entry_up_6", "entry_dn_6"),
        12: ("entry_up_12", "entry_dn_12"),
    }


def _legacy_params_path(source_name: str) -> Path:
    return DATA_DIR / f"Nero_XAUUSD_{source_name}_updn_params.npy"


def load_source_updn_params() -> dict[str, np.ndarray]:
    return {name: load_updn_params(_legacy_params_path(name)) for name in LABELED_PATHS}


def _denormalize_legacy_row(row: pd.Series, params_row: np.ndarray) -> dict[str, float]:
    y_norm = row.loc[list(legacy_foundation.UPDN_TARGET_COLUMNS)].to_numpy(dtype=np.float64)
    y_denorm = denormalize_updn_pairs(y_norm, params_row)
    return {
        column: float(y_denorm[idx])
        for idx, column in enumerate(legacy_foundation.UPDN_TARGET_COLUMNS)
    }


def attach_legacy_denormalized_targets(
    df: pd.DataFrame,
    params_by_source: dict[str, np.ndarray],
) -> pd.DataFrame:
    out = df.copy()
    legacy_values = out.loc[:, list(legacy_foundation.UPDN_TARGET_COLUMNS)].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy(dtype=np.float64)
    source_split = out["source_split"].astype(str).to_numpy()
    source_row_idx = out["source_row_idx"].astype(int).to_numpy()
    denorm_matrix = np.zeros_like(legacy_values, dtype=np.float64)
    for row_idx, source_name in enumerate(source_split):
        denorm_matrix[row_idx, :] = denormalize_updn_pairs(
            legacy_values[row_idx, :],
            params_by_source[source_name][source_row_idx[row_idx]],
        )
    denorm_df = pd.DataFrame(
        denorm_matrix,
        index=out.index,
        columns=[f"legacy_price_{column}" for column in legacy_foundation.UPDN_TARGET_COLUMNS],
    )
    return pd.concat([out, denorm_df], axis=1)


def entry_target_matrix(df: pd.DataFrame) -> np.ndarray:
    return df.loc[:, list(CONFIG.entry_target_columns)].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy(dtype=np.float32)


def feature_matrix(df: pd.DataFrame) -> np.ndarray:
    return legacy_foundation.build_updn_features(df, CONFIG.profile)


def preflight_ohlc(ohlc: pd.DataFrame) -> dict:
    diffs = ohlc["parsed_time"].diff().dropna()
    h1_gap_count = int((diffs != pd.Timedelta(hours=1)).sum())
    return {
        "rows": int(len(ohlc)),
        "parsed_without_na": bool(ohlc["parsed_time"].notna().all()),
        "sorted": bool(ohlc["parsed_time"].is_monotonic_increasing),
        "unique_times": bool(ohlc["parsed_time"].is_unique),
        "non_1h_gap_count": h1_gap_count,
    }


def preflight_split(df: pd.DataFrame) -> dict:
    years = pd.to_datetime(df["time"], format=CONFIG.project_time_format, errors="coerce").dt.year
    result = {
        "rows": int(len(df)),
        "time_parse_ok": bool(years.notna().all()),
        "entry_match_rate": _safe_float(df["entry_open"].notna().mean()),
        "rows_missing_entry_open": int(df["entry_open"].isna().sum()),
    }
    for horizon in CONFIG.horizons:
        result[f"rows_without_full_h{horizon}"] = int((~df[f"has_full_h{horizon}"]).sum())
    return result


def distribution_shift_vs_legacy(df: pd.DataFrame) -> dict:
    out = {}
    for horizon, (up_col, dn_col) in _target_pairs_by_horizon().items():
        legacy_up = pd.to_numeric(df[f"legacy_price_up_{horizon}"], errors="coerce").to_numpy(dtype=float)
        legacy_dn = pd.to_numeric(df[f"legacy_price_dn_{horizon}"], errors="coerce").to_numpy(dtype=float)
        entry_up = pd.to_numeric(df[up_col], errors="coerce").to_numpy(dtype=float)
        entry_dn = pd.to_numeric(df[dn_col], errors="coerce").to_numpy(dtype=float)
        legacy_ratio = safe_log_ratio(legacy_up, legacy_dn)
        entry_ratio = safe_log_ratio(entry_up, entry_dn)
        out[f"h{horizon}"] = {
            "legacy_up_median": _safe_float(np.median(legacy_up)),
            "legacy_dn_median": _safe_float(np.median(legacy_dn)),
            "entry_up_median": _safe_float(np.median(entry_up)),
            "entry_dn_median": _safe_float(np.median(entry_dn)),
            "legacy_vs_entry_log_ratio_spearman": _corr_or_none(stats.spearmanr, legacy_ratio, entry_ratio),
        }
    return out


def rows_csv_view(df: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in ROWS_CSV_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing rows CSV columns: {missing}")
    return df.loc[:, ROWS_CSV_COLUMNS].copy()


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray, target_names: tuple[str, ...]) -> dict:
    targets = {}
    for idx, name in enumerate(target_names):
        yt = y_true[:, idx]
        yp = y_pred[:, idx]
        mae = legacy_foundation.mean_absolute_error(yt, yp)
        rmse = float(np.sqrt(legacy_foundation.mean_squared_error(yt, yp)))
        median_abs_target = float(np.median(np.abs(yt))) if len(yt) else 0.0
        targets[name] = {
            "mae": _safe_float(mae),
            "rmse": _safe_float(rmse),
            "spearman": _corr_or_none(stats.spearmanr, yt, yp),
            "pearson": _corr_or_none(stats.pearsonr, yt, yp),
            "mae_over_median_abs_target": _safe_float(mae / median_abs_target) if median_abs_target else None,
        }
    return {"targets": targets}


def log_ratio_metrics(y_true: np.ndarray, y_pred: np.ndarray, horizon: int) -> dict:
    true_ratio = safe_log_ratio(y_true[:, 0], y_true[:, 1])
    pred_ratio = safe_log_ratio(y_pred[:, 0], y_pred[:, 1])
    return {
        f"log_ratio_{horizon}": {
            "spearman": _corr_or_none(stats.spearmanr, true_ratio, pred_ratio),
            "pearson": _corr_or_none(stats.pearsonr, true_ratio, pred_ratio),
        }
    }


def run_next_open_entry_foundation(
    output_path: Path = REPORT_JSON_PATH,
    rows_path: Path = REPORT_ROWS_PATH,
) -> dict:
    started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("[next-open] load ohlc", flush=True)
    ohlc = load_ohlc()
    print("[next-open] load splits", flush=True)
    split_frames = load_research_splits()
    params_by_source = load_source_updn_params()

    rebuilt_splits = {}
    rows_for_csv = []
    split_preflight = {}
    for split_name, frame in split_frames.items():
        print(f"[next-open] rebuild targets split={split_name} rows={len(frame)}", flush=True)
        rebuilt = rebuild_entry_targets(frame, ohlc, CONFIG.horizons)
        rebuilt["split_name"] = split_name
        rebuilt = attach_legacy_denormalized_targets(rebuilt, params_by_source)
        rebuilt_splits[split_name] = rebuilt
        split_preflight[split_name] = preflight_split(rebuilt)
        rows_for_csv.append(rows_csv_view(rebuilt))

    rows_df = pd.concat(rows_for_csv, ignore_index=True)
    print(f"[next-open] write rows csv rows={len(rows_df)} path={rows_path}", flush=True)
    rows_df.to_csv(rows_path, sep=";", index=False)

    feature_split = {}
    for name, frame in rebuilt_splits.items():
        print(f"[next-open] build features split={name} rows={len(frame)}", flush=True)
        feature_split[name] = feature_matrix(frame)
    train_y = entry_target_matrix(rebuilt_splits["train_core"])
    train_X = feature_split["train_core"]

    report = {
        "experiment": "next_open_entry_updn_foundation",
        "status": "DIAGNOSTIC_ONLY",
        "artifact_status": "DIAGNOSTIC_ONLY",
        "runner_status": "RUNNING",
        "target_contract": "next_open_after_signal_time",
        "decision_time": "signal_time",
        "entry_rule": "first_open_strictly_after_signal_time",
        "horizons": list(CONFIG.horizons),
        "primary_split": CONFIG.primary_split,
        "disclosure_splits": list(CONFIG.disclosure_splits),
        "target_scale": "price_units_from_entry_open",
        "started_at": started_at,
        "config": dataclasses.asdict(CONFIG),
        "coverage": {},
        "preflight": {"ohlc": preflight_ohlc(ohlc), "splits": split_preflight},
        "distribution_shift_vs_legacy": {},
        "dummy_metrics": {},
        "model_metrics": {},
    }

    for split_name, frame in rebuilt_splits.items():
        report["coverage"][split_name] = {
            "rows": int(len(frame)),
            "entry_open_available": int(frame["entry_open"].notna().sum()),
            **{f"full_h{h}": int(frame[f"has_full_h{h}"].sum()) for h in CONFIG.horizons},
        }
        report["distribution_shift_vs_legacy"][split_name] = distribution_shift_vs_legacy(frame)

        y_true = entry_target_matrix(frame)
        print(f"[next-open] evaluate split={split_name} rows={len(frame)}", flush=True)
        pred_dummy = legacy_foundation.updn_constant_median_predict(train_y, len(frame))
        pred_model, _ = legacy_foundation._train_predict_model(CONFIG.model_key, CONFIG.seed, train_X, train_y, feature_split[split_name])

        dummy = regression_metrics(y_true, pred_dummy, CONFIG.entry_target_columns)
        model = regression_metrics(y_true, pred_model, CONFIG.entry_target_columns)

        for horizon, (up_col, dn_col) in _target_pairs_by_horizon().items():
            idxs = [CONFIG.entry_target_columns.index(up_col), CONFIG.entry_target_columns.index(dn_col)]
            dummy.setdefault("log_ratio", {}).update(log_ratio_metrics(y_true[:, idxs], pred_dummy[:, idxs], horizon))
            model.setdefault("log_ratio", {}).update(log_ratio_metrics(y_true[:, idxs], pred_model[:, idxs], horizon))

        report["dummy_metrics"][split_name] = dummy
        report["model_metrics"][split_name] = model

    report["runner_decision_gate"] = build_runner_decision_gate(report)
    report["runner_status"] = decide_runner_status(report)
    missing = validate_summary(report)
    if missing:
        report["runner_status"] = "MODEL_REPRO_FAILED"
        report["status"] = "MODEL_REPRO_FAILED"
        report["missing_summary_fields"] = missing
    report["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    output_path.write_text(json.dumps(report, indent=2, default=str))
    return report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--next-open-entry-updn-foundation", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.next_open_entry_updn_foundation:
        report = run_next_open_entry_foundation()
        print({"status": report["status"], "json": str(REPORT_JSON_PATH), "rows": str(REPORT_ROWS_PATH)})
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
