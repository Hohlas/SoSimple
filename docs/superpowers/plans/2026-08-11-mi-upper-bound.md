# MI Upper Bound Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Оценить фундаментальный предел предсказуемости XAUUSD H1 через mutual information между live-safe признаками и таргетами. Определить, являются ли текущие R² = 0.08-0.18 потолком или недостатком моделей.

**Architecture:** Скрипт `statistics/mi_upper_bound.py` оценивает MI (kNN-оценщик KSG-типа, sklearn) для direction и amplitude таргетов на live-safe признаках `ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS`. Ценовые таргеты строятся джойном labeled CSV с `DATA/XAUUSD_H1_OHLC.csv` (в labeled CSV нет open/close). Включает: per-feature MI (основная метрика — среднее и максимум маргинальных MI; joint MI по 42 признакам не оценивается), rolling MI по конкатенации train+validation+test (2004–2026, чтобы видеть дрейф после 2022), CI по непересекающимся временным фолдам (row-bootstrap для KSG неприменим), permutation test для H0 MI=0, R² ceiling по формуле `1 - 2^(-2·MI)`. Результаты — JSON + отчёт.

**Tech Stack:** Python 3.10, sklearn (mutual_info_regression/mutual_info_classif), numpy, pandas, matplotlib. Данные: `DATA/Nero_{train,validation,test}_labeled.csv` (delimiter `;`) + `DATA/XAUUSD_H1_OHLC.csv` (`time;open;high;low;close;volume;atr14`).

**Импорт:** каталог `statistics/` не является Python-пакетом — имя конфликтует со стандартным модулем `statistics` (namespace-пакет без `__init__.py` проигрывает stdlib-модулю, `from statistics.mi_upper_bound import ...` невозможен). Runner запускается как `.venv/bin/python statistics/run_mi_upper_bound.py` и импортирует `from mi_upper_bound import ...` (sys.path[0] = каталог скрипта). Тесты загружают модуль через `importlib` по пути к файлу.

## Global Constraints

- Python: `.venv/bin/python` (3.10.12)
- Данные: semicolon-delimited CSV из `DATA/` + OHLC джойн
- Признаки: только `ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS` из `ML/entry_path_task.py` (42 признака: `session_hour`, `weekday`, 40 feature bank columns)
- Запрещённые поля: `predict`, `signal`, `ret_*`, `fav_*`, `adv_*`, `target_*`, `ret_dir_atr_lag1` — все future-derived (классификация подтверждена `tests/test_live_safe_audit.py`)
- Уровень исследования: `research_scan`, `allowed_max_verdict = research_only`
- Тесты: `pytest tests/` через `.venv/bin/python`
- Методология: разделы [00-research-management.md](../../methodology/00-research-management.md), [05-eda-data-quality.md](../../methodology/05-eda-data-quality.md), [03-feature-contract-leakage.md](../../methodology/03-feature-contract-leakage.md), [06b-oracle-preflight.md](../../methodology/06b-oracle-preflight.md)

## Методология по этапам

| Этап плана | Раздел методологии | Обязательные проверки | Критерий завершения |
|---|---|---|---|
| Task 1: Аудит существующих MI | 05-eda-data-quality | Smoke-check данных, проверка колонок | Известно, что уже есть в `feature_catalog.json` |
| Task 2: MI-скрипт (ядро) | 03-feature-contract-leakage | Все признаки live-safe, нет future-derived | Функция `estimate_mi()` проходит тесты |
| Task 3: Direction vs Amplitude MI | 00-research-management | Гипотеза зафиксирована до запуска | MI оценён для обоих таргетов с CI по временным фолдам |
| Task 4: Per-feature MI | 05-eda-data-quality | MI по каждому признаку отдельно | Таблица MI per feature сохранена |
| Task 5: Rolling MI | 06b-oracle-preflight | Окно фиксировано до запуска | Временной ряд MI построен |
| Task 6: R² ceiling + отчёт | 16-reporting-audit | Сравнение с текущими моделями | JSON + markdown отчёт |

### Применимость методологии

- **00-research-management:** гипотеза, уровень `research_scan`, gate-критерии фиксированы до запуска.
- **03-feature-contract-leakage:** все 42 признака имеют `PASS` live-safe verdict (подтверждено тестами `test_entry_path_task.py`).
- **05-eda-data-quality:** smoke-check данных перед оценкой MI.
- **06b-oracle-preflight:** MI — information-theoretic аналог oracle-preflight. Результат — `DIAGNOSTIC_ONLY` / `research_only`, не доказательство прибыльности.
- **07-baseline-first:** MI сравнивается с текущими R² моделей как baseline.

### Недоступющий раздел методологии

Нет раздела методологии для information-theoretic upper bound оценки. MI — это не leakage-проверка и не oracle-preflight в классическом смысле. Ближайший аналог — `06b-oracle-preflight` (потолок при идеальном знании), но MI оценивает потолок при **любой** модели, а не при идеальном знании labels.

**Предлагаемый порядок:** применять `06b-oracle-preflight` по аналогии — результат имеет только диагностический смысл, не повышает verdict кандидата, не используется для выбора параметров.

---

### Task 1: Аудит существующих MI-данных

**Files:**
- Read: `statistics/feature_catalog.json`
- Read: `ML/feature_screen_entry_path.py`
- Read: `statistics/nero_features_metadata.json`

**Interfaces:**
- Consumes: существующие артефакты проекта
- Produces: список пробелов — какие MI уже есть, каких нет

**Методология:** [05-eda-data-quality.md](../../methodology/05-eda-data-quality.md) — проверка качества существующих данных.

- [ ] **Step 1: Прочитать `feature_catalog.json` и определить таргет**

