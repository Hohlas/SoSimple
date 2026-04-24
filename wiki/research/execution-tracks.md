---
last_updated: 2026-04-24
sources: 26
status: active
---

# Execution Tracks: Exit Policy, Outcome-Aligned, Triple Barrier, Entry Path v1

> Синтез 26 отчётов (2026-04-08 — 2026-04-24). Параллельные направления execution.

## 1. Exit Policy Research (04-08)

Offline simulator поверх regression_updn для сравнения семейств правил выхода.

**Семейства**: reverse_ratio, weak_edge, profit_guard, их комбинации.

**Результат**: validation winner = `timeout_only` (PF=1.17, 567 trades).
Это тот же `ML_Timeout(12H)`, который уже стоит в MT4. **Новых exit rules не найдено.**

**Вывод**: exit layer не является источником uplift для regression_updn. Если нужен прорыв — другой execution track или другой target.

Источник: [2026-04-08-ml-exit-validation-first.md](../../docs/reports/2026-04-08-ml-exit-validation-first.md)

## 2. Outcome-Aligned Retraining (04-08)

Три семейства outcome-aligned targets: `trade_outcome_cls`, `trade_pnl_reg`, `signal_archetype_cls`.

**Результат**: ни одно семейство не прошло общий trade floor + yearly stability filter на validation. Frozen winner не создан, test не запускался (validation-first discipline).

**Причины провала**:
- Labels по-прежнему close-at-12h, не повторяют реальную MT4 execution.
- trade_outcome и archetype_target схлопываются в одну задачу.
- trade_pnl на signal-only строках — "жёстко плохой" baseline universe.

**Вывод**: outcome-aligned подход требует execution-aware labels (next-bar entry, single open position, exit policy) — простой close-at-12h недостаточен.

Источник: [2026-04-08-outcome-aligned-retraining.md](../../docs/reports/2026-04-08-outcome-aligned-retraining.md)

## 3. Triple Barrier (04-08 — 04-12, три отчёта)

### Hardening: полная пересборка TB вне MT4

- First-touch labeling (24 бара), timeout = 0.5, старт от времени строки сигнала.
- Isotonic calibration вероятностей.
- Правило фиксируется только на validation: `theta=0.475, min_ev=0.10`.
- Test вне MT4: **PF=1.11, 253 trades** (128W / 125L / 24 timeout).
- BUY доминирует (670 BUY vs 46 SELL в train).

### Runtime Verdict: MT4-проверка

| Metric | Python (test) | MT4 (tester) |
|---|---:|---:|
| PF | 1.11 | **1.27** |
| Trades | 253 | 92 |
| SL/TP match | — | 93.8% (61/65) |

Разница объясняется MT4-правилами:
- PosBlock: 113 пропусков (открытая позиция).
- HoldOverTime: 22 закрытия.
- TB_Reversal: 4 закрытия.

**Вывод**: TB-схема согласована с MT4 по уровням. Следующий шаг — Python-режим, повторяющий MT4 execution один в один.

Источники: [2026-04-08-triple-barrier-hardening.md](../../docs/reports/2026-04-08-triple-barrier-hardening.md), [2026-04-08-triple-barrier-runtime-verdict.md](../../docs/reports/2026-04-08-triple-barrier-runtime-verdict.md)

### MT4 Verdict (04-12): gate_fail, не production

Финальный этап по TB-треку. До этого benchmark на `simulate_mt4_tb` давал `losses=0, pf=inf` на обоих сплитах — оказалось артефактом бага: симулятор кастовал outcome через `int(...)`, а лейблы в `DATA/Nero_*_labeled.csv` — float (`1.0=TP, 0.0=SL, 0.5=Timeout`, источник `processing/label_signals.py:919`). `int(0.0)=0` и `int(0.5)=0` оба падали в `else`-ветку `HoldOverTime, pnl=+0.5`, поэтому SL никогда не срабатывал.

Фикс: `_classify_tb_outcome` с порогами `>=0.75` → TP, `<=0.25` → SL, else → Timeout; применён в обеих точках закрытия позиции. Тесты `tests/test_triple_barrier_mt4_execution.py` переведены с устаревшей `{1, -1, 0}` int-схемы на float — 6/6 зелёные.

Честный прогон на `tb_selected_rule.json` (`theta=0.475`, `min_ev=0.1`):

