# Signal Research Variant 3 Prep

> **Date**: 2026-04-02
> **Status**: Completed
> **Goal**: Завершить подготовительный этап по группам сигналов перед полным тестом entry-сценариев Variant 3
> **Related plan/spec**: [docs/superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md](../superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md), [docs/superpowers/plans/2026-04-02-signal-research-variant-3-prep.md](../superpowers/plans/2026-04-02-signal-research-variant-3-prep.md)
> **Related commit**: pending

## Контекст

Signal Research Variant 2 показал, что текущий ML-сигнал больше похож на слабый drift, чем на сильный импульс. Этого хватило, чтобы перейти к следующему вопросу, но не хватило, чтобы ответить на него: какие подгруппы сигналов стоит тестировать в Variant 3 в первую очередь и где именно сосредоточить исследование времени входа.

Этот этап был нужен, чтобы не запускать `market / pullback / delayed / cancel-window` вслепую на всём пуле сигналов. Заодно он закрыл расхождение по волатильности между MT4 и Python: `atr14` добавили в канонический OHLC export.

Завершённый OOS run использовал `MT/MQL4/Files/ml_signals.csv` вместе с `DATA/XAUUSD_H1_OHLC.csv` на периоде `2022-07-18 11:00:00 — 2026-03-20 06:00:00` и дал `2603` реальных BUY/SELL сигналов с excursion-данными.

## Что сделано

- Расширен `MT/MQL4/Scripts/ExportOHLC.mq4`: теперь MT4 export пишет канонический `atr14`.
- Обновлён `API/signal_research.py`: сначала используется `atr14` из CSV, а Python ATR остаётся как fallback для старых OHLC-файлов.
- Добавлена аннотация фиксированного baseline `12H / SL=5 / TP=50`.
- Добавлены новые секции отчёта prep-этапа: `Cohort Map`, `Entry Opportunity Profile`, `Stability Split`, `Priority Cohorts`.
- Расширен `tests/test_signal_research.py`: покрыты загрузка канонического ATR, baseline-сводки по группам, расчёты entry-opportunity и новые секции отчёта.
- Повторно запущен OOS research flow на обновлённом OHLC-файле, где уже есть `atr14`.
- Этап закрыт с каноническим отчётом, записью в `CHANGELOG` и обновлённым `CONTEXT_HANDOFF`.

## Изменённые файлы

- `API/signal_research.py`
- `tests/test_signal_research.py`
- `MT/MQL4/Scripts/ExportOHLC.mq4`
- `docs/DATA_FLOW.md`
- `docs/superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md`
- `docs/superpowers/plans/2026-04-02-signal-research-variant-3-prep.md`
- `docs/reports/2026-04-02-signal-research-variant-3-prep.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`

## Проверка

Команды проверки, использованные на этапе:

```bash
python -m pytest tests/test_signal_research.py -q
python -m API.signal_research --test-only
```

## Результаты

### Основная OOS-сводка

| Метрика | Значение |
|---|---:|
| OOS-период | `2022-07-18 11:00:00 — 2026-03-20 06:00:00` |
| Реальные BUY/SELL сигналы | `2603` |
| Базовый сетап | `12H / SL=5 / TP=50` |
| Базовый PF | `1.05` |
| Базовый AvgPnL | `0.2` |
| Широкий `BUY PF_12` | `1.35` |
| Широкий `SELL PF_12` | `0.95` |
| Широкий `ATR Q4 PF_12` | `1.23` |
| Широкий `non-Q4 PF_12` | `1.02` |
| Лучший широкий ratio-бакет | `4-5` |
| Устойчивый анти-паттерн | `3-4` |

### Проверка извлечения `pic_price`

Перед использованием `pic_price` как anchor для Variant 3 логика извлечения была проверена на `DATA/XAUUSD_H1_OHLC.csv` по всей deduplicated-выборке `Nero.csv`:

- validated rows: `58766`
- match to fractal-bar `High/Low` within `0.05` price tolerance: `100.0%`
- peak rows (`direction=1`) vs `High`: `100.0%`
- trough rows (`direction=-1`) vs `Low`: `100.0%`
- max absolute error: `0.05`
- median absolute error: `0.02`

Это подтверждает, что исследовательский anchor `pic_price` совпадает с реальным fractal-баром в OHLC-терминах; маленькая ненулевая ошибка — это эффект округления/шага цены, а не ошибка выбора бара.

### Приоритетные группы для Variant 3

| Cohort | N | PF_12 | Net_12 mean | AvgPnL_baseline |
|---|---:|---:|---:|---:|
| `ratio 4-5 × ATR Q4` | 101 | 2.62 | 22.2 | 1.4 |
| `ratio 4-5` | 369 | 1.95 | 6.4 | 0.5 |
| `BUY` | 1375 | 1.35 | 2.4 | 0.9 |
| `ATR Q4` | 649 | 1.23 | 4.1 | 0.5 |

### Группы с устойчиво слабым поведением

| Cohort | N | PF_12 | Net_12 mean | AvgPnL_baseline |
|---|---:|---:|---:|---:|
| `ratio 3-4` | 941 | 0.87 | -1.2 | -0.3 |
| `SELL` | 1228 | 0.95 | -0.5 | -0.6 |
| `non-Q4` | 1954 | 1.02 | 0.1 | 0.1 |
| `ratio 5+` | 658 | 1.05 | 0.3 | -0.0 |

### Главное из Entry Opportunity Profile

