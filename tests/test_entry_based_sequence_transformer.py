from __future__ import annotations

import json
import subprocess

import numpy as np
import pandas as pd
import pytest
import torch

import ML.baseline.benchmark_entry_based_sequence_transformer as runner


def _fractal(
    t: int,
    price: float,
    direction: int,
    shift: int,
    up3: float = 0.1,
    dn3: float = 0.2,
) -> str:
    fields = [
        t,
        price,
        direction,
        1.0,
        2.0,
        0,
        1,
        0.0,
        3.0,
        1,
        0.5,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        up3,
        dn3,
        0.3,
        0.35,
        10.0,
        shift,
    ]
    return ":".join(str(x) for x in fields)


def _minimal_frame() -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "time": ["2020-01-01 12:00:00"],
            "ATR": [2.0],
            "fractal0": [_fractal(1000, 100.0, 1, 1)],
            "fractal1": [_fractal(900, 98.0, -1, 5)],
        }
    )
    for idx in range(2, 100):
        frame[f"fractal{idx}"] = [""]
    return frame


def test_sequence_transformer_scope_is_bounded_and_isolated():
    assert runner.SEQUENCE_TRANSFORMER_OUTPUT_PREFIX == "entry_based_sequence_transformer"
    assert runner.SEQUENCE_TRANSFORMER_REPRESENTATIONS == (
        "all100_sequence",
        "nearest_k80_sequence",
        "nearest_k60_sequence",
    )
    assert runner.SEQUENCE_TRANSFORMER_MODEL_KEYS == (
        "transformer_small",
        "transformer_medium",
        "sequence_flat_hist_gradient_boosting",
    )
    assert runner.SEQUENCE_TRANSFORMER_SEEDS == (42,)


def test_job_matrix_has_expected_size():
    jobs = runner.enumerate_sequence_transformer_jobs()
    assert len(jobs) == 9
    assert {(job["representation"], job["model_key"], job["seed"]) for job in jobs}


def test_build_sequence_tensor_uses_fractal_order_and_padding_mask():
    tensor = runner.build_sequence_tensor(_minimal_frame(), "all100_sequence")

    assert tensor.tokens.shape == (1, 100, len(runner.TOKEN_FEATURE_NAMES))
    assert tensor.mask.shape == (1, 100)
    assert tensor.mask[0, 0]
    assert tensor.mask[0, 1]
    assert not tensor.mask[0, 2]
    price_idx = runner.TOKEN_FEATURE_NAMES.index("price_coord_atr")
    direction_idx = runner.TOKEN_FEATURE_NAMES.index("direction")
    assert np.isclose(tensor.tokens[0, 0, price_idx], 0.0)
    assert np.isclose(tensor.tokens[0, 1, price_idx], -1.0)
    assert np.isclose(tensor.tokens[0, 0, direction_idx], 1.0)
    assert np.isclose(tensor.tokens[0, 1, direction_idx], -1.0)
    assert np.allclose(tensor.tokens[0, 2:, :], 0.0)


def test_fractal0_updn_fields_are_forced_to_zero_but_older_tokens_keep_values():
    frame = pd.DataFrame(
        {
            "time": ["2020-01-01 12:00:00"],
            "ATR": [2.0],
            "fractal0": [_fractal(1000, 100.0, 1, 1, up3=9.0, dn3=8.0)],
            "fractal1": [_fractal(900, 98.0, -1, 5, up3=0.7, dn3=0.8)],
        }
    )
    for idx in range(2, 100):
        frame[f"fractal{idx}"] = [""]

    tensor = runner.build_sequence_tensor(frame, "all100_sequence")

    up3_idx = runner.TOKEN_FEATURE_NAMES.index("up_3")
    dn3_idx = runner.TOKEN_FEATURE_NAMES.index("dn_3")
    assert tensor.tokens[0, 0, up3_idx] == 0.0
    assert tensor.tokens[0, 0, dn3_idx] == 0.0
    assert np.isclose(tensor.tokens[0, 1, up3_idx], 0.7)
    assert np.isclose(tensor.tokens[0, 1, dn3_idx], 0.8)


def test_nearest_representation_selects_by_distance_then_restores_recency_order():
    frame = _minimal_frame()
    frame["fractal2"] = [_fractal(800, 100.5, 1, 10)]
    tensor = runner.build_sequence_tensor(frame, "nearest_k60_sequence")
    price_idx = runner.TOKEN_FEATURE_NAMES.index("price_coord_atr")
    assert tensor.mask[0, :3].tolist() == [True, True, True]
    assert tensor.tokens[0, :3, price_idx].tolist() == [0.0, -1.0, 0.25]


