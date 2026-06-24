# Stage 5.1b — абляция Up/Dn полей с расширенным baseline (clock + shift)

> **Date**: 2026-06-24
> **Status**: Draft
> **Level**: поисковый
> **Verdict scope**: `DIAGNOSTIC_ONLY`
> **Goal**: Проверить самостоятельный сигнал 10 полей Up/Dn (максимальный отход цены от уровня за горизонты 3-48 баров) и пересчитать абляцию 9 структурных полей против усиленного baseline (`clock + shift`), чтобы исключить риск, что полезность поля артефакт корреляции с возрастом фрактала.

## Мотивация

### Проблема 1: непроверенные Up/Dn поля

Stage 5.1 тестировал только 9 структурных полей (`direction`, `front`, `back`, `strong`, `break`, `reverse`, `power`, `count`, `impulse`). В `Nero.csv` есть ещё 10 полей Up/Dn — максимальный отход цены от фрактального уровня за горизонты 3, 6, 12, 24, 48 баров в обе стороны. Эти поля несут принципиально иную информацию: 9 структурных описывают *сам уровень*, Up/Dn описывают *поведение цены после него*. Экономический смысл прямой: если цена уже далеко ушла от уровня, она реже к нему вернётся.

### Проблема 2: слабый baseline

Stage 5.1 использовал `clock` (hour/dow) как add-zero baseline. Но `shift` — возраст фрактала в барах от `decision_time` — тоже live-safe и не фрактальное поле в смысле структуры уровня. Без `shift` в baseline модель не знает, насколько свежая структура перед ней. Поля, коррелирующие с возрастом фрактала (например, `back` — сила тыловой границы, которая формируется со временем), могут казаться полезными только потому, что кодируют `shift`. Включение `shift` в baseline делает add-one тест честнее: поле должно показать сигнал сверх календаря **и** возраста.

### Почему перезапуск, а не дополнение

Смешивать результаты против разных baselines в одной таблице нельзя. Старый Stage 5.1 остаётся в архиве как `DIAGNOSTIC_ONLY` с clock-only baseline. Stage 5.1b вводит `clock + shift` как новый baseline и перегоняет все 9 старых полей + 10 новых Up/Dn полей против него.

### Live-safe статус новых полей

**Up/Dn.** `LEVELS_FIND_AROUND()` в `lib_PIC.mqh:378-408` обновляет Up/Dn инкрементально на каждом баре: `hmp = H - F[f].P` (текущий High минус цена фрактала), `pml = F[f].P - L`. Накопление идёт от формирования фрактала к текущему бару — только прошлые данные. CSV пишется в `NERO_CSV_CREATE(bar)`. Методология (`03-feature-contract-leakage.md:136-138`) требует доказать, что Up/Dn накоплены producer-ом, а не пересчитаны Python по будущим барам — **доказано**.

**shift.** `shift = SHIFT(F[f].T) - cur_bar` (`lib_PIC.mqh:901`) — расстояние от времени формирования фрактала до текущего бара. Вычисляется в `NERO_CSV_CREATE(cur_bar)` до записи строки. **Только прошлые данные, live-safe.**

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

1. `time_only`: `clock + shift` (token: `[shift]`, row: `[hour_sin, hour_cos, dow_sin, dow_cos]`).
2. `structure_full`: 9 структурных + `clock + shift`.
3. `updn_full`: 10 Up/Dn + `clock + shift`.
4. `structure_plus_updn`: 9 структурных + 10 Up/Dn + `clock + shift`.

**Drop-one (19 полей):**

5-13. `drop_<field>` для каждого из 9 структурных полей: `structure_full` минус поле.
14-23. `drop_<field>` для каждого из 10 Up/Dn полей: `updn_full` минус поле.

**Add-one (19 полей):**

24-32. `add_<field>` для каждого из 9 структурных полей: `time_only` + поле.
33-42. `add_<field>` для каждого из 10 Up/Dn полей: `time_only` + поле.

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
2. `time_only` Stage 5.1b (clock + shift) должен быть ≥ `time_only` Stage 5.1 (clock only). `shift` содержит информацию, if it doesn't help, that's itself a finding.
3. `updn_full` vs `structure_full`: сравнение двух групп полей «на равных» против общего baseline.