После перевода prep-профиля с порогов в raw-price на ATR-normalized пороги картина пути стала более сдержанной и более полезной для интерпретации:

| Cohort | `pullback>=1ATR_1H` | `fav>=1ATR_1H` | `fav>=3ATR_6H` | `close>0_6H` |
|---|---:|---:|---:|---:|
| `ratio 4-5 × ATR Q4` | `12.9%` | `24.8%` | `13.9%` | `51.5%` |
| `ATR Q4` | `12.6%` | `16.2%` | `10.2%` | `51.4%` |
| `ratio 4-5` | `21.1%` | `20.6%` | `11.1%` | `52.8%` |
| `non-Q4` | `19.2%` | `18.5%` | `11.6%` | `49.6%` |

Важная поправка: прежнее впечатление из raw-price, что «Q4 даёт намного более глубокие pullback», в основном оказалось артефактом масштаба волатильности. После ATR-нормализации частота раннего pullback уже не выглядит сильным разделителем, и широкий `non-Q4` не показывает заметно худшую нормализованную глубину pullback.

Что осталось после нормализации — это сторона continuation: топ-группа shortlist `ratio 4-5 × ATR Q4` остаётся лучшей по раннему favorable-профилю `fav>=1ATR_1H` и по длинному окну `fav>=3ATR_6H`, при этом `close>0_6H` у shortlist-групп близок.
Пороги вида `...>=kATR...` в этом этапе — описательные prep-метрики, а не фиксированные смещения для limit-входа в Variant 3.

### Главное по устойчивости

- `ratio 3-4` оставался слабым во все показанные годы: `PF_12 = 0.78, 0.80, 0.81, 0.99, 0.83`.
- `ratio 4-5` был слабым в `2022-2023`, стал положительным в `2024` и заметно усилился в `2025-2026`.
- Широкий `SELL` оставался слабым в `2023-2025` и улучшился только в `2026`, поэтому он всё ещё чувствителен к режиму рынка.
- `ATR Q4` заметно усилился в поздние OOS-годы, особенно в `2025-2026`.

## Выводы

Variant 3 prep дал реальный статистический результат, а не только tooling:

- самая сильная группа для следующего этапа — `ratio 4-5 × ATR Q4`;
- `ratio 4-5` остаётся лучшим широким ratio-бакетом и должен оставаться в основном shortlist;
- `ratio 3-4` остаётся устойчивым анти-паттерном и должен использоваться как отрицательный контроль, а не как кандидат;
- широкий `SELL` всё ещё слишком слабый, чтобы считать его основной целью Variant 3 без дополнительной фильтрации;
- `ATR Q4` остаётся самым понятным режимным разделением для фокуса на entry-сценариях;
- `pic_price` теперь проверен как надёжный research anchor относительно OHLC `High/Low`, поэтому pic-сценарии Variant 3 можно сравнивать статистически;
- ATR-normalized prep-метрики показывают, что сильные группы по-прежнему лучше на стороне favorable continuation, но не показывают явно большей нормализованной глубины pullback; поэтому `pullback` нужно считать рабочей гипотезой для теста, а не уже «доказанным» фактом.

Этап также уточнил важный нюанс: даже сильные группы могут иметь низкий `TP_FIRST%` на фиксированном baseline `12H / SL=5 / TP=50`, потому что `TP=50` далеко, и много строк заканчиваются как `SL_FIRST` или `NEITHER`. Поэтому ценность этапа не в том, что «готовое торговое правило найдено», а в том, что «понятно, где дальше имеет смысл тратить время на исследование входа».

## Ограничения / открытые вопросы

На этом этапе ещё не симулировались реальные entry-политики Variant 3. Он только подготовил доказательную базу и shortlist.

Главные оставшиеся вопросы:

- превосходит ли `pullback`-вход `market` на `ratio 4-5 × ATR Q4`;
- лучше ли `delayed`-вход, чем немедленный вход, для `ATR Q4`, или это работает только для самых сильных ratio-групп;
- стоит ли держать `ratio 5+` только как вторичный benchmark, а не как основной кандидат;
- можно ли улучшить `SELL` более строгими cohort-фильтрами, или это в основном режимный артефакт в данном OOS-периоде.

## Следующий шаг

Запустить полный тест entry-сценариев Variant 3 на shortlist из этого этапа:

- основные группы: `ratio 4-5 × ATR Q4`, `ratio 4-5`, `BUY`, `ATR Q4`;
- отрицательные контроли: `ratio 3-4`, `non-Q4`;
- сценарии: `market`, `pullback limit entry`, `delayed entry`, `cancel-window`;
- параметризация `pullback` и `cancel-window`: адаптивные смещения `ATR14 * k` при `k=1,2,3` (вместо фиксированных абсолютных смещений цены), с двумя anchor-вариантами `entry_close` и `pic_price`; `pic_price` должен браться из реального fractal `price` в raw `Nero.csv` после построчного упорядочивания по embedded fractal time (аналогично `label_main.py`), а не из нормализованного labeled-выхода.

Цель следующего этапа — сравнить эти способы входа явно на shortlist-группах, а не на полном наборе сигналов.

## Связанные материалы

- [docs/reports/2026-04-01-signal-research-variant-2.md](2026-04-01-signal-research-variant-2.md)
- [docs/superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md](../superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md)
- [docs/superpowers/plans/2026-04-02-signal-research-variant-3-prep.md](../superpowers/plans/2026-04-02-signal-research-variant-3-prep.md)
