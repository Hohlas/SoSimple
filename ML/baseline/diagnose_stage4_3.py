# =============================================================================
# Файл: ML/baseline/diagnose_stage4_3.py
# Назначение: Stage 4.3 DIAGNOSTIC_ONLY — декомпозиция потерь PF между Oracle и
#              Stage 4.2 baseline. Не выбирает winner, не открывает test.
# Вход: DATA/Nero_XAUUSD_*_labeled.csv, DATA/XAUUSD_H1_OHLC.csv
# Выход: ML/reports/stage4_3_diagnostics.json
# Статус: DIAGNOSTIC_ONLY — найденные прибыльные зоны hypothesis_only
# Запрет: no test, no winner selection
# Язык: Python 3.10+
# Создан: 2026-06-15
# =============================================================================

import argparse, json, os, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import roc_auc_score
import xgboost as xgb

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from processing.label_signals import load_ohlc_index, evaluate_fractal_stop_trade

# ---------------------------------------------------------------------------
# Constants (from Stage 4.2)
# ---------------------------------------------------------------------------

BASE_CHANNEL_KEYS = ['price', 'direction', 'front', 'back', 'strong', 'break',
                     'reverse', 'power', 'count', 'impulse']

BREACH_TARGETS = {
    6: {0.2: {'buy': 'buy_stop_broken_H6_off02_flag',
              'sell': 'sell_stop_broken_H6_off02_flag'},
        0.5: {'buy': 'buy_stop_broken_H6_off05_flag',
              'sell': 'sell_stop_broken_H6_off05_flag'}},
    12: {0.2: {'buy': 'buy_stop_broken_H12_off02_flag',
               'sell': 'sell_stop_broken_H12_off02_flag'},
         0.5: {'buy': 'buy_stop_broken_H12_off05_flag',
               'sell': 'sell_stop_broken_H12_off05_flag'}},
}

FAV_TARGETS = {
    6: {'buy': 'target_buy_H6_val', 'sell': 'target_sell_H6_val'},
    12: {'buy': 'target_buy_H12_val', 'sell': 'target_sell_H12_val'},
}

WINNER_TARGET = 'sell_H6_off05'
WINNER_H = 6
WINNER_OFF = 0.5
WINNER_SIDE = 'sell'
WINNER_P = 0.4
WINNER_MIN_FAV = 0.3
WINNER_MIN_RR = 1.0
WINNER_TP_FRACTION = 0.4
CAP = 5.0
CANONICAL_SPREAD = 0.20
BLOCK_BOOTSTRAP_SIZE = 15
N_BOOTSTRAP = 500

TRAIN_MAX_YEAR = 2016
VAL_STOP_YEARS = {2017, 2018}
VAL_EVAL_MIN_YEAR = 2019


# ===========================================================================
# Helper: make JSON-serializable
# ===========================================================================

def _safe(v):
    """Convert numpy/Python values to JSON-safe types."""
    if isinstance(v, np.floating):
        return float(v)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, (float,)) and not np.isfinite(v):
        return None
    return v


# ===========================================================================
# Data loading (source: diagnose_stage4_gap.py)
# ===========================================================================

def load_splits(train_path, val_path, purge_bars=12):
    train_df = pd.read_csv(train_path, sep=';')
    val_df = pd.read_csv(val_path, sep=';')
    train_df['_year'] = pd.to_datetime(
        train_df['time'], format='%Y.%m.%d %H:%M', errors='coerce').dt.year
    val_df['_year'] = pd.to_datetime(
        val_df['time'], format='%Y.%m.%d %H:%M', errors='coerce').dt.year
    train = train_df[train_df['_year'] <= TRAIN_MAX_YEAR].copy()
    val_stop = train_df[train_df['_year'].isin(VAL_STOP_YEARS)].copy()
    val_eval_train_part = train_df[train_df['_year'] >= VAL_EVAL_MIN_YEAR].copy()
    val_eval = pd.concat([val_eval_train_part, val_df], ignore_index=True)
    if purge_bars > 0:
        if len(train) > purge_bars:
            train = train.iloc[:-purge_bars]
        if len(val_stop) > purge_bars:
            val_stop = val_stop.iloc[:-purge_bars]
        if len(val_eval) > purge_bars:
            val_eval = val_eval.iloc[:-purge_bars]
    return train, val_stop, val_eval


# ===========================================================================
# Feature extraction (source: diagnose_stage4_gap.py)
# ===========================================================================

def _extract_base(df, n_levels=100):
    features, names = [], []
    for level in range(n_levels):
        col = f'fractal{level}'
        if col not in df.columns:
            break
        parts = df[col].astype(str).str.split(':', expand=True)
        idx = {'price': 1, 'direction': 2, 'front': 3, 'back': 4, 'strong': 5,
               'break': 6, 'reverse': 7, 'power': 8, 'count': 9, 'impulse': 10}
        for key in BASE_CHANNEL_KEYS:
            vals = pd.to_numeric(parts[idx[key]], errors='coerce').fillna(0.0).values
            features.append(vals.astype(np.float64))
            names.append(f'f{level}_{key}')
    if 'ATR' in df.columns:
        features.append(df['ATR'].values.astype(np.float64))
        names.append('ATR')
    return np.column_stack(features), names


