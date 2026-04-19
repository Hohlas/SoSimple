import pandas as pd

from ML.feature_importance_diagnostics import build_grouped_features, load_sample, run_diagnostics


def _fractal(seed: int) -> str:
    values = [
        1_700_000_000 + seed,
        100.0 + seed,
        1 if seed % 2 == 0 else -1,
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
    ]
    return ':'.join(str(value) for value in values)


def _frame(rows: int = 12, seq_len: int = 5) -> pd.DataFrame:
    data = {
        'time': [f'2024.01.01 {hour:02d}:00' for hour in range(rows)],
        'ATR': [1.0 + i * 0.01 for i in range(rows)],
        'session_hour': [i % 24 for i in range(rows)],
        'weekday': [i % 5 for i in range(rows)],
        'trail_24_pnl_atr_x8': [float(i % 4) - 1.0 for i in range(rows)],
    }
    for fractal_idx in range(seq_len):
        data[f'fractal{fractal_idx}'] = [_fractal(i + fractal_idx) for i in range(rows)]
    return pd.DataFrame(data)


def test_build_grouped_features_contains_expected_groups():
    frame = _frame(seq_len=5)

    features, groups = build_grouped_features(frame, seq_len=5)

    assert 'geometry' in groups
    assert 'path_long' in groups
    assert 'row_context' in groups
    assert 'front_mean_w5' in features.columns
    assert 'up_24_last_w5' in features.columns
    assert 'row_hour_sin' in features.columns


def test_load_sample_keeps_tail_rows(tmp_path):
    path = tmp_path / 'sample.csv'
    _frame(rows=12, seq_len=5).to_csv(path, sep=';', index=False)

    sample = load_sample(path, target='trail_24_pnl_atr_x8', seq_len=5, max_rows=4, chunksize=3)

    assert len(sample) == 4
    assert sample.iloc[0]['time'] == '2024.01.01 08:00'


def test_run_diagnostics_writes_outputs(tmp_path):
    train = tmp_path / 'train.csv'
    validation = tmp_path / 'validation.csv'
    _frame(rows=20, seq_len=5).to_csv(train, sep=';', index=False)
    _frame(rows=16, seq_len=5).to_csv(validation, sep=';', index=False)

    result = run_diagnostics(
        train_path=train,
        validation_path=validation,
        target='trail_24_pnl_atr_x8',
        output_dir=tmp_path / 'out',
        seq_len=5,
        max_train_rows=20,
        max_validation_rows=16,
        chunksize=10,
        n_estimators=5,
        seed=1,
    )

    assert result.feature_count > 0
    assert (tmp_path / 'out' / 'group_importance.csv').exists()
    assert (tmp_path / 'out' / 'feature_importance.csv').exists()
    assert (tmp_path / 'out' / 'summary.json').exists()
    assert (tmp_path / 'out' / 'report.md').exists()
