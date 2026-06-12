# =============================================================================
# Файл: ML/baseline/benchmark_fractal_stop_stage3_2.py
# Назначение: Stage 3.2 — XGBoost на 4 профилях
#              base_raw, time_only, base_raw_plus_time, relative_geometry_clean
#              8 breach targets, validation-only winner selection.
#              Диагностика: lift по часам, калибровка, BUY/SELL, год/квартал, PF proxy.
# Язык: Python 3.10+
# Обновлён: 2026-06-11
# Использование:
#   python -m ML.baseline.benchmark_fractal_stop_stage3_2
#
# Критерии:
#   - base_raw_plus_time AUC > time_only (фракталы несут сигнал поверх времени)
#   - base_raw_plus_time AUC > RF base_raw (XGBoost лучше RF)
#   - relative_geometry_clean не деградирует vs base_raw_plus_time (лишние фичи не шумят)
#   - winner только по validation, test не открывать
# =============================================================================

import argparse, json, os
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score
import xgboost as xgb

BASE_CHANNEL_KEYS = ['price', 'direction', 'front', 'back', 'strong', 'break', 'reverse', 'power',
                     'count', 'impulse']

BREACH_TARGETS = {
    6: {0.2: {'buy': 'buy_stop_broken_H6_off02_flag', 'sell': 'sell_stop_broken_H6_off02_flag'},
        0.5: {'buy': 'buy_stop_broken_H6_off05_flag', 'sell': 'sell_stop_broken_H6_off05_flag'}},
    12: {0.2: {'buy': 'buy_stop_broken_H12_off02_flag', 'sell': 'sell_stop_broken_H12_off02_flag'},
         0.5: {'buy': 'buy_stop_broken_H12_off05_flag', 'sell': 'sell_stop_broken_H12_off05_flag'}},
}

# Mapping from breach target label to fav_val column
FAV_VAL_MAP = {
    'buy_H6': 'target_buy_H6_val',
    'sell_H6': 'target_sell_H6_val',
    'buy_H12': 'target_buy_H12_val',
    'sell_H12': 'target_sell_H12_val',
}


def load_split(path, purge_bars=12):
    df = pd.read_csv(path, sep=';')
    if purge_bars > 0 and len(df) > purge_bars:
        df = df.iloc[:-purge_bars]
    df['_year'] = pd.to_datetime(df['time'], format='%Y.%m.%d %H:%M', errors='coerce').dt.year
    return df


# ---------------------------------------------------------------------------
# Feature extraction (reused from Stage 3.1)
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


# ---------------------------------------------------------------------------
# Profile constructors
# ---------------------------------------------------------------------------

def profile_base_raw(df):
    return _extract_base(df)


def profile_time_only(df):
    return _extract_time(df)


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
# Metrics & diagnostics
# ---------------------------------------------------------------------------

def compute_auc_metrics(y_true, y_pred_proba, years=None):
    mask = ~np.isnan(y_true)
    y_true, y_pred_proba = y_true[mask], y_pred_proba[mask]
    if years is not None:
        years = years[mask]
    if len(y_true) < 10:
        return None
    unique_classes = np.unique(y_true)
    if len(unique_classes) < 2:
        return {'auc': None, 'pr_auc': None, 'breach_rate': round(float(y_true.mean()), 4),
                'n': int(len(y_true)), 'note': 'single_class'}
    auc = roc_auc_score(y_true, y_pred_proba)
    pr_auc = average_precision_score(y_true, y_pred_proba)
    overall_rate = float(y_true.mean())
    cutoff = np.quantile(y_pred_proba, 0.20)
    low_risk_mask = y_pred_proba <= cutoff
    low_risk_rate = float(y_true[low_risk_mask].mean()) if low_risk_mask.sum() > 0 else 0.0
    lift = overall_rate / low_risk_rate if low_risk_rate > 0 else float('inf')
    metrics = {'auc': round(auc, 4), 'pr_auc': round(pr_auc, 4),
               'breach_rate': round(overall_rate, 4),
               'low_risk_breach_rate': round(low_risk_rate, 4),
               'lift': round(lift, 2), 'n': int(len(y_true))}
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
                yearly[int(yr)] = {'auc': round(yr_auc, 4) if yr_auc is not None else None,
                                   'n': int(ym.sum()),
                                   'breach_rate': round(float(y_true[ym].mean()), 4)}
        metrics['yearly'] = yearly
    return metrics


