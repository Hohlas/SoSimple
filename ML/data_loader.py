# =============================================================================
# Файл: data_loader.py
# Назначение: Dataset и DataLoader для фрактальных последовательностей
# Язык: Python 3.11+
# Обновлён: 2026-02-18
# Зависимости:
#   Входные данные:
#     - DATA/Nero_train_labeled.csv (откуда: processing/label_main.py)
#     - DATA/Nero_validation_labeled.csv (откуда: processing/label_main.py)
#   Выходные данные: нет (in-memory Dataset/DataLoader)
# Внешние зависимости:
#   - torch>=2.0
#   - pandas>=2.0
#   - numpy>=1.24
#   - scikit-learn>=1.2
# Использование:
#   from ML.data_loader import create_data_loaders
# Примечания:
#   - fractal_time (индекс 0) исключается из features — может дать data leakage
#   - ATR broadcast на все 100 позиций как 11-й признак
#   - StandardScaler fit на train, transform на val
#   - Нормализация по каждому feature индексу отдельно
# =============================================================================

"""
Dataset и DataLoader для фрактальных последовательностей.

Парсит CSV с фракталами в 3D тензоры (n_samples, 100, 11),
исключает fractal_time, добавляет ATR, нормализует features.
Создаёт padding mask для Transformer (NaN позиции).
"""

from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler


# ─── Константы ───────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'DATA'

TRAIN_FILE = DATA_DIR / 'Nero_train_labeled.csv'
VAL_FILE = DATA_DIR / 'Nero_validation_labeled.csv'

CSV_SEP = ';'
FRACTAL_SEP = ':'
N_FRACTALS = 100
N_RAW_FEATURES = 11   # Всего полей в строке фрактала (включая fractal_time)
N_FRACTAL_FEATURES = 10  # Без fractal_time → price..impulse

# Индекс fractal_time в сырых данных (исключается)
FRACTAL_TIME_IDX = 0

# Маппинг меток: signal {-1, 0, 1} → индексы {0, 1, 2}
LABEL_MAP = {-1: 0, 0: 1, 1: 2}
INV_LABEL_MAP = {v: k for k, v in LABEL_MAP.items()}


# ─── Парсинг данных ──────────────────────────────────────────────────────────

