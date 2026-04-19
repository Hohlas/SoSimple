# =============================================================================
# Файл: data_loader.py
# Назначение: Dataset и DataLoader для фрактальных последовательностей с кэшированием тензоров
# Язык: Python 3.11+
# Обновлён: 2026-04-08
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
#   - N_RAW_FEATURES=22: полный формат фрактала из Nero.csv
#   - N_FRACTAL_FEATURES=20: 17 входных полей + 3 time-фичи (hour_sin, hour_cos, time_pos); форма X: (n, 100, 20)
#   - UPDN_TARGETS: ['up_12','dn_12','up_24','dn_24','up_48','dn_48']
#   - StandardScaler fit на train, transform на val
#   - При первой загрузке данные кэшируются в .npy файлы для быстрого старта
# =============================================================================

"""
Dataset и DataLoader для фрактальных последовательностей.

Парсит CSV с фракталами в 3D тензоры (n_samples, 100, 20),
исключает fractal_time как сырое поле, вычисляет time-фичи (hour_sin, hour_cos, time_pos),
добавляет ATR_ratio, нормализует features.
Создаёт padding mask для Transformer (NaN позиции).
"""

from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from sklearn.preprocessing import StandardScaler

from ML.entry_path_task import (
    ENTRY_PATH_ALLOWED_SEQUENCE_LENGTHS,
    ENTRY_PATH_TARGET,
    ENTRY_PATH_REG_TARGETS,
    ENTRY_PATH_V1_FEATURE_COLUMNS,
    split_entry_path_features,
    split_entry_path_targets,
)
from ML.entry_path_v1_quantile_task import ENTRY_PATH_V1_QUANTILE_TARGET
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
N_RAW_FEATURES = 22   # T:P:Dir:FrntVal:BackVal:Strong:Brk:Rev:PwrSum:Cnt:Imp:Up12:Dn12:Up24:Dn24:Up48:Dn48:Up3:Dn3:Up6:Dn6:FractalAtr
FRACTAL_ATR_RAW_IDX = 21  # fractal_atr в 22-полевом CSV (ранее было 17)
N_FRACTAL_FEATURES = 20  # 17 входных полей + 3 time-фичи (hour_sin, hour_cos, time_pos)

# Индекс fractal_time в сырых данных (исключается как сырое, но используется для time-фич)
FRACTAL_TIME_IDX = 0

# Индексы вычисляемых features в X
ATR_RATIO_IDX = 16      # fractal_atr → ATR_ratio (in-place)
TIME_FEAT_HOUR_SIN = 17  # sin(2π · hour / 24)
TIME_FEAT_HOUR_COS = 18  # cos(2π · hour / 24)
TIME_FEAT_TIME_POS = 19   # позиция на временной оси строки [0..1]

# Маппинг меток: signal {-1, 0, 1} → индексы {0, 1, 2}
LABEL_MAP = {-1: 0, 0: 1, 1: 2}
INV_LABEL_MAP = {v: k for k, v in LABEL_MAP.items()}

# Имя колонки для регрессионного таргета
REGRESSION_TARGET = 'predict'  # backward compat default
UPDN_REGRESSION_TARGET = 'updn'  # multi-task: 6 Up/Dn таргетов
TRADE_OUTCOME_TARGET = 'trade_outcome_cls'
TRADE_PNL_TARGET = 'trade_pnl_reg'
ARCHETYPE_TARGET = 'signal_archetype_cls'

# Доступные up/dn таргеты
UPDN_TARGETS = ['up_3', 'dn_3', 'up_6', 'dn_6', 'up_12', 'dn_12', 'up_24', 'dn_24', 'up_48', 'dn_48']

TRADE_OUTCOME_COLUMN = 'trade_outcome_h12'
TRADE_PNL_COLUMN = 'trade_pnl_h12_atr'
ARCHETYPE_COLUMN = 'archetype_target'

TASK_TARGET_COLUMNS = {
    TRADE_OUTCOME_TARGET: TRADE_OUTCOME_COLUMN,
    TRADE_PNL_TARGET: TRADE_PNL_COLUMN,
    ARCHETYPE_TARGET: ARCHETYPE_COLUMN,
    TRAILING_STOP_TARGET: TRAILING_STOP_TARGET,
    TRAILING_STOP_TARGET_QUANTILE_TARGET: TRAILING_STOP_TARGET_QUANTILE_TARGET,
}

BINARY_CLASSIFICATION_TARGETS = {
    TRADE_OUTCOME_TARGET,
    ARCHETYPE_TARGET,
}

