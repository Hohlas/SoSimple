# =============================================================================
# Файл: tests/test_signal_path_atlas.py
# Назначение: Набор unit и smoke tests для Signal Path Atlas research CLI.
#   Проверяет корректность fixed calendar split, ATR-normalized path math,
#   conditioning features, slice construction, archetype labeling, holdout
#   replication logic, CSV export и базовый CLI flow, чтобы изменения в
#   исследовательском инструменте не ломали его статистический контракт.
# Язык: Python 3.10+
# Создан: 2026-04-03
# Зависимости:
#   Входные данные:
#     - synthetic pandas DataFrame fixtures inside tests
#   Выходные данные:
#     - pytest assertions for API/signal_path_atlas.py
# Внешние зависимости:
#   - pytest>=8.0, numpy>=1.24, pandas>=2.0
# Использование:
#   ./.venv/bin/python -m pytest tests/test_signal_path_atlas.py -q
# Примечания:
#   - тесты покрывают split semantics, path tensor, slices, archetypes и CLI smoke
#   - реальные CLI-прогоны path atlas дополнительно верифицируются вручную перед stage close
# =============================================================================

import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, 'API')
import signal_path_atlas as spa


def _ohlc_frame():
    return pd.DataFrame({
        'time': pd.to_datetime([
            '2024-12-31 23:00',
            '2025-01-01 00:00',
            '2025-01-01 01:00',
            '2025-01-01 02:00',
            '2025-01-01 03:00',
        ]),
        'open': [100.0, 100.0, 102.0, 99.0, 103.0],
        'high': [101.0, 103.0, 104.0, 105.0, 106.0],
        'low': [99.0, 99.5, 97.0, 98.0, 101.0],
        'close': [100.0, 102.0, 98.0, 104.0, 105.0],
        'atr14': [2.0, 2.0, 2.0, 2.0, 2.0],
    })


def test_annotate_sample_split_uses_fixed_calendar_boundary():
    frame = pd.DataFrame({
        'time': pd.to_datetime(['2024-12-31 23:59:59', '2025-01-01 00:00:00'])
    })
    out = spa.annotate_sample_split(frame)
    assert out['sample'].tolist() == ['discovery', 'holdout']


def test_build_path_tensor_aligns_buy_and_sell_in_signed_atr_space():
    ohlc = pd.concat([
        _ohlc_frame(),
        pd.DataFrame({
            'time': pd.date_range('2025-01-01 04:00', periods=12, freq='h'),
            'open': [106.0 + i for i in range(12)],
            'high': [107.0 + i for i in range(12)],
            'low': [105.0 + i for i in range(12)],
            'close': [106.0 + i for i in range(12)],
            'atr14': [2.0] * 12,
        }),
    ], ignore_index=True)
    signals = pd.DataFrame([
        {'time': ohlc.loc[0, 'time'], 'signal': 1, 'entry_close': 100.0, 'entry_atr14': 2.0},
        {'time': ohlc.loc[1, 'time'], 'signal': -1, 'entry_close': 102.0, 'entry_atr14': 2.0},
    ])

    out = spa.build_path_tensor(signals, ohlc)

    assert out.loc[0, 'signed_ret_1'] == pytest.approx(1.0, abs=1e-9)
    assert out.loc[0, 'fav_2'] == pytest.approx(2.0, abs=1e-9)
    assert out.loc[0, 'adv_2'] == pytest.approx(1.5, abs=1e-9)
    assert out.loc[1, 'signed_ret_1'] == pytest.approx(2.0, abs=1e-9)
    assert out.loc[1, 'fav_2'] == pytest.approx(2.5, abs=1e-9)
    assert out.loc[1, 'adv_2'] == pytest.approx(1.5, abs=1e-9)
    assert out.columns.tolist().count('adverse_first_1.0atr') == 1
    assert out.columns.tolist().count('favorable_first_1.0atr') == 1
    assert out.columns.tolist().count('dip_then_rally_1.0atr') == 1
    assert out.columns.tolist().count('rally_then_dip_1.0atr') == 1
    assert out.columns.tolist().count('adverse_first_2.0atr') == 1
    assert out.columns.tolist().count('favorable_first_2.0atr') == 1
    assert out.columns.tolist().count('dip_then_rally_2.0atr') == 1
    assert out.columns.tolist().count('rally_then_dip_2.0atr') == 1
    assert out.columns.tolist().count('adverse_first_3.0atr') == 1
    assert out.columns.tolist().count('favorable_first_3.0atr') == 1
    assert out.columns.tolist().count('dip_then_rally_3.0atr') == 1
    assert out.columns.tolist().count('rally_then_dip_3.0atr') == 1

    assert out.loc[0, 'adverse_first_1.0atr'] == pytest.approx(0.0, abs=1e-9)
    assert out.loc[0, 'favorable_first_1.0atr'] == pytest.approx(1.0, abs=1e-9)
    assert out.loc[0, 'dip_then_rally_1.0atr'] == pytest.approx(0.0, abs=1e-9)
    assert out.loc[0, 'rally_then_dip_1.0atr'] == pytest.approx(1.0, abs=1e-9)
    assert out.loc[0, 'favorable_first_2.0atr'] == pytest.approx(1.0, abs=1e-9)
    assert out.loc[0, 'favorable_first_3.0atr'] == pytest.approx(1.0, abs=1e-9)

    assert out.loc[1, 'adverse_first_1.0atr'] == pytest.approx(0.0, abs=1e-9)
    assert out.loc[1, 'favorable_first_1.0atr'] == pytest.approx(0.0, abs=1e-9)
    assert out.loc[1, 'dip_then_rally_1.0atr'] == pytest.approx(0.0, abs=1e-9)
    assert out.loc[1, 'rally_then_dip_1.0atr'] == pytest.approx(0.0, abs=1e-9)
    assert out.loc[1, 'favorable_first_2.0atr'] == pytest.approx(1.0, abs=1e-9)
    assert out.loc[1, 'rally_then_dip_2.0atr'] == pytest.approx(1.0, abs=1e-9)


