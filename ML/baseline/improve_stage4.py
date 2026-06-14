# =============================================================================
# Файл: ML/baseline/improve_stage4.py
# Назначение: Систематический перебор улучшений Stage 4 по результатам диагностики:
#              1. tp_fraction scan
#              2. stop_offset × tp_fraction scan
#              3. Strong fractal filter
#              4. ATR regime filter
#              5. min_rr (fav confidence) scan
#              6. Combined H6+H12 breach
#              7. Dynamic TP (best exit)
#              8. Cost-sensitive fav regression (quantile XGBoost)
# Использует инфраструктуру Stage 4.2.
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
from processing.label_signals import load_ohlc_index, evaluate_fractal_stop_trade

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
    12: {0.2: {'buy': 'buy_stop_broken_H12_off02_flag',
               'sell': 'sell_stop_broken_H12_off02_flag'},
         0.5: {'buy': 'buy_stop_broken_H12_off05_flag',
               'sell': 'sell_stop_broken_H12_off05_flag'}},
}

FAV_TARGETS = {
    6: {'buy': 'target_buy_H6_val', 'sell': 'target_sell_H6_val'},
    12: {'buy': 'target_buy_H12_val', 'sell': 'target_sell_H12_val'},
}

CAP = 5.0
CANONICAL_SPREAD = 0.20

TRAIN_MAX_YEAR = 2016
VAL_STOP_YEARS = {2017, 2018}
VAL_EVAL_MIN_YEAR = 2019

# Baseline winner config
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
            return None, 0
        parts = str(raw).split(':')
        if len(parts) != 23:
            return None, 0
        price = float(parts[1]) if parts[1] else None
        direction = int(float(parts[2])) if parts[2] else None
        if price is None or direction is None or direction == 0:
            return None, 0
        return {'price': price, 'direction': direction}, 0
    except (ValueError, TypeError):
        return None, 0


# ===========================================================================
# Trade simulation variants
# ===========================================================================

