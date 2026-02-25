# =============================================================================
# Файл: optimize.py
# Назначение: Оптимизация гиперпараметров нейросетей с помощью Optuna
# Язык: Python 3.11+
# Обновлён: 2026-02-25
# Зависимости:
#   Входные данные:
#     - DATA/Nero_train_labeled.csv (откуда: processing/label_main.py)
#     - DATA/Nero_validation_labeled.csv (откуда: processing/label_main.py)
#   Выходные данные:
#     - ML/reports/optuna_best_params_<model>_<task>.json
#     - ML/reports/optuna_study_<model>_<task>.json
# Внешние зависимости:
#   - optuna>=3.0
#   - torch>=2.0
#   - numpy>=1.24
# Использование:
#   python -m ML.optimize --model bilstm --task classification --trials 50
#   python -m ML.optimize --model cnn1d --task regression --trials 30 --seed 42
# Примечания:
#   - Optuna Pruning: досрочно останавливает неуспешные trials
#   - Classification: оптимизирует macro F1, Focal Loss weights
#   - Regression: оптимизирует pearson_r, Huber delta
# =============================================================================

"""
Автоматический подбор гиперпараметров с Optuna.

Пространство поиска:
  - lr: [1e-5, 1e-2] (log scale)
  - batch_size: [64, 128, 256, 512]
  - patience: [3, 10]
  - focal_alpha: веса классов для Focal Loss (classification)
  - huber_delta: [0.5, 2.0] (regression)
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler

from ML.train import train_model, DEFAULTS
from ML.models import MODEL_REGISTRY


# ─── Пути ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ML_DIR = PROJECT_ROOT / 'ML'
REPORTS_DIR = ML_DIR / 'reports'


# ═══════════════════════════════════════════════════════════════════════════════
# ПРОСТРАНСТВО ГИПЕРПАРАМЕТРОВ
# ═══════════════════════════════════════════════════════════════════════════════

def suggest_hyperparameters(trial: optuna.Trial, task: str) -> dict:
    """
    Определение пространства поиска гиперпараметров.

    Аргументы:
        trial: Optuna trial объект
        task: 'classification' или 'regression'

    Возвращает:
        Словарь с предложенными гиперпараметрами
    """
    params = {
        # Общие параметры
        'lr': trial.suggest_float('lr', 1e-5, 1e-2, log=True),
        'batch_size': trial.suggest_categorical('batch_size', [64, 128, 256, 512]),
        'patience': trial.suggest_int('patience', 3, 10),
        'weight_decay': trial.suggest_float('weight_decay', 1e-6, 1e-3, log=True),
        
        # Scheduler параметры
        'scheduler_patience': trial.suggest_int('scheduler_patience', 3, 7),
        'scheduler_factor': trial.suggest_float('scheduler_factor', 0.3, 0.7),
    }

    if task == 'classification':
        # Focal Loss параметры
        # alpha: веса для классов [-1, 0, 1]
        # minority_weight контролирует вес классов -1 и 1
        minority_weight = trial.suggest_float('focal_minority_weight', 0.2, 0.7)
        # Класс 0 (neutral) получает вес 1.0 - 2*minority_weight
        neutral_weight = max(0.01, 1.0 - 2 * minority_weight)
        params['focal_alpha'] = [minority_weight, neutral_weight, minority_weight]
        params['focal_gamma'] = trial.suggest_float('focal_gamma', 1.0, 3.0)
    else:
        # Regression: Huber Loss
        params['huber_delta'] = trial.suggest_float('huber_delta', 0.5, 2.0)

    return params


# ═══════════════════════════════════════════════════════════════════════════════
# OBJECTIVE FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def create_objective(model_name: str, task: str, epochs: int, seed: int):
    """
    Создание objective-функции для Optuna.

    Аргументы:
        model_name: Имя модели из MODEL_REGISTRY
        task: 'classification' или 'regression'
        epochs: Максимальное количество эпох
        seed: Базовый seed

    Возвращает:
        Функцию objective(trial) для Optuna
    """
    def objective(trial: optuna.Trial) -> float:
        # Получаем гиперпараметры
        params = suggest_hyperparameters(trial, task)
        
        # Добавляем уникальность seed для каждого trial
        trial_seed = seed + trial.number

        try:
            # Запускаем обучение
            result = train_model(
                model_name=model_name,
                task=task,
                epochs=epochs,
                batch_size=params['batch_size'],
                lr=params['lr'],
                weight_decay=params['weight_decay'],
                patience=params['patience'],
                seed=trial_seed,
                focal_alpha=params.get('focal_alpha'),
                focal_gamma=params.get('focal_gamma', DEFAULTS['gamma']),
                huber_delta=params.get('huber_delta', DEFAULTS['huber_delta']),
                scheduler_patience=params['scheduler_patience'],
                scheduler_factor=params['scheduler_factor'],
                trial=trial,  # Для Pruning
                silent=True,  # Минимальный вывод
            )

            # Возвращаем основную метрику
            return result['best_metric']

        except optuna.TrialPruned:
            # Re-raise для корректной обработки Optuna
            raise
        except Exception as e:
            # Логируем ошибку и возвращаем худшее значение
            print(f"  ❌ Trial {trial.number} failed: {e}")
            return 0.0

    return objective


# ═══════════════════════════════════════════════════════════════════════════════
# ЗАПУСК ОПТИМИЗАЦИИ
# ═══════════════════════════════════════════════════════════════════════════════

def run_optimization(
    model_name: str,
    task: str,
    n_trials: int,
    epochs: int,
    seed: int,
) -> optuna.Study:
    """
    Запуск оптимизации гиперпараметров.

    Аргументы:
        model_name: Имя модели
        task: 'classification' или 'regression'
        n_trials: Количество trials
        epochs: Макс. эпох на trial
        seed: Random seed

    Возвращает:
        Optuna Study объект с результатами
    """
    # Создаём study с TPE sampler и Median Pruner
    sampler = TPESampler(seed=seed)
    pruner = MedianPruner(
        n_startup_trials=5,     # Минимум trials перед началом pruning
        n_warmup_steps=3,       # Минимум эпох перед pruning
        interval_steps=1,       # Проверка каждую эпоху
    )

    study = optuna.create_study(
        direction='maximize',    # Максимизируем F1 или pearson_r
        sampler=sampler,
        pruner=pruner,
        study_name=f'{model_name}_{task}',
    )

    # Создаём objective функцию
    objective = create_objective(model_name, task, epochs, seed)

    # Callback для вывода прогресса
    def callback(study, trial):
        if trial.state == optuna.trial.TrialState.COMPLETE:
            print(f"  Trial {trial.number:3d}: {trial.value:.4f} "
                  f"(best: {study.best_value:.4f})")
        elif trial.state == optuna.trial.TrialState.PRUNED:
            print(f"  Trial {trial.number:3d}: PRUNED")

    print(f"\n{'═' * 60}")
    print(f"  OPTUNA HYPERPARAMETER OPTIMIZATION")
    print(f"  Модель: {model_name.upper()}  |  Задача: {task.upper()}")
    print(f"  Trials: {n_trials}  |  Epochs/trial: {epochs}")
    print(f"{'═' * 60}\n")

    # Запускаем оптимизацию
    study.optimize(
        objective,
        n_trials=n_trials,
        callbacks=[callback],
        show_progress_bar=False,
    )

    return study


def save_results(study: optuna.Study, model_name: str, task: str):
    """
    Сохранение результатов оптимизации.

    Аргументы:
        study: Optuna Study с результатами
        model_name: Имя модели
        task: Задача
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 1. Лучшие параметры
    best_params_path = REPORTS_DIR / f'optuna_best_params_{model_name}_{task}.json'
    best_params = {
        'model': model_name,
        'task': task,
        'best_value': study.best_value,
        'best_params': study.best_params,
        'best_trial': study.best_trial.number,
        'n_trials': len(study.trials),
        'timestamp': timestamp,
    }
    
    with open(best_params_path, 'w', encoding='utf-8') as f:
        json.dump(best_params, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Лучшие параметры сохранены: {best_params_path}")

    # 2. Полная история trials
    study_path = REPORTS_DIR / f'optuna_study_{model_name}_{task}_{timestamp}.json'
    trials_data = []
    for trial in study.trials:
        trial_data = {
            'number': trial.number,
            'value': trial.value,
            'params': trial.params,
            'state': str(trial.state),
            'datetime_start': str(trial.datetime_start) if trial.datetime_start else None,
            'datetime_complete': str(trial.datetime_complete) if trial.datetime_complete else None,
            'duration': str(trial.duration) if trial.duration else None,
        }
        trials_data.append(trial_data)
    
    study_data = {
        'study_name': study.study_name,
        'direction': study.direction.name,
        'best_trial': study.best_trial.number,
        'best_value': study.best_value,
        'best_params': study.best_params,
        'trials': trials_data,
    }
    
    with open(study_path, 'w', encoding='utf-8') as f:
        json.dump(study_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ История trials сохранена: {study_path}")


def print_best_params(study: optuna.Study):
    """Вывод лучших параметров в консоль."""
    print(f"\n{'═' * 60}")
    print(f"  ЛУЧШИЕ ГИПЕРПАРАМЕТРЫ")
    print(f"{'═' * 60}")
    print(f"  Best value: {study.best_value:.4f}")
    print(f"  Best trial: #{study.best_trial.number}")
    print(f"\n  Параметры:")
    for key, value in study.best_params.items():
        if isinstance(value, float):
            print(f"    {key}: {value:.6f}")
        else:
            print(f"    {key}: {value}")
    
    # Статистика
    completed = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])
    pruned = len([t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED])
    failed = len([t for t in study.trials if t.state == optuna.trial.TrialState.FAIL])
    
    print(f"\n  Статистика:")
    print(f"    Completed: {completed}")
    print(f"    Pruned:    {pruned}")
    print(f"    Failed:    {failed}")
    print(f"{'═' * 60}")


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    """Парсинг аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description='Оптимизация гиперпараметров нейросетей с Optuna'
    )
    parser.add_argument(
        '--model', type=str, required=True,
        choices=list(MODEL_REGISTRY.keys()),
        help=f"Модель: {', '.join(MODEL_REGISTRY.keys())}"
    )
    parser.add_argument(
        '--task', type=str, default='classification',
        choices=['classification', 'regression'],
        help="Задача: 'classification' или 'regression'. Default: classification"
    )
    parser.add_argument(
        '--trials', type=int, default=50,
        help="Количество trials (default: 50)"
    )
    parser.add_argument(
        '--epochs', type=int, default=30,
        help="Макс. эпох на trial (default: 30)"
    )
    parser.add_argument(
        '--seed', type=int, default=42,
        help="Random seed (default: 42)"
    )
    
    return parser.parse_args()


def main():
    """Точка входа."""
    args = parse_args()

    # Проверяем наличие optuna
    try:
        import optuna
    except ImportError:
        print("❌ Optuna не установлена. Установите: pip install optuna")
        sys.exit(1)

    # Запускаем оптимизацию
    study = run_optimization(
        model_name=args.model,
        task=args.task,
        n_trials=args.trials,
        epochs=args.epochs,
        seed=args.seed,
    )

    # Выводим и сохраняем результаты
    print_best_params(study)
    save_results(study, args.model, args.task)

    print("\n✅ Оптимизация завершена!")


if __name__ == '__main__':
    main()