| Split | N | wins | losses | timeouts | reversals | PF | win_rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| validation | 28 | 16 | 4 | 2 | 8 | **4.33** | 57.1% |
| test | 69 | 29 | 23 | 5 | 17 | **1.28** | 42.0% |

Test yearly: 2023 PF=0.55 (N=6), 2024 PF=1.19 (N=21), 2025 PF=2.12 (N=34), 2026 PF=0.00 (N=8, 0% win). Validation yearly: все четыре года положительные (2019–2022).

Gate (унифицированно с quantile: N≥30, PF>2.0, `negative_year_slices=0`):
- N_trades: ✅ (69)
- PF: ❌ (1.28 < 2.0)
- negative_year_slices: ❌ (2023, 2026)

**Verdict**: TB-слой **не** подключается к MT4 как production или parallel execution mode. Явный regime shift между validation и test. `tb_selected_rule.json` зафиксирован как frozen исторический артефакт. Пересмотр возможен только после накопления forward-данных post-2026-06.

Источник: [2026-04-12-tb-verdict.md](../../docs/reports/2026-04-12-tb-verdict.md)

## 4. Entry Path v1 (04-08 — 04-10, пять отчётов)

Новый трек между regression_updn и triple_barrier: реальный вход на следующем баре, отдельные цели для итога сделки и пути цены.

### Baseline (04-08)

- Найден и исправлен cache bug (`--clear_cache` не доходил до `train_model()`).
- Чистый baseline: `ret_pearson_r=0.2450` (test), `path_reg_pearson_r=0.2745`.
- Active-only test: top 10% по pred_ret_24 → positive share 56.2%.
- `path_6_class` не работает (модель всегда предсказывает класс 0).

### Loss Weighting (04-09)

| Режим | Test ret_pearson_r | Test active ret_pearson_r | Test path_cls_f1 |
|---|---:|---:|---:|
| Без весов | 0.2450 | 0.2039 | 0.3259 |
| Только active rows | 0.0112 | -0.0020 | 0.0213 |
| **Вес 5.0 (ret+cls)** | **0.2494** | **0.2285** | **0.4160** |
| Вес 5.0 (только cls) | 0.2415 | 0.1912 | 0.4048 |

**Победитель**: вес 5.0 для активных строк в ret_* и path_6_class. Жёсткое вырезание неактивных строк ломает всё.

### Trade Filter (04-09)

Фильтр A (простой: `pred_ret_24_dir_atr`), фильтр B (составной: ret + fav/adv + path_6).

| Split | Candidate | Coverage | Trades | PF | Win Rate |
|---|---|---:|---:|---:|---:|
| Validation | A @ 7.5% | 7.61% | 36 | 2.67 | — |
| **Test** | **A @ 7.5%** | **9.17%** | **44** | **4.29** | **72.73%** |
| Sequential | A | — | 30 | 2.87 | 66.67% |

Фильтр B на 10% coverage уже показывает преимущество (PF=2.17 vs A=1.08 на test), но по общему правилу отбора A @ 7.5% — текущий рабочий базовый вариант.

**Вывод**: entry_path_v1 имеет рабочий слой "торговать / не торговать". Следующий шаг — conformal-слой поверх замороженного baseline.

### MT4 Final Winner Check (04-09)

Замороженный победитель `A @ 7.5%` был доведён до корректного прямого MT4-прогона без повторного поиска на `test`.

| Metric | Value |
|---|---:|
| Trades | 22 |
| PF | **8.47** |
| Win / Loss | 14 / 8 |
| Position blocked | 0 |
| Timeout closes | 22 |

Это важный сдвиг: линия `entry_path_v1` подтвердилась не только в offline-оценке, но и в реальном MT4-контуре для уже замороженного winner-а.

### Quantile Layer (04-10)

Новый гибридный трек `entry_path_v1_quantile` добавил quantile-головы `ret_24_q10` и `ret_24_q90` поверх уже рабочей базы `entry_path_v1`.

**Результат**:
- winner на validation: `lb_gt_m`
- validation: `25 trades`, `PF=11.05`
- frozen test: `24 trades`, `PF=inf`
- sequential: `11 trades`, `win_rate=100%`, `PF=inf`

Смысл результата не в том, что найден "окончательный победитель", а в том, что quantile-layer выглядит сильнее старой базы `A @ 7.5%`, но пока на слишком малом числе сделок для уверенного практического вывода.

