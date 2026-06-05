# =============================================================================
# Файл: baseline_experiments.py
# Назначение: Baseline-модели для классификации signal ∈ {-1, 0, 1}
# Язык: Python 3.10+
# Обновлён: 2026-02-18
# Зависимости:
#   Входные данные:
#     - DATA/Nero_train_labeled.csv (откуда: processing/label_main.py)
#     - DATA/Nero_validation_labeled.csv (откуда: processing/label_main.py)
#     - statistics/nero_features_engineered.csv (откуда: statistics/EDA.ipynb)
#     - statistics/feature_catalog.json (откуда: statistics/EDA.ipynb)
#   Выходные данные:
#     - ML/plots/baseline_cm_*.png (confusion matrices)
#     - ML/reports/baseline_report.md (отчёт с результатами)
# Внешние зависимости:
#   - pandas>=2.0
#   - numpy>=1.24
#   - scikit-learn>=1.2
#   - lightgbm>=4.0
#   - xgboost>=2.0
#   - matplotlib>=3.7
#   - seaborn>=0.12
# Использование:
#   python -m ML.baseline.baseline_experiments
# Примечания:
#   - Данные НЕ перемешиваются (time-series!)
#   - Основная метрика: macro F1-score
#   - Accuracy НЕ используется как основная (дисбаланс классов)
# =============================================================================

"""
Baseline ML эксперименты для классификации signal ∈ {-1, 0, 1}.

Сравнение 5 моделей: DummyClassifier, LogisticRegression, RandomForest,
XGBoost и LightGBM. Метрики: macro F1, classification report, confusion matrix,
ROC-AUC (OVR).
"""

import os
import sys
import json
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    f1_score, classification_report, confusion_matrix,
    roc_auc_score, accuracy_score
)

import xgboost as xgb
import lightgbm as lgb

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# ─── Константы ───────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / 'DATA'
STATS_DIR = PROJECT_ROOT / 'statistics'
ML_DIR = PROJECT_ROOT / 'ML'
BASELINE_DIR = ML_DIR / 'baseline'
PLOTS_DIR = BASELINE_DIR / 'plots'
REPORTS_DIR = BASELINE_DIR / 'reports'

# Import experiment logger (after PROJECT_ROOT is defined)
from ML.experiment_logger import CSVExperimentLogger

TRAIN_FILE = DATA_DIR / 'Nero_train_labeled.csv'
VAL_FILE = DATA_DIR / 'Nero_validation_labeled.csv'
ENGINEERED_FEATURES_FILE = STATS_DIR / 'nero_features_engineered.csv'
FEATURE_CATALOG_FILE = STATS_DIR / 'feature_catalog.json'

CSV_SEP = ';'
FRACTAL_SEP = ':'
N_FRACTALS = 100
N_FRACTAL_FEATURES = 11

FEATURE_NAMES = [
    'fractal_time', 'price', 'direction', 'front', 'back',
    'strong', 'break', 'reverse', 'power', 'count', 'impulse'
]

# Индексы в 3D тензоре
PRICE_IDX = 1
DIRECTION_IDX = 2
FRONT_IDX = 3
BACK_IDX = 4
POWER_IDX = 8
COUNT_IDX = 9
IMPULSE_IDX = 10
REVERSE_IDX = 7

# 10 избыточных признаков из EDA (корреляция > 0.95)
REDUNDANT_FEATURES = [
    'impulse_max_w2', 'price_max_w1', 'front_mean_w1',
    'impulse_mean_w1', 'front_max_w1', 'price_momentum_5',
    'price_min_w1', 'front_std_w3', 'impulse_max_w1', 'price_slope_10'
]


# ═══════════════════════════════════════════════════════════════════════════════
# РАЗДЕЛ 1. ЗАГРУЗКА И ПАРСИНГ ДАННЫХ
# ═══════════════════════════════════════════════════════════════════════════════

def load_data(filepath: Path) -> pd.DataFrame:
    """
    Загрузка CSV с разделителем ';'. Без перемешивания (time-series).

    Аргументы:
        filepath: Путь к CSV файлу

    Возвращает:
        DataFrame с колонками time, signal, predict, ATR, fractal0..fractal99
    """
    df = pd.read_csv(filepath, sep=CSV_SEP, low_memory=False)
    print(f"  Загружено: {len(df)} строк, {len(df.columns)} колонок из {filepath.name}")
    return df


