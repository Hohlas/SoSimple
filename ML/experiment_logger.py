# =============================================================================
# Файл: experiment_logger.py
# Назначение: Единый CSV-логгер для всех ML-экспериментов
# Язык: Python 3.11+
# Обновлён: 2026-03-11
# Зависимости:
#   Входные данные:
#     - Конфигурация эксперимента (dict)
#     - Метрики эксперимента (dict)
#   Выходные данные:
#     - ML/reports/experiments_log.csv (единый журнал всех экспериментов)
# Внешние зависимости:
#   - pandas>=2.0
#   - pathlib (stdlib)
# Использование:
#   from ML.experiment_logger import CSVExperimentLogger
#   logger = CSVExperimentLogger()
#   logger.log_experiment(config_dict, metrics_dict, checkpoint_path)
# Примечания:
#   - Поддерживает как нейросетевые модели (train.py), так и baseline (baseline_experiments.py)
#   - Автоматически создаёт файл с заголовками при первом запуске
#   - Генерирует уникальный run_id для каждого эксперимента
# =============================================================================

"""
Единый CSV-логгер для всех ML-экспериментов.

Позволяет сохранять параметры и результаты каждого запуска обучения
в единый CSV файл для отслеживания истории и сравнения экспериментов.
"""

import csv
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# ─── Константы ───────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG_PATH = PROJECT_ROOT / 'ML' / 'reports' / 'experiments_log.csv'

# Колонки CSV файла в порядке следования
CSV_COLUMNS = [
    # Идентификация
    'timestamp',
    'run_id',
    'model',
    'task',
    'seed',
    'git_commit',
    # Гиперпараметры обучения
    'epochs',
    'batch_size',
    'lr',
    'weight_decay',
    'patience',
    'scheduler_patience',
    'scheduler_factor',
    'focal_weights',
    'focal_gamma',
    'huber_delta',
    'use_scaler',
    'use_weighted_sampler',
    # Метрики (основная)
    'metric_name',
    'best_metric',
    # Метрики регрессии
    'mae',
    'rmse',
    'r2',
    'dir_acc',
    # Метрики классификации
    'f1_macro',
    'f1_sell',
    'f1_neutral',
    'f1_buy',
    # Доп. информация
    'num_parameters',
    'training_time',
    'best_epoch',
    'checkpoint_path',
]


# ─── Утилиты модуля ──────────────────────────────────────────────────────────

