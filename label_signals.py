import pandas as pd

def process_row_fractals(row_data, fractal_columns, strong_levels):
    """
    Обрабатывает фракталы в строке: сортирует по времени и находит strong фракталы.
    
    Args:
        row_data: данные строки (Series)
        fractal_columns: список названий колонок с фракталами
        strong_levels: множество для хранения времен strong фракталов
    
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
        if len(parts) >= 6:  # Убеждаемся, что есть все необходимые поля
            try:
                time_val = int(parts[0])  # time
                strong = int(parts[5])     # strong
                
                # Добавляем strong фракталы в множество
                if strong == 1:
                    strong_levels.add(time_val)
                
                fractals.append({
                    'time': time_val,
                    'data': fractal_str
                })
            except (ValueError, IndexError):
                continue
    
    # Сортируем по времени в обратном порядке (новые первые)
    fractals.sort(key=lambda x: x['time'], reverse=True)
    
    # Возвращаем отсортированные фракталы
    return [f['data'] for f in fractals]

def label_signals(input_path, output_path):
    """
    Маркирует сигналы в CSV файле с фрактальными данными.
    Сортирует фракталы по времени и находит strong фракталы в одном проходе.
    
    Args:
        input_path: путь к входному CSV файлу
        output_path: путь для сохранения результатов
    """
    # Загрузка данных
    df = pd.read_csv(input_path, sep=';')
    
    # Получаем список колонок с фракталами
    fractal_columns = [col for col in df.columns if col.startswith('fractal')]
        
    # Множество для хранения времен strong фракталов
    strong_levels = set()
    
    # Первый проход: сортировка фракталов и поиск strong фракталов
    for idx, row in df.iterrows():
        # Обрабатываем фракталы в строке
        sorted_fractals = process_row_fractals(row, fractal_columns, strong_levels)
        
        # Перезаписываем отсортированные фракталы обратно в DataFrame
        for i, fractal_data in enumerate(sorted_fractals):
            if i < len(fractal_columns):
                df.at[idx, fractal_columns[i]] = fractal_data
        
        # Очищаем оставшиеся колонки, если фракталов меньше, чем колонок
        for i in range(len(sorted_fractals), len(fractal_columns)):
            df.at[idx, fractal_columns[i]] = ''
    
    print(f"Найдено {len(strong_levels)} strong фракталов")
    
    # Второй проход - маркировка сигналов
    for idx, row in df.iterrows():
        fractal0 = row['fractal0']
        if pd.isna(fractal0) or fractal0 == '':
            continue
            
        # Разбираем fractal0
        parts = str(fractal0).split(':')
        if len(parts) >= 3:  # Нужен time и direction
            try:
                time_value = int(parts[0])  # time
                direction = int(parts[2])   # direction (индекс 2)
                
                # Если время есть в strong_levels, маркируем сигнал
                if time_value in strong_levels:
                    df.at[idx, 'signal'] = direction
                    
            except (ValueError, IndexError):
                continue
    
    # Сохранение результатов
    df.to_csv(output_path, sep=';', index=False)
    print(f"Результат сохранен в {output_path}")
    
    return df

# Пример использования:
# label_signals('Nero.csv', 'Nero_labeled.csv')