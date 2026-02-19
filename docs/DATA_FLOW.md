# DATA FLOW
> **Поток данных через пайплайн SoSimple**

---

## 🔄 Общая схема потока

```
MT/MQL4/Files/Nero.csv (raw)
          ↓
    [Сортировка фракталов]
          ↓
    DATA/Nero_sorted_temp.csv
          ↓
    [Маркировка signal + predict]
          ↓
    DATA/Nero_labeled_temp.csv
          ↓
    [Построчная нормализация]
          ↓
    Nero_normalized (in-memory)
          ↓
    [Разделение 70/15/15]
          ↓
    train / val / test
          ↓
    [ATR нормализация]
          ↓
   DATA/Nero_train_labeled.csv
   DATA/Nero_validation_labeled.csv
   DATA/Nero_test_labeled.csv
          ↓
    [Baseline Experiments] (ML/baseline_experiments.py) ----→ reports/baseline_report.md
          ↓
    [Обучение Нейросетей] (ML/train.py)
          ↓
   ML/checkpoints/*_best.pt
```

---

## ⚙️ Этап 1: Сортировка фракталов

### Вход
- **Файл**: `MT/MQL4/Files/Nero.csv`
- **Формат**: 
  - Columns: `time`, `signal`, `predict`, `ATR`, `fractal0`...`fractal99`
  - Separator: `;`
  - Fractal format: `time:price:direction:front:back:strong:break:reverse:power:count:impulse`

### Процесс
**Модуль**: `processing/label_main.py` → `sort_fractals_in_dataframe()`

1. Парсит каждую строку `fractalN`
2. Извлекает `time` (первое поле до `:`)
3. Сортирует по `time` в **обратном порядке** (новые первые)
4. Записывает обратно в `fractal0`, `fractal1`, ...

### Выход
- **Файл**: `DATA/Nero_sorted_temp.csv` (временный)
- **Валидация**: `verify_sorting_quality()` — проверяет `time[i] >= time[i+1]`

### Ключевые требования
- Сортировка **независима по строкам** — нет data leakage
- Пустые фракталы (`''`) сохраняются как `''`

---

## 🏷️ Этап 2: Маркировка (Labeling)

### Вход
- **Файл**: `DATA/Nero_sorted_temp.csv`
- **Формат**: Отсортированные фракталы

### Процесс
**Модуль**: `processing/label_signals.py` → `label_all()`

#### 2.1. Поиск целевого фрактала
```python
# Логика:
target_fractal = первый фрактал с strong=1 (ближайший в будущем)
```

#### 2.2. Расчёт `signal`
```python
signal = {
  0  если target_fractal не найден,
  +1 если цель выше,
  -1 если цель ниже
}
```

#### 2.3. Расчёт `predict`
```python
predict = (расстояние до цели) * target_direction
# Где:
# - расстояние = front (до пробития)
# - target_direction = -1/+1 (направление целевого фрактала)
```

**Важно**: `predict` может быть **отрицательным** (знак кодирует direction).

### Выход
- **Файл**: `DATA/Nero_labeled_temp.csv` (временный)
- **Новые колонки**: `signal`, `predict` (перезаписывают старые значения)

### Ключевые требования
- Маркировка **всего датасета** до split — затем разделение на train/val/test
- Нет forward-looking bias (цель — это **будущий** фрактал)

---

## 🔢 Этап 3: Построчная нормализация

### Вход
- **DataFrame**: `DATA/Nero_labeled_temp.csv` (в памяти)

### Процесс
**Модуль**: `processing/normalize.py` → `normalize_rowwise()`

#### 3.1. Парсинг фракталов
```python
fractals = parse_fractals_to_array(df)  # shape: (n_rows, n_fractals, 11)
```

#### 3.2. Нормализация по группам

**Группа A**: Piecewise Linear-Log (совместная)
- **Признаки**: `|predict|`, `front`, `back`
- **Логика**:
  1. Объединяем все значения строки
  2. Вычисляем `lo`, `brk` (85%), `cap` (99%)
  3. Применяем piecewise transform
  4. **Возвращаем знак `predict`** после нормализации

**Группа B**: Piecewise Linear-Log (раздельная)
- **Признаки**: `impulse`, `count`, `reverse`, `power`, `break`
- **Логика**: Отдельные параметры для каждого

**Группа C**: Min-Max
- **Признак**: `price`
- **Логика**: Нормализация в [0, 1]

**Группа D**: Без нормализации
- **Признаки**: `direction`, `strong`, `fractal_time`

#### 3.3. Запись обратно
```python
df = array_to_fractal_strings(fractals, df, fractal_columns)
```

### Выход
- **DataFrame** (в памяти): Нормализованные фракталы + predict
- **Артефакт**: `DATA/Nero_normalization_stats.csv` (статистика до нормализации)

### Ключевые требования
- Нормализация **до split** — каждая строка независима
- Нет data leakage (строки не влияют друг на друга)
- ATR **не нормализуется** на этом этапе

---

## ✂️ Этап 4: Разделение (Split)

### Процесс
**Модуль**: `processing/label_main.py` → `split_train_val_test()`

```python
train_end = int(total_rows * 0.70)
val_end = int(total_rows * 0.85)

train_df = df.iloc[:train_end]           # 70%
val_df = df.iloc[train_end:val_end]      # 15%
test_df = df.iloc[val_end:]              # 15%
```