def parse_fractal_string(fractal_str: str) -> np.ndarray:
    """
    Парсинг строки фрактала 'time:price:direction:...' в массив из 11 чисел.

    Аргументы:
        fractal_str: Строка формата 'val1:val2:...:val11'

    Возвращает:
        np.ndarray shape (11,) с числовыми значениями, NaN при ошибке
    """
    if pd.isna(fractal_str) or str(fractal_str).strip() == '':
        return np.full(N_FRACTAL_FEATURES, np.nan)
    try:
        parts = str(fractal_str).split(FRACTAL_SEP)
        if len(parts) != N_FRACTAL_FEATURES:
            return np.full(N_FRACTAL_FEATURES, np.nan)
        return np.array([float(p) for p in parts])
    except (ValueError, TypeError):
        return np.full(N_FRACTAL_FEATURES, np.nan)


def parse_fractals_to_3d(df: pd.DataFrame) -> np.ndarray:
    """
    Парсинг всех фракталов в 3D тензор (векторизованная версия).

    Аргументы:
        df: DataFrame с колонками fractal0..fractal99

    Возвращает:
        np.ndarray shape (n_samples, 100, 11), NaN заполнены нулями
    """
    fractal_cols = [f'fractal{i}' for i in range(N_FRACTALS)]
    n_samples = len(df)
    X = np.zeros((n_samples, N_FRACTALS, N_FRACTAL_FEATURES))

    for j, col in enumerate(fractal_cols):
        if j % 20 == 0:
            print(f"    parsing fractal columns {j}-{min(j+19, N_FRACTALS-1)}...")

        series = df[col].astype(str)
        # Разбиваем по ':' и конвертируем в числа
        split = series.str.split(FRACTAL_SEP, expand=True)
        if split.shape[1] == N_FRACTAL_FEATURES:
            for k in range(N_FRACTAL_FEATURES):
                X[:, j, k] = pd.to_numeric(split[k], errors='coerce').fillna(0).values
        else:
            # Если формат неожиданный — парсим поэлементно
            for i in range(n_samples):
                X[i, j, :] = parse_fractal_string(df.iloc[i][col])

    # NaN → 0
    X = np.nan_to_num(X, nan=0.0)
    return X


# ═══════════════════════════════════════════════════════════════════════════════
# РАЗДЕЛ 2. FEATURE ENGINEERING
# ═══════════════════════════════════════════════════════════════════════════════

def extract_flat_features(df: pd.DataFrame, X_3d: np.ndarray) -> pd.DataFrame:
    """
    Извлечение «плоских» признаков: 11 признаков fractal[0] + ATR + циклические time.

    Используется для LogReg и RandomForest.

    Аргументы:
        df: Исходный DataFrame (для ATR и time)
        X_3d: 3D тензор (n_samples, 100, 11)

    Возвращает:
        DataFrame с ~16 признаками
    """
    features = {}

    # 11 признаков fractal[0] (без fractal_time — не информативен как абсолютное значение)
    for idx, name in enumerate(FEATURE_NAMES):
        if name == 'fractal_time':
            continue
        features[name] = X_3d[:, 0, idx]

    # ATR
    features['ATR'] = df['ATR'].values.astype(float)

    # Циклические временные признаки из строки time
    times = pd.to_datetime(df['time'], format='%Y.%m.%d %H:%M', errors='coerce')

    hours = times.dt.hour.fillna(0).values
    features['hour_sin'] = np.sin(2 * np.pi * hours / 24)
    features['hour_cos'] = np.cos(2 * np.pi * hours / 24)

    dow = times.dt.dayofweek.fillna(0).values
    features['dow_sin'] = np.sin(2 * np.pi * dow / 7)
    features['dow_cos'] = np.cos(2 * np.pi * dow / 7)

    return pd.DataFrame(features)


