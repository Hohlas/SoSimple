# План исследования причин неудачи моделей и поиска решений

## Цель
Выявить причины провала текущих ML моделей (нейросетей и baseline) на задаче прогнозирования разворотов Forex (H1) и определить эффективный путь улучшения: поиск новых моделей/архитектур или оптимизация структуры датасета, признаков и метрик.

## Milestones

### Milestone 1: Глубокий анализ данных и feature engineering
- **Цель**: Понять качество текущих признаков, выявить мультиколлинеарность, добавить информативные признаки.
- **Задачи**:
  - Изучить распределения признаков, корреляции, поиск мультиколлинеарности (используя statistics.py и EDA.ipynb).
  - Добавить вейвлет‑признаки и спектральные характеристики (реализовать в processing/).
  - Провести отбор признаков и оценить их важность через SHAP или mutual information.
- **Definition of Done**: Отчет с визуализациями и списком новых признаков, готовых к интеграции в пайплайн.
- **Validation commands**:
  - `python statistics/statistics.py DATA/Nero_train_labeled.csv --features`
  - `python processing/feature_wavelet.py --input DATA/Nero_train_labeled.csv --output DATA/Nero_train_wavelet.csv`
  - `python processing/feature_selection.py --method shap --data DATA/Nero_train_labeled.csv`
- **Риски**: Возможное увеличение размерности без улучшения сигнала; необходимость избегать утечки данных при создании новых признаков.
- **Статус**: [ ] pending

### Milestone 2: Baseline‑эксперименты с простыми моделями
- **Цель**: Определить, ограничивает ли нас модель capacity или качество данных, сравнив простые модели с текущими нейросетями.
- **Задачи**:
  - Запустить baseline‑эксперименты (SVM, логистическая регрессия, LightGBM, XGBoost) на текущем наборе признаков.
  - Сравнить метрики (F1, precision, recall, Pearson r) с результатами нейросетей.
  - При необходимости повторить с расширенным набором признаков из Milestone 1.
- **Definition of Done**: Таблица сравнения метрик baseline моделей и нейросетей, вывод о том, где bottleneck.
- **Validation commands**:
  - `python ML/baseline/baseline_experiments.py --models svm logistic lightgbm --task classification`
  - `python ML/baseline/baseline_experiments.py --models svm logistic lightgbm --task regression`
  - `python ML/experiment_logger.py --best f1_macro --task classification`
  - `python ML/experiment_logger.py --best pearson_r --task regression`
- **Риски**: Baseline могут показать низкие метрики из‑за шумных данных, что потребует более глубокой очистки.
- **Статус**: [ ] pending

### Milestone 3: Исследование новых архитектур и методов неопределённости (если baseline не превосходит нейросети)
- **Цель**: Если нейросети показывают потенциал, улучшить их через ансамбли, стекинг, методы неопределённости и новые функции потерь.
- **Задачи**:
  - Реализовать асимметричную функцию потерь (Asymmetric Regression Loss) в ML/losses.py и протестировать.
  - Исследовать конформное прогнозирование (Conformal Prediction) для калибровки предсказаний.
  - Попробовать стекинг/блендинг baseline моделей и нейросетей.
  - Добавить метрики калибровки (например, Brier score) и оптимизировать пороги решения.
- **Definition of Done**: Обновленные файлы losses.py, train.py,以及新的实验结果，显示指标改善。
- **Validation commands**:
  - `python -m ML.train --loss asymmetric --task regression`
  - `python -m ML.train --loss asymmetric --task classification`
  - `python -m ML.experiment_logger --best pearson_r --task regression`
  - `python -m ML.experiment_logger --best f1_macro --task classification`
- **Риски**: Сложные методы могут увеличить время обучения и риск переобучения без должной валидации.
- **Статус**: [ ] pending

### Milestone 4: Оптимизация структуры датасета и метрик (если baseline показывает сопоставимые или лучшие результаты)
- **Цель**: Если простые модели работают так же хорошо или лучше, сосредоточиться на улучшении данных: новая разметка, изменение горизонта предсказания, фильтрация шума.
- **Задачи**:
  - Реализовать новый скрипт переразметки predict: максимальное отклонение цены за фиксированный горизонт (например, 24 часа).
  - Обновить пайплайн препроцессинга (processing/label_main.py) для использования новой разметки.
  - Провести эксперименты с новыми целевыми переменными на baseline и нейросетях.
  - Исследовать альтернативные метрики: Quantile Loss, Pinball Loss, направленная точность.
- **Definition of Done**: Новый набор данных с переразметкой, обученные модели и отчет о улучшении предсказуемости.
- **Validation commands**:
  - `python processing/relabel_predict.py --horizon 24 --input MT/MQL4/Files/Nero.csv --output DATA/Nero_relabelled.csv`
  - `python -m ML.compare_architectures --task regression --data DATA/Nero_relabelled_train_labeled.csv`
  - `python -m ML.compare_architectures --task classification --data DATA/Nero_relabelled_train_labeled.csv`
- **Риски**: Изменение разметки требует полного переобучения и может сместить задачу в другую плоскость.
- **Статус**: [ ] pending

## Зависимости
- Milestone 1 должен предшествовать Milestone 2 и 4, так как предоставляет улучшенные признаки.
- Milestone 2 информирует о выборе между Milestone 3 и Milestone 4.
- Milestone 3 и Milestone 4 являются альтернативными путями в зависимости от результатов Milestone 2.

## Предположения
- Текущий датасет Nero.csv корректно размечен и не содержит критических ошибок разметки.
- Доступны вычислительные ресурсы для обучения множества моделей (CPU/GPU).
- Библиотеки (shap, scipy, statsmodels) установлены или могут быть установлены через requirements.txt.

## Определение готовности проекта
Проект считается готовым, когда достигнуто одно из следующего:
- Найдена комбинация признаков и модели, которая показывает статистически значимое улучшение по ключевым метрикам (F1 > 0.6 для классификации, Pearson r > 0.4 для регрессии) на валидационной выборке.
- Или получено четкое заключение, что дальнейшие улучшения невозможны при текущей постановке задачи, и предложен альтернативный подход (например, изменение горизонта предсказания или использование других источников данных).
