import pandas as pd

from ML.benchmark_take_skip_lib_pic_selection import (
    build_candidate_table,
    merge_predictions_with_lib_pic_features,
    run_selection_benchmark_from_frames,
)


def _fractal(seed: int, *, direction: int = 1, edge: float = 1.0) -> str:
    fav = max(edge, 0.0)
    adv = max(-edge, 0.0)
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


def _source_frame(edges: list[float]) -> pd.DataFrame:
    data = {
        'time': [f'2024.01.{idx + 1:02d} 00:00' for idx in range(len(edges))],
        'signal': [1] * len(edges),
        'ATR': [1.0] * len(edges),
    }
    for fractal_idx in range(5):
        data[f'fractal{fractal_idx}'] = [
            _fractal(row_idx + fractal_idx, edge=edge)
            for row_idx, edge in enumerate(edges)
        ]
    return pd.DataFrame(data)


def _prediction_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            'time': ['2024.01.01 00:00', '2024.01.02 00:00', '2024.01.03 00:00', '2024.01.04 00:00'],
            'signal': [1, 1, 1, 1],
            'pred_take_24_x8': [0.90, 0.88, 0.86, 0.84],
            'true_trail_24_pnl_atr_x8': [2.0, -1.0, 1.5, -1.0],
        }
    )


def test_merge_predictions_with_lib_pic_features_preserves_prediction_order():
    predictions = _prediction_frame()
    source = _source_frame([4.0, -2.0, 3.0, -1.0])

    merged = merge_predictions_with_lib_pic_features(
        predictions=predictions,
        source=source,
        feature_profile='baseline_clean_path',
        seq_len=5,
    )

    assert merged['time'].tolist() == predictions['time'].tolist()
    assert 'pic_path_edge24_mean_w5' in merged.columns
    assert merged.loc[0, 'pic_path_edge24_mean_w5'] > 0
    assert merged.loc[1, 'pic_path_edge24_mean_w5'] < 0


def test_build_candidate_table_applies_validation_feature_quantile_filter():
    frame = _prediction_frame()
    frame['pic_path_edge24_mean_w5'] = [4.0, -2.0, 3.0, -1.0]

    table = build_candidate_table(
        frame,
        pairings=[('take_24_x8', 'true_trail_24_pnl_atr_x8')],
        score_thresholds=(0.80,),
        top_k_values=(),
        feature_columns=('pic_path_edge24_mean_w5',),
        feature_quantiles=(0.50,),
    )

    filtered = table.loc[table['feature_column'] == 'pic_path_edge24_mean_w5'].iloc[0]
    baseline = table.loc[table['feature_filter'] == 'none'].iloc[0]
    assert filtered['trades'] == 2
    assert filtered['pf'] == float('inf')
    assert filtered['pf'] > baseline['pf']


def test_run_selection_benchmark_freezes_validation_feature_threshold_to_test():
    validation = _prediction_frame()
    validation['pic_path_edge24_mean_w5'] = [4.0, -2.0, 3.0, -1.0]
    test = _prediction_frame()
    test['pic_path_edge24_mean_w5'] = [10.0, -10.0, 9.0, -9.0]

    result = run_selection_benchmark_from_frames(
        validation=validation,
        test=test,
        pairings=[('take_24_x8', 'true_trail_24_pnl_atr_x8')],
        score_thresholds=(0.80,),
        top_k_values=(),
        feature_columns=('pic_path_edge24_mean_w5',),
        feature_quantiles=(0.50,),
        min_pf=1.0,
        min_trades_per_year=0.1,
    )

    winner = result['validation_winner']
    test_result = result['test_result']
    assert winner is not None
    assert winner['feature_column'] == 'pic_path_edge24_mean_w5'
    assert test_result['feature_threshold'] == winner['feature_threshold']
    assert test_result['trades'] == 2


def test_run_selection_benchmark_reports_feature_frequency_winner():
    validation = _prediction_frame()
    validation['pic_path_edge24_mean_w5'] = [4.0, -2.0, 3.0, -1.0]
    test = _prediction_frame()
    test['pic_path_edge24_mean_w5'] = [10.0, -10.0, 9.0, -9.0]

    result = run_selection_benchmark_from_frames(
        validation=validation,
        test=test,
        pairings=[('take_24_x8', 'true_trail_24_pnl_atr_x8')],
        score_thresholds=(0.89,),
        top_k_values=(1.0,),
        feature_columns=('pic_path_edge24_mean_w5',),
        feature_quantiles=(0.50,),
        min_pf=1.0,
        min_trades_per_year=0.1,
    )

    feature_winner = result['feature_frequency_first']['validation_winner']
    assert feature_winner is not None
    assert feature_winner['feature_column'] == 'pic_path_edge24_mean_w5'
    assert result['feature_frequency_first']['test_result']['trades'] == 2


def test_run_selection_benchmark_serializes_no_feature_winner_as_null():
    validation = _prediction_frame()
    validation['pic_path_edge24_mean_w5'] = [4.0, -2.0, 3.0, -1.0]
    test = validation.copy()

    result = run_selection_benchmark_from_frames(
        validation=validation,
        test=test,
        pairings=[('take_24_x8', 'true_trail_24_pnl_atr_x8')],
        score_thresholds=(0.89,),
        top_k_values=(),
        feature_columns=(),
        feature_quantiles=(0.50,),
        min_pf=1.0,
        min_trades_per_year=0.1,
    )

    assert result['quality_first']['validation_winner']['feature_column'] is None
    assert result['quality_first']['validation_winner']['feature_threshold'] is None
    assert result['quality_first']['validation_winner']['pf'] == 'inf'
