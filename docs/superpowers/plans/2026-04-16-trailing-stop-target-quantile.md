# Trailing Stop Target Quantile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Построить bounded-трек `trailing_stop_target_quantile_v1` для `trail_48_pnl_atr_x3`, обучить одну quantile-модель на `seq_len=20` и проверить, появится ли хотя бы один validation-candidate с `PF > 1`.

**Architecture:** План не меняет базовый trailing-stop target и не запускает новый sweep. Он добавляет отдельный quantile-task с тремя выходами `q10/q50/q90`, протягивает его через train/evaluate/export stack и создаёт короткий validation-first benchmark поверх quantile exports.

**Tech Stack:** Python 3.12, pandas, numpy, torch, pytest, существующие модули `ML/train.py`, `ML/evaluate_test.py`, `API/generate_signals.py`, `ML/data_loader.py`

---

## File Structure

### Read First

- `docs/superpowers/specs/2026-04-16-trailing-stop-target-quantile-design.md`
- `ML/trailing_stop_target_task.py`
- `ML/entry_path_v1_quantile_task.py`
- `ML/models/entry_path_v1_quantile_transformer.py`
- `ML/benchmark_trailing_stop_target.py`
- `ML/run_trailing_stop_target_matrix.py`

### Files To Create

- `ML/trailing_stop_target_quantile_task.py`
- `ML/models/trailing_stop_target_quantile_transformer.py`
- `ML/benchmark_trailing_stop_target_quantile.py`
- `ML/run_trailing_stop_target_quantile.py`
- `tests/test_trailing_stop_target_quantile_task.py`
- `tests/test_trailing_stop_target_quantile_model.py`
- `tests/test_benchmark_trailing_stop_target_quantile.py`
- `tests/test_run_trailing_stop_target_quantile.py`
- `docs/reports/2026-04-16-trailing-stop-target-quantile-first-wave.md`

### Files To Modify

- `ML/data_loader.py`
- `ML/train.py`
- `ML/evaluate_test.py`
- `API/generate_signals.py`
- `MODULE_INDEX.md`
- `CHANGELOG.md`

### Files To Update After Implementation

- `ML/checkpoints/transformer_trailing_stop_target_quantile_v1_best.pt`
- `ML/reports/trailing_stop_target_quantile/`

---

### Task 1: Add Quantile Task Contract And Model

**Files:**
- Create: `ML/trailing_stop_target_quantile_task.py`
- Create: `ML/models/trailing_stop_target_quantile_transformer.py`
- Create: `tests/test_trailing_stop_target_quantile_task.py`
- Create: `tests/test_trailing_stop_target_quantile_model.py`

- [ ] **Step 1: Write the failing task-contract tests**

```python
# tests/test_trailing_stop_target_quantile_task.py
import numpy as np
import pytest

from ML.trailing_stop_target_quantile_task import (
    TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN,
    TRAILING_STOP_TARGET_QUANTILE_Q50_COLUMN,
    TRAILING_STOP_TARGET_QUANTILE_Q90_COLUMN,
    TRAILING_STOP_TARGET_QUANTILE_TARGET,
    build_trailing_stop_quantile_export_frame,
    compute_trailing_stop_quantile_metrics,
)


def test_quantile_task_constants_match_design():
    assert TRAILING_STOP_TARGET_QUANTILE_TARGET == 'trailing_stop_target_quantile_v1'
    assert TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN == 'pred_trail_48_pnl_atr_x3_q10'
    assert TRAILING_STOP_TARGET_QUANTILE_Q50_COLUMN == 'pred_trail_48_pnl_atr_x3_q50'
    assert TRAILING_STOP_TARGET_QUANTILE_Q90_COLUMN == 'pred_trail_48_pnl_atr_x3_q90'


def test_build_export_frame_orders_crossed_quantiles():
    frame = build_trailing_stop_quantile_export_frame(
        times=np.array(['2026.01.01 00:00']),
        signals=np.array([1]),
        pred_q10=np.array([[0.8]], dtype=np.float32),
        pred_q50=np.array([[0.4]], dtype=np.float32),
        pred_q90=np.array([[0.1]], dtype=np.float32),
        true=np.array([[0.3]], dtype=np.float32),
    )

    assert frame.loc[0, 'pred_trail_48_pnl_atr_x3_q10'] == 0.1
    assert frame.loc[0, 'pred_trail_48_pnl_atr_x3_q50'] == 0.4
    assert frame.loc[0, 'pred_trail_48_pnl_atr_x3_q90'] == 0.8
    assert frame.loc[0, 'true_trail_48_pnl_atr_x3'] == 0.3


def test_compute_quantile_metrics_rejects_crossed_bounds():
    with pytest.raises(ValueError, match='must satisfy q10 <= q50 <= q90'):
        compute_trailing_stop_quantile_metrics(
            true_target=np.array([0.0, 1.0], dtype=np.float32),
            pred_q10=np.array([0.5, 0.8], dtype=np.float32),
            pred_q50=np.array([0.4, 0.7], dtype=np.float32),
            pred_q90=np.array([0.3, 0.6], dtype=np.float32),
        )
```

