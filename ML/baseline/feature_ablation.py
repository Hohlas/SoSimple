#!/usr/bin/env python3
"""
Feature Ablation Study: проверка вклада engineered признаков
(build_grouped_features) сверх плоских фрактальных признаков.

Запуск:
  .venv/bin/python -m ML.baseline.feature_ablation

Варианты:
  A:               flat features (parse_fractal_to_features)
  B:               flat + all engineered (excl. ret_dir_atr_lag1)
  C_*:             flat + одна engineered-группа за раз
  C_path_long_nf0: flat + path_long из fractals 1..99 (без fractal0)

Gate: PF >= 1.3, fill_rate >= 20%, trades/year >= 6, negative_years == 0.

Данные: DATA/spread_0.20/ (canonical spread=0.20)
Модель: RF n_estimators=100, max_depth=10, random_state=42
Цель:   buy_sl3_tp3
"""

import argparse
import os
import sys
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')
_BASELINE_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_BASELINE_DIR, '..', '..', 'processing'))
sys.path.insert(0, os.path.join(_BASELINE_DIR, '..'))
sys.path.insert(0, _BASELINE_DIR)

from label_signals import LIMIT_NO_FILL_SENTINEL
from benchmark_limit_order_entry import (
    parse_fractal_to_features,
    compute_pf,
    evaluate_threshold,
    threshold_sweep,
)
from feature_importance_diagnostics import (
    build_grouped_features,
    GROUP_FIELDS,
    ROW_FEATURE_GROUP,
    WINDOWS,
    AGGREGATIONS,
    FRACTAL_FIELD_INDEX,
    FRACTAL_SEP,
    _fractal_columns,
    _split_fractal_series,
    _aggregate_matrix,
)

SPREAD_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'DATA', 'spread_0.20')
TARGET = 'buy_sl3_tp3'
PNL_COL = f'{TARGET}_pnl_r'
FILL_COL = 'buy_fill_lag'
PURGE_HOURS = 30
GATE_PF_MIN = 1.3

UNSAFE_ENGINEERED = {'row_ret_dir_atr_lag1'}


def _field_matrix_from_level(frame, field, start_level, n_levels):
    """Извлечь поле field из fractals start_level..start_level+n_levels-1."""
    idx = FRACTAL_FIELD_INDEX[field]
    columns = []
    for fractal_col in _fractal_columns(start_level + n_levels)[start_level:start_level + n_levels]:
        if fractal_col not in frame.columns:
            break
        split = _split_fractal_series(frame[fractal_col])
        values = pd.to_numeric(split[idx], errors='coerce').fillna(0.0).to_numpy(dtype=np.float32)
        columns.append(values)
    return np.column_stack(columns) if columns else np.zeros((len(frame), 0), dtype=np.float32)


def _build_path_long_nof0(frame, seq_len=100):
    """Построить path_long engineered признаки из fractals 1..99 (без f0)."""
    features = {}
    feature_names = []
    path_fields = GROUP_FIELDS['path_long']
    n_levels = seq_len - 1  # 99 levels: fractals 1..99

    if n_levels <= 0:
        return pd.DataFrame(index=frame.index), []

    windows = tuple(w for w in WINDOWS if w <= n_levels)

    for field in path_fields:
        matrix = _field_matrix_from_level(frame, field, 1, n_levels)
        if matrix.shape[1] == 0:
            continue
        for window in windows:
            for name, values in _aggregate_matrix(matrix, window, field).items():
                features[name + '_nf0'] = values
                feature_names.append(name + '_nf0')

    return pd.DataFrame(features, index=frame.index).replace([np.inf, -np.inf], 0.0).fillna(0.0), feature_names


def _drop_unsafe_features(eng_df, eng_groups):
    dropped = []
    for col in list(eng_df.columns):
        if col in UNSAFE_ENGINEERED:
            eng_df = eng_df.drop(columns=[col])
            dropped.append(col)
    for group_name, cols in eng_groups.items():
        eng_groups[group_name] = [c for c in cols if c not in UNSAFE_ENGINEERED]
    if dropped:
        print(f"  Dropped unsafe features: {dropped}")
    return eng_df, eng_groups


