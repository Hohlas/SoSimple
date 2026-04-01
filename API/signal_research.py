# =============================================================================
# Файл: API/signal_research.py
# Назначение: Статистическое исследование качества ML-сигналов по реальным OHLC
# Язык: Python 3.11+
# Создан: 2026-04-01
# Зависимости:
#   Входные данные:
#     - MT/MQL4/Files/ml_signals.csv
#     - DATA/XAUUSD_H1_OHLC.csv
#   Выходные данные:
#     - stdout (таблицы)
# Использование:
#   python -m API.signal_research
#   python -m API.signal_research --test-only
# =============================================================================

"""
Исследование: как ведёт себя цена после каждого ML-сигнала.

Для каждого сигнала BUY/SELL измеряем реальное движение цены:
- MFE (Maximum Favorable Excursion): максимум в направлении сигнала
- MAE (Maximum Adverse Excursion): максимум против сигнала
- Net: Close[t+N] - Close[t] (знаковое, в направлении сигнала)

Группировки:
1. По горизонту (3, 6, 12, 24, 48 баров)
2. По силе сигнала (ratio = up/dn для основного горизонта)
3. Влияние фильтров (up_3 > dn_3 и up_6 > dn_6)
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SIGNALS_FILE = PROJECT_ROOT / 'MT' / 'MQL4' / 'Files' / 'ml_signals.csv'
OHLC_FILE = PROJECT_ROOT / 'DATA' / 'XAUUSD_H1_OHLC.csv'

HORIZONS = [3, 6, 12, 24, 48]
PRED_COLS = ['up_3', 'dn_3', 'up_6', 'dn_6', 'up_12', 'dn_12',
             'up_24', 'dn_24', 'up_48', 'dn_48']


def load_data(test_only: bool = False):
    """Загрузка и слияние сигналов с OHLC."""
    sig = pd.read_csv(SIGNALS_FILE, sep=';', parse_dates=['time'])
    ohlc = pd.read_csv(OHLC_FILE, sep=';', parse_dates=['time'])

    ohlc.sort_values('time', inplace=True)
    ohlc.reset_index(drop=True, inplace=True)

    # Merge: оставляем только строки где есть и сигнал и OHLC
    df = sig.merge(ohlc[['time', 'open', 'high', 'low', 'close']], on='time', how='inner')
    df.sort_values('time', inplace=True)
    df.reset_index(drop=True, inplace=True)

    if test_only:
        # Test период: последние ~16% данных (как в ML split)
        cutoff = df['time'].quantile(0.84)
        df = df[df['time'] >= cutoff].reset_index(drop=True)

    print(f"  Загружено: {len(sig)} сигналов, {len(ohlc)} OHLC баров")
    print(f"  После merge: {len(df)} строк")
    print(f"  Период: {df['time'].iloc[0]} — {df['time'].iloc[-1]}")
    print(f"  BUY={len(df[df.signal==1])}, SELL={len(df[df.signal==-1])}, FLAT={len(df[df.signal==0])}")

    return df, ohlc


def compute_excursions(df: pd.DataFrame, ohlc: pd.DataFrame):
    """
    Для каждого сигнала вычисляет MFE/MAE/Net по всем горизонтам.

    MFE (Maximum Favorable Excursion):
      BUY:  max(High[t+1..t+N]) - Close[t]  (сколько цена прошла вверх)
      SELL: Close[t] - min(Low[t+1..t+N])    (сколько цена прошла вниз)

    MAE (Maximum Adverse Excursion):
      BUY:  Close[t] - min(Low[t+1..t+N])    (сколько цена просела)
      SELL: max(High[t+1..t+N]) - Close[t]   (сколько цена отскочила)

    Net: направленное изменение Close за N баров.
    """
    # Строим индекс OHLC для быстрого доступа по позиции
    ohlc_sorted = ohlc.sort_values('time').reset_index(drop=True)
    time_to_idx = {t: i for i, t in enumerate(ohlc_sorted['time'])}

    highs = ohlc_sorted['high'].values
    lows = ohlc_sorted['low'].values
    closes = ohlc_sorted['close'].values
    n_ohlc = len(ohlc_sorted)

    # Только сигнальные строки (BUY/SELL)
    sig_mask = df['signal'] != 0
    sig_df = df[sig_mask].copy()

    results = []

    for row_idx, row in sig_df.iterrows():
        t = row['time']
        if t not in time_to_idx:
            continue
        ohlc_idx = time_to_idx[t]
        entry_close = closes[ohlc_idx]
        sig = row['signal']  # 1=BUY, -1=SELL

        rec = {
            'time': t,
            'signal': sig,
            'entry_close': entry_close,
        }

        # Предсказания модели
        for col in PRED_COLS:
            rec[col] = row[col]

        # ratio основного горизонта (12)
        rec['ratio_12'] = row['up_12'] / (row['dn_12'] + 1e-6) if sig == 1 else row['dn_12'] / (row['up_12'] + 1e-6)

        # MFE/MAE/Net по каждому горизонту
        for h in HORIZONS:
            end_idx = ohlc_idx + h
            if end_idx >= n_ohlc:
                rec[f'mfe_{h}'] = np.nan
                rec[f'mae_{h}'] = np.nan
                rec[f'net_{h}'] = np.nan
                continue

            # Срез баров от t+1 до t+h включительно
            h_highs = highs[ohlc_idx + 1: end_idx + 1]
            h_lows = lows[ohlc_idx + 1: end_idx + 1]
            exit_close = closes[end_idx]

            max_high = h_highs.max()
            min_low = h_lows.min()

            if sig == 1:  # BUY
                rec[f'mfe_{h}'] = max_high - entry_close
                rec[f'mae_{h}'] = entry_close - min_low
                rec[f'net_{h}'] = exit_close - entry_close
            else:  # SELL
                rec[f'mfe_{h}'] = entry_close - min_low
                rec[f'mae_{h}'] = max_high - entry_close
                rec[f'net_{h}'] = entry_close - exit_close

        results.append(rec)

    return pd.DataFrame(results)


def print_separator(title: str):
    print(f"\n{'═' * 70}")
    print(f"  {title}")
    print(f"{'═' * 70}")


def report_by_horizon(exc: pd.DataFrame):
    """Таблица 1: MFE/MAE/Net по горизонтам (все сигналы)."""
    print_separator("1. MFE / MAE / Net по горизонтам (все сигналы, в пунктах)")

    rows = []
    for h in HORIZONS:
        mfe = exc[f'mfe_{h}'].dropna()
        mae = exc[f'mae_{h}'].dropna()
        net = exc[f'net_{h}'].dropna()
        rows.append({
            'horizon': f'{h}H',
            'N': len(mfe),
            'MFE_mean': f'{mfe.mean():.1f}',
            'MFE_med': f'{mfe.median():.1f}',
            'MAE_mean': f'{mae.mean():.1f}',
            'MAE_med': f'{mae.median():.1f}',
            'MFE/MAE': f'{mfe.mean() / (mae.mean() + 1e-6):.2f}',
            'Net_mean': f'{net.mean():.1f}',
            'WinRate': f'{(net > 0).mean() * 100:.1f}%',
            'PF': f'{net[net > 0].sum() / (-net[net < 0].sum() + 1e-6):.2f}',
        })

    print(pd.DataFrame(rows).to_string(index=False))


def report_by_ratio(exc: pd.DataFrame, horizon: int = 12):
    """Таблица 2: результаты по силе ratio (основной горизонт)."""
    print_separator(f"2. Результаты по силе ratio (горизонт {horizon}H)")

    bins = [0, 2, 3, 4, 5, 100]
    labels = ['<2', '2-3', '3-4', '4-5', '5+']
    exc['ratio_bin'] = pd.cut(exc['ratio_12'], bins=bins, labels=labels, right=False)

    rows = []
    for label in labels:
        sub = exc[exc['ratio_bin'] == label]
        if len(sub) == 0:
            continue
        mfe = sub[f'mfe_{horizon}'].dropna()
        mae = sub[f'mae_{horizon}'].dropna()
        net = sub[f'net_{horizon}'].dropna()

        neg_sum = -net[net < 0].sum()
        pf = net[net > 0].sum() / (neg_sum + 1e-6) if neg_sum > 0 else 999

        rows.append({
            'ratio': label,
            'N': len(sub),
            'MFE': f'{mfe.mean():.1f}',
            'MAE': f'{mae.mean():.1f}',
            'MFE/MAE': f'{mfe.mean() / (mae.mean() + 1e-6):.2f}',
            'Net': f'{net.mean():.1f}',
            'WinRate': f'{(net > 0).mean() * 100:.1f}%',
            'PF': f'{pf:.2f}',
            'TotalNet': f'{net.sum():.0f}',
        })

    print(pd.DataFrame(rows).to_string(index=False))


def report_filter_impact(exc: pd.DataFrame, horizon: int = 12):
    """Таблица 3: влияние фильтров up_3/dn_3 и up_6/dn_6 при разных порогах."""
    print_separator(f"3. Влияние фильтров (горизонт {horizon}H)")
    print("  ratio_3 = up_3/(dn_3+eps) для BUY, dn_3/(up_3+eps) для SELL")
    print("  ratio_6 аналогично для 6-барного горизонта\n")

    # Вычисляем ratio для коротких горизонтов
    exc = exc.copy()
    exc['ratio_3'] = np.where(exc['signal'] == 1,
                              exc['up_3'] / (exc['dn_3'] + 1e-6),
                              exc['dn_3'] / (exc['up_3'] + 1e-6))
    exc['ratio_6'] = np.where(exc['signal'] == 1,
                              exc['up_6'] / (exc['dn_6'] + 1e-6),
                              exc['dn_6'] / (exc['up_6'] + 1e-6))

    thresholds = [0, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]

    # 3a: Filter3 sweep
    print("  --- Filter3 (up_3/dn_3) ---")
    rows = []
    for thr in thresholds:
        sub = exc[exc['ratio_3'] >= thr] if thr > 0 else exc
        if len(sub) < 10:
            continue
        net = sub[f'net_{horizon}'].dropna()
        mfe = sub[f'mfe_{horizon}'].dropna()
        mae = sub[f'mae_{horizon}'].dropna()
        neg_sum = -net[net < 0].sum()
        pf = net[net > 0].sum() / (neg_sum + 1e-6) if neg_sum > 0 else 999

        rows.append({
            'thr': f'{thr:.1f}' if thr > 0 else 'off',
            'N': len(sub),
            '%': f'{100 * len(sub) / len(exc):.0f}%',
            'MFE': f'{mfe.mean():.1f}',
            'MAE': f'{mae.mean():.1f}',
            'Net': f'{net.mean():.1f}',
            'WinRate': f'{(net > 0).mean() * 100:.1f}%',
            'PF': f'{pf:.2f}',
            'TotalNet': f'{net.sum():.0f}',
        })
    print(pd.DataFrame(rows).to_string(index=False))

    # 3b: Filter6 sweep
    print("\n  --- Filter6 (up_6/dn_6) ---")
    rows = []
    for thr in thresholds:
        sub = exc[exc['ratio_6'] >= thr] if thr > 0 else exc
        if len(sub) < 10:
            continue
        net = sub[f'net_{horizon}'].dropna()
        mfe = sub[f'mfe_{horizon}'].dropna()
        mae = sub[f'mae_{horizon}'].dropna()
        neg_sum = -net[net < 0].sum()
        pf = net[net > 0].sum() / (neg_sum + 1e-6) if neg_sum > 0 else 999

        rows.append({
            'thr': f'{thr:.1f}' if thr > 0 else 'off',
            'N': len(sub),
            '%': f'{100 * len(sub) / len(exc):.0f}%',
            'MFE': f'{mfe.mean():.1f}',
            'MAE': f'{mae.mean():.1f}',
            'Net': f'{net.mean():.1f}',
            'WinRate': f'{(net > 0).mean() * 100:.1f}%',
            'PF': f'{pf:.2f}',
            'TotalNet': f'{net.sum():.0f}',
        })
    print(pd.DataFrame(rows).to_string(index=False))

    # 3c: Лучшие комбинации Filter3 + Filter6
    print("\n  --- Комбинации Filter3 + Filter6 ---")
    combo_thresholds = [1.0, 1.5, 2.0, 3.0]
    rows = []
    for t3 in combo_thresholds:
        for t6 in combo_thresholds:
            sub = exc[(exc['ratio_3'] >= t3) & (exc['ratio_6'] >= t6)]
            if len(sub) < 10:
                continue
            net = sub[f'net_{horizon}'].dropna()
            neg_sum = -net[net < 0].sum()
            pf = net[net > 0].sum() / (neg_sum + 1e-6) if neg_sum > 0 else 999

            rows.append({
                'F3': f'{t3:.1f}',
                'F6': f'{t6:.1f}',
                'N': len(sub),
                'Net': f'{net.mean():.1f}',
                'WinRate': f'{(net > 0).mean() * 100:.1f}%',
                'PF': f'{pf:.2f}',
                'TotalNet': f'{net.sum():.0f}',
            })
    print(pd.DataFrame(rows).to_string(index=False))


def report_prediction_vs_reality(exc: pd.DataFrame):
    """Таблица 4: корреляция предсказаний модели с реальным движением."""
    print_separator("4. Предсказание vs Реальность (корреляция)")

    rows = []
    for h in HORIZONS:
        # Для BUY: pred_up_H vs MFE_H, pred_dn_H vs MAE_H
        buy = exc[exc['signal'] == 1].dropna(subset=[f'mfe_{h}', f'mae_{h}'])
        sell = exc[exc['signal'] == -1].dropna(subset=[f'mfe_{h}', f'mae_{h}'])

        up_col = f'up_{h}'
        dn_col = f'dn_{h}'

        if len(buy) > 10:
            corr_mfe_buy = buy[up_col].corr(buy[f'mfe_{h}'])
            corr_mae_buy = buy[dn_col].corr(buy[f'mae_{h}'])
        else:
            corr_mfe_buy = corr_mae_buy = np.nan

        if len(sell) > 10:
            corr_mfe_sell = sell[dn_col].corr(sell[f'mfe_{h}'])
            corr_mae_sell = sell[up_col].corr(sell[f'mae_{h}'])
        else:
            corr_mfe_sell = corr_mae_sell = np.nan

        rows.append({
            'horizon': f'{h}H',
            'N_buy': len(buy),
            'N_sell': len(sell),
            'BUY pred_up~MFE': f'{corr_mfe_buy:.3f}' if not np.isnan(corr_mfe_buy) else 'n/a',
            'BUY pred_dn~MAE': f'{corr_mae_buy:.3f}' if not np.isnan(corr_mae_buy) else 'n/a',
            'SELL pred_dn~MFE': f'{corr_mfe_sell:.3f}' if not np.isnan(corr_mfe_sell) else 'n/a',
            'SELL pred_up~MAE': f'{corr_mae_sell:.3f}' if not np.isnan(corr_mae_sell) else 'n/a',
        })

    print(pd.DataFrame(rows).to_string(index=False))


def report_sl_tp_grid(exc: pd.DataFrame, horizon: int = 12):
    """Таблица 5: симуляция SL/TP комбинаций."""
    print_separator(f"5. Симуляция SL/TP (горизонт {horizon}H)")
    print("  Результат сделки: TP hit → +TP, SL hit → -SL, ни один → Net")

    sl_levels = [5, 10, 15, 20, 30]    # в пунктах (для Gold ~ $5, $10...)
    tp_levels = [5, 10, 15, 20, 30, 50]

    rows = []
    for sl in sl_levels:
        for tp in tp_levels:
            # Для каждой сделки: если MAE >= SL → лось, иначе если MFE >= TP → профит, иначе Net
            mfe = exc[f'mfe_{horizon}'].values
            mae = exc[f'mae_{horizon}'].values
            net = exc[f'net_{horizon}'].values

            valid = ~(np.isnan(mfe) | np.isnan(mae) | np.isnan(net))
            mfe_v, mae_v, net_v = mfe[valid], mae[valid], net[valid]

            # Упрощённая модель: проверяем достижение уровня
            # (не учитывает порядок — что было раньше, SL или TP)
            sl_hit = mae_v >= sl
            tp_hit = mfe_v >= tp

            # Если оба — считаем 50/50 (приближение)
            both = sl_hit & tp_hit
            pnl = np.where(tp_hit & ~both, tp,
                    np.where(sl_hit & ~both, -sl,
                      np.where(both, (tp - sl) / 2, net_v)))

            n_trades = len(pnl)
            wins = (pnl > 0).sum()
            total_pnl = pnl.sum()
            gross_profit = pnl[pnl > 0].sum()
            gross_loss = -pnl[pnl < 0].sum()
            pf = gross_profit / (gross_loss + 1e-6)

            rows.append({
                'SL': sl, 'TP': tp, 'R:R': f'{tp/sl:.1f}',
                'N': n_trades,
                'WinRate': f'{100 * wins / n_trades:.1f}%',
                'PF': f'{pf:.2f}',
                'Total': f'{total_pnl:.0f}',
                'Avg': f'{total_pnl / n_trades:.1f}',
            })

    print(pd.DataFrame(rows).to_string(index=False))


def main():
    parser = argparse.ArgumentParser(description='Исследование качества ML-сигналов')
    parser.add_argument('--test-only', action='store_true',
                        help='Только тестовый период (OOS)')
    args = parser.parse_args()

    print(f"\n{'═' * 70}")
    print(f"  ИССЛЕДОВАНИЕ КАЧЕСТВА ML-СИГНАЛОВ")
    if args.test_only:
        print(f"  (только тестовый период — Out-of-Sample)")
    print(f"{'═' * 70}")

    df, ohlc = load_data(test_only=args.test_only)

    print("\n  Вычисление MFE/MAE/Net...")
    exc = compute_excursions(df, ohlc)
    print(f"  Готово: {len(exc)} сигналов с excursion данными")

    report_by_horizon(exc)
    report_by_ratio(exc)
    report_filter_impact(exc)
    report_prediction_vs_reality(exc)
    report_sl_tp_grid(exc)


if __name__ == '__main__':
    main()
