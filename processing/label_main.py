# =============================================================================
# Файл: label_main.py
# Назначение: Основной скрипт для подготовки, маркировки и нормализации данных
# Язык: Python 3.10+
# Автор: Antigravity
# Создан: Неизвестно
# Обновлён: 2026-04-08
#
# Зависимости:
#   Входные данные:
#     - MT/MQL4/Files/Nero.csv (путь относительно корня проекта, см. --input)
#   Выходные данные (все в каталог DATA/):
#     - DATA/{stem}_train_labeled.csv (маркированные + нормализованные данные, 70%)
#     - DATA/{stem}_validation_labeled.csv (маркированные + нормализованные данные, 15%)
#     - DATA/{stem}_test_labeled.csv (маркированные + нормализованные данные, 15%)
#     - DATA/{stem}_normalization_stats.csv (статистика признаков до нормализации)
# Внутренние зависимости:
#   - label_signals.py (функции label_all, label_updn, label_trade_targets, label_entry_path_targets)
#   - normalize.py (функция normalize_rowwise)
# Внешние зависимости:
#   - pandas>=2.0.0
#   - numpy>=1.24.0
#   - scikit-learn>=1.3.0
#   - argparse
#
# Использование:
#   python label_main.py  # по умолчанию: MT/MQL4/Files/Nero.csv
#   python label_main.py -i MT/MQL4/Files/Nero.csv --debug
#   python label_main.py -i MT/MQL4/Files/Nero.csv --no-normalize  # без нормализации
#
# Примечания:
#   - Конвейер: сортировка -> маркировка (signal+predict) -> up/dn таргеты -> outcome таргеты -> нормализация -> split
#   - Построчная нормализация выполняется до split (нет data leakage)
#   - ATR (Atr.Slow) не нормализуется — используется только как знаменатель для ATR_ratio в data_loader.py
#   - up_12..dn_48 нормализуются совместно с Up/Dn фичами фракталов (Piecewise Linear-Log, 606 значений на строку)
# =============================================================================

"""
Модуль управления процессом подготовки, разметки и нормализации торговых данных.

Этот скрипт является входной точкой (CLI) для обработки CSV файлов,
полученных из MetaTrader. Он обеспечивает:
1. Корректную сортировку фракталов в строках (новые события слева).
2. Проверку качества сортировки.
3. Маркировку ВСЕГО датасета (signal + predict).
4. Нормализацию признаков (построчная для фракталов).
5. Разделение на train/validation/test (70/15/15%).
"""

import argparse
import numpy as np
import pandas as pd
import os
from pathlib import Path
from label_signals import (
    label_all,
    label_updn,
    label_trade_targets,
    label_triple_barrier,
    label_first_barrier_hit,
    add_entry_path_frequency_features,
    label_entry_path_targets,
    label_trailing_stop_targets,
)
from normalize import normalize_rowwise
try:
    from processing.fractal_preprocessing import (
        sort_fractals_in_dataframe,
        sort_row_fractals as process_row_fractals,
    )
except ModuleNotFoundError:
    from fractal_preprocessing import (
        sort_fractals_in_dataframe,
        sort_row_fractals as process_row_fractals,
    )



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


