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
    [Маркировка signal + predict + Up/Dn (10 горизонтов)]
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
    [Статистическое исследование сигналов] (API/signal_research.py)
          ↓
    [Генерация сигналов] (API/generate_signals.py --theta 2.665 --horizon 12)
          ↓
   MT/MQL4/Files/ml_signals.csv (58K+ строк)
          ↓
    [Торговый эксперт] $o$imple.mq4 → ML_TRADE() → ордера
          ↓          ↓
     MT4 Лог    DATA/Nero_*_labeled.csv (Ground Truth)
          ↓          ↓
    ════════════════════════════════════
         ↓
    [Trade-Level Reconciliation]
      (statistics/signal_tracer.py)
         ↓
    Отчёт: формула SL/TP vs MT4 Actual vs Ground Truth
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
| 8 | Статистическое исследование сигналов | `API/` | — | ✅ |
| 9 | Генерация ML-сигналов для MT4 | `API/` | `docs/MT/` | ✅ |
| 9b| Triple Barrier (параллельный трек) | `ML/` | `docs/ML/` | 🚧 |
| 10 | Trade-Level Reconciliation | `statistics/` | `docs/statistics/` | 🚧 |

> Легенда: ✅ Активный | 🚧 В разработке | 🏁 Завершён | 📦 Архив | ⚠️ Требует внимания

---

## ⚙️ Этап 1: Сортировка фракталов

### Вход
- **Файл**: `MT/MQL4/Files/Nero.csv`
- **Источник**: Создан экспертом `$o$imple.mq4` функцией `NERO_CSV_CREATE()` в `lib_PIC.mqh`
- **Формат**:
  - Columns: `time`, `signal`, `predict`, `ATR`, `fractal0`…`fractal99`
  - Separator: `;`
  - **Fractal format (22 поля)**:
    ```
    T:P:Dir:Frnt:Back:Strong:Brk:Rev:Pwr:Cnt:Imp:Up12:Dn12:Up24:Dn24:Up48:Dn48:Up3:Dn3:Up6:Dn6:FractalAtr
    idx: 0  1   2    3     4    5    6   7   8   9   10   11   12   13   14   15   16  17  18  19  20  21
    ```
    - Поля 0–16: базовые характеристики фрактала
    - Поля 17–20: up_3, dn_3, up_6, dn_6 (MFE/MAE за 3 и 6 баров)
    - Поле 21: fractal_atr (ATR на момент фрактала)

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

# Запуск сортировки + маркировки + нормализации + split
python processing/label_main.py --input MT/MQL4/Files/Nero.csv --debug

# Расчёт статистики по размеченным данным
python statistics/statistics.py DATA/Nero_train_labeled.csv
```

---

## 🏷️ Этап 2: Маркировка (Labeling)

### Вход
- **Файл**: `DATA/Nero_sorted_temp.csv`

### Процесс
**Модуль**: `processing/label_signals.py` → `label_all()` + `label_updn()`

#### 2.1. Маркировка signal/predict (`label_all`)

Поиск целевого фрактала:
```python
target_fractal = первый фрактал с strong=1 (ближайший в будущем)
```

Расчёт `signal` и `predict`:
```python
signal  = +1 / -1 / 0  (BUY / SELL / FLAT — направление к цели)
predict = расстояние до цели × direction  # может быть отрицательным
```

#### 2.2. Маркировка Up/Dn (`label_updn`)

Для каждой строки берутся последние накопленные Up/Dn значения из `fractal[0]`:
```python
# Длинные горизонты (основные таргеты для торговых сигналов)
up_12, dn_12   # MFE/MAE за 12 баров
up_24, dn_24   # за 24 бара
up_48, dn_48   # за 48 баров

