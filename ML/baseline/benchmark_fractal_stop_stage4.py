# =============================================================================
# Файл: ML/baseline/benchmark_fractal_stop_stage4.py
# Назначение: Stage 4 — validation-only торговый слой
#              XGBoost breach + RF fav, trade simulation, PF-optimised grid search.
#              Primary: base_raw_plus_time, Control: relative_geometry_clean.
#              Winner только по validation, test не открывать.
# Язык: Python 3.10+
# Обновлён: 2026-06-11
# Использование:
#   python -m ML.baseline.benchmark_fractal_stop_stage4
# =============================================================================

import argparse, json, os, sys
from collections import Counter
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import roc_auc_score
import xgboost as xgb

# Insert project root for label_signals import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from processing.label_signals import load_ohlc_index, evaluate_fractal_stop_trade

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_CHANNEL_KEYS = ['price', 'direction', 'front', 'back', 'strong', 'break', 'reverse', 'power',
                     'count', 'impulse']

BREACH_TARGETS = {
    6: {0.2: {'buy': 'buy_stop_broken_H6_off02_flag', 'sell': 'sell_stop_broken_H6_off02_flag'},
        0.5: {'buy': 'buy_stop_broken_H6_off05_flag', 'sell': 'sell_stop_broken_H6_off05_flag'}},
    12: {0.2: {'buy': 'buy_stop_broken_H12_off02_flag', 'sell': 'sell_stop_broken_H12_off02_flag'},
         0.5: {'buy': 'buy_stop_broken_H12_off05_flag', 'sell': 'sell_stop_broken_H12_off05_flag'}},
}

FAV_TARGETS = {
    6: {'buy': 'target_buy_H6_val', 'sell': 'target_sell_H6_val'},
    12: {'buy': 'target_buy_H12_val', 'sell': 'target_sell_H12_val'},
}

# Малый grid: 3×2×2×2 = 24 комбинации
P_GRID = [0.3, 0.4, 0.5]
MIN_FAV_GRID = [0.3, 0.5]
MIN_RR_GRID = [1.0, 1.5]
TP_FRACTION_GRID = [0.4, 0.6]
CAP = 5.0
CANONICAL_SPREAD = 0.20
N_BOOTSTRAP = 500
MIN_TRADES_PER_YEAR = 30


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_split(path, purge_bars=12):
    df = pd.read_csv(path, sep=';')
    if purge_bars > 0 and len(df) > purge_bars:
        df = df.iloc[:-purge_bars]
    df['_year'] = pd.to_datetime(df['time'], format='%Y.%m.%d %H:%M', errors='coerce').dt.year
    return df


# ---------------------------------------------------------------------------
# Feature extraction (from Stage 3.1/3.2)
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


def _extract_price_normalized(df, n_levels=100):
    features, names = [], []
    atr_row = pd.to_numeric(df['ATR'], errors='coerce').fillna(1.0).values
    atr_clipped = np.maximum(atr_row, 0.001)
    f0_parts = df['fractal0'].astype(str).str.split(':', expand=True)
    f0_price = pd.to_numeric(f0_parts[1], errors='coerce').fillna(0.0).values
    for level in range(n_levels):
        col = f'fractal{level}'
        if col not in df.columns:
            break
        parts = df[col].astype(str).str.split(':', expand=True)
        idx = {'price': 1, 'direction': 2, 'front': 3, 'back': 4, 'strong': 5,
               'break': 6, 'reverse': 7, 'power': 8, 'count': 9, 'impulse': 10}
        for key in BASE_CHANNEL_KEYS:
            vals = pd.to_numeric(parts[idx[key]], errors='coerce').fillna(0.0).values
            if key == 'price':
                dir_raw = pd.to_numeric(parts[2], errors='coerce').values
                valid = (np.nan_to_num(dir_raw, nan=0.0) != 0)
                vals = np.where(valid, (vals - f0_price) / atr_clipped, 0.0)
            features.append(vals.astype(np.float64))
            names.append(f'f{level}_{key}')
    if 'ATR' in df.columns:
        features.append(df['ATR'].values.astype(np.float64))
        names.append('ATR')
    return np.column_stack(features), names


