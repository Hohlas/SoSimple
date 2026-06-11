# =============================================================================
# Файл: ML/baseline/benchmark_fractal_stop_stage3.py
# Назначение: Stage 3 feature profiles — base_raw vs base_plus_path vs relative_geometry
#              RF breach classifier, metric uplift over Stage 1/2 baseline
# Язык: Python 3.10+
# Обновлён: 2026-06-10
# Использование:
#   python -m ML.baseline.benchmark_fractal_stop_stage3
# =============================================================================

import argparse, json, os, sys
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score

BASE_CHANNEL_KEYS = ['price', 'direction', 'front', 'back', 'strong', 'break', 'reverse', 'power',
                     'count', 'impulse']
MOV_HORIZONS = [3, 6, 12, 24, 48]

BREACH_TARGETS = {
    6: {0.2: {'buy': 'buy_stop_broken_H6_off02_flag', 'sell': 'sell_stop_broken_H6_off02_flag'},
        0.5: {'buy': 'buy_stop_broken_H6_off05_flag', 'sell': 'sell_stop_broken_H6_off05_flag'}},
    12: {0.2: {'buy': 'buy_stop_broken_H12_off02_flag', 'sell': 'sell_stop_broken_H12_off02_flag'},
         0.5: {'buy': 'buy_stop_broken_H12_off05_flag', 'sell': 'sell_stop_broken_H12_off05_flag'}},
}


def load_split(path, purge_bars=12):
    df = pd.read_csv(path, sep=';')
    if purge_bars > 0 and len(df) > purge_bars:
        df = df.iloc[:-purge_bars]
    df['_year'] = pd.to_datetime(df['time'], format='%Y.%m.%d %H:%M', errors='coerce').dt.year
    return df


def _extract_base(df, n_levels=100):
    """Stage 1 compatible: 10 channels x n_levels + ATR. NaN -> 0."""
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


def _extract_path(df, n_levels=100):
    """Folded mov_h + shift + atr_ratio. NaN -> 0."""
    extra_features, extra_names = [], []
    atr_row = pd.to_numeric(df['ATR'], errors='coerce').fillna(1.0).values
    up_idx = {3: 17, 6: 19, 12: 11, 24: 13, 48: 15}
    dn_idx = {3: 18, 6: 20, 12: 12, 24: 14, 48: 16}

    for level in range(n_levels):
        col = f'fractal{level}'
        if col not in df.columns:
            break
        parts = df[col].astype(str).str.split(':', expand=True)
        dirs = pd.to_numeric(parts[2], errors='coerce').fillna(0).values.astype(int)

        for h in MOV_HORIZONS:
            up_v = pd.to_numeric(parts[up_idx[h]], errors='coerce').fillna(0.0).values
            dn_v = pd.to_numeric(parts[dn_idx[h]], errors='coerce').fillna(0.0).values
            mov = np.where(dirs == -1, up_v, np.where(dirs == 1, dn_v, 0.0))
            extra_features.append(mov.astype(np.float64))
            extra_names.append(f'f{level}_mov_{h}')

        shift_v = pd.to_numeric(parts[22], errors='coerce').fillna(0).values
        extra_features.append(shift_v.astype(np.float64))
        extra_names.append(f'f{level}_shift')

        fa_v = pd.to_numeric(parts[21], errors='coerce').fillna(0.001).values
        ar = np.log(np.maximum(fa_v, 0.001) / np.maximum(atr_row, 0.001))
        extra_features.append(ar.astype(np.float64))
        extra_names.append(f'f{level}_atr_ratio')

    return np.column_stack(extra_features), extra_names