# Короткие горизонты (добавлены в Phase B.1)
up_3, dn_3     # MFE/MAE за 3 бара
up_6, dn_6     # за 6 баров
```

**Итого 10 up/dn таргетов** — основа для regression_updn. Direction-independent, фиксированные горизонты.

### Выход
- **Файл**: `DATA/Nero_labeled_temp.csv` (временный)
- **Колонки**: `signal`, `predict`, `up_3`, `dn_3`, `up_6`, `dn_6`, `up_12`, `dn_12`, `up_24`, `dn_24`, `up_48`, `dn_48`

#### 2.3. Маркировка Triple Barrier (`label_triple_barrier`)

Вычисляется **до нормализации** на сырых up_24/dn_24 и ATR.

Для каждой комбинации SL ∈ {2, 3} ATR, TP ∈ {3, 6, 9} ATR × {BUY, SELL}:
```python
tp_hit = (up_24 / ATR) >= tp_level
sl_hit = (dn_24 / ATR) >= sl_level
label = 1 if tp_hit and not sl_hit else 0  # оба → 0 (консервативно)
```

**12 бинарных колонок**: buy_sl2_tp3, buy_sl2_tp6, …, sell_sl3_tp9

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
fractals = parse_fractals_to_array(df)  # shape: (n_rows, 100, 22)
```

#### 3.2. Нормализация по группам

**Группа A**: Piecewise Linear-Log (совместная — front/back/predict)
- **Признаки**: `|predict|`, `front`, `back`
- Вычисляем `lo`, `brk` (85%), `cap` (99%); применяем piecewise transform; возвращаем знак `predict`

**Группа B**: Piecewise Linear-Log (раздельная)
- **Признаки**: `impulse`, `count`, `reverse`, `power`, `break`

**Группа C**: Piecewise Linear-Log (совместная — Up/Dn)
- **UPDN_FIELDS** (пул для расчёта p85/p99): `up_12`, `dn_12`, `up_24`, `dn_24`, `up_48`, `dn_48` — только длинные горизонты
- **UPDN_TARGET_COLUMNS** (нормализуются теми же параметрами, но не входят в пул): `up_3`, `dn_3`, `up_6`, `dn_6`, `up_12`, `dn_12`, `up_24`, `dn_24`, `up_48`, `dn_48`
- **Логика**: (100 фракталов × 6 полей UPDN_FIELDS + 6 таргетов строки) → общие p85/p99; короткие горизонты нормализуются этими же параметрами, не сдвигая их вниз

**Группа D**: Min-Max
- **Признак**: `price` → нормализация в [0, 1]

**Группа E**: Без нормализации
- **Признаки**: `direction`, `strong`, `fractal_time`, `fractal_atr`

#### 3.3. Запись обратно
```python
df = array_to_fractal_strings(fractals, df, fractal_columns)
```

### Выход
- **DataFrame** (в памяти): нормализованные фракталы (22 поля) + predict
- **Артефакт**: `DATA/Nero_normalization_stats.csv`

### Ключевые требования
- Нормализация **до split** — каждая строка независима
- Нет data leakage (строки не влияют друг на друга)
- ATR **не нормализуется** — используется как знаменатель в data_loader.py
- **Короткие горизонты (up_3/dn_3/up_6/dn_6) не включаются в пул p85** — иначе сдвигают перцентиль вниз, нарушая нормализацию длинных горизонтов

---

## ✂️ Этап 4: Разделение (Split)

### Процесс
**Модуль**: `processing/label_main.py` → `split_train_val_test()`

```python
train_end = int(total_rows * 0.70)   # 70%
val_end   = int(total_rows * 0.85)   # 15%
test_df   = df.iloc[val_end:]        # 15% — OOS
```

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
- **Columns**: `time`, `signal`, `predict`, `up_3`, `dn_3`, `up_6`, `dn_6`, `up_12`, `dn_12`, `up_24`, `dn_24`, `up_48`, `dn_48`, `ATR` (сырой), `fractal0`…`fractal99` (нормализованные строки, 22 поля каждая)

---

