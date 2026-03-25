# Денормализация updn: сохранение brk/cap + inverse transform

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Сохранять per-row параметры нормализации (brk, cap) при обучении и использовать их для точной денормализации предсказаний модели из [0,1] в пункты — как в signal_tracer.py, так и (в будущем) при инференсе вместо ручного ML_ScaleK.

**Architecture:** В `normalize_rowwise()` добавляем сбор brk/cap в массив и сохранение в `.npy`. В `signal_tracer.py` загружаем эти параметры и применяем `inverse_piecewise_linear_log` для денормализации ground truth up_12/dn_12. Inverse-функция уже реализована в signal_tracer.py (строка 50).

**Tech Stack:** Python 3.11+, NumPy, pandas

---

## Обзор файлов

| Файл | Действие | Назначение |
|------|----------|------------|
| `processing/normalize.py` | Modify (строки 280-458) | Добавить сбор и сохранение brk/cap массива |
| `processing/label_main.py` | Modify (строки 334-340) | Передать output_base в normalize_rowwise для сохранения .npy |
| `statistics/signal_tracer.py` | Modify (строки 67-72, 260-270) | Загрузка updn_params_*.npy, денормализация через per-row brk/cap |
| `tests/test_inverse_piecewise.py` | Create | Тесты inverse transform: round-trip, edge cases |

---

## Контекст: как устроена нормализация updn

### Что происходит сейчас (`normalize.py:424-454`)

Для каждой строки `i`:
1. Собирается пул из **606 значений**: 100 фракталов × 6 полей updn (индексы 11-16) + 6 row-level таргетов (up_12..dn_48)
2. Из ненулевых значений пула: `brk = p85`, `cap = p99`
3. Все 606 значений + 6 таргетов нормализуются `piecewise_linear_log_transform(x, lo=0, brk, cap)`
4. **brk и cap теряются** — не сохраняются никуда

### Что нужно

Сохранять `brk[i]` и `cap[i]` для каждой строки в массив `(N, 2)` и записывать в `DATA/updn_params_{train,val,test}.npy`.

### Формула inverse (уже есть в signal_tracer.py:50-64)

```python
def inverse_piecewise_linear_log(y, brk, cap, linear_max=0.85, tail_strength=9.0):
    if y <= 0: return 0.0
    if y <= linear_max:
        return y / linear_max * brk   # lo=0 всегда для updn
    # Логарифмическая часть
    t_log = (y - linear_max) / (1.0 - linear_max)
    t = expm1(t_log * log1p(tail_strength)) / tail_strength
    return brk + t * (cap - brk)
```

---

### Task 1: Тест round-trip для inverse transform

**Files:**
- Create: `tests/test_inverse_piecewise.py`
- Read: `processing/normalize.py:208-253` (forward transform)
- Read: `statistics/signal_tracer.py:44-64` (inverse transform)

- [ ] **Step 1: Написать тест round-trip**

