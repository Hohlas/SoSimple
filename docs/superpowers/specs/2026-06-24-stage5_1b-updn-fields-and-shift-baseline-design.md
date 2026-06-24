# Stage 5.1b — абляция Up/Dn полей с расширенным baseline (clock + shift)

> **Date**: 2026-06-24
> **Status**: Draft
> **Level**: поисковый
> **Verdict scope**: `DIAGNOSTIC_ONLY`
> **Goal**: Проверить самостоятельный сигнал 10 полей Up/Dn из `fractalN` (максимальный уже накопленный отход цены от уровня за горизонты 3-48 баров) и пересчитать абляцию 9 структурных полей против усиленного baseline (`clock + shift`), чтобы исключить риск, что полезность поля является артефактом возраста фрактала.

## Мотивация

### Проблема 1: непроверенные Up/Dn поля

Stage 5.1 тестировал только 9 структурных полей (`direction`, `front`, `back`, `strong`, `break`, `reverse`, `power`, `count`, `impulse`). В `Nero.csv` есть ещё 10 полей Up/Dn — максимальный отход цены от фрактального уровня за горизонты 3, 6, 12, 24, 48 баров в обе стороны. Эти поля несут принципиально иную информацию: 9 структурных описывают *сам уровень*, Up/Dn описывают *поведение цены после него*. Экономический смысл прямой: если цена уже далеко ушла от уровня, она реже к нему вернётся.

### Проблема 2: слабый baseline

Stage 5.1 использовал `clock` (hour/dow) как add-zero baseline. Но `shift` — возраст фрактала в барах от `decision_time` — тоже live-safe и не фрактальное поле в смысле структуры уровня. Без `shift` в baseline модель не знает, насколько свежая структура перед ней. Поля, коррелирующие с возрастом фрактала (например, `back` — сила тыловой границы, которая формируется со временем), могут казаться полезными только потому, что кодируют `shift`. Включение `shift` в baseline делает add-one тест честнее: поле должно показать сигнал сверх календаря **и** возраста.

### Почему перезапуск, а не дополнение

Смешивать результаты против разных baselines в одной таблице нельзя. Старый Stage 5.1 остаётся в архиве как `DIAGNOSTIC_ONLY` с clock-only baseline. Stage 5.1b вводит `clock + shift` как новый baseline и перегоняет все 9 старых полей + 10 новых Up/Dn полей против него.

### Live-safe статус новых полей

**Up/Dn.** `LEVELS_FIND_AROUND()` в `lib_PIC.mqh:378-408` обновляет Up/Dn инкрементально на каждом баре: `hmp = H - F[f].P` (текущий High минус цена фрактала), `pml = F[f].P - L`. Накопление идёт от формирования фрактала к текущему бару — только прошлые данные. CSV пишется в `NERO_CSV_CREATE(bar)`. Методология (`03-feature-contract-leakage.md:136-138`) требует доказать, что Up/Dn накоплены producer-ом, а не пересчитаны Python по будущим барам. Для Stage 5.1b это должно быть подтверждено отдельным preflight-аудитом, потому что в labeled CSV также существуют одноимённые top-level колонки `up_3..dn_48`, которые являются будущими target-метками и не могут использоваться как признаки.

**shift.** `shift = SHIFT(F[f].T) - cur_bar` (`lib_PIC.mqh:901`) — расстояние от времени формирования фрактала до текущего бара. Вычисляется в `NERO_CSV_CREATE(cur_bar)` до записи строки. **Только прошлые данные, live-safe.**

## Обязательный preflight перед полным прогоном

Полный прогон на 250+ XGBoost-моделей запускать только после дешёвого preflight-аудита на `train_core` и `val_stop`.

Проверки:

1. **Источник Up/Dn.** Признаки должны извлекаться только из строк `fractal0..fractal99`, индексы 11-20 по `docs/schemas/fractal_v24_raw_price.schema.json`. Запрещено читать top-level колонки `up_3`, `dn_3`, ..., `up_48`, `dn_48`, потому что они создаются `label_updn()` как будущие метки текущей строки.
2. **Контракт фрактала.** Для каждой строки фрактала проверить длину 23 поля, порядок индексов и отсутствие silent-fallback к нулям сверх ожидаемой доли пустых fractal slots.
3. **Монотонность горизонтов.** Для каждого непустого фрактала проверить `up_3 <= up_6 <= up_12 <= up_24 <= up_48` и аналогично для `dn_*`. Нарушения >0 должны попадать в JSON и отчёт.
4. **Maturity по горизонту.** Up/Dn за горизонт `H` полностью наблюдаемы только если `shift >= H`. Если `shift < H`, поле содержит частично накопленный путь и неизбежно кодирует возраст фрактала. Поэтому нужно записать доли mature/non-mature по каждому горизонту и цели.
5. **Shift distribution.** Записать p50/p90/p95/max `shift` по train/val/holdout/2026 и доли `shift >= 3/6/12/24/48`.
6. **Корреляция Up/Dn с shift.** Для каждого поля записать Spearman/Pearson с `log1p(shift)` на train. Если группа почти полностью объясняется возрастом, это должно ограничить интерпретацию `add_*`.
7. **Единицы измерения.** Up/Dn в raw price units. Записать распределения `updn/ATR` как sanity disclosure, но не добавлять ATR как feature в основной Stage 5.1b, чтобы не расширять эксперимент.

Если preflight показывает, что Up/Dn фактически читаются из target-колонок, нарушают контракт или имеют массовые нарушения монотонности, Stage 5.1b останавливается без полного обучения.

## Проверяемые поля

### Структурные поля (9, повтор из Stage 5.1)

| Поле | CSV index | Смысл |
|---|---:|---|
| `direction` | 2 | Направление пробоя уровня |
| `front` | 3 | Сила фронтальной границы |
| `back` | 4 | Сила тыловой границы |
| `strong` | 5 | Флаг сильного уровня |
| `break` | 6 | Флаг пробойного уровня |
| `reverse` | 7 | Сила разворота |
| `power` | 8 | Сумма сил фракталов на уровне |
| `count` | 9 | Количество касаний уровня |
| `impulse` | 10 | Импульс/сила пробоя |

### Up/Dn поля (10, новые)

| Поле | CSV index | Смысл |
|---|---:|---|
| `up_3` | 17 | Макс. движение вверх за 3 бара от уровня |
| `dn_3` | 18 | Макс. движение вниз за 3 бара |
| `up_6` | 19 | Макс. движение вверх за 6 баров |
| `dn_6` | 20 | Макс. движение вниз за 6 баров |
| `up_12` | 11 | Макс. движение вверх за 12 баров |
| `dn_12` | 12 | Макс. движение вниз за 12 баров |
| `up_24` | 13 | Макс. движение вверх за 24 бара |
| `dn_24` | 14 | Макс. движение вниз за 24 бара |
| `up_48` | 15 | Макс. движение вверх за 48 баров |
| `dn_48` | 16 | Макс. движение вниз за 48 баров |

### Baseline-поля

| Поле | Тип | Смысл |
|---|---|---|
| `hour_sin`, `hour_cos` | row | Циклическое кодирование часа суток |
| `dow_sin`, `dow_cos` | row | Циклическое кодирование дня недели |
| `shift` | token | log1p(shift) — возраст фрактала в барах, лог-масштабированный |

`shift` — token-level (возраст разный для каждого фрактала в строке), как и структурные поля. Используется `log1p(shift)`, а не сырой `shift`, для сжатия тяжёлого правого хвоста (возраст может быть 0-200+ баров).

## Дизайн эксперимента

### Профили

Для каждой цели строятся:

**Baselines:**

1. `clock_shift`: `clock + shift` (token: `[shift]`, row: `[hour_sin, hour_cos, dow_sin, dow_cos]`). Если в коде ради совместимости используется старый ключ `time_only`, в отчёте он должен называться `clock_shift`, чтобы не путать с Stage 5.1 clock-only baseline.
2. `structure_full`: 9 структурных + `clock + shift`.
3. `updn_full`: 10 Up/Dn + `clock + shift`.
4. `structure_plus_updn`: 9 структурных + 10 Up/Dn + `clock + shift`.
5. `back_impulse_combo`: `clock + shift + back + impulse`.