## 🚧 Этап 6: ML Training (regression_updn)

### Вход
- `DATA/Nero_train_labeled.csv`
- `DATA/Nero_validation_labeled.csv`

### Процесс

#### 6.1. Загрузка и парсинг данных
**Модуль**: `ML/data_loader.py` → `create_data_loaders(seq_len=20)`

Парсинг 22-полевых фракталов → 3D тензор `(n_samples, 100, 20)`:

| Поле в CSV | idx | → X feature | Примечание |
|-----------|-----|-------------|------------|
| fractal_time | 0 | — | только для time-фич |
| price–dn_48 | 1–16 | X[0–15] | 16 базовых фичей |
| up_3, dn_3, up_6, dn_6 | 17–20 | **пропуск** | это таргеты, не фичи |
| fractal_atr | 21 | X[16] = log(atr/ATR_raw) | ATR_ratio |
| — | — | X[17–19] | hour_sin, hour_cos, time_pos |

Итого: **20 фичей** на фрактал. `N_RAW_FEATURES=22`, `FRACTAL_ATR_RAW_IDX=21`.

**seq_len**: хранится 100 фракталов (fractal0 = свежий, fractal99 = старый), для обучения берётся `X[:, :seq_len, :]`. Оптимальный `seq_len=20` определён через ablation study (100 → 50 → **20** → 10).

**Таргет** `regression_updn`: y shape `(N, 10)` — up_3, dn_3, up_6, dn_6, up_12, dn_12, up_24, dn_24, up_48, dn_48.

Три уровня валидации при загрузке:
- `validate_csv_columns` — заголовок CSV совпадает с ожидаемым
- `validate_fractal_format` — 22 поля, корректные типы и диапазоны
- `validate_parsed_features` — valid=100%, ATR std > 0

#### 6.2. Обучение
**Модуль**: `ML/train.py` (CLI: `--model transformer --task regression_updn`)

- **Loss**: DirectionalAsymmetricLoss (динамически обрабатывает любое чётное число таргетов)
- **Optimizer**: AdamW
- **Early stopping**: на val Pearson r (среднее по всем таргетам, patience=10)
- **Scheduler**: ReduceLROnPlateau (patience=5, factor=0.5)

#### 6.3. Оптимальные параметры (Optuna)
```bash
python -m ML.train --model transformer --task regression_updn --epochs 100 \
  --lr 0.0022829 --batch_size 256 --seq_len 20 \
  --model_kwargs '{"d_model":32,"nhead":8,"num_layers":3,"dim_feedforward":128,"dropout":0.166}'
```

#### 6.4. Другие команды
```bash
# Сравнение 4 архитектур
python -m ML.compare_architectures --task regression_updn

# Optuna оптимизация
python -m ML.optimize --model transformer --task regression_updn --trials 50 --epochs 30

# Ablation: оптимальный seq_len
python -m ML.ablation_study --model transformer --task regression_updn
```

### Выход
- `ML/checkpoints/transformer_updn_best.pt`
- `ML/plots/training_curves_*.png`, `ML/reports/optuna_best_params_*.json`

---

## 📈 Этап 7: OOS Evaluation

### Вход
- `DATA/Nero_test_labeled.csv` (отложенная выборка, 15%)
- `ML/checkpoints/transformer_updn_best.pt`

### Текущие результаты (10-target модель, 2026-04-01)

**Pearson r по таргетам:**

| Таргет | r | MAE |
|--------|---|-----|
| up_3   | 0.799 | 0.046 |
| dn_3   | 0.794 | 0.048 |
| up_6   | 0.669 | 0.076 |
| dn_6   | 0.680 | 0.077 |
| up_12  | 0.539 | 0.115 |
| dn_12  | 0.560 | 0.118 |
| up_24  | 0.426 | 0.167 |
| dn_24  | 0.436 | 0.173 |
| up_48  | 0.354 | 0.221 |
| dn_48  | 0.369 | 0.219 |
| **среднее** | **0.5625** | |

