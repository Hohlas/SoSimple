# 1: Exploratory Data Analysis & Feature Engineering

КОНТЕКСТ:
Ты — специалист по анализу финансовых временных рядов. Тебе предоставлен датасет для прогнозирования разворотов тренда на рынке Forex (H1 таймфрейм).

СТРУКТУРА ДАННЫХ:
- CSV файл формата: human_time ; signal ; fractal[0] ; fractal[1] ; ... ; fractal[98]
- Каждый фрактал: fractal_time:price:direction:front:back:strong:break:reverse:power:count:impulse
- Размерность входа: X ∈ R^{k×99×11}, где k > 5000 строк
- Целевая переменная: y ∈ {-1, 0, 1}^k, экстремально несбалансирована (99.24% класс 0, 0.42% класс -1, 0.34% класс 1)

ТВОЯ ЗАДАЧА:
1. EDA (Exploratory Data Analysis):
   - Проанализируй распределения всех 11 признаков отдельно для классов {-1, 0, 1}
   - Выяви статистически значимые различия между классами (t-test, Mann-Whitney U-test)
   - Построй корреляционные матрицы признаков для fractal[0] (текущий фрактал) по классам
   - Исследуй временные паттерны: есть ли сезонность, тренды, кластеризация событий signal≠0 во времени?
   - Проверь наличие выбросов и аномалий в признаках

2. Feature Engineering:
   - Создай агрегированные признаки из последовательности 99 фракталов:
     * Статистики скользящих окон (mean, std, min, max) для окон 3, 5, 10, 20, 50 последних фракталов
     * Трендовые индикаторы: линейная регрессия slope для price, power, impulse за последние N фракталов
     * Паттерны direction: количество смен направления, longest streak одного направления
     * Interaction features: front*back, power*impulse, count*reverse
   - Создай признаки относительных изменений:
     * Δprice, Δpower, Δimpulse между текущим и предыдущими фракталами
     * Относительная позиция текущего фрактала: (price - min_price) / (max_price - min_price) за окно N
   - Извлеки временные признаки из fractal_time:
     * Hour of day, day of week (цикличная кодировка через sin/cos)
     * Time since previous fractal (Δt между фракталами)
   - Учти доменную специфику:
     * Признаки support/resistance: сколько фракталов в окне имеют близкие значения price (±threshold)
     * Momentum indicators: cumulative sum direction, rate of change
     * Volatility proxy: rolling std(price)

3. Data Quality Checks:
   - Проверь на data leakage: убедись, что эволюционирующие признаки (back, break, strong, power, count, reverse) не содержат forward-looking информацию в момент t_i для fractal[i][0]
   - Проанализируй missing values, infinity, NaN
   - Валидируй causal consistency: для одного и того же физического фрактала, появляющегося в строках i и h (h>i), признаки должны эволюционировать согласованно

4. Визуализация:
   - t-SNE или UMAP проекция признаков fractal[0] с раскраской по классам
   - Boxplots ключевых признаков по классам
   - Временные графики появления signal≠0 для выявления кластеризации

5. Рекомендации:
   - Какие признаки наиболее дискриминативны для разделения классов?
   - Нужна ли дополнительная нормализация/стандартизация?
   - Предложи, какие ценовые метрики из исторических данных стоит добавить (ATR, RSI, MACD, Bollinger Bands)

ВЫХОДНОЙ ФОРМАТ:
- Jupyter notebook с кодом и визуализациями
- Markdown отчет с выводами и рекомендациями
- CSV файл с новыми признаками (feature_engineered.csv)
- Список топ-20 признаков по важности (feature_ranking.csv)

ИНСТРУМЕНТЫ: Python, pandas, numpy, scipy, matplotlib, seaborn, sklearn

# 2: Data Preprocessing & Splitting Strategy

КОНТЕКСТ:
Ты — ML-инженер, специализирующийся на временных рядах в финансах. Задача — подготовить данные для обучения модели прогнозирования разворотов тренда.

ВХОДНЫЕ ДАННЫЕ:
- Оригинальный CSV: Nero.csv (k×99×11 фрактальных признаков)
- Engineered features: feature_engineered.csv (результат Этапа 1)
- Экстремальный дисбаланс: 99.24% класс 0, 0.76% классы {-1, 1}