def extract_engineered_features(X_3d: np.ndarray, df: pd.DataFrame) -> pd.DataFrame:
    """
    Вычисление 233 engineered features из 3D тензора (векторизованная версия).
    Воспроизводит логику из statistics/EDA.ipynb -> engineer_sequence_features().

    Аргументы:
        X_3d: 3D тензор (n, 100, 11)
        df: Исходный DataFrame (для time)

    Возвращает:
        DataFrame с ~233 признаками (без signal, row_idx, time)
    """
    n_samples = len(X_3d)
    features = {}

    print("    A. Rolling Statistics...")
    # ── A. Rolling Statistics (уже векторизовано) ─────────────────────────────
    windows = [1, 2, 3, 4, 5, 10, 20]
    feat_names_rolling = ['price', 'front', 'back', 'power', 'impulse', 'count']
    feat_indices_rolling = [PRICE_IDX, FRONT_IDX, BACK_IDX, POWER_IDX, IMPULSE_IDX, COUNT_IDX]

    for window in windows:
        for fname, fidx in zip(feat_names_rolling, feat_indices_rolling):
            data = X_3d[:, :window, fidx]  # (n, window)
            features[f'{fname}_mean_w{window}'] = np.nanmean(data, axis=1)
            features[f'{fname}_std_w{window}'] = np.nanstd(data, axis=1)
            features[f'{fname}_min_w{window}'] = np.nanmin(data, axis=1)
            features[f'{fname}_max_w{window}'] = np.nanmax(data, axis=1)

    print("    B. Trend Indicators...")
    # ── B. Trend Indicators (vectorized slopes) ──────────────────────────────
    N_values = [2, 3, 4, 5, 10]
    trend_names = ['price', 'power', 'impulse']
    trend_indices = [PRICE_IDX, POWER_IDX, IMPULSE_IDX]

    for N in N_values:
        x = np.arange(N, dtype=float)
        x_mean = x.mean()
        x_var = np.sum((x - x_mean) ** 2)

        for fname, fidx in zip(trend_names, trend_indices):
            data = X_3d[:, :N, fidx]  # (n_samples, N)
            y_mean = np.nanmean(data, axis=1, keepdims=True)
            # slope = sum((x - x_mean)(y - y_mean)) / sum((x - x_mean)^2)
            slopes = np.nansum((x[np.newaxis, :] - x_mean) * (data - y_mean), axis=1) / x_var
            slopes = np.nan_to_num(slopes, nan=0.0)
            features[f'{fname}_slope_{N}'] = slopes

    print("    C. Directional Patterns...")
    # ── C. Directional Patterns (vectorized) ─────────────────────────────────
    for N in [3, 5, 10, 20]:
        dirs = X_3d[:, :N, DIRECTION_IDX]  # (n_samples, N)

        # Direction changes: count transitions
        changes = dirs[:, :-1] != dirs[:, 1:]
        # Exclude transitions involving 0 (padding)
        valid_pair = (dirs[:, :-1] != 0) & (dirs[:, 1:] != 0)
        dir_changes = np.sum(changes & valid_pair, axis=1).astype(float)

        # Peak/valley ratio
        peaks = np.sum(dirs == 1, axis=1).astype(float)
        valleys = np.sum(dirs == -1, axis=1).astype(float)
        peak_ratios = np.where(valleys > 0, peaks / valleys,
                               np.where(peaks > 0, peaks, 0.0))

        # Longest streak — vectorized приближение: O(N) циклов, не O(n_samples*N)
        longest_s = np.ones(n_samples)
        current_s = np.ones(n_samples)
        for j in range(1, N):
            same = (dirs[:, j] == dirs[:, j-1]) & (dirs[:, j] != 0) & (dirs[:, j-1] != 0)
            current_s = np.where(same, current_s + 1, 1)
            longest_s = np.maximum(longest_s, current_s)

        # Majority direction match
        majority_dir = np.where(peaks > valleys, 1.0, -1.0)
        first_dir = dirs[:, 0]
        majority_match = (first_dir == majority_dir).astype(float)

        features[f'direction_changes_w{N}'] = dir_changes
        features[f'peak_valley_ratio_w{N}'] = peak_ratios
        features[f'longest_streak_w{N}'] = longest_s
        features[f'majority_direction_match_w{N}'] = majority_match

    print("    D. Relative Features...")
    # ── D. Relative Features (vectorized z-score, percentile) ────────────────
    for window in [10, 20]:
        for fname, fidx in zip(['price', 'power'], [PRICE_IDX, POWER_IDX]):
            w_data = X_3d[:, :window, fidx]  # (n, window)
            cur = X_3d[:, 0, fidx]  # (n,)
            m = np.nanmean(w_data, axis=1)
            s = np.nanstd(w_data, axis=1)
            z_scores = np.where(s > 0, (cur - m) / s, 0.0)
            z_scores = np.nan_to_num(z_scores, nan=0.0)

            # Percentile: fraction of window values <= current
            # Broadcasting: cur[:, None] vs w_data (n, window)
            pct = np.nansum(w_data <= cur[:, np.newaxis], axis=1) / window * 100
            pct = np.nan_to_num(pct, nan=0.0)

            features[f'{fname}_zscore_w{window}'] = z_scores
            features[f'{fname}_percentile_w{window}'] = pct

    print("    E. Support/Resistance...")
    # ── E. Support/Resistance (vectorized) ───────────────────────────────────
    for window in [3, 5, 10, 20]:
        w_prices = X_3d[:, :window, PRICE_IDX]  # (n, window)
        cur_price = X_3d[:, 0, PRICE_IDX][:, np.newaxis]  # (n, 1)
        p_min = np.nanmin(w_prices, axis=1, keepdims=True)
        p_max = np.nanmax(w_prices, axis=1, keepdims=True)
        p_range = p_max - p_min
        thresh = 0.02 * p_range  # (n, 1)
        # Count how many prices are within threshold
        sr = np.sum(
            (np.abs(w_prices - cur_price) < thresh) & (thresh > 0),
            axis=1
        ).astype(float)
        features[f'support_resistance_w{window}'] = sr

    print("    F. Momentum & Volatility...")
    # ── F. Momentum & Volatility (vectorized) ────────────────────────────────
    for N in [5, 10, 20]:
        # Cumulative direction
        dirs_n = X_3d[:, :N, DIRECTION_IDX]
        features[f'cumulative_direction_{N}'] = np.nansum(dirs_n, axis=1)

        # Price momentum: (first - last) / N
        prices_n = X_3d[:, :N, PRICE_IDX]
        features[f'price_momentum_{N}'] = (prices_n[:, 0] - prices_n[:, -1]) / N

        # Volatility proxy (CV = std / mean)
        p_mean = np.nanmean(prices_n, axis=1)
        p_std = np.nanstd(prices_n, axis=1)
        vols = np.where(p_mean > 0, p_std / p_mean, 0.0)
        features[f'volatility_proxy_{N}'] = vols

        # ATR analog: mean(|diff(prices)|)
        diffs = np.abs(np.diff(prices_n, axis=1))
        features[f'atr_analog_{N}'] = np.nanmean(diffs, axis=1)

    print("    G. Interaction Features...")
    # ── G. Interaction Features ──────────────────────────────────────────────
    features['front_back_interaction'] = X_3d[:, 0, FRONT_IDX] * X_3d[:, 0, BACK_IDX]
    features['power_impulse_interaction'] = X_3d[:, 0, POWER_IDX] * X_3d[:, 0, IMPULSE_IDX]
    features['count_reverse_interaction'] = X_3d[:, 0, COUNT_IDX] * X_3d[:, 0, REVERSE_IDX]

    impulse_mean_w10 = np.nanmean(X_3d[:, :10, IMPULSE_IDX], axis=1)
    features['impulse_direction_interaction'] = (
        (X_3d[:, 0, IMPULSE_IDX] - impulse_mean_w10) * X_3d[:, 0, DIRECTION_IDX]
    )

    print("    H. Time-based Features...")
    # ── H. Time-based Features ───────────────────────────────────────────────
    for offset in [1, 2, 3, 4, 5]:
        td = X_3d[:, 0, 0] - X_3d[:, offset, 0]
        td = np.nan_to_num(td, nan=0.0)
        features[f'time_diff_{offset}'] = td

    # Acceleration: (Δt[0→1] - Δt[1→2]) / Δt[1→2]
    dt_01 = X_3d[:, 0, 0] - X_3d[:, 1, 0]
    dt_12 = X_3d[:, 1, 0] - X_3d[:, 2, 0]
    acc = np.zeros(n_samples)
    valid_mask = dt_12 > 0
    acc[valid_mask] = (dt_01[valid_mask] - dt_12[valid_mask]) / dt_12[valid_mask]
    features['time_acceleration'] = acc

    result = pd.DataFrame(features)
    result = result.fillna(0)
    print(f"    ✅ Всего: {result.shape[1]} признаков")
    return result


