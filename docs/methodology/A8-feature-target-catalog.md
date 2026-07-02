# A8. Канонический каталог признаков и таргетов

## Цель

Собрать в одном месте основные семейства `feature` и `target`, которые уже использовались в SoSimple или были явно зафиксированы в коде, методике и отчётах. Этот файл нужен как навигация и как защита от повторного забывания уже проверенных постановок.

Главное правило:

- этот каталог не доказывает, что семейство полезно;
- он только фиксирует, что именно уже существует в проекте, как это понимать и где искать подробности;
- для нового этапа всё равно нужно отдельно замораживать конкретный набор признаков, конкретный target contract и split policy.

## Как читать каталог

Есть три разные сущности:

1. **Поле признака**: отдельная величина, которая подаётся в модель, например `back`, `shift`, `price_coord_atr`.
2. **Семейство признаков**: группа связанных полей, например `path_reaction` или `updn_full`.
3. **Представление входа**: способ выбрать или сгруппировать фракталы до построения признаков, например `all100`, `nearest_k`, `corridor_Xatr`, `zones_atr`.

Нельзя смешивать эти уровни при интерпретации результата. Улучшение могло прийти:

- от нового поля;
- от нового семейства;
- от другого способа отбора фракталов;
- от их сочетания.

## Часть 1. Каталог признаков

### 1.1. Базовые структурные поля фрактала

Это ядро старых baseline-профилей и основа `structure_full`.

| Семейство | Поля | Смысл | Где описано |
|---|---|---|---|
| `structure_fields` | `direction`, `front`, `back`, `strong`, `break`, `reverse`, `power`, `count`, `impulse` | Геометрия и поведение самого уровня без явной ценовой реакции | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md), [2026-06-24-stage5_1-structural-field-ablation.md](../reports/2026-06-24-stage5_1-structural-field-ablation.md) |

Замечание:

- в Stage 5.1 `back` оказался самым устойчивым из этих полей;
- сами по себе эти поля не являются ценовыми, но они почти всегда идут рядом с ценовыми ветками и служат базой для абляций.

### 1.2. Временные и возрастные признаки

| Семейство | Поля | Смысл | Где описано |
|---|---|---|---|
| `time_control` | `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` | Календарный контроль, а не фрактальный сигнал | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md) |
| `shift_age` | `shift`, `log_shift`, `delta_shift` и близкие варианты | Возраст уровня в барах | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md) |

### 1.3. ATR и смена режима волатильности

| Семейство | Поля | Смысл | Где описано |
|---|---|---|---|
| `atr_ratio` | `fractal_atr / current_ATR` и его лог-варианты | Насколько волатильность при рождении уровня отличается от текущей | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md) |
| `row_atr` | текущий `ATR` строки | Масштаб и режим волатильности на момент решения | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md), [2026-06-21-stage5_0b-asinh-rerun.md](../reports/2026-06-21-stage5_0b-asinh-rerun.md) |

### 1.4. Ценовые признаки уровня

Это главный набор для исследований, где важна привязка к цене и масштабу уровня.

| Семейство | Поля / формула | Смысл | Где описано |
|---|---|---|---|
| `relative_price` | `(price_i - price_0) / ATR` | Цена фрактала относительно `fractal0`, приведённая к ATR | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md), [2026-06-21-stage5_0b-asinh-rerun.md](../reports/2026-06-21-stage5_0b-asinh-rerun.md) |
| `distance_atr` | signed / abs / direction-aware distance from `fractal0` | Явное расстояние от текущего уровня до других уровней | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md), [ML/data_loader.py](../../ML/data_loader.py) |
| `price_coord_atr` | `(price - f0_price) / ATR` | Координата уровня в ATR-системе вокруг `fractal0` | [2026-06-29-stage5_4-fast-price-atr-ablation.md](../superpowers/plans/2026-06-29-stage5_4-fast-price-atr-ablation.md) |
| `price_atr_scaled` | `price / ATR`, иногда с `asinh` | Абсолютная цена, приведённая к текущему ATR | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md), [2026-06-29-stage5_4-fast-price-atr-ablation.md](../superpowers/plans/2026-06-29-stage5_4-fast-price-atr-ablation.md) |
| `absolute_price` | raw `price` или его стабилизированная версия | Абсолютный ценовой режим | [2026-06-21-stage5_0b-asinh-rerun.md](../reports/2026-06-21-stage5_0b-asinh-rerun.md) |

