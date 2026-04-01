# Signal Research Variant 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand `API/signal_research.py` into a trading-oriented OHLC research tool that answers entry, pullback, SL/TP, and regime questions without modifying the EA.

**Architecture:** Keep one script, but split the logic into two layers inside `API/signal_research.py`: a deterministic data-enrichment layer that converts merged signal+OHLC rows into a richer research dataframe, and a reporting layer that prints human-readable tables from those prepared frames. Compute ATR internally from OHLC because the current `ml_signals.csv` format does not contain ATR. Reuse one long-form barrier outcomes dataframe across multiple reports so first-hit logic is implemented once and summarized many ways.

**Tech Stack:** Python 3.11+, pandas, NumPy, pytest

---

## Constraints

- Do not change EA files.
- Do not retrain the model.
- Do not implement variant 3 strategy simulation in this plan.
- Do not add git commit steps: this repository is operated with manual git control by the user.

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `API/signal_research.py` | Modify | Compute enriched signal metrics, path-dependent barrier outcomes, and print new research tables |
| `tests/test_signal_research.py` | Create | Unit tests for directional metrics, ATR computation, barrier ordering, and report smoke tests |

## Current File Map

- `API/signal_research.py:46-69` loads `ml_signals.csv` and `XAUUSD_H1_OHLC.csv`
- `API/signal_research.py:72-150` computes `MFE/MAE/Net`
- `API/signal_research.py:159-397` prints current report sections
- `API/signal_research.py:400-425` wires the CLI

The plan keeps this script as the single code file, but refactors it into smaller pure helpers so it does not turn into an unreadable monolith.

---

### Task 1: Add Failing Tests for Research Math

**Files:**
- Create: `tests/test_signal_research.py`
- Read: `API/signal_research.py:72-150`

- [ ] **Step 1: Write focused tests for ATR, pullback windows, and same-bar barrier ordering**

```python
import sys
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
        'open':  [100.0, 100.0, 103.0,  99.0, 105.0, 106.0],
        'high':  [101.0, 104.0, 105.0, 106.0, 107.0, 108.0],
        'low':   [ 99.0, 100.0,  98.0,  97.0, 102.0, 104.0],
        'close': [100.0, 103.0,  99.0, 105.0, 106.0, 107.0],
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
        'open':  [100.0] * 16,
        'high':  [102.0] * 16,
        'low':   [100.0] * 16,
        'close': [101.0] * 16,
    })
    atr = sr.compute_atr14(ohlc)
    assert atr.iloc[12] != atr.iloc[12]  # still NaN before 14 full bars
    assert atr.iloc[13] == pytest.approx(2.0, abs=1e-9)
    assert atr.iloc[15] == pytest.approx(2.0, abs=1e-9)


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
```

- [ ] **Step 2: Run the tests and verify they fail on the missing helpers/columns**

Run: `cd /home/hohla/git/SoSimple && python -m pytest tests/test_signal_research.py -v`

Expected:
- FAIL because `compute_atr14` does not exist yet
- FAIL because `compute_excursions()` does not yet produce `pred_fav_*`, `pred_adv_*`, `fav_*`, `adv_*`, `close_net_*`
- FAIL because `first_hit_barrier_result()` does not exist yet

---

### Task 2: Enrich the Core Research Frame

**Files:**
- Modify: `API/signal_research.py:37-150`
- Test: `tests/test_signal_research.py`

- [ ] **Step 1: Add research constants and ATR helpers near the module top**

```python
BASE_HORIZON = 12
PULLBACK_WINDOWS = [1, 3, 6]
BARRIER_HORIZONS = [6, 12, 24]
SL_LEVELS = [5, 10, 15, 20, 30]
TP_LEVELS = [5, 10, 15, 20, 30, 50]
ATR_PERIOD = 14


def compute_true_range(ohlc: pd.DataFrame) -> pd.Series:
    prev_close = ohlc['close'].shift(1)
    return pd.concat([
        ohlc['high'] - ohlc['low'],
        (ohlc['high'] - prev_close).abs(),
        (ohlc['low'] - prev_close).abs(),
    ], axis=1).max(axis=1)


def compute_atr14(ohlc: pd.DataFrame) -> pd.Series:
    tr = compute_true_range(ohlc)
    return tr.rolling(ATR_PERIOD, min_periods=ATR_PERIOD).mean()
```

