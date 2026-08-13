# Predictability Gate на сырых фрактальных полях — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить по методике `07b-predictability-gate.md`, несут ли сырые фрактальные поля (100 фракталов × live-safe поля) предсказательную силу для значимых торговых таргетов (направление и MFE за 12 баров), до какого-либо обучения моделей.

**Architecture:** Отдельный модуль `ML/predictability_gate_raw_fractals.py` (загрузка + разбор фрактальных строк каноническим порядком полей, RF-гейт с walk-forward CV и перестановочным тестом) + CLI-раннер `statistics/run_predictability_gate_raw_fractals.py` + unit-тесты. Таргеты берутся из уже размеченных `DATA/Nero_*_labeled.csv` (без джойна OHLC). Результат — JSON в `ML/reports/` и отчёт в `docs/reports/`.

**Tech Stack:** Python 3 (`.venv`), pandas, numpy, scikit-learn (RandomForestClassifier/Regressor, TimeSeriesSplit), pytest.

## Global Constraints

- Окружение: только `./.venv/bin/python` и `./.venv/bin/pytest` из корня проекта.
- Данные гейта: **train** (основной прогон); режим `--include-validation` (train+validation) доступен как fallback при недостатке мощности, по методике 07b «Данные гейта». `DATA/Nero_test_labeled.csv` / locked_test **не используются нигде**.
- Таргеты: `direction_12 = sign(ret_12_dir_atr)`, `mfe_12 = fav_12_atr` (оба уже в labeled CSV; проверка семантики — обязательная проверка Task 1). Чувствительность: H=24 (`ret_24_dir_atr`, `fav_24_atr`).
- Перестановок ≥ 199 (разрешение p_min = 1/(199+1) = 0.005), фиксированные seed'ы. Значение 199 заимствовано из MI-раздела методики 07b; отдельного минимума перестановок для RF-гейта методика не фиксирует — раскрыть это в отчёте.
- При дисбалансе классов дискретного таргета RF-классификатор создаётся с `class_weight='balanced'` (07b п.1); фактический полный список параметров RF и CV фиксируется в JSON и отчёте.
- Вердикт по 07b: **отклонять набор вправе только RF-гейт** (p ≥ 0.05 → FAIL); MI — опциональная диагностика после PASS.
- Multiple testing (07b «Обязательные проверки»): 4 основных таргета → поправка Бонферрони `alpha = 0.05 / 4`; подвыборочные прогоны — робастность-диагностика со статусом не выше `DIAGNOSTIC_ONLY`, в N не входят.
- FAIL по 07b «Критерии прохождения» подтверждается минимум 5 seeds RF до окончательного reject; смешанная картина вердиктов → статус `DIAGNOSTIC_ONLY`.
- Перестановки делаются перемешиванием таргета по времени (временной порядок признаков сохраняется); случайное перемешивание строк матрицы запрещено (walk-forward).
- Отчёт по шаблону `docs/reports/README.md` + research-first блок и раскрытия методологии 16.
- Коммиты локальные; `git push` запрещён.

## File Structure

| Файл | Ответственность |
|---|---|
| `ML/predictability_gate_raw_fractals.py` (создать) | Парсинг фрактальных строк, live-safe отбор полей, сборка матрицы признаков и таргетов, RF-гейт с перестановочным тестом |
| `statistics/run_predictability_gate_raw_fractals.py` (создать) | CLI: прогон гейта по таргетам/горизонтам, smoke-режим, запись JSON |
| `tests/test_predictability_gate_raw_fractals.py` (создать) | Unit-тесты парсинга, live-safe denylist, таргетов, перестановочного теста |
| `ML/reports/predictability_gate_raw_fractals*.json` (генерируется) | Артефакты результатов |
| `docs/reports/2026-08-12-predictability-gate-raw-fractals.md` (создать при закрытии) | Отчёт этапа |

---

### Task 1: Загрузка сырых фрактальных признаков и таргетов

**Применимая методика:**
- `03-feature-contract-leakage.md` — отбор только live-safe полей, denylist future-derived;
- `07b-predictability-gate.md` — состав данных гейта;
- `02-data-pipeline.md` — конвенция дедупликации `drop_duplicates('time', keep='last')`.

**Files:**
- Create: `ML/predictability_gate_raw_fractals.py`
- Test: `tests/test_predictability_gate_raw_fractals.py`

**Interfaces:**
- Consumes: `ML/fractal_level_feature_builder.FRACTAL_FIELDS` (канонический порядок 23 полей), `DATA/Nero_train_labeled.csv` / `DATA/Nero_validation_labeled.csv` (delimiter `;`).
- Produces:
  - `LIVE_SAFE_FRACTAL_FIELDS: tuple[str, ...]` = 12 полей: `('price','direction','front','back','strong','break','reverse','power','count','impulse','fractal_atr','shift')`;
  - `ROW_EXTRA_FEATURES: tuple[str, ...]` = `('ATR',)`;
  - `load_raw_fractal_gate_data(csv_paths: list[str]) -> dict` с ключами: `X` (np.ndarray float64, N×1201), `feature_names` (list[str], длины 1201: `f{slot}_{field}` для 100 слотов × 12 полей + `ATR`), `time` (np.ndarray str), `targets` (dict с `direction_12`, `mfe_12`, `direction_24`, `mfe_24` — np.ndarray), `n_raw`, `n_dedup_dropped`, `n_target_unpopulated_dropped` (строки с `signal == 0` без таргетов).

**Обязательные проверки (утверждаются тестами):**
- поля `up_3..dn_48` и `time` из фрактальных строк **исключены**. Обоснование: для свежего `fractal0` MFE/MAE от рождения уровня future-derived относительно `decision_time` (режим риска fresh fractal0 по методике 03, строка 138); план проверяет **консервативный** live-safe набор без updn целиком. Существующий контракт `ML/fractal_level_feature_builder.py::build_feature_contract` допускает `up_*/dn_*` для `idx > 0` как `historical_fractal_state` (`live_safe: True`); вариант гейта с updn для старых фракталов в этом плане не проверяется и раскрывается в отчёте как возможный follow-up при FAIL консервативного набора; проверка denylist в тесте;
- дедупликация по `time` с `keep='last'`, количество удалённых строк фиксируется; формат `time` валидируется (`pd.to_datetime` без NaT) до сортировки;
- **режим разметки таргетов (signal-based)**: в `DATA/Nero_*_labeled.csv` таргеты `ret_*_dir_atr`/`fav_*_atr` заполнены только для строк с `signal != 0` (эмпирически подтверждено на полном train: 10 487/44 159 = 23.75% строк; при `signal == 0` все четыре таргета равны 0 по построению `processing/label_signals.py::label_entry_path_targets`). Строки с `signal == 0` — структурные нули, а не «флэт», поэтому лоадер отфильтровывает их (`n_target_unpopulated_dropped` фиксируется), и вердикт гейта относится к подвыборке signal-строк. Раскрыть в отчёте: `signal` — future-derived поле (методика 03), здесь используется только как маска доступности таргетов, не как признак и не как candidate-фильтр;
- `ret_12_dir_atr` — непрерывная нормированная на ATR доходность за 12 баров (фактические границы на полном train: min=−18.0630, max=+19.5976, p1=−2.5, p99=5.22; для H=24: min=−22.8450, max=+34.4056); `fav_12_atr` ≥ 0 — благоприятное движение за 12 баров в ATR (max=27.12). Стоп и разбор — только при нефинитных значениях или `|value| > 100` (семантика таргетов не подтверждена); априорные границы не задаются.

