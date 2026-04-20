import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ML.take_skip_trailing_stop_v2_task import TAKE_SKIP_TRUE_PNL_V2_COLUMNS


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
    ]
    return ':'.join(str(value) for value in fields)


def _source_frame(rows: int = 6) -> pd.DataFrame:
    data = {
        'time': [f'2024.01.{idx + 1:02d} 00:00' for idx in range(rows)],
        'signal': [1 if idx % 2 == 0 else -1 for idx in range(rows)],
        'predict': [0.0] * rows,
        'ATR': [1.0] * rows,
    }
    for fractal_idx in range(100):
        data[f'fractal{fractal_idx}'] = [
            _fractal(row_idx + fractal_idx, edge=2.0 if row_idx % 2 == 0 else -1.0)
            for row_idx in range(rows)
        ]
    for idx, column in enumerate(TAKE_SKIP_TRUE_PNL_V2_COLUMNS):
        data[column] = [1.0 if (row_idx + idx) % 3 == 0 else -0.5 for row_idx in range(rows)]
    return pd.DataFrame(data)


def _source_frame_old_grid(rows: int = 6) -> pd.DataFrame:
    frame = _source_frame(rows=rows)
    drop_cols = [column for column in TAKE_SKIP_TRUE_PNL_V2_COLUMNS if column.endswith('_x10') or column.endswith('_x12')]
    return frame.drop(columns=drop_cols)


def test_take_skip_dual_stream_model_outputs_logits():
    from ML.models.take_skip_dual_stream_transformer import TakeSkipDualStreamTransformer

    model = TakeSkipDualStreamTransformer(input_features=20, engineered_feature_dim=7, output_dim=15)
    output = model(
        torch.randn(3, 5, 20),
        engineered=torch.randn(3, 7),
        mask=torch.ones(3, 5, dtype=torch.bool),
    )

    assert output.shape == (3, 15)
    assert not torch.allclose(output, torch.sigmoid(output))


def test_build_feature_dataset_uses_profile_and_targets():
    from ML.run_take_skip_lib_pic_feature_matrix import build_take_skip_feature_arrays

    arrays = build_take_skip_feature_arrays(
        _source_frame(rows=4),
        feature_profile='baseline_clean_path',
        seq_len=20,
        target_columns=('take_12_x2', 'take_24_x4', 'take_48_x8'),
    )

    assert arrays.X.shape == (4, 20, 20)
    assert arrays.mask.shape == (4, 20)
    assert arrays.engineered.shape[0] == 4
    assert arrays.engineered.shape[1] > 100
    assert arrays.y.shape == (4, 3)
    assert np.isfinite(arrays.X).all()
    assert np.isfinite(arrays.engineered).all()


def test_resolve_target_columns_uses_available_old_grid():
    from ML.run_take_skip_lib_pic_feature_matrix import resolve_target_columns

    target_columns = resolve_target_columns(_source_frame_old_grid(rows=4))

    assert target_columns == (
        'take_12_x2', 'take_12_x4', 'take_12_x8',
        'take_24_x2', 'take_24_x4', 'take_24_x8',
        'take_48_x2', 'take_48_x4', 'take_48_x8',
    )


def test_run_single_config_writes_summary_and_exports(tmp_path: Path):
    from ML.run_take_skip_lib_pic_feature_matrix import run_single_config_from_frames

    train = _source_frame(rows=8)
    validation = _source_frame(rows=6)
    test = _source_frame(rows=6)

    result = run_single_config_from_frames(
        train_frame=train,
        validation_frame=validation,
        test_frame=test,
        output_root=tmp_path / 'matrix',
        feature_profile='baseline_clean',
        seq_len=20,
        epochs=1,
        patience=1,
        batch_size=4,
        seed=42,
        min_pf=1.0,
        min_trades_per_year=0.1,
        target_columns=('take_12_x2', 'take_24_x4', 'take_48_x8'),
        model_kwargs={'d_model': 16, 'nhead': 4, 'num_layers': 1, 'dim_feedforward': 32, 'dropout': 0.0},
    )

    run_dir = tmp_path / 'matrix' / 'baseline_clean_seq20'
    assert (run_dir / 'checkpoint.pt').exists()
    assert (run_dir / 'take_skip_trailing_stop_v2_validation_predictions.csv').exists()
    assert (run_dir / 'take_skip_trailing_stop_v2_test_predictions.csv').exists()
    assert (run_dir / 'summary.json').exists()
    assert (run_dir / 'benchmark' / 'final_verdict.json').exists()
    saved = json.loads((run_dir / 'summary.json').read_text(encoding='utf-8'))
    assert saved['config']['feature_profile'] == 'baseline_clean'
    assert saved['config']['target_columns'] == ['take_12_x2', 'take_24_x4', 'take_48_x8']
    assert result['benchmark']['validation_grid_path'].endswith('validation_grid.csv')


def test_run_matrix_accepts_parallel_jobs_and_torch_threads(monkeypatch, tmp_path: Path):
    from ML import run_take_skip_lib_pic_feature_matrix as runner

    calls = []

    def fake_read_labeled_csv(_path):
        return _source_frame_old_grid(rows=4)

    def fake_run_single_config_from_frames(**kwargs):
        calls.append(kwargs)
        return {
            'config': {
                'feature_profile': kwargs['feature_profile'],
                'seq_len': kwargs['seq_len'],
                'torch_threads': kwargs['torch_threads'],
            }
        }

    monkeypatch.setattr(runner, '_read_labeled_csv', fake_read_labeled_csv)
    monkeypatch.setattr(runner, 'run_single_config_from_frames', fake_run_single_config_from_frames)

    manifest = runner.run_matrix(
        output_dir=tmp_path / 'matrix',
        feature_profiles=('baseline_clean',),
        seq_lens=(20, 50),
        epochs=1,
        patience=1,
        batch_size=4,
        seed=42,
        min_pf=1.0,
        min_trades_per_year=0.1,
        target_columns=None,
        jobs=1,
        torch_threads=3,
    )

    assert len(calls) == 2
    assert {call['seq_len'] for call in calls} == {20, 50}
    assert all(call['torch_threads'] == 3 for call in calls)
    assert manifest['jobs'] == 1
    assert manifest['torch_threads'] == 3
