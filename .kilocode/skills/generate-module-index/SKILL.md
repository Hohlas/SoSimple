---
name: generate-module-index
description: Use when regenerating MODULE_INDEX.md from file headers across all code files
---

# Генерация модуля MODULE_INDEX.md

## Overview

Автоматическое пересоздание MODULE_INDEX.md из file headers во всех кодовых файлах проекта.

## When to Use

- После массовых изменений в структуре проекта
- Когда MODULE_INDEX.md потерял синхронизацию с кодом
- Команды: "rebuild module index", "refresh MODULE_INDEX.md"

## The Workflow

**Команда**: `rebuild module index` или `refresh MODULE_INDEX.md`
**Назначение**: Автоматически пересоздать MODULE_INDEX.md из file headers

Шаги:
1. Найти все .py/.mqh/.ipynb в проекте
2. Извлечь file headers
3. Парсить секции: Назначение, Входные данные, Выходные данные, Зависимости
4. Сгенерировать MODULE_INDEX.md
5. Показать diff и запросить подтверждение

Полезно после массовых изменений или если MODULE_INDEX.md потерял синхронизацию.

## Quick Reference

| Category | Values |
|----------|--------|
| Tags | documentation, automation, index |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Missing file headers | Ensure all files have proper headers first |
| Outdated headers | Update file headers before regenerating index |
| Not reviewing the diff | Always review changes before applying |
