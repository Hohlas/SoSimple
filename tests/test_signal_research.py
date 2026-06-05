# =============================================================================
# Файл: tests/test_signal_research.py
# Назначение: Unit и smoke-тесты для API/signal_research.py — статистический контракт
#   research-инструмента: ATR14, excursions, barrier outcomes, фильтрация, отчёты.
# Язык: Python 3.10+
# Обновлён: 2026-04-05
# Зависимости:
#   Входные данные:
#     - синтетические OHLC и signal DataFrame fixtures внутри тестов
#   Выходные данные:
#     - pytest assertions для API/signal_research.py
# Внешние зависимости:
#   - pytest>=8.0, numpy>=1.24, pandas>=2.0
# Использование:
#   ./.venv/bin/python -m pytest tests/test_signal_research.py -q
# Примечания:
#   - тесты фиксируют контракт направленных алиасов (pred_fav/pred_adv), ratio_bin,
#     barrier semantics и discovery/holdout split по calendar boundary
# =============================================================================

import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, 'API')
import signal_research as sr


def _ohlc_frame():
    return pd.DataFrame({
        'time': pd.to_datetime([
            '2026-01-01 00:00',
            '2026-01-01 01:00',
            '2026-01-01 02:00',
            '2026-01-01 03:00',
            '2026-01-01 04:00',
            '2026-01-01 05:00',
        ]),
        'open': [100.0, 100.0, 103.0, 99.0, 105.0, 106.0],
        'high': [101.0, 104.0, 105.0, 106.0, 107.0, 108.0],
        'low': [99.0, 100.0, 98.0, 97.0, 102.0, 104.0],
        'close': [100.0, 103.0, 99.0, 105.0, 106.0, 107.0],
    })


def _signal_row(ts, signal):
    return {
        'time': ts,
        'signal': signal,
        'up_3': 0.30, 'dn_3': 0.10,
        'up_6': 0.40, 'dn_6': 0.20,
        'up_12': 0.50, 'dn_12': 0.25,
        'up_24': 0.60, 'dn_24': 0.35,
        'up_48': 0.70, 'dn_48': 0.45,
    }


def test_compute_atr14_uses_true_range():
    ohlc = pd.DataFrame({
        'time': pd.date_range('2026-01-01', periods=16, freq='h'),
        'open': [
            100.0, 105.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0,
            111.0, 112.0, 113.0, 114.0, 115.0, 116.0, 117.0, 118.0,
        ],
        'high': [
            101.0, 106.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0,
            112.0, 113.0, 114.0, 115.0, 116.0, 117.0, 118.0, 119.0,
        ],
        'low': [
            100.0, 105.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0,
            111.0, 112.0, 113.0, 114.0, 115.0, 116.0, 117.0, 118.0,
        ],
        'close': [
            101.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0,
            112.0, 113.0, 114.0, 115.0, 116.0, 117.0, 118.0, 119.0,
        ],
    })
    atr = sr.compute_atr14(ohlc)
    assert pd.isna(atr.iloc[12])
    assert atr.iloc[13] == pytest.approx(18 / 14, abs=1e-9)


def test_compute_excursions_adds_directional_aliases_and_pullback_windows():
    ohlc = _ohlc_frame()
    df = pd.DataFrame([
        _signal_row(ohlc.loc[0, 'time'], 1),
        _signal_row(ohlc.loc[1, 'time'], -1),
    ])

    exc = sr.compute_excursions(df, ohlc)

    buy = exc.iloc[0]
    sell = exc.iloc[1]

    assert buy['pred_fav_3'] == pytest.approx(0.30, abs=1e-9)
    assert buy['pred_adv_3'] == pytest.approx(0.10, abs=1e-9)
    assert buy['fav_1'] == pytest.approx(4.0, abs=1e-9)
    assert buy['adv_1'] == pytest.approx(0.0, abs=1e-9)
    assert buy['close_net_3'] == pytest.approx(5.0, abs=1e-9)

    assert sell['pred_fav_3'] == pytest.approx(0.10, abs=1e-9)
    assert sell['pred_adv_3'] == pytest.approx(0.30, abs=1e-9)
    assert sell['fav_1'] == pytest.approx(5.0, abs=1e-9)
    assert sell['adv_1'] == pytest.approx(2.0, abs=1e-9)
    assert sell['close_net_3'] == pytest.approx(-3.0, abs=1e-9)


def test_compute_excursions_preserves_pic_price_for_variant3():
    ohlc = _ohlc_frame()
    df = pd.DataFrame([{
        **_signal_row(ohlc.loc[0, 'time'], 1),
        'pic_price': 98.5,
        'atr14': 2.0,
    }])

    exc = sr.compute_excursions(df, ohlc)

    assert exc.iloc[0]['pic_price'] == pytest.approx(98.5, abs=1e-9)


def test_compute_excursions_labels_low_ratio_rows_explicitly():
    ohlc = pd.DataFrame({
        'time': pd.date_range('2026-01-01', periods=20, freq='h'),
        'open': [100.0 + i for i in range(20)],
        'high': [100.5 + i for i in range(20)],
        'low': [99.5 + i for i in range(20)],
        'close': [100.0 + i for i in range(20)],
    })
    df = pd.DataFrame([{
        'time': ohlc.loc[0, 'time'],
        'signal': 1,
        'up_3': 0.30, 'dn_3': 0.10,
        'up_6': 0.40, 'dn_6': 0.20,
        'up_12': 0.10, 'dn_12': 0.20,
        'up_24': 0.60, 'dn_24': 0.35,
        'up_48': 0.70, 'dn_48': 0.45,
    }])

    exc = sr.compute_excursions(df, ohlc)

    assert exc.iloc[0]['ratio_bin'] == '<2'


def test_first_hit_barrier_result_uses_open_distance_when_both_hit_same_bar():
    outcome = sr.first_hit_barrier_result(
        opens=[95.5],
        highs=[106.0],
        lows=[94.0],
        entry_price=100.0,
        signal=1,
        sl=5.0,
        tp=6.0,
    )
    assert outcome == 'SL_FIRST'