def _build_simulate_trades_base(df, entry_prices, breach_proba, fav_pred,
                                 ohlc, times, time_idx,
                                 side, h, stop_offset, p, min_fav_val, min_rr,
                                 tp_fraction, cap, spread,
                                 atr_filter=None, strong_filter=False,
                                 dynamic_tp=False,
                                 return_details=False):
    """Core trade simulation engine. Supports filters and dynamic TP."""
    trade_direction = -1 if side == 'buy' else 1
    expected_fractal_dir = -1 if side == 'buy' else 1
    trades = []

    # Compute ATR percentiles for filter (on the full df)
    atr_p05 = atr_p95 = None
    if atr_filter:
        atr_vals_raw = pd.to_numeric(df['ATR'], errors='coerce').values
        atr_valid = atr_vals_raw[~np.isnan(atr_vals_raw) & (atr_vals_raw > 0)]
        if len(atr_valid) > 100:
            atr_p05 = np.percentile(atr_valid, 5)
            atr_p95 = np.percentile(atr_valid, 95)

    for i, row in df.iterrows():
        fractal0, fractal_strong = parse_trade_fractal0(row.get('fractal0'))
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

        # --- ATR regime filter ---
        if atr_p05 is not None and atr_p95 is not None:
            if atr_val < atr_p05 or atr_val > atr_p95:
                continue

        # --- Strong fractal filter ---
        if strong_filter and fractal_strong != 1:
            continue

        # Stop price (Bid terms)
        if trade_direction == -1:
            stop_price = min(fractal_price, entry_price_val) - stop_offset * atr_val
        else:
            stop_price = max(fractal_price, entry_price_val) + stop_offset * atr_val

        # TP price (Bid terms)
        tp_val_atr = min(pred_fav * tp_fraction, cap)
        if trade_direction == -1:
            tp_price = entry_price_val + tp_val_atr * atr_val
        else:
            tp_price = entry_price_val - tp_val_atr * atr_val

        # Bars
        bars_h_bid = [(ohlc[times[k]][0], ohlc[times[k]][1],
                        ohlc[times[k]][2], ohlc[times[k]][3])
                       for k in range(idx0 + 1, idx0 + 1 + h)]
        if trade_direction == -1:
            entry_eff = entry_price_val + spread
            bars_h_eff = bars_h_bid
        else:
            entry_eff = entry_price_val
            bars_h_eff = [(ob + spread, hb + spread, lb + spread, cb + spread)
                          for ob, hb, lb, cb in bars_h_bid]

        stop_val_actual = abs(entry_eff - stop_price) / atr_val
        if stop_val_actual <= 0:
            continue

        # Filters
        if pred_break >= p:
            continue
        if pred_fav < min_fav_val:
            continue
        if pred_fav / stop_val_actual < min_rr:
            continue

        # Evaluate
        outcome = evaluate_fractal_stop_trade(
            bars_h_eff, trade_direction, entry_eff, stop_price, tp_price, atr_val)

        # Dynamic TP: if outcome is SL or TIMEOUT, check if we could have exited
        # at a better price before the SL hit
        if dynamic_tp and outcome['exit'] != 'TP':
            # Find the bar where SL was hit (if any)
            sl_bar_idx = None
            for j, (ob, hb, lb, cb) in enumerate(bars_h_eff):
                if trade_direction == -1:
                    if lb <= stop_price:
                        sl_bar_idx = j
                        break
                else:
                    if hb >= stop_price:
                        sl_bar_idx = j
                        break

            if sl_bar_idx is not None and sl_bar_idx > 0:
                # SL hit: check bars BEFORE SL for best favorable exit
                best_fav = None
                for j in range(sl_bar_idx):
                    _, hb, lb, _ = bars_h_eff[j]
                    if trade_direction == -1:  # BUY: best exit = highest price
                        best_fav = max(best_fav or 0, hb)
                    else:  # SELL: best exit = lowest price
                        best_fav = min(best_fav or float('inf'), lb)

                if best_fav is not None:
                    # Only replace if best_fav gives a positive PnL
                    if trade_direction == -1:
                        fav_pnl = (best_fav - entry_eff) / atr_val
                    else:
                        fav_pnl = (entry_eff - best_fav) / atr_val
                    if fav_pnl > 0:
                        outcome = {'exit': 'TP_dynamic', 'pnl_val': fav_pnl,
                                   'ambiguous': 0}
            elif sl_bar_idx is None:
                # TIMEOUT: check best favorable price in entire window
                best_fav = None
                for _, hb, lb, _ in bars_h_eff:
                    if trade_direction == -1:
                        best_fav = max(best_fav or 0, hb)
                    else:
                        best_fav = min(best_fav or float('inf'), lb)
                if best_fav is not None:
                    if trade_direction == -1:
                        fav_pnl = (best_fav - entry_eff) / atr_val
                    else:
                        fav_pnl = (entry_eff - best_fav) / atr_val
                    if fav_pnl > 0:
                        outcome = {'exit': 'TP_dynamic', 'pnl_val': fav_pnl,
                                   'ambiguous': 0}

        year_val = row.get('_year')
        year_int = int(year_val) if not pd.isna(year_val) else None
        trade_rec = {
            'exit': outcome['exit'],
            'pnl_val': outcome['pnl_val'],
            'stop_val': stop_val_actual,
            'pnl_r': outcome['pnl_val'] / stop_val_actual
                if stop_val_actual > 0 else outcome['pnl_val'],
            'ambiguous': outcome['ambiguous'],
            'year': year_int, 'side': side,
        }
        trades.append(trade_rec)

    return trades


