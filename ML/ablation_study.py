# =============================================================================
# Файл: ablation_study.py
# Назначение: Автоматизация Ablation Study (ME-2) - проверка влияния длины истории
# Язык: Python 3.11+
# Обновлён: 2026-03-12
# Зависимости:
#   Входные данные: 
#     - DATA/Nero_train_labeled.csv
#   Выходные данные:
#     - Консольный лог с результатами
#     - ML/reports/ablation_study_results.csv
# Использование:
#   python -m ML.ablation_study
# =============================================================================

import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

from ML.train import train_model

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / 'ML' / 'reports'

def run_ablation(
    model_name: str,
    task: str,
    epochs: int,
    batch_size: int,
    optuna_json: str | None = None
):
    print(f"\n{'═' * 60}")
    print(f"  ABLATION STUDY (ME-2): Sequence Length Impact")
    print(f"{'═' * 60}")
    print(f"  Модель: {model_name} | Задача: {task}")
    print(f"  Оцениваемые длины: [100, 50, 20, 10]")

    seq_lengths = [100, 50, 20, 10]
    results = []

    # Загружаем параметры архитектуры из json
    model_kwargs = None
    if optuna_json:
        import json
        with open(optuna_json, 'r', encoding='utf-8') as f:
            optuna_data = json.load(f)
        best_params = optuna_data.get('best_params', {})
        # Извлекаем параметры архитектуры
        model_kwargs = {}
        for k in ['hidden_size', 'num_layers', 'dropout']:
            if k in best_params:
                model_kwargs[k] = best_params[k]
        print(f"  📥 Загружены параметры архитектуры: {model_kwargs}")

    for seq_len in seq_lengths:
        print(f"\n{'─' * 60}")
        print(f"🚀 Обучение с ограничением длины seq_len = {seq_len} фракталов")
        
        result = train_model(
            model_name=model_name,
            task=task,
            epochs=epochs,
            batch_size=batch_size,
            seq_len=seq_len,
            model_kwargs=model_kwargs,
            silent=True  # Используем silent чтобы не спамить в терминале
        )
        
        # Сохраняем метрики
        metric_name = result['metric_name']
        best_metric = result['best_metric']
        best_epoch = result['best_epoch']
        training_time = result['training_time']
        
        res_dict = {
            'seq_len': seq_len,
            'best_val_metric': best_metric,
            'metric_name': metric_name,
            'best_epoch': best_epoch,
            'training_time_sec': training_time
        }
        
        # Добавляем специфичные метрики
        if task == 'regression':
            res_dict['mae'] = result['best_metrics'].get('mae', 0)
            res_dict['rmse'] = result['best_metrics'].get('rmse', 0)
            res_dict['dir_acc'] = result['best_metrics'].get('directional_accuracy', 0)
        
        results.append(res_dict)
        print(f"✅ seq_len={seq_len}: {metric_name} = {best_metric:.5f} (Time: {training_time:.1f}s)")

    # ── Формируем и сохраняем отчет ──────────────────────────────────────────
    df_results = pd.DataFrame(results)
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    save_path = REPORTS_DIR / f'ablation_study_{model_name}_{task}_{timestamp}.csv'
    
    df_results.to_csv(save_path, index=False)
    
    print(f"\n{'═' * 60}")
    print(f"  Итоги Ablation Study")
    print(f"{'═' * 60}")
    print(df_results.to_string(index=False))
    print(f"\n✅ Результаты сохранены в: {save_path.name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Ablation Study для seq_len')
    parser.add_argument('--model', type=str, default='bilstm')
    parser.add_argument('--task', type=str, default='regression')
    parser.add_argument('--epochs', type=int, default=15)
    parser.add_argument('--batch_size', type=int, default=256)
    parser.add_argument('--optuna_json', type=str, default=None,
                        help="Путь к JSON файлу с лучшими параметрами Optuna (опционально)")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    run_ablation(
        model_name=args.model,
        task=args.task,
        epochs=args.epochs,
        batch_size=args.batch_size,
        optuna_json=args.optuna_json
    )
