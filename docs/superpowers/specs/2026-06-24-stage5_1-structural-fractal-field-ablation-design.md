# Stage 5.1 — абляция структурных фрактальных полей

> **Date**: 2026-06-24
> **Status**: Draft
> **Level**: поисковый
> **Verdict scope**: `DIAGNOSTIC_ONLY`
> **Goal**: Разобрать, какие структурные фрактальные поля дают добавку сверх clock-признаков в постановке `H6_off05 stop broken`, без выбора торгового кандидата и без новой большой сетки моделей.

## Мотивация

Stage 5.0f дал неопределённый общий вердикт по устойчивости сигнала во времени, но зафиксировал два полезных факта:

1. `structure_only` близок к `base_raw_plus_time`, хотя не содержит `price` и `ATR`.
2. `structure_only` заметно выше `time_only`, значит остаточный сигнал нельзя честно свести только к календарю.

Проблема: `structure_only` всё ещё является смесью 9 фрактальных полей и clock-признаков. Мы знаем, что группа в целом несёт сигнал, но не знаем, какие поля полезны, какие нейтральны, а какие шумят.

Stage 5.1 нужен как узкая диагностика состава признаков перед любой новой целью, включая возможную Stage 5.2 постановку “время до пробоя”. Без этой диагностики следующая цель унаследует шумные поля вслепую.

## Проверяемые поля

Базовый профиль Stage 5.1:

- `selection = all100`
- порядок фракталов: freshness, как в Stage 5.0f
- token-поля: `NO_PRICE_TOKEN_FIELDS`
- row-поля: `TIME_ONLY_ROW_FIELDS`

Фиксированный список структурных token-полей:

| Поле | Статус в Stage 5.1 |
|---|---|
| `direction` | проверяется drop-one и add-one ablation |
| `front` | проверяется drop-one и add-one ablation |
| `back` | проверяется drop-one и add-one ablation |
| `strong` | проверяется drop-one и add-one ablation |
| `break` | проверяется drop-one и add-one ablation |
| `reverse` | проверяется drop-one и add-one ablation |
| `power` | проверяется drop-one и add-one ablation |
| `count` | проверяется drop-one и add-one ablation |
| `impulse` | проверяется drop-one и add-one ablation |

`price`, `price_coord_atr`, `price_atr_scaled` и `ATR` не входят в Stage 5.1. Stage 5.0f уже показал, что удаление price/ATR не разрушает качество и иногда помогает. Stage 5.1 отвечает только на вопрос о внутреннем составе структурного блока.

## Дизайн эксперимента

### Профили

Для каждой цели строятся:

1. `time_only`: только `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos`.
2. `structure_full`: все 9 структурных полей + clock.
3. `drop_direction`: все структурные поля кроме `direction` + clock.
4. `drop_front`: все структурные поля кроме `front` + clock.
5. `drop_back`: все структурные поля кроме `back` + clock.
6. `drop_strong`: все структурные поля кроме `strong` + clock.
7. `drop_break`: все структурные поля кроме `break` + clock.
8. `drop_reverse`: все структурные поля кроме `reverse` + clock.
9. `drop_power`: все структурные поля кроме `power` + clock.
10. `drop_count`: все структурные поля кроме `count` + clock.
11. `drop_impulse`: все структурные поля кроме `impulse` + clock.
12. `add_direction`: `time_only` + `direction`.
13. `add_front`: `time_only` + `front`.
14. `add_back`: `time_only` + `back`.
15. `add_strong`: `time_only` + `strong`.
16. `add_break`: `time_only` + `break`.
17. `add_reverse`: `time_only` + `reverse`.
18. `add_power`: `time_only` + `power`.
19. `add_count`: `time_only` + `count`.
20. `add_impulse`: `time_only` + `impulse`.

`time_only` — обязательный профиль, а не вспомогательная ссылка на Stage 5.0f. Это add-zero точка отсчёта: без неё нельзя понять, приближается ли drop-профиль к `time_only` или остаётся близко к `structure_full`.

Drop-one и add-one отвечают на разные вопросы:

- drop-one: можно ли убрать поле из полного структурного профиля;
- add-one: что поле добавляет к clock-признакам само по себе.

Это нужно из-за коррелированных полей. Например, `front/back`, `strong/break`, `power/count`, `direction/reverse` могут частично дублировать информацию. Drop-one может показать около нулевой дельты для `front`, потому что его роль закрывает `back`; add-one покажет, есть ли у `front` самостоятельная добавка сверх clock.

### Цели

Используются обе цели из Stage 5.0f:

- `sell_stop_broken_H6_off05_flag`
- `buy_stop_broken_H6_off05_flag`

Эти цели уже использовались для диагностического решения и не являются чистым будущим holdout. Поэтому Stage 5.1 не может объявлять кандидата, winner или торговое правило.

