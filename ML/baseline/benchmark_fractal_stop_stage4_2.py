# =============================================================================
# Файл: ML/baseline/benchmark_fractal_stop_stage4_2.py
# Назначение: Stage 4.2 — DIAGNOSTIC_ONLY пересчёт winner Stage 4
#              с исправленной методикой:
#                - Трёхслойный split: train(2004-2016), val_stop(2017-2018),
#                  val_eval(2019-2022)
#                - Early stopping на val_stop (не на val_eval)
#                - Spread-коррекция под OHLC=Bid
#                - Один target (sell_H6_off05), одна конфигурация (p=0.4, mf=0.3,
#                  rr=1.0, tf=0.4), без grid search
#                - Block bootstrap
#                - Permutation test для одного target
#                - Годовой разрез отдельно от bootstrap
#              НЕ является чистым бенчмарком — winner выбран на Stage 4 по
#              validation 2019-2022, поэтому val_eval косвенно участвовал в выборе.
# Язык: Python 3.10+
# Создан: 2026-06-12
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

# Fixed winner params from Stage 4
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
N_BOOTSTRAP = 500
N_PERMUTATION = 500
BLOCK_BOOTSTRAP_SIZE = 15

# Split years
TRAIN_MAX_YEAR = 2016
VAL_STOP_YEARS = {2017, 2018}
VAL_EVAL_MIN_YEAR = 2019


# ---------------------------------------------------------------------------
# Data loading — трёхслойный split
# ---------------------------------------------------------------------------

def load_splits(train_path, val_path, purge_bars=12):
    """Загрузка и трёхслойное хронологическое разбиение.

    Возвращает: train_df, val_stop_df, val_eval_df
    """
    train_df = pd.read_csv(train_path, sep=';')
    val_df = pd.read_csv(val_path, sep=';')

    # Год из time
    train_df['_year'] = pd.to_datetime(
        train_df['time'], format='%Y.%m.%d %H:%M', errors='coerce').dt.year
    val_df['_year'] = pd.to_datetime(
        val_df['time'], format='%Y.%m.%d %H:%M', errors='coerce').dt.year

    # Split train по году
    train = train_df[train_df['_year'] <= TRAIN_MAX_YEAR].copy()
    val_stop = train_df[train_df['_year'].isin(VAL_STOP_YEARS)].copy()
    val_eval_train_part = train_df[train_df['_year'] >= VAL_EVAL_MIN_YEAR].copy()

    # val_eval = остаток train (2019) + validation CSV
    val_eval = pd.concat([val_eval_train_part, val_df], ignore_index=True)

    # Purge (с хвоста каждого)
    if purge_bars > 0:
        if len(train) > purge_bars:
            train = train.iloc[:-purge_bars]
        if len(val_stop) > purge_bars:
            val_stop = val_stop.iloc[:-purge_bars]
        if len(val_eval) > purge_bars:
            val_eval = val_eval.iloc[:-purge_bars]

    return train, val_stop, val_eval


# ---------------------------------------------------------------------------
# Feature extraction (from Stage 4, base_raw_plus_time)
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
# OHLC & entry prices
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


# ---------------------------------------------------------------------------
# Trade simulation — исправленная spread-модель (OHLC=Bid)
# ---------------------------------------------------------------------------

