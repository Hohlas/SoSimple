# =============================================================================
# Файл: ML/baseline/oracle_fractal_stop_fav.py
# Назначение: Oracle-диагностика — проверка потолка PF при идеальном знании breach/fav_val.
# Язык: Python 3.10+
# Обновлён: 2026-06-10
# Использование:
#   python -m ML.baseline.oracle_fractal_stop_fav
# =============================================================================
"""Oracle diagnostic: подстановка истинных breach/fav_val вместо RF-предсказаний.

Три режима:
  - perfect_breach: истинный breach-флаг, fav по RF (не треб. RF breach)
  - perfect_fav: истинный fav_val, breach по RF (не треб. RF fav)
  - perfect_both: истинный breach + истинный fav_val (не треб. RF вообще)

Фиксированные пороги: oracle-сигнал чистый, grid search не нужен.
  p=0.5, min_fav=0.0, min_rr=1.0, tp_frac=0.7
"""
import json
import math
import os
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'processing'))
from label_signals import load_ohlc_index
from ML.baseline.benchmark_fractal_stop_fav import (
    extract_flat_base_features, load_split, lookup_entry_prices,
    simulate_trades, compute_trade_metrics,
    BREACH_TARGETS, FAV_TARGETS, CAP,
)

CANONICAL_SPREAD = 0.20
STRESS_SPREAD = 0.40
TRAIN = 'DATA/Nero_XAUUSD_train_labeled.csv'
VAL = 'DATA/Nero_XAUUSD_validation_labeled.csv'
OHLC = 'DATA/XAUUSD_H1_OHLC.csv'
PARAMS = {'p': 0.5, 'min_fav': 0.0, 'min_rr': 1.0, 'tp_frac': 0.7}


