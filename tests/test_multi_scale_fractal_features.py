import numpy as np

from ML.multi_scale_fractal_features import (
    MULTI_SCALE_WINDOWS,
    build_multi_scale_fractal_features,
)


def test_multi_scale_windows_match_design():
    assert MULTI_SCALE_WINDOWS == (5, 10, 20, 50, 100)


def test_build_multi_scale_fractal_features_returns_finite_summary_matrix():
    fractal_tensor = np.ones((2, 100, 20), dtype=np.float32)

    summary = build_multi_scale_fractal_features(fractal_tensor)

    assert summary.shape == (2, 20 * len(MULTI_SCALE_WINDOWS) * 5)
    assert np.isfinite(summary).all()


def test_build_multi_scale_fractal_features_handles_shorter_effective_windows():
    fractal_tensor = np.zeros((1, 100, 3), dtype=np.float32)
    fractal_tensor[:, :7, :] = 2.0

    summary = build_multi_scale_fractal_features(fractal_tensor, windows=(5, 10))

    assert summary.shape == (1, 3 * 2 * 5)
    assert np.isfinite(summary).all()


def test_build_multi_scale_fractal_features_rejects_wrong_rank():
    fractal_tensor = np.ones((100, 20), dtype=np.float32)

    try:
        build_multi_scale_fractal_features(fractal_tensor)
    except ValueError as exc:
        assert 'shape (n, seq_len, feature_dim)' in str(exc)
    else:
        raise AssertionError('Expected ValueError for non-3D input')
