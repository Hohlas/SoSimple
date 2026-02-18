# =============================================================================
# Файл: compare_architectures.py
# Назначение: Последовательное обучение и сравнение всех 4 архитектур
# Язык: Python 3.11+
# Обновлён: 2026-02-18
# Зависимости:
#   Входные данные:
#     - DATA/Nero_train_labeled.csv (откуда: processing/label_main.py)
#     - DATA/Nero_validation_labeled.csv (откуда: processing/label_main.py)
#   Выходные данные:
#     - ML/checkpoints/*_best.pt (веса лучших моделей)
#     - ML/plots/training_curves_*.png (кривые обучения)
#     - ML/plots/cm_*.png (confusion matrices)
#     - ML/plots/architecture_comparison.png (сводный график)
#     - ML/reports/architecture_comparison.md (отчёт)
# Внешние зависимости:
#   - torch>=2.0
#   - numpy>=1.24
#   - pandas>=2.0
#   - scikit-learn>=1.2
#   - matplotlib>=3.7
#   - seaborn>=0.12
# Использование:
#   python ML/compare_architectures.py
# Примечания:
#   - Запускает train.py для каждой модели последовательно
#   - Генерирует сводный отчёт ML/reports/architecture_comparison.md
# =============================================================================

"""
Скрипт сравнения всех 4 нейросетевых архитектур.

Последовательно обучает Bi-LSTM, 1D-CNN, Transformer и Hybrid CNN+LSTM,
собирает метрики и генерирует сводный отчёт.
"""

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
from ML.utils import set_seed


# ─── Пути ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ML_DIR = PROJECT_ROOT / 'ML'
REPORTS_DIR = ML_DIR / 'reports'


def compare_all_architectures() -> list[dict]:
    """
    Обучение и сравнение всех моделей из MODEL_REGISTRY.

    Возвращает:
        Список словарей с результатами для каждой модели
    """
    print("=" * 60)
    print("  ARCHITECTURE COMPARISON")
    print(f"  Модели: {', '.join(MODEL_REGISTRY.keys())}")
    print("=" * 60)

    results = []

    for model_name in MODEL_REGISTRY:
        print(f"\n\n{'▶' * 60}")
        print(f"  Обучение: {model_name.upper()}")
        print(f"{'▶' * 60}")

        result = train_model(model_name=model_name)
        results.append(result)

    # Определяем лучшую модель
    best = max(results, key=lambda r: r['best_f1_macro'])

    # Копируем лучшую модель в best_model.pt
    best_src = CHECKPOINTS_DIR / f"{best['model_name']}_best.pt"
    best_dst = CHECKPOINTS_DIR / 'best_model.pt'
    if best_src.exists():
        shutil.copy2(best_src, best_dst)
        print(f"\n✅ Лучшая модель ({best['model_name']}) скопирована в {best_dst.name}")

    # Сводный график
    _plot_comparison(results)

    # Отчёт
    _generate_report(results)

    return results


