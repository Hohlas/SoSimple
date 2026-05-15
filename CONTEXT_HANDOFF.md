# Context Handoff

Дата: 2026-05-15.

## Текущий этап

Завершены эксперименты E0–E5 плана `docs/superpowers/plans/2026-05-15-improving-direct-direction-results.md`.
Проведён frozen test для лучшей конфигурации.

### Результаты экспериментов

| # | Эксперимент | Best PF | Best Seq PF | Passes Gate? |
|---|------------|---------|-------------|--------------|
| E0a | k=4 baseline (3-class RF) | 1.11 | 1.15 | No |
| E0b-e | k=6/8/16, geometry_only | 1.03–1.08 | 0.82–1.15 | No |
| **E1** | **Binary RF margin=0.10** | **1.25** | **1.30** | **Yes** |
| E1 | Binary HGB (one-sided) | 1.38 | 1.29 | No |
| E2 | HGB 3-class | 1.01 | 1.05 | No |
| E2 | LR 3-class | 1.05 | 0.83 | No |
| E3 | Zones | 1.08 | 0.87 | No |
| E5 | Score direction HGB | 1.09 | 1.16 | No |

E4 (Target Grid) пропущен — 3-class формулировка стабильно ниже gate.

### Frozen Test: Binary RF buy=0.4, sell=0.6, margin=0.10

| Metric | Value |
|--------|-------|
| Test PF | 1.226 |
| Test Seq PF | 1.537 |
| Test Trades | 2045 |
| BUY PF | 1.904 |
| SELL PF | 0.618 |
| Negative Years | 2 (2022, 2023) |

**Превышает baseline direct bar model (PF=1.11, SeqPF=1.13).**
SELL направление слабое (PF=0.62). BUY сильное (PF=1.90).

## Git

Локальная ветка: `improve-direct-direction-results`.

Не трогать `AGENTS.md` без явной просьбы пользователя.

## Созданные файлы

- `ML/benchmark_entry_path_binary_direction.py` — binary BUY/SELL benchmark (E1)
- `ML/benchmark_entry_path_score_direction.py` — score-filtered direction resolver (E5)
- `ML/fractal_level_feature_builder.py` — обновлён: geometry_only, zones, zones_plus_nearest_k
- `ML/benchmark_entry_path_fractal_level_direct_direction.py` — обновлён: --k, --geometry-only, --model, --input-family, --e0-grid
- `tests/test_benchmark_entry_path_binary_direction.py`
- `tests/test_fractal_level_feature_builder.py` — обновлён

Артефакты:
- `ML/reports/entry_path_v1_binary_direction/` — E1 results + frozen test
- `ML/reports/entry_path_v1_nearest_k6/` — E0b
- `ML/reports/entry_path_v1_nearest_k8/` — E0c
- `ML/reports/entry_path_v1_nearest_k16/` — E0d
- `ML/reports/entry_path_v1_nearest_k4_geometry_only/` — E0e
- `ML/reports/entry_path_v1_nearest_k4_hgb/` — E2 HGB
- `ML/reports/entry_path_v1_nearest_k4_lr/` — E2 LR
- `ML/reports/entry_path_v1_zones/` — E3 zones
- `ML/reports/entry_path_v1_zones_plus_nearest_k4/` — E3 zones+k4
- `ML/reports/entry_path_v1_score_direction/` — E5
- `ML/reports/entry_path_v1_direct_direction_improvement/` — aggregate summaries E0–E5

## Открытые вопросы

1. **SELL направление ненадёжно** — PF=0.62 на тесте. BUY PF=1.90. Возможные решения:
   - Использовать только BUY сигнал (односторонняя торговля)
   - Фильтровать SELL более агрессивным threshold
   - Комбинировать с каузальным суррогатом для SELL

2. Production watcher `entry_path_v1_live_safe + A @ 7.5%` на M5 — не проверен.

3. Задержка входа ticket `1581716381` (65 мин) — не исследована.

4. `requote ERROR-138` — не проверена обработка в новом коде.

## Следующий шаг

После завершения всех E0–E5 и frozen test:
- Если результат принимается — написать follow-up план для MT4 паритета и confidence intervals
- Если SELL направление критично — исследовать фильтрацию SELL или односторонний BUY-only режим
- Обновить `CHANGELOG.md` и `CONTEXT_HANDOFF.md`