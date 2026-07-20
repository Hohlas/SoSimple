import ML.baseline.benchmark_entry_based_updn_price_feature_matrix as runner
import pandas as pd
import numpy as np


def _fractal(
    *,
    price: float,
    direction: int,
    up3: float = 0.0,
    dn3: float = 0.0,
    up6: float = 0.0,
    dn6: float = 0.0,
    up12: float = 0.0,
    dn12: float = 0.0,
    atr: float = 1.0,
    shift: int = 0,
) -> str:
    fields = [
        "1700000000",
        str(price),
        str(direction),
        "2.0",
        "3.0",
        "1",
        "0",
        "0.5",
        "2.0",
        "1",
        "0.5",
        str(up12),
        str(dn12),
        "0.0",
        "0.0",
        "0.0",
        "0.0",
        str(up3),
        str(dn3),
        str(up6),
        str(dn6),
        str(atr),
        str(shift),
    ]
    return ":".join(fields)


def _sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ATR": [2.0],
            "fractal0": [_fractal(price=100.0, direction=1, up3=1.0, dn3=0.5, up6=2.0, dn6=1.0, up12=3.0, dn12=1.5)],
            "fractal1": [_fractal(price=104.0, direction=-1, up3=1.5, dn3=2.5, up6=2.0, dn6=3.0, up12=2.5, dn12=4.5)],
            "fractal2": [_fractal(price=96.0, direction=1, up3=0.5, dn3=0.25, up6=1.0, dn6=0.75, up12=2.0, dn12=1.25)],
            "time": ["2021.01.05 10:00"],
        }
    )


def test_profile_registry_is_frozen():
    registry = runner.build_profile_registry()

    assert list(registry) == [
        "structure_full",
        "structure_full_relative_price",
        "structure_full_distance_atr",
        "structure_full_price_coord_atr",
        "structure_full_short_updn_source_audited",
        "structure_full_path_reaction",
        "structure_full_price_atr_scaled",
    ]
    assert runner.PRIMARY_PROFILE_KEYS == [
        "structure_full_relative_price",
        "structure_full_price_coord_atr",
        "structure_full_path_reaction",
    ]
    assert runner.DIAGNOSTIC_PROFILE_KEYS == ["structure_full_price_atr_scaled"]


def test_arg_parser_defaults_to_resume():
    parser = runner.build_arg_parser()
    args = parser.parse_args(["--entry-based-updn-price-feature-matrix"])

    assert args.entry_based_updn_price_feature_matrix is True
    assert args.resume is True


def test_relative_price_block_adds_deterministic_columns_without_targets():
    block = runner.build_relative_price_block(_sample_frame())

    assert list(block.columns) == [
        "rel_price_atr_fractal0",
        "rel_price_atr_fractal1",
        "rel_price_atr_fractal2",
    ]
    assert block.loc[0, "rel_price_atr_fractal0"] == 0.0
    assert block.loc[0, "rel_price_atr_fractal1"] == 2.0
    assert block.loc[0, "rel_price_atr_fractal2"] == -2.0
    assert not any("entry_" in name or name.startswith("up_") or name.startswith("dn_") for name in block.columns)


def test_distance_atr_block_exposes_signed_and_absolute_distance_columns():
    block = runner.build_distance_atr_block(_sample_frame())

    assert "distance_atr_signed_fractal1" in block.columns
    assert "distance_atr_abs_fractal1" in block.columns
    assert block.loc[0, "distance_atr_signed_fractal1"] == 2.0
    assert block.loc[0, "distance_atr_abs_fractal2"] == 2.0


def test_audit_updn_feature_source_rejects_top_level_updn_usage():
    frame = _sample_frame().assign(up_3=[9.0], dn_3=[8.0])

    audit = runner.audit_updn_feature_source(frame, used_top_level_columns=["up_3", "dn_3"])

    assert audit["status"] == "fail"
    assert "up_3" in audit["forbidden_top_level_columns"]
    assert audit["uses_only_fractal_fields"] is False