def test_build_path_tensor_leaves_unavailable_horizons_nan_near_series_end():
    ohlc = _ohlc_frame()
    signals = pd.DataFrame([
        {'time': ohlc.loc[3, 'time'], 'signal': 1, 'entry_close': 99.0, 'entry_atr14': 2.0},
    ])

    out = spa.build_path_tensor(signals, ohlc)

    assert out.loc[0, 'signed_ret_1'] == pytest.approx(3.0, abs=1e-9)
    assert out.loc[0, 'fav_1'] == pytest.approx(3.5, abs=1e-9)
    assert out.loc[0, 'adv_1'] == pytest.approx(-1.0, abs=1e-9)
    assert pd.isna(out.loc[0, 'signed_ret_2'])
    assert pd.isna(out.loc[0, 'fav_2'])
    assert pd.isna(out.loc[0, 'adv_2'])
    assert pd.isna(out.loc[0, 'adverse_first_1.0atr'])
    assert pd.isna(out.loc[0, 'favorable_first_1.0atr'])
    assert pd.isna(out.loc[0, 'dip_then_rally_1.0atr'])
    assert pd.isna(out.loc[0, 'rally_then_dip_1.0atr'])
    assert pd.isna(out.loc[0, 'adverse_first_2.0atr'])
    assert pd.isna(out.loc[0, 'favorable_first_2.0atr'])
    assert pd.isna(out.loc[0, 'dip_then_rally_2.0atr'])
    assert pd.isna(out.loc[0, 'rally_then_dip_2.0atr'])
    assert pd.isna(out.loc[0, 'adverse_first_3.0atr'])
    assert pd.isna(out.loc[0, 'favorable_first_3.0atr'])
    assert pd.isna(out.loc[0, 'dip_then_rally_3.0atr'])
    assert pd.isna(out.loc[0, 'rally_then_dip_3.0atr'])


def test_build_path_tensor_raises_when_a_signal_timestamp_is_missing_from_ohlc():
    ohlc = _ohlc_frame()
    signals = pd.DataFrame([
        {'time': pd.Timestamp('2025-01-01 09:00:00'), 'signal': 1, 'entry_close': 100.0, 'entry_atr14': 2.0},
    ])

    with pytest.raises(ValueError, match='missing from OHLC'):
        spa.build_path_tensor(signals, ohlc)


def test_build_path_tensor_raises_when_any_signal_timestamp_is_missing_from_ohlc():
    ohlc = _ohlc_frame()
    signals = pd.DataFrame([
        {'time': ohlc.loc[0, 'time'], 'signal': 1, 'entry_close': 100.0, 'entry_atr14': 2.0},
        {'time': pd.Timestamp('2025-01-01 09:00:00'), 'signal': -1, 'entry_close': 101.0, 'entry_atr14': 2.0},
    ])

    with pytest.raises(ValueError, match='missing from OHLC'):
        spa.build_path_tensor(signals, ohlc)


def test_build_conditioning_frame_creates_ratio_spread_short_vs_long_and_fixed_cohorts():
    frame = pd.DataFrame([
        {
            'time': pd.Timestamp('2024-06-01 00:00'),
            'signal': 1,
            'entry_atr14': 2.0,
            'up_3': 6.0, 'dn_3': 2.0,
            'up_6': 8.0, 'dn_6': 4.0,
            'up_12': 10.0, 'dn_12': 5.0,
            'up_24': 12.0, 'dn_24': 6.0,
            'up_48': 14.0, 'dn_48': 7.0,
        },
        {
            'time': pd.Timestamp('2024-06-01 01:00'),
            'signal': 1,
            'entry_atr14': 2.5,
            'up_3': 7.0, 'dn_3': 3.0,
            'up_6': 9.0, 'dn_6': 4.0,
            'up_12': 11.0, 'dn_12': 5.0,
            'up_24': 13.0, 'dn_24': 6.0,
            'up_48': 15.0, 'dn_48': 8.0,
        },
        {
            'time': pd.Timestamp('2024-06-01 02:00'),
            'signal': -1,
            'entry_atr14': 3.0,
            'up_3': 4.0, 'dn_3': 8.0,
            'up_6': 5.0, 'dn_6': 10.0,
            'up_12': 6.0, 'dn_12': 12.0,
            'up_24': 7.0, 'dn_24': 14.0,
            'up_48': 8.0, 'dn_48': 16.0,
        },
        {
            'time': pd.Timestamp('2024-06-01 03:00'),
            'signal': -1,
            'entry_atr14': 4.0,
            'up_3': 5.0, 'dn_3': 9.0,
            'up_6': 6.0, 'dn_6': 11.0,
            'up_12': 7.0, 'dn_12': 13.0,
            'up_24': 8.0, 'dn_24': 15.0,
            'up_48': 9.0, 'dn_48': 17.0,
        },
    ])
    out, artifacts = spa.build_conditioning_frame(frame)
    assert out.loc[0, 'ratio_12'] == pytest.approx(2.0, abs=1e-9)
    assert out.loc[0, 'spread_12'] == pytest.approx(5.0, abs=1e-9)
    assert out.loc[0, 'ratio_3_vs_12'] == pytest.approx(1.5, abs=1e-9)
    assert out.loc[0, 'signal_label'] == 'BUY'
    assert out.loc[0, 'ratio_bin_12'] == '2-3'
    assert out.loc[2, 'signal_label'] == 'SELL'
    assert out.loc[2, 'pred_fav_12'] == pytest.approx(12.0, abs=1e-9)
    assert out.loc[2, 'pred_adv_12'] == pytest.approx(6.0, abs=1e-9)
    assert artifacts['atr_edges'][0] <= out.loc[0, 'entry_atr14'] <= artifacts['atr_edges'][-1]


