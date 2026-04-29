# =============================================================================
# Файл: normalize.py
# Назначение: Модуль нормализации признаков для торговых данных
# Язык: Python 3.10+
# Автор: Antigravity
# Создан: 2026-02-07
# Обновлён: 2026-04-29
#
# Зависимости:
#   Входные данные:
#     - pd.DataFrame с колонками: time, signal, predict, ATR, fractal0..fractal99
#   Выходные данные:
#     - pd.DataFrame с нормализованными признаками
#     - {base}_atr_scaler.pkl (RobustScaler для ATR)
#     - {base}_normalization_stats.csv (статистика до нормализации)
#
# Внешние зависимости:
#   - pandas>=2.0.0
#   - numpy>=1.24.0
#   - scikit-learn>=1.3.0
#
# Использование:
#   from normalize import normalize_rowwise, normalize_atr_train, normalize_atr_inference
#   df = normalize_rowwise(df, stats_path="stats.csv", debug=True)
#   train_df = normalize_atr_train(train_df, scaler_path="atr_scaler.pkl")
#   val_df = normalize_atr_inference(val_df, scaler_path="atr_scaler.pkl")
#
# Примечания:
#   - Построчная нормализация (rowwise) независима для каждой строки — нет data leakage
#   - ATR нормализация глобальная — требует fit на train, transform на val/test
#   - Признаки direction и strong не нормализуются (уже в {-1,0,1})
#   - fractal_time исключается из нормализации (служебное поле)
#   - Legacy 18-польные фракталы поддерживаются: fractal_atr переносится в поле 21.
# =============================================================================

"""
Модуль нормализации признаков для event-driven time-series данных.

Реализует несколько методов нормализации:
- Piecewise Linear-Log: для признаков с тяжёлыми хвостами (front, back, predict, etc.)
- Min-Max: для price
- RobustScaler: для ATR (глобальная нормализация)

Структура фрактала (18 признаков):
    fractal_time:price:direction:front:back:strong:break:reverse:power:count:impulse:up_12:dn_12:up_24:dn_24:up_48:dn_48:fractal_atr
    [0]         :[1]  :[2]      :[3]  :[4] :[5]   :[6]  :[7]    :[8]  :[9]  :[10]  :[11] :[12] :[13] :[14] :[15] :[16] :[17]
"""

import numpy as np
import pandas as pd
import pickle
from sklearn.preprocessing import RobustScaler
from typing import Tuple, Optional, List

# Индексы признаков в строке фрактала
FRACTAL_INDICES = {
    'fractal_time': 0,
    'price': 1,
    'direction': 2,
    'front': 3,
    'back': 4,
    'strong': 5,
    'break': 6,
    'reverse': 7,
    'power': 8,
    'count': 9,
    'impulse': 10,
    'up_12': 11,
    'dn_12': 12,
    'up_24': 13,
    'dn_24': 14,
    'up_48': 15,
    'dn_48': 16,
    'fractal_atr': 21,
}

# Признаки для piecewise linear-log нормализации (раздельно)
PIECEWISE_SEPARATE = ['impulse', 'count', 'reverse', 'power', 'break']

# Признаки для совместной нормализации (общие параметры)
PIECEWISE_JOINT = ['front', 'back']  # + predict (отдельная колонка)

# Up/Dn поля для совместной piecewise нормализации (отдельный пул от front/back)
UPDN_FIELDS = ['up_12', 'dn_12', 'up_24', 'dn_24', 'up_48', 'dn_48']

# Row-level колонки-таргеты (нормализуются в том же пуле)
UPDN_TARGET_COLUMNS = ['up_3', 'dn_3', 'up_6', 'dn_6', 'up_12', 'dn_12', 'up_24', 'dn_24', 'up_48', 'dn_48']

# Признаки без нормализации
NO_NORMALIZE = ['direction', 'strong', 'fractal_time', 'fractal_atr']

# Параметры piecewise linear-log по умолчанию
DEFAULT_PIECEWISE_PARAMS = {
    'q_break': 0.85,      # точка перехода в лог-часть (85-й перцентиль)
    'q_cap': 0.99,        # cap для устойчивости хвоста (99-й перцентиль)
    'linear_max': 0.85,   # верх линейной части на шкале [0,1]
    'tail_strength': 9.0, # сила логарифмического сжатия
    'eps': 1e-12,
}


