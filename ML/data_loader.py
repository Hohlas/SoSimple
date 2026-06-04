# =============================================================================
# Файл: data_loader.py
# Назначение: Dataset и DataLoader для фрактальных последовательностей с кэшированием тензоров
# Язык: Python 3.11+
# Обновлён: 2026-04-19
# Зависимости:
#   Входные данные:
#     - DATA/Nero_train_labeled.csv (откуда: processing/label_main.py)
#     - DATA/Nero_validation_labeled.csv (откуда: processing/label_main.py)
#   Выходные данные:
#     - (in-memory Dataset/DataLoader)
#     - Кэш NumPy массивов: DATA/X_*.npy, DATA/mask_*.npy, DATA/y_*.npy
# Внешние зависимости:
#   - torch>=2.0
#   - pandas>=2.0
#   - numpy>=1.24
#   - scikit-learn>=1.2
# Использование:
#   from ML.data_loader import create_data_loaders
# Примечания:
#   - fractal_time (индекс 0) исключается из features, но используется для вычисления time-фич
#   - N_RAW_FEATURES=23: полный формат фрактала (fractal_v24_raw_price, без обратной совместимости)
#   - N_FRACTAL_FEATURES=26: 20 входных полей (fields 1-20) + ATR_ratio + 3 time-фичи + 2 shift-фичи; форма X: (n, 100, 26)
#   - UPDN_TARGETS: ['up_3','dn_3','up_6','dn_6','up_12','dn_12','up_24','dn_24','up_48','dn_48']
#   - StandardScaler fit на train, transform на val
#   - При первой загрузке данные кэшируются в .npy файлы для быстрого старта
#   - Для entry_path_v1 кэш инженерных признаков разделяется по feature profile
# =============================================================================

"""
Dataset и DataLoader для фрактальных последовательностей.

Парсит CSV с фракталами в 3D тензоры (n_samples, 100, 26),
исключает fractal_time как сырое поле, вычисляет time-фичи (hour_sin, hour_cos, time_pos),
добавляет ATR_ratio, нормализует features.
Создаёт padding mask для Transformer (NaN позиции).
"""

import random
from pathlib import Path

import numpy as np
import pandas as pd
import json as _json
import torch
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from sklearn.preprocessing import StandardScaler

from ML.entry_path_task import (
    ENTRY_PATH_ALLOWED_SEQUENCE_LENGTHS,
    ENTRY_PATH_DEFAULT_FEATURE_PROFILE,
    ENTRY_PATH_TARGET,
    ENTRY_PATH_REG_TARGETS,
    ENTRY_PATH_V1_FEATURE_COLUMNS,
    split_entry_path_features,
    split_entry_path_targets,
    validate_entry_path_feature_profile,
)
from ML.entry_path_v1_quantile_task import ENTRY_PATH_V1_QUANTILE_TARGET
from ML.multi_scale_fractal_features import build_multi_scale_fractal_features
from ML.take_skip_trailing_stop_task import (
    TAKE_SKIP_TRAILING_STOP_TARGET,
    split_take_skip_targets,
)
from ML.take_skip_trailing_stop_v2_task import (
    TAKE_SKIP_TRAILING_STOP_V2_TARGET,
    TAKE_SKIP_TRAILING_STOP_V2_COLUMNS,
    TAKE_SKIP_V2_ROW_FEATURE_COLUMNS,
    split_take_skip_v2_targets,
)
from ML.trailing_stop_target_quantile_task import (
    TRAILING_STOP_TARGET_QUANTILE_TARGET,
    split_trailing_stop_quantile_target,
)
from ML.trailing_stop_target_task import (
    TRAILING_STOP_TARGET,
    TRAILING_STOP_TARGET_COLUMNS,
    split_trailing_stop_targets,
)


# ─── Константы ───────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'DATA'

TRAIN_FILE = DATA_DIR / 'Nero_train_labeled.csv'
VAL_FILE = DATA_DIR / 'Nero_validation_labeled.csv'
TEST_FILE = DATA_DIR / 'Nero_test_labeled.csv'

CSV_SEP = ';'
FRACTAL_SEP = ':'
N_FRACTALS = 100
N_RAW_FEATURES = 23   # T:P:Dir:FrntVal:BackVal:Strong:Brk:Rev:PwrSum:Cnt:Imp:Up12:Dn12:Up24:Dn24:Up48:Dn48:Up3:Dn3:Up6:Dn6:FractalAtr:Shift
FRACTAL_ATR_RAW_IDX = 21  # fractal_atr в 23-полевом CSV
N_FRACTAL_FEATURES = 26  # 20 исходных (fields 1-20) + ATR_ratio + 3 time-фичи + log_shift + log_delta_shift
SHIFT_IDX = 22  # shift в 23-полевом CSV
DATA_VERSION = 'fractal_v24_raw_price'  # текущая версия формата фрактала

# Индекс fractal_time в сырых данных (исключается как сырое, но используется для time-фич)
FRACTAL_TIME_IDX = 0

# Индексы вычисляемых features в X (N_FRACTAL_FEATURES=26)
ATR_RATIO_IDX = 20       # fractal_atr → ATR_ratio (in-place)
TIME_FEAT_HOUR_SIN = 21   # sin(2π · hour / 24)
TIME_FEAT_HOUR_COS = 22   # cos(2π · hour / 24)
TIME_FEAT_TIME_POS = 23   # позиция на временной оси строки [0..1]
TIME_FEAT_LOG_SHIFT = 24  # log1p(shift) — возраст фрактала в барах
TIME_FEAT_LOG_DELTA_SHIFT = 25  # log1p(delta_shift) — временной зазор до соседа

SCHEMA_DIR = Path(__file__).resolve().parent.parent / 'docs' / 'schemas'

def _schema_path() -> Path:
    """Возвращает путь к schema-файлу, соответствующий текущему DATA_VERSION."""
    return SCHEMA_DIR / f'{DATA_VERSION}.schema.json'

SCHEMA_FILE = _schema_path()


def load_schema(schema_path: Path = SCHEMA_FILE) -> dict:
    if not schema_path.exists():
        raise FileNotFoundError(
            f'Файл схемы не найден: {schema_path}\n'
            f'  Убедись, что schema-файл существует в docs/schemas/'
        )
    with open(schema_path) as f:
        return _json.load(f)


