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

from ML.baseline import benchmark_regression_updn_target_foundation as foundation
from processing.denormalize_updn import denormalize_updn_pairs, load_updn_params


PROJECT_ROOT = foundation.PROJECT_ROOT
REPORTS_DIR = foundation.REPORTS_DIR
DATA_DIR = PROJECT_ROOT / "DATA"
ALREADY_MOVED_JSON_PATH = REPORTS_DIR / "regression_updn_already_moved_audit.json"
ALREADY_MOVED_ROWS_PATH = REPORTS_DIR / "regression_updn_already_moved_audit_rows.csv"
OHLC_PATH = DATA_DIR / "XAUUSD_H1_OHLC.csv"


@dataclasses.dataclass(frozen=True)
class AlreadyMovedConfig:
    profile: str = "structure_full"
    model_key: str = "xgboost_depth3"
    seed: int = 42
    horizons: tuple[int, ...] = (3, 6, 12)
    primary_split: str = "val_stop"
    disclosure_splits: tuple[str, ...] = ("diagnostic_holdout", "low_n_disclosure")
    label_match_abs_tolerance: float = 0.05
    label_match_min_rate: float = 0.98
    strong_pred_quantile: float = 0.90
    model_repro_min_h3_spearman: float = 0.70


CONFIG = AlreadyMovedConfig()


def _price_float(value: float) -> float:
    return float(np.round(float(value), 10))


def parse_fractal0(fractal_value: object) -> dict | None:
    parts = str(fractal_value).split(":")
    if len(parts) < 23:
        return None
    try:
        return {
            "time": int(float(parts[0])),
            "price": float(parts[1]),
            "direction": int(float(parts[2])),
            "shift": int(float(parts[22])),
        }
    except (TypeError, ValueError):
        return None


def safe_log_ratio(up: np.ndarray, dn: np.ndarray) -> np.ndarray:
    return np.log1p(np.clip(np.asarray(up, dtype=np.float64), 0.0, None)) - np.log1p(
        np.clip(np.asarray(dn, dtype=np.float64), 0.0, None)
    )


def movement_from_fractal_to_entry(fractal_price: float, entry_open: float) -> dict:
    delta = float(entry_open) - float(fractal_price)
    return {
        "already_up": _price_float(max(delta, 0.0)),
        "already_dn": _price_float(max(-delta, 0.0)),
        "entry_minus_fractal": _price_float(delta),
    }


def parse_labeled_time(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, format="%Y.%m.%d %H:%M", errors="coerce")