ТВОЯ ЗАДАЧА:

1. Нормализация и Масштабирование:
   - Примени RobustScaler или MinMaxScaler к численным признакам (устойчивы к выбросам)
   - Для temporal features (fractal_time): преобразуй в относительное время (секунды с начала датасета)
   - Для циклических признаков (hour, day_of_week): используй sin/cos кодировку
   - ВАЖНО: fit scaler только на train set, затем transform на val/test

2. Temporal Split стратегия:
   - НЕ используй random shuffle (нарушение temporal causality!)
   - Используй temporal walk-forward split:
     * Train: первые 60% данных по времени
     * Validation: следующие 20% данных по времени  
     * Test: последние 20% данных по времени
   - Альтернатива: expanding window cross-validation для более robust оценки
     * Например, 5 фолдов с incrementing train window

3. Обработка дисбаланса классов:
   - Baseline: сохрани оригинальное распределение для realistic evaluation
   - Для обучения рассмотри несколько стратегий (создай отдельные датасеты для экспериментов):
     
     a) Class Weighting: вычисли weights = n_samples / (n_classes * class_counts)
        - weight_0 ≈ 0.20, weight_1 ≈ 147, weight_-1 ≈ 119
     
     b) SMOTE (Synthetic Minority Over-sampling):
        - Примени SMOTE только к train set для увеличения классов {-1, 1}
        - Попробуй borderline-SMOTE и ADASYN варианты
        - КРИТИЧНО: SMOTE применяется ПОСЛЕ temporal split
     
     c) Undersampling мажоритарного класса:
        - Random undersampling класса 0
        - Tomek Links или ENN (Edited Nearest Neighbors) для очистки границ
        - Hybrid: комбинация SMOTE + undersampling
     
     d) Focal Loss подход (обработка на уровне функции потерь, без изменения датасета)

4. Создание Temporal Sequences (для RNN/Transformer):
   - Каждая строка уже содержит последовательность 99 фракталов — это идеально для sequence models
   - Структура входа для PyTorch/TensorFlow: (batch_size, seq_len=99, n_features=11+n_engineered)
   - Создай PyTorch Dataset/DataLoader с правильным batching
   - Padding: если разрешишь переменную длину последовательности (dynamic n), примени padding + mask

5. Validation Strategy для imbalanced data:
   - Stratified split невозможен (temporal constraint), но отслеживай распределение классов в каждом сплите
   - Убедись, что в val/test есть достаточно примеров классов {-1, 1} для reliable metrics

6. Data Augmentation (опционально):
   - Time-series specific augmentation: jittering, scaling, magnitude warping, time warping
   - Применяй только к minority classes {-1, 1}
   - Validate: augmentation не должна нарушать финансовую логику

7. Artifacts для следующих этапов:
   - Сохрани preprocessed датасеты: X_train.npy, y_train.npy, X_val.npy, y_val.npy, X_test.npy, y_test.npy
   - Сохрани fitted scalers: scaler.pkl
   - Сохрани class weights: class_weights.json
   - Сохрани индексы сплитов: train_indices.npy, val_indices.npy, test_indices.npy (для reproducibility)
   - Создай summary: preprocessing_report.md с распределением классов в каждом сплите

ВЫХОДНОЙ ФОРМАТ:
- preprocessing_pipeline.py (reusable script)
- Preprocessed datasets (.npy или .pt файлы)
- preprocessing_report.md с описанием всех трансформаций
- config.yaml с гиперпараметрами preprocessing

ИНСТРУМЕНТЫ: pandas, numpy, scikit-learn, imbalanced-learn, PyTorch/TensorFlow

# 3: Model Architecture Design & Selection

КОНТЕКСТ:
Ты — архитектор нейронных сетей, специализирующийся на deep learning для финансовых временных рядов. Задача — спроектировать и реализовать несколько архитектур для прогнозирования разворотов тренда.

