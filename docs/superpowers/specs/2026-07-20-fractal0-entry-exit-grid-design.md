# Fractal0 Entry + Exit Grid Design

## Цель

Проверить, можно ли превратить диагностическую механику входа около
`fractal0_price` в полную торговую постановку:

```text
отложенный вход -> fill/no-fill -> выход -> издержки -> PnL/PF
```

Главное уточнение: этот этап не включает проверку на новом инструменте или
таймфрейме. Сначала нужно найти локально жизнеспособную систему на исходном
инструменте. Новый инструмент остаётся необходимым последующим шагом, но только
в самом конце исследовательской цепочки, когда будет заморожена финальная
система после всех разрешённых поисковых уточнений.

## Почему нужен новый spec

Отчёт `2026-07-10-fractal0-price-entry-mechanics.md` показал не PF, а
диагностический потолок входа:

- `val_stop favorable_to_adverse_ratio = 1.2421118400499844`;
- `stress_favorable_to_adverse_ratio = 1.1895354754041108`;
- simple rule ratio `= 1.061228066744197`;
- side contract `PASS`;
- `active_years = 2`, поэтому gate не пройден.

Эти числа говорят, что в районе `fractal0_price` есть полезная механика
возврата цены. Они не доказывают прибыльность, потому что у этапа не было
правил выхода и PnL-симуляции.

Ранее Stage 4.5 показал, что exit-механика может резко менять качество:

- `fixed_r_0_7`: PF `1.038`, `BS_p05 = 0.886`;
- `trail_atr_0_2`: PF `1.831`, `BS_p05 = 1.462`;
- `trail_atr_0_2` при spread `0.40`: PF `1.501`;
- старый diagnostic Stage 4.3 trail PF `1.655` не использовался для выбора.

Также есть готовая research segmentation mask:

- `simple_combined / extra_trees_small / H3 / top_fraction=0.05`;
- `val_eval movement_lift = 2.4806`;
- статус: `FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN`;
- это не direction, не PnL/PF и не trading signal.

## Основная гипотеза

Отложенный вход около `fractal0_price`, дополненный чувствительным exit-rule и
опциональной frozen movement mask, может дать полноценную торговую систему с
PF выше простого fixed-exit baseline.

## Исследовательский уровень

Первый этап остаётся поисковым:

```text
lifecycle_status = research_scan
allowed_max_verdict = research_only
locked_test = not_opened
```

`research_hint` в этом spec означает результат ниже `research_hypothesis`:
метрики интересные, но не хватает сделок, коррекции перебора или исполнимого
контракта для продолжения как основной ветки.

PnL/PF можно считать в этом этапе, но только как исследовательские метрики.
Запрещённые выводы:

- `production`;
- `live-ready`;
- `tradable`;
- `candidate`;
- разрешение открыть `locked_test`.

Проверка на новом инструменте не входит в этот spec. Локальные profit-gates
нужны только для решения, стоит ли продолжать эту ветку и какую конфигурацию
считать сильной исследовательской гипотезой.

Этот spec намеренно соединяет entry, exit и ML-exit в одном поисковом этапе,
но отчёт обязан разделить вклад трёх источников результата:

- исполнимая цена входа и fill/no-fill;
- фильтрация сделок через movement mask;
- правило выхода.

Если в сетке больше `10` конфигураций, сильный результат без коррекции
множественного перебора остаётся не выше `research_hint`. Для повышения до
`research_hypothesis` нужен либо отдельный `val_eval`, не участвовавший в
выборе winner, либо permutation-test, который на каждой перестановке повторяет
весь процесс выбора winner.

## Entry Contract

Используются только отложенные ордера. Это снижает зависимость от задержки
расчётов и от расхождения между расчётным временем сигнала и следующим `Open`.

Базовое правило входа:

```text
entry_type = limit
entry_anchor = fractal0_price
entry_rule = zone_edge
zone_atr = 0.5
fill_lag_bars = 6
horizon = H3
canonical_spread = 0.2
side = -fractal0.dir
```