Открыть `statistics/feature_catalog.json`. Определить:
- Для какого таргета посчитан `mutual_information` (direction? amplitude? ret_*_dir_atr?)
- Какие признаки покрыты (feature bank? fractal features? time?)
- Какие параметры оценщика использованы (k, random_state?)

```bash
.venv/bin/python -c "
import json
data = json.load(open('statistics/feature_catalog.json'))
print(f'Total features: {len(data)}')
print(f'Keys per entry: {list(data[0].keys())}')
mi_values = [d['mutual_information'] for d in data if d.get('mutual_information') is not None]
print(f'MI range: [{min(mi_values):.4f}, {max(mi_values):.4f}]')
print(f'MI mean: {sum(mi_values)/len(mi_values):.4f}')
print(f'Features with MI > 0.1: {sum(1 for v in mi_values if v > 0.1)}')
print(f'Features with MI > 0.05: {sum(1 for v in mi_values if v > 0.05)}')
"
```

- [ ] **Step 2: Определить пробелы**

Зафиксировать, чего нет в существующих данных:
- Нет MI по live-safe таргетам (существующий MI посчитан против future-derived `signal`)
- Нет оценки неопределённости (CI) и permutation test
- Нет rolling MI
- Нет MI для amplitude таргета
- Нет R² ceiling

Результат шага: список пробелов, которые закрывает этот план.

- [ ] **Step 3: Зафиксировать решения по переиспользованию**

Решить (предварительно зафиксировано аудитом):
- Существующий MI из `feature_catalog.json` не переиспользуется (таргет `signal` — future-derived, n_neighbors=3)
- `ML/feature_screen_entry_path.py:rank_features_by_mutual_information()` — только как референс; ядро пишется заново (нужны CI по временным фолдам, permutation test, discrete-таргеты)
- Таргеты: direction `sign(close[t+1] - open[t+1])` и amplitude `|log(close[t+1] / open[t+1])|` — оба из джойна с `DATA/XAUUSD_H1_OHLC.csv`

---

### Task 2: MI-скрипт — ядро оценки

**Files:**
- Create: `statistics/mi_upper_bound.py`
- Create: `tests/test_mi_upper_bound.py`

**Interfaces:**
- Consumes: `DATA/Nero_train_labeled.csv`, `ML/entry_path_task.py:ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS`
- Produces: `estimate_mi(X, y, k=5, n_folds=10, n_permutations=200, random_state=42, discrete_target=False) -> dict` со средним/максимумом маргинальных MI, fold-CI, permutation p-value, R² ceiling

**Методология:** [03-feature-contract-leakage.md](../../methodology/03-feature-contract-leakage.md) — проверка live-safe признаков.

**Импорт в тестах:** `statistics/` не Python-пакет (конфликт со stdlib `statistics`), поэтому тест загружает модуль через `importlib` по пути к файлу.

- [ ] **Step 1: Write the failing test — estimate_mi returns correct structure**

```python
# tests/test_mi_upper_bound.py
import importlib.util
from pathlib import Path

import numpy as np
import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / 'statistics' / 'mi_upper_bound.py'
_spec = importlib.util.spec_from_file_location('mi_upper_bound', _MODULE_PATH)
mi_upper_bound = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mi_upper_bound)

estimate_mi = mi_upper_bound.estimate_mi


def test_estimate_mi_returns_dict_with_required_keys():
    rng = np.random.RandomState(42)
    X = rng.randn(200, 3)
    y = X @ np.array([1.0, 0.5, 0.0]) + rng.randn(200) * 0.1
    result = estimate_mi(X, y, k=5, n_folds=5, n_permutations=20, random_state=42)
    assert 'mean_marginal_mi_bits' in result
    assert 'max_marginal_mi_bits' in result
    assert 'mi_ci_p05' in result
    assert 'mi_ci_p95' in result
    assert 'perm_p_value' in result
    assert 'r2_ceiling' in result
    assert 'n_samples' in result
    assert 'n_features' in result


def test_estimate_mi_r2_ceiling_formula():
    rng = np.random.RandomState(42)
    X = rng.randn(200, 2)
    y = X @ np.array([2.0, -1.0]) + rng.randn(200) * 0.01
    result = estimate_mi(X, y, k=5, n_folds=5, n_permutations=20, random_state=42)
    assert 0.0 <= result['r2_ceiling'] <= 1.0
    assert result['r2_ceiling'] == pytest.approx(1 - 2**(-2 * result['mean_marginal_mi_bits']), rel=1e-6)


def test_estimate_mi_independent_features_low_mi():
    rng = np.random.RandomState(42)
    X = rng.randn(500, 2)
    y = rng.randn(500)
    result = estimate_mi(X, y, k=5, n_folds=5, n_permutations=20, random_state=42)
    assert result['mean_marginal_mi_bits'] < 0.05
    assert result['perm_p_value'] > 0.05
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/python -m pytest tests/test_mi_upper_bound.py -v
```

Expected: FAIL — `statistics/mi_upper_bound.py` ещё не существует (FileNotFoundError при загрузке через importlib)

- [ ] **Step 3: Write minimal implementation**

Основная метрика — **среднее и максимум маргинальных MI** (по одному признаку). Joint MI по 42 признакам не оценивается; `r2_ceiling` из маргинальных MI — диагностическая оценка (см. spec «Ограничения метода», п. 4).

