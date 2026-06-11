# =============================================================================
# Файл: ML/baseline/benchmark_fractal_stop_fav.py
# Назначение: RF breach + fav -> торговый слой -> PnL (Stage 2)
# Язык: Python 3.10+
# Обновлён: 2026-06-11
# Зависимости: numpy, pandas, scikit-learn
#   Входные данные: DATA/Nero_XAUUSD_train_labeled.csv, ...validation_labeled.csv
#   Выходные данные: ML/reports/fractal_stop_fav.json,
#                    ML/reports/fractal_stop_fav_frozen_rule.json
# Использование:
#   source ~/git/SoSimple/.venv/bin/activate
#   python -m ML.baseline.benchmark_fractal_stop_fav
#   python -m ML.baseline.benchmark_fractal_stop_fav --frozen-rule ... --test ...
# =============================================================================

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import roc_auc_score, average_precision_score

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'processing'))
from label_signals import (  # noqa: E402
    load_ohlc_index,
    evaluate_fractal_stop_trade,
)

# Feature contract: 10 live-safe каналов x 100 фракталов + ATR
BASE_CHANNEL_KEYS = [
    'price', 'direction', 'front', 'back', 'strong',
    'break', 'reverse', 'power', 'count', 'impulse',
]

# Grid search
P_GRID = [0.3, 0.4, 0.5]
MIN_FAV_GRID = [0.3, 0.5, 0.7]
MIN_RR_GRID = [1.0, 1.5, 2.0]
TP_FRACTION_GRID = [0.3, 0.5, 0.7]
CAP = 5.0

BREACH_TARGETS = {
    6: {
        0.2: {'buy': 'buy_stop_broken_H6_off02_flag', 'sell': 'sell_stop_broken_H6_off02_flag'},
        0.5: {'buy': 'buy_stop_broken_H6_off05_flag', 'sell': 'sell_stop_broken_H6_off05_flag'},
    },
    12: {
        0.2: {'buy': 'buy_stop_broken_H12_off02_flag', 'sell': 'sell_stop_broken_H12_off02_flag'},
        0.5: {'buy': 'buy_stop_broken_H12_off05_flag', 'sell': 'sell_stop_broken_H12_off05_flag'},
    },
}

FAV_TARGETS = {
    6: {'buy': 'target_buy_H6_val', 'sell': 'target_sell_H6_val'},
    12: {'buy': 'target_buy_H12_val', 'sell': 'target_sell_H12_val'},
}


def extract_flat_base_features(df, n_fractals=100):
    """Извлечь BASE_CHANNEL_KEYS x n_fractals как плоские float64 признаки + ATR."""
    features = []
    feature_names = []
    for level in range(n_fractals):
        col = f'fractal{level}'
        if col not in df.columns:
            break
        parts = df[col].astype(str).str.split(':', expand=True)
        key_to_idx = {
            'price': 1, 'direction': 2, 'front': 3, 'back': 4,
            'strong': 5, 'break': 6, 'reverse': 7, 'power': 8,
            'count': 9, 'impulse': 10,
        }
        for key in BASE_CHANNEL_KEYS:
            idx = key_to_idx[key]
            vals = pd.to_numeric(parts[idx], errors='coerce').fillna(0.0).values
            features.append(vals.astype(np.float64))
            feature_names.append(f'f{level}_{key}')
    if 'ATR' in df.columns:
        features.append(df['ATR'].values.astype(np.float64))
        feature_names.append('ATR')
    X = np.column_stack(features)
    return X, feature_names


def load_split(path, purge_bars=12):
    """Загрузить сплит, добавить колонку _year, применить H-барный purge на хвосте."""
    df = pd.read_csv(path, sep=';')
    if purge_bars > 0 and len(df) > purge_bars:
        df = df.iloc[:-purge_bars]
    df['_year'] = pd.to_datetime(
        df['time'], format='%Y.%m.%d %H:%M', errors='coerce'
    ).dt.year
    return df