def _extract_density(df, n_levels=100, excl_f0=True):
    atr_row = pd.to_numeric(df['ATR'], errors='coerce').fillna(1.0).values
    atr_clipped = np.maximum(atr_row, 0.001)
    f0_parts = df['fractal0'].astype(str).str.split(':', expand=True)
    f0_price = pd.to_numeric(f0_parts[1], errors='coerce').fillna(0.0).values
    density = np.zeros((len(df), 6), dtype=np.float64)
    start_level = 1 if excl_f0 else 0
    for lvl in range(start_level, n_levels):
        col = f'fractal{lvl}'
        if col not in df.columns:
            break
        parts = df[col].astype(str).str.split(':', expand=True)
        price_v = pd.to_numeric(parts[1], errors='coerce').fillna(0.0).values
        dir_v = pd.to_numeric(parts[2], errors='coerce').fillna(0).values
        valid = (dir_v != 0)
        if not valid.any():
            continue
        dist = np.abs(price_v - f0_price)
        for b_idx, b in enumerate([1.0, 2.0, 3.0]):
            within = valid & (dist <= b * atr_clipped)
            density[:, b_idx] += (within & (dir_v == 1)).astype(np.float64)
            density[:, b_idx + 3] += (within & (dir_v == -1)).astype(np.float64)
    names = []
    for b in [1, 2, 3]:
        names.extend([f'density_peaks_atr{b}', f'density_valleys_atr{b}'])
    return density, names


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


# Profile functions
def profile_base_raw(df):
    return _extract_base(df)


def profile_base_raw_plus_time(df):
    Xb, nb = _extract_base(df)
    Xt, nt = _extract_time(df)
    return np.column_stack([Xb, Xt]), nb + nt


def profile_relative_geometry_clean(df):
    X, names = _extract_price_normalized(df)
    Xd, nd = _extract_density(df, excl_f0=True)
    Xt, nt = _extract_time(df)
    return np.column_stack([X, Xd, Xt]), names + nd + nt


# ---------------------------------------------------------------------------
# OHLC & entry prices (adapted from Stage 2)
# ---------------------------------------------------------------------------

def compute_entry_prices(df, ohlc, times, time_idx):
    """Entry price = Open следующего бара для каждой строки."""
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
    """Извлечь price/direction из fractal0 (23 поля через ':')."""
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
# Trade simulation (adapted from Stage 2 benchmark_fractal_stop_fav.py)
# ---------------------------------------------------------------------------

def simulate_trades(df, entry_prices, breach_proba, fav_pred, ohlc, times, time_idx,
                    side, h, stop_offset, p=0.5, min_fav_val=0.5, min_rr=1.5,
                    tp_fraction=0.5, cap=5.0, spread=0.0):
    trade_direction = -1 if side == 'buy' else 1
    expected_fractal_dir = -1 if side == 'buy' else 1
    trades = []

    for i, row in df.iterrows():
        fractal0 = parse_trade_fractal0(row.get('fractal0'))
        if fractal0 is None:
            continue
        if fractal0['direction'] != expected_fractal_dir:
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

        # Stop price
        if trade_direction == -1:
            stop_price = min(fractal_price, entry_price_val) - stop_offset * atr_val
            stop_val = (entry_price_val - stop_price) / atr_val
        else:
            stop_price = max(fractal_price, entry_price_val) + stop_offset * atr_val
            stop_val = (stop_price - entry_price_val) / atr_val

        if stop_val <= 0:
            continue

        # TP price
        tp_val_atr = min(pred_fav * tp_fraction, cap)
        if trade_direction == -1:
            tp_price = entry_price_val + tp_val_atr * atr_val
        else:
            tp_price = entry_price_val - tp_val_atr * atr_val

        # Apply spread
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

        # Trade filters
        if pred_break >= p:
            continue
        if pred_fav < min_fav_val:
            continue
        if pred_fav / stop_val_actual < min_rr:
            continue

        # Extract OHLC bars
        bars_h = [(ohlc[times[k]][0], ohlc[times[k]][1],
                   ohlc[times[k]][2], ohlc[times[k]][3])
                  for k in range(idx0 + 1, idx0 + 1 + h)]

        outcome = evaluate_fractal_stop_trade(
            bars_h, trade_direction, entry_spread, stop_price, tp_price_spread, atr_val)

        year_val = row.get('_year')
        year_int = int(year_val) if not pd.isna(year_val) else None

        trades.append({
            'exit': outcome['exit'],
            'pnl_val': outcome['pnl_val'],
            'stop_val': stop_val_actual,
            'pnl_r': outcome['pnl_val'] / stop_val_actual if stop_val_actual > 0 else outcome['pnl_val'],
            'ambiguous': outcome['ambiguous'],
            'year': year_int,
            'side': side,
        })

    return trades


