import pandas as pd


def parse_fractal(fractal_str):
    """
    Парсит строку фрактала и возвращает словарь с параметрами.
    Формат: fractal_time:price:direction:front:back:strong:break:reverse:power:count:impulse
    Индексы:     [0]      [1]     [2]     [3]   [4]   [5]    [6]    [7]    [8]   [9]   [10]
    
    Returns:
        dict или None если парсинг неудачен
    """
    if pd.isna(fractal_str) or fractal_str == '':
        return None
    
    parts = str(fractal_str).split(':')
    if len(parts) < 7:  # Минимум нужны индексы 0-6
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
            'impulse': float(parts[10]) if len(parts) > 10 else 0.0,
        }
    except (ValueError, IndexError):
        return None


def find_fractal_by_time(row, fractal_columns, target_time):
    """
    Ищет фрактал с заданным временем в строке.
    
    Args:
        row: строка DataFrame
        fractal_columns: список колонок с фракталами
        target_time: искомое время фрактала
        
    Returns:
        dict с параметрами фрактала или None если не найден
    """
    for col_name in fractal_columns:
        parsed = parse_fractal(row[col_name])
        if parsed and parsed['time'] == target_time:
            return parsed
    return None


def label_predict(input_path, output_path, debug=False):
    """
    Маркирует столбец predict в CSV файле с фрактальными данными.
    
    Алгоритм:
    1. Для каждой строки i извлекаем target_time и target_direction из fractal0
    2. Ищем эволюцию этого фрактала в последующих строках j > i
    3. Отслеживаем max_back до момента пробития (break > 0) или выпадения
    4. predict = -max_back * target_direction
    
    Args:
        input_path: путь к входному CSV файлу
        output_path: путь для сохранения результатов
        debug: включить отладочный вывод
    """
    if debug:
        print("=" * 60)
        print("МАРКИРОВКА PREDICT")
        print("=" * 60)
    
    # Загрузка данных
    df = pd.read_csv(input_path, sep=';')
    df.columns = [c.strip() for c in df.columns]
    
    # Получаем список колонок с фракталами (динамически)
    fractal_columns = [col for col in df.columns if col.startswith('fractal')]
    
    total_rows = len(df)
    
    if debug:
        print(f"\n[PREDICT] Загружено строк: {total_rows}")
        print(f"[PREDICT] Колонок с фракталами: {len(fractal_columns)}")
    
    # Статистика
    predict_marked = 0
    predict_empty_fractal0 = 0
    predict_parse_errors = 0
    predict_not_found = 0
    
    for i in range(total_rows):
        row_i = df.iloc[i]
        
        # Парсим fractal0
        fractal0 = parse_fractal(row_i['fractal0'])
        if fractal0 is None:
            predict_empty_fractal0 += 1
            if debug and i < 5:
                print(f"  [Строка {i}] fractal0 пустой или невалидный, пропускаем")
            continue
        
        target_time = fractal0['time']
        target_direction = fractal0['direction']
        max_back = fractal0['back']  # Начальное значение из fractal0
        
        if debug and i < 5:
            print(f"  [Строка {i}] fractal0: time={target_time}, dir={target_direction}, back={max_back}")
        
        # Ищем эволюцию фрактала в последующих строках
        for j in range(i + 1, total_rows):
            row_j = df.iloc[j]
            
            found = find_fractal_by_time(row_j, fractal_columns, target_time)
            
            if found is None:
                # Фрактал выпал из списка - прекращаем поиск
                if debug and i < 5:
                    print(f"    [Строка {j}] Фрактал time={target_time} выпал")
                predict_not_found += 1
                break
            
            # Обновляем max_back
            if found['back'] > max_back:
                max_back = found['back']
            
            # Если фрактал пробит (break > 0) - прекращаем поиск
            if found['break'] > 0:
                if debug and i < 5:
                    print(f"    [Строка {j}] Фрактал пробит: break={found['break']}, max_back={max_back}")
                break
        
        # Записываем predict = -max_back * target_direction
        predict_value = -max_back * target_direction
        df.at[i, 'predict'] = predict_value
        predict_marked += 1
        
        if debug and i < 5:
            print(f"  [Строка {i}] ✓ predict = {predict_value:.4f}")
    
    print(f"\n[PREDICT] Завершено:")
    print(f"  Промаркировано: {predict_marked}")
    print(f"  Пустых fractal0: {predict_empty_fractal0}")
    print(f"  Ошибок парсинга: {predict_parse_errors}")
    print(f"  Фракталов выпало из списка: {predict_not_found}")
    
    # Сохранение результатов
    df.to_csv(output_path, sep=';', index=False)
    print(f"[PREDICT] Результат сохранен в {output_path}")
    
    return df


