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
    [Обучение модели] (🚧 TODO)
          ↓
   model_weights.pt
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

## 🚧 Этап 7: ML Training (TODO)

### Вход
- `DATA/Nero_train_labeled.csv`
- `DATA/Nero_validation_labeled.csv`

### Процесс (планируется)
1. Парсинг фракталов в tensors
2. Построение sequences (если RNN/Transformer)
3. Обучение модели с classification/regression loss
4. Валидация на val_df

### Выход
- `model_weights.pt` или `model.h5`

---

## 🔍 Data Leakage Prevention

### Применённые меры

1. **Сортировка**: Независима по строкам
2. **Построчная нормализация**: Каждая строка нормализуется независимо
3. **ATR fit только на train**: Validation/test используют тот же scaler
4. **Split последовательный**: Не случайный shuffle (сохраняем временной порядок)
5. **Маркировка до split**: Маркируем весь датасет, затем делим

---

**Последнее обновление**: 2026-02-13  
**Автор**: Antigravity + Claude
