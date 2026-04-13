---
last_updated: 2026-04-13
sources: 15
status: active
---

# Execution Tracks: Exit Policy, Outcome-Aligned, Triple Barrier, Entry Path v1

> Синтез 13 отчётов (2026-04-08 — 2026-04-12). Параллельные направления execution.

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
- `trades_lost_from_quantile = 1`
- composition почти ничего не отрезает, но получает один отрицательный годовой срез:
  - `2023`: `N=5`, `PF=0.475`
- итоговый `n_boost_composition.verdict = gate_fail`

**Смысл verdict-а:** composition теперь отклонён не из-за отсутствия данных, а по существу. Фильтр `fav_3_vs_12` поверх quantile почти не меняет набор сделок, но ухудшает yearly stability.

**Решение:** направление composition **closed**. Практической пользы сверх `entry_path_v1_quantile` не найдено.

Источник: [2026-04-13-quantile-fav-composition.md](../../docs/reports/2026-04-13-quantile-fav-composition.md)

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
| entry_path_v1_quantile | PF=8.18 (test, 48 trades, gate PASS), MT4 parity 20/20, PF=11.91 в деньгах | **Production parallel mode** | Forward validation post-2026-04 |
| quantile × fav_3_vs_12 | PF=7.86 (test, 47 trades) | **Gate fail — closed** | No uplift, worsens yearly stability |
| fav_3_vs_12 standalone | no stable threshold | **Rejected — closed** | Not viable as independent second system |
| outcome-aligned | Нет winner | Failed validation | Execution-aware labels |

## Открытые вопросы

1. Forward validation quantile-слоя: когда набирётся достаточная выборка (~10–15 сделок) для пересмотра статуса "parallel → primary"?
2. TB regime shift 2023–2026 — локальный всплеск или системный? Ответ придёт только с накоплением forward-данных.
