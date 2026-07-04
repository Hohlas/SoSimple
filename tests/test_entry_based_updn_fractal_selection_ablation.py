# =============================================================================
# Файл: test_entry_based_updn_fractal_selection_ablation.py
# Назначение: тесты runtime и feature contract для bounded runner-а абляции
#   отбора фракталов на `entry-based` target
# Язык: Python 3.10+
# Обновлён: 2026-07-03
# Зависимости:
#   Внутренние зависимости:
#     - ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py
# Использование:
#   ./.venv/bin/python -m pytest tests/test_entry_based_updn_fractal_selection_ablation.py -q
# =============================================================================

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import numpy as np
import pandas as pd

import ML.baseline.benchmark_entry_based_updn_fractal_selection_ablation as runner


def _fractal(
    *,
    time: int,
    price: float,
    direction: int = 1,
    front: float = 1.0,
    back: float = 2.0,
    strong: int = 0,
    brk: int = 0,
    reverse: float = 0.0,
    power: float = 1.0,
    count: int = 1,
    impulse: float = 0.5,
    up3: float = 0.1,
    dn3: float = 0.2,
    up6: float = 0.3,
    dn6: float = 0.4,
    up12: float = 0.5,
    dn12: float = 0.6,
    up24: float = 0.7,
    dn24: float = 0.8,
    up48: float = 0.9,
    dn48: float = 1.0,
    fractal_atr: float = 1.0,
    shift: float = 3.0,
) -> str:
    parts = [
        time,
        price,
        direction,
        front,
        back,
        strong,
        brk,
        reverse,
        power,
        count,
        impulse,
        up12,
        dn12,
        up24,
        dn24,
        up48,
        dn48,
        up3,
        dn3,
        up6,
        dn6,
        fractal_atr,
        shift,
    ]
    return ":".join(str(value) for value in parts)


def _frame(rows: int = 8, atr: float = 2.0, far_multiplier: float = 1.0) -> pd.DataFrame:
    data = []
    for idx in range(rows):
        base = 100.0 + idx
        data.append(
            {
                "time": f"2021.01.{idx + 1:02d} 00:00",
                "entry_time": f"2021.01.{idx + 1:02d} 01:00",
                "ATR": atr,
                "fractal0": _fractal(time=1000 - idx, price=base, direction=1),
                "fractal1": _fractal(time=999 - idx, price=base + 1.0 * far_multiplier, direction=-1),
                "fractal2": _fractal(time=998 - idx, price=base - 1.0 * far_multiplier, direction=1),
                "fractal3": _fractal(time=997 - idx, price=base + 5.0 * far_multiplier, direction=1),
                "fractal4": _fractal(time=996 - idx, price=base - 6.0 * far_multiplier, direction=-1),
                "entry_up_3": 1.0 + idx * 0.1,
                "entry_dn_3": 0.8 + idx * 0.1,
                "entry_up_6": 1.2 + idx * 0.1,
                "entry_dn_6": 0.7 + idx * 0.1,
                "entry_up_12": 1.4 + idx * 0.1,
                "entry_dn_12": 0.6 + idx * 0.1,
                "entry_log_ratio_3": 0.1 + idx * 0.01,
                "entry_log_ratio_6": 0.2 + idx * 0.01,
                "entry_log_ratio_12": 0.3 + idx * 0.01,
            }
        )
    return pd.DataFrame(data)


def _splits() -> dict[str, pd.DataFrame]:
    train = _frame(rows=8)
    val = _frame(rows=5)
    holdout = _frame(rows=4)
    low_n = _frame(rows=3)
    return {
        "train_core": train,
        "val_stop": val,
        "diagnostic_holdout": holdout,
        "low_n_disclosure": low_n,
    }


def test_representation_registry_is_frozen():
    registry = runner.build_representation_registry()
    assert list(registry) == [
        "all100",
        "nearest_k20",
        "nearest_k40",
        "nearest_k60",
        "nearest_k80",
        "corridor_5atr",
        "corridor_10atr",
        "corridor_15atr",
        "zones_atr",
        "zones_plus_nearest_k40",
    ]