def test_build_barrier_outcomes_produces_tp_sl_and_neither_rows():
    ohlc = pd.DataFrame({
        'time': pd.to_datetime([
            '2026-01-01 00:00',
            '2026-01-01 01:00',
            '2026-01-01 02:00',
            '2026-01-01 03:00',
            '2026-01-01 04:00',
            '2026-01-01 05:00',
            '2026-01-01 06:00',
        ]),
        'open':  [100, 100, 100, 100, 100, 100, 100],
        'high':  [100, 106, 103, 102, 100, 100, 100],
        'low':   [100, 100,  94,  99,  99, 100, 100],
        'close': [100, 105,  95, 100, 100, 100, 100],
    })

    exc = pd.DataFrame([
        {'time': ohlc.loc[0, 'time'], 'signal': 1, 'ohlc_idx': 0, 'entry_close': 100.0, 'net_3': 1.0},
        {'time': ohlc.loc[1, 'time'], 'signal': 1, 'ohlc_idx': 1, 'entry_close': 105.0, 'net_3': -1.0},
        {'time': ohlc.loc[3, 'time'], 'signal': 1, 'ohlc_idx': 3, 'entry_close': 100.0, 'net_3': 0.5},
    ])

    outcomes = sr.build_barrier_outcomes(exc, ohlc, horizons=[3], sl_levels=[5], tp_levels=[5])
    assert list(outcomes['outcome']) == ['TP_FIRST', 'SL_FIRST', 'NEITHER']
    assert list(outcomes['pnl']) == [5.0, -5.0, 0.5]


def test_barrier_helpers_handle_empty_outcomes_and_empty_summary():
    outcomes = sr.build_barrier_outcomes(
        pd.DataFrame(),
        _ohlc_frame(),
        horizons=[3],
        sl_levels=[5],
        tp_levels=[5],
    )
    assert outcomes.empty
    assert list(outcomes.columns) == [
        'time', 'signal', 'ratio_bin', 'atr_bucket',
        'pred_fav_3', 'pred_fav_6', 'pred_fav_12',
        'pred_adv_3', 'pred_adv_6', 'pred_adv_12',
        'horizon', 'SL', 'TP', 'outcome', 'pnl',
    ]

    summary = sr.summarize_barrier_outcomes(outcomes)
    assert summary.empty
    assert list(summary.columns) == [
        'horizon', 'SL', 'TP', 'N',
        'tp_first_pct', 'sl_first_pct', 'neither_pct',
        'PF_num', 'AvgPnL_num', 'TotalPnL_num',
    ]


def test_summarize_barrier_outcomes_uses_infinite_pf_when_no_losses():
    outcomes = pd.DataFrame([
        {'horizon': 3, 'SL': 5, 'TP': 5, 'outcome': 'TP_FIRST', 'pnl': 5.0},
        {'horizon': 3, 'SL': 5, 'TP': 5, 'outcome': 'TP_FIRST', 'pnl': 5.0},
    ])

    summary = sr.summarize_barrier_outcomes(outcomes)
    assert summary.iloc[0]['PF_num'] == float('inf')


def test_variant2_reports_smoke(capsys):
    exc = pd.DataFrame([
        {
            'time': pd.Timestamp('2026-01-01 00:00'),
            'signal': 1,
            'ratio_bin': '2-3',
            'atr_bucket': 'Q1',
            'adv_1': 1.0,
            'adv_3': 2.0,
            'fav_1': 4.0,
            'fav_3': 6.0,
            'fav_6': 8.0,
            'adv_6': 3.0,
            'close_net_1': 1.0,
            'close_net_3': 3.0,
            'close_net_6': 4.0,
            'pred_fav_3': 0.2,
            'pred_fav_6': 0.3,
            'pred_fav_12': 0.4,
            'pred_adv_3': 0.1,
            'pred_adv_6': 0.15,
            'mfe_3': 5.0, 'mae_3': 2.0, 'net_3': 2.0,
            'mfe_6': 7.0, 'mae_6': 3.0, 'net_6': 3.0,
            'mfe_12': 10.0, 'mae_12': 4.0, 'net_12': 6.0,
            'mfe_24': 12.0, 'mae_24': 5.0, 'net_24': 7.0,
            'mfe_48': 14.0, 'mae_48': 6.0, 'net_48': 8.0,
        },
        {
            'time': pd.Timestamp('2026-01-01 01:00'),
            'signal': -1,
            'ratio_bin': '5+',
            'atr_bucket': 'Q4',
            'adv_1': 2.0,
            'adv_3': 3.0,
            'fav_1': 3.0,
            'fav_3': 5.0,
            'fav_6': 7.0,
            'adv_6': 4.0,
            'close_net_1': -1.0,
            'close_net_3': 2.0,
            'close_net_6': 3.0,
            'pred_fav_3': 0.8,
            'pred_fav_6': 0.9,
            'pred_fav_12': 1.0,
            'pred_adv_3': 0.4,
            'pred_adv_6': 0.5,
            'mfe_3': 4.0, 'mae_3': 3.0, 'net_3': -1.0,
            'mfe_6': 6.0, 'mae_6': 4.0, 'net_6': 1.0,
            'mfe_12': 9.0, 'mae_12': 5.0, 'net_12': 4.0,
            'mfe_24': 11.0, 'mae_24': 6.0, 'net_24': 5.0,
            'mfe_48': 13.0, 'mae_48': 7.0, 'net_48': 6.0,
        },
    ])

    barriers = pd.DataFrame([
        {
            'horizon': 12, 'SL': 5, 'TP': 10, 'N': 2,
            'tp_first_pct': 50.0, 'sl_first_pct': 25.0, 'neither_pct': 25.0,
            'PF_num': 2.0, 'AvgPnL_num': 3.5, 'TotalPnL_num': 7.0,
        },
        {
            'horizon': 12, 'SL': 10, 'TP': 20, 'N': 2,
            'tp_first_pct': 25.0, 'sl_first_pct': 50.0, 'neither_pct': 25.0,
            'PF_num': 1.5, 'AvgPnL_num': 2.0, 'TotalPnL_num': 4.0,
        },
        {
            'horizon': 6, 'SL': 5, 'TP': 5, 'N': 2,
            'tp_first_pct': 50.0, 'sl_first_pct': 50.0, 'neither_pct': 0.0,
            'PF_num': 1.0, 'AvgPnL_num': 0.0, 'TotalPnL_num': 0.0,
        },
    ])

    barrier_outcomes = pd.DataFrame([
        {
            'time': pd.Timestamp('2026-01-01 00:00'),
            'signal': 1,
            'ratio_bin': '2-3',
            'atr_bucket': 'Q1',
            'pred_fav_3': 0.2,
            'pred_fav_6': 0.3,
            'pred_fav_12': 0.4,
            'pred_adv_3': 0.1,
            'pred_adv_6': 0.15,
            'pred_adv_12': 0.2,
            'horizon': 12,
            'SL': 5,
            'TP': 10,
            'outcome': 'TP_FIRST',
            'pnl': 10.0,
        },
        {
            'time': pd.Timestamp('2026-01-01 01:00'),
            'signal': -1,
            'ratio_bin': '5+',
            'atr_bucket': 'Q4',
            'pred_fav_3': 0.8,
            'pred_fav_6': 0.9,
            'pred_fav_12': 1.0,
            'pred_adv_3': 0.4,
            'pred_adv_6': 0.5,
            'pred_adv_12': 0.6,
            'horizon': 12,
            'SL': 5,
            'TP': 10,
            'outcome': 'SL_FIRST',
            'pnl': -5.0,
        },
        {
            'time': pd.Timestamp('2026-01-01 00:00'),
            'signal': 1,
            'ratio_bin': '2-3',
            'atr_bucket': 'Q1',
            'pred_fav_3': 0.2,
            'pred_fav_6': 0.3,
            'pred_fav_12': 0.4,
            'pred_adv_3': 0.1,
            'pred_adv_6': 0.15,
            'pred_adv_12': 0.2,
            'horizon': 12,
            'SL': 10,
            'TP': 20,
            'outcome': 'NEITHER',
            'pnl': 6.0,
        },
        {
            'time': pd.Timestamp('2026-01-01 01:00'),
            'signal': -1,
            'ratio_bin': '5+',
            'atr_bucket': 'Q4',
            'pred_fav_3': 0.8,
            'pred_fav_6': 0.9,
            'pred_fav_12': 1.0,
            'pred_adv_3': 0.4,
            'pred_adv_6': 0.5,
            'pred_adv_12': 0.6,
            'horizon': 12,
            'SL': 10,
            'TP': 20,
            'outcome': 'TP_FIRST',
            'pnl': 20.0,
        },
    ])

    sr.report_signal_passport(exc)
    sr.report_pullback_profile(exc)
    sr.report_first_hit_barriers(barriers)
    sr.report_amplitude_filters(exc, barrier_outcomes, barriers)
    sr.report_regime_splits(exc, barrier_outcomes, barriers)
    sr.print_practical_conclusions(exc, barriers)

    out = capsys.readouterr().out
    assert 'Signal Passport' in out
    assert 'Pullback Profile' in out
    assert 'First-Hit Barrier Matrix' in out
    assert 'Amplitude Filters' in out
    assert 'Regime Split' in out
    assert 'Practical Conclusions' in out


