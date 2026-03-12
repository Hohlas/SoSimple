# =============================================================================
# Файл: threshold_analysis.py
# Назначение: Поиск оптимального порога θ для конвертации регрессионных
#              предсказаний |predict| в торговые сигналы
# Язык: Python 3.11+
# Обновлён: 2026-03-11
# Зависимости:
#   Входные данные:
#     - ML/checkpoints/*_regression_best.pt (регрессионный чекпоинт)
#     - DATA/Nero_validation_labeled.csv    (валидационные данные)
#   Выходные данные:
#     - ML/reports/threshold_analysis.md
#     - ML/plots/threshold_precision_recall.png
#     - ML/plots/threshold_metrics_vs_theta.png
#     - ML/plots/threshold_profit_factor.png
# Внешние зависимости:
#   - torch>=2.0, numpy>=1.24, pandas>=2.0, matplotlib>=3.7
# Использование:
#   python -m ML.threshold_analysis
#   python -m ML.threshold_analysis --model bilstm
#   python -m ML.threshold_analysis --checkpoint ML/checkpoints/bilstm_regression_best.pt
# Примечания:
#   - Порог θ применяется к |predict_hat|: if |predict_hat| > θ → signal
#   - Направление определяется из fractal[0].direction
#   - Profit factor = gross_profit / gross_loss (proxy через |predict_true|)
# =============================================================================

"""
Поиск оптимального порога θ для конвертации регрессионных
предсказаний |predict| в торговые сигналы.

Загружает обученную регрессионную модель, прогоняет validation set,
перебирает пороги θ и находит оптимальный по precision/recall trade-off
и profit factor.
"""

import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ML.data_loader import (
    create_data_loaders, CSV_SEP, VAL_FILE, FRACTAL_SEP,
)
from ML.models import get_model
from ML.utils import set_seed, get_device


# ─── Пути ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ML_DIR = PROJECT_ROOT / 'ML'
CHECKPOINTS_DIR = ML_DIR / 'checkpoints'
PLOTS_DIR = ML_DIR / 'plots'
REPORTS_DIR = ML_DIR / 'reports'


# ═══════════════════════════════════════════════════════════════════════════════
# ИНФЕРЕНС
# ═══════════════════════════════════════════════════════════════════════════════

@torch.no_grad()
def run_inference(
    model: torch.nn.Module,
    val_loader: torch.utils.data.DataLoader,
    device: torch.device,
) -> np.ndarray:
    """
    Прогон модели на validation set, сбор предсказаний.

    Аргументы:
        model: Обученная регрессионная модель
        val_loader: DataLoader с validation данными
        device: Устройство (cuda/cpu)

    Возвращает:
        np.ndarray shape (n_val,) — предсказания |predict_hat|
    """
    model.eval()
    all_preds = []

    for X_batch, _y_batch, mask_batch in val_loader:
        X_batch = X_batch.to(device)
        mask_batch = mask_batch.to(device)
        preds = model(X_batch, mask=mask_batch).squeeze(-1).cpu().numpy()
        all_preds.append(preds)

    return np.concatenate(all_preds)


