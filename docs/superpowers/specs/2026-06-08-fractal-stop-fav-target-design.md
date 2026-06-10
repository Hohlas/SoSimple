# Fractal Stop + Fav Target — спецификация

Дата: 2026-06-10

## Статус

Спецификация обновлена после аудита и обсуждения терминов.

Реализацию не начинать до отдельного плана реализации и явного согласования.

## Цель

Проверить, есть ли в текущих фрактальных признаках информация о будущем пробое
уровня `fractal0`.

Первый этап намеренно упрощён: модель предсказывает только факт пробоя уровня за
горизонт `H`. В этом этапе нет входа в сделку, TP, timeout, PnL и PF.

Если первый этап показывает полезный сигнал, вторым этапом проверяется торговая
постановка:

- вход после подтверждения `fractal0`;
- стоп за уровнем `fractal0`;
- TP от предсказанного благоприятного хода;
- оценка по фактическому PnL, а не по одному факту пробоя.

## Мотивация

Старые цели `up_*`, `dn_*`, `ret_*`, `fav_*`, `adv_*` отвечают на вопрос, куда
цена могла сходить. Но для стопа за `fractal0` сначала нужно ответить на более
простой вопрос: будет ли уровень пробит против предполагаемой сделки.

Если модель не умеет предсказывать пробой уровня, торговая постановка со стопом
за этим уровнем вряд ли будет устойчивой.

## Момент решения

`fractal0` становится доступен только после закрытия подтверждающего бара. Поэтому
вход по `Close[row]` невозможен.

Для исследовательской проверки полного торгового слоя на истории используется:

```text
entry_price = Open[row+1]
```

Это самая ранняя исполнимая приближенная цена. В реальной торговле цена может
быть чуть позже из-за записи строки, watcher polling, preprocessing, inference и
отправки ордера. Вывод для рабочего контура требует доказательства задержки или
проверки исполнения в MT4 tester.

В первом этапе "только пробой уровня" `entry_price` не используется.

## Источник кандидатов

Кандидат для рабочего контура не использует `signal`.

Причина: в raw `Nero.csv` поле `signal` всегда равно `0`, а в размеченных данных
оно строится оффлайн по будущему. Поэтому `signal != 0` является фильтром
кандидатов, построенным по будущим данным.

Разметка строится для всех строк с валидным `fractal0.dir`:

| `fractal0.dir` | Смысл уровня | Сторона |
|---:|---|---:|
| `-1` | впадина | BUY |
| `1` | пик | SELL |

```text
direction = -fractal0.dir
```

`signal` допустим только для диагностического сравнения, не для фильтра рабочего
контура.

## Термины и единицы

Имена терминов используют суффиксы:

- `_price` — конкретная цена на графике;
- `_val` — величина движения, расстояния или PnL в ATR-единицах;
- `_flag` — бинарный факт события `0/1`;
- `predict_...` / `pred_...` — предсказание модели.

Базовые величины:

```text
H = 6 или 12
atr = ATR[row]
fractal_price = fractal0.price
fractal_dir = fractal0.dir
direction = -fractal_dir
stop_offset_val = 0.2 или 0.5
```

`stop_offset_val` — отступ за уровень в ATR-единицах.

Окно `row+1 : row+H` во всех формулах означает `H` закрытых H1-баров после
строки `row`, включая бар `row+H`.

## Этап 1: Только пробой уровня

### Гипотеза

Фрактальные признаки позволяют предсказать, будет ли пробит уровень `fractal0`
против предполагаемой сделки за `H` баров.

### Разметка

Для BUY:

```text
stop_buy_price = fractal_price - stop_offset_val * atr
buy_stop_broken_H_flag =
    any(Low[row+1 : row+H] <= stop_buy_price)
```

Для SELL:

```text
stop_sell_price = fractal_price + stop_offset_val * atr
sell_stop_broken_H_flag =
    any(High[row+1 : row+H] >= stop_sell_price)
```

`buy_stop_broken_H_flag` и `sell_stop_broken_H_flag` — целевые переменные,
построенные по будущим данным. Они не могут быть входными признаками.

### Предсказание

Для строки с BUY-стороной:

```text
predict_break =
    P(buy_stop_broken_H_flag = 1 | current_features)
```

Для строки с SELL-стороной:

```text
predict_break =
    P(sell_stop_broken_H_flag = 1 | current_features)
```

`predict_break` — вероятность пробоя уровня. Это не факт пробоя и не торговый
PnL.

### Первый эксперимент

- модель: простая RF-модель;
- горизонты: `H = 6`, `H = 12`;
- `stop_offset_val`: минимум `0.2` и `0.5`;
- `stop_offset_val = 0.0` только как диагностический крайний случай;
- строки: все строки с валидным `fractal0.dir`;
- стороны BUY/SELL считать и показывать отдельно;
- пороги выбирать только на train/validation;
- test использовать один раз после freeze.

### Метрики

