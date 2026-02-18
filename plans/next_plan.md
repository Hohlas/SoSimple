Ты работаешь с проектом SoSimple. Прочитай AGENTS.md и .ai/RULES_INDEX.md

**Контекст**: Завершены этапы 1-2 (предобработка, EDA). Baseline-модели обучены (результаты в `ML/reports/baseline_report.md`).

Описание данных: docs/dataset_description.md.
Статистика: statistics/reports/EDA_report.md
statistics/plots/feature_stats_by_class.csv
statistics/plots/statistical_tests.csv

**Задача**: Реализовать и сравнить 4 архитектуры нейронных сетей для классификации `signal ∈ {-1, 0, 1}` на последовательностях фракталов. Фреймворк: **PyTorch**. Код реализовать в `ML/`.
>
> **Архитектуры для сравнения**:
>
> 1. **Bi-LSTM**
>    - Input: (batch, seq_len=100, features=11) — 10 фрактальных + ATR
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
> 1. Загружать DATA/Nero_train_labeled.csv (train), DATA/Nero_validation_labeled.csv (val). CSV-столбцы разделены `;`. Каждый столбец fractalN (N=0..99) содержит строку с полями через `:`.
> 2. Парсить фракталы в 3D тензор: shape=(n_samples, 100, 11). Формат полей фрактала: `fractal_time:price:direction:front:back:strong:break:reverse:power:count:impulse`.
> 3. ВАЖНО: исключить `fractal_time` (индекс 0) из входных features для модели — он уже учтён через порядок позиций и может дать data leakage. Итого 10 фрактальных features: price, direction, front, back, strong, break, reverse, power, count, impulse.
> 4. Добавить ATR как 11-й признак (broadcast на все 100 позиций). Итого features = **11** (10 фрактальных + 1 ATR).
> 5. Обработка пропусков: заполнять NaN нулями + создать padding mask для Transformer.
> 6. **Нормализация features** (обязательно для нейросетей): применить StandardScaler — fit на train, transform на val. Разные масштабы признаков: price ~1.0, front/back/impulse ~0.001-0.01, power/count — целые числа. Нормализовать по каждому feature индексу отдельно по всему train (shape flatten: n_samples*100, n_features).
>

> ⚠️ **Не запускать обучение!** Только написать код, проверить 
> синтаксис и корректность импортов. Обучение будет запущено отдельно.
>
> **Параметры обучения** (реализовать в train.py):
> - Loss: **Focal Loss** (gamma=2, alpha=[0.45, 0.10, 0.45]) — обязательно. При дисбалансе 95%/2.5%/2.5% обычный CrossEntropy с class_weight недостаточен (baseline показал recall minority 1-12%).
> - Optimizer: AdamW, lr=1e-3, weight_decay=1e-4
> - Scheduler: ReduceLROnPlateau (patience=5, factor=0.5, monitor='val_f1_macro')
> - Epochs: до 50, **early stopping на val macro F1** (patience=10). НЕ на val loss — при 95% дисбалансе loss может улучшаться за счёт majority-класса, пока F1 minority падает.
> - Batch size: 256 (при 43K сэмплах и маленьких моделях 256-512 оптимальнее, чем 128)
> - Train DataLoader: shuffle=True (каждая строка — независимый snapshot, перемешивание допустимо). Validation DataLoader: shuffle=False.
> - **Воспроизводимость**: установить seed для PyTorch, NumPy, random: `torch.manual_seed(42)`, `torch.backends.cudnn.deterministic = True`, `np.random.seed(42)`.
>
> **Метрики** (вычислять после каждой эпохи на validation):
> - macro F1-score (основная, решающая для early stopping и выбора лучшей модели)
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
> ├── losses.py                 # FocalLoss
> ├── utils.py                  # Metrics, нормализация, seed-setting, общие утилиты
> ├── compare_architectures.py  # Скрипт сравнения всех моделей
> ├── reports/
> │   └── architecture_comparison.md
> ├── checkpoints/
> └── plots/
>     └── training_curves_*.png
> ```
