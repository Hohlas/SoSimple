#!/usr/bin/env python3
"""
Утилита денормализации предсказаний up/dn из [0,1] обратно в ATR-единицы (пункты).

Использует per-row per-pair параметры нормализации (brk, cap),
сохранённые `label_main.py` как `*_updn_params.npy` (shape: N, 5, 2).

Нормализация выполнялась через `piecewise_linear_log_transform`,
обратное преобразование — `inverse_piecewise_linear_log`.
Параметры `linear_max` и `tail_strength` должны совпадать с нормализацией
(DEFAULT_PIECEWISE_PARAMS в normalize.py).
"""

import os
import math
import numpy as np

# Должны совпадать с DEFAULT_PIECEWISE_PARAMS в normalize.py
_LINEAR_MAX = 0.85
_TAIL_STRENGTH = 9.0

# Должны совпадать с UPDN_PAIRS в normalize.py
UPDN_PAIR_NAMES = [
    ('up_3', 'dn_3'),
    ('up_6', 'dn_6'),
    ('up_12', 'dn_12'),
    ('up_24', 'dn_24'),
    ('up_48', 'dn_48'),
]


def inverse_piecewise_linear_log(y, brk, cap,
                                  linear_max=_LINEAR_MAX,
                                  tail_strength=_TAIL_STRENGTH):
    """Обратное piecewise_linear_log_transform → исходное значение в пунктах.

    Прямое преобразование (из normalize.py):
      y_lin = x / brk * linear_max                    [0, brk) → [0, linear_max)
      y_tail = linear_max + (1-linear_max) * log1p(s·t) / log1p(s)   [brk, cap] → [linear_max, 1]
      где t = (x − brk) / (cap − brk), s = tail_strength

    Обратное:
      y ≤ 0       → 0
      y ≤ linear_max → y / linear_max * brk
      y > linear_max → brk + t_recovered * (cap − brk)
        где t = (expm1((y−linear_max)/(1−linear_max) * log1p(s))) / s

    Args:
        y: нормализованное значение в [0, 1] (скаляр или массив)
        brk: breakpoint — p85 ненулевых значений пары
        cap: cap — p99 ненулевых значений пары
        linear_max: верх линейной части (default: 0.85)
        tail_strength: сила логарифмического сжатия (default: 9.0)

    Returns:
        Денормализованное значение в исходном масштабе (пункты ATR)
    """
    y = np.asarray(y, dtype=np.float64)
    result = np.zeros_like(y)

    # Линейная часть: y ≤ linear_max
    linear_mask = (y > 0) & (y <= linear_max)
    result[linear_mask] = y[linear_mask] / linear_max * brk

    # Логарифмическая часть: y > linear_max
    tail_mask = y > linear_max
    if np.any(tail_mask):
        log_denom = math.log1p(tail_strength)
        t_log = (y[tail_mask] - linear_max) / (1.0 - linear_max)
        t = np.expm1(t_log * log_denom) / tail_strength
        t = np.clip(t, 0.0, 1.0)
        result[tail_mask] = brk + t * (cap - brk)

    if result.ndim == 0:
        return float(result)
    return result


def denormalize_updn(y_norm, brk, cap):
    """Денормализация одного или нескольких значений up/dn.

    Args:
        y_norm: нормализованное значение [0,1] (скаляр или массив)
        brk: per-row per-pair breakpoint (p85)
        cap: per-row per-pair cap (p99)

    Returns:
        Денормализованное значение в ATR-единицах
    """
    return inverse_piecewise_linear_log(np.asarray(y_norm, dtype=np.float64),
                                        brk, cap)


def denormalize_updn_pairs(y_norm_10, updn_params_row):
    """Денормализация всех 10 значений up/dn с per-pair brk/cap.

    Args:
        y_norm_10: array-like из 10 нормализованных значений
            в порядке [up_3, dn_3, up_6, dn_6, up_12, dn_12, up_24, dn_24, up_48, dn_48]
        updn_params_row: array-like shape (5, 2) — per-pair [brk, cap]

    Returns:
        np.ndarray из 10 денормализованных значений в ATR-единицах
    """
    y_norm_10 = np.asarray(y_norm_10, dtype=np.float64)
    updn_params_row = np.asarray(updn_params_row, dtype=np.float64)

    if y_norm_10.shape[-1] != 2 * len(UPDN_PAIR_NAMES):
        raise ValueError(
            f"y_norm_10 ожидается {2 * len(UPDN_PAIR_NAMES)} значений для "
            f"{len(UPDN_PAIR_NAMES)} пар, получено {y_norm_10.shape[-1]}"
        )

    result = np.zeros(len(y_norm_10), dtype=np.float64)
    for pair_idx in range(len(UPDN_PAIR_NAMES)):
        brk, cap = updn_params_row[pair_idx]
        result[2 * pair_idx] = inverse_piecewise_linear_log(
            y_norm_10[2 * pair_idx], brk, cap)
        result[2 * pair_idx + 1] = inverse_piecewise_linear_log(
            y_norm_10[2 * pair_idx + 1], brk, cap)
    return result


def denormalize_updn_legacy(y_norm_6, brk, cap):
    """Денормализация 6 значений up_12..dn_48 (старый формат, 3 пары).

    Сохранена для обратной совместимости с signal_tracer.
    Новый код должен использовать denormalize_updn_pairs().

    Args:
        y_norm_6: 6 нормализованных значений [up_12, dn_12, ..., dn_48]
        brk: единый breakpoint (исторически — p85 пары up_12/dn_12)
        cap: единый cap

    Returns:
        np.ndarray из 6 денормализованных значений в ATR-единицах
    """
    return inverse_piecewise_linear_log(
        np.asarray(y_norm_6, dtype=np.float64), brk, cap)


def load_updn_params(npy_path):
    """Загрузка per-row updn_params из .npy файла.

    Args:
        npy_path: путь к *_updn_params.npy

    Returns:
        np.ndarray shape (N, 5, 2) — per-pair [brk, cap] для каждой строки
    """
    if not os.path.exists(npy_path):
        raise FileNotFoundError(f"updn_params не найден: {npy_path}")
    arr = np.load(npy_path)
    if arr.ndim != 3 or arr.shape[1:] != (len(UPDN_PAIR_NAMES), 2):
        raise ValueError(
            f"updn_params неожиданной формы {arr.shape}, "
            f"ожидается (N, {len(UPDN_PAIR_NAMES)}, 2). "
            f"Перегенерируйте данные через label_main.py"
        )
    return arr


def load_updn_params_by_time(npy_path, csv_path):
    """Загрузка updn_params с индексацией по времени из CSV.

    Args:
        npy_path: путь к *_updn_params.npy
        csv_path: путь к соответствующему CSV (для time-ключа)

    Returns:
        dict {time_str: np.ndarray shape (5,2)} — brk/cap для всех 5 пар
    """
    params_arr = load_updn_params(npy_path)
    time_to_params = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        f.readline()  # header
        for i, line in enumerate(f):
            if i >= len(params_arr):
                break
            t = line[:16]  # 'YYYY.MM.DD HH:MM'
            time_to_params[t] = params_arr[i]
    return time_to_params