**Оценка стабильности — временные фолды, не bootstrap.** Row-bootstrap с дублями строк для kNN/KSG-оценщика неприменим: идентичные строки дают нулевые расстояния до соседей и раздувают MI (проверено численно: на зависимых данных точечная оценка 0.17, bootstrap-среднее 0.45 — CI не содержит точечную оценку). Вместо него — разброс MI по непересекающимся временным сегментам (данные уже отсортированы по времени в `load_mi_data`). Точечная оценка на полном объёме может лежать выше fold-CI — ожидаемое следствие конечновыборочного смещения KSG (оценка на фолдах смещена сильнее), это не баг.

```python
# statistics/mi_upper_bound.py
from __future__ import annotations

import numpy as np
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression


def _mi_scores(X, y, k, random_state, discrete_target):
    estimator = mutual_info_classif if discrete_target else mutual_info_regression
    return estimator(X, y, discrete_features=False, n_neighbors=k, random_state=random_state)


def estimate_mi(
    X: np.ndarray,
    y: np.ndarray,
    k: int = 5,
    n_folds: int = 10,
    n_permutations: int = 200,
    random_state: int = 42,
    discrete_target: bool = False,
) -> dict:
    n_samples, n_features = X.shape
    rng = np.random.RandomState(random_state)
    scores = _mi_scores(X, y, k, random_state, discrete_target)
    mean_mi = float(scores.mean())
    max_mi = float(scores.max())
    # Разброс по непересекающимся временным сегментам (данные отсортированы по времени).
    fold_scores = []
    for chunk in np.array_split(np.arange(n_samples), n_folds):
        if len(chunk) < max(2 * k + 1, 50):
            continue
        fold_scores.append(float(_mi_scores(
            X[chunk], y[chunk], k, rng.randint(0, 2**31), discrete_target,
        ).mean()))
    if len(fold_scores) >= 2:
        ci = np.percentile(fold_scores, [5, 95])
    else:
        ci = np.array([mean_mi, mean_mi])
    perm_scores = []
    for _ in range(n_permutations):
        y_perm = y[rng.permutation(n_samples)]
        perm_scores.append(float(_mi_scores(
            X, y_perm, k, rng.randint(0, 2**31), discrete_target,
        ).mean()))
    perm_p_value = float((np.sum(np.asarray(perm_scores) >= mean_mi) + 1) / (n_permutations + 1))
    return {
        'mean_marginal_mi_bits': mean_mi,
        'max_marginal_mi_bits': max_mi,
        'mi_ci_p05': float(ci[0]),
        'mi_ci_p95': float(ci[1]),
        'perm_p_value': perm_p_value,
        # R² <= 1 - 2^(-2·I); диагностическая оценка из маргинального MI
        'r2_ceiling': float(1 - 2**(-2 * mean_mi)),
        'n_samples': n_samples,
        'n_features': n_features,
        'n_folds_used': len(fold_scores),
        'discrete_target': discrete_target,
    }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
.venv/bin/python -m pytest tests/test_mi_upper_bound.py -v
```

Expected: PASS

- [ ] **Step 5: Write test — per-feature MI**

```python
# tests/test_mi_upper_bound.py (добавить; estimate_mi_per_feature берётся из уже загруженного модуля)
estimate_mi_per_feature = mi_upper_bound.estimate_mi_per_feature


def test_estimate_mi_per_feature_returns_dataframe():
    rng = np.random.RandomState(42)
    X = rng.randn(200, 3)
    y = X[:, 0] * 2.0 + rng.randn(200) * 0.1
    feature_names = ['feat_a', 'feat_b', 'feat_c']
    result = estimate_mi_per_feature(X, y, feature_names, k=5, random_state=42)
    assert len(result) == 3
    assert list(result.columns) == ['feature', 'mi_bits']
    assert result.iloc[0]['feature'] == 'feat_a'
```

- [ ] **Step 6: Add per-feature MI implementation**

```python
# statistics/mi_upper_bound.py (добавить)
import pandas as pd


def estimate_mi_per_feature(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list[str],
    k: int = 5,
    random_state: int = 42,
    discrete_target: bool = False,
) -> pd.DataFrame:
    scores = _mi_scores(X, y, k, random_state, discrete_target)
    df = pd.DataFrame({'feature': feature_names, 'mi_bits': scores})
    return df.sort_values('mi_bits', ascending=False).reset_index(drop=True)
```

- [ ] **Step 7: Run all tests**

```bash
.venv/bin/python -m pytest tests/test_mi_upper_bound.py -v
```

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add statistics/mi_upper_bound.py tests/test_mi_upper_bound.py
git commit -m "feat: MI upper bound estimation with fold CI and per-feature breakdown"
```

---

### Task 3: Direction vs Amplitude MI — запуск оценки

**Files:**
- Create: `statistics/run_mi_upper_bound.py` (runner)
- Modify: `statistics/mi_upper_bound.py` (добавить загрузку данных и таргеты)

**Interfaces:**
- Consumes: `estimate_mi()`, `estimate_mi_per_feature()` из Task 2
- Produces: `ML/reports/mi_upper_bound.json`

**Методология:** [00-research-management.md](../../methodology/00-research-management.md) — фиксация гипотезы и gate-критериев до запуска.

**Фиксация до запуска (обязательно по методологии):**

```text
lifecycle_status = research_scan
allowed_max_verdict = research_only
locked_test = not_opened

Гипотеза: MI(features; amplitude) > MI(features; direction),
          что подтвердит hypothesis из ретроспективы 2.10.

Таргеты (строятся джойном labeled CSV с DATA/XAUUSD_H1_OHLC.csv по time;
в labeled CSV нет open/close):
  T1_direction: sign(close[t+1] - open[t+1]), дискретный → mutual_info_classif
  T2_amplitude: |log(close[t+1] / open[t+1])|, непрерывный → mutual_info_regression

