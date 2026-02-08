# =============================================================================
# Файл: label_main.py
# Назначение: Основной скрипт для подготовки, маркировки и нормализации данных
# Язык: Python 3.10+
# Автор: Antigravity
# Создан: Неизвестно
# Обновлён: 2026-02-07
#
# Зависимости:
#   Входные данные:
#     - Nero.csv (или другой CSV файл по --input)
#   Выходные данные:
#     - {input}_train_labeled.csv (маркированные + нормализованные данные, 70%)
#     - {input}_validation_labeled.csv (маркированные + нормализованные данные, 15%)
#     - {input}_test_labeled.csv (маркированные + нормализованные данные, 15%)
#     - {input}_atr_scaler.pkl (RobustScaler для ATR, обученный на train)
#     - {input}_normalization_stats.csv (статистика признаков до нормализации)
# Внутренние зависимости:
#   - label_signals.py (функция label_all)
#   - normalize.py (функции normalize_rowwise, normalize_atr_train, normalize_atr_inference)
# Внешние зависимости:
#   - pandas>=2.0.0
#   - numpy>=1.24.0
#   - scikit-learn>=1.3.0
#   - argparse
#
# Использование:
#   python label_main.py --input data/raw.csv --debug
#   python label_main.py -i Nero.csv
#   python label_main.py -i Nero.csv --no-normalize  # без нормализации
#
# Примечания:
#   - Конвейер: сортировка -> маркировка -> нормализация (построчная) -> разделение -> ATR нормализация
#   - Построчная нормализация выполняется до split (нет data leakage)
#   - ATR нормализация: fit на train, transform на val/test
# =============================================================================

"""
Модуль управления процессом подготовки, разметки и нормализации торговых данных.

Этот скрипт является входной точкой (CLI) для обработки CSV файлов,
полученных из MetaTrader. Он обеспечивает:
1. Корректную сортировку фракталов в строках (новые события слева).
2. Проверку качества сортировки.
3. Маркировку ВСЕГО датасета (signal + predict).
4. Нормализацию признаков (построчная для фракталов, глобальная для ATR).
5. Разделение на train/validation/test (70/15/15%).
"""

import argparse
import pandas as pd
import os
from pathlib import Path
from label_signals import label_all
from normalize import normalize_rowwise, normalize_atr_train, normalize_atr_inference



def process_row_fractals(row_data, fractal_columns, debug=False, row_idx=None):
    """
    Парсит и сортирует фракталы в конкретной строке DataFrame.

    Логика: собирает все непустые значения из колонок 'fractalN',
    извлекает время формирования из каждого значения и сортирует
    фракталы так, чтобы самые свежие (наибольшее время) шли первыми.

    Args:
        row_data (pd.Series): Данные одной строки DataFrame.
        fractal_columns (List[str]): Список имен колонок с фракталами.
        debug (bool): Флаг включения отладки.
        row_idx (int, optional): Индекс строки для вывода в логах.

    Returns:
        List[str]: Список отсортированных строк-фракталов.
    """
    fractals = []
    
    # Собираем и парсим все фракталы
    for col_name in fractal_columns:
        fractal_str = row_data[col_name]
        if pd.isna(fractal_str) or fractal_str == '':
            continue
            
        parts = str(fractal_str).split(':')
        if len(parts) >= 1:  # Нам нужно хотя бы время
            try:
                time_val = int(parts[0])  # time
                fractals.append({
                    'time': time_val,
                    'data': fractal_str
                })
            except (ValueError, IndexError) as e:
                if debug:
                    print(f"  [Строка {row_idx}] Ошибка парсинга фрактала в {col_name}: {e}")
                continue
    
    # Сортируем по времени в обратном порядке (новые первые)
    fractals.sort(key=lambda x: x['time'], reverse=True)
    
    # Возвращаем отсортированные фракталы
    return [f['data'] for f in fractals]