def compute_trade_metrics(trades):
    if not trades:
        return {'pf': 0.0, 'n_trades': 0, 'trades_per_year': 0, 'n_years': 0,
                'negative_years': 0, 'timeout_pct': 0.0, 'ambiguous_pct': 0.0,
                'pf_buy': 0.0, 'pf_sell': 0.0}

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

    # Yearly breakdown
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

    # Buy/Sell breakdown
    buy_trades = [t for t in trades if t.get('side') == 'buy']
    sell_trades = [t for t in trades if t.get('side') == 'sell']
    bp = sum(max(0, t['pnl_val']) for t in buy_trades)
    bl = abs(sum(min(0, t['pnl_val']) for t in buy_trades))
    pf_buy = bp / bl if bl > 0 else (float('inf') if bp > 0 else 0.0)
    sp = sum(max(0, t['pnl_val']) for t in sell_trades)
    sl = abs(sum(min(0, t['pnl_val']) for t in sell_trades))
    pf_sell = sp / sl if sl > 0 else (float('inf') if sp > 0 else 0.0)

    return {
        'pf': round(pf, 3) if pf != float('inf') else pf,
        'n_trades': n_trades, 'trades_per_year': round(trades_per_year, 1),
        'n_years': n_years, 'negative_years': negative_years,
        'timeout_pct': round(timeout_pct, 1), 'ambiguous_pct': round(ambiguous_pct, 1),
        'pf_buy': round(pf_buy, 3) if pf_buy != float('inf') else pf_buy,
        'pf_sell': round(pf_sell, 3) if pf_sell != float('inf') else pf_sell,
        'yearly': yearly,
    }


def bootstrap_pf(trades, n_iter=N_BOOTSTRAP, seed=42):
    """Bootstrap PF distribution: median, 5%, 95%."""
    if len(trades) < 20:
        return {'pf_median': None, 'pf_p05': None, 'pf_p95': None, 'n_trades': len(trades)}
    rng = np.random.RandomState(seed)
    pfs = []
    for _ in range(n_iter):
        sample = [trades[i] for i in rng.randint(0, len(trades), size=len(trades))]
        gp = sum(max(0, t['pnl_val']) for t in sample)
        gl = abs(sum(min(0, t['pnl_val']) for t in sample))
        pf = gp / gl if gl > 0 else (float('inf') if gp > 0 else 0.0)
        pfs.append(pf)
    pfs = np.array(pfs)
    finite_pfs = pfs[np.isfinite(pfs)]
    return {
        'pf_median': round(float(np.median(finite_pfs)), 3) if len(finite_pfs) > 0 else None,
        'pf_p05': round(float(np.percentile(finite_pfs, 5)), 3) if len(finite_pfs) > 0 else None,
        'pf_p95': round(float(np.percentile(finite_pfs, 95)), 3) if len(finite_pfs) > 0 else None,
        'pf_inf_pct': round(float((~np.isfinite(pfs)).sum() / len(pfs) * 100), 1),
        'n_trades': len(trades),
    }


# ---------------------------------------------------------------------------
# Model training
# ---------------------------------------------------------------------------

def train_xgb_breach(X_train, y_train, X_val, y_val, random_state=42):
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