- [ ] **Step 2: Write the failing model-shape test**

```python
# tests/test_trailing_stop_target_quantile_model.py
import torch

from ML.models.trailing_stop_target_quantile_transformer import TrailingStopTargetQuantileTransformer


def test_quantile_model_returns_three_scalar_heads():
    model = TrailingStopTargetQuantileTransformer(input_features=20)
    X = torch.zeros((2, 20, 20), dtype=torch.float32)
    mask = torch.ones((2, 20), dtype=torch.bool)

    out = model(X, mask=mask)

    assert set(out.keys()) == {'q10', 'q50', 'q90'}
    assert out['q10'].shape == (2, 1)
    assert out['q50'].shape == (2, 1)
    assert out['q90'].shape == (2, 1)
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_trailing_stop_target_quantile_task.py \
  tests/test_trailing_stop_target_quantile_model.py -q
```

Expected: FAIL with `ModuleNotFoundError` for the new task/model modules.

- [ ] **Step 4: Implement the quantile task contract**

```python
# ML/trailing_stop_target_quantile_task.py
import numpy as np
import pandas as pd


TRAILING_STOP_TARGET_QUANTILE_TARGET = 'trailing_stop_target_quantile_v1'
TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN = 'trail_48_pnl_atr_x3'
TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN = 'pred_trail_48_pnl_atr_x3_q10'
TRAILING_STOP_TARGET_QUANTILE_Q50_COLUMN = 'pred_trail_48_pnl_atr_x3_q50'
TRAILING_STOP_TARGET_QUANTILE_Q90_COLUMN = 'pred_trail_48_pnl_atr_x3_q90'


def split_trailing_stop_quantile_target(df: pd.DataFrame) -> np.ndarray:
    return df[[TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN]].values.astype(np.float32)


def build_trailing_stop_quantile_export_frame(times, signals, pred_q10, pred_q50, pred_q90, true=None) -> pd.DataFrame:
    pred_q10 = np.asarray(pred_q10).reshape(-1)
    pred_q50 = np.asarray(pred_q50).reshape(-1)
    pred_q90 = np.asarray(pred_q90).reshape(-1)
    ordered = np.sort(np.stack([pred_q10, pred_q50, pred_q90], axis=1), axis=1)
    frame = pd.DataFrame({'time': times, 'signal': signals})
    frame[TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN] = ordered[:, 0]
    frame[TRAILING_STOP_TARGET_QUANTILE_Q50_COLUMN] = ordered[:, 1]
    frame[TRAILING_STOP_TARGET_QUANTILE_Q90_COLUMN] = ordered[:, 2]
    if true is not None:
        frame[f'true_{TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN}'] = np.asarray(true).reshape(-1)
    return frame


def _pinball(y_true: np.ndarray, y_pred: np.ndarray, q: float) -> float:
    diff = np.asarray(y_true, dtype=np.float64) - np.asarray(y_pred, dtype=np.float64)
    return float(np.mean(np.maximum(q * diff, (q - 1.0) * diff)))


def compute_trailing_stop_quantile_metrics(true_target, pred_q10, pred_q50, pred_q90) -> dict[str, float]:
    true_target = np.asarray(true_target, dtype=np.float64).reshape(-1)
    pred_q10 = np.asarray(pred_q10, dtype=np.float64).reshape(-1)
    pred_q50 = np.asarray(pred_q50, dtype=np.float64).reshape(-1)
    pred_q90 = np.asarray(pred_q90, dtype=np.float64).reshape(-1)
    if not (len(true_target) == len(pred_q10) == len(pred_q50) == len(pred_q90)):
        raise ValueError('all quantile arrays must have the same length')
    if np.any((pred_q10 > pred_q50) | (pred_q50 > pred_q90)):
        raise ValueError('predictions must satisfy q10 <= q50 <= q90')
    coverage = float(np.mean((true_target >= pred_q10) & (true_target <= pred_q90)))
    width = float(np.median(pred_q90 - pred_q10))
    return {
        'q10_pinball_loss': _pinball(true_target, pred_q10, 0.10),
        'q50_pinball_loss': _pinball(true_target, pred_q50, 0.50),
        'q90_pinball_loss': _pinball(true_target, pred_q90, 0.90),
        'interval_coverage': coverage,
        'median_interval_width': width,
    }
```

