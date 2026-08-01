"""Batch generation of MT5 entry signals for 32 movement-filter candidates.

Usage:
    ./.venv/bin/python -m ML.baseline.run_mt5_batch [--phase signals|tester|all]
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from math import ceil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
BATCH_DIR = REPO_ROOT / "ML" / "reports" / "mt5_execution_loop" / "batch"
CANDIDATES_CSV = REPO_ROOT / "ML" / "reports" / "entry_based_movement_filter_candidates.csv"
EQ_SCORES_CSV = REPO_ROOT / "ML" / "reports" / "fractal0_entry_quality_filter_scores.csv"
SOURCE_ARTIFACT_JSON = REPO_ROOT / "ML" / "reports" / "entry_based_amplitude_movement.json"

VAL_FROM = pd.Timestamp("2021-01-04")
VAL_TO = pd.Timestamp("2022-12-02")

WINE_PREFIX = Path.home() / ".mt5"
TERMINAL_EXE = WINE_PREFIX / "drive_c/Program Files/MetaTrader 5/terminal64.exe"
METAEDITOR_EXE = WINE_PREFIX / "drive_c/Program Files/MetaTrader 5/MetaEditor64.exe"
TESTER_FILES = WINE_PREFIX / "drive_c/Program Files/MetaTrader 5/Tester/Agent-127.0.0.1-3000/MQL5/Files"
TERMINAL_FILES = WINE_PREFIX / "drive_c/Program Files/MetaTrader 5/MQL5/Files"
SET_DIR = WINE_PREFIX / "drive_c/Program Files/MetaTrader 5/MQL5/Profiles/Tester"
MQ5_SOURCE = REPO_ROOT / "MT" / "MQL5" / "Experts" / "$o$imple.mq5"

TESTER_TIMEOUT_S = 1200


def make_run_id(row: dict) -> str:
    return f"{row['profile']}_{row['model_key']}_{int(float(row['horizon']))}h_thr{row['threshold_value']}"


def load_candidates() -> list[dict]:
    df = pd.read_csv(CANDIDATES_CSV)
    return df.to_dict(orient="records")


def load_eq_scores() -> pd.DataFrame:
    df = pd.read_csv(EQ_SCORES_CSV, sep=";")
    df["time_dt"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time_dt"])
    df = df[(df["time_dt"] >= VAL_FROM) & (df["time_dt"] <= VAL_TO)]
    return df


# ---------------------------------------------------------------------------
# Phase 1: Signal generation
# ---------------------------------------------------------------------------


def generate_signals(candidates: list[dict], eq_scores: pd.DataFrame) -> None:
    from ML.baseline.benchmark_entry_based_movement_filter import (
        _build_runtime_context,
        materialize_candidate_score_frames,
    )
    from ML.baseline.export_mt5_entry_signals import export_mt5_entry_signals
    from ML.baseline.prepare_mt5_entry_source import prepare_entry_quality_source

    source_artifact = json.loads(SOURCE_ARTIFACT_JSON.read_text(encoding="utf-8"))
    print("Building runtime context (loading splits, building targets)...")
    ctx = _build_runtime_context(source_artifact)
    print("Runtime context ready.")

    eq_for_join = eq_scores[["time_dt", "time", "signal_time", "side", "limit_price", "protective_stop_price", "atr"]].copy()

    n_total = len(candidates)
    n_generated = 0
    n_skipped = 0

    for i, cand in enumerate(candidates, 1):
        run_id = make_run_id(cand)
        out_dir = BATCH_DIR / run_id
        entry_csv = out_dir / "entry_signals.csv"
        entry_json = out_dir / "entry_signals.json"

        if entry_csv.exists() and entry_json.exists():
            meta = json.loads(entry_json.read_text(encoding="utf-8"))
            if (
                meta.get("rows_total", 0) > 0
                and meta.get("timing_contract") == "feature_time <= time < feature_available_time <= decision_time"
                and int(meta.get("latency_bars", -1)) == 0
            ):
                n_skipped += 1
                print(f"[{i}/{n_total}] SKIP {run_id} (exists, {meta['rows_total']} rows, timing_contract=v2)")
                continue

        print(f"[{i}/{n_total}] Generating {run_id}...")
        result = materialize_candidate_score_frames(cand, ctx)
        score_frame = result["frames"]["val_select"].copy()

        if "time" not in score_frame.columns:
            print(f"  WARNING: no time column in score frame, skipping")
            continue

        score_frame["time_dt"] = pd.to_datetime(score_frame["time"], errors="coerce")
        score_frame = score_frame.dropna(subset=["time_dt"])
        score_frame = score_frame[(score_frame["time_dt"] >= VAL_FROM) & (score_frame["time_dt"] <= VAL_TO)]

        score_cutoff = float(cand["score_cutoff"])
        filtered_scores = score_frame[score_frame["score"] >= score_cutoff]

        if filtered_scores.empty:
            print(f"  WARNING: 0 signals after score filter (cutoff={score_cutoff:.4f})")
            continue

        merged = filtered_scores.merge(eq_for_join, on="time_dt", how="inner")

        if merged.empty:
            print(f"  WARNING: 0 signals after EQ join")
            continue

        source_df = pd.DataFrame({
            "time": merged["time_y"],
            "signal_time": merged["signal_time"],
            "side": merged["side"],
            "limit_price": pd.to_numeric(merged["limit_price"], errors="coerce"),
            "protective_stop_price": pd.to_numeric(merged["protective_stop_price"], errors="coerce"),
            "atr": pd.to_numeric(merged["atr"], errors="coerce"),
        }).dropna()

        if source_df.empty:
            print(f"  WARNING: 0 signals after dropna")
            continue

        prepared = prepare_entry_quality_source(source_df, rule_id=run_id)

        out_dir.mkdir(parents=True, exist_ok=True)
        export_mt5_entry_signals(
            prepared,
            output_csv=entry_csv,
            output_json=entry_json,
            max_fill_lag_bars=6,
            run_id=run_id,
            label="mt5_batch_selection",
            latency_bars=0,
        )
        n_generated += 1
        meta = json.loads(entry_json.read_text(encoding="utf-8"))
        print(f"  OK: {meta['rows_total']} signals ({meta['buy_rows']} BUY, {meta['sell_rows']} SELL)")

    print(f"\nSignal generation done: {n_generated} generated, {n_skipped} skipped (already existed).")


# ---------------------------------------------------------------------------
# Phase 2: MT5 Tester batch loop
# ---------------------------------------------------------------------------


def compile_expert() -> bool:
    compile_log = "/tmp/sosimple_mt5_batch_compile.log"
    cmd = [
        "xvfb-run", "-a", "wine",
        str(METAEDITOR_EXE),
        f"/compile:{MQ5_SOURCE}",
        f"/log:{compile_log}",
    ]
    env = {"WINEPREFIX": str(WINE_PREFIX), "PATH": "/usr/bin:/bin:/usr/local/bin"}
    print("Compiling $o$imple.mq5...")
    subprocess.run(cmd, env={**dict(__import__("os").environ), **env}, timeout=120, capture_output=True)

    log_path = Path(compile_log)
    if not log_path.exists():
        print("ERROR: compile log not found")
        return False

    raw = log_path.read_bytes()
    try:
        text = raw.decode("utf-16-le")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")

    for line in text.splitlines():
        if "Result:" in line:
            print(f"  Compile: {line.strip()}")
            return "0 errors" in line
    print("ERROR: no Result line in compile log")
    return False


def check_liveupdate() -> bool:
    import glob as glob_mod
    pattern = str(WINE_PREFIX / "drive_c/users/*/AppData/Roaming/MetaQuotes/Terminal/*/liveupdate/**")
    files = [f for f in glob_mod.glob(pattern, recursive=True) if Path(f).is_file()]
    if files:
        print(f"WARNING: {len(files)} liveupdate files found. Move them before batch.")
        for f in files[:5]:
            print(f"  {f}")
        return False
    print("LiveUpdate check: clean.")
    return True


def check_tester_file_property() -> bool:
    text = MQ5_SOURCE.read_text(encoding="utf-8", errors="replace")
    if 'tester_file' in text and 'mt5_entry_signals.csv' in text:
        print("tester_file property: present.")
        return True
    print("WARNING: #property tester_file not found in source!")
    return False


def create_set_file(run_id: str) -> Path:
    set_name = f"mt5_batch_{run_id}.set"
    set_path = SET_DIR / set_name

    template_path = SET_DIR / "mt5_tx_lifecycle_20260731.set"
    if template_path.exists():
        raw = template_path.read_bytes()
        try:
            text = raw.decode("utf-16-le")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")

        lines = text.splitlines()
        new_lines = []
        for line in lines:
            if line.startswith("InpMT5_EventFile="):
                new_lines.append(f"InpMT5_EventFile=mt5_trade_events_{run_id}.csv")
            elif line.startswith("InpMT5_ExportNero="):
                new_lines.append("InpMT5_ExportNero=false||false||0||true||N")
            else:
                new_lines.append(line)
        content = "\r\n".join(new_lines) + "\r\n"
    else:
        content = (
            f"InpMT5_DiagnosticExecutor=true||false||0||true||N\r\n"
            f"InpMT5_EntrySignalFile=mt5_entry_signals.csv\r\n"
            f"InpMT5_EventFile=mt5_trade_events_{run_id}.csv\r\n"
            f"InpMT5_BlockBarsSinceFill0Exit=true||false||0||true||N\r\n"
            f"InpMT5_ExportNero=false||false||0||true||N\r\n"
        )

    set_path.write_bytes(content.encode("utf-16-le"))
    return set_path


def create_ini_file(run_id: str, set_filename: str, *, model: int = 1, from_date: str = "2021.01.04", to_date: str = "2022.12.02") -> Path:
    ini_path = WINE_PREFIX / "drive_c" / f"mt5_batch_{run_id}.ini"
    content = f"""[Tester]
