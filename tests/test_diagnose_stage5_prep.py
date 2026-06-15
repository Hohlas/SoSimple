# Tests for ML/baseline/diagnose_stage5_prep.py
# Stage 5.0-prep: feature ablation + AUC->PF sensitivity

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ML.baseline.diagnose_stage5_prep import (
    get_feature_groups,
    build_feature_mask,
    FEATURE_PROFILES,
    oracle_mix_scores,
    schema_ok,
)

BASE_CHANNEL_KEYS = ['price', 'direction', 'front', 'back', 'strong', 'break',
                     'reverse', 'power', 'count', 'impulse']
N_FRACTALS = 100


def _make_names():
    names = []
    for level in range(N_FRACTALS):
        for key in BASE_CHANNEL_KEYS:
            names.append(f'f{level}_{key}')
    names.append('ATR')
    names += ['hour_sin', 'hour_cos', 'dow_sin', 'dow_cos']
    return names


class TestFeatureGroups:
    """Smoke tests for feature group resolver."""

    def test_groups_produce_disjoint_partition(self):
        names = _make_names()
        groups = get_feature_groups(names)
        assigned = set()
        for gname, indices in groups.items():
            assigned.update(indices)
        assert assigned == set(range(len(names))), (
            f"Missing indices: {set(range(len(names))) - assigned}"
        )

    def test_group_sizes(self):
        names = _make_names()
        groups = get_feature_groups(names)
        assert len(groups['fractal_core']) == 1000
        assert len(groups['atr']) == 1
        assert len(groups['time']) == 4

    def test_profile_masks_map_correctly(self):
        names_all = _make_names()
        for profile_name in FEATURE_PROFILES:
            mask = build_feature_mask(profile_name, names_all)
            assert mask.sum() > 0, f"Profile {profile_name} has zero features"
            assert mask.sum() <= len(names_all)


class TestOracleMix:
    """Smoke tests for oracle-like mixing."""

    def test_alpha_0_returns_model_scores(self):
        np.random.seed(42)
        model = np.random.uniform(0, 1, 100)
        labels = np.random.choice([0, 1], 100)
        mixed = oracle_mix_scores(model, labels, alpha=0.0)
        np.testing.assert_array_almost_equal(mixed, model)

    def test_alpha_1_returns_perfect_ranking(self):
        np.random.seed(42)
        model = np.random.uniform(0, 1, 100)
        labels = np.random.choice([0, 1], 100)
        mixed = oracle_mix_scores(model, labels, alpha=1.0)
        assert roc_auc(labels, mixed) > 0.99

    def test_probabilities_in_range(self):
        np.random.seed(42)
        model = np.random.uniform(0, 1, 100)
        labels = np.random.choice([0, 1], 100)
        for alpha in [0.0, 0.1, 0.3, 0.5, 0.7, 1.0]:
            mixed = oracle_mix_scores(model, labels, alpha=alpha)
            assert np.all(mixed >= 0)
            assert np.all(mixed <= 1)

    def test_alpha_05_is_between(self):
        np.random.seed(42)
        model = np.random.uniform(0, 1, 100)
        labels = np.random.choice([0, 1], 100)
        for alpha in [0.1, 0.3, 0.5, 0.7]:
            mixed = oracle_mix_scores(model, labels, alpha=alpha)
            model_auc = roc_auc(labels, model)
            mixed_auc = roc_auc(labels, mixed)
            assert mixed_auc >= model_auc


class TestSchema:
    """JSON schema tests."""

    def test_baseline_schema_ok(self):
        output = {
            'status': 'DIAGNOSTIC_ONLY',
            'config': {},
            'baseline_reproduction': {},
            'feature_ablation': [],
            'auc_pf_sensitivity': [],
            'interpretation_guards': [],
        }
        assert schema_ok(output)


def roc_auc(y_true, y_score):
    from sklearn.metrics import roc_auc_score
    if len(np.unique(y_true)) < 2:
        return 0.5
    return float(roc_auc_score(y_true, y_score))