BINARY_CLASSIFICATION_COLUMNS = {
    TRADE_OUTCOME_COLUMN,
    ARCHETYPE_COLUMN,
}

SIGNAL_ONLY_TARGET_COLUMNS = {
    TRADE_OUTCOME_COLUMN,
    TRADE_PNL_COLUMN,
    ARCHETYPE_COLUMN,
}

SINGLE_REGRESSION_COLUMNS = {
    REGRESSION_TARGET,
    TRADE_PNL_COLUMN,
    TRAILING_STOP_TARGET_QUANTILE_TARGET,
}

TASK_CHECKPOINT_SUFFIXES = {
    TRADE_OUTCOME_TARGET: '_trade_outcome_cls',
    TRADE_PNL_TARGET: '_trade_pnl_reg',
    ARCHETYPE_TARGET: '_signal_archetype_cls',
    TRAILING_STOP_TARGET: '_trailing_stop_target_v1',
    TRAILING_STOP_TARGET_QUANTILE_TARGET: '_trailing_stop_target_quantile_v1',
}

BINARY_LABEL_MAP = {0: 0, 1: 1}


def validate_seq_len_for_target(target: str, seq_len: int) -> int:
    if not 1 <= int(seq_len) <= N_FRACTALS:
        raise ValueError(f'seq_len must be in [1, {N_FRACTALS}], got {seq_len}')
    if target == ENTRY_PATH_TARGET and seq_len not in ENTRY_PATH_ALLOWED_SEQUENCE_LENGTHS:
        allowed = ', '.join(str(value) for value in ENTRY_PATH_ALLOWED_SEQUENCE_LENGTHS)
        raise ValueError(f'{target} supports only seq_len values: {allowed}')
    return int(seq_len)


def task_target_column(task: str) -> str:
    if task in TASK_TARGET_COLUMNS:
        return TASK_TARGET_COLUMNS[task]
    if task == ENTRY_PATH_V1_QUANTILE_TARGET:
        return ENTRY_PATH_TARGET
    if task == TB_TARGET:
        return TB_TARGET
    if task == ENTRY_PATH_TARGET:
        return ENTRY_PATH_TARGET
    if task == UPDN_REGRESSION_TARGET:
        return UPDN_REGRESSION_TARGET
    if task == TRAILING_STOP_TARGET_QUANTILE_TARGET:
        return TRAILING_STOP_TARGET_QUANTILE_TARGET
    if task == TRAILING_STOP_TARGET:
        return TRAILING_STOP_TARGET
    if task == REGRESSION_TARGET:
        return REGRESSION_TARGET
    return 'signal'


def task_checkpoint_suffix(task: str) -> str:
    if task == TB_TARGET:
        return '_tb'
    if task == ENTRY_PATH_V1_QUANTILE_TARGET:
        return '_entry_path_v1_quantile'
    if task == ENTRY_PATH_TARGET:
        return f'_{ENTRY_PATH_TARGET}'
    if task == UPDN_REGRESSION_TARGET:
        return '_updn'
    if task == REGRESSION_TARGET:
        return '_regression'
    return TASK_CHECKPOINT_SUFFIXES.get(task, '')


def target_uses_signal_rows(target: str) -> bool:
    target_name = TASK_TARGET_COLUMNS.get(target, target)
    return target_name in SIGNAL_ONLY_TARGET_COLUMNS


def cache_profile_suffix(target: str) -> str:
    return '_signal_rows' if target_uses_signal_rows(target) else ''


def filter_signal_rows(frame: pd.DataFrame, target: str) -> pd.DataFrame:
    if not target_uses_signal_rows(target):
        return frame
    signal = pd.to_numeric(frame['signal'], errors='coerce').fillna(0).astype(int)
    return frame.loc[signal != 0].reset_index(drop=True)

# Triple Barrier targets (12 binary: 6 BUY + 6 SELL)
TB_TARGET = 'triple_barrier'
TB_SL_LEVELS = [2, 3]
TB_TP_LEVELS = [3, 6, 9]
TB_TARGET_NAMES = []
for _sl in TB_SL_LEVELS:
    for _tp in TB_TP_LEVELS:
        TB_TARGET_NAMES.append(f'buy_sl{_sl}_tp{_tp}')
for _sl in TB_SL_LEVELS:
    for _tp in TB_TP_LEVELS:
        TB_TARGET_NAMES.append(f'sell_sl{_sl}_tp{_tp}')


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
    (21, 'fractal_atr', 'float', lambda v: v > 0,          'fractal_atr > 0'),
]


