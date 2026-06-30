from __future__ import annotations

# =============================================================================
# Файл: analyze_stage6_2_range_w1_postmortem.py
# Назначение: Диагностика доминирования `range_w1_atr` в Stage 6.2 без переобучения.
# Обновлён: 2026-06-30
# Зависимости:
#   Входные данные:
#     - ML/reports/stage6_2_h12_price_action_feature_family.json
#     - DATA/Nero_XAUUSD_*_labeled.csv
#     - DATA/XAUUSD_H1_OHLC.csv
#   Выходные данные:
#     - ML/reports/stage6_2_range_w1_postmortem.json
#     - docs/reports/2026-06-30-stage6_2-range-w1-postmortem.md
#   Внутренние зависимости:
#     - ML/baseline/benchmark_stage6_2_price_action.py
#     - ML/baseline/benchmark_stage6_outcome_based.py
# Использование:
#   ./.venv/bin/python ML/baseline/analyze_stage6_2_range_w1_postmortem.py
# Примечания:
#   - DIAGNOSTIC_ONLY: скрипт не обучает модель и не выбирает новый профиль.
# =============================================================================

import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ML.baseline.benchmark_stage6_outcome_based import STAGE6_0_CONFIG, stage6_load_labeled_splits
from ML.baseline.benchmark_stage6_2_price_action import (
    STAGE6_2_CONFIG,
    stage62_build_price_action_features,
    stage62_load_ohlc_frame,
    stage62_price_action_feature_names,
)

STAGE62_JSON_PATH = REPO_ROOT / "ML/reports/stage6_2_h12_price_action_feature_family.json"
POSTMORTEM_JSON_PATH = REPO_ROOT / "ML/reports/stage6_2_range_w1_postmortem.json"
POSTMORTEM_REPORT_PATH = REPO_ROOT / "docs/reports/2026-06-30-stage6_2-range-w1-postmortem.md"


def bucketize_quantiles(values: pd.Series, n_bins: int = 5) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.notna().sum() == 0:
        return pd.Series(["missing"] * len(values), index=values.index, dtype="object")
    ranked = numeric.rank(method="first")
    bin_count = min(n_bins, int(ranked.notna().sum()))
    bins = pd.qcut(ranked, q=bin_count, labels=False, duplicates="drop")
    out = bins.astype("Int64").astype("object")
    out = out.where(out.isna(), out.map(lambda x: f"q{int(x) + 1}"))
    return out.fillna("missing").astype(str)


def safe_corr(a: pd.Series, b: pd.Series) -> float | None:
    left = pd.to_numeric(a, errors="coerce")
    right = pd.to_numeric(b, errors="coerce")
    mask = left.notna() & right.notna()
    if int(mask.sum()) < 3:
        return None
    left = left[mask]
    right = right[mask]
    if float(left.std(ddof=0)) == 0.0 or float(right.std(ddof=0)) == 0.0:
        return None
    return float(left.corr(right))


def summarize_binary_by_bucket(df: pd.DataFrame, bucket_col: str, target_col: str) -> list[dict]:
    rows: list[dict] = []
    for bucket, group in df.groupby(bucket_col, sort=True, dropna=False):
        target = pd.to_numeric(group[target_col], errors="coerce").dropna()
        rows.append({
            "bucket": str(bucket),
            "n": int(len(target)),
            "positive_rate": float(target.mean()) if len(target) else None,
        })
    return rows


def summarize_numeric_by_period(
    df: pd.DataFrame,
    value_col: str,
    time_col: str = "time",
) -> list[dict]:
    work = df[[time_col, value_col]].copy()
    work["year"] = pd.to_datetime(work[time_col], format="%Y.%m.%d %H:%M", errors="coerce").dt.year
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    work = work.dropna(subset=["year", value_col])
    rows: list[dict] = []
    for year, group in work.groupby("year", sort=True):
        values = group[value_col]
        rows.append({
            "year": int(year),
            "n": int(len(values)),
            "mean": float(values.mean()),
            "median": float(values.median()),
        })
    return rows


