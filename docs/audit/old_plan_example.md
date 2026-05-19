# ЭТАП 1
## 1.1 — EDA (Exploratory Data Analysis)

1. Загрузи данные из Nero.csv и распарси структуру фракталов. Для образца можешь использовать код statistics.py, он загружает тот же файл для обработки.
2. Проанализируй распределения всех 11 признаков отдельно для классов {-1, 0, 1}:
   - Построй таблицу со статистиками: mean, std, min, max, quartiles
   - Построй histograms и boxplots для каждого признака, раскрашенные по классам
3. Выполни статистические тесты на различия между классами:
   - t-test для нормально распределенных признаков
   - Mann-Whitney U-test для non-normal
   - Создай таблицу с p-values
4. Корреляционный анализ:
- Построй корреляционные матрицы признаков fractal[0] отдельно для каждого класса
- Построй коррелцию признаков между соседними фракталами (e.g., power vs power)
- Heatmap визуализация
5. Временной анализ:
- График появления событий signal≠0 во времени (по fractal_time)
- Проверь наличие сезонности (по часам дня, дням недели)
- Есть ли кластеризация событий signal≠0?
6. Проверь на выбросы:
- Boxplots с выделением outliers
- Quantile analysis (1%, 99%)
7. Dimension Reduction Visualization:
   - t-SNE или UMAP проекция признаков fractal[0] с раскраской по классам
   - Помогает визуально оценить разделимость классов

**Цель**: Понять данные глубоко — их статистические свойства, распределения, аномалии и паттерны.

**Назначение**:

- Выявить значимые различия между классами signal={-1, 0, 1}
- Понять, какие признаки фракталов наиболее информативны для разделения классов
- Обнаружить проблемы с данными (выбросы, пропуски, несогласованности)
- Проверить гипотезы: есть ли временные паттерны (сезонность), кластеризуются ли разворотные события во времени

**Ожидаемые данные на выходе**:

- **Таблицы статистик** для каждого класса: mean, std, min/max признаков
- **P-values** из статистических тестов (какие признаки статистически различаются между классами)
- **Корреляционные матрицы** (3 штуки — по одной для каждого класса)
- **Графики**: histograms, boxplots, scatter plots, t-SNE визуализация
- **Текстовый отчет**: какие признаки дискриминативны, есть ли аномалии

**Критичность**: Без понимания данных невозможно правильно построить модель.

## 1.2 — Feature Engineering (используя результаты из 1.1)
**Цель**: Создать новые признаки, которые лучше описывают паттерны разворотов тренда, чем исходные 11 признаков фракталов.

**Назначение**:

- Агрегировать информацию из последовательности 100 фракталов (модель должна видеть не только отдельные фракталы, но и их взаимосвязи)
- Добавить доменную специфику: support/resistance уровни, volatility
- Улучшить разделимость классов

**Ожидаемые данные на выходе**:

- **feature_engineered.csv**: новая таблица с дополнительными столбцами (например, было 11 признаков × 100 фракталов, стало 11 × 100 + 50-100 новых агрегированных признаков)
- **Список новых признаков** с описанием: `rolling_mean_price_10`, `delta_power`, `trend_slope_impulse_20`, и т.д.
- **Feature importance ranking** (предварительный, на основе корреляции с signal)

**Примеры новых признаков**:

- `mean_price_last_10` — средняя цена за последние 10 фракталов
- `trend_slope_impulse` — наклон линейной регрессии impulse за окно
- `direction_changes_count` — сколько раз direction менялся в последовательности
- `relative_position_price` — где текущий фрактал по цене относительно min/max

**Критичность**: Feature engineering часто важнее выбора архитектуры модели.

## 1.3: Data Quality Checks

**Цель**: Убедиться, что данные корректны и не содержат **data leakage** (утечки информации из будущего).

**Назначение**:

- **Data leakage проверка**: эволюционирующие признаки (back, break, strong, power) не должны содержать forward-looking информацию для fractal[i] в момент t_i
- Проверить missing values, NaN, infinity
- Валидировать causal consistency: если фрактал появляется в строках i и h (h>i), его стабильные признаки (time, price, direction) должны совпадать, а эволюционирующие — согласованно изменяться