def label_signals(input_path, output_path, debug=False):
    """
    Маркирует сигналы в CSV файле с фрактальными данными.
    
    Args:
        input_path: путь к входному CSV файлу
        output_path: путь для сохранения результатов
        debug: включить отладочный вывод (по умолчанию False)
    """
    if debug:
        print("=" * 60)
        print("НАЧАЛО ОБРАБОТКИ")
        print("=" * 60)
    
    # Загрузка данных
    df = pd.read_csv(input_path, sep=';')

    # Убираем пробелы из названий колонок (на всякий случай)
    df.columns = [c.strip() for c in df.columns]
    
    # Получаем список колонок с фракталами
    fractal_columns = [col for col in df.columns if col.startswith('fractal')]

    if debug:
        print(f"\n[ЭТАП 1] Загрузка данных")
        print(f"  Всего строк: {len(df)}")
        print(f"  Найдено колонок с фракталами: {len(fractal_columns)}")
        print(f"  Колонки: {fractal_columns[:5]}...")
        print(f"  Все колонки DataFrame: {list(df.columns)}")

    # Множество для хранения времен strong фракталов
    strong_levels = set()
    
    if debug:
        print(f"\n[ЭТАП 2] Поиск strong фракталов")
    
    # Поиск strong фракталов (данные уже отсортированы в label_main.py)
    for idx, row in df.iterrows():
        for col_name in fractal_columns:
            fractal_str = row[col_name]
            if pd.isna(fractal_str) or fractal_str == '':
                continue
            
            parts = str(fractal_str).split(':')
            if len(parts) >= 6:
                try:
                    time_val = int(parts[0])
                    strong = int(parts[5])
                    if strong == 1:
                        if time_val not in strong_levels:
                            strong_levels.add(time_val)
                            if debug:
                                print(f"  [Строка {idx}] Найден strong фрактал: time={time_val}, колонка={col_name}")
                except (ValueError, IndexError):
                    continue
    
    print(f"\n[ЭТАП 2] Завершен: найдено {len(strong_levels)} уникальных strong фракталов")
    if debug:
        print(f"  Времена strong фракталов (первые 10): {sorted(list(strong_levels))[:10]}")
    
    # Второй проход - маркировка сигналов
    if debug:
        print(f"\n[ЭТАП 3] Маркировка сигналов")
    
    signals_marked = 0
    signals_checked = 0
    signals_empty_fractal0 = 0
    signals_parse_errors = 0
    
    for idx, row in df.iterrows():
        fractal0 = row['fractal0']
        if pd.isna(fractal0) or fractal0 == '':
            signals_empty_fractal0 += 1
            if debug and idx < 5:  # Показываем только первые 5 пустых
                print(f"  [Строка {idx}] fractal0 пустой, пропускаем")
            continue
            
        # Разбираем fractal0
        parts = str(fractal0).split(':')
        signals_checked += 1
        
        if len(parts) >= 3:  # Нужен time и direction
            try:
                time_value = int(parts[0])  # time
                direction = int(parts[2])   # direction (индекс 2)
                
                if debug and idx < 10:  # Показываем первые 10 проверок
                    print(f"  [Строка {idx}] fractal0: time={time_value}, direction={direction}, в strong_levels={time_value in strong_levels}")
                
                # Если время есть в strong_levels, маркируем сигнал
                if time_value in strong_levels:
                    df.at[idx, 'signal'] = direction
                    signals_marked += 1
                    if debug:
                        print(f"  [Строка {idx}] ✓ МАРКИРОВКА: signal={direction} для time={time_value}")
                    
            except (ValueError, IndexError) as e:
                signals_parse_errors += 1
                if debug:
                    print(f"  [Строка {idx}] ✗ Ошибка парсинга fractal0: {e}, parts={parts}")
        else:
            signals_parse_errors += 1
            if debug:
                print(f"  [Строка {idx}] ✗ Недостаточно частей в fractal0: {len(parts)} < 3")
    
    print(f"\n[ЭТАП 3] Завершен:")
    print(f"  Проверено строк с fractal0: {signals_checked}")
    print(f"  Помечено сигналов: {signals_marked}")
    print(f"  Пустых fractal0: {signals_empty_fractal0}")
    print(f"  Ошибок парсинга: {signals_parse_errors}")
    
    # Сохранение результатов
    df.to_csv(output_path, sep=';', index=False)
    print(f"\n[ЭТАП 4] Результат сохранен в {output_path}")
    
    if debug:
        print("\n" + "=" * 60)
        print("ОБРАБОТКА ЗАВЕРШЕНА")
        print("=" * 60)
    
    return df


