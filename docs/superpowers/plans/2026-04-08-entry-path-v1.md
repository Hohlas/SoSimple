# Entry Path v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить новый ML-трек `entry_path_v1`, который учится на реальном входе со следующего бара, отдельно предсказывает общую полезность идеи и путь цены, и готовит исследовательские артефакты для будущего слоя `trade / no-trade`.

**Architecture:** План не заменяет `regression_updn` и `triple_barrier`, а добавляет параллельный трек. Разметка строится в `processing` от `Open[t+1]`, затем `ML` получает отдельный набор mixed targets: 9 регрессионных и 1 трёхклассовый. В первом проходе трек ограничивается `transformer`-вариантом с общей спиной и двумя головами, а на выходе даёт test-отчёт и исследовательские CSV для будущего conformal prediction.

**Tech Stack:** Python 3.11+, pandas, numpy, torch, pytest

---

## File Map

- `processing/label_signals.py`
  Назначение: вычисление новых колонок `ret_*`, `fav_*`, `adv_*`, `path_6_class` от реального входа со следующего бара.
- `processing/label_main.py`
  Назначение: подключение новой разметки в основной pipeline до нормализации и split.
- `tests/test_entry_path_labels.py`
  Назначение: unit-тесты формул для BUY/SELL и first-touch логики `path_6_class`.
- `ML/entry_path_task.py`
  Назначение: единый контракт нового трека: списки таргетов, mapping классов, функции split/merge targets, loss, метрики, экспорт исследовательских предсказаний.
- `ML/data_loader.py`
  Назначение: новый режим `entry_path_v1`, отдельный `Dataset` под mixed targets, кэш для регрессионной и классификационной частей.
- `ML/models/entry_path_transformer.py`
  Назначение: shared transformer backbone + регрессионная и классификационная головы.
- `tests/test_entry_path_task.py`
  Назначение: unit-тесты target contract, split targets, export frame.
- `tests/test_entry_path_model.py`
  Назначение: unit-тесты shapes и loss-склейки нового multitask режима.
- `ML/train.py`
  Назначение: task branch `entry_path_v1`, цикл обучения, валидация, checkpoint и report JSON.
- `ML/evaluate_test.py`
  Назначение: test-оценка нового трека и markdown-report в `ML/reports/`.
- `API/generate_signals.py`
  Назначение: исследовательский export validation/test predictions для `entry_path_v1`; без выпуска MT4 CSV.
- `tests/test_entry_path_reports.py`
  Назначение: smoke-тест export columns и report sections.

---

### Task 1: Добавить разметку `entry_path_v1` в processing

**Files:**
- Modify: `processing/label_signals.py`
- Modify: `processing/label_main.py`
- Test: `tests/test_entry_path_labels.py`

- [ ] **Step 1: Write the failing tests for BUY/SELL formulas and `path_6_class`**

```python
# tests/test_entry_path_labels.py
import sys

import pandas as pd
import pytest

sys.path.insert(0, 'processing')
import label_signals as ls


def test_compute_entry_path_slice_buy():
    bars = pd.DataFrame([
        {'open': 100.0, 'high': 112.0, 'low': 99.0, 'close': 110.0},
        {'open': 110.0, 'high': 118.0, 'low': 107.0, 'close': 115.0},
        {'open': 115.0, 'high': 116.0, 'low': 104.0, 'close': 105.0},
    ])

    out = ls.compute_entry_path_slice(
        bars=bars,
        direction=1,
        entry_price=100.0,
        atr=10.0,
        horizon=3,
    )

    assert out['ret_dir_atr'] == pytest.approx(0.5)
    assert out['fav_atr'] == pytest.approx(1.8)
    assert out['adv_atr'] == pytest.approx(0.1)


def test_compute_entry_path_slice_sell():
    bars = pd.DataFrame([
        {'open': 100.0, 'high': 101.0, 'low': 95.0, 'close': 96.0},
        {'open': 96.0, 'high': 99.0, 'low': 90.0, 'close': 92.0},
        {'open': 92.0, 'high': 98.0, 'low': 89.0, 'close': 97.0},
    ])

    out = ls.compute_entry_path_slice(
        bars=bars,
        direction=-1,
        entry_price=100.0,
        atr=10.0,
        horizon=3,
    )

    assert out['ret_dir_atr'] == pytest.approx(0.3)
    assert out['fav_atr'] == pytest.approx(1.1)
    assert out['adv_atr'] == pytest.approx(0.1)


def test_first_touch_path_class_prefers_first_hit():
    bars = pd.DataFrame([
        {'open': 100.0, 'high': 100.8, 'low': 98.9, 'close': 99.2},
        {'open': 99.2, 'high': 101.3, 'low': 99.0, 'close': 101.1},
    ])

    out = ls.first_touch_path_class(
        bars=bars,
        direction=1,
        entry_price=100.0,
        atr=1.0,
        threshold_atr=1.0,
    )

    assert out == -1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_labels.py -q`