- [ ] **Step 1: Написать падающие тесты**

`tests/test_predictability_gate_raw_fractals.py`:

```python
import numpy as np
import pandas as pd
import pytest

from ML.predictability_gate_raw_fractals import (
    LIVE_SAFE_FRACTAL_FIELDS,
    ROW_EXTRA_FEATURES,
    _parse_fractal_row,
    build_fractal_features,
    load_raw_fractal_gate_data,
)
from ML.fractal_level_feature_builder import FRACTAL_FIELDS


def _make_fractal_str(price: float = 2000.0, direction: int = 1,
                      up12: float = 3.0, shift: int = 4) -> str:
    parts = ['0.0'] * 23
    parts[FRACTAL_FIELDS['time']] = '1089140400'
    parts[FRACTAL_FIELDS['price']] = str(price)
    parts[FRACTAL_FIELDS['direction']] = str(direction)
    parts[FRACTAL_FIELDS['front']] = '0.5'
    parts[FRACTAL_FIELDS['back']] = '0.7'
    parts[FRACTAL_FIELDS['strong']] = '1'
    parts[FRACTAL_FIELDS['break']] = '0'
    parts[FRACTAL_FIELDS['reverse']] = '0'
    parts[FRACTAL_FIELDS['power']] = '0.9'
    parts[FRACTAL_FIELDS['count']] = '2'
    parts[FRACTAL_FIELDS['impulse']] = '0.1'
    parts[FRACTAL_FIELDS['up_12']] = str(up12)   # future-derived, must be excluded
    parts[FRACTAL_FIELDS['fractal_atr']] = '1.6'
    parts[FRACTAL_FIELDS['shift']] = str(shift)
    return ':'.join(parts)


def _make_df(n: int = 50) -> pd.DataFrame:
    times = pd.date_range('2020-01-01', periods=n, freq='h').strftime('%Y.%m.%d %H:%M')
    df = pd.DataFrame({'time': times})
    for k in range(100):
        df[f'fractal{k}'] = [_make_fractal_str(price=2000.0 + k)] * n
    df['ATR'] = 1.0
    df['signal'] = np.where(np.arange(n) % 2 == 0, 1, -1)   # все строки с таргетами
    df['ret_12_dir_atr'] = np.linspace(-2.0, 2.0, n)
    df['ret_24_dir_atr'] = np.linspace(-1.0, 1.0, n)
    df['fav_12_atr'] = np.linspace(0.0, 1.0, n)
    df['fav_24_atr'] = np.linspace(0.0, 2.0, n)
    return df


def test_live_safe_fields_exclude_future_derived():
    assert 'up_12' not in LIVE_SAFE_FRACTAL_FIELDS
    assert 'dn_48' not in LIVE_SAFE_FRACTAL_FIELDS
    assert 'time' not in LIVE_SAFE_FRACTAL_FIELDS
    assert len(LIVE_SAFE_FRACTAL_FIELDS) == 12


def test_updn_fields_known_but_excluded():
    # updn обязаны существовать в каноническом порядке полей, но не в live-safe наборе
    for f in ('up_3', 'dn_3', 'up_6', 'dn_6', 'up_12', 'dn_12',
              'up_24', 'dn_24', 'up_48', 'dn_48'):
        assert f in FRACTAL_FIELDS
        assert f not in LIVE_SAFE_FRACTAL_FIELDS


def test_parse_fractal_row_keeps_fractional_break():
    # break в labeled CSV нормализован: ~46-54% значений дробные — дробь сохраняется
    row = _make_fractal_str()
    parts = row.split(':')
    parts[FRACTAL_FIELDS['break']] = '0.8095238209'
    parsed = _parse_fractal_row(':'.join(parts))
    assert parsed is not None and abs(parsed['break'] - 0.8095238209) < 1e-9


def test_parse_fractal_row_rejects_fractional_int_like_field():
    # direction/strong/count integer-like: дробное значение = ошибка режима, fail-fast
    row = _make_fractal_str()
    parts = row.split(':')
    parts[FRACTAL_FIELDS['strong']] = '0.1700000018'
    with pytest.raises(ValueError):
        _parse_fractal_row(':'.join(parts))


def test_build_fractal_features_shape_and_exclusion():
    df = _make_df(10)
    X, names = build_fractal_features(df)
    assert X.shape == (10, 100 * 12 + 1)          # 1201 колонка
    assert names[-1] == 'ATR'
    expected = {f'fractal{k}_{f}' for k in range(100) for f in LIVE_SAFE_FRACTAL_FIELDS} | {'ATR'}
    assert set(names) == expected                 # покрывает up_*, dn_* и *_time разом
    # price fractal0 = 2000.0 попал в матрицу
    assert X[0, names.index('fractal0_price')] == 2000.0


def test_build_fractal_features_empty_string_is_zero():
    df = _make_df(5)
    df.loc[2, 'fractal7'] = ''
    X, names = build_fractal_features(df)
    assert X[2, names.index('fractal7_price')] == 0.0


def test_load_raw_fractal_gate_data_targets_and_dedup(tmp_path):
    df = _make_df(10)
    dup = df.iloc[[3]].copy()                      # дубль time -> keep last
    dup['fav_12_atr'] = 0.99
    df = pd.concat([df, dup]).reset_index(drop=True)
    path = tmp_path / 'mini.csv'
    df.to_csv(path, sep=';', index=False)
    out = load_raw_fractal_gate_data([str(path)])
    assert out['n_raw'] == 11 and out['n_dedup_dropped'] == 1
    assert out['X'].shape == (10, 1201)
    assert np.array_equal(out['targets']['direction_12'],
                          np.sign(np.linspace(-2.0, 2.0, 10)))
    # keep='last' заменяет значение в позиции 3 на 0.99, а не восстанавливает linspace
    expected_mfe = np.linspace(0.0, 1.0, 10)
    expected_mfe[3] = 0.99
    assert np.allclose(out['targets']['mfe_12'], expected_mfe)


def test_load_raw_fractal_gate_data_filters_unpopulated_signal_rows(tmp_path):
    df = _make_df(10)
    df.loc[7:, 'signal'] = 0                       # строки без таргетов (структурные нули)
    path = tmp_path / 'mini.csv'
    df.to_csv(path, sep=';', index=False)
    out = load_raw_fractal_gate_data([str(path)])
    assert out['n_target_unpopulated_dropped'] == 3
    assert out['X'].shape[0] == 7
```

