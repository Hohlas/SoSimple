---
last_updated: 2026-05-23
sources: 10
status: active
---

# Execution Tracks: Take/Skip v1/v2 + Trailing Stop + Execution Policy (04-17 — 04-22)

## 4a. Take/Skip Trailing-Stop Matrix (04-17) — v1 reject

Первая проверка бинарной постановки `take/skip`: модель должна решать, стоит ли
брать вход при trailing-stop логике.

Постановка: `take = 1` если `trail_48_pnl_atr_xN >= 0.5`, иначе `skip`.

Результат полного matrix run (seq20/50/100):

- Все три конфигурации: `verdict = reject`
- Ни один кандидат не прошёл gate `PF >= 1.0`
- Абсолютный probability threshold неработоспособен: модель выдаёт слишком сжатый скор

**Вывод**: смена постановки с regression/quantile на бинарный `take/skip` не решила проблему. Track A почти исчерпан не только на уровне selection layer, но и на уровне самого обучающего сигнала.

Источник: [2026-04-17-take-skip-trailing-stop-matrix.md](../../docs/reports/2026-04-17-take-skip-trailing-stop-matrix.md)

## 4b. Multi-Horizon Take/Skip Feature Track Handoff (04-17) — v2 scaffold

После провала v1 гипотеза сместилась: проблема не в selection layer, а в
представлении данных. Новая постановка `take_skip_trailing_stop_v2`:

- Полные 100 фракталов (вместо усечённой последовательности)
- Multi-scale сводки по окнам 5/10/20/50/100 (mean, std, slope proxy, range)
- Multi-horizon бинарные targets: `take_H_xX` для H ∈ {12,24,48}, X ∈ {2,4,8}
- Positive class: `trail_pnl >= 0.5 ATR`

Локальный smoke-run `transformer_seq20`: `verdict = go`.
Validation winner: `take_48_x4 + top_k_probability 0.05`, PF=6.39, 24 сделки, negative_year_slices=0.

**Статус**: контур готов к полному server matrix run. Это не итоговый verdict.

Источник: [2026-04-17-multi-horizon-take-skip-feature-track-handoff.md](../../docs/reports/2026-04-17-multi-horizon-take-skip-feature-track-handoff.md)

## 5. Take/Skip v2 Frequency Follow-Up (04-18)

Короткий follow-up уже после первого положительного verdict-а `take_skip_trailing_stop_v2`. Цель была не искать новый winner через переобучение, а понять две вещи:

- можно ли заметно поднять частоту сделок;
- помогает ли более широкий trailing-stop `x10 / x12`, если использовать уже найденный score-контур.

Важное ограничение этапа: в репозитории не было канонически сохранённых `take_skip_trailing_stop_v2` prediction CSV, поэтому score для `seq50` был локально восстановлен из checkpoint без нового обучения, но с тем же feature representation (`539` input features).

### Quality-first остался базовым эталоном

Лучший чистый режим не изменился:

- `score = take_24_x8`
- `selector = prob >= 0.70`
- `exit = x8`

Метрики:
- validation: `27 trades`, `6.75 trades/year`, `PF=inf`, `negative_year_slices=0`
- test: `41 trades`, `8.2 trades/year`, `PF=39.74`, `negative_year_slices=0`

### Frequency-first дал отдельный рабочий режим

Новый follow-up нашёл уже не самый "красивый" PF, а более плотную область по числу сделок:

- `score = take_24_x4`
- `selector = top_k 20%`
- `exit = x10`

Метрики:
- validation: `95 trades`, `23.75 trades/year`, `PF=3.92`, `negative_year_slices=0`
- test: `96 trades`, `19.2 trades/year`, `PF=7.18`, `negative_year_slices=1`

### Anchor-expansion оказался лучшим frequent-кандидатом

Следующий frozen refinement не менял обучение и не искал новый score-family. Он просто добавил третий режим отбора: расширение вокруг уже подтверждённого `quality-first` winner-а, с приоритетом:

- тот же score-family;
- тот же exit-family;
- больше сделок, чем у quality-first;
- минимальный уход от базового winner-а.

Именно этот anchored-режим дал лучший practical compromise:

- `score = take_24_x8`
- `selector = top_k 20%`
- `exit = x8`

