# =============================================================================
# Файл: ML/baseline/benchmark_fractal_stop_stage4_1.py
# Назначение: Stage 4.1 — XGBoost-fav + combined breach H6/H12 + permutation test
#              Три изменения по аудиту Stage 4:
#              1. XGBoost-fav вместо RF-fav
#              2. Combined breach: breach_H6<p AND breach_H12<p → entry
#              3. Permutation test для winner selection
# Язык: Python 3.10+
# Обновлён: 2026-06-11
# Использование:
#   python -m ML.baseline.benchmark_fractal_stop_stage4_1
# =============================================================================

import argparse, json, os, sys
from collections import Counter
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
import xgboost as xgb

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from processing.label_signals import load_ohlc_index, evaluate_fractal_stop_trade

# ---------------------------------------------------------------------------
# Feature extraction (from Stage 3.x/4)
# ---------------------------------------------------------------------------

BASE_CHANNEL_KEYS = ['price', 'direction', 'front', 'back', 'strong', 'break', 'reverse', 'power',
                     'count', 'impulse']

CANONICAL_SPREAD = 0.20
MIN_TRADES_PER_YEAR = 30
N_PERMUTATION = 500
RANDOM_SEED = 42

# Grid
P_GRID = [0.3, 0.4, 0.5]
MIN_FAV_GRID = [0.3, 0.5]
MIN_RR_GRID = [1.0, 1.5]
TP_FRACTION_GRID = [0.4, 0.6]
CAP = 5.0


def load_split(path, purge_bars=12):
    df = pd.read_csv(path, sep=';')
    if purge_bars > 0 and len(df) > purge_bars:
        df = df.iloc[:-purge_bars]
    df['_year'] = pd.to_datetime(df['time'], format='%Y.%m.%d %H:%M', errors='coerce').dt.year
    return df


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
    hour_frac = times_dt.dt.hour.fillna(0).values + times_dt.dt.minute.fillna(0).values / 60.0
    hour_sin = np.sin(2 * np.pi * hour_frac / 24)
    hour_cos = np.cos(2 * np.pi * hour_frac / 24)
    dow = times_dt.dt.dayofweek.fillna(0).values.astype(float)
    dow_sin = np.sin(2 * np.pi * dow / 7)
    dow_cos = np.cos(2 * np.pi * dow / 7)
    return np.column_stack([hour_sin, hour_cos, dow_sin, dow_cos]), \
        ['hour_sin', 'hour_cos', 'dow_sin', 'dow_cos']


def profile_base_raw_plus_time(df):
    Xb, nb = _extract_base(df)
    Xt, nt = _extract_time(df)
    return np.column_stack([Xb, Xt]), nb + nt


# ---------------------------------------------------------------------------
# OHLC & entry prices
# ---------------------------------------------------------------------------

def compute_entry_prices(df, ohlc, times, time_idx):
    entry = np.full(len(df), np.nan, dtype=np.float64)
    for i, row in df.iterrows():
        try:
            row_dt = datetime.strptime(str(row['time']), '%Y.%m.%d %H:%M').replace(tzinfo=timezone.utc)
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


# ---------------------------------------------------------------------------
# Trade simulation (individual breach — same as Stage 4)
# ---------------------------------------------------------------------------