- [ ] **Step 2: Запустить тесты — убедиться, что падают**

Run: `./.venv/bin/pytest tests/test_predictability_gate_raw_fractals.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'ML.predictability_gate_raw_fractals'`.

- [ ] **Step 3: Реализовать модуль**

`ML/predictability_gate_raw_fractals.py`:

```python
# =============================================================================
# Файл: predictability_gate_raw_fractals.py
# Назначение: Predictability gate по методике 07b на сырых фрактальных полях.
#             Загрузка Nero_*_labeled.csv, live-safe отбор полей фракталов,
#             RF-гейт с walk-forward CV и перестановочным тестом.
# Входные данные: DATA/Nero_train_labeled.csv, DATA/Nero_validation_labeled.csv
# Выходные данные: JSON через statistics/run_predictability_gate_raw_fractals.py
# Примечания: поля up_*/dn_*/time внутри фрактальных строк исключены —
#             консервативный live-safe набор относительно decision_time
#             (режим риска fresh fractal0; updn для idx>0 по контракту
#             fractal_level_feature_builder допускаются, но здесь не проверяются).
# =============================================================================

from __future__ import annotations

import numpy as np
import pandas as pd

from ML.fractal_level_feature_builder import FRACTAL_FIELDS

# Live-safe поля уровня. up_*/dn_* (MFE/MAE от рождения уровня) и time
# исключены: первые future-derived относительно decision_time для свежего
# fractal0 (консервативный выбор), второй избыточен при наличии shift.
LIVE_SAFE_FRACTAL_FIELDS: tuple[str, ...] = (
    'price', 'direction', 'front', 'back', 'strong', 'break',
    'reverse', 'power', 'count', 'impulse', 'fractal_atr', 'shift',
)
ROW_EXTRA_FEATURES: tuple[str, ...] = ('ATR',)
TARGET_COLUMNS = {
    'direction_12': 'ret_12_dir_atr',
    'direction_24': 'ret_24_dir_atr',
    'mfe_12': 'fav_12_atr',
    'mfe_24': 'fav_24_atr',
}
# 'break' НЕ входит: в labeled CSV он нормализован и дробный (~46-54% значений).
_INT_FIELDS = {'direction', 'strong', 'count'}


def _parse_fractal_row(value: object) -> dict[str, float] | None:
    if pd.isna(value) or str(value) == '':
        return None
    parts = str(value).split(':')
    if len(parts) != 23:
        return None
    out: dict[str, float] = {}
    for name in LIVE_SAFE_FRACTAL_FIELDS:
        raw = parts[FRACTAL_FIELDS[name]]
        if name in _INT_FIELDS:
            # integer-like поля: дробное значение = ошибка режима парсинга
            # (методика 03) — fail-fast вместо молчаливого trunc.
            if raw == '':
                out[name] = 0.0
                continue
            val = float(raw)
            if val != int(val):
                raise ValueError(
                    f'field {name!r} is fractional ({raw!r}): wrong parse mode '
                    f'(normalized data read by semantic parser contract, см. 03)'
                )
            out[name] = float(int(val))
        else:
            out[name] = float(raw) if raw != '' else 0.0
    return out


def build_fractal_features(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """Собирает матрицу 100 слотов x 12 live-safe полей + ROW_EXTRA_FEATURES."""
    fractal_cols = sorted(
        (c for c in df.columns if str(c).startswith('fractal')),
        key=lambda c: int(str(c).replace('fractal', '', 1)),
    )
    if len(fractal_cols) != 100:
        raise ValueError(f'expected 100 fractal columns, got {len(fractal_cols)}')

    blocks: list[np.ndarray] = []
    names: list[str] = []
    for col in fractal_cols:
        parsed = df[col].map(_parse_fractal_row)
        for field in LIVE_SAFE_FRACTAL_FIELDS:
            blocks.append(
                np.array([p[field] if p is not None else 0.0 for p in parsed], dtype=np.float64)
            )
            names.append(f'{col}_{field}')
    for col in ROW_EXTRA_FEATURES:
        blocks.append(pd.to_numeric(df[col], errors='coerce').fillna(0.0).to_numpy(np.float64))
        names.append(col)
    return np.column_stack(blocks), names


def load_raw_fractal_gate_data(csv_paths: list[str]) -> dict:
    """Загружает split'ы, дедуплицирует по time, строит признаки и таргеты."""
    frames = []
    n_raw = 0
    for path in csv_paths:
        df = pd.read_csv(path, delimiter=';')
        n_raw += len(df)
        frames.append(df)
    merged = pd.concat(frames, ignore_index=True)

    # Валидация формата time до сортировки: лексикографический порядок
    # корректен только для 'YYYY.MM.DD HH:MM'.
    parsed_time = pd.to_datetime(merged['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    if parsed_time.isna().any():
        bad = merged.loc[parsed_time.isna(), 'time'].head(5).tolist()
        raise ValueError(f'unparseable time values (expected YYYY.MM.DD HH:MM): {bad}')

    merged = merged.sort_values('time').drop_duplicates('time', keep='last').reset_index(drop=True)
    n_dedup_dropped = n_raw - len(merged)

    missing = [c for c in list(TARGET_COLUMNS.values()) + list(ROW_EXTRA_FEATURES) + ['signal']
               if c not in merged.columns]
    assert not missing, f'missing columns: {missing}'

    # Signal-based режим разметки: таргеты заполнены только при signal != 0
    # (label_entry_path_targets, use_fractal_dir=False). Строки с signal == 0 —
    # структурные нули; они исключаются, число фиксируется для отчёта.
    sig = pd.to_numeric(merged['signal'], errors='coerce').fillna(0)
    populated = sig != 0
    n_target_unpopulated_dropped = int((~populated).sum())
    merged = merged[populated].reset_index(drop=True)

    X, feature_names = build_fractal_features(merged)
    targets = {}
    for tname, col in TARGET_COLUMNS.items():
        vals = pd.to_numeric(merged[col], errors='coerce')
        if not np.isfinite(vals).all() or (vals.abs() > 100).any():
            raise ValueError(f'target {col}: non-finite or |value| > 100 — семантика не подтверждена')
        targets[tname] = (np.sign(vals) if tname.startswith('direction') else vals).to_numpy(np.float64)
    valid = np.isfinite(targets['mfe_12']) & np.isfinite(targets['direction_12'])
    return {
        'X': X[valid],
        'feature_names': feature_names,
        'time': merged['time'].to_numpy()[valid],
        'targets': {k: v[valid] for k, v in targets.items()},
        'n_raw': int(n_raw),
        'n_dedup_dropped': int(n_dedup_dropped),
        'n_target_unpopulated_dropped': n_target_unpopulated_dropped,
    }
```

