# =============================================================================
# File: tests/test_stage5_transformer_breach.py
# Purpose: Smoke tests for Stage 5.0 Transformer Breach Holdout
#          (includes Stage 5.0d — logistic baseline + feature ablation tests)
# Language: Python 3.10+
# Created: 2026-06-17
# Updated: 2026-06-23
# =============================================================================

import json
import os, sys
from concurrent.futures import Future
import numpy as np
import pandas as pd
import pytest
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ML.baseline.benchmark_stage5_transformer_breach import (
    PROFILE_DEFS,
    find_profile,
    define_profiles,
    extract_base10_fields,
    extract_full29_fields,
    build_row_features,
    build_profile_features,
    compute_profile_coverage,
    compute_corridor_stats,
    get_profile_contract,
    get_profile_seq_len,
    normalize_profile_features,
    BASE10_INDICES,
    FULL29_INDICES,
    NO_PRICE_TOKEN_FIELDS,
    PREFLIGHT_PROFILE_NAMES,
    TARGET_COLUMN,
    TRAIN_MAX_YEAR,
    VAL_STOP_YEARS,
    HOLDOUT_MIN_YEAR,
)

from ML.models.fractal_breach_transformer import (
    FractalBreachTransformer,
    TokenSelector,
)


# ───────────────────────────────────────────────────────────────────────────
# Synthetic data helpers
# ───────────────────────────────────────────────────────────────────────────

def _make_fractal_str(fields: list) -> str:
    """Create a valid fractal string from field values (positions match CSV format)."""
    defaults = [0] * 23
    for idx, val in fields:
        defaults[idx] = val
    return ':'.join(str(v) for v in defaults)


def _make_synthetic_df(n_rows: int = 10, n_fractals: int = 10) -> pd.DataFrame:
    """Create a minimal synthetic DataFrame for testing."""
    np.random.seed(42)
    rows = {'time': [], 'signal': [], 'ATR': [], TARGET_COLUMN: []}
    for i in range(n_fractals):
        rows[f'fractal{i}'] = []

    base_price = 390.0
    for r in range(n_rows):
        t = f'2020.{r+1:02d}.01 12:00'
        rows['time'].append(t)
        rows['signal'].append(-1)
        atr = 1.5 + np.random.uniform(-0.5, 0.5)
        rows['ATR'].append(atr)
        rows[TARGET_COLUMN].append(np.random.randint(0, 2))

        for i in range(n_fractals):
            price = base_price + np.random.uniform(-20, 20)
            fields = [
                (0, 10_000_000),
                (1, price),
                (2, -1),
                (3, np.random.uniform(0, 1)),
                (4, np.random.uniform(0, 0.5)),
                (5, np.random.randint(0, 2)),
                (6, np.random.randint(0, 2)),
                (7, 0),
                (8, 1),
                (9, 1),
                (10, np.random.uniform(0, 1)),
                (21, atr + np.random.uniform(-0.3, 0.3)),
                (22, i * 10 + 1),
            ]
            rows[f'fractal{i}'].append(_make_fractal_str(fields))

    return pd.DataFrame(rows)


def _make_ordered_corridor_df(n_rows: int = 2, n_fractals: int = 100, step: float = 0.1,
                              atr: float = 1.0) -> pd.DataFrame:
    """Create rows where fractal prices grow from fractal0 with fixed step."""
    rows = {'time': [], 'signal': [], 'ATR': [], TARGET_COLUMN: []}
    for i in range(n_fractals):
        rows[f'fractal{i}'] = []

    for r in range(n_rows):
        rows['time'].append(f'2020.{r+1:02d}.01 12:00')
        rows['signal'].append(-1)
        rows['ATR'].append(atr)
        rows[TARGET_COLUMN].append(r % 2)
        for i in range(n_fractals):
            price = 390.0 + i * step
            rows[f'fractal{i}'].append(_make_fractal_str([
                (0, 10_000_000),
                (1, price),
                (2, -1),
                (3, 0.5),
                (4, 0.25),
                (5, 1),
                (6, 0),
                (7, 0),
                (8, 1),
                (9, 1),
                (10, 0.5),
                (21, atr),
                (22, i + 1),
            ]))
    return pd.DataFrame(rows)


# ───────────────────────────────────────────────────────────────────────────
# Task 1 Step 1: Profile definitions
# ───────────────────────────────────────────────────────────────────────────

class TestProfileDefinitions:
    """Step 1: Feature profile definitions."""

    def test_all_six_required_profiles_present(self):
        profiles = define_profiles()
        required = {
            'all100_base10_time',
            'all100_base10_no_time',
            'newest20_base10_time',
            'nearest40_base10_time',
            'corridor_10atr_base10_time',
        }
        names = {p['name'] for p in profiles}
        assert required.issubset(names), f"Missing profiles: {required - names}"

    def test_relative_price_profiles_present(self):
        profiles = define_profiles()
        rp_profiles = {
            'all100_base10_relative_price_time',
            'nearest40_base10_relative_price_time',
            'corridor_10atr_base10_relative_price_time',
        }
        names = {p['name'] for p in profiles}
        assert rp_profiles.issubset(names), f"Missing relative_price profiles: {rp_profiles - names}"

    def test_relative_price_flag_set(self):
        for p in define_profiles():
            if 'relative_price' in p['name']:
                assert p.get('relative_price') is True, f"{p['name']} missing relative_price flag"

    def test_each_profile_has_required_keys(self):
        required_keys = {
            'name', 'selection', 'order', 'token_fields', 'row_fields',
            'uses_time', 'seq_len', 'token_dim', 'row_dim',
        }
        for p in define_profiles():
            missing = required_keys - set(p.keys())
            assert not missing, f"Profile {p['name']} missing keys: {missing}"

    def test_profiles_not_created_dynamically(self):
        # PROFILE_DEFS is a static list, not built from results
        assert isinstance(PROFILE_DEFS, list)
        assert len(PROFILE_DEFS) > 0

    def test_find_profile_existing(self):
        p = find_profile('all100_base10_time')
        assert p is not None
        assert p['name'] == 'all100_base10_time'

    def test_find_profile_missing(self):
        p = find_profile('nonexistent')
        assert p is None


# ───────────────────────────────────────────────────────────────────────────
# Task 1 Step 2: Tensor shapes
# ───────────────────────────────────────────────────────────────────────────

class TestTensorShapes:
    """Step 2: Feature builder tensor shapes."""

    def test_all100_shapes(self):
        df = _make_synthetic_df(10, 100)
        profile = find_profile('all100_base10_time')
        tokens, row_features, mask, _selection_meta = build_profile_features(df, profile)
        assert tokens.shape == (10, 100, 10)
        assert row_features.shape == (10, 5)
        assert mask.shape == (10, 100)

    def test_newest20_shapes(self):
        df = _make_synthetic_df(10, 50)
        profile = find_profile('newest20_base10_time')
        tokens, row_features, mask, _selection_meta = build_profile_features(df, profile)
        assert tokens.shape == (10, 20, 10)
        assert row_features.shape == (10, 5)
        assert mask.shape == (10, 20)

    def test_nearest40_shapes(self):
        df = _make_synthetic_df(10, 100)
        profile = find_profile('nearest40_base10_time')
        tokens, row_features, mask, _selection_meta = build_profile_features(df, profile)
        assert tokens.shape == (10, 40, 10)
        assert row_features.shape == (10, 5)
        assert mask.shape == (10, 40)

    def test_corridor_shapes(self):
        df = _make_synthetic_df(10, 100)
        profile = find_profile('corridor_10atr_base10_time')
        tokens, row_features, mask, _selection_meta = build_profile_features(df, profile)
        assert tokens.shape == (10, 40, 10)
        assert row_features.shape == (10, 5)
        assert mask.shape == (10, 40)


# ───────────────────────────────────────────────────────────────────────────
# Task 1 Step 3: Profile contracts
# ───────────────────────────────────────────────────────────────────────────

class TestProfileContracts:
    """Step 3: Profile contracts."""

    def test_no_time_excludes_hour_dow(self):
        profile = find_profile('all100_base10_no_time')
        assert 'uses_time' in profile
        assert not profile['uses_time']
        row_fields = set(profile['row_fields'])
        assert 'hour_sin' not in row_fields
        assert 'dow_sin' not in row_fields

    def test_time_profile_includes_hour_dow(self):
        profile = find_profile('all100_base10_time')
        assert profile['uses_time']
        row_fields = set(profile['row_fields'])
        assert 'hour_sin' in row_fields
        assert 'dow_sin' in row_fields

    def test_nearest_orders_by_price_distance(self):
        profile = find_profile('nearest40_base10_time')
        assert profile['order'] == 'price_distance'

    def test_all100_orders_by_freshness(self):
        profile = find_profile('all100_base10_time')
        assert profile['order'] == 'freshness'

    def test_corridor_10atr_has_corridor_width(self):
        profile = find_profile('corridor_10atr_base10_time')
        assert profile.get('corridor_atr') == 10.0

    def test_newest20_uses_n(self):
        profile = find_profile('newest20_base10_time')
        assert profile.get('n') == 20


# ───────────────────────────────────────────────────────────────────────────
# Task 1 Step 4: Corridor validation
# ───────────────────────────────────────────────────────────────────────────

class TestCorridorValidation:
    """Step 4: Corridor stats and validation."""

    def _corridor_df(self, atr: float, n_fractals: int = 100) -> pd.DataFrame:
        """DataFrame where corridor coverage can be controlled."""
        rows = {'time': [], 'signal': [], 'ATR': [], TARGET_COLUMN: []}
        for i in range(n_fractals):
            rows[f'fractal{i}'] = []

        for r in range(10):
            rows['time'].append('2020.01.01 12:00')
            rows['signal'].append(-1)
            rows['ATR'].append(atr)
            rows[TARGET_COLUMN].append(0)
            for i in range(n_fractals):
                price = 390.0 + (i - 50) * 5 * (atr / 10.0)
                fields = [(0, 10_000_000), (1, price), (2, -1), (3, 0.5), (4, 0.1),
                          (5, 0), (6, 0), (7, 0), (8, 1), (9, 1), (10, 0.5)]
                rows[f'fractal{i}'].append(_make_fractal_str(fields))

        return pd.DataFrame(rows)

    def test_stats_computed(self):
        df = self._corridor_df(atr=1.0)
        profile = find_profile('corridor_10atr_base10_time')
        stats = compute_corridor_stats(df, profile)
        assert 'n_fractals_median' in stats
        assert 'pct_empty' in stats
        assert 'pct_three_plus' in stats

    def test_empty_corridor_mask_valid(self):
        df = self._corridor_df(atr=0.001)
        profile = find_profile('corridor_10atr_base10_time')
        tokens, row_features, mask, _selection_meta = build_profile_features(df, profile)
        assert tokens.shape[0] == 10
        assert not np.isnan(tokens).any()

    def test_single_fractal_corridor_no_nan(self):
        df = self._corridor_df(atr=0.01)
        profile = find_profile('corridor_10atr_base10_time')
        tokens, row_features, mask, _selection_meta = build_profile_features(df, profile)
        assert not np.isnan(tokens).any()

    def test_low_coverage_detected(self):
        profile = find_profile('corridor_10atr_base10_time')
        stats = {'pct_empty': 0.06, 'n_fractals_median': 4}
        from ML.baseline.benchmark_stage5_transformer_breach import corridor_status
        status = corridor_status(stats)
        assert status == 'LOW_COVERAGE'

    def test_low_coverage_by_median(self):
        stats = {'pct_empty': 0.02, 'n_fractals_median': 2}
        from ML.baseline.benchmark_stage5_transformer_breach import corridor_status
        status = corridor_status(stats)
        assert status == 'LOW_COVERAGE'

    def test_rejected_detected(self):
        stats = {'pct_empty': 0.25, 'n_fractals_median': 1}
        from ML.baseline.benchmark_stage5_transformer_breach import corridor_status
        status = corridor_status(stats)
        assert status == 'REJECTED'

    def test_ok_status(self):
        stats = {'pct_empty': 0.01, 'n_fractals_median': 10}
        from ML.baseline.benchmark_stage5_transformer_breach import corridor_status
        status = corridor_status(stats)
        assert status == 'OK'


# ───────────────────────────────────────────────────────────────────────────
# Task 1 Step 5: Split guard
# ───────────────────────────────────────────────────────────────────────────

class TestSplitGuard:
    """Step 5: Train/validation/holdout split integrity."""

    def test_years_assigned_correctly(self):
        df = _make_synthetic_df(20, 10)
        df['_year'] = pd.to_datetime(
            df['time'], format='%Y.%m.%d %H:%M', errors='coerce').dt.year
        train = df[df['_year'] <= TRAIN_MAX_YEAR]
        assert len(train) > 0

    def test_val_stop_years(self):
        from ML.baseline.benchmark_stage5_transformer_breach import VAL_STOP_YEARS
        assert VAL_STOP_YEARS == {2021, 2022}

    def test_holdout_min_year(self):
        from ML.baseline.benchmark_stage5_transformer_breach import HOLDOUT_MIN_YEAR
        assert HOLDOUT_MIN_YEAR == 2023


# ───────────────────────────────────────────────────────────────────────────
# Task 2: Base10 field extraction
# ───────────────────────────────────────────────────────────────────────────

class TestFieldExtraction:
    def test_base10_indices(self):
        assert BASE10_INDICES == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    def test_extract_base10(self):
        fstr = _make_fractal_str([
            (0, 10), (1, 400.0), (2, -1), (3, 0.8), (4, 0.2),
            (5, 1), (6, 0), (7, 0), (8, 1), (9, 2), (10, 0.5),
            (21, 1.5), (22, 5),
        ])
        feats = extract_base10_fields(fstr)
        assert len(feats) == 10
        assert feats[0] == pytest.approx(400.0)
        assert feats[1] == -1.0
        assert feats[2] == pytest.approx(0.8)
        assert feats[9] == pytest.approx(0.5)

    def test_base10_nan_fields_handled(self):
        parts = ['0'] * 23
        parts[1] = 'invalid'
        fstr = ':'.join(parts)
        feats = extract_base10_fields(fstr)
        assert not np.isnan(feats).all()
        assert feats[0] == 0.0  # NaN → 0 coerción


# ───────────────────────────────────────────────────────────────────────────
# Task 3: Model tests
# ───────────────────────────────────────────────────────────────────────────

class TestModel:
    """Step 4: Transformer model unit tests."""

    def _get_model(self, **kwargs):
        defaults = dict(
            token_dim=10, row_dim=5, d_model=64, nhead=4,
            num_layers=2, dim_feedforward=128, dropout=0.15,
        )
        defaults.update(kwargs)
        return FractalBreachTransformer(**defaults)

    def test_forward_pass_with_mask(self):
        model = self._get_model()
        batch, seq_len, token_dim = 4, 100, 10
        tokens = torch.randn(batch, seq_len, token_dim)
        row_feat = torch.randn(batch, 5)
        mask = torch.ones(batch, seq_len, dtype=torch.bool)
        mask[:, -20:] = False  # last 20 are padding
        logits = model(tokens, row_feat, mask)
        assert logits.shape == (batch, 1)
        assert not torch.isnan(logits).any()

    def test_forward_pass_full_padding_row(self):
        model = self._get_model()
        tokens = torch.randn(4, 100, 10)
        row_feat = torch.randn(4, 5)
        mask = torch.zeros(4, 100, dtype=torch.bool)  # all padding
        logits = model(tokens, row_feat, mask)
        assert not torch.isnan(logits).any()

    def test_output_shape_stable_all_profiles(self):
        test_configs = [
            (10, 100),  # all100
            (10, 20),   # newest20
            (10, 40),   # nearest40/corridor
        ]
        for token_dim, seq_len in test_configs:
            model = self._get_model(token_dim=token_dim)
            tokens = torch.randn(4, seq_len, token_dim)
            row_feat = torch.randn(4, 5)
            mask = torch.ones(4, seq_len, dtype=torch.bool)
            logits = model(tokens, row_feat, mask)
            assert logits.shape == (4, 1)

    def test_position_embedding_learned(self):
        model = self._get_model()
        assert hasattr(model, 'pos_embedding')
        assert isinstance(model.pos_embedding, torch.nn.Embedding)

    def test_row_feature_mlp_exists(self):
        model = self._get_model()
        assert hasattr(model, 'row_mlp')

    def test_token_projection_exists(self):
        model = self._get_model()
        assert hasattr(model, 'token_projection')


# ───────────────────────────────────────────────────────────────────────────
# TokenSelector tests
# ───────────────────────────────────────────────────────────────────────────

class TestTokenSelector:
    def test_corridor_selection(self):
        prices = np.array([390.0, 385.0, 395.0, 380.0, 400.0, 375.0, 405.0])
        f0_price = 390.0
        atr = 2.0
        corridor_atr = 5.0
        idx, mask, sel_prices = TokenSelector.by_corridor(prices, f0_price, atr, corridor_atr, seq_len=7)
        # Within corridor_atr * atr = 5 * 2 = 10.0 → 380.0 to 400.0
        n_selected = mask.sum()
        assert n_selected == 5  # 390, 385, 395, 380, 400
        assert 375.0 not in sel_prices
        assert 405.0 not in sel_prices

    def test_nearest_selection(self):
        prices = np.array([390.0, 420.0, 380.0, 395.0, 385.0, 410.0, 375.0])
        f0_price = 390.0
        idx, mask, sel_prices = TokenSelector.by_nearest(prices, f0_price, k=4, seq_len=7)
        n_selected = mask.sum()
        assert n_selected == 4
        # Should be closest by price: 390, 395, 385, 380
        assert set(sel_prices) == {390.0, 395.0, 385.0, 380.0}

    def test_ordering_by_distance(self):
        prices = np.array([390.0, 370.0, 395.0, 385.0, 400.0])
        f0_price = 390.0
        idx, mask, sel_prices = TokenSelector.by_corridor(prices, f0_price, atr=2.0, corridor_atr=20.0, seq_len=40)
        # Ordered by distance ascending
        distances = [abs(p - f0_price) for p in sel_prices]
        assert distances == sorted(distances)


# ───────────────────────────────────────────────────────────────────────────
# Normalization tests
# ───────────────────────────────────────────────────────────────────────────

class TestNormalization:
    def test_normalize_fit_on_train_only(self):
        from ML.baseline.benchmark_stage5_transformer_breach import normalize_profile_features
        rng = np.random.RandomState(42)
        t_train = rng.randn(20, 10, 5).astype(np.float32) * 10 + 100
        m_train = np.ones((20, 10), dtype=bool)
        m_train[:, -2:] = False
        t_val = rng.randn(10, 10, 5).astype(np.float32) * 10 + 100
        m_val = np.ones((10, 10), dtype=bool)
        t_hold = rng.randn(8, 10, 5).astype(np.float32) * 10 + 100
        m_hold = np.ones((8, 10), dtype=bool)
        rf_train = rng.randn(20, 3).astype(np.float32) * 2 + 5
        rf_val = rng.randn(10, 3).astype(np.float32) * 2 + 5
        rf_hold = rng.randn(8, 3).astype(np.float32) * 2 + 5

        (tt, rft, tv, rfv, th, rfh), stats = normalize_profile_features(
            t_train, rf_train, m_train, t_val, rf_val, m_val, t_hold, rf_hold, m_hold)

        # Padding stays zero
        assert np.allclose(tt[0, -2:, :], 0.0)
        # Valid positions are transformed
        assert not np.allclose(tt[0, 0, :], 0.0)
        # Stats recorded
        assert 'token_scaler' in stats
        assert 'row_scaler' in stats
        assert len(stats['token_scaler']['mean']) == 5

    def test_relative_price_builds_tokens(self):
        from ML.baseline.benchmark_stage5_transformer_breach import build_profile_features, find_profile
        df = _make_synthetic_df(5, 100)
        profile = find_profile('all100_base10_relative_price_time')
        tokens, rf, mask, _selection_meta = build_profile_features(df, profile)
        assert tokens.shape == (5, 100, 10)
        assert rf.shape == (5, 5)

    def test_relative_price_formula_verified(self):
        """Verify relative_price token column = signed_log1p((price_i - f0_price) / ATR).

        A7: signed price coordinate must use signed-log transform
        (sign(x)*log1p(abs(x))), not raw value, to compress the long right tail
        of far-away fractals (all100 pos99 train p95=10.86 -> ~2.4 after signed-log).
        Anchor (fractal0): signed_log1p(0)=0.
        """
        from ML.baseline.benchmark_stage5_transformer_breach import build_profile_features, find_profile
        df = _make_synthetic_df(3, 5)
        # Force known values for deterministic check
        f0_price = 400.0
        atr_val = 2.0
        for i in range(len(df)):
            df.at[i, 'ATR'] = atr_val
        # Overwrite fractal0 to have known price
        for i in range(len(df)):
            fields = [0] * 23
            fields[0] = 10_000_000
            fields[1] = f0_price  # fractal0.price
            fields[2] = -1
            fields[3] = 0.5
            fields[4] = 0.5
            fields[5] = 1
            fields[6] = 0
            fields[7] = 0
            fields[8] = 1
            fields[9] = 1
            fields[10] = 0.5
            df.at[i, 'fractal0'] = ':'.join(str(v) for v in fields)
        # Overwrite fractal1 with different price
        f1_price = 410.0
        for i in range(len(df)):
            fields = [0] * 23
            fields[0] = 10_000_000
            fields[1] = f1_price
            fields[2] = -1
            fields[3] = 0.5
            fields[4] = 0.5
            fields[5] = 1
            fields[6] = 0
            fields[7] = 0
            fields[8] = 1
            fields[9] = 1
            fields[10] = 0.5
            df.at[i, 'fractal1'] = ':'.join(str(v) for v in fields)

        profile = find_profile('all100_base10_relative_price_time')
        tokens, rf, mask, _selection_meta = build_profile_features(df, profile)

        # price column (index 0 of base10) = signed_log1p((price_i - f0_price) / ATR)
        # all100 preserves natural order: fractal0=pos0, fractal1=pos1
        # For fractal0: signed_log1p((400 - 400) / 2) = signed_log1p(0) = 0
        # For fractal1: signed_log1p((410 - 400) / 2) = signed_log1p(5) = 1.7917595
        price_col = tokens[0, :, 0]  # first sample, all positions, price column
        valid_mask = mask[0]
        assert valid_mask.sum() >= 2, "Need at least 2 valid fractals"
        valid_prices = price_col[valid_mask]
        assert abs(valid_prices[0] - 0.0) < 0.01, f"fractal0 relative_price expected 0.0, got {valid_prices[0]}"
        assert abs(valid_prices[1] - 1.7917595) < 0.01, f"fractal1 signed_log1p(5.0) expected 1.7918, got {valid_prices[1]}"


# ───────────────────────────────────────────────────────────────────────────
# Phase 3 smoke test
# ───────────────────────────────────────────────────────────────────────────

