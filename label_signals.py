import pandas as pd

def label_signals(input_path, output_path):
    """
    Маркирует сигналы в CSV файле с фрактальными данными.
    
    Args:
        input_path: путь к входному CSV файлу
        output_path: путь для сохранения результатов
    """
    # Загрузка данных
    df = pd.read_csv(input_path, sep=';')
    
    # Поиск фракталов с strong=1
    strong_levels = set()
    
    for idx, row in df.iterrows():
        # Проверяем все fractal колонки (с пробелами)
        for col in df.columns:
            if col.strip().startswith('fractal'):
                fractal_data = row[col]
                if pd.isna(fractal_data) or fractal_data == '':
                    continue
                    
                # Разбираем фрактал на компоненты
                parts = str(fractal_data).split(':')
                if len(parts) >= 6:  # Убеждаемся, что есть enough компонентов
                    try:
                        strong = int(parts[5])  # strong - 6-й элемент (индекс 5)
                        if strong == 1:
                            time_value = int(parts[0])  # time - 1-й элемент (индекс 0)
                            strong_levels.add(time_value)
                    except (ValueError, IndexError):
                        continue
    
    print(f"Найдено {len(strong_levels)} strong фракталов")
    
    # Второй проход - маркировка сигналов
    for idx, row in df.iterrows():
        fractal0 = row[' fractal0 ']  # Учитываем пробелы в названии колонки
        if pd.isna(fractal0) or fractal0 == '':
            continue
            
        # Разбираем fractal0
        parts = str(fractal0).split(':')
        if len(parts) >= 2:  # Нужен time и direction
            try:
                time_value = int(parts[0])  # time
                direction = int(parts[2])   # direction (индекс 2)
                
                # Если время есть в strong_levels, маркируем сигнал
                if time_value in strong_levels:
                    df.at[idx, ' signal '] = direction  # Учитываем пробелы в названии колонки
                    
            except (ValueError, IndexError):
                continue
    
    # Сохранение результатов
    df.to_csv(output_path, sep=';', index=False)
    print(f"Результат сохранен в {output_path}")
    
    return df

# Пример использования:
# label_signals('Nero.csv', 'Nero_labeled.csv')