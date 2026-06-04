import pandas as pd
import pytest

from ML.lib_pic_feature_profiles import (
    BASELINE_CLEAN_DROP_GROUPS,
    build_lib_pic_feature_profile,
)


def _fractal(seed: int) -> str:
    direction = 1 if seed % 2 == 0 else -1
    fields = [
        1_700_000_000 + seed,
        100.0 + seed,
        direction,
        2.0 + seed,
        3.0 + seed,
        1,
        seed % 3,
        0.5 + seed,
        4.0 + seed,
        2,
        1.2 + seed,
        0.1 + seed,
        0.2 + seed,
        0.3 + seed,
        0.4 + seed,
        0.5 + seed,
        0.6 + seed,
        0.7 + seed,
        0.8 + seed,
        0.9 + seed,
        1.0 + seed,
        1.5 + seed,
        0,
    ]
    return ':'.join(str(value) for value in fields)


def _frame(rows: int = 3, seq_len: int = 5) -> pd.DataFrame:
    data = {
        'time': [f'2024.01.01 {hour:02d}:00' for hour in range(rows)],
        'ATR': [1.0 + i * 0.01 for i in range(rows)],
        'session_hour': [i % 24 for i in range(rows)],
        'weekday': [i % 5 for i in range(rows)],
    }
    for fractal_idx in range(seq_len):
        data[f'fractal{fractal_idx}'] = [_fractal(i + fractal_idx) for i in range(rows)]
    return pd.DataFrame(data)


def test_baseline_clean_profile_removes_raw_path_and_position_groups():
    frame = _frame(seq_len=5)

    full = build_lib_pic_feature_profile(frame, profile='baseline_full', seq_len=5)
    clean = build_lib_pic_feature_profile(frame, profile='baseline_clean', seq_len=5)

    assert BASELINE_CLEAN_DROP_GROUPS == ('direction', 'price_position', 'path_long', 'path_short')
    assert len(clean.columns) < len(full.columns)
    assert not any(column.startswith('direction_') for column in clean.columns)
    assert not any(column.startswith('price_') for column in clean.columns)
    assert not any(column.startswith('up_') for column in clean.columns)
    assert not any(column.startswith('dn_') for column in clean.columns)
    assert 'front_mean_w5' in clean.columns
    assert 'row_atr' in clean.columns


def test_profile_variants_add_path_and_geometry_banks_only_when_requested():
    frame = _frame(seq_len=5)

    clean = build_lib_pic_feature_profile(frame, profile='baseline_clean', seq_len=5)
    clean_path = build_lib_pic_feature_profile(frame, profile='baseline_clean_path', seq_len=5)
    clean_both = build_lib_pic_feature_profile(frame, profile='baseline_clean_geometry_path', seq_len=5)

    assert not any(column.startswith('pic_path_') for column in clean.columns)
    assert any(column.startswith('pic_path_') for column in clean_path.columns)
    assert not any(column.startswith('pic_geom_') for column in clean_path.columns)
    assert any(column.startswith('pic_path_') for column in clean_both.columns)
    assert any(column.startswith('pic_geom_') for column in clean_both.columns)
    assert len(clean_both.columns) > len(clean_path.columns) > len(clean.columns)


def test_unknown_feature_profile_is_rejected():
    with pytest.raises(ValueError, match='unknown lib_PIC feature profile'):
        build_lib_pic_feature_profile(_frame(), profile='unknown', seq_len=5)