def simulate_trades_individual(df, entry_prices, breach_proba, fav_pred, ohlc, times, time_idx,
                               side, h, stop_offset, p=0.5, min_fav_val=0.5, min_rr=1.5,
                               tp_fraction=0.5, cap=5.0, spread=0.0):
    trade_direction = -1 if side == 'buy' else 1
    expected_fractal_dir = -1 if side == 'buy' else 1
    trades = []

    for i, row in df.iterrows():
        fractal0 = parse_trade_fractal0(row.get('fractal0'))
        if fractal0 is None or fractal0['direction'] != expected_fractal_dir:
            continue
        fractal_price = fractal0['price']

        try:
            row_dt = datetime.strptime(str(row['time']), '%Y.%m.%d %H:%M').replace(tzinfo=timezone.utc)
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

        if trade_direction == -1:
            stop_price = min(fractal_price, entry_price_val) - stop_offset * atr_val
            stop_val = (entry_price_val - stop_price) / atr_val
        else:
            stop_price = max(fractal_price, entry_price_val) + stop_offset * atr_val
            stop_val = (stop_price - entry_price_val) / atr_val
        if stop_val <= 0:
            continue

        tp_val_atr = min(pred_fav * tp_fraction, cap)
        if trade_direction == -1:
            tp_price = entry_price_val + tp_val_atr * atr_val
        else:
            tp_price = entry_price_val - tp_val_atr * atr_val

        if trade_direction == -1:
            entry_spread = entry_price_val + spread
            tp_price_spread = tp_price - spread
            stop_val_actual = (entry_spread - stop_price) / atr_val
        else:
            entry_spread = entry_price_val - spread
            tp_price_spread = tp_price + spread
            stop_val_actual = (stop_price - entry_spread) / atr_val
        if stop_val_actual <= 0:
            continue

        if pred_break >= p:
            continue
        if pred_fav < min_fav_val:
            continue
        if pred_fav / stop_val_actual < min_rr:
            continue

        bars_h = [(ohlc[times[k]][0], ohlc[times[k]][1],
                   ohlc[times[k]][2], ohlc[times[k]][3])
                  for k in range(idx0 + 1, idx0 + 1 + h)]
        outcome = evaluate_fractal_stop_trade(
            bars_h, trade_direction, entry_spread, stop_price, tp_price_spread, atr_val)

        year_val = row.get('_year')
        year_int = int(year_val) if not pd.isna(year_val) else None
        trades.append({
            'exit': outcome['exit'], 'pnl_val': outcome['pnl_val'],
            'stop_val': stop_val_actual,
            'pnl_r': outcome['pnl_val'] / stop_val_actual if stop_val_actual > 0 else outcome['pnl_val'],
            'ambiguous': outcome['ambiguous'], 'year': year_int, 'side': side,
        })
    return trades


# ---------------------------------------------------------------------------
# Trade simulation (combined breach: H6 AND H12)
# ---------------------------------------------------------------------------

def simulate_trades_combined(df, entry_prices, breach_H6_proba, breach_H12_proba, fav_pred,
                              ohlc, times, time_idx, side, stop_offset,
                              p=0.5, min_fav_val=0.5, min_rr=1.5,
                              tp_fraction=0.5, cap=5.0, spread=0.0):
    """Combined breach: entry requires BOTH breach_H6 < p AND breach_H12 < p.
    Trade horizon = H=12 (longer), fav target = H12."""
    h = 12
    trade_direction = -1 if side == 'buy' else 1
    expected_fractal_dir = -1 if side == 'buy' else 1
    trades = []

    for i, row in df.iterrows():
        fractal0 = parse_trade_fractal0(row.get('fractal0'))
        if fractal0 is None or fractal0['direction'] != expected_fractal_dir:
            continue
        fractal_price = fractal0['price']

        try:
            row_dt = datetime.strptime(str(row['time']), '%Y.%m.%d %H:%M').replace(tzinfo=timezone.utc)
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

        pb_h6 = breach_H6_proba[i]
        pb_h12 = breach_H12_proba[i]
        pred_fav = fav_pred[i]
        if np.isnan(pb_h6) or np.isnan(pb_h12) or np.isnan(pred_fav):
            continue

        if trade_direction == -1:
            stop_price = min(fractal_price, entry_price_val) - stop_offset * atr_val
            stop_val = (entry_price_val - stop_price) / atr_val
        else:
            stop_price = max(fractal_price, entry_price_val) + stop_offset * atr_val
            stop_val = (stop_price - entry_price_val) / atr_val
        if stop_val <= 0:
            continue

        tp_val_atr = min(pred_fav * tp_fraction, cap)
        if trade_direction == -1:
            tp_price = entry_price_val + tp_val_atr * atr_val
        else:
            tp_price = entry_price_val - tp_val_atr * atr_val

        if trade_direction == -1:
            entry_spread = entry_price_val + spread
            tp_price_spread = tp_price - spread
            stop_val_actual = (entry_spread - stop_price) / atr_val
        else:
            entry_spread = entry_price_val - spread
            tp_price_spread = tp_price + spread
            stop_val_actual = (stop_price - entry_spread) / atr_val
        if stop_val_actual <= 0:
            continue

        # Combined breach filter: BOTH below threshold
        if pb_h6 >= p or pb_h12 >= p:
            continue
        if pred_fav < min_fav_val:
            continue
        if pred_fav / stop_val_actual < min_rr:
            continue

        bars_h = [(ohlc[times[k]][0], ohlc[times[k]][1],
                   ohlc[times[k]][2], ohlc[times[k]][3])
                  for k in range(idx0 + 1, idx0 + 1 + h)]
        outcome = evaluate_fractal_stop_trade(
            bars_h, trade_direction, entry_spread, stop_price, tp_price_spread, atr_val)

        year_val = row.get('_year')
        year_int = int(year_val) if not pd.isna(year_val) else None
        trades.append({
            'exit': outcome['exit'], 'pnl_val': outcome['pnl_val'],
            'stop_val': stop_val_actual,
            'pnl_r': outcome['pnl_val'] / stop_val_actual if stop_val_actual > 0 else outcome['pnl_val'],
            'ambiguous': outcome['ambiguous'], 'year': year_int, 'side': side,
        })
    return trades


