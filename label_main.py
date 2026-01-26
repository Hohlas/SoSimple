import argparse
import pandas as pd
import os
from label_signals import label_signals


def process_row_fractals(row_data, fractal_columns, debug=False, row_idx=None):
    """
    Обрабатывает фракталы в строке: сортирует по времени в обратном порядке.
    
    Args:
        row_data: данные строки (Series)
        fractal_columns: список названий колонок с фракталами
        debug: включить отладочный вывод
        row_idx: индекс строки для отладки
    
    Returns:
        list: отсортированные фракталы (новые первые)
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
    Сортирует фракталы в каждой строке DataFrame.
    
    Args:
        df: исходный DataFrame
        debug: флаг отладки
        
    Returns:
        pd.DataFrame: DataFrame с отсортированными фракталами
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
    Проверяет корректность сортировки фракталов (новые первые, т.е. время убывает).
    
    Args:
        df: DataFrame для проверки
        debug: флаг отладки
        
    Returns:
        bool: True если ошибок нет, False если есть
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


def split_train_validation(df, input_path, train_ratio=0.75):
    """
    Разделяет DataFrame на тренировочный и проверочный наборы и сохраняет их.
    
    Args:
        df: DataFrame с данными
        input_path: путь к исходному файлу (для формирования имен)
        train_ratio: доля данных для тренировки (по умолчанию 0.75, т.е. 75%)
    
    Returns:
        tuple: (train_path, validation_path) - пути к созданным файлам
    """
    # Вычисляем границу разделения
    total_rows = len(df)
    train_rows = int(total_rows * train_ratio)
    
    # Разделяем на train и validation
    train_df = df.iloc[:train_rows].copy()
    validation_df = df.iloc[train_rows:].copy()
    
    # Формируем имена выходных файлов
    base_path = os.path.splitext(input_path)[0]
    train_path = f"{base_path}_train.csv"
    validation_path = f"{base_path}_validation.csv"
    
    # Сохраняем файлы
    train_df.to_csv(train_path, sep=';', index=False)
    validation_df.to_csv(validation_path, sep=';', index=False)
    
    print(f"\nРазделение файла:")
    print(f"  Всего строк: {total_rows}")
    print(f"  Train: {len(train_df)} строк ({(len(train_df)/total_rows)*100:.1f}%) → {train_path}")
    print(f"  Validation: {len(validation_df)} строк ({(len(validation_df)/total_rows)*100:.1f}%) → {validation_path}")
    
    return train_path, validation_path


def main():
    parser = argparse.ArgumentParser(
        description="Маркировка сигналов в Nero.csv по strong-фракталам"
    )
    parser.add_argument(
        "--input",
        "-i",
        default="Nero.csv",
        help="Путь к входному CSV (по умолчанию Nero.csv)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="Nero_labeled.csv",
        help="Путь к выходному CSV (по умолчанию Nero_labeled.csv)",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Включить отладочный вывод",
    )

    args = parser.parse_args()

    print(f"Читаю: {args.input}")
    
    # Загружаем данные
    df = pd.read_csv(args.input, sep=';')
    df.columns = [c.strip() for c in df.columns]
    
    # Сортируем фракталы СРАЗУ
    df = sort_fractals_in_dataframe(df, debug=args.debug)
    
    # Проверяем качество
    verify_sorting_quality(df, debug=args.debug)
    
    # Разделяем файл на train и validation
    train_path, validation_path = split_train_validation(df, args.input, train_ratio=0.75)
    
    # Маркируем только train файл
    train_labeled_path = os.path.splitext(train_path)[0] + "_labeled.csv"
    
    if args.debug:
        print("Режим отладки: ВКЛЮЧЕН")
    
    print(f"\nМаркировка train файла:")
    print(f"  Входной файл: {train_path}")
    print(f"  Выходной файл: {train_labeled_path}")
    
    label_signals(train_path, train_labeled_path, debug=args.debug)
    
    print(f"\nИтоговые файлы:")
    print(f"  Train (с метками): {train_labeled_path}")
    print(f"  Validation (без меток): {validation_path}")


if __name__ == "__main__":
    main()
