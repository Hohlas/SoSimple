# =============================================================================
# Файл: API/signal_research.py
# Назначение: Variant 2 / Variant 3 prep / Variant 3 execution research
#              качества ML-сигналов по реальным OHLC
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

Variant 2 отчёт строит:
1. Signal Passport по горизонтам (3, 6, 12, 24, 48 баров)
2. Ratio buckets для базового горизонта 12H
3. Pullback Profile в первые 1/3/6 баров
4. First-Hit Barrier Matrix по OHLC для SL/TP сетки
5. Amplitude Filters по предсказанной favorable/adverse амплитуде
6. Regime Split по направлению, ratio и ATR-квартилям
7. Practical Conclusions для следующего этапа построения EA

Variant 3 prep добавляет cohort-oriented shortlist и entry-opportunity sections.
Variant 3 execution research добавляет прямое сравнение entry scenarios:
- market
- pullback
- delayed
- cancel-window

Этот файл поддерживает Variant 2, Variant 3 prep и full Variant 3 execution research.
Если в OHLC CSV уже есть `atr14`, используется каноническое значение из MT4;
пропуски в нём добираются Python ATR(14) как fallback.
Если колонки `atr14` нет, ATR(14) целиком досчитывается в Python.
`pic_price` берётся из реальной фрактальной `price` feature в raw Nero rows:
внутри каждой строки выбирается фрактал с максимальным embedded-time
(зеркально sort-логике `label_main.py`), затем применяется та же dedupe-политика
по `time`, что и в `generate_signals.py`.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SIGNALS_FILE = PROJECT_ROOT / 'MT' / 'MQL4' / 'Files' / 'ml_signals.csv'
OHLC_FILE = PROJECT_ROOT / 'DATA' / 'XAUUSD_H1_OHLC.csv'
RAW_FEATURES_FILE = PROJECT_ROOT / 'MT' / 'MQL4' / 'Files' / 'Nero.csv'

BASE_HORIZON = 12
PULLBACK_WINDOWS = [1, 3, 6]
BARRIER_HORIZONS = [6, 12, 24]
SL_LEVELS = [5, 10, 15, 20, 30]
TP_LEVELS = [5, 10, 15, 20, 30, 50]
ATR_PERIOD = 14
VARIANT3_PRIMARY_COHORTS = ['ratio 4-5 × ATR Q4', 'ratio 4-5', 'BUY', 'ATR Q4']
VARIANT3_NEGATIVE_CONTROLS = ['ratio 3-4', 'non-Q4']


def compute_true_range(ohlc: pd.DataFrame) -> pd.Series:
    prev_close = ohlc['close'].shift(1)
    return pd.concat([
        ohlc['high'] - ohlc['low'],
        (ohlc['high'] - prev_close).abs(),
        (ohlc['low'] - prev_close).abs(),
    ], axis=1).max(axis=1)


def compute_atr14(ohlc: pd.DataFrame) -> pd.Series:
    tr = compute_true_range(ohlc)
    return tr.rolling(ATR_PERIOD, min_periods=ATR_PERIOD).mean()


HORIZONS = [3, 6, BASE_HORIZON, 24, 48]
PRED_COLS = ['up_3', 'dn_3', 'up_6', 'dn_6', 'up_12', 'dn_12',
             'up_24', 'dn_24', 'up_48', 'dn_48']
AMPLITUDE_BUCKET_LABELS = ['low', 'mid', 'high']


def parse_fractal_price(fractal_value) -> float:
    parsed = parse_fractal_record(fractal_value)
    return parsed['price'] if parsed is not None else np.nan


def parse_fractal_record(fractal_value):
    if pd.isna(fractal_value) or fractal_value == '':
        return None
    parts = str(fractal_value).split(':')
    if len(parts) < 3:
        return None
    try:
        return {
            'fractal_time': int(parts[0]),
            'price': float(parts[1]),
            'direction': int(parts[2]),
        }
    except ValueError:
        return None


def latest_fractal_price(fractal_values) -> float:
    return latest_fractal_record(fractal_values)['price']


def latest_fractal_record(fractal_values):
    latest = {'fractal_time': np.nan, 'price': np.nan, 'direction': np.nan}
    latest_time = None

    for fractal_value in fractal_values:
        parsed = parse_fractal_record(fractal_value)
        if parsed is None:
            continue
        if latest_time is None or parsed['fractal_time'] > latest_time:
            latest_time = parsed['fractal_time']
            latest = parsed

    return latest


def load_pic_price_data() -> pd.DataFrame:
    if not RAW_FEATURES_FILE.exists():
        return pd.DataFrame(columns=['time', 'pic_fractal_time', 'pic_price', 'pic_direction'])

    frame = pd.read_csv(
        RAW_FEATURES_FILE,
        sep=';',
        usecols=lambda col: col == 'time' or col.startswith('fractal'),
        parse_dates=['time'],
        low_memory=False,
    )
    fractal_columns = [col for col in frame.columns if col.startswith('fractal')]
    latest_records = [
        latest_fractal_record(fractal_values)
        for fractal_values in frame[fractal_columns].itertuples(index=False, name=None)
    ]
    frame['pic_fractal_time'] = pd.to_datetime(
        [record['fractal_time'] for record in latest_records],
        unit='s',
        errors='coerce',
    )
    frame['pic_price'] = [record['price'] for record in latest_records]
    frame['pic_direction'] = [record['direction'] for record in latest_records]

    prices = frame[['time', 'pic_fractal_time', 'pic_price', 'pic_direction']].copy()
    prices.sort_values('time', inplace=True)
    prices = prices.drop_duplicates(subset=['time'], keep='last').reset_index(drop=True)
    return prices


def load_data(test_only: bool = False):
    """Загрузка и слияние сигналов с OHLC."""
    sig = pd.read_csv(SIGNALS_FILE, sep=';', parse_dates=['time'])
    ohlc = pd.read_csv(OHLC_FILE, sep=';', parse_dates=['time'])
    pic_prices = load_pic_price_data()

    ohlc.sort_values('time', inplace=True)
    ohlc.reset_index(drop=True, inplace=True)
    atr14_fallback = compute_atr14(ohlc)
    if 'atr14' in ohlc.columns:
        ohlc['atr14'] = pd.to_numeric(ohlc['atr14'], errors='coerce').fillna(atr14_fallback)
    else:
        ohlc['atr14'] = atr14_fallback

    # Merge: оставляем только строки где есть и сигнал и OHLC
    df = sig.merge(ohlc[['time', 'open', 'high', 'low', 'close', 'atr14']], on='time', how='inner')
    if pic_prices.empty:
        df['pic_price'] = np.nan
        df['pic_fractal_time'] = pd.NaT
        df['pic_direction'] = np.nan
    else:
        df = df.merge(pic_prices, on='time', how='left')
    df.sort_values('time', inplace=True)
    df.reset_index(drop=True, inplace=True)

    if test_only:
        # Test период: последние ~16% данных (как в ML split)
        cutoff = df['time'].quantile(0.84)
        df = df[df['time'] >= cutoff].reset_index(drop=True)

    print(f"  Загружено: {len(sig)} сигналов, {len(ohlc)} OHLC баров")
    print(f"  После merge: {len(df)} строк")
    if df.empty:
        print("  Период: n/a (нет строк после merge или test-only slice)")
        print("  BUY=0, SELL=0, FLAT=0")
        return df, ohlc
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
    atr14 = ohlc_sorted['atr14'] if 'atr14' in ohlc_sorted.columns else pd.Series(np.nan, index=ohlc_sorted.index)

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
            'ohlc_idx': ohlc_idx,
            'entry_close': entry_close,
            'entry_atr14': row.get('atr14', atr14.iloc[ohlc_idx]),
            'pic_price': row.get('pic_price', np.nan),
        }

        # Предсказания модели
        for col in PRED_COLS:
            rec[col] = row[col]

        fav_prefix, adv_prefix = ('up', 'dn') if sig == 1 else ('dn', 'up')
        for h in (3, 6, 12):
            rec[f'pred_fav_{h}'] = row[f'{fav_prefix}_{h}']
            rec[f'pred_adv_{h}'] = row[f'{adv_prefix}_{h}']

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

        for w in PULLBACK_WINDOWS:
            end_idx = ohlc_idx + w
            if end_idx >= n_ohlc:
                rec[f'fav_{w}'] = np.nan
                rec[f'adv_{w}'] = np.nan
                rec[f'close_net_{w}'] = np.nan
                continue

            w_highs = highs[ohlc_idx + 1: end_idx + 1]
            w_lows = lows[ohlc_idx + 1: end_idx + 1]
            exit_close = closes[end_idx]
            max_high = w_highs.max()
            min_low = w_lows.min()

            if sig == 1:
                rec[f'fav_{w}'] = max_high - entry_close
                rec[f'adv_{w}'] = entry_close - min_low
                rec[f'close_net_{w}'] = exit_close - entry_close
            else:
                rec[f'fav_{w}'] = entry_close - min_low
                rec[f'adv_{w}'] = max_high - entry_close
                rec[f'close_net_{w}'] = entry_close - exit_close

        results.append(rec)

    exc = pd.DataFrame(results)

    expected_columns = [
        'time', 'signal', 'ohlc_idx', 'entry_close', 'entry_atr14',
        *PRED_COLS,
        'pred_fav_3', 'pred_adv_3', 'pred_fav_6', 'pred_adv_6', 'pred_fav_12', 'pred_adv_12',
        'ratio_12',
        *[f'mfe_{h}' for h in HORIZONS],
        *[f'mae_{h}' for h in HORIZONS],
        *[f'net_{h}' for h in HORIZONS],
        *[f'fav_{w}' for w in PULLBACK_WINDOWS],
        *[f'adv_{w}' for w in PULLBACK_WINDOWS],
        *[f'close_net_{w}' for w in PULLBACK_WINDOWS],
        'ratio_bin', 'atr_bucket',
    ]

    if exc.empty:
        return pd.DataFrame(columns=expected_columns)

    exc['ratio_bin'] = pd.cut(
        exc['ratio_12'],
        bins=[0, 2, 3, 4, 5, np.inf],
        labels=['<2', '2-3', '3-4', '4-5', '5+'],
        right=False,
    )

    atr_valid = exc['entry_atr14'].dropna()
    if len(atr_valid) >= 2 and atr_valid.nunique() > 1:
        try:
            atr_bins = pd.Series(pd.qcut(exc['entry_atr14'], q=4, duplicates='drop'), index=exc.index)
            n_bins = len(atr_bins.cat.categories)
            if n_bins > 0:
                atr_bins = atr_bins.cat.rename_categories([f'Q{i + 1}' for i in range(n_bins)])
                exc['atr_bucket'] = atr_bins.astype('object').fillna('ALL')
            else:
                exc['atr_bucket'] = 'ALL'
        except ValueError:
            exc['atr_bucket'] = 'ALL'
    else:
        exc['atr_bucket'] = 'ALL'

    return exc


