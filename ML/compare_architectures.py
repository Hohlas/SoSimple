# =============================================================================
# Файл: compare_architectures.py
# Назначение: Последовательное обучение и сравнение всех 4 архитектур
# Язык: Python 3.11+
# Обновлён: 2026-02-24
# Зависимости:
#   Входные данные:
#     - DATA/Nero_train_labeled.csv (откуда: processing/label_main.py)
#     - DATA/Nero_validation_labeled.csv (откуда: processing/label_main.py)
#   Выходные данные:
#     - ML/checkpoints/*_best.pt (веса лучших моделей)
#     - ML/plots/architecture_comparison_*.png (сводный график)
#     - ML/reports/architecture_comparison_*.md (отчёт)
# Использование:
#   python -m ML.compare_architectures --task classification
#   python -m ML.compare_architectures --task regression
# Примечания:
#   - Запускает train.py для каждой модели последовательно
#   - Генерирует разные отчёты и графики в зависимости от типа задачи (classification или regression)
# =============================================================================

"""
Скрипт сравнения всех 4 нейросетевых архитектур.

Последовательно обучает Bi-LSTM, 1D-CNN, Transformer и Hybrid CNN+LSTM,
собирает метрики и генерирует сводный отчёт.
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ML.models import MODEL_REGISTRY
from ML.train import train_model, CHECKPOINTS_DIR, PLOTS_DIR


# ─── Пути ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ML_DIR = PROJECT_ROOT / 'ML'
REPORTS_DIR = ML_DIR / 'reports'


def compare_all_architectures(
    task: str = 'classification',
    use_scaler: bool = False,
    use_weighted_sampler: bool = False,
) -> list[dict]:
    """
    Обучение и сравнение всех моделей из MODEL_REGISTRY.

    Аргументы:
        task: 'classification' или 'regression'
        use_scaler: Использовать ли StandardScaler (default: False)
        use_weighted_sampler: Использовать ли WeightedRandomSampler (для classification)

    Возвращает:
        Список словарей с результатами для каждой модели
    """
    print("=" * 60)
    print("  ARCHITECTURE COMPARISON")
    print(f"  Модели: {', '.join(MODEL_REGISTRY.keys())}")
    print(f"  Задача: {task.upper()}")
    print("=" * 60)

    results = []

    for model_name in MODEL_REGISTRY:
        print(f"\n\n{'▶' * 60}")
        print(f"  Обучение: {model_name.upper()}")
        print(f"{'▶' * 60}")

        result = train_model(
            model_name=model_name,
            task=task,
            use_scaler=use_scaler,
            use_weighted_sampler=use_weighted_sampler,
        )
        results.append(result)

    # Определяем лучшую модель
    best = max(results, key=lambda r: r['best_metric'])

    # Копируем лучшую модель в best_model.pt
    regression = (task == 'regression')
    suffix = '_regression' if regression else ''
    best_src = CHECKPOINTS_DIR / f"{best['model_name']}{suffix}_best.pt"
    best_dst = CHECKPOINTS_DIR / f'best_model{suffix}.pt'
    if best_src.exists():
        shutil.copy2(best_src, best_dst)
        print(f"\n✅ Лучшая модель ({best['model_name']}) скопирована в {best_dst.name}")

    # Сводный график
    _plot_comparison(results, task)

    # Отчёт
    _generate_report(results, task)

    return results


def _plot_comparison(results: list[dict], task: str):
    """Сводный bar chart."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    regression = (task == 'regression')

    model_names = [r['model_name'] for r in results]
    best_metrics = [r['best_metric'] for r in results]

    # Bar chart: Основная метрика (Pearson r или Macro F1)
    colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0']
    bars = axes[0].bar(model_names, best_metrics, color=colors[:len(model_names)])
    metric_name = "Pearson r" if regression else "Macro F1-Score"
    axes[0].set_ylabel(metric_name)
    axes[0].set_title(f'Сравнение архитектур: {metric_name}')
    axes[0].grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, best_metrics):
        axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                     f'{val:.4f}', ha='center', va='bottom', fontweight='bold')

    # Grouped bar: дополнительные метрики
    x = np.arange(len(model_names))
    width = 0.25

    if regression:
        val_mae = [r['best_metrics']['mae'] for r in results]
        val_rmse = [r['best_metrics']['rmse'] for r in results]
        val_r2 = [r['best_metrics']['r2'] for r in results]

        axes[1].bar(x - width, val_mae, width, label='MAE', color='#F44336')
        axes[1].bar(x, val_rmse, width, label='RMSE', color='#9E9E9E')
        axes[1].bar(x + width, val_r2, width, label='R²', color='#03A9F4')
        axes[1].set_title('Дополнительные метрики регрессии')
    else:
        f1_neg = [r['best_metrics']['f1_per_class'].get(-1, 0) for r in results]
        f1_zero = [r['best_metrics']['f1_per_class'].get(0, 0) for r in results]
        f1_pos = [r['best_metrics']['f1_per_class'].get(1, 0) for r in results]

        axes[1].bar(x - width, f1_neg, width, label='Class -1 (Sell)', color='#F44336')
        axes[1].bar(x, f1_zero, width, label='Class 0 (Neutral)', color='#9E9E9E')
        axes[1].bar(x + width, f1_pos, width, label='Class 1 (Buy)', color='#03A9F4')
        axes[1].set_title('Per-Class F1 по архитектурам')

    axes[1].set_xticks(x)
    axes[1].set_xticklabels(model_names)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    suffix = '_regression' if regression else ''
    save_path = PLOTS_DIR / f'architecture_comparison{suffix}.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  📊 Сводный график: {save_path.name}")