def build_diagnostic_frame(
    split: dict[str, pd.DataFrame],
    ohlc: pd.DataFrame,
    split_name: str,
) -> pd.DataFrame:
    df = split[split_name].reset_index(drop=True).copy()
    feature_names = stage62_price_action_feature_names("h12_price_action_core")
    features = stage62_build_price_action_features(df, "h12_price_action_core", ohlc=ohlc)
    feature_df = pd.DataFrame(features, columns=feature_names)
    out = pd.concat([df.reset_index(drop=True), feature_df], axis=1)
    out["split"] = split_name
    out["price_action_zero_vector"] = feature_df.abs().sum(axis=1) == 0.0
    out["range_w1_bucket"] = bucketize_quantiles(out["range_w1_atr"], n_bins=5)
    keep = [
        "time",
        "split",
        "ATR",
        "stage6_side",
        "stage6_definitive_tp_vs_sl_flag",
        "stage6_pnl_r",
        "range_w1_atr",
        "range_w1_bucket",
        "close_to_high_w1_atr",
        "close_to_low_w1_atr",
        "bar_range_1_atr",
        "price_action_zero_vector",
    ]
    for col in keep:
        if col not in out.columns:
            out[col] = np.nan
    return out[keep]


def _top_importance_ratio(items: list[dict]) -> float | None:
    if len(items) < 2:
        return None
    first = float(items[0].get("auc_drop", items[0].get("auc_drop_mean", 0.0)) or 0.0)
    second = float(items[1].get("auc_drop", items[1].get("auc_drop_mean", 0.0)) or 0.0)
    if second == 0.0:
        return None
    return float(first / second)


def _mean_or_none(values: pd.Series) -> float | None:
    values = pd.to_numeric(values, errors="coerce").dropna()
    return float(values.mean()) if len(values) else None


def _summarize_group(df: pd.DataFrame, group_cols: list[str]) -> list[dict]:
    work = df.copy()
    work["year"] = pd.to_datetime(work["time"], format="%Y.%m.%d %H:%M", errors="coerce").dt.year
    rows: list[dict] = []
    for keys, group in work.dropna(subset=group_cols).groupby(group_cols, sort=True):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = {}
        for col, val in zip(group_cols, keys):
            out_col = "side" if col == "stage6_side" else col
            row[out_col] = int(val) if col == "year" else str(val)
        row.update({
            "n": int(len(group)),
            "tp_rate": _mean_or_none(group["stage6_definitive_tp_vs_sl_flag"]),
            "mean_pnl_r": _mean_or_none(group["stage6_pnl_r"]),
            "range_w1_target_corr": safe_corr(group["range_w1_atr"], group["stage6_definitive_tp_vs_sl_flag"]),
            "range_w1_pnl_corr": safe_corr(group["range_w1_atr"], group["stage6_pnl_r"]),
        })
        rows.append(row)
    return rows


def _seed_stability(seed_runs: list[dict]) -> dict:
    p_values = [
        float(row["permutation_p_value"])
        for row in seed_runs
        if row.get("permutation_p_value") is not None
    ]
    auc_values = [float(row["val_auc"]) for row in seed_runs if row.get("val_auc") is not None]
    pf_values = [float(row["pf"]) for row in seed_runs if row.get("pf") is not None]
    thresholds = [float(row["threshold"]) for row in seed_runs if row.get("threshold") is not None]
    return {
        "seed_count": int(len(seed_runs)),
        "permutation_p_value_min": float(min(p_values)) if p_values else None,
        "permutation_p_value_max": float(max(p_values)) if p_values else None,
        "permutation_p_value_spread": float(max(p_values) - min(p_values)) if p_values else None,
        "val_auc_min": float(min(auc_values)) if auc_values else None,
        "val_auc_max": float(max(auc_values)) if auc_values else None,
        "val_auc_spread": float(max(auc_values) - min(auc_values)) if auc_values else None,
        "pf_min": float(min(pf_values)) if pf_values else None,
        "pf_max": float(max(pf_values)) if pf_values else None,
        "thresholds": thresholds,
    }


def _selected_trade_analysis(df: pd.DataFrame, seed_runs: list[dict]) -> dict:
    rows: list[dict] = []
    for run in seed_runs:
        seed = int(run["seed"])
        score_col = f"y_score_core_seed{seed}"
        threshold = run.get("threshold")
        if score_col not in df.columns or threshold is None:
            continue
        scores = pd.to_numeric(df[score_col], errors="coerce")
        selected = df[scores >= float(threshold)]
        non_selected = df[scores < float(threshold)]
        rows.append({
            "seed": seed,
            "threshold": float(threshold),
            "selected_n": int(len(selected)),
            "non_selected_n": int(len(non_selected)),
            "selected_tp_rate": _mean_or_none(selected["stage6_definitive_tp_vs_sl_flag"]),
            "non_selected_tp_rate": _mean_or_none(non_selected["stage6_definitive_tp_vs_sl_flag"]),
            "selected_mean_pnl_r": _mean_or_none(selected["stage6_pnl_r"]),
            "non_selected_mean_pnl_r": _mean_or_none(non_selected["stage6_pnl_r"]),
            "selected_bucket_target_rates": summarize_binary_by_bucket(
                selected,
                "range_w1_bucket",
                "stage6_definitive_tp_vs_sl_flag",
            ),
        })
    return {"seed_count": int(len(seed_runs)), "available_seed_count": int(len(rows)), "per_seed": rows}