- [ ] **Step 5: Implement the bounded quantile model**

```python
# ML/models/trailing_stop_target_quantile_transformer.py
import torch
import torch.nn as nn

from ML.models.transformer import PositionalEncoding


class TrailingStopTargetQuantileTransformer(nn.Module):
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
        self.q10_head = nn.Sequential(nn.Dropout(dropout), nn.Linear(d_model, 32), nn.ReLU(), nn.Linear(32, 1))
        self.q50_head = nn.Sequential(nn.Dropout(dropout), nn.Linear(d_model, 32), nn.ReLU(), nn.Linear(32, 1))
        self.q90_head = nn.Sequential(nn.Dropout(dropout), nn.Linear(d_model, 32), nn.ReLU(), nn.Linear(32, 1))

    def forward(self, x: torch.Tensor, mask: torch.Tensor | None = None) -> dict[str, torch.Tensor]:
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
        return {
            'q10': self.q10_head(cls_output),
            'q50': self.q50_head(cls_output),
            'q90': self.q90_head(cls_output),
        }
```

- [ ] **Step 6: Run tests to verify they pass**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_trailing_stop_target_quantile_task.py \
  tests/test_trailing_stop_target_quantile_model.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add \
  ML/trailing_stop_target_quantile_task.py \
  ML/models/trailing_stop_target_quantile_transformer.py \
  tests/test_trailing_stop_target_quantile_task.py \
  tests/test_trailing_stop_target_quantile_model.py