- [ ] **Step 4: Запустить тесты — убедиться, что проходят**

Run: `./.venv/bin/pytest tests/test_predictability_gate_raw_fractals.py -q`
Expected: PASS (8 тестов).

- [ ] **Step 5: Коммит**

```bash
git add ML/predictability_gate_raw_fractals.py tests/test_predictability_gate_raw_fractals.py
git commit -m "feat: raw fractal gate data loader with live-safe field selection"
```

**Критерий завершения Task 1:** тесты зелёные; `LIVE_SAFE_FRACTAL_FIELDS` не содержит future-derived полей; на реальном train-CSV загрузка даёт матрицу 1201 колонок и фиксирует `n_dedup_dropped` (сверка с конвенцией MI-этапа: 6.33% для train, 2796 из 44159) и `n_target_unpopulated_dropped` (~76% строк без таргетов в signal-based режиме).

---

### Task 2: RF-гейт с walk-forward CV и перестановочным тестом

**Применимая методика:**
- `07b-predictability-gate.md` — параметры RF, walk-forward, перестановки ≥199, вердикт только по RF;
- `11-robustness.md` — permutation test;
- `06-temporal-split.md` — временной порядок, никакого перемешивания строк.

**Files:**
- Modify: `ML/predictability_gate_raw_fractals.py`
- Test: `tests/test_predictability_gate_raw_fractals.py`

**Interfaces:**
- Consumes: матрицу `X`, таргет `y` из Task 1.
- Produces:
  - `gate_score(X: np.ndarray, y: np.ndarray, discrete: bool, n_folds: int = 5, n_estimators: int = 100, max_depth: int = 10, n_jobs: int = -1, random_state: int = 42) -> tuple[float, list[float]]` — (средний CV-скор, скоры по фолдам). Метрика: `balanced_accuracy` для классификации (дисбаланс классов), `r2` для регрессии; CV — `TimeSeriesSplit(n_splits=n_folds)`; классификатор создаётся с `class_weight='balanced'` (07b п.1: дисбаланс классов target);
  - `sample_size_gate(y: np.ndarray, discrete: bool, n_folds: int) -> dict` — проверка размеров по методике `06-temporal-split.md`: для каждого фолда `TimeSeriesSplit` фиксирует минимальный размер train-части и минимальную численность класса в train-части (для discrete); пороги `min_fold_train_rows >= 1000` и `min_fold_train_class_count >= 100`; возвращает `{'passed': bool, 'min_fold_train_rows': int, 'min_fold_train_class_count': int | None, 'n_rows': int, 'event_rows_independent': False}` (последний флаг — раскрытие: строки событийного ряда не считаются независимыми автоматически, см. 06);
  - `run_rf_gate(X, y, discrete, n_permutations=199, n_folds=5, alpha=0.05, random_state=42, n_jobs=-1, confirm_seeds=5) -> dict` с ключами `real_score`, `fold_scores`, `perm_scores` (list), `p_value` (доля перестановок со скором ≥ реального; `(k+1)/(n_perm+1)`-коррекция), `verdict` (`PASS` при `p_value < alpha`, иначе `FAIL`; `UNKNOWN` при `n_permutations < 199`), `alpha` (фактический порог с поправкой Бонферрони, передаётся раннером как `0.05 / n_targets`), `status` (`OK` либо `DIAGNOSTIC_ONLY` при непройденном sample_size_gate или смешанной картине seed-вердиктов), `sample_size_gate` (dict выше), `rf_params` (полный фактический список параметров RF и CV: `n_estimators`, `max_depth`, `n_jobs`, `random_state`, `class_weight`, `n_folds` — 07b п.3 «Фиксация результата»), `n_samples`, `n_features`, `n_permutations`, `discrete`, `metric`;
  - multi-seed подтверждение FAIL (07b «Критерии прохождения»): при `verdict == 'FAIL'` и `confirm_seeds >= 2` гейт перезапускается с `confirm_seeds` разными `random_state` (базовый + сдвиги 1000·i), результаты — в `verdict_by_seed: {seed: verdict}`; итог: большинство FAIL → `verdict='FAIL'`; большинство PASS → `verdict='PASS'`; смешанная картина → `status='DIAGNOSTIC_ONLY'` (verdict остаётся FAIL, окончательный reject запрещён);
  - Перестановка: `rng = np.random.default_rng(seed); y_perm = rng.permutation(y)` — таргент перемешивается целиком по обучающим строкам, признаки и их порядок не трогаются.

**Обязательные проверки:**
- CV временной (`TimeSeriesSplit`), не `KFold` с shuffle;
- p-value с коррекцией `(k+1)/(n_perm+1)` (никогда не ровно 0);
- порог вердикта — `alpha` с поправкой на число одновременных проверок (Бонферрони, 07b «Обязательные проверки»);
- при `n_permutations=0` поле `p_value=None`, вердикт `UNKNOWN` (конвенция MI-этапа);
- детерминизм по seed (сравнение скор через `np.allclose`, не побитовое — параллельная редукция RF с `n_jobs=-1` недетерминирована по битам);
- sample_size_gate посчитан и раскрыт; при `passed=False` статус не выше `DIAGNOSTIC_ONLY`;
- при FAIL — multi-seed подтверждение (≥5 seeds) до окончательного reject;
- как консервативная робастность-диагностика допустим block-permutation фон (блоки по 10–20 последовательных строк, см. `11-robustness.md`) — опционально, в отчёте помечать как диагностику.

- [ ] **Step 1: Написать падающие тесты**

Дополнить `tests/test_predictability_gate_raw_fractals.py`:

```python
from ML.predictability_gate_raw_fractals import gate_score, run_rf_gate


def _signal_xy(n=400, discrete=True, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 6))
    y_cont = X[:, 0] * 2.0 + rng.normal(scale=0.1, size=n)
    if discrete:
        return X, np.sign(y_cont)
    return X, y_cont


def test_gate_score_detects_signal():
    X, y = _signal_xy(discrete=True)
    score, folds = gate_score(X, y, discrete=True, n_folds=3)
    assert score > 0.8 and len(folds) == 3


def test_run_rf_gate_pass_on_signal():
    X, y = _signal_xy(discrete=False)
    res = run_rf_gate(X, y, discrete=False, n_permutations=19, n_folds=3)
    assert res['p_value'] <= 0.1 and res['verdict'] == 'UNKNOWN'  # <199 перестановок
    res = run_rf_gate(X, y, discrete=False, n_permutations=199, n_folds=3)
    assert res['verdict'] == 'PASS' and res['p_value'] < 0.05


def test_run_rf_gate_fail_on_noise():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(400, 6))
    y = rng.normal(size=400)
    res = run_rf_gate(X, y, discrete=False, n_permutations=199, n_folds=3, random_state=7)
    assert res['verdict'] == 'FAIL' and res['p_value'] >= 0.05


def test_run_rf_gate_zero_permutations_unknown():
    X, y = _signal_xy(discrete=True)
    res = run_rf_gate(X, y, discrete=True, n_permutations=0, n_folds=3)
    assert res['p_value'] is None and res['verdict'] == 'UNKNOWN'


def test_run_rf_gate_deterministic():
    X, y = _signal_xy(discrete=False, seed=3)
    a = run_rf_gate(X, y, discrete=False, n_permutations=9, n_folds=3, confirm_seeds=1)
    b = run_rf_gate(X, y, discrete=False, n_permutations=9, n_folds=3, confirm_seeds=1)
    # np.allclose, не ==: параллельная редукция RF (n_jobs=-1) недетерминирована по битам
    assert np.allclose(np.asarray(a['perm_scores']), np.asarray(b['perm_scores']))


def test_gate_score_three_class_with_zero():
    # реальный таргет direction_12 трёхклассовый: {-1, 0, +1}
    X, y = _signal_xy(n=600, discrete=True, seed=5)
    y[::5] = 0.0
    score, folds = gate_score(X, y, discrete=True, n_folds=3)
    assert np.isfinite(score) and len(folds) == 3


def test_run_rf_gate_fail_confirmation_multi_seed():
    rng = np.random.default_rng(2)
    X = rng.normal(size=(300, 6))
    y = rng.normal(size=300)
    res = run_rf_gate(X, y, discrete=False, n_permutations=199, n_folds=3,
                      random_state=11, confirm_seeds=5)
    assert res['verdict'] == 'FAIL'
    assert 'verdict_by_seed' in res and len(res['verdict_by_seed']) == 5
    assert res['status'] in ('OK', 'DIAGNOSTIC_ONLY')
```

- [ ] **Step 2: Запустить — убедиться, что падают**

Run: `./.venv/bin/pytest tests/test_predictability_gate_raw_fractals.py -q`
Expected: FAIL — `ImportError: cannot import name 'gate_score'`.

- [ ] **Step 3: Реализовать RF-гейт**

Дополнить `ML/predictability_gate_raw_fractals.py`:

```python
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import balanced_accuracy_score, r2_score
from sklearn.model_selection import TimeSeriesSplit


def _make_model(discrete: bool, n_estimators: int, max_depth: int,
                n_jobs: int, random_state: int):
    cls = RandomForestClassifier if discrete else RandomForestRegressor
    kwargs = dict(n_estimators=n_estimators, max_depth=max_depth,
                  n_jobs=n_jobs, random_state=random_state)
    if discrete:
        kwargs['class_weight'] = 'balanced'   # 07b п.1: дисбаланс классов target
    return cls(**kwargs)


def gate_score(X: np.ndarray, y: np.ndarray, discrete: bool, n_folds: int = 5,
               n_estimators: int = 100, max_depth: int = 10,
               n_jobs: int = -1, random_state: int = 42) -> tuple[float, list[float]]:
    fold_scores: list[float] = []
    for tr_idx, te_idx in TimeSeriesSplit(n_splits=n_folds).split(X):
        model = _make_model(discrete, n_estimators, max_depth, n_jobs, random_state)
        model.fit(X[tr_idx], y[tr_idx])
        pred = model.predict(X[te_idx])
        if discrete:
            fold_scores.append(balanced_accuracy_score(y[te_idx], pred))
        else:
            fold_scores.append(r2_score(y[te_idx], pred))
    return float(np.mean(fold_scores)), fold_scores


def sample_size_gate(y: np.ndarray, discrete: bool, n_folds: int) -> dict:
    """Пороги по 06-temporal-split.md: train-часть каждого фолда >= 1000 строк,
    для discrete — >= 100 наблюдений каждого класса в train-части каждого фолда."""
    splits = list(TimeSeriesSplit(n_splits=n_folds).split(y))
    min_train = min(len(tr) for tr, _ in splits)
    info: dict = {'n_rows': int(len(y)),
                  'min_fold_train_rows': int(min_train),
                  'min_fold_train_class_count': None,
                  'event_rows_independent': False}
    if discrete:
        classes = np.unique(y)
        info['min_fold_train_class_count'] = int(
            min(int(np.sum(y[tr] == c)) for tr, _ in splits for c in classes)
        )
        info['passed'] = bool(min_train >= 1000 and info['min_fold_train_class_count'] >= 100)
    else:
        info['passed'] = bool(min_train >= 1000)
    return info


def run_rf_gate(X: np.ndarray, y: np.ndarray, discrete: bool,
                n_permutations: int = 199, n_folds: int = 5, alpha: float = 0.05,
                random_state: int = 42, n_jobs: int = -1,
                confirm_seeds: int = 5) -> dict:
    rf_params = {'n_estimators': 100, 'max_depth': 10, 'n_jobs': n_jobs,
                 'random_state': random_state,
                 'class_weight': 'balanced' if discrete else None,
                 'n_folds': n_folds}
    size_gate = sample_size_gate(y, discrete, n_folds)
    real_score, fold_scores = gate_score(X, y, discrete, n_folds=n_folds,
                                         n_jobs=n_jobs, random_state=random_state)
    base = {'real_score': real_score, 'fold_scores': fold_scores,
            'n_samples': int(len(y)), 'n_features': int(X.shape[1]),
            'n_permutations': n_permutations, 'discrete': discrete,
            'metric': 'balanced_accuracy' if discrete else 'r2',
            'alpha': alpha, 'rf_params': rf_params,
            'sample_size_gate': size_gate,
            'status': 'OK' if size_gate['passed'] else 'DIAGNOSTIC_ONLY'}
    if n_permutations == 0:
        return {**base, 'perm_scores': [], 'p_value': None, 'verdict': 'UNKNOWN'}
    perm_scores: list[float] = []
    for i in range(n_permutations):
        rng = np.random.default_rng(random_state + i)
        score, _ = gate_score(X, rng.permutation(y), discrete, n_folds=n_folds,
                              n_jobs=n_jobs, random_state=random_state)
        perm_scores.append(score)
    k = int(np.sum(np.asarray(perm_scores) >= real_score))
    p_value = (k + 1) / (n_permutations + 1)
    verdict = 'PASS' if p_value < alpha else 'FAIL'
    if n_permutations < 199:
        verdict = 'UNKNOWN'
    result = {**base, 'perm_scores': perm_scores, 'p_value': p_value, 'verdict': verdict}

    # 07b «Критерии прохождения»: FAIL на выборке подтверждается >= 5 seeds
    # до окончательного reject.
    if verdict == 'FAIL' and confirm_seeds >= 2:
        verdict_by_seed: dict[int, str] = {}
        for i in range(confirm_seeds):
            seed = random_state + 1000 * i
            sub = run_rf_gate(X, y, discrete, n_permutations=n_permutations,
                              n_folds=n_folds, alpha=alpha, random_state=seed,
                              n_jobs=n_jobs, confirm_seeds=1)
            verdict_by_seed[seed] = sub['verdict']
        n_fail = sum(1 for v in verdict_by_seed.values() if v == 'FAIL')
        n_pass = sum(1 for v in verdict_by_seed.values() if v == 'PASS')
        result['verdict_by_seed'] = {str(s): v for s, v in verdict_by_seed.items()}
        if n_fail > n_pass:
            result['verdict'] = 'FAIL'
        elif n_pass > n_fail:
            result['verdict'] = 'PASS'
        else:
            result['status'] = 'DIAGNOSTIC_ONLY'   # смешанная картина — не reject
    return result
```

