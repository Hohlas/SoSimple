# DATA FLOW
> **Поток данных через пайплайн SoSimple**

---

## 🔄 Общая схема потока

```
[Торговый эксперт] $o$imple.mq4 → NERO_CSV_CREATE() (lib_PIC.mqh)
          ↓
MT/MQL4/Files/Nero.csv (raw, UTF-16LE)
          ↓
    [Сортировка фракталов]
          ↓
    DATA/Nero_sorted_temp.csv
          ↓
    [Маркировка signal + predict + Up/Dn]
          ↓
    DATA/Nero_labeled_temp.csv
          ↓
    [Построчная нормализация]
          ↓
    Nero_normalized (in-memory)
          ↓
    [Разделение 70/15/15]
          ↓
   DATA/Nero_train_labeled.csv
   DATA/Nero_validation_labeled.csv
   DATA/Nero_test_labeled.csv
          ↓
    [Обучение NN] (ML/train.py --task regression_updn)
          ↓
   ML/checkpoints/transformer_updn_best.pt
          ↓
    [Threshold Analysis] (ML/threshold_analysis.py) → оптимальный θ
          ↓
    [Генерация сигналов] (API/generate_signals.py --theta 2.665)
          ↓
   MT/MQL4/Files/ml_signals.csv (58K+ строк)
          ↓
    [Торговый эксперт] $o$imple.mq4 → ML_TRADE() → ордера
          ↓          ↓
     MT4 Лог    DATA/Nero_*_labeled.csv + Nero_*_updn_params.npy (Ground Truth)
          ↓          ↓
    ════════════════════════════════════
         ↓
    [Trade-Level Reconciliation]
      (statistics/signal_tracer.py)
         ↓
    Дossiers: формула SL/TP vs MT4 Actual vs Ground Truth
    CSV-отчет для анализа расхождения Python PF vs MT4 PF
```

---

## 📋 Навигация по этапам

| # | Этап | Код | Docs | Статус |
|---|------|-----|------|--------|
| 1 | Сортировка фракталов | `processing/` | `docs/processing/` | 🏁 |
| 2 | Маркировка signal/predict/UpDn | `processing/` | `docs/processing/` | 🏁 |
| 3 | Построчная нормализация | `processing/` | `docs/processing/` | 🏁 |
| 4 | Split train/val/test | `processing/` | — | 🏁 |
| 5 | Сохранение финальных CSV | `processing/` | — | 🏁 |
| 6 | ML Training (regression_updn) | `ML/` | `docs/ML/` | ✅ |
| 7 | OOS Evaluation & Threshold | `ML/` | `docs/ML/` | ✅ |
| 8 | Генерация ML-сигналов для MT4 | `API/` | `docs/MT/` | ✅ |
| 8b| Triple Barrier (параллельный трек) | `ML/` | `docs/ML/` | 🚧 |
| 9 | Trade-Level Reconciliation | `statistics/` | `docs/statistics/` | 🚧 |

> Легенда: ✅ Активный | 🚧 В разработке | 🏁 Завершён | 📦 Архив | ⚠️ Требует внимания

---

## ⚙️ Этап 1: Сортировка фракталов

### Вход
- **Файл**: `MT/MQL4/Files/Nero.csv`
- **Источник**: Создан экспертом `$o$imple.mq4` функцией `NERO_CSV_CREATE()` в `lib_PIC.mqh`
- **Формат**: 
  - Columns: `time`, `signal`, `predict`, `ATR`, `fractal0`...`fractal99`
  - Separator: `;`
  - Fractal format: `time:price:direction:front:back:strong:break:reverse:power:count:impulse:up_12:dn_12:up_24:dn_24:up_48:dn_48:fractal_atr`

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

#### Команды

```bash
# Активация виртуального окружения
source ~/git/SoSimple/.venv/bin/activate

# Запуск сортировки + маркировки + нормализации + раз split
python processing/label_main.py --input MT/MQL4/Files/Nero.csv --debug

# Расчёт статистики по размеченным данным
python statistics/statistics.py DATA/Nero_train_labeled.csv

# Выполнить EDA ноутбук
cd ~/git/SoSimple/statistics
export NERO_INPUT_PATH="../DATA/Nero_train_labeled.csv"
jupyter nbconvert --execute --to notebook --output EDA_executed --output-dir ./reports EDA.ipynb

# Очистить выходы в исходном файле
jupyter nbconvert --clear-output --inplace EDA.ipynb

# Экспорт в Markdown (без кода)
jupyter nbconvert --to markdown --no-input --no-prompt --output EDA_report reports/EDA_executed.ipynb
```