git commit -m "ml: add trailing-stop quantile task contract"
```

### Task 2: Wire Quantile Task Through Train, Evaluate, And Export

**Files:**
- Modify: `ML/data_loader.py`
- Modify: `ML/train.py`
- Modify: `ML/evaluate_test.py`
- Modify: `API/generate_signals.py`
- Test: `tests/test_trailing_stop_target_quantile_task.py`

- [ ] **Step 1: Write the failing integration tests for loader, evaluation, and export**

```python
def test_create_test_loader_trailing_stop_quantile_branch(monkeypatch, tmp_path):
    import pandas as pd
    import numpy as np
    from ML import data_loader
    from ML.trailing_stop_target_quantile_task import TRAILING_STOP_TARGET_QUANTILE_TARGET

    df = pd.DataFrame(
        {
            'time': ['2026.01.01 00:00', '2026.01.01 01:00'],
            'signal': [1, -1],
            'trail_48_pnl_atr_x3': [0.3, -0.1],
        }
    )
    monkeypatch.setattr(data_loader, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(data_loader, 'TEST_FILE', tmp_path / 'Nero_test_labeled.csv')
    monkeypatch.setattr(data_loader.pd, 'read_csv', lambda *args, **kwargs: df)
    monkeypatch.setattr(data_loader, 'validate_csv_columns', lambda *args, **kwargs: None)
    monkeypatch.setattr(data_loader, 'validate_fractal_format', lambda *args, **kwargs: None)
    monkeypatch.setattr(
        data_loader,
        'parse_fractals_to_3d',
        lambda frame: (
            np.ones((len(frame), data_loader.N_FRACTALS, data_loader.N_FRACTAL_FEATURES), dtype=np.float32),
            np.ones((len(frame), data_loader.N_FRACTALS), dtype=bool),
        ),
    )

    loader = data_loader.create_test_loader(
        batch_size=2,
        target=TRAILING_STOP_TARGET_QUANTILE_TARGET,
        seq_len=20,
        clear_cache=True,
        num_workers=0,
    )

    X_batch, y_batch, mask_batch = next(iter(loader))
    assert X_batch.shape == (2, 20, data_loader.N_FRACTAL_FEATURES)
    assert y_batch.shape == (2, 1)


def test_generate_signals_exports_trailing_stop_quantile_columns(monkeypatch, tmp_path):
    import pandas as pd
    import torch
    import API.generate_signals as signal_api
    from ML.trailing_stop_target_quantile_task import TRAILING_STOP_TARGET_QUANTILE_TARGET

    class FakeModel(torch.nn.Module):
        def forward(self, x, mask=None):
            batch = x.shape[0]
            return {
                'q10': torch.full((batch, 1), -0.2, dtype=torch.float32, device=x.device),
                'q50': torch.full((batch, 1), 0.1, dtype=torch.float32, device=x.device),
                'q90': torch.full((batch, 1), 0.8, dtype=torch.float32, device=x.device),
            }

    calls = {}
    df = pd.DataFrame(
        {
            'time': ['2026.01.01 00:00', '2026.01.01 01:00'],
            'signal': [1, -1],
            'trail_48_pnl_atr_x3': [0.3, -0.1],
        }
    )
    monkeypatch.setattr(signal_api, 'CHECKPOINTS_DIR', tmp_path)
    monkeypatch.setattr(signal_api, 'create_data_loaders', lambda *args, **kwargs: ([(torch.zeros((2, 20, 20)), torch.zeros((2, 1)), torch.ones((2, 20), dtype=torch.bool))], [(torch.zeros((2, 20, 20)), torch.zeros((2, 1)), torch.ones((2, 20), dtype=torch.bool))], None))
    monkeypatch.setattr(signal_api, 'create_test_loader', lambda *args, **kwargs: [(torch.zeros((2, 20, 20)), torch.zeros((2, 1)), torch.ones((2, 20), dtype=torch.bool))])
    monkeypatch.setattr(signal_api.pd, 'read_csv', lambda *args, **kwargs: df)
    monkeypatch.setattr(signal_api, 'build_trailing_stop_target_quantile_model', lambda *_args, **_kwargs: FakeModel())
    monkeypatch.setattr(signal_api.torch, 'load', lambda *args, **kwargs: {'model_state_dict': {}, 'model_name': 'transformer', 'num_classes': 1, 'seq_len': 20, 'task': TRAILING_STOP_TARGET_QUANTILE_TARGET})

    signal_api.generate_signals(
        model_name='transformer',
        task=TRAILING_STOP_TARGET_QUANTILE_TARGET,
        research_out_prefix=str(tmp_path / 'quantile'),
    )

    export = pd.read_csv(tmp_path / 'quantile_validation_predictions.csv', sep=';')
    assert 'pred_trail_48_pnl_atr_x3_q10' in export.columns
    assert 'pred_trail_48_pnl_atr_x3_q50' in export.columns
    assert 'pred_trail_48_pnl_atr_x3_q90' in export.columns
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_trailing_stop_target_quantile_task.py -q
```

Expected: FAIL because `data_loader`, `train`, `evaluate_test`, and `generate_signals` do not yet know the new task.

- [ ] **Step 3: Register the new task in loader and training stack**

```python
# ML/data_loader.py
from ML.trailing_stop_target_quantile_task import (
    TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN,
    TRAILING_STOP_TARGET_QUANTILE_TARGET,
    split_trailing_stop_quantile_target,
)

# task_target_column()
if task == TRAILING_STOP_TARGET_QUANTILE_TARGET:
    return TRAILING_STOP_TARGET_QUANTILE_TARGET

# task_checkpoint_suffix()
if task == TRAILING_STOP_TARGET_QUANTILE_TARGET:
    return '_trailing_stop_target_quantile_v1'

# create_data_loaders() / create_test_loader()
elif target == TRAILING_STOP_TARGET_QUANTILE_TARGET:
    y_train = split_trailing_stop_quantile_target(df_train)
    y_val = split_trailing_stop_quantile_target(df_val)
```

```python
# ML/train.py
from ML.trailing_stop_target_quantile_task import TRAILING_STOP_TARGET_QUANTILE_TARGET
from ML.models.trailing_stop_target_quantile_transformer import TrailingStopTargetQuantileTransformer

def _quantile_loss(pred: torch.Tensor, target: torch.Tensor, q: float) -> torch.Tensor:
    diff = target - pred
    return torch.maximum(q * diff, (q - 1.0) * diff).mean()

# model construction branch
elif task == TRAILING_STOP_TARGET_QUANTILE_TARGET:
    model = TrailingStopTargetQuantileTransformer(input_features=model_kwargs.get('input_features', N_FRACTAL_FEATURES))

# train/validate branch
if task == TRAILING_STOP_TARGET_QUANTILE_TARGET:
    out = model(X_batch.to(device), mask=mask_batch.to(device))
    loss = (
        _quantile_loss(out['q10'], y_batch.to(device), 0.10) +
        _quantile_loss(out['q50'], y_batch.to(device), 0.50) +
        _quantile_loss(out['q90'], y_batch.to(device), 0.90)
    )
```

- [ ] **Step 4: Add evaluation and export branches**

```python
# ML/evaluate_test.py
from ML.trailing_stop_target_quantile_task import (
    TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN,
    TRAILING_STOP_TARGET_QUANTILE_TARGET,
    build_trailing_stop_quantile_export_frame,
    compute_trailing_stop_quantile_metrics,
)

elif task == TRAILING_STOP_TARGET_QUANTILE_TARGET:
    with torch.no_grad():
        all_q10, all_q50, all_q90 = [], [], []
        for X_batch, y_batch, mask_batch in test_loader:
            outputs = model(X_batch.to(device), mask=mask_batch.to(device))
            all_q10.append(outputs['q10'].cpu().numpy())
            all_q50.append(outputs['q50'].cpu().numpy())
            all_q90.append(outputs['q90'].cpu().numpy())
    export = build_trailing_stop_quantile_export_frame(
        times=df_test_full['time'].values,
        signals=df_test_full['signal'].values.astype(int),
        pred_q10=np.concatenate(all_q10),
        pred_q50=np.concatenate(all_q50),
        pred_q90=np.concatenate(all_q90),
        true=df_test_full[[TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN]].values.astype(np.float32),
    )
```

```python
# API/generate_signals.py
from ML.trailing_stop_target_quantile_task import (
    TRAILING_STOP_TARGET_QUANTILE_TARGET,
    build_trailing_stop_quantile_export_frame,
)

if task == TRAILING_STOP_TARGET_QUANTILE_TARGET:
    model = build_trailing_stop_target_quantile_model(model_kwargs)
    ...
    export = build_trailing_stop_quantile_export_frame(
        times=df_full['time'].values,
        signals=df_full['signal'].values.astype(int),
        pred_q10=np.concatenate(all_q10),
        pred_q50=np.concatenate(all_q50),
        pred_q90=np.concatenate(all_q90),
        true=df_full[['trail_48_pnl_atr_x3']].values.astype(np.float32),
    )
```

- [ ] **Step 5: Run integration tests to verify they pass**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_trailing_stop_target_quantile_task.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add \
  ML/data_loader.py \
  ML/train.py \
  ML/evaluate_test.py \
  API/generate_signals.py \
  tests/test_trailing_stop_target_quantile_task.py
git commit -m "ml: wire trailing-stop quantile task through stack"
```

### Task 3: Add Quantile Benchmark And Single-Run Orchestrator

**Files:**
- Create: `ML/benchmark_trailing_stop_target_quantile.py`
- Create: `ML/run_trailing_stop_target_quantile.py`
- Create: `tests/test_benchmark_trailing_stop_target_quantile.py`
- Create: `tests/test_run_trailing_stop_target_quantile.py`

- [ ] **Step 1: Write the failing benchmark tests**

```python
# tests/test_benchmark_trailing_stop_target_quantile.py
import pandas as pd

from ML.benchmark_trailing_stop_target_quantile import pick_validation_winner, summarize_candidate


def test_summarize_candidate_for_q10_gt_zero_rule():
    frame = pd.DataFrame(
        {
            'signal': [1, 1, -1],
            'pred_trail_48_pnl_atr_x3_q10': [0.4, -0.1, 0.2],
            'pred_trail_48_pnl_atr_x3_q50': [0.8, 0.3, 0.6],
            'pred_trail_48_pnl_atr_x3_q90': [1.2, 0.9, 1.4],
            'true_trail_48_pnl_atr_x3': [1.0, -0.5, 0.6],
        }
    )

    row = summarize_candidate(
        frame,
        candidate='q10_gt_zero',
        threshold=0.0,
        true_col='true_trail_48_pnl_atr_x3',
    )

    assert row['candidate'] == 'q10_gt_zero'
    assert row['trades'] == 2
    assert row['pf'] > 1.0
```

```python
# tests/test_run_trailing_stop_target_quantile.py
import json
import pandas as pd

from ML.run_trailing_stop_target_quantile import run_single_config


def test_single_run_writes_summary_and_benchmark(monkeypatch, tmp_path):
    import ML.run_trailing_stop_target_quantile as runner

    checkpoint_dir = tmp_path / 'checkpoints'
    reports_dir = tmp_path / 'reports'
    checkpoint_dir.mkdir()
    reports_dir.mkdir()
    monkeypatch.setattr(runner, 'CHECKPOINTS_DIR', checkpoint_dir)
    monkeypatch.setattr(runner, 'REPORTS_DIR', reports_dir)

    def fake_train_model(**kwargs):
        (checkpoint_dir / 'transformer_trailing_stop_target_quantile_v1_best.pt').write_bytes(b'checkpoint')
        return {'best_metric': 0.2, 'task': kwargs['task']}

    def fake_run_evaluation(**kwargs):
        (reports_dir / 'evaluate_test_trailing_stop_target_quantile_v1.md').write_text('ok', encoding='utf-8')
        (reports_dir / 'trailing_stop_target_quantile_test_predictions.csv').write_text('time;signal\n', encoding='utf-8')

    def fake_generate_signals(**kwargs):
        prefix = runner.Path(kwargs['research_out_prefix'])
        frame = pd.DataFrame(
            {
                'time': ['2026.01.01 00:00', '2026.01.02 00:00'],
                'signal': [1, -1],
                'pred_trail_48_pnl_atr_x3_q10': [0.2, -0.3],
                'pred_trail_48_pnl_atr_x3_q50': [0.6, 0.1],
                'pred_trail_48_pnl_atr_x3_q90': [1.0, 0.8],
                'true_trail_48_pnl_atr_x3': [0.7, -0.4],
            }
        )
        frame.to_csv(prefix.parent / f'{prefix.name}_validation_predictions.csv', sep=';', index=False)
        frame.to_csv(prefix.parent / f'{prefix.name}_test_predictions.csv', sep=';', index=False)

    monkeypatch.setattr(runner, 'train_model', fake_train_model)
    monkeypatch.setattr(runner, 'run_evaluation', fake_run_evaluation)
    monkeypatch.setattr(runner, 'generate_signals', fake_generate_signals)

    result = run_single_config(output_dir=tmp_path / 'quantile', epochs=1, patience=1, batch_size=8, seed=42, min_pf=1.0, skip_existing=False)
    saved = json.loads((tmp_path / 'quantile' / 'transformer_seq20_x3_quantile' / 'summary.json').read_text(encoding='utf-8'))
    assert saved['benchmark']['final_verdict']['verdict'] == 'go'
    assert result['benchmark']['final_verdict']['validation_winner']['candidate'] == 'q10_gt_zero'
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_benchmark_trailing_stop_target_quantile.py \
  tests/test_run_trailing_stop_target_quantile.py -q
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement the bounded quantile benchmark**

```python
# ML/benchmark_trailing_stop_target_quantile.py
import pandas as pd


def _active_rows(frame: pd.DataFrame) -> pd.DataFrame:
    signal = pd.to_numeric(frame.get('signal', 0), errors='coerce').fillna(0).astype(int)
    return frame.loc[signal != 0].copy()


def summarize_candidate(frame: pd.DataFrame, candidate: str, threshold: float, true_col: str) -> dict[str, float]:
    active = _active_rows(frame)
    if candidate == 'q10_gt_zero':
        live = active.loc[active['pred_trail_48_pnl_atr_x3_q10'] > 0.0].copy()
    elif candidate == 'q10_gt_m':
        live = active.loc[active['pred_trail_48_pnl_atr_x3_q10'] >= threshold].copy()
    elif candidate == 'q10_q50_positive':
        live = active.loc[(active['pred_trail_48_pnl_atr_x3_q10'] > 0.0) & (active['pred_trail_48_pnl_atr_x3_q50'] > 0.0)].copy()
    else:
        score = active['pred_trail_48_pnl_atr_x3_q10'] / (active['pred_trail_48_pnl_atr_x3_q90'] - active['pred_trail_48_pnl_atr_x3_q10']).abs().clip(lower=1e-6)
        live = active.loc[score >= threshold].copy()
    pnl = live[true_col].to_numpy(dtype=float)
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = float(-pnl[pnl < 0].sum())
    pf = gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)
    return {'candidate': candidate, 'threshold': float(threshold), 'trades': int(len(live)), 'pf': float(pf), 'ulcer_index_atr': float(abs(pnl.cumsum()).mean()) if len(pnl) else 0.0}