Критическая оговорка:

- `relative_price` и signed `distance_atr` часто близки по смыслу;
- их нельзя считать независимыми победителями без явной абляции;
- `price_atr_scaled` методически слабее `price_coord_atr`, потому что может нести режим цены, а не только физику уровня.

### 1.5. Сырые `Up/Dn` внутри строк фракталов

Producer `lib_PIC` экспортирует в `fractal0..fractal99` исторически накопленные реакции цены после уровня:

- `Up3/Dn3`
- `Up6/Dn6`
- `Up12/Dn12`
- `Up24/Dn24`
- `Up48/Dn48`

Они могут использоваться как live-safe признаки **только если** доказано, что:

- это состояние producer-а на момент строки;
- Python не пересчитывал их по будущим барам;
- модель читает их из `fractal*`, а не из top-level target columns.

Где описано:

- [03-feature-contract-leakage.md](03-feature-contract-leakage.md)
- [docs/processing/label_signals.py.md](../processing/label_signals.py.md)
- [2026-06-25-stage5_1b-updn-field-ablation.md](../reports/2026-06-25-stage5_1b-updn-field-ablation.md)

Практические семейства:

| Семейство | Состав | Смысл |
|---|---|---|
| `updn_short` | `up_3/dn_3`, `up_6/dn_6`, `up_12/dn_12` | Короткая и средняя историческая реакция |
| `updn_full` | `up_3/dn_3 ... up_48/dn_48` | Полное семейство реакций по всем доступным горизонтам |

Критическая оговорка:

- в проекте уже была ошибка, где нормализация `Up/Dn` зависела от top-level target;
- поэтому любые новые исследования `Up/Dn` требуют отдельного scale/contract audit до обучения.

### 1.6. Производные признаки `path_reaction`

Это не сырые `Up/Dn`, а агрегаты исторической реакции уровня.

Источник:

- [docs/ML/lib_pic_path_reaction_feature_bank.py.md](../ML/lib_pic_path_reaction_feature_bank.py.md)
- [2026-04-19-lib-pic-path-reaction-feature-bank.md](../reports/2026-04-19-lib-pic-path-reaction-feature-bank.md)
- [ML/lib_pic_path_reaction_feature_bank.py](../../ML/lib_pic_path_reaction_feature_bank.py)

Базовая идея:

- если `Dir > 0`, то `fav = Up`, `adv = Dn`;
- если `Dir < 0`, то `fav = Dn`, `adv = Up`.

То есть реакция переводится не в координаты “вверх/вниз”, а в координаты “благоприятно/неблагоприятно для уровня”.

Строятся по окнам `5/10/20/50/100` и горизонтам `3/6/12/24/48`.

| Группа | Смысл |
|---|---|
| `fav*_mean/max/recent` | средний / максимальный / самый свежий благоприятный ход |
| `adv*_mean/max/recent` | средний / максимальный / самый свежий неблагоприятный ход |
| `edge*_mean/recent` | разность `fav - adv`: было ли историческое преимущество в сторону уровня |
| `rr*_mean/recent` | отношение `fav / adv`: насколько благоприятный ход превосходил неблагоприятный |
| `win_proxy*_share` | доля уровней, где `fav > adv` |
| `*_slope_3_48_mean` | как реакция меняется от короткого горизонта `3` к длинному `48` |
| `*_slope_12_48_mean` | как реакция меняется от среднего горизонта `12` к длинному `48` |