def simulate_trades(df, entry_prices, breach_proba, fav_pred, ohlc, times,
                    time_idx, side='sell', h=6, stop_offset=0.5,
                    p=0.5, min_fav_val=0.5, min_rr=1.5, tp_fraction=0.5,
                    cap=5.0, spread=0.0):
    """Симуляция сделок с корректной spread-моделью для OHLC=Bid.

    OHLC = Bid.
    BUY:  entry = Bid + spread (Ask), exit = Bid (bars as-is).
    SELL: entry = Bid, exit = Ask (bars shifted +spread).
    """
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

        # TP price (Bid terms)
        tp_val_atr = min(pred_fav * tp_fraction, cap)
        if trade_direction == -1:
            tp_price = entry_price_val + tp_val_atr * atr_val
        else:
            tp_price = entry_price_val - tp_val_atr * atr_val

        # --- Build bars with correct convention ---
        bars_h_bid = [(ohlc[times[k]][0], ohlc[times[k]][1],
                        ohlc[times[k]][2], ohlc[times[k]][3])
                       for k in range(idx0 + 1, idx0 + 1 + h)]

        if trade_direction == -1:  # BUY: entry at Ask, exit at Bid
            entry_eff = entry_price_val + spread
            bars_h_eff = bars_h_bid  # exit at Bid → bars as-is
        else:  # SELL: entry at Bid, exit at Ask
            entry_eff = entry_price_val
            bars_h_eff = [(o + spread, h + spread, l + spread, c + spread)
                          for o, h, l, c in bars_h_bid]

        stop_val_actual = (abs(entry_eff - stop_price)) / atr_val
        if stop_val_actual <= 0:
            continue

        # Trade filters
        if pred_break >= p:
            continue
        if pred_fav < min_fav_val:
            continue
        if pred_fav / stop_val_actual < min_rr:
            continue

        outcome = evaluate_fractal_stop_trade(
            bars_h_eff, trade_direction, entry_eff, stop_price, tp_price, atr_val)

        year_val = row.get('_year')
        year_int = int(year_val) if not pd.isna(year_val) else None

        trades.append({
            'exit': outcome['exit'],
            'pnl_val': outcome['pnl_val'],
            'stop_val': stop_val_actual,
            'pnl_r': outcome['pnl_val'] / stop_val_actual
                if stop_val_actual > 0 else outcome['pnl_val'],
            'ambiguous': outcome['ambiguous'],
            'year': year_int,
            'side': side,
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
    pf = gross_profit / gross_loss if gross_loss > 0 \
        else (float('inf') if gross_profit > 0 else 0.0)

    exits = Counter(t['exit'] for t in trades)
    timeout_pct = exits.get('TIMEOUT', 0) / n_trades * 100 if n_trades else 0
    ambiguous_pct = sum(1 for t in trades if t['ambiguous']) / n_trades * 100 \
        if n_trades else 0

    # Yearly breakdown
    yearly = {}
    negative_years = 0
    for yr in years_covered:
        yr_trades = [t for t in trades if t['year'] == yr]
        if len(yr_trades) < 3:
            continue
        yr_profit = sum(max(0, t['pnl_val']) for t in yr_trades)
        yr_loss = abs(sum(min(0, t['pnl_val']) for t in yr_trades))
        yr_pf = yr_profit / yr_loss if yr_loss > 0 \
            else (float('inf') if yr_profit > 0 else 0.0)
        yearly[yr] = {
            'pf': round(yr_pf, 3) if yr_pf != float('inf') else yr_pf,
            'n': len(yr_trades),
        }
        if yr_pf < 1.0:
            negative_years += 1

    return {
        'pf': round(pf, 3) if pf != float('inf') else pf,
        'n_trades': n_trades, 'trades_per_year': round(trades_per_year, 1),
        'n_years': n_years, 'negative_years': negative_years,
        'timeout_pct': round(timeout_pct, 1),
        'ambiguous_pct': round(ambiguous_pct, 1),
        'yearly': yearly,
    }


# ---------------------------------------------------------------------------
# Block bootstrap
# ---------------------------------------------------------------------------

def block_bootstrap_pf(trades, block_size=BLOCK_BOOTSTRAP_SIZE, n_iter=N_BOOTSTRAP,
                       seed=42):
    """Block bootstrap PF для temporally correlated сделок."""
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
        'pf_inf_pct': round(float((~np.isfinite(pfs)).sum() / len(pfs) * 100), 1),
        'n_trades': len(trades),
        'block_size': block_size,
        'n_blocks': n_blocks,
    }


# ---------------------------------------------------------------------------
# Permutation test (single target, no grid search)
# ---------------------------------------------------------------------------

def permutation_test_pf(sim_fn, sim_kwargs_fixed, breach_obs, obs_pf, n_iter=500):
    """Permutation test: shuffle breach probas, re-run, compute PF.

    sim_fn: simulate_trades
    sim_kwargs_fixed: dict with all args EXCEPT breach_proba
    breach_obs: np.array observed breach probabilities
    obs_pf: float observed PF
    Returns p-value.
    """
    if obs_pf == 0 or obs_pf == float('inf'):
        return {'p_value': None, 'obs_pf': obs_pf, 'n_perm': 0,
                'note': 'obs_pf_invalid'}

    rng = np.random.RandomState(42)
    breach = breach_obs.copy()
    count_ge = 0
    perm_pfs = []

    for _ in range(n_iter):
        perm_breach = rng.permutation(breach)
        kwargs = dict(sim_kwargs_fixed, breach_proba=perm_breach)
        perm_trades = sim_fn(**kwargs)
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
        'perm_pf_median': round(float(np.median(finite_perms)), 3)
            if finite_perms else None,
        'perm_pf_p95': round(float(np.percentile(finite_perms, 95)), 3)
            if finite_perms else None,
        'perm_pf_max': round(float(np.max(finite_perms)), 3)
            if finite_perms else None,
        'count_ge': count_ge,
    }