**Drop-one (19 полей):**

6-14. `drop_<field>` для каждого из 9 структурных полей: `structure_full` минус поле.
15-24. `drop_<field>` для каждого из 10 Up/Dn полей: `updn_full` минус поле.

**Add-one (19 полей):**

25-33. `add_<field>` для каждого из 9 структурных полей: `clock_shift` + поле.
34-43. `add_<field>` для каждого из 10 Up/Dn полей: `clock_shift` + поле.

`back_impulse_combo` добавлен как заранее заданный мини-follow-up из Stage 5.1: он проверяет, закрывает ли пара `back + impulse` большую часть `structure_full` без нового широкого поиска. Это не winner-кандидат, а диагностическое сравнение.

Drop-one и add-one отвечают на разные вопросы:

- drop-one: можно ли убрать поле из полного профиля (его роль закрывают другие);
- add-one: что поле добавляет к baseline само по себе.

### Цели

Используются обе цели из Stage 5.0f / 5.1:

- `sell_stop_broken_H6_off05_flag`
- `buy_stop_broken_H6_off05_flag`

Эти цели уже использовались для диагностического решения и не являются чистым будущим holdout. Stage 5.1b не объявляет кандидата, winner или торговое правило.

### Split

Основной split повторяет Stage 5.1:

- `train_core`: данные до 2020 включительно
- `val_stop`: 2021-2022, early stopping и первичная оценка
- `diagnostic_holdout`: 2023-2025, только раскрытие устойчивости дельт
- `low_n_disclosure`: 2026, опционально и отдельно, без влияния на вывод

`2023-2025` уже сожжены Stage 5.0f. В Stage 5.1b — diagnostic disclosure только.

Для совместимости с Stage 5.1 основной `val_auc` считается как один AUC на объединённом `val_stop` 2021-2022. Дополнительно записывается yearly val AUC за 2021 и 2022.

`holdout_2023_2025_auc_median` — отдельная метрика на объединённом diagnostic-holdout 2023-2025. Yearly AUC за 2023, 2024, 2025 записываются отдельно.

### Sanity checks

1. `structure_full` Stage 5.1b должен быть близок к `structure_full` Stage 5.1 (отличие только в добавлении `shift` как token-поля). Если AUC резко изменился — проверять сборку признаков.
2. `clock_shift` Stage 5.1b должен быть ≥ `time_only` Stage 5.1 (clock only). `shift` содержит информацию; если он не помогает, это отдельный диагностический факт.
3. `updn_full` vs `structure_full`: сравнение двух групп полей «на равных» против общего baseline.
4. `back_impulse_combo` должен сравниваться с `structure_full`, а не только с `clock_shift`: если gap большой, `back + impulse` не заменяют полный профиль.

### Модель

Только XGBoost, без Transformer и без торговой симуляции.

Причины те же, что в Stage 5.1:
- Stage 5.0c/5.0e показали, что Transformer не превосходит XGBoost на `H6_off05`.
- Stage 5.1b исследует поля, а не архитектуры.
- Торговая симуляция добавит шум механики выхода.

Семена: `[42, 77, 123]`, результат агрегируется median по seed.

Transform variant: `asinh`, как в Stage 5.1. Для всех профилей нет `ATR` и price-like token-полей; `shift` лог-масштабируется через `log1p`. Up/Dn остаются в raw price units в основном эксперименте. Поэтому `transform_params` должны быть пустыми (`{}`). Записать в JSON: `transform_params_fit_on = train_core` и `transform_params = {}`.

Ожидаемый бюджет:

- 5 baselines/контролей + 19 drop-one + 19 add-one = 43 профиля.
- 43 × 2 цели × 3 seed = 258 XGBoost-моделей.
- Оценка: ~4-5 часов (Stage 5.1 = 120 прогонов за 2.5ч).

## Групповой анализ Up/Dn