def validate_data_contract(
    df: pd.DataFrame,
    source: str = '',
    schema_path: Path = SCHEMA_FILE,
    sample_size: int = 100,
) -> None:
    schema = load_schema(schema_path)
    schema_version = schema['version']
    price_scale = schema['price_scale']
    fractal_cfg = schema['fractal']
    csv_cfg = schema['csv']
    num_fields = fractal_cfg['num_fields']

    errors = []

    # 1. CSV columns
    actual_cols = set(df.columns)
    required = set(csv_cfg['required_columns'])
    missing = required - actual_cols
    if missing:
        errors.append(f'Отсутствуют обязательные колонки CSV: {sorted(missing)}')

    expected_fractals = [
        f"{csv_cfg['required_fractal_columns']['prefix']}{i}"
        for i in range(csv_cfg['required_fractal_columns']['count'])
    ]
    missing_fractals = [c for c in expected_fractals if c not in actual_cols]
    if missing_fractals:
        errors.append(
            f'Отсутствуют fractal-колонки (первые 5): {missing_fractals[:5]}'
            f'{f" ... и ещё {len(missing_fractals) - 5}" if len(missing_fractals) > 5 else ""}'
        )

    # 2. Fractal field count and domain — sample проверка
    sample = df['fractal0'].dropna().head(sample_size)
    if len(sample) == 0:
        errors.append('Колонка fractal0 пуста или содержит только NaN')

    field_errors_by_idx = {}
    for raw in sample:
        parts = str(raw).split(fractal_cfg['separator'])
        if len(parts) != num_fields:
            errors.append(
                f'Неверное число полей фрактала: ожидается {num_fields}, '
                f'найдено {len(parts)}. Строка: {str(raw)[:80]}...'
            )
            break  # достаточно одного примера

        for fdef in fractal_cfg['fields']:
            idx = fdef['index']
            name = fdef['name']
            ftype = fdef['type']
            domain = fdef['domain']

            try:
                if ftype == 'int':
                    v = int(parts[idx])
                else:
                    v = float(parts[idx])
            except (ValueError, IndexError):
                if idx not in field_errors_by_idx:
                    field_errors_by_idx[idx] = (
                        f'[{idx}] {name}: значение "{parts[idx] if idx < len(parts) else "MISSING"}" '
                        f'не конвертируется в {ftype}'
                    )
                continue

            # Проверка домена интерпретируется здесь
            # Простая проверка на основе domain-строки
            ok = _check_domain(v, domain)
            if not ok and idx not in field_errors_by_idx:
                field_errors_by_idx[idx] = f'[{idx}] {name}={v} нарушает домен: {domain}'

    if field_errors_by_idx:
        for e in sorted(field_errors_by_idx.values())[:5]:
            errors.append(e)
        if len(field_errors_by_idx) > 5:
            errors.append(f'... и ещё {len(field_errors_by_idx) - 5} нарушений')

    # 3. Price scale check: для normalized — цена должна быть в (0, 1]
    if price_scale == 'normalized' and 'fractal0' in df.columns:
        price_vals = []
        for raw in df['fractal0'].dropna().head(sample_size):
            parts = str(raw).split(fractal_cfg['separator'])
            try:
                price_vals.append(float(parts[1]))
            except (ValueError, IndexError):
                pass
        if price_vals:
            p_min, p_max = min(price_vals), max(price_vals)
            if p_max > 1.0 or p_min < 0.0:
                errors.append(
                    f'Цена выходит за нормализованный диапазон [0, 1]: '
                    f'min={p_min:.4f}, max={p_max:.4f}. '
                    f'Возможно, данные уже в raw-формате, а схема ожидает normalized.'
                )

    if errors:
        raise ValueError(
            f'\n[validate_data_contract] ОШИБКА КОНТРАКТА ДАННЫХ '
            f'(источник: {source}, версия схемы: {schema_version}):\n'
            + '\n'.join(f'  ✗ {e}' for e in errors)
            + f'\n\n  Ожидаемый формат: {num_fields} полей во фрактале (см. {schema_path})'
            + f'\n  Проверь lib_PIC.mqh (NERO_CSV_CREATE) и N_RAW_FEATURES в data_loader.py'
            + f'\n  Выполнение остановлено.'
        )

    print(
        f'  ✅ validate_data_contract: OK ({source}) | '
        f'версия={schema_version} | price_scale={price_scale} | '
        f'{num_fields} полей | {len(sample)} фракталов проверено'
    )


def _check_domain(value: float, domain: str) -> bool:
    """Простой интерпретатор доменных выражений."""
    import re
    v = float(value)
    d = domain.strip()

    # "{a, b}" — множество
    m_set = re.match(r'^{\s*([^}]+)\s*}$', d)
    if m_set:
        allowed = {float(x.strip()) for x in m_set.group(1).split(',')}
        return v in allowed

    # "> N" / ">= N"
    if d.startswith('>='):
        return v >= float(d[2:].strip())
    if d.startswith('>'):
        return v > float(d[1:].strip())
    if d.startswith('<='):
        return v <= float(d[2:].strip())
    if d.startswith('<'):
        return v < float(d[1:].strip())

    # "(a, b]" / "[a, b]" / etc.
    m_range = re.match(r'^[\[\(](\d+\.?\d*)\s*,\s*(\d+\.?\d*)[\]\)]$', d)
    if m_range:
        lo, hi = float(m_range.group(1)), float(m_range.group(2))
        left_ok = v >= lo if d.startswith('[') else v > lo
        right_ok = v <= hi if d.endswith(']') else v < hi
        return left_ok and right_ok

    return True  # неизвестный домен — пропускаем


# ─── Ожидаемые колонки CSV (контракт с MQL4) ─────────────────────────────────

EXPECTED_CSV_COLUMNS = ['time', 'signal', 'predict', 'ATR'] + [f'fractal{i}' for i in range(N_FRACTALS)]

# Доменные ограничения для каждого поля строки фрактала [индекс]: (название, тип, проверка, описание)
FRACTAL_FIELD_SCHEMA = [
    (0,  'time',        'int',   lambda v: v > 0,          'timestamp > 0'),
    (1,  'price',       'float', lambda v: v > 0,          'price > 0'),
    (2,  'direction',   'int',   lambda v: v in (-1, 1),   'direction ∈ {-1, 1}'),
    (5,  'strong',      'int',   lambda v: v in (0, 1),    'strong ∈ {0, 1}'),
    (6,  'break',       'int',   lambda v: v in (0, 1),    'break ∈ {0, 1}'),
    (11, 'up_12',       'float', lambda v: v >= 0,         'up_12 >= 0'),
    (16, 'dn_48',       'float', lambda v: v >= 0,         'dn_48 >= 0'),
    (17, 'up_3',        'float', lambda v: v >= 0,         'up_3 >= 0'),
    (19, 'up_6',        'float', lambda v: v >= 0,         'up_6 >= 0'),
    (21, 'fractal_atr', 'float', lambda v: v > 0,          'fractal_atr > 0'),
    (22, 'shift',       'int',   lambda v: v >= 0,         'shift >= 0'),
]


def validate_fractal_format(df: pd.DataFrame, source: str = '', sample_size: int = 50) -> None:
    col = 'fractal0'
    if col not in df.columns:
        raise ValueError(
            f'\n[validate_fractal_format] ОШИБКА ({source}): колонка {col} не найдена'
        )

    sample = df[col].dropna().head(sample_size)
    errors = []

    for raw in sample:
        parts = str(raw).split(FRACTAL_SEP)
        # 1. Количество полей
        if len(parts) != N_RAW_FEATURES:
            errors.append(
                f"Ожидается {N_RAW_FEATURES} полей (версия {DATA_VERSION}), "
                f"найдено {len(parts)}: '{raw[:60]}...'"
            )
            break  # достаточно одного примера

        # 2. Типы и доменные значения
        for idx, name, kind, check, desc in FRACTAL_FIELD_SCHEMA:
            try:
                v = int(parts[idx]) if kind == 'int' else float(parts[idx])
                if not check(v):
                    errors.append(f"[{idx}] {name}={v} нарушает: {desc}")
            except (ValueError, IndexError):
                errors.append(f"[{idx}] {name}='{parts[idx]}' не является {kind}")

    if errors:
        raise ValueError(
            f'\n[validate_fractal_format] ОШИБКА ФОРМАТА ФРАКТАЛА ({source}):\n'
            + '\n'.join(f'  ✗ {e}' for e in errors[:5])
            + (f'\n  ... и ещё {len(errors) - 5} ошибок' if len(errors) > 5 else '')
            + f'\n\n  Проверь N_RAW_FEATURES={N_RAW_FEATURES} и NERO_CSV_CREATE в lib_PIC.mqh'
        )
    else:
        print(f"  ✅ validate_fractal_format: OK ({source}) | {N_RAW_FEATURES} полей | типы верны")


def validate_csv_columns(df: pd.DataFrame, source: str = '') -> None:
    actual = set(df.columns)
    expected = set(EXPECTED_CSV_COLUMNS)
    removed = expected - actual  # добавленные колонки — нормально (label_main добавляет свои)
    if removed:
        lines = [f"[validate_csv_columns] ПРЕДУПРЕЖДЕНИЕ — ожидаемые колонки отсутствуют ({source})"]
        lines.append(f"  - Отсутствуют: {sorted(removed)}")
        lines.append("  → Проверь формат Nero.csv и EXPECTED_CSV_COLUMNS в data_loader.py")
        print('\n'.join(lines))
    else:
        print(f"  ✅ validate_csv_columns: OK ({source})")