# ---------------------------------------------------------------------------
# Model training
# ---------------------------------------------------------------------------

def train_xgb_breach(X_train, y_train, X_val_stop, y_val_stop, random_state=42):
    """XGBoost breach с early stopping на val_stop."""
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
    model.fit(X_train, y_train,
              eval_set=[(X_val_stop, y_val_stop)], verbose=False)
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
    parser = argparse.ArgumentParser(
        description='Stage 4.2: DIAGNOSTIC — corrected winner recalc')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--ohlc', default='DATA/XAUUSD_H1_OHLC.csv')
    parser.add_argument('--purge-bars', type=int, default=12)
    parser.add_argument('--output-json',
                        default='ML/reports/stage4_2_diagnostic.json')
    parser.add_argument('--spread', type=float, default=CANONICAL_SPREAD)
    args = parser.parse_args()

    print('=' * 70)
    print('Stage 4.2: DIAGNOSTIC_ONLY — corrected winner (sell_H6_off05) recalc')
    print('=' * 70)
    print(f'  Status: DIAGNOSTIC_ONLY (not a clean benchmark)')
    print(f'  Winner selected on Stage 4 validation 2019-2022')
    print(f'  Fixed params: p={WINNER_P}, mf={WINNER_MIN_FAV}, '
          f'rr={WINNER_MIN_RR}, tf={WINNER_TP_FRACTION}')
    print(f'  Spread={args.spread} (OHLC=Bid convention)')
    print()

    # ---- 1. Load data with three-layer split ----
    print('Loading data (three-layer split)...')
    train_df, val_stop_df, val_eval_df = load_splits(
        args.train, args.val, args.purge_bars)
    print(f'  Train (<=2016): {len(train_df)} rows, '
          f'{train_df["_year"].min():.0f}-{train_df["_year"].max():.0f}')
    print(f'  Val-stop (2017-2018): {len(val_stop_df)} rows, '
          f'{val_stop_df["_year"].min():.0f}-{val_stop_df["_year"].max():.0f}')
    print(f'  Val-eval (>=2019): {len(val_eval_df)} rows, '
          f'{val_eval_df["_year"].min():.0f}-{val_eval_df["_year"].max():.0f}')

    # ---- 2. Load OHLC ----
    print(f'\nLoading OHLC: {args.ohlc}')
    ohlc, times, time_idx = load_ohlc_index(args.ohlc)
    print(f'  OHLC bars: {len(times)}')

    # ---- 3. Entry prices for val_eval ----
    print('Computing entry prices (val_eval)...')
    entry_prices_val = compute_entry_prices(val_eval_df, ohlc, times, time_idx)
    valid_entry = (~np.isnan(entry_prices_val)).sum()
    print(f'  Valid entries: {valid_entry}/{len(val_eval_df)}')

    # ---- 4. Features ----
    print('Extracting breach features (base_raw_plus_time)...')
    X_train_breach, _ = profile_base_raw_plus_time(train_df)
    X_val_stop_breach, _ = profile_base_raw_plus_time(val_stop_df)
    X_val_eval_breach, _ = profile_base_raw_plus_time(val_eval_df)
    print(f'  Breach features: {X_train_breach.shape[1]}')

    print('Extracting fav features (base_raw)...')
    X_train_fav, _ = profile_base_raw(train_df)
    X_val_eval_fav, _ = profile_base_raw(val_eval_df)

    # ---- 5. Prepare target ----
    target_col = BREACH_TARGETS[WINNER_H][WINNER_OFF][WINNER_SIDE]
    fav_col = FAV_TARGETS[WINNER_H][WINNER_SIDE]
    label = WINNER_TARGET

    print(f'\n{"=" * 70}')
    print(f'Target: {label}  (breach={target_col}, fav={fav_col})')
    print(f'{"=" * 70}')

    # ---- 6. Train breach XGBoost (early stopping on val_stop) ----
    y_train_b = train_df[target_col].values
    y_stop_b = val_stop_df[target_col].values
    y_eval_b = val_eval_df[target_col].values

    train_mask_b = ~np.isnan(y_train_b)
    stop_mask_b = ~np.isnan(y_stop_b)
    eval_mask_b = ~np.isnan(y_eval_b)

    print(f'  Breach XGBoost: train_n={train_mask_b.sum()}, '
          f'pos={int(y_train_b[train_mask_b].sum())}')
    print(f'  val_stop_n={stop_mask_b.sum()}, val_eval_n={eval_mask_b.sum()}')

    breach_model = train_xgb_breach(
        X_train_breach[train_mask_b], y_train_b[train_mask_b],
        X_val_stop_breach[stop_mask_b], y_stop_b[stop_mask_b])

    n_iters = getattr(breach_model, 'best_iteration', breach_model.n_estimators)
    print(f'  Best iteration: {n_iters}')

    # Breach AUC on val_eval
    breach_proba_eval = breach_model.predict_proba(
        X_val_eval_breach[eval_mask_b])[:, 1]
    breach_auc = roc_auc_score(y_eval_b[eval_mask_b], breach_proba_eval)
    print(f'  Breach AUC (val_eval): {breach_auc:.4f}')

    # ---- 7. Train fav RF ----
    y_train_f = train_df[fav_col].values
    y_eval_f = val_eval_df[fav_col].values
    train_mask_f = ~np.isnan(y_train_f)
    eval_mask_f = ~np.isnan(y_eval_f)

    print(f'  Fav RF: train_n={train_mask_f.sum()}, val_eval_n={eval_mask_f.sum()}')
    fav_model = train_rf_fav(X_train_fav[train_mask_f], y_train_f[train_mask_f])
    fav_pred_eval = fav_model.predict(X_val_eval_fav[eval_mask_f])

    # ---- 8. Align breach + fav predictions ----
    intersection_mask = eval_mask_b & eval_mask_f
    print(f'  Intersection (breach+fav valid): {intersection_mask.sum()}')
    if intersection_mask.sum() < 50:
        print('  SKIP: too few samples')
        return

    breach_proba_aligned = breach_model.predict_proba(
        X_val_eval_breach[intersection_mask])[:, 1]
    fav_pred_aligned = fav_model.predict(X_val_eval_fav[intersection_mask])
    val_masked = val_eval_df[intersection_mask].reset_index(drop=True)
    entry_masked = entry_prices_val[intersection_mask]

    # ---- 9. Trade simulation (single config, no grid search) ----
    print(f'\n  Trade simulation (fixed params: p={WINNER_P}, '
          f'mf={WINNER_MIN_FAV}, rr={WINNER_MIN_RR}, tf={WINNER_TP_FRACTION})...')

    trades = simulate_trades(
        val_masked, entry_masked,
        breach_proba_aligned, fav_pred_aligned,
        ohlc, times, time_idx,
        side=WINNER_SIDE, h=WINNER_H, stop_offset=WINNER_OFF,
        p=WINNER_P, min_fav_val=WINNER_MIN_FAV,
        min_rr=WINNER_MIN_RR, tp_fraction=WINNER_TP_FRACTION,
        cap=CAP, spread=args.spread)

    metrics = compute_trade_metrics(trades)
    print(f'  PF={metrics["pf"]}  trades={metrics["n_trades"]}  '
          f't/yr={metrics["trades_per_year"]}  '
          f'neg_years={metrics["negative_years"]}/{metrics["n_years"]}')
    print(f'  Timeout: {metrics["timeout_pct"]}%  '
          f'Ambiguous: {metrics["ambiguous_pct"]}%')

    # ---- 10. Yearly breakdown ----
    print(f'\n  Yearly breakdown:')
    for yr in sorted(metrics['yearly'].keys()):
        y = metrics['yearly'][yr]
        print(f'    {yr}: PF={y["pf"]:.3f}  trades={y["n"]}')

    # ---- 11. Block bootstrap ----
    print(f'\n  Block bootstrap (block_size={BLOCK_BOOTSTRAP_SIZE}, '
          f'n_iter={N_BOOTSTRAP})...')
    bs = block_bootstrap_pf(trades)
    if bs.get('pf_median'):
        print(f'  BS: median={bs["pf_median"]}  p05={bs["pf_p05"]}  '
              f'p95={bs["pf_p95"]}')

    # ---- 12. Permutation test ----
    print(f'\n  Permutation test ({N_PERMUTATION} iter)...')
    sim_kwargs_fixed = dict(
        df=val_masked, entry_prices=entry_masked,
        fav_pred=fav_pred_aligned,
        ohlc=ohlc, times=times, time_idx=time_idx,
        side=WINNER_SIDE, h=WINNER_H, stop_offset=WINNER_OFF,
        p=WINNER_P, min_fav_val=WINNER_MIN_FAV,
        min_rr=WINNER_MIN_RR, tp_fraction=WINNER_TP_FRACTION,
        cap=CAP, spread=args.spread,
    )
    perm_result = permutation_test_pf(
        simulate_trades, sim_kwargs_fixed,
        breach_proba_aligned, metrics['pf'], n_iter=N_PERMUTATION)
    print(f'  Perm p-value: {perm_result["p_value"]}  '
          f'(obs PF={perm_result["obs_pf"]}, '
          f'perm median={perm_result.get("perm_pf_median")}, '
          f'perm p95={perm_result.get("perm_pf_p95")})')

    # ---- 13. Stage 4 comparison ----
    stage4_pf = 1.106
    stage4_bs_p05 = 0.923
    delta_pf = round(metrics['pf'] - stage4_pf, 3)
    print(f'\n  Stage 4 winner PF: {stage4_pf}  BS_p05: {stage4_bs_p05}')
    print(f'  Stage 4.2 PF:        {metrics["pf"]}  '
          f'BS_p05: {bs.get("pf_p05", "N/A")}')
    print(f'  Delta PF (4.2 - 4): {delta_pf:+0.3f}  '
          f'(methodological bias estimate)')

    # ---- 14. Save ----
    output = {
        'status': 'DIAGNOSTIC_ONLY',
        'note': 'Winner selected on Stage 4 validation 2019-2022. '
                'Not a clean out-of-sample benchmark.',
        'config': {
            'split': {
                'train_years': f'<={TRAIN_MAX_YEAR}',
                'val_stop_years': list(VAL_STOP_YEARS),
                'val_eval_years': f'>={VAL_EVAL_MIN_YEAR}',
            },
            'target': WINNER_TARGET,
            'h': WINNER_H, 'off': WINNER_OFF, 'side': WINNER_SIDE,
            'fixed_params': {
                'p': WINNER_P, 'min_fav_val': WINNER_MIN_FAV,
                'min_rr': WINNER_MIN_RR, 'tp_fraction': WINNER_TP_FRACTION,
                'cap': CAP,
            },
            'spread': args.spread,
            'spread_model': 'OHLC=Bid. BUY: entry+spread(Ask), exit Bid. '
                            'SELL: entry Bid, bars shifted +spread (exit Ask).',
            'purge_bars': args.purge_bars,
            'block_bootstrap_size': BLOCK_BOOTSTRAP_SIZE,
            'n_bootstrap': N_BOOTSTRAP,
            'n_permutation': N_PERMUTATION,
        },
        'breach_auc': round(breach_auc, 4),
        'n_iters': n_iters if n_iters else None,
        'trade_metrics': metrics,
        'block_bootstrap': bs,
        'permutation_test': perm_result,
        'stage4_comparison': {
            'stage4_pf': stage4_pf,
            'stage4_2_pf': metrics['pf'],
            'delta_pf': delta_pf,
            'stage4_bs_p05': stage4_bs_p05,
            'stage4_2_bs_p05': bs.get('pf_p05'),
        },
    }

    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f'\nSaved: {args.output_json}')


if __name__ == '__main__':
    main()