Правило из oracle-preflight остаётся базовой постановкой, но первая поисковая
партия может шире проверять отложенные варианты входа. Главное ограничение:
все entry families и параметры должны быть перечислены до запуска партии и
войти в `current_search_budget`.

Допустимые entry-варианты первой партии:

| ID | Entry | Зачем нужен |
|---|---|---|
| `E0_selected_zone_edge` | `zone_edge / 0.5 ATR / lag 6 / H3 / spread 0.2` | Основная проверка найденной механики |
| `E1_simple_limit_at_fractal0` | `limit_at_fractal0 / 0.0 ATR / lag 6 / H3 / spread 0.2` | Простой baseline из oracle-preflight |
| `E2_open_pullback_0_5atr` | отложенный вход на `0.5 ATR` от `calculation_open` | Проверка pullback от исполнимой цены расчёта |
| `E3_open_pullback_1_0atr` | отложенный вход на `1.0 ATR` от `calculation_open` | Более глубокий pullback от исполнимой цены расчёта |

`calculation_open` — это `Open` бара, который идёт сразу после `Close`, на
котором `fractal0` считается сформированным и доступны все расчёты. Для BUY
отложенный pullback-ордер ставится ниже `calculation_open`, для SELL — выше
`calculation_open`.

`E1` нужен для измерения добавки от зоны входа. `E2`/`E3` нужны для проверки,
не лучше ли исполнимый pullback относительно цены расчёта, а не относительно
самого `fractal0_price`.

## PnL И Контракт Исполнения

План реализации обязан до запуска сетки зафиксировать точный торговый контракт.
Без этого PF не считается надёжной метрикой даже в исследовательском режиме.

Базовая конвенция для первой реализации:

```text
ohlc_price_type = bid
spread = full bid-ask spread
canonical_spread = 0.20
stress_spread = 0.40
pending_order_price_type:
  BUY limit = Ask price
  SELL limit = Bid price
close_price_policy = next executable Open after close decision
same_bar_tp_sl_policy = SL first
timeout_policy = close at next executable Open after timeout decision
```

Если runner использует более простое `bid-touch` заполнение ордеров из старого
oracle-preflight, это нужно явно записать как `DIAGNOSTIC_ONLY_FILL_MODEL`.
Основной PF-gate должен использовать executable-side fill:

- BUY limit заполнен, если `low_bid + spread <= limit_price`;
- SELL limit заполнен, если `high_bid >= limit_price`;
- BUY закрывается по Bid;
- SELL закрывается по Ask, то есть OHLC для exit сдвигается на `+spread`.

`R` — это риск сделки после фактического fill:

```text
R = abs(entry_effective_price - protective_stop_price)
```

В первой партии protective stop фиксируется, а не подбирается:

```text
protective_stop_atr = 0.5
BUY stop  = min(fractal0_price, entry_bid_equivalent) - 0.5 * ATR
SELL stop = max(fractal0_price, entry_bid_equivalent) + 0.5 * ATR
```

Для `E0`/`E1`/`E2`/`E3` одинаково считаются:

- `limit_price`;
- `fill_trigger_price`;
- `entry_effective_price`;
- `entry_bid_equivalent`;
- `protective_stop_price`;
- `R`;
- no-fill rows.

No-fill не становится нулевой сделкой: он учитывается в `no_fill_rate`, но не
входит в PF/PnL сделок.

## Exit Grid

Главный фокус этапа — не очередная проверка trailing/time exits, а поиск
выходов по ML-сигналам после входа. Классические выходы остаются в сетке как
baseline и контрольные семейства.