def validate_parsed_features(X: np.ndarray, mask: np.ndarray, source: str = '') -> None:
    valid = X[mask]
    if len(valid) == 0:
        raise ValueError(f"validate_parsed_features ({source}): нет валидных фракталов вообще")

    checks = {
        "Слишком мало валидных фракталов (< 20%)": mask.mean() < 0.20,
        "Все значения нулевые — парсер сломан":    float((valid == 0).all()),
        "ATR мёртв (std < 0.01)":                  valid[:, ATR_RATIO_IDX].std() < 0.01,
        "price мёртв (std < 0.01)":                valid[:, 0].std() < 0.01,
        "back мёртв (все нули)":                   float((valid[:, 3] == 0).all()),
    }
    failed = [msg for msg, cond in checks.items() if cond]
    if failed:
        raise ValueError(
            f"validate_parsed_features FAILED ({source}):\n" +
            "\n".join(f"  ✗ {m}" for m in failed) +
            f"\n\n  Подсказка: проверь N_RAW_FEATURES={N_RAW_FEATURES} и "
            f"FRACTAL_ATR_RAW_IDX={FRACTAL_ATR_RAW_IDX} — "
            f"совпадает ли формат Nero.csv?"
        )
    print(
        f"  ✅ validate_parsed_features: OK ({source}) | "
        f"valid={mask.mean():.1%} | "
        f"ATR std={valid[:, ATR_RATIO_IDX].std():.3f} | "
        f"price std={valid[:, 0].std():.3f}"
    )


# ─── Парсинг данных ──────────────────────────────────────────────────────────