def remove_redundant_features(df: pd.DataFrame) -> pd.DataFrame:
    """Удаление избыточных признаков (корреляция > 0.95 из EDA)."""
    cols_to_drop = [c for c in REDUNDANT_FEATURES if c in df.columns]
    return df.drop(columns=cols_to_drop)


# ═══════════════════════════════════════════════════════════════════════════════
# РАЗДЕЛ 3. ВЫЧИСЛЕНИЕ SAMPLE WEIGHTS ДЛЯ XGBOOST
# ═══════════════════════════════════════════════════════════════════════════════

def compute_sample_weights(y: np.ndarray) -> np.ndarray:
    """
    Вычисление весов сэмплов для балансировки классов (аналог class_weight='balanced').

    Формула: weight_i = n_samples / (n_classes * n_samples_class_i)
    """
    classes, counts = np.unique(y, return_counts=True)
    n_samples = len(y)
    n_classes = len(classes)
    class_weight = {c: n_samples / (n_classes * cnt) for c, cnt in zip(classes, counts)}
    return np.array([class_weight[yi] for yi in y])


# ═══════════════════════════════════════════════════════════════════════════════
# РАЗДЕЛ 4. ОБУЧЕНИЕ И ОЦЕНКА МОДЕЛЕЙ
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate_model(model, X_val, y_val, model_name: str) -> dict:
    """
    Оценка модели на валидационном наборе.

    Возвращает:
        dict с метриками: f1_macro, accuracy, roc_auc, classification_report, confusion_matrix
    """
    y_pred = model.predict(X_val)

    # ROC-AUC (OVR) — нужны вероятности
    try:
        if hasattr(model, 'predict_proba'):
            y_proba = model.predict_proba(X_val)
        else:
            y_proba = None

        if y_proba is not None and y_proba.shape[1] == 3:
            roc_auc = roc_auc_score(y_val, y_proba, multi_class='ovr', average='macro')
        else:
            roc_auc = None
    except Exception:
        roc_auc = None

    f1_macro = f1_score(y_val, y_pred, average='macro')
    acc = accuracy_score(y_val, y_pred)
    report = classification_report(y_val, y_pred, target_names=['Sell (-1)', 'Neutral (0)', 'Buy (1)'])
    cm = confusion_matrix(y_val, y_pred, labels=[-1, 0, 1])

    result = {
        'model_name': model_name,
        'f1_macro': f1_macro,
        'accuracy': acc,
        'roc_auc': roc_auc,
        'report': report,
        'confusion_matrix': cm,
        'y_pred': y_pred,
    }

    print(f"\n{'─' * 60}")
    print(f"  {model_name}")
    print(f"{'─' * 60}")
    print(f"  Macro F1:  {f1_macro:.4f}")
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  ROC-AUC:   {roc_auc:.4f}" if roc_auc else "  ROC-AUC:   N/A")
    print(f"\n{report}")

    return result


