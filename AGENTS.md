# AI Agent Configuration

## Quick Start для ИИ-агентов

### Основные индексы
- 📖 **[MODULE_INDEX.md](MODULE_INDEX.md)** — все модули проекта
- 🔄 **[DATA_FLOW.md](DATA_FLOW.md)** — поток данных через pipeline
- ⚡ **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** — команды и пути
- 📜 **[.ai/RULES_INDEX.md](.ai/RULES_INDEX.md)** — правила работы
- ⚙️ **[.ai/SKILLS_INDEX.md](.ai/SKILLS_INDEX.md)** — автоматизированные команды

### Project Context
- **Type**: Trading bot с ML predictions
- **Languages**: Python 3.11+, MQL4, Jupyter
- **Documentation**: Русский (код на английском)

## Pipeline Overview

```text
MT4 (lib_PIC.mqh) → Nero.csv
↓
processing/normalize.py → Nero_normalized.csv
↓
processing/label_main.py → train/val/test + scalers
↓
statistics/ → EDA, reports
↓
ML/ → models (в разработке)
```

**Детали**: [DATA_FLOW.md](DATA_FLOW.md)

## Quick Commands

| Команда | Назначение |
|---------|-----------|
| `sync docs` | Синхронизировать документацию с изменённым кодом |
| `doc this [файл]` | Задокументировать модуль *(⏸️ не реализован)* |
| `check docs` | Проверить актуальность документации *(⏸️ не реализован)* |

**Все команды**: [.ai/SKILLS_INDEX.md](.ai/SKILLS_INDEX.md)

## Критические правила

⚠️ **Всегда читай перед началом**:
1. **[000-documentation.md](.ai/rules/000-documentation.md)** — стандарт документирования
2. **[007-no-csv-context.md](.ai/rules/007-no-csv-context.md)** — запрет загрузки больших CSV
3. **[100-file-handling.md](.ai/rules/100-file-handling.md)** — работа с файлами (кодировки, форматы)

**Все правила**: [.ai/RULES_INDEX.md](.ai/RULES_INDEX.md)

## Workflow для агента

### При изменении кода
1. Запусти `sync docs` — автоматически обновит file headers и .md файлы
2. Если изменились входы/выходы — проверь [DATA_FLOW.md](DATA_FLOW.md)

### При изучении проекта
1. Начни с [MODULE_INDEX.md](MODULE_INDEX.md) — посмотри список модулей
2. Открой [DATA_FLOW.md](DATA_FLOW.md) — пойми pipeline
3. Используй [QUICK_REFERENCE.md](QUICK_REFERENCE.md) — найди команды и пути

### При создании нового модуля
1. Следуй [000-documentation.md](.ai/rules/000-documentation.md) — создай file header
2. Добавь запись в [MODULE_INDEX.md](MODULE_INDEX.md)
3. Создай `docs/[category]/[module].md`
4. Обнови [DATA_FLOW.md](DATA_FLOW.md) если нужно

## Навигация

- **Для людей**: [README.md](README.md)
- **Для агентов**: Этот файл
- **Индексы**: [MODULE_INDEX.md](MODULE_INDEX.md), [DATA_FLOW.md](DATA_FLOW.md), [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Правила**: [.ai/RULES_INDEX.md](.ai/RULES_INDEX.md)
- **Команды**: [.ai/SKILLS_INDEX.md](.ai/SKILLS_INDEX.md)