def _permutation_context(primary: dict) -> dict:
    baseline = primary.get("permutation_baseline", {})
    seed_runs = primary.get("seed_runs", [])
    per_seed = []
    for idx, row in enumerate(baseline.get("per_seed", [])):
        observed = row.get("observed_pf")
        p95 = row.get("permuted_pf_p95")
        seed = row.get("seed")
        if seed is None and idx < len(seed_runs):
            seed = seed_runs[idx].get("seed")
        per_seed.append({
            "seed": seed,
            "observed_pf": observed,
            "permuted_pf_median": row.get("permuted_pf_median"),
            "permuted_pf_p95": p95,
            "observed_minus_permuted_p95": (
                float(observed) - float(p95)
                if observed is not None and p95 is not None
                else None
            ),
            "empirical_p_value": row.get("empirical_p_value"),
        })
    return {
        "primary_p_value": baseline.get("empirical_p_value"),
        "required_p_value": 0.10,
        "observed_pf_median": baseline.get("observed_pf_median"),
        "observed_pf_min": baseline.get("observed_pf_min"),
        "observed_pf_max": baseline.get("observed_pf_max"),
        "per_seed": per_seed,
    }


def attach_core_seed_scores(stage62_report: dict, frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for run in stage62_report.get("raw_runs", []):
        if run.get("profile") != "h12_price_action_core":
            continue
        seed = int(run["seed"])
        scores = run.get("predictions", {}).get("val_stop", {}).get("y_score_all", [])
        if len(scores) == len(out):
            out[f"y_score_core_seed{seed}"] = pd.to_numeric(pd.Series(scores), errors="coerce")
    return out


def _evidence_strength(post: dict) -> str:
    p_value = post["permutation_context"]["primary_p_value"]
    zero_share = post["activity_proxy_checks"]["zero_vector_share"]
    if p_value is None:
        return "insufficient"
    if zero_share is not None and float(zero_share) > 0.20:
        return "artifact_suspected"
    if float(p_value) > 0.10:
        return "weak"
    if any(row.get("range_w1_target_corr") is None for row in post["side_analysis"]):
        return "insufficient"
    return "not_artifact_detected"


def _frame_disclosure(frames: dict[str, pd.DataFrame]) -> dict:
    disclosure = {}
    for split_name, frame in frames.items():
        zero_rows = int(frame["price_action_zero_vector"].sum()) if len(frame) else 0
        disclosure[split_name] = {
            "rows": int(len(frame)),
            "zero_vector_rows": zero_rows,
            "zero_vector_share": float(zero_rows / len(frame)) if len(frame) else None,
            "range_w1_target_corr_non_zero": safe_corr(
                frame.loc[~frame["price_action_zero_vector"].astype(bool), "range_w1_atr"],
                frame.loc[
                    ~frame["price_action_zero_vector"].astype(bool),
                    "stage6_definitive_tp_vs_sl_flag",
                ],
            ),
        }
    return disclosure


def build_postmortem(stage62_report: dict, frames: dict[str, pd.DataFrame]) -> dict:
    primary = stage62_report["summary"]["h12_price_action_core"]
    importance = primary.get("top_feature_importance", [])
    seed_runs = primary.get("seed_runs", [])
    val_frame = attach_core_seed_scores(stage62_report, frames["val_stop"])
    non_zero_val = val_frame[~val_frame["price_action_zero_vector"].astype(bool)].copy()
    post = {
        "source_stage62_status": stage62_report.get("gate", {}).get("status", stage62_report.get("status")),
        "artifact_consistency": {
            "primary_profile": "h12_price_action_core",
            "primary_p_value": primary.get("permutation_baseline", {}).get("empirical_p_value"),
            "top_feature_from_stage62_json": importance[0]["feature"] if importance else None,
            "gate_status_from_stage62_json": stage62_report.get(
                "gate",
                {},
            ).get("status", stage62_report.get("status")),
        },
        "dominance": {
            "top_feature": importance[0]["feature"] if importance else None,
            "top_to_second_auc_drop_ratio": _top_importance_ratio(importance),
            "range_w1_target_corr": safe_corr(
                non_zero_val["range_w1_atr"],
                non_zero_val["stage6_definitive_tp_vs_sl_flag"],
            ),
            "range_w1_pnl_corr": safe_corr(non_zero_val["range_w1_atr"], non_zero_val["stage6_pnl_r"]),
            "bucket_target_rates": summarize_binary_by_bucket(
                non_zero_val,
                "range_w1_bucket",
                "stage6_definitive_tp_vs_sl_flag",
            ),
            "yearly_range_w1": summarize_numeric_by_period(non_zero_val, "range_w1_atr"),
            "zero_vector_rows": int(val_frame["price_action_zero_vector"].sum()),
            "rows": int(len(val_frame)),
        },
        "stability": _seed_stability(seed_runs),
        "selected_trade_analysis": _selected_trade_analysis(non_zero_val, seed_runs),
        "side_analysis": _summarize_group(non_zero_val, ["stage6_side"]),
        "year_side_matrix": _summarize_group(non_zero_val, ["year", "stage6_side"]),
        "activity_proxy_checks": {
            "range_w1_vs_atr_corr": (
                safe_corr(non_zero_val["range_w1_atr"], non_zero_val["ATR"])
                if "ATR" in non_zero_val.columns
                else None
            ),
            "range_w1_vs_bar_range_1_corr": safe_corr(non_zero_val["range_w1_atr"], non_zero_val["bar_range_1_atr"]),
            "range_w1_by_year": summarize_numeric_by_period(non_zero_val, "range_w1_atr"),
            "zero_vector_share": float(val_frame["price_action_zero_vector"].mean()) if len(val_frame) else None,
        },
        "permutation_context": _permutation_context(primary),
        "split_disclosure": _frame_disclosure(frames),
        "verdict": {
            "artifact_status": "DIAGNOSTIC_ONLY",
            "promote_stage6_2": False,
            "next_research_step": "Regression Up/Dn target foundation",
        },
    }
    post["evidence_strength"] = _evidence_strength(post)
    return post


def write_report(postmortem: dict) -> str:
    consistency = postmortem["artifact_consistency"]
    dominance = postmortem["dominance"]
    stability = postmortem["stability"]
    selected = postmortem["selected_trade_analysis"]
    activity = postmortem["activity_proxy_checks"]
    permutation = postmortem["permutation_context"]
    verdict = postmortem["verdict"]
    disclosure = postmortem["split_disclosure"]
    lines = [
        "# Stage 6.2 Range W1 Post-Mortem",
        "",
        "> **Дата**: 2026-06-30",
        "> **Статус**: Completed",
        "> **Вердикт**: DIAGNOSTIC_ONLY",
        "> **Цель**: Check why `range_w1_atr` dominates Stage 6.2 and why the stability check remains weak.",
        "",
        "## Sources And Commands",
        "",
        "- Source Stage 6.2 JSON: `ML/reports/stage6_2_h12_price_action_feature_family.json`.",
        "- Generated JSON: `ML/reports/stage6_2_range_w1_postmortem.json`.",
        "- Command: `./.venv/bin/python ML/baseline/analyze_stage6_2_range_w1_postmortem.py`.",
        "- Scope: no retraining, no new horizon/ATR/TP/SL/profile search.",
        "",
        "## Artifact Consistency",
        "",
        f"- Primary profile: `{consistency['primary_profile']}`.",
        f"- Stage 6.2 gate status: `{consistency['gate_status_from_stage62_json']}`.",
        f"- Stage 6.2 primary p-value: `{consistency['primary_p_value']}`.",
        f"- Top feature from Stage 6.2 JSON: `{consistency['top_feature_from_stage62_json']}`.",
        "",
        "## Multiple Testing Context",
        "",
        "- This post-mortem runs after the fixed Stage 6.2 search: 5 profiles x 3 seeds.",
        "- It does not train models, add features, search thresholds, or change the gate.",
        "- `val_stop` is used only to explain the already failed Stage 6.2 gate.",
        "- `diagnostic_holdout` and `low_n_disclosure` remain disclosure-only.",
        "",
        "## Facts",
        "",
        f"- Top feature: `{dominance['top_feature']}`.",
        f"- Top/second importance ratio: `{dominance['top_to_second_auc_drop_ratio']}`.",
        f"- `range_w1_atr` vs target correlation on non-zero `val_stop`: `{dominance['range_w1_target_corr']}`.",
        f"- `range_w1_atr` vs PnL correlation on non-zero `val_stop`: `{dominance['range_w1_pnl_corr']}`.",
        f"- Primary permutation p-value: `{permutation['primary_p_value']}`; required `<= {permutation['required_p_value']}`.",
        f"- Seed p-value range: `{stability['permutation_p_value_min']}` to `{stability['permutation_p_value_max']}`.",
        f"- Zero-vector rows on `val_stop`: `{dominance['zero_vector_rows']}/{dominance['rows']}`.",
        f"- Evidence strength: `{postmortem['evidence_strength']}`.",
        "",
        "## Selected Trade Analysis",
        "",
        f"- Seeds available for selected-trade analysis: `{selected['available_seed_count']}/{selected['seed_count']}`.",
        "- See JSON section `selected_trade_analysis.per_seed` for selected vs non-selected TP-rate, PnL, and bucket rates.",
        "",
        "## Side And Year Disclosure",
        "",
        "- See JSON section `side_analysis` for BUY/SELL counts, TP-rate, PnL, and correlations.",
        "- See JSON section `year_side_matrix` for year x side breakdown.",
        "",
        "## Activity Proxy Checks",
        "",
        f"- `range_w1_atr` vs `ATR` correlation: `{activity['range_w1_vs_atr_corr']}`.",
        f"- `range_w1_atr` vs `bar_range_1_atr` correlation: `{activity['range_w1_vs_bar_range_1_corr']}`.",
        f"- Zero-vector share on `val_stop`: `{activity['zero_vector_share']}`.",
        "",
        "## Validation Disclosure",
        "",
        f"- `val_stop`: `{disclosure['val_stop']['zero_vector_rows']}/{disclosure['val_stop']['rows']}` zero-vector rows.",
        f"- `diagnostic_holdout`: `{disclosure['diagnostic_holdout']['zero_vector_rows']}/{disclosure['diagnostic_holdout']['rows']}` zero-vector rows.",
        f"- `low_n_disclosure`: `{disclosure['low_n_disclosure']['zero_vector_rows']}/{disclosure['low_n_disclosure']['rows']}` zero-vector rows.",
        "- `diagnostic_holdout` and `low_n_disclosure` were not used for choosing profiles, seeds, thresholds, or gates.",
        "",
        "## Permutation Context",
        "",
        f"- Observed median PF: `{permutation['observed_pf_median']}`.",
        f"- Observed PF range: `{permutation['observed_pf_min']}` to `{permutation['observed_pf_max']}`.",
        "- See JSON section `permutation_context.per_seed` for observed PF vs median and p95 random PF by seed.",
        "",
        "## Interpretation",
        "",
        "- Facts above are measurements from the frozen Stage 6.2 artifacts.",
        "- The dominant feature is associated with the one-bar price range, but this is not enough to prove a robust trading rule.",
        "- The stability check stayed weak because observed PF was not far enough above the random-permutation comparison across seeds.",
        "- Any causal explanation remains a hypothesis unless a later fixed validation cycle tests it.",
        "",
        "This post-mortem does not change the Stage 6.2 verdict and does not promote the feature family.",
        "",
        "## Forbidden Next Steps",
        "",
        "- Do not reopen H12/ATR/TP/SL search from this result.",
        "- Do not create another small OHLC-window variant unless this report provides concrete evidence for a materially new family.",
        "",
        "## Decision",
        "",
        f"- Promote Stage 6.2: `{verdict['promote_stage6_2']}`.",
        f"- Next research step: `{verdict['next_research_step']}`.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    stage62_report = json.loads(STAGE62_JSON_PATH.read_text())
    cfg = replace(
        STAGE6_0_CONFIG,
        horizon_bars=STAGE6_2_CONFIG.horizon_bars,
        stop_offset_atr=STAGE6_2_CONFIG.stop_offset_atr,
        take_profit_atr=STAGE6_2_CONFIG.take_profit_atr,
        entry_lag_bars=STAGE6_2_CONFIG.entry_lag_bars,
    )
    split = stage6_load_labeled_splits(config=cfg)
    ohlc = stage62_load_ohlc_frame()
    frames = {
        "val_stop": build_diagnostic_frame(split, ohlc, "val_stop"),
        "diagnostic_holdout": build_diagnostic_frame(split, ohlc, "diagnostic_holdout"),
        "low_n_disclosure": build_diagnostic_frame(split, ohlc, "low_n_disclosure"),
    }
    postmortem = build_postmortem(stage62_report, frames)
    POSTMORTEM_JSON_PATH.write_text(json.dumps(postmortem, indent=2, ensure_ascii=False) + "\n")
    POSTMORTEM_REPORT_PATH.write_text(write_report(postmortem), encoding="utf-8")
    print(f"wrote {POSTMORTEM_JSON_PATH}")
    print(f"wrote {POSTMORTEM_REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