def json_safe(obj):
    """Рекурсивно заменить inf/nan на null для строгого JSON."""
    if isinstance(obj, dict):
        return {key: json_safe(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [json_safe(value) for value in obj]
    if isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return None
    return obj


def eval_oracle(h, off, side, breach_proba_val, fav_pred_val, val_df, entry_prices_val,
                ohlc_val, times_val, time_idx_val, label):
    """Оценить один oracle-вариант на 3 спредах."""
    metrics = {}
    for spread_label, spread_val in [
        (f'canonical_{CANONICAL_SPREAD}', CANONICAL_SPREAD),
        ('diagnostic_0.00', 0.0),
        (f'stress_{STRESS_SPREAD}', STRESS_SPREAD),
    ]:
        trades = simulate_trades(
            val_df, entry_prices_val, breach_proba_val, fav_pred_val,
            ohlc_val, times_val, time_idx_val,
            side=side, h=h, stop_offset=off,
            p=PARAMS['p'], min_fav_val=PARAMS['min_fav'],
            min_rr=PARAMS['min_rr'], tp_fraction=PARAMS['tp_frac'], cap=CAP,
            spread=spread_val,
        )
        metrics[spread_label] = compute_trade_metrics(trades)
    return metrics


def main():
    train_df = load_split(TRAIN, 12)
    val_df = load_split(VAL, 12)
    ohlc_val, times_val, time_idx_val = load_ohlc_index(OHLC)
    entry_prices_val = lookup_entry_prices(val_df, OHLC)

    # Pre-train RF breach and fav ONCE (used only where needed)
    X_train, _ = extract_flat_base_features(train_df)
    X_val, _ = extract_flat_base_features(val_df)

    print('H|off|side  | phantom       | Trades | PF(can) | PF(0.0) | PF(0.4) | T/yr  | NegYr')
    print('-' * 85)

    all_results = {}

    for h in (6, 12):
        for off in (0.2, 0.5):
            # Pre-train RF models for this (h, off)
            rf_breach_buy = rf_breach_sell = rf_fav_buy = rf_fav_sell = None

            for side in ('buy', 'sell'):
                breach_col = BREACH_TARGETS[h][off][side]
                fav_col = FAV_TARGETS[h][side]

                y_breach_train = train_df[breach_col].values
                y_fav_train = train_df[fav_col].values
                y_breach_val = val_df[breach_col].values
                y_fav_val = val_df[fav_col].values

                breach_train_mask = ~np.isnan(y_breach_train)
                fav_train_mask = ~np.isnan(y_fav_train)
                val_mask = ~np.isnan(y_breach_val) & ~np.isnan(y_fav_val)

                # Train RF breach if needed
                if rf_breach_buy is None and side == 'buy':
                    rf = RandomForestClassifier(n_estimators=200, max_depth=12, min_samples_leaf=50,
                                               random_state=42, n_jobs=-1)
                    rf.fit(X_train[breach_train_mask], y_breach_train[breach_train_mask])
                    rf_breach_buy = rf

                if rf_breach_sell is None and side == 'sell':
                    rf = RandomForestClassifier(n_estimators=200, max_depth=12, min_samples_leaf=50,
                                               random_state=42, n_jobs=-1)
                    rf.fit(X_train[breach_train_mask], y_breach_train[breach_train_mask])
                    rf_breach_sell = rf

                if rf_fav_buy is None and side == 'buy':
                    rf = RandomForestRegressor(n_estimators=200, max_depth=12, min_samples_leaf=50,
                                              random_state=42, n_jobs=-1)
                    rf.fit(X_train[fav_train_mask], y_fav_train[fav_train_mask])
                    rf_fav_buy = rf

                if rf_fav_sell is None and side == 'sell':
                    rf = RandomForestRegressor(n_estimators=200, max_depth=12, min_samples_leaf=50,
                                              random_state=42, n_jobs=-1)
                    rf.fit(X_train[fav_train_mask], y_fav_train[fav_train_mask])
                    rf_fav_sell = rf

                # RF predictions
                rf_breach = rf_breach_buy if side == 'buy' else rf_breach_sell
                rf_fav_model = rf_fav_buy if side == 'buy' else rf_fav_sell

                breach_rf = np.full(len(val_df), np.nan)
                fav_rf = np.full(len(val_df), np.nan)
                breach_rf[val_mask] = rf_breach.predict_proba(X_val[val_mask])[:, 1]
                fav_rf[val_mask] = rf_fav_model.predict(X_val[val_mask])

                # 1) perfect_breach: истинный breach + RF fav
                b_oracle = y_breach_val.copy()  # breach=0 -> prob=0.0 -> ENTER; breach=1 -> prob=1.0 -> SKIP
                key = f'{side}_H{h}_off{int(off*10):02d}|perfect_breach'
                sp = eval_oracle(h, off, side, b_oracle, fav_rf, val_df, entry_prices_val,
                                 ohlc_val, times_val, time_idx_val, key)
                cm = sp[f'canonical_{CANONICAL_SPREAD}']
                print(f'{h:1d}|{off:3.1f} | {side:4s} | perfect_breach | {cm["n_trades"]:6d} | '
                      f'{cm["pf"]:8.3f} | {sp["diagnostic_0.00"]["pf"]:7.3f} | '
                      f'{sp[f"stress_{STRESS_SPREAD}"]["pf"]:7.3f} | '
                      f'{cm["trades_per_year"]:5.1f} | {cm["negative_years"]:5d}')
                all_results[key] = sp

                # 2) perfect_fav: RF breach + истинный fav
                f_oracle = y_fav_val.copy()
                key = f'{side}_H{h}_off{int(off*10):02d}|perfect_fav'
                sp = eval_oracle(h, off, side, breach_rf, f_oracle, val_df, entry_prices_val,
                                 ohlc_val, times_val, time_idx_val, key)
                cm = sp[f'canonical_{CANONICAL_SPREAD}']
                print(f'{h:1d}|{off:3.1f} | {side:4s} | perfect_fav    | {cm["n_trades"]:6d} | '
                      f'{cm["pf"]:8.3f} | {sp["diagnostic_0.00"]["pf"]:7.3f} | '
                      f'{sp[f"stress_{STRESS_SPREAD}"]["pf"]:7.3f} | '
                      f'{cm["trades_per_year"]:5.1f} | {cm["negative_years"]:5d}')
                all_results[key] = sp

                # 3) perfect_both: истинный breach + истинный fav
                key = f'{side}_H{h}_off{int(off*10):02d}|perfect_both'
                sp = eval_oracle(h, off, side, b_oracle, f_oracle, val_df, entry_prices_val,
                                 ohlc_val, times_val, time_idx_val, key)
                cm = sp[f'canonical_{CANONICAL_SPREAD}']
                print(f'{h:1d}|{off:3.1f} | {side:4s} | perfect_both   | {cm["n_trades"]:6d} | '
                      f'{cm["pf"]:8.3f} | {sp["diagnostic_0.00"]["pf"]:7.3f} | '
                      f'{sp[f"stress_{STRESS_SPREAD}"]["pf"]:7.3f} | '
                      f'{cm["trades_per_year"]:5.1f} | {cm["negative_years"]:5d}')
                all_results[key] = sp

    os.makedirs('ML/reports', exist_ok=True)
    with open('ML/reports/oracle_fractal_stop_fav.json', 'w') as f:
        json.dump(json_safe(all_results), f, indent=2, default=str, allow_nan=False)
    print(f'\nSaved: ML/reports/oracle_fractal_stop_fav.json')


if __name__ == '__main__':
    main()