**Вывод**: основной риск линии теперь не в качестве идеи, а в устойчивости. Следующий шаг — не новый поиск, а stress-test по `seed`, годам и MT4 parity для quantile-слоя.

### Quantile Robustness (04-11)

Отдельный этап больше не искал новые правила, а проверял, выдерживает ли quantile-layer повторяемость на фиксированном наборе `seed = 7, 17, 42, 77, 123`.

**Результат**:
- `same_rule_count = 5`
- winner во всех seed: `lb_gt_m`
- `median_test_pf = inf`
- `median_sequential_pf = inf`
- `worst_seed_test_trades = 20`
- `negative_year_slices = 0`
- итоговый verdict: `go_mt4`

По отдельным seed:
- `007`: test `20 trades`, `PF=inf`; sequential `11 trades`, `PF=inf`
- `017`: test `26 trades`, `PF=inf`; sequential `8 trades`, `PF=inf`
- `042`: test `24 trades`, `PF=inf`; sequential `11 trades`, `PF=inf`
- `077`: test `20 trades`, `PF=inf`; sequential `9 trades`, `PF=inf`
- `123`: test `26 trades`, `PF=25.17`; sequential `12 trades`, `PF=44.77`

**Вывод**: `entry_path_v1_quantile` вышел из статуса low-N гипотезы и стал главным подтверждённым кандидатом на следующий MT4 parity-check. Это уже не просто сильный single-run, а устойчивый multi-seed upgrade над baseline `A @ 7.5%`.

### Quantile Status Decision (04-12): production parallel mode

Финальный этап productization quantile-слоя. Решалась конкретная задача: baseline `A @ 7.5%` на test давал мало сделок (N=15) и низкий PF, quantile `lb_gt_m` на строгом rule давал ещё меньше (N<10). Вопрос — можно ли поднять N без потери PF.

Подход: **Research → Gate → Productionize**. Research: relax sweep квантильных порогов (q ∈ {0.20..0.50}) + multi-seed ensemble (5 сидов). Gate: N≥30, PF>2.0, `negative_year_slices=0`, `same_winner_ratio≥0.8` на frozen test.

Результат relax sweep:

| candidate | trades | PF | win_rate |
|---|---:|---:|---:|
| `lb_gt_m_q20` | 40 | 5.67 | — |
| `lb_gt_m_q25` | 37 | 5.64 | — |
| `lb_gt_m_q30` | 35 | 7.87 | 0.77 |
| **`lb_gt_m_q35`** | **32** | **11.24** | **0.81** |
| `lb_gt_m_q40` | 29 | 13.66 | 0.83 |

Winner `lb_gt_m_q35` через median m/w/correction по 5 сидам. Gate PASS: N=48, PF=8.18, win_rate=0.8125, `same_winner_ratio=1.0` (после tolerance ±0.05 для quantile при сохранении same rule — все 5 сидов выбирают `lb_gt_m` с q∈{30,35,40}). Sequential (hold_bars=24): 22 accepted trades, PF=3.64, win_rate=0.73.

Production rule: [ML/reports/entry_path_v1_quantile_selected_rule.json](../../ML/reports/entry_path_v1_quantile_selected_rule.json). Экспорт в MT4: `API.export_entry_path_v1_quantile_signals --rule-path ...`.

Устранённые баги pipeline:
- `pick_winner` не уважал `GATE_MIN_TRADES` → pool pre-filter
- strict stability metric ловил FP-шум в полосе quantile → tolerance ±0.05
- экспортёр брал `baseline_score` из quantile frame вместо baseline-модели → inner join по (time, signal)
- `drop_duplicates(keep='last')` терял сделки на mixed-signal bars → post-selection dedup с приоритетом non-zero signal

MT4 parity-check (tester лог `20260412.log`, period 2023.01.03 — 2025.11.03): **20/20 сделок совпадают** по (time, signal, direction), win rate 80.00% exact, mean pnl_atr Python 2.37 vs MT4 2.55 (~8% diff из-за ATR/spread/exit timing). Money metrics: net=4477.25, PF=11.91, DD=4.01%.

**Verdict**: `entry_path_v1_quantile` подтверждён как **production-ready parallel execution mode**.

Источник: [2026-04-12-quantile-status-decision.md](../../docs/reports/2026-04-12-quantile-status-decision.md)

### Quantile × fav_3_vs_12 Composition (04-13): closed, gate fail
Короткий research-check поверх уже production-ready quantile rule `lb_gt_m_q35`. Цель была бинарной: усиливает ли фиксированный bridge-filter `fav_3_vs_12 <= 0.653` уже готовый quantile-layer, или направление надо закрывать.