ЗАДАЧА SPECIFICATION:
- Input: X ∈ R^{batch×99×n_features}, где 99 — длина последовательности фракталов
- Output: y ∈ {-1, 0, 1} (3-class classification) или 2 binary classifiers для signal=1 и signal=-1 отдельно
- Metric priority: Precision (минимизация ложных сигналов), но с мониторингом Recall и F1
- Constraints: нет latency требований (H1 таймфрейм), GPU доступен

ТВОЯ ЗАДАЧА:

1. Спроектируй 4-5 baseline архитектур:

   a) LSTM-based Architecture:
      ```
      - Bidirectional LSTM (hidden_size=128, num_layers=2)
      - Dropout(0.3) после каждого LSTM слоя
      - Attention mechanism над LSTM outputs (для фокуса на значимых фракталах)
      - Fully connected: hidden_size*2 → 64 → n_classes
      - Output: softmax (3-class) или sigmoid (binary per direction)
      ```
   
   b) Transformer-based Architecture (state-of-art для временных рядов):
      ```
      - Positional encoding для последовательности из 99 фракталов
      - Multi-head Self-Attention (n_heads=8, d_model=128)
      - Feed-forward network с residual connections
      - Num transformer blocks: 3-4
      - Classification head: [CLS] token или pooling последнего hidden state
      - Учти: Transformer'ы эффективны для обнаружения паттернов разворота тренда (см. momentum transformer research)
      ```
   
   c) CNN + LSTM Hybrid:
      ```
      - 1D CNN для извлечения локальных паттернов из фракталов:
        Conv1D(filters=64, kernel_size=3) → ReLU → MaxPool
        Conv1D(filters=128, kernel_size=3) → ReLU → MaxPool
      - LSTM для temporal dependencies в CNN features
      - Global Max Pooling + Dense layers
      ```
   
   d) Temporal Convolutional Network (TCN):
      ```
      - Dilated causal convolutions (dilation rates: 1, 2, 4, 8, ...)
      - Residual blocks
      - Преимущество: параллелизуемость, меньше vanishing gradient vs LSTM
      ```
   
   e) Ensemble / Hybrid подход:
      ```
      - Два отдельных binary classifiers:
        * Model_BUY: предсказывает P(signal=-1 | x)
        * Model_SELL: предсказывает P(signal=1 | x)
      - Архитектура каждого: LSTM или Transformer
      - Преимущество: каждая модель специализируется на своем направлении
      ```

2. Имплементация деталей:

   - Framework: PyTorch (более гибкий для research) или TensorFlow/Keras
   - Модули:
     * Self-Attention layer (если Transformer)
     * Positional Encoding
     * Custom classification head с configurable output (3-class vs binary)
   
   - Regularization:
     * Dropout: 0.2-0.4
     * Weight decay (L2): 1e-4
     * Gradient clipping: max_norm=1.0 (против exploding gradients)
     * Early stopping: patience=15-20 epochs
   
   - Initialization:
     * Xavier/Glorot для Linear layers
     * Orthogonal для RNN weights

3. Loss Function Design (критично для imbalanced data):

   a) Weighted Cross-Entropy:
      - Используй class weights из Этапа 2
      - PyTorch: nn.CrossEntropyLoss(weight=class_weights_tensor)
   
   b) Focal Loss (рекомендуется для extreme imbalance):
      ```python
      FL(p_t) = -α_t * (1 - p_t)^γ * log(p_t)
      где γ=2 (focus на hard examples), α_t — class weights
      ```
   
   c) Class-Balanced Loss (CB Loss):
      - Учитывает effective number of samples
      - Более robust к extreme imbalance vs простые weights
   
   d) Для binary approach: Binary Cross-Entropy с pos_weight

4. Multi-Task Learning (опционально):
   - Auxiliary tasks:
     * Предсказание direction следующего фрактала
     * Регрессия на power или impulse
   - Помогает модели учить более robust representations

5. Implementation Requirements:
   - Код должен быть модульным: separate файлы для models/, losses/, utils/
   - Configurable через config файл (YAML или Hydra)
   - Support для model checkpointing
   - Logging: TensorBoard или Weights & Biases

6. Baseline Experiments Setup:
   - Определи experiment matrix:
     * Architecture: [LSTM, Transformer, CNN-LSTM, TCN]
     * Loss: [WeightedCE, FocalLoss, CB-Loss]
     * Sampling: [Original, SMOTE, Undersampling]
   - Минимум 12 экспериментов (4 arch × 3 loss combinations)