class TestPhase3Smoke:
    """Verify Phase 3 (corridor ablation) normalizes tokens (no scaler_stats NameError)."""

    def test_phase3_uses_normalize(self):
        """Simulate Phase 3: assert normalize is called (no scaler_stats crash)."""
        from ML.baseline.benchmark_stage5_transformer_breach import (
            _train_and_eval_profile,
            build_profile_features,
            normalize_profile_features,
            find_profile,
        )
        from unittest.mock import patch, MagicMock

        df = _make_synthetic_df(5, 20)
        df[TARGET_COLUMN] = df[TARGET_COLUMN].astype(np.float32)  # ensure non-null
        profile = find_profile('corridor_15atr_base10_time')

        tokens, rf, mask, _selection_meta = build_profile_features(df, profile)
        # Simulate the normalize call that Phase 3 would make via _train_and_eval_profile
        (tn, rfn, tv, rfv, th, rfh), stats = normalize_profile_features(
            tokens, rf, mask,
            tokens, rf, mask,  # use same for val
            tokens, rf, mask,  # use same for holdout
        )
        assert 'token_scaler' in stats
        assert 'row_scaler' in stats
        assert 'n_valid_train_positions' in stats['token_scaler']

    def test_phase3_all_profiles_in_defs(self):
        """Phase 3 profiles (corridor_5atr, corridor_15atr) exist in PROFILE_DEFS."""
        from ML.baseline.benchmark_stage5_transformer_breach import find_profile
        for pname in ['corridor_5atr_base10_time', 'corridor_15atr_base10_time']:
            p = find_profile(pname)
            assert p is not None, f"Missing Phase 3 profile: {pname}"
            assert p.get('selection') == 'corridor'


# ───────────────────────────────────────────────────────────────────────────
# OHLC verification fractal_dir_counts test
# ───────────────────────────────────────────────────────────────────────────

class TestOhlcFractalDir:
    """Verify OHLC label verification tracks fractal_dir==1 for sell_stop rows."""

    def test_fractal_dir_counts_in_result(self):
        import tempfile, os
        from ML.baseline.benchmark_stage5_transformer_breach import verify_breach_labels_against_ohlc, load_splits

        train_df, val_stop_df, holdout_df = load_splits()
        v = verify_breach_labels_against_ohlc(holdout_df, n_sample=50, random_seed=123)
        assert 'fractal_dir_counts' in v
        assert 'fractal_dir_ok' in v
        dc = v['fractal_dir_counts']
        # sell_stop_broken_H6_off05_flag target — should only have dir==1 (SELL) rows
        assert dc.get(1, 0) > 0, "No fractal_dir==1 rows in sell_stop verification"
        assert dc.get(0, 0) == 0, "fractal_dir==0 rows should not appear in sell_stop check"
        assert v['fractal_dir_ok'], f"fractal_dir_ok=False, counts={dc}"


# ───────────────────────────────────────────────────────────────────────────
# Row feature building tests
# ───────────────────────────────────────────────────────────────────────────

class TestRowFeatures:
    def test_time_row_features(self):
        df = _make_synthetic_df(5, 10)
        profile = find_profile('all100_base10_time')
        _, row_feat, _, _selection_meta = build_profile_features(df, profile)
        assert row_feat.shape == (5, 5)

    def test_no_time_row_features(self):
        df = _make_synthetic_df(5, 10)
        profile = find_profile('all100_base10_no_time')
        _, row_feat, _, _selection_meta = build_profile_features(df, profile)
        assert row_feat.shape == (5, 1)

    def test_atr_log1p_transformed_in_row_features(self):
        """ATR as row feature must be log1p-transformed before scaler.

        A7 methodology: ATR is non-negative with a long right tail and shows
        holdout regime shift (train p95=1.83 -> holdout p95=12.06 after
        StandardScaler fit on train). log1p compresses the tail before scaling.
        build_row_features must return log1p(raw_ATR), not raw ATR.
        ATR=0 -> log1p(0)=0; ATR=e-1 -> log1p(e-1)=1.0; ATR<0 clipped to 0.
        """
        df = pd.DataFrame({
            "time": ["2020.01.01 00:00", "2020.01.02 00:00", "2020.01.03 00:00"],
            "ATR": [0.0, np.e - 1.0, -1.0],
        })
        profile = find_profile("all100_relative_price_no_time")  # row_fields = ["ATR"]
        row = build_row_features(df, profile)
        assert row.shape == (2, 1) or row.shape == (3, 1)
        assert row[0, 0] == pytest.approx(0.0, abs=1e-6)   # log1p(0) = 0
        assert row[1, 0] == pytest.approx(1.0, abs=1e-6)   # log1p(e-1) = 1.0, NOT e-1=1.718
        assert row[2, 0] == pytest.approx(0.0, abs=1e-6)   # clip(-1) -> 0 -> log1p(0) = 0


class TestTransformComparison:
    def test_asinh_transform_preserves_sign_and_compresses_tail(self):
        from ML.baseline.benchmark_stage5_transformer_breach import _asinh_transform
        values = np.array([-100.0, -1.0, 0.0, 1.0, 100.0], dtype=np.float32)
        out = _asinh_transform(values)
        assert out[2] == pytest.approx(0.0, abs=1e-6)
        assert out[0] < 0
        assert out[-1] > 0
        assert abs(out[-1]) < abs(values[-1])
        assert out[-1] == pytest.approx(-out[0], abs=1e-6)

    def test_piecewise_tail_keeps_middle_and_compresses_both_tails(self):
        from ML.baseline.benchmark_stage5_transformer_breach import (
            _apply_piecewise_tail_transform,
            _fit_piecewise_tail_params,
        )
        train = np.arange(-100, 101, dtype=np.float32)
        params = _fit_piecewise_tail_params(train, lower_q=5, upper_q=95)
        values = np.array([-100.0, -50.0, 0.0, 50.0, 100.0], dtype=np.float32)
        out = _apply_piecewise_tail_transform(values, params)
        assert out[2] == pytest.approx(0.0, abs=1e-6)
        assert out[1] == pytest.approx(-50.0, abs=1e-6)
        assert out[3] == pytest.approx(50.0, abs=1e-6)
        assert out[0] > values[0]
        assert out[4] < values[4]
        assert params["fit_split"] == "train"

    def test_transform_comparison_uses_all_three_variants(self, tmp_path, monkeypatch):
        import ML.baseline.benchmark_stage5_transformer_breach as runner
        df = _make_synthetic_df(4, 100)
        df["_year"] = [2020, 2020, 2020, 2020]
        val = _make_synthetic_df(3, 100)
        val["_year"] = [2021, 2022, 2022]
        hold = _make_synthetic_df(3, 100)
        hold["_year"] = [2023, 2024, 2025]
        monkeypatch.setattr(runner, "REPORTS_DIR", tmp_path)

        report = runner.run_transform_comparison(df, val, hold)

        assert report["training_allowed"] is False
        assert set(report["transform_variants"]) == {"current", "asinh", "piecewise_tail"}
        assert set(report["profile_reports"]) == {"current", "asinh", "piecewise_tail"}
        assert (tmp_path / "stage5_0a_transform_comparison_summary.csv").exists()
        piecewise = report["profile_reports"]["piecewise_tail"]["all100_relative_price_time"]
        assert piecewise["transform_config"]["fit_params"]["ATR"]["fit_split"] == "train"
        assert piecewise["transform_config"]["fit_params"]["price_coord_atr"]["fit_split"] == "train"

    def test_transform_comparison_includes_atr_scaled_price_profiles(self):
        import ML.baseline.benchmark_stage5_transformer_breach as runner
        expected = {
            "corridor_5atr_price_unit_atr_full",
            "corridor_10atr_price_unit_atr_full",
            "all100_absolute_price_atr_scaled_time_raw",
            "all100_absolute_price_atr_scaled_time_asinh",
        }
        assert expected.issubset(set(runner.RERUN_CANDIDATE_PROFILE_NAMES))


# ───────────────────────────────────────────────────────────────────────────
# Normalized distribution audit tests
# ───────────────────────────────────────────────────────────────────────────

class TestDistributionAudit:
    """Verify normalized_feature_distribution_audit detects tails, regime shift, and padding=0."""

    def test_audit_detects_tails(self):
        from ML.baseline.benchmark_stage5_transformer_breach import audit_normalized_distribution
        t_train = np.zeros((5, 3, 2), dtype=np.float32)
        m_train = np.ones((5, 3), dtype=bool)
        rf_train = np.zeros((5, 1), dtype=np.float32)
        t_val = np.zeros((3, 3, 2), dtype=np.float32)
        m_val = np.ones((3, 3), dtype=bool)
        rf_val = np.zeros((3, 1), dtype=np.float32)
        # holdout with deterministic extreme tails (>15 on all valid positions)
        t_hold = np.full((4, 3, 2), 15.0, dtype=np.float32)
        m_hold = np.ones((4, 3), dtype=bool)
        rf_hold = np.zeros((4, 1), dtype=np.float32)

        result = audit_normalized_distribution(
            t_train, m_train, t_val, m_val, t_hold, m_hold,
            rf_train, rf_val, rf_hold,
            token_fields=['feat0', 'feat1'],
            row_fields=['rf0'],
        )
        assert 'TAIL_GT10' in str(result['flags']), \
            f"Should detect TAIL_GT10, got: {result['flags']}"
        assert result['status'] in ('WARNING', 'ERROR'), \
            f"Expected WARNING/ERROR, got {result['status']}"

    def test_audit_detects_row_tails(self):
        """Row features with abs > 10 must also trigger TAIL flags."""
        from ML.baseline.benchmark_stage5_transformer_breach import audit_normalized_distribution
        t_train = np.zeros((5, 3, 2), dtype=np.float32)
        m_train = np.ones((5, 3), dtype=bool)
        rf_train = np.full((5, 1), 15.0, dtype=np.float32)  # row tail
        t_val = np.zeros((3, 3, 2), dtype=np.float32)
        m_val = np.ones((3, 3), dtype=bool)
        rf_val = np.full((3, 1), 15.0, dtype=np.float32)
        t_hold = np.zeros((4, 3, 2), dtype=np.float32)
        m_hold = np.ones((4, 3), dtype=bool)
        rf_hold = np.full((4, 1), 15.0, dtype=np.float32)

        result = audit_normalized_distribution(
            t_train, m_train, t_val, m_val, t_hold, m_hold,
            rf_train, rf_val, rf_hold,
            token_fields=['feat0', 'feat1'],
            row_fields=['rf0'],
        )
        assert 'TAIL_GT10' in str(result['flags']), \
            f"Should detect TAIL_GT10 in row, got: {result['flags']}"
        assert result['status'] in ('WARNING', 'ERROR'), \
            f"Expected WARNING/ERROR, got {result['status']}"

    def test_audit_detects_regime_shift(self):
        from ML.baseline.benchmark_stage5_transformer_breach import audit_normalized_distribution
        n_train, n_hold = 20, 10
        t_train = np.random.randn(n_train, 5, 1).astype(np.float32)
        m_train = np.ones((n_train, 5), dtype=bool)
        rf_train = np.random.randn(n_train, 1).astype(np.float32)
        t_val = np.random.randn(10, 5, 1).astype(np.float32)
        m_val = np.ones((10, 5), dtype=bool)
        rf_val = np.random.randn(10, 1).astype(np.float32)
        # holdout shifted by +5 sigma
        t_hold = np.random.randn(n_hold, 5, 1).astype(np.float32) + 5.0
        m_hold = np.ones((n_hold, 5), dtype=bool)
        rf_hold = np.random.randn(n_hold, 1).astype(np.float32) + 5.0

        result = audit_normalized_distribution(
            t_train, m_train, t_val, m_val, t_hold, m_hold,
            rf_train, rf_val, rf_hold,
            token_fields=['price'],
            row_fields=['atr'],
        )
        assert 'REGIME_SHIFT' in str(result['flags']), \
            f"Should detect regime shift, got: {result['flags']}"

    def test_audit_padding_must_be_zero(self):
        from ML.baseline.benchmark_stage5_transformer_breach import audit_normalized_distribution
        t_train = np.zeros((3, 4, 1), dtype=np.float32)
        m_train = np.ones((3, 4), dtype=bool)
        m_train[:, -1] = False
        t_train[:, -1, 0] = 0.001  # non-zero padding
        rf_train = np.zeros((3, 1), dtype=np.float32)

        result = audit_normalized_distribution(
            t_train, m_train,
            t_train, m_train,
            t_train, m_train,
            rf_train, rf_train, rf_train,
        )
        assert 'PADDING_NOT_ZERO' in str(result['flags']), \
            f"Should flag non-zero padding, got: {result['flags']}"
        assert result['status'] == 'ERROR', \
            f"Non-zero padding should be ERROR, got {result['status']}"

    def test_audit_nan_detection(self):
        from ML.baseline.benchmark_stage5_transformer_breach import audit_normalized_distribution
        t_train = np.zeros((3, 2, 1), dtype=np.float32)
        m_train = np.ones((3, 2), dtype=bool)
        t_train[0, 0, 0] = np.nan
        rf_train = np.zeros((3, 1), dtype=np.float32)

        result = audit_normalized_distribution(
            t_train, m_train,
            t_train, m_train,
            t_train, m_train,
            rf_train, rf_train, rf_train,
        )
        assert 'NaN' in str(result['flags']), \
            f"Should detect NaN, got: {result['flags']}"
        assert result['status'] == 'ERROR', \
            f"NaN should be ERROR, got {result['status']}"

    def test_audit_clean_ok(self):
        from ML.baseline.benchmark_stage5_transformer_breach import audit_normalized_distribution
        t_train = np.random.randn(10, 5, 2).astype(np.float32)
        m_train = np.ones((10, 5), dtype=bool)
        m_train[:, -1] = False  # padding positions
        t_train[~m_train] = 0.0  # padding must be zero
        rf_train = np.random.randn(10, 3).astype(np.float32)
        t_val = np.random.randn(6, 5, 2).astype(np.float32)
        m_val = np.ones((6, 5), dtype=bool)
        rf_val = np.random.randn(6, 3).astype(np.float32)
        t_hold = np.random.randn(4, 5, 2).astype(np.float32)
        m_hold = np.ones((4, 5), dtype=bool)
        rf_hold = np.random.randn(4, 3).astype(np.float32)

        result = audit_normalized_distribution(
            t_train, m_train, t_val, m_val, t_hold, m_hold,
            rf_train, rf_val, rf_hold,
        )
        # With standard normal, should be OK (no extreme tails, no NaN, padding zero)
        assert result['status'] == 'OK', \
            f"Expected OK, got {result['status']} with flags: {result['flags']}"


class TestPerPositionTokenStats:
    """A7 Feature Distribution Audit: for sequence profiles where token order has
    meaning (corridor/nearest/all100), per-position token stats must be computed.
    Aggregated-over-positions stats can hide position-specific tails or padding drift.
    """

    def test_per_position_stats_returned_with_position(self):
        from ML.baseline.benchmark_stage5_transformer_breach import compute_per_position_token_stats
        # 3 samples, seq_len=4, token_dim=2; padding varies per position
        tokens = np.array([
            [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]],
            [[1.1, 2.1], [3.1, 4.1], [0.0, 0.0], [0.0, 0.0]],
            [[1.2, 2.2], [3.2, 4.2], [5.2, 6.2], [0.0, 0.0]],
        ], dtype=np.float32)
        mask = np.array([
            [True, True, True, True],
            [True, True, False, False],
            [True, True, True, False],
        ], dtype=bool)
        rows = compute_per_position_token_stats(tokens, mask, ["feat_a", "feat_b"])
        # 4 positions x 2 features = 8 rows
        assert len(rows) == 8
        positions = sorted({r["token_position"] for r in rows})
        assert positions == [0, 1, 2, 3]
        # position 2 has 2 valid samples (rows 0 and 2); row 1 is padding
        pos2_a = [r for r in rows if r["token_position"] == 2 and r["feature_name"] == "feat_a"][0]
        assert pos2_a["n_valid"] == 2
        # position 3 has only 1 valid sample (row 0); rows 1 and 2 are padding
        pos3_b = [r for r in rows if r["token_position"] == 3 and r["feature_name"] == "feat_b"][0]
        assert pos3_b["n_valid"] == 1
        # every row carries feature_group=token and a non-empty token_position
        for r in rows:
            assert r["feature_group"] == "token"
            assert r["token_position"] != ""

    def test_per_position_empty_position_has_zero_n(self):
        from ML.baseline.benchmark_stage5_transformer_breach import compute_per_position_token_stats
        # position 2 is fully padded for all samples
        tokens = np.zeros((2, 3, 1), dtype=np.float32)
        tokens[:, 0, 0] = 1.0
        tokens[:, 1, 0] = 2.0
        mask = np.array([[True, True, False], [True, True, False]], dtype=bool)
        rows = compute_per_position_token_stats(tokens, mask, ["f0"])
        pos2 = [r for r in rows if r["token_position"] == 2][0]
        assert pos2["n_valid"] == 0

    def test_per_position_skips_row_only_profiles(self):
        """row_only profiles (time_only_clean, atr_only) have no tokens;
        per-position stats must return empty list, not raise."""
        from ML.baseline.benchmark_stage5_transformer_breach import compute_per_position_token_stats
        tokens = np.zeros((2, 0, 0), dtype=np.float32)
        mask = np.zeros((2, 0), dtype=bool)
        rows = compute_per_position_token_stats(tokens, mask, [])
        assert rows == []


