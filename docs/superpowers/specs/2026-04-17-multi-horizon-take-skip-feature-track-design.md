# Multi-Horizon Take/Skip Feature Track Design

> **Date**: 2026-04-17
> **Status**: Draft approved for implementation
> **Goal**: Проверить, даст ли новый feature track на всех 100 фракталах и multi-scale summaries рабочий `take / skip` сигнал там, где прежние trailing-stop regression, quantile и binary tracks дали `reject`.

## Background

Линия `trailing-stop outcome retraining` уже проверила три варианта на текущем представлении входа:

- `trailing_stop_target_v1` (continuous regression);
- `trailing_stop_target_quantile_v1` (quantile regression);
- `take_skip_trailing_stop_v1` (binary take/skip).

Во всех трёх случаях результат отрицательный:

- лучший validation PF у regression: `0.4206`;
- лучший validation PF у quantile: `0.1750`;
- лучший validation PF у binary take/skip при `trades_per_year >= 6`: `0.274`.

Дополнительная диагностика показала, что в binary track абсолютные probability thresholds вообще не работают, а `top-k` только выбирает "наименее плохие" сделки. Это сильный сигнал, что bottleneck уже не в selection layer, а в самом представлении входа.

Следующий трек должен менять не benchmark, а входные признаки.

## Core Hypothesis

Текущее представление последовательности слишком бедное и теряет структуру движения цены на нескольких масштабах.

Новый трек проверяет гипотезу:

> если подать модели полные 100 фракталов, multi-scale summaries по нескольким окнам и сохранить существующие строковые числовые признаки, то бинарная задача `take / skip` для trailing-stop outcomes может стать различимой.

## Model Scope

Для первого нового трека:

- backbone фиксируется как `Transformer`;
- не сравниваются другие архитектуры;
- цель этапа — изолировать эффект нового feature representation.

Это важно: если в первом же прогоне менять и признаки, и backbone, нельзя будет понять источник улучшения или провала.

## Target Definition

Новый target family остаётся бинарным `take / skip`, но становится multi-horizon и multi-stop.

Для каждого горизонта:

```text
12 / 24 / 48 bars
```

и для каждого trailing-stop параметра:

```text
X = 2 / 4 / 8
```

строится binary label:

```text
take_H_xN = 1, если trail_H_pnl_atr_xN >= 0.5
take_H_xN = 0, иначе
```

Где:

- `H` — горизонт в барах;
- `N` — ATR-множитель trailing-stop;
- threshold `0.5 ATR` — минимально полезный результат сделки.

Таким образом, одна строка получает сразу сетку бинарных outcomes.

## Feature Representation

Новый input состоит из трёх частей.

### 1. Full fractal sequence

Используются все `100` доступных фракталов, а не только урезанный хвост.

Цель — не терять дальний контекст, который может быть важен для формы движения до входа.

### 2. Multi-scale summaries

Поверх той же последовательности считаются сводные признаки по окнам:

```text
5 / 10 / 20 / 50 / 100
```

Эти summaries должны описывать форму движения на нескольких длинах истории.

Точный состав summary family будет зафиксирован в implementation plan, но класс признаков должен покрывать:

- уровень и наклон;
- ускорение или замедление;
- размах и вариативность;
- соотношение благоприятного и неблагоприятного хода;
- последние изменения относительно более длинного окна.

### 3. Existing row-level numeric features

Сохраняются уже существующие отдельные числовые признаки строки, если они не дублируют новые summaries и не ломают shape contract модели.

Иными словами, новый feature track может:

- расширить текущее представление;
- или частично заменить его, если старый формат окажется узким местом.

Жёсткого требования "оставить всё как есть" нет.

## Task Contract

Новый task должен быть отдельной версией, а не переписыванием старого `take_skip_trailing_stop_v1`.

Рабочее имя:

```text
take_skip_trailing_stop_v2
```

Task должен уметь:

- строить binary matrix targets по всей сетке `H × X`;
- экспортировать вероятности и истинные continuous outcomes для benchmark;
- считать classification diagnostics без смешения train и benchmark verdict.

## Benchmark

Benchmark сохраняет validation-first discipline:

1. Candidate search только на validation.
2. Frozen winner применяется на test один раз.

Candidate families на первом этапе:

```text
prob_ge_threshold
top_k_probability
```

Но benchmark должен работать уже с multi-horizon target columns.

PnL считается по continuous trailing-stop outcome соответствующей пары `(H, X)`, а не по binary label.

Обязательные метрики:

- `PF`
- `trades`
- `trades_per_year`
- `negative_year_slices`
- `profit_concentration_top_10`
- `ulcer_index_atr`
- `max_drawdown_atr`

## Success Gate

Первый полный прогон считается содержательно успешным, если найден хотя бы один validation candidate, который:

- имеет `PF > 1`;
- имеет `trades_per_year >= 6`;
- не показывает явный развал по годам.

Это мягкий исследовательский порог, не production gate.

## Non-Goals

- Не менять MT4 execution.
- Не вводить новую сложную логику выхода.
- Не сравнивать несколько backbone в первом прогоне.
- Не делать production productization.
- Не превращать benchmark в большой бесконтрольный перебор формул.

## Expected Outcome

Этот этап должен дать один из двух жёстких выводов:

1. Новый feature representation оживляет `take / skip` постановку и даёт хотя бы один validation candidate с `PF > 1`.
2. Даже после смены feature representation Track A-family остаётся мёртвой, и тогда следующий шаг должен менять уже не только признаки, но и саму постановку задачи.
