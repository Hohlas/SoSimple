# SoSimple Research Roadmap

## Контекст

Проект прошёл несколько веток Track A: quantile/entry-path, take-skip trailing-stop, execution policy в MT4 и проверку разных режимов выхода. Лучший текущий практический результат подтверждён в MT4 через frequency-сигналы и trailing-stop execution, но это всё ещё одна система, построенная на текущем представлении фракталов.

Следующий главный вопрос: можно ли получить новые независимые торговые системы за счёт лучшего использования исходной логики `lib_PIC.mqh` и входных данных, а не за счёт очередной подгонки фильтров поверх уже найденного сигнала.

Подробный текущий handoff: [CONTEXT_HANDOFF.md](../../CONTEXT_HANDOFF.md)

---

## Главный порядок работ

### 0. Live-safe ML audit before online trading

**Контекст:** старые прибыльные ML-результаты нужно отделить от честных
online-safe результатов. Высокий PF больше не считается доказательством, пока
не пройден [`ML Leakage Preflight Checklist`](../ML/ml_leakage_preflight_checklist.md).

**Задача:** повторно проверить `quality`, `frequency`, `original_plus_path`,
`entry_path_v1`, `entry_path_v1_quantile`: воспроизвести старые результаты,
построить паспорт признаков, применить leakage gate и выдать verdict.

**Выход:** `ML/reports/live_safe_ml_audit/`, отчёт в `docs/reports/` и решение,
какие системы можно вести в live-safe retrain / forward validation / online
dry-run.

Spec: [2026-05-05-live-safe-ml-audit-design.md](specs/2026-05-05-live-safe-ml-audit-design.md)

Plan: [2026-05-05-live-safe-ml-audit.md](plans/2026-05-05-live-safe-ml-audit.md)

Report: [2026-05-05-live-safe-ml-audit.md](../reports/2026-05-05-live-safe-ml-audit.md)

Current verdict: `quality`, `frequency`, `original_plus_path` are `FAIL`;
`entry_path_v1` and `entry_path_v1_quantile` are `UNKNOWN`. No system should
go to online trading before the unresolved fields are closed.

### 1. `lib_PIC` feature-source audit

**Контекст:** `lib_PIC.mqh` считает больше рыночного состояния, чем сейчас экспортируется в `Nero.csv` и используется Python-моделью.

**Задача:** построить карту `lib_PIC` -> `Nero.csv` -> Python features -> ML model; отделить проверенные факты от гипотез.

**Выход:** отчёт с картой полей, списком потерянных признаков и рисками утечки будущего.

План: [2026-04-19-lib-pic-feature-source-audit.md](plans/2026-04-19-lib-pic-feature-source-audit.md)

### 2. Current-feature importance diagnostics

**Контекст:** прежде чем менять `lib_PIC`, нужно понять, какие уже экспортируемые признаки реально влияют на результат.

**Задача:** проверить важность групп признаков: геометрия уровня, сила, пробой, импульс, время, ATR, Up/Dn, сводки по окнам.

**Выход:** таблица важности групп, список признаков-кандидатов для усиления и список бесполезных/опасных признаков.

План: [2026-04-19-current-feature-importance-diagnostics.md](plans/2026-04-19-current-feature-importance-diagnostics.md)

Первый отчёт: [2026-04-19-current-feature-importance-diagnostics.md](../reports/2026-04-19-current-feature-importance-diagnostics.md)

### 3. Feature export/design decision

**Контекст:** часть полезных состояний может уже считаться в MQL4, но не попадать в данные.

**Задача:** выбрать один из трёх путей для каждого кандидата:

- построить признак на Python-стороне из уже существующего CSV;
- расширить `Nero.csv` новыми полями;
- изменить сам алгоритм `lib_PIC`.

**Выход:** точная спецификация нового набора входных данных без изменения торговой логики “наугад”.

Первый Python-only шаг: [2026-04-19-lib-pic-geometry-feature-bank.md](plans/2026-04-19-lib-pic-geometry-feature-bank.md)

Отчёт: [2026-04-19-lib-pic-geometry-feature-bank.md](../reports/2026-04-19-lib-pic-geometry-feature-bank.md)

