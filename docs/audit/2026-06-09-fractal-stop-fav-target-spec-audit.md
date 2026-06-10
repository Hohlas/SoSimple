# Аудит спецификации Fractal Stop + Fav Target

> Дата: 2026-06-09
> Объект: `docs/superpowers/specs/2026-06-08-fractal-stop-fav-target-design.md`
> Статус: verdict updated after user review; реализация не начиналась

## Вердикт

Идея спецификации разумна как исследовательский дизайн. После уточнения постановки
первым шагом стоит проверять не полную торговую сделку, а более простой вопрос:
будет ли пробит уровень `fractal0` против предполагаемой сделки за горизонт `H`.

Полная торговая постановка с входом, TP, timeout и PF остаётся вторым шагом. Для
неё до плана реализации нужно заранее зафиксировать execution contract, спред,
формулы PnL и BUY/SELL-симметрию.

## Основные проблемы

### 1. `Open[row+1]` — разумный ранний вход, но это optimistic convention

Спецификация задаёт базовый вход `Open[row+1]`, но для `fractal0` это не
автоматически исполнимо. Строка появляется после закрытия подтверждающего бара,
затем идут запись в CSV, watcher, preprocessing, inference и отправка ордера.

Уточнение: по `Close[row]` входить уже нельзя. `Open[row+1]` — логичный earliest
executable proxy для исследования, но в отчёте нужно явно писать, что реальный
online-вход может быть чуть позже. Production-вывод допустим только после проверки
задержек или MT4 tester execution.

### 2. `signal` нельзя оставлять открытым источником кандидатов

`signal` в raw `Nero.csv` всегда равен 0 и заполняется оффлайн по будущему.
Поэтому `signal != 0` как candidate-source является future-derived gate.

Для production-варианта нужно брать все строки с валидным `fractal0.dir`, а
`signal` разрешить только для диагностического сравнения.

### 3. Спред нельзя откладывать на второй этап

Если TP/SL, PnL и выбор правила зависят от цены исполнения, canonical spread
является частью target/execution contract, а не поздней backtest-добавкой.
Zero-spread может быть только диагностикой.

Минимум для первого эксперимента: canonical spread + 2x stress; zero-spread
только как sanity-check геометрии.

### 4. Расстояние до стопа названо как target, но используется в rule

Расстояние до стопа не является меткой, которую модель должна предсказывать.
Это расчетное поле правила после фиксации entry/stop.

В выбранной терминологии:

- `stop_buy_val` — расстояние от BUY-входа до BUY-стопа;
- `stop_sell_val` — расстояние от SELL-входа до SELL-стопа.

Эти поля нужно явно запретить как input модели. Они используются только в торговом
правиле и отчётах.

### 5. Stop placement можно сделать всегда на безопасной стороне входа

Первичная претензия про `INVALID_ENTRY` снимается, если stop convention явно
зафиксирован так:

```text
BUY:
stop_buy_price = min(fractal_price, entry_price) - stop_offset_val * atr

SELL:
stop_sell_price = max(fractal_price, entry_price) + stop_offset_val * atr
```

Тогда стоп всегда находится за входом: ниже входа для BUY и выше входа для SELL.
Остаётся только крайний случай нулевой дистанции, если `stop_offset_val = 0` и
`entry_price == fractal_price`. Для него достаточно правила
`stop_buy_val > 0` / `stop_sell_val > 0`, либо считать `stop_offset_val = 0`
только диагностическим крайним случаем.

### 6. Same-bar policy можно упростить на первом этапе

OHLC H1 не даёт порядка касаний внутри бара. Если TP и SL задеты в одном баре,
на первом этапе допустимо консервативное правило:

- считать SL;
- ставить `ambiguous_flag = 1`;
- отдельно отчитать `ambiguous_rate`.

Если первый этап проверяет только пробой уровня без TP, проблема порядка касаний
вообще не нужна.

### 7. PF по ATR-PnL допустим при одинаковом лоте

Если размер лота одинаковый для всех сделок, основной PF можно считать по
`outcome_pnl_H_val` или по пунктам/цене. Разный стоп при одинаковом лоте —
это нормальная часть правила.

Что всё равно нужно отчитать:

- `stop_val_distribution` — распределение расстояния до стопа, чтобы
  видеть, насколько сильно меняется риск между сделками;
- `outcome_pnl_H_r` — диагностический PnL в единицах риска, чтобы понимать
  результат при risk-normalized sizing.

