# Аудит спецификации Fractal Stop + Fav Target

> Дата: 2026-06-09
> Объект: `docs/superpowers/specs/2026-06-08-fractal-stop-fav-target-design.md`
> Статус: verdict saved; реализация не начиналась

## Вердикт

Идея спецификации разумна как исследовательский дизайн, но до плана реализации
нужно закрыть блокирующие неоднозначности. В текущем виде спецификацию нельзя
пускать как production-кандидат: часть торгового контракта не зафиксирована до
обучения, а значит будущие PF/test-результаты будет сложно интерпретировать.

## Основные проблемы

### 1. `Open[row+1]` не доказан как исполнимый вход

Спецификация задаёт базовый вход `Open[row+1]`, но для `fractal0` это не
автоматически исполнимо. Строка появляется после закрытия подтверждающего бара,
затем идут запись в CSV, watcher, preprocessing, inference и отправка ордера.

Методический вывод: `Open[row+1]` допустим только при доказанной задержке. Иначе
результат должен получить статус `DIAGNOSTIC_ONLY`, либо нужно использовать
first executable price / MT4 tester execution.

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

### 4. `target_stop_distance_atr` назван как target, но используется в rule

`target_stop_distance_atr` не является меткой, которую модель должна предсказывать.
Это расчетное поле правила после фиксации entry/stop. Имя с `target_` повышает
риск случайного попадания в список обучающих целей или признаков.

Лучше переименовать в `rule_stop_distance_atr` или `entry_stop_distance_atr` и
явно запретить как input модели.

### 5. Не описан invalid stop distance

Нужно задать поведение, если стоп оказывается с неправильной стороны входа:

- BUY: `entry_price <= stop_price`;
- SELL: `entry_price >= stop_price`.

Без этого возможны нулевая или отрицательная дистанция риска и некорректное
отношение `pred_fav / stop_distance`.

### 6. Не зафиксирован same-bar TP+SL policy

OHLC H1 не даёт порядка касаний внутри бара. Если TP и SL задеты в одном баре,
нужно заранее зафиксировать консервативное правило, например:

- считать SL;
- ставить `ambiguous_flag = 1`;
- отдельно отчитать `ambiguous_rate`.

### 7. PF по ATR-PnL слаб при переменной stop distance

Если стоп-дистанция меняется по строкам, PF в ATR-единицах смешивает сделки с
разным риском. Нужно явно выбрать convention:

- fixed lot: основной `outcome_rule_pnl_6_atr`;
- risk-normalized sizing: основной `outcome_rule_pnl_6_r`.

Для второго варианта:

```text
TP = +tp_atr / rule_stop_distance_atr
SL = -1
TIMEOUT = timeout_pnl_atr / rule_stop_distance_atr
```

### 8. BUY/SELL-симметрия описана неполно

Формулы стопа и TP есть, но нет полной зеркальной формулы для `fav`, stop breach,
timeout PnL и bid/ask-цен.

Нужно явно добавить:

```text
BUY:
target_fav_6_atr = max(high - entry_price) / atr
target_stop_breached_6 = any(low <= stop_price)
timeout_pnl_atr = (close_timeout - entry_price) / atr

SELL:
target_fav_6_atr = max(entry_price - low) / atr
target_stop_breached_6 = any(high >= stop_price)
timeout_pnl_atr = (entry_price - close_timeout) / atr
```

Если применяется спред, BUY/SELL должны использовать согласованную Bid/Ask
модель входа, TP, SL и timeout.

## Точечные правки к спецификации

1. Добавить раздел `Decision Time / Execution Contract`:
   `decision_time = after row materialization`; `Open[row+1]` только при latency
   proof, иначе `DIAGNOSTIC_ONLY`.
2. Закрыть вопрос про `signal`: production-кандидат использует все строки по
   `fractal0.dir`; `signal` только diagnostic.
3. Включить canonical spread и 2x stress в первый эксперимент; zero-spread не
   участвует в PASS/FAIL.
4. Переименовать `target_stop_distance_atr` в `rule_stop_distance_atr` или
   `entry_stop_distance_atr`.
5. Добавить `outcome_rule_pnl_6_r` и заранее выбрать основную PnL-единицу.
6. Описать invalid stop distance, same-bar TP+SL, timeout и spread-adjusted
   BUY/SELL formulas.
7. Ужесточить gates: минимум сделок, сделок/год, negative years = 0 для PASS
   или явный `research_only`.
8. Добавить purge/embargo минимум на горизонт `H`, если label-окно может
   пересекать split boundary.

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

