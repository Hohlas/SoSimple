# Context Handoff

Дата: 2026-06-18

## Текущий этап

Fractal Stop находится между Stage 5.0 и Stage 5.0a.

Stage 5.0 Transformer Breach Holdout имеет статус **DIAGNOSTIC_FAIL_WITH_PREPROCESSING_BUG**: первый прогон Transformer был выполнен без фактической нормализации финальных признаков для нейросети. `StandardScaler` был импортирован, но не применён. Абсолютная цена инструмента на длинном периоде 2004-2026 могла кодировать эпоху и доминировать над признаками масштаба 0..1.

Прямой повтор старой команды Stage 5.0 сейчас **не является следующим шагом**. Перед повторным обучением нужен Stage 5.0a Feature Preflight: проверка профилей признаков, распределений, clean-контролей времени/ATR/цены и corridor/relative-price представлений.

## Что уже исправлено в Stage 5.0 runner

1. `normalize_profile_features()` — раздельный StandardScaler для token-признаков и row-признаков; fit только на train; padding остаётся 0.
2. Добавлены relative-price профили: `(fractal_price - fractal0_price) / ATR`.
3. Добавлена OHLC-проверка breach labels.
4. Добавлен `normalized_distribution_audit`: распределения финальных нормализованных признаков, хвосты, NaN/Inf, padding, regime shift.
5. Исправлена проверка хвостов и для token-признаков, и для row-признаков.
6. Тесты Stage 5.0 runner: `53 passed` свежей проверкой.

## Методика обновлена

Новые обязательные ориентиры:

- `docs/methodology/A7-feature-distribution-audit.md` — Feature Distribution Audit до обучения.
- `docs/methodology/A6-fractal-feature-profile-catalog.md` — каталог профилей фракталов, включая corridor/nearest/relative_price.
- `docs/methodology/A5-post-mortem-diagnostics.md` — добавлен разбор признаков убыточных периодов.
- `docs/methodology/08-model-development.md` и `16-reporting-audit.md` — финальный audit масштаба tensor/матриц и reporting требований.

Ключевое правило: нельзя делать вывод “время сильнее фракталов”, если фракталы поданы через абсолютную цену на длинном историческом периоде. Нужны clean-контроли:

- `time_only_clean` — только час/день недели;
- `atr_only` — только ATR/волатильность;
- `time_plus_atr` — время + ATR;
- `relative_price_no_time` — геометрия без календаря;
- `relative_price_time` — геометрия + календарь;
- corridor-профили с координатой цены относительно `fractal0` в ATR.

## Последний зафиксированный результат Stage 5.0

Старый результат без нормализации:

| Метрика | Transformer primary | XGBoost base_raw_plus_time |
|---------|--------------------:|---------------------------:|
| Holdout AUC | 0.6018 | 0.6524 |
| Holdout lift_30 | 0.766 | 0.620 |
| Gate verdict | FAIL | — |

Этот результат остаётся `DIAGNOSTIC_ONLY` и не закрывает Transformer-ветку, потому что pipeline признаков был методически некорректен для нейросети.

## Следующий шаг

Выполнить план:

- `docs/superpowers/plans/2026-06-18-stage5_0a-feature-preflight.md`

Цель Stage 5.0a:

1. Не обучать Transformer.
2. Построить финальные входы тем же feature builder-ом, который будет использовать обучение.
3. До обучения показать распределения и coverage каждого профиля.
4. Проверить, что `time_only` действительно clean-time, а не time+ATR.
5. Сравнить абсолютную цену, no-price, relative-price и corridor-представления.
6. Отдельно проверить, сколько фракталов попадает в corridor 5/10/15 ATR.
7. После отчёта получить согласование пользователя на конкретную матрицу Stage 5.0 rerun.

## Важные риски

- `time_only` в старом Stage 5 runner мог включать ATR; это нужно переименовать или разделить на `time_only_clean` и `time_plus_atr`.
- `nearest_k` должен явно описывать, входит ли `fractal0` в K соседей. Методика A6 говорит: `fractal0` — anchor, не сосед.
- `corridor_10atr` с абсолютной ценой не проверяет чистую фрактальную геометрию; нужен `price_coord_atr`.
- 2023-2026 уже использовался как diagnostic holdout в Stage 4.6/walk-forward. Его нельзя использовать для ручной подгонки профилей.
- Любые выводы Stage 5.0a имеют статус `DIAGNOSTIC_ONLY`, пока не пройдёт новый заранее зафиксированный цикл обучения.

## Файлы

Код:

- `ML/baseline/benchmark_stage5_transformer_breach.py` — Stage 5.0 runner с исправленной нормализацией и distribution audit.
- `ML/models/fractal_breach_transformer.py` — Transformer encoder.
- `tests/test_stage5_transformer_breach.py` — 53 smoke/unit tests.

Документы:

- `docs/reports/2026-06-17-stage5-transformer-breach.md` — старый отчёт Stage 5.0, описывает ненормализованный прогон.
- `ML/reports/stage5_transformer_breach.json` — старый structured result без нормализованного rerun.
- `docs/superpowers/plans/2026-06-16-stage5_0-transformer-breach-holdout.md` — исходный Stage 5.0 plan.
- `docs/superpowers/plans/2026-06-18-stage5_0a-feature-preflight.md` — следующий план.

## Git

Ветка: `feature/fractal-stop-fav-spec`.

На момент обновления handoff есть незакоммиченные изменения документации:

- `CONTEXT_HANDOFF.md`;
- `docs/superpowers/plans/2026-06-18-stage5_0a-feature-preflight.md`;
- `MODULE_INDEX.md`.