---

## 🏷️ Этап 2: Маркировка (Labeling)

### Вход
- **Файл**: `DATA/Nero_sorted_temp.csv`
- **Формат**: Отсортированные фракталы

### Процесс
**Модуль**: `processing/label_signals.py` → `label_all()` + `label_updn()`

#### 2.1. Маркировка signal/predict (`label_all`)

Поиск целевого фрактала:
```python
target_fractal = первый фрактал с strong=1 (ближайший в будущем)
```

Расчёт `signal`:
```python
signal = {
  0  если target_fractal не найден,
  +1 если цель выше,
  -1 если цель ниже
}
```

Расчёт `predict`:
```python
predict = (расстояние до цели) * target_direction
```

**Важно**: `predict` может быть **отрицательным** (знак кодирует direction). Этот таргет использовался в ранних экспериментах, сейчас основной таргет — Up/Dn.

#### 2.2. Маркировка Up/Dn (`label_updn`)

Для каждой строки берутся последние накопленные Up/Dn значения из `fractal[0]` до момента его вытеснения:
```python
up_12, dn_12  # макс. экскурсия вверх/вниз за 12 баров после фрактала
up_24, dn_24  # за 24 бара
up_48, dn_48  # за 48 баров
```

Эти 6 значений — **основные таргеты** для regression_updn. Direction-independent, фиксированный горизонт.

### Выход
- **Файл**: `DATA/Nero_labeled_temp.csv` (временный)
- **Колонки**: `signal`, `predict`, `up_12`, `dn_12`, `up_24`, `dn_24`, `up_48`, `dn_48`

#### 2.3. Маркировка Triple Barrier (`label_triple_barrier`)

Вычисляется **до нормализации** на сырых up_24/dn_24 и ATR.

Для каждой комбинации SL ∈ {2, 3} ATR, TP ∈ {3, 6, 9} ATR × {BUY, SELL}:
```python
# BUY: up_24 = MFE вверх, dn_24 = MAE вниз
tp_hit = (up_24 / ATR) >= tp_level
sl_hit = (dn_24 / ATR) >= sl_level
label = 1 if tp_hit and not sl_hit else 0  # оба → 0 (консервативно)
```

**12 бинарных колонок**: buy_sl2_tp3, buy_sl2_tp6, ..., sell_sl3_tp9

### Ключевые требования
- Маркировка **всего датасета** до split — затем разделение на train/val/test
- Нет forward-looking bias (цель — это **будущий** фрактал)
- Up/Dn накапливаются инкрементально в MT4 (LEVELS_FIND_AROUND) и экспортируются в Nero.csv
- **TB labels вычисляются до нормализации** — на сырых значениях up/dn/ATR

---

## 🔢 Этап 3: Построчная нормализация

### Вход
- **DataFrame**: `DATA/Nero_labeled_temp.csv` (в памяти)

### Процесс
**Модуль**: `processing/normalize.py` → `normalize_rowwise()`

#### 3.1. Парсинг фракталов
```python
fractals = parse_fractals_to_array(df)  # shape: (n_rows, n_fractals, 18)
```

#### 3.2. Нормализация по группам

**Группа A**: Piecewise Linear-Log (совместная — front/back/predict)
- **Признаки**: `|predict|`, `front`, `back`
- **Логика**:
  1. Объединяем все значения строки
  2. Вычисляем `lo`, `brk` (85%), `cap` (99%)
  3. Применяем piecewise transform
  4. **Возвращаем знак `predict`** после нормализации

**Группа B**: Piecewise Linear-Log (раздельная)
- **Признаки**: `impulse`, `count`, `reverse`, `power`, `break`
- **Логика**: Отдельные параметры для каждого

