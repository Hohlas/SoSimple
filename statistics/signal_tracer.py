# =============================================================================
# Файл: statistics/signal_tracer.py
# Назначение: Trade-level reconciliation — диагностика расхождения
#             между Python и MT4 для legacy regression_updn и Triple Barrier треков
# Язык: Python 3.11+
# Обновлён: 2026-04-08
# Зависимости:
#   Входные данные:
#     - MT/MQL4/Files/ml_signals.csv       (legacy ML предсказания: pred_up, pred_dn, ratio)
#     - MT/MQL4/Files/ml_signals_tb.csv    (TB сигналы: sl_atr, tp_atr, prob, ev)
#     - DATA/Nero_*_labeled.csv            (fractal[i][0]: price, fractal_atr; up/dn и TB labels)
#     - DATA/Nero_*_updn_params.npy        (per-row brk/cap для денормализации updn, shape (N,5,2))
#     - MT/tester/$o$imple.ini             (legacy параметры: ML_MinRatio, ML_ScaleK и др.)
#     - MT/tester/logs/YYYYMMDD.log        (--from-log: ML BUY/SELL ... или TB BUY/SELL ... из MT4)
#   Выходные данные:
#     - stdout (досье сигналов, сводные таблицы)
#     - [--csv-out PATH].csv               (экспорт для Excel/Python)
# Внешние зависимости:
#   - numpy (стандартная)
# Использование:
#   python statistics/signal_tracer.py --time "2025.12.29 16:00"
#   python statistics/signal_tracer.py --batch --top 10 --min-ratio 5.0 --csv-out batch.csv
#   python statistics/signal_tracer.py --from-log MT/tester/logs/20260324.log --losses-only --csv-out losses.csv
#   python statistics/signal_tracer.py --from-log MT/tester/logs/20260324.log --csv-out all_trades.csv
#   python statistics/signal_tracer.py --from-log MT/tester/logs/20260408_tb.log --signals MT/MQL4/Files/ml_signals_tb.csv --csv-out tb_trades.csv
# Примечания:
#   - bar_time из лога MT4 = time в ml_signals.csv (EA открывает сделку на следующем баре)
#   - fractal[i][0] в labeled CSV = триггерный фрактал (отсортированы, cols[4])
#   - up_12/dn_12 денормализуются per-row через brk/cap из Nero_*_updn_params.npy
#   - legacy SL/TP: точная реплика lib_ML_Signal.mqh строки 171–193
#   - TB outcome берётся напрямую из path-ordered TB labels в labeled CSV
# =============================================================================
import argparse
import os
import re
import csv
import math
import numpy as np
from datetime import datetime, timedelta, timezone


# ─── Normalization Stats ─────────────────────────────────────────────────────

NORM_STATS_DEFAULT = "DATA/Nero_normalization_stats.csv"

def load_normalization_stats(path=NORM_STATS_DEFAULT):
    """Загружает p85/p99 для up/dn полей из Nero_normalization_stats.csv."""
    stats = {}
    if not os.path.exists(path):
        return stats
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats[row['feature']] = {'p85': float(row['p85']), 'p99': float(row['p99'])}
    return stats


def inverse_piecewise_linear_log(y, brk, cap, linear_max=0.85, tail_strength=9.0):
    """Обратное преобразование piecewise linear-log → исходное значение в пунктах."""
    if y <= 0:
        return 0.0
    if y <= linear_max:
        return y / linear_max * brk
    # tail part: y = linear_max + (1 - linear_max) * log1p(tail_strength * t) / log1p(tail_strength)
    log_denom = math.log1p(tail_strength)
    t_log = (y - linear_max) / (1.0 - linear_max)
    t = (math.expm1(t_log * log_denom)) / tail_strength
    t = max(0.0, min(1.0, t))
    return brk + t * (cap - brk)


def denormalize_updn_row(y_norm_6, brk, cap):
    """Денормализация 6 значений updn (up_12..dn_48) для одной строки.

    Args:
        y_norm_6: array-like из 6 нормализованных значений [up_12, dn_12, ..., dn_48]
        brk: per-row breakpoint (p85 ненулевых updn значений строки)
        cap: per-row cap (p99 ненулевых updn значений строки)
    Returns:
        np.ndarray из 6 денормализованных значений в пунктах
    """
    return np.array([inverse_piecewise_linear_log(float(y), brk, cap) for y in y_norm_6])


UPDN_PARAMS_PATHS = [
    ('DATA/Nero_train_updn_params.npy',      'DATA/Nero_train_labeled.csv'),
    ('DATA/Nero_validation_updn_params.npy', 'DATA/Nero_validation_labeled.csv'),
    ('DATA/Nero_test_updn_params.npy',       'DATA/Nero_test_labeled.csv'),
]


def load_updn_params(nero_paths=None):
    """Загружает per-row updn_params (brk, cap) и строит маппинг time->params.

    Формат: (N, 5, 2) — per-pair brk/cap. Для up_12/dn_12 используется пара с индексом 2.

    Returns:
        dict {time_str: (brk, cap)} или {} если файлы не найдены.
    """
    paths = nero_paths or UPDN_PARAMS_PATHS
    time_to_params = {}
    for params_path, csv_path in paths:
        if not os.path.exists(params_path) or not os.path.exists(csv_path):
            continue
        params_arr = np.load(params_path)
        if params_arr.ndim != 3 or params_arr.shape[1:] != (5, 2):
            raise ValueError(
                f"updn_params неожиданной формы {params_arr.shape}, "
                f"ожидается (N, 5, 2). Перегенерируйте данные."
            )
        with open(csv_path, 'r', encoding='utf-8') as f:
            f.readline()  # header
            for i, line in enumerate(f):
                if i >= len(params_arr):
                    break
                t = line[:16]  # 'YYYY.MM.DD HH:MM'
                brk = params_arr[i, 2, 0]
                cap = params_arr[i, 2, 1]
                time_to_params[t] = (brk, cap)
    return time_to_params


# ─── INI Parser ──────────────────────────────────────────────────────────────

ML_DEFAULTS = {
    'ML_MinRatio': 3.5,
    'ML_MaxRR': 4.0,
    'ML_ScaleK': 20.0,
    'ML_Min_SL_ATR': 2.0,
}