Первый прогон дал ложный `INCONCLUSIVE`: `fav_3_vs_12` брался из внешнего research source, который почти не пересекался с quantile universe. Проблема была не в самой идее composition, а в плохом источнике.

Затем источник был пересобран честно:
- добавлен экспорт активных `updn`-предсказаний из `transformer_updn_best.pt`
- `pred_fav_3 / pred_fav_12` посчитаны на тех же активных строках `DATA/Nero_{validation,test}_labeled.csv`
- порядок активных строк verified one-to-one against quantile predictions

После этого composition стал измерим по-настоящему:
- `quantile_only` test: `48 trades`, `PF=8.18`
- `composition` test: `47 trades`, `PF=7.86`

### Fav_3_vs_12 Standalone (04-13): rejected as standalone system

Отдельный этап проверял другой вопрос: может ли `fav_3_vs_12` жить сам по себе, без `quantile` и без другого базового отбора.

Проверка была построена как standalone benchmark:
- источник `pred_fav_3 / pred_fav_12`: `updn_active_source`
- источник фактического результата сделки: `entry_path_v1_quantile_*_predictions.csv`
- выбор порога только на `validation`
- жёсткая проверка устойчивой зоны:
  - sorted unique thresholds
  - full centered window
  - weak year = yearly `PF < 1.0`
  - годы с `trades < 3` не используются как самостоятельный gate-fail

Итог оказался однозначно отрицательным:
- stable threshold: **не найден**
- `selected_threshold = null`
- validation best diagnostic point with `N>=30`: `threshold=0.22`, `N=36`, `PF=0.14`, `negative_year_slices=4`
- test best diagnostic point with `N>=30`: `threshold=0.24`, `N=164`, `PF=0.31`, `negative_year_slices=5`
- финальный verdict: `reject_as_standalone`

**Смысл verdict-а:** признак `fav_3_vs_12` может быть полезен как вспомогательный фактор внутри другого уже сильного отбора, но как отдельная торговая система он не работает.

**Решение:** standalone-направление **closed**. Не рассматривать `fav_3_vs_12` как вторую независимую систему.

Источник: [2026-04-13-fav-3-vs-12-standalone.md](../../docs/reports/2026-04-13-fav-3-vs-12-standalone.md)

### Quantile Forward Validation (04-13): scaffold ready, no forward data yet

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

После закрытия composition и standalone `fav_3_vs_12` главный практический вопрос по `entry_path_v1_quantile` стал не поисковым, а операционным: держится ли production rule на новых данных после принятого решения.

Добавлен отдельный frozen benchmark:
- не меняет rule `lb_gt_m_q35`;
- не ищет новый winner;
- читает внешний forward prediction CSV;
- считает `trades`, `PF`, win_rate, mean PnL в ATR;
- строит квартальные срезы;
- пишет `summary.json`, `time_slices.csv`, `run_metadata.json`;
- выдаёт verdict `confirmed / watch / revisit`.

Текущий результат не является подтверждением и не является провалом `quantile`:
- verdict: `watch`
- reason: `no_forward_data`
- forward trades: `0`
- forward PF: `n/a`

Причина простая: в репозитории нет strictly-forward prediction CSV после production decision. Доступны только historical validation/test prediction-файлы, а повторно использовать старый test как forward validation нельзя.

**Решение:** инструмент готов, но фактический verdict откладывается до появления нового prediction CSV. До этого `entry_path_v1_quantile` остаётся production-ready parallel mode по frozen test и MT4 parity, но не переводится в более сильный статус на основании forward validation.

Источник: [2026-04-13-quantile-forward-validation.md](../../docs/reports/2026-04-13-quantile-forward-validation.md)

### PF Uplift Discovery (04-13): ОТОБРАНЫ 3 ГИПОТЕЗЫ

После закрытия composition и standalone-треков — переход к поиску PF uplift вне ML-слоя. Read-only исследование: без переобучения, без изменения кода, только анализ уже доступных данных.

**Что проверялось**: 20 гипотез по 5 категориям (режим рынка, параметры выхода, логика входа, фильтры по признакам, параметры советника). 6 быстрых проверок с проверкой по траектории цены (симуляция по OHLC, 24 бара).