### Split

Основной split повторяет модельный контур Stage 5.0d/5.0f:

- `train_core`: данные до 2020 включительно
- `val_stop`: 2021-2022, early stopping и первичная оценка
- `diagnostic_holdout`: 2023-2025, только раскрытие устойчивости дельт
- `low_n_disclosure`: 2026, опционально и отдельно, без влияния на вывод

`2023-2025` уже сожжены Stage 5.0f для управленческой диагностики. В Stage 5.1 их можно использовать только как diagnostic disclosure: “дельта держится/не держится на уже раскрытых годах”.

Для совместимости с Stage 5.0d основной `val_auc` считается как один AUC на объединённом `val_stop` 2021-2022. Дополнительно нужно записать yearly val AUC за 2021 и 2022, чтобы видеть смену знака дельты между годами.

`holdout_2023_2025_auc_median` — отдельная метрика на объединённом diagnostic-holdout 2023-2025. Она не заменяет yearly breakdown: AUC за 2023, 2024 и 2025 записываются отдельно и используются для проверки устойчивости знака.

Sanity check: `structure_full` Stage 5.1 должен быть близок к смыслу `no_price`/`structure_only` из Stage 5.0d/5.0f: фрактальная структура + clock, без price/ATR. Если AUC `structure_full` резко не похож на предыдущие значения, сначала проверять сборку признаков и split, а не интерпретировать абляцию.

### Модель

Только XGBoost, без Transformer и без торговой симуляции.

Причины:

- Stage 5.0c/5.0e показали, что Transformer на текущем `H6_off05` не превосходит XGBoost.
- Stage 5.1 исследует поля, а не архитектуры.
- Торговая симуляция добавит шум механики выхода и не поможет понять вклад признаков.

Семена: `[42, 77, 123]`, результат агрегируется median по seed.

Transform variant: `asinh`, как в поздних Stage 5.0b-5.0f. Для `time_only`, `structure_full`, drop-one и add-one профилей нет `ATR` и price-like token-полей, поэтому train-only `transform_params` должны быть пустыми (`{}`) и одинаковыми по смыслу для всех Stage 5.1 профилей. Это всё равно нужно явно записать в JSON как `transform_params_fit_on = train_core` и `transform_params = {}`, чтобы исключить двусмысленность про утечку.

Ожидаемый бюджет:

- 20 профилей × 2 цели × 3 seed = 120 XGBoost-моделей.
- Это включает `time_only`, `structure_full`, 9 drop-one профилей и 9 add-one профилей.
- Опциональный `drop_all_noise` добавляет ещё 2 цели × 3 seed = 6 моделей, если после основного прогона 2-3 поля получают устойчивый `likely_noise`.

## Multiple Testing Context

Stage 5.1 содержит множественный перебор:

- 9 структурных полей;
- 2 режима абляции: drop-one и add-one;
- 2 цели;
- 3 seed;
- несколько периодов оценки: объединённый `val_stop`, yearly val, объединённый 2023-2025 и yearly 2023-2025.

Коррекция вроде Bonferroni не применяется, потому что этап `DIAGNOSTIC_ONLY` и не выбирает кандидата. Но это ограничивает язык вывода: `likely_useful` и `likely_noise` означают предварительный диагностический рисунок, а не статистически подтверждённую полезность поля.

В отчёте обязательно указать, что при таком числе сравнений часть малых дельт может появиться случайно. Для будущей постановки допускается использовать только устойчивые и интерпретируемые группы, а не одиночный лучший профиль по AUC.

## Метрики

Основные метрики:

- `val_auc_median`
- yearly val AUC: 2021, 2022
- `val_lift_30_median`
- `holdout_2023_2025_auc_median`
- yearly AUC на 2023, 2024, 2025
- delta к `structure_full` по каждому полю
- delta к `time_only` для add-one профилей
- seed-level min/median/max для каждой delta
- bootstrap CI для AUC и delta на объединённом `val_stop` и объединённом 2023-2025

`lift_30` трактуется так же, как в Stage 5.0f: bottom-30 risk lift, где меньше = лучше. Это не top-k enrichment.

Главные величины:

```text
delta_drop_field = AUC(drop_field) - AUC(structure_full)
delta_add_field = AUC(add_field) - AUC(time_only)
```

Интерпретация:

- `delta_drop_field < 0`: удаление поля ухудшило AUC, поле выглядит полезным.
- `delta_drop_field ≈ 0`: поле нейтрально в этой постановке.
- `delta_drop_field > 0`: удаление поля улучшило AUC, поле выглядит шумным или вредным.
- `delta_add_field > 0`: поле само добавляет сигнал сверх clock.
- `delta_add_field ≈ 0`: поле само по себе не даёт видимой добавки сверх clock.