def test_variant3_prep_reports_smoke(capsys):
    exc = pd.DataFrame([
        {
            'time': pd.Timestamp('2026-01-01 00:00'),
            'signal': 1,
            'ratio_bin': '2-3',
            'atr_bucket': 'Q1',
            'adv_1': 1.0,
            'adv_3': 2.0,
            'fav_1': 4.0,
            'fav_3': 6.0,
            'fav_6': 8.0,
            'adv_6': 3.0,
            'close_net_1': 1.0,
            'close_net_3': 3.0,
            'close_net_6': 4.0,
            'pred_fav_3': 0.2,
            'pred_fav_6': 0.3,
            'pred_fav_12': 0.4,
            'pred_adv_3': 0.1,
            'pred_adv_6': 0.15,
            'mfe_3': 5.0, 'mae_3': 2.0, 'net_3': 2.0,
            'mfe_6': 7.0, 'mae_6': 3.0, 'net_6': 3.0,
            'mfe_12': 10.0, 'mae_12': 4.0, 'net_12': 6.0,
            'mfe_24': 12.0, 'mae_24': 5.0, 'net_24': 7.0,
            'mfe_48': 14.0, 'mae_48': 6.0, 'net_48': 8.0,
        },
        {
            'time': pd.Timestamp('2026-01-01 01:00'),
            'signal': -1,
            'ratio_bin': '5+',
            'atr_bucket': 'Q4',
            'adv_1': 2.0,
            'adv_3': 3.0,
            'fav_1': 3.0,
            'fav_3': 5.0,
            'fav_6': 7.0,
            'adv_6': 4.0,
            'close_net_1': -1.0,
            'close_net_3': 2.0,
            'close_net_6': 3.0,
            'pred_fav_3': 0.8,
            'pred_fav_6': 0.9,
            'pred_fav_12': 1.0,
            'pred_adv_3': 0.4,
            'pred_adv_6': 0.5,
            'mfe_3': 4.0, 'mae_3': 3.0, 'net_3': -1.0,
            'mfe_6': 6.0, 'mae_6': 4.0, 'net_6': 1.0,
            'mfe_12': 9.0, 'mae_12': 5.0, 'net_12': 4.0,
            'mfe_24': 11.0, 'mae_24': 6.0, 'net_24': 5.0,
            'mfe_48': 13.0, 'mae_48': 7.0, 'net_48': 6.0,
        },
    ])

    barriers = pd.DataFrame([
        {
            'horizon': 12, 'SL': 5, 'TP': 10, 'N': 2,
            'tp_first_pct': 50.0, 'sl_first_pct': 25.0, 'neither_pct': 25.0,
            'PF_num': 2.0, 'AvgPnL_num': 3.5, 'TotalPnL_num': 7.0,
        },
        {
            'horizon': 12, 'SL': 10, 'TP': 20, 'N': 2,
            'tp_first_pct': 25.0, 'sl_first_pct': 50.0, 'neither_pct': 25.0,
            'PF_num': 1.5, 'AvgPnL_num': 2.0, 'TotalPnL_num': 4.0,
        },
        {
            'horizon': 6, 'SL': 5, 'TP': 5, 'N': 2,
            'tp_first_pct': 50.0, 'sl_first_pct': 50.0, 'neither_pct': 0.0,
            'PF_num': 1.0, 'AvgPnL_num': 0.0, 'TotalPnL_num': 0.0,
        },
    ])

    barrier_outcomes = pd.DataFrame([
        {
            'time': pd.Timestamp('2026-01-01 00:00'),
            'signal': 1,
            'ratio_bin': '2-3',
            'atr_bucket': 'Q1',
            'pred_fav_3': 0.2,
            'pred_fav_6': 0.3,
            'pred_fav_12': 0.4,
            'pred_adv_3': 0.1,
            'pred_adv_6': 0.15,
            'pred_adv_12': 0.2,
            'horizon': 12,
            'SL': 5,
            'TP': 10,
            'outcome': 'TP_FIRST',
            'pnl': 10.0,
        },
        {
            'time': pd.Timestamp('2026-01-01 01:00'),
            'signal': -1,
            'ratio_bin': '5+',
            'atr_bucket': 'Q4',
            'pred_fav_3': 0.8,
            'pred_fav_6': 0.9,
            'pred_fav_12': 1.0,
            'pred_adv_3': 0.4,
            'pred_adv_6': 0.5,
            'pred_adv_12': 0.6,
            'horizon': 12,
            'SL': 5,
            'TP': 10,
            'outcome': 'SL_FIRST',
            'pnl': -5.0,
        },
        {
            'time': pd.Timestamp('2026-01-01 00:00'),
            'signal': 1,
            'ratio_bin': '2-3',
            'atr_bucket': 'Q1',
            'pred_fav_3': 0.2,
            'pred_fav_6': 0.3,
            'pred_fav_12': 0.4,
            'pred_adv_3': 0.1,
            'pred_adv_6': 0.15,
            'pred_adv_12': 0.2,
            'horizon': 12,
            'SL': 10,
            'TP': 20,
            'outcome': 'NEITHER',
            'pnl': 6.0,
        },
        {
            'time': pd.Timestamp('2026-01-01 01:00'),
            'signal': -1,
            'ratio_bin': '5+',
            'atr_bucket': 'Q4',
            'pred_fav_3': 0.8,
            'pred_fav_6': 0.9,
            'pred_fav_12': 1.0,
            'pred_adv_3': 0.4,
            'pred_adv_6': 0.5,
            'pred_adv_12': 0.6,
            'horizon': 12,
            'SL': 10,
            'TP': 20,
            'outcome': 'TP_FIRST',
            'pnl': 20.0,
        },
    ])

    sr.report_cohort_map(exc, barriers, barrier_outcomes)
    sr.report_entry_opportunities(exc)
    sr.report_stability_splits(exc, barriers, barrier_outcomes)
    sr.report_priority_cohorts(exc, barriers, barrier_outcomes)

    out = capsys.readouterr().out
    assert 'Cohort Map' in out
    assert 'Entry Opportunity Profile' in out
    assert 'Stability Split' in out
    assert 'Priority Cohorts' in out