**Ожидаемые данные на выходе**:

- **Отчет по quality**: количество missing values, аномалий
- **Validation результат**: leakage обнаружен/не обнаружен
- **Cleaned dataset** (если были проблемы) или подтверждение, что данные валидны

**Критичность**: Data leakage приведет к завышенным метрикам на обучении, но провалу в продакшене.

## 1.4 — Рекомендации
**Цель**: На основе анализа дать конкретные рекомендации для следующих этапов.

**Назначение**:

- Какие признаки использовать (топ-20)
- Нужна ли нормализация (RobustScaler vs MinMaxScaler vs StandardScaler)
- Какие дополнительные признаки добавить (ATR, ...)

**Ожидаемые данные на выходе**:

- **feature_ranking.csv**: список признаков по важности
- **Текстовый отчет**: "Рекомендуется использовать RobustScaler из-за наличия выбросов в признаке break. Добавить ATR для учета волатильности..."

**Критичность**: Направляет дальнейшую работу, экономит время на экспериментах.

# ЭТАП 2: Data Preprocessing & Splitting Strategy

## 2.1 подходы к данным для моделирования
### - RAW SEQUENCE  (99 фракталов × 11 признаков = 1089 признаков на строку)
    **dataset_sequence.csv** для ****LSTM, Transformer, CNN1D — они сами извлекают паттерны из последовательности. 
    X.shape = (5042, 99, 11)  # сырые фракталы
### ENGINEERED FEATURES (агрегированные признаки - 233 на строку.) 
fractal0 8 признаков:  raw_price0, raw_dir0, raw_front0, raw_back0, raw_reverse0, raw_power0, raw_count0, raw_impulse0

статистика цены за 10 фракталов: price_mean_w10, price_std_w10, price_min_w10, price_max_w10  

тренды и относительные позиции: price_slope_2, price_zscore_w20, price_percentile_w10 

взаимодействия: front_back_interaction, impulse_direction_interaction 

паттерны направления: direction_changes_w10, peak_valley_ratio_w5 

доменные индикаторы: support_resistance_w20, volatility_proxy_10 

временные признаки: hour_sin, hour_cos, day_of_week_sin, day_of_week_cos   

X.shape = (5042, 233)     # engineered features из EDA

# ЭТАП 3: Model Architecture Design & Selection

ЗАДАЧА SPECIFICATION:
- Input: X ∈ R^{batch×99×n_features}, где 99 — длина последовательности фракталов
- Output: y ∈ {-1, 0, 1} (3-class classification) или 2 binary classifiers для signal=1 и signal=-1 отдельно
- Metric priority: Precision (минимизация ложных сигналов), но с мониторингом Recall и F1
- Constraints: нет latency требований (H1 таймфрейм), GPU не доступен

## 0. Gradient Boosting Baselines (выполнить ПЕРВЫМ):

   a) Data Preparation для Tree-based моделей:
      - Flatten sequential data: (batch × 99 fractals × 11 features) → (batch × 1089 features)
      - Naming convention: fractal_0_price, fractal_0_direction, ..., fractal_98_impulse
      - Альтернатива: агрегированные признаки из Этапа 1 (rolling stats, trends)
   
   b) XGBoost:
      ```python
      XGBClassifier(
          objective='multi:softmax',  # для 3 класса
          num_class=3,
          scale_pos_weight=class_weights,  # для дисбаланса
          max_depth=6,
          learning_rate=0.1,
          n_estimators=500,
          early_stopping_rounds=50
      )
      ```
   
   c) LightGBM:
      ```python
      LGBMClassifier(
          objective='multiclass',
          num_class=3,
          class_weight='balanced',  # auto balancing
          max_depth=8,
          learning_rate=0.05,
          n_estimators=1000,
          is_unbalance=True  # для extreme imbalance
      )
      ```
   
   d) CatBoost:
      ```python
      CatBoostClassifier(
          loss_function='MultiClass',
          classes_count=3,
          auto_class_weights='Balanced',  # recommended для imbalanced
          depth=8,
          learning_rate=0.03,
          iterations=1000,
          early_stopping_rounds=50
      )
      ```
   
   e) Feature Importance Analysis:
      - Извлеки топ-50 важных признаков из каждой модели
      - SHAP values для интерпретации: какие фракталы и признаки наиболее значимы?
      - Сравни важность между моделями: есть ли консенсус?
   
   f) Baseline Performance:
      - Evaluate на validation set: Precision, Recall, F1 (per class и weighted)
      - Сохрани результаты в baseline_results.csv
      - Inference time: измерь latency для single prediction

