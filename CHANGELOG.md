# Changelog SoSimple
Хронология значимых изменений проекта (major milestones).

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
