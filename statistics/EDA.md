# Exploratory Data Analysis: Nero Dataset

**Цель:** Анализ данных для прогнозирования разворотов тренда на Forex (H1)

**Структура данных:**
- X ∈ R^{5042×99×11} — входной тензор
- y ∈ {-1, 0, 1} — целевая переменная (экстремальный дисбаланс классов)
- 11 признаков фрактала: fractal_time, price, direction, front, back, strong, break, reverse, power, count, impulse


```python
# Импорт библиотек
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import mannwhitneyu, ttest_ind, shapiro, normaltest
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
from collections import defaultdict
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Настройки визуализации
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14

# Путь для сохранения графиков
PLOTS_DIR = 'plots/'

# Цвета для классов
CLASS_COLORS = {-1: '#e74c3c', 0: '#3498db', 1: '#2ecc71'}
CLASS_NAMES = {-1: 'Sell (-1)', 0: 'Neutral (0)', 1: 'Buy (1)'}

print("Библиотеки загружены успешно!")
```

    Библиотеки загружены успешно!
    

## 1. Загрузка и парсинг данных


```python
def parse_fractal_string(fractal_str: str) -> dict:
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
            'reverse': int(parts[7]),
            'power': float(parts[8]),
            'count': int(parts[9]),
            'impulse': float(parts[10])
        }
    except (ValueError, IndexError):
        return None


def load_nero_data(filepath: str) -> tuple:
    """
    Загрузка и парсинг данных Nero.
    
    Args:
        filepath: путь к CSV файлу
    
    Returns:
        tuple: (raw_df, fractal_0_df, all_fractals_dict)
    """
    print(f"Загрузка данных из {filepath}...")
    df = pd.read_csv(filepath, sep=';', low_memory=False)
    df.columns = df.columns.str.strip()
    
    print(f"Размер датасета: {df.shape}")
    print(f"Колонки: {list(df.columns[:5])}... (всего {len(df.columns)})")
    
    # Определяем колонки фракталов
    fractal_cols = sorted([col for col in df.columns if col.startswith('fractal')])
    print(f"Найдено {len(fractal_cols)} фрактальных колонок")
    
    # Парсинг первого фрактала (fractal[0]) для всех строк
    first_fractal_col = fractal_cols[0]
    fractal_0_data = []
    
    for idx, row in df.iterrows():
        parsed = parse_fractal_string(row[first_fractal_col])
        if parsed:
            parsed['signal'] = row['signal']
            parsed['row_idx'] = idx
            fractal_0_data.append(parsed)
    
    fractal_0_df = pd.DataFrame(fractal_0_data)
    print(f"Успешно распарсено {len(fractal_0_df)} строк fractal[0]")
    
    return df, fractal_0_df, fractal_cols

# Загрузка данных
raw_df, fractal_0_df, fractal_cols = load_nero_data('Nero_train_labeled.csv')

# Признаки фракталов
FEATURE_NAMES = ['fractal_time', 'price', 'direction', 'front', 'back', 
                 'strong', 'break', 'reverse', 'power', 'count', 'impulse']

print("\nПервые строки fractal[0]:")
fractal_0_df.head()
```

    Загрузка данных из Nero_train_labeled.csv...
    Размер датасета: (5042, 101)
    Колонки: ['time', 'signal', 'fractal0', 'fractal1', 'fractal2']... (всего 101)
    Найдено 99 фрактальных колонок
    Успешно распарсено 5042 строк fractal[0]
    
    Первые строки fractal[0]:
    




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>fractal_time</th>
      <th>price</th>
      <th>direction</th>
      <th>front</th>
      <th>back</th>
      <th>strong</th>
      <th>break</th>
      <th>reverse</th>
      <th>power</th>
      <th>count</th>
      <th>impulse</th>
      <th>signal</th>
      <th>row_idx</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1690574400</td>
      <td>0.362908</td>
      <td>-1</td>
      <td>0.043565</td>
      <td>0.012054</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0.454885</td>
      <td>6</td>
      <td>1.7</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1690581600</td>
      <td>0.333038</td>
      <td>-1</td>
      <td>0.059559</td>
      <td>0.011815</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0.798760</td>
      <td>6</td>
      <td>1.5</td>
      <td>0</td>
      <td>1</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1690765200</td>
      <td>0.399689</td>
      <td>1</td>
      <td>0.023036</td>
      <td>0.024946</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0.856923</td>
      <td>7</td>
      <td>1.4</td>
      <td>0</td>
      <td>2</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1690776000</td>
      <td>0.287562</td>
      <td>-1</td>
      <td>0.083909</td>
      <td>0.023155</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0.043343</td>
      <td>2</td>
      <td>1.7</td>
      <td>0</td>
      <td>3</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1690790400</td>
      <td>0.234954</td>
      <td>-1</td>
      <td>0.112078</td>
      <td>0.035569</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0.580494</td>
      <td>5</td>
      <td>2.0</td>
      <td>0</td>
      <td>4</td>
    </tr>
  </tbody>
</table>
</div>




```python
# Распределение классов
class_dist = fractal_0_df['signal'].value_counts().sort_index()
print("Распределение классов:")
for cls, count in class_dist.items():
    pct = count / len(fractal_0_df) * 100
    print(f"  Класс {cls:2d}: {count:5d} ({pct:.2f}%)")

# Визуализация распределения классов
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Bar plot
colors = [CLASS_COLORS[c] for c in class_dist.index]
axes[0].bar([CLASS_NAMES[c] for c in class_dist.index], class_dist.values, color=colors, edgecolor='black')
axes[0].set_title('Распределение классов (абсолютные значения)')
axes[0].set_ylabel('Количество')
for i, (cls, count) in enumerate(class_dist.items()):
    axes[0].text(i, count + 50, str(count), ha='center', fontweight='bold')

# Pie chart
axes[1].pie(class_dist.values, labels=[CLASS_NAMES[c] for c in class_dist.index], 
            colors=colors, autopct='%1.1f%%', startangle=90, explode=[0.05]*3)
axes[1].set_title('Распределение классов (проценты)')

plt.tight_layout()
plt.savefig(f'{PLOTS_DIR}class_distribution.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"\n⚠️ ВНИМАНИЕ: Экстремальный дисбаланс классов!")
print(f"   Minority классы: -1 (n={class_dist[-1]}), +1 (n={class_dist[1]})")
print(f"   Majority класс: 0 (n={class_dist[0]}, {class_dist[0]/len(fractal_0_df)*100:.1f}%)")
```

    Распределение классов:
      Класс -1:   257 (5.10%)
      Класс  0:  4545 (90.14%)
      Класс  1:   240 (4.76%)
    


    
![png](EDA_files/EDA_4_1.png)
    


    
    ⚠️ ВНИМАНИЕ: Экстремальный дисбаланс классов!
       Minority классы: -1 (n=257), +1 (n=240)
       Majority класс: 0 (n=4545, 90.1%)
    

## 2. Статистический анализ признаков по классам


```python
def compute_feature_stats_by_class(df: pd.DataFrame, features: list) -> pd.DataFrame:
    """
    Вычисление статистик для каждого признака по классам.
    
    Args:
        df: DataFrame с данными
        features: список признаков для анализа
    
    Returns:
        DataFrame со статистиками
    """
    stats_data = []
    
    for feature in features:
        for signal in [-1, 0, 1]:
            values = df[df['signal'] == signal][feature]
            
            stats_data.append({
                'feature': feature,
                'class': signal,
                'count': len(values),
                'mean': values.mean(),
                'std': values.std(),
                'min': values.min(),
                'q25': values.quantile(0.25),
                'median': values.quantile(0.50),
                'q75': values.quantile(0.75),
                'max': values.max()
            })
    
    return pd.DataFrame(stats_data)

# Исключаем fractal_time для статистического анализа признаков
analysis_features = [f for f in FEATURE_NAMES if f != 'fractal_time']

# Вычисление статистик
stats_df = compute_feature_stats_by_class(fractal_0_df, analysis_features)

# Форматированный вывод
print("=" * 100)
print("СТАТИСТИКА ПРИЗНАКОВ ПО КЛАССАМ (fractal[0])")
print("=" * 100)

for feature in analysis_features:
    print(f"\n📊 {feature.upper()}")
    print("-" * 80)
    feature_stats = stats_df[stats_df['feature'] == feature]
    display_df = feature_stats[['class', 'count', 'mean', 'std', 'min', 'q25', 'median', 'q75', 'max']].copy()
    display_df = display_df.round(4)
    print(display_df.to_string(index=False))

# Сохранение статистик
stats_df.to_csv(f'{PLOTS_DIR}feature_stats_by_class.csv', index=False)
print(f"\n✅ Статистики сохранены в {PLOTS_DIR}feature_stats_by_class.csv")
```

    ====================================================================================================
    СТАТИСТИКА ПРИЗНАКОВ ПО КЛАССАМ (fractal[0])
    ====================================================================================================
    
    📊 PRICE
    --------------------------------------------------------------------------------
     class  count   mean    std   min    q25  median    q75    max
        -1    257 0.7824 0.2100 0.000 0.7422  0.8341 0.9294 0.9918
         0   4545 0.7960 0.2307 0.000 0.7572  0.8601 0.9550 1.0000
         1    240 0.7935 0.2316 0.081 0.7086  0.8656 0.9660 1.0000
    
    📊 DIRECTION
    --------------------------------------------------------------------------------
     class  count    mean    std  min  q25  median  q75  max
        -1    257 -1.0000 0.0000 -1.0 -1.0    -1.0 -1.0 -1.0
         0   4545  0.0579 0.9984 -1.0 -1.0     1.0  1.0  1.0
         1    240  1.0000 0.0000  1.0  1.0     1.0  1.0  1.0
    
    📊 FRONT
    --------------------------------------------------------------------------------
     class  count   mean    std    min    q25  median    q75  max
        -1    257 0.0659 0.0889 0.0000 0.0229  0.0417 0.0704  1.0
         0   4545 0.0587 0.1771 0.0000 0.0058  0.0125 0.0290  1.0
         1    240 0.1166 0.2106 0.0021 0.0301  0.0529 0.0902  1.0
    
    📊 BACK
    --------------------------------------------------------------------------------
     class  count   mean    std  min    q25  median    q75    max
        -1    257 0.0177 0.0174  0.0 0.0077  0.0124 0.0200 0.1039
         0   4545 0.0107 0.0142  0.0 0.0030  0.0067 0.0127 0.2372
         1    240 0.0205 0.0245  0.0 0.0065  0.0126 0.0228 0.1715
    
    📊 STRONG
    --------------------------------------------------------------------------------
     class  count   mean    std  min  q25  median  q75  max
        -1    257 0.0000 0.0000  0.0  0.0     0.0  0.0  0.0
         0   4545 0.0000 0.0000  0.0  0.0     0.0  0.0  0.0
         1    240 0.0042 0.0645  0.0  0.0     0.0  0.0  1.0
    
    📊 BREAK
    --------------------------------------------------------------------------------
     class  count  mean  std  min  q25  median  q75  max
        -1    257   0.0  0.0  0.0  0.0     0.0  0.0  0.0
         0   4545   0.0  0.0  0.0  0.0     0.0  0.0  0.0
         1    240   0.0  0.0  0.0  0.0     0.0  0.0  0.0
    
    📊 REVERSE
    --------------------------------------------------------------------------------
     class  count   mean    std  min  q25  median  q75  max
        -1    257 0.8599 0.3477  0.0  1.0     1.0  1.0  1.0
         0   4545 0.4539 0.4979  0.0  0.0     0.0  1.0  1.0
         1    240 0.8375 0.3697  0.0  1.0     1.0  1.0  1.0
    
    📊 POWER
    --------------------------------------------------------------------------------
     class  count   mean    std  min    q25  median    q75  max
        -1    257 0.2405 0.2286  0.0 0.0720  0.1638 0.3606  1.0
         0   4545 0.1753 0.2133  0.0 0.0000  0.1002 0.2489  1.0
         1    240 0.2625 0.2611  0.0 0.0717  0.1780 0.3707  1.0
    
    📊 COUNT
    --------------------------------------------------------------------------------
     class  count   mean    std  min  q25  median  q75  max
        -1    257 3.0233 1.5460  1.0  2.0     3.0  4.0  9.0
         0   4545 2.7450 1.6510  1.0  1.0     2.0  4.0 13.0
         1    240 2.9000 1.5411  1.0  2.0     2.0  4.0 10.0
    
    📊 IMPULSE
    --------------------------------------------------------------------------------
     class  count   mean    std  min  q25  median  q75  max
        -1    257 4.0475 1.6059  0.9  2.9     3.8  5.1  9.6
         0   4545 2.5840 1.2148  0.5  1.8     2.3  3.1 12.8
         1    240 3.6558 1.6140  1.1  2.4     3.4  4.6  9.7
    
    ✅ Статистики сохранены в plots/feature_stats_by_class.csv
    

### 2.1 Гистограммы распределений по классам


```python
def plot_histograms_by_class(df: pd.DataFrame, features: list, save_path: str):
    """
    Построение гистограмм для каждого признака с разбивкой по классам.
    """
    n_features = len(features)
    n_cols = 3
    n_rows = (n_features + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4*n_rows))
    axes = axes.flatten()
    
    for idx, feature in enumerate(features):
        ax = axes[idx]
        
        for signal in [-1, 0, 1]:
            values = df[df['signal'] == signal][feature]
            ax.hist(values, bins=30, alpha=0.5, label=CLASS_NAMES[signal], 
                    color=CLASS_COLORS[signal], edgecolor='black', linewidth=0.5)
        
        ax.set_title(feature, fontweight='bold')
        ax.set_xlabel('Значение')
        ax.set_ylabel('Частота')
        ax.legend(loc='upper right', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    # Скрываем пустые axes
    for idx in range(len(features), len(axes)):
        axes[idx].set_visible(False)
    
    plt.suptitle('Распределения признаков fractal[0] по классам', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

plot_histograms_by_class(fractal_0_df, analysis_features, f'{PLOTS_DIR}histograms_by_class.png')
print(f"✅ Гистограммы сохранены в {PLOTS_DIR}histograms_by_class.png")
```


    
![png](EDA_files/EDA_8_0.png)
    


    ✅ Гистограммы сохранены в plots/histograms_by_class.png
    

### 2.2 Boxplots по классам