Expected: FAIL with `AttributeError` for missing `compute_entry_path_slice` and `first_touch_path_class`.

- [ ] **Step 3: Add helper functions and row-level label builder**

```python
# processing/label_signals.py
def compute_entry_path_slice(
    bars: pd.DataFrame,
    direction: int,
    entry_price: float,
    atr: float,
    horizon: int,
) -> dict[str, float]:
    window = bars.iloc[:horizon]
    if len(window) < horizon or atr <= 0:
        return {'ret_dir_atr': 0.0, 'fav_atr': 0.0, 'adv_atr': 0.0}

    close_h = float(window.iloc[-1]['close'])
    high_h = float(window['high'].max())
    low_h = float(window['low'].min())

    if direction == 1:
        ret_dir_atr = (close_h - entry_price) / atr
        fav_atr = (high_h - entry_price) / atr
        adv_atr = (entry_price - low_h) / atr
    else:
        ret_dir_atr = (entry_price - close_h) / atr
        fav_atr = (entry_price - low_h) / atr
        adv_atr = (high_h - entry_price) / atr

    return {
        'ret_dir_atr': float(ret_dir_atr),
        'fav_atr': float(fav_atr),
        'adv_atr': float(adv_atr),
    }


def first_touch_path_class(
    bars: pd.DataFrame,
    direction: int,
    entry_price: float,
    atr: float,
    threshold_atr: float = 1.0,
) -> int:
    if atr <= 0:
        return 0

    if direction == 1:
        down_price = entry_price - threshold_atr * atr
        up_price = entry_price + threshold_atr * atr
    else:
        down_price = entry_price + threshold_atr * atr
        up_price = entry_price - threshold_atr * atr

    outcome = first_touch_barrier_outcome(
        bars=bars,
        direction=direction,
        entry_price=entry_price,
        sl_price=down_price if direction == 1 else down_price,
        tp_price=up_price if direction == 1 else up_price,
    )
    if outcome == 1:
        return 1
    if outcome == 0:
        return -1
    return 0


def label_entry_path_targets(
    df: pd.DataFrame,
    ohlc_path: str,
    ret_horizons: tuple[int, ...] = (6, 12, 24),
    path_horizons: tuple[int, ...] = (3, 6, 12, 24),
    debug: bool = False,
) -> pd.DataFrame:
    ohlc = pd.read_csv(ohlc_path, sep=';', low_memory=False)
    ohlc['time'] = ohlc['time'].astype(str)
    time_to_idx = {t: i for i, t in enumerate(ohlc['time'])}

    out = df.copy()
    for h in ret_horizons:
        out[f'ret_{h}_dir_atr'] = 0.0
    for h in path_horizons:
        out[f'fav_{h}_atr'] = 0.0
        out[f'adv_{h}_atr'] = 0.0
    out['path_6_class'] = 0

    for row_idx, row in out.iterrows():
        signal = int(row['signal'])
        if signal not in (-1, 1):
            continue
        base_idx = time_to_idx.get(str(row['time']))
        if base_idx is None or base_idx + 1 >= len(ohlc):
            continue

        entry_bar = ohlc.iloc[base_idx + 1]
        entry_price = float(entry_bar['open'])
        atr = float(row['ATR'])

        for h in sorted(set(ret_horizons) | set(path_horizons)):
            end_idx = base_idx + 1 + h
            if end_idx > len(ohlc):
                continue
            bars = ohlc.iloc[base_idx + 1:end_idx]
            stats = compute_entry_path_slice(bars, signal, entry_price, atr, h)
            if h in ret_horizons:
                out.at[row_idx, f'ret_{h}_dir_atr'] = stats['ret_dir_atr']
            if h in path_horizons:
                out.at[row_idx, f'fav_{h}_atr'] = stats['fav_atr']
                out.at[row_idx, f'adv_{h}_atr'] = stats['adv_atr']

        bars6 = ohlc.iloc[base_idx + 1:base_idx + 7]
        out.at[row_idx, 'path_6_class'] = first_touch_path_class(
            bars=bars6,
            direction=signal,
            entry_price=entry_price,
            atr=atr,
            threshold_atr=1.0,
        )

    return out
```

