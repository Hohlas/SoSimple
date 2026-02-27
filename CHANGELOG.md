# Changelog SoSimple
Хронология значимых изменений проекта (major milestones).


## [2026-02-27] — Оптимизация под торговые сигналы: метрики и балансировка
### Добавлено
- CLI аргумент `--metric_mode` для выбора целевой метрики (f1_macro | f1_minority | signal_precision)
- CLI аргумент `--min_signal_recall` для ограничения минимального recall сигнальных классов
- CLI аргумент `--use_weighted_sampler` для балансировки train-батчей (WeightedRandomSampler)
- Метрики `signal_precision`, `signal_recall`, `f1_minority` в `ML/utils.py`
- Метрик precision_neg, precision_pos, recall_neg, recall_pos в возвращаемый словарь `compute_metrics()`
- Поддержка WeightedRandomSampler в `ML/data_loader.py` для классификации
- Логирование выбранного режима метрики и signal-метрик в результаты эксперимента
- Обновлена документация `docs/ml/neural_networks.md` с описанием новых метрик и режимов

### Изменено
- Early stopping теперь может использовать Precision сигнальных классов вместо Macro F1
- Возвращаемый словарь `compute_metrics()` содержит расширенный набор метрик для сигналов
- `train_model()` передаёт новые параметры в `create_data_loaders()` для WeightedRandomSampler

### Примечание
- WeightedRandomSampler используется только для train; val/test сохраняют реальное распределение
- Для `metric_mode=signal_precision` применяется штраф, если recall < min_signal_recall

### Исправлено
- Ошибка в `WeightedRandomSampler`: преобразование меток {-1, 0, 1} → {0, 1, 2} через `y_train + 1` вместо list comprehension

## [2026-02-27] — CLI аргументы для Optuna
### Добавлено
- CLI аргумент `--metric_mode` в `ML/optimize.py` для выбора целевой метрики оптимизации
- CLI аргумент `--min_signal_recall` в `ML/optimize.py` для настройки порога recall
- Параметры `metric_mode` и `min_signal_recall` в `create_objective()` и `run_optimization()`

### Изменено
- `ML/optimize.py` теперь поддерживает все три режима метрик через CLI (f1_macro, f1_minority, signal_precision)

## [2026-02-27] — Критический анализ: ловушка дисбаланса классов
### Проблема
- **Macro F1 = 0.57 — обманчивая метрика**: высокое значение достигается за счёт F1(0)=0.95 (neutral, 95% данных)
- **Торгово-значимые классы (-1 и 1) имеют F1 ≈ 0.35** — катастрофически низкое качество
- **Precision сигнальных классов**: 0.25–0.30 → 70-75% ложных торговых сигналов
- Веса Focal Loss [0.445, 0.11, 0.445] недостаточны для компенсации дисбаланса 5%/95%

### Вывод
- Модели с "хорошим" Macro F1 фактически непригодны для торговли
- Требуется смена целевой метрики (F1 minority, MCC) и балансировка батчей (WeightedRandomSampler)

## [2026-02-27] — Сравнение архитектур нейросетей (регрессия)
### Добавлено
- `ML/reports/architecture_comparison_regression.md` — отчёт сравнения всех архитектур для регрессии
- Чекпоинты для всех моделей в режиме регрессии: `*_regression_best.pt`
- Графики кривых обучения и residual plots для регрессии в `ML/plots/`
### Результаты
- **Bi-LSTM**: лучший Pearson r = 0.3236, 147K параметров
- **Hybrid CNN+LSTM**: Pearson r = 0.2825, 83K параметров
- **1D-CNN**: Pearson r = 0.2518, 42K параметров (самая быстрая)
- **Transformer**: Pearson r = 0.1143, 70K параметров

## [2026-02-25] — Оптимизация гиперпараметров (Optuna)
### Добавлено
- `ML/optimize.py` — автоматический подбор гиперпараметров с помощью Optuna
- `ML/experiment_logger.py` — единый CSV-логгер для всех ML-экспериментов
- `ML/reports/optuna_best_params_*.json` — лучшие найденные конфигурации
- `ML/reports/optuna_study_*.json` — результаты study Optuna
- Поддержка pruning (досрочная остановка неперспективных trials)
- Оптимизация для classification (macro F1) и regression (pearson_r)
### Зависимости
- `optuna>=3.0`