def test_model_registry_is_frozen():
    registry = runner.build_model_registry()
    assert list(registry) == [
        "xgboost_depth3",
        "xgboost_depth5",
        "hist_gradient_boosting",
        "ridge",
    ]


def test_arg_parser_defaults_to_resume():
    parser = runner.build_arg_parser()
    args = parser.parse_args(["--entry-based-updn-fractal-selection-ablation"])
    assert args.entry_based_updn_fractal_selection_ablation is True
    assert args.resume is True


def test_target_contract_records_rebuilt_mode_and_fingerprint():
    result = runner.validate_entry_based_target_contract(_splits())
    assert result["status"] == "PASS"
    assert result["target_mode"] in {"rebuilt", "loaded_verified"}
    assert result["target_builder_fingerprint"]
    assert set(result["split_checks"]) == {
        "train_core",
        "val_stop",
        "diagnostic_holdout",
        "low_n_disclosure",
    }


def test_target_contract_rejects_target_columns_in_features():
    features = pd.DataFrame({"entry_up_3_bad": [1.0]})
    forbidden = runner.find_forbidden_feature_columns(list(features.columns))
    assert forbidden == ["entry_up_3_bad"]


def test_representation_builder_metadata_and_anchor_contract():
    features, metadata = runner.build_representation_features(_frame(rows=2), "nearest_k20")
    assert metadata["profile_key"] == "nearest_k20"
    assert metadata["selection_family"] == "nearest_k"
    assert metadata["anchor_contract"]["price"] == "fractal0.price"
    assert metadata["anchor_contract"]["atr"] == "row_ATR"
    assert metadata["feature_count"] == features.shape[1]
    assert metadata["feature_names"] == list(features.columns)


def test_all_representations_use_same_allowed_updn_horizons():
    forbidden_parts = ("_up_24", "_dn_24", "_up_48", "_dn_48")
    for profile_key in runner.REPRESENTATION_ORDER:
        features, metadata = runner.build_representation_features(_frame(rows=2), profile_key)
        forbidden = [column for column in features.columns if any(part in column for part in forbidden_parts)]
        assert forbidden == []
        assert metadata["updn_horizons"] == ["3", "6", "12"]


def test_corridor_preflight_reports_coverage_and_bounds():
    _, metadata = runner.build_representation_features(_frame(rows=3), "corridor_5atr")
    coverage = metadata["coverage_summary"]
    assert "selected_count_distribution" in coverage
    assert "share_rows_0" in coverage
    assert "min_price_coord_atr" in coverage
    assert "max_price_coord_atr" in coverage
    preflight = runner.run_representation_preflight(_frame(rows=3), "corridor_5atr")
    assert preflight["status"] in {"PASS", "WARNING"}


def test_distribution_audit_reports_stats_and_flags():
    train = _frame(rows=5)
    other = _frame(rows=5)
    other.loc[0, "ATR"] = np.nan
    audit = runner.audit_feature_distribution(train, other, "nearest_k20")
    assert "feature_stats" in audit
    first_stats = next(iter(audit["feature_stats"].values()))
    for key in ("missing_pct", "zero_pct", "p1", "p5", "p50", "p95", "p99", "frac_abs_gt3", "frac_abs_gt10"):
        assert key in first_stats
    assert "flags" in audit


def test_thread_config_and_fit_predict_schema():
    cfg = runner.thread_config_for("xgboost_depth3")
    assert cfg["thread_count"] == 24
    train = _frame(rows=8)
    val = _frame(rows=4)
    result = runner.fit_and_predict(
        model_key="ridge",
        seed=42,
        thread_count=1,
        train_features=runner.build_representation_features(train, "all100")[0],
        train_targets=runner.target_matrix(train),
        eval_frames={"val_stop": val},
        eval_features={"val_stop": runner.build_representation_features(val, "all100")[0]},
    )
    assert "predictions_by_split" in result
    preds = result["predictions_by_split"]["val_stop"]
    for key in (
        "pred_entry_up_3",
        "pred_entry_dn_3",
        "pred_entry_up_6",
        "pred_entry_dn_6",
        "pred_entry_up_12",
        "pred_entry_dn_12",
        "pred_entry_log_ratio_3",
        "pred_entry_log_ratio_6",
        "pred_entry_log_ratio_12",
    ):
        assert key in preds.columns