- [ ] **Step 2: Extend `load_data()` to compute and merge ATR14 from OHLC**

```python
def load_data(test_only: bool = False):
    sig = pd.read_csv(SIGNALS_FILE, sep=';', parse_dates=['time'])
    ohlc = pd.read_csv(OHLC_FILE, sep=';', parse_dates=['time'])

    ohlc.sort_values('time', inplace=True)
    ohlc.reset_index(drop=True, inplace=True)
    ohlc['atr14'] = compute_atr14(ohlc)

    df = sig.merge(
        ohlc[['time', 'open', 'high', 'low', 'close', 'atr14']],
        on='time',
        how='inner',
    )
```

- [ ] **Step 3: Extend `compute_excursions()` into a richer research dataframe**

Add directional aliases and pullback windows without changing the existing MFE/MAE/Net meaning:

```python
        rec = {
            'time': t,
            'signal': sig,
            'ohlc_idx': ohlc_idx,
            'entry_close': entry_close,
            'entry_atr14': row.get('atr14', np.nan),
        }

        rec['pred_fav_3'] = row['up_3'] if sig == 1 else row['dn_3']
        rec['pred_adv_3'] = row['dn_3'] if sig == 1 else row['up_3']
        rec['pred_fav_6'] = row['up_6'] if sig == 1 else row['dn_6']
        rec['pred_adv_6'] = row['dn_6'] if sig == 1 else row['up_6']
        rec['pred_fav_12'] = row['up_12'] if sig == 1 else row['dn_12']
        rec['pred_adv_12'] = row['dn_12'] if sig == 1 else row['up_12']
```

Inside the loop, after the existing horizon metrics, add early-window pullback metrics:

```python
        for w in PULLBACK_WINDOWS:
            window_end = ohlc_idx + w
            if window_end >= n_ohlc:
                rec[f'fav_{w}'] = np.nan
                rec[f'adv_{w}'] = np.nan
                rec[f'close_net_{w}'] = np.nan
                continue

            w_highs = highs[ohlc_idx + 1: window_end + 1]
            w_lows = lows[ohlc_idx + 1: window_end + 1]
            w_close = closes[window_end]

            if sig == 1:
                rec[f'fav_{w}'] = w_highs.max() - entry_close
                rec[f'adv_{w}'] = entry_close - w_lows.min()
                rec[f'close_net_{w}'] = w_close - entry_close
            else:
                rec[f'fav_{w}'] = entry_close - w_lows.min()
                rec[f'adv_{w}'] = w_highs.max() - entry_close
                rec[f'close_net_{w}'] = entry_close - w_close
```

After the dataframe is built, add ratio and ATR buckets in one place:

```python
    exc = pd.DataFrame(results)
    bins = [2, 3, 4, 5, np.inf]
    labels = ['2-3', '3-4', '4-5', '5+']
    exc['ratio_bin'] = pd.cut(exc['ratio_12'], bins=bins, labels=labels, right=False)

    valid_atr = exc['entry_atr14'].dropna()
    if valid_atr.nunique() >= 4:
        exc.loc[valid_atr.index, 'atr_bucket'] = pd.qcut(
            valid_atr,
            q=4,
            labels=['Q1', 'Q2', 'Q3', 'Q4'],
            duplicates='drop',
        )
    else:
        exc['atr_bucket'] = 'ALL'

    return exc
```

- [ ] **Step 4: Run the tests again and verify Task 1 now passes**

Run: `cd /home/hohla/git/SoSimple && python -m pytest tests/test_signal_research.py -v`

Expected:
- `test_compute_atr14_uses_true_range` PASS
- `test_compute_excursions_adds_directional_aliases_and_pullback_windows` PASS
- `test_first_hit_barrier_result_uses_open_distance_when_both_hit_same_bar` still FAIL because barrier helper is not implemented yet

---

### Task 3: Implement First-Hit Barrier Outcomes Once and Reuse Them

**Files:**
- Modify: `API/signal_research.py:150-220`, `API/signal_research.py:351-397`
- Test: `tests/test_signal_research.py`

- [ ] **Step 1: Add a failing barrier-outcomes regression test**

Append to `tests/test_signal_research.py`:

```python
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
```

- [ ] **Step 2: Run the new barrier test and verify it fails**