def _extract_geo(df, n_levels=100):
    """Relative geometry: price->(price-f0_price)/ATR + time + density. NaN -> 0."""
    features, names = [], []
    atr_row = pd.to_numeric(df['ATR'], errors='coerce').fillna(1.0).values
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
                vals = (vals - f0_price) / np.maximum(atr_row, 0.001)
            features.append(vals.astype(np.float64))
            names.append(f'f{level}_{key}')

    X = np.column_stack(features)

    # Density: fractal count in ±1/2/3 ATR around f0_price
    density = np.zeros((len(df), 6), dtype=np.float64)
    for i in range(len(df)):
        cur_atr = max(atr_row[i], 0.001)
        ref_price = f0_price[i]
        for lvl in range(n_levels):
            col = f'fractal{lvl}'
            if col not in df.columns:
                break
            fp = str(df.iloc[i].get(col, ''))
            if not fp or fp == 'nan':
                break
            parts = fp.split(':')
            if len(parts) < 3:
                break
            p = float(parts[1]) if parts[1] else 0.0
            d_val = parts[2]
            d = int(float(d_val)) if d_val and d_val != 'nan' else 0
            if d == 0:
                continue
            dist = p - ref_price
            for b_idx, b in enumerate([1.0, 2.0, 3.0]):
                if abs(dist) <= b * cur_atr:
                    if d == 1:
                        density[i, b_idx] += 1
                    elif d == -1:
                        density[i, b_idx + 3] += 1

    X = np.column_stack([X, density])
    for b in [1, 2, 3]:
        names.extend([f'density_peaks_atr{b}', f'density_valleys_atr{b}'])

    # Time features
    times = df['time'].values
    hour_sin, hour_cos = np.zeros(len(df)), np.zeros(len(df))
    dow_sin, dow_cos = np.zeros(len(df)), np.zeros(len(df))
    for i, t in enumerate(times):
        try:
            dt = datetime.strptime(str(t), '%Y.%m.%d %H:%M')
            h = dt.hour + dt.minute / 60.0
            hour_sin[i] = np.sin(2 * np.pi * h / 24)
            hour_cos[i] = np.cos(2 * np.pi * h / 24)
            d = dt.weekday()
            dow_sin[i] = np.sin(2 * np.pi * d / 7)
            dow_cos[i] = np.cos(2 * np.pi * d / 7)
        except (ValueError, TypeError):
            pass

    X = np.column_stack([X, hour_sin, hour_cos, dow_sin, dow_cos])
    names.extend(['hour_sin', 'hour_cos', 'dow_sin', 'dow_cos'])

    X = np.column_stack([X, atr_row])
    names.append('ATR')
    return X, names


def profile_base_raw(df):
    return _extract_base(df)


def profile_base_plus_path(df):
    Xb, nb = _extract_base(df)
    Xp, np_list = _extract_path(df)
    return np.column_stack([Xb, Xp]), nb + np_list


def profile_relative_geometry(df):
    return _extract_geo(df)


def compute_metrics(y_true, y_pred_proba, years=None):
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


