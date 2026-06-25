# Stage 5.1b — абляция Up/Dn полей и baseline `clock + shift`

> **Дата**: 2026-06-25
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: Проверить, дают ли 10 Up/Dn полей самостоятельный сигнал сверх `clock + shift`, и сохраняется ли вывод Stage 5.1 о структурных полях после добавления `shift` в baseline
> **Уровень этапа**: поисковый
> **Related plan/spec**: `docs/superpowers/specs/2026-06-24-stage5_1b-updn-fields-and-shift-baseline-design.md`

## Context

Stage 5.1 показал, что среди 9 структурных полей устойчивее всего выделяется `back`, но использовал слабый baseline `clock-only`. Stage 5.1b усиливает baseline: теперь модель всегда видит календарь и возраст фрактала (`shift`). Это нужно, чтобы отделить сигнал поля от простого факта, что старые и свежие фракталы ведут себя по-разному.

Второй вопрос Stage 5.1b — поля `up_3/dn_3 ... up_48/dn_48`. В raw producer-е они описывают уже накопленное движение цены от уровня по разным горизонтам. В модельном входе Stage 5.1b они читаются из `DATA/*_labeled.csv`, где `processing/normalize.py` уже записал их обратно в `fractal0..fractal99` после per-pair piecewise linear-log нормализации. Поэтому модель видит не raw price units, а нормализованные значения. Эти признаки live-safe только если они читаются из producer-строки `fractal0..fractal99`, а не из top-level target-колонок `up_* / dn_*`.

Этап заранее имеет статус `DIAGNOSTIC_ONLY`: `H6_off05` не переоткрывается как торговый кандидат, `2023-2025` уже использовались в предыдущих диагностических решениях, а коррекция множественного тестирования не применялась.

## What Was Done

- Запущен режим `--stage5-1b-updn-field-ablation`.
- Проверены 2 цели:
  - `sell_stop_broken_H6_off05_flag`
  - `buy_stop_broken_H6_off05_flag`
- Проверены 43 профиля:
  - `clock_shift`
  - `structure_full`
  - `updn_full`
  - `structure_plus_updn`
  - `back_impulse_combo`
  - 19 профилей `drop_*`
  - 19 профилей `add_*`
- Использованы 19 token-полей:
  - 9 структурных: `direction`, `front`, `back`, `strong`, `break`, `reverse`, `power`, `count`, `impulse`
  - 10 Up/Dn: `up_3`, `dn_3`, `up_6`, `dn_6`, `up_12`, `dn_12`, `up_24`, `dn_24`, `up_48`, `dn_48`
- Baseline `clock_shift` содержит:
  - row-поля: `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos`
  - token-поле: `log1p(shift)`
- Использован XGBoost, 3 seed: `[42, 77, 123]`.
- Выполнено `258` прогонов: `43 профиля × 2 цели × 3 seed`.
- Итоговый JSON: `ML/reports/stage5_1b_updn_field_ablation.json`.

Во время preflight была найдена и исправлена методическая ошибка проверки монотонности Up/Dn: монотонность нельзя проверять на `DATA/*_labeled.csv`, потому что там пары `up_X/dn_X` уже нормализованы отдельно по горизонту и шкалы между горизонтами не сопоставимы. Структурный preflight теперь берёт Up/Dn из raw-shadow источника `MT/MQL4/Files/Nero.csv`, а обучение остаётся на текущих labeled/normalized данных.

Следствие: preflight аудитирует producer-контракт raw Up/Dn, а не точную числовую структуру входа модели. Maturity shares, shift distribution, Up/Dn/ATR disclosure и корреляции Up/Dn с `shift` считаются по raw-shadow данным; они нужны для проверки live-safe источника и цензурирования горизонтов, но не описывают нормализованные значения, которые видит XGBoost.

## Multiple Testing Context

Search budget:

- 19 полей
- 2 режима сравнения: `drop-one` и `add-one`
- 2 цели
- 3 seed
- 76 основных field-сравнений: `19 × 2 × 2`
- 258 обучений XGBoost

Коррекция множественного тестирования не применялась. Поэтому `target_likely_useful`, `target_specific_signal` и `mixed_or_unclear` — это предварительные диагностические категории, а не доказательство пригодности признака для торговли.

Важное ограничение реализации: в итоговом JSON для Stage 5.1b не сохранены prediction arrays, поэтому paired bootstrap CI для delta не вычислены (`drop_val_delta_ci_low/high = None` для всех 19 полей на обеих целях). Verdict-логика фактически опирается на знак median delta, seed counts и yearly signs, а не на доверительный интервал delta. Это слабее, чем Stage 5.1, где delta CI были доступны.

## Changed Files