Второй Python-only шаг: [2026-04-19-lib-pic-path-reaction-feature-bank.md](plans/2026-04-19-lib-pic-path-reaction-feature-bank.md)

Отчёт: [2026-04-19-lib-pic-path-reaction-feature-bank.md](../reports/2026-04-19-lib-pic-path-reaction-feature-bank.md)

Сравнение feature-bank вариантов: [2026-04-19-feature-bank-comparison-diagnostics.md](plans/2026-04-19-feature-bank-comparison-diagnostics.md)

Отчёт: [2026-04-19-feature-bank-comparison-diagnostics.md](../reports/2026-04-19-feature-bank-comparison-diagnostics.md)

Clean comparison: [2026-04-19-feature-bank-clean-comparison.md](../reports/2026-04-19-feature-bank-clean-comparison.md)

### 4. New training track with revised inputs

**Контекст:** если диагностика признаков покажет полезные группы, их нужно проверить в новом обучении, а не только в отдельных статистиках.

**Задача:** обучить новый трек с улучшенными входами и заранее зафиксированной целевой постановкой.

**Выход:** validation-first benchmark, frozen test check, MT4-ready signal export only if validation/test не конфликтуют.

### 5. Cross-instrument robustness check

**Контекст:** ждать годы forward-истории непрактично. Более быстрый способ проверить робастность — похожие инструменты.

**Задача:** прогнать текущую систему и будущие кандидаты на других схожих инструментах при той же логике данных и исполнения.

**Выход:** таблица устойчивости по инструментам: сделки, PF, просадка, концентрация прибыли, провалы по периодам.

### 6. System correlation and portfolio check

**Контекст:** цель проекта — не один красивый бэктест, а набор независимых или слабо связанных систем.

**Задача:** сравнить сделки текущих систем: пересечение по времени, совпадение направления, корреляция дневной/недельной прибыли, общие провалы.

**Выход:** матрица совместимости систем и решение, какие системы можно объединять.

### 7. Risk filters only after system discovery

**Контекст:** фильтры поверх уже найденного сигнала часто сокращают сделки и повышают риск подгонки.

**Задача:** применять риск-фильтры только после того, как найден самостоятельный источник прибыли.

**Выход:** отдельный bounded benchmark для фильтра, где заранее ограничены число правил и критерии успеха.

### 8. Central multi-profile inference service

**Контекст:** текущий online telemetry-контур требует отдельного watcher-процесса
для связки `Nero.csv -> ml_signals.csv`. Если появится несколько MT4 experts с
разными ML-моделями, ручной запуск отдельных watcher-ов станет операционным
риском.

**Задача:** заменить ручной single-profile watcher одним Python-сервисом, который
по конфигу обслуживает несколько runtime-профилей: входной `Nero*.csv`,
checkpoint, frozen rule, output `ml_signals*.csv`, state/log/metadata.

**Выход:** managed service без обязательного `tmux`, при сохранении текущего
Python training/inference pipeline и совместимости с Strategy Tester через CSV
exports.

Design note: [2026-04-28-central-inference-service-design.md](specs/2026-04-28-central-inference-service-design.md)

---

## Где держать что

- `CONTEXT_HANDOFF.md` — текущая точка остановки, ближайший следующий шаг, риски.
- `docs/superpowers/roadmap.md` — общий порядок работ между несколькими планами.
- `docs/superpowers/plans/*.md` — детальные исполнимые планы по отдельным направлениям.
- `docs/reports/*.md` — канонические отчёты завершённых этапов.
- `docs/DATA_FLOW.md` — стабильная карта пайплайна, не рабочий список исследований.

---

## Закрытые или superseded направления

Эти направления не удалены из истории, но больше не являются активным roadmap:

- `entry_path_v1_quantile × fav_3_vs_12` composition: закрыто, gate fail.
- `fav_3_vs_12` standalone: закрыто, validation PF слишком слабый.
- `PF uplift beyond ML layer`: использовано как источник идей, но текущий фокус смещён на входные данные и независимые системы.
- старые validation-first / ML-exit / triple-barrier hardening планы: выполнены или superseded более поздними отчётами и MT4-проверками.