Практический смысл:

- сырые `Up/Dn` отвечают на вопрос “что происходило после уровня”;
- `path_reaction` отвечает на вопрос “как уровень обычно вел себя относительно своей стороны”.

### 1.7. Агрегаты плотности и зон

| Семейство | Смысл | Где описано |
|---|---|---|
| `density` | сколько уровней рядом, выше, ниже, внутри диапазона | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md) |
| `zones_atr` | агрегаты по ценовым зонам вокруг `fractal0` | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md), [ML/fractal_level_feature_builder.py](../../ML/fractal_level_feature_builder.py) |
| `zones_plus_nearest_k` | зоны плюс несколько ближайших уровней | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md), [ML/fractal_level_feature_builder.py](../../ML/fractal_level_feature_builder.py) |

## Часть 2. Представления входа и группировка фракталов

Это не отдельные признаки, а способы собрать вход до построения признаков.

| Представление | Смысл | Где описано |
|---|---|---|
| `all100` | все `fractal0..fractal99` | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md) |
| `newest_N` | только N самых свежих фракталов | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md) |
| `nearest_k` | K уровней, ближайших по цене к `fractal0` | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md), [ML/fractal_level_feature_builder.py](../../ML/fractal_level_feature_builder.py) |
| `corridor_Xatr` | уровни внутри `±X*ATR` от `fractal0.price` | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md) |
| `zones_atr` | уровни, сведённые в ATR-зоны | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md) |
| `fractal_rows` | вход как список фракталов и их полей | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md) |
| `flat_table` | все признаки развёрнуты в одну строку | [A6-fractal-feature-profile-catalog.md](A6-fractal-feature-profile-catalog.md) |

Критическая оговорка:

- смена `all100` на `nearest_k` или `corridor_Xatr` уже сама по себе меняет hypothesis class;
- поэтому нельзя трактовать такой переход как “мы добавили всего один новый признак”.

## Часть 3. Каталог таргетов

### 3.1. `Regression Up/Dn` от `fractal0_price`

Основная регрессионная семья последних этапов:

- `up_3/dn_3`
- `up_6/dn_6`
- `up_12/dn_12`
- `up_24/dn_24`
- `up_48/dn_48`

Смысл:

- favorable/adverse move от `fractal0_price` по фиксированным горизонтам.

Где описано:

- [2026-06-30-regression-updn-target-foundation.md](../reports/2026-06-30-regression-updn-target-foundation.md)
- [2026-07-02-regression-updn-already-moved-audit.md](../reports/2026-07-02-regression-updn-already-moved-audit.md)

Статус:

- годится как диагностический target foundation;
- не доказан как target для немедленного входа на следующий `open`.

### 3.2. `Entry-based Up/Dn` от фактического входа

Семья для проверки реального исполнимого входа:

- `entry_up_3/dn_3`
- `entry_up_6/dn_6`
- `entry_up_12/dn_12`
- производные `entry_log_ratio_h`

Смысл:

- движение считается от фактического `entry_open`, а не от идеальной фрактальной цены.

Где описано:

- [2026-07-02-next-open-entry-updn-foundation.md](../reports/2026-07-02-next-open-entry-updn-foundation.md)

Статус:

- контракт target валиден;
- для ветки `next open after signal_time` полезного сигнала не найдено.

### 3.3. Binary breach targets

Классическая family для Fractal Stop:

- `sell_stop_broken_H6_off05_flag`
- `buy_stop_broken_H6_off05_flag`
- аналогичные варианты для других `H` и `off`

Смысл:

- будет ли стоповый уровень пробит в пределах заданного горизонта и смещения.

Где описано:

- [2026-06-24-stage5_1-structural-field-ablation.md](../reports/2026-06-24-stage5_1-structural-field-ablation.md)
- [2026-06-21-stage5_0b-asinh-rerun.md](../reports/2026-06-21-stage5_0b-asinh-rerun.md)
- [ML/baseline/benchmark_fractal_stop_stage3_2.py](../../ML/baseline/benchmark_fractal_stop_stage3_2.py)

### 3.4. `bars_to_breach` / time-to-breach

Регрессионная семья времени до пробоя:

- `sell_bars_to_breach_H6_off05`
- `buy_bars_to_breach_H6_off05`

Смысл:

- число баров до первого пробоя, либо `H + 1`, если пробоя не было внутри окна.

Где описано:

- [2026-06-25-stage5_2-time-to-breach-regression.md](../reports/2026-06-25-stage5_2-time-to-breach-regression.md)

Статус:

- полезен как ранжирующий сигнал;
- обычная регрессия одного числа плохо переносит цензуру “не пробит за H”.

### 3.5. `entry_path_v1`

Семья целей для реального входа на следующем баре и траектории сделки:

- `ret_6_dir_atr`, `ret_12_dir_atr`, `ret_24_dir_atr`
- `fav_3_atr`, `adv_3_atr`
- `fav_6_atr`, `adv_6_atr`
- `fav_12_atr`, `adv_12_atr`
- `fav_24_atr`, `adv_24_atr`
- `path_6_class`

Где описано:

- [2026-04-08-entry-path-v1-baseline.md](../reports/2026-04-08-entry-path-v1-baseline.md)

### 3.6. `take_skip` / `trailing_stop_v2`

Семья многогоризонтных бинарных outcome-таргетов:

- `take_12_x2`, `take_12_x4`, `take_12_x8`
- `take_24_x2`, `take_24_x4`, `take_24_x8`
- `take_48_x2`, `take_48_x4`, `take_48_x8`
- а также связанные `trail_*_pnl_atr_x*`

Смысл:

- выдержит ли сделка заданный путь до take / trailing-stop сценария.

Где описано:

- [docs/ML/run_take_skip_lib_pic_feature_matrix.py.md](../ML/run_take_skip_lib_pic_feature_matrix.py.md)
- [2026-04-17-multi-horizon-take-skip-feature-track-handoff.md](../reports/2026-04-17-multi-horizon-take-skip-feature-track-handoff.md)
- [2026-04-20-take-skip-original-contour-feature-ablation.md](../reports/2026-04-20-take-skip-original-contour-feature-ablation.md)

### 3.7. Outcome-based / triple-barrier family

В проекте есть отдельная ветка outcome-based и `triple_barrier`-постановок, где target описывает не отдельный пробой или excursion, а исход барьера/сделки.

Где искать:

- [ML/baseline/benchmark_stage6_outcome_based.py](../../ML/baseline/benchmark_stage6_outcome_based.py)
- [2026-06-29-stage6_1-h12-relative-fractal-geometry.md](../reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md)

Это семейство включено в каталог как навигационная точка, но его конкретные target-варианты надо уточнять по этапу и runner-у.

## Часть 4. Что ещё не каталогизировано полностью

На сегодня в проекте уже есть достаточное покрытие по основным feature- и target-family, но остаются пробелы:

- нет единой короткой таблицы “какие raw поля producer-а доступны для каждого family”;
- нет отдельного каталога всех исторических `score_target` и `rule_target` для selection/telemetry-контуров;
- `outcome-based` и часть старых `take_skip` семейств всё ещё лучше искать по runner-ам и отчётам, чем по одному унифицированному контракту.

## Часть 5. Правила использования каталога в новых этапах

Перед новым этапом нужно явно зафиксировать:

1. какие семейства признаков берутся;
2. какое представление входа используется;
3. какие target-family считаются основными, а какие diagnostic;
4. какие поля live-safe, а какие target-only;
5. какая нормализация применяется отдельно для input и отдельно для target.

Каталог не заменяет:

- feature contract;
- target contract;
- scale audit;
- split policy;
- validation freeze.
