# fav + Brk Multi-Target Regression с ATR-коридором — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Обучить модель предсказывать (1) потенциал прибыли (fav_h) и (2) пробитость уровня фрактала (Brk_h), с ATR-коридором для фильтрации дальних фракталов. Сравнить baseline (100 фракталов) с коридорными вариантами.

**Architecture:** Multi-output модель (4 выхода: fav_6, Brk_6, fav_12, Brk_12). Сначала RF на плоских признаках (3 варианта входа), потом Transformer на тензоре с distance-маской. fav вычисляется direction-aware из up_h/dn_h / ATR. Brk вычисляется из накопленного поля `break` фрактала через h баров (подход label_updn). fav — регрессия, Brk — бинарная классификация (0/1).

**Tech Stack:** PyTorch, numpy, pandas, sklearn, scipy

---

## Контекст

Текущий таргет `edge_6 = up_6 - dn_6` предсказывает направление и размах движения, но не учитывает порядок касаний SL/TP. PF=12.3 на edge_6, но TB (SL/TP первым) — шум (1–20 сделок).

**Ключевая идея:** вместо предсказания adverse excursion (adv, «сколько цена пойдёт против нас»), предсказывать **пробитость уровня** (Brk_h). Brk_h = 0 — уровень держится, вход безопасен. Brk_h = 1 — уровень пробит, вход рискован.

**Торговое правило:** входим когда `pred_Brk_6 ≈ 0` (уровень держится) И `pred_fav_6 > порог` (достаточный потенциал прибыли). Ставим TP на `pred_fav_6 × ATR`.

## Ключевые находки

1. **Per-fractal `up_6`/`dn_6` — не утечка.** fractal0 up_6 = 0 в 100% строк (shift=1, нет lookahead). Корреляция row-level up_6 vs per-fractal up_6 ≈ 0.06. Модель не может восстановить таргет из признаков.
2. **fav из up_h/dn_h покрывает 100% строк** (direction-aware из fractal0.dir), в отличие от OHLC-based fav/adv (23.7%).
3. **ATR-distance уже в тензоре** (канал 27: `abs_dist_atr`). Коридор — простая маска: `mask &= (abs_dist_atr <= X)`.
4. **Поле `break` в тензоре (канал 5):** непрерывное [0, 1]. 33.3% = 0 (не пробит), 63.1% между 0 и 1 (пробит). Для fractal0 всегда 0 (новый фрактал). Brk_h вычисляется накоплением через h баров (подход label_updn).
5. **Модель обучается на всей выборке.** Brk_6 — бинарная классификация (0/1), не фильтр обучающей выборки. Модель учится предсказывать Brk_6 = 0 (уровень держится) и Brk_6 > 0 (уровень пробит).

---

## Порядок экспериментов

| # | Вариант | Вход | Таргет | Цель |
|---|---------|------|--------|------|
| **1** | RF baseline, все 100 фракталов | (N, 100×29) = 2900 признаков | fav_6, Brk_6, fav_12, Brk_12 | Измерить R² (fav), AUC (Brk), PF — *необходимый минимум* |
| **2** | RF, коридор X=5 ATR | только фрактали с `abs_dist_atr ≤ 5`, остальные занулены | fav_6, Brk_6, fav_12, Brk_12 | Влияние коридора на R² и PF |
| **3** | RF, коридор X=3 ATR | только фрактали с `abs_dist_atr ≤ 3`, остальные занулены | fav_6, Brk_6, fav_12, Brk_12 | Более строгий коридор |
потом то же самое с transformer

**Ключевое сравнение:** если PF варианта 2 или 3 **выше**, чем варианта 1 → коридор отсекает шум. Если **ниже** → 100 фракталов несут больше информации, коридор вреден.

---

## Файловая структура

| Файл | Действие | Назначение |
|------|----------|------------|
| `ML/baseline/fav_brk_experiment.py` | Создать | Скрипт эксперимента: данные, RF, оценка, корреляционный тест |
| `processing/label_signals.py` | Изменить | Добавить `label_brk_h()` — вычисление Brk_h через label_updn-подход |
| `tests/test_fav_brk_target.py` | Создать | Тесты вычисления direction-aware fav и Brk_h |
| `ML/models/fav_brk_transformer.py` | Создать (Task 3) | Multi-output Transformer: fav (регрессия) + Brk (классификация) |
| `docs/reports/2026-06-05-fav-brk-target.md` | Создать (Task 4) | Отчёт эксперимента |