Up/Dn поля естественным образом образуют 5 пар по направлению (up/dn) × 5 горизонтов (3, 6, 12, 24, 48). Помимо индивидуальных verdicts, в отчёте проверить:

1. **По направлению:** усреднить drop/add дельты по всем up_* и по всем dn_*. Есть ли асимметрия? Логично, что для `sell_stop_broken` (пробой sell-stop) `up_*` (движение вверх от уровня) может быть сильнее, а для `buy_stop_broken` — `dn_*`.
2. **По горизонту:** усреднить drop/add дельты по горизонтам 3, 6, 12, 24, 48. Есть ли паттерн «короткие горизонты сильнее/слабее длинных»?
3. **Группа vs структура:** сравнить `updn_full` и `structure_full` — какая группа даёт больше премии над baseline.
4. **Maturity-aware разбор:** для горизонтов 12/24/48 отдельно проверить, не возникает ли основной эффект только на non-mature фракталах (`shift < H`). Если да, это скорее возрастной/цензурный эффект, а не устойчивый сигнал поля.

Это групповой анализ, не индивидуальный verdict. Его цель — сгенерировать гипотезы для Stage 5.2, не подтвердить их.

## Multiple Testing Context

Stage 5.1b содержит множественный перебор:

- 19 полей (9 структурных + 10 Up/Dn);
- 2 режима абляции: drop-one и add-one;
- 2 цели;
- 3 seed;
- несколько периодов оценки: объединённый `val_stop`, yearly val, объединённый 2023-2025, yearly 2023-2025.

Коррекция вроде Bonferroni не применяется (`DIAGNOSTIC_ONLY`, не выбирает кандидата). Но это ограничивает язык вывода: `likely_useful` и `likely_noise` означают предварительный диагностический рисунок, а не статистически подтверждённую полезность поля.

В отчёте указать, что при 19 полях × 2 режимах × 2 целях = 76 сравнений, часть малых дельт может появиться случайно. Для будущей постановки допускается использовать только устойчивые и интерпретируемые группы.

## Метрики

Основные метрики:

- `val_auc_median`
- yearly val AUC: 2021, 2022
- `val_lift_30_median`
- `holdout_2023_2025_auc_median`
- yearly AUC на 2023, 2024, 2025
- `low_n_2026_auc` (опционально, disclosure only)
- delta к `structure_full` для drop-one структурных полей
- delta к `updn_full` для drop-one Up/Dn полей
- delta к `clock_shift` для add-one всех полей
- seed-level min/median/max для каждой delta
- bootstrap CI для AUC и delta на объединённом `val_stop` и объединённом 2023-2025

`lift_30` трактуется как bottom-30 risk lift, где меньше = лучше.

Главные величины:

```text
# Структурные поля
delta_drop_struct_field = AUC(drop_struct_field) - AUC(structure_full)
delta_add_struct_field  = AUC(add_struct_field)  - AUC(clock_shift)

# Up/Dn поля
delta_drop_updn_field = AUC(drop_updn_field) - AUC(updn_full)
delta_add_updn_field  = AUC(add_updn_field)  - AUC(clock_shift)

# Групповые сравнения
delta_updn_group      = AUC(updn_full)         - AUC(clock_shift)
delta_structure_group = AUC(structure_full)    - AUC(clock_shift)
delta_combined        = AUC(structure_plus_updn) - AUC(structure_full)
delta_back_impulse    = AUC(back_impulse_combo) - AUC(clock_shift)
gap_back_impulse_full = AUC(back_impulse_combo) - AUC(structure_full)
```

Интерпретация delta_drop и delta_add — та же, что в Stage 5.1:

- `delta_drop < 0`: удаление ухудшило, поле полезно в составе.
- `delta_drop ≈ 0`: поле нейтрально.
- `delta_drop > 0`: удаление улучшило, поле шумит.
- `delta_add > 0`: поле само добавляет сигнал над baseline.
- `delta_add ≈ 0`: поле само по себе не даёт добавки.

### Категории field_verdicts

Те же, что в Stage 5.1, с уточнением для двух групп:

- `target_likely_useful`: для конкретной цели `delta_drop < 0` на объединённом `val_stop` И (`CI_high < 0` ИЛИ `neg_seeds == 3`); `delta_add > 0` на объединённом `val_stop`.
- `target_likely_noise`: для конкретной цели `delta_drop > 0` на объединённом `val_stop` И (`CI_low > 0` ИЛИ `pos_seeds == 3`); `delta_add <= 0` на объединённом `val_stop`.
- `overall_likely_useful`: обе цели получили `target_likely_useful`, без противоположного `target_likely_noise`.
- `overall_likely_noise`: обе цели получили `target_likely_noise`, без противоположного `target_likely_useful`.
- `target_specific_signal`: только одна цель получила `target_likely_useful` или `target_likely_noise`, а вторая осталась `mixed_or_unclear`.
- `mixed_or_unclear`: знак дельты меняется по цели, году или seed; либо есть конфликт useful/noise между целями.

Drop-one для Up/Dn полей считается относительно `updn_full`, а не `structure_full`. Это важно: поле может быть шумным внутри своей группы, но полезным в смешанном профиле. Для проверки второго нужен `structure_plus_updn` baseline, но полный drop-one от `structure_plus_updn` (19 полей × 2 цели × 3 seed = 114 прогонов) удвоит стоимость. Поэтому в Stage 5.1b drop-one от `structure_plus_updn` не делается; если групповой анализ покажет перспективное поле, оно проверяется в отдельном мини-follow-up.

Не вводить PASS/FAIL для отдельных полей. Это карта признаков, не отбор winner-а.

## Выходной артефакт

Структурированный JSON:

```text
ML/reports/stage5_1b_updn_field_ablation.json
```

Минимальная структура:

- `stage`: `"5.1b"`
- `status`: `"DIAGNOSTIC_ONLY"`
- `baseline`: `"clock + shift (log1p)"`
- `targets`
- `fields` (19: 9 структурных + 10 Up/Dn)
- `seeds`
- `profiles` (43: 5 baselines/контролей + 19 drop-one + 19 add-one)
- `raw_runs`
- `summary` (per-profile per-target: val_auc_median, holdout_auc_median, yearly, lift_30, CI)
- `field_verdicts` (per-field per-target: drop delta, add delta, CI, seed counts, yearly signs, verdict)
- `group_analysis` (up vs dn, по горизонтам, updn_full vs structure_full)
- `preflight` (источник Up/Dn, монотонность, maturity по горизонтам, shift distribution, корреляция Up/Dn с shift)
- `multiple_testing_context`
- `holdout_disclosure`
- `transform_config`
- `sanity_checks` (structure_full vs 5.1, clock_shift vs 5.1 time_only, updn_full vs structure_full, back_impulse_combo vs structure_full)

Канонический отчёт:

```text
docs/reports/YYYY-MM-DD-stage5_1b-updn-field-ablation.md
```

Отчёт должен явно сказать:

- Stage 5.1b не выбирает кандидата.
- `2023-2025` используются только как раскрытая диагностика.
- Baseline изменён с clock-only (5.1) на clock + shift (5.1b); результаты 5.1 и 5.1b не сравнимы напрямую по absolute AUC, только по структуре выводов.
- Если поле выглядит шумным, это не означает, что оно вредно во всех будущих целях.
- Если поле выглядит полезным, это не означает, что оно создаёт торговую прибыль.

## Решение после этапа

Stage 5.1b может дать управленческие выводы для следующей постановки:

1. **Up/Dn поля дают устойчивый самостоятельный сигнал.** Следующая постановка (Stage 5.2) должна включать Up/Dn в стартовый профиль.
2. **Up/Dn поля не дают сигнала над clock + shift.** Up/Dn — шум для `H6_off05`; Stage 5.2 не должен включать их по умолчанию.
3. **Структурные поля меняют verdict при добавлении shift в baseline.** Поле, которое было `likely_useful` в 5.1, стало `mixed_or_unclear` в 5.1b — его сигнал частично объяснялся возрастом фрактала.
4. **Структурные поля не меняют verdict.** Shift не конфаундит структурные поля; выводы 5.1 устойчивы.
5. **Групповой паттерн по направлению или горизонту.** Например, `up_*` сильнее на sell, `dn_*` на buy — гипотеза для Stage 5.2.
6. **`back_impulse_combo` близок к `structure_full`.** Тогда следующий диагностический шаг можно строить вокруг компактного профиля `clock+shift+back+impulse`, но только на новом независимом периоде или как явно диагностический mini-cycle.
7. **`back_impulse_combo` заметно хуже `structure_full`.** Тогда Stage 5.1 вывод про `back` остаётся полезным для понимания, но не даёт компактной замены структурного профиля.