| ID | Exit family | Параметры | Роль |
|---|---|---|---|
| `X0_fixed_r_0_7` | fixed TP/SL | TP `0.7R`, SL по entry contract | baseline |
| `X1_ml_opposite_strong` | ML opposite signal | закрыть только при сильном противоположном сигнале | главный ML-exit вариант |
| `X2_ml_opposite_any` | ML opposite signal | закрыть при любом противоположном сигнале | чувствительный ML-exit вариант |
| `X3_ml_hold_close` | ML hold/close | на каждом баре после fill: держать или закрыть | прямой exit-target |
| `X4_ml_movement_exhaustion` | ML movement exhaustion | закрыть, если ожидаемое дальнейшее движение стало слабым | главный вариант “исчез потенциал” |
| `X5_fixed_sl_ml_profit_exit` | fixed protective SL + ML exit | убыток режет фиксированный SL, прибыль закрывает ML-логика | практичный защитный контур |
| `X6_trail_atr_grid` | trailing stop | trail distance `0.2 / 2 / 3 / 5 ATR`; activation `0 / 1 / 2 / 3 ATR` прибыли | сильный historical control против ML-выходов |
| `X7_time_exit_grid` | time-based exit | `1 / 2 / 6 / 12` баров после fill | контроль длительности удержания |
| `X8_profit_giveback` | profit giveback | откат `30% / 50% / 70%` от максимальной прибыли; activation `1 / 2 / 3 ATR` прибыли | контроль отдачи прибыли |

Пояснения:

- `0.2 ATR` сохраняется как обязательный trailing-control, потому что Stage 4.5
  дал для `trail_atr_0_2` PF `1.831` и stress PF `1.501`. В новой постановке
  это сильный ориентир, но не доказательство качества `fractal0_price` системы.
- `profit_giveback` отличается от trailing тем, что отдаёт долю уже накопленной
  прибыли, а не держит фиксированную ATR-дистанцию от лучшей цены.
- Выход “при появлении любого нового фрактала” исключён из первой партии:
  фракталы появляются часто, поэтому такое правило с высокой вероятностью будет
  закрывать позиции шумом до развития движения.
- Breakeven и partial exit не являются главным фокусом. Их можно добавить
  только если отдельная расширенная партия явно включает их в search budget и
  объясняет, зачем повторять слабые прошлые результаты.

ML-exit должен использовать только признаки, доступные после входа на момент
очередного решения о закрытии. Любой target для `hold/close`, opposite signal
или movement exhaustion является future-derived при обучении и не может попасть
во входные признаки модели.

Для честного сравнения каждый ML-exit обязан иметь matched deterministic
baseline: тот же entry, та же mask, тот же protective SL и та же fill/no-fill
выборка, но простой выход без ML (`fixed_r_0_7`, trailing/time/giveback из
раскрытой сетки). Иначе нельзя утверждать, что PF улучшил именно ML-exit.

## Контракт ML-Exit Target

ML-exit обучается только после того, как entry-сделка уже заполнена. No-fill
события не попадают в обучающую выборку exit-модели. После закрытия позиции
для неё больше не создаются exit-решения.

Для каждого бара удержания фиксируются:

```text
position_id
fill_time
fill_index
decision_bar_index
decision_time = Close[decision_bar_index]
first_exit_execution_time = Open[decision_bar_index + 1]
bars_since_fill
unrealized_pnl_r_before_decision
max_favorable_r_before_decision
max_adverse_r_before_decision
target_exit_*
```

Запреты:

- признаки текущего незакрытого бара не используются;
- future-derived поля `target_exit_*`, будущий `pnl_r`, будущий максимум и
  будущий минимум не попадают во входные признаки;
- если close исполняется по `Close[decision_bar_index]`, результат получает
  статус не выше `DIAGNOSTIC_ONLY`, пока нет доказательства live-исполнения по
  этой цене.

Допустимые семьи target-ов:

- `target_exit_opposite_any`: противоположный ML-сигнал любой силы внутри
  следующего окна;
- `target_exit_opposite_strong`: противоположный ML-сигнал выше заранее
  заданного порога;
- `target_exit_hold_close`: бинарное решение, выгоднее ли держать позицию ещё
  один шаг против закрытия на следующем исполнимом `Open`;
- `target_exit_movement_exhaustion`: ожидаемый остаточный ход ниже раскрытого
  порога при ненулевом риске дальнейшего adverse move.