- [ ] **Step 4: Wire the new labels into the main preprocessing pipeline**

```python
# processing/label_main.py
from label_signals import (
    label_all,
    label_updn,
    label_first_barrier_hit,
    label_entry_path_targets,
)

# после TB first-touch и до normalize_rowwise()
labeled_df = label_entry_path_targets(labeled_df, args.ohlc, debug=args.debug)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_labels.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add processing/label_signals.py processing/label_main.py tests/test_entry_path_labels.py
git commit -m "feat: add entry path labels"
```

---

### Task 2: Зарегистрировать новый target contract и mixed DataLoader

**Files:**
- Create: `ML/entry_path_task.py`
- Modify: `ML/data_loader.py`
- Test: `tests/test_entry_path_task.py`

- [ ] **Step 1: Write the failing test for target contract**

```python
# tests/test_entry_path_task.py
import numpy as np
import pandas as pd

from ML.entry_path_task import (
    ENTRY_PATH_TARGET,
    ENTRY_PATH_RET_TARGETS,
    ENTRY_PATH_PATH_REG_TARGETS,
    ENTRY_PATH_CLASS_TARGET,
    split_entry_path_targets,
    build_entry_path_export_frame,
)


def test_entry_path_target_contract():
    assert ENTRY_PATH_TARGET == 'entry_path_v1'
    assert ENTRY_PATH_RET_TARGETS == [
        'ret_6_dir_atr',
        'ret_12_dir_atr',
        'ret_24_dir_atr',
    ]
    assert ENTRY_PATH_CLASS_TARGET == 'path_6_class'


def test_split_entry_path_targets_returns_reg_and_cls_parts():
    frame = pd.DataFrame({
        'ret_6_dir_atr': [0.1],
        'ret_12_dir_atr': [0.2],
        'ret_24_dir_atr': [0.3],
        'fav_6_atr': [0.4],
        'adv_6_atr': [0.1],
        'fav_12_atr': [0.5],
        'adv_12_atr': [0.2],
        'fav_24_atr': [0.7],
        'adv_24_atr': [0.3],
        'path_6_class': [-1],
    })

    y_reg, y_cls = split_entry_path_targets(frame)

    assert y_reg.shape == (1, 9)
    assert y_cls.tolist() == [0]


def test_build_entry_path_export_frame_contains_core_columns():
    frame = build_entry_path_export_frame(
        times=np.array(['2025.01.01 00:00']),
        signals=np.array([1]),
        pred_ret=np.array([[0.1, 0.2, 0.3]], dtype=np.float32),
        pred_path_reg=np.array([[0.4, 0.1, 0.5, 0.2, 0.7, 0.3]], dtype=np.float32),
        pred_path_cls=np.array([[0.1, 0.2, 0.7]], dtype=np.float32),
        true_reg=np.array([[0.0, 0.1, 0.2, 0.3, 0.0, 0.4, 0.1, 0.5, 0.2]], dtype=np.float32),
        true_cls=np.array([2], dtype=np.int64),
    )

    assert 'pred_ret_24_dir_atr' in frame.columns
    assert 'pred_fav_24_atr' in frame.columns
    assert 'pred_path_6_class' in frame.columns
    assert frame.at[0, 'pred_path_6_class'] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_task.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'ML.entry_path_task'`

- [ ] **Step 3: Add the task contract module**

