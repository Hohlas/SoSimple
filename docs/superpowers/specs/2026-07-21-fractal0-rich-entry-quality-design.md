# Fractal0 Rich Entry Quality Design

Дата: 2026-07-21

## Цель

Проверить гипотезу, что текущий `ML-entry quality filter` провалился из-за
слишком бедного набора признаков и слишком шумного бинарного target-а.

Новый этап должен построить pre-order модель качества входа для
`E3_open_pullback_1_0atr` поверх выбранной stop/exit механики:

```text
S2_fractal0_buffer_0_5_entry_floor_2 /
E3_open_pullback_1_0atr /
M0_no_mask /
X2_ml_opposite_any_p0_50
```

Результат остаётся поисковым. `locked_test` не открывать.

## Почему нужен новый этап

Исправленный `fractal0_entry_quality_filter` выбрал на `val_select`
`entry_quality_top10`, но правило не перенеслось на `val_eval`:

```text
val_select: PF=5.4967, BS_p05=3.9370, n_trades=196
val_eval:   PF=1.9543, BS_p05=0.9713, n_trades=53
```

Одна из рабочих гипотез: проблема не только в модели. Текущие признаки почти
не описывают состояние рынка:

```text
side_buy
ATR
entry_to_fractal0_atr
stop_distance_atr
r_value_atr
```

Это planned execution geometry, а не полноценное описание цены, фрактальной
структуры и локального режима рынка. При этом причина провала не считается
доказанной: узкий `top10`, сдвиг score между split-ами и сила простых
baseline-фильтров остаются альтернативными объяснениями. Поэтому следующий
этап должен сначала проверить richer feature contract, а уже потом сравнивать
модели.

## Исследовательская гипотеза

Pre-order фильтр качества E3-входа станет устойчивее, если:

1. Использовать признаки, которые описывают фрактальную структуру, локальное
   состояние цены, режим движения и время сигнала.
2. Target будет отражать силу результата сделки, а не только знак
   `pnl_r > 0`.
3. Primary selection не будет выбирать слишком узкие top10-срезы без
   жёсткого sample-size gate.

## Decision Time

Фильтр принимает решение до отправки limit-заявки E3.

Разрешённая информация:

- строка `Nero_*_labeled.csv` на `signal_time`;
- все поля `fractal0..fractal99`, доступные в этой строке;
- `ATR`;
- календарные признаки строки;
- OHLC только по `last_fully_closed_h1_bar`;
- planned limit/stop/R, вычисленные до отправки заявки;
- frozen movement score, если его контракт подтверждает доступность без
  будущего.

Запрещённая информация:

- факт fill/no-fill;
- фактическая fill price;
- fill lag;
- exit price/time;
- `close_reason`;
- `pnl_r`;
- top-level future target columns: `up_*`, `dn_*`, `ret_*`, `fav_*`,
  `adv_*`, `entry_up_*`, `entry_dn_*`, `entry_log_ratio_*`,
  `trail_*`, `*_pnl_*`, `target_*`, `label_*`, `outcome_*`;
- `high/low/close` незакрытого H1-бара и любые intrabar-признаки, которые
  становятся известны только после `signal_time`;
- M5/M1 как признаки модели. M5 остаётся только для порядка исполнения
  внутри H1-свечи.

## Источники признаков

Спецификация намеренно не ограничивается ATR-производными. ATR-нормализация
может использоваться для масштаба, но сырьё признаков должно включать разные
семейства из прошлых исследований.

### 1. Fractal Structure Profile

Использовать поля из `fractal0..fractal99`, описанные в
`docs/dataset_description.md`:

```text
price
direction
front
back
strong
break
reverse
power
count
impulse
fractal_atr
shift
```

Роли:

- `fractal0` — текущий новый уровень;
- `fractal1..fractal99` — историческая структура уровней;
- `shift` — возраст уровня;
- `power/count/break/reverse/impulse` — структурный контекст, который в
  прошлых абляциях был важнее raw price для ряда target-ов.

Primary compact-профили:

```text
structure_f0_only
structure_nearest_k20
structure_nearest_k40
```

`structure_nearest_k80` и `structure_all100` разрешены только как
diagnostic-only в этой спецификации. Причина: широкий flat-вход по 80-100
фракталам резко увеличивает число признаков и риск ложного winner-а на
ограниченном числе сделок.

### 2. Relative Geometry Profile