Run: `cd /home/hohla/git/SoSimple && python -m pytest tests/test_signal_research.py::test_build_barrier_outcomes_produces_tp_sl_and_neither_rows -v`

Expected:
- FAIL because `build_barrier_outcomes()` does not exist yet

- [ ] **Step 3: Implement the barrier helper and long-form outcomes dataframe**

Add these helpers to `API/signal_research.py`:

```python
def first_hit_barrier_result(opens, highs, lows, entry_price, signal, sl, tp):
    if signal == 1:
        sl_price = entry_price - sl
        tp_price = entry_price + tp
        for opn, high, low in zip(opens, highs, lows):
            sl_hit = low <= sl_price
            tp_hit = high >= tp_price
            if sl_hit and tp_hit:
                return 'SL_FIRST' if abs(opn - sl_price) <= abs(tp_price - opn) else 'TP_FIRST'
            if tp_hit:
                return 'TP_FIRST'
            if sl_hit:
                return 'SL_FIRST'
    else:
        sl_price = entry_price + sl
        tp_price = entry_price - tp
        for opn, high, low in zip(opens, highs, lows):
            sl_hit = high >= sl_price
            tp_hit = low <= tp_price
            if sl_hit and tp_hit:
                return 'SL_FIRST' if abs(opn - sl_price) <= abs(opn - tp_price) else 'TP_FIRST'
            if tp_hit:
                return 'TP_FIRST'
            if sl_hit:
                return 'SL_FIRST'
    return 'NEITHER'


def build_barrier_outcomes(exc, ohlc, horizons=BARRIER_HORIZONS, sl_levels=SL_LEVELS, tp_levels=TP_LEVELS):
    ohlc_sorted = ohlc.sort_values('time').reset_index(drop=True)
    opens = ohlc_sorted['open'].to_numpy()
    highs = ohlc_sorted['high'].to_numpy()
    lows = ohlc_sorted['low'].to_numpy()
    records = []

    for _, row in exc.iterrows():
        idx = int(row['ohlc_idx'])
        entry_price = float(row['entry_close'])
        signal = int(row['signal'])
        for horizon in horizons:
            end_idx = idx + horizon
            if end_idx >= len(ohlc_sorted):
                continue
            bar_opens = opens[idx + 1:end_idx + 1]
            bar_highs = highs[idx + 1:end_idx + 1]
            bar_lows = lows[idx + 1:end_idx + 1]
            for sl in sl_levels:
                for tp in tp_levels:
                    outcome = first_hit_barrier_result(bar_opens, bar_highs, bar_lows, entry_price, signal, sl, tp)
                    pnl = tp if outcome == 'TP_FIRST' else -sl if outcome == 'SL_FIRST' else row[f'net_{horizon}']
                    records.append({
                        'time': row['time'],
                        'signal': signal,
                        'ratio_bin': row.get('ratio_bin'),
                        'atr_bucket': row.get('atr_bucket', 'ALL'),
                        'pred_fav_3': row.get('pred_fav_3'),
                        'pred_fav_6': row.get('pred_fav_6'),
                        'pred_fav_12': row.get('pred_fav_12'),
                        'pred_adv_3': row.get('pred_adv_3'),
                        'pred_adv_6': row.get('pred_adv_6'),
                        'horizon': horizon,
                        'SL': sl,
                        'TP': tp,
                        'outcome': outcome,
                        'pnl': pnl,
                    })

    return pd.DataFrame(records)
```

Add one aggregation helper for reuse by multiple reports:

```python
def summarize_barrier_outcomes(outcomes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (horizon, sl, tp), sub in outcomes.groupby(['horizon', 'SL', 'TP'], sort=False):
        n = len(sub)
        tp_first = (sub['outcome'] == 'TP_FIRST').sum()
        sl_first = (sub['outcome'] == 'SL_FIRST').sum()
        neither = (sub['outcome'] == 'NEITHER').sum()
        gross_profit = sub.loc[sub['pnl'] > 0, 'pnl'].sum()
        gross_loss = -sub.loc[sub['pnl'] < 0, 'pnl'].sum()
        rows.append({
            'horizon': horizon,
            'SL': sl,
            'TP': tp,
            'N': n,
            'tp_first_pct': 100.0 * tp_first / n,
            'sl_first_pct': 100.0 * sl_first / n,
            'neither_pct': 100.0 * neither / n,
            'PF_num': gross_profit / (gross_loss + 1e-6),
            'AvgPnL_num': sub['pnl'].mean(),
            'TotalPnL_num': sub['pnl'].sum(),
        })
    return pd.DataFrame(rows)
```

