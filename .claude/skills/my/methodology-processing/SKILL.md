---
name: methodology-processing
description: Use when starting a new ML experiment, auditing features/targets/split, performing leakage checks, or any ML pipeline task
---

# Methodology Processing

Обязывает агента ознакомиться с соответствующим разделом /docs/methodology/.

## Навигация: задача → этап

| Делаешь | Файл |
|---------|------|
| Формулируешь гипотезу, задаёшь gate-критерии, фиксируешь `decision_time` | [00-research-management.md](../../../docs/methodology/00-research-management.md) |
| Аудит сырых данных: источник, формат, producer, момент доступности полей | [01-raw-data-inventory.md](../../../docs/methodology/01-raw-data-inventory.md) |
| Сортировка, нормализация, labelling, split — сборка pipeline | [02-data-pipeline.md](../../../docs/methodology/02-data-pipeline.md) |
| Проверка на утечки: feature contract, future-derived, online mismatch, candidate-source | [03-feature-contract-leakage.md](../../../docs/methodology/03-feature-contract-leakage.md) |
| Разметка целей: label convention, SL/TP/timeout, multi-target | [04-labeling.md](../../../docs/methodology/04-labeling.md) |
| EDA, качество данных, дисбаланс классов, константные признаки | [05-eda-data-quality.md](../../../docs/methodology/05-eda-data-quality.md) |
| Train/validation/locked_test split, событийный ряд, regime shift, sample size gate, walk-forward, роли validation | [06-temporal-split.md](../../../docs/methodology/06-temporal-split.md) |
| Предварительно проверяешь oracle-потолок торговой механики при идеальном знании будущих labels | [06b-oracle-preflight.md](../../../docs/methodology/06b-oracle-preflight.md) |
| Baseline-модели: dummy, простые ML, сравнение | [07-baseline-first.md](../../../docs/methodology/07-baseline-first.md) |
| Обучение: архитектура, seed, кеш, ablation, CPU/GPU | [08-model-development.md](../../../docs/methodology/08-model-development.md) |
| Выбор winner на validation, заморозка перед locked_test, коррекция множественного тестирования | [09-validation-freeze.md](../../../docs/methodology/09-validation-freeze.md) |
| Locked test, OOS, walk-forward | [10-frozen-test-oos.md](../../../docs/methodology/10-frozen-test-oos.md) |
| Устойчивость: по годам, сторонам, seeds, block bootstrap, permutation test | [11-robustness.md](../../../docs/methodology/11-robustness.md) |
| Бэктест: издержки, симулятор, gross/net | [12-backtest-costs.md](../../../docs/methodology/12-backtest-costs.md) |
| Экспорт, MT4 parity, reconciliation | [13-export-mt4-parity.md](../../../docs/methodology/13-export-mt4-parity.md) |
| Forward-test, online diagnostic, новый период | [14-forward-test-online.md](../../../docs/methodology/14-forward-test-online.md) |
| Мониторинг, retraining policy, drift, rollback | [15-monitoring-retraining.md](../../../docs/methodology/15-monitoring-retraining.md) |
| Отчёт, model card, воспроизводимость, работа с багами | [16-reporting-audit.md](../../../docs/methodology/16-reporting-audit.md) |

### Приложения

| Назначение | Файл |
|-----------|------|
| Финальная проверка перед запуском кандидата | [A1-checklist-dev.md](../../../docs/methodology/A1-checklist-dev.md) |
| Аудит готового результата | [A2-checklist-audit.md](../../../docs/methodology/A2-checklist-audit.md) |
| Известные ошибки проекта (реестр) | [A3-typical-false-conclusions.md](../../../docs/methodology/A3-typical-false-conclusions.md) |
| Verdict-статусы и stop conditions | [A4-verdicts-stop-conditions.md](../../../docs/methodology/A4-verdicts-stop-conditions.md) |
| Post-mortem диагностика | [A5-post-mortem-diagnostics.md](../../../docs/methodology/A5-post-mortem-diagnostics.md) |
| Каталог вариантов представления фракталов | [A6-fractal-feature-profile-catalog.md](../../../docs/methodology/A6-fractal-feature-profile-catalog.md) |
| Feature Distribution Audit | [A7-feature-distribution-audit.md](../../../docs/methodology/A7-feature-distribution-audit.md) |
| Канонический каталог признаков и таргетов | [A8-feature-target-catalog.md](../../../docs/methodology/A8-feature-target-catalog.md) |

## Workflow

### Шаг 1. Определи задачу
Что именно делаешь: новый эксперимент, аудит уже пройденного этапа, leakage-проверку, разметку, бэктест?

### Шаг 2. Открой нужный этап по таблице выше
Читай только один файл — соответствующий текущей задаче. Не читай все подряд.

### Шаг 3. Выполни пошаговые действия из файла этапа
Каждый этап содержит: цель, входы, пошаговые действия, обязательные проверки, критерии успеха, типовые ошибки, ветвления.

### Шаг 4. Проверь обязательные проверки этапа
Критерии из этапа должны быть выполнены. Результат не может быть признан качественным, пока не пройдены проверки этапа.

### Шаг 5. Зафиксируй статус

| Статус | Значение |
|--------|----------|
| `PASS` | Этап пройден, можно переходить к следующему |
| `FAIL` | Блокирующий дефект; следующий этап запрещён |
| `UNKNOWN` | Данных недостаточно; считать как `FAIL` |
| `DIAGNOSTIC_ONLY` | Механика pipeline проверена, но вывод о прибыльности/качестве ML делать нельзя |

При `FAIL`/`UNKNOWN` — остановка и формирование отчёта с указанием причины.
При `PASS` — переход к следующему этапу по таблице.

## Сопутствующие документы

- Pipeline и leakage-инварианты: `docs/DATA_FLOW.md`
- Формат датасета: `docs/dataset_description.md`
- Отчёты по прошлым ошибкам: `docs/reports/`
- Wiki: использовать как навигацию, выводы проверять по первичным отчётам
- Реестр модулей: `MODULE_INDEX.md`

## Частые ошибки

| Ошибка | Исправление |
|--------|-------------|
| Пропущен этап — сразу обучение модели | Пройти baseline-first (07) перед model-development (08) |
| Не зафиксирован статус этапа | После завершения явно указать PASS/FAIL/UNKNOWN/DIAGNOSTIC_ONLY |
| Split без учёта событийного ряда | Читать 06-temporal-split.md, учесть regime shift |
| Вывод о прибыльности при DIAGNOSTIC_ONLY | DIAGNOSTIC_ONLY запрещает выводы о качестве ML |
| Использование wiki как истины | Wiki — навигация; выводы сверять с первоисточниками в docs/reports/ |