| Метрика | Смысл |
|---|---|
| AUC | Умеет ли модель ранжировать строки по вероятности пробоя |
| PR-AUC | Качество при дисбалансе классов |
| доля пробоев | Средняя доля пробоев уровня |
| lift низкого риска | Насколько редко уровень пробивается в строках с низким `predict_break` |
| срезы по годам | Есть ли годы, где сигнал исчезает |
| BUY/SELL срезы | Нет ли скрытого провала одной стороны |

Торговые выводы из этапа "только пробой уровня" запрещены. Он отвечает только
на вопрос: есть ли информация о будущем пробое уровня.

## Этап 2: Торговый слой

Переходить к этому этапу можно только если этап "только пробой уровня"
показывает полезный и устойчивый сигнал.

### Постановка стопа

Для BUY:

```text
stop_buy_price = min(fractal_price, entry_price) - stop_offset_val * atr
stop_buy_val = (entry_price - stop_buy_price) / atr
```

Для SELL:

```text
stop_sell_price = max(fractal_price, entry_price) + stop_offset_val * atr
stop_sell_val = (stop_sell_price - entry_price) / atr
```

Такая постановка стопа всегда ставит стоп за входом:

- BUY: стоп ниже `entry_price`;
- SELL: стоп выше `entry_price`.

Крайний случай `stop_buy_val <= 0` или `stop_sell_val <= 0` должен считаться
ошибкой разметки. На практике он возможен только при `stop_offset_val = 0` и
полном совпадении `entry_price` с `fractal_price`.

### Благоприятный ход

Для BUY:

```text
target_buy_val =
    max(High[row+1 : row+H] - entry_price) / atr
```

Для SELL:

```text
target_sell_val =
    max(entry_price - Low[row+1 : row+H]) / atr
```

`target_buy_val` и `target_sell_val` — целевые переменные, построенные по будущим
данным. Они не могут быть входными признаками.

Предсказания модели:

```text
pred_buy_val
pred_sell_val
```

### Торговое правило

Для BUY:

```text
enter_buy = (
    predict_break < p
    and pred_buy_val > min_fav_val
    and pred_buy_val / stop_buy_val >= min_rr
)
```

Для SELL:

```text
enter_sell = (
    predict_break < p
    and pred_sell_val > min_fav_val
    and pred_sell_val / stop_sell_val >= min_rr
)
```

Параметры:

| Параметр | Смысл |
|---|---|
| `p` | Максимально допустимая вероятность пробоя стоп-уровня |
| `min_fav_val` | Минимальный ожидаемый благоприятный ход |
| `min_rr` | Минимальное отношение ожидаемого хода к расстоянию до стопа |
| `tp_fraction` | Доля от прогнозного хода, на которой ставится TP |
| `cap` | Верхнее ограничение TP |

### TP

Для BUY:

```text
tp_val = min(pred_buy_val * tp_fraction, cap)
tp_buy_price = entry_price + tp_val * atr
```

Для SELL:

```text
tp_val = min(pred_sell_val * tp_fraction, cap)
tp_sell_price = entry_price - tp_val * atr
```

### Оценка результата

Оценка идёт через первое касание по OHLC.

Для BUY:

```text
SL hit = Low <= stop_buy_price
TP hit = High >= tp_buy_price
timeout_buy_pnl_val = (Close[row+H] - entry_price) / atr
```

Для SELL:

```text
SL hit = High >= stop_sell_price
TP hit = Low <= tp_sell_price
timeout_sell_pnl_val = (entry_price - Close[row+H]) / atr
```

Правило одного бара: если в одном H1-баре задеты и TP, и SL, считать SL первым и
ставить `ambiguous_flag = 1`.

Результат сделки:

```text
outcome_pnl_H_val =
    +tp_val                 if TP
    -stop_buy_val           if BUY SL
    -stop_sell_val          if SELL SL
    timeout_buy_pnl_val     if BUY TIMEOUT
    timeout_sell_pnl_val    if SELL TIMEOUT
```

Основной PF при одинаковом лоте считается по `outcome_pnl_H_val` или по
эквивалентному price/pips PnL.

Диагностический PnL в единицах риска:

```text
outcome_pnl_H_r =
    outcome_pnl_H_val / stop_buy_val   # BUY
    outcome_pnl_H_val / stop_sell_val  # SELL
```

### Обязательные отчёты торгового слоя

- PF по валовому итогу `outcome_pnl_H_val`;
- `outcome_pnl_H_r` как диагностика;
- `stop_val_distribution`;
- сделок/год;
- убыточные годы;
- BUY/SELL срезы;
- доля timeout;
- доля `ambiguous_flag`;
- чувствительность к spread: обычный spread, 2x stress, zero-spread диагностика.

## Контракт признаков

Модель не должна получать на вход:

- `signal`;
- `predict`;
- `buy_stop_broken_H_flag`;
- `sell_stop_broken_H_flag`;
- `target_buy_val`;
- `target_sell_val`;
- `outcome_pnl_H_val`;
- `outcome_pnl_H_r`;
- любые `target_*`, `label_*`, `outcome_*`;
- любые будущие OHLC-исходы.

