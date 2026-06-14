# =============================================================================
# Файл: ML/baseline/diagnose_stage4_gap.py
# Назначение: Декомпозиция провала Stage 4:
#              1. Partial Oracle: perfect_breach / perfect_fav / perfect_both
#              2. Breach calibration (decile analysis)
#              3. Trade exit distribution + conditional fav error
#              Использует инфраструктуру Stage 4.2 (split, spread, модели).
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


# ---------------------------------------------------------------------------
# Trade simulation (Stage 4.2 spread model)
# ---------------------------------------------------------------------------

def simulate_trades(df, entry_prices, breach_proba, fav_pred, ohlc, times,
                    time_idx, side='sell', h=6, stop_offset=0.5,
                    p=0.5, min_fav_val=0.5, min_rr=1.5, tp_fraction=0.5,
                    cap=5.0, spread=0.0, return_details=False):
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

        # Filters
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
            trade_rec['pred_fav'] = pred_fav
            trade_rec['pred_break'] = pred_break
            trade_rec['fav_val_true'] = row.get(f'target_{side}_H{h}_val', np.nan)
            trade_rec['atr'] = atr_val
            trade_rec['stop_val'] = stop_val_actual
        trades.append(trade_rec)

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
    trades_per_year = n_trades / n_years if n_years > 0 else n_trades
    gross_profit = sum(max(0, t['pnl_val']) for t in trades)
    gross_loss = abs(sum(min(0, t['pnl_val']) for t in trades))
    pf = gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)

    return {
        'pf': round(pf, 3) if pf != float('inf') else pf,
        'n_trades': n_trades, 'trades_per_year': round(trades_per_year, 1),
        'n_years': n_years,
    }


