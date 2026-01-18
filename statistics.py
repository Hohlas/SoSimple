import pandas as pd
import numpy as np
import json
from collections import Counter, defaultdict
from typing import Dict, List

# ============================================================================
# ЭТАП 1: ПОТОКОВАЯ ОБРАБОТКА И СБОР СТАТИСТИКИ
# ============================================================================

class StreamingStats:
    """Класс для накопления статистики по чанкам [web:7]"""
    def __init__(self):
        self.signal_counts = Counter()
        
        # Для каждого из 11 признаков фрактала
        self.feature_names = ['fractal_time', 'price', 'direction', 'front', 
                            'back', 'strong', 'break', 'reverse', 
                            'power', 'count', 'impulse']
        
        # Онлайн статистика по методу Уэлфорда
        # ИСПРАВЛЕНО: Отдельный счётчик для каждого признака
        self.n_per_feature = {f: 0 for f in self.feature_names}
        self.means = {f: 0.0 for f in self.feature_names}
        self.m2s = {f: 0.0 for f in self.feature_names}  # для вариации
        self.mins = {f: float('inf') for f in self.feature_names}
        self.maxs = {f: float('-inf') for f in self.feature_names}
        
        # Для квантилей: reservoir sampling с ограничением
        self.value_lists = {f: [] for f in self.feature_names}
        self.value_lists_max_size = 10000  # Максимальный размер выборки для квантилей
        self._rng = np.random.default_rng(42)  # Фиксированный seed для воспроизводимости
        
    def update(self, chunk_data: pd.DataFrame, parsed_fractals: Dict):
        """Обновление статистики на основе чанка"""
        # Подсчёт классов
        for signal in chunk_data['signal']:
            self.signal_counts[int(signal)] += 1
        
        # Обновление статистики по признакам (метод Уэлфорда для онлайн расчёта)
        # ИСПРАВЛЕНО: Используем отдельный счётчик для каждого признака
        for feature_name in self.feature_names:
            values = parsed_fractals[feature_name]
            
            for value in values:
                n = self.n_per_feature[feature_name] + 1
                self.n_per_feature[feature_name] = n
                
                delta = value - self.means[feature_name]
                self.means[feature_name] += delta / n
                delta2 = value - self.means[feature_name]
                self.m2s[feature_name] += delta * delta2
                
                self.mins[feature_name] = min(self.mins[feature_name], value)
                self.maxs[feature_name] = max(self.maxs[feature_name], value)
            
            # ИСПРАВЛЕНО: Reservoir sampling для несмещённой выборки квантилей
            self._update_value_list(feature_name, values)
    
    def _update_value_list(self, feature_name: str, new_values: List):
        """
        Reservoir sampling для формирования несмещённой выборки.
        Гарантирует, что каждый элемент имеет равную вероятность попасть в выборку.
        """
        current_list = self.value_lists[feature_name]
        max_size = self.value_lists_max_size
        
        for value in new_values:
            if len(current_list) < max_size:
                # Резервуар ещё не заполнен — добавляем напрямую
                current_list.append(value)
            else:
                # Резервуар заполнен — вероятностная замена
                # Вероятность замены = max_size / (n_per_feature + 1)
                n_seen = self.n_per_feature[feature_name]
                j = self._rng.integers(0, n_seen + 1)
                if j < max_size:
                    current_list[j] = value
    
    def get_summary(self) -> Dict:
        """Финальная статистика"""
        summary = {
            'total_samples': sum(self.signal_counts.values()),
            'class_distribution': dict(self.signal_counts),
            'features': {}
        }
        
        for feature_name in self.feature_names:
            n = self.n_per_feature[feature_name]
            variance = self.m2s[feature_name] / (n - 1) if n > 1 else 0
            std = np.sqrt(variance)
            
            # Квантили из накопленной выборки
            values_sample = np.array(self.value_lists[feature_name])
            if len(values_sample) > 0:
                q25, median, q75 = np.percentile(values_sample, [25, 50, 75])
            else:
                q25, median, q75 = 0, 0, 0
            
            summary['features'][feature_name] = {
                'mean': float(self.means[feature_name]),
                'std': float(std),
                'min': float(self.mins[feature_name]),
                'max': float(self.maxs[feature_name]),
                'q25': float(q25),
                'median': float(median),
                'q75': float(q75)
            }
        
        return summary