- `ML/baseline/benchmark_stage5_transformer_breach.py`
  - добавлен Stage 5.1b runner, profile builder, preflight, raw-shadow проверка Up/Dn, progress/heartbeat и CLI fast path.
- `tests/test_stage5_transformer_breach.py`
  - добавлены тесты Stage 5.1b, включая защиту от чтения top-level target-колонок и fail-fast проверку выравнивания raw-shadow split.
- `ML/reports/stage5_1b_updn_field_ablation.json`
  - структурированный итог полного прогона.
- `docs/reports/2026-06-25-stage5_1b-updn-field-ablation.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`

## Verification

Команды проверки:

- `./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k stage5_1b -q` — `17 passed, 134 deselected`
- `./.venv/bin/python -m pytest tests/ -q` — `838 passed`
- `./.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-1b-updn-field-ablation`
  - завершён полностью;
  - `done_runs = 258`;
  - `total_runs = 258`;
  - `status = DIAGNOSTIC_ONLY`;
  - `elapsed_sec = 23137.5` (~6.4 часа).

Сверка report ↔ JSON:

- `stage = 5.1b`
- `profiles = 43`
- `fields = 19`
- `raw_runs = 258`
- `seeds = [42, 77, 123]`
- `transform_variant = asinh`
- `shift_transform = log1p(max(raw_shift, 0))`
- `updn_units = normalized per-pair piecewise linear-log values in DATA/*_labeled.csv fractal strings; raw-shadow preflight uses raw price units from MT/MQL4/Files/Nero.csv`
- `workers = 6`, `xgb_threads = 4`

Preflight:

| Цель | Source | Monotonicity violations | train rows | val rows | holdout rows | 2026 rows |
|---|---|---:|---:|---:|---:|---:|
| sell | `raw_shadow_split` | 0 | 25672 | 2832 | 4211 | 316 |
| buy | `raw_shadow_split` | 0 | 22745 | 2580 | 3832 | 293 |

Raw-shadow выравнивание прошло: число строк raw-shadow совпадает с модельным split по всем четырём секциям.

Raw-shadow preflight не означает, что нормализованные Up/Dn в модельном входе сохраняют raw-монотонность. Напротив, на labeled данных raw-монотонность ожидаемо нарушается из-за раздельной нормализации пар горизонтов. Поэтому `monotonicity.violations_total = 0` следует читать как проверку producer-а, а не как утверждение о модельной шкале.

Sanity checks против Stage 5.1:

| Цель | 5.1 `time_only` val | 5.1b `clock_shift` val | delta | 5.1 `structure_full` val | 5.1b `structure_full` val | delta |
|---|---:|---:|---:|---:|---:|---:|
| sell | 0.6351 | 0.6259 | -0.0092 | 0.6693 | 0.6720 | +0.0027 |
| buy | 0.6418 | 0.6333 | -0.0084 | 0.6879 | 0.6898 | +0.0020 |

Вывод из sanity checks:

- `structure_full` 5.1b близок к Stage 5.1: добавление `shift` не меняет структурный профиль существенно и не объясняет сигнал `back`.
- `clock_shift` оказался хуже Stage 5.1 `time_only` на обеих целях. Это контринтуитивно: 100 token-level значений `log1p(shift)` добавляют шум или сложность, которые baseline XGBoost не использует с пользой. Поэтому add-one дельты Stage 5.1b нужно читать осторожно: они считаются от более слабого baseline, чем Stage 5.1 `time_only`.

## Results

### Итог этапа

Основной вывод: **Up/Dn поля дают небольшой самостоятельный сигнал над `clock + shift`, но не добавляют качества к полному структурному профилю.** Структурные поля остаются главным носителем сигнала, а `back` сохраняет статус самого устойчивого поля даже после добавления `shift` в baseline.

Ключевые AUC:

| Цель | `clock_shift` val | `updn_full` val | `structure_full` val | `structure_plus_updn` val |
|---|---:|---:|---:|---:|
| sell | 0.6259 | 0.6317 | 0.6720 | 0.6682 |
| buy | 0.6333 | 0.6401 | 0.6898 | 0.6868 |

На diagnostic holdout:

| Цель | `clock_shift` holdout | `updn_full` holdout | `structure_full` holdout | `structure_plus_updn` holdout |
|---|---:|---:|---:|---:|
| sell | 0.6089 | 0.6120 | 0.6635 | 0.6640 |
| buy | 0.6279 | 0.6264 | 0.6612 | 0.6593 |

Групповые дельты на validation:

| Цель | `updn_full - clock_shift` | `structure_full - clock_shift` | `structure_plus_updn - structure_full` |
|---|---:|---:|---:|
| sell | +0.0048 | +0.0460 | -0.0017 |
| buy | +0.0059 | +0.0561 | -0.0021 |

Интерпретация:

- Up/Dn как отдельная группа дают слабую добавку к `clock + shift`.
- Структурная группа даёт примерно на порядок большую добавку.
- Добавление Up/Dn к `structure_full` не улучшает validation на обеих целях.
- Поэтому Up/Dn не стоит включать в следующий стартовый профиль по умолчанию.

### `back` сохранил главный вывод Stage 5.1

`back` — единственное поле с `overall_likely_useful` на обеих целях:

| Цель | drop vs full val | drop vs full holdout | add vs `clock_shift` val | add vs `clock_shift` holdout |
|---|---:|---:|---:|---:|
| sell | -0.0171 | -0.0206 | +0.0408 | +0.0499 |
| buy | -0.0186 | -0.0149 | +0.0575 | +0.0362 |

Удаление `back` ухудшает качество, добавление `back` к `clock + shift` резко улучшает качество. Годовые знаки удаления `back` отрицательны на всех годах `2021-2025` для обеих целей. Значит, вывод Stage 5.1 о `back` не был просто артефактом возраста фрактала.

### `back_impulse_combo` почти догоняет структуру, но не заменяет её полностью

| Цель | `back_impulse_combo` val | `structure_full` val | gap | `back_impulse_combo` holdout | `structure_full` holdout | gap |
|---|---:|---:|---:|---:|---:|---:|
| sell | 0.6661 | 0.6720 | -0.0059 | 0.6628 | 0.6635 | -0.0006 |
| buy | 0.6928 | 0.6898 | +0.0030 | 0.6654 | 0.6612 | +0.0042 |

Пара `back + impulse` выглядит сильной компактной диагностической заменой структуры, особенно на buy. Но это не подтверждённый новый winner: профиль был заранее добавлен как контроль, а не как чистый кандидат, и `2023-2025` остаются disclosure-only.

### Up/Dn поля: слабая и неоднородная картина

Единственный частный useful-ярлык среди Up/Dn:

- `dn_24` получил `target_likely_useful` только на sell: drop val `-0.0030`, add val `+0.0100`, `negative_seed_count = 3`, CI отсутствует.
- Общий verdict `dn_24` = `target_specific_signal`, потому что buy не подтвердил сигнал.

Это слабая категория useful: drop-дельта `-0.0030` мала и без CI может лежать в шуме. Поэтому `dn_24` нужно трактовать только как sell-only гипотезу, а не как надёжный Up/Dn-признак.

По направлениям средние validation-дельты малы:

| Цель | `up_*` add median | `dn_*` add median | `up_*` drop median | `dn_*` drop median |
|---|---:|---:|---:|---:|
| sell | +0.0034 | +0.0079 | -0.0004 | -0.0001 |
| buy | +0.0071 | +0.0023 | +0.0034 | +0.0033 |

Есть слабая асимметрия: на sell чуть сильнее `dn_*`, на buy чуть сильнее `up_*`. Но она неустойчива и не превращается в уверенный групповой вывод.

По горизонтам нет чистого паттерна, который можно было бы переносить дальше:

| Цель | H | add delta val | drop delta val | non-mature share val |
|---|---:|---:|---:|---:|
| sell | 3 | +0.0056 | +0.0001 | 1.3% |
| sell | 6 | +0.0043 | +0.0023 | 2.7% |
| sell | 12 | +0.0058 | -0.0033 | 5.4% |
| sell | 24 | +0.0056 | -0.0005 | 10.7% |
| sell | 48 | +0.0063 | -0.0032 | 19.1% |
| buy | 3 | +0.0052 | +0.0045 | 1.3% |
| buy | 6 | +0.0046 | +0.0025 | 2.7% |
| buy | 12 | +0.0054 | +0.0018 | 5.5% |
| buy | 24 | +0.0069 | +0.0035 | 10.7% |
| buy | 48 | +0.0032 | +0.0057 | 19.2% |

Maturity-риск не выглядит главным объяснением результата: non-mature доля растёт к H48, но именно H48 не даёт устойчивой сильной добавки. Тем не менее Stage 5.1b не выполнял отдельное переобучение mature-only/non-mature-only, поэтому это только sanity disclosure.

### `impulse`

`impulse` снова остался `mixed_or_unclear`, но причина стала жёстче, чем в Stage 5.1:

| Цель | 5.1 drop val | 5.1 add val | 5.1b drop val | 5.1b add val |
|---|---:|---:|---:|---:|
| sell | -0.0036 | +0.0164 | -0.0009 | +0.0263 |
| buy | -0.0010 | +0.0200 | -0.0004 | +0.0338 |

Добавление `shift` не поглотило add-сигнал `impulse`: add-дельты выросли. Но drop-one роль внутри `structure_full` почти исчезла, а seed-согласованность осталась только 2/3 на обеих целях. Поэтому `impulse` полезен как часть диагностического `back_impulse_combo`, но не получает самостоятельный useful verdict.