Gate-критерии (permutation test, H0: MI = 0):
  perm_p_value < 0.05 и CI не включает 0 → предсказуемость существует (PASS)
  perm_p_value >= 0.05 → предсказуемость отсутствует (FAIL)
  p < 0.05, но CI включает 0 → INCONCLUSIVE

Минимальные числа:
  min_samples: 1000 (train)
  min_features: 42 (ENTRY_PATH_V1_LIVE_SAFE)
  max_drop_after_ohlc_join: 5%
```

- [ ] **Step 1: Write test — data loading produces correct shapes**

```python
# tests/test_mi_upper_bound.py (добавить; load_mi_data берётся из уже загруженного модуля)
load_mi_data = mi_upper_bound.load_mi_data


def test_load_mi_data_returns_features_and_targets():
    data = load_mi_data('DATA/Nero_train_labeled.csv', ohlc_path='DATA/XAUUSD_H1_OHLC.csv')
    assert 'X' in data
    assert 'y_direction' in data
    assert 'y_amplitude' in data
    assert 'feature_names' in data
    assert 'time' in data
    assert data['X'].shape[1] == len(data['feature_names'])
    assert data['X'].shape[0] > 1000
    assert set(np.unique(data['y_direction'])).issubset({-1.0, 0.0, 1.0})
    assert np.isfinite(data['y_amplitude']).all()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/python -m pytest tests/test_mi_upper_bound.py::test_load_mi_data_returns_features_and_targets -v
```

Expected: FAIL

- [ ] **Step 3: Implement data loading**

Добавить в `statistics/mi_upper_bound.py`. Таргеты строятся джойном с OHLC: в labeled CSV колонок `open`/`close` нет (проверено: их нет в заголовке `DATA/Nero_train_labeled.csv`).

**Дубли `time` (факт, обнаружен при проверке):** в labeled CSV `time` не уникален — train: 5 592 строк-дублей (44 159 → 41 363, −6.3%), validation −5.1%, test −5.4%. Пары различаются во фрактальных колонках (и в производных таргетах), т.е. это два состояния одного бара. Конвенция проекта — `drop_duplicates('time', keep='last')` (`ML/benchmark_execution_policy_v2.py:78`, `ML/baseline/compare_nero_by_time.py:151`); применяется она ДО feature bank и фиксируется в disclosure.

```python
import sys
from pathlib import Path

import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ML.entry_path_task import ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS
from ML.entry_path_feature_bank import build_entry_path_feature_bank


FUTURE_DERIVED_DENYLIST = {
    'predict', 'signal', 'ret_dir_atr_lag1',
    'ret_6_dir_atr', 'ret_12_dir_atr', 'ret_24_dir_atr',
    'fav_3_atr', 'adv_3_atr', 'fav_6_atr', 'adv_6_atr',
    'fav_12_atr', 'adv_12_atr', 'fav_24_atr', 'adv_24_atr',
}


def load_mi_data(csv_path: str, ohlc_path: str = 'DATA/XAUUSD_H1_OHLC.csv') -> dict:
    df = pd.read_csv(csv_path, delimiter=';')
    assert 'time' in df.columns
    df = df.sort_values('time').reset_index(drop=True)
    n_raw = len(df)
    df = df.drop_duplicates('time', keep='last').reset_index(drop=True)
    n_dedup_dropped = n_raw - len(df)

    overlap = set(ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS) & FUTURE_DERIVED_DENYLIST
    assert not overlap, f'Live-safe features overlap with denylist: {overlap}'

    missing = [c for c in ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS if c not in df.columns]
    assert not missing, f'Missing features in CSV: {missing}'

    ohlc = pd.read_csv(ohlc_path, delimiter=';')
    assert ohlc['time'].is_unique, 'OHLC time column has duplicates'
    merged = df.merge(ohlc[['time', 'open', 'close']], on='time', how='inner', validate='one_to_one')
    drop_ratio = 1.0 - len(merged) / len(df)
    assert drop_ratio <= 0.05, f'OHLC join dropped {drop_ratio:.1%} of rows'
    merged = merged.sort_values('time').reset_index(drop=True)

    df_with_bank = build_entry_path_feature_bank(merged)
    X = df_with_bank[ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS].apply(
        pd.to_numeric, errors='coerce'
    ).fillna(0.0).values.astype(np.float64)

    # Таргеты — следующий бар (t+1), известны только после его закрытия:
    # это таргеты, не признаки — live-safe контракт признаков не нарушается.
    next_open = merged['open'].shift(-1)
    next_close = merged['close'].shift(-1)
    y_direction = np.sign(next_close - next_open).values.astype(np.float64)
    y_amplitude = np.abs(np.log(next_close / next_open)).values

    valid = np.isfinite(y_amplitude) & np.isfinite(y_direction)
    return {
        'X': X[valid],
        'y_direction': y_direction[valid],
        'y_amplitude': y_amplitude[valid],
        'feature_names': list(ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS),
        'time': merged['time'].values[valid],
        'n_dedup_dropped': int(n_dedup_dropped),
        'n_join_dropped': int(len(df) - len(merged)),
    }
```

- [ ] **Step 4: Run test**

```bash
.venv/bin/python -m pytest tests/test_mi_upper_bound.py::test_load_mi_data_returns_features_and_targets -v
```

Expected: PASS (OHLC-джойн обязателен: без `DATA/XAUUSD_H1_OHLC.csv` таргеты не построить)

- [ ] **Step 5: Write runner script**

Runner запускается как `.venv/bin/python statistics/run_mi_upper_bound.py` — sys.path[0] = каталог `statistics/`, поэтому импорт `from mi_upper_bound import ...` (не `statistics.mi_upper_bound` — это имя конфликтует со stdlib).

```python
# statistics/run_mi_upper_bound.py
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from mi_upper_bound import (
    estimate_mi,
    estimate_mi_per_feature,
    load_mi_data,
)