def parse_fractal_column(fractal_str: str) -> Dict:
    """Парсинг строки фрактала 'time:price:direction:...' в словарь"""
    parts = fractal_str.split(':')
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
            'reverse': int(parts[7]),
            'power': float(parts[8]),
            'count': int(parts[9]),
            'impulse': float(parts[10])
        }
    except (ValueError, IndexError):
        return None  # Некорректные данные

def process_nero_csv(filepath: str, chunksize: int = 500):
    """
    Основная функция потоковой обработки
    """
    stats = StreamingStats()
    
    # Чтение файла чанками [web:7]
    chunks_reader = pd.read_csv(filepath, sep=';', chunksize=chunksize, 
                                low_memory=False)
    
    all_rare_events = []  # Для сбора редких событий
    normal_samples = []   # Для сбора нормальных событий
    
    chunk_counter = 0
    total_fractals_processed = 0
    
    for chunk in chunks_reader:
        chunk_counter += 1
        print(f"Обработка чанка {chunk_counter}...")
        
        # Нормализация имён колонок: убираем пробелы в начале и конце
        chunk.columns = chunk.columns.str.strip()
        
        # Парсинг всех фрактальных колонок
        parsed_fractals = defaultdict(list)
        
        # Предполагаем, что колонки: time, signal, fractal0, ..., fractal98
        fractal_columns = [col for col in chunk.columns if col.startswith('fractal')]
        
        for idx, row in chunk.iterrows():
            # перебираем ВСЕ 99 фракталов
            for fractal_col in fractal_columns:
                fractal_str = row[fractal_col]
                parsed = parse_fractal_column(fractal_str)
                
                if parsed:
                    total_fractals_processed += 1
                    for key, value in parsed.items():
                        parsed_fractals[key].append(value)
        # После обработки чанка:
        print(f"Обработка чанка {chunk_counter}... (фракталов: {total_fractals_processed})")

        # Обновление статистики
        stats.update(chunk, parsed_fractals)
        
        # Сбор стратифицированной выборки [web:13][web:14]
        rare_events = chunk[chunk['signal'] != 0]
        if len(rare_events) > 0:
            all_rare_events.append(rare_events)
        
        # Случайная выборка из нормальных событий (10% от чанка)
        normal_events = chunk[chunk['signal'] == 0]
        if len(normal_events) > 0:
            sample_size = min(50, len(normal_events))
            normal_samples.append(normal_events.sample(n=sample_size, random_state=42))
    
    # ========================================================================
    # ГЕНЕРАЦИЯ ОТЧЁТОВ
    # ========================================================================
    
    # 1. statistics_summary.json
    summary = stats.get_summary()
    
    # Добавляем процент дисбаланса
    total = summary['total_samples']
    summary['class_percentages'] = {
        k: f"{(v/total)*100:.2f}%" 
        for k, v in summary['class_distribution'].items()
    }
    
    with open('statistics_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print("[OK] Создан statistics_summary.json")
    
    # 2. class_balance_report.csv
    class_report = pd.DataFrame([
        {
            'signal': signal,
            'count': count,
            'percentage': f"{(count/total)*100:.2f}%"
        }
        for signal, count in sorted(summary['class_distribution'].items())
    ])
    class_report.to_csv('class_balance_report.csv', index=False)
    
    print("[OK] Создан class_balance_report.csv")
    
    # 3. feature_distributions.csv
    feature_dists = []
    for feature_name, feature_stats in summary['features'].items():
        feature_dists.append({
            'feature': feature_name,
            **feature_stats
        })
    
    pd.DataFrame(feature_dists).to_csv('feature_distributions.csv', index=False)
    
    print("[OK] Создан feature_distributions.csv")
    
    # 4. Стратифицированная выборка [web:13][web:15]
    stratified_sample = pd.concat(
        all_rare_events + normal_samples,
        ignore_index=True
    )
    
    # Перемешиваем
    stratified_sample = stratified_sample.sample(frac=1, random_state=42).reset_index(drop=True)
    
    stratified_sample.to_csv('nero_sample_stratified.csv', sep=';', index=False)
    
    print(f"[OK] Создан nero_sample_stratified.csv")
    print(f"  Всего строк: {len(stratified_sample)}")
    print(f"  Распределение классов:")
    print(stratified_sample['signal'].value_counts())
    
    # 5. class_statistics.json
    print("\n[ГЕНЕРАЦИЯ] Создание class_statistics.json...")
    class_stats = {}
    
    # Загружаем весь файл для анализа первого фрактала по классам
    print("  Загрузка данных для class_statistics.json...")
    final_df = pd.read_csv(filepath, sep=';', low_memory=False)
    final_df.columns = final_df.columns.str.strip()
    
    # Определяем имя колонки первого фрактала
    fractal_columns = [col for col in final_df.columns if col.startswith('fractal')]
    if len(fractal_columns) == 0:
        print("[WARNING] Колонки с фракталами не найдены, пропускаем class_statistics.json")
    else:
        # Используем первую колонку с фракталом (fractal0 или fractal[0])
        first_fractal_col = sorted(fractal_columns)[0]  # сортируем для детерминированности
        
        for signal_val in [-1, 0, 1]:
            class_rows = final_df[final_df['signal'] == signal_val]
            
            if len(class_rows) == 0:
                class_stats[str(signal_val)] = {
                    'count': 0,
                    'percentage': '0.00%',
                    'fractal_0_features': {}
                }
                continue
            
            # Парсинг первого фрактала из каждой строки класса
            first_fractal_stats = {}
            for feature_idx, feature_name in enumerate(stats.feature_names):
                feature_values = []
                for _, row in class_rows.iterrows():
                    fractal_str = row[first_fractal_col]
                    if pd.isna(fractal_str) or fractal_str == '':
                        continue
                    try:
                        fractal_parts = str(fractal_str).split(':')
                        if len(fractal_parts) > feature_idx:
                            feature_values.append(float(fractal_parts[feature_idx]))
                    except (ValueError, IndexError):
                        continue
                
                if len(feature_values) > 0:
                    first_fractal_stats[feature_name] = {
                        'mean': float(np.mean(feature_values)),
                        'std': float(np.std(feature_values)),
                        'min': float(np.min(feature_values)),
                        'max': float(np.max(feature_values))
                    }
                else:
                    first_fractal_stats[feature_name] = {
                        'mean': 0.0,
                        'std': 0.0,
                        'min': 0.0,
                        'max': 0.0
                    }
            
            class_stats[str(signal_val)] = {
                'count': len(class_rows),
                'percentage': f"{len(class_rows)/len(final_df)*100:.2f}%",
                'fractal_0_features': first_fractal_stats
            }

        with open('class_statistics.json', 'w', encoding='utf-8') as f:
            json.dump(class_stats, f, indent=2, ensure_ascii=False)

        print("[OK] Создан class_statistics.json")
    
    return summary


# ============================================================================
# ЗАПУСК ОБРАБОТКИ
# ============================================================================

if __name__ == "__main__":
    print("Начало обработки Nero_train_labeled.csv...")
    print("="*60)
    
    summary = process_nero_csv('Nero_train_labeled.csv', chunksize=500)
    
    print("="*60)
    print("Обработка завершена!")
    print(f"\nВсего обработано строк: {summary['total_samples']}")
    print(f"Распределение классов: {summary['class_distribution']}")

    print(f"\nСтатистика по признаку 'strong':")
    print(f"  mean: {summary['features']['strong']['mean']:.4f}")
    print(f"  std: {summary['features']['strong']['std']:.4f}")
    print(f"  min: {summary['features']['strong']['min']}")
    print(f"  max: {summary['features']['strong']['max']}")
    
    print(f"\nСтатистика по признаку 'break':")
    print(f"  mean: {summary['features']['break']['mean']:.4f}")
    print(f"  std: {summary['features']['break']['std']:.4f}")
    print(f"  max: {summary['features']['break']['max']}")