## 1. Спроектируй 4-5 baseline архитектур:

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

## 2. Имплементация деталей:

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

## 3. Loss Function Design (критично для imbalanced data):

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

## 4. Multi-Task Learning (опционально):
   - Auxiliary tasks:
     * Предсказание direction следующего фрактала
     * Регрессия на power или impulse
   - Помогает модели учить более robust representations

## 5. Implementation Requirements:
   - Код должен быть модульным: separate файлы для models/, losses/, utils/
   - Configurable через config файл (YAML или Hydra)
   - Support для model checkpointing
   - Logging: TensorBoard или Weights & Biases

## 6. Baseline Experiments Setup:
   - Определи experiment matrix:
     * Architecture: [LSTM, Transformer, CNN-LSTM, TCN]
     * Loss: [WeightedCE, FocalLoss, CB-Loss]
     * Sampling: [Original, SMOTE, Undersampling]
   - Минимум 12 экспериментов (4 arch × 3 loss combinations)

## ВЫХОДНОЙ ФОРМАТ:
- models/lstm.py, models/transformer.py, models/cnn_lstm.py, models/tcn.py
- losses/focal_loss.py, losses/class_balanced_loss.py
- config/model_configs.yaml
- train.py (training loop script)
- Архитектурная диаграмма (draw.io или PlantUML)
- README_models.md с описанием каждой архитектуры и обоснованием выбора

## REFERENCE:
- Momentum Transformer for changepoint detection in trading
- Cost-sensitive hybrid networks для imbalanced time series
- LSTM для forex prediction с temporal dependencies

## ИНСТРУМЕНТЫ: 
PyTorch, transformers library, timm, pytorch-lightning (опционально)

# ЭТАП 4: Training, Hyperparameter Tuning & Evaluation

## 1. Training Setup:

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

## 2. Hyperparameter Tuning:

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

## 3. Evaluation Metrics (критично для imbalanced 3-class):

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

## 4. Cross-Validation (если применимо):
   - Time-series CV: expanding window или sliding window
   - 5-fold temporal CV для более robust оценки generalization
   - Aggregate metrics: mean ± std across folds

## 5. Test Set Evaluation (final step):
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

## 6. Model Interpretability (опционально, но полезно):
   - SHAP values для feature importance
   - Attention weights visualization (для Transformer/LSTM+Attention)
   - Какие фракталы в последовательности наиболее важны для предсказания?
   - Gradient-based saliency maps

## 7. Model Selection:
   - Сравни все модели по val/test metrics
   - Выбери топ-3 модели
   - Рассмотри ensemble этих топ-3 (voting или stacking)

## ВЫХОДНОЙ ФОРМАТ:
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

## ИНСТРУМЕНТЫ: 
PyTorch, Optuna/Ray Tune, scikit-learn metrics, matplotlib, seaborn, SHAP

# ЭТАП 5: Model Ensemble & Post-Processing Strategies