ВЫХОДНОЙ ФОРМАТ:
- models/lstm.py, models/transformer.py, models/cnn_lstm.py, models/tcn.py
- losses/focal_loss.py, losses/class_balanced_loss.py
- config/model_configs.yaml
- train.py (training loop script)
- Архитектурная диаграмма (draw.io или PlantUML)
- README_models.md с описанием каждой архитектуры и обоснованием выбора

REFERENCE:
- Momentum Transformer for changepoint detection in trading
- Cost-sensitive hybrid networks для imbalanced time series
- LSTM для forex prediction с temporal dependencies

ИНСТРУМЕНТЫ: PyTorch, transformers library, timm, pytorch-lightning (опционально)

# 4: Training, Hyperparameter Tuning & Evaluation

КОНТЕКСТ:
Ты — ML-инженер, специализирующийся на обучении моделей для финансовых временных рядов. Задача — обучить модели из Этапа 3, провести hyperparameter tuning и комплексную оценку.

ВХОДНЫЕ ДАННЫЕ:
- Preprocessed datasets: X_train, y_train, X_val, y_val, X_test, y_test
- Model architectures: LSTM, Transformer, CNN-LSTM, TCN
- Loss functions: WeightedCE, FocalLoss, CB-Loss

ТВОЯ ЗАДАЧА:

1. Training Setup:

   a) Optimizer:
      - AdamW (weight decay=1e-4) — рекомендуется для Transformers
      - Learning rate: 1e-3 (initial) с warm-up и decay
      - Альтернативы: Adam, SGD with momentum
   
   b) Learning Rate Scheduler:
      - ReduceLROnPlateau (mode='max', factor=0.5, patience=5, monitor=val_precision)
      - Или Cosine Annealing with Warm Restarts
      - Warm-up: первые 5-10 epochs линейный рост LR от 1e-5 до 1e-3
   
   c) Training Loop:
      - Batch size: 32-64 (adjust based on GPU memory)
      - Epochs: 100-150 с early stopping (patience=20, monitor=val_precision или val_f1_weighted)
      - Gradient accumulation: если batch size ограничен
      - Mixed precision training (FP16) для ускорения на GPU
   
   d) Monitoring:
      - TensorBoard logging: loss, precision, recall, F1 (per class и weighted)
      - Checkpoint: сохраняй best model по val_precision
      - Log каждые N батчей: loss, grad_norm

2. Hyperparameter Tuning:

   a) Search Space (для каждой архитектуры):
      - LSTM: hidden_size [64, 128, 256], num_layers [1, 2, 3], dropout [0.2, 0.3, 0.4]
      - Transformer: d_model [64, 128, 256], n_heads [4, 8], num_blocks [2, 3, 4], dropout [0.1, 0.2, 0.3]
      - Learning rate [1e-4, 5e-4, 1e-3, 5e-3]
      - Focal Loss γ [0.5, 1.0, 2.0, 3.0]
      - Class weights: manual tuning или auto (n_samples / (n_classes * class_counts))
   
   b) Tuning Strategy:
      - Random Search (быстрее) или Bayesian Optimization (Optuna, Ray Tune)
      - Budget: 50-100 trials
      - Metric: maximize val_precision или val_f1_weighted (в зависимости от business requirement)
      - Early stopping per trial: если val loss не улучшается 10 epochs, прервать trial
   
   c) Multi-Objective Optimization:
      - Оптимизируй Pareto frontier: (Precision, Recall, F1)
      - Используй weighted score: α*Precision + β*Recall + γ*F1
      - Приоритет: α=0.6, β=0.2, γ=0.2 (precision-focused для минимизации ложных сигналов)

