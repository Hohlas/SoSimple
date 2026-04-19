import numpy as np
import pandas as pd

from ML.lib_pic_path_reaction_feature_bank import (
    PATH_REACTION_FEATURE_COLUMNS,
    build_lib_pic_path_reaction_feature_bank,
)


def _fractal(direction: int, up: dict[int, float], dn: dict[int, float]) -> str:
    fields = [
        '1700000000',
        '100.0',
        str(direction),
        '2.0',
        '3.0',
        '1',
        '0',
        '0.5',
        '2.0',
        '1',
        '0.5',
        str(up[12]),
        str(dn[12]),
        str(up[24]),
        str(dn[24]),
        str(up[48]),
        str(dn[48]),
        str(up[3]),
        str(dn[3]),
        str(up[6]),
        str(dn[6]),
        '1.5',
    ]
    return ':'.join(fields)


def test_path_reaction_feature_bank_adds_expected_columns_for_long_direction():
    frame = pd.DataFrame(
        {
            'fractal0': [
                _fractal(
                    1,
                    up={3: 1.0, 6: 2.0, 12: 3.0, 24: 4.0, 48: 5.0},
                    dn={3: 0.5, 6: 1.0, 12: 1.5, 24: 2.0, 48: 2.5},
                )
            ],
            'fractal1': [
                _fractal(
                    1,
                    up={3: 2.0, 6: 3.0, 12: 4.0, 24: 5.0, 48: 6.0},
                    dn={3: 1.0, 6: 1.5, 12: 2.0, 24: 2.5, 48: 3.0},
                )
            ],
        }
    )

    out = build_lib_pic_path_reaction_feature_bank(frame, windows=(2,))

    assert 'pic_path_fav24_mean_w2' in out.columns
    assert 'pic_path_adv24_mean_w2' in out.columns
    assert 'pic_path_edge24_recent_w2' in out.columns
    assert np.isclose(out.loc[0, 'pic_path_fav24_recent_w2'], 4.0)
    assert np.isclose(out.loc[0, 'pic_path_adv24_recent_w2'], 2.0)
    assert np.isclose(out.loc[0, 'pic_path_edge24_recent_w2'], 2.0)


def test_path_reaction_feature_bank_flips_fav_adv_for_short_direction():
    frame = pd.DataFrame(
        {
            'fractal0': [
                _fractal(
                    -1,
                    up={3: 1.0, 6: 1.0, 12: 1.0, 24: 1.0, 48: 1.0},
                    dn={3: 5.0, 6: 5.0, 12: 5.0, 24: 5.0, 48: 5.0},
                )
            ]
        }
    )

    out = build_lib_pic_path_reaction_feature_bank(frame, windows=(1,))

    assert np.isclose(out.loc[0, 'pic_path_fav48_recent_w1'], 5.0)
    assert np.isclose(out.loc[0, 'pic_path_adv48_recent_w1'], 1.0)
    assert out.loc[0, 'pic_path_win_proxy48_share_w1'] == 1.0


def test_path_reaction_feature_bank_handles_empty_or_legacy_fractals():
    frame = pd.DataFrame({'fractal0': ['1700000000:100:1:2:3:1:0:0.5:2:1:0.5']})

    out = build_lib_pic_path_reaction_feature_bank(frame, windows=(5,))

    assert 'pic_path_fav12_mean_w5' in out.columns
    assert np.isfinite(out.filter(like='pic_path_').to_numpy()).all()
    assert out.loc[0, 'pic_path_fav12_mean_w5'] == 0.0


def test_path_reaction_feature_bank_uses_fractal0_as_recent():
    frame = pd.DataFrame(
        {
            'fractal0': [
                _fractal(1, up={3: 9, 6: 9, 12: 9, 24: 9, 48: 9}, dn={3: 1, 6: 1, 12: 1, 24: 1, 48: 1})
            ],
            'fractal1': [
                _fractal(1, up={3: 2, 6: 2, 12: 2, 24: 2, 48: 2}, dn={3: 1, 6: 1, 12: 1, 24: 1, 48: 1})
            ],
        }
    )

    out = build_lib_pic_path_reaction_feature_bank(frame, windows=(2,))

    assert np.isclose(out.loc[0, 'pic_path_fav12_recent_w2'], 9.0)
    assert out.loc[0, 'pic_path_fav_slope_3_48_mean_w2'] == 0.0


def test_path_reaction_feature_columns_match_default_windows():
    assert 'pic_path_fav3_mean_w5' in PATH_REACTION_FEATURE_COLUMNS
    assert 'pic_path_edge_slope_12_48_mean_w100' in PATH_REACTION_FEATURE_COLUMNS
