# =============================================================================
# Файл: data_loader.py
# Назначение: Dataset и DataLoader для фрактальных последовательностей с кэшированием тензоров
# Язык: Python 3.11+
# Обновлён: 2026-03-19
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
#   - N_RAW_FEATURES=18: поле 17 (fractal_atr) → log(ATR_ratio) = log(fractal_atr / Atr.Slow)
#   - N_FRACTAL_FEATURES=20: 17 исходных + 3 time-фичи (hour_sin, hour_cos, time_pos); форма X: (n, 100, 20)
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


# ─── Константы ───────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'DATA'

TRAIN_FILE = DATA_DIR / 'Nero_train_labeled.csv'
VAL_FILE = DATA_DIR / 'Nero_validation_labeled.csv'
TEST_FILE = DATA_DIR / 'Nero_test_labeled.csv'

CSV_SEP = ';'
FRACTAL_SEP = ':'
N_FRACTALS = 100
N_RAW_FEATURES = 18   # T:P:Dir:FrntVal:BackVal:Strong:Brk:Rev:PwrSum:Cnt:Imp:Up12:Dn12:Up24:Dn24:Up48:Dn48:FractalAtr
N_FRACTAL_FEATURES = 20  # 17 исходных (fields 1-17) + 3 time-фичи (hour_sin, hour_cos, time_pos)

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

# Доступные up/dn таргеты
UPDN_TARGETS = ['up_12', 'dn_12', 'up_24', 'dn_24', 'up_48', 'dn_48']

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


# ─── Парсинг данных ──────────────────────────────────────────────────────────