```python
"""Тесты inverse_piecewise_linear_log: round-trip forward→inverse."""
import numpy as np
import math


def piecewise_linear_log_transform(x, lo, brk, cap,
                                   linear_max=0.85, tail_strength=9.0, eps=1e-12):
    """Копия из normalize.py для тестирования без импорта всего модуля."""
    x = np.asarray(x, dtype=np.float64)
    denom_lin = max(brk - lo, eps)
    y_lin = np.clip((x - lo) / denom_lin, 0.0, 1.0) * linear_max
    denom_tail = max(cap - brk, eps)
    excess = np.maximum(x - brk, 0.0)
    t = np.clip(excess / denom_tail, 0.0, 1.0)
    log_part = np.log1p(tail_strength * t) / np.log1p(tail_strength + eps)
    y_tail = linear_max + (1.0 - linear_max) * log_part
    out = np.where(x <= brk, y_lin, y_tail)
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def inverse_piecewise_linear_log(y, brk, cap,
                                  linear_max=0.85, tail_strength=9.0):
    """Копия из signal_tracer.py."""
    if y <= 0:
        return 0.0
    if y <= linear_max:
        return y / linear_max * brk
    log_denom = math.log1p(tail_strength)
    t_log = (y - linear_max) / (1.0 - linear_max)
    t = (math.expm1(t_log * log_denom)) / tail_strength
    t = max(0.0, min(1.0, t))
    return brk + t * (cap - brk)


def test_round_trip_linear_zone():
    """Значения в линейной зоне [0, brk] должны восстанавливаться точно."""
    brk, cap = 20.0, 70.0
    originals = [0.0, 1.0, 5.0, 10.0, 15.0, 19.9]
    for x in originals:
        y = float(piecewise_linear_log_transform(np.array([x]), 0, brk, cap)[0])
        x_back = inverse_piecewise_linear_log(y, brk, cap)
        assert abs(x_back - x) < 0.01, f"x={x}, y={y}, x_back={x_back}"


def test_round_trip_log_zone():
    """Значения в логарифмической зоне (brk, cap] должны восстанавливаться."""
    brk, cap = 20.0, 70.0
    originals = [25.0, 35.0, 50.0, 65.0, 70.0]
    for x in originals:
        y = float(piecewise_linear_log_transform(np.array([x]), 0, brk, cap)[0])
        x_back = inverse_piecewise_linear_log(y, brk, cap)
        assert abs(x_back - x) < 0.1, f"x={x}, y={y}, x_back={x_back}"


def test_round_trip_beyond_cap():
    """Значения > cap клиппируются к 1.0, inverse даёт cap."""
    brk, cap = 20.0, 70.0
    y = float(piecewise_linear_log_transform(np.array([100.0]), 0, brk, cap)[0])
    assert y == 1.0
    x_back = inverse_piecewise_linear_log(y, brk, cap)
    assert abs(x_back - cap) < 0.01


def test_zero_stays_zero():
    """Нулевое значение остается нулем."""
    brk, cap = 20.0, 70.0
    y = float(piecewise_linear_log_transform(np.array([0.0]), 0, brk, cap)[0])
    assert y == 0.0
    x_back = inverse_piecewise_linear_log(y, brk, cap)
    assert x_back == 0.0


def test_round_trip_realistic_updn():
    """Round-trip с реалистичными brk/cap из статистики проекта."""
    # Из DATA/Nero_normalization_stats.csv (глобальные, но порядок величин верный)
    cases = [
        (19.2, 71.9, [0.0, 1.5, 4.3, 13.2, 19.2, 35.0, 71.9]),  # up_12
        (18.1, 73.8, [0.0, 2.8, 11.8, 18.1, 50.0, 73.8]),        # dn_12
    ]
    for brk, cap, values in cases:
        for x in values:
            y = float(piecewise_linear_log_transform(np.array([x]), 0, brk, cap)[0])
            x_back = inverse_piecewise_linear_log(y, brk, cap)
            assert abs(x_back - min(x, cap)) < 0.15, \
                f"brk={brk}, cap={cap}, x={x}, y={y}, x_back={x_back}"
```

- [ ] **Step 2: Запустить тест, убедиться что проходит**

