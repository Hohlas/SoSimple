---
last_updated: 2026-04-11
sources: 11
status: active
---

# Execution Tracks: Exit Policy, Outcome-Aligned, Triple Barrier, Entry Path v1

> Синтез 11 отчётов (2026-04-08 — 2026-04-11). Параллельные направления execution.

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

## 3. Triple Barrier (04-08, два отчёта)

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
| regression_updn + exit | PF~1.05 (OOS) | Production | Нет uplift от exit layer |
| Triple Barrier | PF=1.11 (test), 1.27 (MT4) | Validation-locked | Python-режим = MT4 execution |
| entry_path_v1 | PF=4.29 (test, 44 trades), 8.47 (MT4, 22 trades) | Frozen winner confirmed | Унести MT4 export path в main |
| entry_path_v1_quantile | PF=58.88 (MT4, 8 trades), median test PF=inf (5 seeds) | MT4 confirmed | Decide primary execution status |
| outcome-aligned | Нет winner | Failed validation | Execution-aware labels |

## Открытые вопросы

1. Достаточно ли текущего quantile MT4 support (`8` сделок) для перевода слоя в основной execution mode, или нужен ещё один operational confirmation run?
2. TB + MT4-matching в Python: насколько сократится разрыв 253 vs 92 trades?
3. Нужно ли объединять `entry_path_v1` / quantile-layer с фильтром `fav_3_vs_12`, или это только усложнит рабочую базу без надёжного прироста?