3. Evaluation Metrics (критично для imbalanced 3-class):

   a) Classification Metrics (per class и macro/weighted avg):
      - Precision, Recall, F1-score
      - Confusion Matrix (3×3 для классов {-1, 0, 1})
      - Matthews Correlation Coefficient (MCC) — robust к imbalance
   
   b) Precision-Recall Curve:
      - Для каждого класса: PR curve и Average Precision (AP)
      - Macro-Average Precision (mAP)
   
   c) ROC-AUC (если используешь probabilistic outputs):
      - Micro-average и macro-average ROC-AUC
      - Но помни: ROC может быть misleading для extreme imbalance
   
   d) Business Metrics (domain-specific):
      - True Positive Rate для signal≠0 (catch rate для торговых сигналов)
      - False Positive Rate для signal=0 (сколько ложных входов в рынок?)
      - Cost-sensitive metric: assign costs к FP и FN (e.g., FP_cost=10, FN_cost=1)
   
   e) Calibration:
      - Reliability diagram (calibration curve)
      - Expected Calibration Error (ECE)
      - Важно для probabilistic trading decisions

4. Cross-Validation (если применимо):
   - Time-series CV: expanding window или sliding window
   - 5-fold temporal CV для более robust оценки generalization
   - Aggregate metrics: mean ± std across folds

5. Test Set Evaluation (final step):
   - После выбора best model по validation, evaluate на test set
   - Отчет:
     * Confusion matrix
     * Classification report (precision/recall/F1 per class)
     * PR curves и ROC curves
     * Business metrics: сколько profitable trades vs unprofitable?
     * Calibration plot
   
   - Error Analysis:
     * Какие примеры модель ошибочно классифицирует?
     * Visualize несколько FP и FN случаев: что общего в паттернах фракталов?
     * Есть ли systematic errors? (e.g., хуже в определенное время суток, при высокой volatility)

6. Model Interpretability (опционально, но полезно):
   - SHAP values для feature importance
   - Attention weights visualization (для Transformer/LSTM+Attention)
   - Какие фракталы в последовательности наиболее важны для предсказания?
   - Gradient-based saliency maps

7. Model Selection:
   - Сравни все модели по val/test metrics
   - Выбери топ-3 модели
   - Рассмотри ensemble этих топ-3 (voting или stacking)

ВЫХОДНОЙ ФОРМАТ:
- train_results/ directory:
  * best_model.pth (checkpoint лучшей модели)
  * training_curves.png (loss, precision, recall vs epochs)
  * hyperparameter_tuning_results.csv
- evaluation_report.md:
  * Сравнительная таблица всех моделей
  * Confusion matrices
  * PR curves
  * Рекомендации: какую модель использовать в продакшене
- tensorboard_logs/ или wandb logs
- error_analysis.ipynb (Jupyter notebook с анализом ошибок)

ИНСТРУМЕНТЫ: PyTorch, Optuna/Ray Tune, scikit-learn metrics, matplotlib, seaborn, SHAP

# 5: Model Ensemble & Post-Processing Strategies

КОНТЕКСТ:
Ты — специалист по ensemble learning и post-processing для финансовых моделей. Задача — улучшить финальные предсказания через ensemble и post-hoc оптимизацию.

ВХОДНЫЕ ДАННЫЕ:
- Топ-3 обученные модели из Этапа 4 (e.g., Transformer, LSTM, CNN-LSTM)
- Validation и test predictions от каждой модели
- Business requirement: максимизировать Precision при приемлемом Recall

ТВОЯ ЗАДАЧА:

1. Ensemble Strategies:

   a) Voting Ensemble:
      - Hard voting: majority vote по классам {-1, 0, 1}
      - Soft voting: усреднение predicted probabilities, затем argmax
      - Weighted voting: assign weights к моделям по их val_precision
   
   b) Stacking Ensemble:
      - Meta-learner: Logistic Regression или LightGBM
      - Features: predicted probabilities от base models (3 models × 3 classes = 9 features)
      - Train meta-learner на validation set
      - Evaluate на test set
   
   c) Blending:
      - Подобно stacking, но проще: linear combination of predictions
      - Optimize weights через grid search на validation set
   
   d) Conditional Ensemble (domain-specific):
      - Используй разные модели для разных market regimes
      - Например: LSTM для trending markets, Transformer для reverting markets
      - Regime detection: по volatility (ATR), momentum indicators

