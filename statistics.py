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
        self.n_samples = 0
        self.signal_counts = Counter()
        
        # Для каждого из 11 признаков фрактала
        self.feature_names = ['fractal_time', 'price', 'direction', 'front', 
                            'back', 'strong', 'break', 'reverse', 
                            'power', 'count', 'impulse']
        
        # Онлайн статистика по методу Уэлфорда
        self.means = {f: 0.0 for f in self.feature_names}
        self.m2s = {f: 0.0 for f in self.feature_names}  # для вариации
        self.mins = {f: float('inf') for f in self.feature_names}
        self.maxs = {f: float('-inf') for f in self.feature_names}
        self.value_lists = {f: [] for f in self.feature_names}  # для квантилей
        
    def update(self, chunk_data: pd.DataFrame, parsed_fractals: Dict):
        """Обновление статистики на основе чанка"""
        # Подсчёт классов
        self.signal_counts.update(chunk_data['signal'].value_counts().to_dict())
        
        # Обновление статистики по признакам (метод Уэлфорда для онлайн расчёта)
        for feature_idx, feature_name in enumerate(self.feature_names):
            values = parsed_fractals[feature_name]
            
            for value in values:
                self.n_samples += 1
                delta = value - self.means[feature_name]
                self.means[feature_name] += delta / self.n_samples
                delta2 = value - self.means[feature_name]
                self.m2s[feature_name] += delta * delta2
                
                self.mins[feature_name] = min(self.mins[feature_name], value)
                self.maxs[feature_name] = max(self.maxs[feature_name], value)
            
            # Сохраняем выборку для квантилей (ограничиваем размер)
            self.value_lists[feature_name].extend(values[:1000])
    
    def get_summary(self) -> Dict:
        """Финальная статистика"""
        summary = {
            'total_samples': sum(self.signal_counts.values()),
            'class_distribution': dict(self.signal_counts),
            'features': {}
        }
        
        for feature_name in self.feature_names:
            n = self.n_samples
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