def test_load_data_prefers_atr14_column_from_csv(monkeypatch, tmp_path):
    signals = tmp_path / 'signals.csv'
    ohlc = tmp_path / 'ohlc.csv'

    signals.write_text(
        "time;signal;up_3;dn_3;up_6;dn_6;up_12;dn_12;up_24;dn_24;up_48;dn_48\n"
        "2026-01-01 00:00:00;1;0.3;0.1;0.4;0.2;0.5;0.2;0.6;0.3;0.7;0.4\n",
        encoding='utf-8',
    )
    ohlc.write_text(
        "time;open;high;low;close;volume;atr14\n"
        "2026-01-01 00:00:00;100;101;99;100;10;7.5\n",
        encoding='utf-8',
    )

    monkeypatch.setattr(sr, 'SIGNALS_FILE', signals)
    monkeypatch.setattr(sr, 'OHLC_FILE', ohlc)

    df, merged_ohlc = sr.load_data()

    assert df.loc[0, 'atr14'] == pytest.approx(7.5, abs=1e-9)
    assert merged_ohlc.loc[0, 'atr14'] == pytest.approx(7.5, abs=1e-9)


def test_load_data_falls_back_to_python_atr_when_csv_has_no_atr14(monkeypatch, tmp_path):
    signals = tmp_path / 'signals.csv'
    ohlc = tmp_path / 'ohlc.csv'

    signals.write_text(
        "time;signal;up_3;dn_3;up_6;dn_6;up_12;dn_12;up_24;dn_24;up_48;dn_48\n"
        "2026-01-01 13:00:00;1;0.3;0.1;0.4;0.2;0.5;0.2;0.6;0.3;0.7;0.4\n",
        encoding='utf-8',
    )

    rows = ["time;open;high;low;close;volume"]
    for i in range(16):
        rows.append(f"2026-01-01 {i:02d}:00:00;100;102;100;101;10")
    ohlc.write_text("\n".join(rows) + "\n", encoding='utf-8')

    monkeypatch.setattr(sr, 'SIGNALS_FILE', signals)
    monkeypatch.setattr(sr, 'OHLC_FILE', ohlc)

    df, merged_ohlc = sr.load_data()

    assert 'atr14' in merged_ohlc.columns
    assert df.loc[0, 'atr14'] == pytest.approx(2.0, abs=1e-9)


def test_summarize_signal_groups_returns_baseline_outcome_shares_and_pf():
    frame = pd.DataFrame([
        {
            'cohort': 'A',
            'net_12': 4.0,
            'mfe_12': 8.0,
            'mae_12': 2.0,
            'baseline_outcome': 'TP_FIRST',
            'baseline_pnl': 10.0,
        },
        {
            'cohort': 'A',
            'net_12': -2.0,
            'mfe_12': 5.0,
            'mae_12': 4.0,
            'baseline_outcome': 'SL_FIRST',
            'baseline_pnl': -5.0,
        },
        {
            'cohort': 'A',
            'net_12': 1.0,
            'mfe_12': 4.0,
            'mae_12': 1.0,
            'baseline_outcome': pd.NA,
            'baseline_pnl': float('nan'),
        },
        {
            'cohort': 'B',
            'net_12': 3.0,
            'mfe_12': 6.0,
            'mae_12': 2.0,
            'baseline_outcome': 'NEITHER',
            'baseline_pnl': 3.0,
        },
    ])

    summary = sr.summarize_signal_groups(frame, ['cohort'])

    row_a = summary[summary['cohort'] == 'A'].iloc[0]
    assert row_a['N'] == 3
    assert row_a['PF_12'] == pytest.approx(2.5, abs=1e-9)
    assert row_a['AvgPnL_baseline'] == pytest.approx(2.5, abs=1e-9)
    assert row_a['TP_FIRST_pct'] == pytest.approx(50.0, abs=1e-9)
    assert row_a['SL_FIRST_pct'] == pytest.approx(50.0, abs=1e-9)
    assert row_a['NEITHER_pct'] == pytest.approx(0.0, abs=1e-9)