- [ ] **Step 4: Run the full test file and verify barrier logic now passes**

Run: `cd /home/hohla/git/SoSimple && python -m pytest tests/test_signal_research.py -v`

Expected:
- All current tests PASS

---

### Task 4: Replace the Old Reports with Variant-2 Research Sections

**Files:**
- Modify: `API/signal_research.py:153-425`
- Test: `tests/test_signal_research.py`

- [ ] **Step 1: Add a smoke test that captures the new report section names**

Append to `tests/test_signal_research.py`:

```python
def test_report_sections_print_expected_headers(capsys):
    exc = pd.DataFrame({
        'signal': [1, -1],
        'ratio_bin': ['4-5', '2-3'],
        'atr_bucket': ['Q4', 'Q2'],
        'mfe_12': [20.0, 18.0],
        'mae_12': [10.0, 11.0],
        'net_12': [6.0, 2.0],
        'mfe_3': [6.0, 5.0],
        'mae_3': [2.0, 3.0],
        'net_3': [1.0, 0.5],
        'mfe_6': [10.0, 9.0],
        'mae_6': [5.0, 4.0],
        'net_6': [2.0, 1.0],
        'mfe_24': [26.0, 22.0],
        'mae_24': [16.0, 17.0],
        'net_24': [7.0, 3.0],
        'mfe_48': [35.0, 30.0],
        'mae_48': [20.0, 22.0],
        'net_48': [8.0, 4.0],
        'fav_1': [4.0, 5.0],
        'adv_1': [1.0, 2.0],
        'close_net_1': [2.0, 1.0],
        'fav_3': [7.0, 8.0],
        'adv_3': [2.0, 3.0],
        'close_net_3': [3.0, 2.0],
        'fav_6': [10.0, 9.0],
        'adv_6': [4.0, 5.0],
        'close_net_6': [4.0, 3.0],
        'pred_fav_3': [0.3, 0.4],
        'pred_fav_6': [0.5, 0.6],
        'pred_fav_12': [0.7, 0.8],
        'pred_adv_3': [0.1, 0.2],
        'pred_adv_6': [0.2, 0.3],
    })
    barriers = pd.DataFrame({
        'horizon': [12, 12],
        'SL': [5, 10],
        'TP': [30, 30],
        'N': [2, 2],
        'tp_first_pct': [50.0, 50.0],
        'sl_first_pct': [25.0, 50.0],
        'neither_pct': [25.0, 0.0],
        'PF_num': [1.40, 1.10],
        'AvgPnL_num': [1.5, 0.8],
        'TotalPnL_num': [3.0, 1.6],
    })
    barrier_outcomes = pd.DataFrame({
        'signal': [1, -1],
        'ratio_bin': ['4-5', '2-3'],
        'atr_bucket': ['Q4', 'Q2'],
        'pred_fav_3': [0.3, 0.4],
        'pred_fav_6': [0.5, 0.6],
        'pred_fav_12': [0.7, 0.8],
        'pred_adv_3': [0.1, 0.2],
        'pred_adv_6': [0.2, 0.3],
        'horizon': [12, 12],
        'SL': [5, 5],
        'TP': [30, 30],
        'outcome': ['TP_FIRST', 'SL_FIRST'],
        'pnl': [30.0, -5.0],
    })

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
```

- [ ] **Step 2: Run the report smoke test and verify it fails**

Run: `cd /home/hohla/git/SoSimple && python -m pytest tests/test_signal_research.py::test_report_sections_print_expected_headers -v`

Expected:
- FAIL because the new report functions do not exist yet

- [ ] **Step 3: Implement the report functions from the approved spec**

Replace the old `report_by_horizon`, `report_filter_impact`, and `report_sl_tp_grid` flow with these new functions:

```python
def report_signal_passport(exc: pd.DataFrame):
    print_separator('1. Signal Passport')
    rows = []
    for h in HORIZONS:
        mfe = exc[f'mfe_{h}'].dropna()
        mae = exc[f'mae_{h}'].dropna()
        net = exc[f'net_{h}'].dropna()
        rows.append({
            'horizon': f'{h}H',
            'N': len(mfe),
            'MFE_mean': f'{mfe.mean():.1f}',
            'MFE_med': f'{mfe.median():.1f}',
            'MFE_p75': f'{mfe.quantile(0.75):.1f}',
            'MFE_p90': f'{mfe.quantile(0.90):.1f}',
            'MAE_mean': f'{mae.mean():.1f}',
            'MAE_med': f'{mae.median():.1f}',
            'MAE_p75': f'{mae.quantile(0.75):.1f}',
            'MAE_p90': f'{mae.quantile(0.90):.1f}',
            'Net_mean': f'{net.mean():.1f}',
            'Net_med': f'{net.median():.1f}',
            'MFE/MAE': f'{mfe.mean() / (mae.mean() + 1e-6):.2f}',
            'WinRate': f'{(net > 0).mean() * 100:.1f}%',
            'PF': f'{net[net > 0].sum() / (-net[net < 0].sum() + 1e-6):.2f}',
        })
    print(pd.DataFrame(rows).to_string(index=False))


def report_pullback_profile(exc: pd.DataFrame):
    print_separator('2. Pullback Profile')
    groups = [
        ('ALL', exc),
        ('BUY', exc[exc['signal'] == 1]),
        ('SELL', exc[exc['signal'] == -1]),
    ]
    for ratio_label in ['2-3', '3-4', '4-5', '5+']:
        groups.append((f'ratio={ratio_label}', exc[exc['ratio_bin'] == ratio_label]))
    for name, sub in groups:
        if len(sub) == 0:
            continue
        print(f'  --- {name} ---')
        rows = []
        for w in PULLBACK_WINDOWS:
            rows.append({
                'window': f'{w}H',
                'N': len(sub),
                'fav_mean': f"{sub[f'fav_{w}'].mean():.1f}",
                'fav_med': f"{sub[f'fav_{w}'].median():.1f}",
                'adv_mean': f"{sub[f'adv_{w}'].mean():.1f}",
                'adv_med': f"{sub[f'adv_{w}'].median():.1f}",
                'fav/adv': f"{sub[f'fav_{w}'].mean() / (sub[f'adv_{w}'].mean() + 1e-6):.2f}",
                '%adv>=5': f"{(sub[f'adv_{w}'] >= 5).mean() * 100:.1f}%",
                '%adv>=10': f"{(sub[f'adv_{w}'] >= 10).mean() * 100:.1f}%",
                '%adv>=15': f"{(sub[f'adv_{w}'] >= 15).mean() * 100:.1f}%",
                '%fav>=5': f"{(sub[f'fav_{w}'] >= 5).mean() * 100:.1f}%",
                '%fav>=10': f"{(sub[f'fav_{w}'] >= 10).mean() * 100:.1f}%",
                '%fav>=15': f"{(sub[f'fav_{w}'] >= 15).mean() * 100:.1f}%",
                '%close>0': f"{(sub[f'close_net_{w}'] > 0).mean() * 100:.1f}%",
            })
        print(pd.DataFrame(rows).to_string(index=False))


def report_first_hit_barriers(barrier_summary: pd.DataFrame):
    print_separator('3. First-Hit Barrier Matrix')
    rows = barrier_summary.copy()
    rows['R:R'] = rows['TP'] / rows['SL']
    rows['%TP_FIRST'] = rows['tp_first_pct'].map(lambda x: f'{x:.1f}%')
    rows['%SL_FIRST'] = rows['sl_first_pct'].map(lambda x: f'{x:.1f}%')
    rows['%NEITHER'] = rows['neither_pct'].map(lambda x: f'{x:.1f}%')
    rows['PF'] = rows['PF_num'].map(lambda x: f'{x:.2f}')
    rows['AvgPnL'] = rows['AvgPnL_num'].map(lambda x: f'{x:.1f}')
    rows['TotalPnL'] = rows['TotalPnL_num'].map(lambda x: f'{x:.0f}')
    print(rows[['horizon', 'SL', 'TP', 'R:R', 'N', '%TP_FIRST', '%SL_FIRST', '%NEITHER', 'PF', 'AvgPnL', 'TotalPnL']].to_string(index=False))
```

Then add the two group-level reports:

```python
def report_amplitude_filters(exc: pd.DataFrame, barrier_outcomes: pd.DataFrame, barrier_summary: pd.DataFrame):
    print_separator('4. Amplitude Filters')
    top_barriers = (
        barrier_summary[barrier_summary['horizon'] == BASE_HORIZON]
        .sort_values(['PF_num', 'AvgPnL_num'], ascending=False)
        .head(2)[['horizon', 'SL', 'TP']]
    )
    for metric in ['pred_fav_3', 'pred_fav_6', 'pred_fav_12', 'pred_adv_3', 'pred_adv_6']:
        sub = exc[['time', metric, 'net_12', 'mfe_12', 'mae_12']].dropna().copy()
        if len(sub) < 20 or sub[metric].nunique() < 3:
            continue
        sub['bucket'] = pd.qcut(sub[metric], q=[0, 0.25, 0.75, 1.0], labels=['low', 'mid', 'high'], duplicates='drop')
        print(f'  --- {metric} ---')
        rows = []
        for bucket, bucket_df in sub.groupby('bucket', observed=False):
            row = {
                'bucket': bucket,
                'N': len(bucket_df),
                'Net_12': f"{bucket_df['net_12'].mean():.1f}",
                'MFE_12': f"{bucket_df['mfe_12'].mean():.1f}",
                'MAE_12': f"{bucket_df['mae_12'].mean():.1f}",
                'PF_12': f"{bucket_df.loc[bucket_df['net_12'] > 0, 'net_12'].sum() / (-bucket_df.loc[bucket_df['net_12'] < 0, 'net_12'].sum() + 1e-6):.2f}",
            }
            for _, best in top_barriers.iterrows():
                best_outcomes = barrier_outcomes[
                    (barrier_outcomes['horizon'] == best['horizon']) &
                    (barrier_outcomes['SL'] == best['SL']) &
                    (barrier_outcomes['TP'] == best['TP']) &
                    (barrier_outcomes['time'].isin(bucket_df['time']))
                ]
                row[f"TP%_{int(best['SL'])}/{int(best['TP'])}"] = f"{(best_outcomes['outcome'] == 'TP_FIRST').mean() * 100:.1f}%"
                row[f"SL%_{int(best['SL'])}/{int(best['TP'])}"] = f"{(best_outcomes['outcome'] == 'SL_FIRST').mean() * 100:.1f}%"
            rows.append(row)
        print(pd.DataFrame(rows).to_string(index=False))


def report_regime_splits(exc: pd.DataFrame, barrier_outcomes: pd.DataFrame, barrier_summary: pd.DataFrame):
    print_separator('5. Regime Split')
    best_12 = (
        barrier_summary[barrier_summary['horizon'] == BASE_HORIZON]
        .sort_values(['PF_num', 'AvgPnL_num'], ascending=False)
        .head(1)
    )
    best_sl = int(best_12.iloc[0]['SL'])
    best_tp = int(best_12.iloc[0]['TP'])
    best_outcomes = barrier_outcomes[
        (barrier_outcomes['horizon'] == BASE_HORIZON) &
        (barrier_outcomes['SL'] == best_sl) &
        (barrier_outcomes['TP'] == best_tp)
    ][['time', 'outcome']]
    base = exc.merge(best_outcomes, on='time', how='left')
    group_defs = [
        ('direction', base.assign(direction=np.where(base['signal'] == 1, 'BUY', 'SELL')), 'direction'),
        ('ratio_bin', base, 'ratio_bin'),
        ('atr_bucket', base, 'atr_bucket'),
    ]
    for label, frame, key in group_defs:
        print(f'  --- {label} ---')
        rows = []
        for group_value, sub in frame.groupby(key, dropna=False):
            rows.append({
                label: group_value,
                'N': len(sub),
                'MFE_12': f"{sub['mfe_12'].mean():.1f}",
                'MAE_12': f"{sub['mae_12'].mean():.1f}",
                'Net_12': f"{sub['net_12'].mean():.1f}",
                'PF_12': f"{sub.loc[sub['net_12'] > 0, 'net_12'].sum() / (-sub.loc[sub['net_12'] < 0, 'net_12'].sum() + 1e-6):.2f}",
                'TP_FIRST': f"{(sub['outcome'] == 'TP_FIRST').mean() * 100:.1f}%",
                'SL_FIRST': f"{(sub['outcome'] == 'SL_FIRST').mean() * 100:.1f}%",
                'Best': f'{best_sl}/{best_tp}',
            })
        print(pd.DataFrame(rows).to_string(index=False))
```