- [ ] **Step 4: Запустить тесты — убедиться, что проходят**

Run: `./.venv/bin/pytest tests/test_predictability_gate_raw_fractals.py -q`
Expected: PASS (15 тестов).

- [ ] **Step 5: Коммит**

```bash
git add ML/predictability_gate_raw_fractals.py tests/test_predictability_gate_raw_fractals.py
git commit -m "feat: RF predictability gate with walk-forward CV and permutation test"
```

**Критерий завершения Task 2:** тесты зелёные; на синтетике гейт отличает сигнал от шума; p-value с `(k+1)/(n+1)`-коррекцией; детерминизм по seed.

---

### Task 3: CLI-раннер и основные прогоны

**Применимая методика:**
- `07b-predictability-gate.md` — данные гейта (train; train+validation как fallback), фиксация результатов;
- `16-reporting-audit.md` — сохранение артефактов.

**Files:**
- Create: `statistics/run_predictability_gate_raw_fractals.py`
- Test: `tests/test_predictability_gate_raw_fractals.py` (smoke-тест раннера)

**Interfaces:**
- Consumes: `load_raw_fractal_gate_data`, `run_rf_gate` из Tasks 1–2.
- Produces: JSON `ML/reports/predictability_gate_raw_fractals.json` со структурой `{meta: {...}, gates: {<target>_<H>: {результат run_rf_gate + gate_data, subsample_p_value, subsample_verdict}}}`.

**Обязательные проверки:**
- smoke-режим (`--smoke`) работает на первых 3000 строк с `--n-permutations 9`;
- в JSON фиксируются: данные гейта (`train` или `train+validation`), границы периода, `n_raw`/`n_dedup_dropped`/`n_target_unpopulated_dropped`, число перестановок, метрика, `alpha` и `n_tests`;
- multiple testing: `n_tests = len(TARGETS)` (4 основных таргета), `alpha = 0.05 / n_tests` передаётся в `run_rf_gate`; подвыборочные прогоны — робастность-диагностика, в N не входят и интерпретируются со статусом не выше `DIAGNOSTIC_ONLY`;
- робастность к перекрытию горизонтов: для каждого таргета считается повторный гейт на подвыборке, разреженной **по времени** (`time_thin_mask`: сохраняются строки, отстоящие от последней сохранённой минимум на H часов; строки событийного ряда не равноотстоящи, поэтому stride по индексу `X[::H]` не эквивалентен H барам) — `subsample_p_value`; расхождение основного и подвыборочного вердиктов фиксируется в JSON.

- [ ] **Step 1: Написать падающий тест smoke-раннера**

```python
import json
import subprocess


def test_runner_smoke(tmp_path):
    out = tmp_path / 'out.json'
    proc = subprocess.run(
        ['./.venv/bin/python', 'statistics/run_predictability_gate_raw_fractals.py',
         '--smoke', '--n-permutations', '9', '--output', str(out)],
        capture_output=True, text=True, cwd='.',
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    data = json.loads(out.read_text())
    assert set(data['gates']) == {'direction_12', 'mfe_12', 'direction_24', 'mfe_24'}
    for gate in data['gates'].values():
        assert gate['n_permutations'] == 9 and gate['verdict'] == 'UNKNOWN'
        assert gate['gate_data'] in ('train', 'train+validation')
```

- [ ] **Step 2: Запустить — убедиться, что падает**

Run: `./.venv/bin/pytest tests/test_predictability_gate_raw_fractals.py::test_runner_smoke -q`
Expected: FAIL (раннер не существует).

- [ ] **Step 3: Реализовать раннер**

`statistics/run_predictability_gate_raw_fractals.py`:

```python
# =============================================================================
# Файл: run_predictability_gate_raw_fractals.py
# Назначение: CLI-прогон predictability gate (методика 07b) на сырых
#             фрактальных полях Nero_*_labeled.csv.
# Использование:
#   ./.venv/bin/python statistics/run_predictability_gate_raw_fractals.py
#   ./.venv/bin/python statistics/run_predictability_gate_raw_fractals.py --smoke
#   ./.venv/bin/python statistics/run_predictability_gate_raw_fractals.py \
#       --include-validation --n-permutations 199
# =============================================================================

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ML.predictability_gate_raw_fractals import (  # noqa: E402
    load_raw_fractal_gate_data, run_rf_gate,
)

TRAIN = 'DATA/Nero_train_labeled.csv'
VALIDATION = 'DATA/Nero_validation_labeled.csv'
TARGETS = {'direction_12': 12, 'mfe_12': 12, 'direction_24': 24, 'mfe_24': 24}


def time_thin_mask(time_strs: np.ndarray, horizon_hours: int) -> np.ndarray:
    """Разреживание по времени: строка сохраняется, если от последней
    сохранённой прошло >= horizon_hours. Строки событийного ряда
    не равноотстоящи, поэтому stride по индексу неприменим (см. 06, B1 аудита)."""
    t = pd.to_datetime(pd.Series(np.asarray(time_strs)), format='%Y.%m.%d %H:%M')
    hours = (t.astype('int64') // 10**9 / 3600.0).to_numpy()
    keep = np.zeros(len(hours), dtype=bool)
    last = -np.inf
    for i, v in enumerate(hours):
        if v - last >= horizon_hours:
            keep[i] = True
            last = v
    return keep


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--include-validation', action='store_true')
    ap.add_argument('--n-permutations', type=int, default=199)
    ap.add_argument('--n-folds', type=int, default=5)
    ap.add_argument('--output', default='ML/reports/predictability_gate_raw_fractals.json')
    args = ap.parse_args()

    paths = [TRAIN] + ([VALIDATION] if args.include_validation else [])
    data = load_raw_fractal_gate_data(paths)
    X, targets = data['X'], data['targets']
    if args.smoke:
        X, targets = X[:3000], {k: v[:3000] for k, v in targets.items()}
    gate_data = 'train+validation' if args.include_validation else 'train'

    n_tests = len(TARGETS)                 # multiple testing: только основные таргеты
    alpha = 0.05 / n_tests                 # Бонферрони (07b «Обязательные проверки»)

    gates = {}
    for tname, horizon in TARGETS.items():
        y = targets[tname]
        discrete = tname.startswith('direction')
        gate = run_rf_gate(X, y, discrete, n_permutations=args.n_permutations,
                           n_folds=args.n_folds, alpha=alpha)
        gate['gate_data'] = gate_data
        mask = time_thin_mask(data['time'][:len(X)], horizon)
        sub = run_rf_gate(X[mask], y[mask], discrete,
                          n_permutations=args.n_permutations, n_folds=args.n_folds,
                          alpha=alpha)
        gate['subsample_method'] = f'time_thin>={horizon}h'
        gate['subsample_n'] = int(mask.sum())
        gate['subsample_p_value'] = sub['p_value']
        gate['subsample_verdict'] = sub['verdict']
        gate['subsample_status'] = 'DIAGNOSTIC_ONLY'   # робастность, не основной вердикт
        gates[tname] = gate
        print(f"{tname}: score={gate['real_score']:.4f} p={gate['p_value']} "
              f"verdict={gate['verdict']} (subsample p={sub['p_value']})")

    result = {
        'meta': {
            'gate_data': gate_data,
            'csv_paths': paths,
            'n_raw': data['n_raw'],
            'n_dedup_dropped': data['n_dedup_dropped'],
            'n_target_unpopulated_dropped': data['n_target_unpopulated_dropped'],
            'n_samples': int(len(X)),
            'n_features': int(X.shape[1]),
            'time_range': [str(data['time'][0]), str(data['time'][-1])],
            'n_permutations': args.n_permutations,
            'n_folds': args.n_folds,
            'n_tests': n_tests,
            'alpha': alpha,
            'multiple_testing': 'Bonferroni по основным таргетам; подвыборки — диагностика',
        },
        'gates': gates,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, default=str))
    print(f'saved: {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

- [ ] **Step 4: Запустить smoke и тесты**

Run: `./.venv/bin/pytest tests/test_predictability_gate_raw_fractals.py -q`
Expected: PASS (16 тестов).

- [ ] **Step 5: Основной прогон — train, 199 перестановок**

Run: `./.venv/bin/python statistics/run_predictability_gate_raw_fractals.py`
Expected: JSON создан; в stdout 4 строки с вердиктами. Ожидаемое время: часы (200 фитов RF × 4 таргета × 2 с подвыборкой; при вердикте FAIL добавляется multi-seed подтверждение — до ×6 на таргет). Если время неприемлемо — запуск в фоне, но не сокращать перестановки ниже 199.

- [ ] **Step 6: Fallback при недостатке мощности**

Если вердикт какого-либо таргета `FAIL` с p в пограничной зоне (0.05–0.20), повторить с `--include-validation` (по методике 07b «Данные гейта») и сохранить как `..._trainval.json`.

- [ ] **Step 7: Коммит**

```bash
git add statistics/run_predictability_gate_raw_fractals.py tests/test_predictability_gate_raw_fractals.py
git commit -m "feat: CLI runner for raw fractal predictability gate"
```

**Критерий завершения Task 3:** smoke зелёный; основной прогон завершён; JSON содержит все раскрытия (данные гейта, дедупликация, перестановки, подвыборочная робастность).

---

### Task 4: MI-диагностика по топ-признакам (только при PASS)

**Применимая методика:**
- `07b-predictability-gate.md` — MI опционален, не вправе отклонять набор, только после PASS RF-гейта.

**Files:**
- Modify: `statistics/run_predictability_gate_raw_fractals.py`
- Test: `tests/test_predictability_gate_raw_fractals.py`

**Interfaces:**
- Consumes: `statistics/mi_upper_bound.py::estimate_mi_per_feature` и `estimate_mi` (существующие, проверенные в MI-этапе). Модуль лежит в `statistics/` и не является пакетом (конфликт имени со stdlib `statistics`), поэтому загружается через `importlib.util.spec_from_file_location` — тот же приём, что в `tests/test_mi_upper_bound.py`; обычный `from statistics.mi_upper_bound import ...` не сработает; важности RF последнего гейта.
- Produces: ключ `mi_top` в JSON: для каждого PASS-таргета маргинальное MI топ-20 фич по RF-важности — **только bits** (`estimate_mi_per_feature` не возвращает per-feature p-value, см. сигнатуру `statistics/mi_upper_bound.py:181`); плюс `mi_set_p_value` — агрегированный перестановочный p-value (`estimate_mi`, `n_permutations >= 200`) на подмножестве этих топ-N фич. Per-feature p-value не обещается и не фабрикуется; при необходимости — отдельный дорогой follow-up (200 перестановок × 20 фич).

**Обязательные проверки:**
- MI считается только для таргетов с вердиктом PASS (задача пропускается целиком, если PASS нет);
- топ-фичи берутся из `feature_importances_` RF, обученного на данных гейта (добавить возврат в `gate_score` или отдельный фит);
- перед MI — z-score по данным гейта (методика 07b).

- [ ] **Step 1: Расширить `gate_score` возвратом важностей** — добавить опциональный параметр `return_importances: bool = False` и в этом случае возвращать `(score, folds, importances)`; обновить тесты Task 2 соответственно.
- [ ] **Step 2: Добавить флаг `--mi-top 20` в раннер:** загрузить модуль через `importlib.util.spec_from_file_location('mi_upper_bound', Path('statistics/mi_upper_bound.py'))` (как в `tests/test_mi_upper_bound.py`); для каждого PASS-таргета обучить RF на всех данных гейта, взять топ-N по `feature_importances_`, посчитать `estimate_mi_per_feature` на этих колонках (z-score предварительно) — в JSON фиксируется `mi_top` только с bits; затем `estimate_mi(..., n_permutations=200)` на том же топ-N подмножестве — в JSON фиксируется `mi_set_p_value`.
- [ ] **Step 3: Прогнать** `./.venv/bin/python statistics/run_predictability_gate_raw_fractals.py --mi-top 20` поверх готового основного прогона (или отдельным запуском с тем же seed).
- [ ] **Step 4: Коммит**

```bash
git add statistics/run_predictability_gate_raw_fractals.py ML/predictability_gate_raw_fractals.py tests/test_predictability_gate_raw_fractals.py
git commit -m "feat: optional MI diagnostics for top RF features in gate"
```

**Критерий завершения Task 4:** при PASS-таргетах в JSON есть `mi_top` (bits по каждой фиче) и `mi_set_p_value`; при отсутствии PASS блок честно отсутствует (не «нули»).

---

### Task 5: Отчёт и закрытие этапа

**Применимая методика:**
- `docs/reports/README.md` — 14 обязательных элементов отчёта;
- `16-reporting-audit.md` — research-first блок (`lifecycle_status`, `origin_bias`, `research_priority`, бюджеты, `allowed_max_verdict`), Multiple Testing Context, Validation Split Disclosure;
- `A4-verdicts-stop-conditions.md` — формулировка вердиктов;
- скилл `stage-reporting` — синхронизация CHANGELOG / CONTEXT_HANDOFF / MODULE_INDEX / wiki / docs-страницы + коммит файлов этапа.

**Files:**
- Create: `docs/reports/2026-08-12-predictability-gate-raw-fractals.md` (дату взять фактическую на момент закрытия)
- Modify: `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `MODULE_INDEX.md`, `wiki/*` (по скиллу stage-reporting)

