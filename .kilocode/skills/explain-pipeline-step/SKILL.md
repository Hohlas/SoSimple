---
name: explain-pipeline-step
description: Use when explaining a specific pipeline step by combining information from DATA_FLOW.md and module documentation
---

# Объяснение шага pipeline

## Overview

Предоставление детального объяснения конкретного шага pipeline на основе информации из DATA_FLOW.md и документации модулей.

## When to Use

- Нужно понять, что делает конкретный шаг обработки
- Изучение pipeline новым разработчиком
- Команды: "explain step [name]", "what does [name] do"

## The Workflow

**Команда**: `explain step [название]` или `what does [название] do`
**Назначение**: Дать детальное объяснение конкретного шага pipeline

Шаги:
1. Найти шаг в DATA_FLOW.md
2. Найти связанные скрипты в MODULE_INDEX.md
3. Загрузить docs/[категория]/[скрипт].md
4. Сформировать краткое объяснение:
   - Что делает
   - Какие данные входят/выходят
   - Какие параметры доступны
   - Как запустить

Пример:
> explain step normalization

## Нормализация данных
**Скрипт**: processing/normalize.py
**Назначение**: RobustScaler-нормализация признаков, устойчивая к выбросам

**Входы**: Nero.csv (сырые фракталы)
**Выходы**: Nero_normalized.csv, Nero_atr_scaler.pkl

**Использование**:
python processing/normalize.py --input Nero.csv --output Nero_normalized.csv

**Особенности**:
- ATR нормализуется отдельным scaler (сохраняется для inference)
- Исключены признаки time_open, symbol (немасштабируемые)

## Quick Reference

| Category | Values |
|----------|--------|
| Tags | documentation, explanation, pipeline |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Looking only at code, not documentation | Check docs/ directory for context |
| Missing DATA_FLOW.md reference | Always cross-reference with data flow |
| Not checking module dependencies | Review MODULE_INDEX.md for full picture |
