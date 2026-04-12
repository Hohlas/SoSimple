import pandas as pd

from ML import entry_path_quantile_task as eqt


def test_attach_quantile_context_columns_adds_atr_baseline_and_year():
    export = pd.DataFrame({
        'time': ['2024.01.01 00:00'],
        'signal': [1],
        'pred_ret_24_point': [0.5],
        'pred_ret_24_q10': [0.1],
        'pred_ret_24_q90': [0.9],
    })
    source = pd.DataFrame({
        'time': ['2024.01.01 00:00'],
        'ATR': [1.8],
    })

    out = eqt.attach_quantile_context_columns(export, source)

    assert out['ATR'].tolist() == [1.8]
    assert out['baseline_score'].tolist() == [0.5]
    assert out['year'].tolist() == [2024]


def test_build_quantile_report_mentions_val_score_and_coverage():
    frame = pd.DataFrame({
        'time': ['2024.01.01 00:00', '2024.01.01 01:00'],
        'signal': [1, -1],
        'pred_ret_24_point': [0.5, -0.2],
        'pred_ret_24_q10': [0.1, -0.7],
        'pred_ret_24_q90': [0.9, 0.2],
        'true_ret_24_dir_atr': [0.4, -0.3],
    })

    text = eqt.build_entry_path_quantile_report_markdown(
        frame,
        model_name='transformer',
        artifact_name='demo.csv',
    )

    assert 'ret_pearson_r' in text
    assert 'interval_coverage' in text
    assert 'median_interval_width' in text