def parse_ini(ini_path):
    """Читает ML-параметры из секции <inputs> файла $o$imple.ini."""
    params = dict(ML_DEFAULTS)
    if not os.path.exists(ini_path):
        print(f"  [!] INI не найден: {ini_path}, используются дефолты")
        return params

    in_inputs = False
    with open(ini_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line == '<inputs>':
                in_inputs = True
                continue
            if line == '</inputs>':
                break
            if not in_inputs:
                continue
            # Формат: KEY=VALUE (пропускаем KEY,F= KEY,1= итд)
            if ',' in line.split('=')[0]:
                continue
            m = re.match(r'^(ML_\w+)=([\d.+-]+)', line)
            if m and m.group(1) in params:
                params[m.group(1)] = float(m.group(2))
    return params


# ─── SL/TP Formula (реплика lib_ML_Signal.mqh:171-193) ──────────────────────

def calc_sl_tp(sig, pred_up, pred_dn, ratio_up, ratio_dn, atr, params):
    """Точная реплика MT4 формулы SL/TP из lib_ML_Signal.mqh."""
    scale_k = params['ML_ScaleK']
    min_sl_atr = params['ML_Min_SL_ATR']
    min_ratio = params['ML_MinRatio']
    max_rr = params['ML_MaxRR']

    if sig == 1:  # BUY
        sl = max(pred_dn * scale_k * atr, atr * min_sl_atr)
        tp = sl * min(ratio_up / min_ratio, max_rr)
    elif sig == -1:  # SELL
        sl = max(pred_up * scale_k * atr, atr * min_sl_atr)
        tp = sl * min(ratio_dn / min_ratio, max_rr)
    else:
        sl, tp = 0.0, 0.0
    return sl, tp


# ─── Classification ─────────────────────────────────────────────────────────

def classify_outcome(sig, up_12, dn_12, sl_dist, tp_dist):
    """
    4-категорийная классификация исхода сделки.
    BOTH_HIT — ключ к MFE/MAE иллюзии (оба барьера достигнуты, порядок неизвестен).
    """
    if sig == 1:
        sl_hit = dn_12 >= sl_dist
        tp_hit = up_12 >= tp_dist
    elif sig == -1:
        sl_hit = up_12 >= sl_dist
        tp_hit = dn_12 >= tp_dist
    else:
        return 'FLAT', 'Нет торгового сигнала'

    if tp_hit and not sl_hit:
        return 'TP_CLEAR', 'TP достигнут, SL не задет'
    elif sl_hit and not tp_hit:
        return 'SL_CLEAR', 'SL достигнут, TP недосягаем'
    elif tp_hit and sl_hit:
        return 'BOTH_HIT', 'Оба барьера достигнуты (порядок неизвестен — MFE/MAE иллюзия)'
    else:
        return 'TIMEOUT', 'Ни SL, ни TP не достигнуты за 12H'


# ─── Fractal Parsing ────────────────────────────────────────────────────────

FRACTAL_FIELDS = [
    'fractal_time', 'price', 'direction', 'front', 'back', 'strong',
    'break_status', 'reverse', 'power', 'count', 'impulse',
    'up_12', 'dn_12', 'up_24', 'dn_24', 'up_48', 'dn_48',
    'up_3', 'dn_3', 'up_6', 'dn_6', 'fractal_atr'
]

def parse_fractal0(fractal_str):
    """Парсинг строки fractal0 (23 поля)."""
    parts = fractal_str.split(':')
    if len(parts) != 23:
        return None
    try:
        return {
            'fractal_time': int(parts[0]),
            'price': float(parts[1]),
            'direction': int(parts[2]),
            'front': float(parts[3]),
            'back': float(parts[4]),
            'strong': int(parts[5]),
            'break_status': int(parts[6]),
            'reverse': float(parts[7]),
            'power': float(parts[8]),
            'count': int(parts[9]),
            'impulse': float(parts[10]),
            'up_12': float(parts[11]),
            'dn_12': float(parts[12]),
            'up_24': float(parts[13]),
            'dn_24': float(parts[14]),
            'up_48': float(parts[15]),
            'dn_48': float(parts[16]),
            'fractal_atr': float(parts[21])
        }
    except (ValueError, IndexError):
        return None


def time_str_to_unix(time_str):
    """'YYYY.MM.DD HH:MM' -> unix timestamp."""
    return int(datetime.strptime(time_str, "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc).timestamp())


# ─── Dossier Builder ────────────────────────────────────────────────────────

def build_dossier(target_time, signal_row, nero_cols, fractal, params, mt4_trade=None,
                  updn_params_map=None):
    """
    Строит досье для одного сигнала.
    signal_row: dict из ml_signals.csv (time, signal, pred_up, pred_dn, ratio_up, ratio_dn)
    nero_cols: list of raw columns from Nero.csv row
    fractal: parsed fractal0 dict
    params: ML parameters dict
    updn_params_map: dict {time_str: (brk, cap)} из load_updn_params()
    Returns: dict with all diagnostic fields
    """
    if 'sl_atr' in signal_row and 'tp_atr' in signal_row:
        return build_tb_dossier(target_time, signal_row, nero_cols, fractal, mt4_trade=mt4_trade)

    d = {'time': target_time}

    # ML prediction data
    sig = int(signal_row.get('signal', 0))
    pred_up = float(signal_row.get('pred_up', 0))
    pred_dn = float(signal_row.get('pred_dn', 0))
    ratio_up = float(signal_row.get('ratio_up', 0))
    ratio_dn = float(signal_row.get('ratio_dn', 0))

    d['signal'] = sig
    d['pred_up'] = pred_up
    d['pred_dn'] = pred_dn
    d['ratio_up'] = ratio_up
    d['ratio_dn'] = ratio_dn
    d['ratio'] = ratio_up if sig == 1 else ratio_dn if sig == -1 else 0
    d['direction'] = 'BUY' if sig == 1 else 'SELL' if sig == -1 else 'FLAT'

    # MT4 actual trade data — заполняем до раннего выхода, чтобы данные лога были в CSV
    if mt4_trade:
        mt4_sl = abs(mt4_trade['val'] - mt4_trade['stp'])
        mt4_tp = abs(mt4_trade['prf'] - mt4_trade['val'])
        d['val']          = mt4_trade['val']
        d['stp']          = mt4_trade['stp']
        d['prf']          = mt4_trade['prf']
        d['atr_mt4']      = mt4_trade['atr_mt4']
        d['mt4_sl_dist']  = mt4_sl
        d['mt4_tp_dist']  = mt4_tp
        d['mt4_sl_atr']   = mt4_sl / mt4_trade['atr_mt4'] if mt4_trade['atr_mt4'] > 0 else 0
        d['mt4_tp_atr']   = mt4_tp / mt4_trade['atr_mt4'] if mt4_trade['atr_mt4'] > 0 else 0
        d['close_type']   = mt4_trade['close_type']
        d['close_price']  = mt4_trade['close_price']
        d['mt4']          = mt4_trade
        ct = mt4_trade['close_type']
        if ct == 'SL':
            d['mt4_result'] = 'LOSS(SL)'
        elif ct == 'TP':
            d['mt4_result'] = 'WIN(TP)'
        elif ct == 'MARKET':
            if mt4_trade['dir'] == 'BUY':
                d['mt4_result'] = 'WIN(MKT)' if mt4_trade['close_price'] > mt4_trade['val'] else 'LOSS(MKT)'
            else:
                d['mt4_result'] = 'WIN(MKT)' if mt4_trade['close_price'] < mt4_trade['val'] else 'LOSS(MKT)'
        else:
            d['mt4_result'] = ct

        # P&L расчёт
        cp = mt4_trade.get('close_price')
        atr_mt4 = mt4_trade['atr_mt4']
        if cp is not None and cp > 0:
            if mt4_trade['dir'] == 'BUY':
                d['mt4_pnl_pips'] = cp - mt4_trade['val']
            else:
                d['mt4_pnl_pips'] = mt4_trade['val'] - cp
            d['mt4_pnl_atr'] = d['mt4_pnl_pips'] / atr_mt4 if atr_mt4 > 0 else 0
        elif ct == 'SL':
            d['mt4_pnl_pips'] = -mt4_sl
            d['mt4_pnl_atr'] = -d.get('mt4_sl_atr', 0)
        elif ct == 'TP':
            d['mt4_pnl_pips'] = mt4_tp
            d['mt4_pnl_atr'] = d.get('mt4_tp_atr', 0)

    if fractal is None:
        d['error'] = 'fractal0 не распарсен'
        return d

    atr = fractal['fractal_atr']
    d['price'] = fractal['price']
    d['atr'] = atr

    # up_12/dn_12: берём нормализованные из cols[104]/[105], денормализуем per-row brk/cap
    # Labeled формат: time;signal;predict;ATR;fractal0..fractal99;up_12;dn_12;...
    # cols[104]=up_12, cols[105]=dn_12 (после 100 фракталов, cols[4..103])
    d['up_12'] = 0.0
    d['dn_12'] = 0.0
    if nero_cols and len(nero_cols) > 105 and updn_params_map:
        row_params = updn_params_map.get(target_time)
        if row_params:
            brk, cap = row_params
            y_norm_6 = [float(nero_cols[104]), float(nero_cols[105]),
                        float(nero_cols[106]) if len(nero_cols) > 106 else 0.0,
                        float(nero_cols[107]) if len(nero_cols) > 107 else 0.0,
                        float(nero_cols[108]) if len(nero_cols) > 108 else 0.0,
                        float(nero_cols[109]) if len(nero_cols) > 109 else 0.0]
            vals = denormalize_updn_row(y_norm_6, brk, cap)
            d['up_12'] = vals[0]
            d['dn_12'] = vals[1]

    # SL/TP по формуле MT4
    sl_dist, tp_dist = calc_sl_tp(sig, pred_up, pred_dn, ratio_up, ratio_dn, atr, params)
    d['sl_dist'] = sl_dist
    d['tp_dist'] = tp_dist

    # SL formula breakdown
    if sig == 1:
        pred_component = pred_dn * params['ML_ScaleK'] * atr
        floor_component = atr * params['ML_Min_SL_ATR']
    elif sig == -1:
        pred_component = pred_up * params['ML_ScaleK'] * atr
        floor_component = atr * params['ML_Min_SL_ATR']
    else:
        pred_component = 0
        floor_component = 0
    d['sl_from_pred'] = pred_component
    d['sl_from_floor'] = floor_component
    d['sl_source'] = 'pred*ScaleK' if pred_component >= floor_component else 'Min_SL_ATR'

    # SL/TP в ATR
    d['sl_atr'] = sl_dist / atr if atr > 0 else 0
    d['tp_atr'] = tp_dist / atr if atr > 0 else 0

    # Classification (использует денормализованные d['up_12']/d['dn_12'])
    category, detail = classify_outcome(sig, d['up_12'], d['dn_12'], sl_dist, tp_dist)
    d['category'] = category
    d['category_detail'] = detail

    # Lag bias
    signal_time_unix = time_str_to_unix(target_time)
    fractal_time_unix = fractal['fractal_time']
    lag_seconds = signal_time_unix - fractal_time_unix
    d['lag_bars'] = lag_seconds / 3600  # H1 bars
    d['lag_seconds'] = lag_seconds
    d['fractal_time_unix'] = fractal_time_unix

    # Дельты формулы vs MT4 (требуют atr из фрактала)
    if mt4_trade:
        d['atr_delta'] = mt4_trade['atr_mt4'] - atr
        d['sl_delta']  = d['mt4_sl_dist'] - sl_dist
        d['tp_delta']  = d['mt4_tp_dist'] - tp_dist

    return d


def build_tb_dossier(target_time, signal_row, nero_cols, fractal, mt4_trade=None):
    d = {'time': target_time, 'track': 'tb'}

    sig = int(signal_row.get('signal', 0))
    sl_atr = float(signal_row.get('sl_atr', 0))
    tp_atr = float(signal_row.get('tp_atr', 0))
    prob = float(signal_row.get('prob', 0))
    ev = float(signal_row.get('ev', 0))

    d['signal'] = sig
    d['direction'] = 'BUY' if sig == 1 else 'SELL' if sig == -1 else 'FLAT'
    d['ratio'] = prob
    d['prob'] = prob
    d['ev'] = ev
    d['sl_atr'] = sl_atr
    d['tp_atr'] = tp_atr

    target_name = ''
    if sig in (1, -1) and sl_atr > 0 and tp_atr > 0:
        prefix = 'buy' if sig == 1 else 'sell'
        target_name = f"{prefix}_sl{int(round(sl_atr))}_tp{int(round(tp_atr))}"
    d['target_name'] = target_name

    if mt4_trade:
        mt4_sl = abs(mt4_trade['val'] - mt4_trade['stp'])
        mt4_tp = abs(mt4_trade['prf'] - mt4_trade['val'])
        d['val'] = mt4_trade['val']
        d['stp'] = mt4_trade['stp']
        d['prf'] = mt4_trade['prf']
        d['atr_mt4'] = mt4_trade['atr_mt4']
        d['mt4_sl_dist'] = mt4_sl
        d['mt4_tp_dist'] = mt4_tp
        d['mt4_sl_atr'] = mt4_sl / mt4_trade['atr_mt4'] if mt4_trade['atr_mt4'] > 0 else 0
        d['mt4_tp_atr'] = mt4_tp / mt4_trade['atr_mt4'] if mt4_trade['atr_mt4'] > 0 else 0
        d['close_type'] = mt4_trade['close_type']
        d['close_price'] = mt4_trade['close_price']
        ct = mt4_trade['close_type']
        if ct == 'SL':
            d['mt4_result'] = 'LOSS(SL)'
        elif ct == 'TP':
            d['mt4_result'] = 'WIN(TP)'
        elif ct == 'MARKET':
            if mt4_trade['dir'] == 'BUY':
                d['mt4_result'] = 'WIN(MKT)' if mt4_trade['close_price'] > mt4_trade['val'] else 'LOSS(MKT)'
            else:
                d['mt4_result'] = 'WIN(MKT)' if mt4_trade['close_price'] < mt4_trade['val'] else 'LOSS(MKT)'
        else:
            d['mt4_result'] = ct

        cp = mt4_trade.get('close_price')
        atr_mt4 = mt4_trade['atr_mt4']
        if cp is not None and cp > 0:
            if mt4_trade['dir'] == 'BUY':
                d['mt4_pnl_pips'] = cp - mt4_trade['val']
            else:
                d['mt4_pnl_pips'] = mt4_trade['val'] - cp
            d['mt4_pnl_atr'] = d['mt4_pnl_pips'] / atr_mt4 if atr_mt4 > 0 else 0
        elif ct == 'SL':
            d['mt4_pnl_pips'] = -mt4_sl
            d['mt4_pnl_atr'] = -d.get('mt4_sl_atr', 0)
        elif ct == 'TP':
            d['mt4_pnl_pips'] = mt4_tp
            d['mt4_pnl_atr'] = d.get('mt4_tp_atr', 0)

    if fractal is None:
        d['error'] = 'fractal0 не распарсен'
        return d

    atr = fractal['fractal_atr']
    d['price'] = fractal['price']
    d['atr'] = atr
    d['sl_dist'] = sl_atr * atr
    d['tp_dist'] = tp_atr * atr

    outcome_value = np.nan
    if target_name and nero_cols and target_name in TB_TARGET_NAMES:
        col_idx = TB_COLUMN_BASE + TB_TARGET_NAMES.index(target_name)
        if len(nero_cols) > col_idx:
            try:
                outcome_value = float(nero_cols[col_idx])
            except ValueError:
                outcome_value = np.nan

    d['label_value'] = outcome_value
    if outcome_value == 1.0:
        d['category'] = 'TP_FIRST'
        d['category_detail'] = 'TP reached first in path-ordered TB label'
    elif outcome_value == 0.5:
        d['category'] = 'TIMEOUT'
        d['category_detail'] = 'Neither barrier reached within TB timeout window'
    elif outcome_value == 0.0:
        d['category'] = 'SL_FIRST'
        d['category_detail'] = 'SL reached first in path-ordered TB label'
    else:
        d['category'] = 'UNKNOWN'
        d['category_detail'] = 'TB target not found in labeled row'

    signal_time_unix = time_str_to_unix(target_time)
    fractal_time_unix = fractal['fractal_time']
    lag_seconds = signal_time_unix - fractal_time_unix
    d['lag_bars'] = lag_seconds / 3600
    d['lag_seconds'] = lag_seconds
    d['fractal_time_unix'] = fractal_time_unix

    if mt4_trade:
        d['atr_delta'] = mt4_trade['atr_mt4'] - atr
        d['sl_delta'] = d['mt4_sl_atr'] - sl_atr
        d['tp_delta'] = d['mt4_tp_atr'] - tp_atr

    return d


def print_dossier(d, params):
    """Печать полного досье одного сигнала."""
    print(f"\n{'='*60}")
    print(f"  ДОСЬЕ СИГНАЛА: {d['time']}")
    print(f"{'='*60}")

    if d.get('track') == 'tb':
        print(f"\n--- TB Оценка ---")
        print(f"  Направление : {d['direction']} ({d['signal']})")
        print(f"  Target      : {d.get('target_name', '')}")
        print(f"  prob        : {d.get('prob', 0):.4f}")
        print(f"  ev          : {d.get('ev', 0):.4f}")
        print(f"  SL / TP ATR : {d.get('sl_atr', 0):.2f} / {d.get('tp_atr', 0):.2f}")

        if 'error' in d:
            print(f"\n  [!] {d['error']}")
            return

        print(f"\n--- TB Ground Truth ---")
        print(f"  Цена фрактала : {d['price']:.5f}")
        print(f"  ATR (fractal) : {d['atr']:.5f}")
        print(f"  Label outcome : {d.get('category', '?')} ({d.get('label_value', float('nan'))})")

        if 'mt4_result' in d:
            print(f"\n--- MT4 Реальные уровни ---")
            print(f"  MT4 result   : {d.get('mt4_result', '?')}")
            print(f"  SL / TP ATR  : {d.get('mt4_sl_atr', 0):.2f} / {d.get('mt4_tp_atr', 0):.2f}")
            print(f"  Δ ATR units  : SL {d.get('sl_delta', 0):+.3f}, TP {d.get('tp_delta', 0):+.3f}")

        print(f"\n--- TB Диагноз ---")
        print(f"  {d.get('category', '?')}: {d.get('category_detail', '')}")
        return

    # ML prediction
    print(f"\n--- ML Оценка ---")
    print(f"  Направление : {d['direction']} ({d['signal']})")
    print(f"  pred_up     : {d['pred_up']:.6f}")
    print(f"  pred_dn     : {d['pred_dn']:.6f}")
    print(f"  ratio_up    : {d['ratio_up']:.2f}")
    print(f"  ratio_dn    : {d['ratio_dn']:.2f}")

    if 'error' in d:
        print(f"\n  [!] {d['error']}")
        return

    # MT4 math
    print(f"\n--- Математика MT4 (lib_ML_Signal.mqh) ---")
    print(f"  ML_MinRatio = {params['ML_MinRatio']}, ML_MaxRR = {params['ML_MaxRR']}")
    print(f"  ML_ScaleK   = {params['ML_ScaleK']}, ML_Min_SL_ATR = {params['ML_Min_SL_ATR']}")
    print(f"  ATR (fractal): {d['atr']:.5f}")
    print(f"  SL = max(pred*ScaleK*ATR, ATR*Min_SL_ATR) = max({d['sl_from_pred']:.5f}, {d['sl_from_floor']:.5f}) = {d['sl_dist']:.5f}  [{d['sl_source']}]")
    rr_mult = d['tp_dist'] / d['sl_dist'] if d['sl_dist'] > 0 else 0
    print(f"  TP = SL * min(ratio/MinRatio, MaxRR) = {d['tp_dist']:.5f}")
    print(f"  R:R = 1 : {rr_mult:.2f}")
    print(f"  SL в ATR: {d['sl_atr']:.2f},  TP в ATR: {d['tp_atr']:.2f}")

    # Ground truth
    print(f"\n--- Ground Truth (MFE/MAE за 12H после фрактала) ---")
    print(f"  Цена фрактала : {d['price']:.5f}")
    print(f"  Реальный ВВЕРХ: {d['up_12']:.5f}")
    print(f"  Реальный ВНИЗ : {d['dn_12']:.5f}")

    # Lag bias
    lag = d['lag_bars']
    ft = datetime.fromtimestamp(d['fractal_time_unix'], tz=timezone.utc).strftime('%Y.%m.%d %H:%M')
    print(f"\n--- Lag Bias ---")
    print(f"  Время формирования фрактала: {ft}")
    print(f"  Время сигнального бара:      {d['time']}")
    print(f"  Задержка: {lag:.0f} бар(а) ({d['lag_seconds']/3600:.0f}ч)")
    if lag <= 5:
        print(f"  Нормальная задержка (PicPer подтверждение)")
    elif lag <= 48:
        print(f"  Умеренная задержка — фрактал не самый свежий")
    else:
        print(f"  ! Фрактал устарел ({lag:.0f} баров) — ML предсказывает на основе старых данных")

    # MT4 actual vs formula comparison
    if 'mt4' in d:
        m = d['mt4']
        print(f"\n--- MT4 Реальные уровни (из лога тестера) ---")
        print(f"  Результат  : {d.get('mt4_result','?')}  (закрытие: {d.get('close_type','?')} @ {d.get('close_price','?')})")
        print(f"  Val (вход) : {m['val']:.5f}")
        print(f"  Stp (SL)   : {m['stp']:.5f}  →  SL дист = {d['mt4_sl_dist']:.5f}  ({d['mt4_sl_atr']:.2f} ATR)")
        print(f"  Prf (TP)   : {m['prf']:.5f}  →  TP дист = {d['mt4_tp_dist']:.5f}  ({d['mt4_tp_atr']:.2f} ATR)")
        print(f"  ATR (MT4 бар): {d['atr_mt4']:.5f}")
        print(f"\n  Сравнение формула vs MT4:")
        print(f"  ATR: фрактал={d['atr']:.5f}  MT4_бар={d['atr_mt4']:.5f}  delta={d['atr_delta']:+.5f}")
        print(f"  SL:  формула={d['sl_dist']:.5f}  MT4={d['mt4_sl_dist']:.5f}  delta={d['sl_delta']:+.5f}")
        print(f"  TP:  формула={d['tp_dist']:.5f}  MT4={d['mt4_tp_dist']:.5f}  delta={d['tp_delta']:+.5f}")

    # Diagnosis
    print(f"\n--- ДИАГНОЗ ---")
    cat = d['category']
    if cat == 'TP_CLEAR':
        print(f"  TP_CLEAR: {d['category_detail']}")
    elif cat == 'SL_CLEAR':
        print(f"  SL_CLEAR: {d['category_detail']}")
    elif cat == 'BOTH_HIT':
        print(f"  BOTH_HIT: {d['category_detail']}")
        if d['signal'] == 1:
            print(f"     Dn_12 ({d['dn_12']:.5f}) >= SL ({d['sl_dist']:.5f}) И Up_12 ({d['up_12']:.5f}) >= TP ({d['tp_dist']:.5f})")
        else:
            print(f"     Up_12 ({d['up_12']:.5f}) >= SL ({d['sl_dist']:.5f}) И Dn_12 ({d['dn_12']:.5f}) >= TP ({d['tp_dist']:.5f})")
        print(f"     Python засчитает ПРОФИТ, MT4 мог закрыть по СТОПУ (зависит от порядка)")
    elif cat == 'TIMEOUT':
        print(f"  TIMEOUT: {d['category_detail']}")


# ─── File Loaders ────────────────────────────────────────────────────────────

def load_signal(target_time, signals_path):
    """Найти строку в ml_signals.csv по точному совпадению time."""
    if not os.path.exists(signals_path):
        return None
    with open(signals_path, 'r', encoding='utf-8') as f:
        headers = f.readline().strip().split(';')
        for line in f:
            row = line.strip().split(';')
            if row[0] == target_time:
                return dict(zip(headers, row))
    return None


def load_nero_row(target_time, nero_paths):
    """Найти строку в labeled-файлах по совпадению time.
    nero_paths: список путей к Nero_*_labeled.csv.
    Labeled формат: time;signal;predict;up_12;dn_12;up_24;dn_24;up_48;dn_48;ATR;fractal0;...
    fractal0 (cols[10]) — новейший фрактал (fractal[i][0]) с fractal_atr и price.
    """
    if isinstance(nero_paths, str):
        nero_paths = [nero_paths]
    for path in nero_paths:
        if not os.path.exists(path):
            continue
        with open(path, 'r', encoding='utf-8') as f:
            f.readline()  # пропускаем заголовок
            for line in f:
                if line.startswith(target_time):
                    cols = line.strip().split(';')
                    fractal = parse_fractal0(cols[4]) if len(cols) > 4 and cols[4] else None
                    return cols, fractal
    return None, None


def load_all_signals(signals_path, min_ratio=0.0):
    """Загрузить все ненулевые сигналы из ml_signals.csv. Фильтр по ratio."""
    results = []
    if not os.path.exists(signals_path):
        return results
    with open(signals_path, 'r', encoding='utf-8') as f:
        headers = f.readline().strip().split(';')
        for line in f:
            row = line.strip().split(';')
            if len(row) < len(headers):
                continue
            d = dict(zip(headers, row))
            sig = int(d.get('signal', 0))
            if sig == 0:
                continue
            ratio_up = float(d.get('ratio_up', 0))
            ratio_dn = float(d.get('ratio_dn', 0))
            ratio = ratio_up if sig == 1 else ratio_dn
            if ratio >= min_ratio:
                d['_ratio'] = ratio
                results.append(d)
    return results


def load_nero_batch(target_times_set, nero_paths):
    """Проход по labeled-файлам — собрать строки, чьи time в target_times_set.
    nero_paths: список путей к Nero_*_labeled.csv.
    """
    if isinstance(nero_paths, str):
        nero_paths = [nero_paths]
    matched = {}
    remaining = set(target_times_set)
    for path in nero_paths:
        if not os.path.exists(path) or not remaining:
            continue
        with open(path, 'r', encoding='utf-8') as f:
            f.readline()  # заголовок
            for line in f:
                time_key = line[:16]
                if time_key in remaining:
                    cols = line.strip().split(';')
                    fractal = parse_fractal0(cols[4]) if len(cols) > 4 and cols[4] else None
                    matched[time_key] = (cols, fractal)
                    remaining.discard(time_key)
    return matched


# ─── Log Parser ─────────────────────────────────────────────────────────────

RE_ML_ENTRY = re.compile(
    r'ML (BUY|SELL) ratio=([\d.]+) Val=([\d.]+) Stp=([\d.]+) Prf=([\d.]+) ATR=([\d.]+) bar=(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2})'
)
RE_TB_ENTRY = re.compile(
    r'TB (BUY|SELL) prob=([-\d.]+) ev=([-\d.]+) SL=([-\d.]+)ATR TP=([-\d.]+)ATR '
    r'Val=([\d.]+) Stp=([\d.]+) Prf=([\d.]+) ATR=([\d.]+) bar=(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2})'
)
RE_OPEN    = re.compile(r'open #(\d+) (buy|sell)')
RE_SL      = re.compile(r'Tester: stop loss #(\d+)')
RE_TP      = re.compile(r'Tester: take profit #(\d+)')
RE_CLOSE   = re.compile(r'close #(\d+) (?:buy|sell) .+? at price ([\d.]+)')
TB_TARGET_NAMES = [
    'buy_sl2_tp3', 'buy_sl2_tp6', 'buy_sl2_tp9',
    'buy_sl3_tp3', 'buy_sl3_tp6', 'buy_sl3_tp9',
    'sell_sl2_tp3', 'sell_sl2_tp6', 'sell_sl2_tp9',
    'sell_sl3_tp3', 'sell_sl3_tp6', 'sell_sl3_tp9',
]
TB_COLUMN_BASE = 114


def parse_tb_signal_line(line: str) -> dict:
    return {
        'prob': float(re.search(r'prob=([-\d.]+)', line).group(1)),
        'ev': float(re.search(r'ev=([-\d.]+)', line).group(1)),
        'sl_atr': float(re.search(r'SL=([-\d.]+)ATR', line).group(1)),
        'tp_atr': float(re.search(r'TP=([-\d.]+)ATR', line).group(1)),
        'bar_time': re.search(r'bar=([0-9. :]+)$', line).group(1),
    }


def parse_log(log_path):
    """
    Парсит лог MT4 тестера и возвращает список исполненных ML-сделок.
    Каждая запись: bar_time, dir, ratio, val, stp, prf, atr_mt4,
                   order_num, close_type (SL/TP/MARKET), close_price.
    """
    trades   = {}    # order_num -> dict
    pending  = None  # ждём open #N после ML BUY/SELL
    results  = []

    with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            m = RE_ML_ENTRY.search(line)
            if m:
                pending = {
                    'track':    'legacy',
                    'dir':      m.group(1),
                    'ratio':    float(m.group(2)),
                    'val':      float(m.group(3)),
                    'stp':      float(m.group(4)),
                    'prf':      float(m.group(5)),
                    'atr_mt4':  float(m.group(6)),
                    'bar_time': m.group(7),
                    'order_num':   None,
                    'close_type':  None,
                    'close_price': None,
                }
                continue

            m = RE_TB_ENTRY.search(line)
            if m:
                pending = {
                    'track':    'tb',
                    'dir':      m.group(1),
                    'prob':     float(m.group(2)),
                    'ev':       float(m.group(3)),
                    'sl_atr':   float(m.group(4)),
                    'tp_atr':   float(m.group(5)),
                    'val':      float(m.group(6)),
                    'stp':      float(m.group(7)),
                    'prf':      float(m.group(8)),
                    'atr_mt4':  float(m.group(9)),
                    'bar_time': m.group(10),
                    'order_num':   None,
                    'close_type':  None,
                    'close_price': None,
                }
                continue

            m = RE_OPEN.search(line)
            if m and pending:
                n = int(m.group(1))
                pending['order_num'] = n
                trades[n] = pending
                pending = None
                continue

            m = RE_SL.search(line)
            if m:
                n = int(m.group(1))
                if n in trades:
                    trades[n]['close_type'] = 'SL'
                    results.append(trades.pop(n))
                continue

            m = RE_TP.search(line)
            if m:
                n = int(m.group(1))
                if n in trades:
                    trades[n]['close_type'] = 'TP'
                    results.append(trades.pop(n))
                continue

            m = RE_CLOSE.search(line)
            if m:
                n = int(m.group(1))
                if n in trades:
                    trades[n]['close_type']  = 'MARKET'
                    trades[n]['close_price'] = float(m.group(2))
                    results.append(trades.pop(n))

    # Сделки без закрытия (тест закончился, позиция ещё открыта)
    for t in trades.values():
        t['close_type'] = 'OPEN'
        results.append(t)

    return results


def from_log_reconciliation(log_path, signals_path, nero_path, params, losses_only, csv_out, updn_params_map=None):
    """
    Разбор всех исполненных ML-сделок из лога тестера.
    Для каждой сделки: реальные MT4 Val/Stp/Prf/ATR vs формула vs Ground Truth.
    """
    print(f"[1] Парсинг лога {log_path}...")
    all_trades = parse_log(log_path)
    print(f"  Найдено сделок: {len(all_trades)}")

    if losses_only:
        trades = [t for t in all_trades if t['close_type'] == 'SL']
        print(f"  Фильтр --losses-only (SL): {len(trades)} сделок")
    else:
        trades = all_trades

    if not trades:
        print("  [!] Нет подходящих сделок.")
        return

    # Загрузка ML-сигналов и Nero пакетом
    target_times = {t['bar_time'] for t in trades}
    print(f"[2] Загрузка ml_signals.csv...")
    all_sig_rows = {}
    if os.path.exists(signals_path):
        with open(signals_path, 'r', encoding='utf-8') as f:
            headers = f.readline().strip().split(';')
            for line in f:
                row = line.strip().split(';')
                if row[0] in target_times:
                    all_sig_rows[row[0]] = dict(zip(headers, row))

    print(f"[3] Загрузка Nero.csv ({len(target_times)} записей)...")
    nero_data = load_nero_batch(target_times, nero_path)
    print(f"  Совпадений Nero: {len(nero_data)}")

    # Строим досье
    dossiers = []
    for t in trades:
        bt = t['bar_time']
        sig_row = all_sig_rows.get(bt)
        nero_cols, fractal = nero_data.get(bt, (None, None))
        if sig_row is None:
            if t.get('track') == 'tb':
                sig_row = {
                    'time': bt,
                    'signal': '1' if t['dir'] == 'BUY' else '-1',
                    'sl_atr': str(t.get('sl_atr', 0)),
                    'tp_atr': str(t.get('tp_atr', 0)),
                    'prob': str(t.get('prob', 0)),
                    'ev': str(t.get('ev', 0)),
                }
            else:
                sig_row = {
                    'time': bt,
                    'signal': '1' if t['dir'] == 'BUY' else '-1',
                    'pred_up': '0', 'pred_dn': '0',
                    'ratio_up': str(t['ratio']) if t['dir'] == 'BUY' else '0',
                    'ratio_dn': str(t['ratio']) if t['dir'] == 'SELL' else '0',
                }
        d = build_dossier(bt, sig_row, nero_cols, fractal, params, mt4_trade=t, updn_params_map=updn_params_map)
        dossiers.append(d)

    # Сводная таблица
    counts_mt4  = {}
    counts_nero = {}
    total_sl_delta = 0.0
    total_tp_delta = 0.0
    n_delta = 0

    print(f"\n{'='*115}")
    label = 'losses (SL only)' if losses_only else 'all trades'
    print(f"  FROM-LOG RECONCILIATION  |  {label}  |  {len(dossiers)} сделок")
    print(f"{'='*115}")

    hdr = (f" {'#':>3} | {'Time':<18} | {'Dir':<4} | {'Ratio':>6} | "
           f"{'MT4_SL':>7} | {'FML_SL':>7} | {'Δ_SL':>6} | "
           f"{'MT4_TP':>7} | {'FML_TP':>7} | {'Δ_TP':>6} | "
           f"{'Up12':>7} | {'Dn12':>7} | {'NeroRes':<9} | {'MT4_Res':<10}")
    print(hdr)
    print('-' * len(hdr))

    for i, d in enumerate(dossiers, 1):
        ct = d.get('close_type', '?')
        counts_mt4[ct] = counts_mt4.get(ct, 0) + 1
        nc = d.get('category', '?')
        counts_nero[nc] = counts_nero.get(nc, 0) + 1

        mt4_sl = f"{d.get('mt4_sl_dist', 0):.2f}" if 'mt4_sl_dist' in d else '?'
        fml_sl = f"{d.get('sl_dist', 0):.2f}"     if 'sl_dist' in d else '?'
        d_sl   = f"{d.get('sl_delta', 0):+.2f}"   if 'sl_delta' in d else '?'
        mt4_tp = f"{d.get('mt4_tp_dist', 0):.2f}" if 'mt4_tp_dist' in d else '?'
        fml_tp = f"{d.get('tp_dist', 0):.2f}"     if 'tp_dist' in d else '?'
        d_tp   = f"{d.get('tp_delta', 0):+.2f}"   if 'tp_delta' in d else '?'
        up12   = f"{d.get('up_12', 0):.2f}"        if 'up_12' in d else '?'
        dn12   = f"{d.get('dn_12', 0):.2f}"        if 'dn_12' in d else '?'

        if 'sl_delta' in d:
            total_sl_delta += d['sl_delta']
            total_tp_delta += d['tp_delta']
            n_delta += 1

        print(f" {i:>3} | {d['time']:<18} | {d['direction']:<4} | {d.get('ratio',0):>6.2f} | "
              f"{mt4_sl:>7} | {fml_sl:>7} | {d_sl:>6} | "
              f"{mt4_tp:>7} | {fml_tp:>7} | {d_tp:>6} | "
              f"{up12:>7} | {dn12:>7} | {nc:<9} | {d.get('mt4_result','?'):<10}")

    print(f"\n  MT4 результаты : " + ", ".join(f"{k}={v}" for k, v in sorted(counts_mt4.items())))
    print(f"  Nero категории : " + ", ".join(f"{k}={v}" for k, v in sorted(counts_nero.items())))
    if n_delta > 0:
        print(f"  Ср. погрешность формулы: SL Δ={total_sl_delta/n_delta:+.3f}  TP Δ={total_tp_delta/n_delta:+.3f}")

    # Детальные досье
    print(f"\n{'='*60}")
    print(f"  ДЕТАЛЬНЫЕ ДОСЬЕ")
    print(f"{'='*60}")
    for d in dossiers:
        print_dossier(d, params)

    # CSV
    if csv_out:
        fieldnames = ['time', 'direction', 'ratio', 'close_type', 'mt4_result',
                      'val', 'stp', 'prf', 'close_price', 'atr_mt4',
                      'mt4_sl_dist', 'mt4_tp_dist', 'mt4_sl_atr', 'mt4_tp_atr',
                      'mt4_pnl_pips', 'mt4_pnl_atr',
                      'price', 'sl_dist', 'tp_dist', 'sl_atr', 'tp_atr',
                      'sl_delta', 'tp_delta', 'atr_delta',
                      'up_12', 'dn_12', 'category', 'lag_bars']
        with open(csv_out, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', extrasaction='ignore')
            writer.writeheader()
            for d in dossiers:
                writer.writerow(d)
        print(f"\n  CSV экспортирован: {csv_out}")


# ─── Single Trace Mode ──────────────────────────────────────────────────────

def trace_signal(target_time, nero_path, signals_path, params, updn_params_map=None):
    """Полный разбор одного сигнала. Если время не найдено — пробует time-1H (смещение EA)."""
    print(f"[1] Поиск ML-интерпретации в {signals_path}...")
    signal_row = load_signal(target_time, signals_path)
    actual_time = target_time
    if not signal_row:
        # EA открывает сделку на баре T, читая сигнал бара T-1
        t_minus1 = (datetime.strptime(target_time, "%Y.%m.%d %H:%M") - timedelta(hours=1)).strftime("%Y.%m.%d %H:%M")
        signal_row = load_signal(t_minus1, signals_path)
        if signal_row:
            print(f"  [i] Сигнал не найден для {target_time}, используется T-1: {t_minus1}")
            actual_time = t_minus1
        else:
            print(f"  [!] Сигнал '{target_time}' не найден в {signals_path}")
            return

    print(f"[2] Поиск фрактала в {nero_path}...")
    nero_cols, fractal = load_nero_row(actual_time, nero_path)
    if nero_cols is None:
        print(f"  [!] Строка '{actual_time}' не найдена в Nero.csv")
        return

    d = build_dossier(actual_time, signal_row, nero_cols, fractal, params, updn_params_map=updn_params_map)
    print_dossier(d, params)


# ─── Batch Mode ─────────────────────────────────────────────────────────────

def batch_reconciliation(signals_path, nero_path, params, top_n, min_ratio, csv_out, updn_params_map=None):
    """Пакетный разбор: найти top_n сигналов с ratio >= min_ratio, создать досье."""
    print(f"[1] Загрузка сигналов из {signals_path} (min_ratio >= {min_ratio})...")
    signals = load_all_signals(signals_path, min_ratio)
    if not signals:
        print("  [!] Подходящих сигналов не найдено.")
        return

    # Сортировка по ratio desc, отрезаем top_n
    signals.sort(key=lambda x: x['_ratio'], reverse=True)
    signals = signals[:top_n]
    print(f"  Найдено {len(signals)} сигналов, анализируем top {len(signals)}...")

    # Собираем времена для batch-загрузки Nero
    target_times = {s['time'] for s in signals}
    print(f"[2] Загрузка фракталов из {nero_path} ({len(target_times)} записей)...")
    nero_data = load_nero_batch(target_times, nero_path)
    print(f"  Найдено совпадений: {len(nero_data)}")

    # Build dossiers
    dossiers = []
    for s in signals:
        t = s['time']
        nero_cols, fractal = nero_data.get(t, (None, None))
        d = build_dossier(t, s, nero_cols, fractal, params, updn_params_map=updn_params_map)
        dossiers.append(d)

    # Summary table
    print(f"\n{'='*100}")
    print(f"  BATCH RECONCILIATION (top {len(dossiers)}, ratio >= {min_ratio})")
    print(f"{'='*100}")

    header = f" {'#':>2} | {'Time':<18} | {'Dir':<4} | {'Ratio':>6} | {'SL(ATR)':>7} | {'TP(ATR)':>7} | {'Up_12':>8} | {'Dn_12':>8} | {'Result':<9} | {'Lag':>4}"
    print(header)
    print('-' * len(header))

    counts = {'TP_CLEAR': 0, 'SL_CLEAR': 0, 'BOTH_HIT': 0, 'TIMEOUT': 0, 'FLAT': 0}
    total_lag = 0.0
    lag_count = 0

    for i, d in enumerate(dossiers, 1):
        cat = d.get('category', '?')
        counts[cat] = counts.get(cat, 0) + 1

        sl_atr = f"{d.get('sl_atr', 0):.2f}" if 'sl_atr' in d else '?'
        tp_atr = f"{d.get('tp_atr', 0):.2f}" if 'tp_atr' in d else '?'
        up_12 = f"{d.get('up_12', 0):.5f}" if 'up_12' in d else '?'
        dn_12 = f"{d.get('dn_12', 0):.5f}" if 'dn_12' in d else '?'
        lag = d.get('lag_bars', 0)
        lag_str = f"{lag:.0f}h"
        if 'lag_bars' in d:
            total_lag += lag
            lag_count += 1

        print(f" {i:>2} | {d['time']:<18} | {d['direction']:<4} | {d['ratio']:>6.2f} | {sl_atr:>7} | {tp_atr:>7} | {up_12:>8} | {dn_12:>8} | {cat:<9} | {lag_str:>4}")

    # Summary
    print(f"\n  Итого: TP_CLEAR={counts['TP_CLEAR']}, SL_CLEAR={counts['SL_CLEAR']}, BOTH_HIT={counts['BOTH_HIT']}, TIMEOUT={counts['TIMEOUT']}")
    if lag_count > 0:
        print(f"  Средний lag: {total_lag/lag_count:.1f} бар(а)")

    # Full dossiers
    print(f"\n{'='*60}")
    print(f"  ДЕТАЛЬНЫЕ ДОСЬЕ")
    print(f"{'='*60}")
    for d in dossiers:
        print_dossier(d, params)

    # CSV export
    if csv_out:
        fieldnames = ['time', 'direction', 'signal', 'ratio', 'pred_up', 'pred_dn',
                       'ratio_up', 'ratio_dn', 'price', 'atr', 'sl_dist', 'tp_dist',
                       'sl_atr', 'tp_atr', 'sl_source', 'up_12', 'dn_12',
                       'category', 'lag_bars']
        with open(csv_out, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', extrasaction='ignore')
            writer.writeheader()
            for d in dossiers:
                writer.writerow(d)
        print(f"\n  CSV экспортирован: {csv_out}")


# ─── Main ────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Trade-level reconciliation: ML vs MT4 (Разбор полетов)")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--time", help="Время фрактала: 'YYYY.MM.DD HH:MM' (single-trace)")
    mode.add_argument("--batch", action='store_true', help="Пакетный анализ top-N сигналов")
    mode.add_argument("--from-log", metavar="LOG", help="Разбор реальных сделок из лога MT4 тестера")

    parser.add_argument("--losses-only", action='store_true', help="--from-log: только убыточные (SL)")
    parser.add_argument("--top", type=int, default=10, help="Кол-во сигналов в batch (default: 10)")
    parser.add_argument("--min-ratio", type=float, default=5.0, help="Мин. ratio для batch (default: 5.0)")
    parser.add_argument("--csv-out", help="Путь для CSV-экспорта результатов")

    parser.add_argument("--nero", nargs='+',
                        default=["DATA/Nero_train_labeled.csv",
                                 "DATA/Nero_validation_labeled.csv",
                                 "DATA/Nero_test_labeled.csv"],
                        help="Пути к Nero_*_labeled.csv (можно несколько)")
    parser.add_argument("--signals", default="MT/MQL4/Files/ml_signals.csv", help="Путь к ml_signals.csv")
    parser.add_argument("--ini", default="MT/tester/$o$imple.ini", help="Путь к $o$imple.ini")
    parser.add_argument("--stats", default=NORM_STATS_DEFAULT, help="Путь к Nero_normalization_stats.csv")

    # CLI overrides for ML params
    parser.add_argument("--ml-min-ratio", type=float, help="Override ML_MinRatio из ini")
    parser.add_argument("--ml-max-rr", type=float, help="Override ML_MaxRR из ini")
    parser.add_argument("--ml-scale-k", type=float, help="Override ML_ScaleK из ini")
    parser.add_argument("--ml-min-sl-atr", type=float, help="Override ML_Min_SL_ATR из ini")

    return parser.parse_args()


def load_params(args):
    """Загрузка параметров: defaults -> ini -> CLI overrides."""
    params = parse_ini(args.ini)
    if args.ml_min_ratio is not None:
        params['ML_MinRatio'] = args.ml_min_ratio
    if args.ml_max_rr is not None:
        params['ML_MaxRR'] = args.ml_max_rr
    if args.ml_scale_k is not None:
        params['ML_ScaleK'] = args.ml_scale_k
    if args.ml_min_sl_atr is not None:
        params['ML_Min_SL_ATR'] = args.ml_min_sl_atr
    return params


if __name__ == "__main__":
    args = parse_args()
    params = load_params(args)
    updn_params_map = load_updn_params()

    print(f"--- Параметры MT4 ---")
    for k, v in params.items():
        print(f"  {k} = {v}")
    print(f"  updn_params: {len(updn_params_map)} строк загружено")

    if args.from_log:
        from_log_reconciliation(args.from_log, args.signals, args.nero, params,
                                losses_only=args.losses_only, csv_out=args.csv_out,
                                updn_params_map=updn_params_map)
    elif args.batch:
        batch_reconciliation(args.signals, args.nero, params,
                             top_n=args.top, min_ratio=args.min_ratio,
                             csv_out=args.csv_out, updn_params_map=updn_params_map)
    else:
        trace_signal(args.time, args.nero, args.signals, params, updn_params_map=updn_params_map)
