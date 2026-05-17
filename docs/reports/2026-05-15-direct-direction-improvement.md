# Direct Direction Improvement: Iterative Experiments E0–E5

> **Date**: 2026-05-15
> **Status**: Completed
> **Goal**: Итеративно улучшить fractal-level SELL/SKIP/BUY direct-direction модель, которая не проходит validation gate (лучшая PF=1.11 < 1.15), тестируя binary модели, альтернативные ML алгоритмы, zone features, tighter targets и score-filtered direction.
> **Related plan**: `docs/superpowers/plans/2026-05-15-improving-direct-direction-results.md`
> **Related commit**: pending

## Context

Предыдущий этап (entry-path-fractal-level-direct-direction) установил, что 3-class SELL/SKIP/BUY на fractal-level признаках с RandomForest не даёт торгового преимущества: лучшая конфигурация D_nearest_k4 даёт PF=1.11, SELL PF=0.99, что ниже gate PF≥1.15. Все три target family (A/C/D) показывают вероятности BUY/SELL ≈ 1/3 (едва выше random).

## What Was Done

### Experiment 0: Feature Ablation

Проверка гипотезы: «Проблема в признаках или цели, а не в модели». Запущены варианты nearest_k с k=4/6/8/16 и k=4 geometry_only (без up_*/dn_* полей).

**Результаты (Target D, RandomForest, threshold [0.10–0.40]):**

| Variant | Features | Best PF | Best Seq PF | Trades | BUY PF | SELL PF |
|---------|----------|---------|-------------|--------|--------|---------|
| k=4 baseline | 97 | 1.11 | 1.15 | 9415 | 1.31 | 0.99 |
| k=6 | 143 | 1.03 | 0.82 | 9264 | 1.20 | 0.94 |
| k=8 | 189 | 1.05 | 1.03 | 9251 | 1.21 | 0.94 |
| k=16 | 373 | 1.08 | 1.12 | 9221 | 1.29 | 0.97 |
| k=4 geom_only | 57 | 1.07 | 1.15 | 9247 | 1.23 | 0.96 |

**Диагностические ответы:**
1. Увеличение k ухудшает PF — больше признаков добавляют шум, а не сигнал.
2. up_/dn_ поля дают маргинальный вклад (~0.04 PF). Удаление их почти не влияет.
3. `fractal0_direction` не входит в top-20 ни одного варианта. Топ-признаки: front, back, impulse. Сигнал распределён, но слаб.

### Experiment 1: Binary BUY/SELL Models

Две независимые бинарных модели (BUY-vs-REST, SELL-vs-REST) с порогом и margin rule. Цель — лучше разделить direction от skip.

**Результаты (сбалансированные конфигурации, BUY/SELL balance ≥ 0.20):**

| Config | Model | BUY thr | SELL thr | Margin | Trades | PF | Seq PF | BUY PF | SELL PF | Balance | Neg Yrs |
|--------|-------|---------|----------|--------|--------|------|--------|--------|---------|---------|---------|
| rf_buy0.40_sell0.60_m0.10 | RF | 0.4 | 0.6 | 0.10 | 1923 | 1.25 | 1.30 | 1.32 | 1.21 | 0.37 | 0 |
| rf_buy0.60_sell0.60_m0.10 | RF | 0.6 | 0.6 | 0.10 | 1828 | 1.26 | 1.19 | 1.34 | 1.21 | 0.34 | 0 |
| hgb_buy0.50_sell0.50_m0.00 | HGB | 0.5 | 0.5 | 0.00 | 5182 | 1.16 | 1.40 | 1.40 | 1.02 | 0.38 | 0 |

**Несбалансированные конфигурации HGB:**

| Config | Trades | PF | Seq PF | BUY PF | SELL PF | Balance |
|--------|--------|------|--------|--------|---------|---------|
| hgb_buy0.30_sell0.60_m0.05 | 1931 | 1.38 | 1.29 | 1.36 | 1.54 | 0.09 |

**Ключевой вывод:** Binary модели существенно превосходят 3-class. Лучший сбалансированный результат — RF margin=0.10: PF=1.25, SeqPF=1.30, 0 отрицательных лет, проходит validation gate. HGB создаёт skew-сигналы (91% BUY).

### Experiment 2: HGB + LR 3-Class Model

Проверка: улучшит ли HistGradientBoosting или LogisticRegression 3-class формулировку?

| Model | Best PF | Best Seq PF | Trades | Notes |
|-------|---------|-------------|--------|-------|
| RF baseline | 1.11 | 1.15 | 9415 | Приthreshold=0.10 |
| HGB | 1.01 | 1.05 | 3294 | Хуже RF |
| LR | 1.05 | 0.83 | 9415 | Хуже при низких thresholds |
| LR@0.40 | 1.11 | 1.23 | 1091 | Сравним при высоких |

