# Stage 5.1 — структурная абляция фрактальных полей

> **Дата**: 2026-06-24
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: Проверить, какие из 9 структурных полей фрактала дают устойчивый добавочный сигнал для `H6_off05 stop broken` сверх clock-only baseline, не переоткрывая ветку как торгового кандидата
> **Уровень этапа**: поисковый
> **Related plan/spec**: `docs/superpowers/plans/2026-06-24-stage5_1-structural-field-ablation.md`

## Context

После Stage 5.0d и Stage 5.0f стало ясно две вещи:

- `price` и `ATR` не выглядят главным источником сигнала;
- ветка `H6_off05` остаётся диагностической: `2023-2025` уже сожжены в управленческих выводах Stage 5.0f и не могут считаться новым независимым подтверждением.

Stage 5.1 нужен как узкая диагностическая декомпозиция: не выбрать winner, а понять, какой вклад дают отдельные структурные поля `direction/front/back/strong/break/reverse/power/count/impulse`.

Этап заранее имеет статус `DIAGNOSTIC_ONLY`. Он не переоткрывает `H6_off05` как торгового кандидата и не даёт права объявлять новое правило или нового winner.

## What Was Done

- Добавлен новый режим `--stage5-1-structural-field-ablation` в `ML/baseline/benchmark_stage5_transformer_breach.py`.
- Зафиксированы две цели:
  - `sell_stop_broken_H6_off05_flag`
  - `buy_stop_broken_H6_off05_flag`
- Зафиксированы 20 профилей:
  - `time_only`
  - `structure_full`
  - 9 профилей `drop_*`
  - 9 профилей `add_*`
- `time_only` содержит ровно 4 clock-признака:
  - `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos`
- Stage 5.1 полностью исключает:
  - `price`
  - `price_coord_atr`
  - `price_atr_scaled`
  - `ATR`
- Использован только XGBoost.
- Использованы 3 seed: `[42, 77, 123]`.
- Использован фиксированный split:
  - `train_core <= 2020`
  - `val_stop = 2021-2022`
  - `diagnostic_holdout = 2023-2025`
- `low_n_disclosure = 2026` (sell `n=316`, buy `n=293`)
- Для каждого profile × target × seed считались:
  - AUC и `lift_30` на `train_core`, `val_stop`, `diagnostic_holdout`, `low_n_disclosure`
  - годовые метрики для `2021-2022` и `2023-2025`
  - bootstrap CI на AUC и `lift_30`
  - paired bootstrap delta для сравнения `drop_*` против `structure_full` и `add_*` против `time_only`
- Итоговый JSON: `ML/reports/stage5_1_structural_field_ablation.json`

Модельный бюджет этапа:

- `2 цели × 20 профилей × 3 seed = 120` XGBoost моделей

## Multiple Testing Context

Search budget заранее зафиксирован:

- 2 цели
- 20 профилей
- 3 seed
- paired delta для `drop_*` и `add_*`

Итого: `120` обучений XGBoost плюс пост-агрегация delta/CI.

Коррекция множественного тестирования не применялась. Это сознательно допустимо только потому, что этап имеет статус `DIAGNOSTIC_ONLY`.

Важно:

- `likely_useful`
- `likely_noise`
- `mixed_or_unclear`

в этом отчёте означают только предварительные диагностические категории. Они не являются подтверждённым статистическим verdict для выбора признаков в production-кандидате.

## Changed Files

- `ML/baseline/benchmark_stage5_transformer_breach.py`
  - добавлены Stage 5.1 константы, split, profile builders, seed evaluation, paired bootstrap deltas, field verdicts, runner и CLI.
- `tests/test_stage5_transformer_breach.py`
  - добавлены тесты Stage 5.1 для констант, профилей, split, evaluation, summary, verdicts, runner и CLI.
- `ML/reports/stage5_1_structural_field_ablation.json`
  - структурированный артефакт полного прогона.