def save_datasets(train_df, val_df, test_df, output_base: Path):
    """
    Сохраняет train/validation/test датасеты в CSV файлы.

    Args:
        train_df (pd.DataFrame): Обучающий датасет.
        val_df (pd.DataFrame): Валидационный датасет.
        test_df (pd.DataFrame): Тестовый датасет.
        output_base (Path): Базовый путь для имён файлов (без расширения).
            Все артефакты сохраняются в проект: {output_base}_train_labeled.csv и т.д.

    Returns:
        Tuple[str, str, str]: Пути к сохранённым файлам (train, validation, test).
    """
    output_base_str = str(output_base)
    train_path = f"{output_base_str}_train_labeled.csv"
    val_path = f"{output_base_str}_validation_labeled.csv"
    test_path = f"{output_base_str}_test_labeled.csv"
    
    train_df.to_csv(train_path, sep=';', index=False)
    val_df.to_csv(val_path, sep=';', index=False)
    test_df.to_csv(test_path, sep=';', index=False)
    
    print(f"\nСохранение файлов:")
    print(f"  Train:      {train_path}")
    print(f"  Validation: {val_path}")
    print(f"  Test:       {test_path}")
    
    return train_path, val_path, test_path


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
    5. Сохранение файлов
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
    parser.add_argument(
        "--ohlc",
        default="DATA/XAUUSD_H1_OHLC.csv",
        help="Путь к H1 OHLC CSV для path-ordered Triple Barrier (по умолчанию DATA/XAUUSD_H1_OHLC.csv)",
    )

    args = parser.parse_args()

    # Пути: входной — относительно корня проекта, выходы — в каталог DATA/
    project_root = get_project_root()
    input_path = Path(args.input)
    input_resolved = (project_root / input_path) if not input_path.is_absolute() else input_path
    output_base = project_root / "DATA" / input_path.stem

    stats_path = str(output_base) + "_normalization_stats.csv"

    print(f"Чтение данных из: {input_resolved}")
    df = pd.read_csv(input_resolved, sep=';')
    df.columns = [c.strip() for c in df.columns]
    
    # 1. Сортируем фракталы
    df = sort_fractals_in_dataframe(df, debug=args.debug)
    
    # 2. Проверяем качество сортировки
    verify_sorting_quality(df, debug=args.debug)
    
    # 3. Маркируем ВЕСЬ датасет (сохраняем во временный файл)
    temp_sorted_path = str(output_base) + "_sorted_temp.csv"
    df.to_csv(temp_sorted_path, sep=';', index=False)

    temp_labeled_path = str(output_base) + "_labeled_temp.csv"
    print(f"\nМаркировка ВСЕГО датасета ({len(df)} строк)...")
    labeled_df = label_all(temp_sorted_path, temp_labeled_path, debug=args.debug)

    # 3b. Разметка Up/Dn таргетов
    print(f"\nРазметка Up/Dn таргетов...")
    labeled_df = label_updn(labeled_df, debug=args.debug)

    # 3c. Outcome-aligned targets (before normalization)
    print(f"\nРазметка outcome-aligned таргетов...")
    labeled_df = label_trade_targets(labeled_df, ohlc_path=args.ohlc)

    # 3d. Triple Barrier labels (path-ordered, bar-by-bar OHLC scan, before normalization)
    print(f"\nРазметка Triple Barrier таргетов (path-ordered, OHLC={args.ohlc})...")
    labeled_df = label_first_barrier_hit(labeled_df, args.ohlc, scan_bars=24, debug=args.debug)

    # 3d. Entry-path v1 labels (real entry on next bar, before normalization)
    print(f"\nРазметка entry_path_v1 таргетов (OHLC={args.ohlc})...")
    labeled_df = label_entry_path_targets(labeled_df, args.ohlc, debug=args.debug)
    labeled_df = add_entry_path_frequency_features(labeled_df)

    print(f"\nРазметка trailing-stop таргетов...")
    labeled_df = label_trailing_stop_targets(labeled_df, ohlc_path=args.ohlc)

    # 4. Построчная нормализация (до split — каждая строка независима)
    updn_params = None
    if not args.no_normalize:
        labeled_df, updn_params = normalize_rowwise(
            labeled_df,
            stats_path=stats_path,
            debug=args.debug,
            return_updn_params=True
        )

    # 5. Разделяем на train/validation/test (70/15/15)
    train_df, val_df, test_df = split_train_val_test(labeled_df)

    # 6. Сохраняем файлы
    save_datasets(train_df, val_df, test_df, output_base)

    # 6b. Сохраняем per-row updn_params (brk, cap) для денормализации
    if updn_params is not None:
        n_train = len(train_df)
        n_val = len(val_df)
        n_total = len(labeled_df)
        np.save(str(output_base) + "_train_updn_params.npy", updn_params[:n_train])
        np.save(str(output_base) + "_validation_updn_params.npy", updn_params[n_train:n_train + n_val])
        np.save(str(output_base) + "_test_updn_params.npy", updn_params[n_train + n_val:])
        print(f"  updn_params: train={n_train}, val={n_val}, test={n_total - n_train - n_val}")

    # 7. Удаляем временные файлы
    for tmp in [temp_sorted_path, temp_labeled_path]:
        if os.path.exists(tmp):
            os.remove(tmp)

    print(f"\n" + "=" * 60)
    print("ПОДГОТОВКА ЗАВЕРШЕНА")
    print("=" * 60)
    print(f"Метки: signal, predict, up_3..dn_48, trade_outcome_h12, trade_pnl_h12_atr, archetype_target, buy_sl*_tp*, sell_sl*_tp*")
    if not args.no_normalize:
        print(f"Нормализация: применена")
        print(f"  Статистика: {stats_path}")
    else:
        print(f"Нормализация: пропущена (--no-normalize)")


if __name__ == "__main__":
    main()