def load_ohlc(path: Path = OHLC_PATH) -> pd.DataFrame:
    ohlc = pd.read_csv(path, sep=";", usecols=["time", "open", "high", "low", "close"])
    ohlc["time"] = pd.to_datetime(ohlc["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    ohlc = ohlc.dropna(subset=["time"]).sort_values("time").drop_duplicates("time")
    return ohlc.reset_index(drop=True)


def _add_fractal0_columns(rows: pd.DataFrame) -> pd.DataFrame:
    out = rows.copy()
    parsed = out["fractal0"].map(parse_fractal0)
    out["fractal0_time_unix"] = parsed.map(lambda x: x["time"] if x else np.nan)
    out["fractal0_time"] = pd.to_datetime(out["fractal0_time_unix"], unit="s", errors="coerce")
    out["fractal0_price"] = parsed.map(lambda x: x["price"] if x else np.nan)
    out["fractal0_direction"] = parsed.map(lambda x: x["direction"] if x else np.nan)
    out["fractal0_shift"] = parsed.map(lambda x: x["shift"] if x else np.nan)
    out["signal_time"] = parse_labeled_time(out["time"])
    return out


def attach_entry_open(rows: pd.DataFrame, ohlc: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    out = _add_fractal0_columns(rows)
    ohlc_sorted = ohlc.sort_values("time").reset_index(drop=True)
    ohlc_times = ohlc_sorted["time"].to_numpy()
    entry_times = []
    entry_opens = []
    for signal_time in out["signal_time"]:
        if pd.isna(signal_time):
            entry_times.append(pd.NaT)
            entry_opens.append(np.nan)
            continue
        pos = ohlc_times.searchsorted(np.datetime64(signal_time), side="right")
        if pos >= len(ohlc_sorted):
            entry_times.append(pd.NaT)
            entry_opens.append(np.nan)
            continue
        entry_times.append(ohlc_sorted.iloc[pos]["time"])
        entry_opens.append(float(ohlc_sorted.iloc[pos]["open"]))
    out["entry_time"] = entry_times
    out["entry_open"] = entry_opens
    report = {
        "rows": int(len(out)),
        "missing_signal_time": int(out["signal_time"].isna().sum()),
        "missing_fractal0": int(out["fractal0_price"].isna().sum()),
        "missing_entry_open": int(out["entry_open"].isna().sum()),
        "entry_match_rate": float(out["entry_open"].notna().mean()) if len(out) else 0.0,
    }
    return out, report


def reconstruct_window_moves(rows: pd.DataFrame, ohlc: pd.DataFrame, horizon: int) -> pd.DataFrame:
    values = []
    ohlc_sorted = ohlc.sort_values("time").reset_index(drop=True)
    time_to_pos = {timestamp: pos for pos, timestamp in enumerate(ohlc_sorted["time"])}
    for row in rows.itertuples(index=False):
        start_time = pd.NaT
        end_time = pd.NaT
        window = pd.DataFrame()
        if not pd.isna(row.fractal0_time):
            start_pos = time_to_pos.get(row.fractal0_time)
            if start_pos is not None:
                window = ohlc_sorted.iloc[start_pos + 1:start_pos + 1 + int(horizon)]
                if len(window) == int(horizon):
                    start_time = window.iloc[0]["time"]
                    end_time = window.iloc[-1]["time"]
        if len(window) < int(horizon) or pd.isna(row.fractal0_price):
            values.append({
                f"reconstructed_up_{horizon}": np.nan,
                f"reconstructed_dn_{horizon}": np.nan,
                f"bars_in_window_{horizon}": int(len(window)),
                f"label_start_time_{horizon}": start_time,
                f"label_end_time_{horizon}": end_time,
            })
            continue
        price = float(row.fractal0_price)
        values.append({
            f"reconstructed_up_{horizon}": _price_float(max(float(window["high"].max()) - price, 0.0)),
            f"reconstructed_dn_{horizon}": _price_float(max(price - float(window["low"].min()), 0.0)),
            f"bars_in_window_{horizon}": int(len(window)),
            f"label_start_time_{horizon}": start_time,
            f"label_end_time_{horizon}": end_time,
        })
    return pd.DataFrame(values)


def _params_path_for_source(source_name: str) -> Path:
    mapping = {
        "train": DATA_DIR / "Nero_XAUUSD_train_updn_params.npy",
        "validation": DATA_DIR / "Nero_XAUUSD_validation_updn_params.npy",
        "test": DATA_DIR / "Nero_XAUUSD_test_updn_params.npy",
    }
    if source_name not in mapping:
        raise ValueError(f"Unknown source split: {source_name}")
    return mapping[source_name]


def load_source_updn_params() -> dict[str, np.ndarray]:
    return {source: load_updn_params(_params_path_for_source(source)) for source in ("train", "validation", "test")}


def denormalize_updn_matrix(
    values: np.ndarray,
    source_split: pd.Series,
    source_row_idx: pd.Series,
    params: dict[str, np.ndarray],
) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    out = np.zeros((len(values), len(foundation.UPDN_TARGET_COLUMNS)), dtype=np.float64)
    source_values = source_split.reset_index(drop=True)
    row_values = source_row_idx.reset_index(drop=True).astype(int)
    for row_idx, source_name in enumerate(source_values):
        out[row_idx, :] = denormalize_updn_pairs(values[row_idx, :], params[str(source_name)][int(row_values.iloc[row_idx])])
    return out


def _read_labeled_source(path: Path, source_name: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";")
    df["source_split"] = source_name
    df["source_row_idx"] = np.arange(len(df), dtype=int)
    return df


def load_source_frames() -> dict[str, pd.DataFrame]:
    return {
        "train": _read_labeled_source(foundation.XAUUSD_SPLIT_FILES["train_core"], "train"),
        "validation": _read_labeled_source(foundation.XAUUSD_SPLIT_FILES["val_stop"], "validation"),
        "test": _read_labeled_source(foundation.XAUUSD_SPLIT_FILES["diagnostic_holdout"], "test"),
    }


def load_split_frames_with_source() -> dict[str, pd.DataFrame]:
    sources = load_source_frames()
    train = sources["train"]
    validation = sources["validation"]
    test = sources["test"]

    train_year = foundation._parse_years(train["time"])
    validation_year = foundation._parse_years(validation["time"])
    test_year = foundation._parse_years(test["time"])

    return {
        "train_core": train.loc[train_year <= foundation.REGRESSION_UPDN_CONFIG.train_max_year].reset_index(drop=True),
        "val_stop": pd.concat(
            [
                train.loc[train_year.isin(foundation.REGRESSION_UPDN_CONFIG.val_years)],
                validation.loc[validation_year.isin(foundation.REGRESSION_UPDN_CONFIG.val_years)],
            ],
            ignore_index=True,
        ),
        "diagnostic_holdout": pd.concat(
            [
                train.loc[train_year.isin(foundation.REGRESSION_UPDN_CONFIG.holdout_years)],
                validation.loc[validation_year.isin(foundation.REGRESSION_UPDN_CONFIG.holdout_years)],
                test.loc[test_year.isin(foundation.REGRESSION_UPDN_CONFIG.holdout_years)],
            ],
            ignore_index=True,
        ),
        "low_n_disclosure": pd.concat(
            [
                train.loc[train_year.isin(foundation.REGRESSION_UPDN_CONFIG.low_n_years)],
                validation.loc[validation_year.isin(foundation.REGRESSION_UPDN_CONFIG.low_n_years)],
                test.loc[test_year.isin(foundation.REGRESSION_UPDN_CONFIG.low_n_years)],
            ],
            ignore_index=True,
        ),
    }


def validate_source_row_alignment(
    source_frames: dict[str, pd.DataFrame],
    split_frames: dict[str, pd.DataFrame],
    params: dict[str, np.ndarray],
) -> dict:
    report = {"status": "PASS", "sources": {}, "splits": {}}
    for source_name, frame in source_frames.items():
        n_rows = len(frame)
        n_params = len(params[source_name])
        ok = n_rows == n_params
        report["sources"][source_name] = {
            "csv_rows": int(n_rows),
            "params_rows": int(n_params),
            "row_count_match": bool(ok),
        }
        if not ok:
            report["status"] = "PARAM_ROW_ALIGNMENT_FAILED"
    for split_name, split_frame in split_frames.items():
        mismatches = 0
        for row in split_frame.loc[:, ["time", "source_split", "source_row_idx"]].itertuples(index=False):
            source_frame = source_frames[str(row.source_split)]
            source_idx = int(row.source_row_idx)
            if source_idx >= len(source_frame):
                mismatches += 1
                continue
            if str(source_frame.iloc[source_idx]["time"]) != str(row.time):
                mismatches += 1
        report["splits"][split_name] = {
            "rows": int(len(split_frame)),
            "time_position_mismatches": int(mismatches),
        }
        if mismatches:
            report["status"] = "PARAM_ROW_ALIGNMENT_FAILED"
    return report


def _safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    den = den.replace(0, np.nan)
    return num / den


def attach_already_moved_columns(rows: pd.DataFrame, horizons: tuple[int, ...]) -> pd.DataFrame:
    out = rows.copy()
    move = out.apply(
        lambda row: movement_from_fractal_to_entry(row["fractal0_price"], row["entry_open"]),
        axis=1,
        result_type="expand",
    )
    out = pd.concat([out, move], axis=1)
    for h in horizons:
        out[f"already_up_share_{h}"] = _safe_div(out["already_up"], out[f"actual_up_{h}_price"])
        out[f"already_dn_share_{h}"] = _safe_div(out["already_dn"], out[f"actual_dn_{h}_price"])
        out[f"already_abs_share_max_{h}"] = out[[f"already_up_share_{h}", f"already_dn_share_{h}"]].max(axis=1)
        out[f"actual_residual_up_{h}_by_subtraction"] = np.clip(out[f"actual_up_{h}_price"] - out["already_up"], 0.0, None)
        out[f"actual_residual_dn_{h}_by_subtraction"] = np.clip(out[f"actual_dn_{h}_price"] - out["already_dn"], 0.0, None)
        out[f"pred_residual_up_{h}_by_subtraction"] = np.clip(out[f"pred_up_{h}_price"] - out["already_up"], 0.0, None)
        out[f"pred_residual_dn_{h}_by_subtraction"] = np.clip(out[f"pred_dn_{h}_price"] - out["already_dn"], 0.0, None)
        out[f"actual_residual_log_ratio_{h}"] = safe_log_ratio(
            out[f"actual_residual_up_{h}_by_subtraction"].to_numpy(),
            out[f"actual_residual_dn_{h}_by_subtraction"].to_numpy(),
        )
        out[f"pred_residual_log_ratio_{h}"] = safe_log_ratio(
            out[f"pred_residual_up_{h}_by_subtraction"].to_numpy(),
            out[f"pred_residual_dn_{h}_by_subtraction"].to_numpy(),
        )
    return out


def attach_future_from_entry_columns(rows: pd.DataFrame, ohlc: pd.DataFrame, horizons: tuple[int, ...]) -> pd.DataFrame:
    out = rows.copy()
    indexed = ohlc.set_index("time", drop=False)
    for h in horizons:
        future_up = []
        future_dn = []
        bars_after = []
        for row in out.itertuples(index=False):
            end_time = getattr(row, f"label_end_time_{h}")
            if pd.isna(row.entry_time) or pd.isna(row.entry_open) or pd.isna(end_time):
                future_up.append(np.nan)
                future_dn.append(np.nan)
                bars_after.append(0)
                continue
            window = indexed.loc[(indexed.index >= row.entry_time) & (indexed.index <= end_time)]
            if window.empty:
                future_up.append(np.nan)
                future_dn.append(np.nan)
                bars_after.append(0)
                continue
            entry_open = float(row.entry_open)
            future_up.append(_price_float(max(float(window["high"].max()) - entry_open, 0.0)))
            future_dn.append(_price_float(max(entry_open - float(window["low"].min()), 0.0)))
            bars_after.append(int(len(window)))
        out[f"future_up_from_entry_{h}"] = future_up
        out[f"future_dn_from_entry_{h}"] = future_dn
        out[f"bars_after_entry_{h}"] = bars_after
        out[f"future_entry_log_ratio_{h}"] = safe_log_ratio(
            out[f"future_up_from_entry_{h}"].to_numpy(),
            out[f"future_dn_from_entry_{h}"].to_numpy(),
        )
    return out


def _corr(a: pd.Series, b: pd.Series) -> float | None:
    valid = pd.DataFrame({"a": a, "b": b}).replace([np.inf, -np.inf], np.nan).dropna()
    if len(valid) < 3 or valid["a"].nunique() <= 1 or valid["b"].nunique() <= 1:
        return None
    return float(stats.spearmanr(valid["a"], valid["b"])[0])


def _safe_float(value) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _summarize_subset(subset: pd.DataFrame, h: int) -> dict:
    if len(subset):
        strong_threshold = subset[f"pred_log_ratio_{h}"].abs().quantile(CONFIG.strong_pred_quantile)
        strong_subset = subset.loc[subset[f"pred_log_ratio_{h}"].abs() >= strong_threshold]
    else:
        strong_threshold = np.nan
        strong_subset = subset
    return {
        "rows": int(len(subset)),
        "median_already_up_share": _safe_float(subset[f"already_up_share_{h}"].median()) if len(subset) else None,
        "median_already_dn_share": _safe_float(subset[f"already_dn_share_{h}"].median()) if len(subset) else None,
        "p90_already_up_share": _safe_float(subset[f"already_up_share_{h}"].quantile(0.90)) if len(subset) else None,
        "p90_already_dn_share": _safe_float(subset[f"already_dn_share_{h}"].quantile(0.90)) if len(subset) else None,
        "p75_already_abs_share_max": _safe_float(subset[f"already_abs_share_max_{h}"].quantile(0.75)) if len(subset) else None,
        "share_already_abs_over_50pct": _safe_float((subset[f"already_abs_share_max_{h}"] >= 0.50).mean()) if len(subset) else None,
        "share_already_abs_over_100pct": _safe_float((subset[f"already_abs_share_max_{h}"] >= 1.00).mean()) if len(subset) else None,
        "share_future_up_zero": _safe_float((subset[f"future_up_from_entry_{h}"] <= 0.0).mean()) if len(subset) else None,
        "share_future_dn_zero": _safe_float((subset[f"future_dn_from_entry_{h}"] <= 0.0).mean()) if len(subset) else None,
        "pred_vs_actual_log_ratio_spearman": _corr(subset[f"pred_log_ratio_{h}"], subset[f"actual_log_ratio_{h}"]),
        "pred_vs_future_entry_log_ratio_spearman": _corr(subset[f"pred_log_ratio_{h}"], subset[f"future_entry_log_ratio_{h}"]),
        "pred_residual_vs_actual_residual_log_ratio_spearman": _corr(
            subset[f"pred_residual_log_ratio_{h}"], subset[f"actual_residual_log_ratio_{h}"]
        ),
        "actual_residual_vs_direct_future_log_ratio_spearman": _corr(
            subset[f"actual_residual_log_ratio_{h}"], subset[f"future_entry_log_ratio_{h}"]
        ),
        "strong_abs_pred_log_ratio": {
            "threshold": _safe_float(strong_threshold),
            "rows": int(len(strong_subset)),
            "median_already_abs_share_max": _safe_float(strong_subset[f"already_abs_share_max_{h}"].median()) if len(strong_subset) else None,
            "share_already_abs_over_100pct": _safe_float((strong_subset[f"already_abs_share_max_{h}"] >= 1.00).mean()) if len(strong_subset) else None,
            "pred_vs_future_entry_log_ratio_spearman": _corr(
                strong_subset[f"pred_log_ratio_{h}"], strong_subset[f"future_entry_log_ratio_{h}"]
            ),
        },
    }


def summarize_already_moved(rows: pd.DataFrame, horizons: tuple[int, ...]) -> dict:
    summary = {}
    for h in horizons:
        entry = _summarize_subset(rows, h)
        for direction in (-1, 1):
            entry[f"dir_{direction}"] = _summarize_subset(rows.loc[rows["fractal0_direction"] == direction], h)
        summary[f"h{h}"] = entry
    return summary


def ohlc_alignment_report(ohlc: pd.DataFrame) -> dict:
    diffs = ohlc["time"].sort_values().diff().dropna()
    one_hour = pd.Timedelta(hours=1)
    return {
        "rows": int(len(ohlc)),
        "timestamps_unique": bool(ohlc["time"].is_unique),
        "timestamps_monotonic": bool(ohlc["time"].is_monotonic_increasing),
        "non_1h_gap_count": int((diffs != one_hour).sum()),
    }


def label_window_contract_report(rows: pd.DataFrame, horizons: tuple[int, ...]) -> dict:
    report = {"status": "PASS", "per_horizon": {}}
    for h in horizons:
        valid = rows.loc[
            rows[f"actual_up_{h}_price"].notna()
            & rows[f"actual_dn_{h}_price"].notna()
            & rows[f"reconstructed_up_{h}"].notna()
            & rows[f"reconstructed_dn_{h}"].notna()
        ]
        if valid.empty:
            report["status"] = "LABEL_WINDOW_CONTRACT_FAILED"
            report["per_horizon"][f"h{h}"] = {
                "rows_compared": 0,
                "up_match_rate": 0.0,
                "dn_match_rate": 0.0,
                "max_up_abs_diff": None,
                "max_dn_abs_diff": None,
            }
            continue
        up_diff = (valid[f"actual_up_{h}_price"] - valid[f"reconstructed_up_{h}"]).abs()
        dn_diff = (valid[f"actual_dn_{h}_price"] - valid[f"reconstructed_dn_{h}"]).abs()
        up_match = float((up_diff <= CONFIG.label_match_abs_tolerance).mean())
        dn_match = float((dn_diff <= CONFIG.label_match_abs_tolerance).mean())
        report["per_horizon"][f"h{h}"] = {
            "rows_compared": int(len(valid)),
            "up_match_rate": up_match,
            "dn_match_rate": dn_match,
            "max_up_abs_diff": float(up_diff.max()),
            "max_dn_abs_diff": float(dn_diff.max()),
        }
        if up_match < CONFIG.label_match_min_rate or dn_match < CONFIG.label_match_min_rate:
            report["status"] = "LABEL_WINDOW_CONTRACT_FAILED"
    return report


def select_label_window_contract(rows: pd.DataFrame, ohlc: pd.DataFrame, horizons: tuple[int, ...]) -> dict:
    candidate = rows.copy()
    for h in horizons:
        candidate = pd.concat([candidate, reconstruct_window_moves(candidate, ohlc, horizon=h)], axis=1)
    report = label_window_contract_report(candidate, horizons)
    return {"status": report["status"], "contract": "next_h_ohlc_bars_after_fractal_bar", "attempts": [report]}


def coverage_disclosure(rows: pd.DataFrame, horizons: tuple[int, ...]) -> dict:
    full_window_mask = np.ones(len(rows), dtype=bool)
    for h in horizons:
        full_window_mask &= rows[f"bars_in_window_{h}"].to_numpy() >= h
        full_window_mask &= rows[f"bars_after_entry_{h}"].to_numpy() > 0
    used = rows["fractal0_price"].notna().to_numpy() & rows["entry_open"].notna().to_numpy() & full_window_mask
    rows["used_in_summary"] = used
    return {
        "rows_total": int(len(rows)),
        "rows_with_fractal0": int(rows["fractal0_price"].notna().sum()),
        "rows_with_entry": int(rows["entry_open"].notna().sum()),
        "rows_with_full_label_window": int(full_window_mask.sum()),
        "rows_used_in_summary": int(used.sum()),
        "dropped_missing_fractal0": int(rows["fractal0_price"].isna().sum()),
        "dropped_missing_entry": int(rows["entry_open"].isna().sum()),
        "dropped_missing_full_window": int((~full_window_mask).sum()),
    }


def _fit_fixed_model(train_frame: pd.DataFrame, eval_frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    train_x = foundation.build_updn_features(train_frame, CONFIG.profile)
    eval_x = foundation.build_updn_features(eval_frame, CONFIG.profile)
    train_y = foundation.extract_updn_targets(train_frame)
    eval_y = foundation.extract_updn_targets(eval_frame)
    pred, _ = foundation._train_predict_model(CONFIG.model_key, CONFIG.seed, train_x, train_y, eval_x)
    return eval_y, pred


def _attach_denormalized_targets(rows: pd.DataFrame, y_true: np.ndarray, y_pred: np.ndarray, params: dict[str, np.ndarray]) -> pd.DataFrame:
    out = rows.copy()
    true_price = denormalize_updn_matrix(y_true, out["source_split"], out["source_row_idx"], params)
    pred_price = denormalize_updn_matrix(y_pred, out["source_split"], out["source_row_idx"], params)
    for idx, name in enumerate(foundation.UPDN_TARGET_COLUMNS):
        out[f"actual_{name}_price"] = true_price[:, idx]
        out[f"pred_{name}_price"] = pred_price[:, idx]
    for h in CONFIG.horizons:
        out[f"actual_log_ratio_{h}"] = safe_log_ratio(
            out[f"actual_up_{h}_price"].to_numpy(), out[f"actual_dn_{h}_price"].to_numpy()
        )
        out[f"pred_log_ratio_{h}"] = safe_log_ratio(
            out[f"pred_up_{h}_price"].to_numpy(), out[f"pred_dn_{h}_price"].to_numpy()
        )
    return out


def _model_reproduction_report(rows: pd.DataFrame) -> dict:
    h = 3
    rho = _corr(rows[f"pred_log_ratio_{h}"], rows[f"actual_log_ratio_{h}"])
    status = "PASS" if rho is not None and rho >= CONFIG.model_repro_min_h3_spearman else "MODEL_REPRO_FAILED"
    return {
        "status": status,
        "horizon": h,
        "pred_vs_actual_log_ratio_spearman": rho,
        "min_required_spearman": CONFIG.model_repro_min_h3_spearman,
    }


def run_already_moved_audit(
    output_json: Path = ALREADY_MOVED_JSON_PATH,
    output_rows: Path = ALREADY_MOVED_ROWS_PATH,
) -> dict:
    started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    output_json.parent.mkdir(parents=True, exist_ok=True)
    source_frames = load_source_frames()
    split_frames = load_split_frames_with_source()
    ohlc = load_ohlc()
    ohlc_report = ohlc_alignment_report(ohlc)
    params = load_source_updn_params()
    source_alignment = validate_source_row_alignment(source_frames, split_frames, params)
    if source_alignment["status"] != "PASS":
        report = {
            "experiment": "regression_updn_already_moved_audit",
            "status": source_alignment["status"],
            "artifact_status": "DIAGNOSTIC_ONLY",
            "config": dataclasses.asdict(CONFIG),
            "preflight": {"source_row_alignment": source_alignment, "ohlc_alignment": ohlc_report},
        }
        output_json.write_text(json.dumps(report, indent=2, default=str))
        return report
    if not ohlc_report["timestamps_unique"] or not ohlc_report["timestamps_monotonic"]:
        report = {
            "experiment": "regression_updn_already_moved_audit",
            "status": "OHLC_ALIGNMENT_FAILED",
            "artifact_status": "DIAGNOSTIC_ONLY",
            "config": dataclasses.asdict(CONFIG),
            "preflight": {"source_row_alignment": source_alignment, "ohlc_alignment": ohlc_report},
        }
        output_json.write_text(json.dumps(report, indent=2, default=str))
        return report

    train_frame = split_frames["train_core"]
    all_summaries = {}
    all_preflight = {}
    csv_frames = []

    for split_name in (CONFIG.primary_split, *CONFIG.disclosure_splits):
        frame = split_frames[split_name].reset_index(drop=True)
        y_true, y_pred = _fit_fixed_model(train_frame, frame)
        rows, entry_report = attach_entry_open(frame, ohlc)
        rows = _attach_denormalized_targets(rows, y_true, y_pred, params)
        model_repro = _model_reproduction_report(rows) if split_name == CONFIG.primary_split else None
        if split_name == CONFIG.primary_split and model_repro["status"] != "PASS":
            rows.assign(analysis_split=split_name).to_csv(output_rows, index=False)
            report = {
                "experiment": "regression_updn_already_moved_audit",
                "status": "MODEL_REPRO_FAILED",
                "artifact_status": "DIAGNOSTIC_ONLY",
                "config": dataclasses.asdict(CONFIG),
                "preflight": {
                    split_name: {
                        **entry_report,
                        "source_row_alignment": source_alignment,
                        "ohlc_alignment": ohlc_report,
                        "model_reproduction": model_repro,
                    }
                },
            }
            output_json.write_text(json.dumps(report, indent=2, default=str))
            return report

        selected_contract = select_label_window_contract(rows, ohlc, CONFIG.horizons)
        all_preflight[split_name] = {
            **entry_report,
            "source_row_alignment": source_alignment,
            "ohlc_alignment": ohlc_report,
            "label_window_selection": selected_contract,
        }
        if model_repro is not None:
            all_preflight[split_name]["model_reproduction"] = model_repro
        if selected_contract["status"] != "PASS" and split_name == CONFIG.primary_split:
            rows.assign(analysis_split=split_name).to_csv(output_rows, index=False)
            report = {
                "experiment": "regression_updn_already_moved_audit",
                "status": "LABEL_WINDOW_CONTRACT_FAILED",
                "artifact_status": "DIAGNOSTIC_ONLY",
                "config": dataclasses.asdict(CONFIG),
                "preflight": all_preflight,
            }
            output_json.write_text(json.dumps(report, indent=2, default=str))
            return report
        if selected_contract["status"] != "PASS":
            continue

        for h in CONFIG.horizons:
            rows = pd.concat([rows, reconstruct_window_moves(rows, ohlc, horizon=h)], axis=1)

        rows = attach_already_moved_columns(rows, CONFIG.horizons)
        rows = attach_future_from_entry_columns(rows, ohlc, CONFIG.horizons)
        coverage = coverage_disclosure(rows, CONFIG.horizons)
        used_rows = rows.loc[rows["used_in_summary"]].copy()
        all_preflight[split_name]["coverage_disclosure"] = coverage
        all_summaries[split_name] = {
            "coverage_disclosure": coverage,
            "already_moved": summarize_already_moved(used_rows, CONFIG.horizons),
        }
        rows["analysis_split"] = split_name
        csv_frames.append(rows)

    row_table = pd.concat(csv_frames, ignore_index=True) if csv_frames else pd.DataFrame()
    row_table.to_csv(output_rows, index=False)
    report = {
        "experiment": "regression_updn_already_moved_audit",
        "status": "PASS_DIAGNOSTIC",
        "artifact_status": "DIAGNOSTIC_ONLY",
        "started_at": started_at,
        "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "config": dataclasses.asdict(CONFIG),
        "preflight": all_preflight,
        "summary": all_summaries,
        "row_artifact": str(output_rows),
    }
    output_json.write_text(json.dumps(report, indent=2, default=str))
    return report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--regression-updn-already-moved-audit", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.regression_updn_already_moved_audit:
        report = run_already_moved_audit()
        print({"status": report["status"], "json": str(ALREADY_MOVED_JSON_PATH)})
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
