---
last_updated: 2026-05-21
sources: 3
status: active
---

# Execution Tracks: Reconciliation + Candidate-Source Audit (05-12 — 05-15)

## 18. Online/Tester Execution Reconciliation (05-12)

M5 diagnostic-прогон проверял механику `MT4 -> ML -> MT4`, а не прибыльность
стратегии. Online и tester `ml_signals.csv` совпали: сигнальный слой
воспроизводится, расхождение возникло на этапе исполнения сделок в MT4.

Стабильный закрытый срез `2026.05.12 00:10` - `2026.05.12 13:05`:

| Metric | Online | Tester |
|---|---:|---:|
| closed trades | 67 | 68 |
| PnL | -680.2 | -522.6 |
| E[PnL] per closed trade | -10.1522 | -7.6853 |

На общей исполнимой части online пропустил 6 входов против tester. Первые три
пропуска подтверждены в MT4-логе как `requote ERROR-138`. В парных 65 закрытых
сделках разница матожидания была небольшой: online `-11.4615`, tester
`-10.7185`, delta `-0.7431`.

Вывод: главный вред старого прогона дали пропущенные online-входы, а не PnL
расхождение по уже открытым парным сделкам. Для следующих прогонов нужно
использовать append-only `ml_signals.csv`, event-log с `OPEN_FAILED` и запускать
`ML.online_tester_reconciliation` с явными `--start-time` / `--end-time`.
Инструкция по инструменту живёт в
[docs/ML/online_tester_reconciliation.py.md](../../docs/ML/online_tester_reconciliation.py.md);
отчёты должны фиксировать только конкретные результаты прогонов.

Источник: [2026-05-12-online-tester-execution-reconciliation.md](../../docs/reports/2026-05-12-online-tester-execution-reconciliation.md)

## 19. Entry Path Candidate-Source Audit (05-14)

После online watcher проверки обнаружен разрыв уровнем выше model inputs:
`entry_path_v1_live_safe` не использует future-derived признаки в `X`, но export
по-прежнему требует `signal != 0`. В offline этот `signal` приходит из
`label_all()`, а в live raw `Nero.csv` равен нулю.

Первый ablation отделил offline candidate universe от ML score:

| Mode | Trades | PF | Sequential trades | Sequential PF |
|---|---:|---:|---:|---:|
| `signal_only` | 486 | 0.1757 | 237 | 0.1696 |
| `current_score_gate` | 41 | 7.5737 | 27 | 5.9352 |

Вывод: offline `signal != 0` сам по себе убыточен; положительный вклад даёт
score-фильтр модели. Но этот score всё ещё применяется поверх недоступного live
candidate-source.

Затем проверен all-rows ranking без offline gate:

| Check | Trades | PF | Win rate | Mean pnl ATR |
|---|---:|---:|---:|---:|
| validation winner, 5% coverage | 471 | 0.9661 | 47.77% | -0.0503 |
| frozen test | 329 | 0.9134 | 46.20% | -0.1275 |
| frozen test sequential | 133 | 0.5908 | 40.60% | -0.6768 |

Вывод: просто снять `signal != 0` gate и брать направление из
`fractal0.direction` нельзя. Текущий `pred_ret_24_dir_atr` не переносится на
all-rows universe без новой постановки обучения. Следующая проверка - causal
surrogate для `label_all().signal`.

Источник: [2026-05-14-entry-path-all-rows-ranking.md](../../docs/reports/2026-05-14-entry-path-all-rows-ranking.md)

Causal surrogate проверил, можно ли приблизить `label_all().signal` только по
текущим live-safe PIC-состояниям, без будущих строк:

| Check | Trades | PF | Win rate | Mean pnl ATR |
|---|---:|---:|---:|---:|
| validation winner, prob >= 0.50 | 43 | 1.0507 | 53.49% | 0.0753 |
| frozen test | 36 | 1.1537 | 58.33% | 0.2319 |
| frozen test sequential | 31 | 1.4111 | 64.52% | 0.5854 |

Качество приближения слабое: на test active precision только 20.41%, но recall
89.09%, direction accuracy на true-active строках 89.09%. Вывод: направление и
часть candidate-source можно восстановить причинно, но точность кандидатов пока
низкая; это исследовательский baseline, не production-rule.

Источник: [2026-05-14-entry-path-causal-surrogate.md](../../docs/reports/2026-05-14-entry-path-causal-surrogate.md)

Direct bar model проверил постановку, где модель сама выбирает `BUY`, `SELL`
или `SKIP` для каждого бара. Обучающая цель строилась по будущей OHLC-доходности
от следующего бара до close через 24 бара; offline `signal` не использовался как
gate.

| Check | Trades | PF | Win rate | Mean pnl ATR |
|---|---:|---:|---:|---:|
| validation winner, prob >= 0.80 | 1450 | 1.1673 | 51.17% | 0.2392 |
| frozen test | 1277 | 1.1141 | 48.24% | 0.1631 |
| frozen test sequential | 274 | 1.1334 | 45.26% | 0.1660 |

Вывод: direct score+direction лучше all-rows ranking и не зависит от offline
`signal != 0`. Но результат пока слабый: test PF `1.1141`, 2022 год
отрицательный, correct signal precision на test `45.50%`. Это направление для
следующего retrain, не готовая production-rule.

Источник: [2026-05-14-entry-path-direct-bar-model.md](../../docs/reports/2026-05-14-entry-path-direct-bar-model.md)

## 20. Direct Direction Improvement (05-15)

Следующая итерация проверяла, можно ли улучшить direct-direction постановку
после слабого 3-class `SELL/SKIP/BUY` результата. Главный методологический
вывод: проблема была не только в признаках, а в самой 3-class формулировке.

Validation experiments:

| Experiment | Best PF | Best sequential PF | Verdict |
|---|---:|---:|---|
| k variants / geometry-only | 1.03-1.11 | 0.82-1.15 | gate fail |
| binary RF BUY/SELL margin=0.10 | 1.25 | 1.30 | gate pass |
| HGB / LR 3-class | 1.01-1.05 | 0.83-1.05 | gate fail |
| zone features | 1.04-1.08 | 0.87 | gate fail |
| score-filtered direction | 1.09 | 1.16 | gate fail |

Frozen test для validation-winner `Binary RF buy=0.4, sell=0.6,
margin=0.10`:

| Metric | Value |
|---|---:|
| test PF | 1.226 |
| sequential PF | 1.537 |
| trades | 2045 |
| BUY PF | 1.904 |
| SELL PF | 0.618 |
| negative years | 2 |

Вывод: binary BUY/SELL заметно лучше 3-class и превосходит all-rows,
surrogate и direct-bar baselines. Но это ещё не production-доказательство:
SELL сторона убыточна, два года test отрицательные, а frozen test был выполнен
для одной выбранной конфигурации. Следующие решения должны рассматривать
BUY-only или отдельный SELL-фильтр как новые кандидаты, а не как post-test
подкрутку текущего результата.

Источник: [2026-05-15-direct-direction-improvement.md](../../docs/reports/2026-05-15-direct-direction-improvement.md)