def _generate_report(results: list[dict], task: str):
    """Генерация markdown-отчёта ML/reports/architecture_comparison_{task}.md."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    regression = (task == 'regression')

    best = max(results, key=lambda r: r['best_metric'])
    lines = []

    lines.append(f"# Architecture Comparison Report ({task.upper()})")
    lines.append("")
    lines.append(f"**Дата**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if regression:
        lines.append(f"**Задача**: Регрессия (target = predict)")
        lines.append(f"**Loss**: Huber Loss (delta=1.0)")
        lines.append(f"**Early stopping**: на val pearson_r (patience=10)")
        metric_name = "Pearson r"
        suffix = "_regression"
    else:
        lines.append(f"**Задача**: Классификация signal ∈ {{-1, 0, 1}}")
        lines.append(f"**Loss**: Focal Loss (gamma=2, alpha=[0.495, 0.01, 0.495])")
        lines.append(f"**Early stopping**: на val macro F1 (patience=10)")
        metric_name = "Macro F1"
        suffix = ""

    lines.append(f"**Фреймворк**: PyTorch")
    lines.append(f"**Optimizer**: AdamW (lr=1e-3, weight_decay=1e-4)")
    lines.append("")

    # Сводная таблица
    lines.append("---")
    lines.append("")
    lines.append("## 1. Сводная таблица")
    lines.append("")
    
    if regression:
        lines.append("| Модель | Val Pearson r | MAE | RMSE | R² | DirAcc | "
                     "Параметры | Время (с) | Best Epoch |")
        lines.append("|--------|-------------|--------|-------|-------|--------|"
                     "-----------|-----------|------------|")
        for r in results:
            m = r['best_metrics']
            marker = " ⭐" if r['model_name'] == best['model_name'] else ""
            lines.append(
                f"| {r['model_name']}{marker} | "
                f"**{r['best_metric']:.4f}** | "
                f"{m.get('mae', 0):.4f} | "
                f"{m.get('rmse', 0):.4f} | "
                f"{m.get('r2', 0):.4f} | "
                f"{m.get('directional_accuracy', 0):.4f} | "
                f"{r['num_parameters']:,} | "
                f"{r['training_time']:.1f} | "
                f"{r['best_epoch']} |"
            )
    else:
        lines.append("| Модель | Val Macro F1 | F1(-1) | F1(0) | F1(1) | "
                     "Параметры | Время (с) | Best Epoch |")
        lines.append("|--------|-------------|--------|-------|-------|"
                     "-----------|-----------|------------|")
        for r in results:
            f1p = r['best_metrics']['f1_per_class']
            marker = " ⭐" if r['model_name'] == best['model_name'] else ""
            lines.append(
                f"| {r['model_name']}{marker} | "
                f"**{r['best_metric']:.4f}** | "
                f"{f1p.get(-1, 0):.4f} | "
                f"{f1p.get(0, 0):.4f} | "
                f"{f1p.get(1, 0):.4f} | "
                f"{r['num_parameters']:,} | "
                f"{r['training_time']:.1f} | "
                f"{r['best_epoch']} |"
            )

    lines.append("")

    if not regression:
        # Classification reports
        lines.append("---")
        lines.append("")
        lines.append("## 2. Classification Reports")
        lines.append("")

        for r in results:
            lines.append(f"### {r['model_name']}")
            lines.append("```")
            report_text = r['best_metrics'].get('classification_report', 'N/A')
            lines.append(report_text.strip())
            lines.append("```")
            lines.append("")

    # Visualizations
    lines.append("---")
    lines.append("")
    lines.append("## 2. Visualizations")
    lines.append("")
    for r in results:
        lines.append(f"### {r['model_name']}")
        lines.append(f"![{r['model_name']} Training Curves](../plots/training_curves_{r['model_name']}{suffix}.png)")
        if regression:
            lines.append(f"![{r['model_name']} Residuals](../plots/regression_{r['model_name']}.png)")
        else:
            lines.append(f"![{r['model_name']} Confusion Matrix](../plots/cm_{r['model_name']}.png)")
        lines.append("")

    # Сводный график
    lines.append("---")
    lines.append("")
    lines.append("## 3. Сводное сравнение")
    lines.append("")
    lines.append(f"![Architecture Comparison](../plots/architecture_comparison{suffix}.png)")
    lines.append("")

    # Выводы
    lines.append("---")
    lines.append("")
    lines.append("## 4. Выводы")
    lines.append("")
    lines.append(f"**Лучшая модель**: {best['model_name']} "
                 f"({metric_name} = {best['best_metric']:.4f})")
    lines.append("")

    report_text = "\n".join(lines)
    report_path = REPORTS_DIR / f'architecture_comparison_{task}.md'
    report_path.write_text(report_text, encoding='utf-8')
    print(f"\n✅ Отчёт сохранён: {report_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# CLI & MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Сравнение всех архитектур.')
    parser.add_argument(
        '--task', type=str, required=True,
        choices=['classification', 'regression'],
        help="Задача: 'classification' или 'regression'."
    )
    parser.add_argument(
        '--use_scaler', action='store_true',
        help="Включить StandardScaler (по умолчанию выключено)"
    )
    parser.add_argument(
        '--use_weighted_sampler', action='store_true',
        help="Использовать WeightedRandomSampler (для классификации)"
    )
    return parser.parse_args()


def main():
    """Точка входа: сравнение всех архитектур."""
    args = parse_args()
    results = compare_all_architectures(
        task=args.task,
        use_scaler=args.use_scaler,
        use_weighted_sampler=args.use_weighted_sampler,
    )

    print("\n" + "=" * 60)
    print(f"  ✅ СРАВНЕНИЕ АРХИТЕКТУР ЗАВЕРШЕНО ({args.task.upper()})")
    print("=" * 60)

    # Финальная сводка
    best = max(results, key=lambda r: r['best_metric'])
    metric_name = "Pearson r" if args.task == 'regression' else "Macro F1"
    
    print(f"\n  🏆 Лучшая модель: {best['model_name']}")
    print(f"     {metric_name}: {best['best_metric']:.4f}")
    if args.task == 'regression':
        print(f"     MAE: {best['best_metrics'].get('mae', 0):.4f}")
    print(f"     Параметров: {best['num_parameters']:,}")
    print(f"     Время обучения: {best['training_time']:.1f}с")


if __name__ == '__main__':
    main()