def test_short_updn_source_audited_uses_only_3_6_12_and_reports_metadata():
    frame = _sample_frame()
    audit = runner.audit_updn_feature_source(frame)

    block = runner.build_short_updn_source_audited_block(frame, audit)
    _, metadata = runner.build_profile_features(frame, "structure_full_short_updn_source_audited")

    assert any(name.startswith("short_updn_fav_3_") for name in block.columns)
    assert any(name.startswith("short_updn_adv_6_") for name in block.columns)
    assert not any("_24_" in name or "_48_" in name for name in block.columns)
    assert metadata["updn_source_audit"]["status"] == "pass"
    assert metadata["transform"]["horizons"] == [3, 6, 12]


def test_path_reaction_block_uses_pic_path_prefix():
    block = runner.build_path_reaction_block(_sample_frame())

    assert block.columns.tolist()
    assert all(name.startswith("pic_path_") for name in block.columns)


def test_build_profile_features_reports_feature_metadata():
    features, metadata = runner.build_profile_features(_sample_frame(), "structure_full_relative_price")

    assert metadata["profile_key"] == "structure_full_relative_price"
    assert metadata["feature_names"] == list(features.columns)
    assert metadata["feature_count"] == features.shape[1]
    assert metadata["added_blocks"] == ["relative_price"]
    assert "block_hypothesis" in metadata


def test_load_entry_based_splits_reuses_foundation_contract(monkeypatch):
    split_calls = {"load": 0, "rebuild": 0}
    source = {"train_core": _sample_frame()}

    def fake_load():
        split_calls["load"] += 1
        return source

    def fake_ohlc():
        return pd.DataFrame({"time": [], "open": [], "high": [], "low": [], "parsed_time": []})

    def fake_rebuild(df, ohlc, horizons):
        split_calls["rebuild"] += 1
        assert horizons == (3, 6, 12)
        return df.assign(entry_up_3=1.0, entry_dn_3=0.5, entry_up_6=1.5, entry_dn_6=0.7, entry_up_12=2.0, entry_dn_12=1.0)

    monkeypatch.setattr(runner.entry_foundation, "load_research_splits", fake_load)
    monkeypatch.setattr(runner.entry_foundation, "load_ohlc", fake_ohlc)
    monkeypatch.setattr(runner.entry_foundation, "rebuild_entry_targets", fake_rebuild)

    splits = runner.load_entry_based_splits()

    assert split_calls == {"load": 1, "rebuild": 1}
    assert "entry_up_3" in splits["train_core"].columns


def test_profile_matrix_excludes_forbidden_target_columns():
    frame = _sample_frame().assign(entry_up_3=[1.0], entry_dn_3=[0.5])
    matrix, metadata = runner.profile_matrix(frame, "structure_full_relative_price")

    assert matrix.shape[1] == metadata["feature_count"]
    assert "entry_up_3" not in metadata["feature_names"]
    assert "entry_dn_3" not in metadata["feature_names"]


def test_profile_matrix_feature_count_matches_width():
    matrix, metadata = runner.profile_matrix(_sample_frame(), "structure_full_relative_price")

    assert isinstance(matrix, np.ndarray)
    assert metadata["feature_count"] == matrix.shape[1]
    assert metadata["feature_names_sha256"]


def test_completed_run_keys_and_resume_helpers_roundtrip(tmp_path):
    report = {
        "runs": [
            {"profile_key": "structure_full", "seed": 42},
            {"profile_key": "structure_full_relative_price", "seed": 77},
        ]
    }
    path = tmp_path / "report.json"

    runner.write_report_atomic(report, path)
    loaded = runner.load_existing_report(path)

    assert loaded == report
    assert runner.completed_run_keys(loaded) == {
        ("structure_full", 42),
        ("structure_full_relative_price", 77),
    }


def test_make_model_params_passes_thread_count():
    params = runner.make_xgb_model_params(seed=42, xgb_threads=24)

    assert params["random_state"] == 42
    assert params["n_jobs"] == 24
    assert params["max_depth"] == 3