def first_hit_barrier_result(opens, highs, lows, entry_price, signal, sl, tp):
    if signal == 1:
        sl_price = entry_price - sl
        tp_price = entry_price + tp
        for opn, high, low in zip(opens, highs, lows):
            sl_hit = low <= sl_price
            tp_hit = high >= tp_price
            if sl_hit and tp_hit:
                return 'SL_FIRST' if abs(opn - sl_price) <= abs(tp_price - opn) else 'TP_FIRST'
            if tp_hit:
                return 'TP_FIRST'
            if sl_hit:
                return 'SL_FIRST'
    else:
        sl_price = entry_price + sl
        tp_price = entry_price - tp
        for opn, high, low in zip(opens, highs, lows):
            sl_hit = high >= sl_price
            tp_hit = low <= tp_price
            if sl_hit and tp_hit:
                return 'SL_FIRST' if abs(opn - sl_price) <= abs(opn - tp_price) else 'TP_FIRST'
            if tp_hit:
                return 'TP_FIRST'
            if sl_hit:
                return 'SL_FIRST'
    return 'NEITHER'


def build_barrier_outcomes(exc, ohlc, horizons=BARRIER_HORIZONS, sl_levels=SL_LEVELS, tp_levels=TP_LEVELS):
    columns = [
        'time', 'signal', 'ratio_bin', 'atr_bucket',
        'pred_fav_3', 'pred_fav_6', 'pred_fav_12',
        'pred_adv_3', 'pred_adv_6', 'pred_adv_12',
        'horizon', 'SL', 'TP', 'outcome', 'pnl',
    ]
    ohlc_sorted = ohlc.sort_values('time').reset_index(drop=True)
    opens = ohlc_sorted['open'].to_numpy()
    highs = ohlc_sorted['high'].to_numpy()
    lows = ohlc_sorted['low'].to_numpy()
    records = []

    for _, row in exc.iterrows():
        idx = int(row['ohlc_idx'])
        entry_price = float(row['entry_close'])
        signal = int(row['signal'])
        for horizon in horizons:
            end_idx = idx + horizon
            if end_idx >= len(ohlc_sorted):
                continue
            bar_opens = opens[idx + 1:end_idx + 1]
            bar_highs = highs[idx + 1:end_idx + 1]
            bar_lows = lows[idx + 1:end_idx + 1]
            for sl in sl_levels:
                for tp in tp_levels:
                    outcome = first_hit_barrier_result(bar_opens, bar_highs, bar_lows, entry_price, signal, sl, tp)
                    pnl = tp if outcome == 'TP_FIRST' else -sl if outcome == 'SL_FIRST' else row[f'net_{horizon}']
                    records.append({
                        'time': row['time'],
                        'signal': signal,
                        'ratio_bin': row.get('ratio_bin'),
                        'atr_bucket': row.get('atr_bucket', 'ALL'),
                        'pred_fav_3': row.get('pred_fav_3'),
                        'pred_fav_6': row.get('pred_fav_6'),
                        'pred_fav_12': row.get('pred_fav_12'),
                        'pred_adv_3': row.get('pred_adv_3'),
                        'pred_adv_6': row.get('pred_adv_6'),
                        'pred_adv_12': row.get('pred_adv_12'),
                        'horizon': horizon,
                        'SL': sl,
                        'TP': tp,
                        'outcome': outcome,
                        'pnl': pnl,
                    })

    if not records:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(records, columns=columns)


def summarize_barrier_outcomes(outcomes: pd.DataFrame) -> pd.DataFrame:
    columns = [
        'horizon', 'SL', 'TP', 'N',
        'tp_first_pct', 'sl_first_pct', 'neither_pct',
        'PF_num', 'AvgPnL_num', 'TotalPnL_num',
    ]
    if outcomes.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for (horizon, sl, tp), sub in outcomes.groupby(['horizon', 'SL', 'TP'], sort=False):
        n = len(sub)
        tp_first = (sub['outcome'] == 'TP_FIRST').sum()
        sl_first = (sub['outcome'] == 'SL_FIRST').sum()
        neither = (sub['outcome'] == 'NEITHER').sum()
        gross_profit = sub.loc[sub['pnl'] > 0, 'pnl'].sum()
        gross_loss = -sub.loc[sub['pnl'] < 0, 'pnl'].sum()
        if gross_loss == 0:
            pf = np.inf if gross_profit > 0 else np.nan
        elif gross_profit == 0:
            pf = 0.0
        else:
            pf = gross_profit / gross_loss
        rows.append({
            'horizon': horizon,
            'SL': sl,
            'TP': tp,
            'N': n,
            'tp_first_pct': 100.0 * tp_first / n,
            'sl_first_pct': 100.0 * sl_first / n,
            'neither_pct': 100.0 * neither / n,
            'PF_num': pf,
            'AvgPnL_num': sub['pnl'].mean(),
            'TotalPnL_num': sub['pnl'].sum(),
        })
    return pd.DataFrame(rows, columns=columns)


def annotate_baseline_setup(
    exc: pd.DataFrame,
    barrier_outcomes: pd.DataFrame,
    horizon: int = BASE_HORIZON,
    sl: int = 5,
    tp: int = 50,
) -> pd.DataFrame:
    """Attach the fixed baseline barrier outcome to each signal row."""
    baseline = barrier_outcomes[
        (barrier_outcomes['horizon'] == horizon)
        & (barrier_outcomes['SL'] == sl)
        & (barrier_outcomes['TP'] == tp)
    ][['time', 'signal', 'outcome', 'pnl']].copy()

    baseline.rename(
        columns={
            'outcome': 'baseline_outcome',
            'pnl': 'baseline_pnl',
        },
        inplace=True,
    )
    baseline['baseline_setup'] = f'{horizon}H_SL{sl}_TP{tp}'

    annotated = exc.merge(baseline, on=['time', 'signal'], how='left')
    if 'baseline_setup' not in annotated.columns:
        annotated['baseline_setup'] = f'{horizon}H_SL{sl}_TP{tp}'
    else:
        annotated['baseline_setup'] = annotated['baseline_setup'].fillna(f'{horizon}H_SL{sl}_TP{tp}')
    return annotated