def _extract_time(df):
    times_dt = pd.to_datetime(df['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    hour_frac = times_dt.dt.hour.fillna(0).values + \
        times_dt.dt.minute.fillna(0).values / 60.0
    hour_sin = np.sin(2 * np.pi * hour_frac / 24)
    hour_cos = np.cos(2 * np.pi * hour_frac / 24)
    dow = times_dt.dt.dayofweek.fillna(0).values.astype(float)
    dow_sin = np.sin(2 * np.pi * dow / 7)
    dow_cos = np.cos(2 * np.pi * dow / 7)
    return np.column_stack([hour_sin, hour_cos, dow_sin, dow_cos]), \
        ['hour_sin', 'hour_cos', 'dow_sin', 'dow_cos']


def profile_base_raw(df):
    return _extract_base(df)


def profile_base_raw_plus_time(df):
    Xb, nb = _extract_base(df)
    Xt, nt = _extract_time(df)
    return np.column_stack([Xb, Xt]), nb + nt


# ===========================================================================
# OHLC & entry prices (source: diagnose_stage4_gap.py)
# ===========================================================================

def compute_entry_prices(df, ohlc, times, time_idx):
    entry = np.full(len(df), np.nan, dtype=np.float64)
    for i, row in df.iterrows():
        try:
            row_dt = datetime.strptime(str(row['time']), '%Y.%m.%d %H:%M') \
                .replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        idx0 = time_idx.get(row_dt)
        if idx0 is not None and idx0 + 1 < len(times):
            entry[i] = ohlc[times[idx0 + 1]][0]
    return entry


def parse_trade_fractal0(raw):
    try:
        if pd.isna(raw):
            return None
        parts = str(raw).split(':')
        if len(parts) != 23:
            return None
        price = float(parts[1]) if parts[1] else None
        direction = int(float(parts[2])) if parts[2] else None
        if price is None or direction is None or direction == 0:
            return None
        return {'price': price, 'direction': direction}
    except (ValueError, TypeError):
        return None


# ===========================================================================
# Model training (source: diagnose_stage4_gap.py)
# ===========================================================================

def train_xgb_breach(X_train, y_train, X_val_stop, y_val_stop, random_state=42):
    neg = int((y_train == 0).sum())
    pos = int((y_train == 1).sum())
    scale_pos_weight = neg / pos if pos > 0 else 1.0
    model = xgb.XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        objective='binary:logistic', eval_metric='auc',
        early_stopping_rounds=20, random_state=random_state,
        n_jobs=-1, verbosity=0,
    )
    model.fit(X_train, y_train, eval_set=[(X_val_stop, y_val_stop)], verbose=False)
    return model


def train_rf_fav(X_train, y_train, random_state=42):
    model = RandomForestRegressor(
        n_estimators=200, max_depth=12, min_samples_leaf=50,
        random_state=random_state, n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


# ===========================================================================
# Trade simulation — extended for Stage 4.3 (source: diagnose_stage4_gap.py,
# enhanced with return_details tracking trade_id, row_index, all debug fields)
# ===========================================================================

def simulate_trades(df, entry_prices, breach_proba, fav_pred, ohlc, times,
                    time_idx, side='sell', h=6, stop_offset=0.5,
                    p=0.5, min_fav_val=0.5, min_rr=1.5, tp_fraction=0.5,
                    cap=5.0, spread=0.0, return_details=False,
                    tp_policy='fav_fraction', tp_policy_value=None,
                    skip_min_fav=False, skip_min_rr=False):
    """Simulate trades with correct spread model (OHLC=Bid).

    Args:
        tp_policy: 'fav_fraction', 'fixed_atr', 'fixed_r'
        tp_policy_value: value for the policy (fraction, atr_constant, r_multiple)
        skip_min_fav: if True, skip min_fav_val filter
        skip_min_rr: if True, skip min_rr filter
    """
    if tp_policy_value is None:
        tp_policy_value = tp_fraction

    trade_direction = -1 if side == 'buy' else 1
    expected_fractal_dir = -1 if side == 'buy' else 1
    trades = []
    trade_id = 0

    for i, (idx, row) in enumerate(df.iterrows()):
        fractal0 = parse_trade_fractal0(row.get('fractal0'))
        if fractal0 is None:
            continue
        if fractal0['direction'] != expected_fractal_dir:
            continue

        fractal_price = fractal0['price']
        try:
            row_dt = datetime.strptime(str(row['time']), '%Y.%m.%d %H:%M') \
                .replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        idx0 = time_idx.get(row_dt)
        if idx0 is None or idx0 + h >= len(times):
            continue

        entry_price_val = entry_prices[i]
        if np.isnan(entry_price_val):
            continue
        atr_val = float(row.get('ATR', np.nan))
        if np.isnan(atr_val) or atr_val <= 0:
            continue

        pred_break = breach_proba[i]
        pred_fav = fav_pred[i]
        if np.isnan(pred_break) or np.isnan(pred_fav):
            continue

        # Stop price (Bid terms)
        if trade_direction == -1:
            stop_price = min(fractal_price, entry_price_val) - stop_offset * atr_val
            stop_val = (entry_price_val - stop_price) / atr_val
        else:
            stop_price = max(fractal_price, entry_price_val) + stop_offset * atr_val
            stop_val = (stop_price - entry_price_val) / atr_val
        if stop_val <= 0:
            continue

        # Resolve TP value based on policy
        tp_val_atr = resolve_tp_val(tp_policy, tp_policy_value, pred_fav, stop_val)
        tp_val_atr = min(tp_val_atr, cap)
        if tp_val_atr <= 0:
            continue

        # TP price (Bid terms)
        if trade_direction == -1:
            tp_price = entry_price_val + tp_val_atr * atr_val
        else:
            tp_price = entry_price_val - tp_val_atr * atr_val

        # Bars with correct convention (OHLC=Bid)
        bars_h_bid = [(ohlc[times[k]][0], ohlc[times[k]][1],
                        ohlc[times[k]][2], ohlc[times[k]][3])
                       for k in range(idx0 + 1, idx0 + 1 + h)]
        if trade_direction == -1:
            entry_eff = entry_price_val + spread
            bars_h_eff = bars_h_bid
        else:
            entry_eff = entry_price_val
            bars_h_eff = [(o + spread, h + spread, l + spread, c + spread)
                          for o, h, l, c in bars_h_bid]

        stop_val_actual = abs(entry_eff - stop_price) / atr_val
        if stop_val_actual <= 0:
            continue

        # Trade filters
        if pred_break >= p:
            continue
        if not skip_min_fav and pred_fav < min_fav_val:
            continue
        if not skip_min_rr and pred_fav / stop_val_actual < min_rr:
            continue

        trade_id += 1
        outcome = evaluate_fractal_stop_trade(
            bars_h_eff, trade_direction, entry_eff, stop_price, tp_price, atr_val)

        year_val = row.get('_year')
        year_int = int(year_val) if not pd.isna(year_val) else None

        actual_rr_val = tp_val_atr / stop_val_actual if stop_val_actual > 0 else 0

        trade_rec = {
            'exit': outcome['exit'],
            'pnl_val': outcome['pnl_val'],
            'stop_val': stop_val_actual,
            'pnl_r': outcome['pnl_val'] / stop_val_actual
                if stop_val_actual > 0 else outcome['pnl_val'],
            'ambiguous': outcome['ambiguous'],
            'year': year_int,
            'side': side,
        }
        if return_details:
            trade_rec['trade_id'] = trade_id
            trade_rec['row_index'] = int(idx)
            if '_candidate_id' in row:
                trade_rec['candidate_id'] = int(row.get('_candidate_id'))
            trade_rec['time'] = str(row.get('time', ''))
            trade_rec['entry_price'] = float(entry_eff)
            trade_rec['stop_price'] = float(stop_price)
            trade_rec['tp_price'] = float(tp_price)
            trade_rec['tp_val'] = float(tp_val_atr)
            trade_rec['actual_rr'] = float(actual_rr_val)
            trade_rec['pred_break'] = float(pred_break)
            trade_rec['breach_flag_true'] = int(row.get(
                BREACH_TARGETS[h][stop_offset][side], 0) or 0)
            trade_rec['pred_fav'] = float(pred_fav)
            trade_rec['fav_val_true'] = float(row.get(
                FAV_TARGETS[h][side], np.nan) or np.nan)
            fav_true = float(row.get(FAV_TARGETS[h][side], np.nan) or np.nan)
            fav_error_val = float(pred_fav) - fav_true if not np.isnan(fav_true) else np.nan
            trade_rec['fav_error'] = fav_error_val
            trade_rec['atr'] = float(atr_val)
        trades.append(trade_rec)

    return trades


# ===========================================================================
# Helper: resolve TP value
# ===========================================================================

def resolve_tp_val(policy, value, pred_fav, stop_val):
    if policy == 'fav_fraction':
        return pred_fav * value
    elif policy == 'fixed_atr':
        return float(value)
    elif policy == 'fixed_r':
        return stop_val * value
    return 0.0


# ===========================================================================
# Helper: actual RR
# ===========================================================================

def actual_rr(trade):
    tp = trade.get('tp_val', 0)
    sv = trade.get('stop_val', 1)
    return tp / sv if sv > 0 else 0.0


# ===========================================================================
# Trade metrics — Stage 4.3 enhanced version
# ===========================================================================

def compute_yearly_metrics(trades):
    years_covered = sorted(set(t['year'] for t in trades if t['year'] is not None))
    yearly = {}
    for yr in years_covered:
        yr_trades = [t for t in trades if t['year'] == yr]
        if len(yr_trades) < 1:
            continue
        yr_profit = sum(max(0, t['pnl_val']) for t in yr_trades)
        yr_loss = abs(sum(min(0, t['pnl_val']) for t in yr_trades))
        yr_pf = yr_profit / yr_loss if yr_loss > 0 else (float('inf') if yr_profit > 0 else 0.0)
        exits = Counter(t['exit'] for t in yr_trades)
        n_yr = len(yr_trades)
        yearly[str(int(yr))] = {
            'pf': round(_safe(yr_pf), 3) if yr_pf != float('inf') else yr_pf,
            'n': n_yr,
            'gross_profit': round(_safe(yr_profit), 3),
            'gross_loss': round(_safe(yr_loss), 3),
            'tp_pct': round(exits.get('TP', 0) / n_yr * 100, 1) if n_yr else 0,
            'sl_pct': round(exits.get('SL', 0) / n_yr * 100, 1) if n_yr else 0,
            'timeout_pct': round(exits.get('TIMEOUT', 0) / n_yr * 100, 1) if n_yr else 0,
        }
    return yearly


def compute_trade_metrics(trades):
    if not trades:
        return {'pf': 0.0, 'n_trades': 0, 'trades_per_year': 0, 'n_years': 0,
                'gross_profit': 0.0, 'gross_loss': 0.0, 'win_rate': 0.0}

    n_trades = len(trades)
    years_covered = sorted(set(t['year'] for t in trades if t['year'] is not None))
    n_years = len(years_covered) if years_covered else 1
    trades_per_year = n_trades / n_years if n_years > 0 else n_trades

    gross_profit = sum(max(0, t['pnl_val']) for t in trades)
    gross_loss = abs(sum(min(0, t['pnl_val']) for t in trades))
    pf = gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)

    exits = Counter(t['exit'] for t in trades)
    ambiguous_n = sum(1 for t in trades if t.get('ambiguous', 0))
    win_rate = sum(1 for t in trades if t['pnl_val'] > 0) / n_trades * 100 if n_trades else 0

    wins = [t for t in trades if t['pnl_val'] > 0]
    losses = [t for t in trades if t['pnl_val'] < 0]
    avg_win_atr = np.mean([t['pnl_val'] for t in wins]) if wins else 0
    avg_loss_atr = np.mean([abs(t['pnl_val']) for t in losses]) if losses else 0

    def _get_pnl_r(t):
        if 'pnl_r' in t:
            return t['pnl_r']
        sv = t.get('stop_val', 1.0)
        return t['pnl_val'] / sv if sv > 0 else t['pnl_val']
    avg_win_r = np.mean([_get_pnl_r(t) for t in wins]) if wins else 0
    avg_loss_r = np.mean([abs(_get_pnl_r(t)) for t in losses]) if losses else 0

    yearly = compute_yearly_metrics(trades)

    result = {
        'pf': round(_safe(pf), 3) if pf != float('inf') else pf,
        'n_trades': n_trades,
        'trades_per_year': round(_safe(trades_per_year), 1),
        'n_years': n_years,
        'yearly': yearly,
        'gross_profit': round(_safe(gross_profit), 3),
        'gross_loss': round(_safe(gross_loss), 3),
        'win_rate': round(_safe(win_rate), 1),
        'avg_win_atr': round(_safe(avg_win_atr), 3),
        'avg_loss_atr': round(_safe(avg_loss_atr), 3),
        'avg_win_r': round(_safe(avg_win_r), 3),
        'avg_loss_r': round(_safe(avg_loss_r), 3),
        'tp_n': exits.get('TP', 0),
        'sl_n': exits.get('SL', 0),
        'timeout_n': exits.get('TIMEOUT', 0),
        'ambiguous_n': ambiguous_n,
    }
    return result


# ===========================================================================
# Loss attribution
# ===========================================================================

def loss_attribution(trades):
    out = {}
    for exit_type in ('TP', 'SL', 'TIMEOUT'):
        subset = [t for t in trades if t['exit'] == exit_type]
        n = len(subset)
        if n == 0:
            out[exit_type] = {
                'n': 0, 'total_pnl': 0.0, 'mean_pnl': 0.0,
                'gross_profit': 0.0, 'gross_loss': 0.0,
                'pct_of_total_gross_profit': 0.0, 'pct_of_total_gross_loss': 0.0,
            }
            if exit_type == 'SL':
                out[exit_type].update({
                    'ambiguous_sl': 0, 'non_ambiguous_sl': 0,
                    'breach_fn_non_ambiguous': 0, 'breach_flag_true_rate': 0.0,
                })
            continue

        total_pnl = sum(t['pnl_val'] for t in subset)
        gross_profit_local = sum(max(0, t['pnl_val']) for t in subset)
        gross_loss_local = abs(sum(min(0, t['pnl_val']) for t in subset))

        total_gross_profit_all = sum(max(0, t['pnl_val']) for t in trades)
        total_gross_loss_all = abs(sum(min(0, t['pnl_val']) for t in trades))

        entry = {
            'n': n,
            'total_pnl': round(_safe(total_pnl), 2),
            'mean_pnl': round(_safe(total_pnl / n), 2) if n else 0,
            'gross_profit': round(_safe(gross_profit_local), 2),
            'gross_loss': round(_safe(gross_loss_local), 2),
            'pct_of_total_gross_profit': round(
                _safe(gross_profit_local / total_gross_profit_all),
                3) if total_gross_profit_all > 0 else 0.0,
            'pct_of_total_gross_loss': round(
                _safe(gross_loss_local / total_gross_loss_all),
                3) if total_gross_loss_all > 0 else 0.0,
        }

        if exit_type == 'SL':
            ambiguous_sl = sum(1 for t in subset if t.get('ambiguous', 0))
            non_ambiguous = n - ambiguous_sl
            breach_rate = sum(
                1 for t in subset if t.get('breach_flag_true', 0) == 1) / n if n else 0
            entry.update({
                'ambiguous_sl': ambiguous_sl,
                'non_ambiguous_sl': non_ambiguous,
                'breach_fn_non_ambiguous': non_ambiguous,
                'breach_flag_true_rate': round(_safe(breach_rate), 3),
            })

        out[exit_type] = entry
    return out


# ===========================================================================
# Yearly loss attribution
# ===========================================================================

def yearly_loss_attribution(trades):
    years_covered = sorted(set(t['year'] for t in trades if t['year'] is not None))
    result = {}
    for yr in years_covered:
        yr_trades = [t for t in trades if t['year'] == yr]
        if len(yr_trades) < 3:
            continue
        result[str(int(yr))] = loss_attribution(yr_trades)
    return result


# ===========================================================================
# Block bootstrap
# ===========================================================================

def block_bootstrap_pf(trades, block_size=BLOCK_BOOTSTRAP_SIZE, n_iter=N_BOOTSTRAP,
                       seed=42):
    if len(trades) < max(20, block_size * 2):
        return {'pf_median': None, 'pf_p05': None, 'pf_p95': None,
                'n_trades': len(trades), 'block_size': block_size}
    rng = np.random.RandomState(seed)
    pfs = []
    n_blocks = max(1, len(trades) // block_size)
    for _ in range(n_iter):
        block_idx = rng.randint(0, len(trades) - block_size, size=n_blocks)
        sample = []
        for bi in block_idx:
            sample.extend(trades[bi:bi + block_size])
        gp = sum(max(0, t['pnl_val']) for t in sample)
        gl = abs(sum(min(0, t['pnl_val']) for t in sample))
        pf = gp / gl if gl > 0 else (float('inf') if gp > 0 else 0.0)
        pfs.append(pf)
    pfs = np.array(pfs)
    finite_pfs = pfs[np.isfinite(pfs)]
    return {
        'pf_median': round(float(np.median(finite_pfs)), 3)
            if len(finite_pfs) > 0 else None,
        'pf_p05': round(float(np.percentile(finite_pfs, 5)), 3)
            if len(finite_pfs) > 0 else None,
        'pf_p95': round(float(np.percentile(finite_pfs, 95)), 3)
            if len(finite_pfs) > 0 else None,
        'n_trades': len(trades),
        'block_size': block_size,
    }


def block_bootstrap_mean_pnl(trades, block_size=BLOCK_BOOTSTRAP_SIZE,
                             n_iter=N_BOOTSTRAP, seed=42):
    """Estimate a block-bootstrap interval for mean PnL per trade."""
    if len(trades) < max(20, block_size * 2):
        return {'mean_pnl_median': None, 'mean_pnl_p05': None,
                'mean_pnl_p95': None, 'n_trades': len(trades),
                'block_size': block_size}
    rng = np.random.RandomState(seed)
    means = []
    n_blocks = max(1, len(trades) // block_size)
    for _ in range(n_iter):
        block_idx = rng.randint(0, len(trades) - block_size, size=n_blocks)
        sample = []
        for bi in block_idx:
            sample.extend(trades[bi:bi + block_size])
        if sample:
            means.append(np.mean([t['pnl_val'] for t in sample]))
    means = np.array(means)
    finite_means = means[np.isfinite(means)]
    return {
        'mean_pnl_median': round(float(np.median(finite_means)), 4)
            if len(finite_means) > 0 else None,
        'mean_pnl_p05': round(float(np.percentile(finite_means, 5)), 4)
            if len(finite_means) > 0 else None,
        'mean_pnl_p95': round(float(np.percentile(finite_means, 95)), 4)
            if len(finite_means) > 0 else None,
        'n_trades': len(trades),
        'block_size': block_size,
    }


def summarize_trade_category(trades, n_candidates, n_eligible,
                             baseline_total_pnl=None,
                             block_size=BLOCK_BOOTSTRAP_SIZE,
                             n_bootstrap=N_BOOTSTRAP):
    """Summarize a diagnostic category with PnL, yearly and exit metrics."""
    n_candidates = int(n_candidates)
    pct = n_candidates / n_eligible * 100 if n_eligible else 0.0
    total_pnl = sum(t['pnl_val'] for t in trades)
    metrics = compute_trade_metrics(trades)
    exits = Counter(t.get('exit') for t in trades)
    out = {
        'n_candidates': n_candidates,
        'pct_of_eligible': round(float(pct), 2),
        'n_trades': len(trades),
        'pf': metrics.get('pf'),
        'gross_profit': metrics.get('gross_profit', 0.0),
        'gross_loss': metrics.get('gross_loss', 0.0),
        'total_pnl': round(float(total_pnl), 3),
        'mean_pnl': round(float(total_pnl / len(trades)), 4)
            if trades else 0.0,
        'yearly_pf': {
            str(k): v['pf'] for k, v in metrics.get('yearly', {}).items()
        },
        'yearly_n': {
            str(k): v['n'] for k, v in metrics.get('yearly', {}).items()
        },
        'tp_n': exits.get('TP', 0),
        'sl_n': exits.get('SL', 0),
        'timeout_n': exits.get('TIMEOUT', 0),
        'bootstrap_mean_pnl': block_bootstrap_mean_pnl(
            trades, block_size=block_size, n_iter=n_bootstrap),
    }
    if baseline_total_pnl is not None:
        out['delta_vs_baseline_total_pnl'] = round(
            float(total_pnl - baseline_total_pnl), 3)
    return out


# ===========================================================================
# Profit concentration
# ===========================================================================

def profit_concentration(yearly_or_trades):
    """Check if a single year dominates gross profit. Accepts yearly dict or trades list."""
    if isinstance(yearly_or_trades, dict):
        gross_by_year = {}
        for yr, d in yearly_or_trades.items():
            gross_by_year[str(yr)] = d.get('gross_profit', 0)
    elif isinstance(yearly_or_trades, list):
        yearly_metrics = compute_yearly_metrics(yearly_or_trades)
        gross_by_year = {}
        for yr, d in yearly_metrics.items():
            gross_by_year[str(yr)] = d.get('gross_profit', 0)
    else:
        return {'max_year_profit_share': 0.0, 'max_year': None,
                'profit_concentration_warning': False}

    total = sum(gross_by_year.values())
    if total <= 0:
        return {'max_year_profit_share': 0.0, 'max_year': None,
                'profit_concentration_warning': False}
    max_yr = max(gross_by_year, key=gross_by_year.get)
    max_share = gross_by_year[max_yr] / total
    return {
        'max_year_profit_share': round(_safe(max_share), 3),
        'max_year': int(max_yr) if max_yr else None,
        'profit_concentration_warning': max_share > 0.6,
    }


# ===========================================================================
# Bucket helpers
# ===========================================================================

def _bucket_metrics(trades, yearly_pf_calc=None):
    """Compute standard bucket metrics for a subset of trades."""
    n = len(trades)
    if n == 0:
        return {
            'n': 0, 'pf': None, 'bs_p05': None, 'trades_per_year': None,
            'yearly_pf': {}, 'tp_pct': None, 'sl_pct': None, 'timeout_pct': None,
        }

    m = compute_trade_metrics(trades)
    bs = block_bootstrap_pf(trades)
    exits = Counter(t['exit'] for t in trades)

    result = {
        'n': n,
        'pf': m['pf'],
        'bs_p05': bs.get('pf_p05'),
        'trades_per_year': m['trades_per_year'],
        'yearly_pf': {str(k): v['pf'] for k, v in m['yearly'].items()},
        'tp_pct': round(exits.get('TP', 0) / n * 100, 1) if n else 0,
        'sl_pct': round(exits.get('SL', 0) / n * 100, 1) if n else 0,
        'timeout_pct': round(exits.get('TIMEOUT', 0) / n * 100, 1) if n else 0,
    }
    return result


def _bucket_metrics_breach(trades):
    """Extended bucket metrics for breach analysis."""
    n = len(trades)
    if n == 0:
        return {'n': 0}

    m = compute_trade_metrics(trades)
    bs = block_bootstrap_pf(trades)
    exits = Counter(t['exit'] for t in trades)
    breach_rates = [t.get('breach_flag_true', 0) for t in trades]
    pred_favs = [t.get('pred_fav', np.nan) for t in trades
                 if 'pred_fav' in t and not np.isnan(t.get('pred_fav', np.nan))]
    stop_vals = [t.get('stop_val', np.nan) for t in trades
                 if not np.isnan(t.get('stop_val', np.nan))]
    actual_rrs = [t.get('actual_rr', np.nan) for t in trades
                  if 'actual_rr' in t and not np.isnan(t.get('actual_rr', np.nan))]

    return {
        'n': n,
        'pf': m['pf'],
        'bs_p05': bs.get('pf_p05'),
        'trades_per_year': m['trades_per_year'],
        'yearly_pf': {str(k): v['pf'] for k, v in m['yearly'].items()},
        'breach_flag_true_rate': round(np.mean(breach_rates), 4)
            if breach_rates else None,
        'tp_pct': round(exits.get('TP', 0) / n * 100, 1) if n else 0,
        'sl_pct': round(exits.get('SL', 0) / n * 100, 1) if n else 0,
        'timeout_pct': round(exits.get('TIMEOUT', 0) / n * 100, 1) if n else 0,
        'avg_pred_fav': round(float(np.mean(pred_favs)), 4) if pred_favs else None,
        'avg_stop_val': round(float(np.mean(stop_vals)), 4) if stop_vals else None,
        'avg_actual_rr': round(float(np.mean(actual_rrs)), 4) if actual_rrs else None,
    }


def _bucket_metrics_fav(trades):
    """Extended bucket metrics for fav analysis."""
    n = len(trades)
    if n == 0:
        return {'n': 0}

    m = compute_trade_metrics(trades)
    bs = block_bootstrap_pf(trades)
    exits = Counter(t['exit'] for t in trades)
    fav_preds = np.array([t.get('pred_fav', np.nan) for t in trades])
    fav_trues = np.array([t.get('fav_val_true', np.nan) for t in trades])
    valid = ~np.isnan(fav_preds) & ~np.isnan(fav_trues)
    actual_rrs = [t.get('actual_rr', np.nan) for t in trades
                  if 'actual_rr' in t and not np.isnan(t.get('actual_rr', np.nan))]

    return {
        'n': n,
        'pf': m['pf'],
        'bs_p05': bs.get('pf_p05'),
        'trades_per_year': m['trades_per_year'],
        'yearly_pf': {str(k): v['pf'] for k, v in m['yearly'].items()},
        'mean_true_fav': round(float(np.mean(fav_trues[valid])), 4)
            if valid.sum() > 0 else None,
        'mean_pred_fav': round(float(np.mean(fav_preds[valid])), 4)
            if valid.sum() > 0 else None,
        'mean_fav_error': round(float(np.mean(fav_preds[valid] - fav_trues[valid])), 4)
            if valid.sum() > 0 else None,
        'tp_pct': round(exits.get('TP', 0) / n * 100, 1) if n else 0,
        'sl_pct': round(exits.get('SL', 0) / n * 100, 1) if n else 0,
        'timeout_pct': round(exits.get('TIMEOUT', 0) / n * 100, 1) if n else 0,
        'actual_rr_mean': round(float(np.mean(actual_rrs)), 4) if actual_rrs else None,
    }


# ===========================================================================
# Main diagnostic runner
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description='Stage 4.3 DIAGNOSTIC_ONLY')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--ohlc', default='DATA/XAUUSD_H1_OHLC.csv')
    parser.add_argument('--output', default='ML/reports/stage4_3_diagnostics.json')
    parser.add_argument('--spread', type=float, default=CANONICAL_SPREAD)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--n-bootstrap', type=int, default=N_BOOTSTRAP)
    args = parser.parse_args()

    print('=' * 70)
    print('Stage 4.3: DIAGNOSTIC_ONLY — Oracle → Stage 4.2 PF decomposition')
    print('=' * 70)
    print(f'  Target: {WINNER_TARGET}')
    print(f'  Fixed params: p={WINNER_P}, mf={WINNER_MIN_FAV}, '
          f'rr={WINNER_MIN_RR}, tf={WINNER_TP_FRACTION}')
    print(f'  Spread={args.spread} (OHLC=Bid)  seed={args.seed}')
    print()

    # ---- Data ----
    print('Loading data...')
    train_df, val_stop_df, val_eval_df = load_splits(args.train, args.val)
    print(f'  Train (<=2016): {len(train_df)}')
    print(f'  Val-stop (2017-2018): {len(val_stop_df)}')
    print(f'  Val-eval (>=2019): {len(val_eval_df)}')

    ohlc, times, time_idx = load_ohlc_index(args.ohlc)
    entry_prices_val = compute_entry_prices(val_eval_df, ohlc, times, time_idx)

    # ---- Features ----
    X_train_breach, _ = profile_base_raw_plus_time(train_df)
    X_val_stop_breach, _ = profile_base_raw_plus_time(val_stop_df)
    X_val_eval_breach, _ = profile_base_raw_plus_time(val_eval_df)
    X_train_fav, _ = profile_base_raw(train_df)
    X_val_eval_fav, _ = profile_base_raw(val_eval_df)

    h, off, side = WINNER_H, WINNER_OFF, WINNER_SIDE
    target_col = BREACH_TARGETS[h][off][side]
    fav_col = FAV_TARGETS[h][side]

    # ---- Train models ----
    y_train_b = train_df[target_col].values
    y_stop_b = val_stop_df[target_col].values
    y_eval_b = val_eval_df[target_col].values
    train_mask_b = ~np.isnan(y_train_b)
    stop_mask_b = ~np.isnan(y_stop_b)
    eval_mask_b = ~np.isnan(y_eval_b)

    print(f'\nTraining XGBoost breach...')
    breach_model = train_xgb_breach(
        X_train_breach[train_mask_b], y_train_b[train_mask_b],
        X_val_stop_breach[stop_mask_b], y_stop_b[stop_mask_b],
        random_state=args.seed)
    breach_proba = breach_model.predict_proba(X_val_eval_breach[eval_mask_b])[:, 1]
    breach_auc = roc_auc_score(y_eval_b[eval_mask_b], breach_proba)
    print(f'  Breach AUC val_eval: {breach_auc:.4f}  '
          f'iters={getattr(breach_model, "best_iteration", "?")}')

    y_train_f = train_df[fav_col].values
    y_eval_f = val_eval_df[fav_col].values
    train_mask_f = ~np.isnan(y_train_f)
    eval_mask_f = ~np.isnan(y_eval_f)

    print(f'Training RF fav...')
    fav_model = train_rf_fav(X_train_fav[train_mask_f], y_train_f[train_mask_f],
                             random_state=args.seed)
    fav_pred = fav_model.predict(X_val_eval_fav[eval_mask_f])

    # ---- Align ----
    intersection_mask = eval_mask_b & eval_mask_f
    n_valid = intersection_mask.sum()
    print(f'  Intersection valid: {n_valid}')

    breach_proba_aligned = breach_model.predict_proba(
        X_val_eval_breach[intersection_mask])[:, 1]
    fav_pred_aligned = fav_model.predict(X_val_eval_fav[intersection_mask])
    val_masked = val_eval_df[intersection_mask].reset_index(drop=True)
    entry_masked = entry_prices_val[intersection_mask]

    y_breach_true = y_eval_b[intersection_mask]
    y_fav_true = y_eval_f[intersection_mask]

    sim_kwargs_base = dict(
        ohlc=ohlc, times=times, time_idx=time_idx,
        side=side, h=h, stop_offset=off,
        p=WINNER_P, min_fav_val=WINNER_MIN_FAV,
        min_rr=WINNER_MIN_RR, tp_fraction=WINNER_TP_FRACTION,
        cap=CAP, spread=args.spread,
    )

    # =====================================================================
    # 1. Baseline trade simulation with full details
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('BASELINE — Stage 4.2 winner reproduction')
    print(f'{"=" * 70}')

    sim_kwargs = dict(
        sim_kwargs_base,
        df=val_masked, entry_prices=entry_masked,
        breach_proba=breach_proba_aligned, fav_pred=fav_pred_aligned,
        return_details=True,
    )
    baseline_trades = simulate_trades(**sim_kwargs)
    baseline_m = compute_trade_metrics(baseline_trades)
    baseline_bs = block_bootstrap_pf(baseline_trades)

    print(f'  PF={baseline_m["pf"]}  trades={baseline_m["n_trades"]}  '
          f't/yr={baseline_m["trades_per_year"]}')
    print(f'  BS: median={baseline_bs.get("pf_median")}  '
          f'p05={baseline_bs.get("pf_p05")}  p95={baseline_bs.get("pf_p95")}')
    print(f'  GP={baseline_m["gross_profit"]}  GL={baseline_m["gross_loss"]}')
    print(f'  Win rate={baseline_m["win_rate"]}%')
    print(f'  TP={baseline_m["tp_n"]}  SL={baseline_m["sl_n"]}  '
          f'TIMEOUT={baseline_m["timeout_n"]}  Ambiguous={baseline_m["ambiguous_n"]}')
    for yr_str, yd in sorted(baseline_m['yearly'].items()):
        print(f'    {yr_str}: PF={yd["pf"]}  n={yd["n"]}')

    # =====================================================================
    # 2. Loss attribution
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('LOSS ATTRIBUTION')
    print(f'{"=" * 70}')

    la = loss_attribution(baseline_trades)
    for exit_type in ('TP', 'SL', 'TIMEOUT'):
        e = la[exit_type]
        print(f'  {exit_type}: n={e["n"]}  total_pnl={e["total_pnl"]}  '
              f'mean_pnl={e["mean_pnl"]}  pct_gl={e["pct_of_total_gross_loss"]}')
        if exit_type == 'SL':
            print(f'    ambiguous_sl={e["ambiguous_sl"]}  '
                  f'breach_flag_true_rate={e["breach_flag_true_rate"]}')

    yearly_la = yearly_loss_attribution(baseline_trades)
    print(f'  Yearly LA computed for {len(yearly_la)} years')

    # =====================================================================
    # 3. Breach buckets
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('BREACH BUCKETS')
    print(f'{"=" * 70}')

    breach_ranges = [
        (0.00, 0.10), (0.10, 0.20), (0.20, 0.30), (0.30, 0.40),
    ]
    breach_buckets = []
    for lo, hi in breach_ranges:
        bucket_trades = [t for t in baseline_trades
                         if lo <= t.get('pred_break', 0) < hi]
        bm = _bucket_metrics_breach(bucket_trades)
        bm['range'] = f'[{lo:.2f}, {hi:.2f})'
        if bm.get('n', 0) > 0 and bm['n'] < 30:
            bm['low_n'] = True
        breach_buckets.append(bm)
        if bm.get('n', 0) > 0:
            print(f'  [{lo:.2f}, {hi:.2f}): n={bm["n"]}  PF={bm.get("pf")}  '
                  f'breach_rate={bm.get("breach_flag_true_rate")}')
        else:
            print(f'  [{lo:.2f}, {hi:.2f}): n=0 (empty)')

    # =====================================================================
    # 4. Fav buckets by pred_fav (quantile)
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('FAV BUCKETS by pred_fav (quantile)')
    print(f'{"=" * 70}')

    pred_favs = np.array([t.get('pred_fav', 0) for t in baseline_trades])
    quantile_edges = np.percentile(pred_favs, [0, 20, 40, 60, 80, 100])
    quantile_labels = ['q0-q20', 'q20-q40', 'q40-q60', 'q60-q80', 'q80-q100']

    fav_buckets_pred_fav = []
    for i in range(len(quantile_edges) - 1):
        lo, hi = quantile_edges[i], quantile_edges[i + 1]
        if i == len(quantile_edges) - 2:
            hi += 1e-9
        bucket_trades = [t for t in baseline_trades
                         if lo <= t.get('pred_fav', 0) < hi]
        bm = _bucket_metrics_fav(bucket_trades)
        bm['range'] = f'{quantile_labels[i]} ({lo:.2f}-{hi:.2f})'
        fav_buckets_pred_fav.append(bm)
        print(f'  {bm["range"]}: n={bm["n"]}  PF={bm.get("pf")}  '
              f'fav_err={bm.get("mean_fav_error")}')

    # =====================================================================
    # 5. Fav buckets by pred_fav / stop_val (fixed)
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('FAV BUCKETS by pred_fav / stop_val (fixed)')
    print(f'{"=" * 70}')

    fs_ranges = [
        (1.0, 1.3, '[1.0, 1.3)'),
        (1.3, 1.5, '[1.3, 1.5)'),
        (1.5, 2.0, '[1.5, 2.0)'),
        (2.0, 3.0, '[2.0, 3.0)'),
        (3.0, float('inf'), '[3.0, +inf)'),
    ]
    fav_buckets_over_stop = []
    for lo, hi, label in fs_ranges:
        bucket_trades = [t for t in baseline_trades
                         if lo <= (t.get('pred_fav', 0) / max(t.get('stop_val', 1), 0.01)) < hi]
        bm = _bucket_metrics_fav(bucket_trades)
        bm['range'] = label
        fav_buckets_over_stop.append(bm)
        print(f'  {label}: n={bm["n"]}  PF={bm.get("pf")}  '
              f'fav_err={bm.get("mean_fav_error")}')

    # Fav monotonicity
    fav_trues_arr = np.array([t.get('fav_val_true', np.nan) for t in baseline_trades])
    pred_favs_arr = np.array([t.get('pred_fav', np.nan) for t in baseline_trades])
    stop_vals_arr = np.array([t.get('stop_val', np.nan) for t in baseline_trades])
    pnl_vals_arr = np.array([t.get('pnl_val', np.nan) for t in baseline_trades])

    valid_mask = ~np.isnan(pred_favs_arr) & ~np.isnan(fav_trues_arr)
    fs_ratio = pred_favs_arr / np.maximum(stop_vals_arr, 0.01)

    sp1 = spearmanr(pred_favs_arr[valid_mask], fav_trues_arr[valid_mask])
    sp2 = spearmanr(fs_ratio[valid_mask], pnl_vals_arr[valid_mask])

    fav_mono = {
        'spearman_pred_fav_vs_true_fav': round(float(sp1.correlation), 3),
        'spearman_pred_fav_over_stop_vs_pnl': round(float(sp2.correlation), 3),
    }
    print(f'\n  Spearman(pred_fav, true_fav)={fav_mono["spearman_pred_fav_vs_true_fav"]}')
    print(f'  Spearman(pred_fav/stop, pnl)={fav_mono["spearman_pred_fav_over_stop_vs_pnl"]}')

    # =====================================================================
    # 6. 2D map (cumulative)
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('2D MAP: predict_break × pred_fav/stop_val (cumulative)')
    print(f'{"=" * 70}')

    pb_thresholds = [0.15, 0.20, 0.25, 0.30, 0.40]
    fs_thresholds = [0.7, 1.0, 1.3, 1.5, 2.0]

    cells_2d = {}
    for pb_t in pb_thresholds:
        for fs_t in fs_thresholds:
            key = f'pb_lt_{pb_t}_fs_ge_{fs_t}'
            cell_trades = [t for t in baseline_trades
                           if t.get('pred_break', 0) < pb_t
                           and (t.get('pred_fav', 0) / max(t.get('stop_val', 1), 0.01)) >= fs_t]
            n_cell = len(cell_trades)
            if n_cell == 0:
                cells_2d[key] = {
                    'n': 0, 'threshold_pb': pb_t, 'threshold_fs': fs_t,
                }
                continue

            cm = compute_trade_metrics(cell_trades)
            bs = block_bootstrap_pf(cell_trades)
            exits = Counter(t['exit'] for t in cell_trades)
            breach_rates = [t.get('breach_flag_true', 0) for t in cell_trades]
            actual_rrs = [t.get('actual_rr', np.nan) for t in cell_trades
                          if 'actual_rr' in t and not np.isnan(t.get('actual_rr', np.nan))]
            conc = profit_concentration(cell_trades)
            yearly_data = compute_yearly_metrics(cell_trades)

            cell_pf = cm['pf']
            is_hypothesis = (
                isinstance(cell_pf, (int, float)) and cell_pf > 1.15
                and bs.get('pf_p05') is not None and bs['pf_p05'] >= 1.0
                and n_cell >= 30
                and not conc['profit_concentration_warning']
            )

            cells_2d[key] = {
                'threshold_pb': pb_t,
                'threshold_fs': fs_t,
                'n': n_cell,
                'pf': cell_pf,
                'bs_p05': bs.get('pf_p05'),
                'trades_per_year': cm['trades_per_year'],
                'yearly_pf': {str(k): v['pf'] for k, v in yearly_data.items()},
                'tp_n': exits.get('TP', 0),
                'sl_n': exits.get('SL', 0),
                'timeout_n': exits.get('TIMEOUT', 0),
                'actual_breach_rate': round(float(np.mean(breach_rates)), 4)
                    if breach_rates else None,
                'avg_actual_rr': round(float(np.mean(actual_rrs)), 4)
                    if actual_rrs else None,
                'max_year_profit_share': conc['max_year_profit_share'],
                'profit_concentration_warning': conc['profit_concentration_warning'],
                'hypothesis_candidate': is_hypothesis,
            }
            status = 'HYPOTHESIS' if is_hypothesis else ''
            print(f'  pb<{pb_t} fs>={fs_t}: n={n_cell}  PF={cell_pf}  {status}')

    # =====================================================================
    # 7. Actual RR diagnostics
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('ACTUAL RR DIAGNOSTICS')
    print(f'{"=" * 70}')

    actual_rrs_all = np.array([t.get('actual_rr', np.nan) for t in baseline_trades])
    actual_rrs_valid = actual_rrs_all[~np.isnan(actual_rrs_all)]
    avg_win_r_val = np.mean([t['pnl_r'] for t in baseline_trades if t['pnl_r'] > 0]) \
        if any(t['pnl_r'] > 0 for t in baseline_trades) else 0
    avg_loss_r_val = np.mean([abs(t['pnl_r']) for t in baseline_trades if t['pnl_r'] < 0]) \
        if any(t['pnl_r'] < 0 for t in baseline_trades) else 0
    req_win_rate = avg_loss_r_val / (avg_win_r_val + avg_loss_r_val) * 100 \
        if (avg_win_r_val + avg_loss_r_val) > 0 else 0

    rr_diag = {
        'mean_rr': round(float(np.mean(actual_rrs_valid)), 4),
        'median_rr': round(float(np.median(actual_rrs_valid)), 4),
        'p05_rr': round(float(np.percentile(actual_rrs_valid, 5)), 4),
        'p95_rr': round(float(np.percentile(actual_rrs_valid, 95)), 4),
        'avg_win_r': round(float(avg_win_r_val), 3),
        'avg_loss_r': round(float(avg_loss_r_val), 3),
        'required_win_rate_for_pf1': round(float(req_win_rate), 1),
    }

    print(f'  Mean RR={rr_diag["mean_rr"]}  Median={rr_diag["median_rr"]}  '
          f'p05={rr_diag["p05_rr"]}  p95={rr_diag["p95_rr"]}')
    print(f'  Avg win={rr_diag["avg_win_r"]}R  Avg loss={rr_diag["avg_loss_r"]}R  '
          f'Req WR={rr_diag["required_win_rate_for_pf1"]}%')

    # RR buckets
    rr_bucket_ranges = [
        (0.0, 0.4, '[0.0R, 0.4R)'),
        (0.4, 0.6, '[0.4R, 0.6R)'),
        (0.6, 0.8, '[0.6R, 0.8R)'),
        (0.8, 1.0, '[0.8R, 1.0R)'),
        (1.0, float('inf'), '[1.0R, +infR)'),
    ]
    rr_buckets = []
    for lo, hi, label in rr_bucket_ranges:
        bucket_trades = [t for t in baseline_trades
                         if lo <= t.get('actual_rr', 0) < hi]
        n_b = len(bucket_trades)
        if n_b == 0:
            rr_buckets.append({'range': label, 'n': 0})
            continue
        m = compute_trade_metrics(bucket_trades)
        wins_avg = np.mean([t['pnl_val'] for t in bucket_trades if t['pnl_val'] > 0]) \
            if any(t['pnl_val'] > 0 for t in bucket_trades) else 0
        losses_avg = np.mean([abs(t['pnl_val']) for t in bucket_trades if t['pnl_val'] < 0]) \
            if any(t['pnl_val'] < 0 for t in bucket_trades) else 0
        rr_buckets.append({
            'range': label, 'n': n_b, 'pf': m['pf'],
            'win_rate': round(float(sum(1 for t in bucket_trades if t['pnl_val'] > 0) / n_b * 100), 1),
            'avg_win_atr': round(float(wins_avg), 3),
            'avg_loss_atr': round(float(losses_avg), 3),
        })
        print(f'  {label}: n={n_b}  PF={m["pf"]}')

    rr_diag['rr_buckets'] = rr_buckets

    # =====================================================================
    # 8. TP policy comparison
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('TP POLICY COMPARISON (DIAGNOSTIC_ONLY)')
    print(f'{"=" * 70}')

    tp_policies = [
        # (name, policy, value, skip_min_fav, skip_min_rr)
        ('current_fav_fraction_0.4', 'fav_fraction', 0.4, False, False),
        ('fixed_atr_0.3', 'fixed_atr', 0.3, False, False),
        ('fixed_atr_0.5', 'fixed_atr', 0.5, False, False),
        ('fixed_atr_0.7', 'fixed_atr', 0.7, False, False),
        ('fixed_atr_1.0', 'fixed_atr', 1.0, False, False),
        ('fixed_r_0.3', 'fixed_r', 0.3, False, False),
        ('fixed_r_0.5', 'fixed_r', 0.5, False, False),
        ('fixed_r_0.7', 'fixed_r', 0.7, False, False),
        ('fixed_r_1.0', 'fixed_r', 1.0, False, False),
        ('fixed_r_1.5', 'fixed_r', 1.5, False, False),
        ('fixed_r_2.0', 'fixed_r', 2.0, False, False),
        ('breach_only_fixed_r_0.5', 'fixed_r', 0.5, True, True),
        ('breach_only_fixed_r_1.0', 'fixed_r', 1.0, True, True),
        ('breach_fav_filter_fixed_r_0.5', 'fixed_r', 0.5, False, False),
        ('breach_fav_filter_fixed_r_1.0', 'fixed_r', 1.0, False, False),
    ]

    tp_results = []
    for pol_name, pol_type, pol_val, skip_mf, skip_rr in tp_policies:
        pol_kwargs = dict(
            sim_kwargs_base,
            df=val_masked, entry_prices=entry_masked,
            breach_proba=breach_proba_aligned, fav_pred=fav_pred_aligned,
            return_details=False,
            tp_policy=pol_type, tp_policy_value=pol_val,
            skip_min_fav=skip_mf, skip_min_rr=skip_rr,
        )
        pol_trades = simulate_trades(**pol_kwargs)
        pol_m = compute_trade_metrics(pol_trades)
        pol_bs = block_bootstrap_pf(pol_trades)
        exits = Counter(t['exit'] for t in pol_trades)

        pol_avg_win_atr = np.mean([t['pnl_val'] for t in pol_trades if t['pnl_val'] > 0]) \
            if any(t['pnl_val'] > 0 for t in pol_trades) else 0
        pol_avg_loss_atr = np.mean([abs(t['pnl_val']) for t in pol_trades if t['pnl_val'] < 0]) \
            if any(t['pnl_val'] < 0 for t in pol_trades) else 0
        pol_avg_win_r = np.mean([t['pnl_r'] for t in pol_trades if t['pnl_r'] > 0]) \
            if any(t['pnl_r'] > 0 for t in pol_trades) else 0
        pol_avg_loss_r = np.mean([abs(t['pnl_r']) for t in pol_trades if t['pnl_r'] < 0]) \
            if any(t['pnl_r'] < 0 for t in pol_trades) else 0

        entry = {
            'policy_name': pol_name,
            'tp_policy': pol_type,
            'value': pol_val,
            'skip_min_fav': skip_mf,
            'skip_min_rr': skip_rr,
            'n': pol_m['n_trades'],
            'pf': pol_m['pf'],
            'bs_p05': pol_bs.get('pf_p05'),
            'yearly_pf': {str(k): v['pf'] for k, v in pol_m['yearly'].items()},
            'trades_per_year': pol_m['trades_per_year'],
            'tp_n': exits.get('TP', 0),
            'sl_n': exits.get('SL', 0),
            'timeout_n': exits.get('TIMEOUT', 0),
            'avg_win_atr': round(float(pol_avg_win_atr), 3),
            'avg_loss_atr': round(float(pol_avg_loss_atr), 3),
            'avg_win_r': round(float(pol_avg_win_r), 3),
            'avg_loss_r': round(float(pol_avg_loss_r), 3),
        }
        tp_results.append(entry)
        print(f'  {pol_name:>35s}: n={entry["n"]}  PF={entry["pf"]}  '
              f'BS_p05={entry["bs_p05"]}')

    # =====================================================================
    # 9. Oracle deviation attribution
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('ORACLE DEVIATION ATTRIBUTION')
    print(f'{"=" * 70}')

    # --- Build eligible universe ---
    # Rows that pass basic trade executability but before model filters
    eligible_mask = np.ones(len(val_masked), dtype=bool)
    for i, (idx, row) in enumerate(val_masked.iterrows()):
        row_dt = None
        try:
            row_dt = datetime.strptime(str(row['time']), '%Y.%m.%d %H:%M') \
                .replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            eligible_mask[i] = False
            continue
        idx0 = time_idx.get(row_dt)
        if idx0 is None or idx0 + h >= len(times):
            eligible_mask[i] = False
            continue
        entry_p = entry_masked[i]
        if np.isnan(entry_p):
            eligible_mask[i] = False
            continue
        atr_v = float(row.get('ATR', np.nan))
        if np.isnan(atr_v) or atr_v <= 0:
            eligible_mask[i] = False
            continue
        fractal0 = parse_trade_fractal0(row.get('fractal0'))
        if fractal0 is None or fractal0['direction'] != (-1 if side == 'buy' else 1):
            eligible_mask[i] = False
            continue
        if np.isnan(breach_proba_aligned[i]) or np.isnan(fav_pred_aligned[i]):
            eligible_mask[i] = False
            continue
        yb = y_breach_true[i]
        yf = y_fav_true[i]
        if np.isnan(yb) or np.isnan(yf):
            eligible_mask[i] = False
            continue

    n_eligible = eligible_mask.sum()
    print(f'  Eligible universe: {n_eligible} rows')
    eligible_val = val_masked[eligible_mask].reset_index(drop=True)
    eligible_val['_candidate_id'] = np.arange(len(eligible_val), dtype=int)
    eligible_entry = entry_masked[eligible_mask]
    eligible_breach = breach_proba_aligned[eligible_mask]
    eligible_fav = fav_pred_aligned[eligible_mask]
    eligible_yb = y_breach_true[eligible_mask]
    eligible_yf = y_fav_true[eligible_mask]

    # --- 4 model/oracle regimes ---
    regimes = {}

    # model_breach_model_fav
    regime_trades = simulate_trades(
        df=eligible_val, entry_prices=eligible_entry,
        breach_proba=eligible_breach, fav_pred=eligible_fav,
        return_details=False, **sim_kwargs_base)
    regimes['model_breach_model_fav'] = compute_trade_metrics(regime_trades)
    regimes['model_breach_model_fav']['bs_p05'] = \
        block_bootstrap_pf(regime_trades).get('pf_p05')

    # oracle_breach_model_fav
    regime_trades = simulate_trades(
        df=eligible_val, entry_prices=eligible_entry,
        breach_proba=eligible_yb.astype(float), fav_pred=eligible_fav,
        return_details=False, **sim_kwargs_base)
    regimes['oracle_breach_model_fav'] = compute_trade_metrics(regime_trades)
    regimes['oracle_breach_model_fav']['bs_p05'] = \
        block_bootstrap_pf(regime_trades).get('pf_p05')

    # model_breach_oracle_fav
    regime_trades = simulate_trades(
        df=eligible_val, entry_prices=eligible_entry,
        breach_proba=eligible_breach, fav_pred=eligible_yf.copy(),
        return_details=False, **sim_kwargs_base)
    regimes['model_breach_oracle_fav'] = compute_trade_metrics(regime_trades)
    regimes['model_breach_oracle_fav']['bs_p05'] = \
        block_bootstrap_pf(regime_trades).get('pf_p05')

    # oracle_breach_oracle_fav
    regime_trades = simulate_trades(
        df=eligible_val, entry_prices=eligible_entry,
        breach_proba=eligible_yb.astype(float), fav_pred=eligible_yf.copy(),
        return_details=False, **sim_kwargs_base)
    regimes['oracle_breach_oracle_fav'] = compute_trade_metrics(regime_trades)
    regimes['oracle_breach_oracle_fav']['bs_p05'] = \
        block_bootstrap_pf(regime_trades).get('pf_p05')

    for name, rm in regimes.items():
        print(f'  {name}: PF={rm["pf"]}  n={rm["n_trades"]}  '
              f'BS_p05={rm.get("bs_p05")}')

    baseline_total_pnl = baseline_m['gross_profit'] - baseline_m['gross_loss']

    def forced_candidate_trades(mask, fav_values, basis):
        """Force-evaluate candidates with fixed breach pass and supplied fav values."""
        mask = np.asarray(mask, dtype=bool)
        n_mask = int(mask.sum())
        if n_mask == 0:
            return []
        force_kwargs = dict(sim_kwargs_base)
        force_kwargs.update({
            'df': eligible_val[mask].reset_index(drop=True),
            'entry_prices': eligible_entry[mask],
            'breach_proba': np.zeros(n_mask, dtype=float),
            'fav_pred': fav_values[mask],
            'return_details': True,
            'p': 1.1,
            'min_fav_val': 0.0,
            'min_rr': 0.0,
            'tp_policy': 'fav_fraction',
            'tp_policy_value': WINNER_TP_FRACTION,
            'skip_min_fav': True,
            'skip_min_rr': True,
        })
        trades_forced = simulate_trades(**force_kwargs)
        for t in trades_forced:
            t['forced_basis'] = basis
        return trades_forced

    # --- Breach entry error categories ---
    model_breach_allows = eligible_breach < WINNER_P
    oracle_breach_ok = eligible_yb == 0
    oracle_breach_blocks = eligible_yb == 1

    entered_both = model_breach_allows & oracle_breach_ok
    entered_model_oracle_blocks = model_breach_allows & oracle_breach_blocks
    missed_model_oracle_allows = (~model_breach_allows) & oracle_breach_ok
    blocked_both = (~model_breach_allows) & oracle_breach_blocks

    breach_masks = {
        'entered_model_and_oracle': entered_both,
        'entered_model_but_oracle_breach_blocks': entered_model_oracle_blocks,
        'missed_by_model_but_oracle_breach_allows': missed_model_oracle_allows,
        'blocked_by_both': blocked_both,
    }
    breach_entry_categories = {}
    for cat, mask in breach_masks.items():
        forced = forced_candidate_trades(
            mask, eligible_fav, 'forced_entry_model_fav_tp')
        entry = summarize_trade_category(
            forced, int(mask.sum()), n_eligible,
            baseline_total_pnl=baseline_total_pnl,
            block_size=BLOCK_BOOTSTRAP_SIZE,
            n_bootstrap=args.n_bootstrap,
        )
        entry['n'] = entry['n_candidates']
        entry['forced_trade_basis'] = 'model_fav_tp_forced_entry'
        breach_entry_categories[cat] = entry

    print(f'\n  Breach entry error categories:')
    for cat, cd in breach_entry_categories.items():
        print(f'    {cat}: n={cd["n"]} ({cd["pct_of_eligible"]}%)  '
              f'forced_pnl={cd["total_pnl"]}')

    # --- Fav error categories (only where model or oracle breach allows entry) ---
    fav_scope = model_breach_allows | oracle_breach_ok
    n_fav_scope = int(fav_scope.sum())
    fav_error = eligible_fav - eligible_yf
    tp_error = eligible_fav * WINNER_TP_FRACTION - eligible_yf * WINNER_TP_FRACTION
    stop_vals_eligible = np.full(len(eligible_val), np.nan)
    for i in range(len(eligible_val)):
        stop_vals_eligible[i] = abs(
            eligible_entry[i] - min(
                parse_trade_fractal0(eligible_val.iloc[i].get('fractal0')).get('price', eligible_entry[i]),
                eligible_entry[i])) / max(float(eligible_val.iloc[i].get('ATR', 1)), 0.01)

    model_fav_passes_rr = (eligible_fav / np.maximum(stop_vals_eligible, 0.01)) >= WINNER_MIN_RR
    oracle_fav_passes_rr = (eligible_yf / np.maximum(stop_vals_eligible, 0.01)) >= WINNER_MIN_RR
    model_fav_passes_mf = eligible_fav >= WINNER_MIN_FAV
    oracle_fav_passes_mf = eligible_yf >= WINNER_MIN_FAV

    fav_overpredict = fav_error > 0.2
    fav_underpredict = fav_error < -0.2
    fav_near = np.abs(fav_error) <= 0.2
    fav_false_accept = model_fav_passes_rr & model_fav_passes_mf & \
        (~oracle_fav_passes_rr | ~oracle_fav_passes_mf)
    fav_false_reject = (~model_fav_passes_rr | ~model_fav_passes_mf) & \
        oracle_fav_passes_rr & oracle_fav_passes_mf

    fav_masks = {
        'fav_overpredict_tp_too_far': fav_scope & fav_overpredict,
        'fav_underpredict_tp_too_close': fav_scope & fav_underpredict,
        'model_fav_false_accept': fav_scope & fav_false_accept,
        'model_fav_false_reject': fav_scope & fav_false_reject,
        'fav_near_oracle': fav_scope & fav_near,
    }
    fav_error_cats = {}
    for cat, mask in fav_masks.items():
        model_forced = forced_candidate_trades(
            mask, eligible_fav, 'forced_entry_model_fav_tp')
        oracle_forced = forced_candidate_trades(
            mask, eligible_yf, 'forced_entry_oracle_fav_tp')
        entry = summarize_trade_category(
            model_forced, int(mask.sum()), n_eligible,
            baseline_total_pnl=baseline_total_pnl,
            block_size=BLOCK_BOOTSTRAP_SIZE,
            n_bootstrap=args.n_bootstrap,
        )
        entry['n'] = entry['n_candidates']
        entry['pct_of_fav_scope'] = round(
            float(mask.sum() / n_fav_scope * 100), 2) if n_fav_scope else 0.0
        entry['scope'] = (
            'model_breach_allows OR oracle_breach_allows; '
            'categories_are_not_mutually_exclusive')
        entry['mean_fav_error'] = round(float(np.mean(fav_error[mask])), 3) \
            if mask.sum() > 0 else None
        entry['median_fav_error'] = round(float(np.median(fav_error[mask])), 3) \
            if mask.sum() > 0 else None
        entry['mean_tp_error_val'] = round(float(np.mean(tp_error[mask])), 3) \
            if mask.sum() > 0 else None
        entry['median_tp_error_val'] = round(float(np.median(tp_error[mask])), 3) \
            if mask.sum() > 0 else None
        oracle_total = sum(t['pnl_val'] for t in oracle_forced)
        model_total = sum(t['pnl_val'] for t in model_forced)
        entry['oracle_fav_forced'] = summarize_trade_category(
            oracle_forced, int(mask.sum()), n_eligible,
            baseline_total_pnl=baseline_total_pnl,
            block_size=BLOCK_BOOTSTRAP_SIZE,
            n_bootstrap=args.n_bootstrap,
        )
        entry['delta_oracle_minus_model_total_pnl'] = round(
            float(oracle_total - model_total), 3)
        fav_error_cats[cat] = entry

    print(f'\n  Fav error categories:')
    for cat, cd in fav_error_cats.items():
        print(f'    {cat}: n={cd["n"]}  mean_err={cd["mean_fav_error"]}  '
              f'forced_pnl={cd["total_pnl"]}')

    # Delta summary
    pf_baseline = regimes['model_breach_model_fav']['pf']
    pf_ob_mf = regimes['oracle_breach_model_fav']['pf']
    pf_mb_of = regimes['model_breach_oracle_fav']['pf']
    pf_ob_of = regimes['oracle_breach_oracle_fav']['pf']

    largest_gap = 'pf_oracle_breach_oracle_fav'
    oracle_dev = {
        'regimes': regimes,
        'eligible_universe_n': int(n_eligible),
        'fav_error_scope_n': int(n_fav_scope),
        'breach_entry_categories_are_mutually_exclusive': True,
        'fav_error_categories_are_mutually_exclusive': False,
        'breach_entry_error_categories': breach_entry_categories,
        'fav_error_categories': fav_error_cats,
        'delta_summary': {
            'pf_baseline': pf_baseline,
            'pf_oracle_breach_model_fav': pf_ob_mf,
            'pf_model_breach_oracle_fav': pf_mb_of,
            'pf_oracle_breach_oracle_fav': pf_ob_of,
            'largest_observed_gap': largest_gap,
        },
        'status': 'DIAGNOSTIC_ONLY_oracle_labels_are_future',
    }

    print(f'\n  Delta summary:')
    print(f'    Baseline (model/model):            PF={pf_baseline}')
    print(f'    Oracle breach / model fav:         PF={pf_ob_mf}')
    print(f'    Model breach / oracle fav:         PF={pf_mb_of}')
    print(f'    Oracle breach / oracle fav:        PF={pf_ob_of}')

    # =====================================================================
    # Assemble JSON output
    # =====================================================================
    output = {
        'status': 'DIAGNOSTIC_ONLY',
        'source': 'docs/audit/2026-06-14-stage4-brainstorm_result_codex.md',
        'config': {
            'split': {
                'train': f'<={TRAIN_MAX_YEAR}',
                'val_stop': list(VAL_STOP_YEARS),
                'val_eval': f'>={VAL_EVAL_MIN_YEAR}',
            },
            'target': WINNER_TARGET,
            'h': h, 'off': off, 'side': side,
            'fixed_params': {
                'p': WINNER_P, 'min_fav_val': WINNER_MIN_FAV,
                'min_rr': WINNER_MIN_RR, 'tp_fraction': WINNER_TP_FRACTION,
                'cap': CAP,
            },
            'spread': args.spread,
            'block_bootstrap_size': BLOCK_BOOTSTRAP_SIZE,
            'n_bootstrap': args.n_bootstrap,
            'seed': args.seed,
        },
        'search_budget': {
            'breach_buckets': 4,
            'fav_buckets_pred_fav': 5,
            'fav_buckets_pred_fav_over_stop': 5,
            '2d_map_cells': '5x5 cumulative',
            'tp_policy_variants': len(tp_policies),
            'oracle_deviation_regimes': 4,
            'oracle_deviation_error_categories': 4,
            'fav_error_categories': 5,
        },
        'baseline_metrics': baseline_m,
        'baseline_block_bootstrap': baseline_bs,
        'loss_attribution': la,
        'yearly_loss_attribution': yearly_la,
        'breach_buckets': breach_buckets,
        'fav_buckets_pred_fav': fav_buckets_pred_fav,
        'fav_buckets_pred_fav_over_stop': fav_buckets_over_stop,
        'fav_monotonicity': fav_mono,
        'breach_fav_2d_map': {
            'cumulative': True,
            'cells': cells_2d,
        },
        'actual_rr': rr_diag,
        'tp_policy_comparison': tp_results,
        'tp_policy_comparison_status': 'DIAGNOSTIC_ONLY_not_winner_selection',
        'oracle_deviation_attribution': oracle_dev,
        'interpretation_guards': [
            'Stage 4.3 does NOT select a winner',
            'Test is NOT opened',
            'Best cell/policy is NOT a trading rule — hypothesis_only',
            'Trailing stop was NOT evaluated as Stage 4.3 candidate',
            'Stage 4 verdict is NOT changed',
            'Any cell with PF > 1.15 is hypothesis_only until validated '
            'by separate val-select/val-eval protocol',
            'Oracle deviation attribution uses future information and '
            'cannot be trading features',
        ],
    }

    def _custom_default(obj):
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, (pd.Timestamp,)):
            return str(obj)
        raise TypeError(f'Object of type {type(obj)} is not JSON serializable')

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2, default=_custom_default)
    print(f'\nSaved: {args.output}')
    print('DIAGNOSTIC_ONLY — complete.')


if __name__ == '__main__':
    main()
