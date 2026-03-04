---
name: refactor-agents-md
description: Use when AGENTS.md exceeds 200 lines, needs restructuring, or when refactoring project documentation architecture
---

# Рефакторинг AGENTS.md

## Overview

AGENTS.md > 200 lines — проблема: загружается на КАЖДЫЙ запрос, тратит токены.

**Core principle:** Модульная архитектура: Foundation → Component → Feature.

## When to Use

- AGENTS.md > 200 lines
- Появился task-specific контент (ML, MQL4, deploy)
- Дублирование между AGENTS.md и другими документами
- Нужно добавить новый компонент в проект
- Команды: "refactor agents.md", "split agents.md"

## The Process

### Phase 1: Audit (Обязательно!)

**Шаг 1.1: Подсчитать строки**
```bash
wc -l AGENTS.md
wc -l .kilocode/rules/*.md
```

**Шаг 1.2: Найти task-specific контент**
Разметить каждую секцию AGENTS.md:
| Секция | Тип | Действие |
|--------|-----|----------|
| Quick start | Foundation | Оставить |
| ML pipeline details | Component | Вынести в rules/ml.md |
| MQL4 encoding | Component | Вынести в rules/mql4.md |
| Deployment | Feature | Вынести в docs/deploy.md |

**Шаг 1.3: Найти дублирование**
Сравнить с:
- README.md
- docs/DATA_FLOW.md
- MODULE_INDEX.md

### Phase 2: Extract (Вынести компоненты)

**Шаг 2.1: Создать component rules**

Для каждого task-specific раздела:
```bash
# Пример: ML компонент
cat > .kilocode/rules/ml.md << 'EOF'
---
name: ml-pipeline
description: ML pipeline specific rules for SoSimple project
globs:
  - "ML/**/*.py"
  - "ML/**/*.ipynb"
alwaysApply: false
---

# ML Pipeline Rules

## Model Training
- Все модели наследуются от BaseModel
- Сохраняй чекпоинты в ML/checkpoints/
- Используй ExperimentLogger для логирования

## Data Loading
- Используй data_loader.DataLoader
- Нормализация через normalize.py
EOF
```

**Шаг 2.2: Создать feature docs**
```bash
mkdir -p docs/ml
cat > docs/ml/training_guide.md << 'EOF'
# ML Training Guide

@AGENTS.md:45  # Ссылка на архитектуру

## Quick Start
...
EOF
```

**Шаг 2.3: Обновить AGENTS.md**
- Удалить вынесенные секции
- Добавить ссылки:
```markdown
## ML Pipeline
Детали: [.kilocode/rules/ml.md](.kilocode/rules/ml.md)  
Руководство: [docs/ml/training_guide.md](docs/ml/training_guide.md)
```

### Phase 3: Validate (Проверить)

**Шаг 3.1: Проверить размеры**
```bash
wc -l AGENTS.md  # Должно быть < 200
wc -l .kilocode/rules/*.md  # Каждый < 500
```

**Шаг 3.2: Проверить ссылки**
```bash
# Проверить все markdown ссылки
grep -r '\[.*\](.*\.md)' AGENTS.md .kilocode/rules/ | head -20
```

**Шаг 3.3: Проверить @ ссылки**
Убедиться, что используются `@file` вместо копирования.

### Phase 4: Commit

**Шаг 4.1: Создать коммит**
```bash
git add AGENTS.md .kilocode/rules/ docs/
git commit -m "refactor: split AGENTS.md into modular rules

- Extract ML rules to .kilocode/rules/ml.md
- Extract MQL4 rules to .kilocode/rules/mql4.md
- Reduce AGENTS.md from XXX to < 200 lines
- Add cross-references with @ syntax"
```

## Quick Reference

| Category | Values |
|----------|--------|
| Tags | documentation, refactoring, agents, architecture |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Оставить task-specific в AGENTS.md | Выносить в отдельные rules |
| Дублировать контент | Использовать @ ссылки вместо копирования |
| Забыть globs в новых rules | Добавлять globs для автозагрузки |
| AGENTS.md > 200 строк | Разбить на skills и docs |
| Не проверять размеры после рефакторинга | Всегда проверять wc -l |

## Examples

### ✅ Before (AGENTS.md > 300 lines)
```markdown
# SoSimple

## Quick Start  (10 строк)
## Architecture (20 строк)
## ML Pipeline  (80 строк!) ← Сюда
## MQL4 Details (60 строк!) ← И сюда
## Data Flow    (40 строк) ← И сюда
```

### ✅ After (AGENTS.md < 100 lines)
```markdown
# SoSimple

## Quick Start
## Architecture
## Modular Docs
- ML: @.kilocode/rules/ml.md, @docs/ml/
- MQL4: @.kilocode/rules/mql4.md
- Data: @docs/DATA_FLOW.md
```
