---
priority: ALWAYS
trigger: Работа с .csv файлами (особенно большими > 10MB)
affects: Контекст ИИ-агента, производительность
description: Запрет загрузки CSV в контекст (использовать sampling/streaming)
tags: csv, performance, memory
---

НИКОГДА не помещай .csv файлы целиком в контекст.

Используй:
- head(10) для просмотра структуры
- describe() для статистики
- sample(100) для анализа паттернов

Для больших операций используй streaming/chunking.