def main():
    parser = argparse.ArgumentParser(description='Stage 3: 3 feature profiles vs breach AUC')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--purge-bars', type=int, default=12)
    parser.add_argument('--output-json', default='ML/reports/stage3_profiles.json')
    parser.add_argument('--n-estimators', type=int, default=200)
    parser.add_argument('--max-depth', type=int, default=12)
    parser.add_argument('--min-samples-leaf', type=int, default=50)
    args = parser.parse_args()

    train_df = load_split(args.train, args.purge_bars)
    val_df = load_split(args.val, args.purge_bars)
    print(f'Train: {len(train_df)} rows, Val: {len(val_df)} rows')

    profiles = {
        'base_raw': profile_base_raw,
        'base_plus_path': profile_base_plus_path,
        'relative_geometry': profile_relative_geometry,
    }

    targets = []
    for h in (6, 12):
        for off in (0.2, 0.5):
            for side in ('buy', 'sell'):
                targets.append((BREACH_TARGETS[h][off][side], f'{side}_H{h}_off{int(off*10):02d}'))

    all_results = {}

    for profile_name, profile_fn in profiles.items():
        print(f'\n{"="*60}')
        print(f'Profile: {profile_name}')
        print(f'{"="*60}')

        X_train, train_names = profile_fn(train_df)
        X_val, val_names = profile_fn(val_df)
        print(f'  Features: {X_train.shape[1]}')

        profile_results = {}
        baseline_aucs = {}

        for target_col, target_label in targets:
            y_train = train_df[target_col].values
            y_val = val_df[target_col].values
            train_mask = ~np.isnan(y_train)
            val_mask = ~np.isnan(y_val)

            n_tr = train_mask.sum()
            if n_tr < 50:
                profile_results[target_label] = {'status': 'SKIP', 'reason': f'train n={n_tr}'}
                continue

            X_tr = X_train[train_mask]; y_tr = y_train[train_mask]
            X_v = X_val[val_mask]; y_v = y_val[val_mask]

            rf = RandomForestClassifier(n_estimators=args.n_estimators, max_depth=args.max_depth,
                                        min_samples_leaf=args.min_samples_leaf,
                                        random_state=42, n_jobs=-1)
            rf.fit(X_tr, y_tr)
            pred_val = rf.predict_proba(X_v)[:, 1]
            metrics = compute_metrics(y_v, pred_val, val_df['_year'].values[val_mask])

            profile_results[target_label] = {'train_n': int(n_tr),
                                             'val_n': int(val_mask.sum()), 'rf_val': metrics}

            if profile_name == 'base_raw':
                baseline_aucs[target_label] = metrics.get('auc') if metrics else None
            auc_s = f'{metrics.get("auc", "N/A"):.4f}' if metrics and metrics.get('auc') else 'N/A'
            print(f'  {target_label:20s}: AUC={auc_s}')

        all_results[profile_name] = {'n_features': X_train.shape[1],
                                     'targets': profile_results}

    # Deltas vs base_raw
    print(f'\n{"="*60}')
    print('DELTAS vs base_raw (bp = basis points × 10000)')
    print(f'{"="*60}')
    print(f'{"Target":>20s} | {"base_plus_path":>20s} | {"relative_geometry":>20s}')
    print(f'{"":>20s} | {"ΔAUC(bp)":>10s} {"Δlift":>8s} | {"ΔAUC(bp)":>10s} {"Δlift":>8s}')
    print('-' * 70)

    deltas = {}
    for target_label in sorted(all_results['base_raw']['targets'].keys()):
        base = all_results['base_raw']['targets'][target_label].get('rf_val')
        if base is None:
            continue
        base_auc = base.get('auc', 0)
        base_lift = base.get('lift', 0)

        row = []
        for profile_name in ['base_plus_path', 'relative_geometry']:
            pr = all_results[profile_name]['targets'].get(target_label, {}).get('rf_val')
            if pr is None:
                row.extend([0.0, 0.0])
                continue
            dauc = round((pr.get('auc', 0) - base_auc) * 10000)
            dlift = round(pr.get('lift', 0) - base_lift, 2)
            row.extend([dauc, dlift])

        print(f'{target_label:>20s} | {row[0]:+10d} {row[1]:+8.2f} | {row[2]:+10d} {row[3]:+8.2f}')

        deltas[target_label] = {
            'base_auc': base_auc, 'base_lift': base_lift,
            'base_plus_path': {'delta_auc_bp': row[0], 'delta_lift': row[1]},
            'relative_geometry': {'delta_auc_bp': row[2], 'delta_lift': row[3]},
        }

    # Yearly stability
    print(f'\n{"="*60}')
    print('YEARLY STABILITY: AUC by year (val), AUC<0.55 = fail')
    print(f'{"="*60}')
    for profile_name in profiles:
        results = all_results[profile_name]['targets']
        fails = total = 0
        for tr in results.values():
            rf_val = tr.get('rf_val')
            if rf_val is None or 'yearly' not in rf_val:
                continue
            for yr, ym in rf_val['yearly'].items():
                if ym.get('auc') is not None:
                    total += 1
                    if ym['auc'] < 0.55:
                        fails += 1
        print(f'{profile_name:>20s}: {fails}/{total} year-slices AUC<0.55')

    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    output = {
        'config': {'n_estimators': args.n_estimators, 'max_depth': args.max_depth,
                   'min_samples_leaf': args.min_samples_leaf, 'purge_bars': args.purge_bars,
                   'profiles': {p: {'n_features': all_results[p]['n_features']}
                                for p in profiles}},
        'results': all_results, 'deltas': deltas,
    }
    with open(args.output_json, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f'\nSaved: {args.output_json}')


if __name__ == '__main__':
    main()