def validate_fractal_format(df: pd.DataFrame, source: str = '', sample_size: int = 50) -> None:
    col = 'fractal0'
    if col not in df.columns:
        print(f"  ⚠ validate_fractal_format ({source}): колонка {col} не найдена")
        return

    sample = df[col].dropna().head(sample_size)
    errors = []

    for raw in sample:
        parts = str(raw).split(FRACTAL_SEP)
        # 1. Количество полей
        if len(parts) != N_RAW_FEATURES:
            errors.append(
                f"Ожидается {N_RAW_FEATURES} полей, найдено {len(parts)}: '{raw[:60]}...'"
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
        lines = [f"[validate_fractal_format] ПРЕДУПРЕЖДЕНИЕ ({source}):"]
        for e in errors[:5]:  # не спамим, только первые 5
            lines.append(f"  ✗ {e}")
        if len(errors) > 5:
            lines.append(f"  ... и ещё {len(errors) - 5} ошибок")
        lines.append(f"  → Проверь N_RAW_FEATURES={N_RAW_FEATURES} и формат NERO_CSV в lib_PIC.mqh")
        print('\n'.join(lines))
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
    Парсит 22 поля на фрактал; поле 21 (fractal_atr) заменяется ATR_ratio in-place.

    Аргументы:
        df: DataFrame с колонками fractal0..fractal99, ATR, signal

    Возвращает:
        Кортеж (X, mask):
        - X: np.ndarray shape (n_samples, 100, 20) — 20 features per fractal.
             Feature order: price, direction, front, back, strong, break,
             reverse, power, count, impulse, up_12, dn_12, up_24, dn_24,
             up_48, dn_48, ATR_ratio, hour_sin, hour_cos, time_pos
        - mask: np.ndarray shape (n_samples, 100) — True для валидных позиций,
                False для padding (все features == 0)
    """
    fractal_cols = [f'fractal{i}' for i in range(N_FRACTALS)]
    n_samples = len(df)

    # 20 features: CSV fields 1-16 plus field 21 (fractal_atr) + 3 time-фичи.
    n_features = N_FRACTAL_FEATURES
    X = np.zeros((n_samples, N_FRACTALS, n_features), dtype=np.float32)
    # Маска валидности: True если фрактал присутствует (не все NaN)
    raw_valid = np.ones((n_samples, N_FRACTALS), dtype=bool)
    # Хранилище fractal_time для вычисления time-фич
    fractal_times = np.zeros((n_samples, N_FRACTALS), dtype=np.float64)

    for j, col in enumerate(fractal_cols):
        if j % 20 == 0:
            print(f"    парсинг fractal columns {j}-{min(j + 19, N_FRACTALS - 1)}...")

        series = df[col].astype(str)
        split = series.str.split(FRACTAL_SEP, expand=True)

        if split.shape[1] >= N_RAW_FEATURES:
            # Парсим поля: time → fractal_times, fields 1-16 → X[0-15], field 21 (fractal_atr) → X[16]
            for k in range(N_RAW_FEATURES):
                if k == FRACTAL_TIME_IDX:
                    vals = pd.to_numeric(split[k], errors='coerce')
                    fractal_times[:, j] = vals.fillna(0).values
                    continue
                if k >= 17 and k < FRACTAL_ATR_RAW_IDX:
                    continue  # поля up_3/dn_3/up_6/dn_6 (17-20) пропускаем в X
                # k=1..16 → feat_idx=0..15; k=21 (fractal_atr) → feat_idx=16
                feat_idx = k - 1 if k <= 16 else ATR_RATIO_IDX
                vals = pd.to_numeric(split[k], errors='coerce')
                X[:, j, feat_idx] = vals.fillna(0).values

            # Определяем padding: если все features после парсинга NaN
            all_nan = split.iloc[:, 1:].apply(
                lambda col_s: pd.to_numeric(col_s, errors='coerce')
            ).isna().all(axis=1)
            raw_valid[:, j] = ~all_nan.values
        else:
            # Неожиданный формат — помечаем как padding
            raw_valid[:, j] = False

    # ATR_ratio = log(fractal_atr / Atr.Slow) — log-transform сжимает выбросы
    # fractal_atr уже в X[:,:,16] (ATR_RATIO_IDX), ATR — сырое (без RobustScaler)
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
    - X: tensor shape (seq_len=100, features=20)
    - y: tensor scalar (classification/single regression) или (6,) для multi-target
    - mask: tensor shape (seq_len=100) — True для валидных позиций

    Аргументы:
        X: np.ndarray shape (n_samples, 100, 20) — нормализованные features
        y: np.ndarray shape (n_samples,) — метки {-1, 0, 1} (classification)
               или float predict (regression) или shape (n_samples, 6) для multi-target
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
    )
    multi_target = (target == UPDN_REGRESSION_TARGET)
    triple_barrier = (target == TB_TARGET)
    binary_classification = (target in BINARY_CLASSIFICATION_COLUMNS)
    entry_path = (target == ENTRY_PATH_TARGET)
    entry_path_quantile = (target == ENTRY_PATH_V1_QUANTILE_TARGET)
    entry_path_like = entry_path or entry_path_quantile
    trailing_stop = (target == TRAILING_STOP_TARGET)
    trailing_stop_quantile = (target == TRAILING_STOP_TARGET_QUANTILE_TARGET)

    def load_or_parse_data(
        csv_file: Path,
        target_col: str,
        prefix: str,
    ):
        profile_suffix = cache_profile_suffix(target_col)
        x_path = DATA_DIR / f'X_{prefix}{profile_suffix}.npy'
        mask_path = DATA_DIR / f'mask_{prefix}{profile_suffix}.npy'
        if entry_path:
            engineered_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_engineered{profile_suffix}.npy'
            y_reg_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_reg{profile_suffix}.npy'
            y_cls_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_cls{profile_suffix}.npy'
            signal_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_signal{profile_suffix}.npy'
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
                if X.shape[2] != N_FRACTAL_FEATURES:
                    print(f"  🔄 Кэш {prefix} устарел ({X.shape[2]} features, ожидается {N_FRACTAL_FEATURES}). Инвалидация...")
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
                            or engineered.shape[1] != len(ENTRY_PATH_V1_FEATURE_COLUMNS)
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
                    else:
                        y = np.load(y_path)
                        return X, mask, y

        print(f"  Кэш не найден. Загрузка {csv_file.name} и парсинг...")
        df = pd.read_csv(csv_file, sep=CSV_SEP, low_memory=False)
        validate_csv_columns(df, source=csv_file.name)
        validate_fractal_format(df, source=csv_file.name)
        if target_uses_signal_rows(target_col):
            total_rows = len(df)
            df = filter_signal_rows(df, target_col)
            print(f"  🎯 Outcome target profile: signal-only rows {len(df)}/{total_rows}")
        
        # Извлечение таргета
        if entry_path_like:
            engineered = split_entry_path_features(df)
            y_reg, y_cls = split_entry_path_targets(df)
            signal = df['signal'].values.astype(np.int64)
        elif multi_target:
            y = df[UPDN_TARGETS].values.astype(np.float32)  # shape (n, 6)
        elif trailing_stop:
            y = split_trailing_stop_targets(df)
        elif trailing_stop_quantile:
            y = split_trailing_stop_quantile_target(df)
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

    # Если use_weighted_sampler: создаём WeightedRandomSampler только для train
    if use_weighted_sampler and not regression and not entry_path and not trailing_stop_quantile:
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
            replacement=True
        )
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            sampler=sampler,  # Используем sampler вместо shuffle
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available(),
            drop_last=False,
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
        )
        sampler_info = ""

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=False,
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
) -> DataLoader:
    """Только для инференса на отложенной выборке. StandardScaler отключён (False)."""
    print("\n📦 Загрузка тестовых данных...")
    seq_len = validate_seq_len_for_target(target, seq_len)
    regression = (
        (target in SINGLE_REGRESSION_COLUMNS)
        or (target == UPDN_REGRESSION_TARGET)
        or (target == TRAILING_STOP_TARGET)
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
    prefix = 'test'
    missing_entry_path_labels = False

    x_path = DATA_DIR / f'X_{prefix}{profile_suffix}.npy'
    mask_path = DATA_DIR / f'mask_{prefix}{profile_suffix}.npy'
    if entry_path:
        engineered_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_engineered{profile_suffix}.npy'
        y_reg_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_reg{profile_suffix}.npy'
        y_cls_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_cls{profile_suffix}.npy'
        signal_path = DATA_DIR / f'y_{prefix}_{ENTRY_PATH_TARGET}_signal{profile_suffix}.npy'
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
            if X.shape[2] != N_FRACTAL_FEATURES:
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
                        or engineered.shape[1] != len(ENTRY_PATH_V1_FEATURE_COLUMNS)
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
            engineered = split_entry_path_features(df)
    elif trailing_stop:
        y = split_trailing_stop_targets(df)
    elif trailing_stop_quantile:
        y = split_trailing_stop_quantile_target(df)
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