def plot_confusion_matrix(cm: np.ndarray, model_name: str, save_path: Path):
    """Сохранение confusion matrix как PNG."""
    fig, ax = plt.subplots(figsize=(8, 6))
    labels = ['Sell (-1)', 'Neutral (0)', 'Buy (1)']

    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=labels, yticklabels=labels)
    ax.set_xlabel('Predicted', fontsize=12)
    ax.set_ylabel('Actual', fontsize=12)
    ax.set_title(f'Confusion Matrix: {model_name}', fontsize=14)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✅ CM сохранена: {save_path.name}")


def train_all_models(X_train_flat, X_train_eng, X_val_flat, X_val_eng,
                     y_train, y_val) -> list[dict]:
    """
    Обучение всех 5 моделей и оценка на validation.

    Аргументы:
        X_train_flat: Flat features для train (16 признаков)
        X_train_eng: Engineered features для train (223 признака)
        X_val_flat: Flat features для validation
        X_val_eng: Engineered features для validation
        y_train: Метки train
        y_val: Метки validation

    Возвращает:
        Список словарей с результатами для каждой модели
    """
    results = []

    # ── 1. Dummy Classifier ──────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  1/5  DUMMY CLASSIFIER (stratified)")
    print("═" * 60)

    dummy = DummyClassifier(strategy='stratified', random_state=42)
    dummy.fit(X_train_flat, y_train)
    res = evaluate_model(dummy, X_val_flat, y_val, 'Dummy (stratified)')
    res['features_used'] = f'flat ({X_train_flat.shape[1]})'
    plot_confusion_matrix(res['confusion_matrix'], 'Dummy',
                          PLOTS_DIR / 'baseline_cm_dummy.png')
    results.append(res)

    # ── 2. Logistic Regression ───────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  2/5  LOGISTIC REGRESSION")
    print("═" * 60)

    # StandardScaler fit только на train
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_flat)
    X_val_scaled = scaler.transform(X_val_flat)

    lr = LogisticRegression(
        class_weight='balanced',
        max_iter=1000,
        solver='lbfgs',
        random_state=42
    )
    lr.fit(X_train_scaled, y_train)
    res = evaluate_model(lr, X_val_scaled, y_val, 'Logistic Regression')
    res['features_used'] = f'flat ({X_train_flat.shape[1]})'
    plot_confusion_matrix(res['confusion_matrix'], 'LogisticRegression',
                          PLOTS_DIR / 'baseline_cm_logreg.png')
    results.append(res)

    # ── 3. Random Forest ─────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  3/5  RANDOM FOREST")
    print("═" * 60)

    rf = RandomForestClassifier(
        n_estimators=200,
        class_weight='balanced',
        max_depth=15,
        min_samples_leaf=10,
        n_jobs=-1,
        random_state=42
    )
    rf.fit(X_train_flat, y_train)
    res = evaluate_model(rf, X_val_flat, y_val, 'Random Forest')
    res['features_used'] = f'flat ({X_train_flat.shape[1]})'
    plot_confusion_matrix(res['confusion_matrix'], 'RandomForest',
                          PLOTS_DIR / 'baseline_cm_rf.png')
    results.append(res)

    # ── 4. XGBoost ───────────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  4/5  XGBOOST")
    print("═" * 60)

    # Для мультиклассовой задачи XGBoost: sample_weight
    sample_weights = compute_sample_weights(y_train)

    xgb_model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric='mlogloss',
        use_label_encoder=False,
        random_state=42,
        n_jobs=-1,
        verbosity=0
    )
    # Remap labels: XGBoost требует 0-indexed labels
    label_map = {-1: 0, 0: 1, 1: 2}
    inv_label_map = {v: k for k, v in label_map.items()}
    y_train_xgb = np.array([label_map[y] for y in y_train])
    y_val_xgb = np.array([label_map[y] for y in y_val])

    xgb_model.fit(X_train_eng, y_train_xgb, sample_weight=sample_weights)

    # Оценка — нужно remap обратно
    y_pred_xgb = xgb_model.predict(X_val_eng)
    y_pred_original = np.array([inv_label_map[y] for y in y_pred_xgb])
    y_proba_xgb = xgb_model.predict_proba(X_val_eng)

    f1_macro = f1_score(y_val, y_pred_original, average='macro')
    acc = accuracy_score(y_val, y_pred_original)
    try:
        roc_auc = roc_auc_score(y_val_xgb, y_proba_xgb, multi_class='ovr', average='macro')
    except Exception:
        roc_auc = None

    report = classification_report(y_val, y_pred_original,
                                   target_names=['Sell (-1)', 'Neutral (0)', 'Buy (1)'])
    cm = confusion_matrix(y_val, y_pred_original, labels=[-1, 0, 1])

    res_xgb = {
        'model_name': 'XGBoost',
        'f1_macro': f1_macro,
        'accuracy': acc,
        'roc_auc': roc_auc,
        'report': report,
        'confusion_matrix': cm,
        'y_pred': y_pred_original,
        'features_used': f'engineered ({X_train_eng.shape[1]})'
    }

    print(f"\n{'─' * 60}")
    print(f"  XGBoost")
    print(f"{'─' * 60}")
    print(f"  Macro F1:  {f1_macro:.4f}")
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  ROC-AUC:   {roc_auc:.4f}" if roc_auc else "  ROC-AUC:   N/A")
    print(f"\n{report}")

    plot_confusion_matrix(cm, 'XGBoost', PLOTS_DIR / 'baseline_cm_xgboost.png')
    results.append(res_xgb)

    # ── 5. LightGBM ──────────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  5/5  LIGHTGBM")
    print("═" * 60)

    lgb_model = lgb.LGBMClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        is_unbalance=True,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )
    lgb_model.fit(X_train_eng, y_train)
    res = evaluate_model(lgb_model, X_val_eng, y_val, 'LightGBM')
    res['features_used'] = f'engineered ({X_train_eng.shape[1]})'
    plot_confusion_matrix(res['confusion_matrix'], 'LightGBM',
                          PLOTS_DIR / 'baseline_cm_lightgbm.png')
    results.append(res)

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# РАЗДЕЛ 5. ГЕНЕРАЦИЯ ОТЧЁТА
# ═══════════════════════════════════════════════════════════════════════════════