```text
TP = +tp_val / stop_buy_val      # BUY
TP = +tp_val / stop_sell_val     # SELL
SL = -1
TIMEOUT = timeout_buy_pnl_val / stop_buy_val
TIMEOUT = timeout_sell_pnl_val / stop_sell_val
```

### 8. BUY/SELL-симметрия описана неполно

Формулы стопа и TP есть, но нет полной зеркальной формулы для `fav`, stop breach,
timeout PnL и bid/ask-цен.

Нужно явно добавить:

```text
BUY:
target_buy_val = max(high - entry_price) / atr
buy_stop_broken_H_flag = any(low <= stop_buy_price)
timeout_buy_pnl_val = (close_timeout - entry_price) / atr

SELL:
target_sell_val = max(entry_price - low) / atr
sell_stop_broken_H_flag = any(high >= stop_sell_price)
timeout_sell_pnl_val = (entry_price - close_timeout) / atr
```

Если применяется спред, BUY/SELL должны использовать согласованную Bid/Ask
модель входа, TP, SL и timeout.

## Точечные правки к спецификации

1. Добавить раздел `Decision Time / Execution Contract`:
   `decision_time = after row materialization`; `Open[row+1]` — earliest
   executable proxy, production требует latency proof или MT4 tester execution.
2. Закрыть вопрос про `signal`: production-кандидат использует все строки по
   `fractal0.dir`; `signal` только diagnostic.
3. Включить canonical spread и 2x stress в первый эксперимент; zero-spread не
   участвует в PASS/FAIL.
4. Переименовать расчетные расстояния до стопа в `stop_buy_val` и
   `stop_sell_val`.
5. Для постановки стопа использовать
   `min(fractal_price, entry_price) - stop_offset_val * atr` для BUY и
   `max(fractal_price, entry_price) + stop_offset_val * atr` для SELL.
6. Добавить `outcome_pnl_H_r` как диагностическую метрику; основной PF при
   fixed lot можно считать по ATR/price PnL.
7. Описать same-bar SL policy, timeout и spread-adjusted BUY/SELL formulas.
8. Добавить отдельный этап "только пробой уровня": модель предсказывает только
   пробой уровня `fractal0` за `H` баров, без входа, TP, timeout и PF.
9. Ужесточить gates: минимум сделок, сделок/год, negative years = 0 для PASS
   или явный `research_only`.
10. Добавить purge/embargo минимум на горизонт `H`, если label-окно может
    пересекать split boundary.

## Рекомендуемый первый шаг: только пробой уровня

Самый простой и полезный первый эксперимент — не торговый PF, а проверка вопроса:
может ли модель предсказать, будет ли пробит уровень `fractal0` против сделки за
`H` баров.

В этом режиме нет `entry_price`, TP, timeout и PnL. Есть только уровень, сторона
и факт пробоя:

```text
direction = -fractal0.dir
atr = ATR[row]
stop_offset_val = 0.2 или 0.5

BUY setup:
stop_buy_price = fractal_price - stop_offset_val * atr
buy_stop_broken_H_flag = any(Low[row+1 : row+H] <= stop_buy_price)

SELL setup:
stop_sell_price = fractal_price + stop_offset_val * atr
sell_stop_broken_H_flag = any(High[row+1 : row+H] >= stop_sell_price)
```

Модель учится именно событию "уровень пробит", а не порядку касания SL/TP.
Горизонты для первой проверки: `H = 6` и `H = 12`.

Метрики первого шага:

- AUC / PR-AUC для `buy_stop_broken_H_flag` и `sell_stop_broken_H_flag`;
- доля пробоев по BUY/SELL и годам;
- lift по группам вероятности: например, насколько часто уровень пробивается в
  нижних 10% `predict_break` против среднего.

Торговые выводы из этого шага делать нельзя. Он отвечает только на вопрос:
"есть ли в признаках информация о будущем пробое уровня".

## Источники

- `docs/superpowers/specs/2026-06-08-fractal-stop-fav-target-design.md`
- `docs/methodology/03-feature-contract-leakage.md`
- `docs/methodology/04-labeling.md`
- `docs/methodology/12-backtest-costs.md`
- `docs/dataset_description.md`
- `docs/reports/2026-05-25-methodology-cycle-stages-00-04.md`
- `docs/reports/2026-05-29-limit-order-entry.md`
- `docs/reports/2026-06-03-direction-only-signal.md`
- `docs/reports/2026-06-04-fractal-ablation.md`

## Памятка терминов

Ниже имена черновые. Их можно переименовать перед планом реализации.

