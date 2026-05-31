# Методика разработки и аудита ML-моделей торговых систем

> Статус: основной пайплайн разработки и аудита ML-моделей торговых систем в проекте SoSimple.
> Область: ML-модели торговых систем на событийных и временных данных Forex.
> Роль в проекте: управляющий документ качества ML-разработки. `docs/DATA_FLOW.md` описывает маршрут данных, а эта методика задаёт обязательные проверки, критерии перехода между этапами и правила интерпретации результатов.
> Главный принцип: результат нельзя считать качеством модели, пока не доказано, что данные, признаки, разметка, split, правило отбора, экспорт и исполнение соответствуют моменту торгового решения.
> Для live-кандидатов цена входа в label/backtest должна быть исполнима после фактической доступности признаков и runtime-задержек; более ранний вход допускается только как `DIAGNOSTIC_ONLY`.

## Как использовать

Методика применяется к любому новому ML-кандидату: классификации направления, регрессии MFE/MAE, take/skip, triple barrier, фильтру сигналов, execution-policy или модели выбора стороны сделки.

Каждый этап — отдельный файл. Не читай все файлы подряд: найди нужный этап в таблице ниже и открой только его.

Каждый этап имеет одинаковую структуру:

- цель;
- входы;
- пошаговые действия;
- обязательные проверки;
- критерии успешного завершения;
- типовые ошибки;
- ветвления по результатам проверки.

Результат этапа получает один из статусов:

| Статус | Значение |
|---|---|
| `PASS` | Этап прошёл обязательные проверки, можно переходить дальше |
| `FAIL` | Найден блокирующий дефект; следующий этап запрещён |
| `UNKNOWN` | Данных недостаточно; считать как `FAIL`, пока не доказано обратное |
| `DIAGNOSTIC_ONLY` | Можно проверять механику pipeline, но нельзя делать вывод о прибыльности или качестве ML |

Главные источники для сверки:

- pipeline и leakage-инварианты: [`docs/DATA_FLOW.md`](../DATA_FLOW.md);
- формат датасета: [`docs/dataset_description.md`](../dataset_description.md);
- отчёты по прошлым ошибкам: [`docs/reports/`](../reports/);
- wiki использовать как навигацию, но выводы проверять по первичным отчётам.

## Навигация: задача → файл

| Делаешь | Файл |
|---------|------|
| Формулируешь гипотезу, задаёшь gate-критерии, фиксируешь `decision_time` | [00-research-management.md](00-research-management.md) |
| Аудит сырых данных: источник, формат, producer, момент доступности полей | [01-raw-data-inventory.md](01-raw-data-inventory.md) |
| Сортировка, нормализация, labelling, split — сборка pipeline | [02-data-pipeline.md](02-data-pipeline.md) |
| Проверка на утечки: feature contract, future-derived, online mismatch, candidate-source | [03-feature-contract-leakage.md](03-feature-contract-leakage.md) |
| Разметка целей: label convention, SL/TP/timeout, multi-target | [04-labeling.md](04-labeling.md) |
| EDA, качество данных, дисбаланс классов, константные признаки | [05-eda-data-quality.md](05-eda-data-quality.md) |
| Train/val/test split, событийный ряд, regime shift, walk-forward | [06-temporal-split.md](06-temporal-split.md) |
| Baseline-модели: dummy, простые ML, сравнение | [07-baseline-first.md](07-baseline-first.md) |
| Обучение: архитектура, seed, кеш, ablation, CPU/GPU | [08-model-development.md](08-model-development.md) |
| Выбор winner на validation, заморозка перед test | [09-validation-freeze.md](09-validation-freeze.md) |
| Frozen test, OOS, walk-forward | [10-frozen-test-oos.md](10-frozen-test-oos.md) |
| Устойчивость: по годам, сторонам, seeds, provider drift, transfer | [11-robustness.md](11-robustness.md) |
| Бэктест: издержки, симулятор, gross/net | [12-backtest-costs.md](12-backtest-costs.md) |
| Экспорт, MT4 parity, reconciliation | [13-export-mt4-parity.md](13-export-mt4-parity.md) |
| Forward-test, online diagnostic, новый период | [14-forward-test-online.md](14-forward-test-online.md) |
| Мониторинг, retraining policy, drift, rollback | [15-monitoring-retraining.md](15-monitoring-retraining.md) |
| Отчёт, model card, воспроизводимость, работа с багами | [16-reporting-audit.md](16-reporting-audit.md) |

## Приложения

| Назначение | Файл |
|-----------|------|
| Финальная проверка перед запуском кандидата | [A1-checklist-dev.md](A1-checklist-dev.md) |
| Аудит готового результата | [A2-checklist-audit.md](A2-checklist-audit.md) |
| Известные ошибки проекта (реестр) | [A3-typical-false-conclusions.md](A3-typical-false-conclusions.md) |
| Verdict-статусы и stop conditions | [A4-verdicts-stop-conditions.md](A4-verdicts-stop-conditions.md) |
