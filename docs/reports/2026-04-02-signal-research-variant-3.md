# Signal Research Variant 3

> **Date**: 2026-04-02
> **Status**: Completed
> **Goal**: Реализовать и запустить в Python полную матрицу entry-сценариев Variant 3 на shortlist-группах и на отрицательных контролях
> **Related plan/spec**: [docs/superpowers/specs/2026-04-02-signal-research-variant-3-design.md](../superpowers/specs/2026-04-02-signal-research-variant-3-design.md), [docs/superpowers/plans/2026-04-02-signal-research-variant-3.md](../superpowers/plans/2026-04-02-signal-research-variant-3.md)
> **Related commit**: pending

## Контекст

Variant 2 показал, что текущий ML-сигнал больше похож на слабый drift, чем на сильный импульс. После этого Variant 3 Prep сузил shortlist до `ratio 4-5 × ATR Q4`, `ratio 4-5`, `BUY` и `ATR Q4`. Группы `ratio 3-4` и `non-Q4` оставили как отрицательные контроли.

Не хватало честного сравнения способов входа при одинаковых условиях по времени и барьерам. Чтобы результатам матрицы можно было доверять, нужно было сделать две вещи:

- брать `pic_price` из реального fractal `price` в сыром `Nero.csv`, а не из приближённого источника;
- сравнивать pending-сценарии при одной и той же базовой геометрии `12H / SL=5 / TP=50` и одинаковом сроке `t+12`.

Этот этап закрывает этот пробел и расширяет `API/signal_research.py` от Variant 2 / Prep до полной Variant 3 execution-логики.

## Что сделано

- Расширен `API/signal_research.py`: добавлена полная симуляция Variant 3 для `market`, `pullback`, `delayed`, `cancel-window`.
- Добавлено извлечение raw `pic_price` из `MT/MQL4/Files/Nero.csv`: берётся самый поздний встроенный fractal в строке через `fractal_time`, после чего применён такой же dedupe по `time`, как и для сигналов.
- Добавлена секция `Pic Price Validation` против `DATA/XAUUSD_H1_OHLC.csv`: проверка по времени fractal и ожидаемой стороне `High/Low`.
- Для `pullback` и `cancel-window` добавлены ATR-смещения вместо фиксированных смещений в цене:
  - `entry_close - ATR14 * k`, `k=1,2,3` для `BUY`, зеркально для `SELL`;
  - `pic_price`, `pic_price + ATR14`, `pic_price - ATR14`, с корректным учётом направления.
- В CLI-отчёт добавлены три секции:
  - `Variant 3 Scenario Matrix`
  - `Variant 3 Shortlist Verdict`
  - `Variant 3 Negative Controls`
- Добавлен слой robustness поверх полной Variant 3 матрицы:
  - support ladder `10/5 -> 20/10 -> 30/10 -> 40/15` для `N_filled` и `fill_pct`;
  - дельты к baseline `market` для той же группы (`PF_delta`, `AvgPnL_delta`);
  - более строгий shortlist verdict: нужен положительный uplift и support tier не ниже `Supported` (`30/10` или `40/15`), а не выбор строки только по сырому `PF` при малом числе fill.
- Расширен `tests/test_signal_research.py`: покрыты raw fractal parsing, выбор последнего fractal в строке, сохранение `pic_price`, OHLC validation, логика limit-fill, сценарные исходы и smoke-тест отчёта Variant 3.
- Дополнительно расширены тесты для robustness-аннотаций, проверки support ladder по уровням и нового строгого shortlist verdict.
- После robustness-pass повторно запущен OOS CLI и сделано сравнение основных групп с отрицательными контролями при одном и том же support-фильтре.

## Изменённые файлы

- `API/signal_research.py`
- `tests/test_signal_research.py`
- `docs/superpowers/specs/2026-04-02-signal-research-variant-3-design.md`
- `docs/superpowers/plans/2026-04-02-signal-research-variant-3.md`
- `docs/reports/2026-04-02-signal-research-variant-3.md`
- `docs/reports/2026-04-02-signal-research-variant-3-prep.md`
- `docs/superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`

## Проверка

Команды проверки, которые использовались на этапе:

```bash
./.venv/bin/python -m pytest tests/test_signal_research.py -q
./.venv/bin/python -m API.signal_research --test-only
```

## Результаты

### OOS-покрытие и проверка anchor

Свежий OOS CLI run использовал период `2022-07-18 11:00:00 — 2026-03-20 06:00:00` и дал:

- `9403` merged-строк сигналов в test-only срезе;
- `2603` реальных BUY/SELL сигналов с excursion-данными;
- `9403 / 9403` совпадений OOS `pic_price` с ожидаемой стороной OHLC `High/Low` в пределах допустимой погрешности.

Это снимает последнее крупное замечание по целостности данных для pic-сценариев: anchor теперь статистически надёжен и прозрачно связан с исходным raw-признаком.

### Главное по матрице на основных группах

Матрица действительно показывает заметное улучшение относительно `market` на основных группах, если разрешить более глубокий pullback-вход:

| Cohort | `market PF` | Лучший кандидат при `N_filled>=20` и `fill_pct>=10` | Candidate PF | Fill |
|---|---:|---|---:|---:|
| `ratio 4-5 × ATR Q4` | `1.34` | `pullback pic_price-1ATR` | `6.20` | `22 / 101` (`21.8%`) |
| `ratio 4-5` | `1.15` | `pullback entry_close-3ATR` | `3.55` | `54 / 369` (`14.6%`) |
| `BUY` | `1.27` | `pullback entry_close-3ATR` | `2.35` | `227 / 1374` (`16.5%`) |
| `ATR Q4` | `1.12` | `pullback entry_close-3ATR` | `2.57` | `106 / 648` (`16.4%`) |

То есть первый вывод Variant 3 не такой, что «market лучший». Матрица прямо показывает, что более поздний и более глубокий вход может улучшать итог по выбранным группам.

### Отрицательные контроли тоже улучшаются

Более важный факт: похожий рост есть не только у shortlist-групп.

| Control cohort | `market PF` | Сильный кандидат при том же robustness-фильтре | Candidate PF | Fill |
|---|---:|---|---:|---:|
| `ratio 3-4` | `0.92` | `pullback entry_close-3ATR` | `1.62` | `193 / 940` (`20.5%`) |
| `non-Q4` | `1.02` | `cancel-window entry_close-1ATR@1b` | `1.41` | `375 / 1954` (`19.2%`) |

Это значит, что текущий рост `PF` в Variant 3 пока нельзя считать чисто cohort-специфичным преимуществом. На этом этапе часть эффекта выглядит как общий execution-эффект от более выгодной цены входа.

### Robustness-pass убирает winners с малым числом fill

Чтобы shortlist не реагировал на тонкие хвосты, готовая матрица была пересчитана при четырёх support-уровнях:

- `10/5`: `N_filled >= 10`, `fill_pct >= 5%`
- `20/10`: `N_filled >= 20`, `fill_pct >= 10%`
- `30/10`: `N_filled >= 30`, `fill_pct >= 10%`
- `40/15`: `N_filled >= 40`, `fill_pct >= 15%`

Это сразу показало проблему старого verdict:

- `ratio 4-5`: старый winner `cancel-window entry_close-3ATR@1b` исчезает, потому что у него всего `3` fill;
- `BUY`: старый winner `cancel-window entry_close-3ATR@1b` исчезает, потому что у него всего `14` fill;
- `ATR Q4`: старый winner `cancel-window entry_close-3ATR@1b` исчезает, потому что у него всего `6` fill;
- `ratio 4-5 × ATR Q4`: яркая строка `pullback pic_price-1ATR` остаётся интересной, но проходит только `20/10`, поэтому ниже нового порога verdict.

Самый сильный практический shortlist после нового фильтра:

| Cohort | Robust survivor | Support tier | `PF` | `PF_delta vs market` | Fill |
|---|---|---|---:|---:|---:|
| `ratio 4-5 × ATR Q4` | `pullback entry_close-2ATR` | `Supported` | `3.69` | `+2.35` | `36 / 101` (`35.6%`) |
| `ratio 4-5` | `pullback entry_close-3ATR` | `Supported` | `3.55` | `+2.39` | `54 / 369` (`14.6%`) |
| `BUY` | `pullback entry_close-3ATR` | `Strong` | `2.35` | `+1.08` | `227 / 1374` (`16.5%`) |
| `ATR Q4` | `pullback entry_close-3ATR` | `Strong` | `2.57` | `+1.45` | `106 / 648` (`16.4%`) |

Итог: более строгий verdict не убил гипотезу pullback. Он убрал артефакты хвостов и оставил более узкий и более чистый набор кандидатов.

### Основные группы против отрицательных контролей при одном фильтре

Если применить ту же логику verdict к отрицательным контролям:

| Control cohort | Лидер при том же фильтре | Support tier | `PF` | `PF_delta vs market` | Fill |
|---|---|---|---:|---:|---:|
| `ratio 3-4` | `pullback entry_close-3ATR` | `Strong` | `1.62` | `+0.69` | `193 / 940` (`20.5%`) |
| `non-Q4` | `cancel-window entry_close-1ATR@1b` | `Strong` | `1.41` | `+0.39` | `375 / 1954` (`19.2%`) |

Ключевое разделение по переносимости:

- широкий `pullback entry_close-3ATR` всё ещё улучшает контроли, поэтому это скорее общий «вход по лучшей цене», а не уникальный эффект отдельной группы;
- у основных групп улучшение заметно сильнее, особенно у `ratio 4-5` и `ATR Q4`;
- самый чистый cohort-специфичный survivor сейчас: `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR`.

Для топ-группы тот же `entry_close-2ATR` на контролях заметно слабее:

- `ratio 4-5 × ATR Q4`: `PF=3.69`, `PF_delta=+2.35`, `36` fill;
- `ratio 3-4`: `PF=1.13`, `PF_delta=+0.21`, `342` fill;
- `non-Q4`: `PF=1.04`, `PF_delta=+0.01`, `663` fill.

Значит `entry_close-2ATR` не просто «улучшает всё подряд»; самый сильный uplift остаётся в лучшей shortlist-группе.

## Выводы

Variant 3 теперь реализован и полностью запускается в `API/signal_research.py`.

Полная матрица вместе с robustness-pass дала четыре практических вывода:

- `pic_price` теперь проверен и валиден как anchor для исследования, поэтому pic-сценарии можно сравнивать статистически;
- старый verdict по сырому `PF` действительно был слишком мягким и поднимал кандидатов с малым числом fill;
- после явного support-фильтра `pullback` всё ещё лидирует в shortlist, но широкий класс `entry_close-3ATR` только частично cohort-специфичен, так как тоже улучшает контроли;
- для будущего EA prototyping остаётся один квалифицированный кандидат: `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR`.

Этот кандидат ещё нельзя назвать «готовым к production», но это первая строка Variant 3, где одновременно есть:

- не маленькая поддержка (`36` fill, `35.6%` fill rate);
- сильный прирост относительно своего `market` baseline (`PF 1.34 -> 3.69`);
- отсутствие сопоставимого прироста на `ratio 3-4` и широком `non-Q4`.

Поэтому этап перестал быть только про tooling. Теперь есть фильтрованный статистический итог: для EA-прототипа есть правдоподобный кандидат, но только один выглядит действительно чище общего эффекта «более глубокого входа».

## Ограничения / открытые вопросы

- Даже самый чистый кандидат `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR` имеет только `36` fill в OOS-срезе. Это средняя поддержка, а не крупная выборка.
- Сравнение всё ещё идёт на фиксированном baseline `12H / SL=5 / TP=50`. Выбор входа выглядит перспективно, но геометрия барьеров остаётся жёсткой.
- `pullback entry_close-3ATR` всё ещё улучшает отрицательные контроли, поэтому его стоит считать широким benchmark-правилом, а не чистым cohort-специфичным открытием.
- Часть сильных exploratory-строк всё ещё ниже нового support-порога. Их нужно оставлять только в research, не в prototype shortlist.

## Next Step

Если проект идёт дальше от research к EA prototyping, начинать стоит только с фильтрованного winner:

- основной prototype-кандидат: `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR`;
- `pullback entry_close-3ATR` для `ratio 4-5` / `BUY` / `ATR Q4` оставить как широкий research benchmark, а не как столь же чистый production-кандидат.

Перед изменениями в EA самый безопасный дополнительный шаг — ещё один Python-only robustness-check для winner:

- year-split устойчивость для `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR`;
- чувствительность к близкой геометрии барьеров при том же фиксированном правиле входа.

## Related Materials

- [docs/reports/2026-04-01-signal-research-variant-2.md](2026-04-01-signal-research-variant-2.md)
- [docs/reports/2026-04-02-signal-research-variant-3-prep.md](2026-04-02-signal-research-variant-3-prep.md)
- [docs/superpowers/specs/2026-04-02-signal-research-variant-3-design.md](../superpowers/specs/2026-04-02-signal-research-variant-3-design.md)
- [docs/superpowers/plans/2026-04-02-signal-research-variant-3.md](../superpowers/plans/2026-04-02-signal-research-variant-3.md)