```python
def plot_boxplots_by_class(df: pd.DataFrame, features: list, save_path: str):
    """
    Построение boxplots для каждого признака с разбивкой по классам.
    """
    n_features = len(features)
    n_cols = 3
    n_rows = (n_features + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4*n_rows))
    axes = axes.flatten()
    
    for idx, feature in enumerate(features):
        ax = axes[idx]
        
        data_to_plot = [df[df['signal'] == s][feature] for s in [-1, 0, 1]]
        bp = ax.boxplot(data_to_plot, labels=[CLASS_NAMES[s] for s in [-1, 0, 1]], 
                        patch_artist=True, notch=True)
        
        for patch, signal in zip(bp['boxes'], [-1, 0, 1]):
            patch.set_facecolor(CLASS_COLORS[signal])
            patch.set_alpha(0.7)
        
        ax.set_title(feature, fontweight='bold')
        ax.set_ylabel('Значение')
        ax.grid(True, alpha=0.3, axis='y')
    
    # Скрываем пустые axes
    for idx in range(len(features), len(axes)):
        axes[idx].set_visible(False)
    
    plt.suptitle('Boxplots признаков fractal[0] по классам', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

plot_boxplots_by_class(fractal_0_df, analysis_features, f'{PLOTS_DIR}boxplots_by_class.png')
print(f"✅ Boxplots сохранены в {PLOTS_DIR}boxplots_by_class.png")
```


    
![png](EDA_files/EDA_10_0.png)
    


    ✅ Boxplots сохранены в plots/boxplots_by_class.png
    

## 3. Статистические тесты на различия между классами


```python
def check_normality(values, alpha=0.05):
    """
    Проверка нормальности распределения.
    Использует тест Шапиро-Уилка для малых выборок (<5000)
    и D'Agostino-Pearson для больших.
    
    Returns:
        tuple: (is_normal: bool, p_value: float)
    """
    if len(values) < 3:
        return False, 0.0
    
    try:
        if len(values) < 5000:
            stat, p = shapiro(values[:min(len(values), 5000)])
        else:
            stat, p = normaltest(values)
        return p > alpha, p
    except:
        return False, 0.0


def cohens_d(group1, group2):
    """
    Вычисление размера эффекта Cohen's d.
    
    Интерпретация:
    - |d| < 0.2: незначительный эффект
    - 0.2 ≤ |d| < 0.5: малый эффект
    - 0.5 ≤ |d| < 0.8: средний эффект
    - |d| ≥ 0.8: большой эффект
    """
    n1, n2 = len(group1), len(group2)
    var1, var2 = group1.var(), group2.var()
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
    
    if pooled_std == 0:
        return 0.0
    
    return (group1.mean() - group2.mean()) / pooled_std


def interpret_cohens_d(d):
    """Интерпретация Cohen's d."""
    d_abs = abs(d)
    if d_abs < 0.2:
        return 'negligible'
    elif d_abs < 0.5:
        return 'small'
    elif d_abs < 0.8:
        return 'medium'
    else:
        return 'large'


def perform_statistical_tests(df: pd.DataFrame, features: list) -> pd.DataFrame:
    """
    Выполнение статистических тестов для сравнения классов.
    
    Сравнения:
    - Class -1 vs Class 0
    - Class 1 vs Class 0  
    - Class -1 vs Class 1
    """
    results = []
    comparisons = [(-1, 0), (1, 0), (-1, 1)]
    
    for feature in features:
        for c1, c2 in comparisons:
            g1 = df[df['signal'] == c1][feature].dropna()
            g2 = df[df['signal'] == c2][feature].dropna()
            
            if len(g1) < 3 or len(g2) < 3:
                continue
            
            # Проверка нормальности
            normal1, p_normal1 = check_normality(g1)
            normal2, p_normal2 = check_normality(g2)
            both_normal = normal1 and normal2
            
            # Выбор теста
            if both_normal:
                stat, p_value = ttest_ind(g1, g2, equal_var=False)  # Welch's t-test
                test_name = 't-test (Welch)'
            else:
                stat, p_value = mannwhitneyu(g1, g2, alternative='two-sided')
                test_name = 'Mann-Whitney U'
            
            # Effect size
            d = cohens_d(g1, g2)
            
            results.append({
                'feature': feature,
                'comparison': f'{c1} vs {c2}',
                'n_group1': len(g1),
                'n_group2': len(g2),
                'test': test_name,
                'statistic': stat,
                'p_value': p_value,
                'significant_005': p_value < 0.05,
                'significant_001': p_value < 0.01,
                'cohens_d': d,
                'effect_size': interpret_cohens_d(d),
                'mean_diff': g1.mean() - g2.mean()
            })
    
    return pd.DataFrame(results)

# Выполнение тестов
test_results = perform_statistical_tests(fractal_0_df, analysis_features)

print("=" * 120)
print("РЕЗУЛЬТАТЫ СТАТИСТИЧЕСКИХ ТЕСТОВ")
print("=" * 120)
print("\n⚠️ ВАЖНО: При малых размерах minority классов (n=240, n=257) тесты имеют низкую мощность.")
print("   Cohen's d (effect size) более информативен, чем p-value!\n")

# Форматированный вывод
display_cols = ['feature', 'comparison', 'test', 'p_value', 'significant_005', 'cohens_d', 'effect_size']
display_df = test_results[display_cols].copy()
display_df['p_value'] = display_df['p_value'].apply(lambda x: f'{x:.2e}' if x < 0.001 else f'{x:.4f}')
display_df['cohens_d'] = display_df['cohens_d'].round(3)

print(display_df.to_string(index=False))

# Сохранение результатов
test_results.to_csv(f'{PLOTS_DIR}statistical_tests.csv', index=False)
print(f"\n✅ Результаты тестов сохранены в {PLOTS_DIR}statistical_tests.csv")
```

    ========================================================================================================================
    РЕЗУЛЬТАТЫ СТАТИСТИЧЕСКИХ ТЕСТОВ
    ========================================================================================================================
    
    ⚠️ ВАЖНО: При малых размерах minority классов (n=240, n=257) тесты имеют низкую мощность.
       Cohen's d (effect size) более информативен, чем p-value!
    
      feature comparison           test  p_value  significant_005  cohens_d effect_size
        price    -1 vs 0 Mann-Whitney U 3.20e-04             True    -0.059  negligible
        price     1 vs 0 Mann-Whitney U   0.5240            False    -0.011  negligible
        price    -1 vs 1 Mann-Whitney U   0.0070             True    -0.050  negligible
    direction    -1 vs 0 Mann-Whitney U 3.85e-61             True    -1.089       large
    direction     1 vs 0 Mann-Whitney U 2.11e-46             True     0.968       large
    direction    -1 vs 1 t-test (Welch) 0.00e+00             True     0.000  negligible
        front    -1 vs 0 Mann-Whitney U 1.47e-50             True     0.042  negligible
        front     1 vs 0 Mann-Whitney U 8.32e-59             True     0.324       small
        front    -1 vs 1 Mann-Whitney U   0.0028             True    -0.318       small
         back    -1 vs 0 Mann-Whitney U 9.31e-23             True     0.488       small
         back     1 vs 0 Mann-Whitney U 1.77e-19             True     0.659      medium
         back    -1 vs 1 Mann-Whitney U   0.8598            False    -0.132  negligible
       strong    -1 vs 0 t-test (Welch)      nan            False     0.000  negligible
       strong     1 vs 0 Mann-Whitney U 1.36e-05             True     0.289       small
       strong    -1 vs 1 Mann-Whitney U   0.3026            False    -0.093  negligible
        break    -1 vs 0 t-test (Welch)      nan            False     0.000  negligible
        break     1 vs 0 t-test (Welch)      nan            False     0.000  negligible
        break    -1 vs 1 t-test (Welch)      nan            False     0.000  negligible
      reverse    -1 vs 0 Mann-Whitney U 7.78e-37             True     0.827       large
      reverse     1 vs 0 Mann-Whitney U 4.18e-31             True     0.779      medium
      reverse    -1 vs 1 Mann-Whitney U   0.4860            False     0.063  negligible
        power    -1 vs 0 Mann-Whitney U 1.73e-09             True     0.305       small
        power     1 vs 0 Mann-Whitney U 2.72e-10             True     0.404       small
        power    -1 vs 1 Mann-Whitney U   0.5819            False    -0.090  negligible
        count    -1 vs 0 Mann-Whitney U 5.55e-04             True     0.169  negligible
        count     1 vs 0 Mann-Whitney U   0.0335             True     0.094  negligible
        count    -1 vs 1 Mann-Whitney U   0.2895            False     0.080  negligible
      impulse    -1 vs 0 Mann-Whitney U 3.42e-54             True     1.181       large
      impulse     1 vs 0 Mann-Whitney U 2.00e-28             True     0.866       large
      impulse    -1 vs 1 Mann-Whitney U   0.0037             True     0.243       small
    
    ✅ Результаты тестов сохранены в plots/statistical_tests.csv
    


```python
# Визуализация p-values и effect sizes
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# Pivot для heatmap p-values
pivot_pvalue = test_results.pivot(index='feature', columns='comparison', values='p_value')

# Heatmap p-values (log scale)
log_pvalues = -np.log10(pivot_pvalue + 1e-300)  # Избегаем log(0)
sns.heatmap(log_pvalues, annot=True, fmt='.1f', cmap='RdYlGn', ax=axes[0],
            cbar_kws={'label': '-log10(p-value)'})
axes[0].set_title('P-values статистических тестов\n(выше = более значимо)', fontweight='bold')
axes[0].set_xlabel('Сравнение классов')
axes[0].set_ylabel('Признак')

# Pivot для heatmap Cohen's d
pivot_cohens = test_results.pivot(index='feature', columns='comparison', values='cohens_d')

# Heatmap Cohen's d
sns.heatmap(pivot_cohens, annot=True, fmt='.2f', cmap='RdBu_r', center=0, ax=axes[1],
            cbar_kws={'label': "Cohen's d"})
axes[1].set_title("Cohen's d (Effect Size)\n(|d|≥0.8 = large effect)", fontweight='bold')
axes[1].set_xlabel('Сравнение классов')
axes[1].set_ylabel('Признак')

plt.tight_layout()
plt.savefig(f'{PLOTS_DIR}statistical_tests_heatmap.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"✅ Heatmap сохранён в {PLOTS_DIR}statistical_tests_heatmap.png")
```


    
![png](EDA_files/EDA_13_0.png)
    


    ✅ Heatmap сохранён в plots/statistical_tests_heatmap.png
    


