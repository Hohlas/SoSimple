import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from API import export_take_skip_trailing_stop_v2_signals as exporter


def _write_prediction_csv(tmp_path: Path) -> Path:
    path = tmp_path / 'predictions.csv'
    pd.DataFrame(
        [
            {'time': '2025.01.01 00:00', 'signal': 1, 'pred_take_24_x8': 0.95},
            {'time': '2025.01.01 01:00', 'signal': -1, 'pred_take_24_x8': 0.72},
            {'time': '2025.01.01 02:00', 'signal': 1, 'pred_take_24_x8': 0.66},
            {'time': '2025.01.01 03:00', 'signal': 0, 'pred_take_24_x8': 0.99},
            {'time': '2025.01.01 04:00', 'signal': -1, 'pred_take_24_x8': 0.31},
        ]
    ).to_csv(path, sep=';', index=False)
    return path


def _write_rule(tmp_path: Path, *, selector: str = 'prob_ge_threshold', threshold: float = 0.7) -> Path:
    path = tmp_path / 'rule.json'
    path.write_text(
        json.dumps(
            {
                'mode': 'test',
                'winner': {
                    'score_target': 'take_24_x8',
                    'selector': selector,
                    'threshold': threshold,
                    'exit_atr_multiplier': 8,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )
    return path


def test_apply_rule_prob_threshold_selects_only_active_rows(tmp_path):
    predictions = exporter.load_prediction_frame(_write_prediction_csv(tmp_path))
    rule = exporter.load_rule_payload_from_file(_write_rule(tmp_path, selector='prob_ge_threshold', threshold=0.7))

    selected = exporter.apply_rule(predictions, rule)

    assert selected.tolist() == [True, True, False, False, False]


def test_apply_rule_top_k_uses_only_active_rows(tmp_path):
    predictions = exporter.load_prediction_frame(_write_prediction_csv(tmp_path))
    rule = exporter.load_rule_payload_from_file(_write_rule(tmp_path, selector='top_k_probability', threshold=0.5))

    selected = exporter.apply_rule(predictions, rule)

    assert selected.tolist() == [True, True, False, False, False]


def test_export_signals_can_expand_to_full_base_series(tmp_path):
    predictions_path = _write_prediction_csv(tmp_path)
    rule_path = _write_rule(tmp_path, selector='prob_ge_threshold', threshold=0.7)
    base_path = tmp_path / 'base.csv'
    pd.DataFrame(
        [
            {'time': '2025.01.01 00:00', 'signal': 1},
            {'time': '2025.01.01 01:00', 'signal': -1},
            {'time': '2025.01.01 02:00', 'signal': 1},
            {'time': '2025.01.01 03:00', 'signal': 0},
            {'time': '2025.01.01 04:00', 'signal': -1},
            {'time': '2025.01.01 05:00', 'signal': 1},
        ]
    ).to_csv(base_path, sep=';', index=False)

    output = tmp_path / 'ml_signals.csv'
    exporter.export_signals(
        predictions_path=predictions_path,
        rule_path=rule_path,
        output_path=output,
        base_csv=base_path,
    )

    out = pd.read_csv(output, sep=';')
    assert out['signal'].tolist() == [1, -1, 0, 0, 0, 0]


def test_export_signals_rejects_unknown_selector(tmp_path):
    _write_prediction_csv(tmp_path)
    rule_path = _write_rule(tmp_path, selector='mystery_selector', threshold=0.7)

    with pytest.raises(ValueError, match='unsupported selector'):
        exporter.load_rule_payload_from_file(rule_path)


def test_export_signals_copy_to_mt4_writes_both_targets(tmp_path):
    predictions_path = _write_prediction_csv(tmp_path)
    rule_path = _write_rule(tmp_path, selector='prob_ge_threshold', threshold=0.7)
    output = tmp_path / 'ml_signals.csv'
    tester_path = tmp_path / 'tester' / 'files' / 'ml_signals.csv'
    runtime_path = tmp_path / 'MQL4' / 'Files' / 'ml_signals.csv'

    exporter.MT4_TESTER_SIGNALS = tester_path
    exporter.MT4_RUNTIME_SIGNALS = runtime_path

    exporter.export_signals(
        predictions_path=predictions_path,
        rule_path=rule_path,
        output_path=output,
        copy_to_mt4=True,
    )

    out = output.read_text(encoding='utf-8')
    assert tester_path.read_text(encoding='utf-8') == out
    assert runtime_path.read_text(encoding='utf-8') == out


def test_export_signals_writes_reproducible_metadata(tmp_path):
    predictions_path = _write_prediction_csv(tmp_path)
    rule_path = _write_rule(tmp_path, selector='prob_ge_threshold', threshold=0.7)
    output = tmp_path / 'ml_signals.csv'
    metadata = tmp_path / 'metadata.json'

    exporter.export_signals(
        predictions_path=predictions_path,
        rule_path=rule_path,
        output_path=output,
        metadata_output=metadata,
        label='telemetry_frequency_v1',
    )

    payload = json.loads(metadata.read_text(encoding='utf-8'))
    assert payload['label'] == 'telemetry_frequency_v1'
    assert payload['predictions_path'] == str(predictions_path)
    assert payload['rule_path'] == str(rule_path)
    assert payload['output_path'] == str(output)
    assert len(payload['predictions_sha256']) == 64
    assert len(payload['rule_sha256']) == 64
    assert len(payload['output_sha256']) == 64
    assert payload['rows_total'] == 5
    assert payload['nonzero_rows'] == 2
    assert payload['buy_rows'] == 1
    assert payload['sell_rows'] == 1
    assert payload['duplicate_time_rows'] == 0
    assert payload['same_time_opposite_signal_groups'] == 0