**Вывод:** HGB хуже RF для 3-class. LR сравним только при высоких thresholds, где нелинейные взаимодействия менее важны. Сигнал частично линеен, но RF извлекает больше.

### Experiment 3: Zone Features

Проверка: даёт ли агрегация фракталов по ценовым зонам лучшую структуру, чем proximity?

| Input Family | Features | Best PF | Best Seq PF |
|-------------|----------|---------|-------------|
| nearest_k4 (baseline) | 97 | 1.11 | 1.15 |
| zones | 127 | 1.08 | 0.87 |
| zones+nearest_k4 | 221 | 1.04 | 0.87 |

**Вывод:** Zone features хуже nearest_k4. Zones+k4 комбинированный хуже каждого по отдельности — зоны добавляют шум, а не сигнал. Агрегация по зонам теряет информацию о близости.

### Experiment 4: Target Parameter Grid

**Пропущен.** Все 3-class конфигурации стабильно ниже gate (PF < 1.15). Разные параметры таргетов не решат фундаментальную проблему 3-class формулировки.

### Experiment 5: Score-Filtered Direction

HGB binary BUY-vs-SELL на universe `score >= threshold` (те же ~6174 строки, что и production entry_path_v1_live_safe).

| Config | Mode | Trades | PF | Seq PF | BUY PF | SELL PF |
|--------|------|--------|------|--------|--------|---------|
| thr=0.30 | standalone | 6127 | 1.08 | 1.07 | 1.29 | 0.96 |
| thr=0.40 | standalone | 5510 | 1.09 | 1.16 | 1.29 | 0.95 |
| thr=0.50 | standalone | 2402 | 1.29 | 1.06 | 1.29 | 0.00 |
| thr=0.60 | standalone | 435 | 1.16 | 1.21 | 1.16 | 0.00 |
| thr=0.30 | fractal0_diagnostic | 6174 | 0.98 | 0.99 | 1.09 | 0.86 |

**Вывод:** HGB direction resolver улучшает над `fractal0.direction` baseline (PF=1.09 vs 0.98), но не достигает PF=1.15. При threshold≥0.50 SELL сигналы исчезают.

### Frozen Test

**Конфигурация:** Binary RF, buy_threshold=0.4, sell_threshold=0.6, margin=0.10

Перетренирована на train+validation (53,349 строк), оценена на test.

| Metric | Value |
|--------|-------|
| **Test PF** | **1.226** |
| **Test Seq PF** | **1.537** |
| Test Trades | 2045 (1202 BUY / 843 SELL) |
| BUY PF | 1.904 |
| SELL PF | 0.618 |
| BUY Win Rate | 52.7% |
| SELL Win Rate | 40.7% |
| BUY/SELL Balance | 0.41 |
| Negative Years | 2 (2022: PF=0.35, 2023: PF=0.94) |

| Year | Trades | PF |
|------|--------|------|
| 2022 | 92 | 0.35 |
| 2023 | 512 | 0.94 |
| 2024 | 600 | 1.31 |
| 2025 | 620 | 1.48 |
| 2026 | 221 | 2.43 |

**Сравнение с baselines:**

| Baseline | Test PF | Seq PF | Trades / seq |
|----------|---------|--------|-------------|
| all-rows ranking | 0.9134 | 0.5908 | 329 / 133 |
| causal surrogate | 1.1537 | 1.4111 | 36 / 31 |
| direct bar model | 1.1141 | 1.1334 | 1277 / 274 |
| **binary RF (new)** | **1.2260** | **1.5374** | **2045 / 330** |

## Changed Files

- `ML/fractal_level_feature_builder.py` — добавлена поддержка geometry_only, zones, zones_plus_nearest_k input_family
- `ML/benchmark_entry_path_fractal_level_direct_direction.py` — добавлены --k, --geometry-only, --model (rf/hgb/lr), --input-family, --e0-grid
- `ML/benchmark_entry_path_binary_direction.py` — новый файл, binary BUY/SELL benchmark с RF и HGB, threshold/margin grid, frozen-test stage
- `ML/benchmark_entry_path_score_direction.py` — новый файл, score-filtered direction resolver
- `tests/test_fractal_level_feature_builder.py` — тесты для k variants, geometry_only, zones
- `tests/test_benchmark_entry_path_binary_direction.py` — новый файл, binary signal logic тесты