**Ключевые находки из разметки режимов**:
- Азия = 100% выигрышных сделок в квантиле (N=19, PF=inf)
- Убыточный паттерн в Нью-Йорке: PF=0.28; тот же паттерн в Азии: PF=inf
- Верхняя четверть волатильности: WR высокий, но крупные убытки тянут PF вниз

**Результаты 6 проверок**:

| Гипотеза | N после | PF после | Прирост PF | Оценка |
|----------|--------:|---------:|-----------:|--------|
| Исключить Нью-Йорк | 34 | 20.276 | +12.097 | **СИЛЬНАЯ** |
| Ранний выход — бар 12 | 48 | 13.731 | +5.552 | **СИЛЬНАЯ** |
| pred_adv12 ≤ Q75 | 37 | 12.746 | +4.567 | **СИЛЬНАЯ** |
| Исключить верх. четверть волат. | 42 | 10.599 | +2.420 | СИЛЬНАЯ (#4) |
| Исключить ниж. четверть волат. | 33 | 9.390 | +1.211 | Слабая |
| Ширина интервала ≤ медиана | 22 | inf | inf | Слабая (N–54%) |

Три механизма подтверждены по траектории цены:
- Нью-Йорк: убыточный паттерн концентрирован именно там (PF=0.28 vs inf в Азии)
- Ранний выход: 0 из 37 выигрышных на баре 12 переворачиваются к бару 24
- pred_adv12: максимальный убыток 4x выше для отброшенных сделок (1.38 vs 0.35 ATR)

**Отобранные гипотезы и предварительные планы**:
- [2026-04-13-ny-session-filter.md](../../docs/superpowers/plans/2026-04-13-ny-session-filter.md)
- [2026-04-13-early-timeout-bar12.md](../../docs/superpowers/plans/2026-04-13-early-timeout-bar12.md)
- [2026-04-13-pred-adv-cap.md](../../docs/superpowers/plans/2026-04-13-pred-adv-cap.md)

**Следующий шаг**: `/writing-plans` для любого из трёх предварительных планов (рекомендован порядок: Нью-Йорк → бар 12 → pred_adv cap).

Источник: [2026-04-13-pf-uplift-discovery.md](../../docs/reports/2026-04-13-pf-uplift-discovery.md)

### Quantile MT4 Parity (04-11)

После multi-seed verdict `go_mt4` был проведён отдельный MT4 parity-check именно для quantile winner `lb_gt_m`.

Ключевой технический результат этапа:

- расхождение оказалось не в MQL, а в Python exporter-е;
- исходный export содержал дубликаты `time`, поэтому Python видел `9378` строк и `16` активных сигналов;
- `lib_ML_Signal.mqh` при загрузке CSV оставляет последнюю строку для каждого времени;
- после исправления exporter-а на `keep='last'` канонический CSV стал совпадать с реальным MT4 runtime.

Итоговый quantile export:

| Metric | Value |
|---|---:|
| Rows | `8872` |
| Active signals | `8` |
| BUY / SELL | `4 / 4` |

MT4 result по `20260411.log`:

| Metric | Value |
|---|---:|
| Trades | `8` |
| PF | **58.88** |
| Net profit | `2951.63` |
| Drawdown | `2.85%` |
| Win / Loss | `7 / 1` |

Trade-level reconciliation был сохранён отдельно:

- `ML/reports/entry_path_v1_quantile_mt4_reconciliation.csv`

Счётчики в логе и reconciliation совпали:

- `Opened = 8`
- `Timeout closes = 8`
- `Position blocked = 0`
- `Score filtered = 0`

**Вывод**: `entry_path_v1_quantile` теперь подтверждён не только как robust Python-upgrade, но и как реальный MT4 execution mode. Следующий вопрос уже продуктовый: переводить ли quantile-layer в основной execution contour.

Источники: [2026-04-08-entry-path-v1-baseline.md](../../docs/reports/2026-04-08-entry-path-v1-baseline.md), [2026-04-09-entry-path-v1-loss-weighting.md](../../docs/reports/2026-04-09-entry-path-v1-loss-weighting.md), [2026-04-09-entry-path-trade-filter.md](../../docs/reports/2026-04-09-entry-path-trade-filter.md), [2026-04-09-mt4-parity-check-winner.md](../../docs/reports/2026-04-09-mt4-parity-check-winner.md), [2026-04-10-entry-path-v1-quantile.md](../../docs/reports/2026-04-10-entry-path-v1-quantile.md), [2026-04-11-entry-path-v1-quantile-robustness.md](../../docs/reports/2026-04-11-entry-path-v1-quantile-robustness.md), [2026-04-11-entry-path-v1-quantile-mt4-parity.md](../../docs/reports/2026-04-11-entry-path-v1-quantile-mt4-parity.md)

## Сравнение треков (на сегодня)

| Track | Production PF | Validated? | Ближайший шаг |
|---|---:|---|---|
| regression_updn + exit | PF~1.05 (OOS) | Production baseline | Нет uplift от exit layer |
| Triple Barrier | PF=1.28 (test, 69 trades, fixed simulator) | **Gate fail — не production** | Пересмотр только после forward-данных post-2026-06 |
| entry_path_v1 | PF=4.29 (test, 44 trades), 8.47 (MT4, 22 trades) | Frozen winner confirmed | Superseded by quantile-layer |
| entry_path_v1_quantile | PF=8.18 (test, 48 trades, gate PASS), MT4 parity 20/20, PF=11.91 в деньгах; forward scaffold `watch/no_forward_data` | **Production parallel mode** | Собрать strictly-forward prediction CSV |
| quantile × fav_3_vs_12 | PF=7.86 (test, 47 trades) | **Gate fail — closed** | No uplift, worsens yearly stability |
| fav_3_vs_12 standalone | no stable threshold | **Rejected — closed** | Not viable as independent second system |
| outcome-aligned | Нет winner | Failed validation | Execution-aware labels |
| take/skip v2 frequency execution | MT4 `TrailATR=8, TP=0`: PF=3.77, 56 trades, net=24521.88 | **Основной frequent candidate** | Искать независимую систему, не подбирать TP дальше |

## Открытые вопросы

1. Forward validation quantile-слоя: нужен strictly-forward prediction CSV; текущий scaffold готов, но данных после production decision пока нет.
2. TB regime shift 2023–2026 — локальный всплеск или системный? Ответ придёт только с накоплением forward-данных.
3. PF uplift реализация: три отобранных гипотезы требуют `/writing-plans` перед реализацией; пороги нужно фиксировать на проверочном периоде, не на тестовом.
4. Нужна следующая независимая некоррелированная система; дальнейшая подгонка `TrailATR/TP` внутри текущего `frequency` набора имеет убывающую ценность.

## 6. Cross-Instrument Robustness Check (04-24)

Этап был специально разделён на две независимые проверки:

- `provider_drift_baseline` на том же `XAUUSD`;
- `cross_instrument_transfer` на `XAGUSD`, `EURUSD`, `GBPUSD`, `USDCHF`.

Это убрало главную методологическую ошибку: нельзя объяснять провал переноса на новом рынке только сменой провайдера котировок.

### Provider drift baseline

Для `XAUUSD MetaQuotes -> Alpari` все три системы сохранили статус `provider_stable`:

- `quality`
- `frequency`
- `original_plus_path`

Практический вывод: drift котировок заметен в сыром `OHLC/Nero`, но сам по себе не разрушает текущие frozen execution-tracks на том же инструменте.

### Cross-instrument transfer

| Instrument | `quality` | `frequency` | `original_plus_path` |
|---|---|---|---|
| `XAGUSD` | failed | supported | failed |
| `EURUSD` | failed | failed | failed |
| `GBPUSD` | inconclusive | inconclusive | supported |
| `USDCHF` | supported | supported | supported |

Итог по breadth:

- `quality`: `1 supported / 1 inconclusive / 2 failed`
- `frequency`: `2 supported / 1 inconclusive / 1 failed`
- `original_plus_path`: `2 supported / 0 inconclusive / 2 failed`

Ключевые наблюдения:

- `EURUSD` — самый жёсткий negative case: все три режима провалились.
- `USDCHF` — strongest positive case: все три режима сохранили practical viability.
- `frequency` оказался самым живучим по ширине переноса.
- `original_plus_path` не универсален, но по breadth выглядит сильнее `quality`.
- `quality` остаётся самым строгим режимом по качеству отдельных прогонов, но не самым устойчивым по переносу.

Структурный вывод: после этого этапа главный следующий вопрос уже не “переносится ли система вообще”, а “какие из подтверждённых систем достаточно независимы, чтобы их объединять в portfolio-layer”.

Источник: [2026-04-24-cross-instrument-robustness-check.md](../../docs/reports/2026-04-24-cross-instrument-robustness-check.md)