def compute_trade_metrics_detailed(trades):
    if not trades:
        return {}
    base = compute_trade_metrics(trades)
    exits = Counter(t['exit'] for t in trades)
    n = len(trades)
    base['tp_pct'] = round(exits.get('TP', 0) / n * 100, 1)
    base['sl_pct'] = round(exits.get('SL', 0) / n * 100, 1)
    base['timeout_pct'] = round(exits.get('TIMEOUT', 0) / n * 100, 1)
    base['ambiguous_pct'] = round(sum(1 for t in trades if t['ambiguous']) / n * 100, 1)

    # Conditional fav error
    for exit_type in ('TP', 'SL', 'TIMEOUT'):
        subset = [t for t in trades if t['exit'] == exit_type
                  and 'pred_fav' in t and 'fav_val_true' in t]
        if not subset:
            continue
        preds = np.array([t['pred_fav'] for t in subset])
        trues = np.array([t['fav_val_true'] for t in subset])
        valid = ~np.isnan(preds) & ~np.isnan(trues)
        if valid.sum() < 5:
            continue
        err = preds[valid] - trues[valid]
        mae = np.mean(np.abs(err))
        bias = np.mean(err)  # >0 = overpredict
        base[f'fav_mae_{exit_type}'] = round(float(mae), 2)
        base[f'fav_bias_{exit_type}'] = round(float(bias), 2)

    return base


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

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
# Main
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description='Stage 4 gap diagnostics')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--ohlc', default='DATA/XAUUSD_H1_OHLC.csv')
    parser.add_argument('--output', default='ML/reports/stage4_gap_diagnostics.json')
    parser.add_argument('--spread', type=float, default=CANONICAL_SPREAD)
    args = parser.parse_args()

    print('=' * 70)
    print('Stage 4 Gap Diagnostics: Partial Oracle + Calibration + Fav Error')
    print('=' * 70)
    print(f'  Target: sell_H6_off05')
    print(f'  Fixed params: p={WINNER_P} mf={WINNER_MIN_FAV} '
          f'rr={WINNER_MIN_RR} tf={WINNER_TP_FRACTION}')
    print(f'  Spread={args.spread} (OHLC=Bid)')
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

    h, off, side = 6, 0.5, 'sell'
    target_col = BREACH_TARGETS[h][off][side]
    fav_col = FAV_TARGETS[h][side]

    # ---- Train models ----
    y_train_b = train_df[target_col].values
    y_stop_b = val_stop_df[target_col].values
    y_eval_b = val_eval_df[target_col].values
    train_mask_b = ~np.isnan(y_train_b)
    stop_mask_b = ~np.isnan(y_stop_b)
    eval_mask_b = ~np.isnan(y_eval_b)

    print(f'\nTraining XGBoost breach (train={train_mask_b.sum()}, '
          f'val_stop={stop_mask_b.sum()})...')
    breach_model = train_xgb_breach(
        X_train_breach[train_mask_b], y_train_b[train_mask_b],
        X_val_stop_breach[stop_mask_b], y_stop_b[stop_mask_b])
    breach_proba = breach_model.predict_proba(X_val_eval_breach[eval_mask_b])[:, 1]
    breach_auc = roc_auc_score(y_eval_b[eval_mask_b], breach_proba)
    print(f'  Breach AUC val_eval: {breach_auc:.4f}  '
          f'iters={getattr(breach_model, "best_iteration", "?")}')

    y_train_f = train_df[fav_col].values
    y_eval_f = val_eval_df[fav_col].values
    train_mask_f = ~np.isnan(y_train_f)
    eval_mask_f = ~np.isnan(y_eval_f)

    print(f'Training RF fav (train={train_mask_f.sum()})...')
    fav_model = train_rf_fav(X_train_fav[train_mask_f], y_train_f[train_mask_f])
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

    # True labels for oracle
    y_breach_true = val_eval_df[target_col].values[intersection_mask]
    y_fav_true = val_eval_df[fav_col].values[intersection_mask]

    sim_kwargs = dict(
        df=val_masked, entry_prices=entry_masked,
        ohlc=ohlc, times=times, time_idx=time_idx,
        side=side, h=h, stop_offset=off,
        p=WINNER_P, min_fav_val=WINNER_MIN_FAV,
        min_rr=WINNER_MIN_RR, tp_fraction=WINNER_TP_FRACTION,
        cap=CAP, spread=args.spread,
    )

    results = {}
    gap_summary = {}

    # =========================================================================
    # 1. Partial Oracle
    # =========================================================================
    print(f'\n{"=" * 70}')
    print('1. PARTIAL ORACLE DECOMPOSITION')
    print(f'{"=" * 70}')

    oracle_configs = [
        ('baseline', breach_proba_aligned, fav_pred_aligned),
        ('perfect_breach', y_breach_true.copy(), fav_pred_aligned),
        ('perfect_fav', breach_proba_aligned, y_fav_true.copy()),
        ('perfect_both', y_breach_true.copy(), y_fav_true.copy()),
    ]

    for name, breach_arr, fav_arr in oracle_configs:
        trades = simulate_trades(
            breach_proba=breach_arr, fav_pred=fav_arr, **sim_kwargs)
        m = compute_trade_metrics(trades)
        gap_summary[name] = m['pf']
        results[name] = {'pf': m['pf'], 'n_trades': m['n_trades'],
                         'trades_per_year': m['trades_per_year']}
        print(f'  {name:>16s}: PF={m["pf"]:.3f}  trades={m["n_trades"]}  '
              f'T/yr={m["trades_per_year"]:.1f}')

    # Decompose gaps
    gap_breach = gap_summary['perfect_breach'] - gap_summary['baseline']
    gap_fav = gap_summary['perfect_fav'] - gap_summary['baseline']
    gap_both = gap_summary['perfect_both'] - gap_summary['baseline']
    gap_total = gap_summary['perfect_both'] - gap_summary['baseline']

    print(f'\n  Gap decomposition:')
    print(f'    Baseline → perfect_breach: +{gap_breach:.3f} PF')
    print(f'    Baseline → perfect_fav:    +{gap_fav:.3f} PF')
    print(f'    Baseline → perfect_both:   +{gap_both:.3f} PF')
    print(f'    Total gap to oracle:       +{gap_total:.3f} PF')

    if gap_both > 0:
        breach_share = gap_breach / gap_both * 100
        fav_share = gap_fav / gap_both * 100
        print(f'    Breach contribution:       {breach_share:.0f}%')
        print(f'    Fav contribution:          {fav_share:.0f}%')
        results['gap_decomposition'] = {
            'baseline_pf': gap_summary['baseline'],
            'perfect_breach_pf': gap_summary['perfect_breach'],
            'perfect_fav_pf': gap_summary['perfect_fav'],
            'perfect_both_pf': gap_summary['perfect_both'],
            'gap_to_oracle': gap_total,
            'breach_gap': round(gap_breach, 3),
            'fav_gap': round(gap_fav, 3),
            'breach_share_pct': round(breach_share, 1),
            'fav_share_pct': round(fav_share, 1),
        }

    # =========================================================================
    # 2. Breach Decile Calibration
    # =========================================================================
    print(f'\n{"=" * 70}')
    print('2. BREACH CALIBRATION (decline analysis)')
    print(f'{"=" * 70}')

    valid_breach = y_breach_true[~np.isnan(y_breach_true)]
    valid_proba = breach_proba_aligned[~np.isnan(y_breach_true)]
    n_valid = len(valid_breach)

    deciles = np.percentile(valid_proba, np.arange(0, 101, 10))
    calib = []
    print(f'  {"Decile":>8s}  {"Range":>18s}  {"N":>6s}  '
          f'{"p(breach)":>10s}  {"Actual":>8s}  '
          f'{"Trades@pf=0.4":>14s}  {"PF":>8s}')
    print(f'  {"-"*80}')

    for i in range(len(deciles) - 1):
        lo = deciles[i]
        hi = deciles[i + 1] if i < len(deciles) - 2 else deciles[i + 1] + 1e-9
        mask = (valid_proba >= lo) & (valid_proba < hi)
        n_bucket = mask.sum()
        if n_bucket == 0:
            continue
        actual_rate = valid_breach[mask].mean()

        # How many trades would be taken at p=0.4 threshold from this bucket?
        # (only rows with prob < 0.4 enter; count rows with prob in [lo, hi)
        #  AND prob < 0.4)
        enter_mask = mask & (valid_proba < WINNER_P)
        n_trades_bucket = enter_mask.sum()

        # Simulate trades for this bucket (use full sim on the subset)
        if n_trades_bucket >= 10:
            # Build filtered df indices
            full_indices = np.where(~np.isnan(y_breach_true))[0]
            bucket_indices = full_indices[mask & (valid_proba < WINNER_P)]
            if len(bucket_indices) >= 10:
                bucket_df = val_masked.iloc[bucket_indices].reset_index(drop=True)
                bucket_entry = entry_masked[bucket_indices]
                bucket_breach = breach_proba_aligned[~np.isnan(y_breach_true)][
                    mask & (valid_proba < WINNER_P)]
                bucket_fav = fav_pred_aligned[~np.isnan(y_breach_true)][
                    mask & (valid_proba < WINNER_P)]
                # Build kwargs without overlapping data keys
                bucket_kwargs = {k: v for k, v in sim_kwargs.items()
                                 if k not in ('df', 'entry_prices',
                                              'breach_proba', 'fav_pred')}
                bucket_trades = simulate_trades(
                    bucket_df, bucket_entry, bucket_breach, bucket_fav,
                    return_details=False, **bucket_kwargs)
                bucket_m = compute_trade_metrics(bucket_trades)
                bucket_pf = bucket_m['pf']
            else:
                bucket_pf = 0.0
        else:
            bucket_pf = 0.0

        calib.append({
            'decile': i + 1,
            'lo': round(float(lo), 4),
            'hi': round(float(hi), 4),
            'n_bucket': int(n_bucket),
            'actual_breach_rate': round(float(actual_rate), 4),
            'n_trades_at_p04': int(n_trades_bucket),
            'pf_at_p04': round(float(bucket_pf), 3) if bucket_pf else None,
        })
        print(f'  D{i+1:>3d} ({i*10:>2d}%)  '
              f'[{lo:.3f}, {hi:.3f})  {n_bucket:>6d}  '
              f'{actual_rate:.4f} ({actual_rate*100:5.1f}%)  '
              f'{n_trades_bucket:>14d}  {bucket_pf:>8.3f}')

    results['breach_calibration'] = calib

    # =========================================================================
    # 3. Trade Exit Distribution + Fav Error
    # =========================================================================
    print(f'\n{"=" * 70}')
    print('3. TRADE EXIT DISTRIBUTION + CONDITIONAL FAV ERROR')
    print(f'{"=" * 70}')

    trades_detailed = simulate_trades(
        breach_proba=breach_proba_aligned, fav_pred=fav_pred_aligned,
        return_details=True, **sim_kwargs)
    m_detailed = compute_trade_metrics_detailed(trades_detailed)

    print(f'  Total trades: {m_detailed["n_trades"]}')
    print(f'  PF: {m_detailed["pf"]}')
    print(f'  Exit distribution:')
    print(f'    TP:      {m_detailed["tp_pct"]}%')
    print(f'    SL:      {m_detailed["sl_pct"]}%')
    print(f'    TIMEOUT: {m_detailed["timeout_pct"]}%')
    print(f'    Ambiguous: {m_detailed["ambiguous_pct"]}%')

    print(f'\n  Fav prediction error by exit type (MAE, bias):')
    for exit_type in ('TP', 'SL', 'TIMEOUT'):
        mae_key = f'fav_mae_{exit_type}'
        bias_key = f'fav_bias_{exit_type}'
        if mae_key in m_detailed:
            sign = '+' if m_detailed[bias_key] > 0 else ''
            print(f'    {exit_type:>7s}: MAE={m_detailed[mae_key]:.2f} ATR  '
                  f'bias={sign}{m_detailed[bias_key]:.2f} ATR  '
                  f'({"overpredicts" if m_detailed[bias_key] > 0 else "underpredicts"})')

    # Additional: mean fav_pred vs actual fav_val for all trades
    fav_preds_all = np.array([t['pred_fav'] for t in trades_detailed])
    fav_trues_all = np.array([t['fav_val_true'] for t in trades_detailed])
    valid_all = ~np.isnan(fav_preds_all) & ~np.isnan(fav_trues_all)
    if valid_all.sum() > 5:
        fav_corr = np.corrcoef(fav_preds_all[valid_all], fav_trues_all[valid_all])[0, 1]
        fav_rmse = np.sqrt(np.mean((fav_preds_all[valid_all] - fav_trues_all[valid_all]) ** 2))
        print(f'\n  Fav global metrics (all trades):')
        print(f'    Correlation: {fav_corr:.3f}')
        print(f'    RMSE:        {fav_rmse:.2f} ATR')
        print(f'    Mean pred:   {np.mean(fav_preds_all[valid_all]):.2f} ATR')
        print(f'    Mean true:   {np.mean(fav_trues_all[valid_all]):.2f} ATR')
        results['fav_global'] = {
            'correlation': round(float(fav_corr), 3),
            'rmse_atr': round(float(fav_rmse), 2),
            'mean_pred': round(float(np.mean(fav_preds_all[valid_all])), 2),
            'mean_true': round(float(np.mean(fav_trues_all[valid_all])), 2),
        }

    results['trade_exit'] = m_detailed

    # =========================================================================
    # 4. Additional: stop_val distribution
    # =========================================================================
    stops = [t['stop_val'] for t in trades_detailed]
    if stops:
        print(f'\n{"=" * 70}')
        print('4. STOP SIZE DISTRIBUTION')
        print(f'{"=" * 70}')
        stops_arr = np.array(stops)
        print(f'  Mean stop: {np.mean(stops_arr):.2f} ATR  '
              f'Median: {np.median(stops_arr):.2f}  '
              f'p05: {np.percentile(stops_arr, 5):.2f}  '
              f'p95: {np.percentile(stops_arr, 95):.2f}')

        # PnL distribution
        pnls = [t['pnl_r'] for t in trades_detailed]
        pnls_arr = np.array(pnls)
        print(f'\n  PnL/R distribution:')
        print(f'    Mean:   {np.mean(pnls_arr):.3f}R')
        print(f'    Median: {np.median(pnls_arr):.3f}R')
        print(f'    p05:    {np.percentile(pnls_arr, 5):.3f}R')
        print(f'    p95:    {np.percentile(pnls_arr, 95):.3f}R')
        win_rate = (pnls_arr > 0).mean() * 100
        print(f'    Win rate: {win_rate:.1f}%')
        avg_win = np.mean(pnls_arr[pnls_arr > 0]) if (pnls_arr > 0).any() else 0
        avg_loss = np.mean(np.abs(pnls_arr[pnls_arr < 0])) if (pnls_arr < 0).any() else 0
        print(f'    Avg win:  {avg_win:.3f}R')
        print(f'    Avg loss: {avg_loss:.3f}R')
        results['pnl_distribution'] = {
            'mean_pnl_r': round(float(np.mean(pnls_arr)), 3),
            'median_pnl_r': round(float(np.median(pnls_arr)), 3),
            'p05_pnl_r': round(float(np.percentile(pnls_arr, 5)), 3),
            'p95_pnl_r': round(float(np.percentile(pnls_arr, 95)), 3),
            'win_rate_pct': round(float(win_rate), 1),
            'avg_win_r': round(float(avg_win), 3),
            'avg_loss_r': round(float(avg_loss), 3),
        }

    # ---- Save ----
    output = {
        'config': {
            'target': 'sell_H6_off05',
            'params': {'p': WINNER_P, 'min_fav': WINNER_MIN_FAV,
                       'min_rr': WINNER_MIN_RR, 'tp_fraction': WINNER_TP_FRACTION},
            'spread': args.spread,
            'split': {
                'train': f'<={TRAIN_MAX_YEAR}',
                'val_stop': list(VAL_STOP_YEARS),
                'val_eval': f'>={VAL_EVAL_MIN_YEAR}',
            },
        },
        'breach_auc_val_eval': round(breach_auc, 4),
        'results': results,
    }
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f'\nSaved: {args.output}')


if __name__ == '__main__':
    main()