Артефакты:
- `ML/reports/entry_path_v1_nearest_k6/` — E0b
- `ML/reports/entry_path_v1_nearest_k8/` — E0c
- `ML/reports/entry_path_v1_nearest_k16/` — E0d
- `ML/reports/entry_path_v1_nearest_k4_geometry_only/` — E0e
- `ML/reports/entry_path_v1_binary_direction/` — E1 + frozen test
- `ML/reports/entry_path_v1_nearest_k4_hgb/` — E2 HGB
- `ML/reports/entry_path_v1_nearest_k4_lr/` — E2 LR
- `ML/reports/entry_path_v1_zones/` — E3 zones
- `ML/reports/entry_path_v1_zones_plus_nearest_k4/` — E3 zones+k4
- `ML/reports/entry_path_v1_score_direction/` — E5

## Verification

```bash
./.venv/bin/python -m pytest tests/test_fractal_level_feature_builder.py tests/test_benchmark_entry_path_fractal_level_direct_direction.py tests/test_benchmark_entry_path_binary_direction.py -v   # 22 passed
```

## Results Summary

| Experiment | Best PF | Best Seq PF | Trades | Passes Gate? |
|-----------|---------|-------------|--------|--------------|
| E0a k=4 baseline (3-class RF) | 1.11 | 1.15 | 9415 | No (PF<1.15) |
| E0b-e k variants / geometry_only | 1.03–1.08 | 0.82–1.15 | 9247–9415 | No |
| **E1 Binary RF margin=0.10** | **1.25** | **1.30** | **1923** | **Yes** |
| E1 Binary HGB (one-sided) | 1.38 | 1.29 | 1931 | No (unbalanced) |
| E2 HGB 3-class | 1.01 | 1.05 | 3294 | No |
| E2 LR 3-class | 1.05 | 0.83 | 9415 | No |
| E3 Zones | 1.08 | 0.87 | 2469 | No |
| E3 Zones+k4 | 1.04 | 0.87 | 9293 | No |
| E5 Score direction HGB | 1.09 | 1.16 | 5510 | No (PF<1.15) |

**Frozen test winner:** Binary RF buy=0.4, sell=0.6, margin=0.10 → Test PF=1.226, SeqPF=1.537.

## Conclusions

1. **3-class формулировка SELL/SKIP/BUY нежизнеспособна** — ни один вариант (RF, HGB, LR, зоны, target family) не достиг PF≥1.15. Проблема в разделении трёх классов, а не в признаках или модели.

2. **Binary BUY/SELL модели радикально лучше** — RF с margin rule достигает PF=1.25 на validation и PF=1.23 на test. Это лучший результат среди всех протестированных конфигураций.

3. **SELL направление слабое** — SELL PF=0.62 на test. Это означает, что модель уверенно предсказывает BUY (PF=1.90), но не SELL. Возможные причины: структурная асимметрия рынка (uptrend bias), недостаток SELL-примеров в обучении.

4. **Feature engineering не помог** —_zones, увеличенное k, geometry_only — все хужe baseline k=4. Сигнал слабо связан с пространственной структурой фракталов.

5. **HGB не лучше RF для этой задачи** — ни в 3-class (PF=1.01 vs 1.11), ни в binary (создаёт skew-сигналы с 91% BUY).

6. **Score-filtered direction лучше fractal0.direction** (PF=1.09 vs 0.98), но не достигает gate порога standalone.

## Limitations / Open Questions

1. **SELL PF=0.62 на test** — основной риск. Модель теряет деньги на SELL-трейдах. Возможные решения: (a) использовать только BUY-сигнал, (b) фильтровать SELL более агрессивным threshold, (c) совместить с каузальным суррогатом для SELL.

2. **2 отрицательных года на тесте** (2022, 2023). 2022 год особенно слаб (PF=0.35, 92 сделки). Вероятно, модель не адаптирована к низковолатильным периодам.

3. **Одна тестовая конфигурация** — frozen test прогнан только для одного набора гиперпараметров. Другие конфигурации E1 (HGB, другие thresholds/margins) не тестировались на test.

4. **E4 (Target Grid) пропущен** — не проверялись альтернативные параметры Target A/C/D.

5. **E6 (Sequence Features) не проводился** — условный эксперимент (требовался PF 1.05–1.15 от E0–E3), не актуален после успеха E1.

## Next Step

- Рассмотреть BUY-only торговую стратегию как production кандидат (BUY PF=1.90 на test).
- Исследовать фильтрацию SELL сигналов через более высокий sell_threshold или дополнительный SELL score filter.
- Подготовить MT4 parity для binary модели.

## Related Materials

- `docs/superpowers/plans/2026-05-15-improving-direct-direction-results.md`
- `ML/reports/entry_path_v1_direct_direction_improvement/aggregate_summary.md`
- `ML/reports/entry_path_v1_binary_direction/frozen_test.json`
- `CONTEXT_HANDOFF.md`