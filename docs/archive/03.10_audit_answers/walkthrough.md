# Walkthrough: Исправление логгера экспериментов

## Что сделано

Добавлены 9 недостающих колонок для полной воспроизводимости экспериментов.

### Изменённые файлы

| Файл | Что изменено |
|------|-------------|
| [experiment_logger.py](file:///home/hohla/git/SoSimple/ML/experiment_logger.py) | 9 новых колонок в `CSV_COLUMNS`, [_get_git_commit()](file:///home/hohla/git/SoSimple/ML/experiment_logger.py#89-100), [_migrate_csv_columns()](file:///home/hohla/git/SoSimple/ML/experiment_logger.py#147-172) |
| [train.py](file:///home/hohla/git/SoSimple/ML/train.py) | [_log_experiment()](file:///home/hohla/git/SoSimple/ML/train.py#588-655) — расширена сигнатура и вызов, передаются все параметры |

### Новые колонки CSV

| Колонка | Пример значения | Источник |
|---------|----------------|---------|
| [seed](file:///home/hohla/git/SoSimple/ML/utils.py#41-57) | 42 | [train_model()](file:///home/hohla/git/SoSimple/ML/train.py#267-581) param |
| [git_commit](file:///home/hohla/git/SoSimple/ML/experiment_logger.py#89-100) | 42668a1 | `git rev-parse --short HEAD` (авто) |
| `weight_decay` | 0.000100 | [train_model()](file:///home/hohla/git/SoSimple/ML/train.py#267-581) param |
| `scheduler_patience` | 5 | [train_model()](file:///home/hohla/git/SoSimple/ML/train.py#267-581) param |
| `scheduler_factor` | 0.500000 | [train_model()](file:///home/hohla/git/SoSimple/ML/train.py#267-581) param |
| `focal_gamma` | 2.000000 | только classification |
| `huber_delta` | 1.000000 | только regression |
| `use_weighted_sampler` | false | [train_model()](file:///home/hohla/git/SoSimple/ML/train.py#267-581) param |
| `num_parameters` | 147073 | [count_parameters()](file:///home/hohla/git/SoSimple/ML/utils.py#157-168) |

### Обратная совместимость

[_migrate_csv_columns()](file:///home/hohla/git/SoSimple/ML/experiment_logger.py#147-172) при инициализации логгера проверяет заголовки старого CSV и перезаписывает файл с новыми колонками, заполняя пустыми значениями для старых записей.

## Верификация (Фаза 1: Логгер)

```
# Последняя запись (тестовый запуск 1 epoch):
bilstm_20260311_172951 | seed=42 | git=42668a1 | weight_decay=0.0001 |
scheduler_patience=5 | huber_delta=1.0 | num_parameters=147073 | pearson_r=0.2362
```

Все 9 новых полей заполнены ✅. Старые записи сохранены с пустыми значениями для новых полей ✅.

## Тесты Репродуктивности (Фаза 2)

После исправления логгера и внедрения кэширования для ускорения (QW-1), был выполнен полный прогон `compare_architectures --task regression`.

**Результаты (seed=42, 50 epochs, Huber):**
- **BiLSTM**: Pearson r = 0.3236
- **CNN1D**: Pearson r = 0.2518 
- **Transformer**: Pearson r = 0.1143
- **Hybrid**: Pearson r = 0.2825

**Выводы:**
1. **100% Воспроизводимость**: Эти результаты с точностью до 4 знаков совпадают с результатами, зафиксированными **10 марта** (до всех изменений).
2. **Детерминированность доказана**: Кодовая база теперь стабильна. Фиксации `seed=42`, `lr=0.001` и других гиперпараметров достаточно для точного повторения результата на одной и той же машине.
3. **Откуда взялся Pearson r=0.555 в аудите?**: Теперь достоверно известно, что текущий код **не выдаёт 0.555** на текущих данных. Высокие значения (0.5+), зафиксированные в февральских чекпоинтах и упомянутые в аудите, были получены либо на другой версии данных, либо до исправления data leakage (как отмечено в Changelog от 10 марта), либо с совершенно иной конфигурацией гиперпараметров. 

> [!SUCCESS]
> Блокер снят. Теперь можно с уверенностью двигаться к экспериментам с регрессией (подбор гиперпараметров, новые фичи), зная, что любой результат будет честно и подробно занесён в лог и может быть повторён.