def generate_report(results: list[dict], n_train: int, n_val: int,
                    class_dist_train: dict, class_dist_val: dict):
    """Генерация markdown-отчёта ML/reports/baseline_report.md."""

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Определяем лучшую модель
    best = max(results, key=lambda r: r['f1_macro'])
    dummy_f1 = results[0]['f1_macro']  # Dummy всегда первый

    lines = []
    lines.append("# Baseline Models Report")
    lines.append("")
    lines.append(f"**Дата**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Задача**: Классификация signal ∈ {{-1, 0, 1}}")
    lines.append(f"**Основная метрика**: Macro F1-score")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 1. Данные")
    lines.append("")
    lines.append(f"| Параметр | Train | Validation |")
    lines.append(f"|----------|-------|------------|")
    lines.append(f"| Строк | {n_train} | {n_val} |")

    for cls in [-1, 0, 1]:
        t_count = class_dist_train.get(cls, 0)
        v_count = class_dist_val.get(cls, 0)
        t_pct = t_count / n_train * 100
        v_pct = v_count / n_val * 100
        lines.append(f"| Класс {cls} | {t_count} ({t_pct:.1f}%) | {v_count} ({v_pct:.1f}%) |")

    lines.append("")

    # Сводная таблица
    lines.append("---")
    lines.append("")
    lines.append("## 2. Сравнение моделей")
    lines.append("")
    lines.append("| Модель | Features | Macro F1 | Accuracy | ROC-AUC |")
    lines.append("|--------|----------|----------|----------|---------|")

    for r in results:
        roc = f"{r['roc_auc']:.4f}" if r['roc_auc'] else "N/A"
        marker = " ⭐" if r['model_name'] == best['model_name'] else ""
        lines.append(f"| {r['model_name']}{marker} | {r['features_used']} | "
                     f"**{r['f1_macro']:.4f}** | {r['accuracy']:.4f} | {roc} |")

    lines.append("")

    # Classification reports
    lines.append("---")
    lines.append("")
    lines.append("## 3. Classification Reports")
    lines.append("")

    for r in results:
        lines.append(f"### {r['model_name']}")
        lines.append("```")
        lines.append(r['report'].strip())
        lines.append("```")
        lines.append("")

    # Confusion matrices
    lines.append("---")
    lines.append("")
    lines.append("## 4. Confusion Matrices")
    lines.append("")
    for r in results:
        # Генерируем имя файла
        safe_name = r['model_name'].lower().replace(' ', '_').replace('(', '').replace(')', '')
        plot_name = f"baseline_cm_{safe_name}.png"
        # Проверяем есть ли такой файл
        existing_plots = list(PLOTS_DIR.glob(f'baseline_cm_*.png'))
        lines.append(f"### {r['model_name']}")
        lines.append(f"![{r['model_name']}](../plots/{plot_name})")
        lines.append("")

    # Выводы
    lines.append("---")
    lines.append("")
    lines.append("## 5. Выводы")
    lines.append("")

    signal_exists = best['f1_macro'] > dummy_f1 * 1.1  # >10% улучшение над Dummy

    if signal_exists:
        lines.append(f"✅ **Предиктивный сигнал обнаружен.** "
                     f"Лучшая модель ({best['model_name']}) достигает "
                     f"macro F1 = {best['f1_macro']:.4f}, "
                     f"что на {((best['f1_macro'] / dummy_f1 - 1) * 100):.1f}% выше Dummy baseline "
                     f"(F1 = {dummy_f1:.4f}).")
    else:
        lines.append(f"⚠️ **Слабый предиктивный сигнал.** "
                     f"Лучшая модель ({best['model_name']}) достигает "
                     f"macro F1 = {best['f1_macro']:.4f}, "
                     f"Dummy baseline: F1 = {dummy_f1:.4f}.")

    lines.append("")

    # Детальные наблюдения
    lines.append("### Наблюдения")
    lines.append("")

    # F1 по классам из лучшей модели
    lines.append(f"- **Лучшая модель**: {best['model_name']} (macro F1 = {best['f1_macro']:.4f})")
    lines.append(f"- **Dummy baseline**: macro F1 = {dummy_f1:.4f}")
    lines.append(f"- **Дисбаланс**: класс 0 доминирует (~{class_dist_train.get(0, 0)/n_train*100:.0f}%)")
    lines.append(f"- **Feature-based vs Sequence**: gradient boosting модели работают на полном наборе engineered features ({results[-1]['features_used']})")
    lines.append("")

    lines.append("### Рекомендации")
    lines.append("")
    lines.append("1. Перейти к нейросетевым архитектурам (LSTM, Transformer) для использования последовательной структуры")
    lines.append("2. Попробовать hyperparameter tuning для лучших baseline-моделей")
    lines.append("3. Рассмотреть feature selection на основе importance из gradient boosting")
    lines.append("")

    report_text = "\n".join(lines)
    report_path = REPORTS_DIR / 'baseline_report.md'
    report_path.write_text(report_text, encoding='utf-8')
    print(f"\n✅ Отчёт сохранён: {report_path}")

    return report_path