def test_build_conditioning_frame_preserves_existing_pred_column_when_only_sibling_is_missing():
    frame = pd.DataFrame([
        {
            'time': pd.Timestamp('2024-06-01 00:00'),
            'signal': 1,
            'entry_atr14': 2.0,
            'up_3': 6.0,
            'dn_3': 2.0,
            'up_6': 8.0,
            'dn_6': 4.0,
            'up_12': 10.0,
            'dn_12': 5.0,
            'up_24': 12.0,
            'dn_24': 6.0,
            'up_48': 14.0,
            'dn_48': 7.0,
            'pred_fav_3': 999.0,
        },
        {
            'time': pd.Timestamp('2024-06-01 01:00'),
            'signal': -1,
            'entry_atr14': 2.5,
            'up_3': 7.0,
            'dn_3': 3.0,
            'up_6': 9.0,
            'dn_6': 4.0,
            'up_12': 11.0,
            'dn_12': 5.0,
            'up_24': 13.0,
            'dn_24': 6.0,
            'up_48': 15.0,
            'dn_48': 8.0,
        },
        {
            'time': pd.Timestamp('2024-06-01 02:00'),
            'signal': 1,
            'entry_atr14': 3.0,
            'up_3': 4.0,
            'dn_3': 8.0,
            'up_6': 5.0,
            'dn_6': 10.0,
            'up_12': 6.0,
            'dn_12': 12.0,
            'up_24': 7.0,
            'dn_24': 14.0,
            'up_48': 8.0,
            'dn_48': 16.0,
        },
        {
            'time': pd.Timestamp('2024-06-01 03:00'),
            'signal': -1,
            'entry_atr14': 4.0,
            'up_3': 5.0,
            'dn_3': 9.0,
            'up_6': 6.0,
            'dn_6': 11.0,
            'up_12': 7.0,
            'dn_12': 13.0,
            'up_24': 8.0,
            'dn_24': 15.0,
            'up_48': 9.0,
            'dn_48': 17.0,
        },
    ])

    out, _ = spa.build_conditioning_frame(frame)

    assert out.loc[0, 'pred_fav_3'] == pytest.approx(999.0, abs=1e-9)
    assert out.loc[0, 'pred_adv_3'] == pytest.approx(2.0, abs=1e-9)
    assert out.loc[1, 'pred_fav_3'] == pytest.approx(3.0, abs=1e-9)
    assert out.loc[1, 'pred_adv_3'] == pytest.approx(7.0, abs=1e-9)


def test_build_conditioning_frame_uses_single_bucket_fallback_when_atr_quantiles_collapse():
    frame = pd.DataFrame([
        {
            'time': pd.Timestamp('2024-06-01 00:00'),
            'signal': 1,
            'entry_atr14': 2.0,
            'up_3': 6.0, 'dn_3': 2.0,
            'up_6': 8.0, 'dn_6': 4.0,
            'up_12': 10.0, 'dn_12': 5.0,
            'up_24': 12.0, 'dn_24': 6.0,
            'up_48': 14.0, 'dn_48': 7.0,
        },
        {
            'time': pd.Timestamp('2024-06-01 01:00'),
            'signal': -1,
            'entry_atr14': 2.0,
            'up_3': 7.0, 'dn_3': 3.0,
            'up_6': 9.0, 'dn_6': 4.0,
            'up_12': 11.0, 'dn_12': 5.0,
            'up_24': 13.0, 'dn_24': 6.0,
            'up_48': 15.0, 'dn_48': 8.0,
        },
        {
            'time': pd.Timestamp('2024-06-01 02:00'),
            'signal': 1,
            'entry_atr14': 2.0,
            'up_3': 4.0, 'dn_3': 8.0,
            'up_6': 5.0, 'dn_6': 10.0,
            'up_12': 6.0, 'dn_12': 12.0,
            'up_24': 7.0, 'dn_24': 14.0,
            'up_48': 8.0, 'dn_48': 16.0,
        },
        {
            'time': pd.Timestamp('2024-06-01 03:00'),
            'signal': -1,
            'entry_atr14': 2.0,
            'up_3': 5.0, 'dn_3': 9.0,
            'up_6': 6.0, 'dn_6': 11.0,
            'up_12': 7.0, 'dn_12': 13.0,
            'up_24': 8.0, 'dn_24': 15.0,
            'up_48': 9.0, 'dn_48': 17.0,
        },
    ])

    out, artifacts = spa.build_conditioning_frame(frame)

    assert out['atr_bucket'].tolist() == ['Q1', 'Q1', 'Q1', 'Q1']
    assert artifacts['atr_edges'].tolist() == [2.0]


def test_build_conditioning_frame_leaves_missing_atr_rows_unbucketed():
    frame = pd.DataFrame([
        {
            'time': pd.Timestamp('2024-06-01 00:00'),
            'signal': 1,
            'entry_atr14': 2.0,
            'up_3': 6.0, 'dn_3': 2.0,
            'up_6': 8.0, 'dn_6': 4.0,
            'up_12': 10.0, 'dn_12': 5.0,
            'up_24': 12.0, 'dn_24': 6.0,
            'up_48': 14.0, 'dn_48': 7.0,
        },
        {
            'time': pd.Timestamp('2024-06-01 01:00'),
            'signal': -1,
            'entry_atr14': np.nan,
            'up_3': 7.0, 'dn_3': 3.0,
            'up_6': 9.0, 'dn_6': 4.0,
            'up_12': 11.0, 'dn_12': 5.0,
            'up_24': 13.0, 'dn_24': 6.0,
            'up_48': 15.0, 'dn_48': 8.0,
        },
        {
            'time': pd.Timestamp('2024-06-01 02:00'),
            'signal': 1,
            'entry_atr14': 4.0,
            'up_3': 4.0, 'dn_3': 8.0,
            'up_6': 5.0, 'dn_6': 10.0,
            'up_12': 6.0, 'dn_12': 12.0,
            'up_24': 7.0, 'dn_24': 14.0,
            'up_48': 8.0, 'dn_48': 16.0,
        },
        {
            'time': pd.Timestamp('2024-06-01 03:00'),
            'signal': -1,
            'entry_atr14': 5.0,
            'up_3': 5.0, 'dn_3': 9.0,
            'up_6': 6.0, 'dn_6': 11.0,
            'up_12': 7.0, 'dn_12': 13.0,
            'up_24': 8.0, 'dn_24': 15.0,
            'up_48': 9.0, 'dn_48': 17.0,
        },
    ])

    out, artifacts = spa.build_conditioning_frame(frame)

    assert pd.isna(out.loc[1, 'atr_bucket'])
    assert out.loc[0, 'atr_bucket'] == 'Q1'
    assert pd.notna(out.loc[2, 'atr_bucket'])
    assert artifacts['atr_edges'][0] == pytest.approx(2.0, abs=1e-9)
    assert artifacts['atr_edges'][-1] == pytest.approx(5.0, abs=1e-9)


def test_build_conditioning_frame_handles_empty_frame_without_crashing():
    frame = pd.DataFrame(columns=[
        'time', 'signal', 'entry_atr14',
        'up_3', 'dn_3', 'up_6', 'dn_6', 'up_12', 'dn_12', 'up_24', 'dn_24', 'up_48', 'dn_48',
    ])

    out, artifacts = spa.build_conditioning_frame(frame)

    assert out.empty
    assert 'atr_bucket' in out.columns
    assert artifacts['atr_edges'].tolist() == []