def test_build_entry_opportunity_profile_counts_pullback_and_favorable_levels():
    frame = pd.DataFrame([
        {
            'time': pd.Timestamp('2026-01-01 00:00'), 'cohort': 'A', 'signal': 1,
            'entry_atr14': 4.0,
            'adv_1': 4.0, 'adv_3': 8.0, 'adv_6': 12.0,
            'fav_1': 4.0, 'fav_3': 8.0, 'fav_6': 12.0,
            'close_net_1': 2.0, 'close_net_3': 5.0, 'close_net_6': 9.0,
        },
        {
            'time': pd.Timestamp('2026-01-01 01:00'), 'cohort': 'A', 'signal': 1,
            'entry_atr14': 4.0,
            'adv_1': 3.0, 'adv_3': 7.0, 'adv_6': 11.0,
            'fav_1': 3.0, 'fav_3': 7.0, 'fav_6': 11.0,
            'close_net_1': -1.0, 'close_net_3': 1.0, 'close_net_6': None,
        },
    ])

    table = sr.build_entry_opportunity_profile(frame, 'cohort', ['A'])
    row = table.iloc[0]

    assert row['pullback>=1ATR_1H'] == pytest.approx(50.0, abs=1e-9)
    assert row['pullback>=2ATR_3H'] == pytest.approx(50.0, abs=1e-9)
    assert row['pullback>=3ATR_6H'] == pytest.approx(50.0, abs=1e-9)
    assert row['fav>=1ATR_1H'] == pytest.approx(50.0, abs=1e-9)
    assert row['fav>=2ATR_3H'] == pytest.approx(50.0, abs=1e-9)
    assert row['fav>=3ATR_6H'] == pytest.approx(50.0, abs=1e-9)
    assert row['close>0_1H'] == pytest.approx(50.0, abs=1e-9)
    assert row['close>0_3H'] == pytest.approx(100.0, abs=1e-9)
    assert row['close>0_6H'] == pytest.approx(100.0, abs=1e-9)


def test_select_base_barrier_setups_prefers_adaptive_viable_sample_over_tiny_inf_pf():
    barrier_summary = pd.DataFrame([
        {
            'horizon': 12, 'SL': 5, 'TP': 30, 'N': 1,
            'tp_first_pct': 100.0, 'sl_first_pct': 0.0, 'neither_pct': 0.0,
            'PF_num': float('inf'), 'AvgPnL_num': 30.0, 'TotalPnL_num': 30.0,
        },
        {
            'horizon': 12, 'SL': 10, 'TP': 20, 'N': 20,
            'tp_first_pct': 55.0, 'sl_first_pct': 30.0, 'neither_pct': 15.0,
            'PF_num': 1.8, 'AvgPnL_num': 4.0, 'TotalPnL_num': 80.0,
        },
        {
            'horizon': 12, 'SL': 5, 'TP': 10, 'N': 18,
            'tp_first_pct': 52.0, 'sl_first_pct': 33.0, 'neither_pct': 15.0,
            'PF_num': 1.6, 'AvgPnL_num': 3.0, 'TotalPnL_num': 54.0,
        },
    ])

    top = sr._select_base_barrier_setups(barrier_summary, top_n=2)

    assert list(top['SL']) == [10, 5]
    assert list(top['TP']) == [20, 10]


def test_report_regime_splits_excludes_missing_best_outcomes_from_tp_sl_denominator(capsys):
    exc = pd.DataFrame([
        {
            'time': pd.Timestamp('2026-01-01 00:00'), 'signal': 1, 'ratio_bin': '2-3', 'atr_bucket': 'Q1',
            'mfe_12': 10.0, 'mae_12': 3.0, 'net_12': 4.0,
        },
        {
            'time': pd.Timestamp('2026-01-01 01:00'), 'signal': 1, 'ratio_bin': '2-3', 'atr_bucket': 'Q1',
            'mfe_12': 8.0, 'mae_12': 4.0, 'net_12': 2.0,
        },
        {
            'time': pd.Timestamp('2026-01-01 02:00'), 'signal': -1, 'ratio_bin': '5+', 'atr_bucket': 'Q4',
            'mfe_12': 7.0, 'mae_12': 5.0, 'net_12': -1.0,
        },
    ])
    barrier_summary = pd.DataFrame([
        {
            'horizon': 12, 'SL': 5, 'TP': 10, 'N': 3,
            'tp_first_pct': 50.0, 'sl_first_pct': 50.0, 'neither_pct': 0.0,
            'PF_num': 1.2, 'AvgPnL_num': 1.0, 'TotalPnL_num': 3.0,
        },
    ])
    barrier_outcomes = pd.DataFrame([
        {'time': pd.Timestamp('2026-01-01 00:00'), 'horizon': 12, 'SL': 5, 'TP': 10, 'outcome': 'TP_FIRST'},
        {'time': pd.Timestamp('2026-01-01 02:00'), 'horizon': 12, 'SL': 5, 'TP': 10, 'outcome': 'SL_FIRST'},
    ])

    sr.report_regime_splits(exc, barrier_outcomes, barrier_summary)

    out = capsys.readouterr().out
    assert 'BUY' in out
    assert '100.0%' in out
    assert '0.0%' in out


def test_report_pullback_profile_uses_effective_non_null_window_sample_size(capsys):
    exc = pd.DataFrame([
        {
            'time': pd.Timestamp('2026-01-01 00:00'), 'signal': 1, 'ratio_bin': '2-3',
            'fav_1': 4.0, 'adv_1': 1.0, 'close_net_1': 1.0,
            'fav_3': 6.0, 'adv_3': 2.0, 'close_net_3': 2.0,
            'fav_6': 8.0, 'adv_6': 3.0, 'close_net_6': 3.0,
        },
        {
            'time': pd.Timestamp('2026-01-01 01:00'), 'signal': -1, 'ratio_bin': '5+',
            'fav_1': 3.0, 'adv_1': 2.0, 'close_net_1': -1.0,
            'fav_3': 5.0, 'adv_3': 3.0, 'close_net_3': 1.0,
            'fav_6': None, 'adv_6': None, 'close_net_6': None,
        },
    ])

    sr.report_pullback_profile(exc)

    out = capsys.readouterr().out
    assert '1H' in out
    assert '6H' in out
    assert ' 2 ' in out
    assert ' 1 ' in out