```python
# ML/entry_path_task.py
import numpy as np
import pandas as pd

ENTRY_PATH_TARGET = 'entry_path_v1'
ENTRY_PATH_RET_TARGETS = ['ret_6_dir_atr', 'ret_12_dir_atr', 'ret_24_dir_atr']
ENTRY_PATH_PATH_REG_TARGETS = [
    'fav_6_atr', 'adv_6_atr',
    'fav_12_atr', 'adv_12_atr',
    'fav_24_atr', 'adv_24_atr',
]
ENTRY_PATH_CLASS_TARGET = 'path_6_class'
ENTRY_PATH_REG_TARGETS = ENTRY_PATH_RET_TARGETS + ENTRY_PATH_PATH_REG_TARGETS
ENTRY_PATH_CLASS_MAP = {-1: 0, 0: 1, 1: 2}
ENTRY_PATH_INV_CLASS_MAP = {v: k for k, v in ENTRY_PATH_CLASS_MAP.items()}


def split_entry_path_targets(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    y_reg = df[ENTRY_PATH_REG_TARGETS].values.astype(np.float32)
    y_cls = df[ENTRY_PATH_CLASS_TARGET].map(ENTRY_PATH_CLASS_MAP).values.astype(np.int64)
    return y_reg, y_cls


def build_entry_path_export_frame(
    times: np.ndarray,
    signals: np.ndarray,
    pred_ret: np.ndarray,
    pred_path_reg: np.ndarray,
    pred_path_cls: np.ndarray,
    true_reg: np.ndarray | None = None,
    true_cls: np.ndarray | None = None,
) -> pd.DataFrame:
    cls_idx = pred_path_cls.argmax(axis=1)
    frame = pd.DataFrame({
        'time': times,
        'signal': signals,
        'pred_ret_6_dir_atr': pred_ret[:, 0],
        'pred_ret_12_dir_atr': pred_ret[:, 1],
        'pred_ret_24_dir_atr': pred_ret[:, 2],
        'pred_fav_6_atr': pred_path_reg[:, 0],
        'pred_adv_6_atr': pred_path_reg[:, 1],
        'pred_fav_12_atr': pred_path_reg[:, 2],
        'pred_adv_12_atr': pred_path_reg[:, 3],
        'pred_fav_24_atr': pred_path_reg[:, 4],
        'pred_adv_24_atr': pred_path_reg[:, 5],
        'pred_path_6_class': np.array([ENTRY_PATH_INV_CLASS_MAP[i] for i in cls_idx]),
        'pred_path_6_prob_neg': pred_path_cls[:, 0],
        'pred_path_6_prob_flat': pred_path_cls[:, 1],
        'pred_path_6_prob_pos': pred_path_cls[:, 2],
    })
    if true_reg is not None:
        for i, name in enumerate(ENTRY_PATH_REG_TARGETS):
            frame[f'true_{name}'] = true_reg[:, i]
    if true_cls is not None:
        frame['true_path_6_class'] = np.array([ENTRY_PATH_INV_CLASS_MAP[i] for i in true_cls])
    return frame
```

- [ ] **Step 4: Add a dedicated Dataset branch in `data_loader.py`**

```python
# ML/data_loader.py
from ML.entry_path_task import ENTRY_PATH_TARGET, split_entry_path_targets


class EntryPathDataset(Dataset):
    def __init__(self, X: np.ndarray, y_reg: np.ndarray, y_cls: np.ndarray, mask: np.ndarray):
        self.X = torch.from_numpy(X).float()
        self.y_reg = torch.from_numpy(y_reg.astype(np.float32)).float()
        self.y_cls = torch.from_numpy(y_cls.astype(np.int64)).long()
        self.mask = torch.from_numpy(mask).bool()

    def __len__(self) -> int:
        return len(self.y_cls)

    def __getitem__(self, idx: int):
        return self.X[idx], self.y_reg[idx], self.y_cls[idx], self.mask[idx]


# inside create_data_loaders(...)
entry_path = (target == ENTRY_PATH_TARGET)

# inside load_or_parse_data(...)
if target_col == ENTRY_PATH_TARGET:
    y_reg_path = DATA_DIR / f'y_{prefix}_{target_col}_reg.npy'
    y_cls_path = DATA_DIR / f'y_{prefix}_{target_col}_cls.npy'
    ...
    y_reg, y_cls = split_entry_path_targets(df)
    np.save(y_reg_path, y_reg)
    np.save(y_cls_path, y_cls)
    return X, mask, y_reg, y_cls

# after parsing
if entry_path:
    train_dataset = EntryPathDataset(X_train, y_train_reg, y_train_cls, mask_train)
    val_dataset = EntryPathDataset(X_val, y_val_reg, y_val_cls, mask_val)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_task.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add ML/entry_path_task.py ML/data_loader.py tests/test_entry_path_task.py
git commit -m "feat: add entry path target contract"
```

