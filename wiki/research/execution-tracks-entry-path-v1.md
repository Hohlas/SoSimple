---
last_updated: 2026-05-14
sources: 14
status: active
---

# Execution Tracks: Entry Path v1 + Quantile (04-08 — 04-24)

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

### Entry Path Cross-Instrument Robustness (04-24)

Следующий stress-test после `quality/frequency/original_plus_path` был уже не про `take_skip`, а про две зрелые `entry_path` execution-системы:

- `entry_path_v1`
- `entry_path_v1_quantile`

Методология была сохранена жёстко:

- без retraining;
- без новых thresholds;
- без изменения frozen rules;
- сначала `provider drift baseline` на `XAUUSD MetaQuotes -> Alpari`;
- потом `cross-instrument transfer` на `EURUSD/GBPUSD/USDCHF/XAGUSD`;
- verdict для drift и transfer считаются отдельно.

Для этого пришлось зафиксировать реальный execution protocol `entry_path` систем и переиспользовать его в benchmark как `hold_24_backstop_50`:

- вход на следующем баре;
- `ML_HoldBars=24`;
- `ML_BackStopATR=50`;
- без reversal-close.

Дополнительно были добавлены два operational модуля:

- `API/export_entry_path_v1_signals.py` — frozen baseline rule -> единый `time;signal`;
- `ML/export_entry_path_predictions.py` — inference frozen `entry_path_v1` и `entry_path_v1_quantile` на arbitrary labeled CSV.

#### Provider drift

На том же `XAUUSD` новый провайдер не сломал обе системы:

| System | Trades | PF | Max DD ATR | Verdict |
|---|---:|---:|---:|---|
| `entry_path_v1` | 27 | 25.02 | 1.63 | `provider_stable` |
| `entry_path_v1_quantile` | 10 | `inf` | 0.00 | `provider_stable` |

Это важный отрицательный результат: сам по себе drift котировок не объясняет будущие провалы переноса на новые рынки.

#### Cross-instrument transfer

| Instrument | `entry_path_v1` | `entry_path_v1_quantile` |
|---|---|---|
| `EURUSD` | `transfer_failed` | `transfer_failed` |
| `GBPUSD` | `transfer_failed` | `transfer_failed` |
| `USDCHF` | `transfer_failed` | `transfer_supported` |
| `XAGUSD` | `transfer_supported` | `transfer_supported` |

Breadth by system:

| System | supported | failed |
|---|---:|---:|
| `entry_path_v1` | 1 | 3 |
| `entry_path_v1_quantile` | 2 | 2 |

Практический вывод по линии:

- baseline `entry_path_v1` переносится узко;
- quantile-версия живучее baseline и удерживает два supported-case;
- `XAGUSD` стал лучшим общим positive case для обеих систем;
- `EURUSD` и `GBPUSD` дали общий отрицательный сигнал;
- separation `provider drift` vs `transfer` оказался методологически правильным и для `entry_path` трека.

Источник: [2026-04-24-entry-path-cross-instrument-robustness.md](../../docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md)

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