2. Threshold Optimization (критично для precision):

   a) Для 3-class classification:
      - Вместо простого argmax(probabilities), используй custom thresholds
      - Если max(P(signal=-1), P(signal=1)) < threshold, предсказывай signal=0
      - Tuning: sweep threshold от 0.3 до 0.9, выбери по max precision на validation
   
   b) Для binary approach (2 отдельные модели):
      - Каждая модель (BUY, SELL) имеет свой threshold
      - Оптимизируй thresholds независимо
      - Правило: если оба model scores < thresholds, output signal=0
   
   c) Precision-Recall Operating Point:
      - Построй PR curve на validation set
      - Выбери operating point: (precision=X, recall=Y), где X максимально при Y > min_acceptable_recall
      - Пример: precision=0.7 при recall≥0.4

3. Calibration (для probabilistic outputs):
   - Platt Scaling (Logistic Regression on logits)
   - Isotonic Regression (non-parametric, more flexible)
   - Temperature Scaling (для neural networks)
   - Цель: улучшить reliability predicted probabilities для risk management

4. Post-Processing Rules (domain logic):

   a) Temporal Smoothing:
      - Если модель предсказывает signal≠0, требуй confirmation в следующих N фракталах
      - Избегай rapidly switching signals (whipsaws)
   
   b) Confidence Gating:
      - Генерируй сигнал только если P(signal) > high_confidence_threshold
      - Для trading: лучше пропустить сомнительные сделки, чем войти с FP
   
   c) Risk-based Filtering:
      - Интегрируй volatility (ATR): не входи в рынок если ATR > threshold (high risk)
      - Momentum check: подтверди signal=-1 с bearish momentum, signal=1 с bullish momentum
   
   d) Multi-Timeframe Confirmation (если есть данные):
      - Проверь согласованность с более высоким timeframe (e.g., H4, D1)

5. Performance Optimization:
   - Model Quantization (FP32 → FP16 или INT8) для faster inference
   - ONNX export для deployment efficiency
   - Batch inference optimization (если real-time не критично)

6. Backtesting на историческом периоде:
   - Simulate trading с финальными predictions
   - Metrics:
     * Total return, Sharpe ratio, Max drawdown
     * Win rate, average win/loss, profit factor
     * Number of trades (не слишком много или мало?)
   - Сравни с baseline: buy-and-hold, simple momentum strategy

7. Uncertainty Quantification:
   - Monte Carlo Dropout: несколько forward passes с dropout enabled
   - Ensemble uncertainty: variance в predictions между models
   - Flagging: помечай predictions с high uncertainty для manual review

ВЫХОДНОЙ ФОРМАТ:
- ensemble_model.py (код ensemble inference)
- threshold_optimization_results.json
- backtest_report.md:
  * Trading performance metrics
  * Equity curve
  * Drawdown analysis
- final_model_card.md:
  * Архитектура выбранной модели/ensemble
  * Precision, Recall, F1 на test set
  * Recommended thresholds
  * Limitations и risks
- deployment_package/:
  * Serialized model (.pth, .onnx)
  * Preprocessing pipeline (scaler, transforms)
  * Inference script (inference.py)
  * Config file (deployment_config.yaml)

ИНСТРУМЕНТЫ: scikit-learn, xgboost/lightgbm, backtesting.py, PyTorch, ONNX

# 6: Deployment, Monitoring & Continuous Improvement

КОНТЕКСТ:
Ты — MLOps инженер для автоматической торговой системы на Forex. Задача — развернуть обученную модель, настроить monitoring и процессы для continuous improvement.

ВХОДНЫЕ ДАННЫЕ:
- Финальная модель (ensemble или single best model)
- Preprocessing pipeline
- Inference script
- Test set performance benchmarks

ТВОЯ ЗАДАЧА:

1. Deployment Architecture:

   a) System Components:
      ```
      Market Data Stream → Fractal Detector → Feature Engineering → 
      Preprocessing → Model Inference → Post-Processing → Trading Signal → 
      Execution Engine
      ```
   
   b) Model Serving:
      - Option 1: Local inference в торговой системе (Python script)
      - Option 2: Model server (Flask API, FastAPI, TorchServe)
      - Option 3: Cloud deployment (AWS SageMaker, GCP Vertex AI)
      - Latency: на H1 timeframe latency не критична (<1 sec приемлемо)
   
   c) Input Pipeline:
      - Realtive streaming: при появлении нового фрактала trigger inference
      - Buffering: maintain последние 99 фракталов в памяти
      - Feature computation: apply engineering transforms в real-time
      - Preprocessing: apply fitted scaler