def main():
    parser = argparse.ArgumentParser(description='MI Upper Bound estimation')
    parser.add_argument('--train', default='DATA/Nero_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_validation_labeled.csv')
    parser.add_argument('--ohlc', default='DATA/XAUUSD_H1_OHLC.csv')
    parser.add_argument('--output', default='ML/reports/mi_upper_bound.json')
    parser.add_argument('--k', type=int, default=5)
    parser.add_argument('--n-folds', type=int, default=10)
    parser.add_argument('--n-permutations', type=int, default=200)
    parser.add_argument('--random-state', type=int, default=42)
    args = parser.parse_args()

    results = {
        'config': {
            'k': args.k,
            'n_folds': args.n_folds,
            'n_permutations': args.n_permutations,
            'random_state': args.random_state,
            'train_file': args.train,
            'val_file': args.val,
            'ohlc_file': args.ohlc,
            'feature_set': 'ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS',
            'n_features': 42,
            'r2_ceiling_formula': '1 - 2^(-2 * mean_marginal_mi_bits)',
            'targets': {
                'direction': 'sign(close[t+1] - open[t+1]) из OHLC-джойна',
                'amplitude': '|log(close[t+1] / open[t+1])| из OHLC-джойна',
            },
        },
    }

    for split_name, split_path in [('train', args.train), ('validation', args.val)]:
        data = load_mi_data(split_path, ohlc_path=args.ohlc)
        split_result = {
            'n_samples': data['X'].shape[0],
            'n_features': data['X'].shape[1],
        }

        mi_dir = estimate_mi(
            data['X'], data['y_direction'],
            k=args.k, n_folds=args.n_folds, n_permutations=args.n_permutations,
            random_state=args.random_state, discrete_target=True,
        )
        split_result['direction'] = mi_dir

        mi_amp = estimate_mi(
            data['X'], data['y_amplitude'],
            k=args.k, n_folds=args.n_folds, n_permutations=args.n_permutations,
            random_state=args.random_state, discrete_target=False,
        )
        split_result['amplitude'] = mi_amp

        per_feat_dir = estimate_mi_per_feature(
            data['X'], data['y_direction'],
            data['feature_names'], k=args.k, random_state=args.random_state,
            discrete_target=True,
        )
        split_result['per_feature_direction'] = per_feat_dir.to_dict('records')

        per_feat_amp = estimate_mi_per_feature(
            data['X'], data['y_amplitude'],
            data['feature_names'], k=args.k, random_state=args.random_state,
            discrete_target=False,
        )
        split_result['per_feature_amplitude'] = per_feat_amp.to_dict('records')

        results[split_name] = split_result

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=float)
    print(f'Results saved to {args.output}')


if __name__ == '__main__':
    main()
```

- [ ] **Step 6: Run the estimation**

```bash
.venv/bin/python statistics/run_mi_upper_bound.py \
    --train DATA/Nero_train_labeled.csv \
    --val DATA/Nero_validation_labeled.csv \
    --ohlc DATA/XAUUSD_H1_OHLC.csv \
    --output ML/reports/mi_upper_bound.json \
    --k 5 --n-folds 10 --n-permutations 200 --random-state 42
```

- [ ] **Step 7: Проверить результат**

```bash
.venv/bin/python -c "
import json
r = json.load(open('ML/reports/mi_upper_bound.json'))
for split in ['train', 'validation']:
    d = r[split]
    print(f'=== {split} (N={d[\"n_samples\"]}) ===')
    for target in ['direction', 'amplitude']:
        m = d[target]
        print(f'  {target}: MI={m[\"mean_marginal_mi_bits\"]:.4f} (max {m[\"max_marginal_mi_bits\"]:.4f}) bits '
              f'CI=[{m[\"mi_ci_p05\"]:.4f}, {m[\"mi_ci_p95\"]:.4f}] p={m[\"perm_p_value\"]:.3f} '
              f'R2ceiling={m[\"r2_ceiling\"]:.4f}')
    top5 = d['per_feature_direction'][:5]
    print(f'  Top-5 features (direction): {[(f[\"feature\"], round(f[\"mi_bits\"], 4)) for f in top5]}')
"
```

- [ ] **Step 8: Commit**

```bash
git add statistics/run_mi_upper_bound.py ML/reports/mi_upper_bound.json
git commit -m "feat: run MI upper bound estimation for direction and amplitude targets"
```

---

### Task 4: Per-feature MI — анализ и визуализация

**Files:**
- Modify: `statistics/run_mi_upper_bound.py` (добавить групповой анализ)
- Create: `ML/plots/mi_per_feature.png`

**Interfaces:**
- Consumes: `ML/reports/mi_upper_bound.json` из Task 3
- Produces: групповой анализ MI по семействам признаков

**Методология:** [05-eda-data-quality.md](../../methodology/05-eda-data-quality.md) — EDA-анализ информативности признаков.

- [ ] **Step 1: Добавить групповой анализ в runner**

Добавить в `statistics/run_mi_upper_bound.py` функцию:

```python
FEATURE_GROUPS = {
    'time': ['session_hour', 'weekday'],
    'strong': [c for c in ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS if 'strong' in c],
    'break': [c for c in ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS if 'break' in c],
    'direction_balance': [c for c in ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS if 'direction_balance' in c],
    'back': [c for c in ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS if 'back' in c],
    'impulse': [c for c in ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS if 'impulse' in c],
    'power': [c for c in ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS if 'power' in c],
    'count': [c for c in ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS if 'count' in c],
}