def simulate_trades(df, entry_prices, breach_proba, fav_pred, ohlc, times,
                    time_idx, side='sell', h=6, stop_offset=0.5,
                    p=0.5, min_fav_val=0.5, min_rr=1.5, tp_fraction=0.5,
                    cap=5.0, spread=0.0, return_details=False,
                    atr_filter=False, strong_filter=False, dynamic_tp=False):
    return _build_simulate_trades_base(
        df, entry_prices, breach_proba, fav_pred, ohlc, times, time_idx,
        side=side, h=h, stop_offset=stop_offset, p=p, min_fav_val=min_fav_val,
        min_rr=min_rr, tp_fraction=tp_fraction, cap=cap, spread=spread,
        atr_filter=atr_filter, strong_filter=strong_filter,
        dynamic_tp=dynamic_tp, return_details=return_details,
    )


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
    return {'pf': round(pf, 3) if pf != float('inf') else pf,
            'n_trades': n_trades, 'trades_per_year': round(tpyr, 1),
            'n_years': n_years}


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


def train_xgb_fav_quantile(X_train, y_train, X_val_stop, y_val_stop,
                            quantile=0.3, random_state=42):
    """Cost-sensitive fav: predict lower quantile to avoid overprediction."""
    model = xgb.XGBRegressor(
        n_estimators=200, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        objective='reg:quantileerror',
        quantile_alpha=quantile,
        early_stopping_rounds=20, random_state=random_state,
        n_jobs=-1, verbosity=0)
    model.fit(X_train, y_train, eval_set=[(X_val_stop, y_val_stop)], verbose=False)
    return model