def _yearly_slices(scores, threshold, pnl_values, fill_mask, time_col):
    """Yearly PF slices, win_rate и single-day profit concentration по выбранным сигналам."""
    times = pd.to_datetime(time_col)
    selected = scores >= threshold
    selected_fill = selected & fill_mask

    years = times.dt.year
    yearly = {}
    for y in sorted(years.unique()):
        mask_y = years == y
        pnl_y = pnl_values[mask_y & selected_fill]
        if len(pnl_y) > 0:
            yearly[y] = {
                'pf': compute_pf(pnl_y),
                'n_trades': pnl_y.shape[0],
                'total_r': float(pnl_y.sum()),
            }
        else:
            yearly[y] = {'pf': 0, 'n_trades': 0, 'total_r': 0.0}

    # Win rate: доля прибыльных сделок среди заполненных
    if selected_fill.sum() > 0:
        filled_pnl = pnl_values[selected_fill]
        win_rate = float((filled_pnl > 0).sum()) / len(filled_pnl)

        # Single-day profit concentration
        filled_days = times[selected_fill].dt.date
        day_profits = pd.Series(filled_pnl, index=filled_days).groupby(level=0).sum()
        total_profit = day_profits[day_profits > 0].sum()
        if total_profit > 0:
            top_day_pct = day_profits.max() / total_profit
        else:
            top_day_pct = 0.0
    else:
        win_rate = 0.0
        top_day_pct = 0.0

    # Yearly PF stability (std по годам с ненулевыми сделками)
    yearly_pfs = [d['pf'] for d in yearly.values() if d['n_trades'] > 0 and d['pf'] != float('inf')]
    yearly_pf_std = float(np.std(yearly_pfs)) if len(yearly_pfs) > 1 else 0.0

    return yearly, top_day_pct, win_rate, yearly_pf_std


def evaluate_variant(name, X_train, X_val, y_train, pnl_val, fill_mask, time_val):
    from sklearn.ensemble import RandomForestRegressor

    model = RandomForestRegressor(
        n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)
    scores = model.predict(X_val)

    results = threshold_sweep(scores, pnl_val, fill_mask, time_val)

    valid = [r for r in results
             if r['pf'] >= GATE_PF_MIN
             and r['fill_rate'] >= 0.20
             and r['trades_per_year'] >= 6
             and r['negative_years'] == 0]
    if valid:
        best = max(valid, key=lambda r: r['pf'])
    else:
        best_pf = max(results, key=lambda r: r['pf'])
        best = best_pf
        best['gate_pass'] = False

    gate_pass = bool(valid)
    best['gate_pass'] = gate_pass

    # Yearly PF slices и top-day diagnostics для best threshold
    best_threshold = best.get('threshold', 0)
    yearly, top_day_pct, win_rate, yearly_pf_std = _yearly_slices(
        scores, best_threshold, pnl_val, fill_mask, time_val,
    )

    return {
        'variant': name,
        'n_features': X_train.shape[1],
        'pf': best['pf'],
        'fill_rate': best['fill_rate'],
        'trades_per_year': best['trades_per_year'],
        'negative_years': best['negative_years'],
        'mean_r_signal': best.get('mean_r_signal', 0),
        'mean_r_trade': best.get('mean_r_trade', 0),
        'n_selected': best['n_selected'],
        'n_filled': best['n_filled'],
        'threshold': best.get('threshold', 0),
        'gate_pass': gate_pass,
        'yearly_pf': yearly,
        'top_day_pct': top_day_pct,
        'win_rate': win_rate,
        'yearly_pf_std': yearly_pf_std,
    }