def label_all(input_path, output_path, debug=False):
    """
    Совместная маркировка signal и predict в одном проходе для оптимизации.
    
    Преимущества:
    - Один проход для сбора strong_levels (используется для signal)
    - Один проход для маркировки обоих столбцов
    - Сохранение файла только 1 раз
    
    Args:
        input_path: путь к входному CSV файлу
        output_path: путь для сохранения результатов
        debug: включить отладочный вывод
    """
    if debug:
        print("=" * 60)
        print("СОВМЕСТНАЯ МАРКИРОВКА SIGNAL + PREDICT")
        print("=" * 60)
    
    # Загрузка данных
    df = pd.read_csv(input_path, sep=';')
    df.columns = [c.strip() for c in df.columns]
    
    # Получаем список колонок с фракталами
    fractal_columns = [col for col in df.columns if col.startswith('fractal')]
    total_rows = len(df)
    
    if debug:
        print(f"\n[ЗАГРУЗКА] Строк: {total_rows}, колонок фракталов: {len(fractal_columns)}")
    
    # === ЭТАП 1: Сбор strong_levels для signal ===
    strong_levels = set()
    
    for idx, row in df.iterrows():
        for col_name in fractal_columns:
            parsed = parse_fractal(row[col_name])
            if parsed and parsed['strong'] == 1:
                if parsed['time'] not in strong_levels:
                    strong_levels.add(parsed['time'])
                    if debug:
                        print(f"  [Строка {idx}] Strong фрактал: time={parsed['time']}")
    
    print(f"\n[SIGNAL] Найдено {len(strong_levels)} уникальных strong фракталов")
    
    # === ЭТАП 2: Маркировка signal и predict ===
    signals_marked = 0
    predict_marked = 0
    empty_fractal0 = 0
    parse_errors = 0
    
    for i in range(total_rows):
        row_i = df.iloc[i]
        
        # Парсим fractal0
        fractal0 = parse_fractal(row_i['fractal0'])
        if fractal0 is None:
            empty_fractal0 += 1
            continue
        
        target_time = fractal0['time']
        target_direction = fractal0['direction']
        
        # --- Маркировка signal ---
        if target_time in strong_levels:
            df.at[i, 'signal'] = target_direction
            signals_marked += 1
            if debug:
                print(f"  [Строка {i}] ✓ signal={target_direction}")
        
        # --- Маркировка predict ---
        max_back = fractal0['back']
        
        for j in range(i + 1, total_rows):
            row_j = df.iloc[j]
            
            found = find_fractal_by_time(row_j, fractal_columns, target_time)
            
            if found is None:
                # Фрактал выпал
                break
            
            if found['back'] > max_back:
                max_back = found['back']
            
            if found['break'] > 0:
                # Фрактал пробит
                break
        
        predict_value = -max_back * target_direction
        df.at[i, 'predict'] = predict_value
        predict_marked += 1
        
        if debug and i < 5:
            print(f"  [Строка {i}] ✓ predict={predict_value:.4f}")
    
    # === Статистика ===
    print(f"\n[РЕЗУЛЬТАТ]")
    print(f"  Signal помечено: {signals_marked}")
    print(f"  Predict помечено: {predict_marked}")
    print(f"  Пустых fractal0: {empty_fractal0}")
    print(f"  Ошибок парсинга: {parse_errors}")
    
    # Сохранение
    df.to_csv(output_path, sep=';', index=False)
    print(f"[СОХРАНЕНО] {output_path}")
    
    return df


# Пример использования:
# label_signals('Nero.csv', 'Nero_labeled.csv')
# label_predict('Nero.csv', 'Nero_predict.csv')
# label_all('Nero.csv', 'Nero_full.csv')  # Рекомендуется для эффективности