Фрактальные цены не подавать только как raw price. Нужны относительные
координаты:

```text
price_i - fractal0_price
abs(price_i - fractal0_price)
(price_i - fractal0_price) * direction_i
distance_to_planned_limit
distance_to_planned_stop
level_density_near_limit
level_density_near_stop
nearest_same_direction_level_distance
nearest_opposite_direction_level_distance
```

Нормализация на ATR допустима, но это только масштабирование, а не отдельная
feature family.

### 3. Serialized Historical Up/Dn Inside Fractals

Условно разрешены `Up3/Dn3/Up6/Dn6/Up12/Dn12/Up24/Dn24/Up48/Dn48` внутри
`fractal0..fractal99`, если отдельная проверка producer-а подтверждает, что
это состояние фрактальных объектов уже накоплено в строке к `signal_time`, а
не пересчитано Python-постобработкой по будущим барам.

Запрещены top-level `up_3`, `dn_3`, ... из разметки, потому что это будущие
target-колонки текущей строки.

Обязательное disclosure:

```text
declared_feature_sources: serialized_fractal_subfields
raw_columns_touched: fractal0..fractal99
forbidden_top_level_targets_touched: false
producer_contract_check: PASS
feature_builder_reads_serialized_subfields_only: true
```

### 4. Price Action Profile

Добавить признаки последней полностью закрытой H1-свечи и прошлых H1-свечей
из OHLC, доступных на `signal_time`:

```text
open
high
low
close
body
range
upper_wick
lower_wick
close_position_in_range
ret_1
ret_3
ret_6
ret_12
rolling_high_6
rolling_low_6
rolling_high_12
rolling_low_12
close_to_rolling_high_6
close_to_rolling_low_6
close_to_rolling_high_12
close_to_rolling_low_12
```

Все `ret_*` и rolling-признаки считаются только назад от
`last_fully_closed_h1_bar`. В `feature_contract_audit.csv` для каждого
OHLC-признака обязательны поля:

```text
bar_offset
requires_bar_close
available_at
```

Если используется ATR-нормализация, дополнительно сохранить raw/value source
и scaled value. Отчёт должен отделять "источник признака" от "масштаба".

### 5. Time And Session Profile

Старые исследования показывали, что time-only иногда сильнее ожидаемого.
Поэтому время обязательно как baseline и как часть combined profiles:

```text
session_hour
weekday
hour_sin
hour_cos
weekday_sin
weekday_cos
month
```

### 6. Movement Regime Profile

Использовать только frozen/live-safe score из предыдущего movement-filter
контура, если он доступен без будущего и не был подобран после просмотра
текущего entry-quality результата.

Роли:

- `movement_score` как отдельный control feature;
- `movement_score` + rich fractal/price features как combined profile;
- без использования `selected` как входного признака.

Обязательные поля provenance:

```text
movement_artifact_path
movement_rule_id
movement_train_period
movement_score_split_mapping
movement_locked_before_entry_quality
```

### 7. Planned Execution Geometry

Сохранить текущую planned geometry, но не считать её полноценным рынковым
описанием:

```text
planned_limit_price
planned_entry_bid_equivalent
planned_protective_stop_price
planned_r_value
planned_entry_to_fractal0
planned_stop_distance
planned_limit_to_current_close
```

Эти признаки нужны как контроль: если rich model не превосходит planned
geometry, усложнение не оправдано.

## Feature Profiles Для Сравнения

Первая партия ограничена компактным bounded-набором:

| profile_id | Состав | Роль |
|---|---|---|
| `planned_geometry_only` | planned execution geometry + side + ATR | текущий baseline |
| `time_only` | session/weekday/month | контроль calendar effect |
| `structure_f0_only` | только `fractal0` structural fields | локальный фрактал |
| `structure_nearest_k20` | ближайшие 20 фракталов по расстоянию к planned limit/fractal0 | compact profile |
| `structure_nearest_k40` | ближайшие 40 фракталов | основной compact profile |
| `relative_geometry_k40` | relative distances/density без raw price | геометрия уровней |
| `price_action_h1` | H1 OHLC-window признаки | состояние цены |
| `movement_plus_time` | movement score + time | простой сильный control |
| `rich_combined_k40` | structure_k40 + relative geometry + price action + time + planned geometry | основной rich profile |
| `structure_nearest_k80` | ближайшие 80 фракталов | diagnostic-only |
| `structure_all100` | все 100 фракталов | diagnostic-only |