def _plot_comparison(results: list[dict]):
    """Сводный bar chart: F1 по моделям и классам."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    model_names = [r['model_name'] for r in results]
    f1_macros = [r['best_f1_macro'] for r in results]

    # Bar chart: macro F1
    colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0']
    bars = axes[0].bar(model_names, f1_macros, color=colors[:len(model_names)])
    axes[0].set_ylabel('Macro F1-Score')
    axes[0].set_title('Сравнение архитектур: Macro F1')
    axes[0].grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, f1_macros):
        axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                     f'{val:.4f}', ha='center', va='bottom', fontweight='bold')

    # Grouped bar: per-class F1
    x = np.arange(len(model_names))
    width = 0.25
    f1_neg = [r['best_metrics']['f1_per_class'].get(-1, 0) for r in results]
    f1_zero = [r['best_metrics']['f1_per_class'].get(0, 0) for r in results]
    f1_pos = [r['best_metrics']['f1_per_class'].get(1, 0) for r in results]

    axes[1].bar(x - width, f1_neg, width, label='Class -1 (Sell)', color='#F44336')
    axes[1].bar(x, f1_zero, width, label='Class 0 (Neutral)', color='#9E9E9E')
    axes[1].bar(x + width, f1_pos, width, label='Class 1 (Buy)', color='#03A9F4')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(model_names)
    axes[1].set_ylabel('F1-Score')
    axes[1].set_title('Per-Class F1 по архитектурам')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    save_path = PLOTS_DIR / 'architecture_comparison.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  📊 Сводный график: {save_path.name}")


def _generate_report(results: list[dict]):
    """Генерация markdown-отчёта ML/reports/architecture_comparison.md."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    best = max(results, key=lambda r: r['best_f1_macro'])
    lines = []

    lines.append("# Architecture Comparison Report")
    lines.append("")
    lines.append(f"**Дата**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Задача**: Классификация signal ∈ {{-1, 0, 1}}")
    lines.append(f"**Фреймворк**: PyTorch")
    lines.append(f"**Loss**: Focal Loss (gamma=2, alpha=[0.45, 0.10, 0.45])")
    lines.append(f"**Optimizer**: AdamW (lr=1e-3, weight_decay=1e-4)")
    lines.append(f"**Early stopping**: на val macro F1 (patience=10)")
    lines.append("")

    # Сводная таблица
    lines.append("---")
    lines.append("")
    lines.append("## 1. Сводная таблица")
    lines.append("")
    lines.append("| Модель | Val Macro F1 | F1(-1) | F1(0) | F1(1) | "
                 "Параметры | Время (с) | Best Epoch |")
    lines.append("|--------|-------------|--------|-------|-------|"
                 "-----------|-----------|------------|")

    for r in results:
        f1p = r['best_metrics']['f1_per_class']
        marker = " ⭐" if r['model_name'] == best['model_name'] else ""
        lines.append(
            f"| {r['model_name']}{marker} | "
            f"**{r['best_f1_macro']:.4f}** | "
            f"{f1p.get(-1, 0):.4f} | "
            f"{f1p.get(0, 0):.4f} | "
            f"{f1p.get(1, 0):.4f} | "
            f"{r['num_parameters']:,} | "
            f"{r['training_time']:.1f} | "
            f"{r['best_epoch']} |"
        )

    lines.append("")

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

    # Confusion matrices
    lines.append("---")
    lines.append("")
    lines.append("## 3. Confusion Matrices")
    lines.append("")
    for r in results:
        lines.append(f"### {r['model_name']}")
        lines.append(f"![{r['model_name']}](../plots/cm_{r['model_name']}.png)")
        lines.append("")

    # Training curves
    lines.append("---")
    lines.append("")
    lines.append("## 4. Training Curves")
    lines.append("")
    for r in results:
        lines.append(f"### {r['model_name']}")
        lines.append(f"![{r['model_name']}](../plots/training_curves_{r['model_name']}.png)")
        lines.append("")

    # Сводный график
    lines.append("---")
    lines.append("")
    lines.append("## 5. Сводное сравнение")
    lines.append("")
    lines.append("![Architecture Comparison](../plots/architecture_comparison.png)")
    lines.append("")

    # Выводы
    lines.append("---")
    lines.append("")
    lines.append("## 6. Выводы")
    lines.append("")
    lines.append(f"**Лучшая модель**: {best['model_name']} "
                 f"(macro F1 = {best['best_f1_macro']:.4f})")
    lines.append("")

    lines.append("### Параметры обучения")
    lines.append("- Loss: Focal Loss (gamma=2, alpha=[0.45, 0.10, 0.45])")
    lines.append("- Optimizer: AdamW (lr=1e-3, weight_decay=1e-4)")
    lines.append("- Scheduler: ReduceLROnPlateau (patience=5, factor=0.5, monitor=val_f1_macro)")
    lines.append("- Early stopping: patience=10 на val macro F1")
    lines.append("- Batch size: 256")
    lines.append("- Seed: 42")
    lines.append("")

    lines.append("### Рекомендации")
    lines.append("1. Провести анализ ошибок лучшей модели (Этап 3.3)")
    lines.append("2. Ablation study: влияние длины последовательности и групп признаков")
    lines.append("3. Зафиксировать архитектуру для полноценного обучения (Этап 4)")
    lines.append("")

    report_text = "\n".join(lines)
    report_path = REPORTS_DIR / 'architecture_comparison.md'
    report_path.write_text(report_text, encoding='utf-8')
    print(f"\n✅ Отчёт сохранён: {report_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Точка входа: сравнение всех архитектур."""
    results = compare_all_architectures()

    print("\n" + "=" * 60)
    print("  ✅ СРАВНЕНИЕ АРХИТЕКТУР ЗАВЕРШЕНО")
    print("=" * 60)

    # Финальная сводка
    best = max(results, key=lambda r: r['best_f1_macro'])
    print(f"\n  🏆 Лучшая модель: {best['model_name']}")
    print(f"     Macro F1: {best['best_f1_macro']:.4f}")
    print(f"     Параметров: {best['num_parameters']:,}")
    print(f"     Время обучения: {best['training_time']:.1f}с")


if __name__ == '__main__':
    main()
