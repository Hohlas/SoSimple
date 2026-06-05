import pandas as pd

from ML.feature_bank_comparison_diagnostics import build_variant_features, run_comparison


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


def _frame(rows: int = 18, seq_len: int = 5) -> pd.DataFrame:
    data = {
        'time': [f'2024.01.01 {hour % 24:02d}:00' for hour in range(rows)],
        'ATR': [1.0 + i * 0.01 for i in range(rows)],
        'session_hour': [i % 24 for i in range(rows)],
        'weekday': [i % 5 for i in range(rows)],
        'trail_24_pnl_atr_x8': [float(i % 4) - 1.0 for i in range(rows)],
    }
    for fractal_idx in range(seq_len):
        data[f'fractal{fractal_idx}'] = [_fractal(i + fractal_idx) for i in range(rows)]
    return pd.DataFrame(data)


def test_build_variant_features_adds_expected_banks():
    frame = _frame(seq_len=5)

    baseline = build_variant_features(frame, variant='baseline_full', seq_len=5)
    clean = build_variant_features(frame, variant='baseline_clean', seq_len=5)
    full_path = build_variant_features(frame, variant='baseline_full_path', seq_len=5)
    clean_path = build_variant_features(frame, variant='baseline_clean_path', seq_len=5)
    clean_both = build_variant_features(frame, variant='baseline_clean_geometry_path', seq_len=5)

    assert len(clean.columns) < len(baseline.columns)
    assert len(full_path.columns) > len(baseline.columns)
    assert len(clean_path.columns) > len(clean.columns)
    assert len(clean_both.columns) > len(clean_path.columns)
    assert any(column.startswith('pic_geom_') for column in clean_both.columns)
    assert any(column.startswith('pic_path_') for column in clean_path.columns)
    assert not any(column.startswith('direction_') for column in clean.columns)
    assert not any(column.startswith('up_') for column in clean.columns)


def test_run_comparison_writes_outputs(tmp_path):
    train = tmp_path / 'train.csv'
    validation = tmp_path / 'validation.csv'
    _frame(rows=24, seq_len=5).to_csv(train, sep=';', index=False)
    _frame(rows=20, seq_len=5).to_csv(validation, sep=';', index=False)

    results = run_comparison(
        train_path=train,
        validation_path=validation,
        target='trail_24_pnl_atr_x8',
        output_dir=tmp_path / 'out',
        seq_len=5,
        max_train_rows=24,
        max_validation_rows=20,
        chunksize=10,
        n_estimators=5,
        seed=1,
        variants=('baseline_full', 'baseline_clean'),
    )

    assert len(results) == 2
    assert (tmp_path / 'out' / 'summary.csv').exists()
    assert (tmp_path / 'out' / 'summary.json').exists()
    assert (tmp_path / 'out' / 'report.md').exists()