def summarize_signal_groups(exc: pd.DataFrame, group_cols) -> pd.DataFrame:
    group_cols = [group_cols] if isinstance(group_cols, str) else list(group_cols)
    columns = [
        *group_cols,
        'N',
        'PF_12',
        'AvgPnL_baseline',
        'TP_FIRST_pct',
        'SL_FIRST_pct',
        'NEITHER_pct',
    ]
    if exc.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for group_key, sub in exc.groupby(list(group_cols), sort=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        baseline = sub['baseline_outcome'].dropna()
        baseline_pnl = sub['baseline_pnl'].dropna()
        net_12 = sub['net_12'].dropna()

        tp_first = (baseline == 'TP_FIRST').sum()
        sl_first = (baseline == 'SL_FIRST').sum()
        neither = (baseline == 'NEITHER').sum()
        denom = len(baseline)
        rows.append({
            **dict(zip(group_cols, group_key)),
            'N': len(sub),
            'PF_12': _profit_factor(net_12),
            'AvgPnL_baseline': baseline_pnl.mean() if len(baseline_pnl) else np.nan,
            'TP_FIRST_pct': 100.0 * tp_first / denom if denom else np.nan,
            'SL_FIRST_pct': 100.0 * sl_first / denom if denom else np.nan,
            'NEITHER_pct': 100.0 * neither / denom if denom else np.nan,
        })
    return pd.DataFrame(rows, columns=columns)


def _amplitude_bucket_series(series: pd.Series) -> pd.Series:
    return _safe_quantile_bins(series, AMPLITUDE_BUCKET_LABELS)


def _non_null_rate(series: pd.Series, predicate) -> float:
    valid = pd.to_numeric(series, errors='coerce').dropna()
    if len(valid) == 0:
        return np.nan
    return 100.0 * predicate(valid).mean()


def _atr_multiple_rate(frame: pd.DataFrame, value_col: str, threshold_atr: float) -> float:
    value_series = pd.to_numeric(frame.get(value_col, pd.Series(index=frame.index, dtype=float)), errors='coerce')
    atr_series = pd.to_numeric(frame.get('entry_atr14', pd.Series(index=frame.index, dtype=float)), errors='coerce')
    valid = pd.DataFrame({'value': value_series, 'atr': atr_series}).replace([np.inf, -np.inf], np.nan)
    valid = valid.dropna()
    valid = valid[valid['atr'] > 0]
    if valid.empty:
        return np.nan
    return 100.0 * ((valid['value'] / valid['atr']) >= threshold_atr).mean()


def build_entry_opportunity_profile(frame: pd.DataFrame, group_col, group_values) -> pd.DataFrame:
    group_cols = [group_col] if isinstance(group_col, str) else list(group_col)
    if group_values is None:
        selected_values = []
    elif isinstance(group_values, (str, bytes)):
        selected_values = [group_values]
    else:
        selected_values = list(group_values)
    columns = [
        *group_cols,
        'N',
        'pullback>=1ATR_1H',
        'pullback>=2ATR_3H',
        'pullback>=3ATR_6H',
        'fav>=1ATR_1H',
        'fav>=2ATR_3H',
        'fav>=3ATR_6H',
        'close>0_1H',
        'close>0_3H',
        'close>0_6H',
    ]

    if frame.empty:
        return pd.DataFrame(columns=columns)

    if selected_values:
        if len(group_cols) == 1:
            working = frame[frame[group_cols[0]].isin(selected_values)].copy()
        else:
            lookup = {tuple(value) if isinstance(value, (list, tuple)) else value for value in selected_values}
            working = frame[frame[group_cols].apply(lambda row: tuple(row), axis=1).isin(lookup)].copy()
    else:
        working = frame.copy()

    if working.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for group_key, sub in working.groupby(group_cols, sort=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)

        rows.append({
            **dict(zip(group_cols, group_key)),
            'N': len(sub),
            'pullback>=1ATR_1H': _atr_multiple_rate(sub, 'adv_1', 1.0),
            'pullback>=2ATR_3H': _atr_multiple_rate(sub, 'adv_3', 2.0),
            'pullback>=3ATR_6H': _atr_multiple_rate(sub, 'adv_6', 3.0),
            'fav>=1ATR_1H': _atr_multiple_rate(sub, 'fav_1', 1.0),
            'fav>=2ATR_3H': _atr_multiple_rate(sub, 'fav_3', 2.0),
            'fav>=3ATR_6H': _atr_multiple_rate(sub, 'fav_6', 3.0),
            'close>0_1H': _non_null_rate(sub.get('close_net_1', pd.Series(dtype=float)), lambda s: s > 0),
            'close>0_3H': _non_null_rate(sub.get('close_net_3', pd.Series(dtype=float)), lambda s: s > 0),
            'close>0_6H': _non_null_rate(sub.get('close_net_6', pd.Series(dtype=float)), lambda s: s > 0),
        })

    return pd.DataFrame(rows, columns=columns)


def _cohort_map_extended_summary(exc: pd.DataFrame, group_cols) -> pd.DataFrame:
    group_cols = [group_cols] if isinstance(group_cols, str) else list(group_cols)
    columns = [
        *group_cols,
        'N',
        'Net_12_mean',
        'Net_12_median',
        'MFE_12_mean',
        'MAE_12_mean',
        'PF_12',
        'AvgPnL_baseline',
        'TP_FIRST_pct',
        'SL_FIRST_pct',
        'NEITHER_pct',
    ]
    if exc.empty:
        return pd.DataFrame(columns=columns)

    base = summarize_signal_groups(exc, group_cols)
    rows = []
    for group_key, sub in exc.groupby(group_cols, sort=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        net_12 = pd.to_numeric(sub['net_12'], errors='coerce').dropna()
        mfe_12 = pd.to_numeric(sub['mfe_12'], errors='coerce').dropna()
        mae_12 = pd.to_numeric(sub['mae_12'], errors='coerce').dropna()
        rows.append({
            **dict(zip(group_cols, group_key)),
            'Net_12_mean': net_12.mean() if len(net_12) else np.nan,
            'Net_12_median': net_12.median() if len(net_12) else np.nan,
            'MFE_12_mean': mfe_12.mean() if len(mfe_12) else np.nan,
            'MAE_12_mean': mae_12.mean() if len(mae_12) else np.nan,
        })

    metrics = pd.DataFrame(rows, columns=[*group_cols, 'Net_12_mean', 'Net_12_median', 'MFE_12_mean', 'MAE_12_mean'])
    summary = base.merge(metrics, on=group_cols, how='left')
    return summary[columns]


def _prepare_priority_cohort_frame(frame: pd.DataFrame) -> pd.DataFrame:
    analysis = frame.copy()
    analysis['direction'] = pd.Series(np.where(analysis['signal'] == 1, 'BUY', 'SELL'), index=analysis.index)

    if 'ratio_bin' not in analysis.columns and 'ratio_12' in analysis.columns:
        analysis['ratio_bin'] = pd.cut(
            analysis['ratio_12'],
            bins=[0, 2, 3, 4, 5, np.inf],
            labels=['<2', '2-3', '3-4', '4-5', '5+'],
            right=False,
        )
    if 'ratio_bin' not in analysis.columns:
        analysis['ratio_bin'] = 'ALL'
    analysis['ratio_bin'] = analysis['ratio_bin'].astype('object')

    if 'atr_bucket' not in analysis.columns:
        analysis['atr_bucket'] = 'ALL'
    analysis['atr_bucket'] = analysis['atr_bucket'].astype('object')
    analysis['atr_regime'] = np.where(analysis['atr_bucket'] == 'Q4', 'Q4', 'non-Q4')
    analysis['year'] = pd.to_datetime(analysis['time']).dt.year
    return analysis


def _build_priority_cohort_frame(frame: pd.DataFrame) -> pd.DataFrame:
    analysis = _prepare_priority_cohort_frame(frame)
    cohort_specs = [
        ('BUY', analysis['signal'] == 1),
        ('SELL', analysis['signal'] == -1),
        ('ratio 3-4', analysis['ratio_bin'] == '3-4'),
        ('ratio 4-5', analysis['ratio_bin'] == '4-5'),
        ('ratio 5+', analysis['ratio_bin'] == '5+'),
        ('ATR Q4', analysis['atr_bucket'] == 'Q4'),
        ('non-Q4', analysis['atr_bucket'] != 'Q4'),
        ('ratio 4-5 × ATR Q4', (analysis['ratio_bin'] == '4-5') & (analysis['atr_bucket'] == 'Q4')),
    ]

    frames = []
    for label, mask in cohort_specs:
        sub = analysis.loc[mask].copy()
        if sub.empty:
            continue
        sub['cohort'] = label
        frames.append(sub)

    if not frames:
        return pd.DataFrame(columns=[*analysis.columns, 'cohort'])
    return pd.concat(frames, axis=0, ignore_index=True)


def summarize_pic_price_validation(frame: pd.DataFrame, ohlc: pd.DataFrame, eps: float = 0.051) -> dict:
    summary = {
        'N_rows': 0,
        'N_joined': 0,
        'N_matched': 0,
        'match_pct': np.nan,
        'peak_match_pct': np.nan,
        'trough_match_pct': np.nan,
        'max_abs_error': np.nan,
        'median_abs_error': np.nan,
    }
    required = {'pic_fractal_time', 'pic_price', 'pic_direction'}
    if frame.empty or not required.issubset(frame.columns):
        return summary

    working = frame[['time', 'pic_fractal_time', 'pic_price', 'pic_direction']].copy()
    working = working.dropna(subset=['pic_fractal_time', 'pic_price', 'pic_direction'])
    working = working[working['pic_direction'].isin([-1, 1])]
    if working.empty:
        return summary

    reference = ohlc[['time', 'high', 'low']].copy()
    reference.rename(columns={'time': 'pic_fractal_time'}, inplace=True)
    merged = working.merge(reference, on='pic_fractal_time', how='left')
    joined = merged.dropna(subset=['high', 'low']).copy()

    summary['N_rows'] = len(working)
    summary['N_joined'] = len(joined)
    if joined.empty:
        return summary

    expected_price = np.where(joined['pic_direction'] == 1, joined['high'], joined['low'])
    abs_error = (joined['pic_price'] - expected_price).abs()
    matched = abs_error <= eps
    summary['N_matched'] = int(matched.sum())
    summary['match_pct'] = 100.0 * matched.mean()
    peaks = joined['pic_direction'] == 1
    troughs = joined['pic_direction'] == -1
    if peaks.any():
        summary['peak_match_pct'] = 100.0 * matched[peaks].mean()
    if troughs.any():
        summary['trough_match_pct'] = 100.0 * matched[troughs].mean()
    summary['max_abs_error'] = abs_error.max()
    summary['median_abs_error'] = abs_error.median()
    return summary


def default_variant3_scenario_specs():
    specs = [{'scenario': 'market'}]
    for delay_bars in [1, 3]:
        specs.append({'scenario': 'delayed', 'delay_bars': delay_bars})
    for offset_atr in [1.0, 2.0, 3.0]:
        specs.append({'scenario': 'pullback', 'anchor': 'entry_close', 'offset_atr': offset_atr})
    for offset_atr in [0.0, 1.0, -1.0]:
        specs.append({'scenario': 'pullback', 'anchor': 'pic_price', 'offset_atr': offset_atr})
    for expiry_bars in [1, 3, 6]:
        for offset_atr in [1.0, 2.0, 3.0]:
            specs.append({
                'scenario': 'cancel-window',
                'anchor': 'entry_close',
                'offset_atr': offset_atr,
                'expiry_bars': expiry_bars,
            })
        for offset_atr in [0.0, 1.0, -1.0]:
            specs.append({
                'scenario': 'cancel-window',
                'anchor': 'pic_price',
                'offset_atr': offset_atr,
                'expiry_bars': expiry_bars,
            })
    return specs


def _format_atr_label(value) -> str:
    value = float(value)
    if value.is_integer():
        return f'{int(value)}ATR'
    return f'{value:.1f}ATR'


def _variant3_params_label(spec: dict) -> str:
    scenario = spec['scenario']
    if scenario == 'market':
        return 'market'
    if scenario == 'delayed':
        return f"delay={int(spec['delay_bars'])}"

    anchor = spec['anchor']
    offset_atr = float(spec['offset_atr'])
    if anchor == 'entry_close':
        base = f"entry_close-{_format_atr_label(abs(offset_atr))}"
    elif offset_atr > 0:
        base = f"pic_price+{_format_atr_label(offset_atr)}"
    elif offset_atr < 0:
        base = f"pic_price-{_format_atr_label(abs(offset_atr))}"
    else:
        base = 'pic_price'

    if scenario == 'cancel-window':
        return f"{base}@{int(spec['expiry_bars'])}b"
    return base


def resolve_limit_fill(opens, highs, lows, signal, limit_price):
    for idx, (opn, high, low) in enumerate(zip(opens, highs, lows)):
        if signal == 1:
            if opn <= limit_price:
                return idx, float(opn)
            if low <= limit_price:
                return idx, float(limit_price)
        else:
            if opn >= limit_price:
                return idx, float(opn)
            if high >= limit_price:
                return idx, float(limit_price)
    return None, np.nan


def _variant3_limit_price(row: pd.Series, anchor: str, offset_atr: float):
    atr = row.get('entry_atr14', np.nan)
    if pd.isna(atr):
        return np.nan

    if anchor == 'entry_close':
        base_price = row.get('entry_close', np.nan)
        if pd.isna(base_price):
            return np.nan
        return base_price - atr * offset_atr if int(row['signal']) == 1 else base_price + atr * offset_atr

    if anchor == 'pic_price':
        base_price = row.get('pic_price', np.nan)
        if pd.isna(base_price):
            return np.nan
        return base_price + atr * offset_atr if int(row['signal']) == 1 else base_price - atr * offset_atr

    return np.nan


def _variant3_net_from_close(signal: int, entry_price: float, exit_close: float):
    return exit_close - entry_price if signal == 1 else entry_price - exit_close


def _evaluate_variant3_outcome(opens, highs, lows, closes, signal, fill_idx, deadline_idx, fill_price, sl, tp):
    future_opens = opens[fill_idx + 1:deadline_idx + 1]
    future_highs = highs[fill_idx + 1:deadline_idx + 1]
    future_lows = lows[fill_idx + 1:deadline_idx + 1]
    outcome = first_hit_barrier_result(future_opens, future_highs, future_lows, fill_price, signal, sl, tp)
    if outcome == 'TP_FIRST':
        return outcome, float(tp)
    if outcome == 'SL_FIRST':
        return outcome, -float(sl)
    return outcome, _variant3_net_from_close(signal, fill_price, float(closes[deadline_idx]))


def build_variant3_scenario_outcomes(
    exc: pd.DataFrame,
    ohlc: pd.DataFrame,
    horizon: int = BASE_HORIZON,
    sl: int = 5,
    tp: int = 50,
    scenario_specs=None,
) -> pd.DataFrame:
    columns = [
        'time', 'signal', 'ratio_bin', 'atr_bucket', 'pic_price',
        'scenario', 'params', 'anchor', 'offset_atr', 'delay_bars', 'expiry_bars',
        'fill_status', 'fill_idx', 'fill_price', 'outcome', 'pnl',
    ]
    if exc.empty:
        return pd.DataFrame(columns=columns)

    specs = default_variant3_scenario_specs() if scenario_specs is None else list(scenario_specs)
    ohlc_sorted = ohlc.sort_values('time').reset_index(drop=True)
    opens = ohlc_sorted['open'].to_numpy()
    highs = ohlc_sorted['high'].to_numpy()
    lows = ohlc_sorted['low'].to_numpy()
    closes = ohlc_sorted['close'].to_numpy()
    records = []

    for _, row in exc.iterrows():
        idx = int(row['ohlc_idx'])
        deadline_idx = idx + horizon
        if deadline_idx >= len(ohlc_sorted):
            continue

        for spec in specs:
            scenario = spec['scenario']
            anchor = spec.get('anchor')
            offset_atr = spec.get('offset_atr')
            delay_bars = spec.get('delay_bars')
            expiry_bars = spec.get('expiry_bars')

            fill_idx = None
            fill_price = np.nan
            fill_status = 'SKIP'

            if scenario == 'market':
                fill_idx = idx
                fill_price = float(row['entry_close'])
                fill_status = 'FILLED'
            elif scenario == 'delayed':
                fill_idx = idx + int(delay_bars)
                if fill_idx <= deadline_idx and fill_idx < len(ohlc_sorted):
                    fill_price = float(closes[fill_idx])
                    fill_status = 'FILLED'
            elif scenario in ('pullback', 'cancel-window'):
                limit_price = _variant3_limit_price(row, anchor, float(offset_atr))
                if not pd.isna(limit_price):
                    expiry_limit = deadline_idx if scenario == 'pullback' else min(deadline_idx, idx + int(expiry_bars))
                    if expiry_limit > idx:
                        relative_fill_idx, resolved_price = resolve_limit_fill(
                            opens=opens[idx + 1:expiry_limit + 1],
                            highs=highs[idx + 1:expiry_limit + 1],
                            lows=lows[idx + 1:expiry_limit + 1],
                            signal=int(row['signal']),
                            limit_price=float(limit_price),
                        )
                        if relative_fill_idx is not None:
                            fill_idx = idx + 1 + int(relative_fill_idx)
                            fill_price = resolved_price
                            fill_status = 'FILLED'

            if fill_status == 'FILLED':
                outcome, pnl = _evaluate_variant3_outcome(
                    opens=opens,
                    highs=highs,
                    lows=lows,
                    closes=closes,
                    signal=int(row['signal']),
                    fill_idx=fill_idx,
                    deadline_idx=deadline_idx,
                    fill_price=float(fill_price),
                    sl=sl,
                    tp=tp,
                )
            else:
                outcome, pnl = 'SKIP', np.nan

            records.append({
                'time': row['time'],
                'signal': int(row['signal']),
                'ratio_bin': row.get('ratio_bin'),
                'atr_bucket': row.get('atr_bucket', 'ALL'),
                'pic_price': row.get('pic_price', np.nan),
                'scenario': scenario,
                'params': _variant3_params_label(spec),
                'anchor': anchor,
                'offset_atr': offset_atr,
                'delay_bars': delay_bars,
                'expiry_bars': expiry_bars,
                'fill_status': fill_status,
                'fill_idx': fill_idx,
                'fill_price': fill_price,
                'outcome': outcome,
                'pnl': pnl,
            })

    return pd.DataFrame(records, columns=columns)


def summarize_variant3_scenarios(outcomes: pd.DataFrame, group_cols) -> pd.DataFrame:
    group_cols = [group_cols] if isinstance(group_cols, str) else list(group_cols)
    columns = [
        *group_cols,
        'N_signals',
        'N_filled',
        'fill_pct',
        'skip_pct',
        'PF',
        'AvgPnL',
        'TP_FIRST_pct',
        'SL_FIRST_pct',
        'NEITHER_pct',
    ]
    if outcomes.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for group_key, sub in outcomes.groupby(group_cols, sort=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        filled = sub[sub['fill_status'] == 'FILLED'].copy()
        n_signals = len(sub)
        n_filled = len(filled)
        outcomes_filled = filled['outcome']
        denom = len(outcomes_filled)
        rows.append({
            **dict(zip(group_cols, group_key)),
            'N_signals': n_signals,
            'N_filled': n_filled,
            'fill_pct': 100.0 * n_filled / n_signals if n_signals else np.nan,
            'skip_pct': 100.0 * (sub['fill_status'] == 'SKIP').sum() / n_signals if n_signals else np.nan,
            'PF': _profit_factor(filled['pnl'].dropna()) if n_filled else np.nan,
            'AvgPnL': filled['pnl'].mean() if n_filled else np.nan,
            'TP_FIRST_pct': 100.0 * (outcomes_filled == 'TP_FIRST').sum() / denom if denom else np.nan,
            'SL_FIRST_pct': 100.0 * (outcomes_filled == 'SL_FIRST').sum() / denom if denom else np.nan,
            'NEITHER_pct': 100.0 * (outcomes_filled == 'NEITHER').sum() / denom if denom else np.nan,
        })
    return pd.DataFrame(rows, columns=columns)


def build_variant3_summary(exc: pd.DataFrame, ohlc: pd.DataFrame) -> pd.DataFrame:
    scenario_outcomes = build_variant3_scenario_outcomes(exc, ohlc)
    if scenario_outcomes.empty:
        return pd.DataFrame(columns=[
            'cohort', 'scenario', 'params', 'N_signals', 'N_filled', 'fill_pct', 'skip_pct',
            'PF', 'AvgPnL', 'TP_FIRST_pct', 'SL_FIRST_pct', 'NEITHER_pct',
        ])

    cohort_frame = _build_priority_cohort_frame(scenario_outcomes)
    if cohort_frame.empty:
        return pd.DataFrame(columns=[
            'cohort', 'scenario', 'params', 'N_signals', 'N_filled', 'fill_pct', 'skip_pct',
            'PF', 'AvgPnL', 'TP_FIRST_pct', 'SL_FIRST_pct', 'NEITHER_pct',
        ])

    wanted = VARIANT3_PRIMARY_COHORTS + VARIANT3_NEGATIVE_CONTROLS
    cohort_frame = cohort_frame[cohort_frame['cohort'].isin(wanted)].copy()
    return summarize_variant3_scenarios(cohort_frame, ['cohort', 'scenario', 'params'])


def print_separator(title: str):
    print(f"\n{'═' * 70}")
    print(f"  {title}")
    print(f"{'═' * 70}")


def _format_num(value, digits: int = 1):
    if pd.isna(value):
        return 'n/a'
    return f'{value:.{digits}f}'


def _format_pct(value):
    if pd.isna(value):
        return 'n/a'
    return f'{value:.1f}%'


def _format_pf(value):
    if pd.isna(value):
        return 'n/a'
    if np.isinf(value):
        return 'inf'
    return f'{value:.2f}'


def _profit_factor(series: pd.Series):
    gross_profit = series[series > 0].sum()
    gross_loss = -series[series < 0].sum()
    if gross_loss == 0:
        return np.inf if gross_profit > 0 else np.nan
    if gross_profit == 0:
        return 0.0
    return gross_profit / gross_loss


def _safe_quantile_bins(series: pd.Series, labels):
    valid = series.dropna()
    if len(valid) < len(labels) or valid.nunique() < len(labels):
        return pd.Series(['mid'] * len(series), index=series.index, dtype='object')
    try:
        return pd.qcut(series, q=[0, 0.25, 0.75, 1.0], labels=labels, duplicates='drop').astype('object')
    except ValueError:
        return pd.Series(['mid'] * len(series), index=series.index, dtype='object')


def _select_base_barrier_setups(barrier_summary: pd.DataFrame, top_n: int):
    subset = barrier_summary[barrier_summary['horizon'] == BASE_HORIZON].copy()
    if subset.empty:
        return subset

    max_n = subset['N'].max()
    min_n = min(20, max_n) if not pd.isna(max_n) else 0
    viable = subset[subset['N'] >= min_n]
    sort_cols = ['PF_num', 'AvgPnL_num', 'N']
    sort_order = [False, False, False]
    ranked_viable = viable.sort_values(sort_cols, ascending=sort_order)
    if len(ranked_viable) >= top_n or viable.empty:
        ranked = ranked_viable if not viable.empty else subset.sort_values(['N', 'PF_num', 'AvgPnL_num'], ascending=[False, False, False])
        return ranked.head(top_n)

    remainder = subset.loc[~subset.index.isin(ranked_viable.index)].sort_values(['N', 'PF_num', 'AvgPnL_num'], ascending=[False, False, False])
    return pd.concat([ranked_viable, remainder], axis=0).head(top_n)


def report_signal_passport(exc: pd.DataFrame):
    print_separator("Signal Passport")

    rows = []
    for h in HORIZONS:
        mfe = exc[f'mfe_{h}'].dropna()
        mae = exc[f'mae_{h}'].dropna()
        net = exc[f'net_{h}'].dropna()
        pf = _profit_factor(net)
        rows.append({
            'horizon': f'{h}H',
            'N': len(mfe),
            'MFE_mean': _format_num(mfe.mean()),
            'MFE_med': _format_num(mfe.median()),
            'MFE_p75': _format_num(mfe.quantile(0.75)),
            'MFE_p90': _format_num(mfe.quantile(0.90)),
            'MAE_mean': _format_num(mae.mean()),
            'MAE_med': _format_num(mae.median()),
            'MAE_p75': _format_num(mae.quantile(0.75)),
            'MAE_p90': _format_num(mae.quantile(0.90)),
            'Net_mean': _format_num(net.mean()),
            'Net_med': _format_num(net.median()),
            'MFE/MAE': _format_num(mfe.mean() / (mae.mean() + 1e-6), 2),
            'WinRate': _format_pct((net > 0).mean() * 100),
            'PF': _format_pf(pf),
        })

    print(pd.DataFrame(rows).to_string(index=False))


def report_by_ratio(exc: pd.DataFrame, horizon: int = 12):
    """Таблица 2: результаты по силе ratio (основной горизонт)."""
    print_separator(f"2. Результаты по силе ratio (горизонт {horizon}H)")

    exc = exc.copy()
    bins = [0, 2, 3, 4, 5, np.inf]
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


def report_pullback_profile(exc: pd.DataFrame):
    print_separator("Pullback Profile")

    groups = [('ALL', exc), ('BUY', exc[exc['signal'] == 1]), ('SELL', exc[exc['signal'] == -1])]
    for ratio_bin in ['2-3', '3-4', '4-5', '5+']:
        groups.append((f'ratio {ratio_bin}', exc[exc['ratio_bin'].astype('object') == ratio_bin]))

    for label, sub in groups:
        print(f"\n  [{label}]")
        rows = []
        for w in PULLBACK_WINDOWS:
            window_cols = [f'fav_{w}', f'adv_{w}', f'close_net_{w}']
            window_sub = sub.dropna(subset=window_cols)
            fav = window_sub.get(f'fav_{w}', pd.Series(dtype=float))
            adv = window_sub.get(f'adv_{w}', pd.Series(dtype=float))
            close_net = window_sub.get(f'close_net_{w}', pd.Series(dtype=float))
            rows.append({
                'window': f'{w}H',
                'N': len(window_sub),
                'fav_mean': _format_num(fav.mean()),
                'fav_med': _format_num(fav.median()),
                'adv_mean': _format_num(adv.mean()),
                'adv_med': _format_num(adv.median()),
                'fav/adv': _format_num(fav.mean() / (adv.mean() + 1e-6), 2),
                '%adv>=5': _format_pct((adv >= 5).mean() * 100),
                '%adv>=10': _format_pct((adv >= 10).mean() * 100),
                '%adv>=15': _format_pct((adv >= 15).mean() * 100),
                '%fav>=5': _format_pct((fav >= 5).mean() * 100),
                '%fav>=10': _format_pct((fav >= 10).mean() * 100),
                '%fav>=15': _format_pct((fav >= 15).mean() * 100),
                '%close>0': _format_pct((close_net > 0).mean() * 100),
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


def report_first_hit_barriers(barrier_summary: pd.DataFrame):
    print_separator("First-Hit Barrier Matrix")
    if barrier_summary.empty:
        print("  No barrier summary available.")
        return

    table = barrier_summary.copy()
    table['R:R'] = table['TP'] / table['SL']
    table['%TP_FIRST'] = table['tp_first_pct'].map(_format_pct)
    table['%SL_FIRST'] = table['sl_first_pct'].map(_format_pct)
    table['%NEITHER'] = table['neither_pct'].map(_format_pct)
    table['PF'] = table['PF_num'].map(_format_pf)
    table['AvgPnL'] = table['AvgPnL_num'].map(_format_num)
    table['TotalPnL'] = table['TotalPnL_num'].map(_format_num)
    print(table[['horizon', 'SL', 'TP', 'R:R', 'N', '%TP_FIRST', '%SL_FIRST', '%NEITHER', 'PF', 'AvgPnL', 'TotalPnL']].to_string(index=False))


def report_amplitude_filters(exc: pd.DataFrame, barrier_outcomes: pd.DataFrame, barrier_summary: pd.DataFrame):
    print_separator("Amplitude Filters")

    top_barriers = _select_base_barrier_setups(barrier_summary, top_n=2)
    if top_barriers.empty:
        print("  No barrier setups available for amplitude filters.")
        return

    metrics = ['pred_fav_3', 'pred_fav_6', 'pred_fav_12', 'pred_adv_3', 'pred_adv_6']
    for metric in metrics:
        buckets = _safe_quantile_bins(exc[metric], ['low', 'mid', 'high'])
        metric_exc = exc.assign(bucket=buckets)
        print(f"\n  [{metric}]")

        rows = []
        for bucket in ['low', 'mid', 'high']:
            sub = metric_exc[metric_exc['bucket'] == bucket]
            effective_sub = sub.dropna(subset=['net_12'])
            row = {
                'bucket': bucket,
                'N': len(effective_sub),
                'Net_12': _format_num(effective_sub['net_12'].mean()),
                'MFE_12': _format_num(effective_sub['mfe_12'].mean()),
                'MAE_12': _format_num(effective_sub['mae_12'].mean()),
                'PF_12': _format_pf(_profit_factor(effective_sub['net_12'].dropna())),
            }
            for _, barrier in top_barriers.iterrows():
                sl = barrier['SL']
                tp = barrier['TP']
                label = f'{int(sl)}/{int(tp)}'
                outcome_sub = barrier_outcomes[
                    (barrier_outcomes['horizon'] == barrier['horizon']) &
                    (barrier_outcomes['SL'] == sl) &
                    (barrier_outcomes['TP'] == tp) &
                    (barrier_outcomes['time'].isin(effective_sub['time']))
                ]
                row[f'TP%_{label}'] = _format_pct((outcome_sub['outcome'] == 'TP_FIRST').mean() * 100)
                row[f'SL%_{label}'] = _format_pct((outcome_sub['outcome'] == 'SL_FIRST').mean() * 100)
            rows.append(row)
        print(pd.DataFrame(rows).to_string(index=False))


def report_cohort_map(exc: pd.DataFrame, barriers: pd.DataFrame, barrier_outcomes: pd.DataFrame):
    print_separator("Cohort Map")
    print("  Baseline setup: 12H / SL=5 / TP=50")

    annotated = annotate_baseline_setup(exc, barrier_outcomes)
    analysis = annotated.copy()
    analysis['direction'] = pd.Series(np.where(analysis['signal'] == 1, 'BUY', 'SELL'), index=analysis.index)
    if 'ratio_bin' not in analysis.columns and 'ratio_12' in analysis.columns:
        analysis['ratio_bin'] = pd.cut(
            analysis['ratio_12'],
            bins=[0, 2, 3, 4, 5, np.inf],
            labels=['<2', '2-3', '3-4', '4-5', '5+'],
            right=False,
        )
    if 'ratio_bin' not in analysis.columns:
        analysis['ratio_bin'] = 'ALL'
    analysis['ratio_bin'] = analysis['ratio_bin'].astype('object')
    if 'atr_bucket' not in analysis.columns:
        analysis['atr_bucket'] = 'ALL'
    pred_fav_3 = analysis['pred_fav_3'] if 'pred_fav_3' in analysis.columns else pd.Series(np.nan, index=analysis.index)
    pred_adv_3 = analysis['pred_adv_3'] if 'pred_adv_3' in analysis.columns else pd.Series(np.nan, index=analysis.index)
    analysis['pred_fav_3_bucket'] = _amplitude_bucket_series(pred_fav_3)
    analysis['pred_adv_3_bucket'] = _amplitude_bucket_series(pred_adv_3)

    specs = [
        ('BUY/SELL × ratio_12', ['direction', 'ratio_bin']),
        ('BUY/SELL × atr_bucket', ['direction', 'atr_bucket']),
        ('ratio_12 × atr_bucket', ['ratio_bin', 'atr_bucket']),
        ('ratio_12 × pred_fav_3 bucket', ['ratio_bin', 'pred_fav_3_bucket']),
        ('ratio_12 × pred_adv_3 bucket', ['ratio_bin', 'pred_adv_3_bucket']),
    ]

    sort_orders = {
        'direction': ['BUY', 'SELL'],
        'ratio_bin': ['<2', '2-3', '3-4', '4-5', '5+'],
        'atr_bucket': ['Q1', 'Q2', 'Q3', 'Q4', 'ALL'],
        'pred_fav_3_bucket': AMPLITUDE_BUCKET_LABELS,
        'pred_adv_3_bucket': AMPLITUDE_BUCKET_LABELS,
    }

    for title, group_cols in specs:
        subset = analysis.copy()
        for col in group_cols:
            if col in sort_orders:
                subset[col] = pd.Categorical(subset[col], categories=sort_orders[col], ordered=True)
        subset = subset.sort_values(group_cols, kind='stable')
        summary = _cohort_map_extended_summary(subset, group_cols)

        print(f"\n  [{title}]")
        if summary.empty:
            print("  No rows.")
            continue

        table = summary.copy()
        for col in ['Net_12_mean', 'Net_12_median', 'MFE_12_mean', 'MAE_12_mean', 'AvgPnL_baseline']:
            table[col] = table[col].map(_format_num)
        table['PF_12'] = table['PF_12'].map(_format_pf)
        table['TP_FIRST_pct'] = table['TP_FIRST_pct'].map(_format_pct)
        table['SL_FIRST_pct'] = table['SL_FIRST_pct'].map(_format_pct)
        table['NEITHER_pct'] = table['NEITHER_pct'].map(_format_pct)
        print(table.to_string(index=False))


def report_entry_opportunities(exc: pd.DataFrame):
    print_separator("Entry Opportunity Profile")

    if exc.empty:
        print("  No signal rows available.")
        return

    cohort_frame = _build_priority_cohort_frame(exc)
    if cohort_frame.empty:
        print("  No priority cohorts available.")
        return

    wanted = ['BUY', 'SELL', 'ratio 3-4', 'ratio 4-5', 'ratio 5+', 'ATR Q4', 'non-Q4', 'ratio 4-5 × ATR Q4']
    wanted = [label for label in wanted if label in cohort_frame['cohort'].unique()]
    table = build_entry_opportunity_profile(cohort_frame, 'cohort', wanted)
    print(table.to_string(index=False))


def report_pic_price_validation(df: pd.DataFrame, ohlc: pd.DataFrame):
    print_separator("Pic Price Validation")

    summary = summarize_pic_price_validation(df, ohlc)
    if summary['N_rows'] == 0:
        print("  No pic_price rows available.")
        return

    print(
        f"  Rows: {summary['N_rows']}, joined on fractal time: {summary['N_joined']}, "
        f"matched High/Low within 0.05 tolerance: {summary['N_matched']} ({_format_pct(summary['match_pct'])})."
    )
    print(
        f"  Peaks vs High: {_format_pct(summary['peak_match_pct'])}, "
        f"troughs vs Low: {_format_pct(summary['trough_match_pct'])}."
    )
    print(
        f"  Abs error: median={_format_num(summary['median_abs_error'])}, "
        f"max={_format_num(summary['max_abs_error'])}."
    )


def report_stability_splits(exc: pd.DataFrame, barriers: pd.DataFrame, barrier_outcomes: pd.DataFrame):
    print_separator("Stability Split")

    annotated = annotate_baseline_setup(exc, barrier_outcomes)
    if annotated.empty:
        print("  No signal rows available.")
        return

    cohort_frame = _build_priority_cohort_frame(annotated)
    if cohort_frame.empty:
        print("  No priority cohorts available.")
        return

    table = _cohort_map_extended_summary(cohort_frame.dropna(subset=['net_12']), ['year', 'cohort'])
    if table.empty:
        print("  No stability rows available.")
        return

    table = table[table['N'] >= 10].copy()
    if table.empty:
        print("  No stability rows with N>=10.")
        return

    table = table.sort_values(['cohort', 'year'], kind='stable').reset_index(drop=True)
    table['PF_12'] = table['PF_12'].map(_format_pf)
    table['Net_12_mean'] = table['Net_12_mean'].map(_format_num)
    table['TP_FIRST_pct'] = table['TP_FIRST_pct'].map(_format_pct)
    table['SL_FIRST_pct'] = table['SL_FIRST_pct'].map(_format_pct)
    print("  Baseline setup: 12H / SL=5 / TP=50")
    print("  Only rows with N>=10 are shown.")
    print(table[['year', 'cohort', 'N', 'PF_12', 'Net_12_mean', 'TP_FIRST_pct', 'SL_FIRST_pct']].to_string(index=False))


def report_priority_cohorts(exc: pd.DataFrame, barriers: pd.DataFrame, barrier_outcomes: pd.DataFrame):
    print_separator("Priority Cohorts")

    annotated = annotate_baseline_setup(exc, barrier_outcomes)
    if annotated.empty:
        print("  No signal rows available.")
        return

    cohort_frame = _build_priority_cohort_frame(annotated)
    if cohort_frame.empty:
        print("  No priority cohorts available.")
        return

    summary = _cohort_map_extended_summary(cohort_frame, ['cohort'])
    if summary.empty:
        print("  No cohort summaries available.")
        return

    summary = summary.copy()
    summary['PF_sort'] = pd.to_numeric(summary['PF_12'], errors='coerce')
    summary['AvgPnL_sort'] = pd.to_numeric(summary['AvgPnL_baseline'], errors='coerce')
    summary['Net_sort'] = pd.to_numeric(summary['Net_12_mean'], errors='coerce')
    weak_mask = (
        summary['PF_sort'].isna()
        | (summary['PF_sort'] <= 1.05)
        | (summary['AvgPnL_sort'] <= 0.1)
        | (summary['Net_sort'] <= 0)
    )

    best_pool = summary[~weak_mask].copy()
    if best_pool.empty:
        best_pool = summary.copy()

    best = best_pool.sort_values(
        ['PF_sort', 'AvgPnL_sort', 'N'],
        ascending=[False, False, False],
        na_position='last',
    ).head(5).drop(columns=['PF_sort', 'AvgPnL_sort', 'Net_sort'])
    best_cohorts = set(best['cohort'].tolist())

    anti_seed = summary[summary['cohort'] == 'ratio 3-4']
    weak = summary[weak_mask].sort_values(
        ['PF_sort', 'AvgPnL_sort', 'N'],
        ascending=[True, True, False],
        na_position='first',
    )

    anti = pd.concat([anti_seed, weak], axis=0, ignore_index=True)
    if not anti.empty:
        anti = anti.drop_duplicates(subset=['cohort'], keep='first')
        anti = anti[~anti['cohort'].isin(best_cohorts)].copy()
        anti = anti.assign(_priority=np.where(anti['cohort'] == 'ratio 3-4', 0, 1))
        anti = anti.sort_values(
            ['_priority', 'PF_sort', 'AvgPnL_sort', 'N'],
            ascending=[True, True, True, False],
            na_position='first',
        ).head(4)
        anti = anti.drop(columns=['PF_sort', 'AvgPnL_sort', 'Net_sort'], errors='ignore')
        anti = anti.drop(columns=['_priority'], errors='ignore')

    for title, table in [('Best candidates', best), ('Anti-pattern cohorts', anti)]:
        print(f"\n  [{title}]")
        if table.empty:
            print("  No rows.")
            continue
        display = table.copy()
        display['PF_12'] = display['PF_12'].map(_format_pf)
        display['AvgPnL_baseline'] = display['AvgPnL_baseline'].map(_format_num)
        display['Net_12_mean'] = display['Net_12_mean'].map(_format_num)
        display['Net_12_median'] = display['Net_12_median'].map(_format_num)
        display['MFE_12_mean'] = display['MFE_12_mean'].map(_format_num)
        display['MAE_12_mean'] = display['MAE_12_mean'].map(_format_num)
        display['TP_FIRST_pct'] = display['TP_FIRST_pct'].map(_format_pct)
        display['SL_FIRST_pct'] = display['SL_FIRST_pct'].map(_format_pct)
        display['NEITHER_pct'] = display['NEITHER_pct'].map(_format_pct)
        print(display[['cohort', 'N', 'PF_12', 'AvgPnL_baseline', 'Net_12_mean', 'TP_FIRST_pct', 'SL_FIRST_pct', 'NEITHER_pct']].to_string(index=False))


def report_variant3_scenario_matrix(summary: pd.DataFrame):
    print_separator("Variant 3 Scenario Matrix")
    if summary.empty:
        print("  No Variant 3 scenario rows available.")
        return

    table = summary.copy()
    table['fill_pct'] = table['fill_pct'].map(_format_pct)
    table['skip_pct'] = table['skip_pct'].map(_format_pct)
    table['PF'] = table['PF'].map(_format_pf)
    table['AvgPnL'] = table['AvgPnL'].map(_format_num)
    table['TP_FIRST_pct'] = table['TP_FIRST_pct'].map(_format_pct)
    table['SL_FIRST_pct'] = table['SL_FIRST_pct'].map(_format_pct)
    table['NEITHER_pct'] = table['NEITHER_pct'].map(_format_pct)
    table = table.sort_values(['cohort', 'scenario', 'params'], kind='stable').reset_index(drop=True)
    print(table.to_string(index=False))


def report_variant3_shortlist_verdict(summary: pd.DataFrame):
    print_separator("Variant 3 Shortlist Verdict")
    shortlist = summary[summary['cohort'].isin(VARIANT3_PRIMARY_COHORTS)].copy()
    if shortlist.empty:
        print("  No primary cohort rows available.")
        return

    shortlist = shortlist[shortlist['N_filled'] > 0].copy()
    if shortlist.empty:
        print("  No filled primary-cohort rows available.")
        return

    shortlist['PF_sort'] = pd.to_numeric(shortlist['PF'], errors='coerce')
    shortlist['AvgPnL_sort'] = pd.to_numeric(shortlist['AvgPnL'], errors='coerce')
    shortlist['fill_sort'] = pd.to_numeric(shortlist['fill_pct'], errors='coerce')
    verdict = shortlist.sort_values(
        ['cohort', 'PF_sort', 'AvgPnL_sort', 'fill_sort'],
        ascending=[True, False, False, False],
        na_position='last',
    ).groupby('cohort', sort=False).head(1)

    display = verdict.drop(columns=['PF_sort', 'AvgPnL_sort', 'fill_sort'])
    display['fill_pct'] = display['fill_pct'].map(_format_pct)
    display['skip_pct'] = display['skip_pct'].map(_format_pct)
    display['PF'] = display['PF'].map(_format_pf)
    display['AvgPnL'] = display['AvgPnL'].map(_format_num)
    display['TP_FIRST_pct'] = display['TP_FIRST_pct'].map(_format_pct)
    display['SL_FIRST_pct'] = display['SL_FIRST_pct'].map(_format_pct)
    display['NEITHER_pct'] = display['NEITHER_pct'].map(_format_pct)
    print(display.to_string(index=False))


def report_variant3_negative_controls(summary: pd.DataFrame):
    print_separator("Variant 3 Negative Controls")
    controls = summary[summary['cohort'].isin(VARIANT3_NEGATIVE_CONTROLS)].copy()
    if controls.empty:
        print("  No negative-control rows available.")
        return

    controls = controls.sort_values(['cohort', 'scenario', 'params'], kind='stable').reset_index(drop=True)
    controls['fill_pct'] = controls['fill_pct'].map(_format_pct)
    controls['skip_pct'] = controls['skip_pct'].map(_format_pct)
    controls['PF'] = controls['PF'].map(_format_pf)
    controls['AvgPnL'] = controls['AvgPnL'].map(_format_num)
    controls['TP_FIRST_pct'] = controls['TP_FIRST_pct'].map(_format_pct)
    controls['SL_FIRST_pct'] = controls['SL_FIRST_pct'].map(_format_pct)
    controls['NEITHER_pct'] = controls['NEITHER_pct'].map(_format_pct)
    print(controls.to_string(index=False))


def report_regime_splits(exc: pd.DataFrame, barrier_outcomes: pd.DataFrame, barrier_summary: pd.DataFrame):
    print_separator("Regime Split")

    best_barrier = _select_base_barrier_setups(barrier_summary, top_n=1)
    if best_barrier.empty:
        print("  No base-horizon barrier setup available.")
        return

    best = best_barrier.iloc[0]
    best_outcomes = barrier_outcomes[
        (barrier_outcomes['horizon'] == best['horizon']) &
        (barrier_outcomes['SL'] == best['SL']) &
        (barrier_outcomes['TP'] == best['TP'])
    ][['time', 'outcome']].rename(columns={'outcome': 'best_outcome'})
    merged = exc.merge(best_outcomes, on='time', how='left')
    best_label = f"{int(best['SL'])}/{int(best['TP'])}"
    ratio_order = ['<2', '2-3', '3-4', '4-5', '5+']
    ratio_series = merged['ratio_bin'].astype('object')

    specs = [
        ('BUY/SELL', pd.Series(np.where(merged['signal'] == 1, 'BUY', 'SELL'), index=merged.index)),
        ('ratio_bin', ratio_series.fillna('MISSING')),
        ('atr_bucket', merged['atr_bucket'].astype('object').fillna('ALL')),
    ]
    for title, groups in specs:
        rows = []
        if title == 'ratio_bin':
            group_values = [value for value in ratio_order if (groups == value).any()]
            if ratio_series.isna().any():
                group_values.append('MISSING')
        else:
            group_values = [value for value in dict.fromkeys(groups.tolist()) if pd.notna(value)]
        for value in group_values:
            sub = merged[groups == value]
            outcome_sub = sub['best_outcome'].dropna()
            rows.append({
                title: value,
                'N': len(sub),
                'MFE_12': _format_num(sub['mfe_12'].mean()),
                'MAE_12': _format_num(sub['mae_12'].mean()),
                'Net_12': _format_num(sub['net_12'].mean()),
                'PF_12': _format_pf(_profit_factor(sub['net_12'].dropna())),
                'TP_FIRST': _format_pct((outcome_sub == 'TP_FIRST').mean() * 100 if len(outcome_sub) else np.nan),
                'SL_FIRST': _format_pct((outcome_sub == 'SL_FIRST').mean() * 100 if len(outcome_sub) else np.nan),
                'Best': best_label,
            })
        print(f"\n  [{title}]")
        print(pd.DataFrame(rows).to_string(index=False))


def print_practical_conclusions(exc: pd.DataFrame, barrier_summary: pd.DataFrame):
    print_separator("Practical Conclusions")

    best = _select_base_barrier_setups(barrier_summary, top_n=1)
    if best.empty:
        sl_tp_line = "SL/TP: no base-horizon barrier summary available."
    else:
        row = best.iloc[0]
        sl_tp_line = (
            f"SL/TP: best base setup is H{int(row['horizon'])} SL={int(row['SL'])} TP={int(row['TP'])} "
            f"(PF={_format_pf(row['PF_num'])}, AvgPnL={_format_num(row['AvgPnL_num'])})."
        )

    print(
        f"  Entry: early adverse move averages adv_1={_format_num(exc['adv_1'].mean())} "
        f"and adv_3={_format_num(exc['adv_3'].mean())}, so entries should tolerate shallow pullbacks."
    )
    print(f"  {sl_tp_line}")
    print("  Filters: use amplitude buckets to compare low/mid/high predicted favorable and adverse profiles.")
    print("  Regimes: validate the best setup separately across BUY/SELL, ratio bins, and ATR buckets.")
    print("  Next for Variant 3: market entry, pullback limit entry, delayed entry, and cancel windows.")


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
    report_pic_price_validation(df, ohlc)

    print("\n  Вычисление MFE/MAE/Net...")
    exc = compute_excursions(df, ohlc)
    print(f"  Готово: {len(exc)} сигналов с excursion данными")
    barrier_outcomes = build_barrier_outcomes(exc, ohlc)
    barrier_summary = summarize_barrier_outcomes(barrier_outcomes)
    variant3_summary = build_variant3_summary(exc, ohlc)

    report_signal_passport(exc)
    report_by_ratio(exc)
    report_pullback_profile(exc)
    report_first_hit_barriers(barrier_summary)
    report_amplitude_filters(exc, barrier_outcomes, barrier_summary)
    report_regime_splits(exc, barrier_outcomes, barrier_summary)
    report_prediction_vs_reality(exc)
    report_cohort_map(exc, barrier_summary, barrier_outcomes)
    report_entry_opportunities(exc)
    report_stability_splits(exc, barrier_summary, barrier_outcomes)
    report_priority_cohorts(exc, barrier_summary, barrier_outcomes)
    report_variant3_scenario_matrix(variant3_summary)
    report_variant3_shortlist_verdict(variant3_summary)
    report_variant3_negative_controls(variant3_summary)
    print_practical_conclusions(exc, barrier_summary)


if __name__ == '__main__':
    main()
