# Выбор архитектуры нейронной сети — План этапов

## Контекст задачи

**Проект**: SoSimple — ML-бот для прогнозирования разворотов Forex (XAUUSD, H1).

**Данные**: Входной тензор X ∈ R^{32136×100×11} — последовательности из 100 фракталов, каждый с 11 признаками. Целевая переменная: `signal ∈ {-1, 0, 1}` (классификация) и `predict ∈ [-1, 1]` (регрессия).

**Ключевые характеристики датасета** (из EDA):

| Характеристика | Значение |
|---|---|
| Размер | 32 136 выборок |
| Длина последовательности | 100 фракталов |
| Признаков на фрактал | 11 (fractal_time, price, direction, front, back, strong, break, reverse, power, count, impulse) |
| Дисбаланс классов | -1: 12.4%, 0: 74.3%, 1: 13.3% |
| Пропуски в поздних позициях | до 73.6% на позиции 21+ |
| Ключевые признаки (Cohen's d > 0.6) | direction, impulse, front, reverse, back |
| Engineered features | 233 (из них 10 избыточных) |
| Топ engineered features | price_slope_2..5, price_zscore_w10, front_min_w1 |
| PCA (2 компоненты) | 46.5% дисперсии |
| t-SNE | Частичное разделение классов |

---

## Обзор этапов

Выбор архитектуры разбит на **3 этапа**:

1. **Этап 3.1** — Baseline-модели (простые, быстрые) для установки точки отсчёта
2. **Этап 3.2** — Сравнение архитектур нейронных сетей на полных последовательностях
3. **Этап 3.3** — Финальный выбор, фиксация гиперпараметров и документирование

> [!IMPORTANT]
> Нумерация этапов начинается с 3.x, так как этапы 1 (предобработка) и 2 (статистический анализ) уже завершены.

---

## Этап 3.1 — Baseline-модели

### Цель
Установить нижнюю границу качества с помощью простых моделей. Результаты baseline определят, есть ли предиктивный сигнал в данных и насколько сложная модель нужна.

### Промпт для AI-агента

---

> **Промпт: Этап 3.1 — Baseline-эксперименты**
> 
> Ты работаешь с проектом SoSimple. Прочитай AGENTS.md и .
>
> **Контекст**: Завершены этапы предобработки и EDA. Статистические результаты в [statistics/reports/EDA_report.md](../../statistics/reports/EDA_report.md), [statistics/plots/feature_stats_by_class.csv](../../statistics/plots/feature_stats_by_class.csv), [statistics/plots/statistical_tests.csv](../../statistics/plots/statistical_tests.csv). Рекомендации по моделированию — `statistics/sequence_analysis_report.md` (файл отсутствует в текущем репозитории). Описание формата данных и целевых переменных — [docs/dataset_description.md](../dataset_description.md). Поток данных — [docs/DATA_FLOW.md](../DATA_FLOW.md).
>
> **Задача**: Создать и обучить baseline-модели для задачи классификации `signal ∈ {-1, 0, 1}`. Код реализовать в `ML/baseline_experiments.py`.
>
> **Требования к данным**:
> 1. Загружать данные из [DATA/Nero_train_labeled.csv](../../DATA/Nero_train_labeled.csv) (train) и [DATA/Nero_validation_labeled.csv](../../DATA/Nero_validation_labeled.csv) (validation). Разделитель `;`. НЕ перемешивать данные (time-series!).
> 2. Парсинг фракталов: каждая строка содержит 100 фракталов в формате `fractal_time:price:direction:front:back:strong:break:reverse:power:count:impulse`. Разделитель фракталов `;`, разделитель признаков `:`.
> 3. Для feature-based моделей использовать уже готовые engineered features из EDA (файлы [statistics/nero_features_engineered.csv](../../statistics/nero_features_engineered.csv) и [statistics/feature_catalog.json](../../statistics/feature_catalog.json)) — но помни, что этот файл содержит только train split. Для validation применить ту же логику feature engineering.
> 4. Для sequence-based моделей парсить полный 3D тензор: X shape=(n_samples, 100, 11). Обработать пропуски (NaN) — заполнять нулями или masking.
>
> **Модели для сравнения**:
> 1. **Dummy classifier** (stratified) — чистый baseline
> 2. **Logistic Regression** — на flat features (fractal0, 11 признаков) + ATR + циклические временные
> 3. **Random Forest** — на тех же flat features
> 4. **XGBoost/LightGBM** — на полном наборе engineered features (233 признака без избыточных)
>
> **Балансировка классов** (обязательно!):
> - Для каждой модели попробовать `class_weight='balanced'` или эквивалент
> - Для XGBoost: `scale_pos_weight` или sample weights
>
> **Метрики** (НЕ использовать accuracy как основную!):
> - **Основная**: macro F1-score
> - **Дополнительные**: classification report (precision, recall, F1 по каждому классу), confusion matrix, ROC-AUC (OVR)
> - Вычислять на validation set
>
> **Формат результатов**:
> 1. Таблица сравнения моделей (markdown) с метриками
> 2. Сохранить confusion matrix для каждой модели в `ML/plots/`
> 3. Вывод: какой f1-score достигнут baseline-моделями, есть ли предиктивный сигнал
> 4. Создать отчёт `ML/reports/baseline_report.md`
>
> **Структура файлов**:
> ```
> ML/
> ├── baseline_experiments.py   # Основной скрипт
> ├── reports/
> │   └── baseline_report.md    # Отчёт с результатами
> └── plots/
>     └── baseline_*.png        # Confusion matrices
> ```

---

## Этап 3.2 — Сравнение архитектур нейронных сетей

### Цель
Сравнить несколько архитектур NN на полных последовательностях фракталов (3D тензор) и определить наиболее подходящую.

### Почему именно эти архитектуры

| Архитектура | Обоснование для данного датасета |
|---|---|
| **Bi-LSTM** | Последовательности фракталов имеют временной порядок и зависимости между позициями. LSTM лучше всего захватывает такие зависимости. Bidirectional — потому что информативны и свежие (pos 0), и старые фракталы |
| **1D-CNN** | Attention-анализ показал, что соседние фракталы дискриминативны. CNN эффективно захватывает *локальные* паттерны в последовательностях |
| **Transformer (encoder)** | Self-attention может обнаружить зависимости между произвольными позициями. Особенно полезно при наличии пропусков в поздних позициях |
| **Hybrid CNN+LSTM** | CNN → локальные паттерны, LSTM → глобальная динамика. Объединяет преимущества обоих подходов |

### Промпт для AI-агента

---

> **Промпт: Этап 3.2 — Сравнение архитектур нейронных сетей**
>
> Ты работаешь с проектом SoSimple. Прочитай AGENTS.md и .
>
> **Контекст**: Завершены этапы 1-2 (предобработка, EDA). Baseline-модели обучены (результаты в `ML/reports/baseline_report.md`). Описание данных: [docs/dataset_description.md](../dataset_description.md). Статистика: [statistics/reports/EDA_report.md](../../statistics/reports/EDA_report.md).
>
> **Задача**: Реализовать и сравнить 4 архитектуры нейронных сетей для классификации `signal ∈ {-1, 0, 1}` на последовательностях фракталов. Фреймворк: **PyTorch**. Код реализовать в `ML/`.
>
> **Архитектуры для сравнения**:
>
> 1. **Bi-LSTM**
>    - Input: (batch, seq_len=100, features=11)
>    - 2 слоя Bi-LSTM (hidden_size=64)
>    - Dropout 0.3 между слоями
>    - Pooling: concat(last_hidden_fwd, last_hidden_bwd)
>    - FC → 3 класса
>
> 2. **1D-CNN**
>    - Input: (batch, features=11, seq_len=100) — conv по оси времени
>    - 3 блока: Conv1D → BatchNorm → ReLU → MaxPool
>    - Каналы: 32 → 64 → 128, kernel_sizes: 5, 3, 3
>    - Global Average Pooling → FC → 3 класса
>
> 3. **Transformer Encoder**
>    - Input: (batch, seq_len=100, features=11) + positional encoding
>    - 2 encoder layers, d_model=64, nhead=4, feedforward=128
>    - CLS token или mean pooling → FC → 3 класса
>    - Mask для padding (NaN позиции)
>
> 4. **Hybrid CNN+LSTM**
>    - Conv1D block (32→64, kernel=5,3) → LSTM (hidden=64)
>    - Concat последних hidden states → FC → 3 класса
>
> **Требования к данным**:
> 1. Загружать [DATA/Nero_train_labeled.csv](../../DATA/Nero_train_labeled.csv) (train), [DATA/Nero_validation_labeled.csv](../../DATA/Nero_validation_labeled.csv) (val). Разделитель `;`.
> 2. Парсить фракталы в 3D тензор: shape=(n_samples, 100, 11). Фракталы разделены `;`, поля внутри фрактала разделены `:`. Формат: `fractal_time:price:direction:front:back:strong:break:reverse:power:count:impulse`.
> 3. ВАЖНО: исключить `fractal_time` (индекс 0) из входных features для модели — он уже учтён через порядок позиций и может дать data leakage. Итого features = 10 (price, direction, front, back, strong, break, reverse, power, count, impulse).
> 4. Обработка пропусков: заполнять NaN нулями + создать padding mask для Transformer.
> 5. Добавить ATR как дополнительный статический признак (broadcast на все позиции или concat к эмбеддингу).
>
> **Обучение** (одинаковые условия для всех моделей):
> - Loss: **Focal Loss** (gamma=2) или CrossEntropy с `class_weight` (рассчитать inverse frequency)
> - Optimizer: AdamW, lr=1e-3, weight_decay=1e-4
> - Scheduler: ReduceLROnPlateau (patience=5, factor=0.5)
> - Epochs: до 50, early stopping на val loss (patience=10)
> - Batch size: 128
> - НЕ перемешивать данные случайно (time-series!). Допустимо перемешивать внутри эпохи, т.к. каждая строка — независимый snapshot.
>
> **Метрики** (вычислять после каждой эпохи на validation):
> - macro F1-score (основная)
> - Per-class F1 (особенно для классов -1 и 1)
> - Confusion matrix (сохранить best epoch)
> - Training curves: loss и F1 по эпохам
>
> **Формат результатов**:
> 1. Таблица сравнения 4 архитектур: val macro F1, per-class F1, #parameters, время обучения
> 2. Training curves для каждой модели (plots)
> 3. Confusion matrix для best epoch каждой модели
> 4. Сохранить веса лучшей модели: `ML/checkpoints/best_model.pt`
> 5. Создать отчёт `ML/reports/architecture_comparison.md`
>
> **Структура кода**:
> ```
> ML/
> ├── data_loader.py            # Dataset и DataLoader для фрактальных последовательностей
> ├── models/
> │   ├── __init__.py
> │   ├── bilstm.py             # Bi-LSTM модель
> │   ├── cnn1d.py              # 1D-CNN модель
> │   ├── transformer.py        # Transformer Encoder
> │   └── hybrid_cnn_lstm.py    # Hybrid CNN+LSTM
> ├── train.py                  # Единый скрипт обучения (принимает --model arg)
> ├── losses.py                 # FocalLoss и утилиты
> ├── compare_architectures.py  # Скрипт сравнения всех моделей
> ├── reports/
> │   └── architecture_comparison.md
> ├── checkpoints/
> └── plots/
>     └── training_curves_*.png
> ```
>
> **Важно**:
> - Все модели должны иметь единый интерфейс: `forward(x, mask=None)` → logits (batch, 3)
> - Фиксировать random seed (42) для воспроизводимости
> - Логировать в stdout: epoch, train_loss, val_loss, val_f1
> - При обучении использовать GPU если доступен, иначе CPU

---

## Этап 3.3 — Финальный выбор и конфигурация

### Цель
На основе результатов этапов 3.1 и 3.2 выбрать финальную архитектуру, провести анализ ошибок и зафиксировать конфигурацию для дальнейшего обучения.

### Промпт для AI-агента

---

> **Промпт: Этап 3.3 — Финальный выбор архитектуры и анализ ошибок**
>
> Ты работаешь с проектом SoSimple. Прочитай AGENTS.md и .
>
> **Контекст**: Завершены baseline эксперименты (`ML/reports/baseline_report.md`) и сравнение архитектур NN (`ML/reports/architecture_comparison.md`).
>
> **Задача**: Провести анализ ошибок лучшей модели, зафиксировать финальную архитектуру и подготовить конфигурацию для полноценного обучения. Результат — документ `ML/reports/architecture_decision.md`.
>
> **Шаги**:
>
> 1. **Анализ ошибок (Error Analysis)**:
>    - Загрузить лучшую модель из `ML/checkpoints/best_model.pt`
>    - Прогнать prediction на validation set
>    - Для каждого класса найти примеры:
>      - True Positives (правильно предсказанные)
>      - False Positives (ложные сигналы)
>      - False Negatives (пропущенные сигналы)
>    - Проанализировать: есть ли паттерн в ошибках? Связано ли с волатильностью (ATR), временем, определёнными признаками?
>    - Сохранить визуализацию ошибок в `ML/plots/error_analysis_*.png`
>
> 2. **Ablation Study** (если позволяет время):
>    - Влияние длины последовательности: обучить лучшую модель на seq_len=20, 50, 100
>    - Влияние отдельных групп признаков (убрать морфологические / топологические)
>    - Таблица с результатами
>
> 3. **Фиксация архитектуры**:
>    - Написать `ML/reports/architecture_decision.md`:
>      - Выбранная архитектура и почему
>      - Сравнение с baseline (прирост F1)
>      - Сравнение с другими NN архитектурами
>      - Финальная конфигурация (гиперпараметры, loss, optimizer)
>      - Известные ограничения и слабые стороны
>      - Рекомендации для фазы полноценного обучения (Этап 4)
>
> 4. **Обновить документацию проекта**:
>    - Обновить [AGENTS.md](../../AGENTS.md): секцию "Статус разработки" — отметить "Выбор архитектуры ✅"
>    - Обновить [docs/PRD.md](../PRD.md): roadmap — отметить "Выбор архитектуры" как выполненный
>    - Обновить `CHANGELOG.md`
>
> **Формат `architecture_decision.md`**:
> ```markdown
> # Architecture Decision Record
> 
> ## Резюме
> [Какая архитектура выбрана и ключевые цифры]
> 
> ## Сравнение с baseline
> [Таблица: Baseline vs NN]
> 
> ## Сравнение NN архитектур
> [Таблица из этапа 3.2]
> 
> ## Анализ ошибок
> [Паттерны в ошибках, проблемные случаи]
> 
> ## Финальная конфигурация
> [Полная спецификация модели для обучения]
> 
> ## Рекомендации для Этапа 4 (Полное обучение)
> [План для следующего шага]
> ```

---

## Общие принципы для всех этапов

> [!WARNING]
> **Data Leakage Prevention**: Данные уже разделены на train/val/test по времени (последовательно, без shuffle). Использовать только `train` для обучения и `validation` для оценки. `test` — только для финального бэктеста (Этап 5, не сейчас!).

> [!IMPORTANT]
> **Дисбаланс классов**: Класс 0 (74.3%) доминирующий. Без балансировки модель будет предсказывать «всё = 0». Обязательно использовать class weights или Focal Loss.

### Что НЕ делать на этих этапах
- ❌ Не оптимизировать гиперпараметры (это Фаза 3 по PRD — Optuna/Ray Tune)
- ❌ Не запускать на test set (только на validation)
- ❌ Не усложнять модели (цель — выбор базовой архитектуры, а не финальное качество)
- ❌ Не делать ensemble (это тоже Фаза 3)
