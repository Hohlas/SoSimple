#!/usr/bin/env python3
"""
Тестовый скрипт для проверки новой логики путей
"""
from pathlib import Path
import os

def get_project_root():
    """Находит корень проекта (где находится .git папка)"""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / '.git').exists():
            return parent
    return current.parent

def test_path_logic():
    # Тестовые данные
    input_file = "MT/MQL4/Files/Nero.csv"
    project_root = get_project_root()
    base_filename = os.path.basename(input_file).replace('.csv', '')
    base_path = project_root / base_filename
    
    print(f"Project root: {project_root}")
    print(f"Input file: {input_file}")
    print(f"Base filename: {base_filename}")
    print(f"Base path: {base_path}")
    print(f"Stats path: {base_path}_normalization_stats.csv")
    print(f"Scaler path: {base_path}_atr_scaler.pkl")
    print(f"Train path: {base_path}_train_labeled.csv")
    print(f"Test path: {base_path}_test_labeled.csv")

if __name__ == "__main__":
    test_path_logic()