**MT4 Strategy Tester** (OOS период, θ=2.665, horizon=12): **PF=1.18**, 584 сделки, просадка 12.66%

### Команды
```bash
python -m ML.evaluate_test --task regression_updn --model transformer
python -m ML.threshold_analysis --task regression_updn --horizon 12
python -m ML.experiment_logger --best pearson_r --task regression_updn
```

---

## 🔬 Этап 8: Статистическое исследование сигналов

> **Проводить перед любым изменением торговой логики EA.**

### Вход
- `MT/MQL4/Files/ml_signals.csv`
- `DATA/XAUUSD_H1_OHLC.csv` (126K баров OHLC + `atr14` для расчёта реального MFE/MAE и volatility splits)

### Процесс
**Модуль**: `API/signal_research.py`

Для каждого сигнала BUY/SELL вычисляет по реальным OHLC:
- **MFE** (Maximum Favorable Excursion): max(High) - Close за N баров в направлении сигнала
- **MAE** (Maximum Adverse Excursion): Close - min(Low) за N баров против сигнала
- **Net**: Close[t+N] - Close[t] в направлении сигнала

**Таблицы отчёта:**
1. MFE/MAE/PF по горизонтам (3H, 6H, 12H, 24H, 48H)
2. PF по бакетам силы сигнала (ratio 2-3, 3-4, 4-5, 5+)
3. Влияние фильтров up_3/dn_3 и up_6/dn_6 (с порогами)
4. Корреляция предсказаний модели с реальным MFE/MAE
5. Симуляция SL/TP комбинаций

### Ключевые находки (OOS, θ=2.665, 2603 сигнала)

**Нелинейность ratio:**
| ratio_12 | N | PF | Net |
|----------|---|----|-----|
| 2–3 | 635 | 1.26 | +1289 |
| 3–4 | 941 | **0.87** | **−1109** |
| 4–5 | 369 | **1.95** | +2367 |
| 5+  | 652 | 1.05 | +216 |

**Вывод**: θ=2.665 → ML_MinRatio=3.5 попадает в убыточный бакет 3–4. Рекомендуется ML_MinRatio=4.0.

**Лучший фиксированный SL/TP**: SL=5, TP=30 → PF=1.43 (лучше текущего адаптивного PF=1.18).

**Filter3/Filter6** как ratio-threshold: бесполезны — 96% сигналов уже имеют ratio_3 > 5.0.

```bash
python -m API.signal_research --test-only   # только OOS период
python -m API.signal_research               # весь датасет
```

---

## 🔄 Этап 9: Генерация ML-сигналов для MT4

### Вход
- `DATA/Nero_{train,validation,test}_labeled.csv`
- `ML/checkpoints/transformer_updn_best.pt`

### Процесс
**Модуль**: `API/generate_signals.py`

1. Загружает чекпоинт (seq_len читается из `model_kwargs`)
2. Прогоняет все три датасета через модель
3. Для каждой строки вычисляет сигнал по `ratio = up_12 / dn_12`:
   - `ratio > θ` → signal = **1** (BUY)
   - `1/ratio > θ` → signal = **-1** (SELL)
   - иначе → signal = **0** (FLAT)
4. Записывает все 10 предсказаний в CSV

```bash
python -m API.generate_signals                        # дефолт: θ=2.665, horizon=12
python -m API.generate_signals --theta 3.0 --horizon 24
```

### Выход — ml_signals.csv (v3.0)
```
time;signal;up_3;dn_3;up_6;dn_6;up_12;dn_12;up_24;dn_24;up_48;dn_48
2004.07.07 20:00;0;0.2041;0.0282;0.2573;0.0659;0.3215;0.1227;...
```
- ~58K строк, диапазон 2004–2026
- `ratio_up`/`ratio_dn` не хранятся — вычисляются в EA на лету из up_12/dn_12