### Модель

Только XGBoost, без Transformer и без торговой симуляции.

Причины те же, что в Stage 5.1:
- Stage 5.0c/5.0e показали, что Transformer не превосходит XGBoost на `H6_off05`.
- Stage 5.1b исследует поля, а не архитектуры.
- Торговая симуляция добавит шум механики выхода.

Семена: `[42, 77, 123]`, результат агрегируется median по seed.

Transform variant: `asinh`, как в Stage 5.1. Для всех профилей нет `ATR` и price-like token-полей (кроме `shift`, который лог-масштабирован и не требует piecewise tail), поэтому `transform_params` должны быть пустыми (`{}`). Записать в JSON: `transform_params_fit_on = train_core` и `transform_params = {}`.

Ожидаемый бюджет:

- 4 baselines + 19 drop-one + 19 add-one = 42 профиля.
- 42 × 2 цели × 3 seed = 252 XGBoost-модели.
- Оценка: ~4-5 часов (Stage 5.1 = 120 прогонов за 2.5ч).

## Групповой анализ Up/Dn

Up/Dn поля естественным образом образуют 5 пар по направлению (up/dn) × 5 горизонтов (3, 6, 12, 24, 48). Помимо индивидуальных verdicts, в отчёте проверить:

1. **По направлению:** усреднить drop/add дельты по всем up_* и по всем dn_*. Есть ли асимметрия? Логично, что для `sell_stop_broken` (пробой sell-stop) `up_*` (движение вверх от уровня) может быть сильнее, а для `buy_stop_broken` — `dn_*`.
2. **По горизонту:** усреднить drop/add дельты по горизонтам 3, 6, 12, 24, 48. Есть ли паттерн «короткие горизонты сильнее/слабее длинных»?
3. **Группа vs структура:** сравнить `updn_full` и `structure_full` — какая группа даёт больше премии над baseline.

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
- delta к `time_only` для add-one всех полей
- seed-level min/median/max для каждой delta
- bootstrap CI для AUC и delta на объединённом `val_stop` и объединённом 2023-2025

`lift_30` трактуется как bottom-30 risk lift, где меньше = лучше.

Главные величины:

```text
# Структурные поля
delta_drop_struct_field = AUC(drop_struct_field) - AUC(structure_full)
delta_add_struct_field  = AUC(add_struct_field)  - AUC(time_only)

# Up/Dn поля
delta_drop_updn_field = AUC(drop_updn_field) - AUC(updn_full)
delta_add_updn_field  = AUC(add_updn_field)  - AUC(time_only)

# Групповые сравнения
delta_updn_group      = AUC(updn_full)         - AUC(time_only)
delta_structure_group = AUC(structure_full)    - AUC(time_only)
delta_combined        = AUC(structure_plus_updn) - AUC(structure_full)
```

Интерпретация delta_drop и delta_add — та же, что в Stage 5.1:

- `delta_drop < 0`: удаление ухудшило, поле полезно в составе.
- `delta_drop ≈ 0`: поле нейтрально.
- `delta_drop > 0`: удаление улучшило, поле шумит.
- `delta_add > 0`: поле само добавляет сигнал над baseline.
- `delta_add ≈ 0`: поле само по себе не даёт добавки.

### Категории field_verdicts

Те же, что в Stage 5.1, с уточнением для двух групп:

- `likely_useful`: для хотя бы одной цели `delta_drop < 0` на объединённом `val_stop` И (`CI_high < 0` ИЛИ `neg_seeds == 3`); `delta_add > 0` на объединённом `val_stop`. Кросс-таргет: если на одной цели `likely_useful`, а на другой `likely_noise` → `mixed_or_unclear`.
- `likely_noise`: для хотя бы одной цели `delta_drop > 0` на объединённом `val_stop` И (`CI_low > 0` ИЛИ `pos_seeds == 3`); `delta_add <= 0` на объединённом `val_stop`. Кросс-таргет конфликт → `mixed_or_unclear`.
- `mixed_or_unclear`: знак дельты меняется по цели, году или seed.

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
- `profiles` (42: 4 baselines + 19 drop-one + 19 add-one)
- `raw_runs`
- `summary` (per-profile per-target: val_auc_median, holdout_auc_median, yearly, lift_30, CI)
- `field_verdicts` (per-field per-target: drop delta, add delta, CI, seed counts, yearly signs, verdict)
- `group_analysis` (up vs dn, по горизонтам, updn_full vs structure_full)
- `multiple_testing_context`
- `holdout_disclosure`
- `transform_config`
- `sanity_checks` (structure_full vs 5.1, time_only vs 5.1, updn_full vs structure_full)

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

