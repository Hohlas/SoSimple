# fav/adv Multi-Target Regression с ATR-коридором — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Обучить модель предсказывать direction-aware favourable и adverse excursion (fav/adv) на горизонтах 6 и 12 баров, с ATR-коридором для фильтрации дальних фракталов. Сравнить baseline (100 фракталов) с коридорными вариантами.

**Architecture:** Multi-output регрессор (4 выхода: fav_6, adv_6, fav_12, adv_12). Сначала RF на плоских признаках (3 варианта входа), потом Transformer с distance-маской. Таргет вычисляется direction-aware из up_h/dn_h / ATR (быстрый старт, не требует переразметки).

**Tech Stack:** PyTorch, numpy, pandas, sklearn, scipy

---

## Контекст

Текущий таргет `edge_6 = up_6 - dn_6` предсказывает направление и размах движения, но не учитывает порядок касаний SL/TP. PF=12.3 на edge_6, но TB (SL/TP первым) — шум (1–20 сделок). fav/adv — два таргета вместо одного: favourable excursion (потенциал прибыли) и adverse excursion (потенциальный убыток), оба нормированы на ATR. Торговое решение — функция от обоих: брать сделку, когда `fav >> adv`.

## Ключевые находки

1. **Per-fractal `up_6`/`dn_6` — не утечка.** fractal0 up_6 = 0 в 100% строк (shift=1, нет lookahead). Корреляция row-level up_6 vs per-fractal up_6 ≈ 0.06. Модель не может восстановить таргет из признаков.
2. **fav/adv из OHLC существуют только для 23.7% строк** (signal != 0). Direction-aware (из fractal0.dir + up_h/dn_h) покрывает 100% строк. Нужно проверить корреляцию.
3. **ATR-distance уже в тензоре** (канал 27: `abs_dist_atr`). Коридор — простая маска: `mask &= (abs_dist_atr <= X)`.

---

## Порядок экспериментов

| # | Вариант | Вход | Таргет | Цель |
|---|---------|------|--------|------|
| **1** | RF baseline, все 100 фракталов | (N, 100×29) = 2900 признаков | fav/adv dir-aware | Измерить R², PF, direction accuracy — *необходимый минимум* |
| **2** | RF, коридор X=5 ATR | только фрактали с `abs_dist_atr ≤ 5`, остальные занулены | fav/adv dir-aware | Влияние коридора на R² и PF |
| **3** | RF, коридор X=3 ATR | только фрактали с `abs_dist_atr ≤ 3`, остальные занулены | fav/adv dir-aware | Более строгий коридор |

**Ключевое сравнение:** если PF варианта 2 или 3 **выше**, чем варианта 1 → коридор отсекает шум и помогает модели. Если **ниже** → 100 фракталов несут больше информации, коридор вреден.

---

## Файловая структура

| Файл | Действие | Назначение |
|------|----------|------------|
| `ML/baseline/fav_adv_experiment.py` | Создать | Скрипт эксперимента: данные, RF, оценка, корреляционный тест |
| `tests/test_fav_adv_target.py` | Создать | Тесты вычисления direction-aware таргета |
| `ML/models/fav_adv_transformer.py` | Создать (Task 3) | Multi-output Transformer регрессор с ATR-маской |
| `docs/reports/2026-06-05-fav-adv-target.md` | Создать (Task 4) | Отчёт эксперимента |

---

### Task 1: Тесты direction-aware таргета

**Files:**
- Create: `tests/test_fav_adv_target.py`

- [ ] **Step 1: Написать тесты вычисления direction-aware fav/adv таргета**

