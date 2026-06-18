# docs/

Карта документации внутри `docs/`. Общие правила для AI-агентов живут в [`../AGENTS.md`](../AGENTS.md).

| Артефакт | Роль | Когда обновлять | Формат |
|---|---|---|---|
| [`PRD.md`](PRD.md) | Продуктовая цель, scope, критерии успеха | Меняются продуктовые цели, ограничения или scope | Краткие разделы: цель, проблема, требования, риски, product phases |
| [`DATA_FLOW.md`](DATA_FLOW.md) | Source of truth по pipeline, форматам данных и leakage-инвариантам | Меняется поток данных, CSV contract, split, target, inference/export формат | Этапы pipeline: вход, процесс, выход, требования |
| [`ML/online_tester_reconciliation.py.md`](ML/online_tester_reconciliation.py.md) | Инструкция для повторной сверки online/tester `ml_trade_events.csv` | Перед и после online/tester diagnostic-прогонов MT4 | Входы, команда запуска, выходные CSV/JSON, метрики и ограничения |
| [`dataset_description.md`](dataset_description.md) | Формат исходного датасета `Nero.csv` | Меняется структура исходных колонок или смысл признаков | Описание колонок, типов, целевых меток |
| [`reports/`](reports/) | Канонические отчёты завершённых этапов | Завершён этап, получены выводы, изменилось поведение или интерпретация результатов | См. [`reports/README.md`](reports/README.md) |
| [`audit/`](audit/) | Основной регламент разработки и audit-gates для ML-моделей торговых систем, включая leakage preflight | Меняются обязательные проверки, leakage-инварианты, validation/test/forward протокол или типовые ошибки | См. [`audit/README.md`](audit/README.md) |
| [`superpowers/roadmap.md`](superpowers/roadmap.md) | Исторический research roadmap (апрель–май 2026); текущая разработка — [`CONTEXT_HANDOFF.md`](../CONTEXT_HANDOFF.md) | Меняется порядок крупных направлений работ | Короткий ordered backlog + ссылки на планы/отчёты |
| [`superpowers/plans/`](superpowers/plans/) | Исполнимые планы отдельных задач | Перед реализацией многошаговой задачи | Чеклист задач, файлы, проверки, expected outputs |
| [`superpowers/specs/`](superpowers/specs/) | Design/spec материалы | Нужно зафиксировать проектное решение до плана | Контекст, решение, альтернативы, риски |
| `API/`, `ML/`, `MT/`, `processing/`, `statistics/`, `tests/` | Module-level docs | Меняется CLI, назначение, вход/выход или ограничения модуля | Назначение, входы, выходы, запуск, ограничения |
| [`schemas/`](schemas/) | Контракт данных между MT4 и Python (`fractal_v23`/`v24`) | Меняется число полей фрактала, смысл полей или producer в lib_PIC.mqh | JSON Schema с версией, полями, доменами |
| [`archive/`](archive/) | Архив | Не обновлять без явной просьбы | Не читать без явной просьбы |

## Правила обновления

- Новый/изменённый модуль: обновить связанную страницу в `docs/` и строку в [`../MODULE_INDEX.md`](../MODULE_INDEX.md).
- Завершённый этап: создать отчёт в `docs/reports/`, затем обновить `CHANGELOG.md`, `CONTEXT_HANDOFF.md` и при необходимости `wiki/`.
- Документационная правка без продуктового изменения: не добавлять запись в `CHANGELOG.md`.
- После значимых изменений docs/wiki: обновить `wiki/REPO_integrity.md`.