---

### Task 3: Добавить multitask transformer и обучение `entry_path_v1`

**Files:**
- Create: `ML/models/entry_path_transformer.py`
- Modify: `ML/train.py`
- Test: `tests/test_entry_path_model.py`

- [ ] **Step 1: Write the failing tests for output shapes and loss split**

```python
# tests/test_entry_path_model.py
import torch

from ML.models.entry_path_transformer import EntryPathTransformer


def test_entry_path_transformer_output_shapes():
    model = EntryPathTransformer(
        input_features=20,
        d_model=32,
        nhead=4,
        num_layers=1,
        dim_feedforward=64,
        dropout=0.1,
    )
    x = torch.randn(2, 20, 20)
    mask = torch.ones(2, 20, dtype=torch.bool)

    out = model(x, mask=mask)

    assert out['ret'].shape == (2, 3)
    assert out['path_reg'].shape == (2, 6)
    assert out['path_cls'].shape == (2, 3)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_model.py -q`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Create the dedicated transformer model for `entry_path_v1`**

```python
# ML/models/entry_path_transformer.py
import torch
import torch.nn as nn

from ML.models.transformer import PositionalEncoding


class EntryPathTransformer(nn.Module):
    def __init__(
        self,
        input_features: int = 20,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 128,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.input_projection = nn.Linear(input_features, d_model)
        self.cls_token = nn.Parameter(torch.randn(1, 1, d_model))
        self.pos_encoding = PositionalEncoding(d_model, max_len=200, dropout=dropout)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation='relu',
            batch_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.shared_head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.ret_head = nn.Linear(32, 3)
        self.path_reg_head = nn.Linear(32, 6)
        self.path_cls_head = nn.Linear(32, 3)

    def forward(self, x: torch.Tensor, mask: torch.Tensor | None = None) -> dict[str, torch.Tensor]:
        batch_size = x.size(0)
        x = self.input_projection(x)
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)
        x = self.pos_encoding(x)

        if mask is not None:
            cls_mask = torch.ones(batch_size, 1, dtype=torch.bool, device=mask.device)
            mask = torch.cat([cls_mask, mask], dim=1)
            src_key_padding_mask = ~mask
        else:
            src_key_padding_mask = None

        x = self.transformer_encoder(x, src_key_padding_mask=src_key_padding_mask)
        cls_output = self.shared_head(x[:, 0, :])
        return {
            'ret': self.ret_head(cls_output),
            'path_reg': self.path_reg_head(cls_output),
            'path_cls': self.path_cls_head(cls_output),
        }
```

- [ ] **Step 4: Add `entry_path_v1` branch in `train.py`**

```python
# ML/train.py
from ML.entry_path_task import ENTRY_PATH_TARGET
from ML.models.entry_path_transformer import EntryPathTransformer


def train_one_epoch_entry_path(model, train_loader, optimizer, device, reg_loss_fn, cls_loss_fn):
    model.train()
    total_loss = 0.0
    for X_batch, y_reg_batch, y_cls_batch, mask_batch in train_loader:
        X_batch = X_batch.to(device)
        y_reg_batch = y_reg_batch.to(device)
        y_cls_batch = y_cls_batch.to(device)
        mask_batch = mask_batch.to(device)

        optimizer.zero_grad()
        out = model(X_batch, mask=mask_batch)
        loss_ret = reg_loss_fn(out['ret'], y_reg_batch[:, :3])
        loss_path_reg = reg_loss_fn(out['path_reg'], y_reg_batch[:, 3:])
        loss_path_cls = cls_loss_fn(out['path_cls'], y_cls_batch)
        loss = 1.0 * loss_ret + 0.5 * loss_path_reg + 0.5 * loss_path_cls
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(train_loader)


# inside main task selection
if args.task == ENTRY_PATH_TARGET:
    if args.model != 'transformer':
        raise ValueError("entry_path_v1 в первой версии поддерживает только --model transformer")
    model = EntryPathTransformer(
        input_features=N_FRACTAL_FEATURES,
        d_model=model_kwargs.get('hidden_size', 64),
        nhead=4,
        num_layers=model_kwargs.get('num_layers', 2),
        dim_feedforward=model_kwargs.get('hidden_size', 64) * 2,
        dropout=model_kwargs.get('dropout', 0.3),
    )
```