Метрики:
- validation: `95 trades`, `23.75 trades/year`, `PF=3.89`, `negative_year_slices=0`
- test: `96 trades`, `19.2 trades/year`, `PF=7.17`, `negative_year_slices=0`

### Узкий sweet spot внутри anchored-зоны

После этого был сделан ещё более узкий frozen-sweep только по `top_k` в диапазоне `16%–20%`, уже без смены score-family и exit-family.

Лучший practical compromise под критерий **`>15 trades/year`** оказался не на `20%`, а на `17%`:

- `score = take_24_x8`
- `selector = top_k 17%`
- `exit = x8`

Метрики:
- validation: `20.25 trades/year`, `PF=7.64`, `negative_year_slices=0`
- test: `16.4 trades/year`, `PF=13.12`, `negative_year_slices=0`, `max_drawdown_atr=4.03`

### Вывод по follow-up

- Линия `take_skip_trailing_stop_v2` живёт не только как low-frequency high-PF candidate, но и как более частый режим.
- Raw `frequency-first` оказался полезной диагностикой, но не финальным frequent-winner-ом.
- Лучший текущий frequent-кандидат — `anchor-expansion`, потому что он даёт ту же частоту, но без отрицательного годового среза на test.
- Ещё лучше оказался узкий sweet spot внутри anchored-зоны: `top_k 17%` сохраняет частоту выше 15 сделок в год, но заметно улучшает PF и drawdown относительно `20%`.
- Практический компромисс:
  - quality-first: чище, стабильнее, реже;
  - anchor-expansion: почти в 2.3 раза больше сделок на test (`8.2 -> 19.2 trades/year`) при сохранении `negative_year_slices=0`;
  - anchor sweet spot 17%: `16.4 trades/year`, `PF=13.12`, `negative_year_slices=0`, то есть лучший компромисс под floor `>15/year`;
  - raw frequency-first: такая же частота, но хуже yearly stability.
- Для следующего шага зафиксированы два канонических frozen rule-артефакта:
  - `ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json`
  - `ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json`

На этом этапе разумно не переобучать модель снова. Если продолжать, то только узко вокруг anchored sweet spot `top_k 16%–18%`.

Источник: [2026-04-18-take-skip-frequency-followup.md](../../docs/reports/2026-04-18-take-skip-frequency-followup.md)

### Rule Consumer (04-18): frozen rules стали рабочим интерфейсом

После фиксации двух frozen rule JSON был добавлен отдельный consumer-слой:

- `API/export_take_skip_trailing_stop_v2_signals.py`

Его задача не в новом исследовании и не в переобучении, а в стандартном применении уже выбранных правил к готовому prediction CSV.

Поддержаны оба режима:
- `quality`: `take_24_x8 + prob_ge_threshold >= 0.70`
- `frequency`: `take_24_x8 + top_k_probability = 17%`

Что умеет exporter:
- читать frozen rule JSON и доставать `score_target`, `selector`, `threshold`;
- применять rule к колонке `pred_<score_target>`;
- писать `time;signal`;
- при `--base-csv` разворачивать sparse predictions обратно в полный временной ряд;
- при `--copy-to-mt4` сразу класть результат в tester/runtime `ml_signals.csv`.

Смысл этого этапа: `take_skip_trailing_stop_v2_quality_selected_rule.json` и `take_skip_trailing_stop_v2_frequency_selected_rule.json` больше не являются только отчётными артефактами. Они стали прикладным интерфейсом, который можно одинаково запускать на любом готовом prediction CSV.

Источник: [2026-04-18-take-skip-rule-consumer.md](../../docs/reports/2026-04-18-take-skip-rule-consumer.md)

### MT4 Trailing-Stop Execution (04-18): direct mode теперь умеет честный trailing exit

После consumer-слоя выяснилось важное ограничение: MT4 уже мог тестировать новые `quality` и `frequency` входы, но всё ещё закрывал сделки старым способом через `ML_HoldBars`. Это значило, что MT4 подтверждал только новый **entry-layer**, а не тот тип выхода, под который строился `take_skip_trailing_stop_v2`.

Чтобы убрать этот разрыв, в прямой MT4-контур `iSignal=3` был добавлен отдельный режим:

- `ML_ExitMode = 0` -> старый timeout parity-check
- `ML_ExitMode = 1` -> отдельный trailing-stop по `ML_TrailATR * ATR`

Принцип intentionally простой и совпадает с новой исследовательской линией:

- BUY:
  - лучший максимум после входа хранится по `High[bar]`
  - уровень выхода = `best_high - ATR * X`
- SELL:
  - лучший минимум хранится по `Low[bar]`
  - уровень выхода = `best_low + ATR * X`

Что важно practically:

- trailing реализован прямо внутри `lib_ML_Signal.mqh`;
- старые `OUTPUT()/TRAILING_STOP()` по-прежнему не участвуют в `iSignal=3`;
- timeout path сохранён как default, поэтому старые parity-check сценарии не сломаны;
- в tester-логе появились отдельные строки `reason=TrailingStop`, а также поля `best`, `trail`, `trail_atr`.

**Смысл этапа:** теперь MT4 может проверить не только "хорошо ли новый CSV выбирает входы", но и "что будет, если исполнить эти входы именно на trailing-stop-логике".

**Новый практический вопрос:** какой режим лучше проходит через реальное MT4 execution:

- `quality` + trailing `x8`
- `frequency` + trailing `x8`

Именно этот ручной tester-check теперь стал следующим честным шагом для `take_skip_trailing_stop_v2`.

Источник: [2026-04-18-mt4-trailing-stop-execution.md](../../docs/reports/2026-04-18-mt4-trailing-stop-execution.md)

### Execution Policy v2 (04-19): выходы проверены в Python и MT4

Следующий этап закрыл практический вопрос после добавления MT4 trailing execution: какой выход использовать для уже готовых `quality` и `frequency` сигналов.

Добавлен `ML/benchmark_execution_policy_v2.py`:

- работает без нового обучения;
- читает готовые `ml_signals_quality.csv` и `ml_signals_frequency.csv`;
- использует `DATA/XAUUSD_H1_OHLC.csv`;
- сравнивает варианты выхода в ATR;
- считает не только PF, но и форму equity.

Ключевые метрики:

- `max_drawdown_atr`;
- `ulcer_index_atr`;
- `equity_linearity_r2`;
- `profit_concentration_top_1/3/10`;
- `negative_months / negative_years`;
- худшая сделка и худшие серии.

В MT4 добавлен `ML_TakeProfitATR`: обычный broker-side take profit в ATR от входа. `0` означает, что take profit выключен.

#### Quality

MT4:

| Mode | Net Profit | Trades | PF | Max Relative DD | Max Win |
|---|---:|---:|---:|---:|---:|
| `TrailATR=8, TP=0` | 18037.59 | 20 | 51.95 | 11.70% | 7996.90 |
| `TrailATR=8, TP=12` | 11544.89 | 20 | 33.61 | 4.97% | 1817.00 |

**Вывод:** take profit `12 ATR` сильно режет одиночную экстремальную сделку и снижает просадку, но уменьшает прибыль. Для `quality` это допустимый более ровный режим.

#### Frequency

MT4:

| Mode | Net Profit | Trades | PF | Max Relative DD |
|---|---:|---:|---:|---:|
| `TrailATR=6, TP=0` | 18455.93 | 56 | 4.22 | 16.78% |
| `TrailATR=8, TP=0` | 24521.88 | 56 | 3.77 | 25.71% |
| `TrailATR=10, TP=0` | 26137.10 | 56 | 3.31 | 27.44% |
| `TrailATR=8, TP=12` | 12085.05 | 56 | 2.37 | 17.27% |

Python `frequency_trail_scan`:

| Policy | PF | Net ATR | Max DD ATR | Ulcer | R2 | Top 1 | Top 3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `trail_x6` | 4.08 | 169.72 | 18.00 | 5.79 | 0.821 | 13.8% | 37.3% |
| `trail_x8` | 3.73 | 215.77 | 22.54 | 7.28 | 0.766 | 18.9% | 38.1% |
| `trail_x10` | 4.12 | 323.09 | 39.66 | 16.52 | 0.564 | 30.3% | 56.7% |