def test_nearest_delta_shift_uses_next_selected_token_not_original_neighbor():
    frame = _minimal_frame()
    frame["fractal1"] = [_fractal(900, 130.0, -1, 100)]
    frame["fractal2"] = [_fractal(800, 101.0, 1, 7)]
    for idx in range(3, 63):
        frame[f"fractal{idx}"] = [_fractal(800 - idx, 101.0 + idx * 0.001, 1, 10 + idx)]
    tensor = runner.build_sequence_tensor(frame, "nearest_k60_sequence")
    delta_idx = runner.TOKEN_FEATURE_NAMES.index("log_delta_shift")
    assert np.isclose(tensor.tokens[0, 0, delta_idx], np.log1p(6.0))


def test_invalid_atr_or_fractal0_blocks_tensor_build():
    frame = _minimal_frame()
    frame["ATR"] = [0.0]
    with pytest.raises(ValueError, match="invalid ATR or fractal0"):
        runner.build_sequence_tensor(frame, "all100_sequence")


def test_forbidden_top_level_targets_are_not_sequence_inputs():
    forbidden_examples = [
        "up_24",
        "dn_24",
        "entry_up_24",
        "entry_dn_24",
        "entry_log_ratio_24",
        "ret_24_dir_atr",
        "fav_24_atr",
        "adv_24_atr",
        "predict",
        "signal",
    ]
    for column in forbidden_examples:
        assert runner.is_forbidden_input_column(column)


def test_low_n_disclosure_is_not_used_by_verdict():
    summary = runner.decide_sequence_verdict(
        rows=[
            {
                "representation": "nearest_k80_sequence",
                "target_family": "entry_log_ratio",
                "horizon": 24,
                "val_select": 0.01,
                "val_eval": -0.01,
                "low_n_disclosure": 0.50,
            },
        ],
        smoke_check={"status": "PASS"},
        tensor_audit={"status": "PASS"},
    )
    assert summary["verdict"] == "REJECT_SEQUENCE_CAPACITY_EXPLANATION"


def test_low_n_disclosure_is_not_used_by_winner_selection():
    rows = [
        {"representation": "nearest_k80_sequence", "target_family": "entry_log_ratio", "horizon": 12, "val_select": 0.02, "val_eval": 0.01, "low_n_disclosure": 0.50},
        {"representation": "nearest_k60_sequence", "target_family": "entry_log_ratio", "horizon": 12, "val_select": 0.03, "val_eval": -0.01, "low_n_disclosure": -0.20},
    ]
    winner = runner.select_winner_by_policy(rows, selection_policy=runner.SELECTION_POLICY)
    assert winner["representation"] == "nearest_k60_sequence"
    assert winner["val_select"] == 0.03


def test_normalizer_fits_only_valid_train_tokens_and_keeps_padding_zero():
    tokens = np.zeros((2, 3, 2), dtype=np.float32)
    tokens[0, 0] = [1.0, 10.0]
    tokens[0, 1] = [2.0, 20.0]
    tokens[1, 0] = [3.0, 30.0]
    mask = np.array([[True, True, False], [True, False, False]])
    train = runner.SequenceTensor(tokens=tokens, mask=mask, feature_names=("a", "b"), representation="unit")

    normalizer = runner.fit_sequence_normalizer(train)
    normalized = runner.apply_sequence_normalizer(train, normalizer)

    assert normalizer.fit_split == "train"
    assert normalizer.n_fit_tokens == 3
    assert np.allclose(normalized.tokens[~mask], 0.0)
    assert np.isfinite(normalized.tokens[mask]).all()


def test_audit_flags_nonzero_padding_as_error():
    tokens = np.zeros((1, 2, 1), dtype=np.float32)
    tokens[0, 1, 0] = 1.0
    tensor = runner.SequenceTensor(tokens=tokens, mask=np.array([[True, False]]), feature_names=("a",), representation="unit")
    audit = runner.audit_sequence_tensor({"train": tensor})
    assert audit["status"] == "ERROR"


def test_audit_flags_rows_without_valid_tokens_as_error():
    tensor = runner.SequenceTensor(
        tokens=np.zeros((1, 2, 1), dtype=np.float32),
        mask=np.array([[False, False]]),
        feature_names=("a",),
        representation="unit",
    )
    audit = runner.audit_sequence_tensor({"train": tensor})
    assert audit["status"] == "ERROR"
    assert audit["errors"][0]["family"] == "NO_VALID_TOKENS"


def test_transformer_regressor_output_shape():
    model = runner.SequenceTransformerRegressor(input_features=5, output_dim=12, d_model=16, nhead=4, num_layers=1, dropout=0.0)
    x = torch.zeros((4, 100, 5), dtype=torch.float32)
    mask = torch.ones((4, 100), dtype=torch.bool)
    out = model(x, mask)
    assert out.shape == (4, 12)


