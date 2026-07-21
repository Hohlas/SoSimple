# Аудит Fractal0 Entry Quality Filter

Дата: 2026-07-21

Проверены:

- `docs/reports/2026-07-21-fractal0-entry-quality-filter.md`
- `ML/reports/fractal0_entry_quality_filter.json`
- `ML/reports/fractal0_entry_quality_filter_summary.csv`
- `ML/reports/fractal0_entry_quality_filter_scores.csv`
- `ML/reports/fractal0_entry_quality_filter_trades.csv`
- `ML/reports/fractal0_entry_quality_filter_yearly.csv`
- `ML/reports/fractal0_entry_quality_filter_permutation.csv`
- `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
- `CONTEXT_HANDOFF.md`
- `CHANGELOG.md`
- `wiki/research/fractal-stop-research.md`

## Главный вывод

Отчёт в целом честно формулирует главный результат: `entry_quality_top20`
перспективен по PF и mean PnL, но не доказал превосходство над no-mask по
консервативной метрике `BS_p05`. С выводом `RESEARCH_ONLY` согласен.

Однако перед следующим этапом нужно исправить несколько методических и
артефактных проблем. Самая серьёзная: простые baseline-фильтры
`simple_stop_distance_top50` и `simple_r_value_top50` фактически сломаны и
дали 0 сделок из-за NaN cutoff. Это не влияет на выбранный
`entry_quality_top20`, но ослабляет доказательство, что ML-entry даёт пользу
поверх простой геометрии.

## Что считаю корректным

1. `locked_test` не открыт. В отчёте и JSON указано `locked_test =
   not_opened`.

2. Winner выбран на `val_select`, а `val_eval` использован как проверка
   фиксированного cutoff. В summary у winner один и тот же
   `score_cutoff_on_val_select = 0.364504748199685` на `val_select` и
   `val_eval`.

3. Отчёт правильно не делает trading/candidate вывод. Итоговая формулировка
   "research hypothesis, not candidate" соответствует методике.

4. Отчёт правильно раскрывает слабое место результата: на `val_eval` PF
   вырос с `2.5317` до `2.9439`, но `BS_p05` упал с `2.2865` до `2.1886`.
   Поэтому фильтр не доказал устойчивое превосходство над no-mask.

5. В wiki и handoff основной вывод синхронизирован осторожно: результат
   помечен как `research_only`, нужен заранее зафиксированный shortlist/stress
   probe.

## Критические замечания

### 1. Simple baseline-фильтры top50 сломаны

В `ML/reports/fractal0_entry_quality_filter_summary.csv`:

- `simple_stop_distance_top30`: `1481` сделка на `val_select`;
- `simple_r_value_top30`: `1454` сделки на `val_select`;
- `simple_stop_distance_top50`: `0` сделок;
- `simple_r_value_top50`: `0` сделок.

Это нелогично: top50 не должен выбирать меньше сделок, чем top30.

Причина видна в коде:

- `apply_entry_filter()` считает cutoff по всем entry rows;
- `stop_distance_atr` и `r_value_atr` заполнены только для filled rows;
- на `val_select` всего `4731` entry rows, но filled только `2294`;
- для top50 нужно взять примерно `2366` строк, то есть cutoff попадает в NaN
  зону;
- сравнение `score >= NaN` возвращает false, поэтому фильтр выбирает 0 строк.

Это не ломает ML-winner напрямую, но ломает контрольную проверку: отчёт не
доказывает, что ML-entry лучше простой геометрии, потому что часть геометрических
baseline-ов некорректна.

Что исправить:

- для фильтров, где score существует только после fill, считать cutoff только
  на строках с `filled = True`, либо явно запретить такие фильтры как
  pre-entry baseline;
- добавить тест: top50 не может выбрать меньше строк, чем top30, если score
  задан на одной и той же выборке;
- в отчёт добавить предупреждение, что текущие `simple_*_top50` строки
  недействительны.

### 2. Не до конца определён момент принятия решения entry-фильтром

Отчёт пишет, что entry features доступны на момент входа. Но текущий runner
считает часть признаков через поля, которые заполнены только для filled rows:

- `entry_to_fractal0_atr`;
- `stop_distance_atr`;
- `r_value_atr`.

Для фактической live-механики надо явно решить, когда применяется entry-filter:

- до отправки limit-заявки;
- после постановки limit, но до fill;
- после fill.

Если фильтр применяется до отправки заявки, признаки должны считаться от
известной limit price, а не от `entry_bid_equivalent`, который сейчас NaN для
no-fill строк. Если фильтр применяется после fill, он уже не является чистым
entry-фильтром, а становится фильтром удержания/активации позиции после
исполнения.

Что исправить:

- в отчёте и коде явно зафиксировать `decision_time`;
- пересчитать entry-time-safe признаки от planned limit price;
- отдельно хранить `planned_entry_price`, `planned_stop_price`,
  `planned_r_value_atr`;
- запретить признаки, которые появляются только после фактического fill, если
  фильтр должен работать до отправки заявки.

### 3. JSON artifact недостаточно самодостаточен

В отчёте есть `Статус: Completed` и `Вердикт: RESEARCH_ONLY`, но в
`ML/reports/fractal0_entry_quality_filter.json` нет top-level полей:

- `status`;
- `verdict`;
- `lifecycle_status`;
- `split_roles`;
- `forbidden_interpretations`;
- `entry_feature_columns`;
- `entry_label_contract`;
- `filter_contract`.

Часть информации есть в markdown, часть в коде, но машинный артефакт должен
быть каноническим источником для следующего агента.

Что исправить:

- добавить `status = completed`;
- добавить `verdict = research_only`;
- добавить `lifecycle_status = research_hypothesis`;
- добавить `split_roles`;
- добавить `forbidden_interpretations`;
- добавить список entry features и label contract;
- добавить contract: `val_select` chooses cutoff, `val_eval` applies fixed
  cutoff.

### 4. Permutation не прошёл, это надо сильнее подчеркнуть

В JSON:

```text
empirical_p_value = 0.15422885572139303
status = RESEARCH_HINT
```

Отчёт говорит, что permutation artifact exists и что это не license для
повышения статуса. Это корректно, но слишком мягко. Методически лучше прямо
написать: permutation correction не подтвердила статистическое отделение
выбранного filter winner от перестановочного выбора.

Что исправить:

- добавить таблицу permutation в отчёт;
- явно написать: `permutation_status = RESEARCH_HINT`, не PASS;
- добавить это в ограничения и next-step gate.

### 5. Сравнение с no-mask неполное

Отчёт сравнивает winner с no-mask внутри S2/E3/M0/X2. Это правильно, но
следующий probe должен сравнивать минимум три линии:

- `S2/E3/M0/X2/M0_no_mask`;
- `S2/E3/M0/X2/entry_quality_top20`;
- прежний сильный baseline `S0/E3/M0/X0_fixed_r_0_7`.

Иначе можно сделать неверный вывод, что entry-filter улучшил систему, хотя
он улучшил только один выбранный stop-grid путь, который сам не доказал
превосходство над S0/X0 по `BS_p05`.

Что добавить:

- в отчёт добавить явную таблицу сравнения с S0/X0 baseline из предыдущего
  этапа;
- в next step записать S0/X0 как обязательный контроль.

### 6. Fraction shift слишком большой для будущего frozen-rule

Winner `entry_quality_top20` выбрал:

- `18.79%` filled trades на `val_select`;
- только `8.79%` filled trades на `val_eval`.

Это говорит о сильном сдвиге распределения score. Отчёт это раскрывает, но
следующий план должен не просто "freeze exact cutoff", а проверить калибровку.

Что добавить:

- distribution diagnostics по score: p10/p30/p50/p70/p90 для train,
  `val_select`, `val_eval`;
- доля NaN/zero-filled score;
- stability chart/table для фактической выбранной доли;
- если используется фиксированный cutoff, заранее задать минимальное число
  сделок и правило отказа, если selected fraction сжимается слишком сильно.

## С чем не согласен или где нужна осторожная формулировка

1. Не согласен с неявным впечатлением, что `entry_quality_top20` является
   лучшим направлением для следующего frozen probe. По `val_eval` лучше
   выглядят `entry_quality_top30` и `entry_avoid_sl_top30`, но они не могут
   заменить winner задним числом. Поэтому следующий probe не должен просто
   брать top20 как "лучший"; корректнее заранее зарегистрировать shortlist из
   нескольких правил и не менять его после просмотра нового результата.

2. Не согласен считать simple baselines уже проверенными. Из-за NaN/cutoff
   проблемы top50 строки недействительны, а top30 сравнивается с ML-фильтрами
   несимметрично. До исправления этого места нельзя утверждать, что ML-entry
   превосходит простую геометрию.

3. Не согласен с формулировкой, что все entry features доступны на момент
   входа, пока в коде признаки для no-fill строк NaN. Доступность признака
   должна быть доказана через planned limit/stop contract, а не через
   заполненность после фактического fill.

## Что добавить перед следующим этапом

1. Исправить simple baseline фильтры и пересчитать summary.

2. Добавить в JSON top-level поля `status`, `verdict`,
   `lifecycle_status`, `split_roles`, `forbidden_interpretations`,
   `entry_feature_columns`, `entry_label_contract`, `filter_contract`.

3. Добавить в отчёт permutation table:

```text
method = block_shuffled_val_select_pnl_r
observed_winner_bs_p05 = 3.806873
null_repeats = 200
empirical_p_value = 0.154229
status = RESEARCH_HINT
```

4. Добавить score distribution diagnostics по split и filter score.

5. Добавить отдельную таблицу сравнения:

```text
S0/E3/M0/X0 baseline
S2/E3/M0/X2 no-mask
S2/E3/M0/X2 entry_quality_top20
S2/E3/M0/X2 entry_quality_top30 diagnostic
S2/E3/M0/X2 entry_avoid_sl_top30 diagnostic
```

6. Перед любым frozen/locked-test циклом сначала сделать shortlist-only
   stress-spread. Текущий результат без stress-spread и с permutation
   `RESEARCH_HINT` не готов к locked_test.

## Итоговая оценка

Текущий результат полезен как исследовательская гипотеза: entry-quality score
умеет отбирать подмножество сделок с более высоким PF и меньшей просадкой на
`val_eval`. Но доказательство слабее, чем может показаться по PF:

- `BS_p05` хуже no-mask;
- permutation не прошёл;
- осталось только 202 сделки;
- фактическая доля отбора на `val_eval` сильно сжалась;
- simple geometry baselines частично сломаны;
- decision_time entry-фильтра нужно формально уточнить.

Рекомендация: не переходить к `locked_test`. Сначала исправить baseline/cutoff
логику, усилить JSON disclosure, затем сделать заранее зафиксированный
shortlist/stress probe.