`rich_combined_k40` может выиграть только если превосходит простые controls:
`planned_geometry_only`, `time_only`, `movement_plus_time`,
`relative_geometry_k40`.

## Search Budget

До запуска записать `current_search_budget` и `cumulative_search_budget`.

Primary eligible сетка первой партии:

```text
n_profiles = 9
n_models = 3
n_targets = 3
n_primary_filters = 3
n_seeds = 1
n_total_ranked_configs = 243
```

`structure_nearest_k80`, `structure_all100`, `top20`, `top10`,
дополнительные seeds и XGBoost/LightGBM варианты в Phase A не входят в
eligible winner первого запуска. Если они запускаются, они должны иметь
`not_eligible_for_winner=true` и учитываться в `diagnostic_search_budget`.

Расширение после просмотра результатов первой партии запрещено без новой
версии спецификации или отдельного заранее записанного плана.

## Targets

Текущий target `pnl_r > 0` слишком грубый: микроплюс и сильная прибыль
становятся одинаковым классом.

## Training Universe

Primary universe: все planned E3 orders, построенные до факта исполнения.

Для каждого planned order сохранить:

```text
order_planned = true
order_filled
fill_lag
no_fill_reason
pnl_r_if_filled
pnl_r_per_planned_order
```

Модель качества сделки может обучаться только на filled trades, но тогда её
статус должен быть `conditional_quality_model`: она оценивает результат при
условии исполнения, а не качество limit-заявки целиком. В отчёте для обоих
режимов обязательны:

```text
fill_rate
no_fill_rate
expected_pnl_per_planned_order
expected_pnl_per_filled_trade
```

Selection по PF/BS_p05 проводится на фактически исполненных сделках, но
disclosure по planned orders обязателен, чтобы фильтр не выглядел лучше только
из-за игнорирования no-fill.

Target candidates:

```text
target_entry_ev_regression = pnl_r_if_filled
target_entry_good_0_5r = 1 if pnl_r_if_filled >= 0.5R else 0
target_entry_avoid_sl = 1 if close_reason != "SL" else 0
```

Diagnostic targets:

```text
target_entry_filled = 1 if order_filled else 0
target_entry_good_0_25r = 1 if pnl_r_if_filled >= 0.25R else 0
target_entry_good_1r = 1 if pnl_r_if_filled >= 1.0R else 0
target_entry_avoid_bad = 1 if pnl_r_if_filled > -0.5R else 0
```

Перед selection выполнить target-distribution audit по `train_core`,
`val_select`, `val_eval`, BUY/SELL и годам. Если любой eligible target имеет
меньше 100 наблюдений минорного класса на `train_core` или меньше 30
наблюдений минорного класса на `val_select`, он исключается из eligible
winner и остаётся только diagnostic.

Регрессионный target обязателен. Для него выбирать фильтр можно по predicted
EV или по predicted lower-bound, но не по фактическому `pnl_r` на `val_eval`.
Пороги `0.25R`, `0.5R`, `1.0R` считаются разными targets и входят в search
budget, если участвуют в eligible selection.

## Models

Не начинать с тяжёлой модели как primary. Eligible модели первой партии:

```text
ridge_regression / logistic_regression
hist_gradient_boosting
extra_trees_shallow
```

Diagnostic-only модели, если нужны для сравнения сложности:

```text
extra_trees_current
random_forest_shallow
xgboost_depth3
xgboost_depth5
lightgbm_small
```

XGBoost/LightGBM не удаляются из направления. В первой партии они могут
запускаться только как `diagnostic-only`, если зависимости уже доступны и это
зафиксировано до старта. Они не могут стать eligible winner первого запуска.

Если после первой партии rich-признаки дадут переносимый сигнал на
`val_eval`, следующий Phase B может заранее включить XGBoost/LightGBM в
eligible search budget отдельным планом. Добавлять их после просмотра
результатов Phase A без новой записи бюджета запрещено.

Каждая модель должна писать:

```text
model_family
seed
feature_profile_id
target_id
feature_count
train_rows
val_select_rows
val_eval_rows
normalization_contract
```

## Filter Policy

Primary filters:

```text
top50
top40
top30
```

Diagnostic-only filters:

```text
top20
top10
```

Причина: текущий `top10` оставил только `53` сделки на `val_eval` и не
перенёсся. Узкие срезы нельзя делать primary без отдельного доказательства
стабильности.