Run: `cd /home/hohla/git/SoSimple && python -m pytest tests/test_inverse_piecewise.py -v`
Expected: 5 tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_inverse_piecewise.py
git commit -m "test: round-trip tests for inverse_piecewise_linear_log"
```

---

### Task 2: Сохранение brk/cap в normalize.py

**Files:**
- Modify: `processing/normalize.py:280-458`

**Суть изменения:** В `normalize_rowwise()` создать массив `updn_params = np.zeros((n_rows, 2))`, заполнять `updn_params[i] = [brk_updn, cap_updn]` в цикле, и вернуть его вызывающему коду.

- [ ] **Step 1: Написать тест для сохранения параметров**

Добавить в `tests/test_inverse_piecewise.py`:

```python
def test_normalize_rowwise_returns_updn_params():
    """normalize_rowwise должен возвращать (df, updn_params) при return_updn_params=True."""
    # Минимальный DataFrame: 1 строка, 100 фракталов
    import pandas as pd

    # Создаём строку с одним фракталом, у которого up_12=10.0
    fractal_str = "1700000000:1000.0:1:5.0:3.0:0:0:0:1.0:1:0.5:10.0:8.0:15.0:12.0:20.0:16.0:2.5"
    # Остальные 99 фракталов — с нулевыми updn
    empty_frac = "1699999000:999.0:1:2.0:1.0:0:0:0:0.5:0:0.3:0.0:0.0:0.0:0.0:0.0:0.0:2.0"

    cols = {'time': ['2025.01.01 00:00'], 'signal': [0], 'predict': [0.0], 'ATR': [2.5],
            'up_12': [10.0], 'dn_12': [8.0], 'up_24': [15.0], 'dn_24': [12.0],
            'up_48': [20.0], 'dn_48': [16.0]}
    for i in range(100):
        cols[f'fractal{i}'] = [fractal_str if i == 0 else empty_frac]

    df = pd.DataFrame(cols)

    from processing.normalize import normalize_rowwise
    result = normalize_rowwise(df, return_updn_params=True)

    assert isinstance(result, tuple) and len(result) == 2
    df_out, updn_params = result
    assert updn_params.shape == (1, 2)
    brk, cap = updn_params[0]
    assert brk > 0, f"brk должен быть > 0, got {brk}"
    assert cap >= brk, f"cap должен быть >= brk, got cap={cap}, brk={brk}"
```

- [ ] **Step 2: Запустить тест, убедиться что FAIL**

Run: `cd /home/hohla/git/SoSimple && python -m pytest tests/test_inverse_piecewise.py::test_normalize_rowwise_returns_updn_params -v`
Expected: FAIL — `normalize_rowwise` ещё не принимает `return_updn_params`

- [ ] **Step 3: Реализовать сохранение в normalize_rowwise**

В файле `processing/normalize.py`:

**3a.** Добавить параметр `return_updn_params` в сигнатуру:

```python
def normalize_rowwise(
    df: pd.DataFrame,
    stats_path: Optional[str] = None,
    debug: bool = False,
    piecewise_params: Optional[dict] = None,
    return_updn_params: bool = False        # ← NEW
) -> pd.DataFrame:
```

**3b.** После строки `updn_targets[col] = ...` (строка ~349), добавить:

```python
    # Массив для per-row параметров нормализации updn
    updn_params = np.zeros((n_rows, 2), dtype=np.float64)  # [brk, cap]
```

**3c.** Внутри цикла, после строки `cap_updn = max(cap_updn, brk_updn + eps)` (строка ~440), добавить:

```python
            updn_params[i] = [brk_updn, cap_updn]
```

**3d.** В конце функции (перед `return df`, строка ~504), заменить return:

```python
    if return_updn_params:
        return df, updn_params
    return df
```

- [ ] **Step 4: Запустить тест**

Run: `cd /home/hohla/git/SoSimple && python -m pytest tests/test_inverse_piecewise.py -v`
Expected: 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add processing/normalize.py tests/test_inverse_piecewise.py
git commit -m "feat(normalize): collect per-row brk/cap updn params"
```

---

### Task 3: Сохранение updn_params в label_main.py

**Files:**
- Modify: `processing/label_main.py:334-346`

**Суть:** При вызове `normalize_rowwise` запросить `return_updn_params=True`, после split на train/val/test сохранить `.npy` файлы.

- [ ] **Step 1: Модифицировать label_main.py**

Изменить строки 334-346:

```python
    # 4. Построчная нормализация (до split — каждая строка независима)
    updn_params = None
    if not args.no_normalize:
        labeled_df, updn_params = normalize_rowwise(
            labeled_df,
            stats_path=stats_path,
            debug=args.debug,
            return_updn_params=True
        )

    # 5. Разделяем на train/validation/test (70/15/15)
    train_df, val_df, test_df = split_train_val_test(labeled_df)

    # 6. Сохраняем файлы
    save_datasets(train_df, val_df, test_df, output_base)

    # 6b. Сохраняем per-row updn_params (brk, cap) для денормализации
    if updn_params is not None:
        n_total = len(labeled_df)
        n_train = len(train_df)
        n_val = len(val_df)
        np.save(str(output_base) + "_train_updn_params.npy", updn_params[:n_train])
        np.save(str(output_base) + "_validation_updn_params.npy", updn_params[n_train:n_train + n_val])
        np.save(str(output_base) + "_test_updn_params.npy", updn_params[n_train + n_val:])
        print(f"  updn_params: train={n_train}, val={n_val}, test={n_total - n_train - n_val}")
```

- [ ] **Step 2: Commit**

```bash
git add processing/label_main.py
git commit -m "feat(label_main): save per-row updn_params .npy after normalization"
```

- [ ] **Step 3: Перезапустить pipeline**

Run: `cd /home/hohla/git/SoSimple && python processing/label_main.py MT/MQL4/Files/Nero.csv`

Expected: В `DATA/` появятся:
- `Nero_train_updn_params.npy`
- `Nero_validation_updn_params.npy`
- `Nero_test_updn_params.npy`

Проверить: `python -c "import numpy as np; p=np.load('DATA/Nero_test_updn_params.npy'); print(p.shape, p[:3])"`
Expected: shape `(N, 2)`, значения brk ≈ 10-30, cap ≈ 50-150 (порядок пунктов)

---

### Task 4: Интеграция в signal_tracer.py

**Files:**
- Modify: `statistics/signal_tracer.py:67-72, 260-270`

**Суть:** Заменить текущую `denormalize_updn()` (глобальные p85/p99) на per-row inverse через загруженные `updn_params_*.npy`.

- [ ] **Step 1: Добавить загрузку updn_params**

В секцию загрузки данных (где загружаются labeled CSV и y_*_updn.npy), добавить:

```python
# Загрузка per-row updn параметров (brk, cap)
updn_params = {}
for prefix, path in [('train', 'DATA/Nero_train_updn_params.npy'),
                     ('val', 'DATA/Nero_validation_updn_params.npy'),
                     ('test', 'DATA/Nero_test_updn_params.npy')]:
    full_path = os.path.join(PROJECT_ROOT, path)
    if os.path.exists(full_path):
        updn_params[prefix] = np.load(full_path)
```

- [ ] **Step 2: Заменить denormalize_updn**

Текущий `denormalize_updn` (строки 67-72) использует глобальные p85/p99. Заменить на per-row:

```python
def denormalize_updn_row(y_norm_6, brk, cap):
    """Денормализация 6 значений updn (up_12..dn_48) для одной строки.

    Args:
        y_norm_6: массив из 6 нормализованных значений [up_12, dn_12, ..., dn_48]
        brk: per-row breakpoint (p85 ненулевых updn значений строки)
        cap: per-row cap (p99 ненулевых updn значений строки)
    Returns:
        массив из 6 денормализованных значений в пунктах
    """
    return np.array([inverse_piecewise_linear_log(float(y), brk, cap)
                     for y in y_norm_6])
```

- [ ] **Step 3: В build_dossier использовать per-row параметры**

Заменить строки 264-269 (чтение cols[104]/[105] + denormalize_updn) на:

```python
    # Ground truth: из y_*_updn.npy с per-row денормализацией
    if updn_entry is not None and params_entry is not None:
        brk, cap = params_entry
        vals = denormalize_updn_row(updn_entry, brk, cap)
        d['up_12'] = vals[0]
        d['dn_12'] = vals[1]
    else:
        d['up_12'] = 0.0
        d['dn_12'] = 0.0
```

Где `updn_entry = y_updn[row_idx]` (shape (6,)), `params_entry = updn_params[row_idx]` (shape (2,)) передаются в build_dossier.

- [ ] **Step 4: Обновить сигнатуру build_dossier**

Заменить `norm_stats=None` на `updn_entry=None, params_entry=None`:

```python
def build_dossier(target_time, signal_row, nero_cols, fractal, params,
                  mt4_trade=None, updn_entry=None, params_entry=None):
```