`break` внутри фрактальных признаков можно использовать только в состоянии,
которое реально известно на момент строки. Будущая эволюция `break` для `fractal0`
не может быть входным признаком.

Сборщик признаков должен использовать явный список разрешённых входных признаков.

## Временное разделение и заморозка

- Разделение выборок строго временное.
- Если окно целевой переменной `H` пересекает границу разделения выборок, нужен
  purge/embargo или явное доказательство отсутствия пересечения.
- Все пороги выбираются только на train/validation.
- Test открывается один раз для frozen candidate.
- Если test использован для выбора, нужен новый holdout или forward period.

## Критерии Успеха

### Только пробой уровня

Минимум для продолжения:

- AUC или PR-AUC выше простой модели сравнения;
- lift в группе низкого риска;
- нет полного провала по годам;
- BUY/SELL показаны отдельно.

Этот этап не может получить торговый зачёт.

### Торговый слой

Минимум для исследовательского зачёта:

- PF > 1.0 на validation;
- PF > 1.0 на frozen test;
- достаточное число сделок, заданное в плане реализации;
- убыточные годы отдельно разобраны;
- zero-spread не участвует в PASS/FAIL.

Для кандидата в рабочий контур нужны более строгие условия допуска, включая
издержки, совпадение с MT4 и подтверждение на новом периоде или в tester.

## Открытые Решения Перед Планом

1. Какие `stop_offset_val` брать в первом эксперименте только на пробой уровня:
   `0.2`, `0.5`, возможно `1.0`.
2. Считать ли BUY и SELL одной моделью с direction-aware признаками или двумя
   отдельными моделями.
3. Какой минимум lift считать достаточным для перехода от этапа "только пробой
   уровня" к торговому слою.
4. Какой обычный spread использовать для XAUUSD H1 в торговом слое.
5. Какой минимум сделок нужен для допуска на validation/test.

## Памятка Терминов

```text
H = 6 или 12
```

Горизонт проверки после строки `row`.

```text
atr = ATR[row]
```

Волатильность строки.

```text
fractal_price = fractal0.price
```

Цена свежего фрактального уровня.

```text
fractal_dir = fractal0.dir
```

Тип фрактала: `-1` = впадина, `1` = пик.

```text
direction = -fractal_dir
```

Сторона постановки: BUY для впадины, SELL для пика.

```text
stop_offset_val = 0.2 или 0.5
```

Отступ за уровень.

```text
stop_buy_price = fractal_price - stop_offset_val * atr
stop_sell_price = fractal_price + stop_offset_val * atr
```

Уровни пробоя для этапа "только пробой уровня".

```text
buy_stop_broken_H_flag =
    any(Low[row+1 : row+H] <= stop_buy_price)
sell_stop_broken_H_flag =
    any(High[row+1 : row+H] >= stop_sell_price)
```

Факт пробоя уровня за `H` баров.

```text
predict_break
```

Предсказанная вероятность пробоя уровня.

```text
entry_price = Open[row+1]
```

Цена входа для торгового слоя.

```text
stop_buy_price = min(fractal_price, entry_price) - stop_offset_val * atr
stop_sell_price = max(fractal_price, entry_price) + stop_offset_val * atr
```

Стоп-цены для торгового слоя.

```text
stop_buy_val = (entry_price - stop_buy_price) / atr
stop_sell_val = (stop_sell_price - entry_price) / atr
```

Расстояние от входа до стопа.

```text
target_buy_val =
    max(High[row+1 : row+H] - entry_price) / atr
target_sell_val =
    max(entry_price - Low[row+1 : row+H]) / atr
```

Будущий благоприятный ход. Это целевая переменная, не входной признак.

```text
pred_buy_val
pred_sell_val
```

Предсказанный благоприятный ход.

```text
tp_val = min(pred_buy_val * tp_fraction, cap)
tp_val = min(pred_sell_val * tp_fraction, cap)
```

Размер TP.

```text
tp_buy_price = entry_price + tp_val * atr
tp_sell_price = entry_price - tp_val * atr
```

Цена TP.

```text
timeout_buy_pnl_val = (Close[row+H] - entry_price) / atr
timeout_sell_pnl_val = (entry_price - Close[row+H]) / atr
```

PnL при выходе по времени.

```text
outcome_pnl_H_val
```

Фактический результат сделки в ATR при одинаковом лоте.

```text
outcome_pnl_H_r
```

Фактический результат сделки в единицах риска.

```text
stop_val_distribution
```

Распределение `stop_buy_val` / `stop_sell_val` по выбранным сделкам.

```text
outcome_exit_H in {TP, SL, TIMEOUT}
```

Причина закрытия сделки.

```text
ambiguous_flag = 1
```

Флаг бара, где по OHLC нельзя узнать порядок касаний TP/SL.