def test_screen_features_drops_near_constant_axes_before_slicing():
    frame = pd.DataFrame({
        'time': pd.date_range('2024-01-01', periods=120, freq='h'),
        'good_feature': np.linspace(1.0, 3.0, 120),
        'flat_q90_q10': np.ones(120),
        'flat_iqr': np.r_[np.zeros(119), 1.0],
    })
    summary, live = spa.screen_numeric_features(frame, ['good_feature', 'flat_q90_q10', 'flat_iqr'])
    assert 'good_feature' in live
    assert 'flat_q90_q10' not in live
    assert 'flat_iqr' not in live


def test_summarize_slice_groups_counts_effective_support_only():
    frame = pd.DataFrame({
        'bin_id': [0] * 6,
        'signed_ret_12': [1.0, 2.0, np.nan, np.nan, np.nan, np.nan],
        'fav_12': [3.0, 4.0, np.nan, np.nan, np.nan, np.nan],
        'adv_12': [0.5, 0.6, np.nan, np.nan, np.nan, np.nan],
        'adverse_first_1atr': [1, 0, np.nan, np.nan, np.nan, np.nan],
        'favorable_first_1atr': [0, 1, np.nan, np.nan, np.nan, np.nan],
        'dip_then_rally_1atr': [1, 0, np.nan, np.nan, np.nan, np.nan],
        'rally_then_dip_1atr': [0, 1, np.nan, np.nan, np.nan, np.nan],
    })
    out = spa.summarize_slice_groups(frame, 'bin_id')
    assert out.loc[0, 'N'] == 2


def test_build_global_atlas_reports_quantiles_first_passage_and_ordering():
    frame = pd.DataFrame({
        'signed_ret_1': [0.5, -0.5, 1.0, 0.0],
        'signed_ret_12': [2.0, -1.0, 3.0, 0.5],
        'fav_3': [1.5, 0.4, 2.5, 0.8],
        'adv_3': [0.2, 1.2, 0.4, 0.7],
        'fav_12': [3.5, 1.0, 5.0, 1.5],
        'adv_12': [0.5, 2.5, 1.0, 1.2],
        'adverse_first_1atr': [0, 1, 0, 1],
        'favorable_first_1atr': [1, 0, 1, 0],
        'dip_then_rally_1atr': [0, 1, 0, 0],
        'rally_then_dip_1atr': [1, 0, 0, 1],
    })
    atlas = spa.build_global_atlas(frame)
    assert set(atlas.keys()) == {'path_quantiles', 'first_passage', 'ordering'}
    assert (atlas['first_passage']['level_atr'] == 3.0).any()


def test_build_global_atlas_ignores_derived_horizons_and_keeps_partial_raw_first_passage():
    frame = pd.DataFrame({
        'signed_ret_12': [2.0, -1.0, 3.0, 0.5],
        'fav_3': [1.5, 0.4, 2.5, 0.8],
        'adv_3': [0.2, 1.2, 0.4, 0.7],
        'adv_12': [0.5, 2.5, 1.0, 1.2],
        'fav_3_vs_12': [1.0, 1.2, 0.8, 0.9],
        'adverse_first_1atr': [0, 1, 0, 1],
        'favorable_first_1atr': [1, 0, 1, 0],
        'dip_then_rally_1atr': [0, 1, 0, 0],
        'rally_then_dip_1atr': [1, 0, 0, 1],
    })
    atlas = spa.build_global_atlas(frame)
    assert atlas['path_quantiles'].empty
    assert set(atlas['first_passage']['horizon']) == {3, 12}
    assert set(atlas['first_passage']['side']) == {'adverse', 'favorable'}


def test_build_global_atlas_ordering_levels_include_non_adverse_prefixes():
    frame = pd.DataFrame({
        'fav_3': [1.0, 1.2, 1.4],
        'adv_3': [0.2, 0.3, 0.4],
        'fav_12': [2.0, 2.2, 2.4],
        'adv_12': [0.5, 0.6, 0.7],
        'favorable_first_2atr': [1, 0, 1],
        'dip_then_rally_2atr': [0, 1, 0],
        'rally_then_dip_2atr': [1, 0, 1],
    })
    atlas = spa.build_global_atlas(frame)
    assert 2.0 in atlas['ordering']['level_atr'].tolist()


def test_build_numeric_slices_merges_thin_bins_until_support_floor_is_met():
    frame = pd.DataFrame({
        'feature_a': np.linspace(0.0, 11.0, 12),
        'signed_ret_12': [1.0, np.nan, np.nan, 1.1, np.nan, np.nan, 1.2, np.nan, np.nan, 1.3, np.nan, np.nan],
        'fav_12': [2.0, np.nan, np.nan, 2.1, np.nan, np.nan, 2.2, np.nan, np.nan, 2.3, np.nan, np.nan],
        'adv_12': [0.5, np.nan, np.nan, 0.6, np.nan, np.nan, 0.7, np.nan, np.nan, 0.8, np.nan, np.nan],
        'adverse_first_1atr': [1, np.nan, np.nan, 0, np.nan, np.nan, 1, np.nan, np.nan, 0, np.nan, np.nan],
        'favorable_first_1atr': [0, np.nan, np.nan, 1, np.nan, np.nan, 0, np.nan, np.nan, 1, np.nan, np.nan],
        'dip_then_rally_1atr': [1, np.nan, np.nan, 0, np.nan, np.nan, 1, np.nan, np.nan, 0, np.nan, np.nan],
        'rally_then_dip_1atr': [0, np.nan, np.nan, 1, np.nan, np.nan, 0, np.nan, np.nan, 1, np.nan, np.nan],
    })
    slices = spa.build_numeric_slices(frame, feature='feature_a', min_rows=20, min_frac=0.10)
    assert slices['bin_id'].nunique() == 1
    assert slices['N'].tolist() == [4]


def test_build_numeric_slices_handles_derived_feature_without_duplicate_columns():
    frame = pd.DataFrame({
        'fav_3_vs_12': np.linspace(0.5, 1.5, 24),
        'signed_ret_12': np.linspace(-1.0, 1.0, 24),
        'fav_12': np.linspace(2.0, 3.0, 24),
        'adv_12': np.linspace(0.5, 1.5, 24),
        'adverse_first_1atr': [0, 1] * 12,
        'favorable_first_1atr': [1, 0] * 12,
        'dip_then_rally_1atr': [0, 1] * 12,
        'rally_then_dip_1atr': [1, 0] * 12,
    })
    out = spa.build_numeric_slices(frame, feature='fav_3_vs_12', min_rows=5, min_frac=0.10)
    assert not out.empty
    assert out['feature'].unique().tolist() == ['fav_3_vs_12']