```python
"""Tests for direction-aware fav/adv target computation."""
import numpy as np
import pandas as pd
import pytest


def compute_direction_aware_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Compute fav_h_atr and adv_h_atr for all rows using fractal0 direction.

    For BUY (direction=1): fav = up_h/ATR, adv = dn_h/ATR
    For SELL (direction=-1): fav = dn_h/ATR, adv = up_h/ATR
    """
    from processing.label_signals import parse_fractal

    dirs = []
    for val in df['fractal0'].values:
        p = parse_fractal(str(val))
        dirs.append(p['direction'] if p is not None else 0)

    dirs = np.array(dirs, dtype=np.int8)
    atr = pd.to_numeric(df['ATR'], errors='coerce').fillna(1.0).values.astype(np.float32)
    atr = np.where(atr > 0, atr, 1.0)

    result = df.copy()
    for h in [3, 6, 12, 24, 48]:
        up = pd.to_numeric(df[f'up_{h}'], errors='coerce').fillna(0).values.astype(np.float32)
        dn = pd.to_numeric(df[f'dn_{h}'], errors='coerce').fillna(0).values.astype(np.float32)

        fav = np.where(dirs == 1, up, np.where(dirs == -1, dn, 0.0))
        adv = np.where(dirs == 1, dn, np.where(dirs == -1, up, 0.0))

        result[f'fav_{h}_dir_atr'] = (fav / atr).astype(np.float32)
        result[f'adv_{h}_dir_atr'] = (adv / atr).astype(np.float32)

    return result


def test_direction_aware_buy_row():
    """BUY direction: fav=up/ATR, adv=dn/ATR."""
    df = pd.DataFrame({
        'fractal0': ['0:1900.0:1:0:0:0:0:0:0:0:0:0.1:0.2:0.3:0.4:0.5:0.6:0.05:0.03:0.8:0.2:0.5:1'],
        'up_6': [0.8], 'dn_6': [0.2], 'ATR': [2.0],
        'up_12': [1.2], 'dn_12': [0.5],
    })
    result = compute_direction_aware_targets(df)
    assert np.isclose(result['fav_6_dir_atr'].iloc[0], 0.8 / 2.0)
    assert np.isclose(result['adv_6_dir_atr'].iloc[0], 0.2 / 2.0)


def test_direction_aware_sell_row():
    """SELL direction: fav=dn/ATR, adv=up/ATR."""
    df = pd.DataFrame({
        'fractal0': ['0:1900.0:-1:0:0:0:0:0:0:0:0:0.1:0.2:0.3:0.4:0.5:0.6:0.05:0.03:0.8:0.2:0.5:1'],
        'up_6': [0.8], 'dn_6': [0.2], 'ATR': [2.0],
    })
    result = compute_direction_aware_targets(df)
    assert np.isclose(result['fav_6_dir_atr'].iloc[0], 0.2 / 2.0)  # fav = dn for SELL
    assert np.isclose(result['adv_6_dir_atr'].iloc[0], 0.8 / 2.0)  # adv = up for SELL


def test_direction_aware_zero_atr():
    """ATR=0 or NaN should not cause division by zero."""
    df = pd.DataFrame({
        'fractal0': ['0:1900.0:1:0:0:0:0:0:0:0:0:0.1:0.2:0.3:0.4:0.5:0.6:0.05:0.03:0.8:0.2:0.5:1'],
        'up_6': [0.8], 'dn_6': [0.2], 'ATR': [0.0],
    })
    result = compute_direction_aware_targets(df)
    assert np.isfinite(result['fav_6_dir_atr'].iloc[0])
    assert np.isfinite(result['adv_6_dir_atr'].iloc[0])


def test_fav_adv_coverage():
    """Direction-aware targets should be non-zero for most rows (direction != 0 for 100%)."""
    train = pd.read_csv('DATA/Nero_XAUUSD_train_labeled.csv', sep=';', low_memory=False, nrows=1000)
    result = compute_direction_aware_targets(train)
    nonzero_fav = (result['fav_6_dir_atr'] != 0).sum()
    nonzero_adv = (result['adv_6_dir_atr'] != 0).sum()
    assert nonzero_fav > 500, f"Only {nonzero_fav}/1000 rows have non-zero fav_6_dir_atr"
    assert nonzero_adv > 500, f"Only {nonzero_adv}/1000 rows have non-zero adv_6_dir_atr"
```

- [ ] **Step 2: Запустить тесты, проверить green**

```bash
cd /home/hohla/git/SoSimple && .venv/bin/pytest tests/test_fav_adv_target.py -v
```