Для каждого фильтра:

- cutoff выбирается только на `val_select`;
- `val_eval` применяет только сохранённый cutoff;
- фактическая доля selected на `val_eval` пишется отдельно;
- если `val_eval n_trades < 300`, результат не может быть positive verdict,
  даже при высоком PF.

## Split И Selection

Использовать существующие роли:

```text
train_core: обучение ML-exit и ML-entry
val_select: выбор feature_profile + target + model + filter cutoff
val_eval: проверка выбранного правила
locked_test: not_opened
```

Selection protocol:

1. На `val_select` отфильтровать строки с `FEATURE_CONTRACT_FAIL`,
   `sample_size_gate FAIL` и diagnostic-only profile/filter/model/target.
2. Выбрать ровно один rule по заранее заданному порядку:
   `BS_p05`, затем `max_drawdown_r`, затем более простой profile/model.
3. Сохранить `selected_rule` с feature profile, target, model, seed, cutoff и
   всеми source artifact hashes.
4. На `val_eval` применить только этот `selected_rule` и заранее заданные
   baselines.
5. Остальную таблицу `val_eval`, если она сохраняется, пометить как
   `diagnostic_grid` и `not_eligible_for_winner=true`.

Запрещено:

- выбирать winner по `val_eval`;
- менять cutoff после просмотра `val_eval`;
- добавлять новые feature profiles после просмотра текущего результата без
  новой записи в search budget.

В отчёте отдельно печатать:

```text
selected_winner_val_eval
diagnostic_best_val_eval
```

`diagnostic_best_val_eval` нельзя использовать как новый winner без нового
заранее записанного плана.

## Baselines

Обязательные сравнения:

```text
S0/E3/M0/X0_fixed_r_0_7
S2/E3/M0/X2 no-mask
planned_geometry_only
time_only
movement_plus_time
simple_r_value_top50
simple_stop_distance_top50
```

Если rich profile не превосходит эти baselines по `BS_p05` на `val_eval`,
итог не может быть положительным.

`S2/E3/M0/X2` считается исследовательской механикой, а не доказанной заменой
`S0/E3/M0/X0`: в stop-grid она была выше по PF, но не лучше по `BS_p05`.
Поэтому rich-фильтр должен улучшить обе базы: собственный S2 no-mask и
предыдущий S0/X0 baseline.

## Метрики И Gates

Основные метрики:

```text
PF
BS_p05
mean_pnl_r
median_pnl_r
max_drawdown_r
n_trades
selected_fraction
SL-rate
pf_without_best_year
effective_profit_years
BUY/SELL split
yearly split
score distribution shift
target distribution by split/side/year
fill_rate
no_fill_rate
expected_pnl_per_planned_order
expected_pnl_per_filled_trade
delta_BS_p05
delta_mean_pnl_r
delta_max_drawdown_r
delta_SL_rate
permutation
```

Минимальные gates для positive research result:

```text
val_eval n_trades >= 300
val_eval BS_p05 > S2 no-mask BS_p05
val_eval BS_p05 > S0/X0 baseline BS_p05
val_eval PF > S2 no-mask PF
val_eval selected_fraction >= 0.15
effective_profit_years >= 1.5
negative_years = 0
permutation status PASS
stress-spread shortlist not failed
```

Если `BS_p05` хуже no-mask, результат может быть только `research_hint` или
`reject`, даже если PF выше.

Если `rich_combined_k40` не превосходит controls и baselines, ветку закрыть
без расширения модели. Расширять сложность допустимо только после отдельного
post-mortem и новой спецификации.

## Diagnostics

Обязательные диагностические артефакты:

```text
feature_contract_audit.csv
forbidden_column_audit.csv
target_distribution_audit.csv
planned_order_diagnostics.csv
score_distribution_diagnostics.csv
feature_importance_by_profile.csv
summary.csv
winner_yearly.csv
permutation.csv
json artifact
```

Feature audit должен раскрывать:

- какие raw CSV columns прочитаны;
- какие subfields фракталов использованы;
- какие top-level target columns запрещены и не использованы;
- какие признаки требуют OHLC и по какой временной границе;
- какие признаки normalized/scaled и где fit scaler.

## Multiple Testing Correction

Если `n_total_ranked_configs > 10`, permutation test должен повторять весь
selection protocol: profile, target, model, filter и cutoff выбираются заново
на каждой перестановке по тем же правилам, что и на реальных данных.