CI можно считать так же, как в Stage 5.0f: bootstrap по строкам сэмплирует test/val rows с возвращением, пересчитывает AUC, затем в summary записывается median от per-seed CI bounds. Для delta предпочтительно считать paired bootstrap на одних и тех же строках: на каждом bootstrap-sample пересчитать `AUC(profile_a) - AUC(profile_b)`. Если реализация paired delta CI окажется слишком дорогой, минимально допустимый вариант — seed-level spread и устойчивость знака по seed, но это нужно явно раскрыть в отчёте.

Категории `field_verdicts`:

- `likely_useful`: для хотя бы одной цели `delta_drop_field < 0` на объединённом `val_stop` и минимум на 2 из 3 yearly holdout-лет; знак `delta_drop_field` устойчив минимум в 2 из 3 seed на `val_stop`; `delta_add_field > 0` на объединённом `val_stop` или объединённом 2023-2025.
- `likely_noise`: для хотя бы одной цели `delta_drop_field > 0` на объединённом `val_stop` и минимум на 2 из 3 yearly holdout-лет; знак `delta_drop_field` устойчив минимум в 2 из 3 seed на `val_stop`; `delta_add_field <= 0` на объединённом `val_stop`.
- `mixed_or_unclear`: знак дельты меняется по цели, году или seed.

Не вводить PASS/FAIL для отдельных полей. Это карта признаков, не отбор winner-а.

Если 2-3 поля получают `likely_noise`, разрешён один дополнительный профиль `drop_all_noise`: `structure_full` минус все эти поля. Это не новый поиск winner-а, а sanity check совместного удаления шумных полей. Если шумных полей больше трёх, `drop_all_noise` не запускать в Stage 5.1: это уже новая сетка.

## Выходной артефакт

Структурированный JSON:

```text
ML/reports/stage5_1_structural_field_ablation.json
```

Минимальная структура:

- `stage`
- `status = DIAGNOSTIC_ONLY`
- `targets`
- `fields`
- `seeds`
- `profiles`
- `raw_runs`
- `summary`
- `field_verdicts`
- `multiple_testing_context`
- `holdout_disclosure`
- `transform_config`
- `sanity_checks`

Канонический отчёт:

```text
docs/reports/YYYY-MM-DD-stage5_1-structural-field-ablation.md
```

Отчёт должен явно сказать:

- Stage 5.1 не выбирает кандидата.
- `2023-2025` используются только как раскрытая диагностика.
- Если поле выглядит шумным, это не означает, что оно вредно во всех будущих целях.
- Если поле выглядит полезным, это не означает, что оно создаёт торговую прибыль.

## Решение после этапа

Stage 5.1 может дать только управленческие выводы для следующей постановки:

1. **Есть компактное устойчивое ядро полей.** Следующий этап может проектировать новую цель вокруг этого ядра, например “время до пробоя”.
2. **Все поля дают смешанные или малые дельты.** Значит `structure_only` работает как слабая сумма множества признаков; агрессивно сокращать профиль нельзя.
3. **Удаление нескольких полей улучшает качество.** Следующая постановка должна исключить эти поля из стартового профиля, но только как предварительное ограничение, не как доказанный winner.
4. **Drop-one и add-one расходятся.** Если drop-one показывает ноль, а add-one положительный, поле вероятно дублируется другими полями. Если drop-one отрицательный, а add-one нулевой, поле полезно только во взаимодействии с остальными.

Запрещённые выводы:

- “Поле X доказанно полезно для торговли.”
- “Поле X надо навсегда удалить из всех Fractal Stop задач.”
- “H6_off05 переоткрыт.”
- “Stage 5.2 можно считать подтверждённой до нового протокола.”

## Риски

1. **Коррелированные поля.** Add-one снижает риск недооценки отдельных полей, но не решает полностью взаимодействия между парами и тройками признаков.
2. **Слабые дельты.** Разницы AUC могут быть меньше шума годовых выборок. Поэтому нужен median по seed и осторожная категория `mixed_or_unclear`.
3. **Сожжённый holdout.** 2023-2025 нельзя использовать для выбора будущего кандидата. Результат Stage 5.1 должен оставаться диагностикой.
4. **Clock остаётся в профиле.** `structure_full` и drop-one профили содержат clock-признаки. Поэтому вывод звучит как “поле добавляет к structure+clock”, а не как “чистая фрактальная причинность”.
5. **Старый target.** `H6_off05` исчерпан как кандидат, но остаётся пригодным диагностическим стендом для анализа признаков.

## Связанные материалы

- `docs/superpowers/roadmap.md`
- `docs/reports/2026-06-24-stage5_0f-signal-stationarity.md`
- `ML/reports/stage5_0f_signal_stationarity.json`
- `docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md`
- `ML/reports/stage5_0d_diagnostic_screening.json`
- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `tests/test_stage5_transformer_breach.py`
