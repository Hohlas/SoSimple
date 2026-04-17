# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Session Start Protocol

В начале каждой сессии читать в этом порядке:
1. `AGENTS.md` — главный индекс проекта (структура, правила, команды)
2. `CONTEXT_HANDOFF.md` — текущее состояние, что дальше, открытые риски
3. `wiki/index.md` — каталог синтезированных знаний
4. Через `search_knowledge` найти релевантные `wiki/`, `docs/reports/`, код

Источники знаний по приоритету: явный запрос пользователя → `AGENTS.md` / `docs/` → `docs/superpowers/` → `wiki/` → `.claude/memory/`.

## Commands

```bash
# Виртуальное окружение
source .venv/bin/activate

# Тесты (все / один файл)
python -m pytest tests/ -v
python -m pytest tests/test_entry_path_task.py -q

# Препроцессинг данных
python processing/label_main.py --input MT/MQL4/Files/Nero.csv

# Обучение модели (общий вид — конкретную модель/задачу см. в CONTEXT_HANDOFF.md)
python -m ML.train --model <model_name> --task <task_name>

# Статистика по данным
python statistics/statistics.py DATA/Nero_train_labeled.csv
```

## Architecture

**SoSimple** — ML-бот для прогнозирования разворотов Forex XAUUSD (H1) на базе паттерна Price-in-Channel (PIC) с 100 фракталами как входными признаками.

### Data Pipeline

```
MT4 Expert ($o$imple.mq4)
  → lib_PIC.mqh (NERO_CSV_CREATE)
  → MT/MQL4/Files/Nero.csv  [UTF-16LE, separator ";"]
  → processing/label_main.py  (sort → label → normalize → split 70/15/15)
  → DATA/Nero_{train,validation,test}_labeled.csv
  → ML/train.py  (Transformer Encoder, multi-task)
  → ML/checkpoints/*_best.pt
  → API/export_entry_path_v1_quantile_signals.py
  → MT/MQL4/Files/ml_signals.csv  [time;signal]
  → lib_ML_Signal.mqh  (BUY/SELL/CLOSE/SKIP)
```

### Key Modules

| Модуль | Статус | Назначение |
|--------|--------|-----------|
| `processing/label_main.py` | 🏁 | CLI-оркестратор: sort → label → normalize → split |
| `ML/models/entry_path_v1_quantile_transformer.py` | ✅ | Production-модель: Transformer с multi-head quantile output |
| `ML/entry_path_v1_quantile_task.py` | ✅ | Контракт таргетов и метрик для production-задачи |
| `ML/train.py` | ✅ | Основной скрипт обучения, multi-task |
| `API/export_entry_path_v1_quantile_signals.py` | ✅ | Генерация `ml_signals.csv` для MT4 |
| `statistics/signal_tracer.py` | ✅ | Reconciliation ML-сигналов с реальными сделками MT4 |
| `ML/benchmark_quantile_forward_validation.py` | ✅ | Frozen benchmark для forward validation |

## Critical Conventions

### CSV-файлы из MT/
```python
# ВСЕГДА использовать для MT4-данных:
pd.read_csv('MT/MQL4/Files/Nero.csv', encoding='utf-16-le', sep=';')
```
- Никогда не загружать CSV >100 MB целиком в контекст — использовать `Read` с `limit`/`offset`, `Grep` для поиска
- Читать первые 10 строк любого CSV перед обработкой

### После изменения кода
Обновить file header в изменённом файле + соответствующую документацию в `docs/`. Использовать скилл `update-docs-on-code-change`.

### Новый файл
Добавить запись в `MODULE_INDEX.md` через Mode 4 скилла `update-docs-on-code-change`.

### Язык
Документация и комментарии — **русский**. Идентификаторы в коде — **английский**.

### Git
- Всегда создавать новую feature-ветку для каждой задачи
- `git push` — только по явной просьбе пользователя
- Bugfix без рефакторинга «заодно»

## Documentation Map

| Файл | Назначение |
|------|-----------|
| `AGENTS.md` | Главный индекс: структура, правила, статусы |
| `CONTEXT_HANDOFF.md` | Текущий статус и следующий шаг |
| `MODULE_INDEX.md` | Реестр всех модулей со статусами |
| `docs/DATA_FLOW.md` | Полная схема потока данных |
| `docs/reports/` | Канонические отчёты завершённых этапов |
| `docs/superpowers/roadmap.md` | Активный roadmap |
| `wiki/index.md` | Каталог синтезированных wiki-страниц |
| `CHANGELOG.md` | История изменений (читать первые 300 строк) |

Папка `docs/archive/` — **не открывать** без явной просьбы.

## RAG Search

`knowledge-rag` MCP — retrieval layer для поиска по проекту. Результат — кандидаты; после RAG открывать первоисточник и проверять контекст.

```python
# Точный поиск (имена, пути, метрики):
search_knowledge("entry_path_v1_quantile", hybrid_alpha=0.0)
# Технический поиск:
search_knowledge("triple barrier label convention", hybrid_alpha=0.3)
# Концептуальный поиск:
search_knowledge("why quantile execution filter works", hybrid_alpha=0.7)
# Переиндексация:
reindex_documents()          # только изменённые файлы
reindex_documents(force=True) # полный rebuild BM25
```