### Выход
- `train_df`, `val_df`, `test_df` (в памяти)

### Ключевые требования
- Разделение **последовательное**, не случайное (time series!)

---

## 📉 Этап 5: ATR нормализация

### Процесс
**Модуль**: `processing/normalize.py`

#### 5.1. Train
```python
train_df = normalize_atr_train(train_df, scaler_path="DATA/Nero_atr_scaler.pkl")
# Выполняет:
# - RobustScaler.fit(train_df['ATR'])
# - RobustScaler.transform(train_df['ATR'])
# - Сохраняет scaler в .pkl
```

#### 5.2. Validation/Test
```python
val_df = normalize_atr_inference(val_df, scaler_path="DATA/Nero_atr_scaler.pkl")
test_df = normalize_atr_inference(test_df, scaler_path="DATA/Nero_atr_scaler.pkl")
# Выполняет:
# - Загружает scaler из .pkl
# - RobustScaler.transform(df['ATR'])
```

### Выход
- **Артефакт**: `DATA/Nero_atr_scaler.pkl` (RobustScaler)

### Ключевые требования
- **fit только на train** — нет data leakage
- Validation/test используют **тот же scaler**

---

## 💾 Этап 6: Сохранение финальных файлов

### Выход
```
DATA/Nero_train_labeled.csv
DATA/Nero_validation_labeled.csv
DATA/Nero_test_labeled.csv
DATA/Nero_atr_scaler.pkl
DATA/Nero_normalization_stats.csv
```

### Формат CSV
- **Separator**: `;`
- **Columns**: `time`, `signal`, `predict`, `ATR` (нормализованный), `fractal0`...`fractal99` (нормализованные строки)

---

## 📊 Этап 6.5: Baseline Experiments

### Вход
- `DATA/Nero_train_labeled.csv`
- `DATA/Nero_validation_labeled.csv`

### Процесс
**Модуль**: `ML/baseline_experiments.py`

1. **Flat features**: Extract 15 features (price, direction, ..., time[hour, dow]) from `fractal[0]`
2. **Engineered features**: ~233 features (rolling stats, trends, volatility)
3. **Training**: 
   - Dummy Classifier (Stratified/MostFrequent)
   - Logistic Regression (StandardScaler)
   - Random Forest (n_estimators=100)
   - XGBoost / LightGBM (class_weight='balanced')
4. **Evaluation**: Macro F1-score, Precision/Recall per class

### Выход
- `ML/reports/baseline_report.md`
- `ML/plots/*.png` (confusion matrices)

---

## 🚧 Этап 7: ML Training

### Вход
- `DATA/Nero_train_labeled.csv`
- `DATA/Nero_validation_labeled.csv`

### Процесс

#### 7.1. Загрузка и парсинг данных
**Модуль**: `ML/data_loader.py` → `create_data_loaders()`

1. CSV → 3D тензор `(n_samples, 100, 11)`:
   - 10 фрактальных features (price, direction, front, back, strong, break, reverse, power, count, impulse)
   - `fractal_time` **исключён** (data leakage через абсолютное время)
   - ATR broadcast на все 100 позиций как 11-й признак
2. **StandardScaler**: fit на train (flatten `n_samples*100 × 11`), transform на val
3. Padding mask для NaN-позиций (используется Transformer)
4. Маппинг меток: `{-1, 0, 1}` → `{0, 1, 2}`

#### 7.2. Обучение
**Модуль**: `ML/train.py` (CLI: `--model bilstm|cnn1d|transformer|hybrid`)

- **Loss**: Focal Loss (gamma=2, alpha=[0.45, 0.10, 0.45])
- **Optimizer**: AdamW (lr=1e-3, weight_decay=1e-4)
- **Early stopping**: на val macro F1 (patience=10). НЕ на loss — при 95% дисбалансе loss может улучшаться за счёт majority-класса
- **Scheduler**: ReduceLROnPlateau (patience=5, factor=0.5, monitor=val_f1_macro)
- **Архитектуры**: Bi-LSTM, 1D-CNN, Transformer Encoder, Hybrid CNN+LSTM

#### 7.3. Сравнение архитектур
**Модуль**: `ML/compare_architectures.py`

Последовательно обучает все 4 модели, генерирует сводный отчёт.

### Выход
- `ML/checkpoints/<model>_best.pt` (веса лучшей модели по val F1)
- `ML/plots/training_curves_<model>.png` (кривые обучения)
- `ML/plots/cm_<model>.png` (confusion matrices)
- `ML/reports/architecture_comparison.md` (сводный отчёт)

### Ключевые требования
- **StandardScaler fit только на train** — нет data leakage
- **Shuffle=True в train DataLoader** — каждая строка является независимым snapshot
- **Shuffle=False в val DataLoader** — для воспроизводимости метрик

---

## 🔍 Data Leakage Prevention

### Применённые меры

1. **Сортировка**: Независима по строкам
2. **Построчная нормализация**: Каждая строка нормализуется независимо
3. **ATR fit только на train**: Validation/test используют тот же scaler
4. **Split последовательный**: Не случайный shuffle (сохраняем временной порядок)
5. **Маркировка до split**: Маркируем весь датасет, затем делим
6. **StandardScaler (NN)**: fit только на train, transform на val
7. **fractal_time исключён** из features для нейросетей

---

**Последнее обновление**: 2026-02-18  
**Автор**: Antigravity + Claude