def lookup_entry_prices(df, ohlc_path):
    """Добавить колонку entry_price = Open[row+1]."""
    ohlc, times, time_idx = load_ohlc_index(ohlc_path)
    entries = []
    for _, row in df.iterrows():
        try:
            row_dt = datetime.strptime(str(row['time']), "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            entries.append(np.nan)
            continue
        idx0 = time_idx.get(row_dt)
        if idx0 is None or idx0 + 1 >= len(times):
            entries.append(np.nan)
        else:
            entries.append(ohlc[times[idx0 + 1]][0])
    return np.array(entries, dtype=np.float64)


def parse_trade_fractal0(raw):
    """Прочитать только price/direction из fractal0 для торговой симуляции."""
    if pd.isna(raw):
        return None
    parts = str(raw).split(':')
    if len(parts) != 23:
        return None
    try:
        return {
            'price': float(parts[1]),
            'direction': int(float(parts[2])),
        }
    except (TypeError, ValueError):
        return None


def simulate_trades(df, entry_prices, breach_proba, fav_pred, ohlc, times, time_idx,
                    side, h, stop_offset, atr_col='ATR',
                    p=0.5, min_fav_val=0.5, min_rr=1.5, tp_fraction=0.5, cap=5.0,
                    spread=0.0):
    """
    Применить торговое правило к данным.

    Принимает предзагруженные ohlc, times, time_idx.
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
        if fractal0['direction'] == 0:
            continue
        fractal_price = fractal0['price']

        try:
            row_dt = datetime.strptime(str(row['time']), "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        idx0 = time_idx.get(row_dt)
        if idx0 is None or idx0 + h >= len(times):
            continue

        entry_price_val = entry_prices[i]
        if np.isnan(entry_price_val):
            continue
        atr_val = float(row[atr_col])
        if atr_val <= 0:
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

        bars_h = []
        for k in range(idx0 + 1, idx0 + 1 + h):
            o, hi, lo, c = ohlc[times[k]]
            bars_h.append((o, hi, lo, c))

        outcome = evaluate_fractal_stop_trade(
            bars_h, trade_direction, entry_spread, stop_price, tp_price_spread, atr_val
        )

        year = row.get('_year', np.nan)
        trades.append({
            'exit': outcome['exit'],
            'pnl_val': outcome['pnl_val'],
            'stop_val': stop_val_actual,
            'pnl_r': outcome['pnl_val'] / stop_val_actual if stop_val_actual > 0 else outcome['pnl_val'],
            'ambiguous': outcome['ambiguous'],
            'year': int(year) if not pd.isna(year) else None,
            'side': side,
        })

    return trades


def compute_trade_metrics(trades):
    """PF, сделок/год, убыточные годы, timeout%, ambiguous%."""
    if len(trades) == 0:
        return {'n_trades': 0, 'status': 'no_trades'}

    df_t = pd.DataFrame(trades)
    gross_profit = df_t[df_t['pnl_val'] > 0]['pnl_val'].sum()
    gross_loss = abs(df_t[df_t['pnl_val'] < 0]['pnl_val'].sum())
    pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')

    yearly = df_t.groupby('year').agg(
        n=('pnl_val', 'count'),
        pf=('pnl_val', lambda x: x[x > 0].sum() / abs(x[x < 0].sum()) if (x < 0).any() else float('inf')),
        total_pnl=('pnl_val', 'sum'),
    ).to_dict('index')

    negative_years = sum(1 for y in yearly.values()
                         if y['pf'] < 1.0 and y['n'] >= 5)

    buy_side = df_t[df_t['side'] == 'buy']
    sell_side = df_t[df_t['side'] == 'sell']

    def side_pf(side_df):
        if len(side_df) == 0:
            return None
        gp = side_df[side_df['pnl_val'] > 0]['pnl_val'].sum()
        gl = abs(side_df[side_df['pnl_val'] < 0]['pnl_val'].sum())
        return round(gp / gl, 3) if gl > 0 else float('inf')

    return {
        'n_trades': len(trades),
        'pf': round(pf, 3),
        'timeout_pct': round((df_t['exit'] == 'TIMEOUT').mean(), 3),
        'ambiguous_pct': round(df_t['ambiguous'].mean(), 3),
        'trades_per_year': round(len(trades) / len(yearly), 1) if yearly else 0,
        'negative_years': negative_years,
        'n_years': len(yearly),
        'yearly': {str(y): v for y, v in yearly.items()},
        'buy': {
            'n': len(buy_side),
            'pf': side_pf(buy_side),
        } if len(buy_side) > 0 else None,
        'sell': {
            'n': len(sell_side),
            'pf': side_pf(sell_side),
        } if len(sell_side) > 0 else None,
    }


def compute_breach_metrics(y_true, y_pred_proba, years=None):
    """AUC, PR-AUC, breach_rate, lift@20%."""
    mask = ~np.isnan(y_true)
    y_true = y_true[mask]
    y_pred_proba = y_pred_proba[mask]
    if years is not None:
        years = years[mask]
    if len(y_true) < 10:
        return None

    unique_classes = np.unique(y_true)
    if len(unique_classes) < 2:
        return {
            'auc': None, 'pr_auc': None,
            'breach_rate': round(float(y_true.mean()), 4),
            'n': int(len(y_true)),
            'note': 'single_class',
        }

    auc = roc_auc_score(y_true, y_pred_proba)
    pr_auc = average_precision_score(y_true, y_pred_proba)
    overall_rate = float(y_true.mean())

    cutoff = np.quantile(y_pred_proba, 0.20)
    low_risk_mask = y_pred_proba <= cutoff
    low_risk_rate = float(y_true[low_risk_mask].mean()) if low_risk_mask.sum() > 0 else 0.0
    lift = overall_rate / low_risk_rate if low_risk_rate > 0 else float('inf')

    metrics = {
        'auc': round(auc, 4),
        'pr_auc': round(pr_auc, 4),
        'breach_rate': round(overall_rate, 4),
        'low_risk_breach_rate': round(low_risk_rate, 4),
        'lift': round(lift, 2),
        'n': int(len(y_true)),
    }

    if years is not None:
        yearly = {}
        for yr in sorted(set(years)):
            ym = years == yr
            if ym.sum() >= 5:
                yr_unique = np.unique(y_true[ym])
                if len(yr_unique) >= 2:
                    try:
                        yr_auc = roc_auc_score(y_true[ym], y_pred_proba[ym])
                    except ValueError:
                        yr_auc = None
                else:
                    yr_auc = None
                yearly[int(yr)] = {
                    'auc': round(yr_auc, 4) if yr_auc is not None else None,
                    'n': int(ym.sum()),
                    'breach_rate': round(float(y_true[ym].mean()), 4),
                }
        metrics['yearly'] = yearly
    return metrics


def _grid_search_trades(train_df, val_df, ohlc_path, h, off, side, args):
    """Обучить breach + fav, grid search порогов на val (canonical spread only)."""
    breach_col = BREACH_TARGETS[h][off][side]
    fav_col = FAV_TARGETS[h][side]

    X_train, feature_names = extract_flat_base_features(train_df)
    X_val, _ = extract_flat_base_features(val_df)

    y_breach_train = train_df[breach_col].values
    y_breach_val = val_df[breach_col].values
    y_fav_train = train_df[fav_col].values
    y_fav_val = val_df[fav_col].values

    breach_train_mask = ~np.isnan(y_breach_train)
    fav_train_mask = ~np.isnan(y_fav_train)
    val_mask = ~np.isnan(y_breach_val) & ~np.isnan(y_fav_val)

    n_breach_train = breach_train_mask.sum()
    n_fav_train = fav_train_mask.sum()

    if n_breach_train < 50 or n_fav_train < 50:
        return None

    print(f'\n--- {breach_col} / {fav_col} ---')
    print(f'  Train breach n={n_breach_train}, breach_rate={float(y_breach_train[breach_train_mask].mean()):.3f}')
    print(f'  Train fav n={n_fav_train}, mean={float(y_fav_train[fav_train_mask].mean()):.2f}')

    rf_breach = RandomForestClassifier(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        random_state=42,
        n_jobs=-1,
    )
    rf_breach.fit(X_train[breach_train_mask], y_breach_train[breach_train_mask])

    rf_fav = RandomForestRegressor(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        random_state=42,
        n_jobs=-1,
    )
    rf_fav.fit(X_train[fav_train_mask], y_fav_train[fav_train_mask])

    breach_proba_val = np.full(len(val_df), np.nan)
    fav_pred_val = np.full(len(val_df), np.nan)
    breach_proba_val[val_mask] = rf_breach.predict_proba(X_val[val_mask])[:, 1]
    fav_pred_val[val_mask] = rf_fav.predict(X_val[val_mask])

    entry_prices_val = lookup_entry_prices(val_df, ohlc_path)
    ohlc_val, times_val, time_idx_val = load_ohlc_index(ohlc_path)

    breach_metrics = compute_breach_metrics(
        y_breach_val[val_mask],
        breach_proba_val[val_mask],
        val_df['_year'].values[val_mask],
    )

    fav_residuals = fav_pred_val[val_mask] - y_fav_val[val_mask]
    fav_mse = float(np.mean(fav_residuals ** 2))
    fav_mae = float(np.mean(np.abs(fav_residuals)))
    reg_metrics = {
        'mse': round(fav_mse, 4),
        'mae': round(fav_mae, 4),
        'rmse': round(np.sqrt(fav_mse), 4),
    }

    best = None
    grid_results = []
    for p in P_GRID:
        for min_fav in MIN_FAV_GRID:
            for min_rr in MIN_RR_GRID:
                for tp_frac in TP_FRACTION_GRID:
                    trades = simulate_trades(
                        val_df, entry_prices_val, breach_proba_val, fav_pred_val,
                        ohlc_val, times_val, time_idx_val,
                        side=side, h=h, stop_offset=off,
                        p=p, min_fav_val=min_fav, min_rr=min_rr,
                        tp_fraction=tp_frac, cap=CAP,
                        spread=args.spread,
                    )
                    metrics = compute_trade_metrics(trades)
                    entry = {
                        'p': p, 'min_fav_val': min_fav, 'min_rr': min_rr,
                        'tp_fraction': tp_frac, 'cap': CAP,
                        **metrics,
                    }
                    grid_results.append(entry)
                    tpyr = metrics.get('trades_per_year', 0)
                    if tpyr >= 30 and (best is None or metrics['pf'] > best['pf']):
                        best = entry

    spread_results = {}
    for spread_label, spread_val in [('diagnostic_0.00', 0.0), ('stress_0.40', args.spread_stress)]:
        trades = simulate_trades(
            val_df, entry_prices_val, breach_proba_val, fav_pred_val,
            ohlc_val, times_val, time_idx_val,
            side=side, h=h, stop_offset=off,
            p=best['p'], min_fav_val=best['min_fav_val'], min_rr=best['min_rr'],
            tp_fraction=best['tp_fraction'], cap=CAP,
            spread=spread_val,
        ) if best else []
        spread_results[spread_label] = compute_trade_metrics(trades)

    result = {
        'h': h,
        'stop_offset_val': off,
        'side': side,
        'breach_col': breach_col,
        'fav_col': fav_col,
        'train_breach_n': int(n_breach_train),
        'train_fav_n': int(n_fav_train),
        'val_breach_metrics': breach_metrics,
        'val_reg_metrics': reg_metrics,
        'grid_results': grid_results,
        'best_on_val': best,
        'spread_results': spread_results,
    }
    return result


def _run_validation_baseline(args):
    """Stage 2 baseline: train на train, grid search на val. Test заморожен."""
    train_df = load_split(args.train, args.purge_bars)
    val_df = load_split(args.val, args.purge_bars)

    print(f'Train: {len(train_df)} rows, {train_df["_year"].min():.0f}-{train_df["_year"].max():.0f}')
    print(f'Val:   {len(val_df)} rows, {val_df["_year"].min():.0f}-{val_df["_year"].max():.0f}')

    results = {}
    for h in (6, 12):
        for off in (0.2, 0.5):
            for side in ('buy', 'sell'):
                key = f'{side}_H{h}_off{int(off * 10):02d}'
                result = _grid_search_trades(train_df, val_df, args.ohlc, h, off, side, args)
                if result is not None:
                    results[key] = result

    # Find overall best
    best_canonical = None
    for key, r in results.items():
        best = r.get('best_on_val')
        if best and best.get('trades_per_year', 0) >= 30:
            if best_canonical is None or best['pf'] > best_canonical['best_on_val']['pf']:
                best_canonical = r

    # Save frozen rule if we have a winner
    if best_canonical:
        frozen_rule = {
            'h': best_canonical['h'],
            'stop_offset_val': best_canonical['stop_offset_val'],
            'side': best_canonical['side'],
            'p': best_canonical['best_on_val']['p'],
            'min_fav_val': best_canonical['best_on_val']['min_fav_val'],
            'min_rr': best_canonical['best_on_val']['min_rr'],
            'tp_fraction': best_canonical['best_on_val']['tp_fraction'],
            'cap': CAP,
            'n_estimators': args.n_estimators,
            'max_depth': args.max_depth,
            'min_samples_leaf': args.min_samples_leaf,
            'selected_on': f'val_canonical_spread_{args.spread}',
            'val_pf': best_canonical['best_on_val']['pf'],
            'val_trades_per_year': best_canonical['best_on_val']['trades_per_year'],
        }
        os.makedirs(os.path.dirname(args.frozen_rule_json), exist_ok=True)
        with open(args.frozen_rule_json, 'w') as f:
            json.dump(frozen_rule, f, indent=2)
        print(f'\nFrozen rule saved: {args.frozen_rule_json}')
    else:
        frozen_rule = None

    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    report = {
        'stage': 'validation_baseline',
        'config': {
            'purge_bars': args.purge_bars,
            'n_estimators': args.n_estimators,
            'max_depth': args.max_depth,
            'min_samples_leaf': args.min_samples_leaf,
            'canonical_spread': args.spread,
            'spread_stress': args.spread_stress,
            'p_grid': P_GRID,
            'min_fav_grid': MIN_FAV_GRID,
            'min_rr_grid': MIN_RR_GRID,
            'tp_fraction_grid': TP_FRACTION_GRID,
            'cap': CAP,
            'feature_keys': BASE_CHANNEL_KEYS,
        },
        'test_not_run': True,
        'frozen_rule': frozen_rule,
        'results': results,
    }
    with open(args.output_json, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f'\nSaved: {args.output_json}')


def _run_frozen_test(args):
    """Frozen test: train на train+val, eval на test с замороженными параметрами."""
    if not args.frozen_rule or not os.path.exists(args.frozen_rule):
        print("!!! --frozen-rule is required and must exist for frozen test")
        sys.exit(1)

    with open(args.frozen_rule) as f:
        frozen_rule = json.load(f)

    h = frozen_rule['h']
    off = frozen_rule['stop_offset_val']
    side = frozen_rule['side']
    p = frozen_rule['p']
    min_fav_val = frozen_rule['min_fav_val']
    min_rr = frozen_rule['min_rr']
    tp_fraction = frozen_rule['tp_fraction']
    cap = frozen_rule['cap']

    print('=== FROZEN TEST ===')
    print(f'  Rule: {side} H={h} off={off}, p={p}, min_fav={min_fav_val}, min_rr={min_rr}, tp_frac={tp_fraction}')
    print(f'  Selected on: {frozen_rule["selected_on"]}')
    print(f'  Val PF: {frozen_rule["val_pf"]}, Val trades/yr: {frozen_rule["val_trades_per_year"]}')
    print(f'  Status: research candidate only (test previously used in Stage 1)')
    print()

    train_df = load_split(args.train, frozen_rule.get('purge_bars', h))
    val_df = load_split(args.val, frozen_rule.get('purge_bars', h))
    test_df = load_split(args.test, purge_bars=0)

    train_val_df = pd.concat([train_df, val_df], ignore_index=True)
    print(f'  Train+val: {len(train_val_df)} rows')
    print(f'  Test:      {len(test_df)} rows')
    print()

    breach_col = BREACH_TARGETS[h][off][side]
    fav_col = FAV_TARGETS[h][side]

    X_train_val, feature_names = extract_flat_base_features(train_val_df)
    X_test, _ = extract_flat_base_features(test_df)

    y_breach_train = train_val_df[breach_col].values
    y_fav_train = train_val_df[fav_col].values
    y_breach_test = test_df[breach_col].values
    y_fav_test = test_df[fav_col].values

    breach_train_mask = ~np.isnan(y_breach_train)
    fav_train_mask = ~np.isnan(y_fav_train)
    test_mask = ~np.isnan(y_breach_test) & ~np.isnan(y_fav_test)

    print(f'--- {breach_col} / {fav_col} ---')
    print(f'  Train+val breach n={breach_train_mask.sum()}')
    print(f'  Train+val fav n={fav_train_mask.sum()}')
    print(f'  Test n={test_mask.sum()}')

    rf_breach = RandomForestClassifier(
        n_estimators=frozen_rule.get('n_estimators', args.n_estimators),
        max_depth=frozen_rule.get('max_depth', args.max_depth),
        min_samples_leaf=frozen_rule.get('min_samples_leaf', args.min_samples_leaf),
        random_state=42,
        n_jobs=-1,
    )
    rf_breach.fit(X_train_val[breach_train_mask], y_breach_train[breach_train_mask])

    rf_fav = RandomForestRegressor(
        n_estimators=frozen_rule.get('n_estimators', args.n_estimators),
        max_depth=frozen_rule.get('max_depth', args.max_depth),
        min_samples_leaf=frozen_rule.get('min_samples_leaf', args.min_samples_leaf),
        random_state=42,
        n_jobs=-1,
    )
    rf_fav.fit(X_train_val[fav_train_mask], y_fav_train[fav_train_mask])

    breach_proba_test = np.full(len(test_df), np.nan)
    fav_pred_test = np.full(len(test_df), np.nan)
    breach_proba_test[test_mask] = rf_breach.predict_proba(X_test[test_mask])[:, 1]
    fav_pred_test[test_mask] = rf_fav.predict(X_test[test_mask])

    entry_prices_test = lookup_entry_prices(test_df, args.ohlc)
    ohlc_test, times_test, time_idx_test = load_ohlc_index(args.ohlc)

    breach_metrics = compute_breach_metrics(
        y_breach_test[test_mask],
        breach_proba_test[test_mask],
        test_df['_year'].values[test_mask],
    )

    trades_canonical = simulate_trades(
        test_df, entry_prices_test, breach_proba_test, fav_pred_test,
        ohlc_test, times_test, time_idx_test,
        side=side, h=h, stop_offset=off,
        p=p, min_fav_val=min_fav_val, min_rr=min_rr,
        tp_fraction=tp_fraction, cap=cap,
        spread=args.spread,
    )
    trades_stress = simulate_trades(
        test_df, entry_prices_test, breach_proba_test, fav_pred_test,
        ohlc_test, times_test, time_idx_test,
        side=side, h=h, stop_offset=off,
        p=p, min_fav_val=min_fav_val, min_rr=min_rr,
        tp_fraction=tp_fraction, cap=cap,
        spread=args.spread_stress,
    )
    trades_diag = simulate_trades(
        test_df, entry_prices_test, breach_proba_test, fav_pred_test,
        ohlc_test, times_test, time_idx_test,
        side=side, h=h, stop_offset=off,
        p=p, min_fav_val=min_fav_val, min_rr=min_rr,
        tp_fraction=tp_fraction, cap=cap,
        spread=0.0,
    )

    trade_metrics = {
        f'canonical_{args.spread}': compute_trade_metrics(trades_canonical),
        f'stress_{args.spread_stress}': compute_trade_metrics(trades_stress),
        'diagnostic_0.00': compute_trade_metrics(trades_diag),
    }

    print(f'\n  Test breach AUC: {breach_metrics.get("auc", "N/A")}')
    for label, tm in trade_metrics.items():
        print(f'  {label}: PF={tm.get("pf", "N/A")}, trades={tm.get("n_trades", 0)}, '
              f't/yr={tm.get("trades_per_year", 0)}, neg_yrs={tm.get("negative_years", 0)}')

    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    report = {
        'stage': 'frozen_test',
        'status': 'research_candidate',
        'note': 'Test previously used in Stage 1. Forward period or MT4 needed for live admission.',
        'frozen_rule': frozen_rule,
        'config': {
            'n_estimators': args.n_estimators,
            'max_depth': args.max_depth,
            'min_samples_leaf': args.min_samples_leaf,
            'canonical_spread': args.spread,
        },
        'breach_metrics': breach_metrics,
        'trade_metrics': trade_metrics,
    }
    with open(args.output_json, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f'\nSaved: {args.output_json}')


def main():
    parser = argparse.ArgumentParser(description='Baseline: fractal stop + fav trade (Stage 2)')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--test', default=None, help='Frozen test (only after freeze)')
    parser.add_argument('--frozen-rule', default=None,
                        help='JSON with frozen params. Required for --test. Disables grid search.')
    parser.add_argument('--ohlc', default='DATA/XAUUSD_H1_OHLC.csv')
    parser.add_argument('--purge-bars', type=int, default=12)
    parser.add_argument('--output-json', default='ML/reports/fractal_stop_fav.json')
    parser.add_argument('--frozen-rule-json', default='ML/reports/fractal_stop_fav_frozen_rule.json')
    parser.add_argument('--n-estimators', type=int, default=200)
    parser.add_argument('--max-depth', type=int, default=12)
    parser.add_argument('--min-samples-leaf', type=int, default=50)
    parser.add_argument('--spread', type=float, default=0.20,
                        help='Spread for order (canonical XAUUSD H1)')
    parser.add_argument('--spread-stress', type=float, default=0.40,
                        help='2x spread stress test')
    args = parser.parse_args()

    if args.test:
        _run_frozen_test(args)
    else:
        _run_validation_baseline(args)


if __name__ == '__main__':
    main()