- [ ] **Step 5: Run unit tests to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_model.py tests/test_entry_path_task.py -q`
Expected: PASS

- [ ] **Step 6: Run a short smoke training**

Run: `./.venv/bin/python -m ML.train --model transformer --task entry_path_v1 --epochs 1 --batch_size 256 --seed 42 --clear_cache`
Expected: One epoch finishes, checkpoint JSON for `entry_path_v1` is written without runtime errors.

- [ ] **Step 7: Commit**

```bash
git add ML/models/entry_path_transformer.py ML/train.py tests/test_entry_path_model.py
git commit -m "feat: add entry path multitask training"
```

---

### Task 4: Добавить test-оценку и исследовательский export для будущего `trade / no-trade`

**Files:**
- Modify: `ML/evaluate_test.py`
- Modify: `API/generate_signals.py`
- Test: `tests/test_entry_path_reports.py`

- [ ] **Step 1: Write the failing test for export columns**

```python
# tests/test_entry_path_reports.py
import numpy as np

from ML.entry_path_task import build_entry_path_export_frame


def test_entry_path_export_frame_keeps_validation_columns():
    frame = build_entry_path_export_frame(
        times=np.array(['2025.01.01 00:00', '2025.01.01 01:00']),
        signals=np.array([1, -1]),
        pred_ret=np.array([[0.3, 0.2, 0.1], [-0.1, 0.0, 0.2]], dtype=np.float32),
        pred_path_reg=np.array([
            [0.4, 0.1, 0.6, 0.2, 0.8, 0.3],
            [0.2, 0.5, 0.1, 0.6, 0.3, 0.7],
        ], dtype=np.float32),
        pred_path_cls=np.array([[0.1, 0.2, 0.7], [0.6, 0.3, 0.1]], dtype=np.float32),
        true_reg=np.zeros((2, 9), dtype=np.float32),
        true_cls=np.array([2, 0], dtype=np.int64),
    )

    assert frame.columns.tolist()[:5] == [
        'time',
        'signal',
        'pred_ret_6_dir_atr',
        'pred_ret_12_dir_atr',
        'pred_ret_24_dir_atr',
    ]
    assert 'true_ret_24_dir_atr' in frame.columns
    assert 'true_path_6_class' in frame.columns
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_reports.py -q`
Expected: FAIL until `build_entry_path_export_frame()` and the new entry_path branch are wired end-to-end.

- [ ] **Step 3: Add `entry_path_v1` branch in `evaluate_test.py`**

```python
# ML/evaluate_test.py
from ML.entry_path_task import (
    ENTRY_PATH_TARGET,
    ENTRY_PATH_RET_TARGETS,
    ENTRY_PATH_PATH_REG_TARGETS,
    build_entry_path_export_frame,
)
from ML.models.entry_path_transformer import EntryPathTransformer

if task == ENTRY_PATH_TARGET:
    test_loader = create_test_loader(
        batch_size=256,
        target=ENTRY_PATH_TARGET,
        seq_len=20,
        num_workers=0,
    )

    all_ret = []
    all_path_reg = []
    all_path_cls = []
    all_true_reg = []
    all_true_cls = []

    with torch.no_grad():
        for X_batch, y_reg_batch, y_cls_batch, mask_batch in test_loader:
            out = model(X_batch.to(device), mask=mask_batch.to(device))
            all_ret.append(out['ret'].cpu().numpy())
            all_path_reg.append(out['path_reg'].cpu().numpy())
            all_path_cls.append(torch.softmax(out['path_cls'], dim=1).cpu().numpy())
            all_true_reg.append(y_reg_batch.numpy())
            all_true_cls.append(y_cls_batch.numpy())

    pred_ret = np.concatenate(all_ret)
    pred_path_reg = np.concatenate(all_path_reg)
    pred_path_cls = np.concatenate(all_path_cls)
    true_reg = np.concatenate(all_true_reg)
    true_cls = np.concatenate(all_true_cls)

    export = build_entry_path_export_frame(
        times=df_test['time'].values,
        signals=df_test['signal'].values.astype(int),
        pred_ret=pred_ret,
        pred_path_reg=pred_path_reg,
        pred_path_cls=pred_path_cls,
        true_reg=true_reg,
        true_cls=true_cls,
    )
    export.to_csv(REPORTS_DIR / 'entry_path_test_predictions.csv', sep=';', index=False)