**Группа C**: Piecewise Linear-Log (совместная — Up/Dn)
- **Признаки**: `up_12`, `dn_12`, `up_24`, `dn_24`, `up_48`, `dn_48` (фичи фракталов + таргеты строки)
- **Логика**: 606 значений на строку (100 фракталов × 6 полей + 6 таргетов) → общие p85/p99

**Группа D**: Min-Max
- **Признак**: `price`
- **Логика**: Нормализация в [0, 1]

**Группа E**: Без нормализации
- **Признаки**: `direction`, `strong`, `fractal_time`, `fractal_atr`

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
- ATR **не нормализуется** — используется только как знаменатель для ATR_ratio в data_loader.py

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

## 💾 Этап 5: Сохранение финальных файлов

### Выход
```
DATA/Nero_train_labeled.csv
DATA/Nero_validation_labeled.csv
DATA/Nero_test_labeled.csv
DATA/Nero_normalization_stats.csv
```

### Формат CSV
- **Separator**: `;`
- **Columns**: `time`, `signal`, `predict`, `up_12`, `dn_12`, `up_24`, `dn_24`, `up_48`, `dn_48`, `ATR` (сырой), `fractal0`...`fractal99` (нормализованные строки)

---

## 🚧 Этап 6: ML Training (regression_updn)

### Вход
- `DATA/Nero_train_labeled.csv`
- `DATA/Nero_validation_labeled.csv`

### Процесс

#### 6.1. Загрузка и парсинг данных
**Модуль**: `ML/data_loader.py` → `create_data_loaders()`

1. CSV → 3D тензор `(n_samples, 100, 20)`:
   - 17 фрактальных features из CSV (fields 1-17): price, direction, front, back, strong, break, reverse, power, count, impulse, up_12, dn_12, up_24, dn_24, up_48, dn_48, ATR_ratio
   - `fractal_time` (field 0) **исключён как сырое поле**, но используется для вычисления time-фич
   - `fractal_atr` (field 17) → `log(ATR_ratio)` = log(fractal_atr / ATR_raw) — in-place
   - 3 вычисляемые time-фичи: `hour_sin`, `hour_cos` (циклическое кодирование часа), `time_pos` (позиция на оси [0..1])
2. **StandardScaler** (опционально): fit на train (flatten `n_samples*100 × 20`), transform на val
3. Padding mask для NaN-позиций (используется Transformer)
4. **Таргет** `regression_updn`: y shape `(N, 6)` — up_12, dn_12, up_24, dn_24, up_48, dn_48

#### 6.2. Обучение
**Модуль**: `ML/train.py` (CLI: `--model bilstm|cnn1d|transformer|hybrid --task regression_updn`)

- **Loss**: HuberLoss (δ=1.0) на 6 выходов
- **Optimizer**: AdamW (lr, weight_decay подбираются Optuna)
- **Early stopping**: на val Pearson r (среднее по 6 таргетам, patience=10)
- **Scheduler**: ReduceLROnPlateau (patience=5, factor=0.5, monitor=val_pearson_r)
- **Архитектуры**: Transformer Encoder (лучший), Bi-LSTM, 1D-CNN, Hybrid CNN+LSTM

#### 6.3. Сравнение архитектур
**Модуль**: `ML/compare_architectures.py --task regression_updn`

Последовательно обучает все 4 модели, генерирует сводный отчёт.

#### 6.4. Optuna оптимизация
**Модуль**: `ML/optimize.py --model transformer --task regression_updn`

Подбирает: lr, batch_size, dropout, d_model, nhead, num_layers, dim_feedforward.

#### 6.5. Команды

```bash
# Сравнение 4 архитектур
python -m ML.compare_architectures --task regression_updn

# Optuna оптимизация (transformer — лучшая архитектура)
python -m ML.optimize --model transformer --task regression_updn --trials 50 --epochs 30 --seed 42

# Оценка на тестовой выборке (OOS)
python -m ML.evaluate_test --task regression_updn --model transformer

# Threshold analysis: поиск оптимального θ для торговых сигналов
python -m ML.threshold_analysis --task regression_updn --horizon 12

# Логгер экспериментов
python -m ML.experiment_logger --best pearson_r --task regression_updn
```