## [2026-02-23] — Поддержка обучения в режиме регрессии (predict target)
### Добавлено
- `ML/train.py` — аргумент `--task {classification,regression}`
- `ML/train.py` — поддержка раннего останова (early stopping) по корреляции Пирсона (`pearson_r`)
- `ML/data_loader.py` — аргумент `target` для загрузки `predict` как float32-тензора
- `ML/losses.py` — `HuberLoss` (δ=1.0) для робастной функции ошибок при регрессии
- `ML/utils.py` — `compute_regression_metrics()` (MAE, RMSE, R², pearson_r, DirAcc)
- `docs/ml/neural_networks.md` — обновлено описание пайплайна и используемых метрик
### Изменено
- Архитектура `models/` поддерживает `num_classes=1` для регрессии (скалярный выход)
- Артефакты регрессии сохраняются с суффиксом `_regression` во избежание конфликтов

## [2026-02-20] — Реструктуризация ML/baseline
### Изменено
- Создан подкаталог `ML/baseline/` для изоляции baseline-моделей
- `ML/baseline_experiments.py` перемещен в `ML/baseline/`
- Автогенерируемые артефакты baseline теперь сохраняются в `ML/baseline/plots/` и `ML/baseline/reports/`
- Обновлена документация: `AGENTS.md`, `MODULE_INDEX.md`, `CHANGELOG.md`, `docs/ml/baseline_experiments.py.md`

## [2026-02-18] — Нейросетевые архитектуры (Этап 3.2)
### Добавлено
- `ML/models/bilstm.py` — Bi-LSTM классификатор (147K параметров)
- `ML/models/cnn1d.py` — 1D-CNN классификатор (42K параметров)
- `ML/models/transformer.py` — Transformer Encoder с CLS-токеном (70K параметров)
- `ML/models/hybrid_cnn_lstm.py` — Hybrid CNN+LSTM (83K параметров)
- `ML/data_loader.py` — Dataset/DataLoader с парсингом, нормализацией и padding mask
- `ML/train.py` — Единый скрипт обучения (Focal Loss, AdamW, early stopping на F1)
- `ML/losses.py` — Focal Loss для несбалансированных данных
- `ML/utils.py` — Seed, метрики, подсчёт параметров
- `ML/compare_architectures.py` — Скрипт сравнения всех архитектур
- Зависимость: torch>=2.0

## [2026-02-18] — Baseline ML эксперименты
### Добавлено
- `ML/baseline_experiments.py` — 5 baseline-моделей (Dummy, LogReg, RF, XGBoost, LightGBM)
- `ML/reports/baseline_report.md` — автогенерируемый отчёт с метриками и confusion matrices
- Зависимости: xgboost, lightgbm

## [2026-02-15] — Изменение путей вывода данных
### Изменено
- Выходные файлы `label_main.py` теперь создаются в каталоге `DATA/` вместо корня проекта
- Обновлена документация: `AGENTS.md`, `DATA_FLOW.md`, `docs/data_preprocessing/label_main.py.md`

## [2026-02-14] — Оптимизация документации
### Изменено
- Консолидирована документация: убрано дублирование, объединены файлы
- Стандартизированы YAML frontmatter во всех skills
- Обновлены пути в QUICK_REFERENCE → интегрирован в AGENTS.md

## [2026-02-10] — Оптимизация документации для ИИ-агентов
### Добавлено
- `MODULE_INDEX.md` — справочник всех модулей
- `DATA_FLOW.md` — визуальный граф потока данных
- `.ai/RULES_INDEX.md` — каталог правил с приоритетами
- `.ai/SKILLS_INDEX.md` — каталог skills
- 8 новых правил для ИИ-агентов (001-008)
### Изменено
- Реструктурирована документация для минимизации дублирования
- Добавлены обратные ссылки между файлами для быстрой навигации

## [2026-02-07] — Исправление нормализации predict
### Исправлено
- Обработка знакового `predict` в `normalize.py`
- `predict` теперь корректно нормализуется: модуль → нормализация → восстановление знака