# ===========================================================================
# Main
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description='Stage 4 improvement scans')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--ohlc', default='DATA/XAUUSD_H1_OHLC.csv')
    parser.add_argument('--output', default='ML/reports/stage4_improvements.json')
    parser.add_argument('--spread', type=float, default=CANONICAL_SPREAD)
    args = parser.parse_args()

    print('=' * 70)
    print('Stage 4 Improvement Scans')
    print('=' * 70)

    # ---- Data ----
    print('Loading data...')
    train_df, val_stop_df, val_eval_df = load_splits(args.train, args.val)
    ohlc, times, time_idx = load_ohlc_index(args.ohlc)
    entry_prices_val = compute_entry_prices(val_eval_df, ohlc, times, time_idx)

    # Features
    X_train_breach, _ = profile_base_raw_plus_time(train_df)
    X_val_stop_breach, _ = profile_base_raw_plus_time(val_stop_df)
    X_val_eval_breach, _ = profile_base_raw_plus_time(val_eval_df)
    X_train_fav, _ = profile_base_raw(train_df)
    X_val_stop_fav, _ = profile_base_raw(val_stop_df)
    X_val_eval_fav, _ = profile_base_raw(val_eval_df)

    h, off, side = 6, 0.5, 'sell'
    target_col = BREACH_TARGETS[h][off][side]
    fav_col = FAV_TARGETS[h][side]
    target_h12 = BREACH_TARGETS[12][off][side]

    # ---- Train breach H6 ----
    y_train_b6 = train_df[target_col].values
    y_stop_b6 = val_stop_df[target_col].values
    y_eval_b6 = val_eval_df[target_col].values
    m_train_b = ~np.isnan(y_train_b6)
    m_stop_b = ~np.isnan(y_stop_b6)
    m_eval_b = ~np.isnan(y_eval_b6)

    print('Training XGBoost breach H6...')
    breach_h6 = train_xgb_breach(
        X_train_breach[m_train_b], y_train_b6[m_train_b],
        X_val_stop_breach[m_stop_b], y_stop_b6[m_stop_b])
    breach_proba_h6 = breach_h6.predict_proba(X_val_eval_breach[m_eval_b])[:, 1]
    print(f'  AUC: {roc_auc_score(y_eval_b6[m_eval_b], breach_proba_h6):.4f}')

    # ---- Train breach H12 (for combined) ----
    y_train_b12 = train_df[target_h12].values
    y_stop_b12 = val_stop_df[target_h12].values
    y_eval_b12 = val_eval_df[target_h12].values
    m_train_b12 = ~np.isnan(y_train_b12)
    m_stop_b12 = ~np.isnan(y_stop_b12)
    m_eval_b12 = ~np.isnan(y_eval_b12)

    print('Training XGBoost breach H12...')
    breach_h12 = train_xgb_breach(
        X_train_breach[m_train_b12], y_train_b12[m_train_b12],
        X_val_stop_breach[m_stop_b12], y_stop_b12[m_stop_b12])
    breach_proba_h12 = breach_h12.predict_proba(X_val_eval_breach[m_eval_b12])[:, 1]
    print(f'  AUC: {roc_auc_score(y_eval_b12[m_eval_b12], breach_proba_h12):.4f}')

    # ---- Train fav (RF + quantile XGBoost) ----
    y_train_f = train_df[fav_col].values
    y_stop_f = val_stop_df[fav_col].values
    y_eval_f = val_eval_df[fav_col].values
    m_train_f = ~np.isnan(y_train_f)
    m_stop_f = ~np.isnan(y_stop_f)
    m_eval_f = ~np.isnan(y_eval_f)

    print('Training RF fav...')
    fav_rf = train_rf_fav(X_train_fav[m_train_f], y_train_f[m_train_f])

    print('Training XGBoost fav quantile (q=0.3)...')
    fav_xgb_q30 = train_xgb_fav_quantile(
        X_train_fav[m_train_f], y_train_f[m_train_f],
        X_val_stop_fav[m_stop_f], y_stop_f[m_stop_f], quantile=0.3)

    # ---- Align ----
    inter = m_eval_b & m_eval_f
    inter_h12 = m_eval_b12 & m_eval_f
    inter_all3 = m_eval_b & m_eval_b12 & m_eval_f
    print(f'  Intersection H6+fav: {inter.sum()}, '
          f'H12+fav: {inter_h12.sum()}, '
          f'All3: {inter_all3.sum()}')

    bp_h6 = breach_h6.predict_proba(X_val_eval_breach[inter])[:, 1]
    bp_h12_aligned = breach_h12.predict_proba(X_val_eval_breach[inter_h12])[:, 1]
    fp_rf = fav_rf.predict(X_val_eval_fav[inter])
    fp_xgb30 = fav_xgb_q30.predict(X_val_eval_fav[inter])
    val_m = val_eval_df[inter].reset_index(drop=True)
    entry_m = entry_prices_val[inter]

    # For combined: align all 3
    bp_h6_comb = breach_h6.predict_proba(X_val_eval_breach[inter_all3])[:, 1]
    bp_h12_comb = breach_h12.predict_proba(X_val_eval_breach[inter_all3])[:, 1]
    fp_comb = fav_rf.predict(X_val_eval_fav[inter_all3])
    val_comb = val_eval_df[inter_all3].reset_index(drop=True)
    entry_comb = entry_prices_val[inter_all3]

    results = {}
    baseline_pf = None

    def sim(m, e, bp, fp, **kw):
        return simulate_trades(m, e, bp, fp, ohlc, times, time_idx,
                               side=side, h=h, stop_offset=off,
                               p=WINNER_P, min_fav_val=WINNER_MIN_FAV,
                               min_rr=WINNER_MIN_RR, tp_fraction=WINNER_TP_FRACTION,
                               cap=CAP, spread=args.spread, **kw)

    def pf(trades):
        return compute_trade_metrics(trades)['pf']

    # =====================================================================
    # 0. Baseline (re-establish)
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('0. BASELINE (sell_H6_off05, p=0.4, mf=0.3, rr=1.0, tf=0.4)')
    print(f'{"=" * 70}')
    t0 = sim(val_m, entry_m, bp_h6, fp_rf)
    baseline_pf = pf(t0)
    print(f'  PF={baseline_pf}  trades={len(t0)}')
    results['baseline'] = {'pf': baseline_pf, 'n_trades': len(t0)}

    # =====================================================================
    # 1. tp_fraction scan
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('1. TP_FRACTION SCAN')
    print(f'{"=" * 70}')
    print(f'  {"tf":>6s}  {"PF":>8s}  {"Trades":>7s}  {"T/Yr":>6s}')
    tf_results = {}
    for tf in [0.4, 0.6, 0.8, 1.0, 1.5, 2.0]:
        t = simulate_trades(val_m, entry_m, bp_h6, fp_rf, ohlc, times, time_idx,
                            side=side, h=h, stop_offset=off,
                            p=WINNER_P, min_fav_val=WINNER_MIN_FAV,
                            min_rr=WINNER_MIN_RR, tp_fraction=tf,
                            cap=CAP, spread=args.spread)
        m = compute_trade_metrics(t)
        tf_results[f'tf={tf}'] = {'pf': m['pf'], 'n_trades': m['n_trades'],
                                   'trades_per_year': m['trades_per_year']}
        print(f'  {tf:6.1f}  {m["pf"]:8.3f}  {m["n_trades"]:7d}  '
              f'{m["trades_per_year"]:6.1f}')
    results['tp_fraction_scan'] = tf_results

    # =====================================================================
    # 2. stop_offset × tp_fraction scan
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('2. STOP_OFFSET × TP_FRACTION SCAN')
    print(f'{"=" * 70}')
    print(f'  {"off":>5s} {"tf":>5s}  {"PF":>8s}  {"Trades":>7s}  {"T/Yr":>6s}')
    so_tf_results = {}
    best_so_tf = (None, 0)
    for so in [0.2, 0.3, 0.4, 0.5]:
        for tf in [0.4, 0.6, 0.8, 1.0]:
            t = simulate_trades(val_m, entry_m, bp_h6, fp_rf, ohlc, times, time_idx,
                                side=side, h=h, stop_offset=so,
                                p=WINNER_P, min_fav_val=WINNER_MIN_FAV,
                                min_rr=WINNER_MIN_RR, tp_fraction=tf,
                                cap=CAP, spread=args.spread)
            m = compute_trade_metrics(t)
            key = f'off={so}_tf={tf}'
            so_tf_results[key] = {'pf': m['pf'], 'n_trades': m['n_trades'],
                                   'trades_per_year': m['trades_per_year']}
            print(f'  {so:5.1f} {tf:5.1f}  {m["pf"]:8.3f}  {m["n_trades"]:7d}  '
                  f'{m["trades_per_year"]:6.1f}')
            if m['pf'] > best_so_tf[1]:
                best_so_tf = (key, m['pf'])
    print(f'\n  Best: {best_so_tf[0]} PF={best_so_tf[1]:.3f}')
    results['stop_offset_x_tp_fraction'] = so_tf_results

    # =====================================================================
    # 3. Strong fractal filter
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('3. STRONG FRACTAL FILTER')
    print(f'{"=" * 70}')
    t = sim(val_m, entry_m, bp_h6, fp_rf, strong_filter=True)
    m = compute_trade_metrics(t)
    print(f'  PF={m["pf"]}  trades={m["n_trades"]}  '
          f'T/yr={m["trades_per_year"]}')
    results['strong_fractal_filter'] = {'pf': m['pf'], 'n_trades': m['n_trades'],
                                         'trades_per_year': m['trades_per_year']}

    # =====================================================================
    # 4. ATR regime filter
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('4. ATR REGIME FILTER (skip p5/p95 extremes)')
    print(f'{"=" * 70}')
    t = sim(val_m, entry_m, bp_h6, fp_rf, atr_filter=True)
    m = compute_trade_metrics(t)
    print(f'  PF={m["pf"]}  trades={m["n_trades"]}  '
          f'T/yr={m["trades_per_year"]}')
    results['atr_filter'] = {'pf': m['pf'], 'n_trades': m['n_trades'],
                              'trades_per_year': m['trades_per_year']}

    # ---- Combined: strong + ATR ----
    print(f'\n{"=" * 70}')
    print('4b. STRONG + ATR FILTER (combined)')
    print(f'{"=" * 70}')
    t = sim(val_m, entry_m, bp_h6, fp_rf, strong_filter=True, atr_filter=True)
    m = compute_trade_metrics(t)
    print(f'  PF={m["pf"]}  trades={m["n_trades"]}  '
          f'T/yr={m["trades_per_year"]}')
    results['strong_plus_atr_filter'] = {'pf': m['pf'], 'n_trades': m['n_trades'],
                                          'trades_per_year': m['trades_per_year']}

    # =====================================================================
    # 5. min_rr (fav confidence) scan
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('5. MIN_RR (FAV CONFIDENCE) SCAN')
    print(f'{"=" * 70}')
    print(f'  {"min_rr":>7s}  {"PF":>8s}  {"Trades":>7s}  {"T/Yr":>6s}')
    rr_results = {}
    for rr in [0.5, 0.75, 1.0, 1.5, 2.0]:
        t = simulate_trades(val_m, entry_m, bp_h6, fp_rf, ohlc, times, time_idx,
                            side=side, h=h, stop_offset=off,
                            p=WINNER_P, min_fav_val=WINNER_MIN_FAV,
                            min_rr=rr, tp_fraction=WINNER_TP_FRACTION,
                            cap=CAP, spread=args.spread)
        m = compute_trade_metrics(t)
        rr_results[f'rr={rr}'] = {'pf': m['pf'], 'n_trades': m['n_trades'],
                                   'trades_per_year': m['trades_per_year']}
        print(f'  {rr:7.2f}  {m["pf"]:8.3f}  {m["n_trades"]:7d}  '
              f'{m["trades_per_year"]:6.1f}')
    results['min_rr_scan'] = rr_results

    # =====================================================================
    # 6. Combined H6+H12 breach
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('6. COMBINED H6+H12 BREACH (both < p)')
    print(f'{"=" * 70}')
    # Align all 3
    combined_mask = bp_h6_comb < WINNER_P
    combined_mask &= bp_h12_comb < WINNER_P
    # Create arrays with only combined-mask entries
    mask_indices = np.where(combined_mask)[0]
    if len(mask_indices) > 20:
        comb_df = val_comb.iloc[mask_indices].reset_index(drop=True)
        comb_entry = entry_comb[mask_indices]
        comb_bp = bp_h6_comb[mask_indices]
        comb_fp = fp_comb[mask_indices]
        # For combined, we use H6 for the trade (stop/TP based on H6 horizon)
        t = simulate_trades(comb_df, comb_entry, comb_bp, comb_fp,
                            ohlc, times, time_idx,
                            side=side, h=6, stop_offset=off,
                            p=WINNER_P, min_fav_val=WINNER_MIN_FAV,
                            min_rr=WINNER_MIN_RR, tp_fraction=WINNER_TP_FRACTION,
                            cap=CAP, spread=args.spread)
        m = compute_trade_metrics(t)
        print(f'  PF={m["pf"]}  trades={m["n_trades"]}  '
              f'T/yr={m["trades_per_year"]}')
        results['combined_h6h12'] = {'pf': m['pf'], 'n_trades': m['n_trades'],
                                      'trades_per_year': m['trades_per_year']}
    else:
        print('  Insufficient trades')
        results['combined_h6h12'] = {'pf': 0, 'n_trades': 0}

    # =====================================================================
    # 7. Dynamic TP
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('7. DYNAMIC TP (best exit before SL or within window)')
    print(f'{"=" * 70}')
    t = sim(val_m, entry_m, bp_h6, fp_rf, dynamic_tp=True)
    m = compute_trade_metrics(t)
    exits = Counter(trade['exit'] for trade in t)
    print(f'  PF={m["pf"]}  trades={m["n_trades"]}  '
          f'T/yr={m["trades_per_year"]}')
    print(f'  Exit distribution: TP={exits.get("TP",0)}  '
          f'SL={exits.get("SL",0)}  '
          f'TP_dyn={exits.get("TP_dynamic",0)}  '
          f'TIMEOUT={exits.get("TIMEOUT",0)}')
    results['dynamic_tp'] = {'pf': m['pf'], 'n_trades': m['n_trades'],
                              'trades_per_year': m['trades_per_year'],
                              'exit_distribution': dict(exits)}

    # ---- Dynamic TP + Strong + ATR ----
    print(f'\n{"=" * 70}')
    print('7b. DYNAMIC TP + STRONG + ATR FILTER')
    print(f'{"=" * 70}')
    t = sim(val_m, entry_m, bp_h6, fp_rf,
            dynamic_tp=True, strong_filter=True, atr_filter=True)
    m = compute_trade_metrics(t)
    exits = Counter(trade['exit'] for trade in t)
    print(f'  PF={m["pf"]}  trades={m["n_trades"]}  '
          f'T/yr={m["trades_per_year"]}')
    print(f'  Exit: TP={exits.get("TP",0)} SL={exits.get("SL",0)} '
          f'TP_dyn={exits.get("TP_dynamic",0)} TO={exits.get("TIMEOUT",0)}')
    results['dynamic_tp_strong_atr'] = {'pf': m['pf'], 'n_trades': m['n_trades'],
                                         'trades_per_year': m['trades_per_year'],
                                         'exit_distribution': dict(exits)}

    # =====================================================================
    # 8. Cost-sensitive fav: quantile XGBoost q=0.3
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('8. COST-SENSITIVE FAV: XGBoost quantile q=0.3')
    print(f'{"=" * 70}')
    t = sim(val_m, entry_m, bp_h6, fp_xgb30)
    m = compute_trade_metrics(t)
    print(f'  PF={m["pf"]}  trades={m["n_trades"]}  '
          f'T/yr={m["trades_per_year"]}')
    results['fav_xgb_quantile_03'] = {'pf': m['pf'], 'n_trades': m['n_trades'],
                                       'trades_per_year': m['trades_per_year']}

    # ---- Fav quantile + dynamic TP ----
    print(f'\n{"=" * 70}')
    print('8b. FAV QUANTILE q=0.3 + DYNAMIC TP')
    print(f'{"=" * 70}')
    t = sim(val_m, entry_m, bp_h6, fp_xgb30, dynamic_tp=True)
    m = compute_trade_metrics(t)
    print(f'  PF={m["pf"]}  trades={m["n_trades"]}  '
          f'T/yr={m["trades_per_year"]}')
    results['fav_quantile_plus_dynamic_tp'] = {
        'pf': m['pf'], 'n_trades': m['n_trades'],
        'trades_per_year': m['trades_per_year']}

    # ---- Best combo: dynamic TP + strong + ATR + quantile fav ----
    print(f'\n{"=" * 70}')
    print('9. BEST COMBO: dynTP + strong + ATR + fav_q30')
    print(f'{"=" * 70}')
    t = sim(val_m, entry_m, bp_h6, fp_xgb30,
            dynamic_tp=True, strong_filter=True, atr_filter=True)
    m = compute_trade_metrics(t)
    exits = Counter(trade['exit'] for trade in t)
    print(f'  PF={m["pf"]}  trades={m["n_trades"]}  '
          f'T/yr={m["trades_per_year"]}')
    print(f'  Exit: TP={exits.get("TP",0)} SL={exits.get("SL",0)} '
          f'TP_dyn={exits.get("TP_dynamic",0)} TO={exits.get("TIMEOUT",0)}')
    results['best_combo'] = {'pf': m['pf'], 'n_trades': m['n_trades'],
                              'trades_per_year': m['trades_per_year'],
                              'exit_distribution': dict(exits)}

    # =====================================================================
    # Summary
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('SUMMARY')
    print(f'{"=" * 70}')
    print(f'  {"Experiment":<45s}  {"PF":>8s}  {"Trades":>7s}  {"Δ vs baseline":>13s}')
    print(f'  {"-"*75}')
    for name, data in results.items():
        if isinstance(data, dict) and 'pf' in data:
            delta = data['pf'] - baseline_pf if baseline_pf else 0
            print(f'  {name:<45s}  {data["pf"]:8.3f}  {data.get("n_trades",0):7d}  '
                  f'{delta:+.3f}')

    # Save
    output = {
        'config': {
            'target': 'sell_H6_off05',
            'baseline_params': {'p': WINNER_P, 'min_fav': WINNER_MIN_FAV,
                                'min_rr': WINNER_MIN_RR,
                                'tp_fraction': WINNER_TP_FRACTION},
            'spread': args.spread,
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
