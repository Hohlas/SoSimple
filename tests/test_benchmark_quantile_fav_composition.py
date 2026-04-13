import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from API import export_entry_path_v1_quantile_signals as exporter
from ML import benchmark_quantile_fav_composition as composition
from ML.benchmark_entry_path_v1_quantile_filter import apply_conformal_correction


def test_compose_intersection_mask_matches_logical_and():
    mask_q = pd.Series([True, False, True, True, False, False, True, False])
    mask_f = pd.Series([True, True, False, True, False, True, False, False])

    out = composition.compose_intersection_mask(mask_q, mask_f)

    assert out.tolist() == (mask_q & mask_f).tolist()


def test_compute_mode_masks_excludes_flat_rows_from_all_modes():
    frame = pd.DataFrame(
        [
            {'signal': 1, 'baseline_score': 0.9, 'fav_3_vs_12': 0.50, 'lb': 1.2, 'width': 0.4},
            {'signal': 0, 'baseline_score': 0.9, 'fav_3_vs_12': 0.40, 'lb': 1.4, 'width': 0.3},
            {'signal': -1, 'baseline_score': 0.8, 'fav_3_vs_12': 0.90, 'lb': 1.1, 'width': 0.5},
            {'signal': 0, 'baseline_score': 0.2, 'fav_3_vs_12': 0.10, 'lb': 0.8, 'width': 0.6},
        ]
    )

    masks = composition.compute_mode_masks(
        frame=frame,
        baseline_threshold=0.3,
        fav_threshold=0.653,
        rule='lb_gt_m',
        m=1.0,
        w=10.0,
    )

    for mask in masks.values():
        assert not mask.loc[frame['signal'] == 0].any()

    assert masks['baseline'].tolist() == [True, False, True, False]
    assert masks['quantile_only'].tolist() == [True, False, True, False]
    assert masks['fav_only'].tolist() == [True, False, False, False]
    assert masks['composition'].tolist() == [True, False, False, False]


def test_materialize_export_frame_matches_production_dedup_policy():
    raw_frame = pd.DataFrame(
        [
            {
                'time': '2025.01.01 00:00',
                'signal': 1,
                'pred_ret_24_q10': 1.1,
                'pred_ret_24_q90': 2.0,
            },
            {
                'time': '2025.01.01 00:00',
                'signal': -1,
                'pred_ret_24_q10': 1.0,
                'pred_ret_24_q90': 1.8,
            },
            {
                'time': '2025.01.01 01:00',
                'signal': 0,
                'pred_ret_24_q10': -0.5,
                'pred_ret_24_q90': 0.5,
            },
            {
                'time': '2025.01.01 02:00',
                'signal': -1,
                'pred_ret_24_q10': 0.7,
                'pred_ret_24_q90': 0.9,
            },
        ]
    )
    baseline_frame = pd.DataFrame(
        [
            {'time': '2025.01.01 00:00', 'signal': 1, 'pred_ret_24_dir_atr': 0.9},
            {'time': '2025.01.01 00:00', 'signal': -1, 'pred_ret_24_dir_atr': 0.1},
            {'time': '2025.01.01 01:00', 'signal': 0, 'pred_ret_24_dir_atr': 0.9},
            {'time': '2025.01.01 02:00', 'signal': -1, 'pred_ret_24_dir_atr': 0.8},
        ]
    )
    rule_payload = {
        'correction': 0.0,
        'baseline_threshold': 0.3,
        'winner': {'rule': 'lb_gt_m', 'm': 0.5, 'w': 10.0},
    }

    selected_mask = exporter.apply_production_rule(raw_frame, baseline_frame, rule_payload)
    out = composition.materialize_export_frame(raw_frame, selected_mask)

    assert out['time'].tolist() == ['2025.01.01 00:00', '2025.01.01 01:00', '2025.01.01 02:00']
    assert out['signal'].tolist() == [1, 0, -1]


def test_compute_mode_masks_matches_manual_expectations_on_six_rows():
    frame = pd.DataFrame(
        [
            {
                'signal': 1,
                'baseline_score': 0.90,
                'pred_ret_24_dir_atr': 2.0,
                'pred_ret_24_q10': 1.2,
                'pred_ret_24_q90': 2.0,
                'fav_3_vs_12': 0.50,
            },
            {
                'signal': -1,
                'baseline_score': 0.85,
                'pred_ret_24_dir_atr': 1.5,
                'pred_ret_24_q10': 0.2,
                'pred_ret_24_q90': 1.0,
                'fav_3_vs_12': 0.50,
            },
            {
                'signal': 1,
                'baseline_score': 0.20,
                'pred_ret_24_dir_atr': -1.0,
                'pred_ret_24_q10': 2.0,
                'pred_ret_24_q90': 3.0,
                'fav_3_vs_12': 0.20,
            },
            {
                'signal': -1,
                'baseline_score': 0.80,
                'pred_ret_24_dir_atr': -0.5,
                'pred_ret_24_q10': 1.5,
                'pred_ret_24_q90': 1.9,
                'fav_3_vs_12': 0.80,
            },
            {
                'signal': 0,
                'baseline_score': 0.95,
                'pred_ret_24_dir_atr': 0.0,
                'pred_ret_24_q10': 3.0,
                'pred_ret_24_q90': 4.0,
                'fav_3_vs_12': 0.10,
            },
            {
                'signal': 1,
                'baseline_score': 0.75,
                'pred_ret_24_dir_atr': 0.7,
                'pred_ret_24_q10': 1.1,
                'pred_ret_24_q90': 1.8,
                'fav_3_vs_12': 0.30,
            },
        ]
    )
    frame = apply_conformal_correction(frame, correction=0.0)

    masks = composition.compute_mode_masks(
        frame=frame,
        baseline_threshold=0.3,
        fav_threshold=0.653,
        rule='lb_gt_m',
        m=1.0,
        w=10.0,
    )

    assert masks['baseline'].tolist() == [True, True, False, True, False, True]
    assert masks['quantile_only'].tolist() == [True, False, False, True, False, True]
    assert masks['fav_only'].tolist() == [True, True, False, False, False, True]
    assert masks['composition'].tolist() == [True, False, False, False, False, True]


def test_attach_fav_by_active_row_order_preserves_full_row_count_and_order():
    quantile = pd.DataFrame(
        [
            {'time': '2025.01.01 00:00', 'signal': 0},
            {'time': '2025.01.01 01:00', 'signal': 1},
            {'time': '2025.01.01 01:00', 'signal': 1},
            {'time': '2025.01.01 02:00', 'signal': -1},
            {'time': '2025.01.01 03:00', 'signal': 0},
        ]
    )
    updn_active = pd.DataFrame(
        [
            {'time': '2025.01.01 01:00', 'signal': 1, 'fav_3_vs_12': 0.30},
            {'time': '2025.01.01 01:00', 'signal': 1, 'fav_3_vs_12': 0.40},
            {'time': '2025.01.01 02:00', 'signal': -1, 'fav_3_vs_12': 0.50},
        ]
    )

    out = composition.attach_fav_by_active_row_order(quantile, updn_active)

    assert len(out) == len(quantile)
    assert out['signal'].tolist() == quantile['signal'].tolist()
    assert out['fav_3_vs_12'].isna().tolist() == [True, False, False, False, True]
    assert out.loc[out['signal'] != 0, 'fav_3_vs_12'].tolist() == [0.30, 0.40, 0.50]
