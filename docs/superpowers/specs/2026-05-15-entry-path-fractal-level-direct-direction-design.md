# Entry Path Fractal Level Direct Direction Design

> **Date**: 2026-05-15
> **Status**: Draft
> **Track**: Entry path direction-source redesign
> **Goal**: Заменить фиксированное направление из `fractal0.direction` на модель, которая сама выбирает `SELL / SKIP / BUY` по текущей строке фракталов.
> **Related materials**: `docs/superpowers/plans/2026-05-15-entry-path-all-rows-level-signal.md`, `docs/reports/2026-05-14-entry-path-direct-bar-model.md`, `docs/reports/2026-05-14-entry-path-all-rows-ranking.md`, `docs/reports/2026-05-14-entry-path-causal-surrogate.md`

## Контекст

Предыдущий план `Entry Path All-Rows Level Signal` был остановлен на Task B.
Проверка не подтвердила, что `fractal0.direction` можно использовать как
надёжное направление сделки.

Значит дальше нельзя строить цели A/C/D в сторону сделки, заданную
`fractal0.direction`. Иначе модель будет искать сильный уровень, но входить в
направлении, которое не доказало полезность.

Новая ветка исследования сохраняет идею сильного уровня по всей строке
фракталов, но меняет источник направления:

```text
раньше: direction = fractal0.direction
теперь: direction = output модели
```

## Цель

Построить live-safe модель, которая для каждой текущей строки фракталов выдаёт:

```text
-1 = SELL
 0 = SKIP
 1 = BUY
```

Модель должна сама решить две вещи:

1. есть ли сильный уровень около `fractal0.price`;
2. в какую сторону от этого уровня стоит торговать.

## Что переиспользуем из старого плана

Старый план не выбрасывается. Из него остаются полезные защитные части:

- live-safe audit текущей строки;
- работа только с `time`, `ATR`, `fractal0..fractal99` как входными полями;
- исключение `fractal0.Up/Dn` из признаков;
- использование `fractal1..fractal99.Up/Dn` только как исторической реакции,
  если они есть в текущей строке;
- признаки уровня: расстояние от `fractal0.price`, зоны, ближайшие фракталы по
  цене;
- `feature_contract.json`;
- train-only нормализация;
- сравнение со старыми результатами;
- old-score режим только как диагностика;
- `ML Leakage Preflight` перед test.

## Что меняется

Удаляется ключевое допущение:

```text
fractal0.direction задаёт направление сделки
```

В новой ветке:

- `fractal0.direction` можно использовать как обычный входной признак;
- `fractal0.direction` нельзя использовать как готовое направление;
- target строится отдельно для BUY и отдельно для SELL;
- финальная цель становится трёхклассовой: `SELL / SKIP / BUY`.

## Построение целей

Для каждой строки считаются два независимых будущих результата:

```text
buy_result
sell_result
```

BUY считается так, будто мы открыли покупку на следующем баре.
SELL считается так, будто мы открыли продажу на следующем баре.

Для каждой стороны строятся те же семейства целей, но без опоры на
`fractal0.direction`.

### Target A: быстрый отскок

Для BUY:

```text
buy_adv_6_atr < N
buy_fav_6_atr >= Y
```

Для SELL:

```text
sell_adv_6_atr < N
sell_fav_6_atr >= Y
```

### Target C: отскок с ограниченным риском

Для BUY:

```text
buy_fav_24_atr >= X
buy_adv_12_atr <= Y
```

Для SELL:

```text
sell_fav_24_atr >= X
sell_adv_12_atr <= Y
```

### Target D: trailing-прибыль

Target D строится только по OHLC path, отдельно для BUY и SELL.

Правило:

```text
entry = open следующего бара
BUY: best_high, stop = best_high - N * ATR
SELL: best_low, stop = best_low + N * ATR
```

Если в одном OHLC-баре возможны и новый лучший экстремум, и stop, применяется
консервативная политика: выбирается менее выгодный для кандидата порядок.

## Преобразование BUY/SELL целей в класс

Для каждой target family:

```text
buy_good = BUY target positive
sell_good = SELL target positive
```

Базовое правило первого этапа:

```text
buy_good=True,  sell_good=False -> BUY
buy_good=False, sell_good=True  -> SELL
иначе                         -> SKIP
```

Если обе стороны хорошие, первая версия ставит `SKIP`. Причина: это
неоднозначная строка, и на первом этапе лучше не учить модель на спорном
направлении.

## Входные признаки

Вход модели строится по текущей строке фракталов:

```text
time, ATR, fractal0..fractal99
```

Запрещено использовать как вход:

- `source["signal"]`;
- `predict`;
- будущие `ret_*`;
- будущие `fav_*` / `adv_*`;
- target D outcomes;
- любые колонки, созданные offline-разметкой.

Разрешены:

- `fractal0.price` как точка отсчёта;
- поля `fractal0`, кроме `fractal0.Up/Dn`;
- поля `fractal1..fractal99`, включая накопленные `Up/Dn`, если они прочитаны
  из текущей строки;
- локальные признаки уровня, построенные из текущей строки.

## Первые входные представления

Первый проход не должен быть слишком широким.

Порядок:

1. `nearest_k16` по цене.
2. Если есть потенциал, добавить `zones`.
3. Если есть потенциал, добавить `zones_plus_nearest_k16`.

`K=8`, `K=32`, все 100 фракталов и переменная длина входа остаются вторым
этапом.

## Старый score

Старый score не является production-частью нового решения.

Его можно использовать только в режиме диагностики:

```text
mode = old_score_diagnostic
```

Порог:

```text
original_score_threshold = -0.07158749
```

Основное доказательство качества:

```text
mode = standalone
```

## Сравнение с базой

Новый вариант сравнивается минимум с:

| Baseline | Test PF | Sequential PF | Trades / sequential trades |
|---|---:|---:|---:|
| all-rows ranking | 0.9134 | 0.5908 | 329 / 133 |
| causal surrogate | 1.1537 | 1.4111 | 36 / 31 |
| direct bar model | 1.1141 | 1.1334 | 1277 / 274 |

Главная база сравнения здесь — direct bar model, потому что он тоже решает
направление как выход модели.

## Критерии прохождения research-этапа

Минимальный research-pass:

- standalone test PF > 1.2;
- standalone sequential PF > 1.1;
- test trades >= 100;
- результат не хуже direct-bar baseline по смысловым метрикам;
- нет очевидной зависимости от old-score diagnostic режима;
- leakage preflight = PASS.

Production-candidate этим этапом не объявляется. Для production позже нужны:

- spread/commission/slippage;
- MT4 parity;
- drawdown;
- bootstrap/confidence interval;
- online/runtime parity.

## Стоп-условия

Остановить ветку до test, если:

- live-safe audit не проходит;
- target BUY/SELL слишком редкие;
- validation не даёт standalone-кандидата с достаточным числом сделок;
- победитель появляется только в `old_score_diagnostic`;
- winner выбран на конфигурации с высоким риском переобучения.

