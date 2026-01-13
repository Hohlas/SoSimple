import argparse
import pandas as pd
import os
from label_signals import label_signals


def split_train_validation(input_path, train_ratio=0.75):
    """
    Разделяет CSV файл на тренировочный и проверочный наборы.
    
    Args:
        input_path: путь к входному CSV файлу
        train_ratio: доля данных для тренировки (по умолчанию 0.75, т.е. 75%)
    
    Returns:
        tuple: (train_path, validation_path) - пути к созданным файлам
    """
    # Загружаем данные
    df = pd.read_csv(input_path, sep=';')
    
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
    
    # Разделяем файл на train и validation
    train_path, validation_path = split_train_validation(args.input, train_ratio=0.75)
    
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
