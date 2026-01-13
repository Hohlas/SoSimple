import pandas as pd

def process_row_fractals(row_data, fractal_columns, strong_levels, debug=False, row_idx=None):
    """
    Обрабатывает фракталы в строке: сортирует по времени и находит strong фракталы.
    
    Args:
        row_data: данные строки (Series)
        fractal_columns: список названий колонок с фракталами
        strong_levels: множество для хранения времен strong фракталов
        debug: включить отладочный вывод
        row_idx: индекс строки для отладки
    
    Returns:
        list: отсортированные фракталы (новые первые)
    """
    fractals = []
    strong_found_in_row = []
    
    # Собираем и парсим все фракталы
    for col_name in fractal_columns:
        fractal_str = row_data[col_name]
        if pd.isna(fractal_str) or fractal_str == '':
            continue
            
        parts = str(fractal_str).split(':')
        if len(parts) >= 6:  # Убеждаемся, что есть все необходимые поля
            try:
                time_val = int(parts[0])  # time
                strong = int(parts[5])     # strong
                
                # Добавляем strong фракталы в множество
                if strong == 1:
                    if time_val not in strong_levels:
                        strong_levels.add(time_val)
                        strong_found_in_row.append(time_val)
                        if debug:
                            print(f"  [Строка {row_idx}] Найден strong фрактал: time={time_val}, колонка={col_name}")
                
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
    
    if debug and strong_found_in_row:
        print(f"  [Строка {row_idx}] Найдено strong фракталов в строке: {len(strong_found_in_row)}")
    
    # Возвращаем отсортированные фракталы
    return [f['data'] for f in fractals]

def label_signals(input_path, output_path, debug=False):
    """
    Маркирует сигналы в CSV файле с фрактальными данными.
    Сортирует фракталы по времени и находит strong фракталы в одном проходе.
    
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
        print(f"\n[ЭТАП 2] Поиск strong фракталов и сортировка")
    
    # Первый проход: сортировка фракталов и поиск strong фракталов
    for idx, row in df.iterrows():
        # Обрабатываем фракталы в строке
        sorted_fractals = process_row_fractals(row, fractal_columns, strong_levels, debug=debug, row_idx=idx)
        
        # Перезаписываем отсортированные фракталы обратно в DataFrame
        for i, fractal_data in enumerate(sorted_fractals):
            if i < len(fractal_columns):
                df.at[idx, fractal_columns[i]] = fractal_data
        
        # Очищаем оставшиеся колонки, если фракталов меньше, чем колонок
        for i in range(len(sorted_fractals), len(fractal_columns)):
            df.at[idx, fractal_columns[i]] = ''
    
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

# Пример использования:
# label_signals('Nero.csv', 'Nero_labeled.csv')