# Track A Max-Out Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Расширить Track A одним ограниченным max-out проходом: richer dataset, `seq_len 20/50/100`, до двух новых вариантов модели и один строгий benchmark phase с целью найти хотя бы один устойчивый validation-кандидат в зоне `PF > 1`.

**Architecture:** План не делает бесконечный sweep. Он добавляет банк агрегированных признаков строки, протаскивает их через loader/cache, поддерживает три длины истории и сравнивает три варианта модели: `Baseline+`, `Dual-Stream`, `Long-Context Transformer`. После обучения снимаются prediction exports и прогоняется уже существующий `benchmark_v2`.

**Tech Stack:** Python 3.11, pandas, numpy, torch, pytest, существующие модули `processing/label_signals.py`, `ML/data_loader.py`, `ML/train.py`, `ML/evaluate_test.py`, `API/generate_signals.py`, `ML/benchmark_entry_path_v2.py`

---

## File Structure

### Read First

- `docs/superpowers/specs/2026-04-15-track-a-max-out-design.md`
- `ML/entry_path_task.py`
- `ML/data_loader.py`
- `ML/models/entry_path_transformer.py`
- `ML/train.py`
- `ML/evaluate_test.py`
- `API/generate_signals.py`
- `ML/benchmark_entry_path_v2.py`

### Files To Create

- `ML/entry_path_feature_bank.py`
- `ML/models/entry_path_dual_stream_transformer.py`
- `tests/test_entry_path_feature_bank.py`
- `tests/test_entry_path_dual_stream_transformer.py`
- `docs/reports/2026-04-15-track-a-max-out.md`

### Files To Modify

- `ML/entry_path_task.py`
- `ML/data_loader.py`
- `ML/models/entry_path_transformer.py`
- `ML/train.py`
- `ML/evaluate_test.py`
- `API/generate_signals.py`
- `tests/test_entry_path_task.py`
- `tests/test_entry_path_model.py`
- `tests/test_entry_path_training.py`
- `tests/test_entry_path_reports.py`

### Files To Update After Implementation

- `ML/reports/entry_path_v1_frequency_v2/*`
- `ML/checkpoints/transformer_entry_path_v1_best.pt`
- `ML/checkpoints/transformer_entry_path_v1_result.json`

---

### Task 1: Create A Dedicated Entry-Path Feature Bank

**Files:**
- Create: `ML/entry_path_feature_bank.py`
- Create: `tests/test_entry_path_feature_bank.py`

- [ ] **Step 1: Write the failing test for multi-window row summaries**

```python
import sys

import pandas as pd

sys.path.insert(0, '.')

from ML.entry_path_feature_bank import build_entry_path_feature_bank


def test_build_entry_path_feature_bank_adds_multi_window_columns():
    frame = pd.DataFrame(
        {
            'fractal0': ['10:1:1:1:2:1:1:0:3:2:4:0:0:0:0:0:0:0:0:0:0:1'],
            'fractal1': ['9:1:-1:1:3:0:0:0:1:1:2:0:0:0:0:0:0:0:0:0:0:1'],
            'fractal2': ['8:1:1:1:4:1:0:0:2:3:5:0:0:0:0:0:0:0:0:0:0:1'],
            'fractal3': [''],
            'fractal4': [''],
            'session_hour': [10],
            'weekday': [2],
            'range_atr_6': [1.5],
            'body_atr_3': [0.4],
            'ret_dir_atr_lag1': [0.2],
            'vol_regime_24': [1.1],
        }
    )

    out = build_entry_path_feature_bank(frame)

    expected = {
        'row_strong_share_w5',
        'row_break_share_w5',
        'row_direction_balance_w5',
        'row_back_mean_w5',
        'row_impulse_mean_w5',
        'row_strong_share_w100',
    }
    assert expected.issubset(out.columns)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_feature_bank.py::test_build_entry_path_feature_bank_adds_multi_window_columns -q
```

Expected: fail with `ModuleNotFoundError` for `ML.entry_path_feature_bank`.

- [ ] **Step 3: Implement the feature-bank module**

Create `ML/entry_path_feature_bank.py`:

```python
from __future__ import annotations

import numpy as np
import pandas as pd


WINDOWS = (5, 10, 20, 50, 100)


def _parse_fractal(raw: str) -> dict[str, float] | None:
    if pd.isna(raw) or raw == '':
        return None
    parts = str(raw).split(':')
    if len(parts) < 22:
        return None
    try:
        return {
            'direction': float(parts[2]),
            'front': float(parts[3]),
            'back': float(parts[4]),
            'strong': float(parts[5]),
            'break': float(parts[6]),
            'power': float(parts[8]),
            'count': float(parts[9]),
            'impulse': float(parts[10]),
            'fractal_atr': float(parts[21]),
        }
    except ValueError:
        return None


def _window_stats(parsed: list[dict[str, float]], window: int) -> dict[str, float]:
    chunk = parsed[:window]
    if not chunk:
        return {
            f'row_strong_share_w{window}': 0.0,
            f'row_break_share_w{window}': 0.0,
            f'row_direction_balance_w{window}': 0.0,
            f'row_back_mean_w{window}': 0.0,
            f'row_back_std_w{window}': 0.0,
            f'row_impulse_mean_w{window}': 0.0,
            f'row_power_mean_w{window}': 0.0,
            f'row_count_mean_w{window}': 0.0,
        }

    def values(name: str) -> np.ndarray:
        return np.asarray([item[name] for item in chunk], dtype=np.float64)

    direction = values('direction')
    back = values('back')
    return {
        f'row_strong_share_w{window}': float(values('strong').mean()),
        f'row_break_share_w{window}': float(values('break').mean()),
        f'row_direction_balance_w{window}': float(direction.mean()),
        f'row_back_mean_w{window}': float(back.mean()),
        f'row_back_std_w{window}': float(back.std()),
        f'row_impulse_mean_w{window}': float(values('impulse').mean()),
        f'row_power_mean_w{window}': float(values('power').mean()),
        f'row_count_mean_w{window}': float(values('count').mean()),
    }


def build_entry_path_feature_bank(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    fractal_cols = [column for column in out.columns if column.startswith('fractal')]
    rows = []
    for _, row in out[fractal_cols].iterrows():
        parsed = [item for item in (_parse_fractal(row[col]) for col in fractal_cols) if item is not None]
        features = {}
        for window in WINDOWS:
            features.update(_window_stats(parsed, window))
        rows.append(features)
    feature_frame = pd.DataFrame(rows, index=out.index).fillna(0.0)
    return pd.concat([out, feature_frame], axis=1)
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_feature_bank.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add ML/entry_path_feature_bank.py tests/test_entry_path_feature_bank.py
git commit -m "entry_path: add multi-window feature bank"
```

### Task 2: Expand The Entry-Path Feature Contract

**Files:**
- Modify: `ML/entry_path_task.py`
- Modify: `tests/test_entry_path_task.py`

- [ ] **Step 1: Write the failing test for expanded feature columns**

Add to `tests/test_entry_path_task.py`:

```python
def test_entry_path_task_exposes_feature_bank_columns():
    expected = {
        'row_strong_share_w5',
        'row_break_share_w10',
        'row_direction_balance_w20',
        'row_back_mean_w50',
        'row_impulse_mean_w100',
    }
    assert expected.issubset(set(ENTRY_PATH_V1_FEATURE_COLUMNS))
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_task.py::test_entry_path_task_exposes_feature_bank_columns -q
```

Expected: fail because the new feature names are not in `ENTRY_PATH_V1_FEATURE_COLUMNS`.

- [ ] **Step 3: Expand the feature contract**

Update `ML/entry_path_task.py`:

```python
ENTRY_PATH_V1_BASE_FEATURE_COLUMNS = [
    'session_hour',
    'weekday',
    'range_atr_6',
    'body_atr_3',
    'ret_dir_atr_lag1',
    'vol_regime_24',
]

ENTRY_PATH_V1_WINDOW_FEATURE_COLUMNS = [
    'row_strong_share_w5',
    'row_break_share_w5',
    'row_direction_balance_w5',
    'row_back_mean_w5',
    'row_back_std_w5',
    'row_impulse_mean_w5',
    'row_power_mean_w5',
    'row_count_mean_w5',
    'row_strong_share_w10',
    'row_break_share_w10',
    'row_direction_balance_w10',
    'row_back_mean_w10',
    'row_back_std_w10',
    'row_impulse_mean_w10',
    'row_power_mean_w10',
    'row_count_mean_w10',
    'row_strong_share_w20',
    'row_break_share_w20',
    'row_direction_balance_w20',
    'row_back_mean_w20',
    'row_back_std_w20',
    'row_impulse_mean_w20',
    'row_power_mean_w20',
    'row_count_mean_w20',
    'row_strong_share_w50',
    'row_break_share_w50',
    'row_direction_balance_w50',
    'row_back_mean_w50',
    'row_back_std_w50',
    'row_impulse_mean_w50',
    'row_power_mean_w50',
    'row_count_mean_w50',
    'row_strong_share_w100',
    'row_break_share_w100',
    'row_direction_balance_w100',
    'row_back_mean_w100',
    'row_back_std_w100',
    'row_impulse_mean_w100',
    'row_power_mean_w100',
    'row_count_mean_w100',
]

ENTRY_PATH_V1_FEATURE_COLUMNS = ENTRY_PATH_V1_BASE_FEATURE_COLUMNS + ENTRY_PATH_V1_WINDOW_FEATURE_COLUMNS
```

