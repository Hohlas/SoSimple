import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Читаем ноутбук
with open(r'c:\Users\hohla\git\SoSimple\statistics\EDA.ipynb', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Новый код для ячейки 3 (загрузка данных)
new_cell_3_code = '''def parse_fractal_string(fractal_str: str) -> dict:
    """
    Парсинг строки фрактала в словарь признаков.
    
    Args:
        fractal_str: строка формата 'time:price:direction:front:back:strong:break:reverse:power:count:impulse'
    
    Returns:
        dict с 11 признаками или None при ошибке парсинга
    """
    parts = str(fractal_str).split(':')
    if len(parts) != 11:
        return None
    
    try:
        return {
            'fractal_time': int(parts[0]),
            'price': float(parts[1]),
            'direction': int(parts[2]),
            'front': float(parts[3]),
            'back': float(parts[4]),
            'strong': int(parts[5]),
            'break': int(parts[6]),
            'reverse': float(parts[7]),
            'power': float(parts[8]),
            'count': int(parts[9]),
            'impulse': float(parts[10])
        }
    except (ValueError, IndexError):
        return None


def load_nero_data(filepath: str) -> tuple:
    """
    Загрузка и парсинг данных Nero с динамическим определением количества фракталов.
    
    Args:
        filepath: путь к CSV файлу
    
    Returns:
        tuple: (raw_df, fractal_0_df, fractal_cols, n_fractals)
    """
    import re
    
    print(f"Загрузка данных из {filepath}...")
    df = pd.read_csv(filepath, sep=';', low_memory=False)
    df.columns = df.columns.str.strip()
    
    print(f"Размер датасета: {df.shape}")
    print(f"Колонки: {list(df.columns[:6])}... (всего {len(df.columns)})")
    
    # Проверка обязательных столбцов
    required_cols = ['human_time', 'signal', 'predict', 'ATR']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Отсутствуют обязательные столбцы: {missing_cols}")
    print(f"✅ Все обязательные столбцы найдены: {required_cols}")
    
    # Динамическое определение колонок фракталов
    # Поддержка обоих форматов: fractal0, fractal1, ... или fractal_0, fractal_1, ...
    fractal_cols = [col for col in df.columns if col.startswith('fractal')]
    
    # Сортировка по номеру фрактала
    def extract_fractal_num(col_name):
        match = re.search(r'fractal_?(\\d+)', col_name)
        return int(match.group(1)) if match else 0
    
    fractal_cols = sorted(fractal_cols, key=extract_fractal_num)
    n_fractals = len(fractal_cols)
    
    print(f"✅ Найдено {n_fractals} фрактальных колонок")
    
    # Парсинг первого фрактала (fractal[0]) для всех строк
    first_fractal_col = fractal_cols[0]
    fractal_0_data = []
    
    for idx, row in df.iterrows():
        parsed = parse_fractal_string(row[first_fractal_col])
        if parsed:
            parsed['signal'] = row['signal']
            parsed['predict'] = row['predict']
            parsed['ATR'] = row['ATR']
            parsed['human_time'] = row['human_time']
            parsed['row_idx'] = idx
            fractal_0_data.append(parsed)
    
    fractal_0_df = pd.DataFrame(fractal_0_data)
    print(f"✅ Успешно распарсено {len(fractal_0_df)} строк fractal[0]")
    
    return df, fractal_0_df, fractal_cols, n_fractals

# Загрузка данных
raw_df, fractal_0_df, fractal_cols, N_FRACTALS = load_nero_data('Nero_train_labeled.csv')

# Признаки фракталов
FEATURE_NAMES = ['fractal_time', 'price', 'direction', 'front', 'back', 
                 'strong', 'break', 'reverse', 'power', 'count', 'impulse']

print(f"\\n📊 Количество фракталов в строке: {N_FRACTALS}")
print("\\nПервые строки fractal[0]:")
fractal_0_df.head()'''

# Обновляем ячейку 3
data['cells'][3]['source'] = new_cell_3_code.split('\n')
data['cells'][3]['source'] = [line + '\n' if i < len(new_cell_3_code.split('\n')) - 1 else line 
                              for i, line in enumerate(new_cell_3_code.split('\n'))]
# Очищаем outputs
data['cells'][3]['outputs'] = []
data['cells'][3]['execution_count'] = None

# Сохраняем
with open(r'c:\Users\hohla\git\SoSimple\statistics\EDA.ipynb', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

print("Ячейка 3 обновлена успешно!")