def group_mi(per_feature: list[dict]) -> dict:
    df = pd.DataFrame(per_feature)
    result = {}
    for group_name, group_features in FEATURE_GROUPS.items():
        mask = df['feature'].isin(group_features)
        if mask.any():
            result[group_name] = {
                'mean_mi': float(df.loc[mask, 'mi_bits'].mean()),
                'max_mi': float(df.loc[mask, 'mi_bits'].max()),
                'n_features': int(mask.sum()),
            }
    return result
```

- [ ] **Step 2: Добавить вызов group_mi в runner**

В `main()`, после `per_feat_dir` и `per_feat_amp`:

```python
split_result['group_mi_direction'] = group_mi(split_result['per_feature_direction'])
if 'per_feature_amplitude' in split_result:
    split_result['group_mi_amplitude'] = group_mi(split_result['per_feature_amplitude'])
```

- [ ] **Step 3: Перезапустить runner**

```bash
.venv/bin/python statistics/run_mi_upper_bound.py \
    --train DATA/Nero_train_labeled.csv \
    --val DATA/Nero_validation_labeled.csv \
    --output ML/reports/mi_upper_bound.json
```

- [ ] **Step 4: Построить визуализацию**

```bash
.venv/bin/python -c "
import json
import matplotlib.pyplot as plt
import pandas as pd

r = json.load(open('ML/reports/mi_upper_bound.json'))

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for ax, target in zip(axes, ['direction', 'amplitude']):
    per_feat = r['train'].get(f'per_feature_{target}', [])
    if not per_feat:
        continue
    df = pd.DataFrame(per_feat).head(20)
    ax.barh(df['feature'], df['mi_bits'])
    ax.set_xlabel('MI (bits)')
    ax.set_title(f'Top-20 features: {target}')
    ax.invert_yaxis()

plt.tight_layout()
plt.savefig('ML/plots/mi_per_feature.png', dpi=150)
print('Saved ML/plots/mi_per_feature.png')
"
```

- [ ] **Step 5: Зафиксировать групповой вывод**

```bash
.venv/bin/python -c "
import json
r = json.load(open('ML/reports/mi_upper_bound.json'))
for split in ['train', 'validation']:
    print(f'=== {split} ===')
    for target in ['direction', 'amplitude']:
        key = f'group_mi_{target}'
        if key in r[split]:
            print(f'  {target}:')
            for group, stats in r[split][key].items():
                print(f'    {group}: mean={stats[\"mean_mi\"]:.4f}, max={stats[\"max_mi\"]:.4f}, n={stats[\"n_features\"]}')
"
```

- [ ] **Step 6: Commit**

```bash
git add statistics/run_mi_upper_bound.py ML/reports/mi_upper_bound.json ML/plots/mi_per_feature.png
git commit -m "feat: per-feature MI grouping and visualization"
```

---

### Task 5: Rolling MI — regime drift detection

**Files:**
- Modify: `statistics/mi_upper_bound.py` (добавить `estimate_rolling_mi`)
- Modify: `statistics/run_mi_upper_bound.py` (добавить rolling MI в output)

**Interfaces:**
- Consumes: `load_mi_data()`, `estimate_mi()` из Task 2
- Produces: секция `rolling` в `ML/reports/mi_rolling.json` / `mi_upper_bound.json` — временной ряд MI

**Методология:** [06b-oracle-preflight.md](../../methodology/06b-oracle-preflight.md) — проверка стабильности потолка во времени.

**Фиксация до запуска:**

```text
Данные: конкатенация train + validation + test (2004–2026).
        Только так rolling MI покрывает период после 2022, где ретроспектива 6.3
        зафиксировала regime drift. Окна на стыках split'ов — допустимы (диагностика).
window = 500 bars (~2 месяца при плотности этого датасета, ~246 баров/мес)
step = 100 bars
min_window_samples = 500 (фиксировано до запуска)
n_folds = 5, n_permutations = 0 (только точечные оценки, CI окон не интерпретируются)
```

- [ ] **Step 1: Write test — rolling MI**

```python
# tests/test_mi_upper_bound.py (добавить; в начало файла добавить import pandas as pd)
estimate_rolling_mi = mi_upper_bound.estimate_rolling_mi


def test_estimate_rolling_mi_returns_time_series():
    rng = np.random.RandomState(42)
    n = 1000
    X = rng.randn(n, 2)
    y = X[:, 0] + rng.randn(n) * 0.5
    timestamps = pd.date_range('2020-01-01', periods=n, freq='h')
    result = estimate_rolling_mi(X, y, timestamps, window=200, step=100, k=5, random_state=42)
    assert 'timestamps' in result
    assert 'mi_bits' in result
    assert 'r2_ceiling' in result
    assert len(result['mi_bits']) == len(result['timestamps'])
    assert all(0 <= v <= 1 for v in result['r2_ceiling'])
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/python -m pytest tests/test_mi_upper_bound.py::test_estimate_rolling_mi_returns_time_series -v
```

Expected: FAIL

- [ ] **Step 3: Implement rolling MI**

```python
# statistics/mi_upper_bound.py (добавить)
import pandas as pd


def estimate_rolling_mi(
    X: np.ndarray,
    y: np.ndarray,
    timestamps,
    window: int = 500,
    step: int = 100,
    k: int = 5,
    random_state: int = 42,
    discrete_target: bool = False,
) -> dict:
    n = len(y)
    ts_list, mi_list, r2_list = [], [], []
    for start in range(0, n - window + 1, step):
        end = start + window
        mi_result = estimate_mi(
            X[start:end], y[start:end], k=k,
            n_folds=5, n_permutations=0,
            random_state=random_state, discrete_target=discrete_target,
        )
        ts_list.append(str(timestamps[end - 1]))
        mi_list.append(mi_result['mean_marginal_mi_bits'])
        r2_list.append(mi_result['r2_ceiling'])
    return {
        'timestamps': ts_list,
        'mi_bits': mi_list,
        'r2_ceiling': r2_list,
        'window': window,
        'step': step,
    }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