- [ ] **Step 5: Обновить вызовы build_dossier**

Найти все вызовы `build_dossier(...)` и передать `updn_entry` и `params_entry` из загруженных массивов по row_idx.

- [ ] **Step 6: Запуск и проверка**

Run: `cd /home/hohla/git/SoSimple && python statistics/signal_tracer.py --batch --top 5 --min-ratio 5.0`

Expected: В досье `up_12/dn_12` показывают **реальные пункты** (не 0.0 и не 0..1), категории TP_CLEAR/SL_CLEAR/BOTH_HIT/TIMEOUT распределяются осмысленно.

- [ ] **Step 7: Commit**

```bash
git add statistics/signal_tracer.py
git commit -m "feat(signal_tracer): per-row updn denormalization via brk/cap params"
```

---

### Task 5: Обновление документации и header

**Files:**
- Modify: `statistics/signal_tracer.py` (header)
- Modify: `docs/data_analysis/signal_tracer.py.md`

- [ ] **Step 1: Обновить header signal_tracer.py**

Убрать строку `DATA/y_{train,val,test}_updn.npy   (ground truth up_12/dn_12, нормализованные)`.
Добавить:
```
#     - DATA/Nero_*_updn_params.npy           (per-row brk/cap для денормализации)
#     - DATA/y_{train,val,test}_updn.npy      (ground truth up_12/dn_12, нормализованные)
```

Убрать из примечаний строку про `up_12/dn_12 в fractal[i][0] всегда 0; берутся из y_*_updn.npy + денормализация`.
Заменить на:
```
#   - up_12/dn_12: денормализация per-row через brk/cap из updn_params.npy
```

- [ ] **Step 2: Обновить signal_tracer.py.md**

Убрать предупреждение `⚠️ Статус: ground truth из y_*_updn.npy пока не денормализован`.
Обновить секцию входных данных — добавить `DATA/Nero_*_updn_params.npy`.

- [ ] **Step 3: Обновить CHANGELOG.md**

Добавить запись:
```markdown
## [2026-03-25] — Per-row денормализация updn через brk/cap

### Добавлено
- `processing/normalize.py`: параметр `return_updn_params` — возврат per-row brk/cap
- `processing/label_main.py`: сохранение `DATA/Nero_*_updn_params.npy`
- `statistics/signal_tracer.py`: загрузка updn_params, точная денормализация ground truth
- `tests/test_inverse_piecewise.py`: round-trip тесты inverse transform

### Изменено
- Формула денормализации: вместо глобальных p85/p99 → per-row brk/cap из 606 значений строки
- signal_tracer.py: classify_outcome теперь использует реальные пункты (не нормализованные 0..1)

### Результаты
- [заполнить после запуска: распределение TP_CLEAR/SL_CLEAR/BOTH_HIT/TIMEOUT]
```

- [ ] **Step 4: Commit**

```bash
git add statistics/signal_tracer.py docs/data_analysis/signal_tracer.py.md CHANGELOG.md
git commit -m "docs: update signal_tracer docs after updn denormalization"
```

---

## Верификация

1. **Round-trip тесты**: `pytest tests/test_inverse_piecewise.py -v` — все 6 PASS
2. **Pipeline**: `python processing/label_main.py MT/MQL4/Files/Nero.csv` — появились `*_updn_params.npy`
3. **Sanity check params**: `python -c "import numpy as np; p=np.load('DATA/Nero_test_updn_params.npy'); print('shape:', p.shape, 'brk mean:', p[:,0].mean(), 'cap mean:', p[:,1].mean())"` — brk ≈ 10-30, cap ≈ 50-150
4. **Signal tracer**: `python statistics/signal_tracer.py --batch --top 10 --min-ratio 5.0` — up_12/dn_12 в пунктах, осмысленная классификация
5. **From-log сверка**: `python statistics/signal_tracer.py --from-log MT/tester/logs/20260324.log --csv-out test_denorm.csv` — сравнить категории с mt4_result
