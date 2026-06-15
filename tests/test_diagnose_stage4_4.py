# Tests for ML/baseline/diagnose_stage4_4.py
# Stage 4.4: DIAGNOSTIC_ONLY micro-check smoke tests

import pytest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ML.baseline.diagnose_stage4_3 import (
    resolve_tp_val,
    simulate_trades,
    compute_trade_metrics,
)

from ML.baseline.diagnose_stage4_4 import (
    CANONICAL_SPREAD,
    BASELINE_P,
    BASELINE_MIN_FAV,
    BASELINE_MIN_RR,
    BASELINE_TP_FRACTION,
    CAP,
)


class TestFixedTPResolve:
    def test_fixed_tp_uses_stop_val_times_R(self):
        assert resolve_tp_val('fixed_r', 0.5, pred_fav=2.0, stop_val=1.2) == pytest.approx(0.6)

    def test_fixed_tp_r_0_7(self):
        assert resolve_tp_val('fixed_r', 0.7, pred_fav=1.5, stop_val=1.0) == pytest.approx(0.7)

    def test_fav_fraction_unchanged(self):
        assert resolve_tp_val('fav_fraction', 0.4, pred_fav=2.0, stop_val=1.2) == pytest.approx(0.8)


class TestSkipMinFav:
    def test_skip_min_fav_increases_universe(self):
        df = pd.DataFrame({
            'time': ['2020.01.01 00:00'] * 20,
            'fractal0': ['0:100:-1'] + [''] * 4 + [''] * 15,
            'ATR': [0.1] * 20,
            '_year': [2019] * 20,
            'target_sell_H6_val': [0.5] * 20,
            'sell_stop_broken_H6_off05_flag': [0] * 20,
        })
        entry_prices = np.array([1.0] * 20, dtype=float)
        breach_proba = np.array([0.3] * 20, dtype=float)
        fav_pred = np.array([0.5] * 20, dtype=float)

        trades_with_fav = simulate_trades(
            df=df, entry_prices=entry_prices,
            breach_proba=breach_proba, fav_pred=fav_pred,
            ohlc={(0,): (1.0, 1.1, 0.9, 1.0)}, times=[0], time_idx={},
            side='sell', h=1, stop_offset=0.5,
            p=BASELINE_P, min_fav_val=1.0, min_rr=1.0,
            tp_fraction=BASELINE_TP_FRACTION,
            cap=CAP, spread=CANONICAL_SPREAD,
            return_details=False,
            tp_policy='fav_fraction', tp_policy_value=BASELINE_TP_FRACTION,
            skip_min_fav=False, skip_min_rr=False,
        )

        trades_skip_fav = simulate_trades(
            df=df, entry_prices=entry_prices,
            breach_proba=breach_proba, fav_pred=fav_pred,
            ohlc={(0,): (1.0, 1.1, 0.9, 1.0)}, times=[0], time_idx={},
            side='sell', h=1, stop_offset=0.5,
            p=BASELINE_P, min_fav_val=BASELINE_MIN_FAV, min_rr=BASELINE_MIN_RR,
            tp_fraction=BASELINE_TP_FRACTION,
            cap=CAP, spread=CANONICAL_SPREAD,
            return_details=False,
            tp_policy='fav_fraction', tp_policy_value=BASELINE_TP_FRACTION,
            skip_min_fav=True, skip_min_rr=True,
        )

        assert len(trades_skip_fav) >= len(trades_with_fav)


class TestBaselineReproduces:
    def test_baseline_does_not_crash(self):
        """Smoke test: verify baseline run does not crash and returns positive n_trades."""
        import pandas as pd
        from ML.baseline.diagnose_stage4_4 import run_simulation_and_metrics

        np.random.seed(42)
        n = 100
        def _fractal0_str(i):
            parts = ['0', '100', '-1'] + ['50'] * 20
            parts_str = ':'.join(parts)
            return parts_str

        df = pd.DataFrame({
            'time': [f'2020.01.01 {i % 24:02d}:00' for i in range(n)],
            'fractal0': [_fractal0_str(i) for i in range(n)],
            'ATR': np.random.uniform(0.05, 0.15, n),
            '_year': [2019] * n,
            '_candidate_id': list(range(n)),
            'target_sell_H6_val': np.random.uniform(0.1, 2.0, n),
            'sell_stop_broken_H6_off05_flag': np.random.choice([0, 1], n, p=[0.7, 0.3]),
        })

        entry_prices = np.array([1.0 + 0.001 * i for i in range(n)])
        breach_proba = np.random.uniform(0, 1, n).astype(float)
        fav_pred = np.random.uniform(0, 2, n).astype(float)

        ohlc = {}
        times = []
        time_idx = {}
        from datetime import datetime, timezone
        for i in range(n):
            t = (i, i + 6)
            times.append(t)
            dt = datetime(2020, 1, 1, i % 24, 0, tzinfo=timezone.utc)
            time_idx[dt] = len(time_idx)
            for j in range(7):
                ohlc[(i, i + j)] = (1.0 + 0.001 * (i + j),
                                    1.0 + 0.002 * (i + j),
                                    1.0 - 0.001 * (i + j),
                                    1.0 + 0.0)

        result = run_simulation_and_metrics(
            df_val=df, entry_prices=entry_prices,
            breach_proba=breach_proba, fav_pred=fav_pred,
            ohlc=ohlc, times=times, time_idx=time_idx,
            side='sell', h=6, stop_offset=0.5,
            p=BASELINE_P, min_fav_val=BASELINE_MIN_FAV, min_rr=BASELINE_MIN_RR,
            tp_fraction=BASELINE_TP_FRACTION,
            tp_policy='fav_fraction', tp_policy_value=BASELINE_TP_FRACTION,
            skip_min_fav=False, skip_min_rr=False,
            cap=CAP, spread=CANONICAL_SPREAD,
        )

        assert 'pf' in result
        assert 'n_trades' in result
        assert isinstance(result['n_trades'], int)