def main():
    parser = argparse.ArgumentParser(description='Feature Ablation Study')
    parser.add_argument('--data-dir', default=SPREAD_DATA_DIR)
    parser.add_argument('--target', default=TARGET)
    parser.add_argument('--purge-hours', type=int, default=PURGE_HOURS)
    parser.add_argument('--rf-only', action='store_true', help='Only flat features (skip engineered)')
    args = parser.parse_args()

    train_path = os.path.join(args.data_dir, 'Nero_train_labeled.csv')
    val_path = os.path.join(args.data_dir, 'Nero_validation_labeled.csv')

    print(f"Loading data from {args.data_dir} ...")
    train_df = pd.read_csv(train_path, sep=';', low_memory=False)
    val_df = pd.read_csv(val_path, sep=';', low_memory=False)

    target = args.target
    fill_col = FILL_COL
    pnl_col = PNL_COL

    train_fill = pd.to_numeric(train_df[fill_col], errors='coerce').fillna(-1).astype(int) >= 0
    train_rows = train_df[train_fill].copy()
    val_fill_mask = (pd.to_numeric(val_df[fill_col], errors='coerce').fillna(-1).astype(int) >= 0).values

    print(f"Train (fill-only): {len(train_rows)}  Val (all): {len(val_df)}")
    print(f"Val filled: {val_fill_mask.sum()} / {len(val_fill_mask)}")
    print(f"Gate: PF>={GATE_PF_MIN}, fill>=20%, t/yr>=6, neg_y==0")

    if 'time' in train_rows.columns:
        train_times = pd.to_datetime(train_rows['time'])
        val_min_time = pd.to_datetime(val_df['time']).min()
        purge_mask = train_times + pd.Timedelta(hours=args.purge_hours) < val_min_time
        train_rows = train_rows[purge_mask].copy()
        print(f"Train after purge: {len(train_rows)}")

    y_train = pd.to_numeric(train_rows[target], errors='coerce').fillna(0.0).values.astype(np.float64)
    pnl_val = pd.to_numeric(val_df[pnl_col], errors='coerce').fillna(0.0).values.astype(np.float64)
    time_val = pd.to_datetime(val_df['time'])

    # ── Flat features ──────────────────────────────────────────────────────
    print("\n=== Parsing flat features ===")
    X_flat_train, fnames = parse_fractal_to_features(train_rows)
    X_flat_val, _ = parse_fractal_to_features(val_df)
    print(f"  Flat features: {X_flat_train.shape[1]}")

    results = []

    # ── Variant A: flat only ───────────────────────────────────────────────
    print("\n=== Variant A: flat only ===")
    r = evaluate_variant(
        'A: flat', X_flat_train, X_flat_val,
        y_train, pnl_val, val_fill_mask, time_val,
    )
    results.append(r)
    _print_variant(r)

    if args.rf_only:
        _print_table(results)
        return

    # ── Engineered features ────────────────────────────────────────────────
    print("\n=== Building engineered features ===")
    eng_train_df, eng_groups = build_grouped_features(train_rows)
    eng_val_df, _ = build_grouped_features(val_df)
    eng_train_df, eng_groups = _drop_unsafe_features(eng_train_df, eng_groups)
    eng_val_df, _ = _drop_unsafe_features(eng_val_df, eng_groups)
    print(f"  Engineered features: {len(eng_train_df.columns)}")
    print(f"  Groups: {', '.join(sorted(eng_groups.keys()))}")

    # ── Variant B: flat + all engineered ───────────────────────────────────
    print("\n=== Variant B: flat + engineered ===")
    X_full_train = np.hstack([X_flat_train, eng_train_df.to_numpy(dtype=np.float64)])
    X_full_val = np.hstack([X_flat_val, eng_val_df.to_numpy(dtype=np.float64)])
    r = evaluate_variant(
        'B: flat+eng', X_full_train, X_full_val,
        y_train, pnl_val, val_fill_mask, time_val,
    )
    results.append(r)
    _print_variant(r)

    # ── Variant C: flat + one group at a time ──────────────────────────────
    for group_name in sorted(eng_groups.keys()):
        if group_name == ROW_FEATURE_GROUP:
            continue

        group_cols = [c for c in eng_groups[group_name] if c in eng_train_df.columns]
        if not group_cols:
            continue

        print(f"\n=== Variant C_{group_name}: flat + {group_name} ===")
        eng_c_train = eng_train_df[group_cols].to_numpy(dtype=np.float64)
        eng_c_val = eng_val_df[group_cols].to_numpy(dtype=np.float64)
        Xg_train = np.hstack([X_flat_train, eng_c_train])
        Xg_val = np.hstack([X_flat_val, eng_c_val])

        r = evaluate_variant(
            f'C_{group_name}', Xg_train, Xg_val,
            y_train, pnl_val, val_fill_mask, time_val,
        )
        results.append(r)
        _print_variant(r, extra=f"(flat+{len(group_cols)})")

    # ── row_context ────────────────────────────────────────────────────────
    row_cols = [c for c in eng_groups.get(ROW_FEATURE_GROUP, []) if c in eng_train_df.columns]
    if row_cols:
        print(f"\n=== Variant C_row_context: flat + row_context ===")
        eng_r_train = eng_train_df[row_cols].to_numpy(dtype=np.float64)
        eng_r_val = eng_val_df[row_cols].to_numpy(dtype=np.float64)
        Xr_train = np.hstack([X_flat_train, eng_r_train])
        Xr_val = np.hstack([X_flat_val, eng_r_val])

        r = evaluate_variant(
            'C_row_context', Xr_train, Xr_val,
            y_train, pnl_val, val_fill_mask, time_val,
        )
        results.append(r)
        _print_variant(r, extra=f"(flat+{len(row_cols)})")

    # ── path_long without fractal0 ─────────────────────────────────────────
    print("\n=== Variant C_path_long_nf0: flat + path_long (fractals 1..99) ===")
    pl_nf0_train, _ = _build_path_long_nof0(train_rows)
    pl_nf0_val, _ = _build_path_long_nof0(val_df)
    if len(pl_nf0_train.columns) > 0:
        Xpl_train = np.hstack([X_flat_train, pl_nf0_train.to_numpy(dtype=np.float64)])
        Xpl_val = np.hstack([X_flat_val, pl_nf0_val.to_numpy(dtype=np.float64)])
        r = evaluate_variant(
            'C_path_long_nf0', Xpl_train, Xpl_val,
            y_train, pnl_val, val_fill_mask, time_val,
        )
        results.append(r)
        _print_variant(r, extra=f"(flat+{len(pl_nf0_train.columns)})")
    else:
        print("  SKIP: no features produced")

    _print_table(results)