**Вывод:** для `frequency` take profit режет главный источник прибыли. Основной practical candidate — `ML_TrailATR=8`, `ML_TakeProfitATR=0`; осторожная альтернатива — `ML_TrailATR=6`, `ML_TakeProfitATR=0`. `TrailATR=10` даёт больше прибыли, но слишком ухудшает форму equity: просадка, ulcer, концентрация прибыли и линейность хуже.

Источник: [2026-04-19-execution-policy-v2.md](../../docs/reports/2026-04-19-execution-policy-v2.md)

### lib_PIC External Selection (04-20): признаки полезны как диагностика, но не заменяют rule

Следующий быстрый шаг проверил идею внешнего слоя отбора поверх уже готовых `take_skip_trailing_stop_v2` prediction CSV. Модель не переобучалась: benchmark просто добавлял к строкам prediction производные признаки `lib_PIC` и выбирал порог признака только на validation.

Добавлен `ML/benchmark_take_skip_lib_pic_selection.py`:

- соединяет prediction CSV и source/labeled CSV по порядку строк и `time`;
- строит профиль `baseline_clean_geometry_path`;
- проверяет ограниченную сетку feature-фильтров вида `feature >= validation_quantile`;
- замораживает числовой порог признака и применяет его на test без пересчёта.

Ключевой результат:

| Mode | Rule | Feature filter | Test trades/year | Test PF | Negative years |
|---|---|---|---:|---:|---:|
| quality-first | `take_24_x8`, `prob >= 0.70`, exit `x8` | none | 8.2 | 39.74 | 0 |
| raw frequency-first | `take_24_x4`, `top_k 20%`, exit `x10` | none | 19.2 | 7.18 | 1 |
| feature-frequency-first | `take_24_x8`, `top_k 20%`, exit `x10` | `pic_path_win_proxy24_share_w20 >= 0.25` | 14.8 | 5.30 | 0 |

**Вывод:** внешний `lib_PIC`-фильтр не улучшил quality-кандидат и не стал новым главным правилом. Но он показал полезный устойчивостный сигнал: фильтр по доле свежих фракталов с благоприятным ходом выше неблагоприятного режет часть сделок и убирает отрицательный годовой срез на test.

Практическое следствие: не стоит дальше усложнять внешний selection-layer. Более рационально использовать этот результат как аргумент для нового training track, где `lib_PIC`-производные признаки будут доступны самой модели при обучении.

Источник: [2026-04-20-take-skip-lib-pic-selection.md](../../docs/reports/2026-04-20-take-skip-lib-pic-selection.md)

### lib_PIC Feature Training (04-20): добавление признаков внутрь модели не прошло gate

Следующий этап проверил более сильную гипотезу: если внешний `lib_PIC`-фильтр даёт устойчивостный сигнал, сможет ли модель использовать эти признаки напрямую во время обучения.

Добавлен отдельный dual-stream training contour:

- sequence branch читает `fractal0..fractal99`;
- engineered branch читает профиль `lib_PIC`;
- проверены `baseline_clean`, `baseline_clean_path`, `baseline_clean_geometry_path`;
- проверены `seq_len = 20 / 50 / 100`;
- runner автоматически ограничивает цели теми `take_skip_v2` target columns, которые есть в текущих CSV.

Результат полной серверной сетки:

| Metric | Value |
|---|---:|
| Configs | 9 |
| Runtime | 3123.32 sec |
| Verdicts | 9 reject |
| validation grid rows | 1377 |
| rows with `PF > 1` | 79 |
| rows with `PF > 1` and `trades_per_year >= 6` | 0 |

Лучшие редкие точки были только на 3-5 сделках за validation (`0.75-1.25` trades/year). При практической частоте `>=6` trades/year лучший validation PF был ниже единицы:

| Run | Target | Selector | Trades/year | Validation PF |
|---|---|---|---:|---:|
| `baseline_clean_seq20` | `take_12_x2` | `top_k=5%` | 6.0 | 0.9476 |
| `baseline_clean_seq100` | `take_12_x2` | `top_k=5%` | 6.0 | 0.9020 |
| `baseline_clean_seq20` | `take_24_x2` | `top_k=5%` | 6.0 | 0.8416 |

**Вывод:** простое добавление `lib_PIC`-профилей внутрь dual-stream модели не создало рабочий selection layer. `lib_PIC` пока выглядит полезнее как внешний фильтр, чем как прямое расширение входа модели.