### Интеграция с MT4 (lib_ML_Signal.mqh v3.0)

**EA параметры:**
```
ML_MinRatio     — порог ratio для входа (текущий: 3.5, рекомендуется 4.0)
ML_MaxRatio     — верхний порог (0=выкл)
ML_MaxRR        — макс R:R множитель (текущий: 4.0)
ML_ScaleK       — pred → ATR для SL (текущий: 20.0)
ML_Min_SL_ATR   — минимальный SL в ATR (текущий: 2.0)
ML_Filter3      — порог ratio_3 для фильтра (0=выкл)
ML_Filter6      — порог ratio_6 для фильтра (0=выкл)
```

**SL/TP логика:**
- BUY:  `sl = max(dn_12 × ScaleK × ATR, ATR × Min_SL_ATR)`, `tp = sl × CalcRR(ratio_12)`
- SELL: `sl = max(up_12 × ScaleK × ATR, ATR × Min_SL_ATR)`, `tp = sl × CalcRR(ratio_12)`

---

## 🎯 Этап 9b: Triple Barrier Training & Signals (параллельный трек)

### Отличия от regression_updn
- **Таргет**: 12 бинарных колонок (buy_sl2_tp3 … sell_sl3_tp9) вместо 10 непрерывных up/dn
- **Loss**: BCEWithLogitsLoss с pos_weight вместо DirectionalAsymmetricLoss
- **Метрика**: Mean AUC ROC вместо Pearson r
- **ВАЖНО**: Требует transfer learning — `--encoder_ckpt ML/checkpoints/transformer_updn_best.pt`. Обучение с нуля → AUC=0.5 (коллапс энкодера).
- **Статус**: Требует пересмотра подхода.

```bash
python -m ML.train --model transformer --task triple_barrier --epochs 100 \
  --encoder_ckpt ML/checkpoints/transformer_updn_best.pt \
  --model_kwargs '{"num_layers":3,"dropout":0.166,"input_features":20}'

python -m API.generate_signals --task triple_barrier --theta 0.6
```

### Выход
- `ML/checkpoints/transformer_tb_best.pt`
- `MT/MQL4/Files/ml_signals_tb.csv` — формат: `time;signal;sl_atr;tp_atr;prob;ev`
- MT4: `ML_TRADE_TB()` (iSignal=5)

---

## 🔍 Data Leakage Prevention

1. **Сортировка**: Независима по строкам
2. **Построчная нормализация**: Каждая строка нормализуется независимо
3. **Split последовательный**: Не случайный shuffle (сохраняем временной порядок)
4. **Маркировка до split**: Маркируем весь датасет, затем делим
5. **UPDN_FIELDS ≠ UPDN_TARGET_COLUMNS**: Короткие горизонты не включаются в пул p85 — только нормализуются теми же параметрами
6. **fractal_time** не подаётся как сырое абсолютное значение — только для вычисления hour_sin/hour_cos/time_pos
7. **seq_len берётся из чекпоинта** при инференсе — модель и данные всегда консистентны

---

## 🔍 Этап 10: Trade-Level Reconciliation (Диагностика)

### Проблема
Расхождение между ML OOS метриками и реальным MT4 бэктестом.

### Три режима диагностики

```bash
# Single-trace: разбор одного сигнала
python statistics/signal_tracer.py --time "2023.01.03 04:00"

# Batch: top-N высокорейтинговых сигналов
python statistics/signal_tracer.py --batch --top 10 --min-ratio 5.0 --csv-out batch.csv

# From-Log: разбор реальных сделок из MT4 логов
python statistics/signal_tracer.py --from-log MT/tester/logs/20260324.log --losses-only --csv-out losses.csv
```

### Документация
- [docs/statistics/signal_tracer.py.md](statistics/signal_tracer.py.md)

---

**Последнее обновление**: 2026-04-01
**Авторы**: Antigravity + AI agents