**Обязательные проверки и раскрытия в отчёте:**
- данные гейта (train или train+validation) и обоснование выбора;
- дедупликация, фильтрация строк без таргетов (`n_target_unpopulated_dropped`) и размеры выборок;
- число перестановок и минимально достижимое p; раскрыть, что 199 перестановок для RF-гейта заимствовано из MI-раздела 07b (отдельного RF-минимума методика не задаёт);
- робастность к перекрытию горизонтов (основной vs подвыборочный вердикт по каждому таргету; метод подвыборки — разрежение по времени, подвыборки — `DIAGNOSTIC_ONLY`);
- MFE интерпретирован как верхняя оценка «забираемого» движения, не как фиксируемая прибыль;
- Multiple Testing Context: `n_tests = 4` основных таргета, применена поправка Бонферрони `alpha = 0.05/4`; раскрыть вердикты с поправкой и без (без поправки статус не выше `DIAGNOSTIC_ONLY`, 07b);
- распределение вердиктов по seeds при FAIL-подтверждении (`verdict_by_seed`) и статус `DIAGNOSTIC_ONLY` при смешанной картине;
- результат sample_size_gate по фолдам и классам; при непрохождении — статус не выше `DIAGNOSTIC_ONLY`;
- отсутствие embargo между фолдами TimeSeriesSplit: таргет с горизонтом 12 баров пересекает границы фолдов, скоры могут быть слегка оптимистичны; embargo не применяется, раскрыть как ограничение (по 06 п.4 для внутренних CV-границ допустимо письменное обоснование вместо embargo);
- вердикт гейта относится к подвыборке signal-строк (signal-based режим разметки); `signal` — future-derived поле, использовано только как маска доступности таргетов;
- проверялся консервативный live-safe набор без updn; контракт `fractal_level_feature_builder.build_feature_contract` допускает updn для `idx > 0` — этот вариант не проверялся (follow-up при FAIL);
- если вердикт FAIL: не «сигнала нет», а «не обнаружено» + анализ мощности (по образцу MI-этапа).

- [ ] **Step 1: Написать отчёт** по шаблону `docs/reports/README.md`, все числа — только из JSON-артефактов (сверка отчёт↔JSON по методологии 16).
- [ ] **Step 2: Прогнать скилл `stage-reporting`** — синхронизация CHANGELOG/CONTEXT_HANDOFF/MODULE_INDEX/wiki, docs-страницы новых модулей, коммит файлов этапа.
- [ ] **Step 3: Финальная проверка** — `./.venv/bin/pytest tests/test_predictability_gate_raw_fractals.py -q` зелёные; `git status` чистый по файлам этапа.

**Критерий завершения Task 5:** отчёт содержит все обязательные элементы и раскрытия; синхронизация выполнена; всё закоммичено локально (без push).

---

## Неизвестное и вопросы (явные допущения плана)

1. **Live-safe статус сырых полей** — утверждается по построению (факты: поля уровня фиксируются при рождении фрактала в прошлом; `up_*/dn_*` внутри строки исключены как консервативный выбор относительно `decision_time`). Формального аудита по методике 03 для этого набора раньше не проводилось — проверка denylist в Task 1 является этим аудитом; если при ревью возникнут сомнения по отдельным полям (например `reverse`), они исключаются до прогонов.
2. **Время основного прогона** — оценка «часы» не проверена (1201 фича × ~10 500 signal-строк × ~2000 фитов на таргет, плюс multi-seed подтверждение FAIL). Если прогон оказывается неприемлемо долгим, легитимные сокращения: `n_estimators=100→` оставить, `n_folds=5→` оставить; сокращать перестановки ниже 199 нельзя (теряется разрешение p). Альтернатива — запуск в фоне.
3. **Нули в direction_12** — после фильтрации signal-строк нули почти исчезают (остаточные ~0.7%: строки с `signal != 0`, но `ret_12_dir_atr == 0`); метрика `balanced_accuracy` трёхклассовость выдерживает, распределение классов фиксируется в отчёте.
4. **`fav_12_atr` vs entry-based Up/Dn** — взят row-based таргет из labeled CSV (простота, без OHLC-джойна). Режим разметки подтверждён эмпирически: signal-based (`label_entry_path_targets` с `use_fractal_dir=False`) — таргеты заполнены только при `signal != 0` (23.75% строк train); при `use_fractal_dir=True` таргеты были бы на всех строках, но в фактическом CSV это не так. Entry-based таргеты (`3.2` в A8) признаны валидными, но сигнала в той ветке ранее не найдено; при желании сравнить — отдельный follow-up, в этот план не входит.
5. **Embargo между фолдами CV** — не применяется; пересечение таргета (12 баров) с границами фолдов раскрывается в отчёте как ограничение (скоры слегка оптимистичны). Вопрос аудита Q2 закрыт раскрытием; добавление embargo — возможный follow-up.
6. **Row-level time vs fractal time** (вопрос аудита Q4) — разрешён по построению: сортировка и дедупликация используют row-level колонку `time` из заголовка CSV; поле `time` внутри фрактальных строк не читается (исключено из `LIVE_SAFE_FRACTAL_FIELDS`). Валидация формата row-level `time` добавлена в лоадер (Task 1).

## Self-review notes

- Спека диалога: RF-гейт обязателен, MI опционален после PASS, train(+validation), H=12 основной/H=24 чувствительность, нормализация только для MI, робастность к перекрытию — всё покрыто задачами 1–4.
- Имена функций консистентны между задачами: `load_raw_fractal_gate_data`, `build_fractal_features`, `gate_score`, `run_rf_gate`, `LIVE_SAFE_FRACTAL_FIELDS`, `TARGETS`.
- Плейсхолдеров нет; код в шагах полный.