- [ ] **Step 4: Run the focused test**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_task.py::test_entry_path_task_exposes_feature_bank_columns -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add ML/entry_path_task.py tests/test_entry_path_task.py
git commit -m "entry_path: expand row feature contract"
```

### Task 3: Build The Feature Bank Into The Loader And Cache Layer

**Files:**
- Modify: `ML/data_loader.py`
- Modify: `tests/test_entry_path_task.py`
- Modify: `tests/test_entry_path_training.py`

- [ ] **Step 1: Write the failing dataset test for engineered-feature width**

Add to `tests/test_entry_path_task.py`:

```python
def test_entry_path_dataset_uses_full_engineered_feature_width():
    dataset = EntryPathDataset(
        X=np.zeros((1, 4, 3), dtype=np.float32),
        engineered=np.zeros((1, len(ENTRY_PATH_V1_FEATURE_COLUMNS)), dtype=np.float32),
        y_reg=np.zeros((1, 9), dtype=np.float32),
        y_cls=np.array([2], dtype=np.int64),
        mask=np.array([[True, True, False, False]]),
        signal=np.array([1], dtype=np.int64),
    )

    _x, engineered_item, _y_reg, _y_cls, _mask, _signal = dataset[0]
    assert engineered_item.shape == (len(ENTRY_PATH_V1_FEATURE_COLUMNS),)
```

- [ ] **Step 2: Run the test to verify current width assumptions fail**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_task.py::test_entry_path_dataset_uses_full_engineered_feature_width -q
```

Expected: fail if any hard-coded engineered width assumptions remain.

- [ ] **Step 3: Wire the feature bank into loader parsing**

Update `ML/data_loader.py`:

```python
from ML.entry_path_feature_bank import build_entry_path_feature_bank
```

Inside both train/val and test entry-path branches:

```python
if entry_path:
    df = build_entry_path_feature_bank(df)
    engineered = split_entry_path_features(df)
    y_reg, y_cls = split_entry_path_targets(df)
    signal = df['signal'].values.astype(np.int64)
```

Cache validation must use:

```python
engineered.shape[1] == len(ENTRY_PATH_V1_FEATURE_COLUMNS)
```

- [ ] **Step 4: Verify focused tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_task.py tests/test_entry_path_training.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add ML/data_loader.py tests/test_entry_path_task.py tests/test_entry_path_training.py
git commit -m "entry_path: build feature bank into loader cache"
```

### Task 4: Support `seq_len 20/50/100` As A First-Class Entry-Path Sweep Axis

**Files:**
- Modify: `ML/train.py`
- Modify: `ML/evaluate_test.py`
- Modify: `API/generate_signals.py`
- Modify: `tests/test_entry_path_training.py`

- [ ] **Step 1: Write the failing training test for `seq_len` propagation**

Add to `tests/test_entry_path_training.py`:

```python
def test_main_passes_seq_len_to_train_model_for_entry_path(monkeypatch, tmp_path):
    captured = {}

    monkeypatch.setattr(
        tr,
        'parse_args',
        lambda: SimpleNamespace(
            model='transformer',
            task='entry_path_v1',
            use_scaler=False,
            epochs=1,
            batch_size=32,
            lr=1e-3,
            weight_decay=1e-4,
            patience=1,
            seed=42,
            focal_minority_weight=0.25,
            focal_gamma=2.0,
            regression_loss='huber',
            asym_over_penalty=1.0,
            asym_under_penalty=10.0,
            scheduler_patience=1,
            scheduler_factor=0.5,
            metric_mode='f1_macro',
            min_signal_recall=0.3,
            use_weighted_sampler=False,
            model_kwargs=None,
            seq_len=100,
            encoder_ckpt=None,
            optuna_json=None,
            clear_cache=False,
        ),
    )

    monkeypatch.setattr(tr, 'CHECKPOINTS_DIR', tmp_path)
    monkeypatch.setattr(tr, 'train_model', lambda **kwargs: captured.update(kwargs) or {
        'model_name': 'transformer',
        'task': 'entry_path_v1',
        'best_metric': 0.1,
        'best_epoch': 1,
        'num_parameters': 1,
        'training_time': 1.0,
        'best_metrics': {'ret_pearson_r': 0.1, 'pearson_r': 0.1, 'mae': 0.1, 'rmse': 0.1, 'r2': 0.0},
    })

    tr.main()
    assert captured['seq_len'] == 100