def _get_git_commit() -> str:
    """Получить короткий hash текущего git коммита."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True, text=True, timeout=5,
            cwd=PROJECT_ROOT,
        )
        return result.stdout.strip() if result.returncode == 0 else 'unknown'
    except Exception:
        return 'unknown'


# ═══════════════════════════════════════════════════════════════════════════════
# КЛАСС ЛОГГЕРА
# ═══════════════════════════════════════════════════════════════════════════════

class CSVExperimentLogger:
    """
    CSV-логгер для экспериментов ML.
    
    Автоматически сохраняет параметры и результаты каждого запуска обучения
    в единый CSV файл. Поддерживает как нейросетевые модели, так и baseline.
    
    Атрибуты:
        log_filepath: Путь к CSV файлу с логами
    
    Примеры:
        >>> logger = CSVExperimentLogger()
        >>> config = {'model': 'bilstm', 'task': 'classification', 'epochs': 50}
        >>> metrics = {'f1_macro': 0.45, 'best_epoch': 23}
        >>> logger.log_experiment(config, metrics, 'checkpoints/best.pt')
    """
    
    def __init__(self, log_filepath: Optional[Path] = None):
        """
        Инициализация логгера.
        
        Аргументы:
            log_filepath: Путь к CSV файлу. По умолчанию ML/reports/experiments_log.csv
        """
        self.log_filepath = Path(log_filepath) if log_filepath else DEFAULT_LOG_PATH
        self._ensure_log_file_exists()
    
    def _ensure_log_file_exists(self) -> None:
        """Создаёт CSV файл с заголовками или мигрирует старый формат."""
        # Создаём директорию, если не существует
        self.log_filepath.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.log_filepath.exists():
            # Новый файл — записываем актуальные заголовки
            with open(self.log_filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(CSV_COLUMNS)
        else:
            # Файл существует — проверяем, нужна ли миграция колонок
            self._migrate_csv_columns()
    
    def _migrate_csv_columns(self) -> None:
        """
        Мигрирует старый CSV к новому формату колонок.
        
        Читает существующий файл, добавляет отсутствующие колонки
        (заполняя пустыми значениями) и перезаписывает файл.
        """
        with open(self.log_filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing_columns = reader.fieldnames or []
            
            # Если колонки совпадают — миграция не нужна
            if existing_columns == CSV_COLUMNS:
                return
            
            rows = list(reader)
        
        # Перезаписываем файл с новыми колонками
        with open(self.log_filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for row in rows:
                # Новые колонки будут заполнены пустыми значениями
                migrated = {col: row.get(col, '') for col in CSV_COLUMNS}
                writer.writerow(migrated)
    
    def _generate_run_id(self, model_name: str) -> str:
        """
        Генерирует уникальный ID запуска.
        
        Формат: <model>_<YYYYMMDD>_<HHMMSS>
        Например: bilstm_20260225_120531
        
        Аргументы:
            model_name: Имя модели
        
        Возвращает:
            Уникальный идентификатор запуска
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Нормализуем имя модели (убираем пробелы, приводим к нижнему регистру)
        safe_model = model_name.lower().replace(' ', '_').replace('(', '').replace(')', '')
        return f"{safe_model}_{timestamp}"
    
    def _format_value(self, value: Any) -> str:
        """
        Форматирует значение для записи в CSV.
        
        Аргументы:
            value: Значение любого типа
        
        Возвращает:
            Строковое представление значения
        """
        if value is None:
            return ''
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, float):
            # Форматируем float с 6 знаками после запятой
            return f"{value:.6f}"
        if isinstance(value, (list, tuple)):
            # Списки форматируем как строку с разделителем |
            return '|'.join(str(v) for v in value)
        return str(value)
    
    def _extract_f1_per_class(self, metrics_dict: dict) -> tuple[str, str, str]:
        """
        Извлекает F1 по классам из словаря метрик.
        
        Аргументы:
            metrics_dict: Словарь с метриками
        
        Возвращает:
            Кортеж (f1_sell, f1_neutral, f1_buy)
        """
        # Вариант 1: f1_per_class как словарь {-1: ..., 0: ..., 1: ...}
        f1_per_class = metrics_dict.get('f1_per_class', {})
        if isinstance(f1_per_class, dict):
            f1_sell = f1_per_class.get(-1, '')
            f1_neutral = f1_per_class.get(0, '')
            f1_buy = f1_per_class.get(1, '')
            return (
                self._format_value(f1_sell),
                self._format_value(f1_neutral),
                self._format_value(f1_buy)
            )
        
        # Вариант 2: отдельные ключи val_f1_class_neg, val_f1_class_zero, val_f1_class_pos
        f1_sell = metrics_dict.get('f1_sell') or metrics_dict.get('val_f1_class_neg', '')
        f1_neutral = metrics_dict.get('f1_neutral') or metrics_dict.get('val_f1_class_zero', '')
        f1_buy = metrics_dict.get('f1_buy') or metrics_dict.get('val_f1_class_pos', '')
        
        return (
            self._format_value(f1_sell),
            self._format_value(f1_neutral),
            self._format_value(f1_buy)
        )
    
    def log_experiment(
        self,
        config_dict: dict,
        metrics_dict: dict,
        checkpoint_path: Optional[str] = None,
    ) -> str:
        """
        Логирует эксперимент в CSV файл.
        
        Аргументы:
            config_dict: Словарь с конфигурацией эксперимента
                - model / model_name: Имя модели
                - task: 'classification' или 'regression'
                - epochs: Количество эпох (для нейросетей)
                - batch_size: Размер батча (для нейросетей)
                - lr: Learning rate (для нейросетей)
                - patience: Early stopping patience
                - focal_weights / alpha: Веса классов для Focal Loss
                - use_scaler: Использование StandardScaler
            metrics_dict: Словарь с метриками эксперимента
                - best_metric: Лучшее значение основной метрики
                - metric_name: Название основной метрики
                - mae, rmse, r2, directional_accuracy / dir_acc: Для регрессии
                - f1_macro, f1_per_class: Для классификации
                - training_time: Время обучения в секундах
                - best_epoch: Эпоха с лучшим результатом
            checkpoint_path: Путь к сохранённому чекпойнту
        
        Возвращает:
            Сгенерированный run_id
        
        Примеры:
            >>> config = {'model': 'bilstm', 'task': 'classification', 'epochs': 50}
            >>> metrics = {'f1_macro': 0.45, 'best_epoch': 23, 'training_time': 120.5}
            >>> run_id = logger.log_experiment(config, metrics, 'checkpoints/best.pt')
        """
        # Извлекаем имя модели
        model_name = config_dict.get('model') or config_dict.get('model_name', 'unknown')
        
        # Генерируем run_id
        run_id = self._generate_run_id(model_name)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Извлекаем F1 по классам
        f1_sell, f1_neutral, f1_buy = self._extract_f1_per_class(metrics_dict)
        
        # Git commit (автоматически)
        git_commit = config_dict.get('git_commit') or _get_git_commit()
        
        # Формируем строку данных
        row = {
            # Идентификация
            'timestamp': timestamp,
            'run_id': run_id,
            'model': model_name,
            'task': config_dict.get('task', 'classification'),
            'seed': self._format_value(config_dict.get('seed')),
            'git_commit': git_commit,
            # Гиперпараметры
            'epochs': self._format_value(config_dict.get('epochs')),
            'batch_size': self._format_value(config_dict.get('batch_size')),
            'lr': self._format_value(config_dict.get('lr')),
            'weight_decay': self._format_value(config_dict.get('weight_decay')),
            'patience': self._format_value(config_dict.get('patience')),
            'scheduler_patience': self._format_value(config_dict.get('scheduler_patience')),
            'scheduler_factor': self._format_value(config_dict.get('scheduler_factor')),
            'focal_weights': self._format_value(
                config_dict.get('focal_weights') or config_dict.get('alpha')
            ),
            'focal_gamma': self._format_value(config_dict.get('focal_gamma')),
            'huber_delta': self._format_value(config_dict.get('huber_delta')),
            'use_scaler': self._format_value(config_dict.get('use_scaler')),
            'use_weighted_sampler': self._format_value(config_dict.get('use_weighted_sampler')),
            # Метрики (основная)
            'metric_name': metrics_dict.get('metric_name', ''),
            'best_metric': self._format_value(
                metrics_dict.get('best_metric') or metrics_dict.get('f1_macro')
            ),
            # Метрики регрессии
            'mae': self._format_value(metrics_dict.get('mae')),
            'rmse': self._format_value(metrics_dict.get('rmse')),
            'r2': self._format_value(metrics_dict.get('r2')),
            'dir_acc': self._format_value(
                metrics_dict.get('dir_acc') or metrics_dict.get('directional_accuracy')
            ),
            # Метрики классификации
            'f1_macro': self._format_value(metrics_dict.get('f1_macro')),
            'f1_sell': f1_sell,
            'f1_neutral': f1_neutral,
            'f1_buy': f1_buy,
            # Доп. информация
            'num_parameters': self._format_value(
                config_dict.get('num_parameters') or metrics_dict.get('num_parameters')
            ),
            'training_time': self._format_value(metrics_dict.get('training_time')),
            'best_epoch': self._format_value(metrics_dict.get('best_epoch')),
            'checkpoint_path': checkpoint_path or '',
        }
        
        # Записываем строку в CSV
        with open(self.log_filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writerow(row)
        
        print(f"  📝 Эксперимент залогирован: {run_id}")
        return run_id


# ═══════════════════════════════════════════════════════════════════════════════
# УТИЛИТЫ
# ═══════════════════════════════════════════════════════════════════════════════

def get_latest_experiments(n: int = 10, log_filepath: Optional[Path] = None) -> list[dict]:
    """
    Возвращает последние N экспериментов из лога.
    
    Аргументы:
        n: Количество экспериментов для возврата
        log_filepath: Путь к CSV файлу
    
    Возвращает:
        Список словарей с данными экспериментов (новые первые)
    """
    log_path = Path(log_filepath) if log_filepath else DEFAULT_LOG_PATH
    
    if not log_path.exists():
        return []
    
    experiments = []
    with open(log_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            experiments.append(row)
    
    # Возвращаем последние N (с конца файла)
    return experiments[-n:][::-1]


def find_best_experiment(
    metric: str = 'f1_macro',
    task: Optional[str] = None,
    log_filepath: Optional[Path] = None,
) -> Optional[dict]:
    """
    Находит лучший эксперимент по указанной метрике.
    
    Аргументы:
        metric: Название метрики для сравнения
        task: Фильтр по типу задачи ('classification' или 'regression')
        log_filepath: Путь к CSV файлу
    
    Возвращает:
        Словарь с данными лучшего эксперимента или None
    """
    log_path = Path(log_filepath) if log_filepath else DEFAULT_LOG_PATH
    
    if not log_path.exists():
        return None
    
    best = None
    best_value = -float('inf')
    
    with open(log_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Фильтр по task
            if task and row.get('task') != task:
                continue
            
            # Извлекаем значение метрики
            value_str = row.get(metric, '')
            if not value_str:
                continue
            
            try:
                value = float(value_str)
                if value > best_value:
                    best_value = value
                    best = row
            except ValueError:
                continue
    
    return best


# ═══════════════════════════════════════════════════════════════════════════════
# CLI (для тестирования)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Утилита для работы с логом экспериментов')
    parser.add_argument(
        '--latest', type=int, default=10,
        help='Показать последние N экспериментов (default: 10)'
    )
    parser.add_argument(
        '--best', type=str, default=None,
        help='Найти лучший эксперимент по метрике (например, f1_macro)'
    )
    parser.add_argument(
        '--task', type=str, default=None,
        choices=['classification', 'regression'],
        help='Фильтр по типу задачи'
    )
    
    args = parser.parse_args()
    
    if args.best:
        best = find_best_experiment(metric=args.best, task=args.task)
        if best:
            print(f"\n🏆 Лучший эксперимент по {args.best}:")
            print(f"   Run ID: {best.get('run_id')}")
            print(f"   Model:  {best.get('model')}")
            print(f"   Task:   {best.get('task')}")
            print(f"   {args.best}: {best.get(args.best)}")
        else:
            print(f"❌ Эксперименты с метрикой '{args.best}' не найдены")
    else:
        experiments = get_latest_experiments(n=args.latest)
        if experiments:
            print(f"\n📋 Последние {len(experiments)} экспериментов:")
            print("-" * 80)
            for exp in experiments:
                print(f"  {exp.get('timestamp')} | {exp.get('run_id'):30} | "
                      f"{exp.get('model'):15} | {exp.get('task'):15}")
        else:
            print("❌ Лог экспериментов пуст или не существует")
