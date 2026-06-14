# =============================================================================
# Файл: ML/baseline/trail_stop_stage4.py
# Назначение: Тест стратегий трейлинг-стопа на инфраструктуре Stage 4.2.
#             SELL (sell_H6_off05) — от безубытка до непрерывного ATR-трейла.
# Язык: Python 3.10+
# Создан: 2026-06-14
# =============================================================================

import argparse, json, os, sys
from collections import Counter
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import roc_auc_score
import xgboost as xgb

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from processing.label_signals import load_ohlc_index

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_CHANNEL_KEYS = ['price', 'direction', 'front', 'back', 'strong', 'break',
                     'reverse', 'power', 'count', 'impulse']

BREACH_TARGETS = {
    6: {0.2: {'buy': 'buy_stop_broken_H6_off02_flag',
              'sell': 'sell_stop_broken_H6_off02_flag'},
        0.5: {'buy': 'buy_stop_broken_H6_off05_flag',
              'sell': 'sell_stop_broken_H6_off05_flag'}},
}

FAV_TARGETS = {
    6: {'buy': 'target_buy_H6_val', 'sell': 'target_sell_H6_val'},
}

CAP = 5.0
CANONICAL_SPREAD = 0.20

TRAIN_MAX_YEAR = 2016
VAL_STOP_YEARS = {2017, 2018}
VAL_EVAL_MIN_YEAR = 2019

WINNER_P = 0.4
WINNER_MIN_FAV = 0.3
WINNER_MIN_RR = 1.0
WINNER_TP_FRACTION = 0.4

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_splits(train_path, val_path, purge_bars=12):
    train_df = pd.read_csv(train_path, sep=';')
    val_df = pd.read_csv(val_path, sep=';')
    train_df['_year'] = pd.to_datetime(
        train_df['time'], format='%Y.%m.%d %H:%M', errors='coerce').dt.year
    val_df['_year'] = pd.to_datetime(
        val_df['time'], format='%Y.%m.%d %H:%M', errors='coerce').dt.year
    train = train_df[train_df['_year'] <= TRAIN_MAX_YEAR].copy()
    val_stop = train_df[train_df['_year'].isin(VAL_STOP_YEARS)].copy()
    val_eval_train = train_df[train_df['_year'] >= VAL_EVAL_MIN_YEAR].copy()
    val_eval = pd.concat([val_eval_train, val_df], ignore_index=True)
    if purge_bars > 0:
        if len(train) > purge_bars:
            train = train.iloc[:-purge_bars]
        if len(val_stop) > purge_bars:
            val_stop = val_stop.iloc[:-purge_bars]
        if len(val_eval) > purge_bars:
            val_eval = val_eval.iloc[:-purge_bars]
    return train, val_stop, val_eval


# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# OHLC
# ---------------------------------------------------------------------------

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
# Trailing Stop Trade Simulator
# ===========================================================================

# Trail strategies: (mode, param1, param2)
# mode: 'none' | 'dynamic' | 'breakeven' | 'atr' | 'step'
# 'breakeven': param1 = fraction of TP distance to move to breakeven
# 'atr': param1 = ATR multiplier for trail distance
# 'step': param1 = list of (fraction_of_TP, fraction_of_TP_to_lock)

TRAIL_STRATEGIES = {
    'baseline':          ('none',     0.0,      None),
    'dynamic':           ('dynamic',  0.0,      None),
    'be_03':             ('breakeven', 0.3,     None),
    'be_05':             ('breakeven', 0.5,     None),
    'be_07':             ('breakeven', 0.7,     None),
    'atr_02':            ('atr',       0.2,     None),
    'atr_03':            ('atr',       0.3,     None),
    'atr_05':            ('atr',       0.5,     None),
    'atr_10':            ('atr',       1.0,     None),
    'step_33_66':        ('step',      0.0,     [(0.33, 0.33), (0.66, 0.66)]),
    'step_50_50':        ('step',      0.0,     [(0.50, 0.50)]),
    'step_25_50_75':     ('step',      0.0,     [(0.25, 0.25), (0.50, 0.50), (0.75, 0.75)]),
    'be05_atr03':        ('be_atr',    0.5,     0.3),
    'be05_atr05':        ('be_atr',    0.5,     0.5),
}

# ---------------------------------------------------------------------------
# SELL trade with trailing stop (OHLC=Bid, Ask-transformed bars)
# ---------------------------------------------------------------------------