def load_validation_metadata() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Загрузка signal, predict и direction из validation CSV.

    Возвращает:
        Кортеж (signal, predict_true, direction):
        - signal: np.ndarray (n,) — метки {-1, 0, 1}
        - predict_abs: np.ndarray (n,) — |predict| (absolute)
        - direction: np.ndarray (n,) — direction из fractal[0] {-1, 1}
    """
    print("  📄 Загрузка метаданных из validation CSV...")
    df = pd.read_csv(VAL_FILE, sep=CSV_SEP, low_memory=False)

    signal = df['signal'].values.astype(int)
    predict_abs = np.abs(df['predict'].values.astype(np.float64))

    # Извлекаем direction из fractal0 (3-е поле, индекс 2)
    direction = df['fractal0'].astype(str).apply(
        lambda x: int(float(x.split(FRACTAL_SEP)[2]))
    ).values

    print(f"    Загружено {len(signal)} строк")
    print(f"    Signals: {(signal != 0).sum()} ({(signal != 0).mean()*100:.1f}%)")
    print(f"    Direction: {(direction == 1).sum()} пиков, "
          f"{(direction == -1).sum()} впадин")

    return signal, predict_abs, direction


# ═══════════════════════════════════════════════════════════════════════════════
# АНАЛИЗ ПОРОГОВ
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_thresholds(
    y_pred: np.ndarray,
    signal_true: np.ndarray,
    predict_abs_true: np.ndarray,
    n_thresholds: int = 200,
) -> pd.DataFrame:
    """
    Перебор порогов θ и вычисление метрик для каждого.

    Логика сигнала:
        predicted_signal = 1 if y_pred > θ, else 0
        true_signal      = 1 if signal_true ≠ 0, else 0

    Profit factor (proxy):
        gross_profit = Σ |predict_true| для верных сигналов (TP)
        gross_loss   = Σ |predict_true| для ложных сигналов (FP)
        PF = gross_profit / gross_loss

    Аргументы:
        y_pred: предсказания модели |predict_hat|
        signal_true: истинные метки signal {-1, 0, 1}
        predict_abs_true: истинные |predict|
        n_thresholds: количество точек для перебора

    Возвращает:
        DataFrame с колонками: theta, precision, recall, f1,
        trades_count, tp, fp, fn, gross_profit, gross_loss, profit_factor
    """
    true_signal_binary = (signal_true != 0).astype(int)
    total_signals = true_signal_binary.sum()

    # Генерируем θ от min(y_pred) до max(y_pred) по percentilям
    percentiles = np.linspace(0, 99.5, n_thresholds)
    thresholds = np.unique(np.percentile(y_pred, percentiles))

    rows = []

    for theta in thresholds:
        pred_signal = (y_pred > theta).astype(int)

        tp = int(((pred_signal == 1) & (true_signal_binary == 1)).sum())
        fp = int(((pred_signal == 1) & (true_signal_binary == 0)).sum())
        fn = int(((pred_signal == 0) & (true_signal_binary == 1)).sum())

        trades = tp + fp

        precision = tp / trades if trades > 0 else 0.0
        recall = tp / total_signals if total_signals > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)
              if (precision + recall) > 0 else 0.0)

        # Profit factor: proxy через |predict_true|
        tp_mask = (pred_signal == 1) & (true_signal_binary == 1)
        fp_mask = (pred_signal == 1) & (true_signal_binary == 0)

        gross_profit = float(predict_abs_true[tp_mask].sum())
        gross_loss = float(predict_abs_true[fp_mask].sum())

        pf = gross_profit / gross_loss if gross_loss > 0 else np.inf

        rows.append({
            'theta': float(theta),
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'trades_count': trades,
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'profit_factor': pf,
        })

    return pd.DataFrame(rows)


def find_optimal_theta(
    df_thresholds: pd.DataFrame,
    min_precision: float = 0.40,
    min_recall: float = 0.20,
    min_trades: int = 10,
) -> dict:
    """
    Поиск оптимального θ по приоритету:
    1. max profit_factor при precision >= min_precision и recall >= min_recall
    2. Если нет → max profit_factor при trades >= min_trades
    3. Fallback → θ с максимальным F1

    Возвращает:
        Словарь с ключами: theta, precision, recall, f1,
        profit_factor, trades_count, selection_method
    """
    # Стратегия 1: precision >= 40%, recall >= 20%
    mask = (
        (df_thresholds['precision'] >= min_precision) &
        (df_thresholds['recall'] >= min_recall) &
        (df_thresholds['trades_count'] >= min_trades) &
        np.isfinite(df_thresholds['profit_factor'])
    )

    if mask.any():
        best_idx = df_thresholds.loc[mask, 'profit_factor'].idxmax()
        row = df_thresholds.loc[best_idx]
        return {**row.to_dict(), 'selection_method': 'precision≥40% & recall≥20% → max PF'}

    # Стратегия 2: max PF при достаточном количестве сделок
    mask2 = (
        (df_thresholds['trades_count'] >= min_trades) &
        np.isfinite(df_thresholds['profit_factor'])
    )

    if mask2.any():
        best_idx = df_thresholds.loc[mask2, 'profit_factor'].idxmax()
        row = df_thresholds.loc[best_idx]
        return {**row.to_dict(), 'selection_method': f'max PF при trades≥{min_trades}'}

    # Стратегия 3: max F1
    best_idx = df_thresholds['f1'].idxmax()
    row = df_thresholds.loc[best_idx]
    return {**row.to_dict(), 'selection_method': 'max F1 (fallback)'}


# ═══════════════════════════════════════════════════════════════════════════════
# ВИЗУАЛИЗАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════════

def plot_precision_recall_curve(df: pd.DataFrame, optimal: dict):
    """Precision-Recall curve с отмеченной оптимальной точкой."""
    fig, ax = plt.subplots(figsize=(8, 6))

    # Фильтруем точки с trades > 0
    valid = df[df['trades_count'] > 0]

    ax.plot(valid['recall'], valid['precision'],
            color='#2196F3', linewidth=2, label='PR Curve')

    # Оптимальная точка
    ax.scatter(optimal['recall'], optimal['precision'],
               color='#F44336', s=120, zorder=5, edgecolors='black',
               label=f"Optimal θ={optimal['theta']:.4f}")

    ax.set_xlabel('Recall (Signal)', fontsize=12)
    ax.set_ylabel('Precision (Signal)', fontsize=12)
    ax.set_title('Precision-Recall Curve (Regression → Signal)', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # Референсные линии
    ax.axhline(y=0.40, color='green', linestyle='--', alpha=0.5, label='Precision=40%')
    ax.axvline(x=0.20, color='orange', linestyle='--', alpha=0.5, label='Recall=20%')
    ax.legend(fontsize=10)

    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)

    plt.tight_layout()
    save_path = PLOTS_DIR / 'threshold_precision_recall.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  📊 {save_path.name}")


def plot_metrics_vs_theta(df: pd.DataFrame, optimal: dict):
    """Precision, Recall, F1 vs θ."""
    fig, ax = plt.subplots(figsize=(10, 6))

    valid = df[df['trades_count'] > 0]

    ax.plot(valid['theta'], valid['precision'],
            color='#4CAF50', linewidth=2, label='Precision')
    ax.plot(valid['theta'], valid['recall'],
            color='#2196F3', linewidth=2, label='Recall')
    ax.plot(valid['theta'], valid['f1'],
            color='#FF9800', linewidth=2, label='F1')

    # Оптимальный θ
    ax.axvline(x=optimal['theta'], color='#F44336', linestyle='--',
               linewidth=1.5, label=f"θ*={optimal['theta']:.4f}")

    # Референс precision=40%
    ax.axhline(y=0.40, color='green', linestyle=':', alpha=0.4)

    ax.set_xlabel('Threshold θ', fontsize=12)
    ax.set_ylabel('Metric Value', fontsize=12)
    ax.set_title('Precision / Recall / F1 vs Threshold', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-0.02, 1.02)

    plt.tight_layout()
    save_path = PLOTS_DIR / 'threshold_metrics_vs_theta.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  📊 {save_path.name}")


def plot_profit_factor(df: pd.DataFrame, optimal: dict):
    """Profit Factor и Trades count vs θ (dual axis)."""
    fig, ax1 = plt.subplots(figsize=(10, 6))

    valid = df[(df['trades_count'] > 0) & np.isfinite(df['profit_factor'])]

    # Profit Factor (левая ось)
    color_pf = '#9C27B0'
    ax1.plot(valid['theta'], valid['profit_factor'],
             color=color_pf, linewidth=2, label='Profit Factor')
    ax1.axhline(y=1.0, color='red', linestyle='--', linewidth=1.5,
                alpha=0.7, label='PF = 1.0 (breakeven)')
    ax1.set_xlabel('Threshold θ', fontsize=12)
    ax1.set_ylabel('Profit Factor', fontsize=12, color=color_pf)
    ax1.tick_params(axis='y', labelcolor=color_pf)

    # Ограничиваем ось Y для PF (избегаем экстремальных значений)
    pf_max = min(valid['profit_factor'].quantile(0.95) * 1.5, 10.0)
    ax1.set_ylim(0, max(pf_max, 2.0))

    # Оптимальный θ
    ax1.axvline(x=optimal['theta'], color='#F44336', linestyle='--',
                linewidth=1.5, label=f"θ*={optimal['theta']:.4f}")

    # Trades count (правая ось)
    ax2 = ax1.twinx()
    color_trades = '#607D8B'
    ax2.fill_between(valid['theta'], 0, valid['trades_count'],
                     alpha=0.15, color=color_trades)
    ax2.plot(valid['theta'], valid['trades_count'],
             color=color_trades, linewidth=1, linestyle='--', label='Trades')
    ax2.set_ylabel('Trades Count', fontsize=12, color=color_trades)
    ax2.tick_params(axis='y', labelcolor=color_trades)

    # Объединённая легенда
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=10)

    ax1.set_title('Profit Factor & Trades Count vs Threshold', fontsize=14)
    ax1.grid(True, alpha=0.3)

    plt.tight_layout()
    save_path = PLOTS_DIR / 'threshold_profit_factor.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  📊 {save_path.name}")


# ═══════════════════════════════════════════════════════════════════════════════
# ОТЧЁТ
# ═══════════════════════════════════════════════════════════════════════════════

def generate_report(
    df: pd.DataFrame,
    optimal: dict,
    model_name: str,
    pearson_r: float,
    n_val: int,
    n_signals: int,
):
    """Генерация markdown-отчёта."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Threshold Analysis Report")
    lines.append("")
    lines.append(f"**Дата**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Модель**: {model_name} (regression)")
    lines.append(f"**Pearson r на val**: {pearson_r:.5f}")
    lines.append(f"**Validation set**: {n_val} строк, "
                 f"{n_signals} signals ({n_signals/n_val*100:.1f}%)")
    lines.append("")

    # Оптимальный порог
    lines.append("---")
    lines.append("")
    lines.append("## 1. Оптимальный порог")
    lines.append("")
    lines.append(f"**Метод выбора**: {optimal['selection_method']}")
    lines.append("")
    lines.append("| Параметр | Значение |")
    lines.append("|----------|----------|")
    lines.append(f"| **θ (threshold)** | **{optimal['theta']:.5f}** |")
    lines.append(f"| Precision | {optimal['precision']:.4f} |")
    lines.append(f"| Recall | {optimal['recall']:.4f} |")
    lines.append(f"| F1 | {optimal['f1']:.4f} |")
    lines.append(f"| Trades count | {int(optimal['trades_count'])} |")
    lines.append(f"| TP / FP / FN | {int(optimal['tp'])} / "
                 f"{int(optimal['fp'])} / {int(optimal['fn'])} |")
    lines.append(f"| Gross profit | {optimal['gross_profit']:.4f} |")
    lines.append(f"| Gross loss | {optimal['gross_loss']:.4f} |")
    pf_str = (f"{optimal['profit_factor']:.4f}"
              if np.isfinite(optimal['profit_factor']) else "∞")
    lines.append(f"| **Profit factor** | **{pf_str}** |")
    lines.append("")

    # Оценка результата
    lines.append("### Оценка")
    lines.append("")
    precision_ok = optimal['precision'] >= 0.40
    recall_ok = optimal['recall'] >= 0.20
    pf_ok = np.isfinite(optimal['profit_factor']) and optimal['profit_factor'] > 1.0

    if precision_ok and recall_ok and pf_ok:
        lines.append("> [!TIP]")
        lines.append("> ✅ **Все критерии выполнены**: precision > 40%, "
                     "recall > 20%, profit factor > 1.0")
        lines.append("> Модель можно использовать для генерации торговых "
                     "сигналов на данном пороге.")
    elif pf_ok:
        lines.append("> [!NOTE]")
        lines.append(f"> ⚠️ Profit factor > 1.0, но "
                     f"{'precision < 40%' if not precision_ok else ''}"
                     f"{' и ' if not precision_ok and not recall_ok else ''}"
                     f"{'recall < 20%' if not recall_ok else ''}.")
        lines.append("> Рекомендуется улучшение модели (HPO, feature engineering) "
                     "перед использованием.")
    else:
        lines.append("> [!WARNING]")
        lines.append("> ❌ Profit factor ≤ 1.0. Модель убыточна на validation set.")
        lines.append("> Сигнал в данных слишком слаб для торговли с текущими features. "
                     "Необходим feature engineering или другой подход.")
    lines.append("")

    # Таблица по ключевым порогам
    lines.append("---")
    lines.append("")
    lines.append("## 2. Метрики по ключевым порогам")
    lines.append("")

    # Выбираем ключевые точки: каждые 5% percentile + оптимальный
    key_percentiles = [50, 60, 70, 75, 80, 85, 90, 92, 94, 95, 96, 97, 98, 99]
    key_thetas = np.percentile(df['theta'].values, key_percentiles)

    lines.append("| Percentile | θ | Precision | Recall | F1 | Trades | "
                 "TP | FP | PF |")
    lines.append("|------------|-------|-----------|--------|------|--------|"
                 "----|----|----|")

    for pct, theta in zip(key_percentiles, key_thetas):
        # Ближайшая строка в таблице
        idx = (df['theta'] - theta).abs().idxmin()
        row = df.loc[idx]
        pf_val = (f"{row['profit_factor']:.2f}"
                  if np.isfinite(row['profit_factor']) else "∞")
        lines.append(
            f"| {pct}% | {row['theta']:.4f} | "
            f"{row['precision']:.3f} | {row['recall']:.3f} | "
            f"{row['f1']:.3f} | {int(row['trades_count'])} | "
            f"{int(row['tp'])} | {int(row['fp'])} | {pf_val} |"
        )

    lines.append("")

    # Визуализации
    lines.append("---")
    lines.append("")
    lines.append("## 3. Визуализации")
    lines.append("")
    lines.append("### Precision-Recall Curve")
    lines.append("![PR Curve](../plots/threshold_precision_recall.png)")
    lines.append("")
    lines.append("### Metrics vs Threshold")
    lines.append("![Metrics vs θ](../plots/threshold_metrics_vs_theta.png)")
    lines.append("")
    lines.append("### Profit Factor vs Threshold")
    lines.append("![PF vs θ](../plots/threshold_profit_factor.png)")
    lines.append("")

    # Trading signal scheme
    lines.append("---")
    lines.append("")
    lines.append("## 4. Схема торгового решения")
    lines.append("")
    lines.append("```")
    lines.append(f"Input: X ∈ R^{{100×11}} → Model → |predict_hat| ∈ R+")
    lines.append("")
    lines.append(f"if |predict_hat| > θ={optimal['theta']:.5f}:")
    lines.append(f"    direction = fractal[0].direction")
    lines.append(f"    if direction == -1:  → BUY  (впадина → рост)")
    lines.append(f"    if direction ==  1:  → SELL (пик → падение)")
    lines.append(f"else:")
    lines.append(f"    → NO SIGNAL")
    lines.append("```")
    lines.append("")

    report_text = "\n".join(lines)
    report_path = REPORTS_DIR / 'threshold_analysis.md'
    report_path.write_text(report_text, encoding='utf-8')
    print(f"\n✅ Отчёт: {report_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def run_threshold_analysis(
    model_name: str | None = None,
    checkpoint_path: str | None = None,
    seed: int = 42,
    optuna_json: str | None = None,
) -> dict:
    """
    Полный pipeline анализа порогов.

    Аргументы:
        model_name: Имя модели ('bilstm', 'cnn1d', ...) — если не задан checkpoint
        checkpoint_path: Путь к чекпоинту — приоритет над model_name
        seed: Random seed для воспроизводимости

    Возвращает:
        Словарь с оптимальным порогом и метриками
    """
    set_seed(seed)
    device = get_device()
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Определяем чекпоинт ──────────────────────────────────────────────────
    if checkpoint_path:
        ckpt_path = Path(checkpoint_path)
    elif model_name:
        ckpt_path = CHECKPOINTS_DIR / f'{model_name}_regression_best.pt'
    else:
        ckpt_path = CHECKPOINTS_DIR / 'best_model_regression.pt'

    if not ckpt_path.exists():
        raise FileNotFoundError(
            f"Чекпоинт не найден: {ckpt_path}\n"
            f"Сначала обучите модель: python -m ML.compare_architectures --task regression"
        )

    print(f"\n{'═' * 60}")
    print(f"  THRESHOLD ANALYSIS: Regression → Trading Signal")
    print(f"{'═' * 60}")
    print(f"  Чекпоинт: {ckpt_path.name}")

    # ── Загрузка чекпоинта ───────────────────────────────────────────────────
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    ckpt_model_name = ckpt.get('model_name', model_name or 'bilstm')
    num_classes = ckpt.get('num_classes', 1)
    pearson_r_val = ckpt.get('best_metric', 0.0)
    metric_name = ckpt.get('metric_name', 'pearson_r')

    print(f"  Модель: {ckpt_model_name}")
    print(f"  Best {metric_name}: {pearson_r_val:.5f}")
    print(f"  Best epoch: {ckpt.get('epoch', '?')}")

    # ── Загрузка Optuna parameters ───────────────────────────────────────────
    model_kwargs = {}
    if optuna_json:
        import json
        with open(optuna_json, 'r', encoding='utf-8') as f:
            optuna_data = json.load(f)
        best_params = optuna_data.get('best_params', {})
        for k in ['hidden_size', 'num_layers', 'dropout']:
            if k in best_params:
                model_kwargs[k] = best_params[k]
        print(f"  📥 Загружены параметры архитектуры: {model_kwargs}")

    # ── Создание модели и загрузка весов ─────────────────────────────────────
    model = get_model(ckpt_model_name, num_classes=num_classes, **model_kwargs)
    model.load_state_dict(ckpt['model_state_dict'])
    model = model.to(device)
    print(f"  ✅ Модель загружена")

    # ── Загрузка данных ──────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    _train_loader, val_loader, _scaler = create_data_loaders(
        batch_size=256,
        target='predict',
        use_scaler=False,
    )

    # Загрузка метаданных (signal, predict, direction) из CSV
    signal_true, predict_abs_true, direction = load_validation_metadata()

    # ── Инференс ─────────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("🔮 Инференс на validation set...")
    y_pred = run_inference(model, val_loader, device)
    print(f"  Предсказания: min={y_pred.min():.4f}, max={y_pred.max():.4f}, "
          f"mean={y_pred.mean():.4f}, std={y_pred.std():.4f}")

    # Проверяем согласованность размеров
    assert len(y_pred) == len(signal_true), (
        f"Размер предсказаний ({len(y_pred)}) ≠ размер signal ({len(signal_true)})"
    )

    # ── Анализ порогов ───────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("📊 Анализ порогов...")
    df_thresholds = analyze_thresholds(y_pred, signal_true, predict_abs_true)
    print(f"  Проанализировано {len(df_thresholds)} порогов")

    # ── Оптимальный порог ────────────────────────────────────────────────────
    optimal = find_optimal_theta(df_thresholds)

    print(f"\n{'═' * 60}")
    print(f"  РЕЗУЛЬТАТ")
    print(f"{'═' * 60}")
    print(f"  Метод выбора: {optimal['selection_method']}")
    print(f"  θ* = {optimal['theta']:.5f}")
    print(f"  Precision: {optimal['precision']:.4f}")
    print(f"  Recall: {optimal['recall']:.4f}")
    print(f"  F1: {optimal['f1']:.4f}")
    print(f"  Trades: {int(optimal['trades_count'])}")
    pf_str = (f"{optimal['profit_factor']:.4f}"
              if np.isfinite(optimal['profit_factor']) else "∞")
    print(f"  Profit Factor: {pf_str}")

    # ── Визуализации ─────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("📊 Построение графиков...")
    plot_precision_recall_curve(df_thresholds, optimal)
    plot_metrics_vs_theta(df_thresholds, optimal)
    plot_profit_factor(df_thresholds, optimal)

    # ── Отчёт ────────────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("📝 Генерация отчёта...")
    n_signals = int((signal_true != 0).sum())
    generate_report(
        df_thresholds, optimal,
        model_name=ckpt_model_name,
        pearson_r=pearson_r_val,
        n_val=len(signal_true),
        n_signals=n_signals,
    )

    return optimal


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Поиск оптимального порога θ для регрессионных предсказаний.'
    )
    parser.add_argument(
        '--model', type=str, default=None,
        choices=['bilstm', 'cnn1d', 'transformer', 'hybrid'],
        help="Имя модели (загрузит <model>_regression_best.pt)"
    )
    parser.add_argument(
        '--checkpoint', type=str, default=None,
        help="Путь к конкретному чекпоинту (приоритет над --model)"
    )
    parser.add_argument(
        '--seed', type=int, default=42,
        help="Random seed (default: 42)"
    )
    parser.add_argument(
        '--optuna_json', type=str, default=None,
        help="Путь к JSON файлу с лучшими параметрами Optuna"
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    run_threshold_analysis(
        model_name=args.model,
        checkpoint_path=args.checkpoint,
        seed=args.seed,
        optuna_json=args.optuna_json,
    )