- `docs/ML/benchmark_stage5_transformer_breach.py.md`
- `MODULE_INDEX.md`
- `docs/reports/2026-06-24-stage5_1-structural-field-ablation.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`

## Verification

- `./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -q` — `134 passed`
- `./.venv/bin/python -m pytest tests/ -q` — `819 passed`
- `./.venv/bin/python ML/baseline/benchmark_stage5_transformer_breach.py --stage5-1-structural-field-ablation`
  - завершён полностью;
  - записан `ML/reports/stage5_1_structural_field_ablation.json`;
  - итог `done_runs = 120`, `status = DIAGNOSTIC_ONLY`

Сверка отчёт ↔ structured artifact:

- `status = DIAGNOSTIC_ONLY`
- `done_runs = 120`
- `total_runs = 120`
- `profiles = 20`
- `raw_runs = 120`
- `elapsed_sec = 9185.3` (~2.5 часа)
- `field_verdicts.back.overall_verdict = likely_useful`
- других `overall_verdict = likely_useful` или `likely_noise` нет

Sanity check против Stage 5.0d: `structure_full` val_auc sell = 0.6693, buy = 0.6879 — идентично 5.0d `no_price` (sell 0.6693, buy 0.6879). Holdout: 5.1 sell 0.6662 vs 5.0d 0.6592, buy 0.6610 vs 5.0d 0.6601 — небольшая разница из-за yearly vs pooled. Это подтверждает корректность реализации: `structure_full` и 5.0d `no_price` — один и тот же набор признаков.

## Results

### Итог этапа

Stage 5.1 не реабилитирует `H6_off05`. Он только показывает, что среди 9 структурных полей одно поле выделяется устойчивее остальных:

- **`back` = `likely_useful` на обеих целях**
- все остальные поля = **`mixed_or_unclear`**
- полей с итоговым `likely_noise` не найдено

Это означает:

- clock-only baseline (`time_only`) явно неполон;
- полный структурный профиль (`structure_full`) несёт реальный добавочный сигнал;
- но внутри структуры только поле `back` показало согласованный рисунок и в режиме `drop-one`, и в режиме `add-one`.

### Базовые профили

Медианные AUC:

| Цель | `time_only` val | `structure_full` val | `time_only` holdout | `structure_full` holdout |
|---|---:|---:|---:|---:|
| sell | 0.6351 | 0.6693 | 0.6144 | 0.6662 |
| buy | 0.6418 | 0.6879 | 0.6252 | 0.6610 |

Медианный `lift_30` (меньше = лучше):

| Цель | `time_only` val | `structure_full` val | `time_only` holdout | `structure_full` holdout |
|---|---:|---:|---:|---:|
| sell | 0.6529 | 0.5477 | 0.6952 | 0.5825 |
| buy | 0.6287 | 0.5216 | 0.6993 | 0.5673 |

Вывод из этих базовых сравнений: структурный набор заметно лучше чисто календарного baseline и по AUC, и по нижней зоне риска.

### Единственный устойчивый сигнал: `back`

**Предметный смысл поля.** `back_val` («сила тыловой границы») — это характеристика прочности противоположной стороны фрактального уровня (см. `docs/schemas/fractal_v24_raw_price.schema.json`, index 4). Экономически: уровень с сильной тыловой границей труднее пробить сзади, что может объяснить связь с устойчивостью stop-пробоя — чем сильнее «спина» уровня, тем меньше шанс, что цена откатится через него. Это гипотеза, не доказательство; но она объясняет, почему именно это поле выделилось, а не технический артефакт кодирования.

Для поля `back`:

| Цель | `drop_back` delta vs `structure_full` на val | drop CI на val | neg seeds | `add_back` delta vs `time_only` на val | `add_back` delta vs `time_only` на holdout | Verdict |
|---|---:|---|---:|---:|---:|---|
| sell | -0.0100 | [-0.0228, +0.0009] | 3/3 | +0.0213 | +0.0277 | `likely_useful` |
| buy | -0.0209 | [-0.0317, -0.0101] | 3/3 | +0.0359 | +0.0344 | `likely_useful` |