Expected: все тесты PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_fav_adv_target.py
git commit -m "test: direction-aware fav/adv target computation"
```

---

### Task 2: Скрипт эксперимента — RF baseline + коридор + корреляционный тест

**Files:**
- Create: `ML/baseline/fav_adv_experiment.py`

Скрипт выполняет:

1. **Корреляционный тест**: сравнить direction-aware fav/adv с OHLC-based fav/adv (колонки `fav_6_atr`, `adv_6_atr`) на signal-строках. Измерить Pearson r. Если r ≥ 0.7 → быстрый расчёт достаточен; если r < 0.5 → нужен OHLC-пересчёт.

2. **RF baseline (все 100 фракталов)**: обучить RF на 2900 признаках (100×29 flatten), 4 выхода (fav_6, adv_6, fav_12, adv_12). Оценить R² по каждому выходу, PF по торговому правилу.

3. **RF с коридором X=5**: занулить признаки фракталей с `abs_dist_atr > 5`, обучить RF. Сравнить с baseline.

4. **RF с коридором X=3**: то же с порогом 3.

Торговое правило: BUY если `pred_fav_6 - pred_adv_6 > 70pctl`, SELL если `< 30pctl`. Пороги на train.

- [ ] **Step 1: Написать скрипт `ML/baseline/fav_adv_experiment.py`** (полный код в приложении, ключевые функции: `compute_direction_aware_targets()`, `correlation_test()`, `evaluate_rf()`, `profit_factor()`)

- [ ] **Step 2: Запустить 3 варианта RF**

```bash
cd /home/hohla/git/SoSimple
.venv/bin/python -m ML.baseline.fav_adv_experiment --json-out ML/reports/fav_adv_baseline.json
.venv/bin/python -m ML.baseline.fav_adv_experiment --corridor 5 --json-out ML/reports/fav_adv_corridor5.json
.venv/bin/python -m ML.baseline.fav_adv_experiment --corridor 3 --json-out ML/reports/fav_adv_corridor3.json
```

- [ ] **Step 3: Проанализировать результаты**

Проверить:
1. Корреляция direction-aware vs OHLC (r ≥ 0.5 — достаточно для эксперимента)
2. R² по каждому выходу (fav_6, adv_6, fav_12, adv_12)
3. PF edge_6_dir по торговому правилу (сравнить с PF=12.33 из текущей абляции)
4. Влияние коридора (X=5, X=3) на PF и R² vs baseline

Если корреляция < 0.5 → пересчитать OHLC-based таргет (use_fractal_dir=True).

- [ ] **Step 4: Commit**

```bash
git add ML/baseline/fav_adv_experiment.py ML/reports/fav_adv_*.json
git commit -m "feat: fav/adv target experiment with ATR corridor"
```

---

### Task 3: Transformer с ATR-маской и fav/adv таргетом

**Depends on:** Task 2 (результаты RF)

**Files:**
- Create: `ML/models/fav_adv_transformer.py`
- Modify: `ML/train.py` (добавить task `fav_adv`)

- [ ] **Step 1: Создать FavAdvTransformer** — multi-output регрессор на базе TransformerClassifier: Input (batch, 100, 29) → Linear(29, d_model) → CLS + PE → TransformerEncoder → CLS output → FC(64, 32) → ReLU → FC(32, 4). ATR corridor реализуется через `src_key_padding_mask`: фрактали с `abs_dist_atr > threshold` маскируются.

- [ ] **Step 2: Добавить `--task fav_adv` в train.py** — загрузка direction-aware таргетов, 4 выхода, HuberLoss, early stopping на val Pearson r по edge_6_dir

- [ ] **Step 3: Обучить 3 варианта Transformer** (все 100 фракталов, коридор 5, коридор 3)

```bash
.venv/bin/python -m ML.train --model fav_adv_transformer --task fav_adv --epochs 50
.venv/bin/python -m ML.train --model fav_adv_transformer --task fav_adv --epochs 50 --atr_corridor 5
.venv/bin/python -m ML.train --model fav_adv_transformer --task fav_adv --epochs 50 --atr_corridor 3
```

- [ ] **Step 4: Сравнить Transformer vs RF** — если Transformer R² > RF R² и PF > RF PF → Transformer с коридором улучшает fav/adv предсказание

- [ ] **Step 5: Commit**

```bash
git add ML/models/fav_adv_transformer.py
git commit -m "feat: multi-output fav/adv Transformer regressor"
```

---

### Task 4: Отчёт эксперимента

**Depends on:** Tasks 2, 3

**Files:**
- Create: `docs/reports/2026-06-05-fav-adv-target.md`

- [ ] **Step 1: Написать отчёт** — корреляционный тест, RF baseline, RF с коридором, Transformer результаты, сравнение с edge_6 baseline (PF=12.33), выводы и рекомендации

- [ ] **Step 2: Обновить CONTEXT_HANDOFF.md, CHANGELOG.md**

- [ ] **Step 3: Commit**

```bash
git add docs/reports/2026-06-05-fav-adv-target.md
git commit -m "docs: fav/adv target experiment report"
```

---

## Критерии успеха

| Метрика | Минимальный порог |
|---------|-------------------|
| Корреляция direction-aware vs OHLC (r) | ≥ 0.5 (достаточно для эксперимента) |
| RF R² по fav_6 | > 0 (модель предсказывает лучше константы) |
| RF PF edge_6_dir | > 1.0 (модель прибыльна) |
| Коридор улучшает PF | PF(corridor) > PF(baseline) или объяснить почему нет |
| Direction accuracy | > 55% (лучше случайного) |

## Риски и план B

| Риск | План B |
|------|--------|
| Direction-aware ≈ OHLC (r < 0.5) | Пересчитать OHLC: запустить `label_entry_path_targets(df, ohlc_path, use_fractal_dir=True)` |
| RF R² < 0 по fav_adv | Признаки не несут fav/adv сигнала. Вернуться к edge_6 baseline и улучшать признаки |
| Transformer AUC ≈ 0.5 на fav/adv | fav/adv — регрессия, не классификация. AUC неприменим, оцениваем R² и PF |
| fav/adv утечка через ATR | Запустить RF без ATR_ratio канала (канал 20). Если R² падает значительно — утечка подтверждена |
| Коридор ухудшает PF | 100 фракталов несут больше информации, чем X ближайших. Это полезный вывод — не ограничивать вход |