def test_build_numeric_slices_runs_across_numeric_feature_subset_including_derived_feature():
    frame = pd.DataFrame({
        'ratio_3': np.linspace(0.8, 1.8, 24),
        'spread_3': np.linspace(0.1, 2.4, 24),
        'ratio_6': np.linspace(0.9, 1.9, 24),
        'spread_6': np.linspace(0.2, 2.5, 24),
        'ratio_12': np.linspace(1.0, 2.0, 24),
        'spread_12': np.linspace(0.3, 2.6, 24),
        'ratio_24': np.linspace(1.1, 2.1, 24),
        'spread_24': np.linspace(0.4, 2.7, 24),
        'ratio_48': np.linspace(1.2, 2.2, 24),
        'spread_48': np.linspace(0.5, 2.8, 24),
        'ratio_3_vs_12': np.linspace(0.7, 1.3, 24),
        'spread_3_vs_12': np.linspace(0.4, 1.0, 24),
        'fav_3_vs_12': np.linspace(0.6, 1.4, 24),
        'ratio_6_vs_24': np.linspace(0.8, 1.2, 24),
        'spread_6_vs_24': np.linspace(0.3, 0.9, 24),
        'ratio_12_vs_48': np.linspace(0.9, 1.1, 24),
        'spread_12_vs_48': np.linspace(0.2, 0.8, 24),
        'signed_ret_12': np.linspace(-1.0, 1.0, 24),
        'fav_12': np.linspace(2.0, 3.0, 24),
        'adv_12': np.linspace(0.5, 1.5, 24),
        'adverse_first_1atr': [0, 1] * 12,
        'favorable_first_1atr': [1, 0] * 12,
        'dip_then_rally_1atr': [0, 1] * 12,
        'rally_then_dip_1atr': [1, 0] * 12,
    })
    subset = ['ratio_3', 'spread_3', 'ratio_3_vs_12', 'spread_3_vs_12', 'fav_3_vs_12']
    outputs = [spa.build_numeric_slices(frame, feature=feature, min_rows=5, min_frac=0.10) for feature in subset]
    assert [out['feature'].iat[0] for out in outputs] == subset


def test_build_categorical_slices_keeps_signal_ratio_bucket_and_atr_bucket():
    frame = pd.DataFrame({
        'signal_label': ['BUY', 'BUY', 'SELL', 'SELL'],
        'ratio_bin_12': ['4-5', '4-5', '3-4', '5+'],
        'atr_bucket': ['Q4', 'Q4', 'Q2', 'Q1'],
        'signed_ret_12': [1.0, 1.2, -0.4, 0.1],
        'fav_12': [3.0, 3.5, 1.0, 1.5],
        'adv_12': [0.5, 0.6, 1.2, 0.8],
        'adverse_first_1atr': [0, 0, 1, 0],
        'favorable_first_1atr': [1, 1, 0, 1],
        'dip_then_rally_1atr': [0, 1, 0, 0],
        'rally_then_dip_1atr': [0, 0, 1, 0],
    })
    out = spa.build_categorical_slices(frame, ['signal_label', 'ratio_bin_12', 'atr_bucket'])
    assert {'signal_label', 'ratio_bin_12', 'atr_bucket'} <= set(out['group_col'])


def test_build_categorical_slices_preserves_null_cohorts():
    frame = pd.DataFrame({
        'signal_label': ['BUY', 'SELL', 'BUY'],
        'atr_bucket': ['Q1', pd.NA, 'Q1'],
        'signed_ret_12': [1.0, 0.2, 1.5],
        'fav_12': [3.0, 1.5, 3.2],
        'adv_12': [0.5, 0.8, 0.4],
        'adverse_first_1atr': [0, 1, 0],
        'favorable_first_1atr': [1, 0, 1],
        'dip_then_rally_1atr': [0, 1, 0],
        'rally_then_dip_1atr': [0, 0, 0],
    })
    out = spa.build_categorical_slices(frame, ['atr_bucket'])
    assert out['atr_bucket'].isna().any()
    assert out.loc[out['atr_bucket'].isna(), 'N'].item() == 1


def test_fit_path_archetypes_merges_tiny_clusters_and_returns_readable_names():
    rows = []
    for idx in range(40):
        rows.append({'signed_ret_1': 0.8, 'signed_ret_12': 2.5, 'fav_12': 3.5, 'adv_12': 0.4, 'fav_1': 1.0, 'adv_1': 0.2})
    for idx in range(40):
        rows.append({'signed_ret_1': -0.8, 'signed_ret_12': 1.8, 'fav_12': 3.0, 'adv_12': 2.0, 'fav_1': 0.2, 'adv_1': 1.4})
    for idx in range(40):
        rows.append({'signed_ret_1': 0.0, 'signed_ret_12': 0.2, 'fav_12': 1.0, 'adv_12': 0.9, 'fav_1': 0.1, 'adv_1': 0.1})
    frame = pd.DataFrame(rows)
    labeled, model = spa.fit_path_archetypes(frame, min_frac=0.10)
    assert labeled['archetype'].nunique() in (3, 4)
    assert set(labeled['archetype']).issubset({'immediate_continuation', 'deep_dip_then_recovery', 'flat_or_noisy_drift', 'failure_or_adverse_continuation'})


def test_fit_path_archetypes_iteratively_merges_multiple_tiny_clusters():
    rows = []
    for idx in range(90):
        rows.append({'signed_ret_1': 0.8, 'signed_ret_12': 2.5, 'fav_12': 3.5, 'adv_12': 0.4, 'fav_1': 1.0, 'adv_1': 0.2})
    for idx in range(5):
        rows.append({'signed_ret_1': -0.8, 'signed_ret_12': 1.8, 'fav_12': 3.0, 'adv_12': 2.0, 'fav_1': 0.2, 'adv_1': 1.4})
    for idx in range(3):
        rows.append({'signed_ret_1': -0.7, 'signed_ret_12': 1.7, 'fav_12': 2.9, 'adv_12': 2.2, 'fav_1': 0.3, 'adv_1': 1.5})
    for idx in range(2):
        rows.append({'signed_ret_1': -0.6, 'signed_ret_12': 1.6, 'fav_12': 2.8, 'adv_12': 2.4, 'fav_1': 0.4, 'adv_1': 1.6})
    frame = pd.DataFrame(rows)
    labeled, model = spa.fit_path_archetypes(frame, min_frac=0.10)
    counts = labeled['cluster_id'].value_counts(normalize=True)
    assert counts.min() >= 0.10