def _print_variant(r, extra=None):
    nfeat = f"n_features={r['n_features']}"
    if extra:
        nfeat += f" {extra}"
    print(f"  {nfeat}  PF={r['pf']:.3f}  "
          f"fill_rate={r['fill_rate']:.1%}  t/yr={r['trades_per_year']:.1f}  "
          f"win%={r['win_rate']:.1%}  neg_y={r['negative_years']}  "
          f"gate={r['gate_pass']}")
    if r['yearly_pf']:
        yr_str = "  ".join(
            f"{y}: PF={d['pf']:.2f} n={d['n_trades']}"
            for y, d in sorted(r['yearly_pf'].items())
        )
        print(f"  yearly PF: {yr_str}")
        print(f"  top_day: {r['top_day_pct']:.1%}  PF_std: {r['yearly_pf_std']:.3f}")


def _print_table(results):
    print("\n" + "=" * 115)
    print("ABLATION RESULTS SUMMARY")
    print("=" * 115)
    header = (
        f"{'Variant':<26} {'Feat':>5} {'PF':>7} {'Fill%':>7} "
        f"{'T/yr':>7} {'Win%':>6} {'NegY':>5} {'R/trade':>8} "
        f"{'TopDay':>7} {'PFstd':>6} {'Gate':>5}"
    )
    print(header)
    print("-" * 115)

    a_pf = None
    for r in results:
        if r['variant'].startswith('A:'):
            a_pf = r['pf']
            break

    for r in results:
        pf_delta = ''
        if a_pf is not None and r['variant'] != 'A: flat':
            delta = r['pf'] - a_pf
            pf_delta = f'({delta:+.3f})'
        print(
            f"{r['variant']:<26} {r['n_features']:>5} {r['pf']:>7.3f} "
            f"{r['fill_rate']:>7.1%} {r['trades_per_year']:>7.1f} "
            f"{r['win_rate']:>6.1%} {r['negative_years']:>5} "
            f"{r['mean_r_trade']:>8.3f} "
            f"{r['top_day_pct']:>7.1%} {r['yearly_pf_std']:>6.3f} "
            f"{'PASS' if r['gate_pass'] else 'FAIL':>5} {pf_delta}"
        )

    print("=" * 115)
    if a_pf is not None:
        b_variant = [r for r in results if r['variant'] == 'B: flat+eng']
        b_pf = b_variant[0]['pf'] if b_variant else None

        group_results = [r for r in results
                         if r['variant'].startswith('C_')
                         and r['pf'] != float('inf')
                         and r['trades_per_year'] >= 6]
        best_group = max(group_results, key=lambda r: r['pf']) if group_results else None

        print("\nCONCLUSION:")
        if b_pf is not None and b_pf > a_pf + 0.05:
            print(f"  B (flat+eng) PF={b_pf:.3f} > A PF={a_pf:.3f} + 0.05")
            print("  Engineered features AS A WHOLE add significant signal.")
        else:
            print(f"  B (flat+eng) PF={b_pf:.3f} <= A PF={a_pf:.3f} + 0.05")
            print("  All engineered features together add NOISE, not signal.")

        if best_group:
            print(f"\n  HOWEVER, individual groups SHOW SIGNAL:")
            for r in sorted(group_results, key=lambda x: x['pf'], reverse=True)[:6]:
                delta = r['pf'] - a_pf
                print(f"    {r['variant']:<28} PF={r['pf']:.3f} (Δ{delta:+.3f})  "
                      f"{'PASS' if r['gate_pass'] else 'FAIL'}")

        if best_group and best_group['pf'] > a_pf + 0.05 and best_group['gate_pass']:
            print(f"\n  RECOMMENDATION: retain only {best_group['variant']} group(s) in feature set.")
            print(f"  Remove other groups to avoid noise.")
        else:
            print(f"\n  No single engineered group passes gate with significant PF delta vs flat.")


if __name__ == '__main__':
    main()