def test_heartbeat_prints_stage_and_progress(capsys):
    runner.heartbeat("run_start", done_runs=1, total_runs=7)

    captured = capsys.readouterr()

    assert "run_start" in captured.out
    assert "1/7" in captured.out


def test_run_preflight_includes_progress_and_smoke_check(monkeypatch):
    monkeypatch.setattr(
        runner,
        "_run_data_contract_smoke_check",
        lambda: {"status": "PASS", "command": "smoke"},
    )

    report = runner.run_preflight({"train_core": _sample_frame()})

    assert report["data_contract_smoke_check"]["status"] == "PASS"
    assert report["progress"]["done_runs"] == 0
    assert report["progress"]["total_runs"] == len(runner.PROFILE_KEYS) * len(runner.CONFIG.seeds)
    assert "started_at" in report
    assert report["elapsed_sec"] >= 0.0


def test_entry_based_target_contract_check_passes_on_entry_targets():
    splits = {"train_core": _split_frame_with_targets(), "val_stop": _split_frame_with_targets()}

    check = runner.run_entry_based_target_contract_check(splits)

    assert check["status"] == "PASS"
    assert check["target_columns"] == list(runner.TARGET_COLUMNS)
    assert check["split_checks"]["train_core"]["rows"] == 4
    assert check["split_checks"]["val_stop"]["entry_log_ratio"]["H3"]["finite"] is True
    assert check["forbidden_feature_prefixes"] == list(runner.FORBIDDEN_TOP_LEVEL_TARGET_PREFIXES)


def test_entry_based_target_contract_check_fails_on_missing_target():
    broken = _split_frame_with_targets().drop(columns=["entry_dn_12"])

    check = runner.run_entry_based_target_contract_check({"train_core": broken})

    assert check["status"] == "FAIL"
    assert "entry_dn_12" in check["split_checks"]["train_core"]["missing_target_columns"]


def test_run_preflight_includes_entry_based_target_contract(monkeypatch):
    monkeypatch.setattr(
        runner,
        "_run_data_contract_smoke_check",
        lambda: {"status": "FAIL", "command": "legacy smoke"},
    )

    report = runner.run_preflight({"train_core": _split_frame_with_targets()})

    assert report["data_contract_smoke_check"]["status"] == "FAIL"
    assert report["entry_based_target_contract_check"]["status"] == "PASS"


def _split_frame_with_targets() -> pd.DataFrame:
    frame = pd.concat([_sample_frame()] * 4, ignore_index=True)
    frame["entry_up_3"] = [1.0, 2.0, 3.0, 4.0]
    frame["entry_dn_3"] = [0.5, 1.0, 1.5, 2.0]
    frame["entry_up_6"] = [1.5, 2.5, 3.5, 4.5]
    frame["entry_dn_6"] = [0.4, 0.9, 1.4, 1.9]
    frame["entry_up_12"] = [2.0, 3.0, 4.0, 5.0]
    frame["entry_dn_12"] = [0.3, 0.8, 1.3, 1.8]
    return frame


def test_evaluate_profile_seed_writes_entry_metrics_for_all_horizons():
    splits = {
        "train_core": _split_frame_with_targets(),
        "val_stop": _split_frame_with_targets(),
        "diagnostic_holdout": _split_frame_with_targets(),
        "low_n_disclosure": _split_frame_with_targets(),
    }

    result = runner.evaluate_profile_seed("structure_full", 42, splits)

    assert result["profile_key"] == "structure_full"
    assert result["seed"] == 42
    assert "entry_log_ratio" in result["val_stop_metrics"]
    assert "H3" in result["val_stop_metrics"]["entry_log_ratio"]
    assert "entry_up" in result["diagnostic_holdout_metrics"]
    assert "entry_dn" in result["low_n_disclosure_metrics"]