def parse_fractals_to_3d(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """
    Векторизованный парсинг фракталов в 3D тензор + padding mask.

    Парсит колонки fractal0..fractal99 из DataFrame.
    Исключает fractal_time (индекс 0) из features.
    Добавляет ATR как 11-й признак (broadcast на все 100 позиций).

    Аргументы:
        df: DataFrame с колонками fractal0..fractal99, ATR, signal

    Возвращает:
        Кортеж (X, mask):
        - X: np.ndarray shape (n_samples, 100, 11) — 10 фрактальных + ATR.
             Feature order: price, direction, front, back, strong, break,
             reverse, power, count, impulse, ATR
        - mask: np.ndarray shape (n_samples, 100) — True для валидных позиций,
                False для padding (все features == 0)
    """
    fractal_cols = [f'fractal{i}' for i in range(N_FRACTALS)]
    n_samples = len(df)

    # 10 фрактальных features (без fractal_time) + 1 ATR = 11
    n_features = N_FRACTAL_FEATURES + 1
    X = np.zeros((n_samples, N_FRACTALS, n_features), dtype=np.float32)
    # Маска валидности: True если фрактал присутствует (не все NaN)
    raw_valid = np.ones((n_samples, N_FRACTALS), dtype=bool)

    for j, col in enumerate(fractal_cols):
        if j % 20 == 0:
            print(f"    парсинг fractal columns {j}-{min(j + 19, N_FRACTALS - 1)}...")

        series = df[col].astype(str)
        split = series.str.split(FRACTAL_SEP, expand=True)

        if split.shape[1] == N_RAW_FEATURES:
            # Парсим все 11 полей, затем исключаем fractal_time (индекс 0)
            for k in range(N_RAW_FEATURES):
                if k == FRACTAL_TIME_IDX:
                    continue
                # Сдвигаем индекс: k=1 → 0, k=2 → 1, ..., k=10 → 9
                feat_idx = k - 1
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

    # ATR как 11-й признак (индекс 10), broadcast на все позиции
    atr_values = pd.to_numeric(df['ATR'], errors='coerce').fillna(0).values.astype(np.float32)
    X[:, :, N_FRACTAL_FEATURES] = atr_values[:, np.newaxis]

    # Финальная маска: True для валидных (non-padding) позиций
    mask = raw_valid

    # NaN → 0
    X = np.nan_to_num(X, nan=0.0).astype(np.float32)

    return X, mask


def normalize_features(
    X_train: np.ndarray,
    X_val: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, StandardScaler]:
    """
    Нормализация features с помощью StandardScaler.

    Fit на train, transform на val. Нормализуется по каждому feature индексу
    отдельно по всему train. Для этого flatten: (n_samples * seq_len, n_features).

    Аргументы:
        X_train: shape (n_train, 100, 11)
        X_val: shape (n_val, 100, 11)

    Возвращает:
        Кортеж (X_train_norm, X_val_norm, scaler):
        - X_train_norm: shape (n_train, 100, 11) нормализованный train
        - X_val_norm: shape (n_val, 100, 11) нормализованный val
        - scaler: обученный StandardScaler
    """
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
    - X: tensor shape (seq_len=100, features=11)
    - y: tensor scalar — метка класса (0, 1 или 2 после маппинга)
    - mask: tensor shape (seq_len=100) — True для валидных позиций

    Аргументы:
        X: np.ndarray shape (n_samples, 100, 11) — нормализованные features
        y: np.ndarray shape (n_samples,) — метки {-1, 0, 1}
        mask: np.ndarray shape (n_samples, 100) — padding mask
    """

    def __init__(self, X: np.ndarray, y: np.ndarray, mask: np.ndarray):
        self.X = torch.from_numpy(X).float()
        # Маппинг меток: {-1, 0, 1} → {0, 1, 2}
        y_mapped = np.array([LABEL_MAP[label] for label in y], dtype=np.int64)
        self.y = torch.from_numpy(y_mapped).long()
        self.mask = torch.from_numpy(mask).bool()

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.X[idx], self.y[idx], self.mask[idx]


# ─── Фабрика DataLoader'ов ───────────────────────────────────────────────────

def create_data_loaders(
    batch_size: int = 256,
    num_workers: int = 0,
) -> tuple[DataLoader, DataLoader, StandardScaler]:
    """
    Создание train и val DataLoader'ов.

    Полный pipeline: загрузка CSV → парсинг 3D → нормализация → Dataset → DataLoader.

    Аргументы:
        batch_size: Размер батча (по умолчанию 256)
        num_workers: Количество worker'ов для загрузки данных

    Возвращает:
        Кортеж (train_loader, val_loader, scaler):
        - train_loader: DataLoader (shuffle=True)
        - val_loader: DataLoader (shuffle=False)
        - scaler: обученный StandardScaler для последующего использования

    Пример:
        >>> train_loader, val_loader, scaler = create_data_loaders(batch_size=256)
        >>> for X_batch, y_batch, mask_batch in train_loader:
        ...     # X_batch: (256, 100, 11), y_batch: (256,), mask_batch: (256, 100)
        ...     logits = model(X_batch, mask_batch)
    """
    print("📦 Загрузка данных...")

    # ── Загрузка CSV ─────────────────────────────────────────────────────────
    df_train = pd.read_csv(TRAIN_FILE, sep=CSV_SEP, low_memory=False)
    df_val = pd.read_csv(VAL_FILE, sep=CSV_SEP, low_memory=False)
    print(f"  Train: {len(df_train)} строк, Val: {len(df_val)} строк")

    # ── Извлечение меток ─────────────────────────────────────────────────────
    y_train = df_train['signal'].values.astype(int)
    y_val = df_val['signal'].values.astype(int)

    # Проверка распределения классов
    for name, y in [('Train', y_train), ('Val', y_val)]:
        classes, counts = np.unique(y, return_counts=True)
        total = len(y)
        dist_str = ", ".join(
            [f"{c}: {cnt} ({cnt / total * 100:.1f}%)" for c, cnt in zip(classes, counts)]
        )
        print(f"  {name}: {dist_str}")

    # ── Парсинг фракталов в 3D тензоры ───────────────────────────────────────
    print("\n🔧 Парсинг фракталов в 3D тензоры...")
    print("  Train...")
    X_train, mask_train = parse_fractals_to_3d(df_train)
    print(f"  ✅ Train: X={X_train.shape}, mask={mask_train.shape}")

    print("  Validation...")
    X_val, mask_val = parse_fractals_to_3d(df_val)
    print(f"  ✅ Val: X={X_val.shape}, mask={mask_val.shape}")

    # ── Нормализация ─────────────────────────────────────────────────────────
    print("\n📏 Нормализация features (StandardScaler, fit на train)...")
    X_train_norm, X_val_norm, scaler = normalize_features(X_train, X_val)
    print(f"  ✅ Нормализация завершена")

    # ── Создание Dataset и DataLoader ────────────────────────────────────────
    train_dataset = FractalSequenceDataset(X_train_norm, y_train, mask_train)
    val_dataset = FractalSequenceDataset(X_val_norm, y_val, mask_val)

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,       # Каждая строка — независимый snapshot, shuffle допустим
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=False,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=False,
    )

    print(f"\n✅ DataLoaders: train={len(train_loader)} batches, "
          f"val={len(val_loader)} batches (batch_size={batch_size})")

    return train_loader, val_loader, scaler