def train_rf_fav(X_train, y_train, random_state=42):
    model = RandomForestRegressor(
        n_estimators=200, max_depth=12, min_samples_leaf=50,
        random_state=random_state, n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Stage 4: XGBoost breach + trade simulation')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--ohlc', default='DATA/XAUUSD_H1_OHLC.csv')
    parser.add_argument('--purge-bars', type=int, default=12)
    parser.add_argument('--output-json', default='ML/reports/stage4_trade.json')
    parser.add_argument('--spread', type=float, default=CANONICAL_SPREAD)
    parser.add_argument('--profile', default='base_raw_plus_time',
                        choices=['base_raw_plus_time', 'relative_geometry_clean'])
    args = parser.parse_args()

    profile_fn = {'base_raw_plus_time': profile_base_raw_plus_time,
                  'relative_geometry_clean': profile_relative_geometry_clean}[args.profile]

    print(f'Stage 4: profile={args.profile}, spread={args.spread}')
    print(f'Loading data...')

    train_df = load_split(args.train, args.purge_bars)
    val_df = load_split(args.val, args.purge_bars)
    print(f'  Train: {len(train_df)} rows, Val: {len(val_df)} rows')

    print(f'Loading OHLC: {args.ohlc}')
    ohlc, times, time_idx = load_ohlc_index(args.ohlc)
    print(f'  OHLC bars: {len(times)}')

    print('Computing entry prices (val)...')
    entry_prices_val = compute_entry_prices(val_df, ohlc, times, time_idx)
    valid_entry = (~np.isnan(entry_prices_val)).sum()
    print(f'  Valid entries: {valid_entry}/{len(val_df)}')

    # Extract features: breach uses profile, fav uses base_raw
    print('Extracting breach features...')
    X_train_breach, _ = profile_fn(train_df)
    X_val_breach, _ = profile_fn(val_df)
    print(f'  Breach features: {X_train_breach.shape[1]}')

    print('Extracting fav features (base_raw)...')
    X_train_fav, _ = profile_base_raw(train_df)
    X_val_fav, _ = profile_base_raw(val_df)

    # Results per (h, off, side)
    all_results = {}
    grid_summary = []

    for h in (6, 12):
        for off in (0.2, 0.5):
            for side in ('buy', 'sell'):
                target_col = BREACH_TARGETS[h][off][side]
                fav_col = FAV_TARGETS[h][side]
                label = f'{side}_H{h}_off{int(off*10):02d}'

                print(f'\n{"="*60}')
                print(f'Target: {label}  (breach={target_col}, fav={fav_col})')
                print(f'{"="*60}')

                # Prepare breach data
                y_train_b = train_df[target_col].values
                y_val_b = val_df[target_col].values
                train_mask_b = ~np.isnan(y_train_b)
                val_mask_b = ~np.isnan(y_val_b)
                if train_mask_b.sum() < 50:
                    print(f'  SKIP: train n={train_mask_b.sum()}')
                    continue

                # Train breach XGBoost
                print(f'  Training XGBoost breach (pos={y_train_b[train_mask_b].sum():.0f})...')
                breach_model = train_xgb_breach(
                    X_train_breach[train_mask_b], y_train_b[train_mask_b],
                    X_val_breach[val_mask_b], y_val_b[val_mask_b])
                breach_proba = breach_model.predict_proba(X_val_breach[val_mask_b])[:, 1]

                # Breach AUC
                breach_auc = roc_auc_score(y_val_b[val_mask_b], breach_proba)
                print(f'  Breach AUC: {breach_auc:.4f}  (iters={getattr(breach_model, "best_iteration", breach_model.n_estimators)})')

                # Train fav RF
                y_train_f = train_df[fav_col].values
                y_val_f = val_df[fav_col].values
                train_mask_f = ~np.isnan(y_train_f)
                val_mask_f = ~np.isnan(y_val_f)
                if train_mask_f.sum() < 50:
                    print(f'  SKIP fav: train n={train_mask_f.sum()}')
                    continue

                print(f'  Training RF fav (n={train_mask_f.sum()})...')
                fav_model = train_rf_fav(X_train_fav[train_mask_f], y_train_f[train_mask_f])
                fav_pred = fav_model.predict(X_val_fav[val_mask_f])

                # Align predictions: find intersection of breach and fav valid masks
                intersection_mask = val_mask_b & val_mask_f
                if intersection_mask.sum() < 50:
                    print(f'  SKIP: intersection n={intersection_mask.sum()}')
                    continue

                breach_proba_aligned = breach_model.predict_proba(
                    X_val_breach[intersection_mask])[:, 1]
                fav_pred_aligned = fav_model.predict(X_val_fav[intersection_mask])
                val_masked = val_df[intersection_mask].reset_index(drop=True)
                entry_masked = entry_prices_val[intersection_mask]

                print(f'  Grid search ({len(P_GRID)}×{len(MIN_FAV_GRID)}×{len(MIN_RR_GRID)}×{len(TP_FRACTION_GRID)}={len(P_GRID)*len(MIN_FAV_GRID)*len(MIN_RR_GRID)*len(TP_FRACTION_GRID)} combos)...')

                best_grid = None
                best_metrics = None
                best_trades = None

                for p in P_GRID:
                    for min_fav in MIN_FAV_GRID:
                        for min_rr in MIN_RR_GRID:
                            for tp_frac in TP_FRACTION_GRID:
                                trades = simulate_trades(
                                    val_masked, entry_masked,
                                    breach_proba_aligned, fav_pred_aligned,
                                    ohlc, times, time_idx,
                                    side=side, h=h, stop_offset=off,
                                    p=p, min_fav_val=min_fav,
                                    min_rr=min_rr, tp_fraction=tp_frac,
                                    cap=CAP, spread=args.spread)

                                metrics = compute_trade_metrics(trades)
                                tpyr = metrics['trades_per_year']

                                if tpyr >= MIN_TRADES_PER_YEAR:
                                    if best_metrics is None or metrics['pf'] > best_metrics['pf']:
                                        best_metrics = metrics
                                        best_grid = {'p': p, 'min_fav_val': min_fav,
                                                     'min_rr': min_rr, 'tp_fraction': tp_frac}
                                        best_trades = trades

                if best_grid is None:
                    print(f'  FAIL: no grid combo with trades/year >= {MIN_TRADES_PER_YEAR}')
                    all_results[label] = {'status': 'FAIL', 'breach_auc': round(breach_auc, 4)}
                    continue

                # Bootstrap PF
                bs = bootstrap_pf(best_trades) if best_trades else {}

                print(f'  Best: p={best_grid["p"]} min_fav={best_grid["min_fav_val"]} '
                      f'min_rr={best_grid["min_rr"]} tp_frac={best_grid["tp_fraction"]}')
                print(f'  PF={best_metrics["pf"]}  trades={best_metrics["n_trades"]}  '
                      f't/yr={best_metrics["trades_per_year"]}  neg_years={best_metrics["negative_years"]}')
                if bs.get('pf_median'):
                    print(f'  BS: median={bs["pf_median"]}  5%={bs["pf_p05"]}  95%={bs["pf_p95"]}')

                all_results[label] = {
                    'breach_auc': round(breach_auc, 4),
                    'best_grid': best_grid,
                    'trade_metrics': best_metrics,
                    'bootstrap': bs,
                }
                grid_summary.append({
                    'target': label, 'h': h, 'off': off, 'side': side,
                    'breach_auc': round(breach_auc, 4),
                    'pf': best_metrics['pf'],
                    'trades_per_year': best_metrics['trades_per_year'],
                    'negative_years': best_metrics['negative_years'],
                    'pf_buy': best_metrics['pf_buy'],
                    'pf_sell': best_metrics['pf_sell'],
                    'bootstrap_pf_median': bs.get('pf_median'),
                    'bootstrap_pf_p05': bs.get('pf_p05'),
                    'params': best_grid,
                })

    # Summary
    print(f'\n{"="*80}')
    print(f'STAGE 4 SUMMARY: {args.profile}')
    print(f'{"="*80}')
    print(f'{"Target":>20s} | {"AUC":>6s} | {"PF":>8s} | {"T/Yr":>6s} | {"NegY":>5s} | '
          f'{"BS_med":>8s} | {"BS_p05":>8s} | {"PF_buy":>8s} | {"PF_sell":>8s} | params')
    print('-' * 110)

    for s in sorted(grid_summary, key=lambda x: x['pf'] if x['pf'] != float('inf') else 999,
                    reverse=True):
        pf_str = f'{s["pf"]:.3f}' if s['pf'] != float('inf') else 'inf'
        bs_m = f'{s["bootstrap_pf_median"]:.3f}' if s.get('bootstrap_pf_median') else 'N/A'
        bs_05 = f'{s["bootstrap_pf_p05"]:.3f}' if s.get('bootstrap_pf_p05') else 'N/A'
        pf_b = f'{s["pf_buy"]:.3f}' if s['pf_buy'] != float('inf') else 'inf'
        pf_s = f'{s["pf_sell"]:.3f}' if s['pf_sell'] != float('inf') else 'inf'
        params_str = f'p={s["params"]["p"]} mf={s["params"]["min_fav_val"]} '
        params_str += f'rr={s["params"]["min_rr"]} tf={s["params"]["tp_fraction"]}'
        print(f'{s["target"]:>20s} | {s["breach_auc"]:.4f} | {pf_str:>8s} | '
              f'{s["trades_per_year"]:>6.1f} | {s["negative_years"]:>5d} | '
              f'{bs_m:>8s} | {bs_05:>8s} | {pf_b:>8s} | {pf_s:>8s} | {params_str}')

    # Winner selection
    valid = [s for s in grid_summary if s['pf'] != float('inf')
             and s['pf'] > 0 and s['trades_per_year'] >= MIN_TRADES_PER_YEAR]
    if valid:
        winner = max(valid, key=lambda x: (x['pf'], x['breach_auc']))
        print(f'\nWINNER: {winner["target"]}  PF={winner["pf"]:.3f}  '
              f'AUC={winner["breach_auc"]:.4f}  T/Yr={winner["trades_per_year"]:.1f}')
        print(f'  Params: {winner["params"]}')
    else:
        print('\nWINNER: NONE (no PF>1.0 with trades/year >= 30)')

    # Save
    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    output = {
        'config': {
            'profile': args.profile, 'spread': args.spread,
            'purge_bars': args.purge_bars,
            'grid': {'p': P_GRID, 'min_fav': MIN_FAV_GRID,
                     'min_rr': MIN_RR_GRID, 'tp_fraction': TP_FRACTION_GRID},
            'n_bootstrap': N_BOOTSTRAP,
        },
        'results': all_results,
        'summary': grid_summary,
    }
    with open(args.output_json, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f'\nSaved: {args.output_json}')


if __name__ == '__main__':
    main()