def test_report_amplitude_filters_uses_effective_base_horizon_sample_size(capsys):
    exc = pd.DataFrame([
        {
            'time': pd.Timestamp('2026-01-01 00:00'),
            'signal': 1,
            'ratio_bin': '2-3',
            'atr_bucket': 'Q1',
            'pred_fav_3': 0.1,
            'pred_fav_6': 0.2,
            'pred_fav_12': 0.3,
            'pred_adv_3': 0.1,
            'pred_adv_6': 0.2,
            'net_12': 4.0,
            'mfe_12': 6.0,
            'mae_12': 2.0,
        },
        {
            'time': pd.Timestamp('2026-01-01 01:00'),
            'signal': -1,
            'ratio_bin': '2-3',
            'atr_bucket': 'Q1',
            'pred_fav_3': 0.1,
            'pred_fav_6': 0.2,
            'pred_fav_12': 0.3,
            'pred_adv_3': 0.1,
            'pred_adv_6': 0.2,
            'net_12': None,
            'mfe_12': None,
            'mae_12': None,
        },
    ])
    barrier_summary = pd.DataFrame([
        {
            'horizon': 12, 'SL': 5, 'TP': 10, 'N': 1,
            'tp_first_pct': 100.0, 'sl_first_pct': 0.0, 'neither_pct': 0.0,
            'PF_num': 2.0, 'AvgPnL_num': 4.0, 'TotalPnL_num': 4.0,
        },
    ])
    barrier_outcomes = pd.DataFrame([
        {
            'time': pd.Timestamp('2026-01-01 00:00'),
            'signal': 1,
            'ratio_bin': '2-3',
            'atr_bucket': 'Q1',
            'pred_fav_3': 0.1,
            'pred_fav_6': 0.2,
            'pred_fav_12': 0.3,
            'pred_adv_3': 0.1,
            'pred_adv_6': 0.2,
            'pred_adv_12': 0.3,
            'horizon': 12,
            'SL': 5,
            'TP': 10,
            'outcome': 'TP_FIRST',
            'pnl': 10.0,
        },
    ])

    sr.report_amplitude_filters(exc, barrier_outcomes, barrier_summary)

    out = capsys.readouterr().out
    section = out.split('[pred_fav_3]')[1]
    assert 'mid' in section
    assert ' 1 ' in section
    assert ' 2 ' not in section


def test_report_by_ratio_does_not_mutate_existing_variant2_ratio_bin(capsys):
    exc = pd.DataFrame([
        {
            'time': pd.Timestamp('2026-01-01 00:00'),
            'signal': 1,
            'ratio_12': 150.0,
            'ratio_bin': '5+',
            'mfe_12': 10.0,
            'mae_12': 2.0,
            'net_12': 6.0,
        },
    ])

    sr.report_by_ratio(exc)
    capsys.readouterr()

    assert exc.loc[0, 'ratio_bin'] == '5+'


def test_parse_fractal_price_reads_price_field_from_fractal0():
    fractal = '1664470800:4585.25:-1:0.1:0.2:0:0:0:0:0:0:1:2:3:4:5:6:7:8:9:10:11'
    assert sr.parse_fractal_price(fractal) == pytest.approx(4585.25, abs=1e-9)


def test_latest_fractal_price_uses_latest_embedded_time_not_column_order():
    fractals = [
        '1664470800:4585.25:-1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0',
        '1664478000:4601.50:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0',
        '1664474400:4590.75:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0',
    ]

    assert sr.latest_fractal_price(fractals) == pytest.approx(4601.50, abs=1e-9)


def test_load_pic_price_data_extracts_latest_sorted_price_and_mirrors_signal_dedupe(monkeypatch, tmp_path):
    raw = tmp_path / 'nero_variant3.csv'
    raw.write_text(
        "\n".join([
            "time;fractal0;fractal1;fractal2",
            "2026.01.01 00:00;1664470800:4585.25:-1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0;1664478000:4601.50:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0;1664474400:4590.75:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0",
            "2026.01.01 01:00;1664481600:4610.00:-1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0;1664479800:4604.25:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0;",
            "2026.01.01 01:00;1664485200:4622.75:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0;1664483400:4618.50:-1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0;",
        ]),
        encoding='utf-8',
    )

    monkeypatch.setattr(sr, 'RAW_FEATURES_FILE', raw)

    prices = sr.load_pic_price_data()

    assert list(prices['time']) == list(pd.to_datetime([
        '2026-01-01 00:00',
        '2026-01-01 01:00',
    ]))
    assert list(prices['pic_price']) == pytest.approx([4601.50, 4622.75], abs=1e-9)
    assert list(prices['pic_direction']) == [1, 1]
    assert list(prices['pic_fractal_time']) == list(pd.to_datetime([1664478000, 1664485200], unit='s'))


def test_summarize_pic_price_validation_matches_high_low_by_direction():
    frame = pd.DataFrame({
        'time': pd.to_datetime(['2026-01-01 00:00', '2026-01-01 01:00']),
        'pic_fractal_time': pd.to_datetime(['2025-12-31 23:00', '2026-01-01 00:00']),
        'pic_price': [105.0, 97.0],
        'pic_direction': [1, -1],
    })
    ohlc = pd.DataFrame({
        'time': pd.to_datetime(['2025-12-31 23:00', '2026-01-01 00:00']),
        'high': [105.0, 103.0],
        'low': [100.0, 97.0],
    })

    summary = sr.summarize_pic_price_validation(frame, ohlc)

    assert summary['N_rows'] == 2
    assert summary['N_joined'] == 2
    assert summary['N_matched'] == 2
    assert summary['match_pct'] == pytest.approx(100.0, abs=1e-9)
    assert summary['peak_match_pct'] == pytest.approx(100.0, abs=1e-9)
    assert summary['trough_match_pct'] == pytest.approx(100.0, abs=1e-9)
    assert summary['max_abs_error'] == pytest.approx(0.0, abs=1e-9)


def test_resolve_limit_fill_uses_open_for_better_buy_fill():
    fill_idx, fill_price = sr.resolve_limit_fill(
        opens=[89.0],
        highs=[110.0],
        lows=[88.0],
        signal=1,
        limit_price=90.0,
    )
    assert fill_idx == 0
    assert fill_price == pytest.approx(89.0, abs=1e-9)