def test_summarize_profiles_can_return_weak_trace_found():
    report = {
        "runs": [
            {
                "profile_key": "structure_full",
                "profile_role": "baseline",
                "seed": 42,
                "val_stop_metrics": {"entry_log_ratio": {"H3": {"spearman": 0.01}, "H6": {"spearman": 0.01}, "H12": {"spearman": 0.01}}},
                "diagnostic_holdout_metrics": {"entry_log_ratio": {"H3": {"spearman": 0.0}, "H6": {"spearman": 0.0}, "H12": {"spearman": 0.0}}},
                "low_n_disclosure_metrics": {"entry_log_ratio": {"H3": {"spearman": 0.0}, "H6": {"spearman": 0.0}, "H12": {"spearman": 0.0}}},
                "val_stop_entry_side_trace": 0.05,
            },
            {
                "profile_key": "structure_full_relative_price",
                "profile_role": "primary",
                "seed": 42,
                "val_stop_metrics": {
                    "entry_log_ratio": {"H3": {"spearman": 0.02}, "H6": {"spearman": 0.02}, "H12": {"spearman": 0.02}},
                    "entry_up": {"H3": {"spearman": 0.17}, "H6": {"spearman": 0.16}, "H12": {"spearman": 0.14}},
                    "entry_dn": {"H3": {"spearman": 0.15}, "H6": {"spearman": 0.12}, "H12": {"spearman": 0.11}},
                },
                "diagnostic_holdout_metrics": {"entry_log_ratio": {"H3": {"spearman": 0.01}, "H6": {"spearman": 0.01}, "H12": {"spearman": 0.01}}},
                "low_n_disclosure_metrics": {"entry_log_ratio": {"H3": {"spearman": 0.0}, "H6": {"spearman": 0.0}, "H12": {"spearman": 0.0}}},
                "val_stop_entry_side_trace": 0.17,
            },
        ]
    }

    summary = runner.summarize_profiles(report)

    assert summary["runner_status"] == "WEAK_TRACE_FOUND"
    assert summary["profile_roles"]["structure_full_relative_price"] == "primary"


def test_run_entry_based_matrix_creates_one_run_per_profile_seed(monkeypatch, tmp_path):
    splits = {"train_core": _split_frame_with_targets()}

    monkeypatch.setattr(runner, "load_entry_based_splits", lambda: splits)
    monkeypatch.setattr(
        runner,
        "run_preflight",
        lambda split_frames: {
            "started_at": "2026-07-02T00:00:00+00:00",
            "artifact_status": "DIAGNOSTIC_ONLY",
            "runs": [],
            "progress": {"done_runs": 0, "total_runs": len(runner.PROFILE_KEYS) * len(runner.CONFIG.seeds), "elapsed_sec": 0.0},
        },
    )
    monkeypatch.setattr(
        runner,
        "evaluate_profile_seed",
        lambda profile_key, seed, split_frames: {
            "profile_key": profile_key,
            "profile_role": runner.build_profile_registry()[profile_key]["role"],
            "seed": seed,
            "elapsed_sec": 0.01,
            "val_stop_metrics": {"entry_log_ratio": {"H3": {"spearman": 0.0}, "H6": {"spearman": 0.0}, "H12": {"spearman": 0.0}}},
            "diagnostic_holdout_metrics": {"entry_log_ratio": {"H3": {"spearman": 0.0}, "H6": {"spearman": 0.0}, "H12": {"spearman": 0.0}}},
            "low_n_disclosure_metrics": {"entry_log_ratio": {"H3": {"spearman": 0.0}, "H6": {"spearman": 0.0}, "H12": {"spearman": 0.0}}},
            "rows_csv_preview": [{"split_name": "train_core", "entry_up_3": 1.0}],
        },
    )

    report = runner.run_entry_based_updn_price_feature_matrix(
        resume=False,
        report_path=tmp_path / "report.json",
        rows_path=tmp_path / "rows.csv",
    )

    assert len(report["runs"]) == len(runner.PROFILE_KEYS) * len(runner.CONFIG.seeds)
    assert report["progress"]["done_runs"] == report["progress"]["total_runs"]
    assert (tmp_path / "rows.csv").exists()