class TestStage50aPreflightContracts:
    def test_preflight_profiles_exist(self):
        names = {p["name"] for p in define_profiles()}
        assert set(PREFLIGHT_PROFILE_NAMES).issubset(names)

    def test_time_only_clean_contains_only_calendar(self):
        profile = find_profile("time_only_clean")
        assert profile["token_fields"] == []
        assert profile["row_fields"] == ["hour_sin", "hour_cos", "dow_sin", "dow_cos"]
        assert "ATR" not in profile["row_fields"]

    def test_time_plus_atr_contains_calendar_and_atr(self):
        profile = find_profile("time_plus_atr")
        assert profile["token_fields"] == []
        assert profile["row_fields"] == ["ATR", "hour_sin", "hour_cos", "dow_sin", "dow_cos"]

    def test_profile_contract_fields_present(self):
        for profile_name in PREFLIGHT_PROFILE_NAMES:
            contract = get_profile_contract(find_profile(profile_name))
            assert set(contract.keys()) == {
                "name", "selection", "selector", "token_fields",
                "row_fields", "token_order", "seq_len",
                "padding_value", "mask_semantics", "diagnostic_only",
            }

    def test_full_corridor_no_time_profiles_exclude_atr_and_calendar(self):
        for profile_name in [
            "corridor_5atr_relative_price_no_time_full",
            "corridor_10atr_relative_price_no_time_full",
        ]:
            profile = find_profile(profile_name)
            assert profile["row_fields"] == []
            assert profile["seq_len"] == 100
            assert "price_coord_atr" in profile["token_fields"]

    def test_full_corridor_atr_profiles_keep_atr_row_field(self):
        for profile_name in [
            "corridor_5atr_relative_price_atr_full",
            "corridor_10atr_relative_price_atr_full",
        ]:
            profile = find_profile(profile_name)
            assert profile["row_fields"] == ["ATR"]
            assert profile["seq_len"] == 100
            assert "price_coord_atr" in profile["token_fields"]

    def test_full_corridor_contract_marks_diagnostic_only_only_for_row_dim_zero_profiles(self):
        assert get_profile_contract(find_profile("corridor_5atr_relative_price_no_time_full"))["diagnostic_only"] is True
        assert get_profile_contract(find_profile("corridor_10atr_relative_price_no_time_full"))["diagnostic_only"] is True
        assert get_profile_contract(find_profile("corridor_5atr_relative_price_atr_full"))["diagnostic_only"] is False

    def test_all100_profiles_order_by_freshness(self):
        for profile_name in [
            "all100_absolute_price_time",
            "all100_no_price_time",
            "all100_relative_price_no_time",
            "all100_relative_price_time",
        ]:
            profile = find_profile(profile_name)
            assert profile["selection"] == "all100"
            assert profile["order"] == "freshness"

    def test_corridor_profiles_anchor_first_then_distance(self):
        df = _make_synthetic_df(2, 100)
        profile = find_profile("corridor_10atr_relative_price_no_time")
        tokens, _, mask, _selection_meta = build_profile_features(df, profile)
        valid = tokens[0, mask[0]]
        assert len(valid) >= 1
        assert valid[0, 0] == pytest.approx(0.0, abs=1e-6)
        distances = np.abs(valid[:, 0])
        assert list(distances) == sorted(distances.tolist())

    def test_nearest40_excludes_anchor_and_tie_breaks_by_freshness(self):
        prices = np.array([100.0, 101.0, 99.0, 101.0, 99.0], dtype=np.float32)
        idx, mask, _ = TokenSelector.by_nearest(
            prices, 100.0, k=4, seq_len=4, exclude_anchor=True, anchor_valid_position=0
        )
        selected = idx[mask]
        assert 0 not in selected
        assert list(selected[:4]) == [1, 2, 3, 4]

    def test_relative_price_formula_matches_contract(self):
        df = _make_synthetic_df(3, 5)
        for i in range(len(df)):
            df.at[i, "ATR"] = 2.0
            df.at[i, "fractal0"] = _make_fractal_str([
                (0, 10_000_000), (1, 400.0), (2, -1), (3, 0.5), (4, 0.5),
                (5, 1), (6, 0), (7, 0), (8, 1), (9, 1), (10, 0.5),
            ])
            df.at[i, "fractal1"] = _make_fractal_str([
                (0, 10_000_000), (1, 410.0), (2, -1), (3, 0.5), (4, 0.5),
                (5, 1), (6, 0), (7, 0), (8, 1), (9, 1), (10, 0.5),
            ])
        profile = find_profile("all100_relative_price_time")
        tokens, _, mask, _selection_meta = build_profile_features(df, profile)
        valid_prices = tokens[0, mask[0], 0]
        # signed_log1p((400-400)/2)=0 (anchor), signed_log1p((410-400)/2)=signed_log1p(5)=1.7918
        assert valid_prices[0] == pytest.approx(0.0, abs=1e-6)
        assert valid_prices[1] == pytest.approx(1.7917595, abs=1e-4)

    def test_corridor_price_unit_atr_formula_matches_contract(self):
        df = _make_synthetic_df(1, 5)
        df.at[0, "ATR"] = 2.0
        df.at[0, "fractal0"] = _make_fractal_str([
            (0, 10_000_000), (1, 400.0), (2, -1), (3, 0.5), (4, 0.5),
            (5, 1), (6, 0), (7, 0), (8, 1), (9, 1), (10, 0.5),
        ])
        df.at[0, "fractal1"] = _make_fractal_str([
            (0, 10_000_000), (1, 410.0), (2, -1), (3, 0.5), (4, 0.5),
            (5, 1), (6, 0), (7, 0), (8, 1), (9, 1), (10, 0.5),
        ])
        for idx in range(2, 5):
            df.at[0, f"fractal{idx}"] = _make_fractal_str([
                (0, 10_000_000), (1, 1000.0 + idx), (2, -1), (3, 0.5), (4, 0.5),
                (5, 1), (6, 0), (7, 0), (8, 1), (9, 1), (10, 0.5),
            ])
        profile = find_profile("corridor_5atr_price_unit_atr_full")
        tokens, _, mask, _selection_meta = build_profile_features(df, profile)
        valid_prices = tokens[0, mask[0], 0]
        assert valid_prices[0] == pytest.approx(0.0, abs=1e-6)
        assert valid_prices[1] == pytest.approx(1.0, abs=1e-6)

    def test_absolute_price_atr_scaled_profiles_match_contract(self):
        import math
        df = _make_synthetic_df(1, 5)
        df.at[0, "ATR"] = 2.0
        df.at[0, "fractal0"] = _make_fractal_str([
            (0, 10_000_000), (1, 400.0), (2, -1), (3, 0.5), (4, 0.5),
            (5, 1), (6, 0), (7, 0), (8, 1), (9, 1), (10, 0.5),
        ])
        raw_profile = find_profile("all100_absolute_price_atr_scaled_time_raw")
        asinh_profile = find_profile("all100_absolute_price_atr_scaled_time_asinh")

        raw_tokens, _, raw_mask, _ = build_profile_features(df, raw_profile)
        asinh_tokens, _, asinh_mask, _ = build_profile_features(df, asinh_profile)

        assert raw_tokens[0, raw_mask[0], 0][0] == pytest.approx(200.0, abs=1e-6)
        assert asinh_tokens[0, asinh_mask[0], 0][0] == pytest.approx(math.asinh(200.0), abs=1e-6)

    def test_price_coord_atr_signed_log_edge_cases(self):
        """A7 signed-log transform for price_coord_atr: sign(x)*log1p(abs(x)).
        Edge cases: 0 -> 0; large positive -> log1p(x); symmetric for +/-.
        """
        import math
        df = _make_synthetic_df(2, 5)
        # row0: f0=400, f1=400 (price_coord=0), ATR=2.0
        # row1: f0=400, f1=600 (price_coord=(600-400)/2=100 -> signed_log1p(100)=4.6151)
        for i in range(len(df)):
            df.at[i, "ATR"] = 2.0
            df.at[i, "fractal0"] = _make_fractal_str([
                (0, 10_000_000), (1, 400.0), (2, -1), (3, 0.5), (4, 0.5),
                (5, 1), (6, 0), (7, 0), (8, 1), (9, 1), (10, 0.5),
            ])
        df.at[0, "fractal1"] = _make_fractal_str([
            (0, 10_000_000), (1, 400.0), (2, -1), (3, 0.5), (4, 0.5),
            (5, 1), (6, 0), (7, 0), (8, 1), (9, 1), (10, 0.5),
        ])
        df.at[1, "fractal1"] = _make_fractal_str([
            (0, 10_000_000), (1, 600.0), (2, -1), (3, 0.5), (4, 0.5),
            (5, 1), (6, 0), (7, 0), (8, 1), (9, 1), (10, 0.5),
        ])
        profile = find_profile("all100_relative_price_time")
        tokens, _, mask, _ = build_profile_features(df, profile)
        # row0 pos1: signed_log1p((400-400)/2) = signed_log1p(0) = 0
        r0_valid = tokens[0, mask[0], 0]
        assert r0_valid[1] == pytest.approx(0.0, abs=1e-6)
        # row1 pos1: signed_log1p((600-400)/2) = signed_log1p(100) = 4.6151205
        r1_valid = tokens[1, mask[1], 0]
        assert r1_valid[1] == pytest.approx(math.log1p(100.0), abs=1e-4)

    def test_corridor_profiles_respect_declared_boundaries(self):
        df = _make_synthetic_df(4, 100)
        for profile_name, limit in [
            ("corridor_5atr_relative_price_no_time", 5.0),
            ("corridor_10atr_relative_price_no_time", 10.0),
            ("corridor_15atr_relative_price_no_time", 15.0),
        ]:
            profile = find_profile(profile_name)
            tokens, _, mask, _selection_meta = build_profile_features(df, profile)
            # price_coord_atr is signed-log transformed in tokens; recover RAW
            # bounds via inverse raw = sign(x)*expm1(abs(x)) for A7 corridor check.
            signed_log_vals = tokens[:, :, 0][mask]
            if len(signed_log_vals) > 0:
                raw_vals = np.sign(signed_log_vals) * np.expm1(np.abs(signed_log_vals))
                assert np.max(np.abs(raw_vals)) <= limit + 1e-6, \
                    f"{profile_name}: raw |price_coord_atr|={np.max(np.abs(raw_vals))} > {limit}"

    def test_row_only_profiles_have_empty_tokens(self):
        df = _make_synthetic_df(5, 10)
        for profile_name, row_dim in [
            ("time_only_clean", 4),
            ("atr_only", 1),
            ("time_plus_atr", 5),
        ]:
            profile = find_profile(profile_name)
            tokens, row_features, mask, _selection_meta = build_profile_features(df, profile)
            assert tokens.shape == (5, 0, 0)
            assert mask.shape == (5, 0)
            assert row_features.shape == (5, row_dim)

    def test_normalization_keeps_padding_zero_for_preflight_profiles(self):
        df = _make_synthetic_df(6, 100)
        profile = find_profile("nearest40_relative_price_time")
        tokens, row_features, mask, _selection_meta = build_profile_features(df, profile)
        (t_train, _, _, _, _, _), _stats = normalize_profile_features(
            tokens, row_features, mask,
            tokens, row_features, mask,
            tokens, row_features, mask,
        )
        assert np.allclose(t_train[~mask], 0.0)

    def test_full_corridor_no_time_profiles_have_zero_row_dim(self):
        df = _make_synthetic_df(3, 100)
        for profile_name in [
            "corridor_5atr_relative_price_no_time_full",
            "corridor_10atr_relative_price_no_time_full",
        ]:
            profile = find_profile(profile_name)
            tokens, row_features, mask, _selection_meta = build_profile_features(df, profile)
            assert tokens.shape == (3, 100, 10)
            assert row_features.shape == (3, 0)
            assert mask.shape == (3, 100)

    def test_full_corridor_can_select_more_than_40_fractals(self):
        df = _make_ordered_corridor_df(n_rows=2, n_fractals=100, step=0.1, atr=1.0)
        profile = find_profile("corridor_10atr_relative_price_no_time_full")
        tokens, _, mask, selection_meta = build_profile_features(df, profile)
        assert tokens.shape == (2, 100, 10)
        assert int(selection_meta["candidate_count_before_cap"][0]) == 100
        assert int(selection_meta["selected_count_after_cap"][0]) == 100
        assert int(mask[0].sum()) == 100


class TestCorridorCoverageMeta:
    def test_candidate_count_equal_seq_len_is_not_truncated(self):
        profile = find_profile("corridor_10atr_relative_price_no_time_full")
        counts = np.array([100, 100], dtype=np.int32)
        selected = np.array([100, 100], dtype=np.int32)
        meta = {
            "candidate_count_before_cap": counts,
            "selected_count_after_cap": selected,
            "is_truncated": counts > profile["seq_len"],
        }
        coverage = compute_profile_coverage(
            np.zeros((2, 100, 10), dtype=np.float32),
            np.ones((2, 100), dtype=bool),
            profile,
            meta,
        )
        assert coverage["pct_truncation_true"] == 0.0

    def test_candidate_count_above_seq_len_is_truncated(self):
        profile = find_profile("corridor_10atr_relative_price_no_time")
        counts = np.array([41, 60], dtype=np.int32)
        selected = np.array([40, 40], dtype=np.int32)
        meta = {
            "candidate_count_before_cap": counts,
            "selected_count_after_cap": selected,
            "is_truncated": counts > profile["seq_len"],
        }
        coverage = compute_profile_coverage(
            np.zeros((2, 40, 10), dtype=np.float32),
            np.ones((2, 40), dtype=bool),
            profile,
            meta,
        )
        assert coverage["pct_truncation_true"] == 1.0

    def test_seq_len_100_truncation_is_not_based_on_selected_equals_seq_len(self):
        df = _make_ordered_corridor_df(n_rows=2, n_fractals=100, step=0.1, atr=1.0)
        profile = find_profile("corridor_5atr_relative_price_no_time_full")
        tokens, _, mask, selection_meta = build_profile_features(df, profile)
        coverage = compute_profile_coverage(tokens, mask, profile, selection_meta)
        assert int(selection_meta["candidate_count_before_cap"][0]) == 51
        assert int(selection_meta["selected_count_after_cap"][0]) == 51
        assert coverage["pct_truncation_true"] == 0.0
        assert coverage["candidate_count_before_cap_p50"] == pytest.approx(51.0)


def test_stage5_0b_profile_sets_are_frozen_and_separated():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_0B_CONFIRMATORY_PROFILE_NAMES == [
        "all100_relative_price_time",
        "nearest40_relative_price_time",
        "corridor_5atr_relative_price_atr_full",
        "corridor_10atr_relative_price_atr_full",
    ]
    assert runner.STAGE5_0B_DIAGNOSTIC_PROFILE_NAMES == [
        "all100_relative_price_no_time",
        "nearest40_relative_price_no_time",
        "all100_absolute_price_atr_scaled_time_asinh",
        "corridor_5atr_price_unit_atr_full",
        "corridor_10atr_price_unit_atr_full",
    ]
    assert runner.STAGE5_0B_ASINH_PROFILE_NAMES == (
        runner.STAGE5_0B_CONFIRMATORY_PROFILE_NAMES
        + runner.STAGE5_0B_DIAGNOSTIC_PROFILE_NAMES
    )
    for profile_name in runner.STAGE5_0B_ASINH_PROFILE_NAMES:
        assert runner.find_profile(profile_name) is not None