def parse_fractals_to_3d(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """
    Векторизованный парсинг фракталов в 3D тензор + padding mask.

    Парсит колонки fractal0..fractal99 из DataFrame.
    Исключает fractal_time (индекс 0) из features.
    Требуется ровно N_RAW_FEATURES=23 поля на фрактал; несовпадение — ошибка.

    Аргументы:
        df: DataFrame с колонками fractal0..fractal99, ATR, signal

    Возвращает:
        Кортеж (X, mask):
        - X: np.ndarray shape (n_samples, 100, 26) — 26 features per fractal.
             Feature order: price, direction, front, back, strong, break,
             reverse, power, count, impulse, up_12, dn_12, up_24, dn_24,
             up_48, dn_48, up_3, dn_3, up_6, dn_6,
             ATR_ratio, hour_sin, hour_cos, time_pos, log_shift, log_delta_shift
        - mask: np.ndarray shape (n_samples, 100) — True для валидных позиций,
                False для padding (все features == 0)
    """
    fractal_cols = [f'fractal{i}' for i in range(N_FRACTALS)]
    n_samples = len(df)

    # 26 features: CSV fields 1-20 plus ATR_ratio + 3 time-фичи + log_shift + log_delta_shift.
    n_features = N_FRACTAL_FEATURES
    X = np.zeros((n_samples, N_FRACTALS, n_features), dtype=np.float32)
    # Маска валидности: True если фрактал присутствует (не все NaN)
    raw_valid = np.ones((n_samples, N_FRACTALS), dtype=bool)
    # Хранилище fractal_time и shift для вычисления time-фич
    fractal_times = np.zeros((n_samples, N_FRACTALS), dtype=np.float64)
    shifts = np.zeros((n_samples, N_FRACTALS), dtype=np.float64)

    for j, col in enumerate(fractal_cols):
        if j % 20 == 0:
            print(f"    парсинг fractal columns {j}-{min(j + 19, N_FRACTALS - 1)}...")

        series = df[col].astype(str)
        split = series.str.split(FRACTAL_SEP, expand=True)

        if split.shape[1] != N_RAW_FEATURES:
            raise ValueError(
                f'parse_fractals_to_3d: колонка {col} содержит {split.shape[1]} полей, '
                f'ожидается ровно {N_RAW_FEATURES} (версия {DATA_VERSION}). '
                f'Проверь NERO_CSV_CREATE в lib_PIC.mqh.'
            )
        for k in range(N_RAW_FEATURES):
            if k == FRACTAL_TIME_IDX:
                vals = pd.to_numeric(split[k], errors='coerce')
                fractal_times[:, j] = vals.fillna(0).values
                continue
            if k == SHIFT_IDX:
                vals = pd.to_numeric(split[k], errors='coerce')
                shifts[:, j] = vals.fillna(0).values
                continue
            # k=1..20 → feat_idx=0..19; k=21 (fractal_atr) → feat_idx=ATR_RATIO_IDX
            feat_idx = k - 1 if k < FRACTAL_ATR_RAW_IDX else ATR_RATIO_IDX
            vals = pd.to_numeric(split[k], errors='coerce')
            X[:, j, feat_idx] = vals.fillna(0).values

        # Определяем padding: если все features после парсинга NaN
        all_nan = split.iloc[:, 1:].apply(
            lambda col_s: pd.to_numeric(col_s, errors='coerce')
        ).isna().all(axis=1)
        raw_valid[:, j] = ~all_nan.values

    # ATR_ratio = log(fractal_atr / Atr.Slow) — log-transform сжимает выбросы
    # fractal_atr уже в X[:,:,20] (ATR_RATIO_IDX), ATR — сырое (без RobustScaler)
    atr_slow = pd.to_numeric(df['ATR'], errors='coerce').fillna(1.0).values.astype(np.float32)
    denom = np.where(atr_slow > 0, atr_slow, 1.0)
    ratio = X[:, :, ATR_RATIO_IDX] / denom[:, np.newaxis]
    ratio = np.clip(ratio, 1e-6, None)  # защита от log(0)
    X[:, :, ATR_RATIO_IDX] = np.log(ratio)

    # === Time features (вычисляются из fractal_time) ===
    # hour_sin, hour_cos — циклическое кодирование часа суток
    hour = (fractal_times % 86400) / 3600.0  # 0..23.99
    X[:, :, TIME_FEAT_HOUR_SIN] = np.where(raw_valid, np.sin(2 * np.pi * hour / 24), 0.0)
    X[:, :, TIME_FEAT_HOUR_COS] = np.where(raw_valid, np.cos(2 * np.pi * hour / 24), 0.0)

    # time_pos — позиция фрактала на временной оси строки [0..1]
    # newest=1, oldest=0; padding=0
    times_masked = np.where(raw_valid & (fractal_times > 0), fractal_times, np.nan)
    t_newest = np.nanmax(times_masked, axis=1, keepdims=True)  # (n_samples, 1)
    t_oldest = np.nanmin(times_masked, axis=1, keepdims=True)  # (n_samples, 1)
    span = t_newest - t_oldest
    span = np.where(span > 0, span, 1.0)  # avoid division by zero
    time_pos = (fractal_times - t_oldest) / span
    X[:, :, TIME_FEAT_TIME_POS] = np.where(raw_valid & (fractal_times > 0), time_pos, 0.0)

    # === Shift features (из 23-го поля фрактала: возраст фрактала в барах = SHIFT(T) - cur_bar) ===
    # log_shift — log1p(shift): возраст фрактала в барах, лог-масштабированный
    X[:, :, TIME_FEAT_LOG_SHIFT] = np.where(raw_valid, np.log1p(shifts), 0.0)

    # delta_shift — |shift[i] - shift[i+1]|: временной зазор между соседними фракталами
    # shift[i+1] > shift[i] (старший фрактал старше), поэтому берём модуль разности
    # delta_shift вычисляется только если ОБА соседних фрактала валидны;
    # для fractal99 delta_shift = 0 (нет fractal100)
    delta_shift = np.zeros_like(shifts)
    for i in range(N_FRACTALS - 1):
        both_valid = raw_valid[:, i] & raw_valid[:, i + 1]
        delta_shift[:, i] = np.where(both_valid, np.abs(shifts[:, i] - shifts[:, i + 1]), 0.0)
    X[:, :, TIME_FEAT_LOG_DELTA_SHIFT] = np.where(raw_valid, np.log1p(delta_shift), 0.0)

    # Финальная маска: True для валидных (non-padding) позиций
    mask = raw_valid

    # NaN → 0
    X = np.nan_to_num(X, nan=0.0).astype(np.float32)

    validate_parsed_features(X, mask, source=df.index.name or 'parse_fractals_to_3d')

    return X, mask


def normalize_features(
    X_train: np.ndarray,
    X_val: np.ndarray,
    use_scaler: bool = True,
) -> tuple[np.ndarray, np.ndarray, StandardScaler | None]:
    """
    Нормализация features с помощью StandardScaler (опционально).

    Если use_scaler=False, данные возвращаются без изменений (но scaler=None).

    Fit на train, transform на val. Нормализуется по каждому feature индексу
    отдельно по всему train. Для этого flatten: (n_samples * seq_len, n_features).

    Аргументы:
        X_train: shape (n_train, 100, 11)
        X_val: shape (n_val, 100, 11)

    Возвращает:
        Кортеж (X_train_norm, X_val_norm, scaler):
        - X_train_norm: shape (n_train, 100, 11) нормализованный train
        - X_val_norm: shape (n_val, 100, 11) нормализованный val
        - scaler: обученный StandardScaler (или None, если отключено)
    """
    if not use_scaler:
        return X_train, X_val, None

    n_train, seq_len, n_features = X_train.shape
    n_val = X_val.shape[0]

    # Flatten для fit/transform: (n_samples * seq_len, n_features)
    X_train_flat = X_train.reshape(-1, n_features)
    X_val_flat = X_val.reshape(-1, n_features)

    scaler = StandardScaler()
    X_train_norm = scaler.fit_transform(X_train_flat).reshape(n_train, seq_len, n_features)
    X_val_norm = scaler.transform(X_val_flat).reshape(n_val, seq_len, n_features)

    return (
        X_train_norm.astype(np.float32),
        X_val_norm.astype(np.float32),
        scaler,
    )


# ─── PyTorch Dataset ─────────────────────────────────────────────────────────

class FractalSequenceDataset(Dataset):
    """
    PyTorch Dataset для фрактальных последовательностей.

    Каждый сэмпл содержит:
    - X: tensor shape (seq_len=100, features=26)
    - y: tensor scalar (classification/single regression) или (10,) для multi-target
    - mask: tensor shape (seq_len=100) — True для валидных позиций

    Аргументы:
        X: np.ndarray shape (n_samples, 100, 26) — нормализованные features
        y: np.ndarray shape (n_samples,) — метки {-1, 0, 1} (classification)
               или float predict (regression) или shape (n_samples, 10) для multi-target
        mask: np.ndarray shape (n_samples, 100) — padding mask
        regression: bool — если True, y трактуется как float (не маппируется)
    """

    def __init__(
        self,
        X: np.ndarray,
        y: np.ndarray,
        mask: np.ndarray,
        regression: bool = False,
        label_map: dict[int, int] | None = None,
    ):
        self.X = torch.from_numpy(X).float()
        if regression:
            # Регрессия: y — float, маппинг не нужен
            self.y = torch.from_numpy(y.astype(np.float32)).float()
        else:
            # Классификация: маппинг {-1, 0, 1} → {0, 1, 2}
            target_map = label_map if label_map is not None else LABEL_MAP
            y_mapped = np.array([target_map[int(label)] for label in y], dtype=np.int64)
            self.y = torch.from_numpy(y_mapped).long()
        self.mask = torch.from_numpy(mask).bool()

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.X[idx], self.y[idx], self.mask[idx]


class EntryPathDataset(Dataset):
    def __init__(
        self,
        X: np.ndarray,
        engineered: np.ndarray | None,
        y_reg: np.ndarray,
        y_cls: np.ndarray,
        mask: np.ndarray,
        signal: np.ndarray,
    ):
        lengths = [len(X), len(y_reg), len(y_cls), len(mask), len(signal)]
        if engineered is not None:
            lengths.append(len(engineered))
        if len(set(lengths)) != 1:
            raise ValueError('X, engineered, y_reg, y_cls, mask, and signal must have the same length')
        self.X = torch.from_numpy(X).float()
        self.engineered = None if engineered is None else torch.from_numpy(engineered.astype(np.float32)).float()
        self.y_reg = torch.from_numpy(y_reg.astype(np.float32)).float()
        self.y_cls = torch.from_numpy(y_cls.astype(np.int64)).long()
        self.mask = torch.from_numpy(mask).bool()
        self.signal = torch.from_numpy(signal.astype(np.int64)).long()

    def __len__(self) -> int:
        return len(self.y_cls)

    def __getitem__(self, idx: int):
        if self.engineered is None:
            return self.X[idx], self.y_reg[idx], self.y_cls[idx], self.mask[idx], self.signal[idx]
        return self.X[idx], self.engineered[idx], self.y_reg[idx], self.y_cls[idx], self.mask[idx], self.signal[idx]


# ─── Фабрика DataLoader'ов ───────────────────────────────────────────────────

def create_data_loaders(
    batch_size: int = 256,
    num_workers: int = 0,
    target: str = 'signal',
    use_scaler: bool = False,
    use_weighted_sampler: bool = False,
    seq_len: int = 100,
    clear_cache: bool = False,
    entry_path_feature_profile: str = ENTRY_PATH_DEFAULT_FEATURE_PROFILE,
    seed: int = 42,
) -> tuple[DataLoader, DataLoader, StandardScaler | None]:
    """
    Создание train и val DataLoader'ов.

    Полный pipeline: загрузка CSV → парсинг 3D → нормализация → Dataset → DataLoader.

    Аргументы:
        batch_size: Размер батча (по умолчанию 256)
        num_workers: Количество worker'ов для загрузки данных
        target: Колонка таргета — 'signal' (классификация, default) или
                'predict' (регрессия, непрерывные значения float)
        use_scaler: Использовать ли математический StandardScaler (default: False)
        use_weighted_sampler: Использовать ли WeightedRandomSampler для train (только для classification).
                             Веса обратны частотам класса. Default: False
        seq_len: Количество последних фракталов для обучения (максимум 100). Default: 100

    Возвращает:
        Кортеж (train_loader, val_loader, scaler):
        - train_loader: DataLoader (shuffle=True или sampler=WeightedRandomSampler)
        - val_loader: DataLoader (shuffle=False, реальное распределение)
        - scaler: обученный StandardScaler (или None, если use_scaler=False)

    Пример:
        >>> train_loader, val_loader, scaler = create_data_loaders(batch_size=256)
        >>> for X_batch, y_batch, mask_batch in train_loader:
        ...     # X_batch: (256, 100, 11), y_batch: (256,), mask_batch: (256, 100)
        ...     logits = model(X_batch, mask_batch)
    """
    print("📦 Загрузка данных...")
    seq_len = validate_seq_len_for_target(target, seq_len)
    regression = (
        (target in SINGLE_REGRESSION_COLUMNS)
        or (target == UPDN_REGRESSION_TARGET)
        or (target == TRAILING_STOP_TARGET)
        or (target == TAKE_SKIP_TRAILING_STOP_TARGET)
        or (target == TAKE_SKIP_TRAILING_STOP_V2_TARGET)
    )
    multi_target = (target == UPDN_REGRESSION_TARGET)
    triple_barrier = (target == TB_TARGET)
    binary_classification = (target in BINARY_CLASSIFICATION_COLUMNS)
    entry_path = (target == ENTRY_PATH_TARGET)
    entry_path_quantile = (target == ENTRY_PATH_V1_QUANTILE_TARGET)
    entry_path_like = entry_path or entry_path_quantile
    trailing_stop = (target == TRAILING_STOP_TARGET)
    trailing_stop_quantile = (target == TRAILING_STOP_TARGET_QUANTILE_TARGET)
    take_skip_trailing_stop = (target == TAKE_SKIP_TRAILING_STOP_TARGET)
    take_skip_trailing_stop_v2 = (target == TAKE_SKIP_TRAILING_STOP_V2_TARGET)

    def load_or_parse_data(
        csv_file: Path,
        target_col: str,
        prefix: str,
    ):
        profile_suffix = cache_profile_suffix(target_col)
        entry_path_profile_suffix = entry_path_feature_cache_suffix(entry_path_feature_profile) if entry_path else ''
        x_path = DATA_DIR / f'X_{prefix}{profile_suffix}.npy'
        mask_path = DATA_DIR / f'mask_{prefix}{profile_suffix}.npy'
        if entry_path:
            cache_suffix = f'{profile_suffix}{entry_path_profile_suffix}'
            engineered_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_engineered{cache_suffix}.npy'
            y_reg_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_reg{cache_suffix}.npy'
            y_cls_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_cls{cache_suffix}.npy'
            signal_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_signal{cache_suffix}.npy'
            cache_files = [x_path, mask_path, engineered_path, y_reg_path, y_cls_path, signal_path]
        elif entry_path_quantile:
            y_reg_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_reg{profile_suffix}.npy'
            y_cls_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_cls{profile_suffix}.npy'
            signal_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_signal{profile_suffix}.npy'
            cache_files = [x_path, mask_path, y_reg_path, y_cls_path, signal_path]
        else:
            y_path = DATA_DIR / f'y_{prefix}_{target_col}{profile_suffix}.npy'
            cache_files = [x_path, mask_path, y_path]

        # 1. Принудительная очистка
        if clear_cache:
            print(f"  🧹 Принудительная очистка кэша ({prefix})...")
            for f in cache_files:
                if f.exists():
                    f.unlink()

        # 2. Автоматическая инвалидация по дате изменения
        elif all(f.exists() for f in cache_files):
            csv_mtime = csv_file.stat().st_mtime
            cache_mtimes = [f.stat().st_mtime for f in cache_files]
            
            if any(csv_mtime > mtime for mtime in cache_mtimes):
                print(f"  🔄 Исходный файл {csv_file.name} обновился. Инвалидация кэша {prefix}...")
                for f in cache_files:
                    f.unlink()
            else:
                X = np.load(x_path)
                # Проверяем совместимость кэша по количеству features
                expected_feature_dim = TAKE_SKIP_V2_INPUT_FEATURES if take_skip_trailing_stop_v2 else N_FRACTAL_FEATURES
                if X.shape[2] != expected_feature_dim:
                    print(f"  🔄 Кэш {prefix} устарел ({X.shape[2]} features, ожидается {expected_feature_dim}). Инвалидация...")
                    for f in cache_files:
                        f.unlink()
                else:
                    print(f"  Загрузка кэшированных данных {prefix} из .npy...")
                    mask = np.load(mask_path)
                    if entry_path:
                        engineered = np.load(engineered_path)
                        y_reg = np.load(y_reg_path)
                        y_cls = np.load(y_cls_path)
                        signal = np.load(signal_path)
                        if (
                            engineered.ndim != 2
                            or (
                                entry_path_feature_profile == ENTRY_PATH_DEFAULT_FEATURE_PROFILE
                                and engineered.shape[1] != len(ENTRY_PATH_V1_FEATURE_COLUMNS)
                            )
                            or
                            y_reg.ndim != 2
                            or y_reg.shape[1] != len(ENTRY_PATH_REG_TARGETS)
                            or y_cls.ndim != 1
                            or signal.ndim != 1
                            or len(engineered) != len(X)
                            or len(y_reg) != len(X)
                            or len(y_cls) != len(X)
                            or len(signal) != len(X)
                        ):
                            print(f"  🔄 Кэш {prefix} entry_path_v1 повреждён. Инвалидация...")
                            for f in cache_files:
                                f.unlink()
                        else:
                            return X, mask, engineered, y_reg, y_cls, signal
                    elif entry_path_quantile:
                        y_reg = np.load(y_reg_path)
                        y_cls = np.load(y_cls_path)
                        signal = np.load(signal_path)
                        if (
                            y_reg.ndim != 2
                            or y_reg.shape[1] != len(ENTRY_PATH_REG_TARGETS)
                            or y_cls.ndim != 1
                            or signal.ndim != 1
                            or len(y_reg) != len(X)
                            or len(y_cls) != len(X)
                            or len(signal) != len(X)
                        ):
                            print(f"  🔄 Кэш {prefix} entry_path_v1_quantile повреждён. Инвалидация...")
                            for f in cache_files:
                                f.unlink()
                        else:
                            return X, mask, y_reg, y_cls, signal
                    elif trailing_stop:
                        y = np.load(y_path)
                        if (
                            y.ndim != 2
                            or y.shape[1] != len(TRAILING_STOP_TARGET_COLUMNS)
                            or len(y) != len(X)
                        ):
                            print(f"  🔄 Кэш {prefix} trailing_stop_target_v1 повреждён. Инвалидация...")
                            for f in cache_files:
                                f.unlink()
                        else:
                            return X, mask, y
                    elif trailing_stop_quantile:
                        y = np.load(y_path)
                        if y.ndim != 2 or y.shape[1] != 1 or len(y) != len(X):
                            print(f"  🔄 Кэш {prefix} trailing_stop_target_quantile_v1 повреждён. Инвалидация...")
                            for f in cache_files:
                                f.unlink()
                        else:
                            return X, mask, y
                    elif take_skip_trailing_stop:
                        y = np.load(y_path)
                        if y.ndim != 2 or y.shape[1] != 5 or len(y) != len(X):
                            print(f"  🔄 Кэш {prefix} take_skip_trailing_stop_v1 повреждён. Инвалидация...")
                            for f in cache_files:
                                f.unlink()
                        else:
                            return X, mask, y
                    elif take_skip_trailing_stop_v2:
                        y = np.load(y_path)
                        if y.ndim != 2 or y.shape[1] != len(TAKE_SKIP_TRAILING_STOP_V2_COLUMNS) or len(y) != len(X):
                            print(f"  🔄 Кэш {prefix} take_skip_trailing_stop_v2 повреждён. Инвалидация...")
                            for f in cache_files:
                                f.unlink()
                        else:
                            return X, mask, y
                    else:
                        y = np.load(y_path)
                        return X, mask, y

        print(f"  Кэш не найден. Загрузка {csv_file.name} и парсинг...")
        df = pd.read_csv(csv_file, sep=CSV_SEP, low_memory=False)
        validate_data_contract(df, source=csv_file.name)
        validate_csv_columns(df, source=csv_file.name)
        validate_fractal_format(df, source=csv_file.name)
        if target_uses_signal_rows(target_col):
            total_rows = len(df)
            df = filter_signal_rows(df, target_col)
            print(f"  🎯 Outcome target profile: signal-only rows {len(df)}/{total_rows}")
        
        # Извлечение таргета
        if entry_path_like:
            engineered = split_entry_path_features(
                df,
                feature_profile=entry_path_feature_profile,
                seq_len=seq_len,
            )
            y_reg, y_cls = split_entry_path_targets(df)
            signal = df['signal'].values.astype(np.int64)
        elif multi_target:
            y = df[UPDN_TARGETS].values.astype(np.float32)  # shape (n, 10)
        elif trailing_stop:
            y = split_trailing_stop_targets(df)
        elif trailing_stop_quantile:
            y = split_trailing_stop_quantile_target(df)
        elif take_skip_trailing_stop:
            y = split_take_skip_targets(df)
        elif take_skip_trailing_stop_v2:
            y = split_take_skip_v2_targets(df)
        elif triple_barrier:
            y = df[TB_TARGET_NAMES].values.astype(np.float32)  # shape (n, 12)
            y = np.where(y == 0.5, 0.0, y)  # TIMEOUT → LOSS (didn't reach TP in scan window)
        elif regression:
            y = df[target_col].values.astype(np.float32)
            if target_col == REGRESSION_TARGET:
                y = np.abs(y)
        elif binary_classification:
            y = df[target_col].values.astype(np.int64)
        else:
            y = df[target_col].values.astype(int)
            
        print(f"  🔧 Парсинг фракталов в 3D тензоры ({prefix})...")
        X, mask = parse_fractals_to_3d(df)
        if take_skip_trailing_stop_v2:
            engineered = build_take_skip_v2_engineered_features(df, X)
            X = append_take_skip_v2_engineered_channels(X, engineered)
        
        # Сохранение кэша
        np.save(x_path, X)
        np.save(mask_path, mask)
        if entry_path:
            np.save(engineered_path, engineered)
            np.save(y_reg_path, y_reg)
            np.save(y_cls_path, y_cls)
            np.save(signal_path, signal)
        elif entry_path_quantile:
            np.save(y_reg_path, y_reg)
            np.save(y_cls_path, y_cls)
            np.save(signal_path, signal)
        elif trailing_stop:
            np.save(y_path, y)
        else:
            np.save(y_path, y)
        print(f"  ✅ Данные {prefix} сохранены в кэш.")
        
        if entry_path:
            return X, mask, engineered, y_reg, y_cls, signal
        if entry_path_quantile:
            return X, mask, y_reg, y_cls, signal
        return X, mask, y

    if entry_path:
        X_train, mask_train, engineered_train, y_train_reg, y_train_cls, signal_train = load_or_parse_data(TRAIN_FILE, target, 'train')
        X_val, mask_val, engineered_val, y_val_reg, y_val_cls, signal_val = load_or_parse_data(VAL_FILE, target, 'val')
    elif entry_path_quantile:
        X_train, mask_train, y_train_reg, y_train_cls, signal_train = load_or_parse_data(TRAIN_FILE, target, 'train')
        X_val, mask_val, y_val_reg, y_val_cls, signal_val = load_or_parse_data(VAL_FILE, target, 'val')
    else:
        X_train, mask_train, y_train = load_or_parse_data(TRAIN_FILE, target, 'train')
        X_val, mask_val, y_val = load_or_parse_data(VAL_FILE, target, 'val')

    # Truncate sequence length if requested
    if seq_len < 100:
        print(f"  ✂️ Усечение последовательности фракталов до {seq_len} (оставляем самые недавние)")
        # Фракталы записаны: 0 - самый новый, 99 - самый старый
        X_train = X_train[:, :seq_len, :]
        mask_train = mask_train[:, :seq_len]
        X_val = X_val[:, :seq_len, :]
        mask_val = mask_val[:, :seq_len]

    if entry_path_like:
        print(f"  Train: {len(y_train_cls)} строк, Val: {len(y_val_cls)} строк")
    else:
        print(f"  Train: {len(y_train)} строк, Val: {len(y_val)} строк")

    if entry_path_like:
        for name, y_reg, y_cls in [('Train', y_train_reg, y_train_cls), ('Val', y_val_reg, y_val_cls)]:
            print(f"  {name} entry_path reg targets: shape={y_reg.shape}")
            print(f"  {name} entry_path class targets: shape={y_cls.shape}")
    elif multi_target:
        for name, y in [('Train', y_train), ('Val', y_val)]:
            print(f"  {name} updn targets: shape={y.shape}")
            for i, col in enumerate(UPDN_TARGETS):
                print(f"    {col}: mean={y[:, i].mean():.4f}, std={y[:, i].std():.4f}, "
                      f"min={y[:, i].min():.4f}, max={y[:, i].max():.4f}")
    elif trailing_stop:
        for name, y in [('Train', y_train), ('Val', y_val)]:
            print(f"  {name} trailing_stop targets: shape={y.shape}")
            for i, col in enumerate(TRAILING_STOP_TARGET_COLUMNS):
                print(f"    {col}: mean={y[:, i].mean():.4f}, std={y[:, i].std():.4f}, "
                      f"min={y[:, i].min():.4f}, max={y[:, i].max():.4f}")
    elif take_skip_trailing_stop:
        for name, y in [('Train', y_train), ('Val', y_val)]:
            print(f"  {name} take_skip targets: shape={y.shape}")
            for i in range(y.shape[1]):
                print(f"    take_skip_{i}: positive_rate={y[:, i].mean():.4f}")
    elif take_skip_trailing_stop_v2:
        for name, y in [('Train', y_train), ('Val', y_val)]:
            print(f"  {name} take_skip_v2 targets: shape={y.shape}")
            for i, column in enumerate(TAKE_SKIP_TRAILING_STOP_V2_COLUMNS):
                print(f"    {column}: positive_rate={y[:, i].mean():.4f}")
    elif triple_barrier:
        for name, y in [('Train', y_train), ('Val', y_val)]:
            print(f"  {name} TB targets: shape={y.shape}")
            for i, col in enumerate(TB_TARGET_NAMES):
                ones = y[:, i].sum()
                total = len(y)
                print(f"    {col}: {int(ones)}/{total} ({ones/total*100:.1f}%)")
    elif regression:
        for name, y in [('Train', y_train), ('Val', y_val)]:
            print(f"  {name} predict (absolute): min={y.min():.4f}, max={y.max():.4f}, "
                  f"mean={y.mean():.4f}, std={y.std():.4f}")
    else:
        for name, y in [('Train', y_train), ('Val', y_val)]:
            classes, counts = np.unique(y, return_counts=True)
            total = len(y)
            dist_str = ", ".join(
                [f"{c}: {cnt} ({cnt / total * 100:.1f}%)" for c, cnt in zip(classes, counts)]
            )
            print(f"  {name}: {dist_str}")

    print(f"  ✅ Train: X={X_train.shape}, mask={mask_train.shape}")
    print(f"  ✅ Val: X={X_val.shape}, mask={mask_val.shape}")

    # ── Дополнительная Нормализация (StandardScaler) ─────────────────────────
    if use_scaler:
        print("\n📏 Формирование features (StandardScaler, fit на train)...")
    else:
        print("\n📏 StandardScaler выключен (use_scaler=False). Дополнительная нормализация не применяется.")
    X_train_norm, X_val_norm, scaler = normalize_features(X_train, X_val, use_scaler=use_scaler)
    if use_scaler:
        print(f"  ✅ Нормализация завершена")

    # ── Создание Dataset и DataLoader ────────────────────────────────────────
    if entry_path:
        train_dataset = EntryPathDataset(X_train_norm, engineered_train, y_train_reg, y_train_cls, mask_train, signal_train)
        val_dataset = EntryPathDataset(X_val_norm, engineered_val, y_val_reg, y_val_cls, mask_val, signal_val)
    elif entry_path_quantile:
        train_dataset = EntryPathDataset(X_train_norm, None, y_train_reg, y_train_cls, mask_train, signal_train)
        val_dataset = EntryPathDataset(X_val_norm, None, y_val_reg, y_val_cls, mask_val, signal_val)
    else:
        train_dataset = FractalSequenceDataset(
            X_train_norm, y_train, mask_train,
            regression=(regression or triple_barrier),
            label_map=BINARY_LABEL_MAP if binary_classification else None,
        )
        val_dataset = FractalSequenceDataset(
            X_val_norm, y_val, mask_val,
            regression=(regression or triple_barrier),
            label_map=BINARY_LABEL_MAP if binary_classification else None,
        )

    generator = torch.Generator()
    generator.manual_seed(int(seed))

    def worker_init_fn(worker_id: int):
        worker_seed = int(seed) + int(worker_id)
        np.random.seed(worker_seed)
        random.seed(worker_seed)

    # Если use_weighted_sampler: создаём WeightedRandomSampler только для train
    if use_weighted_sampler and not regression and not entry_path and not trailing_stop_quantile and not take_skip_trailing_stop and not take_skip_trailing_stop_v2:
        # Рассчитываем веса: 1 / freq(class)
        if binary_classification:
            y_train_mapped = y_train.astype(np.int64)
            class_counts = np.bincount(y_train_mapped, minlength=2)
        else:
            y_train_mapped = y_train + 1  # {-1, 0, 1} → {0, 1, 2}
            class_counts = np.bincount(y_train_mapped)
        class_weights = 1.0 / class_counts
        sample_weights = class_weights[y_train_mapped]
        sampler = WeightedRandomSampler(
            weights=sample_weights,
            num_samples=len(train_dataset),
            replacement=True,
            generator=generator,
        )
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            sampler=sampler,  # Используем sampler вместо shuffle
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available(),
            drop_last=False,
            generator=generator,
            worker_init_fn=worker_init_fn,
        )
        sampler_info = " (WeightedRandomSampler)"
    else:
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,       # Каждая строка — независимый snapshot, shuffle допустим
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available(),
            drop_last=False,
            generator=generator,
            worker_init_fn=worker_init_fn,
        )
        sampler_info = ""

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=False,
        worker_init_fn=worker_init_fn,
    )

    print(f"\n✅ DataLoaders: train={len(train_loader)} batches{sampler_info}, "
          f"val={len(val_loader)} batches (batch_size={batch_size})")

    return train_loader, val_loader, scaler


