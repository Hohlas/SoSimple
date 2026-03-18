# =============================================================================
# Файл: label_signals.py
# Назначение: Маркировка торговых сигналов и расчет прогнозных значений (predict)
# Язык: Python 3.10+
# Автор: Antigravity
# Создан: Неизвестно
# Обновлён: 2026-02-11
#
# Зависимости:
#   Входные данные:
#     - CSV файлы (например, Nero.csv или Nero_train.csv) с колонками фракталов
#   Выходные данные:
#     - Обновленный pd.DataFrame с колонками 'signal' и 'predict'
#     - CSV файл по указанному output_path
# Внешние зависимости:
#   - pandas>=2.0.0
#
# Использование:
#   from label_signals import label_all
#   label_all('input.csv', 'output.csv', debug=True)
#
# Примечания:
#   - Использует "forward-looking" логику (заглядывание в будущее) для расчета 'predict'
#   - Формат строки фрактала является критически важным для парсинга
# =============================================================================

"""
Модуль для анализа и маркировки исторических данных котировок.

Этот модуль предоставляет функции для обнаружения сильных уровней (strong levels)
на основе фракталов и разметки обучающей выборки для нейронных сетей.
Включает расчет целевой переменной 'predict', которая отражает потенциал
движения цены против пробитого фрактала.
"""

import pandas as pd


def parse_fractal(fractal_str):
    """
    Парсит строку фрактала и возвращает словарь с параметрами.

    Формат строки:
    `fractal_time:price:direction:front:back:strong:break:reverse:power:count:impulse:up_12:dn_12:up_24:dn_24:up_48:dn_48:fractal_atr`

    Индексы в строке:
        [0]  time (int): Время формирования
        [1]  price (float): Цена фрактала
        [2]  direction (int): Направление (1 - верх, -1 - низ)
        [3]  front (float): Расстояние до фронтального бара
        [4]  back (float): Расстояние до заднего бара
        [5]  strong (int): Флаг сильного фрактала (1 - да, 0 - нет)
        [6]  break (int): Флаг пробития (1 - да, 0 - нет)
        [7]  reverse (float): Значение разворота
        [8]  power (float): Сила импульса
        [9]  count (int): Счетчик подтверждений
        [10] impulse (float): Значение импульса
        [11] up_12 (float): max(High - P) за 12 баров H1
        [12] dn_12 (float): max(P - Low) за 12 баров H1
        [13] up_24 (float): max(High - P) за 24 бара H1
        [14] dn_24 (float): max(P - Low) за 24 бара H1
        [15] up_48 (float): max(High - P) за 48 баров H1
        [16] dn_48 (float): max(P - Low) за 48 баров H1
        [17] fractal_atr (float): Atr.Fast в момент формирования фрактала

    Args:
        fractal_str (str): Строка с данными фрактала из CSV.

    Returns:
        Optional[Dict[str, Any]]: Словарь с распарсенными данными или None,
            если строка пуста или некорректна.
    """
    if pd.isna(fractal_str) or fractal_str == '':
        return None
    
    parts = str(fractal_str).split(':')
    if len(parts) < 7:  # Минимум нужны индексы 0-6 для базовой логики
        return None
    
    try:
        return {
            'time': int(parts[0]),
            'price': float(parts[1]),
            'direction': int(parts[2]),
            'front': float(parts[3]),
            'back': float(parts[4]),
            'strong': int(parts[5]),
            'break': int(parts[6]),
            'reverse': float(parts[7]) if len(parts) > 7 else 0.0,
            'power': float(parts[8]) if len(parts) > 8 else 0.0,
            'count': int(parts[9]) if len(parts) > 9 else 0,
            'impulse':     float(parts[10]) if len(parts) > 10 else 0.0,
            'up_12':       float(parts[11]) if len(parts) > 11 else 0.0,
            'dn_12':       float(parts[12]) if len(parts) > 12 else 0.0,
            'up_24':       float(parts[13]) if len(parts) > 13 else 0.0,
            'dn_24':       float(parts[14]) if len(parts) > 14 else 0.0,
            'up_48':       float(parts[15]) if len(parts) > 15 else 0.0,
            'dn_48':       float(parts[16]) if len(parts) > 16 else 0.0,
            'fractal_atr': float(parts[17]) if len(parts) > 17 else 0.0,
        }
    except (ValueError, IndexError):
        return None