## Movement Mask Grid

Movement mask используется как segmentation layer, а не как самостоятельный
сигнал.

| ID | Mask | Роль |
|---|---|---|
| `M0_no_mask` | все заполненные entry-события | baseline полной механики |
| `M1_frozen_movement_top5` | frozen mask `simple_combined / extra_trees_small / H3 / top_fraction=0.05` | проверка SNR внутри режима сильного движения |

Для `M1` обязательно раскрыть:

- `selected_n`;
- trades/year;
- BUY/SELL coverage;
- PF по годам;
- PF без лучшего года;
- что `top_fraction=0.05` не является готовым live cutoff.

Если `M1` улучшает PF, но создаёт слишком мало сделок, результат остаётся
только `research_hint`.

Если winner зависит от `M1_frozen_movement_top5`, но для неё нет абсолютного
score cutoff, который можно применить в live без знания будущего распределения,
такой winner не может быть основной финальной системой. В этом этапе `M1`
остаётся допустимой диагностической сегментацией для повышения отношения
сигнал/шум, а live-safe cutoff переносится в следующий план.

## Полная первая сетка

Первая партия является широкой поисковой партией:

```text
4 entry rules x exit-family parameter grid x 2 mask states
```

Точное число конфигураций считается в implementation plan после раскрытия всех
порогов ML-сигналов и параметров exit families. Это число становится
`current_search_budget`. Любое расширение сетки после просмотра результатов
требует новой записи в плане и увеличивает `cumulative_search_budget`.

Широкий перебор разрешён. Запрещено только скрывать его, менять сетку задним
числом или трактовать лучший результат как кандидат без следующего проверочного
цикла.

Отчёт по первой сетке обязан показать:

- `current_search_budget`;
- `cumulative_search_budget`;
- метод коррекции множественного перебора;
- если коррекция не выполнена, явное понижение результата до `research_hint`;
- все rejected alternatives, а не только top-N.

## Runtime Contract

План реализации обязан переиспользовать runtime-паттерн тяжёлых benchmark-ов
проекта:

- `--threads 24` по умолчанию; фактическое число потоков писать в JSON;
- для XGBoost/ExtraTrees и аналогичных моделей явно задавать `n_jobs`,
  `nthread` или соответствующий параметр библиотеки;
- печатать heartbeat на start, preflight, начало/конец каждого run, progress
  `done_runs/total_runs`, `elapsed`, по возможности `ETA`;
- сохранять JSON после каждого run атомарной записью;
- поддерживать остановку и продолжение: `--resume` по умолчанию,
  `--no-resume` для чистого перезапуска;
- использовать `run_config_hash`, чтобы нельзя было продолжить старый JSON с
  другой сеткой;
- failed runs не должны останавливать всю матрицу, но обязаны попадать в JSON;
- тестами покрыть resume, progress JSON, thread count и отказ продолжать
  несовместимый `run_config_hash`.

## Split Protocol

Используется текущий entry-based split protocol:

- `train_core`: только для обучения моделей и инженерной отладки pipeline;
- `val_select`: выбор одной торговой конфигурации из заранее раскрытой сетки;
- `val_eval`: проверка выбранной конфигурации без изменения правила;
- `diagnostic_holdout`: disclosure-only;
- `low_n_disclosure`: disclosure-only;
- `locked_test`: не открывать.

Если текущий артефакт не содержит явных `val_select`/`val_eval` ролей для этой
механики, runner обязан создать их до выбора winner. Нельзя выбирать winner и
оценивать его на одном и том же validation-срезе без понижения статуса.

Выбор entry baseline тоже является торговым выбором и должен входить в
`val_select` и `current_search_budget`. `train_core` не выбирает entry, exit,
mask, threshold или торговый baseline.

## Profit Gates

Цель исследования - двигаться к PF `> 2.0`, но не замораживать и не развивать
слабые конфигурации.

### Gate A: локальный минимум для продолжения

Конфигурация может стать `research_hypothesis`, если на `val_eval` выполнено:

- PF `>= 1.50`;
- `BS_p05 >= 1.10`;
- spread stress PF при `spread=0.40` `>= 1.20`;
- минимум `300` сделок всего;
- минимум `50` сделок в каждом активном году, если годовой срез используется
  как gate;
- не больше одного отрицательного года;
- PF без лучшего года `>= 1.10`;
- обе стороны BUY/SELL присутствуют, либо side-specific результат явно
  оформлен как отдельная гипотеза.

Если сделок меньше `300`, но остальные проверки выглядят сильными, разрешён
только статус `research_hint` с `low_n_warning`; он не заменяет Gate A и не
даёт права считать конфигурацию полноценной `research_hypothesis`.

Если Gate A не пройден, ветка останавливается или возвращается к новой
постановке входа/выхода. Проверка на новом инструменте на этом этапе всё равно
не рассматривается.

### Gate B: цель сильной локальной системы

Конфигурация считается достаточно сильной, чтобы стать основной локальной
исследовательской системой для следующего уточняющего плана, если на `val_eval`
выполнено:

- PF `>= 2.00`;
- `BS_p05 >= 1.30`;
- spread stress PF при `spread=0.40` `>= 1.50`;
- средний `pnl_r` на сделку после издержек `> 0`;
- `max_drawdown_r` и худшая серия сделок раскрыты и не противоречат смыслу
  системы;
- PF без лучшего года `>= 1.30`;
- `effective_profit_years >= max(1.5, 0.6 * n_years)`;
- минимум `3` активных года или эквивалентные заранее заданные временные окна;
- заранее заданный walk-forward disclosure не показывает системного слома
  поздних окон;
- нет явного провала одной стороны, если система торгует обе стороны.

Если PF между `1.50` и `2.00`, ветку можно продолжать только одной
дополнительной заранее описанной поисковой партией. Если и после неё Gate B не
пройден, ветка не должна бесконечно расширять перебор.

## Selection Policy

Winner выбирается на `val_select` только среди конфигураций, прошедших
минимальные sample-size checks.

Порядок выбора:

1. Отбросить конфигурации с малым числом сделок.
2. Отбросить конфигурации с явным провалом spread stress.
3. Отбросить конфигурации с отрицательными годовыми срезами выше разрешённого
   лимита.
4. Отбросить конфигурации с отрицательным средним `pnl_r` после издержек,
   неприемлемым drawdown или прибылью, сосредоточенной в одном году.
5. Среди оставшихся выбрать максимум `BS_p05`.
6. Если `BS_p05` близок, выбрать правило с более понятной механикой и меньшим
   числом дополнительных ML/exit-порогов.

Точечный PF не является главным tie-breaker, потому что он сильнее завышается
на малом числе сделок.

Для каждой рассматриваемой конфигурации и winner-а обязательно раскрыть:

- PF, gross profit, gross loss;
- `BS_p05`;
- средний и медианный `pnl_r` на сделку;
- `max_drawdown_r`;
- trades/year и PF/year;
- `effective_profit_years`, best-year share, PF without best year;
- BUY/SELL PF и число сделок;
- exit reason distribution.

## Attribution Checks

Чтобы не приписать успех неверному компоненту, отчёт обязан посчитать
entry-only attribution:

| Проверка | Что сравнивает |
|---|---|
| `A0_matched_entry_mask_baseline_exit` | тот же entry и mask, но простой deterministic exit |
| `A1_same_exit_no_mask` | тот же entry и exit, но без movement mask |
| `A2_same_exit_simple_entry` | тот же exit и mask, но `E1_simple_limit_at_fractal0` |
| `A3_same_trades_exit_swap` | одна и та же заполненная выборка сделок, разные exit rules |

Минимальный вывод: улучшение PF разложить на `entry_price_effect`,
`trade_filter_effect` и `exit_effect`. Если это невозможно из-за структуры
данных, отчёт обязан явно записать `attribution_status = incomplete`.

## Simulator Test Requirements

До использования PF/PnL нового runner-а для любых gate-решений нужны
синтетические тесты симулятора:

- TP-only;
- SL-only;
- timeout;
- TP+SL в одном баре с политикой `SL first`;
- BUY spread correction;
- SELL spread correction;
- no-fill не попадает в PF;
- ML-close исполняется не раньше разрешённого `first_exit_execution_time`.

## Последующая Проверка На Новом Инструменте

Проверка на новом инструменте обязательна перед серьёзными выводами о
робастности, но она не входит в этот этап.

Причина: после этой сетки может понадобиться ещё несколько поисковых уточнений:
другой набор exit-правил, ML-модель выхода, другой segmentation layer или
пересмотр side-specific политики. Новый инструмент нельзя тратить на каждую
промежуточную конфигурацию, иначе он сам станет частью подбора.

Перед будущей проверкой на новом инструменте должна быть заморожена уже
финальная система:

- entry rule;
- exit rule;
- movement mask state;
- spread/cost model;
- fill/no-fill policy;
- PnL convention;
- minimum trades gates;
- failure criteria;
- список инструментов;
- запрет менять параметры после просмотра нового инструмента.

Эта будущая проверка оформляется отдельным plan/spec. В текущем отчёте можно
только указать, является ли найденная локальная система достаточно сильной,
чтобы продолжать её доводку до финальной заморозки.

## Артефакты

Ожидаемые артефакты будущего плана:

- `ML/reports/fractal0_entry_exit_grid.json`;
- `ML/reports/fractal0_entry_exit_grid_summary.csv`;
- `ML/reports/fractal0_entry_exit_grid_trades.csv`;
- `ML/reports/fractal0_entry_exit_grid_yearly.csv`;
- `ML/reports/fractal0_entry_exit_grid_spread_stress.csv`;
- `docs/reports/YYYY-MM-DD-fractal0-entry-exit-grid.md`.

JSON обязан содержать:

- `current_search_budget` как фактическое число раскрытых конфигураций;
- `cumulative_search_budget`;
- exact grid;
- multiple-testing correction status;
- ML-exit thresholds и target contracts;
- PnL convention;
- simulator test status;
- attribution status и attribution metrics;
- walk-forward disclosure, если Gate B заявляется;
- movement mask live-cutoff status;
- sample-size warning status;
- selected winner;
- rejected alternatives;
- split roles;
- entry/exit/mask hashes;
- canonical spread;
- stress spread;
- forbidden interpretation block;
- `allowed_max_verdict`.

## Stop Rules

Остановить ветку или не повышать её выше `research_hypothesis`, если:

- ни одна конфигурация не проходит Gate A;
- лучший результат держится только на одном году;
- лучший результат ломается при `spread=0.40`;
- frozen movement mask даёт PF за счёт слишком малого числа сделок;
- winner зависит от `M1_frozen_movement_top5`, но не раскрыт live-safe cutoff,
  а результат пытаются трактовать как финальную систему;
- обе стороны торгуются, но одна сторона явно убыточна;
- результат хуже `E1_simple_limit_at_fractal0` или `X0_fixed_r_0_7` baseline;
- PF/PnL получены без синтетических тестов симулятора;
- используется `DIAGNOSTIC_ONLY_FILL_MODEL`, но результат трактуется как
  основной PF-gate;
- после первой партии возникает желание добавить параметры без новой причины,
  кроме "найти красивый PF".

## Открытые вопросы для implementation plan

1. Где в текущих артефактах надёжнее брать OHLC для симуляции exit после fill:
   через существующие Stage 4.5 helpers или отдельный entry-based simulator.
2. Как точно разделить `val_select` и `val_eval` для `fractal0_price`, чтобы
   не переиспользовать `val_stop` одновременно для выбора и проверки.
3. Нужен ли отдельный absolute score cutoff для frozen movement mask перед
   live-проверками, потому что текущий `top_fraction=0.05` не является
   исполнимым live-rule.
4. Какие условия должны завершать всю серию поисков и запускать отдельный
   final-system freeze перед проверкой на новом инструменте.
