from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ML.data_loader import N_FRACTAL_FEATURES


def _fractal(seed: int, *, edge: float = 1.0) -> str:
    fav = max(edge, 0.0)
    adv = max(-edge, 0.0)
    fields = [
        1_700_000_000 + seed,
        100.0 + seed,
        1,
        2.0 + seed,
        3.0 + seed,
        1,
        0,
        0.5 + seed,
        4.0 + seed,
        2,
        1.2 + seed,
        fav,
        adv,
        fav,
        adv,
        fav,
        adv,
        fav,
        adv,
        fav,
        adv,
        1.5 + seed,
        0,
    ]
    return ':'.join(str(value) for value in fields)


def _source_frame(rows: int = 6) -> pd.DataFrame:
    data = {
        'time': [f'2024.01.{idx + 1:02d} 00:00' for idx in range(rows)],
        'signal': [1 if idx % 2 == 0 else -1 for idx in range(rows)],
        'predict': [0.1 * idx for idx in range(rows)],
        'ATR': [1.0 + 0.1 * idx for idx in range(rows)],
        'session_hour': [idx % 24 for idx in range(rows)],
        'weekday': [idx % 5 for idx in range(rows)],
        'range_atr_6': [0.2 + idx for idx in range(rows)],
        'body_atr_3': [0.3 + idx for idx in range(rows)],
        'ret_dir_atr_lag1': [0.4 + idx for idx in range(rows)],
        'vol_regime_24': [0.5 + idx for idx in range(rows)],
        'ret_6_dir_atr': [0.6 + idx for idx in range(rows)],
        'ret_12_dir_atr': [0.7 + idx for idx in range(rows)],
        'ret_24_dir_atr': [0.8 + idx for idx in range(rows)],
        'fav_3_atr': [0.9 + idx for idx in range(rows)],
        'adv_3_atr': [1.0 + idx for idx in range(rows)],
        'fav_6_atr': [1.1 + idx for idx in range(rows)],
        'adv_6_atr': [1.2 + idx for idx in range(rows)],
        'fav_12_atr': [1.3 + idx for idx in range(rows)],
        'adv_12_atr': [1.4 + idx for idx in range(rows)],
        'fav_24_atr': [1.5 + idx for idx in range(rows)],
        'adv_24_atr': [1.6 + idx for idx in range(rows)],
    }
    for fractal_idx in range(100):
        data[f'fractal{fractal_idx}'] = [
            _fractal(row_idx + fractal_idx, edge=2.0 if row_idx % 2 == 0 else -1.0)
            for row_idx in range(rows)
        ]
    for column_idx, column in enumerate(
        (
            'trail_12_pnl_atr_x2',
            'trail_12_pnl_atr_x4',
            'trail_24_pnl_atr_x2',
            'trail_24_pnl_atr_x4',
        )
    ):
        data[column] = [1.0 if (row_idx + column_idx) % 2 == 0 else -0.5 for row_idx in range(rows)]
    return pd.DataFrame(data)


def test_original_contour_builder_repeats_engineered_channels():
    from ML.run_take_skip_original_contour_feature_matrix import (
        ORIGINAL_BASELINE_ROW_FEATURE_COLUMNS,
        build_original_baseline_features,
        build_original_contour_arrays,
    )

    frame = _source_frame(rows=4)
    arrays = build_original_contour_arrays(frame, feature_mode='original_baseline', seq_len=20)
    baseline_features = build_original_baseline_features(frame, arrays.parsed_X)

    assert arrays.X.shape[0] == 4
    assert arrays.X.shape[1] == 20
    assert arrays.X.shape[2] == N_FRACTAL_FEATURES + baseline_features.shape[1]
    assert arrays.mask.shape == (4, 20)
    assert arrays.y.shape == (4, 4)
    assert arrays.target_columns == ('take_12_x2', 'take_12_x4', 'take_24_x2', 'take_24_x4')
    assert baseline_features.shape[1] > len(ORIGINAL_BASELINE_ROW_FEATURE_COLUMNS)

    repeated = arrays.X[:, :, N_FRACTAL_FEATURES:]
    assert np.allclose(repeated[:, 0, :], repeated[:, -1, :])
    assert np.allclose(repeated[:, 0, :], baseline_features)
    assert np.isfinite(arrays.X).all()


def test_feature_modes_expand_original_contour_without_row_drift():
    from ML.run_take_skip_original_contour_feature_matrix import build_original_contour_arrays

    frame = _source_frame(rows=5)
    baseline = build_original_contour_arrays(frame, feature_mode='original_baseline', seq_len=20)
    with_path = build_original_contour_arrays(frame, feature_mode='original_plus_path', seq_len=20)
    with_geometry_path = build_original_contour_arrays(frame, feature_mode='original_plus_geometry_path', seq_len=20)

    assert baseline.X.shape[0] == with_path.X.shape[0] == with_geometry_path.X.shape[0] == 5
    assert baseline.X.shape[1] == with_path.X.shape[1] == with_geometry_path.X.shape[1] == 20
    assert baseline.y.shape == with_path.y.shape == with_geometry_path.y.shape
    assert baseline.target_columns == with_path.target_columns == with_geometry_path.target_columns
    assert np.array_equal(baseline.mask, with_path.mask)
    assert np.array_equal(baseline.mask, with_geometry_path.mask)

    assert with_path.X.shape[2] > baseline.X.shape[2]
    assert with_geometry_path.X.shape[2] > with_path.X.shape[2]
    assert np.allclose(with_path.X[:, :, : baseline.X.shape[2]], baseline.X)
    assert np.allclose(with_geometry_path.X[:, :, : baseline.X.shape[2]], baseline.X)