**Годовая устойчивость.** Удаление `back` ухудшает AUC на всех 5 годах (2021-2025) на обеих целях: yearly drop signs = [-1, -1] (val 2021-2022) + [-1, -1, -1] (holdout 2023-2025) = 5/5 отрицательных. Это самый согласованный годовой рисунок среди всех 9 полей.

Ключевой смысл:

- если убрать `back` из полного структурного профиля, качество падает;
- если оставить только `back` поверх clock-only baseline, качество заметно растёт;
- рисунок повторился на sell и buy.

**Важное уточнение по CI.** Для buy CI не пересекает 0 ([-0.0317, -0.0101]) — вывод устойчив и по seed, и по CI. Для sell верхняя граница CI пересекает 0 (+0.0009) — здесь `likely_useful` держится на согласии всех 3 seed (`negative_seed_count = 3`), а не на CI. Это не опровергает вывод, но означает, что на sell уверенность слабее, чем на buy.

**Ограничение add-one интерпретации.** `add_back` сравнивается с `time_only` — очень слабым baseline (sell val 0.6351). `back` один даёт +0.0213 (sell) / +0.0359 (buy) над clock, но `structure_full` даёт +0.0342 (sell) / +0.0461 (buy). То есть `back` одиночно захватывает ~64% (sell) и ~74% (buy) структурной премии — существенную часть, но не всю. Прямое сравнение `time+back` vs `structure_full` не проводилось; нельзя утверждать, что `back` заменяет полный профиль. Разница может быть значимой, особенно для sell, где 36% премии приходится на остальные 8 полей.

Это самый сильный диагностический вывод Stage 5.1.

### Второй по интересу, но ещё не подтверждённый: `impulse`

`impulse` дал частично похожий рисунок, но не собрал достаточной согласованности для `likely_useful`:

| Цель | `drop_impulse` delta vs `structure_full` на val | `add_impulse` delta vs `time_only` на val | `add_impulse` delta vs `time_only` на holdout | Verdict |
|---|---:|---:|---:|---|
| sell | -0.0036 | +0.0164 | +0.0270 | `mixed_or_unclear` |
| buy | -0.0010 | +0.0200 | +0.0197 | `mixed_or_unclear` |

**Почему `mixed_or_unclear`, несмотря на сильные add-дельты.** Verdict `likely_useful` требует одновременного выполнения нескольких условий. Для `impulse` они не сошлись по разным причинам на каждой цели:

- **sell**: `drop_val = -0.0036` и все 3 seed согласны (neg), но yearly holdout signs = [+1, +1, -1] — на 2 из 3 годов holdout удаление `impulse` **улучшает** AUC. Условие `yearly_negative >= 2` не выполнено.
- **buy**: `drop_val = -0.0010`, `neg_seeds = 2` (не 3), yearly holdout = [-1, -1, -1] (все отрицательные), `add_val = +0.0200 > 0`. Но CI пересекает 0 ([-0.0081, +0.0060]) и `neg_seeds = 2 ≠ 3` — условие `useful_ci_or_seed_confirmed` не выполнено.

То есть `impulse` выглядит потенциально полезным, но Stage 5.1 не даёт права считать это устойчивым выводом.

### Полная таблица дельт по всем полям

