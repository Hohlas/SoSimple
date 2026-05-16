---
last_updated: 2026-05-14
sources: 4
status: active
---

# Execution Tracks: Reproducibility + MT4 Parity (05-07)

## 14. CPU/GPU Reproducibility (05-07)

После исправления нормализации `predict -> front/back` возник вопрос, почему
один и тот же seed даёт разные checkpoint и разные верхние сделки на CPU и GPU.

Проверка показала две разные проблемы:

| Area | Result |
|---|---|
| initial weights | CPU и GPU одинаковые (`max_diff=0`) |
| eval forward without dropout | отличие около `1e-7`, практически ноль |
| train forward with dropout | отличие большое: dropout создаёт разные маски |
| full training without dropout | малые отличия матричных операций накапливаются до `~0.2` в весах |
| deterministic algorithms | помогают внутри одного устройства, но не делают CPU и GPU одинаковыми |
| same CPU-trained checkpoint inference on CPU/GPU | top-5% overlap `100%`, correlation `1.0` |

Вывод: проблема не в применении готовой модели, а в обучении. Production
retrain должен быть CPU-only. GPU можно использовать для research или для
inference готового CPU-trained checkpoint, если нужен быстрый расчёт.

Источник: [2026-05-07-cpu-gpu-reproducibility.md](../../docs/reports/2026-05-07-cpu-gpu-reproducibility.md)

## 15. Entry Path v1 Live-Safe Reproducibility (05-07)

После исправления нормализации без `predict` в пуле `front/back` первый
провал retrain (`ret_pearson_r ~= 0.004`) оказался не следствием исправления,
а ошибкой источника данных: текущий `MT/MQL4/Files/Nero.csv` содержал M5, а
`entry_path_v1` требует H1. Проверка перенесена на
`MT/MQL4/Files/Nero_XAUUSD.csv`.

Серверный CPU multi-seed (`7`, `17`, `42`, `77`, `123`) показал:

| Check | Result |
|---|---:|
| model `ret_pearson_r` range | `0.2703..0.2807` |
| auto-winner median sequential PF | 1.6183 |
| auto-winner PF > 2.0 | 1 / 5 |
| production baseline `A @ 7.5%` median sequential PF | 2.3249 |
| production baseline min sequential PF | 1.8188 |
| production baseline PF > 2.0 | 4 / 5 |
| production baseline PF <= 1.0 | 0 / 5 |

Вывод: подтверждён не автоматический выбор лучшего validation winner, а заранее
выбранный простой baseline `A @ 7.5%`. Это текущий главный live-safe кандидат.
Следующий practical gate - MT4 parity: проверить, что MT4 воспроизводит тот же
контракт входов и сигналов.

Источник: [2026-05-07-entry-path-live-safe-reproducibility.md](../../docs/reports/2026-05-07-entry-path-live-safe-reproducibility.md)

## 16. Entry Path Quantile Over CPU Baseline (05-07)

`entry_path_v1_quantile` повторно проверен поверх нового CPU baseline
`entry_path_v1_live_safe + A @ 7.5%`.

| Metric | Result |
|---|---:|
| quantile sequential PF > 2.0 | 5 / 5 seeds |
| finite sequential PF median | 5.9134 |
| sequential trades range | 3..28 |
| median sequential trades | 8 |
| same quantile rule max ratio | 2 / 5 |

Вывод: прибыльная область у quantile не исчезла, но слой всё ещё не готов в
 production. Причина простая: правило выбора нестабильно между seed, а число
сделок после фильтра слишком маленькое. Главным кандидатом остаётся plain
baseline `A @ 7.5%`; quantile - только research-only.

Источник: [2026-05-07-entry-path-quantile-cpu-baseline.md](../../docs/reports/2026-05-07-entry-path-quantile-cpu-baseline.md)

## 17. Entry Path v1 Live-Safe MT4 Parity (05-07)

Первый MT4 parity-прогон выполнен для frozen кандидата
`entry_path_v1_live_safe + A @ 7.5%`.

Проверенный период: `2022.10.28` - `2025.12.31`. Это не весь диапазон
`ml_signals.csv`, но уже покрывает 26 из 29 ненулевых сигналов.

MT4 tester:

| Metric | Result |
|---|---:|
| Expert version | `260.332` |
| Symbol/timeframe | `XAUUSD,H1` |
| Trades | 26 |
| BUY / SELL | 18 / 8 |
| Net profit | 5217.70 |
| Profit Factor | 9.03 |
| Chart mismatch errors | 0 |

Reconciliation:

| Metric | Result |
|---|---:|
| expected_signals | 26 |
| opened_trades | 26 |
| closed_trades | 26 |
| critical_mismatch_count | 0 |
| missing_close_count | 0 |

Вывод: механическая цепочка `Python rule -> ml_signals.csv -> MT4` для
проверенного периода совпадает. Осталось закрыть полный диапазон файла
сигналов: после `2025.12.31` остаются 3 BUY-сигнала в 2026 году.

Источник: [2026-05-07-entry-path-mt4-parity.md](../../docs/reports/2026-05-07-entry-path-mt4-parity.md)