2. Inference Workflow:
   ```python
   def predict(fractal_sequence):  # shape: (99, 11)
       # 1. Feature engineering
       features = feature_engineer(fractal_sequence)
       
       # 2. Preprocessing
       features_scaled = scaler.transform(features)
       
       # 3. Model inference
       logits = model(features_scaled)
       probs = softmax(logits)
       
       # 4. Threshold application
       if max(probs) < confidence_threshold:
           return signal=0
       
       # 5. Post-processing rules
       signal = apply_domain_rules(probs, market_context)
       
       return signal, probs
    ```

3. Model Monitoring (критично для production):

a) Performance Monitoring:

- Precision, Recall, F1 на live predictions vs ground truth (post-factum)
- Confusion matrix обновляется ежедневно/еженедельно
- Alert если metrics деградируют > threshold (e.g., precision < 0.5)

b) Data Drift Detection:

- Monitor distributions входных признаков
- KL-divergence, Wasserstein distance между train data и production data
- Alert если drift_score > threshold

c) Prediction Distribution:

- Track частоту каждого класса {-1, 0, 1}
- Если слишком много signal≠0 или слишком мало — investigate

d) Model Confidence:

- Average confidence (max probability) в predictions
- Если падает — возможно data drift или market regime change

e) Business Metrics:

- Win rate, Sharpe ratio, drawdown в live trading
- PnL tracking: cumulative profit/loss
- Compare с benchmark стратегией

4. Logging & Alerting:

- Log каждый prediction: timestamp, input features, output signal, probabilities
- Store в database (PostgreSQL, ClickHouse) для post-analysis
- Alerts: email/Telegram при critical events
  - Model error (exception)
  - Performance degradation
  - High uncertainty predictions

5. Model Retraining Strategy:

a) Trigger Conditions:

- Scheduled: ежемесячно/ежеквартально
- Performance-based: если val_precision падает ниже threshold
- Data drift: если drift_score превышает threshold

b) Incremental Learning:

- Retrain на расширенном датасете: старые данные + новые
- Fine-tuning: используй старую модель как initialization

c) A/B Testing:

- Deploy новая модель в parallel с текущей
- Compare performance на live data за период (e.g., 1 месяц)
- Switch если новая модель лучше

d) Versioning:

- Semantic versioning: v1.0.0, v1.1.0, v2.0.0
- Track модели, датасеты, hyperparameters в MLflow или Weights & Biases
- Rollback capability если новая модель fails

6. Edge Cases & Risk Management:

a) Handle extreme market events:

- Market gaps (price jumps)
- Low liquidity periods
- Flash crashes
- Fallback: disable trading или switch к conservative mode

b) Model uncertainty:

- Если confidence < low_threshold, skip trade
- Human-in-the-loop: flag high-uncertainty predictions для manual review

c) Circuit breakers:

- Max daily loss limit: stop trading если drawdown > X%
- Max trades per day: avoid overtrading
- Position sizing: adjust lot size based на confidence

7. Documentation & Handover:

- Deployment guide: step-by-step setup instructions
- API documentation (если model server)
- Monitoring dashboard setup (Grafana, custom UI)
- Incident response playbook
- Contact: кто ответственен за модель, escalation path

## ВЫХОДНОЙ ФОРМАТ:

- deployment/ directory:

  - inference_service.py (Flask API или standalone script)
  - Dockerfile (для containerization)
  - requirements.txt
  - deployment_config.yaml

- monitoring/ directory:

  - monitoring_dashboard.py (Streamlit или Grafana config)
  - drift_detection.py
  - alert_system.py

- docs/:

  - deployment_guide.md
  - monitoring_guide.md
  - retraining_procedure.md
  - troubleshooting.md

- tests/:

  - test_inference.py (unit tests)
  - test_integration.py

## ИНСТРУМЕНТЫ: Docker, Flask/FastAPI, MLflow, Prometheus+Grafana, Evidently AI (drift detection), PostgreSQL