Важное ограничение: это не доказывает, что новые признаки вредят старой прибыльной модели. Контур обучения изменился: новый runner, доступная старая target-сетка `x2/x4/x8`, очищенные профили, BCE-обучение и post-hoc PF benchmark. Следующий честный шаг — controlled ablation: воспроизвести исходный baseline и добавить к нему сильные `lib_PIC` path-признаки.

Источник: [2026-04-20-take-skip-lib-pic-feature-training.md](../../docs/reports/2026-04-20-take-skip-lib-pic-feature-training.md)

### Original Contour Feature Ablation (04-20): `path` признаки дают practical uplift

После провала dual-stream feature training был выполнен более строгий controlled ablation: новые `lib_PIC` признаки добавлялись не в новую архитектуру, а поверх старого single-tensor `take_skip_v2` контура.

Добавлен `ML/run_take_skip_original_contour_feature_matrix.py`:

- `original_baseline` восстанавливает старый input contract;
- `original_plus_path` добавляет path-reaction признаки;
- `original_plus_geometry_path` добавляет path + geometry признаки;
- проверены `seq_len = 20 / 50 / 100`;
- все engineered-признаки повторяются на каждом шаге sequence tensor.

Контроль `original_baseline_seq50` прошёл gate:

| Metric | Value |
|---|---:|
| input_features | 539 |
| target / selector | `take_24_x8`, `prob>=0.70` |
| validation trades/year | 7.75 |
| validation PF | inf |
| test trades/year | 9.2 |
| test PF | 49.58 |
| test negative years | 0 |

Полная матрица `3 × 3` завершилась за `2840.42 sec`; все 9 конфигураций получили `go`.

Лучший practical candidate:

| Run | Rule | Validation | Test |
|---|---|---|---|
| `original_plus_path_seq50` | `take_24_x8`, `prob>=0.60`, exit `x8` | `9.75` trades/year, PF `16.07` | `10.2` trades/year, PF `38.78`, negative years `0` |

Сравнение с `original_baseline_seq50`:

- test trades/year выросли `8.4 -> 10.2`;
- test PF снизился `43.35 -> 38.78`, но остался очень высоким;
- negative years остались `0`;
- max drawdown снизился `4.38 -> 3.89 ATR`.

Geometry-ветка не выбрана: PF высокий, но test частота только `4.8` trades/year, ниже practical gate.

**Вывод:** `lib_PIC` path-признаки не ломают старый прибыльный контур и дают полезный trade-off: больше сделок при сохранении высокого PF. Это первый положительный результат именно от добавления `lib_PIC` признаков внутрь модели.

MT4 confirmation:

| Exit | Trades | Net profit | PF | Relative DD |
|---|---:|---:|---:|---:|
| `TrailATR=8`, `TP=0` | 29 | 22294.65 | 23.79 | 14.74% |
| `TrailATR=8`, `TP=12` | 29 | 15873.12 | 17.23 | 6.64% |

MT4 log for `TP=0` confirmed `Position blocked=0`, `Score filtered=0`, `Opened=29`, `Trailing closes=29`. `TP=0` keeps trend tails and gives higher net profit; `TP=12` cuts tails and lowers drawdown.

Signal-export parity was closed on 2026-04-22:

| Metric | Value |
|---|---:|
| export nonzero rows | 51 |
| export unique `time` | 37 |
| export unique `time+signal` | 37 |
| duplicate `time+signal` rows | 14 |
| same-time opposite signal groups | 0 |
| MT4 opened trades | 29 |
| MT4 position blocked | 0 |
| MT4 score filtered | 0 |

Interpretation: duplicate timestamps are expected in DATA because one H1 bar can form multiple different `lib_PIC` peaks/levels. They should not be collapsed in DATA. The runtime signal format `time;signal` is coarser: MT4 consumes direct ML signals by bar time, not by DATA row id.

Практическое следствие: `original_plus_path_seq50` становится третьей MT4-подтверждённой системой рядом с текущими `quality` и `frequency`. `original_baseline_seq50/100` остаётся quality anchor.

Источники: [2026-04-20-take-skip-original-contour-feature-ablation.md](../../docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md), [2026-04-22-signal-export-parity.md](../../docs/reports/2026-04-22-signal-export-parity.md)