def test_live_safe_baseline_excludes_future_derived_row_features():
    from ML.run_take_skip_original_contour_feature_matrix import (
        LIVE_SAFE_BASELINE_ROW_FEATURE_COLUMNS,
        ORIGINAL_BASELINE_ROW_FEATURE_COLUMNS,
        build_live_safe_baseline_features,
        build_original_baseline_features,
        build_original_contour_arrays,
    )

    frame = _source_frame(rows=4)
    arrays = build_original_contour_arrays(frame, feature_mode='live_safe_baseline', seq_len=20)
    original_features = build_original_baseline_features(frame, arrays.parsed_X)
    live_safe_features = build_live_safe_baseline_features(frame, arrays.parsed_X)

    forbidden = {
        'predict',
        'ret_dir_atr_lag1',
        'ret_6_dir_atr',
        'ret_12_dir_atr',
        'ret_24_dir_atr',
        'fav_3_atr',
        'adv_3_atr',
        'fav_6_atr',
        'adv_6_atr',
        'fav_12_atr',
        'adv_12_atr',
        'fav_24_atr',
        'adv_24_atr',
    }

    assert not forbidden.intersection(LIVE_SAFE_BASELINE_ROW_FEATURE_COLUMNS)
    assert forbidden.issubset(set(ORIGINAL_BASELINE_ROW_FEATURE_COLUMNS))
    assert live_safe_features.shape[1] < original_features.shape[1]
    assert arrays.X.shape[2] == N_FRACTAL_FEATURES + live_safe_features.shape[1]
    assert np.allclose(arrays.X[:, 0, N_FRACTAL_FEATURES:], live_safe_features)


def test_live_safe_geometry_expands_live_safe_baseline_without_path_fields():
    from ML.run_take_skip_original_contour_feature_matrix import build_original_contour_arrays

    frame = _source_frame(rows=5)
    baseline = build_original_contour_arrays(frame, feature_mode='live_safe_baseline', seq_len=20)
    geometry = build_original_contour_arrays(frame, feature_mode='live_safe_geometry', seq_len=20)

    assert geometry.X.shape[0] == baseline.X.shape[0] == 5
    assert geometry.X.shape[1] == baseline.X.shape[1] == 20
    assert geometry.y.shape == baseline.y.shape
    assert geometry.target_columns == baseline.target_columns
    assert np.array_equal(geometry.mask, baseline.mask)
    assert geometry.X.shape[2] > baseline.X.shape[2]
    assert np.allclose(geometry.X[:, :, : baseline.X.shape[2]], baseline.X)


def test_live_safe_path_expands_live_safe_baseline_with_mt_updn_features():
    from ML.run_take_skip_original_contour_feature_matrix import build_original_contour_arrays

    frame = _source_frame(rows=5)
    baseline = build_original_contour_arrays(frame, feature_mode='live_safe_baseline', seq_len=20)
    path = build_original_contour_arrays(frame, feature_mode='live_safe_path', seq_len=20)

    assert path.X.shape[0] == baseline.X.shape[0] == 5
    assert path.X.shape[1] == baseline.X.shape[1] == 20
    assert path.y.shape == baseline.y.shape
    assert path.target_columns == baseline.target_columns
    assert np.array_equal(path.mask, baseline.mask)
    assert path.X.shape[2] > baseline.X.shape[2]
    assert np.allclose(path.X[:, :, : baseline.X.shape[2]], baseline.X)


def test_live_safe_path_uses_windows_limited_by_seq_len():
    from ML.run_take_skip_original_contour_feature_matrix import build_original_contour_arrays

    frame = _source_frame(rows=5)
    seq20 = build_original_contour_arrays(frame, feature_mode='live_safe_path', seq_len=20)
    seq50 = build_original_contour_arrays(frame, feature_mode='live_safe_path', seq_len=50)

    assert seq50.engineered.shape[1] > seq20.engineered.shape[1]
    assert seq20.X.shape[2] == N_FRACTAL_FEATURES + seq20.engineered.shape[1]
    assert seq50.X.shape[2] == N_FRACTAL_FEATURES + seq50.engineered.shape[1]


def test_original_contour_runner_writes_summary_and_benchmark(tmp_path: Path):
    from ML.run_take_skip_original_contour_feature_matrix import run_single_config_from_frames

    result = run_single_config_from_frames(
        train_frame=_source_frame(rows=8),
        validation_frame=_source_frame(rows=6),
        test_frame=_source_frame(rows=6),
        output_root=tmp_path / 'matrix',
        feature_mode='original_baseline',
        seq_len=20,
        epochs=1,
        patience=1,
        batch_size=4,
        seed=42,
        min_pf=1.0,
        min_trades_per_year=0.1,
        target_columns=('take_12_x2', 'take_24_x4'),
        model_kwargs={'d_model': 16, 'nhead': 4, 'num_layers': 1, 'dim_feedforward': 32, 'dropout': 0.0},
    )

    run_dir = tmp_path / 'matrix' / 'original_baseline_seq20'
    assert (run_dir / 'checkpoint.pt').exists()
    assert (run_dir / 'take_skip_trailing_stop_v2_validation_predictions.csv').exists()
    assert (run_dir / 'take_skip_trailing_stop_v2_test_predictions.csv').exists()
    assert (run_dir / 'summary.json').exists()
    assert (run_dir / 'benchmark' / 'final_verdict.json').exists()

    saved = json.loads((run_dir / 'summary.json').read_text(encoding='utf-8'))
    assert saved['config']['feature_mode'] == 'original_baseline'
    assert saved['config']['target_columns'] == ['take_12_x2', 'take_24_x4']
    assert saved['config']['input_features'] > 20
    assert result['benchmark']['validation_grid_path'].endswith('validation_grid.csv')