Запрещённые выводы:

- "Поле X доказанно полезно для торговли."
- "Поле X надо навсегда удалить из всех Fractal Stop задач."
- "H6_off05 переоткрыт."
- "Stage 5.2 можно считать подтверждённой до нового протокола."
- "Результаты Stage 5.1 недействительны." (5.1 остаётся валидной диагностикой со своим baseline; 5.1b — уточнение, не замена)

## Кодовые изменения

### 1. Расширение BASE10 → BASE20

`extract_base10_fields` извлекает индексы 1-10. В коде уже есть `extract_full29_fields`, который читает индексы 1-20, но текущий `project_token_fields()` завязан на `BASE10_NAME_TO_INDEX`. Для Stage 5.1b нужен явный общий mapping для полей 1-20 плюс `shift`, чтобы Up/Dn и `shift` не ломали старые профили.

Рекомендуемый вариант: не расширять `BASE10_NAMES` глобально, а добавить отдельный `BASE20_NAME_TO_INDEX` / `STAGE5_1B_NAME_TO_INDEX` и отдельный builder для Stage 5.1b. Так старые Stage 5.0/5.1 профили останутся неизменными.

Новые константы:

```python
# CSV field indices 1-20 in fractal string (0-indexed)
# Format: time:price:dir:front:back:strong:break:reverse:power:count:impulse:up12:dn12:up24:dn24:up48:dn48:up3:dn3:up6:dn6:...
BASE20_INDICES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
BASE20_NAMES = ['price', 'direction', 'front', 'back', 'strong', 'break',
                'reverse', 'power', 'count', 'impulse',
                'up_12', 'dn_12', 'up_24', 'dn_24', 'up_48', 'dn_48',
                'up_3', 'dn_3', 'up_6', 'dn_6']
```

### 2. shift как token-поле

`shift` (CSV index 22) не входит в BASE20. Его нужно извлекать отдельно, как `log1p(shift)`, и добавлять в token-массив. Вариант: добавить `shift` в `BASE20_NAMES` как 21-е поле (index 22), или обрабатывать отдельно в `build_profile_features`.

Для безопасности предпочтителен отдельный extractor:

```python
def extract_stage5_1b_fields(fractal_str: str) -> dict[str, float]:
    # fields 1-20 + log1p(field 22 as shift)
    ...
```

Он должен возвращать `shift = log1p(max(raw_shift, 0))` и не читать top-level CSV columns.

### 3. Новые списки полей

```python
UPDN_TOKEN_FIELDS = ['up_3', 'dn_3', 'up_6', 'dn_6', 'up_12', 'dn_12',
                     'up_24', 'dn_24', 'up_48', 'dn_48']
STAGE5_1B_STRUCTURE_FIELDS = NO_PRICE_TOKEN_FIELDS.copy()  # 9 старых
STAGE5_1B_UPDN_FIELDS = UPDN_TOKEN_FIELDS.copy()           # 10 новых
STAGE5_1B_ALL_FIELDS = STAGE5_1B_STRUCTURE_FIELDS + STAGE5_1B_UPDN_FIELDS  # 19
STAGE5_1B_BASELINE_TOKEN_FIELDS = ['shift']  # token-level baseline
```

### 4. Профили

`_stage5_1b_profile_for_key(profile_key)` — аналог `_stage5_1_profile_for_key`, но:

- `clock_shift`: token_fields = `['shift']`, row_fields = `TIME_ONLY_ROW_FIELDS`
- `structure_full`: token_fields = `STAGE5_1B_STRUCTURE_FIELDS + ['shift']`
- `updn_full`: token_fields = `STAGE5_1B_UPDN_FIELDS + ['shift']`
- `structure_plus_updn`: token_fields = `STAGE5_1B_ALL_FIELDS + ['shift']`
- `back_impulse_combo`: token_fields = `['shift', 'back', 'impulse']`
- `drop_<field>`: соответствующий full профиль минус поле, shift остаётся
- `add_<field>`: `['shift', field]` + row clock

### 5. Тесты

- Расширить тесты для `extract_base20_fields` / расширенного `extract_base10_fields`.
- Тест: `shift` корректно извлекается и лог-масштабируется.
- Тест: профили Stage 5.1b содержат `shift` в token_fields.
- Тест: `clock_shift` 5.1b ≠ `time_only` 5.1 (дополнительное token-поле).
- Тест: `structure_full` 5.1b = `structure_full` 5.1 + `shift`.
- Тест: `back_impulse_combo` содержит только `shift`, `back`, `impulse` как token-поля.
- Тест: Stage 5.1b builder не читает top-level `up_3..dn_48` колонки.
- Тест: drop/add для Up/Dn полей корректно строятся.

## Риски

1. **Коррелированные Up/Dn поля.** `up_3` и `up_6` сильно коррелируют (короткий горизонт вложен в длинный). Drop-one может показать около нулевой дельты для `up_3`, потому что `up_6` закрывает его роль. Add-one покажет самостоятельный сигнал.
2. **Up/Dn как proxy цены.** Up/Dn измеряются в валюте инструмента (доллары за унцию для XAUUSD), не нормализованы к ATR. Это означает, что Up/Dn несут ценовой масштаб, который Stage 5.0f объявил шумным. Нужно следить за тем, не является ли сигнал Up/Dn замаскированной ценой. Sanity check: если `updn_full` ≈ `base_raw_plus_time` из 5.0f — это цена, не структура.
3. **Up/Dn как proxy возраста и maturity.** Для молодых фракталов длинные горизонты не успели накопиться полностью. Если эффект `up_48/dn_48` живёт только при `shift < 48`, это может быть не рыночный сигнал, а цензурирование исторического окна.
4. **Shift конфаундер.** Добавление `shift` в baseline может «съесть» сигнал поля, которое коррелировало с возрастом фрактала. Это не баг, а цель эксперимента — но если все поля станут `mixed_or_unclear`, эксперимент не даст управленческого вывода.
5. **Стоимость.** 258 прогонов — больше чем в 2 раза Stage 5.1. Все 43 профиля обязательны: `structure_plus_updn` нужен для `delta_combined`, `back_impulse_combo` — для проверки взаимодействия из 5.1. Сокращений нет.
6. **Сожжённый holdout.** 2023-2025 нельзя использовать для выбора будущего кандидата.
7. **Старый target.** `H6_off05` исчерпан как кандидат, но остаётся пригодным диагностическим стендом.

## Связанные материалы

- `docs/superpowers/roadmap.md`
- `docs/superpowers/specs/2026-06-24-stage5_1-structural-fractal-field-ablation-design.md` — спецификация Stage 5.1 (clock-only baseline)
- `docs/reports/2026-06-24-stage5_1-structural-field-ablation.md` — отчёт Stage 5.1
- `ML/reports/stage5_1_structural_field_ablation.json` — JSON Stage 5.1
- `docs/reports/2026-06-24-stage5_0f-signal-stationarity.md` — отчёт Stage 5.0f
- `ML/baseline/benchmark_stage5_transformer_breach.py` — код раннера
- `tests/test_stage5_transformer_breach.py` — тесты
- `docs/schemas/fractal_v24_raw_price.schema.json` — схема fractal-строки (23 поля)
- `MT/MQL4/Include/lib_PIC.mqh` — producer Up/Dn и shift
- `MT/MQL4/Include/head_PIC.mqh` — структура PICS (все поля фрактала)
- `docs/methodology/03-feature-contract-leakage.md` — leakage-проверки (Up/Dn: строка 136-138)