```

- [ ] **Step 2: Run the focused test and verify failure if `seq_len` plumbing is missing**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_training.py::test_main_passes_seq_len_to_train_model_for_entry_path -q
```

Expected: fail only if entry-path CLI plumbing ignores `seq_len`.

- [ ] **Step 3: Ensure all entry-path inference flows propagate `seq_len` from checkpoint/model kwargs**

Update:

- `ML/train.py`
- `ML/evaluate_test.py`
- `API/generate_signals.py`

Code to preserve:

```python
model_kwargs.setdefault('seq_len', seq_len)
```

and

```python
test_loader = create_test_loader(
    batch_size=256,
    target=target_col,
    seq_len=model_kwargs.get('seq_len', 20),
    num_workers=0,
)
```

- [ ] **Step 4: Run the focused suite**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_training.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add ML/train.py ML/evaluate_test.py API/generate_signals.py tests/test_entry_path_training.py
git commit -m "entry_path: preserve seq_len across train and inference"
```

### Task 5: Extend The Baseline Transformer For Larger Row-Feature Fusion

**Files:**
- Modify: `ML/models/entry_path_transformer.py`
- Modify: `tests/test_entry_path_model.py`

- [ ] **Step 1: Write the failing test for wider engineered feature fusion**

Add to `tests/test_entry_path_model.py`:

```python
def test_entry_path_transformer_accepts_large_engineered_feature_dim():
    model = EntryPathTransformer(
        input_features=20,
        engineered_feature_dim=46,
        d_model=32,
        nhead=4,
        num_layers=1,
        dim_feedforward=64,
        dropout=0.1,
    )
    x = torch.randn(2, 20, 20)
    engineered = torch.randn(2, 46)
    mask = torch.ones(2, 20, dtype=torch.bool)
    out = model(x, engineered, mask=mask)
    assert out['ret'].shape == (2, 3)
```

- [ ] **Step 2: Run the focused test**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_model.py::test_entry_path_transformer_accepts_large_engineered_feature_dim -q
```

Expected: fail if model still assumes the old engineered width or weak fusion block.

- [ ] **Step 3: Upgrade the fusion block**

Update `ML/models/entry_path_transformer.py`:

```python
self.entry_path_projection = nn.Sequential(
    nn.Linear(d_model + engineered_feature_dim, d_model),
    nn.ReLU(),
    nn.Dropout(dropout),
    nn.Linear(d_model, d_model),
    nn.ReLU(),
    nn.Dropout(dropout),
)
```

- [ ] **Step 4: Run the model suite**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_model.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add ML/models/entry_path_transformer.py tests/test_entry_path_model.py
git commit -m "entry_path: widen baseline fusion block"
```

### Task 6: Add The Dual-Stream Variant

**Files:**
- Create: `ML/models/entry_path_dual_stream_transformer.py`
- Create: `tests/test_entry_path_dual_stream_transformer.py`
- Modify: `ML/train.py`
- Modify: `ML/evaluate_test.py`
- Modify: `API/generate_signals.py`

- [ ] **Step 1: Write the failing model test**

Create `tests/test_entry_path_dual_stream_transformer.py`:

```python
import sys

import torch

sys.path.insert(0, '.')

from ML.models.entry_path_dual_stream_transformer import EntryPathDualStreamTransformer


def test_entry_path_dual_stream_transformer_returns_expected_shapes():
    model = EntryPathDualStreamTransformer(
        input_features=20,
        engineered_feature_dim=46,
        d_model=32,
        nhead=4,
        num_layers=1,
        dim_feedforward=64,
        dropout=0.1,
    )
    x = torch.randn(2, 50, 20)
    engineered = torch.randn(2, 46)
    mask = torch.ones(2, 50, dtype=torch.bool)
    out = model(x, engineered, mask=mask)
    assert out['ret'].shape == (2, 3)
    assert out['path_reg'].shape == (2, 6)
    assert out['path_cls'].shape == (2, 3)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_dual_stream_transformer.py -q
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement the dual-stream model**