def compute_lift_by_hour(y_true, y_pred_proba, times_dt):
    """Breach rate and lift per hour bucket. All arrays pre-masked (same length)."""
    overall_rate = float(y_true.mean())

    hours = times_dt.dt.hour.values
    result = {}
    for h in range(24):
        hm = (hours == h)
        if hm.sum() < 10:
            result[h] = {'n': int(hm.sum()), 'breach_rate': None, 'lift': None}
            continue
        h_rate = float(y_true[hm].mean())
        result[h] = {'n': int(hm.sum()),
                     'breach_rate': round(h_rate, 4),
                     'lift': round(overall_rate / h_rate, 2) if h_rate > 0 else None}
    return result


def compute_calibration(y_true, y_pred_proba, n_bins=10):
    """Expected Calibration Error (ECE). Arrays pre-masked (same length)."""
    if len(y_true) < n_bins * 10:
        return {'ece': None, 'n': len(y_true), 'note': 'too_few_samples'}

    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    bins = []
    for i in range(n_bins):
        in_bin = (y_pred_proba >= bin_edges[i]) & (y_pred_proba < bin_edges[i + 1])
        if in_bin.sum() < 5:
            bins.append({'bin_start': round(bin_edges[i], 2), 'n': int(in_bin.sum()),
                         'pred_mean': None, 'obs_rate': None, 'contrib': None})
            continue
        pred_mean = float(y_pred_proba[in_bin].mean())
        obs_rate = float(y_true[in_bin].mean())
        contrib = abs(pred_mean - obs_rate) * in_bin.sum() / len(y_true)
        ece += contrib
        bins.append({'bin_start': round(bin_edges[i], 2), 'n': int(in_bin.sum()),
                     'pred_mean': round(pred_mean, 4), 'obs_rate': round(obs_rate, 4),
                     'contrib': round(contrib, 6)})

    return {'ece': round(ece, 4), 'n_bins': n_bins, 'bins': bins}


def compute_quarterly_auc(y_true, y_pred_proba, times_dt):
    """AUC per quarter (YYYY-Q format). Arrays pre-masked (same length)."""
    quarters = times_dt.dt.year.astype(str) + '-Q' + times_dt.dt.quarter.astype(str)
    result = {}
    for q in sorted(set(quarters)):
        qm = (quarters == q)
        if qm.sum() < 20:
            continue
        q_unique = np.unique(y_true[qm])
        if len(q_unique) < 2:
            result[q] = {'auc': None, 'n': int(qm.sum()), 'note': 'single_class'}
            continue
        try:
            q_auc = roc_auc_score(y_true[qm], y_pred_proba[qm])
        except ValueError:
            q_auc = None
        result[q] = {'auc': round(q_auc, 4) if q_auc is not None else None,
                     'n': int(qm.sum())}
    return result


def simple_pf_proxy(y_true, y_pred_proba, fav_val, atr_val, threshold_pct=20):
    """Minimal PnL proxy: top-K% predictions vs actual breach outcome.

    Uses fav_val (favourable move in ATR units) for true-positive PnL.
    False positives lose spread (0.20 * ATR).
    """
    mask = ~(np.isnan(y_true) | np.isnan(y_pred_proba) | np.isnan(fav_val) | np.isnan(atr_val))
    y_true = y_true[mask]
    y_pred_proba = y_pred_proba[mask]
    fav_val = fav_val[mask]
    atr_val = atr_val[mask]

    if len(y_true) < 50:
        return None

    threshold = np.quantile(y_pred_proba, 0.80)
    trade_mask = y_pred_proba >= threshold
    n_trades = int(trade_mask.sum())
    if n_trades == 0:
        return {'pf': None, 'n_trades': 0, 'note': 'no_trades_at_threshold'}

    tp = trade_mask & (y_true == 1)
    fp = trade_mask & (y_true == 0)
    n_tp = int(tp.sum())
    n_fp = int(fp.sum())

    gross_profit = np.sum(np.maximum(fav_val[tp], 0) * atr_val[tp])
    gross_loss_from_tp = np.sum(np.abs(np.minimum(fav_val[tp], 0)) * atr_val[tp])
    spread_loss = np.sum(0.20 * atr_val[fp])
    gross_loss = gross_loss_from_tp + spread_loss

    if gross_loss == 0:
        pf = float('inf') if gross_profit > 0 else 1.0
    else:
        pf = round(gross_profit / gross_loss, 3)

    return {'pf': pf, 'n_trades': n_trades, 'n_tp': n_tp, 'n_fp': n_fp,
            'gross_profit': round(float(gross_profit), 2),
            'gross_loss': round(float(gross_loss), 2)}