### Общие величины

```text
H = 6 или 12
```

Горизонт проверки в барах после строки `row`.

```text
atr = ATR[row]
```

Волатильность строки. Используется для перевода отступов и движений в ATR-единицы.

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

Предполагаемая сторона сделки: для впадины BUY, для пика SELL.

```text
stop_offset_val = 0.2 или 0.5
```

Отступ за уровень в ATR-единицах.

### Этап "только пробой уровня"

```text
stop_buy_price = fractal_price - stop_offset_val * atr
```

Уровень пробоя для BUY-постановки: цена ушла ниже впадины с отступом.

```text
stop_sell_price = fractal_price + stop_offset_val * atr
```

Уровень пробоя для SELL-постановки: цена ушла выше пика с отступом.

```text
buy_stop_broken_H_flag =
    any(Low[row+1 : row+H] <= stop_buy_price)
```

Цель для BUY: будет ли пробита впадина за `H` баров.

```text
sell_stop_broken_H_flag =
    any(High[row+1 : row+H] >= stop_sell_price)
```

Цель для SELL: будет ли пробит пик за `H` баров.

```text
predict_break =
    P(buy_stop_broken_H_flag = 1 | current_features)   # BUY
    P(sell_stop_broken_H_flag = 1 | current_features)  # SELL
```

Предсказанная моделью вероятность пробоя уровня.

### Полная торговая постановка

```text
entry_price = Open[row+1]
```

Цена входа в исследовательской проверке на истории. Это самая ранняя исполнимая
приближенная цена; в реальной торговле цена может быть чуть позже.

```text
stop_buy_price = min(fractal_price, entry_price) - stop_offset_val * atr
```

Стоп для BUY: всегда ниже цены входа и ниже/на уровне фрактала.

```text
stop_sell_price = max(fractal_price, entry_price) + stop_offset_val * atr
```

Стоп для SELL: всегда выше цены входа и выше/на уровне фрактала.

```text
stop_buy_val = (entry_price - stop_buy_price) / atr
```

Расстояние от входа до стопа для BUY в ATR.

```text
stop_sell_val = (stop_sell_price - entry_price) / atr
```

Расстояние от входа до стопа для SELL в ATR.

```text
target_buy_val =
    max(High[row+1 : row+H] - entry_price) / atr
```

Максимальный благоприятный ход BUY за `H` баров.

```text
target_sell_val =
    max(entry_price - Low[row+1 : row+H]) / atr
```

Максимальный благоприятный ход SELL за `H` баров.

```text
pred_buy_val
pred_sell_val
```

Предсказанный моделью благоприятный ход за `H` баров.

```text
tp_val = min(pred_buy_val * tp_fraction, cap)   # BUY
tp_val = min(pred_sell_val * tp_fraction, cap)  # SELL
```

Размер TP в ATR. TP ставится ближе прогнозного максимального хода.

```text
tp_buy_price = entry_price + tp_val * atr
```

Цена TP для BUY.

```text
tp_sell_price = entry_price - tp_val * atr
```

Цена TP для SELL.

```text
timeout_buy_pnl_val = (Close[row+H] - entry_price) / atr
```

PnL BUY при выходе по времени.

```text
timeout_sell_pnl_val = (entry_price - Close[row+H]) / atr
```

PnL SELL при выходе по времени.

```text
outcome_pnl_H_val =
    +tp_val                 if TP
    -stop_buy_val           if BUY SL
    -stop_sell_val          if SELL SL
    timeout_buy_pnl_val     if BUY TIMEOUT
    timeout_sell_pnl_val    if SELL TIMEOUT
```

Фактический результат сделки в ATR при одинаковом лоте.

```text
outcome_pnl_H_r =
    outcome_pnl_H_val / stop_buy_val   # BUY
    outcome_pnl_H_val / stop_sell_val  # SELL
```

Фактический результат сделки в единицах риска. Это диагностическая метрика, если
основной режим использует одинаковый лот.

```text
stop_val_distribution =
    min / p10 / p50 / p90 / max(stop_buy_val или stop_sell_val выбранной сделки)
```

Распределение расстояния до стопа. Нужно, чтобы видеть, насколько разный риск
получается при одинаковом лоте.

```text
outcome_exit_H in {TP, SL, TIMEOUT}
```

Причина закрытия сделки.

```text
ambiguous_flag = 1
```

Флаг бара, где из OHLC нельзя понять порядок касаний. В консервативном первом
варианте любое касание SL считается SL.