Expert=$o$imple.ex5
ExpertParameters={set_filename}
Symbol=XAUUSD
Period=H1
Optimization=0
Model={model}
FromDate={from_date}
ToDate={to_date}
ForwardMode=0
Deposit=10000
Currency=USD
Leverage=1:500
ExecutionMode=0
Visual=0
ReplaceReport=1
ShutdownTerminal=1
UseLocal=1
UseRemote=0
UseCloud=0
"""
    ini_path.write_text(content, encoding="utf-8")
    return ini_path


def run_tester(ini_path: Path) -> bool:
    wine_ini_name = ini_path.name
    cmd = [
        "xvfb-run", "-a", "wine",
        str(TERMINAL_EXE),
        f"/config:C:\\{wine_ini_name}",
    ]
    import os
    env = {**dict(os.environ), "WINEPREFIX": str(WINE_PREFIX)}
    try:
        proc = subprocess.run(cmd, env=env, timeout=TESTER_TIMEOUT_S, capture_output=True)
        if proc.returncode != 0:
            stdout = proc.stdout.decode("utf-8", errors="replace") if isinstance(proc.stdout, bytes) else str(proc.stdout)
            stderr = proc.stderr.decode("utf-8", errors="replace") if isinstance(proc.stderr, bytes) else str(proc.stderr)
            print(f"  ERROR: tester exited with code {proc.returncode}")
            if stdout.strip():
                print(f"  tester stdout: {stdout.strip()[:500]}")
            if stderr.strip():
                print(f"  tester stderr: {stderr.strip()[:500]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"  ERROR: tester timed out after {TESTER_TIMEOUT_S}s")
        return False


def parse_events(run_id: str, events_csv: Path) -> dict | None:
    out_dir = BATCH_DIR / run_id
    metrics_json = out_dir / "metrics.json"

    cmd = [
        str(REPO_ROOT / ".venv" / "bin" / "python"),
        "-m", "ML.baseline.parse_mt5_execution_report",
        "--events", str(events_csv),
        "--output-json", str(metrics_json),
    ]
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        print(f"  ERROR parsing events: {proc.stderr[:200]}")
        return None
    if metrics_json.exists():
        return json.loads(metrics_json.read_text(encoding="utf-8"))
    return None


def run_smoke_test(candidates: list[dict]) -> bool:
    smoke_dir = BATCH_DIR / "_smoke"
    smoke_dir.mkdir(parents=True, exist_ok=True)

    cand = candidates[0]
    run_id = make_run_id(cand)
    entry_csv = BATCH_DIR / run_id / "entry_signals.csv"
    if not entry_csv.exists():
        print("SMOKE: entry CSV not found, run signal generation first.")
        return False

    print(f"SMOKE TEST: {run_id} (Model=2, 2021.01-2021.03)")

    shutil.copy2(entry_csv, TERMINAL_FILES / "mt5_entry_signals.csv")
    set_path = create_set_file("_smoke")
    ini_path = create_ini_file("_smoke", set_path.name, model=2, from_date="2021.01.04", to_date="2021.03.31")

    event_file_name = "mt5_trade_events__smoke.csv"
    events_src = TESTER_FILES / event_file_name
    events_src.unlink(missing_ok=True)

    if not run_tester(ini_path):
        return False

    if not events_src.exists():
        print(f"  ERROR: events file not found: {events_src}")
        return False

    events_dst = smoke_dir / "events.csv"
    shutil.copy2(events_src, events_dst)

    metrics = parse_events("_smoke", events_dst)
    if metrics is None:
        return False

    recon = metrics.get("reconciliation", {})
    unexplained = recon.get("class_counts", {}).get("UNEXPLAINED", -1)
    n_events = sum(recon.get("class_counts", {}).values())
    print(f"  SMOKE RESULT: positions={n_events}, UNEXPLAINED={unexplained}")
    return unexplained == 0


def run_batch(candidates: list[dict]) -> None:
    n_total = len(candidates)
    n_done = 0
    n_skipped = 0
    n_failed = 0

    for i, cand in enumerate(candidates, 1):
        run_id = make_run_id(cand)
        out_dir = BATCH_DIR / run_id
        metrics_json = out_dir / "metrics.json"
        events_csv = out_dir / "events.csv"

        if metrics_json.exists() and events_csv.exists():
            meta = json.loads(metrics_json.read_text(encoding="utf-8"))
            recon = meta.get("reconciliation", {})
            unexpl = recon.get("class_counts", {}).get("UNEXPLAINED", -1)
            if unexpl == 0:
                n_skipped += 1
                print(f"[{i}/{n_total}] SKIP {run_id} (metrics exist, UNEXPLAINED=0)")
                continue

        entry_csv = out_dir / "entry_signals.csv"
        if not entry_csv.exists():
            print(f"[{i}/{n_total}] ERROR: no entry CSV for {run_id}")
            n_failed += 1
            continue

        print(f"[{i}/{n_total}] Running tester: {run_id}...")
        t0 = time.time()

        shutil.copy2(entry_csv, TERMINAL_FILES / "mt5_entry_signals.csv")
        set_path = create_set_file(run_id)
        ini_path = create_ini_file(run_id, set_path.name)

        event_file_name = f"mt5_trade_events_{run_id}.csv"
        events_src = TESTER_FILES / event_file_name
        events_src.unlink(missing_ok=True)

        if not run_tester(ini_path):
            n_failed += 1
            continue

        if not events_src.exists():
            print(f"  ERROR: events file not found: {events_src}")
            n_failed += 1
            continue

        out_dir.mkdir(parents=True, exist_ok=True)
        events_dst = out_dir / "events.csv"
        shutil.copy2(events_src, events_dst)

        metrics = parse_events(run_id, events_dst)
        elapsed = time.time() - t0

        if metrics is None:
            n_failed += 1
            continue

        recon = metrics.get("reconciliation", {})
        unexplained = recon.get("class_counts", {}).get("UNEXPLAINED", -1)
        n_positions = recon.get("class_counts", {}).get("CLOSED_TX", 0)
        n_done += 1
        print(f"  DONE ({elapsed:.0f}s): positions={n_positions}, UNEXPLAINED={unexplained}")

    print(f"\nBatch complete: {n_done} done, {n_skipped} skipped, {n_failed} failed.")


# ---------------------------------------------------------------------------
# Phase 3: Aggregation + multiple-testing correction
# ---------------------------------------------------------------------------


def block_bootstrap_pf(pnl_series: np.ndarray, n_iter: int = 2000, block_size: int = 15, seed: int = 42) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    n = len(pnl_series)
    if n < block_size:
        block_size = max(2, n // 2)
    n_blocks = ceil(n / block_size)
    pf_samples = np.empty(n_iter)
    for i in range(n_iter):
        starts = rng.integers(0, n - block_size + 1, size=n_blocks)
        sample = np.concatenate([pnl_series[s:s + block_size] for s in starts])[:n]
        gross_profit = sample[sample > 0].sum()
        gross_loss = abs(sample[sample < 0].sum())
        pf_samples[i] = gross_profit / gross_loss if gross_loss > 0 else np.inf
    p_value = float((pf_samples <= 1.0).mean())
    bs_p05 = float(np.percentile(pf_samples, 5))
    return p_value, bs_p05


def holm_bonferroni(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    n = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    rejected = [False] * n
    for rank, (orig_idx, p) in enumerate(indexed):
        adjusted_alpha = alpha / (n - rank)
        if p <= adjusted_alpha:
            rejected[orig_idx] = True
        else:
            break
    return rejected


def compute_metrics_from_events(events_csv: Path, metrics_json: Path) -> dict | None:
    if not events_csv.exists():
        return None

    unexplained = -1
    if metrics_json.exists():
        meta = json.loads(metrics_json.read_text(encoding="utf-8"))
        recon = meta.get("reconciliation", {})
        unexplained = recon.get("class_counts", {}).get("UNEXPLAINED", -1)

    df = pd.read_csv(events_csv, sep=";")
    tx = df[df["event"] == "TX_CLOSE"].copy()
    if tx.empty:
        return {"unexplained": unexplained, "trades_count": 0}

    tx["profit"] = pd.to_numeric(tx["profit"], errors="coerce").fillna(0.0)
    tx["time_dt"] = pd.to_datetime(tx["time"], errors="coerce")
    tx["year"] = tx["time_dt"].dt.year

    pnl = tx["profit"].to_numpy(dtype=float)
    gross_profit = pnl[pnl > 0].sum()
    gross_loss = abs(pnl[pnl < 0].sum())
    pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    wins = (pnl > 0).sum()
    win_rate = wins / len(pnl) if len(pnl) > 0 else 0.0

    cumulative = np.cumsum(pnl)
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = running_max - cumulative
    max_dd = float(drawdowns.max()) if len(drawdowns) > 0 else 0.0

    buy_tx = tx[tx["side"].str.upper() == "BUY"]["profit"].to_numpy(dtype=float)
    sell_tx = tx[tx["side"].str.upper() == "SELL"]["profit"].to_numpy(dtype=float)

    def _pf(arr: np.ndarray) -> float | None:
        if len(arr) == 0:
            return None
        gp = arr[arr > 0].sum()
        gl = abs(arr[arr < 0].sum())
        return gp / gl if gl > 0 else float("inf")

    pf_by_year = {}
    gross_profit_by_year = {}
    for year in sorted(tx["year"].dropna().unique()):
        yr_pnl = tx[tx["year"] == year]["profit"].to_numpy(dtype=float)
        pf_by_year[int(year)] = _pf(yr_pnl)
        gross_profit_by_year[int(year)] = float(yr_pnl[yr_pnl > 0].sum())

    return {
        "unexplained": unexplained,
        "trades_count": int(len(pnl)),
        "profit_factor": round(pf, 4) if pf != float("inf") else None,
        "win_rate": round(win_rate, 4),
        "max_drawdown": round(max_dd, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "pf_buy": _pf(buy_tx),
        "pf_sell": _pf(sell_tx),
        "trades_buy": int(len(buy_tx)),
        "trades_sell": int(len(sell_tx)),
        "pf_by_year": pf_by_year,
        "gross_profit_by_year": gross_profit_by_year,
        "pnl_by_trade": pnl.tolist(),
    }


def aggregate_batch(candidates: list[dict]) -> dict:
    rows = []
    for cand in candidates:
        run_id = make_run_id(cand)
        out_dir = BATCH_DIR / run_id
        events_csv = out_dir / "events.csv"
        metrics_json = out_dir / "metrics.json"

        if not events_csv.exists():
            rows.append({"run_id": run_id, "status": "NO_EVENTS"})
            continue

        m = compute_metrics_from_events(events_csv, metrics_json)
        if m is None:
            rows.append({"run_id": run_id, "status": "PARSE_ERROR"})
            continue

        rows.append({
            "run_id": run_id,
            "profile": cand["profile"],
            "model_key": cand["model_key"],
            "horizon": int(float(cand["horizon"])),
            "threshold_value": float(cand["threshold_value"]),
            **m,
        })

    df = pd.DataFrame(rows)
    valid = df[df.get("unexplained", pd.Series()) == 0].copy() if "unexplained" in df.columns else df.copy()

    eligible = valid[valid["trades_count"] >= 100].copy() if "trades_count" in valid.columns else pd.DataFrame()
    diagnostic = valid[(valid["trades_count"] >= 30) & (valid["trades_count"] < 100)].copy() if "trades_count" in valid.columns else pd.DataFrame()

    bootstrap_results = []
    if not eligible.empty and "pnl_by_trade" in eligible.columns:
        for _, row in eligible.iterrows():
            pnl = row.get("pnl_by_trade")
            if pnl and len(pnl) >= 10:
                pnl_arr = np.array(pnl, dtype=float)
                p_val, bs_p05 = block_bootstrap_pf(pnl_arr)
                bootstrap_results.append({
                    "run_id": row["run_id"],
                    "p_value": p_val,
                    "bs_p05": bs_p05,
                })
            else:
                bootstrap_results.append({"run_id": row["run_id"], "p_value": 1.0, "bs_p05": 0.0})

    holm_results = {}
    if bootstrap_results:
        p_values = [r["p_value"] for r in bootstrap_results]
        rejected = holm_bonferroni(p_values)
        for r, rej in zip(bootstrap_results, rejected):
            holm_results[r["run_id"]] = {**r, "holm_rejected": rej}

    winners = []
    for run_id, bs in holm_results.items():
        row = eligible[eligible["run_id"] == run_id].iloc[0]
        trades_buy = row.get("trades_buy", 0) or 0
        trades_sell = row.get("trades_sell", 0) or 0
        bs_p05 = bs["bs_p05"]

        gates = {
            "trades_total": int(row["trades_count"]) >= 100,
            "trades_per_side": trades_buy >= 30 and trades_sell >= 30,
            "unexplained_zero": True,
            "bs_p05_above_1": bs_p05 > 1.0,
            "holm_rejected": bs["holm_rejected"],
        }

        gp_by_year = row.get("gross_profit_by_year", {})
        profit_concentration_pass = True
        effective_profit_years = None
        if gp_by_year:
            total_gp = sum(gp_by_year.values())
            if total_gp > 0:
                shares = [gp / total_gp for gp in gp_by_year.values()]
                effective_profit_years = 1.0 / sum(s ** 2 for s in shares)
                profit_concentration_pass = effective_profit_years >= 1.5

        all_pass = all(gates.values()) and profit_concentration_pass
        winners.append({
            "run_id": run_id,
            "gates": gates,
            "profit_concentration_pass": profit_concentration_pass,
            "all_gates_pass": all_pass,
            "bs_p05": bs_p05,
            "trades_count": int(row["trades_count"]),
        })

    winners.sort(key=lambda w: (-w["bs_p05"], -w["trades_count"]))

    verdict = "BATCH_NO_WINNER"
    winner_id = None

    summary = {
        "status": "DIAGNOSTIC_ONLY",
        "verdict": verdict,
        "winner": winner_id,
        "n_candidates": len(candidates),
        "n_valid": int(len(valid)) if not valid.empty else 0,
        "n_eligible": int(len(eligible)) if not eligible.empty else 0,
        "n_diagnostic_only": int(len(diagnostic)) if not diagnostic.empty else 0,
        "winners_ranked": winners,
        "holm_bonferroni": holm_results,
        "validation_period": {"from": str(VAL_FROM.date()), "to": str(VAL_TO.date())},
        "multiple_testing": {
            "method": "Holm-Bonferroni",
            "alpha": 0.05,
            "n_tests": len(bootstrap_results),
        },
        "bootstrap_config": {"n_iter": 2000, "block_size": 15, "seed": 42},
        "table": rows,
    }

    summary_path = BATCH_DIR / "batch_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"\nVerdict: {verdict}" + (f" → {winner_id}" if winner_id else ""))
    print(f"Summary written to {summary_path}")
    return summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="MT5 batch selection pipeline")
    parser.add_argument("--phase", choices=["signals", "tester", "aggregate", "all"], default="all")
    args = parser.parse_args()

    candidates = load_candidates()
    print(f"Loaded {len(candidates)} candidates.")

    if args.phase in ("signals", "all"):
        eq_scores = load_eq_scores()
        print(f"EQ scores: {len(eq_scores)} rows in validation period.")
        generate_signals(candidates, eq_scores)

    if args.phase in ("tester", "all"):
        if not compile_expert():
            print("ABORT: compilation failed")
            sys.exit(1)
        if not check_liveupdate():
            print("ABORT: liveupdate files present")
            sys.exit(1)
        if not check_tester_file_property():
            print("ABORT: tester_file property missing")
            sys.exit(1)

        print("\n--- SMOKE TEST ---")
        if not run_smoke_test(candidates):
            print("ABORT: smoke test failed")
            sys.exit(1)
        print("Smoke test PASSED.\n")

        print("--- FULL BATCH ---")
        run_batch(candidates)

    if args.phase in ("aggregate", "all"):
        aggregate_batch(candidates)


if __name__ == "__main__":
    main()