def test_resume_skips_completed_jobs_and_writes_artifacts(tmp_path: Path, monkeypatch):
    splits = _splits()
    monkeypatch.setattr(runner, "load_entry_based_splits", lambda target_mode="rebuilt": splits)
    monkeypatch.setattr(runner, "run_distribution_audit", lambda splits, profile_keys: {"status": "PASS", "profiles": {}})
    monkeypatch.setattr(runner, "run_data_contract_smoke_check", lambda: {"status": "PASS"})
    monkeypatch.setattr(
        runner,
        "enumerate_jobs",
        lambda representation_keys=None, model_keys=None, seeds=None: [
            {"representation_key": "all100", "model_key": "ridge", "seed": 42},
            {"representation_key": "nearest_k20", "model_key": "ridge", "seed": 42},
        ],
    )

    calls: list[tuple[str, str, int]] = []

    def fake_eval(job, splits, report):
        calls.append((job["representation_key"], job["model_key"], job["seed"]))
        return {
            "job_key": runner.job_key(job),
            "representation_key": job["representation_key"],
            "model_key": job["model_key"],
            "seed": job["seed"],
            "elapsed_sec": 0.1,
            "split_metrics": {
                "val_stop": {
                    "entry_log_ratio_3": {"spearman": 0.0},
                    "entry_up_3": {"spearman": 0.0},
                    "entry_dn_3": {"spearman": 0.0},
                }
            },
            "rows_preview": pd.DataFrame(
                [{"representation_key": job["representation_key"], "model_key": job["model_key"], "seed": job["seed"], "split_name": "val_stop"}]
            ),
            "metrics_rows": [
                {
                    "representation_key": job["representation_key"],
                    "model_key": job["model_key"],
                    "seed": job["seed"],
                    "split_name": "val_stop",
                    "target_name": "entry_log_ratio",
                    "horizon": "H3",
                    "spearman": 0.0,
                    "elapsed_sec": 0.1,
                }
            ],
        }

    monkeypatch.setattr(runner, "evaluate_job", fake_eval)

    args = Namespace(entry_based_updn_fractal_selection_ablation=True, resume=True)
    report_path = tmp_path / "report.json"
    metrics_path = tmp_path / "metrics.csv"
    rows_path = tmp_path / "rows.csv"
    runner.run_benchmark(args, report_path=report_path, metrics_path=metrics_path, rows_path=rows_path)
    runner.run_benchmark(args, report_path=report_path, metrics_path=metrics_path, rows_path=rows_path)

    assert calls == [("all100", "ridge", 42), ("nearest_k20", "ridge", 42)]
    assert report_path.exists()
    assert metrics_path.exists()
    assert rows_path.exists()
    assert ";" in metrics_path.read_text(encoding="utf-8")


def test_summary_verdict_rules():
    report = {
        "runs": [
            {
                "representation_key": "all100",
                "model_key": "ridge",
                "seed": 42,
                "coverage_penalty": False,
                "split_metrics": {
                    "val_stop": {"entry_log_ratio_3": {"spearman": 0.05}, "entry_up_3": {"spearman": 0.20}, "entry_dn_3": {"spearman": 0.20}},
                    "diagnostic_holdout": {"entry_log_ratio_3": {"spearman": 0.02}, "entry_up_3": {"spearman": 0.10}, "entry_dn_3": {"spearman": 0.10}},
                },
            },
            {
                "representation_key": "nearest_k20",
                "model_key": "ridge",
                "seed": 42,
                "coverage_penalty": False,
                "split_metrics": {
                    "val_stop": {"entry_log_ratio_3": {"spearman": 0.08}, "entry_up_3": {"spearman": 0.19}, "entry_dn_3": {"spearman": 0.19}},
                    "diagnostic_holdout": {"entry_log_ratio_3": {"spearman": -0.01}, "entry_up_3": {"spearman": -0.01}, "entry_dn_3": {"spearman": -0.01}},
                },
            },
        ]
    }
    summary = runner.summarize_results(report)
    assert summary["status"] == "NO_SIGNAL_FOUND"

    report["runs"].append(
        {
            "representation_key": "nearest_k20",
            "model_key": "xgboost_depth3",
            "seed": 42,
            "coverage_penalty": False,
            "split_metrics": {
                    "val_stop": {"entry_log_ratio_3": {"spearman": 0.08}, "entry_up_3": {"spearman": 0.32}, "entry_dn_3": {"spearman": 0.30}},
                    "diagnostic_holdout": {"entry_log_ratio_3": {"spearman": 0.03}, "entry_up_3": {"spearman": 0.15}, "entry_dn_3": {"spearman": 0.14}},
            },
        }
    )
    summary = runner.summarize_results(report)
    assert summary["status"] == "NO_SIGNAL_FOUND"

    report["runs"].append(
        {
            "representation_key": "nearest_k20",
            "model_key": "xgboost_depth5",
            "seed": 42,
            "coverage_penalty": False,
            "split_metrics": {
                    "val_stop": {"entry_log_ratio_3": {"spearman": 0.09}, "entry_up_3": {"spearman": 0.29}, "entry_dn_3": {"spearman": 0.28}},
                "diagnostic_holdout": {"entry_log_ratio_3": {"spearman": 0.04}, "entry_up_3": {"spearman": 0.12}, "entry_dn_3": {"spearman": 0.12}},
            },
        }
    )
    summary = runner.summarize_results(report)
    assert summary["status"] == "WEAK_TRACE_FOUND"