def test_train_eval_profile_passes_asinh_to_feature_builder(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    calls = []
    df = _make_synthetic_df(3, 100)
    df["_year"] = [2020, 2020, 2020]
    y = df[runner.TARGET_COLUMN]
    report = {"transformer_results": {}}

    def fake_build(df_arg, parsed_arg, profile_arg, transform_variant="current", transform_params=None):
        calls.append(transform_variant)
        n = len(df_arg)
        return (
            np.zeros((n, 2, 1), dtype=np.float32),
            np.zeros((n, 1), dtype=np.float32),
            np.ones((n, 2), dtype=bool),
            {
                "candidate_count_before_cap": np.zeros(n, dtype=np.int32),
                "selected_count_after_cap": np.zeros(n, dtype=np.int32),
                "is_truncated": np.zeros(n, dtype=bool),
            },
        )

    class DummyModel:
        def eval(self):
            pass

    monkeypatch.setattr(runner, "build_profile_features_from_parsed", fake_build)
    monkeypatch.setattr(
        runner,
        "normalize_profile_features",
        lambda *args: ((args[0], args[1], args[3], args[4], args[6], args[7]), {}),
    )
    monkeypatch.setattr(
        runner,
        "audit_normalized_distribution",
        lambda *args, **kwargs: {"status": "OK", "flags": [], "by_split": {}},
    )
    monkeypatch.setattr(
        runner,
        "train_transformer",
        lambda *args, **kwargs: (DummyModel(), {"best_val_auc": 0.5, "num_epochs": 1}),
    )
    monkeypatch.setattr(
        runner,
        "evaluate_transformer",
        lambda *args, **kwargs: np.array([0.1, 0.2, 0.3], dtype=np.float32),
    )
    monkeypatch.setattr(
        runner,
        "compute_metrics",
        lambda y_true, pred: {
            "auc": 0.5,
            "pr_auc": 0.5,
            "n": len(y_true),
            "lift_10": 1.0,
            "lift_20": 1.0,
            "lift_30": 1.0,
        },
    )
    monkeypatch.setattr(runner, "compute_yearly_metrics", lambda df_arg, pred, target_col=runner.TARGET_COLUMN: {})

    parsed = {
        "train": runner.parse_split_fractals(df),
        "val_stop": runner.parse_split_fractals(df),
        "holdout": runner.parse_split_fractals(df),
    }
    runner._train_and_eval_profile(
        df,
        df,
        df,
        42,
        "cpu",
        report,
        "all100_relative_price_time",
        y,
        y,
        y,
        transform_variant="asinh",
        parsed_splits=parsed,
        allow_dynamic_seq_len=False,
    )

    assert calls == ["asinh", "asinh", "asinh"]
    result = report["transformer_results"]["all100_relative_price_time"][0]
    assert result["transform_variant"] == "asinh"
    assert result["training_run"] is True


def test_stage5_0b_can_disable_dynamic_corridor_seq_len(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    observed_seq_lens = []
    df = _make_synthetic_df(3, 100)
    df["_year"] = [2020, 2020, 2020]
    y = df[runner.TARGET_COLUMN]
    report = {"transformer_results": {}}

    monkeypatch.setattr(
        runner,
        "compute_corridor_stats",
        lambda df_arg, profile: {"n_fractals_median": 10, "n_fractals_p80": 10},
    )
    monkeypatch.setattr(runner, "corridor_status", lambda stats: "OK")

    def fake_build(df_arg, parsed_arg, profile_arg, transform_variant="current", transform_params=None):
        observed_seq_lens.append(profile_arg["seq_len"])
        n = len(df_arg)
        return (
            np.zeros((n, profile_arg["seq_len"], 1), dtype=np.float32),
            np.zeros((n, 1), dtype=np.float32),
            np.ones((n, profile_arg["seq_len"]), dtype=bool),
            {
                "candidate_count_before_cap": np.zeros(n, dtype=np.int32),
                "selected_count_after_cap": np.zeros(n, dtype=np.int32),
                "is_truncated": np.zeros(n, dtype=bool),
            },
        )

    class DummyModel:
        def eval(self):
            pass

    monkeypatch.setattr(runner, "build_profile_features_from_parsed", fake_build)
    monkeypatch.setattr(
        runner,
        "normalize_profile_features",
        lambda *args: ((args[0], args[1], args[3], args[4], args[6], args[7]), {}),
    )
    monkeypatch.setattr(
        runner,
        "audit_normalized_distribution",
        lambda *args, **kwargs: {"status": "OK", "flags": [], "by_split": {}},
    )
    monkeypatch.setattr(
        runner,
        "train_transformer",
        lambda *args, **kwargs: (DummyModel(), {"best_val_auc": 0.5, "num_epochs": 1}),
    )
    monkeypatch.setattr(
        runner,
        "evaluate_transformer",
        lambda *args, **kwargs: np.array([0.1, 0.2, 0.3], dtype=np.float32),
    )
    monkeypatch.setattr(
        runner,
        "compute_metrics",
        lambda y_true, pred: {
            "auc": 0.5,
            "pr_auc": 0.5,
            "n": len(y_true),
            "lift_10": 1.0,
            "lift_20": 1.0,
            "lift_30": 1.0,
        },
    )
    monkeypatch.setattr(runner, "compute_yearly_metrics", lambda df_arg, pred, target_col=runner.TARGET_COLUMN: {})

    parsed = {
        "train": runner.parse_split_fractals(df),
        "val_stop": runner.parse_split_fractals(df),
        "holdout": runner.parse_split_fractals(df),
    }
    runner._train_and_eval_profile(
        df,
        df,
        df,
        42,
        "cpu",
        report,
        "corridor_5atr_relative_price_atr_full",
        y,
        y,
        y,
        transform_variant="asinh",
        parsed_splits=parsed,
        allow_dynamic_seq_len=False,
    )

    assert observed_seq_lens == [100, 100, 100]


def test_find_buy_stop_target_columns_returns_sorted_candidates():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = pd.DataFrame(
        {
            "buy_stop_broken_H6_off05_flag": [0, 1],
            "sell_stop_broken_H6_off05_flag": [1, 0],
            "buy_stop_broken_H12_off05_flag": [0, 0],
        }
    )
    assert runner.find_buy_stop_target_columns(df) == [
        "buy_stop_broken_H12_off05_flag",
        "buy_stop_broken_H6_off05_flag",
    ]


def test_summarize_target_contract_reports_balance_and_nulls_for_sell_and_buy():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    train = pd.DataFrame({"sell_stop_broken_H6_off05_flag": [0, 1, 1, None]})
    val = pd.DataFrame({"sell_stop_broken_H6_off05_flag": [0, 0, 1]})
    result = runner.summarize_target_contract(
        {"train": train, "val_stop": val},
        "sell_stop_broken_H6_off05_flag",
    )
    assert result["target"] == "sell_stop_broken_H6_off05_flag"
    assert result["splits"]["train"]["exists"] is True
    assert result["splits"]["train"]["n_rows"] == 4
    assert result["splits"]["train"]["n_non_null"] == 3
    assert result["splits"]["train"]["positive_rate"] == pytest.approx(2 / 3)


def test_load_splits_filters_by_requested_target(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    def make_frame(years, buy_vals, sell_vals):
        rows = []
        for i, (year, buy_val, sell_val) in enumerate(zip(years, buy_vals, sell_vals)):
            rows.append(
                {
                    "time": f"{year}.01.{i + 1:02d} 12:00",
                    "signal": 1 if pd.notna(buy_val) else -1,
                    "ATR": 1.0,
                    "fractal0": _make_fractal_str([(1, 100.0), (2, -1 if pd.notna(buy_val) else 1)]),
                    "buy_stop_broken_H6_off05_flag": buy_val,
                    "sell_stop_broken_H6_off05_flag": sell_val,
                }
            )
        return pd.DataFrame(rows)

    frames = [
        make_frame([2020, 2020], [1.0, np.nan], [np.nan, 0.0]),
        make_frame([2021, 2021], [0.0, np.nan], [np.nan, 1.0]),
        make_frame([2023, 2023], [1.0, np.nan], [np.nan, 0.0]),
    ]
    calls = iter(frames)
    monkeypatch.setattr(runner.pd, "read_csv", lambda *args, **kwargs: next(calls).copy())

    train, val_stop, holdout = runner.load_splits(target_col="buy_stop_broken_H6_off05_flag")

    assert train["buy_stop_broken_H6_off05_flag"].notna().all()
    assert val_stop["buy_stop_broken_H6_off05_flag"].notna().all()
    assert holdout["buy_stop_broken_H6_off05_flag"].notna().all()
    assert train["sell_stop_broken_H6_off05_flag"].isna().all()
    assert val_stop["sell_stop_broken_H6_off05_flag"].isna().all()
    assert holdout["sell_stop_broken_H6_off05_flag"].isna().all()


def test_stage5_0b_runner_records_checks_baselines_and_profile_roles(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    calls = []
    df = _make_synthetic_df(3, 100)
    df["_year"] = [2020, 2020, 2020]
    ohlc = {"status": "PASS"}
    sanity = {"status": "PASS", "positive_rate": 0.5}
    xgb = {
        "base_raw_plus_time": {"val": {"auc": 0.5, "lift_30": 1.0}},
        "time_only": {"val": {"auc": 0.5, "lift_30": 1.0}},
    }

    def fake_train(
        train_df,
        val_df,
        hold_df,
        seed,
        device,
        report,
        pname,
        y_train,
        y_val,
        y_holdout,
        diagnostic_only=False,
        transform_variant="current",
        parsed_splits=None,
        allow_dynamic_seq_len=True,
        profile_role="legacy",
        target_col=runner.TARGET_COLUMN,
    ):
        calls.append((pname, transform_variant, allow_dynamic_seq_len, profile_role))
        report["transformer_results"].setdefault(pname, []).append(
            {
                "profile": pname,
                "seed": seed,
                "transform_variant": transform_variant,
                "profile_role": profile_role,
                "training_run": True,
                "normalized_distribution_audit": {"status": "OK"},
                "val": {"auc": 0.51, "lift_30": 0.9},
                "holdout": {"auc": 0.51, "lift_30": 0.9},
                "yearly": {},
            }
        )
        return 1.0

    monkeypatch.setattr(runner, "_train_and_eval_profile", fake_train)
    report = runner.run_stage5_0b_asinh_rerun(
        df,
        df,
        df,
        seed=42,
        device="cpu",
        ohlc_verification=ohlc,
        label_sanity=sanity,
        xgb_results=xgb,
        output_path=tmp_path / "stage5_0b_asinh_rerun.json",
    )

    assert report["status"] == "DIAGNOSTIC_ONLY"
    assert report["no_trading_winner_declared"] is True
    assert report["ohlc_verification"] == ohlc
    assert report["label_sanity"] == sanity
    assert report["xgb_baselines"] == xgb
    assert report["decision_policy"]["holdout_usage"] == "disclosure only"
    assert {c[1] for c in calls} == {"asinh"}
    assert {c[2] for c in calls} == {False}
    assert calls[0][3] == "confirmatory"
    assert calls[-1][3] == "diagnostic_control"
    assert (tmp_path / "stage5_0b_asinh_rerun.json").exists()


def test_stage5_0b_runner_can_promote_all_profiles_and_disable_gates(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(3, 100)
    df["_year"] = [2020, 2020, 2020]
    df["buy_stop_broken_H6_off05_flag"] = [0, 1, 0]
    roles = []
    xgb = {
        "base_raw_plus_time": {"val": {"auc": 0.9, "lift_30": 0.5}},
        "time_only": {"val": {"auc": 0.9, "lift_30": 0.5}},
    }

    def fake_train(
        train_df,
        val_df,
        hold_df,
        seed,
        device,
        report,
        pname,
        y_train,
        y_val,
        y_holdout,
        diagnostic_only=False,
        transform_variant="current",
        parsed_splits=None,
        allow_dynamic_seq_len=True,
        profile_role="legacy",
        target_col=runner.TARGET_COLUMN,
    ):
        roles.append(profile_role)
        assert target_col == "buy_stop_broken_H6_off05_flag"
        report["transformer_results"].setdefault(pname, []).append(
            {
                "profile": pname,
                "seed": seed,
                "transform_variant": transform_variant,
                "profile_role": profile_role,
                "training_run": True,
                "normalized_distribution_audit": {"status": "OK"},
                "val": {"auc": 0.1, "lift_30": 2.0},
                "holdout": {"auc": 0.1, "lift_30": 2.0},
                "yearly": {},
            }
        )

    monkeypatch.setattr(runner, "_train_and_eval_profile", fake_train)
    report = runner.run_stage5_0b_asinh_rerun(
        df,
        df,
        df,
        seed=42,
        device="cpu",
        ohlc_verification={"status": "PASS"},
        label_sanity={"status": "PASS"},
        xgb_results=xgb,
        output_path=tmp_path / "buy.json",
        target_col="buy_stop_broken_H6_off05_flag",
        all_profiles_confirmatory=True,
        use_multiseed_gates=False,
    )

    assert set(roles) == {"confirmatory"}
    assert report["diagnostic_control_profiles"] == []
    assert report["target"] == "buy_stop_broken_H6_off05_flag"
    assert report["target_contracts"]["trained"]["target"] == "buy_stop_broken_H6_off05_flag"
    assert report["decision_policy"]["multi_seed_rules"]["status"].startswith("disabled")
    first = report["transformer_results"][runner.STAGE5_0B_ASINH_PROFILE_NAMES[0]][0]
    assert first["multi_seed_decision"]["reason"] == "selection_gates_disabled"


def test_train_eval_profile_preserves_legacy_full29_builder(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(3, 100)
    df["_year"] = [2020, 2020, 2020]
    y = df[runner.TARGET_COLUMN]
    report = {"transformer_results": {}}
    direct_calls = []

    def fail_parsed(*args, **kwargs):
        raise AssertionError("full29 legacy profile must not use parsed base10 builder")

    def fake_direct(df_arg, profile_arg, transform_variant="current", transform_params=None):
        direct_calls.append((profile_arg["name"], transform_variant))
        n = len(df_arg)
        seq_len = profile_arg["seq_len"]
        token_dim = profile_arg["token_dim"]
        row_dim = profile_arg["row_dim"]
        return (
            np.zeros((n, seq_len, token_dim), dtype=np.float32),
            np.zeros((n, row_dim), dtype=np.float32),
            np.ones((n, seq_len), dtype=bool),
            {
                "candidate_count_before_cap": np.full(n, seq_len, dtype=np.int32),
                "selected_count_after_cap": np.full(n, seq_len, dtype=np.int32),
                "is_truncated": np.zeros(n, dtype=bool),
            },
        )

    class DummyModel:
        def eval(self):
            pass

    monkeypatch.setattr(runner, "build_profile_features_from_parsed", fail_parsed)
    monkeypatch.setattr(runner, "build_profile_features", fake_direct)
    monkeypatch.setattr(
        runner,
        "normalize_profile_features",
        lambda *args: ((args[0], args[1], args[3], args[4], args[6], args[7]), {}),
    )
    monkeypatch.setattr(
        runner,
        "audit_normalized_distribution",
        lambda *args, **kwargs: {"status": "OK", "flags": [], "by_split": {}},
    )
    monkeypatch.setattr(
        runner,
        "train_transformer",
        lambda *args, **kwargs: (DummyModel(), {"best_val_auc": 0.5, "num_epochs": 1}),
    )
    monkeypatch.setattr(
        runner,
        "evaluate_transformer",
        lambda *args, **kwargs: np.array([0.1, 0.2, 0.3], dtype=np.float32),
    )
    monkeypatch.setattr(
        runner,
        "compute_metrics",
        lambda y_true, pred: {
            "auc": 0.5,
            "pr_auc": 0.5,
            "n": len(y_true),
            "lift_10": 1.0,
            "lift_20": 1.0,
            "lift_30": 1.0,
        },
    )
    monkeypatch.setattr(runner, "compute_yearly_metrics", lambda df_arg, pred, target_col=runner.TARGET_COLUMN: {})

    runner._train_and_eval_profile(
        df,
        df,
        df,
        42,
        "cpu",
        report,
        "all100_full29_time",
        y,
        y,
        y,
    )

    assert direct_calls == [
        ("all100_full29_time", "current"),
        ("all100_full29_time", "current"),
        ("all100_full29_time", "current"),
    ]


# ───────────────────────────────────────────────────────────────────────────
# Stage 5.0c tests
# ───────────────────────────────────────────────────────────────────────────

def test_build_flat_features_passes_transform_variant_to_builder(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    captured = {}

    def fake_build(df_arg, profile_arg, transform_variant="current", transform_params=None):
        captured["transform_variant"] = transform_variant
        captured["transform_params"] = transform_params
        n = len(df_arg)
        return (
            np.zeros((n, 5, 2), dtype=np.float32),
            np.zeros((n, 1), dtype=np.float32),
            np.ones((n, 5), dtype=bool),
            {},
        )

    monkeypatch.setattr(runner, "build_profile_features", fake_build)
    df = _make_synthetic_df(3, 10)
    profile = runner.find_profile("all100_absolute_price_atr_scaled_time_asinh")
    runner.build_flat_features(df, profile, transform_variant="asinh", transform_params={"foo": 1})
    assert captured["transform_variant"] == "asinh"
    assert captured["transform_params"] == {"foo": 1}


def test_build_xgb_features_for_profile_returns_expected_shape():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(4, 100)
    X = runner.build_xgb_features_for_profile(
        df, "all100_absolute_price_atr_scaled_time_asinh", transform_variant="asinh")
    profile = runner.find_profile("all100_absolute_price_atr_scaled_time_asinh")
    expected_dim = profile["seq_len"] * profile["token_dim"] + profile["row_dim"]
    assert X.shape == (4, expected_dim)
    assert X.dtype == np.float32
    assert np.isfinite(X).all()


def test_compute_xgb_same_profile_baseline_returns_val_and_holdout_metrics(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner
    import sys

    df = _make_synthetic_df(10, 100)
    df["_year"] = [2020] * 5 + [2023] * 5

    class _FakeModel:
        def predict(self, dm):
            return np.array([0.5] * len(dm))

    class _FakeDMatrix:
        def __init__(self, data):
            self._data = data
        def __len__(self):
            return len(self._data)

    if "xgboost" in sys.modules:
        monkeypatch.setattr(sys.modules["xgboost"], "DMatrix", _FakeDMatrix)

    monkeypatch.setattr(runner, "build_xgb_features_for_profile",
                        lambda d, pname, tv, transform_params=None: np.random.rand(len(d), 10).astype(np.float32))
    monkeypatch.setattr(runner, "fit_transform_params_for_profile",
                        lambda df, parsed, profile, variant: {})
    monkeypatch.setattr(runner, "parse_split_fractals", lambda df: {})
    monkeypatch.setattr(runner, "find_profile",
                        lambda name: {"seq_len": 1, "token_dim": 5, "row_dim": 5})
    monkeypatch.setattr(runner, "train_xgb_baseline",
                        lambda Xtr, ytr, Xv, yv, seed=42: (_FakeModel(), 0.6))
    monkeypatch.setattr(runner, "compute_metrics",
                        lambda yt, yp: {"auc": 0.6, "pr_auc": 0.5, "n": len(yt),
                                        "lift_10": 1.0, "lift_20": 1.0, "lift_30": 0.8})
    monkeypatch.setattr(runner, "compute_yearly_metrics", lambda df_arg, pred, target_col=None: {})

    result = runner.compute_xgb_same_profile_baseline(
        df.iloc[:5], df.iloc[:5], df.iloc[5:],
        "all100_absolute_price_atr_scaled_time_asinh",
        transform_variant="asinh", target_col=runner.TARGET_COLUMN, seed=42)
    assert "val" in result and "holdout" in result
    assert result["val"]["auc"] == 0.6
    assert result["holdout"]["auc"] == 0.6
    assert result["profile"] == "all100_absolute_price_atr_scaled_time_asinh"
    assert result["transform_variant"] == "asinh"
    assert result["transform_params_fit_on"] == "train"


def test_stage5_0c_constants_are_frozen():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_0C_PROFILE_NAME == "all100_absolute_price_atr_scaled_time_asinh"
    assert runner.STAGE5_0C_TARGETS == [
        "sell_stop_broken_H6_off05_flag",
        "buy_stop_broken_H6_off05_flag",
    ]
    assert runner.STAGE5_0C_SEEDS == [42, 77, 123, 202, 777]
    gates = runner.STAGE5_0C_GATES
    assert gates["g1_auc"]["median_above_xgb"] is True
    assert gates["g1_auc"]["min_seeds_above_xgb_minus_tol"] == 4
    assert gates["g1_auc"]["tolerance"] == 0.005
    assert gates["g2_lift30"]["median_below_xgb"] is True
    assert gates["g3_cross_target"]["both_targets_required"] is True
    assert gates["g5_seed_spread"]["max_range"] == 0.03
    assert "g4_holdout_degradation" not in gates
    holdout_check = runner.STAGE5_0C_HOLDOUT_CHECK
    assert holdout_check["max_drop"] == 0.05
    assert holdout_check["enters_overall_pass"] is False
    assert runner.find_profile(runner.STAGE5_0C_PROFILE_NAME) is not None


def test_stage5_0c_replication_decision_all_gates_pass():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    def make_target(xgb_auc, xgb_lift, seed_aucs, seed_lifts, holdout_aucs):
        return {
            "xgb_same_profile": {"val": {"auc": xgb_auc, "lift_30": xgb_lift}},
            "seed_metrics": [
                {"val": {"auc": a, "lift_30": l}, "holdout": {"auc": h}}
                for a, l, h in zip(seed_aucs, seed_lifts, holdout_aucs)
            ],
        }

    target_results = {
        "sell": make_target(
            xgb_auc=0.65, xgb_lift=0.60,
            seed_aucs=[0.66, 0.67, 0.67, 0.66, 0.67],
            seed_lifts=[0.55, 0.56, 0.54, 0.57, 0.56],
            holdout_aucs=[0.64, 0.65, 0.66, 0.63, 0.65]),
        "buy": make_target(
            xgb_auc=0.67, xgb_lift=0.58,
            seed_aucs=[0.68, 0.69, 0.69, 0.68, 0.69],
            seed_lifts=[0.53, 0.54, 0.52, 0.55, 0.54],
            holdout_aucs=[0.66, 0.67, 0.68, 0.65, 0.67]),
    }
    decision = runner.stage5_0c_replication_decision(target_results)
    assert decision["overall_pass"] is True
    assert decision["g1_auc"]["pass"] is True
    assert decision["g2_lift30"]["pass"] is True
    assert decision["g3_cross_target"]["pass"] is True
    assert decision["g5_seed_spread"]["pass"] is True
    assert decision["holdout_check"]["status"] == "OK"
    assert "holdout_check" not in decision["overall_pass_components"]
    assert decision["sell_pass"] is True
    assert decision["buy_pass"] is True
    assert decision["cross_target_pass"] is True


def test_stage5_0c_replication_decision_cross_target_fail_when_one_target_fails():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    def make_target(xgb_auc, xgb_lift, seed_aucs, seed_lifts, holdout_aucs):
        return {
            "xgb_same_profile": {"val": {"auc": xgb_auc, "lift_30": xgb_lift}},
            "seed_metrics": [
                {"val": {"auc": a, "lift_30": l}, "holdout": {"auc": h}}
                for a, l, h in zip(seed_aucs, seed_lifts, holdout_aucs)
            ],
        }

    target_results = {
        "sell": make_target(
            xgb_auc=0.65, xgb_lift=0.60,
            seed_aucs=[0.66, 0.67, 0.67, 0.66, 0.67],
            seed_lifts=[0.55, 0.56, 0.54, 0.57, 0.56],
            holdout_aucs=[0.64, 0.65, 0.66, 0.63, 0.65]),
        "buy": make_target(
            xgb_auc=0.75, xgb_lift=0.50,
            seed_aucs=[0.68, 0.69, 0.70, 0.67, 0.68],
            seed_lifts=[0.53, 0.54, 0.52, 0.55, 0.54],
            holdout_aucs=[0.66, 0.67, 0.68, 0.65, 0.67]),
    }
    decision = runner.stage5_0c_replication_decision(target_results)
    assert decision["overall_pass"] is False
    assert decision["g1_auc"]["sell"]["pass"] is True
    assert decision["g1_auc"]["buy"]["pass"] is False
    assert decision["g3_cross_target"]["pass"] is False
    assert decision["sell_pass"] is True
    assert decision["buy_pass"] is False
    assert decision["cross_target_pass"] is False


def test_stage5_0c_replication_decision_seed_spread_fail():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    def make_target(xgb_auc, xgb_lift, seed_aucs, seed_lifts, holdout_aucs):
        return {
            "xgb_same_profile": {"val": {"auc": xgb_auc, "lift_30": xgb_lift}},
            "seed_metrics": [
                {"val": {"auc": a, "lift_30": l}, "holdout": {"auc": h}}
                for a, l, h in zip(seed_aucs, seed_lifts, holdout_aucs)
            ],
        }

    target_results = {
        "sell": make_target(
            xgb_auc=0.60, xgb_lift=0.70,
            seed_aucs=[0.62, 0.68, 0.55, 0.66, 0.67],
            seed_lifts=[0.55, 0.56, 0.54, 0.57, 0.56],
            holdout_aucs=[0.60, 0.60, 0.60, 0.60, 0.60]),
        "buy": make_target(
            xgb_auc=0.60, xgb_lift=0.70,
            seed_aucs=[0.62, 0.63, 0.64, 0.61, 0.62],
            seed_lifts=[0.55, 0.56, 0.54, 0.57, 0.56],
            holdout_aucs=[0.60, 0.60, 0.60, 0.60, 0.60]),
    }
    decision = runner.stage5_0c_replication_decision(target_results)
    assert decision["overall_pass"] is False
    assert decision["g5_seed_spread"]["sell"]["range"] >= 0.03
    assert decision["g5_seed_spread"]["pass"] is False


def test_stage5_0c_runner_trains_both_targets_and_applies_replication_decision(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    transformer_calls = []
    xgb_calls = []

    df_sell = _make_synthetic_df(5, 100)
    df_sell["_year"] = [2020] * 5
    df_buy = df_sell.copy()
    df_buy["buy_stop_broken_H6_off05_flag"] = [0, 1, 0, 1, 0]

    def fake_train(train_df, val_df, hold_df, seed, device, report,
                   pname, y_train, y_val, y_holdout,
                   diagnostic_only=False, transform_variant="current",
                   parsed_splits=None, allow_dynamic_seq_len=True,
                   profile_role="legacy", target_col=runner.TARGET_COLUMN):
        transformer_calls.append((target_col, transform_variant, seed, profile_role))
        report["transformer_results"].setdefault(pname, []).append({
            "profile": pname,
            "seed": seed,
            "transform_variant": transform_variant,
            "profile_role": profile_role,
            "training_run": True,
            "normalized_distribution_audit": {"status": "OK", "flags": []},
            "val": {"auc": 0.70, "lift_30": 0.50, "pr_auc": 0.6, "n": 5,
                    "lift_10": 1.0, "lift_20": 1.0},
            "holdout": {"auc": 0.68, "lift_30": 0.55, "pr_auc": 0.6, "n": 5,
                        "lift_10": 1.0, "lift_20": 1.0},
            "yearly": {},
        })
        return 1.0

    def fake_xgb_same(train_df, val_df, hold_df, profile_name,
                      transform_variant="asinh", target_col=runner.TARGET_COLUMN, seed=42):
        xgb_calls.append((target_col, profile_name, transform_variant))
        return {
            "profile": profile_name,
            "transform_variant": transform_variant,
            "seed": seed,
            "val": {"auc": 0.65, "lift_30": 0.60, "pr_auc": 0.6, "n": 5,
                    "lift_10": 1.0, "lift_20": 1.0},
            "holdout": {"auc": 0.63, "lift_30": 0.65, "pr_auc": 0.6, "n": 5,
                        "lift_10": 1.0, "lift_20": 1.0},
            "yearly": {},
        }

    monkeypatch.setattr(runner, "_train_and_eval_profile", fake_train)
    monkeypatch.setattr(runner, "compute_xgb_same_profile_baseline", fake_xgb_same)
    monkeypatch.setattr(runner, "compute_xgb_baselines",
                        lambda tr, va, ho, target_col=runner.TARGET_COLUMN: {
                            "base_raw_plus_time": {"val": {"auc": 0.6, "lift_30": 0.7}},
                            "no_time": {"val": {"auc": 0.55, "lift_30": 0.8}},
                            "time_only": {"val": {"auc": 0.58, "lift_30": 0.75}},
                        })
    monkeypatch.setattr(runner, "verify_breach_labels_against_ohlc",
                        lambda df, target_col: {"status": "PASS", "n_matches": 50, "n_checked": 50, "n_mismatches": 0})
    monkeypatch.setattr(runner, "label_sanity_check",
                        lambda df, target_col=runner.TARGET_COLUMN: {"status": "SANITY_ONLY", "positive_rate": 0.4})

    report = runner.run_stage5_0c_cross_target_rerun(
        sell_splits=(df_sell, df_sell, df_sell),
        buy_splits=(df_buy, df_buy, df_buy),
        seeds=[42, 77],
        device="cpu",
        output_path=tmp_path / "stage5_0c.json",
    )

    assert report["status"] == "DIAGNOSTIC_ONLY"
    assert report["stage"] == "5.0c_cross_target_rerun"
    assert report["profile"] == runner.STAGE5_0C_PROFILE_NAME
    assert report["framing"] == "replication_test_of_5_0b_hypothesis"
    assert report["no_trading_winner_declared"] is True
    assert report["holdout_used_for_decision"] is False
    assert "sell" in report["targets"] and "buy" in report["targets"]
    assert len(report["targets"]["sell"]["transformer_results"][runner.STAGE5_0C_PROFILE_NAME]) == 2
    assert {c[0] for c in transformer_calls} == {"sell_stop_broken_H6_off05_flag", "buy_stop_broken_H6_off05_flag"}
    assert {c[1] for c in transformer_calls} == {"asinh"}
    assert "replication_decision" in report
    assert "overall_pass" in report["replication_decision"]
    assert (tmp_path / "stage5_0c.json").exists()


def test_stage5_0c_cli_argument_exists_in_build_arg_parser():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = runner.build_arg_parser()
    args = parser.parse_args(["--stage5-0c-cross-target-rerun"])
    assert args.stage5_0c_cross_target_rerun is True


# ───────────────────────────────────────────────────────────────────────────
# Stage 5.0d tests
# ───────────────────────────────────────────────────────────────────────────

def test_stage5_0d_constants_are_frozen():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_0D_PROFILE_NAMES == runner.STAGE5_0B_ASINH_PROFILE_NAMES
    assert runner.STAGE5_0D_SEEDS == [42, 77, 123]
    assert runner.STAGE5_0D_TARGETS == [
        "sell_stop_broken_H6_off05_flag",
        "buy_stop_broken_H6_off05_flag",
    ]
    assert runner.STAGE5_0D_SCREENER_THRESHOLD == 0.02
    for pname in runner.STAGE5_0D_PROFILE_NAMES:
        assert runner.find_profile(pname) is not None


def test_compute_logistic_same_profile_baseline_returns_metrics(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(10, 100)
    df["_year"] = [2020] * 5 + [2023] * 5

    monkeypatch.setattr(runner, "build_xgb_features_for_profile",
                        lambda d, pname, tv, transform_params=None: np.random.rand(len(d), 10).astype(np.float32))
    monkeypatch.setattr(runner, "fit_transform_params_for_profile",
                        lambda df, parsed, profile, variant: {})
    monkeypatch.setattr(runner, "parse_split_fractals", lambda df: {})
    monkeypatch.setattr(runner, "find_profile",
                        lambda name: {"seq_len": 1, "token_dim": 5, "row_dim": 5})
    monkeypatch.setattr(runner, "compute_metrics",
                        lambda yt, yp: {"auc": 0.58, "pr_auc": 0.5, "n": len(yt),
                                        "lift_10": 1.0, "lift_20": 1.0, "lift_30": 0.9})
    monkeypatch.setattr(runner, "compute_yearly_metrics", lambda df_arg, pred, target_col=None: {})

    result = runner.compute_logistic_same_profile_baseline(
        df.iloc[:5], df.iloc[:5], df.iloc[5:],
        "all100_relative_price_time",
        transform_variant="current", target_col=runner.TARGET_COLUMN, seed=42)
    assert "val" in result and "holdout" in result
    assert result["model_type"] == "logistic_regression"
    assert result["val"]["auc"] == 0.58
    assert result["transform_params_fit_on"] == "train"


def test_compute_feature_group_ablation_returns_all_groups(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner
    import sys

    df = _make_synthetic_df(10, 100)
    df["_year"] = [2020] * 5 + [2023] * 5

    class _FakeModel:
        def predict(self, dm):
            return np.array([0.5] * len(dm))

    class _FakeDMatrix:
        def __init__(self, data):
            self._data = data
        def __len__(self):
            return len(self._data)

    if "xgboost" in sys.modules:
        monkeypatch.setattr(sys.modules["xgboost"], "DMatrix", _FakeDMatrix)

    monkeypatch.setattr(runner, "build_xgb_features_for_profile",
                        lambda d, pname, tv, transform_params=None: np.random.rand(len(d), 15).astype(np.float32))
    monkeypatch.setattr(runner, "fit_transform_params_for_profile",
                        lambda df, parsed, profile, variant: {})
    monkeypatch.setattr(runner, "parse_split_fractals", lambda df: {})
    monkeypatch.setattr(runner, "find_profile",
                        lambda name: {"seq_len": 1, "token_dim": 10, "row_dim": 5,
                                      "token_fields": ["price_coord_atr", "direction", "front", "back", "strong",
                                                       "break", "reverse", "power", "count", "impulse"],
                                      "row_fields": ["ATR", "hour_sin", "hour_cos", "dow_sin", "dow_cos"]})
    monkeypatch.setattr(runner, "train_xgb_baseline",
                        lambda Xtr, ytr, Xv, yv, seed=42: (_FakeModel(), 0.65))
    monkeypatch.setattr(runner, "compute_metrics",
                        lambda yt, yp: {"auc": 0.65, "pr_auc": 0.5, "n": len(yt),
                                        "lift_10": 1.0, "lift_20": 1.0, "lift_30": 0.8})
    monkeypatch.setattr(runner, "compute_yearly_metrics", lambda df_arg, pred, target_col=None: {})

    result = runner.compute_feature_group_ablation(
        df.iloc[:5], df.iloc[:5], df.iloc[5:],
        "all100_relative_price_time",
        transform_variant="current", target_col=runner.TARGET_COLUMN, seed=42)
    assert "full" in result
    assert "no_price" in result
    assert "no_structure" in result
    assert "no_atr" in result
    assert "no_time" in result
    for group in ["full", "no_price", "no_structure", "no_atr", "no_time"]:
        assert "val" in result[group]
        assert "auc" in result[group]["val"]


def test_stage5_0d_runner_screens_all_profiles_and_writes_json(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df_sell = _make_synthetic_df(5, 100)
    df_sell["_year"] = [2020] * 5
    df_buy = df_sell.copy()
    df_buy["buy_stop_broken_H6_off05_flag"] = [0, 1, 0, 1, 0]

    monkeypatch.setattr(runner, "compute_xgb_same_profile_baseline",
                        lambda train_df, val_stop_df, holdout_df, profile_name,
                               transform_variant="asinh", target_col=runner.TARGET_COLUMN, seed=42: {
                            "profile": profile_name, "val": {"auc": 0.66, "lift_30": 0.6},
                            "holdout": {"auc": 0.64, "lift_30": 0.65}, "yearly": {}})
    monkeypatch.setattr(runner, "compute_logistic_same_profile_baseline",
                        lambda train_df, val_stop_df, holdout_df, profile_name,
                               transform_variant="current", target_col=runner.TARGET_COLUMN, seed=42: {
                            "profile": profile_name, "model_type": "logistic_regression",
                            "val": {"auc": 0.62, "lift_30": 0.7},
                            "holdout": {"auc": 0.61, "lift_30": 0.72}, "yearly": {}})
    monkeypatch.setattr(runner, "compute_feature_group_ablation",
                        lambda train_df, val_stop_df, holdout_df, profile_name,
                               transform_variant="asinh", target_col=runner.TARGET_COLUMN, seed=42: {
                            "full": {"n_features": 15, "val": {"auc": 0.66},
                                     "holdout": {"auc": 0.64}},
                            "no_price": {"n_features": 14, "val": {"auc": 0.64},
                                         "holdout": {"auc": 0.63}},
                            "no_structure": {"n_features": 6, "val": {"auc": 0.65},
                                             "holdout": {"auc": 0.63}},
                            "no_atr": {"n_features": 14, "val": {"auc": 0.66},
                                       "holdout": {"auc": 0.64}},
                            "no_time": {"n_features": 11, "val": {"auc": 0.63},
                                        "holdout": {"auc": 0.62}}})
    monkeypatch.setattr(runner, "compute_xgb_baselines",
                        lambda tr, va, ho, target_col=runner.TARGET_COLUMN: {
                            "base_raw_plus_time": {"val": {"auc": 0.65, "lift_30": 0.7}}})
    monkeypatch.setattr(runner, "STAGE5_0D_PROFILE_NAMES", ["p1", "p2"])
    monkeypatch.setattr(runner, "STAGE5_0D_TARGETS", [
        "sell_stop_broken_H6_off05_flag",
        "buy_stop_broken_H6_off05_flag",
    ])
    monkeypatch.setattr(runner, "STAGE5_0D_SCREENER_THRESHOLD", 0.02)

    report = runner.run_stage5_0d_diagnostic_screening(
        sell_splits=(df_sell, df_sell, df_sell),
        buy_splits=(df_buy, df_buy, df_buy),
        seeds=[42, 77, 123],
        device="cpu",
        output_path=tmp_path / "stage5_0d.json",
    )

    assert report["stage"] == "5.0d_diagnostic_screening"
    assert report["level"] == "exploratory"
    assert report["holdout_used_for_decision"] is False
    assert len(report["targets"]["sell"]["profiles"]) == 2
    assert "base_raw_plus_time_auc" in report["targets"]["sell"]
    assert "base_raw_plus_time_lift_30" in report["targets"]["sell"]
    assert "ablation" in report["targets"]["sell"]
    assert "screener_result" in report
    sr = report["screener_result"]
    assert sr["verdict"] in ("profile_with_potential", "h6_off05_target_exhausted")
    assert "sell_best" in sr and "buy_best" in sr
    assert "overall_best" in sr
    assert "criteria" in sr
    assert "auc_pass" in sr["criteria"]
    assert "lift_pass" in sr["criteria"]
    assert (tmp_path / "stage5_0d.json").exists()


def test_stage5_0d_cli_argument_exists_in_build_arg_parser():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = runner.build_arg_parser()
    args = parser.parse_args(["--stage5-0d-diagnostic-screening"])
    assert args.stage5_0d_diagnostic_screening is True


# ───────────────────────────────────────────────────────────────────────────
# Stage 5.0e tests
# ───────────────────────────────────────────────────────────────────────────

def test_stage5_0e_constants_are_frozen():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_0E_TARGET == "sell_stop_broken_H6_off05_flag"
    assert runner.STAGE5_0E_PROFILE_NAMES == [
        "all100_relative_price_time",
    ]
    assert runner.STAGE5_0E_SEEDS == [42, 77, 123]
    assert [cfg["name"] for cfg in runner.STAGE5_0E_MODEL_CONFIGS] == [
        "current",
        "small_regularized",
    ]
    assert runner.STAGE5_0E_MODEL_CONFIGS[1]["d_model"] == 32
    assert runner.STAGE5_0E_MODEL_CONFIGS[1]["dropout"] == 0.35
    assert str(runner.STAGE5_0E_JSON_REPORT_PATH).endswith(
        "stage5_0e_small_transformer_check.json"
    )


def test_train_transformer_accepts_model_config(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    captured = {}

    class DummyModel(torch.nn.Module):
        def __init__(self, **kwargs):
            super().__init__()
            captured.update(kwargs)
            self.linear = torch.nn.Linear(1, 1)

        def forward(self, tokens, row_feat, mask):
            return self.linear(tokens[:, :1, :1])

    monkeypatch.setattr(runner, "FractalBreachTransformer", DummyModel)

    tokens = np.random.rand(8, 2, 1).astype(np.float32)
    row = np.random.rand(8, 1).astype(np.float32)
    mask = np.ones((8, 2), dtype=bool)
    y = pd.Series([0, 1, 0, 1, 0, 1, 0, 1])

    runner.train_transformer(
        tokens, row, mask, y,
        tokens, row, mask, y,
        profile={"name": "unit"},
        seed=42,
        device=torch.device("cpu"),
        model_config={
            "d_model": 32,
            "nhead": 2,
            "num_layers": 1,
            "dim_feedforward": 64,
            "dropout": 0.35,
            "weight_decay": 1e-3,
            "learning_rate": 7e-4,
            "patience": 3,
        },
    )

    assert captured["d_model"] == 32
    assert captured["nhead"] == 2
    assert captured["num_layers"] == 1
    assert captured["dim_feedforward"] == 64
    assert captured["dropout"] == 0.35


def test_stage5_0e_runner_writes_json(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(12, 100)
    df["_year"] = [2020] * 12

    monkeypatch.setattr(runner, "STAGE5_0E_PROFILE_NAMES", ["all100_relative_price_time"])
    monkeypatch.setattr(runner, "STAGE5_0E_SEEDS", [42])
    monkeypatch.setattr(runner, "STAGE5_0E_MODEL_CONFIGS", [
        {
            "name": "small_regularized",
            "d_model": 32,
            "nhead": 2,
            "num_layers": 1,
            "dim_feedforward": 64,
            "dropout": 0.35,
            "weight_decay": 1e-3,
            "learning_rate": 7e-4,
            "patience": 3,
        }
    ])
    monkeypatch.setattr(runner, "parse_split_fractals", lambda *a, **k: {})
    monkeypatch.setattr(runner, "verify_breach_labels_against_ohlc", lambda *a, **k: {"status": "PASS"})
    monkeypatch.setattr(runner, "label_sanity_check", lambda *a, **k: {"status": "PASS"})
    monkeypatch.setattr(runner, "compute_xgb_same_profile_baseline", lambda *a, **k: {
        "val": {"auc": 0.67, "lift_30": 0.52},
        "holdout": {"auc": 0.64, "lift_30": 0.55},
    })
    monkeypatch.setattr(runner, "_train_and_eval_profile", lambda *a, **k: a[5]["transformer_results"].setdefault(
        "all100_relative_price_time", []).append({
            "profile": "all100_relative_price_time",
            "target": runner.STAGE5_0E_TARGET,
            "val": {"auc": 0.668, "lift_30": 0.53},
            "holdout": {"auc": 0.64, "lift_30": 0.56},
            "history": {"best_epoch": 4, "overfit_drop_after_best": 0.002},
        }) or 1.0)

    report = runner.run_stage5_0e_small_transformer_check(
        (df, df, df),
        seed=42,
        device=torch.device("cpu"),
        output_path=tmp_path / "stage5_0e.json",
    )

    assert report["stage"] == "5.0e_small_transformer_overfit_check"
    assert report["holdout_used_for_decision"] is False
    assert report["target"] == runner.STAGE5_0E_TARGET
    assert report["decision"]["status"] == "DIAGNOSTIC_ONLY"
    assert report["decision"]["overfit_hypothesis_supported"] in {"yes", "no"}
    assert report["decision"]["transformer_reopens_h6_off05"] in {"no", "review_required"}
    assert (tmp_path / "stage5_0e.json").exists()


def test_stage5_0e_cli_argument_exists_in_build_arg_parser():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = runner.build_arg_parser()
    args = parser.parse_args(["--stage5-0e-small-transformer-check"])
    assert args.stage5_0e_small_transformer_check is True


# ───────────────────────────────────────────────────────────────────────────
# Stage 5.0f tests
# ───────────────────────────────────────────────────────────────────────────

def test_stage5_0f_constants_are_frozen():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_0F_TARGETS == [
        "sell_stop_broken_H6_off05_flag",
        "buy_stop_broken_H6_off05_flag",
    ]
    assert runner.STAGE5_0F_PROFILE_KEYS == [
        "base_raw_plus_time",
        "structure_only",
        "time_only",
        "all100_relative_price_time",
    ]
    assert runner.STAGE5_0F_SEEDS == [42, 77, 123]
    assert runner.STAGE5_0F_DECISION_YEARS == [2023, 2024, 2025]
    assert runner.STAGE5_0F_LOW_N_YEAR == 2026
    assert str(runner.STAGE5_0F_JSON_REPORT_PATH).endswith(
        "stage5_0f_signal_stationarity.json"
    )


def test_stage5_0f_time_only_has_no_calendar_index_fields():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.TIME_ONLY_ROW_FIELDS == ["hour_sin", "hour_cos", "dow_sin", "dow_cos"]
    forbidden = {"time_pos", "year", "month", "date_index", "calendar_index"}
    assert forbidden.isdisjoint(set(runner.TIME_ONLY_ROW_FIELDS))


def test_build_stage5_0f_features_shapes_and_profiles():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(6, 100)

    base_params = runner.fit_stage5_0f_transform_params(
        df, "base_raw_plus_time", transform_variant="asinh"
    )
    X_base = runner.build_stage5_0f_features(
        df, "base_raw_plus_time", transform_variant="asinh", transform_params=base_params
    )
    assert X_base.shape == (6, 1005)

    structure_params = runner.fit_stage5_0f_transform_params(
        df, "structure_only", transform_variant="asinh"
    )
    X_structure = runner.build_stage5_0f_features(
        df, "structure_only", transform_variant="asinh", transform_params=structure_params
    )
    assert X_structure.shape == (6, 904)

    X_time = runner.build_stage5_0f_features(
        df, "time_only", transform_variant="asinh", transform_params=None
    )
    assert X_time.shape == (6, 4)

    rel_params = runner.fit_stage5_0f_transform_params(
        df, "all100_relative_price_time", transform_variant="asinh"
    )
    X_rel = runner.build_stage5_0f_features(
        df, "all100_relative_price_time", transform_variant="asinh", transform_params=rel_params
    )
    assert X_rel.shape == (6, 1005)


def _make_stage5_0f_year_df() -> pd.DataFrame:
    """Tiny yearly fixture for split/JSON structure tests, not statistical CI tests."""
    rows = []
    for year in range(2010, 2027):
        for i in range(4):
            rows.append({
                "time": f"{year}.01.{i + 1:02d} 12:00",
                "_year": year,
                "sell_stop_broken_H6_off05_flag": i % 2,
                "buy_stop_broken_H6_off05_flag": (i + 1) % 2,
                "ATR": 1.0,
                "signal": -1,
                **{f"fractal{j}": _make_fractal_str([
                    (0, 10_000_000),
                    (1, 390.0 + j),
                    (2, -1),
                    (3, 0.5),
                    (4, 0.25),
                    (5, 1),
                    (6, 0),
                    (7, 0),
                    (8, 1),
                    (9, 1),
                    (10, 0.5),
                    (21, 1.0),
                    (22, j + 1),
                ]) for j in range(100)},
            })
    return pd.DataFrame(rows)


def test_stage5_0f_build_rolling_window_has_internal_val_stop():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    window = runner.build_stage5_0f_window(df, strategy="rolling", test_year=2024)

    assert sorted(window["train_core"]["_year"].unique().tolist()) == list(range(2016, 2023))
    assert sorted(window["val_stop"]["_year"].unique().tolist()) == [2023]
    assert sorted(window["test"]["_year"].unique().tolist()) == [2024]
    assert window["manifest"]["strategy"] == "rolling"
    assert window["manifest"]["test_year"] == 2024


def test_stage5_0f_build_anchored_window_has_internal_val_stop():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    window = runner.build_stage5_0f_window(df, strategy="anchored", test_year=2022)

    assert window["train_core"]["_year"].max() == 2020
    assert sorted(window["val_stop"]["_year"].unique().tolist()) == [2021]
    assert sorted(window["test"]["_year"].unique().tolist()) == [2022]
    assert window["manifest"]["strategy"] == "anchored"


def test_stage5_0f_build_fixed_window_uses_2020_val_stop():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    window = runner.build_stage5_0f_window(df, strategy="fixed", test_year=2025)

    assert window["train_core"]["_year"].max() == 2019
    assert sorted(window["val_stop"]["_year"].unique().tolist()) == [2020]
    assert sorted(window["test"]["_year"].unique().tolist()) == [2025]
    assert window["manifest"]["strategy"] == "fixed"


def test_bootstrap_stage5_0f_metric_ci_is_deterministic():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    y = pd.Series([0, 0, 1, 1, 0, 1, 0, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9, 0.3, 0.7, 0.4, 0.6])

    ci1 = runner.bootstrap_stage5_0f_metric_ci(y, p, metric_name="auc", n_boot=100, seed=42)
    ci2 = runner.bootstrap_stage5_0f_metric_ci(y, p, metric_name="auc", n_boot=100, seed=42)

    assert ci1 == ci2
    assert ci1["metric"] == "auc"
    assert ci1["n_boot"] == 100
    assert ci1["low"] <= ci1["median"] <= ci1["high"]


def test_bootstrap_stage5_0f_metric_ci_handles_single_class():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    y = pd.Series([0, 0, 0, 0])
    p = np.array([0.1, 0.2, 0.3, 0.4])

    ci = runner.bootstrap_stage5_0f_metric_ci(y, p, metric_name="auc", n_boot=100, seed=42)

    assert ci["low"] is None
    assert ci["median"] is None
    assert ci["high"] is None


def test_evaluate_stage5_0f_window_seed_returns_manifest_and_metrics(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    window = runner.build_stage5_0f_window(
        df, "fixed", 2023, target_col="sell_stop_broken_H6_off05_flag")

    class DummyDMatrix:
        def __init__(self, X, label=None):
            self.X = X
            self.label = label

    class DummyModel:
        def predict(self, dmat):
            return np.linspace(0.05, 0.95, len(dmat.X))

    monkeypatch.setattr(runner.xgb, "DMatrix", DummyDMatrix)
    monkeypatch.setattr(runner, "train_xgb_baseline", lambda *a, **k: (DummyModel(), 0.61))
    monkeypatch.setattr(runner, "STAGE5_0F_BOOTSTRAP_N", 50)

    result = runner.evaluate_stage5_0f_window_seed(
        window,
        profile_key="time_only",
        target_col="sell_stop_broken_H6_off05_flag",
        seed=42,
    )

    assert result["strategy"] == "fixed"
    assert result["profile"] == "time_only"
    assert result["target"] == "sell_stop_broken_H6_off05_flag"
    assert result["seed"] == 42
    assert result["test_year"] == 2023
    assert result["test"]["n"] == 4
    assert "auc_ci" in result["test"]
    assert "lift_30_ci" in result["test"]
    assert "split_manifest" in result


def test_summarize_stage5_0f_seed_runs_uses_median():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    runs = [
        {
            "test": {
                "auc": 0.60,
                "lift_30": 0.80,
                "n": 100,
                "auc_ci": {"low": 0.55, "high": 0.64},
                "lift_30_ci": {"low": 0.70, "high": 0.90},
            },
            "train_core": {"auc": 0.70},
            "val_stop": {"auc": 0.62, "lift_30": 0.82},
            "split_manifest": {"strategy": "fixed"},
        },
        {
            "test": {
                "auc": 0.66,
                "lift_30": 0.70,
                "n": 100,
                "auc_ci": {"low": 0.60, "high": 0.69},
                "lift_30_ci": {"low": 0.62, "high": 0.79},
            },
            "train_core": {"auc": 0.74},
            "val_stop": {"auc": 0.66, "lift_30": 0.72},
            "split_manifest": {"strategy": "fixed"},
        },
        {
            "test": {
                "auc": 0.63,
                "lift_30": 0.75,
                "n": 100,
                "auc_ci": {"low": 0.58, "high": 0.67},
                "lift_30_ci": {"low": 0.69, "high": 0.81},
            },
            "train_core": {"auc": 0.72},
            "val_stop": {"auc": 0.64, "lift_30": 0.76},
            "split_manifest": {"strategy": "fixed"},
        },
    ]

    summary = runner.summarize_stage5_0f_seed_runs(runs)

    assert summary["test"]["auc_median"] == pytest.approx(0.63)
    assert summary["test"]["lift_30_median"] == pytest.approx(0.75)
    assert summary["train_core"]["auc_median"] == pytest.approx(0.72)
    assert summary["n_seed_runs"] == 3


def test_stage5_0f_stationarity_decision_returns_known_status():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    report = {
        "summary": {
            "sell_stop_broken_H6_off05_flag": {
                "base_raw_plus_time": {
                    "fixed": {
                        "2023": {"test": {"auc_median": 0.60, "auc_ci_high": 0.62}},
                        "2024": {"test": {"auc_median": 0.61, "auc_ci_high": 0.63}},
                        "2025": {"test": {"auc_median": 0.60, "auc_ci_high": 0.62}},
                    },
                    "rolling": {
                        "2023": {"test": {"auc_median": 0.70, "auc_ci_low": 0.68}},
                        "2024": {"test": {"auc_median": 0.71, "auc_ci_low": 0.69}},
                        "2025": {"test": {"auc_median": 0.72, "auc_ci_low": 0.70}},
                    },
                }
            }
        }
    }

    decision = runner.stage5_0f_stationarity_decision(report)

    assert decision["status"] == "DIAGNOSTIC_ONLY"
    assert decision["overall_verdict"] in {"temporal_decay", "weak_signal", "inconclusive"}
    assert "target_verdicts" in decision


def test_stage5_0f_runner_writes_json(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    monkeypatch.setattr(runner, "STAGE5_0F_PROFILE_KEYS", ["time_only"])
    monkeypatch.setattr(runner, "STAGE5_0F_SEEDS", [42])
    monkeypatch.setattr(runner, "STAGE5_0F_BOOTSTRAP_N", 20)

    class DummyDMatrix:
        def __init__(self, X, label=None):
            self.X = X
            self.label = label

    class DummyModel:
        def predict(self, dmat):
            return np.linspace(0.05, 0.95, len(dmat.X))

    monkeypatch.setattr(runner.xgb, "DMatrix", DummyDMatrix)
    monkeypatch.setattr(runner, "train_xgb_baseline", lambda *a, **k: (DummyModel(), 0.61))

    report = runner.run_stage5_0f_signal_stationarity(
        target_splits={
            "sell_stop_broken_H6_off05_flag": (df, df, df),
            "buy_stop_broken_H6_off05_flag": (df, df, df),
        },
        output_path=tmp_path / "stage5_0f.json",
    )

    assert report["stage"] == "5.0f_signal_stationarity"
    assert report["status"] == "DIAGNOSTIC_ONLY"
    assert report["holdout_used_for_diagnostic_decision"] is True
    assert report["decision"]["overall_verdict"] in {"temporal_decay", "weak_signal", "inconclusive"}
    assert report["raw_runs"]
    assert isinstance(report["raw_runs"][0]["elapsed_sec"], float)
    assert report["raw_runs"][0]["elapsed_sec"] >= 0.0
    assert (tmp_path / "stage5_0f.json").exists()


def test_stage5_0f_cli_argument_exists_in_build_arg_parser():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = runner.build_arg_parser()
    args = parser.parse_args(["--stage5-0f-signal-stationarity"])
    assert args.stage5_0f_signal_stationarity is True


# ───────────────────────────────────────────────────────────────────────────
# Stage 5.1 tests
# ───────────────────────────────────────────────────────────────────────────

def test_stage5_1_constants_are_frozen():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_1_TARGETS == [
        "sell_stop_broken_H6_off05_flag",
        "buy_stop_broken_H6_off05_flag",
    ]
    assert runner.STAGE5_1_FIELDS == [
        "direction", "front", "back", "strong", "break",
        "reverse", "power", "count", "impulse",
    ]
    assert runner.STAGE5_1_PROFILE_KEYS == [
        "time_only",
        "structure_full",
        "drop_direction",
        "drop_front",
        "drop_back",
        "drop_strong",
        "drop_break",
        "drop_reverse",
        "drop_power",
        "drop_count",
        "drop_impulse",
        "add_direction",
        "add_front",
        "add_back",
        "add_strong",
        "add_break",
        "add_reverse",
        "add_power",
        "add_count",
        "add_impulse",
    ]
    assert runner.STAGE5_1_SEEDS == [42, 77, 123]
    assert runner.STAGE5_1_BOOTSTRAP_N == 1000
    assert str(runner.STAGE5_1_JSON_REPORT_PATH).endswith(
        "stage5_1_structural_field_ablation.json"
    )


def test_stage5_1_profiles_have_expected_fields():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    time_profile = runner._stage5_1_profile_for_key("time_only")
    full_profile = runner._stage5_1_profile_for_key("structure_full")
    drop_front = runner._stage5_1_profile_for_key("drop_front")
    add_front = runner._stage5_1_profile_for_key("add_front")

    assert time_profile["token_fields"] == []
    assert time_profile["row_fields"] == runner.TIME_ONLY_ROW_FIELDS
    assert time_profile["seq_len"] == 0

    assert full_profile["token_fields"] == runner.STAGE5_1_FIELDS
    assert full_profile["row_fields"] == runner.TIME_ONLY_ROW_FIELDS
    assert full_profile["seq_len"] == 100

    assert "front" not in drop_front["token_fields"]
    assert len(drop_front["token_fields"]) == 8
    assert drop_front["row_fields"] == runner.TIME_ONLY_ROW_FIELDS

    assert add_front["token_fields"] == ["front"]
    assert add_front["row_fields"] == runner.TIME_ONLY_ROW_FIELDS
    assert add_front["seq_len"] == 100


def test_build_stage5_1_features_shapes_and_no_atr_in_time_only():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(6, 100)

    X_time = runner.build_stage5_1_features(df, "time_only")
    X_full = runner.build_stage5_1_features(df, "structure_full")
    X_drop = runner.build_stage5_1_features(df, "drop_front")
    X_add = runner.build_stage5_1_features(df, "add_front")

    assert X_time.shape == (6, 4)
    assert X_full.shape == (6, 904)
    assert X_drop.shape == (6, 804)
    assert X_add.shape == (6, 104)
    assert runner.fit_stage5_1_transform_params(df, "structure_full") == {}


def test_build_stage5_1_split_matches_spec_years():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    split = runner.build_stage5_1_split(df, "sell_stop_broken_H6_off05_flag")

    assert sorted(split["train_core"]["_year"].unique().tolist()) == list(range(2010, 2021))
    assert sorted(split["val_stop"]["_year"].unique().tolist()) == [2021, 2022]
    assert sorted(split["diagnostic_holdout"]["_year"].unique().tolist()) == [2023, 2024, 2025]
    assert sorted(split["low_n_disclosure"]["_year"].unique().tolist()) == [2026]
    assert split["manifest"]["target"] == "sell_stop_broken_H6_off05_flag"
    assert split["manifest"]["train_core"]["years"] == list(range(2010, 2021))
    assert split["manifest"]["val_stop"]["years"] == [2021, 2022]
    assert split["manifest"]["diagnostic_holdout"]["years"] == [2023, 2024, 2025]
    assert split["manifest"]["low_n_disclosure"]["years"] == [2026]


def test_evaluate_stage5_1_profile_seed_returns_metrics_and_predictions(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    split = runner.build_stage5_1_split(df, "sell_stop_broken_H6_off05_flag")

    class DummyDMatrix:
        def __init__(self, X, label=None):
            self.X = X
            self.label = label

    class DummyModel:
        def predict(self, dmat):
            return np.linspace(0.05, 0.95, len(dmat.X))

    monkeypatch.setattr(runner.xgb, "DMatrix", DummyDMatrix)
    monkeypatch.setattr(runner, "train_xgb_baseline", lambda *a, **k: (DummyModel(), 0.61))
    monkeypatch.setattr(runner, "STAGE5_1_BOOTSTRAP_N", 20)

    result = runner.evaluate_stage5_1_profile_seed(
        split,
        profile_key="time_only",
        target_col="sell_stop_broken_H6_off05_flag",
        seed=42,
    )

    assert result["profile"] == "time_only"
    assert result["target"] == "sell_stop_broken_H6_off05_flag"
    assert result["seed"] == 42
    assert result["transform_params"] == {}
    assert result["val_stop"]["n"] == 8
    assert result["diagnostic_holdout"]["n"] == 12
    assert set(result["yearly_val"].keys()) == {"2021", "2022"}
    assert set(result["yearly_diagnostic_holdout"].keys()) == {"2023", "2024", "2025"}
    assert "auc_ci" in result["val_stop"]
    assert "auc_ci" in result["diagnostic_holdout"]
    assert len(result["predictions"]["val_stop"]) == 8
    assert len(result["predictions"]["diagnostic_holdout"]) == 12
    assert "split_manifest" in result


def test_bootstrap_stage5_1_delta_ci_is_deterministic():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    y = pd.Series([0, 0, 1, 1, 0, 1, 0, 1])
    a = np.array([0.1, 0.2, 0.8, 0.9, 0.3, 0.7, 0.4, 0.6])
    b = np.array([0.2, 0.3, 0.7, 0.8, 0.4, 0.6, 0.5, 0.55])

    ci1 = runner.bootstrap_stage5_1_delta_ci(y, a, b, n_boot=100, seed=42)
    ci2 = runner.bootstrap_stage5_1_delta_ci(y, a, b, n_boot=100, seed=42)

    assert ci1 == ci2
    assert ci1["metric"] == "auc_delta"
    assert ci1["low"] <= ci1["median"] <= ci1["high"]


def test_summarize_stage5_1_seed_runs_uses_median_and_seed_spread():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    runs = [
        {
            "train_core": {"auc": 0.70},
            "val_stop": {"auc": 0.62, "lift_30": 0.82, "auc_ci": {"low": 0.55, "high": 0.68}},
            "diagnostic_holdout": {"auc": 0.60, "lift_30": 0.80, "auc_ci": {"low": 0.53, "high": 0.66}},
            "low_n_disclosure": {"auc": 0.59, "lift_30": 0.78},
            "yearly_val": {"2021": {"auc": 0.61}, "2022": {"auc": 0.63}},
            "yearly_diagnostic_holdout": {"2023": {"auc": 0.59}, "2024": {"auc": 0.60}, "2025": {"auc": 0.61}},
            "split_manifest": {"target": "sell_stop_broken_H6_off05_flag"},
        },
        {
            "train_core": {"auc": 0.74},
            "val_stop": {"auc": 0.66, "lift_30": 0.72, "auc_ci": {"low": 0.60, "high": 0.70}},
            "diagnostic_holdout": {"auc": 0.64, "lift_30": 0.70, "auc_ci": {"low": 0.58, "high": 0.69}},
            "low_n_disclosure": {"auc": 0.62, "lift_30": 0.74},
            "yearly_val": {"2021": {"auc": 0.65}, "2022": {"auc": 0.67}},
            "yearly_diagnostic_holdout": {"2023": {"auc": 0.63}, "2024": {"auc": 0.64}, "2025": {"auc": 0.65}},
            "split_manifest": {"target": "sell_stop_broken_H6_off05_flag"},
        },
        {
            "train_core": {"auc": 0.72},
            "val_stop": {"auc": 0.64, "lift_30": 0.76, "auc_ci": {"low": 0.57, "high": 0.69}},
            "diagnostic_holdout": {"auc": 0.62, "lift_30": 0.75, "auc_ci": {"low": 0.55, "high": 0.67}},
            "low_n_disclosure": {"auc": 0.60, "lift_30": 0.76},
            "yearly_val": {"2021": {"auc": 0.63}, "2022": {"auc": 0.65}},
            "yearly_diagnostic_holdout": {"2023": {"auc": 0.61}, "2024": {"auc": 0.62}, "2025": {"auc": 0.63}},
            "split_manifest": {"target": "sell_stop_broken_H6_off05_flag"},
        },
    ]

    summary = runner.summarize_stage5_1_seed_runs(runs)

    assert summary["n_seed_runs"] == 3
    assert summary["val_stop"]["auc_median"] == pytest.approx(0.64)
    assert summary["diagnostic_holdout"]["auc_median"] == pytest.approx(0.62)
    assert summary["val_stop"]["auc_seed_min"] == pytest.approx(0.62)
    assert summary["val_stop"]["auc_seed_max"] == pytest.approx(0.66)
    assert summary["yearly_val"]["2021"]["auc_median"] == pytest.approx(0.63)
    assert summary["yearly_diagnostic_holdout"]["2025"]["auc_median"] == pytest.approx(0.63)


def test_stage5_1_field_verdicts_classify_useful_noise_and_unclear():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    target = "sell_stop_broken_H6_off05_flag"
    report = {
        "summary": {
            target: {
                "drop_front": {
                    "delta_vs_structure_full": {
                        "val_stop": {
                            "delta_median": -0.02,
                            "delta_ci_low": -0.04,
                            "delta_ci_high": -0.01,
                            "negative_seed_count": 3,
                            "positive_seed_count": 0,
                        },
                    },
                    "yearly_val": {
                        "2021": {"auc_median": 0.60},
                        "2022": {"auc_median": 0.61},
                    },
                    "yearly_diagnostic_holdout": {
                        "2023": {"auc_median": 0.60},
                        "2024": {"auc_median": 0.61},
                        "2025": {"auc_median": 0.62},
                    },
                },
                "add_front": {
                    "delta_vs_time_only": {
                        "val_stop": {"delta_median": 0.03},
                        "diagnostic_holdout": {"delta_median": 0.01},
                    }
                },
                "drop_back": {
                    "delta_vs_structure_full": {
                        "val_stop": {
                            "delta_median": 0.02,
                            "delta_ci_low": 0.01,
                            "delta_ci_high": 0.04,
                            "negative_seed_count": 0,
                            "positive_seed_count": 3,
                        },
                    },
                    "yearly_val": {
                        "2021": {"auc_median": 0.64},
                        "2022": {"auc_median": 0.65},
                    },
                    "yearly_diagnostic_holdout": {
                        "2023": {"auc_median": 0.62},
                        "2024": {"auc_median": 0.63},
                        "2025": {"auc_median": 0.64},
                    },
                },
                "add_back": {
                    "delta_vs_time_only": {
                        "val_stop": {"delta_median": 0.0},
                        "diagnostic_holdout": {"delta_median": -0.01},
                    }
                },
                "structure_full": {
                    "yearly_val": {
                        "2021": {"auc_median": 0.62},
                        "2022": {"auc_median": 0.63},
                    },
                    "yearly_diagnostic_holdout": {
                        "2023": {"auc_median": 0.63},
                        "2024": {"auc_median": 0.62},
                        "2025": {"auc_median": 0.63},
                    }
                },
                "drop_direction": {
                    "delta_vs_structure_full": {
                        "val_stop": {
                            "delta_median": 0.0,
                            "delta_ci_low": -0.01,
                            "delta_ci_high": 0.01,
                            "negative_seed_count": 1,
                            "positive_seed_count": 1,
                        }
                    },
                    "yearly_val": {
                        "2021": {"auc_median": 0.62},
                        "2022": {"auc_median": 0.64},
                    },
                    "yearly_diagnostic_holdout": {
                        "2023": {"auc_median": 0.63},
                        "2024": {"auc_median": 0.61},
                        "2025": {"auc_median": 0.63},
                    },
                },
                "add_direction": {
                    "delta_vs_time_only": {
                        "val_stop": {"delta_median": 0.01},
                        "diagnostic_holdout": {"delta_median": 0.0},
                    }
                },
            }
        }
    }

    verdicts = runner.stage5_1_field_verdicts(report)

    assert verdicts["front"]["overall_verdict"] == "likely_useful"
    assert verdicts["back"]["overall_verdict"] == "likely_noise"
    assert verdicts["direction"]["overall_verdict"] == "mixed_or_unclear"
    assert verdicts["front"]["targets"][target]["drop_val_delta_ci_high"] == pytest.approx(-0.01)


def test_stage5_1_field_verdicts_conflicting_targets_are_unclear():
    import copy
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    sell = "sell_stop_broken_H6_off05_flag"
    buy = "buy_stop_broken_H6_off05_flag"
    useful_target_summary = {
        "drop_front": {
            "delta_vs_structure_full": {
                "val_stop": {
                    "delta_median": -0.02,
                    "delta_ci_low": -0.04,
                    "delta_ci_high": -0.01,
                    "negative_seed_count": 3,
                    "positive_seed_count": 0,
                },
            },
            "yearly_diagnostic_holdout": {
                "2023": {"auc_median": 0.60},
                "2024": {"auc_median": 0.61},
                "2025": {"auc_median": 0.62},
            },
        },
        "add_front": {
            "delta_vs_time_only": {
                "val_stop": {"delta_median": 0.03},
                "diagnostic_holdout": {"delta_median": 0.01},
            },
        },
        "structure_full": {
            "yearly_diagnostic_holdout": {
                "2023": {"auc_median": 0.63},
                "2024": {"auc_median": 0.62},
                "2025": {"auc_median": 0.63},
            },
        },
    }
    noise_target_summary = copy.deepcopy(useful_target_summary)
    noise_target_summary["drop_front"]["delta_vs_structure_full"]["val_stop"] = {
        "delta_median": 0.02,
        "delta_ci_low": 0.01,
        "delta_ci_high": 0.04,
        "negative_seed_count": 0,
        "positive_seed_count": 3,
    }
    noise_target_summary["drop_front"]["yearly_diagnostic_holdout"] = {
        "2023": {"auc_median": 0.64},
        "2024": {"auc_median": 0.63},
        "2025": {"auc_median": 0.65},
    }
    noise_target_summary["add_front"]["delta_vs_time_only"]["val_stop"] = {"delta_median": 0.0}

    report = {"summary": {sell: useful_target_summary, buy: noise_target_summary}}

    verdicts = runner.stage5_1_field_verdicts(report)

    assert verdicts["front"]["targets"][sell]["verdict"] == "likely_useful"
    assert verdicts["front"]["targets"][buy]["verdict"] == "likely_noise"
    assert verdicts["front"]["overall_verdict"] == "mixed_or_unclear"


def test_stage5_1_runner_writes_json(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    monkeypatch.setattr(runner, "STAGE5_1_PROFILE_KEYS", ["time_only", "structure_full"])
    monkeypatch.setattr(runner, "STAGE5_1_SEEDS", [42])
    monkeypatch.setattr(runner, "STAGE5_1_BOOTSTRAP_N", 20)

    class DummyDMatrix:
        def __init__(self, X, label=None):
            self.X = X
            self.label = label

    class DummyModel:
        def predict(self, dmat):
            return np.linspace(0.05, 0.95, len(dmat.X))

    monkeypatch.setattr(runner.xgb, "DMatrix", DummyDMatrix)
    monkeypatch.setattr(runner, "train_xgb_baseline", lambda *a, **k: (DummyModel(), 0.61))

    report = runner.run_stage5_1_structural_field_ablation(
        target_splits={
            "sell_stop_broken_H6_off05_flag": (df, df, df),
            "buy_stop_broken_H6_off05_flag": (df, df, df),
        },
        output_path=tmp_path / "stage5_1.json",
    )

    assert report["stage"] == "5.1_structural_field_ablation"
    assert report["status"] == "DIAGNOSTIC_ONLY"
    assert report["profiles"] == ["time_only", "structure_full"]
    assert report["fields"] == runner.STAGE5_1_FIELDS
    assert report["raw_runs"]
    assert "predictions" not in report["raw_runs"][0]
    assert "labels" not in report["raw_runs"][0]
    assert report["summary"]
    assert "field_verdicts" in report
    assert "multiple_testing_context" in report
    assert "holdout_disclosure" in report
    assert "transform_config" in report
    assert report["progress"]["done_runs"] == 4
    assert (tmp_path / "stage5_1.json").exists()


def test_stage5_1_cli_argument_exists_in_build_arg_parser():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = runner.build_arg_parser()
    args = parser.parse_args(["--stage5-1-structural-field-ablation"])
    assert args.stage5_1_structural_field_ablation is True


def test_stage5_1b_constants_are_frozen():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_1B_TARGETS == [
        "sell_stop_broken_H6_off05_flag",
        "buy_stop_broken_H6_off05_flag",
    ]
    assert runner.STAGE5_1B_STRUCTURE_FIELDS == [
        "direction", "front", "back", "strong", "break",
        "reverse", "power", "count", "impulse",
    ]
    assert runner.STAGE5_1B_UPDN_FIELDS == [
        "up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12",
        "up_24", "dn_24", "up_48", "dn_48",
    ]
    assert runner.STAGE5_1B_FIELDS == (
        runner.STAGE5_1B_STRUCTURE_FIELDS + runner.STAGE5_1B_UPDN_FIELDS
    )
    assert len(runner.STAGE5_1B_PROFILE_KEYS) == 43
    assert runner.STAGE5_1B_PROFILE_KEYS[:5] == [
        "clock_shift",
        "structure_full",
        "updn_full",
        "structure_plus_updn",
        "back_impulse_combo",
    ]
    assert str(runner.STAGE5_1B_JSON_REPORT_PATH).endswith(
        "stage5_1b_updn_field_ablation.json"
    )


def test_extract_stage5_1b_fields_reads_fractal_indices_and_log_shift():
    import math
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    fstr = _make_fractal_str([
        (1, 390.5),
        (2, -1),
        (3, 0.3),
        (4, 0.4),
        (5, 1),
        (6, 0),
        (7, 0.7),
        (8, 8.0),
        (9, 9.0),
        (10, 1.5),
        (11, 12.0),
        (12, 13.0),
        (13, 24.0),
        (14, 25.0),
        (15, 48.0),
        (16, 49.0),
        (17, 3.0),
        (18, 4.0),
        (19, 6.0),
        (20, 7.0),
        (22, 48),
    ])

    fields = runner.extract_stage5_1b_fields(fstr)

    assert fields["price"] == pytest.approx(390.5)
    assert fields["direction"] == pytest.approx(-1)
    assert fields["back"] == pytest.approx(0.4)
    assert fields["impulse"] == pytest.approx(1.5)
    assert fields["up_3"] == pytest.approx(3.0)
    assert fields["dn_3"] == pytest.approx(4.0)
    assert fields["up_6"] == pytest.approx(6.0)
    assert fields["dn_6"] == pytest.approx(7.0)
    assert fields["up_12"] == pytest.approx(12.0)
    assert fields["dn_12"] == pytest.approx(13.0)
    assert fields["up_24"] == pytest.approx(24.0)
    assert fields["dn_24"] == pytest.approx(25.0)
    assert fields["up_48"] == pytest.approx(48.0)
    assert fields["dn_48"] == pytest.approx(49.0)
    assert fields["shift"] == pytest.approx(math.log1p(48))


def test_extract_stage5_1b_fields_short_or_bad_fractal_returns_zeroes():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    short_fields = runner.extract_stage5_1b_fields("1:2:3")
    bad_shift = runner.extract_stage5_1b_fields(_make_fractal_str([(22, -10)]))

    assert set(short_fields) >= {"price", "direction", "up_3", "dn_48", "shift"}
    assert all(v == pytest.approx(0.0) for v in short_fields.values())
    assert bad_shift["shift"] == pytest.approx(0.0)


def test_stage5_1b_profiles_have_expected_fields():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    clock = runner._stage5_1b_profile_for_key("clock_shift")
    structure = runner._stage5_1b_profile_for_key("structure_full")
    updn = runner._stage5_1b_profile_for_key("updn_full")
    combined = runner._stage5_1b_profile_for_key("structure_plus_updn")
    combo = runner._stage5_1b_profile_for_key("back_impulse_combo")
    drop_back = runner._stage5_1b_profile_for_key("drop_back")
    drop_up3 = runner._stage5_1b_profile_for_key("drop_up_3")
    add_up3 = runner._stage5_1b_profile_for_key("add_up_3")

    assert clock["token_fields"] == ["shift"]
    assert clock["row_fields"] == runner.TIME_ONLY_ROW_FIELDS
    assert clock["seq_len"] == 100

    assert structure["token_fields"] == runner.STAGE5_1B_STRUCTURE_FIELDS + ["shift"]
    assert updn["token_fields"] == runner.STAGE5_1B_UPDN_FIELDS + ["shift"]
    assert combined["token_fields"] == runner.STAGE5_1B_FIELDS + ["shift"]
    assert combo["token_fields"] == ["shift", "back", "impulse"]

    assert "back" not in drop_back["token_fields"]
    assert "shift" in drop_back["token_fields"]
    assert "up_3" not in drop_up3["token_fields"]
    assert "shift" in drop_up3["token_fields"]
    assert add_up3["token_fields"] == ["shift", "up_3"]


def test_build_stage5_1b_features_shapes_and_log_shift():
    import math
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(6, 100)

    X_clock = runner.build_stage5_1b_features(df, "clock_shift")
    X_structure = runner.build_stage5_1b_features(df, "structure_full")
    X_updn = runner.build_stage5_1b_features(df, "updn_full")
    X_combined = runner.build_stage5_1b_features(df, "structure_plus_updn")
    X_combo = runner.build_stage5_1b_features(df, "back_impulse_combo")
    X_drop = runner.build_stage5_1b_features(df, "drop_back")
    X_add = runner.build_stage5_1b_features(df, "add_up_3")

    assert X_clock.shape == (6, 104)
    assert X_structure.shape == (6, 1004)
    assert X_updn.shape == (6, 1104)
    assert X_combined.shape == (6, 2004)
    assert X_combo.shape == (6, 304)
    assert X_drop.shape == (6, 904)
    assert X_add.shape == (6, 204)
    assert X_clock[0, 0] == pytest.approx(math.log1p(1))
    assert runner.fit_stage5_1b_transform_params(df, "structure_full") == {}


def test_stage5_1b_builder_does_not_read_top_level_updn_columns():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(2, 100)
    df["up_3"] = 999999.0
    df["dn_3"] = 999999.0

    X = runner.build_stage5_1b_features(df, "add_up_3")

    assert np.max(X[:, :200]) < 999999.0


def test_stage5_1b_preflight_reports_contract_maturity_shift_and_correlations():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    split = runner.build_stage5_1_split(df, "sell_stop_broken_H6_off05_flag")

    preflight = runner.run_stage5_1b_preflight(split, "sell_stop_broken_H6_off05_flag")

    assert preflight["source_check"]["uses_fractal_columns_only"] is True
    assert preflight["source_check"]["forbidden_top_level_updn_columns_used"] is False
    assert preflight["contract"]["expected_num_fields"] == 23
    assert preflight["contract"]["short_fractal_count"] == 0
    assert preflight["monotonicity"]["violations_total"] == 0
    assert set(preflight["maturity"]["train_core"].keys()) == {"3", "6", "12", "24", "48"}
    assert "p50" in preflight["shift_distribution"]["train_core"]
    assert "up_3" in preflight["updn_shift_correlation"]["train_core"]
    assert "up_3_over_atr" in preflight["updn_atr_disclosure"]["train_core"]
    assert runner.stage5_1b_preflight_passed(preflight) is True


def test_stage5_1b_preflight_fails_on_monotonicity_violation():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    bad = _make_fractal_str([
        (11, 10.0),
        (13, 5.0),
        (15, 4.0),
        (17, 20.0),
        (19, 15.0),
        (22, 48),
    ])
    df.loc[df.index[0], "fractal0"] = bad
    split = runner.build_stage5_1_split(df, "sell_stop_broken_H6_off05_flag")

    preflight = runner.run_stage5_1b_preflight(split, "sell_stop_broken_H6_off05_flag")

    assert preflight["monotonicity"]["violations_total"] > 0
    assert runner.stage5_1b_preflight_passed(preflight) is False


def test_stage5_1b_preflight_can_use_raw_shadow_split_to_avoid_normalized_false_fail():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    raw_df = _make_stage5_0f_year_df()
    for idx in range(len(raw_df)):
        raw_df.at[idx, "fractal0"] = _make_fractal_str([
            (0, 10_000_000 + idx),
            (1, 390.0),
            (2, -1),
            (3, 0.5),
            (4, 0.25),
            (5, 1),
            (6, 0),
            (7, 0.0),
            (8, 1.0),
            (9, 1.0),
            (10, 0.5),
            (11, 3.0),
            (12, 3.0),
            (13, 6.0),
            (14, 6.0),
            (15, 12.0),
            (16, 12.0),
            (17, 1.0),
            (18, 1.0),
            (19, 2.0),
            (20, 2.0),
            (21, 1.0),
            (22, 12),
        ])

    labeled_df = raw_df.copy()
    for idx in range(len(labeled_df)):
        labeled_df.at[idx, "fractal0"] = _make_fractal_str([
            (0, 10_000_000 + idx),
            (1, 390.0),
            (2, -1),
            (3, 0.5),
            (4, 0.25),
            (5, 1),
            (6, 0),
            (7, 0.0),
            (8, 1.0),
            (9, 1.0),
            (10, 0.5),
            (11, 0.6),
            (12, 0.6),
            (13, 0.4),
            (14, 0.4),
            (15, 0.2),
            (16, 0.2),
            (17, 0.8),
            (18, 0.8),
            (19, 0.7),
            (20, 0.7),
            (21, 1.0),
            (22, 12),
        ])

    split = runner.build_stage5_1_split(labeled_df, "sell_stop_broken_H6_off05_flag")
    raw_split = runner.build_stage5_1_split(raw_df, "sell_stop_broken_H6_off05_flag")

    labeled_preflight = runner.run_stage5_1b_preflight(split, "sell_stop_broken_H6_off05_flag")
    raw_preflight = runner.run_stage5_1b_preflight_with_source(
        split, "sell_stop_broken_H6_off05_flag", raw_split=raw_split
    )

    assert labeled_preflight["monotonicity"]["violations_total"] > 0
    assert raw_preflight["monotonicity"]["violations_total"] == 0
    assert raw_preflight["source_check"]["preflight_source"] == "raw_shadow_split"
    assert runner.stage5_1b_preflight_passed(raw_preflight) is True


def test_stage5_1b_preflight_rejects_raw_shadow_split_length_mismatch():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    split = runner.build_stage5_1_split(df, "sell_stop_broken_H6_off05_flag")
    raw_split = {
        name: value.copy() if hasattr(value, "copy") else value
        for name, value in split.items()
    }
    raw_split["val_stop"] = raw_split["val_stop"].iloc[:-1].copy()

    with pytest.raises(RuntimeError, match="Raw-shadow split alignment mismatch"):
        runner.run_stage5_1b_preflight_with_source(
            split, "sell_stop_broken_H6_off05_flag", raw_split=raw_split
        )


def test_evaluate_stage5_1b_profile_seed_returns_metrics_and_predictions(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    split = runner.build_stage5_1_split(df, "sell_stop_broken_H6_off05_flag")

    class DummyDMatrix:
        def __init__(self, X, label=None):
            self.X = X
            self.label = label

    class DummyModel:
        def predict(self, dmat):
            return np.linspace(0.05, 0.95, len(dmat.X))

    monkeypatch.setattr(runner.xgb, "DMatrix", DummyDMatrix)
    monkeypatch.setattr(runner, "train_xgb_baseline", lambda *a, **k: (DummyModel(), 0.61))
    monkeypatch.setattr(runner, "STAGE5_1_BOOTSTRAP_N", 20)
    monkeypatch.setattr(runner, "STAGE5_1B_BOOTSTRAP_N", 20)

    result = runner.evaluate_stage5_1b_profile_seed(
        split,
        profile_key="clock_shift",
        target_col="sell_stop_broken_H6_off05_flag",
        seed=42,
    )

    assert result["profile"] == "clock_shift"
    assert result["target"] == "sell_stop_broken_H6_off05_flag"
    assert result["seed"] == 42
    assert result["transform_params"] == {}
    assert result["transform_params_fit_on"] == "train_core"
    assert result["val_stop"]["n"] == 8
    assert set(result["yearly_val"].keys()) == {"2021", "2022"}
    assert set(result["yearly_diagnostic_holdout"].keys()) == {"2023", "2024", "2025"}
    assert len(result["predictions"]["val_stop"]) == 8
    assert len(result["labels"]["diagnostic_holdout"]) == 12


def test_summarize_stage5_1b_target_adds_expected_delta_blocks(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    raw_runs = []
    target = "sell_stop_broken_H6_off05_flag"
    for profile in ["clock_shift", "structure_full", "updn_full", "drop_back", "drop_up_3", "add_back", "add_up_3"]:
        for seed, auc in [(42, 0.60), (77, 0.62), (123, 0.64)]:
            raw_runs.append({
                "profile": profile,
                "target": target,
                "seed": seed,
                "train_core": {"auc": auc},
                "val_stop": {"auc": auc, "lift_30": 0.8, "auc_ci": {"low": auc - 0.01, "high": auc + 0.01}},
                "diagnostic_holdout": {"auc": auc - 0.02, "lift_30": 0.82, "auc_ci": {"low": auc - 0.03, "high": auc}},
                "low_n_disclosure": {"auc": auc - 0.03, "lift_30": 0.84},
                "yearly_val": {"2021": {"auc": auc}, "2022": {"auc": auc}},
                "yearly_diagnostic_holdout": {"2023": {"auc": auc}, "2024": {"auc": auc}, "2025": {"auc": auc}},
                "split_manifest": {"target": target},
                "predictions": {
                    "val_stop": [0.1, 0.2, 0.8, 0.9],
                    "diagnostic_holdout": [0.1, 0.2, 0.8, 0.9],
                },
                "labels": {
                    "val_stop": [0, 0, 1, 1],
                    "diagnostic_holdout": [0, 0, 1, 1],
                },
            })
    monkeypatch.setattr(runner, "STAGE5_1B_PROFILE_KEYS", [
        "clock_shift", "structure_full", "updn_full", "drop_back", "drop_up_3", "add_back", "add_up_3"
    ])

    summary = runner.summarize_stage5_1b_target(raw_runs, target)

    assert "delta_vs_structure_full" in summary["drop_back"]
    assert "delta_vs_updn_full" in summary["drop_up_3"]
    assert "delta_vs_clock_shift" in summary["add_back"]
    assert "delta_vs_clock_shift" in summary["add_up_3"]


def test_stage5_1b_field_verdicts_require_both_targets_for_overall_useful():
    import copy
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    sell = "sell_stop_broken_H6_off05_flag"
    buy = "buy_stop_broken_H6_off05_flag"
    target_summary = {
        "add_back": {
            "delta_vs_clock_shift": {
                "val_stop": {"delta_median": 0.03},
                "diagnostic_holdout": {"delta_median": 0.01},
            },
        },
        "structure_full": {
            "yearly_val": {
                "2021": {"auc_median": 0.62},
                "2022": {"auc_median": 0.63},
            },
            "yearly_diagnostic_holdout": {
                "2023": {"auc_median": 0.63},
                "2024": {"auc_median": 0.62},
                "2025": {"auc_median": 0.63},
            },
        },
        "drop_back": {
            "delta_vs_structure_full": {
                "val_stop": {
                    "delta_median": -0.02,
                    "delta_ci_low": -0.04,
                    "delta_ci_high": -0.01,
                    "negative_seed_count": 3,
                    "positive_seed_count": 0,
                },
            },
            "yearly_val": {
                "2021": {"auc_median": 0.60},
                "2022": {"auc_median": 0.61},
            },
            "yearly_diagnostic_holdout": {
                "2023": {"auc_median": 0.60},
                "2024": {"auc_median": 0.61},
                "2025": {"auc_median": 0.62},
            },
        },
    }
    report = {"summary": {sell: copy.deepcopy(target_summary), buy: copy.deepcopy(target_summary)}}

    verdicts = runner.stage5_1b_field_verdicts(report)

    assert verdicts["back"]["targets"][sell]["verdict"] == "target_likely_useful"
    assert verdicts["back"]["overall_verdict"] == "overall_likely_useful"
    assert verdicts["back"]["targets"][sell]["yearly_val_drop_signs_2021_2022"] == [-1, -1]
    assert verdicts["back"]["targets"][sell]["yearly_drop_signs_2023_2025"] == [-1, -1, -1]

    report["summary"][buy]["drop_back"]["delta_vs_structure_full"]["val_stop"]["delta_median"] = 0.0
    report["summary"][buy]["drop_back"]["delta_vs_structure_full"]["val_stop"]["negative_seed_count"] = 1
    verdicts = runner.stage5_1b_field_verdicts(report)
    assert verdicts["back"]["overall_verdict"] == "target_specific_signal"


def test_stage5_1b_group_analysis_reports_direction_horizon_and_group_deltas():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    target = "sell_stop_broken_H6_off05_flag"
    summary = {
        "updn_full": {"delta_updn_group": {"val_stop": {"delta_median": 0.02}}},
        "structure_full": {"delta_structure_group": {"val_stop": {"delta_median": 0.03}}},
        "structure_plus_updn": {"delta_combined": {"val_stop": {"delta_median": 0.01}}},
    }
    for field in runner.STAGE5_1B_UPDN_FIELDS:
        summary[f"add_{field}"] = {
            "delta_vs_clock_shift": {"val_stop": {"delta_median": 0.01}}
        }
        summary[f"drop_{field}"] = {
            "delta_vs_updn_full": {"val_stop": {"delta_median": -0.005}}
        }
    report = {
        "summary": {target: summary},
        "preflight": {
            target: {
                "maturity": {
                    "train_core": {
                        "3": {"mature_share": 0.99, "non_mature_share": 0.01},
                        "6": {"mature_share": 0.97, "non_mature_share": 0.03},
                        "12": {"mature_share": 0.90, "non_mature_share": 0.10},
                        "24": {"mature_share": 0.80, "non_mature_share": 0.20},
                        "48": {"mature_share": 0.60, "non_mature_share": 0.40},
                    },
                    "val_stop": {
                        "3": {"mature_share": 0.98, "non_mature_share": 0.02},
                        "6": {"mature_share": 0.96, "non_mature_share": 0.04},
                        "12": {"mature_share": 0.88, "non_mature_share": 0.12},
                        "24": {"mature_share": 0.76, "non_mature_share": 0.24},
                        "48": {"mature_share": 0.55, "non_mature_share": 0.45},
                    },
                }
            }
        },
    }

    analysis = runner.stage5_1b_group_analysis(report)

    assert target in analysis
    assert "direction" in analysis[target]
    assert "horizon" in analysis[target]
    assert "group_deltas" in analysis[target]
    assert analysis[target]["group_deltas"]["delta_updn_group_val"] == pytest.approx(0.02)
    assert analysis[target]["horizon"]["48"]["maturity"]["val_stop"]["non_mature_share"] == pytest.approx(0.45)


def test_stage5_1b_runner_writes_json_and_stops_after_preflight_failure(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    monkeypatch.setattr(runner, "STAGE5_1B_PROFILE_KEYS", ["clock_shift"])
    monkeypatch.setattr(runner, "STAGE5_1B_SEEDS", [42])
    monkeypatch.setattr(
        runner, "load_stage5_1b_raw_shadow_split",
        lambda target_col: runner.build_stage5_1_split(df, target_col)
    )
    monkeypatch.setattr(runner, "run_stage5_1b_preflight_with_source", lambda split, target, raw_split=None: {
        "target": target,
        "source_check": {"uses_fractal_columns_only": True, "forbidden_top_level_updn_columns_used": False},
        "contract": {"short_fractal_count": 0},
        "monotonicity": {"violations_total": 1},
        "pass": False,
    })

    called = {"train": False}
    def fail_if_called(*args, **kwargs):
        called["train"] = True
        raise AssertionError("training must not run when preflight fails")
    monkeypatch.setattr(runner, "evaluate_stage5_1b_profile_seed", fail_if_called)

    report = runner.run_stage5_1b_updn_field_ablation(
        target_splits={
            "sell_stop_broken_H6_off05_flag": (df, df, df),
            "buy_stop_broken_H6_off05_flag": (df, df, df),
        },
        output_path=tmp_path / "stage5_1b.json",
    )

    assert report["stage"] == "5.1b"
    assert report["experiment"] == "updn_field_ablation"
    assert report["status"] == "PREFLIGHT_FAILED"
    assert called["train"] is False
    assert (tmp_path / "stage5_1b.json").exists()


def test_stage5_1b_runner_writes_diagnostic_json(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    monkeypatch.setattr(runner, "STAGE5_1B_PROFILE_KEYS", ["clock_shift", "structure_full", "updn_full"])
    monkeypatch.setattr(runner, "STAGE5_1B_SEEDS", [42])
    monkeypatch.setattr(runner, "STAGE5_1_BOOTSTRAP_N", 20)
    monkeypatch.setattr(runner, "STAGE5_1B_BOOTSTRAP_N", 20)
    monkeypatch.setattr(
        runner, "load_stage5_1b_raw_shadow_split",
        lambda target_col: runner.build_stage5_1_split(
            pd.concat([df, df, df], ignore_index=True), target_col
        )
    )

    class DummyDMatrix:
        def __init__(self, X, label=None):
            self.X = X
            self.label = label

    class DummyModel:
        def predict(self, dmat):
            return np.linspace(0.05, 0.95, len(dmat.X))

    monkeypatch.setattr(runner.xgb, "DMatrix", DummyDMatrix)
    monkeypatch.setattr(runner, "train_xgb_baseline", lambda *a, **k: (DummyModel(), 0.61))

    report = runner.run_stage5_1b_updn_field_ablation(
        target_splits={
            "sell_stop_broken_H6_off05_flag": (df, df, df),
            "buy_stop_broken_H6_off05_flag": (df, df, df),
        },
        output_path=tmp_path / "stage5_1b.json",
    )

    assert report["stage"] == "5.1b"
    assert report["experiment"] == "updn_field_ablation"
    assert report["status"] == "DIAGNOSTIC_ONLY"
    assert report["baseline"] == "clock + shift (log1p)"
    assert report["profiles"] == ["clock_shift", "structure_full", "updn_full"]
    assert report["raw_runs"]
    assert "predictions" not in report["raw_runs"][0]
    assert "labels" not in report["raw_runs"][0]
    assert "preflight" in report
    assert "group_analysis" in report
    assert "field_verdicts" in report
    assert report["progress"]["done_runs"] == 6


def test_stage5_1b_cli_argument_exists_in_build_arg_parser():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = runner.build_arg_parser()
    args = parser.parse_args(["--stage5-1b-updn-field-ablation"])
    assert args.stage5_1b_updn_field_ablation is True


def test_stage5_1b_runner_resume_skips_completed_jobs(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    monkeypatch.setattr(runner, "STAGE5_1B_TARGETS", ["sell_stop_broken_H6_off05_flag"])
    monkeypatch.setattr(runner, "STAGE5_1B_PROFILE_KEYS", ["clock_shift", "structure_full"])
    monkeypatch.setattr(runner, "STAGE5_1B_SEEDS", [42, 77])
    monkeypatch.setattr(
        runner, "load_stage5_1b_raw_shadow_split",
        lambda target_col: runner.build_stage5_1_split(pd.concat([df, df, df], ignore_index=True), target_col)
    )
    monkeypatch.setattr(runner, "run_stage5_1b_preflight_with_source", lambda split, target, raw_split=None: {
        "target": target,
        "source_check": {"uses_fractal_columns_only": True, "forbidden_top_level_updn_columns_used": False},
        "contract": {"short_fractal_count": 0},
        "monotonicity": {"violations_total": 0},
        "pass": True,
    })

    output_path = tmp_path / "stage5_1b_resume.json"
    existing = {
        "stage": "5.1b",
        "experiment": "updn_field_ablation",
        "status": "RUNNING",
        "targets": ["sell_stop_broken_H6_off05_flag"],
        "fields": [],
        "seeds": [42, 77],
        "profiles": ["clock_shift", "structure_full"],
        "raw_runs": [{
            "target": "sell_stop_broken_H6_off05_flag",
            "profile": "clock_shift",
            "seed": 42,
            "val_stop": {"auc": 0.61},
            "diagnostic_holdout": {"auc": 0.59},
            "low_n_disclosure": {"auc": 0.58},
            "yearly_val": {},
            "yearly_diagnostic_holdout": {},
            "elapsed_sec": 10.0,
        }],
        "summary": {},
        "field_verdicts": {},
        "group_analysis": {},
        "preflight": {},
        "multiple_testing_context": {},
        "holdout_disclosure": {},
        "transform_config": {},
        "sanity_checks": {},
        "progress": {"started_at_unix": 1.0, "done_runs": 999, "total_runs": 4, "last_completed": None},
    }
    output_path.write_text(json.dumps(existing), encoding="utf-8")

    calls = []

    def fake_worker(job):
        calls.append((job["target"], job["profile"], job["seed"], job["xgb_threads"]))
        return {
            "profile": job["profile"],
            "target": job["target"],
            "seed": job["seed"],
            "val_stop": {"auc": 0.62},
            "diagnostic_holdout": {"auc": 0.6},
            "low_n_disclosure": {"auc": 0.57},
            "yearly_val": {},
            "yearly_diagnostic_holdout": {},
            "elapsed_sec": 20.0,
        }

    monkeypatch.setattr(runner, "_run_stage5_1b_job", fake_worker)
    monkeypatch.setattr(runner, "summarize_stage5_1b_target", lambda raw_runs, target: {"n_runs": len(raw_runs)})
    monkeypatch.setattr(runner, "stage5_1b_field_verdicts", lambda report: {"ok": True})
    monkeypatch.setattr(runner, "stage5_1b_group_analysis", lambda report: {"ok": True})

    report = runner.run_stage5_1b_updn_field_ablation(
        target_splits={"sell_stop_broken_H6_off05_flag": (df, df, df)},
        output_path=output_path,
        resume=True,
        workers=1,
        xgb_threads=3,
    )

    assert len(calls) == 3
    assert ("sell_stop_broken_H6_off05_flag", "clock_shift", 42, 3) not in calls
    assert report["progress"]["done_runs"] == 4
    assert len(report["raw_runs"]) == 4
    assert report["summary"]["sell_stop_broken_H6_off05_flag"]["n_runs"] == 4


def test_stage5_1b_runner_uses_process_pool_for_parallel_jobs(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    monkeypatch.setattr(runner, "STAGE5_1B_TARGETS", ["sell_stop_broken_H6_off05_flag"])
    monkeypatch.setattr(runner, "STAGE5_1B_PROFILE_KEYS", ["clock_shift", "structure_full"])
    monkeypatch.setattr(runner, "STAGE5_1B_SEEDS", [42])
    monkeypatch.setattr(
        runner, "load_stage5_1b_raw_shadow_split",
        lambda target_col: runner.build_stage5_1_split(pd.concat([df, df, df], ignore_index=True), target_col)
    )
    monkeypatch.setattr(runner, "run_stage5_1b_preflight_with_source", lambda split, target, raw_split=None: {
        "target": target,
        "source_check": {"uses_fractal_columns_only": True, "forbidden_top_level_updn_columns_used": False},
        "contract": {"short_fractal_count": 0},
        "monotonicity": {"violations_total": 0},
        "pass": True,
    })
    monkeypatch.setattr(runner, "summarize_stage5_1b_target", lambda raw_runs, target: {"n_runs": len(raw_runs)})
    monkeypatch.setattr(runner, "stage5_1b_field_verdicts", lambda report: {"ok": True})
    monkeypatch.setattr(runner, "stage5_1b_group_analysis", lambda report: {"ok": True})

    seen = {"max_workers": None, "jobs": []}

    class FakeExecutor:
        def __init__(self, max_workers):
            seen["max_workers"] = max_workers

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn, job):
            seen["jobs"].append((job["profile"], job["seed"], job["xgb_threads"]))
            fut = Future()
            fut.set_result(fn(job))
            return fut

    def fake_worker(job):
        return {
            "profile": job["profile"],
            "target": job["target"],
            "seed": job["seed"],
            "val_stop": {"auc": 0.7},
            "diagnostic_holdout": {"auc": 0.69},
            "low_n_disclosure": {"auc": 0.68},
            "yearly_val": {},
            "yearly_diagnostic_holdout": {},
            "elapsed_sec": 15.0,
        }

    monkeypatch.setattr(runner, "ProcessPoolExecutor", FakeExecutor)
    monkeypatch.setattr(runner, "_run_stage5_1b_job", fake_worker)

    report = runner.run_stage5_1b_updn_field_ablation(
        target_splits={"sell_stop_broken_H6_off05_flag": (df, df, df)},
        output_path=tmp_path / "stage5_1b_parallel.json",
        resume=False,
        workers=2,
        xgb_threads=4,
    )

    assert seen["max_workers"] == 2
    assert seen["jobs"] == [("clock_shift", 42, 4), ("structure_full", 42, 4)]
    assert report["progress"]["done_runs"] == 2


def test_stage5_2_constants_and_profiles_are_frozen():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_2_TARGETS == [
        "sell_bars_to_breach_H6_off05",
        "buy_bars_to_breach_H6_off05",
    ]
    assert runner.STAGE5_2_TARGET_TO_BINARY == {
        "sell_bars_to_breach_H6_off05": "sell_stop_broken_H6_off05_flag",
        "buy_bars_to_breach_H6_off05": "buy_stop_broken_H6_off05_flag",
    }
    assert runner.STAGE5_2_PROFILE_KEYS == [
        "time_only",
        "clock_shift",
        "clock_shift_back",
        "clock_shift_impulse",
        "clock_shift_back_impulse",
        "structure_full",
        "structure_full_without_back",
    ]
    assert str(runner.STAGE5_2_JSON_REPORT_PATH).endswith(
        "stage5_2_time_to_breach_regression.json"
    )


def test_stage5_2_profile_token_fields():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner._stage5_2_profile_for_key("time_only")["token_fields"] == []
    assert runner._stage5_2_profile_for_key("clock_shift")["token_fields"] == ["shift"]
    assert runner._stage5_2_profile_for_key("clock_shift_back")["token_fields"] == ["shift", "back"]
    assert runner._stage5_2_profile_for_key("clock_shift_impulse")["token_fields"] == ["shift", "impulse"]
    assert runner._stage5_2_profile_for_key("clock_shift_back_impulse")["token_fields"] == ["shift", "back", "impulse"]
    assert "back" in runner._stage5_2_profile_for_key("structure_full")["token_fields"]
    assert "back" not in runner._stage5_2_profile_for_key("structure_full_without_back")["token_fields"]


def test_build_stage5_2_features_shapes_and_no_updn():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    df["up_3"] = 999999.0
    X_time = runner.build_stage5_2_features(df, "time_only")
    X_clock_shift = runner.build_stage5_2_features(df, "clock_shift")
    X_back_impulse = runner.build_stage5_2_features(df, "clock_shift_back_impulse")
    X_structure = runner.build_stage5_2_features(df, "structure_full")

    assert X_time.shape == (len(df), 4)
    assert X_clock_shift.shape == (len(df), 104)
    assert X_back_impulse.shape == (len(df), 304)
    assert X_structure.shape == (len(df), 904)
    assert np.isfinite(X_structure).all()


def test_stage5_2_regression_metrics_include_auc_mae_spearman_and_calibration():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    y_true = np.array([1, 2, 3, 4, 5, 7, 7], dtype=float)
    y_pred = np.array([1.2, 2.2, 2.8, 4.2, 5.2, 6.5, 6.8], dtype=float)

    metrics = runner.stage5_2_regression_metrics(y_true, y_pred)

    assert metrics["n"] == 7
    assert metrics["spearman_r"] > 0.9
    assert metrics["mae"] < 0.5
    assert metrics["uncensored_mae"] < 0.5
    assert 0.0 <= metrics["auc_true_ge_4"] <= 1.0
    assert metrics["fixed_threshold"]["threshold"] == 4
    assert metrics["fixed_threshold"]["predicted_entries"] == 4
    assert len(metrics["calibration_table"]) == 3
    assert metrics["pred_summary"]["min"] == pytest.approx(1.2)
    assert metrics["pred_summary"]["max"] == pytest.approx(6.8)
    assert metrics["pred_summary"]["std"] > 0.0
    assert metrics["pred_summary"]["unique_rounded_4"] == 7


def test_stage5_2_constant_baseline_metrics_are_defined():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    y_true = np.array([1, 2, 7, 7], dtype=float)
    metrics = runner.stage5_2_constant_baseline_metrics(y_true)

    assert metrics["prediction_value"] == 7
    assert metrics["mae"] == pytest.approx((6 + 5 + 0 + 0) / 4)
    assert metrics["spearman_r"] == 0.0


def test_stage5_2_gate_results_require_oracle_model_and_baseline_improvement():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    summary = {
        "best_profile": {
            "profile": "clock_shift_back_impulse",
            "val_stop": {
                "spearman_r": 0.35,
                "mae": 2.5,
                "auc_true_ge_4": 0.72,
                "yearly": {"2021": {"spearman_r": 0.32}, "2022": {"spearman_r": 0.31}},
            },
            "improvement_vs_constant": {
                "spearman_delta": 0.35,
                "mae_improvement_frac": 0.12,
            },
            "improvement_vs_time_only": {"spearman_delta": 0.04},
            "improvement_vs_clock_shift": {"spearman_delta": 0.05},
        }
    }
    oracle = {
        "pass": True,
        "oracle_time_pf": 1.4,
        "oracle_binary_pf": 1.1,
        "trades_per_year": 80,
        "yearly": {"2021": {"pf": 1.2}, "2022": {"pf": 1.4}},
    }
    censoring = {"train_core": {"censoring_rate": 0.60}}

    gates = runner.stage5_2_gate_results(summary, oracle, censoring)

    assert gates["overall_status"] == "CANDIDATE_HYPOTHESIS"
    assert gates["model_gate"]["pass"] is True


def test_stage5_2_oracle_gate_rejects_invalid_binary_comparison():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    summary = {
        "best_profile": {
            "profile": "clock_shift_back_impulse",
            "val_stop": {
                "spearman_r": 0.35,
                "mae": 2.5,
                "auc_true_ge_4": 0.72,
                "yearly": {"2021": {"spearman_r": 0.32}, "2022": {"spearman_r": 0.31}},
            },
            "improvement_vs_constant": {
                "spearman_delta": 0.35,
                "mae_improvement_frac": 0.12,
            },
            "improvement_vs_time_only": {"spearman_delta": 0.04},
            "improvement_vs_clock_shift": {"spearman_delta": 0.05},
        }
    }
    oracle = {
        "pass": True,
        "oracle_time_pf": 1.6,
        "oracle_binary_pf": float("inf"),
        "pf_delta_vs_binary": None,
        "trades_per_year": 1000,
        "yearly": {"2021": {"pf": 1.2}, "2022": {"pf": 1.4}},
    }
    censoring = {"train_core": {"censoring_rate": 0.60}}

    gates = runner.stage5_2_gate_results(summary, oracle, censoring)

    assert gates["overall_status"] == "ORACLE_FAILED"
    assert gates["oracle_gate"]["pass"] is False
    assert gates["oracle_gate"]["reason"] == "invalid_oracle_binary_comparison"


def test_stage5_2_first_touch_trade_result_tp_sl_and_timeout():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    buy_tp = runner.stage5_2_first_touch_trade_result(
        entry_price=100.0,
        stop_price=98.0,
        take_price=104.0,
        side="buy",
        future_bars=[
            {"high": 103.0, "low": 99.0},
            {"high": 104.5, "low": 99.5},
        ],
    )
    sell_sl = runner.stage5_2_first_touch_trade_result(
        entry_price=100.0,
        stop_price=102.0,
        take_price=96.0,
        side="sell",
        future_bars=[
            {"high": 102.5, "low": 99.0},
            {"high": 101.0, "low": 95.5},
        ],
    )
    timeout = runner.stage5_2_first_touch_trade_result(
        entry_price=100.0,
        stop_price=98.0,
        take_price=104.0,
        side="buy",
        future_bars=[{"high": 101.0, "low": 99.0}],
    )

    assert buy_tp["outcome"] == "TP"
    assert buy_tp["pnl_r"] == pytest.approx(2.0)
    assert sell_sl["outcome"] == "SL"
    assert sell_sl["pnl_r"] == pytest.approx(-1.0)
    assert timeout["outcome"] == "TIMEOUT"
    assert timeout["pnl_r"] == pytest.approx(0.0)


def test_evaluate_stage5_2_profile_seed_returns_regression_metrics():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    df["sell_bars_to_breach_H6_off05"] = np.where(
        df["sell_stop_broken_H6_off05_flag"] == 1.0, 2, 7
    )
    split = runner.build_stage5_1_split(df, "sell_bars_to_breach_H6_off05")

    result = runner.evaluate_stage5_2_profile_seed(
        split,
        "clock_shift_back",
        "sell_bars_to_breach_H6_off05",
        seed=42,
    )

    assert result["profile"] == "clock_shift_back"
    assert result["target"] == "sell_bars_to_breach_H6_off05"
    assert result["seed"] == 42
    assert "spearman_r" in result["val_stop"]
    assert "mae" in result["val_stop"]
    assert "auc_true_ge_4" in result["val_stop"]
    assert "pred_summary" in result["val_stop"]


def test_evaluate_stage5_2_profile_seed_uses_stable_squarederror_objective(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    df["sell_bars_to_breach_H6_off05"] = np.where(
        df["sell_stop_broken_H6_off05_flag"] == 1.0, 2, 7
    )
    split = runner.build_stage5_1_split(df, "sell_bars_to_breach_H6_off05")
    seen = {}

    class DummyRegressor:
        def __init__(self, **kwargs):
            seen.update(kwargs)

        def fit(self, X, y):
            self.n_features_ = X.shape[1]
            return self

        def predict(self, X):
            return np.linspace(2.0, 7.0, len(X))

    monkeypatch.setattr(runner.xgb, "XGBRegressor", DummyRegressor)

    result = runner.evaluate_stage5_2_profile_seed(
        split,
        "clock_shift_back",
        "sell_bars_to_breach_H6_off05",
        seed=42,
    )

    assert seen["objective"] == "reg:squarederror"
    assert result["val_stop"]["pred_summary"]["std"] > 0.0


def test_summarize_stage5_2_target_selects_best_profile_and_baselines():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    target = "sell_bars_to_breach_H6_off05"
    raw_runs = []
    for profile, rho, mae in [
        ("time_only", 0.10, 3.5),
        ("clock_shift", 0.12, 3.4),
        ("clock_shift_back", 0.35, 2.7),
    ]:
        raw_runs.append({
            "target": target,
            "profile": profile,
            "seed": 42,
            "val_stop": {"spearman_r": rho, "mae": mae, "auc_true_ge_4": 0.71},
            "diagnostic_holdout": {"spearman_r": rho - 0.05, "mae": mae + 0.2},
        })

    summary = runner.summarize_stage5_2_target(raw_runs, target)

    assert summary["best_profile"]["profile"] == "clock_shift_back"
    assert summary["best_profile"]["improvement_vs_time_only"]["spearman_delta"] == pytest.approx(0.25)
    assert summary["best_profile"]["improvement_vs_clock_shift"]["spearman_delta"] == pytest.approx(0.23)


def test_stage5_2_runner_writes_json(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    df["sell_bars_to_breach_H6_off05"] = np.where(
        df["sell_stop_broken_H6_off05_flag"] == 1.0, 2, 7
    )
    df["buy_bars_to_breach_H6_off05"] = np.where(
        df["buy_stop_broken_H6_off05_flag"] == 1.0, 2, 7
    )
    target_splits = {"sell": (df, df, df), "buy": (df, df, df)}

    monkeypatch.setattr(
        runner,
        "run_stage5_2_oracle_preflight",
        lambda split, target_col, binary_col, ohlc_path=runner.OHLC_FILE: {
            "pass": True,
            "oracle_time_pf": 1.5,
            "oracle_binary_pf": 1.1,
            "trades_per_year": 80,
            "yearly": {"2021": {"pf": 1.2}, "2022": {"pf": 1.4}},
        },
    )
    monkeypatch.setattr(
        runner,
        "evaluate_stage5_2_profile_seed",
        lambda split, profile, target, seed, xgb_threads=1: {
            "profile": profile,
            "target": target,
            "seed": seed,
            "elapsed_sec": 1.25,
            "val_stop": {"spearman_r": 0.35, "mae": 2.5, "auc_true_ge_4": 0.72},
            "diagnostic_holdout": {"spearman_r": 0.30, "mae": 2.8, "auc_true_ge_4": 0.69},
        },
    )
    monkeypatch.setattr(
        runner,
        "summarize_stage5_2_target",
        lambda raw_runs, target: {
            "profiles": {},
            "best_profile": {
                "profile": "clock_shift_back_impulse",
                "val_stop": {
                    "spearman_r": 0.35,
                    "mae": 2.5,
                    "auc_true_ge_4": 0.72,
                    "yearly": {"2021": {"spearman_r": 0.31}, "2022": {"spearman_r": 0.32}},
                },
                "improvement_vs_constant": {
                    "spearman_delta": 0.35,
                    "mae_improvement_frac": 0.12,
                },
                "improvement_vs_time_only": {"spearman_delta": 0.04},
                "improvement_vs_clock_shift": {"spearman_delta": 0.04},
            },
        },
    )

    report = runner.run_stage5_2_time_to_breach_regression(
        target_splits,
        output_path=tmp_path / "stage5_2.json",
    )

    assert report["stage"] == "5.2_time_to_breach_regression"
    assert report["status"] in {"CANDIDATE_HYPOTHESIS", "MODEL_GATE_FAILED", "ORACLE_FAILED", "DIAGNOSTIC_ONLY"}
    assert report["progress"]["done_runs"] == 42
    assert report["progress"]["run_elapsed_sec"] == [1.25] * 42
    assert (tmp_path / "stage5_2.json").exists()


def test_stage5_2_cli_argument_exists_in_build_arg_parser():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = runner.build_arg_parser()
    args = parser.parse_args(["--stage5-2-time-to-breach-regression"])

    assert args.stage5_2_time_to_breach_regression is True


def test_stage5_2_cli_parallel_arguments_exist_in_build_arg_parser():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = runner.build_arg_parser()
    args = parser.parse_args([
        "--stage5-2-time-to-breach-regression",
        "--stage5-2-workers", "8",
        "--stage5-2-xgb-threads", "4",
    ])

    assert args.stage5_2_workers == 8
    assert args.stage5_2_xgb_threads == 4


def test_stage5_2_runner_uses_process_pool_for_parallel_jobs(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    df["sell_bars_to_breach_H6_off05"] = np.where(
        df["sell_stop_broken_H6_off05_flag"] == 1.0, 2, 7
    )
    df["buy_bars_to_breach_H6_off05"] = np.where(
        df["buy_stop_broken_H6_off05_flag"] == 1.0, 2, 7
    )
    monkeypatch.setattr(runner, "STAGE5_2_TARGETS", ["sell_bars_to_breach_H6_off05"])
    monkeypatch.setattr(runner, "STAGE5_2_PROFILE_KEYS", ["time_only", "clock_shift"])
    monkeypatch.setattr(runner, "STAGE5_2_SEEDS", [42])
    monkeypatch.setattr(
        runner,
        "run_stage5_2_oracle_preflight",
        lambda split, target_col, binary_col, ohlc_path=runner.OHLC_FILE: {
            "pass": True,
            "oracle_time_pf": 1.5,
            "oracle_binary_pf": 1.1,
            "trades_per_year": 80,
            "yearly": {"2021": {"pf": 1.2}, "2022": {"pf": 1.4}},
        },
    )
    monkeypatch.setattr(runner, "summarize_stage5_2_target", lambda raw_runs, target: {"best_profile": {}})

    seen = {"max_workers": None, "jobs": []}

    class FakeExecutor:
        def __init__(self, max_workers):
            seen["max_workers"] = max_workers

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn, job):
            seen["jobs"].append((job["profile"], job["seed"], job["xgb_threads"]))
            fut = Future()
            fut.set_result(fn(job))
            return fut

    def fake_worker(job):
        return {
            "profile": job["profile"],
            "target": job["target"],
            "seed": job["seed"],
            "elapsed_sec": 0.5,
            "val_stop": {"spearman_r": 0.35, "mae": 2.5, "auc_true_ge_4": 0.72},
            "diagnostic_holdout": {"spearman_r": 0.30, "mae": 2.8, "auc_true_ge_4": 0.69},
            "low_n_disclosure": {"n": 0},
            "yearly_val": {},
            "yearly_diagnostic_holdout": {},
        }

    monkeypatch.setattr(runner, "ProcessPoolExecutor", FakeExecutor)
    monkeypatch.setattr(runner, "_run_stage5_2_job", fake_worker)

    report = runner.run_stage5_2_time_to_breach_regression(
        {"sell": (df, df, df), "buy": (df, df, df)},
        output_path=tmp_path / "stage5_2_parallel.json",
        workers=2,
        xgb_threads=4,
    )

    assert seen["max_workers"] == 2
    assert seen["jobs"] == [("time_only", 42, 4), ("clock_shift", 42, 4)]
    assert report["progress"]["done_runs"] == 2


def test_stage5_3_constants_and_target_specs_are_frozen():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_3_SOURCE_TARGETS == [
        "sell_bars_to_breach_H6_off05",
        "buy_bars_to_breach_H6_off05",
    ]
    assert runner.STAGE5_3_PROFILE_KEYS == [
        "time_only",
        "clock_shift",
        "clock_shift_back",
        "clock_shift_impulse",
        "clock_shift_back_impulse",
        "structure_full",
    ]
    assert [s["name"] for s in runner.STAGE5_3_MAIN_TARGET_SPECS] == [
        "breach_after_k2",
        "breach_after_k3",
        "breach_after_k4",
        "breach_after_k5",
        "fast",
        "medium",
        "no_breach",
    ]
    assert [s["name"] for s in runner.STAGE5_3_BINARY_BASELINE_SPECS] == [
        "binary_breach",
    ]
    assert [s["name"] for s in runner.STAGE5_3_CONTROL_TARGET_SPECS] == [
        "survives_at_least_k2",
        "survives_at_least_k3",
        "survives_at_least_k4",
        "survives_at_least_k5",
    ]
    assert str(runner.STAGE5_3_JSON_REPORT_PATH).endswith(
        "stage5_3_time_to_breach_target_reformulation.json"
    )


def test_stage5_3_make_binary_target_for_breach_after_k_and_buckets():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    y = np.array([1, 2, 3, 4, 5, 6, 7, np.nan], dtype=float)

    assert runner.stage5_3_make_binary_target(
        y, {"family": "breach_after_k", "k": 3}
    ).tolist() == [0, 0, 0, 1, 1, 1, 0, -1]
    assert runner.stage5_3_make_binary_target(
        y, {"family": "survives_at_least_k", "k": 3}
    ).tolist() == [0, 0, 0, 1, 1, 1, 1, -1]
    assert runner.stage5_3_make_binary_target(
        y, {"family": "bucket", "bucket": "fast"}
    ).tolist() == [1, 1, 0, 0, 0, 0, 0, -1]
    assert runner.stage5_3_make_binary_target(
        y, {"family": "bucket", "bucket": "medium"}
    ).tolist() == [0, 0, 1, 1, 1, 1, 0, -1]
    assert runner.stage5_3_make_binary_target(
        y, {"family": "bucket", "bucket": "no_breach"}
    ).tolist() == [0, 0, 0, 0, 0, 0, 1, -1]


def test_stage5_3_make_binary_target_from_frame_for_binary_breach_baseline():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = pd.DataFrame({
        "sell_bars_to_breach_H6_off05": [1, 7, 4, np.nan],
        "sell_stop_broken_H6_off05_flag": [1.0, 0.0, 1.0, np.nan],
    })

    y = runner.stage5_3_make_binary_target_from_frame(
        df,
        "sell_bars_to_breach_H6_off05",
        {"name": "binary_breach", "family": "binary_breach", "role": "baseline"},
    )

    assert y.tolist() == [1, 0, 1, -1]


def test_stage5_3_binary_metrics_include_auc_pr_auc_and_threshold_counts():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    y_true = np.array([0, 0, 1, 1], dtype=int)
    y_score = np.array([0.1, 0.3, 0.7, 0.9], dtype=float)

    metrics = runner.stage5_3_binary_metrics(y_true, y_score)

    assert metrics["n"] == 4
    assert metrics["positive_rate"] == pytest.approx(0.5)
    assert metrics["auc"] == pytest.approx(1.0)
    assert metrics["pr_auc"] == pytest.approx(1.0)
    assert metrics["pred_summary"]["std"] > 0.0
    assert metrics["threshold_0_5"]["predicted_positive"] == 2
    assert metrics["threshold_0_5"]["precision"] == pytest.approx(1.0)
    assert metrics["threshold_0_5"]["recall"] == pytest.approx(1.0)


def test_stage5_3_gate_requires_main_target_auc_lift_and_yearly_consistency():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    summary = {
        "best_main": {
            "target_id": "sell_breach_after_k3",
            "spec": {"role": "main"},
            "profile": "clock_shift_back",
            "val_stop": {
                "auc": 0.70,
                "pr_auc": 0.42,
                "positive_rate": 0.30,
                "yearly": {"2021": {"auc": 0.61}, "2022": {"auc": 0.62}},
            },
            "binary_breach_baseline": {"same_profile_val_auc": 0.66, "auc_delta": 0.04},
            "improvement_vs_time_only": {"auc_delta": 0.04},
            "improvement_vs_clock_shift": {"auc_delta": 0.05},
            "seed_consistency": {"auc_delta_vs_binary_positive_count": 2, "n_seeds": 3},
        }
    }

    gate = runner.stage5_3_gate_results(summary)

    assert gate["overall_status"] == "TARGET_REFORMULATION_FOUND"
    assert gate["model_gate"]["pass"] is True


def test_evaluate_stage5_3_profile_seed_returns_binary_metrics(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    df["sell_bars_to_breach_H6_off05"] = np.where(
        df["sell_stop_broken_H6_off05_flag"] == 1.0, 4, 7
    )
    split = runner.build_stage5_1_split(df, "sell_bars_to_breach_H6_off05")
    spec = {"name": "breach_after_k3", "family": "breach_after_k", "k": 3, "role": "main"}

    result = runner.evaluate_stage5_3_profile_seed(
        split,
        "sell_bars_to_breach_H6_off05",
        spec,
        "clock_shift_back",
        seed=42,
    )

    assert result["source_target"] == "sell_bars_to_breach_H6_off05"
    assert result["target_id"] == "sell_breach_after_k3"
    assert result["profile"] == "clock_shift_back"
    assert result["seed"] == 42
    assert "auc" in result["val_stop"]
    assert "pr_auc" in result["val_stop"]
    assert "yearly_val" in result
    assert "predictions" not in result
    assert "labels" not in result
    assert "feature_importance_gain_top20" in result


def test_summarize_stage5_3_source_selects_best_main_and_keeps_controls():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    source = "sell_bars_to_breach_H6_off05"
    raw_runs = []
    for target_id, role, profile, auc in [
        ("sell_breach_after_k3", "main", "time_only", 0.58),
        ("sell_breach_after_k3", "main", "clock_shift_back", 0.69),
        ("sell_binary_breach", "baseline", "clock_shift_back", 0.66),
        ("sell_survives_at_least_k3", "control", "clock_shift_back", 0.75),
    ]:
        raw_runs.append({
            "source_target": source,
            "target_id": target_id,
            "spec": {"name": target_id.replace("sell_", ""), "role": role},
            "profile": profile,
            "seed": 42,
            "val_stop": {"auc": auc, "pr_auc": 0.40, "positive_rate": 0.30},
            "diagnostic_holdout": {"auc": auc - 0.05, "pr_auc": 0.35, "positive_rate": 0.30},
            "yearly_val": {"2021": {"auc": 0.61}, "2022": {"auc": 0.62}},
        })

    summary = runner.summarize_stage5_3_source(raw_runs, source)

    assert summary["best_main"]["target_id"] == "sell_breach_after_k3"
    assert summary["best_main"]["profile"] == "clock_shift_back"
    assert summary["best_control"]["target_id"] == "sell_survives_at_least_k3"
    assert summary["best_main"]["improvement_vs_time_only"]["auc_delta"] == pytest.approx(0.11)
    assert summary["best_main"]["binary_breach_baseline"]["auc_delta"] == pytest.approx(0.03)


def test_stage5_3_runner_writes_json(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    df["sell_bars_to_breach_H6_off05"] = np.where(
        df["sell_stop_broken_H6_off05_flag"] == 1.0, 4, 7
    )
    df["buy_bars_to_breach_H6_off05"] = np.where(
        df["buy_stop_broken_H6_off05_flag"] == 1.0, 4, 7
    )
    monkeypatch.setattr(runner, "STAGE5_3_MAIN_TARGET_SPECS", [
        {"name": "breach_after_k3", "family": "breach_after_k", "k": 3, "role": "main"}
    ])
    monkeypatch.setattr(runner, "STAGE5_3_CONTROL_TARGET_SPECS", [])
    monkeypatch.setattr(runner, "STAGE5_3_BINARY_BASELINE_SPECS", [])
    monkeypatch.setattr(runner, "STAGE5_3_TARGET_SPECS", runner.STAGE5_3_MAIN_TARGET_SPECS)
    monkeypatch.setattr(runner, "STAGE5_3_PROFILE_KEYS", ["time_only", "clock_shift_back"])
    monkeypatch.setattr(runner, "STAGE5_3_SEEDS", [42])
    monkeypatch.setattr(
        runner,
        "evaluate_stage5_3_profile_seed",
        lambda split, source_target, spec, profile, seed, xgb_threads=1, feature_split=None: {
            "source_target": source_target,
            "target_id": runner.stage5_3_target_id(source_target, spec),
            "spec": dict(spec),
            "profile": profile,
            "seed": seed,
            "elapsed_sec": 0.5,
            "val_stop": {"auc": 0.68, "pr_auc": 0.42, "positive_rate": 0.30},
            "diagnostic_holdout": {"auc": 0.62, "pr_auc": 0.36, "positive_rate": 0.30},
            "yearly_val": {"2021": {"auc": 0.61}, "2022": {"auc": 0.62}},
            "yearly_diagnostic_holdout": {},
        },
    )

    report = runner.run_stage5_3_target_reformulation(
        {"sell": (df, df, df), "buy": (df, df, df)},
        output_path=tmp_path / "stage5_3.json",
    )

    assert report["stage"] == "5.3_time_to_breach_target_reformulation"
    assert report["progress"]["done_runs"] == 4
    assert report["progress"]["total_runs"] == 4
    assert set(report["summary"]) == set(runner.STAGE5_3_SOURCE_TARGETS)
    assert (tmp_path / "stage5_3.json").exists()


def test_stage5_3_cli_arguments_exist_in_build_arg_parser():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = runner.build_arg_parser()
    args = parser.parse_args([
        "--stage5-3-target-reformulation",
        "--stage5-3-workers", "8",
        "--stage5-3-xgb-threads", "4",
    ])

    assert args.stage5_3_target_reformulation is True
    assert args.stage5_3_workers == 8
    assert args.stage5_3_xgb_threads == 4
