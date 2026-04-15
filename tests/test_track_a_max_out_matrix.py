import sys

import numpy as np

sys.path.insert(0, '.')

from ML.run_track_a_max_out_matrix import DEFAULT_MATRIX_CONFIGS, _jsonable, config_slug


def test_default_track_a_matrix_has_expected_configs():
    slugs = [config_slug(config['model'], config['seq_len']) for config in DEFAULT_MATRIX_CONFIGS]
    assert slugs == [
        'transformer_seq20',
        'transformer_seq50',
        'transformer_seq100',
        'entry_path_dual_stream_seq20',
        'entry_path_dual_stream_seq50',
        'entry_path_dual_stream_seq100',
    ]


def test_jsonable_converts_numpy_arrays():
    payload = _jsonable({'values': np.array([1.0, 2.0], dtype=np.float32)})
    assert payload == {'values': [1.0, 2.0]}
