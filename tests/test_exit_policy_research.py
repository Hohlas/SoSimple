import pandas as pd
import pytest

import API.exit_policy_research as epr


def test_close_on_reverse_signal_triggers_when_opposite_ratio_crosses_threshold():
    trade = pd.DataFrame({
        'bar': [0, 1, 2],
        'signal': [1, 1, 1],
        'ratio_up': [4.0, 2.8, 1.5],
        'ratio_dn': [0.2, 0.8, 2.6],
        'net_atr': [0.2, 0.6, 0.4],
    })

    policy = {'name': 'reverse_close', 'reverse_ratio': 2.5}
    out = epr.simulate_trade_exit(trade, policy)

    assert out['exit_bar'] == 2
    assert out['reason'] == 'reverse_ratio'


def test_close_on_weak_edge_respects_min_hold_bars():
    trade = pd.DataFrame({
        'bar': [0, 1, 2, 3],
        'signal': [1, 1, 1, 1],
        'ratio_up': [3.5, 1.8, 1.4, 1.2],
        'ratio_dn': [0.4, 0.7, 0.9, 1.1],
        'net_atr': [0.1, 0.4, 0.2, 0.1],
    })

    policy = {'name': 'weak_edge_close', 'keep_ratio_min': 1.6, 'min_hold_bars': 2}
    out = epr.simulate_trade_exit(trade, policy)

    assert out['exit_bar'] == 2
    assert out['reason'] == 'weak_edge'


def test_close_on_profit_guard_requires_prior_favorable_excursion():
    trade = pd.DataFrame({
        'bar': [0, 1, 2],
        'signal': [1, 1, 1],
        'ratio_up': [3.0, 1.7, 1.6],
        'ratio_dn': [0.3, 0.6, 0.8],
        'net_atr': [0.2, 0.4, 0.1],
        'fav_atr': [0.2, 1.2, 1.2],
    })

    policy = {
        'name': 'profit_guard_close',
        'profit_start_atr': 1.0,
        'keep_ratio_min': 1.8,
        'min_hold_bars': 1,
    }
    out = epr.simulate_trade_exit(trade, policy)

    assert out['exit_bar'] == 1
    assert out['reason'] == 'profit_guard'


def test_rank_policies_sorts_by_pf_then_keeps_trade_floor():
    table = pd.DataFrame([
        {'policy': 'a', 'pf': 1.4, 'trades': 120},
        {'policy': 'b', 'pf': 1.6, 'trades': 18},
        {'policy': 'c', 'pf': 1.5, 'trades': 90},
    ])

    out = epr.rank_policies(table, min_trades=50)

    assert out.iloc[0]['policy'] == 'c'


def test_render_mql_thresholds_returns_expected_names():
    cfg = epr.render_mql_thresholds({
        'reverse_ratio': 2.2,
        'keep_ratio_min': 1.7,
        'profit_start_atr': 1.0,
    })

    assert 'ML_ExitReverseRatio' in cfg
    assert 'ML_ExitKeepRatio' in cfg


def test_filter_frame_to_split_uses_explicit_validation_time_catalog(tmp_path):
    frame = pd.DataFrame({
        'time': pd.to_datetime([
            '2025-01-01 00:00:00',
            '2025-01-01 01:00:00',
            '2026-01-01 00:00:00',
        ]),
        'value': [10, 20, 30],
    })

    validation_file = tmp_path / 'validation.csv'
    test_file = tmp_path / 'test.csv'
    pd.DataFrame({'time': ['2025.01.01 00:00', '2025.01.01 01:00']}).to_csv(
        validation_file,
        sep=';',
        index=False,
    )
    pd.DataFrame({'time': ['2026.01.01 00:00']}).to_csv(test_file, sep=';', index=False)

    out = epr.filter_frame_to_split(
        frame,
        split_profile='validation_research',
        validation_file=validation_file,
        test_file=test_file,
    )

    assert out['value'].tolist() == [10, 20]


def test_simulate_policy_reprocesses_reverse_bar_for_same_bar_flip():
    frame = pd.DataFrame({
        'time': pd.date_range('2025-01-01 00:00:00', periods=4, freq='h'),
        'signal': [1, -1, 0, 0],
        'close': [100.0, 99.0, 98.0, 97.0],
        'high': [100.0, 99.0, 98.0, 97.0],
        'low': [100.0, 99.0, 98.0, 97.0],
        'atr14': [1.0, 1.0, 1.0, 1.0],
        'ratio_up': [4.0, 1.0, 1.0, 1.0],
        'ratio_dn': [0.2, 3.0, 3.0, 3.0],
    })

    trades = epr.simulate_policy(frame, {'name': 'reverse_close', 'reverse_ratio': 2.5}, max_hold_bars=3)

    assert trades['entry_signal'].tolist() == [1, -1]
    assert trades['reason'].tolist()[0] == 'reverse_ratio'


def test_summarize_policy_result_reports_core_ranking_metrics():
    trades = pd.DataFrame({
        'pnl_atr': [1.2, -0.5, 0.3],
        'exit_bar': [1, 2, 3],
        'blocked_signals': [0, 1, 0],
    })

    out = epr.summarize_policy_result(trades, {'name': 'layered_exit_v1'})

    assert out['policy'] == 'layered_exit_v1'
    assert out['trades'] == 3
    assert out['pf'] == pytest.approx(3.0, abs=1e-9)
    assert out['win_rate'] == pytest.approx(66.6666666667, abs=1e-6)
    assert out['avg_hold_bars'] == pytest.approx(2.0, abs=1e-9)


def test_resolve_policy_candidates_blocks_search_on_test_final():
    with pytest.raises(ValueError, match='frozen policy'):
        epr.resolve_policy_candidates(split_profile='test_final', policy_path=None)


def test_build_policy_library_keeps_timeout_baseline_and_grid_candidates():
    names = [policy['name'] for policy in epr.build_policy_library()]

    assert 'timeout_only' in names
    assert 'reverse_close_r2.0' in names
    assert 'weak_edge_k1.6_h2' in names
    assert 'profit_guard_p1.0_k1.8_h2' in names
