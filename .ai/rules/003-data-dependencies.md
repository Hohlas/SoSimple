---
priority: CONTEXT
trigger: Изменение формата входных/выходных данных в скрипте
affects: Downstream-скрипты, MODULE_INDEX.md, DATA_FLOW.md
description: Проверка влияния изменений данных на зависимые компоненты
tags: data-flow, dependencies, breaking-changes
---

При изменении формата входных/выходных данных:
1. Обнови file header скрипта (секция Зависимости)
2. Обнови DATA_FLOW.md
3. Обнови DATASET_SPEC.md (если изменилась структура CSV)
4. Проверь downstream-скрипты в MODULE_INDEX.md (секция "Используется в")

Используй команду: `check data impact [файл]`