### Выход
- `ML/checkpoints/transformer_updn_best.pt` (лучшая модель)
- `ML/plots/training_curves_*.png`, `ML/plots/scatter_*.png`
- `ML/reports/architecture_comparison.md`, `ML/reports/optuna_best_params_*.json`

### Ключевые требования
- **StandardScaler fit только на train** — нет data leakage
- **Shuffle=True в train DataLoader** — каждая строка является независимым snapshot
- **Shuffle=False в val DataLoader** — для воспроизводимости метрик

---

## 📈 Этап 7: OOS Evaluation & Threshold Analysis

### Вход
- `DATA/Nero_test_labeled.csv` (отложенная выборка, 15%)
- `ML/checkpoints/transformer_updn_best.pt`

### Процесс

#### 7.1. Оценка на тестовой выборке
**Модуль**: `ML/evaluate_test.py`

Прогоняет обученную модель на test set, вычисляет per-target Pearson r, MAE, R².

#### 7.2. Threshold Analysis
**Модуль**: `ML/threshold_analysis.py --horizon 12`

Для каждого порога θ вычисляет:
- `ratio_up = pred_up / pred_dn` → если `ratio_up > θ` → BUY signal
- `ratio_dn = pred_dn / pred_up` → если `ratio_dn > θ` → SELL signal
- Метрики: Precision, Recall, Profit Factor, кол-во сделок

### Выход
- `ML/reports/evaluate_test_H12.md`
- `ML/reports/threshold_analysis_12H.md`

### Текущий результат (OOS, θ=2.665, 12H)
- Сделок: 2203, Win Rate: 86.20%, **Profit Factor: 4.50**

---

## 🔄 Этап 8: Генерация ML-сигналов для MT4

### Вход
- `DATA/Nero_{train,validation,test}_labeled.csv`
- `ML/checkpoints/transformer_updn_best.pt`

### Процесс
**Модуль**: `API/generate_signals.py`

1. Загружает чекпоинт модели и параметры Optuna
2. Прогоняет все три датасета через модель
3. Для каждой строки: `ratio_up = pred_up / pred_dn`
   - `ratio_up > θ` → signal = **1** (BUY)
   - `ratio_dn > θ` → signal = **-1** (SELL)
   - иначе → signal = **0** (FLAT)
4. Записывает CSV в `MT/MQL4/Files/ml_signals.csv`

```bash
python -m API.generate_signals                     # дефолт: θ=2.665, horizon=12
python -m API.generate_signals --theta 3.0 --horizon 24  # кастом
```

### Выход
- `MT/MQL4/Files/ml_signals.csv` (~58K строк, 2004–2026)
- Формат: `time;signal;pred_up;pred_dn;ratio_up;ratio_dn`

### Интеграция с MT4
- ML_TRADE() в $o$imple.mq4 читает ml_signals.csv через ML_INIT() (lazy load)
- ML_FindSignal() — бинарный поиск по Time[bar]
- Подробности: [docs/MT/ml_signal_integration.md](MT/ml_signal_integration.md), [docs/MT/trading_strategy.md](MT/trading_strategy.md)

---

## 🎯 Этап 8b: Triple Barrier Training & Signals (параллельный трек)

### Отличия от regression_updn
- **Таргет**: 12 бинарных колонок (buy_sl2_tp3 ... sell_sl3_tp9) вместо 6 непрерывных up/dn
- **Loss**: BCEWithLogitsLoss с pos_weight вместо HuberLoss
- **Метрика**: Mean AUC ROC вместо Pearson r
- **Чекпоинт**: `transformer_tb_best.pt`, val Mean AUC=0.7172 (per-target 0.69-0.77)
- **PF**: Реалистичный — `(wins × TP) / (losses × SL)`, timeouts = полный SL loss
- **ВАЖНО**: Требует transfer learning — `--encoder_ckpt ML/checkpoints/transformer_updn_best.pt`. Обучение с нуля → AUC=0.5 (коллапс энкодера из-за симметричного pos_weight).
- **Статус**: Не закончен, требует пересмотра подхода.

### Команды