Create `ML/models/entry_path_dual_stream_transformer.py`:

```python
import torch
import torch.nn as nn

from ML.models.transformer import PositionalEncoding


class EntryPathDualStreamTransformer(nn.Module):
    def __init__(
        self,
        input_features: int = 20,
        engineered_feature_dim: int = 46,
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
        self.engineered_branch = nn.Sequential(
            nn.Linear(engineered_feature_dim, d_model),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, d_model),
            nn.ReLU(),
        )
        self.fusion = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.ret_head = nn.Linear(d_model, 3)
        self.path_reg_head = nn.Linear(d_model, 6)
        self.path_cls_head = nn.Linear(d_model, 3)

    def forward(self, x: torch.Tensor, engineered: torch.Tensor, mask: torch.Tensor | None = None):
        batch_size = x.size(0)
        x = self.input_projection(x)
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)
        x = self.pos_encoding(x)
        if mask is not None:
            cls_mask = torch.ones(batch_size, 1, dtype=torch.bool, device=mask.device)
            src_key_padding_mask = ~torch.cat([cls_mask, mask], dim=1)
        else:
            src_key_padding_mask = None
        x = self.transformer_encoder(x, src_key_padding_mask=src_key_padding_mask)
        cls_output = x[:, 0, :]
        engineered_output = self.engineered_branch(engineered)
        fused = self.fusion(torch.cat([cls_output, engineered_output], dim=1))
        return {
            'ret': self.ret_head(fused),
            'path_reg': self.path_reg_head(fused),
            'path_cls': self.path_cls_head(fused),
        }
```

- [ ] **Step 4: Register the variant in train/eval/generate flows**

In `ML/train.py`, `ML/evaluate_test.py`, and `API/generate_signals.py`, branch on:

```python
if model_name == 'entry_path_dual_stream':
    model = EntryPathDualStreamTransformer(**model_kwargs)
```

- [ ] **Step 5: Run the model test**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_dual_stream_transformer.py -q
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add ML/models/entry_path_dual_stream_transformer.py tests/test_entry_path_dual_stream_transformer.py ML/train.py ML/evaluate_test.py API/generate_signals.py
git commit -m "entry_path: add dual-stream transformer variant"
```

### Task 7: Add A Long-Context Transformer Mode

**Files:**
- Modify: `ML/models/entry_path_transformer.py`
- Modify: `tests/test_entry_path_model.py`

- [ ] **Step 1: Write the failing test for `seq_len=100` forward pass**

Add to `tests/test_entry_path_model.py`:

```python
def test_entry_path_transformer_supports_seq_len_100():
    model = EntryPathTransformer(
        input_features=20,
        engineered_feature_dim=46,
        d_model=64,
        nhead=4,
        num_layers=2,
        dim_feedforward=128,
        dropout=0.1,
    )
    x = torch.randn(2, 100, 20)
    engineered = torch.randn(2, 46)
    mask = torch.ones(2, 100, dtype=torch.bool)
    out = model(x, engineered, mask=mask)
    assert out['path_cls'].shape == (2, 3)
```

- [ ] **Step 2: Run the focused test**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_model.py::test_entry_path_transformer_supports_seq_len_100 -q
```

Expected: fail if positional encoding or fusion path still assumes shorter context.

- [ ] **Step 3: Ensure the baseline model is stable at `max_len=200` and `seq_len=100`**

Keep in `ML/models/entry_path_transformer.py`:

```python
self.pos_encoding = PositionalEncoding(d_model, max_len=200, dropout=dropout)
```

and make sure no pooling logic assumes `20`.

- [ ] **Step 4: Run the model suite again**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_model.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add ML/models/entry_path_transformer.py tests/test_entry_path_model.py
git commit -m "entry_path: validate long-context transformer mode"
```

### Task 8: Execute The Bounded Training Matrix

**Files:**
- Modify: `docs/reports/2026-04-15-track-a-max-out.md`

- [ ] **Step 1: Run `Baseline+` with `seq_len=20`**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.train --model transformer --task entry_path_v1 --epochs 30 --seed 42 --seq-len 20
```

Expected: writes updated `ML/checkpoints/transformer_entry_path_v1_best.pt` and result JSON.