## 1. Ensemble Strategies:

   a) Voting Ensemble:
      - Hard voting: majority vote по классам {-1, 0, 1}
      - Soft voting: усреднение predicted probabilities, затем argmax
      - Weighted voting: assign weights к моделям по их val_precision
   
   b) Stacking Ensemble  (Neural-only):
      - Meta-learner: Logistic Regression или LightGBM
      - Features: predicted probabilities от base models (3 models × 3 classes = 9 features)
      - Train meta-learner на validation set
      - Evaluate на test set
   
   c) Blending:
      - Подобно stacking, но проще: linear combination of predictions
      - Optimize weights через grid search на validation set
   
   d) Hybrid Stacking (Neural + Tree-based):
      - Base models: [Best Transformer/LSTM, XGBoost, LightGBM, CatBoost]
      - Feature construction для meta-learner:
        * Predicted probabilities: 4 models × 3 classes = 12 features
        * Model confidence scores: max(probabilities) для каждой модели = 4 features
        * Agreement indicators: majority vote, entropy of predictions = 2 features
        * Total: 18 features для meta-learner
      - Meta-learner options:
        * Logistic Regression (simple, interpretable)
        * LightGBM (captures non-linear interactions между моделями)
        * MLP (2-layer neural net для complex patterns)
      - Training strategy:
        * Train base models на train set
        * Generate predictions на validation set для meta-learner training
        * Evaluate final stack на test set (unseen by meta-learner)
      - Преимущество: комбинирует temporal pattern recognition (neural nets) 
        с feature interaction learning (tree models)
   
   e) Conditional Ensemble (domain-specific):
      - Используй разные модели для разных market regimes
      - Например: LSTM для trending markets, Transformer для reverting markets
      - Regime detection: по volatility (ATR), momentum indicators
      - Hybrid consideration: XGBoost для high-volatility periods (более stable)
      
      
      

## 2. Threshold Optimization (критично для precision):

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

## 3. Calibration (для probabilistic outputs):
   - Platt Scaling (Logistic Regression on logits)
   - Isotonic Regression (non-parametric, more flexible)
   - Temperature Scaling (для neural networks)
   - Цель: улучшить reliability predicted probabilities для risk management

## 4. Post-Processing Rules (domain logic):

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

## 5. Performance Optimization:
   - Model Quantization (FP32 → FP16 или INT8) для faster inference
   - ONNX export для deployment efficiency
   - Batch inference optimization (если real-time не критично)

## 6. Backtesting на историческом периоде:
   - Simulate trading с финальными predictions
   - Metrics:
     * Total return, Sharpe ratio, Max drawdown
     * Win rate, average win/loss, profit factor
     * Number of trades (не слишком много или мало?)
   - Сравни с baseline: buy-and-hold, simple momentum strategy

## 7. Uncertainty Quantification:
   - Monte Carlo Dropout: несколько forward passes с dropout enabled
   - Ensemble uncertainty: variance в predictions между models
   - Flagging: помечай predictions с high uncertainty для manual review

## ВЫХОДНОЙ ФОРМАТ:
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

## ИНСТРУМЕНТЫ: 
scikit-learn, xgboost/lightgbm, backtesting.py, PyTorch, ONNX

# ЭТАП 6: Deployment, Monitoring & Continuous Improvement

## 1. Deployment Architecture:
    
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
## 2. Inference Workflow:
    
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
    
## 3. Model Monitoring (критично для production):
    
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
## 4. Logging & Alerting:
    - Log каждый prediction: timestamp, input features, output signal, probabilities
    - Store в database (PostgreSQL, ClickHouse) для post-analysis
    - Alerts: email/Telegram при critical events
        - Model error (exception)
        - Performance degradation
        - High uncertainty predictions
## 5. Model Retraining Strategy:
    
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
## 6. Edge Cases & Risk Management:
    
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
## 7. Documentation & Handover:
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

## ИНСТРУМЕНТЫ: 
Docker, Flask/FastAPI, MLflow, Prometheus+Grafana, Evidently AI (drift detection), PostgreSQL

**Альтернативные подходы**:
- Two-stage модель: сначала binary classifier (trade/no_trade), затем direction classifier (buy/sell)
- Регрессионная оценка вероятности разворота вместо жесткой классификации
- Reinforcement Learning: обучите агента принимать торговые решения с reward = PnL

**Критически важные аспекты**:
- Избегайте data leakage: эволюционирующие признаки должны отражать состояние в момент t_i
- Temporal causality: используйте только walk-forward validation
- Class imbalance: focal loss и тщательный threshold tuning критичны для успеха