def parse_fractal(fractal_str: str) -> Optional[List[float]]:
    """
    Парсит строку фрактала в список значений.

    Args:
        fractal_str: Строка формата "T:P:Dir:Frnt:Back:Strong:Brk:Rev:Pwr:Cnt:Imp:Up12:Dn12:Up24:Dn24:Up48:Dn48:FractalAtr"

    Returns:
        Список из 18 float значений или None, если строка некорректна.
    """
    if pd.isna(fractal_str) or fractal_str == '':
        return None

    parts = str(fractal_str).split(':')
    if len(parts) < 18:
        return None

    try:
        values = [float(p) for p in parts[:22]] if len(parts) >= 22 else [float(p) for p in parts[:18]]
        if len(values) == 18:
            legacy_fractal_atr = values[17]
            values = values[:17] + [np.nan, np.nan, np.nan, np.nan, legacy_fractal_atr]
        return values
    except (ValueError, IndexError):
        return None


def fractal_to_string(values: np.ndarray) -> str:
    """
    Собирает массив значений обратно в строку фрактала.

    Args:
        values: Массив из 18 значений признаков фрактала.

    Returns:
        Строка формата "time:price:direction:...".
    """
    # fractal_time, direction, strong, count — целые числа
    int_indices = [0, 2, 5, 9]
    parts = []
    for i, v in enumerate(values):
        if i in int_indices:
            parts.append(str(int(round(v))))
        else:
            # Форматируем float без лишних нулей
            parts.append(f"{v:.10g}")
    return ':'.join(parts)