def find_fractal_by_time(row, fractal_columns, target_time):
    """
    Ищет фрактал с заданным временем в текущей строке данных.

    Просматривает все колонки, начинающиеся на 'fractal', чтобы найти
    совпадение по времени формирования (time_val).

    Args:
        row (Union[pd.Series, NamedTuple]): Строка DataFrame.
        fractal_columns (List[str]): Список имен колонок, содержащих фракталы.
        target_time (int): Искомый временной отпечаток фрактала.

    Returns:
        Optional[Dict[str, Any]]: Данные найденного фрактала или None.
    """
    for col_name in fractal_columns:
        # Поддержка как namedtuple (itertuples), так и Series (iloc)
        if hasattr(row, '_asdict'):
            val = getattr(row, col_name, None)
        else:
            val = row[col_name]
        parsed = parse_fractal(val)
        if parsed and parsed['time'] == target_time:
            return parsed
    return None


def label_all(input_path, output_path, debug=False, label_signal=True, label_predict=True):
    """
    Выполняет комплексную маркировку данных: сигналы (signal) и прогнозы (predict).

    Алгоритм:
    1. Находит все фракталы с пометкой 'strong' во всем файле.
    2. Для каждой строки:
       - Если fractal0 является 'strong', ставит метку в 'signal'.
       - Рассчитывает 'predict' как максимальный откат (back) цены до момента
         пробития (break) этого фрактала в будущем.

    Args:
        input_path (str): Путь к исходному CSV файлу (разделитель ';').
        output_path (str): Путь для сохранения результата.
        debug (bool): Флаг включения подробного вывода в консоль.
        label_signal (bool): Нужно ли маркировать колонку 'signal'.
        label_predict (bool): Нужно ли маркировать колонку 'predict'.

    Returns:
        pd.DataFrame: DataFrame с добавленными метками.

    Note:
        Процесс маркировки 'predict' является ресурсоемким (O(N^2) в худшем случае),
        так как требует просмотра будущих строк для каждого фрактала.
    """
    if debug:
        print("=" * 60)
        mode = []
        if label_signal:
            mode.append("SIGNAL")
        if label_predict:
            mode.append("PREDICT")
        print(f"МАРКИРОВКА: {' + '.join(mode)}")
        print("=" * 60)
    
    # Загрузка данных
    df = pd.read_csv(input_path, sep=';')
    df.columns = [c.strip() for c in df.columns]
    
    # Инициализация и приведение типов для целевых колонок
    if 'signal' not in df.columns:
        df['signal'] = 0
    
    if 'predict' not in df.columns:
        df['predict'] = 0.0
    else:
        df['predict'] = df['predict'].astype(float)
    
    # Получаем список колонок с фракталами динамически
    fractal_columns = [col for col in df.columns if col.startswith('fractal')]
    total_rows = len(df)
    
    if debug:
        print(f"\n[ЗАГРУЗКА] Строк: {total_rows}, колонок фракталов: {len(fractal_columns)}")
    
    # === ЭТАП 1: Сбор strong_levels для signal ===
    # Мы собираем времена всех сильных фракталов во всем датасете заранее,
    # чтобы при проходе по строкам мгновенно проверять fractal0 на "силу".
    strong_levels = set()
    
    if label_signal:
        for row in df.itertuples(index=False):
            for col_name in fractal_columns:
                val = getattr(row, col_name, None)
                parsed = parse_fractal(val)
                if parsed and parsed['strong'] == 1:
                    if parsed['time'] not in strong_levels:
                        strong_levels.add(parsed['time'])
                        if debug:
                            print(f"  Strong фрактал: time={parsed['time']}")
        
        print(f"\n[SIGNAL] Найдено {len(strong_levels)} уникальных strong фракталов")
    
    # === ЭТАП 2: Маркировка signal и predict ===
    signals_marked = 0
    predict_marked = 0
    empty_fractal0 = 0
    fractals_dropped = 0
    
    # Конвертируем в список для быстрого доступа по индексу (нужно для forward-looking)
    rows_list = list(df.itertuples(index=False))
    
    for i, row_i in enumerate(rows_list):
        # Парсим текущий активный фрактал (fractal0)
        fractal0_val = getattr(row_i, 'fractal0', None)
        fractal0 = parse_fractal(fractal0_val)
        
        if fractal0 is None:
            empty_fractal0 += 1
            continue
        
        target_time = fractal0['time']
        target_direction = fractal0['direction']
        
        # --- Маркировка signal ---
        if label_signal and target_time in strong_levels:
            df.at[i, 'signal'] = target_direction
            signals_marked += 1
            if debug:
                print(f"  [Строка {i}] ✓ signal={target_direction}")
        
        # --- Маркировка predict ---
        if label_predict:
            # Логика: идем вперед по времени (строкам), пока фрактал существует
            # и пока он не пробит. Фиксируем максимальное значение 'back'.
            max_back = fractal0['back']
            was_broken = False
            
            for j in range(i + 1, total_rows):
                row_j = rows_list[j]
                
                # Ищем тот же самый фрактал в будущих строках
                found = find_fractal_by_time(row_j, fractal_columns, target_time)
                
                if found is None:
                    # Фрактал исчез из истории (вытеснен новыми фракталами) раньше, чем был пробит
                    fractals_dropped += 1
                    if debug and i < 5:
                        print(f"    [Строка {j}] Фрактал time={target_time} выпал")
                    break
                
                # Обновляем максимальный откат
                if found['back'] > max_back:
                    max_back = found['back']
                
                # Проверяем условие пробития уровня
                if found['break'] > 0:
                    was_broken = True
                    if debug and i < 5:
                        print(f"    [Строка {j}] Фрактал пробит: break={found['break']}, max_back={max_back}")
                    break
            
            # Predict рассчитывается как негативный откат относительно направления
            predict_value = -max_back * target_direction
            df.at[i, 'predict'] = predict_value
            predict_marked += 1
            
            if debug and i < 5:
                print(f"  [Строка {i}] ✓ predict={predict_value:.4f}")
    
    # === Статистика ===
    print(f"\n[РЕЗУЛЬТАТ]")
    if label_signal:
        print(f"  Signal помечено: {signals_marked}")
    if label_predict:
        print(f"  Predict помечено: {predict_marked}")
        print(f"  Фракталов выпало до пробития: {fractals_dropped}")
    print(f"  Пустых fractal0: {empty_fractal0}")
    
    # Сохранение результата
    df.to_csv(output_path, sep=';', index=False)
    print(f"[СОХРАНЕНО] {output_path}")
    
    return df


