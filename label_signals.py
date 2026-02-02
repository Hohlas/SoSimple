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
        row: строка DataFrame (namedtuple из itertuples или Series)
        fractal_columns: список колонок с фракталами
        target_time: искомое время фрактала
        
    Returns:
        dict с параметрами фрактала или None если не найден
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
    Совместная маркировка signal и predict с оптимизацией производительности.
    
    Args:
        input_path: путь к входному CSV файлу
        output_path: путь для сохранения результатов
        debug: включить отладочный вывод
        label_signal: маркировать столбец signal (по умолчанию True)
        label_predict: маркировать столбец predict (по умолчанию True)
        
    Returns:
        pd.DataFrame с маркированными данными
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
    
    # Получаем список колонок с фракталами (динамически, не привязываясь к n=100)
    fractal_columns = [col for col in df.columns if col.startswith('fractal')]
    total_rows = len(df)
    
    if debug:
        print(f"\n[ЗАГРУЗКА] Строк: {total_rows}, колонок фракталов: {len(fractal_columns)}")
    
    # === ЭТАП 1: Сбор strong_levels для signal (если нужно) ===
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
    # Статистика
    signals_marked = 0
    predict_marked = 0
    empty_fractal0 = 0
    fractals_dropped = 0  # Количество фракталов, выпавших до пробития
    
    # Конвертируем в список для доступа по индексу (для predict нужен forward-looking)
    rows_list = list(df.itertuples(index=False))
    
    for i, row_i in enumerate(rows_list):
        # Парсим fractal0
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
            max_back = fractal0['back']
            was_broken = False
            
            for j in range(i + 1, total_rows):
                row_j = rows_list[j]
                
                found = find_fractal_by_time(row_j, fractal_columns, target_time)
                
                if found is None:
                    # Фрактал выпал из списка
                    fractals_dropped += 1
                    if debug and i < 5:
                        print(f"    [Строка {j}] Фрактал time={target_time} выпал")
                    break
                
                if found['back'] > max_back:
                    max_back = found['back']
                
                if found['break'] > 0:
                    # Фрактал пробит
                    was_broken = True
                    if debug and i < 5:
                        print(f"    [Строка {j}] Фрактал пробит: break={found['break']}, max_back={max_back}")
                    break
            
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
    
    # Сохранение
    df.to_csv(output_path, sep=';', index=False)
    print(f"[СОХРАНЕНО] {output_path}")
    
    return df


def label_signals(input_path, output_path, debug=False):
    """
    Маркирует только столбец signal.
    Обёртка над label_all() для обратной совместимости.
    """
    return label_all(input_path, output_path, debug=debug, 
                     label_signal=True, label_predict=False)


def label_predict_only(input_path, output_path, debug=False):
    """
    Маркирует только столбец predict.
    Обёртка над label_all().
    """
    return label_all(input_path, output_path, debug=debug, 
                     label_signal=False, label_predict=True)


# Пример использования:
# label_all('Nero.csv', 'Nero_full.csv')  # Рекомендуется - маркирует оба столбца
# label_signals('Nero.csv', 'Nero_signals.csv')  # Только signal
# label_predict_only('Nero.csv', 'Nero_predict.csv')  # Только predict