def parse_fractals_to_3d(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """
    Векторизованный парсинг фракталов в 3D тензор + padding mask.

    Парсит колонки fractal0..fractal99 из DataFrame.
    Исключает fractal_time (индекс 0) из features.
    Парсит 18 полей на фрактал; поле 17 (fractal_atr) заменяется ATR_ratio in-place.

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

    # 20 features: 17 из CSV (fields 1-17) + 3 time-фичи (вычисляются из fractal_time)
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

        if split.shape[1] == N_RAW_FEATURES:
            # Парсим все 18 полей: fractal_time → отдельный массив, остальные → X
            for k in range(N_RAW_FEATURES):
                if k == FRACTAL_TIME_IDX:
                    vals = pd.to_numeric(split[k], errors='coerce')
                    fractal_times[:, j] = vals.fillna(0).values
                    continue
                # Сдвигаем индекс: k=1 → 0, k=2 → 1, ..., k=17 → 16
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
        signal: np.ndarray | None = None,
    ):
        self.X = torch.from_numpy(X).float()
        if regression:
            # Регрессия: y — float, маппинг не нужен
            self.y = torch.from_numpy(y.astype(np.float32)).float()
        else:
            # Классификация: маппинг {-1, 0, 1} → {0, 1, 2}
            y_mapped = np.array([LABEL_MAP[label] for label in y], dtype=np.int64)
            self.y = torch.from_numpy(y_mapped).long()
        self.mask = torch.from_numpy(mask).bool()
        self.signal = torch.from_numpy(signal).long() if signal is not None else None

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, idx: int):
        if self.signal is not None:
            return self.X[idx], self.y[idx], self.mask[idx], self.signal[idx]
        return self.X[idx], self.y[idx], self.mask[idx]


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
    regression = (target == REGRESSION_TARGET) or (target == UPDN_REGRESSION_TARGET)
    multi_target = (target == UPDN_REGRESSION_TARGET)
    triple_barrier = (target == TB_TARGET)

    def load_or_parse_data(csv_file: Path, target_col: str, prefix: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        x_path = DATA_DIR / f'X_{prefix}.npy'
        mask_path = DATA_DIR / f'mask_{prefix}.npy'
        y_path = DATA_DIR / f'y_{prefix}_{target_col}.npy'

        # Список всех файлов кэша для данного набора
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
                    y = np.load(y_path)
                    return X, mask, y

        print(f"  Кэш не найден. Загрузка {csv_file.name} и парсинг...")
        df = pd.read_csv(csv_file, sep=CSV_SEP, low_memory=False)
        
        # Извлечение таргета
        if multi_target:
            y = df[UPDN_TARGETS].values.astype(np.float32)  # shape (n, 6)
        elif triple_barrier:
            y = df[TB_TARGET_NAMES].values.astype(np.float32)  # shape (n, 12)
            y = np.where(y == 0.5, 0.0, y)  # TIMEOUT → LOSS (didn't reach TP in scan window)
        elif regression:
            y = np.abs(df[target_col].values.astype(np.float32))
        else:
            y = df[target_col].values.astype(int)
            
        print(f"  🔧 Парсинг фракталов в 3D тензоры ({prefix})...")
        X, mask = parse_fractals_to_3d(df)
        
        # Сохранение кэша
        np.save(x_path, X)
        np.save(mask_path, mask)
        np.save(y_path, y)
        print(f"  ✅ Данные {prefix} сохранены в кэш.")
        
        return X, mask, y

    X_train, mask_train, y_train = load_or_parse_data(TRAIN_FILE, target, 'train')
    X_val, mask_val, y_val = load_or_parse_data(VAL_FILE, target, 'val')

    # Signal column для directional asymmetric loss (regression_updn only)
    signal_train = signal_val = None
    if multi_target:
        signal_train = pd.read_csv(TRAIN_FILE, sep=CSV_SEP, usecols=['signal'])['signal'].values.astype(np.int64)
        signal_val = pd.read_csv(VAL_FILE, sep=CSV_SEP, usecols=['signal'])['signal'].values.astype(np.int64)

    # Truncate sequence length if requested
    if seq_len < 100:
        print(f"  ✂️ Усечение последовательности фракталов до {seq_len} (оставляем самые недавние)")
        # Фракталы записаны: 0 - самый новый, 99 - самый старый
        X_train = X_train[:, :seq_len, :]
        mask_train = mask_train[:, :seq_len]
        X_val = X_val[:, :seq_len, :]
        mask_val = mask_val[:, :seq_len]

    print(f"  Train: {len(y_train)} строк, Val: {len(y_val)} строк")

    if multi_target:
        for name, y in [('Train', y_train), ('Val', y_val)]:
            print(f"  {name} updn targets: shape={y.shape}")
            for i, col in enumerate(UPDN_TARGETS):
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
    train_dataset = FractalSequenceDataset(
        X_train_norm, y_train, mask_train,
        regression=(regression or triple_barrier),
        signal=signal_train,
    )
    val_dataset = FractalSequenceDataset(
        X_val_norm, y_val, mask_val,
        regression=(regression or triple_barrier),
        signal=signal_val,
    )

    # Если use_weighted_sampler: создаём WeightedRandomSampler только для train
    if use_weighted_sampler and not regression:
        # Рассчитываем веса: 1 / freq(class)
        # Отображаем {-1, 0, 1} → {0, 1, 2} для np.bincount()
        # Векторизованное преобразование меток
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
    regression = (target == REGRESSION_TARGET) or (target == UPDN_REGRESSION_TARGET)
    multi_target = (target == UPDN_REGRESSION_TARGET)
    triple_barrier = (target == TB_TARGET)
    prefix = 'test'
    
    x_path = DATA_DIR / f'X_{prefix}.npy'
    mask_path = DATA_DIR / f'mask_{prefix}.npy'
    y_path = DATA_DIR / f'y_{prefix}_{target}.npy'
    cache_files = [x_path, mask_path, y_path]
    
    if clear_cache:
        print(f"  🧹 Принудительная очистка кэша ({prefix})...")
        for f in cache_files:
            if f.exists(): f.unlink()
    elif all(f.exists() for f in cache_files):
        csv_mtime = TEST_FILE.stat().st_mtime
        if any(csv_mtime > f.stat().st_mtime for f in cache_files):
            print(f"  🔄 Файл {TEST_FILE.name} обновился. Инвалидация кэша {prefix}...")
            for f in cache_files: f.unlink()
        else:
            X = np.load(x_path)
            if X.shape[2] != N_FRACTAL_FEATURES:
                print(f"  🔄 Кэш {prefix} устарел. Инвалидация...")
                for f in cache_files: f.unlink()
            else:
                print(f"  Загрузка кэшированных данных {prefix} из .npy...")
                mask = np.load(mask_path)
                y = np.load(y_path)
                
                if seq_len < 100:
                    X = X[:, :seq_len, :]
                    mask = mask[:, :seq_len]
                
                dataset = FractalSequenceDataset(X, y, mask, regression=(regression or triple_barrier))
                return DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    print(f"  Кэш не найден. Загрузка {TEST_FILE.name} и парсинг...")
    df = pd.read_csv(TEST_FILE, sep=CSV_SEP, low_memory=False)
    
    if multi_target:
        y = df[UPDN_TARGETS].values.astype(np.float32)
    elif triple_barrier:
        y = df[TB_TARGET_NAMES].values.astype(np.float32)
        y = np.where(y == 0.5, 0.0, y)  # TIMEOUT → LOSS
    elif regression:
        y = np.abs(df[target].values.astype(np.float32))
    else:
        y = df[target].values.astype(int)
        
    X, mask = parse_fractals_to_3d(df)
    np.save(x_path, X)
    np.save(mask_path, mask)
    np.save(y_path, y)
    print(f"  ✅ Данные {prefix} сохранены в кэш.")
    
    if seq_len < 100:
        X = X[:, :seq_len, :]
        mask = mask[:, :seq_len]
        
    dataset = FractalSequenceDataset(X, y, mask, regression=(regression or triple_barrier))
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