### `lift_30`

`lift_30` трактуется как доля пробоев в нижних 30% риска относительно средней доли; меньше = лучше.

| Цель | `clock_shift` val | `updn_full` val | `structure_full` val | `structure_plus_updn` val |
|---|---:|---:|---:|---:|
| sell | 0.6374 | 0.6251 | 0.5353 | 0.5353 |
| buy | 0.6943 | 0.6632 | 0.4801 | 0.4940 |

Картина совпадает с AUC: Up/Dn немного улучшают baseline, но не догоняют структуру; добавка Up/Dn к структуре не улучшает нижнюю зону риска.

## Conclusions

1. **Stage 5.1b не реабилитирует `H6_off05`.** Это диагностический этап, а не новый кандидат.
2. **Главный носитель сигнала остаётся в структурных полях, не в Up/Dn.** `structure_full` даёт +0.0460/+0.0561 AUC над `clock_shift`, а `updn_full` только +0.0048/+0.0059.
3. **Up/Dn не нужно включать в следующий стартовый профиль по умолчанию.** Они дают слабый самостоятельный след, но ухудшают validation при добавлении к `structure_full`.
4. **`back` остаётся главным подтверждённым диагностическим полем.** Добавление `shift` не съело его сигнал.
5. **`back + impulse` заслуживает узкого будущего follow-up.** Пара почти догоняет `structure_full` на sell и превосходит его на buy, но это ещё не подтверждение.
6. **`dn_24` — только target-specific гипотеза для sell.** Её нельзя переносить как общий вывод по Up/Dn.

## Limitations / Open Questions

- `2023-2025` уже использовались в Stage 5.0f/5.1, поэтому не являются новым независимым подтверждением.
- Коррекция множественного тестирования не применялась.
- Модельные Up/Dn — нормализованные per-pair значения, а не raw price units. Поэтому риск "Up/Dn как прямой proxy цены" для модельного входа слабее, чем предполагалось в спецификации. Raw Up/Dn/ATR disclosure остаётся только аудитом producer-а.
- Maturity-aware анализ ограничен долями mature/non-mature; отдельного mature-only обучения не было.
- Delta CI не вычислены в итоговом JSON; field verdicts слабее, чем в Stage 5.1, и опираются на seed counts/yearly signs.
- `back_impulse_combo` выглядит перспективно, но не проходил чистый confirmatory-cycle.
- На buy `back_impulse_combo` превосходит `structure_full` и на validation, и на diagnostic holdout 2023-2025, но 2023-2025 уже сожжены предыдущими этапами и не являются независимым подтверждением.
- `2026` остаётся low-N disclosure: sell `n=316`, buy `n=293`.
- Торговая симуляция не запускалась; AUC/lift не доказывают прибыльность.

## Validation Split Disclosure

Split повторяет Stage 5.1:

- `train_core`: годы `2004-2020`
- `val_stop`: годы `2021-2022`, primary diagnostic validation и early stopping
- `diagnostic_holdout`: годы `2023-2025`, disclosure only
- `low_n_disclosure`: `2026`, не используется для verdict

Строки:

| Цель | train_core | val_stop | diagnostic_holdout | low_n_disclosure |
|---|---:|---:|---:|---:|
| sell | 25672 | 2832 | 4211 | 316 |
| buy | 22745 | 2580 | 3832 | 293 |

Holdout не использовался для выбора winner-а. Этап не объявляет winner.

## Next Step

Допустимый следующий шаг — узкий Stage 5.1c/5.2 mini-follow-up, если вообще продолжать `H6_off05`:

- `clock_shift`
- `clock_shift + back`
- `clock_shift + impulse`
- `clock_shift + back + impulse`
- `structure_full`
- `structure_full_without_back`

Запрещённые выводы:

- объявлять Up/Dn полезными торговыми признаками;
- включать весь `updn_full` в следующий стартовый профиль без новой проверки;
- считать `back` production-признаком;
- использовать `2023-2025` как новое независимое подтверждение;
- переоткрывать `H6_off05` как торговую ветку без нового периода `2026+`.

## Related Materials

- `ML/reports/stage5_1b_updn_field_ablation.json`
- `docs/superpowers/specs/2026-06-24-stage5_1b-updn-fields-and-shift-baseline-design.md`
- `docs/reports/2026-06-24-stage5_1-structural-field-ablation.md`
- `ML/reports/stage5_1_structural_field_ablation.json`
- `docs/reports/2026-06-24-stage5_0f-signal-stationarity.md`
- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `tests/test_stage5_transformer_breach.py`
- `MT/MQL4/Files/Nero.csv`
- `docs/schemas/fractal_v24_raw_price.schema.json`
