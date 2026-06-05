import numpy as np
import pandas as pd

from ML.lib_pic_geometry_feature_bank import (
    GEOMETRY_FEATURE_COLUMNS,
    build_lib_pic_geometry_feature_bank,
)


def _fractal(front: float, back: float, reverse: float = 0.0, atr: float = 1.0) -> str:
    fields = [
        '1700000000',
        '100.0',
        '1',
        str(front),
        str(back),
        '1',
        '0',
        str(reverse),
        '2.0',
        '1',
        '0.5',
        '0',
        '0',
        '0',
        '0',
        '0',
        '0',
        '0',
        '0',
        '0',
        '0',
        str(atr),
        '0',
    ]
    return ':'.join(fields)


def test_geometry_feature_bank_adds_expected_columns():
    frame = pd.DataFrame(
        {
            'fractal0': [_fractal(4.0, 2.0, reverse=1.0)],
            'fractal1': [_fractal(2.0, 2.0, reverse=0.5)],
            'fractal2': [_fractal(1.0, 3.0, reverse=0.0)],
            'fractal3': [_fractal(1.0, 1.0, reverse=0.0)],
            'fractal4': [_fractal(2.0, 1.0, reverse=0.0)],
        }
    )

    out = build_lib_pic_geometry_feature_bank(frame, windows=(5,))

    assert 'pic_geom_ratio_recent_w5' in out.columns
    assert 'pic_geom_balance_recent_w5' in out.columns
    assert 'pic_geom_front_dominant_share_w5' in out.columns
    assert out.loc[0, 'pic_geom_ratio_recent_w5'] > 1.99
    assert np.isclose(out.loc[0, 'pic_geom_front_dominant_share_w5'], 0.4)


def test_geometry_feature_bank_uses_fractal0_as_recent():
    frame = pd.DataFrame(
        {
            'fractal0': [_fractal(10.0, 1.0)],
            'fractal1': [_fractal(1.0, 10.0)],
        }
    )

    out = build_lib_pic_geometry_feature_bank(frame, windows=(2,))

    assert np.isclose(out.loc[0, 'pic_geom_front_recent_w2'], 10.0)
    assert np.isclose(out.loc[0, 'pic_geom_back_recent_w2'], 1.0)
    assert out.loc[0, 'pic_geom_front_recent_minus_mean_w2'] > 0


def test_geometry_feature_bank_does_not_require_updn_values():
    short_legacy_fractal = '1700000000:100:1:2:4:1:0:0.5:1:1:0.1'
    frame = pd.DataFrame({'fractal0': [short_legacy_fractal]})

    out = build_lib_pic_geometry_feature_bank(frame, windows=(5,))

    assert 'pic_geom_atr_recent_w5' in out.columns
    assert np.isfinite(out.filter(like='pic_geom_').to_numpy()).all()


def test_geometry_feature_bank_handles_empty_frame_without_fractals():
    frame = pd.DataFrame({'time': ['2024.01.01 00:00']})

    out = build_lib_pic_geometry_feature_bank(frame, windows=(5,))

    assert out.loc[0, 'pic_geom_front_mean_w5'] == 0.0


def test_geometry_feature_columns_match_default_windows():
    assert 'pic_geom_front_mean_w5' in GEOMETRY_FEATURE_COLUMNS
    assert 'pic_geom_size_recent_minus_mean_w100' in GEOMETRY_FEATURE_COLUMNS