Запрещённые выводы:

- "Поле X доказанно полезно для торговли."
- "Поле X надо навсегда удалить из всех Fractal Stop задач."
- "H6_off05 переоткрыт."
- "Stage 5.2 можно считать подтверждённой до нового протокола."
- "Результаты Stage 5.1 недействительны." (5.1 остаётся валидной диагностикой со своим baseline; 5.1b — уточнение, не замена)

## Кодовые изменения

### 1. Расширение BASE10 → BASE20

`extract_base10_fields` (line 721) извлекает индексы 1-10. Добавить `extract_base20_fields`, извлекающий индексы 1-20 (или расширить `BASE10_INDICES` / `BASE10_NAMES` до 20 полей). Существующие профили, использующие `BASE10_NAMES`, остаются обратно совместимыми — они листают только первые 10 имён.

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

- `time_only`: token_fields = `['shift']`, row_fields = `TIME_ONLY_ROW_FIELDS`
- `structure_full`: token_fields = `STAGE5_1B_STRUCTURE_FIELDS + ['shift']`
- `updn_full`: token_fields = `STAGE5_1B_UPDN_FIELDS + ['shift']`
- `structure_plus_updn`: token_fields = `STAGE5_1B_ALL_FIELDS + ['shift']`
- `drop_<field>`: соответствующий full профиль минус поле, shift остаётся
- `add_<field>`: `['shift', field]` + row clock

### 5. Тесты

- Расширить тесты для `extract_base20_fields` / расширенного `extract_base10_fields`.
- Тест: `shift` корректно извлекается и лог-масштабируется.
- Тест: профили Stage 5.1b содержат `shift` в token_fields.
- Тест: `time_only` 5.1b ≠ `time_only` 5.1 (дополнительное token-поле).
- Тест: `structure_full` 5.1b = `structure_full` 5.1 + `shift`.
- Тест: drop/add для Up/Dn полей корректно строятся.

## Риски

1. **Коррелированные Up/Dn поля.** `up_3` и `up_6` сильно коррелируют (короткий горизонт вложен в длинный). Drop-one может показать около нулевой дельты для `up_3`, потому что `up_6` закрывает его роль. Add-one покажет самостоятельный сигнал.
2. **Up/Dn как proxy цены.** Up/Dn измеряются в валюте инструмента (доллары за унцию для XAUUSD), не нормализованы к ATR. Это означает, что Up/Dn несут ценовой масштаб, который Stage 5.0f объявил шумным. Нужно следить за тем, не является ли сигнал Up/Dn замаскированной ценой. Sanity check: если `updn_full` ≈ `base_raw_plus_time` из 5.0f — это цена, не структура.
3. **Shift конфаундер.** Добавление `shift` в baseline может «съесть» сигнал поля, которое коррелировало с возрастом фрактала. Это не баг, а цель эксперимента — но если все поля станут `mixed_or_unclear`, эксперимент не даст управленческого вывода.
4. **Стоимость.** 252 прогона — в 2 раза больше Stage 5.1. Если время критично, можно сократить: убрать `structure_plus_updn` (4 профиля) и group drop-one для Up/Dn от `structure_plus_updn` (не делается). Минимум: 38 профилей × 2 × 3 = 228 прогонов.
5. **Сожжённый holdout.** 2023-2025 нельзя использовать для выбора будущего кандидата.
6. **Старый target.** `H6_off05` исчерпан как кандидат, но остаётся пригодным диагностическим стендом.

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