# ---------------------------------------------------------------------------
# Trade metrics
# ---------------------------------------------------------------------------

def compute_trade_metrics(trades):
    if not trades:
        return {'pf': 0.0, 'n_trades': 0, 'trades_per_year': 0, 'n_years': 0,
                'negative_years': 0, 'timeout_pct': 0.0, 'ambiguous_pct': 0.0}

    n_trades = len(trades)
    years_covered = sorted(set(t['year'] for t in trades if t['year'] is not None))
    n_years = len(years_covered) if years_covered else 1
    trades_per_year = n_trades / n_years if n_years > 0 else n_trades

    gross_profit = sum(max(0, t['pnl_val']) for t in trades)
    gross_loss = abs(sum(min(0, t['pnl_val']) for t in trades))
    pf = gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)

    exits = Counter(t['exit'] for t in trades)
    timeout_pct = exits.get('TIMEOUT', 0) / n_trades * 100 if n_trades else 0
    ambiguous_pct = sum(1 for t in trades if t['ambiguous']) / n_trades * 100 if n_trades else 0

    yearly = {}
    negative_years = 0
    for yr in years_covered:
        yr_trades = [t for t in trades if t['year'] == yr]
        if len(yr_trades) < 3:
            continue
        yr_profit = sum(max(0, t['pnl_val']) for t in yr_trades)
        yr_loss = abs(sum(min(0, t['pnl_val']) for t in yr_trades))
        yr_pf = yr_profit / yr_loss if yr_loss > 0 else (float('inf') if yr_profit > 0 else 0.0)
        yearly[yr] = {'pf': round(yr_pf, 3) if yr_pf != float('inf') else yr_pf,
                      'n': len(yr_trades)}
        if yr_pf < 1.0:
            negative_years += 1

    return {
        'pf': round(pf, 3) if pf != float('inf') else pf,
        'n_trades': n_trades, 'trades_per_year': round(trades_per_year, 1),
        'n_years': n_years, 'negative_years': negative_years,
        'timeout_pct': round(timeout_pct, 1), 'ambiguous_pct': round(ambiguous_pct, 1),
        'yearly': yearly,
    }


def bootstrap_pf(trades, n_iter=500, seed=RANDOM_SEED):
    if len(trades) < 20:
        return {'pf_median': None, 'pf_p05': None, 'pf_p95': None, 'n_trades': len(trades)}
    rng = np.random.RandomState(seed)
    pfs = []
    for _ in range(n_iter):
        sample_idx = rng.randint(0, len(trades), size=len(trades))
        gp = sum(max(0, trades[j]['pnl_val']) for j in sample_idx)
        gl = abs(sum(min(0, trades[j]['pnl_val']) for j in sample_idx))
        pf = gp / gl if gl > 0 else (float('inf') if gp > 0 else 0.0)
        pfs.append(pf)
    pfs = np.array(pfs)
    finite = pfs[np.isfinite(pfs)]
    return {
        'pf_median': round(float(np.median(finite)), 3) if len(finite) > 0 else None,
        'pf_p05': round(float(np.percentile(finite, 5)), 3) if len(finite) > 0 else None,
        'pf_p95': round(float(np.percentile(finite, 95)), 3) if len(finite) > 0 else None,
        'n_trades': len(trades),
    }