```

- [ ] **Step 4: Add research-only export branch in `API/generate_signals.py`**

```python
# API/generate_signals.py
from ML.entry_path_task import ENTRY_PATH_TARGET, build_entry_path_export_frame
from ML.models.entry_path_transformer import EntryPathTransformer

parser.add_argument(
    '--research-out-prefix',
    type=str,
    default='',
    help='Prefix for entry_path_v1 research CSVs; example ML/reports/entry_path_v1',
)

if args.task == ENTRY_PATH_TARGET:
    if not args.research_out_prefix:
        raise ValueError("Для entry_path_v1 нужен --research-out-prefix; MT4 CSV пока не выпускается")

    # write:
    # <prefix>_validation_predictions.csv
    # <prefix>_test_predictions.csv
```

- [ ] **Step 5: Run tests to verify the reporting/export layer passes**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_reports.py tests/test_entry_path_task.py -q`
Expected: PASS

- [ ] **Step 6: Run full entry_path evaluation and export**

Run: `./.venv/bin/python -m ML.evaluate_test --task entry_path_v1 --model transformer`
Expected: Writes `ML/reports/evaluate_test_entry_path_v1.md` and `ML/reports/entry_path_test_predictions.csv`

Run: `./.venv/bin/python -m API.generate_signals --task entry_path_v1 --model transformer --research-out-prefix ML/reports/entry_path_v1`
Expected: Writes `ML/reports/entry_path_v1_validation_predictions.csv` and `ML/reports/entry_path_v1_test_predictions.csv`

- [ ] **Step 7: Commit**

```bash
git add ML/evaluate_test.py API/generate_signals.py tests/test_entry_path_reports.py
git commit -m "feat: add entry path evaluation exports"
```

---

### Task 5: Прогнать полный `entry_path_v1` baseline и зафиксировать рабочие артефакты

**Files:**
- Modify: `ML/reports/evaluate_test_entry_path_v1.md`
- Create: `ML/reports/entry_path_v1_validation_predictions.csv`
- Create: `ML/reports/entry_path_v1_test_predictions.csv`

- [ ] **Step 1: Rebuild labeled data with the new columns**

Run: `./.venv/bin/python processing/label_main.py --input MT/MQL4/Files/Nero.csv --ohlc DATA/XAUUSD_H1_OHLC.csv --debug`
Expected: `DATA/Nero_{train,validation,test}_labeled.csv` regenerated with `ret_*`, `fav_*`, `adv_*`, `path_6_class`

- [ ] **Step 2: Run the focused test suite**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_labels.py tests/test_entry_path_task.py tests/test_entry_path_model.py tests/test_entry_path_reports.py -q`
Expected: PASS

- [ ] **Step 3: Train the baseline model**

Run: `./.venv/bin/python -m ML.train --model transformer --task entry_path_v1 --epochs 50 --seed 42 --clear_cache`
Expected: checkpoint like `ML/checkpoints/transformer_entry_path_v1_best.pt` and a result JSON are written

- [ ] **Step 4: Evaluate on test**

Run: `./.venv/bin/python -m ML.evaluate_test --task entry_path_v1 --model transformer`
Expected: `ML/reports/evaluate_test_entry_path_v1.md` created with:
- metrics for `ret_6/12/24`
- metrics for `fav/adv`
- metrics for `path_6_class`
- top-vs-bottom slice for `pred_ret_24_dir_atr`

- [ ] **Step 5: Export validation/test predictions for future conformal work**

Run: `./.venv/bin/python -m API.generate_signals --task entry_path_v1 --model transformer --research-out-prefix ML/reports/entry_path_v1`
Expected:
- `ML/reports/entry_path_v1_validation_predictions.csv`
- `ML/reports/entry_path_v1_test_predictions.csv`

- [ ] **Step 6: Commit**

```bash
git add ML/checkpoints/transformer_entry_path_v1_best.pt \
        ML/reports/evaluate_test_entry_path_v1.md \
        ML/reports/entry_path_v1_validation_predictions.csv \
        ML/reports/entry_path_v1_test_predictions.csv
git commit -m "feat: add entry path baseline artifacts"
```