def create_test_loader(
    batch_size: int = 256,
    target: str = 'predict',
    seq_len: int = 100,
    clear_cache: bool = False,
    num_workers: int = 4,
    entry_path_feature_profile: str = ENTRY_PATH_DEFAULT_FEATURE_PROFILE,
) -> DataLoader:
    """Только для инференса на отложенной выборке. StandardScaler отключён (False)."""
    print("\n📦 Загрузка тестовых данных...")
    seq_len = validate_seq_len_for_target(target, seq_len)
    regression = (
        (target in SINGLE_REGRESSION_COLUMNS)
        or (target == UPDN_REGRESSION_TARGET)
        or (target == TRAILING_STOP_TARGET)
        or (target == TAKE_SKIP_TRAILING_STOP_TARGET)
        or (target == TAKE_SKIP_TRAILING_STOP_V2_TARGET)
    )
    multi_target = (target == UPDN_REGRESSION_TARGET)
    triple_barrier = (target == TB_TARGET)
    binary_classification = (target in BINARY_CLASSIFICATION_COLUMNS)
    profile_suffix = cache_profile_suffix(target)
    entry_path = (target == ENTRY_PATH_TARGET)
    entry_path_quantile = (target == ENTRY_PATH_V1_QUANTILE_TARGET)
    entry_path_like = entry_path or entry_path_quantile
    trailing_stop = (target == TRAILING_STOP_TARGET)
    trailing_stop_quantile = (target == TRAILING_STOP_TARGET_QUANTILE_TARGET)
    take_skip_trailing_stop = (target == TAKE_SKIP_TRAILING_STOP_TARGET)
    take_skip_trailing_stop_v2 = (target == TAKE_SKIP_TRAILING_STOP_V2_TARGET)
    prefix = 'test'
    missing_entry_path_labels = False

    x_path = DATA_DIR / f'X_{prefix}{profile_suffix}.npy'
    mask_path = DATA_DIR / f'mask_{prefix}{profile_suffix}.npy'
    if entry_path:
        cache_suffix = f'{profile_suffix}{entry_path_feature_cache_suffix(entry_path_feature_profile)}'
        engineered_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_engineered{cache_suffix}.npy'
        y_reg_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_reg{cache_suffix}.npy'
        y_cls_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_cls{cache_suffix}.npy'
        signal_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_signal{cache_suffix}.npy'
        cache_files = [x_path, mask_path, engineered_path, y_reg_path, y_cls_path, signal_path]
    elif entry_path_quantile:
        y_reg_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_reg{profile_suffix}.npy'
        y_cls_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_cls{profile_suffix}.npy'
        signal_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_signal{profile_suffix}.npy'
        cache_files = [x_path, mask_path, y_reg_path, y_cls_path, signal_path]
    elif trailing_stop:
        y_path = DATA_DIR / f'y_{prefix}_{target}{profile_suffix}.npy'
        cache_files = [x_path, mask_path, y_path]
    else:
        y_path = DATA_DIR / f'y_{prefix}_{target}{profile_suffix}.npy'
        cache_files = [x_path, mask_path, y_path]

    if clear_cache:
        print(f"  🧹 Принудительная очистка кэша ({prefix})...")
        for f in cache_files:
            if f.exists():
                f.unlink()
    elif all(f.exists() for f in cache_files):
        csv_mtime = TEST_FILE.stat().st_mtime
        if any(csv_mtime > f.stat().st_mtime for f in cache_files):
            print(f"  🔄 Файл {TEST_FILE.name} обновился. Инвалидация кэша {prefix}...")
            for f in cache_files:
                f.unlink()
        else:
            X = np.load(x_path)
            expected_feature_dim = TAKE_SKIP_V2_INPUT_FEATURES if take_skip_trailing_stop_v2 else N_FRACTAL_FEATURES
            if X.shape[2] != expected_feature_dim:
                print(f"  🔄 Кэш {prefix} устарел. Инвалидация...")
                for f in cache_files:
                    f.unlink()
            else:
                print(f"  Загрузка кэшированных данных {prefix} из .npy...")
                mask = np.load(mask_path)
                if entry_path:
                    engineered = np.load(engineered_path)
                    y_reg = np.load(y_reg_path)
                    y_cls = np.load(y_cls_path)
                    signal = np.load(signal_path)
                    if (
                        engineered.ndim != 2
                        or (
                            entry_path_feature_profile == ENTRY_PATH_DEFAULT_FEATURE_PROFILE
                            and engineered.shape[1] != len(ENTRY_PATH_V1_FEATURE_COLUMNS)
                        )
                        or
                        y_reg.ndim != 2
                        or y_reg.shape[1] != len(ENTRY_PATH_REG_TARGETS)
                        or y_cls.ndim != 1
                        or signal.ndim != 1
                        or len(engineered) != len(X)
                        or len(y_reg) != len(X)
                        or len(y_cls) != len(X)
                        or len(signal) != len(X)
                    ):
                        print(f"  🔄 Кэш {prefix} entry_path_v1 повреждён. Инвалидация...")
                        for f in cache_files:
                            f.unlink()
                    else:
                        if seq_len < 100:
                            X = X[:, :seq_len, :]
                            mask = mask[:, :seq_len]
                        dataset = EntryPathDataset(X, engineered, y_reg, y_cls, mask, signal)
                        return DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)
                elif entry_path_quantile:
                    y_reg = np.load(y_reg_path)
                    y_cls = np.load(y_cls_path)
                    signal = np.load(signal_path)
                    if (
                        y_reg.ndim != 2
                        or y_reg.shape[1] != len(ENTRY_PATH_REG_TARGETS)
                        or y_cls.ndim != 1
                        or signal.ndim != 1
                        or len(y_reg) != len(X)
                        or len(y_cls) != len(X)
                        or len(signal) != len(X)
                    ):
                        print(f"  🔄 Кэш {prefix} entry_path_v1_quantile повреждён. Инвалидация...")
                        for f in cache_files:
                            f.unlink()
                    else:
                        if seq_len < 100:
                            X = X[:, :seq_len, :]
                            mask = mask[:, :seq_len]
                        dataset = EntryPathDataset(X, None, y_reg, y_cls, mask, signal)
                        return DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)
                elif trailing_stop:
                    y = np.load(y_path)
                    if (
                        y.ndim != 2
                        or y.shape[1] != len(TRAILING_STOP_TARGET_COLUMNS)
                        or len(y) != len(X)
                    ):
                        print(f"  🔄 Кэш {prefix} trailing_stop_target_v1 повреждён. Инвалидация...")
                        for f in cache_files:
                            f.unlink()
                    else:
                        if seq_len < 100:
                            X = X[:, :seq_len, :]
                            mask = mask[:, :seq_len]
                        dataset = FractalSequenceDataset(
                            X,
                            y,
                            mask,
                            regression=True,
                            label_map=None,
                        )
                        return DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)
                elif trailing_stop_quantile:
                    y = np.load(y_path)
                    if y.ndim != 2 or y.shape[1] != 1 or len(y) != len(X):
                        print(f"  🔄 Кэш {prefix} trailing_stop_target_quantile_v1 повреждён. Инвалидация...")
                        for f in cache_files:
                            f.unlink()
                    else:
                        if seq_len < 100:
                            X = X[:, :seq_len, :]
                            mask = mask[:, :seq_len]
                        dataset = FractalSequenceDataset(
                            X,
                            y,
                            mask,
                            regression=True,
                            label_map=None,
                        )
                        return DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)
                elif take_skip_trailing_stop_v2:
                    y = np.load(y_path)
                    if y.ndim != 2 or y.shape[1] != len(TAKE_SKIP_TRAILING_STOP_V2_COLUMNS) or len(y) != len(X):
                        print(f"  🔄 Кэш {prefix} take_skip_trailing_stop_v2 повреждён. Инвалидация...")
                        for f in cache_files:
                            f.unlink()
                    else:
                        if seq_len < 100:
                            X = X[:, :seq_len, :]
                            mask = mask[:, :seq_len]
                        dataset = FractalSequenceDataset(
                            X,
                            y,
                            mask,
                            regression=True,
                            label_map=None,
                        )
                        return DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)
                elif take_skip_trailing_stop:
                    y = np.load(y_path)
                    if y.ndim != 2 or y.shape[1] != 5 or len(y) != len(X):
                        print(f"  🔄 Кэш {prefix} take_skip_trailing_stop_v1 повреждён. Инвалидация...")
                        for f in cache_files:
                            f.unlink()
                    else:
                        if seq_len < 100:
                            X = X[:, :seq_len, :]
                            mask = mask[:, :seq_len]
                        dataset = FractalSequenceDataset(
                            X,
                            y,
                            mask,
                            regression=True,
                            label_map=None,
                        )
                        return DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)
                else:
                    y = np.load(y_path)

                    if seq_len < 100:
                        X = X[:, :seq_len, :]
                        mask = mask[:, :seq_len]

                    dataset = FractalSequenceDataset(
                        X,
                        y,
                        mask,
                        regression=(regression or triple_barrier),
                        label_map=BINARY_LABEL_MAP if binary_classification else None,
                    )
                    return DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    print(f"  Кэш не найден. Загрузка {TEST_FILE.name} и парсинг...")
    df = pd.read_csv(TEST_FILE, sep=CSV_SEP, low_memory=False)
    if target_uses_signal_rows(target):
        total_rows = len(df)
        df = filter_signal_rows(df, target)
        print(f"  🎯 Outcome target profile: signal-only rows {len(df)}/{total_rows}")

    if entry_path_like:
        if all(col in df.columns for col in ENTRY_PATH_REG_TARGETS + ['path_6_class']):
            y_reg, y_cls = split_entry_path_targets(df)
        else:
            missing_entry_path_labels = True
            print("  ⚠ entry_path_v1 test labels не найдены в TEST CSV. Используются placeholder targets для inference/export.")
            y_reg = np.zeros((len(df), len(ENTRY_PATH_REG_TARGETS)), dtype=np.float32)
            y_cls = np.zeros(len(df), dtype=np.int64)
        signal = df['signal'].values.astype(np.int64)
        if entry_path:
            engineered = split_entry_path_features(
                df,
                feature_profile=entry_path_feature_profile,
                seq_len=seq_len,
            )
    elif trailing_stop:
        y = split_trailing_stop_targets(df)
    elif trailing_stop_quantile:
        y = split_trailing_stop_quantile_target(df)
    elif take_skip_trailing_stop:
        y = split_take_skip_targets(df)
    elif take_skip_trailing_stop_v2:
        y = split_take_skip_v2_targets(df)
    elif multi_target:
        y = df[UPDN_TARGETS].values.astype(np.float32)
    elif triple_barrier:
        y = df[TB_TARGET_NAMES].values.astype(np.float32)
        y = np.where(y == 0.5, 0.0, y)  # TIMEOUT → LOSS
    elif regression:
        y = df[target].values.astype(np.float32)
        if target == REGRESSION_TARGET:
            y = np.abs(y)
    elif binary_classification:
        y = df[target].values.astype(np.int64)
    else:
        y = df[target].values.astype(int)

    X, mask = parse_fractals_to_3d(df)
    if take_skip_trailing_stop_v2:
        engineered = build_take_skip_v2_engineered_features(df, X)
        X = append_take_skip_v2_engineered_channels(X, engineered)
    np.save(x_path, X)
    np.save(mask_path, mask)
    if entry_path:
        np.save(engineered_path, engineered)
        if not missing_entry_path_labels:
            np.save(y_reg_path, y_reg)
            np.save(y_cls_path, y_cls)
        np.save(signal_path, signal)
    elif entry_path_quantile:
        if not missing_entry_path_labels:
            np.save(y_reg_path, y_reg)
            np.save(y_cls_path, y_cls)
        np.save(signal_path, signal)
    elif trailing_stop:
        np.save(y_path, y)
    elif trailing_stop_quantile:
        np.save(y_path, y)
    elif take_skip_trailing_stop:
        np.save(y_path, y)
    else:
        np.save(y_path, y)
    print(f"  ✅ Данные {prefix} сохранены в кэш.")

    if seq_len < 100:
        X = X[:, :seq_len, :]
        mask = mask[:, :seq_len]

    if entry_path:
        if missing_entry_path_labels:
            y_reg = np.zeros((len(df), len(ENTRY_PATH_REG_TARGETS)), dtype=np.float32)
            y_cls = np.zeros(len(df), dtype=np.int64)
        dataset = EntryPathDataset(X, engineered, y_reg, y_cls, mask, signal)
    elif entry_path_quantile:
        if missing_entry_path_labels:
            y_reg = np.zeros((len(df), len(ENTRY_PATH_REG_TARGETS)), dtype=np.float32)
            y_cls = np.zeros(len(df), dtype=np.int64)
        dataset = EntryPathDataset(X, None, y_reg, y_cls, mask, signal)
    elif trailing_stop:
        dataset = FractalSequenceDataset(
            X,
            y,
            mask,
            regression=True,
            label_map=None,
        )
    elif take_skip_trailing_stop:
        dataset = FractalSequenceDataset(
            X,
            y,
            mask,
            regression=True,
            label_map=None,
        )
    elif take_skip_trailing_stop_v2:
        dataset = FractalSequenceDataset(
            X,
            y,
            mask,
            regression=True,
            label_map=None,
        )
    else:
        dataset = FractalSequenceDataset(
            X,
            y,
            mask,
            regression=(regression or triple_barrier),
            label_map=BINARY_LABEL_MAP if binary_classification else None,
        )
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=False,
    )
    print(f"  ✅ Test DataLoader создан: {len(loader)} batches (batch_size={batch_size})")
    
    return loader