| Поле | sell drop_val | sell add_val | sell add_hold | buy drop_val | buy add_val | buy add_hold | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| `direction` | +0.0026 | -0.0026 | -0.0058 | -0.0000 | -0.0019 | -0.0005 | `mixed_or_unclear` |
| `front` | -0.0023 | -0.0070 | -0.0035 | -0.0018 | -0.0066 | -0.0036 | `mixed_or_unclear` |
| `back` | -0.0100 | +0.0213 | +0.0277 | -0.0209 | +0.0359 | +0.0344 | `likely_useful` |
| `strong` | +0.0010 | +0.0012 | -0.0006 | -0.0001 | +0.0031 | +0.0027 | `mixed_or_unclear` |
| `break` | +0.0046 | +0.0001 | -0.0032 | -0.0003 | -0.0015 | +0.0016 | `mixed_or_unclear` |
| `reverse` | +0.0018 | +0.0012 | -0.0039 | +0.0008 | +0.0040 | +0.0015 | `mixed_or_unclear` |
| `power` | +0.0007 | -0.0030 | -0.0043 | +0.0017 | -0.0071 | +0.0048 | `mixed_or_unclear` |
| `count` | +0.0015 | -0.0052 | -0.0018 | +0.0031 | +0.0005 | -0.0002 | `mixed_or_unclear` |
| `impulse` | -0.0036 | +0.0164 | +0.0270 | -0.0010 | +0.0200 | +0.0197 | `mixed_or_unclear` |

### Большинство полей не имеют самостоятельного сигнала над clock

Из 9 полей только 2 (`back` и `impulse`) дают положительную добавку (`add_val > 0`) на обеих целях. Остальные 7 полей имеют `add_val < 0` хотя бы на одной цели, а 5 (`direction`, `front`, `power`, `count`, `break` на buy) — на обеих. Это значит: добавление **одного** поля к clock не только не помогает, но часто **ухудшает** AUC.

Особенно показателен `front`: `drop_val = -0.0023` (удаление вредит), но `add_val = -0.0070` (добавление тоже вредит). Это классическая картина коррелированного поля — оно дублирует информацию других полей в составе полного профиля, но само по себе шумит.

Вывод: большинство фрактальных полей не несут самостоятельного сигнала над clock; их ценность — только в контексте полного профиля. Это не означает, что их нужно удалить: drop-one показывает, что их удаление вредит. Но и переносить их в новую постановку как «самостоятельно полезные» нельзя.

### Аномальный паттерн `direction`

`direction` — единственное поле с `drop_val > 0` на sell (+0.0026): удаление **улучшает** AUC на val. Но на holdout yearly signs = [-1, -1, -1] — удаление **вредит** на всех 3 годах. Это противоречие: на val удаление помогает, на holdout — вредит. `direction` = {-1, 1} — бинарное поле, и его полезность может зависеть от знака (long/short), который уже закодирован в target (sell vs buy). Это гипотеза, не вывод — Stage 5.1 не проверял взаимодействие полей с target.

### Что не подтвердилось

Поля:

- `direction`
- `front`
- `strong`
- `break`
- `reverse`
- `power`
- `count`

не дали согласованного рисунка. У них наблюдаются либо малые дельты, либо разнонаправленность между seed, либо неустойчивость между `val_stop` и `diagnostic_holdout`.

Особенно важно, что Stage 5.1:

- **не нашёл ни одного поля с итоговым `likely_noise`**

То есть нет надёжного основания сказать, что какое-то структурное поле можно смело выкинуть как бесполезное.

### Таблица итоговых verdicts

| Поле | Overall verdict |
|---|---|
| `direction` | `mixed_or_unclear` |
| `front` | `mixed_or_unclear` |
| `back` | `likely_useful` |
| `strong` | `mixed_or_unclear` |
| `break` | `mixed_or_unclear` |
| `reverse` | `mixed_or_unclear` |
| `power` | `mixed_or_unclear` |
| `count` | `mixed_or_unclear` |
| `impulse` | `mixed_or_unclear` |

## Conclusions

- Stage 5.1 показывает диагностически наблюдаемую прибавку структурных полей над clock-only baseline; это не сводится к одним calendar-признакам.
- Единственное поле, которое прошло диагностический фильтр на обеих целях, — `back` («сила тыловой границы»).
- `back` выглядит наиболее правдоподобным кандидатом на отдельную узкую follow-up проверку, но одиночно захватывает только ~64-74% структурной премии — не заменяет полный профиль.
- Ни одно поле не доказано как `likely_noise`, поэтому Stage 5.1 не даёт права упростить `structure_full` до "всё лишнее, кроме X".
- Ветка `H6_off05` остаётся **DIAGNOSTIC_ONLY** и **не переоткрыта** как торговый кандидат.