def simulate_sell_trail(df, entry_prices, breach_proba, fav_pred,
                         ohlc, times, time_idx,
                         h=6, stop_offset=0.5,
                         p=0.5, min_fav_val=0.5, min_rr=1.5,
                         tp_fraction=0.5, cap=5.0, spread=0.0,
                         trail_mode='none', trail_param=0.0,
                         trail_steps=None,
                         return_details=False):
    """Симуляция SELL с трейлинг-стопом. OHLC=Bid, бары преобразованы в Ask."""
    expected_fractal_dir = 1  # SELL: fractal direction = 1 (peak)
    trades = []

    for i, row in df.iterrows():
        fractal0 = parse_trade_fractal0(row.get('fractal0'))
        if fractal0 is None or fractal0['direction'] != expected_fractal_dir:
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

        # --- Entry filters ---
        if pred_break >= p:
            continue
        if pred_fav < min_fav_val:
            continue

        # Stop (Bid) and TP (Bid)
        stop_price = max(fractal_price, entry_price_val) + stop_offset * atr_val
        tp_val_atr = min(pred_fav * tp_fraction, cap)
        tp_price = entry_price_val - tp_val_atr * atr_val

        # Ask-transformed bars
        bars_bid = [(ohlc[times[k]][0], ohlc[times[k]][1],
                      ohlc[times[k]][2], ohlc[times[k]][3])
                     for k in range(idx0 + 1, idx0 + 1 + h)]
        bars = [(ob + spread, hb + spread, lb + spread, cb + spread)
                for ob, hb, lb, cb in bars_bid]
        entry_eff = entry_price_val  # Bid

        # Stop in Ask terms (adjusted for bars transformation)
        initial_sl = stop_price  # same in Bid/Ask since bars are shifted

        # Risk/reward
        stop_val = (initial_sl - entry_eff) / atr_val
        if stop_val <= 0:
            continue
        if pred_fav / stop_val < min_rr:
            continue

        # --- Bar-by-bar evaluation with trailing stop ---
        best_low = entry_eff
        trail_level = initial_sl
        exit_type = 'TIMEOUT'
        exit_price = bars[-1][3]  # close of last bar
        ambiguous = 0

        # When was the stop moved (for diagnostics)
        stop_moved_bar = -1

        for j, (ob, hb, lb, cb) in enumerate(bars):
            # Check fixed TP
            if lb <= tp_price:
                # Check simultaneous SL
                if hb >= trail_level:
                    exit_type = 'SL'
                    exit_price = trail_level
                    ambiguous = 1
                else:
                    exit_type = 'TP'
                    exit_price = tp_price
                break

            # Check trail SL
            if hb >= trail_level:
                exit_type = 'SL'
                exit_price = trail_level
                break

            # Update best_low
            if lb < best_low:
                best_low = lb

            # Compute new trail level
            new_trail = trail_level
            if trail_mode == 'dynamic':
                new_trail = best_low + 1e-6  # exit at best price
                if stop_moved_bar < 0:
                    stop_moved_bar = j if new_trail < initial_sl else -1
            elif trail_mode == 'breakeven':
                tp_dist = entry_eff - tp_price
                be_thresh = entry_eff - trail_param * tp_dist
                if best_low <= be_thresh and trail_level > entry_eff:
                    new_trail = entry_eff
                    if stop_moved_bar < 0:
                        stop_moved_bar = j
            elif trail_mode == 'atr':
                new_trail = best_low + trail_param * atr_val
                new_trail = min(new_trail, initial_sl)
                if new_trail < trail_level - 0.0001 and stop_moved_bar < 0:
                    stop_moved_bar = j
            elif trail_mode == 'step':
                tp_dist = entry_eff - tp_price
                for frac, lock in trail_steps:
                    trig = entry_eff - frac * tp_dist
                    lock_level = entry_eff - lock * tp_dist
                    if best_low <= trig and trail_level > lock_level:
                        new_trail = max(new_trail, lock_level)
                        if stop_moved_bar < 0:
                            stop_moved_bar = j
            elif trail_mode == 'be_atr':
                tp_dist = entry_eff - tp_price
                be_thresh = entry_eff - trail_param * tp_dist
                if best_low <= be_thresh and trail_level > entry_eff:
                    new_trail = entry_eff
                    if stop_moved_bar < 0:
                        stop_moved_bar = j
                if trail_level <= entry_eff + 0.0001:
                    new_trail = best_low + trail_steps * atr_val
                    new_trail = max(new_trail, tp_price)
                if new_trail < trail_level - 0.0001 and stop_moved_bar < 0:
                    stop_moved_bar = j

            new_trail = min(new_trail, initial_sl)
            if new_trail < trail_level:
                trail_level = new_trail

        pnl_val = (entry_eff - exit_price) / atr_val

        year_val = row.get('_year')
        year_int = int(year_val) if not pd.isna(year_val) else None

        rec = {
            'exit': exit_type,
            'pnl_val': pnl_val,
            'stop_val': stop_val,
            'pnl_r': pnl_val / stop_val if stop_val > 0 else pnl_val,
            'ambiguous': ambiguous,
            'year': year_int,
            'side': 'sell',
        }
        if return_details:
            rec['pred_break'] = pred_break
            rec['pred_fav'] = pred_fav
            rec['stop_moved_bar'] = stop_moved_bar
            rec['best_low'] = best_low
        trades.append(rec)

    return trades


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_trade_metrics(trades):
    if not trades:
        return {'pf': 0.0, 'n_trades': 0, 'trades_per_year': 0, 'n_years': 0}
    n_trades = len(trades)
    years_covered = sorted(set(t['year'] for t in trades if t['year'] is not None))
    n_years = len(years_covered) if years_covered else 1
    tpyr = n_trades / n_years if n_years > 0 else n_trades
    gp = sum(max(0, t['pnl_val']) for t in trades)
    gl = abs(sum(min(0, t['pnl_val']) for t in trades))
    pf = gp / gl if gl > 0 else (float('inf') if gp > 0 else 0.0)

    exits = Counter(t['exit'] for t in trades)
    sl_pct = exits.get('SL', 0) / n_trades * 100 if n_trades else 0
    tp_pct = exits.get('TP', 0) / n_trades * 100 if n_trades else 0
    to_pct = exits.get('TIMEOUT', 0) / n_trades * 100 if n_trades else 0
    amb_pct = sum(1 for t in trades if t['ambiguous']) / n_trades * 100 if n_trades else 0

    win_rate = sum(1 for t in trades if t['pnl_val'] > 0) / n_trades * 100 if n_trades else 0
    avg_win = np.mean([t['pnl_val'] for t in trades if t['pnl_val'] > 0]) if n_trades else 0
    avg_loss = np.mean([abs(t['pnl_val']) for t in trades if t['pnl_val'] < 0]) if n_trades else 0

    return {
        'pf': round(pf, 3) if pf != float('inf') else pf,
        'n_trades': n_trades, 'trades_per_year': round(tpyr, 1),
        'n_years': n_years,
        'sl_pct': round(sl_pct, 1), 'tp_pct': round(tp_pct, 1),
        'timeout_pct': round(to_pct, 1), 'ambiguous_pct': round(amb_pct, 1),
        'win_rate_pct': round(float(win_rate), 1),
        'avg_win_atr': round(float(avg_win), 3),
        'avg_loss_atr': round(float(avg_loss), 3),
    }


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