def test_summary_uses_all_horizons_for_best_and_verdict():
    report = {
        "runs": [
            {
                "representation_key": "all100",
                "model_key": "ridge",
                "seed": 42,
                "coverage_penalty": False,
                "split_metrics": {
                    "val_stop": {
                        "entry_log_ratio_3": {"spearman": 0.02},
                        "entry_log_ratio_6": {"spearman": 0.03},
                        "entry_log_ratio_12": {"spearman": 0.04},
                        "entry_up_12": {"spearman": 0.10},
                        "entry_dn_12": {"spearman": 0.10},
                    },
                    "diagnostic_holdout": {
                        "entry_log_ratio_3": {"spearman": -0.01},
                        "entry_log_ratio_6": {"spearman": -0.01},
                        "entry_log_ratio_12": {"spearman": -0.01},
                    },
                },
            },
            {
                "representation_key": "nearest_k20",
                "model_key": "ridge",
                "seed": 42,
                "coverage_penalty": False,
                "split_metrics": {
                    "val_stop": {
                        "entry_log_ratio_3": {"spearman": 0.01},
                        "entry_log_ratio_6": {"spearman": 0.02},
                        "entry_log_ratio_12": {"spearman": 0.08},
                        "entry_up_12": {"spearman": 0.30},
                        "entry_dn_12": {"spearman": 0.22},
                    },
                    "diagnostic_holdout": {
                        "entry_log_ratio_3": {"spearman": -0.01},
                        "entry_log_ratio_6": {"spearman": -0.01},
                        "entry_log_ratio_12": {"spearman": 0.01},
                    },
                },
            },
        ]
    }
    summary = runner.summarize_results(report)
    best = summary["best_by_model"]["ridge"]["best_val_stop"]
    assert best["representation_key"] == "nearest_k20"
    assert best["target_name"] == "entry_log_ratio"
    assert best["horizon"] == "H12"
    assert best["score"] == 0.08
    assert summary["status"] == "NO_SIGNAL_FOUND"


def test_smoke_check_disclosure_preserves_legacy_failure():
    disclosure = runner.build_smoke_check_disclosure(
        {"status": "FAIL", "returncode": 1},
        {"status": "PASS"},
    )
    assert disclosure["legacy_smoke_check_status"] == "FAIL"
    assert disclosure["entry_based_target_contract_status"] == "PASS"
    assert disclosure["interpretation"] == "LEGACY_SMOKE_FAIL_STAGE_CONTRACT_PASS"


def test_load_or_init_report_roundtrip(tmp_path: Path):
    path = tmp_path / "report.json"
    report = runner.load_or_init_report(path, resume=False)
    assert report["runs"] == []
    path.write_text(json.dumps({"runs": [{"job_key": "x"}]}), encoding="utf-8")
    loaded = runner.load_or_init_report(path, resume=True)
    assert loaded["runs"] == [{"job_key": "x"}]