def test_build_variant3_scenario_outcomes_compares_market_pullback_delayed_and_cancel():
    ohlc = pd.DataFrame({
        'time': pd.to_datetime([
            '2026-01-01 00:00',
            '2026-01-01 01:00',
            '2026-01-01 02:00',
            '2026-01-01 03:00',
            '2026-01-01 04:00',
        ]),
        'open': [100.0, 99.0, 90.0, 150.0, 150.0],
        'high': [100.0, 104.0, 160.0, 151.0, 151.0],
        'low': [100.0, 88.0, 89.0, 149.0, 149.0],
        'close': [100.0, 90.0, 150.0, 150.0, 150.0],
        'atr14': [10.0, 10.0, 10.0, 10.0, 10.0],
    })
    exc = pd.DataFrame([
        {
            'time': ohlc.loc[0, 'time'],
            'signal': 1,
            'ohlc_idx': 0,
            'entry_close': 100.0,
            'entry_atr14': 10.0,
            'pic_price': 80.0,
            'ratio_bin': '4-5',
            'atr_bucket': 'Q4',
            'net_3': 50.0,
        },
    ])
    scenario_specs = [
        {'scenario': 'market'},
        {'scenario': 'delayed', 'delay_bars': 1},
        {'scenario': 'pullback', 'anchor': 'entry_close', 'offset_atr': 1.0},
        {'scenario': 'pullback', 'anchor': 'pic_price', 'offset_atr': 1.0},
        {'scenario': 'cancel-window', 'anchor': 'entry_close', 'offset_atr': 2.0, 'expiry_bars': 1},
    ]

    outcomes = sr.build_variant3_scenario_outcomes(
        exc,
        ohlc,
        horizon=3,
        sl=5,
        tp=50,
        scenario_specs=scenario_specs,
    )

    market = outcomes[outcomes['scenario'] == 'market'].iloc[0]
    delayed = outcomes[(outcomes['scenario'] == 'delayed') & (outcomes['delay_bars'] == 1)].iloc[0]
    pullback_close = outcomes[
        (outcomes['scenario'] == 'pullback')
        & (outcomes['anchor'] == 'entry_close')
        & (outcomes['offset_atr'] == 1.0)
    ].iloc[0]
    pullback_pic = outcomes[
        (outcomes['scenario'] == 'pullback')
        & (outcomes['anchor'] == 'pic_price')
        & (outcomes['offset_atr'] == 1.0)
    ].iloc[0]
    cancel_skip = outcomes[
        (outcomes['scenario'] == 'cancel-window')
        & (outcomes['anchor'] == 'entry_close')
        & (outcomes['offset_atr'] == 2.0)
        & (outcomes['expiry_bars'] == 1)
    ].iloc[0]

    assert market['outcome'] == 'SL_FIRST'
    assert market['fill_price'] == pytest.approx(100.0, abs=1e-9)

    assert delayed['outcome'] == 'TP_FIRST'
    assert delayed['fill_price'] == pytest.approx(90.0, abs=1e-9)

    assert pullback_close['outcome'] == 'TP_FIRST'
    assert pullback_close['fill_price'] == pytest.approx(90.0, abs=1e-9)

    assert pullback_pic['outcome'] == 'TP_FIRST'
    assert pullback_pic['fill_price'] == pytest.approx(90.0, abs=1e-9)

    assert cancel_skip['fill_status'] == 'SKIP'
    assert pd.isna(cancel_skip['pnl'])


def test_build_variant3_scenario_outcomes_uses_common_signal_deadline():
    ohlc = pd.DataFrame({
        'time': pd.to_datetime([
            '2026-01-01 00:00',
            '2026-01-01 01:00',
            '2026-01-01 02:00',
            '2026-01-01 03:00',
        ]),
        'open': [100.0, 100.0, 100.0, 100.0],
        'high': [100.0, 101.0, 101.0, 160.0],
        'low': [100.0, 99.0, 99.0, 99.0],
        'close': [100.0, 100.0, 100.0, 150.0],
        'atr14': [10.0, 10.0, 10.0, 10.0],
    })
    exc = pd.DataFrame([
        {
            'time': ohlc.loc[0, 'time'],
            'signal': 1,
            'ohlc_idx': 0,
            'entry_close': 100.0,
            'entry_atr14': 10.0,
            'pic_price': 90.0,
            'ratio_bin': '4-5',
            'atr_bucket': 'Q4',
            'net_2': 0.0,
        },
    ])

    outcomes = sr.build_variant3_scenario_outcomes(
        exc,
        ohlc,
        horizon=2,
        sl=5,
        tp=50,
        scenario_specs=[{'scenario': 'delayed', 'delay_bars': 1}],
    )

    delayed = outcomes.iloc[0]
    assert delayed['outcome'] == 'NEITHER'
    assert delayed['pnl'] == pytest.approx(0.0, abs=1e-9)


def test_summarize_variant3_scenarios_reports_fill_and_skip_rates():
    outcomes = pd.DataFrame([
        {
            'cohort': 'A',
            'scenario': 'pullback',
            'params': 'entry_close-1ATR',
            'fill_status': 'FILLED',
            'outcome': 'TP_FIRST',
            'pnl': 50.0,
        },
        {
            'cohort': 'A',
            'scenario': 'pullback',
            'params': 'entry_close-1ATR',
            'fill_status': 'SKIP',
            'outcome': 'SKIP',
            'pnl': np.nan,
        },
    ])

    summary = sr.summarize_variant3_scenarios(outcomes, ['cohort', 'scenario', 'params'])
    row = summary.iloc[0]

    assert row['N_signals'] == 2
    assert row['N_filled'] == 1
    assert row['fill_pct'] == pytest.approx(50.0, abs=1e-9)
    assert row['skip_pct'] == pytest.approx(50.0, abs=1e-9)
    assert row['PF'] == float('inf')


def test_annotate_variant3_robustness_computes_support_tiers_and_market_deltas():
    summary = pd.DataFrame([
        {
            'cohort': 'ratio 4-5',
            'scenario': 'market',
            'params': 'market',
            'N_signals': 100,
            'N_filled': 100,
            'fill_pct': 100.0,
            'skip_pct': 0.0,
            'PF': 1.2,
            'AvgPnL': 0.5,
            'TP_FIRST_pct': 40.0,
            'SL_FIRST_pct': 30.0,
            'NEITHER_pct': 30.0,
        },
        {
            'cohort': 'ratio 4-5',
            'scenario': 'pullback',
            'params': 'entry_close-3ATR',
            'N_signals': 100,
            'N_filled': 30,
            'fill_pct': 30.0,
            'skip_pct': 70.0,
            'PF': 3.5,
            'AvgPnL': 4.0,
            'TP_FIRST_pct': 60.0,
            'SL_FIRST_pct': 20.0,
            'NEITHER_pct': 20.0,
        },
        {
            'cohort': 'ratio 4-5',
            'scenario': 'pullback',
            'params': 'pic_price-1ATR',
            'N_signals': 100,
            'N_filled': 20,
            'fill_pct': 10.0,
            'skip_pct': 80.0,
            'PF': 6.0,
            'AvgPnL': 7.0,
            'TP_FIRST_pct': 70.0,
            'SL_FIRST_pct': 10.0,
            'NEITHER_pct': 20.0,
        },
    ])

    annotated = sr.annotate_variant3_robustness(summary)

    supported = annotated[annotated['params'] == 'entry_close-3ATR'].iloc[0]
    fragile = annotated[annotated['params'] == 'pic_price-1ATR'].iloc[0]

    assert supported['PF_delta'] == pytest.approx(2.3, abs=1e-9)
    assert supported['AvgPnL_delta'] == pytest.approx(3.5, abs=1e-9)
    assert supported['support_tier'] == 'Supported'
    assert supported['support_floors'] == '10/5, 20/10, 30/10'
    assert bool(supported['verdict_eligible']) is True

    assert fragile['support_tier'] == 'Standard'
    assert fragile['support_floors'] == '10/5, 20/10'
    assert bool(fragile['verdict_eligible']) is False