# ---------------------------------------------------------------------------
# XGBoost training
# ---------------------------------------------------------------------------

def train_xgb(X_train, y_train, X_val, y_val, random_state=42):
    """Train XGBoost with early stopping."""
    neg = int((y_train == 0).sum())
    pos = int((y_train == 1).sum())
    scale_pos_weight = neg / pos if pos > 0 else 1.0

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        objective='binary:logistic',
        eval_metric='auc',
        early_stopping_rounds=20,
        random_state=random_state,
        n_jobs=-1,
        verbosity=0,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )
    return model


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Stage 3.2: XGBoost on 4 profiles')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--purge-bars', type=int, default=12)
    parser.add_argument('--output-json', default='ML/reports/stage3_2_xgboost.json')
    parser.add_argument('--rf-baseline-json', default='ML/reports/stage3_1_profiles.json')
    args = parser.parse_args()

    train_df = load_split(args.train, args.purge_bars)
    val_df = load_split(args.val, args.purge_bars)
    print(f'Train: {len(train_df)} rows, Val: {len(val_df)} rows')

    profiles = {
        'base_raw': profile_base_raw,
        'time_only': profile_time_only,
        'base_raw_plus_time': profile_base_raw_plus_time,
        'relative_geometry_clean': profile_relative_geometry_clean,
    }

    targets = []
    for h in (6, 12):
        for off in (0.2, 0.5):
            for side in ('buy', 'sell'):
                targets.append((BREACH_TARGETS[h][off][side],
                                f'{side}_H{h}_off{int(off*10):02d}',
                                f'{side}_H{h}'))

    all_results = {}

    for profile_name, profile_fn in profiles.items():
        print(f'\n{"="*60}')
        print(f'Profile: {profile_name}')
        print(f'{"="*60}')

        X_train, train_names = profile_fn(train_df)
        X_val, val_names = profile_fn(val_df)
        print(f'  Features: {X_train.shape[1]}')

        profile_results = {}

        for target_col, target_label, target_key in targets:
            y_train = train_df[target_col].values
            y_val = val_df[target_col].values
            train_mask = ~np.isnan(y_train)
            val_mask = ~np.isnan(y_val)

            n_tr = train_mask.sum()
            if n_tr < 50:
                profile_results[target_label] = {'status': 'SKIP', 'reason': f'train n={n_tr}'}
                continue

            X_tr = X_train[train_mask]
            y_tr = y_train[train_mask]
            X_v = X_val[val_mask]
            y_v = y_val[val_mask]

            model = train_xgb(X_tr, y_tr, X_v, y_v)
            pred_val = model.predict_proba(X_v)[:, 1]

            metrics = compute_auc_metrics(y_v, pred_val, val_df['_year'].values[val_mask])

            # Diagnostics (all use pre-masked arrays: y_v, pred_val)
            val_times_full = pd.to_datetime(val_df['time'], format='%Y.%m.%d %H:%M',
                                            errors='coerce')
            val_times_masked = val_times_full[val_mask].reset_index(drop=True)
            hour_lift = compute_lift_by_hour(y_v, pred_val, val_times_masked)
            calibration = compute_calibration(y_v, pred_val)
            quarterly = compute_quarterly_auc(y_v, pred_val, val_times_masked)

            # Feature importance
            imp = model.feature_importances_
            feat_imp = sorted(
                [{'name': train_names[i], 'gain': round(float(imp[i]), 6)}
                 for i in range(len(imp)) if imp[i] > 0],
                key=lambda x: x['gain'], reverse=True)[:20]

            # PF proxy using fav_val columns
            fav_col = FAV_VAL_MAP.get(target_key)
            pf_proxy = None
            if fav_col and fav_col in val_df.columns:
                fav_full = val_df[fav_col].values
                atr_full = pd.to_numeric(val_df['ATR'], errors='coerce').fillna(0).values
                pf_proxy = simple_pf_proxy(y_v, pred_val,
                                           fav_full[val_mask],
                                           atr_full[val_mask])

            profile_results[target_label] = {
                'train_n': int(n_tr), 'val_n': int(val_mask.sum()),
                'xgb_val': metrics,
                'hour_lift': hour_lift,
                'calibration': calibration,
                'quarterly_auc': quarterly,
                'top_features': feat_imp,
                'pf_proxy': pf_proxy,
                'n_estimators_used': int(getattr(model, 'best_iteration', model.n_estimators)),
            }

            auc_s = f'{metrics.get("auc", "N/A"):.4f}' if metrics and metrics.get('auc') else 'N/A'
            print(f'  {target_label:20s}: AUC={auc_s}  (iters={getattr(model, "best_iteration", model.n_estimators)})')

        all_results[profile_name] = {'n_features': X_train.shape[1],
                                     'targets': profile_results}

    # Load RF baseline for delta comparison
    rf_aucs = {}
    try:
        with open(args.rf_baseline_json) as f:
            rf_data = json.load(f)
        rf_raw = rf_data.get('results', {}).get('base_raw', {}).get('targets', {})
        for t, v in rf_raw.items():
            rfv = v.get('rf_val')
            if rfv and rfv.get('auc'):
                rf_aucs[t] = rfv['auc']
    except FileNotFoundError:
        print(f'WARNING: RF baseline JSON not found ({args.rf_baseline_json}), skipping RF deltas')

    # Deltas vs RF base_raw
    print(f'\n{"="*100}')
    print('DELTAS vs RF base_raw (bp)')
    print(f'{"="*100}')
    other_profiles = [p for p in profiles if p != 'base_raw']
    header = f'{"Target":>20s} |'
    for p in other_profiles:
        header += f' {p:>28s} |'
    print(header)
    sub_h = f'{"":>20s} |'
    for _p in other_profiles:
        sub_h += f' {"ΔAUC(bp)":>10s} {"Δlift":>8s} {"PF":>6s} |'
    print(sub_h)
    print('-' * len(sub_h))

    deltas = {}
    for target_label in sorted(all_results['base_raw']['targets'].keys()):
        base = all_results['base_raw']['targets'][target_label].get('xgb_val')
        if base is None:
            continue
        base_auc = base.get('auc', 0)
        base_lift = base.get('lift', 0)

        row_parts = f'{target_label:>20s} |'
        dl_entry = {}
        for profile_name in other_profiles:
            pr = all_results[profile_name]['targets'].get(target_label, {}).get('xgb_val')
            if pr is None:
                row_parts += f' {"N/A":>10s} {"N/A":>8s} {"N/A":>6s} |'
                dl_entry[profile_name] = {'delta_auc_bp': 0, 'delta_lift': 0.0}
                continue
            dauc = round((pr.get('auc', 0) - base_auc) * 10000)
            dlift = round(pr.get('lift', 0) - base_lift, 2)

            pf_px = all_results[profile_name]['targets'][target_label].get('pf_proxy')
            pf_str = f'{pf_px["pf"]:.2f}' if pf_px and pf_px.get('pf') is not None else 'N/A'

            row_parts += f' {dauc:+10d} {dlift:+8.2f} {pf_str:>6s} |'
            dl_entry[profile_name] = {'delta_auc_bp': dauc, 'delta_lift': dlift}

        print(row_parts)
        deltas[target_label] = {'xgb_base_auc': base_auc, 'xgb_base_lift': base_lift, **dl_entry}

    # RF deltas
    if rf_aucs:
        print(f'\n{"="*100}')
        print('DELTAS vs RF base_raw (bp)')
        print(f'{"="*100}')
        header2 = f'{"Target":>20s} | XGB_base_raw_vs_RF | XGB_time_only_vs_RF | XGB_base+time_vs_RF | XGB_geom_clean_vs_RF'
        print(header2)
        print(f'{"":>20s} | {"ΔAUC":>16s} | {"ΔAUC":>16s} | {"ΔAUC":>17s} | {"ΔAUC":>18s}')
        print('-' * 95)

        rf_deltas = {}
        for target_label in sorted(rf_aucs.keys()):
            rf_auc = rf_aucs[target_label]
            row2 = f'{target_label:>20s} |'
            for profile_name in ['base_raw', 'time_only', 'base_raw_plus_time', 'relative_geometry_clean']:
                xgb_r = all_results.get(profile_name, {}).get('targets', {}).get(target_label, {}).get('xgb_val')
                if xgb_r and xgb_r.get('auc'):
                    dauc = round((xgb_r['auc'] - rf_auc) * 10000)
                    row2 += f' {dauc:+16d}'
                else:
                    row2 += f' {"N/A":>16s}'
            print(row2)
            rf_deltas[target_label] = {'rf_auc': rf_auc}

    # Mean deltas
    print(f'\n{"="*80}')
    print('MEAN DELTAS across 8 targets (bp)')
    print(f'{"="*80}')
    print(f'{"Profile":>30s} | {"ΔAUC_vs_XGB_base":>16s} | {"ΔAUC_vs_RF_base":>16s}')
    print('-' * 70)
    for profile_name in other_profiles:
        auc_bps = [deltas[t][profile_name]['delta_auc_bp'] for t in deltas]
        mean_auc = round(sum(auc_bps) / len(auc_bps))
        rf_bps = None
        if rf_aucs:
            rf_bps_list = []
            for t in deltas:
                xgb_r = all_results.get(profile_name, {}).get('targets', {}).get(t, {}).get('xgb_val')
                rf_a = rf_aucs.get(t)
                if xgb_r and xgb_r.get('auc') and rf_a:
                    rf_bps_list.append(round((xgb_r['auc'] - rf_a) * 10000))
            if rf_bps_list:
                rf_bps = round(sum(rf_bps_list) / len(rf_bps_list))
        rf_str = f'{rf_bps:+16d}' if rf_bps is not None else f'{"N/A":>16s}'
        print(f'{profile_name:>30s} | {mean_auc:+16d} | {rf_str}')

    # Yearly stability
    print(f'\n{"="*60}')
    print('YEARLY STABILITY: AUC by year (val), AUC<0.55 = fail')
    print(f'{"="*60}')
    for profile_name in profiles:
        results = all_results[profile_name]['targets']
        fails = total = 0
        for tr in results.values():
            xgb_val = tr.get('xgb_val')
            if xgb_val is None or 'yearly' not in xgb_val:
                continue
            for yr, ym in xgb_val['yearly'].items():
                if ym.get('auc') is not None:
                    total += 1
                    if ym['auc'] < 0.55:
                        fails += 1
        print(f'{profile_name:>30s}: {fails}/{total} year-slices AUC<0.55')

    # Key diagnostic: time_only vs base_raw
    print(f'\n{"="*80}')
    print('KEY CHECK: time_only vs base_raw (фракталы несут сигнал поверх времени?)')
    print(f'{"="*80}')
    time_only_aucs = []
    base_raw_aucs = []
    for target_label in sorted(all_results['base_raw']['targets'].keys()):
        t_auc = all_results['time_only']['targets'].get(target_label, {}).get('xgb_val', {}).get('auc')
        b_auc = all_results['base_raw']['targets'].get(target_label, {}).get('xgb_val', {}).get('auc')
        if t_auc and b_auc:
            time_only_aucs.append(t_auc)
            base_raw_aucs.append(b_auc)
            delta = round((b_auc - t_auc) * 10000)
            print(f'  {target_label:20s}: base_raw={b_auc:.4f}  time_only={t_auc:.4f}  Δ={delta:+d} bp')

    if time_only_aucs:
        mean_time = sum(time_only_aucs) / len(time_only_aucs)
        mean_base = sum(base_raw_aucs) / len(base_raw_aucs)
        print(f'  {"MEAN":>20s}: base_raw={mean_base:.4f}  time_only={mean_time:.4f}  '
              f'Δ={round((mean_base - mean_time) * 10000):+d} bp')

    # Save
    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    output = {
        'config': {
            'profiles': {p: {'n_features': all_results[p]['n_features']} for p in profiles},
            'purge_bars': args.purge_bars,
        },
        'results': all_results,
        'deltas_vs_xgb_base': deltas,
        'rf_deltas': rf_deltas if rf_aucs else {},
    }
    with open(args.output_json, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f'\nSaved: {args.output_json}')


if __name__ == '__main__':
    main()