def test_fit_path_archetypes_model_predict_matches_merged_labels():
    frame = pd.DataFrame([
        {'signed_ret_1': 0.9, 'signed_ret_12': 2.7, 'fav_12': 3.8, 'adv_12': 0.3, 'fav_1': 1.1, 'adv_1': 0.2},
        {'signed_ret_1': 0.9, 'signed_ret_12': 2.7, 'fav_12': 3.8, 'adv_12': 0.3, 'fav_1': 1.1, 'adv_1': 0.2},
        {'signed_ret_1': 0.9, 'signed_ret_12': 2.7, 'fav_12': 3.8, 'adv_12': 0.3, 'fav_1': 1.1, 'adv_1': 0.2},
        {'signed_ret_1': -0.9, 'signed_ret_12': 1.4, 'fav_12': 2.6, 'adv_12': 2.3, 'fav_1': 0.2, 'adv_1': 1.5},
        {'signed_ret_1': -0.9, 'signed_ret_12': 1.4, 'fav_12': 2.6, 'adv_12': 2.3, 'fav_1': 0.2, 'adv_1': 1.5},
        {'signed_ret_1': -0.9, 'signed_ret_12': 1.4, 'fav_12': 2.6, 'adv_12': 2.3, 'fav_1': 0.2, 'adv_1': 1.5},
        {'signed_ret_1': 0.1, 'signed_ret_12': 0.2, 'fav_12': 1.0, 'adv_12': 0.9, 'fav_1': 0.1, 'adv_1': 0.1},
        {'signed_ret_1': 0.1, 'signed_ret_12': 0.2, 'fav_12': 1.0, 'adv_12': 0.9, 'fav_1': 0.1, 'adv_1': 0.1},
        {'signed_ret_1': 0.1, 'signed_ret_12': 0.2, 'fav_12': 1.0, 'adv_12': 0.9, 'fav_1': 0.1, 'adv_1': 0.1},
        {'signed_ret_1': 0.1, 'signed_ret_12': 0.2, 'fav_12': 1.0, 'adv_12': 0.9, 'fav_1': 0.1, 'adv_1': 0.1},
    ])

    labeled, artifacts = spa.fit_path_archetypes(frame, min_frac=0.20)
    model = artifacts['model']
    feature_cols = artifacts['feature_cols']
    assert np.array_equal(model.predict(frame[feature_cols].fillna(0.0).to_numpy()), labeled['cluster_id'].to_numpy())


def test_fit_path_archetypes_only_assigns_recovery_label_when_final_metric_is_positive():
    rows = []
    for idx in range(40):
        rows.append({'signed_ret_1': 0.8, 'signed_ret_12': -1.5, 'fav_12': 2.5, 'adv_12': 3.0, 'fav_1': 1.0, 'adv_1': 0.5})
    for idx in range(40):
        rows.append({'signed_ret_1': 0.2, 'signed_ret_12': 1.8, 'fav_12': 3.2, 'adv_12': 0.6, 'fav_1': 0.4, 'adv_1': 0.2})
    for idx in range(40):
        rows.append({'signed_ret_1': -0.1, 'signed_ret_12': 0.1, 'fav_12': 1.2, 'adv_12': 1.0, 'fav_1': 0.2, 'adv_1': 0.2})
    frame = pd.DataFrame(rows)

    labeled, artifacts = spa.fit_path_archetypes(frame, min_frac=0.10)
    cluster_stats = labeled.groupby('cluster_id')['signed_ret_12'].median()
    recovery_clusters = labeled.groupby('cluster_id')['archetype'].first()
    for cluster_id, archetype in recovery_clusters.items():
        if archetype == 'deep_dip_then_recovery':
            assert cluster_stats.loc[cluster_id] > 0
    assert not ((recovery_clusters == 'deep_dip_then_recovery') & (cluster_stats <= 0)).any()


def test_fit_path_archetypes_uses_neutral_label_when_roles_collapse_to_one_cluster():
    frame = pd.DataFrame([
        {'signed_ret_1': 0.6, 'signed_ret_12': 1.8, 'fav_12': 3.0, 'adv_12': 0.4, 'fav_1': 0.8, 'adv_1': 0.2},
        {'signed_ret_1': 0.6, 'signed_ret_12': 1.8, 'fav_12': 3.0, 'adv_12': 0.4, 'fav_1': 0.8, 'adv_1': 0.2},
        {'signed_ret_1': 0.6, 'signed_ret_12': 1.8, 'fav_12': 3.0, 'adv_12': 0.4, 'fav_1': 0.8, 'adv_1': 0.2},
    ])

    labeled, _artifacts = spa.fit_path_archetypes(frame, min_frac=0.10)

    assert labeled['cluster_id'].nunique() == 1
    assert labeled['archetype'].unique().tolist() == ['flat_or_noisy_drift']


def test_fit_path_archetypes_rejects_empty_input():
    frame = pd.DataFrame(columns=['signed_ret_1', 'fav_1', 'adv_1'])
    with pytest.raises(ValueError, match='at least one row'):
        spa.fit_path_archetypes(frame)


def test_fit_path_archetypes_rejects_frames_without_signed_ret_columns():
    frame = pd.DataFrame([
        {'fav_1': 1.0, 'adv_1': 0.2},
        {'fav_1': 0.9, 'adv_1': 0.3},
    ])
    with pytest.raises(ValueError, match='signed_ret_'):
        spa.fit_path_archetypes(frame)


def test_fit_path_archetypes_rejects_frames_without_adv_columns():
    frame = pd.DataFrame([
        {'signed_ret_1': 0.2, 'fav_1': 1.0},
        {'signed_ret_1': 0.3, 'fav_1': 0.9},
    ])
    with pytest.raises(ValueError, match='adv_'):
        spa.fit_path_archetypes(frame)


def test_fit_explanation_tree_rejects_empty_input():
    frame = pd.DataFrame(columns=['ratio_12', 'spread_12', 'ratio_3_vs_12', 'archetype'])
    with pytest.raises(ValueError, match='at least one row'):
        spa.fit_explanation_tree(frame, ['ratio_12', 'spread_12', 'ratio_3_vs_12'])