# ═══════════════════════════════════════════════════════════════════════════════
# РАЗДЕЛ 6. MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Основная функция: загрузка, обучение, оценка, отчёт."""

    print("=" * 60)
    print("  BASELINE ML EXPERIMENTS")
    print("  Классификация signal ∈ {-1, 0, 1}")
    print("=" * 60)

    # Создаём директории
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Загрузка данных ──────────────────────────────────────────────────────
    print("\n📦 Загрузка данных...")
    df_train = load_data(TRAIN_FILE)
    df_val = load_data(VAL_FILE)

    y_train = df_train['signal'].values.astype(int)
    y_val = df_val['signal'].values.astype(int)

    # Статистика классов
    print("\n📊 Распределение классов:")
    for name, y in [('Train', y_train), ('Val', y_val)]:
        classes, counts = np.unique(y, return_counts=True)
        total = len(y)
        dist_str = ", ".join([f"{c}: {cnt} ({cnt/total*100:.1f}%)" for c, cnt in zip(classes, counts)])
        print(f"  {name}: {dist_str}")

    class_dist_train = dict(zip(*np.unique(y_train, return_counts=True)))
    class_dist_val = dict(zip(*np.unique(y_val, return_counts=True)))

    # ── Парсинг 3D тензоров ──────────────────────────────────────────────────
    print("\n🔧 Парсинг фракталов в 3D тензоры...")
    print("  Train...")
    X_3d_train = parse_fractals_to_3d(df_train)
    print(f"  ✅ Train: {X_3d_train.shape}")

    print("  Validation...")
    X_3d_val = parse_fractals_to_3d(df_val)
    print(f"  ✅ Validation: {X_3d_val.shape}")

    # ── Flat features (для LogReg, RF) ───────────────────────────────────────
    print("\n📐 Извлечение flat features (fractal[0] + ATR + time)...")
    X_flat_train = extract_flat_features(df_train, X_3d_train)
    X_flat_val = extract_flat_features(df_val, X_3d_val)
    print(f"  ✅ Flat features: {X_flat_train.shape[1]} признаков")

    # ── Engineered features (для XGBoost, LightGBM) ──────────────────────────
    print("\n🔬 Подготовка engineered features...")

    # Train: загружаем из готового файла
    if ENGINEERED_FEATURES_FILE.exists():
        print(f"  Train: загрузка из {ENGINEERED_FEATURES_FILE.name}")
        eng_train_full = pd.read_csv(ENGINEERED_FEATURES_FILE, sep=',')
        # Удаляем служебные колонки
        cols_to_drop = [c for c in ['signal', 'row_idx', 'time', 'predict'] if c in eng_train_full.columns]
        X_eng_train = eng_train_full.drop(columns=cols_to_drop)
        X_eng_train = X_eng_train.fillna(0)
        print(f"  ✅ Train engineered: {X_eng_train.shape}")
    else:
        print(f"  ⚠️ Файл {ENGINEERED_FEATURES_FILE.name} не найден, вычисляю...")
        X_eng_train = extract_engineered_features(X_3d_train, df_train)
        print(f"  ✅ Train engineered (computed): {X_eng_train.shape}")

    # Validation: вычисляем из 3D тензора
    print(f"  Validation: вычисление engineered features из 3D тензора...")
    X_eng_val = extract_engineered_features(X_3d_val, df_val)
    print(f"  ✅ Validation engineered: {X_eng_val.shape}")

    # Согласование колонок: берём только те, что есть в обоих
    common_cols = sorted(set(X_eng_train.columns) & set(X_eng_val.columns))
    X_eng_train = X_eng_train[common_cols]
    X_eng_val = X_eng_val[common_cols]
    print(f"  ✅ Общих признаков: {len(common_cols)}")

    # Удаляем избыточные
    X_eng_train = remove_redundant_features(X_eng_train)
    X_eng_val = remove_redundant_features(X_eng_val)
    print(f"  ✅ После удаления избыточных: {X_eng_train.shape[1]} признаков")

    # ── Обучение и оценка ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  ОБУЧЕНИЕ МОДЕЛЕЙ")
    print("=" * 60)

    results = train_all_models(
        X_flat_train.values, X_eng_train.values,
        X_flat_val.values, X_eng_val.values,
        y_train, y_val
    )

    # ── Сводная таблица ──────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  СВОДНАЯ ТАБЛИЦА")
    print("=" * 60)
    print(f"\n  {'Модель':<25} {'Features':<20} {'Macro F1':>10} {'Accuracy':>10} {'ROC-AUC':>10}")
    print(f"  {'─' * 75}")
    for r in results:
        roc = f"{r['roc_auc']:.4f}" if r['roc_auc'] else "N/A"
        print(f"  {r['model_name']:<25} {r['features_used']:<20} {r['f1_macro']:>10.4f} "
              f"{r['accuracy']:>10.4f} {roc:>10}")

    # ── Генерация отчёта ─────────────────────────────────────────────────────
    print("\n📝 Генерация отчёта...")
    generate_report(results, len(y_train), len(y_val),
                    class_dist_train, class_dist_val)

    # ── Логирование экспериментов ────────────────────────────────────────────
    print("\n📝 Логирование экспериментов...")
    logger = CSVExperimentLogger()
    for r in results:
        config_dict = {
            'model': r['model_name'],
            'task': 'classification',
            'use_scaler': 'scaled' in r.get('features_used', '').lower(),
        }
        metrics_dict = {
            'metric_name': 'f1_macro',
            'best_metric': r['f1_macro'],
            'f1_macro': r['f1_macro'],
        }
        # F1 per class из classification report не извлекается, оставляем пустым
        logger.log_experiment(config_dict, metrics_dict, checkpoint_path=None)

    print("\n" + "=" * 60)
    print("  ✅ BASELINE EXPERIMENTS ЗАВЕРШЕНЫ")
    print("=" * 60)


if __name__ == '__main__':
    main()