```bash
# Обучение (transfer learning от regression_updn обязателен!)
python -m ML.train --model transformer --task triple_barrier --epochs 100 --patience 20 \
  --encoder_ckpt ML/checkpoints/transformer_updn_best.pt \
  --model_kwargs '{"num_layers":3,"dropout":0.166,"input_features":20}'

# Оценка на тестовой выборке
python -m ML.evaluate_test --task triple_barrier --model transformer

# Threshold analysis: поиск оптимального θ
python -m ML.threshold_analysis --task triple_barrier --model transformer

# Генерация сигналов
python -m API.generate_signals --task triple_barrier --theta 0.6
```

### Выход
- `ML/checkpoints/transformer_tb_best.pt`
- `MT/MQL4/Files/ml_signals_tb.csv` — формат: `time;signal;sl_atr;tp_atr;prob;ev`
- MT4: `ML_TRADE_TB()` (iSignal=5), SL/TP из CSV в ATR-единицах

---

## 🔍 Data Leakage Prevention

### Применённые меры

1. **Сортировка**: Независима по строкам
2. **Построчная нормализация**: Каждая строка нормализуется независимо
3. **Split последовательный**: Не случайный shuffle (сохраняем временной порядок)
4. **Маркировка до split**: Маркируем весь датасет, затем делим
5. **StandardScaler (NN)**: fit только на train, transform на val
6. **fractal_time** не подаётся как сырое абсолютное значение — используется только для вычисления time-фич (hour_sin, hour_cos, time_pos)
7. **Up/Dn таргеты**: Накапливаются в MT4 инкрементально, не зависят от будущих данных после горизонта

---

## 🔍 Этап 9: Trade-Level Reconciliation (Диагностика расхождения)

### Проблема
Критическое расхождение между Python ML OOS (PF=4.50) и MT4 Strategy Tester (PF≈1.0).

### Три режима диагностики

#### 9.1. Single-trace: полный разбор одного сигнала
```bash
python statistics/signal_tracer.py --time "2023.01.03 04:00"
```
Выводит: ML prediction → формула SL/TP → Ground Truth → Диагноз (TP_CLEAR / SL_CLEAR / BOTH_HIT / TIMEOUT)

#### 9.2. Batch: автоматический поиск top-N высокорейтинговых сигналов
```bash
python statistics/signal_tracer.py --batch --top 10 --min-ratio 5.0 --csv-out batch.csv
```

#### 9.3. From-Log: разбор РЕАЛЬНЫХ сделок из MT4 логов
```bash
python statistics/signal_tracer.py --from-log MT/tester/logs/20260324.log --losses-only --csv-out losses.csv
```
Сравнивает: MT4 actual (Val/Stp/Prf/ATR из лога) vs формула vs Ground Truth

### Вход

| Источник | Данные |
|----------|--------|
| `MT/tester/Files/ml_signals.csv` | time, signal, pred_up, pred_dn, ratio_up, ratio_dn |
| `DATA/Nero_*_labeled.csv` | fractal[i][0] (sorted) → price, fractal_atr, direction |
| `DATA/Nero_*_labeled.csv` cols[104-109] | up_12, dn_12, up_24, dn_24, up_48, dn_48 (нормализованные) |
| `DATA/Nero_*_updn_params.npy` | per-row (brk, cap) для денормализации updn, shape (N, 2) |
| `MT/tester/logs/YYYYMMDD.log` | ML BUY/SELL bar=..., Val, Stp, Prf, ATR, stop loss/take profit |
| `MT/tester/$o$imple.ini` | ML_MinRatio, ML_MaxRR, ML_ScaleK, ML_Min_SL_ATR |

**Важно**: `bar_time` из лога MT4 = `time` в ml_signals.csv. EA открывает сделку на следующем баре после сигнала.

**Ground Truth**: up_12/dn_12 берутся из `Nero_*_labeled.csv` cols[104-109] (нормализованы piecewise linear-log, per-row), денормализуются через `brk/cap` из `Nero_*_updn_params.npy`.

**Погрешность SL/TP**: `Δ ≈ −4/−7 пунктов` — скрипт использует `fractal_atr` из `fractal[i][0]`, MT4 использует `Atr.Fast` на баре входа.

### Документация
- [docs/statistics/signal_tracer.py.md](statistics/signal_tracer.py.md) — полное описание

---

**Последнее обновление**: 2026-03-25
**Автор**: Antigravity + Claude
