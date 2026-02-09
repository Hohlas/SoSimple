# Архитектура проекта SoSimple

## Обзор

Тогровая система в виде комплекса ботов:
1. Сбор данных из MetaTrader-4 и формирование массива фракталов (MQL4) 
2. Сортировка нормализация и маркировка (Python)
3. Статистический анализ (Python, Jupyter Notebooks)
4. Обучение моделей (ML)
5. Тестирование (ML)
6. Развертывание (ML)   


## Структура проекта

.ai/rules/ # Правила документирования и стиля
.ai/prompts/ # Готовые промпты
ML/ # Модели машинного обучения
MT/MQL4/Include/lib_PIC.mqh # Библиотека формирования датасета из рыночных данных
processing/ # Скрипты предобработки данных (нормализация, маркировка, разделение)
statistics/ # Скрипты и результаты статистического анализа данных
docs/ # Документация
├── data_analysis/ # Статистический анализ данных
├── data_preprocessing/ # скрипты предобработки данных
├── architecture.md # общая архитектура
├── data-flow.md    # Потоки данных, зависимости
└── dataset_description.md # структура датасета
Nero_normalization_stats.csv # татистика признаков до нормализации
Nero_atr_scaler.pkl # RobustScaler для ATR, обученный на train
Nero_test_labeled.csv # тестовая выборка с метками
Nero_train_labeled.csv # обучающая выборка с метками
Nero_val_labeled.csv # валидационная выборка с метками  




## Data Flow
MT/MQL4/Include/lib_PIC.mqh → Nero.csv
↓
processing/label_main.py → Nero_normalization_stats.csv, Nero_test_labeled.csv, Nero_train_labeled.csv, Nero_val_labeled.csv, Nero_atr_scaler.pkl 
↓
statistics/EDA.ipynb → reports/*, plots/*, EDA_files/*