import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from API import export_entry_path_v1_quantile_signals as exporter


def _write_seed_dir(tmp_path: Path, *, split: str = 'test', winner_rule: str = 'lb_gt_m') -> Path:
    seed_dir = tmp_path / 'seed_123'
    seed_dir.mkdir(parents=True, exist_ok=True)

    rule_payload = {
        'winner': {
            'candidate': winner_rule,
            'rule': winner_rule,
            'm': -1.5,
            'w': 10.0,
        },
        'baseline_threshold': 0.2,
        'correction': 0.5,
    }
    (seed_dir / 'entry_path_v1_quantile_filter_selected_rule.json').write_text(
        json.dumps(rule_payload, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    frame = pd.DataFrame(
        [
            {
                'time': '2025.01.01 00:00',
                'signal': 1,
                'pred_ret_24_dir_atr': 0.40,
                'pred_ret_24_q10': 0.80,
                'pred_ret_24_q90': 2.20,
            },
            {
                'time': '2025.01.01 01:00',
                'signal': -1,
                'pred_ret_24_dir_atr': 0.35,
                'pred_ret_24_q10': -1.10,
                'pred_ret_24_q90': 1.10,
            },
            {
                'time': '2025.01.01 02:00',
                'signal': 1,
                'pred_ret_24_dir_atr': 0.10,
                'pred_ret_24_q10': 1.50,
                'pred_ret_24_q90': 2.50,
            },
            {
                'time': '2025.01.01 03:00',
                'signal': 0,
                'pred_ret_24_dir_atr': 0.50,
                'pred_ret_24_q10': 2.00,
                'pred_ret_24_q90': 3.00,
            },
        ]
    )
    frame.to_csv(seed_dir / f'entry_path_v1_quantile_{split}_predictions.csv', sep=';', index=False)
    return seed_dir


def test_export_signals_writes_full_series_from_frozen_rule(tmp_path):
    seed_dir = _write_seed_dir(tmp_path, split='test')
    output_path = tmp_path / 'ml_signals.csv'

    exporter.export_signals(seed_dir=seed_dir, split='test', output_path=output_path)

    out = pd.read_csv(output_path, sep=';')

    assert list(out.columns) == ['time', 'signal']
    assert out['time'].tolist() == [
        '2025.01.01 00:00',
        '2025.01.01 01:00',
        '2025.01.01 02:00',
        '2025.01.01 03:00',
    ]
    assert out['signal'].tolist() == [1, 0, 0, 0]


def test_export_signals_supports_baseline_rule(tmp_path):
    seed_dir = _write_seed_dir(tmp_path, split='validation', winner_rule='baseline')
    output_path = tmp_path / 'ml_signals_validation.csv'

    exporter.export_signals(seed_dir=seed_dir, split='validation', output_path=output_path)

    out = pd.read_csv(output_path, sep=';')

    assert out['signal'].tolist() == [1, -1, 0, 0]


def test_export_signals_rejects_unknown_rule(tmp_path):
    seed_dir = _write_seed_dir(tmp_path, split='test', winner_rule='mystery_rule')
    output_path = tmp_path / 'ml_signals.csv'

    try:
        exporter.export_signals(seed_dir=seed_dir, split='test', output_path=output_path)
    except ValueError as exc:
        assert 'Unknown rule' in str(exc)
    else:
        raise AssertionError('Expected ValueError for unknown frozen rule')


def test_export_signals_copy_to_mt4_writes_both_targets(tmp_path):
    seed_dir = _write_seed_dir(tmp_path, split='test')
    output_path = tmp_path / 'ml_signals.csv'
    tester_path = tmp_path / 'tester' / 'files' / 'ml_signals.csv'
    runtime_path = tmp_path / 'MQL4' / 'Files' / 'ml_signals.csv'

    exporter.MT4_TESTER_SIGNALS = tester_path
    exporter.MT4_RUNTIME_SIGNALS = runtime_path

    exporter.export_signals(
        seed_dir=seed_dir,
        split='test',
        output_path=output_path,
        copy_to_mt4=True,
    )

    out = output_path.read_text(encoding='utf-8')
    assert tester_path.read_text(encoding='utf-8') == out
    assert runtime_path.read_text(encoding='utf-8') == out


def test_export_signals_deduplicates_time_with_keep_last(tmp_path):
    seed_dir = tmp_path / 'seed_123'
    seed_dir.mkdir(parents=True, exist_ok=True)

    rule_payload = {
        'winner': {
            'candidate': 'lb_gt_m',
            'rule': 'lb_gt_m',
            'm': -1.5,
            'w': 10.0,
        },
        'baseline_threshold': 0.2,
        'correction': 0.5,
    }
    (seed_dir / 'entry_path_v1_quantile_filter_selected_rule.json').write_text(
        json.dumps(rule_payload, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    pd.DataFrame(
        [
            {
                'time': '2025.01.01 00:00',
                'signal': 1,
                'pred_ret_24_dir_atr': 0.4,
                'pred_ret_24_q10': 0.8,
                'pred_ret_24_q90': 2.0,
            },
            {
                'time': '2025.01.01 00:00',
                'signal': 0,
                'pred_ret_24_dir_atr': -1.0,
                'pred_ret_24_q10': -5.0,
                'pred_ret_24_q90': -1.0,
            },
            {
                'time': '2025.01.01 01:00',
                'signal': -1,
                'pred_ret_24_dir_atr': 0.4,
                'pred_ret_24_q10': 0.5,
                'pred_ret_24_q90': 1.0,
            },
        ]
    ).to_csv(seed_dir / 'entry_path_v1_quantile_test_predictions.csv', sep=';', index=False)

    output_path = tmp_path / 'ml_signals.csv'
    exporter.export_signals(seed_dir=seed_dir, split='test', output_path=output_path)

    out = pd.read_csv(output_path, sep=';')
    assert out['time'].tolist() == ['2025.01.01 00:00', '2025.01.01 01:00']
    assert out['signal'].tolist() == [0, -1]
