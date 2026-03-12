# =============================================================================
# Файл: feature_engineering.py
# Назначение: Добавление новых динамических признаков к фрактальным данным
# Язык: Python 3.11+
# Обновлён: 2026-03-12
# Зависимости:
#   Входные данные:
#     - 3D тензор X из data_loader.py (сигналы: price, direction, front, back, etc.)
#   Выходные данные:
#     - Расширенный 3D тензор X_new с новыми признаками
# Использование:
#   from ML.feature_engineering import enrich_features
#   X_enriched = enrich_features(X_raw)
# =============================================================================

import numpy as np

# Индексы базовых фичей из N_FRACTAL_FEATURES_ORDER в data_loader.py:
# order: price (0), direction (1), front (2), back (3), strong (4), break (5),
# reverse (6), power (7), count (8), impulse (9), ATR (10)
IDX_PRICE = 0
IDX_DIR = 1
IDX_FRONT = 2
IDX_BACK = 3
IDX_IMPULSE = 9
IDX_ATR = 10

def enrich_features(X: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Добавляет инженерные признаки (ME-3) в 3D тензор сырых данных.

    Аргументы:
        X: np.ndarray shape (n_samples, seq_len, N_FEATURES=11)
        mask: np.ndarray shape (n_samples, seq_len) — маска валидных фракталов

    Возвращает:
        X_new: np.ndarray shape (n_samples, seq_len, N_FEATURES + NEW_FEATURES)
    """
    n_samples, seq_len, n_features = X.shape
    
    # Инициализация списков новых фичей (чтобы потом собрать их через dstack или concatenate)
    new_features = []
    
    # 1. Price Momentum (Дельта цены между фракталами: цена текущего - цена предыдущего)
    # Помним, что фракталы идут от нового (0) к старому (seq_len-1).
    # Дельта цены[i] = price[i] - price[i+1] (насколько мы сдвинулись от предыдущего)
    price = X[:, :, IDX_PRICE]
    price_shifted = np.roll(price, shift=-1, axis=1)
    price_shifted[:, -1] = price[:, -1] # Заполняем NaN на последнем валидном значении, чтобы не было скачка в 0.
    
    price_momentum = price - price_shifted
    
    # Зануляем momentum там, где padding (чтобы не дать сети ложных сигналов на стыке с NaN)
    # И там, где shift зашел за край валидных данных (mask shift).
    mask_shifted = np.roll(mask, shift=-1, axis=1)
    mask_shifted[:, -1] = False
    
    # Считаем momentum валидным, только если оба фрактала валидны
    valid_momentum = mask & mask_shifted
    price_momentum = np.where(valid_momentum, price_momentum, 0.0)
    new_features.append(price_momentum)
    
    # 2. Относительные фичи: нормировка на ATR
    # front/ATR, back/ATR, impulse/ATR, momentum/ATR
    atr = X[:, :, IDX_ATR]
    # Защита от деления на 0:
    atr_safe = np.where(atr > 1e-6, atr, 1.0)
    
    front_norm = X[:, :, IDX_FRONT] / atr_safe
    back_norm = X[:, :, IDX_BACK] / atr_safe
    impulse_norm = X[:, :, IDX_IMPULSE] / atr_safe
    momentum_norm = price_momentum / atr_safe
    
    new_features.append(front_norm)
    new_features.append(back_norm)
    new_features.append(impulse_norm)
    new_features.append(momentum_norm)
    
    # 3. Скользящие средние (Rolling means)
    # Вычислим MA(3) для momentum_norm
    ma3_momentum = np.zeros_like(momentum_norm)
    for i in range(seq_len):
        # Окно по фракталам от 0 до i+2
        # i..i+2 означает [i, i+1, i+2]
        window = momentum_norm[:, i:min(i+3, seq_len)]
        ma3_momentum[:, i] = np.mean(window, axis=1)
        
    new_features.append(ma3_momentum)
    
    # ─── Сборка ──────────────────────────────────────────────────────────────
    # Объединяем старые и новые фичи.
    # Стакаем вдоль последней оси.
    new_features_array = np.stack(new_features, axis=2)
    X_enriched = np.concatenate([X, new_features_array], axis=2)
    
    # Гарантируем, что весь padding строго 0.0
    X_enriched = np.where(mask[:, :, np.newaxis], X_enriched, 0.0)
    
    return X_enriched.astype(np.float32)