## Limitations / Open Questions

- `2023-2025` уже использовались в Stage 5.0f и здесь являются только diagnostic disclosure, а не независимым подтверждением.
- `time_only` — это add-zero baseline, а не trading candidate.
- `lift_30` интерпретируется как bottom-30 risk lift, где меньше = лучше; это не обычный "uplift больше лучше".
- Коррекция множественного тестирования не применялась.
- Verdict `likely_useful` для `back` — это ещё не доказательство production-ценности.
- У `structure_full` сохраняются clock-признаки; Stage 5.1 не доказывает "чисто структурный" сигнал без временной компоненты.
- Не проверялся профиль наподобие `drop_all_noise`; план специально оставляет такой follow-up только на отдельный мини-цикл.
- **Взаимодействия полей не проверялись.** Drop-one/add-one не ловит совместные эффекты: поле может быть полезным только в сочетании с другим (например, `back` + `impulse`). Для проверки нужен отдельный мини-прогон с предзарегистрированными комбинациями.
- **`add_back` сравнивается со слабым baseline.** `time_only` val AUC = 0.635-0.642; большая прибавка `back` над этим baseline доказывает полезность против календаря, но не доказывает, что `back` заменяет полный структурный профиль. Прямое сравнение `time+back` vs `structure_full` не проводилось.
- **Ранний 2026 не подтверждает сильный sell-сигнал.** `structure_full` на sell 2026 даёт AUC 0.5597 (n=316) — близко к 0.5. `time_only` — 0.5294. На buy 2026 лучше: 0.6498 vs 0.5999. Это не доказательство (low-N), но ранний сигнал риска: sell-сигнал может ослабевать на самых свежих данных, что согласуется с Stage 5.0f.

Запрещённые выводы после этого этапа:

- нельзя объявлять Stage 5.1 новым winner;
- нельзя говорить, что `H6_off05` снова стал кандидатом;
- нельзя трактовать `2023-2025` как новый frozen test;
- нельзя объявлять все поля, кроме `back`, бесполезными.

## Validation Split Disclosure

Разделение данных в Stage 5.1:

- `train_core <= 2020`
- `val_stop = 2021-2022`
- `diagnostic_holdout = 2023-2025`
- `low_n_disclosure = 2026`

Правило интерпретации:

- `val_stop` — основной диагностический слой сравнения профилей;
- `diagnostic_holdout` — только disclosure, потому что этот период уже был использован в управленческих выводах Stage 5.0f;
- `2026` раскрывается отдельно как low-N disclosure и не используется для verdict.

Следовательно, Stage 5.1 не создаёт frozen candidate и не даёт подтверждающего статуса.

## Next Step

Самый аккуратный следующий шаг:

- если ветку `H6_off05` ещё имеет смысл диагностировать, делать **один узкий follow-up** вокруг `back`, без нового большого перебора и без claim о кандидате. Предзарегистрированные профили для мини-follow-up: `time_only`, `time+back`, `time+impulse`, `time+back+impulse`, `structure_full`, `structure_full_without_back`. Цель — проверить, заменяет ли `back` (отдельно или с `impulse`) полный профиль, и ловит ли взаимодействие `back`+`impulse`;
- если нужен честный подтверждающий ответ, использовать новый независимый период `2026+`;
- если цель проекта — искать production-кандидата, практичнее менять target/постановку (например, время до пробоя как регрессия — Stage 5.2 из roadmap), а не продолжать большой search по `H6_off05`.

## Related Materials

- JSON artifact: `ML/reports/stage5_1_structural_field_ablation.json`
- План: `docs/superpowers/plans/2026-06-24-stage5_1-structural-field-ablation.md`
- Предыдущий этап: `docs/reports/2026-06-24-stage5_0f-signal-stationarity.md`
- Диагностический no-price reference: `docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md`
- Код раннера: `ML/baseline/benchmark_stage5_transformer_breach.py`