def label_signals(input_path, output_path, debug=False):
    """
    Маркирует только столбец signal (для обратной совместимости).

    Args:
        input_path (str): Путь к входному CSV.
        output_path (str): Путь для сохранения.
        debug (bool): Режим отладки.

    Returns:
        pd.DataFrame: Обработанные данные.
    """
    return label_all(input_path, output_path, debug=debug, 
                     label_signal=True, label_predict=False)


def label_predict_only(input_path, output_path, debug=False):
    """
    Маркирует только столбец predict.

    Args:
        input_path (str): Путь к входному CSV.
        output_path (str): Путь для сохранения.
        debug (bool): Режим отладки.

    Returns:
        pd.DataFrame: Обработанные данные.
    """
    return label_all(input_path, output_path, debug=debug, 
                     label_signal=False, label_predict=True)


def label_updn(df, debug=False):
    """
    Извлекает up/dn таргеты для каждой строки из накопленных значений фрактала.

    Алгоритм: для каждой строки i берёт fractal0 (новейший фрактал).
    Сканирует вперёд до тех пор, пока фрактал существует в массиве.
    Берёт последние найденные значения Up/Dn (самые накопленные).
    Записывает в колонки up_12, dn_12, up_24, dn_24, up_48, dn_48.

    Args:
        df (pd.DataFrame): DataFrame с колонками fractalN.
        debug (bool): Флаг отладки.

    Returns:
        pd.DataFrame: DataFrame с добавленными колонками up/dn.
    """
    HORIZONS = [12, 24, 48]
    for h in HORIZONS:
        df[f'up_{h}'] = 0.0
        df[f'dn_{h}'] = 0.0

    fractal_columns = [col for col in df.columns if col.startswith('fractal')]
    rows_list = list(df.itertuples(index=False))
    total_rows = len(rows_list)

    found_count = 0
    for i, row_i in enumerate(rows_list):
        fractal0 = parse_fractal(getattr(row_i, 'fractal0', None))
        if fractal0 is None:
            continue

        target_time = fractal0['time']
        best = fractal0  # начинаем с текущей строки (Up/Dn = 0 для новейшего)

        for j in range(i + 1, total_rows):
            found = find_fractal_by_time(rows_list[j], fractal_columns, target_time)
            if found is None:
                break  # фрактал вытеснен — берём best
            best = found

        for h in HORIZONS:
            df.at[i, f'up_{h}'] = best.get(f'up_{h}', 0.0)
            df.at[i, f'dn_{h}'] = best.get(f'dn_{h}', 0.0)
        found_count += 1

    if debug:
        print(f"[UPDN] Размечено строк: {found_count} / {total_rows}")

    return df


if __name__ == "__main__":
    # Пример использования модуля при прямом запуске
    # label_all('Nero.csv', 'Nero_full.csv', debug=True)
    pass