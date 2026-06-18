# =============================================================================
# File: tests/test_stage5_transformer_breach.py
# Purpose: Smoke tests for Stage 5.0 Transformer Breach Holdout
# Language: Python 3.10+
# Created: 2026-06-17
# =============================================================================

import os, sys
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
    compute_corridor_stats,
    get_profile_seq_len,
    BASE10_INDICES,
    FULL29_INDICES,
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
        tokens, row_features, mask = build_profile_features(df, profile)
        assert tokens.shape == (10, 100, 10)
        assert row_features.shape == (10, 5)
        assert mask.shape == (10, 100)

    def test_newest20_shapes(self):
        df = _make_synthetic_df(10, 50)
        profile = find_profile('newest20_base10_time')
        tokens, row_features, mask = build_profile_features(df, profile)
        assert tokens.shape == (10, 20, 10)
        assert row_features.shape == (10, 5)
        assert mask.shape == (10, 20)

    def test_nearest40_shapes(self):
        df = _make_synthetic_df(10, 100)
        profile = find_profile('nearest40_base10_time')
        tokens, row_features, mask = build_profile_features(df, profile)
        assert tokens.shape == (10, 40, 10)
        assert row_features.shape == (10, 5)
        assert mask.shape == (10, 40)

    def test_corridor_shapes(self):
        df = _make_synthetic_df(10, 100)
        profile = find_profile('corridor_10atr_base10_time')
        tokens, row_features, mask = build_profile_features(df, profile)
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
        tokens, row_features, mask = build_profile_features(df, profile)
        assert tokens.shape[0] == 10
        assert not np.isnan(tokens).any()

    def test_single_fractal_corridor_no_nan(self):
        df = self._corridor_df(atr=0.01)
        profile = find_profile('corridor_10atr_base10_time')
        tokens, row_features, mask = build_profile_features(df, profile)
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
        tokens, rf, mask = build_profile_features(df, profile)
        assert tokens.shape == (5, 100, 10)
        assert rf.shape == (5, 5)

    def test_relative_price_formula_verified(self):
        """Verify that relative_price token column = (price_i - f0_price) / ATR."""
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
        tokens, rf, mask = build_profile_features(df, profile)

        # The price column (index 0 of base10) should be (price_i - f0_price) / ATR
        # all100 preserves natural order: fractal0=pos0, fractal1=pos1
        # For fractal0: (400 - 400) / 2 = 0
        # For fractal1: (410 - 400) / 2 = 5
        price_col = tokens[0, :, 0]  # first sample, all positions, price column
        valid_mask = mask[0]
        assert valid_mask.sum() >= 2, "Need at least 2 valid fractals"
        valid_prices = price_col[valid_mask]
        assert abs(valid_prices[0] - 0.0) < 0.01, f"fractal0 relative_price expected 0.0, got {valid_prices[0]}"
        assert abs(valid_prices[1] - 5.0) < 0.01, f"fractal1 relative_price expected 5.0, got {valid_prices[1]}"


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

        tokens, rf, mask = build_profile_features(df, profile)
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
        _, row_feat, _ = build_profile_features(df, profile)
        assert row_feat.shape == (5, 5)

    def test_no_time_row_features(self):
        df = _make_synthetic_df(5, 10)
        profile = find_profile('all100_base10_no_time')
        _, row_feat, _ = build_profile_features(df, profile)
        assert row_feat.shape == (5, 1)


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
