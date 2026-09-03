# tests/test_pair_spread_runner.py
import importlib.util
import sys
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[1] / 'statistics' / 'pair_spread' / 'run_pair_spread.py'
_spec = importlib.util.spec_from_file_location('run_pair_spread', _MODULE_PATH)
runner = importlib.util.module_from_spec(_spec)
sys.modules['run_pair_spread'] = runner
_spec.loader.exec_module(runner)


def test_build_costs_parses_snapshot(tmp_path):
    p = tmp_path / 'costs.csv'
    p.write_text(
        'symbol;point;spread_points;spread_price;swap_long;swap_short;digits\n'
        'EURUSD;0.00001;10;0.00010;-5.0;1.0;5\n'
        'GBPUSD;0.00001;12;0.00012;-3.0;0.5;5\n')
    costs = runner.build_costs(p)
    assert abs(costs['EURUSD']['spread_price'] - 0.00010) < 1e-12
    assert abs(costs['GBPUSD']['swap_long'] - (-3.0)) < 1e-12


def test_round_trip_cost_c_uses_abs_beta():
    # beta отрицательный (mul-кросс) — вес ноги B по модулю
    c = runner.round_trip_cost_c(spread_a_price=0.0001, spread_b_price=0.0001,
                                 price_a=1.0, price_b=1.0, beta=-1.0)
    assert abs(c - 2 * (0.0001 + 0.0001)) < 1e-12


def test_stress_cost_c():
    assert abs(runner.stress_cost_c(0.001, 2.0) - 0.002) < 1e-15
    assert runner.stress_cost_c(0.001, 1.0) == 0.001


def test_pair_verdict_gates():
    base = {'pf': 1.5, 'bs_p05': 1.05, 'n_trades': 150, 'n_per_side_min': 60,
            'eg_p_test': 0.02}
    assert runner.pair_verdict(dict(base)) == 'SURVIVED'
    assert runner.pair_verdict(dict(base, pf=1.2)) == 'KILLED'
    assert runner.pair_verdict(dict(base, bs_p05=0.99)) == 'KILLED'
    assert runner.pair_verdict(dict(base, eg_p_test=0.2)) == 'KILLED'
    assert runner.pair_verdict(dict(base, n_trades=80)) == 'DIAGNOSTIC_ONLY'
    assert runner.pair_verdict(dict(base, n_per_side_min=20)) == 'DIAGNOSTIC_ONLY'
    # приоритет (аудит Q-1): слом коинтеграции убивает даже при малом N
    assert runner.pair_verdict(dict(base, n_trades=40, eg_p_test=0.9)) == 'KILLED'