def parse_fractals_to_array(df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
    """
    Парсит все фракталы DataFrame в numpy array.

    Args:
        df: DataFrame с колонками fractal0, fractal1, ..., fractal99.

    Returns:
        Tuple:
            - numpy array shape (n_rows, n_fractals, 18)
            - список имён колонок фракталов
    """
    fractal_columns = sorted(
        [col for col in df.columns if col.startswith('fractal')],
        key=lambda x: int(x.replace('fractal', ''))
    )
    
    n_rows = len(df)
    n_fractals = len(fractal_columns)
    n_features = 22

    # Инициализируем массив NaN для обработки пустых фракталов
    result = np.full((n_rows, n_fractals, n_features), np.nan, dtype=np.float64)
    
    for i, row in df.iterrows():
        for j, col in enumerate(fractal_columns):
            parsed = parse_fractal(row[col])
            if parsed is not None:
                result[i, j, :] = parsed
    
    return result, fractal_columns


def array_to_fractal_strings(
    fractals: np.ndarray,
    df: pd.DataFrame,
    fractal_columns: List[str]
) -> pd.DataFrame:
    """
    Записывает numpy array обратно в DataFrame как строки фракталов.

    Args:
        fractals: Массив shape (n_rows, n_fractals, 18).
        df: Исходный DataFrame для модификации.
        fractal_columns: Список имён колонок фракталов.

    Returns:
        DataFrame с обновлёнными колонками фракталов.
    """
    df = df.copy()
    
    for i in range(len(df)):
        for j, col in enumerate(fractal_columns):
            if np.isnan(fractals[i, j, 0]):
                # Пустой фрактал — оставляем пустым
                df.at[i, col] = ''
            else:
                df.at[i, col] = fractal_to_string(fractals[i, j, :])
    
    return df


def piecewise_linear_log_transform(
    x: np.ndarray,
    lo: float,
    brk: float,
    cap: float,
    linear_max: float = 0.85,
    tail_strength: float = 9.0,
    eps: float = 1e-12
) -> np.ndarray:
    """
    Применяет piecewise linear-log трансформацию к массиву значений.

    Линейная часть: [lo, brk] -> [0, linear_max]
    Логарифмическая часть: (brk, cap] -> (linear_max, 1]

    Args:
        x: Входной массив значений.
        lo: Минимум (нижняя граница).
        brk: Точка перехода (break point).
        cap: Верхняя граница (cap).
        linear_max: Максимум линейной части (по умолчанию 0.85).
        tail_strength: Сила логарифмического сжатия (по умолчанию 9.0).
        eps: Малое число для защиты от деления на 0.

    Returns:
        Нормализованный массив в диапазоне [0, 1].
    """
    x = np.asarray(x, dtype=np.float64)
    
    # Линейная часть
    denom_lin = max(brk - lo, eps)
    y_lin = np.clip((x - lo) / denom_lin, 0.0, 1.0) * linear_max
    
    # Логарифмическая часть (хвост)
    denom_tail = max(cap - brk, eps)
    excess = np.maximum(x - brk, 0.0)
    t = np.clip(excess / denom_tail, 0.0, 1.0)
    log_part = np.log1p(tail_strength * t) / np.log1p(tail_strength + eps)
    y_tail = linear_max + (1.0 - linear_max) * log_part
    
    # Выбираем между линейной и логарифмической частью
    out = np.where(x <= brk, y_lin, y_tail)
    out = np.clip(out, 0.0, 1.0)
    out = np.where(np.isfinite(out), out, np.nan)
    
    return out.astype(np.float32)


def minmax_normalize(x: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """
    Min-Max нормализация в диапазон [0, 1].

    Args:
        x: Входной массив значений.
        eps: Малое число для защиты от деления на 0.

    Returns:
        Нормализованный массив. При вырожденном случае (max=min) возвращает 0.5.
    """
    x = np.asarray(x, dtype=np.float64)
    lo = np.nanmin(x)
    hi = np.nanmax(x)
    
    if hi - lo < eps:
        # Вырожденный случай: все значения одинаковы
        return np.full_like(x, 0.5, dtype=np.float32)
    
    result = (x - lo) / (hi - lo)
    return result.astype(np.float32)


def normalize_rowwise(
    df: pd.DataFrame,
    stats_path: Optional[str] = None,
    debug: bool = False,
    piecewise_params: Optional[dict] = None,
    return_updn_params: bool = False,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Выполняет построчную нормализацию всех признаков (кроме ATR).

    Каждая строка нормализуется независимо от других.
    
    Группы нормализации:
        - |predict| + front + back: совместная piecewise linear-log (общие параметры);
          знак predict сохраняется и восстанавливается после нормализации
        - impulse, count, reverse, power, break: раздельная piecewise linear-log
        - price: min-max [0, 1]
        - direction, strong: без изменений
        - fractal_time: без изменений

    Args:
        df: DataFrame с колонками predict, ATR, fractal0..fractal99.
        stats_path: Путь для сохранения статистики (опционально).
        debug: Флаг отладки для вывода примеров до/после.
        piecewise_params: Параметры piecewise linear-log (опционально).
        return_updn_params: Вернуть per-row параметры нормализации Up/Dn.
        verbose: Печатать progress в stdout. В runtime watcher используется False.

    Returns:
        DataFrame с нормализованными признаками.
    """
    if piecewise_params is None:
        piecewise_params = DEFAULT_PIECEWISE_PARAMS

    def log(message: str = "") -> None:
        if verbose:
            print(message)
    
    q_break = piecewise_params['q_break']
    q_cap = piecewise_params['q_cap']
    linear_max = piecewise_params['linear_max']
    tail_strength = piecewise_params['tail_strength']
    eps = piecewise_params['eps']
    
    log("\n" + "=" * 60)
    log("НОРМАЛИЗАЦИЯ ПРИЗНАКОВ (построчная)")
    log("=" * 60)
    
    # Парсим фракталы в numpy array
    log("\n[1/4] Парсинг фракталов в numpy array...")
    fractals, fractal_columns = parse_fractals_to_array(df)
    n_rows, n_fractals, n_features = fractals.shape
    log(f"      Shape: ({n_rows}, {n_fractals}, {n_features})")
    
    # Собираем статистику до нормализации
    if stats_path:
        log(f"\n[2/4] Сбор статистики до нормализации...")
        stats = collect_statistics(df, fractals)
        save_statistics(stats, stats_path)
        log(f"      Сохранено: {stats_path}")
    
    # Индексы признаков
    idx_front = FRACTAL_INDICES['front']
    idx_back = FRACTAL_INDICES['back']
    idx_price = FRACTAL_INDICES['price']
    
    # Копируем DataFrame и predict
    df = df.copy()
    predict_original = df['predict'].values.copy()
    predict_normalized = np.zeros_like(predict_original, dtype=np.float32)

    # Подготовка Up/Dn target columns для нормализации в общем пуле с фичами фракталов
    updn_targets = {}
    for col in UPDN_TARGET_COLUMNS:
        if col in df.columns:
            updn_targets[col] = df[col].values.copy().astype(np.float64)
        else:
            updn_targets[col] = np.zeros(n_rows, dtype=np.float64)

    # Массив для per-row параметров нормализации updn
    updn_params = np.zeros((n_rows, 2), dtype=np.float64)  # [brk, cap]
    
    # Логирование: сохраняем примеры до нормализации
    if debug:
        samples_before = []
        for i in range(min(3, n_rows)):
            samples_before.append({
                'predict': df.iloc[i]['predict'],
                'front': fractals[i, :3, idx_front].copy(),
                'back': fractals[i, :3, idx_back].copy(),
                'price': fractals[i, :3, idx_price].copy(),
            })
    
    log(f"\n[3/4] Нормализация строк...")
    
    for i in range(n_rows):
        # === 1. Совместная нормализация predict + front + back ===
        predict_val = predict_original[i]
        front_vals = fractals[i, :, idx_front]
        back_vals = fractals[i, :, idx_back]
        
        # predict может быть отрицательным (из-за target_direction в label_signals.py),
        # а front и back — всегда >= 0 (расстояния). Для корректного объединения
        # используем модуль predict, а после нормализации возвращаем знак.
        predict_sign = np.sign(predict_val) if np.isfinite(predict_val) else 1.0
        predict_abs = np.abs(predict_val)
        
        # Объединяем |predict| с front/back для расчёта общих параметров
        pooled = np.concatenate([[predict_abs], front_vals, back_vals])
        pooled_valid = pooled[np.isfinite(pooled)]
        
        if len(pooled_valid) > 0:
            lo = np.nanmin(pooled_valid)
            brk = np.nanpercentile(pooled_valid, q_break * 100)
            cap = np.nanpercentile(pooled_valid, q_cap * 100)
            brk = max(brk, lo + eps)
            cap = max(cap, brk + eps)
            
            # Нормализуем модуль predict и возвращаем знак
            predict_norm_abs = piecewise_linear_log_transform(
                predict_abs, lo, brk, cap, linear_max, tail_strength, eps
            )
            predict_normalized[i] = predict_norm_abs * predict_sign
            
            fractals[i, :, idx_front] = piecewise_linear_log_transform(
                front_vals, lo, brk, cap, linear_max, tail_strength, eps
            )
            fractals[i, :, idx_back] = piecewise_linear_log_transform(
                back_vals, lo, brk, cap, linear_max, tail_strength, eps
            )
        
        # === 2. Раздельная нормализация (impulse, count, reverse, power, break) ===
        for feat_name in PIECEWISE_SEPARATE:
            idx = FRACTAL_INDICES[feat_name]
            vals = fractals[i, :, idx]
            vals_valid = vals[np.isfinite(vals)]
            
            if len(vals_valid) > 0:
                lo = np.nanmin(vals_valid)
                brk = np.nanpercentile(vals_valid, q_break * 100)
                cap = np.nanpercentile(vals_valid, q_cap * 100)
                brk = max(brk, lo + eps)
                cap = max(cap, brk + eps)
                
                fractals[i, :, idx] = piecewise_linear_log_transform(
                    vals, lo, brk, cap, linear_max, tail_strength, eps
                )
        
        # === 3. Min-max нормализация price ===
        price_vals = fractals[i, :, idx_price]
        price_valid = price_vals[np.isfinite(price_vals)]

        if len(price_valid) > 0:
            fractals[i, :, idx_price] = minmax_normalize(price_vals, eps)

        # === 4. Joint piecewise нормализация Up/Dn (фичи + таргеты) ===
        updn_indices = [FRACTAL_INDICES[name] for name in UPDN_FIELDS]

        # 600 значений из фракталов + 6 значений из таргетов строки = 606
        updn_fractal_vals = fractals[i, :, updn_indices].flatten()
        updn_target_vals = np.array([updn_targets[col][i] for col in UPDN_TARGET_COLUMNS])
        updn_pool = np.concatenate([updn_fractal_vals, updn_target_vals])

        # Перцентили считаем по ненулевым (нули — "цена не двигалась" — не должны сдвигать p85)
        updn_valid = updn_pool[np.isfinite(updn_pool) & (updn_pool > 0)]

        if len(updn_valid) > 0:
            lo_updn = 0.0  # Up/Dn >= 0 всегда, нули останутся нулями
            brk_updn = np.nanpercentile(updn_valid, q_break * 100)
            cap_updn = np.nanpercentile(updn_valid, q_cap * 100)
            brk_updn = max(brk_updn, lo_updn + eps)
            cap_updn = max(cap_updn, brk_updn + eps)
            updn_params[i] = [brk_updn, cap_updn]

            # Нормализуем фичи фракталов (поля 11-16)
            for idx in updn_indices:
                fractals[i, :, idx] = piecewise_linear_log_transform(
                    fractals[i, :, idx], lo_updn, brk_updn, cap_updn,
                    linear_max, tail_strength, eps
                )

            # Нормализуем таргеты строки
            for col in UPDN_TARGET_COLUMNS:
                updn_targets[col][i] = piecewise_linear_log_transform(
                    np.array([updn_targets[col][i]]), lo_updn, brk_updn, cap_updn,
                    linear_max, tail_strength, eps
                )[0]

        # Прогресс
        if (i + 1) % 10000 == 0 or i == n_rows - 1:
            log(f"      Обработано: {i + 1}/{n_rows} строк")
    
    # Записываем нормализованный predict обратно
    df['predict'] = predict_normalized

    # Записываем нормализованные Up/Dn таргеты обратно
    for col in UPDN_TARGET_COLUMNS:
        if col in df.columns:
            df[col] = updn_targets[col].astype(np.float32)
    
    # Записываем фракталы обратно в DataFrame
    log(f"\n[4/4] Запись нормализованных фракталов...")
    df = array_to_fractal_strings(fractals, df, fractal_columns)
    
    # Логирование: примеры после нормализации
    if debug:
        log("\n" + "-" * 60)
        log("ПРИМЕРЫ НОРМАЛИЗАЦИИ (первые 3 строки)")
        log("-" * 60)
        
        for i in range(min(3, n_rows)):
            log(f"\n[Строка {i}]")
            log(f"  predict: {samples_before[i]['predict']:.6f} -> {df.iloc[i]['predict']:.6f}")
            
            # Парсим нормализованные фракталы для сравнения
            frac_norm = parse_fractal(df.iloc[i]['fractal0'])
            if frac_norm:
                log(f"  front[0]: {samples_before[i]['front'][0]:.6f} -> {frac_norm[idx_front]:.6f}")
                log(f"  back[0]:  {samples_before[i]['back'][0]:.6f} -> {frac_norm[idx_back]:.6f}")
                log(f"  price[0]: {samples_before[i]['price'][0]:.6f} -> {frac_norm[idx_price]:.6f}")
    
    log(f"\n[ГОТОВО] Построчная нормализация завершена")

    if return_updn_params:
        return df, updn_params
    return df


def collect_statistics(df: pd.DataFrame, fractals: np.ndarray) -> dict:
    """
    Собирает статистику признаков до нормализации.

    Args:
        df: DataFrame с колонкой predict.
        fractals: Numpy array фракталов shape (n_rows, n_fractals, 18).

    Returns:
        Словарь со статистикой по каждому признаку.
    """
    stats = {}
    
    # Статистика predict
    predict_vals = df['predict'].values
    predict_valid = predict_vals[np.isfinite(predict_vals)]
    if len(predict_valid) > 0:
        stats['predict'] = {
            'min': float(np.min(predict_valid)),
            'max': float(np.max(predict_valid)),
            'p25': float(np.percentile(predict_valid, 25)),
            'p50': float(np.percentile(predict_valid, 50)),
            'p75': float(np.percentile(predict_valid, 75)),
            'p85': float(np.percentile(predict_valid, 85)),
            'p99': float(np.percentile(predict_valid, 99)),
        }
    
    # Статистика ATR (если есть)
    if 'ATR' in df.columns:
        atr_vals = df['ATR'].values
        atr_valid = atr_vals[np.isfinite(atr_vals)]
        if len(atr_valid) > 0:
            stats['ATR'] = {
                'min': float(np.min(atr_valid)),
                'max': float(np.max(atr_valid)),
                'p25': float(np.percentile(atr_valid, 25)),
                'p50': float(np.percentile(atr_valid, 50)),
                'p75': float(np.percentile(atr_valid, 75)),
                'p85': float(np.percentile(atr_valid, 85)),
                'p99': float(np.percentile(atr_valid, 99)),
            }
    
    # Статистика признаков фракталов
    feature_names = list(FRACTAL_INDICES.keys())
    for feat_name, idx in FRACTAL_INDICES.items():
        if feat_name in NO_NORMALIZE:
            continue
        
        vals = fractals[:, :, idx].flatten()
        vals_valid = vals[np.isfinite(vals)]
        
        if len(vals_valid) > 0:
            stats[feat_name] = {
                'min': float(np.min(vals_valid)),
                'max': float(np.max(vals_valid)),
                'p25': float(np.percentile(vals_valid, 25)),
                'p50': float(np.percentile(vals_valid, 50)),
                'p75': float(np.percentile(vals_valid, 75)),
                'p85': float(np.percentile(vals_valid, 85)),
                'p99': float(np.percentile(vals_valid, 99)),
            }
    
    return stats


def save_statistics(stats: dict, path: str) -> None:
    """
    Сохраняет статистику в CSV файл.

    Args:
        stats: Словарь со статистикой.
        path: Путь к файлу.
    """
    rows = []
    for feat_name, feat_stats in stats.items():
        row = {'feature': feat_name}
        row.update(feat_stats)
        rows.append(row)
    
    stats_df = pd.DataFrame(rows)
    stats_df.to_csv(path, index=False)


def normalize_atr_train(
    df: pd.DataFrame,
    scaler_path: str
) -> pd.DataFrame:
    """
    Нормализует ATR на train данных (fit + transform).

    Использует RobustScaler для устойчивости к выбросам.
    Сохраняет обученный scaler в файл.

    Args:
        df: DataFrame с колонкой ATR.
        scaler_path: Путь для сохранения scaler.

    Returns:
        DataFrame с нормализованным ATR.
    """
    print("\n[ATR] Нормализация train (fit + transform)...")
    
    df = df.copy()
    scaler = RobustScaler()
    
    atr_values = df[['ATR']].values
    atr_normalized = scaler.fit_transform(atr_values)
    df['ATR'] = atr_normalized.flatten()
    
    # Сохраняем scaler
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    
    print(f"      Median (center): {scaler.center_[0]:.6f}")
    print(f"      IQR (scale): {scaler.scale_[0]:.6f}")
    print(f"      Scaler сохранён: {scaler_path}")
    
    return df


def normalize_atr_inference(
    df: pd.DataFrame,
    scaler_path: str
) -> pd.DataFrame:
    """
    Нормализует ATR на val/test данных (только transform).

    Использует ранее обученный scaler из файла.

    Args:
        df: DataFrame с колонкой ATR.
        scaler_path: Путь к сохранённому scaler.

    Returns:
        DataFrame с нормализованным ATR.
    """
    print(f"\n[ATR] Нормализация inference (transform only)...")
    
    df = df.copy()
    
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    
    atr_values = df[['ATR']].values
    atr_normalized = scaler.transform(atr_values)
    df['ATR'] = atr_normalized.flatten()
    
    print(f"      Применён scaler из: {scaler_path}")
    
    return df


if __name__ == "__main__":
    # Пример использования модуля при прямом запуске
    print("Модуль normalize.py")
    print("Используйте: from normalize import normalize_rowwise, normalize_atr_train")