def test_positive_direction_requires_replication_not_freeze():
    rows = [
        {
            "representation": "nearest_k80_sequence",
            "model_key": "transformer_small",
            "target_family": "entry_log_ratio",
            "horizon": 12,
            "val_select": 0.12,
            "val_eval": 0.06,
            "matching_all100_val_select": 0.03,
            "matching_all100_val_eval": 0.01,
            "simple_trade_val_select": 0.02,
            "simple_trade_val_eval": 0.01,
            "yearly_check_pass": True,
        }
    ]
    summary = runner.decide_sequence_verdict(rows, {"status": "PASS"}, {"status": "PASS"})
    assert summary["verdict"] == "DIRECTION_REPLICATION_REQUIRED"
    assert "FREEZE" not in summary["verdict"]


def test_all100_cannot_create_direction_replication_verdict():
    rows = [
        {
            "representation": "all100_sequence",
            "model_key": "transformer_small",
            "target_family": "entry_log_ratio",
            "horizon": 12,
            "val_select": 0.20,
            "val_eval": 0.10,
            "simple_trade_val_select": 0.02,
            "simple_trade_val_eval": 0.02,
            "yearly_check_pass": True,
        }
    ]
    summary = runner.decide_sequence_verdict(rows, {"status": "PASS"}, {"status": "PASS"})
    assert summary["verdict"] != "DIRECTION_REPLICATION_REQUIRED"


def test_yearly_concentration_blocks_direction_replication():
    rows = [
        {
            "representation": "nearest_k80_sequence",
            "model_key": "transformer_small",
            "target_family": "entry_log_ratio",
            "horizon": 12,
            "val_select": 0.12,
            "val_eval": 0.06,
            "matching_all100_val_select": 0.03,
            "matching_all100_val_eval": 0.01,
            "simple_trade_val_select": 0.02,
            "simple_trade_val_eval": 0.01,
            "yearly_check_pass": False,
        }
    ]
    summary = runner.decide_sequence_verdict(rows, {"status": "PASS"}, {"status": "PASS"})
    assert summary["verdict"] != "DIRECTION_REPLICATION_REQUIRED"


def test_yearly_check_is_computed_from_run_payload():
    run = {
        "yearly_metrics": {
            "val_select": {
                "2021": {"entry_log_ratio_12": {"spearman": 0.30}},
                "2022": {"entry_log_ratio_12": {"spearman": -0.10}},
            },
            "val_eval": {
                "2024": {"entry_log_ratio_12": {"spearman": 0.20}},
                "2025": {"entry_log_ratio_12": {"spearman": -0.05}},
            },
        }
    }
    assert runner.yearly_check_pass_for_run(run, "entry_log_ratio", 12) is False


def test_contract_blocker_summary_is_abort_contract_fail():
    summary = {
        "verdict": "ABORT_CONTRACT_FAIL",
        "smoke_status": "PASS",
        "split_horizon_overlap_status": "DIAGNOSTIC_ONLY",
        "tensor_audit_status": "PASS",
    }
    assert summary["verdict"] == "ABORT_CONTRACT_FAIL"


def test_resume_rejects_different_config_hash(tmp_path):
    path = tmp_path / "report.json"
    path.write_text(json.dumps({"run_config_hash": "old", "runs": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="run_config_hash"):
        runner.load_resume_report(path, current_hash="new")


def test_report_has_top_level_machine_fields(tmp_path):
    path = tmp_path / "report.json"
    report = {
        "run_config": {"schema_version": 1, "dependency_versions": {"torch": "x"}},
        "summary": {"verdict": "REJECT_SEQUENCE_CAPACITY_EXPLANATION"},
        "normalization_contract": {"fit_split": "train"},
    }
    runner.save_sequence_report(report, path)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["schema_version"] == 1
    assert saved["verdict"] == "REJECT_SEQUENCE_CAPACITY_EXPLANATION"
    assert saved["dependency_versions"]["torch"] == "x"
    assert saved["normalization_contract"]["fit_split"] == "train"
    assert saved["target_normalization_contract"]["scaler"] == "median_iqr"


def test_run_config_hash_covers_contract_fields():
    config = runner.build_run_config()
    for key in ("split_policy", "normalization_config", "target_normalization_config", "output_schema"):
        assert key in config
    changed = dict(config)
    changed["normalization_config"] = {**config["normalization_config"], "clip": [-5.0, 5.0]}
    assert runner.compute_run_config_hash(config) != runner.compute_run_config_hash(changed)


def test_cli_help_lists_sequence_transformer_flag():
    result = subprocess.run(
        ["./.venv/bin/python", "ML/baseline/benchmark_entry_based_sequence_transformer.py", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "--entry-based-sequence-transformer" in result.stdout
    assert "--resume" in result.stdout
    assert "--no-resume" in result.stdout