.venv/bin/python -m pytest tests/test_mi_upper_bound.py::test_estimate_rolling_mi_returns_time_series -v
```

Expected: PASS

- [ ] **Step 5: Добавить rolling MI в runner**

В `statistics/run_mi_upper_bound.py` добавить (конкатенация всех трёх split'ов, timestamps берутся из результата `load_mi_data`):

```python
import numpy as np


def compute_rolling_mi(split_paths: list[str], ohlc_path: str, k: int, random_state: int) -> dict:
    parts = [load_mi_data(path, ohlc_path=ohlc_path) for path in split_paths]
    X = np.concatenate([p['X'] for p in parts])
    order = np.argsort(np.concatenate([p['time'] for p in parts]), kind='stable')
    X = X[order]
    y_dir = np.concatenate([p['y_direction'] for p in parts])[order]
    y_amp = np.concatenate([p['y_amplitude'] for p in parts])[order]
    timestamps = np.concatenate([p['time'] for p in parts])[order]

    return {
        'direction': estimate_rolling_mi(
            X, y_dir, timestamps, window=500, step=100, k=k,
            random_state=random_state, discrete_target=True,
        ),
        'amplitude': estimate_rolling_mi(
            X, y_amp, timestamps, window=500, step=100, k=k,
            random_state=random_state, discrete_target=False,
        ),
        'splits': split_paths,
        'n_samples_total': int(len(y_dir)),
    }
```

И в `main()`:

```python
results['rolling'] = compute_rolling_mi(
    [args.train, args.val, 'DATA/Nero_test_labeled.csv'],
    ohlc_path=args.ohlc, k=args.k, random_state=args.random_state,
)
```

- [ ] **Step 6: Построить rolling MI plot**

```bash
.venv/bin/python -c "
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

r = json.load(open('ML/reports/mi_upper_bound.json'))
rolling = r.get('rolling', {})

fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

for ax, target in zip(axes, ['direction', 'amplitude']):
    if target not in rolling:
        continue
    d = rolling[target]
    ts = [t[:10] for t in d['timestamps']]
    ax.plot(ts, d['mi_bits'], label='MI (bits)')
    ax.axhline(0.01, color='red', linestyle='--', alpha=0.5, label='threshold 0.01')
    ax.set_ylabel('MI (bits)')
    ax.set_title(f'Rolling MI: {target}')
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('ML/plots/mi_rolling.png', dpi=150)
print('Saved ML/plots/mi_rolling.png')
"
```

- [ ] **Step 7: Commit**

```bash
git add statistics/mi_upper_bound.py statistics/run_mi_upper_bound.py \
       ML/reports/mi_upper_bound.json ML/plots/mi_rolling.png
git commit -m "feat: rolling MI for regime drift detection"
```

---

### Task 6: R² ceiling, сравнение с моделями, итоговый отчёт

**Files:**
- Create: `docs/reports/2026-08-11-mi-upper-bound.md`

**Interfaces:**
- Consumes: `ML/reports/mi_upper_bound.json` из Task 5
- Produces: итоговый отчёт с интерпретацией

**Методология:** [16-reporting-audit.md](../../methodology/16-reporting-audit.md) — отчёт с disclosure.

- [ ] **Step 1: Извлечь R² ceiling и сравнить с моделями**

Legacy-значения R² взяты из ретроспективы: BiLSTM R²=0.10 (r=0.32) и Transformer R²=0.18 (r=0.43) — регрессия up/dn на горизонтах 12/24/48H (стр. 17); `baseline_clean` R²=0.084 — feature bank (секция 2.5). Эти модели обучены на future-derived признаках (live-safe аудит: все 5 систем FAIL, секция 2.6) и на других горизонтах — сравнение **ориентировочное**, не доказательство переобучения.

```bash
.venv/bin/python -c "
import json
r = json.load(open('ML/reports/mi_upper_bound.json'))

print('=== R² Ceiling vs Legacy Models (ориентировочное сравнение) ===')
print()

legacy_models = {
    'BiLSTM up/dn (12/24/48H, future-derived входы)': 0.10,
    'Transformer up/dn (12/24/48H, future-derived входы)': 0.18,
    'baseline_clean feature bank': 0.084,
}

for split in ['train', 'validation']:
    d = r[split]
    for target in ['direction', 'amplitude']:
        if target in d:
            mi = d[target]
            print(f'{split} / {target}:')
            print(f'  mean marginal MI = {mi[\"mean_marginal_mi_bits\"]:.4f} bits '
                  f'(max {mi[\"max_marginal_mi_bits\"]:.4f}, p={mi[\"perm_p_value\"]:.3f})')
            print(f'  R² ceiling (диагностический) = {mi[\"r2_ceiling\"]:.4f}')
            print(f'  CI = [{mi[\"mi_ci_p05\"]:.4f}, {mi[\"mi_ci_p95\"]:.4f}]')
            for model_name, model_r2 in legacy_models.items():
                gap = mi['r2_ceiling'] - model_r2
                status = 'NEAR CEILING' if abs(gap) < 0.02 else 'HEADROOM' if gap > 0.02 else 'ABOVE (сравнение нестрогое: другие входы/горизонт)'
                print(f'    vs {model_name} (R²={model_r2}): gap={gap:+.4f} → {status}')
            print()