Permutation только на уже выбранной строке разрешён, но его статус:

```text
permutation_scope = selected_rule_only
permutation_verdict = diagnostic_only
```

В JSON обязательно сохранить:

```text
n_profiles
n_models
n_targets
n_filters
n_seeds
n_total_ranked_configs
n_diagnostic_configs
selection_protocol_replayed_in_permutation
```

## Validation Windows

Минимально требовать yearly/side disclosure. Если хватает данных, добавить
2-3 заранее заданных validation windows внутри validation:

```text
window_id
train_until
val_select_period
val_eval_period
selected_rule_id
selected_rule_val_eval_pf
selected_rule_val_eval_bs_p05
```

Если walk-forward/windows не запускаются, максимум результата остаётся
`RESEARCH_HINT_RICH_FEATURES`, даже при прохождении основных gates.

## Implementation Tests

Минимальные тесты реализации:

- запрет top-level future columns во feature builder;
- `Up/Dn` читаются только из serialized `fractal*`, не из top-level
  target-колонок;
- OHLC-признаки используют только `last_fully_closed_h1_bar` и прошлые бары;
- `val_eval` применяет сохранённый cutoff, а не пересчитывает `topX`;
- `top10` и `top20` не могут дать positive verdict;
- `val_eval n_trades < 300` блокирует positive verdict;
- `feature_count`, порядок колонок и имена совпадают между `train_core`,
  `val_select` и `val_eval`;
- simple/topX cutoff считается только по валидным score;
- no-fill строки входят в planned-order disclosure;
- JSON содержит search budget, split roles, feature contract, target
  contract и baseline comparisons.

После Python-изменений запускать:

```bash
./.venv/bin/python -m pytest tests/ -q
```

## Verdicts

Разрешённые статусы:

```text
REJECT_RICH_ENTRY_QUALITY
RESEARCH_HINT_RICH_FEATURES
ABORT_FEATURE_CONTRACT_FAIL
```

Разрешённая рекомендация следующего шага:

```text
recommendation = RICH_ENTRY_REPLICATION_REQUIRED
```

Запрещённые статусы:

```text
CANDIDATE
FROZEN
READY_FOR_LOCKED_TEST
LIVE_READY
PRODUCTION
```

Даже при сильном результате этап не открывает `locked_test`.

Максимум при текущем eligible search budget `243`:

```text
RESEARCH_HINT_RICH_FEATURES
```

`RICH_ENTRY_REPLICATION_REQUIRED` разрешён только для следующего отдельного
этапа, если заранее задана малая сетка, пройдены gates и permutation повторяет
весь selection protocol.

## Артефакты

Планируемый префикс:

```text
ML/reports/fractal0_rich_entry_quality
```

Ожидаемые файлы:

```text
ML/reports/fractal0_rich_entry_quality.json
ML/reports/fractal0_rich_entry_quality_summary.csv
ML/reports/fractal0_rich_entry_quality_scores.csv
ML/reports/fractal0_rich_entry_quality_feature_contract.csv
ML/reports/fractal0_rich_entry_quality_target_distribution.csv
ML/reports/fractal0_rich_entry_quality_planned_order_diagnostics.csv
ML/reports/fractal0_rich_entry_quality_score_diagnostics.csv
ML/reports/fractal0_rich_entry_quality_permutation.csv
ML/reports/fractal0_rich_entry_quality_winner_yearly.csv
docs/reports/2026-07-21-fractal0-rich-entry-quality.md
```

## Важные Ограничения

1. Это не новый поиск direction от next open. Он уже многократно слабел в
   прошлых исследованиях.
2. Это проверка качества конкретной E3-сделки с уже заданной stop/exit
   механикой.
3. `Up/Dn` можно использовать только внутри serialized `fractal*` как
   состояние фрактальных объектов; top-level `up_*`/`dn_*` запрещены как
   target leakage.
4. M5 используется только для исполнения, не как feature source.
5. Если rich features опять выбирают маленький top10/top20 срез, который не
   переносится на `val_eval`, ветку нужно закрывать как
   `REJECT_RICH_ENTRY_QUALITY`, а не подбирать ещё одну модель.
6. Optional-модели и широкие фрактальные профили можно запускать только если
   они заранее помечены как diagnostic-only или вынесены в Phase B с отдельным
   search budget. Добавлять их после просмотра результата текущей партии как
   eligible-варианты запрещено.