def test_fit_explanation_tree_rejects_empty_feature_list():
    frame = pd.DataFrame({
        'archetype': ['immediate_continuation', 'deep_dip_then_recovery'],
    })
    with pytest.raises(ValueError, match='feature_cols'):
        spa.fit_explanation_tree(frame, [])


def test_fit_explanation_tree_is_depth_2_and_respects_min_leaf():
    frame = pd.DataFrame({
        'ratio_12': np.linspace(1.0, 5.0, 120),
        'spread_12': np.linspace(2.0, 10.0, 120),
        'ratio_3_vs_12': np.linspace(0.8, 1.2, 120),
        'archetype': ['immediate_continuation'] * 60 + ['deep_dip_then_recovery'] * 60,
    })
    model, text = spa.fit_explanation_tree(frame, ['ratio_12', 'spread_12', 'ratio_3_vs_12'])
    assert model.get_depth() <= 2
    assert model.min_samples_leaf >= 80
    assert 'class:' in text


def test_classify_replication_verdict_uses_sign_and_magnitude_retention():
    verdict = spa.classify_replication_verdict({
        'N_holdout': 40,
        'delta_signed_ret_12_q50_discovery': 0.80,
        'delta_signed_ret_12_q50_holdout': 0.50,
        'delta_fav_hit_3atr_12h_discovery': 12.0,
        'delta_fav_hit_3atr_12h_holdout': 9.0,
        'delta_adv_hit_1atr_3h_discovery': -10.0,
        'delta_adv_hit_1atr_3h_holdout': -6.0,
        'delta_adverse_first_1atr_discovery': -8.0,
        'delta_adverse_first_1atr_holdout': -5.0,
    })
    assert verdict == 'Replicated'


def test_export_tables_writes_expected_csv_files(tmp_path):
    tables = {
        'feature_screen': pd.DataFrame({'feature': ['ratio_12'], 'is_live': [True]}),
        'holdout_verdicts': pd.DataFrame({'artifact_id': ['signal_label=BUY'], 'verdict': ['Replicated']}),
    }
    spa.export_tables(tables, tmp_path)
    assert (tmp_path / 'feature_screen.csv').exists()
    assert (tmp_path / 'holdout_verdicts.csv').exists()


def test_build_conditioning_frame_can_apply_frozen_atr_edges_without_holdout_leakage():
    discovery = pd.DataFrame([
        {
            'time': pd.Timestamp('2024-06-01 00:00'),
            'signal': 1,
            'sample': 'discovery',
            'entry_atr14': 2.0,
            'up_3': 6.0, 'dn_3': 2.0,
            'up_6': 8.0, 'dn_6': 4.0,
            'up_12': 10.0, 'dn_12': 5.0,
            'up_24': 12.0, 'dn_24': 6.0,
            'up_48': 14.0, 'dn_48': 7.0,
        },
        {
            'time': pd.Timestamp('2024-06-01 01:00'),
            'signal': -1,
            'sample': 'discovery',
            'entry_atr14': 4.0,
            'up_3': 4.0, 'dn_3': 8.0,
            'up_6': 5.0, 'dn_6': 10.0,
            'up_12': 6.0, 'dn_12': 12.0,
            'up_24': 7.0, 'dn_24': 14.0,
            'up_48': 8.0, 'dn_48': 16.0,
        },
    ])
    holdout = pd.DataFrame([
        {
            'time': pd.Timestamp('2025-01-02 00:00'),
            'signal': 1,
            'sample': 'holdout',
            'entry_atr14': 100.0,
            'up_3': 7.0, 'dn_3': 1.5,
            'up_6': 9.0, 'dn_6': 3.0,
            'up_12': 11.0, 'dn_12': 4.0,
            'up_24': 13.0, 'dn_24': 5.0,
            'up_48': 15.0, 'dn_48': 6.0,
        },
    ])

    discovery_out, artifacts = spa.build_conditioning_frame(discovery)
    combined_out, reused = spa.build_conditioning_frame(
        pd.concat([discovery, holdout], ignore_index=True),
        atr_edges=artifacts['atr_edges'],
    )

    assert combined_out.loc[combined_out['sample'] == 'discovery', 'atr_bucket'].tolist() == discovery_out['atr_bucket'].tolist()
    assert reused['atr_edges'].tolist() == artifacts['atr_edges'].tolist()
    assert pd.isna(combined_out.loc[combined_out['sample'] == 'holdout', 'atr_bucket']).item()


def test_build_holdout_verdicts_keeps_discovery_archetypes_with_zero_holdout_support():
    discovery = pd.DataFrame([
        {
            'signal_label': 'BUY',
            'ratio_bin_12': '2-3',
            'atr_bucket': 'Q1',
            'signed_ret_12': 2.0,
            'fav_12': 3.5,
            'adv_3': 0.2,
            'adverse_first_1atr': 0.0,
            'archetype': 'immediate_continuation',
        },
        {
            'signal_label': 'SELL',
            'ratio_bin_12': '3-4',
            'atr_bucket': 'Q2',
            'signed_ret_12': 0.4,
            'fav_12': 1.2,
            'adv_3': 1.5,
            'adverse_first_1atr': 1.0,
            'archetype': 'deep_dip_then_recovery',
        },
    ])
    holdout = discovery.iloc[0:0].copy()

    out = spa.build_holdout_verdicts(
        discovery,
        holdout,
        pd.DataFrame(columns=['feature', 'bin_id', 'lower_edge', 'upper_edge']),
        archetype_artifacts={'feature_cols': ['signed_ret_12'], 'model': object(), 'name_map': {}},
    )

    archetypes = out[out['artifact_id'].str.startswith('archetype:')].set_index('artifact_id')
    assert set(archetypes.index) == {'archetype:immediate_continuation', 'archetype:deep_dip_then_recovery'}
    assert archetypes['N_holdout'].tolist() == [0, 0]
    assert set(archetypes['verdict']) == {'Exploratory'}