def sort_fractals_in_dataframe(df, debug=False):
    """
    Выполняет сортировку фракталов во всем DataFrame.

    Проходит по каждой строке и переупорядочивает значения в колонках
    'fractal0', 'fractal1', ... на основе времени их появления.

    Args:
        df (pd.DataFrame): Исходный DataFrame с неструктурированными фракталами.
        debug (bool): Флаг отладки.

    Returns:
        pd.DataFrame: DataFrame, где в каждой строке фракталы упорядочены (новые первые).
    """
    if debug:
        print(f"\n[СОРТИРОВКА] Начало сортировки фракталов в {len(df)} строках")
    
    # Получаем список колонок с фракталами
    fractal_columns = [col for col in df.columns if col.startswith('fractal')]
    
    for idx, row in df.iterrows():
        sorted_fractals = process_row_fractals(row, fractal_columns, debug=debug, row_idx=idx)
        
        # Перезаписываем отсортированные фракталы обратно в DataFrame
        for i, fractal_data in enumerate(sorted_fractals):
            if i < len(fractal_columns):
                df.at[idx, fractal_columns[i]] = fractal_data
        
        # Очищаем оставшиеся колонки
        for i in range(len(sorted_fractals), len(fractal_columns)):
            df.at[idx, fractal_columns[i]] = ''
            
    if debug:
        print(f"[СОРТИРОВКА] Завершена")
    
    return df


def verify_sorting_quality(df, debug=False):
    """
    Функция валидации качества сортировки фракталов.

    Проверяет бизнес-правило: время фрактала N должно быть больше или равно
    времени фрактала N+1 (убывающая последовательность).

    Args:
        df (pd.DataFrame): DataFrame после обработки функцией сортировки.
        debug (bool): Флаг отладки для вывода конкретных строк с ошибками.

    Returns:
        bool: True, если все строки отсортированы корректно, иначе False.
    """
    fractal_columns = [col for col in df.columns if col.startswith('fractal')]
    correct_rows = 0
    error_rows = 0
    
    if debug:
        print(f"\n[ПРОВЕРКА] Качество сортировки для {len(df)} строк")

    for idx, row in df.iterrows():
        row_times = []
        for col_name in fractal_columns:
            val = row[col_name]
            if pd.isna(val) or val == '':
                continue
            try:
                time_val = int(str(val).split(':')[0])
                row_times.append(time_val)
            except (ValueError, IndexError):
                continue
        
        # Проверяем на убывание: time[i] >= time[i+1]
        is_sorted = True
        for i in range(len(row_times) - 1):
            if row_times[i] < row_times[i+1]:
                is_sorted = False
                if debug:
                    print(f"  [Строка {idx}] Ошибка сортировки: fractal{i}({row_times[i]}) < fractal{i+1}({row_times[i+1]})")
                break
        
        if is_sorted:
            correct_rows += 1
        else:
            error_rows += 1
            
    print(f"\nСтатистика проверки сортировки:")
    print(f"  Корректно отсортированных строк: {correct_rows}")
    print(f"  Строк с ошибками: {error_rows}")
    
    return error_rows == 0


def split_train_val_test(df, train_ratio=0.70, val_ratio=0.15):
    """
    Разделяет DataFrame на train/validation/test.

    Разделение происходит последовательно (не случайно!), так как в
    торговых данных важен порядок времени.

    Args:
        df (pd.DataFrame): Промаркированный и нормализованный набор данных.
        train_ratio (float): Доля данных для обучения (по умолчанию 0.70).
        val_ratio (float): Доля данных для валидации (по умолчанию 0.15).

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: (train_df, val_df, test_df).
    """
    total_rows = len(df)
    train_end = int(total_rows * train_ratio)
    val_end = int(total_rows * (train_ratio + val_ratio))
    
    train_df = df.iloc[:train_end].copy()
    val_df = df.iloc[train_end:val_end].copy()
    test_df = df.iloc[val_end:].copy()
    
    print(f"\nРазделение файла:")
    print(f"  Всего строк: {total_rows}")
    print(f"  Train:      {len(train_df):>6} ({len(train_df)/total_rows*100:.1f}%)")
    print(f"  Validation: {len(val_df):>6} ({len(val_df)/total_rows*100:.1f}%)")
    print(f"  Test:       {len(test_df):>6} ({len(test_df)/total_rows*100:.1f}%)")
    
    return train_df, val_df, test_df