---

### Task 1: Вычисление Brk_h и тесты

**Files:**
- Modify: `processing/label_signals.py` (добавить `label_brk_h()`)
- Create: `tests/test_fav_brk_target.py`

- [ ] **Step 1: Реализовать `label_brk_h(df, horizons=[3, 6, 12])` в label_signals.py**

Алгоритм (аналог `label_updn`):
1. Пройти снизу вверх по всем строкам.
2. Для каждого фрактала (fractal0..fractal99) записать `last_seen_break[fractal_time] = fractal.break`.
3. Для каждой строки i взять fractal0.time, посмотреть `last_seen_break[time]` — это Brk_h для горизонта «бесконечность» (к моменту исчезновения фрактала).
4. Для конкретного горизонта h: найти break фрактала fractal0.time в строке i+h (если фрактал ещё виден). Если не найден — использовать last_seen.

Brk_h как бинарный таргет: `Brk_h = 1` если break > 0, иначе `Brk_h = 0`.

Записывает колонки: `brk_3`, `brk_6`, `brk_12`.

- [ ] **Step 2: Тесты direction-aware fav и Brk_h**

```python
"""Tests for direction-aware fav and Brk_h target computation."""
import numpy as np
import pandas as pd
import pytest


def test_direction_aware_fav_buy():
    """BUY direction: fav=up/ATR."""
    df = pd.DataFrame({
        'fractal0': ['0:1900.0:1:0:0:0:0:0:0:0:0:0.1:0.2:0.3:0.4:0.5:0.6:0.05:0.03:0.8:0.2:0.5:1'],
        'up_6': [0.8], 'dn_6': [0.2], 'ATR': [2.0],
    })
    # ... (direction-aware fav = up/ATR for BUY)


def test_brk_h_binary():
    """Brk_h must be 0 or 1 (binary), not continuous."""
    train = pd.read_csv('DATA/Nero_XAUUSD_train_labeled.csv', sep=';', low_memory=False, nrows=1000)
    from processing.label_signals import label_brk_h
    result = label_brk_h(train, horizons=[6, 12])
    unique_vals_6 = result['brk_6'].unique()
    unique_vals_12 = result['brk_12'].unique()
    assert set(unique_vals_6).issubset({0.0, 1.0}), f"Brk_6 has non-binary values: {unique_vals_6}"
    assert set(unique_vals_12).issubset({0.0, 1.0}), f"Brk_12 has non-binary values: {unique_vals_12}"


def test_brk_h_coverage():
    """Brk_h should be defined for most rows (fractal0.time found in future)."""
    train = pd.read_csv('DATA/Nero_XAUUSD_train_labeled.csv', sep=';', low_memory=False, nrows=1000)
    from processing.label_signals import label_brk_h
    result = label_brk_h(train, horizons=[6, 12])
    non_null_6 = result['brk_6'].notna().sum()
    non_null_12 = result['brk_12'].notna().sum()
    assert non_null_6 > 500, f"Brk_6 defined only for {non_null_6}/1000 rows"
    assert non_null_12 > 500, f"Brk_12 defined only for {non_null_12}/1000 rows"
```

- [ ] **Step 3: Запустить тесты**

```bash
cd /home/hohla/git/SoSimple && .venv/bin/pytest tests/test_fav_brk_target.py -v
```

- [ ] **Step 4: Commit**

```bash
git add processing/label_signals.py tests/test_fav_brk_target.py
git commit -m "feat: add label_brk_h and direction-aware fav target computation"
```

---

### Task 2: Скрипт эксперимента — RF baseline + коридор + корреляционный тест

**Files:**
- Create: `ML/baseline/fav_brk_experiment.py`

Скрипт выполняет:

1. **Корреляционный тест**: сравнить direction-aware fav_6 с OHLC-based fav_6_atr на signal-строках (Pearson r ≥ 0.5 — достаточно для эксперимента).

2. **Brk_6 статистика**: распределение Brk_6 = 0 vs 1, покрытие, баланс классов.

3. **RF baseline (все 100 фракталов)**: обучить RF на 2900 признаках. Четыре выхода: fav_6 (регрессия), Brk_6 (классификация), fav_12 (регрессия), Brk_12 (классификация). Оценить: R² по fav, AUC по Brk, PF по торговому правилу.

