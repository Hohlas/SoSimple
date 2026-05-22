---
last_updated: 2026-05-21
sources: 40
status: active
---

# Execution Tracks: Overview

> Синтез 40 отчётов (2026-04-08 — 2026-05-15). Параллельные направления execution, live-safe аудит прибыльных ML-систем, MT4 parity, online/tester diagnostic-сверка, candidate-source audit и direct-direction улучшения.

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
5. Direct-direction binary RF улучшил all-rows/direct-bar baselines, но SELL PF=0.62 и два отрицательных года блокируют production verdict без отдельного BUY-only или SELL-filter follow-up.

## Содержание (подстраницы)

Этот файл — обзорная страница. Детали по каждому направлению — в подстраницах:

| Подстраница | Секции | Отчётов |
|-------------|--------|---------|
| [execution-tracks-early-research.md](execution-tracks-early-research.md) | §1 Exit Policy, §2 Outcome-Aligned, §3 Triple Barrier | 4 |
| [execution-tracks-entry-path-v1.md](execution-tracks-entry-path-v1.md) | §4 Entry Path v1 + quantile + cross-instrument + PF uplift | 14 |
| [execution-tracks-take-skip-v2.md](execution-tracks-take-skip-v2.md) | §5 Take/Skip v2 + trailing stop + execution policy | 8 |
| [execution-tracks-robustness-plus-portfolio.md](execution-tracks-robustness-plus-portfolio.md) | §6 Cross-Instrument, §7 Portfolio | 2 |
| [execution-tracks-telemetry-plus-mql.md](execution-tracks-telemetry-plus-mql.md) | §8 Telemetry, §9 MQL Runtime | 2 |
| [execution-tracks-live-safe-audit.md](execution-tracks-live-safe-audit.md) | §10-13 Live-Safe Audit + Retrain | 4 |
| [execution-tracks-reproducibility-plus-parity.md](execution-tracks-reproducibility-plus-parity.md) | §14-17 Reproducibility + MT4 Parity | 4 |
| [execution-tracks-reconciliation-plus-audit.md](execution-tracks-reconciliation-plus-audit.md) | §18-20 Reconciliation + Candidate-Source + Direct Direction | 3 |
