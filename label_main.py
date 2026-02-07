# =============================================================================
# Файл: label_main.py
# Назначение: Основной скрипт для подготовки и маркировки данных (Preprocessing & Labeling)
# Язык: Python 3.10+
# Автор: Antigravity
# Создан: Неизвестно
# Обновлён: 2026-02-07
#
# Зависимости:
#   Входные данные:
#     - Nero.csv (или другой CSV файл по --input)
#   Выходные данные:
#     - {input}_train_labeled.csv (маркированные данные для обучения, 70%)
#     - {input}_validation_labeled.csv (маркированные данные для валидации, 15%)
#     - {input}_test_labeled.csv (маркированные данные для теста, 15%)
# Внутренние зависимости:
#   - label_signals.py (функция label_all_df)
# Внешние зависимости:
#   - pandas>=2.0.0
#   - argparse
#
# Использование:
#   python label_main.py --input data/raw.csv --debug
#   python label_main.py -i Nero.csv
#
# Примечания:
#   - Конвейер: сортировка -> маркировка ВСЕГО датасета -> разделение (70/15/15)
#   - Все три выходных файла содержат метки signal и predict
# =============================================================================

"""
Модуль управления процессом подготовки и разметки торговых данных.

Этот скрипт является входной точкой (CLI) для обработки CSV файлов,
полученных из MetaTrader. Он обеспечивает:
1. Корректную сортировку фракталов в строках (новые события слева).
2. Проверку качества сортировки.
3. Маркировку ВСЕГО датасета (signal + predict).
4. Разделение на train/validation/test (70/15/15%).
"""

import argparse
import pandas as pd
import os
from label_signals import label_all



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


def split_train_val_test(df, input_path, train_ratio=0.70, val_ratio=0.15):
    """
    Разделяет уже маркированный DataFrame на train/validation/test.

    Разделение происходит последовательно (не случайно!), так как в
    торговых данных важен порядок времени.

    Args:
        df (pd.DataFrame): Промаркированный набор данных.
        input_path (str): Путь к исходному файлу для генерации имен новых файлов.
        train_ratio (float): Доля данных для обучения (по умолчанию 0.70).
        val_ratio (float): Доля данных для валидации (по умолчанию 0.15).

    Returns:
        Tuple[str, str, str]: Пути к сохраненным файлам (train, validation, test).
    """
    total_rows = len(df)
    train_end = int(total_rows * train_ratio)
    val_end = int(total_rows * (train_ratio + val_ratio))
    
    train_df = df.iloc[:train_end].copy()
    val_df = df.iloc[train_end:val_end].copy()
    test_df = df.iloc[val_end:].copy()
    
    base_path = os.path.splitext(input_path)[0]
    train_path = f"{base_path}_train_labeled.csv"
    val_path = f"{base_path}_validation_labeled.csv"
    test_path = f"{base_path}_test_labeled.csv"
    
    train_df.to_csv(train_path, sep=';', index=False)
    val_df.to_csv(val_path, sep=';', index=False)
    test_df.to_csv(test_path, sep=';', index=False)
    
    print(f"\nРазделение файла (ВСЕ с метками):")
    print(f"  Всего строк: {total_rows}")
    print(f"  Train:      {len(train_df):>6} ({len(train_df)/total_rows*100:.1f}%) → {train_path}")
    print(f"  Validation: {len(val_df):>6} ({len(val_df)/total_rows*100:.1f}%) → {val_path}")
    print(f"  Test:       {len(test_df):>6} ({len(test_df)/total_rows*100:.1f}%) → {test_path}")
    
    return train_path, val_path, test_path


def main():
    """
    Главная точка входа скрипта.
    
    Конвейер: сортировка -> маркировка ВСЕГО датасета -> разделение (70/15/15).
    """
    parser = argparse.ArgumentParser(
        description="Программный комплекс для подготовки и маркировки котировок"
    )
    parser.add_argument(
        "--input", "-i",
        default="Nero.csv",
        help="Путь к входному CSV (по умолчанию Nero.csv)",
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Включить детальный отладочный вывод",
    )

    args = parser.parse_args()

    print(f"Чтение данных из: {args.input}")
    df = pd.read_csv(args.input, sep=';')
    df.columns = [c.strip() for c in df.columns]
    
    # 1. Сортируем фракталы
    df = sort_fractals_in_dataframe(df, debug=args.debug)
    
    # 2. Проверяем качество сортировки
    verify_sorting_quality(df, debug=args.debug)
    
    # 3. Маркируем ВЕСЬ датасет (сохраняем во временный файл)
    temp_sorted_path = os.path.splitext(args.input)[0] + "_sorted_temp.csv"
    df.to_csv(temp_sorted_path, sep=';', index=False)
    
    temp_labeled_path = os.path.splitext(args.input)[0] + "_labeled_temp.csv"
    print(f"\nМаркировка ВСЕГО датасета ({len(df)} строк)...")
    labeled_df = label_all(temp_sorted_path, temp_labeled_path, debug=args.debug)
    
    # 4. Разделяем на train/validation/test (70/15/15)
    train_p, val_p, test_p = split_train_val_test(labeled_df, args.input)
    
    # 5. Удаляем временные файлы
    os.remove(temp_sorted_path)
    os.remove(temp_labeled_path)
    
    print(f"\nПодготовка завершена. Все файлы содержат метки signal и predict.")


if __name__ == "__main__":
    main()
