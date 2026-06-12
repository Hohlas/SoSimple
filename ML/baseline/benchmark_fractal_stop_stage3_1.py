# =============================================================================
# Файл: ML/baseline/benchmark_fractal_stop_stage3_1.py
# Назначение: Stage 3.1 — декомпозиция relative_geometry на компоненты
#              Изоляция price/ATR, density_excl_f0, time.
#              RF breach classifier, metric uplift vs base_raw.
#              fix_missing (только валидные фракталы) вшит, а не отдельная гипотеза.
# Язык: Python 3.10+
# Обновлён: 2026-06-11
# Использование:
#   python -m ML.baseline.benchmark_fractal_stop_stage3_1
#
# Критерии успеха:
#   - relative_geometry_clean сохраняет >=60% среднего ΔAUC Stage 3
#   - ΔAUC положительный на >=6/8 таргетов
#   - 0 year-slices AUC<0.55
#   - lift не деградирует vs base_raw
#   - winner выбирается только по validation
# =============================================================================

import argparse, json, os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score

BASE_CHANNEL_KEYS = ['price', 'direction', 'front', 'back', 'strong', 'break', 'reverse', 'power',
                     'count', 'impulse']

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


def _extract_price_normalized(df, n_levels=100):
    """Base channels with price -> (price - f0_price) / ATR.
    Only normalizes valid fractal cells (dir != 0); empty cells stay 0.0."""
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
    """Density: fractal count in ±1/2/3 ATR around f0_price, per row.
    excl_f0=True: skip fractal0 (constant +1 for all rows)."""
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
    """Cyclical time features: hour sin/cos + day-of-week sin/cos."""
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


def profile_relative_price_only(df):
    return _extract_price_normalized(df)


def profile_relative_price_plus_density_excl_f0(df):
    X, names = _extract_price_normalized(df)
    Xd, nd = _extract_density(df, excl_f0=True)
    return np.column_stack([X, Xd]), names + nd


def profile_relative_price_plus_time(df):
    X, names = _extract_price_normalized(df)
    Xt, nt = _extract_time(df)
    return np.column_stack([X, Xt]), names + nt


def profile_relative_geometry_clean(df):
    X, names = _extract_price_normalized(df)
    Xd, nd = _extract_density(df, excl_f0=True)
    Xt, nt = _extract_time(df)
    return np.column_stack([X, Xd, Xt]), names + nd + nt


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Stage 3.1: decompose relative_geometry into components')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--purge-bars', type=int, default=12)
    parser.add_argument('--output-json', default='ML/reports/stage3_1_profiles.json')
    parser.add_argument('--n-estimators', type=int, default=200)
    parser.add_argument('--max-depth', type=int, default=12)
    parser.add_argument('--min-samples-leaf', type=int, default=50)
    args = parser.parse_args()

    train_df = load_split(args.train, args.purge_bars)
    val_df = load_split(args.val, args.purge_bars)
    print(f'Train: {len(train_df)} rows, Val: {len(val_df)} rows')

    profiles = {
        'base_raw': profile_base_raw,
        'relative_price_only': profile_relative_price_only,
        'relative_price_plus_density_excl_f0': profile_relative_price_plus_density_excl_f0,
        'relative_price_plus_time': profile_relative_price_plus_time,
        'relative_geometry_clean': profile_relative_geometry_clean,
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

        for target_col, target_label in targets:
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

            rf = RandomForestClassifier(
                n_estimators=args.n_estimators, max_depth=args.max_depth,
                min_samples_leaf=args.min_samples_leaf,
                random_state=42, n_jobs=-1)
            rf.fit(X_tr, y_tr)
            pred_val = rf.predict_proba(X_v)[:, 1]
            metrics = compute_metrics(y_v, pred_val, val_df['_year'].values[val_mask])

            profile_results[target_label] = {'train_n': int(n_tr),
                                             'val_n': int(val_mask.sum()), 'rf_val': metrics}

            auc_s = f'{metrics.get("auc", "N/A"):.4f}' if metrics and metrics.get('auc') else 'N/A'
            print(f'  {target_label:20s}: AUC={auc_s}')

        all_results[profile_name] = {'n_features': X_train.shape[1],
                                     'targets': profile_results}

    # Deltas vs base_raw (bp)
    print(f'\n{"="*80}')
    print('DELTAS vs base_raw (bp = basis points x 10000)')
    print(f'{"="*80}')
    other_profiles = [p for p in profiles if p != 'base_raw']
    header = f'{"Target":>20s} |'
    for p in other_profiles:
        header += f' {p:>26s} |'
    print(header)
    sub_h = f'{"":>20s} |'
    for _p in other_profiles:
        sub_h += f' {"ΔAUC(bp)":>10s} {"Δlift":>8s} {"Δlrb":>8s} |'
    print(sub_h)
    print('-' * len(sub_h))

    deltas = {}
    for target_label in sorted(all_results['base_raw']['targets'].keys()):
        base = all_results['base_raw']['targets'][target_label].get('rf_val')
        if base is None:
            continue
        base_auc = base.get('auc', 0)
        base_lift = base.get('lift', 0)
        base_lrb = base.get('low_risk_breach_rate', 0)

        row = []
        dl_entry = {}
        for profile_name in other_profiles:
            pr = all_results[profile_name]['targets'].get(target_label, {}).get('rf_val')
            if pr is None:
                row.extend([0.0, 0.0, 0.0])
                dl_entry[profile_name] = {'delta_auc_bp': 0, 'delta_lift': 0.0,
                                          'delta_low_risk_breach_rate_bp': 0.0}
                continue
            dauc = round((pr.get('auc', 0) - base_auc) * 10000)
            dlift = round(pr.get('lift', 0) - base_lift, 2)
            dlrb = round((pr.get('low_risk_breach_rate', 0) - base_lrb) * 10000)
            row.extend([dauc, dlift, dlrb])
            dl_entry[profile_name] = {'delta_auc_bp': dauc, 'delta_lift': dlift,
                                      'delta_low_risk_breach_rate_bp': dlrb}

        parts = f'{target_label:>20s} |'
        for i in range(len(other_profiles)):
            parts += f' {row[i*3]:+10d} {row[i*3+1]:+8.2f} {row[i*3+2]:+8d} |'
        print(parts)

        deltas[target_label] = {'base_auc': base_auc, 'base_lift': base_lift,
                                **dl_entry}

    # Mean deltas across all targets
    print(f'\n{"="*80}')
    print('MEAN DELTAS across 8 targets (bp)')
    print(f'{"="*80}')
    print(f'{"Profile":>30s} | {"ΔAUC":>10s} {"Δlift":>8s} {"Δlrb":>8s}')
    print('-' * 60)
    for profile_name in other_profiles:
        auc_bps = [deltas[t][profile_name]['delta_auc_bp'] for t in deltas]
        lifts = [deltas[t][profile_name]['delta_lift'] for t in deltas]
        lrbs = [deltas[t][profile_name]['delta_low_risk_breach_rate_bp'] for t in deltas]
        mean_auc = round(sum(auc_bps) / len(auc_bps))
        mean_lift = round(sum(lifts) / len(lifts), 2)
        mean_lrb = round(sum(lrbs) / len(lrbs))
        print(f'{profile_name:>30s} | {mean_auc:+10d} {mean_lift:+8.2f} {mean_lrb:+8d}')

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
        print(f'{profile_name:>30s}: {fails}/{total} year-slices AUC<0.55')

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