def test_build_variant3_support_ladder_tracks_floor_specific_winners():
    summary = pd.DataFrame([
        {
            'cohort': 'ratio 4-5',
            'scenario': 'market',
            'params': 'market',
            'N_signals': 100,
            'N_filled': 100,
            'fill_pct': 100.0,
            'skip_pct': 0.0,
            'PF': 1.2,
            'AvgPnL': 0.5,
            'TP_FIRST_pct': 40.0,
            'SL_FIRST_pct': 30.0,
            'NEITHER_pct': 30.0,
        },
        {
            'cohort': 'ratio 4-5',
            'scenario': 'pullback',
            'params': 'fragile-edge',
            'N_signals': 100,
            'N_filled': 20,
            'fill_pct': 10.0,
            'skip_pct': 80.0,
            'PF': 6.0,
            'AvgPnL': 6.0,
            'TP_FIRST_pct': 70.0,
            'SL_FIRST_pct': 10.0,
            'NEITHER_pct': 20.0,
        },
        {
            'cohort': 'ratio 4-5',
            'scenario': 'pullback',
            'params': 'supported-edge',
            'N_signals': 100,
            'N_filled': 30,
            'fill_pct': 10.0,
            'skip_pct': 70.0,
            'PF': 3.5,
            'AvgPnL': 4.0,
            'TP_FIRST_pct': 60.0,
            'SL_FIRST_pct': 20.0,
            'NEITHER_pct': 20.0,
        },
        {
            'cohort': 'ratio 4-5',
            'scenario': 'cancel-window',
            'params': 'strong-edge',
            'N_signals': 100,
            'N_filled': 40,
            'fill_pct': 15.0,
            'skip_pct': 60.0,
            'PF': 1.8,
            'AvgPnL': 1.5,
            'TP_FIRST_pct': 55.0,
            'SL_FIRST_pct': 20.0,
            'NEITHER_pct': 25.0,
        },
    ])

    ladder = sr.build_variant3_support_ladder(summary, cohorts=['ratio 4-5'])

    assert list(ladder['support_floor']) == ['10/5', '20/10', '30/10', '40/15']
    assert ladder.loc[ladder['support_floor'] == '10/5', 'params'].iloc[0] == 'fragile-edge'
    assert ladder.loc[ladder['support_floor'] == '20/10', 'params'].iloc[0] == 'fragile-edge'
    assert ladder.loc[ladder['support_floor'] == '30/10', 'params'].iloc[0] == 'supported-edge'
    assert ladder.loc[ladder['support_floor'] == '40/15', 'params'].iloc[0] == 'strong-edge'


def test_build_variant3_shortlist_verdict_requires_supported_tier():
    summary = pd.DataFrame([
        {
            'cohort': 'ratio 4-5',
            'scenario': 'market',
            'params': 'market',
            'N_signals': 100,
            'N_filled': 100,
            'fill_pct': 100.0,
            'skip_pct': 0.0,
            'PF': 1.2,
            'AvgPnL': 0.5,
            'TP_FIRST_pct': 40.0,
            'SL_FIRST_pct': 30.0,
            'NEITHER_pct': 30.0,
        },
        {
            'cohort': 'ratio 4-5',
            'scenario': 'pullback',
            'params': 'fragile-edge',
            'N_signals': 100,
            'N_filled': 20,
            'fill_pct': 10.0,
            'skip_pct': 80.0,
            'PF': 6.0,
            'AvgPnL': 6.0,
            'TP_FIRST_pct': 70.0,
            'SL_FIRST_pct': 10.0,
            'NEITHER_pct': 20.0,
        },
        {
            'cohort': 'ratio 4-5',
            'scenario': 'pullback',
            'params': 'supported-edge',
            'N_signals': 100,
            'N_filled': 30,
            'fill_pct': 10.0,
            'skip_pct': 70.0,
            'PF': 3.5,
            'AvgPnL': 4.0,
            'TP_FIRST_pct': 60.0,
            'SL_FIRST_pct': 20.0,
            'NEITHER_pct': 20.0,
        },
        {
            'cohort': 'ratio 4-5',
            'scenario': 'cancel-window',
            'params': 'strong-but-weaker',
            'N_signals': 100,
            'N_filled': 40,
            'fill_pct': 15.0,
            'skip_pct': 60.0,
            'PF': 1.8,
            'AvgPnL': 1.5,
            'TP_FIRST_pct': 55.0,
            'SL_FIRST_pct': 20.0,
            'NEITHER_pct': 25.0,
        },
    ])

    verdict = sr.build_variant3_shortlist_verdict(summary)

    assert len(verdict) == 1
    row = verdict.iloc[0]
    assert row['cohort'] == 'ratio 4-5'
    assert row['params'] == 'supported-edge'
    assert row['support_tier'] == 'Supported'


def test_variant3_reports_smoke(capsys):
    summary = pd.DataFrame([
        {
            'cohort': 'ratio 4-5 x ATR Q4',
            'scenario': 'pullback',
            'params': 'entry_close-1ATR',
            'N_signals': 10,
            'N_filled': 6,
            'fill_pct': 60.0,
            'skip_pct': 40.0,
            'PF': 2.0,
            'AvgPnL': 5.0,
            'TP_FIRST_pct': 50.0,
            'SL_FIRST_pct': 16.7,
            'NEITHER_pct': 33.3,
        },
        {
            'cohort': 'ratio 3-4',
            'scenario': 'pullback',
            'params': 'entry_close-1ATR',
            'N_signals': 10,
            'N_filled': 5,
            'fill_pct': 50.0,
            'skip_pct': 50.0,
            'PF': 0.8,
            'AvgPnL': -1.0,
            'TP_FIRST_pct': 20.0,
            'SL_FIRST_pct': 40.0,
            'NEITHER_pct': 40.0,
        },
    ])

    sr.report_variant3_scenario_matrix(summary)
    sr.report_variant3_shortlist_verdict(summary)
    sr.report_variant3_negative_controls(summary)

    out = capsys.readouterr().out
    assert 'Variant 3 Scenario Matrix' in out
    assert 'Variant 3 Shortlist Verdict' in out
    assert 'Variant 3 Negative Controls' in out
