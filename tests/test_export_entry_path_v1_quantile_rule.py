import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, '.')

from ML import export_entry_path_v1_quantile_rule as export_mod
from tests.test_entry_path_v1_quantile_n_boost import _write_minimal_seed


def _make_baseline_rule(tmp_path, seed_dir):
    baseline_rule = {
        'winner': {'candidate': 'A', 'score_threshold': 0.4, 'pf': 2.0},
        'validation_csv': str(seed_dir / 'entry_path_v1_quantile_validation_predictions.csv'),
        'test_csv': str(seed_dir / 'entry_path_v1_quantile_test_predictions.csv'),
        'sequential_hold_bars': 24,
    }
    path = tmp_path / 'baseline_rule.json'
    path.write_text(json.dumps(baseline_rule), encoding='utf-8')
    return path


def test_compute_seed_params_returns_required_fields(tmp_path):
    seed_dir = _write_minimal_seed(tmp_path, 7, n_rows=40)
    baseline_path = seed_dir / 'entry_path_v1_quantile_validation_predictions.csv'
    baseline = pd.read_csv(baseline_path, sep=';')[['time', 'signal', 'pred_ret_24_dir_atr']]
    baseline['time'] = pd.to_datetime(baseline['time'], format='%Y.%m.%d %H:%M', errors='coerce')

    params = export_mod.compute_seed_params(
        seed_dir=seed_dir,
        baseline_frame=baseline,
        baseline_threshold=0.4,
        quantile=0.35,
        alpha=0.10,
    )
    assert {'seed_dir', 'm', 'w', 'correction'} <= params.keys()
    assert isinstance(params['m'], float)
    assert isinstance(params['w'], float)
    assert isinstance(params['correction'], float)


def test_export_rule_writes_median_params(tmp_path):
    seeds = [7, 17, 42]
    for s in seeds:
        _write_minimal_seed(tmp_path, s, n_rows=40)
    baseline_path = _make_baseline_rule(tmp_path, tmp_path / 'seed_007')
    output_path = tmp_path / 'entry_path_v1_quantile_selected_rule.json'

    result = export_mod.export_rule(
        root_dir=tmp_path,
        seeds=seeds,
        baseline_rule_path=baseline_path,
        rule='lb_gt_m',
        quantile=0.35,
        alpha=0.10,
        output_path=output_path,
    )
    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['winner']['rule'] == 'lb_gt_m'
    assert payload['winner']['quantile'] == 0.35
    assert 'm' in payload['winner']
    assert 'w' in payload['winner']
    assert 'correction' in payload['winner']
    assert len(payload['per_seed_params']) == 3
    assert payload['seeds'] == seeds

    per_seed_m = [p['m'] for p in payload['per_seed_params']]
    expected_median_m = float(pd.Series(per_seed_m).median())
    assert abs(payload['winner']['m'] - expected_median_m) < 1e-12