def train_xgb_breach(X_train, y_train, X_val_stop, y_val_stop, random_state=42):
    neg = int((y_train == 0).sum())
    pos = int((y_train == 1).sum())
    sw = neg / pos if pos > 0 else 1.0
    model = xgb.XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, scale_pos_weight=sw,
        objective='binary:logistic', eval_metric='auc',
        early_stopping_rounds=20, random_state=random_state,
        n_jobs=-1, verbosity=0)
    model.fit(X_train, y_train, eval_set=[(X_val_stop, y_val_stop)], verbose=False)
    return model


def train_rf_fav(X_train, y_train, random_state=42):
    model = RandomForestRegressor(
        n_estimators=200, max_depth=12, min_samples_leaf=50,
        random_state=random_state, n_jobs=-1)
    model.fit(X_train, y_train)
    return model


# ===========================================================================
# Main
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Trailing stop strategies for Stage 4')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--ohlc', default='DATA/XAUUSD_H1_OHLC.csv')
    parser.add_argument('--output', default='ML/reports/trail_stop_stage4.json')
    parser.add_argument('--spread', type=float, default=CANONICAL_SPREAD)
    args = parser.parse_args()

    print('=' * 80)
    print('Trailing Stop Strategies for Stage 4 (sell_H6_off05)')
    print('=' * 80)

    # ---- Data ----
    print('Loading data...')
    train_df, val_stop_df, val_eval_df = load_splits(args.train, args.val)
    ohlc, times, time_idx = load_ohlc_index(args.ohlc)
    entry_prices_val = compute_entry_prices(val_eval_df, ohlc, times, time_idx)

    X_train_breach, _ = profile_base_raw_plus_time(train_df)
    X_val_stop_breach, _ = profile_base_raw_plus_time(val_stop_df)
    X_val_eval_breach, _ = profile_base_raw_plus_time(val_eval_df)
    X_train_fav, _ = profile_base_raw(train_df)
    X_val_eval_fav, _ = profile_base_raw(val_eval_df)

    h, off = 6, 0.5
    target_col = BREACH_TARGETS[h][off]['sell']
    fav_col = FAV_TARGETS[h]['sell']

    # ---- Train models ----
    y_train_b = train_df[target_col].values
    y_stop_b = val_stop_df[target_col].values
    y_eval_b = val_eval_df[target_col].values
    m_train_b = ~np.isnan(y_train_b)
    m_stop_b = ~np.isnan(y_stop_b)
    m_eval_b = ~np.isnan(y_eval_b)

    print('Training XGBoost breach H6...')
    breach_h6 = train_xgb_breach(
        X_train_breach[m_train_b], y_train_b[m_train_b],
        X_val_stop_breach[m_stop_b], y_stop_b[m_stop_b])
    breach_proba_h6 = breach_h6.predict_proba(X_val_eval_breach[m_eval_b])[:, 1]
    print(f'  AUC val_eval: {roc_auc_score(y_eval_b[m_eval_b], breach_proba_h6):.4f}')

    y_train_f = train_df[fav_col].values
    m_train_f = ~np.isnan(y_train_f)
    m_eval_f = ~np.isnan(val_eval_df[fav_col].values)

    print('Training RF fav...')
    fav_rf = train_rf_fav(X_train_fav[m_train_f], y_train_f[m_train_f])

    # ---- Align ----
    inter = m_eval_b & m_eval_f
    print(f'  Intersection: {inter.sum()}')
    bp = breach_h6.predict_proba(X_val_eval_breach[inter])[:, 1]
    fp = fav_rf.predict(X_val_eval_fav[inter])
    val_m = val_eval_df[inter].reset_index(drop=True)
    entry_m = entry_prices_val[inter]

    # ---- Test strategies ----
    results = {}
    baseline_pf = None

    for name, (mode, p1, p2) in TRAIL_STRATEGIES.items():
        print(f'\n  {name}: mode={mode}, p1={p1}, p2={p2} ...', end=' ', flush=True)

        trades = simulate_sell_trail(
            val_m, entry_m, bp, fp, ohlc, times, time_idx,
            h=h, stop_offset=off,
            p=WINNER_P, min_fav_val=WINNER_MIN_FAV,
            min_rr=WINNER_MIN_RR, tp_fraction=WINNER_TP_FRACTION,
            cap=CAP, spread=args.spread,
            trail_mode=mode, trail_param=p1, trail_steps=p2,
            return_details=(name == 'baseline'),
        )
        m = compute_trade_metrics(trades)
        results[name] = m

        if name == 'baseline':
            baseline_pf = m['pf']
            baseline_details = trades

        delta_str = f'(Δ {m["pf"] - baseline_pf:+.3f})' if baseline_pf is not None else ''
        print(f'PF={m["pf"]:.3f}  tr={m["n_trades"]}  '
              f'TP={m["tp_pct"]:.0f}% SL={m["sl_pct"]:.0f}% TO={m["timeout_pct"]:.0f}% '
              f'WR={m["win_rate_pct"]:.0f}%  '
              f'aW={m["avg_win_atr"]:.3f} aL={m["avg_loss_atr"]:.3f}  {delta_str}')

    # ---- Summary table ----
    print(f'\n{"=" * 80}')
    print(f'{"Strategy":<20s} {"PF":>8s} {"Trades":>7s} {"TP%":>6s} {"SL%":>6s} '
          f'{"TO%":>6s} {"Win%":>6s} {"aW":>7s} {"aL":>7s} {"ΔPF":>8s}')
    print('-' * 80)

    for name in TRAIL_STRATEGIES:
        m = results[name]
        delta = m['pf'] - baseline_pf if baseline_pf is not None else 0
        pf_str = f'{m["pf"]:.3f}' if m['pf'] != float('inf') else 'inf'
        print(f'{name:<20s} {pf_str:>8s} {m["n_trades"]:>7d} '
              f'{m["tp_pct"]:>5.0f}% {m["sl_pct"]:>5.0f}% '
              f'{m["timeout_pct"]:>5.0f}% {m["win_rate_pct"]:>5.0f}% '
              f'{m["avg_win_atr"]:>7.3f} {m["avg_loss_atr"]:>7.3f} '
              f'{delta:>+8.3f}')

    # ---- Save ----
    output = {
        'config': {
            'target': 'sell_H6_off05',
            'params': {'p': WINNER_P, 'min_fav': WINNER_MIN_FAV,
                       'min_rr': WINNER_MIN_RR, 'tp_fraction': WINNER_TP_FRACTION},
            'spread': args.spread,
            'split': {'train': f'<={TRAIN_MAX_YEAR}',
                      'val_stop': list(VAL_STOP_YEARS),
                      'val_eval': f'>={VAL_EVAL_MIN_YEAR}'},
        },
        'baseline_pf': baseline_pf,
        'results': results,
    }
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f'\nSaved: {args.output}')


if __name__ == '__main__':
    main()
