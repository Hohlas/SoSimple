# =============================================================================
# Файл: reproducibility_tests.py
# Назначение: Автоматизация тестов на воспроизводимость из аудита
# Язык: Python 3.11+
# Обновлён: 2026-03-11
# =============================================================================

"""
Скрипт для тестирования воспроизводимости моделей машинного обучения.

Реализует тесты:
- Тест 2 (Seed stability): 3 запуска с одинаковым seed
- Тест 3 (Seed sensitivity): 5 запусков с разными seed
- Тест 4 (Data pipeline integrity): MD5 хэши данных
"""

import argparse
import hashlib
from datetime import datetime
from pathlib import Path

import numpy as np

from ML.train import train_model

# ─── Пути ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'DATA'
REPORTS_DIR = PROJECT_ROOT / 'ML' / 'reports'


def md5sum(filepath: Path) -> str:
    """Вычисляет MD5 хэш файла."""
    if not filepath.exists():
        return "Not found"
    
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def test_data_integrity() -> list[str]:
    """Тест 4: Проверка целостности данных (MD5 хэши файлов)."""
    print("\n" + "=" * 60)
    print("  ТЕСТ 4: ЦЕЛОСТНОСТЬ ДАННЫХ (MD5 хэши)")
    print("=" * 60)

    files = [
        'Nero_train_labeled.csv',
        'Nero_validation_labeled.csv',
        'Nero_test_labeled.csv',
    ]
    
    lines = []
    lines.append("### Тест 4: Целостность данных (MD5)\n")
    lines.append("| Файл | MD5 хэш |")
    lines.append("|------|---------|")
    
    for filename in files:
        filepath = DATA_DIR / filename
        file_hash = md5sum(filepath)
        print(f"  {filename:30} : {file_hash}")
        lines.append(f"| {filename} | `{file_hash}` |")
    
    lines.append("\n**Вывод**: Зафиксируйте эти хэши. Они должны совпадать при каждом запуске.")
    lines.append("\n---")
    return lines


def test_seed_stability(epochs: int = 50) -> list[str]:
    """Тест 2: Проверка детерминизма (3 запуска с seed=42)."""
    print("\n" + "=" * 60)
    print("  ТЕСТ 2: ДЕТЕРМИНИЗМ (seed stability)")
    print("=" * 60)
    
    seed = 42
    results = []
    pearson_rs = []
    
    for i in range(1, 4):
        print(f"  Запуск {i}/3 (seed={seed})...")
        res = train_model(
            model_name='bilstm',
            task='regression',
            epochs=epochs,
            seed=seed,
            silent=True,
        )
        pearson_r = res['best_metric']
        pearson_rs.append(pearson_r)
        
        print(f"    Pearson r: {pearson_r:.5f} | Best Epoch: {res['best_epoch']} "
              f"| MAE: {res['best_metrics'].get('mae', 0):.5f}")
    
    diff = max(pearson_rs) - min(pearson_rs)
    is_stable = diff < 0.01
    
    lines = []
    lines.append("### Тест 2: Детерминизм (seed stability)\n")
    lines.append(f"**Seed**: {seed}\n")
    lines.append("| Запуск | Pearson r | MAE | RMSE | Best Epoch |")
    lines.append("|--------|-----------|-----|------|------------|")
    
    for i, p_r in enumerate(pearson_rs):
        lines.append(f"| {i+1} | {p_r:.5f} | - | - | - |") # Simplification for report
        
    lines.append(f"\n**Max Diff**: {diff:.5f} (Критерий < 0.01)")
    lines.append(f"**Статус**: {'✅ УСПЕХ' if is_stable else '❌ ПРОВАЛ'}")
    lines.append("\n---")
    
    return lines


def test_seed_sensitivity(epochs: int = 50) -> list[str]:
    """Тест 3: Проверка чувствительности к seed (5 разных seed)."""
    print("\n" + "=" * 60)
    print("  ТЕСТ 3: ЧУВСТВИТЕЛЬНОСТЬ К SEED (seed sensitivity)")
    print("=" * 60)
    
    seeds = [42, 123, 456, 789, 1000]
    pearson_rs = []
    
    lines = []
    lines.append("### Тест 3: Чувствительность к seed (seed sensitivity)\n")
    lines.append("| Seed | Pearson r | Best Epoch |")
    lines.append("|------|-----------|------------|")
    
    for seed in seeds:
        print(f"  Запуск с seed={seed}...")
        res = train_model(
            model_name='bilstm',
            task='regression',
            epochs=epochs,
            seed=seed,
            silent=True,
        )
        pearson_r = res['best_metric']
        pearson_rs.append(pearson_r)
        
        print(f"    Pearson r: {pearson_r:.5f} | Best Epoch: {res['best_epoch']}")
        lines.append(f"| {seed} | {pearson_r:.5f} | {res['best_epoch']} |")
    
    mean_r = np.mean(pearson_rs)
    std_r = np.std(pearson_rs)
    is_robust = std_r < 0.03
    
    lines.append(f"\n**Mean Pearson r**: {mean_r:.5f}")
    lines.append(f"**Std Dev**: {std_r:.5f} (Критерий < 0.03)")
    lines.append(f"**Статус**: {'✅ УСПЕХ' if is_robust else '❌ ПРОВАЛ'}")
    lines.append(f"**Интервал 95% (±2σ)**: [{mean_r - 2*std_r:.5f}, {mean_r + 2*std_r:.5f}]")
    lines.append("\n---")
    
    return lines


def generate_report(sections: list[list[str]], epochs: int):
    """Сборка и сохранение финального отчёта."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / 'reproducibility_report.md'
    
    lines = [
        "# Отчёт: Воспроизводимость и стабильность регрессии\n",
        f"**Дата**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        f"**Модель**: BiLSTM (regression)",
        f"**Эпох в тестах**: {epochs}\n",
        "---\n"
    ]
    
    for section_lines in sections:
        lines.extend(section_lines)
        
    report_text = "\n".join(lines)
    report_path.write_text(report_text, encoding='utf-8')
    print(f"\n✅ Отчёт сохранён: {report_path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Автоматизация тестов воспроизводимости.")
    parser.add_argument('--epochs', type=int, default=50, help="Количество эпох (default: 50).")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    
    print("\n" + "=" * 60)
    print(f"  СТАРТ ТЕСТОВ (Эпох: {args.epochs})")
    print("=" * 60)
    
    sections = []
    
    # Тест 4
    sections.append(test_data_integrity())
    
    # Тест 2
    sections.append(test_seed_stability(epochs=args.epochs))
    
    # Тест 3
    sections.append(test_seed_sensitivity(epochs=args.epochs))
    
    # Отчёт
    generate_report(sections, epochs=args.epochs)
    
    print("\n" + "=" * 60)
    print("  ✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("=" * 60)