def save_datasets(train_df, val_df, test_df, input_name, project_root):
    """
    Сохраняет train/validation/test датасеты в CSV файлы.

    Args:
        train_df (pd.DataFrame): Обучающий датасет.
        val_df (pd.DataFrame): Валидационный датасет.
        test_df (pd.DataFrame): Тестовый датасет.
        input_name (str): Базовое имя входного файла (без пути и расширения).
        project_root (Path): Путь к корню проекта.

    Returns:
        Tuple[str, str, str]: Пути к сохранённым файлам (train, validation, test).
    """
    train_path = project_root / f"{input_name}_train_labeled.csv"
    val_path = project_root / f"{input_name}_validation_labeled.csv"
    test_path = project_root / f"{input_name}_test_labeled.csv"
    
    train_df.to_csv(train_path, sep=';', index=False)
    val_df.to_csv(val_path, sep=';', index=False)
    test_df.to_csv(test_path, sep=';', index=False)
    
    print(f"\nСохранение файлов:")
    print(f"  Train:      {train_path}")
    print(f"  Validation: {val_path}")
    print(f"  Test:       {test_path}")
    
    return str(train_path), str(val_path), str(test_path)


def get_project_root():
    """Находит корень проекта (где находится .git папка)"""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / '.git').exists():
            return parent
    return current.parent


def main():
    """
    Главная точка входа скрипта.
    
    Конвейер:
    1. Сортировка фракталов
    2. Маркировка (signal + predict)
    3. Построчная нормализация (до split — нет data leakage)
    4. Разделение train/val/test (70/15/15)
    5. ATR нормализация (fit на train, transform на val/test)
    6. Сохранение файлов
    """
    parser = argparse.ArgumentParser(
        description="Программный комплекс для подготовки, маркировки и нормализации котировок"
    )
    parser.add_argument(
        "--input", "-i",
        default="MT/MQL4/Files/Nero.csv",
        help="Путь к входному CSV относительно корня проекта (по умолчанию MT/MQL4/Files/Nero.csv)",
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Включить детальный отладочный вывод",
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Пропустить этап нормализации",
    )

    args = parser.parse_args()
    
    # Получаем корень проекта
    project_root = get_project_root()
    
    # Формируем полный путь к входному файлу
    input_path = project_root / args.input
    input_name = input_path.stem  # Имя файла без расширения
    
    # Формируем пути для артефактов в корне проекта
    stats_path = project_root / f"{input_name}_normalization_stats.csv"
    scaler_path = project_root / f"{input_name}_atr_scaler.pkl"

    print(f"Чтение данных из: {input_path}")
    df = pd.read_csv(input_path, sep=';')
    df.columns = [c.strip() for c in df.columns]
    
    # 1. Сортируем фракталы
    df = sort_fractals_in_dataframe(df, debug=args.debug)
    
    # 2. Проверяем качество сортировки
    verify_sorting_quality(df, debug=args.debug)
    
    # 3. Маркируем ВЕСЬ датасет (сохраняем во временный файл)
    temp_sorted_path = project_root / f"{input_name}_sorted_temp.csv"
    df.to_csv(temp_sorted_path, sep=';', index=False)
    
    temp_labeled_path = project_root / f"{input_name}_labeled_temp.csv"
    print(f"\nМаркировка ВСЕГО датасета ({len(df)} строк)...")
    labeled_df = label_all(temp_sorted_path, temp_labeled_path, debug=args.debug)
    
    # 4. Построчная нормализация (до split — каждая строка независима)
    if not args.no_normalize:
        labeled_df = normalize_rowwise(
            labeled_df, 
            stats_path=stats_path, 
            debug=args.debug
        )
    
    # 5. Разделяем на train/validation/test (70/15/15)
    train_df, val_df, test_df = split_train_val_test(labeled_df)
    
    # 6. ATR нормализация (fit на train, transform на val/test)
    if not args.no_normalize and 'ATR' in train_df.columns:
        train_df = normalize_atr_train(train_df, scaler_path)
        val_df = normalize_atr_inference(val_df, scaler_path)
        test_df = normalize_atr_inference(test_df, scaler_path)
    
    # 7. Сохраняем файлы
    save_datasets(train_df, val_df, test_df, args.input)
    
    # 8. Удаляем временные файлы
    os.remove(temp_sorted_path)
    os.remove(temp_labeled_path)
    
    print(f"\n" + "=" * 60)
    print("ПОДГОТОВКА ЗАВЕРШЕНА")
    print("=" * 60)
    print(f"Метки: signal, predict")
    if not args.no_normalize:
        print(f"Нормализация: применена")
        print(f"  Статистика: {stats_path}")
        if 'ATR' in df.columns:
            print(f"  ATR scaler: {scaler_path}")
    else:
        print(f"Нормализация: пропущена (--no-normalize)")


if __name__ == "__main__":
    main()