"
```

- [ ] **Step 2: Написать итоговый отчёт**

Создать `docs/reports/2026-08-11-mi-upper-bound.md` с разделами:

```markdown
# MI Upper Bound: оценка предсказуемости XAUUSD H1

**Дата:** 2026-08-11
**Уровень:** research_scan, allowed_max_verdict = research_only
**Метод:** kNN-оценщик KSG-типа (sklearn mutual_info_regression/classif), k=5, CI по 10 временным фолдам, permutation 200
**Формула потолка:** R² <= 1 - 2^(-2·I); потолок из среднего маргинального MI — диагностический (не joint MI)

## 1. Цель

Оценить фундаментальный предел предсказуемости через mutual information.
Ответить: текущие R² = 0.08-0.18 — потолок или недостаток моделей?

## 2. Конфигурация

- Признаки: ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS (42 признака)
- Таргеты: direction = sign(close[t+1]-open[t+1]), amplitude = |log(close[t+1]/open[t+1])| (джойн с DATA/XAUUSD_H1_OHLC.csv)
- Данные: Nero_train_labeled.csv, Nero_validation_labeled.csv; rolling MI — конкатенация с Nero_test_labeled.csv (2004–2026)
- Параметры KSG: k=5, n_folds=10, n_permutations=200, random_state=42
- Rolling MI: window=500, step=100

## 3. Результаты

[Вставить вывод из Step 1]

## 4. Per-feature MI

[Вставить top-10 признаков по MI для direction и amplitude]

## 5. Rolling MI

[Вставить анализ стабильности MI во времени, включая поведение после 2022]
[Вставить график mi_rolling.png]

## 6. Интерпретация

### 6.1 Direction vs Amplitude
[Сравнить MI direction и amplitude. Подтверждает ли hypothesis ретроспективы?]

### 6.2 R² Ceiling vs Models
[Модели на пределе или есть запас? Обязательно указать ограничения сравнения:
legacy-модели на future-derived входах (ретроспектива 2.6) и горизонтах 12/24/48H,
потолок из маргинального MI — диагностический.]

### 6.3 Regime Drift
[Rolling MI показывает стабильность или деградацию, в т.ч. после 2022?]

### 6.4 Time-only dominance
[Группа time vs другие группы по MI]

## 7. Вердикт

[PASS / FAIL / INCONCLUSIVE по gate-критериям permutation test из Task 3]

## 8. Рекомендации

[Что делать дальше на основе MI]

## 9. Disclosure

- N конфигураций: 1 (фиксированная до запуска)
- Search budget: 1 оценка MI
- Feature contract: ENTRY_PATH_V1_LIVE_SAFE (PASS по live-safe audit)
- R² ceiling: диагностический (маргинальный MI, не joint)
- Сравнение с legacy R²: ориентировочное (future-derived входы legacy-моделей)
- Smoke-check: [результат]
```

- [ ] **Step 3: Заполнить отчёт фактическими данными**

Выполнить все команды из Steps 1-2, вставить реальные числа в отчёт.

- [ ] **Step 4: Commit**

```bash
git add docs/reports/2026-08-11-mi-upper-bound.md
git commit -m "docs: MI upper bound report with R² ceiling analysis"
```

---

## Unknowns / Вопросы для уточнения

1. **Таргет direction — РЕШЕНО (аудит К2):** в labeled CSV нет `open`/`close` (проверено по заголовку `DATA/Nero_train_labeled.csv`), поэтому `path_6_class` как замена не эквивалентен spec. Решение: таргеты строятся джойном с `DATA/XAUUSD_H1_OHLC.csv` (`time;open;high;low;close;volume;atr14`, данные с 2004.06): T1 = `sign(close[t+1] - open[t+1])` (дискретный → `mutual_info_classif`), T2 = `|log(close[t+1] / open[t+1])|` (непрерывный → `mutual_info_regression`). `path_6_class` не используется.

2. **Таргет amplitude — РЕШЕНО (аудит К2):** `close`/`open` берутся из OHLC-джойна, future-derived прокси (`ret_*_dir_atr`) не нужны. Контроль качества джойна: дубли `time` запрещены, потери строк ≤ 5% (stop rule в spec).

3. **feature_catalog.json — РЕШЕНО (аудит У4):** существующий MI посчитан против таргета `signal` (future-derived, `statistics/EDA.ipynb`, n_neighbors=3, только top-100 признаков). Не переиспользуется; ядро пишется заново.

4. **Вычислительная стоимость:** train ~41 000 строк после дедупликации (не ~4000 — факт проверен), оценка MI с фолдами и permutation по 42 признакам занимает минуты. Rolling MI: ~620 окон по всей конкатенации (~60 000 строк) × (1 + 5 фолдов) вызовов. **Решение:** rolling считается с n_folds=5 и без permutation (зафиксировано в Task 5); при неприемлемом времени — уменьшить шаг до 200, зафиксировав это до запуска.

5. **Импорт модуля — РЕШЕНО (аудит К3):** `statistics/` конфликтует со stdlib-модулем `statistics` (namespace-пакет без `__init__.py` проигрывает обычному модулю). `__init__.py` не добавляется (риск затенить stdlib для скриптов, запускаемых из корня). Импорт: runner — `from mi_upper_bound import ...`; тесты — `importlib` по пути к файлу.

6. **Открыто:** joint MI по 42 признакам не оценивается (среднее маргинальных MI — не joint; R²-потолок диагностический). Если потребуется строгая граница — отдельный эксперимент с npeet на пониженной размерности.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-11-mi-upper-bound.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