```python
# Анализ наиболее значимых различий
print("\n" + "=" * 80)
print("НАИБОЛЕЕ ЗНАЧИМЫЕ РАЗЛИЧИЯ (|Cohen's d| ≥ 0.5)")
print("=" * 80)

significant_effects = test_results[test_results['cohens_d'].abs() >= 0.5].sort_values('cohens_d', key=abs, ascending=False)

if len(significant_effects) > 0:
    for _, row in significant_effects.iterrows():
        print(f"\n📌 {row['feature']} ({row['comparison']})")
        print(f"   Cohen's d = {row['cohens_d']:.3f} ({row['effect_size']} effect)")
        print(f"   p-value = {row['p_value']:.2e}")
        print(f"   Mean difference = {row['mean_diff']:.4f}")
else:
    print("\nНе найдено признаков со средним или большим размером эффекта.")
```

    
    ================================================================================
    НАИБОЛЕЕ ЗНАЧИМЫЕ РАЗЛИЧИЯ (|Cohen's d| ≥ 0.5)
    ================================================================================
    
    📌 impulse (-1 vs 0)
       Cohen's d = 1.181 (large effect)
       p-value = 3.42e-54
       Mean difference = 1.4635
    
    📌 direction (-1 vs 0)
       Cohen's d = -1.089 (large effect)
       p-value = 3.85e-61
       Mean difference = -1.0579
    
    📌 direction (1 vs 0)
       Cohen's d = 0.968 (large effect)
       p-value = 2.11e-46
       Mean difference = 0.9421
    
    📌 impulse (1 vs 0)
       Cohen's d = 0.866 (large effect)
       p-value = 2.00e-28
       Mean difference = 1.0718
    
    📌 reverse (-1 vs 0)
       Cohen's d = 0.827 (large effect)
       p-value = 7.78e-37
       Mean difference = 0.4060
    
    📌 reverse (1 vs 0)
       Cohen's d = 0.779 (medium effect)
       p-value = 4.18e-31
       Mean difference = 0.3836
    
    📌 back (1 vs 0)
       Cohen's d = 0.659 (medium effect)
       p-value = 1.77e-19
       Mean difference = 0.0098
    

## 4. Корреляционный анализ


```python
# Корреляционные матрицы для каждого класса
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

corr_features = [f for f in analysis_features if f not in ['strong', 'break']]  # Исключаем константные

for idx, signal in enumerate([-1, 0, 1]):
    class_data = fractal_0_df[fractal_0_df['signal'] == signal][corr_features]
    corr_matrix = class_data.corr()
    
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r', 
                center=0, ax=axes[idx], square=True, linewidths=0.5,
                cbar_kws={'shrink': 0.8})
    axes[idx].set_title(f'{CLASS_NAMES[signal]}\n(n={len(class_data)})', fontweight='bold')

plt.suptitle('Корреляционные матрицы признаков fractal[0] по классам', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(f'{PLOTS_DIR}correlation_matrices_by_class.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"✅ Корреляционные матрицы сохранены в {PLOTS_DIR}correlation_matrices_by_class.png")
```


    
![png](EDA_files/EDA_16_0.png)
    


    ✅ Корреляционные матрицы сохранены в plots/correlation_matrices_by_class.png
    


```python
# Корреляция признаков между соседними фракталами
def parse_multiple_fractals(df: pd.DataFrame, fractal_cols: list, max_fractals: int = 10) -> dict:
    """
    Парсинг нескольких фракталов для анализа корреляций между ними.
    """
    fractals_data = {i: [] for i in range(max_fractals)}
    
    for idx, row in df.iterrows():
        for f_idx in range(min(max_fractals, len(fractal_cols))):
            parsed = parse_fractal_string(row[fractal_cols[f_idx]])
            if parsed:
                parsed['row_idx'] = idx
                parsed['signal'] = row['signal']
                fractals_data[f_idx].append(parsed)
    
    return {i: pd.DataFrame(data) for i, data in fractals_data.items()}

print("Парсинг первых 5 фракталов для анализа корреляций...")
fractals_dict = parse_multiple_fractals(raw_df, fractal_cols, max_fractals=5)

# Корреляция между fractal[0] и fractal[1] для каждого признака
cross_fractal_corr = []
for feature in analysis_features:
    if feature in ['strong', 'break']:  # Пропускаем константные
        continue
    for i in range(4):
        if i not in fractals_dict or (i+1) not in fractals_dict:
            continue
        
        f1 = fractals_dict[i][feature]
        f2 = fractals_dict[i+1][feature]
        
        # Выравниваем по длине
        min_len = min(len(f1), len(f2))
        corr = np.corrcoef(f1[:min_len], f2[:min_len])[0, 1]
        
        cross_fractal_corr.append({
            'feature': feature,
            'fractal_pair': f'f[{i}] vs f[{i+1}]',
            'correlation': corr
        })

cross_corr_df = pd.DataFrame(cross_fractal_corr)

# Визуализация
fig, ax = plt.subplots(figsize=(12, 6))

pivot_cross = cross_corr_df.pivot(index='feature', columns='fractal_pair', values='correlation')
sns.heatmap(pivot_cross, annot=True, fmt='.2f', cmap='RdBu_r', center=0, ax=ax,
            linewidths=0.5, cbar_kws={'label': 'Корреляция Пирсона'})
ax.set_title('Автокорреляция признаков между соседними фракталами', fontweight='bold')
ax.set_xlabel('Пара фракталов')
ax.set_ylabel('Признак')

plt.tight_layout()
plt.savefig(f'{PLOTS_DIR}cross_fractal_correlation.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"✅ Кросс-фрактальные корреляции сохранены в {PLOTS_DIR}cross_fractal_correlation.png")
```

    Парсинг первых 5 фракталов для анализа корреляций...
    


    
![png](EDA_files/EDA_17_1.png)
    


    ✅ Кросс-фрактальные корреляции сохранены в plots/cross_fractal_correlation.png
    

## 5. Временной анализ


```python
# Конвертация временных меток
fractal_0_df['datetime'] = pd.to_datetime(fractal_0_df['fractal_time'], unit='s')
fractal_0_df['hour'] = fractal_0_df['datetime'].dt.hour
fractal_0_df['day_of_week'] = fractal_0_df['datetime'].dt.dayofweek
fractal_0_df['date'] = fractal_0_df['datetime'].dt.date

print("Временной диапазон данных:")
print(f"  От: {fractal_0_df['datetime'].min()}")
print(f"  До: {fractal_0_df['datetime'].max()}")
print(f"  Длительность: {(fractal_0_df['datetime'].max() - fractal_0_df['datetime'].min()).days} дней")
```

    Временной диапазон данных:
      От: 2023-07-28 20:00:00
      До: 2025-06-11 20:00:00
      Длительность: 684 дней
    


```python
# График появления сигналов во времени
fig, axes = plt.subplots(2, 1, figsize=(16, 10))

# Все сигналы
for signal in [-1, 0, 1]:
    signal_data = fractal_0_df[fractal_0_df['signal'] == signal]
    axes[0].scatter(signal_data['datetime'], [signal]*len(signal_data), 
                    alpha=0.5, s=10, c=CLASS_COLORS[signal], label=CLASS_NAMES[signal])

axes[0].set_title('Распределение сигналов во времени', fontweight='bold')
axes[0].set_xlabel('Время')
axes[0].set_ylabel('Класс сигнала')
axes[0].legend()
axes[0].set_yticks([-1, 0, 1])
axes[0].grid(True, alpha=0.3)

# Только non-zero сигналы (кумулятивный график)
nonzero_signals = fractal_0_df[fractal_0_df['signal'] != 0].sort_values('datetime')

# Кумулятивный подсчёт
nonzero_signals['cumcount_sell'] = (nonzero_signals['signal'] == -1).cumsum()
nonzero_signals['cumcount_buy'] = (nonzero_signals['signal'] == 1).cumsum()

axes[1].plot(nonzero_signals['datetime'], nonzero_signals['cumcount_sell'], 
             color=CLASS_COLORS[-1], label='Sell (-1)', linewidth=2)
axes[1].plot(nonzero_signals['datetime'], nonzero_signals['cumcount_buy'], 
             color=CLASS_COLORS[1], label='Buy (1)', linewidth=2)
axes[1].set_title('Кумулятивное появление сигналов (signal ≠ 0)', fontweight='bold')
axes[1].set_xlabel('Время')
axes[1].set_ylabel('Кумулятивное количество')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{PLOTS_DIR}signals_over_time.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"✅ Временные графики сохранены в {PLOTS_DIR}signals_over_time.png")
```


    
![png](EDA_files/EDA_20_0.png)
    


    ✅ Временные графики сохранены в plots/signals_over_time.png
    


```python
# Анализ сезонности: по часам дня и дням недели
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

day_names_full = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

# 1. Распределение по часам (все сигналы)
hour_counts = fractal_0_df.groupby(['hour', 'signal']).size().unstack(fill_value=0)
hour_counts[[c for c in [-1, 0, 1] if c in hour_counts.columns]].plot(
    kind='bar', ax=axes[0, 0], color=[CLASS_COLORS[c] for c in hour_counts.columns], 
    width=0.8, edgecolor='black', linewidth=0.5)
axes[0, 0].set_title('Распределение по часам дня (все классы)', fontweight='bold')
axes[0, 0].set_xlabel('Час')
axes[0, 0].set_ylabel('Количество')
axes[0, 0].tick_params(axis='x', rotation=0)
axes[0, 0].legend([CLASS_NAMES[c] for c in hour_counts.columns])

# 2. Распределение по часам (только non-zero)
nonzero_df = fractal_0_df[fractal_0_df['signal'] != 0]
hour_nonzero = nonzero_df.groupby(['hour', 'signal']).size().unstack(fill_value=0)
hour_nonzero.plot(kind='bar', ax=axes[0, 1], 
                  color=[CLASS_COLORS[c] for c in hour_nonzero.columns], 
                  width=0.8, edgecolor='black', linewidth=0.5)
axes[0, 1].set_title('Распределение по часам дня (signal ≠ 0)', fontweight='bold')
axes[0, 1].set_xlabel('Час')
axes[0, 1].set_ylabel('Количество')
axes[0, 1].tick_params(axis='x', rotation=0)
axes[0, 1].legend([CLASS_NAMES[c] for c in hour_nonzero.columns])

# 3. Распределение по дням недели (все сигналы)
dow_counts = fractal_0_df.groupby(['day_of_week', 'signal']).size().unstack(fill_value=0)
dow_counts.plot(kind='bar', ax=axes[1, 0], 
                color=[CLASS_COLORS[c] for c in dow_counts.columns], 
                width=0.8, edgecolor='black', linewidth=0.5)
axes[1, 0].set_title('Распределение по дням недели (все классы)', fontweight='bold')
axes[1, 0].set_xlabel('День недели')
axes[1, 0].set_ylabel('Количество')
# ИСПРАВЛЕНИЕ: используем только те дни, которые есть в данных
unique_days = sorted(dow_counts.index)
day_names = [day_names_full[d] for d in unique_days]
axes[1, 0].set_xticklabels(day_names)
axes[1, 0].tick_params(axis='x', rotation=0)
axes[1, 0].legend([CLASS_NAMES[c] for c in dow_counts.columns])

# 4. Распределение по дням недели (только non-zero)
dow_nonzero = nonzero_df.groupby(['day_of_week', 'signal']).size().unstack(fill_value=0)
dow_nonzero.plot(kind='bar', ax=axes[1, 1], 
                 color=[CLASS_COLORS[c] for c in dow_nonzero.columns], 
                 width=0.8, edgecolor='black', linewidth=0.5)
axes[1, 1].set_title('Распределение по дням недели (signal ≠ 0)', fontweight='bold')
axes[1, 1].set_xlabel('День недели')
axes[1, 1].set_ylabel('Количество')
# ИСПРАВЛЕНИЕ: используем только те дни, которые есть в данных
unique_days_nonzero = sorted(dow_nonzero.index)
day_names_nonzero = [day_names_full[d] for d in unique_days_nonzero]
axes[1, 1].set_xticklabels(day_names_nonzero)
axes[1, 1].tick_params(axis='x', rotation=0)
axes[1, 1].legend([CLASS_NAMES[c] for c in dow_nonzero.columns])

plt.tight_layout()
plt.savefig(f'{PLOTS_DIR}seasonality_analysis.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"✅ Анализ сезонности сохранён в {PLOTS_DIR}seasonality_analysis.png")
```


    
![png](EDA_files/EDA_21_0.png)
    


    ✅ Анализ сезонности сохранён в plots/seasonality_analysis.png
    


```python
# Проверка кластеризации событий (межсобытийные интервалы)
print("\n" + "=" * 80)
print("АНАЛИЗ КЛАСТЕРИЗАЦИИ СОБЫТИЙ (signal ≠ 0)")
print("=" * 80)

nonzero_sorted = fractal_0_df[fractal_0_df['signal'] != 0].sort_values('fractal_time')
time_diffs = nonzero_sorted['fractal_time'].diff().dropna()
time_diffs_hours = time_diffs / 3600  # Конвертация в часы

print(f"\nСтатистика межсобытийных интервалов:")
print(f"  Всего событий: {len(nonzero_sorted)}")
print(f"  Среднее время между событиями: {time_diffs_hours.mean():.1f} часов")
print(f"  Медиана: {time_diffs_hours.median():.1f} часов")
print(f"  Std: {time_diffs_hours.std():.1f} часов")
print(f"  Min: {time_diffs_hours.min():.1f} часов")
print(f"  Max: {time_diffs_hours.max():.1f} часов")

# Визуализация
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Гистограмма межсобытийных интервалов
axes[0].hist(time_diffs_hours, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
axes[0].axvline(time_diffs_hours.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {time_diffs_hours.mean():.1f}h')
axes[0].axvline(time_diffs_hours.median(), color='orange', linestyle='--', linewidth=2, label=f'Median: {time_diffs_hours.median():.1f}h')
axes[0].set_title('Распределение межсобытийных интервалов', fontweight='bold')
axes[0].set_xlabel('Время между событиями (часы)')
axes[0].set_ylabel('Частота')
axes[0].legend()

# Проверка на кластеризацию: соотношение variance/mean
# Для Пуассоновского процесса = 1, >1 указывает на кластеризацию
dispersion_index = time_diffs_hours.var() / time_diffs_hours.mean()
print(f"\n📊 Индекс дисперсии (variance/mean): {dispersion_index:.2f}")
print(f"   (>1 указывает на кластеризацию событий)")

# Log-log график для проверки power-law
axes[1].hist(time_diffs_hours, bins=50, cumulative=-1, density=True, 
             color='steelblue', edgecolor='black', alpha=0.7)
axes[1].set_yscale('log')
axes[1].set_title('Кумулятивное распределение (survival function)', fontweight='bold')
axes[1].set_xlabel('Время между событиями (часы)')
axes[1].set_ylabel('P(T > t)')

plt.tight_layout()
plt.savefig(f'{PLOTS_DIR}event_clustering.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"\n✅ Анализ кластеризации сохранён в {PLOTS_DIR}event_clustering.png")
```

    
    ================================================================================
    АНАЛИЗ КЛАСТЕРИЗАЦИИ СОБЫТИЙ (signal ≠ 0)
    ================================================================================
    
    Статистика межсобытийных интервалов:
      Всего событий: 497
      Среднее время между событиями: 32.9 часов
      Медиана: 20.0 часов
      Std: 35.0 часов
      Min: 0.0 часов
      Max: 211.0 часов
    
    📊 Индекс дисперсии (variance/mean): 37.27
       (>1 указывает на кластеризацию событий)
    


    
![png](EDA_files/EDA_22_1.png)
    


    
    ✅ Анализ кластеризации сохранён в plots/event_clustering.png
    

## 6. Анализ выбросов


```python
def analyze_outliers(df: pd.DataFrame, features: list) -> pd.DataFrame:
    """
    Анализ выбросов с использованием IQR и квантильного методов.
    
    Returns:
        DataFrame с информацией о выбросах для каждого признака
    """
    outlier_stats = []
    
    for feature in features:
        values = df[feature].dropna()
        
        # IQR метод
        q1, q3 = values.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        iqr_outliers_low = (values < lower_bound).sum()
        iqr_outliers_high = (values > upper_bound).sum()
        
        # Квантильный метод (1%, 99%)
        p01, p99 = values.quantile([0.01, 0.99])
        quantile_outliers_low = (values < p01).sum()
        quantile_outliers_high = (values > p99).sum()
        
        outlier_stats.append({
            'feature': feature,
            'total_values': len(values),
            'q1': q1,
            'q3': q3,
            'iqr': iqr,
            'iqr_lower_bound': lower_bound,
            'iqr_upper_bound': upper_bound,
            'iqr_outliers_low': iqr_outliers_low,
            'iqr_outliers_high': iqr_outliers_high,
            'iqr_outliers_pct': (iqr_outliers_low + iqr_outliers_high) / len(values) * 100,
            'p01': p01,
            'p99': p99,
            'quantile_outliers_low': quantile_outliers_low,
            'quantile_outliers_high': quantile_outliers_high
        })
    
    return pd.DataFrame(outlier_stats)

# Анализ выбросов
outlier_df = analyze_outliers(fractal_0_df, analysis_features)

print("=" * 100)
print("АНАЛИЗ ВЫБРОСОВ (IQR МЕТОД)")
print("=" * 100)

display_cols = ['feature', 'iqr_lower_bound', 'iqr_upper_bound', 
                'iqr_outliers_low', 'iqr_outliers_high', 'iqr_outliers_pct']
print(outlier_df[display_cols].round(4).to_string(index=False))

print("\n" + "=" * 100)
print("КВАНТИЛЬНЫЙ АНАЛИЗ (1%, 99%)")
print("=" * 100)

quantile_cols = ['feature', 'p01', 'p99', 'quantile_outliers_low', 'quantile_outliers_high']
print(outlier_df[quantile_cols].round(4).to_string(index=False))

# Сохранение
outlier_df.to_csv(f'{PLOTS_DIR}outlier_analysis.csv', index=False)
print(f"\n✅ Анализ выбросов сохранён в {PLOTS_DIR}outlier_analysis.csv")
```

    ====================================================================================================
    АНАЛИЗ ВЫБРОСОВ (IQR МЕТОД)
    ====================================================================================================
      feature  iqr_lower_bound  iqr_upper_bound  iqr_outliers_low  iqr_outliers_high  iqr_outliers_pct
        price           0.4508           1.2559               502                  0            9.9564
    direction          -4.0000           4.0000                 0                  0            0.0000
        front          -0.0379           0.0800                 0                600           11.9000
         back          -0.0124           0.0292                 0                388            7.6954
       strong           0.0000           0.0000                 0                  1            0.0198
        break           0.0000           0.0000                 0                  0            0.0000
      reverse          -1.5000           2.5000                 0                  0            0.0000
        power          -0.3551           0.6313                 0                288            5.7120
        count          -1.0000           7.0000                 0                 71            1.4082
      impulse          -0.4500           5.5500                 0                207            4.1055
    
    ====================================================================================================
    КВАНТИЛЬНЫЙ АНАЛИЗ (1%, 99%)
    ====================================================================================================
      feature     p01    p99  quantile_outliers_low  quantile_outliers_high
        price  0.0198 1.0000                     51                       0
    direction -1.0000 1.0000                      0                       0
        front  0.0000 1.0000                      0                       0
         back  0.0000 0.0781                      0                      51
       strong  0.0000 0.0000                      0                       1
        break  0.0000 0.0000                      0                       0
      reverse  0.0000 1.0000                      0                       0
        power  0.0000 1.0000                      0                       0
        count  1.0000 8.0000                      0                      25
      impulse  0.9000 7.2000                     32                      48
    
    ✅ Анализ выбросов сохранён в plots/outlier_analysis.csv
    


```python
# Визуализация выбросов
fig, axes = plt.subplots(2, 5, figsize=(20, 10))
axes = axes.flatten()

for idx, feature in enumerate(analysis_features):
    ax = axes[idx]
    values = fractal_0_df[feature].dropna()
    
    # Boxplot с выделением выбросов
    bp = ax.boxplot(values, vert=True, patch_artist=True,
                    flierprops={'marker': 'o', 'markerfacecolor': 'red', 'markersize': 4, 'alpha': 0.5})
    bp['boxes'][0].set_facecolor('steelblue')
    bp['boxes'][0].set_alpha(0.7)
    
    # Добавляем 1% и 99% квантили
    p01, p99 = values.quantile([0.01, 0.99])
    ax.axhline(p01, color='orange', linestyle='--', linewidth=1, alpha=0.8, label='1%')
    ax.axhline(p99, color='orange', linestyle='--', linewidth=1, alpha=0.8, label='99%')
    
    ax.set_title(feature, fontweight='bold')
    ax.set_ylabel('Значение')
    ax.grid(True, alpha=0.3, axis='y')

# Скрываем лишний subplot
if len(analysis_features) < len(axes):
    axes[-1].set_visible(False)

plt.suptitle('Boxplots с выбросами (красные точки) и квантилями 1%/99% (оранжевые линии)', 
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(f'{PLOTS_DIR}outliers_boxplots.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"✅ Boxplots выбросов сохранены в {PLOTS_DIR}outliers_boxplots.png")
```


    
![png](EDA_files/EDA_25_0.png)
    


    ✅ Boxplots выбросов сохранены в plots/outliers_boxplots.png
    

## 7. Dimension Reduction (t-SNE)


```python
# Подготовка данных для t-SNE
# Исключаем fractal_time и константные признаки
tsne_features = [f for f in FEATURE_NAMES if f not in ['fractal_time', 'strong', 'break']]

print(f"Признаки для t-SNE: {tsne_features}")

# Подготовка матрицы признаков
X = fractal_0_df[tsne_features].values
y = fractal_0_df['signal'].values

print(f"Размерность X: {X.shape}")
print(f"Классы в y: {np.unique(y)}")

# Стандартизация
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print("\nДанные стандартизированы.")
```

    Признаки для t-SNE: ['price', 'direction', 'front', 'back', 'reverse', 'power', 'count', 'impulse']
    Размерность X: (5042, 8)
    Классы в y: [-1  0  1]
    
    Данные стандартизированы.
    


```python
# t-SNE проекция
print("Выполнение t-SNE... (может занять несколько минут)")

tsne = TSNE(n_components=2, perplexity=30, max_iter=1000, random_state=42, 
            learning_rate='auto', init='pca')
X_tsne = tsne.fit_transform(X_scaled)

print(f"t-SNE завершён. Размерность результата: {X_tsne.shape}")
```

    Выполнение t-SNE... (может занять несколько минут)
    t-SNE завершён. Размерность результата: (5042, 2)
    


```python
# Визуализация t-SNE
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# 1. Все классы вместе
for signal in [-1, 0, 1]:
    mask = y == signal
    axes[0].scatter(X_tsne[mask, 0], X_tsne[mask, 1], 
                    c=CLASS_COLORS[signal], label=CLASS_NAMES[signal],
                    alpha=0.6 if signal == 0 else 0.9,
                    s=20 if signal == 0 else 60,
                    edgecolors='black' if signal != 0 else 'none',
                    linewidths=0.5)

axes[0].set_title('t-SNE проекция признаков fractal[0]\n(minority классы выделены)', fontweight='bold')
axes[0].set_xlabel('t-SNE компонента 1')
axes[0].set_ylabel('t-SNE компонента 2')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# 2. Только minority классы на фоне контура majority
# Контур density для класса 0
mask_0 = y == 0
from scipy.stats import gaussian_kde
try:
    xy_0 = np.vstack([X_tsne[mask_0, 0], X_tsne[mask_0, 1]])
    kde = gaussian_kde(xy_0)
    
    # Создаём сетку
    xmin, xmax = X_tsne[:, 0].min() - 5, X_tsne[:, 0].max() + 5
    ymin, ymax = X_tsne[:, 1].min() - 5, X_tsne[:, 1].max() + 5
    xx, yy = np.meshgrid(np.linspace(xmin, xmax, 100), np.linspace(ymin, ymax, 100))
    zz = kde(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
    
    axes[1].contour(xx, yy, zz, levels=5, colors='lightgray', alpha=0.5)
    axes[1].contourf(xx, yy, zz, levels=5, cmap='Blues', alpha=0.2)
except:
    # Fallback если KDE не работает
    axes[1].scatter(X_tsne[mask_0, 0], X_tsne[mask_0, 1], 
                    c='lightgray', alpha=0.1, s=5)

# Minority классы
for signal in [-1, 1]:
    mask = y == signal
    axes[1].scatter(X_tsne[mask, 0], X_tsne[mask, 1], 
                    c=CLASS_COLORS[signal], label=CLASS_NAMES[signal],
                    alpha=0.9, s=80, edgecolors='black', linewidths=1)

axes[1].set_title('Minority классы на фоне density majority класса', fontweight='bold')
axes[1].set_xlabel('t-SNE компонента 1')
axes[1].set_ylabel('t-SNE компонента 2')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{PLOTS_DIR}tsne_projection.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"✅ t-SNE проекция сохранена в {PLOTS_DIR}tsne_projection.png")
```


    
![png](EDA_files/EDA_29_0.png)
    


    ✅ t-SNE проекция сохранена в plots/tsne_projection.png
    


```python
# Анализ разделимости классов
print("\n" + "=" * 80)
print("АНАЛИЗ РАЗДЕЛИМОСТИ КЛАССОВ В t-SNE ПРОСТРАНСТВЕ")
print("=" * 80)

# Вычисление центроидов
centroids = {}
for signal in [-1, 0, 1]:
    mask = y == signal
    centroids[signal] = X_tsne[mask].mean(axis=0)
    print(f"\nЦентроид класса {CLASS_NAMES[signal]}: ({centroids[signal][0]:.2f}, {centroids[signal][1]:.2f})")

# Расстояния между центроидами
print("\nРасстояния между центроидами:")
for c1 in [-1, 0, 1]:
    for c2 in [-1, 0, 1]:
        if c1 < c2:
            dist = np.linalg.norm(centroids[c1] - centroids[c2])
            print(f"  {CLASS_NAMES[c1]} <-> {CLASS_NAMES[c2]}: {dist:.2f}")

# Intra-class variance
print("\nВнутриклассовая дисперсия:")
for signal in [-1, 0, 1]:
    mask = y == signal
    variance = X_tsne[mask].var()
    print(f"  {CLASS_NAMES[signal]}: {variance:.2f}")
```

    
    ================================================================================
    АНАЛИЗ РАЗДЕЛИМОСТИ КЛАССОВ В t-SNE ПРОСТРАНСТВЕ
    ================================================================================
    
    Центроид класса Sell (-1): (5.78, 36.63)
    
    Центроид класса Neutral (0): (-1.81, -1.20)
    
    Центроид класса Buy (1): (31.03, -10.77)
    
    Расстояния между центроидами:
      Sell (-1) <-> Neutral (0): 38.58
      Sell (-1) <-> Buy (1): 53.71
      Neutral (0) <-> Buy (1): 34.21
    
    Внутриклассовая дисперсия:
      Sell (-1): 596.03
      Neutral (0): 1305.17
      Buy (1): 843.60
    

## 8. Выводы и рекомендации


```python
print("="*100)
print("ИТОГОВЫЕ ВЫВОДЫ EDA")
print("="*100)

print("""
1. ДИСБАЛАНС КЛАССОВ
   - Экстремальный дисбаланс: класс 0 составляет ~90% данных
   - Minority классы: -1 (257 образцов, 5.1%), +1 (240 образцов, 4.8%)
   - Требуется специальная обработка: oversampling, undersampling, или class weights

2. КЛЮЧЕВЫЕ ПРИЗНАКИ (по Cohen's d):
   - direction: полностью разделяет классы -1 и +1 (d → ∞)
   - impulse: различается между классами (выше для minority)
   - reverse: различается между классами
   - count: minority классы имеют отличные распределения

3. КОНСТАНТНЫЕ ПРИЗНАКИ:
   - strong и break: почти всегда 0 в fractal[0]
   - Рекомендуется проверить их в других фракталах

4. ВРЕМЕННЫЕ ПАТТЕРНЫ:
   - Проверить сезонность по часам и дням недели
   - Анализировать кластеризацию событий

5. t-SNE ВИЗУАЛИЗАЦИЯ:
   - Оценить визуальную разделимость классов
   - Minority классы могут образовывать кластеры

6. РЕКОМЕНДАЦИИ ДЛЯ МОДЕЛИРОВАНИЯ:
   - Использовать стратифицированное разбиение train/test
   - Применять SMOTE или другие техники балансировки
   - Рассмотреть ансамблевые методы (XGBoost, LightGBM)
   - Использовать F1-score или AUC-PR как метрику (не accuracy!)
   - Рассмотреть использование временных признаков
""")

print(f"\n✅ Все графики сохранены в папку: {PLOTS_DIR}")
print("✅ EDA завершён!")
```

    ====================================================================================================
    ИТОГОВЫЕ ВЫВОДЫ EDA
    ====================================================================================================
    
    1. ДИСБАЛАНС КЛАССОВ
       - Экстремальный дисбаланс: класс 0 составляет ~90% данных
       - Minority классы: -1 (257 образцов, 5.1%), +1 (240 образцов, 4.8%)
       - Требуется специальная обработка: oversampling, undersampling, или class weights
    
    2. КЛЮЧЕВЫЕ ПРИЗНАКИ (по Cohen's d):
       - direction: полностью разделяет классы -1 и +1 (d → ∞)
       - impulse: различается между классами (выше для minority)
       - reverse: различается между классами
       - count: minority классы имеют отличные распределения
    
    3. КОНСТАНТНЫЕ ПРИЗНАКИ:
       - strong и break: почти всегда 0 в fractal[0]
       - Рекомендуется проверить их в других фракталах
    
    4. ВРЕМЕННЫЕ ПАТТЕРНЫ:
       - Проверить сезонность по часам и дням недели
       - Анализировать кластеризацию событий
    
    5. t-SNE ВИЗУАЛИЗАЦИЯ:
       - Оценить визуальную разделимость классов
       - Minority классы могут образовывать кластеры
    
    6. РЕКОМЕНДАЦИИ ДЛЯ МОДЕЛИРОВАНИЯ:
       - Использовать стратифицированное разбиение train/test
       - Применять SMOTE или другие техники балансировки
       - Рассмотреть ансамблевые методы (XGBoost, LightGBM)
       - Использовать F1-score или AUC-PR как метрику (не accuracy!)
       - Рассмотреть использование временных признаков
    
    
    ✅ Все графики сохранены в папку: plots/
    ✅ EDA завершён!
    


```python
# Сохранение ключевых данных для дальнейшего анализа
fractal_0_df.to_csv(f'{PLOTS_DIR}fractal_0_parsed.csv', index=False)
print(f"✅ Распарсенные данные fractal[0] сохранены в {PLOTS_DIR}fractal_0_parsed.csv")

# Сохранение t-SNE координат
tsne_df = pd.DataFrame({
    'tsne_1': X_tsne[:, 0],
    'tsne_2': X_tsne[:, 1],
    'signal': y
})
tsne_df.to_csv(f'{PLOTS_DIR}tsne_coordinates.csv', index=False)
print(f"✅ t-SNE координаты сохранены в {PLOTS_DIR}tsne_coordinates.csv")
```

    ✅ Распарсенные данные fractal[0] сохранены в plots/fractal_0_parsed.csv
    ✅ t-SNE координаты сохранены в plots/tsne_coordinates.csv
    

## 9. Анализ полной последовательности фракталов (99 фракталов)

**Цель:** Комплексное исследование временных паттернов в полной последовательности фракталов и подготовка признаков для моделирования.

**Содержание:**
- 9.1 Парсинг и валидация полной последовательности
- 9.2 Статистика последовательности по классам
- 9.3 Feature Engineering из последовательности
- 9.4 Визуализация паттернов последовательности
- 9.5 Корреляционный анализ engineered features
- 9.6 Экспорт результатов

### 9.1 Парсинг и валидация полной последовательности


```python
def parse_full_sequence(df: pd.DataFrame, fractal_cols: list, max_fractals: int = 99) -> tuple:
    """
    Парсинг полной последовательности фракталов в 3D тензор.
    
    Args:
        df: исходный DataFrame с данными
        fractal_cols: список колонок с фракталами
        max_fractals: максимальное количество фракталов для парсинга
        
    Returns:
        X: np.array shape (n_samples, max_fractals, 11 features)
        y: np.array shape (n_samples,) — signal
        valid_mask: boolean mask для строк без ошибок парсинга
        parse_stats: dict со статистикой парсинга
    """
    n_samples = len(df)
    n_features = 11  # fractal_time, price, direction, front, back, strong, break, reverse, power, count, impulse
    
    # Инициализация тензора с NaN для отслеживания пропусков
    X = np.full((n_samples, max_fractals, n_features), np.nan)
    y = df['signal'].values.copy()
    valid_mask = np.ones(n_samples, dtype=bool)
    
    # Статистика парсинга
    parse_errors_per_position = np.zeros(max_fractals, dtype=int)
    parse_errors_per_row = np.zeros(n_samples, dtype=int)
    
    print(f"Парсинг {max_fractals} фракталов для {n_samples} строк...")
    
    for row_idx, row in df.iterrows():
        for f_idx in range(min(max_fractals, len(fractal_cols))):
            parsed = parse_fractal_string(row[fractal_cols[f_idx]])
            if parsed:
                X[row_idx, f_idx, 0] = parsed['fractal_time']
                X[row_idx, f_idx, 1] = parsed['price']
                X[row_idx, f_idx, 2] = parsed['direction']
                X[row_idx, f_idx, 3] = parsed['front']
                X[row_idx, f_idx, 4] = parsed['back']
                X[row_idx, f_idx, 5] = parsed['strong']
                X[row_idx, f_idx, 6] = parsed['break']
                X[row_idx, f_idx, 7] = parsed['reverse']
                X[row_idx, f_idx, 8] = parsed['power']
                X[row_idx, f_idx, 9] = parsed['count']
                X[row_idx, f_idx, 10] = parsed['impulse']
            else:
                parse_errors_per_position[f_idx] += 1
                parse_errors_per_row[row_idx] += 1
    
    # Строки с ошибками парсинга
    valid_mask = parse_errors_per_row == 0
    
    parse_stats = {
        'total_rows': n_samples,
        'valid_rows': valid_mask.sum(),
        'invalid_rows': (~valid_mask).sum(),
        'parse_rate': valid_mask.sum() / n_samples * 100,
        'errors_per_position': parse_errors_per_position,
        'errors_per_row': parse_errors_per_row
    }
    
    print(f"✅ Успешно распарсено: {parse_stats['valid_rows']} строк ({parse_stats['parse_rate']:.2f}%)")
    print(f"❌ Ошибки парсинга: {parse_stats['invalid_rows']} строк")
    
    return X, y, valid_mask, parse_stats

# Парсинг полной последовательности
X_full, y_full, valid_mask, parse_stats = parse_full_sequence(raw_df, fractal_cols, max_fractals=99)

print(f"\nРазмерность тензора X: {X_full.shape}")
print(f"Размерность вектора y: {y_full.shape}")
```

    Парсинг 99 фракталов для 5042 строк...
    ✅ Успешно распарсено: 5042 строк (100.00%)
    ❌ Ошибки парсинга: 0 строк
    
    Размерность тензора X: (5042, 99, 11)
    Размерность вектора y: (5042,)
    


```python
# Data Quality проверки

# 1. Проверка missing values по позициям
missing_per_position = np.isnan(X_full[:, :, 0]).sum(axis=0)  # Проверяем по fractal_time
missing_rate_per_position = missing_per_position / len(X_full) * 100

print("=" * 60)
print("DATA QUALITY REPORT")
print("=" * 60)

print(f"\n1. MISSING VALUES по позициям фракталов:")
print(f"   Позиции с пропусками: {(missing_rate_per_position > 0).sum()}")
if missing_rate_per_position.max() > 0:
    print(f"   Максимальный % пропусков: {missing_rate_per_position.max():.2f}% на позиции {missing_rate_per_position.argmax()}")
else:
    print(f"   ✅ Пропусков не обнаружено!")

# 2. Heatmap: (row_index × fractal_position) → missing_rate
missing_matrix = np.isnan(X_full[:, :, 0]).astype(float)

fig, axes = plt.subplots(1, 2, figsize=(16, 5))

# Общий график missing values по позициям
ax1 = axes[0]
ax1.bar(range(99), missing_rate_per_position, color='#e74c3c', alpha=0.7)
ax1.set_xlabel('Позиция фрактала')
ax1.set_ylabel('% пропущенных значений')
ax1.set_title('Missing Values по позициям фракталов')
ax1.axhline(y=1, color='r', linestyle='--', alpha=0.5, label='1% threshold')
ax1.legend()

# Heatmap для первых 100 строк (если есть пропуски)
ax2 = axes[1]
if missing_matrix.sum() > 0:
    # Показываем только строки с пропусками
    rows_with_missing = np.where(missing_matrix.sum(axis=1) > 0)[0]
    if len(rows_with_missing) > 0:
        sample_size = min(100, len(rows_with_missing))
        sample_rows = rows_with_missing[:sample_size]
        im = ax2.imshow(missing_matrix[sample_rows], aspect='auto', cmap='Reds')
        ax2.set_xlabel('Позиция фрактала')
        ax2.set_ylabel('Индекс строки (с пропусками)')
        ax2.set_title(f'Heatmap пропусков (первые {sample_size} строк с пропусками)')
        plt.colorbar(im, ax=ax2, label='Missing (1) / Present (0)')
    else:
        ax2.text(0.5, 0.5, 'Нет пропусков для отображения', ha='center', va='center', fontsize=14)
        ax2.set_title('Heatmap пропусков')
else:
    ax2.text(0.5, 0.5, '✅ Нет пропусков в данных', ha='center', va='center', fontsize=14, color='green')
    ax2.set_title('Heatmap пропусков')

plt.tight_layout()
plt.savefig(f'{PLOTS_DIR}sequence_missing_values.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"\n✅ График сохранён: {PLOTS_DIR}sequence_missing_values.png")
```

    ============================================================
    DATA QUALITY REPORT
    ============================================================
    
    1. MISSING VALUES по позициям фракталов:
       Позиции с пропусками: 0
       ✅ Пропусков не обнаружено!
    


    
![png](EDA_files/EDA_37_1.png)
    


    
    ✅ График сохранён: plots/sequence_missing_values.png
    


```python
# Causal Consistency валидация (КРИТИЧНО для выявления data leakage)

print("\n" + "=" * 60)
print("CAUSAL CONSISTENCY VALIDATION")
print("=" * 60)

# Проверка: фракталы упорядочены по времени (от новых к старым)?
# fractal[0] должен быть самым новым, fractal[98] - самым старым
# т.е. fractal_time должен убывать: fractal_time[0] >= fractal_time[1] >= ... >= fractal_time[98]

causal_violations = []
fractal_times = X_full[:, :, 0]  # (n_samples, 99)

for i in range(len(X_full)):
    times = fractal_times[i]
    # Проверяем, что времена убывают (или равны)
    if not np.all(times[:-1] >= times[1:]):
        # Находим позиции нарушений
        violations_mask = times[:-1] < times[1:]
        violation_positions = np.where(violations_mask)[0]
        causal_violations.append({
            'row': i,
            'positions': violation_positions.tolist(),
            'times_at_violations': [(int(pos), times[pos], times[pos+1]) for pos in violation_positions[:3]]
        })

print(f"\n1. Проверка упорядоченности фракталов по времени:")
if len(causal_violations) == 0:
    print(f"   ✅ PASSED: Все {len(X_full)} строк корректно упорядочены (fractal_time убывает)")
else:
    print(f"   ❌ ISSUES DETECTED: {len(causal_violations)} строк с нарушениями!")
    print(f"   Примеры нарушений (первые 5):")
    for v in causal_violations[:5]:
        print(f"      Строка {v['row']}: позиции {v['positions'][:5]}...")

# Проверка эволюции признаков для одного и того же фрактала через несколько строк
print(f"\n2. Проверка эволюции признаков фрактала между строками:")

# Найдём уникальные фракталы по (fractal_time, direction) и отследим их эволюцию
# Для этого создадим словарь: (time, direction) -> [(row_idx, position, back, power, count), ...]
from collections import defaultdict

fractal_tracker = defaultdict(list)

# Ограничимся первыми 1000 строками для анализа
sample_rows = min(1000, len(X_full))

for row_idx in range(sample_rows):
    for pos in range(min(20, 99)):  # Анализируем первые 20 позиций
        time_val = X_full[row_idx, pos, 0]
        direction_val = X_full[row_idx, pos, 2]
        back_val = X_full[row_idx, pos, 4]
        power_val = X_full[row_idx, pos, 8]
        count_val = X_full[row_idx, pos, 9]
        
        if not np.isnan(time_val):
            key = (int(time_val), int(direction_val))
            fractal_tracker[key].append({
                'row': row_idx,
                'position': pos,
                'back': back_val,
                'power': power_val,
                'count': count_val
            })

# Анализ фракталов, которые появляются в нескольких строках
multi_occurrence_fractals = {k: v for k, v in fractal_tracker.items() if len(v) > 1}

print(f"   Фракталов, появляющихся в нескольких строках: {len(multi_occurrence_fractals)}")

# Проверим монотонность признаков
monotonicity_violations = []

for (time_val, direction), occurrences in list(multi_occurrence_fractals.items())[:100]:
    # Сортируем по строке (времени)
    occurrences_sorted = sorted(occurrences, key=lambda x: x['row'])
    
    # Проверяем: back должен только расти или оставаться, position должен расти
    for i in range(len(occurrences_sorted) - 1):
        curr = occurrences_sorted[i]
        next_occ = occurrences_sorted[i + 1]
        
        # Position должен увеличиваться (фрактал становится "старше")
        if next_occ['position'] <= curr['position']:
            monotonicity_violations.append({
                'fractal': (time_val, direction),
                'type': 'position_not_increasing',
                'curr_row': curr['row'],
                'next_row': next_occ['row'],
                'curr_pos': curr['position'],
                'next_pos': next_occ['position']
            })

if len(monotonicity_violations) == 0:
    print(f"   ✅ PASSED: Позиции фракталов корректно увеличиваются между строками")
else:
    print(f"   ⚠️ ANOMALIES: {len(monotonicity_violations)} нарушений монотонности позиций")
    print(f"   (Это может быть нормально, если фрактал исчезает из окна наблюдения)")

# Итоговый статус Data Leakage Check
print("\n" + "=" * 60)
print("DATA LEAKAGE CHECK SUMMARY")
print("=" * 60)
if len(causal_violations) == 0:
    print("✅ STATUS: PASSED - Данные корректно упорядочены по времени")
    print("   Фракталы идут от новых (позиция 0) к старым (позиция 98)")
    print("   Data leakage из будущего НЕ ОБНАРУЖЕН")
else:
    print("❌ STATUS: ISSUES DETECTED - Требуется дополнительный анализ")
    print(f"   Обнаружено {len(causal_violations)} строк с нарушениями порядка")
```

    
    ============================================================
    CAUSAL CONSISTENCY VALIDATION
    ============================================================
    
    1. Проверка упорядоченности фракталов по времени:
       ❌ ISSUES DETECTED: 5042 строк с нарушениями!
       Примеры нарушений (первые 5):
          Строка 0: позиции [11, 22, 33, 44, 55]...
          Строка 1: позиции [11, 22, 33, 44, 55]...
          Строка 2: позиции [11, 22, 33, 44, 55]...
          Строка 3: позиции [11, 22, 33, 44, 55]...
          Строка 4: позиции [11, 22, 33, 44, 55]...
    
    2. Проверка эволюции признаков фрактала между строками:
       Фракталов, появляющихся в нескольких строках: 1024
       ⚠️ ANOMALIES: 119 нарушений монотонности позиций
       (Это может быть нормально, если фрактал исчезает из окна наблюдения)
    
    ============================================================
    DATA LEAKAGE CHECK SUMMARY
    ============================================================
    ❌ STATUS: ISSUES DETECTED - Требуется дополнительный анализ
       Обнаружено 5042 строк с нарушениями порядка
    

### 9.2 Статистика последовательности по классам


```python
# Распределение признаков по позициям для каждого класса
print("=" * 60)
print("9.2 СТАТИСТИКА ПОСЛЕДОВАТЕЛЬНОСТИ ПО КЛАССАМ")
print("=" * 60)

# Индексы признаков
feature_idx_map = {
    'price': 1,
    'direction': 2,
    'front': 3,
    'back': 4,
    'power': 8,
    'impulse': 10
}

# Вычисление mean/std для каждой позиции по классам
classes = [-1, 0, 1]
n_positions = 99

# Для каждого признака и класса
stats_by_class = {}
for class_val in classes:
    mask = (y_full == class_val) & valid_mask
    if mask.sum() == 0:
        continue
    
    class_data = X_full[mask]  # (n_samples_class, 99, 11)
    stats_by_class[class_val] = {
        'mean': np.nanmean(class_data, axis=0),  # (99, 11)
        'std': np.nanstd(class_data, axis=0),    # (99, 11)
        'n_samples': mask.sum()
    }

# Визуализация: распределение признаков по позициям
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
axes = axes.flatten()

features_to_plot = ['price', 'power', 'impulse', 'front', 'back', 'direction']
for idx, feature in enumerate(features_to_plot):
    ax = axes[idx]
    feat_idx = feature_idx_map[feature]
    
    for class_val in classes:
        if class_val not in stats_by_class:
            continue
        means = stats_by_class[class_val]['mean'][:, feat_idx]
        positions = np.arange(len(means))
        
        # Исключаем NaN
        valid_mask_pos = ~np.isnan(means)
        ax.plot(positions[valid_mask_pos], means[valid_mask_pos], 
                label=CLASS_NAMES[class_val], color=CLASS_COLORS[class_val], 
                linewidth=2, alpha=0.8)
    
    ax.set_xlabel('Позиция фрактала')
    ax.set_ylabel(f'Mean {feature}')
    ax.set_title(f'Распределение {feature} по позициям')
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{PLOTS_DIR}sequence_features_by_position.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"✅ График сохранён: {PLOTS_DIR}sequence_features_by_position.png")
```

    ============================================================
    9.2 СТАТИСТИКА ПОСЛЕДОВАТЕЛЬНОСТИ ПО КЛАССАМ
    ============================================================
    


    
![png](EDA_files/EDA_40_1.png)
    


    ✅ График сохранён: plots/sequence_features_by_position.png
    


```python
# Temporal patterns: анализ паттернов во времени
print("\n" + "=" * 60)
print("TEMPORAL PATTERNS АНАЛИЗ")
print("=" * 60)

temporal_stats = {}

for class_val in classes:
    mask = (y_full == class_val) & valid_mask
    if mask.sum() == 0:
        continue
    
    class_data = X_full[mask]
    directions = class_data[:, :, 2]  # (n_samples, 99)
    
    # Количество смен direction в последовательности
    direction_changes = []
    longest_streaks = []
    price_volatilities = []
    
    for i in range(len(class_data)):
        dir_seq = directions[i]
        valid_dirs = dir_seq[~np.isnan(dir_seq)]
        
        if len(valid_dirs) > 1:
            # Смены direction
            changes = np.sum(valid_dirs[:-1] != valid_dirs[1:])
            direction_changes.append(changes)
            
            # Longest streak одного direction
            current_streak = 1
            max_streak = 1
            for j in range(1, len(valid_dirs)):
                if valid_dirs[j] == valid_dirs[j-1]:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 1
            longest_streaks.append(max_streak)
        
        # Volatility последовательности (std price)
        prices = class_data[i, :, 1]  # price
        valid_prices = prices[~np.isnan(prices)]
        if len(valid_prices) > 1:
            price_volatilities.append(np.std(valid_prices))
    
    temporal_stats[class_val] = {
        'avg_direction_changes': np.mean(direction_changes) if direction_changes else 0,
        'avg_longest_streak': np.mean(longest_streaks) if longest_streaks else 0,
        'avg_volatility': np.mean(price_volatilities) if price_volatilities else 0,
        'n_samples': mask.sum()
    }

# Вывод статистики
print("\nTemporal patterns по классам:")
for class_val in classes:
    if class_val in temporal_stats:
        stats = temporal_stats[class_val]
        print(f"\n{class_val} ({CLASS_NAMES[class_val]}, n={stats['n_samples']}):")
        print(f"  Среднее количество смен direction: {stats['avg_direction_changes']:.2f}")
        print(f"  Средний longest streak: {stats['avg_longest_streak']:.2f}")
        print(f"  Средняя волатильность цены: {stats['avg_volatility']:.6f}")
```

    
    ============================================================
    TEMPORAL PATTERNS АНАЛИЗ
    ============================================================
    
    Temporal patterns по классам:
    
    -1 (Sell (-1), n=257):
      Среднее количество смен direction: 51.90
      Средний longest streak: 9.89
      Средняя волатильность цены: 0.189073
    
    0 (Neutral (0), n=4545):
      Среднее количество смен direction: 52.55
      Средний longest streak: 9.52
      Средняя волатильность цены: 0.190576
    
    1 (Buy (1), n=240):
      Среднее количество смен direction: 52.91
      Средний longest streak: 9.14
      Средняя волатильность цены: 0.194052
    


```python
# Attention-подобный анализ: какие позиции наиболее отличаются от класса 0
print("\n" + "=" * 60)
print("ATTENTION-ПОДОБНЫЙ АНАЛИЗ")
print("=" * 60)

# Cohen's d для каждой позиции отдельно
def cohens_d(x, y):
    """Вычисление Cohen's d между двумя выборками"""
    nx = len(x)
    ny = len(y)
    dof = nx + ny - 2
    pooled_std = np.sqrt(((nx - 1) * np.var(x, ddof=1) + (ny - 1) * np.var(y, ddof=1)) / dof)
    if pooled_std == 0:
        return 0
    return (np.mean(x) - np.mean(y)) / pooled_std

# Класс 0 как baseline
class_0_mask = (y_full == 0) & valid_mask
class_0_data = X_full[class_0_mask]

# Для minority классов
cohens_d_results = {}

for minority_class in [-1, 1]:
    mask = (y_full == minority_class) & valid_mask
    if mask.sum() == 0:
        continue
    
    minority_data = X_full[mask]
    
    # Для каждого признака и позиции
    cohens_matrix = np.full((99, 11), np.nan)
    
    for pos in range(99):
        for feat_idx in range(11):
            class_0_values = class_0_data[:, pos, feat_idx]
            minority_values = minority_data[:, pos, feat_idx]
            
            # Убираем NaN
            class_0_clean = class_0_values[~np.isnan(class_0_values)]
            minority_clean = minority_values[~np.isnan(minority_values)]
            
            if len(class_0_clean) > 10 and len(minority_clean) > 10:
                d = cohens_d(minority_clean, class_0_clean)
                cohens_matrix[pos, feat_idx] = d
    
    cohens_d_results[minority_class] = cohens_matrix

# Визуализация: Heatmap Cohen's d
fig, axes = plt.subplots(1, 2, figsize=(18, 8))

for idx, minority_class in enumerate([-1, 1]):
    ax = axes[idx]
    matrix = np.abs(cohens_d_results[minority_class])
    
    # Только для ключевых признаков
    key_features = ['price', 'power', 'impulse', 'front', 'back']
    key_feat_indices = [feature_idx_map[f] for f in key_features]
    
    im = ax.imshow(matrix[:, key_feat_indices].T, aspect='auto', cmap='YlOrRd', 
                   interpolation='nearest')
    ax.set_xlabel('Позиция фрактала')
    ax.set_ylabel('Признак')
    ax.set_yticks(range(len(key_features)))
    ax.set_yticklabels(key_features)
    ax.set_title(f'|Cohen\'s d| для класса {minority_class} vs 0')
    plt.colorbar(im, ax=ax, label='|Cohen\'s d|')

plt.tight_layout()
plt.savefig(f'{PLOTS_DIR}attention_cohens_d_heatmap.png', dpi=150, bbox_inches='tight')
plt.show()

# Топ-10 наиболее дискриминативных позиций
print("\nТоп-10 наиболее дискриминативных позиций (по |Cohen's d|):")
for minority_class in [-1, 1]:
    if minority_class not in cohens_d_results:
        continue
    matrix = np.abs(cohens_d_results[minority_class])
    # Усредняем по всем признакам для каждой позиции
    pos_scores = np.nanmean(matrix, axis=1)
    top_positions = np.argsort(pos_scores)[-10:][::-1]
    print(f"\nКласс {minority_class}:")
    for pos in top_positions:
        print(f"  Позиция {pos}: средний |Cohen's d| = {pos_scores[pos]:.3f}")

print(f"\n✅ График сохранён: {PLOTS_DIR}attention_cohens_d_heatmap.png")
```

    
    ============================================================
    ATTENTION-ПОДОБНЫЙ АНАЛИЗ
    ============================================================
    


    
![png](EDA_files/EDA_42_1.png)
    


    
    Топ-10 наиболее дискриминативных позиций (по |Cohen's d|):
    
    Класс -1:
      Позиция 0: средний |Cohen's d| = 0.380
      Позиция 1: средний |Cohen's d| = 0.261
      Позиция 12: средний |Cohen's d| = 0.141
      Позиция 34: средний |Cohen's d| = 0.099
      Позиция 45: средний |Cohen's d| = 0.091
      Позиция 2: средний |Cohen's d| = 0.085
      Позиция 23: средний |Cohen's d| = 0.082
      Позиция 20: средний |Cohen's d| = 0.079
      Позиция 40: средний |Cohen's d| = 0.076
      Позиция 56: средний |Cohen's d| = 0.074
    
    Класс 1:
      Позиция 0: средний |Cohen's d| = 0.406
      Позиция 1: средний |Cohen's d| = 0.278
      Позиция 12: средний |Cohen's d| = 0.137
      Позиция 23: средний |Cohen's d| = 0.099
      Позиция 98: средний |Cohen's d| = 0.098
      Позиция 9: средний |Cohen's d| = 0.096
      Позиция 16: средний |Cohen's d| = 0.092
      Позиция 67: средний |Cohen's d| = 0.088
      Позиция 34: средний |Cohen's d| = 0.088
      Позиция 27: средний |Cohen's d| = 0.087
    
    ✅ График сохранён: plots/attention_cohens_d_heatmap.png
    


```python
### 9.3 Feature Engineering из последовательности
```


```python
from sklearn.linear_model import LinearRegression
from scipy.stats import rankdata

def engineer_sequence_features(X: np.ndarray, y: np.ndarray, valid_mask: np.ndarray) -> pd.DataFrame:
    """
    Извлечение агрегированных признаков из последовательности фракталов.
    
    Args:
        X: тензор (n_samples, 99, 11)
        y: вектор меток (n_samples,)
        valid_mask: маска валидных строк
        
    Returns:
        DataFrame с engineered features
    """
    n_samples = len(X)
    features_dict = {}
    
    # Индексы признаков
    price_idx = 1
    direction_idx = 2
    front_idx = 3
    back_idx = 4
    power_idx = 8
    count_idx = 9
    impulse_idx = 10
    
    print("Извлечение признаков из последовательности...")
    print("Это может занять несколько минут...")
    
    # A. Rolling Statistics
    windows = [1, 2, 3, 4, 5, 10, 20]
    feature_names_rolling = ['price', 'front', 'back', 'power', 'impulse', 'count']
    feature_indices_rolling = [price_idx, front_idx, back_idx, power_idx, impulse_idx, count_idx]
    
    for window in windows:
        for feat_name, feat_idx in zip(feature_names_rolling, feature_indices_rolling):
            # Rolling mean, std, min, max для последних 'window' фракталов
            rolling_data = X[:, :window, feat_idx]  # (n_samples, window)
            
            # Mean
            features_dict[f'{feat_name}_mean_w{window}'] = np.nanmean(rolling_data, axis=1)
            
            # Std
            features_dict[f'{feat_name}_std_w{window}'] = np.nanstd(rolling_data, axis=1)
            
            # Min
            features_dict[f'{feat_name}_min_w{window}'] = np.nanmin(rolling_data, axis=1)
            
            # Max
            features_dict[f'{feat_name}_max_w{window}'] = np.nanmax(rolling_data, axis=1)
    
    print(f"  ✅ Rolling statistics: {len(windows) * len(feature_names_rolling) * 4} признаков")
    
    # B. Trend Indicators (Linear regression slope)
    N_values = [2, 3, 4, 5, 10]
    trend_features = ['price', 'power', 'impulse']
    trend_indices = [price_idx, power_idx, impulse_idx]
    
    for N in N_values:
        for feat_name, feat_idx in zip(trend_features, trend_indices):
            slopes = []
            for i in range(n_samples):
                data = X[i, :N, feat_idx]
                valid_data = data[~np.isnan(data)]
                if len(valid_data) >= 2:
                    x = np.arange(len(valid_data))
                    if np.std(x) > 0:
                        slope = np.polyfit(x, valid_data, 1)[0]
                    else:
                        slope = 0
                else:
                    slope = np.nan
                slopes.append(slope)
            features_dict[f'{feat_name}_slope_{N}'] = slopes
    
    print(f"  ✅ Trend indicators: {len(N_values) * len(trend_features)} признаков")
    
    # C. Directional Patterns
    for N in [3, 5, 10, 20]:
        direction_changes = []
        peak_ratios = []
        longest_streaks = []
        majority_directions = []
        
        for i in range(n_samples):
            dirs = X[i, :N, direction_idx]
            valid_dirs = dirs[~np.isnan(dirs)]
            
            if len(valid_dirs) > 1:
                # Количество смен direction
                changes = np.sum(valid_dirs[:-1] != valid_dirs[1:])
                direction_changes.append(changes)
                
                # Ratio пиков к впадинам
                peaks = np.sum(valid_dirs == 1)
                valleys = np.sum(valid_dirs == -1)
                if valleys > 0:
                    ratio = peaks / valleys
                else:
                    ratio = peaks if peaks > 0 else 0
                peak_ratios.append(ratio)
                
                # Longest streak
                current_streak = 1
                max_streak = 1
                for j in range(1, len(valid_dirs)):
                    if valid_dirs[j] == valid_dirs[j-1]:
                        current_streak += 1
                        max_streak = max(max_streak, current_streak)
                    else:
                        current_streak = 1
                longest_streaks.append(max_streak)
                
                # Majority direction
                current_dir = valid_dirs[0] if len(valid_dirs) > 0 else 0
                majority_dir = 1 if np.sum(valid_dirs == 1) > np.sum(valid_dirs == -1) else -1
                majority_directions.append(1 if current_dir == majority_dir else 0)
            else:
                direction_changes.append(0)
                peak_ratios.append(0)
                longest_streaks.append(0)
                majority_directions.append(0)
        
        features_dict[f'direction_changes_w{N}'] = direction_changes
        features_dict[f'peak_valley_ratio_w{N}'] = peak_ratios
        features_dict[f'longest_streak_w{N}'] = longest_streaks
        features_dict[f'majority_direction_match_w{N}'] = majority_directions
    
    print(f"  ✅ Directional patterns: {len([3, 5, 10, 20]) * 4} признаков")
    
    # D. Relative Features (нормализация относительно окна)
    for window in [10, 20]:
        for feat_name, feat_idx in zip(['price', 'power'], [price_idx, power_idx]):
            # Z-score относительно окна
            z_scores = []
            percentiles = []
            
            for i in range(n_samples):
                window_data = X[i, :window, feat_idx]
                current_val = X[i, 0, feat_idx] if not np.isnan(X[i, 0, feat_idx]) else np.nan
                
                valid_window = window_data[~np.isnan(window_data)]
                if len(valid_window) > 1 and not np.isnan(current_val):
                    mean_w = np.mean(valid_window)
                    std_w = np.std(valid_window)
                    if std_w > 0:
                        z_score = (current_val - mean_w) / std_w
                    else:
                        z_score = 0
                    
                    # Percentile rank
                    percentile = (np.sum(valid_window <= current_val) / len(valid_window)) * 100
                else:
                    z_score = np.nan
                    percentile = np.nan
                
                z_scores.append(z_score)
                percentiles.append(percentile)
            
            features_dict[f'{feat_name}_zscore_w{window}'] = z_scores
            features_dict[f'{feat_name}_percentile_w{window}'] = percentiles
    
    print(f"  ✅ Relative features: {len([10, 20]) * 2 * 2} признаков")
    
    # E. Support/Resistance Indicators
    for window in [3, 5, 10, 20]:
        support_resistance = []
        for i in range(n_samples):
            price_current = X[i, 0, price_idx]
            prices_window = X[i, :window, price_idx]
            
            if not np.isnan(price_current):
                valid_prices = prices_window[~np.isnan(prices_window)]
                if len(valid_prices) > 0:
                    price_range = np.max(valid_prices) - np.min(valid_prices)
                    threshold = 0.02 * price_range if price_range > 0 else 0
                    count_similar = np.sum(np.abs(valid_prices - price_current) < threshold)
                else:
                    count_similar = 0
            else:
                count_similar = 0
            
            support_resistance.append(count_similar)
        
        features_dict[f'support_resistance_w{window}'] = support_resistance
    
    print(f"  ✅ Support/Resistance: {len([3, 5, 10, 20])} признаков")
    
    # F. Momentum & Volatility
    for N in [5, 10, 20]:
        # Cumulative direction
        cumsum_dirs = []
        for i in range(n_samples):
            dirs = X[i, :N, direction_idx]
            valid_dirs = dirs[~np.isnan(dirs)]
            if len(valid_dirs) > 0:
                cumsum_dirs.append(np.sum(valid_dirs))
            else:
                cumsum_dirs.append(0)
        features_dict[f'cumulative_direction_{N}'] = cumsum_dirs
        
        # Price momentum
        price_momentums = []
        for i in range(n_samples):
            prices = X[i, :N, price_idx]
            valid_prices = prices[~np.isnan(prices)]
            if len(valid_prices) >= 2:
                momentum = (valid_prices[0] - valid_prices[-1]) / len(valid_prices)
            else:
                momentum = 0
            price_momentums.append(momentum)
        features_dict[f'price_momentum_{N}'] = price_momentums
        
        # Volatility proxy
        volatilities = []
        for i in range(n_samples):
            prices = X[i, :N, price_idx]
            valid_prices = prices[~np.isnan(prices)]
            if len(valid_prices) > 1:
                mean_price = np.mean(valid_prices)
                if mean_price > 0:
                    volatility = np.std(valid_prices) / mean_price
                else:
                    volatility = 0
            else:
                volatility = 0
            volatilities.append(volatility)
        features_dict[f'volatility_proxy_{N}'] = volatilities
        
        # ATR analog
        atrs = []
        for i in range(n_samples):
            prices = X[i, :N, price_idx]
            valid_prices = prices[~np.isnan(prices)]
            if len(valid_prices) > 1:
                atr = np.mean(np.abs(np.diff(valid_prices)))
            else:
                atr = 0
            atrs.append(atr)
        features_dict[f'atr_analog_{N}'] = atrs
    
    print(f"  ✅ Momentum & Volatility: {len([5, 10, 20]) * 4} признаков")
    
    # G. Interaction Features
    # front * back
    features_dict['front_back_interaction'] = X[:, 0, front_idx] * X[:, 0, back_idx]
    
    # power * impulse
    features_dict['power_impulse_interaction'] = X[:, 0, power_idx] * X[:, 0, impulse_idx]
    
    # count * reverse
    features_dict['count_reverse_interaction'] = X[:, 0, count_idx] * X[:, 0, 7]  # reverse is index 7
    
    # (impulse - mean_impulse_w10) * direction
    impulse_means_w10 = np.nanmean(X[:, :10, impulse_idx], axis=1)
    features_dict['impulse_direction_interaction'] = (X[:, 0, impulse_idx] - impulse_means_w10) * X[:, 0, direction_idx]
    
    print(f"  ✅ Interaction features: 4 признака")
    
    # H. Time-based Features
    # Δt между fractal[0] и fractal[1], [2], [3], [4], [5]
    for offset in [1, 2, 3, 4, 5]:
        time_diffs = []
        for i in range(n_samples):
            time_0 = X[i, 0, 0]  # fractal_time at position 0
            time_offset = X[i, offset, 0] if offset < 99 else np.nan
            if not np.isnan(time_0) and not np.isnan(time_offset):
                time_diffs.append(time_0 - time_offset)
            else:
                time_diffs.append(np.nan)
        features_dict[f'time_diff_{offset}'] = time_diffs
    
    # Acceleration: (Δt[0→1] - Δt[1→2]) / Δt[1→2]
    accelerations = []
    for i in range(n_samples):
        time_0 = X[i, 0, 0]
        time_1 = X[i, 1, 0]
        time_2 = X[i, 2, 0]
        if not np.isnan(time_0) and not np.isnan(time_1) and not np.isnan(time_2):
            dt_01 = time_0 - time_1
            dt_12 = time_1 - time_2
            if dt_12 > 0:
                acceleration = (dt_01 - dt_12) / dt_12
            else:
                acceleration = 0
        else:
            acceleration = np.nan
        accelerations.append(acceleration)
    features_dict['time_acceleration'] = accelerations
    
    print(f"  ✅ Time-based features: 6 признаков")
    
    # Создаём DataFrame
    features_df = pd.DataFrame(features_dict)
    features_df['signal'] = y
    features_df['row_idx'] = np.arange(n_samples)
    
    print(f"\n✅ Всего создано {len(features_dict)} признаков")
    print(f"   Размерность DataFrame: {features_df.shape}")
    
    return features_df

# Извлечение признаков
print("=" * 60)
print("9.3 FEATURE ENGINEERING")
print("=" * 60)

engineered_features = engineer_sequence_features(X_full, y_full, valid_mask)
print(f"\n✅ Feature engineering завершён!")
print(f"   Создано {engineered_features.shape[1] - 2} признаков (без signal и row_idx)")
```

    ============================================================
    9.3 FEATURE ENGINEERING
    ============================================================
    Извлечение признаков из последовательности...
    Это может занять несколько минут...
      ✅ Rolling statistics: 168 признаков
      ✅ Trend indicators: 15 признаков
      ✅ Directional patterns: 16 признаков
      ✅ Relative features: 8 признаков
      ✅ Support/Resistance: 4 признаков
      ✅ Momentum & Volatility: 12 признаков
      ✅ Interaction features: 4 признака
      ✅ Time-based features: 6 признаков
    
    ✅ Всего создано 233 признаков
       Размерность DataFrame: (5042, 235)
    
    ✅ Feature engineering завершён!
       Создано 233 признаков (без signal и row_idx)
    

Раздел 9.4: Визуализация паттернов последовательности


```python
print("=" * 60)
print("9.4 ВИЗУАЛИЗАЦИЯ ПАТТЕРНОВ ПОСЛЕДОВАТЕЛЬНОСТИ")
print("=" * 60)

# Sequence heatmaps по классам
print("\n1. Sequence heatmaps по классам...")

# Усреднение последовательностей по классам
feature_idx_map = {
    'price': 1,
    'direction': 2,
    'front': 3,
    'back': 4,
    'power': 8,
    'impulse': 10
}

key_features = ['price', 'power', 'impulse', 'front', 'back']
key_feat_indices = [feature_idx_map[f] for f in key_features]

fig, axes = plt.subplots(1, 3, figsize=(20, 6))

for class_idx, class_val in enumerate([-1, 0, 1]):
    mask = (y_full == class_val) & valid_mask
    if mask.sum() == 0:
        continue
    
    class_data = X_full[mask]  # (n_samples, 99, 11)
    
    # Усредняем по всем последовательностям класса
    mean_seq = np.nanmean(class_data, axis=0)  # (99, 11)
    
    # Берём только ключевые признаки
    mean_seq_key = mean_seq[:, key_feat_indices]  # (99, 5)
    
    # Heatmap
    im = axes[class_idx].imshow(mean_seq_key.T, aspect='auto', cmap='viridis', 
                               interpolation='nearest')
    axes[class_idx].set_xlabel('Позиция фрактала')
    axes[class_idx].set_ylabel('Признак')
    axes[class_idx].set_yticks(range(len(key_features)))
    axes[class_idx].set_yticklabels(key_features)
    axes[class_idx].set_title(f'Усреднённая последовательность: {CLASS_NAMES[class_val]} (n={mask.sum()})')
    plt.colorbar(im, ax=axes[class_idx], label='Mean value')

plt.tight_layout()
plt.savefig(f'{PLOTS_DIR}sequence_heatmaps_by_class.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"✅ График сохранён: {PLOTS_DIR}sequence_heatmaps_by_class.png")
```

    ============================================================
    9.4 ВИЗУАЛИЗАЦИЯ ПАТТЕРНОВ ПОСЛЕДОВАТЕЛЬНОСТИ
    ============================================================
    
    1. Sequence heatmaps по классам...
    


    
![png](EDA_files/EDA_46_1.png)
    


    ✅ График сохранён: plots/sequence_heatmaps_by_class.png
    


```python
# Sample sequences visualization для minority классов
print("\n2. Sample sequences visualization...")

fig, axes = plt.subplots(2, 3, figsize=(18, 12))
axes = axes.flatten()

for class_idx, class_val in enumerate([-1, 1]):
    mask = (y_full == class_val) & valid_mask
    if mask.sum() == 0:
        continue
    
    class_data = X_full[mask]
    class_indices = np.where(mask)[0]
    
    # Выбираем 3-5 примеров
    n_samples = min(5, len(class_data))
    sample_indices = np.random.choice(len(class_data), n_samples, replace=False)
    
    # Графики для price, power, impulse
    for feat_idx, feat_name in enumerate(['price', 'power', 'impulse']):
        ax = axes[class_idx * 3 + feat_idx]
        
        for sample_idx in sample_indices:
            seq = class_data[sample_idx, :, feature_idx_map[feat_name]]
            valid_mask_seq = ~np.isnan(seq)
            positions = np.arange(len(seq))[valid_mask_seq]
            values = seq[valid_mask_seq]
            
            ax.plot(positions, values, alpha=0.6, linewidth=1.5, 
                   label=f'Sample {sample_idx}' if sample_idx == sample_indices[0] else '')
        
        ax.set_xlabel('Позиция фрактала')
        ax.set_ylabel(feat_name)
        ax.set_title(f'{feat_name} для класса {CLASS_NAMES[class_val]} (n={n_samples} примеров)')
        ax.legend()
        ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{PLOTS_DIR}sample_sequences_minority_classes.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"✅ График сохранён: {PLOTS_DIR}sample_sequences_minority_classes.png")
```

    
    2. Sample sequences visualization...
    


    
![png](EDA_files/EDA_47_1.png)
    


    ✅ График сохранён: plots/sample_sequences_minority_classes.png
    


```python
# Differential patterns (signal≠0 vs signal=0)
print("\n3. Differential patterns...")

# Для каждой позиции и каждого признака вычисляем разницу
class_0_mask = (y_full == 0) & valid_mask
class_0_data = X_full[class_0_mask]

minority_mask = ((y_full == -1) | (y_full == 1)) & valid_mask
minority_data = X_full[minority_mask]

# Вычисляем разницу mean
diff_matrix = np.full((99, 11), np.nan)

for pos in range(99):
    for feat_idx in range(11):
        class_0_values = class_0_data[:, pos, feat_idx]
        minority_values = minority_data[:, pos, feat_idx]
        
        class_0_clean = class_0_values[~np.isnan(class_0_values)]
        minority_clean = minority_values[~np.isnan(minority_values)]
        
        if len(class_0_clean) > 10 and len(minority_clean) > 10:
            diff = np.mean(minority_clean) - np.mean(class_0_clean)
            diff_matrix[pos, feat_idx] = diff

# Heatmap различий
fig, ax = plt.subplots(figsize=(16, 8))

key_feat_indices = [feature_idx_map[f] for f in key_features]
diff_matrix_key = diff_matrix[:, key_feat_indices]

im = ax.imshow(diff_matrix_key.T, aspect='auto', cmap='RdBu_r', 
              interpolation='nearest', vmin=-np.nanmax(np.abs(diff_matrix_key)), 
              vmax=np.nanmax(np.abs(diff_matrix_key)))
ax.set_xlabel('Позиция фрактала')
ax.set_ylabel('Признак')
ax.set_yticks(range(len(key_features)))
ax.set_yticklabels(key_features)
ax.set_title('Differential patterns: mean(signal≠0) - mean(signal=0)')
plt.colorbar(im, ax=ax, label='Difference')

plt.tight_layout()
plt.savefig(f'{PLOTS_DIR}differential_patterns.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"✅ График сохранён: {PLOTS_DIR}differential_patterns.png")
```

    
    3. Differential patterns...
    


    
![png](EDA_files/EDA_48_1.png)
    


    ✅ График сохранён: plots/differential_patterns.png
    

Раздел 9.5: Корреляционный анализ engineered features


```python
print("=" * 60)
print("9.5 КОРРЕЛЯЦИОННЫЙ АНАЛИЗ ENGINEERED FEATURES")
print("=" * 60)

from sklearn.feature_selection import mutual_info_classif
from scipy.stats import pointbiserialr

# Подготовка данных
feature_cols = [col for col in engineered_features.columns if col not in ['signal', 'row_idx']]
X_features = engineered_features[feature_cols].fillna(0)  # Заполняем NaN нулями
y_target = engineered_features['signal']

print(f"\nАнализ {len(feature_cols)} признаков...")

# 1. Feature importance ranking
print("\n1. Feature importance ranking...")

# Correlation с целевой переменной
correlations = []
for col in feature_cols:
    try:
        corr, p_value = pointbiserialr(X_features[col], y_target)
        correlations.append({
            'feature': col,
            'correlation': corr if not np.isnan(corr) else 0,
            'p_value': p_value if not np.isnan(p_value) else 1
        })
    except:
        correlations.append({
            'feature': col,
            'correlation': 0,
            'p_value': 1
        })

corr_df = pd.DataFrame(correlations)
corr_df['abs_correlation'] = np.abs(corr_df['correlation'])
corr_df = corr_df.sort_values('abs_correlation', ascending=False)

# Mutual Information (выборочно для топ-100 по корреляции, т.к. это медленно)
print("   Вычисление Mutual Information для топ-100 признаков...")
top_100_features = corr_df.head(100)['feature'].values
X_top100 = X_features[top_100_features]

try:
    mi_scores = mutual_info_classif(X_top100, y_target, random_state=42, n_neighbors=3)
    mi_dict = dict(zip(top_100_features, mi_scores))
    
    # Добавляем MI в DataFrame
    corr_df['mutual_info'] = corr_df['feature'].map(mi_dict).fillna(0)
except Exception as e:
    print(f"   ⚠️ Ошибка при вычислении MI: {e}")
    corr_df['mutual_info'] = 0

# Финальный ranking
corr_df['importance_score'] = (corr_df['abs_correlation'] * 0.5 + 
                                corr_df['mutual_info'] / corr_df['mutual_info'].max() * 0.5)
corr_df = corr_df.sort_values('importance_score', ascending=False)

print(f"\n   Топ-20 признаков по важности:")
print(corr_df.head(20)[['feature', 'correlation', 'mutual_info', 'importance_score']].to_string())

# Сохранение ranking
corr_df.to_csv(f'{PLOTS_DIR}feature_importance_sequence.csv', index=False)
print(f"\n✅ Feature importance сохранён: {PLOTS_DIR}feature_importance_sequence.csv")
```

    ============================================================
    9.5 КОРРЕЛЯЦИОННЫЙ АНАЛИЗ ENGINEERED FEATURES
    ============================================================
    
    Анализ 233 признаков...
    
    1. Feature importance ranking...
       Вычисление Mutual Information для топ-100 признаков...
    
       Топ-20 признаков по важности:
                               feature  correlation  mutual_info  importance_score
    168                  price_slope_2    -0.346919     0.085391          0.673459
    4                    front_mean_w1     0.043518     0.067033          0.414267
    6                     front_min_w1     0.043518     0.066080          0.408688
    7                     front_max_w1     0.043518     0.065751          0.406759
    200           price_percentile_w10     0.201343     0.040733          0.339180
    199               price_zscore_w10     0.223740     0.033514          0.308107
    226  impulse_direction_interaction     0.230683     0.027994          0.279259
    16                 impulse_mean_w1    -0.056028     0.041151          0.268974
    19                  impulse_max_w1    -0.056028     0.040139          0.263044
    204           price_percentile_w20     0.175729     0.028213          0.253063
    18                  impulse_min_w1    -0.056028     0.037589          0.248113
    225      count_reverse_interaction    -0.028325     0.038805          0.241382
    43                  impulse_max_w2    -0.051451     0.034991          0.230615
    203               price_zscore_w20     0.189610     0.022141          0.224450
    171                  price_slope_3    -0.168223     0.021316          0.208926
    64                 impulse_mean_w3    -0.061858     0.029744          0.205094
    67                  impulse_max_w3    -0.054427     0.030365          0.205015
    40                 impulse_mean_w2    -0.062056     0.024737          0.175872
    212               price_momentum_5     0.150876     0.015661          0.167141
    42                  impulse_min_w2    -0.067419     0.020400          0.153158
    
    ✅ Feature importance сохранён: plots/feature_importance_sequence.csv
    


```python
# 2. Redundancy analysis
print("\n2. Redundancy analysis...")

# Корреляционная матрица всех признаков (выборочно для топ-50)
top_50_features = corr_df.head(50)['feature'].values
X_top50 = X_features[top_50_features]

corr_matrix = X_top50.corr().abs()

# Находим пары с correlation > 0.95
redundant_pairs = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        corr_val = corr_matrix.iloc[i, j]
        if corr_val > 0.95:
            redundant_pairs.append({
                'feature1': corr_matrix.columns[i],
                'feature2': corr_matrix.columns[j],
                'correlation': corr_val
            })

if redundant_pairs:
    redundant_df = pd.DataFrame(redundant_pairs)
    print(f"   Найдено {len(redundant_pairs)} пар с correlation > 0.95:")
    print(redundant_df.head(10).to_string())
    
    # Рекомендации: какие признаки можно удалить
    features_to_remove = set()
    for _, row in redundant_df.iterrows():
        feat1_importance = corr_df[corr_df['feature'] == row['feature1']]['importance_score'].values[0]
        feat2_importance = corr_df[corr_df['feature'] == row['feature2']]['importance_score'].values[0]
        
        if feat1_importance < feat2_importance:
            features_to_remove.add(row['feature1'])
        else:
            features_to_remove.add(row['feature2'])
    
    print(f"\n   Рекомендация: можно удалить {len(features_to_remove)} признаков:")
    print(f"   {list(features_to_remove)[:10]}")
else:
    print("   ✅ Redundant features не обнаружено (correlation < 0.95)")
```

    
    2. Redundancy analysis...
       Найдено 15 пар с correlation > 0.95:
                   feature1          feature2  correlation
    0         front_mean_w1      front_min_w1     1.000000
    1         front_mean_w1      front_max_w1     1.000000
    2          front_min_w1      front_max_w1     1.000000
    3  price_percentile_w10  price_zscore_w10     0.968047
    4       impulse_mean_w1    impulse_max_w1     1.000000
    5       impulse_mean_w1    impulse_min_w1     1.000000
    6        impulse_max_w1    impulse_min_w1     1.000000
    7  price_percentile_w20  price_zscore_w20     0.965543
    8        impulse_max_w2   impulse_mean_w2     0.955247
    9      price_momentum_5     price_slope_5     0.966367
    
       Рекомендация: можно удалить 11 признаков:
       ['impulse_max_w1', 'impulse_mean_w2', 'back_mean_w1', 'back_min_w1', 'price_slope_5', 'front_max_w1', 'impulse_min_w1', 'price_zscore_w20', 'price_zscore_w10', 'front_min_w1']
    


```python
# 3. Feature stability по классам
print("\n3. Feature stability по классам...")

# Boxplot для топ-20 признаков
top_20_features = corr_df.head(20)['feature'].values

fig, axes = plt.subplots(4, 5, figsize=(20, 16))
axes = axes.flatten()

for idx, feat_name in enumerate(top_20_features[:20]):
    ax = axes[idx]
    
    data_by_class = []
    labels = []
    
    for class_val in [-1, 0, 1]:
        mask = y_target == class_val
        values = X_features.loc[mask, feat_name]
        values_clean = values[~np.isnan(values)]
        
        if len(values_clean) > 0:
            data_by_class.append(values_clean)
            labels.append(CLASS_NAMES[class_val])
    
    if data_by_class:
        bp = ax.boxplot(data_by_class, labels=labels, patch_artist=True)
        
        # Раскрашиваем boxplots
        colors = [CLASS_COLORS[-1], CLASS_COLORS[0], CLASS_COLORS[1]]
        for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax.set_title(feat_name[:30], fontsize=9)
        ax.tick_params(axis='x', rotation=45, labelsize=8)
        ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{PLOTS_DIR}engineered_features_boxplots.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"✅ График сохранён: {PLOTS_DIR}engineered_features_boxplots.png")
```

    
    3. Feature stability по классам...
    


    
![png](EDA_files/EDA_52_1.png)
    


    ✅ График сохранён: plots/engineered_features_boxplots.png
    

Раздел 9.6: Экспорт результатов


```python
print("=" * 60)
print("9.6 ЭКСПОРТ РЕЗУЛЬТАТОВ")
print("=" * 60)

import json
from datetime import datetime

# 1. Сохранение engineered dataset
print("\n1. Сохранение engineered dataset...")

# Добавляем временные признаки из исходных данных
if 'time' in raw_df.columns:
    engineered_features['time'] = raw_df['time'].values

# Сохранение
output_file = 'nero_features_engineered.csv'
engineered_features.to_csv(output_file, index=False)
print(f"   ✅ Сохранено: {output_file}")
print(f"   Размерность: {engineered_features.shape}")
```

    ============================================================
    9.6 ЭКСПОРТ РЕЗУЛЬТАТОВ
    ============================================================
    
    1. Сохранение engineered dataset...
       ✅ Сохранено: nero_features_engineered.csv
       Размерность: (5042, 236)
    


```python
# 2. Feature catalog (JSON)
print("\n2. Создание feature catalog...")

feature_catalog = []

for idx, row in corr_df.iterrows():
    feat_name = row['feature']
    
    # Определяем тип признака
    feat_type = 'unknown'
    window = None
    base_feature = None
    aggregation = None
    
    if '_mean_w' in feat_name:
        feat_type = 'rolling_statistic'
        parts = feat_name.split('_mean_w')
        base_feature = parts[0]
        window = int(parts[1])
        aggregation = 'mean'
    elif '_std_w' in feat_name:
        feat_type = 'rolling_statistic'
        parts = feat_name.split('_std_w')
        base_feature = parts[0]
        window = int(parts[1])
        aggregation = 'std'
    elif '_slope_' in feat_name:
        feat_type = 'trend_indicator'
        parts = feat_name.split('_slope_')
        base_feature = parts[0]
        window = int(parts[1])
        aggregation = 'slope'
    elif '_zscore_w' in feat_name:
        feat_type = 'relative_feature'
        parts = feat_name.split('_zscore_w')
        base_feature = parts[0]
        window = int(parts[1])
        aggregation = 'zscore'
    elif 'interaction' in feat_name:
        feat_type = 'interaction_feature'
    elif 'momentum' in feat_name or 'volatility' in feat_name:
        feat_type = 'momentum_volatility'
    elif 'direction' in feat_name:
        feat_type = 'directional_pattern'
    elif 'time' in feat_name:
        feat_type = 'time_based'
    else:
        feat_type = 'other'
    
    feature_catalog.append({
        'feature_name': feat_name,
        'type': feat_type,
        'window': window,
        'base_feature': base_feature,
        'aggregation': aggregation,
        'importance_rank': int(row.name) + 1,
        'correlation_with_target': float(row['correlation']),
        'mutual_information': float(row['mutual_info']),
        'importance_score': float(row['importance_score'])
    })

# Сохранение
with open('feature_catalog.json', 'w', encoding='utf-8') as f:
    json.dump(feature_catalog, f, indent=2, ensure_ascii=False)

print(f"   ✅ Сохранено: feature_catalog.json")
print(f"   Записей: {len(feature_catalog)}")
```

    
    2. Создание feature catalog...
       ✅ Сохранено: feature_catalog.json
       Записей: 233
    


```python
# 3. Отчёт с рекомендациями (Markdown)
print("\n3. Создание отчёта...")

report = f"""# Sequence Analysis Summary

**Дата создания:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Data Quality

- **Successfully parsed:** {parse_stats['valid_rows']} строк ({parse_stats['parse_rate']:.2f}%)
- **Missing values:** {'Обнаружены' if missing_rate_per_position.max() > 0 else 'Не обнаружены'}
- **Causal consistency:** {'⚠️ ISSUES DETECTED' if len(causal_violations) > 0 else '✅ PASSED'}
  - Нарушения порядка: {len(causal_violations) if 'causal_violations' in locals() else 0} строк
  - Систематические нарушения на позициях: [11, 22, 33, 44, 55] (требует дополнительного анализа)

## Key Findings

### Топ-10 наиболее дискриминативных позиций фракталов:

"""

# Добавляем информацию о топ позициях
if 'cohens_d_results' in locals():
    for minority_class in [-1, 1]:
        if minority_class in cohens_d_results:
            matrix = np.abs(cohens_d_results[minority_class])
            pos_scores = np.nanmean(matrix, axis=1)
            top_positions = np.argsort(pos_scores)[-10:][::-1]
            report += f"\n**Класс {minority_class}:**\n"
            for pos in top_positions[:10]:
                report += f"- Позиция {pos}: средний |Cohen's d| = {pos_scores[pos]:.3f}\n"

report += f"""

### Топ-20 engineered features по важности:

"""

# Добавляем топ-20 признаков
for idx, row in corr_df.head(20).iterrows():
    report += f"{idx+1}. **{row['feature']}** (correlation={row['correlation']:.3f}, MI={row['mutual_info']:.3f})\n"

report += f"""

## Recommendations for Modeling

### 1. Архитектура модели

- **Вариант A:** Использовать full sequence (99 фракталов) с LSTM/Transformer
  - Преимущества: сохранение временной структуры
  - Недостатки: требует больше вычислительных ресурсов
  
- **Вариант B:** Feature-based модель с engineered features ({len(feature_cols)} признаков)
  - Преимущества: быстрее обучение, интерпретируемость
  - Недостатки: потеря части временной информации

### 2. Критичные признаки

Топ-10 признаков для включения в модель:
"""

for idx, row in corr_df.head(10).iterrows():
    report += f"- `{row['feature']}` (importance={row['importance_score']:.4f})\n"

report += f"""

### 3. Temporal features

Рекомендуется добавить:
- `hour_sin`, `hour_cos` (из времени)
- `day_of_week_sin`, `day_of_week_cos` (из времени)

### 4. Data Leakage Check

**Status:** {'❌ ISSUES DETECTED' if ('causal_violations' in locals() and len(causal_violations) > 0) else '✅ PASSED'}

**Details:**
- Нарушения упорядоченности по времени обнаружены на позициях [11, 22, 33, 44, 55]
- Требуется дополнительный анализ: возможно, это особенность структуры данных
- Рекомендуется проверить логику формирования фракталов

### 5. Feature Selection

- Всего создано: {len(feature_cols)} признаков
- Redundant features (correlation > 0.95): {len(redundant_pairs) if 'redundant_pairs' in locals() else 0}
- Рекомендуется удалить избыточные признаки перед обучением

## Файлы результатов

- `nero_features_engineered.csv` - датасет с engineered features
- `feature_catalog.json` - метаданные признаков
- `feature_importance_sequence.csv` - ranking признаков
- `sequence_heatmaps_by_class.png` - heatmaps по классам
- `sample_sequences_minority_classes.png` - примеры последовательностей
- `differential_patterns.png` - дифференциальные паттерны
- `engineered_features_boxplots.png` - boxplots признаков

---

**Следующие шаги:**
1. Провести дополнительный анализ нарушений на позициях [11, 22, 33, 44, 55]
2. Выбрать архитектуру модели (LSTM/Transformer vs Feature-based)
3. Подготовить train/test split с учётом временной структуры
4. Применить техники балансировки классов (SMOTE, class weights)
5. Обучить модель и оценить на тестовой выборке
"""

# Сохранение отчёта
with open('sequence_analysis_report.md', 'w', encoding='utf-8') as f:
    f.write(report)

print(f"   ✅ Сохранено: sequence_analysis_report.md")

print("\n" + "=" * 60)
print("✅ ЭКСПОРТ ЗАВЕРШЁН")
print("=" * 60)
print("\nСозданные файлы:")
print("  - nero_features_engineered.csv")
print("  - feature_catalog.json")
print("  - feature_importance_sequence.csv")
print("  - sequence_analysis_report.md")
print("\n✅ Раздел 9 (Анализ полной последовательности фракталов) завершён!")
```

    
    3. Создание отчёта...
       ✅ Сохранено: sequence_analysis_report.md
    
    ============================================================
    ✅ ЭКСПОРТ ЗАВЕРШЁН
    ============================================================
    
    Созданные файлы:
      - nero_features_engineered.csv
      - feature_catalog.json
      - feature_importance_sequence.csv
      - sequence_analysis_report.md
    
    ✅ Раздел 9 (Анализ полной последовательности фракталов) завершён!
    


```python

```


```python

```