Finally, add a short summary printer:

```python
def print_practical_conclusions(exc: pd.DataFrame, barrier_summary: pd.DataFrame):
    print_separator('6. Practical Conclusions')
    pullback_1 = exc['adv_1'].mean()
    pullback_3 = exc['adv_3'].mean()
    best_12 = barrier_summary[barrier_summary['horizon'] == BASE_HORIZON].sort_values(['PF_num', 'AvgPnL_num'], ascending=False).head(1).iloc[0]
    print(f"  Entry: early adverse move mean = {pullback_1:.1f} in 1H, {pullback_3:.1f} in 3H.")
    print(f"  SL/TP: best 12H first-hit combo so far = SL {int(best_12['SL'])} / TP {int(best_12['TP'])}, PF {best_12['PF_num']:.2f}.")
    print("  Filters: inspect amplitude buckets where pred_fav is high or pred_adv is low.")
    print("  Regimes: compare BUY vs SELL, ratio buckets, and ATR quartiles before choosing one universal rule.")
    print("  Next for Variant 3: test market entry, pullback limit entry, delayed entry, and cancel windows using the strongest findings above.")
```

- [ ] **Step 4: Update `main()` to use the new flow**

Replace the old wiring with:

```python
    exc = compute_excursions(df, ohlc)
    print(f"  Готово: {len(exc)} сигналов с excursion данными")

    barrier_outcomes = build_barrier_outcomes(exc, ohlc)
    barrier_summary = summarize_barrier_outcomes(barrier_outcomes)

    report_signal_passport(exc)
    report_by_ratio(exc)
    report_pullback_profile(exc)
    report_first_hit_barriers(barrier_summary)
    report_amplitude_filters(exc, barrier_outcomes, barrier_summary)
    report_regime_splits(exc, barrier_outcomes, barrier_summary)
    report_prediction_vs_reality(exc)
    print_practical_conclusions(exc, barrier_summary)
```

- [ ] **Step 5: Run the test file and verify the new reporting functions work**

Run: `cd /home/hohla/git/SoSimple && python -m pytest tests/test_signal_research.py -v`

Expected:
- All tests PASS

---

### Task 5: Verify Variant-2 Output End-to-End

**Files:**
- Modify: none
- Verify: `API/signal_research.py`, `tests/test_signal_research.py`

- [ ] **Step 1: Run targeted pytest for the new research module**

Run: `cd /home/hohla/git/SoSimple && python -m pytest tests/test_signal_research.py -v`

Expected:
- PASS

- [ ] **Step 2: Run the actual OOS research script**

Run: `cd /home/hohla/git/SoSimple && source .venv/bin/activate && python -m API.signal_research --test-only`

Expected:
- stdout includes these sections in order:
  - `Signal Passport`
  - `Результаты по силе ratio`
  - `Pullback Profile`
  - `First-Hit Barrier Matrix`
  - `Amplitude Filters`
  - `Regime Split`
  - `Предсказание vs Реальность`
  - `Practical Conclusions`

- [ ] **Step 3: Do a manual spec coverage check before calling the task complete**

Check the output against [2026-04-01-signal-research-variant-2-design.md](../specs/2026-04-01-signal-research-variant-2-design.md):

- `Signal Passport` includes percentiles, not only means
- `Pullback Profile` covers windows `1/3/6`
- `First-Hit Barrier Matrix` is path-dependent, not 50/50 approximated
- `Amplitude Filters` uses directional amplitude aliases, not `ratio_3/ratio_6`
- `Regime Split` shows `BUY/SELL`, `ratio_bin`, and ATR-based groups
- `Practical Conclusions` points to concrete hypotheses for variant 3

Expected:
- every bullet above can be answered with “yes” from the actual script output

---

## Self-Review Notes

- Spec coverage: all six report blocks from the approved spec are mapped to concrete functions and verification steps.
- Hidden dependency resolved: ATR buckets are defined through internal `ATR14` from OHLC because the current signal CSV has no ATR field.
- Placeholder scan: no `TODO` or “implement later” language remains in the tasks.
- Scope check: the plan stays inside variant 2 and does not drift into EA logic or strategy simulation.