4. **RF с коридором X=5**: занулить признаки фракталей с `abs_dist_atr > 5`.

5. **RF с коридором X=3**: то же с порогом 3.

Торговое правило: BUY если `pred_Brk_6 < 0.5` (уровень держится) И `pred_fav_6 > 70pctl`. SELL если `pred_Brk_6 < 0.5` И `pred_fav_6 < 30pctl`. Пороги на train.

```bash
.venv/bin/python -m ML.baseline.fav_brk_experiment --json-out ML/reports/fav_brk_baseline.json
.venv/bin/python -m ML.baseline.fav_brk_experiment --corridor 5 --json-out ML/reports/fav_brk_corridor5.json
.venv/bin/python -m ML.baseline.fav_brk_experiment --corridor 3 --json-out ML/reports/fav_brk_corridor3.json
```

- [ ] **Step 1: Написать скрипт** (compute_direction_aware_targets, label_brk_h интеграция, RF с multi-output)

- [ ] **Step 2: Запустить 3 варианта**

- [ ] **Step 3: Проанализировать результаты** (R² fav_6, AUC Brk_6, PF, влияние коридора, сравнение с edge_6 baseline PF=12.33)

- [ ] **Step 4: Commit**

```bash
git add ML/baseline/fav_brk_experiment.py ML/reports/fav_brk_*.json
git commit -m "feat: fav + Brk experiment with ATR corridor"
```

---

### Task 3: Transformer с ATR-маской и fav/Brk таргетом

**Depends on:** Task 2 (результаты RF)

**Files:**
- Create: `ML/models/fav_brk_transformer.py`
- Modify: `ML/train.py` (добавить task `fav_brk`)

- [ ] **Step 1: Создать FavBrkTransformer** — multi-output модель:
  - fav выходы: регрессия (MSE/Huber loss) — fav_6, fav_12
  - Brk выходы: классификация (BCE loss) — Brk_6, Brk_12
  - ATR corridor маска: фрактали с `abs_dist_atr > threshold` маскируются в attention

- [ ] **Step 2: Добавить `--task fav_brk` в train.py**

- [ ] **Step 3: Обучить 3 варианта Transformer** (все 100 фракталов, коридор 5, коридор 3)

- [ ] **Step 4: Сравнить Transformer vs RF**

- [ ] **Step 5: Commit**

---

### Task 4: Отчёт эксперимента

**Depends on:** Tasks 2, 3

**Files:**
- Create: `docs/reports/2026-06-05-fav-brk-target.md`

- [ ] **Step 1: Написать отчёт** — корреляционный тест, Brk_6 статистика, RF baseline, RF с коридором, Transformer результаты, сравнение с edge_6 PF=12.33, выводы и рекомендации

- [ ] **Step 2: Обновить CONTEXT_HANDOFF.md, CHANGELOG.md**

- [ ] **Step 3: Commit**

---

## Критерии успеха

| Метрика | Минимальный порог |
|---------|-------------------|
| Корреляция direction-aware fav_6 vs OHLC fav_6_atr | r ≥ 0.5 |
| RF R² по fav_6 | > 0 (модель предсказывает лучше константы) |
| RF AUC по Brk_6 | > 0.55 (лучше случайного) |
| RF AUC по Brk_12 | > 0.55 (лучше случайного) |
| RF PF по торговому правилу | > 1.0 (модель прибыльна) |
| Коридор влияет на PF | PF(corridor) > PF(baseline) ИЛИ объяснить почему нет |

## Риски и план B

| Риск | План B |
|------|--------|
| Direction-aware fav ≈ OHLC fav (r < 0.5) | Пересчитать OHLC: `label_entry_path_targets(use_fractal_dir=True)` |
| RF R² < 0 по fav | Признаки не несут fav сигнала. Вернуться к edge_6 и улучшать признаки |
| AUC Brk_6 ≈ 0.5 (случайный) | Brk_6 не предсказуем из фрактальных признаков. Использовать Brk_6 как фильтр обучающей выборки, а не как выход модели |
| fav/Brk утечка через ATR | Запустить RF без ATR_ratio канала (канал 20). Если R² падает — утечка |
| Коридор ухудшает PF | 100 фракталов несут больше информации. Полезный вывод — не ограничивать вход |