def permutation_test_pf(sim_fn, sim_kwargs, best_trades_obs, best_params, n_iter=N_PERMUTATION):
    """Permutation test: shuffle breach probas, re-run trade sim, compute PF.

    sim_fn: simulate_trades_combined or simulate_trades_individual
    sim_kwargs: all keyword arguments EXCEPT breach probas (provided separately)
    best_trades_obs: observed trades for the best grid combo
    best_params: dict with grid params {p, min_fav_val, min_rr, tp_fraction}
    Returns: p-value (fraction of permuted PFs >= observed PF)
    """
    obs_pf = compute_trade_metrics(best_trades_obs)['pf']
    if obs_pf == 0 or obs_pf == float('inf'):
        return {'p_value': None, 'obs_pf': obs_pf, 'n_perm': 0,
                'note': 'obs_pf_invalid'}

    # Determine breach arrays from kwargs
    breach_keys = [k for k in sim_kwargs if k.startswith('breach')]
    if not breach_keys:
        return {'p_value': None, 'obs_pf': obs_pf, 'n_perm': 0,
                'note': 'no_breach_keys'}

    breach_arrays = {k: sim_kwargs[k].copy() for k in breach_keys}
    perm_kwargs = dict(sim_kwargs)

    rng = np.random.RandomState(RANDOM_SEED)
    count_ge = 0
    perm_pfs = []

    for _ in range(n_iter):
        for k in breach_keys:
            perm_kwargs[k] = rng.permutation(breach_arrays[k])

        perm_trades = sim_fn(**perm_kwargs)
        perm_metrics = compute_trade_metrics(perm_trades)
        perm_pf = perm_metrics['pf']
        if perm_pf == float('inf'):
            count_ge += 1
        elif perm_pf >= obs_pf:
            count_ge += 1
        perm_pfs.append(perm_pf if perm_pf != float('inf') else np.inf)

    p_value = count_ge / n_iter

    finite_perms = [p for p in perm_pfs if np.isfinite(p)]
    return {
        'p_value': round(p_value, 4),
        'obs_pf': obs_pf,
        'n_perm': n_iter,
        'perm_pf_median': round(float(np.median(finite_perms)), 3) if finite_perms else None,
        'perm_pf_p95': round(float(np.percentile(finite_perms, 95)), 3) if finite_perms else None,
        'perm_pf_max': round(float(np.max(finite_perms)), 3) if finite_perms else None,
        'count_ge': count_ge,
    }


# ---------------------------------------------------------------------------
# XGBoost training
# ---------------------------------------------------------------------------

def train_xgb_clf(X_train, y_train, X_val, y_val, random_state=RANDOM_SEED):
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
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    return model