def test_print_report_sections_smoke(capsys):
    tables = {
        'split_summary': pd.DataFrame({'sample': ['discovery', 'holdout'], 'N': [100, 40]}),
        'feature_screen': pd.DataFrame({'feature': ['ratio_12'], 'is_live': [True]}),
        'path_quantiles': pd.DataFrame({'horizon': [3], 'signed_ret_q50': [0.5]}),
        'first_passage': pd.DataFrame({'side': ['adverse'], 'level_atr': [1.0], 'hit_pct': [10.0]}),
        'ordering': pd.DataFrame({'level_atr': [1.0], 'adverse_first_pct': [40.0]}),
        'archetype_summary': pd.DataFrame({'archetype': ['immediate_continuation'], 'N': [12]}),
        'holdout_verdicts': pd.DataFrame({'artifact_id': ['signal_label=BUY'], 'verdict': ['Replicated']}),
        'execution_implications': pd.DataFrame({'recommendation': ['market and pullback both justified']}),
    }
    spa.print_report_sections(tables)
    out = capsys.readouterr().out
    assert 'Signal Path Atlas — Discovery/Holdout Split' in out
    assert 'Feature Variance Screen' in out
    assert 'Global Path Quantiles' in out
    assert 'First Passage Atlas' in out
    assert 'Ordering Atlas' in out
    assert 'Archetype Summary' in out
    assert 'Holdout Replication Verdicts' in out
    assert 'Execution Implications' in out


def test_main_cli_smoke_runs_loader_argparse_and_export(monkeypatch, tmp_path, capsys):
    ohlc = pd.DataFrame({
        'time': pd.date_range('2024-12-31 00:00', periods=40, freq='h'),
        'open': np.linspace(100.0, 139.0, 40),
        'high': np.linspace(101.0, 140.0, 40),
        'low': np.linspace(99.0, 138.0, 40),
        'close': np.linspace(100.5, 139.5, 40),
        'atr14': [2.0] * 40,
    })
    signals = pd.DataFrame([
        {
            'time': pd.Timestamp('2024-12-31 00:00'),
            'signal': 1,
            'entry_close': 100.5,
            'entry_atr14': 2.0,
            'up_3': 6.0, 'dn_3': 2.0,
            'up_6': 8.0, 'dn_6': 3.0,
            'up_12': 10.0, 'dn_12': 4.0,
            'up_24': 12.0, 'dn_24': 5.0,
            'up_48': 14.0, 'dn_48': 6.0,
        },
        {
            'time': pd.Timestamp('2024-12-31 01:00'),
            'signal': -1,
            'entry_close': 101.5,
            'entry_atr14': 2.0,
            'up_3': 3.0, 'dn_3': 7.0,
            'up_6': 4.0, 'dn_6': 9.0,
            'up_12': 5.0, 'dn_12': 11.0,
            'up_24': 6.0, 'dn_24': 13.0,
            'up_48': 7.0, 'dn_48': 15.0,
        },
        {
            'time': pd.Timestamp('2025-01-01 00:00'),
            'signal': 1,
            'entry_close': 124.5,
            'entry_atr14': 2.0,
            'up_3': 7.0, 'dn_3': 2.0,
            'up_6': 9.0, 'dn_6': 3.0,
            'up_12': 11.0, 'dn_12': 4.0,
            'up_24': 13.0, 'dn_24': 5.0,
            'up_48': 15.0, 'dn_48': 6.0,
        },
        {
            'time': pd.Timestamp('2025-01-01 01:00'),
            'signal': -1,
            'entry_close': 125.5,
            'entry_atr14': 2.0,
            'up_3': 2.0, 'dn_3': 6.0,
            'up_6': 3.0, 'dn_6': 8.0,
            'up_12': 4.0, 'dn_12': 10.0,
            'up_24': 5.0, 'dn_24': 12.0,
            'up_48': 6.0, 'dn_48': 14.0,
        },
    ])
    seen = {}

    def fake_load_atlas_inputs(test_only=False):
        seen['test_only'] = test_only
        return signals.copy(), ohlc.copy()

    monkeypatch.setattr(spa, 'load_atlas_inputs', fake_load_atlas_inputs)
    monkeypatch.setattr(sys, 'argv', ['signal_path_atlas.py', '--test-only', '--export-dir', str(tmp_path)])

    spa.main()

    out = capsys.readouterr().out
    assert seen['test_only'] is True
    assert 'Signal Path Atlas — Discovery/Holdout Split' in out
    assert 'Global Path Quantiles' in out
    assert 'Ordering Atlas' in out
    assert 'Archetype Summary' in out
    assert (tmp_path / 'split_summary.csv').exists()
    assert (tmp_path / 'path_quantiles.csv').exists()
    assert (tmp_path / 'first_passage.csv').exists()
    assert (tmp_path / 'ordering.csv').exists()
    assert (tmp_path / 'holdout_verdicts.csv').exists()
    assert (tmp_path / 'archetype_summary.csv').exists()


def test_build_holdout_verdicts_numeric_slice_shared_boundary_counts_holdout_once():
    discovery = pd.DataFrame({
        'feature_a': [1.0] * 8 + [2.0] * 8 + [3.0] * 8 + [4.0] * 8,
        'signal_label': ['BUY'] * 32,
        'ratio_bin_12': ['2-3'] * 32,
        'atr_bucket': ['Q1'] * 32,
        'signed_ret_12': np.linspace(0.1, 3.2, 32),
        'fav_12': np.linspace(1.0, 4.1, 32),
        'adv_12': np.linspace(0.5, 1.8, 32),
        'adv_3': np.linspace(0.2, 1.5, 32),
        'adverse_first_1atr': [0.0, 1.0] * 16,
        'archetype': ['immediate_continuation'] * 32,
    })
    holdout = pd.DataFrame({
        'feature_a': [2.0],
        'signal_label': ['BUY'],
        'ratio_bin_12': ['2-3'],
        'atr_bucket': ['Q1'],
        'signed_ret_12': [1.5],
        'fav_12': [2.5],
        'adv_12': [1.1],
        'adv_3': [0.8],
        'adverse_first_1atr': [0.0],
        'archetype': ['immediate_continuation'],
    })
    numeric_slices = spa.build_numeric_slices(discovery, 'feature_a', min_rows=1, min_frac=0.0)

    class DummyModel:
        def predict(self, X):
            return np.zeros(len(X), dtype=int)

    verdicts = spa.build_holdout_verdicts(
        discovery,
        holdout,
        numeric_slices,
        archetype_artifacts={'feature_cols': ['signed_ret_12'], 'model': DummyModel(), 'name_map': {0: 'immediate_continuation'}},
    )

    feature_rows = verdicts[verdicts['artifact_id'].str.startswith('feature_a:bin_')]
    assert feature_rows['N_holdout'].sum() == 1