def pick_validation_winner(table: pd.DataFrame, min_pf: float = 1.0) -> pd.Series | None:
    eligible = table.loc[table['pf'] >= min_pf].copy()
    if eligible.empty:
        return None
    return eligible.sort_values(['pf', 'ulcer_index_atr', 'trades'], ascending=[False, True, False]).iloc[0]
```

- [ ] **Step 4: Implement the single-run orchestrator**

```python
# ML/run_trailing_stop_target_quantile.py
from pathlib import Path
import json
import shutil
import time

import pandas as pd

from API.generate_signals import generate_signals
from ML.benchmark_trailing_stop_target_quantile import pick_validation_winner, summarize_candidate
from ML.data_loader import task_checkpoint_suffix
from ML.evaluate_test import run_evaluation
from ML.train import CHECKPOINTS_DIR, REPORTS_DIR, train_model
from ML.trailing_stop_target_quantile_task import TRAILING_STOP_TARGET_QUANTILE_TARGET


def run_single_config(*, output_dir: Path, epochs: int, patience: int, batch_size: int, seed: int, min_pf: float, skip_existing: bool) -> dict[str, object]:
    run_dir = output_dir / 'transformer_seq20_x3_quantile'
    run_dir.mkdir(parents=True, exist_ok=True)
    train_result = train_model(
        model_name='transformer',
        task=TRAILING_STOP_TARGET_QUANTILE_TARGET,
        epochs=epochs,
        batch_size=batch_size,
        lr=1e-3,
        weight_decay=1e-4,
        patience=patience,
        seed=seed,
        use_scaler=False,
        use_weighted_sampler=False,
        seq_len=20,
        clear_cache=False,
        silent=False,
        model_kwargs={},
    )
    suffix = task_checkpoint_suffix(TRAILING_STOP_TARGET_QUANTILE_TARGET)
    ckpt = CHECKPOINTS_DIR / f'transformer{suffix}_best.pt'
    run_ckpt = run_dir / 'checkpoint.pt'
    shutil.copy2(ckpt, run_ckpt)
    run_evaluation(model_name='transformer', checkpoint_path=str(run_ckpt), task=TRAILING_STOP_TARGET_QUANTILE_TARGET, seed=seed, seq_len_override=20)
    generate_signals(model_name='transformer', task=TRAILING_STOP_TARGET_QUANTILE_TARGET, seed=seed, research_out_prefix=str(run_dir / 'trailing_stop_target_quantile'), seq_len_override=20)
    validation = pd.read_csv(run_dir / 'trailing_stop_target_quantile_validation_predictions.csv', sep=';')
    rows = [
        summarize_candidate(validation, 'q10_gt_zero', 0.0, 'true_trail_48_pnl_atr_x3'),
        summarize_candidate(validation, 'q10_q50_positive', 0.0, 'true_trail_48_pnl_atr_x3'),
    ]
    for threshold in sorted({float(validation['pred_trail_48_pnl_atr_x3_q10'].quantile(q)) for q in (0.8, 0.85, 0.9, 0.95)}, reverse=True):
        rows.append(summarize_candidate(validation, 'q10_gt_m', threshold, 'true_trail_48_pnl_atr_x3'))
    table = pd.DataFrame(rows)
    table.to_csv(run_dir / 'validation_grid.csv', sep=';', index=False)
    winner = pick_validation_winner(table, min_pf=min_pf)
    verdict = {'verdict': 'reject', 'validation_winner': None}
    if winner is not None:
        verdict = {'verdict': 'go', 'validation_winner': winner.to_dict()}
    payload = {'config': {'seq_len': 20, 'target_column': 'trail_48_pnl_atr_x3', 'epochs': epochs, 'patience': patience, 'batch_size': batch_size, 'seed': seed, 'min_pf': min_pf}, 'train_result': train_result, 'benchmark': verdict}
    (run_dir / 'summary.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return payload
```

- [ ] **Step 5: Run benchmark tests to verify they pass**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_benchmark_trailing_stop_target_quantile.py \
  tests/test_run_trailing_stop_target_quantile.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add \
  ML/benchmark_trailing_stop_target_quantile.py \
  ML/run_trailing_stop_target_quantile.py \
  tests/test_benchmark_trailing_stop_target_quantile.py \
  tests/test_run_trailing_stop_target_quantile.py
git commit -m "ml: add trailing-stop quantile benchmark"
```

### Task 4: Run First Wave, Write Report, Update Project Indexes

**Files:**
- Modify: `MODULE_INDEX.md`
- Modify: `CHANGELOG.md`
- Create: `docs/reports/2026-04-16-trailing-stop-target-quantile-first-wave.md`

- [ ] **Step 1: Run the full target-specific test suite**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_trailing_stop_target_quantile_task.py \
  tests/test_trailing_stop_target_quantile_model.py \
  tests/test_benchmark_trailing_stop_target_quantile.py \
  tests/test_run_trailing_stop_target_quantile.py -q
```

Expected: PASS.

- [ ] **Step 2: Run the bounded quantile experiment**

Run:

```bash
MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_trailing_stop_target_quantile \
  --output-dir ML/reports/trailing_stop_target_quantile \
  --epochs 3 \
  --patience 2 \
  --batch-size 256 \
  --min-pf 1.0
```

Expected:

- `ML/reports/trailing_stop_target_quantile/transformer_seq20_x3_quantile/summary.json`
- `validation_grid.csv`
- `final_verdict.json` or equivalent summary payload
- `trailing_stop_target_quantile_validation_predictions.csv`
- `trailing_stop_target_quantile_test_predictions.csv`

- [ ] **Step 3: Write the stage report**

```md
# Trailing Stop Target Quantile First Wave

> **Date**: 2026-04-16
> **Status**: Completed
> **Goal**: Проверить, даёт ли quantile-постановка для `trail_48_pnl_atr_x3` рабочую validation-zone лучше обычной регрессии

## Results

- Config: `transformer_seq20_x3_quantile`
- Best validation metric: `...`
- Best validation candidate: `...`
- Validation PF: `...`
- Test PF: `...`
- Verdict: `go` or `reject`

## Conclusion

- Сравнить с обычным `trailing_stop_target_v1` на `seq20 + x3`
- Явно указать, был ли достигнут порог `PF > 1`
```

- [ ] **Step 4: Update `MODULE_INDEX.md` and `CHANGELOG.md`**

Add to `MODULE_INDEX.md`:

```md
| [trailing_stop_target_quantile_task.py](ML/trailing_stop_target_quantile_task.py) | Quantile task для `trail_48_pnl_atr_x3`: contract, export helpers, metrics | — | — | ✅ |
| [benchmark_trailing_stop_target_quantile.py](ML/benchmark_trailing_stop_target_quantile.py) | Validation-first benchmark для trailing-stop quantile exports | prediction CSVs → validation/test verdict | — | ✅ |
| [run_trailing_stop_target_quantile.py](ML/run_trailing_stop_target_quantile.py) | Оркестратор bounded quantile run для `trail_48_pnl_atr_x3` | config → `reports/trailing_stop_target_quantile` | — | ✅ |
```

Add to `CHANGELOG.md`:

```md
## [2026-04-16] - Trailing-stop target quantile first wave

### Добавлено
- `ML/trailing_stop_target_quantile_task.py`
- `ML/models/trailing_stop_target_quantile_transformer.py`
- `ML/benchmark_trailing_stop_target_quantile.py`
- `ML/run_trailing_stop_target_quantile.py`

### Результаты
- bounded run для `trail_48_pnl_atr_x3`, `seq_len=20`, `q10/q50/q90`
- verdict: `...`

### Вывод
- quantile-постановка `...` обычную регрессию на том же target-е
```

- [ ] **Step 5: Commit**

```bash
git add \
  MODULE_INDEX.md \
  CHANGELOG.md \
  docs/reports/2026-04-16-trailing-stop-target-quantile-first-wave.md \
  ML/reports/trailing_stop_target_quantile
git commit -m "reports: record trailing-stop quantile first wave"
```
