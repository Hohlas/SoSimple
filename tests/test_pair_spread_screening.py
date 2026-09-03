# tests/test_pair_spread_screening.py
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_MODULE_PATH = Path(__file__).resolve().parents[1] / 'statistics' / 'pair_spread' / 'screening.py'
_spec = importlib.util.spec_from_file_location('screening', _MODULE_PATH)
screening = importlib.util.module_from_spec(_spec)
sys.modules['screening'] = screening  # dataclass-аннотации резолвятся через sys.modules (аудит К-1)
_spec.loader.exec_module(screening)


def test_fit_beta_known_value():
    rng = np.random.RandomState(0)
    b = np.cumsum(rng.randn(5000)) + 100
    a = 3.0 + 1.5 * b + rng.randn(5000) * 0.01
    assert abs(screening.fit_beta(a, b) - 1.5) < 0.01


def test_half_life_known_rho():
    # AR(1) с rho=0.99 -> полураспад = -ln2/ln0.99 ≈ 68.97 баров
    rng = np.random.RandomState(1)
    n = 200000
    s = np.empty(n)
    s[0] = 0.0
    for i in range(1, n):
        s[i] = 0.99 * s[i - 1] + rng.randn() * 0.01
    hl = screening.half_life_bars(pd.Series(s))
    assert abs(hl - (-np.log(2) / np.log(0.99))) / 69.0 < 0.10


def test_half_life_antipersistent_is_inf():
    # чередующийся ряд: rho < 0 -> полураспад не определён (inf), детерминированно.
    # Примечание (аудит К-2.2): random walk даёт конечный полураспад (OLS rho<1),
    # от random walk полураспад-гейт не защищает — это делает EG-гейт.
    s = pd.Series(np.tile([1.0, -1.0], 2500))
    assert screening.half_life_bars(s) == float('inf')


def test_engle_granger_stationary_pair_low_p():
    rng = np.random.RandomState(3)
    x = np.cumsum(rng.randn(3000))          # random walk
    y = 2.0 + 0.8 * x + rng.randn(3000) * 0.1  # коинтегрирован с x
    p = screening.engle_granger_pvalue(y, x)
    assert p < 0.01


def test_engle_granger_independent_walks_high_p():
    # сид 2 проверен до коммита: p ≈ 0.96 (аудит К-2.3: сид 4 давал p=0.013)
    rng = np.random.RandomState(2)
    x = np.cumsum(rng.randn(3000))
    y = np.cumsum(rng.randn(3000))
    p = screening.engle_granger_pvalue(y, x)
    assert p > 0.10


def test_episode_bounds_basic():
    z = pd.Series([0.0, 2.5, 2.6, 1.2, 0.9, 0.1, -2.2, -0.8])
    eps = screening.episode_bounds(z, entry_z=2.0)
    # первый эпизод: старт 1 (|2.5|), половина = 1.25, бар 3: |1.2| <= 1.25 -> конец 3
    assert eps[0] == (1, 3)
    # второй эпизод: старт 6 (|-2.2|), половина = 1.1, бар 7: |-0.8| <= 1.1 -> конец 7
    assert eps[1] == (6, 7)


def test_episode_ignores_continuation():
    # |z| остаётся >= 2 подряд — это один эпизод, не несколько
    z = pd.Series([2.5, 2.7, 2.9, 0.5])
    eps = screening.episode_bounds(z, entry_z=2.0)
    assert len(eps) == 1
    assert eps[0][0] == 0


def test_spread_mu_sigma():
    s = pd.Series([1.0, 2.0, 3.0])
    mu, sigma = screening.spread_mu_sigma(s)
    assert mu == 2.0
    assert abs(sigma - np.std([1.0, 2.0, 3.0], ddof=1)) < 1e-12


def test_screening_metrics_episode_durations():
    # эпизоды те же, что в test_episode_bounds_basic: (1,3) и (6,7) -> длины 2 и 1
    idx = pd.date_range('2010-01-01', periods=8, freq='5min')
    z = pd.Series([0.0, 2.5, 2.6, 1.2, 0.9, 0.1, -2.2, -0.8], index=idx)
    s = pd.Series(np.linspace(0.0, 0.7, 8), index=idx)
    m = screening.screening_metrics(s, z, cost_c=0.001,
                                    thresholds=screening.ScreeningThresholds())
    assert m['n_episodes'] == 2
    assert m['episode_durations_bars'] == [2, 1]
    assert m['median_episode_duration_bars'] == 1.5


def test_verdict_all_pass():
    th = screening.ScreeningThresholds()
    metrics = {
        'coint_p': 0.01, 'half_life_bars': 100.0,
        'cost_c': 0.001, 'p75_abs_ds': 0.005,
        'median_episode_deviation': 0.01, 'episodes_per_year': 8.0,
    }
    ok, reasons = screening.verdict_pass(metrics, th)
    assert ok and reasons == []


def test_verdict_kills_on_each_gate():
    th = screening.ScreeningThresholds()
    base = {
        'coint_p': 0.01, 'half_life_bars': 100.0,
        'cost_c': 0.001, 'p75_abs_ds': 0.005,
        'median_episode_deviation': 0.01, 'episodes_per_year': 8.0,
    }
    for key, bad in [('coint_p', 0.2), ('half_life_bars', 2.0),
                     ('p75_abs_ds', 0.0005), ('median_episode_deviation', 0.0005),
                     ('episodes_per_year', 1.0)]:
        m = dict(base, **{key: bad})
        ok, reasons = screening.verdict_pass(m, th)
        assert not ok and len(reasons) >= 1


def test_screening_metrics_empty_input_raises():
    idx = pd.date_range('2010-01-01', periods=0, freq='5min')
    s = pd.Series([], index=idx, dtype=float)
    z = pd.Series([], index=idx, dtype=float)
    try:
        screening.screening_metrics(s, z, cost_c=0.001,
                                    thresholds=screening.ScreeningThresholds())
        assert False, "expected ValueError"
    except ValueError as e:
        assert "empty" in str(e).lower()


def test_screening_metrics_length_mismatch_raises():
    idx = pd.date_range('2010-01-01', periods=5, freq='5min')
    s = pd.Series(np.ones(5), index=idx)
    z = pd.Series(np.ones(4), index=idx[:4])
    try:
        screening.screening_metrics(s, z, cost_c=0.001,
                                    thresholds=screening.ScreeningThresholds())
        assert False, "expected ValueError"
    except ValueError as e:
        assert "mismatch" in str(e).lower()