- [ ] **Step 2: Run `Baseline+` with `seq_len=50`**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.train --model transformer --task entry_path_v1 --epochs 30 --seed 42 --seq-len 50
```

Expected: complete without shape/cache errors.

- [ ] **Step 3: Run `Baseline+` with `seq_len=100`**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.train --model transformer --task entry_path_v1 --epochs 30 --seed 42 --seq-len 100
```

Expected: complete without shape/cache errors.

- [ ] **Step 4: Run `Dual-Stream` on the best baseline context length**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.train --model entry_path_dual_stream --task entry_path_v1 --epochs 30 --seed 42 --seq-len 50
```

Expected: complete and produce checkpoint.

- [ ] **Step 5: Run `Long-Context Transformer` on `seq_len=100`**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.train --model transformer --task entry_path_v1 --epochs 30 --seed 42 --seq-len 100 --model-kwargs '{"d_model":96,"dim_feedforward":192}'
```

Expected: complete and produce checkpoint for the wider long-context variant.

- [ ] **Step 6: Record validation metrics in the report draft**

Add to `docs/reports/2026-04-15-track-a-max-out.md` a table with:

```md
| Variant | seq_len | best_epoch | val ret_pearson_r | val path_reg_pearson_r | val path_cls_f1_macro |
|---------|---------|------------|-------------------|-------------------------|------------------------|
```

- [ ] **Step 7: Commit**

```bash
git add docs/reports/2026-04-15-track-a-max-out.md ML/checkpoints/transformer_entry_path_v1_result.json ML/checkpoints/transformer_entry_path_v1_best.pt
git commit -m "entry_path: run bounded track a max-out matrix"
```

### Task 9: Export Predictions And Run Benchmark V2

**Files:**
- Modify: `docs/reports/2026-04-15-track-a-max-out.md`
- Modify: `ML/reports/entry_path_v1_frequency_v2/*`

- [ ] **Step 1: Run `evaluate_test` on the selected winner checkpoint**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.evaluate_test --task entry_path_v1 --checkpoint ML/checkpoints/transformer_entry_path_v1_best.pt
```

Expected: rewrites `ML/reports/evaluate_test_entry_path_v1.md`.

- [ ] **Step 2: Export validation/test prediction CSVs**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m API.generate_signals --task entry_path_v1 --model transformer --research-out-prefix ML/reports/entry_path_v1
```

Expected: rewrites:

- `ML/reports/entry_path_v1_validation_predictions.csv`
- `ML/reports/entry_path_v1_test_predictions.csv`

- [ ] **Step 3: Run `benchmark_v2` on the new exports**

Run:

```bash
rm -rf ML/reports/entry_path_v1_frequency_v2
mkdir -p ML/reports/entry_path_v1_frequency_v2
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_entry_path_v2 \
  --validation-csv ML/reports/entry_path_v1_validation_predictions.csv \
  --test-csv ML/reports/entry_path_v1_test_predictions.csv \
  --output-dir ML/reports/entry_path_v1_frequency_v2
```

Expected: writes:

- `validation_grid.csv`
- `validation_family_summary.csv`
- `test_grid.csv`
- `selected_candidate.json`
- `final_verdict.json`

- [ ] **Step 4: Record the final verdict**

Append to `docs/reports/2026-04-15-track-a-max-out.md`:

```md
## Final Verdict

- winner family:
- winner candidate:
- validation PF:
- validation trades_per_year:
- validation negative_year_slices:
- validation ulcer_index:
- test PF:
- test trades_per_year:
- Track A status: still alive / near exhausted
```

- [ ] **Step 5: Commit**

```bash
git add docs/reports/2026-04-15-track-a-max-out.md ML/reports/entry_path_v1_frequency_v2 ML/reports/evaluate_test_entry_path_v1.md ML/reports/entry_path_v1_validation_predictions.csv ML/reports/entry_path_v1_test_predictions.csv
git commit -m "entry_path: benchmark bounded track a max-out results"
```

## Self-Review

- Spec coverage:
  - richer dataset: Task 1-3
  - `seq_len 20/50/100`: Task 4 and Task 8
  - 2-3 model variants: Task 5-7
  - validation-first benchmark: Task 9
- Placeholder scan:
  - no `TODO/TBD`
  - all test steps include concrete code or commands
- Type consistency:
  - `ENTRY_PATH_V1_FEATURE_COLUMNS` remains the source of truth for engineered width
  - all models use `(x, engineered, mask)` forward signature