def train_xgb_reg(X_train, y_train, X_val, y_val, random_state=RANDOM_SEED):
    model = xgb.XGBRegressor(
        n_estimators=200, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        objective='reg:squarederror', eval_metric='rmse',
        early_stopping_rounds=20, random_state=random_state,
        n_jobs=-1, verbosity=0,
    )
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    return model


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Stage 4.1: XGBoost-fav + combined breach + permutation test')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--ohlc', default='DATA/XAUUSD_H1_OHLC.csv')
    parser.add_argument('--purge-bars', type=int, default=12)
    parser.add_argument('--output-json', default='ML/reports/stage4_1.json')
    parser.add_argument('--spread', type=float, default=CANONICAL_SPREAD)
    args = parser.parse_args()

    print('Stage 4.1: XGBoost-fav + combined breach H6/H12 + permutation test')
    print(f'Loading data...')

    train_df = load_split(args.train, args.purge_bars)
    val_df = load_split(args.val, args.purge_bars)
    print(f'  Train: {len(train_df)} rows, Val: {len(val_df)} rows')

    ohlc, times, time_idx = load_ohlc_index(args.ohlc)
    print(f'  OHLC bars: {len(times)}')

    print('Computing entry prices (val)...')
    entry_prices_val = compute_entry_prices(val_df, ohlc, times, time_idx)
    print(f'  Valid entries: {(~np.isnan(entry_prices_val)).sum()}/{len(val_df)}')

    # Extract features: base_raw_plus_time for breach, base_raw for fav
    print('Extracting features...')
    X_train_br, _ = profile_base_raw_plus_time(train_df)
    X_val_br, _ = profile_base_raw_plus_time(val_df)
    X_train_fav, _ = _extract_base(train_df)
    X_val_fav, _ = _extract_base(val_df)
    print(f'  Breach features: {X_train_br.shape[1]}, Fav features: {X_train_fav.shape[1]}')

    # -----------------------------------------------------------------------
    # Part A: Individual sell targets with XGBoost-fav (baseline vs Stage 4 RF-fav)
    # -----------------------------------------------------------------------

    INDIVIDUAL = {
        'sell_H6_off02':  {'breach': 'sell_stop_broken_H6_off02_flag',  'h': 6,  'off': 0.2, 'side': 'sell', 'fav': 'target_sell_H6_val'},
        'sell_H6_off05':  {'breach': 'sell_stop_broken_H6_off05_flag',  'h': 6,  'off': 0.5, 'side': 'sell', 'fav': 'target_sell_H6_val'},
        'sell_H12_off02': {'breach': 'sell_stop_broken_H12_off02_flag', 'h': 12, 'off': 0.2, 'side': 'sell', 'fav': 'target_sell_H12_val'},
        'sell_H12_off05': {'breach': 'sell_stop_broken_H12_off05_flag', 'h': 12, 'off': 0.5, 'side': 'sell', 'fav': 'target_sell_H12_val'},
    }

    individual_results = {}

    for label, cfg in INDIVIDUAL.items():
        print(f'\n{"="*60}')
        print(f'Individual: {label}  (h={cfg["h"]}, off={cfg["off"]}, side={cfg["side"]})')
        print(f'{"="*60}')

        breach_col = cfg['breach']
        fav_col = cfg['fav']
        h = cfg['h']
        off = cfg['off']
        side = cfg['side']

        # Train XGBoost breach
        y_train_b = train_df[breach_col].values
        y_val_b = val_df[breach_col].values
        train_mask_b = ~np.isnan(y_train_b)
        val_mask_b = ~np.isnan(y_val_b)
        print(f'  Breach XGBoost: train_n={train_mask_b.sum()}, pos={y_train_b[train_mask_b].sum():.0f}')
        breach_model = train_xgb_clf(
            X_train_br[train_mask_b], y_train_b[train_mask_b],
            X_val_br[val_mask_b], y_val_b[val_mask_b])
        breach_auc = roc_auc_score(y_val_b[val_mask_b],
                                    breach_model.predict_proba(X_val_br[val_mask_b])[:, 1])
        print(f'  Breach AUC: {breach_auc:.4f}')

        # Train XGBoost fav
        y_train_f = train_df[fav_col].values
        y_val_f = val_df[fav_col].values
        train_mask_f = ~np.isnan(y_train_f)
        val_mask_f = ~np.isnan(y_val_f)
        print(f'  Fav XGBoost: train_n={train_mask_f.sum()}')
        fav_model = train_xgb_reg(
            X_train_fav[train_mask_f], y_train_f[train_mask_f],
            X_val_fav[val_mask_f], y_val_f[val_mask_f])

        # Intersection mask
        inter = val_mask_b & val_mask_f
        if inter.sum() < 50:
            print(f'  SKIP: intersection n={inter.sum()}')
            continue

        breach_proba = breach_model.predict_proba(X_val_br[inter])[:, 1]
        fav_pred = fav_model.predict(X_val_fav[inter])
        val_masked = val_df[inter].reset_index(drop=True)
        entry_masked = entry_prices_val[inter]

        # Grid search
        best_grid = None
        best_metrics = None
        best_trades = None
        print(f'  Grid search ({len(P_GRID)}×{len(MIN_FAV_GRID)}×{len(MIN_RR_GRID)}×{len(TP_FRACTION_GRID)} combos)...')

        for p in P_GRID:
            for mf in MIN_FAV_GRID:
                for rr in MIN_RR_GRID:
                    for tf in TP_FRACTION_GRID:
                        trades = simulate_trades_individual(
                            val_masked, entry_masked, breach_proba, fav_pred,
                            ohlc, times, time_idx,
                            side=side, h=h, stop_offset=off,
                            p=p, min_fav_val=mf, min_rr=rr,
                            tp_fraction=tf, cap=CAP, spread=args.spread)
                        metrics = compute_trade_metrics(trades)
                        if metrics['trades_per_year'] >= MIN_TRADES_PER_YEAR:
                            if best_metrics is None or metrics['pf'] > best_metrics['pf']:
                                best_metrics = metrics
                                best_grid = {'p': p, 'min_fav_val': mf, 'min_rr': rr, 'tp_fraction': tf}
                                best_trades = trades

        if best_grid is None:
            print(f'  FAIL: no combo with trades/year >= {MIN_TRADES_PER_YEAR}')
            individual_results[label] = {'status': 'FAIL', 'breach_auc': round(breach_auc, 4)}
            continue

        bs = bootstrap_pf(best_trades)
        print(f'  Best: p={best_grid["p"]} mf={best_grid["min_fav_val"]} '
              f'rr={best_grid["min_rr"]} tf={best_grid["tp_fraction"]}')
        print(f'  PF={best_metrics["pf"]}  trades={best_metrics["n_trades"]}  '
              f't/yr={best_metrics["trades_per_year"]}  neg_y={best_metrics["negative_years"]}')
        if bs.get('pf_median'):
            print(f'  BS: median={bs["pf_median"]}  p05={bs["pf_p05"]}  p95={bs["pf_p95"]}')

        individual_results[label] = {
            'breach_auc': round(breach_auc, 4),
            'best_grid': best_grid,
            'trade_metrics': best_metrics,
            'bootstrap': bs,
        }

    # -----------------------------------------------------------------------
    # Part B: Combined breach H6+H12 (sell only)
    # -----------------------------------------------------------------------

    COMBINED = {
        'sell_comb_off02': {
            'H6_breach': 'sell_stop_broken_H6_off02_flag',
            'H12_breach': 'sell_stop_broken_H12_off02_flag',
            'off': 0.2, 'side': 'sell', 'fav': 'target_sell_H12_val',
        },
        'sell_comb_off05': {
            'H6_breach': 'sell_stop_broken_H6_off05_flag',
            'H12_breach': 'sell_stop_broken_H12_off05_flag',
            'off': 0.5, 'side': 'sell', 'fav': 'target_sell_H12_val',
        },
    }

    combined_results = {}

    for label, cfg in COMBINED.items():
        print(f'\n{"="*60}')
        print(f'Combined: {label}  (off={cfg["off"]}, side={cfg["side"]})')
        print(f'{"="*60}')

        side = cfg['side']
        off = cfg['off']

        # Train H6 breach
        y_train_h6 = train_df[cfg['H6_breach']].values
        y_val_h6 = val_df[cfg['H6_breach']].values
        tmask_h6 = ~np.isnan(y_train_h6)
        vmask_h6 = ~np.isnan(y_val_h6)
        breach_H6 = train_xgb_clf(
            X_train_br[tmask_h6], y_train_h6[tmask_h6],
            X_val_br[vmask_h6], y_val_h6[vmask_h6])
        auc_h6 = roc_auc_score(y_val_h6[vmask_h6],
                                breach_H6.predict_proba(X_val_br[vmask_h6])[:, 1])

        # Train H12 breach
        y_train_h12 = train_df[cfg['H12_breach']].values
        y_val_h12 = val_df[cfg['H12_breach']].values
        tmask_h12 = ~np.isnan(y_train_h12)
        vmask_h12 = ~np.isnan(y_val_h12)
        breach_H12 = train_xgb_clf(
            X_train_br[tmask_h12], y_train_h12[tmask_h12],
            X_val_br[vmask_h12], y_val_h12[vmask_h12])
        auc_h12 = roc_auc_score(y_val_h12[vmask_h12],
                                 breach_H12.predict_proba(X_val_br[vmask_h12])[:, 1])

        print(f'  Breach AUC: H6={auc_h6:.4f}  H12={auc_h12:.4f}')

        # Train XGBoost fav (H12)
        y_train_f = train_df[cfg['fav']].values
        y_val_f = val_df[cfg['fav']].values
        tmask_f = ~np.isnan(y_train_f)
        vmask_f = ~np.isnan(y_val_f)
        fav_model = train_xgb_reg(
            X_train_fav[tmask_f], y_train_f[tmask_f],
            X_val_fav[vmask_f], y_val_f[vmask_f])
        print(f'  Fav XGBoost: train_n={tmask_f.sum()}')

        # Intersection of all three masks
        inter = vmask_h6 & vmask_h12 & vmask_f
        if inter.sum() < 50:
            print(f'  SKIP: intersection n={inter.sum()}')
            continue

        breach_H6_proba = breach_H6.predict_proba(X_val_br[inter])[:, 1]
        breach_H12_proba = breach_H12.predict_proba(X_val_br[inter])[:, 1]
        fav_pred = fav_model.predict(X_val_fav[inter])
        val_masked = val_df[inter].reset_index(drop=True)
        entry_masked = entry_prices_val[inter]

        # Grid search (combined)
        best_grid = None
        best_metrics = None
        best_trades = None
        print(f'  Grid search ({len(P_GRID)}×{len(MIN_FAV_GRID)}×{len(MIN_RR_GRID)}×{len(TP_FRACTION_GRID)} combos)...')

        for p in P_GRID:
            for mf in MIN_FAV_GRID:
                for rr in MIN_RR_GRID:
                    for tf in TP_FRACTION_GRID:
                        trades = simulate_trades_combined(
                            val_masked, entry_masked,
                            breach_H6_proba, breach_H12_proba, fav_pred,
                            ohlc, times, time_idx,
                            side=side, stop_offset=off,
                            p=p, min_fav_val=mf, min_rr=rr,
                            tp_fraction=tf, cap=CAP, spread=args.spread)
                        metrics = compute_trade_metrics(trades)
                        if metrics['trades_per_year'] >= MIN_TRADES_PER_YEAR:
                            if best_metrics is None or metrics['pf'] > best_metrics['pf']:
                                best_metrics = metrics
                                best_grid = {'p': p, 'min_fav_val': mf, 'min_rr': rr, 'tp_fraction': tf}
                                best_trades = trades

        if best_grid is None:
            print(f'  FAIL: no combo with trades/year >= {MIN_TRADES_PER_YEAR}')
            combined_results[label] = {
                'status': 'FAIL',
                'breach_auc_H6': round(auc_h6, 4),
                'breach_auc_H12': round(auc_h12, 4),
            }
            continue

        bs = bootstrap_pf(best_trades)
        print(f'  Best: p={best_grid["p"]} (both H6+H12) mf={best_grid["min_fav_val"]} '
              f'rr={best_grid["min_rr"]} tf={best_grid["tp_fraction"]}')
        print(f'  PF={best_metrics["pf"]}  trades={best_metrics["n_trades"]}  '
              f't/yr={best_metrics["trades_per_year"]}  neg_y={best_metrics["negative_years"]}')
        if bs.get('pf_median'):
            print(f'  BS: median={bs["pf_median"]}  p05={bs["pf_p05"]}  p95={bs["pf_p95"]}')

        # Permutation test
        print(f'  Permutation test ({N_PERMUTATION} iter)...')
        sim_kwargs = dict(
            df=val_masked, entry_prices=entry_masked,
            breach_H6_proba=breach_H6_proba,
            breach_H12_proba=breach_H12_proba,
            fav_pred=fav_pred,
            ohlc=ohlc, times=times, time_idx=time_idx,
            side=side, stop_offset=off,
            p=best_grid['p'], min_fav_val=best_grid['min_fav_val'],
            min_rr=best_grid['min_rr'], tp_fraction=best_grid['tp_fraction'],
            cap=CAP, spread=args.spread,
        )
        perm_result = permutation_test_pf(
            simulate_trades_combined, sim_kwargs,
            best_trades, best_grid, n_iter=N_PERMUTATION)
        p_val_str = f'{perm_result["p_value"]:.4f}' if perm_result.get('p_value') else 'N/A'
        print(f'  Perm p-value: {p_val_str}  (obs PF={perm_result["obs_pf"]}, '
              f'perm median={perm_result.get("perm_pf_median", "N/A")}, '
              f'perm p95={perm_result.get("perm_pf_p95", "N/A")})')

        combined_results[label] = {
            'breach_auc_H6': round(auc_h6, 4),
            'breach_auc_H12': round(auc_h12, 4),
            'best_grid': best_grid,
            'trade_metrics': best_metrics,
            'bootstrap': bs,
            'permutation_test': perm_result,
        }

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------

    print(f'\n{"="*90}')
    print('STAGE 4.1 SUMMARY')
    print(f'{"="*90}')

    print('\n--- Individual (XGBoost-fav) ---')
    print(f'{"Target":>20s} | {"AUC":>6s} | {"PF":>8s} | {"T/Yr":>6s} | {"NegY":>5s} | '
          f'{"BS_med":>8s} | {"BS_p05":>8s} | params')
    print('-' * 100)
    for label in sorted(individual_results.keys()):
        r = individual_results[label]
        if r.get('status') == 'FAIL':
            print(f'{label:>20s} | {"FAIL":>6s}')
            continue
        m = r['trade_metrics']
        bs = r['bootstrap']
        pf_str = f'{m["pf"]:.3f}' if m['pf'] != float('inf') else 'inf'
        bmed = f'{bs["pf_median"]:.3f}' if bs.get('pf_median') else 'N/A'
        bp05 = f'{bs["pf_p05"]:.3f}' if bs.get('pf_p05') else 'N/A'
        g = r['best_grid']
        ps = f'p={g["p"]} mf={g["min_fav_val"]} rr={g["min_rr"]} tf={g["tp_fraction"]}'
        print(f'{label:>20s} | {r["breach_auc"]:.4f} | {pf_str:>8s} | '
              f'{m["trades_per_year"]:>6.1f} | {m["negative_years"]:>5d} | '
              f'{bmed:>8s} | {bp05:>8s} | {ps}')

    print('\n--- Combined (H6 AND H12) ---')
    print(f'{"Target":>20s} | {"AUC6":>6s} | {"AUC12":>6s} | {"PF":>8s} | {"T/Yr":>6s} | '
          f'{"NegY":>5s} | {"BS_p05":>8s} | {"perm_p":>8s} | params')
    print('-' * 110)
    for label in sorted(combined_results.keys()):
        r = combined_results[label]
        if r.get('status') == 'FAIL':
            print(f'{label:>20s} | {"FAIL":>6s}')
            continue
        m = r['trade_metrics']
        bs = r['bootstrap']
        pf_str = f'{m["pf"]:.3f}' if m['pf'] != float('inf') else 'inf'
        bp05 = f'{bs["pf_p05"]:.3f}' if bs.get('pf_p05') else 'N/A'
        pt = r.get('permutation_test', {})
        pv = f'{pt["p_value"]:.4f}' if pt.get('p_value') is not None else 'N/A'
        g = r['best_grid']
        ps = f'p={g["p"]} mf={g["min_fav_val"]} rr={g["min_rr"]} tf={g["tp_fraction"]}'
        print(f'{label:>20s} | {r["breach_auc_H6"]:.4f} | {r["breach_auc_H12"]:.4f} | '
              f'{pf_str:>8s} | {m["trades_per_year"]:>6.1f} | {m["negative_years"]:>5d} | '
              f'{bp05:>8s} | {pv:>8s} | {ps}')

    # Stage 4 comparison (load baseline)
    stage4_baseline = {}
    try:
        with open('ML/reports/stage4_trade.json') as f:
            s4 = json.load(f)
        for t in INDIVIDUAL:
            if t in s4['results'] and s4['results'][t].get('trade_metrics'):
                stage4_baseline[t] = s4['results'][t]['trade_metrics']['pf']
    except FileNotFoundError:
        pass

    if stage4_baseline:
        print('\n--- ΔPF vs Stage 4 (RF-fav → XGBoost-fav) ---')
        for label in sorted(individual_results.keys()):
            r = individual_results[label]
            if r.get('status') == 'FAIL':
                continue
            pf41 = r['trade_metrics']['pf']
            pf4 = stage4_baseline.get(label, 0)
            dpf = pf41 - pf4
            dpf_str = f'{dpf:+.3f}' if dpf != float('inf') else 'inf'
            print(f'  {label:>20s}: Stage4={pf4:.3f}  Stage4.1={pf41:.3f}  Δ={dpf_str}')

    # Save
    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    output = {
        'config': {
            'profile': 'base_raw_plus_time',
            'spread': args.spread,
            'purge_bars': args.purge_bars,
            'grid': {'p': P_GRID, 'min_fav': MIN_FAV_GRID,
                     'min_rr': MIN_RR_GRID, 'tp_fraction': TP_FRACTION_GRID},
            'n_permutation': N_PERMUTATION,
            'fav_model': 'XGBoostRegressor',
        },
        'individual': individual_results,
        'combined': combined_results,
        'note': 'Stage 4.1: XGBoost-fav + combined breach H6/H12 + permutation test',
    }
    with open(args.output_json, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f'\nSaved: {args.output_json}')


if __name__ == '__main__':
    main()
